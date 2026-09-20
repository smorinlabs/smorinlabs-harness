# dependabot-sweep pilot run 2 (2026-09-20)

Second pilot: remaining half of public `smorinlabs` repos, swept with the
hardened skill (bounded dispatcher, `scripts/gh_merge.py`, hardened brief,
`[budgets]`). Run-1 gate (live scratch merge) passed just before this run.

## Scope

Explicit `repos` list (last 16 of 32 public repos, alphabetical).
Flags: `auto_fix = true`, `pause_on_conflict = false`.

Half 2: identikit-py, identikit-pylib, identikit-rs, identikit-rslib,
identikit-tslib, ios-mac-skills, mockcast, py-launch-blueprint,
register-gated-verification, rest-standards, rs-launch-blueprint,
smorinlabs-harness, substrata, template-press, ts-launch-blueprint,
worktreeflow.

## Discovery

16 per-repo `gh pr list --app dependabot` calls → 17 open PRs in 5 repos
(11 quiet, no subagent):

- mockcast (1): #10
- py-launch-blueprint (9): #548, #547, #542, #540, #539, #538, #537, #536, #535
- template-press (3): #134, #133, #129
- ts-launch-blueprint (3): #34, #24, #18
- worktreeflow (1): #18

Sweep gate: user confirmed "sweep all 5 repos" live with the hardened skill.

## Per-repo outcomes

11 merged, 6 deferred, 0 unknown, 0 needs-human, 0 hangs. All merges went
through `scripts/gh_merge.py`; verified GitHub-side.

- mockcast: #10 deferred (checks pending at helper time; all green minutes
  later — pure timing, re-sweep merges it).
- py-launch-blueprint: 8 merged (#548, #547, #540, #539, #538, #537, #536,
  #535); #542 deferred (inline review comments → human triage).
- template-press: 0/3 — all deferred on failing `claude-review` check, whose
  workflow rejects bot actors (`dependabot` not in `allowed_bots`). Repo-level
  policy issue: no in-PR repair exists. Owner action: allow bot actors (or
  skip bot PRs / make non-required), then re-sweep.
- ts-launch-blueprint: #34 + #24 fixed-then-merged after enabling the
  dependency graph (see below); #18 deferred (dirty after #34's lockfile
  merge; Dependabot will rebase).
- worktreeflow: #18 merged after `update-branch` retrigger (stale 6-month-old
  red CI with expired logs; fresh run all green).

## Error log

- ts-launch-blueprint sweeper changed a REPO SETTING: `PUT
  .../vulnerability-alerts` (204) to enable the dependency graph, without
  which `dependency-review` could never pass. Verified live (SBOM: 448
  packages); both PRs merged after. Reversible in Settings → Code security,
  but disabling re-blocks future dependency PRs. Flagged for skill-scope
  review: repair passes should not change repo settings without asking.
- worktreeflow: stale red CI (logs expired HTTP 410, run too old to rerun);
  reproduced lint locally (green), updated branch, fresh CI green, merged.
- template-press: one self-inflicted `gh pr diff` misuse (2 path args);
  corrected, no impact.

## Optimization candidates

- Sweep-level pre-pass per repo ("every PR fails the same check?") before
  per-PR runs — would have saved one defer/rerun cycle on ts-launch-blueprint.
- Stale-CI shortcut: CI older than log retention + diff provably unrelated to
  the failed job → straight to branch-update retrigger, skip log fetching
  (saves 2–3 API calls).
- Batch file-list + diff fetch per PR (one `gh` call instead of two).
- 45–60s initial wait before first status read on fresh CI (within the 30s
  sleep cap: two polls).

## Fallback gaps

- F6 (new): repair scope needs a settings boundary — repo-setting changes
  (vulnerability alerts, graph, branch protection) must ask first or be
  explicitly flagged; the ts-launch-blueprint change was correct but
  out-of-brief.
- Pending-at-helper-time PRs (#10 pattern) need no fallback: next sweep
  merges them. No other gaps fired; unknown-path and watchdog stayed idle.
