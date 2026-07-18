---
name: pr-merge-flow
description: 'Drive an open GitHub PR to merge by resolving every review thread. Waits (bounded) for AI reviewer bots (Claude, Codex, Greptile, Copilot) to comment, then triages each thread — validate the claim, verify by running code where possible, fix valid findings and push, refute invalid ones with a reasoned reply — every thread resolved either way. Cycles as fixes trigger new reviews, checks the PR title against repo conventions (CLAUDE.md, else Conventional Commits), then ends per mode: --auto (merge, no questions), --confirm (final gate; default), --ready (prep only); --deep adds an opt-in deep review. Quota-safe polling throughout (rate-limit preflight, 20s+ floor, bounded monitors). Use when the user says "merge this PR", "get PR #N merged", "resolve the PR comments", "address review feedback and merge", "close out this PR", "babysit the PR". Never closes a PR without merging; does not write the initial review (/code-review does) or fix failing CI (that is ci-audit).'
allowed-tools: Bash, Read, Grep, Glob, Edit, Write, AskUserQuestion, Skill, Task
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
  `references/polling.md`. Never assume quota; measure it.

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

## 5. Re-review cycle

Pushed fixes can trigger fresh bot reviews. Return to step 2. Bound: 3 cycles
by default; still dirty after that → stop with a report of what remains.
Never loop indefinitely.

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
  otherwise; `delete-branch` per prefs), then report what was done. If GitHub
  rejects the merge (branch protection — required approvals, etc.), downgrade
  to the ready-report; never force.
- **confirm** (default) — one final menu: a summary line (threads
  fixed/refuted, checks, title), then **Merge now** (default) /
  **Run deep review first** (non-default) / **Don't merge**.
- **ready** — report the ready-to-merge state plus the exact merge command;
  mention deep review is available; stop.

## 8. Deep review (opt-in, never default)

Trigger surfaces: `--deep` or a plain ask at invocation (any mode) ·
`deep-review: always` in the prefs file (any mode, silent) · the confirm-gate
option (confirm mode only). Engines — offer whichever are installed, singly
or as a panel: `/code-review` at high effort, a Codex adversarial pass, the
pr-review-toolkit review agents. Findings land as PR comments and feed
straight back into step 3's loop; when the pass is clean, return to step 7.

## Red Flags

| Thought | Reality |
|---------|---------|
| "This bot comment is obviously wrong, skip the reply" | Refute in writing, then resolve. Silent dismissal leaves an open thread and no audit trail. |
| "I'll poll every 5 seconds, it's just a few minutes" | Quota is shared. 20–30s floor, rate-limit preflight, bounded total — always. |
| "The monitor script will exit eventually" | Untested monitors hang. Fixed 5–10 min lifetime, then one manual recheck. Pre-validate the check once before arming. |
| "Checks are red — I'll just fix the workflow here" | CI debugging is ci-audit's job. Hand off, resume after. |
| "The suggestion looks right, implement it" | Verify by running first where possible. Plausible ≠ true. |
| "One clean pass, merge" | A push can spawn new reviews. Re-check after every push; merge only from a clean, current pass. |

## See also

- `references/polling.md` — quota preflight, poll bounds, the bounded
  monitor-script pattern, REST/GraphQL split.
- `references/triage.md` — thread queries, verdict rubric, reply etiquette,
  bot roster.
- `ci-audit` — failing checks and workflow debugging belong there.
- superpowers `receiving-code-review` — the discipline step 4 applies.
- `/code-review` · pr-review-toolkit · Codex — deep-mode engines
  (availability varies by tool).
