"""tests/test_extract_failures.py — failing-test IDs from a CI job log.

The script is the localizing half of ci-fix's targeted-repro loop: given a
GitHub Actions job log (timestamp-prefixed, possibly ANSI-colored), it emits
the failing test identifiers for pytest, jest, cargo, or go so the narrowest
local command can be built. Exit 0 = found, 1 = none recognized, 2 = usage.
"""

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "plugins/repo-hygiene/skills/ci-fix/scripts/extract_failures.py"
FIXTURES = REPO_ROOT / "tests/fixtures/ci_fix"

assert SCRIPT.is_file(), f"extract_failures.py not found at {SCRIPT}"


def run(*args, stdin=None):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *[str(a) for a in args]],
        capture_output=True,
        text=True,
        input=stdin,
    )


def extract(*args):
    result = run("--json", *args)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


# ---------------------------------------------------------------- pytest (real)


def test_pytest_real_log_yields_node_ids_without_reasons():
    data = extract(FIXTURES / "log_pytest.txt")
    assert data["format"] == "pytest"
    assert data["failures"] == [
        "tests/test_sample.py::test_rollup_total",
        "tests/test_sample.py::TestAuth::test_login",
        "tests/test_sample.py::test_param[2]",
        "tests/test_sample.py::test_error_in_setup",
    ]


def test_text_output_is_one_id_per_line():
    result = run(FIXTURES / "log_pytest.txt")
    assert result.returncode == 0
    assert result.stdout.splitlines()[0] == "tests/test_sample.py::test_rollup_total"
    assert len(result.stdout.splitlines()) == 4


def test_ansi_escapes_and_timestamps_are_stripped():
    data = extract(FIXTURES / "log_pytest_ansi.txt")
    assert data["failures"] == ["tests/test_color.py::test_ansi"]


def test_reads_stdin_when_no_file_given():
    log = FIXTURES.joinpath("log_pytest.txt").read_text()
    result = run("--json", stdin=log)
    assert result.returncode == 0, result.stderr
    assert len(json.loads(result.stdout)["failures"]) == 4


# ------------------------------------------------------------------------ jest


def test_jest_yields_suite_and_test_names_deduplicated():
    data = extract(FIXTURES / "log_jest.txt")
    assert data["format"] == "jest"
    # the ● block names are canonical; the ✕ lines carry the same tests
    assert data["failures"] == [
        "login flow › rejects a bad password",
        "login flow › locks after five attempts",
    ]


# ----------------------------------------------------------------------- cargo


def test_cargo_yields_full_test_paths_once():
    data = extract(FIXTURES / "log_cargo.txt")
    assert data["format"] == "cargo"
    # each name appears in `---- X stdout ----`, the `failures:` list, and the
    # running list; it must come out exactly once
    assert data["failures"] == ["parser::tests::parses_nested", "rollup::tests::sums_totals"]


# -------------------------------------------------------------------------- go


def test_go_yields_leaf_failures_and_packages():
    data = extract(FIXTURES / "log_go.txt")
    assert data["format"] == "go"
    # a parent that fails only because a subtest failed is not a separate target
    assert data["failures"] == ["TestRollup/nested", "TestLogin"]
    assert data["packages"] == ["github.com/acme/api/internal/rollup"]


# ------------------------------------------------------------ format handling


def test_explicit_format_overrides_detection():
    result = run("--format", "go", "--json", FIXTURES / "log_pytest.txt")
    assert result.returncode == 1  # no go failures in a pytest log
    assert json.loads(result.stdout)["failures"] == []


def test_no_failures_recognized_exits_one_with_empty_list():
    result = run("--json", FIXTURES / "log_no_failures.txt")
    assert result.returncode == 1
    assert json.loads(result.stdout) == {"format": None, "failures": [], "packages": []}
    assert "no failures recognized" in result.stderr.lower()


def test_unknown_format_is_a_usage_error():
    result = run("--format", "mocha", FIXTURES / "log_pytest.txt")
    assert result.returncode == 2


def test_missing_file_is_a_usage_error(tmp_path):
    result = run(tmp_path / "nope.log")
    assert result.returncode == 2
    assert "nope.log" in result.stderr
