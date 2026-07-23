---
name: question-walkthrough
description: Walk a pile of open questions or undecided to-dos one at a time via the AskUserQuestion tool — smartest question first, just-enough context per item, and after EVERY answer re-evaluate the remaining pile (drop what became moot, reorder what changed, surface implied follow-ups). Sources it handles — mine open questions from the current conversation, read them from a document the user points at (PRD, design doc, notes), take a list given inline, or pull undecided items from task systems (tasks, PROJECTS.md). Decisions are recorded back at their source. Use when the user says "go through these one by one", "walk me through the open questions", "there's a bunch of to-dos, help me decide", "triage these decisions with me", or a doc/plan is blocked on several unanswered questions. Not for scoping a project idea (project-refine), not for batch shareable decision pages (html-codesign — offer it if they'd rather review async), and context style defers to the explain skill's anatomy.
---

# question-walkthrough

Turn a pile of undecided things into a sequence of single, well-framed
decisions — one AskUserQuestion at a time, each non-obvious question fronted
by a pre-read, with the pile re-planned after every answer.

> **NO NON-OBVIOUS QUESTION WITHOUT ITS PRE-READ DELIVERED — AND THE TURN
> ENDED — FIRST.** Text bundled in the same turn as an AskUserQuestion call
> does not function as context: the dialog takes over before the text is
> read. Same-turn context is invisible context. The pre-read is a chat
> message that ENDS its turn; the question fires in the NEXT turn, after
> the user has replied with the pre-read actually in hand.
>
> No exceptions: not "it's in the question text", not "I put it right above
> the tool call", not "the option descriptions carry the trade-offs".
>
> Violating the letter of this rule is violating the spirit of it.

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
4. **Walk — pre-read turn, then question turn.** For each question:
   - **any question that isn't simple or obvious gets a pre-read**: why this
     question exists, the impact of the choice, trade-offs, pros and cons,
     terms the user may not know. The standard is sufficiency — whatever
     makes the decision easy to understand and make, nothing more
     (explain-skill anatomy: anchored, just-enough);
   - **the pre-read ends its turn** (the Iron Law above). Deliver it as
     plain chat text and stop — no AskUserQuestion in the same turn, ever.
     The user reads at their own pace; their reply — "go", a question back,
     a correction — opens the turn that asks. Questions back and corrections
     are resolved before the dialog is raised;
   - steady-state cadence: the pre-read for the next question rides at the
     end of the turn that processed the previous answer — record and
     re-evaluate first, then the pre-read, then the turn ends. One
     round-trip per question, with the pre-read always in hand;
   - simple or obvious questions skip the pre-read and go straight to the
     dialog — that is what keeps the walk fast. When in doubt, pre-read;
   - the question body stays terse — what's being decided and the concrete
     consequence, compressed; the pre-read carries the weight;
   - options wherever candidates exist, recommendation first and marked
     "(Recommended)" with the reasoning in its description; per-option
     trade-offs live in option descriptions, not the question body;
   - previews when options are concrete artifacts (code shapes, formats);
   - the built-in Other is the escape hatch;
   - "skip" parks the item (revisit at the end); "stop" ends the walk with a
     partial summary.
5. **Notes are read, classified, and honored — never dropped.** Every note on
   an answer is one of three things:
   - **modifier** — it reshapes the chosen option ("pick A, but rename it"):
     apply it to the decision immediately;
   - **directive-extra** — an instruction beyond the answer ("…and also
     update the doc"): repeat the interpretation back in one line, get a
     quick confirm, then queue it for the end-of-walk batch;
   - **directive-redirect** — the note replaces the answer ("instead of
     answering, go check X first"): repeat back + confirm, queue the work,
     park the question; it returns after the batch runs — re-framed if the
     work changed it — unless the work mooted it.
   The repeat-back is one line and lives inside the confirm question's own
   body — short enough that no pre-read turn is needed for it. Queued is the
   default timing for directives; execute immediately only when the note
   says so ("now", "first") or the walk cannot sensibly continue without it.
6. **Re-evaluate after every answer** — this is the skill's core:
   - **drop** questions the answer mooted, saying which and why;
   - **reorder** if the answer changed what's now highest-leverage;
   - **add** follow-ups the answer implies (confirm additions — the pile
     only grows with consent);
   - keep a running tally: decided · dropped · parked · queued · remaining.
7. **Record at the source.** Doc-sourced → write the decision into the doc
   beside its question (e.g. `**Decision (YYYY-MM-DD):** …`); task-sourced →
   update the task/PROJECTS row; conversation/inline → nothing to edit.
8. **End-of-walk batch, then parked items.** Execute the queued directives
   in order, reporting each as it lands; then one final pass over parked
   questions — redirects whose work just ran are re-asked, re-framed where
   the work changed them. Close with the summary table: each question, its
   outcome (decided/dropped/parked), the one-line decision — and each
   directive with its outcome. Anything still parked is marked open, with
   where it lives.

## Red Flags

| Thought | Reality |
|---|---|
| "I'll put the pre-read right above the tool call — same message" | Same-turn text is unread text: the dialog takes over first. The pre-read ends its turn; the question waits for the user's reply. |
| "An extra round-trip per question is too slow" | The round-trip is the only proof the pre-read was seen. Speed comes from skipping pre-reads on obvious questions and riding the next pre-read on the previous answer's turn — never from bundling. |
| "The question body can carry the context" | Non-obvious questions get a pre-read turn first — the dialog is too small a channel for impact, trade-offs, and terms. |
| "More context = better framing" | The pre-read standard is sufficiency, not volume — whatever makes the decision easy, nothing more. Padding stalls the walk. |
| "The note is just color — I'll fold it into the option" | Classify first. A directive folded into an option tweak is an instruction dropped. |
| "The note says do X — I'll do it right now" | Repeat back, confirm, queue. The end-of-walk batch is the default; immediate only when the note says so. |
| "I'll batch three related questions into one message" | One question per message. Related = adjacent, never merged. |
| "The pile is obvious, skip confirmation" | Mining errors compound over a whole walk. Confirm first. |
| "That answer probably moots Q4, I'll silently drop it" | Drop loudly — name the question and the reason, or the user loses the thread. |
| "The user skipped it, so it's resolved" | Parked ≠ decided. It returns in the final pass and the summary. |

## See also

- `explain` — owns the context anatomy this skill frames questions with.
- `project-refine` — scoping/decomposing a *project idea*; a walkthrough that
  keeps converging on one project's shape belongs there.
- `html-codesign` — the async sibling: a shareable decision *page* instead of
  a live dialog. Offer it when the user wants to review alone or share.
- `project-audit` / `project-next` — task-state truth; this skill only walks
  what they surface, it doesn't audit.
