# Worked examples

Nine fictional situations rendered through the workflow, one per shape the
skill must handle. Every fact, revision, test result, and repository detail
below is invented for illustration and is not a claim about any real project.
Read the one closest to the situation at hand before drafting; the shape is the
point, not the wording. Sizing paragraphs are author notes; rendered briefs omit
tier tags and start with orientation only when the question needs it.
The outer code fences in this file quote each rendered message; the message
itself is sent as ordinary text with pipe tables. Alignment-dependent diagrams
retain their own inner fences. Behavioral edge cases and grading expectations
live separately in `../evals/evals.json`; examples alone are not validation.

## 1. Routine authorized work: the gate says no ask

Situation: the approved plan's step 3 said to rename `exportCsv` to
`exportCsvReport`; done at six call sites on commit `a1b2c3d`; type check and
unit tests pass; no behavior change.

Gate result: authorization exists (the plan, approved two hours ago), the
change is on plan, and nothing is uncertain. This skill does not fire. The run
reports in ordinary form and continues:

```
Renamed exportCsv to exportCsvReport at its six call sites, step 3 of the
approved plan. Type check and unit tests pass on commit a1b2c3d. No behavior
change. Continuing with step 4.
```

## 2. Completed, tested change behind a required gate: T1

Situation: PR #142 fixes keyboard focus in the search dialog exactly as
planned; checks passed on revision `9c8d7e6`; the repository requires a human
to approve every merge.

Sizing: every axis low; the gate is the only reason to ask.

```
Q1. Merge PR #142, the keyboard-focus fix for the search dialog?
It implements the approved change. The keyboard-interaction test and all
required checks passed on revision 9c8d7e6. CONTRIBUTING.md requires a human
merge approval. Recommendation: Q1.A.
  Q1.A  Merge (Recommended)  -- the fix ships on the next deploy
  Q1.B  Hold                 -- the PR stays open; say what to change
```

## 3. Scope deviation with a compatibility tradeoff: T2

Situation: the request covered CSV imports only; the prepared fix lives in the
shared date validator and changes API uploads too; tests pass for both paths on
commit `3f2a9c1`; third-party caller compatibility cannot be verified from the
repository.

Sizing: departure elevated (scope the human has not seen), uncertainty elevated
(callers unverifiable). Change type: conditional behavior, so a same-input
table.

```
The CSV import repair changes a shared date validator, src/validate/date.ts,
which also handles API uploads. The prepared fix passes both test suites, but
changing API upload behavior exceeds the approved CSV-only scope.

Q1. Include the shared date-validation fix in this PR?
Recommendation: Q1.A, include it, so CSV imports and API uploads validate dates
the same way. Q1.B wins if existing external caller behavior must be preserved.

Why I am asking: the next commit would include the API behavior change.
Keeping it CSV-only preserves existing external caller behavior.

What changes, same input on both paths (reproduced from the regression run on
commit 3f2a9c1):
| Input                          | Today                            | With the fix                              |
|--------------------------------|----------------------------------|-------------------------------------------|
| 2024-02-30 through CSV import  | corrected to 2024-03-01 silently | rejected: "day 30 is not valid for February" |
| 2024-02-30 through API upload  | corrected to 2024-03-01 silently | rejected with the same message            |

What you would be accepting: API callers that rely on silent correction start
receiving validation errors. Reverting is one commit, but any upload rejected
in the meantime must be resubmitted by the caller.

Evidence: Verified: regression tests pass for both paths on commit 3f2a9c1.
Not verified: whether any third-party caller depends on silent correction; the
repository holds no caller inventory.

Options:
  Q1.A  Include the shared fix (Recommended)      -- both paths reject impossible dates; the PR gains one file
  Q1.B  Keep the fix to CSV imports               -- the API keeps silently correcting; validator logic is duplicated
  Q1.C  Include the shared fix behind a flag      -- default off for the API; no caller change now; a setting to retire later

Would change my recommendation: a rule that existing external caller behavior
must be preserved favors Q1.B.

On Q1.A I will: add the shared change to PR #57 and rerun the API upload suite.
Nothing merges.

Details: diff at src/validate/date.ts; test output in ci/run-4412.log.
```

## 4. Race condition: T3 by domain complexity, no record

