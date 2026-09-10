# Targeted reproduction — the narrowest local command

Rung 0 of the ladder runs only the tests that failed in CI; rung 1 runs the
whole step. This file maps a failed step to both commands, says how each run
is timed and recorded, and covers the cases where the narrowest target is the
whole step. Which rung to enter at is `ladder_plan.py`'s call (SKILL.md step
6): rung 0 only when the step is expected over the local floor (`--isolate-local`,
30s) or is unmeasured, because the isolated run's own overhead is 5–20 s and
isolating a shorter step saves nothing.

## Extract the failing IDs

```bash
gh api "repos/{owner}/{repo}/actions/runs/<run_id>/jobs?per_page=100" \
  --jq '.jobs[] | select(.conclusion=="failure") | {id, name, failed_steps: [.steps[] | select(.conclusion=="failure") | .name]}'
gh api --allow-escape-sequences "repos/{owner}/{repo}/actions/jobs/<job_id>/logs" > "$SCRATCH/job-<job_id>.log"
python3 <skill-dir>/scripts/extract_failures.py --json "$SCRATCH/job-<job_id>.log"
```

`<run_id>` is the failed run from SKILL.md step 1; the first call yields the
failed job's `id` and its failed step names.

**IDs are data, never shell text.** A contributor controls test names and
parameter IDs, and `$(…)` inside double quotes executes on the maintainer's
machine. Every local command below takes the ID from the script's
`failures_quoted` list verbatim — single-quoted by `shlex.quote` when it
contains anything outside `[A-Za-z0-9_@%+=:,./-]`, bare otherwise — and never
re-interpolates the bare `failures` entry into a shell string. An ID that
still looks like shell syntax after quoting is shown to the user before it
runs. The script strips GitHub's per-line timestamps
and ANSI color, detects the runner, and returns
`{"format": "pytest", "failures": [...], "failures_quoted": [...], "packages": [...]}`;
commands take IDs from `failures_quoted`. Exit 1 means no IDs were recognized — go to *No IDs* below. Force a runner with
`--format pytest|jest|vitest|cargo|nextest|go` when a log mixes tools.

## Map the CI step to a local command

Read the failed step's `run:` line in the workflow. Keep its wrapper (`uv run`,
`npx`, `pnpm`, `just`, `make`, `cargo`, `go`) and narrow the target:

| Runner | CI step looks like | Rung 0 — targeted | Rung 1 — full step |
|---|---|---|---|
| pytest | `uv run pytest` / `pytest tests` | `uv run pytest -x <id> [<id> …]` — IDs are node IDs, taken from `failures_quoted` | the `run:` line verbatim |
| jest | `npm test` / `npx jest` | `npx jest -t <quoted pattern>` — `-t` is a **regex**, so escape every metacharacter in the name first (`(`, `)`, `[`, `.`, `+`, `*`, `?`, `$`, `^`, `\|`) or a name like `parses (float)` matches nothing and Jest exits 0, a false green; then quote as `failures_quoted` does, with ` › ` replaced by a space | the `run:` line verbatim |
| vitest | `npx vitest run` | an ID is `<file> > <suite> > <name>` (or `<file>` alone for a suite that failed to load): `npx vitest run <quoted file> -t <quoted pattern>` with the last ` > ` segment as the pattern, escaped as for jest; a file-only ID runs `npx vitest run <quoted file>`. **The file is shell-quoted like every other extracted value** — a committed test filename can contain `$(…)`, which would execute here; split the ID yourself and quote each half, never paste the raw ID | the `run:` line verbatim |
| cargo | `cargo test` | `cargo test <module::tests::name> -- --exact` | the `run:` line verbatim |
| cargo-nextest | `cargo nextest run` | `cargo nextest run -E 'test(=<name>)'`; to scope a test to its binary use its own pair from `failure_pairs`, `-E 'binary_id(<id>) & test(=<name>)'` — never a binary from `packages` with a test from `failures`, because the same test name can fail in one binary and pass in another, so the cross product runs a passing test or none; several pairs join with ` \| ` inside one expression | the `run:` line verbatim |
| go | `go test ./...` | `go test <package> -run '^<TestName>$'` — for an ID with `/`, split on it and anchor each segment: `TestParent/sub` → `-run '^TestParent$/^sub$'`; `<package>` from `packages` when present, else the package of the failing file | the `run:` line verbatim |
| just / make wrapper | `just test`, `make test` | open the recipe and narrow its inner command as above; run the inner command directly at rung 0, the recipe at rung 1 | the recipe |
| lint / format / typecheck | `ruff check .`, `eslint .`, `tsc` | the tool on the files the log names (`ruff check <file>`); a typecheck has no narrower target than the project | the `run:` line verbatim |
| build | `cargo build`, `npm run build` | none — the step is the target; enter at rung 1 | the `run:` line verbatim |

