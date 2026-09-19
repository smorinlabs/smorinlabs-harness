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

## 4. Fan out (one subagent per repo-with-PRs)

One Task subagent per repo from step 2 — never one per PR (same-repo PRs share lockfiles and CI; parallel agents in one repo conflict) and never one per quiet repo. Render each agent's brief from [templates/agent-brief.md](templates/agent-brief.md). Delegation to `ci-fix` / `pr-merge-flow` always happens inside these Task subagents, which load and follow the named skill themselves; the orchestrator never invokes a skill directly. The delegation ladder inside every brief:

1. Trivially mergeable (green, no conflicts) → review the diff, merge.
2. Red CI → delegate to `ci-fix` for that repo, then merge.
3. Review findings or involved fixes → delegate to `pr-merge-flow` for that PR.
4. Merge conflict: `pause_on_conflict` set → report back and wait; otherwise record the conflict and move to the next PR.

Agents report back per PR: merged / fixed-then-merged / conflict / needs-human (with reason). No agent touches another repo.

## 5. Trivial direct fixes (narrow fast path, no subagent)

Skip the subagent only when all three hold: the repo is already checked out locally, exactly one Dependabot PR is open in it, and the fix is a mechanical one-file edit (pin bump, generated lockfile refresh). Apply with Edit/Write, commit, push, re-check CI. Anything else fans out per step 4.

## 6. Report

Aggregate every agent's results into one report: merged, fixed-then-merged, conflicts (paused or recorded), needs-human with reasons, plus the discovery cost in API calls. Conflicts under `pause_on_conflict` surface as AskUserQuestion follow-ups, one repo at a time.

## See also

- `ci-fix` — owns red-CI repair inside one repo; sweep agents delegate to it.
- `pr-merge-flow` — owns driving one PR through review to merge; sweep agents delegate involved PRs to it.
- `repo-finder` — resolves a repo name to local checkouts when an agent needs orientation.
- [Config schema](references/config.md) — the TOML file in full.
- [Subagent brief](templates/agent-brief.md) — the fan-out contract.
