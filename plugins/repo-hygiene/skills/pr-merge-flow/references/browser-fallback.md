# Browser fallback — thread state and resolution when GraphQL is exhausted

The escape hatch for the one failure the tool ladder in `polling.md` cannot
climb out of. It covers the **two GraphQL thread operations** — read
`isResolved`, and resolve a thread — and nothing else.

## Why a browser is the answer

Those two operations have no REST equivalent, and they are exactly what the
Iron Law rests on. When the GraphQL budget is gone the ladder does not help:
`gh` porcelain, `gh api`, and raw `curl` all bill the same exhausted endpoint.
The limit is on the endpoint, not the client.

GitHub's web UI performs both through session-authenticated internal
endpoints, which do **not** draw on the token's `api.github.com` GraphQL
budget. Same effect, different quota pool.

| Need | API path | Browser path |
|---|---|---|
| Which threads are unresolved? | GraphQL `reviewThreads.isResolved` | the thread's own rendered state — **Resolve conversation** vs **Unresolve conversation** |
| Close a thread | GraphQL `resolveReviewThread` | click **Resolve conversation** |
| The thread list + comment `id` | REST `…/pulls/{n}/comments` — **keep using this** | not needed; see below |
| Post a thread reply | REST `…/comments/{id}/replies` — **keep using this** | never |

## Target one thread at a time — never enumerate

The failure mode that makes this dangerous is clicking the *wrong* thread's
button. The fix is not a better enumeration; it is to stop enumerating.

REST already gives the authoritative thread list, each with its integer `id` —
and GitHub renders a permalink `#discussion_r<id>` for every thread. The same
integer on both sides is the bridge. So drive the browser **per thread, by
ID**:

### The ID correlation table — how identifiers match across tools

Three surfaces name the same objects differently, and mixing them up is how a
run resolves the wrong thread. Worked example from a real PR:

| Object | REST (`…/pulls/{n}/comments`) | GraphQL (`reviewThreads`) | Web page |
|---|---|---|---|
| **Top comment, integer** | `id` → `3617915140` | `comments.nodes[].databaseId` → `3617915140` | anchor `#discussion_r3617915140` |
| **Top comment, node** | `node_id` → `PRRC_kwDOTO0m-s7XpQEE` | the comment's GraphQL `id` | — |
| **Thread** | **no thread object at all** — threads are implied by `in_reply_to_id` chains | `reviewThreads.nodes[].id` → `PRRT_kwDOTO0m-s6SZa7N` | the rendered thread block |

Read that table carefully, because two consequences fall out of it:

- **The comment integer is the REST ↔ web bridge.** REST's `id`, GraphQL's
  `databaseId`, and the page's `discussion_r…` suffix are all the same number.
  That is what makes per-thread anchoring possible, and it is the only
  identifier that appears on all three surfaces.
- **The thread node id (`PRRT_…`) is GraphQL-only**, and it is what
  `resolveReviewThread` requires. So when GraphQL is exhausted you cannot even
  *name* the thread to the mutation — which is why waiting is not the only
  answer and the browser path exists. The browser resolves by clicking a
  control it reached through the comment integer, an identifier REST still
  serves.

Prefixes are a useful sanity check: `PRRC_` is a review **c**omment,
`PRRT_` is a review **t**hread. If a `PRRT_` value ever shows up where a
comment id belongs (or a bare integer where a node id belongs), stop — the
correlation is wrong, and a wrong correlation resolves the wrong thread.

> **Field name matters.** The REST review-comments endpoint returns `id` (and
> `node_id`); there is no `databaseId` field on it — that is GraphQL's name for
> the same integer. `id` is what the reply path
> (`…/comments/{comment_id}/replies`) and the `#discussion_r…` anchor both
> take.

- `navigate` to `…/pull/$N#discussion_r<id>` — GitHub scrolls to and
  renders that specific thread;
- `read_page` then contains that thread's controls **and** its permalink,
  which confirms which thread you are looking at before you touch anything.

