---
name: pr-merge-flow
description: 'Drive an open GitHub PR to merge by resolving every review thread. Waits (bounded) for AI reviewer bots (Claude, Codex, Greptile, Copilot) to comment, then triages each thread — validate the claim, verify by running code where possible, fix valid findings and push, refute invalid ones with a reasoned reply — every thread resolved either way. Cycles as fixes trigger new reviews, checks the PR title against repo conventions (CLAUDE.md, else Conventional Commits), then ends per mode: --auto (merge, no questions), --confirm (final gate; default), --ready (prep only); --deep adds an opt-in deep review. Quota-safe polling throughout (rate-limit preflight, 20s+ floor, bounded monitors). Use when the user says "merge this PR", "get PR #N merged", "resolve the PR comments", "address review feedback and merge", "close out this PR", "babysit the PR". Never closes a PR without merging; does not write the initial review (/code-review does) or fix failing CI (that is ci-audit).'
allowed-tools: Bash, Read, Grep, Glob, Edit, Write, AskUserQuestion, Skill, Task, mcp__claude-in-chrome__tabs_context_mcp, mcp__claude-in-chrome__tabs_create_mcp, mcp__claude-in-chrome__navigate, mcp__claude-in-chrome__computer, mcp__claude-in-chrome__read_page, mcp__claude-in-chrome__get_page_text, mcp__claude-in-chrome__find
---

# PR merge flow

Resolve every review thread on an open PR — triage, verify, fix or refute — then
drive it to merge per the chosen end mode.

> **Iron Law: EVERY THREAD RESOLVED BEFORE MERGE; EVERY WAIT BOUNDED.** A thread closes
> only as fixed (commit pushed, reply posted) or refuted (reasoned reply
> posted) — never silently. Every poll loop has an interval floor and a hard
> time bound.
>
> No exceptions: not "the bot comment is obviously noise", not "a tight loop
> just this once", not "checks will finish any second".
>
> Violating the letter of this rule is violating the spirit of it.

## Arguments

- `--auto` | `--confirm` | `--ready` — end-mode override for this run
- `--deep` — run the deep-review pass this run

Precedence: invocation (flag or plain ask) > `.claude/pr-merge-flow.local.md` >
default (`confirm`, no deep review). Natural language counts as the flag
("merge it fully automated", "deep review first").

## 1. Resolve target and settings

- Target PR: an explicit number/URL, else the current branch's PR
  (`gh pr view --json number,title,url,state,isDraft`). No PR → stop and say
  so. Draft → report and stop unless told to mark it ready (`gh pr ready`);
  bots rarely review drafts.
- Preferences: read `.claude/pr-merge-flow.local.md` if present (keys: `mode`,
  `deep-review`, `merge-method`, `delete-branch`) and apply silently — its
  whole point is not being asked every time. No file and no flag → `confirm`
  mode; after the first completed run, offer to save the choices there and
  ensure the file is ignored via `.git/info/exclude` — never edit
  `.gitignore` mid-flow, which injects an unrelated change into the very PR
  being merged.
- Conventions: read the repo's CLAUDE.md — commit/PR-title format and
  merge-method conventions there override the defaults below.
- Preflight: `gh auth status`, then the quota check in
  `references/polling.md`. Never assume quota; measure it. GraphQL exhausted
  (its budget is separate from core, and the two thread operations below have
  no REST equivalent) → route via `references/browser-fallback.md`, which
  decides between waiting out the reset and the gated browser escape hatch.

## 2. Bot-wait (bounded)

If the PR was just opened or just received a push, AI reviewer bots may still
be writing. Wait per `references/polling.md`: poll every 20–30s, total bound
~5 minutes (up to 10 on explicit request), proceed early when new reviews
land, proceed anyway at the bound. Never skip the bound; never poll tighter.

## 3. Collect open threads

Follow `references/triage.md`: reads go through REST (`gh pr view`,
`gh api repos/…`); one GraphQL query per cycle fetches thread resolution state
(REST cannot see `isResolved`), and the `resolveReviewThread` mutation is the
only other GraphQL use — GraphQL is never polled. Inventory every unresolved
thread: id, author, file/line, the concrete claim.

If that GraphQL read is rate-limited, build the inventory from REST instead —
it carries every field except `isResolved`, including the `databaseId` replies
and anchors need — and get that one bit from the PR's web UI per
`references/browser-fallback.md`, gated and reset-guarded.

### Keep a thread ledger — the set is live, not a snapshot

Threads keep arriving. Every push can trigger fresh reviews, bots finish at
different times, and a reviewer can post while you are mid-triage. Maintain a
**ledger keyed by `databaseId`** and treat it — never a single fetch, and never
a count — as the source of truth.

Each entry carries: author, file/line, the concrete claim, and its state
through `discovered → verdict → fixed → replied → resolved`.

Re-fetch the REST inventory at the start of every cycle and after every push,
then **merge**: ids already in the ledger keep their state; ids you have not
seen enter at `discovered` and go through the identical loop — verify,
validate, then either refute-and-resolve or fix-comment-resolve. A rising
thread count is the normal lifecycle, not a failed read and not a reason to
re-plan.

