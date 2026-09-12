"""Exercise the evaluation runner with local fake processes, never model calls."""

import importlib.util
import json
from pathlib import Path
import sys
import time

import pytest


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "plugins/clear-decision-communication/skills/clear-decision-communication/evals/run_evals.py"
)
SPEC = importlib.util.spec_from_file_location("decision_eval_runner", SCRIPT)
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)


def case():
    return {
        "id": 1,
        "name": "case-name-for-review-only",
        "prompt": "Continue the conversation.",
        "files": [{"path": "handoff.md", "content": "Raw project fact."}],
        "covered_findings": ["CDC-01"],
        "expectations": ["SECRET_GRADER_EXPECTATION"],
    }


@pytest.fixture
def source(tmp_path):
    skill = tmp_path / "source"
    (skill / "references").mkdir(parents=True)
    (skill / "SKILL.md").write_text("Use the references.")
    (skill / "references/delivery.md").write_text("A source delivery rule.")
    (skill / "evals").mkdir()
    (skill / "evals/evals.json").write_text(json.dumps({"evals": [case()]}))
    return skill


def test_staged_context_excludes_grader_and_other_skill_files(source, tmp_path):
    (source / "unrelated.txt").write_text("DO_NOT_EXPOSE")
    snapshot = tmp_path / "snapshot"
    hashes = runner.snapshot_skill(source, snapshot)
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    prompt = runner.stage_case(case(), snapshot, workspace)
    exposed = [p for p in workspace.rglob("*") if p.is_file()]
    assert {p.relative_to(workspace).as_posix() for p in exposed} == {
        "skill/SKILL.md", "skill/references/delivery.md", "inputs/handoff.md",
    }
    content = prompt + "".join(p.read_text() for p in exposed)
    for secret in ("SECRET_GRADER_EXPECTATION", "case-name-for-review-only", "CDC-01", "DO_NOT_EXPOSE"):
        assert secret not in content
    assert set(hashes) == {"SKILL.md", "references/delivery.md"}


@pytest.mark.parametrize("path", [
    "../review.json", "/tmp/escape", "a/../../escape", "./file", "",
    r"..\review.json", r"C:\escape", "C:/escape", "D:escape",
    r"\escape", r"\\server\share\escape",
])
def test_input_paths_cannot_escape_the_scenario(path):
    with pytest.raises(ValueError):
        runner.safe_relative(path)


def test_snapshot_refuses_a_symlink_to_grader_content(source, tmp_path):
    (source / "references/leak.md").symlink_to(source / "evals/evals.json")
    with pytest.raises(ValueError, match="symlinks"):
        runner.snapshot_skill(source, tmp_path / "snapshot")


def test_prepare_makes_no_executable_calls_and_preserves_expectations(source, tmp_path, monkeypatch):
    monkeypatch.setattr(runner, "SKILL_DIR", source)

    def unexpected_call(*args, **kwargs):
        pytest.fail("Preparation must not invoke a CLI, including --version")

    monkeypatch.setattr(runner.subprocess, "Popen", unexpected_call)
    output = tmp_path / "records"
    assert runner.main(["--tool", "codex", "--output", str(output)]) == 0
    process = json.loads((output / "codex/case-01/process.json").read_text())
    review = json.loads((output / "codex/case-01/review.json").read_text())
    assert process["status"] == "not_run"
    assert process["exit_code"] is None
    assert review["semantic_verdict"] == "not_reviewed"
    assert review["criteria"][0]["expectation"] == "SECRET_GRADER_EXPECTATION"
    assert review["criteria"][0]["met"] is None


def test_zero_exit_does_not_grade_the_model_response(source, tmp_path, monkeypatch):
    monkeypatch.setattr(runner, "SKILL_DIR", source)
    executable = tmp_path / "fake-codex"
    executable.write_text(
        f"#!{sys.executable}\n"
        "import sys\n"
        "if '--version' in sys.argv: print('fake CLI version 1')\n"
        "else: print('I ignored the user and did something unrelated.')\n"
    )
    executable.chmod(0o700)
    monkeypatch.setattr(runner.shutil, "which", lambda tool: str(executable))
    output = tmp_path / "records"
    assert runner.main(["--tool", "codex", "--output", str(output), "--run"]) == 0
    process = json.loads((output / "codex/case-01/process.json").read_text())
    review = json.loads((output / "codex/case-01/review.json").read_text())
    assert process["status"] == "completed"
    assert process["exit_code"] == 0
    assert review["semantic_verdict"] == "not_reviewed"
    assert all(item["met"] is None and item["evidence"] is None for item in review["criteria"])
    assert "fake CLI version 1" in (output / "codex/version.stdout.txt").read_text()
    assert not Path(process["working_directory"]).exists()