This sidesteps every enumeration hazard at once: no ambiguous list, no
`find` 20-match cap, no document-order assumption, and no dependence on what
happens to be scrolled into view.

**Why the naive approach fails, so it is not retried:** `read_page` reflects
what is *rendered*, and GitHub renders threads lazily. Reading the tree with
the page at the top returns page chrome and no thread controls — at any
`depth`, because depth is the wrong axis; scroll position is the right one.
`find` will surface buttons but labels them all `"Resolve conversation"`, so a
ref cannot be mapped to a thread from the result alone. Both observations are
about *enumeration*, and both dissolve under per-thread anchoring.

## Availability — pick the harness's entry point first

This fallback needs browser-automation tooling, which ships with the harness,
**not** with this plugin or this repo. `pr-merge-flow` is cross-tool and every
other step works everywhere; only this escape hatch is harness-dependent.

| Harness | Entry point |
|---|---|
| **Claude Code** | the `claude-in-chrome` skill — invoke it before any `mcp__claude-in-chrome__*` call |
| **Codex** | the **`chrome@openai-bundled`** plugin, driven through the `node_repl` MCP server (`BROWSER_USE_AVAILABLE_BACKENDS` includes `chrome`) |
| neither present | `stop` → ready-report |

Confirm the entry point is installed and enabled before routing to `browser`
(Codex: `codex plugin list`, `codex mcp list`). Missing tooling is a `stop`, not
a failed attempt.

### Why the Chrome plugin on Codex, and not the other two

- **`browser@openai-bundled`** drives the *in-app* browser, which carries no
  logged-in GitHub session — and session-authenticated endpoints are the whole
  premise.
- **`computer-use@openai-bundled`** drives desktop apps generically. Prefer the
  Chrome plugin, as OpenAI's own bundled guidance also says.

## The tools, and what each is for

| Tool | Produces | Role here |
|---|---|---|
| `get_page_text` | plain text, **no refs** | read thread state and the unresolved counter |
| `read_page` (`filter: "interactive"`) | **element refs** + permalinks | the ref producer; confirms thread identity |
| `find` | **element refs** (≤20) | locate one control in an already-anchored thread |
| `computer` | clicks, `scroll_to`, screenshot, zoom | the only actuator — clicks by `ref` or `coordinate` |

`computer` is the only thing that clicks, and it needs a `ref` from `read_page`
or `find` (preferred — stable across reflow) or a `coordinate` from a
screenshot (last resort). **Granting `computer` without a ref producer leaves
coordinate-clicking as the only path** — an incoherent configuration. Keep them
together.

## When this fires

All three conditions, checked at the step 1 preflight and again on any
mid-run GraphQL failure (availability above is a precondition to all three):

1. **GraphQL is exhausted** — `resources.graphql.remaining` at/near 0, or a
   GraphQL call returned 403 with `RATE_LIMITED` or a secondary-rate-limit
   body.
2. **Waiting is not cheaper** — see the reset guard below.
3. **Core is healthy** — `resources.core.remaining` comfortably above ~100, so
   the REST inventory and replies still work.

The `rate_limit` endpoint is free — GitHub does not count it against any
budget — so this check costs nothing and never needs rationing:

```bash
gh api rate_limit --jq '{
  graphql_remaining: .resources.graphql.remaining,
  graphql_reset:     .resources.graphql.reset,
  core_remaining:    .resources.core.remaining,
  now:               now
}'
```

**A healthy reading is not a promise.** Secondary rate limits do not appear in
`rate_limit` at all: a call can fail with `RATE_LIMITED` while this endpoint
reports thousands of points remaining (observed 2026-07-20). Treat the numbers
as a floor check, never as proof the next call succeeds — and set `SECONDARY=1`
from the failing call's body, not from this payload.

## The reset guard — wait, or open a browser?

GraphQL quota resets hourly, so a 403 is not by itself a reason to drive a
browser: if the reset is minutes away, a bounded wait is cheaper and keeps the
run on the API path. Secondary rate limits are the exception — they publish no
reset time, so there is no clock to wait on.

