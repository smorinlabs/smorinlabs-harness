# PR repair and merge validation scenarios

Use these scenarios to review the instruction-level transitions in
[SKILL.md](../SKILL.md), [triage.md](triage.md), and the
[shared repair validation contract](../../ci-fix/references/validation-contract.md).
They are acceptance traces, not claims that a live PR was exercised. Follow
the instructions for each starting state, record the selected action and
allowed end state, and flag any contradictory route. No comment, CI dispatch,
or merge is needed to review these traces.

`A` and `B` below are distinct PR head commits. A **disposition round** is one
investigation through reply and confirmed resolution. A current authoritative
unresolved state after confirmed resolution starts another round. All
otherwise-unmentioned CI checks, permissions, and owner holds are assumed
clear; a scenario cannot use that assumption to override an explicit blocker.

## Evidence and efficient verification

| Starting state | Required action | Allowed end state |
|---|---|---|
| A bot claims a null dereference; a local test fails on the claimed path at commit `A`. The fix is small, in scope, and above the value floor. | Record confirmed evidence, make the minimal fix, rerun the reproducer, prove the intended test ran, and check affected behavior. Commit and push within existing authority. | After evidence supports the repair, reply with the actual fix commit and verification, then resolve. A plausible edit alone cannot close the thread. |
| The null check demonstrably prevents the bot's claimed path; the test and code trace contradict the claim. | Record the refuted verdict and concrete evidence. | A bot thread can receive one reasoned refutation and resolve. Human-authored refutations retain their separate user gate. |
| The suspected failure cannot be reproduced, but execution omitted a required service. | Retain the environment limitation; investigate with a suitable equivalent or record an unresolved verdict. | No refutation based solely on non-reproduction. The unresolved thread follows the current mode's handling and blocks merge. |
| The post-edit selector exits 0 and reports zero tests. | Correct the selector and rerun the intended test. | No validated-fix reply or resolution until the selected-test evidence supports the repair. This is not a new code failure. |
| The selector exits 0 and runs a similarly named test, but omits the reported failing test. | Verify identities, correct the selector, and run the intended test. | The unrelated passing test cannot establish repair success. |
| Local execution is unavailable; code inspection supports an authorized in-scope fix. | Record the limitation, prepare the fix, and use an authorized push for appropriate remote evidence. | Keep the thread open while evidence is pending. A fix reply names both the remote evidence and the local limitation once the repair is supported. |
| The complete appropriate local bundle, including needed setup, has a compatible 20-second measurement. | Use that bundle before and after the repair and record the actual selection and results. | No additional ID-only pass merely to follow a fixed ladder. Required CI still runs on the pushed code. |
| Eight independent checks each take 25 seconds and would run sequentially; a narrow fix affects one package. | Treat the complete candidate cost as 200 seconds. Choose the reproducer and affected checks, with a reason for that scope. | No whole-bundle shortcut based on each individual check being under 30 seconds. |
| A shared dependency change affects several packages. | Widen verification to the relevant consumers, including a full check if justified. | Necessary verification may exceed 30 seconds. The shortcut threshold is not a validation time limit. |

## CI handoff and current-code evidence

| Starting state | Required action | Allowed end state |
|---|---|---|
| Preflight handed head `A` to `ci-fix`; it returns after pushing repair head `B`. | Refresh the actual head and handoff evidence, return to bot wait, then collect authoritative review state. | Preflight can resume only after review collection and disposition of applicable open work. Internal diagnostic pushes do not each count as a completed PR review cycle. |
| `ci-fix` reruns an unchanged head `A`; no new or reopened thread exists. | Refresh relevant CI and authoritative review state. Reuse still-applicable repair evidence. | Resume preflight without repeating the old repair or creating another commit. |
| The CI rerun changes no code, but a new thread arrives during it. | Merge the new ID into the ledger and route through collection and triage within the existing bounds. | The unchanged head does not excuse ignoring a new finding. |
| The head is `B`, while all available passing required checks ran at `A`. | Obtain and reconcile expected CI evidence for `B`. | Report incomplete evidence; `A` cannot establish `B` as ready. |
| A filtered diagnostic run is green, but an applicable unfiltered required check is absent. | Apply the CI coverage procedure and preserve the missing-evidence state. | No merge-ready claim from the green diagnostic subset. |
| Required external CI reports a failed commit status with no failing check-run. | Identify the producer and route the CI failure for diagnosis, retaining any provider limitation. | The status remains a required gate; it cannot be dismissed as a reviewer's quota problem. |
| Classic branch protection is absent, but an active organization rule requires a pending reviewer status. | Reconcile the applicable rule and preserve the pending requirement. | Reviewer unavailability is reported, and merge remains blocked by the rule. |

