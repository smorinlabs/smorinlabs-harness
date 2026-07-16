# Birchline anti-patterns

Things Birchline deliberately is NOT. Each item is a violation that should be
fixed before delivering.

## Visual

- **Multi-color accents.** Birchline has one accent color (clay). Do not
  introduce a second accent.
- **Gradients.** No linear-gradient or radial-gradient anywhere. Flat fills
  only.
- **Glass / glassmorphism.** No `backdrop-filter: blur()`. No translucent
  overlays.
- **Pure-black shadows.** All shadows use `rgba(20, 20, 19, *)`. Never
  `rgba(0,0,0,*)`.
- **Emoji in headings.** Headings are typographic, not decorative.
- **Dark mode.** Birchline is a light-only theme. The `<meta>` color-scheme
  must be `light`. Do not add a `@media (prefers-color-scheme: dark)` query.

## Typography

- **Bold body.** Never `font-weight: bold`. Body emphasis is `<em>` (renders
  as slate + 500), not `<strong>`.
- **Title case headings.** Sentence case only.
- **Sans-serif H1.** The H1 family is `var(--font-serif)`. Body is sans.
- **Multiple .accent spans.** Exactly one `<span class="accent">` per H1,
  and nowhere else. The italic-clay accent is the system's signature move;
  if everything is accented, nothing is.

## Layout

- **Containers with rounded children but no own background.** The ivory page
  color leaks through at corners. Always set an explicit background on the
  container.
- **Pixel-perfect symmetry everywhere.** Birchline includes one handcrafted
  imperfect element per illustration (e.g., a slightly-tilted clay oval).
  See `illustrations.md`.

## Smoke test

These six checks must pass before delivering any Birchline artifact:

1. `<meta name="color-scheme" content="light">` is in `<head>`.
2. Exactly one `<span class="accent">` in the document, inside the H1.
3. No `font-weight: bold` anywhere.
4. All shadows use `rgba(20, 20, 19, *)`.
5. All headings are sentence case.
6. All colors come from CSS variables, no hex literals scattered inline.
