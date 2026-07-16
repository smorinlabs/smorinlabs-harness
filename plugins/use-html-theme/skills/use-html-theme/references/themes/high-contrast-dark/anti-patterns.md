# High-contrast-dark anti-patterns

## Visual

- **Light-mode color-scheme.** Must be `dark`. Both the `<meta>` tag and
  `color-scheme:` in `:root` must say `dark`. Without this, iOS Safari may
  attempt its own dark-mode transformation on top of the existing dark
  palette and produce washed-out grays.
- **Bright white text on near-black.** Use `--ink` (`#FAFAFA`) for body,
  reserve `--ink-strong` (`#FFFFFF`) for headings only. Pure white on pure
  black causes halation.
- **Multiple accent colors.** One accent (blue). Semantic colors (success /
  warning / danger) are not accents; they're status signals.
- **Gradients on surfaces.** Flat surfaces only. Subtle 1px borders separate
  layers, not gradients.

## Typography

- **Serif anywhere.** Sans-serif everything. This theme does not have a
  serif token.
- **Bold body weight.** Use `--fw-medium` (500) for emphasis.
- **Tight letter-spacing on body.** Reserve letter-spacing for captions and
  labels only.

## Layout

- **Padded floating cards with heavy shadows.** Shadows are subtle on dark.
  Layer separation comes from `--surface` / `--surface-2` / `--surface-3`
  contrast plus 1px borders, not glow effects.

## Smoke test

1. `<meta name="color-scheme" content="dark">` is in `<head>`.
2. `color-scheme: dark;` in `:root`.
3. All colors from CSS variables.
4. All headings sans-serif.
5. No `font-weight: bold`.
6. Body text uses `--ink`, not `--ink-strong`.
