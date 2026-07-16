# Override grammar

Three overlapping mechanisms to override the session theme choice. All are
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

## Slash commands (change SESSION state, may change PERSISTED state)

| Command | Effect |
|---------|--------|
| `/theme <name>` | Set session theme to `<name>` |
| `/theme none` | Set session state to NOTHEME (skill stops asking and applying) |
| `/theme clear` | Set session state to NONE; offer to delete the persistence file |
| `/theme list` | Print the catalog |
| `/theme persist` | Write the current session choice to `.claude/use-html-theme.local.md` |

## Natural language (change SESSION state)

Treat these phrases as session-level switches:

- "switch to <theme>" / "change to <theme>" / "use <theme> instead"
- "switch themes to <theme>" / "let's use <theme>"
- "stop using <theme>" / "no more <theme>"
- "clear the theme" / "forget the theme" / "no theme any more"

Treat these as one-off overrides (do NOT change session state):

- "no theme this time" / "plain html this time" / "skip the theme"
- "just for this page, use <theme>" / "this one in <theme>"

If the phrasing is ambiguous between session and one-off, prefer one-off and
ask "Make this the session default too?" only if the user repeats the
override on the next request.

## Precedence

When multiple mechanisms appear in the same request, apply in this order
(highest first):

1. Inline flag (`[theme: x]`, `[notheme]`)
2. Slash command (`/theme x`)
3. Natural-language override
4. Session state (SESSION/PERSISTED/NOTHEME)
5. Persistence file (`.claude/use-html-theme.local.md`)
6. Ask the picker (no state, no file, no overrides)
