"""tests/test_ladder_plan.py — the isolation heuristic as a truth table.

ladder_plan.py decides, from the duration profile (and the local ledger when
one exists), where a fix enters the ladder and how the fix reaches CI. The
two levels have different floors because isolating costs seconds locally and
minutes in CI (Decision Q3.A, 2026-09-09):

- local: a failed step expected under the local floor (30s) runs whole
  (rung 1, no rung 0); over it or unmeasured, the extracted IDs run first
  (rung 0) and the whole step follows. Rung 1 always runs when the step can
  run here and is expected within the cap (10m); above the cap it is asked
  about once, and a "no" makes CI the lab.
- remote: a plain push (rung 2 = rung 3) unless CI is the lab AND the target
  job is expected over the remote floor (5m) AND the workflow is
  dispatchable: then only that workflow is dispatched with the failing IDs in
  its filter input, with a one-time offer to add the input. After a local
  green, one CI round is expected and a dispatch would only lose time.
"""

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "plugins/repo-hygiene/skills/ci-fix/scripts/ladder_plan.py"

assert SCRIPT.is_file(), f"ladder_plan.py not found at {SCRIPT}"

PYTEST_STEP = "Run uv run pytest"
LINT_STEP = "Run uv run ruff check ."


def profile_fixture():
    """A hand-built ci_profile.py --json document: one slow job, one fast, one unmeasured."""
    return {
        "threshold_s": 120,
        "runs_sampled": 10,
        "external_jobs": [],
        "unknown_ownership_jobs": [],
        "truncated_runs": [],
        "jobs": [
            {
                "name": "CI / pytest",  # display name: disambiguated because Nightly also runs a pytest job
                "job": "pytest",
                "workflow_name": "CI",
                "workflow_path": ".github/workflows/ci.yml",
                "external": False,
                "class": "slow",
                "samples": 10,
                "median_s": 600.0,
                "max_s": 660.0,
                "queue_median_s": 10.0,
                "wait_bound_s": 915,
                "slowest_step": {"name": PYTEST_STEP, "median_s": 540.0},
                "steps": [
                    {"name": "Set up job", "median_s": 5.0},
                    {"name": PYTEST_STEP, "median_s": 540.0},
                ],
            },
            {
                "name": "lint",
                "job": "lint",
                "workflow_name": "CI",
                "workflow_path": ".github/workflows/ci.yml",
                "external": False,
                "class": "fast",
                "samples": 10,
                "median_s": 20.0,
                "max_s": 25.0,
                "queue_median_s": 4.0,
                "wait_bound_s": 60,
                "slowest_step": {"name": LINT_STEP, "median_s": 15.0},
                "steps": [
                    {"name": "Set up job", "median_s": 3.0},
                    {"name": LINT_STEP, "median_s": 15.0},
                ],
            },
            {
                "name": "nightly",
                "job": "nightly",
                "workflow_name": "Nightly",
                "workflow_path": ".github/workflows/nightly.yml",
                "external": False,
                "class": "unmeasured",
                "samples": 0,
                "median_s": None,
                "max_s": None,
                "queue_median_s": None,
                "wait_bound_s": None,
                "slowest_step": None,
                "steps": [],
            },
            {
                "name": "Nightly / pytest",
                "job": "pytest",
                "workflow_name": "Nightly",
                "workflow_path": ".github/workflows/nightly.yml",
                "external": False,
                "class": "slow",
                "samples": 4,
                "median_s": 1800.0,
                "max_s": 1900.0,
                "queue_median_s": 5.0,
                "wait_bound_s": 2708,
                "slowest_step": {"name": PYTEST_STEP, "median_s": 1750.0},
                "steps": [{"name": PYTEST_STEP, "median_s": 1750.0}],
            },
        ],
    }


def write_profile(tmp_path, data=None):
    path = tmp_path / "profile.json"
    path.write_text(json.dumps(data or profile_fixture()))
    return path