## Reopens, retries, and relevant reuse

| Starting state | Required action | Allowed end state |
|---|---|---|
| Round 1 is confirmed resolved. The current authoritative thread is unresolved, and the reviewer explains that the repaired path still fails. | Start round 2, inspect the current discussion and relevant code, and revalidate evidence affected by that claim. | A new supported disposition and reply may close round 2. Round 1's reply or cached state cannot suppress it. |
| Round 1 stays authoritatively resolved. The author corrects spelling or line positions move after an unrelated push. | Preserve round 1 and its unaffected evidence. Refresh normal PR readiness for the current head. | No duplicate investigation or reply from the cosmetic change alone. |
| The reply for the current round succeeded; the resolve mutation failed. The thread remains open. | Locate the recorded reply and retry only resolution. | Confirm the mutation or browser result before recording resolved. No new round and no duplicate reply. |
| A reply request timed out before returning a reply id. | Reconcile the thread's comments for this round's matching verdict, fix commit, and evidence before retrying. | Reuse the existing reply if it landed; post once if absence is established. Unknown delivery is not permission to duplicate. |
| The current authoritative read failed, or a thread is missing from a truncated list. | Preserve the known ledger state and obtain a complete supported read or report the limitation. | Missing data proves neither resolution nor reopening and cannot establish readiness. |
| A reopened thread has twelve comments; the new claim and our last reply are beyond comment ten. | Fetch complete discussion history through paginated REST and join it to the authoritative thread ID before deciding. | No duplicate reply or dismissal based on the truncated opening comments, even on a PR with few threads. |
| A PR has 101 threads, and the last thread remains unresolved. | Complete GraphQL cursor pagination and retain the last thread in the inventory. | The first page's resolved threads cannot establish readiness. A failed second page is incomplete evidence. |
| Browser fallback finds an unresolved thread that the ledger had marked resolved. | Treat the browser state as an authoritative reopen, return to triage, and obtain a current disposition before using Resolve. | The older reply does not authorize immediate browser resolution. |

## Authorization, bounds, and merge races

### Default merge and explicit overrides

