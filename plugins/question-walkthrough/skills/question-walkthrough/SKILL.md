---
name: question-walkthrough
description: Walk a pile of open questions or undecided to-dos one at a time via the AskUserQuestion tool — smartest question first, just-enough context per item, and after EVERY answer re-evaluate the remaining pile (drop what became moot, reorder what changed, surface implied follow-ups). Sources it handles — mine open questions from the current conversation, read them from a document the user points at (PRD, design doc, notes), take a list given inline, or pull undecided items from task systems (tasks, PROJECTS.md). Decisions are recorded back at their source. Use when the user says "go through these one by one", "walk me through the open questions", "there's a bunch of to-dos, help me decide", "triage these decisions with me", or a doc/plan is blocked on several unanswered questions. Not for scoping a project idea (project-refine), not for batch shareable decision pages (html-codesign — offer it if they'd rather review async), and context style defers to the explain skill's anatomy.
---

# question-walkthrough

Turn a pile of undecided things into a sequence of single, well-framed
decisions — one AskUserQuestion at a time, each non-obvious question fronted
by a pre-read, with the pile re-planned after every answer.

> **NO NON-OBVIOUS QUESTION WITHOUT ITS PRE-READ DELIVERED — AND THE TURN
> ENDED — FIRST.** Prose in the same turn as an AskUserQuestion call may
> **never render at all**: the user receives only the question UI (confirmed
> repeatedly in the field). Same-turn context is invisible context. Two rules
> follow, one per turn:
>
> - **The delivering turn** — the pre-read is a TURN-ENDING message: the
>   prose is the turn's final content, with **no tool call of any kind after
>   it**. Wanting to call a tool after the prose is the violation signal —
>   that call opens the NEXT turn instead. The user's reply is what proves
>   the pre-read was in hand.
> - **The asking turn** — a turn that calls AskUserQuestion contains **no
>   prose the user needs**. Anything they must read either ended a previous
>   turn or lives inside the dialog itself (question body, option labels and
>   descriptions — the one channel that always renders).
>
> This governs every prose delivery in the walk — pile lists, sequencing
> rationale, re-evaluation narration, batch reports — not just pre-reads.
>
> No exceptions: not "it's in the question text", not "I put it right above
> the tool call", not "just one quick tool call after the pre-read", not
> "the option descriptions carry the trade-offs".
>
> Violating the letter of this rule is violating the spirit of it.

## Workflow

1. **Intake.** Identify the source: the conversation (mine it for options
   floated but never chosen, explicit "we still need to decide X", deferred
   items), a document path, an inline list, or task systems. Ambiguous →
   ask which — the listing of what you'd mine from each source lives inside
   the dialog itself, one option per source with the mining plan as its
   description; the asking turn needs no prose.
2. **Confirm the pile before walking.** Present the harvested questions as a
   numbered list (one line each) — a turn-ending message, no tool call after
   it. The user's reply prunes, adds, or confirms; raise a confirmation
   dialog in the next turn only if the reply is ambiguous. Never walk an
   unconfirmed pile — mining errors compound across a whole session.
3. **Sequence.** Order by leverage, not by original order:
   - questions whose answer could **eliminate or reshape others** go first;
   - then by impact on the work at hand;
   - related questions adjacent, so context carries over;
   - quick factual confirmations early only when they unblock later framing.
   Say the order you chose and why in one line — on a turn-ending message
   (it rides the pile confirmation or the first pre-read), so the user can
   reorder before the first dialog fires.
4. **Walk — pre-read turn, then question turn.** For each question:
   - **any question that isn't simple or obvious gets a pre-read**: why this
     question exists, the impact of the choice, trade-offs, pros and cons,
     terms the user may not know. The standard is sufficiency — whatever
     makes the decision easy to understand and make, nothing more
     (explain-skill anatomy: anchored, just-enough);
   - **the pre-read ends its turn** (the Iron Law above). Deliver it as
     plain chat text and stop — no tool call of any kind after it,
     AskUserQuestion included. The user reads at their own pace; their
     reply — "go", a question back, a correction — opens the turn that
     asks. Questions back and corrections are resolved before the dialog
     is raised;
   - steady-state cadence: the pre-read for the next question rides at the
     end of the turn that processed the previous answer — record and
     re-evaluate first, then the pre-read, then the turn ends. One
     round-trip per question, with the pre-read always in hand;
   - simple or obvious questions skip the pre-read and go straight to the
     dialog — that is what keeps the walk fast — but only when the turn
     carries nothing else the user needs to read (see step 6). When in
     doubt, pre-read;
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
   body — dialog-internal, so it renders without a prior turn. Queued is the
   default timing for directives; execute immediately only when the note
   says so ("now", "first") or the walk cannot sensibly continue without it.
6. **Re-evaluate after every answer** — this is the skill's core:
   - **drop** questions the answer mooted, saying which and why;
   - **reorder** if the answer changed what's now highest-leverage;
   - **add** follow-ups the answer implies (confirm additions — the pile
     only grows with consent);
   - keep a running tally: decided · dropped · parked · queued · remaining;
   - narration follows the delivery rule: drops, adds, reorders, and tally
     changes are prose the user must see, so the turn that carries them
     ENDS before the next dialog — even when the next question is simple
     enough to need no pre-read. Only a nothing-changed continuation may go
     straight to the next dialog.
7. **Record at the source.** Doc-sourced → write the decision into the doc
   beside its question (e.g. `**Decision (YYYY-MM-DD):** …`); task-sourced →
   update the task/PROJECTS row; conversation/inline → nothing to edit.
8. **End-of-walk batch, then parked items.** Execute the queued directives
   in order, reporting each as it lands — the batch report is a turn-ending
   message, and the first re-ask dialog opens the next turn. Then one final
   pass over parked questions — redirects whose work just ran are re-asked,
   re-framed where the work changed them. Close with the summary table: each
   question, its outcome (decided/dropped/parked), the one-line decision —
   and each directive with its outcome. Anything still parked is marked
   open, with where it lives.

## Red Flags

| Thought | Reality |
|---|---|
| "I'll put the pre-read right above the tool call — same message" | Same-turn prose may never render at all: the user gets only the question UI. The pre-read ends its turn; the question waits for the user's reply. |
| "The pre-read is written — one quick tool call before I end the turn" | Any tool call after the prose un-ends the turn and buries it. The pre-read is the turn's final content; the next tool call opens the next turn. |
| "It's not a pre-read, just a status line above the dialog" | Same turn, same invisibility. The asking turn carries no prose the user needs. |
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