def capture(tmp_path, code, timeout=2, max_bytes=4096):
    incoming = tmp_path / "prompt.txt"
    incoming.write_text("scenario")
    stdout, stderr = tmp_path / "stdout", tmp_path / "stderr"
    result = runner.run_bounded(
        [sys.executable, "-c", code], tmp_path, incoming,
        stdout, stderr, timeout, max_bytes,
    )
    return result, stdout, stderr


def test_nonzero_exit_and_both_output_streams_are_preserved(tmp_path):
    result, stdout, stderr = capture(
        tmp_path, "import sys; print('partial answer'); print('failure', file=sys.stderr); sys.exit(7)"
    )
    assert result["status"] == "completed"
    assert result["exit_code"] == 7
    assert stdout.read_text() == "partial answer\n"
    assert stderr.read_text() == "failure\n"


@pytest.mark.parametrize("exit_code", [0, 7])
def test_completed_process_does_not_signal_a_reaped_group(tmp_path, monkeypatch, exit_code):
    signals = []
    monkeypatch.setattr(runner.os, "killpg", lambda pid, signal: signals.append((pid, signal)))
    result, stdout, _ = capture(
        tmp_path, f"import sys; print('finished'); sys.exit({exit_code})"
    )
    assert result["status"] == "completed"
    assert result["exit_code"] == exit_code
    assert stdout.read_text() == "finished\n"
    assert signals == []


def test_output_limit_bounds_captured_bytes_and_terminates_the_process(tmp_path):
    result, stdout, stderr = capture(
        tmp_path, "import os\nwhile True: os.write(1, b'x' * 65536)", max_bytes=1000
    )
    assert result["status"] == "output_limit"
    assert result["exit_code"] != 0
    assert stdout.stat().st_size + stderr.stat().st_size == 1000
    assert result["captured_bytes"] == 1000
    assert result["duration_seconds"] < 2


def test_timeout_kills_the_spawned_process_group(tmp_path):
    child_code = "import time; from pathlib import Path; time.sleep(0.7); Path('escaped').write_text('child survived')"
    parent_code = (
        "import subprocess, sys, time\n"
        f"subprocess.Popen([sys.executable, '-c', {child_code!r}])\n"
        "print('started', flush=True)\n"
        "time.sleep(10)\n"
    )
    result, stdout, _ = capture(tmp_path, parent_code, timeout=0.2)
    assert result["status"] == "timeout"
    assert result["exit_code"] != 0
    assert "started" in stdout.read_text()
    assert result["duration_seconds"] < 2
    time.sleep(0.8)
    assert not (tmp_path / "escaped").exists()


def test_case_suite_has_separate_expectations_and_covers_reviewed_behaviors():
    cases = runner.read_cases(SCRIPT.with_name("evals.json"))
    assert len(cases) == 22
    findings = {finding for item in cases for finding in item["covered_findings"]}
    behavioral_findings = (*range(1, 11), *range(13, 21))
    assert {f"CDC-{number:02}" for number in behavioral_findings} <= findings
    for item in cases:
        assert item["files"]
        assert item["expectations"]
        for criterion in item["expectations"]:
            assert criterion not in item["prompt"]
            assert all(criterion not in raw["content"] for raw in item["files"])


SOURCE_REVIEW_DRAFT = "Raw project fact.\n\n"
SOURCE_REVIEW_FLAWED_DRAFT = "Raw project fact.\n\nEvery run succeeds.\n"
SOURCE_REVIEW_REVISION = "Raw project fact.\n"


def source_review_report(with_findings=False):
    return {
        "schema_version": 1,
        "findings": [{
            "id": "F1", "kind": "unsupported",
            "draft_excerpt": "Every run succeeds.", "sources": [],
            "reason": "The supplied source does not establish every run's outcome.",
            "repair": "Remove the universal outcome claim.",
        }] if with_findings else [],
        "supported_claims": [{
            "draft_excerpt": "Raw project fact.",
            "sources": [{"path": "inputs/handoff.md", "excerpt": "Raw project fact."}],
            "basis": "direct", "preserve": "Retain the supplied project fact.",
        }],
    }


