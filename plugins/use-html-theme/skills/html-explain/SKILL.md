---
name: html-explain
description: |
  Build a read-only "explainer" page as one self-contained HTML file — a rich
  explanation of settled material, where diagrams, annotated figures, charts,
  and small interactive widgets do work prose cannot. Authoring maps which
  parts are intrinsically hardest, budgets the page around them, then enriches
  ONLY where comprehension actually breaks. Use when an explanation should be
  a shareable PAGE not inline chat: "explain the design we just landed",
  "write up what the tests showed", "make an explainer for this spec", "deep
  dive on X as a page", explainer, walkthrough page, "explain this
  visually". Reads recent context and ALWAYS confirms the target before
  generating, even on explicit invocation with an argument. If context is
  mostly UNANSWERED questions it offers html-codesign instead (that answers
  questions; this explains — including a deep dive on one already resolved).
  Inline chat explanations are the `explain` skill; charts defer to dataviz
  when present. Pairs with use-html-theme.
allowed-tools: Read, Write, Edit, Glob, Grep, AskUserQuestion, Bash
---

# What this makes

One `.html` file that explains something as well as it can be explained —
read-only, no decision round-trip, opened anywhere by anyone. "Read-only"
governs the **contract**, not the medium: the page carries whatever makes
the subject land, including annotated diagrams, small multiples, charts,
build-up sequences, and interactive widgets the reader can manipulate.

The objective function is **clarity**, not coverage and not compliance with
the canon in `references/`. Those principles are aids. A page that breaks
one of them and lands is better than a page that satisfies all of them and
doesn't.

# When this skill applies

✓ "Explain the retry design we landed — as a page I can send the team"
✓ "Write up what the load tests showed"
✓ "Make an explainer for this spec"
✓ "Deep dive on the caching decision, with diagrams"
✗ An explanation that belongs inline in chat → the `explain` skill (which
  hard-rules itself to chat and hands the page case here)
✗ A page whose job is to collect a decision → `html-codesign`
✗ Open questions to work through conversationally → `question-walkthrough`

# Process

## 1. Triage and confirm the target — before anything else

Run `../../references/context-triage.md` in full. It classifies recent
context, produces a confidence verdict, and defines the gate.

**The gate always fires** — including when this skill was invoked explicitly
and including when an argument named the topic. An argument shortens the
question; it never removes it. Rendering a whole page about the wrong
artifact is the expensive mistake this one question prevents.

**The gate is TWO turns, never one.** Same-turn prose may never render —
when a turn ends in a tool call the user can receive only the dialog. So:
turn 1 delivers the candidate targets as the turn's **final content, with no
tool call after it**; turn 2 opens with AskUserQuestion. Write each option to
name its own target ("Deep dive on the backoff design") rather than "the
first one", so the dialog still makes sense if the pre-read is lost.

If triage finds mostly unanswered questions, say so and offer
`html-codesign` — and offer `question-walkthrough` alongside it, since
resolving them in chat is a first-class answer. If it finds a mix, offer
both page types.

## 2. Outline — inventory what is actually there

Before writing a word of the page, list the material the explanation will
be built from, and **read the real artifacts**: the diff, the spec, the test
output, the design doc, the code. Pull them with Read/Grep/Glob and
`git log` / `git show` / `git diff`.

Produce a working outline — the sections, and what each has to establish.
This is for you, not the reader; it exists so steps 3–5 have something to
operate on.

**Never explain from memory of the conversation when the artifact is on
disk.** Reconstructed examples are how explainers drift from what shipped.

## 3. Difficulty map — decide where the emphasis goes, BEFORE drafting

Run `references/difficulty-map.md`. Rate each outline section by how hard it
is **intrinsically** — for a stranger, assuming it is written well — name
*what kind* of hard it is, and allocate the page's budget accordingly.

This has to happen before the draft for two reasons. Critiquing a draft can
only find difficulty **you introduced by writing badly**; it cannot find
difficulty that belongs to the subject. And a difficulty list written before
the draft is **pre-registered** — step 7's enrichments must trace back to
it, so a figure can never be justified after the fact.

The kind-of-hard column also selects the principles: it names them directly.
Collect the two or three that recur across rows and write against those.
`references/explanatory-canon.md` is indexed by symptom for exactly this.

**Be spiky.** A map where everything rates the same is a map that wasn't
made. If you can't say which part is hardest, go back to the artifacts.

## 4. Draft

Write it, spending the budget from step 3. The hardest one or two sections
get the clear majority of the words.

## 5. Critique — the clarity pass

Read the draft as **someone who was never in this conversation** — because
that is who opens the file.

The failure mode has a name — the **curse of knowledge** — and it is the
single most likely thing to go wrong here: you cannot un-know the subject,
so you compress exactly the step the reader needed. Hunt for it
specifically:

- a term of art used before it is defined
- session jargon ("the fix from earlier", "the new approach")
- a conclusion whose supporting step was left implicit
- an abstraction with no instance attached

Fix these in the prose first. **Do not reach for a visual to rescue a
passage that is simply badly written** — an unclear paragraph with a diagram
beside it is two unclear things.

