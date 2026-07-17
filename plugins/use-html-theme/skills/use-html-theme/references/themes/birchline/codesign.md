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
