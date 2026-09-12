---
name: ci-fix
description: Fix failing GitHub Actions and git hooks (lefthook, pre-commit) by measuring job durations, triaging each red job, reproducing the failing tests locally, and verifying up a ladder before full CI. --audit reports only; --optimize proposes speed changes without applying them. Use when the user says "fix CI", "CI is red", "actions broken", "audit CI", "why is CI slow", "make CI faster", or "are my hooks running?". Not for merging a PR (pr-merge-flow).
argument-hint: "[--audit] [--optimize] [--actions-only|--hooks-only] [--slow-threshold <dur>] [--isolate-local <dur>] [--isolate-remote <dur>] [--update-versions]"
allowed-tools: Bash, Read, Grep, Glob, Edit, Write, AskUserQuestion, Task
---

# CI fix

Get a repository's GitHub Actions and git hooks green again in the least CI
time possible, or report on their health and speed without touching anything.

> **Iron Law: verify the claim and the repair with the smallest useful
> scope, and prove applicable required CI before completion.** Use
> [the shared validation contract](references/validation-contract.md).
> A complete compatible local bundle measured at approximately 30 seconds or
> less runs directly; otherwise reproduce failing tests and verify affected
> behavior. Broader runs need a reason. A successful exit without the intended
> test selection is not proof.
>
> No exceptions for an unmeasured suite, an unresolved environment, or a green
> diagnostic run with missing required checks. Violating the letter of this
> rule is violating the spirit of it.

`<skill-dir>` below is this skill's directory, announced when the skill
loaded; the working directory is the user's repository.

## Modes and flags

| Mode | Invocation | Does | Mutates |
|---|---|---|---|
| **Fix** (default) | `/ci-fix` | Gather relevant evidence → triage → reproduce → fix → verify affected behavior → reconcile required CI → report | Authorized repo edits, commits and pushes; supplemental diagnostic dispatch when useful |
| **Audit** | `--audit` | Steps 1–3 and 8: measure and audit, then stop | Nothing |
| **Optimize** | `--optimize` | Steps 1–2 and 7–8: measure, then a dedicated sub-agent analyzes each slow job and proposes what would make it faster | Nothing |

`--audit --optimize` produces both reports. Fix and optimize never combine: a
speed change is not a fix, and is applied only on a later explicit request.

Scoping flags, valid in every mode:

- `--actions-only` / `--hooks-only` — skip the other half. `--hooks-only`
  skips the run listing, the duration profile, and every CI rung: it audits
  and fixes hooks only, with nothing to wait for.
- `--slow-threshold <dur>` — the slow-job line, default `2m` (`90s`, `1h`,
  `1h30m`, or bare seconds).

Fix-mode flags:

- `--isolate-local <dur>` — complete measured local bundle shortcut,
  default `30s`. This is the total appropriate bundle, including needed
  setup, not a failed step's CI median. Above it, or when unknown, start
  with failing IDs or the smallest useful target and widen for affected behavior.
- `--isolate-remote <dur>` — supplemental remote isolation floor, default
  `5m`. When local reproduction is unavailable or a remote discrepancy
  remains, a slower/unmeasured job may justify a filtered diagnostic dispatch.
  An ordinary push still supplies required unfiltered CI.
- `--update-versions` — after the fix, bump every `uses:` pin the audit found
  stale, in its own `chore(ci):` commit, verified at rung 3. A tag pin moves
  to the floating major of the latest release (`v10`) only when the upstream
  publishes that tag, else to the exact release tag (`v10.0.1`); either way
  the tag is verified with `gh api "repos/<owner>/<repo>/git/refs/tags/<tag>"`
  before it is written (`astral-sh/setup-uv` publishes no `v10`; a pin to it
  fails at checkout). A commit-SHA pin moves to the SHA of the latest release
  and never to a mutable tag unless the user asks for that. Ignored under
  `--audit` and `--optimize`, where stale pins are reported. A pin that is
  itself the red cause is fixed in step 4 without this flag.

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
  names, job guards/environment, containers/services, effective step context,
  validation hints requiring inspection, and triggers with dispatch inputs:
  `find .github/workflows -maxdepth 1 \( -name '*.yml' -o -name '*.yaml' \) -print0 | xargs -0 -r uv run --no-project --with pyyaml <skill-dir>/scripts/workflow_inventory.py --json`
  (`--no-project` keeps uv away from the user's own project; the `find`
  passes only YAML files, and the script skips any file that is not a
  workflow with a warning rather than failing the whole inventory).
