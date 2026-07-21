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

## [x] Project P14: pr-merge-flow skill (repo-hygiene) (v0.9.0)
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
- [x] [P14-T03] Dev placement both tools (claude-code, then codex) — static verify pass ×2; caught+fixed a YAML plain-scalar defect in the description first
- [x] [P14-T04] Docs: per-skill page docs/skills/pr-merge-flow.md + README table row; accepted-overlap baseline entry added in smorin-harness docs/doctor-baseline.md
- [x] [P14-TS01] skill-quality gate PASS — 4 layers green (982-char description, no collisions, no placeholders/PII, verify pass claude-code+codex); skill-reviewer deep pass: 3 majors + 5 minors found, all fixed (thread-reply recipe + databaseId, pulls/comments data model, .git/info/exclude-only, per_page=100 probes, draft/mergeable-null/branch-protection handling, Iron Law label, close-without-merge disambiguation)
- [x] [P14-T05] Commit ce8329a ✓; pushed to public main via partial push ✓; v0.9.0 tag + RELEASE-NOTES cut as part of the P15-T06 release flow (deferred bookkeeping folded in as planned)

---

## [x] Project P15: html-codesign ergonomics 2 — skip, ask channel, free-form context (v0.10.0)
**Goal**: Close the gaps the first real codesign page exposed (governing principle: the page must
work for a reader who wasn't in the room). Engine-level Skip on every section (MD omits skipped,
JSON records `skipped: true`); per-section ask-a-question channel (`q-NN`) with a Questions-first
batch paste-back; context split into a schema envelope (summary/recommendation/recommended — badges,
verdicts, exports keep working) + free-form HTML body in the page (tables, inline SVG charts,
data-URI images) shaped by a clarity scaffold (`.ctx-what`/`.ctx-why`/free zone/`.ctx-rec`) with
hard authoring rules (question-shaped titles, zero session jargon); full exports carry the envelope
only — the page file is the rich-context archive. Design spec:
`docs/superpowers/specs/2026-07-18-html-codesign-ergonomics-2-design.md`. Sequenced before theme
overlay work (component set changes here).

### Tests & Tasks
- [x] [P15-TS01] Fixtures first: valid fixture → envelope form (legacy `body` tolerated, exit 0); invalid fixture exercises missing-summary (15 errors, exit 1)
- [x] [P15-T01] validate_spec.py: envelope checks (summary required, body ignored); docstring updated
- [x] [P15-T02] codesign-template.html: skip/ask controls + q-NN fields, Questions-first button, ctx-what/ctx-why scaffold + ctx-free zone (sample pros/cons table), skipped/❓ summary markers, skip-aware exports with open_question, question-shaped sample titles
- [x] [P15-T03] References: spec-format (envelope), id-grammar (q-NN, five prefixes), export-formats (skips/questions/envelope-only full), iteration-loop (Questions first, honor skips, answer q-NN), theming (new classes), design-notes (governing principle + decision history)
- [x] [P15-T04] SKILL.md: two-part context authoring step, hard writing rules, skip/ask in process + hard rules, 8-step smoke test, clarity gotcha
- [x] [P15-TS02] Plugin validate.py extended (scaffold/skip/ask/open_question checks) — green; gen-check green
- [x] [P15-T05] Docs page + README row refreshed; plugin 0.5.0 → 0.6.0
- [x] [P15-T06] Browser assertions 29/29 pre-rebase + 22/22 re-run post-rebase; skill-quality 4 layers + load verification green on both tools; surgical commit (rebased to c096230); release flow cut v0.9.0 (deferred P14 bookkeeping) then v0.10.0, both tagged + pushed

---

## [x] Project P16: codesign theme overlays + fresh-session E2E (v0.11.0)
**Goal**: Style the v0.9.0–v0.10.0 html-codesign component set in all three theme overlays
(birchline, technical-minimal, high-contrast-dark `codesign.md`) — `.ctx-what`/`.ctx-why`/
`.ctx-free` (incl. tables), `.summary` with `.s-mark-*` markers, `.badge-rec`, `.sec-actions`
(`.fold`/`.opt-toggle`/`.skip-toggle`/`.ask-toggle`), `.q-wrap`, `.seg` — per
`references/theming.md`'s component list, 100% token-sourced (P12 pattern, no invented colors);
and run the fresh-session E2E generation test on both tools (mirror P11-TS03: a clean session on
claude-code AND codex generates a page from the updated SKILL.md alone; embedded specs pass
`validate_spec.py`) — the one check the building sessions structurally could not run on
themselves. Scope decided via codesign answers export 2026-07-18: ch-01-a (all three in one
pass), ch-02-a (fresh-session test), ch-04-b (no fleet audit for this cycle).

