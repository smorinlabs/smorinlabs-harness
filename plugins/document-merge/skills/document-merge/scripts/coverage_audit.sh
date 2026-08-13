#!/usr/bin/env bash
# Phase 7: dump every source heading so the model can diff against the topic-to-source map.
# Usage: coverage_audit.sh <consolidated-dir> <source-file> [<source-file> ...]
# Prints the heading list to stdout and a brief reminder of what to do with it.

set -euo pipefail

if [ "$#" -lt 2 ]; then
  echo "Usage: $0 <consolidated-dir> <source-file> [<source-file> ...]" >&2
  exit 2
fi

CONSOLIDATED_DIR="$1"
shift

if [ ! -d "$CONSOLIDATED_DIR" ]; then
  echo "Consolidated directory does not exist: $CONSOLIDATED_DIR" >&2
  exit 1
fi

OUT="/tmp/source-headings-audit.txt"
: > "$OUT"

for f in "$@"; do
  if [ ! -f "$f" ]; then
    echo "Skipping missing file: $f" >&2
    continue
  fi
  echo "=== $f ===" >> "$OUT"
  grep -nE "^#{1,3} " "$f" >> "$OUT" || true
done

heading_count=$(grep -cE "^[0-9]+:#" "$OUT" || true)
echo "Wrote $heading_count headings from $# source file(s) to $OUT"
echo ""
echo "Next: for each heading, verify it appears either"
echo "  (a) referenced (by line range) in the topic-to-source map in $CONSOLIDATED_DIR/decisions-and-conflicts.md, or"
echo "  (b) listed under 'Intentionally omitted source sections' with a reason."
echo "Add any missing entries to 'Intentionally omitted source sections' before declaring the merge complete."
