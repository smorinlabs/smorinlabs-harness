# smorinlabs-harness

The public cross-platform plugin marketplace for **smorinlabs** — publishing a
Claude Code marketplace and an OpenAI Codex marketplace from one tree. Seven
plugins, nineteen skills. Plugin metadata lives in a single source of truth
(`plugin.meta.toml` per plugin); the per-platform manifests are generated, so
they can't drift.

## Install

**Use it** — add the marketplace, then install a plugin:

```
/plugin marketplace add smorinlabs/smorinlabs-harness
/plugin install repo-hygiene@smorinlabs-harness
```

Codex: register a local marketplace source in `~/.codex/config.toml`, then enable
the plugin:

```toml
[marketplaces.smorinlabs-harness]
source_type = "local"
source = "/absolute/path/to/smorinlabs-harness"
```

**Develop it** — clone the repo and symlink a skill straight into your local
skills directory to iterate on it:

```
git clone https://github.com/smorinlabs/smorinlabs-harness
ln -s "$(pwd)/smorinlabs-harness/plugins/<plugin>/skills/<skill>" ~/.claude/skills/<skill>
```

Codex users: dev-symlink the same skill into `~/.agents/skills` (Codex's current
skills location) as well.

### repo-hygiene

Repo & release-readiness skills.

| Skill | Does | Details |
|---|---|---|
| `ci-audit` | Audits GitHub Actions runs, lints workflows with actionlint, checks Action version pins, and verifies pre-commit hook parity — fixes with `--fix`. | [docs/skills/ci-audit.md](docs/skills/ci-audit.md) |
| `version-check` | Reports the project version across manifest, git tag, main branch, and (with `--full`) the registry, flagging mismatches. | [docs/skills/version-check.md](docs/skills/version-check.md) |
| `readme-sync` | Audits README.md against the codebase (install steps, CLI usage, code examples, structure, links) and applies fixes with `--fix`. | [docs/skills/readme-sync.md](docs/skills/readme-sync.md) |
| `manual-test-guide` | Generates a copy-pasteable manual testing guide, prioritizing recently changed areas. | [docs/skills/manual-test-guide.md](docs/skills/manual-test-guide.md) |
| `pr-merge-flow` | Drives an open PR to merge: waits (bounded) for AI reviewer bots, triages every review thread — verify, fix or refute with a reply — cycles until clean, then merges per mode (`--auto`/`--confirm`/`--ready`, opt-in `--deep`) and surveys post-merge cleanup (branches, worktrees, a guarded ff-only sync of the local default branch — confirm-gated, never automatic). | [docs/skills/pr-merge-flow.md](docs/skills/pr-merge-flow.md) |

### factor-harness

Architecture-aware review, refactor, and cross-implementation dedup.

| Skill | Does | Details |
|---|---|---|
| `using-factor-harness` | Orients across the bundle and routes to the right workflow skill. | [docs/skills/using-factor-harness.md](docs/skills/using-factor-harness.md) |
| `factor-architect` | Reviews a plan or shipped code against internal precedent and external patterns; produces a refactor spec. | [docs/skills/factor-architect.md](docs/skills/factor-architect.md) |
| `factor-scan` | Broad sweep for bugs, quality issues, and architectural smells over a code area. | [docs/skills/factor-scan.md](docs/skills/factor-scan.md) |
| `factor-dedup` | Compares N implementations and proposes a consolidation, or documents why to keep them separate. | [docs/skills/factor-dedup.md](docs/skills/factor-dedup.md) |

### project-harness

Lightweight `PROJECTS.md` project management.

| Skill | Does | Details |
|---|---|---|
| `using-project-harness` | Bootstraps the bundle in a repo and routes project-state changes to the right skill. | [docs/skills/using-project-harness.md](docs/skills/using-project-harness.md) |
| `project-add` | Captures a new project idea in at most 4 questions and reserves the next `P##` with an atomic commit. | [docs/skills/project-add.md](docs/skills/project-add.md) |
| `project-audit` | Runs 11 drift checks against `PROJECTS.md`/`projects/` and fixes per-finding on confirmation. | [docs/skills/project-audit.md](docs/skills/project-audit.md) |
| `project-next` | Surfaces a menu of in-progress, next-up, and recently touched projects. | [docs/skills/project-next.md](docs/skills/project-next.md) |
| `project-refine` | Refines notes, scopes an idea to ready, or decomposes a project into tasks. | [docs/skills/project-refine.md](docs/skills/project-refine.md) |

