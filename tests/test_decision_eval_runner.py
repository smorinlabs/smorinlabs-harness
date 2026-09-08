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


@pytest.mark.parametrize("path", ["../review.json", "/tmp/escape", "a/../../escape", "./file", ""])
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
    assert len(cases) == 13
    findings = {finding for item in cases for finding in item["covered_findings"]}
    assert {f"CDC-{number:02}" for number in range(1, 11)} <= findings
    for item in cases:
        assert item["files"]
        assert item["expectations"]
        for criterion in item["expectations"]:
            assert criterion not in item["prompt"]
            assert all(criterion not in raw["content"] for raw in item["files"])