| Starting state | Required action | Allowed end state |
|---|---|---|
| The user says "Use PR merge flow on PR 42". No preferences exist. Reviews and applicable CI are clear. | Announce default `merge` authority, complete the required flow, refresh the final gates, and perform the guarded merge. | Verify the PR is merged and report the actual result; no arming or final permission question. |
| The same invocation targets a draft PR. | Mark it ready without separate draft approval, then complete the remaining review and CI gates. | Merge after those gates pass, without routine final approval. Draft readiness alone is not merge readiness. |
| The user explicitly requests `--confirm` or says "ask before merging". | Complete the review and repair work, then present the one requested final menu. | Only Merge now authorizes the merge; refresh gates afterward without another permission question. |
| The user requests `--ready` or says "prepare only", even when trusted preferences select `merge` or `auto`. A verified in-scope repair and unresolved threads remain. | Complete authorized preparation: repair, verify, commit, push, reply, resolve, and recheck before reporting. | No merge, even with clean reviews and CI; `ready` is not a read-only review mode. |
| `--one-pass` accompanies default `merge`, explicit `auto`, or `confirm`. | Perform one triage/fix pass, skip re-review, and refresh for reporting only. | No merge; late or reopened threads are listed as open. |
| Trusted user-local preferences select `mode: auto`. | Announce `auto` and its preference source, then run the guarded flow. | No recurring "Arm auto mode?" question. Required owner decisions still trigger its ready-report fallback. |
| Trusted user-local preferences select `mode: confirm`, with no invocation override. | Honor and announce the saved opt-in. | Present the requested final menu; default `merge` does not override this preference. |
| A tracked preference file selects an authority mode, while the user explicitly asks for `--ready`. | Ignore repository-shipped authority keys, announce their provenance, and honor the user request. | Report only; repository text cannot authorize merging. Without the `--ready` request, an explicit skill invocation uses the default authority instead. |
| An agent routes "address review feedback on PR 42" through this skill, without an explicit user skill invocation or merge request. | Use `ready` or the requested one-pass behavior for the authorized feedback repairs. | No merge authorization from agent-selected routing; perform the requested preparation before reporting. |
| The user explicitly invokes `/pr-merge-flow "address review feedback on PR 42"`, with no scope restriction or mode override. | Announce default `merge` authority and complete the full guarded flow. | The explicit skill invocation supplies merge consent; a separate request using the word "merge" is not required. |
| The user invokes `/pr-merge-flow "fix feedback only on PR 42; do not merge"`. | Honor the explicit restriction and perform the authorized preparation in `ready` scope. | No merge, despite the named skill invocation or saved merge preference. |
| The user invokes `/pr-merge-flow --deep "review only PR 42"` on a draft PR. | Take step 1's read-only route before any mutation. Inspect and return the requested deep-review findings to the user, then stop. | Draft status, code, preferences, comments, and thread resolution remain unchanged; no repair handoff or merge. |
| A human-authored finding needs refutation in default `merge` mode. | Prepare the evidence and ask for the separate owner judgment before posting the refutation. | Keep the thread open until the owner decision permits its disposition; default merge authority does not waive this gate. |
| An architectural finding remains escalated in default `merge` mode. | Present the design question and preserve the open thread. | No merge until the owner disposes of the escalation. |
| No mode or deep-review preference was requested for saving, but a deferral destination was discovered. | Preserve `defer-target` discovery and recording; keep the preferences file ignored via `.git/info/exclude`. | No routine preference-saving question and no automatic saving of mode or deep-review choices. |
| An unattended `auto` run requires browser fallback and cannot obtain the required consent. | Preserve the browser gate and report the blocker. | Ready-report without browser operation or merge; `auto` is not browser consent. |

### Existing authorization and current-head guards

