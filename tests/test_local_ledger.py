"""tests/test_local_ledger.py — the local duration ledger.

local_ledger.py records how long a CI step's command took on this machine
(rung 1 and rung 1s runs, successes only, last 10 per step) and reports the
median, so ladder_plan.py can key the local decision on local time rather
than the CI proxy. The file is machine-level under $XDG_CACHE_HOME, never in
the repo.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "plugins/repo-hygiene/skills/ci-fix/scripts/local_ledger.py"

assert SCRIPT.is_file(), f"local_ledger.py not found at {SCRIPT}"

KEY = ["--workflow", "CI", "--job", "pytest", "--step", "Run uv run pytest"]


def run(*args, env=None):
    merged = {**os.environ, **(env or {})}
    return subprocess.run(
        [sys.executable, str(SCRIPT), *[str(a) for a in args]],
        capture_output=True,
        text=True,
        env=merged,
        check=False,
    )


def record(ledger, seconds, conclusion="success", key=KEY):
    result = run(
        "record",
        "--ledger",
        ledger,
        *key,
        "--seconds",
        seconds,
        "--conclusion",
        conclusion,
    )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def median(ledger, key=KEY):
    result = run("median", "--ledger", ledger, *key)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def test_median_of_recorded_successes(tmp_path):
    ledger = tmp_path / "ledger.json"
    for s in (70, 50, 60):
        record(ledger, s)
    m = median(ledger)
    assert m == {"samples": 3, "median_s": 60.0}


def test_failures_are_not_recorded(tmp_path):
    ledger = tmp_path / "ledger.json"
    record(ledger, 50)
    out = record(ledger, 500, conclusion="failure")
    assert out["recorded"] is False
    assert median(ledger) == {"samples": 1, "median_s": 50.0}


def test_keeps_the_last_ten_samples(tmp_path):
    ledger = tmp_path / "ledger.json"
    for s in range(1, 13):  # 1..12
        record(ledger, s)
    m = median(ledger)
    assert m["samples"] == 10
    assert m["median_s"] == 7.5  # median of 3..12


def test_missing_ledger_yields_no_median(tmp_path):
    assert median(tmp_path / "absent.json") == {"samples": 0, "median_s": None}


def test_keys_are_independent(tmp_path):
    ledger = tmp_path / "ledger.json"
    record(ledger, 10)
    record(ledger, 900, key=["--workflow", "CI", "--job", "lint", "--step", "Run ruff"])
    record(
        ledger,
        300,
        key=["--workflow", "Nightly", "--job", "pytest", "--step", "Run uv run pytest"],
    )
    assert median(ledger)["median_s"] == 10.0
    assert (
        median(ledger, key=["--workflow", "CI", "--job", "lint", "--step", "Run ruff"])[
            "median_s"
        ]
        == 900.0
    )


def test_default_path_is_under_xdg_cache_home(tmp_path):
    cache = tmp_path / "cache"
    result = run(
        "record",
        "--repo",
        "acme/widgets",
        *KEY,
        "--seconds",
        "42",
        "--conclusion",
        "success",
        env={"XDG_CACHE_HOME": str(cache)},
    )
    assert result.returncode == 0, result.stderr
    out = json.loads(result.stdout)
    expected = cache / "ci-fix" / "acme--widgets.json"
    assert Path(out["ledger"]) == expected
    assert expected.is_file()
    data = json.loads(expected.read_text())
    assert data["version"] == 1
    assert data["samples"][0]["seconds"] == 42.0
    assert data["samples"][0]["at"].endswith("Z")


def test_path_command_prints_the_default_without_writing(tmp_path):
    cache = tmp_path / "cache"
    result = run("path", "--repo", "acme/widgets", env={"XDG_CACHE_HOME": str(cache)})
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == str(cache / "ci-fix" / "acme--widgets.json")
    assert not (cache / "ci-fix").exists()


def test_repo_or_ledger_is_required(tmp_path):
    result = run("median", *KEY)
    assert result.returncode == 2
    assert "--ledger" in result.stderr and "--repo" in result.stderr


def test_ledger_file_shape_is_what_ladder_plan_reads(tmp_path):
    ledger = tmp_path / "ledger.json"
    record(ledger, 12.5)
    data = json.loads(ledger.read_text())
    assert set(data) == {"version", "samples"}
    assert set(data["samples"][0]) == {
        "workflow",
        "workflow_path",
        "job",
        "step",
        "seconds",
        "at",
    }


def test_workflow_path_is_part_of_the_identity(tmp_path):
    """CodeRabbit on PR #61: two workflow files may share a `name:`; keying on
    the display name alone would lend one file's local median to the other."""
    ledger = tmp_path / "ledger.json"
    ci = [
        "--workflow",
        "CI",
        "--workflow-path",
        ".github/workflows/ci.yml",
        "--job",
        "test",
        "--step",
        "Run tests",
    ]
    arm = [
        "--workflow",
        "CI",
        "--workflow-path",
        ".github/workflows/ci-arm.yml",
        "--job",
        "test",
        "--step",
        "Run tests",
    ]
    record(ledger, 20, key=ci)
    record(ledger, 900, key=arm)
    assert median(ledger, key=ci) == {"samples": 1, "median_s": 20.0}
    assert median(ledger, key=arm) == {"samples": 1, "median_s": 900.0}
    # a query with no path is its own bucket, never a wildcard over the two above
    assert median(
        ledger, key=["--workflow", "CI", "--job", "test", "--step", "Run tests"]
    ) == {
        "samples": 0,
        "median_s": None,
    }


def test_seconds_must_be_finite_and_non_negative(tmp_path):
    """CodeRabbit on PR #61: a negative value would classify as `fast`, and a
    persisted nan or inf raises in ladder_plan's duration formatter."""
    ledger = tmp_path / "ledger.json"
    for bad in ("-5", "nan", "inf", "-inf"):
        result = run(
            "record",
            "--ledger",
            ledger,
            *KEY,
            "--seconds",
            bad,
            "--conclusion",
            "success",
        )
        assert result.returncode == 2, bad
        assert "--seconds" in result.stderr, bad
    assert not ledger.exists()
    assert median(ledger) == {"samples": 0, "median_s": None}
