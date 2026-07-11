# factor-scan

Runs a broad sweep over a directory, file set, or diff range looking for
bugs, quality issues, and architectural smells. It confirms scope and
dimensions with the user, dispatches one `factor-scanner` subagent per
file or area in parallel, collates and deduplicates the findings by
severity, walks each one interactively (accept / modify / skip / mark
intentional), and packages accepted findings into an inline spec ready for
Superpowers `writing-plans`. It never fixes anything itself, and its iron
law defaults every severity conservative — the user lifts severity, not
the skill.

**Triggers on:** "scan", "audit", "review for bugs", "find issues", "quality
check", "code health check", "what's wrong with this?", "any problems in
this code?", or pointing at a file/directory and asking for a sweep ·
**Arguments:** none as flags — the skill's first two steps ask the user to
confirm scope (a directory, file set, diff range, or "recently changed")
and which dimensions to scan (bugs, quality, architectural smells, or all
three)

## Install

| Mode | When | How |
|---|---|---|
| Plugin (recommended) | Just use it | `/plugin install factor-harness@smorinlabs-harness` |
| Dev symlink | Tweak/iterate | `git clone https://github.com/smorinlabs/smorinlabs-harness` then `ln -s "$(pwd)/smorinlabs-harness/plugins/factor-harness/skills/factor-scan" ~/.claude/skills/factor-scan` |
| Direct copy | No marketplace access | copy `plugins/factor-harness/skills/factor-scan/` into `~/.claude/skills/` |

**Codex:** register the marketplace in `~/.codex/config.toml`
(`[marketplaces.smorinlabs-harness]`, source_type local) and enable the
plugin — or dev-symlink into `~/.agents/skills` (Codex's current skills
location) as well.

## Example session

> "Scan src/cli/ for bugs and quality issues"
> → confirms the directory and dimensions, dispatches one `factor-scanner`
> per file in the same message, collates and sorts findings by severity,
> walks each one with the user, and returns a spec titled "bugs / quality /
> refactor in src/cli/" ready to hand to `writing-plans`.