The run is complete only when **every** ledger entry reaches `resolved`,
including entries that arrived after you started. Counting open buttons or
trusting a stale inventory is how a thread gets merged over.

## 4. Triage every thread

Per `references/triage.md`, with the receiving-code-review discipline —
technical rigor, no performative agreement:

1. Restate the claim as something checkable.
2. Verify before believing: run the code, test, or failing scenario where
   feasible — a judgment call, but "ran it" beats "read it".
3. Verdict:
   - **Valid** → minimal fix, conventional commit, push, reply naming the fix
     commit, resolve the thread.
   - **Invalid** → reply with the concrete reason it does not hold, resolve
     the thread.
   - **Unclear** → `confirm`/`ready` modes: ask the user, one question at a
     time. `--auto` never asks: make the call if verification can settle it;
     if genuinely undecidable, leave the thread open and downgrade the run to
     a ready-report — the Iron Law forbids merging over it.

When the resolve mutation is rate-limited, the verdicts and fixes are
unchanged and only the closing move relocates: reply over REST first (it rides
the healthy core budget), then resolve that thread in the browser per
`references/browser-fallback.md` — anchored to its own
`#discussion_r<databaseId>`, never picked out of an enumerated list — and
verify that thread flipped. Reply-first is the invariant: a failed browser leg
must leave a replied-but-open thread, never a silent resolve. If the browser is
unavailable too, replied-but-open is the correct resting state and the Iron Law
still forbids merging over it.

**Replies are idempotent.** Before posting, check the thread's existing
comments for one already authored by us (`in_reply_to_id` matching the thread's
top comment). A retry after a failed resolve must not post the reply twice —
re-attempt only the step that failed.

## 5. Re-review cycle

Pushed fixes can trigger fresh bot reviews. Return to step 2, then re-fetch and
**merge into the ledger** (step 3) before triaging — new entries are expected
output of your own fixes, not an anomaly. Bound: 3 cycles by default; still
dirty after that → stop with a report naming every unresolved ledger entry.
Never loop indefinitely.

A cycle that produces only new threads and no new fixes still counts against
the bound; the bound is on cycles, not on progress.

## 6. Merge preflight

- Checks: `gh pr checks` (or REST check-runs). Red checks → hand to
  **ci-audit**; this skill never debugs CI. Resume here after.
- Mergeability/conflicts: REST `mergeable` state (`null` means GitHub is
  still computing — retry once after ~30s; it is not a verdict).
- Title: must match the repo convention (CLAUDE.md), else Conventional
  Commits `type(scope): subject` — with squash merges the title becomes the
  commit subject. Fix via `gh pr edit --title`; `--auto` fixes silently,
  `confirm` shows old → new at the gate.

## 7. End per mode

- **auto** — merge now (`gh pr merge --squash` unless prefs/CLAUDE.md say
  otherwise; `delete-branch` per prefs), then report what was done and run
  the step 9 survey — report-only in this mode. If GitHub rejects the merge
  (branch protection — required approvals, etc.), downgrade to the
  ready-report; never force.
- **confirm** (default) — one final menu: a summary line (threads
  fixed/refuted, checks, title), then **Merge now** (default) /
  **Run deep review first** (non-default) / **Don't merge**. After a
  completed merge, continue to step 9.
- **ready** — report the ready-to-merge state plus the exact merge command;
  mention deep review is available; include the step 9 survey as a
  post-merge preview; stop.

## 8. Deep review (opt-in, never default)

Trigger surfaces: `--deep` or a plain ask at invocation (any mode) ·
`deep-review: always` in the prefs file (any mode, silent) · the confirm-gate
option (confirm mode only). Engines — offer whichever are installed, singly
or as a panel: `/code-review` at high effort, a Codex adversarial pass, the
pr-review-toolkit review agents. Findings land as PR comments and feed
straight back into step 3's loop; when the pass is clean, return to step 7.

## 9. Post-merge cleanup (survey → confirm; never unasked)

After a successful merge, survey — read-only — then present every finding as
a named action with its exact command, in two lists: **needs cleanup** and
**already clean** (state what is done; never silently omit it).

Typical needs-cleanup findings:

