#!/usr/bin/env python3
"""Discover a Fusion Windows runner and bind one GitHub diagnostic to its evidence.

GitHub schedules these jobs on pushed code. This is not pre-push local execution.
VM provisioning, protected registration and shutdown belong to fusion-runner.
"""

import argparse
import io
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

VERSION = "0.1.0"
VMRUN = "/Applications/VMware Fusion.app/Contents/Library/vmrun"
MAX_JSON = 1024 * 1024


class Failure(Exception):
    def __init__(self, code, message, exit_code=1):
        super().__init__(message)
        self.code, self.exit_code = code, exit_code


def read_json(path):
    path = Path(path).expanduser()
    if not path.is_file() or path.stat().st_size > MAX_JSON:
        raise Failure("invalid_file", "expected a regular JSON file of at most 1 MiB", 2)
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as exc:
        raise Failure("invalid_json", "could not read valid UTF-8 JSON", 2) from exc


def write_json(path, data, *, reserve=False):
    path = Path(path).expanduser()
    if path.is_symlink() or (path.exists() and not path.is_file()):
        raise Failure("invalid_file", "receipt must be a regular file, not a symlink", 2)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    try:
        with temporary.open("x", encoding="utf-8") as handle:
            os.chmod(temporary, 0o600)
            json.dump(data, handle, indent=2)
            handle.write("\n")
        if reserve:
            try:
                os.link(temporary, path)  # atomic no-clobber publication
            except FileExistsError as exc:
                raise Failure("receipt_exists", "another invocation reserved this receipt; collect it instead", 2) from exc
        else:
            temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def positive_id(value):
    return type(value) is int and value > 0


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def handoff(path, repository):
    data = read_json(path)
    if not isinstance(data, dict) or type(data.get("schema_version")) is not int or data["schema_version"] != 1:
        raise Failure("invalid_handoff", "expected handoff schema_version 1", 2)
    # A private recovery configuration must never be repurposed as this handoff.
    def secret_keys(value):
        if isinstance(value, dict):
            return any(re.search(r"password|token|credential|private.?key|secret|cookie|authorization|(?:api|access).?key", str(k), re.I)
                       or secret_keys(v) for k, v in value.items())
        return isinstance(value, list) and any(secret_keys(v) for v in value)
    if secret_keys(data):
        raise Failure("unsafe_handoff", "use the secret-free public handoff, not credential configuration", 2)
    runner, guest, vm = (data.get(key) for key in ("runner", "guest", "vm"))
    if not all(isinstance(item, dict) for item in (runner, guest, vm)):
        raise Failure("invalid_handoff", "handoff needs vm, guest and runner objects", 2)
    if runner.get("scope_type") != "repository" or runner.get("scope_url") != f"https://github.com/{repository}":
        raise Failure("scope_mismatch", "this helper supports the exact configured github.com repository", 2)
    if guest.get("os_arch") not in ("ARM64", "X64"):
        raise Failure("invalid_handoff", "guest architecture must have been observed inside Windows", 2)
    if not nonempty(vm.get("vmx_path")) or not Path(vm["vmx_path"]).is_absolute():
        raise Failure("invalid_handoff", "vm.vmx_path must be an absolute observed VM path", 2)
    if not Path(vm["vmx_path"]).is_file() or Path(vm["vmx_path"]).suffix.lower() != ".vmx":
        raise Failure("invalid_handoff", "the recorded VM configuration does not exist", 2)
    if runner.get("id") is not None and not positive_id(runner["id"]):
        raise Failure("invalid_handoff", "runner.id must be a positive integer or null", 2)
    if not nonempty(runner.get("name")):
        raise Failure("invalid_handoff", "record the intended runner name", 2)
    labels = runner.get("labels")
    if not isinstance(labels, list) or not labels or any(not nonempty(x) for x in labels):
        raise Failure("invalid_handoff", "record the actual runner label list", 2)
    if len({x.casefold() for x in labels}) != len(labels):
        raise Failure("invalid_handoff", "runner labels must not repeat", 2)
    return data


