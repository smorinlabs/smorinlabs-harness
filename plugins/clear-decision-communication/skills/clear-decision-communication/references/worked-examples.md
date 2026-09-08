# Worked examples

Eight fictional situations rendered through the workflow, one per shape the
skill must handle. Every fact, revision, test result, and repository detail
below is invented for illustration and is not a claim about any real project.
Read the one closest to the situation at hand before drafting; the shape is the
point, not the wording.
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
Q1. Merge PR #142, the keyboard-focus fix for the search dialog?   [T1]
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
Q1. Include the shared date-validation fix in this PR?   [T2: departure, uncertainty]
Recommendation: Q1.A, include it, so CSV imports and API uploads validate dates
the same way. Q1.B wins if existing external caller behavior must be preserved.

Why I am asking: the request covered CSV imports only. The fix I prepared lives
in the shared date validator (src/validate/date.ts), so it also changes API
uploads. That is a scope change you have not approved.

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
Q1. Approve the fix that lets only the latest search request update the results?   [T3: domain]
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
  Q1.A  Approve the sequence-number fix (Recommended)  -- ships on the next deploy; 14 lines in src/search/handler.ts
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
Q1. Which direction for report exports: a separate worker process, or streaming inside the web process?   [T3: reversibility, tradeoff]
Recommendation: Q1.A, the worker process, because it removes the gateway limit
entirely. Q1.B wins if a maintenance window cannot be scheduled this month.

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
        exports of any size; reversal means dropping the table and restoring
        the synchronous path, a day of work plus a second window.
  Q1.B  no migration; report size capped at what one request can carry,
        which the two largest customers already exceed (invoice sizes,
        2026-08); reversal is one commit.

Evidence: Verified: p95 export time 48 s from production logs on 2026-09-01.
Inferred: the size cap under Q1.B, from the request limit, not measured.
Not verified: neither approach is prototyped; I can build a throwaway worker
in about a day if you want evidence before choosing.

Options:
  Q1.A  Move exports to a worker process with a jobs queue (Recommended)  -- migration and window required; no size limit
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
Q1. Lower log retention from 90 days to 30 days, which also shortens audit-log retention below the 90 days the compliance policy requires?   [T3: impact, reversibility]
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
Q1. Approve the new retry timing for the nightly cache warmer?   [T3: domain]
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
  Q1.A  Approve exponential backoff with jitter (Recommended)  -- spreads retries; adds up to 3.25 s of scheduled waiting
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
Q1. Add a database index on the jobs table's status column, a new migration outside the approved plan, or poll the table without it?   [T2: departure, reversibility]
Recommendation: Q1.A, add the index. Q1.B wins if a migration cannot be
scheduled this week.

Why I am asking: the worker health-check endpoint (Task 4 of the second phase,
which moves report exports into background workers) needs to count jobs by
status quickly. The first phase's migration, which created the table that
stores queued jobs, did not add an index on the status column. Adding one is a
new migration the plan did not include, so it needs your approval.

What changes: with the index, the status count runs in milliseconds; without
it, the count scans the whole table, about 2 s at today's 400,000 rows
(measured on a staging copy, 2026-09-06), and grows with the table.

What you would be accepting: one more migration in this phase, run during a
maintenance window; reversal is dropping the index.

Evidence: Verified: the 2 s scan on staging at 400,000 rows. Inferred: growth
with table size, from the query plan, not measured at larger sizes.

Options:
  Q1.A  Add the status index as a new migration (Recommended)  -- one window; fast health check; plan updated
  Q1.B  Poll the table on a timer instead of counting on demand -- no migration; the health check reports up to 60 s stale
  Q1.C  Defer the health check to the third phase              -- the worker rollout proceeds without it

Would change my recommendation: no maintenance window available this week.

On Q1.A I will: write the migration, add it to the plan's second phase as a new
task, and rerun the health-check test.
```