```bash
# Decide the fallback route from a `gh api rate_limit` payload.
# Reads: GRAPHQL_REMAINING, GRAPHQL_RESET (epoch), CORE_REMAINING, SECONDARY (0|1)
# Echoes exactly one of: proceed | wait <seconds> | browser | stop <reason>
decide_fallback_route() {
  local wait_max=600     # reset within 10 min → wait; beyond → browser
  local core_floor=100   # below this, the REST inventory and replies are at risk

  # Core first: resolving threads you cannot reply to is a silent resolve from
  # the other direction. Better to stop honestly than half-satisfy the Iron Law.
  if [ "${CORE_REMAINING:-0}" -lt "$core_floor" ]; then
    echo "stop core at ${CORE_REMAINING:-0} — REST inventory and replies would fail"; return
  fi
  # Secondary limits publish no reset, so there is no clock to wait on.
  [ "${SECONDARY:-0}" -eq 1 ] && { echo "browser"; return; }
  [ "${GRAPHQL_REMAINING:-0}" -gt 0 ] && { echo "proceed"; return; }

  local until_reset=$(( ${GRAPHQL_RESET:-0} - $(date +%s) ))
  if   [ "$until_reset" -le 0 ];         then echo "proceed"
  elif [ "$until_reset" -le "$wait_max" ]; then echo "wait $(( until_reset + 5 ))"
  else                                        echo "browser"
  fi
}
```

The three numbers are policy, not physics — tune them in place:

| Knob | Default | Trade-off |
|---|---|---|
| `wait_max` | 600s | Too low opens Chrome for a wait that would have been shorter than the browser pass; too high parks the run for most of an hour. |
| `core_floor` | 100 | The REST budget: the inventory, the IDs, and the replies all ride it. |
| reset buffer | +5s | Guards against clock skew re-tripping the limit. The caller still enforces `polling.md`'s 20s floor. |

Route contract:

| Route | Meaning | Caller does |
|---|---|---|
| `proceed` | GraphQL is fine | normal API path, no fallback |
| `wait <seconds>` | reset is near | bounded wait per `polling.md` (20s+ floor), then re-check once and re-decide |
| `browser` | reset is far, or a secondary limit with no clock | gate with the user, then run the procedure below |
| `stop <reason>` | core is dead too, auth is broken, or the harness has no browser tooling | report honestly; downgrade to a ready-report |

## Gate — always, in every mode

Ask before the browser opens. **`--auto` asks too.** `--auto`'s "never ask" is
a rule about review judgment, not a licence to drive the user's logged-in
Chrome while they may be using it.

