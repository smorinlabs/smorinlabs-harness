# factor-dedup

Compares N implementations the user suspects are duplicates, dispatches
`factor-comparator` subagents in parallel (and optionally a
`factor-researcher` for ecosystem-specific consolidation patterns),
classifies each divergence as truly identical, intentionally different, or
accidentally divergent, and walks the accidental divergences with the user
one at a time. Produces either a unified-design consolidation spec or —
when the divergence turns out to be justified — a documentation spec that
records why the implementations should stay separate, both ready for
Superpowers `writing-plans`. Its iron law: "these look duplicated" is a
hypothesis, not a fact, and the right answer is sometimes "leave them
separate".

**Triggers on:** "consolidate these", "these all look the same", "DRY this
up", "extract common code", "shared abstraction", "these N files look
duplicated", "5 commands doing the same thing", "merge these
implementations" · **Arguments:** none — the skill's first step confirms
the candidate set of files/functions with the user and checks whether any
sibling implementations were missed

## Install

| Mode | When | How |
|---|---|---|
| Plugin (recommended) | Just use it | `/plugin install factor-harness@smorinlabs-harness` |
| Dev symlink | Tweak/iterate | `git clone https://github.com/smorinlabs/smorinlabs-harness` then `ln -s "$(pwd)/smorinlabs-harness/plugins/factor-harness/skills/factor-dedup" ~/.claude/skills/factor-dedup` |
| Direct copy | No marketplace access | copy `plugins/factor-harness/skills/factor-dedup/` into `~/.claude/skills/` |

**Codex:** register the marketplace in `~/.codex/config.toml`
(`[marketplaces.smorinlabs-harness]`, source_type local) and enable the
plugin — or dev-symlink into `~/.agents/skills` (Codex's current skills
location) as well.

## Example session

> "These 4 CLI subcommands all look the same, can we consolidate?"
> → confirms the 4 files, dispatches one `factor-comparator` per file in
> parallel plus a `factor-researcher` on canonical subcommand patterns,
> buckets the findings (2 truly identical, 1 intentionally different due to
> a domain constraint, 1 accidentally missing a validation check), walks
> the accidental divergence with the user, and returns a consolidation spec
> with a unified signature and migration plan.