def fake_pipeline_processes(monkeypatch, replies, failure=None, incomplete_stage=None):
    """Record staged inputs and emit real CLI event shapes without spawning a CLI."""
    calls = []

    def unexpected_process(*args, **kwargs):
        pytest.fail("Pipeline tests must never execute a real process")

    monkeypatch.setattr(runner.subprocess, "Popen", unexpected_process)
    monkeypatch.setattr(runner.shutil, "which", lambda tool: f"/fake/{tool}")

    def bounded(command, cwd, input_path, stdout_path, stderr_path, timeout, max_bytes):
        if "--version" in command:
            stage = "version"
        elif stdout_path.parent.name in {"source-review", "revision"}:
            stage = stdout_path.parent.name
        else:
            stage = "writer"
        call = {
            "stage": stage, "workspace": cwd, "command": command,
            "prompt": input_path.read_text(),
            "files": {} if stage == "version" else {
                path.relative_to(cwd).as_posix(): path.read_text()
                for path in cwd.rglob("*") if path.is_file()
            },
        }
        calls.append(call)
        if stage == "version":
            output = "fake CLI version 1\n"
        else:
            assert stage in replies, f"Unexpected dependent model stage: {stage}"
            response = replies[stage]
            if not isinstance(response, str):
                response = json.dumps(response)
            progress = {"type": "text", "text": "PROGRESS_IS_NOT_THE_FINAL_RESPONSE"}
            if "--output-format" in command:
                events = [
                    {"type": "assistant", "message": {"content": [progress]}},
                    {"type": "assistant", "message": {"content": [
                        {"type": "text", "text": response},
                    ]}},
                ]
                if stage != incomplete_stage:
                    events.append({
                        "type": "result", "subtype": "success",
                        "is_error": False, "result": response,
                    })
            else:
                events = [
                    {"type": "item.completed", "item": {
                        "type": "agent_message", "text": progress["text"],
                    }},
                    {"type": "item.completed", "item": {
                        "type": "agent_message", "text": response,
                    }},
                ]
                if stage != incomplete_stage:
                    events.append({"type": "turn.completed", "usage": {}})
            output = "".join(json.dumps(event) + "\n" for event in events)
        stdout_path.write_text(output)
        stderr_path.write_text(f"fake {stage} stderr\n")
        status, exit_code = ("completed", 0)
        if failure and stage == failure[0]:
            status, exit_code = failure[1:]
        return {
            "status": status, "exit_code": exit_code,
            "command": command, "working_directory": str(cwd),
            "duration_seconds": 0.001,
            "captured_bytes": len(output.encode()) + stderr_path.stat().st_size,
            "timeout_seconds": timeout, "output_limit_bytes": max_bytes,
        }

    monkeypatch.setattr(runner, "run_bounded", bounded)
    return calls


def assert_pipeline_reviews_ungraded(case_dir):
    for name in ("draft-review.json", "review.json"):
        review = json.loads((case_dir / name).read_text())
        assert review["semantic_verdict"] == "not_reviewed"
        assert review["reviewer"] is None and review["summary"] is None
        assert all(c["met"] is None and c["evidence"] is None for c in review["criteria"])


def assert_pipeline_context_isolation(calls):
    model_calls = [call for call in calls if call["stage"] != "version"]
    workspaces = [call["workspace"] for call in model_calls]
    assert len(workspaces) == len(set(workspaces))
    assert all(not path.exists() for path in workspaces)
    for call in model_calls:
        exposed = call["prompt"] + "\n".join(call["files"]) + "\n".join(call["files"].values())
        for hidden in (
            "SECRET_GRADER_EXPECTATION", "case-name-for-review-only", "CDC-01",
            "PRIVATE_BASELINE_GRADE", "PRIVATE_BASELINE_REVIEWER", "NEW_PRIVATE_EXPECTATION",
        ):
            assert hidden not in exposed
        assert call["files"]["inputs/handoff.md"] == "Raw project fact."
        command = call["command"]
        if "--output-format" in command:
            assert command[command.index("--tools") + 1] == "Read,Glob,Grep"
            assert "--safe-mode" in command and "--restricted" in command
        else:
            assert command[command.index("--sandbox") + 1] == "read-only"
        if call["stage"] == "source-review":
            assert set(call["files"]) == {
                "review-instructions.md", "request.txt", "draft.txt", "inputs/handoff.md",
            }
        elif call["stage"] == "revision":
            assert set(call["files"]) == {
                "skill/SKILL.md", "skill/references/delivery.md", "inputs/handoff.md",
                "draft.txt", "reviewer-findings.json",
            }


@pytest.mark.parametrize("tool", ["claude", "codex"])
def test_source_review_is_opt_in(source, tmp_path, monkeypatch, tool):
    monkeypatch.setattr(runner, "SKILL_DIR", source)
    calls = fake_pipeline_processes(monkeypatch, {"writer": SOURCE_REVIEW_DRAFT})
    output = tmp_path / "default-records"
    assert runner.main(["--tool", tool, "--output", str(output), "--run"]) == 0
    case_dir = output / tool / "case-01"
    assert [call["stage"] for call in calls] == ["version", "writer"]
    assert not (case_dir / "source-review").exists()
    assert not (case_dir / "revision").exists()
    assert not (case_dir / "pipeline.json").exists()
    assert json.loads((case_dir / "review.json").read_text())["semantic_verdict"] == "not_reviewed"


def test_source_review_prepare_never_invokes_a_cli(source, tmp_path, monkeypatch):
    monkeypatch.setattr(runner, "SKILL_DIR", source)
    calls = fake_pipeline_processes(monkeypatch, {})
    output = tmp_path / "prepared-source-review"
    assert runner.main(["--tool", "codex", "--output", str(output), "--source-review"]) == 0
    assert calls == []
    case_dir = output / "codex/case-01"
    pipeline = json.loads((case_dir / "pipeline.json").read_text())
    assert pipeline["status"] == "prepared" and pipeline["final_origin"] is None
    assert not (case_dir / "final.txt").exists()
    assert json.loads((case_dir / "process.json").read_text())["status"] == "not_run"


