---
name: question-walkthrough
description: Walk a pile of open questions or undecided to-dos one at a time via the AskUserQuestion tool — smartest question first, just-enough context per item, and after EVERY answer re-evaluate the remaining pile (drop what became moot, reorder what changed, surface implied follow-ups). Sources it handles — mine open questions from the current conversation, read them from a document the user points at (PRD, design doc, notes), take a list given inline, or pull undecided items from task systems (tasks, PROJECTS.md). Decisions are recorded back at their source. Use when the user says "go through these one by one", "walk me through the open questions", "there's a bunch of to-dos, help me decide", "triage these decisions with me", or a doc/plan is blocked on several unanswered questions. Not for scoping a project idea (project-refine), not for batch shareable decision pages (html-codesign — offer it if they'd rather review async), and context style defers to the explain skill's anatomy.
---

# question-walkthrough

Turn a pile of undecided things into a sequence of single, well-framed
decisions — one AskUserQuestion at a time, with the pile re-planned after
every answer.

## Workflow

1. **Intake.** Identify the source: the conversation (mine it for options
   floated but never chosen, explicit "we still need to decide X", deferred
   items), a document path, an inline list, or task systems. Ambiguous →
   ask which, listing what you'd mine from each.
2. **Confirm the pile before walking.** Present the harvested questions as a
   numbered list (one line each). The user prunes/adds via notes. Never walk
   an unconfirmed pile — mining errors compound across a whole session.
3. **Sequence.** Order by leverage, not by original order:
   - questions whose answer could **eliminate or reshape others** go first;
   - then by impact on the work at hand;
   - related questions adjacent, so context carries over;
   - quick factual confirmations early only when they unblock later framing.
   Say the order you chose and why in one line — the user can reorder.
4. **Walk — one AskUserQuestion per item.** For each question:
   - context first, in the question text: what this is, why it matters *now*,
     and the concrete consequence of the choice — explain-skill anatomy
     (just-enough, anchored in a real example), never a wall of background;
   - options wherever candidates exist, recommendation first and marked
     "(Recommended)" with the reasoning in its description; trade-offs live
     in option descriptions, not the question body;
   - previews when options are concrete artifacts (code shapes, formats);
   - the built-in Other is the escape hatch; **notes always modify the
     chosen option — apply them, never drop them**;
   - "skip" parks the item (revisit at the end); "stop" ends the walk with a
     partial summary.
5. **Re-evaluate after every answer** — this is the skill's core:
   - **drop** questions the answer mooted, saying which and why;
   - **reorder** if the answer changed what's now highest-leverage;
   - **add** follow-ups the answer implies (confirm additions — the pile
     only grows with consent);
   - keep a running tally: decided · dropped · parked · remaining.
6. **Record at the source.** Doc-sourced → write the decision into the doc
   beside its question (e.g. `**Decision (YYYY-MM-DD):** …`); task-sourced →
   update the task/PROJECTS row; conversation/inline → nothing to edit.
   In every case, end with the summary table: each question, its outcome
   (decided/dropped/parked), and the one-line decision.
7. **Parked items.** Offer one final pass over skipped questions; anything
   still parked lands in the summary marked open, with where it lives.

## Red Flags

| Thought | Reality |
|---|---|
| "I'll batch three related questions into one message" | One question per message. Related = adjacent, never merged. |
| "The pile is obvious, skip confirmation" | Mining errors compound over a whole walk. Confirm first. |
| "That answer probably moots Q4, I'll silently drop it" | Drop loudly — name the question and the reason, or the user loses the thread. |
| "More context = better framing" | Context is just-enough and anchored (explain's rule). Long preambles stall the walk. |
| "The user skipped it, so it's resolved" | Parked ≠ decided. It returns in the final pass and the summary. |

## See also

- `explain` — owns the context anatomy this skill frames questions with.
- `project-refine` — scoping/decomposing a *project idea*; a walkthrough that
  keeps converging on one project's shape belongs there.
- `html-codesign` — the async sibling: a shareable decision *page* instead of
  a live dialog. Offer it when the user wants to review alone or share.
- `project-audit` / `project-next` — task-state truth; this skill only walks
  what they surface, it doesn't audit.
