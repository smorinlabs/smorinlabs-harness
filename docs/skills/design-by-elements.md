# design-by-elements

A process skill for prototyping the *form* of an artifact — terminal output, a
report or CLI layout, a table, a status block, a page or email mockup — before
building it. It runs a five-move loop, once per element: (1) interrogate what the
element *means* and which reader-question it answers before arguing form; (2)
decompose the artifact into independently lockable elements tracked in a section
queue; (3) offer 2–3 deliberately *opposed* variants with short IDs (via
`AskUserQuestion`, one element at a time) rather than a catalog; (4) lock each
element and record `Fork | Decision | Rationale` in a decisions log; (5) promote
every fix into a **named rule** that then polices the rest of the artifact — the
move that makes the design *converge* instead of looping. It closes with an
explicit zoom-out pass to re-integrate the locked pieces, and carries companion
principles (admission tests, design-for-scale up and down, weight-by-consequence,
name-everything, the column-vs-line density rule, medium awareness). Lineage:
Atomic Design, pattern language, design-rationale capture, and concept design.

**Triggers on:** "design this layout/format", "prototype the look", "iterate on
this output", "let's lock this section", "element-wise", or a formatting debate
that keeps looping. NOT general feature/product brainstorming (that's
`superpowers:brainstorming`), and NOT an async HTML decision page (that's
`html-codesign`).
**Arguments:** none — it interviews per element as it goes.

## Install

| Mode | When | How |
|---|---|---|
| Plugin (recommended) | You just want to use it | `/plugin install design-by-elements@smorinlabs-harness` |
| Dev symlink | You want to tweak/iterate | `git clone https://github.com/smorinlabs/smorinlabs-harness` then `ln -s "$(pwd)/smorinlabs-harness/plugins/design-by-elements/skills/design-by-elements" ~/.claude/skills/design-by-elements` |
| Direct copy | No marketplace access | copy `plugins/design-by-elements/skills/design-by-elements/` into `~/.claude/skills/` |

**Codex:** register the marketplace in `~/.codex/config.toml`
(`[marketplaces.smorinlabs-harness]`) and enable the plugin — or use the
dev-symlink path, also linking into `~/.agents/skills` (Codex's current
skills location).

## Example session

> "Let's design the header block for this status report — element-wise."
> → names what the header is *for* and its one reader-question (move 1);
> decomposes the block into glyph / id / title / tag elements and opens a section
> queue (move 2); for the first element offers three *opposed* variants
> (`H1`/`H2`/`H3`) via `AskUserQuestion` with previews (move 3); on the pick,
> locks it and writes a `Fork | Decision | Rationale` row (move 4); turns the
> user's aside ("the tag is obvious from the title") into a named rule that then
> applies to every later element (move 5); after all elements lock, runs the
> zoom-out pass to check spacing and rule-consistency across the whole block.
