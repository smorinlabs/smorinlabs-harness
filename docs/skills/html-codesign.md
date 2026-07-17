# html-codesign

Builds an interactive **"codesign" decision page** as a single self-contained
HTML file: sections of choices (pick-one or pick-any), per-section notes, and
a control bar with four actions — **Export → MD**, **Export → JSON**,
**Another draft**, **Here are my answers**. The reader — who may not be in
the chat at all — opens the file anywhere, toggles what they want, and sends
the export back. Every choosable element carries a **stable ID** (`sec-01`,
`ch-01-a`) so a pasted line like "keep `ch-01-a`, swap `ch-02-b`" resolves
precisely and a regenerated v2 is a *diff*, not a fresh blob. The spec behind
the page is embedded JSON, machine-validated before rendering
(`scripts/validate_spec.py`, stdlib-only), and re-emitted losslessly by the
JSON export; the Markdown export reads like a lightweight decision record for
PRs, Slack, or `docs/decisions/`.

**Triggers on:** wanting to choose between options and capture/export the
decision — "give me 4 layout directions and let me pick", "decision page for
plan A vs plan B", "prioritize these and let me toggle", codesign /
co-design, "pick from these", "compare the options", "choose and export" ·
**Not for:** read-only reports (that's just themed HTML), quick either/or
questions answerable in chat, or signing macOS/iOS apps and binaries
(Apple's `codesign` tool is unrelated) · **Arguments:** none — controlled in
natural language.

## How it composes with use-html-theme

This skill owns structure, behavior, and exports; the page's *look* comes
from a three-level cascade: the active theme's `codesign.md` overlay (all
three themes ship one — Birchline's warm choice cards, Technical-minimal's
flat docs register, High-contrast-dark's layered near-black), else generic
components painted with the theme's tokens, else a neutral built-in style.
Works with no theme at all; never mixes two.

## The loop

```
agent: spec JSON → validate_spec.py → themed HTML page
reader: toggle choices, add notes → Export MD/JSON or a re-prompt
anyone: paste it back into any chat → v2 reuses every surviving ID
```

The back-channel is plain text, so the loop works identically from Claude
Code, Codex, or a stakeholder who only ever saw the HTML file.

## Install

| Mode | When | How |
|---|---|---|
| Plugin (recommended) | Just use it | `/plugin install use-html-theme@smorinlabs-harness` (ships both skills) |
| Dev symlink | Tweak/iterate | `git clone https://github.com/smorinlabs/smorinlabs-harness` then `ln -s "$(pwd)/smorinlabs-harness/plugins/use-html-theme/skills/html-codesign" ~/.claude/skills/html-codesign` |
| Direct copy | No marketplace access | copy `plugins/use-html-theme/skills/html-codesign/` into `~/.claude/skills/` |

**Codex:** register the marketplace in `~/.codex/config.toml`. Pure skill —
behavior is identical on Codex and Claude Code.