Re-read the sections rated hardest in step 3 the most carefully — that is
where a reader actually falls out.

## 6. Enrich — the medium pass

Now ask the question that makes this a *page* and not a document:

> This is HTML. What here would land better as something other than prose?

Walk the outline and look for the places where prose is genuinely working
too hard: spatial relationships, parallel structure across many cases,
change over time, a mechanism with moving parts, quantities to compare, a
process with branches, a parameter whose effect is the point.

Consult `references/enrichment-ladder.md` — it ranks the options from
"annotate the text" up to "build a manipulable model", with the cost of
each — and `references/visual-encoding.md` for anything where a mark's
position or size stands for a number.

## 7. Judge — enrich only where comprehension breaks

**This is a hard rule, not a preference.** Every enrichment must trace to a
row in step 3's difficulty map rated ●● or higher, or to a defect step 5
found. Uniform enrichment is a failure: a diagram beside an already-clear
paragraph adds load without adding understanding, and buries the figures
that are doing real work.

The test, per element:

> Remove it. Is the passage meaningfully harder to understand?
> **No → it does not ship.**

For an interactive control there is a stricter version, because a control
costs the reader an action before it pays anything:

> Does *manipulating* this change what the reader understands?
> If the insight arrives from looking at the default state, it is a figure,
> not a widget. Ship the figure.

## 8. Whole-page review

Steps 5–7 work section by section. This one reads the finished page as a
single object, and asks four questions the per-section passes structurally
cannot:

- **Arc** — is there a spine (something was broken/unknown → this changed →
  here is what's true now), or just an inventory of facts? (canon L3.7)
- **Budget check** — does the page's actual shape match step 3's map? If a
  ● section grew to a third of the page, cut it back or re-rate honestly.
- **Enrichment density** — if much more than a third of the page is figures
  and widgets, re-run the removal test on all of them. That ratio usually
  means enrichment stopped being diagnostic and became a habit.
- **First-screen test** — from the title and lede alone, does a stranger
  know what this is about and why it matters, before any argument starts?

## 9. Resolve the theme

Follow the same cascade `html-codesign` uses (`references/theming.md` in the
sibling skill): the use-html-theme session theme if one is active, else its
persistence file (`.claude/use-html-theme.local.md`), else the neutral
built-in style in the scaffold. Never mix themes. Do NOT force the theme
picker just for an explainer page.

**Birchline ships an explainer overlay** —
`../use-html-theme/references/themes/birchline/explain.md`. Apply it when
Birchline is the active theme; its warm-editorial register suits long-form
explanation better than anything else in this plugin.

Technical-minimal and High-contrast-dark have **no explainer overlay**, and
the cascade handles that by deriving the scaffold's components from that
theme's `tokens.md`. That is deliberate, not a gap: an explainer's
components vary with its subject, so beyond Birchline there is not yet a
fixed vocabulary worth hand-tuning.

## 10. Render and look at it

Start from `assets/explainer-scaffold.html`. Then **open or screenshot the
result** and actually look: figure/caption collisions, overflow on narrow
widths, a widget that doesn't respond, a diagram that lost its labels. The
scaffold guarantees structure, not layout.

## 11. Deliver

Give the file path, name the two or three principles you wrote against and
which difficulty rows the enrichments were spent on, and offer the obvious
next moves — go deeper on a section, add a figure somewhere it was thin, or
restyle under a different theme.

Then close out per `../../references/delivery-close.md`: the **full absolute
path on its own line** (never relative — the reader is often not in the shell
that made the file), and a short prose list of what they might want next.
Those offers are strictly conditional — open it in the browser only when this
session runs on the user's own machine (same gate for copying the path to
the clipboard), add it to `shelf` only when that skill is
installed (if it isn't, don't mention it at all), and where to save it
whenever the file sits somewhere temporary **or anywhere you chose rather
than the user**. The save recommendation is read from context, never a fixed
ranking. The next moves above lead; these come after them.

# Hard rules

- **Self-contained.** One `.html`, embedded CSS/JS/assets, no external
  requests, no build step. It must work from `file://`, an artifact host, or
  an email attachment. Diagrams are inline SVG; images are `data:` URIs;
  interactivity is vanilla JS. No CDN, no webfont link.
- **Read-only.** No decision round-trip, no picks, no answers export. If the
  page's job is to collect a choice, it is a codesign page — stop and hand
  off. (A "copy this section" or print affordance is fine; a *decision*
  channel is not.)
- **Enrichment is earned, never uniform.** Step 6's removal test governs
  every figure and every control.
- **Real artifacts only.** Examples, diffs, numbers, and outputs come from
  the actual source. Never invent an example when the real one exists;
  never round a number you did not read.
- **Write for a stranger.** Zero session jargon. Every term of art defined
  at first use. Orient before arguing.
- **Charts defer to `dataviz` when it is present** — and fall through
  silently to `references/visual-encoding.md` when it is not. See the
  delegation rule there; `dataviz` is bundled with Claude Code and does not
  exist on Codex, so the fallback is load-bearing, not decorative.
