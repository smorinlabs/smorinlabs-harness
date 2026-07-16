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
markdown, JSON, prose, or non-HTML code, or when the user says `[notheme]` or
asks for no theme · **Arguments:** none — control it in natural language or
with `[theme: <name>]` / `[notheme]` inline flags. See "Controlling the theme".

## Controlling the theme

All in natural language — this is a **pure skill** (no slash commands), so it
behaves identically on Claude Code and Codex:

- **Switch:** "switch to birchline" / "use dark instead", or `[theme: <name>]`
  inline (aliases: `birch`, `minimal`/`tech`, `dark`/`hc-dark`/`hcdark`).
- **One-off:** `[theme: <name>]` or `[notheme]` for a single request.
- **No theme / clear / list / persist:** "no theme this session", "clear the
  theme", "list the themes", "remember this theme for the project".
- **Preview:** "preview the themes" / "show me the options" renders a
  side-by-side catalog page (`assets/preview-template.html`).

## Install

| Mode | When | How |
|---|---|---|
| Plugin (recommended) | Just use it | `/plugin install use-html-theme@smorinlabs-harness` |
| Dev symlink | Tweak/iterate | `git clone https://github.com/smorinlabs/smorinlabs-harness` then `ln -s "$(pwd)/smorinlabs-harness/plugins/use-html-theme/skills/use-html-theme" ~/.claude/skills/use-html-theme` |
| Direct copy | No marketplace access | copy `plugins/use-html-theme/skills/use-html-theme/` into `~/.claude/skills/` |

All three modes install the same **skill** — the plugin is skills-only (no
slash commands), so behavior is identical across install modes and tools.

**Codex:** register the marketplace in `~/.codex/config.toml`. The skill loads
and behaves identically on Codex and Claude Code.
