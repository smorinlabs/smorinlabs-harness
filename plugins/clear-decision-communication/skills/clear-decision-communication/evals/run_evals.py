# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Run this skill's communication scenarios in fresh CLI sessions.

Prepare records without calling a model (the default):
  uv run --no-project path/to/evals/run_evals.py --output /tmp/cdc-prepared

Run selected cases with installed CLI defaults, without choosing a model:
  uv run --no-project path/to/evals/run_evals.py --tool both --cases 1 2 4 \
      --output /tmp/cdc-live --run

Add --source-review for a separate reviewer and at most one revision per draft.
With --drafts-from /tmp/prior-run, validate and reuse the original writer captures
instead of generating new drafts. Reviewer reports never replace independent
semantic grades. The source-review protocol and paired grading criteria are
snapshotted outside the unchanged skill instructions and model input sources.

The output directory must be new. Each case gets a private temporary working
directory containing only the snapshotted skill, references, and raw inputs.
Only those input paths enter the prompt; expectations remain in the outer
review.json. Outputs, prompts, commands, versions, source hashes, and process
results persist in --output. Scratch directories are removed after each case.

These are decision and communication simulations, not live mutation tests or
native dialog-rendering tests. CLI read-only controls restrict permitted tools;
this runner is not a security sandbox for hostile models or executables.
Configured authentication is reused; no credentials or environment dumps are
copied into the records. No model, effort, or provider is selected by the runner.

Review actual stdout.jsonl and stderr.txt, then fill each review.json's semantic
verdict, reviewer, and evidence per criterion. A successful process exit is NEVER
a behavioral pass. An incomplete or failed run may be inconclusive; it is not a
failed skill evaluation without reviewing what occurred. The runner never grades.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import selectors
import shutil
import signal
import subprocess
import tempfile
import time


SKILL_DIR = Path(__file__).resolve().parent.parent
REVIEW_INSTRUCTIONS = Path(__file__).with_name("source-review.md")


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def safe_relative(value: str) -> Path:
    path = PurePosixPath(value)
    if (
        not value or "\\" in value or PureWindowsPath(value).drive
        or path.is_absolute() or any(p in {".", ".."} for p in value.split("/"))
    ):
        raise ValueError(f"Expected a nonempty relative input path: {value!r}")
    return Path(*path.parts)


def read_cases(path: Path) -> list[dict]:
    cases = json.loads(path.read_text(encoding="utf-8"))["evals"]
    ids = set()
    for case in cases:
        if not isinstance(case["id"], int) or case["id"] < 1 or case["id"] in ids:
            raise ValueError("Case IDs must be unique positive integers")
        ids.add(case["id"])
        if not isinstance(case["prompt"], str) or not case["expectations"]:
            raise ValueError(f"Case {case['id']} needs a prompt and separate expectations")
        paths = [safe_relative(item["path"]) for item in case["files"]]
        if len(set(paths)) != len(paths):
            raise ValueError(f"Case {case['id']} repeats an input path")
    return cases


def instruction_files(source: Path):
    """Read only instruction files; never follow links or include evaluations."""
    paths = [source / "SKILL.md", source / "references"]
    paths.extend(sorted((source / "references").rglob("*")))
    for path in paths:
        if path.is_symlink():
            raise ValueError(f"Skill snapshots do not follow symlinks: {path}")
        if path.is_dir():
            continue
        if not path.is_file():
            raise ValueError(f"Expected a regular skill file: {path}")
        yield path.relative_to(source), path.read_bytes()


def snapshot_skill(source: Path, target: Path) -> dict[str, str]:
    """Copy only skill instructions and references; never copy the eval directory."""
    hashes = {}
    for relative, data in instruction_files(source):
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
        hashes[relative.as_posix()] = hashlib.sha256(data).hexdigest()
    return hashes


def stage_case(case: dict, snapshot: Path, workspace: Path) -> str:
    shutil.copytree(snapshot, workspace / "skill")
    for item in case["files"]:
        destination = workspace / "inputs" / safe_relative(item["path"])
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(item["content"], encoding="utf-8")
    return case_prompt(case)


