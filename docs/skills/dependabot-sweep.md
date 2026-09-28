# dependabot-sweep

Clears the Dependabot backlog across configured GitHub organizations or repos.
An initial open-only app search per owner finds dependency PRs. A repository
inventory supplies visibility and includes repositories with no matching PRs.
Bounded subagent batches review, fix and merge each eligible PR, delegating red CI to `ci-fix` and involved merges to
`pr-merge-flow`. Scope and behavior come from a TOML config; v1 supports
GitHub and `gh` only (anything else stops the sweep). Auto-fix is the
default, with report-only and pause-on-conflict escapes. Further discovery
passes after merge batches and at the end keep evolving scope visible. Full
readable results and follow-up recommendations are both saved and printed inline.

**Triggers on:** "update my dependabot PRs", "dependabot sweep", "clear the
dependabot backlog", "update all the dependency PRs" ·
**Arguments:** `--check` (report only), `--no-auto-fix` (triage, don't fix),
`--pause-on-conflict` (stop and ask), `--config <path>`, `--org <name>`,
`--repo <owner/name>` (repeatable, overrides config scope)

## Install

| Mode | When | How |
|---|---|---|
| Plugin (recommended) | Just use it | `/plugin install repo-hygiene@smorinlabs-harness` |
| Dev symlink | Tweak/iterate | `git clone https://github.com/smorinlabs/smorinlabs-harness` then `ln -s "$(pwd)/smorinlabs-harness/plugins/repo-hygiene/skills/dependabot-sweep" ~/.claude/skills/dependabot-sweep` |
| Direct copy | No marketplace access | copy `plugins/repo-hygiene/skills/dependabot-sweep/` into `~/.claude/skills/` |

**Codex:** register the marketplace in `~/.codex/config.toml`
(`[marketplaces.smorinlabs-harness]`, source_type local) and enable the
plugin — or dev-symlink into `~/.agents/skills` (Codex's current skills
location) as well.

## Example session

> "Clear the dependabot backlog."
> → reads `~/.config/dependabot-sweep/config.toml`, runs one open-only
> Dependabot search per configured org, reports N open PRs across M repos
> and confirms the sweep, then fans out one subagent per repo-with-PRs —
> green PRs merged, red CI delegated to `ci-fix`, involved PRs to
> `pr-merge-flow` — and aggregates one report.

## Durable runs and approval

Each sweep stores its selected PRs, worker attempts, repository leases,
outcomes and follow-ups in a JSONL transaction journal. Concurrent coordinator processes
serialize changes, and replay restores complete transactions. A torn final
append is preserved before recovery repairs the uncommitted tail. Restart
reconciliation checks unfinished attempts before another worker receives the
repository. Reclaiming another session's attempt requires verified termination
of its worker and delegates, supplied through `run reconcile --stopped ATTEMPT`.
Heartbeat silence alone cannot release it. An uncertain merge quarantines the
repository until read-only evidence resolves it.

The configured mode controls authority:

| Mode | Behavior |
|---|---|
| `inspect` | Observe and diagnose; do not repair or merge. `--no-auto-fix` selects this mode. |
| `automated` | Perform granted repairs and merge only after all readiness checks pass. |
| `gated` | Complete preparation, then request approval for each PR before merging. |

Repair permissions are separate grants. Repository settings are never a worker
repair. Approval never waives CI or review requirements, and a changed head
requires new classification and gated approval. A technical failure discovered
while approval is pending becomes a recorded hold. Approval lists include
linked replacement PRs and identify the full head being approved.

Organization and user configuration overrides are resolved per repository at
run creation and saved with the run. Later config edits cannot change that
authority. The report shows each repository's effective mode and repair grants.

The internal orchestrator, `python3 scripts/sweep_cli.py`, creates runs, renders
worker briefs, collects outcomes, and reports the remaining work. Its
`pr observe` and `pr evaluate` commands also support a read-only dry run.
The orchestrator does not merge. The designated worker uses `sweep_merge.py`
to bind the existing merge helper to the classified and approved head, or the
guarded PR-flow route for an involved change. Merge completion requires a fresh
GitHub observation with a merge commit and timestamp.

Commands are relative to the installed skill directory. See the
[CLI interface](../../plugins/repo-hygiene/skills/dependabot-sweep/references/cli-interface.md)
and [configuration schema](../../plugins/repo-hygiene/skills/dependabot-sweep/references/config.md).

## Complete results and follow-ups

The complete readable report is saved to a file and printed inline. Every PR
has its title, link and result; each unresolved PR has a recommendation, a
responsible party and the evidence or event needed to resume. Shared causes and
decisions can be grouped without dropping individual PR rows. Closing a PR is
reported separately from delivering its update through a merge or replacement.

Follow-ups remain visible even after a merge. Their records distinguish the
problem, cause or uncertainty, current status, recommendation, evidence and any
external issue actually filed. An expired budget is an execution stop; an
explicit owner hold cites the instruction that imposed it. The report preserves
completed repair evidence and states whether a verified continuation is running.

Run `python3 scripts/sweep_cli.py --store run.jsonl run describe --save report.md`
from the installed skill directory to save and emit the same report snapshot.
See the [report contract](../../plugins/repo-hygiene/skills/dependabot-sweep/references/reporting.md).

## Bounded work and dependency evidence

Scheduling uses the capacity available to this run and small repository batches.
Waiting for admission does not start a PR's execution clock; retries inherit its
original deadline. Partial worker returns record completed PRs while retaining
outstanding cards and exclusive repository ownership. Discovery preserves both
PR creation time and sweep discovery time and never grants mutation authority
from a newly encountered repository alone.

Classification identifies actual installers and fixture consumers, generated
exports, and requested/resolved/tested versions. A passing frozen-lock workflow
does not prove that another requirements installer tested the requested version.
Relevant check applicability is recorded with evidence; documented exclusions
are distinguished from unexplained missing analysis. Required merge checks are
never waived. See the [receipt contract](../../plugins/repo-hygiene/skills/dependabot-sweep/references/dependency-evidence.md).
