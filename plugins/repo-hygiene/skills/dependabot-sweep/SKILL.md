---
name: dependabot-sweep
description: Sweep every open Dependabot PR across configured GitHub orgs or repos and drive each toward merge, fanning out one subagent per repo. Reads scope and behavior flags from a TOML config (assumes GitHub and gh unless told otherwise), auto-fixes by default, and delegates red CI to ci-fix and involved merges to pr-merge-flow. Use when the user says "update my dependabot PRs", "dependabot sweep", "clear the dependabot backlog", or "update all the dependency PRs". Not for fixing CI in one repo (ci-fix) or merging one PR (pr-merge-flow).
argument-hint: "[--check] [--no-auto-fix] [--pause-on-conflict] [--config <path>] [--org <name>] [--repo <owner/name>]"
allowed-tools: Bash, Read, Edit, Write, AskUserQuestion, Task
---

# Dependabot sweep

Clear the configured Dependabot backlog through bounded repository workers, with complete results saved to a file and presented inline.

## Arguments (from the user's request)

- `--check` — report only: discover and list open Dependabot PRs, fix nothing.
- `--no-auto-fix` — discover and triage, but don't fix or merge (overrides config `auto_fix`).
- `--pause-on-conflict` — stop and ask on any merge conflict instead of recording and continuing (overrides config).
- `--config <path>` — read this config instead of `~/.config/dependabot-sweep/config.toml`.
- `--org <name>` — select this GitHub org or user; repeatable. Matching configured repository and visibility restrictions still apply.
- `--repo <owner/name>` — select this explicit repository; repeatable. Matching owner visibility and behavior restrictions still apply.

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

## 2. Discover (one cheap initial pass per org)

Start with owner-level searches and a repository inventory; paginate when
needed. Do not send a worker to a repository with no matching PRs.

- Org/user scope: one open-only app search per org (raise `--limit` toward 1000 for large backlogs):
  `gh search prs --app dependabot --state open --owner <org> --limit 100 --json number,title,url,repository,createdAt`
  `--state open` is mandatory — without it, closed PRs pollute the results.
- Explicit repo list (`repos = [...]` or `--repo`): one call per listed repo only —
  `gh pr list --app dependabot --state open -R <owner/name> --limit 100 --json number,title,url,createdAt`
  Add the known `org` and `repo` to each row because this response omits them.
- Collect `gh repo list <org> --limit 1000 --json nameWithOwner,visibility`
  and join by repository identity. Preserve zero-PR repositories in the
  inventory. Each discovery row must carry the observed `visibility`, normalized
  to lowercase, either at top level or in `repository.visibility`. Apply the
  configured public/private filter before admission; missing visibility is an
  evidence gap, not permission to widen scope.
- Never silently truncate: if any result count hits its `--limit` (search page, per-repo list, repo list), page further or raise the limit; if it still caps out, report discovery as INCOMPLETE with the capped scope instead of claiming a full sweep.

Group the open PRs by repo. Repos with no PRs get no subagent. Keep the
complete inventory in one run store. Record each PR's creation time separately
from the time this sweep discovered it. After a merge batch, repeat the
bounded discovery pass while time remains; repeat it once more before the
final report. Apply the original scope and visibility filters on every pass.
An evolving run may admit authorized arrivals within its original deadline;
a fixed run reports arrivals separately. A newly encountered repository never
inherits mutation authority from a search result alone.

## 3. Gate the sweep

Report the discovery (N open PRs across M repos, grouped by repo with titles).
Under `--check`, save that complete discovery report and print it inline, then
stop without dispatch. If the user's existing instructions authorize the
current scope and mode, proceed under them. Otherwise ask one scope question:
sweep all (Recommended), or check-only, honoring notes that narrow the scope.

## 4. Dispatch (bounded dispatcher, one executor per repo)

The coordinator (`scripts/sweep_coordinator.py`) owns inventory, scheduling,
recovery, and reporting from one durable record store
(`scripts/sweep_core.py`: a JSONL transaction journal, replayed on restart). It never
merges. **One executor per repository**: the worker attempt that holds the
repository's mutation lease. It merges through exactly one transport per
PR: `scripts/sweep_merge.py`, which binds the unchanged SHA-bound helper
(`scripts/gh_merge.py`) to the classified and approved head, for
dependency-only PRs; or `pr-merge-flow`'s guarded merge
(`--match-head-commit`) for involved PRs. Nothing else merges, and the
dispatcher never issues a second merge. The orchestrator commands are
`python3 scripts/sweep_cli.py` (interface in
[references/cli-interface.md](references/cli-interface.md)); the rules
below are what those commands enforce.