def case_prompt(case: dict) -> str:
    return (
        "Use the clear-decision-communication skill in skill/SKILL.md and its "
        "references to handle the request below. Read the supplied raw files in inputs/. "
        "This is a self-contained simulation: the supplied project facts are the "
        "scenario baseline, not claims about any live project. Read only files under "
        "this working directory. Do not browse or inspect other projects or sessions. "
        "Produce the next user-facing response and identify the immediate next action "
        "you would take. Do not perform external actions or mutations. If the scenario "
        "calls for an unavailable action or question tool, describe that action or "
        "show its proposed payload rather than claiming to have executed it.\n\n"
        + case["prompt"]
        + "\n"
    )


def completed_response(tool: str, directory: Path, capture: dict | None = None) -> tuple[str, dict]:
    """Extract a complete visible response, retaining its event provenance."""
    capture = capture if capture is not None else {
        name: (directory / name).read_bytes() for name in ("process.json", "stdout.jsonl")
    }
    process = json.loads(capture["process.json"])
    if not isinstance(process, dict) or process.get("status") != "completed" or process.get("exit_code") != 0:
        raise ValueError("response capture did not complete successfully")
    raw = capture["stdout.jsonl"]
    final = None
    completed = False
    for number, line in enumerate(raw.decode("utf-8").splitlines(), 1):
        if not line.strip():
            continue
        event = json.loads(line)
        if not isinstance(event, dict):
            raise ValueError("CLI event must be an object")
        if tool == "claude" and event.get("type") == "result":
            if event.get("is_error") or event.get("subtype") != "success":
                raise ValueError("Claude result is not successful")
            final = (number, event.get("result"))
            completed = True
        if tool == "codex":
            if event.get("type") in {"error", "turn.failed"}:
                raise ValueError("Codex reported a failed turn")
            if event.get("type") == "turn.started":
                completed = False
                final = None
            if event.get("type") == "turn.completed":
                completed = True
            item = event.get("item", {})
            if event.get("type") == "item.completed" and not isinstance(item, dict):
                raise ValueError("Codex completed item must be an object")
            if event.get("type") == "item.completed" and item.get("type") == "agent_message":
                completed = False
                final = (number, item.get("text"))
    if not completed or final is None or not isinstance(final[1], str) or not final[1].strip():
        raise ValueError("no complete final response found")
    number, response = final
    return response, {
        "response_line": number,
        "stdout_sha256": hashlib.sha256(raw).hexdigest(),
        "response_sha256": hashlib.sha256(response.encode("utf-8")).hexdigest(),
        "extraction": "Claude success result" if tool == "claude" else "last completed Codex agent_message in a completed turn",
    }


def validate_drafts(run: Path, selected: list[dict], tools: list[str], hashes: dict) -> dict:
    """Validate every requested baseline before invoking any new model process."""
    manifest = json.loads((run / "manifest.json").read_text(encoding="utf-8"))
    if not isinstance(manifest, dict) or not isinstance(manifest.get("runs"), list):
        raise ValueError("retained draft manifest is invalid")
    actual = {
        relative.as_posix(): hashlib.sha256(data).hexdigest()
        for relative, data in instruction_files(run / "skill")
    }
    if manifest.get("source_hashes") != hashes or actual != hashes:
        raise ValueError("retained draft instruction files do not match the current snapshot")
    retained = {}
    for tool in tools:
        for case in selected:
            if not any(
                isinstance(item, dict) and item.get("tool") == tool and item.get("case_id") == case["id"]
                and item.get("process_status") == "completed"
                for item in manifest.get("runs", [])
            ):
                raise ValueError(f"retained manifest has no completed {tool} case {case['id']}")
            directory = run / tool / f"case-{case['id']:02d}"
            expected = {safe_relative(item["path"]): item["content"].encode("utf-8") for item in case["files"]}
            found = {
                path.relative_to(directory / "inputs"): path.read_bytes()
                for path in (directory / "inputs").rglob("*") if path.is_file()
            }
            if found != expected:
                raise ValueError(f"retained {tool} case {case['id']} raw inputs differ")
            capture = {
                name: (directory / name).read_bytes()
                for name in ("prompt.txt", "stdout.jsonl", "stderr.txt", "process.json")
            }
            if capture["prompt.txt"] != case_prompt(case).encode("utf-8"):
                raise ValueError(f"retained {tool} case {case['id']} prompt differs")
            response, provenance = completed_response(tool, directory, capture)
            # Freeze all capture bytes now; later changes to the prior run cannot alter the pair.
            retained[tool, case["id"]] = (directory, response, provenance, capture)
    return retained