def test_drafts_from_requires_source_review(source, tmp_path, monkeypatch):
    monkeypatch.setattr(runner, "SKILL_DIR", source)
    calls = fake_pipeline_processes(monkeypatch, {})
    with pytest.raises(SystemExit) as error:
        runner.main([
            "--tool", "codex", "--output", str(tmp_path / "invalid"),
            "--drafts-from", str(tmp_path / "prior"), "--run",
        ])
    assert error.value.code == 2
    assert calls == []


@pytest.mark.parametrize("tool", ["claude", "codex"])
def test_source_review_no_findings_retains_the_exact_draft(source, tmp_path, monkeypatch, tool):
    monkeypatch.setattr(runner, "SKILL_DIR", source)
    report = source_review_report()
    calls = fake_pipeline_processes(monkeypatch, {
        "writer": SOURCE_REVIEW_DRAFT, "source-review": report,
    })
    output = tmp_path / "reviewed"
    assert runner.main(["--tool", tool, "--output", str(output), "--source-review", "--run"]) == 0
    case_dir = output / tool / "case-01"
    assert [c["stage"] for c in calls if c["stage"] != "version"] == ["writer", "source-review"]
    assert (case_dir / "draft.txt").read_text() == SOURCE_REVIEW_DRAFT
    assert (case_dir / "final.txt").read_bytes() == (case_dir / "draft.txt").read_bytes()
    assert json.loads((case_dir / "source-review/report.json").read_text()) == report
    pipeline = json.loads((case_dir / "pipeline.json").read_text())
    assert pipeline["status"] == "completed" and pipeline["final_origin"] == "draft"
    assert not (case_dir / "revision").exists()
    reviewer = next(c for c in calls if c["stage"] == "source-review")
    assert reviewer["files"]["request.txt"] == (case_dir / "prompt.txt").read_text()
    assert reviewer["files"]["draft.txt"] == SOURCE_REVIEW_DRAFT
    assert_pipeline_reviews_ungraded(case_dir)
    assert_pipeline_context_isolation(calls)


@pytest.mark.parametrize("tool", ["claude", "codex"])
def test_source_review_findings_trigger_one_fresh_revision(source, tmp_path, monkeypatch, tool):
    monkeypatch.setattr(runner, "SKILL_DIR", source)
    report = source_review_report(with_findings=True)
    calls = fake_pipeline_processes(monkeypatch, {
        "writer": SOURCE_REVIEW_FLAWED_DRAFT, "source-review": report,
        "revision": SOURCE_REVIEW_REVISION,
    })
    output = tmp_path / "revised"
    assert runner.main(["--tool", tool, "--output", str(output), "--source-review", "--run"]) == 0
    case_dir = output / tool / "case-01"
    assert [c["stage"] for c in calls if c["stage"] != "version"] == [
        "writer", "source-review", "revision",
    ]
    assert (case_dir / "draft.txt").read_text() == SOURCE_REVIEW_FLAWED_DRAFT
    assert (case_dir / "revision/response.txt").read_text() == SOURCE_REVIEW_REVISION
    assert (case_dir / "final.txt").read_text() == SOURCE_REVIEW_REVISION
    pipeline = json.loads((case_dir / "pipeline.json").read_text())
    assert pipeline["status"] == "completed" and pipeline["final_origin"] == "revision"
    revision = next(c for c in calls if c["stage"] == "revision")
    assert revision["files"]["draft.txt"] == SOURCE_REVIEW_FLAWED_DRAFT
    assert json.loads(revision["files"]["reviewer-findings.json"]) == report
    assert_pipeline_reviews_ungraded(case_dir)
    assert_pipeline_context_isolation(calls)