- **Run wiring**: `run create --run-id <id> --file <discoveries>` accepts the
  identity-complete, visibility-enriched rows from step 2 and stores the header, the
  effective authority resolved per repository from config, and one card per PR;
  carry explicit invocation scope through `--org`, `--repo`, and `--exclude`.
  Later briefs and evaluations use that saved authority. Record the complete
  initial inventory using `run discover --file <inventory>` with the frozen
  coverage selectors and all observed repositories, including those with no PRs.
  Use the same command after merge batches and before final reporting. Its
  JSON contract is in [references/cli-interface.md](references/cli-interface.md).
  `attempt create`
  expires dead work and admits bounded repository batches within available
  worker capacity and the remaining run budget;
  `brief view <attempt>` renders that worker's brief; hand it to a Task
  subagent; `attempt collect <attempt> --file <outcomes.jsonl>` applies
  the returned outcome records; on any restart, `run reconcile --file
  <observed.json> --live <attempt>...` runs before `attempt create`.
  To reclaim an attempt owned by another session, verify that its worker
  and all delegates have stopped and released mutation handles, then pass
  `--stopped <attempt>`. Silence or an expired deadline is not that evidence;
  `run describe` and `approval list` render the report and the approval
  set; `run finish --continuation ...` records the stop reason. Every
  command takes `--store <run.jsonl>` and `-o json`. `pr observe` and
  `pr evaluate` inspect one PR read-only, for diagnosis or a dry run.

- **Tasking**: at most one active Task subagent per repo with schedulable cards, never one
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
  coordinator session over the same store cannot issue a second writer.
  Store transactions serialize scheduling, ID allocation, and collection
  across coordinator processes. Collection checks the current lease holder,
  attempt generation, and owning session. Reconciliation preserves another
  session's held or quarantined attempt until explicitly confirmed stopped,
  regardless of heartbeat age. Missing session identities remain protected
  too; use a stable `--session` value across commands for the same coordinator.
  Set capacity to the worker slots actually available. Use small repository
  batches; unassigned cards remain in the same inventory. A card receives its
  execution deadline only when admitted, and a successor keeps that deadline.
  Do not begin a repair unless the remaining window covers the repair and its
  required post-push validation. Call `plan_repair(expected_secs, now,
  deadline_epoch, reserve_secs)` in [sweep_patience.py](scripts/sweep_patience.py) first, with a
  reserve sufficient for that validation. Proceed only on `decision: repair`
  and stop preparation by its `repair_until` boundary. The default 30-second
  reserve is a floor for admission, not an estimate of every CI run.
  Record a budget continuation instead of
  extending a deadline or claiming that untested preparation is complete.
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
  Classification must also identify the changed files' roles and their actual
  consumers, including secondary installers and generated exports. Record the
  requested, resolved and tested versions for each affected installation path.
  A frozen-lock test does not validate another manifest's requested version.
  Establish fixture use from consumers, not the directory name alone. Record
  relevant check applicability with evidence: an unknown or missing applicable
  analysis remains a hold; a documented exclusion is reported as such. A
  classifier cannot waive a repository-required check. Use the receipt contract
  in [references/dependency-evidence.md](references/dependency-evidence.md).
- **Merge path**: use `sweep_protocol.helper_command` or the exact command
  in the rendered worker brief. It invokes
  `python3 scripts/sweep_merge.py --expected-head <head> --helper-path scripts/gh_merge.py -- <owner> <repo> <pr> merge <progress-log> --assert-trivial`,
  with `[budgets]` from config exported as `GH_MERGE_*` per PR. The head
  must match the classifier receipt and, in gated mode, the approved head.
  Missing or invalid heads fail closed. A different head observed during
  helper preflight defers before any merge; classify the new diff and
  obtain a new gated approval instead of adopting it automatically.
  Exit `0`: verify with a fresh GET before recording
  merged. `10`: hold with the helper's literal reason. A
  `merge queue required` refusal is `BLOCKED` `K12`: the helper and
  evaluator disagree or the worker chose the wrong executor. Refresh
  policy and re-evaluate before choosing an executor; the refusal is never
  queue acceptance. `11`: unknown; the repository is quarantined and the
  coordinator reconciles it read-only before any retry, never auto-retrying
  an uncertain mutation. The helper
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
  mechanism unknown; a runner or network signature is `K06` only when no
  matched baseline exists. Matched control evidence takes precedence over
  those signatures. Every verdict still holds the PR. Changed files alone
  never prove a pre-existing failure, and a baseline failure never waives
  required CI.