Match the toolchain the red cell used: read `matrix` for the failing job's
versions and use the same interpreter or runtime locally when the machine
has it. When it does not, say so and treat the job as *not reproducible
locally* (fix from evidence, verify at rung 2).

Environment the step depends on (`env:`, `working-directory:`,
`services:`) must be reproduced or the class changes: a job that needs a
Postgres service container and none is running locally is *not reproducible
locally*, not *code or test*.

## No IDs

`extract_failures.py` exits 1 when the log has no recognizable test failure:
a compile error, a build step, a script that exited non-zero, a runner the
script does not know. The narrowest target is then the failed step's whole
`run:` command, entered at rung 1. Read the last 50 lines of the failed step
in the log for the actual error before running anything.

## Widening — rung 1, and the cap

Rung 0 green does not mean the step is green: a fix can break a neighbor
test in the same suite. Rung 1 runs the full step locally so that breakage
is found here, where it costs the step's duration, instead of in CI, where
it costs a full cycle. That is its whole value: one avoided CI cycle. It is
not a correctness gate (rung 3 is), so its cost has a ceiling.

- Expected within the cap of 10 minutes (the harness's single-command
  limit): rung 1 runs, always. The expected duration is stated (ledger
  median, else the CI step median) so the user knows what they are waiting
  for; it is information, not a question.
- Unmeasured: rung 1 runs in the background and is timed; the number goes in
  the ledger for next time.
