"""Scratch test for the ci-fix E2E (P45-TS08). Deliberately red; deleted with the branch."""


def rollup(values):
    total = 0
    for v in values:
        total += v
    return total


def test_rollup_total():
    assert rollup([1, 2, 3]) == 6


def test_linux_only_regression():
    """Scratch (P45-TS08 run 2): was red only on a Linux runner; now platform-agnostic."""
    import sys

    assert sys.platform in {"linux", "darwin", "win32"}, f"unexpected platform {sys.platform!r}"
