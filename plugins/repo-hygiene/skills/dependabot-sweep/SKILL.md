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
- Never silently truncate: if any result count hits its `--limit` (search page, per-repo list, repo list), page further or raise the limit; if it still caps out, report discovery as INCOMPLETE with the capped scope instead of claiming a full sweep.

Group the open PRs by repo. Repos with no PRs get no subagent.

## 3. Gate the sweep

Report the discovery (N open PRs across M repos, grouped by repo with titles). Under `--check`, stop here — no dispatch, no merges. Otherwise confirm via AskUserQuestion — sweep all (Recommended), or check-only instead, with notes to narrow the repo set. One question; notes modify the set.

## 4. Dispatch (bounded dispatcher, one executor per repo)

The coordinator (`scripts/sweep_coordinator.py`) owns inventory, scheduling,
recovery, and reporting from one durable record store
(`scripts/sweep_core.py`: append-only JSONL, replayed on restart). It never
merges. **One executor per repository**: the worker attempt that holds the
repository's mutation lease. It merges through exactly one transport per
PR: the SHA-bound helper (`scripts/gh_merge.py`, behavior unchanged) for
dependency-only PRs, or `pr-merge-flow`'s guarded merge
(`--match-head-commit`) for involved PRs. Nothing else merges, and the
dispatcher never issues a second merge. The orchestrator commands are
`python3 scripts/sweep_cli.py` (interface in
[references/cli-interface.md](references/cli-interface.md)); the rules
below are what those commands enforce.

- **Run wiring**: `run create --run-id <id> --file <discoveries>` (the
  `gh search` JSON from step 2 is accepted as is) stores the header, the
  authority resolved from config, and one card per PR; `attempt create`
  expires dead work and issues one tasking per free repository;
  `brief view <attempt>` renders that worker's brief; hand it to a Task
  subagent; `attempt collect <attempt> --file <outcomes.jsonl>` applies
  the returned outcome records; on any restart, `run reconcile --file
  <observed.json> --live <attempt>...` runs before `attempt create`;
  `run describe` and `approval list` render the report and the approval
  set; `run finish --continuation ...` records the stop reason. Every
  command takes `--store <run.jsonl>` and `-o json`. `pr observe` and
  `pr evaluate` inspect one PR read-only, for diagnosis or a dry run.

- **Tasking**: one Task subagent per repo with schedulable cards, never one
  per PR (same-repo PRs share lockfiles and CI) and never one per quiet
  repo. The brief is rendered from
  [templates/agent-brief.md](templates/agent-brief.md) by
  `scripts/sweep_protocol.py` from a Tasking record: mode (`inspect` /
  `automated` / `gated`), permitted repairs, each granted on its own
  (`branch_update`, `lockfile`, `code_repair`, `major_migration`,
  `replacement_pr`; repository settings never), owner holds, approvals,
  fixed or evolving scope with its cutoff, and one absolute
  `GH_MERGE_DEADLINE_EPOCH` per PR, capped by the run deadline, that
  successor attempts inherit. `--no-auto-fix` selects `inspect`;
  `--check` never reaches dispatch (step 3). No agent touches another repo.
  Each repository has a lock file beside the record store, so a second
  coordinator session over the same store cannot issue a second writer,
  and never reconciles away another session's attempt while its heartbeat
  is fresh.
- **Five checks** (`scripts/sweep_evaluator.py`) at one pinned head decide
  every PR. *Is it what we think?* A full refresh (pull, files, reviews,
  threads, check-runs, check suites, statuses, queue, effective policy)
  bound to the head, and a classifier receipt bound to that head and file
  set. *Did no one lose track?* The lease is held and the repo is not
  quarantined. *Is it green?* The complete effective policy from branch
  protection plus branch rules (unknown never means none); every required
  check green from its required producer; no pending, failed, or
  prerequisite-skipped check; change requests, required approvals, and
  threads clear; `mergeable_state` clean; not in a merge queue. *Allowed?*
  Mode, approval, owner hold, dependency-only receipt, budget. *Did it
  actually merge?* A fresh GET showing `merged` with merge commit and
  timestamp; queue acceptance and auto-merge arming are pending. Missing
  or truncated evidence is `K13` and never merges. A reviewer bot's own
  rate limit is reviewer-unavailable (`K08`), never CI red.
