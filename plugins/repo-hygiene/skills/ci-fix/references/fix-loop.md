# Fix loop — triage signals, reruns, waiting, and stopping

The loop for one red job. The ladder itself is defined once, in SKILL.md
step 6; this file carries the signals, the rerun mechanics, the polling laws,
and the stopping rule.

## Triage signals

| Class | Signals in the log or run | First action |
|---|---|---|
| **Workflow or config** | actionlint finding; `Unable to resolve action`; `Resource not accessible by integration` (permissions); YAML parse error; a step referencing a secret name that does not exist | Edit the workflow; `actionlint <file>` locally (its rung 1); push and watch the job (rung 2) |
| **Code or test** | `FAILED …::…`, `● suite › test`, `---- name stdout ----`, `--- FAIL:`, a compiler error naming a file and line | SKILL.md steps 5–6: extract, map, reproduce at rung 0 |
| **Flake or infrastructure** | `The runner has received a shutdown signal`; `The hosted runner … lost communication`; a network timeout in an install step; the same `head_sha` green in another attempt (`run_attempt` > 1) | Rerun the failed job once on the same commit (below). Green → record as flake, done. Red → reclassify as code or test |
| **Not reproducible locally** | the step needs `secrets.*`, a `services:` container, a self-hosted runner label, or a matrix OS this machine lacks | Fix from the log evidence; no local rung is available; enter at rung 2 |

Two things that look like CI and are not:

- A red **commit status** with no failing check-run (`…/commits/{sha}/status`
  red, `…/commits/{sha}/check-runs` all green) is a bot reporting about
  itself. Say so; it is `pr-merge-flow`'s reviewer-unavailable case.
- A **cancelled** run superseded by a newer push (a workflow with
  `concurrency: cancel-in-progress`). Profile the newer run.

## Same-commit reruns

A rerun re-executes jobs on the commit that already ran. It cannot verify a
fix, because the fix is not in that commit; it serves the flake check and a
neighbor that went red at rung 3 with no code change of its own.

```bash
# one job (job id = .jobs[].id from the run's jobs JSON)
gh api -X POST "repos/{owner}/{repo}/actions/jobs/<job_id>/rerun"
# every failed job in the run, with their dependencies
gh api -X POST "repos/{owner}/{repo}/actions/runs/<run_id>/rerun-failed-jobs"
```

Porcelain equivalents: `gh run rerun --job <job_id>` (no run id with `--job`)
and `gh run rerun <run_id> --failed`. A rerun keeps the `run_id`, increments
`run_attempt`, and assigns **new job ids** — re-fetch the run's jobs before
pulling a rerun's log.

## Why CI cannot run a subset on a new commit

A push runs every workflow whose trigger matches. GitHub has no way to run one
job of a workflow on a fresh commit, which is why rung 2 is "push and watch the
target job" rather than "run the target job": CI compute is the same as rung
3; only the feedback latency differs, and a red target job ends the wait early.
The structural way to make fast jobs run *before* long ones on every push is
`needs:` gating, which is lever 3 of `--optimize`, not something this loop
does on the side.

## Waiting on CI — the four laws

Every wait in this skill obeys these; `pr-merge-flow/references/polling.md`
has the fuller treatment.

1. **Interval floor**: 20–30 seconds between calls to any GitHub endpoint.
2. **Hard bound from data**: the profile's `wait_bound_s` for the job being
   watched (rung 2) or the longest job (rung 3). On expiry: one manual
   recheck, then report. Never re-arm silently.
3. **Pre-validate**: run the check command once by hand and confirm its output
   matches every terminal state the loop keys on — every job conclusion GitHub
   can return: `success`, `failure`, `cancelled`, `skipped`, `timed_out`,
   `action_required`, `neutral`, `stale` — plus `queued`/`in_progress` for a
   job that has not finished. Anything other than `success` on the watched job
   ends the wait as red.
4. **Errors are no data**: an API error, an empty body, or a listing whose
   first run has a null `id` (the run is not registered yet) is not a state
   change and does not reset the bound.

The check, REST. The new run's id comes from the runs listing filtered by the
pushed `head_sha`:

```bash
# the target run, through the workflow-specific listing: a push that starts
# several workflows cannot hide it, and a same-named job from another
# workflow cannot be mistaken for it; keep this run_id for every later check
gh api "repos/{owner}/{repo}/actions/workflows/<file>.yml/runs?head_sha=<sha>&per_page=5" \
  --jq '.workflow_runs[0] | {id, status, conclusion}'
gh api "repos/{owner}/{repo}/actions/runs/<run_id>/jobs?per_page=100" \
  --jq '.jobs[] | select(.name == "<job>") | {status, conclusion, run_attempt}'
```

## Attempts and stopping

Three attempts per red job, counted across rungs. An attempt is one edit
followed by a red at any rung. The original CI failure, the reproduction run
before any edit, and the single flake rerun are not attempts. On the third
red, stop and report:

- the class, the rung reached, and each attempt's change and result;
- the log evidence (the failing IDs, the last error lines);
- the best remaining hypothesis and what would test it.

A loop that stops with evidence is a result. A loop that keeps pushing is not.

## Done

Every job on the pushed commit is `conclusion: success` (rung 3). Then return
to the caller. `pr-merge-flow` resumes its own flow from there; this skill
never merges, never touches review threads, and never tidies branches.
