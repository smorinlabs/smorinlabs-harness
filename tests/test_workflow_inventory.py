"""tests/test_workflow_inventory.py — what a workflow file declares.

The script gives ci-fix the facts it needs without reading YAML by eye: each
job's runner family, matrix cells with their GitHub display names, container
and services, every step with its display name and whether it is a `run:` step
the local sweep may execute, and the workflow's triggers including
`workflow_dispatch` inputs. Exit 0 ok, 2 usage (missing file, bad YAML, or
PyYAML absent — with the exact `uv run --no-project --with pyyaml` line).
"""

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "plugins/repo-hygiene/skills/ci-fix/scripts/workflow_inventory.py"
WF = REPO_ROOT / "tests/fixtures/ci_fix/workflows"
REAL = WF / "ci_real.yml"  # this repo's CI workflow, verbatim
SYNTH = WF / "synthetic.yml"

assert SCRIPT.is_file(), f"workflow_inventory.py not found at {SCRIPT}"


def run(*args):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *[str(a) for a in args]],
        capture_output=True,
        text=True,
    )


def inventory(*args):
    result = run("--json", *args)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def jobs_of(data, path):
    wf = next(w for w in data["workflows"] if w["path"].endswith(path))
    return wf, {j["id"]: j for j in wf["jobs"]}


# ------------------------------------------------------------- real workflow


def test_real_workflow_triggers_and_jobs():
    wf, jobs = jobs_of(inventory(REAL), "ci_real.yml")
    # PyYAML parses a bare `on:` key as boolean True; the script must still find it
    assert wf["triggers"] == ["pull_request", "push"]
    assert wf["dispatch_inputs"] is None
    assert set(jobs) == {"plugin-validate", "static-checks", "pytest", "gen-check"}
    assert all(j["os_family"] == "linux" for j in jobs.values())


def test_step_display_names_match_the_jobs_api():
    """The jobs API names unnamed steps `Run <uses>` / `Run <first run line>`;
    the inventory must produce the same strings so steps join to the profile."""
    _, jobs = jobs_of(inventory(REAL), "ci_real.yml")
    names = [s["display_name"] for s in jobs["pytest"]["steps"]]
    assert names == [
        "Run actions/checkout@v6",
        "Run astral-sh/setup-uv@v5",
        "Run uv sync --locked",
        "Run uv run pytest",
    ]


def test_run_steps_are_marked_local_and_setup_steps_are_not():
    _, jobs = jobs_of(inventory(REAL), "ci_real.yml")
    steps = {s["display_name"]: s for s in jobs["plugin-validate"]["steps"]}
    assert steps["Run actions/checkout@v6"]["kind"] == "uses"
    assert steps["Run npm install -g @anthropic-ai/claude-code"]["kind"] == "run"
    assert steps["Run npm install -g @anthropic-ai/claude-code"]["setup"] is True
    assert steps["Run claude plugin validate ."]["setup"] is False
    assert steps["Run claude plugin validate ."]["run"] == "claude plugin validate ."


# -------------------------------------------------------- synthetic workflow


def test_dispatch_inputs_are_listed():
    wf, _ = jobs_of(inventory(SYNTH), "synthetic.yml")
    assert "workflow_dispatch" in wf["triggers"]
    assert wf["dispatch_inputs"]["filter"] == {"required": False, "default": "", "type": None, "options": None}
    assert wf["dispatch_inputs"]["job"]["type"] == "choice"
    assert wf["dispatch_inputs"]["job"]["options"] == ["all", "unit", "integration"]


def test_matrix_cells_expand_with_include_and_carry_display_names():
    _, jobs = jobs_of(inventory(SYNTH), "synthetic.yml")
    unit = jobs["unit"]
    assert unit["runs_on"] == "${{ matrix.os }}"
    assert unit["os_family"] == "matrix"
    cells = unit["matrix_cells"]
    # 2 os × 2 python = 4, plus one include row that matches no cell = 5
    assert len(cells) == 5
    names = [c["display_name"] for c in cells]
    assert "unit (ubuntu-latest, 3.12)" in names
    assert "unit (macos-latest, 3.13)" in names
    extra = next(c for c in cells if c.get("experimental"))
    assert extra["display_name"] == "unit (ubuntu-latest, 3.14, true)"
    assert extra["os_family"] == "linux"
    assert next(c for c in cells if c["os"] == "macos-latest")["os_family"] == "macos"


def test_container_services_needs_timeout_and_windows_family():
    _, jobs = jobs_of(inventory(SYNTH), "synthetic.yml")
    integ = jobs["integration"]
    assert integ["container"] == "python:3.13-slim"
    assert integ["services"] == ["postgres"]
    assert integ["needs"] == ["lint", "unit"]
    assert integ["timeout_minutes"] == 30
    assert jobs["windows-smoke"]["os_family"] == "windows"
    assert jobs["lint"]["timeout_minutes"] is None


def test_step_working_directory_env_and_multiline_run():
    _, jobs = jobs_of(inventory(SYNTH), "synthetic.yml")
    tests = next(s for s in jobs["unit"]["steps"] if s["display_name"] == "Tests")
    assert tests["working_directory"] == "packages/core"
    assert tests["env"] == {"PYTHONHASHSEED": "0"}
    assert tests["run"].strip() == "uv run pytest -x ${{ inputs.filter }}"
    apt = jobs["integration"]["steps"][1]
    assert apt["setup"] is True  # apt-get is package-manager setup, never swept


def test_text_output_one_line_per_job():
    result = run(SYNTH)
    assert result.returncode == 0, result.stderr
    lines = result.stdout.splitlines()
    assert any(l.startswith("synthetic.yml") and "workflow_dispatch" in l for l in lines)
    assert sum(1 for l in lines if "  integration " in l or l.strip().startswith("integration ")) == 1


# ------------------------------------------------------------------- errors


def test_missing_file_is_a_usage_error(tmp_path):
    result = run(tmp_path / "nope.yml")
    assert result.returncode == 2
    assert "nope.yml" in result.stderr


def test_invalid_yaml_is_a_usage_error(tmp_path):
    bad = tmp_path / "bad.yml"
    bad.write_text("on: [push\njobs: {")
    result = run(bad)
    assert result.returncode == 2
    assert "bad.yml" in result.stderr


def test_missing_pyyaml_names_the_runner_line(tmp_path):
    """Without PyYAML the script must say exactly how to run it, not trace back."""
    result = subprocess.run(
        [sys.executable, "-S", str(SCRIPT), str(SYNTH)],  # -S: no site-packages → no yaml
        capture_output=True,
        text=True,
    )
    assert result.returncode == 2
    assert "uv run --no-project --with pyyaml" in result.stderr
    assert "Traceback" not in result.stderr
