# codesign-spec format (the INPUT document)

The JSON contract behind every codesign page. Written FIRST (before any
HTML), validated with `scripts/validate_spec.py`, and embedded verbatim in
the page as `<script id="codesign-spec" type="application/json">`.

This is the **input** side only. What the page emits back is a different
document — `codesign-answers`, defined in `references/export-formats.md`.
Inputs and outputs deliberately do NOT share a schema: the input is the
question set an agent authors; the output is the decision a person made.

The `sections` core is an ID-stamped superset of the AskUserQuestion tool
payload — a shape both Claude and Codex natively understand. Keep it that
way: decision structure goes in `sections`; advisory material goes in the
sibling `contexts` array, never inside a section. (Lineage and rationale:
`references/design-notes.md`.)

## Shape

```json
{
  "version": "1",
  "skill": "html-codesign",
  "mode": "codesign",
  "title": "Dashboard redesign — pick a direction",
  "lead": "Review each context, toggle your picks, then export.",
  "generated_at": "2026-07-16T09:12:00-07:00",
  "sections": [
    {
      "id": "sec-01-direction",
      "title": "Overall direction",
      "lead": "Pick one — these are mutually exclusive.",
      "exclusive": true,
      "choices": [
        { "id": "ch-01-a", "label": "Focused — one hero number + one chart",
          "detail": "Demote everything else to on-demand detail.",
          "selected": true },
        { "id": "ch-01-b", "label": "Split — hero + a compact 3-tile strip",
          "selected": false }
      ],
      "note": { "id": "note-01", "placeholder": "Why this one?", "value": "" }
    }
  ],
  "contexts": [
    {
      "id": "ctx-01",
      "section": "sec-01-direction",
      "body": "The dashboard's primary job is a five-second status check. A focused layout serves that; a split layout serves browsing, which telemetry says is rare.",
      "recommendation": "Focused — it matches the dominant usage pattern.",
      "recommended": ["ch-01-a"]
    }
  ],
  "feedback": { "id": "note-overall", "value": "" }
}
```

## Field rules

| Field | Rule |
|---|---|
| `version` | always `"1"` |
| `skill` | always `"html-codesign"` (lets downstream tools route) |
| `mode` | always `"codesign"` |
| `title`, `lead` | strings; become the H1 and lead on render |
| `generated_at` | ISO 8601, set at first render |
| `sections[].exclusive` | `true` = pick-one (radio behavior), `false` = pick-any (checkbox behavior) |
| `choices[].label` | ≤ 120 chars, non-empty |
| `choices[].detail` | optional one-line elaboration shown under the label |
| `choices[].selected` | boolean; these are the defaults the page hydrates from |
| `note` | optional per-section free-text block (`id`, `placeholder`, `value`) |
| `contexts` | **required — exactly one entry per section.** See below. |
| `feedback` | optional page-level note; its id is always `note-overall` |

All ids follow `references/id-grammar.md`.

## The contexts layer

Every generated page carries a context per section — the preamble the
reader reviews before choosing. Required at generation, always:

| Field | Rule |
|---|---|
| `id` | `ctx-{NN}`, NN matching the joined section's number |
| `section` | the id of the section this context belongs to |
| `body` | non-empty — the comprehensive view: landscape, constraints, trade-offs |
| `recommendation` | non-empty — the argued case for the recommended pick |
| `recommended` | array of choice ids **in that section**; may be `[]` ONLY when the recommendation text argues why the trade-off is genuinely neutral |

The page renders the context as a collapsible block (open on load) and puts
a ★ badge on each recommended choice. "Followed / went against the
recommendation" is DERIVED at render/export time by comparing `selected`
against `recommended` — never stored.

## What the validator does and doesn't check

`validate_spec.py` enforces: the literal `version`/`skill`/`mode` values,
non-empty `title`, the full ID grammar, global ID uniqueness, unique section
numbers, choice/note/context numbers matching their section, `exclusive`
present as a boolean, ≤1 selected choice in exclusive sections, label
type/length, **exactly one context per section with non-empty
`body`/`recommendation` and resolvable `recommended` ids**, and that no
string contains `</script` (which would truncate the embedded spec tag). It
rejects `codesign-answers` documents outright — it validates inputs only.
It does NOT check: timestamp formats, `lead`/`detail`/`placeholder` types,
or that the rendered DOM mirrors the spec — those are yours to honor (the
SKILL.md smoke test covers the DOM mirror). Run the validator AND do the
smoke test; neither replaces the other.

## Invariants

- Every section has **exactly one** context; every context names a real
  section; every `recommended` id is a choice in that same section.
- An exclusive section ships with **at most one** `selected: true`.
- Ids are globally unique across the whole spec.
- A choice's number matches its section's number (`ch-02-*` lives in
  `sec-02-*`); same for notes (`note-02`) and contexts (`ctx-02`).
- The embedded spec and the DOM agree: every `data-id` in the page exists
  in the spec and vice versa — including one `.ctx` block per context.
- Collapse/hide state is view state — DOM only, never in this document,
  never in exports.
