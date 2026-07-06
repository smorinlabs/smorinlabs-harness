---
name: manual-test-guide
description: Use when the user asks "how to manually test", "what are manual testing steps", "what commands to test", "how to test the latest features", "what to test", "what are the testing commands", or any request for manual testing instructions and validation steps for a project.
---

# Manual test guide

Generate a practical, copy-pasteable manual testing guide for the project.

## Arguments (from the user's request)

- `--recent` — focus only on features changed in recent commits
- `--full` — comprehensive test guide for the entire project
- a specific feature or area name to focus on

## 1. Gather context

- Project type: `ls pyproject.toml Cargo.toml package.json go.mod 2>/dev/null`
- Task runner: `ls justfile Makefile 2>/dev/null`
- Recent changes: `git log --oneline -5`
- Examples dir: `ls -d examples/ 2>/dev/null`
- CLI entry points: `grep -A2 '\[project.scripts\]' pyproject.toml` or `grep '"bin"' package.json`

## 2. Discover entry points

Scan for all runnable things:
- **CLI commands**: `[project.scripts]` (pyproject), `bin` (package.json), `[[bin]]` (Cargo.toml)
- **Task runner recipes**: parse justfile/Makefile for user-facing targets
- **Example scripts**: files in `examples/`
- **Demo commands**: documented demo commands in README.md

## 3. Check recent changes

If `--recent` or no specific scope: `git diff HEAD~5 --name-only` to find recently changed
files; map them to features/components; prioritize testing those areas.

## 4. Generate the test guide

```markdown
## Manual Testing Guide

### Prerequisites
- [ ] `<install command>` — Install dependencies
- [ ] `<build command>` — Build the project

### Smoke Tests (run these first)
1. `<command>` — Expected: <what should happen>

### Feature Tests
#### <Feature Area>
1. `<command>` — Expected: <behavior>

### Recent Changes (needs extra attention)
- <file changed> → test with: `<command>`

### Examples
1. `<example command>` — Demonstrates: <what>
```

## 5. Validation

- Verify commands actually exist before listing them (check justfile, Makefile, etc.)
- Include expected output or behavior for each command.
- Note commands that require specific environment setup (API keys, services).

## Important notes

- Commands must be copy-pasteable — use exact syntax.
- Prefer `just <recipe>` / `make <target>` over raw commands when available.
- If `examples/` exist, include the most representative ones.
- For TUI/interactive apps, describe the key interactions (what keys to press, what to look for).
