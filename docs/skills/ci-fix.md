# ci-fix

Gets a repository's GitHub Actions and git hooks (lefthook, pre-commit) green
again in the least CI time possible. Every run starts by measuring: it samples
the last successful runs through the REST jobs endpoint and profiles each
job's median duration, queue wait, and slowest step against a slow-job
threshold (default 2 minutes). In fix mode it then triages every red job
(workflow or config, code or test, flake, or not reproducible locally),
extracts the failing test IDs from the job log, reproduces the failure before
editing, and verifies up a ladder: the targeted tests locally, the full step
locally, a local sweep of every other fast job's commands, then CI. One
heuristic with two floors decides how narrow each level runs, computed by
`scripts/ladder_plan.py` from the measurement, because isolating costs
seconds locally and minutes in CI. Locally, a failed step expected over 30
seconds (`--isolate-local`) runs its failing tests first and the whole step
follows; a shorter one runs whole. The whole step always runs when expected
within 10 minutes, and is asked about once above that. In CI, the fix is a
plain push, one run that is both the targeted check and the full run,
unless CI is the only place the failure can be seen (not reproducible
locally, the long local step declined, or CI red again after a local green)
and the job is expected over 5 minutes (`--isolate-remote`): then the fix
is pushed with `[skip ci]` and only that workflow is dispatched carrying
just the failing tests through a filter input, with a one-time offer to add
the input when the workflow lacks one, and the full run follows. Each rung
runs only after the one below is green, and each CI wait is bounded by the
measured duration. Local runs are timed too and kept in a machine-level
ledger, so later fixes on the same machine decide from local numbers rather
than CI's. A Linux job this host cannot run directly is not automatically a
CI-only failure: the skill surveys what is already on the machine that could
run it (Podman, Docker, Lima, act), ranks by what is already running rather
than by what is most faithful, and runs the same rungs there. Nothing is
started, pulled, or installed without asking, and a machine with none of
them is told the one easiest thing to install rather than the best one. Done means every job is green in CI on the pushed commit.
After that, the skill offers once to add the failed check as a lefthook or
pre-commit hook, staged by its measured duration, so the same failure never
reaches CI again. `--audit` runs the measurement and the checks (actionlint,
Action pins, hook installation and CI/hook parity) and stops. `--optimize`
dispatches a read-only sub-agent that analyzes each slow job and returns
ranked, evidence-backed changes that would make it faster; nothing is
applied. Six bundled scripts do the measuring, the localizing, the reading
of workflow files, the planning, and the local timing: `scripts/ci_profile.py`,
`scripts/extract_failures.py` (pytest, jest, vitest, cargo, cargo-nextest,
go), `scripts/workflow_inventory.py` (run with `uv run --no-project --with
pyyaml`), `scripts/ladder_plan.py`, `scripts/local_ledger.py`, and
`scripts/detect_runners.py`.

Renamed from `ci-audit` in repo-hygiene 0.9.0.

**Triggers on:** "fix CI", "fix GitHub actions", "actions broken", "CI is
red", "audit CI", "check actions", "why is CI slow", "make CI faster",
"speed up CI", "actionlint", "lefthook", "pre-commit hooks", "are my hooks
running?" ·
**Arguments:** `--audit` (measure and report, no changes), `--optimize`
(job-by-job speed analysis, no changes), `--actions-only` / `--hooks-only`
(skip the other half), `--slow-threshold <dur>` (slow-job line, default
`2m`), `--isolate-local <dur>` / `--isolate-remote <dur>` (fix mode: the
isolation floors, default `30s` and `5m`), `--update-versions` (fix mode
only: bump stale Action pins in their own commit)

## Install

| Mode | When | How |
|---|---|---|
| Plugin (recommended) | Just use it | `/plugin install repo-hygiene@smorinlabs-harness` |
| Dev symlink | Tweak/iterate | `git clone https://github.com/smorinlabs/smorinlabs-harness` then `ln -s "$(pwd)/smorinlabs-harness/plugins/repo-hygiene/skills/ci-fix" ~/.claude/skills/ci-fix` |
| Direct copy | No marketplace access | copy `plugins/repo-hygiene/skills/ci-fix/` into `~/.claude/skills/` |

**Codex:** register the marketplace in `~/.codex/config.toml`
(`[marketplaces.smorinlabs-harness]`, source_type local) and enable the
plugin — or dev-symlink into `~/.agents/skills` (Codex's current skills
location) as well.

## Example session

> "Fix CI"
> → profiles the last ten successful runs (the `integration` job runs 18
> minutes, the rest under a minute), finds `integration` red, pulls its log
> and extracts `tests/test_rollup.py::test_nested_totals`. The plan says: the
> step is expected at 9 minutes here, over the 30-second floor, so the one
> test first; the whole step is under the 10-minute cap, so it runs
> afterwards without asking. It runs that one test locally in two seconds
> and sees it fail, fixes the rollup, re-runs it green, runs the whole
> integration step locally (9m10s, recorded for next time), sweeps the lint
> and typecheck jobs in 40 seconds, and — verified locally, so one CI round
> expected — pushes plainly and watches `integration` under a 27-minute
> bound. That run is the full run: every job green, done, and a pre-push
> hook offered for the test that failed.

> "Fix CI" when the red job is Linux-only and a container runtime is running
> → the survey finds Podman already up, so the failing test runs in it in
> nine seconds, the whole step follows, and the fix reaches CI verified —
> one plain push, no dispatch. The report names the runner, why it was
> picked ("already running"), and that the run was emulated to `linux/amd64`
> because the host is arm64.

> "Fix CI" when the red job is Linux-only and nothing local can run it
> → not reproducible on this host and the one install offer was declined, so
> CI is the lab; the `integration` job is
> expected at 18 minutes, over the 5-minute remote floor, and its workflow
> has no filter input: one question to add it (rendered from
> `references/filter-input.md`), then the fix commit carries the input and
> `[skip ci]`, only `integration` is dispatched with that one test, feedback
> arrives in three minutes instead of eighteen, and the empty `ci: full
> run` commit proves an empty input still runs the whole suite.

> "Fix CI" on a repo whose slowest step takes 20 seconds
> → under the local floor: the whole failing step runs locally (no isolated
> test), the sweep follows, and one plain push is both the targeted run and
> the full run — no marker, no dispatch, no second commit.

> "Why is CI slow?"
> → `--optimize`: profiles the runs, hands the workflow files, the profile,
> and the `integration` job's log to a read-only sub-agent, and reports a
> ranked table: no dependency cache (install is 6 of the 18 minutes), no
> `needs:` gate behind the 40-second lint, no `timeout-minutes` — each with
> the evidence line and a before/after sketch, nothing applied.
