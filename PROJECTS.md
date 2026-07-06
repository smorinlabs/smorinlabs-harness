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

## [ ] Project P02: Shared harness-kit + first plugin (graduation)
**Goal**: When the first cross-platform plugin arrives, add manifest generation by
depending on the shared `harness-kit` (extracted from `smorin-harness`) rather than
copying the generator; author the plugin's `plugin.meta.toml`; generate manifests.

### Tests & Tasks
- [ ] [P02-T01] Depend on shared `harness-kit`; wire `just gen` / `gen-check`
- [ ] [P02-T02] First plugin `plugin.meta.toml`; generate `.claude-plugin` + `.codex-plugin`

---

- [ ] Regression Test Status