- **Deliver the absolute path.** The full path, on its own line, every time.
  A relative path is only meaningful from a working directory the reader
  can't see.
- **Declare the color scheme.** Light theme → `<meta name="color-scheme"
  content="light">`; dark → `dark`. (iOS Safari auto-darkens pages that
  don't declare.)
- **Accessibility basics.** Visible `:focus-visible`; respect
  `prefers-reduced-motion`; every figure has a text equivalent in its
  caption or body; identity is never carried by color alone; interactive
  controls are keyboard-operable.

# Quick smoke test

1. Did the gate fire and get a real answer — even though the skill was
   invoked explicitly?
2. Did the pre-read land on **its own turn**, with no tool call after it,
   and does every dialog option name its own target so the dialog survives
   the pre-read being lost?
3. Does every example, number, and snippet trace to an artifact you actually
   read?
4. Was there a difficulty map before the draft, and is it **spiky** — not
   every section rated the same?
5. Budget check: do the hardest one or two sections actually hold the
   majority of the page? (Uniform depth is the default failure.)
6. Stranger pass: hand the first screen to someone with no context. Do they
   know what this is about and why it matters before any argument starts?
7. Curse-of-knowledge pass: is every term of art defined at first use? Any
   "the new approach" left dangling?
8. Removal test on **every** figure and widget: does taking it out make the
   passage harder? Any that survive removal are cut.
9. Does each surviving enrichment trace to a difficulty row rated ●● or
   higher, or to a defect the critique found? (Pre-registered — no
   after-the-fact justification.)
10. Widget test: does manipulating each control change understanding, or does
   the default state already carry it?
11. Density check: is the page much more than a third figures?
12. Does it open from `file://` with the network off, with nothing missing?
13. Narrow-width pass: does anything overflow horizontally?
14. Is the right `color-scheme` meta present, and does it match the theme?
15. Delivery pass: is the **full absolute path** on its own line? Are the
    convenience offers conditional — browser-open only if this session can
    reach one, `shelf` only if that skill is installed (and unmentioned if
    not)?

# Gotchas

- **A wall of prose with pictures is not an explainer.** The enrichment pass
  is step 6 of a loop that begins with an outline and a difficulty map. Skipping to
  "add diagrams" produces decorated text.
- **Don't reimplement theming.** Tokens and component looks come from
  use-html-theme (or the neutral fallback). This skill owns structure,
  content, and enrichment only.
- **Don't reimplement charting where `dataviz` is present.** It carries a
  runnable colorblind/contrast validator this skill has no equivalent for.
  Use it when it's there.
- **`dataviz` is not on disk.** It is compiled into the Claude Code binary
  and materializes at a versioned temp path when invoked. It is absent on
  Codex entirely. Do not "simplify" the fallback away on the grounds that
  the delegate exists — on half the fleet it doesn't.
- **A deep dive on a settled question is this skill's job, not
  codesign's.** They overlap precisely there. Codesign *poses* a question;
  this *explains* one. If the user wants to understand the fork rather than
  resolve it, you're in the right place.
- **Interactivity is not free clarity.** It is the most expensive thing on
  the page — to build, to review, and for the reader to operate. The bar in
  step 7 is deliberately higher for controls than for figures.
- **Length is not depth.** More sections is the usual way an explainer gets
  worse. Coherence — cutting what doesn't serve the explanation — is the
  first principle in the canon for a reason.
- **Uniform depth is the quiet failure.** Explaining every section at the
  same level of detail feels thorough and is the single most common reason a
  page doesn't land — the hard part got the same treatment as the trivial
  one. That is what the difficulty map exists to prevent; skipping it
  reliably produces this.
- **Don't publish the difficulty map.** It's scaffolding. Saying "this next
  part is the tricky one" is good; printing your own ●●● ratings is the page
  talking about itself instead of its subject.
- **"The candidate list is right there above the dialog."** It may not be.
  A turn that ends in a tool call can reach the user as the dialog alone —
  so a same-turn pre-read is a pre-read that might not exist. Two turns, and
  options that stand on their own.

# See also

- `../../references/context-triage.md` — the shared preflight; the routing
  authority between this skill and `html-codesign`.
- `html-codesign` (this plugin) — the sibling that collects decisions.
- `use-html-theme` (this plugin) — owns the page's look.
- `explain` (explain plugin, this marketplace) — the same job inline in
  chat, and the source of the concrete-anchored anatomy this skill renders.
- `dataviz` (bundled with Claude Code) — quantitative charts, when present.
- `../../references/delivery-close.md` — the shared close-out: absolute
  path, then the conditional convenience offers.
- `references/difficulty-map.md` — step 3: rating intrinsic difficulty and
  allocating the page's budget.
- `references/explanatory-canon.md` — clarity principles, indexed by symptom.
- `references/visual-encoding.md` — encoding rules + the dataviz carve.
- `references/enrichment-ladder.md` — what to reach for, and what it costs.
- `assets/explainer-scaffold.html` — the page skeleton to start from.