def command_for(tool: str, executable: str, workspace: Path) -> list[str]:
    if tool == "claude":
        return [
            executable, "--print", "--safe-mode", "--restricted",
            "--strict-mcp-config", "--mcp-config", '{"mcpServers":{}}',
            "--tools", "Read,Glob,Grep", "--allowedTools", "Read,Glob,Grep",
            "--permission-mode", "dontAsk", "--permission-prompts", "none",
            "--no-session-persistence", "--output-format", "stream-json", "--verbose",
        ]
    command = [
        executable, "exec", "--strict-config", "--ignore-user-config", "--ephemeral",
        "--skip-git-repo-check", "--sandbox", "read-only", "--color", "never", "--json",
        "-C", str(workspace), "-c", 'approval_policy="never"', "-c", "project_doc_max_bytes=0",
        "-c", 'web_search="disabled"', "--enable", "skip_host_skill_discovery",
    ]
    for feature in (
        "plugins", "remote_plugin", "hooks", "memories", "apps", "multi_agent",
        "multi_agent_v2", "browser_use", "computer_use", "image_generation",
        "skill_search", "skill_mcp_dependency_install",
    ):
        command.extend(["--disable", feature])
    return command + ["-"]


def run_bounded(
    command: list[str], cwd: Path, input_path: Path, stdout_path: Path,
    stderr_path: Path, timeout: float, max_bytes: int,
) -> dict:
    """Capture bounded output and kill the spawned process group on interruption."""
    started = time.monotonic()
    result = {
        "status": "starting", "exit_code": None,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "command": command, "working_directory": str(cwd),
        "output_limit_bytes": max_bytes, "timeout_seconds": timeout,
    }
    process = None
    captured = 0
    try:
        with input_path.open("rb") as incoming, stdout_path.open("wb") as stdout, \
                stderr_path.open("wb") as stderr, selectors.DefaultSelector() as ready:
            process = subprocess.Popen(
                command, cwd=cwd, stdin=incoming, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, start_new_session=True,
            )
            ready.register(process.stdout, selectors.EVENT_READ, stdout)
            ready.register(process.stderr, selectors.EVENT_READ, stderr)
            result["status"] = "completed"
            while ready.get_map() or process.poll() is None:
                if time.monotonic() - started >= timeout:
                    result["status"] = "timeout"
                    break
                overflow = False
                for event, _ in ready.select(timeout=min(0.1, timeout)):
                    data = os.read(event.fileobj.fileno(), 65536)
                    if not data:
                        ready.unregister(event.fileobj)
                        event.fileobj.close()
                        continue
                    remaining = max_bytes - captured
                    event.data.write(data[:remaining])
                    captured += min(len(data), remaining)
                    if len(data) > remaining:
                        result["status"] = "output_limit"
                        overflow = True
                        break
                if overflow:
                    break
    except OSError as error:
        result.update(status="process_error", error=str(error))
    except KeyboardInterrupt:
        result["status"] = "interrupted"
    finally:
        if process is not None:
            # poll() reaps normal completion; that PID may then be reused.
            # An unreaped leader still reserves its PID while we stop its group.
            if process.returncode is None:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            result["exit_code"] = process.wait()
            for stream in (process.stdout, process.stderr):
                if stream is not None:
                    stream.close()
        result["duration_seconds"] = round(time.monotonic() - started, 3)
        result["captured_bytes"] = captured
    return result


