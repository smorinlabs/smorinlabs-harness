# reader-steps

The style spec for the moment work crosses from agent to human. Whenever a
response involves actions only the reader can or will perform — agent-
impossible actions (interactive auth, UI clicks, external approvals), manual
verification handoffs, or work the user claimed for themselves — those
actions are rendered as a delineated, self-contained block toward the
response's end.

The block is bounded by a blockquote rail (the container) with horizontal
rules separating header, steps, and footer. It binds to what it completes by
exact tracked ID and title, numbers its steps with a stable tag (`RB.1`) so
they stay referenceable across turns, and groups them by surface — ⌨️
terminal, 🌐 browser, 🖥️ desktop or system UI, 📱 phone, 🖐️ physical world —
under merged dividers that carry the group's intent. Each step is titled by
its **outcome** (never echoing a button label), with the literal command or
UI path below it and a `✓` verification line under that; `mono` means type
it, **bold** means click it, `▸` is one navigation hop.

It scales: a single step collapses to one inline line with no frame at all;
two or three steps on one surface drop the rules and dividers; eight or more
gain a `Map:` line and `Stop points:` so a long sequence reads as finite and
resumable. Navigation breadcrumbs promote to one hop per line past ~3 hops or
on any caveat. Reactive actions (a phone prompt fired by a terminal command)
nest inside the step that triggers them rather than posing as sequential
steps. Across turns the block re-renders as a scoreboard — done steps
collapse to a ✅ line, the live step keeps full detail, pending steps dim to
⬜ — closing explicitly when the last confirms. Errors, including failed
reader steps, state cause and fix with the corrected step restated.
Decisions are never steps — anything needing the reader's judgment is asked
(`question-walkthrough`) before instructing.

Worked renders at every scale live in the skill's `references/formats.md`.

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

> (agent finishes wiring a release-bot GitHub App; installation, key storage,
> and the first trigger can only be done by the user)
> → The response closes with a framed **YOUR STEPS ▼ · release-bot · 0/4 ·
> `[P26-T03]` · tag RB** block: a browser group (install the App on the repo)
> and a terminal group (store the key, set the secret, trigger the check),
> each step titled by its outcome with its command and `✓` beneath, the phone
> 2FA prompt nested inside the step that triggers it, and a footer reading
> "▲ That's all 4 — start with ▶ RB.1." The next turn re-renders it as a
> scoreboard at 1/4.
