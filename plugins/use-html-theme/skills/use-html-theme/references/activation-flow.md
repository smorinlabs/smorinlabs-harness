# Activation flow

The skill's state machine for deciding whether to ask, which theme to apply,
and when to persist.

## States

- **NONE** — no theme chosen yet this session, no persistence file
- **SESSION(<name>)** — theme chosen in this conversation
- **PERSISTED(<name>)** — theme chosen and saved to `.claude/use-html-theme.local.md`
- **NOTHEME** — user explicitly chose no theme for the session

## Transitions

On every user request that will produce HTML:

```
1. Parse inline overrides first.
   - If `[theme: <name>]` present → apply <name> for this request only;
     do not change session state.
   - If `[notheme]` present → produce plain HTML for this request only;
     do not change session state.

2. If state is SESSION(<name>) or PERSISTED(<name>):
   - Apply <name> silently. Generate.

3. If state is NOTHEME:
   - Produce plain HTML. Generate.

4. If state is NONE:
   a. Read `.claude/use-html-theme.local.md` if it exists.
      - If theme name parses → state = PERSISTED(<name>), apply, generate.
   b. Otherwise ASK via AskUserQuestion:
      - Birchline / Technical minimal / High-contrast dark / No theme
   c. If picked a theme → state = SESSION(<name>).
      Then ASK once: "Remember this theme for the project?"
      - If yes → write the file, state = PERSISTED(<name>).
   d. If picked "No theme" → state = NOTHEME.
   e. Apply, generate.
```

## Slash commands

- `/theme <name>` → state = SESSION(<name>) (or PERSISTED if file exists and
  user wants persistence updated; default is to leave the file alone)
- `/theme none` → state = NOTHEME (clear any prior SESSION/PERSISTED choice
  in memory; file untouched unless `/theme persist` follows)
- `/theme clear` → state = NONE; delete the persistence file if it exists
  (confirm with the user before deleting)
- `/theme list` → print the catalog, do not change state
- `/theme persist` → write the current session theme to the file; state
  becomes PERSISTED(<name>)

## When the picker should NOT fire

- The user already chose a theme this session (apply silently).
- The persistence file exists with a valid theme (adopt silently).
- The request includes `[notheme]` (one-off, do not ask).
- The user said "no theme this time" or similar natural-language override
  (one-off; do not change session state unless the phrase reads as
  session-level like "stop using a theme").
- The output is not HTML.

## Asking the picker only once per session

If the user picks "No theme", do NOT re-ask on subsequent HTML requests in
the same session. The state is NOTHEME until `/theme clear` or
`/theme <name>`. This prevents nag.

## Token loading discipline

After the chosen theme is known, read ONLY that theme's reference files.
Reading a non-chosen theme's `tokens.md` defeats the progressive disclosure
guarantee and is a bug. The validator does not catch this — be disciplined.
