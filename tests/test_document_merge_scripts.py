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