### Tests & Tasks
- [x] [P16-T01] birchline codesign.md overlay: new-components section (warm editorial register; weight-500 lead-ins, oat/clay callout, sage/amber markers)
- [x] [P16-T02] technical-minimal codesign.md overlay: new-components section (flat docs register; accent-soft callout, semantic status colors)
- [x] [P16-T03] high-contrast-dark codesign.md overlay: new-components section (layered near-black; surface-step inset ctx, brighter-on-hover)
- [x] [P16-TS01] Plugin validate.py: 10 coverage checks x 3 overlays (RED-first: 30 fails -> green) + var()-vs-tokens.md purity check per overlay; gen-check green
- [x] [P16-TS02] Fresh-session E2E PASS both tools: codex exec (--skip-git-repo-check) and claude -p produce pages whose written AND embedded specs pass validate_spec.py, question titles, envelope contexts, full component set, clean ID mirror. Finding: headless claude -p outside the harness tree needs --add-dir <clone> to read dev-symlinked skill bodies (Skill tool accepts the name but cannot inline the body); interactive sessions unaffected
- [x] [P16-T04] Plugin 0.6.0 -> 0.7.0 (feature commit b62656f); marketplace v0.11.0; RELEASE-NOTES; tag + push

---

## [x] Project P17: explain plugin — concrete-anchored explanation shorthand (plugin v0.1.0, shipped in v0.11.0)
**Goal**: New single-skill plugin `explain`: `/explain <thing>` answers in a fixed anatomy
(what it is → just-enough context → real before/after example → payoff → go-deeper offer)
with modes inferred from the target (options / deeper / steps; explicit argument wins; one
question only on genuine ambiguity). Design grounded in session-transcript research
(2026-07-17: 172 sessions scanned, 104 matching messages, five recurring patterns —
before/after examples, "more context on <item>", options-with-recommendation-and-runner-up,
payoff framing, bigger-picture escalation). Trigger space verified clean against the
74-skill fleet; steps mode carves manual testing out to manual-test-guide. Least-privilege
tools: Read, Grep, Glob, AskUserQuestion, Bash scoped to git diff/log/show.

### Tests & Tasks
- [x] [P17-T01] Session-transcript research + pattern extraction with quotes
- [x] [P17-T02] Pre-skill design: proposal confirmed, interview (modes/triggering/tools), verdict create-new, route home 3 / new plugin / name `explain`
- [x] [P17-T03] Author plugin (plugin.meta.toml, SKILL.md, references/examples.md; description 966 chars after review revision)
- [x] [P17-T04] Wire: `just gen` + `just gen-check` green; marketplace entry generated
- [x] [P17-T05] Docs: docs/skills/explain.md + README section + plugin/skill count bump
- [x] [P17-T06] Dev placement on both tools (dev symlinks, claude-code then codex; static verify pass both)
- [x] [P17-TS01] skill-quality gate: 4 layers run; skill-reviewer findings applied (anatomy scope, steps-mode triggers, session-recap dangling ref, numbered workflow naming Glob + git subcommands, calibration-example fix); re-verified green both tools
- [x] [P17-TS02] Deep load verification: session-backed load pass on both tools (static + deep)
- [x] [P17-T07] Marketplace version fold-in: shipped inside v0.11.0 (P16 release cut on top of the explain commit); release-notes entry backfilled

---

## [x] Project P18: pr-merge-flow post-merge cleanup + guarded default-branch sync (v0.12.0)
**Goal**: After a successful merge, pr-merge-flow surveys cleanup read-only and presents
needs-cleanup vs already-clean lists — every item a named, discrete action with its exact
command (local/remote PR branch, worktrees on the merged branch, prunable entries, stale
merged branches; dirty state report-never-touch) — running only what is multi-select
confirmed (`--auto` report-only). Plus a guarded, ask-first sync of the local default
branch: blocked on dirty state, default checked out in another worktree, local-ahead
commits, or in-progress git ops; guards re-run at execution time (state can change between
survey and click); ff-only (`git fetch origin <default>:<default>` when unchecked-out,
else `git pull --ff-only`) — never bare pull, rebase, or force.

### Tests & Tasks
- [x] [P18-T01] Step 9 cleanup survey + multi-select confirm gate + Red Flags row
- [x] [P18-T02] Step 10 guarded double-checked default-branch sync (joins the step 9 menu) + Red Flags row; repo-hygiene 0.2.0 → 0.3.0
- [x] [P18-T03] Docs page + README row refreshed; gen-check green; re-gated (verify static both tools)
- [x] [P18-T04] CI scrub: 3 private-tooling references in P15/P17 notes removed (commit aeff13a; tree scan clean — latest CI run was red on this gate)
- [x] [P18-T05] Commit + push done (3d5f349); released in v0.12.0 (cut alongside P19)

