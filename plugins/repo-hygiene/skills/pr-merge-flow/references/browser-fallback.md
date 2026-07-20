# Browser fallback — reading thread state when GraphQL is exhausted

The escape hatch for the one failure the tool ladder in `polling.md` cannot
climb out of. Narrow by design, and narrower than it first looks: the browser
supplies **one bit per thread — is it resolved — and nothing else.** It never
resolves, never replies, never merges.

## What is actually missing when GraphQL dies

Split the thread inventory by who can supply each field, and the gap is small:

| Field | REST | GraphQL | Browser |
|---|---|---|---|
| comment `databaseId` (needed to reply) | ✅ `…/pulls/{n}/comments` | ✅ | ❌ |
| path, line, author, body | ✅ | ✅ | ✅ (as text) |
| `in_reply_to_id` (has it been answered?) | ✅ | ✅ | — |
| **`isResolved`** | ❌ | ✅ | ✅ |
| resolve a thread | ❌ | ✅ mutation | ❌ **see below** |

REST already carries everything except one boolean. So the browser's job is to
supply that boolean and hand it back to a REST-built inventory — the
`databaseId` never has to survive the page. Resolution itself stays on the API
path: if GraphQL cannot resolve, the run waits or degrades. It does not click.

GitHub's web UI reads that state through session-authenticated internal
endpoints, which do **not** draw on the token's `api.github.com` GraphQL
budget. That is the whole trick: the same fact, billed to a different pool.

## Why this does not resolve threads

Resolving by clicking was tried and does not work on GitHub's PR page. Three
findings, all reproduced on a live PR:

- **`read_page` (`filter: "interactive"`) does not enumerate the Resolve
  buttons at all** — not at default depth, and byte-identically not at
  `depth: 40`. GitHub renders thread controls lazily, so they are absent from
  the accessibility tree. The "deterministic enumeration" this design once
  rested on does not exist here.
- **`find` returns the buttons but strips their identity** — N results, all
  labelled `"Resolve conversation"`, with nothing tying a `ref` to a thread.
  The 20-match cap is not the binding problem; anonymity is. Two threads would
  be as unsafe as twenty.
- **Collapsed and outdated threads render no button at all**, so the visible
  set is not the set you need. On the live PR this was total: every button
  `find` returned belonged to a thread that must *not* be resolved, and the two
  that should have been were invisible.

A click chosen from an anonymous list is a coin flip on a mutating action, and
losing means resolving a thread that has no reply — the silent resolve the Iron
Law forbids, reached through the back door. **So there is no click.**

If a future harness offers per-thread element identity (a ref carrying the
thread or comment id), revisit this section with evidence — not before.

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
a failed attempt — report honestly and never spend the degrade budget
rediscovering the absence.

### Why the Chrome plugin on Codex, and not the other two

- **`browser@openai-bundled`** drives the *in-app* browser. The entire premise
  is GitHub's session-authenticated endpoints; a browser without the user's
  logged-in session cannot read the state at all.
- **`computer-use@openai-bundled`** drives desktop apps generically, with no
  element references. OpenAI's own bundled guidance says the same: prefer the
  Chrome plugin over Computer Use unless the user asks otherwise.

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
browser: if the reset is minutes away, a bounded wait is cheaper, safer, and
keeps the whole run on the API path. Secondary rate limits are the exception —
they publish no reset time, so there is no clock to wait on.