Situation: stale search results overwrite newer ones; fix is a sequence number
check, 14 lines in `src/search/handler.ts`. Before drafting, the agent ran
tests that force out-of-order success responses and an older error arriving
after a newer success; both pass on commit `6f5e4d3`. Impact is limited to the
search box; the project requires approval for user-visible behavior changes.

Sizing: domain complexity high (timing); impact elevated because the behavior
is user-visible, which the T3 already covers; the rest low. Change type:
timing, so an event table with identical event order. Record: not due, only
"real tradeoff" is arguable, and the change is one revert away.

```
Q1. Merge commit 6f5e4d3 into the release branch so only the latest search request updates the results?
Recommendation: Q1.A, approve. Q1.B (hold) wins only if the search box must
keep showing every response, which nothing in the product asks for.

Why I am asking: CONTRIBUTING.md requires approval for any user-visible
behavior change. This one changes what the search box shows when responses
arrive out of order.

What changes. The failure and the fix, same events in the same order (the
event order is the one the new test reproduces):
| Event                                  | Current behavior                             | Proposed behavior                                      |
|----------------------------------------|----------------------------------------------|--------------------------------------------------------|
| you search "cat", then "caterpillar"   | both requests run                            | both run; "caterpillar" is recorded as latest (seq 2)  |
| results for "caterpillar" arrive first | displays "caterpillar" results               | displays "caterpillar" results                         |
| results for "cat" arrive later         | overwrites the display with stale "cat"      | seq 1 is older than 2, so the response is dropped      |
Mechanism: each request gets an increasing sequence number; the response
handler updates the display only when the response's number matches the latest
request. Property protected: only the most recent search request may update the
results. Limit: older requests still consume network until they finish.

What you would be accepting: no visible change except that stale results stop
appearing. Reversal is one commit with no lasting effect.

Evidence: Verified: the out-of-order success test and the older-error-after-newer-success
test both pass on commit 6f5e4d3. Inferred, from reading the handler rather than a test: the
latest number and the response number are read on the same thread, so no
interleaving can update the display with an older response. Not verified:
production traffic; the controlled tests establish the two specified response
orders, not every browser or network condition.

Options:
  Q1.A  Merge the sequence-number fix (Recommended)  -- the release branch gains the tested change in src/search/handler.ts
  Q1.B  Hold                                           -- stale results keep appearing; say what evidence you want first

Would change my recommendation: a requirement to show every response, or a
failing error-path test.

On Q1.A I will: merge the verified commit 6f5e4d3 into the release branch.
Deployment remains outside this approval.

Details: diff at src/search/handler.ts; both tests in test/search/order.test.ts.
```

## 5. Architectural direction during planning: T3 with a record

Situation: exports time out (p95 48 s against a 30 s gateway limit, production
logs 2026-09-01); worker process with a queue table and a migration, or
streaming in the web process with a size cap; migrations need a maintenance
window; nothing prototyped; the direction is hard to reverse once the
migration ships.

Sizing: reversibility high, tradeoff complexity high. Change type:
architectural, so a coded map with the change as ghosts. Record: due, hard to
reverse and a real tradeoff.

```
Report exports currently run inside the web request and exceed its 30-second
gateway timeout. Neither alternative has been prototyped. This choice selects
implementation work on a branch; running a database migration requires a
separate maintenance-window approval.

Q1. Which direction for report exports: a separate worker process, or streaming inside the web process?
Recommendation: Q1.A, the worker process, because export execution would run
outside the request's gateway timeout. Q1.B wins if a maintenance window cannot
be scheduled this month.

Why I am asking: this selects the next two weeks of work, and once the jobs
migration ships the direction is expensive to undo. The approved plan assumed
exports stay in the web process.

What changes. Today, one representative export (illustrative map of the three
structures the decision touches):
[U] browser --request--> [W] web process --runs export--> [D] primary db (store)
                                                |
                                          gateway cuts off at 30 s
With Q1.A, the change as new pieces:
[U] browser --request--> [W] web process --enqueue- - > [J] jobs table (store, proposed)
                                                          |
                                                          `- - > [X] export worker (proposed) --> [D]
Unchanged, not shown: auth, billing, the report renderer.
Q1.B keeps the map as it is today and streams rows from W as they are produced.

