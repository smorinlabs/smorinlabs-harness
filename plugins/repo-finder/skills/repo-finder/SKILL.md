---
name: repo-finder
description: Resolve a repo name to its local path(s) and identity facts — origin, default branch, checkout-vs-worktree kind, branch, dirty state, build tooling — with one fast config-bounded command instead of exploring the filesystem. Fire whenever a repo is referenced by bare name and its location isn't already established in this session — BEFORE running ls/find/glob over home or code directories to locate a repo, BEFORE gh repo view/list to identify an origin or enumerate org repos, and for "where is <repo>", "what repos do I have", "which org owns X", "is this a worktree", "what's the exact name to clone". Covers local multi-root scan plus a gh REST-first remote org fallback from user config. Not for searching file contents inside an already-located repo, and not for cloning or mutating anything — it only finds and describes.
allowed-tools: Bash
---

# repo-finder

One command that replaces filesystem hunting: resolve a repo name to every
local copy (with orientation facts) or, failing that, to its exact remote
`owner/name` — so agents never `ls`/`find` their way through a code directory.

## Locate and run the CLI (any install mode, either tool)

The CLI ships inside this skill's own directory, so every install method
(plugin, dev symlink, direct copy — Claude Code or Codex) delivers it.
Resolve it in this order and reuse the result for the whole session:

```bash
RF="$(command -v repo-finder || true)"                 # 1. explicit PATH install, if any
[ -x "$RF" ] || RF="<skill-base>/scripts/repo-finder"  # 2. base dir announced when this skill loaded
if [ ! -x "$RF" ]; then                                # 3. well-known placements
  for d in "$HOME/.claude/skills/repo-finder" "$HOME/.agents/skills/repo-finder"; do
    [ -x "$d/scripts/repo-finder" ] && RF="$d/scripts/repo-finder" && break
  done
fi
"$RF" find <query>
```

No `uv` on the machine? `python3 "$RF" ...` works identically — the script is
stdlib-only (Python ≥3.11). Quote the path; never guess other locations.

```bash
"$RF" find <query>      # resolve a name (substring ok)
"$RF" list              # every repo, one line each
"$RF" orgs              # configured GitHub orgs (no network)
"$RF" org <name>        # one org's repos (paged REST)
"$RF" init              # write a starter user config
```

Add `--json` for machine output. Full interface: `docs/cli-interface.md` in
the plugin.

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
- `3` — definitively not found: local roots AND (unless skipped) the
  configured GitHub orgs were all actually searched. Expected negative:
  don't treat as a tool failure.
- `1` on `find` — degraded search: the local scan missed AND the GitHub
  lookup failed for the orgs named on stderr, so the result is LOCAL-ONLY
  and may be incomplete. Do not conclude the repo doesn't exist; fix the
  gh problem or retry before deciding.
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
