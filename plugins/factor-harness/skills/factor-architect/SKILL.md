---
name: factor-architect
description: Architectural review against precedent, conventions, and external good-pattern references. Two trigger contexts — pre-execution (review a Superpowers plan before code is written) or post-execution (review delivered code for refactor opportunities). Walks user through findings per-bucket. Produces an inline architectural review and refactor spec ready for Superpowers writing-plans. Use this whenever the user has just gotten a plan back, just shipped a feature, or wants an architectural review — even if they don't say "factor-architect" (phrases like "review this plan", "is this architecturally sound?", "any refactor opportunities?", "does this fit our patterns?", "look at recent commits" should all trigger).
when_to_use: After a Superpowers writing-plans output is produced and the user wants architectural review before executing-plans. Or after features ship and the user wants refactor opportunities reviewed. Triggers include "review this plan", "architectural review", "any refactor opportunities?", "does this fit our patterns?", "review recent commits", "look at the new auth module", "is this the right shape?", "should we apply pattern X here?".
allowed-tools: Read Grep Glob Task TodoWrite WebFetch WebSearch
---

# factor-architect — architectural review against precedent and external patterns

**Iron law:** **Existing precedent is not automatically good
precedent.** When the proposed code follows existing patterns,
this skill must separately verify the pattern is itself worth
following. If precedent is poor, the recommendation is to refactor
*both* the new code and the precedent — never "follow the bad
pattern for consistency". Reflexive precedent-following is the
single most common failure mode of architectural review.

This skill conducts an architectural review of either a forthcoming
plan (pre-execution) or shipped code (post-execution). It surfaces
findings classified into four buckets, walks the user through each,
and produces a refactor spec ready for Superpowers `writing-plans`.

See [`../​_conventions.md`](../_conventions.md) for the shared
factor-harness conventions.

---

## When to use this skill

Trigger phrases:
- "review this plan" (after Superpowers writing-plans)
- "architectural review"
- "any refactor opportunities?"
- "does this fit our patterns?"
- "is this architecturally sound?"
- "review the recent commits"
- "look at the new <feature> module"
- "should we apply pattern X here?"

Do **not** use this skill when:
- The user wants a broad bug + quality scan over a code area →
  use `factor-scan`.
- The user has N specific implementations they want consolidated
  → use `factor-dedup`.

## Two invocation contexts

This skill has two trigger contexts. The workflow is largely
shared; the difference is what gets reviewed.

### Pre-execution: review a forthcoming plan

A spec or plan has just been produced (typically by Superpowers
`brainstorming` → `writing-plans`, but any planning source
counts). The user wants to validate the architectural shape
before code is written.

Input: pointer to the plan file (e.g.,
`docs/superpowers/plans/2026-04-30-auth-rewrite.md`).

### Post-execution: review delivered code

Features have shipped. The user wants to surface refactor
opportunities in the delivered code — places where the shipped
code drifted from good patterns, or where applying a known
pattern would lift quality.

Input: pointer to a directory, file set, commit range, or
"recently changed" hint.

## Workflow

### Step 1 — Confirm context

Ask which trigger applies and confirm the input pointer:

- "Pre-execution review of a plan, or post-execution review of
  shipped code?"
- "Where's the plan file / which files / what commit range?"

If the input is large (a 600-line plan, a 50-file feature),
proceed but expect to scope further in Step 2.

### Step 2 — Read the input

Read the plan or the delivered code inline. For large code
inputs, dispatch one or two `factor-scanner` subagents for a
structural overview (what modules, what patterns, what
dependencies). The scanner output gives you the lay of the
land before you dive in.

See [`../../agents/factor-scanner.md`](../../agents/factor-scanner.md).

### Step 3 — Identify pattern clusters

Cluster the patterns the input proposes or uses. Each cluster
is a shape — for example:

- "command parser shape" (how subcommands are wired, how shared
  flags are handled)
- "error handling style" (panic vs Result vs typed errors;
  where errors get logged vs surfaced)
- "module boundary choice" (what's exposed; what's internal;
  how dependencies flow)
- "naming convention" (do similar things have similar names?)
- "test layout" (where do tests live; how is fixture data
  organized)

The clusters are surfaces of comparison. You'll evaluate each
against precedent and external patterns in Step 4.

### Step 4 — Survey precedent (in parallel)

For each pattern cluster, run two surveys in parallel:

1. **Internal precedent.** Dispatch `factor-comparator`
   subagents in parallel against existing similar files in the
   codebase. Each comparator describes one file's structure
   and behavior. The collated reports tell you what precedent
   exists and where it's consistent vs inconsistent.

   See [`../../agents/factor-comparator.md`](../../agents/factor-comparator.md).

2. **External canonical patterns.** When the cluster is
   ecosystem-specific (CLI patterns in a known framework, HTTP
   handler patterns in a stack, ORM patterns), dispatch
   `factor-researcher` to find canonical references. Skip when
   the cluster is general (e.g., naming conventions don't
   benefit from external research).

   See [`../../agents/factor-researcher.md`](../../agents/factor-researcher.md).

