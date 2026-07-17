# html-codesign ergonomic extensions — design

**Date:** 2026-07-17
**Target skill:** `plugins/use-html-theme/skills/html-codesign`
**Status:** approved (interviewed and signed off by Steve in-session)
**Implementation route:** skill-create (enhance-existing-skill)

## Goal

Make codesign pages ergonomic for both *deciding* and *reviewing*: every
question carries an always-present context-and-recommendation preamble, and
every layer of the page (context, options, whole sections) collapses so a
finished page scans as a dense summary of the decision. Exports default to a
slim, token-cheap answers document; a full human decision record is one
toggle away.

## Decisions (locked in interview)

1. **Collapse model — two toggles + summary.** Context has its own
   collapse; an open section has a "hide unchosen options" toggle (question,
   chosen answer(s), and note stay visible); the section header chevron
   folds the section to a one-line summary row. Control bar gains
   Collapse-all / Expand-all.
2. **Context shape — structured and linked.** `{ body, recommendation,
   recommended: [choice-ids] }`; recommended options get a ★ badge.
3. **Motion — all manual.** Page opens fully expanded (context blocks
   open); nothing auto-collapses.
4. **Summary row — dense with rec marker.** ID · question · ALL selected
   labels · ★followed / ⚠went-against-rec marker · note clamped to ~2 lines;
   unanswered sections show the pending rec (`★ rec: ch-XX-y`).
5. **Exports — slim by default, full by toggle.** Slim = ID, question,
   chosen answer(s), note if present — no context, no rec, no verdict.
   Full = ADR style with context body, rec line, and verdict. Applies to
   both MD and JSON.
6. **Context is generation-mandatory, export-optional.** Every generated
   page has a context per section; slimness is purely an output concern.

## Architecture: input and output are different documents

The input document's `sections` core is an ID-stamped superset of the
AskUserQuestion tool payload — that lineage is deliberate (both Claude and
Codex natively understand the shape) and must be preserved:

| AskUserQuestion | codesign input | delta |
|---|---|---|
| `questions[]` | `sections[]` | + stable `id` |
| `question` | `title` + `lead` | split |
| `options[] {label, description}` | `choices[] {label, detail}` | + `id`, `selected` |
| `multiSelect` | `exclusive` | inverted |
| automatic "Other" | `note`, `feedback` | explicit |

Therefore context does NOT go inside sections. It lives in a **sibling
`contexts` array** in the same embedded document (layered single doc —
option A of the reevaluation). Outputs get their own purpose-built
`codesign-answers` schema. The former invariant "an export IS a valid spec"
is **consciously dropped**: the v2-rendering agent already holds the plan
(it authored it; it is embedded in the v1 page), so exports only need to
carry the picks. Validation of inputs and the shape of outputs are separate
concerns.

## 1. Input document (`codesign-spec`)

```json
{
  "version": "1", "skill": "html-codesign", "mode": "codesign",
  "title": "Auth decision",
  "lead": "Toggle choices, add notes, then export your picks.",
  "generated_at": "2026-07-17T10:00:00-07:00",
  "sections": [
    { "id": "sec-01-auth", "title": "Which auth?", "lead": "Pick one.",
      "exclusive": true,
      "choices": [
        { "id": "ch-01-a", "label": "Magic link", "detail": "No reset flow.", "selected": false },
        { "id": "ch-01-b", "label": "Passwords", "selected": false }
      ],
      "note": { "id": "note-01", "placeholder": "Why?", "value": "" } }
  ],
  "contexts": [
    { "id": "ctx-01", "section": "sec-01-auth",
      "body": "Three viable routes. Passwords drive reset tickets; OAuth adds vendor lock-in; magic link kills the reset flow but needs deliverable email.",
      "recommendation": "Magic link — removes ~40% of support tickets, no vendor tie.",
      "recommended": ["ch-01-a"] }
  ],
  "feedback": { "id": "note-overall", "value": "" }
}
```

Rules:

- `sections` is unchanged from the current schema (AskUserQuestion-shaped
  core stays byte-compatible).
- `contexts`: exactly one entry per section, joined via `section`.
  Required at generation — a plan spec without a context per section is
  invalid, unconditionally.
- `body` = comprehensive view (landscape, constraints, trade-offs).
  `recommendation` = the argued case. `recommended` = choice IDs in that
  section; may be empty ONLY when the recommendation text states why the
  trade-off is genuinely neutral.
- `version` stays `"1"`.

## 2. ID grammar

Fourth prefix joins `id-grammar.md`:

```
ctx-{NN}   context blocks   ctx-01, ctx-02   (NN matches the section)
```

Referenceable in chat ("expand ctx-02's argument"). Summary rows carry no
IDs — they are pure view state.

## 3. Page components and view states

- **Context block** — collapsible region at the top of each section, open
  on load. Header "Context & recommendation"; prose body; visually distinct
  ★ recommendation callout naming the recommended choice(s). Recommended
  choice rows show a small ★ badge.
