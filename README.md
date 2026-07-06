# smorinlabs-harness

The public cross-platform plugin marketplace for **smorinlabs** — designed to
publish both a Claude Code marketplace and an OpenAI Codex marketplace from one
tree, following the same pattern as
[`smorin-harness`](https://github.com/smorin/smorin-harness). Plugin metadata will
live in a single source of truth (`plugin.meta.toml`) with generated per-platform
manifests once the first plugin lands.

## Plugins

_None yet — this marketplace was just stood up. Plugins land here as they graduate
to public._

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