- Local PR branch still present → `git branch -d <branch>` (`-d`, never
  `-D`: a refusal means unmerged commits — surface it, don't force).
- Remote PR branch not auto-deleted → `git push origin --delete <branch>`.
- A worktree checked out on the merged branch (also blocks local deletion) →
  `git worktree remove <path>`; stale entries → `git worktree prune`
  (inventory: `git worktree list`).
- Other local branches already merged into the default branch
  (`git branch --merged <default-branch>`, minus the default itself).

Always report, never touch: dirty uncommitted state anywhere (main checkout
or any worktree) — list it as needs-attention and leave it to the user.

The gate: one multi-select menu of the needs-cleanup actions (name +
command). Run only what is selected; a note can adjust any item (a different
branch name, a different worktree path). `--auto` prints the same two lists
and runs nothing — cleanup never executes without an explicit selection or
ask.

## 10. Sync the local default branch (ask; guarded, double-checked)

After the merge, offer — never assume — to bring the local default branch up
to date with the merged remote; the offer joins the step 9 menu as its own
named action. Guards run read-only at survey time and are **re-run
immediately before execution** — state can change between the survey and the
click; a guard tripping at either moment blocks the action and downgrades it
to a needs-attention report:

- Dirty state where the sync would act (`git status --porcelain`).
- The default branch checked out in another worktree (`git worktree list`) —
  someone may be mid-edit there; name the worktree.
- Local commits ahead of the remote
  (`git rev-list --count origin/<default>..<default>` > 0) — fast-forward is
  impossible and those commits belong to someone; never rebase or merge them
  on your own.
- An in-progress git operation (rebase/merge/cherry-pick markers under
  `.git/`).

When every guard is clear, the sync is fast-forward-only:

- default branch not checked out anywhere →
  `git fetch origin <default>:<default>` (moves the ref without touching any
  working tree — the safest form);
- default branch is the current branch → `git pull --ff-only`.

Never bare `git pull`, never `--rebase`, never force. If fast-forward is
impossible a guard already blocked it; divergence is a human decision.

## Red Flags

| Thought | Reality |
|---------|---------|
| "This bot comment is obviously wrong, skip the reply" | Refute in writing, then resolve. Silent dismissal leaves an open thread and no audit trail. |
| "I'll poll every 5 seconds, it's just a few minutes" | Quota is shared. 20–30s floor, rate-limit preflight, bounded total — always. |
| "The monitor script will exit eventually" | Untested monitors hang. Fixed 5–10 min lifetime, then one manual recheck. Pre-validate the check once before arming. |
| "Checks are red — I'll just fix the workflow here" | CI debugging is ci-audit's job. Hand off, resume after. |
| "The suggestion looks right, implement it" | Verify by running first where possible. Plausible ≠ true. |
| "One clean pass, merge" | A push can spawn new reviews. Re-check after every push; merge only from a clean, current pass. |
| "Merged — I'll just tidy the branches too" | Cleanup is survey-then-confirm. Nothing is deleted without an explicit selection. |
| "I'll quickly pull main while I'm at it" | The sync is offered, guarded, re-checked at execution, and ff-only — never a side effect. |
| "GraphQL is rate-limited — nothing to do but report" | The two thread ops have no REST equivalent, but the web UI is a different quota pool. Check the reset clock, then wait or use the gated browser fallback. |
| "GraphQL 403 — open Chrome" | 403 alone is not the trigger. Quota resets hourly; a near reset makes a bounded wait cheaper and safer. `decide_fallback_route` makes the call. |
| "`--auto` means don't ask before opening the browser" | `--auto` suppresses review-judgment questions, not consent to drive the user's logged-in Chrome. The browser gate fires in every mode. |
| "I can see the button in the screenshot — click those coordinates" | Screenshots diagnose; they never target. The browser path is read-only, so a click is never the answer. |
| "`read_page` shows no Resolve button, so it cannot be clicked" | It shows what is *rendered*. Anchor to `#discussion_r<databaseId>` first — depth is the wrong axis, scroll position is the right one. |
| "The button list shrank, so the click worked" | Counting is not verification: the page renders lazily and bots post mid-run, so totals move on their own. Re-read *that* thread's own state. |
| "I tried twice and it failed, so it is impossible" | Negative results need the same rigor as positive ones. Vary the axis that matters before concluding anything is impossible — and never cite a rule from this skill as proof a capability is absent. |
| "Every finding is valid, but there are a lot — let me ask how to proceed" | Valid is not unclear. The rubric already names the action: fix, commit, reply, resolve. Ask only when a verdict is genuinely undecidable, never about strategy. |
| "New bot comments arrived — time to re-plan" | That is step 5, the ordinary re-review cycle. Merge them into the ledger and triage them the same way; the bound is 3 cycles, not a fresh design discussion. |
| "I collected the threads at the start, so I know the set" | The set is live. Re-fetch and merge every cycle and after every push — a thread that arrived while you worked still blocks the merge. |

## See also

- `references/polling.md` — quota preflight, poll bounds, the bounded
  monitor-script pattern, REST/GraphQL split.
- `references/triage.md` — thread queries, verdict rubric, reply etiquette,
  bot roster.
- `references/browser-fallback.md` — the GraphQL-exhaustion escape hatch:
  trigger conditions, reset guard, the read-only browser procedure, and the
  per-thread anchoring that keeps identity exact, and the degrade path.
- `claude-in-chrome` (Claude Code) · `chrome@openai-bundled` (Codex) — the
  fallback's browser entry points, one per harness. Both ship with the harness,
  not with this plugin; the availability table in `browser-fallback.md` picks
  between them, and where neither exists the run degrades to a ready-report.
- `ci-audit` — failing checks and workflow debugging belong there.
- superpowers `receiving-code-review` — the discipline step 4 applies.
- `/code-review` · pr-review-toolkit · Codex — deep-mode engines
  (availability varies by tool).
