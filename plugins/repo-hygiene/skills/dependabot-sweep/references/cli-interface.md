# sweep_cli — interface spec

The orchestrator CLI the sweep skill runs: `python3 scripts/sweep_cli.py`.
Pinned to the CLI Design Standard **v1.4.14** (`cli-design-standard.md`,
2026-06-28). Tier **minimal** (an internal skill helper, not an installed
binary). Profile **noun-verb** (R1.1): twelve commands across six nouns,
above the Appendix A verb-first bound. Conformance record:
[cli-conformance.md](cli-conformance.md).

This CLI never merges and never mutates GitHub. `pr observe` is its only
network command and it only reads.

## Identity

| | |
|---|---|
| Invocation | `python3 scripts/sweep_cli.py <noun> <verb> [flags]` (program name `dependabot-sweep`) |
| Version | `-V` / `--version` prints `dependabot-sweep <semver>`; the version comes from `plugins/repo-hygiene/.claude-plugin/plugin.json` (authoritative), else `0.0.0+unknown` (R4.6) |
| Help | `-h` / `--help` on every command: `Usage:` line, arguments, flags, `Examples:` (R7.5); help and version go to stdout with exit 0 (R7.1) |

## Command tree

| Command | Purpose | Verb basis |
|---|---|---|
| `run create` | Create the run: header, authority from config, one NEW card per discovered PR | R2.1 `create` |
| `run view` | Header, counts, delivered totals, stored authority | R2.1 `view` |
| `run describe` | The full report rendered from the store | R2.1 `describe` (expanded detail) |
| `run reconcile` | Reconcile dead attempts and quarantined repositories against fresh observations | domain verb |
| `run finish` | Record the stop reason and the one explicit continuation | domain verb |
| `attempt create` | Expire dead work, then issue one tasking per free repository | R2.1 `create` |
| `attempt collect` | Apply one worker's outcome records (whole batch validated first) | domain verb |
| `brief view` | Render an attempt's brief from the template and the run's authority | R2.1 `view` |
| `card list` | Every card with state and reason | R2.1 `list`; empty list exits 0 (R6.2) |
| `card view` | One card | R2.1 `view`; unknown id exits 3 (R6.2) |
| `pr observe` | One full read-only observation of a PR (pull, files, reviews, threads, checks, suites, statuses, queue, effective policy) | domain verb |
| `pr evaluate` | The five checks over an observation; prints the outcome record a worker would return | domain verb |
| `approval list` | The approval set: every NEEDS_OWNER card, most consequential first | R2.1 `list` |

Domain verbs are justified in the conformance note (R2.1).

## Global flags

| Flag | Short | Meaning |
|---|---|---|
| `--help` | `-h` | help, exit 0 |
| `--version` | `-V` | version, exit 0 (`-v` is verbose, never version) |
| `--verbose` | `-v` | more diagnostics on stderr; repeatable |
| `--quiet` | `-q` | suppress non-essential stderr notes; never suppresses stdout results |
| `--debug` | | maximum diagnostics |
| `--config PATH` | | config file; replaces discovery (R5.2) |
| `--store PATH` | | the run's JSONL record store; env `DEPENDABOT_SWEEP_STORE` |
| `--session ID` | | this coordinator session's id; env `DEPENDABOT_SWEEP_SESSION` |
| `--output FORMAT` | `-o` | `table` (default, human) or `json` (machine); accepted before or after the command (R4.5) |
| `--json` | | identical to `-o json` (R4.2) |

No flag is prefix-abbreviated (R3.10). `--` ends option parsing (R3.1).
Every `--file` accepts `-` for stdin (R3.2, R3.9). No secret is accepted on
the command line (R5.5).

## Command flags

