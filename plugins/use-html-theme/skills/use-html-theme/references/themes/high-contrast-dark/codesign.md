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

## New components (v0.9.0–v0.10.0 set)

Same sourcing rule: `tokens.md` values only. Layering carries structure:
the ctx block steps DOWN from the card, controls step UP on interaction.

- **Context block** (`.ctx`): `var(--surface)` ground (the page
  near-black, inset one step below the `var(--surface-2)` card) with a
  `var(--border)` hairline — depth without heavy strokes. `.ctx-toggle`
  caption `var(--ink-muted)` uppercase. The `.ctx-what` / `.ctx-why`
  lead-in `<b>` renders `var(--fw-semibold)` `var(--ink-strong)` — one of
  the few sanctioned uses of pure white. `.ctx-free` tables:
  `var(--surface-3)` header, `var(--border-strong)` rules, `--fs-small`.
- **Recommendation callout** (`.ctx-rec`): `var(--accent-soft)` deep-blue
  fill (`#0F1F3D` per `tokens.md`) with a 3px `var(--accent)` left
  border; ★ and the choice id in `var(--accent-hover)` (the brighter
  blue — legibility over dark).
- **Rec badge** (`.badge-rec`): `var(--accent-soft)` pill with a
  `var(--accent)` hairline and `var(--accent-hover)` text — the border
  carries the state, the fill stays subtle.
- **Summary rows** (`.summary`): question `var(--fw-semibold)`
  `var(--ink)`; picks (`.s-sel`) `var(--accent-hover)`. Markers
  (`.s-mark-*`): followed = `var(--success)`, went-against and open
  question = `var(--warning)`, skipped = `var(--ink-subtle)` — saturated
  semantic colors read well on near-black; never dim them. Note excerpt
  `var(--ink-muted)`.
- **Section actions** (`.sec-actions`: `.opt-toggle`, `.skip-toggle`,
  `.ask-toggle`): `var(--surface-3)` ground, `var(--border-strong)` line,
  `var(--ink-muted)` text. Active skip lifts to `var(--surface-3)` with
  `var(--ink-strong)` text. Hover brightens the border
  (`var(--accent-hover)`), never darkens.
- **Question field** (`.q-wrap`): label in `var(--warning)` uppercase
  caption; textarea `var(--surface-3)` fill, `var(--border-strong)` line,
  `var(--accent-hover)` focus ring (bright focus matters most on dark).
- **Export toggle** (`.seg` / `.seg-btn`): `var(--surface-3)` ground with
  a `var(--border-strong)` frame; the pressed `.seg-btn` is
  `var(--accent)` with `var(--ink-strong)` text.

## High-contrast-dark rules that bind codesign pages

From this theme's `anti-patterns.md`:

- Text is **off-white**, never `#FFFFFF` for body — reserve pure white for
  the rare `--ink-strong` emphasis.
- Layer surfaces to separate structure; don't rely on glow or heavy borders.
- Single saturated accent; semantic colors only for status.
- Contrast stays legible: muted text is `--ink-muted`, not fainter.
- Fonts are system/mono stacks; **no webfont `<link>`** (codesign pages are
  self-contained — html-codesign hard rule).
