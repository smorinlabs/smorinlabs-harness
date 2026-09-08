# Targeted reproduction — the narrowest local command

Rung 0 of the ladder runs only the tests that failed in CI. This file maps a
failed step to that command. Extraction first, then the mapping, then the
cases where the narrowest target is the whole step.

## Extract the failing IDs

```bash
gh api "repos/{owner}/{repo}/actions/runs/<run_id>/jobs" \
  --jq '.jobs[] | select(.conclusion=="failure") | {id, name, failed_steps: [.steps[] | select(.conclusion=="failure") | .name]}'
gh api "repos/{owner}/{repo}/actions/jobs/<job_id>/logs" > "$SCRATCH/job-<job_id>.log"
python3 <skill-dir>/scripts/extract_failures.py --json "$SCRATCH/job-<job_id>.log"
```

`<run_id>` is the failed run from SKILL.md step 1; the first call yields the
failed job's `id` and its failed step names. The script strips GitHub's per-line timestamps
and ANSI color, detects the runner, and returns
`{"format": "pytest", "failures": [...], "packages": [...]}`. Exit 1 means no
IDs were recognized — go to *No IDs* below. Force a runner with
`--format pytest|jest|cargo|go` when a log mixes tools.

## Map the CI step to a local command

Read the failed step's `run:` line in the workflow. Keep its wrapper (`uv run`,
`npx`, `pnpm`, `just`, `make`, `cargo`, `go`) and narrow the target:

| Runner | CI step looks like | Rung 0 — targeted | Rung 1 — full step |
|---|---|---|---|
| pytest | `uv run pytest` / `pytest tests` | `uv run pytest -x <id> [<id> …]` — IDs are node IDs, quote ones with `[params]` | the `run:` line verbatim |
| jest / vitest | `npm test` / `npx jest` | `npx jest -t "<suite> <name>"` — Jest matches the full name with describe and test joined by single spaces, so replace the ID's ` › ` with a space (vitest: `npx vitest run -t "<name>"`) | the `run:` line verbatim |
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
