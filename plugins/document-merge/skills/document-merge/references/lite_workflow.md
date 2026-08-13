# Lite workflow (2 sources, low conflict)

When the user has only 2 markdown files to merge and there's no real conflict to track (e.g., merging two README variants, two outline drafts, two notes from the same meeting), the full 8-phase workflow is overkill.

The lite path:

1. **Snapshot.** Capture SHA-256 of both source files (still important — you'll archive originals).
2. **Read both** in full.
3. **Pick the structural skeleton** from the source that has better organization, OR propose a merged outline if neither dominates.
4. **Merge inline.** For each section, take the more complete/clearer version, append unique content from the other.
5. **Write a short diff report** listing:
   - What was deduplicated (which paragraphs from B were dropped because A already covered them)
   - What was kept from each source uniquely
   - Any wording choices where the two versions disagreed
6. **Archive originals** to the user's chosen archive dir, verify byte-identical.
7. **Commit.**

No CFL log, no validation script, no topic-to-source map, no coverage audit. The diff report is the audit trail.

## Switch to full workflow when

- Sources actually conflict on a fact, recommendation, or value (not just wording)
- One or both sources are >500 lines
- The user says "I want to be able to audit every decision"
- A third source is added mid-merge

## Diff report template

```markdown
# <Topic> Merge Report

**Date:** YYYY-MM-DD
**Sources:**
- `<source-a.md>` (NN lines)
- `<source-b.md>` (NN lines)

**Output:** `<output.md>`
**Archive:** `<archive-dir>/`

## What was deduplicated
- Source B's "<section>" paragraph dropped — fully duplicated by source A.
- ...

## What was kept uniquely from each
- From A: <bullets>
- From B: <bullets>

## Wording choices
- <if any non-trivial choices were made, list them with both versions>

## SHA-256 verification
Pre-merge baseline matches post-archive sums (zero diff).
```
