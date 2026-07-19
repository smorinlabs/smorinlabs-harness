# repo-finder

Resolves a repo name to every local copy with orientation facts — path, origin,
default branch, checkout-vs-worktree kind (worktrees labeled with their main
repo), current branch, dirty state, last-commit age, and build tooling — via a
single config-bounded command, so agents stop exploring the filesystem with
`ls`/`find` cascades. On a local miss it falls back to the user's configured
GitHub orgs over `gh` REST-first (GraphQL only as configured fallback) and
returns the exact `owner/name` plus a ready `git clone` command. Ships a
single-file, zero-dependency uv Python CLI inside the skill, conforming to the
CLI Design Standard v1.4.14 (small-CLI profile, minimal tier — see the
plugin's `docs/cli-interface.md` and `CONFORMANCE.md`).

**Triggers on:** a repo referenced by bare name whose location isn't known yet;
the agent being about to `ls`/`find`/glob directories to locate a repo; "where
is <repo>", "what repos do I have", "which org owns X", "is this a worktree",
"what's the exact name to clone"; pre-`gh repo view`/`gh repo list` identity
checks.
**Arguments:** none (the skill wraps the CLI: `find <query>` / `list` / `orgs`
/ `org <name>` / `init`).

## Install

| Mode | When | How |
|---|---|---|
| Plugin (recommended) | You just want to use it | `/plugin install repo-finder@smorinlabs-harness` |
| Dev symlink | You want to tweak/iterate | `git clone https://github.com/smorinlabs/smorinlabs-harness` then `ln -s "$(pwd)/smorinlabs-harness/plugins/repo-finder/skills/repo-finder" ~/.claude/skills/repo-finder` |
| Direct copy | No marketplace access | copy `plugins/repo-finder/skills/repo-finder/` into `~/.claude/skills/` |

**Codex:** register the marketplace in `~/.codex/config.toml`
(`[marketplaces.smorinlabs-harness]`) and enable the plugin — or use the
dev-symlink path, also linking into `~/.agents/skills` (Codex's current
skills location).

**First run:** `scripts/repo-finder init` writes a starter config to
`$XDG_CONFIG_HOME/repo-finder/repo-finder_config.toml`; fill in your scan
roots and GitHub orgs once. Without config it scans `~/c` (or `~`) to depth 3.

## Example session

> "Check CI on the difftree action repo"
> → Instead of `ls ~/c | grep diff` + `gh repo view` probes, the agent runs
> `repo-finder find difftree`, gets all three family members
> (`difftree`, `difftree-action`, `difftree-action-test`) with paths, origins,
> and default branches in ~0.5s / ~180 tokens, and proceeds directly.
