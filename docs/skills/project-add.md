# project-add

Captures a new project idea in at most four one-at-a-time questions (title,
one-sentence description, optional open-questions/notes, and
idea-vs-refine-now), reserves the next `P##` ID as local-max-plus-one,
writes the idea stub from the plugin's template, appends the trunk row,
and commits both files atomically in a single local git commit. It refuses
to ask about scope, references, or tasks — that depth is `project-refine`'s
job.

**Triggers on:** "I had an idea", "capture this", "add a project for...",
any phrasing signaling a new project to register on the trunk ·
**Arguments:** `[seed]` — an optional positional seed title (e.g.
`project-add "Rate-limit OpenAI client"`) that pre-fills question 1 without
skipping its confirmation

## Install

| Mode | When | How |
|---|---|---|
| Plugin (recommended) | Just use it | `/plugin install project-harness@smorinlabs-harness` |
| Dev symlink | Tweak/iterate | `git clone https://github.com/smorinlabs/smorinlabs-harness` then `ln -s "$(pwd)/smorinlabs-harness/plugins/project-harness/skills/project-add" ~/.claude/skills/project-add` |
| Direct copy | No marketplace access | copy `plugins/project-harness/skills/project-add/` into `~/.claude/skills/` |

**Codex:** register the marketplace in `~/.codex/config.toml`
(`[marketplaces.smorinlabs-harness]`, source_type local) and enable the
plugin — or dev-symlink into `~/.agents/skills` (Codex's current skills
location) as well.

## Example session

> "I had an idea: rate-limit the OpenAI client per provider"
> → asks for the title (seed pre-filled, confirmed), then the one-sentence
> description, then optional open questions/notes, then whether to leave it
> as an idea or refine now; computes the next P-number as local max+1,
> writes `projects/P<NN>-rate-limit-openai-client-.md` from the template,
> appends the trunk row, and commits with `docs(projects): capture P<NN> —
> Rate-limit OpenAI client`.
