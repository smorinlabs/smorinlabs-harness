# Technical-minimal anti-patterns

## Visual

- **Warm-tinted shadows.** Shadows are neutral black-alpha
  (`rgba(0, 0, 0, *)` at low alpha). This is one of the few themes where pure
  black shadows are correct, because the surface is pure white.
- **Multiple accent colors.** One accent (blue). Do not introduce a second.
- **Decorative gradients.** No. Flat fills only.
- **Heavy borders.** Always 1px. Heavy borders read as defensive UI.

## Typography

- **Serif headings.** Sans-serif for everything. Technical-minimal does not
  have a serif token.
- **Bold body.** Use `--fw-medium` (500) for emphasis; reserve `--fw-semibold`
  (600) for headings.
- **Tight body line-height.** Body is `--lh-normal` (1.5). Tighter reads as
  marketing copy, not docs.

## Layout

- **Generous whitespace.** Spacing is tighter than Birchline by design — this
  is engineering-density. Do not import Birchline's spacing rhythm.

## Smoke test

1. `<meta name="color-scheme" content="light">` is in `<head>`.
2. All colors come from CSS variables.
3. All headings sans-serif.
4. No `font-weight: bold`.
5. All borders 1px.
