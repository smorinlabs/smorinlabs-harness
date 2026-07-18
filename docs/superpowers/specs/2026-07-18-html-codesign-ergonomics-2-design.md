# html-codesign ergonomics 2 — skip, ask channel, free-form context

**Date:** 2026-07-18
**Target skill:** `plugins/use-html-theme/skills/html-codesign` (v0.8.0 state)
**Status:** approved (co-designed and signed off by Steve in-session)
**Implementation route:** skill-create (update mode); plugin 0.5.0 → 0.6.0
**Predecessor:** `2026-07-17-html-codesign-ergonomics-design.md`

## Root cause this revision addresses

A codesign page must work for a reader who *wasn't in the room*. The v0.8.0
release enforced that structurally (every section has a context) but not
qualitatively (the context can still be session jargon — the first real page
proved it with "Theme overlay coverage · .ctx, .summary, .badge-rec…") and
not interactively (a reader who can't answer has no way to say so). The
three features below close those gaps. Record this framing in
`references/design-notes.md`.

## Decisions (locked in co-design)

1. **Skip on every question** — engine-provided control, MD omits skipped
   sections, JSON records `skipped: true`.
2. **Ask channel** — per-section question capture + a "Questions first"
   batch paste-back button.
3. **Context = schema envelope + free-form body** — contract bits stay in
   JSON; the body becomes unrestricted HTML in the page.
4. **Clarity via default scaffold + hard authoring rules** — `.ctx-what` /
   `.ctx-why` slots, question-shaped titles, written for outsiders.
5. **Full exports carry the envelope only** — the self-contained page file
   is the durable rich-context archive.

## 1. Skip

- The template ships a **Skip control on every section** (engine-level, not
  a spec choice — authoring agents cannot forget it; no ID churn).
- Selecting Skip clears the section's selections; making a selection clears
  Skip. Works identically for pick-one and pick-any.
- Summary row shows `⏩ skipped`.
- **Exports:** slim and full MD omit the section entirely — unless it also
  has an open question, in which case only the question line renders
  (questions always surface; skip governs decision content only). JSON
  keeps the answer entry as `{ "section": …, "skipped": true }` (no
  `selected`; plus `question` if one was raised), so the loop can
  distinguish *deliberately not decided* from *never asked*.
- **Iteration:** on a v2, a skipped section is dropped or re-framed at the
  agent's judgment (with the user's cues) — never silently re-asked as-is.
- Skip state is decision state at export time but needs no spec field: a v2
  spec simply includes or omits the section.

## 2. Ask channel ("I need more context")

- Each section gets an **"Ask a question"** affordance that reveals a small
  question field — separate from the note (**note = why I chose; question =
  what I need to know**; both can coexist on one section).
- Question fields carry a new ID prefix: **`q-{NN}`** (number matches the
  section), added to `id-grammar.md`. Like notes, the elements are
  template-provided per section.
- New control-bar button **"Questions first"**: bundles every raised
  question into one paste-back prompt with section/ctx IDs, e.g.
  `Before I decide "<title>": sec-01 (ctx-01): <question> · sec-04: <question>
  — answer these, then I'll continue.` Copies to clipboard like the other
  re-prompts.
- **Exports:** JSON answer entries gain `"open_question": <text>` when
  raised (`"question"` was already taken by the section title in the
  answers schema).
  In MD, a section with an open question and no picks renders the question
  (`❓ **Open question (`q-01`):** …`) instead of a decision; with picks
  *and* a question, both render.
- Summary row gains a `❓` marker when a question is open.

## 3. Context: envelope in schema, body free-form

The `contexts[]` entry slims to the **envelope** — exactly the parts other
machinery depends on:

```json
{
  "id": "ctx-01",
  "section": "sec-01-overlays",
  "summary": "The three themes don't yet style this page's newer parts.",
  "recommendation": "All three in one pass — proven pattern, small scope.",
  "recommended": ["ch-01-a"]
}
```

