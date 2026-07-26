---
name: html-codesign
description: |
  Build an interactive "codesign" decision page as one self-contained HTML
  file: the reader toggles choices (pick-one or pick-any), adds notes, and
  exports the decision as Markdown and JSON with stable IDs (sec-01, ch-01-a)
  so picks can be quoted in chat — "keep ch-01-a, swap ch-02-b" yields a
  diffable v2. Use when the user wants to choose between options and capture
  the decision: design directions, plan A vs B, prioritization, async option
  pages for a stakeholder. Triggers: codesign, co-design, decision
  page, pick from these, which should we, compare the options, prioritize
  these. ALWAYS confirms before generating — lists the UNANSWERED questions
  found in recent context, each with its ID and a recommendation, then waits
  for a yes; the gate fires even on explicit invocation with an argument.
  Answered questions are out of scope; if context is mostly settled material
  it offers html-explain instead. Styled by use-html-theme. NOT for signing
  macOS/iOS binaries (Apple's codesign).
allowed-tools: Read Write Edit Glob Bash AskUserQuestion
---

# What this makes

A single `.html` file that turns a decision into something a person can
*operate*: sections of choices (pick-one or pick-any), each opening with a
collapsible **context & recommendation** preamble — free-form content
(prose, tables, inline SVG charts, images) shaped by a clarity scaffold,
with a ★ badge on the recommended option — plus per-section notes, a
**Skip** control on every question (deliberately-not-deciding is a
first-class answer), an **Ask a question** channel for "I can't answer
this yet", and three layers of manual collapse — fold the context away,
hide unchosen options (note stays visible), or fold a whole section to a
dense one-line summary (question · picks · followed/went-against marker ·
note) so a finished page scans as a review of the decision. The control
bar carries the contract — **Export → MD**, **Export → JSON** (slim by
default, full by toggle), **Another draft**, **Here are my answers**,
**Questions first**, plus Collapse/Expand all. The reader — who may not
be in this chat at all — opens the file anywhere, clicks, and sends the
export back. That text round-trip is the interface; it works identically
whether the page was generated from Claude Code, Codex, or anything else,
because the page never needs a live connection to an agent.

# When this skill applies

✓ "Give me 4 layout directions and let me pick"
✓ "Make a decision page for plan A vs plan B"
✓ "I want to prioritize these features — let me toggle and export"
✓ "Codesign the palette with me"
✗ A read-only page, report, or writeup (that is plain themed HTML — use-html-theme alone)
✗ A quick either/or the user can answer in chat (just ask; AskUserQuestion exists)
✗ Anything about signing apps or binaries — Apple's `codesign` is unrelated

# Preflight — triage and confirm, before anything else

Run `../../references/context-triage.md` in full, then **gate**.

**Never open codesign without human confirmation.** Building a decision page
is expensive, and a page of the wrong questions is worse than no page — it
re-litigates settled work and asks the user to spend attention on choices
they already made or never had.

The gate fires **every time**:

- when the skill was inferred from a natural-language request
- **when the user invoked it explicitly** (`/html-codesign`)
- **when the user supplied an argument** naming a topic

An explicit invocation settles *which page type*, not *which questions*. An
argument narrows the target but rarely pins the exact set — "codesign the
caching questions" still leaves which ones, and whether the ones you found
are the ones meant. An argument shortens the gate to a confirmation. It
never removes it.

**Show the actual questions before asking.** List every section you would
put on the page, each with the `sec-NN` ID it will carry and the
recommendation you would argue — that is what makes the confirmation
meaningful rather than ceremonial:

```
Recent context has 4 open questions. Here's how I'd shape the page:

  sec-01  Should the fallback ship as its own module, or fold into core?
          → I'd argue fold in — one less package to version.
  sec-02  Do we keep the v1 endpoint alive through the migration?
          → I'd argue yes, behind a deprecation header.
  sec-03  Who owns the rotation runbook — platform or on-call?
          → Genuinely neutral; I'd lay out both and not recommend.
  sec-04  Ship behind a flag, or straight to default-on?
          → I'd argue flag — the blast radius is the whole write path.

A codesign page poses each of these with a reasoned recommendation and
lets you pick, skip, or ask back. It doesn't decide for you.

Generate it for these four?
```

Frame the value honestly: **codesign poses questions with recommendations —
it does not decide.** A user who thinks they're delegating the decision has
misunderstood what they'll get back.

**The gate is TWO turns, never one.** Same-turn prose may never render — when
a turn ends in a tool call the user can receive only the dialog, which here
would mean approving a page whose questions they never saw. That is worse
than no gate at all. So the question list above **ends its turn — no tool
call of any kind after it** — and AskUserQuestion opens the next one.

Belt and suspenders: write every option to stand alone, in case the pre-read
is lost anyway. "Generate the page for these 4 (sec-01…sec-04)" beats "Yes".

One AskUserQuestion, triage verdict recommended first, always including:

- **just answer them here in chat** → `question-walkthrough`
- **wrong set — these are settled** → `html-explain`
- **a different topic entirely**

**Unanswered questions only.** A question already asked *and answered* is
settled material — it belongs to `html-explain` as a deep dive on how it was
resolved. Never re-pose it. The user may explicitly ask to revisit one; that
is their call to make, never an offer to pad the page with.

If triage finds little that is open and a lot that is settled, say so and
offer `html-explain` as the recommended option instead.

# Process

1. **Shape the decision.** Identify the sections (one per question), whether
   each is pick-one (`exclusive: true`) or pick-any, the 2–5 choices each,
   and sensible defaults. If the structure is genuinely ambiguous, ask ONE
   clarifying question (AskUserQuestion if available; plain numbered chat
   list otherwise).

2. **Author a context per section — always.** Two parts. The spec gets the
   **envelope** — a one-line `summary`, an argued `recommendation`, and
   the `recommended` choice id(s); a page without one per section is
   invalid (empty `recommended` only when the recommendation text argues
   why the trade-off is genuinely neutral). The **body** is free-form HTML
   authored in the page's `.ctx` block, default-shaped by the clarity
   scaffold: `.ctx-what` (what this decision is, in plain words), then
   `.ctx-why` (why it's being asked, what the answer drives), then a free
   zone — prose, a pros/cons table, an inline SVG chart, a `data:`-URI
   image, whatever genuinely orients — then the `.ctx-rec` ★ callout.
   **Hard writing rules:** section titles are real questions ("Which
   themes should learn the new look?", never "Theme overlay coverage");
   write every context for a reader who was never in this chat — zero
   session jargon, define each term of art at first use, orient before
   arguing.

3. **Write the spec first.** Author the `codesign-spec` JSON to
   `references/spec-format.md`, with IDs per `references/id-grammar.md`.
   Write it to a file next to where the artifact will go.

4. **Validate before rendering.** Run
   `scripts/validate_spec.py <spec-file>` (stdlib Python, no deps). Fix
   until exit 0. Never render from an unvalidated spec — a duplicate ID, a
   missing context, or a double-selected exclusive section breaks the page
   silently.

5. **Resolve the theme.** Follow `references/theming.md`: use the
   use-html-theme session theme if one is active, else its persistence file,
   else the neutral built-in style. Never mix themes.

6. **Render from the template.** Start from
   `assets/codesign-template.html`. Embed the validated spec in the
   `<script id="codesign-spec" type="application/json">` tag (the validator
   already rejects strings containing `</script`; if you must keep such
   text, escape `/` as `\/` — valid JSON, HTML-safe), author the DOM to
   match it — every `data-id` mirrors a spec id, one `.ctx` block per
   contexts envelope (scaffold + free-form body per step 2), a
   `.badge-rec` on each recommended choice, and each section's `.summary`
   row, `.fold` button, `.sec-actions` (opt/skip/ask toggles), and
   `.q-wrap` with its `q-NN` textarea in place — and keep the engine
   script intact. Apply the theme layer per step 5.

7. **Deliver and explain the loop.** Give the file path (and open/preview it
   when the platform can). Tell the user the reader can review then collapse
   each context, **skip questions they're not deciding**, **raise a
   question when they can't answer** ("Questions first" bundles them into
   a paste-back), fold answered sections to scan their decisions, and
   export MD/JSON (slim by default; Full toggle for a human decision
   record) or click "Another draft" / "Here are my answers" and paste the
   result back into any chat with you.

   Then close out per `../../references/delivery-close.md`: the **full
   absolute path on its own line** (never relative — the reader is often not
   in the shell that made the file), and a short prose list of what they might
   want next. Those offers are strictly conditional — open it in the browser
   only when this session can actually reach one, add it to `shelf` only when
   that skill is installed (if it isn't, don't mention it at all), and where
   to save it whenever the file landed somewhere temporary. The paste-back
   loop above leads; these come after it.

8. **On a returned export or re-prompt**, follow
   `references/iteration-loop.md`: reuse every surviving ID, mint new IDs
   only for new choices, re-author every section's context for the v2,
   honor skips (drop or re-frame, never re-ask unchanged), answer every
   `open_question` quoting its `q-NN`, and treat the returned selections
   as the user's decision.

# Hard rules

- **Never generate without the preflight gate.** Triage, show the questions
  with their IDs and recommendations, get a human yes. Explicit invocation
  and a supplied argument shorten the gate; neither skips it.
- **Only unanswered questions.** Already-decided ones are `html-explain`'s
  material, not this skill's.
- **Self-contained.** One `.html`, embedded CSS/JS, no external requests, no
  build step. The file must work from `file://`, an artifact host, or an
  email attachment.
- **The spec is the source of truth** and ships inside the page. DOM
  `data-id`s mirror it exactly.
- **IDs are stable.** Once shipped, an ID means the same thing in every
  export, chat message, and v2. Never re-letter surviving choices.
- **Every section gets a context.** Envelope (summary + argued
  recommendation + recommended ids) validator-enforced at generation; body
  free-form in the page, never in the schema. Exports carry the envelope
  at most (that's what slim/full mean) — the page always carries the full
  body.
- **Skip is a first-class answer.** Every section has the engine's Skip
  control; skipped sections leave the MD record but export
  `skipped: true` in JSON so the loop never re-asks unchanged.
- **Questions always surface.** An open `q-NN` appears in every export and
  re-prompt, even on skipped sections — skip governs decision content
  only.
- **Both exports, always.** MD for humans, JSON for machines — both emitted
  as `codesign-answers` documents (`references/export-formats.md`), slim by
  default with a Full toggle. Don't make the user choose a format.
- **Collapse is view state.** Section folding, hidden options, context
  open/closed, and the Slim/Full toggle live in the DOM only — identical
  picks export identically however the page is folded.
- **Exclusive means exclusive.** Pick-one sections enforce a single
  selection in the UI and are validated to ship with at most one default.
- **Deliver the absolute path.** The full path, on its own line, every time.
  A relative path is only meaningful from a working directory the reader
  can't see.
- **Declare the color scheme.** Light theme → `<meta name="color-scheme"
  content="light">`; dark theme → `dark`. (iOS Safari auto-darkens pages
  that don't declare.)
- **Keyboard and motion basics.** Visible `:focus-visible` states; respect
  `prefers-reduced-motion`.

# Quick smoke test

1. Does `validate_spec.py` exit 0 on the embedded spec?
2. Does every spec id have a matching `data-id` in the DOM, and vice versa —
   including one `.ctx` block **with a non-empty free-form body** per
   contexts envelope? (On load the engine hydrates selections FROM the
   spec — a mismatched `data-id` silently drops that choice from exports.)
3. Clarity pass: is every section title a real question; does every
   context open with `.ctx-what` orientation a stranger could follow (no
   session jargon), then `.ctx-why`?
4. Click every choice: do exclusive sections enforce pick-one? Does each
   recommended choice show its ★ badge?
5. Skip/ask pass: does Skip clear the section's picks (and picking clear
   Skip); does "Ask a question" reveal the `q-NN` field; does "Questions
   first" bundle every non-empty question into the paste-back?
6. Collapse pass: does the context block fold and reopen; does
   "Hide unchosen options" leave the question, picks, and note visible;
   does folding a section show the dense summary (picks + rec/skip/❓
   markers + note excerpt); do Collapse all / Expand all work?
7. Export pass: does slim MD/JSON carry exactly ID · question · picks ·
   note; is a skipped section absent from MD but `skipped: true` in JSON;
   does an `open_question` surface in both; does Full add the context
   envelope (summary + rec + verdict — never the body), all options, and
   the followed/went-against verdict; do exports ignore collapse state?
8. Is the right `color-scheme` meta present?
9. Delivery pass: is the **full absolute path** on its own line? Are the
   convenience offers conditional — browser-open only if this session can
   reach one, `shelf` only if that skill is installed (and unmentioned if
   not)?

# Gotchas

- **Don't reimplement theming.** Tokens and component looks come from
  use-html-theme (or the neutral fallback) — this skill owns structure,
  behavior, and exports only.
- **Don't add a server or live callback.** The paste-back loop is the
  portable contract; a live "regenerate" button only works on hosts that
  provide a runtime and would silently break everywhere else.
- **Don't bloat sections.** More than ~5 choices per section means the
  decision is under-shaped — split the section or pre-filter with the user.
- **A "report" request is not codesign.** If nothing is chosen or exported,
  it's an explainer — hand it to `html-explain`, which owns read-only pages
  and their figures.
- **"They invoked it explicitly, so they know what they want."** They know
  the page *type*. They have not seen which questions you found. That is the
  whole content of the page and the entire point of the gate.
- **"The question list is right there above the dialog."** It may not be. A
  turn that ends in a tool call can reach the user as the dialog alone, so a
  same-turn question list is one that might never exist — and then the gate
  collects approval for a page nobody reviewed. Two turns, and options that
  stand on their own.
- **A recently-asked question is ambiguous, not obvious.** Codesign *poses*
  it for decision; `html-explain` *deep-dives* it without asking for a pick.
  When the request could mean either, offer both rather than guessing —
  this is where triage most often goes wrong.
- **Slim is the default paste-back.** The agent already holds the contexts
  it authored — a full export pasted into chat re-sends them for nothing.
  Full is for human decision records (PRs, `docs/decisions/`); either way
  the page file itself is the archive of the rich context.
- **The clarity failure mode is jargon, not length.** "Theme overlay
  coverage · .ctx, .summary…" shipped once and was undecipherable — the
  scaffold exists because a context that argues before it orients is
  worthless to the stranger it's written for.
- **Editing this skill?** Read `references/design-notes.md` first — it
  records the AskUserQuestion lineage of the sections core, the
  input/output schema split, and the invariants edits must preserve.

# See also

- `../../references/context-triage.md` — the shared preflight this skill
  runs before anything else; the routing authority between the two page
  skills.
- `html-explain` (this plugin) — the sibling: read-only explainer pages for
  settled material, including a deep dive on a question already resolved.
- `../../references/delivery-close.md` — the shared close-out: absolute
  path, then the conditional convenience offers.
- `use-html-theme` (this plugin) — owns the page's look.
- `question-walkthrough` (this marketplace) — the synchronous alternative:
  the same open questions worked through one at a time in chat.
