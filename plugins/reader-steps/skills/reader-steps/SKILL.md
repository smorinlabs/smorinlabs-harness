---
name: reader-steps
description: Render actions only the READER can or will perform as concrete, self-contained task blocks — numbered verb-first steps with exact commands/paths/values, a done-so-far recap line, a ✓ verification clause per step, inline mentions restated in full, no tangents, closing with the immediate next move — plus cross-turn restating of in-flight manual processes and matter-of-fact error shape (cause + fix). Fire on request — "format the manual steps", "what do I need to do by hand", "what's left for me" — and when composing any handoff containing agent-impossible actions (interactive auth, UI clicks, approvals in external systems), manual verification steps, or work the user claimed for themselves. Decisions are not steps — anything needing the user's judgment is asked (question-walkthrough) before instructing; only settled work becomes instructions. This skill is the canonical spec; users typically keep an always-on digest of it in their global instructions so it applies unprompted.
---

# reader-steps

When the work crosses to the human — actions the agent can't do, verification
needing eyes, steps the user claimed — render it so it can be executed from
the block alone: concrete, bounded, verifiable, nothing held in memory.

## When it applies

Three trigger classes; any one activates the block:

1. **Agent-impossible actions** — interactive auth, UI clicks, approvals in
   external systems, physical-world steps, anything sandbox/permissions block.
2. **Manual verification handoffs** — end-of-task "prove it works" steps
   needing human eyes.
3. **User-claimed work** — steps the user said they'll do themselves. Once
   claimed, rendered like any reader task, never a vague reminder.

**Not a trigger — decisions.** Anything needing the user's judgment is a
*question*: ask it (AskUserQuestion; a pile of them → question-walkthrough).
When a response holds both, decisions resolve first; only settled work
becomes instructions.

**Concreteness is the gate.** The rules below are hard defaults wherever
actions can be concrete. Where they genuinely can't be yet, say what's known
and what's missing — never fabricate precision.

## The block — seven rules

1. **Toward the end, under a scannable header** (e.g. "Your steps") — after
   the analysis it follows from, in the response's closing region.
2. **Opens with a one-line recap of work already done**, so the tasks stand
   alone without scrolling. *"Done so far: OAuth app created, secrets set."*
3. **Numbered, verb-first, one bounded action per step** — no step contains
   "and then" twice; the action leads, context trails inside the step.
4. **Very specific** — exact commands, paths, URLs, values, line numbers.
   "Update the config" is not a step.
5. **Self-contained** — no "as mentioned above", no "keep in mind"; an
   instruction that appeared inline in prose is restated in full here. The
   block alone is sufficient.
6. **Verification clause per step** (or one closing the block when steps
   verify together): *"✓ exits 0, prints the new scopes"*. No time
   estimates; no cap on item count.
7. **No tangents inside the block; it closes with the immediate next move.**
   Side-observations live outside it or become an offered follow-up.

## Across turns

While a manual process is in flight, every later turn **restates the live
instruction itself** — never "now do the next thing" — plus position:

> Steps 1–2 done (callback set, token refreshed). You're on 3 of 4: run
> `gh api user/orgs` — ✓ your org list includes your org.

When the last step is confirmed, say so explicitly ("all 4 reader steps
confirmed") — a multi-turn process gets a visible close, not a trail-off.

## Error shape

Errors — including a failed reader step — are stated matter-of-factly:
**cause and fix**, no dramatization, no hedging filler; a failed step gets
its corrected form restated, not the whole block rerun.

> Test fails at `auth.spec.ts:42`: expected 200, got 401. Cause: missing
> auth header. Fix: add `Authorization: Bearer ${token}` to the request.

## Red Flags

| Thought | Reality |
|---|---|
| "I mentioned it inline, that's enough" | Inline mentions are context, not instructions. Restate in the block. |
| "They'll remember we're on step 3" | Restate the live instruction with position, every turn. |
| "This choice can be step 2" | Decisions are asked, never listed as steps. |
| "Steps can't be exact yet, I'll approximate" | Don't fabricate precision — name what's missing instead. |
| "Quick 'by the way' inside the block" | Tangents outside the block, always. |

## See also

- `question-walkthrough` — the decisions counterpart; asks what this skill
  must never list.
- `manual-test-guide` — full manual *testing* procedures on request; a
  verification handoff here can point to it for depth.
- `explain` (steps mode) — on-request operator instructions; shares this
  anatomy.
