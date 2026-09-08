---
name: ci-fix
description: Fix failing GitHub Actions and git hooks (lefthook, pre-commit) by measuring job durations, triaging each red job, reproducing the failing tests locally, and verifying up a ladder before full CI. --audit reports only; --optimize proposes speed changes without applying them. Use when the user says "fix CI", "CI is red", "actions broken", "audit CI", "why is CI slow", "make CI faster", or "are my hooks running?". Not for merging a PR (pr-merge-flow).
argument-hint: "[--audit] [--optimize] [--actions-only|--hooks-only] [--slow-threshold <dur>] [--update-versions]"
allowed-tools: Bash, Read, Grep, Glob, Edit, Write, AskUserQuestion, Task
---

# CI fix

Get a repository's GitHub Actions and git hooks green again in the least CI
time possible, or report on their health and speed without touching anything.

> **Iron Law: every run is the narrowest one the profile allows.** Nothing is
> executed, locally or in CI, before the duration profile (step 2) exists, and
> every verification enters the ladder (step 6) at its lowest available rung
> and climbs one rung per green.
>
> No exceptions: not "it's probably quick", not "the whole suite is the only
> way to be sure", not "CI will tell us". The profile costs one REST call per
> sampled run; a 20-minute job says nothing for 20 minutes.
>
> Violating the letter of this rule is violating the spirit of it.

`<skill-dir>` below is this skill's directory, announced when the skill
loaded; the working directory is the user's repository.

## Modes and flags

| Mode | Invocation | Does | Mutates |
|---|---|---|---|
| **Fix** (default) | `/ci-fix` | Steps 1–6, 6b, 8: measure → triage → local repro and sweep → targeted CI run → full run → offer a hook → report | Repo files and commits (shown first), pushes, one dispatched workflow per iteration plus one full run |
| **Audit** | `--audit` | Steps 1–3 and 8: measure and audit, then stop | Nothing |
| **Optimize** | `--optimize` | Steps 1–2 and 7–8: measure, then a dedicated sub-agent analyzes each slow job and proposes what would make it faster | Nothing |

`--audit --optimize` produces both reports. Fix and optimize never combine: a
speed change is not a fix, and is applied only on a later explicit request.

Scoping flags, valid in every mode:

- `--actions-only` / `--hooks-only` — skip the other half.
- `--slow-threshold <dur>` — the slow-job line, default `2m` (`90s`, `1h`,
  `1h30m`, or bare seconds).

Fix-mode flag:

- `--update-versions` — after the fix, bump every `uses:` pin the audit found
  stale to its latest tag, in its own `chore(ci):` commit, verified at rung 3.
  Ignored under `--audit` and `--optimize`, where stale pins are reported. A
  pin that is itself the red cause is fixed in step 4 without this flag.

## 1. Gather context (all modes)

- Scratch space, once: `SCRATCH="${SCRATCH:-$(mktemp -d "${TMPDIR:-/tmp}/ci-fix.XXXXXX")}"`
  (use the harness scratchpad directory instead when one is announced).
- Auth and quota, measured not assumed: `gh auth status`, then
  `gh api rate_limit --jq '.resources.core.remaining'` (comfortably above 100 → proceed).
- Repo identity: `gh api "repos/{owner}/{repo}" --jq .full_name` (`gh api`
  fills `{owner}` and `{repo}` from the remote; every call in this skill is
  REST — the `gh run` porcelain rate-limits sooner).
