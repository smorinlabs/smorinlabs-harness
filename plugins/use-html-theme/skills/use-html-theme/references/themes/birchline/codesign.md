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

## Tokens for the template's neutral slots

| Template token | Birchline value |
|---|---|
| `--ink` | `var(--slate)` `#141413` |
| `--muted` | `#5C574E` |
| `--bg` | `var(--ivory)` `#FAF9F5` |
| `--card` | `#FFFFFF` |
| `--line` | `var(--oat)` `#E3DACC` |
| `--line-soft` | `var(--gray-100)` `#F0EEE6` |
| `--accent` | `var(--clay)` `#D97757` |
| `--accent-deep` | `#B85C3E` |
| `--sel-bg` | `#FBF1EC` (12% clay tint on white) |
| `--radius` | `10px` |
| `--shadow` | `0 1px 2px rgba(20,20,19,.06), 0 6px 20px rgba(20,20,19,.06)` |

## Component notes

- **Choice cards**: selected state is clay border + `#FBF1EC` warm fill;
  hover is clay border only. Check glyph on clay. Exclusive sections keep
  the circular box (radio shape).
- **Control bars**: ivory with `backdrop-filter: blur(8px)` at 92% opacity,
  oat hairline. Primary buttons clay → clay-deep on hover; secondary white
  with oat border.
- **Textareas**: ivory fill, oat border, clay focus ring.
- **Export panel**: slate (`#141413`) ground, warm off-white text
  (`#EDE7DC`), clay top border — the one dark surface on the page, framed as
  "machine output".
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
