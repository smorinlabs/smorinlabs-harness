# Release Notes

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
