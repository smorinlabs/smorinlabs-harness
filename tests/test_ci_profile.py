"""tests/test_ci_profile.py — duration profile for GitHub Actions jobs.

The script is the measuring half of ci-fix's Iron Law (measure before you
run): given one `/actions/runs/{id}/jobs` response per sampled run, it emits
per-job median/max duration, queue wait, a slow/fast/unmeasured class against
a threshold, the slowest step, and a data-derived CI-wait bound.
"""

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "plugins/repo-hygiene/skills/ci-fix/scripts/ci_profile.py"
FIXTURES = REPO_ROOT / "tests/fixtures/ci_fix"
FAST_RUN = FIXTURES / "jobs_fast_run.json"  # real run 34088065449, 4 jobs, all < 15s

assert SCRIPT.is_file(), f"ci_profile.py not found at {SCRIPT}"


def run(*args):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *[str(a) for a in args]],
        capture_output=True,
        text=True,
    )


def profile(*args):
    result = run("--json", *args)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def by_name(data):
    return {j["name"]: j for j in data["jobs"]}


def job(name, created, started, completed, steps=(), conclusion="success"):
    """Build one job record in the shape the REST jobs endpoint returns."""
    return {
        "name": name,
        "conclusion": conclusion,
        "status": "completed" if completed else "in_progress",
        "created_at": created,
        "started_at": started,
        "completed_at": completed,
        "steps": [
            {"name": n, "started_at": s, "completed_at": c, "conclusion": "success"}
            for n, s, c in steps
        ],
    }


def write_run(path, jobs):
    path.write_text(json.dumps({"total_count": len(jobs), "jobs": jobs}))
    return path


# ---------------------------------------------------------------- real fixture


def test_real_run_all_jobs_fast_at_default_threshold():
    data = profile(FAST_RUN)
    assert data["threshold_s"] == 120
    assert data["runs_sampled"] == 1
    jobs = by_name(data)
    assert set(jobs) == {"plugin-validate", "static-checks", "pytest", "gen-check"}
    assert all(j["class"] == "fast" for j in jobs.values())
    # plugin-validate ran 05:46:10 → 05:46:23 = 13s; queued 05:46:07 → 05:46:10 = 3s
    assert jobs["plugin-validate"]["median_s"] == 13
    assert jobs["plugin-validate"]["queue_median_s"] == 3


def test_threshold_flag_reclassifies_real_run():
    jobs = by_name(profile("--threshold", "10s", FAST_RUN))
    assert jobs["plugin-validate"]["class"] == "slow"  # 13s > 10s
    assert jobs["pytest"]["class"] == "slow"  # 12s
    assert jobs["static-checks"]["class"] == "fast"  # 7s
    assert jobs["gen-check"]["class"] == "fast"  # 6s


def test_slowest_step_comes_from_step_timestamps():
    jobs = by_name(profile(FAST_RUN))
    # In the real run, `Run npm install -g @anthropic-ai/claude-code` took 3s,
    # the longest step of plugin-validate; pytest's longest is `Run uv run pytest` (5s).
    assert jobs["pytest"]["slowest_step"]["name"] == "Run uv run pytest"
    assert jobs["pytest"]["slowest_step"]["median_s"] == 5


def test_text_output_lists_jobs_slowest_first():
    result = run(FAST_RUN)
    assert result.returncode == 0, result.stderr
    lines = [l for l in result.stdout.splitlines() if l.strip()]
    order = [l.split()[1] for l in lines if l.startswith(("fast", "slow", "unmeasured"))]
    assert order[0] == "plugin-validate"  # 13s, the longest
    assert order[-1] == "gen-check"  # 6s, the shortest
    assert "threshold" in result.stdout


# ------------------------------------------------------------- synthetic runs


def test_median_over_multiple_runs_and_in_progress_jobs_are_not_samples(tmp_path):
    r1 = write_run(
        tmp_path / "r1.json",
        [
            job("suite", "2026-01-01T00:00:00Z", "2026-01-01T00:01:00Z", "2026-01-01T00:16:00Z"),
            job("lint", "2026-01-01T00:00:00Z", "2026-01-01T00:00:30Z", "2026-01-01T00:01:00Z"),
        ],
    )
    r2 = write_run(
        tmp_path / "r2.json",
        [
            job("suite", "2026-01-01T01:00:00Z", "2026-01-01T01:00:20Z", "2026-01-01T01:20:20Z"),
            job("lint", "2026-01-01T01:00:00Z", "2026-01-01T01:00:10Z", "2026-01-01T01:00:50Z"),
        ],
    )
    r3 = write_run(
        tmp_path / "r3.json",
        [
            # still running: no completed_at → not a duration sample
            job("suite", "2026-01-01T02:00:00Z", "2026-01-01T02:00:05Z", None),
            job("lint", "2026-01-01T02:00:00Z", "2026-01-01T02:00:05Z", "2026-01-01T02:00:35Z"),
        ],
    )
    data = profile(r1, r2, r3)
    assert data["runs_sampled"] == 3
    jobs = by_name(data)
    suite, lint = jobs["suite"], jobs["lint"]
    assert suite["samples"] == 2 and suite["in_progress"] == 1
    assert suite["median_s"] == (900 + 1200) / 2  # 15m and 20m → 17.5m
    assert suite["max_s"] == 1200
    assert suite["class"] == "slow"
    assert lint["samples"] == 3
    assert lint["median_s"] == 30 and lint["class"] == "fast"


