# project-next

Reads `PROJECTS.md` and the relevant `projects/` files to build a
composite, three-part menu — in-progress projects with their next task and
any blocking dependency, the next 2-3 lowest-ID unstarted projects, and the
2-3 most recently committed project files (by git commit time, not
filesystem mtime) — then asks the user where to focus and points them at
the right sibling skill or framework in text, without ever invoking it or
editing the trunk itself.

**Triggers on:** "what's next?", "where are we?", "what should I work on?",
returning to a repo after time away · **Arguments:** none

## Install

| Mode | When | How |
|---|---|---|
| Plugin (recommended) | Just use it | `/plugin install project-harness@smorinlabs-harness` |
| Dev symlink | Tweak/iterate | `git clone https://github.com/smorinlabs/smorinlabs-harness` then `ln -s "$(pwd)/smorinlabs-harness/plugins/project-harness/skills/project-next" ~/.claude/skills/project-next` |
| Direct copy | No marketplace access | copy `plugins/project-harness/skills/project-next/` into `~/.claude/skills/` |

**Codex:** register the marketplace in `~/.codex/config.toml`
(`[marketplaces.smorinlabs-harness]`, source_type local) and enable the
plugin — or dev-symlink into `~/.agents/skills` (Codex's current skills
location) as well.

## Example session

> "Where are we?"
> → reads the trunk, checks git commit recency for each project file, and
> returns "In progress: P21 (next: TS02), P19 (blocked on P39) · Next up:
> P22, P25 (blocked on P19, P22) · Recently touched: P33 (idea), P21, P40 —
> where would you like to focus?", then hands off to `project-refine P33`
> or `superpowers:executing-plans` based on the answer, without starting
> anything itself.
