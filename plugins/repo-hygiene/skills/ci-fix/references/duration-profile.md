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
b=$(git branch --show-current)                        # empty on a detached HEAD: then no branch filter
gh api "repos/{owner}/{repo}/actions/runs?status=success&per_page=10${b:+&branch=$b}" \
  > "$SCRATCH/profile/runs.json"
for id in $(python3 -c 'import json,sys; print(*[r["id"] for r in json.load(open(sys.argv[1]))["workflow_runs"]])' "$SCRATCH/profile/runs.json"); do
  gh api "repos/{owner}/{repo}/actions/runs/$id/jobs?per_page=100" > "$SCRATCH/profile/jobs-$id.json"
done
```

The listing is kept: `--runs` joins each job to its workflow `path`, which is
how GitHub-managed workflows (`dynamic/…`, such as the Copilot reviewer) are
told apart from the repo's own.

One request per sampled run: eleven calls including the listing.
`per_page=100` matters: the jobs endpoint pages at 30 by default, and a
matrix larger than that would lose cells silently; the script warns when a
run's `total_count` exceeds the jobs it holds.

### Per-workflow top-up

A repo with several workflows shares the ten among them, and a busy one can
starve an infrequent one into `unmeasured`. The script's `runs per workflow`
line (JSON: `runs_per_workflow`) shows the split. For every repository-owned
workflow file in the inventory with fewer than 3 sampled runs, fetch its own
listing and its runs, then merge the listings so `--runs` still knows every
run's path:

```bash
for wf in <each workflow basename from the inventory with fewer than 3 runs>; do
  gh api "repos/{owner}/{repo}/actions/workflows/$wf/runs?status=success&per_page=10${b:+&branch=$b}" \
    > "$SCRATCH/profile/runs-$wf.json"
  for id in $(python3 -c 'import json,sys; print(*[r["id"] for r in json.load(open(sys.argv[1]))["workflow_runs"]])' "$SCRATCH/profile/runs-$wf.json"); do
    [ -f "$SCRATCH/profile/jobs-$id.json" ] || gh api "repos/{owner}/{repo}/actions/runs/$id/jobs?per_page=100" > "$SCRATCH/profile/jobs-$id.json"
  done
done
# merge every listing into runs.json, one entry per run id
python3 - "$SCRATCH/profile" <<'PY'
import glob, json, os, sys
d = sys.argv[1]; seen = {}
for f in [os.path.join(d, "runs.json")] + sorted(glob.glob(os.path.join(d, "runs-*.json"))):
    for r in json.load(open(f))["workflow_runs"]:
        seen.setdefault(r["id"], r)
json.dump({"workflow_runs": list(seen.values())}, open(os.path.join(d, "runs.json"), "w"))
PY
```

Still fewer than 3 for that workflow on the branch → repeat its fetch without
`&branch=` (the default branch's runs), and the report names the workflow
and the sample it ended up with. The per-workflow endpoint also resolves an
`ambiguous join` (two files sharing one `name:`, below), because every run
it returns carries its `path`.

## Profile

```bash
# find | xargs -r, not a bare glob: zero fetched runs must neither abort the shell under zsh
# nor invoke the profiler with no input (-r: GNU stops, BSD/macOS never ran it anyway)
find "$SCRATCH/profile" -name 'jobs-*.json' -print0 | xargs -0 -r python3 <skill-dir>/scripts/ci_profile.py --threshold <slow-threshold> --runs "$SCRATCH/profile/runs.json"          # table
find "$SCRATCH/profile" -name 'jobs-*.json' -print0 | xargs -0 -r python3 <skill-dir>/scripts/ci_profile.py --threshold <slow-threshold> --runs "$SCRATCH/profile/runs.json" --json   # for --optimize
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
| `external`, `workflow_path` | `true` when the run's `path` is under `dynamic/`: a GitHub-managed job, listed last, never fixed, swept, or optimized |
| `samples`, `in_progress`, `excluded` | only jobs with conclusion `success` are samples; still-running jobs are listed, not measured; failed and timed-out jobs (time-to-failure, e.g. under `continue-on-error`), skipped (0s), and cancelled (truncated) are excluded |

Jobs sort slowest first; `unmeasured` rows sort to the top so they are never
overlooked.

## Rules

- **Fewer than 3 successful runs for a workflow** (`runs_per_workflow`) →
  top it up from its own listing, then from the default branch, and state
  the sample size per workflow in the report. One sample is a measurement;
  zero is not.
- **Two workflow files with the same `name:`** stay two rows once `--runs`
  supplies their paths (`<file> / <job>` in the table). A sampled run that
  the listing does not cover cannot be attributed to either file: its jobs
  are an `ambiguous join`, reported `unmeasured` and named in the output.
  The per-workflow fetch above resolves it.
- **Zero successful runs anywhere** → skip the script (an empty glob aborts
  under zsh and the script refuses no input): every job is `unmeasured`, rung 1
  needs the user's acceptance, and a CI wait is bounded by 1.5 × the failed
  run's own duration for that job.
- **A job that has never been green is absent, not `unmeasured`** — success-only
  sampling never sees it. The inventory is the complete job list; an
  inventory job with no profile row is `unmeasured` (`targeted-repro.md`,
  *Join inventory to profile*).
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
| Fix mode, the sweep (rung 1s) | `class` per job: `fast` jobs are swept; `slow` only when the user accepts; `external` never |
| Fix mode, the entry rung (`ladder_plan.py`) | the failed step's own median in `steps`, overridden by the local ledger's median when one exists, against `--isolate-local` (30s): under it → enter at rung 1 (no rung 0); over it or unmeasured → rung 0 first, then rung 1. Rung 1 itself is gated only by the 10-minute cap (a question, once), never by this floor |
| Fix mode, the remote mode (`ladder_plan.py`) | the target job's `median_s` against `--isolate-remote` (5m), and only when CI is the lab: over it or unmeasured → dispatch with the failing IDs in the filter input; anything else → plain push (rung 2 = rung 3). The profile's `class` (against `--slow-threshold`) is not this decision: it drives the sweep, the report, and the `--optimize` pointer |
| Fix mode, CI waits | `wait_bound_s` of the job being watched (rung 2) or of the longest job (rung 3) |
| Audit report | the whole table, plus the `--optimize` pointer when any job is not `fast` |
| Optimize sub-agent | the `--json` output: `steps` per job tell it where the time goes |

## The local ledger

CI time is a proxy for local time; the two diverge with hardware, caches, and
service containers. `scripts/local_ledger.py` keeps the last 10 successful
local durations per (workflow, job, step) at
`${XDG_CACHE_HOME:-~/.cache}/ci-fix/<owner>--<repo>.json` (`path --repo` prints
it; never inside the repo). `record` is called after every rung-1 and
rung-1s run (`targeted-repro.md`, *Timing*); `median` and
`ladder_plan.py --ledger` read it. On a machine's first fix of a step there
is no local sample, the CI step median decides, and the report says
`(CI proxy)`; from the second fix on it says `(ledger, n samples)`.
