# Tool mapping for OpenAI Codex CLI

The `project-harness` skills use Claude Code tool names in their
prose. When running under Codex CLI, substitute these equivalents:

| Claude Code tool | Codex equivalent |
|---|---|
| `Skill` | Codex's native `skill` tool (auto-discovered from `~/.agents/skills/`) |
| `TodoWrite` | Codex's native todo / task list tool (`todowrite` in some versions) |
| `Task` (subagent dispatch) | Codex `@mention` syntax for sub-agent invocation |
| `Read` / `Write` / `Edit` | Codex's native file tools |
| `Bash` | Codex's native shell tool |
| `AskUserQuestion` | Inline question in chat — Codex doesn't have a structured-question tool |
| `EnterPlanMode` | Codex doesn't have plan mode — describe your plan in chat and ask for approval before executing |

## Skill-specific notes

- `project-next`, `project-refine`, `project-audit` describe
  dispatching subagents in parallel. In Codex, use multiple
  `@mention` calls in one turn — Codex executes them concurrently.
- `project-audit` writes one commit per accepted finding. Codex's
  `Bash` shell tool handles `git add` + `git commit` the same way
  Claude Code does.
- The hooks/SessionStart context injection is Claude Code / Cursor
  specific. Under Codex, `using-project-harness` discovery relies on
  the `~/.agents/skills/project-harness` symlink and the skill's own
  `description` and `when_to_use` frontmatter.
