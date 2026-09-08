# Decision record

What to retain after a significant decision, and where. Read this at workflow
step 7. The record is plain text. This skill writes the text and names where it
should live; the run persists it there.

## When a record is due

Retain a record when at least two of these hold:

- The decision is hard to reverse: a migration, an external commitment, or an
  effect that survives reverting code.
- The decision is surprising without its context: a later reader would ask
  "why on earth" unless the finding that forced it is beside it.
- The decision is the result of a real tradeoff: a credible alternative lost on
  a stated criterion.

Routine decisions stay in ordinary change history: the pull request, the
commit message, the task row. A record for those is noise.

## The record

Keyed by the question's ID, which continues across the run, so the record and
the ask share one identity.

```
Decision Q3 (2026-09-07): Run report exports in a separate worker process.
Status: decided, followed the recommendation (Q3.A).
Problem: exports time out; p95 48 s against a 30 s gateway limit (production
  logs, 2026-09-01).
Context: the approved plan assumed exports stay in the web process; a
  migration needs a maintenance window (team constraint, docs/policies.md).
Chosen: Q3.A, a worker process fed by a database-backed queue.
Rationale: removes the gateway limit entirely; the streaming alternative caps
  report size at one request, which the largest customers already exceed.
Alternatives: Q3.B stream results in the web process (no migration; size cap).
Approval scope: selects the direction for the next two weeks; does not
  authorize the migration, which needs its own window.
Conditions: none.
Evidence: p95 measured from production logs on 2026-09-01; neither approach
  prototyped; the size cap for Q3.B is inferred from the request limit, not
  tested.
Revisit when: a material new finding or a changed constraint; state the
  finding explicitly when reopening.
```

Fields, in order: the decision as a sentence; status with followed or overrode;
problem; context; chosen option; rationale; alternatives and why they lost;
approval scope and its limits; conditions attached by the reader; evidence with
its status; when to revisit.

## Rules

- The rationale is never optional. It is what stops a settled decision from
  reopening every time someone new reads the code.
- A decision lives in exactly one place. Summaries elsewhere gist it in one
  line and link or point to the record; they never restate it.
- The accepted decision is the baseline for later work. Reconsider it only
  when a material new finding or a changed constraint warrants it, and say what
  that finding is.
- After recording, sweep everything that persists for the rejected option's
  name and for claims the decision made stale. The reader reads everything.
- Refer to the decision by its sentence, with the ID attached, never by the
  bare ID: "the worker-process decision (Q3)".

## Where it lives

In order of preference, whichever the project already has: an architecture
decision record directory such as `docs/adr/`, a decisions section of the
plan or the project file, the pull request description, the task row. When
none exists, the record goes in the pull request description and the ask says
so, so the reader knows where to find it later.
