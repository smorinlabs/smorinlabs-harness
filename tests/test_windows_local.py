"""Real snapshot controls and routing/evidence boundaries; VM evidence is separate."""
import importlib.util
import json
import math
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
import zipfile

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "plugins/repo-hygiene/skills/ci-fix/scripts"
sys.path.insert(0, str(SCRIPTS))
import windows_local as w
import windows_snapshot as snap
from windows_cost import choose

RUN = ROOT / "plugins/fusion-runner/skills/fusion-runner-run"
guest = w.guest_module(RUN)


def spec():
    return {"schema_version": 1, "workflow_path": ".github/workflows/windows.yml", "job": "test",
            "architecture": "ARM64", "command": "exit 0\n", "scope": "named check",
            "working_directory": ".", "environment": {}, "timeout_seconds": 10,
            "snapshot_exclude": [], "expected_test_ids": ["path-leaf"],
            "evidence": {"kind": "json", "path": "artifacts/tests.json"}}


def inventory(family="windows", cells=None):
    return {"workflows": [{"path": ".github/workflows/windows.yml", "jobs": [
        {"id": "test", "os_family": family, "matrix_cells": cells or [], "condition_state": True}
    ]}]}


def put(path, data):
    path.write_text(json.dumps(data)); return path


@pytest.fixture
def planned(tmp_path):
    vmx = tmp_path / "Working VM.vmx"; vmx.write_text("")
    return SimpleNamespace(inventory=put(tmp_path / "inventory.json", inventory()),
        profile=put(tmp_path / "profile.json", {"vm": {"vmx_path": str(vmx)}, "guest": {"os_arch": "ARM64"}}),
        fusion_setup=ROOT / "plugins/fusion-runner/skills/fusion-runner-setup", fusion_run=RUN,
        costs=None, access_file=tmp_path / "does-not-exist", receipt=tmp_path / "receipt.json",
        repository=tmp_path, yes=True, dry_run=False)


def test_linux_inventory_does_not_probe_fusion_or_read_credentials(planned, monkeypatch):
    put(planned.inventory, inventory("linux"))
    monkeypatch.setattr(w, "helper", lambda *_: pytest.fail("Fusion probed for Linux"))
    assert w.plan(planned, spec())["state"] == "not-applicable"
    assert w.run(planned, spec())["state"] == "not-applicable"
    assert not planned.receipt.exists()


def test_matrix_requires_one_resolved_windows_cell_before_probing():
    inv = inventory("unknown", [{"os": "ubuntu-latest", "os_family": "linux"}, {"os": "windows-11-arm", "os_family": "windows"}])
    with pytest.raises(w.Failure, match="matrix cell"):
        w.selected_windows_job(inv, spec())
    chosen = dict(spec(), matrix_cell={"os": "windows-11-arm"})
    assert w.selected_windows_job(inv, chosen)["id"] == "test"


def test_plan_delegates_only_to_existing_fusion_helpers(planned, monkeypatch):
    calls = []
    def helper(path, *args):
        calls.append((path.name, args))
        return {"fusion": {"installed": True}} if path.name == "host_preflight.py" else {"power_state": "running"}
    monkeypatch.setattr(w, "helper", helper)
    result = w.plan(planned, spec())
    assert [c[0] for c in calls] == ["host_preflight.py", "vm_power.py"]
    assert calls[1][1][0] == "status"
    assert result["cost"]["decision"] == "measure"
    assert result["changed"] is False


def test_missing_fusion_is_a_named_preparation_gap(planned, monkeypatch):
    monkeypatch.setattr(w, "helper", lambda *_: {"fusion": {"installed": False}})
    with pytest.raises(w.Failure, match="Fusion is not installed"):
        w.plan(planned, spec())


def test_remote_cost_decision_cannot_start_vm_or_read_access_file(planned, monkeypatch):
    monkeypatch.setattr(w, "plan", lambda *_: {"state": "planned", "cost": {"decision": "remote"}})
    monkeypatch.setattr(w, "guest_module", lambda *_: pytest.fail("guest access started"))
    with pytest.raises(w.Failure, match="selects CI"):
        w.run(planned, spec())
    assert not planned.receipt.exists()


def test_existing_receipt_never_reexecutes_even_before_discovery(planned, monkeypatch):
    planned.receipt.write_text('{"invocation":"first"}')
    monkeypatch.setattr(w, "plan", lambda *_: pytest.fail("existing invocation was replanned"))
    with pytest.raises(w.Failure, match="collect"):
        w.run(planned, spec())
    assert json.loads(planned.receipt.read_text())["invocation"] == "first"