| Command | Flag | Type | Default | Meaning |
|---|---|---|---|---|
| `run create` | `--run-id ID` | string, required | | stable run identifier |
| | `--file PATH` | path or `-`, required | | discoveries as JSON: the coordinator shape, or `gh search prs --json number,title,url,repository` output |
| | `--mode MODE` | `inspect` \| `automated` \| `gated` | from config | override the configured mode |
| | `--no-auto-fix` | boolean | false | triage only: inspect mode, no repair, no merge (historical flag) |
| | `--pause-on-conflict` | boolean | from config | stop a repository at its first conflict |
| | `--evolving` | boolean | false (fixed scope) | later arrivals join the selected set |
| | `--cutoff ISO8601` | string | now | discovery instant of a fixed scope |
| | `--authorization TEXT` | string | `dependabot-sweep run create` | the user's authorizing words or record id |
| `run reconcile` | `--file PATH` | path or `-`, required | | `{card id: {"merged": bool\|null, "commit", "at"}}` |
| | `--live ATTEMPT` | repeatable | none | attempt ids known to still run |
| `run finish` | `--continuation KIND` | `none` \| `watcher` \| `scheduled`, required | | the one explicit continuation |
| | `--ref REF` | string | | watcher or invocation reference (required unless `none`) |
| | `--verified-at ISO8601` | string | | when the continuation was verified running (required unless `none`) |
| | `--discovery-incomplete` | boolean | false | discovery capped out; the run ends incomplete |
| `attempt create` | `--model LABEL` | string | | worker model label |
| | `--wake CARD` | repeatable | none | hold card whose resume trigger fired |
| `attempt collect` | `ATTEMPT` | positional | | attempt id (identity, R2.3) |
| | `--file PATH` | path or `-`, required | | outcome records as JSON lines |
| `brief view` | `ATTEMPT` | positional | | attempt id |
| | `--progress-log PATH` | path | `<store>.progress.log` | helper progress log named in the brief |
| `card view` | `CARD` | positional | | card id |
| `pr observe` | `TARGET` | positional | | card id (with `--store`) or `owner/repo#number` |
| `pr evaluate` | `TARGET` | positional | | as above |
| | `--file PATH` | path or `-`, required | | observation JSON from `pr observe -o json` |
| | `--dependency-only` | boolean | false | attest the diff is dependency-only; recorded as a receipt bound to head and file digest |
| | `--classifier NAME` | string | `operator` | who attests |
| | `--mode MODE` | as above | `inspect` | authority when no store is given |
| | `--attempt ATTEMPT` | string | | the attempt holding the repository lease; without it the lease check fails (K12) |
| | `--reviewer-context CONTEXT` | repeatable | from config | status context of a reviewer bot |

## Exit codes and error codes

| Exit | Meaning (R6.1) | Error codes (R7.8 `error.code`) |
|---|---|---|
| 0 | success | |
| 1 | runtime error | `store_error`, `transition_refused`, `lease_refused`, `config_invalid`, `unsupported_host`, `unsupported_tool`, `no_scope`, `invalid_input`, `invalid`, `transport`, `github_error` |
| 2 | usage | `usage` |
| 3 | not found: store file, card, attempt, config file named explicitly | `not_found` |
| 4 | authentication required: no token from `GH_MERGE_TOKEN` or `gh auth token` | `auth_required` |
| 5 | precondition failed: store already exists on `run create`, run header without authority | `precondition_failed` |
| 130 | interrupted | `interrupted` |

Under `-o json` or `--json`, every error is one JSON object on stderr:

```json
{"error": {"code": "not_found", "message": "card 'PR-999' not found; run `card list`"}}
```

Human errors are `error: <lowercase message, no trailing period>` on
stderr (R7.6).

## Configuration and environment (R5.1 to R5.4)

Precedence, highest first: command-line flags; environment variables;
the config file (`--config`, else `DEPENDABOT_SWEEP_CONFIG`, else
`$XDG_CONFIG_HOME/dependabot-sweep/config.toml`, falling back to
`~/.config/dependabot-sweep/config.toml`); built-in defaults. An explicit
`--config` replaces discovery. The schema and defaults are in
[config.md](config.md).

Curated environment variables: `DEPENDABOT_SWEEP_CONFIG` (config path),
`DEPENDABOT_SWEEP_STORE` (run store), `DEPENDABOT_SWEEP_SESSION` (session
id), `DEPENDABOT_SWEEP_OUTPUT` (`json` selects machine output when `-o` is
absent), `GH_MERGE_TOKEN` (GitHub token; the helper's variable, so reads
and merges share one credential source). `GH_MERGE_API_BASE` and
`GH_MERGE_OP_TIMEOUT` are honored by the shared transport.

## Output contract

`table` is the human default and may change between releases. `json` is
the machine format and stays stable within a repo-hygiene major version:
`run create`/`run view` print the run header (plus `counts` on view);
`attempt create` prints the tasking list; `attempt collect` prints
`{attempt, applied, pending}`; `pr observe` prints the observation
(`observation_to_dict`); `pr evaluate` prints
`{target, evaluation, outcome, receipt}`; `run describe` prints
`{header, cards, attempts, issues, report}`. Fields are added, never
renamed or removed, within a major (R7.2).

## Safety

No command is destructive: the store is append-only and `pr observe` only
reads GitHub. Merges are performed by the worker's transport
(`gh_merge.py` or pr-merge-flow), never by this CLI, so `--dry-run`,
`--force`, `--yes`, and `--no-input` do not apply (§8 N/A). The CLI never
prompts.

## Networked behavior (§10)

- Credentials: `GH_MERGE_TOKEN` in the environment, else the `gh auth
  token` credential helper; never a flag (R5.5, R10.1). No token resolves:
  exit 4.
- Reads are bounded by the helper's per-call timeout and the card's
  deadline when a store is given; files and reviews page at 100 items for
  at most three pages, and a capped listing is flagged `truncated` rather
  than silently shortened (R10.3).
- TLS verification is `urllib`'s default; there is no insecure mode
  (R10.6).
- A rate-limit or other HTTP error on a section makes that section
  unreadable (`status` set, `error` filled) and the evaluator holds with
  K13; the CLI does not retry (R10.7 waiver in the conformance note).