State in the ask: that a new tab will open on the PR, and that declining means
a ready-report. Include the thread count **when it is known** — at preflight it
is not, because the inventory has not been collected; say so plainly ("count
not yet known") rather than inventing a number.

## Procedure

Tool names below are Claude Code's. On Codex, map each **role** onto the Chrome
plugin's equivalent — the roles and their order are what matter: open a fresh
tab, confirm identity, anchor to one thread, click its control, verify that
thread. A role with no equivalent is a `stop`, not something to approximate.

1. **Build the inventory over REST, fully paginated** —
   `gh api --paginate "…/pulls/{n}/comments?per_page=100"` gives every comment
   with its integer `id`, `path`, `line`, `author`, and `in_reply_to_id`.
   Top-level entries (`in_reply_to_id == null`) are the threads. **One page is
   not the inventory**: past 100 review comments GitHub paginates, and a thread
   that never enters the ledger is a thread merged over without reply or
   resolution. Follow `Link` to the last page before declaring the set
   complete. This list is authoritative; the page is not.
2. **Enter through the harness's entry point** from the availability table. If
   neither is present, availability has already routed this to `stop`.
3. `tabs_context_mcp` — also the connectivity probe. An error means the tooling
   is not connected: degrade, do not retry.
4. `tabs_create_mcp` — always a **new** tab. Never reuse a tab the user has
   open.
5. **Confirm PR identity once** — `navigate` to the PR, then require an exact
   match on owner, repository, and PR number from the page's **own** canonical
   URL and title, not from the URL you requested. A redirect, login wall, SSO
   prompt, or stale tab lands you elsewhere, and a similar-looking page is
   worse than an obvious error. Mismatch → `stop` before anything is read or
   clicked.

Then, **for each thread, one at a time**:

6. **Reply over REST first** (skip if already replied — see idempotency in
   `triage.md`). The reply is the audit trail; a browser leg that then fails
   leaves a replied-but-open thread, which is honest and recoverable, rather
   than a resolved-but-unexplained one.
7. **Anchor to that thread** — `navigate` to
   `…/pull/$N#discussion_r<id>`. This renders it; without anchoring or
   scrolling, its controls are not in the tree at all.
8. **`read_page`** (`filter: "interactive"`) and confirm the thread's permalink
   `#discussion_r<id>` is present and matches the thread you intend.
   Not present → `scroll_to` a `find` ref and re-read; still absent after that
   → treat as a failed interaction and move on. **Never click a Resolve button
   you have not tied to a specific comment `id`.**
9. **Click that thread's Resolve control by `ref`** with `computer`
   `left_click`. Prefer `ref` over `coordinate`: it names the element and
   cannot drift when the page reflows. Coordinates from a screenshot are a last
   resort, and only after step 8 has established identity.
10. **Verify that thread**, not a count. Re-read and confirm *this* thread now
    shows **Unresolve conversation** / "marked this conversation as resolved".
    **Counting remaining Resolve buttons is not a verification signal**: the
    page renders lazily and reviewers post while you work, so the total can
    rise mid-run for reasons unrelated to your click (observed 2026-07-20:
    2 → 5 while a new review landed). Refs also go stale after a re-render —
    on a missing-element error, re-anchor and re-read rather than retrying the
    old ref.

Bots comment while you work. Re-read the REST inventory at the end of the pass;
new threads are step 5's re-review cycle, not a failure.

## Screenshots — diagnostic, ephemeral by default

`computer`'s `screenshot` and `zoom` are available when the text path cannot
explain what is happening — a login wall, SSO or 2FA prompt, abuse
interstitial, permissions banner, or a click that reported success while step
10 says otherwise. One image beats three blind retries.

**Do not persist them.** An authenticated PR screenshot can carry private code,
usernames, and unreleased review context. Keep diagnostics in-session and
report sanitized metadata in words; use `save_to_disk: true` **only after
asking the user and getting a yes**.

A screenshot informs the decision to continue or degrade. It may supply
coordinates only as step 9's last resort, and only for a thread whose identity
step 8 already established — never as a way to skip that step.

## Degrade path

Stop after **2–3 failed interactions** — page not loading, identity mismatch,
a thread whose permalink will not render, tooling unresponsive.

On stopping, report the split explicitly: which threads were resolved, which
were replied-to but left open, which were untouched. Then downgrade to a
ready-report. A partial pass is fine if stated accurately.

**Negative results need the same rigor as positive ones.** "I could not find
the control" is not "the control does not exist" — vary the axis that actually
matters (scroll position, anchoring, a second tool) before concluding anything
is impossible, and never let a house rule from this file stand as evidence that
a capability is absent. Report a blocked attempt as blocked, not as proof.

## What the browser never does

- **Never merges.** The merge decision stays on the API path behind the mode
  gate — a browser click is not a mode gate.
- **Never closes a PR**, never edits the title, never pushes.
- **Never replies.** Replies ride REST, which carries the comment `id` and the
  audit trail.
- **Never resolves a thread it has not identified** by comment `id` at step 8.
- **Never uses `javascript_tool`.** Clicking a button does not need arbitrary
  page script; the grant is deliberately absent, as are `file_upload`,
  `gif_creator`, and `read_network_requests`.
- **Never triggers a dialog.** A dialog blocks every subsequent command and
  ends the session.
- **Never polls.** Waits stay on the API path under `polling.md`'s bounds.