class GitHub:
    def __init__(self, executable, timeout):
        self.executable = shutil.which(executable)
        if not self.executable:
            raise Failure("missing_gh", "resolve an authenticated GitHub CLI executable", 3)
        self.deadline = time.monotonic() + timeout

    def remaining(self):
        left = self.deadline - time.monotonic()
        if left <= 0:
            raise Failure("deadline", "operation deadline expired; resume from its receipt", 5)
        return left

    def api(self, endpoint, *, method="GET", body=None, binary=False):
        args = [self.executable, "api", "--method", method, endpoint]
        if binary:
            args.append("--allow-escape-sequences")
        if body is not None:
            args += ["--input", "-"]
        try:
            result = subprocess.run(args, input=json.dumps(body).encode() if body is not None else None,
                                    capture_output=True, timeout=min(30, self.remaining()), check=False)
        except subprocess.TimeoutExpired as exc:
            raise Failure("request_timeout", "GitHub response is uncertain; reconcile before retrying a mutation", 5) from exc
        if result.returncode:
            raise Failure("github_error", f"GitHub request failed for {endpoint}; verify access and saved state")
        if binary:
            return result.stdout
        try:
            return json.loads(result.stdout) if result.stdout else None
        except ValueError as exc:
            raise Failure("github_response", "GitHub returned invalid JSON") from exc

    def pages(self, endpoint, key):
        output = []
        separator = "&" if "?" in endpoint else "?"
        for page in range(1, 101):
            data = self.api(f"{endpoint}{separator}per_page=100&page={page}")
            values = data.get(key) if isinstance(data, dict) else None
            if not isinstance(values, list):
                raise Failure("github_response", f"GitHub response lacks {key}")
            output.extend(values)
            if len(values) < 100:
                return output
        raise Failure("listing_bound", "listing exceeds 100 pages; absence is unverified")


