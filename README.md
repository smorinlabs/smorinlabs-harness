# smorinlabs-harness

The public cross-platform plugin marketplace for **smorinlabs** — designed to
publish both a Claude Code marketplace and an OpenAI Codex marketplace from one
tree, following the same pattern as
[`smorin-harness`](https://github.com/smorin/smorin-harness). Plugin metadata will
live in a single source of truth (`plugin.meta.toml`) with generated per-platform
manifests once the first plugin lands.

## Plugins

| Plugin | What it does |
|--------|--------------|
| **repo-hygiene** | Repo & release-readiness skills: `ci-audit`, `version-check`, `readme-sync`, `manual-test-guide`. |
| **factor-harness** | Architecture-aware review, refactor, and cross-implementation dedup (4 skills + subagents). |
| **project-harness** | Lightweight `PROJECTS.md` project management (5 skills + subagents + templates). |
| **guided-research** | Orchestration layer over the built-in `/deep-research` — when to research, prompt shaping, and a durable reusable research tree. |

`factor-harness` and `project-harness` were previously standalone repos (now archived);
they live here as plugins. Manifests are generated from each plugin's `plugin.meta.toml`
via [`harness-kit`](https://github.com/smorinlabs/harness-kit).

## Install the marketplace

**Claude Code**

```
/plugin marketplace add smorinlabs/smorinlabs-harness
```

**Codex** — register a local marketplace source in `~/.codex/config.toml`:

```toml
[marketplaces.smorinlabs-harness]
source_type = "local"
source = "/absolute/path/to/smorinlabs-harness"
```

## Placement & tooling

This repo starts lean: a valid (empty) marketplace with no build tooling. When the
first cross-platform plugin lands, manifest generation is added by depending on a
shared `harness-kit` (extracted from `smorin-harness`), so the anti-drift generator
is never copied. Full rules:
[`smorin-harness/docs/skills-placement-strategy.md`](https://github.com/smorin/smorin-harness/blob/main/docs/skills-placement-strategy.md).

## License

MIT — see [`LICENSE`](./LICENSE).
