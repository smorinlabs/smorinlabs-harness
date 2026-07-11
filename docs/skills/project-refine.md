# project-refine

Walks the user through refining an existing project via one of three
sub-modes chosen by its current trunk status — refining notes/references
(any status), scoping an idea up to ready (`[?]` → `[ ]`, filling
References/Scope/Open-questions), or decomposing a ready/in-progress
project into numbered tasks (`T##`/`TS##`, TDD-biased to start with a test
stub). Every question is asked one at a time, and promotion from idea to
ready always requires an explicit `[y/n]` confirmation — the skill never
flips the trunk glyph on inference alone. When the user uses verbs like
"find"/"look up"/"research"/"investigate", it proactively dispatches
`project-researcher` subagents in parallel and folds the findings into
References or Open questions.

**Triggers on:** "flesh out P##", "scope P##", "promote P##", "add tasks to
P##", "decompose P##", "refine the references on P##" · **Arguments:**
`[project]` — the `P##` to refine (e.g. `project-refine P33`)

## Install

| Mode | When | How |
|---|---|---|
| Plugin (recommended) | Just use it | `/plugin install project-harness@smorinlabs-harness` |
| Dev symlink | Tweak/iterate | `git clone https://github.com/smorinlabs/smorinlabs-harness` then `ln -s "$(pwd)/smorinlabs-harness/plugins/project-harness/skills/project-refine" ~/.claude/skills/project-refine` |
| Direct copy | No marketplace access | copy `plugins/project-harness/skills/project-refine/` into `~/.claude/skills/` |

**Codex:** register the marketplace in `~/.codex/config.toml`
(`[marketplaces.smorinlabs-harness]`, source_type local) and enable the
plugin — or dev-symlink into `~/.agents/skills` (Codex's current skills
location) as well.

## Example session

> "Scope P33"
> → since P33 is `[?]`, enters scope mode: runs the references-block
> helper first (searching plans/specs/git for candidates), then asks about
> Scope and Open questions one at a time, then summarizes and asks
> "Promote P33 to [ ]? [y/n]" — on `y`, renames the file, flips the trunk
> glyph, and commits both in one go.
