---
name: design-by-elements
description: >-
  Iterative, element-by-element method for prototyping the visual or textual FORM of an artifact —
  terminal output, report/CLI layouts, table designs, page or email mockups, status blocks — BEFORE
  building it. Decompose the artifact into independently lockable elements; settle what each element
  MEANS and which reader-question it answers before arguing form; offer 2–3 deliberately OPPOSED
  variants (short IDs, pick by shorthand) instead of a catalog; lock each with its rationale in a
  decisions log; and promote every fix into a NAMED RULE that polices the rest, so the design
  converges instead of looping. Ends with a zoom-out pass and scale probes (1 vs many vs zoomed-out).
  Use when the user says "design this layout/format", "prototype the look", "iterate on this output",
  "let's lock this section", "element-wise", or when a formatting debate keeps looping. NOT general
  feature/product brainstorming (superpowers:brainstorming), NOT an async HTML decision page
  (html-codesign).
---

# Design by elements

Prototype the *form* of an artifact — terminal output, a report layout, a table, a status block, a
page or email — by decomposing it into small lockable elements, settling meaning before form,
contrasting opposed variants, locking each with its rationale, and turning every fix into a named
rule. The design converges because each locked element makes the next one cheaper.

> **Iron Law — never redesign the whole artifact at once.**
> Decompose it into named elements; settle what each element *means* before arguing how it *looks*;
> lock one element at a time with its rationale; and turn every fix into a named rule that polices
> the rest.
>
> - Not "it's a small artifact" — small artifacts still have elements, and the loop is cheap.
> - Not "the fix is obvious, I'll just apply it" — an un-generalized fix resurfaces in the next element.
> - Not "let me show all the options at once" — a catalog of near-duplicates paralyzes; 2–3 opposed variants decide.
> - Not "it renders fine in the source" — design the *rendered* form; the source is not what the reader sees.
>
> Whole-artifact iteration produces "work vomit" — each pass re-breaks the last. Element-wise locking
> is the correction. Violating the letter of this law is violating the spirit.

## The five moves

Run them per element, in order. Move 3 is the only interactive gate.

### 1. Interrogate semantics before form

Ask "what is this element supposed to *represent*?" before any styling. Form arguments are
unresolvable while meaning is fuzzy — **every looping formatting debate is a disguised semantic
question.** When form talk stalls, stop and name what the element is *for* and which single
reader-question it answers; then return to form.

> A `Tree ⚠ 2` status line nobody understood became `Local changes  2 config files — not committed,
> so not in the PR` only after asking what the line was *for*.

### 2. Decompose into independently lockable elements

Break the artifact into elements small enough to iterate alone, each with explicit interfaces to its
neighbors (spacing, order). Keep a **section queue** — the ordered list of elements with a status
each (`locked` / `active` / `pending`) — so nothing is dropped and the order is visible.

> A "stream block" decomposes into header / description / facts block / plan spine / launch prompt.
> Blank-line spacing between them is itself part of each lock.

### 3. Contrast, don't enumerate

Offer **2–3 deliberately opposed variants** per element — not a catalog of near-duplicates. Opposed
variants reveal actual preference; near-duplicates reveal nothing. Give each variant a short stable ID
(`A1`/`A2`, `B1`–`B3`, `Dh1`–`Dh3`) so the user replies in shorthand. **Use `AskUserQuestion`**, one
element at a time, with the variants as options and previews for visual comparison; the built-in Other
is the escape hatch, and notes refine the pick.

### 4. Lock and advance

Once an element is settled, **lock it** and record the decision in a **decisions log** with three
columns — `Fork | Decision | Rationale` — then flip the section queue and move to the next element.
The rationale is not optional: it is what stops a locked element from reopening later.

### 5. Generalize every fix into a named rule

The distinctive move. A user comment ("the branch annotation is obvious") does **not** become one
edit — it becomes a **named rule** (e.g. `LG1`) recorded in a rule ledger, and every later element is
checked against it. This is why the method converges: a fix applied locally is whack-a-mole and
resurfaces; promoted to a rule it is paid once, and each locked element makes the next cheaper because
its rules already apply. **Make convergence the goal — keep a rule ledger and cite rule IDs as you go.**