def survey(profile, repository, architecture, api, vmrun):
    repo = api.api(f"repos/{repository}")
    if repo.get("full_name", "").casefold() != repository.casefold():
        raise Failure("scope_mismatch", "GitHub repository identity differs")
    vmx = str(Path(profile["vm"]["vmx_path"]).resolve())
    try:
        response = subprocess.run([vmrun, "-T", "fusion", "list"], capture_output=True,
                                  text=True, timeout=min(15, api.remaining()), check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise Failure("power_unknown", "Fusion power inventory is unavailable") from exc
    lines = response.stdout.splitlines()
    header = re.fullmatch(r"Total running VMs: (\d+)", lines[0].strip()) if lines else None
    paths = [s.strip() for s in lines[1:] if s.strip()]
    if response.returncode or not header or len(paths) != int(header[1]) or any(not Path(p).is_absolute() for p in paths):
        raise Failure("power_unknown", "Fusion returned an invalid power inventory")
    running = vmx in [str(Path(p).resolve()) for p in paths]
    expected = profile["runner"]
    runners = api.pages(f"repos/{repository}/actions/runners", "runners")
    matches = [r for r in runners if r["id"] == expected["id"]]
    if len(matches) > 1 or (matches and matches[0]["name"] != expected["name"]):
        raise Failure("runner_mismatch", "runner ID and name do not identify the same installation")
    runner = matches[0] if matches else None
    state = "unregistered"
    if runner:
        actual_labels = {label["name"].casefold() for label in runner["labels"]}
        requested_labels = {s.casefold() for s in expected["labels"]}
        if requested_labels != actual_labels:
            raise Failure("label_mismatch", "configured labels no longer match GitHub")
        eligible = [r for r in runners
                    if requested_labels <= {label['name'].casefold() for label in r['labels']}]
        if len(eligible) != 1 or eligible[0]['id'] != expected['id']:
            raise Failure('ambiguous_labels', 'the observed labels are not exclusive to this runner')
        state = "busy" if runner["busy"] else "ready" if runner["status"] == "online" else "offline"
        if runner["status"] not in ("online", "offline"):
            raise Failure("runner_unknown", "unrecognized runner connectivity")
        if not running and runner["status"] == "online":
            raise Failure("identity_conflict", "runner is online while its recorded VM is not running")
    if not running and state != "unregistered":
        state = "vm_not_running"
    if profile["guest"]["os_arch"] != architecture:
        state = "incompatible"
    return {"schema_version": 1, "state": state, "repository": repository,
            "runner_id": expected["id"], "runner_name": expected["name"],
            "labels": expected["labels"], "guest_architecture": profile["guest"]["os_arch"],
            "architecture_source": "recorded guest observation; verify again in the job report",
            "power_state": "running" if running else "not_running",
            "hosted_image_equivalence": "not_established", "changed": False}


def selection(path):
    value = read_json(path) if path else []
    if not isinstance(value, list) or len(value) > 1000 or any(not nonempty(x) for x in value):
        raise Failure("invalid_selection", "selection must be a JSON array of test IDs; [] means the complete diagnostic check", 2)
    if len(value) != len(set(value)):
        raise Failure("invalid_selection", "selected test IDs must be unique", 2)
    return value


def dispatch(args, api, profile):
    if Path(args.receipt).exists():
        raise Failure("receipt_exists", "use a new receipt or collect the existing invocation; do not redispatch", 2)
    current = survey(profile, args.repository, args.architecture, api, args.vmrun)
    if current["state"] != "ready":
        raise Failure("runner_not_ready", f"runner state is {current['state']}", 5)
    workflow = api.api(f"repos/{args.repository}/actions/workflows/{quote(args.workflow, safe='')}")
    if workflow.get("state") != "active":
        raise Failure("workflow_unavailable", "the diagnostic workflow must exist and be active on the default branch", 5)
    commit = api.api(f"repos/{args.repository}/commits/{quote(args.ref, safe='')}")["sha"]
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise Failure("invalid_commit", "GitHub did not resolve an exact commit")
    invocation = uuid.uuid4().hex
    inputs = {"diagnostic_id": invocation, "runner_labels": json.dumps(current["labels"]),
              "test_ids": json.dumps(selection(args.selection)), "expected_architecture": args.architecture}
    receipt = {"schema_version": 1, "repository": args.repository, "workflow_id": workflow["id"],
               "workflow_path": workflow["path"], "ref": args.ref, "commit": commit,
               "invocation": invocation, "runner_id": current["runner_id"],
               "runner_name": current["runner_name"], "architecture": args.architecture,
               "inputs": inputs, "created_at": datetime.now(timezone.utc).isoformat(),
               "status": "dispatch_intent", "evidence_verified": False}
    if args.dry_run:
        return dict(receipt, dry_run=True, changed=False)
    if not args.yes:
        raise Failure("confirmation_required", "dispatch requires --yes for this trusted repository/revision", 2)
    write_json(args.receipt, receipt, reserve=True)  # Persist before a possibly ambiguous POST.
    api.api(f"repos/{args.repository}/actions/workflows/{workflow['id']}/dispatches", method="POST",
            body={"ref": args.ref, "inputs": inputs})
    receipt["status"] = "dispatched"
    write_json(args.receipt, receipt)
    return receipt


def validate_report(report, receipt, job):
    if not isinstance(report, dict) or type(report.get("schema_version")) is not int or report["schema_version"] != 1:
        raise Failure("invalid_report", "diagnostic report schema is unsupported")
    if not all(positive_id(report.get(key)) for key in ('run_id', 'run_attempt')):
        raise Failure("invalid_report", "report run identifiers must be positive integers")
    for key, expected in {"commit": receipt["commit"], "invocation": receipt["invocation"],
                          "runner_name": receipt["runner_name"], "architecture": receipt["architecture"],
                          "run_id": receipt["run_id"], "run_attempt": receipt["run_attempt"],
                          "operating_system": "Windows", "native_architecture": receipt["architecture"],
                          "process_architecture": receipt["architecture"]}.items():
        if report.get(key) != expected:
            raise Failure("report_mismatch", f"report {key} does not match this invocation")
    if report.get("is_administrator") is not False:
        raise Failure("report_mismatch", "job did not prove non-administrator execution")
    tests = report.get("tests")
    if not isinstance(tests, list) or any(not isinstance(t, dict) or not nonempty(t.get("id"))
                                          or t.get("status") not in ("passed", "failed") for t in tests):
        raise Failure("invalid_report", "report needs test IDs and outcomes")
    ids = [t["id"] for t in tests]
    if len(ids) != len(set(ids)):
        raise Failure("invalid_report", "report contains duplicate test IDs")
    selected = json.loads(receipt["inputs"]["test_ids"])
    if selected and set(ids) != set(selected):
        raise Failure("no_selection", "the intended test selection was not executed", 5)
    if not ids:
        raise Failure("no_selection", "zero tests is not a passing diagnostic", 5)
    status = "failed" if any(t["status"] == "failed" for t in tests) else "passed"
    if report.get("status") != status or job["conclusion"] != ("failure" if status == "failed" else "success"):
        raise Failure("outcome_mismatch", "job, report and test outcomes disagree")
    return status, len(tests)


def collect(args, api):
    receipt = read_json(args.receipt)
    if (not isinstance(receipt, dict) or type(receipt.get("schema_version")) is not int or receipt["schema_version"] != 1
            or receipt.get("repository") != args.repository
            or not re.fullmatch(r"[0-9a-f]{32}", receipt.get("invocation", ""))
            or not positive_id(receipt.get("runner_id"))):
        raise Failure("invalid_receipt", "receipt does not bind this repository and invocation", 2)
    repo = args.repository
    marker = "Windows diagnostic " + receipt["invocation"]
    # A re-collection cannot carry forward a successful verdict while observing
    # another attempt or incomplete new evidence. Keep the previous files as history.
    receipt['evidence_verified'] = False
    receipt['status'] = 'collecting'
    for key in ('diagnostic_outcome', 'tests_executed', 'report_path', 'checked_at', 'job_log', 'job_log_truncated'):
        receipt.pop(key, None)
    write_json(args.receipt, receipt)
    while True:
        runs = api.pages(f"repos/{repo}/actions/workflows/{receipt['workflow_id']}/runs?event=workflow_dispatch", "workflow_runs")
        matches = [r for r in runs if r.get("display_title") == marker]
        if len(matches) > 1:
            raise Failure("ambiguous_run", "multiple runs match the invocation; inspect before proceeding")
        if matches:
            run = matches[0]
            if ((receipt.get('run_attempt') is None and run['run_attempt'] != 1)
                    or (receipt.get('run_id') is not None and receipt['run_id'] != run['id'])
                    or (receipt.get('run_attempt') is not None and receipt['run_attempt'] != run['run_attempt'])):
                raise Failure('run_attempt_changed', 'the invocation was rerun; preserve this receipt and inspect the new attempt')
            if run["head_sha"] != receipt["commit"]:
                raise Failure("commit_mismatch", "the dispatched ref moved; the job is not evidence for the intended commit")
            receipt.update(run_id=run["id"], run_attempt=run['run_attempt'], run_url=run["html_url"], status=run["status"])
            write_json(args.receipt, receipt)
            jobs = api.pages(f"repos/{repo}/actions/runs/{run['id']}/attempts/{run['run_attempt']}/jobs", "jobs")
            candidates = [j for j in jobs if j["name"] == "Windows diagnostic"]
            if len(candidates) > 1:
                raise Failure("ambiguous_job", "multiple jobs have the diagnostic identity")
            if candidates:
                job = candidates[0]
                receipt.update(job_id=job["id"], job_url=job["html_url"], job_status=job["status"], conclusion=job["conclusion"])
                write_json(args.receipt, receipt)
                if job["status"] == "completed":
                    break
            if run["status"] == "completed":
                raise Failure("missing_job", "workflow ended without the expected diagnostic job")
        time.sleep(min(3, api.remaining()))
    # Failed-job logs are saved before parsing artifacts or classifying failure.
    log_path = Path(args.receipt).with_suffix(".job.log")
    raw = api.api(f"repos/{repo}/actions/jobs/{job['id']}/logs", binary=True)
    if log_path.is_symlink() or (log_path.exists() and not log_path.is_file()):
        raise Failure("invalid_file", "job log path is not a regular file", 2)
    temporary = log_path.with_name(log_path.name + '.' + uuid.uuid4().hex + '.tmp')
    try:
        with temporary.open('xb') as handle:
            temporary.chmod(0o600)
            handle.write(raw[:16 * MAX_JSON])
        temporary.replace(log_path)
    finally:
        temporary.unlink(missing_ok=True)
    receipt["job_log"] = str(log_path.resolve())
    receipt['job_log_truncated'] = len(raw) > 16 * MAX_JSON
    write_json(args.receipt, receipt)
    if job["runner_id"] != receipt["runner_id"] or job["runner_name"] != receipt["runner_name"]:
        raise Failure("runner_mismatch", "the actual job executed on a different runner; its logs were retained")
    artifacts = api.pages(f"repos/{repo}/actions/runs/{run['id']}/artifacts", "artifacts")
    matches = [a for a in artifacts if a["name"] == "windows-diagnostic-" + receipt["invocation"] and not a["expired"]]
    if len(matches) != 1:
        raise Failure("missing_artifact", "one unexpired report artifact is required; retain the failed-job logs")
    if matches[0].get('size_in_bytes', 0) > 16 * MAX_JSON:
        raise Failure('artifact_too_large', 'diagnostic archive exceeds 16 MiB; preserve its metadata and logs')
    archive = api.api(f"repos/{repo}/actions/artifacts/{matches[0]['id']}/zip", binary=True)
    if len(archive) > 16 * MAX_JSON:
        raise Failure('artifact_too_large', 'diagnostic report archive exceeds 16 MiB')
    try:
        with zipfile.ZipFile(io.BytesIO(archive)) as zipped:
            files = zipped.infolist()
            if len(files) != 1 or files[0].filename != "windows-diagnostic.json" or files[0].file_size > MAX_JSON:
                raise Failure("invalid_artifact", "expected one bounded windows-diagnostic.json report")
            report = json.loads(zipped.read(files[0]).decode("utf-8-sig"))
    except (ValueError, OSError, zipfile.BadZipFile) as exc:
        raise Failure("invalid_artifact", "could not decode the diagnostic report") from exc
    report_path = Path(args.receipt).with_suffix(".report.json")
    write_json(report_path, report)
    status, count = validate_report(report, receipt, job)
    current = api.api(f"repos/{repo}/actions/runs/{run['id']}")
    if current['run_attempt'] != receipt['run_attempt'] or current['head_sha'] != receipt['commit']:
        raise Failure('run_attempt_changed', 'the workflow changed during collection; the saved report is historical evidence')
    receipt.update(status="completed", diagnostic_outcome=status, tests_executed=count,
                   evidence_verified=True, report_path=str(report_path.resolve()),
                   checked_at=datetime.now(timezone.utc).isoformat())
    write_json(args.receipt, receipt)
    return receipt


def display_table(result):
    fields = ('state', 'status', 'repository', 'guest_architecture', 'architecture',
              'power_state', 'runner_name', 'runner_id', 'commit', 'invocation',
              'run_url', 'job_url', 'diagnostic_outcome', 'tests_executed',
              'evidence_verified', 'job_log', 'report_path', 'changed', 'dry_run')
    rows = [(key, result[key]) for key in fields if key in result]
    width = max(len(key) for key, _ in rows)
    return '\n'.join(f'{key:<{width}}  {json.dumps(value) if isinstance(value, bool) else value}'
                     for key, value in rows)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("command", choices=("survey", "dispatch", "collect"))
    parser.add_argument("--version", "-V", action="version", version=VERSION)
    parser.add_argument("--repository", required=True, help="exact owner/repository on github.com")
    parser.add_argument("--handoff", help="secret-free local Fusion handoff JSON")
    parser.add_argument("--architecture", choices=("ARM64", "X64"))
    parser.add_argument("--vmrun", default=VMRUN)
    parser.add_argument("--gh", default="gh", help="authenticated GitHub CLI executable")
    parser.add_argument("--workflow", help="existing diagnostic workflow filename or ID")
    parser.add_argument("--ref", help="pushed branch or tag; resolved to an exact commit before dispatch")
    parser.add_argument("--selection", help="JSON file containing test IDs; omit for the complete diagnostic check")
    parser.add_argument("--receipt", help="local invocation receipt; new for dispatch, existing for collect")
    parser.add_argument("--timeout", type=int, default=120, help="total operation deadline in seconds, 1 to 1800 (default: 120)")
    parser.add_argument("--yes", "-y", action="store_true", help="authorize dispatch of this trusted revision")
    parser.add_argument("--dry-run", action="store_true", help="read-only dispatch preflight without writing a receipt")
    parser.add_argument("--output", "-o", choices=("table", "json"), default="table")
    parser.add_argument("--json", dest="output", action="store_const", const="json")
    values = sys.argv[1:] if argv is None else argv
    if not values:
        parser.print_help()
        return 0
    args = parser.parse_args(values)
    try:
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", args.repository) or not 1 <= args.timeout <= 1800:
            raise Failure("invalid_options", "use owner/repository and a timeout from 1 to 1800 seconds", 2)
        required = {"survey": ("handoff", "architecture"), "dispatch": ("handoff", "architecture", "workflow", "ref", "receipt"), "collect": ("receipt",)}[args.command]
        if any(not getattr(args, key) for key in required):
            raise Failure("invalid_options", "required for this command: " + ", ".join("--" + k for k in required), 2)
        if args.command != "dispatch" and any((args.yes, args.dry_run, args.ref, args.workflow, args.selection)):
            raise Failure("invalid_options", "dispatch options apply only to dispatch", 2)
        api = GitHub(args.gh, args.timeout)
        if args.command == "collect":
            result = collect(args, api)
        else:
            profile = handoff(args.handoff, args.repository)
            result = survey(profile, args.repository, args.architecture, api, args.vmrun) if args.command == "survey" else dispatch(args, api, profile)
        print(json.dumps(result, indent=2) if args.output == "json" else display_table(result))
        return 1 if result.get("diagnostic_outcome") == "failed" else 0
    except (Failure, OSError, KeyError, TypeError, ValueError) as exc:
        if not isinstance(exc, Failure):
            exc = Failure("invalid_state", "input or observed state is invalid; inspect the saved receipt", 2)
        error = {"error": {"code": exc.code, "message": str(exc)}}
        print(json.dumps(error) if args.output == "json" else str(exc), file=sys.stderr)
        return exc.exit_code


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(143))
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(130)
    except BrokenPipeError:
        sys.exit(0)
