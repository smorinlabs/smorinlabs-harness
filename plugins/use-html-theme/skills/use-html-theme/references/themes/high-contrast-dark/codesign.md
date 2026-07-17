# High-contrast-dark codesign overlay

Component treatments for html-codesign pages rendered under High-contrast-dark.
Wins level 1 of the theming cascade (see html-codesign's `references/theming.md`):
apply on top of the template, sourcing every color from this theme's
`tokens.md`. Structure, `data-id`s, and the engine script stay untouched —
paint, not plumbing.

This is the one overlay that FLIPS the template: the built-in default is
light, so this overlay must switch the color-scheme to dark and repaint every
surface. Layer the near-black surfaces (page darkest, cards one step up) so
the structure reads without heavy borders.

## Page frame — flip to dark

- `<meta name="color-scheme" content="dark">` (NOT light) AND
  `color-scheme: dark` in `:root`. Both must change; a light meta on a dark
  page makes iOS Safari mis-handle form controls.
- Body: `background: var(--surface)` (near-black), ink `var(--ink)` — the
  **off-white** `#FAFAFA`, never pure white (theme anti-pattern).
- H1 `var(--font-sans)`, `var(--fw-semibold)`, `--fs-h1`. Emphasis is weight
  and the single saturated accent; no serif, no italic.
- Section/choice IDs monospace (`var(--font-mono)`, `--ink-muted`).

## Tokens for the template's neutral slots

Every value is a `tokens.md` token — no new hex. Note two dark-specific
inversions: cards sit ABOVE the page (surface-2 over surface), and the accent
"deep" slot maps to the theme's LIGHTER hover (dark UIs brighten on hover).

| Template token | High-contrast-dark value |
|---|---|
| `--ink` | `var(--ink)` (off-white `#FAFAFA`) |
| `--muted` | `var(--ink-muted)` |
| `--bg` | `var(--surface)` (near-black page) |
| `--card` | `var(--surface-2)` (one step up from the page) |
| `--line` | `var(--border-strong)` (visible on dark) |
| `--line-soft` | `var(--border)` |
| `--accent` | `var(--accent)` |
| `--accent-deep` | `var(--accent-hover)` (lighter — dark-mode hover brightens) |
| `--sel-bg` | `var(--accent-soft)` (deep-blue tint `#0F1F3D`) |
| `--radius` | `var(--r-lg)` |
| `--shadow` | `var(--shadow-md)` (strong `rgba(0,0,0,.6)` — subtle over dark) |
| `--font` | `var(--font-sans)` |
| `--mono` | `var(--font-mono)` |

## Component notes

- **Choice cards**: unselected sit on `var(--surface-2)` with a
  `var(--border)` edge; selected = `var(--accent)` border + `var(--accent-soft)`
  (`#0F1F3D`) fill. Check glyph is off-white/`var(--ink-strong)` on the
  saturated accent. Keep contrast legible — the fill is subtle, so the border
  carries the state.
- **Control bars**: `var(--surface-2)` with a `var(--border-strong)` hairline;
  the blur reads well over dark. Primary buttons `var(--accent)` →
  `var(--accent-hover)` (brighter) on hover.
- **Textareas**: `var(--surface-3)` fill, `var(--border-strong)` line, accent
  focus ring.
- **Export panel**: on an already-dark page it must still read as a distinct
  "machine output" surface — use `var(--surface-3)` (a step lighter than the
  page) with an `var(--accent)` top border, not the same near-black as the
  page.
- **Focus states**: keep `:focus-visible` rings bright (`var(--accent-hover)`)
  — focus legibility matters more on dark.

## High-contrast-dark rules that bind codesign pages

From this theme's `anti-patterns.md`:

- Text is **off-white**, never `#FFFFFF` for body — reserve pure white for
  the rare `--ink-strong` emphasis.
- Layer surfaces to separate structure; don't rely on glow or heavy borders.
- Single saturated accent; semantic colors only for status.
- Contrast stays legible: muted text is `--ink-muted`, not fainter.
- Fonts are system/mono stacks; **no webfont `<link>`** (codesign pages are
  self-contained — html-codesign hard rule).
