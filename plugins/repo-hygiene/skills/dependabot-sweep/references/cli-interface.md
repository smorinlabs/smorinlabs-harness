# sweep_cli — interface spec

The orchestrator CLI the sweep skill runs: `python3 scripts/sweep_cli.py`.
Pinned to the CLI Design Standard **v1.4.14** (`cli-design-standard.md`,
2026-06-28). Tier **minimal** (an internal skill helper, not an installed
binary). Profile **noun-verb** (R1.1): eighteen commands across seven nouns,
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
| `run describe` | The full report; `--save` saves and emits the same readable snapshot | R2.1 `describe` (expanded detail) |
| `run discover` | Record a scoped inventory snapshot and its arrivals without changing GitHub | domain verb |
| `run reconcile` | Reconcile dead attempts and quarantined repositories against fresh observations | domain verb |
| `run finish` | Record the stop reason and the one explicit continuation | domain verb |
| `attempt create` | Admit repository batches within capacity and remaining deadlines | R2.1 `create` |
| `attempt collect` | Apply one worker's outcome records (whole batch validated first) | domain verb |
| `brief view` | Render an attempt's brief from the template and the run's authority | R2.1 `view` |
| `card list` | Every card with state and reason | R2.1 `list`; empty list exits 0 (R6.2) |
| `card view` | One card | R2.1 `view`; unknown id exits 3 (R6.2) |
| `card refresh` | Append current read-only evidence without changing mutation authority or outcome state | domain verb |
| `pr observe` | One full read-only observation of a PR (pull, files, reviews, threads, checks, suites, statuses, queue, effective policy) | domain verb |
| `pr evaluate` | The five checks over an observation; prints the outcome record a worker would return | domain verb |
| `approval list` | The approval set: every NEEDS_OWNER card, most consequential first | R2.1 `list` |
| `incident list` | Recorded blockers and follow-ups, including resolved history | R2.1 `list` |
| `incident record` | Record follow-up work locally, including after a merge | domain verb |
| `incident update` | Update follow-up lifecycle and evidence locally | R2.1 `update` |

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
| `--session ID` | | this coordinator session's stable id; env `DEPENDABOT_SWEEP_SESSION`; recovery without a known matching id requires `--stopped` |
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
| | `--org NAME` | repeatable | configured scope | explicit owner scope; discovered repositories alone never grant authority over all of their owner's repositories |
| | `--repo OWNER/NAME` | repeatable | configured scope | explicit repository scope |
| | `--exclude OWNER/NAME` | repeatable | none | exclude a repository from the stored scope |
| `run describe` | `--save PATH` | path | none | atomically save the readable report and still emit it; JSON contains identical text in `report`; refuses the journal path and symbolic-link destinations |
| `run discover` | `--file PATH` | path or `-`, required | | explicit inventory snapshot with timestamp, completeness, coverage, repositories, discoveries and source |
| `run reconcile` | `--file PATH` | path or `-`, required | | `{card id: {"merged": bool\|null, "commit", "at"}}` |
| | `--live ATTEMPT` | repeatable | none | attempt ids known to still run |
| | `--stopped ATTEMPT` | repeatable | none | worker and all delegates verified stopped with mutation handles released; required to reclaim another session's attempt |
| `run finish` | `--continuation KIND` | `none` \| `watcher` \| `scheduled`, required | | the one explicit continuation |
| | `--ref REF` | string | | watcher or invocation reference (required unless `none`) |
| | `--verified-at ISO8601` | string | | when the continuation was verified running (required unless `none`) |
| | `--discovery-incomplete` | boolean | false | discovery capped out; the run ends incomplete |
| `attempt create` | `--model LABEL` | string | | worker model label |
| | `--wake CARD` | repeatable | none | hold card whose resume trigger fired |
| | `--capacity COUNT` | nonnegative integer | 1 | total repository slots available to this run, including its existing occupied slots; not an additional allowance on each call |
| | `--batch-size COUNT` | positive integer | 1 | maximum cards admitted per repository attempt |
| | `--reserve-secs SECONDS` | nonnegative number | 30 | minimum remaining window reserved before admission; workers also judge whether a specific repair and validation fit |
| `attempt collect` | `ATTEMPT` | positional | | attempt id (identity, R2.3) |
| | `--file PATH` | path or `-`, required | | outcome records as JSON lines |
| `brief view` | `ATTEMPT` | positional | | attempt id |
| | `--progress-log PATH` | path | `<store>.progress.log` | helper progress log named in the brief |
| `card view` | `CARD` | positional | | card id |
| `card refresh` | `CARD` | positional | | card id whose evidence is being refreshed |
| | `--file PATH` | path or `-`, required | | read-only observation; never grants approval, adopts a changed head or releases a held/quarantined repository |
| `pr observe` | `TARGET` | positional | | card id (with `--store`) or `owner/repo#number` |
| `pr evaluate` | `TARGET` | positional | | as above |
| | `--file PATH` | path or `-`, required | | observation JSON from `pr observe -o json` |
| | `--dependency-only` | boolean | false | attest the diff is dependency-only; recorded as a receipt bound to head and file digest |
| | `--classifier NAME` | string | `operator` | who attests |
| | `--receipt PATH` | path or `-` | none | complete version-2 classifier receipt, including consumers, tested versions and check applicability; observation and receipt cannot both use stdin |
| | `--mode MODE` | as above | `inspect` | authority when no store is given |
| | `--attempt ATTEMPT` | string | | the attempt holding the repository lease; without it the lease check fails (K12) |
| | `--reviewer-context CONTEXT` | repeatable | from config | status context of a reviewer bot |
| `incident record` | `--file PATH` | path or `-`, required | | follow-up fields; records work locally and never files an external issue |
| | `--card CARD` | repeatable | none | affected cards in the same repository; merged cards may be linked |
| `incident update` | `INCIDENT` | positional | | recorded incident id |
| | `--file PATH` | path or `-`, required | | mutable lifecycle/evidence fields; previous evidence and history remain recorded |

