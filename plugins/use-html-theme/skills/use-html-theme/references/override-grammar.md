# Override grammar

Two overlapping mechanisms to override the session theme choice. Both are
supported simultaneously.

## Inline flags (one-off, do NOT change session state)

Recognize at the start, end, or anywhere in the request:

| Flag | Effect |
|------|--------|
| `[theme: birchline]` | Use Birchline for this request only |
| `[theme: technical-minimal]` | Use Technical minimal for this request only |
| `[theme: high-contrast-dark]` | Use High-contrast dark for this request only |
| `[notheme]` | Generate plain HTML for this request only |

### Aliases (case-insensitive)

| Alias | Resolves to |
|-------|-------------|
| `birchline`, `birch` | `birchline` |
| `technical-minimal`, `minimal`, `tech-minimal`, `tech` | `technical-minimal` |
| `high-contrast-dark`, `dark`, `hc-dark`, `hcdark` | `high-contrast-dark` |

Example: `[theme: dark]` and `[theme: high-contrast-dark]` are equivalent.

## Natural language (change SESSION state)

Treat these phrases as session-level switches:

- "switch to <theme>" / "change to <theme>" / "use <theme> instead"
- "switch themes to <theme>" / "let's use <theme>"
- "stop using <theme>" / "no more <theme>"
- "clear the theme" / "forget the theme" / "no theme any more"

Treat these as one-off overrides (do NOT change session state):

- "no theme this time" / "plain html this time" / "skip the theme"
- "just for this page, use <theme>" / "this one in <theme>"

Treat these as catalog / persistence actions (no HTML generated):

- "list the themes" / "what themes are there?" / "show me the options" → print
  the catalog, or render the preview per SKILL.md's "Previewing the catalog".
- "remember this theme" / "save it for the project" / "make it the default" →
  write `.claude/use-html-theme.local.md` (see `persistence.md`).

If the phrasing is ambiguous between session and one-off, prefer one-off and
ask "Make this the session default too?" only if the user repeats the
override on the next request.

## Precedence

When multiple mechanisms appear in the same request, apply in this order
(highest first):

1. Inline flag (`[theme: x]`, `[notheme]`)
2. Natural-language override
3. Session state (SESSION/PERSISTED/NOTHEME)
4. Persistence file (`.claude/use-html-theme.local.md`)
5. Ask the picker (no state, no file, no overrides)
