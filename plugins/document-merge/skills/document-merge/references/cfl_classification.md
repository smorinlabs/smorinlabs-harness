# When is a decision CFL-worthy?

The standing rule from real-world use: **every non-trivial synthesis, conflict, or judgment call.** This file expands on what "non-trivial" means so the model classifies consistently.

## Always log a CFL entry

These are the unambiguous triggers — if any of these is true, log it.

1. **Sources disagree on a fact, recommendation, or value.** Different version pins, different recommended defaults, different counts/numbers. Log both excerpts and the chosen version.
2. **Two or more sources cover the same topic with different framing or emphasis, and the merged version blends them.** Log the synthesis even if no factual conflict exists — future readers need to see what came from where.
3. **A source provides unique content that doesn't fit cleanly into any output section.** Log the inclusion judgment (where it landed and why).
4. **A source provides content that is fully duplicated by another source, and you chose which version to keep verbatim.** Even with no factual conflict, the choice matters for traceability.
5. **A version pin, naming choice, or configuration default is taken from one source over another.** These are the kinds of decisions that surface as bugs months later — log them so the user can audit.
6. **A non-obvious cross-reference replaces inline content.** When § 5.4 says "see § 2.1" instead of repeating, log why.
7. **Same content was synthesized from 3+ sources.** Even if all three agree, the merged version is a synthesis — log the sources used.

## Never log (handle silently)

- **Identical text across sources** — keep verbatim, no entry needed.
- **Pure formatting normalization** (e.g., aligning code-block syntax across sources).
- **Removing duplicate paragraphs that are word-for-word identical.**
- **Trivial wording adjustments (sentence smoothing) that change no fact.**

## Borderline cases

Default to logging if in doubt. The cost of an extra log entry is small; the cost of a silent judgment is high.

- **Choosing source A's wording over source B's wording when both are close to identical**: log only if the wording difference encodes a different emphasis or implication. Pure stylistic preference can be silent.
- **Reordering bullet points from a source**: silent unless the new order changes meaning.
- **Splitting a long source paragraph across two output sections**: log only if the split required a judgment about where the topic boundary is.

## Entry classification (for the `Type:` field)

Use one of these labels — they make the log easier to scan:

| Type | When |
|------|------|
| `Synthesis judgment` | Multiple sources blended into one paragraph; no factual conflict, but the merged version isn't a quote of any single source. |
| `Conflict resolution` | Sources disagreed on a fact, recommendation, or value. |
| `Version pin` | A library/runtime version was chosen from one source over another. |
| `Naming choice` | A function/variable/section name was chosen from one variant over another. |
| `Cross-reference choice` | Inline content was replaced with a pointer to another section. |
| `Inclusion/exclusion judgment` | Decided to include (or omit) source content that didn't have an obvious home. |

## Marker placement

Place the inline marker at the **end** of the synthesized block, not the start. Readers should see the content first, then the audit pointer. Reviewers will catch start-placement and require a fix — save the round-trip by getting it right the first time.

Format: `<!-- CONFLICT: CFL-XXX -->` (HTML comment, invisible in rendered markdown, greppable in source).

## ID hygiene

- IDs are zero-padded three digits: `CFL-001`, `CFL-002`, ..., `CFL-099`, `CFL-100`.
- IDs are write-once and gap-free. If you assign CFL-007 and then realize the entry should be deleted, leave the ID retired with a one-line `**Status:** Withdrawn — <reason>` note instead of renumbering.
- Once a marker is in a merged doc, its ID never changes.