What you would be accepting:
  Q1.A  a new jobs table and a migration, which needs a maintenance window;
        export execution outside the request timeout, with maximum size still
        unmeasured; reversal means dropping the table and restoring
        the synchronous path, a day of work plus a second window.
  Q1.B  no migration; report size capped at what one request can carry,
        which the two largest customers already exceed (invoice sizes,
        2026-08); reversal is one commit.

Evidence: Verified: p95 export time 48 s from production logs on 2026-09-01.
Inferred: the size cap under Q1.B, from the request limit, not measured.
Not verified: neither approach is prototyped; I can build a throwaway worker
in about a day if you want evidence before choosing.

Options:
  Q1.A  Move exports to a worker process with a jobs queue (Recommended)  -- migration and window required; maximum size unmeasured
  Q1.B  Stream exports from the web process                              -- no migration; size cap; two customers affected
  Q1.C  Prototype the worker for a day before choosing                   -- delays the decision one day; produces measured evidence

Would change my recommendation: no maintenance window available this month, or
a measured streaming result that clears the largest reports.

On Q1.A I will: write the jobs-table migration and the worker skeleton on a
branch; the migration itself still needs its own window approval.

Details: production log query in research/export-timing.md; the plan's export
section in docs/plan.md.

Record: this decision will be retained as Decision Q1 in docs/adr/ once you
answer, because it is hard to reverse and the result of a real tradeoff.
```

## 6. Short change with a major consequence: T3 by impact and reversibility

Situation: a one-line change lowers log retention from 90 days to 30 days,
saving an estimated 1,800 USD per month; the compliance page requires audit
logs to be kept 90 days and the setting governs both log kinds; deleted logs
cannot be recovered. The user requested unattended analysis through the end of
the day, with retention changes still requiring approval.

Sizing: impact high (a compliance contract), reversibility high (deleted logs
are gone). One line changed is not one axis low. Change type: conditional, one
sentence suffices because the mechanism is not the difficulty. Record: due,
hard to reverse and a real tradeoff.

```
Q1. Split log-retention settings to reduce application-log storage cost while preserving the required 90 days of audit logs?
Recommendation: Q1.A, split the setting first so application logs drop to 30
days and audit logs stay at 90. Q1.B wins only if the 90-day policy no longer
applies.

Why I am asking: you asked me to cut storage cost. The one-line change in
config/retention.yaml does that, but the same setting governs audit logs, and
docs/policies.md says audit logs must be kept 90 days. Cutting them is a
policy decision, not a cost decision.

What you would be accepting under Q1.B: audit logs older than 30 days are
deleted and cannot be recovered; reverting the line restores the setting but
not the logs. Under Q1.A: most of the saving, one extra configuration key.

Evidence: Verified: the setting applies to both log kinds (config/logging.ts,
line 41). Inferred: about 1,800 USD per month saved, estimated from last
month's invoice, not confirmed against a quote. Not verified: whether the
policy is still in force; docs/policies.md was last edited 2025-11-03.

Options:
  Q1.A  Split the setting: application logs 30 days, audit logs 90 (Recommended)  -- most of the saving; policy kept; one extra config key
  Q1.B  Lower retention for all logs to 30 days                                  -- full saving; audit logs breach the written policy; deleted logs are gone
  Q1.C  Defer changes pending clarification of the policy                        -- existing retention stays in place

Would change my recommendation: confirmation that the 90-day policy is retired.

On Q1.A I will: add a separate audit-retention key, keep it at 90 days, and
lower the application-log key to 30 days, then rerun the config tests.

If I hear nothing by the end of the day: leave the retention change pending
and the existing settings intact, because deleted logs cannot be restored.
This fallback changes no retention setting and grants no approval.

Record: retained as Decision Q1 in docs/adr/ once you answer.

Details: the one-line diff in config/retention.yaml; the policy text in
docs/policies.md; last month's storage invoice in finance/2026-08-storage.pdf.
```

## 7. Unfamiliar mechanism with low impact: T3 by domain complexity

Situation: retry backoff for a nightly cache warmer changed from fixed 200 ms to
exponential with jitter; only one internal dashboard is affected; tests pass on
commit `7b6c5d4`; the project requires approval for retry-logic changes after a
past incident; the reader is not familiar with backoff.

Sizing: domain complexity high for this reader, everything else low. Change
type: algorithm, so a worked example with the boundary case and the invariant.

```
Q1. Merge commit 7b6c5d4, the tested retry-timing change for the nightly cache warmer?
Recommendation: Q1.A, approve. Q1.B wins if you want the fixed timing kept
until the next incident review.