---

## [x] Project P19: explain follow-up semantics — the altitude ladder (plugin v0.2.0, ships in v0.12.0)
**Goal**: Make `explain` conversation-aware: a bare `explain` (or `explain <guidance>`) right
after an explanation is a follow-up meaning "make that clearer" — climb exactly one rung of
the altitude ladder (anatomy → clarify → deeper → internals), never repeating the rung below.
One similarity test arbitrates everything: similar/bare → climb; argument naming an aspect of
the current subject → steer the climb; argument outside it → new target, restart at anatomy;
genuinely unclear → repeat back the interpretation first. Cold start defined (last substantive
subject, else ask). Design confirmed with user 2026-07-18 (adopt-with-refinements: unified
similarity test + explicit ladder over the five literal rules).

### Tests & Tasks
- [x] [P19-T01] SKILL.md: follow-up section + workflow step-1 hook + red-flag row; description reworked inside the envelope
- [x] [P19-T02] references/examples.md: follow-up ladder calibration example (clarify → deeper → steering → new target)
- [x] [P19-T03] Docs page + README row follow-up-aware; plugin.meta.toml 0.1.0 → 0.2.0
- [x] [P19-TS01] Re-gate: skill-quality layers green; skill-reviewer pass found the two-control-planes issue (modes vs ladder) — reconciled: rungs defined over any mode's first answer, explicit altitude jumps set ladder position, above-internals terminal state, cold-start boundary; description 990 chars
- [x] [P19-TS02] Deep load verification passed on both tools post-change
- [x] [P19-T04] Release v0.12.0 cut via skill-harness-release (with P18's pr-merge-flow work): bump, RELEASE-NOTES, tag, push

---

## [x] Project P20: explain gap diagnosis — replace the ladder (plugin v0.3.0, v0.13.0)
**Goal**: Replace the altitude ladder's mechanical climb with gap diagnosis, per user design
discussion 2026-07-18: a follow-up `explain` means "not enough to act on" — re-read the prior
answer and diagnose the block, trying remedies in observed-frequency order (too specific →
step back to bigger picture [most common]; unclear language → plain words; missing/vague
example → sharpen). Rewrite-over-append default (expansion woven in; append only small
self-contained deltas; never repeat material unimproved). Undiagnosable gap → ask which part
is unclear, with candidates (rare path). Action anchor adopted as root principle: "just
enough context" = enough for the action in front of you (what it changes, value, rationale,
fit); no live action → enough to recognize when it matters later — reshapes the default
anatomy's context section, not just follow-ups.

### Tests & Tasks
- [x] [P20-T01] SKILL.md: diagnosis section replaces ladder; action-anchored anatomy context; workflow/deeper-row/red-flag updates; description re-fit to envelope
- [x] [P20-T02] references/examples.md: diagnosis walkthrough (step back → sharpen → steer → new target → ask)
- [x] [P20-T03] Docs page + README row + plugin.meta.toml 0.2.0 → 0.3.0
- [x] [P20-TS01] Re-gate: reviewer third pass (1 major: remedy-1 shape conflict; 3 moderate: anchor placement/boundary, circular go-deeper close; 6 minor) — all 10 fixed: deeper back to explicit-only, follow-ups keep prior mode shape, anchor moved to Rules with discriminator, non-circular close, description slimmed to 895 chars
- [x] [P20-TS02] Deep load verification passed on both tools post-fix
- [x] [P20-T04] Release v0.13.0 cut: bump, RELEASE-NOTES, tag, push

---

## [x] Project P21: project-harness sandbox trigger boundary (plugin v0.1.3)
**Goal**: Keep the broad project/plan trigger focused on tracked work while
explicitly routing Lima/VM/sandbox execution-environment setup to the new
`sandbox-lima`, `sandbox-prepare`, and `sandbox-project` skills.

### Tests & Tasks
- [x] [P21-T01] Valid frontmatter description distinguishes PROJECTS.md/
      project-state management from guest execution setup; removed the legacy,
      unsupported `when_to_use` key while preserving its trigger content
- [x] [P21-T02] SKILL.md trigger-boundary section, red flag, and deliberate
      non-responsibility added with a concrete routing example in docs
- [x] [P21-T03] README row refreshed; project-harness 0.1.2 → 0.1.3
- [x] [P21-TS01] Generated manifests, public-repo scrub/parity checks,
      gen-check, quick validation, and static load verification green

---

