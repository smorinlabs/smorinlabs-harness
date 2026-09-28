# Complete report delivery

The saved report and the inline result describe one final snapshot. The
orchestrator's `run describe --save PATH` writes the readable report and also
emits it. Include that full readable result in the conversation. Raw API
payloads and logs are supporting evidence and need not be printed inline.

## Required contents

1. Scope, observation time, selected PR count and distinct outcome counts.
   A separately observed open total needs complete discovery evidence for that
   same scope; unknown mutation outcomes are not proved open. Label stale or
   unavailable counts explicitly.
2. Every selected PR, linked replacement and unselected late arrival: repository,
   number, title, URL and result. Preserve the distinction between a PR created
   during the run and one discovered after its execution budget ended.
3. Every unresolved PR: current technical conditions, remaining reviews,
   execution stop, recommendation, responsible party and resume evidence or
   event. A deadline is an execution stop, not proof of a product defect.
4. Every closed PR: closure reason and replacement relationship. A closed
   original only counts as delivered when its replacement has merged proof.
5. Follow-ups, including those discovered after merges: affected repository,
   problem, attribution or uncertainty, status, recommendation, responsible
   party, evidence and external issue links if an issue was actually filed.
   If none were identified, say so explicitly.
6. Recommended order for continuing, the actual decisions still needed and one
   verified continuation reference, or an explicit statement that none runs.

For large results, group rows by repository or shared cause and use consecutive
tables. Every PR still has an individual row. A short summary and file link
cannot replace the full result in chat.

## Current conditions and historical evidence

Retain older observations so the report can explain a change, but identify the
commit they concern. A successful repair remains useful history after a budget
stop; it does not prove that a newer commit is tested. Fresh reporting evidence
must not silently change the evaluated head, renew a deadline, grant approval,
release a repository or resolve an uncertain mutation.

An explicit owner hold needs the source and scope of that instruction. Keep
technical prerequisites, permission to perform an action, and owner preferences
separate. A planning note is not automatically an owner veto. A permitted
migration may require bounded implementation work without another permission
question.

## Shared decisions and follow-ups

Group genuinely identical decisions by repository, action scope and effects.
Keep the exact PR identities and commits visible. A shared closure proposal
does not authorize alert dismissal, repository settings or unrelated merges.
The existing incident records also track follow-up work; extending one record
must not discard the other PRs it affects.

Workers may include follow-ups in any outcome, including `merged`. Later
read-only observations may add or update a follow-up after its attempt ends.
These local records do not create issues externally. Record whether a problem
was caused by this sweep, pre-existing, or of unknown attribution, with evidence
for that conclusion. Resolved records remain visible as resolved history.

### Record a follow-up

Use `incident record --file followup.json --card PR-001` to attach work to a
card, including a merged card. Without a card, identify `repo_id` or `target`.
The JSON fields are:

| Field | Meaning |
| --- | --- |
| `key` | Stable, repository-specific identity used to avoid duplicate incidents. |
| `claim` | Observed problem or remaining work. |
| `repo_id`, `target` | Affected repository or other named target; at least one is required. |
| `action`, `action_owner` | Concrete recommendation and who can carry it out. |
| `evidence` | Nonempty list of objects with `what` and `establishes`; include `head_sha` when commit-specific. |
| `status` | `open`, `in_progress`, `blocked`, `resolved`, or `dismissed`. |
| `attribution` | `caused_by_sweep`, `pre_existing`, `unknown`, or `not_applicable`. |
| `attribution_note` | Evidence or uncertainty behind the attribution. |
| `external_links` | Objects with `url` and optional `title` and `tracker`; include only actual filed issues. |

Workers can include the same records in a `followups` list on any outcome.
Use `incident update ISSUE-ID --file update.json` later. Updates preserve prior
evidence and lifecycle history. Resolving or dismissing work requires fresh
evidence. `incident list` includes the resolved history as well as open work.

### Keep conditions separate

Outcome records can include these additive fields:

| Field | Meaning |
| --- | --- |
| `blockers` | List of current conditions with `kind` (`technical`, `review`, `evidence`, `decision`), `reason_code`, and `reason_line`. An explicit empty list clears previously evaluated blockers. |
| `execution_stop` | Why execution stopped, with `reason_code` and `reason_line`. `K14` denotes the exhausted budget. An empty object clears a previous stop. |
| `owner_hold` | A real instruction, with its `source` and `reason`; optional `scope`, `actor`, `recorded_at`, `head_sha`, and `active`. Releasing a recorded hold requires sourced `active: false`. |

Conditions and stops may also include `action`, `action_owner`, `resume_trigger`,
`evidence`, `observed_at`, and `head_sha`. Bind evidence to the evaluated commit.
Old or unbound evidence remains history, not proof that the current commit is
ready. A budget outcome preserves earlier technical findings and repair receipts.
An active merge hold also protects tasking and evaluation. A worker's report of
a release does not remove a hold frozen in the run's authority: the coordinator
must first verify the user's release and update that authority. Report fields
never grant new execution permission.

For identical decisions, `decision.group_key` and `decision.scope` can group
the recommendation. Grouping preserves each PR URL and full commit and does
not broaden the permission to merge, close, or change settings.

## Acceptance

Replay a representative saved run and compare the saved report with the full
human output. Account for every selected, replacement and late-arriving identity,
all holds, all follow-ups and every continuation. Check observable delivery
through supported agent surfaces as well as renderer behavior. A test that only
finds these instructions in the skill text does not prove delivery.