- Expected over the cap: one AskUserQuestion carrying the number ("the whole
  `integration` step is expected to take 25m here; run it in the background
  before CI?"). Yes → background run, awaited. No → recorded as declined,
  the sweep runs, and **CI is the lab** for the remote decision, because the
  fix reaches CI verified only on its isolated tests.

A background run (over the cap, or unmeasured; no `timeout` binary exists on
macOS) is started detached and awaited, then its exit status and tail are
read from the captured log:

```bash
start=$(date +%s)
( <the run: line> > "$SCRATCH/rung1-<job>.log" 2>&1; echo "exit=$?" >> "$SCRATCH/rung1-<job>.log" ) &
# wait with the harness's background mechanism (run_in_background + the completion notification),
# not a hand-rolled poll loop; then:
tail -n 60 "$SCRATCH/rung1-<job>.log"
```

Rung 1 is unavailable only when the step cannot run here at all (toolchain,
matrix OS, `services:`, secrets): the *not reproducible locally* class.

## Timing — feed the local ledger

Every rung-1 and rung-1s command is timed, and a green run is recorded so
the next fix on this machine decides from local numbers rather than the CI
proxy (SKILL.md step 2). Rung 0 is timed for the report but never recorded:
its duration is not the step's.

```bash
LEDGER=$(python3 <skill-dir>/scripts/local_ledger.py path --repo <owner/repo>)
start=$(date +%s); <the run: line>; rc=$?; secs=$(( $(date +%s) - start ))
python3 <skill-dir>/scripts/local_ledger.py record --ledger "$LEDGER" \
  --workflow "<workflow name>" --workflow-path "<.github/workflows/file.yml>" \
  --job "<job display name>" --step "<step display name>" \
  --seconds "$secs" --conclusion "$([ "$rc" -eq 0 ] && echo success || echo failure)"
```

`record` keeps the last 10 successes per (workflow, workflow path, job, step)
and prints the
new median; a failure is reported and not stored (a red measures
time-to-failure, the same rule the CI profile applies). The step name is the
jobs API's display name, so the ledger key matches the profile's `steps`
entry and `ladder_plan.py --ledger` can prefer it. Pass `--workflow-path`
(the profile row's `workflow_path`) wherever it is known: two workflow files
can share a `name:`, and without the path one file's local median would
decide the other's rung. A query and a sample match only when their paths
match, so a ledger written before the path was known simply misses — a cache
miss, not a wrong answer. Report the local duration
beside the CI median (`rung 1: 3m10s local, CI median 9m40s`) so the reader
sees why the local decision differed from the remote one.

## The sweep (rung 1s) — every other job, locally, before every push

A fix that makes the failed step green can break a neighbor job. The sweep
finds that locally, where it costs the neighbors' measured medians, instead of
in CI, where it costs a full push cycle. It runs before **every** push, not
only the first.

**Join inventory to profile** on the pair (workflow name, job display name):
the profile row's `workflow_name` and `job` fields against the workflow's
`name` and the inventory job's `name` if set, else its `id`, else the matrix
cell's `display_name`. Never join on the profile's `name` column, which
becomes `<workflow> / <job>` when a job name repeats across workflows. An
inventory job with no profile row has never been green on the sampled runs:
treat it as `unmeasured`.

| Include a job when | Because |
|---|---|
| its class is `fast` (ledger median for its steps when known, else CI), or `slow`/`unmeasured` and the user accepted the stated time | the sweep's bound is the sum of the swept medians; unlike rung 1, a slow neighbor is a cost the user may decline, because rung 3 runs it regardless |
| it has no `container` and no `services` | those need a Linux runner, not the host |
| its `os_family` is this host's; or `linux` when the host is macOS | toolchain commands (`pytest`, `ruff`, `npm test`, `cargo test`) are portable between the two; a Windows host sweeps Windows jobs only |
| its family is not `matrix`, `unknown`, or `self-hosted` — a matrix job contributes one cell whose family and toolchain match the host, named in the report | the other cells are rung 3's job |
| it is not `external` | GitHub-managed jobs cannot be changed here |
| no step downloads an artifact (`actions/download-artifact`) or depends on a `needs:` output | it would fail locally for a reason that is not the code |

**Toolchain pre-check, before running anything.** For every sweepable step
(`kind: run`, `setup: false`, no `if:` that names an event the local run is
not, `shell` unset or a shell), take the first token of each simple command
after stripping `sudo` and `NAME=value` prefixes — skipping shell keywords
(`if`, `then`, `else`, `fi`, `for`, `do`, `done`, `case`, `esac`, `while`,
`until`), builtins (`cd`, `export`, `set`, `echo`, `test`, `[`), comments,
and operators, and looking past `&&`, `||`, `|`, and `;` for the commands
they join — and `command -v` it; check the
matrix cell's version with `<tool> --version` where the cell pins one. Any
token absent → skip the **job** with reason `toolchain: <tool>` (later steps
depend on it); it is listed as skipped in the report and first verified at
rung 3. The same holds for exit 127 mid-run.

**Run** each included job's sweepable steps in order, from the job's
`defaults_run.working_directory` or the step's own, with the merged workflow,
job, and step `env`, `${{ matrix.* }}` substituted from the chosen cell, and
`${{ inputs.* }}` / `${{ secrets.* }}` removed only when the command stays
meaningful (else skip the job, reason recorded). Skip `uses:` steps (actions,
not commands) and `setup` steps (installers that write outside the repo). A
`continue-on-error: true` step's red is not a red. Capture every job's output
to `$SCRATCH/sweep-<job>.log`, so a red yields rung-0 IDs through
`extract_failures.py`. Time each swept step and record the greens in the
ledger (*Timing* above), keyed by that job's and step's display names.

**Outcome.** All green → rung 2. Any red → a new red job: stop, triage it, fix
it at rungs 0–1, sweep again. Several red jobs are fixed locally and pushed
once. Attempt counting for a neighbor red is in `fix-loop.md`, *Attempts*.