## [x] Project P22: repo-finder plugin — one-command repo resolution for agents (plugin v0.1.0)
**Goal**: New single-skill plugin `repo-finder`: thin skill + single-file zero-dependency uv
Python CLI resolving repo names to local paths + identity facts (origin, default branch,
checkout/worktree/nested kind with worktree→main linkage, branch, dirty, tooling profile)
via config-bounded multi-root depth scan; gh REST-first remote org fallback (GraphQL as
configured fallback); deterministic ranking (kind → root order → depth; recency displayed,
never ranked — the consuming LLM decides). Evidence-based: dual session-history audit
(2026-07-19, 164 Claude + 505 Codex sessions) found ~1 in 8 sessions burning tokens on repo
location/identity (~90K tokens direct, 500–10K per episode, resident for 25–581 turns), plus
pervasive gh GraphQL rate-limit errors motivating REST-first. Conforms to CLI Design
Standard v1.4.14 (small-CLI profile, minimal tier; CONFORMANCE.md seeded). Phase 2 (not
started): cache tier, primarily for remote facts.

### Tests & Tasks
- [x] [P22-TS01] Test suite first: 20 subprocess tests (fixture tree with checkout, group-dir, worktree, vendored-nested, excluded; exit codes 0/2/3/4/5; JSON contract + error schema; REST-first gh stub; init conflict) — all pass
- [x] [P22-T01] CLI script `skills/repo-finder/scripts/repo-finder` (uv shebang, stdlib-only, argparse verb-first)
- [x] [P22-T02] Interface spec `docs/cli-interface.md` + `CONFORMANCE.md` (cli-standards plan mode, v1.4.14 pinned)
- [x] [P22-T03] SKILL.md (agent-side trigger description, ≤1000 chars) + plugin.meta.toml; `just gen`/`gen-check` clean
- [x] [P22-T04] Docs: `docs/skills/repo-finder.md` + README section + plugin/skill counts
- [x] [P22-T05] Dev placements on both tools (dev symlinks, claude-code then codex; static verify pass both)
- [x] [P22-TS02] skill-quality gate: content (desc 830 chars, no collisions, least-privilege Bash, no personal paths) ✓, docs (page + README, zero placeholders) ✓, conventions (meta.toml, marketplace, gen-check) ✓, loads (static load verification pass both tools, 0 err/0 warn) ✓
- [x] [P22-T06] Release: harness version bump + RELEASE-NOTES (shipped in marketplace v0.14.0)

---