def costs():
    return {"schema_version": 1, "context": "same", "source": "fixture-only",
        "remote_available": True,
        "local": {"startup_s": 100, "snapshot_s": 2, "transfer_s": 3, "setup_s": 1, "checks_s": 10, "collect_s": 1},
        "remote": {"submit_s": 1, "queue_s": 10, "setup_s": 15, "checks_s": 10, "collect_s": 1}}


def test_same_check_chooses_differently_for_cold_and_running_vm():
    assert choose(costs(), "same", "running")["local_seconds"] == 17
    assert choose(costs(), "same", "running")["decision"] == "local"
    assert choose(costs(), "same", "not_running")["local_seconds"] == 117
    assert choose(costs(), "same", "not_running")["decision"] == "remote"


def test_stale_context_and_missing_phase_do_not_claim_known_cost():
    assert choose(costs(), "changed", "running")["decision"] == "measure"
    data = costs(); del data["local"]["transfer_s"]
    assert choose(data, "same", "running")["local_seconds"] is None


@pytest.mark.parametrize("value", [-1, math.nan, math.inf, True])
def test_invalid_phase_times_are_rejected(value):
    data = costs(); data["local"]["checks_s"] = value
    with pytest.raises(ValueError): choose(data, "same", "running")


@pytest.fixture
def repository(tmp_path):
    root = tmp_path / "repo"; root.mkdir()
    def git(*args):
        return subprocess.run(["git", "-C", str(root), "-c", "core.hooksPath=/dev/null", "-c", "user.name=Fixture",
                               "-c", "user.email=fixture@example.invalid", *args], capture_output=True, check=True)
    git("init", "-q")
    (root / "tracked.ps1").write_text("original")
    (root / "deleted.ps1").write_text("deleted")
    (root / ".gitignore").write_text("ignored/\nartifacts/\n")
    git("add", "."); git("commit", "-qm", "fixture")
    return root, git


def test_snapshot_uses_worktree_edits_new_files_and_deletions(repository, tmp_path):
    root, git = repository
    (root / "tracked.ps1").write_text("staged"); git("add", "tracked.ps1")
    (root / "tracked.ps1").write_text("unstaged newest")
    (root / "deleted.ps1").unlink()
    (root / "new file 世界.txt").write_text("new")
    (root / "ignored").mkdir(); (root / "ignored/credential").write_text("excluded-fixture")
    archive = tmp_path / "snapshot.zip"
    result = snap.capture(root, archive, spec())
    with zipfile.ZipFile(archive) as z:
        assert z.read("source/tracked.ps1") == b"unstaged newest"
        assert z.read("source/new file 世界.txt") == b"new"
        assert not any("deleted.ps1" in n or "ignored" in n or "/.git/" in n for n in z.namelist())
    assert snap.matches(root, result, [])
    (root / "tracked.ps1").write_text("edited while Windows runs")
    assert not snap.matches(root, result, [])


def test_symlinks_and_lfs_pointers_are_preparation_gaps(repository, tmp_path):
    root, _ = repository
    (root / "linked").symlink_to("tracked.ps1")
    with pytest.raises(snap.SnapshotError, match="symlink"):
        snap.capture(root, tmp_path / "one.zip", spec())
    (root / "linked").unlink()
    (root / "large.bin").write_text("version https://git-lfs.github.com/spec/v1\noid sha256:fixture\n")
    with pytest.raises(snap.SnapshotError, match="LFS"):
        snap.capture(root, tmp_path / "two.zip", spec())


@pytest.mark.parametrize("path", ["../outside", "/absolute", "C:/drive", "a\\b", "a/../b", "NUL.txt", "name.", "x/.Git/config"])
def test_windows_paths_cannot_escape_or_silently_change_meaning(path):
    with pytest.raises(snap.SnapshotError): snap.relative_path(path)


@pytest.mark.parametrize("tests", [[], [{"id": "other", "status": "passed"}], [{"id": "path-leaf", "status": "skipped"}],
                                  [{"id": "path-leaf", "status": "passed"}]*2])
def test_exit_zero_is_insufficient_without_intended_tests(tests):
    with pytest.raises(w.Failure): w.test_evidence(json.dumps({"tests": tests}).encode(), spec())