def review_record(case: dict) -> dict:
    return {
        "case_id": case["id"], "name": case["name"],
        "covered_findings": case["covered_findings"],
        "semantic_verdict": "not_reviewed", "reviewer": None, "summary": None,
        "verdict_choices": ["pass", "fail", "inconclusive"],
        "criteria": [
            {"expectation": expectation, "met": None, "evidence": None}
            for expectation in case["expectations"]
        ],
    }


def source_report(response: str, draft: str, sources: dict[str, str]) -> dict:
    """Validate report structure and exact quotations, not semantic correctness."""
    text = response.strip()
    try:
        report = json.loads(text)
    except json.JSONDecodeError:
        # Accept one fenced payload, never search prose for a parseable JSON fragment.
        lines = text.splitlines(keepends=True)
        fences = [
            index for index, line in enumerate(lines)
            if line.lstrip().startswith(("```", "~~~"))
        ]
        if len(fences) != 2:
            raise ValueError("reviewer report needs one complete JSON fence")
        start, end = fences
        opening, closing = lines[start].rstrip("\r\n"), lines[end].rstrip("\r\n")
        if opening not in {"```", "```json"} or closing != "```":
            raise ValueError("reviewer report has an invalid JSON fence")
        outside = ("".join(lines[:start]), "".join(lines[end + 1:]))
        if any(part.strip() for part in outside) and opening != "```json":
            raise ValueError("a reviewer report surrounded by prose needs a json fence")
        for part in outside:
            if (
                any(character in part for character in "{}[]")
                or "``" in part or "~~~" in part or part.count("`") % 2
            ):
                raise ValueError("reviewer report has ambiguous content outside its JSON fence")
        # Preserve payload characters; exact source and draft matching still applies below.
        report = json.loads("".join(lines[start + 1:end]))
    if not isinstance(report, dict) or set(report) != {"schema_version", "findings", "supported_claims"}:
        raise ValueError("reviewer report has unexpected fields")
    if type(report["schema_version"]) is not int or report["schema_version"] != 1:
        raise ValueError("unsupported reviewer report schema")
    findings, supported = report["findings"], report["supported_claims"]
    if not isinstance(findings, list) or not isinstance(supported, list) or not (findings or supported):
        raise ValueError("report needs findings or supported claims")

    def nonempty(value):
        return isinstance(value, str) and bool(value.strip())

    def references(item, require_source):
        excerpt = item.get("draft_excerpt")
        if excerpt is None:
            if item.get("kind") != "omitted":
                raise ValueError("only an omission may have no draft excerpt")
        elif not nonempty(excerpt) or excerpt not in draft:
            raise ValueError("reviewer draft excerpt does not match the captured draft")
        citations = item.get("sources")
        if not isinstance(citations, list) or (require_source and not citations):
            raise ValueError("supported claim needs source references")
        for citation in citations:
            if not isinstance(citation, dict) or set(citation) != {"path", "excerpt"}:
                raise ValueError("invalid source reference")
            path, quote = citation["path"], citation["excerpt"]
            if not isinstance(path, str) or path not in sources or not nonempty(quote) or quote not in sources[path]:
                raise ValueError("reviewer source path or excerpt does not match a supplied source")

    ids = set()
    for finding in findings:
        required = {"id", "kind", "draft_excerpt", "sources", "reason", "repair"}
        if not isinstance(finding, dict) or set(finding) != required:
            raise ValueError("invalid reviewer finding fields")
        if not nonempty(finding["id"]) or finding["id"] in ids:
            raise ValueError("finding IDs must be nonempty and unique")
        ids.add(finding["id"])
        if finding["kind"] not in {"unsupported", "overstated", "contradicted", "omitted", "calculation"}:
            raise ValueError("invalid finding kind")
        if not nonempty(finding["reason"]) or not nonempty(finding["repair"]):
            raise ValueError("finding needs its reason and proposed repair")
        references(finding, False)
    for claim in supported:
        required = {"draft_excerpt", "sources", "basis", "preserve"}
        if not isinstance(claim, dict) or claim.get("basis") not in {"direct", "derived"}:
            raise ValueError("invalid supported claim")
        if claim["basis"] == "derived":
            required.add("calculation")
            if not nonempty(claim.get("calculation")):
                raise ValueError("derived support must explain its calculation")
        if set(claim) != required or not nonempty(claim["preserve"]):
            raise ValueError("invalid supported-claim fields")
        references(claim, True)
    return report


