---
name: factor-dedup
description: Cross-implementation consolidation for N similar implementations. Walks comparator reports per-implementation, classifies divergences as intentional or accidental, proposes a unified design (or documents why divergence should stay). Produces an inline consolidation spec ready to feed to Superpowers writing-plans. Use this whenever the user has multiple files/functions/commands they suspect are duplicates — even if they don't say "factor-dedup" (phrases like "consolidate these", "these all look the same", "DRY this up", "extract common code", "shared abstraction" should all trigger).
when_to_use: When the user has N implementations they suspect are duplicates and wants to consolidate. Triggers include "consolidate these N files", "deduplicate", "extract common code", "DRY this up", "these look identical", "merge these implementations", "shared abstraction across X", "5 commands doing the same thing".
allowed-tools: Read Grep Glob Task TodoWrite WebFetch WebSearch
---

# factor-dedup — cross-implementation consolidation

**Iron law:** **"These look duplicated" is a hypothesis, not a
fact.** The comparator subagents may surface that the
divergence is intentional (different domain, different
trade-off) and the right answer is "leave them separate". This
skill must accept that outcome and produce a spec that
*documents the intentional divergence* rather than forcing a
consolidation.

This skill compares N implementations, classifies their
divergences, and proposes either a unified design or a
documented reason to keep them separate. It does not refactor
anything. The output is a consolidation spec the user feeds to
Superpowers `writing-plans`.

See [`../​_conventions.md`](../_conventions.md) for the shared
factor-harness conventions.

---

## When to use this skill

Trigger phrases:
- "these N files look duplicated"
- "consolidate these implementations"
- "DRY this up"
- "extract common code"
- "5 commands doing the same thing"
- "shared abstraction across X"
- "merge these into one"

Do **not** use this skill when:
- The user wants a broad scan that may *find* duplicates but
  doesn't have specific candidates → use `factor-scan`.
- The user is reviewing a plan or finished feature for general
  architectural concerns → use `factor-architect`.

## Workflow

### Step 1 — Confirm the candidate set

Ask: "These N files? Anything missing?"

Surface the candidate set the user named. Then ask if any
related implementations might also belong in the comparison —
sometimes the user only spotted 3 of 5 duplicates. A
half-complete consolidation is worse than a complete one.

If the user is unsure, you can dispatch a `factor-scanner`
quick scan over the surrounding directory to see if the
scanner surfaces sibling implementations the user missed. But
don't make this the default — the user usually knows their
codebase.

### Step 2 — Optionally dispatch a researcher

Before dispatching comparators, decide whether external
ecosystem patterns matter:

- If the implementations are ecosystem-specific (CLI subcommands
  in `clap`, HTTP handlers in Express, ORM models in Django,
  etc.), dispatch `factor-researcher` to find the canonical
  pattern for "consolidating N similar X in <ecosystem>".
- If the implementations are general code (utility functions,
  internal helpers), skip the researcher.

The researcher's output informs Step 5's unified design. It
does not gate the workflow — proceed with comparators in
parallel even while the researcher runs.

See [`../../agents/factor-researcher.md`](../../agents/factor-researcher.md).

### Step 3 — Dispatch comparators in parallel

Use the `Task` tool to dispatch one `factor-comparator` subagent
per implementation. All dispatches in the same message so they
execute in parallel.

Each dispatch prompt includes:
- The target file or function
- Comparison question (initially generic: "describe structure,
  behavior, edge cases" — used for the first pass; specific
  follow-up dispatches against a chosen reference are also fine)
- Optional: a short brief on what the user is trying to
  accomplish

See [`../../agents/factor-comparator.md`](../../agents/factor-comparator.md)
for the comparator's contract and output structure.

### Step 4 — Collate into three categories

Synthesize the comparator reports into three buckets:

1. **Truly identical** — same structure, same behavior, same
   edge-case handling. Consolidate freely.
2. **Intentionally different** — divergence has visible
   justification in the comparator reports. Different domain,
   different trade-off, different level of detail. Document
   and keep separate (or extract a partial shared core).
3. **Accidentally divergent** — subtle bugs, missing features
   in some, inconsistent edge-case handling, drift over time.
   These are the *interesting* findings; they're often bugs in
   their own right and may need fixing independently of the
   consolidation.

The bucket assignment is not always obvious. When a comparator
classifies a divergence as "unclear" (intentional vs accidental
ambiguous), surface it to the user during the per-finding walk
in Step 6.

### Step 5 — Decide direction per cluster

For each cluster of related implementations, decide:

- **Consolidate** — pick a winner; design the unified
  abstraction. Surface the design choice (signature, parameter
  shape, edge-case strategy) to the user before producing the
  spec.
