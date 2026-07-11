# smorinlabs-harness

The public cross-platform plugin marketplace for **smorinlabs** — designed to
publish both a Claude Code marketplace and an OpenAI Codex marketplace from one
tree, following the same pattern as
[`smorin-harness`](https://github.com/smorin/smorin-harness). Plugin metadata will
live in a single source of truth (`plugin.meta.toml`) with generated per-platform
manifests once the first plugin lands.

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

`factor-harness` and `project-harness` were previously standalone repos (now archived);
they live here as plugins. Manifests are generated from each plugin's `plugin.meta.toml`
via [`harness-kit`](https://github.com/smorinlabs/harness-kit).

## Placement & tooling

This repo starts lean: a valid (empty) marketplace with no build tooling. When the
first cross-platform plugin lands, manifest generation is added by depending on a
shared `harness-kit` (extracted from `smorin-harness`), so the anti-drift generator
is never copied. Full rules:
[`smorin-harness/docs/skills-placement-strategy.md`](https://github.com/smorin/smorin-harness/blob/main/docs/skills-placement-strategy.md).

## License

MIT — see [`LICENSE`](./LICENSE).