```bash
# Decide the fallback route from a `gh api rate_limit` payload.
# Reads: GRAPHQL_REMAINING, GRAPHQL_RESET (epoch), CORE_REMAINING, SECONDARY (0|1)
# Echoes exactly one of: proceed | wait <seconds> | browser | stop <reason>
decide_fallback_route() {
  local wait_max=600     # reset within 10 min → wait; beyond → browser
  local core_floor=100   # below this, the REST inventory and replies are at risk

  if [ "${CORE_REMAINING:-0}" -lt "$core_floor" ]; then
    echo "stop core at ${CORE_REMAINING:-0} — REST inventory would fail"; return
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
| `wait_max` | 600s | Too low opens Chrome for a wait that would have been shorter than the read itself; too high parks the run for most of an hour. |
| `core_floor` | 100 | The REST budget. Below it, `stop` is more honest than `browser` — a resolution state you cannot act on is not worth fetching. |
| reset buffer | +5s | Guards against clock skew re-tripping the limit immediately. The caller still enforces `polling.md`'s 20s floor. |

Route contract:

| Route | Meaning | Caller does |
|---|---|---|
| `proceed` | GraphQL is fine | normal API path, no fallback |
| `wait <seconds>` | reset is near | bounded wait per `polling.md` (20s+ floor), then re-check once and re-decide |
| `browser` | reset is far, or a secondary limit with no clock | gate with the user, then run the procedure below to **read** state |
| `stop <reason>` | core is dead too, auth is broken, or the harness has no browser tooling | report honestly; downgrade to a ready-report |

Note what `browser` no longer means: it unblocks *seeing* which threads are
open. Closing them still needs GraphQL, so a run that reaches `browser` with
threads left to resolve ends as a ready-report either way — better informed,
not further along.

## Gate — always, in every mode

Ask before the browser opens. **`--auto` asks too.** `--auto`'s "never ask" is
a rule about review judgment, not a licence to drive the user's logged-in
Chrome while they may be using it.

State in the ask: that a new tab will open on the PR, that the browser only
reads and cannot resolve anything, and that declining means a ready-report.
Include the unresolved count **when it is known** — at preflight it is not yet,
because the inventory has not been collected; say so plainly ("count not yet
known; it is what this read determines") rather than inventing a number.
Declined → ready-report, no argument.

## Procedure

Tool names below are Claude Code's. On Codex, map each **role** onto the Chrome
plugin's equivalent — the roles and their order are what matter, not the names:
open a fresh tab, confirm identity, read state as text. A role with no
equivalent on the harness is a `stop`, not something to approximate.

1. **Build the inventory over REST first** — `…/pulls/{n}/comments?per_page=100`
   gives every comment with its `databaseId`, `path`, `line`, `author`, and
   `in_reply_to_id`. Top-level entries (`in_reply_to_id == null`) are the
   threads. This is the spine; the browser only annotates it.
2. **Enter through the harness's entry point** from the availability table. If
   neither is present the availability check has already routed this to `stop`;
   do not improvise a way in.
3. `tabs_context_mcp` — also the connectivity probe. An error here means the
   tooling is not connected: degrade, do not retry.
4. `tabs_create_mcp` — always a **new** tab. Never reuse a tab the user has
   open.
5. `navigate` to `https://github.com/$OWNER/$REPO/pull/$N`.
6. **Confirm identity before trusting one word of the page.** A failed
   navigation, a redirect, a login or SSO wall, or a stale tab can leave you on
   another page entirely, and a coincidentally similar layout is worse than an
   obvious error. Require an exact match on owner, repository, and PR number
   from the page's own canonical URL and title — not from the URL you asked
   for. Any mismatch is a `stop` before anything is read or acted on.
7. **Read state with `get_page_text`.** Take the *N unresolved conversations*
   counter and each thread's rendered header (file path + line range + author).
8. **Correlate back to the REST inventory** on `path` + `line` + `author`, with
   the comment body's first line as tiebreak. Every REST thread must match
   exactly one page thread and vice versa. An ambiguous or partial correlation
   is a `stop` — report the inventory as unknown rather than guessing which
   thread a bit belongs to. Guessing here is the same failure as clicking an
   anonymous button, one step earlier.
9. **Hand back the annotated inventory** and leave the browser. Resolution,
   replies, and the merge decision all happen on the API path, under the
   normal rules in `triage.md`.

## Screenshots — diagnostic only, ephemeral by default

`computer`'s `screenshot` and `zoom` actions are available when the text path
cannot explain what is happening. No extra grant is needed: they are actions of
`computer`, which is already held.

Reach for one when the page is not the expected PR view (login wall, SSO or 2FA
prompt, abuse interstitial, permissions banner), or when `get_page_text` and the
rendered page clearly disagree. Diagnosing that in one image beats three blind
retries.

**Do not persist them.** An authenticated PR screenshot can carry private code,
usernames, and unreleased review context. Keep diagnostics in-session; report
sanitized metadata (what was on screen, in words) rather than the image. Use
`save_to_disk: true` **only after asking the user and getting a yes** — the
degrade report says what blocked the run; it does not need a picture of it
unless the user wants one.

Screenshots count toward the degrade budget: they are for understanding a
failure, not for retrying past one.

## Degrade path

Stop after **2–3 failed interactions** — page not loading, identity mismatch,
correlation ambiguity, tooling unresponsive. Do not keep retrying and do not
explore other pages.

On stopping, report the split explicitly: which threads are known-unresolved,
which are known-resolved, and which could not be determined. Then downgrade the
run to a ready-report. A partial read is a fine outcome as long as it is stated
accurately — an unknown reported as unknown costs nothing; an unknown reported
as resolved breaks the Iron Law.

## What the browser never does

- **Never resolves a thread.** See *Why this does not resolve threads*. There
  is no safe targeting on this page, so resolution stays on the API path.
- **Never replies, never merges, never closes a PR**, never edits the title,
  never pushes.
- **Never clicks anything at all.** This path is read-only, so the old
  ref-versus-coordinate question is moot — and a screenshot is certainly not a
  click target.
- **Never uses `javascript_tool`.** Reading text does not need arbitrary page
  script; the grant is deliberately absent, as are `file_upload`,
  `gif_creator`, and `read_network_requests`.
- **Never triggers a dialog.** A dialog blocks every subsequent command and
  ends the session.
- **Never polls.** This is a one-shot read, not a monitor. Waits stay on the
  API path under `polling.md`'s bounds.