CI_PATH = ".github/workflows/ci.yml"
NIGHTLY_PATH = ".github/workflows/nightly.yml"


def write_ledger(tmp_path, samples):
    """The ledger keys on the workflow path too, so a sample without one is a
    separate bucket; the fixtures fill it in unless a case says otherwise."""
    path = tmp_path / "ledger.json"
    for s in samples:
        s.setdefault(
            "workflow_path", CI_PATH if s["workflow"] == "CI" else NIGHTLY_PATH
        )
    path.write_text(json.dumps({"version": 1, "samples": samples}))
    return path


def run(*args):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *[str(a) for a in args]],
        capture_output=True,
        text=True,
        check=False,
    )


def plan(profile, *args):
    result = run("--json", "--profile", profile, *args)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def base(tmp_path, job="pytest", step=PYTEST_STEP, workflow="CI", ids=3, **flags):
    """Common arguments: a dispatchable workflow, no filter input, local step, not CI-is-lab."""
    args = ["--workflow", workflow, "--job", job, "--step", step, "--ids", str(ids)]
    for flag in ("isolate_local", "isolate_remote"):
        if flag in flags:
            args += ["--" + flag.replace("_", "-"), flags.pop(flag)]
    args.append(
        "--dispatchable" if flags.pop("dispatchable", True) else "--not-dispatchable"
    )
    args.append("--local-step" if flags.pop("local_step", True) else "--no-local-step")
    args.append("--ci-is-lab" if flags.pop("ci_is_lab", False) else "--not-ci-is-lab")
    filter_input = flags.pop("filter_input", None)
    if filter_input:
        args += ["--filter-input", filter_input]
    ledger = flags.pop("ledger", None)
    if ledger:
        args += ["--ledger", str(ledger)]
    assert not flags, f"unused flags: {flags}"
    return plan(write_profile(tmp_path), *args)


# ---------------------------------------------------------------- local rungs
# fixture: lint step 15s (under the 30s floor), pytest step 540s (over it, under the 10m cap),
# Nightly pytest step 1750s (over the cap), nightly job unmeasured


def test_defaults_are_30s_local_5m_remote_and_a_10m_cap(tmp_path):
    p = base(tmp_path)
    assert p["local"]["floor_s"] == 30
    assert p["local"]["cap_s"] == 600
    assert p["remote"]["floor_s"] == 300


def test_fast_step_enters_at_rung_1_even_with_ids(tmp_path):
    p = base(tmp_path, job="lint", step=LINT_STEP, ids=3)
    local = p["local"]
    assert local["step_class"] == "fast"
    assert local["step_expected_s"] == 15.0
    assert local["source"] == "profile"
    assert local["entry_rung"] == 1
    assert local["rung_0"] is False
    assert local["rung_1"] is True
    assert local["rung_1_gate"] == "run"
    assert "under the local floor" in local["reason"]


def test_slow_step_with_ids_enters_at_rung_0_and_still_runs_rung_1(tmp_path):
    p = base(tmp_path, ids=3)
    local = p["local"]
    assert local["step_class"] == "slow"
    assert local["entry_rung"] == 0
    assert local["rung_0"] is True
    assert local["rung_1"] is True
    assert local["rung_1_gate"] == "run"  # 540s is under the 10m cap: no question asked
    assert local["rung_1_background"] is False


def test_a_ninety_second_step_is_isolated(tmp_path):
    """The owner's case: a suite of about a minute is still worth isolating,
    because the isolated run costs seconds."""
    ledger = write_ledger(
        tmp_path,
        [
            {
                "workflow": "CI",
                "job": "lint",
                "step": LINT_STEP,
                "seconds": 90.0,
                "at": "2026-09-09T00:00:00Z",
            }
        ],
    )
    p = base(tmp_path, job="lint", step=LINT_STEP, ids=2, ledger=ledger)
    assert p["local"]["step_class"] == "slow"
    assert p["local"]["entry_rung"] == 0


