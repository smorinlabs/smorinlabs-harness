---
name: repo-finder
description: Resolve a repo name to its local path(s) and identity facts — origin, default branch, checkout-vs-worktree kind, branch, dirty state, build tooling — with one fast config-bounded command instead of exploring the filesystem. Fire whenever a repo is referenced by bare name and its location isn't already established in this session — BEFORE running ls/find/glob over home or code directories to locate a repo, BEFORE gh repo view/list to identify an origin or enumerate org repos, and for "where is <repo>", "what repos do I have", "which org owns X", "is this a worktree", "what's the exact name to clone". Covers local multi-root scan plus a gh REST-first remote org fallback from user config. Not for searching file contents inside an already-located repo, and not for cloning or mutating anything — it only finds and describes.
allowed-tools: Bash
---

# repo-finder

One command that replaces filesystem hunting: resolve a repo name to every
local copy (with orientation facts) or, failing that, to its exact remote
`owner/name` — so agents never `ls`/`find` their way through a code directory.

## Run it

The CLI ships inside this skill. From this skill's base directory (shown when
the skill loads):

```bash
<skill-base>/scripts/repo-finder find <query>      # resolve a name (substring ok)
<skill-base>/scripts/repo-finder list              # every repo, one line each
<skill-base>/scripts/repo-finder orgs              # configured GitHub orgs (no network)
<skill-base>/scripts/repo-finder org <name>        # one org's repos (gh REST-first)
<skill-base>/scripts/repo-finder init              # write a starter user config
```

Runs via `uv` (shebang) or `python3 <path>` directly — zero dependencies,
Python ≥3.11. Add `--json` for machine output. Full interface:
`docs/cli-interface.md` in the plugin.

## Reading the output

Matches are ordered deterministically — canonical checkouts first (config-root
order), then worktrees (each labeled `worktree -> <main repo>`), then
nested/vendored copies. Recency, branch, and dirty state are *displayed, not
ranked on*: when several copies exist, YOU decide which one the user means
from those facts (a dirty worktree on a feature branch vs. a clean stale copy
tells its own story). Don't re-verify with `git remote -v` or `gh repo view`
— the facts shown are read live from each repo.

## Exit codes that matter

- `0` — matches printed (local or remote).
- `3` — genuinely not found; stderr carries close-name suggestions and, for
  remote-only hits, the exact `git clone` command. Expected negative: don't
  treat as a tool failure.
- `4` — remote tier needed but `gh` is unauthenticated; either run with
  `--no-remote` or ask the user to `gh auth login`.

## On a miss

The tool already widened within configured roots before reporting `3`. Do not
fall back to `find ~ -type d` or home-wide globs — instead ask the user where
the repo lives and offer to add that root to their config
(`repo-finder_config.toml`, created by `init`), or pass `--root <path>` for a
one-off extra root.

## First use on a machine

If no config exists, defaults scan `~/c` (or `~`) to depth 3. Run `init` and
have the user fill roots and orgs once — that's what makes every later lookup
one cheap call.

## See also

- `docs/cli-interface.md` (plugin) — full flag/exit-code contract.
- Grep/Glob — content search inside a repo this skill has already located.