### guided-research

Orchestration layer over the built-in `/deep-research`.

| Skill | Does | Details |
|---|---|---|
| `guided-research` | Decides when deep research is worth doing, shapes and runs it, and organizes results into a reusable research tree. | [docs/skills/guided-research.md](docs/skills/guided-research.md) |

### use-html-theme

Themed-HTML toolkit, two pure skills — controlled entirely in natural language, portable across Claude Code and Codex.

| Skill | Does | Details |
|---|---|---|
| `use-html-theme` | Offers a catalog of three fully-isolated visual themes (Birchline, Technical-minimal, High-contrast-dark) on any HTML request and applies the chosen one to all subsequent HTML, with inline-flag and natural-language overrides, a side-by-side preview, and per-project persistence. | [docs/skills/use-html-theme.md](docs/skills/use-html-theme.md) |
| `html-codesign` | Builds interactive "pick and export" decision pages — self-contained HTML with pick-one/pick-any sections, a collapsible free-form context-and-recommendation preamble per question on a clarity scaffold (★ badge on the recommended option; rich bodies: tables, inline SVG charts, images), a Skip control and ask-a-question channel on every section, notes, stable IDs (`ch-01-a`), three layers of manual collapse (context, unchosen options, whole sections to dense summary rows) for reviewing decisions, a validated embedded spec, and slim-default / full-toggle Markdown/JSON answers exports (skips and open questions round-trip) for diffable v2s. Styled by the active theme via a per-theme overlay, with a neutral fallback. | [docs/skills/html-codesign.md](docs/skills/html-codesign.md) |

### explain

Concrete-anchored explanation shorthand.

| Skill | Does | Details |
|---|---|---|
| `explain` | Answers `/explain <thing>` in a fixed anatomy — what it is, just-enough context, a real before/after example, the payoff — with options/deeper/steps modes inferred from the target (explicit argument wins), and follow-up aware: a bare `explain` after an explanation diagnoses what's blocking action (step back to the bigger picture, clearer language, sharper example) and rewrites rather than repeats. | [docs/skills/explain.md](docs/skills/explain.md) |

### repo-finder

One-command repo resolution for agents — a thin skill wrapping a single-file,
zero-dependency uv Python CLI (CLI Design Standard conformant).

| Skill | Does | Details |
|---|---|---|
| `repo-finder` | Resolves a repo name to every local copy with orientation facts (path, origin, default branch, checkout-vs-worktree kind with the worktree's main repo, branch, dirty state, tooling) via a config-bounded multi-root scan, deterministically ranked; falls back to the user's configured GitHub orgs over `gh` REST-first and returns the exact `owner/name` plus a ready `git clone` command. Replaces token-expensive `ls`/`find` cascades and repeated `gh repo view` identity checks. | [docs/skills/repo-finder.md](docs/skills/repo-finder.md) |

`factor-harness` and `project-harness` were previously standalone repos (now archived);
they live here as plugins. Manifests are generated from each plugin's `plugin.meta.toml`
via [`harness-kit`](https://github.com/smorinlabs/harness-kit).

## Placement & tooling

Manifests are generated by the shared
[`harness-kit`](https://github.com/smorinlabs/harness-kit) (`just gen` /
`just gen-check`), depended on — never copied — so the anti-drift generator has
one home. Every push runs CI: gen-check plus static gates (path scrub,
placeholder scan, marketplace parity). Placement rules:
[`smorin-harness/docs/skills-placement-strategy.md`](https://github.com/smorin/smorin-harness/blob/main/docs/skills-placement-strategy.md).

## License

MIT — see [`LICENSE`](./LICENSE).
