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
    assert json.loads(result.stdout) == {"format": None, "failures": [], "failures_quoted": [], "packages": []}
    assert "no failures recognized" in result.stderr.lower()


def test_unknown_format_is_a_usage_error():
    result = run("--format", "mocha", FIXTURES / "log_pytest.txt")
    assert result.returncode == 2


def test_missing_file_is_a_usage_error(tmp_path):
    result = run(tmp_path / "nope.log")
    assert result.returncode == 2
    assert "nope.log" in result.stderr


# ------------------------------------------------- PR #49 review findings


def test_pytest_ids_with_whitespace_in_param_brackets_are_kept(tmp_path):
    """CodeRabbit: `\\S+` dropped `test_case[case one]`; the ID runs to the
    ` - reason` delimiter (summary) or to ` FAILED` (verbose)."""
    log = tmp_path / "ws.log"
    log.write_text(
        "2026-09-08T10:00:00.0000000Z FAILED tests/test_x.py::test_case[case one] - AssertionError\n"
        "2026-09-08T10:00:01.0000000Z tests/test_x.py::test_case[two words here] FAILED [ 50%]\n"
        "2026-09-08T10:00:02.0000000Z ERROR tests/test_x.py::test_setup[a b]\n"
    )
    data = extract(log)
    assert data["failures"] == [
        "tests/test_x.py::test_case[case one]",
        "tests/test_x.py::test_case[two words here]",
        "tests/test_x.py::test_setup[a b]",
    ]


def test_json_carries_shell_quoted_ids(tmp_path):
    """Greptile + CodeRabbit: a contributor-controlled test name can carry
    shell syntax; `$(...)` inside double quotes executes. The JSON carries a
    shell-safe form the skill must use verbatim in local commands."""
    log = tmp_path / "evil.log"
    log.write_text("2026-09-08T10:00:00.0000000Z FAILED tests/test_x.py::test_case[$(touch /tmp/pwned)] - boom\n")
    data = extract(log)
    assert data["failures"] == ["tests/test_x.py::test_case[$(touch /tmp/pwned)]"]
    assert data["failures_quoted"] == ["'tests/test_x.py::test_case[$(touch /tmp/pwned)]'"]
    plain = extract(FIXTURES / "log_pytest.txt")
    assert plain["failures_quoted"][0] == "tests/test_sample.py::test_rollup_total"  # safe IDs stay bare


def test_pytest_ids_are_parsed_bracket_aware(tmp_path):
    """CodeRabbit (wave 2): a ` - ` or ` FAILED` inside `[param ids]` must not
    end the ID; only a delimiter at bracket depth 0 does."""
    log = tmp_path / "brackets.log"
    log.write_text(
        "2026-09-08T10:00:00.0000000Z FAILED tests/test_x.py::test_range[a - b] - AssertionError\n"
        "2026-09-08T10:00:01.0000000Z tests/test_x.py::test_words[x FAILED y] FAILED [ 50%]\n"
        "2026-09-08T10:00:02.0000000Z ERROR tests/test_x.py::test_setup[p - q - r]\n"
        "2026-09-08T10:00:03.0000000Z FAILED tests/test_x.py::test_nested[a[1] - b[2]] - boom\n"
    )
    data = extract(log)
    assert data["failures"] == [
        "tests/test_x.py::test_range[a - b]",
        "tests/test_x.py::test_words[x FAILED y]",
        "tests/test_x.py::test_setup[p - q - r]",
        "tests/test_x.py::test_nested[a[1] - b[2]]",
    ]


# ------------------------------------------------- deep-review findings (PR #49)


def test_verbose_non_failure_lines_containing_verdict_words_are_ignored(tmp_path):
    """A `-v` SKIPPED/PASSED line whose free text contains ERROR or FAILED is
    not a failure: the node ID ends at the first whitespace outside brackets
    and the very next token must be the verdict."""
    log = tmp_path / "v.log"
    log.write_text(
        "2026-09-08T10:00:00.0000000Z test_a1.py::test_a SKIPPED (waiting on upstream ERROR to be fixed)  [ 50%]\n"
        "2026-09-08T10:00:01.0000000Z test_a1.py::test_b PASSED  [ 75%]\n"
        "2026-09-08T10:00:02.0000000Z test_a1.py::test_c[x y] FAILED  [100%]\n"
    )
    assert extract(log)["failures"] == ["test_a1.py::test_c[x y]"]


def test_cargo_show_output_headers_for_passing_tests_are_not_failures(tmp_path):
    """`cargo test -- --show-output` prints `---- X stdout ----` under a
    `successes:` section too; only headers after the `failures:` marker count."""
    log = tmp_path / "cargo.log"
    log.write_text(
        "2026-09-08T10:00:00.0000000Z successes:\n"
        "2026-09-08T10:00:01.0000000Z \n"
        "2026-09-08T10:00:02.0000000Z ---- tests::passing_with_output stdout ----\n"
        "2026-09-08T10:00:03.0000000Z hello\n"
        "2026-09-08T10:00:04.0000000Z \n"
        "2026-09-08T10:00:05.0000000Z failures:\n"
        "2026-09-08T10:00:06.0000000Z \n"
        "2026-09-08T10:00:07.0000000Z ---- tests::failing_test stdout ----\n"
        "2026-09-08T10:00:08.0000000Z thread 'tests::failing_test' panicked\n"
        "2026-09-08T10:00:09.0000000Z test result: FAILED. 1 passed; 1 failed\n"
    )
    data = extract(log)
    assert data["format"] == "cargo"
    assert data["failures"] == ["tests::failing_test"]
