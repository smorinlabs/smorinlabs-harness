# GitHub markdown auto-anchor rules

When you write `## Section Title` in a markdown file, GitHub (and most renderers) auto-generate an anchor you can link to from the same or another file. Phase 6 of the merge workflow relies on these anchors to cross-reference between consolidated docs without manually managing IDs.

## The rules

1. **Lowercase everything.** `## My Section` → `#my-section`.
2. **Spaces become hyphens.** `## My Long Section` → `#my-long-section`.
3. **Em-dash with surrounding spaces collapses to a single hyphen.** `## A — B` → `#a--b` becomes `#a-b` after collapse. **This is the single most common gotcha.** If a section title contains an em-dash with spaces around it, the auto-anchor is one hyphen, not two or three.
4. **En-dash same rule.** `## A – B` → `#a-b`.
5. **Punctuation is stripped.** `## Section 1.2: Topic!` → `#section-12-topic`. Periods, colons, exclamation marks, question marks all drop.
6. **Parentheses, brackets, braces drop.** `## Function (Variant)` → `#function-variant`.
7. **Slashes drop.** `## Reads/Writes` → `#readswrites` (no hyphen between).
8. **Apostrophes and quotes drop.** `## What's New` → `#whats-new`.
9. **Backticks drop.** `## The `useEffect` Hook` → `#the-useeffect-hook`.
10. **Numbers preserved.** `## 4.5 The JSON Payload` → `#45-the-json-payload`.

## Cross-file linking

```markdown
[See implementation § 5.4](implementation.md#54-the-resolution-middleware)
```

The fragment after `#` follows the same rules as same-file anchors.

## Verifying anchors after a merge

After completing the merge, grep for cross-references and verify each one resolves:

```bash
# Find all in-doc cross-refs
grep -rE "\]\([^)]+\.md#[^)]+\)" <consolidated-dir>/

# For each, check that the target heading exists in the target file
# (this is a manual or scripted check — there's no built-in linter)
```

If a section title changes during the merge, every cross-reference to it breaks. **Rename heading → grep for old anchor → update all references** is the workflow.

## Common bugs caught by reviewers

- `#54-the-special-json-payload--how-gcp-interprets-your-stdout` (double-dash from "—") instead of `#54-the-special-json-payload-how-gcp-interprets-your-stdout` — collapsed em-dash.
- Forgetting that periods drop: `#section-1.2` doesn't work; it's `#section-12`.
- Backticks in titles: `\`useEffect\` Hook` becomes `#useeffect-hook`, not `#use-effect-hook` or `#-useeffect--hook`.
