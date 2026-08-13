#!/usr/bin/env bash
# Phase 4 enforcement: every CFL marker has a matching log entry, and vice versa.
# Usage: validate_round_trip.sh <decisions-log> <merged-doc> [<merged-doc> ...]

set -euo pipefail

if [ "$#" -lt 2 ]; then
  echo "Usage: $0 <decisions-log> <merged-doc> [<merged-doc> ...]" >&2
  exit 2
fi

DECISIONS_LOG="$1"
shift

if [ ! -f "$DECISIONS_LOG" ]; then
  echo "FAIL: decisions log not found at $DECISIONS_LOG" >&2
  exit 1
fi

# Every merged doc must exist. A skipped path would make the gate pass against
# files it never read, so this is checked here rather than inside the command
# substitution below, where `exit` would only leave the subshell.
for doc in "$@"; do
  if [ ! -f "$doc" ]; then
    echo "FAIL: merged doc not found at $doc" >&2
    exit 1
  fi
done

# Inline markers: <!-- CONFLICT: CFL-### -->
markers=$(for doc in "$@"; do
  grep -oE "CONFLICT: CFL-[0-9]+" "$doc" | grep -oE "CFL-[0-9]+" || true
done | sort -u)

# Log entries: ### [ ] CFL-### or ### [x] CFL-###
entries=$(grep -E "^### \[[x ]\] CFL-[0-9]+" "$DECISIONS_LOG" | grep -oE "CFL-[0-9]+" | sort -u || true)

markers_only=$(comm -23 <(echo "$markers") <(echo "$entries") || true)
entries_only=$(comm -13 <(echo "$markers") <(echo "$entries") || true)

failed=0
if [ -n "$markers_only" ]; then
  echo "FAIL: markers without matching log entries:"
  echo "$markers_only" | sed 's/^/  - /'
  failed=1
fi
if [ -n "$entries_only" ]; then
  echo "FAIL: log entries without matching inline markers:"
  echo "$entries_only" | sed 's/^/  - /'
  failed=1
fi

marker_count=$(echo -n "$markers" | grep -c "CFL-" || true)
entry_count=$(echo -n "$entries" | grep -c "CFL-" || true)

if [ "$failed" = "0" ]; then
  echo "PASS: $marker_count markers and $entry_count entries (all matched)"
fi

exit $failed
