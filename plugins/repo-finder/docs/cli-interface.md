# repo-finder — CLI interface spec

| | |
|---|---|
| **Binary** | `repo-finder` (lowercase, kebab-case — R1.4) |
| **Profile** | Small-CLI, verb-first (Appendix A — criteria hold: 5 fixed commands, single implicit resource "repo", unlikely to grow; migration trigger: a second resource type ⇒ noun-verb in the next major) |
| **Tier** | minimal |
| **Standard** | CLI Design Standard v1.4.14 |
| **Shape** | Single-file uv-shebang Python script (argparse) |

Purpose: resolve repo names to local paths + identity facts (origin, default
branch, checkout-vs-worktree kind, tooling profile) from a config-bounded
multi-root scan, with a gh REST-first remote org tier. Primary consumer is an
LLM agent; output is token-optimized compact text by default, JSON on request.

## Command tree

| Command | Purpose | Exit on "nothing" |
|---|---|---|
| `find <query>` | Resolve a repo name (substring/fuzzy) to all local matches with orientation facts; on local miss, remote org lookup; on total miss print clone hint + search suggestions to stderr | `3` not found (R6.2 view-of-missing default) |
| `list` | Enumerate all repos across configured roots, one line each | `0` — empty set is success (R6.2) |
| `orgs` | Show configured GitHub orgs (owned/member) from config; no network | `0` |
| `org <name>` | List repos in one remote org (REST-first), bounded page | `3` if org unknown/empty answer from API distinguishes: unknown org `3`, empty list `0` |
| `init` | Write a starter config to the user config path and print it; refuses to overwrite without `--force` | `0`; existing config without `--force` → `5` conflict |

Depth 1 ≤ 3 (decision 11). Verbs are domain verbs (`find`, `init`) plus core
`list` (R2.1); `orgs`/`org` are read-only views, documented here (decision 23).

## Flags

Global (all commands):

| Long | Short | Type | Default | Notes |
|---|---|---|---|---|
| `--help` | `-h` | flag | — | stdout, exit 0 (R4.1) |
| `--version` | `-V` | flag | — | stdout, exit 0 (R4.1; `-v` reserved for verbose per decision 3, not used at this tier) |
| `--config` | — | path | XDG chain | explicit config file (R5.1) |
| `--output` | `-o` | enum `text\|json` | `text` | machine output (R4.2) |
| `--json` | — | flag | — | ≡ `-o json` (R4.2) |

Per command:

| Command | Long | Type | Default | Notes |
|---|---|---|---|---|
| `find` | `--no-remote` | flag | remote on | skip the remote org tier (negation form, R3.6; config key `remote.enabled`, R3.8) |
| `find` | `--root` | path, repeatable | — | extra scan root(s) for this run (R3.7) |
| `org` | `--limit` | int | `100` | bounded remote page (R10.3); hint on stderr when more exist |
| `init` | `--force` | flag | — | overwrite existing config (R3.4 reserved `-f` not given a short here to keep the destructive-ish path deliberate) |

`--` terminator honored; no command reads stdin, so `-` has no file role
(R3.1/R3.2 N/A noted). No secrets are accepted via argv — there are no
credential flags at all; GitHub auth is delegated to `gh` (R5.5).

## Exit codes (R6.1)

| Code | Meaning here |
|---|---|
| `0` | Success (including empty `list`) |
| `1` | Runtime error (config unparseable, root unreadable, gh invocation failed unexpectedly) |
| `2` | Usage error (unknown command/flag) — argparse native |
| `3` | Not found (`find` with zero local+remote matches; `org` with unknown org) |
| `4` | Auth required (remote tier needed but `gh` unauthenticated) |
| `5` | Conflict (`init` onto an existing config without `--force`) |
| `130` | SIGINT |

`find` miss (`3`) is an expected negative: the clone hint / suggestions go to
stderr as *diagnostics*, not as an error record (R6.2, R7.6).

## Config & env (R5.1–R5.4)

Precedence: flags > `REPO_FINDER_*` env > project `./.repo-finder/repo-finder_config.toml`
> user `$XDG_CONFIG_HOME/repo-finder/repo-finder_config.toml` > built-in defaults
(default root: `~/c` if it exists, else `~`,  depth 1).

Curated env (R5.4): `REPO_FINDER_CONFIG` (config path), `REPO_FINDER_NO_REMOTE=1`.

```toml
# repo-finder_config.toml
[[roots]]
path = "~/c"            # expanded; walked to `depth` (default 3) with a built-in
# depth = 3             # prune list (node_modules, .venv, target, …) — unknown
exclude = ["_archive"]  # group subdirs and nested copies are found automatically

[[roots]]
path = "~/wt"           # worktree root — matches link back to their main repo

[orgs]
owned  = ["example-org"]
member = ["another-org"]

[remote]
enabled = true
transport = "rest"      # "rest" (default; gh api repos/...) | "graphql" (gh repo list/view)
```

## Output contract

Human/agent default (`text`): one compact block per match, ~5 lines, stable
field order:

```
py-launch-blueprint  ~/c/py-launch-blueprint
  origin  github.com/example-org/py-launch-blueprint  default main  clean  2d ago
  kind    checkout
  tooling uv (pyproject.toml), just
py-launch-blueprint  ~/wt/py-launch-blueprint-fix
  kind    worktree -> ~/c/py-launch-blueprint  branch fix/ci  dirty
```

`--json` (R7.2 open-by-default, additive-only): array of match objects
`{name, path, kind, worktree_of, origin, default_branch, branch, dirty,
last_commit, tooling[], source: "local"|"remote"}`. Errors under `--json` are a
single object `{"error": {"code": "...", "message": "..."}}` on stderr (R7.8);
codes include `not_found`, `auth_required`, `rate_limited` (R10.7).

## Networked tier (§10, applicable subset)

- Auth: delegated entirely to `gh` — no tokens touched (R10.1 N/A beyond the
  exit-`4` mapping when `gh auth status` fails).
- REST-first: `gh api users/<org>/repos` / `gh api orgs/<org>/repos`
  (paginated via `--limit`, R10.3); `transport = "graphql"` opts into
  `gh repo list`. Rate-limit responses are recognized distinctly, reported on
  stderr, and trigger the transport fallback once (R10.7).
- TLS, retries, idempotency: owned by `gh` (R10.5/R10.6 N/A — no direct HTTP).

## Not-found ladder (`find`)

1. Exact name match across roots (incl. group dirs) → done.
2. Substring / fuzzy match → ranked candidates.
3. Widen: `depth+1` under configured roots only — never `$HOME`-wide.
4. Remote: org membership lookup (unless `--no-remote`).
5. Miss: exit `3`; stderr prints the exact `git clone` command when the name
   resolved remotely-only, else 2–3 bounded suggestions (other roots to add to
   config, `repo-finder init` hint) and invites the user to name a location.
