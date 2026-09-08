# Targeted reproduction — the narrowest local command

Rung 0 of the ladder runs only the tests that failed in CI. This file maps a
failed step to that command. Extraction first, then the mapping, then the
cases where the narrowest target is the whole step.

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
`--format pytest|jest|cargo|go` when a log mixes tools.

## Map the CI step to a local command

Read the failed step's `run:` line in the workflow. Keep its wrapper (`uv run`,
`npx`, `pnpm`, `just`, `make`, `cargo`, `go`) and narrow the target:

| Runner | CI step looks like | Rung 0 — targeted | Rung 1 — full step |
|---|---|---|---|
| pytest | `uv run pytest` / `pytest tests` | `uv run pytest -x <id> [<id> …]` — IDs are node IDs, taken from `failures_quoted` | the `run:` line verbatim |
| jest / vitest | `npm test` / `npx jest` | `npx jest -t <quoted pattern>` — `-t` is a **regex**, so escape every metacharacter in the name first (`(`, `)`, `[`, `.`, `+`, `*`, `?`, `$`, `^`, `|`) or a name like `parses (float)` matches nothing and Jest exits 0, a false green; then quote as `failures_quoted` does, with ` › ` replaced by a space. vitest: `npx vitest run -t <quoted pattern>`, same rule; note the extractor reads Jest's log shape, so vitest and cargo-nextest IDs are read from the log by hand until their shapes are added | the `run:` line verbatim |
| cargo | `cargo test` | `cargo test <module::tests::name> -- --exact` (nextest: `cargo nextest run -E 'test(=<name>)'`) | the `run:` line verbatim |
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

## Widening

Rung 0 green does not mean the step is green: a fix can break a neighbor. Rung
1 runs the full step locally. It is available when the step's own median (the
profile's `steps`) is under the threshold, or when it is over and the user
accepted the stated time. A 25-minute suite the user declined makes rung 1
unavailable for a recorded reason; the next rung is 2, push and watch the job.

## The sweep (rung 1s) — every other job, locally, before every push

A fix that makes the failed step green can break a neighbor job. The sweep
finds that locally, where it costs the neighbors' measured medians, instead of
in CI, where it costs a full push cycle. It runs before **every** push, not
only the first.

**Join inventory to profile** by the API display name: the job's `name` if
set, else its `id`, else the matrix cell's `display_name`. An inventory job
with no profile row has never been green on the sampled runs: treat it as
`unmeasured`.

| Include a job when | Because |
|---|---|
| its class is `fast`, or `slow`/`unmeasured` and the user accepted the stated time | the sweep's bound is the sum of the swept medians |
| it has no `container` and no `services` | those need a Linux runner, not the host |
| its `os_family` is this host's; or `linux` when the host is macOS | toolchain commands (`pytest`, `ruff`, `npm test`, `cargo test`) are portable between the two; a Windows host sweeps Windows jobs only |
| its family is not `matrix`, `unknown`, or `self-hosted` — a matrix job contributes one cell whose family and toolchain match the host, named in the report | the other cells are rung 3's job |
| it is not `external` | GitHub-managed jobs cannot be changed here |
| no step downloads an artifact (`actions/download-artifact`) or depends on a `needs:` output | it would fail locally for a reason that is not the code |

**Toolchain pre-check, before running anything.** For every sweepable step
(`kind: run`, `setup: false`, no `if:` that names an event the local run is
not, `shell` unset or a shell), take the first token of each line after
stripping `sudo` and `NAME=value` prefixes, and `command -v` it; check the
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
`extract_failures.py`.

**Outcome.** All green → rung 2. Any red → a new red job: stop, triage it, fix
it at rungs 0–1, sweep again. Several red jobs are fixed locally and pushed
once. Attempt counting for a neighbor red is in `fix-loop.md`, *Attempts*.