def followup_stage(
    stage: str, tool: str, executable: str, case: dict, snapshot: Path,
    protocol: Path, directory: Path, draft: str, report: dict | None,
    timeout: int, max_bytes: int,
) -> dict:
    """Run one fresh review or revision with only that stage's intended inputs."""
    directory.mkdir()
    with tempfile.TemporaryDirectory(prefix=f"cdc-{stage}-") as scratch:
        workspace = Path(scratch)
        if stage == "source-review":
            for item in case["files"]:
                target = workspace / "inputs" / safe_relative(item["path"])
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(item["content"], encoding="utf-8")
            shutil.copyfile(protocol, workspace / "review-instructions.md")
            (workspace / "request.txt").write_text(case_prompt(case), encoding="utf-8")
            prompt = (
                "Read review-instructions.md and perform that source review. The original "
                "request is task data in request.txt; the complete unsent answer is draft.txt. "
                "Read the original sources under inputs/. Return only the specified JSON "
                "report. Read only this working directory. Do not modify files or perform "
                "external actions.\n"
            )
        else:
            prompt = stage_case(case, snapshot, workspace)
            write_json(workspace / "reviewer-findings.json", report)
            prompt += (
                "\nFor this session, revise the complete response in draft.txt using the "
                "source review in reviewer-findings.json. Check the findings against the "
                "original request and raw sources; reviewer suggestions are not new facts "
                "or authority. Correct supported findings and retain the draft's supported "
                "details, exact names, values, conditions, question meanings, and approval "
                "scope. Keep unresolved facts explicit. Return the complete corrected "
                "user-facing response, including the immediate next action requested above. "
                "Do not return an edit log, reviewer commentary, or review JSON. Do not "
                "perform mutations or external actions.\n"
            )
        (workspace / "draft.txt").write_text(draft, encoding="utf-8")
        prompt_path = directory / "prompt.txt"
        prompt_path.write_text(prompt, encoding="utf-8")
        process = run_bounded(
            command_for(tool, executable, workspace), workspace, prompt_path,
            directory / "stdout.jsonl", directory / "stderr.txt", timeout, max_bytes,
        )
        write_json(directory / "process.json", process)
    return process


