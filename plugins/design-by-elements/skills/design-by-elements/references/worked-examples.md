# Worked examples

Four examples of the method in practice, drawn from the session that produced it
(redesigning a terminal session-recap output). Read them to see how each move
looks concretely; they are illustration, not procedure.

## Example 1 — feedback → named rules (move 5)

One review pass over a single facts block produced six line-grammar rules, each
now law across the whole artifact. This is move 5 in action: a comment becomes a
rule, not an edit.

- **LG1 — annotate only when non-obvious.** `value — annotation`, and the
  annotation must say something the value doesn't. `#212 — open, changes
  requested` passes; `feat/billing-metering — feature branch` fails (the branch
  name already says it's a branch).
- **LG2 — status is a colored dot + plain words.** `🔴 failing` / `🟢 passing`,
  never glyph stacks.
- **LG3 — no unglossed symbols.** `§Rollup` → `— "Rollup" section`.
- **LG4 — hanging indent.** Wrapped text aligns under content, never under labels.
- **LG5 — provenance by zone.** One footer line ("Live state checked just now")
  instead of per-line markers; only inference gets marked inline.
- **LG6 — self-explanatory prompts.** Every ID is glossed where it appears; a
  zero-context reader can act on the line alone.

LG1 and LG6 are the same test at two scales: *could the reader act on this line
alone?* Naming both makes the test enforceable everywhere.

## Example 2 — decisions-log excerpt (move 4)

The running `Fork | Decision | Rationale` table. Each row is one lock; the
rationale column is what keeps a locked element from silently reopening.

| Fork | Decision | Rationale |
|------|----------|-----------|
| URL placement | Always an indented line below the fact (B2) | Fact line stays human; label-column scanning never crosses a URL. |
| Plan-spine form | Enriched table `Plan item / What it is / Status` (C1); compact label+sentence fallback (C2c) for ≤3 items | Names must survive — a `3/6 ✅✅✅🔄⬜⬜` compression hid what the items *were*. |
| Prompt header | `▶ Prompt — paste this to <outcome>:` (Dh1) | Announces THAT it's a prompt and what pasting it buys, before the body. |
| Column set | Anchors in-cell, not a fifth column | Density rule: sparse facts don't earn a column. |

## Example 3 — element decomposition with locks (moves 2 + 4)

A "stream block" decomposed into five elements, each iterated and locked one at a
time, with spacing between them part of each lock:

1. **header** — `▸ 🎯 P07 · Billing v2 — usage-based pricing [milestone]`
2. **description** — 1–3 plain sentences.
3. **facts block** — aligned labels, where-first order: Repo · Branch · PR · CI ·
   Local changes · Spec · Ticket.
4. **plan spine** — from a named source ("Plan — from PROJECTS.md P07").
5. **launch prompt** — Dh1 header + glossed body.

Each element got contrasting variants first (A1/A2 for order; B1–B3 for URLs;
C1/C2a–d for plan forms; Da–Dh3 for prompt headers), then a lock.

## Example 4 — scale probing (companion principle)

The same design was stress-rendered at three scales *before* locking, to prove it
scales up and down:

1. a sparse single-item stream;
2. a busy multi-anchor stream — **the real test: a layout must get *better* under
   load, not worse**;
3. a multi-day, multi-milestone session — zoomed out to a milestone table with a
   repo column and full PR URLs.

A variant that degraded under load (a run-on metadata strip) was eliminated
*because* of the busy render — a defect the single-item render never would have
exposed.