def test_slow_step_without_ids_enters_at_rung_1(tmp_path):
    p = base(tmp_path, ids=0)
    local = p["local"]
    assert local["entry_rung"] == 1
    assert local["rung_0"] is False
    assert local["rung_1"] is True
    assert "no test IDs" in local["reason"]


def test_unmeasured_step_counts_as_slow_and_runs_rung_1_in_the_background(tmp_path):
    p = base(tmp_path, job="nightly", step="Run make test", workflow="Nightly", ids=2)
    local = p["local"]
    assert local["step_class"] == "unmeasured"
    assert local["step_expected_s"] is None
    assert local["entry_rung"] == 0
    assert local["rung_1_gate"] == "run"
    assert local["rung_1_background"] is True


def test_step_missing_from_a_measured_job_is_unmeasured(tmp_path):
    p = base(tmp_path, step="Run a step that was renamed", ids=1)
    assert p["local"]["step_class"] == "unmeasured"
    assert p["local"]["entry_rung"] == 0


def test_ledger_median_overrides_the_ci_step_median(tmp_path):
    ledger = write_ledger(
        tmp_path,
        [
            {
                "workflow": "CI",
                "job": "pytest",
                "step": PYTEST_STEP,
                "seconds": s,
                "at": "2026-09-08T00:00:00Z",
            }
            for s in (18.0, 20.0, 22.0)
        ],
    )
    p = base(tmp_path, ids=3, ledger=ledger)
    local = p["local"]
    assert local["source"] == "ledger"
    assert local["step_expected_s"] == 20.0
    assert local["step_class"] == "fast"  # 540s in CI, 20s here: no isolation
    assert local["entry_rung"] == 1
    assert local["rung_0"] is False


def test_ledger_without_a_matching_key_falls_back_to_the_profile(tmp_path):
    ledger = write_ledger(
        tmp_path,
        [
            {
                "workflow": "Nightly",
                "job": "pytest",
                "step": PYTEST_STEP,
                "seconds": 5.0,
                "at": "2026-09-08T00:00:00Z",
            }
        ],
    )
    p = base(tmp_path, ids=3, ledger=ledger)
    assert p["local"]["source"] == "profile"
    assert p["local"]["step_expected_s"] == 540.0


def test_step_that_cannot_run_locally_has_no_local_rung_and_makes_ci_the_lab(tmp_path):
    p = base(tmp_path, ids=3, local_step=False)
    local = p["local"]
    assert local["entry_rung"] is None
    assert local["rung_0"] is False
    assert local["rung_1"] is False
    assert local["rung_1_gate"] == "unavailable"
    assert "not reproducible locally" in local["reason"]
    assert p["remote"]["ci_is_lab"] is True


def test_rung_1_over_the_cap_is_asked_about_not_skipped(tmp_path):
    p = base(tmp_path, workflow="Nightly", ids=3)
    local = p["local"]
    assert local["step_expected_s"] == 1750.0
    assert local["rung_1"] is True
    assert local["rung_1_gate"] == "ask"
    assert local["rung_1_background"] is True
    assert "cap" in local["reason"] and "CI is the lab" in local["reason"]


def test_local_floor_flag_moves_the_line(tmp_path):
    p = base(tmp_path, job="lint", step=LINT_STEP, ids=2, isolate_local="10s")
    assert p["local"]["step_class"] == "slow" and p["local"]["entry_rung"] == 0
    p = base(tmp_path, ids=3, isolate_local="15m")
    assert p["local"]["step_class"] == "fast" and p["local"]["entry_rung"] == 1


