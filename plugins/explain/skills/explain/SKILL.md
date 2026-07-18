---
name: explain
description: >
  Explain anything in a concrete-anchored style — succinct, just-enough
  context, always grounded in a real example. Use when the
  user invokes /explain, or asks in their own words: "explain X", "give me a before and after", "add more context on
  <finding/step/option>", "show examples of the options so I can decide",
  "what does this change get us", "what's the bigger picture here", "give me
  step by step instructions". A bare "explain" right after an explanation
  means "not enough to act on yet": diagnose the gap (bigger picture,
  clearer language, or a sharper example) and usually rewrite, not append;
  an argument steers the focus; a dissimilar target restarts fresh. Modes
  (inferred from the target; explicit argument wins): default, options
  (example per option + recommendation), deeper, steps (operator
  instructions). Not for manual testing
  steps (manual-test-guide) or whole-session recaps.
allowed-tools: Read, Grep, Glob, AskUserQuestion, Bash(git diff:*), Bash(git log:*), Bash(git show:*)
---

# explain

Deliver explanations in a fixed, concrete-anchored anatomy: succinct, just
enough context, always with a real example — never an unanchored abstraction.

## Workflow

1. **Locate the target** — a bare or re-issued `explain` right after an
   explanation is a follow-up: the target is what was just explained (see
   the gap diagnosis below). Otherwise it is the code, change, finding, or
   option set being pointed at: Glob/Grep to find it, Read to load it; for
   changes, pull the real diff via `git diff`, `git log`, or `git show`.
2. **Infer the mode** from the target's shape (table below) — or, for a
   follow-up, the gap (diagnosis below). An explicit argument wins
   unconditionally; torn between two readings, ask one AskUserQuestion
   before writing — this should be rare.
3. **Pull the evidence** — the actual snippet, config, or command output.
   Never invent an example when the real artifact exists.
4. **Write in the mode's shape**, inline in chat.
5. **Close with a follow-up offer** (one line) — go deeper by default; if
   the answer just delivered the bigger picture, offer the next likely gap
   (a concrete example, the internals) instead.

## Rules of the house (all modes and follow-ups)

- **The action anchor.** Explain toward the live action in front of the
  user (what it changes, the value, the rationale, how it fits); with no
  live action, toward recognizing when this matters later. The anchor picks
  which context earns its few sentences — it does not license more of them.
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
2. **Context** — 2–4 sentences, scoped to the action in front of the user
   (the action anchor above): why it exists, where it sits, what touches it.
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
| **deeper** | the bigger picture is asked for explicitly | why this exists at all, what breaks without it, the key decisions and their whys, the mental model — then back down to one concrete example |
| **steps** | "how do I do X" / operator instructions | numbered steps with exact copy-pasteable commands; when both parties act, split into "what I can do" vs "what you must do". Manual *testing* steps are out of scope — hand off to `manual-test-guide` |

## Follow-up invocations — diagnose the gap

A bare `explain` (or `explain <guidance>`) issued right after an
explanation — from this skill in any mode, or any explanation the assistant
just gave — is a **follow-up**: the answer wasn't enough to act on. "Right
after" means the immediately preceding answer; anything older is a cold
start.

**Re-read the prior answer and diagnose what's blocking the action**, then
name the guess in half a line. The common gaps, in the order to try them:

1. **Too specific — no frame.** The most common failure and the usual first
   move: step back and put it in the bigger picture — what it changes, the
   value, the rationale of the what and why, how it fits. The first answer
   carries the minimum frame the action needs; this remedy expands it when
   that minimum proved too thin.
2. **Unclear language.** Rewrite in plain language; drop the jargon.
3. **Missing or vague example.** Add one, or make the existing one
   explicit and concrete.

A follow-up keeps the prior answer's mode shape — remedies change the
content (frame, language, example), not the mode; only an explicit ask
changes the mode.

**Rewrite over append.** Restating the whole explanation with the expansion
woven in is usually clearer — a bigger-picture reframe restructures the
answer, it doesn't sit under it. Append only when the delta is small,
clear, and self-contained. Either way, never repeat prior material
unimproved.

The rest of the reading rules:

- **Argument naming an aspect of the current subject** — steering: diagnose
  within that aspect.
- **Argument outside the current subject** — a new target: a fresh first
  answer.
- **Explicit asks** (`deeper`, "how does it actually work", accepting the
  closing go-deeper offer) — go straight there; diagnosis yields. ("How
  does it actually work" takes the anatomy with a mechanism walkthrough as
  the example.)
- **Gap not diagnosable** — ask which part is unclear, offering candidates
  (the frame? the example? the why?) via AskUserQuestion — the rare path.
- **Genuinely unclear whether this is a follow-up at all** — repeat back
  the interpretation in one line and confirm before answering.
- **Cold start** (nothing just explained): target the last substantive
  thing discussed; if there is none, ask what to explain.

## Red flags

| Thought | Reality |
|---|---|
| "An illustrative example is fine" | Pull the real artifact. Invented examples are how explanations drift from the code. |
| "More context makes it clearer" | Past just-enough, context buries the example. Offer deeper instead. |
| "The example would be long, so I'll describe it" | Trim the example; don't replace it with prose. |
| "I'll restate the code line by line" | That's narration, not explanation. Say why; show before/after. |
| "The mode is ambiguous; I'll pick one silently" | Torn between two modes → one question first. |
| "They asked again — I'll say it again, better" | Diagnose first: too specific → step back; jargon → plain words; thin example → sharpen it. |

## See also

- `manual-test-guide` (repo-hygiene plugin, this marketplace) — owns manual
  testing steps (the steps-mode carve-out).
- `references/examples.md` — worked outputs (default and options mode) plus
  a follow-up diagnosis walkthrough to calibrate against.
