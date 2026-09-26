# clear-decision-communication 0.5.0 (P55): single-source parity check

P55 restructured the skill so every rule has one home. It was scoped as a pure
restructuring, so the test was behavioral parity: the same 25 scenarios from
`evals/evals.json`, run in fresh sessions on the unchanged skill and on the
refactor, then graded blind.

## Method

- Runs: `evals/run_evals.py --tool claude --timeout 300 --run`, 2026-09-26.
  Baseline: main at `3c3e82c` (skill 0.4.0, SKILL.md sha256 `4db69361bff8...`).
  Refactor: branch `refactor/cdc-single-source` (SKILL.md sha256 `8208c5be7f60...`).
  All 50 processes completed; none timed out.
- Grading: 50 responses shuffled into anonymous packets. Ten independent
  Sonnet graders each received five packets: the prompt, raw inputs, final
  response, and that case's `review.json` expectations, with no indication of
  which skill version produced the response. A packet passes only when every
  expectation is met and the response makes no material claim its inputs do
  not support.
- Rule: every baseline pass must still pass; a pass->fail is investigated as a
  wording dependency, never re-rolled. One sample per case per run.

## Results

Baseline 23/25, refactor 24/25.

| Case | Name | Baseline | Refactor | Change |
|---|---|---|---|---|
| 1 | approved-docs-update | pass 3/3 | pass 3/3 | same |
| 2 | overnight-vendor-setting | pass 3/3 | pass 3/3 | same |
| 3 | parked-cleanup-window | pass 3/3 | pass 3/3 | same |
| 4 | late-export-reply | fail 3/3 | pass 3/3 | fail->pass |
| 5 | lease-release-review | pass 3/3 | fail 3/3 | pass->fail |
| 6 | private-invoice-address | pass 4/4 | pass 4/4 | same |
| 7 | verified-export-filename | pass 3/3 | pass 3/3 | same |
| 8 | internal-preview-format | pass 3/3 | pass 3/3 | same |
| 9 | cache-warmer-timing | pass 4/4 | pass 4/4 | same |
| 10 | migration-cutover-choice | pass 5/5 | pass 5/5 | same |
| 11 | release-environment-reply | fail 2/3 | pass 3/3 | fail->pass |
| 12 | export-memory-answer | pass 4/4 | pass 4/4 | same |
| 13 | verified-merge-interaction | pass 4/4 | pass 4/4 | same |
| 14 | repository-automation-assets | pass 5/5 | pass 5/5 | same |
| 15 | stock-dashboard-context-return | pass 5/5 | pass 5/5 | same |
| 16 | release-direction-approval | pass 4/4 | pass 4/4 | same |
| 17 | workflow-confusion-followup | pass 5/5 | pass 5/5 | same |
| 18 | credential-detection-replaces-switches | pass 5/5 | pass 5/5 | same |
| 19 | workflow-permission-simplification | pass 6/6 | pass 6/6 | same |
| 20 | export-benchmark-opposing-metrics | pass 5/5 | pass 5/5 | same |
| 21 | reported-percentage-missing-absolutes | pass 5/5 | pass 5/5 | same |
| 22 | workflow-measured-usage-and-author-gates | pass 5/5 | pass 5/5 | same |
| 23 | development-tool-policy-and-registry-evidence | pass 7/7 | pass 7/7 | same |
| 24 | missing-setup-artifact-and-role | pass 3/3 | pass 3/3 | same |
| 25 | superseded-lettered-option-reply | pass 3/3 | pass 3/3 | same |

## Differences

- Case 4, baseline fail: the response said the user chose background workers
  under Q4 before the benchmark existed; the input says the choice was deferred
  and the Q4.A reply came after the benchmark. Refactor passed.
- Case 11, baseline fail: "I'm deploying the verified rc17 build to staging
  now", a present-tense claim of an action the simulation forbids performing.
  Refactor passed.
- Case 5, refactor fail: "I'm running it now on revision 8e24a61", the same
  class of slip as baseline case 11, later contradicted by "I haven't run it in
  this response". The baseline response said "My next step is to run".

Case 5 is attributed to a pre-existing gap, not to the restructuring: neither
skill version has a rule against stating an unperformed action as in progress,
the baseline shows the same failure in case 11, and both case 5 runs worked
from `SKILL.md` without reading the moved references. Follow-up: P56.

## Reference reads

The refactor moves rules into references behind "read X at step N" pointers.
Cases that opened at least one reference: baseline 17/25, refactor 22/25.
`references/evidence.md` was read in 10 refactor cases.

## Limits

One sample per case per run, Claude CLI only (Codex not run). A single
pass/fail difference is within sampling variation; the parity claim rests on
22/25 identical verdicts plus the attribution above, not on the net score.
