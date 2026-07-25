# Birchline explainer overlay

Component treatments for `html-explain` pages rendered under Birchline. This
file wins level 1 of the theming cascade: apply these on top of
`assets/explainer-scaffold.html`, sourcing every color from `tokens.md`.
Structure, class names, and any widget script stay untouched — this is paint,
not plumbing.

Birchline's register is **warm editorial** — a long-form essay, not a docs
page. That fits an explainer better than it fits anything else in this
plugin, so lean into it.

## Page frame

- `<meta name="color-scheme" content="light">` and `color-scheme: light` in
  `:root`. Birchline is light-only — no dark query, no `prefers-color-scheme`
  branch.
- Body: `background: var(--ivory)`, ink `var(--slate)`, `font-weight: 430`,
  `font-family: var(--font-sans)`, line-height 1.55.
- **No webfont `<link>`.** Explainer pages are self-contained (skill hard
  rule). Use the token stacks and let them fall back locally — the serif
  stack lands on Georgia, which carries the editorial register perfectly
  well.
- Measure: keep `--measure` at ~68ch. Birchline's body size is 16px, so the
  column lands near 640px — right for sustained reading.

## Headings — the one accent

- **H1 in `var(--font-serif)`, weight 600, size 32–40px**, with the page's
  ONE `<span class="accent">` (serif italic clay) on the key phrase. An
  explainer title is usually a claim or a question, so accent the word the
  claim turns on: *Why retries made it* **worse**.
- **H2 in sans, 24px, weight 500.** Section heads stay sans — the serif is
  reserved for the hero so it keeps its weight.
- **H3 in sans, 18px, weight 500.**
- Never a second `.accent` anywhere on the page. Clay is spent once.

## Lede and meta

- `.lede` — 18px sans, `var(--gray-700)`, line-height 1.55. This carries the
  answer-first conclusion, so give it `margin-bottom: var(--sp-6)` and let it
  breathe.
- `.meta` — Caption role: 12px, uppercase, `.08em` letter-spacing,
  `var(--gray-500)`, weight 500.

## Figures — the heart of an explainer under Birchline

- `figure` sits on `var(--white)` inside a `var(--r-md)` radius with
  `--shadow-sm`, padded `var(--sp-5)`. The card lifts the diagram off the
  ivory page the way a plate sits in a printed essay.
- Inline SVG follows `illustrations.md`'s construction principles: **brand
  tokens only, no gradients, no opacity tricks, hairline 1.5px slate
  strokes, `rx` 4–10 on outer shapes**, and soft `feDropShadow` with
  `flood-color="#141413"` at .06–.10 — never pure black.
- **Differentiate by hue, not intensity.** For explanatory diagrams the
  working set is `--clay` (the subject under discussion), `--info`
  slate-blue (a contrasting element), `--gray-500` (recessive context), and
  `--success` sage / `--danger` brick where the semantics are genuinely
  good/bad. Do not tint one hue lighter to mean "less" — that reads as
  disabled.
- **Clay marks the thing being explained**, and only that. In a figure with
  five boxes, the one the paragraph is about is clay; the rest are
  gray-500. This is the theme's native form of signaling (canon L1.2), and
  it is why one-pop-out-per-view (E5) matters here: two clay elements in one
  figure cancel.
- `figcaption` — 14px sans, `var(--gray-700)`, with a `2px solid
  var(--oat)` left rule and `padding-left: var(--sp-3)`. Oat, not gray-300 —
  the caption is warm furniture, not a divider.

## Callouts

`.note` renders as an oat card, not a colored bar:

- `background: var(--oat)`, no left border, `border-radius: var(--r-sm)`,
  padding `var(--sp-4) var(--sp-5)`.
- Where the callout is semantic, keep the oat card and put a 12–16% tint of
  the semantic color behind it instead — `--warning` amber for a caveat,
  `--danger` brick for a genuine trap, `--info` for an aside. Full-strength
  semantic color goes on the *text* or a small leading label, never as a
  background.

## Code and real artifacts

- `pre` — `background: var(--gray-100)`, `1px solid var(--gray-300)`,
  `border-radius: var(--r-sm)`, `var(--font-mono)` at 14px.
- Diff highlighting uses semantic tints at 12–16%: `--success` sage for
  additions, `--danger` brick for deletions. Not GitHub green/red — they
  clash with the warm neutrals badly.
- Inline `p code` — `var(--gray-100)` chip, `var(--r-xs)`.

## Tables

- No outer border and no zebra striping. A `1px solid var(--gray-300)` rule
  under each row, and a slightly heavier one under the header.
- `th` — 14px, weight 500, `var(--gray-500)`, uppercase with `.08em`
  letter-spacing (the Caption role). This is the editorial move: the header
  recedes and the data carries.
- Numeric columns right-aligned, `var(--font-mono)`, `font-variant-numeric:
  tabular-nums`.

## Build-up sequences

- `.seq-step` — `var(--white)` card, `--shadow-sm`, `var(--r-md)`, padded
  `var(--sp-5)`.
- The step number in serif italic clay (the section-ID treatment codesign
  uses), the step name in sans 14px `var(--gray-700)`.
- **At most one purposeful tilt across the whole sequence**, per
  `illustrations.md` rule 5, and only to mark a "before / the wrong way"
  panel. Never tilt more than one.

## Details on demand

- `details` — hairline `1px solid var(--gray-300)`, `var(--r-sm)`, no fill;
  it should read as a quiet seam in the page, not another card.
- `summary` — sans 16px weight 500, `var(--slate)`; the marker in
  `var(--clay)`.

## Widgets

- `.widget` — `var(--gray-100)` surface, `var(--r-md)`, `--shadow-sm`,
  padded `var(--sp-5)`. Sunk rather than lifted: a control panel is
  furniture, a figure is a plate.
- Range track `var(--gray-300)`, thumb `var(--clay)`, focus ring
  `2px var(--clay)` at `outline-offset: 3px`.
- Transitions use `var(--ease-out)`; keep them under 200ms, and honor
  `prefers-reduced-motion`.
- `.widget-out` — `var(--font-mono)`, `tabular-nums`, `var(--slate)`.

## What not to do

- **Don't put clay on more than one thing per view.** It is the theme's
  emphasis channel and the page's signaling channel at once; spending it
  twice spends it zero times.
- **Don't add the Google Fonts link.** The self-contained rule outranks
  having the exact families.
- **Don't reach for gradients, glows, or opacity ramps** to show magnitude.
  Birchline differentiates by hue; magnitude is position or length
  (`visual-encoding.md`, E2).
- **Don't card everything.** Ivory page, white plates for figures, oat for
  callouts, gray-100 for code and widgets. If every block is a white card,
  the figures stop reading as figures.
