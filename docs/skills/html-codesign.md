# html-codesign

Builds an interactive **"codesign" decision page** as a single self-contained
HTML file: sections of choices (pick-one or pick-any), each opening with a
collapsible **context & recommendation preamble** — free-form rich content
(prose, pros/cons tables, inline SVG charts, images) on a clarity scaffold
(*What this is* → *Why you're being asked* → analysis → ★ recommendation),
with a ★ badge on the recommended option — plus per-section notes, a
**Skip control on every question** (deliberately-not-deciding is a
first-class answer), an **Ask-a-question channel** for "I can't answer this
yet", and a control bar — **Export → MD**, **Export → JSON** (slim by
default, full ADR-style by toggle), **Another draft**, **Here are my
answers**, **Questions first**, plus **Collapse/Expand all**. Three layers
of manual collapse make review ergonomic: fold the context out of the way,
hide unchosen options (the note stays visible), or fold a whole section to
a dense one-line summary — question, picks, followed/went-against/skipped/❓
markers, and the note — so a finished page scans as a review of the
decision. The reader — who may not be in the chat at all — opens the file
anywhere, toggles what they want, and sends the export back. Every
choosable element carries a **stable ID** (`sec-01`, `ch-01-a`, `ctx-01`,
`q-01`) so a pasted line like "keep `ch-01-a`, swap `ch-02-b`" resolves
precisely and a regenerated v2 is a *diff*, not a fresh blob. The spec
behind the page is embedded JSON, machine-validated before rendering
(`scripts/validate_spec.py`, stdlib-only — every section must carry a
context envelope; the rich body lives free-form in the page); exports are
purpose-built `codesign-answers` documents — slim for the agent loop
(ID · question · picks · note; skipped sections drop out of MD but export
`skipped: true` in JSON; open questions always surface), full for human
decision records in PRs, Slack, or `docs/decisions/`.

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
agent: spec JSON (sections + context envelopes) → validate_spec.py
       → themed HTML page (free-form context bodies on the clarity scaffold)
reader: review contexts, answer / skip / raise questions, add notes,
        fold sections to review → Export MD/JSON (slim default / full
        toggle), "Questions first", or another re-prompt
anyone: paste it back into any chat → questions answered by q-NN, skips
        honored, v2 reuses every surviving ID, contexts re-authored fresh
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