def test_same_job_name_in_two_workflows_needs_the_workflow(tmp_path):
    result = run(
        "--json",
        "--profile",
        write_profile(tmp_path),
        "--job",
        "pytest",
        "--step",
        PYTEST_STEP,
        "--ids",
        "1",
        "--dispatchable",
        "--local-step",
    )
    assert result.returncode == 2
    assert CI_PATH in result.stderr and NIGHTLY_PATH in result.stderr
    assert "pass --workflow" in result.stderr


def test_two_workflow_files_sharing_a_name_are_selected_by_path(tmp_path):
    """CodeRabbit on PR #61: with two `CI / test` rows, --workflow CI matched
    both and the error told the user to pass the flag they already had.
    --workflow-path separates them, and the error names the paths."""
    profile = profile_fixture()
    for j in profile["jobs"]:
        j["workflow_name"] = "CI"  # both files are named CI; only the paths differ
        j["name"] = "CI / " + j["job"]
    path = write_profile(tmp_path, profile)

    result = run(
        "--json",
        "--profile",
        path,
        "--workflow",
        "CI",
        "--job",
        "pytest",
        "--step",
        PYTEST_STEP,
        "--ids",
        "1",
    )
    assert result.returncode == 2
    assert "pass --workflow-path" in result.stderr
    assert CI_PATH in result.stderr and NIGHTLY_PATH in result.stderr

    p = plan(
        path,
        "--workflow-path",
        CI_PATH,
        "--job",
        "pytest",
        "--step",
        PYTEST_STEP,
        "--ids",
        "2",
        "--local-step",
    )
    assert p["workflow_path"] == CI_PATH
    assert p["local"]["step_expected_s"] == 540.0
    p = plan(
        path,
        "--workflow-path",
        NIGHTLY_PATH,
        "--job",
        "pytest",
        "--step",
        PYTEST_STEP,
        "--ids",
        "2",
        "--local-step",
    )
    assert p["workflow_path"] == NIGHTLY_PATH
    assert p["local"]["step_expected_s"] == 1750.0


def test_the_ledger_lookup_is_scoped_to_the_workflow_path(tmp_path):
    """A sample recorded for ci-arm.yml must not decide ci.yml's rung."""
    ledger = write_ledger(
        tmp_path,
        [
            {
                "workflow": "CI",
                "workflow_path": ".github/workflows/ci-arm.yml",
                "job": "pytest",
                "step": PYTEST_STEP,
                "seconds": 5.0,
                "at": "2026-09-09T00:00:00Z",
            }
        ],
    )
    p = base(tmp_path, ids=3, ledger=ledger)
    assert p["local"]["source"] == "profile"  # not the 5s sample from the other file
    assert p["local"]["step_expected_s"] == 540.0


# --------------------------------------------------------------- remote mode
# fixture: pytest job 600s (over the 5m floor), lint job 20s, nightly unmeasured, Nightly pytest 1800s


def test_verified_locally_is_always_a_plain_push(tmp_path):
    """After a local green one CI round is expected; a dispatch would add its
    own setup and a second cycle. Whatever the job's size or the flags."""
    for kwargs in (
        {},
        {"filter_input": "filter"},
        {"workflow": "Nightly"},
        {"workflow": "Nightly", "filter_input": "filter"},
        {"dispatchable": False},
        {"ids": 0},
    ):
        p = base(tmp_path, **kwargs)
        remote = p["remote"]
        assert remote["ci_is_lab"] is False, kwargs
        assert remote["mode"] == "push", kwargs
        assert remote["marker"] is False, kwargs
        assert "verified locally" in remote["reason"], kwargs
        assert "same run" in remote["reason"], kwargs


def test_ci_is_lab_with_a_fast_job_is_a_plain_push(tmp_path):
    for kwargs in ({}, {"filter_input": "filter"}, {"local_step": False}):
        p = base(tmp_path, job="lint", step=LINT_STEP, ci_is_lab=True, **kwargs)
        remote = p["remote"]
        assert remote["ci_is_lab"] is True, kwargs
        assert remote["job_class"] == "fast"
        assert remote["mode"] == "push", kwargs
        assert remote["marker"] is False
        assert remote["wait_bound_s"] == 60
        assert "under the remote floor" in remote["reason"]