- Workflows: `ls .github/workflows/` (or Glob `.github/workflows/*`), then the
  inventory — jobs, runner families, matrix cells with their API display
  names, containers, services, each step's display name and whether the local
  sweep may run it, and the triggers with any `workflow_dispatch` inputs:
  `uv run --no-project --with pyyaml <skill-dir>/scripts/workflow_inventory.py --json .github/workflows/*`
  (`--no-project` keeps uv away from the user's own project).
- Hooks: `ls lefthook.yml .pre-commit-config.yaml 2>/dev/null`.
- Recent runs on this branch:
  `gh api "repos/{owner}/{repo}/actions/runs?per_page=10&branch=$(git branch --show-current)" --jq '.workflow_runs[] | {id, name, conclusion, status, head_sha, created_at}'`.

## 2. Measure — the duration profile (all modes)

Sample the last 10 **successful** runs on this branch (a failed run measures
time-to-failure, not the job's shape), fetch each run's jobs, and profile them:

```bash
mkdir -p "$SCRATCH/profile"
gh api "repos/{owner}/{repo}/actions/runs?status=success&per_page=10&branch=$(git branch --show-current)" \
  > "$SCRATCH/profile/runs.json"
for id in $(python3 -c 'import json,sys; print(*[r["id"] for r in json.load(open(sys.argv[1]))["workflow_runs"]])' "$SCRATCH/profile/runs.json"); do
  gh api "repos/{owner}/{repo}/actions/runs/$id/jobs" > "$SCRATCH/profile/jobs-$id.json"
done
python3 <skill-dir>/scripts/ci_profile.py --threshold <slow-threshold> --runs "$SCRATCH/profile/runs.json" "$SCRATCH/profile"/jobs-*.json
```

Fewer than 3 successful runs on the branch → add the default branch's (drop
`&branch=`), and say so in the report. The script reports, per job, the
median and max duration, queue wait, the slowest step, a class (`slow` above
the threshold, `fast`, or `unmeasured`), and `wait_bound_s`, the data-derived
lifetime for any CI wait on that job. `--json` gives the same for the
sub-agent and for scripting. Recipe and fields: `references/duration-profile.md`.

Profile rules:

- `unmeasured` (no successful sample) is treated as `slow`.
- `external` jobs come from GitHub-managed workflows (run path under
  `dynamic/`, such as the Copilot reviewer). They are listed last and never
  fixed, swept, or optimized: the repo cannot change them.
- Matrix cells are separate jobs (`pytest (3.12)`); profile them as such.
- Never estimate a duration from the workflow file. Runtimes come from runs.

## 3. Audit (audit mode, and fix mode's first pass)

Skip parts excluded by `--actions-only` / `--hooks-only`.

- **Run status** — every failed or cancelled run in step 1's list, with its
  red jobs and their class from step 2.
- **Workflow lint** — `actionlint` from the repo root (it finds
  `.github/workflows` itself); if absent, a finding plus the platform install
  (`brew install actionlint` on macOS).
- **Action pins** — every `uses:` line against
  `gh api "repos/<owner>/<action>/releases/latest" --jq .tag_name` (one call
  per distinct action, counted in the quota check; fall back to
  `.../tags?per_page=1`). Flag an old major, and SHA-pinned vs tag-pinned.
  Report only unless fix mode with `--update-versions`.
- **Hooks** — lefthook: installed (`lefthook --version`), the hook file
  present at `"$(git rev-parse --git-path hooks)/pre-commit"` (worktree-safe;
  also report `git config core.hooksPath` when set), referenced tools resolve
  (`command -v ruff actionlint pytest …`), config complete. pre-commit:
  installed, hook `rev`s current.
- **Parity** — actionlint is itself a hook; for each CI `run:` step, a hook
  runs the same tool at the same pinned version. List every gap; fix mode's
  step 6b offers to close the one that just failed.

`--audit` writes the report (step 8) and stops. When any job is `slow` or
`unmeasured`, the report ends with the pointer:
`N job(s) over <threshold> — run /ci-fix --optimize for a job-by-job analysis.`

## 4. Triage every red job (fix mode)

Classify before fixing anything. `references/fix-loop.md` has the signals.

| Class | Looks like | Handling |
|---|---|---|
| **Workflow or config** | actionlint finding, bad `uses:`, missing permission, YAML typo, a secret name that does not exist | Edit the workflow; `actionlint <file>` locally is its rung 1. Sweep (1s) unless the edit changed no `run:` line; then push (rung 2) |
| **Code or test** | a test ID or compile error in the failed step's log | Steps 5–6, the targeted loop |
| **Flake or infrastructure** | runner lost, network timeout, the same commit green on another attempt | Rerun the failed job once on the same commit (`references/fix-loop.md`). Green → record it as a flake; do not "fix" it. Red again → treat as code or test |
| **Not reproducible locally** | needs secrets, a service container, or a matrix OS this machine lacks | No local rung **for this job**; fix from the log evidence. The sweep (1s) still runs on the neighbors; then enter CI at rung 2 |

A red **commit status** with no failing check-run (a reviewer bot reporting its
own rate limit, for example) is not CI. Say so and leave it to `pr-merge-flow`.

## 5. Localize (fix mode, code or test class)

1. The failed run's jobs and steps (`<run_id>` from step 1's list):
   `gh api "repos/{owner}/{repo}/actions/runs/<run_id>/jobs" --jq '.jobs[] | select(.conclusion=="failure") | {id, name, failed_steps: [.steps[] | select(.conclusion=="failure") | .name]}'`
