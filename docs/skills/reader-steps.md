# reader-steps

The style spec for the moment work crosses from agent to human. Whenever a
response involves actions only the reader can or will perform — agent-
impossible actions (interactive auth, UI clicks, external approvals), manual
verification handoffs, or work the user claimed for themselves — those
actions are rendered as a self-contained block toward the response's end: a
one-line done-so-far recap, numbered verb-first steps (one bounded action
each, exact commands/paths/values), inline mentions restated in full, a ✓
verification clause per step, no tangents, closing with the immediate next
move. Across turns, an in-flight manual process gets its live instruction
restated with position ("on 3 of 5") and an explicit completion when the
last step confirms. Errors — including failed reader steps — take the
matter-of-fact shape: cause, fix, corrected step restated. Decisions are
never steps: anything needing the reader's judgment is asked
(`question-walkthrough`) before instructing.

The skill is the **canonical spec**; the unprompted behavior comes from a
~12-line digest kept in the user's always-on global instructions
(`~/.claude/CLAUDE.md`, Codex global instructions), since a skill can't
reliably self-trigger on what a response turns out to contain.

**Triggers on (as a skill):** "format the manual steps", "what do I need to
do by hand", "what's left for me", "give me my steps", or composing any
handoff in the three trigger classes.
**Arguments:** none.

## Install

| Mode | When | How |
|---|---|---|
| Plugin (recommended) | You just want to use it | `/plugin install reader-steps@smorinlabs-harness` |
| Dev symlink | You want to tweak/iterate | `git clone https://github.com/smorinlabs/smorinlabs-harness` then `ln -s "$(pwd)/smorinlabs-harness/plugins/reader-steps/skills/reader-steps" ~/.claude/skills/reader-steps` |
| Direct copy | No marketplace access | copy `plugins/reader-steps/skills/reader-steps/` into `~/.claude/skills/` |

**Codex:** register the marketplace in `~/.codex/config.toml`
(`[marketplaces.smorinlabs-harness]`) and enable the plugin — or use the
dev-symlink path, also linking into `~/.agents/skills` (Codex's current
skills location).

To get the unprompted behavior, add the digest from the skill body's rules
to your global instructions file.

## Example session

> (agent finishes wiring a GitHub OAuth app; callback URL and token scope
> can only be set by the user)
> → The response ends with "**Your steps** — Done so far: app created,
> secrets set. 1. Open `github.com/settings/apps/…` → set callback to
> `https://…/cb` — ✓ page shows "Updated". 2. Run
> `gh auth refresh -s admin:org` — ✓ exits 0." Next turn, after step 1:
> "Step 1 done. You're on 2 of 2: run `gh auth refresh -s admin:org` — ✓
> exits 0."