def test_ci_is_lab_slow_job_not_dispatchable_is_a_plain_push_with_lever_11(tmp_path):
    p = base(tmp_path, ci_is_lab=True, dispatchable=False, filter_input="filter")
    remote = p["remote"]
    assert remote["mode"] == "push"
    assert remote["marker"] is False
    assert "lever 11" in remote["reason"]


def test_ci_is_lab_slow_job_with_filter_input_is_a_filtered_dispatch(tmp_path):
    for kwargs in ({"ci_is_lab": True}, {"local_step": False}):
        p = base(tmp_path, filter_input="filter", **kwargs)
        remote = p["remote"]
        assert remote["mode"] == "dispatch-filtered", kwargs
        assert remote["marker"] is True
        assert remote["filter_input"] == "filter"
        assert remote["wait_bound_s"] == 915


def test_ci_is_lab_slow_job_without_filter_input_offers_one(tmp_path):
    p = base(tmp_path, ci_is_lab=True)
    remote = p["remote"]
    assert remote["mode"] == "offer-filter"
    assert remote["marker"] is False
    assert remote["on_accept"] == {"mode": "dispatch-filtered", "marker": True}
    assert remote["on_decline"] == {
        "mode": "push",
        "marker": False,
    }  # never a whole-workflow dispatch
    assert "runner minutes" in remote["reason"]


def test_ci_is_lab_slow_job_without_ids_has_nothing_to_isolate(tmp_path):
    p = base(tmp_path, ci_is_lab=True, ids=0, filter_input="filter")
    assert p["remote"]["mode"] == "push"
    assert p["remote"]["marker"] is False
    assert "nothing to isolate" in p["remote"]["reason"]


def test_unmeasured_job_is_treated_as_slow_remotely(tmp_path):
    p = base(
        tmp_path,
        job="nightly",
        step="Run make test",
        workflow="Nightly",
        ids=2,
        filter_input="tests",
        local_step=False,
    )
    remote = p["remote"]
    assert remote["job_class"] == "unmeasured"
    assert remote["mode"] == "dispatch-filtered"
    assert (
        remote["wait_bound_s"] is None
    )  # the skill substitutes the longest measured bound


def test_job_missing_from_the_profile_is_unmeasured(tmp_path):
    p = base(
        tmp_path,
        job="docs",
        step="Run mkdocs build",
        workflow="Docs",
        ids=2,
        ci_is_lab=True,
    )
    assert p["remote"]["job_class"] == "unmeasured"
    assert p["local"]["step_class"] == "unmeasured"
    assert p["remote"]["mode"] == "offer-filter"


def test_remote_floor_flag_moves_the_line(tmp_path):
    p = base(
        tmp_path,
        job="lint",
        step=LINT_STEP,
        ids=2,
        ci_is_lab=True,
        filter_input="filter",
        isolate_remote="10s",
    )
    assert (
        p["remote"]["job_class"] == "slow"
        and p["remote"]["mode"] == "dispatch-filtered"
    )
    p = base(
        tmp_path, ids=3, ci_is_lab=True, filter_input="filter", isolate_remote="1h"
    )
    assert p["remote"]["job_class"] == "fast" and p["remote"]["mode"] == "push"


def test_a_three_minute_job_is_not_isolated_in_ci(tmp_path):
    """The remote floor exists because an isolated CI run still pays checkout
    and setup (1–3 min): isolating a 3-minute job saves nothing."""
    profile = profile_fixture()
    profile["jobs"][1]["median_s"] = 180.0  # lint job: 3 minutes
    path = tmp_path / "profile.json"
    path.write_text(json.dumps(profile))
    p = plan(
        path,
        "--workflow",
        "CI",
        "--job",
        "lint",
        "--step",
        LINT_STEP,
        "--ids",
        "2",
        "--dispatchable",
        "--no-local-step",
        "--filter-input",
        "filter",
    )
    assert p["remote"]["job_class"] == "fast"
    assert p["remote"]["mode"] == "push"