- Hooks: `ls lefthook.yml .pre-commit-config.yaml 2>/dev/null`.
- Local Linux runners, when any job's `runs-on` this host cannot satisfy:
  `python3 <skill-dir>/scripts/detect_runners.py` writes and prints
  `~/.config/ci-fix/runners.toml` — a read-only survey of what is already
  here (podman, docker, lima, act, devcontainer), ranked by readiness before
  fidelity. It starts, pulls, and installs nothing. Fields and recipes:
  `references/local-runners.md`.
- Windows diagnostics, when a Windows job needs a guest on this Mac: read
  [Windows runners](references/windows-runners.md) and survey the secret-free
  Fusion handoff with `scripts/windows_runner.py survey`. Discovery starts
  nothing and registers nothing. Fusion setup/run owns preparation and
  lifecycle; this route uses GitHub scheduling on pushed code. Preserve the
  observed architecture and Windows-image differences.
- Runs on this commit, the fix-target set — listed by `head_sha`, not by
  branch, so every workflow's run on HEAD is present however many the branch
  has:
  `gh api "repos/{owner}/{repo}/actions/runs?head_sha=$(git rev-parse HEAD)&per_page=100" --jq '.workflow_runs[] | {id, name, conclusion, status, created_at}'`.
  Recent runs on the branch, audit history only (omit `&branch=` on a
  detached HEAD, where the branch name is empty and would filter to nothing):
  `gh api "repos/{owner}/{repo}/actions/runs?per_page=10&branch=$(git branch --show-current)" --jq '.workflow_runs[] | {id, name, conclusion, status, head_sha, created_at}'`.

## 2. Measure — reuse relevant cost evidence

In fix mode, reuse a compatible profile within the repair. Fetch timings only
for failing or affected workflows when a scope or wait decision needs them;
use the workflow-specific endpoint in `references/duration-profile.md`.
The repository-wide recipe below is for audit/optimization or an initially
unknown target. Do not top up unrelated workflows before a narrow repair.
Unknown cost permits a bounded informative reproducer, not a blind full suite.


Sample the last 10 **successful** runs on this branch (a failed run measures
time-to-failure, not the job's shape), fetch each run's jobs, and profile them:

```bash
mkdir -p "$SCRATCH/profile"
b=$(git branch --show-current)                        # empty on a detached HEAD: then no branch filter
gh api "repos/{owner}/{repo}/actions/runs?status=success&per_page=10${b:+&branch=$b}" \
  > "$SCRATCH/profile/runs.json"
for id in $(python3 -c 'import json,sys; print(*[r["id"] for r in json.load(open(sys.argv[1]))["workflow_runs"]])' "$SCRATCH/profile/runs.json"); do
  gh api "repos/{owner}/{repo}/actions/runs/$id/jobs?per_page=100" > "$SCRATCH/profile/jobs-$id.json"
done
# find | xargs -r, not a glob: zero fetched runs must neither abort the shell (zsh: "no matches
# found") nor invoke the profiler with no input (GNU xargs would; -r stops it, a no-op on BSD)
find "$SCRATCH/profile" -name 'jobs-*.json' -print0 | xargs -0 -r python3 <skill-dir>/scripts/ci_profile.py --threshold <slow-threshold> --runs "$SCRATCH/profile/runs.json" --json > "$SCRATCH/profile/profile.json"
```

Zero files found → skip the script and write `{"jobs": []}` to
`$SCRATCH/profile/profile.json`: every job is `unmeasured` and the rules
below apply. A failed profiler command is a preparation failure; do not
replace its output with an empty profile or use a partial file as evidence.

The listing is branch-wide, so a busy workflow can starve an infrequent one.
The script's `runs per workflow` line says how many runs each workflow
contributed; any repository-owned workflow with fewer than 3 is topped up
from its own listing (`actions/workflows/<file>/runs`), then from the default
branch (drop `&branch=`), and the report says so. The recipe is in
`references/duration-profile.md`, *Per-workflow top-up*. The script reports,
per job, the median and max duration, queue wait, every step's median, the
slowest step, a class (`slow` above the threshold, `fast`, or `unmeasured`),
and `wait_bound_s`, the data-derived lifetime for any CI wait on that job.
`--json` gives the same for the sub-agent, for `ladder_plan.py`, and for
scripting. Recipe and fields: `references/duration-profile.md`.

Local time is measured too. Time the validation commands actually selected;
record successful results with a compatible command/scope/environment identity using
`scripts/local_ledger.py` in a machine-level ledger
(`${XDG_CACHE_HOME:-~/.cache}/ci-fix/<owner>--<repo>.json`, never in the
repo). The local decision in step 6 uses the ledger's median for the step
only when `--context` matches, and the CI step median as an estimate otherwise.
Neither establishes a measured complete-bundle shortcut. The report
names which. Recording recipe: `references/targeted-repro.md`, *Timing*.

Profile rules:

- `unmeasured` (no successful sample) is treated as `slow`.
- `external` jobs come from GitHub-managed workflows (run path under
  `dynamic/`, such as the Copilot reviewer). They are listed last and never
  fixed, swept, or optimized: the repo cannot change them. A job whose run
  was not in the listing has unknown ownership (`external: null`) and is
  treated the same way by the sweep and the optimizer; only `external:
  false` is repository-owned.
- Matrix cells are separate jobs (`pytest (3.12)`); profile them as such.
- Never estimate a duration from the workflow file. Runtimes come from runs.
- `unmeasured` jobs have no `wait_bound_s`. A CI wait on one uses the longest
  measured job's bound; with no measured job at all, 1.5 × the failed run's
  own duration for that job, stated in the report.
- An `ambiguous join` (two workflow files share a `name:` and a sampled run
  is missing from the listing) is reported `unmeasured` rather than folded
  into the wrong file's row; re-fetch the listing with the workflow-specific
  endpoint above to resolve it.

## 3. Audit requested surfaces

`--audit` runs the full applicable audit below. Fix mode inspects the failed
surface and its relevant prerequisites only; action-version comparisons run
when requested with `--update-versions` or when a pin causes the failure.
Hook checks run for hook failures/`--hooks-only` or requested prevention work.
Do not perform broad version/hook audits as a prerequisite to every repair.
Skip parts excluded by `--actions-only` / `--hooks-only`.

- **Run status** — every failed or cancelled run in step 1's list, with its
  red jobs and their class from step 2. Fix mode targets only the latest run
  per workflow in step 1's `head_sha` listing (every run on HEAD, paged at
  100); if the local checkout is behind the branch head, say so and stop. Older runs are audit
  history, never fix targets: a failure from a superseded commit must not
  drive an edit.