- **Hide-unchosen toggle** — collapses non-selected options behind
  "show N hidden options"; question, chosen answer(s), and note remain
  visible (covers the 5–6-option case).
- **Section collapse** — chevron in the section header folds to the dense
  summary row (decision 4). Clicking the row reopens the section.
- **Control bar** — adds Collapse-all, Expand-all, and a Slim/Full export
  toggle (default Slim) governing both export buttons. Existing four
  buttons unchanged.
- **A11y** — chevrons/toggles are real buttons with `aria-expanded`;
  `:focus-visible` and `prefers-reduced-motion` conventions as today.

## 4. Engine

- Collapse state lives ONLY in DOM attributes (`data-collapsed`,
  `data-options-hidden`, `data-ctx-open`) — never in the spec, never in
  exports. Identical picks with different collapse states export
  identically.
- Summary-row content re-renders through the existing `refresh()` path so
  it always mirrors live selections and notes.
- Rec markers (★followed / ⚠went-against) are derived at render time by
  comparing `selected` against `recommended` — no stored state.

## 5. Output documents (`codesign-answers`)

Slim JSON (default):

```json
{ "kind": "codesign-answers", "version": "1", "variant": "slim",
  "title": "Auth decision", "exported_at": "2026-07-17T10:12:00-07:00",
  "answers": [
    { "section": "sec-01-auth", "question": "Which auth?",
      "selected": [ { "id": "ch-01-a", "label": "Magic link" } ],
      "note": "lower support load" }
  ],
  "feedback": "" }
```

Slim MD mirrors it: `## sec-01-auth · Which auth?`, the selected choice
line(s) with IDs, note blockquote when non-empty. No context, no rec, no
verdict, unselected options omitted.

Full (`"variant": "full"` / full MD via the page toggle): adds per-answer
context body, ★ recommendation line, every option with ✓/✗, and a
followed / went-against-recommendation verdict — the human decision record
for PRs and `docs/decisions/`.

Filenames carry the variant: `{title-slug}-{ISO-date}.slim.md`,
`{title-slug}-{ISO-date}.full.json`, etc.

## 6. Validation

`validate_spec.py` validates **inputs only**. Added checks:

- `contexts` present; exactly one entry per section; `section` values
  resolve; no orphan contexts.
- `ctx-{NN}` grammar; NN matches the joined section's number.
- `recommended` may be an empty array (a deliberately neutral
  recommendation — §1 requires the recommendation text to argue why, which
  is the authoring agent's responsibility, not the validator's); when
  non-empty, every ID must exist among that section's choices.
- `body` and `recommendation` are non-empty strings.
- Existing checks (ID grammar, uniqueness, exclusivity, `</script` scan)
  unchanged and extended over the new strings.

The answers schema is documented in `export-formats.md` and covered by the
SKILL.md smoke test; it is machine-produced by the engine and gets no
agent-facing validator.

Fixtures: valid fixture gains `contexts`; invalid fixture gains a
missing-context case and a dangling-`recommended` case.

## 7. Documentation changes

- **SKILL.md** — process step 1 gains "author a context per section:
  comprehensive view + argued recommendation naming choice IDs"; smoke test
  gains context/badge/collapse/summary/export-toggle checks; gotchas gains
  "slim is the default export — paste-backs to the agent should stay slim;
  use full only when a human record needs the reasoning."
- **`spec-format.md`** — documents the layered input doc (sections core +
  contexts array) and the generation-mandatory context rule.
- **`export-formats.md`** — rewritten around `codesign-answers`, slim and
  full variants for both formats, with examples.
- **`iteration-loop.md`** — v2 from a slim answers doc: reuse surviving
  IDs as today, and re-author fresh contexts (the plan spec requires them;
  stale context must not be copied forward blindly).
- **`theming.md`** — new component classes for theme overlays: `.ctx`,
  `.ctx-toggle`, `.summary-row`, `.badge-rec`, `.hide-unchosen`.
- **NEW `references/design-notes.md`** — meta-documentation for future
  editors, not for functional use: the AskUserQuestion lineage table, the
  input/output separation rationale, the dropped export-IS-spec invariant
  and its replacement, invariants that must survive edits (ID stability,
  self-containment, spec-first, DOM mirrors spec), and this redesign's
  decision history. SKILL.md points to it with one line: "Editing this
  skill? Read references/design-notes.md first."

## Out of scope

- Auto-collapse / wizard flows (explicitly rejected in interview).
- Persisting collapse state into exports or the spec.
- A validator for answers documents.
- Any change to theming beyond documenting the new classes.
- Live agent callbacks from the page (standing rule of the skill).

## Verification

- `scripts/validate_spec.py` passes on the updated valid fixture; fails
  with clear messages on the new invalid cases.
- Template smoke test (manual, per SKILL.md): context opens/collapses;
  ★ badge on recommended options; hide-unchosen keeps note visible;
  summary row shows labels + rec marker + clamped note; Collapse-all /
  Expand-all; slim and full exports for both MD and JSON match the schemas
  here; exports unaffected by collapse state.
- skill-quality gate passes (skill-create pipeline).
