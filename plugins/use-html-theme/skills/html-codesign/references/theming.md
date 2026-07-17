# Theming — the cascade

This skill owns structure, behavior, and exports. The way the page LOOKS
comes from a three-level cascade, resolved top-down at render time:

```
1. Theme overlay      themes/<name>/codesign.md in use-html-theme
                      (rich, hand-tuned artifact components for that theme)
2. Theme tokens       themes/<name>/tokens.md in use-html-theme
                      (derive generic components from the theme's variables)
3. Neutral built-in   the token block shipped inside codesign-template.html
```

A theme with an overlay (Birchline) keeps every ounce of its personality —
warm choice cards, its accent rhythm, its shadows. A theme without one still
works: the template's components are shaped generically and painted with that
theme's tokens. No theme at all → the neutral built-in. Nothing is watered
down; richness is opt-in per theme.

## Resolving the active theme

Same sources use-html-theme itself uses, in order:

1. **Session state** — a theme already chosen in this conversation (or the
   use-html-theme picker just ran for this request; honor its outcome,
   including NOTHEME → neutral).
2. **Persistence file** — `.claude/use-html-theme.local.md` frontmatter
   `theme:` key in the working directory.
3. **Neither** → neutral built-in. Do NOT force the theme picker just for a
   codesign page; if use-html-theme is installed it will have asked already.

Then check the sibling skill's theme folder for an overlay — from this
skill's directory that is
`../use-html-theme/references/themes/<name>/codesign.md` (in the plugin
tree: `skills/use-html-theme/references/themes/<name>/codesign.md`). If it
exists, apply its component treatments; otherwise restyle the template's
components using only that theme's `tokens.md` variables.

## Hard rules

- **Never mix themes.** One theme per page, exactly as use-html-theme's own
  rule states.
- **Match the color-scheme meta to the theme.** birchline and
  technical-minimal are light (`<meta name="color-scheme" content="light">`
  + `color-scheme: light` in `:root`); high-contrast-dark is dark. The
  neutral built-in is light.
- **Honor the theme's anti-patterns.** When rendering under a theme, its
  `anti-patterns.md` binds this page too (e.g. Birchline: exactly one
  `.accent` span, in the H1; no pure-black shadows; sentence case).
- **Keep the engine intact.** Theming changes tokens and component CSS —
  never the spec tag, `data-id`s, or the engine script.
- **No remote font links.** Codesign pages are self-contained ("no external
  requests" is a hard rule) and this wins over any theme guidance to load
  webfonts: use the theme's font stacks and let local fallbacks carry them
  (Birchline's serif falls back to Georgia). Never add a `<link>` to a font
  CDN.

## The neutral built-in

Deliberately quiet so themes provide the personality: system font stack,
near-black ink on warm-white, hairline borders, a single restrained
steel-blue accent, monospace IDs. It should read as "considered default",
not as a fourth theme — if the neutral starts growing personality, that
personality belongs in a theme overlay instead.