## The final move: zoom back out

Locking element-by-element risks a set of locally-good pieces that don't cohere. **Schedule an
explicit final pass** to re-integrate every locked element and check the whole: spacing between
elements, consistent application of every named rule, and the artifact read end-to-end at real scale.
This pass is part of the contract, not optional.

## Companion principles

Fold these in throughout — they are first-class parts of the method, not asides.

- **Admission test.** Every element (and every column/field within one) must justify itself by the
  reader-question it answers. Name the question or cut the element.
- **Design for scale — up *and* down.** Always render the design at more than one size: 1 element,
  ~10 elements, and zoomed out to only the big items. A layout must get *better* under load, not
  worse. Encode this as zoom tiers and per-element fallbacks (e.g. a full table for ≥4 items, a
  compact label+sentence form for ≤3).
- **Weight by consequence, not size.** Big items get full treatment; small ones collapse ("also: 2
  small fixes") — *unless* a small item carries a key decision, learning, or change of approach, which
  overrides size. Corollary: *finished* minutiae roll up into one counted row; live or blocked items
  never roll up, however small.
- **Name things.** Elements, rules, variants, and sections all get stable names and IDs — names are
  what make locks referenceable and rules enforceable.
- **Density rule (columns vs in-cell lines).** A fact earns a *column* only when it is dense (present
  in nearly every row) — columns are paid by every row. Sparse facts become in-cell lines, paid only
  where used.
- **Medium awareness.** Design the *rendered* form, not the source. A markdown table renders as a box
  table in a terminal; wrapping output in a code fence silently degrades it. Preview the real output.

## Artifacts you keep

Three lightweight running records, referenced by ID throughout:

- **Section queue** — the ordered element list with per-element status (move 2).
- **Decisions log** — `Fork | Decision | Rationale`, one row per lock (move 4).
- **Rule ledger** — named rules with rationale, applied to every later element (move 5).

## Red Flags

| Thought | Reality |
|---------|---------|
| "Let me just try a few layouts" | Form debate while meaning is fuzzy is unresolvable. Ask what the element *represents* first (move 1). |
| "I'll show them all five options" | A catalog paralyzes. 2–3 *opposed* variants with IDs decide (move 3). |
| "I'll just fix this one line" | A local fix is whack-a-mole; it resurfaces in the next element. Promote it to a named rule (move 5). |
| "Let me iterate the whole artifact" | Whole-artifact iteration is "work vomit" — each pass re-breaks the last. Lock element-by-element (Iron Law). |
| "It renders fine in the source" | The reader sees the *rendered* form. A code fence degrades a table. Preview real output (medium awareness). |
| "This field looks nice" | Every field earns its slot by a reader-question. Name the question or cut it (admission test). |
| "The pieces are all locked, we're done" | Locally-good pieces need not cohere. Run the zoom-out pass before declaring done. |

## Lineage

For rationale, not procedure:

- **Atomic Design** (Brad Frost) — the element hierarchy: line grammar = atoms, fields = molecules,
  facts block / plan spine = organisms, the block = template, the artifact = page.
- **Pattern language** (Christopher Alexander) — named rules carrying their own rationale.
- **Design-rationale capture** — the decisions log (fork → decision → why).
- **Concept design** (Daniel Jackson) — the admission test: every element justified by the purpose it
  serves, or cut.

Four full worked examples (feedback → named rules, a decisions-log excerpt, element decomposition with
locks, and scale probing) are in `references/worked-examples.md`.

## See also

- `superpowers:brainstorming` — general feature/product design *before* implementation. This skill is
  narrower: iterative prototyping of an artifact's visual/textual *form*. Reach for brainstorming to
  decide *what to build*; reach for this to decide *how the output looks*.
- `html-codesign` — when the choose-and-capture should be an async, shareable HTML decision page
  instead of an in-conversation loop.
- `question-walkthrough` — when the task is triaging a pile of *existing* open questions, not
  prototyping a form.
- `reader-steps` — for rendering the manual steps a design produces, once locked.
