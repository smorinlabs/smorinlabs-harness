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

## Rung 2d — the targeted CI run through `workflow_dispatch`

A push starts every workflow whose trigger matches, and GitHub cannot run one
job of a workflow on a fresh commit. It can run one **workflow** on demand,
when that workflow declares `on: workflow_dispatch`. Rung 2d uses that so a
fix iteration costs one workflow in CI, not all of them; the full run happens
once, at rung 3.

`[skip ci]` in the commit subject makes GitHub skip every workflow triggered
by `push` or `pull_request` for that commit; the other accepted markers are
`[ci skip]`, `[no ci]`, `[skip actions]`, `[actions skip]`. Dispatched runs
are unaffected (GitHub docs, "Skipping workflow runs", verified 2026-09-08).
Use `[skip ci]` in the subject, consistently.

```bash
# 1. commit the fix so the push starts nothing, and push
git commit -m "fix(<scope>): <what> [skip ci]"
git push -u origin "$(git branch --show-current)"
SHA=$(git rev-parse HEAD); T0=$(date -u +%Y-%m-%dT%H:%M:%SZ)

# 2. dispatch only the failing workflow on this branch (204 = accepted, no body)
gh api -X POST "repos/{owner}/{repo}/actions/workflows/<file>.yml/dispatches" \
  -f ref="$(git branch --show-current)"            # -f "inputs[filter]=<expr>" when the workflow declares inputs

# 3. find the run it created: same event, same commit, created after the dispatch
gh api "repos/{owner}/{repo}/actions/runs?event=workflow_dispatch&head_sha=$SHA&per_page=5" \
  --jq --arg t0 "$T0" '.workflow_runs[] | select(.created_at >= $t0) | {id, status, conclusion, created_at}'
```

The run appears a few seconds after the 204; poll step 3 under the four laws
below until one run matches, then watch the target job on it with the jobs
check. A `422` from step 2 saying the workflow does not have a
`workflow_dispatch` trigger means the trigger is absent on this branch: fall
back to push-and-watch (rung 2 without `d`) and record `--optimize` lever 11.
Always attempt the POST rather than reading the local file — the copy GitHub
evaluates is the one on the ref you pass, and only the API answers for it.

Rung 3 after 2d: `git commit --allow-empty -m "ci: full run"` and push. The
empty commit carries no marker, so every workflow runs on it. Done is judged
on that commit.

When the failing workflow declares a filter input (lever 11's sketch adds
`inputs.filter` wired into the test command), pass the extracted IDs through
it so even the dispatched run is targeted.

## Waiting on CI — the four laws

Every wait in this skill obeys these; `pr-merge-flow/references/polling.md`
has the fuller treatment.

1. **Interval floor**: 20–30 seconds between calls to any GitHub endpoint.
2. **Hard bound from data**: the profile's `wait_bound_s` for the job being
   watched (rung 2) or the longest job (rung 3). On expiry: one manual
   recheck, then report. Never re-arm silently.
3. **Pre-validate**: run the check command once by hand and confirm its output
   matches every terminal state the loop keys on (`success`, `failure`,
   `cancelled`, and `queued`/`in_progress` for a job that has not started).
4. **Errors are no data**: an API error or empty body is not a state change
   and does not reset the bound.

The check, REST. The new run's id comes from the runs listing filtered by the
pushed `head_sha`:

```bash
gh api "repos/{owner}/{repo}/actions/runs?head_sha=<sha>&per_page=5" \
  --jq '.workflow_runs[] | {id, name, status, conclusion}'
gh api "repos/{owner}/{repo}/actions/runs/<run_id>/jobs" \
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
