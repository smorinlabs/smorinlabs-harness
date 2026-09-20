# dependabot-sweep config

TOML file. Default location: `~/.config/dependabot-sweep/config.toml`.
`--config <path>` overrides it; `--org` / `--repo` override the scope tables.

## Schema

```toml
[defaults]
host = "github"          # optional, default "github"; only host in v1
tool = "gh"              # optional, default "gh"; only tool in v1
auto_fix = true          # optional, default true; false = triage only
pause_on_conflict = false  # optional, default false; true = stop and ask

# One table per GitHub org or user. The key after org./user. is the login.
[org."my-org"]
visibility = "all"       # all | public | private; ignored when repos is set
# repos = ["web", "api"] # explicit repo names instead of a visibility sweep

[user."my-login"]
visibility = "private"

# Execution budgets, enforced by scripts/gh_merge.py (never by prompt text).
# The orchestrator exports each key as GH_MERGE_<UPPER> before rendering briefs.
[budgets]
op_timeout_secs = 30    # per HTTP call inside the helper (connect+transfer)
pr_budget_secs = 600    # absolute per-PR deadline; retries cannot reset it
```

- Each scope table takes either `visibility` or `repos`, not both. `repos`
  holds bare repo names (`"web"`), resolved under that org/user.
- Any `[defaults]` key may be repeated inside a scope table to override it
  for that scope only.
- Unknown hosts or tools: out of scope in v1 — the sweep stops with a plain
  message rather than guessing.

## Precedence

Invocation flags (`--no-auto-fix`, `--pause-on-conflict`, `--org`, `--repo`,
`--config`) beat the config file; the config file beats built-in defaults.

## Examples

Sweep everything, everywhere configured:

```toml
[org."my-org"]
visibility = "all"
```

Only private repos of one org, and never auto-fix there:

```toml
[org."my-org"]
visibility = "private"
auto_fix = false
```

An explicit list, pausing on conflicts:

```toml
[org."my-org"]
repos = ["web", "api", "worker"]
pause_on_conflict = true
```
