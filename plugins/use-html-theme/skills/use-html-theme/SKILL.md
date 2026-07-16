---
name: use-html-theme
description: |
  Whenever the user asks Claude to generate or restyle HTML — a page, artifact,
  mockup, dashboard, doc, status page, landing page, release-notes page, HTML
  email, or styled snippet — offer a small catalog of visual themes and apply
  the chosen one to all subsequent HTML in the session. v1 catalog: birchline
  (warm editorial), technical-minimal (docs-site neutral), high-contrast-dark
  (dashboard/terminal). Each theme is a self-contained folder of tokens,
  components, anti-patterns, and a worked example; only the chosen theme's
  files are read (progressive disclosure). The choice persists in session
  memory and can be saved per-project to `.claude/use-html-theme.local.md`.
  Overrides via natural language, `[theme: <name>]` / `[notheme]` inline flags,
  and the `/theme` and `/theme-preview` slash commands. Do NOT activate for
  markdown, JSON, prose, or non-HTML code, or when the user said `[notheme]`
  or `/theme none`.
allowed-tools: Read Write Edit Glob AskUserQuestion
---

# When this skill applies

Activate whenever the next response will produce HTML. This is the load-bearing
trigger — the catalog ask happens on the HTML request, not on any earlier
"can we talk about a page" conversation.

✓ "Make me a status page in HTML"
✓ "Build an HTML landing page for my app"
✓ "Convert this changelog into a single-file HTML page"
✗ "Explain how flexbox works" (no HTML output)
✗ "Write me a README" (markdown, not HTML)

# Process

Follow these steps in order. The state machine lives in
`references/activation-flow.md`; read it once on first activation per session.

1. **Detect HTML-generation intent.** The user asked for HTML output.

2. **Check session state.** If a theme was already chosen in this conversation,
   apply it silently. Skip to step 6.

3. **Check `.claude/use-html-theme.local.md`.** If the file exists in the cwd
   and contains a valid theme name under the `theme:` frontmatter key, adopt
   it as the session choice and skip to step 6.

4. **Ask the user.** Use `AskUserQuestion` if available; otherwise print a
   numbered list in chat. Options:
   - Birchline — warm editorial, ivory paper / coral accent / serif hero
   - Technical minimal — neutral grays, blue accent, system sans, docs-site
   - High-contrast dark — near-black surface, off-white text, single accent
   - No theme — plain HTML for this session

5. **Record choice in session memory.** If a theme was picked, ask once:
   "Remember this theme for the project?" If yes, write
   `.claude/use-html-theme.local.md` (see `references/persistence.md` for
   the file format).

6. **Load only the chosen theme's reference files** — read
   `references/themes/<name>/tokens.md` always; read `components.md` if the
   task needs interactive or semantic elements; read `illustrations.md` only
   if an illustration would replace a paragraph of prose (Birchline only).
   Files from non-chosen themes are never read.

7. **Generate** the HTML using those tokens and components.

# Overrides

Three mechanisms — see `references/override-grammar.md` for full grammar and
precedence. Quick reference:

| Mechanism | Example | Scope |
|-----------|---------|-------|
| Inline flag | `[theme: dark]`, `[notheme]` | This request only |
| Slash command | `/theme technical-minimal`, `/theme none` | Session |
| Natural language | "switch to dark", "no theme this time" | Session or request |

Precedence (highest first): inline flag → slash command → natural-language
override → session memory → persistence file → ask. (Full ordering in
`references/override-grammar.md`.)

# Hard rules (cross-theme)

- **Tokens only.** Every color, font, spacing, radius, and shadow comes from
  the chosen theme's `tokens.md`. Never invent values.
- **Color-scheme declared.** Light themes emit
  `<meta name="color-scheme" content="light">` in `<head>` AND
  `color-scheme: light;` in `:root`. The dark theme emits the `dark`
  equivalents. Without these, iOS Safari auto-darkens light pages.
- **Never mix tokens from two themes.** If a request seems to want both,
  ask which theme to use.
- **Vocabulary not structure.** This skill does not impose page rhythm,
  required sections, or document format. The user composes; the skill
  supplies the tokens.
- **Vanilla HTML/CSS only.** Single self-contained `.html` with embedded
  `<style>`. No build step, no React, no Tailwind, no external CSS files.
  Google Fonts allowed.
- **Each theme has its own anti-patterns.** Read the chosen theme's
  `anti-patterns.md` before finalizing.

# Quick smoke test

Before delivering any themed artifact, ask:

1. Is the right color-scheme meta tag in `<head>`?
2. Are all colors sourced from CSS variables (not hex literals inline)?
3. Did I check the chosen theme's `anti-patterns.md`?

# Gotchas

- **Don't carry the theme across sessions silently** unless
  `.claude/use-html-theme.local.md` says so. Session memory is the default.
- **Don't apply a theme to non-HTML output.** Markdown, JSON, prose — leave
  alone.
- **Don't extend the catalog ad-hoc.** Themes are bundled; adding a fourth
  means a new folder under `references/themes/` and a new entry in the
  picker. Don't invent a theme inline.
