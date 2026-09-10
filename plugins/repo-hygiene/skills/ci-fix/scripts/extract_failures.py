#!/usr/bin/env python3
"""extract_failures.py — failing test IDs from a GitHub Actions job log.

Reads one or more job logs (files, or stdin when none are given), strips the
per-line timestamps GitHub prefixes and any ANSI color, and emits the failing
test identifiers in the form each runner accepts back as a filter:

  pytest  tests/test_x.py::TestCls::test_name[param]   (FAILED/ERROR summary lines)
  jest    Suite › test name                             (● failure blocks)
  vitest  src/x.test.ts > suite > test name             (FAIL summary lines; a suite
                                                         that failed to load yields
                                                         its file alone)
  cargo   module::tests::test_name                      (---- X stdout ---- headers)
  nextest tests::module::test_name                      (FAIL [ time ] <binary-id> <test>
                                                         lines; binary ids → packages)
  go      TestName/subtest                              (leaf --- FAIL lines; parents
                                                         whose only failures are
                                                         subtests are dropped)

`--format auto` (default) picks the runner with the most matches. Output is
one ID per line, or with `--json` an object {format, failures,
failures_quoted, packages, failure_pairs}. `failures_quoted` is each ID passed through
`shlex.quote`: a contributor controls test names and parameter IDs, and
`$(...)` inside double quotes executes, so local commands take the quoted
form verbatim and never re-interpolate the bare one. `packages` is populated
for go from `FAIL <pkg>` lines and for nextest from the binary ids;
`failure_pairs` keeps nextest's (binary_id, test) pairs, which a filter must
not recombine.

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

# pytest node IDs may contain whitespace, ` - `, or even ` FAILED` inside
# `[param ids]`, so the delimiter that ends an ID (` - reason` on summary
# lines, ` FAILED`/` ERROR` on verbose lines) counts only at bracket depth 0.
PYTEST_SUMMARY_PREFIX_RE = re.compile(r"^(?:FAILED|ERROR)\s+(\S+::.*)$")


def _cut_at_depth0(text: str, delimiters: tuple[str, ...]) -> str | None:
    """`text` up to the first delimiter that sits outside any [...] pair."""
    depth = 0
    for i, ch in enumerate(text):
        if ch == "[":
            depth += 1
        elif ch == "]":
            depth = max(0, depth - 1)
        elif depth == 0 and any(text.startswith(d, i) for d in delimiters):
            return text[:i]
    return None


def _cut_after_first_bracket(text: str, delimiters: tuple[str, ...]) -> str | None:
    """Fallback for a param ID with an unmatched `[` (depth never returns to
    0): cut at the first `]` that is directly followed by one of the
    delimiters. First, not last: a failure reason often contains `] - `
    (`assert x[0] - y == 1`), while a param ID that contains the delimiter
    *and* an unmatched bracket is vanishingly rare."""
    best = -1
    for d in delimiters:
        idx = text.find("]" + d)
        if idx >= 0 and (best < 0 or idx < best):
            best = idx
    return text[: best + 1] if best >= 0 else None


def _pytest_id(line: str) -> str | None:
    """A node ID has no whitespace outside its [param] brackets, so it ends at
    the first depth-0 whitespace. Summary lines carry a FAILED/ERROR prefix;
    verbose lines must have the verdict as the very next token, so a SKIPPED
    or PASSED line whose free text mentions ERROR is not a failure. When the
    brackets never close (an unmatched `[` inside a param ID) the depth-aware
    cut finds nothing and the first `] - ` (summary) or `] FAILED` / `] ERROR`
    (verbose) split is used instead."""
    m = PYTEST_SUMMARY_PREFIX_RE.match(line)
    if m:
        rest = m.group(1)
        cut = _cut_at_depth0(rest, (" ",))
        if cut is None:
            cut = _cut_after_first_bracket(rest, (" - ",))
        return (cut if cut is not None else rest).rstrip()
    if "::" in line:
        cut = _cut_at_depth0(line, (" ",))
        if cut is None:
            cut = _cut_after_first_bracket(line, (" FAILED", " ERROR"))
        if cut and "::" in cut and not cut.startswith(("FAILED", "ERROR")):
            verdict = line[len(cut) :].split(None, 1)
            if verdict and verdict[0] in ("FAILED", "ERROR"):
                return cut.rstrip()
    return None


JEST_BLOCK_RE = re.compile(r"^●\s+(.+?)\s*$")
JEST_MARK_RE = re.compile(r"^✕\s+(.+?)(?:\s+\(\d+\s*m?s\))?\s*$")
VITEST_FAIL_RE = re.compile(r"^FAIL\s+(\S+(?:\s+>\s+.+?)?)\s*$")
VITEST_SUITE_RE = re.compile(r"^FAIL\s+(\S+)\s+\[\s*\S+\s*\]\s*$")
VITEST_MARK_RE = re.compile(r"^×\s+(.+?)(?:\s+\d+\s*m?s)?\s*$")
VITEST_FILE_RE = re.compile(r"^❯\s+(\S+)\s+\(\d+\s+tests?")
CARGO_HEADER_RE = re.compile(r"^----\s+(\S+)\s+stdout\s+----$")
NEXTEST_FAIL_RE = re.compile(r"^FAIL\s+\[\s*[\d.]+s\s*\]\s+(\S+)\s+(\S+)\s*$")
GO_FAIL_RE = re.compile(r"^---\s+FAIL:\s+(\S+)")
GO_PACKAGE_RE = re.compile(r"^FAIL\s+(\S+)\s+[\d.]+s$")

FORMATS = ("auto", "pytest", "jest", "vitest", "cargo", "nextest", "go")


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
        node_id = _pytest_id(line)
        if node_id:
            ids.append(node_id)
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


def detect_vitest(lines: list[str]) -> list[str]:
    """`FAIL  <file> > <suite> > <name>` summary lines, or `FAIL  <file> [ <file> ]`
    for a suite that failed to load (the file alone is the target). Without a
    summary, the `×` marks under the file's `❯` line name the failing tests."""
    ids = []
    for line in lines:
        if m := VITEST_SUITE_RE.match(line):
            ids.append(m.group(1))
        elif (m := VITEST_FAIL_RE.match(line)) and " > " in m.group(1):
            ids.append(m.group(1).strip())
    if ids:
        return dedup(ids)
    # Fallback: the `×` marks carry only `<suite> > <name>`, but the targeted
    # command needs the file too, so each mark takes the file from the `❯
    # <file> (N tests…)` header above it. A mark with no header yet is kept
    # bare rather than dropped.
    current_file = None
    for line in lines:
        if m := VITEST_FILE_RE.match(line):
            current_file = m.group(1)
        elif m := VITEST_MARK_RE.match(line):
            name = m.group(1)
            ids.append(f"{current_file} > {name}" if current_file else name)
    return dedup(ids)