- **Workflow lint** — `actionlint` from the repo root (it finds
  `.github/workflows` itself); if absent, a finding plus the platform install
  (`brew install actionlint` on macOS).
- **Action pins** — every `uses:` line against
  `gh api "repos/<owner>/<repo>/releases/latest" --jq .tag_name`, where
  `<owner>/<repo>` is the first two path segments of the `uses:` value
  (`github/codeql-action/init@v4` → `github/codeql-action`); one call per
  distinct repo, counted in the quota check; fall back to
  `.../tags?per_page=1`. Skip local actions (`./…`), `docker://` images, and
  reusable workflows (`….yml@…`), which have no release to compare. Flag an
  old major, and SHA-pinned vs tag-pinned. A recommended replacement tag is
  named only after `git/refs/tags/<tag>` returns it: the floating major when
  it exists, else the exact release tag.
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
| **Workflow or config** | actionlint finding, bad `uses:`, missing permission, YAML typo, a secret name that does not exist | Edit the workflow; `actionlint <file>` locally is a relevant validation check. Verify affected commands if behavior changed, then push |
| **Code or test** | a test ID or compile error in the failed step's log | Steps 5–6, the targeted loop |
| **Flake or infrastructure** | runner lost, network timeout, the same commit green on another attempt | Rerun the failed job once on the same commit (`references/fix-loop.md`). Green → record it as a flake; do not "fix" it. Red again → inspect evidence and reclassify; do not assume the cause |
| **Not reproducible on this host** | needs secrets, a service container, or a matrix OS this machine lacks | Survey Linux runners before declaring an `ubuntu-*` job CI-only (`references/local-runners.md`). For Windows on a Mac, survey a configured Fusion guest and inspect fidelity (`references/windows-runners.md`); that path is a GitHub-scheduled diagnostic on pushed code. With no suitable environment, retain the limitation, verify affected checks that can run, and use supplemental CI diagnosis when useful. A Linux container cannot execute a Windows or macOS job |

A red **commit status** needs producer identification: external CI can use
statuses without check-runs. Inspect its context, description and target.
A reviewer reporting its own rate limit belongs to `pr-merge-flow`'s
reviewer-unavailable path; a failing CI service needs diagnosis. Either can
still be required by repository policy; preserve that gate in the handoff.

## 5. Localize (fix mode, code or test class)

1. The failed run's jobs and steps (`<run_id>` from step 1's list):
   `gh api "repos/{owner}/{repo}/actions/runs/<run_id>/jobs?per_page=100" --jq '.jobs[] | select(.conclusion=="failure") | {id, name, failed_steps: [.steps[] | select(.conclusion=="failure") | .name]}'`
