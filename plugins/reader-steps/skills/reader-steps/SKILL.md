---
name: reader-steps
description: Render actions only the READER can or will perform as a delineated, self-contained task block — a bounded frame (rail + rules) carrying what it completes, steps numbered with a stable tag, grouped by surface (terminal, browser, desktop/system UI, phone, physical world), each step titled by its outcome with the literal command or UI path below it and a ✓ verification line, closing with the immediate next move. Scales down to one line for a single step and up with a map and stop points for long sequences; re-renders in-flight processes across turns as a scoreboard; states errors as cause and fix. Fire on request — "format the manual steps", "what do I need to do by hand", "what's left for me" — and when composing any handoff with agent-impossible actions, manual verification, or work the user claimed. Decisions are not steps — anything needing the user's judgment is asked (question-walkthrough) before instructing. Canonical spec behind an always-on digest kept in global instructions.
---

# reader-steps

When work crosses to the human, render it so it can be executed from the
block alone: bounded, ordered, concrete, verifiable, nothing held in memory.

Worked renders at every scale, divider forms, and navigation examples live in
`references/formats.md` — read it when composing a block bigger than three
steps or spanning surfaces.

## When it applies

Three trigger classes; any one activates the block:

1. **Agent-impossible actions** — interactive auth, UI clicks, approvals in
   external systems, physical-world steps, anything sandbox/permissions block.
2. **Manual verification handoffs** — "prove it works" steps needing eyes.
3. **User-claimed work** — steps the user said they'd do themselves.

**Not a trigger — decisions.** Anything needing the user's judgment is a
*question*: ask it (AskUserQuestion; a pile → question-walkthrough). When a
response holds both, decisions resolve first; only settled work becomes
instructions.

**Concreteness is the gate.** These rules are hard defaults wherever actions
can be concrete. Where they can't be yet, say what's known and what's
missing — never fabricate precision.

## Notation

| Signal | Means |
|---|---|
| `mono` | You **type** it, paste it, or a machine returns it verbatim |
| **bold** | A UI label you **click or look for** (button, menu item, field, app) |
| ▸ | One navigation hop inside an interface |
| ▶ | The step to start with |
| ✓ | How you know the step worked |

**The load-bearing rule: mono = fingers on keyboard, bold = eyes and mouse.**

**Surfaces:** ⌨️ terminal · 🌐 browser · 🖥️ desktop app or system UI ·
📱 phone · 🖐️ physical world. Icons ride on the group dividers, plus on any
line that departs from its group's surface.

## The scale ladder

| Size | Form |
|---|---|
| 1 step | Inline: `▶ Your step · <icon>` + action + ✓. No frame, count, tag, divider, or footer. Add why it's yours. |
| 2–3 steps, one surface | Light: one bold header line, plain numbers, icons on steps, one-line footer. No rules, no dividers. |
| 4+ steps, or 2+ surfaces | Full block (below). |
| 8+ steps | Full block **plus** a `Map:` line, a `Stop points:` line, and step ranges on dividers. |

## The full block

Wrapped in a blockquote — the rail is the container; the horizontal rules are
internal separators between header, steps, and footer.

1. **Header:** `YOUR STEPS ▼ · <what> · 0/N · [tracked-id] · tag XX`, fenced
   above and below by a rule.
2. **Binding:** a `Completes:` line naming the tracked item **by its exact ID
   and title** plus what finishing unblocks, then `Done so far by me:`.
3. **Groups:** steps grouped by surface, in execution order, under a merged
   divider — `— 🌐 in the browser · install the app on the repo —` (add the
   step range at 8+ steps). Split the intent onto its own line only when it
   needs more than ~6 words.
4. **Steps:** `**XX.n · <outcome title>**`, the literal command or UI path
   indented below, then the indented `✓` line. **Titles state the outcome in
   your words, never echo the button label** — that is what keeps title and
   body from repeating each other. Promote `✓` to `Done when:` for steps whose
   success is ambiguous or expensive to get wrong.
5. **Footer:** a closing rule, then `▲ That's all N — start with ▶ XX.1`, plus
   what happens once they're done.

**Self-containment:** anything mentioned inline earlier in the response is
restated in full inside the block. No "as mentioned above", no "keep in mind".
No tangents inside the block. No time estimates.

**Consistency (verify before sending):** the header count, the footer count,
and the number of steps are the same N; every ID in the footer or in prose is
quoted exactly as declared.

## Navigation and reactive steps

- **Breadcrumb by default**: **System Settings** ▸ **General** ▸ **Sharing**.
  Promote to one hop per numbered line when the chain exceeds ~3 hops or any
  hop carries a decision or caveat. Micro-steps use plain numbers and are
  referenced as "XX.1, hop 4".
- **Reactive actions** (a phone prompt during a terminal command) are a line
  *inside* the step that triggers them, marked with their own surface icon —
  never a sequential step, which would tell the reader to do it at the wrong
  time.

## Across turns

While a process is in flight, re-render the block as a scoreboard rather than
saying "do the next thing": done steps collapse to a single `✅` line with
their outcome, the live step keeps `▶` and full detail, pending steps dim to
`⬜` one-liners, and the header count advances. When the last step confirms,
say so explicitly — a multi-turn process gets a visible close.

## Error shape

Errors — including a failed reader step — are stated matter-of-factly:
**cause and fix**, no dramatization, no hedging filler. A failed step gets its
corrected form restated; the whole block is not rerun.

> Test fails at `auth.spec.ts:42`: expected 200, got 401. Cause: missing auth
> header. Fix: add `Authorization: Bearer ${token}` to the request.

## Red Flags

| Thought | Reality |
|---|---|
| "I mentioned it inline, that's enough" | Inline mentions are context, not instructions. Restate in the block. |
| "Title it after the button" | Titles state the outcome; echoing the label creates the redundancy. |
| "The phone approval is the next step" | Reactive actions live inside the step that triggers them. |
| "They'll remember we're on step 3" | Re-render the scoreboard with the live instruction, every turn. |
| "This choice can be step 2" | Decisions are asked, never listed as steps. |
| "One step still deserves the full frame" | At one step the frame is ceremony. Collapse to the inline form. |
| "I added a step; the count is close enough" | Header, footer, and step count are one number. A wrong count kills the closure signal. |

## See also

- `question-walkthrough` — the decisions counterpart; asks what this must never list.
- `manual-test-guide` — full manual *testing* procedures on request.
- `explain` (steps mode) — on-request operator instructions; shares this anatomy.
