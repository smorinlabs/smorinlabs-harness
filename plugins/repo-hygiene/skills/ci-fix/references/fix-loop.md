# Fix loop — triage signals, reruns, waiting, and stopping

The loop for one red job. The ladder itself is defined once, in SKILL.md
step 6; this file carries the signals, the rerun mechanics, the polling laws,
and the stopping rule.

## Triage signals

| Class | Signals in the log or run | First action |
|---|---|---|
| **Workflow or config** | actionlint finding; `Unable to resolve action`; `Resource not accessible by integration` (permissions); YAML parse error; a step referencing a secret name that does not exist | Validate the affected workflow with `actionlint <file>` and verify commands affected by the edit, then use ordinary CI |
| **Code or test** | `FAILED …::…`, `● suite › test`, `---- name stdout ----`, `--- FAIL:`, a compiler error naming a file and line | SKILL.md steps 5–6: extract, map, reproduce at rung 0 |
| **Flake or infrastructure** | `The runner has received a shutdown signal`; `The hosted runner … lost communication`; a network timeout in an install step; the same `head_sha` green in another attempt (`run_attempt` > 1) | Rerun the failed job once on the same commit (below). Green → record the rerun evidence, then reconcile required coverage. Red → investigate and reclassify from evidence |
| **Not reproducible locally** | the step needs `secrets.*`, a `services:` container, a self-hosted runner label, or a matrix OS this machine lacks | Inspect local runner alternatives and required context. If none is suitable, retain the limitation, verify affected local checks, and use supplemental remote diagnosis when useful |

Classify these signals before routing:

- A red **commit status** without a failing check-run may be external CI
  or a reviewer. Inspect its producer, context, description and target.
  Only an identified reviewer's own service failure belongs to
  `pr-merge-flow`'s reviewer-unavailable case. Keep any required-policy gate;
  absence from the check-runs API does not make a status optional.
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

## Supplemental targeted CI through `workflow_dispatch`

Ordinary push/PR CI remains enabled. When local reproduction is unavailable
or a discrepancy remains after local success, `ladder_plan.py` may recommend
`dispatch-filtered` for a slow/unmeasured job. Check whether the existing run
already supplies the needed diagnosis before adding a duplicate run.

The workflow must be repository-owned, present on the default branch, and
have `workflow_dispatch` in the ref being dispatched. Verify the file through
`gh api "repos/{owner}/{repo}/contents/.github/workflows/<file>?ref=<default>"`;
inspect the evaluated branch's workflow for the trigger and required inputs.
Use the exact workflow filename, including `.yml` or `.yaml`. Missing evidence
means no dispatch assumption; ordinary CI still runs.

Read the existing filter consumer. `INPUT` is its resolved input name and
`VALUE` uses that runner's grammar from `filter-input.md`, not a generic list
for every runner. Keep test/binary associations for nextest. If no suitable
input exists, propose the concrete change once when isolation would help;
a decline keeps ordinary CI. Without IDs, localize before proposing filtering.

After the authorized ordinary commit and push, record the pushed commit as
`SHA`, the branch as `BRANCH`, and the current UTC timestamp as `T0` before
this request:

```bash
gh api -X POST "repos/{owner}/{repo}/actions/workflows/<file>/dispatches" \
  -f ref="$BRANCH" -f "inputs[$INPUT]=$VALUE"
gh api --paginate "repos/{owner}/{repo}/actions/workflows/<file>/runs?event=workflow_dispatch&head_sha=$SHA&per_page=100" \
  --jq '.workflow_runs[] | {id, path, event, head_sha, created_at, run_attempt, status, conclusion}'
```

Pass all other required inputs as well. A 204 is acceptance, not completion.
Identify the run by file, event, actual commit and creation time after `T0`;
retain its ID and attempt. If another push moves the branch during dispatch,
inspect which commit actually ran and reconcile the current head. Do not use
an earlier green run simply because its branch or display name matches.

A failed POST leaves ordinary CI intact. Inspect its response: a missing
trigger requires re-reading the branch workflow; a missing required input
requires supplying it; an unresolved file/ref requires correcting identity or
using ordinary CI. Do not generate an empty commit as generic recovery.

Verify that the intended tests ran. Zero or different selected tests require
selector correction. A diagnostic success then returns to ordinary required
coverage on the evaluated code, following `ci-coverage.md`. Neither a skip
marker nor a separate empty commit is part of this repair strategy.

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
   job that has not finished. A terminal result ends polling, then the
   reconciliation table in `ci-coverage.md` determines its meaning. A legitimate
   conditional skip is not the same as a failed prerequisite or missing coverage.
4. **Errors are no data**: an API error, an empty body, or a listing whose
   first run has a null `id` (the run is not registered yet) is not a state
   change and does not reset the bound.

The check, REST. The new run's id comes from the runs listing filtered by the
pushed `head_sha`:

```bash
# the target run, through the workflow-specific listing: a push that starts
# several workflows cannot hide it, and a same-named job from another
# workflow cannot be mistaken for it; keep this run_id for every later check
gh api --paginate "repos/{owner}/{repo}/actions/workflows/<file>/runs?head_sha=<sha>&per_page=100" \
  --jq '.workflow_runs[] | {id, event, head_sha, run_attempt, status, conclusion}'
gh api --paginate "repos/{owner}/{repo}/actions/runs/<run_id>/jobs?per_page=100" \
  --jq '.jobs[] | select(.name == "<job>") | {status, conclusion, run_attempt}'
```

## Attempts and stopping

Three attempts per red job, counted across rungs. An attempt is one edit
followed by a red at any rung. The original CI failure, the reproduction run
before any edit, and the single flake rerun are not attempts. Neither are
`no-selection`, unresolved context, missing prerequisites, or other preparation
failures; correct localization/environment before assessing a code repair. On the third
red, stop and report:

- the class, the rung reached, and each attempt's change and result;
- the log evidence (the failing IDs, the last error lines);
- the best remaining hypothesis and what would test it.

An affected neighbor that goes red locally or in required CI is counted by where it
came from. Already in step 4's red list → the local red is its reproduction
and it keeps its own counter. Green in CI before this edit → the red was
caused by the edit and counts as one attempt on the job being fixed. A rerun without an edit does not consume an edit-attempt counter.

A loop that stops with evidence is a result. A loop that keeps pushing is not.

## Done

Apply `ci-coverage.md` to the complete expected set and current evaluated
revision. Report applicable successes, justified inapplicability, and any
missing, pending, failed or unknown evidence. Return the compact handoff from
`validation-contract.md`. `pr-merge-flow` refreshes reviews after a repair push;
this skill never merges, resolves review threads, or tidies branches.
