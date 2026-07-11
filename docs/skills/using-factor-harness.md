# using-factor-harness

Orients across the other three factor-harness skills (`factor-architect`,
`factor-scan`, `factor-dedup`) and routes to the right one based on what's
being asked for — architectural review, a broad bug/quality/smell sweep, or
cross-implementation dedup. Explains the shared conventions (pure workflow
shape, per-finding interactive walk, inline output only, read-only, three
subagents) and how the plugin hands off to Superpowers `writing-plans` /
`executing-plans` for the actual refactor. It never invokes the workflow
skills itself — it teaches and routes.

**Triggers on:** "what factor-harness skills exist?", mentions of
architecture review, refactor opportunities, code scanning, bug hunting,
quality checks, or duplicated implementations, or before invoking any
specific factor-* skill when the right choice is unclear · **Arguments:**
none

## Install

| Mode | When | How |
|---|---|---|
| Plugin (recommended) | Just use it | `/plugin install factor-harness@smorinlabs-harness` |
| Dev symlink | Tweak/iterate | `git clone https://github.com/smorinlabs/smorinlabs-harness` then `ln -s "$(pwd)/smorinlabs-harness/plugins/factor-harness/skills/using-factor-harness" ~/.claude/skills/using-factor-harness` |
| Direct copy | No marketplace access | copy `plugins/factor-harness/skills/using-factor-harness/` into `~/.claude/skills/` |

**Codex:** register the marketplace in `~/.codex/config.toml`
(`[marketplaces.smorinlabs-harness]`, source_type local) and enable the
plugin — or dev-symlink into `~/.agents/skills` (Codex's current skills
location) as well.

## Example session

> "I'm not sure if I want factor-scan or factor-architect for this"
> → walks the routing table (`factor-scan` is broad and dimension-agnostic;
> `factor-architect` is narrow and pattern-focused, keyed to a specific plan
> or feature), asks one clarifying question if it's still ambiguous, and
> points at the right skill without running it.
