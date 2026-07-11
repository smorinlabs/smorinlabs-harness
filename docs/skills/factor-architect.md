# factor-architect

Conducts an architectural review of either a forthcoming plan
(pre-execution) or shipped code (post-execution) against existing precedent
and external canonical patterns. It clusters the patterns in play,
dispatches comparator and researcher subagents in parallel to survey
internal precedent and ecosystem conventions, classifies every finding into
one of four buckets — following good precedent, following bad precedent,
breaking precedent, or new pattern introduced — and walks the user through
each finding before producing an inline architectural review and refactor
spec for Superpowers `writing-plans`. Its iron law: existing precedent is
not automatically good precedent, so following a bad pattern is always
flagged for refactor, never waved through for consistency.

**Triggers on:** "review this plan", "is this architecturally sound?", "any
refactor opportunities?", "does this fit our patterns?", "review recent
commits", "look at the new auth module", "should we apply pattern X here?"
· **Arguments:** none — the skill's first step asks which context applies
(pre- or post-execution) and for the input pointer (plan file, directory,
file set, or commit range)

## Install

| Mode | When | How |
|---|---|---|
| Plugin (recommended) | Just use it | `/plugin install factor-harness@smorinlabs-harness` |
| Dev symlink | Tweak/iterate | `git clone https://github.com/smorinlabs/smorinlabs-harness` then `ln -s "$(pwd)/smorinlabs-harness/plugins/factor-harness/skills/factor-architect" ~/.claude/skills/factor-architect` |
| Direct copy | No marketplace access | copy `plugins/factor-harness/skills/factor-architect/` into `~/.claude/skills/` |

**Codex:** register the marketplace in `~/.codex/config.toml`
(`[marketplaces.smorinlabs-harness]`, source_type local) and enable the
plugin — or dev-symlink into `~/.agents/skills` (Codex's current skills
location) as well.

## Example session

> "I just shipped the new auth module, any refactor opportunities?"
> → reads the delivered code, clusters patterns (error handling, module
> boundaries, naming), dispatches `factor-comparator` against similar
> existing files and `factor-researcher` for ecosystem-canonical auth
> patterns in the same message, classifies findings into the four buckets,
> walks each one (accept / modify / skip / mark intentional), and outputs a
> refactor spec — flagging any case where the new code just follows an
> existing bad pattern instead of fixing it.