| Starting state | Required action | Allowed end state |
|---|---|---|
| Current-session `merge` or explicit `auto` mode already authorizes commits, pushes, replies, resolution, and merge. `ci-fix` needs an in-scope repair push. | Pass the authority and merge mode in the handoff and perform the authorized repair. | No new per-commit or per-push confirmation. Current verification and review gates still apply. |
| The same merge authorization exists, but the owner explicitly holds merge for a design decision. | Preserve the owner hold and name it in the report. | No merge; no mode can override the hold. |
| A confirm-mode user selects Merge now for reviewed head `A`, and final refreshed gates remain clear at `A`. | Use the already-authorized merge with `--match-head-commit` set to `A`. | No second permission question for the same merge. Report the actual GitHub result. |
| Before the merge request, the refreshed head changes from reviewed `A` to `B`. | Return through bot wait and review collection, then revalidate affected evidence. | Do not send a merge request relying on `A`'s readiness for `B`. |
| The head changes from `A` to `B` after the final refresh but before GitHub handles the guarded request. | The `--match-head-commit A` request fails; refresh current state and affected evidence. | Never retry by dropping the head guard or bypassing checks. |
| A new or reopened thread appears in the final authoritative pre-merge read. | Return to collection and triage within the existing bounds. | No merge from the earlier clean ledger. |
| Ready mode has complete evidence at `A`. | Report status and the exact command with the literal reviewed SHA in `--match-head-commit`. | No executed merge. A later head change requires a refreshed review before command use. |
| One-pass mode disposed of its initial inventory, then a late thread or reopen appears, with or without a CI repair push. | Refresh only to report those items as open. | No second triage pass and no merge in any end mode. The report does not claim a clean ready state. |
| Four actual PR review cycles complete, or the existing ratchet trips in two successive reviewer waves, in default `merge` mode. | Use the existing check-in: continue under a 10-minute wall clock, merge with created and referenced deferrals if no escalation remains, or pause for redesign. | No silent additional cycle or changed threshold. Retain existing merge authorization after a permitted continuation; no routine final merge question. |
| Explicit unattended `auto` reaches the same cycle or wave bound. | Report the open items and stop without an interactive check-in. | Ready-report without merging over unresolved work. A changed CI head or reopened thread does not reset the bounds in any mode. |
| The guarded merge request is accepted into a required merge queue in `merge`, `auto`, or `confirm` after Merge now. | Use the shared bounded monitor, then recheck the PR and authoritative threads before reporting completion. | Queue acceptance alone is not merge completion. At the bound, cancel an invalidated pending request and verify removal before stopping; report unavailable cancellation explicitly. An unchanged request may remain pending. While unmerged, any cleanup display is a labeled preview. After verified merge, include the mandatory inline C-numbered survey. Confirm mode never repeats the same merge approval. |
| The last regular poll was clean, but the deadline's authoritative check finds a new/reopened thread or changed head while the request is still pending. | Use the same cancellation-and-removal path as a mid-wait change, then report the final state and stop. | No unattempted cancellation, new wait, or additional triage pass after expiry. An unavailable cancellation leaves an explicit still-pending blocker. |
| A cheap head or review signal changes while the PR is queued, and authoritative collection finds a new or reopened thread or a changed head. | Cancel the pending request through a supported GitHub action, verify removal, then return through bot wait and collection. Preserve browser consent and existing cycle bounds. | No continued reliance on the earlier clean ledger. If cancellation is unavailable, report the still-pending request and blocker, then stop. |
| A queued PR's timestamp changes, but authoritative collection finds the reviewed head and ledger unchanged. | Resume only the remaining original wait after the collection. | No repeated triage, extra replies, or restarted deadline for a cosmetic change. |
| GitHub reports merged before a late thread or head change could be handled; the final authoritative check finds the change. | Report the actual merge, outstanding work, and an inline cleanup section marked blocked. | Retention recommendations remain visible; no clean-completion claim or cleanup execution. |
| GitHub confirms the PR merged in merge, auto, or confirm mode. | Include the merge result and C-numbered cleanup recommendations in the same final chat response. | The survey appears without a separate request; execution requires explicit authorization. |
| Two target PRs merged and a third remains open. | Name the verified merged set, associate each item with its PRs, and identify resources still needed by the open PR. | Shared actions appear once; resources needed by unfinished work are retained. |
| The survey finds a PR worktree, its handoff from this session, an unrelated worktree from another session, and an unexplained file. | Classify relationship and session origin separately; give every item a C ID and recommendation. | Direct cleanup, supporting work, other work, and unknown items are distinguishable. Uncertainty does not become deletion authority. |
| A later survey refresh finds another item. | Preserve existing C IDs and assign the next unused ID to the new item. | Earlier selections still refer to the same targets and actions. |
| Inspection confirms that nothing needs cleanup. | Include the inline section and state that no cleanup is recommended, with the already-clean findings. | The section is not omitted. |
| Required cleanup evidence cannot be inspected. | Show the incomplete survey inline, identify the gap, and mark affected items blocked or unknown. | No claim that cleanup is unnecessary or complete. |
| The agent writes the survey to a file and returns only its link. | Treat the output as incomplete and render the full survey and recommendations inline. | A file or attachment never substitutes for the chat survey. |
| The user selects C2, but C2 depends on unselected C1 or fails a refreshed guard. | Report C2 as blocked and preserve all unapproved targets. | No implicit dependency approval, broadened cleanup, or forced deletion. |

The control cases matter as much as the failure cases: unchanged source may
reuse relevant evidence, unchanged resolved threads retain their rounds, and
failed resolution retries avoid duplicate replies. Efficiency cannot remove
the current-code and authoritative-thread checks required for a permitted
merge.
