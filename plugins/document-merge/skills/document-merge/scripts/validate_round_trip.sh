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
  if [ ! -r "$doc" ]; then
    echo "FAIL: merged doc not readable at $doc" >&2
    exit 1
  fi
done

# Inline markers: <!-- CONFLICT: CFL-### -->
# Collected in a plain loop, not a command substitution: a read error must be
# able to abort the script, and `exit` inside a substitution only leaves the
# subshell. grep exit 1 means "no markers in this doc", which is normal;
# anything above 1 is a real read failure and must never be swallowed into an
# empty marker set.
raw_markers=""
for doc in "$@"; do
  status=0
  found=$(grep -oE "CONFLICT: CFL-[0-9]+" "$doc") || status=$?
  if [ "$status" -gt 1 ]; then
    echo "FAIL: could not read markers from $doc (grep exit $status)" >&2
    exit 1
  fi
  [ -n "$found" ] && raw_markers="$raw_markers$found"$'\n'
done
markers=$(printf '%s' "$raw_markers" | grep -oE "CFL-[0-9]+" | sort -u || true)

# Log entries: ### [ ] CFL-### or ### [x] CFL-###
entries=$(grep -E "^### \[[x ]\] CFL-[0-9]+" "$DECISIONS_LOG" | grep -oE "CFL-[0-9]+" | sort -u || true)

# IDs retired per the ID-hygiene rule carry a `**Status:** Withdrawn` line in
# their body and have no inline marker by design, so they are excluded from the
# comparison. The id is tracked across lines because the status sits under its
# own heading, and the exclusion is reported below rather than applied silently.
withdrawn=$(awk '
  /^### \[[x ]\] CFL-[0-9]+/ {
    match($0, /CFL-[0-9]+/); id = substr($0, RSTART, RLENGTH); next
  }
  id != "" && tolower($0) ~ /^\*\*status:\*\*[[:space:]]*withdrawn/ { print id; id = "" }
' "$DECISIONS_LOG" | sort -u)

if [ -n "$withdrawn" ]; then
  entries=$(comm -23 <(echo "$entries") <(echo "$withdrawn") || true)
fi

markers_only=$(comm -23 <(echo "$markers") <(echo "$entries") || true)
entries_only=$(comm -13 <(echo "$markers") <(echo "$entries") || true)

if [ -n "$withdrawn" ]; then
  echo "Withdrawn entries excluded from the comparison (no inline marker expected):"
  echo "$withdrawn" | sed 's/^/  - /'
fi

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
