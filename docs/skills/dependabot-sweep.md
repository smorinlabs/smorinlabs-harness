# dependabot-sweep

Clears the Dependabot backlog across every configured GitHub org or repo —
one open-only app search per org finds every open dependency PR (~1 API
call per result page, not ~1 per repo; visibility-filtered scopes add one
`gh repo list`), then one subagent per repo-with-PRs reviews, fixes,
and merges each, delegating red CI to `ci-fix` and involved merges to
`pr-merge-flow`. Scope and behavior come from a TOML config; v1 supports
GitHub and `gh` only (anything else stops the sweep). Auto-fix is the
default, with report-only and pause-on-conflict escapes.

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

Each sweep stores its selected PRs, worker attempts, repository leases, and
outcomes in a JSONL transaction journal. Concurrent coordinator processes
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

The final report accounts for every selected PR, reports skipped checks
separately from successful checks, and names the owner and resume condition for
each hold. It states whether a verified continuation is running.
