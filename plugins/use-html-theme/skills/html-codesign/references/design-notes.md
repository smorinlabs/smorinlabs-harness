# Design notes — for editors of this skill, not users of it

This file is meta-documentation: the reasoning behind this skill's
architecture, kept so future edits don't undo deliberate decisions. Nothing
here is needed to *use* the skill. Full design record:
`docs/superpowers/specs/2026-07-17-html-codesign-ergonomics-design.md` in
the harness repo.

## Lineage: the input core is AskUserQuestion-shaped

The input spec's `sections` array is an ID-stamped superset of the
AskUserQuestion tool payload — the shape agents (Claude, Codex) already
emit and understand when asking a user to decide:

| AskUserQuestion | codesign input | delta |
|---|---|---|
| `questions[]` | `sections[]` | + stable `id` |
| `question` text | `title` + `lead` | split |
| `options[] {label, description}` | `choices[] {label, detail}` | + `id`, `selected` |
| `multiSelect` | `exclusive` | inverted name |
| automatic "Other" | `note`, `feedback` | explicit |

**Consequence:** advisory material must never be injected into `sections`.
The context/recommendation layer lives in the sibling `contexts` array,
joined by section id. If a future feature needs per-question data, ask
first: is it part of the *question contract* (goes in sections, sparingly)
or *advice about the question* (goes in a sibling layer)?

## The governing principle: the reader wasn't in the room

A codesign page must work for someone with zero session context — that is
the whole point of the paste-back loop. v0.8.0 enforced this structurally
(every section has a context); the 2026-07-18 revision enforces it
qualitatively (the clarity scaffold and authoring rules — the first real
page shipped jargon like "Theme overlay coverage · .ctx, .summary…") and
interactively (Skip and the ask channel — a reader who *can't* answer
needs a first-class way to say so). Test every future feature against this
principle.

## Inputs and outputs are different documents

- **Input** (`codesign-spec`, spec-format.md): the question set an agent
  authors. Context ENVELOPES required — id, section join, one-line
  summary, argued recommendation, recommended choice ids.
  `validate_spec.py` enforces this, unconditionally.
- **Context body** — free-form HTML in the page's `.ctx` block, outside
  both schemas (2026-07-18 decision): JSON is good at contracts and bad at
  content, and a schema'd body field caps richness (no charts, tables,
  images) while inviting escaping hazards. The envelope carries exactly
  what machinery consumes (badges, verdicts, exports, the one-per-section
  guarantee); everything else is page content, shaped by the default
  scaffold (`.ctx-what` / `.ctx-why` / free zone / `.ctx-rec`) and hard
  authoring rules (question-shaped titles, orient-before-arguing, zero
  unexplained jargon). Do not move the body back into JSON — and do not
  let envelope fields grow into content fields.
- **Output** (`codesign-answers`, export-formats.md): the decision a person
  made. Purpose-built, variant-aware (slim default / full toggle), never
  validated as an input. Full exports carry the envelope only — the
  self-contained page file IS the rich-context archive; innerText
  extraction of free-form HTML was rejected as lossy and nondeterministic.
- **Skip and open questions** (2026-07-18): Skip is an engine-provided
  control (not a spec choice — agents can't forget it, no ID churn);
  skipping is *deliberately not deciding*, so MD omits the section while
  JSON records `skipped: true` for the loop. Questions are captured
  per-section (`q-{NN}`) and exported as `open_question` (`question` was
  already the section title). Questions always surface in exports even on
  skipped sections — skip governs decision content only.

**Dropped invariant (2026-07-17):** v1 of this skill held "an export IS a
valid spec" — one schema for plan, page, and export, letting a v2 render
straight from an export. Dropped because it forced context into every
export (tokens spent re-sending what the agent already holds) or forced
conditional validation hacks. Replacement: the v2-rendering agent already
holds the plan (it authored it; it is embedded in the v1 page), so exports
only carry picks + notes with stable IDs, and iteration-loop.md requires
re-authoring contexts for a v2. Do not reintroduce schema-sharing between
the two sides without revisiting that reasoning.

## Slim-by-default exports

The loop's main consumer is the agent, which already has the contexts —
so the default export is the smallest faithful decision record (ID,
question, picks, note). Full exists for human decision records. The
Slim/Full toggle is page state, not spec state.

## Decision state vs view state

- **Decision state** — selections, notes, contexts, recommendations: lives
  in the spec, flows into exports.
- **View state** — section collapse, hidden unchosen options, context
  open/closed, export variant: lives ONLY in DOM attributes. Never in the
  spec, never in exports. Identical picks export identically regardless of
  folding. Keep it that way — persisted view state would make exports
  nondeterministic and pollute the iteration loop.

Derived, not stored: the followed/went-against-recommendation verdict is
computed from `selected` vs `recommended` at render/export time. Storing it
would create a second source of truth that drifts.

## Invariants that must survive any future edit

1. **ID stability** (id-grammar.md): shipped ids never change meaning;
   survivors keep their letters; new content takes the next unused id.
2. **Self-containment**: one `.html`, no external requests, works from
   `file://`. No live agent callbacks — the paste-back loop is the
   portable contract.
3. **Spec-first**: the embedded spec is the source of truth; the DOM
   mirrors it (`data-id` both directions, including `.ctx` blocks); the
   engine hydrates FROM the spec.
4. **Validator-before-render**: never render from an unvalidated spec.
5. **Sections stay AskUserQuestion-shaped** (see lineage above).
6. **All collapse is manual.** Auto-collapse/wizard flows were considered
   and explicitly rejected (surprise motion; pick-any has no "done"
   signal). Don't add them without a new decision.

## Decision history (2026-07-17 ergonomics redesign)

Interviewed decisions, in order: two-toggles-plus-summary collapse model
(over three-state cycle and single-collapse); structured context linked to
choice ids (over free prose); all-manual motion (over auto-hide and wizard);
dense summary rows with rec markers (over compact or two-line); slim-default
exports (revised from an initial full-ADR-default choice — token economy for
the agent loop won); layered single input doc (over two embedded docs and a
literal-AskUserQuestion payload).

## Decision history (2026-07-18 ergonomics 2)

Driven by the first real page's review. Decisions, in order: engine-level
Skip with JSON-recorded state (over skip-as-spec-choice and
fully-invisible-in-output); per-section question capture + batch
"Questions first" paste-back (over a note-field mode toggle and a
batch-only panel); context envelope in schema with free-form body in the
page (over fully-schemaless context — loses badges/verdicts/guarantees —
and body_html-in-JSON — escaping and bloat); default clarity scaffold,
extendable (over mandatory slots and guidance-prose-only); envelope-only
full exports (over innerText extraction). Spec:
docs/superpowers/specs/2026-07-18-html-codesign-ergonomics-2-design.md.
