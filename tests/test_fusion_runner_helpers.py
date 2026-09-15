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


@pytest.mark.parametrize('action,initial,target', [('start', False, True), ('stop', True, False)])
def test_optional_polling_observes_delayed_transition_once(tmp_path, monkeypatch, action, initial, target):
    from types import SimpleNamespace
    module = load_module(POWER)
    vmx = tmp_path / 'VM.vmx'; vmx.write_text('')
    executable = tmp_path / 'vmrun'; executable.write_text(''); executable.chmod(0o755)
    clock = [0.0]
    observations = iter([initial, initial, target])
    calls = []
    monkeypatch.setattr(module.time, 'monotonic', lambda: clock[0])
    monkeypatch.setattr(module.time, 'sleep', lambda seconds: clock.__setitem__(0, clock[0]+seconds))
    monkeypatch.setattr(module, 'is_running', lambda *_: next(observations))
    monkeypatch.setattr(module, 'invoke', lambda _vmrun, args, timeout: calls.append((args, timeout)))
    args = SimpleNamespace(vmx=str(vmx), vmrun=str(executable), action=action, timeout=30,
                           wait_seconds=3, runner_offline=action=='stop', yes=action=='stop',
                           dry_run=False, no_input=True)
    result = module.execute(args)
    assert result['changed'] and len(calls)==1
    assert calls[0][1] <= 3 and clock[0] <= 3


def test_poll_deadline_does_not_repeat_a_stuck_power_request(tmp_path, monkeypatch):
    from types import SimpleNamespace
    module=load_module(POWER)
    vmx=tmp_path/'VM.vmx';vmx.write_text('')
    executable=tmp_path/'vmrun';executable.write_text('');executable.chmod(0o755)
    clock=[0.0];calls=[]
    monkeypatch.setattr(module.time,'monotonic',lambda:clock[0])
    monkeypatch.setattr(module.time,'sleep',lambda seconds:clock.__setitem__(0,clock[0]+seconds))
    monkeypatch.setattr(module,'is_running',lambda *_:False)
    monkeypatch.setattr(module,'invoke',lambda *args:calls.append(args))
    args=SimpleNamespace(vmx=str(vmx),vmrun=str(executable),action='start',timeout=30,
                         wait_seconds=3,runner_offline=False,yes=False,dry_run=False,no_input=True)
    with pytest.raises(module.Failure,match='deadline'):
        module.execute(args)
    assert len(calls)==1 and clock[0]==3


def test_poll_budget_includes_initial_inventory_and_mutation(tmp_path, monkeypatch):
    from types import SimpleNamespace
    module=load_module(POWER)
    vmx=tmp_path/'VM.vmx';vmx.write_text('')
    executable=tmp_path/'vmrun';executable.write_text('');executable.chmod(0o755)
    clock=[0.0];limits=[]
    monkeypatch.setattr(module.time,'monotonic',lambda:clock[0])
    def inventory(_binary,_path,timeout):
        limits.append(timeout);clock[0]+=1;return False
    def request(_binary,_args,timeout):
        limits.append(timeout);clock[0]+=timeout
    monkeypatch.setattr(module,'is_running',inventory)
    monkeypatch.setattr(module,'invoke',request)
    args=SimpleNamespace(vmx=str(vmx),vmrun=str(executable),action='start',timeout=30,
                         wait_seconds=3,runner_offline=False,yes=False,dry_run=False,no_input=True)
    with pytest.raises(module.Failure,match='deadline'):module.execute(args)
    assert limits==[3,2] and clock[0]==3


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


def test_already_off_stop_is_observation_without_shutdown(fake_fusion):
    call, calls, _, _, _ = fake_fusion
    result = call("stop")
    assert result.returncode == 0
    report = json.loads(result.stdout)
    assert report["changed"] is False
    assert report["power_state"] == "not_running"
    assert report["runner_state"] == "not_checked"
    assert calls() == [["list"]]


@pytest.fixture
def mac_preflight(monkeypatch):
    from types import SimpleNamespace

    module = load_module(PREFLIGHT)
    monkeypatch.setattr(module.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(module.platform, "machine", lambda: "x86_64")
    monkeypatch.setattr(module.platform, "mac_ver", lambda: ("26.4", (), ""))
    values = {"hw.optional.arm64": "1", "hw.memsize": "51539607552"}
    monkeypatch.setattr(module, "probe_value", lambda *command: values.get(command[-1]))
    monkeypatch.setattr(module.shutil, "disk_usage", lambda path: SimpleNamespace(free=4096))
    return module, values


def test_preflight_collect_labels_planned_windows_architecture(mac_preflight, tmp_path):
    import plistlib

    module, _ = mac_preflight
    app = tmp_path / "Renamed Fusion.app"
    library = app / "Contents/Library"
    library.mkdir(parents=True)
    (app / "Contents/Info.plist").write_bytes(
        plistlib.dumps({"CFBundleShortVersionString": "26H1u1"})
    )
    vmrun = library / "vmrun"
    vmrun.write_text("#!/bin/sh\nexit 0\n")
    vmrun.chmod(0o755)
    report = json.loads(json.dumps(module.collect(tmp_path, app)))
    assert report["schema_version"] == 2
    assert report["host"]["process_architecture"] == "x86_64"
    assert report["host"]["architecture"] == "ARM64"
    assert report["host"]["memory_bytes"] == 51539607552
    assert report["expected_windows_architecture"] == "ARM64"
    assert "windows_architecture" not in report
    assert report["compatibility_verified"] is False
    assert report["storage"] == {"path": str(tmp_path), "free_bytes": 4096}
    assert report["fusion"]["installed"] is True
    assert report["fusion"]["version"] == "26H1u1"
    assert report["fusion"]["vmrun_path"] == str(vmrun)
    assert report["fusion"]["vmrun_executable"] is True


@pytest.mark.parametrize("plist_state", ["absent", "malformed"])
def test_preflight_collect_preserves_unknown_facts(mac_preflight, tmp_path, plist_state):
    module, values = mac_preflight
    values.clear()
    app = tmp_path / "Unavailable.app"
    if plist_state == "malformed":
        (app / "Contents").mkdir(parents=True)
        (app / "Contents/Info.plist").write_bytes(b"not a plist")
    report = module.collect(tmp_path, app)
    assert report["host"]["architecture"] is None
    assert report["host"]["memory_bytes"] is None
    assert report["expected_windows_architecture"] is None
    assert report["fusion"]["installed"] is False
    assert report["fusion"]["version"] is None
    assert report["fusion"]["vmrun_executable"] is False


@pytest.mark.parametrize("storage_kind", ["file", "missing"])
def test_preflight_collect_rejects_invalid_storage(mac_preflight, tmp_path, storage_kind):
    module, _ = mac_preflight
    storage = tmp_path / "destination"
    if storage_kind == "file":
        storage.touch()
    with pytest.raises((ValueError, FileNotFoundError)):
        module.collect(storage, tmp_path / "Fusion.app")


def test_preflight_collect_rejects_non_macos(mac_preflight, monkeypatch, tmp_path):
    module, _ = mac_preflight
    monkeypatch.setattr(module.platform, "system", lambda: "Linux")
    with pytest.raises(ValueError, match="requires macOS"):
        module.collect(tmp_path, tmp_path / "Fusion.app")
