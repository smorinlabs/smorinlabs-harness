"""Behavioral acceptance cases for scoped validation, timing identity and remote evidence."""

import json
import subprocess
import sys

import pytest
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
    for flag in (
        "isolate_local",
        "isolate_remote",
        "bundle_seconds",
        "full_step_reason",
        "context",
    ):
        if flag in flags:
            args += ["--" + flag.replace("_", "-"), flags.pop(flag)]
    args.append(
        "--dispatchable" if flags.pop("dispatchable", True) else "--not-dispatchable"
    )
    args.append("--local-step" if flags.pop("local_step", True) else "--no-local-step")
    args.append("--ci-is-lab" if flags.pop("ci_is_lab", False) else "--not-ci-is-lab")
    if "local_env" in flags:
        args += ["--local-env", flags.pop("local_env")]
    filter_input = flags.pop("filter_input", None)
    if filter_input:
        args += ["--filter-input", filter_input]
    ledger = flags.pop("ledger", None)
    if ledger:
        args += ["--ledger", str(ledger)]
    assert not flags, f"unused flags: {flags}"
    return plan(write_profile(tmp_path), *args)


@pytest.mark.parametrize(
    "bundle,scope",
    [(20, "bundle"), (30, "bundle"), (31, "ids"), (200, "ids"), (None, "ids")],
)
def test_shortcut_uses_the_measured_complete_bundle(tmp_path, bundle, scope):
    flags = {} if bundle is None else {"bundle_seconds": bundle}
    local = base(tmp_path, **flags)["local"]
    assert local["scope"] == scope
    assert local["rung_0"] == (scope == "ids")
    assert local["rung_1"] == (scope == "bundle")


def test_fast_step_proxy_does_not_make_the_complete_bundle_fast(tmp_path):
    local = base(tmp_path, job="lint", step=LINT_STEP)["local"]
    assert local["step_expected_s"] == 15
    assert local["scope"] == "ids"
    assert local["rung_1"] is False


def test_nine_minute_step_is_not_automatically_repeated(tmp_path):
    local = base(tmp_path)["local"]
    assert local["step_expected_s"] == 540
    assert local["rung_0"] is True and local["rung_1"] is False
    assert local["rung_1_gate"] == "not-needed"


def test_shared_configuration_change_can_require_the_full_step(tmp_path):
    local = base(tmp_path, full_step_reason="shared fixture changed all tests")["local"]
    assert local["scope"] == "full-step"
    assert local["rung_0"] is True and local["rung_1"] is True
    assert local["rung_1_gate"] == "run"
    assert "shared fixture" in local["reason"]


def test_long_required_validation_uses_background_wait_without_new_scope_gate(tmp_path):
    local = base(
        tmp_path,
        workflow="Nightly",
        full_step_reason="compiler settings affect all targets",
    )["local"]
    assert local["step_expected_s"] == 1750
    assert local["rung_1"] is True and local["rung_1_background"] is True
    assert local["rung_1_gate"] == "run"


def test_missing_ids_requires_localization_instead_of_blind_full_suite(tmp_path):
    local = base(tmp_path, ids=0)["local"]
    assert local["scope"] == "localize"
    assert not local["rung_0"] and not local["rung_1"]
    justified = base(
        tmp_path, ids=0, full_step_reason="compiler is the smallest failing check"
    )["local"]
    assert justified["scope"] == "full-step" and justified["entry_rung"] == 1


def test_no_local_environment_keeps_remote_diagnosis_available(tmp_path):
    p = base(tmp_path, local_step=False, filter_input="test_filter")
    assert p["local"]["scope"] == "unavailable"
    assert p["remote"]["ci_is_lab"] is True
    assert p["remote"]["mode"] == "dispatch-filtered"
    assert p["remote"]["marker"] is False


def test_explicit_bundle_threshold_changes_only_the_bundle_decision(tmp_path):
    assert (
        base(tmp_path, bundle_seconds=20, isolate_local="10s")["local"]["scope"]
        == "ids"
    )
    assert base(tmp_path, bundle_seconds=20)["local"]["scope"] == "bundle"


@pytest.mark.parametrize(
    "local_step,ci_is_lab,dispatchable,ids,filter_input,mode",
    [
        (True, False, True, 2, "filter", "push"),
        (True, True, True, 2, "filter", "dispatch-filtered"),
        (False, False, True, 2, "filter", "dispatch-filtered"),
        (False, False, False, 2, "filter", "push"),
        (False, False, True, 0, "filter", "push"),
        (False, False, True, 2, None, "offer-filter"),
    ],
)
def test_remote_diagnostics_never_suppress_required_ci(
    tmp_path, local_step, ci_is_lab, dispatchable, ids, filter_input, mode
):
    remote = base(
        tmp_path,
        local_step=local_step,
        ci_is_lab=ci_is_lab,
        dispatchable=dispatchable,
        ids=ids,
        filter_input=filter_input,
    )["remote"]
    assert remote["mode"] == mode and remote["marker"] is False
    assert "unfiltered" in remote["required_coverage"]
    if mode == "offer-filter":
        assert remote["on_accept"]["marker"] is False
        assert remote["on_decline"] == {"mode": "push", "marker": False}


