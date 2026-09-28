#!/usr/bin/env bash
# Fails if a pre-rename repo name appears in a live (non-historical) tracked file.
# Both repos cross-reference each other, so the guard bans BOTH old names.
set -euo pipefail
old='smorin[-_]harness|smorinlabs[-_]harness'
status=0
git grep -niE "$old" -- \
  ':!docs/handoffs' ':!docs/superpowers' ':!docs/reviews' ':!docs/validation' ':!docs/plans' \
  ':!tests/fixtures' ':!research' ':!PROJECTS.md' ':!RELEASE-NOTES.md' \
  ':!scripts/check-no-old-name.sh' || status=$?
case "$status" in
  0) echo "::error::old repo name found in a live file (see above)"; exit 1 ;;
  1) echo "No live references to the old repo names." ;;
  *) echo "::error::old-name scan failed (exit $status)"; exit "$status" ;;
esac
# Over-match guard: fleet-concept names must survive the sweep.
for keep in 'harness-kit' 'skill-harness-release' 'factor-harness'; do
  git grep -qE "$keep" || { echo "::error::'$keep' vanished — the sweep over-matched"; exit 1; }
done
