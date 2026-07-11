# version-check

Reports the project's version across every source it can find — the local
manifest (`pyproject.toml`, `package.json`, `Cargo.toml`, or git tags for
Go), the latest git tag, the `main` branch's manifest, and — with `--full`
— the published registry version — and flags any discrepancies between
them, along with the bump commands the project's task runner exposes.

**Triggers on:** "what version", "check version", "is version published",
"version mismatch", "bump version", "what version is this project", "check
if published" · **Arguments:** `--full` (also check remote registries),
`--bump <patch|minor|major>` (show what the next version would be); no args
shows local version, git tag, and any discrepancies

## Install

| Mode | When | How |
|---|---|---|
| Plugin (recommended) | Just use it | `/plugin install repo-hygiene@smorinlabs-harness` |
| Dev symlink | Tweak/iterate | `git clone https://github.com/smorinlabs/smorinlabs-harness` then `ln -s "$(pwd)/smorinlabs-harness/plugins/repo-hygiene/skills/version-check" ~/.claude/skills/version-check` |
| Direct copy | No marketplace access | copy `plugins/repo-hygiene/skills/version-check/` into `~/.claude/skills/` |

**Codex:** register the marketplace in `~/.codex/config.toml`
(`[marketplaces.smorinlabs-harness]`, source_type local) and enable the
plugin — or dev-symlink into `~/.agents/skills` (Codex's current skills
location) as well.

## Example session

> "What version is this project, and is it published?"
> → reads `pyproject.toml`'s version, compares it to the latest git tag and
> `origin/main`, checks PyPI since the request implies `--full`, and
> returns a table plus the exact `just`/`make` bump command needed if
> anything is behind.