@pytest.mark.parametrize("tool", ["claude", "codex"])
def test_source_review_paired_reuse_skips_writer_and_prior_grades(source, tmp_path, monkeypatch, tool):
    monkeypatch.setattr(runner, "SKILL_DIR", source)
    prior = tmp_path / "prior"
    fake_pipeline_processes(monkeypatch, {"writer": SOURCE_REVIEW_DRAFT})
    assert runner.main(["--tool", tool, "--output", str(prior), "--run"]) == 0
    prior_case = prior / tool / "case-01"
    old_review = json.loads((prior_case / "review.json").read_text())
    old_review.update(semantic_verdict="fail", reviewer="PRIVATE_BASELINE_REVIEWER", summary="PRIVATE_BASELINE_GRADE")
    (prior_case / "review.json").write_text(json.dumps(old_review))
    original = {p.relative_to(prior): p.read_bytes() for p in prior.rglob("*") if p.is_file()}
    updated_case = case()
    updated_case["expectations"].append("NEW_PRIVATE_EXPECTATION")
    (source / "evals/evals.json").write_text(json.dumps({"evals": [updated_case]}))
    calls = fake_pipeline_processes(monkeypatch, {"source-review": source_review_report()})
    output = tmp_path / "paired"
    assert runner.main([
        "--tool", tool, "--output", str(output), "--source-review", "--drafts-from", str(prior), "--run",
    ]) == 0
    case_dir = output / tool / "case-01"
    assert [c["stage"] for c in calls if c["stage"] != "version"] == ["source-review"]
    for name in ("prompt.txt", "stdout.jsonl", "process.json"):
        assert (case_dir / name).read_bytes() == (prior_case / name).read_bytes()
    assert (case_dir / "draft.txt").read_text() == SOURCE_REVIEW_DRAFT
    assert (case_dir / "final.txt").read_text() == SOURCE_REVIEW_DRAFT
    assert {p.relative_to(prior): p.read_bytes() for p in prior.rglob("*") if p.is_file()} == original
    assert_pipeline_reviews_ungraded(case_dir)
    assert json.loads((case_dir / "draft-review.json").read_text())["criteria"][-1]["expectation"] == "NEW_PRIVATE_EXPECTATION"
    assert_pipeline_context_isolation(calls)


@pytest.mark.parametrize("failed_stage", ["writer", "source-review", "revision"])
@pytest.mark.parametrize("status,exit_code,pipeline_status,return_code", [
    ("timeout", -9, "blocked", 1),
    ("completed", 7, "blocked", 1),
    ("interrupted", -9, "interrupted", 130),
])
def test_source_review_process_failure_never_falls_back_to_draft(
    source, tmp_path, monkeypatch, failed_stage, status, exit_code, pipeline_status, return_code,
):
    monkeypatch.setattr(runner, "SKILL_DIR", source)
    stages = ["writer", "source-review", "revision"]
    replies = {
        "writer": SOURCE_REVIEW_FLAWED_DRAFT,
        "source-review": source_review_report(with_findings=True), "revision": SOURCE_REVIEW_REVISION,
    }
    calls = fake_pipeline_processes(monkeypatch, replies, failure=(failed_stage, status, exit_code))
    output = tmp_path / "failed"
    assert runner.main(["--tool", "codex", "--output", str(output), "--source-review", "--run"]) == return_code
    case_dir = output / "codex/case-01"
    pipeline = json.loads((case_dir / "pipeline.json").read_text())
    assert pipeline["status"] == pipeline_status and pipeline["final_origin"] is None
    assert not (case_dir / "final.txt").exists()
    assert [c["stage"] for c in calls if c["stage"] != "version"] == stages[:stages.index(failed_stage) + 1]
    assert json.loads((case_dir / "review.json").read_text())["semantic_verdict"] == "not_reviewed"
    failed_dir = case_dir if failed_stage == "writer" else case_dir / failed_stage
    assert (failed_dir / "stdout.jsonl").read_text()
    assert json.loads((failed_dir / "process.json").read_text())["status"] == status


@pytest.mark.parametrize("tool", ["claude", "codex"])
@pytest.mark.parametrize("incomplete_stage", ["source-review", "revision"])
def test_source_review_requires_completed_cli_events(source, tmp_path, monkeypatch, tool, incomplete_stage):
    monkeypatch.setattr(runner, "SKILL_DIR", source)
    calls = fake_pipeline_processes(monkeypatch, {
        "writer": SOURCE_REVIEW_FLAWED_DRAFT,
        "source-review": source_review_report(with_findings=True), "revision": SOURCE_REVIEW_REVISION,
    }, incomplete_stage=incomplete_stage)
    output = tmp_path / "incomplete"
    assert runner.main(["--tool", tool, "--output", str(output), "--source-review", "--run"]) == 1
    case_dir = output / tool / "case-01"
    pipeline = json.loads((case_dir / "pipeline.json").read_text())
    assert pipeline["status"] == "blocked" and pipeline["final_origin"] is None
    assert not (case_dir / "final.txt").exists()
    assert [c["stage"] for c in calls if c["stage"] != "version"][-1] == incomplete_stage
    assert (case_dir / incomplete_stage / "stdout.jsonl").read_text()