## Discovery and reporting refresh inputs

`run discover --file inventory.json` accepts a read-only inventory:

```json
{
  "observed_at": "2026-09-27T21:40:00Z",
  "complete": true,
  "coverage": [{"kind": "org", "login": "example", "visibility": "public", "repos": []}],
  "scope_repositories": ["example/tool"],
  "repositories": [{"nameWithOwner": "example/tool", "visibility": "public"}],
  "discoveries": [{"org": "example", "repo": "tool", "number": 1,
                   "url": "https://github.com/example/tool/pull/1",
                   "createdAt": "2026-09-27T21:20:00Z"}],
  "source": "complete paginated public-repository and open-PR responses"
}
```

Use the exact frozen selectors from `authority.discovery_scopes`, omitting
only each selector's `authority` field, as `coverage`. Completeness requires
the corresponding repository and visibility inventory, including repositories
with zero open PRs. The observation must be newer than the prior inventory.
Input grants never replace saved authorization. Incomplete scope evidence and
out-of-scope arrivals remain visible and prevent a claim of a complete open
count. An authorized arrival in fixed scope can be counted without being
selected for execution. Absence from discovery never closes a recorded PR.

`card refresh CARD --file observation.json` accepts the JSON from `pr observe`,
with `repository: "owner/name"` and `number` added if the pull response lacks
`base.repo.full_name` and `number`. It requires `observed_at`, a full `head_sha`,
and matching PR identity. It stores `latest_observation` separately from the
evaluated head and outcome. It never evaluates readiness or releases quarantine.
A changed head requires a new evaluation under the existing authorization rules.

`run discover` returns `{snapshot, new_card_ids}`; `card refresh` returns
`{observed_at, observed_head, snapshot}`. Follow-up input fields are documented
in [reporting.md](reporting.md).

## Exit codes and error codes

| Exit | Meaning (R6.1) | Error codes (R7.8 `error.code`) |
|---|---|---|
| 0 | success | |
| 1 | runtime error | `store_error`, `transition_refused`, `lease_refused`, `config_invalid`, `unsupported_host`, `unsupported_tool`, `no_scope`, `invalid_input`, `invalid`, `transport`, `github_error`, `report_write_failed` |
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
`{header, cards, attempts, issues, snapshot, report}`. `snapshot` includes the
distinct outcome counts, separately evidenced open count, complete result rows,
follow-ups and continuation used for the readable report. Fields are added, never
renamed or removed, within a major (R7.2).

`incident list` prints a list of durable incident records; `incident record`
and `incident update` print the resulting record. `run describe --save PATH`
writes the readable report before emitting its result; write failure produces
a structured error without claiming the report was saved. The report's file
and stdout copies use one in-memory snapshot, including follow-ups. The file
cannot replace the source journal, including through an existing hard link.

The version-2 classifier receipt is defined in [dependency-evidence.md](dependency-evidence.md).
Its fields are additive. Loading an older receipt does not establish the new
consumer evidence: evaluation reports an evidence gap until it is refreshed.
The legacy `--dependency-only` flag does not fabricate that evidence.

New run headers include `authority.repositories`, keyed by `owner/repo`,
with each repository's resolved mode, repairs, pause-on-conflict, and
reviewer contexts. Flat authority fields describe the global defaults.
Worker briefs and PR evaluations select the repository entry; only legacy
stores without this map use flat authority. Human reports show the
effective repository modes, including mixed-mode runs.

## Safety

Commands never mutate GitHub; `pr observe` only reads it. Store mutations
are serialized and append one complete transaction at a time. Replay also
accepts legacy single-record lines. A torn final append is reported; before
the next write, its bytes are preserved separately and the uncommitted tail
is removed under the store lock. Malformed committed history fails closed.
Run creation commits its scope, authority, and deadline together.

Reconciliation never infers that another session's worker has stopped from
heartbeat age. Missing session identities are treated as unknown, even when
both are empty. `--stopped ATTEMPT` asserts verified termination of the worker
and every delegate and release of their mutation handles. It cannot overlap
`--live` or name an unknown attempt. Fresh GitHub evidence is still required
before a successor may mutate the repository.

Merges are performed by the worker's transport
(`sweep_merge.py` around the unchanged `gh_merge.py`, or pr-merge-flow),
never by this CLI, so `--dry-run`,
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
