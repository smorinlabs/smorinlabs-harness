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
from pathlib import Path, PurePosixPath
import selectors
import shutil
import signal
import subprocess
import tempfile
import time


SKILL_DIR = Path(__file__).resolve().parent.parent


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def safe_relative(value: str) -> Path:
    path = PurePosixPath(value)
    if not value or path.is_absolute() or any(p in {".", ".."} for p in value.split("/")):
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


def snapshot_skill(source: Path, target: Path) -> dict[str, str]:
    """Copy only skill instructions and references; never copy the eval directory."""
    paths = [source / "SKILL.md", source / "references"]
    paths.extend(sorted((source / "references").rglob("*")))
    hashes = {}
    for path in paths:
        if path.is_symlink():
            raise ValueError(f"Skill snapshots do not follow symlinks: {path}")
        if path.is_dir():
            continue
        if not path.is_file():
            raise ValueError(f"Expected a regular skill file: {path}")
        relative = path.relative_to(source)
        data = path.read_bytes()
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
            # Descendants can retain pipes after the CLI exits; kill the whole new group.
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
    args = parser.parse_args(argv)
    cases = read_cases(SKILL_DIR / "evals/evals.json")
    requested = set(args.cases or [case["id"] for case in cases])
    unknown = requested - {case["id"] for case in cases}
    if unknown:
        parser.error(f"unknown case IDs: {sorted(unknown)}")
    selected = [case for case in cases if case["id"] in requested]
    output = args.output.expanduser().resolve()
    if output.exists():
        parser.error("--output must not already exist; preserve prior evidence with a new directory")
    output.mkdir(parents=True)
    snapshot = output / "skill"
    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(), "skill": "clear-decision-communication",
        "source_hashes": snapshot_skill(SKILL_DIR, snapshot),
        "cases": sorted(requested), "mode": "run" if args.run else "prepare",
        "semantic_status": "not_reviewed", "runs": [],
    }
    tools = ["claude", "codex"] if args.tool == "both" else [args.tool]
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
            with tempfile.TemporaryDirectory(prefix="cdc-eval-") as scratch:
                workspace = Path(scratch)
                prompt = stage_case(case, snapshot, workspace)
                prompt_path = case_dir / "prompt.txt"
                prompt_path.write_text(prompt, encoding="utf-8")
                shutil.copytree(workspace / "inputs", case_dir / "inputs")
                command = command_for(tool, executable or tool, workspace)
                process = {"status": "not_run", "exit_code": None, "command": command}
                if args.run:
                    process = run_bounded(
                        command, workspace, prompt_path, case_dir / "stdout.jsonl",
                        case_dir / "stderr.txt", args.timeout, args.max_output_bytes,
                    )
                write_json(case_dir / "process.json", process)
            manifest["runs"].append({"tool": tool, "case_id": case["id"], "process_status": process["status"]})
            write_json(output / "manifest.json", manifest)
            print(f"{tool} case {case['id']}: process={process['status']}; semantic=not_reviewed", flush=True)
            if args.run and (process["status"] != "completed" or process["exit_code"] != 0):
                failure = True
            if process["status"] == "interrupted":
                return 130
    print(f"Records: {output}. Review actual outputs before assigning behavioral verdicts.")
    return 1 if failure else 0


if __name__ == "__main__":
    raise SystemExit(main())