def detect_nextest(lines: list[str]) -> tuple[list[str], list[str], list[dict]]:
    """`FAIL [   0.012s] <binary-id> <test>` lines (printed during the run and
    again under the summary; deduplicated). Binary ids become `packages`, and
    the (binary, test) pairs are kept in `failure_pairs`: the same test name
    can exist in several binaries, so pairing a binary with a test that did
    not fail in it would build a filter that runs the wrong test, or none."""
    seen: list[tuple[str, str]] = []
    for line in lines:
        if m := NEXTEST_FAIL_RE.match(line):
            pair = (m.group(1), m.group(2))
            if pair not in seen:
                seen.append(pair)
    return (
        dedup([t for _, t in seen]),
        dedup([b for b, _ in seen]),
        [{"binary_id": b, "test": t} for b, t in seen],
    )


def detect_cargo(lines: list[str]) -> list[str]:
    """`---- X stdout ----` headers count only after a `failures:` marker:
    `cargo test -- --show-output` prints the same headers under `successes:`."""
    ids = []
    in_failures = False
    for line in lines:
        if line == "failures:":
            in_failures = True
            continue
        if line == "successes:":
            in_failures = False
            continue
        if in_failures and (m := CARGO_HEADER_RE.match(line)):
            ids.append(m.group(1))
    return dedup(ids)


def detect_go(lines: list[str]) -> tuple[list[str], list[str]]:
    fails = dedup([m.group(1) for line in lines if (m := GO_FAIL_RE.match(line))])
    # drop a parent when one of its own subtests failed — the leaf is the target
    leaves = [
        f for f in fails if not any(o != f and o.startswith(f + "/") for o in fails)
    ]
    packages = dedup([m.group(1) for line in lines if (m := GO_PACKAGE_RE.match(line))])
    return leaves, packages


def extract(lines: list[str], fmt: str) -> dict:
    go_failures, go_packages = detect_go(lines)
    nextest_failures, nextest_packages, nextest_pairs = detect_nextest(lines)
    results = {
        "pytest": (detect_pytest(lines), [], []),
        "jest": (detect_jest(lines), [], []),
        "vitest": (detect_vitest(lines), [], []),
        "cargo": (detect_cargo(lines), [], []),
        "nextest": (nextest_failures, nextest_packages, nextest_pairs),
        "go": (go_failures, go_packages, []),
    }
    if fmt != "auto":
        failures, packages, pairs = results[fmt]
        return _result(fmt if failures else None, failures, packages, pairs)
    best = max(results, key=lambda k: len(results[k][0]))  # ties keep dict order
    failures, packages, pairs = results[best]
    if not failures:
        return _result(None, [], [])
    return _result(best, failures, packages, pairs)


def _result(fmt, failures, packages, pairs=()) -> dict:
    return {
        "format": fmt,
        "failures": failures,
        "failures_quoted": [shlex.quote(f) for f in failures],
        "packages": packages,
        "failure_pairs": list(pairs),
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
    parser.add_argument(
        "--format",
        default="auto",
        help="auto|pytest|jest|vitest|cargo|nextest|go (default auto)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit {format, failures, failures_quoted, packages}",
    )
    parser.add_argument(
        "logs", nargs="*", metavar="LOG", help="job log file(s); stdin when omitted"
    )
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
        print(
            "no failures recognized (pytest/jest/vitest/cargo/nextest/go); fall back to the step command",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
