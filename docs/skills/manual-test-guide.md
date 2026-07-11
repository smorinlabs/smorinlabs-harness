# manual-test-guide

Generates a copy-pasteable manual testing guide for the project — discovers
CLI entry points, task-runner recipes, and example scripts, prioritizes
areas touched by recent commits, and produces a guide with prerequisites,
smoke tests, per-feature tests, and recent-change call-outs, with every
command verified to actually exist before it's listed.

**Triggers on:** "how to manually test", "what are manual testing steps",
"what commands to test", "how to test the latest features", "what to
test", "what are the testing commands" · **Arguments:** `--recent` (focus
on recently changed features), `--full` (comprehensive guide for the whole
project), or a specific feature/area name; no args behaves like `--recent`

## Install

| Mode | When | How |
|---|---|---|
| Plugin (recommended) | Just use it | `/plugin install repo-hygiene@smorinlabs-harness` |
| Dev symlink | Tweak/iterate | `git clone https://github.com/smorinlabs/smorinlabs-harness` then `ln -s "$(pwd)/smorinlabs-harness/plugins/repo-hygiene/skills/manual-test-guide" ~/.claude/skills/manual-test-guide` |
| Direct copy | No marketplace access | copy `plugins/repo-hygiene/skills/manual-test-guide/` into `~/.claude/skills/` |

**Codex:** register the marketplace in `~/.codex/config.toml`
(`[marketplaces.smorinlabs-harness]`, source_type local) and enable the
plugin — or dev-symlink into `~/.agents/skills` (Codex's current skills
location) as well.

## Example session

> "What should I manually test after this change?"
> → scans `git diff HEAD~5` for touched files, maps them to CLI commands
> and justfile recipes, and returns a guide with a smoke-test section plus
> a "Recent Changes" section naming exactly which commands exercise the
> diff.
