# project-audit

Runs 11 drift checks against `PROJECTS.md` and `projects/` (trunk/file
consistency, filename-vs-slug, idea-state hygiene, references-block format,
trunk-row link format, TDD task ordering, unique task IDs, cross-reference
resolution) by dispatching one read-only `project-auditor` subagent per
check in parallel, then walks every finding one at a time and asks before
fixing — never batch-applying. By default it runs in focus mode,
restricting to the projects most likely to hold drift (out-of-order
completions, near-done stragglers, and the next few projects above the
completion high-water mark); `--all` runs the full sweep. Every accepted
fix is its own commit and is re-verified immediately afterward, and the
skill is stateless — it doesn't remember past skips, so intentional drift
resurfaces every run for reconfirmation.

**Triggers on:** "audit projects", "is everything in order?", "did I forget
to flip anything?", periodically before merging a long-running branch ·
**Arguments:** `[P##]` to scope to one project, `--all` / `--focus` /
`--candidates` to control scope, `--<check-id>` to run a single check
(e.g. `--filenames`, `--tdd`)

## Install

| Mode | When | How |
|---|---|---|
| Plugin (recommended) | Just use it | `/plugin install project-harness@smorinlabs-harness` |
| Dev symlink | Tweak/iterate | `git clone https://github.com/smorinlabs/smorinlabs-harness` then `ln -s "$(pwd)/smorinlabs-harness/plugins/project-harness/skills/project-audit" ~/.claude/skills/project-audit` |
| Direct copy | No marketplace access | copy `plugins/project-harness/skills/project-audit/` into `~/.claude/skills/` |

**Codex:** register the marketplace in `~/.codex/config.toml`
(`[marketplaces.smorinlabs-harness]`, source_type local) and enable the
plugin — or dev-symlink into `~/.agents/skills` (Codex's current skills
location) as well.

## Example session

> "Audit projects"
> → computes focus candidates (out-of-order, stragglers, recent-active),
> dispatches one `project-auditor` subagent per relevant check in parallel,
> reports "Found 3 drift findings across 2 projects," then walks each one
> ("Fix this? [y/n/skip/explain]"), committing and re-verifying each
> accepted fix individually before moving to the next finding.