- **Keep separate** — document the justification visibly so
  future maintainers don't try to consolidate again.
- **Hybrid** — extract a shared core; keep variant entry
  points. Common when implementations agree on most logic but
  diverge meaningfully on some inputs.

Use the researcher's findings (if dispatched) to inform the
unified design. If the ecosystem has a canonical pattern, lean
into it; if multiple patterns exist, surface both to the user
during Step 6.

### Step 6 — Per-finding walk on accidental divergences

Each accidental divergence walks per-finding because each may
itself be a bug. For each:

```
file.ext:line — <description>
Reference behavior: <what the reference does>
This implementation's behavior: <what diverges>
Classification: accidental | unclear
Reasoning: <one sentence>
```

Ask: accept (fix as part of consolidation) / modify (capture
adjustment) / skip (don't fix in this consolidation, defer) /
mark intentional (the divergence is justified; document and
preserve).

This walk is the most valuable part of the workflow. The user's
domain knowledge converts ambiguous divergences into either
"yes, that's a bug we should fix" or "no, that's intentional
because of X" — and either way, the spec gains permanent
context.

### Step 7 — Output inline consolidation spec

Suggested structure:

```markdown
# Consolidation: <name of the unified abstraction>

**Goal:** Consolidate N similar implementations into <unified
shape>. <One sentence on the win — fewer code paths, consistent
edge-case handling, single place to update.>

## Implementations consolidated
- file_a.ext (winner | merged | retired)
- file_b.ext (...)
- ...

## Unified design
- Signature: <function or class signature>
- Parameters: <description of each, including defaults and
              constraints>
- Edge-case strategy: <one paragraph: how nullability, errors,
              and divergent behaviors of the original
              implementations are handled in the unified version>
- Migration plan: <one paragraph or list: how existing callers
              are updated>

## Accidental divergences fixed
- file:line — <what was wrong; how the unified version handles it>
- ...

## Intentional divergences preserved
- file:line — <description>. **Reason kept:** <user's reasoning>
- ...

## Risks
- <bullet: subtle behavioral changes that callers may depend on>
- <bullet: migration ordering risks>

## Suggested sequencing
<Optional: order of consolidation steps; whether to extract
shared core first or replace implementations one at a time>
```

Tell the user this is ready to hand to
`superpowers:writing-plans` for an executable plan.

### Step 8 — When the answer is "keep separate"

If the comparators reveal the divergence is mostly intentional
and consolidation would lose meaningful behavior, the spec
becomes a *documentation spec* rather than a refactor spec:

```markdown
# Documented divergence: <name of the cluster>

**Goal:** Document why these N implementations are separate,
to prevent future consolidation attempts.

## Implementations
- file_a.ext — <purpose, audience, key constraints>
- file_b.ext — ...

## Why they are separate
<paragraph or list: the trade-offs that make consolidation
the wrong move>

## Optional: minimal shared extraction
<If a small shared core can still be extracted without losing
the meaningful divergence, describe it; otherwise omit>
```

This outcome is a success, not a failure. Forcing consolidation
when divergence is intentional is the failure mode the iron law
prevents.

## Anti-patterns to avoid

- **Forcing consolidation when divergence is intentional.** If
  the comparator reports show real reasons for divergence,
  produce a documentation spec, not a refactor spec.
- **Picking the "winner" implementation arbitrarily.** Use the
  comparator reports' edge-case-handling and error-pathway
  observations to choose; if no winner emerges, the unified
  design synthesizes the best of each.
- **Ignoring accidental divergences as "out of scope".** They
  are exactly in scope. Each one may be a bug; the per-finding
  walk surfaces the user's judgment on each.
- **Producing the spec without the per-finding walk.** The
  walk is where intentional-vs-accidental gets resolved. Skip
  it and you ship a spec that conflates the two.
- **Researching ecosystem patterns when the implementations
  are general code.** Researcher dispatch should be deliberate;
  generic utility functions don't need ecosystem research.

## See also

- [`../using-factor-harness/SKILL.md`](../using-factor-harness/SKILL.md)
  — orientation across the four factor-harness skills.
- [`../factor-scan/SKILL.md`](../factor-scan/SKILL.md) — broad
  scan that may surface duplicate candidates worth feeding into
  this skill.
- [`../factor-architect/SKILL.md`](../factor-architect/SKILL.md)
  — architectural review more broadly than dedup.
- [`../_conventions.md`](../_conventions.md) — shared conventions.
- [`../../agents/factor-comparator.md`](../../agents/factor-comparator.md)
  — comparator subagent dispatched in parallel by this skill.
- [`../../agents/factor-researcher.md`](../../agents/factor-researcher.md)
  — researcher subagent for ecosystem patterns.