2. The failed job's log:
   `gh api "repos/{owner}/{repo}/actions/jobs/<job_id>/logs" > "$SCRATCH/job-<job_id>.log"`
3. The failing test IDs:
   `python3 <skill-dir>/scripts/extract_failures.py --json "$SCRATCH/job-<job_id>.log"`
   → `{format, failures, packages}` for pytest, jest, cargo, or go. Exit 1
   means no test IDs were recognized: Grep the log for the failed step's name
   and read its last 50 lines for the actual error; the step's whole `run:`
   command is then the narrowest target.
4. Map the failed step's `run:` command to the local equivalent with
   `references/targeted-repro.md`: the same runner wrapper (`uv run`, `npx`,
   `just`, `make`), narrowed to the extracted IDs.

## 6. Reproduce, fix, and verify up the ladder (fix mode)

**Reproduce before editing.** Run the lowest available rung once, unchanged.
Red → the failure reproduces; proceed. Green → the failure depends on
environment, ordering, or toolchain: reclassify per
`references/targeted-repro.md` (matrix toolchain, `env:`, `services:`, flake)
and never edit on a hypothesis that does not reproduce. A job with no local
rung (not reproducible locally) is reproduced by the existing failed run, plus
its rerun when step 4 did one. Root-causing between reproduction and
edit is `superpowers:systematic-debugging`'s discipline.

| Rung | Runs | Where | Wait bound | Available when |
|---|---|---|---|---|
| 0 | the extracted test IDs only | local | seconds | IDs were extracted and the toolchain exists here |
| 1 | the failed step's full `run:` command | local | the step's measured median | the step runs here, and its median is under the threshold or the user accepted the stated time |
| 1s | **the sweep**: every other host-runnable job's sweepable `run:` steps (candidate rules, toolchain pre-check, and skips: `references/targeted-repro.md`, *The sweep*) | local | the sum of the swept jobs' medians | rung 1 green (or unavailable); before **every** push |
| 2 | push; when the push would start more than one repo-owned workflow and the failing one has `workflow_dispatch`, the commit carries `[skip ci]` and only that workflow is dispatched (rung 2d, `references/fix-loop.md`); otherwise watch the target job on the run the push started | CI | that job's `wait_bound_s` (the largest, when several workflows are watched) | rung 1s green |
| 3 | every job on the last pushed commit: the run the push started, or after 2d the first marker-free commit — the step-6b hook commit, the `--update-versions` commit, or an empty `ci: full run` commit | CI | the longest job's `wait_bound_s` | rung 2 green |

Rules:

- Start at the lowest **available** rung and climb one rung per green. A rung
  is unavailable only for a recorded reason: no IDs (rung 0); no local
  equivalent, or a step median over the threshold that the user did not
  accept (rung 1); no other sweepable job (rung 1s). Never skip an available
  rung, and never call one unavailable by judgment alone.
- A red in the sweep is a new red job: stop before any push, triage it, and
  fix it at rungs 0–1 before sweeping again. Several red jobs are fixed
  locally and pushed once, not once per job.
- Rung 2d is decided before the commit, from the inventory's `triggers` for
  the failing workflow: the marker goes on its own body line only when
  `workflow_dispatch` is listed. A dispatch that still fails is recovered by
  making the rung-3 commit at once and watching the target job on the run it
  starts. Mechanics and failure cases: `references/fix-loop.md`, *Rung 2d*.
- Same-commit reruns are not a rung. They serve two cases only: the flake
  check in step 4, and a neighbor job that went red at rung 3 with no code
  change of its own. Commands in `references/fix-loop.md`.
- Show the diff and confirm with AskUserQuestion before every commit and push.
- Every CI wait is bounded by the profile's `wait_bound_s` for the job being
  watched; poll REST no more often than every 20–30 seconds; an API error is
  "no data", not a state change; on expiry do one manual recheck and report.
  Pre-validate the check command once before arming any monitor.
- Three attempts per red job, counted across rungs. An attempt is one edit
  followed by a red at any rung; the original CI failure, the reproduction
  run, the single flake rerun, and the rung-3 empty commit are not attempts.
  A neighbor that goes red in the sweep or at rung 3 keeps its own counter
  when it was already red in step 4, and counts as one attempt on the job
  being fixed when it was green before the edit. The third red stops the
  loop: report what was tried, the evidence, and the best hypothesis.