Dispatch both kinds of subagent in the **same message** when
both are needed for a cluster — let them run in parallel.

### Step 5 — Classify findings into four buckets

Once subagent reports are in, synthesize findings into four
buckets:

1. **Following good precedent** — the proposed/shipped code
   matches existing patterns AND those patterns are themselves
   worth following (per the canonical references or the
   pattern's own merits). Confirm; no action needed. **Surface
   anyway** so the review documents what was checked.

2. **Following bad precedent** — the proposed/shipped code
   matches existing patterns BUT those patterns themselves are
   problematic (anti-patterns, deprecated approaches, things
   the canonical references warn against). The recommended
   action is to refactor *both* — extending bad precedent
   makes the system worse, not better.

3. **Breaking precedent** — the proposed/shipped code does
   *not* match existing patterns. This is sometimes good
   (deliberately escaping a bad pattern) and sometimes
   accidental (the author didn't notice the precedent). Surface
   the divergence and let the user judge.

4. **New pattern introduced** — the input introduces a pattern
   not present in existing precedent. Evaluate it against the
   canonical references (if researched) and the codebase's
   overall style. Justified? Coherent? A net improvement?

The iron law lives in bucket 2. **A skill that just says "match
existing patterns" produces dead weight; a skill that asks "is
this a good pattern, AND does this match it?" produces lift.**

### Step 6 — Per-finding interactive walk

For each finding, present:

```
[Bucket] file.ext:line (or plan-section: <heading>)
Pattern: <name of the pattern cluster>
Evidence: <code/plan excerpt or paraphrase>
Comparison: <what precedent shows; what canonical reference
            shows>
Recommendation: <one sentence — accept, refactor both,
            justify deviation, or document>
```

User responds with one of:

- **accept** — the recommendation is right; carry into the spec
- **modify** — capture the user's amendment
- **skip** — defer; not in this review's spec
- **mark intentional** — the user has reasoning for the current
  state; capture the reasoning for the spec

The "mark intentional" response is critical for buckets 3 and
4 — many "breaks precedent" and "new pattern" findings have
real domain reasons that aren't visible from the code alone.

### Step 7 — Output inline architectural review + refactor spec

Produce two things in chat:

1. **Architectural review** — narrative summary covering all
   four buckets, including skipped findings and intentional
   markers. This is the artifact that documents what was
   considered but not acted on.

2. **Refactor spec** — only if findings were accepted. Format:

```markdown
# Architectural refactor: <area or feature name>

**Goal:** <one sentence — apply pattern X, refactor bad
precedent, etc.>

## Findings to address
1. **[Bucket]** <pattern cluster> — file:line / plan-section
   - Recommendation: <one sentence>
   - Optional: user's modification

## Findings consciously preserved
- file:line — <description>. **Reason kept:** <user's reasoning>

## Suggested approach
<2-3 sentences on whether to refactor in order, in parallel,
or to address the precedent before the new code>
```

The spec content is what the user feeds to
`superpowers:writing-plans` for an executable plan.

## Anti-patterns to avoid

- **Reflexive precedent-following.** A skill that recommends
  "match the existing pattern" without verifying the pattern
  is good has zero value-add and may make things worse. The
  iron law exists to prevent this.
- **Treating researcher output as gospel.** External canonical
  patterns inform; they do not dictate. The codebase has its
  own context. If the researcher says "everyone uses X" and
  the codebase has good reason not to, the codebase wins. The
  researcher's confidence levels matter — weight high-confidence
  more than low-confidence.
- **Skipping the per-bucket structure.** Lumping all findings
  into one list loses the most important distinction (good
  precedent vs bad precedent). Stay disciplined.
- **Producing a refactor spec without the per-finding walk.**
  The walk is where the user's domain knowledge converts noise
  into signal.
- **Going broader than the input.** If the input is a single
  module's plan, don't review the entire system. Stay focused.
  Note out-of-scope observations briefly in the review's
  optional `context_observations` section, but do not let them
  dominate.
- **Making code changes.** This skill is read-only. The output
  is descriptions; Superpowers turns descriptions into code.

## See also

- [`../using-factor-harness/SKILL.md`](../using-factor-harness/SKILL.md)
  — orientation across the four factor-harness skills.
- [`../factor-scan/SKILL.md`](../factor-scan/SKILL.md) — broader
  scan when the input isn't a specific plan or feature.
- [`../factor-dedup/SKILL.md`](../factor-dedup/SKILL.md) —
  when the architectural concern is specifically about N
  similar implementations.
- [`../_conventions.md`](../_conventions.md) — shared conventions.
- [`../../agents/factor-comparator.md`](../../agents/factor-comparator.md)
  — comparator subagent for in-codebase precedent surveys.
- [`../../agents/factor-researcher.md`](../../agents/factor-researcher.md)
  — researcher subagent for external canonical patterns.
- [`../../agents/factor-scanner.md`](../../agents/factor-scanner.md)
  — scanner subagent for structural surveys of large inputs.
