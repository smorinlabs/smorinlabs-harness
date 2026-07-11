---
name: project-next
description: Reads PROJECTS.md and projects/ to surface a composite menu of in-progress projects, the next 2-3 lowest-ID unstarted projects, and the 2-3 most recently committed project files, then asks the user where to focus and points at the appropriate sibling skill or framework. Read-only — never edits PROJECTS.md or projects/.
when_to_use: When the user asks "what's next?", "what should I work on?", or returns to a repo after time away.
allowed-tools: Read Bash
---

# project-next

**Core principle:** orient first, decide together. The skill brings
the trunk's current state into the conversation as a small,
scannable menu so the user can choose where to focus, rather than
dictating a single answer.

## When to use

- *"What's next?"* / *"What should I work on?"*
- *"Anything in progress I forgot about?"*
- Start of a session, or after time away from the repo.
- Before deciding whether to capture a new idea, refine an existing
  project, or run an audit — `project-next` makes the choice
  obvious.

## What it does

1. **Read `PROJECTS.md`** in full. Parse the trunk index. Note
   which projects are `[~]` (in progress), which are `[ ]`
   (scoped, not started), and which are `[?]` (idea).
2. **Read per-project files** for projects that are `[~]` (to find
   the next unchecked task and any `**Depends on:**` lines), for
   `[ ]` projects (to surface their dependencies in the menu), and
   for any project the user has mentioned recently in this session.
   Do not read every project file — `[?]` ideas and `[x]` /
   `[-]` / `[>]` projects are not part of the menu and don't need
   their bodies read.
3. **Read recency signals via git.** Use
   `git log -1 --format=%ct -- projects/<filename>` per project
   file. Commit time is the canonical recency signal — robust
   across worktrees, clones, and freshly cloned machines (where
   filesystem mtimes are all equal). If a file is untracked
   (rare but possible for a just-created idea), treat it as
   "now". Sort descending.
4. **Parse dependencies.** For each `[~]` and `[ ]` project, look
   for `**Depends on:**` lines in the body. If any named dependency
   is not `[x]` in the trunk, mark the project as
   *blocked on Pnn*. Multiple dependencies → list the first two
   plus "+N more".
5. **Compose the composite menu** — three short lists, each with
   ≤3 entries:
   - **In progress** — `[~]` projects, with the next unchecked task
     ID and any *blocked on* annotation.
   - **Next up (lowest IDs)** — the lowest 2-3 unstarted (`[ ]`)
     IDs, with *blocked on* annotation if dependencies aren't met.
   - **Recently touched** — the 2-3 most recently committed project
     files, regardless of status.

   If the trunk has fewer than three projects total, just list
   what exists with one sentence ("Only one project here: P21
   (in progress, next task TS02). Where would you like to
   focus?"). The three-list format is for when there is genuine
   choice.
6. **Ask one focusing question.** Format:
   ```
   • In progress: P21 (next: TS02), P19 (blocked on P39)
   • Next up (lowest IDs): P22, P25 (blocked on P19, P22), P26
   • Recently touched: P33 (idea), P21, P40

   Where would you like to focus?
   ```
7. **Hand off in text.** Based on the user's answer, point at the
   right next skill or framework — never invoke it. Examples:
   - *"Use `project-add` to capture that."*
   - *"Use `project-refine P33` to scope it."*
   - *"P21-TS02 is ready — hand to Superpowers
     (`superpowers:executing-plans`) or just start editing."*
8. **Stop.** Do not start the next thing yourself.

If the trunk is empty (no projects), say so and point at
`project-add`.

## What it deliberately does not do

- Does not capture ideas (that's `project-add`).
- Does not refine, scope, or decompose (that's `project-refine`).
- Does not execute tasks (Superpowers / Claude Code / your editor).
- Does not flip task checkboxes during execution (that's whoever
  executes the task, per companion proposal §8).
- Does not edit `PROJECTS.md` except to update a *Last reviewed*
  marker if the trunk has one. (The default trunk template does not
  include such a marker.)
- Does not block on dependencies. If the user wants to focus on
  P21b while P21 is `[~]`, mention the dependency in one line and
  let the user decide.

## Red Flags

| Thought | Reality |
|---------|---------|
| "I should also start scoping while I'm here" | No. That's `project-refine`'s job. End this conversation. |
| "The user mentioned an idea, I'll capture it inline" | No. Point at `project-add` and exit. |
| "I'll just pick the lowest ID and start working" | The user picks. The skill surfaces options; it doesn't make decisions. |
| "Reading every project file gives the user more context" | Read only `[~]` projects + recently-mentioned ones. The trunk is the source for status. |
| "The trunk is empty, let me design the first project" | No. Point at `project-add` and stop. |

## Quick reference: status glyphs

| Glyph | Meaning                | Reach for…                    |
|-------|------------------------|-------------------------------|
| `[?]` | Idea                   | `project-refine` to scope     |
| `[ ]` | Scoped, not started    | start work; flip to `[~]`     |
| `[~]` | In progress            | continue; check next task     |
| `[x]` | Completed              | leave alone                   |
| `[-]` | Decided not to do      | leave alone                   |
| `[>]` | Proceeded to successor | follow the redirect           |

## See also

- `project-add` — when the user surfaces a new idea during the
  conversation.
- `project-refine` — when the user wants to scope or decompose an
  existing project.
- `project-audit` — when the user wonders whether the trunk's state
  is consistent with the per-project files.
- Superpowers (`superpowers:executing-plans`) — when the user is
  ready to execute a task.
