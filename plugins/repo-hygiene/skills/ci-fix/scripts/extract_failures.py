#!/usr/bin/env python3
"""extract_failures.py — failing test IDs from a GitHub Actions job log.

Reads one or more job logs (files, or stdin when none are given), strips the
per-line timestamps GitHub prefixes and any ANSI color, and emits the failing
test identifiers in the form each runner accepts back as a filter:

  pytest  tests/test_x.py::TestCls::test_name[param]   (FAILED/ERROR summary lines)
  jest    Suite › test name                             (● failure blocks)
  cargo   module::tests::test_name                      (---- X stdout ---- headers)
  go      TestName/subtest                              (leaf --- FAIL lines; parents
                                                         whose only failures are
                                                         subtests are dropped)

`--format auto` (default) picks the runner with the most matches. Output is
one ID per line, or with `--json` an object {format, failures,
failures_quoted, packages}. `failures_quoted` is each ID passed through
`shlex.quote`: a contributor controls test names and parameter IDs, and
`$(...)` inside double quotes executes, so local commands take the quoted
form verbatim and never re-interpolate the bare one. `packages` is populated
for go from `FAIL <pkg>` lines.

Exit 0 when at least one failure was recognized, 1 when none, 2 on usage error.
"""

from __future__ import annotations

import argparse
import json
import re
import shlex
import sys

TIMESTAMP_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z\s?")
ANSI_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")

# IDs may contain whitespace inside `[param ids]`; they end at the ` - reason`
# delimiter (summary lines) or before ` FAILED`/` ERROR` (verbose lines).
PYTEST_SUMMARY_RE = re.compile(r"^(?:FAILED|ERROR)\s+(\S+::.+?)(?:\s+-\s.*)?$")
PYTEST_VERBOSE_RE = re.compile(r"^(\S+::.+?)\s+(?:FAILED|ERROR)\b")
JEST_BLOCK_RE = re.compile(r"^●\s+(.+?)\s*$")
JEST_MARK_RE = re.compile(r"^✕\s+(.+?)(?:\s+\(\d+\s*m?s\))?\s*$")
CARGO_HEADER_RE = re.compile(r"^----\s+(\S+)\s+stdout\s+----$")
GO_FAIL_RE = re.compile(r"^---\s+FAIL:\s+(\S+)")
GO_PACKAGE_RE = re.compile(r"^FAIL\s+(\S+)\s+[\d.]+s$")

FORMATS = ("auto", "pytest", "jest", "cargo", "go")


def clean(line: str) -> str:
    return ANSI_RE.sub("", TIMESTAMP_RE.sub("", line.rstrip("\n"))).strip()


def dedup(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out = []
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def detect_pytest(lines: list[str]) -> list[str]:
    ids = []
    for line in lines:
        m = PYTEST_SUMMARY_RE.match(line) or PYTEST_VERBOSE_RE.match(line)
        if m:
            ids.append(m.group(1))
    return dedup(ids)


def detect_jest(lines: list[str]) -> list[str]:
    blocks = []
    for line in lines:
        m = JEST_BLOCK_RE.match(line)
        if m and not m.group(1).startswith("Test suite failed to run"):
            blocks.append(m.group(1))
    if blocks:
        return dedup(blocks)
    return dedup([m.group(1) for line in lines if (m := JEST_MARK_RE.match(line))])


def detect_cargo(lines: list[str]) -> list[str]:
    return dedup([m.group(1) for line in lines if (m := CARGO_HEADER_RE.match(line))])


def detect_go(lines: list[str]) -> tuple[list[str], list[str]]:
    fails = dedup([m.group(1) for line in lines if (m := GO_FAIL_RE.match(line))])
    # drop a parent when one of its own subtests failed — the leaf is the target
    leaves = [f for f in fails if not any(o != f and o.startswith(f + "/") for o in fails)]
    packages = dedup([m.group(1) for line in lines if (m := GO_PACKAGE_RE.match(line))])
    return leaves, packages


def extract(lines: list[str], fmt: str) -> dict:
    results = {
        "pytest": (detect_pytest(lines), []),
        "jest": (detect_jest(lines), []),
        "cargo": (detect_cargo(lines), []),
        "go": detect_go(lines),
    }
    if fmt != "auto":
        failures, packages = results[fmt]
        return _result(fmt if failures else None, failures, packages)
    best = max(results, key=lambda k: len(results[k][0]))  # ties keep dict order
    failures, packages = results[best]
    if not failures:
        return _result(None, [], [])
    return _result(best, failures, packages)


def _result(fmt, failures, packages) -> dict:
    return {
        "format": fmt,
        "failures": failures,
        "failures_quoted": [shlex.quote(f) for f in failures],
        "packages": packages,
    }


def read_lines(paths: list[str]) -> list[str]:
    if not paths:
        return [clean(l) for l in sys.stdin]
    lines: list[str] = []
    for path in paths:
        try:
            with open(path, encoding="utf-8", errors="replace") as fh:
                lines.extend(clean(l) for l in fh)
        except OSError as exc:
            raise SystemExit(f"error: cannot read {path}: {exc.strerror}") from exc
    return lines


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--format", default="auto", help="auto|pytest|jest|cargo|go (default auto)")
    parser.add_argument("--json", action="store_true", help="emit {format, failures, packages}")
    parser.add_argument("logs", nargs="*", metavar="LOG", help="job log file(s); stdin when omitted")
    args = parser.parse_args(argv)
    if args.format not in FORMATS:
        print(f"error: --format must be one of {', '.join(FORMATS)}", file=sys.stderr)
        return 2
    try:
        lines = read_lines(args.logs)
    except SystemExit as exc:
        print(exc, file=sys.stderr)
        return 2
    data = extract(lines, args.format)
    if args.json:
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print("\n".join(data["failures"]))
    if not data["failures"]:
        print("no failures recognized (pytest/jest/cargo/go); fall back to the step command", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
