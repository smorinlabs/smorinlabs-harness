#!/usr/bin/env python3
"""Plan or execute current worktree files in a prepared standard-account Windows VM.

This path never pushes code or registers a GitHub runner. Plan is read-only;
run requires --yes and an inspected non-secret execution specification.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
import uuid
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
from windows_cost import choose
from local_ledger import context_digest
from windows_snapshot import capture, contents, digest, matches, relative_path, SnapshotError

VERSION = "0.1.0"
MAX_LOG = 16 * 1024 * 1024


class Failure(RuntimeError):
    def __init__(self, code, message, exit_code=5):
        super().__init__(message)
        self.code, self.exit_code = code, exit_code


def read_json(path):
    if path is None:
        raise Failure("preparation_gap", "provide the required local configuration or specification file")
    return json.load(sys.stdin) if str(path) == "-" else json.loads(Path(path).read_text(encoding="utf-8"))


def no_secrets(value):
    if isinstance(value, dict):
        for key, child in value.items():
            if re.search(r"(?i)password|token|cookie|secret|private.?key", key):
                raise Failure("secret_input", "keep credentials in the separate owner-only access file")
            no_secrets(child)
    elif isinstance(value, list):
        for child in value:
            no_secrets(child)


def specification(path):
    spec = read_json(path)
    if not isinstance(spec, dict) or spec.get("schema_version") != 1:
        raise Failure("invalid_spec", "execution specification needs schema_version 1", 2)
    no_secrets(spec)
    for field in ("workflow_path", "job", "command", "scope"):
        if not isinstance(spec.get(field), str) or not spec[field].strip():
            raise Failure("invalid_spec", f"execution specification needs {field}", 2)
    if spec.get("architecture") not in ("ARM64", "X64") or spec.get("shell", "pwsh") != "pwsh":
        raise Failure("unsupported_environment", "this adapter requires native ARM64 or X64 Windows with PowerShell 7")
    if spec.get("requires_git"):
        raise Failure("git_metadata_required", "this snapshot omits .git; use a prepared Git-aware environment for this command")
    if "${{" in spec["command"] or "\0" in spec["command"]:
        raise Failure("unresolved_command", "resolve workflow expressions and inspect the actual PowerShell command first")
    spec.setdefault("working_directory", ".")
    if spec["working_directory"] != ".":
        relative_path(spec["working_directory"])
    spec.setdefault("environment", {})
    if not isinstance(spec["environment"], dict) or any(
        not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", k) or not isinstance(v, str) or "${{" in v or "\0" in v
        for k, v in spec["environment"].items()
    ):
        raise Failure("invalid_environment", "use explicit resolved non-secret environment strings", 2)
    spec.setdefault("timeout_seconds", 120)
    if type(spec["timeout_seconds"]) is not int or not 1 <= spec["timeout_seconds"] <= 900:
        raise Failure("invalid_timeout", "command timeout must be 1 through 900 seconds", 2)
    spec.setdefault("snapshot_exclude", [])
    if not isinstance(spec["snapshot_exclude"], list) or any(not isinstance(x, str) or not x for x in spec["snapshot_exclude"]):
        raise Failure("invalid_exclusions", "snapshot_exclude must be a list of explicit path patterns", 2)
    evidence = spec.get("evidence", {})
    if not isinstance(evidence, dict) or evidence.get("kind") not in ("json", "junit", "command"):
        raise Failure("invalid_evidence", "evidence.kind must be json, junit or command", 2)
    if evidence["kind"] != "command":
        relative_path(evidence.get("path"))
    spec.setdefault("expected_test_ids", [])
    ids = spec["expected_test_ids"]
    if not isinstance(ids, list) or any(not isinstance(x, str) or not x.strip() for x in ids) or len(set(ids)) != len(ids):
        raise Failure("invalid_selection", "expected_test_ids must contain unique nonempty report IDs", 2)
    if evidence["kind"] == "command" and ids:
        raise Failure("invalid_selection", "test selection requires a JSON or JUnit report", 2)
    if not isinstance(spec.get("matrix_cell", {}), dict) or not isinstance(spec.get("execution_identity", {}), dict):
        raise Failure("invalid_spec", "matrix_cell and execution_identity must be objects", 2)
    return spec


def execution_context(spec, vmx_path=None):
    return {"command": spec["command"], "scope": spec["scope"], "environment": {
        "runner": "windows-vm", "architecture": spec["architecture"], "shell": "pwsh",
        "working_directory": spec["working_directory"], "values": spec["environment"],
        "identity": spec.get("execution_identity", {}),
        "vm": str(vmx_path) if vmx_path else None,
    }}


def context(spec, vmx_path=None):
    return context_digest(execution_context(spec, vmx_path))


def selected_windows_job(inventory, spec):
    if not isinstance(inventory, dict) or not isinstance(inventory.get("workflows"), list):
        raise Failure("invalid_inventory", "use workflow_inventory.py JSON output", 2)
    workflows = inventory.get("workflows", [])
    for workflow in workflows:
        if not isinstance(workflow, dict) or not isinstance(workflow.get("jobs"), list):
            raise Failure("invalid_inventory", "each workflow needs its jobs array", 2)
        for job in workflow["jobs"]:
            if not isinstance(job, dict) or not isinstance(job.get("matrix_cells", []), list) or any(
                not isinstance(cell, dict) for cell in job.get("matrix_cells", [])
            ):
                raise Failure("invalid_inventory", "each job needs resolved matrix objects", 2)
    any_windows = any(
        j.get("os_family") == "windows" or any(c.get("os_family") == "windows" for c in j.get("matrix_cells", []))
        for w in workflows for j in w.get("jobs", [])
    )
    if not any_windows:
        return None
    jobs = [j for w in workflows if w.get("path") == spec["workflow_path"]
            for j in w.get("jobs", []) if j.get("id") == spec["job"]]
    if len(jobs) != 1:
        raise Failure("ambiguous_job", "select one workflow path and job key from the inventory")
    job = jobs[0]
    if job.get("condition_state") is False:
        raise Failure("inactive_job", "the selected workflow job is disabled")
    cells = job.get("matrix_cells", [])
    if cells:
        selection = spec.get("matrix_cell", {})
        cells = [c for c in cells if all(c.get(k) == v for k, v in selection.items())]
        if len(cells) != 1 or cells[0].get("os_family") != "windows":
            raise Failure("ambiguous_cell", "select one resolved Windows matrix cell before Fusion discovery")
    elif job.get("os_family") != "windows":
        raise Failure("unsupported_job", "the selected job does not resolve to Windows")
    return job


def helper(path, *args):
    if not Path(path).is_file():
        raise Failure("fusion_skill_missing", "install fusion-runner@smorinlabs-harness, then supply --fusion-setup and --fusion-run with its actual skill directories")
    result = subprocess.run([sys.executable, str(path), *map(str, args), "--json"],
                            capture_output=True, timeout=330, check=False)
    if result.returncode:
        raise Failure("fusion_preparation_gap", "Fusion helper could not verify the requested state; inspect its own status and any unlock prompt")
    return json.loads(result.stdout)


def plan(args, spec):
    inventory = read_json(args.inventory)
    if selected_windows_job(inventory, spec) is None:
        return {"schema_version": 1, "state": "not-applicable", "reason": "inventory contains no Windows job", "changed": False}
    # The inventory gate precedes every Fusion probe and all access-file reads.
    host = helper(args.fusion_setup / "scripts/host_preflight.py", "probe")
    if host.get("fusion", {}).get("installed") is not True:
        raise Failure("fusion_missing", "Fusion is not installed; follow fusion-runner-setup before selecting local Windows execution")
    profile = read_json(args.profile)
    no_secrets(profile)
    if not isinstance(profile, dict) or not isinstance(profile.get("vm"), dict) or not isinstance(profile.get("guest"), dict):
        raise Failure("invalid_profile", "provide a Fusion profile with vm and guest objects", 2)
    vmx = Path(profile.get("vm", {}).get("vmx_path", ""))
    if not vmx.is_absolute() or not vmx.is_file():
        raise Failure("guest_missing", "provide the existing VM path in the Fusion profile; if no guest exists, follow fusion-runner-setup/references/create-your-own-runner.md")
    if profile.get("guest", {}).get("os_arch") != spec["architecture"]:
        raise Failure("incompatible_architecture", "the prepared guest does not match the check's required native architecture")
    if isinstance(profile.get("runner"), dict) and profile["runner"].get("id") is not None:
        raise Failure("runner_registered", "reconcile and retire the recorded GitHub registration before local execution")
    power = helper(args.fusion_run / "scripts/vm_power.py", "status", "--vmx", vmx)
    if power.get("power_state") not in ("running", "not_running"):
        raise Failure("unknown_power", "Fusion did not establish the selected VM power state")
    cost = choose(read_json(args.costs) if args.costs else None, context(spec, vmx.resolve()), power["power_state"])
    return {"schema_version": 1, "state": "planned", "changed": False,
            "vmx_path": str(vmx.resolve()), "power_state": power["power_state"],
            "context": context(spec, vmx.resolve()), "execution_context": execution_context(spec, vmx.resolve()), "cost": cost,
            "guest_access": "standard-account identity and prerequisite checks remain required at execution",
            "planned_effects": ["start the selected VM if needed", "transfer a new source snapshot",
                                "execute the reviewed command as the standard account", "retain invocation results"],
            "shutdown": "use fusion-runner-run after confirming admission and all active work; this helper never shuts Windows down"}


def write_receipt(path, value, *, reserve=False):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if reserve:
        with path.open("x", encoding="utf-8") as stream:
            path.chmod(0o600)
            json.dump(value, stream, indent=2)
            stream.write("\n")
    else:
        temporary = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
        with temporary.open("x", encoding="utf-8") as stream:
            temporary.chmod(0o600)
            json.dump(value, stream, indent=2)
            stream.write("\n")
        temporary.replace(path)


def record_timing(args, receipt):
    """Use the existing ledger; failed or stale-source runs are never samples."""
    if not getattr(args, "ledger", None) or receipt.get("status") != "passed":
        return
    spec = receipt["spec"]
    with tempfile.TemporaryDirectory(prefix="windows-timing-") as temporary:
        path = Path(temporary) / "context.json"
        path.write_text(json.dumps(receipt["plan"]["execution_context"]))
        completed = subprocess.run([
            sys.executable, str(HERE / "local_ledger.py"), "record", "--ledger", str(args.ledger),
            "--workflow", spec.get("workflow_name", spec["workflow_path"]),
            "--workflow-path", spec["workflow_path"], "--job", spec.get("job_name", spec["job"]),
            "--step", spec.get("step_name", spec["scope"]), "--context", str(path),
            "--seconds", str(receipt["timings"]["checks_s"]), "--conclusion", "success",
        ], capture_output=True, timeout=30, check=False)
        receipt["ledger"] = json.loads(completed.stdout) if completed.returncode == 0 else {
            "recorded": False, "reason": "ledger write failed; invocation evidence remains valid"}


def guest_module(directory):
    path = Path(directory) / "scripts/guest_session.py"
    if not path.is_file():
        raise Failure("fusion_skill_missing", "the installed Fusion run skill lacks the local guest adapter")
    module_spec = importlib.util.spec_from_file_location("fusion_local_guest", path)
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    return module


def test_evidence(data, spec):
    if spec["evidence"]["kind"] == "command":
        return {"kind": "command", "tests": [], "selection_verified": None}
    if len(data) > 8 * 1024 * 1024:
        raise Failure("invalid_report", "test evidence exceeds 8 MiB")
    if spec["evidence"]["kind"] == "json":
        try:
            report = json.loads(data)
        except ValueError:
            raise Failure("invalid_report", "test report is not valid JSON") from None
        tests = report.get("tests") if isinstance(report, dict) else None
    else:
        if b"<!DOCTYPE" in data or b"<!ENTITY" in data:
            raise Failure("invalid_report", "DTD declarations are not supported in JUnit evidence")
        tests = []
        try:
            root = ET.fromstring(data)
        except ET.ParseError:
            raise Failure("invalid_report", "test report is not valid JUnit XML") from None
        for case in root.iter("testcase"):
            name = case.get("name", "")
            identity = case.get("classname", "")
            tests.append({"id": f"{identity}::{name}" if identity else name,
                          "status": "failed" if case.find("failure") is not None or case.find("error") is not None
                          else "skipped" if case.find("skipped") is not None else "passed"})
    if not isinstance(tests, list) or not tests or any(
        not isinstance(t, dict) or not isinstance(t.get("id"), str) or not t["id"]
        or t.get("status") not in ("passed", "failed", "skipped") for t in tests
    ):
        raise Failure("no_selection", "a successful process without executed test evidence is not a pass")
    ids = [t["id"] for t in tests]
    if len(set(ids)) != len(ids):
        raise Failure("invalid_report", "test report contains duplicate IDs")
    executed = {t["id"] for t in tests if t["status"] != "skipped"}
    expected = set(spec["expected_test_ids"])
    if not executed or (expected and expected != executed):
        raise Failure("no_selection", "the executed test IDs differ from the intended selection, or all tests were skipped")
    return {"kind": spec["evidence"]["kind"], "tests": tests, "selection_verified": True}


def collect_with(client, module, receipt, path):
    if not isinstance(receipt.get("spec"), dict) or digest(receipt["spec"]) != receipt.get("spec_sha256"):
        raise Failure("invalid_receipt", "the recorded execution specification changed; preserve the original invocation", 2)
    snapshot = receipt.get("snapshot", {})
    if not isinstance(snapshot, dict) or digest({k: snapshot.get(k) for k in ("files", "excluded", "bytes")}) != receipt.get("snapshot_sha256") or snapshot.get("snapshot_sha256") != receipt.get("snapshot_sha256"):
        raise Failure("invalid_receipt", "the recorded source manifest changed; preserve the original invocation", 2)
    spec = receipt["spec"]
    observed = client.probe(spec["architecture"], require_idle=False)
    directory = observed["work_root"] + "\\" + receipt["invocation"]
    if receipt.get("guest_directory") != directory or receipt.get("account_sid") != observed["account_sid"]:
        raise Failure("identity_mismatch", "receipt does not match this account's invocation directory")
    result = client.powershell("$ErrorActionPreference='Stop'; Get-Content -LiteralPath " + module.ps_literal(directory + "\\result.json") + " -Raw")
    if result.returncode:
        raise Failure("result_unavailable", "guest result is not available; inspect the recorded invocation before any retry")
    report = json.loads(result.stdout.decode("utf-8-sig"))
    if not isinstance(report, dict):
        raise Failure("invalid_report", "guest result must be a structured invocation result")
    for key in ("invocation", "spec_sha256", "account_sid"):
        if report.get(key) != receipt.get(key):
            raise Failure("identity_mismatch", "guest evidence does not match the captured invocation")
    if report.get("architecture") != spec["architecture"] or report.get("is_administrator") is not False:
        raise Failure("identity_mismatch", "guest evidence does not prove native standard-account execution")
    receipt["guest_result"] = report
    if report.get("status") not in ("completed", "preparation-failed", "process-state-unknown"):
        raise Failure("invalid_report", "guest result has an unknown execution state")
    if report["status"] == "completed" and report.get("snapshot_sha256") != receipt.get("snapshot_sha256"):
        raise Failure("identity_mismatch", "guest snapshot differs from the captured invocation")
    receipt["status"] = "evidence-unverified" if report["status"] == "completed" else report["status"]
    artifact_root = Path(path).with_suffix(".artifacts")
    artifact_root.mkdir(exist_ok=True)
    for name in ("stdout", "stderr"):
        size = report.get(name + "_bytes", 0)
        if type(size) is not int or size < 0:
            raise Failure("invalid_report", "guest log sizes must be nonnegative integer byte counts")
        if size:
            if size > MAX_LOG:
                raise Failure("log_limit", "a log exceeds 16 MiB; retained guest logs need explicit collection")
            client.copy(directory + "\\" + name + ".log", artifact_root / (name + ".log"), download=True)
    if report["status"] != "completed":
        raise Failure("preparation_failed", "guest preparation failed; inspect guest_result in the private invocation receipt")
    if report.get("timed_out") is True:
        receipt["status"] = "timed-out"
        raise Failure("command_timeout", "the command exceeded its bound; inspect retained logs and confirmed process termination")
    data = b""
    if spec["evidence"]["kind"] != "command":
        if not report.get("evidence_sha256"):
            raise Failure("no_selection", "the command produced no test report")
        evidence = artifact_root / "evidence"
        client.copy(directory + "\\evidence", evidence, download=True)
        data = evidence.read_bytes()
        if hashlib.sha256(data).hexdigest() != report["evidence_sha256"]:
            raise Failure("report_mismatch", "downloaded test report digest differs from the guest report")
    verified = test_evidence(data, spec)
    receipt.update(evidence=verified, source_matches_snapshot=matches(receipt["repository"], receipt["snapshot"], spec["snapshot_exclude"]))
    if type(report.get("exit_code")) is not int or type(report.get("timed_out")) is not bool:
        raise Failure("invalid_report", "guest result must preserve integer exit status and boolean timeout state")
    receipt['admission_after'] = client.check_admission(spec['architecture'])
    passed = report["exit_code"] == 0 and report["timed_out"] is False and all(t["status"] != "failed" for t in verified["tests"])
    receipt["status"] = "passed" if passed else "failed"
    if not receipt["source_matches_snapshot"]:
        receipt["status"] = "source-changed"
    return receipt


def run(args, spec):
    invocation_start = time.monotonic()
    if not args.receipt:
        raise Failure("missing_receipt", "run requires a new --receipt path", 2)
    if args.receipt.exists():
        raise Failure("receipt_exists", "collect the existing invocation; run never reuses its receipt")
    planned = plan(args, spec)
    if planned["state"] == "not-applicable":
        return planned
    if args.dry_run:
        return planned
    if not args.yes:
        raise Failure("confirmation_required", "run requires --yes for the inspected repository, command and VM", 2)
    if planned["cost"]["decision"] == "remote":
        raise Failure("remote_cheaper", "the current cost plan selects CI; local execution was not started")
    module = guest_module(args.fusion_run)
    access = module.load_access(args.access_file)
    repo = args.repository.resolve()
    if args.access_file.resolve().is_relative_to(repo):
        selected, _ = contents(repo, spec["snapshot_exclude"])
        if args.access_file.resolve().relative_to(repo).as_posix() in {f["path"] for f in selected["files"]}:
            raise Failure("credential_in_snapshot", "exclude the access file from the repository snapshot")
    invocation = uuid.uuid4().hex
    receipt = {"schema_version": 1, "invocation": invocation, "status": "intent",
               "created_at": datetime.now(timezone.utc).isoformat(), "repository": str(repo),
               "plan": planned, "spec": spec, "spec_sha256": digest(spec), "account_sid": access["account_sid"],
               "context": planned["context"], "timings": {}}
    with tempfile.TemporaryDirectory(prefix="windows-local-") as scratch:
        archive = Path(scratch) / "input.zip"
        start = time.monotonic()
        receipt["snapshot"] = capture(repo, archive, spec)
        receipt["snapshot_sha256"] = receipt["snapshot"]["snapshot_sha256"]
        receipt["archive_sha256"] = hashlib.sha256(archive.read_bytes()).hexdigest()
        receipt["timings"]["snapshot_s"] = time.monotonic() - start
        write_receipt(args.receipt, receipt, reserve=True)
        try:
            start = time.monotonic()
            if planned["power_state"] != "running":
                helper(args.fusion_run / "scripts/vm_power.py", "start", "--vmx", planned["vmx_path"], "--wait-seconds", "300")
            receipt["timings"]["startup_s"] = time.monotonic() - start
            access_start = time.monotonic()
            with module.SSH(access) as client:
                observed = client.probe(spec["architecture"])
                receipt["guest"] = observed
                directory = observed["work_root"] + "\\" + invocation
                receipt["guest_directory"] = directory
                code = "$ErrorActionPreference='Stop'; $root=" + module.ps_literal(observed["work_root"]) + "; "
                code += "$node=Get-Item -LiteralPath (Split-Path $root -Parent); while ($null -ne $node) {"
                code += "if ($node.Attributes -band [IO.FileAttributes]::ReparsePoint) {throw 'Redirected ancestor'}; $node=$node.Parent}; "
                code += "$null=New-Item -ItemType Directory -Path $root -Force; "
                code += "if ((Get-Item -LiteralPath $root).Attributes -band [IO.FileAttributes]::ReparsePoint) {throw 'Redirected root'}; "
                code += "$null=New-Item -ItemType Directory -Path " + module.ps_literal(directory)
                if client.powershell(code).returncode:
                    raise Failure("workspace_failed", "could not create a new owned Windows invocation directory")
                receipt["timings"]["access_s"] = time.monotonic() - access_start
                start = time.monotonic()
                executor = args.fusion_run / "scripts/local_job.ps1"
                client.copy(archive, directory + "\\input.zip")
                client.copy(executor, directory + "\\executor.ps1")
                receipt["timings"]["transfer_s"] = time.monotonic() - start
                receipt["status"] = "execution-intent"
                write_receipt(args.receipt, receipt)
                executor_hash = hashlib.sha256(executor.read_bytes()).hexdigest()
                remote_executor = module.ps_literal(directory + "\\executor.ps1")
                code = "$ErrorActionPreference='Stop'; if ((Get-FileHash -LiteralPath " + remote_executor
                code += " -Algorithm SHA256).Hash.ToLowerInvariant() -cne '" + executor_hash + "') {throw 'Executor digest mismatch'}; & " + remote_executor
                payload = {k: receipt[k] for k in ("invocation", "account_sid", "archive_sha256", "snapshot_sha256", "spec_sha256")}
                payload["architecture"] = spec["architecture"]
                # An SSH timeout is uncertain execution. Collection never starts another job.
                client.powershell(code, input_data=json.dumps(payload).encode(), timeout=spec["timeout_seconds"] + 90)
                start = time.monotonic()
                collect_with(client, module, receipt, args.receipt)
                receipt["timings"]["collect_s"] = time.monotonic() - start
                receipt["timings"].update(setup_s=receipt["timings"]["access_s"] + receipt["guest_result"]["preparation_seconds"], checks_s=receipt["guest_result"]["execution_seconds"])
        except Exception as exc:
            if receipt["status"] in ("intent", "execution-intent"):
                receipt["status"] = "unresolved" if receipt["status"] == "execution-intent" else "preparation-failed"
            receipt["error"] = {"code": getattr(exc, "code", type(exc).__name__), "message": str(exc).replace(access["password"], "[redacted]")}
            write_receipt(args.receipt, receipt)
            if isinstance(exc, Failure):
                raise
            raise Failure("invocation_incomplete", "inspect the retained receipt and collect its exact invocation; do not assume a retry is safe") from None
        write_receipt(args.receipt, receipt)
        # Measure through collection before recording the cost sample. Include
        # host preflight and SSH session overhead; exclude the ledger write itself.
        receipt['timings']['total_s'] = time.monotonic() - invocation_start
        accounted = sum(receipt['timings'][name] for name in ('snapshot_s', 'startup_s', 'transfer_s', 'checks_s', 'collect_s'))
        receipt['timings']['setup_s'] = max(0.0, receipt['timings']['total_s'] - accounted)
        try:
            record_timing(args, receipt)
        except (OSError, ValueError, subprocess.SubprocessError):
            receipt["ledger"] = {"recorded": False, "reason": "ledger write failed; invocation evidence remains valid"}
        write_receipt(args.receipt, receipt)
    return receipt


def main(argv=None):
    default = HERE.parents[3] / "fusion-runner/skills"
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0], allow_abbrev=False)
    parser.add_argument("action", choices=("plan", "run", "collect"))
    parser.add_argument("--version", "-V", action="version", version=VERSION)
    for flag in ("inventory", "spec", "profile", "access-file", "costs", "receipt", "ledger"):
        parser.add_argument("--" + flag, type=Path)
    parser.add_argument("--repository", type=Path, default=Path.cwd())
    parser.add_argument("--fusion-setup", type=Path, default=default / "fusion-runner-setup")
    parser.add_argument("--fusion-run", type=Path, default=default / "fusion-runner-run")
    parser.add_argument("--yes", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--no-input", action="store_true", help="never prompt; run still requires explicit --yes")
    parser.add_argument("--output", "-o", choices=("table", "json"), default="table")
    parser.add_argument("--json", dest="output", action="store_const", const="json")
    argv = sys.argv[1:] if argv is None else argv
    if not argv:
        parser.print_help()
        return 0
    args = parser.parse_args(argv)
    if sum(str(getattr(args, field)) == "-" for field in ("inventory", "spec", "profile", "costs")) > 1:
        parser.error("only one JSON input can read stdin with '-'")
    if any(str(getattr(args, field)) == "-" for field in ("receipt", "access_file", "ledger")):
        parser.error("receipt, access-file and ledger require real local file paths")
    if args.action == "collect" and args.dry_run:
        parser.error("collect retrieves evidence; --dry-run is supported only for plan and run")
    receipt = None
    try:
        if args.action == "collect":
            receipt = read_json(args.receipt)
            if not isinstance(receipt, dict) or receipt.get("schema_version") != 1 or not isinstance(receipt.get("invocation"), str) or not re.fullmatch(r"[a-f0-9]{32}", receipt.get("invocation", "")):
                receipt = None
                raise Failure("invalid_receipt", "select an intact local invocation receipt", 2)
            module = guest_module(args.fusion_run)
            with module.SSH(module.load_access(args.access_file)) as client:
                result = collect_with(client, module, receipt, args.receipt)
                write_receipt(args.receipt, result)
        else:
            spec = specification(args.spec)
            result = plan(args, spec) if args.action == "plan" else run(args, spec)
        print(json.dumps(result, indent=2) if args.output == "json" else f"Windows local: {result.get('status', result.get('state'))}\n{result.get('reason', '')}")
        return 1 if result.get("status") == "failed" else 5 if result.get("status") == "source-changed" else 0
    except (RuntimeError, SnapshotError, OSError, ValueError, ImportError, subprocess.SubprocessError) as exc:
        if receipt is not None:
            receipt["collection_error"] = {"code": getattr(exc, "code", "collection_failed"), "message": str(exc)}
            write_receipt(args.receipt, receipt)
        error = {"error": {"code": getattr(exc, "code", "local_execution_failed"), "message": str(exc)}}
        print(json.dumps(error) if args.output == "json" else "error: " + str(exc), file=sys.stderr)
        return getattr(exc, "exit_code", 1)
    except KeyboardInterrupt:
        print("Interrupted; inspect the invocation receipt before retrying guest execution.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    sys.exit(main())