def test_fast_remote_job_does_not_add_a_dispatch(tmp_path):
    remote = base(
        tmp_path, job="lint", step=LINT_STEP, local_step=False, filter_input="filter"
    )["remote"]
    assert remote["mode"] == "push"


def test_remote_threshold_is_independent_of_local_bundle_budget(tmp_path):
    assert (
        base(tmp_path, local_step=False, filter_input="filter", isolate_remote="20m")[
            "remote"
        ]["mode"]
        == "push"
    )


@pytest.mark.parametrize("env,expected", [("host", 15), ("container", 30)])
def test_container_proxy_remains_an_estimate_not_a_measured_shortcut(
    tmp_path, env, expected
):
    local = base(tmp_path, job="lint", step=LINT_STEP, local_env=env)["local"]
    assert local["local_env"] == env and local["step_expected_s"] == expected
    assert local["scope"] == "ids"


def test_unmeasured_container_does_not_become_fast(tmp_path):
    local = base(
        tmp_path,
        workflow="Nightly",
        job="nightly",
        step="Run make test",
        local_env="container",
    )["local"]
    assert local["step_expected_s"] is None and local["scope"] == "ids"


def measured_ledger(tmp_path):
    ledger = tmp_path / "ledger.json"
    context = tmp_path / "context.json"
    context.write_text(
        json.dumps(
            {
                "command": "uv run pytest",
                "scope": "complete step",
                "environment": {"runner": "container", "os": "linux", "arch": "x86_64"},
            }
        )
    )
    script = SCRIPT.with_name("local_ledger.py")
    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "record",
            "--ledger",
            str(ledger),
            "--context",
            str(context),
            "--workflow",
            "CI",
            "--workflow-path",
            CI_PATH,
            "--job",
            "pytest",
            "--step",
            PYTEST_STEP,
            "--seconds",
            "5",
            "--conclusion",
            "success",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    return ledger, context


def test_compatible_local_sample_beats_container_proxy_but_not_scope_rules(tmp_path):
    ledger, context = measured_ledger(tmp_path)
    local = base(tmp_path, ledger=ledger, context=context, local_env="container")[
        "local"
    ]
    assert local["source"] == "ledger" and local["step_expected_s"] == 5
    assert local["scope"] == "ids"  # this sample is a step, not the complete bundle


@pytest.mark.parametrize("change", ["command", "scope", "environment"])
def test_stale_context_cannot_override_current_cost(tmp_path, change):
    ledger, context = measured_ledger(tmp_path)
    data = json.loads(context.read_text())
    data[change] = {"runner": "host"} if change == "environment" else "changed"
    context.write_text(json.dumps(data))
    local = base(tmp_path, ledger=ledger, context=context)["local"]
    assert local["source"] == "profile" and local["step_expected_s"] == 540


def test_same_command_in_another_workflow_does_not_borrow_local_timing(tmp_path):
    ledger, context = measured_ledger(tmp_path)
    local = base(tmp_path, workflow="Nightly", ledger=ledger, context=context)["local"]
    assert local["source"] == "profile" and local["step_expected_s"] == 1750


def test_ledger_without_current_context_is_not_used(tmp_path):
    ledger, _ = measured_ledger(tmp_path)
    local = base(tmp_path, ledger=ledger)["local"]
    assert local["source"] == "profile"


@pytest.mark.parametrize(
    "args",
    [
        ("--bundle-seconds", "nan"),
        ("--bundle-seconds", "-1"),
        ("--ids", "-2"),
        ("--full-step-reason", " "),
    ],
)
def test_invalid_scope_inputs_are_usage_errors(tmp_path, args):
    result = run(
        "--profile",
        write_profile(tmp_path),
        "--job",
        "lint",
        "--step",
        LINT_STEP,
        *args,
    )
    assert result.returncode == 2 and "error:" in result.stderr


def test_text_reports_scope_and_required_coverage(tmp_path):
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
        "2",
        "--no-local-step",
        "--dispatchable",
        "--filter-input",
        "filter",
    )
    assert result.returncode == 0, result.stderr
    assert "unavailable" in result.stdout and "dispatch-filtered" in result.stdout
    assert (
        "no skip marker" in result.stdout and "ordinary unfiltered CI" in result.stdout
    )


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
