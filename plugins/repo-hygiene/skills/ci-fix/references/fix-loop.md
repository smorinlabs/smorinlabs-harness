# Fix loop — triage signals, reruns, waiting, and stopping

The loop for one red job. The ladder itself is defined once, in SKILL.md
step 6; this file carries the signals, the rerun mechanics, the polling laws,
and the stopping rule.

## Triage signals

| Class | Signals in the log or run | First action |
|---|---|---|
| **Workflow or config** | actionlint finding; `Unable to resolve action`; `Resource not accessible by integration` (permissions); YAML parse error; a step referencing a secret name that does not exist | Edit the workflow; `actionlint <file>` locally (its rung 1). The sweep (1s) is unavailable only when the edit changed no `run:` line; otherwise re-run the inventory and sweep, then push (rung 2) |
| **Code or test** | `FAILED …::…`, `● suite › test`, `---- name stdout ----`, `--- FAIL:`, a compiler error naming a file and line | SKILL.md steps 5–6: extract, map, reproduce at rung 0 |
| **Flake or infrastructure** | `The runner has received a shutdown signal`; `The hosted runner … lost communication`; a network timeout in an install step; the same `head_sha` green in another attempt (`run_attempt` > 1) | Rerun the failed job once on the same commit (below). Green → record as flake, done. Red → reclassify as code or test |
| **Not reproducible locally** | the step needs `secrets.*`, a `services:` container, a self-hosted runner label, or a matrix OS this machine lacks | Fix from the log evidence; no local rung **for this job**. The sweep (1s) still runs on the neighbors before the push; enter CI at rung 2 |

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
job of a workflow on a fresh commit. It can run one **workflow** on demand
when that workflow declares `on: workflow_dispatch`. Rung 2d uses that so a
fix iteration costs one workflow in CI, not all of them.

**When 2d applies.** Only when the push would start more than one
non-external workflow (inventory `triggers` containing `push` or
`pull_request`, minus the profile's `external` jobs' workflows). With a single
repo-owned workflow, plain push-and-watch is rung 2 and that same run, all
green, is rung 3; 2d there would add a marker commit, a dispatch, and a second
full run for nothing.

**Decide the marker before committing, from the inventory.** The working tree
you are about to push *is* the copy GitHub will evaluate (verified 2026-09-08:
a dispatch against a branch carrying the trigger while `main` did not returned
204, and the run appeared one second later). So: `workflow_dispatch` in the
failing workflow's `triggers` → commit with the marker; absent → plain rung 2,
and record `--optimize` lever 11. The POST executes; it does not decide.

`[skip ci]` anywhere in the commit message makes GitHub skip every workflow
triggered by `push` or `pull_request` for that commit (accepted markers:
`[skip ci]`, `[ci skip]`, `[no ci]`, `[skip actions]`, `[actions skip]`;
dispatched runs are unaffected — GitHub docs, "Skipping workflow runs",
verified 2026-09-08). Put it on its own body line, not in the subject, so
conventional-commit tooling (release-please lifts `fix(...)` subjects into
changelogs) reads a clean subject. That the body placement is honored is a
verify-once item for the first real 2d run.

```bash
T0=$(date -u +%Y-%m-%dT%H:%M:%SZ)                   # before the commit: a fast local clock must not miss the run
git commit -m "fix(<scope>): <what>" -m "[skip ci]"
git push -u origin "$(git branch --show-current)"
SHA=$(git rev-parse HEAD)

# dispatch only the failing workflow on this branch (204 = accepted, no body);
# every dispatch_inputs entry marked required must be passed
gh api -X POST "repos/{owner}/{repo}/actions/workflows/<file>.yml/dispatches" \
  -f ref="$(git branch --show-current)" \
  -f "inputs[<name>]=<value>"                           # one per required input; drop the line when there are none

# find the run it created: same event, same commit, created after T0
gh api "repos/{owner}/{repo}/actions/runs?event=workflow_dispatch&head_sha=$SHA&per_page=5" \
  --jq ".workflow_runs[] | select(.created_at >= \"$T0\") | {id, status, conclusion, created_at}"
```

(`gh api --jq` takes only the expression, no `--arg`; the timestamp is
inlined.) The run appears within seconds of the 204; poll the lookup under
the four laws until one matches, then watch the target job with the jobs
check below. Several failing workflows → dispatch each once on the same
commit; the wait bound is the largest `wait_bound_s` among the watched jobs.

**When the POST fails anyway.** Read the body. `does not have a
'workflow_dispatch' trigger` → the pushed copy differs from what the inventory
read (re-run it). `Required input '<name>' not provided` → pass every
required input. `404` → GitHub could not resolve the workflow file, which can
happen for a file that is new on this branch (not verified; the fallback is
the same). All three recover the same way: the pushed commit started nothing,
so make the rung-3 commit now (next paragraph) and watch the target job on
the run it starts, as plain rung 2.

**Rung 3 after 2d.** It is carried by the first marker-free commit after the
fix: `chore(hooks): …` from step 6b when the user accepted the hook offer,
`chore(ci): …` from `--update-versions`, or, when neither exists, an empty
commit: `git commit --allow-empty -m "ci: full run"`. Push it; every workflow
runs on it; done is judged on that commit, so the report's `green on <sha>`
names it, not the fix commit. Under a rebase-merge repository, confirm the
empty commit survives the merge; if it would not, the marker must not sit on
the branch's final code commit.

When the failing workflow declares a filter input (lever 11's sketch adds
`inputs.filter` wired into the test command), pass the extracted IDs through
it only when rung 1 was unavailable — a filtered dispatch is rung 0 in CI,
which pays only when the full step could not run locally.

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

A neighbor that goes red in the sweep or at rung 3 is counted by where it
came from. Already in step 4's red list → the local red is its reproduction
and it keeps its own counter. Green in CI before this edit → the red was
caused by the edit and counts as one attempt on the job being fixed. The
rung-3 empty commit is not an edit and never counts on its own.

A loop that stops with evidence is a result. A loop that keeps pushing is not.

## Done

Every job on the rung-3 commit — the last commit pushed — is
`conclusion: success`. Then return
to the caller. `pr-merge-flow` resumes its own flow from there; this skill
never merges, never touches review threads, and never tidies branches.
