---
name: factor-scan
description: Broad sweep over a code area surfacing bugs, quality issues, and architectural smells. Walks the user through findings one at a time. Produces an inline spec ready to feed to Superpowers writing-plans. Use this whenever the user wants to scan a directory, file set, or recently-changed code for issues — even if they don't say "factor-scan" by name (phrases like "any bugs in this?", "review this for quality", "audit these files", "what's wrong here?", "code health check" should all trigger).
when_to_use: When the user says "scan", "audit", "review for bugs", "find issues", "quality check", "code health check", "what's wrong with this?", "any problems in this code?", or points at a file/directory and asks for a sweep. Also when `factor-architect` or `factor-dedup` reaches a point where a broader scan would inform their decision.
allowed-tools: Read Grep Glob Task TodoWrite
---

# factor-scan — broad code scan with per-finding triage

**Iron law:** **Severity defaults conservative; the user lifts
severity, not the skill.** False positives marked critical
poison every future scan. Mark conservatively; let the user
upgrade during the per-finding walk.

This skill conducts a broad sweep over a code area and surfaces
bugs, quality issues, and architectural smells. It does not fix
anything. The output is a list of findings (walked one at a time
with the user) and an inline spec the user can hand to Superpowers
`writing-plans` for the actual fixes.

See [`../​_conventions.md`](../_conventions.md) for the
conventions every factor-harness skill follows: pure workflow
shape, per-finding interactive UX, inline output, read-only
discipline, and the iron law layout.

---

## When to use this skill

Trigger phrases:
- "scan this directory for bugs"
- "audit these files"
- "any quality issues in X?"
- "review this for problems"
- "what's wrong with this code?"
- "code health check"
- "find issues in X"

Do **not** use this skill when:
- The user has a specific architectural review in mind for a plan
  or a finished feature → use `factor-architect`.
- The user explicitly says "these N files look duplicated, can we
  consolidate?" → use `factor-dedup`.
- The user wants to *fix* the issues directly → produce the spec
  inline, then redirect to Superpowers `writing-plans`.

If you're unsure between `factor-scan` and `factor-architect`:
`factor-scan` is broad and dimension-agnostic (looks for any kind
of issue across an area); `factor-architect` is narrow and
pattern-focused (reviews a specific plan or feature against
precedent). When in doubt, ask the user one clarifying question.

## Workflow

### Step 1 — Confirm scope (one question)