@pytest.mark.parametrize("invalid", [
    "not_json", "unsupported_schema", "no_supported_claims", "empty_supported_sources",
    "source_path_escape", "source_excerpt_mismatch", "draft_excerpt_mismatch", "missing_calculation",
])
def test_source_review_invalid_report_blocks_revision_and_final(source, tmp_path, monkeypatch, invalid):
    monkeypatch.setattr(runner, "SKILL_DIR", source)
    report = source_review_report()
    supported = report["supported_claims"][0]
    if invalid == "not_json":
        report = "The draft looks fine."
    elif invalid == "unsupported_schema":
        report["schema_version"] = 2
    elif invalid == "no_supported_claims":
        report["supported_claims"] = []
    elif invalid == "empty_supported_sources":
        supported["sources"] = []
    elif invalid == "source_path_escape":
        supported["sources"][0]["path"] = "../review.json"
    elif invalid == "source_excerpt_mismatch":
        supported["sources"][0]["excerpt"] = "A fact absent from the supplied source."
    elif invalid == "draft_excerpt_mismatch":
        supported["draft_excerpt"] = "A claim absent from the draft."
    elif invalid == "missing_calculation":
        supported["basis"] = "derived"
    calls = fake_pipeline_processes(monkeypatch, {"writer": SOURCE_REVIEW_DRAFT, "source-review": report})
    output = tmp_path / "invalid-report"
    assert runner.main(["--tool", "codex", "--output", str(output), "--source-review", "--run"]) == 1
    case_dir = output / "codex/case-01"
    pipeline = json.loads((case_dir / "pipeline.json").read_text())
    assert pipeline["status"] == "blocked" and pipeline["final_origin"] is None
    assert [c["stage"] for c in calls if c["stage"] != "version"] == ["writer", "source-review"]
    assert not (case_dir / "revision").exists() and not (case_dir / "final.txt").exists()
    assert not (case_dir / "source-review/report.json").exists()
    response = (case_dir / "source-review/response.txt").read_text()
    assert response == (report if isinstance(report, str) else json.dumps(report))
    assert_pipeline_reviews_ungraded(case_dir)


@pytest.mark.parametrize("mismatch", [
    "instructions", "inputs", "prompt", "input_crlf", "prompt_crlf",
    "not_completed", "nonzero", "missing_output",
])
def test_source_review_mismatched_import_is_rejected_before_any_cli(source, tmp_path, monkeypatch, mismatch):
    monkeypatch.setattr(runner, "SKILL_DIR", source)
    prior = tmp_path / "prior"
    if mismatch == "input_crlf":
        initial = case()
        initial["files"][0]["content"] += "\n"
        (source / "evals/evals.json").write_text(json.dumps({"evals": [initial]}))
    fake_pipeline_processes(monkeypatch, {"writer": SOURCE_REVIEW_DRAFT})
    assert runner.main(["--tool", "codex", "--output", str(prior), "--run"]) == 0
    prior_case = prior / "codex/case-01"
    if mismatch == "instructions":
        (source / "SKILL.md").write_text("Changed source instructions.")
    elif mismatch in {"inputs", "prompt"}:
        changed = case()
        if mismatch == "inputs":
            changed["files"][0]["content"] = "Different raw project fact."
        else:
            changed["prompt"] = "A different owner request."
        (source / "evals/evals.json").write_text(json.dumps({"evals": [changed]}))
    elif mismatch in {"input_crlf", "prompt_crlf"}:
        changed_path = prior_case / ("inputs/handoff.md" if mismatch == "input_crlf" else "prompt.txt")
        original_bytes = changed_path.read_bytes()
        assert b"\n" in original_bytes
        changed_path.write_bytes(original_bytes.replace(b"\n", b"\r\n"))
    elif mismatch == "missing_output":
        (prior_case / "stdout.jsonl").unlink()
    else:
        process = json.loads((prior_case / "process.json").read_text())
        process.update(status="timeout" if mismatch == "not_completed" else "completed", exit_code=7)
        (prior_case / "process.json").write_text(json.dumps(process))
    calls = fake_pipeline_processes(monkeypatch, {})
    with pytest.raises(SystemExit) as error:
        runner.main([
            "--tool", "codex", "--output", str(tmp_path / "rejected"),
            "--source-review", "--drafts-from", str(prior), "--run",
        ])
    assert error.value.code == 2
    assert calls == []


