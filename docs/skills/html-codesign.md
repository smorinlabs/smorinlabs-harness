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

## Closing the delivery

Both page skills in this plugin end the same way, via the shared
`references/delivery-close.md` at the plugin root — the editable source of
truth. Each skill reads its own vendored copy at
`references/_shared/delivery-close.md`, generated from that source by the
pinned harness-kit generator (kept in sync by `gen-check`) — added on top of
each skill's own delivery step, not in place of it.

**The full absolute path, on its own line, every time.** A relative path is
only meaningful from a working directory the reader cannot see, and the
person opening the file is routinely not in the shell that made it. If the
file landed somewhere temporary, the close-out says so plainly — scratch
paths get reaped, which is what makes the save offer below matter.

**Then it asks what you'd like to do next**, as a prose list rather than a
dialog (the path has to stay visible, and prose sharing a turn with
AskUserQuestion may never render). Every offer is strictly conditional:

| Offer | Only when |
|---|---|
| Open it in the browser | the session can actually reach one — never web-hosted, remote, headless, or a display-less sandbox, where the command reports success while nothing opens. In doubt → don't offer |
| Copy the path to the clipboard | same gate — the session runs on your own machine | on a remote session a clipboard write **reports success** into a clipboard you can't reach, a sharper failure than a browser-open that visibly does nothing |
| Add it to `shelf` | that skill is installed. If it isn't, `shelf` is not mentioned at all — not even as a suggestion to install it |
| Where to save it | the file sits somewhere temporary, **or anywhere the agent chose rather than you**. Read from context, never a fixed ranking — see below. Never moved silently |

### The save recommendation is read, not ranked

A fixed order gets this wrong in both directions: it files a design doc that
obviously belongs beside its spec into a general library, and it proposes a
permanent home for a page nobody will open again. So the question is *what is
this page, and where do things like it already live?* — answered with one
recommendation and its reason, plus the runner-up named in a clause.

| The page looks like… | Recommendation |
|---|---|
| something this session has already been saving somewhere | that same place — repeating an established destination beats introducing one |
| a document this repo already has a home for | that home — `docs/`, `docs/decisions/` or `adr/` for a decision record, beside the spec it explains. Convention beats invention |
| durable and repo-bound, but with no existing home | the location fitting the repo's shape, flagged as a *new* home so it's cheap to redirect |
| standalone — research, a comparison, a briefing, or anything with no clean place to live | `shelf`, **if that skill is installed**; if not, say plainly there's no obvious home and ask |
| ephemeral — a throwaway, or a page settling a decision being settled right now | **not saving it.** "This doesn't look like a keeper" is a real recommendation and spares a filing decision |

Those are examples, not a taxonomy — other clear homes exist (a notes vault, a
docs-site content tree, a path the project's own CLAUDE.md names) and the
context in front of you decides.

## Install

| Mode | When | How |
|---|---|---|
| Plugin (recommended) | Just use it | `/plugin install use-html-theme@smorinlabs-harness` (ships all three skills) |
| Dev symlink | Tweak/iterate | `git clone https://github.com/smorinlabs/smorinlabs-harness` then `ln -s "$(pwd)/smorinlabs-harness/plugins/use-html-theme/skills/html-codesign" ~/.claude/skills/html-codesign` |
| Direct copy | No marketplace access | copy just `skills/html-codesign/` — its shared references travel with it as vendored copies at `references/_shared/`. The one thing that doesn't survive a lone copy: sibling-skill theme paths (`../use-html-theme/...`) |

**Codex:** register the marketplace in `~/.codex/config.toml`. Pure skill —
behavior is identical on Codex and Claude Code.
