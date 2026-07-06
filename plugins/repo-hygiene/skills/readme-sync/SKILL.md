---
name: readme-sync
description: Use when the user asks to "update README", "sync README", "check README", "is README up to date", "are docs consistent", "does README match the code", or any request to verify or update README.md to match the current state of the codebase.
---

# README sync

Audit `README.md` for consistency with the actual codebase and suggest (or apply) updates.

## Arguments (from the user's request)

- `--check` — only report issues, don't apply fixes (default)
- `--fix` — apply fixes to README.md
- `--since <commit>` — only check changes since a specific commit

## 1. Gather context

- README present: `ls README.md 2>/dev/null`
- Recent commits: `git log --oneline -10`
- Project type: `ls pyproject.toml Cargo.toml package.json 2>/dev/null`
- Task runner: `ls justfile Makefile 2>/dev/null`

## 2. Read current state

Read the full `README.md`; read recent git log to understand what changed
(`git log --oneline -20`). If `--since` is specified, scope to
`git diff <commit>..HEAD --name-only`.

## 3. Check categories

**Install instructions** — package name matches manifest; install commands work
(`pip install`, `uv add`, `npm install`); dependency requirements match.

**CLI commands & usage examples** — documented commands exist in project scripts; flags/options
match the implementation; run documented non-destructive examples to verify.

**API/code examples** — imported names exist in the package's public API (`__init__.py`,
`__all__`); documented signatures match reality; example code would run.

**Project structure** — documented directories/files exist; flag removed/renamed files.

**Links & references** — internal links (to other `.md` files) are valid; referenced paths exist.

**Task runner recipes** — referenced `just`/`make` commands exist; flag important new recipes
that aren't documented.

## 4. Report

```
## README Sync Report

### Inconsistencies Found
1. **<category>**: <description>
   - README says: `<quoted text>`
   - Actual: `<what's true now>`
   - Fix: <suggested change>

### Missing Documentation
- <new feature/command not mentioned in README>

### Outdated Sections
- <section referencing removed/changed functionality>

### README is Current
- ✅ <section that is accurate>
```

## 5. Apply fixes (if `--fix`)

Apply the suggested changes to `README.md`.

## Important notes

- Only suggest changes for real inconsistencies — don't rewrite style or add sections unprompted.
- If the README is correct and up to date, say so explicitly.
- Focus on factual accuracy (commands, paths, names) over prose quality.
