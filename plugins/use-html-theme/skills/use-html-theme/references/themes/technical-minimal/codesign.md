# Technical-minimal codesign overlay

Component treatments for html-codesign pages rendered under Technical-minimal.
Wins level 1 of the theming cascade (see html-codesign's `references/theming.md`):
apply on top of the template, sourcing every color from this theme's
`tokens.md`. Structure, `data-id`s, and the engine script stay untouched —
paint, not plumbing.

Technical-minimal is the closest theme to the template's own neutral default,
so this overlay is deliberately thin: it pins the neutral slots to the real
Technical-minimal tokens and tightens the geometry. The register is a docs
site — flat, precise, monospace IDs — so unlike Birchline, IDs stay in
`var(--font-mono)`, not serif.

## Page frame

- `<meta name="color-scheme" content="light">` and `color-scheme: light` in
  `:root` (light theme).
- Body: `background: var(--surface-2)`, ink `var(--ink)`, `var(--font-sans)`,
  weight `var(--fw-regular)`.
- H1 in `var(--font-sans)`, `var(--fw-semibold)`, `--fs-h1`. No serif, no
  italic accent — emphasis is weight and the single blue accent only.
- Section and choice IDs stay monospace (`var(--font-mono)`, `--ink-muted`).

## Tokens for the template's neutral slots

Every value is a `tokens.md` token — no new hex.

| Template token | Technical-minimal value |
|---|---|
| `--ink` | `var(--ink)` |
| `--muted` | `var(--ink-muted)` |
| `--bg` | `var(--surface-2)` |
| `--card` | `var(--surface)` |
| `--line` | `var(--border)` |
| `--line-soft` | `var(--surface-3)` |
| `--accent` | `var(--accent)` |
| `--accent-deep` | `var(--accent-hover)` |
| `--sel-bg` | `var(--accent-soft)` |
| `--radius` | `var(--r-lg)` |
| `--shadow` | `var(--shadow-md)` |
| `--font` | `var(--font-sans)` |
| `--mono` | `var(--font-mono)` |

## Component notes

- **Choice cards**: selected = `var(--accent)` border + `var(--accent-soft)`
  fill; hover = accent border only. Square checkbox (`--r-sm`) for pick-any,
  circle for exclusive. Check glyph `var(--on-accent)` on accent.
- **Control bars**: `var(--surface)` with a `var(--border)` hairline; the
  blur is optional and can be dropped for a flatter docs feel. Primary
  buttons `var(--accent)` → `var(--accent-hover)`; secondary `var(--surface)`
  with border.
- **Textareas**: `var(--surface-2)` fill, `var(--border)` line, accent focus
  ring.
- **Export panel**: keep it distinct from the light page — `var(--ink)` ground
  with `var(--surface)` text and an `var(--accent)` top border, so "machine
  output" still reads as a separate surface.
- **IDs, counters, stat lines**: monospace, tabular numerals.

## Technical-minimal rules that bind codesign pages

From this theme's `anti-patterns.md`:

- 1px borders only — no heavy strokes; radii stay tight (`--r-sm`…`--r-lg`).
- Single blue accent; never a second accent hue. Semantic colors
  (success/warning/danger) are separate and only for status, not decoration.
- No serif anywhere; no italic display.
- No warm-tinted shadows — shadows are neutral `rgba(0,0,0,*)` per `tokens.md`.
- Fonts are system stacks; **no webfont `<link>`** (codesign pages are
  self-contained — html-codesign hard rule).
