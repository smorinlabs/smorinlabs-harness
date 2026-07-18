# Birchline codesign overlay

Component treatments for html-codesign pages rendered under Birchline. This
file wins level 1 of the theming cascade (see html-codesign's
`references/theming.md`): apply these on top of the template, sourcing every
color from `tokens.md`. Structure, `data-id`s, and the engine script stay
untouched — this is paint, not plumbing.

## Page frame

- `<meta name="color-scheme" content="light">` and `color-scheme: light` in
  `:root` (Birchline is light-only — no dark query).
- Body: `background: var(--ivory)`, ink `var(--slate)`, `font-weight: 430`,
  body family `var(--font-sans)`.
- H1 in `var(--font-serif)`, weight 500, with the page's ONE
  `<span class="accent">` (italic clay) on the key phrase — nowhere else.
- Section IDs and choice IDs render in the serif italic
  (`var(--font-serif)`, `font-style: italic`, clay for section IDs, muted
  for choice IDs) instead of monospace — Birchline's editorial register.
- **No webfont `<link>`** — codesign pages are self-contained (html-codesign
  hard rule, restated in its `theming.md`). Use the token font stacks and
  let them fall back locally (the serif stack lands on Georgia).

## Tokens for the template's neutral slots

Every value is a `tokens.md` token or a derivation `tokens.md` itself
documents (the 12–16% tint recipe; slate-tinted shadows). No new hex.

| Template token | Birchline value |
|---|---|
| `--ink` | `var(--slate)` |
| `--muted` | `var(--gray-700)` |
| `--bg` | `var(--ivory)` |
| `--card` | `#FFFFFF` (paper white, the card ground `tokens.md` composes on) |
| `--line` | `var(--oat)` |
| `--line-soft` | `var(--gray-100)` |
| `--accent` | `var(--clay)` |
| `--accent-deep` | `color-mix(in srgb, var(--clay) 82%, var(--slate))` (hover-darkened clay) |
| `--sel-bg` | `color-mix(in srgb, var(--clay) 12%, #FFFFFF)` (the documented 12% tint) |
| `--radius` | `var(--r-md)` |
| `--shadow` | `var(--shadow-md)` |

## Component notes

- **Choice cards**: selected state is clay border + the `--sel-bg` warm fill
  (the 12% clay tint above); hover is clay border only. Check glyph on clay.
  Exclusive sections keep the circular box (radio shape).
- **Control bars**: ivory with `backdrop-filter: blur(8px)` at 92% opacity,
  oat hairline. Primary buttons clay → clay-deep on hover; secondary white
  with oat border.
- **Textareas**: ivory fill, oat border, clay focus ring.
- **Export panel**: slate (`var(--slate)`) ground, ivory text
  (`var(--ivory)`), clay top border — the one dark surface on the page,
  framed as "machine output".
- **Stat line / counters**: tabular numerals.

## New components (v0.9.0–v0.10.0 set)

Same sourcing rule: tokens and documented derivations only.

- **Context block** (`.ctx`): `var(--gray-100)` ground, oat hairline,
  `var(--r-sm)` radius — a nested surface per `tokens.md`. The
  `.ctx-toggle` caption is gray-500 uppercase; its chevron rotates, no
  other motion. The `.ctx-what` / `.ctx-why` lead-ins ("What this is:",
  "Why you're being asked:") render their `<b>` at **weight 500 slate** —
  never bold (anti-pattern) and never clay (the accent span stays unique
  to the H1). `.ctx-free` tables: `var(--gray-100)` header row, oat cell
  hairlines, small sans text.
- **Recommendation callout** (`.ctx-rec`): `var(--oat)` fill with a 3px
  clay left border — the theme's callout recipe. The ★ and the choice id
  render clay; the id keeps Birchline's serif italic register.
- **Rec badge** (`.badge-rec`): pill on the documented 12% clay tint
  (`color-mix(in srgb, var(--clay) 12%, #FFFFFF)`), clay text, clay
  hairline, caption size. Sits quietly next to the label — the ★ carries
  the meaning, not weight.
- **Summary rows** (`.summary`): question in weight 500 slate; picks
  (`.s-sel`) in `var(--accent-deep)` (hover-darkened clay). Markers
  (`.s-mark-*`): followed = `var(--success)` sage, went-against and open
  question = `var(--warning)` amber, skipped = `var(--gray-500)` — full
  color text, no tinted chips (semantic tints stay for surfaces). Note
  excerpt gray-700.
- **Section actions** (`.sec-actions`: `.opt-toggle`, `.skip-toggle`,
  `.ask-toggle`): quiet secondary buttons — white ground, oat border,
  gray-700 text, sentence case. Active skip (`aria-pressed="true"`) fills
  `var(--gray-100)` with slate text; no color shout — skipping is calm.
- **Question field** (`.q-wrap`): label is the amber caption
  (`var(--warning)`, uppercase, .08em); textarea matches the note fields
  (ivory fill, oat border, clay focus ring).
- **Export toggle** (`.seg` / `.seg-btn`): white ground, oat border;
  the pressed `.seg-btn` fills clay with white text — the same primary
  treatment as the export buttons it governs.

## Birchline rules that bind codesign pages

From `anti-patterns.md`, restated because codesign pages are dense with UI:

- Exactly ONE `.accent` span, in the H1. Choice labels never use it.
- No `font-weight: bold` — emphasis is weight 500–600 or `<em>` (slate).
- All shadows `rgba(20, 20, 19, *)` — never pure black.
- Sentence case everywhere, including buttons ("Export → MD" keeps its
  arrow; "Another draft", not "Another Draft").
- No gradients, no glassmorphism beyond the bar blur, flat fills only.
- One handcrafted detail per page is welcome (a slightly imperfect
  underline, a tilted oval behind a count) — see `illustrations.md`.