2. The failed job's log (the flag is required: `gh api` refuses a body that
   contains ANSI color codes, which most test runners emit):
   `gh api --allow-escape-sequences "repos/{owner}/{repo}/actions/jobs/<job_id>/logs" > "$SCRATCH/job-<job_id>.log"`
3. The failing test IDs:
   `python3 <skill-dir>/scripts/extract_failures.py --json "$SCRATCH/job-<job_id>.log"`
   → `{format, failures, failures_quoted, packages, failure_pairs}` for
   pytest, jest, vitest, cargo, cargo-nextest, or go; local commands take IDs
   from `failures_quoted` only, and a cargo-nextest command that scopes a test
   to a binary takes both halves from one `failure_pairs` entry, never a
   binary and a test paired across entries. Exit 1
   means no test IDs were recognized: Grep the log for the failed step's name
   and read its last 50 lines for the actual error. Localize to a useful
   file/module/package/check; the full command requires a stated reason.
4. Map the failed step's `run:` command to the local equivalent with
   `references/targeted-repro.md`: the same runner wrapper (`uv run`, `npx`,
   `just`, `make`), narrowed to the extracted IDs.

## 6. Reproduce, fix, and verify affected behavior

Apply `references/validation-contract.md` and `references/targeted-repro.md`.
The local stages remain host or Linux-runner execution; a runner does not
change the evidence requirements or make a full suite mandatory. Windows in
Fusion uses the supplemental dispatch path in
[Windows runners](references/windows-runners.md), after the chosen code is
pushed. Do not represent it as a pre-push local rung or a hosted-image match.

Build the plan from facts already established:

```bash
python3 <skill-dir>/scripts/ladder_plan.py --profile "$SCRATCH/profile/profile.json" \
  --ledger "$LEDGER" --context "$SCRATCH/execution-context.json" \
  --workflow "<workflow name from inventory>" --workflow-path "<workflow file from inventory>" \
  --job "<jobs-API job name>" --step "<failed step display name>" \
  --ids <extracted count> --dispatchable|--not-dispatchable \
  --local-step|--no-local-step --ci-is-lab|--not-ci-is-lab \
  [--local-env host|container] [--filter-input <resolved input name>] \
  [--bundle-seconds <compatible measured total>] [--full-step-reason <affected behavior>]
```

These are helper inputs, established by inspecting the workflow and local
measurements. `profile.json` is the profiler's `--json` output; use
`{"jobs": []}` when no samples exist. `--context` uses the non-secret JSON
shape in `targeted-repro.md`, *Timing*. Without it, the planner ignores ledger
timings. Supply both workflow name and path from inventory even when the job
has no successful CI timing row. `--job` is the profile's `job` field when
present, otherwise the resolved inventory job/cell name, never the decorated
profile `name` column.
`--bundle-seconds` is measured on the intended environment with all necessary
setup; do not feed it a single fast step or a container estimate.
`--full-step-reason` states why the changed behavior requires the whole command.

| Local scope | Action |
|---|---|
| `bundle` | Use the complete measured fast bundle before and after the edit; no separate ID-only pass |
| `ids` | Reproduce the selected failures, fix, rerun them, then choose additional affected checks |
| `localize` | Identify the smallest useful file/module/package/check; use the full command only with a reason |
| `full-step` | Reproduce extracted IDs when available, then verify the justified full command |
| `unavailable` | Retain the limitation and diagnose in CI; run relevant checks with a suitable local equivalent |

The planner's legacy `rung_0` flag means a separate ID-only command, and
`rung_1` means full-command or bundle execution. Neither flag represents
permission to omit pre-edit reproduction or post-edit verification: rerun the
chosen scope after every relevant edit. Legacy stage 1s names affected
neighboring checks, 2 names push/optional remote diagnosis, and 3 names expected
CI coverage. In an ordinary push, stages 2 and 3 observe one run.

Rules:

- Reproduce before editing, then rerun after. Confirm intended test selection
  from runner output or supported reports. `no-selection` returns to selector
  localization; preparation failures return to environment setup. Neither is
  a passing check or a code-repair attempt.
- Identify affected checks by shared code, fixtures, configuration, dependencies
  and generated outputs. Remove duplicate commands; do not sweep unrelated fast
  jobs. Broaden only for affected behavior or unresolved uncertainty. Preserve
  compatible prior results and batch compatible fixes into one validated push.