Why I am asking: CONTRIBUTING.md requires approval for any change to retry
logic since the March incident. This one changes how long the warmer waits
between attempts.

What changes. Backoff is the wait between retries. Fixed backoff waits the same
200 ms every time; exponential backoff doubles the wait each time, and jitter
adds a small random amount so many warmers do not retry in lockstep. This
illustrative schedule waits once before each of five attempts; there is no
immediate first attempt in this example:
| Attempt | Fixed (today) | Exponential with jitter (proposed) |
|---------|---------------|------------------------------------|
| 1       | wait 200 ms   | wait 100 ms plus 0 to 50 ms        |
| 2       | wait 200 ms   | wait 200 ms plus 0 to 100 ms       |
| 3       | wait 200 ms   | wait 400 ms plus 0 to 200 ms       |
| 4       | wait 200 ms   | wait 800 ms plus 0 to 400 ms       |
| 5       | wait 200 ms   | wait 1,600 ms plus 0 to 800 ms, capped at 2 s |
Rule preserved: never more than five attempts, never a wait above 2 s.
Boundary case: the fifth wait can reach the cap. Maximum cumulative waiting is
4.25 s (150 + 300 + 600 + 1,200 + 2,000 ms), versus 1 s today. These totals
exclude request execution and network timeouts; they do not bound total runtime.

What you would be accepting: the schedule can add up to 3.25 s of backoff
waiting for one internal dashboard. Total cold-start time also depends on how
long each request takes. Reversal is one commit.

Evidence: Verified: tests on commit 7b6c5d4 assert every attempt's wait falls
inside its window, and the attempt cap. The timing table above is illustrative,
computed from the parameters, not recorded from a run. Not verified: maximum
request duration; an end-to-end runtime bound needs a bound on each attempt.

Options:
  Q1.A  Merge exponential backoff with jitter (Recommended)  -- spreads retries; adds up to 3.25 s of scheduled waiting
  Q1.B  Keep fixed 200 ms                                       -- no change; the incident review's concern stays open

Would change my recommendation: a strict total cold-start deadline; measure or
bound request duration before approving a schedule against that deadline.

On Q1.A I will: merge commit 7b6c5d4.

Details: diff at src/cache/warmer.ts; timing test in test/cache/backoff.test.ts.
```

## 8. Identifiers that must be defined locally: T2

Situation: Phase 1 (a migration that stores queued jobs) is merged; Phase 2
(exports move to background workers) is in progress; Task 4 in it (the worker
health-check endpoint) is blocked because Phase 1 did not create the
`jobs_status` index; adding it is a new migration outside the plan; an earlier
"Option B" was to poll the table instead.

Sizing: departure elevated (a migration outside the plan); reversibility
elevated (a schema change undone by dropping the index). Every reference is
defined where it is used.

```
Q1. Add a database index on the jobs table's status column, a new migration outside the approved plan, or poll the table without it?
Recommendation: Q1.A, add the index. Q1.B wins if a migration cannot be
scheduled this week.

Why I am asking: the worker health-check endpoint (Task 4 of the second phase,
which moves report exports into background workers) needs to count jobs by
status quickly. The first phase's migration, which created the table that
stores queued jobs, did not add an index on the status column. Adding one is a
new migration the plan did not include, so it needs your approval.

What changes: the current status count scans the whole table, about 2 s at
today's 400,000 rows (measured on a staging copy, 2026-09-06). The index is
intended to avoid that full scan; its effect on latency has not been measured.

What you would be accepting: one more migration in this phase, run during a
maintenance window; reversal is dropping the index.

Evidence: Verified: the 2 s scan on staging at 400,000 rows. Inferred: growth
with table size, from the query plan, not measured at larger sizes.
Not verified: latency with the proposed index.

Options:
  Q1.A  Add the status index as a new migration (Recommended)  -- one window; intended to avoid the full scan; latency still to verify
  Q1.B  Poll the table on a timer instead of counting on demand -- no migration; the health check reports up to 60 s stale
  Q1.C  Defer the health check to the third phase              -- the worker rollout proceeds without it

Would change my recommendation: no maintenance window available this week.