@pytest.mark.parametrize("tool", ["claude", "codex"])
@pytest.mark.parametrize("change", [
    "stdout.jsonl", "stderr.txt", "process.json", "missing_hashes",
    "incomplete_hashes", "invalid_hashes", "duplicate_record",
])
def test_source_review_altered_capture_is_rejected_before_any_cli(
    source, tmp_path, monkeypatch, tool, change,
):
    monkeypatch.setattr(runner, "SKILL_DIR", source)
    prior = tmp_path / "prior"
    fake_pipeline_processes(monkeypatch, {"writer": SOURCE_REVIEW_DRAFT})
    assert runner.main(["--tool", tool, "--output", str(prior), "--run"]) == 0
    prior_case = prior / tool / "case-01"
    if change == "stdout.jsonl":
        path = prior_case / change
        path.write_bytes(path.read_bytes().replace(b"Raw project fact.", b"Altered project fact."))
        response, _ = runner.completed_response(tool, prior_case)
        assert response == SOURCE_REVIEW_DRAFT.replace("Raw", "Altered")
    elif change == "stderr.txt":
        (prior_case / change).write_text("Altered capture diagnostics.\n")
    elif change == "process.json":
        path = prior_case / change
        process = json.loads(path.read_text())
        process["duration_seconds"] = 99
        path.write_text(json.dumps(process))
        assert runner.completed_response(tool, prior_case)[0] == SOURCE_REVIEW_DRAFT
    else:
        path = prior / "manifest.json"
        manifest = json.loads(path.read_text())
        record = manifest["runs"][0]
        if change == "missing_hashes":
            record.pop("capture_sha256", None)
        elif change == "incomplete_hashes":
            record["capture_sha256"] = {"stdout.jsonl": "0" * 64}
        elif change == "invalid_hashes":
            record["capture_sha256"] = []
        else:
            manifest["runs"].append(dict(record))
        path.write_text(json.dumps(manifest))
    calls = fake_pipeline_processes(monkeypatch, {})
    output = tmp_path / "rejected"
    with pytest.raises(SystemExit) as error:
        runner.main([
            "--tool", tool, "--output", str(output),
            "--source-review", "--drafts-from", str(prior), "--run",
        ])
    assert error.value.code == 2
    assert calls == []
    assert not output.exists()


@pytest.mark.parametrize("tool", ["claude", "codex"])
def test_writer_capture_hashes_are_saved_before_source_review(source, tmp_path, monkeypatch, tool):
    from hashlib import sha256

    monkeypatch.setattr(runner, "SKILL_DIR", source)
    fake_pipeline_processes(monkeypatch, {
        "writer": SOURCE_REVIEW_DRAFT, "source-review": source_review_report(),
    })
    output = tmp_path / "captured-before-review"
    pipeline = runner.review_pipeline
    observed = []

    def check_saved_capture(*args, **kwargs):
        manifest = json.loads((output / "manifest.json").read_text())
        expected = {
            name: sha256((output / tool / "case-01" / name).read_bytes()).hexdigest()
            for name in ("prompt.txt", "stdout.jsonl", "stderr.txt", "process.json")
        }
        assert manifest["runs"][0]["capture_sha256"] == expected
        observed.append(expected)
        return pipeline(*args, **kwargs)

    monkeypatch.setattr(runner, "review_pipeline", check_saved_capture)
    assert runner.main(["--tool", tool, "--output", str(output), "--source-review", "--run"]) == 0
    manifest = json.loads((output / "manifest.json").read_text())
    assert len(manifest["runs"]) == len(observed) == 1
    assert manifest["runs"][0]["capture_sha256"] == observed[0]
    assert manifest["runs"][0]["pipeline_status"] == "completed"


@pytest.mark.parametrize("tool", ["claude", "codex"])
def test_source_review_paired_import_freezes_the_validated_capture(source, tmp_path, monkeypatch, tool):
    from hashlib import sha256

    monkeypatch.setattr(runner, "SKILL_DIR", source)
    prior = tmp_path / "prior"
    fake_pipeline_processes(monkeypatch, {"writer": SOURCE_REVIEW_DRAFT})
    assert runner.main(["--tool", tool, "--output", str(prior), "--run"]) == 0
    prior_case = prior / tool / "case-01"
    original = {
        name: (prior_case / name).read_bytes()
        for name in ("prompt.txt", "stdout.jsonl", "stderr.txt", "process.json")
    }
    calls = fake_pipeline_processes(monkeypatch, {"source-review": source_review_report()})
    bounded = runner.run_bounded
    replaced = []

    def replace_prior_after_preflight(*args, **kwargs):
        if "--version" in args[0] and not replaced:
            replaced.append(True)
            (prior_case / "prompt.txt").write_text("REPLACED_CAPTURE_SECRET")
            (prior_case / "stdout.jsonl").write_bytes(
                original["stdout.jsonl"].replace(b"Raw project fact.", b"REPLACED_CAPTURE_SECRET")
            )
            (prior_case / "stderr.txt").write_text("REPLACED_CAPTURE_SECRET")
            process = json.loads(original["process.json"])
            process["replacement_note"] = "REPLACED_CAPTURE_SECRET"
            (prior_case / "process.json").write_text(json.dumps(process))
        return bounded(*args, **kwargs)

    monkeypatch.setattr(runner, "run_bounded", replace_prior_after_preflight)
    output = tmp_path / "frozen-pair"
    assert runner.main([
        "--tool", tool, "--output", str(output), "--source-review", "--drafts-from", str(prior), "--run",
    ]) == 0
    assert replaced == [True]
    case_dir = output / tool / "case-01"
    for name, content in original.items():
        assert (prior_case / name).read_bytes() != content
        assert (case_dir / name).read_bytes() == content
    assert (case_dir / "final.txt").read_text() == SOURCE_REVIEW_DRAFT
    provenance = json.loads((case_dir / "draft-provenance.json").read_text())
    assert provenance["capture_sha256"] == {name: sha256(data).hexdigest() for name, data in original.items()}
    assert [c["stage"] for c in calls if c["stage"] != "version"] == ["source-review"]
    for call in calls:
        exposed = call["prompt"] + "\n".join(call["files"].values())
        assert "REPLACED_CAPTURE_SECRET" not in exposed
    assert_pipeline_reviews_ungraded(case_dir)
    assert_pipeline_context_isolation(calls)

