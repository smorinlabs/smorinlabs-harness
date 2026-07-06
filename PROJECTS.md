# PROJECTS

Status glyphs: `[?]` idea · `[ ]` scoped · `[~]` in progress · `[x]` done · `[-]` won't do · `[>]` superseded

## [x] Project P01: Harness skeleton (v0.1.0)
**Goal**: Stand up the canonical lean marketplace shape — a valid (empty)
`.claude-plugin/marketplace.json`, `plugins/`, README, LICENSE, and repo hygiene —
with no build tooling until the first cross-platform plugin lands.

### Tests & Tasks
- [x] [P01-T01] `.claude-plugin/marketplace.json` (valid JSON, empty `plugins`)
- [x] [P01-T02] README + install instructions; `.gitignore`; `plugins/` placeholder; LICENSE (MIT)
- [x] [P01-TS01] `python3 -m json.tool` validates the manifest

### Automated Verification
- `python3 -m json.tool .claude-plugin/marketplace.json` exits 0.

---

## [x] Project P02: Shared harness-kit + generator generalization (v0.2.0)
**Goal**: Extract `smorin-harness/src/smorin_harness/manifests.py` into a standalone,
installable `smorinlabs/harness-kit` (public); generalize the marketplace renderer
(parameterize name/owner/metadata via a repo-root `harness.toml`) so any harness can
use it; renderers already handle markdown-only multi-skill plugins. Wire
`smorinlabs-harness` to depend on it via `just gen` / `gen-check`.

### Tests & Tasks
- [x] [P02-TS01] Generator renders a markdown-only, multi-skill plugin fixture → valid Claude + Codex manifests + parameterized marketplace.json (8 tests green)
- [x] [P02-T01] Create `smorinlabs/harness-kit`: `harness_kit` package + `harness-kit` CLI (`gen [--check]`), pyproject/justfile/tests
- [x] [P02-T02] Publish `harness-kit` as a public repo
- [x] [P02-T03] `smorinlabs-harness`: add `pyproject.toml` (git-dep on harness-kit) + `justfile` + `harness.toml`; wire `just gen` / `gen-check`

## [x] Project P03: repo-hygiene plugin (4 commands → skills)
**Goal**: Convert the four kept loose commands (`ci-audit`, `version-check`,
`readme-sync`, `manual-test-guide`) into skills; author `plugin.meta.toml`; generate
manifests; list in the marketplace. Graduate them off `~/.claude/commands`.

### Tests & Tasks
- [x] [P03-TS01] Each skill has valid SKILL.md frontmatter + triggering description
- [x] [P03-T01] Convert the 4 commands → skills under `plugins/repo-hygiene/skills/`
- [x] [P03-T02] `plugin.meta.toml`; `just gen`; verify in `marketplace.json`
- [>] [P03-T03] Remove the 4 command files + activate skills — folded into P06-T02 (live-env wiring)

## [x] Project P04: factor-harness plugin (fold in + scrub)
**Goal**: Migrate factor-harness's 4 skills + 3 agents + hooks + `_conventions.md` into
`plugins/factor-harness/`; exclude `docs/superpowers/`; reword the README private-repo
note; author `plugin.meta.toml`; generate; list.

### Tests & Tasks
- [x] [P04-TS01] Scrub gate: no `/Users/` paths, no `docs/superpowers/` in migrated tree
- [x] [P04-T01] Copy skills/agents/hooks/_conventions (exclude docs/); private note N/A — README not carried into monorepo
- [x] [P04-T02] `plugin.meta.toml`; `just gen`; verify in `marketplace.json`

## [x] Project P05: project-harness plugin (fold in + scrub)
**Goal**: Migrate project-harness's 5 skills + references + 2 agents + templates +
`_conventions.md` into `plugins/project-harness/`; exclude `archive/research/`; fix the
`CLAUDE.md:99` dead pointer; reconcile 3-vs-4 / 10-vs-11 doc drift; generate; list.

### Tests & Tasks
- [x] [P05-TS01] Scrub gate: no `/Users/`, no `team@smorinlabs.com`, dead pointer gone (all in files not carried into monorepo)
- [x] [P05-T01] Copy skills/refs/agents/templates/_conventions (exclude archive/)
- [x] [P05-T02] `plugin.meta.toml`; `just gen`; CLAUDE.md pointer N/A (not carried); 3-vs-4 / 10-vs-11 doc drift deferred → P07

## [x] Project P06: Deprecate standalone repos + repoint + publish (v0.2.0)
**Goal**: Deprecate + archive `smorinlabs/factor-harness` & `smorinlabs/project-harness`
(content now in the monorepo, preserved); repoint the live `~/.claude/skills` dev-symlinks
to the monorepo; bump to v0.2.0; publish; verify the marketplace lists all 3 plugins.

### Tests & Tasks
- [x] [P06-T01] Deprecate + archive the 2 standalone repos (README/CLAUDE.md notice → smorinlabs-harness)
- [x] [P06-T02] Repoint 9 factor-*/project-* symlinks + activate 4 repo-hygiene skills → monorepo; preserve 4 command originals (absorbs P03-T03)
- [x] [P06-T03] Bump v0.2.0 + RELEASE-NOTES; regenerate; commit; tag; push
- [~] [P06-TS01] Automated: marketplace.json valid + lists 3 plugins ✓. Manual (user): `/plugin marketplace add smorinlabs/smorinlabs-harness` + install smoke test

## [?] Project P07: Reconcile project-harness doc drift
**Goal**: Reconcile cosmetic internal inconsistencies carried in from the standalone
repo — "≤3 vs ≤4 questions" (canonical is 4, fourth optional) across `_conventions.md`,
`project-add/SKILL.md`, templates; and "ten vs 11 checks" in `project-audit`. Non-blocking
quality cleanup; count the checks and pick the canonical value before editing.

---

- [ ] Regression Test Status
