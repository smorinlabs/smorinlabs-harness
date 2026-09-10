"""tests/test_workflow_inventory.py — what a workflow file declares.

The script gives ci-fix the facts it needs without reading YAML by eye: each
job's runner family, matrix cells with their GitHub display names, container
and services, every step's raw and effective context plus conservative
validation hints, and the workflow's triggers including
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
REAL = WF / "ci_real.yml"  # this repo's CI workflow, copied verbatim (kept in sync by hand)
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
    assert wf["triggers"] == ["pull_request", "push", "workflow_dispatch"]
    assert wf["dispatch_inputs"] == {}  # the trigger is declared with no inputs
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
    assert any(
        line.startswith("synthetic.yml") and "workflow_dispatch" in line
        for line in lines
    )
    assert (
        sum(
            1
            for line in lines
            if "  integration " in line or line.strip().startswith("integration ")
        )
        == 1
    )


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


# ------------------------------------------- review round 2: sweep needs these


def test_setup_detection_covers_every_line_and_installers_only():
    _, jobs = jobs_of(inventory(SYNTH), "synthetic.yml")
    steps = jobs["misc"]["steps"]
    by_run = {s["run"].strip().splitlines()[-1]: s for s in steps if s["run"]}
    assert by_run["sudo apt-get install -y libfoo"]["setup"] is True  # second line of a multi-line run
    assert by_run["curl -fsSL https://example.com/install.sh | sh"]["setup"] is True  # piped installer
    assert by_run["curl -f http://localhost:8080/health"]["setup"] is False  # a smoke check, not setup
    assert by_run["npm ci"]["setup"] is False  # project-local install stays a job step
    assert by_run["pip install -e ."]["setup"] is True  # writes outside the repo


def test_job_env_defaults_and_step_conditions_are_emitted():
    _, jobs = jobs_of(inventory(SYNTH), "synthetic.yml")
    misc = jobs["misc"]
    assert misc["env"] == {"WORKFLOW_LEVEL": "w", "JOB_LEVEL": "1"}  # workflow env, then job env
    assert misc["defaults_run"] == {"working_directory": "svc", "shell": "bash"}
    steps = misc["steps"]
    cond = next(s for s in steps if s["run"] and "only-on-push" in s["run"])
    assert cond["if"] == "github.event_name == 'push'"
    flaky = next(s for s in steps if s["run"] and "flaky" in s["run"])
    assert flaky["continue_on_error"] is True
    py = next(s for s in steps if s["shell"] == "python")
    assert py["run"].strip() == 'print("hi")'
    plain = next(s for s in steps if s["run"] and s["run"].strip() == "npm ci")
    assert plain["if"] is None and plain["continue_on_error"] is False and plain["shell"] is None


def test_matrix_job_with_name_uses_the_substituted_name_as_display():
    """The jobs API names a matrix job by its `name:` with expressions
    evaluated, not by `<id> (<values>)`; the join to the profile depends on it."""
    _, jobs = jobs_of(inventory(SYNTH), "synthetic.yml")
    cells = jobs["named-matrix"]["matrix_cells"]
    assert sorted(c["display_name"] for c in cells) == ["nm (ubuntu-latest)", "nm (windows-latest)"]
    assert {c["os_family"] for c in cells} == {"linux", "windows"}


# ------------------------------------------------- PR #55 review findings


def test_step_with_neither_uses_nor_run_is_not_runnable():
    _, jobs = jobs_of(inventory(SYNTH), "synthetic.yml")
    steps = jobs["odd-steps"]["steps"]
    assert steps[0]["kind"] == "other" and steps[0]["run"] is None
    assert steps[1]["kind"] == "run"
    text = run(SYNTH).stdout
    assert any(
        line.strip().startswith("odd-steps ") and "validation-candidates=0" in line
        for line in text.splitlines()
    )


def test_later_include_overwrites_earlier_include_values_but_never_axes():
    """GitHub: an include matches on the ORIGINAL axis values; values it adds
    can be overwritten by a later include; axis values never are."""
    _, jobs = jobs_of(inventory(SYNTH), "synthetic.yml")
    cells = {c["display_name"]: c for c in jobs["seq-include"]["matrix_cells"]}
    assert cells["seq-include (ubuntu-latest, 18, yes)"]["coverage"] == "yes"  # second include won
    assert "seq-include (ubuntu-latest, 20)" in cells  # untouched axis cell
    assert "seq-include (ubuntu-latest, 22)" in cells  # include that matched no cell: new cell
    assert len(cells) == 3


def test_trigger_filters_are_exposed():
    wf, _ = jobs_of(inventory(SYNTH), "synthetic.yml")
    f = wf["trigger_filters"]
    assert f["push"] == {
        "branches": ["main"],
        "branches_ignore": None,
        "paths": None,
        "paths_ignore": ["docs/**", "*.md"],
        "tags": None,
        "tags_ignore": None,
        "types": None,
    }
    assert f["pull_request"]["types"] == ["opened", "synchronize"] and f["pull_request"]["branches"] is None
    real, _ = jobs_of(inventory(REAL), "ci_real.yml")
    assert real["trigger_filters"]["push"]["branches"] == ["main"]
    assert real["trigger_filters"]["pull_request"] == {
        "branches": None,
        "branches_ignore": None,
        "paths": None,
        "paths_ignore": None,
        "tags": None,
        "tags_ignore": None,
        "types": None,
    }


def test_exclude_applies_before_include_so_include_can_add_back():
    """GitHub processes `exclude` on the base matrix first; `include` runs after
    and may add a combination back. Excluding then re-including must yield the
    cell, marked with the include's extras."""
    _, jobs = jobs_of(inventory(SYNTH), "synthetic.yml")
    cells = {c["display_name"]: c for c in jobs["excl-then-incl"]["matrix_cells"]}
    assert len(cells) == 4  # 2×2 minus one excluded plus one added back
    assert cells["excl-then-incl (windows-latest, 18, true)"]["experimental"] is True
    assert "excl-then-incl (windows-latest, 18)" not in cells


