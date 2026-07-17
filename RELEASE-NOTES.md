# Release Notes

## v0.7.0 — 2026-07-16

### Added

- **html-codesign theme overlays** — Technical-minimal and High-contrast-dark
  now ship `codesign.md` overlays alongside Birchline, so codesign decision
  pages render in each theme's full personality instead of the neutral
  fallback: Technical-minimal's flat docs register (monospace IDs, tight
  geometry, blue accent), High-contrast-dark's color-scheme flip to layered
  near-black with off-white ink and a saturated accent. Every overlay value
  is sourced from that theme's `tokens.md` (no invented colors). Plugin
  validator generalized to assert all three overlays. use-html-theme 0.3.0 →
  0.4.0.

## v0.6.0 — 2026-07-16

### Added

- **html-codesign** — new skill in the `use-html-theme` plugin (0.2.0 → 0.3.0):
  interactive "pick and export" decision pages as single self-contained HTML
  files. Sections of pick-one/pick-any choices with per-section notes; stable
  IDs (`sec-01`, `ch-01-a`) that survive round-trips so "keep ch-01-a, swap
  ch-02-b" yields a diffable v2; an embedded, machine-validated spec
  (`validate_spec.py`, stdlib-only, fixture-tested); Markdown + JSON decision
  exports and clipboard re-prompts — a plain-text back-channel that works
  identically from Claude Code, Codex, or a stakeholder's browser. Theming
  cascades from the active use-html-theme theme (Birchline ships a rich
  `codesign.md` overlay) down to a neutral built-in. First-principles rebuild
  of the unpublished birchline-html-artifacts prototype: report mode dropped,
  constraints simplified to section-level exclusivity, theme lock-in removed.

## v0.5.0 — 2026-07-16

### Changed

- **use-html-theme** (0.1.0 → 0.2.0) — **migrated to a pure skill**: removed the
  `/theme` and `/theme-preview` slash commands. Slash commands are Claude
  Code-only — Codex and the other agents that read `~/.agents/skills` consume
  skills, not plugin `commands/` — so the plugin now behaves identically across
  every tool. All theme control is natural language ("switch to birchline",
  "no theme this session", "clear the theme", "list the themes", "remember this
  theme", "preview the themes" → renders the side-by-side catalog) plus
  `[theme: x]` / `[notheme]` inline flags. No capability lost.

## v0.4.0 — 2026-07-16

### Added

- **use-html-theme** — new plugin. On any HTML-generation (or restyle) request,
  offers a catalog of three fully-isolated visual themes — Birchline
  (warm editorial), Technical-minimal (docs-site neutral), High-contrast-dark
  (dashboard) — and applies the chosen one to all subsequent HTML in the
  session, with progressive disclosure (only the chosen theme's tokens are
  read). Ships the `use-html-theme` skill plus `/theme` and `/theme-preview`
  slash commands, a side-by-side preview template, and a structural validator.
  Overrides via natural language, `[theme: x]` / `[notheme]` inline flags, and
  the slash commands; the choice can persist per-project in
  `.claude/use-html-theme.local.md`. Brings the marketplace to five plugins,
  fifteen skills.

## v0.3.3 — 2026-07-10

### Fixed

- **project-next** — no longer claims "where are we?"; that utterance is now
  owned exclusively by the `session-recap` skill. Trigger carved out of the
  frontmatter `when_to_use`, the body's "When to use" list, and the docs
  page's "Triggers on" line.

## v0.3.2 — 2026-07-10

### Added

- **Docs backfill** — a dedicated page for every skill (14 pages under
  `docs/skills/`): what it does, trigger phrases, all three install modes,
  Codex specifics (`~/.agents/skills`), and an example session; guided-research
  carries its import provenance. README reworked around a single Install
  section with per-plugin skill tables linking to the pages.

## v0.3.1 — 2026-07-10

### Fixed

- **factor-harness** — `using-factor-harness` SKILL frontmatter corrected; same
  defect class as the document-merge frontmatter fix. A fleet-wide scan came
  back clean.

### Added

- **CI workflow** — `harness-kit gen --check` plus hardened static gates
  (absolute-path scrub, private-tooling-reference scrub, placeholder scan,
  marketplace parity); red-green proven on PR #1.

## v0.3.0 — 2026-07-05

### Added

- **guided-research** — an orchestration layer over the built-in `/deep-research`: decides when
  deep research is worth doing (four triggers + a value test), mode-gates (propose vs auto-run vs
  defer), shapes the prompt from project constraints, and organizes results into a durable,
  reusable research tree so knowledge gained once is never re-researched. Imported from a `.skill`
  bundle; scrub-verified clean.

## v0.2.1 — 2026-07-05

### Fixed

- **project-harness**: reconcile internal doc drift carried in from the standalone repo —
  the idea-capture cap is **four questions (fourth optional)** across `_conventions.md`,
  templates, and pointer blocks; `project-audit` runs **eleven** drift checks (its
  description previously said "ten"). No behavior change.

## v0.2.0 — 2026-07-05

First plugins land. The marketplace graduates from empty to three plugins, generated from
each plugin's `plugin.meta.toml` via the shared, anti-drift
[`harness-kit`](https://github.com/smorinlabs/harness-kit).

### Added

- **repo-hygiene** — four dev/release-readiness skills (`ci-audit`, `version-check`,
  `readme-sync`, `manual-test-guide`), converted from loose Claude commands.
- **factor-harness** — architecture-aware review, refactor, and cross-implementation dedup
  (4 skills + 3 subagents + hooks). Folded in from the now-archived
  `smorinlabs/factor-harness`.
- **project-harness** — lightweight `PROJECTS.md` project management (5 skills + 2 subagents
  + templates). Folded in from the now-archived `smorinlabs/project-harness`.

### Tooling

- Manifest generation via `harness-kit` (`just gen` / `just gen-check`) — a single source of
  truth (`plugin.meta.toml` + `harness.toml`) with byte-stable, anti-drift generated manifests.

## v0.1.0 — 2026-07-05

- Stand up the canonical lean, empty marketplace shape.
