---
name: dependabot-sweep
description: Sweep every open Dependabot PR across configured GitHub orgs or repos and drive each toward merge, fanning out one subagent per repo. Reads scope and behavior flags from a TOML config (assumes GitHub and gh unless told otherwise), auto-fixes by default, and delegates red CI to ci-fix and involved merges to pr-merge-flow. Use when the user says "update my dependabot PRs", "dependabot sweep", "clear the dependabot backlog", or "update all the dependency PRs". Not for fixing CI in one repo (ci-fix) or merging one PR (pr-merge-flow).
argument-hint: "[--check] [--no-auto-fix] [--pause-on-conflict] [--config <path>] [--org <name>] [--repo <owner/name>]"
allowed-tools: Bash, Read, Edit, Write, AskUserQuestion, Task
---

# Dependabot sweep

Clear the Dependabot backlog across every configured repo with one discovery pass and one subagent per repo that has open PRs.

## Arguments (from the user's request)

- `--check` — report only: discover and list open Dependabot PRs, fix nothing.
- `--no-auto-fix` — discover and triage, but don't fix or merge (overrides config `auto_fix`).
- `--pause-on-conflict` — stop and ask on any merge conflict instead of recording and continuing (overrides config).
- `--config <path>` — read this config instead of `~/.config/dependabot-sweep/config.toml`.
- `--org <name>` — sweep only this GitHub org or user (overrides config scope).
- `--repo <owner/name>` — sweep only this repo; repeatable (overrides config scope).

Invocation flags beat config; config beats defaults.

## 1. Load scope

Read the TOML config (`--config`, or the default path above). Missing file and no `--org`/`--repo`: ask conversationally which org, user, or repos to sweep — there is nothing credible to suggest. The full schema lives in [references/config.md](references/config.md); the shape is:

```toml
[defaults]
host = "github"   # only host in v1
tool = "gh"       # only tool in v1
auto_fix = true
pause_on_conflict = false

[org."my-org"]
visibility = "all"  # all | public | private, or use repos = [...] instead
```

Non-GitHub hosts are out of scope in v1 — say so and stop rather than guessing at another forge's CLI.

## 2. Discover (one cheap pass per org)

Cost discipline is the point of this skill: discovery costs ~1 API call per org, not ~1 per repo.

- Org/user scope: one open-only app search per org (raise `--limit` toward 1000 for large backlogs):
  `gh search prs --app dependabot --state open --owner <org> --limit 100 --json number,title,url,repository`
  `--state open` is mandatory — without it, closed PRs pollute the results. Each page of results costs exactly 1 search-API call and 0 core calls.
- Explicit repo list (`repos = [...]` or `--repo`): one call per listed repo only —
  `gh pr list --app dependabot -R <owner/name> --json number,title,url`
- `visibility = "public"|"private"`: run the org search, then join `gh repo list <org> --limit 1000` for visibility and drop the rest. Still a handful of calls for the whole org.

Group the open PRs by repo. Repos with no PRs get no subagent.

## 3. Gate the sweep

Unless `--check`: report the discovery (N open PRs across M repos, grouped by repo with titles) and confirm via AskUserQuestion — sweep all (Recommended), or check-only instead, with notes to narrow the repo set. One question; notes modify the set.

## 4. Dispatch (bounded dispatcher, one writer per repo)

The orchestrator classifies every PR and owns deferral; workers execute merges
through the helper and never merge any other way. One merge owner per repo:
the worker running `scripts/gh_merge.py`. The dispatcher owns classification,
the per-repo mutation slot, quarantine records, and post-crash reconciliation.

- **Eligible-now** (all true at a pinned head): checks green (check-runs AND
  commit statuses, required contexts green), dependency-only diff asserted by
  the classifier, `mergeable=true` + `mergeable_state=clean`, no
  `CHANGES_REQUESTED` as any reviewer's latest state, zero unresolved review
  threads, no merge queue requirement.
- **Deferred** (recorded with reason for a later sweep or a human): pending,
  red, dirty, nontrivial, queue-required, oversize/unreadable evidence, or
  anything unknown. Missing evidence always defers — never merges.
- **Merge path**: `python3 scripts/gh_merge.py <owner> <repo> <pr> merge
  <progress-log> --assert-trivial`, with `[budgets]` from config exported as
  `GH_MERGE_*`. Exit `0` merged; `10` deferred (reason logged); `11` unknown
  (hold the repo slot, reconcile read-only, quarantine across restarts —
  never auto-retry an uncertain mutation).
- **Freshness**: volatile checks/reviews refresh inside the helper immediately
  before each PUT; any head change between preflight and merge aborts the
  merge. After each merge or repair push, sibling cached evidence is stale.
  Base movement races are settled server-side: the PUT is SHA-bound and a
  `4xx` is a definitive defer, never a retry.
- **Repair loop** (bounded): red PRs go to `ci-fix` with the PR's remaining
  budget, then return to classification exactly once; a repaired PR may merge
  in the same sweep only after a fresh helper preflight passes. Repairs never
  change repo settings — if one is needed, the PR goes to needs-human with
  the exact enable path. Involved PRs
  go to `pr-merge-flow` with a preparation-only instruction (triage and fix,
  do not merge). `--check` / `--no-auto-fix` skip all merges;
  `pause_on_conflict` stops the repo at the first conflict instead of
  recording and continuing.

One Task subagent per repo-with-PRs — never one per PR (same-repo PRs share
lockfiles and CI) and never one per quiet repo. Render each brief from
[templates/agent-brief.md](templates/agent-brief.md). No agent touches another
repo. After a crash or restart, the dispatcher reads the progress log first
and reconciles every `start` without a matching `result` before any new merge.

## 5. Trivial direct fixes (narrow fast path, no subagent)

Skip the subagent only when all hold: the repo is already checked out locally,
exactly one Dependabot PR is open in it, the repo mutation slot is free, and
the fix is a mechanical one-file edit (pin bump, generated lockfile refresh).
Apply with Edit/Write, commit, push, then merge only through the step-4 helper
(a repair push invalidates cached evidence, so the helper re-preflights).
Anything else dispatches per step 4.

## 6. Report

Aggregate every agent's results into one report with distinct reasons:
merged, fixed-then-merged, deferred (pending / failed-checks / conflict /
queue-required / nontrivial / unreadable-evidence), unknown (quarantined, with
reconcile status), needs-human with reasons — plus the discovery cost in API
calls. Conflicts under `pause_on_conflict` surface as AskUserQuestion
follow-ups, one repo at a time.

## See also

- `ci-fix` — owns red-CI repair inside one repo; sweep agents delegate to it.
- `pr-merge-flow` — owns driving one PR through review to merge; sweep agents delegate involved PRs to it.
- `repo-finder` — resolves a repo name to local checkouts when an agent needs orientation.
- [Config schema](references/config.md) — the TOML file in full.
- [Subagent brief](templates/agent-brief.md) — the fan-out contract.
