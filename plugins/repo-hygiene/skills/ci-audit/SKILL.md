---
name: ci-audit
description: Use when the user asks about "GitHub Actions", "CI", "fix CI", "fix GitHub actions", "actions broken", "check actions", "monitor actions", "actionlint", "pre-commit hooks", "are hooks running", "check if actions are passing", or any request to audit, fix, monitor, or troubleshoot CI/CD pipelines and pre-commit hooks.
---

# CI/CD & pre-commit audit

Audit a repository's CI/CD pipelines and pre-commit hooks, and optionally fix issues.

## Arguments (from the user's request)

- `--fix` — automatically fix issues found
- `--actions-only` — only check GitHub Actions, skip pre-commit
- `--hooks-only` — only check pre-commit hooks, skip Actions
- `--update-versions` — update GitHub Action versions to latest

## 1. Gather context

Orient first (skip parts excluded by the arguments above):

- Workflows: `ls .github/workflows/*.yml .github/workflows/*.yaml 2>/dev/null`
- Pre-commit config: `ls lefthook.yml .pre-commit-config.yaml 2>/dev/null`
- Recent runs: check `gh auth status`, then `gh run list --limit 10`

## 2. GitHub Actions status

Check current workflow run status with `gh run list --limit 10`. If any runs failed, get
details: `gh run view <run-id> --log-failed`.

## 3. Workflow file linting

Run actionlint on all workflow files: `actionlint .github/workflows/*.yml`. If actionlint
is not installed, note it as a finding and suggest `brew install actionlint` (macOS) or the
platform-appropriate install.

## 4. GitHub Action version audit

For each workflow file:
- Extract all `uses:` directives (e.g. `actions/checkout@v4`)
- Check if the version is the latest available
- Flag actions using commit SHAs vs tags (SHAs are more secure but harder to maintain)
- Flag actions pinned to old major versions

If `--update-versions` is specified, update to latest versions.

## 5. Pre-commit hooks audit

**For lefthook.yml:** verify lefthook is installed (`lefthook --version`); check hooks are
installed (`ls .git/hooks/pre-commit`); verify referenced tools are available (ruff,
actionlint, pytest, bandit, etc.); check config completeness.

**For .pre-commit-config.yaml:** verify pre-commit is installed; check hook versions are current.

## 6. Cross-check

- Ensure actionlint is part of pre-commit hooks (common gap)
- Ensure CI runs the same checks as pre-commit hooks
- Check for workflow/hook mismatches (different tool versions, missing checks)

## 7. Report

```
## CI/CD Audit Report

### GitHub Actions Status
- ✅/❌ Workflow: <name> — <status>

### Workflow Lint Results
- ✅ No actionlint issues / ❌ X issues found
  - <file>:<line> — <issue>

### Action Version Status
- ✅/⚠️ <action>@<version> — current: <latest>

### Pre-commit Hooks
- ✅/❌ Hooks installed: <yes/no>
- ✅/❌ Tools available: <list>
- ⚠️ Missing from hooks: <list>

### Recommendations
1. <action item>
```

## Important notes

- Always check `gh auth status` before using gh commands.
- If actionlint is not installed, suggest `brew install actionlint` (macOS) or the appropriate install.
- When fixing issues with `--fix`, always show the changes before committing.
