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

## The escape hatch — not a rung

The ladder cannot climb out of an exhausted **GraphQL** budget: all three rungs
bill the same endpoint. Those two thread operations have no REST equivalent, so
GraphQL exhaustion stalls the Iron Law itself.

The browser fallback in `references/browser-fallback.md` recovers both by
driving the GitHub web UI, whose session-authenticated internal endpoints do not
draw on the token's GraphQL budget. It is an **escape hatch, not a fourth
rung** — never reached for a call REST can still make, and never used to poll.
It works one thread at a time, anchored to that thread's own
`#discussion_r<id>` from the REST inventory, so it never has to
enumerate controls or guess which button belongs to which thread.

Before reaching for it, check the reset clock: GraphQL quota resets hourly, so
a near reset makes a bounded wait cheaper and safer than opening a browser.
`browser-fallback.md`'s `decide_fallback_route` owns that call and returns one
of `proceed` / `wait <seconds>` / `browser` / `stop <reason>`.

## Cheap change detection

Poll the cheapest signal, not the full state:

```bash
gh api "repos/$OWNER/$REPO/pulls/$N" --jq '{merged, state, updated_at, head: .head.sha}'
gh api "repos/$OWNER/$REPO/pulls/$N/reviews?per_page=100" --jq 'length'
```

Review count or `updated_at` moved → run the full thread collection once.
Quote any URL containing `?` or `&` (zsh globs otherwise).

## Pending merge monitoring

Use this for every authorized merge that returns before GitHub reports the PR
merged, including `confirm` after **Merge now**. Preserve the interval floor,
fixed deadline, and final recheck above; a state change never resets the wait.

- Poll the PR's REST `merged`, `state`, `head.sha`, and `updated_at` fields
  with the cheap review signal above. A change to `head.sha`, `updated_at`,
  or review count exits the poll loop for one full collection with
  authoritative thread state. `merged: true` enters final verification
  immediately; a closed, unmerged PR is reported as such and ends the wait.
  GraphQL is not polled. An unchanged head and ledger may resume the remaining
  wait; a cosmetic timestamp change does not restart triage.
- If the head changed or a thread is new or reopened while the request is
  pending, cancel the pending merge or queue entry through a supported GitHub
  action and verify removal before returning through steps 2–3. Preserve
  existing review-cycle bounds. GitHub's
  [queue removal instructions](https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/merging-a-pull-request-with-a-merge-queue#removing-a-pull-request-from-a-merge-queue)
  document the PR page's **Remove from queue** action. The separate
  [browser consent gate](browser-fallback.md) still applies.
  Queue cancellation is a separate PR-level browser action, even with healthy
  quotas: reuse that consent gate and verify the exact PR's identity, not the
  fallback's exhaustion trigger or thread-resolution procedure. State the
  cancellation action in the consent request and verify removal on the PR page.
  `gh pr merge --disable-auto` disables auto-merge; it is not proof of queue
  removal. If cancellation is unavailable, report the still-pending request
  and blocker promptly, then stop without claiming completion.
- At the merged signal or deadline, recheck the PR and authoritative thread
  state once and reconcile the ledger before reporting the result. If the
  deadline recheck finds a changed head or new/reopened thread while the request
  is still pending, use the cancellation-and-removal path above before reporting
  and stopping. Report any unavailable cancellation explicitly; do not re-arm the
  wait or start another triage pass after expiry. Only an unchanged pending
  request may be left in place without attempting cancellation. If GitHub
  merged before a late thread or head change could be handled, report the
  actual merge and unresolved work explicitly; do not claim a clean completion
  or start cleanup. A completed merge cannot be canceled or returned to the
  pre-merge loop. Report the final pending, canceled, or blocked state and stop
  when still unmerged at the deadline.

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
