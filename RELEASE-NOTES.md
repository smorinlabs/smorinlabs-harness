# Release Notes

## v0.15.1 — 2026-07-23

### Fixed

- **question-walkthrough 0.2.1 — no tool call after the pre-read; same-turn
  prose loopholes closed** — a second field report confirmed same-turn prose
  may never render at all (the user receives only the question UI). The Iron
  Law is now two per-turn rules: the delivering turn ends with the pre-read
  as its final content, no tool call of any kind after it (the tool call
  opens the NEXT turn); the asking turn carries no prose the user needs —
  dialog-internal content only. Five loopholes patched (pile-confirmation
  list, sequencing rationale, re-evaluation narration before simple
  questions, intake-source listing moved into the dialog options, batch
  reports before parked re-asks) and two Red Flags added.

## v0.15.0 — 2026-07-23

### Added

- **question-walkthrough 0.2.0 — pre-read turns + note directives** — new Iron
  Law: every non-obvious question gets a pre-read (why it exists, impact,
  trade-offs, pros/cons, terms) delivered as a chat turn that ends BEFORE the
  AskUserQuestion dialog fires — same-turn context is invisible context, so
  the turn boundary is the delivery guarantee. Answer notes are classified
  (modifier / directive-extra / directive-redirect); directives get a one-line
  repeat-back + confirm, then run in an end-of-walk batch by default; the
  running tally gains `queued` and the closing table gains directive outcomes.
- **reader-steps 0.3.0 — every step carries its address** — browser steps give
  the literal deep-link URL; terminal steps give the working directory plus an
  executable that resolves on the reader's PATH; desktop and phone steps name
  the app and how it opens; placeholders say where their values come from; an
  address that cannot be sourced is stated as a gap, never guessed.
- **pr-merge-flow 0.4.0 (repo-hygiene) — Chrome fallback for GraphQL-blocked
  thread resolution** — a bounded browser-automation path (reset guard, route
  contract, degrade path) keeps thread triage moving when GraphQL quota blocks
  it; re-review cycle bound raised to 4 and now ends in a check-in; merge
  strategy defaults to merge commit per CLAUDE.md precedence.

### Fixed

- **repo-hygiene 0.5.0 (pr-merge-flow)** — red checks are classified before
  routing to ci-audit, so rate-limit statuses no longer misroute.
- **repo-finder 0.2.1** — searching a repo's name now returns that repo's
  worktrees; docs describe the actual local match instead of an
  exact-then-fuzzy ladder.
- **reader-steps 0.3.1** — private-tooling references removed from the address
  rule's examples (`~/.local/bin/demo-cli` convention), returning the CI
  no-private-tooling scrub to green.

## v0.14.0 — 2026-07-20

### Added

- **repo-finder — one-command repo resolution for agents (repo-finder 0.2.0)** —
  a thin skill wrapping a single-file, zero-dependency `uv` Python CLI that
  resolves a repo name to every local copy with the facts agents reach for
  next: path, origin, default branch, checkout-vs-worktree kind (worktrees
  labeled with their main repo), branch, dirty state, and build tooling. A
  config-bounded multi-root scan replaces `ls`/`find` cascades; matches are
  ranked deterministically (kind, then root order, then depth) with recency
  displayed rather than ranked, so the consuming model decides which copy is
  meant. On a local miss it filters server-side through one GitHub Search API
  call across the user's configured orgs and returns the exact `owner/name`
  plus a ready `git clone`. Designed from a session-history audit of 164
  Claude and 505 Codex sessions, which found roughly one session in eight
  spending tokens establishing where or what a repo is. Conforms to the CLI
  Design Standard v1.4.14 (small-CLI profile, minimal tier) with a committed
  conformance note; 25 tests.
- **question-walkthrough — adaptive one-question-at-a-time decisions
  (question-walkthrough 0.1.0)** — takes a pile of open questions or
  undecided to-dos (mined from the conversation, read from a document,
  given inline, or pulled from task systems), confirms the pile, sequences
  it by leverage so answers that could moot other questions come first, then
  walks it one question at a time with just-enough anchored context. Its
  defining move is re-planning after every answer: mooted questions dropped
  loudly, order revised, implied follow-ups added only with consent.
  Decisions are recorded back at their source and the walk closes with an
  outcome table.
