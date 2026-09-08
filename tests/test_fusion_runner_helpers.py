"""Host-only controls. These fixtures do not validate Fusion or Windows itself."""

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SETUP = ROOT / "plugins/fusion-runner/skills/fusion-runner-setup"
RUN = ROOT / "plugins/fusion-runner/skills/fusion-runner-run"
POWER = RUN / "scripts/vm_power.py"
PREFLIGHT = SETUP / "scripts/host_preflight.py"


def load_module(path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def fake_fusion(tmp_path):
    vmx = tmp_path / "Windows with spaces $(touch INJECTION).vmwarevm" / "Windows.vmx"
    vmx.parent.mkdir()
    vmx.write_text('displayName = "Fixture Windows"\n')
    state = tmp_path / "state.json"
    state.write_text("[]")
    log = tmp_path / "calls.jsonl"
    vmrun = tmp_path / "fake vmrun"
    vmrun.write_text(
        f"#!{sys.executable}\n"
        + """import json, os, pathlib, sys, time
args = sys.argv[1:]
with open(os.environ['FAKE_LOG'], 'a') as handle:
    handle.write(json.dumps(args) + '\\n')
assert args[:2] == ['-T', 'fusion']
args = args[2:]
state = pathlib.Path(os.environ['FAKE_STATE'])
running = json.loads(state.read_text())
if os.environ.get('FAKE_FAILURE'):
    print('upstream error, not an inventory')
    sys.exit(1)
if args == ['list']:
    if os.environ.get('FAKE_MALFORMED'):
        print('Total running VMs: 2\\n' + str(state))
    else:
        print('Total running VMs: ' + str(len(running)))
        for vmx in running: print(vmx)
elif args[0] == 'start':
    assert args[2] == 'nogui'
    if os.environ.get('FAKE_SLOW'): time.sleep(3)
    state.write_text(json.dumps(running + [args[1]]))
elif args[0] == 'stop':
    assert args[2] == 'soft'
    state.write_text(json.dumps([p for p in running if p != args[1]]))
else:
    sys.exit(2)
"""
    )
    vmrun.chmod(0o755)
    env = dict(os.environ, FAKE_LOG=str(log), FAKE_STATE=str(state))

    def call(action, *flags, **overrides):
        return subprocess.run(
            [
                sys.executable,
                str(POWER),
                action,
                "--vmx",
                str(vmx),
                "--vmrun",
                str(vmrun),
                "--json",
                *flags,
            ],
            input="",
            capture_output=True,
            text=True,
            env=dict(env, **overrides),
            cwd=tmp_path,
            timeout=8,
            check=False,
        )

    def calls():
        return (
            [json.loads(line)[2:] for line in log.read_text().splitlines()]
            if log.exists()
            else []
        )

    return call, calls, vmx, state, tmp_path


def test_start_is_idempotent_and_keeps_path_one_argument(fake_fusion):
    call, calls, vmx, state, root = fake_fusion
    first = call("start")
    assert first.returncode == 0, first.stderr
    assert json.loads(first.stdout)["power_state"] == "running"
    assert json.loads(first.stdout)["runner_state"] == "not_checked"
    assert json.loads(state.read_text()) == [str(vmx)]
    second = call("start")
    assert second.returncode == 0
    assert json.loads(second.stdout)["changed"] is False
    assert sum(command[0] == "start" for command in calls()) == 1
    assert not (root / "INJECTION").exists()


@pytest.mark.parametrize(
    "flags,code", [([], 5), (["--yes"], 5), (["--runner-offline", "--no-input"], 2)]
)
def test_stop_refuses_without_offline_attestation_and_consent(fake_fusion, flags, code):
    call, calls, vmx, state, _ = fake_fusion
    state.write_text(json.dumps([str(vmx)]))
    result = call("stop", *flags)
    assert result.returncode == code
    assert result.stdout == ""
    assert "error" in json.loads(result.stderr)
    assert all(command[0] != "stop" for command in calls())
    assert json.loads(state.read_text()) == [str(vmx)]


def test_stop_is_graceful_and_scoped_to_one_vm(fake_fusion):
    call, calls, vmx, state, root = fake_fusion
    other = str(root / "another.vmx")
    state.write_text(json.dumps([str(vmx), other]))
    result = call("stop", "--runner-offline", "--yes")
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["power_state"] == "not_running"
    assert json.loads(state.read_text()) == [other]
    assert ["stop", str(vmx), "soft"] in calls()


@pytest.mark.parametrize("action,running", [("start", False), ("stop", True)])
def test_dry_run_does_not_change_power(fake_fusion, action, running):
    call, calls, vmx, state, _ = fake_fusion
    expected = [str(vmx)] if running else []
    state.write_text(json.dumps(expected))
    result = call(action, "--dry-run")
    assert result.returncode == 0
    assert json.loads(result.stdout)["dry_run"] is True
    assert json.loads(state.read_text()) == expected
    assert calls() == [["list"]]


@pytest.mark.parametrize(
    "overrides,error",
    [
        ({"FAKE_MALFORMED": "1"}, "invalid_inventory"),
        ({"FAKE_FAILURE": "1"}, "vmrun_failed"),
    ],
)
def test_unknown_power_inventory_never_triggers_a_start(fake_fusion, overrides, error):
    call, calls, _, _, _ = fake_fusion
    result = call("start", **overrides)
    assert result.returncode == 1
    assert result.stdout == ""
    assert json.loads(result.stderr)["error"]["code"] == error
    assert calls() == [["list"]]


def test_timeout_is_reported_as_uncertain_without_retry(fake_fusion):
    call, calls, _, _, _ = fake_fusion
    result = call("start", "--timeout", "1", FAKE_SLOW="1")
    assert result.returncode == 1
    error = json.loads(result.stderr)["error"]
    assert error["code"] == "timeout"
    assert "may have changed" in error["message"]
    assert sum(command[0] == "start" for command in calls()) == 1


def test_fifo_is_refused_without_reading_or_invoking_vmrun(fake_fusion):
    call, calls, vmx, _, _ = fake_fusion
    vmx.unlink()
    os.mkfifo(vmx)
    result = call("start")
    assert result.returncode == 2
    assert json.loads(result.stderr)["error"]["code"] == "invalid_path"
    assert calls() == []


@pytest.mark.parametrize(
    "machine,arm,expected",
    [
        ("x86_64", "1", "ARM64"),
        ("arm64", None, "ARM64"),
        ("x86_64", "0", "X64"),
        ("x86_64", None, None),
    ],
)
def test_hardware_architecture_handles_rosetta_and_denied_probe(machine, arm, expected):
    assert load_module(PREFLIGHT).host_architecture(machine, arm) == expected


@pytest.mark.parametrize("script", [POWER, PREFLIGHT])
@pytest.mark.parametrize("arguments", [[], ["--help"], ["-h"], ["--version"], ["-V"]])
def test_information_commands_succeed_without_vm_or_host_access(script, arguments):
    result = subprocess.run(
        [sys.executable, str(script), *arguments],
        text=True,
        capture_output=True,
        timeout=5,
        check=False,
    )
    assert result.returncode == 0
    assert result.stdout
    assert not result.stderr


def test_json_output_aliases_are_equivalent(fake_fusion):
    call, _, _, _, _ = fake_fusion
    assert json.loads(call("status").stdout) == json.loads(
        call("status", "-o", "json").stdout
    )


@pytest.mark.parametrize(
    "flags", [["--time", "1"], ["--timeout", "0"], ["--timeout", "nan"]]
)
def test_invalid_options_do_not_invoke_vmrun(fake_fusion, flags):
    call, calls, _, _, _ = fake_fusion
    result = call("start", *flags)
    assert result.returncode == 2
    assert result.stdout == ""
    assert calls() == []
