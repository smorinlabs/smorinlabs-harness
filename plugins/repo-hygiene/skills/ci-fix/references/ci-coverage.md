# Prove expected CI coverage before completion

Ordinary push/PR CI supplies the final evidence. A filtered dispatch is a
diagnostic run, even if its check label matches a required check. An empty
push can match no path filters and cannot restore omitted coverage by itself.

## Reconciliation procedure

1. **Fix the revision being evaluated.** Refresh the PR's current head and
   base. Record the source commit and the event/ref used by each run. If CI
   tests a synthetic merge revision, establish its relationship to the current
   PR head/base rather than treating an unrelated SHA as equivalent. A moving
   branch name alone is insufficient. A changed head/base invalidates affected
   readiness evidence and requires a fresh reconciliation.
2. **Build expectations independently of observed runs.** Read the applicable
   required-check policy, including branch protection and active repository or
   organization rules. Record required check names and their expected source
   application. Read repository-owned workflow definitions for the evaluated
   code: file path, event, branch/path/tag filters, job conditions, matrix and
   dependencies. Include expected validation and the failed checks being repaired.
   A success-only duration profile is not a job inventory. A permissions/API
   error reading policy is unknown policy, not an empty set of requirements.
3. **Collect complete observations.** Paginate workflow runs and each run's
   jobs; inspect required external checks/commit statuses too. Retain workflow
   file, run ID, event, actual evaluated commit, attempt, matrix-cell identity,
   conclusion, and whether test filtering was enabled. Join by workflow path
   and the resolved job/cell display name, never just a workflow display name.
   Use the latest relevant attempt; do not choose an older green attempt to
   hide a later red one. An external required check stays material even when
   `ci-fix` cannot repair its producer; return it to the appropriate caller.
4. **Classify every expected row using the table below.** Keep the reason and
   evidence for an inapplicable job. Conditions that cannot be resolved stay
   unknown when no sufficient run evidence exists. A failed prerequisite is
   not proof that a dependent validation was legitimately unnecessary.
5. **Compare the entire expected set.** Completion requires appropriate
   unfiltered success for applicable validation/required checks and justified
   inapplicability where policy permits it. No pending, missing, failed or
   unknown required evidence may be silently dropped. Separately report
   optional/non-validation failures with their policy and task relevance.
6. **Refresh before handoff and merge.** Recheck the PR revision and authoritative
   review state. Return before/after head, push state, expectations, observations
   and unresolved work to `pr-merge-flow` using `validation-contract.md`.
   The caller binds any authorized merge to its reviewed head.

| Observation | Meaning and action |
|---|---|
| Successful, unfiltered, matching revision/event/job | Satisfies that expected validation row, subject to required-check policy |
| Successful filtered diagnostic | Useful diagnosis only; locate/obtain ordinary required coverage |
| Queued/in progress or run not registered yet | Pending; wait within the existing bound |
| Expected check absent | Missing evidence; inspect trigger/condition/registration and policy, never green by omission |
| Intentionally irrelevant job skipped | Inapplicable only with the condition and policy evidence recorded |
| Job skipped because a prerequisite failed | Coverage not established; investigate the prerequisite |
| Failure/cancelled/timed out/action required/stale | Unsuccessful evidence; triage, rerun only when justified, or report the blocker |
| Neutral or tolerated failure | Inspect the check contract and policy; not automatically success or inapplicability |
| API error, incomplete pagination, unknown condition/policy | Unresolved; recover the read or state the limitation |
| Result belongs to an older/unrelated revision | Does not establish current readiness |

If a filtered diagnostic reuses a required check name, inspect both its run
identity and the unfiltered required result. The shared label alone is never
proof of coverage; do not use filtering to satisfy or weaken protection rules.

## Acceptance traces

These are instruction-level cases, not claims of live GitHub execution.

| Input state | Required decision | Completion |
|---|---|---|
| Path-filtered push was suppressed; a separate empty commit follows | Inspect missing expected workflow; the empty push does not prove coverage | No |
| Required workflow absent from the observed list | Retain it in the expected set and investigate | No |
| Matching unfiltered test success plus a deploy job irrelevant to this event | Record deploy condition/policy; accept applicable tests | Yes, if all other gates pass |
| Test job skipped after its build prerequisite failed | Repair/revalidate prerequisite and dependent coverage | No |
| Filtered diagnostic passes under the same label as a required check | Keep diagnostic separate from unfiltered evidence | No, until required coverage exists |
| Run registration delayed | Bounded wait, then one final read and explicit pending status | No |
| PR changes from A to B while a dispatch tests A | Diagnose from A if useful; establish coverage/reviews for B | No for B |
| Current synthetic merge revision maps to current PR head/base and all expected checks pass | Record that mapping and current required policy | Yes, if other gates pass |
| Policy endpoint fails but visible tests pass | Recover the policy read or report unknown requirements | No |
| Same run's earlier attempt passes and its latest relevant attempt fails | Use the latest relevant attempt and triage | No |
| All owned checks pass but an external required check remains pending | Return external gate to caller; do not edit a workflow to bypass it | No |

Primary references: [path filters and diff comparisons](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#git-diff-comparisons),
[skipping workflow runs](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/skip-workflow-runs),
and [conditional jobs](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-jobs-with-conditions).