@pytest.mark.parametrize("envelope", [
    "<report>",
    "```json\n<report>\n```",
    "```\n<report>\n```",
    "I've read all four files. Here is the review report.\n\n```json\n<report>\n```",
    "I read `inputs/handoff.md`.\n\n```json\n<report>\n```\n\nThe report is complete.",
    "```json\n<report>\n```\n\nThe report is complete.",
])
def test_source_report_accepts_one_unambiguous_payload(envelope):
    report = source_review_report()
    response = envelope.replace("<report>", json.dumps(report, indent=2))
    assert runner.source_report(
        response, SOURCE_REVIEW_DRAFT, {"inputs/handoff.md": "Raw project fact."},
    ) == report


@pytest.mark.parametrize("envelope", [
    "Here is the report: <report>",
    "Here is the report:\n```\n<report>\n```",
    "```json\n<report>",
    "```json\n<report>\n```\n```json\n<report>\n```",
    "```python\npass\n```\n```json\n<report>\n```",
    "```json\n<report>\n```json",
    "~~~json\n<report>\n~~~",
    "{}\n```json\n<report>\n```",
    "```json\n<report>\n```\n[]",
    "I read `inputs/handoff.md.\n```json\n<report>\n```",
    "I read ``inputs/handoff.md``.\n```json\n<report>\n```",
    "Here is ```json\n<report>\n```",
    "```json\n<report>\n```\n```json",
])
def test_source_report_rejects_ambiguous_or_unclosed_envelopes(envelope):
    response = envelope.replace("<report>", json.dumps(source_review_report()))
    with pytest.raises(ValueError):
        runner.source_report(
            response, SOURCE_REVIEW_DRAFT, {"inputs/handoff.md": "Raw project fact."},
        )


@pytest.mark.parametrize("invalid", ["schema", "source_path", "source_excerpt", "draft_excerpt"])
def test_source_report_wrapping_does_not_weaken_validation(invalid):
    report = source_review_report()
    claim = report["supported_claims"][0]
    if invalid == "schema":
        report["schema_version"] = 2
    elif invalid == "source_path":
        claim["sources"][0]["path"] = "../review.json"
    elif invalid == "source_excerpt":
        claim["sources"][0]["excerpt"] = "Raw  project fact."
    else:
        claim["draft_excerpt"] = "Raw  project fact."
    response = "Here is the report:\n```json\n" + json.dumps(report) + "\n```\nReport complete."
    with pytest.raises(ValueError):
        runner.source_report(
            response, SOURCE_REVIEW_DRAFT, {"inputs/handoff.md": "Raw project fact."},
        )


def test_source_report_fence_extraction_preserves_excerpt_characters():
    fact = "Measured  value.\r\nNext\tvalue: 10%."
    report = source_review_report()
    claim = report["supported_claims"][0]
    claim["draft_excerpt"] = fact
    claim["sources"][0]["excerpt"] = fact
    response = "Here is the report:\r\n```json\r\n" + json.dumps(report, indent=2) + "\r\n```"
    assert runner.source_report(response, fact, {"inputs/handoff.md": fact}) == report


@pytest.mark.parametrize("tool", ["claude", "codex"])
def test_source_review_wrapped_report_retains_capture_and_revises_once(source, tmp_path, monkeypatch, tool):
    monkeypatch.setattr(runner, "SKILL_DIR", source)
    report = source_review_report(with_findings=True)
    wrapped = "I read `inputs/handoff.md`. Here is the report:\n\n```json\n" + json.dumps(report) + "\n```"
    calls = fake_pipeline_processes(monkeypatch, {
        "writer": SOURCE_REVIEW_FLAWED_DRAFT, "source-review": wrapped,
        "revision": SOURCE_REVIEW_REVISION,
    })
    output = tmp_path / "wrapped-report"
    assert runner.main(["--tool", tool, "--output", str(output), "--source-review", "--run"]) == 0
    case_dir = output / tool / "case-01"
    assert [c["stage"] for c in calls if c["stage"] != "version"] == [
        "writer", "source-review", "revision",
    ]
    assert (case_dir / "source-review/response.txt").read_text() == wrapped
    assert json.loads((case_dir / "source-review/report.json").read_text()) == report
    assert (case_dir / "draft.txt").read_text() == SOURCE_REVIEW_FLAWED_DRAFT
    assert (case_dir / "final.txt").read_text() == SOURCE_REVIEW_REVISION
    assert_pipeline_reviews_ungraded(case_dir)
    assert_pipeline_context_isolation(calls)
