# using-project-harness

Bootstraps the project-harness bundle on first use in a repo — scaffolding
a `PROJECTS.md` trunk if missing, adding a pointer block to
`AGENTS.md`/`CLAUDE.md`, asking once which planning system is in use, and
nudging toward the references-block convention — then routes every
subsequent project-state change (capture, orient, refine, audit) to the
right one of the other four skills. It never edits `PROJECTS.md` or
`projects/` itself; hand-edits bypass the discipline that keeps the trunk
reliable, so this skill insists on routing through the sibling skills
instead.

**Triggers on:** mentions of a project, plan, roadmap, milestone, or
backlog; starting a session in a repo with project-management state;
before editing PROJECTS.md or projects/ by hand; "set up project-harness",
"init project-harness" · **Arguments:** none

## Install

| Mode | When | How |
|---|---|---|
| Plugin (recommended) | Just use it | `/plugin install project-harness@smorinlabs-harness` |
| Dev symlink | Tweak/iterate | `git clone https://github.com/smorinlabs/smorinlabs-harness` then `ln -s "$(pwd)/smorinlabs-harness/plugins/project-harness/skills/using-project-harness" ~/.claude/skills/using-project-harness` |
| Direct copy | No marketplace access | copy `plugins/project-harness/skills/using-project-harness/` into `~/.claude/skills/` |

**Codex:** register the marketplace in `~/.codex/config.toml`
(`[marketplaces.smorinlabs-harness]`, source_type local) and enable the
plugin — or dev-symlink into `~/.agents/skills` (Codex's current skills
location) as well.

## Example session

> "Let's start tracking projects in this repo"
> → runs the four-step bootstrap (scaffolds `PROJECTS.md` from the
> template, offers to add the pointer block to `CLAUDE.md`, asks once
> whether the user uses Superpowers / another system / none, and points at
> the references-block format), then routes: "what's next?" →
> `project-next`, "add an idea" → `project-add`, and so on.
