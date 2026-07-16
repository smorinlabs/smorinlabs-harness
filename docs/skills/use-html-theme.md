# use-html-theme

On any HTML-generation request, offers a small catalog of visual themes and
applies the chosen one to all subsequent HTML in the session. Three
**fully-isolated** themes — **Birchline** (warm editorial: ivory paper, single
coral/clay accent, serif hero, sentence-case), **Technical-minimal** (docs-site
neutral grays, blue accent, system sans, 1px borders), and
**High-contrast-dark** (near-black surface, off-white text, saturated accent) —
each a self-contained folder of design tokens, component snippets,
anti-patterns, and a worked `example.html`. Progressive disclosure means only
the chosen theme's files are ever read; an unused theme costs zero context. It
is a *vocabulary applier*, not a structure imposer — it supplies tokens and
components without dictating page rhythm or document format. The choice lives in
session memory and can be persisted per-project in
`.claude/use-html-theme.local.md`.

**Triggers on:** any request that will produce HTML — a page, artifact, mockup,
dashboard, doc, status page, landing page, release-notes page, HTML email, or
styled snippet, and restyling an existing HTML artifact. Does **not** fire on
markdown, JSON, prose, or non-HTML code, or when the user says `[notheme]` /
`/theme none` · **Arguments:** none for the skill itself; overrides via
`[theme: <name>]` / `[notheme]` inline flags, natural language, and the two
slash commands below.

## Commands

- `/theme [birchline | technical-minimal | high-contrast-dark | none | clear | list | persist]`
  — switch, clear, list, or persist the session theme (aliases: `birch`,
  `minimal`/`tech`, `dark`/`hc-dark`/`hcdark`).
- `/theme-preview` — render all three themes side-by-side as preview cards.

## Install

| Mode | When | How |
|---|---|---|
| Plugin (recommended) | Just use it | `/plugin install use-html-theme@smorinlabs-harness` |
| Dev symlink | Tweak/iterate | `git clone https://github.com/smorinlabs/smorinlabs-harness` then `ln -s "$(pwd)/smorinlabs-harness/plugins/use-html-theme/skills/use-html-theme" ~/.claude/skills/use-html-theme` |
| Direct copy | No marketplace access | copy `plugins/use-html-theme/skills/use-html-theme/` into `~/.claude/skills/` |

The dev-symlink and direct-copy modes install the **skill** (the theming
behavior); the `/theme` and `/theme-preview` slash commands ship with the full
**plugin**, so use the plugin install to get them too.

**Codex:** register the marketplace in `~/.codex/config.toml`. Codex loads the
skill; the slash commands are Claude Code-specific.