| Field | Consumer |
|---|---|
| `id` | chat reference ("expand ctx-02"), one-per-section validator guarantee |
| `section` | the join |
| `summary` | **new** — one plain-text line; full exports and unanswered summary rows |
| `recommendation` | argued sentence; ★ callout text, full exports |
| `recommended` | ★ badges, followed/went-against verdicts |

The **body leaves the schema**: the page's `.ctx` block holds free-form
HTML — multi-paragraph prose, comparison tables, inline SVG charts (dataviz
skill applies), `data:`-URI images, side-by-side mockups. Self-containment
remains a hard rule (no external requests; SVG-first over data-URI bloat).

- Validator changes: `summary` required non-empty; `body` **no longer part
  of the schema** — if present (a v0.8.0-era spec), it is ignored as a
  legacy extra, not an error.
- The DOM-mirror invariant extends: every ctx envelope has a `.ctx` block
  with a non-empty payload — checked by the smoke test (the JSON validator
  cannot see the DOM).

## 4. Clarity: scaffold + authoring rules

Template's `.ctx` block ships with default slots, filled by default and
freely extendable/replaceable when a visual serves better:

```html
<div class="ctx" data-id="ctx-01" data-open="true">
  <button class="ctx-toggle">Context &amp; recommendation</button>
  <p class="ctx-what"><b>What this is:</b> …orientation, zero jargon…</p>
  <p class="ctx-why"><b>Why you're being asked:</b> …what the answer drives…</p>
  <!-- free zone: prose / pros-cons table / inline SVG chart / data-URI image -->
  <p class="ctx-rec">★ Recommends <span class="cid">ch-01-a</span> … — <argued case></p>
</div>
```

Hard authoring rules added to SKILL.md:

- **Titles are real questions.** "Which themes should learn the new look?"
  — never a noun phrase like "Theme overlay coverage".
- **Write for a reader who wasn't in the room.** Zero session jargon;
  define every term of art the first time it appears.
- **Orient before arguing.** `ctx-what` first, `ctx-why` second, analysis
  after. Pros/cons live in the free zone (table or list) when they help.
- Smoke test checks orientation-first; the plugin validator checks the
  scaffold classes exist in the template.

## 5. Exports

- **Slim:** unchanged shape (ID · question · picks · note), now minus
  skipped sections (MD) / with `skipped: true` (JSON), plus `question`
  fields where raised.
- **Full:** per-section context becomes envelope-only — `summary`,
  `recommendation`, `recommended`, verdict — plus a one-line pointer that
  the rich context (charts, tables) lives in the page file. No innerText
  extraction of free-form HTML (lossy, nondeterministic).
- `codesign-answers` version stays `"1"` (additive fields only).

## Out of scope

- Theme overlay updates for the new/changed component classes — deliberately
  sequenced AFTER this lands (the component set changes here); tracked as
  follow-on work.
- Any change to the trigger description (capability change only).
- Persisting skip/question/collapse view state into the spec.
- Auto-collapse behaviors (still rejected).

## Verification

- Fixtures first: valid fixture moves to envelope form; invalid fixture
  gains missing-`summary` and legacy-`body`-tolerated cases.
- `validate_spec.py` green/red as designed; plugin `validate.py` extended
  (scaffold classes, skip/ask controls present in template).
- Browser assertion pass: skip clears picks and vice versa; skipped section
  absent from MD, `skipped: true` in JSON; ask flow (reveal field, Questions
  first prompt, export fields); scaffold renders; envelope-only full export;
  exports still ignore all view state.
- skill-quality gate; skill load verification on both tools.

## Sequencing note

Parallel in-flight work holds P14 (pr-merge-flow, v0.9.0). This work is
**P15**, release target **v0.10.0**. Shared files (PROJECTS.md, README.md,
marketplace.json) are dirty with that work — commits for this project stage
only their own hunks.
