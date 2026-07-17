# codesign-spec format

The JSON contract behind every codesign page. Written FIRST (before any HTML),
validated with `scripts/validate_spec.py`, embedded verbatim in the page as
`<script id="codesign-spec" type="application/json">`, and re-emitted (with
the user's selections and notes) by Export → JSON. One schema for all three
moments: plan, page, export.

## Shape

```json
{
  "version": "1",
  "skill": "html-codesign",
  "mode": "codesign",
  "title": "Dashboard redesign — pick a direction",
  "lead": "Toggle the pieces you want, then export your picks.",
  "generated_at": "2026-07-16T09:12:00-07:00",
  "exported_at": "2026-07-16T09:47:21-07:00",
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
| `exported_at` | ISO 8601, set by the page at export time (absent in the plan spec) |
| `sections[].exclusive` | `true` = pick-one (radio behavior), `false` = pick-any (checkbox behavior). **This replaces per-choice constraint strings** — section-level exclusivity covers real decisions without cross-reference bookkeeping. |
| `choices[].label` | ≤ 120 chars, non-empty |
| `choices[].detail` | optional one-line elaboration shown under the label |
| `choices[].selected` | boolean; in the plan spec these are the defaults; in an export they are the user's picks |
| `note` | optional per-section free-text block (`id`, `placeholder`, `value`) |
| `feedback` | optional page-level note; its id is always `note-overall` |

All ids follow `references/id-grammar.md`.

## What the validator does and doesn't check

`validate_spec.py` enforces: the literal `version`/`skill`/`mode` values,
non-empty `title`, the full ID grammar, global ID uniqueness, unique section
numbers, choice/note numbers matching their section, `exclusive` present as a
boolean, ≤1 selected choice in exclusive sections, label type/length, and
that no string contains `</script` (which would truncate the embedded spec
tag). It does NOT check: timestamp formats, `lead`/`detail`/`placeholder`
types, or that the rendered DOM mirrors the spec — those are yours to honor
(the SKILL.md smoke test covers the DOM mirror). Run the validator AND do the
smoke test; neither replaces the other.

## Invariants

- An exclusive section ships with **at most one** `selected: true`.
- Ids are globally unique across the whole spec.
- A choice's number matches its section's number (`ch-02-*` lives in `sec-02-*`).
- The embedded spec and the DOM agree: every `data-id` in the page exists in
  the spec and vice versa.
