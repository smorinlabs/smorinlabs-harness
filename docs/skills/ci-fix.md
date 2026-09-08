# ci-audit

Audits a repository's CI/CD pipelines and pre-commit hooks — checks GitHub
Actions run status via `gh run list`, lints workflow files with `actionlint`,
audits Action version pins (flagging old majors and SHA-vs-tag choices), and
verifies pre-commit/lefthook hook installation and config completeness.
Cross-checks that `actionlint` runs as a pre-commit hook and that CI and
pre-commit run the same checks, then reports every finding — and applies
fixes when asked.

**Triggers on:** "GitHub Actions", "CI", "fix CI", "fix GitHub actions",
"actions broken", "check actions", "monitor actions", "actionlint",
"pre-commit hooks", "are hooks running", "check if actions are passing" ·
**Arguments:** `--fix` (automatically fix issues found), `--actions-only`
(skip pre-commit), `--hooks-only` (skip Actions), `--update-versions`
(update Action versions to latest)

## Install

| Mode | When | How |
|---|---|---|
| Plugin (recommended) | Just use it | `/plugin install repo-hygiene@smorinlabs-harness` |
| Dev symlink | Tweak/iterate | `git clone https://github.com/smorinlabs/smorinlabs-harness` then `ln -s "$(pwd)/smorinlabs-harness/plugins/repo-hygiene/skills/ci-audit" ~/.claude/skills/ci-audit` |
| Direct copy | No marketplace access | copy `plugins/repo-hygiene/skills/ci-audit/` into `~/.claude/skills/` |

**Codex:** register the marketplace in `~/.codex/config.toml`
(`[marketplaces.smorinlabs-harness]`, source_type local) and enable the
plugin — or dev-symlink into `~/.agents/skills` (Codex's current skills
location) as well.

## Example session

> "Fix CI"
> → gathers workflow files and `gh run list` status, runs `actionlint`
> against every workflow, audits Action version pins, checks lefthook
> installation and hook/CI parity, then reports a structured audit with
> recommendations — and, since `--fix` was implied, applies the fixes and
> shows the changes before committing.
