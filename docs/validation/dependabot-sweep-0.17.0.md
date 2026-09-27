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
Claude and Codex native loading passed. Native loading checks availability, not
behavior; the tests and live proof below supply behavioral evidence.

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

Final release validation after integrating current main and generating the
0.31.0 marketplace metadata:

```text
just all
736 passed, 4 skipped in 80.79 seconds
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
