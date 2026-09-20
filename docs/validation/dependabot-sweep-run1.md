# dependabot-sweep pilot run 1 (2026-09-19)

Live pilot of the new skill against the first half of public `smorinlabs`
repos. Purpose: shake out subagent errors and skill-design gaps before the
second run and publication.

## Scope

Config: explicit `repos` list (first 16 of 32 public repos, alphabetical).
Flags: `auto_fix = true`, `pause_on_conflict = false`.

Half 1: agent-fork, agent2linear, claude-openrouter-launcher, cli-standards,
contributors-please, contributors-please-action, contributors-please-e2e,
contributors-please-test, difftree, difftree-action, difftree-action-test,
doxa-research, envgen, harness-kit, homebrew-tap, identikit.

## Discovery

16 per-repo `gh pr list --app dependabot` calls → 17 open PRs in 3 repos
(13 quiet, no subagent):

- doxa-research (13): #158, #157, #156, #155, #154, #153, #152, #151, #143,
  #137, #133, #131, #118
- harness-kit (2): #11, #9
- identikit (2): #4, #2

Sweep gate: user confirmed "sweep all 3 repos" live.

## Per-repo outcomes

- harness-kit: 2/2 merged (#11, #9). Verified GitHub-side.
- identikit: 2/2 merged (#4, then #2 on R1b after the first sweeper wedged).
- doxa-research R1b: 11/13 merged; #133 and #118 recorded as conflicts
  (`mergeable=null`, dirty) and deferred — both still open. Progress log holds
  all 13 result lines. Run-1 total: 15 merged, 2 deferred conflicts.

## Error log

- 10:28: doxa + identikit sweepers both wedged inside a single `gh pr merge`
  bash call that never returned; zero output for 2+ hrs (state still
  "running"). Cancelled and redispatched hardened (R1b).
- harness-kit sweeper: `gh pr checks` GraphQL `context deadline exceeded`;
  retried via REST per ci-fix — succeeded. `uv sync` failed on unwritable
  default cache; reran with `UV_CACHE_DIR=/tmp/...` — succeeded.
- R1b doxa: the 90s kill-wrapper failed silently — one `gh pr merge` ran
  61 min then exited rc=0 with the merge applied. Same run also used
  foreground `sleep 120/90/60` waits and ~20 min of review archaeology on
  patch bumps before batch-merging the remaining 9 simple PRs.
- Fresh-child probe (post-run): the wrapper DOES kill `sleep` (3.0s, rc=137)
  and network-hung `curl` in a child sandbox, and `curl --max-time` bounds a
  stalled endpoint there (rc=28, 2.0s). The 61-min escape mechanism is
  therefore still unproven — not simply "sandbox denies kill".

## Optimization candidates

- (pending R1b sweeper reports)

## Fallback gaps (errors needing a fallback plan or skill correction)

- F1: hung `gh` process with no timeout → child waits forever. Fix: brief
  mandates every `gh` call timeout-wrapped (`with-timeout.sh`, no coreutils
  on macOS), retry-once then REST fallback then needs-human.
- F2: no per-PR progress trail — a wedged child leaves nothing. Fix: append
  one result line per PR to a progress log immediately.
- F3: pending-checks behavior unspecified (wait? how long? merge?). Fix:
  bounded wait (30s poll, 10 min cap), merge only on green at bound.
- F4: mergeability assumed, never checked. Fix: REST `mergeable` check
  before merge; null = recheck, don't assume.
- F5: `UV_CACHE_DIR` needed in sandboxed environments. Fix: brief sets it.

## Learnings → skill changes

Implemented (3-way review: Muse + Codex + local reviewer; plan approved by
Codex with 6 required changes, all folded in):

- Bounded dispatcher (SKILL.md step 4): eligible-now vs deferred with
  reasons; one writer per repo; volatile-evidence refresh; post-crash
  reconcile from the progress log; bounded repair loop with
  return-to-classification; distinct report reasons.
- Hang-proof merge transport (`scripts/gh_merge.py`): every HTTP call
  natively timed out; SHA-bound PUT; effective review decision + unresolved
  threads + check-runs/statuses + mergeable + queue detection in preflight;
  definitive-vs-uncertain split with read-only reconcile and quarantine —
  never blind retry.
- Hardened brief + `[budgets]` config: merges only through the helper, no
  sleep over 30s, no review archaeology on trivials, per-PR absolute
  deadline, per-PR start/result log lines.
- Behavioral gates (`scripts/test-gh-merge.py`, 14 fixture tests green):
  timeout enforcement, eligibility matrix, ambiguous-merge reconcile with no
  duplicate PUT, head-change rejection.

Run-2 gate PASSED 2026-09-20: helper merged scratch PR
contributors-please-test#16 live in 6.5s (rc=0, verified MERGED), proving
REST/`gh` equivalence end to end. Along the way the gate caught one real
over-strict rule (top-level bot COMMENTED reviews blocked merges) — fixed to
defer only on inline comments, covered by 2 new fixture tests (16/16 green).
Probe branch and file removed afterwards.