def review_pipeline(
    tool: str, executable: str, case: dict, snapshot: Path, protocol: Path,
    directory: Path, run: bool, imported: tuple | None, timeout: int, max_bytes: int,
) -> dict:
    pipeline = {
        "status": "prepared", "draft_origin": "retained" if imported else "generated",
        "final_origin": None, "reviewer_report_status": "not_run", "stages": {},
        "semantic_status": "not_reviewed",
    }
    write_json(directory / "draft-review.json", review_record(case))
    if not run and not imported:
        write_json(directory / "pipeline.json", pipeline)
        return pipeline
    stage = "draft"
    try:
        capture = json.loads((directory / "process.json").read_text(encoding="utf-8"))
        if isinstance(capture, dict):
            pipeline["stages"]["draft"] = capture.get("status")
            if capture.get("status") == "interrupted":
                pipeline["status"] = "interrupted"
                return pipeline
        draft, provenance = completed_response(tool, directory)
        if imported:
            if draft != imported[1] or provenance != imported[2]:
                raise ValueError("retained response changed after preflight validation")
            if (directory / "prompt.txt").read_bytes() != case_prompt(case).encode("utf-8"):
                raise ValueError("retained prompt changed after preflight validation")
            provenance["retained_run"] = imported[0].parent.parent.name
            provenance["capture_sha256"] = {
                name: hashlib.sha256(data).hexdigest() for name, data in imported[3].items()
            }
        write_json(directory / "draft-provenance.json", provenance)
        (directory / "draft.txt").write_text(draft, encoding="utf-8")
        pipeline["stages"]["draft"] = "completed"
        if not run:
            return pipeline
        stage = "source-review"
        process = followup_stage(
            stage, tool, executable, case, snapshot, protocol, directory / stage,
            draft, None, timeout, max_bytes,
        )
        pipeline["stages"][stage] = process["status"]
        if process["status"] == "interrupted":
            pipeline["status"] = "interrupted"
            return pipeline
        response, provenance = completed_response(tool, directory / stage)
        (directory / stage / "response.txt").write_text(response, encoding="utf-8")
        write_json(directory / stage / "response-provenance.json", provenance)
        pipeline["reviewer_report_status"] = "invalid"
        sources = {"request.txt": case_prompt(case)}
        sources.update({f"inputs/{safe_relative(item['path']).as_posix()}": item["content"] for item in case["files"]})
        report = source_report(response, draft, sources)
        write_json(directory / stage / "report.json", report)
        pipeline["reviewer_report_status"] = "valid"
        pipeline["finding_count"] = len(report["findings"])
        final, origin = draft, "draft"
        if report["findings"]:
            stage = "revision"
            process = followup_stage(
                stage, tool, executable, case, snapshot, protocol, directory / stage,
                draft, report, timeout, max_bytes,
            )
            pipeline["stages"][stage] = process["status"]
            if process["status"] == "interrupted":
                pipeline["status"] = "interrupted"
                return pipeline
            final, provenance = completed_response(tool, directory / stage)
            (directory / stage / "response.txt").write_text(final, encoding="utf-8")
            write_json(directory / stage / "response-provenance.json", provenance)
            origin = "revision"
        (directory / "final.txt").write_text(final, encoding="utf-8")
        pipeline.update(status="completed", final_origin=origin)
    except (OSError, ValueError, TypeError, KeyError) as error:
        pipeline.update(status="blocked", blocked_stage=stage, error=str(error))
    finally:
        write_json(directory / "pipeline.json", pipeline)
    return pipeline


