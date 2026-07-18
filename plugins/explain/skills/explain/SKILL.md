---
name: explain
description: >
  Explain anything in a concrete-anchored style — succinct, just-enough
  context, always grounded in a real example, inline in chat. Use when the
  user invokes /explain, or asks in their own words: "explain X", "help me
  understand", "give me a before and after", "add more context on
  <finding/step/option>", "show examples of the options so I can decide",
  "what does this change get us", "what's the bigger picture here", "walk me
  through this change", "give me step by step instructions", "which of these
  can you do and which do I have to do". Modes, inferred from the target (an
  explicit mode argument always wins): default (context, a real before/after
  example, the payoff), options (example per option + recommendation + why +
  runner-up), deeper (bigger picture, why it exists, key decisions), steps
  (operator instructions split by who runs what). Not for manual testing
  steps (that is manual-test-guide) and not for whole-session orientation or
  catch-me-up recaps.
allowed-tools: Read, Grep, Glob, AskUserQuestion, Bash(git diff:*), Bash(git log:*), Bash(git show:*)
---

# explain

Deliver explanations in a fixed, concrete-anchored anatomy: succinct, just
enough context, always with a real example — never an unanchored abstraction.

## Workflow

1. **Locate the target** — the code, change, finding, or option set being
   pointed at: Glob/Grep to find it, Read to load it; for changes, pull the
   real diff via `git diff`, `git log`, or `git show`.
2. **Infer the mode** from the target's shape (table below). An explicit
   argument wins unconditionally; torn between two modes, ask one
   AskUserQuestion before writing — this should be rare.
3. **Pull the evidence** — the actual snippet, config, or command output.
   Never invent an example when the real artifact exists.
4. **Write in the mode's shape**, inline in chat.
5. **Close with the go-deeper offer** (one line).

## Rules of the house (all modes)

- **Succinct by default.** Just enough context to make the example land.
  Depth is an escalation, not the default.
- **Concrete over abstract.** If a claim can be shown with a real snippet,
  show the snippet.
- **Inline in chat, always.** Never route an explanation into a file or page
  unless explicitly asked.
- When several items need explaining (findings A–L, six open questions), go
  one at a time, each in the anatomy, rather than one wall covering all.

## The default-mode anatomy

Every **default-mode** answer has exactly these parts, in order (the other
modes define their own shapes in the table below):

1. **What it is** — one plain-language sentence.
2. **Context** — 2–4 sentences: why it exists, where it sits, what touches it.
3. **Example** — the core of the answer. A concrete before → after pair
   (code, config, command, output, behavior) pulled from the real artifact
   via Read/Grep/git — never invented pseudo-code when the real thing is
   available. For bugs and fixes, frame it as current behavior → intended
   behavior → the change that bridges them.
4. **What this gets you** — the payoff: what becomes possible, safer, or
   simpler because of it.
5. **Go deeper?** — close with a one-line offer to zoom out (deeper mode).

## Modes

Inferred from the target (workflow step 2); explicit arguments are
`/explain options …`, `/explain deeper`, `/explain steps …`.

| Mode | Fires when | Output shape |
|---|---|---|
| **default** | a concept, change, finding, or piece of code | the five-part anatomy above |
| **options** | a set of alternatives (A/B/C, competing designs, open questions) | per option: a worked example plus context; then one recommendation with why; the runner-up named when the call is close; pros/cons/risks/confidence when it feeds a decision |
| **deeper** | a prior explanation didn't land, or the bigger picture is asked for | why this exists at all, what breaks without it, the key decisions and their whys, the mental model — then back down to one concrete example |
| **steps** | "how do I do X" / operator instructions | numbered steps with exact copy-pasteable commands; when both parties act, split into "what I can do" vs "what you must do". Manual *testing* steps are out of scope — hand off to `manual-test-guide` |

## Red flags

| Thought | Reality |
|---|---|
| "An illustrative example is fine" | Pull the real artifact. Invented examples are how explanations drift from the code. |
| "More context makes it clearer" | Past just-enough, context buries the example. Offer deeper instead. |
| "The example would be long, so I'll describe it" | Trim the example; don't replace it with prose. |
| "I'll restate the code line by line" | That's narration, not explanation. Say why; show before/after. |
| "The mode is ambiguous; I'll pick one silently" | Torn between two modes → one question first. |

## See also

- `manual-test-guide` (repo-hygiene plugin, this marketplace) — owns manual
  testing steps (the steps-mode carve-out).
- `references/examples.md` — two full worked outputs (default and options
  mode) to calibrate against.
