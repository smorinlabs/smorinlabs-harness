# Optimize — the job speed analysis sub-agent

`--optimize` looks at each slow job, works out where its time goes, and
proposes what would make it faster. It is analysis: nothing is applied. The
work is delegated to one read-only sub-agent so the analysis is thorough
without loading every workflow and log into the main session.

## Dispatch

Use the `Task` tool with `subagent_type: general-purpose`; the brief's first
paragraph is the read-only constraint (there is no read-only agent type — the
restriction is stated, as the fleet does elsewhere). Hand it, verbatim, the
brief below plus three inputs — the first inline, the other two by path,
because logs run to thousands of lines:

1. the profile, inline: the `--json` output of
   `python3 <skill-dir>/scripts/ci_profile.py` (step 2);
2. every file under `.github/workflows/`, by path;
3. the latest log of each `slow` or `unmeasured` job, by path:
   `gh api --allow-escape-sequences "repos/{owner}/{repo}/actions/jobs/<job_id>/logs" > "$SCRATCH/job-<job_id>.log"`.

Only jobs classed `slow` or `unmeasured` are analyzed. Fast jobs are listed in
the report as already under threshold.

## The brief

> You are analyzing GitHub Actions jobs for speed. You may read files and run
> read-only commands. You must not edit any file or run anything that changes
> repository, workflow, or CI state.
>
> Inputs: a duration profile (JSON; per job: median/max seconds, queue wait,
> per-step medians), the workflow files, and the latest log of each slow job.
>
> For every job classed `slow` or `unmeasured`, do the following in order:
>
> 1. **Attribute the time.** From the profile's `steps`, split the job's median
>    into setup (checkout, toolchain setup, dependency install), the main
>    command, and teardown. State the split in seconds.
> 2. **Run the checklist below** against the job's YAML and log. For each item
>    that applies, record the evidence line (file:line or a quoted log line),
>    the estimated saving in seconds derived from the step timings, and an
>    effort of S/M/L.
> 3. **Sketch each change** as a before/after YAML or command fragment, minimal
>    and copy-pasteable.
>
> Rank all items across jobs by `estimated_saving / effort` and return a table
> with columns: `#`, job, recommendation, evidence, estimated saving, effort,
> sketch. Then one paragraph per job naming its single biggest lever. Say
> plainly when a job has no meaningful lever.

## Checklist

| # | Lever | Detect | Sketch |
|---|---|---|---|
| 1 | **Dependency cache absent or missing** | no `cache:` on `setup-node`/`setup-python`/`setup-uv`/`setup-go`, no `actions/cache`; or the log shows `Cache not found` / a full install every run; install step median dominates | `with: cache: 'npm'` / `enable-cache: true`; `actions/cache` keyed on the lockfile hash |
| 2 | **No `concurrency` cancel** | superseded pushes run to completion; several runs per `head_branch` in the listing | block form (an expression cannot sit inside a flow mapping): `concurrency:` / `  group: ${{ github.workflow }}-${{ github.ref }}` / `  cancel-in-progress: true` |
| 3 | **Fast jobs do not gate slow ones** | a 20-minute suite starts in parallel with a 30-second lint that fails first | `needs: [lint, typecheck]` on the long job: it never starts when a gate is red. Cost: the gate's duration lands on the critical path of every green run — worth it when gates fail often |
| 4 | **No path filters** | docs-only or config-only commits run the full suite | `on.push.paths` / `paths-ignore` for `docs/**`, `*.md` |
| 5 | **No fail-fast in the test command** | the log keeps running long after the first failure; `pytest` without `-x`/`--maxfail`; `fail-fast: false` on a matrix with no stated reason | `pytest -x --maxfail=5`; drop `fail-fast: false` unless every cell's result is needed |
| 6 | **Unsharded or serial suite** | one long test step; no `-n`/`--shard`; sequential steps that share no state | `pytest -n auto` (xdist), `jest --shard=1/4` across a matrix, `cargo nextest`, or split into parallel jobs |
| 7 | **Redundant work** | the same checkout+install+check in several jobs; every matrix cell repeating a non-matrix step (lint, build) | hoist shared steps into one job and pass artifacts, or run the non-matrix step once |
| 8 | **Setup dominates** | setup + install > 50% of the job's median | a cached toolchain, a prebuilt container image, `actions/checkout` with `fetch-depth: 1`, drop unneeded `submodules`/`lfs` |
| 9 | **No `timeout-minutes`** | absent on the job; the default is 360 | `timeout-minutes:` at roughly 2 × `max_s` |
| 10 | **Runner or matrix oversized** | a macOS or large runner for a job that is pure CPU-light; matrix dimensions that never differ in outcome | `ubuntu-latest`; prune cells that have been green in lockstep across the sampled runs |
| 11 | **No `workflow_dispatch` on a slow workflow** | the workflow's `on:` lacks `workflow_dispatch`; every fix iteration therefore runs every workflow | block form: `on:` / `  workflow_dispatch:` / `    inputs:` / `      filter: {description: test filter, required: false, default: ""}`, and the test step reading it (`pytest ${{ inputs.filter }}`), so ci-fix's rung 2d runs this workflow alone and, with the filter, only the failing tests |

Estimated savings are derived, never invented: item 1's saving is the install
step's median; item 3's is the long job's median multiplied by the fraction
of sampled runs where a fast job was red; item 6's is the main step's median
times `1 − 1/shards`; item 11's saving per fix iteration is the sum of the
*other* repo-owned workflows' longest-job medians. When a number cannot be derived from the inputs, say
"not measurable from these runs" instead of guessing.

## Output handling

The main session prints the sub-agent's table under *Speed analysis* in the
report (SKILL.md step 8), unchanged, and adds the *Next* line:
"To apply an item, ask for it by number; it will be shown as a diff before
commit." Nothing in `--optimize` mode writes to the repository.
