---
description: Switch, clear, list, or persist the HTML theme for this session.
argument-hint: "[birchline | technical-minimal | high-contrast-dark | none | clear | list | persist]"
---

Manage the `use-html-theme` skill's session theme.

## Argument parsing

Parse `$ARGUMENTS` as the first whitespace-separated token. Match
case-insensitively. Recognize aliases per
`skills/use-html-theme/references/override-grammar.md`.

| Arg | Action |
|-----|--------|
| `birchline` / `birch` | Set session theme to `birchline` |
| `technical-minimal` / `minimal` / `tech-minimal` / `tech` | Set session theme to `technical-minimal` |
| `high-contrast-dark` / `dark` / `hc-dark` / `hcdark` | Set session theme to `high-contrast-dark` |
| `none` | Set session state to NOTHEME (stop applying any theme) |
| `clear` | Clear session state AND offer to delete `.claude/use-html-theme.local.md` |
| `list` | Print the catalog (do not change state) |
| `persist` | Write current session theme to `.claude/use-html-theme.local.md` |
| _(empty)_ | Print current state + usage hint |

## Behavior

1. If the argument resolves to a theme name: silently update the session
   theme. Acknowledge in one line: "Theme set to `<name>` for this session.
   Run `/theme persist` to save it for the project."

2. If the argument is `none`: set session state to NOTHEME and acknowledge:
   "Theme cleared for this session. The skill will not apply a theme until
   you say `/theme <name>` or pick from the picker."

3. If the argument is `clear`: ask the user to confirm before deleting the
   persistence file. Use AskUserQuestion with options "Delete file" /
   "Keep file". On confirm, delete `.claude/use-html-theme.local.md` if it
   exists. Always clear session state.

4. If the argument is `list`: print the v1 catalog as a numbered list:

   ```
   1. birchline — warm editorial, ivory paper / coral accent / serif hero
   2. technical-minimal — neutral grays, blue accent, system sans, docs-site
   3. high-contrast-dark — near-black surface, off-white text, single accent
   ```

5. If the argument is `persist`: read the current session theme from
   conversation memory. If a theme is set, follow
   `skills/use-html-theme/references/persistence.md` to write the file.
   If no theme is currently set, say "No session theme to persist — pick one
   first."

6. If empty: print "Current session theme: `<name | none | unset>`. Usage:
   `/theme <name|none|clear|list|persist>`."

## Argument

$ARGUMENTS