- **Merge path**: `python3 scripts/gh_merge.py <owner> <repo> <pr> merge
  <progress-log> --assert-trivial`, with `[budgets]` from config exported
  as `GH_MERGE_*` per PR. Exit `0`: verify with a fresh GET before recording
  merged. `10`: hold with the helper's literal reason. `11`: unknown; the
  repository is quarantined and the coordinator reconciles it read-only
  before any retry, never auto-retrying an uncertain mutation. The helper
  re-reads volatile evidence immediately before the PUT, and the SHA-bound
  PUT rejects a moved head with `409`. A queue-required target never goes
  through the helper, which refuses it: `pr-merge-flow` enqueues it once,
  and the card holds as `WAITING` `K10` (pending, never merged) until a
  fresh observation shows the merge.
- **Diagnosis before repair** (`scripts/sweep_diagnosis.py`): a red check
  is attributed only by a matched baseline control, meaning the same
  workflow, job, matrix, command, toolchain, environment, and inputs run on
  the base revision. The same failure there is `K05` baseline, and every
  PR it blocks links one shared incident id (`ISS-…`); base green is `K04`
  regression; unmatched or missing controls are `K04` with low confidence
  and name the gap; a green same-head retry is `K17` transient with the
  mechanism unknown; a runner or network signature is `K06`. Every verdict
  still holds the PR. Changed files alone never prove a pre-existing
  failure, and a baseline failure never waives required CI.
- **Repair loop** (bounded, within the permitted repairs): red PRs go to
  `ci-fix` with the PR's remaining budget, diagnosed first, then return to
  the five checks exactly once at the resulting head. Repairs never change
  repo settings; if one is needed, the PR goes to `NEEDS_OWNER` with the
  exact enable path. Involved PRs go to `pr-merge-flow` under the same
  authority. `pause_on_conflict` stops the repo at the first conflict.
- **Returns and recovery**: workers return one outcome record per assigned
  PR (`merged` / `ready` / `hold` / `unknown` / `closed`, fields per the
  brief); the coordinator refuses an incomplete batch before any record
  changes. After a crash or restart it replays the store, marks dead
  attempts, reconciles every orphaned or quarantined repository against
  fresh observation, and only then schedules successor attempts.
- **Patience** (`scripts/sweep_patience.py`): one absolute deadline bounds
  each child's whole process tree; at expiry the process group is
  terminated, then killed. A delegate inherits the earlier deadline, and a
  retry after the deadline never starts. Observation waits only when the
  expected CI time fits the window; a longer job is deferred to a named
  continuation. Holds are re-dispatched only when explicitly woken, and
  idle cards past their deadline expire to `WAITING` `K14`.

## 5. Trivial direct fixes (narrow fast path, no subagent)

Skip the subagent only when all hold: the repo is already checked out locally,
exactly one Dependabot PR is open in it, the repo mutation slot is free, and
the fix is a mechanical one-file edit (pin bump, generated lockfile refresh).
Apply with Edit/Write, commit, push, then merge only through the step-4 helper
(a repair push invalidates cached evidence, so the helper re-preflights).
Anything else dispatches per step 4.

## 6. Report

`scripts/sweep_report.py` renders one report from the record store: a
header with selected and delivered counts (direct plus via replacement),
unresolved cards first by consequence and owner (each with reason code,
evidence, next action, owner, and resume trigger), prepared cards, merges
with commit and timestamp, shared incidents with every PR they block, late
arrivals, worker reconciliation, and one explicit continuation state. The
ending is COMPLETE (every selected PR terminal), WITH EXCEPTIONS (every
PR processed, the rest held with a reason and owner), or INCOMPLETE (a PR
never processed, or discovery incomplete). A watcher or scheduled
invocation counts as continuation only with a concrete reference and the
time it was verified running; otherwise the report says none is
running. The approval presenter lists every
`NEEDS_OWNER` card most-consequential-first with a fixed decision block.
Add the discovery cost in API calls. Conflicts under `pause_on_conflict`
surface as AskUserQuestion follow-ups, one repo at a time.

## See also

- `ci-fix` — owns red-CI repair inside one repo; sweep agents delegate to it.
- `pr-merge-flow` — owns driving one PR through review to merge; sweep agents delegate involved PRs to it.
- `repo-finder` — resolves a repo name to local checkouts when an agent needs orientation.
- [Config schema](references/config.md) — the TOML file in full.
- [Subagent brief](templates/agent-brief.md) — the fan-out contract.