def test_bad_duration_is_a_usage_error(tmp_path):
    result = run(
        "--profile",
        write_profile(tmp_path),
        "--workflow",
        "CI",
        "--job",
        "pytest",
        "--step",
        PYTEST_STEP,
        "--ids",
        "1",
        "--isolate-local",
        "soon",
    )
    assert result.returncode == 2
    assert "soon" in result.stderr


def test_text_output_names_both_decisions(tmp_path):
    result = run(
        "--profile",
        write_profile(tmp_path),
        "--workflow",
        "CI",
        "--job",
        "pytest",
        "--step",
        PYTEST_STEP,
        "--ids",
        "3",
        "--dispatchable",
        "--no-local-step",
        "--filter-input",
        "filter",
    )
    assert result.returncode == 0, result.stderr
    out = result.stdout
    assert "no rung" in out
    assert "dispatch-filtered" in out and "[skip ci]" in out and "CI is the lab" in out
    result = run(
        "--profile",
        write_profile(tmp_path),
        "--workflow",
        "CI",
        "--job",
        "pytest",
        "--step",
        PYTEST_STEP,
        "--ids",
        "3",
        "--dispatchable",
        "--local-step",
    )
    out = result.stdout
    assert (
        "rung 0" in out
        and "rung 1" in out
        and "verified locally" in out
        and "push" in out
    )


# ------------------------------------------ the real profiler output, end to end


def test_plan_reads_the_profiler_output_when_job_names_collide(tmp_path):
    """Copilot on PR #61: ci_profile.py sets `name` to `CI / pytest` when two
    workflows share a job name and keeps the jobs-API name in `job`; the
    planner must match on `job`, or every such job reads as unmeasured."""
    profiler = REPO_ROOT / "plugins/repo-hygiene/skills/ci-fix/scripts/ci_profile.py"

    def job_record(workflow, seconds):
        end = f"2026-01-01T00:{seconds // 60:02d}:{seconds % 60 + 10:02d}Z"
        return {
            "name": "pytest",
            "workflow_name": workflow,
            "conclusion": "success",
            "status": "completed",
            "created_at": "2026-01-01T00:00:00Z",
            "started_at": "2026-01-01T00:00:10Z",
            "completed_at": end,
            "steps": [
                {
                    "name": PYTEST_STEP,
                    "started_at": "2026-01-01T00:00:10Z",
                    "completed_at": end,
                    "conclusion": "success",
                }
            ],
        }

    run_file = tmp_path / "r1.json"
    run_file.write_text(
        json.dumps(
            {
                "total_count": 2,
                "jobs": [job_record("CI", 20), job_record("Nightly", 600)],
            }
        )
    )
    out = subprocess.run(
        [sys.executable, str(profiler), "--json", str(run_file)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert out.returncode == 0, out.stderr
    profile = json.loads(out.stdout)
    assert {j["name"] for j in profile["jobs"]} == {"CI / pytest", "Nightly / pytest"}
    path = tmp_path / "profile.json"
    path.write_text(out.stdout)
    p = plan(
        path,
        "--workflow",
        "CI",
        "--job",
        "pytest",
        "--step",
        PYTEST_STEP,
        "--ids",
        "2",
        "--local-step",
    )
    assert p["local"]["step_class"] == "fast" and p["local"]["step_expected_s"] == 20.0
    p = plan(
        path,
        "--workflow",
        "Nightly",
        "--job",
        "pytest",
        "--step",
        PYTEST_STEP,
        "--ids",
        "2",
        "--no-local-step",
    )
    assert p["remote"]["job_class"] == "slow" and p["remote"]["job_expected_s"] == 600.0