- **Repair loop** (bounded, within the permitted repairs): red PRs go to
  `ci-fix` with the PR's remaining budget, diagnosed first, then return to
  the five checks exactly once at the resulting head. Repairs never change
  repo settings; if one is needed, the PR goes to `NEEDS_OWNER` with the
  exact enable path. Involved PRs go to `pr-merge-flow` under the same
  authority. `pause_on_conflict` stops the repo at the first conflict.
- **Returns and recovery**: workers return one outcome record per assigned
  PR (`merged` / `ready` / `hold` / `unknown` / `closed`, fields per the
  brief), either incrementally or in one final batch. The coordinator validates
  every submitted batch before changing records; missing required fields
  refuse that batch. Partial returns retain outstanding cards and repository
  ownership until the attempt is fully accounted for. Include follow-ups on any
  outcome, including a merge. Preserve completed repair evidence and distinguish
  current blockers from execution stops. An owner hold needs its actual source;
  a technical migration or an expired observation window does not imply an
  owner veto. Evaluated READY records carry the full head; a changed head
  revokes any approval that does not match it. After a crash or restart,
  replay restores only committed transactions. A torn final append is
  reported and preserved separately before a locked writer repairs the
  journal tail; corruption inside committed history fails closed. Recovery
  can release a protocol-marked repository claim that never reached a
  committed lease, but never steals an unknown lock by age. After confirmed
  worker termination, reconcile unfinished and quarantined attempts against
  fresh observation before scheduling a successor.
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

**Save the full readable report and print that same report inline.** A file
link, counts-only summary or referral to a ledger does not replace the inline
result. Run `run describe --save <report-path>` to save and emit the same
snapshot, then include its complete human-readable output in the conversation.
For a large sweep, use consecutive repository tables; retain every PR row and
follow-up recommendation. Raw logs and machine journals may remain linked.

The renderer in scripts/sweep_report.py accounts for selected PRs, prepared
work, merges with proof, closures and replacements, unknown outcomes and late
arrivals. Every PR has a title, URL and result. Every unresolved PR has the
current condition, concrete next action, responsible party and evidence or
event needed to resume. Show the execution stop separately from technical
blockers and explicit owner decisions. Group a shared decision once while
keeping every affected PR visible; PR closure and alert/settings changes are
separate scopes. Never turn grouped presentation into blanket merge approval.

Include follow-up work discovered by the sweep even when its associated PR
merged. Give the affected repository, observed problem, cause or uncertainty,
status, recommendation, responsible party and next step. Distinguish local
records from issues actually filed. Say when no follow-ups were identified.
Use the existing incident records for this lifecycle rather than maintaining
an unrelated manual list. See [references/reporting.md](references/reporting.md).

Use non-overlapping outcome counts. Give an observed open-PR total only when
the discovery evidence is complete for the stated scope, and label its time.
Explain unknown or stale counts. Closing an original is not update delivery
unless a linked replacement actually merged. The
ending is COMPLETE (every selected PR terminal), WITH EXCEPTIONS (every
PR processed, the rest held with a reason and owner), or INCOMPLETE (a PR
never processed, or discovery incomplete). A watcher or scheduled
invocation counts as a verified continuation only with a concrete reference
and the time it was verified running. Report missing liveness evidence as
unverified; say none is running only when that absence is established.
The approval presenter lists selected `NEEDS_OWNER` cards and their
linked replacements most-consequential-first with a fixed decision block,
including the head to approve. Unselected late arrivals remain separate.
Recommend an execution order for the remaining work. Name only genuine
uncovered owner decisions; reuse existing authority. Finish with the verified
continuation, unverified work, or established absence of running work, and link the saved
report and supporting evidence. Add the discovery cost in API calls. Conflicts under `pause_on_conflict`
surface as AskUserQuestion follow-ups, one repo at a time.

## See also

- `ci-fix` — owns red-CI repair inside one repo; sweep agents delegate to it.
- `pr-merge-flow` — owns driving one PR through review to merge; sweep agents delegate involved PRs to it.
- `repo-finder` — resolves a repo name to local checkouts when an agent needs orientation.
- [Config schema](references/config.md) — the TOML file in full.
- [Subagent brief](templates/agent-brief.md) — the fan-out contract.