def positive(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be at least 1")
    return parsed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--tool", choices=["claude", "codex", "both"], default="both")
    parser.add_argument("--cases", type=positive, nargs="+", help="case IDs; default: all")
    parser.add_argument("--output", type=Path, required=True, help="new durable records directory")
    parser.add_argument("--timeout", type=positive, default=120, help="seconds per model call")
    parser.add_argument("--max-output-bytes", type=positive, default=1048576)
    parser.add_argument("--run", action="store_true", help="invoke CLIs; default only prepares records")
    parser.add_argument("--source-review", action="store_true", help="review the draft in a fresh session, then revise once if needed")
    parser.add_argument("--drafts-from", type=Path, help="reuse matching completed writer captures from a prior run; requires --source-review")
    args = parser.parse_args(argv)
    if args.drafts_from and not args.source_review:
        parser.error("--drafts-from requires --source-review")
    cases = read_cases(SKILL_DIR / "evals/evals.json")
    requested = set(args.cases or [case["id"] for case in cases])
    unknown = requested - {case["id"] for case in cases}
    if unknown:
        parser.error(f"unknown case IDs: {sorted(unknown)}")
    selected = [case for case in cases if case["id"] in requested]
    tools = ["claude", "codex"] if args.tool == "both" else [args.tool]
    hashes = {
        relative.as_posix(): hashlib.sha256(data).hexdigest()
        for relative, data in instruction_files(SKILL_DIR)
    }
    retained = {}
    try:
        if args.drafts_from:
            args.drafts_from = args.drafts_from.expanduser().resolve()
            retained = validate_drafts(args.drafts_from, selected, tools, hashes)
        protocol_bytes = REVIEW_INSTRUCTIONS.read_bytes() if args.source_review else None
    except (OSError, ValueError, TypeError, KeyError) as error:
        parser.error(f"source-review preflight: {error}")
    output = args.output.expanduser().resolve()
    if output.exists():
        parser.error("--output must not already exist; preserve prior evidence with a new directory")
    output.mkdir(parents=True)
    snapshot = output / "skill"
    snapshotted = snapshot_skill(SKILL_DIR, snapshot)
    if snapshotted != hashes:
        parser.error("instruction files changed during snapshot preparation")
    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(), "skill": "clear-decision-communication",
        "source_hashes": snapshotted,
        "cases": sorted(requested), "mode": "run" if args.run else "prepare",
        "semantic_status": "not_reviewed", "runs": [],
        "source_review": args.source_review,
        "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    protocol = output / "source-review.md"
    if protocol_bytes is not None:
        protocol.write_bytes(protocol_bytes)
        manifest["source_review_sha256"] = hashlib.sha256(protocol_bytes).hexdigest()
        if args.drafts_from:
            manifest["drafts_from"] = str(args.drafts_from)
        # Both paired answers use these frozen criteria; none enter model workspaces.
        write_json(output / "cases.json", selected)
        manifest["cases_sha256"] = hashlib.sha256((output / "cases.json").read_bytes()).hexdigest()
    write_json(output / "manifest.json", manifest)
    failure = False
    for tool in tools:
        executable = shutil.which(tool)
        tool_dir = output / tool
        tool_dir.mkdir()
        if args.run:
            # --version is recorded separately; no credential files or environment dump.
            blank = tool_dir / "version.stdin.txt"
            blank.write_text("", encoding="utf-8")
            version = run_bounded(
                [executable or tool, "--version"], tool_dir, blank,
                tool_dir / "version.stdout.txt", tool_dir / "version.stderr.txt", 10, 65536,
            )
            write_json(tool_dir / "version.process.json", version)
            if version["status"] == "interrupted":
                write_json(output / "manifest.json", manifest)
                return 130
        for case in selected:
            case_dir = tool_dir / f"case-{case['id']:02d}"
            case_dir.mkdir()
            write_json(case_dir / "review.json", review_record(case))
            imported = retained.get((tool, case["id"]))
            with tempfile.TemporaryDirectory(prefix="cdc-eval-") as scratch:
                workspace = Path(scratch)
                prompt = stage_case(case, snapshot, workspace)
                prompt_path = case_dir / "prompt.txt"
                prompt_path.write_text(prompt, encoding="utf-8")
                shutil.copytree(workspace / "inputs", case_dir / "inputs")
                command = command_for(tool, executable or tool, workspace)
                process = {"status": "not_run", "exit_code": None, "command": command}
                if imported:
                    for name, data in imported[3].items():
                        (case_dir / name).write_bytes(data)
                    process = json.loads((case_dir / "process.json").read_text(encoding="utf-8"))
                elif args.run:
                    process = run_bounded(
                        command, workspace, prompt_path, case_dir / "stdout.jsonl",
                        case_dir / "stderr.txt", args.timeout, args.max_output_bytes,
                    )
                if not imported:
                    write_json(case_dir / "process.json", process)
            result = {"tool": tool, "case_id": case["id"], "process_status": process["status"]}
            pipeline = None
            if args.source_review:
                pipeline = review_pipeline(
                    tool, executable or tool, case, snapshot, protocol, case_dir,
                    args.run, imported, args.timeout, args.max_output_bytes,
                )
                result["pipeline_status"] = pipeline["status"]
                result["draft_origin"] = pipeline["draft_origin"]
            manifest["runs"].append(result)
            write_json(output / "manifest.json", manifest)
            if pipeline:
                print(
                    f"{tool} case {case['id']}: draft={pipeline['draft_origin']}; "
                    f"capture={process['status']}; pipeline={pipeline['status']}; semantic=not_reviewed",
                    flush=True,
                )
            else:
                print(f"{tool} case {case['id']}: process={process['status']}; semantic=not_reviewed", flush=True)
            if args.run and (process["status"] != "completed" or process["exit_code"] != 0):
                failure = True
            if pipeline:
                if pipeline["status"] in {"blocked", "interrupted"}:
                    failure = True
            if process["status"] == "interrupted" or (pipeline and pipeline["status"] == "interrupted"):
                return 130
    print(f"Records: {output}. Review actual outputs before assigning behavioral verdicts.")
    return 1 if failure else 0


if __name__ == "__main__":
    raise SystemExit(main())
