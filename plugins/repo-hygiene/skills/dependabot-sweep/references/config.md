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

# Authority (Slice 4). Defaults reproduce the historical behavior.
# mode = "automated"       # inspect | automated | gated; auto_fix = false means inspect
# repairs = ["branch_update", "lockfile", "code_repair", "major_migration", "replacement_pr"]
#                          # each repair is granted on its own; repo_settings is never one
# reviewer_contexts = []   # status contexts of reviewer bots (their outage is never CI red)

# Execution budgets, enforced by scripts/gh_merge.py and the coordinator
# (never by prompt text). The orchestrator exports op_timeout_secs as
# GH_MERGE_OP_TIMEOUT and sets GH_MERGE_DEADLINE_EPOCH once per PR when it is
# first scheduled; successor attempts inherit it.
[budgets]
op_timeout_secs = 30    # per HTTP call inside the helper (connect+transfer)
pr_budget_secs = 600    # per-PR deadline span; one absolute epoch per PR
# run_budget_secs = 0           # whole-run deadline; 0 = unbounded
# observation_window_secs = 600 # longest wait one observation may promise
# poll_floor_secs = 20          # minimum seconds between polls; never lowered
# stale_after_secs = 600        # another session's attempt is reconciled only
#                               # past this much heartbeat silence (default =
#                               # pr_budget_secs)
```

- Each scope table takes `visibility` or `repos`. If both appear, `repos`
  wins and `visibility` is ignored. `repos` holds bare repo names (`"web"`),
  resolved under that org/user.
- Any `[defaults]` key may be repeated inside a scope table to override it
  for that scope only.
- Unknown hosts or tools: out of scope in v1 — the sweep stops with a plain
  message rather than guessing.

## Precedence

Highest first: invocation flags (`--no-auto-fix`, `--pause-on-conflict`,
`--mode`, `--org`, `--repo`, `--config`); environment variables
(`DEPENDABOT_SWEEP_CONFIG` names the config file, `DEPENDABOT_SWEEP_STORE`
the run store, `DEPENDABOT_SWEEP_SESSION` the session id,
`DEPENDABOT_SWEEP_OUTPUT` the output format); the config file; built-in
defaults. `--config` (or the env variable) names the sole config file and
replaces discovery of `$XDG_CONFIG_HOME/dependabot-sweep/config.toml`. A
missing discovered file is fine when `--org`/`--repo` supply the scope; a
missing explicit file is an error. `--no-auto-fix` and `--check` always
resolve to `inspect`, whatever `mode` says. `poll_floor_secs` below 20 is
raised to 20. The loader is `scripts/sweep_config.py`; the orchestrator
CLI that consumes it is documented in [cli-interface.md](cli-interface.md).

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
