# Persistence

The skill remembers the chosen theme at two scopes: **session** (always) and
**project** (opt-in, via a file).

## Session memory (default)

The skill tracks the chosen theme in conversation context. No files written.
The choice is forgotten when the session ends. This is the default scope —
do not write the file unless the user opts in.

## Project persistence (opt-in)

After picking a theme via the picker, ask **once**:

> Remember this theme for the project?

If yes, write `.claude/use-html-theme.local.md` in the working directory:

```markdown
---
theme: birchline
---

Selected by user on YYYY-MM-DD via the use-html-theme plugin. Override by
asking to switch themes, or with `[theme: <name>]` / `[notheme]` inline.
Clear by asking to clear the theme.
```

The file is single-key: only `theme:` is read. Other frontmatter keys are
ignored. The body is informational — humans may edit it freely; the skill
ignores everything outside the frontmatter.

## Reading the file

On any HTML request in a fresh session, before asking the picker:

1. Look for `.claude/use-html-theme.local.md` in the working directory.
2. If present, parse the frontmatter for `theme:`.
3. If the value is one of `birchline`, `technical-minimal`,
   `high-contrast-dark`, adopt as session choice; do not ask.
4. If the value is anything else (typo, removed theme), warn the user and
   ask the picker.

## Writing the file

Use this template exactly (replace `<theme>` and date):

```markdown
---
theme: <theme>
---

Selected by user on <YYYY-MM-DD> via the use-html-theme plugin. Override by
asking to switch themes, or with `[theme: <name>]` / `[notheme]` inline.
Clear by asking to clear the theme.
```

Always create the `.claude/` directory if missing (`mkdir -p .claude`).

## Clearing the file

Clearing the theme (the user asks to "clear" or "forget" it) should:

1. Confirm with the user (one-line: "Delete .claude/use-html-theme.local.md?").
2. If yes, remove the file.
3. Set session state to NONE so the next HTML request asks the picker.

Never delete the file silently.

## Multiple projects

Each project's persistence file is scoped to that project's working directory.
Cross-project isolation is automatic. There is no global user-level
persistence in v1.
