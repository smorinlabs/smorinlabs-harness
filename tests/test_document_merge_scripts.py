"""tests/test_document_merge_scripts.py"""

import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
VALIDATE = (
    REPO_ROOT
    / "plugins/document-merge/skills/document-merge/scripts/validate_round_trip.sh"
)


def run_validate(*args):
    return subprocess.run(
        ["bash", str(VALIDATE), *[str(a) for a in args]],
        capture_output=True,
        text=True,
    )


def write(path, text):
    path.write_text(text)
    return path


def test_missing_merged_doc_is_an_error(tmp_path):
    """A merged-doc path that does not exist must fail, not pass vacuously.

    Regression for B4: the loop skipped unreadable paths silently, so a typo'd
    path plus an empty decisions log reported `PASS: 0 markers and 0 entries`.
    """
    log = write(tmp_path / "log.md", "# Decisions log\n\nNo conflicts yet.\n")

    result = run_validate(log, tmp_path / "does-not-exist.md")

    assert result.returncode != 0, (
        f"expected failure for a missing merged doc, got exit 0:\n{result.stdout}"
    )
    assert "does-not-exist.md" in result.stdout + result.stderr


WITHDRAWN_LOG = """# Decisions log

### [x] CFL-001
Resolved in favour of the newer wording.

### [ ] CFL-007
**Status:** Withdrawn — superseded by CFL-001
"""


def test_withdrawn_entry_does_not_fail_the_gate(tmp_path):
    """An ID retired per the ID-hygiene rule must not fail validation forever.

    Regression for B2: cfl_classification.md requires a withdrawn ID to stay in
    the log with a `**Status:** Withdrawn` note, but its inline marker is gone
    from the merged doc — so the gate reported it as an unmatched entry.
    """
    log = write(tmp_path / "log.md", WITHDRAWN_LOG)
    doc = write(tmp_path / "merged.md", "body text <!-- CONFLICT: CFL-001 -->\n")

    result = run_validate(log, doc)

    assert result.returncode == 0, (
        f"withdrawn CFL-007 should not fail the gate:\n{result.stdout}{result.stderr}"
    )


def test_withdrawn_entry_is_reported_not_silently_dropped(tmp_path):
    """Excluding an entry from the comparison must be visible in the output."""
    log = write(tmp_path / "log.md", WITHDRAWN_LOG)
    doc = write(tmp_path / "merged.md", "body text <!-- CONFLICT: CFL-001 -->\n")

    result = run_validate(log, doc)

    assert "CFL-007" in result.stdout and "withdrawn" in result.stdout.lower(), (
        f"the skipped entry should be named and marked withdrawn:\n{result.stdout}"
    )