- **reader-steps — the agent-to-human handoff format (reader-steps 0.2.0)** —
  renders actions only the reader can or will perform as a delineated,
  self-contained block: a bounded frame binding to the tracked item by exact
  ID, steps numbered with a stable tag and grouped by surface (terminal,
  browser, desktop or system UI, phone, physical world) under
  intent-carrying dividers, each step titled by its outcome with the literal
  command or UI path and a verification line beneath. `mono` means type it,
  **bold** means click it. It scales from a one-line inline form for a single
  step to a mapped, stop-pointed sequence past eight; nests reactive prompts
  inside the step that triggers them; re-renders across turns as a progress
  scoreboard; and states errors as cause and fix. Decisions are never steps —
  they are asked via `question-walkthrough` before anything is instructed.

### Fixed

- **project-harness: sandbox trigger boundary (project-harness 0.1.3)** —
  keeps the broad project/plan trigger on tracked work and routes Lima, VM,
  and sandbox execution-environment setup to the sandbox skills instead
  (via PR #2).

## v0.13.0 — 2026-07-18

### Changed

- **explain: gap diagnosis replaces the altitude ladder (explain 0.3.0)** —
  a follow-up `explain` no longer climbs a fixed rung sequence; it means
  "not enough to act on," and the skill re-reads its prior answer to
  diagnose what's blocking the action, trying remedies in
  observed-frequency order: step back to the bigger picture (the most
  common fix — the first answer was usually too specific), clearer plainer
  language, or a sharper more explicit example. Rewriting with the
  expansion woven in is the default (appending only small, self-contained
  deltas); follow-ups keep the prior answer's mode shape; a genuinely
  undiagnosable gap asks which part is unclear, with candidates. New house
  rule — the action anchor: every explanation is scoped to the live action
  in front of the user (what it changes, the value, the rationale, how it
  fits), or, with no live action, to recognizing when it matters later.

## v0.12.0 — 2026-07-18

### Added

- **explain follow-up invocations — the altitude ladder (explain 0.2.0)** —
  a bare `explain` (or `explain <guidance>`) right after an explanation is
  now a follow-up meaning "make that clearer": it climbs exactly one rung
  of an altitude ladder (rung 1 → clarify → deeper → internals), never
  repeating a rung. One similarity test arbitrates everything: a similar or
  bare re-invoke climbs; an argument naming an aspect of the current
  subject steers the climb; an argument outside it restarts at rung 1 on
  the new target; genuinely unclear cases repeat back the interpretation
  first. Explicit altitudes (`deeper`, accepting the closing go-deeper
  offer) jump straight there and set ladder position; above internals the
  ladder reports itself exhausted; cold starts target the last substantive
  subject or ask. Ships a follow-up-ladder calibration walkthrough.

- **pr-merge-flow post-merge cleanup + guarded default-branch sync
  (repo-hygiene 0.3.0)** — after a successful merge, the flow surveys
  cleanup read-only (local/remote PR branch, worktrees on the merged
  branch, prunable entries, stale merged branches) and runs only what is
  multi-select confirmed; plus an ask-first, ff-only sync of the local
  default branch with guards re-checked at execution time (dirty state,
  other-worktree checkout, local-ahead, in-progress git ops all block).

### Fixed

- v0.11.0 release notes backfilled with the explain plugin entry (it
  shipped inside v0.11.0 but was missing from the record).
- CI scrub: private-tooling references removed from P15/P17 project notes.

## v0.11.0 — 2026-07-18

### Added

- **explain plugin (new, v0.1.0)** — concrete-anchored explanation
  shorthand: `/explain <thing>` answers in a fixed anatomy (what it is →
  just-enough context → real before/after example pulled from the actual
  artifact → the payoff → a go-deeper offer), with options / deeper / steps
  modes inferred from the target (explicit argument wins; one clarifying
  question only on genuine ambiguity). Ships two worked calibration
  examples; least-privilege tools (Bash scoped to `git diff`/`log`/`show`);
  skill-quality gated and `verify --deep` green on both tools. Marketplace
  grows to six plugins, eighteen skills.

- **Codesign theme overlay coverage + fresh-session E2E** — all three theme
  overlays (Birchline, Technical-minimal, High-contrast-dark `codesign.md`)
  gain a token-sourced "New components" section styling the v0.9.0–v0.10.0
  html-codesign set: the context scaffold (what/why lead-ins, free-zone
  tables, ★ recommendation callout), collapsed summary rows with
  followed/went-against/skipped/question markers, the ★ rec badge, the
  Skip/Ask/hide-options action row, the question field, and the Slim/Full
  export toggle — no theme leaves neutral-styled islands. Plugin validator
  gains 30 overlay-coverage checks plus a per-overlay token-purity check
  (every var() must exist in that theme's tokens.md). Fresh-session E2E
  passed on both tools: clean claude-code and codex sessions each generated
  a page whose written and embedded specs pass validate_spec.py with the
  full component set and clean ID mirrors. use-html-theme 0.6.0 → 0.7.0.

## v0.10.0 — 2026-07-18

### Added

- **html-codesign ergonomics 2** — closes the gaps the first real codesign
  page exposed (governing principle: the page must work for a reader who
  wasn't in the room). A **Skip control on every question** (skipping
  clears picks; MD exports omit skipped sections while JSON records
  `skipped: true` so a v2 never re-asks unchanged); an **ask-a-question
  channel** per section (`q-NN` fields, a "Questions first" button that
  bundles every open question into one paste-back, `open_question` in both
  export formats — questions surface even on skipped sections); and
  **free-form context bodies** — the spec now carries only a context
  envelope (one-line summary, argued recommendation, recommended ids)
  while the page's context block holds unrestricted HTML (prose, pros/cons
  tables, inline SVG charts, data-URI images) on a clarity scaffold
  ("What this is" → "Why you're being asked" → analysis → ★
  recommendation) with hard authoring rules: question-shaped titles, zero
  session jargon. Full exports carry the envelope only — the page file is
  the durable rich-context archive. Legacy v0.8.0 `body` fields are
  tolerated as ignored extras. use-html-theme 0.5.0 → 0.6.0.

## v0.9.0 — 2026-07-18

### Added

- **pr-merge-flow skill** (repo-hygiene) — drives an open GitHub PR to
  merge by resolving every review thread: bounded wait for AI reviewer
  bots (Claude, Codex, Greptile, Copilot), per-thread triage (validate →
  verify by running code where possible → fix valid findings and push /
  refute invalid ones with a reasoned reply), re-review cycles (max 3),
  PR-title convention preflight, then ends per mode — `--auto`,
  `--confirm` (default), `--ready`, with opt-in `--deep` review. Per-repo
  preferences persist in a git-ignored `.claude/pr-merge-flow.local.md`.
  Quota-safe throughout: rate-limit preflight, 20–30s poll floor,
  hard-bounded monitors, gh → REST → curl ladder. repo-hygiene 0.1.0 →
  0.2.0.

## v0.8.0 — 2026-07-17

### Added

- **html-codesign ergonomics** — every question now opens with a required
  context-and-recommendation preamble (structured `contexts` layer joined to
  the AskUserQuestion-shaped sections core; ★ badge on recommended options;
  validator-enforced at generation), three layers of manual collapse
  (context block, hide-unchosen options with the note kept visible, whole
  sections folding to dense summary rows with followed/went-against-rec
  markers, plus Collapse/Expand all), and exports rebuilt as purpose-built
  `codesign-answers` documents — slim by default for the token-cheap agent
  loop, full ADR-style by toggle for human decision records. New
  `references/design-notes.md` records the AskUserQuestion lineage,
  input/output schema split, and edit invariants. Fixtures cover six new
  context error classes; template verified with 49 live-browser assertions.
  use-html-theme 0.4.0 → 0.5.0.

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
