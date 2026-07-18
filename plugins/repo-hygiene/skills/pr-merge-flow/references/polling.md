# Quota-safe GitHub polling

Rules and recipes for every wait in pr-merge-flow. The failure mode this file
prevents: an unbounded or tight loop silently burning API quota, or a monitor
that never fires and never dies.

## Preflight — measure, never assume

```bash
gh auth status
gh api rate_limit --jq '{core: .resources.core.remaining, graphql: .resources.graphql.remaining}'
```

Both remaining counts comfortably above ~100 → proceed. Low → widen intervals;
nearly exhausted → stop and tell the user. GraphQL and REST have separate
budgets — the split below keeps the GraphQL side nearly idle.

## The four laws of a poll loop

1. **Interval floor**: ≥20–30s between calls to any GitHub endpoint.
2. **Hard bound**: a fixed total lifetime (bot-wait ~5 min; monitors 5–10
   min). On expiry, do one manual recheck and report — never re-arm silently.
3. **Pre-validate before arming**: run the underlying check command once and
   confirm its output actually matches the loop's trigger and exit conditions
   (every terminal state). An unvalidated loop is how "blocked or in error"
   becomes "polls forever".
4. **Errors are "no data"**: an API error or empty response never counts as a
   state change and never resets the bound.

## Tool ladder

1. `gh` porcelain — `gh pr view`, `gh pr checks`. Convenient, but some
   porcelain is GraphQL-backed and rate-limits sooner; drop a rung when it
   errors or quota is tight.
2. `gh api` REST — `repos/{owner}/{repo}/pulls/{n}`, `…/reviews`,
   `…/comments`, `commits/{sha}/check-runs`. Preferred for anything repeated.
3. Raw REST — `curl -H "Authorization: Bearer $GITHUB_TOKEN"
   https://api.github.com/…` — last resort when gh itself is broken.

GraphQL is reserved for the two thread operations in `references/triage.md`
(resolution-state read, resolve mutation) and is never called inside a poll
loop.

## Cheap change detection

Poll the cheapest signal, not the full state:

```bash
gh api "repos/$OWNER/$REPO/pulls/$N" --jq '{updated_at, head: .head.sha}'
gh api "repos/$OWNER/$REPO/pulls/$N/reviews?per_page=100" --jq 'length'
```

Review count or `updated_at` moved → run the full thread collection once.
Quote any URL containing `?` or `&` (zsh globs otherwise).

## Canonical bounded monitor

Generated per-run (adapt owner/repo/number and bounds); never left running
past its lifetime:

```bash
#!/usr/bin/env bash
# bounded-monitor: watch for new PR reviews, then exit. Never outlives DEADLINE.
set -u
OWNER=octocat REPO=example N=42
INTERVAL=30                        # seconds; never below 20
DEADLINE=$(( $(date +%s) + 300 ))  # 5-min hard lifetime (600 only on explicit request)
baseline=$(gh api "repos/$OWNER/$REPO/pulls/$N/reviews?per_page=100" --jq 'length') || baseline=""
[ -z "$baseline" ] && { echo "prevalidation-failed"; exit 2; }
while [ "$(date +%s)" -lt "$DEADLINE" ]; do
  sleep "$INTERVAL"
  count=$(gh api "repos/$OWNER/$REPO/pulls/$N/reviews?per_page=100" --jq 'length') || continue  # error = no data
  [ "$count" != "$baseline" ] && { echo "changed"; exit 0; }
done
echo "not-triggered"; exit 1
```

Exit contract: `0` changed → collect threads now; `1` timed out → one manual
recheck, then report or ask; `2` pre-validation failed → do not re-arm, drop
down the tool ladder instead.