Ask the user to confirm what should be scanned. Surface a
concrete default if one is obvious from context (e.g., "the
files you just changed", "the directory you mentioned"), but
let the user adjust.

Acceptable scope shapes:
- A directory (e.g., `src/cli/`)
- A file set (e.g., a list of files, a glob)
- A git diff range (e.g., "since main", "in the last 3 commits")
- "Recently changed" (interpret as `git diff --name-only` against
  the upstream branch or last common ancestor)

If the scope is huge (more than ~30 files), ask the user to
narrow it before proceeding. Per-finding interaction over
hundreds of findings is not productive. A focused scope produces
a focused spec.

### Step 2 — Confirm dimensions (one question)

Default: scan all three dimensions (bugs, quality, architectural
smells). The user may want to narrow:

- "Just bugs" → scan only `bug`.
- "Just quality" → scan only `quality`.
- "Architectural review" → that's likely `factor-architect`'s
  job; redirect rather than running a single-dimension scan.

Briefly explain what each dimension means if it helps:
- **bugs** — logic errors, error-handling gaps, null/undefined
  risks, off-by-one, races
- **quality** — overly complex functions, unclear names, dead
  code, untested branches, missing observability
- **architectural smells** — god objects, tangled responsibilities,
  leaky abstractions, inconsistent module boundaries

### Step 3 — Dispatch scanners in parallel

Use the `Task` tool to dispatch one `factor-scanner` subagent per
file (or per logical area when files cluster). All dispatches
should be in the **same message** so they execute in parallel.

Each dispatch prompt includes:
- The file or area to scan
- The dimensions selected in Step 2
- Optional context (what the user is trying to accomplish, what
  the surrounding architecture is)

See [`../../agents/factor-scanner.md`](../../agents/factor-scanner.md)
for the scanner's contract and output format.

### Step 4 — Collate findings

Once all scanners report:

1. **Deduplicate.** If the same pattern shows up across many
   files (e.g., "missing null check on `req.user`"), keep all
   instances but flag them as related. The user may want one
   spec that fixes the pattern everywhere, or per-file fixes.
2. **Sort by severity.** Critical first, then important, then
   minor. Within severity, sort by file path so related findings
   group together.
3. **Sanity check the count.** If you have 50+ findings, the
   per-finding walk will exhaust the user. Offer to filter
   (e.g., "scope to critical and important only"; "scope to one
   directory at a time") before walking.

### Step 5 — Per-finding interactive walk

For each finding, present:

```
[Severity] [Dimension] — file.ext:line
Description: <one sentence>
Evidence:
  <code excerpt>
Recommended action: <one sentence>
```

Then ask the user one of:

- **accept** — include in the output spec as-is
- **modify** — capture the user's amendment, include modified
- **skip** — exclude from the spec (deferred, not invalidated)
- **mark intentional** — exclude from the spec AND capture the
  user's reasoning so the spec documents the conscious choice

Keep moving. Do not over-discuss any single finding; the user's
attention budget is finite. If a finding sparks a deep
discussion, capture the result and move on.

### Step 6 — Choose spec packaging

Once the walk is done, ask:

- **One spec** — bundle all accepted findings into one
  Superpowers spec. Default for small batches.
- **Split by dimension** — separate bug-fix spec, quality-fix
  spec, refactor spec. Default when accepted findings span
  dimensions and would be naturally executed by different
  workflows.
- **Both** — produce both styles; user picks which to use.

### Step 7 — Output inline spec(s)

Output the spec(s) inline in chat. Suggested structure:

```markdown
# <Title> — bugs / quality / refactor in <area>

**Goal:** <one sentence>

## Findings to address
1. **[Severity]** [Dimension] file:line — <description>
   - Recommended action: <one sentence>
   - <Optional: user's modification or reasoning if marked
     intentional was inverted>
2. ...

## Findings consciously preserved (intentional)
- file:line — <description>. **Reason kept:** <user's reasoning>
- ...

## Suggested sequencing
<Optional: 2-3 sentences on whether to fix in order, parallel,
or in groups>
```

Tell the user this content is ready to feed to
`superpowers:writing-plans` for an executable plan.

## Anti-patterns to avoid

- **Inflating severity to demonstrate value.** A scan that
  returns 12 critical findings on a healthy codebase trains the
  user to ignore future scans. Default conservative.
- **Producing findings without evidence.** Every finding cites
  `file:line`. If you can't, don't surface it.
- **Skipping the per-finding walk for "small" batches.** Even 5
  findings benefit from per-finding judgment. The user's
  domain knowledge is the value-add; collect it.
- **Recommending fixes you'd implement.** This skill is
  read-only. Do not propose code; the spec contains
  *descriptions* of fixes. Superpowers `writing-plans` will
  turn descriptions into code-level plans.
- **Overlapping with factor-architect.** If a scan surfaces
  predominantly architectural concerns, hand off:
  "Most of what I'm seeing is architectural — would you rather
  use `factor-architect` for a focused review?"

## See also

- [`../using-factor-harness/SKILL.md`](../using-factor-harness/SKILL.md)
  — orientation across the four factor-harness skills.
- [`../factor-architect/SKILL.md`](../factor-architect/SKILL.md)
  — narrower architectural review keyed to a plan or feature.
- [`../factor-dedup/SKILL.md`](../factor-dedup/SKILL.md) —
  cross-implementation consolidation.
- [`../_conventions.md`](../_conventions.md) — shared conventions.
- [`../../agents/factor-scanner.md`](../../agents/factor-scanner.md)
  — the subagent this skill dispatches.