- **Done** means every job on the last pushed commit is green (rung 3). A
  local green is not a fix; a rung-2 green beside a red neighbor is not done.

## 6b. Shift the failed check left (fix mode, between rung 2 and rung 3)

For a code, test, or lint failure whose check has no hook equivalent in the
step-3 parity list, offer once, with AskUserQuestion, to add it:
`references/shift-left.md` renders the hook for lefthook or pre-commit from
the failed step's command, staged as `pre-commit` when the step's median is
under the threshold and `pre-push` when it is over. On yes: show the diff (a
repo with no hook manager gets a new `lefthook.yml`), commit as
`chore(hooks): …` with no skip marker, install and run the hook once locally,
and push — that push is rung 3. On no: record the declined gap in the report;
the empty `ci: full run` commit carries rung 3. Never add a hook silently.

Then return to whatever called this skill (`pr-merge-flow` resumes its own
flow). This skill never merges.

## 7. Optimize — job-by-job speed analysis (optimize mode)

Dispatch one sub-agent with the `Task` tool (`Agent` in current Claude Code; `subagent_type: general-purpose`)
using the brief in `references/optimize.md`; its first paragraph is the
read-only constraint. Pass the step-2 profile JSON inline, and the workflow
files and the latest log of every `slow` or `unmeasured` job by path under
`$SCRATCH`. The sub-agent attributes each job's time to setup, main command,
and teardown, runs an eleven-lever checklist, and returns a ranked table:
recommendation, evidence line, estimated saving derived from the measured
step durations, effort, and a before/after sketch.

Nothing is applied. To act on an item, the user asks for it by number in a
later run, and the change is shown as a diff before commit like any fix.

## 8. Report

```
## CI report — <mode> — <owner/repo>@<branch>

### Duration profile (<N> successful runs sampled, threshold <dur>)
| class | job | median | max | queue | slowest step |
<one row per job, slowest first; unmeasured rows first>

### Run status
- ✅/❌ <workflow> — <conclusion> — red jobs: <job (class)>, …

### Findings                       (audit; fix mode's first pass)
- Lint: ✅ none / ❌ <file>:<line> — <issue>
- Pins: ✅/⚠️ <action>@<version> — latest <version>
- Hooks: ✅/❌ installed · tools resolve · parity gaps: <list>

### Fixes                          (fix mode)
- <job> — <class> — reproduced at rung <n> — <what changed> — sweep: <jobs run>, skipped <job (reason)> — CI: dispatched <workflow> / push-and-watch — ✅ every job green on <rung-3 sha> / ❌ stopped after 3 attempts: <evidence>
- Shift left: hook added for <check> (<stage>) / declined / not applicable

### Speed analysis                 (optimize mode)
| # | job | recommendation | evidence | est. saving | effort |

### Next
- <pointer to --optimize when slow jobs exist and this was not optimize mode>
- <anything left for the user: unreproducible classes, stopped loops>
```

## Red Flags

| Thought | Reality |
|---|---|
| "Small fix — push and let CI tell us" | A 20-minute job says nothing for 20 minutes. Profile, run the one test, sweep the fast jobs, then push. The full run is rung 3, not rung 0. |
| "The failed step is green, push" | The sweep is what catches the neighbor the fix broke. One local sweep costs less than one extra CI cycle. |
| "This job was never measured, so just run it" | Unmeasured is slow until a successful sample says otherwise. |
| "CI is red — fix the workflow" | Triage first. A flake is rerun, not fixed; a reviewer-bot status is not CI at all. |
| "The dispatched run is green — done" | 2d ran one workflow. Done is every workflow green on the rung-3 commit. |
| "It's green locally, so it's fixed" | Done is every job green in CI on the pushed commit. Rung 3 exists for exactly this. |

## See also

- `pr-merge-flow` — hands real build failures here and resumes after; its
  `references/polling.md` is the fuller treatment of quota-safe waiting.
- `superpowers:systematic-debugging` — root-causing between reproduction and
  edit.
- `factor-architect`, `factor-scan` — code refactoring; `--optimize` analyzes
  CI jobs only.
- `release-publishing-setup`, `repo-please-setup` — install workflows; this
  skill debugs runs.
- `references/duration-profile.md` · `references/targeted-repro.md` ·
  `references/fix-loop.md` · `references/shift-left.md` ·
  `references/optimize.md`.
