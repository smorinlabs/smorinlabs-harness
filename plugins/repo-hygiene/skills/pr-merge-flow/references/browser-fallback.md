# Browser fallback — resolving threads when GraphQL is exhausted

The escape hatch for the one failure the tool ladder in `polling.md` cannot
climb out of. Narrow by design: it covers the **two GraphQL operations only**
(read thread resolution state, resolve a thread) and nothing else.

## Why a browser is the answer

Those two operations have no REST equivalent, and they are exactly what the
Iron Law rests on. When the GraphQL budget is gone, the ladder does not help —
`gh` porcelain, `gh api`, and raw `curl` all bill the same exhausted endpoint
budget. The limit is on the endpoint, not the client.

github.com's web UI performs both operations through session-authenticated
internal endpoints, which do **not** draw on the token's `api.github.com`
GraphQL budget. The browser is not a slower version of the same call — it is
the same effect billed to a different quota pool.

| Need | API path | Browser path |
|---|---|---|
| Which threads are unresolved? | GraphQL `reviewThreads.isResolved` | PR **Conversation** page — the *N unresolved conversations* counter, and each thread's **Resolve conversation** button |
| Close a thread | GraphQL `resolveReviewThread` | Click **Resolve conversation** |
| Post a thread reply | REST `…/comments/{id}/replies` — **keep using this** | not used |

The browser tools split three ways, and the split is load-bearing:

| Tool | Job | Why not the others |
|---|---|---|
| `get_page_text` | read thread state + the unresolved counter | plain text, no element refs — cannot produce a click target |
| `read_page` (`filter: "interactive"`) | enumerate every Resolve button with a stable `ref` | the only deterministic enumeration; `find` caps at 20 matches with no pagination |
| `find` | shortcut to one named element | convenience only — never used to enumerate threads |
| `computer` `left_click` by `ref` | the click itself | `ref` beats `coordinate`: no screenshot, no pixel arithmetic, no drift on reflow |

Note the third row: replies ride the **core** budget, which is separate and far
larger (5000/hr) and which this flow barely touches. In the ordinary failure
only the two GraphQL operations need rescuing.

## When this fires

All three conditions, checked at the step 1 preflight and again on any
mid-run GraphQL failure:

1. **GraphQL is exhausted** — `resources.graphql.remaining` at/near 0, or a
   GraphQL call returned 403 with `RATE_LIMITED` or a secondary-rate-limit
   body.
2. **Waiting is not cheaper** — see the reset guard below.
3. **Core is healthy** — `resources.core.remaining` comfortably above ~100, so
   replies still post normally over REST.

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

## The reset guard — wait, or open a browser?

GraphQL quota resets hourly, so a 403 is not by itself a reason to drive a
browser: if the reset is minutes away, a bounded wait is cheaper, safer, and
keeps the whole run on the API path. Secondary rate limits are the exception —
they publish no reset time, so there is no clock to wait on.

```bash
# Decide the fallback route from a `gh api rate_limit` payload.
# Reads: GRAPHQL_REMAINING, GRAPHQL_RESET (epoch), CORE_REMAINING, SECONDARY (0|1)
# Echoes exactly one of: proceed | wait <seconds> | browser | stop <reason>
decide_fallback_route() {
  local wait_max=600     # reset within 10 min → wait; beyond → browser
  local core_floor=100   # below this, replies are at risk

  # Core first: resolving threads you cannot reply to is a silent resolve from
  # the other direction. Better to stop honestly than half-satisfy the Iron Law.
  if [ "${CORE_REMAINING:-0}" -lt "$core_floor" ]; then
    echo "stop core at ${CORE_REMAINING:-0} — replies would fail"; return
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
| `wait_max` | 600s | Too low opens Chrome for a wait that would have been shorter than the browser pass itself; too high parks the merge for most of an hour. Ten minutes roughly matches the cost of resolving a dozen threads by clicking. |
| `core_floor` | 100 | The reply budget. Below it, `stop` is more honest than `browser`. |
| reset buffer | +5s | Guards against clock skew re-tripping the limit immediately. The caller still enforces `polling.md`'s 20s floor. |

Route contract:

| Route | Meaning | Caller does |
|---|---|---|
| `proceed` | GraphQL is fine | normal API path, no fallback |
| `wait <seconds>` | reset is near | bounded wait per `polling.md` (20s+ floor), then re-check once and re-decide |
| `browser` | reset is far, or a secondary limit with no clock | gate with the user, then run the procedure below |
| `stop <reason>` | core is dead too, or auth is broken | report honestly; downgrade to a ready-report |

## Gate — always, in every mode

Ask before the browser opens. **`--auto` asks too.** `--auto`'s "never ask" is
a rule about review judgment, not a licence to commandeer the user's desktop
Chrome under their logged-in identity while they may be using it.

State in the ask: how many threads need resolving, that a new tab will open,
and that the alternative is a ready-report. Declined → ready-report, no
argument.

## Procedure

1. **Invoke the `claude-in-chrome` skill first** — its documented entry point,
   before any `mcp__claude-in-chrome__*` call.
2. `tabs_context_mcp` — also the connectivity probe. An error here means the
   extension is not connected: degrade, do not retry.
3. `tabs_create_mcp` — always a **new** tab. Never reuse a tab the user has
   open.
4. `navigate` to `https://github.com/$OWNER/$REPO/pull/$N` — the Conversation
   tab carries every thread and its Resolve button on one page.