def test_inventory_tolerates_non_workflow_files(tmp_path):
    """`.github/workflows/` can hold a README or an action fragment; those are
    skipped with a warning, never a usage error that hides every workflow."""
    readme = tmp_path / "README.md"
    readme.write_text("# notes\n")
    frag = tmp_path / "fragment.yml"
    frag.write_text("- just\n- a list\n")
    result = run("--json", SYNTH, readme, frag)
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert [w["path"] for w in data["workflows"]] == [str(SYNTH)]
    assert "README.md" in result.stderr and "fragment.yml" in result.stderr


def test_conditions_and_release_boundaries_are_preserved(tmp_path):
    workflow = tmp_path / "guarded.yml"
    workflow.write_text("""on:
  push:
    tags: ['v*']
jobs:
  release:
    if: false
    environment: production
    runs-on: ubuntu-latest
    steps:
      - run: npm publish
        continue-on-error: ${{ false }}
  tests:
    runs-on: ubuntu-latest
    steps:
      - run: pytest tests/unit
      - run: pytest tests/optional
        if: ${{ inputs.enabled }}
      - run: pytest tests/disabled
        if: ${{ false }}
""")
    wf, jobs = jobs_of(inventory(workflow), "guarded.yml")
    release = jobs["release"]
    assert release["if"] is False and release["condition_state"] is False
    assert release["environment"] == "production"
    step = release["steps"][0]
    assert step["continue_on_error"] == "${{ false }}"
    assert step["continue_on_error_state"] is False
    assert step["validation_kind"] == "not-validation"
    assert jobs["tests"]["steps"][0]["validation_kind"] == "candidate"
    assert jobs["tests"]["steps"][1]["condition_state"] is None
    assert jobs["tests"]["steps"][2]["condition_state"] is False
    assert wf["trigger_filters"]["push"]["tags"] == ["v*"]


def test_shell_and_environment_precedence_and_unknown_context(tmp_path):
    workflow = tmp_path / "shells.yml"
    workflow.write_text("""env: {LEVEL: workflow, KEEP: yes}
defaults:
  run: {working-directory: root}
jobs:
  windows:
    runs-on: windows-latest
    steps:
      - run: pytest
  container:
    runs-on: ubuntu-latest
    container: {image: python:3.12, options: '--user 1000'}
    steps:
      - run: pytest
  linux:
    runs-on: ubuntu-latest
    env: {LEVEL: job}
    defaults:
      run: {shell: sh, working-directory: package}
    steps:
      - run: pytest
      - run: pytest
        shell: bash
        working-directory: tests
        env: {LEVEL: step}
      - run: echo app:${{ github.sha }}
""")
    _, jobs = jobs_of(inventory(workflow), "shells.yml")
    assert jobs["windows"]["steps"][0]["effective_shell"] == "pwsh"
    assert jobs["container"]["steps"][0]["effective_shell"] == "sh"
    assert jobs["container"]["container_config"]["options"] == "--user 1000"
    inherited, override, unresolved = jobs["linux"]["steps"]
    assert inherited["effective_shell"] == "sh"
    assert inherited["effective_working_directory"] == "package"
    assert inherited["effective_env"]["LEVEL"] == "job"
    assert override["effective_shell"] == "bash"
    assert override["effective_working_directory"] == "tests"
    assert override["effective_env"]["LEVEL"] == "step"
    assert unresolved["unresolved_expressions"] == ["${{ github.sha }}"]
    assert unresolved["validation_kind"] == "inspect"


def test_unknown_wrappers_and_compound_commands_need_inspection(tmp_path):
    workflow = tmp_path / "commands.yml"
    workflow.write_text("""jobs:
  checks:
    runs-on: ubuntu-latest
    steps:
      - run: make test
      - run: npm test
      - run: pytest && npm publish
      - run: uv run ruff check --fix .
      - run: uv run ruff check .
      - run: python3 -m pytest tests/unit
""")
    _, jobs = jobs_of(inventory(workflow), "commands.yml")
    assert [s["validation_kind"] for s in jobs["checks"]["steps"]] == [
        "inspect",
        "inspect",
        "not-validation",
        "inspect",
        "candidate",
        "candidate",
    ]
