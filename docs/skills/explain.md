# explain

Explains anything in a concrete-anchored style: every answer follows a fixed
anatomy — what it is in one plain-language line, just-enough context (2–4
sentences), a real before/after or worked example pulled from the actual
artifact, and the payoff ("what this gets you") — closing with an offer to go
deeper. Depth is an escalation, never the default. Three named modes layer on
top: **options** (a worked example per alternative, a recommendation with
why, and the runner-up when the call is close), **deeper** (bigger picture,
why the thing exists, the key decisions), and **steps** (numbered operator
instructions with exact commands, split into "what I can do" vs "what you
must do"). The mode is inferred from what's being pointed at; an explicit
argument always wins; genuine ambiguity gets one clarifying question before
writing.

**Triggers on:** `/explain <thing>`, "explain X", "help me understand",
"give me a before and after", "add more context on <finding/step/option>",
"show examples of the options so I can decide", "what does this change get
us", "what's the bigger picture here", "walk me through this change", "give
me step by step instructions", "which of these can you do and which do I
have to do"
**Arguments:** optional mode (`options`, `deeper`, `steps`) followed by the
target; bare `/explain <thing>` infers the mode

Not for manual testing steps (that is `manual-test-guide`, in this
marketplace's repo-hygiene plugin) and not for whole-session orientation or
catch-me-up recaps.

## Install

| Mode | When | How |
|---|---|---|
| Plugin (recommended) | You just want to use it | `/plugin install explain@smorinlabs-harness` |
| Dev symlink | You want to tweak/iterate | `git clone https://github.com/smorinlabs/smorinlabs-harness` then `ln -s "$(pwd)/smorinlabs-harness/plugins/explain/skills/explain" ~/.claude/skills/explain` |
| Direct copy | No marketplace access | copy `plugins/explain/skills/explain/` into `~/.claude/skills/` |

**Codex:** register the marketplace in `~/.codex/config.toml`
(`[marketplaces.smorinlabs-harness]`) and enable the plugin — or use the
dev-symlink path, also linking into `~/.agents/skills` (Codex's current
skills location).

## Example session

> Can you explain the retry backoff change with a before and after?
> → One plain-language line on what changed, two sentences of context, the
> actual before/after snippet from the diff, what the change gets you, and a
> one-line offer to go deeper into why exponential was chosen.

> Show me examples of options A, B and C so I can decide.
> → Options mode: a worked example per option with its trade-offs, one
> recommendation with the why, and the runner-up named because the call is
> close.
