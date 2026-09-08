# ci-fix

Gets a repository's GitHub Actions and git hooks (lefthook, pre-commit) green
again in the least CI time possible. Every run starts by measuring: it samples
the last successful runs through the REST jobs endpoint and profiles each
job's median duration, queue wait, and slowest step against a slow-job
threshold (default 2 minutes). In fix mode it then triages every red job
(workflow or config, code or test, flake, or not reproducible locally),
extracts the failing test IDs from the job log, reproduces the failure before
editing, and verifies up a ladder: the targeted tests locally, the full step
locally, then a push watching only the target job, then every job on that
run — each rung only after the one below is green, each CI wait bounded by
the measured duration. Done means every job is green in CI on the pushed
commit. `--audit` runs the measurement and the checks (actionlint,
Action pins, hook installation and CI/hook parity) and stops. `--optimize`
dispatches a read-only sub-agent that analyzes each slow job and returns
ranked, evidence-backed changes that would make it faster; nothing is
applied. Two bundled scripts do the measuring and the localizing:
`scripts/ci_profile.py` and `scripts/extract_failures.py`.

Renamed from `ci-audit` in repo-hygiene 0.9.0.

**Triggers on:** "fix CI", "fix GitHub actions", "actions broken", "CI is
red", "audit CI", "check actions", "why is CI slow", "make CI faster",
"speed up CI", "actionlint", "lefthook", "pre-commit hooks", "are my hooks
running?" ·
**Arguments:** `--audit` (measure and report, no changes), `--optimize`
(job-by-job speed analysis, no changes), `--actions-only` / `--hooks-only`
(skip the other half), `--slow-threshold <dur>` (slow-job line, default
`2m`), `--update-versions` (fix mode only: bump stale Action pins in their own commit)

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
> and extracts `tests/test_rollup.py::test_nested_totals`, runs that one test
> locally in two seconds and sees it fail, fixes the rollup, re-runs it green,
> asks before running the 18-minute step locally and skips it on a no, pushes,
> watches only `integration` on the new run under a 27-minute bound, then
> waits for the remaining jobs and reports every job green on the pushed
> commit.

> "Why is CI slow?"
> → `--optimize`: profiles the runs, hands the workflow files, the profile,
> and the `integration` job's log to a read-only sub-agent, and reports a
> ranked table: no dependency cache (install is 6 of the 18 minutes), no
> `needs:` gate behind the 40-second lint, no `timeout-minutes` — each with
> the evidence line and a before/after sketch, nothing applied.
