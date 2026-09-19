# dependabot-sweep

Clears the Dependabot backlog across every configured GitHub org or repo —
one open-only author search per org finds every open dependency PR (~1 API
call, not ~1 per repo), then one subagent per repo-with-PRs reviews, fixes,
and merges each, delegating red CI to `ci-fix` and involved merges to
`pr-merge-flow`. Scope and behavior come from a TOML config that assumes
GitHub and `gh` unless told otherwise; auto-fix is the default, with
report-only and pause-on-conflict escapes.

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
