# Duration profile — measure before you run

The profile is the Iron Law's evidence. Every other decision in ci-fix (which
rung to enter, how long to wait on CI, which jobs the optimizer inspects) reads
from it. It is built from completed runs, never estimated from workflow text.

## Fetch

`gh api` resolves `{owner}` and `{repo}` from the current repository's remote.
Every call below is REST; nothing here touches GraphQL.

```bash
# quota preflight — proceed only when comfortably above ~100
gh api rate_limit --jq '.resources.core.remaining'

SCRATCH="${SCRATCH:-$(mktemp -d "${TMPDIR:-/tmp}/ci-fix.XXXXXX")}"
mkdir -p "$SCRATCH/profile"
# last 10 successful runs on this branch — a failed run measures time-to-failure,
# not the job's shape; drop &branch= to fall back to the whole repo
for id in $(gh api "repos/{owner}/{repo}/actions/runs?status=success&per_page=10&branch=$(git branch --show-current)" \
              --jq '.workflow_runs[].id'); do
  gh api "repos/{owner}/{repo}/actions/runs/$id/jobs?per_page=100" > "$SCRATCH/profile/jobs-$id.json"
done
```

One request per sampled run: eleven calls including the listing.
`per_page=100` matters: the jobs endpoint pages at 30 by default, and a
matrix larger than that would lose cells silently; the script warns when a
run's `total_count` exceeds the jobs it holds. A repo with
several workflows shares the ten among them; scope to one workflow with
`repos/{owner}/{repo}/actions/workflows/<file>.yml/runs?status=success&per_page=10`.

## Profile

```bash
python3 <skill-dir>/scripts/ci_profile.py --threshold <slow-threshold> "$SCRATCH/profile"/jobs-*.json          # table
python3 <skill-dir>/scripts/ci_profile.py --threshold <slow-threshold> --json "$SCRATCH/profile"/jobs-*.json   # for --optimize
```

Per job the script reports:

| Field | Meaning |
|---|---|
| `median_s`, `max_s` | `completed_at − started_at` across completed samples |
| `queue_median_s` | `started_at − created_at`: time waiting for a runner, kept separate from run time |
| `class` | `slow` when `median_s` exceeds the threshold, `fast` otherwise, `unmeasured` when no sample completed |
| `slowest_step` | the step with the highest median across samples — where the time goes |
| `wait_bound_s` | `ceil(1.5 × (median + queue))`, floor 60s: the lifetime of any CI wait on this job; `null` for `unmeasured` |
| `job`, `workflow_name` | jobs are keyed by both, so `test` in two workflows stays two rows; `name` shows `<workflow> / <job>` only when bare names collide |
| `samples`, `in_progress`, `excluded` | successful samples counted; still-running jobs are listed, not measured; skipped (0s) and cancelled (truncated) jobs are excluded |

Jobs sort slowest first; `unmeasured` rows sort to the top so they are never
overlooked.

## Rules

- **Fewer than 3 successful runs on the branch** → add the default branch's
  runs and state the sample size in the report. One sample is a measurement;
  zero is not.
- **`unmeasured` is `slow`.** A job with no successful sample (always
  cancelled or skipped, new in this branch, only in-progress) gets the slow
  treatment: rung 0 and 1 locally before any CI run, and the longest measured
  job's `wait_bound_s` as its wait.
- **Every job unmeasured** (no successful run anywhere) → there is no measured
  bound. Rung 2 still runs, bounded by 1.5 × the failed run's own duration for
  the job being watched, and the report says the bound is not from a
  successful sample. Never wait unbounded.
- **Matrix cells are jobs.** `pytest (3.12)` and `pytest (3.13)` profile
  separately. When only one cell is red, target that cell's toolchain locally.
- **A cache hit and a cache miss are both samples.** The median absorbs one
  miss; `max_s` shows it. A wide gap between the two is itself an `--optimize`
  finding.
- **Re-profile after a fix lands** only when the fix touched the workflow or
  the test command; a code fix does not change the job's shape.
- **Threshold is a flag, not a constant.** `--slow-threshold 10s` makes a fast
  repo exercise the slow path; that is how the skill's own slow-path test runs
  against a repo whose CI finishes in seconds.

## How the numbers are used

| Consumer | Reads |
|---|---|
| Fix mode, rung 1 availability | the failed step's own median in `steps`: under the threshold → rung 1 is available at no stated cost; over it → available only when the user accepts the stated time |
| Fix mode, CI waits | `wait_bound_s` of the job being watched (rung 2) or of the longest job (rung 3) |
| Audit report | the whole table, plus the `--optimize` pointer when any job is not `fast` |
| Optimize sub-agent | the `--json` output: `steps` per job tell it where the time goes |