def test_wait_bound_is_derived_from_measured_duration_and_queue(tmp_path):
    r = write_run(
        tmp_path / "r.json",
        [job("suite", "2026-01-01T00:00:00Z", "2026-01-01T00:02:00Z", "2026-01-01T00:12:00Z")],
    )
    suite = by_name(profile(r))["suite"]
    # 10m run + 2m queue = 12m; ×1.5 = 18m = 1080s
    assert suite["queue_median_s"] == 120
    assert suite["wait_bound_s"] == 1080


def test_wait_bound_has_a_floor_for_tiny_jobs():
    jobs = by_name(profile(FAST_RUN))
    assert all(j["wait_bound_s"] >= 60 for j in jobs.values())


def test_job_with_no_completed_sample_is_unmeasured(tmp_path):
    r = write_run(
        tmp_path / "r.json",
        [job("flaky-e2e", "2026-01-01T00:00:00Z", "2026-01-01T00:00:05Z", None)],
    )
    j = by_name(profile(r))["flaky-e2e"]
    assert j["samples"] == 0
    assert j["class"] == "unmeasured"
    assert j["median_s"] is None


def test_skipped_and_cancelled_jobs_are_not_samples(tmp_path):
    """A skipped job has equal timestamps (0s); a cancelled one is truncated.
    Neither is a measurement of the job's shape (real shape seen in run
    34087870904: conclusion skipped, started_at == completed_at, no steps)."""
    r1 = write_run(
        tmp_path / "r1.json",
        [
            job("e2e", "2026-01-01T00:00:00Z", "2026-01-01T00:00:00Z", "2026-01-01T00:00:00Z", conclusion="skipped"),
            job("suite", "2026-01-01T00:00:00Z", "2026-01-01T00:00:10Z", "2026-01-01T00:01:10Z", conclusion="cancelled"),
        ],
    )
    r2 = write_run(
        tmp_path / "r2.json",
        [job("suite", "2026-01-01T01:00:00Z", "2026-01-01T01:00:10Z", "2026-01-01T01:10:10Z")],
    )
    jobs = by_name(profile(r1, r2))
    assert jobs["e2e"]["class"] == "unmeasured" and jobs["e2e"]["samples"] == 0
    assert jobs["e2e"]["excluded"] == 1
    assert jobs["suite"]["samples"] == 1 and jobs["suite"]["excluded"] == 1
    assert jobs["suite"]["median_s"] == 600  # the cancelled 60s run did not drag it down


def test_accepts_bare_job_list(tmp_path):
    p = tmp_path / "list.json"
    p.write_text(
        json.dumps(
            [job("x", "2026-01-01T00:00:00Z", "2026-01-01T00:00:01Z", "2026-01-01T00:00:31Z")]
        )
    )
    assert by_name(profile(p))["x"]["median_s"] == 30


# --------------------------------------------------------- threshold parsing


def test_threshold_accepts_common_duration_spellings(tmp_path):
    r = write_run(
        tmp_path / "r.json",
        [job("j", "2026-01-01T00:00:00Z", "2026-01-01T00:00:00Z", "2026-01-01T00:05:00Z")],
    )
    for spelling, seconds in [("2m", 120), ("90s", 90), ("1h", 3600), ("1h30m", 5400), ("2m30s", 150), ("120", 120)]:
        assert profile("--threshold", spelling, r)["threshold_s"] == seconds, spelling


def test_bad_threshold_is_a_usage_error():
    result = run("--threshold", "soon", FAST_RUN)
    assert result.returncode == 2
    assert "threshold" in result.stderr.lower()


def test_missing_file_is_a_usage_error(tmp_path):
    result = run(tmp_path / "nope.json")
    assert result.returncode == 2
    assert "nope.json" in result.stderr


# ------------------------------------------------- PR #49 review findings


def test_same_job_name_in_two_workflows_is_two_rows(tmp_path):
    """Greptile: keying by display name alone merged `test` from two workflows
    into one median. The jobs API carries `workflow_name`; key on both."""
    r1 = write_run(tmp_path / "r1.json", [
        {**job("test", "2026-01-01T00:00:00Z", "2026-01-01T00:00:10Z", "2026-01-01T00:00:40Z"), "workflow_name": "CI"},
        {**job("test", "2026-01-01T00:00:00Z", "2026-01-01T00:00:10Z", "2026-01-01T00:20:10Z"), "workflow_name": "Nightly"},
    ])
    data = profile(r1)
    rows = {(j["workflow_name"], j["job"]): j for j in data["jobs"]}
    assert set(rows) == {("CI", "test"), ("Nightly", "test")}
    assert rows[("CI", "test")]["median_s"] == 30 and rows[("CI", "test")]["class"] == "fast"
    assert rows[("Nightly", "test")]["median_s"] == 1200 and rows[("Nightly", "test")]["class"] == "slow"
    text = run(r1).stdout
    assert "Nightly / test" in text and "CI / test" in text  # disambiguated only when names collide


def test_truncated_jobs_page_is_reported(tmp_path):
    """Greptile: the jobs endpoint pages at 30 by default; a run with more jobs
    than the page silently loses matrix cells unless total_count is checked."""
    p = tmp_path / "r.json"
    p.write_text(json.dumps({"total_count": 45, "jobs": [job("a", "2026-01-01T00:00:00Z", "2026-01-01T00:00:01Z", "2026-01-01T00:00:31Z")]}))
    result = run("--json", p)
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["truncated_runs"] == [str(p)]
    assert "45" in result.stderr and "per_page=100" in result.stderr


def test_unmeasured_wait_bound_is_documented_as_null():
    doc = SCRIPT.read_text()
    assert "wait_bound_s" in doc and "null" in doc.split('"""')[1].lower()  # the module docstring says it
    assert "UNITS" not in doc  # Copilot: dead constant removed
