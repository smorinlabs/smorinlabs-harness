---
name: version-check
description: Use when the user asks "what version", "check version", "is version published", "version mismatch", "bump version", "what version is this project", "check if published", or any request to inspect, compare, or validate project versions across local files, git tags, and package registries.
---

# Version check

Report the project version across all sources and flag discrepancies.

## Arguments (from the user's request)

- `--full` — check all sources including remote registries
- `--bump <patch|minor|major>` — show what the next version would be
- no args — show local version, git tag, and any discrepancies

## 1. Gather context

- Project type: `ls pyproject.toml Cargo.toml package.json go.mod 2>/dev/null`
- Latest git tag: `git describe --tags --abbrev=0 2>/dev/null`
- Local version: `grep -E '^version\s*=' pyproject.toml` or `grep '"version"' package.json`

## 2. Local version

Read the version from the project manifest:
- **Python**: `pyproject.toml` → `[project] version` or `[tool.poetry] version`
- **Node**: `package.json` → `"version"`
- **Rust**: `Cargo.toml` → `version`
- **Go**: git tags (Go uses tag-based versioning)

Also check `__init__.py` / `__version__.py`, `version.py` / `_version.py`, or any `VERSION` file.

## 3. Git tags

`git tag --sort=-v:refname | head -5`. Compare the latest tag to the local version; flag if they differ.

## 4. Remote branch version

`git show origin/main:pyproject.toml 2>/dev/null | grep -E '^version\s*='` (adapt to the manifest).

## 5. Published version (if `--full`)

- **PyPI**: `pip index versions <package>` or `https://pypi.org/pypi/<name>/json`
- **npm**: `npm view <package> version`
- **crates.io**: `cargo search <package> --limit 1`

## 6. Available bump commands

- justfile: `just --list | grep -i bump`
- Makefile: `grep -E 'bump|version' Makefile`
- Scripts: `ls scripts/bump* 2>/dev/null`

## 7. Report

```
## Version Report

| Source | Version | Status |
|---|---|---|
| Local (pyproject.toml) | 1.2.3 | — |
| Latest git tag | v1.2.3 | ✅ Match |
| Main branch | 1.2.3 | ✅ Match |
| PyPI (published) | 1.2.2 | ⚠️ Behind local |

### Bump Commands Available
- `just bump-patch` → 1.2.4

### Next Steps
- <recommendation based on discrepancies>
```

## Important notes

- If version sources disagree, clearly state which is authoritative.
- Show the actual bump commands available in the project's task runner.
- For Python projects, prefer `uv` over `pip` for any commands.
