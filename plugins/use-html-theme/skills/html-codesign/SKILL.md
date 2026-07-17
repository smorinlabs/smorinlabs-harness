---
name: html-codesign
description: |
  Build an interactive "codesign" decision page as a single self-contained
  HTML file: the reader toggles choices (pick-one or pick-any sections), adds
  notes, and exports the decision as Markdown and JSON with stable IDs
  (sec-01, ch-01-a) so picks can be quoted in chat and iterated — "keep
  ch-01-a, swap ch-02-b" yields a diffable v2. Use whenever the user wants to
  choose between options and capture the decision: design directions, plan A
  vs plan B, prioritization passes, "pick from these" reviews, option pages a
  stakeholder reviews async and sends back. Trigger phrases: codesign,
  co-design, decision page, pick from these, which should we, compare the
  options, choose and export, design directions, prioritize these. Pairs with
  use-html-theme — the active theme styles the page; without one it falls
  back to a built-in neutral style. NOT for signing macOS/iOS apps or
  binaries (Apple's codesign tool).
allowed-tools: Read Write Edit Glob Bash AskUserQuestion
---

# What this makes

A single `.html` file that turns a decision into something a person can
*operate*: sections of choices (pick-one or pick-any), per-section notes, and
a control bar whose four buttons are the whole contract — **Export → MD**,
**Export → JSON**, **Another draft**, **Here are my answers**. The reader —
who may not be in this chat at all — opens the file anywhere, clicks, and
sends the export back. That text round-trip is the interface; it works
identically whether the page was generated from Claude Code, Codex, or
anything else, because the page never needs a live connection to an agent.

# When this skill applies

✓ "Give me 4 layout directions and let me pick"
✓ "Make a decision page for plan A vs plan B"
✓ "I want to prioritize these features — let me toggle and export"
✓ "Codesign the palette with me"
✗ A read-only page, report, or writeup (that is plain themed HTML — use-html-theme alone)
✗ A quick either/or the user can answer in chat (just ask; AskUserQuestion exists)
✗ Anything about signing apps or binaries — Apple's `codesign` is unrelated

# Process

1. **Shape the decision.** Identify the sections (one per question), whether
   each is pick-one (`exclusive: true`) or pick-any, the 2–5 choices each,
   and sensible defaults. If the structure is genuinely ambiguous, ask ONE
   clarifying question (AskUserQuestion if available; plain numbered chat
   list otherwise).

2. **Write the spec first.** Author the `codesign-spec` JSON to
   `references/spec-format.md`, with IDs per `references/id-grammar.md`.
   Write it to a file next to where the artifact will go.

3. **Validate before rendering.** Run
   `scripts/validate_spec.py <spec-file>` (stdlib Python, no deps). Fix
   until exit 0. Never render from an unvalidated spec — a duplicate ID or a
   double-selected exclusive section breaks the page silently.

4. **Resolve the theme.** Follow `references/theming.md`: use the
   use-html-theme session theme if one is active, else its persistence file,
   else the neutral built-in style. Never mix themes.

5. **Render from the template.** Start from
   `assets/codesign-template.html`. Embed the validated spec verbatim in the
   `<script id="codesign-spec" type="application/json">` tag, author the DOM
   to match it (every `data-id` mirrors a spec id), and keep the engine
   script intact. Apply the theme layer per step 4.

6. **Deliver and explain the loop.** Give the file path (and open/preview it
   when the platform can). Tell the user the reader can export MD/JSON or
   click "Another draft" / "Here are my answers" and paste the result back
   into any chat with you.

7. **On a returned export or re-prompt**, follow
   `references/iteration-loop.md`: reuse every surviving ID, mint new IDs
   only for new choices, and treat the returned `selected` values as the
   user's decision.

# Hard rules

- **Self-contained.** One `.html`, embedded CSS/JS, no external requests, no
  build step. The file must work from `file://`, an artifact host, or an
  email attachment.
- **The spec is the source of truth** and ships inside the page. DOM
  `data-id`s mirror it exactly.
- **IDs are stable.** Once shipped, an ID means the same thing in every
  export, chat message, and v2. Never re-letter surviving choices.
- **Both exports, always.** MD for humans (PRs, Slack, docs — reads like a
  lightweight decision record), JSON for machines (re-render, diff,
  validate). Don't make the user choose.
- **Exclusive means exclusive.** Pick-one sections enforce a single
  selection in the UI and are validated to ship with at most one default.
- **Declare the color scheme.** Light theme → `<meta name="color-scheme"
  content="light">`; dark theme → `dark`. (iOS Safari auto-darkens pages
  that don't declare.)
- **Keyboard and motion basics.** Visible `:focus-visible` states; respect
  `prefers-reduced-motion`.

# Quick smoke test

1. Does `validate_spec.py` exit 0 on the embedded spec?
2. Click every choice: do exclusive sections enforce pick-one?
3. Does Export → MD reflect exactly the current toggles and notes?
4. Is the right `color-scheme` meta present?

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
  it's a plain themed page; hand it to use-html-theme conventions instead.
