# Artifact formats

Consistent artifact shapes are what make research reusable — an agent months from now must be able to trust a leaf without re-deriving it, and a DECISION must make lateral fallback instant.

## Terminal leaf (`reference/<concept>-<date>.md`)

```markdown
---
type: terminal
status: current            # current | superseded (superseded copies live in _archive)
created: 2026-07-05
updated: 2026-07-05        # == the filename date; means "last verified"
library_version: tokio 1.40   # when it's a library — the sharper staleness signal than the date
confidence: high           # high | medium | low
confidence_basis: cross-checked docs against source; example validated
verified_example: true     # was the example actually run?
assumptions: single-process CLI; no work-stealing needed
sources: [<urls or citations the synthesis drew from>]
origin_prompt: topics/<topic>/prompts/01-tokio.prompt.md   # provenance backlink
---

# <Concept>

## The specific knowledge
The API/pattern/algorithm for the exact use case — written so implementation
reads from here, not from a fresh search.

## Minimal example
A validated snippet for our use case. Where feasible, actually run it and set
verified_example accordingly — a copied-from-docs example that was never run
is a trap, especially across version drift. If validation wasn't feasible,
say so and why.

## Gotchas
Version-specific behavior, edge cases, and pitfalls relevant to us.

## Currency notes
Anything recent (bugs, changes, deprecations) in this version range that
affects usage.
```

Confidence must be **explicit at the leaf** — it's what gets built against. If confidence is low or sources conflicted irreconcilably, say so in the body; in autonomous mode that is a defer trigger, not something to paper over.

## Funnel files (`topics/<topic>/NN-*.md`)

Same frontmatter shape, with `type: exploratory` and `status: open | chosen | rejected`. Status — not tree depth — is what tells a future agent whether a branch is worth re-reading.

## DECISION.md (one per funnel)

```markdown
---
decided: 2026-07-05
status: decided            # open | decided | reopened | retired
---

# Decision: <the question>

## Choice
The named choice. If conditional, state the conditions explicitly:
"A under conditions X; B under conditions Y; C is high-quality and overlaps in Z."
A conditional choice is a legitimate resolution — pretending certainty that the
research didn't support is not.

## Why
The reasoning, grounded in the constraints that were in play.

## Runner-up (ranked)
The explicit next-best option and what would make us switch to it. This is what
makes lateral fallback instant: when the choice fails or is blocked, recovery
starts here — already researched, no new thread, no budget spent.

## Why not the others
One line per rejected option. Negative knowledge prevents re-litigating settled
questions months later.

## Chain
- Prompt: prompts/NN-*.prompt.md
- Framing: prompts/NN-*.framing.md
- Output: NN-*.md
- Leaf(s): ../../reference/<concept>-<date>.md
```

## Prompt and framing files

- `.prompt.md` — the exact final prompt handed to `/deep-research`. Nothing else in the file; a clean provenance record readable in isolation when diagnosing a bad run.
- `.framing.md` — the shaping sub-agent's light-search findings and the constraint set it selected. Kept separate so a bad *prompt* and a bad *framing* can be diagnosed independently — they are different failure modes.

Write ordering: `.framing.md` → `.prompt.md` → run → output `.md` → leaf promotion → `DECISION.md` → update `research/CLAUDE.md`. Each file persists the moment it's produced, so a crash anywhere leaves everything up to that point on disk.
