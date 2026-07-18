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
- [x] [P04-TS01] Scrub gate: no absolute personal paths, no `docs/superpowers/` in migrated tree
- [x] [P04-T01] Copy skills/agents/hooks/_conventions (exclude docs/); private note N/A — README not carried into monorepo
- [x] [P04-T02] `plugin.meta.toml`; `just gen`; verify in `marketplace.json`

## [x] Project P05: project-harness plugin (fold in + scrub)
**Goal**: Migrate project-harness's 5 skills + references + 2 agents + templates +
`_conventions.md` into `plugins/project-harness/`; exclude `archive/research/`; fix the
`CLAUDE.md:99` dead pointer; reconcile 3-vs-4 / 10-vs-11 doc drift; generate; list.

### Tests & Tasks
- [x] [P05-TS01] Scrub gate: no absolute personal paths, no team email, dead pointer gone (all in files not carried into monorepo)
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

## [x] Project P07: Reconcile project-harness doc drift (v0.2.1)
**Goal**: Reconcile cosmetic internal inconsistencies carried in from the standalone
repo — "≤3 vs ≤4 questions" (canonical is 4, fourth optional) across `_conventions.md`,
`project-add/SKILL.md`, templates; and "ten vs 11 checks" in `project-audit`. Non-blocking
quality cleanup; count the checks and pick the canonical value before editing.

## [x] Project P08: guided-research plugin (v0.3.0)
**Goal**: Add the `guided-research` skill (imported from a `.skill` bundle) as a public plugin —
an orchestration layer over the built-in `/deep-research` that decides when to research, shapes
prompts, and organizes results into a reusable research tree. Scrub-verified clean; attributed to
Steve Morin (bundle carried no embedded author/license).

### Tests & Tasks
- [x] [P08-TS01] Scrub gate: no secrets/PII; SKILL.md + 4 references intact
- [x] [P08-T01] Add plugin (`skills/guided-research/` + references); `plugin.meta.toml`; `just gen`
- [x] [P08-T02] Bump marketplace v0.3.0; dev-symlink; README + RELEASE-NOTES; tag

---

## [x] Project P09: use-html-theme plugin (v0.4.0)
**Goal**: Add the `use-html-theme` skill + `/theme` and `/theme-preview` commands as a public
plugin — on any HTML request, offer a 3-theme catalog (Birchline, Technical-minimal,
High-contrast-dark) and apply the chosen theme session-wide, with fully-isolated themes,
progressive disclosure, inline-flag / slash-command / natural-language overrides, and per-project
persistence. Built + whole-branch-reviewed as a standalone repo (use-html-theme v0.1.0), folded
in scrub-verified clean; attributed to Steve Morin.

### Tests & Tasks
- [x] [P09-TS01] Scrub gate: no secrets/PII/absolute paths; validator green in new home
- [x] [P09-T01] Fold plugin in (skills + commands + assets + scripts); `plugin.meta.toml`; `just gen` + gen-check clean
- [x] [P09-T02] Docs: `docs/skills/use-html-theme.md` + README section + count (five plugins, fifteen skills)
- [x] [P09-T03] Bump marketplace v0.4.0; dev-symlink both tools; skill-quality gate; RELEASE-NOTES; tag + push

---

## [x] Project P10: use-html-theme → pure skill (v0.5.0)
**Goal**: Migrate `use-html-theme` to skills-only by removing the `/theme` and `/theme-preview`
slash commands. Rationale: slash commands are Claude Code-only (Codex and the other `~/.agents/skills`
consumers read skills, not plugin `commands/`), and the fleet is deliberately skills-only. All control
folds into the skill's natural-language grammar + inline flags; the preview renders on request. No
capability lost; behavior now identical across tools.

### Tests & Tasks
- [x] [P10-T01] Remove commands/ + validator command checks
- [x] [P10-T02] Fold theme-control + preview into the skill (SKILL.md, references)
- [x] [P10-T03] Scrub slash-command refs (skill, meta, preview template, docs, README)
- [x] [P10-T04] Regen; validator green; skill-quality green; verify --deep green (both tools)
- [x] [P10-T05] Bump plugin 0.2.0 / marketplace v0.5.0; RELEASE-NOTES; tag + push

---

## [x] Project P11: html-codesign skill (v0.6.0)
**Goal**: First-principles rebuild of the unpublished birchline-html-artifacts codesign mode as a
theme-agnostic pure skill in the use-html-theme plugin. Interactive "pick and export" decision pages:
self-contained HTML, pick-one/pick-any sections, stable IDs, embedded machine-validated spec,
MD+JSON decision exports, clipboard re-prompts (portable text round-trip — identical on Claude Code
and Codex). Theming cascade: theme codesign.md overlay > theme tokens > neutral built-in; Birchline
overlay ports the original warm styling. Report mode abandoned (decision 2026-07-16); the old
prototype is donor material, to be archived.

### Tests & Tasks
- [x] [P11-TS01] Plugin validator extended with 14 html-codesign checks, RED-first, then green
- [x] [P11-TS02] validate_spec.py fixture tests: valid → exit 0; invalid → exit 1 with 7 error classes
- [x] [P11-T01] validate_spec.py (stdlib spec/export contract validator)
- [x] [P11-T02] SKILL.md + 5 references (spec-format, id-grammar, export-formats, iteration-loop, theming)
- [x] [P11-T03] codesign-template.html (neutral engine: embedded spec, exclusivity, exports, re-prompts)
- [x] [P11-T04] Birchline codesign.md overlay + use-html-theme composition note
- [x] [P11-T05] Docs page + README; plugin 0.3.0 / marketplace v0.6.0; whole-branch review (fable; all 7 Important findings fixed + verified)
- [x] [P11-TS03] E2E: fresh-session generation on claude-code AND codex; both embedded specs pass validate_spec.py
- [x] [P11-T06] Placements both tools; verify --deep green both tools; merge; tag v0.6.0 + push