On Q1.A I will: write the migration, add it to the plan's second phase as a new
task, and rerun the health-check test.
```

## 9. Recover the artifact, then reassess the choice

Situation: implementation of optional automation for the fictional public
`library-starter` template is authorized. Two workflow candidates exist as
`research/automation/review.yml` and `research/automation/assistant.yml`;
neither is installed under `.github/workflows/`.
The review candidate checks the pull-request author; the assistant candidate
checks the author of the requesting comment. Question Q2 offered three planning
choices: leave both inactive, prepare review
activation after validation, or prepare both for activation after validation.
The agent called them "lanes". The user asks, "Which files are these, and what
would my answer change today?"

The clarification below is an excerpt replacing the opening and comparison of
Q2, not a complete risk-acceptance brief. The unchanged options retain their
IDs. The artifact table answers the missing identity question before any token
ordering trace.

```
This concerns optional GitHub Actions automation for `library-starter`, the
public repository template we are building. These are two proposed workflow
files. A workflow tells GitHub which event starts its jobs.

| Existing research file | Proposed installed file | Role |
|---|---|---|
| `research/automation/review.yml` | `.github/workflows/review.yml` | Run Claude to review pull requests |
| `research/automation/assistant.yml` | `.github/workflows/assistant.yml` | Run Claude when a collaborator requests help in a comment |

Neither workflow is installed or running. Q2 chooses the activation plan I
will record today. Activation would happen later, after implementation,
validation, and the separately required activation approval.

Both candidates currently assume a repository setting named `AI_ENABLED`,
an on/off switch. Shipping optional automation is agreed; this manual switch
is my proposed implementation. You can replace that proposal.

For the same collaborator comment requesting help:

| State | Result |
|---|---|
| Today, with no installed assistant workflow | No assistant job runs |
| Proposed workflow installed, `AI_ENABLED` absent | Candidate condition prevents the assistant job; not tested on GitHub |
| Proposed workflow installed, `AI_ENABLED=true` | Eligible to run, subject to the remaining checks; not tested on GitHub |

This explains the proposed control. It does not establish that its safeguards
work. The source inspection also found different permissions and restrictions:

| Workflow | Declared contents permission | Separately acquired token | Bot exclusion in candidate |
|---|---|---|---|
| `review.yml` | read | Effective permissions not verified | Present; platform behavior not tested |
| `assistant.yml` | write | Contents write requested; effective permissions not verified | Absent |

The review workflow's read declaration therefore does not prove that all its
credentials are read-only. A restriction in `review.yml` also does not protect
`assistant.yml`. Both findings remain part of the decision.
```

Now the user says: "Use credential detection instead. Install both workflow
files by default; missing credentials should produce a successful run with a
visible explanation. Exclude bots and require both collaborator status and
write access. Implement that, but do not activate either workflow here."

The response changes because the user has supplied requirements and authority,
not merely asked for a clearer account of the old options:

```
I will include the GitHub Actions workflow files `.github/workflows/review.yml`
and `.github/workflows/assistant.yml` in the template by default, using
credential detection. When credentials are missing, the required behavior is
a successful run with a visible explanation.

Both workflows must exclude bots and require collaborator status plus write
access. The review workflow checks the pull-request author; the assistant
workflow checks the author of the requesting comment.

Q2 is superseded: its options assumed the `AI_ENABLED` manual switch, which you
have replaced. I am recording decided Q3 with your requirements and your
implementation approval. Neither workflow is authorized for activation here.

I will now replace the candidate conditions, implement the missing bot check,
and validate the missing-credential and author-permission cases. Those are
requirements to prove; they are not yet observed platform behavior. The review
workflow's exchanged-token permissions remain unverified and must be resolved
before an activation decision can describe its access accurately.
```

The second reply does not re-offer obsolete options or ask the user to approve
the same requirements again. It preserves the new implementation boundary and
the unresolved permission fact. A further owner decision is needed only if the
investigation discovers a tradeoff not covered by that approval.

The user's final verb determines the authorized work; do not copy the approval
scope from this example into a different conversation. If the reply instead
says "Update the design and implementation plan accordingly", the response and
record both say: "Q3 approves updating the design document and implementation
plan. It does not authorize implementing, installing, or activating the workflow
files." The requirements for the future workflows stay the same, but the
immediate action is editing the planning documents. A decision record cannot
grant broader authority than the reply that created it.