5. **Read state with `get_page_text`.** Plain text is cheapest and most
   reliable for "is this thread resolved" and for the *N unresolved
   conversations* counter. Confirm that counter matches the thread inventory
   from step 3 of SKILL.md; a mismatch means the page is stale — reload once,
   then treat a second mismatch as a degrade.
6. **Build the click map with `read_page`** (`filter: "interactive"`), which
   returns the accessibility tree: every **Resolve conversation** button with a
   stable `ref`, in document order. This is the step that makes clicking
   deterministic — `get_page_text` returns no refs, and `find` caps at 20
   matches with no pagination, so on a PR with more than ~20 threads it
   silently truncates and a fuzzier per-thread query risks matching the *wrong*
   thread. Resolving a thread that has no reply, while leaving a replied one
   open, is the silent resolve arriving through the back door. (`triage.md`
   flags the same scale problem for GraphQL at ~100 threads; the browser path
   hits it 5× earlier.) Use `find` only as a shortcut for a single named
   target, never to enumerate. Large trees: narrow with `depth` / `ref_id`
   rather than falling back to `find`.
7. **Reply over REST first, then resolve in the browser** — never the reverse.
   The reply is the audit trail; if the browser leg then fails you are left
   with a replied-but-open thread (honest and recoverable) instead of a
   resolved-but-unexplained one, which is the silent resolve the Iron Law
   forbids.
8. Click that thread's **Resolve conversation** button with `computer`
   `left_click` **by `ref`, never by coordinate**. The ref comes from step 6's
   tree and names the element directly, so the flow needs no screenshot and no
   pixel arithmetic — and cannot drift when the page reflows between reading
   and clicking. Off-screen button → `computer` `scroll_to` with the same ref.
9. **Verify the mutation landed** — re-read the thread's state and confirm it
   flipped to resolved and the unresolved count decremented. A click is not a
   result. Never assume; never batch-click and check once at the end. Refs can
   go stale when the page re-renders after a resolve: if a subsequent click
   reports a missing element, re-run step 6 for a fresh map rather than
   retrying the old ref.

## Degrade path

Stop after **2–3 failed interactions** — element not found, click with no
state change, page not loading, extension unresponsive. Do not keep retrying
and do not explore other pages.

On stopping, report the split explicitly: which threads were resolved, which
were replied-to but left open, which were untouched. Then downgrade the run to
a ready-report. A partial browser pass is a fine outcome as long as it is
stated accurately.

## What the browser never does

- **Never merges.** The merge decision stays on the API path behind the mode
  gate — a browser click is not a mode gate.
- **Never closes a PR**, never edits the title, never pushes.
- **Never uses `javascript_tool`.** Clicking a button does not need arbitrary
  page script; the grant is deliberately absent, as are `file_upload`,
  `gif_creator`, and `read_network_requests`.
- **Never takes a screenshot.** State comes from `get_page_text`, click targets
  from `read_page`'s accessibility tree, and clicks go by `ref` — the pixel
  path is never needed, so `computer`'s `screenshot` action stays unused.
- **Never triggers a dialog.** A JS dialog blocks every subsequent extension
  command and ends the session.
- **Never polls.** This is a fallback for two operations, not a monitor. Waits
  stay on the API path under `polling.md`'s bounds.
