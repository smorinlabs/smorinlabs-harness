# dependabot-sweep 0.17.0 validation

This release adds executable, durable coordination to the Dependabot sweep.
The proof combines regression tests, independent review, native loading, and
one approved live dependency merge. A single live PR does not establish every
repair or merge-queue path; those paths retain fixture coverage and their
existing approval and readiness requirements.

## Implementation and regression evidence

The four implementation slices cover the JSONL record store and replay,
repository leases, readiness evaluation, worker briefs, failure diagnosis,
bounded execution, configuration, observation, and the orchestration CLI.

Pre-pilot reviews reproduced and corrected these defects:

| Defect | Verified correction |
| --- | --- |
| Network signatures could override matched baseline evidence | Matched controls take precedence; unmatched failures retain environment classification |
| A helper queue refusal looked like successful enqueueing | The literal refusal records a blocked executor disagreement and requires fresh policy evidence |
| A fresh technical failure after an approval hold stranded the attempt | The state table permits a waiting or blocked hold, while rejecting direct owner-hold-to-merged claims |
| Successful-check evidence included skipped checks | Successful and skipped counts are separate |
| The helper could adopt a head newer than classification or approval | A dedicated wrapper requires the full approved head and refuses mismatch before issuing a merge request |
| Run creation lost owner-specific permission restrictions | Per-repository permissions are saved and survive replay and later config edits; missing new-format entries fail closed |
| The permission correction accidentally restricted explicit repository selection | Explicit inventory selection remains supported while matching owner behavior restrictions still apply |

The original `gh_merge.py` transport is unchanged. Its standalone test script
passed all 24 cases. Independent wrapper probes confirmed that mismatched heads
issue no merge request, matching heads remain pinned, and original deadline and
exit semantics remain intact.

Independent CLI probes covered original failure inputs, mixed org/user scopes,
separate-process replay, later config changes, mode and conflict flags, legacy
flat stores, missing repository entries, human reports, and reviewer contexts.
Claude 2.1.283 and Codex 0.145.0 native loading passed, including a refresh
after the review corrections. Native loading checks availability, not
behavior; the tests and live proof below supply behavioral evidence.

## Implementation PR review

[PR 87](https://github.com/smorinlabs/smorinlabs-harness/pull/87) identified
additional recovery and permission defects after the pilot checkpoint.
Regression tests reproduced each finding before correction.

| Defect | Verified correction |
| --- | --- |
| Creation could publish an empty selected scope before its cards | Scope, cards, saved authority, and deadline commit in one transaction |
| A crash after claiming a repository left an unrecoverable lock | Only protocol-marked claims without a matching committed lease can be recovered under the store lock |
| Stale coordinators could collect old results or reuse IDs | Decisions refresh inside serialized transactions; collection requires current holder, session, and attempt generation |
| A torn final append prevented replay | Preceding transactions replay with a warning; a locked writer preserves and removes the uncommitted tail; malformed committed records fail |
| Heartbeat silence allowed takeover while delegates might still mutate | Foreign attempts remain protected until their worker and delegates are explicitly confirmed stopped |
| An unattributed commit status could satisfy a producer-specific required check | A matching check-run producer is required |
| Delegation could lose an earlier helper deadline | Both inherited deadline variables and the offered deadline are capped to their minimum |
| Evaluated heads were lost and replacement approvals were hidden | READY and identity-verified hold outcomes transfer their head; stale approvals are revoked; both approval formats include linked replacements |

Independent composition review then found and reproduced five additional
edge cases: worker briefs ignored explicit approval-head records; unnamed
sessions could reclaim each other; successive partial result batches lost
remaining-work history; a standalone incident link persisted only one
direction; and a same-store write from another thread could join a transaction
that later rolled back. Focused regressions cover those boundaries alongside
the original GitHub findings.

Crash tests terminate actual child processes before commit and during a write.
Separate processes test lock contention and ID allocation from stale snapshots.
These tests establish process-crash recovery on the local macOS host; they are
not a claim of Windows runtime or storage power-loss testing.

## Live pilot: Gmail2PDF PR 40

| Item | Observed result |
| --- | --- |
| Target | [smorinlabs/gmail2pdf#40](https://github.com/smorinlabs/gmail2pdf/pull/40), Tach 0.35.0 to 0.35.1 |
| Scope | Only `uv.lock`, 18 additions and 18 deletions; one fixed selection |
| Approved head | `44a32b2547c27bdf2caa725b54672cb068122a10` |
| Authority | Gated mode, explicit approval of this PR, no repair permissions |
| Pre-merge checks | 22 successful, 8 skipped, no pending or failed check runs; no unresolved threads or change requests |
| Optional reviewer | CodeRabbit's successful status explicitly reported that its review was skipped |
| Policy | Known effective policy; no required contexts, approvals, or merge queue |
| Merge | [f30d0e720bb8f5c783fe355693e3fa55e466ed7b](https://github.com/smorinlabs/gmail2pdf/commit/f30d0e720bb8f5c783fe355693e3fa55e466ed7b), observed merged at 2026-09-27T07:32:42Z |
| Durable completion | Reloaded store: selected 1, merged 1, delivered 1, unknown 0; both attempts complete; lease released; no continuation |

The pilot ran before the PR 87 recovery corrections. Its unchanged completed
journal was replayed with the revised implementation and retained the same
merge, attempt, lease, and accounting results. No second live merge was used
to validate those corrections.

The preparation run returned the approval hold and was finished when its
original deadlines expired during safety work. After approval, a new execution
run explicitly linked to that preparation. Its first worker attempt returned
READY under the saved approval and actual lease. The coordinator collected
that outcome before scheduling the merge attempt with the inherited deadline.
The designated worker used the approved-head wrapper. Fresh GitHub observations
by both worker and coordinator verified merged state, commit, and timestamp
before collection and replay.

Nine integration suites retained queued suite records but contained no check
runs. Separate complete suite/check-run reads found no actual pending job.
Those records were disclosed and were not counted as successful checks.

Final release validation after integrating current main, the PR 87 review
corrections, and the 0.31.0 marketplace metadata:

```text
just all
835 passed, 4 skipped in 81.62 seconds
```

This includes the generation drift check and all discovered tests. The
standalone helper's 24 tests run separately because its filename is outside
pytest discovery.

At 2026-09-27T07:36:01Z, all eight expected workflows on the merged commit
completed successfully: CI/CD, CodeQL, large-file-guard, commitlint, secret-scan,
release-please, press-verify, and lint. Reading all 14 workflow files at the
merged commit established that exactly those eight apply to a push to `main`.
The commit had 25 successful check runs and three conditional skips: public-only
CodeQL analysis, Dependabot-PR-only commitlint, and manual-only Weasyprint live
tests. No applicable workflow was missing or pending. There were no commit
status contexts.

The principal post-merge run is
[CI/CD 36303431371](https://github.com/smorinlabs/gmail2pdf/actions/runs/36303431371).
The pilot made no repair, workflow rerun, or repository-setting change.

## Limits

This pilot proves the direct, dependency-only, gated path for one lockfile PR.
It does not exercise a live repair, replacement PR, merge queue, or ambiguous
transport result. Windows-only tests skipped on the local macOS host remain
skips. No repository settings or repair permissions were changed for the pilot.
