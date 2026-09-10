# ci-fix

Repairs failing GitHub Actions and git hooks with evidence before and after
an edit. It shares `references/validation-contract.md` with `pr-merge-flow`:
confirm or refute the claim, reproduce locally where a suitable environment
exists, verify the intended tests actually ran, then check affected behavior
and applicable required CI.

A complete compatible local validation bundle measured at approximately 30
seconds or less runs directly. Otherwise the skill starts with failing tests
or the smallest useful target and widens for a stated reason. A single fast
step or a suite below ten minutes does not require broader execution. Compatible
fixes are batched; unrelated fast jobs and broad action/hook audits are excluded
from the default repair path.

`scripts/ladder_plan.py` reports local scope and whether supplemental remote
isolation would help. A filtered dispatch preserves the runner-specific input
format and never replaces ordinary required CI. Completion reconciles expected
workflows/jobs, conditions, required-check policy, actual revision and attempts;
missing checks are not green, and legitimate conditional skips are not defects.
No skip-marker/empty-trigger-commit strategy is used.

The local Linux runner survey remains installed-first: prefer existing runners,
then images/VMs already on disk, then Podman, Lima and Docker, with the owner's
pin preserved. A runner changes the execution environment, not the verification
scope. Check architecture, toolchain, shell and services. A new start, install
or pull outside current authority needs a concrete decision; inherited approval
is honored without repeat questions.

Six scripts provide timing profiles (`ci_profile.py`), failure extraction
(`extract_failures.py`), workflow facts (`workflow_inventory.py`), scope planning
(`ladder_plan.py`), compatible timing history (`local_ledger.py`) and runner
survey (`detect_runners.py`). Inventory retains raw conditions, job environments,
tag filters and effective step context. Its validation hints require inspection;
`run` plus `setup: false` never authorizes local execution.

The version-2 timing ledger hashes a non-secret command/scope/environment
context. `record` and `median` now require `--context <json-file>`; the planner
accepts the same option and ignores ledger history without it. Legacy samples
are retained but cannot override a compatible current estimate. The helper's
`--bundle-seconds` accepts a measured total, while `--full-step-reason` states
why affected behavior needs the whole command. These helper inputs are documented
in the skill; they are not additional top-level skill modes.

Existing commit/push authority carries through a PR handoff. A repair push sends
`pr-merge-flow` back to review collection; no-change repair reruns refresh state.
The CI skill itself does not merge. Hook prevention and unrelated pin updates
remain optional; later edits get fresh verification rather than inheriting a
previous commit's readiness.

Renamed from `ci-audit` in repo-hygiene 0.9.0.

**Triggers on:** "fix CI", "CI is red", "actions broken", "audit CI",
"why is CI slow", "make CI faster", or "are my hooks running?".

**Arguments:** `--audit` reports health, `--optimize` proposes speed changes,
`--actions-only` / `--hooks-only` restrict scope, `--slow-threshold <dur>`
sets the reporting threshold (default `2m`), `--isolate-local <dur>` sets the
measured complete-bundle shortcut (default `30s`), `--isolate-remote <dur>`
sets the supplemental diagnosis threshold (default `5m`), and
`--update-versions` requests action-pin updates. Fix and optimize remain separate.

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

## Example sessions

> "Fix CI" for a narrow defect in a nine-minute test step
> → reproduce the extracted failure, repair it, verify that test and relevant
> affected behavior, then push once and reconcile required CI. Run the whole
> step only when the change or unresolved uncertainty justifies it.

> "Fix CI" where the complete appropriate local bundle is measured at 20 seconds
> → run that bundle directly; avoid a redundant isolated test pass. Preserve
> the pre-edit and post-edit evidence, then observe ordinary required CI.

> "Fix CI" for a Linux-specific failure with a suitable runner already available
> → run the selected tests in that runner, verify environment and selected IDs,
> record compatible timings, and report ordinary CI coverage for the pushed code.

> "Fix CI" with no adequate local equivalent
> → retain that limitation. When a filtered diagnostic would help, use the
> existing runner-specific input or propose the concrete required addition.
> Confirm the intended tests ran and separately establish unfiltered required CI.

> "Why is CI slow?"
> → profile requested workflows and validate optimization proposals against the
> evidence. An all-green matrix does not justify removing supported platforms;
> successful timing samples alone do not estimate gate-failure frequency.