def test_json_and_junit_preserve_failure_evidence():
    result = w.test_evidence(b'{"tests":[{"id":"path-leaf","status":"failed"}]}', spec())
    assert result["selection_verified"] and result["tests"][0]["status"] == "failed"
    junit = dict(spec(), expected_test_ids=["test_paths::leaf"], evidence={"kind": "junit", "path": "tests.xml"})
    result = w.test_evidence(b'<testsuite><testcase classname="test_paths" name="leaf"><failure/></testcase></testsuite>', junit)
    assert result["tests"] == [{"id": "test_paths::leaf", "status": "failed"}]


def test_access_file_permissions_and_password_newline_are_checked(tmp_path):
    path = put(tmp_path / "access.json", {"address": "192.0.2.1", "port": 22, "username": "fixture",
        "password": "fixture-password", "host_public_key": "ssh-ed25519 AAAA", "account_sid": "S-1-5-21-1-2-3-1001"})
    path.chmod(0o644)
    with pytest.raises(guest.GuestError, match="owner-only"): guest.load_access(path)
    path.chmod(0o600)
    assert guest.load_access(path)["port"] == 22
    data = json.loads(path.read_text()); data["password"] += "\n"; put(path, data)
    with pytest.raises(guest.GuestError, match="newline"): guest.load_access(path)


def test_sftp_paths_preserve_windows_drive_and_literal_metacharacters():
    assert guest.sftp_quote(r'C:\LocalFixture\name [1].txt') == '"/C:/LocalFixture/name \\[1\\].txt"'
    assert guest.sftp_quote('/private/tmp/name.txt') == '"/private/tmp/name.txt"'
    with pytest.raises(guest.GuestError): guest.sftp_quote('file\nget unrelated')


@pytest.mark.parametrize('field,value', [('address', '192.0.2.9'), ('host_public_key', 'ssh-ed25519 AQID'),
                                       ('account_sid', 'S-1-5-21-1-2-3-1001')])
def test_admission_observer_must_match_guest_and_use_separate_identity(field, value):
    access = {'address': '192.0.2.1', 'username': 'fixture', 'password': 'fixture-value',
              'host_public_key': 'ssh-ed25519 AAAA', 'account_sid': 'S-1-5-21-1-2-3-1001'}
    observer = dict(access, username='maintenance', account_sid='S-1-5-21-1-2-3-1002')
    assert guest.validate_access(dict(access, admission_access=observer))['admission_access']['username'] == 'maintenance'
    observer[field] = value
    with pytest.raises(guest.GuestError, match='same pinned'): guest.validate_access(dict(access, admission_access=observer))


def test_missing_inventory_permissions_cannot_be_treated_as_idle(monkeypatch):
    session = guest.SSH({'account_sid': 'expected'})
    monkeypatch.setattr(session, 'powershell', lambda *_: SimpleNamespace(returncode=1, stdout=b''))
    with pytest.raises(guest.GuestError, match='admission could not be verified'): session.check_admission('ARM64')


@pytest.mark.parametrize("field,value", [("is_administrator", True), ("account_sid", "another"), ("process_arch", "X64"), ("local_processes", 1), ("runner_processes", 1), ("runner_services", 1)])
def test_guest_probe_rejects_identity_or_active_work(field, value, monkeypatch):
    access = {"account_sid": "expected"}
    response = {"account_sid": "expected", "is_administrator": False, "is_windows": True,
                "os_arch": "ARM64", "process_arch": "ARM64", "runner_processes": 0, "runner_services": 0, "local_processes": 0}
    response[field] = value
    session = guest.SSH(access)
    monkeypatch.setattr(session, "powershell", lambda *_: SimpleNamespace(returncode=0, stdout=json.dumps(response).encode()))
    with pytest.raises(guest.GuestError): session.probe("ARM64")