---

## [x] Project P12: codesign overlays for all themes (v0.7.0)
**Goal**: Ship `codesign.md` overlays for Technical-minimal and High-contrast-dark (Birchline already
had one), so html-codesign pages get each theme's full personality via the cascade instead of the
neutral fallback. Overlays are 100% token-sourced; validator generalized to check all three.

### Tests & Tasks
- [x] [P12-T01] technical-minimal/codesign.md (flat docs register, mono IDs, blue accent)
- [x] [P12-T02] high-contrast-dark/codesign.md (color-scheme flip to dark, layered surfaces, off-white ink)
- [x] [P12-TS01] Validator asserts all 3 overlays; token-purity checked (no invented hex); gen-check green
- [x] [P12-T03] Docs updated (all three ship overlays); plugin 0.4.0 / marketplace v0.7.0; tag + push

---

## [x] Project P13: html-codesign ergonomics — contexts, collapse, slim exports (v0.8.0)
**Goal**: Per-question context-and-recommendation preambles (structured, choice-linked, ★ badges,
validator-required at generation), three layers of manual collapse (context block, hide-unchosen
options, section → dense summary row with followed/went-against rec markers, Collapse/Expand all),
and slim-default / full-toggle `codesign-answers` exports (MD+JSON) decoupled from the input schema.
Input `sections` core stays AskUserQuestion-shaped; contexts live in a sibling array; the
export-IS-spec invariant consciously dropped. Design spec:
`docs/superpowers/specs/2026-07-17-html-codesign-ergonomics-design.md`. New
`references/design-notes.md` records lineage + invariants for future editors.

### Tests & Tasks
- [x] [P13-TS01] Fixtures first: valid fixture gains contexts (exit 0); invalid fixture gains 6 new context error classes (15 errors total, exit 1)
- [x] [P13-T01] validate_spec.py: contexts layer checks (one per section, ctx-NN grammar, resolvable recommended ids, answers-doc rejection)
- [x] [P13-T02] codesign-template.html: ctx blocks + ★ badges, hide-unchosen, summary rows, Collapse/Expand all, Slim/Full toggle, codesign-answers exports (embedded sample spec validates; engine JS syntax-checked; DOM mirror verified)
- [x] [P13-T03] References: spec-format + export-formats rewritten, id-grammar (ctx-NN), iteration-loop (re-author contexts), theming (new component classes), NEW design-notes.md
- [x] [P13-T04] SKILL.md: context authoring step, collapse/export smoke tests, slim-default gotcha, design-notes pointer
- [x] [P13-TS02] Plugin validate.py extended (design-notes, contexts-in-template, answers-export checks) — all green; gen-check green
- [x] [P13-T05] Docs page + README row refreshed; plugin 0.4.0 → 0.5.0
- [x] [P13-T06] skill-quality gate (4/4 layers + verify --deep both tools); 49-assertion browser smoke test; commit a3a43db; marketplace v0.8.0 tag + push

---

## [~] Project P14: pr-merge-flow skill (repo-hygiene) (v0.9.0)
**Goal**: New `pr-merge-flow` skill in `plugins/repo-hygiene/` — drive an open PR to
merge by resolving every review thread: bounded bot-wait (Claude/Codex/Greptile/Copilot),
triage each comment (validate → verify by running where possible → fix valid / refute
invalid with a reasoned reply), re-review cycles (max 3), title-convention preflight
(repo CLAUDE.md, else Conventional Commits), then end per mode — `--auto` / `--confirm`
(default) / `--ready`, with opt-in `--deep` review (/code-review, Codex,
pr-review-toolkit). Per-repo prefs in git-ignored `.claude/pr-merge-flow.local.md`.
Quota-safe: rate-limit preflight, 20–30s poll floor, hard-bounded monitors (5–10 min +
one manual recheck), gh → gh api REST → curl ladder; GraphQL only for thread-state read
+ resolve mutation. Verdict: create-new (no fleet collision; boundary line to ci-audit;
accepted overlap with superpowers receiving-code-review recorded).

### Tests & Tasks
- [x] [P14-T01] Author SKILL.md (Iron Law, 8-step workflow, Red Flags) + references/polling.md + references/triage.md
- [x] [P14-T02] plugin.meta.toml 0.1.0 → 0.2.0 (description + keywords); `just gen` + gen-check green
- [x] [P14-T03] Dev placement both tools via skillsmith (claude-code, then codex) — static verify pass ×2; caught+fixed a YAML plain-scalar defect in the description first
- [x] [P14-T04] Docs: per-skill page docs/skills/pr-merge-flow.md + README table row; accepted-overlap baseline entry added in smorin-harness docs/doctor-baseline.md
- [x] [P14-TS01] skill-quality gate PASS — 4 layers green (982-char description, no collisions, no placeholders/PII, verify pass claude-code+codex); skill-reviewer deep pass: 3 majors + 5 minors found, all fixed (thread-reply recipe + databaseId, pulls/comments data model, .git/info/exclude-only, per_page=100 probes, draft/mergeable-null/branch-protection handling, Iron Law label, close-without-merge disambiguation)
- [ ] [P14-T05] Commit (conventional); optional release via skill-harness-release (v0.9.0)

---

- [ ] Regression Test Status
