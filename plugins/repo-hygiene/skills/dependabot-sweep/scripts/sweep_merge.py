#!/usr/bin/env python3
"""Approved-head entry point for durable sweep workers.

Run in its own process. Wrapper options precede ``--``; everything after
it keeps gh_merge.py's existing argument shape and exit semantics.
"""

from __future__ import annotations

import argparse
import importlib.util
import re
import sys
from pathlib import Path

DEFAULT_HELPER = Path(__file__).resolve().with_name("gh_merge.py")


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        raise ValueError(message)


def _load_helper(path):
    spec = importlib.util.spec_from_file_location("_sweep_merge_transport", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load merge helper: {path}")
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    return helper


def main(argv):
    parser = _Parser(prog="sweep_merge.py", add_help=False, allow_abbrev=False)
    parser.add_argument("--expected-head", required=True)
    parser.add_argument("--helper-path", default=str(DEFAULT_HELPER))
    parser.add_argument("helper_args", nargs=argparse.REMAINDER)
    try:
        args = parser.parse_args(argv[1:])
        if not re.fullmatch(r"[0-9a-fA-F]{40}", args.expected_head):
            raise ValueError("--expected-head must be the full approved "
                             "40-hex commit SHA")
        if not args.helper_args or args.helper_args[0] != "--":
            raise ValueError("put -- before the unchanged helper arguments")
        helper = _load_helper(args.helper_path)
    except (ImportError, OSError, TypeError, ValueError) as exc:
        print(f"refusing: {exc}")
        return 12
    original_preflight = helper.preflight
    expected_head = args.expected_head.lower()

    def approved_preflight(*positional, **keywords):
        observed = original_preflight(*positional, **keywords)
        if observed[0] != expected_head:
            raise helper.DefinitiveFailure(
                "head changed since classification or approval")
        return observed

    helper.preflight = approved_preflight
    try:
        return helper.main([args.helper_path, *args.helper_args[1:]])
    finally:
        # Production runs in a dedicated process. Restore the module for
        # in-process callers and tests, including unexpected exceptions.
        helper.preflight = original_preflight


if __name__ == "__main__":
    sys.exit(main(sys.argv))