def test_guest_powershell_adapter_parses_without_executing_it():
    pwsh = os.environ.get("P45_PWSH")
    if not pwsh: pytest.skip("P45_PWSH is required for the host PowerShell syntax control")
    script = guest.ps_literal(str(RUN / "scripts/local_job.ps1"))
    code = f"$tokens=$null;$errors=$null;[void][Management.Automation.Language.Parser]::ParseFile({script},[ref]$tokens,[ref]$errors);if($errors.Count){{$errors|Out-String|Write-Error;exit 1}}"
    result = subprocess.run([pwsh, "-NoProfile", "-Command", code], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("document", [[], {}, {"workflows": [None]}, {"workflows": [{"jobs": [None]}]}])
def test_invalid_inventory_is_a_named_input_error(document):
    with pytest.raises(w.Failure, match="workflow|job"):
        w.selected_windows_job(document, spec())


def test_json_array_and_unexpected_extra_tests_cannot_pass():
    with pytest.raises(w.Failure):
        w.test_evidence(b'[]', spec())
    data = {"tests": [{"id": "path-leaf", "status": "passed"}, {"id": "another", "status": "passed"}]}
    with pytest.raises(w.Failure, match="selection"):
        w.test_evidence(json.dumps(data).encode(), spec())


@pytest.fixture
def collected(repository, tmp_path):
    root, _ = repository
    selected = spec()
    snapshot = snap.capture(root, tmp_path / "collect.zip", selected)
    invocation = "a" * 32
    directory = "C:\\Users\\fixture\\AppData\\Local\\FusionLocalJobs\\" + invocation
    receipt = {"invocation": invocation, "spec": selected, "spec_sha256": snap.digest(selected),
               "snapshot": snapshot, "snapshot_sha256": snapshot["snapshot_sha256"],
               "account_sid": "fixture-sid", "repository": str(root), "guest_directory": directory}
    evidence = b'{"tests":[{"id":"path-leaf","status":"passed"}]}'
    report = {k: receipt[k] for k in ("invocation", "spec_sha256", "snapshot_sha256", "account_sid")}
    report.update(status="completed", architecture="ARM64", is_administrator=False,
                  timed_out=False, exit_code=0, evidence_sha256=w.hashlib.sha256(evidence).hexdigest())
    class Client:
        def check_admission(self, _architecture):
            return {'runner_services': 0, 'runner_processes': 0, 'local_processes': 0}
        def probe(self, *_args, **_kwargs):
            return {"account_sid": "fixture-sid", "work_root": directory.rsplit("\\", 1)[0]}
        def powershell(self, _code):
            return SimpleNamespace(returncode=0, stdout=json.dumps(report).encode())
        def copy(self, _source, target, **_kwargs):
            target.write_bytes(evidence)
    return receipt, report, Client(), tmp_path / "result.json", root


def test_collection_pass_binds_source_and_changed_source_stays_visible(collected):
    receipt, _, client, path, root = collected
    assert w.collect_with(client, guest, receipt, path)["status"] == "passed"
    (root / "tracked.ps1").write_text("changed during execution")
    result = w.collect_with(client, guest, receipt, path)
    assert result["status"] == "source-changed"
    assert result["evidence"]["selection_verified"] is True


def test_pass_requires_a_fresh_post_run_admission_check(collected, monkeypatch):
    receipt, _, client, path, _ = collected
    def blocked(_architecture):
        raise guest.GuestError('new runner service requires reconciliation')
    monkeypatch.setattr(client, 'check_admission', blocked)
    with pytest.raises(guest.GuestError): w.collect_with(client, guest, receipt, path)
    assert receipt['status'] == 'evidence-unverified'


@pytest.mark.parametrize("change", ["spec", "snapshot", "invocation", "account_sid", "exit_code"])
def test_changed_receipt_or_guest_identity_cannot_be_promoted_to_pass(collected, change):
    receipt, report, client, path, _ = collected
    if change == "spec": receipt["spec"]["expected_test_ids"] = []
    elif change == "snapshot": receipt["snapshot"]["bytes"] += 1
    elif change == "exit_code": report["exit_code"] = False
    else: report[change] = "different"
    with pytest.raises(w.Failure): w.collect_with(client, guest, receipt, path)


def test_timeout_is_not_an_empty_test_pass(collected):
    receipt, report, client, path, _ = collected
    report.update(timed_out=True, exit_code=-1, evidence_sha256=None)
    with pytest.raises(w.Failure, match="bound"):
        w.collect_with(client, guest, receipt, path)
    assert receipt["status"] == "timed-out"


def test_preparation_failure_retains_the_guest_reason(collected):
    receipt, report, client, path, _ = collected
    report.update(status="preparation-failed", snapshot_sha256=None, error="existing invocation lease")
    with pytest.raises(w.Failure, match="preparation failed"):
        w.collect_with(client, guest, receipt, path)
    assert receipt["guest_result"]["error"] == "existing invocation lease"
    assert receipt["status"] == "preparation-failed"


def test_only_successful_unchanged_source_is_added_to_the_existing_ledger(tmp_path):
    from local_ledger import load, matching
    selected = spec()
    ctx = w.execution_context(selected, "/observed/guest.vmx")
    args = SimpleNamespace(ledger=tmp_path / "ledger.json")
    receipt = {"spec": selected, "plan": {"execution_context": ctx}, "timings": {"checks_s": 4.0}}
    for status in ("failed", "source-changed", "unresolved"):
        receipt["status"] = status
        w.record_timing(args, receipt)
        assert not args.ledger.exists()
    receipt["status"] = "passed"
    w.record_timing(args, receipt)
    samples = matching(load(args.ledger), selected["workflow_path"], selected["workflow_path"], selected["job"], selected["scope"], w.context_digest(ctx))
    assert len(samples) == 1 and samples[0]["seconds"] == 4.0


@pytest.mark.parametrize("power,decision", [("running", "local"), ("not_running", "remote")])
def test_windows_cost_is_integrated_with_the_existing_scope_ladder(tmp_path, capsys, power, decision):
    import ladder_plan
    profile = put(tmp_path / "profile.json", {"jobs": [{"job": "test", "median_s": 200,
        "steps": [{"name": "check", "median_s": 2}]}]})
    ctx = w.execution_context(spec(), "/observed/guest.vmx")
    context_path = put(tmp_path / "context.json", ctx)
    estimate = costs(); estimate["context"] = w.context_digest(ctx)
    plan = put(tmp_path / "windows.json", {"state": "planned", "context": w.context_digest(ctx),
        "cost": choose(estimate, w.context_digest(ctx), power)})
    assert ladder_plan.main(["--profile", str(profile), "--context", str(context_path), "--job", "test",
        "--step", "check", "--ids", "1", "--local-env", "windows-vm", "--windows-plan", str(plan), "--json"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["local"]["windows_cost"]["decision"] == decision
    assert result["local"]["scope"] == ("ids" if decision == "local" else "unavailable")
    assert result["local"]["step_expected_s"] is None  # Hosted 2 seconds is not a local measurement.


def test_native_child_failure_is_not_lost_by_the_command_wrapper(repository, tmp_path):
    pwsh = os.environ.get("P45_PWSH")
    if not pwsh: pytest.skip("P45_PWSH is required for actual PowerShell child-exit semantics")
    selected = dict(spec(), command="& " + guest.ps_literal(pwsh) + " -NoProfile -Command 'exit 17'")
    archive = tmp_path / "child.zip"
    snap.capture(repository[0], archive, selected)
    script = tmp_path / "command.ps1"
    with zipfile.ZipFile(archive) as source:
        script.write_bytes(source.read("command.ps1"))
    result = subprocess.run([pwsh, "-NoProfile", "-File", str(script)], capture_output=True, timeout=15)
    assert result.returncode == 17


def test_lost_execution_response_retains_identity_and_never_retries(repository, planned, monkeypatch):
    root, _ = repository
    planned.repository = root
    ctx = w.execution_context(spec(), "/observed/guest.vmx")
    monkeypatch.setattr(w, "plan", lambda *_: {"state": "planned", "cost": {"decision": "measure"},
        "power_state": "running", "context": w.context_digest(ctx), "execution_context": ctx})
    executions = []
    class Client:
        def __init__(self, _access): pass
        def __enter__(self): return self
        def __exit__(self, *_): pass
        def probe(self, *_args, **_kwargs):
            return {"account_sid": "fixture-sid", "work_root": "C:\\Users\\fixture\\FusionLocalJobs"}
        def copy(self, *_args, **_kwargs): pass
        def powershell(self, code, **kwargs):
            if "input_data" in kwargs:
                executions.append(json.loads(kwargs["input_data"]))
                raise subprocess.TimeoutExpired("ssh", 1)
            return SimpleNamespace(returncode=1 if "Get-Content" in code else 0, stdout=b"")
    module = SimpleNamespace(SSH=Client, ps_literal=guest.ps_literal,
        load_access=lambda _: {"account_sid": "fixture-sid", "password": "private-fixture"})
    monkeypatch.setattr(w, "guest_module", lambda _: module)
    with pytest.raises(w.Failure, match="exact invocation"):
        w.run(planned, spec())
    retained = json.loads(planned.receipt.read_text())
    assert retained["status"] == "unresolved"
    assert executions[0]["invocation"] == retained["invocation"]
    assert executions[0]["snapshot_sha256"] == retained["snapshot_sha256"]
    with pytest.raises(w.Failure, match="collect"):
        w.run(planned, spec())
    with pytest.raises(w.Failure, match="before any retry"):
        w.collect_with(Client(None), module, retained, planned.receipt)
    assert len(executions) == 1