## [ ] Project P23: repo-finder phase 2 — remote-only TTL cache (plugin v0.3.0; shrinks after P24 — search-filtered find no longer needs org-list caching)
**Goal**: Cache the one thing v1 still fetches live from the network: gh org repo listings.
Store per-org as `$XDG_CACHE_HOME/repo-finder/orgs/<org>.json` with a `fetched_at` stamp;
config gains `[cache] enabled = true` / `ttl_hours = 24`; R5.9 controls `--refresh` (force
refetch) and `--no-cache`; stale-but-present list served with a stderr note when gh is
unreachable (graceful offline); corrupt cache self-heals by refetch. CONFORMANCE.md caching
axis flips to yes. Evaluated 2026-07-19: v1's live local reads already eliminated the
audited token waste — this is latency/API-budget convenience on the miss path only
(~1–2s + 1–4 REST calls per remote event, low single digits/week). Explicitly rejected:
caching the local scan (stale-path risk vs <1s saved; live facts can't be cached anyway).

### Tests & Tasks
- [ ] [P23-TS01] Tests first: TTL expiry triggers refetch; `--refresh` bypasses fresh cache; offline falls back to stale with stderr note; corrupt cache file self-heals
- [ ] [P23-T01] Cache read/write + TTL in `gh_org_repos`; `[cache]` config keys; `--refresh`/`--no-cache` flags
- [ ] [P23-T02] Docs: cli-interface.md (flags, cache path), CONFORMANCE.md caching axis + R5.9, skill page note
- [ ] [P23-T03] plugin.meta.toml 0.1.0 → 0.2.0; `just gen`/`gen-check`; re-run skill-quality

---

## [x] Project P24: repo-finder v0.2.0 — remote correctness round (user feedback 2026-07-19)
**Goal**: Fix four field-tested findings from first real use. F1 (🔴): remote failures
silently collapse into "not in configured roots" (`gh_org_repos` → None swallowed by
`or []`) — track remote state, branch the miss message, exit 1 for degraded searches per
R6.3 partial-failure (not 5; R6.1 reserves 5 for conflict), JSON code `remote_lookup_failed`.
F2 (🔴 at 500-600 repos): `per_page=100` single page silently truncates → false not-founds;
`find` switches to server-side name filtering via the Search API (one call, KBs, vs 6+
paginated calls, MBs), `org` paginates internally with `--limit` as total cap + truncation
warning. F3 (🟡): rate-limit detection by stderr prose → authoritative `gh api rate_limit`
check on failure. F4: skill-native script invocation contract (PATH → announced skill base
dir → well-known placements), cross-platform Claude Code + Codex, any install mode —
bootstrap-repo PATH plumbing explicitly rejected as machine-specific.

### Tests & Tasks
- [x] [P24-TS01] Tests first per finding: degraded-state trio (failed org → exit 1 + honest message + JSON schema), search-path stub for find, org pagination + truncation warning, rate-limit authoritative check
- [x] [P24-T01] F1: remote_state/failed_orgs tracking, branched hints, exit 1 degraded
- [x] [P24-T02] F2: Search API find (live-verify user:/org: qualifier mechanics first), paginated org + warning
- [x] [P24-T03] F3: `gh api rate_limit` authoritative detection, prose match demoted to hint
- [x] [P24-T04] F4: SKILL.md invocation ladder, cross-platform
- [x] [P24-T05] Docs/spec/CONFORMANCE updates (exit table, R10.3 waiver narrowed), meta 0.2.0, gen, skill-quality re-gate, commit

---

## [x] Project P25: question-walkthrough — adaptive one-question-at-a-time decision engine (plugin v0.1.0)
**Goal**: New single-skill plugin: gather open questions from four sources (conversation
mining, pointed-at doc, inline list, task systems), confirm the pile, sequence by leverage
(answers that could moot/reshape others first), walk one AskUserQuestion at a time with
explain-anatomy context, re-plan the remaining pile after EVERY answer (drop mooted loudly,
reorder, add follow-ups with consent), record decisions at their source, close with an
outcome table. Carved vs project-refine (project scoping), html-codesign (async batch page),
explain (owns context anatomy). Built first in the 2026-07-19 three-skill round because
session-loose-ends (smorin-harness P16) delegates its confirmation loop to this engine.
Name chosen for future family grammar (question-*).

### Tests & Tasks
- [x] [P25-T01] SKILL.md (desc 988 chars, pure markdown); plugin.meta.toml; gen/gen-check green
- [x] [P25-T02] Docs page + README section + counts (eight plugins, twenty skills)
- [x] [P25-TS01] Gate: dev placements both tools, static verify pass, no placeholders
- [x] [P25-TS02] Deep load verification: session-backed load pass both tools (claude 2.1.215, codex 0.144.6), no findings

---

## [x] Project P26: reader-steps — agent→human handoff style spec (plugin v0.1.0)
**Goal**: New single-skill plugin distilled from a field-submitted "i-have-adhd" skill via a
question-walkthrough design session (2026-07-19): keep the manual-steps discipline, drop the
global always-on styling. Three trigger classes (agent-impossible actions, manual
verification handoffs, user-claimed work; decisions explicitly excluded — asked via
question-walkthrough, never listed); seven block rules (end placement, done-so-far recap,
numbered verb-first bounded steps, exact values, inline mentions restated, ✓ verification
per step, no tangents/closes with next move); cross-turn live-instruction restating with
position + completion sweep; matter-of-fact error shape incl. failed reader steps.
Architecture: skill = canonical spec; always-on ~12-line digest deployed to
~/.claude/CLAUDE.md (via smorin-bootstrap dotfiles) and ~/.codex/AGENTS.md — a skill can't
reliably self-trigger on what a response turns out to contain.

### Tests & Tasks
- [x] [P26-T01] SKILL.md (desc 988 chars) + plugin.meta.toml; gen/gen-check green
- [x] [P26-T02] Docs page + README section + counts (nine plugins, twenty-one skills)
- [x] [P26-T03] Digests: dotfiles/claude-CLAUDE.md (smorin-bootstrap) + ~/.codex/AGENTS.md
- [x] [P26-TS01] Gate: placements both tools, static verify pass, no placeholders

---

## [x] Project P27: reader-steps v2 — format spec from five prototyping rounds (plugin v0.2.0)
**Goal**: Turn the v1 prose rules into a full format spec, designed by rendering one realistic
handoff in competing formats each round (2026-07-19/20). Landed: bounded frame (blockquote
rail as container, horizontal rules separating header/steps/footer); header carrying
`0/N · [tracked-id] · tag XX` with a `Completes:` binding by exact ID and title; steps
grouped by surface under merged intent-carrying dividers; five surfaces incl. new 🖥️ desktop/
system UI; outcome-titles rule (titles never echo button labels — dissolves title/body
redundancy); notation contract (mono = type it, bold = click it, ▸ = one hop); ✓ default with
`Done when:` escalation; scale ladder (1 step inline / 2–3 light / 4+ full / 8+ adds Map and
Stop points with divider ranges); breadcrumb → hop-per-line past ~3 hops or on a caveat;
reactive actions nested inside their triggering step; cross-turn scoreboard re-render;
count/ID consistency rule. Worked renders split to references/formats.md per house style.

### Tests & Tasks
- [x] [P27-T01] SKILL.md rewritten (desc 996 chars) + references/formats.md with renders at every scale
- [x] [P27-T02] Both always-on digests refreshed (dotfiles/claude-CLAUDE.md, dotfiles/codex-AGENTS.md in smorin-bootstrap)
- [x] [P27-T03] plugin.meta.toml 0.1.0 → 0.2.0; docs page + README row rewritten; gen/gen-check green
- [x] [P27-TS01] Gate: static verify caught a YAML colon-space in the description (would have loaded with all frontmatter silently dropped) — fixed, re-verified pass

---

## [x] Project P28: pr-merge-flow Chrome fallback for GraphQL-blocked thread resolution (plugin v0.4.0)
**Goal**: Close the one failure the quota ladder cannot climb out of. pr-merge-flow reserves
GraphQL for exactly two operations — reading `isResolved` per review thread and the
`resolveReviewThread` mutation — and neither has a REST equivalent, so an exhausted GraphQL
budget stalls the Iron Law itself (`gh` porcelain, `gh api`, and `curl` all bill the same
endpoint). Add a narrow escape hatch: drive the PR's web UI via the claude-in-chrome tools,
whose session-authenticated internal endpoints draw on a different quota pool. Scope is those
two operations only — never a poll, never a merge, never `javascript_tool`. Guarded on both
ends: `decide_fallback_route` weighs the hourly GraphQL reset clock (near reset → bounded
wait beats opening a browser; secondary limits publish no reset → straight to browser) and a
confirmation gate fires in **every** mode including `--auto`, because suppressing
review-judgment questions is not consent to drive the user's logged-in Chrome. Reply-over-REST
precedes the browser resolve so a failed leg leaves a replied-but-open thread, never a silent
resolve; every click is verified by re-reading state; 2–3 failed interactions degrade to a
ready-report naming which threads were resolved, replied-to, or untouched.

**Out of Scope**
- Browser as a general fallback rung for any rate-limited call (thread replies, check status)
  — core budget is separate and ample; revisit only if the field shows it is needed.
- `--browser` / `--no-browser` flags and a `browser-fallback:` prefs key (deferred with the above).
- Description edit: left unchanged at 978/~1000 chars — the fallback adds no firing moments,
  so trigger budget is better spent elsewhere; keeps this a pure capability change (no overlap re-scan).

### Tests & Tasks
- [x] [P28-T01] `references/browser-fallback.md`: trigger conditions, reset guard + route contract, gate, procedure, degrade path, never-does list
- [x] [P28-T02] `decide_fallback_route` body — core-floor-first ordering, secondary limits straight to browser (no reset clock), reset-window wait; three knobs (`wait_max` 600s, `core_floor` 100, +5s buffer) documented as tunable policy
- [x] [P28-T03] Wiring: SKILL.md steps 1/3/4 + 4 Red Flags rows + See-also; polling.md escape-hatch section; triage.md pointers at both GraphQL blocks
- [x] [P28-T04] `allowed-tools` + 7 claude-in-chrome tools (read/click only; `javascript_tool`, `file_upload`, `gif_creator`, `read_network_requests` excluded)
- [x] [P28-T05] plugin.meta.toml 0.3.0 → 0.4.0; gen + gen-check green (all three manifests carry 0.4.0)
- [x] [P28-T06] Docs page + README row refreshed
- [x] [P28-T08] Post-review fixes: `read_page` restored (find caps at 20 matches — wrong-thread click risk); screenshots allowed as diagnostic-only, clicks stay `ref`-based (no grant change — `screenshot`/`zoom` are `computer` actions)
- [x] [P28-T09] Cross-tool browser entry points: availability table (Claude Code `claude-in-chrome` / Codex `chrome@openai-bundled` / neither → `stop`); ruled out `browser@openai-bundled` (in-app browser has no logged-in GitHub session) and `computer-use@openai-bundled` (no element refs → would force forbidden coordinate clicking); ref rule holds on every harness
- [x] [P28-T10] Live dogfood on PR #4 disproved the click path: `read_page` `filter:interactive` does not enumerate GitHub's Resolve buttons (identical output at depth 15 and 40 — rendered lazily, absent from the a11y tree); `find` returns them but anonymous (N identical labels, no thread identity); collapsed/outdated threads render no button at all. On the live PR every returned ref belonged to a thread that must NOT be resolved. Degraded without clicking — the bounded degrade path prevented a silent resolve
- [x] [P28-T11] Redesign to read-only: browser supplies `isResolved` only and annotates a REST-built inventory (REST carries `databaseId`, path, line, author, `in_reply_to_id`), so the ID bridge never has to survive the page. Resolution stays GraphQL-only; threads are replied-to and left open until quota returns. Resolves CodeRabbit CR-3 and dissolves CR-4
- [x] [P28-T12] CodeRabbit CR-1/2/4/5: gate states count only when known ("not yet known" at preflight); mandatory owner/repo/PR identity check from the page's own canonical URL before trusting content; idempotent replies (skip if one already exists via `in_reply_to_id`) in SKILL.md + triage.md; screenshots ephemeral by default, `save_to_disk` only with explicit consent
- [x] [P28-T13] `allowed-tools` 7 → 5 browser tools: `read_page` and `find` dropped (read-only procedure calls neither; they survive only as the documented evidence for why clicking fails). Distinct from the earlier bad drop — verified against the procedure, not a grep
- [x] [P28-T14] Red Flags: browser-cannot-click, valid-is-not-unclear (do not ask about strategy when the rubric names the action), new-bot-comments-are-step-5-not-a-re-plan
- [>] [P28-T10..T13] SUPERSEDED by T15-T17 — the read-only retreat was based on a wrong negative result; see below
- [x] [P28-T15] Retraction: the browser CAN resolve. Verified live on PR #4 — clicked a Resolve control by `ref`, thread flipped. The earlier "provably cannot" rested on three errors: (a) never scrolled — `read_page` reflects what is RENDERED and GitHub renders threads lazily, so depth 15 vs 40 tested the wrong axis entirely; (b) proposed the `#discussion_r<id>` anchor test and never ran it; (c) circular reasoning — treated this skill's own "never click by coordinate" style rule as evidence that clicking was impossible
- [x] [P28-T16] Correct architecture — per-thread anchoring, never enumeration: REST supplies the authoritative thread list with `databaseId`; navigate to `…#discussion_r<databaseId>` renders that one thread; `read_page` then carries its controls AND its permalink, so identity is confirmed before any click. Dissolves the enumeration hazards at once (no anonymous refs, no `find` 20-cap, no document-order assumption, no lazy-render dependence) and supplies CodeRabbit CR-3's ID bridge — the permalink carries the same `databaseId` REST uses
- [x] [P28-T17] Thread ledger keyed by `databaseId`: the thread set is live, not a snapshot. Re-fetch and merge every cycle and after every push; new entries run the identical verify → validate → (refute+resolve | fix+comment+resolve) loop; completion requires every ledger entry resolved. Counting open buttons is NOT a verification signal — observed 2→5 mid-run as Greptile posted a new thread while lazy content rendered. Verify per-thread by re-reading that thread's own state
- [x] [P28-T18] `allowed-tools` restored to 7 browser tools: `computer` is the only actuator and needs a `ref` from `read_page`/`find`; granting the actuator without a ref producer leaves coordinate-clicking as the only path — an incoherent config, and the direct cause of the earlier bad drop
- [x] [P28-T19] Retained from the CodeRabbit pass regardless of the retraction: mandatory PR-identity check (CR-2), idempotent replies (CR-4), ephemeral screenshots (CR-5), gate states count only when known (CR-1). Plus a standing rule: negative results need the same rigor as positive ones — vary the axis that matters before declaring impossibility, and never cite a house rule as proof a capability is absent
- [x] [P28-T20] Greptile P1: REST review-comments returns `id`/`node_id` — no `databaseId` (that is GraphQL's name for the same integer). Verified against the live API; corrected across all five files. Procedure had named a field absent from the endpoint it told you to call
- [x] [P28-T21] ID correlation table from real values: comment integer (REST `id` = GraphQL `databaseId` = page `#discussion_r<id>`) is the ONLY identifier on all three surfaces — which is what makes per-thread anchoring possible. Thread node id (`PRRT_…`) is GraphQL-only and is exactly what `resolveReviewThread` needs, so an exhausted GraphQL budget cannot even name the thread to the mutation — the structural reason the browser path must exist. `PRRC_` vs `PRRT_` prefix sanity check
- [x] [P28-T22] Greptile: a Red Flags row still asserted "the browser path is read-only" after the retraction, telling users to reject the documented fallback exactly when GraphQL is blocked. Fixed, plus a stale See-also line
- [x] [P28-T23] Greptile: REST inventory used `per_page=100` and treated one page as authoritative — past 100 review comments GitHub paginates and omitted threads get merged over. Now `gh api --paginate` / follow `Link` before declaring the set complete
- [x] [P28-T24] Endpoint asymmetry recorded: reply is `…/pulls/{n}/comments/{id}/replies` (PR number) but single-comment GET is `…/pulls/comments/{id}` (no PR number). Appending an id to the list route 404s and reads exactly like a deletion — it is not. Confirm disappearance against a fresh paginated list. (Hit live this session; a transient `unexpected EOF` on the retry nearly compounded it — errors are "no data", never a state change)
- [x] [P28-T25] Greptile: procedure replied (step 6) before reading thread state (steps 7-8), but the REST inventory carries no `isResolved` and lists resolved/unresolved identically — so a literal run posts replies to threads a reviewer already auto-resolved. Observed live this session: Copilot auto-resolved its own thread 3617915140 once the fix landed. Reordered to anchor → confirm identity → read state → (already resolved: record and skip) → reply → click → verify
- [x] [P28-T26] Re-review cycle policy: bound raised 3 → 4, and the bound now ends in a CHECK-IN rather than a silent stop — report the ledger by id, then ask. Options: continue-until-clean (no cycle limit, bounded instead by a 10-minute wall clock, polling rules still apply inside it), gate/merge now, or stop. New prefs keys `cycle-bound` and `continue-until-clean` for repos that always want one answer. Rationale from this run: five cycles happened and convergence made continuing feel obviously right — which is exactly when a run is most tempted to keep going on its own judgment
- [x] [P28-TS01] Gate: skill-quality on pr-merge-flow; static verify both tools
- [x] [P28-T07] Commits 8e3f848 / 13d8e52 / 502e5a6 on `feat/pr-merge-flow-browser-fallback` (rebased onto origin/main — release/v0.14.0 was squash-merged as 998ce09)

---

## [~] Project P29: reader-steps — every step carries its address (plugin v0.3.0)
**Goal**: Close the gap between "the step names an action" and "the reader can start it".
A browser step reading "your app's settings page" and a terminal step reading `just update`
are both incomplete — the first withholds the URL, the second withholds both the working
directory and any evidence that `just` resolves on the reader's PATH. Add one authoring
rule covering all five surfaces: every step states where it starts. Browser gives the
literal deep-link URL; terminal gives the working directory (carried once on the group
divider when the group shares one, per-step when it doesn't) plus an executable that
resolves — a bare command name only when `command -v` was actually run this session,
otherwise a full path or a runner invocation (`uv run`, `npx`). Desktop and phone steps
name the app and how it opens. Two corollaries: placeholders the reader must substitute
say where their value comes from, and an address that cannot be sourced is stated as a
known gap rather than guessed. The rule ships to both delivery paths — the canonical
SKILL.md and the always-on digest in global instructions, since the unprompted behavior
comes from the digest.

**Out of Scope**
- Per-step prerequisite/install checks ("if `gh` is missing, `brew install gh`") — roughly
  doubles step length and turns the handoff block into a setup guide; the executable-address
  rule already covers the failure it targets.
- Description edit: frontmatter and meta descriptions left unchanged (978/~1000 chars). The
  rule changes what a rendered step contains, not when the skill fires — a pure capability
  change, so no overlap re-scan and no README row churn.

### Tests & Tasks
- [x] [P29-T01] SKILL.md `## Every step says where it starts` — per-surface address table,
      terminal's two halves (directory + resolvable executable), substitution sourcing,
      "unknown beats invented"; placed before `## Navigation and reactive steps`
- [x] [P29-T02] Red Flags: 4 rows — obviously-in-the-repo-directory, `gh`-is-definitely-installed,
      they'll-find-the-settings-page, plausible-looking-URL
- [x] [P29-T03] `references/formats.md` — existing worked renders corrected (they violated the
      new rule: RB.2–RB.4 ran `op`/`gh`/`git` with no directory, NM.12 ran a bare `just update`
      on a machine whose PATH the bootstrap had just rewritten)
- [x] [P29-T04] `references/formats.md` `## Addresses` — shared-directory-on-divider vs
      per-step form, the three correct executable forms, placeholder sourcing, honest-gap render
- [x] [P29-T05] plugin.meta.toml 0.2.0 → 0.3.0; gen + gen-check green
- [x] [P29-T06] Docs page refreshed (README row unchanged — description unchanged)
- [ ] [P29-T07] Digest sync: `~/.claude/CLAUDE.md` reader-task block gains the address rule
      (outside the repo — the unprompted path does not read SKILL.md)
- [ ] [P29-TS01] Gate: skill-quality on reader-steps
- [ ] [P29-T08] Branch `feat/reader-steps-step-addresses`, PR, merge-commit, ff main

---

- [ ] Regression Test Status