- Long necessary validation uses the harness's background mechanism and bounded
  waits. The ten-minute foreground limit determines how to wait, not whether
  coverage is required or whether an already-authorized action needs another ask.
- Survey Linux runners before declaring no local path. Keep the installed/image
  ranking and owner pin. Respect architecture, shell, toolchain and services.
  For a start/install outside existing authority, make the concrete offer once,
  record a decline, and proceed with the appropriate remote path.
- For a Windows diagnostic, bind the trusted repository, workflow, pushed
  revision, selected tests and exact Fusion registration to the invocation
  receipt. Use fresh one-job registration and actual labels, then collect
  the matching run/job/report with `scripts/windows_runner.py`. Prove native
  architecture, non-administrator execution and selected test outcomes. An
  uncertain dispatch response resumes collection; it does not justify a
  duplicate dispatch. Follow Fusion's lifecycle operations, retaining
  failure evidence and requiring a real admission barrier before shutdown.
- After local success use an ordinary push. `dispatch-filtered` is supplemental
  diagnosis on the same pushed code when CI is the lab and isolation pays;
  preserve the runner-specific `INPUT`/`VALUE` formats in `filter-input.md`.
  `offer-filter` proposes the concrete needed workflow change once. A decline
  keeps ordinary CI. Never use `[skip ci]` or an empty commit as a generic
  strategy to restore required coverage.
- Show the relevant diff and inherit current-session commit/push authority.
  Ask only for a new action outside that scope or an explicit owner decision.
- Three unsuccessful repair attempts per red job, with the counting and
  preparation exclusions in `references/fix-loop.md`. Stop with evidence at
  the bound. A local/remote discrepancy needs investigation; it does not prove
  that the environment is the cause.
- Before completion, reconcile expected applicable workflows/jobs and required
  checks using `references/ci-coverage.md`. Missing evidence is not green, and
  an intentionally inapplicable job is not a repair target.

Return the shared handoff record: before/after commit, push and coverage status,
verification evidence/limitations and inherited mode. A changed PR head returns
`pr-merge-flow` to review collection; an unchanged head refreshes relevant state.
One-pass reports later findings without a new triage pass and never merges.

## 6b. Optional prevention work

`references/shift-left.md` describes adding the failed check as a hook. If
already requested, prepare the hook before the planned validation and push.
Otherwise report the relevant proposal after repair completion. Do not put an
optional hook decision between observing the target job and completing the same
CI run. An accepted later change gets fresh validation, CI and review refresh.
This skill never merges.

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

Report only the surfaces actually inspected. Name the mode, repository, evaluated
commit and duration evidence. In fix mode include the compact record from
`validation-contract.md`: claim/verdict, pre/post-edit evidence, selected tests,
additional affected checks and why, execution environment and measured/estimated
cost, repair commit/push status, expected CI coverage and unresolved work.
Do not present an omitted broad audit as passed.

Audit mode adds lint, action-pin, hook-installation and parity findings.
Optimize mode adds the ranked evidence/savings table from `optimize.md`.
Optional prevention proposals appear after repair status, with accepted/declined
state. Name any stopped loop and the evidence needed to continue. A slow-job
pointer to `--optimize` is a proposal, not a required extra phase.

## Red Flags

| Thought | Reality |
|---|---|
| "Each job is under 30 seconds, so run everything" | Measure the complete local bundle, including necessary preparation |
| "The whole step is under ten minutes, so it must run" | Full scope needs an affected-behavior reason; duration controls waiting |
| "Exit 0 means the selected test passed" | Prove the intended selection; zero or different tests do not verify the fix |
| "A ready Linux runner proves CI equivalence" | Verify relevant shell, architecture, toolchain, services and skipped tests |
| "Filtered CI is green, so done" | Reconcile applicable required coverage for the evaluated commit |
| "An empty commit restores every workflow" | Push path filters may match no files; preserve ordinary CI instead |

## See also

- `pr-merge-flow` — review collection and merge readiness after the handoff.
- `references/validation-contract.md` — shared evidence, scope and authority.
- `references/ci-coverage.md` — expected-check reconciliation and acceptance cases.
- `references/duration-profile.md` · `references/targeted-repro.md` ·
  `references/fix-loop.md` · `references/filter-input.md` ·
  `references/local-runners.md` · `references/windows-runners.md` · `references/shift-left.md` ·
  `references/optimize.md`.
- `superpowers:systematic-debugging` — root-cause diagnosis.
- `factor-architect`, `factor-scan` — code refactoring rather than CI optimization.
- `release-publishing-setup`, `repo-please-setup` — workflow installation.
