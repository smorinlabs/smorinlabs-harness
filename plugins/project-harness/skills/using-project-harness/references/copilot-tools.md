# Tool mapping for GitHub Copilot CLI

The `project-harness` skills use Claude Code tool names. When running
under Copilot CLI, substitute these equivalents:

| Claude Code tool | Copilot CLI equivalent |
|---|---|
| `Skill` | Copilot's native `skill` tool — works the same way |
| `TodoWrite` | Copilot's task / todo list tool |
| `Task` (subagent dispatch) | Copilot's sub-agent invocation (consult Copilot docs for current syntax) |
| `Read` / `Write` / `Edit` | Copilot's native file tools |
| `Bash` | Copilot's native shell tool |
| `AskUserQuestion` | Inline chat prompt |
| `EnterPlanMode` | Inline plan-then-confirm pattern |

## Skill-specific notes

- Copilot CLI auto-discovers skills from installed plugins, so
  `using-project-harness` and the four workflow skills appear
  automatically once the plugin is installed.
- The SessionStart hook in `hooks/session-start` emits the
  `additionalContext` shape that Copilot CLI v1.0.11+ consumes — no
  Copilot-specific hooks file needed.
- Subagent-style parallel work (used by `project-refine` and
  `project-audit`) maps to whatever concurrent-task primitive your
  Copilot version supports. If unavailable, run the same checks
  sequentially — output is identical, just slower.
