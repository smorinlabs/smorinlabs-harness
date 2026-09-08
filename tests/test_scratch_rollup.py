"""Deliberately failing test for the ci-fix fix-mode E2E (P45-TS03). Scratch branch only."""


def test_rollup_total():
    assert sum([1, 2]) == 3
