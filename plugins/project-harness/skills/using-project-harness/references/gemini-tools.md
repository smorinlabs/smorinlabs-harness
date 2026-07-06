# Tool mapping for Gemini CLI

The `project-harness` skills use Claude Code tool names. When running
under Gemini CLI, substitute these equivalents:

| Claude Code tool | Gemini CLI equivalent |
|---|---|
| `Skill` | Gemini's `activate_skill` tool — Gemini loads skill metadata at session start and activates the full content on demand |
| `TodoWrite` | Gemini's todo / task list tool |
| `Task` (subagent dispatch) | Gemini's parallel-tool-call mechanism — issue multiple tool calls in one response |
| `Read` / `Write` / `Edit` | Gemini's native file tools |
| `Bash` | Gemini's shell tool |
| `AskUserQuestion` | Inline chat prompt |
| `EnterPlanMode` | Plan-then-confirm in chat |

## Skill-specific notes

- The Gemini extension declares `contextFileName: "GEMINI.md"` and
  `GEMINI.md` `@-imports` `using-project-harness/SKILL.md` and this
  file. So both are loaded into context at session start without the
  user invoking anything.
- For the four workflow skills (`project-next`, `project-add`,
  `project-refine`, `project-audit`), the user invokes
  `activate_skill` once Gemini surfaces them as available.
- The SessionStart hook script in `hooks/session-start` falls through
  to the `additionalContext` (top-level) JSON shape when neither
  `CURSOR_PLUGIN_ROOT` nor `CLAUDE_PLUGIN_ROOT` is set, which matches
  what Gemini-style hosts consume. No Gemini-specific hooks file is
  needed.
- Skills like `project-audit` and `project-refine` describe parallel
  subagent dispatch. In Gemini, emit multiple tool calls in a single
  response — the runtime parallelizes them.
