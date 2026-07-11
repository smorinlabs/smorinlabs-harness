# guided-research

An orchestration layer over the built-in `/deep-research` skill. It decides
*when* deep research is worth doing (four triggers: architectural
decision, domain best-practice, implementation deep-dive, error-driven),
applies a value test gated by work classification and by interaction mode
(interactive proposes, autonomous auto-runs against a stricter bar, by-hand
runs immediately), shapes the research prompt with project constraints in
a sub-agent, invokes `/deep-research`, and normalizes the output into a
durable, reusable research tree (`research/reference/`, `DECISION.md`
files with confidence and ranked runner-ups) so the same question is never
re-researched from scratch.

**Triggers on:** making an architectural decision (choosing between
libraries/algorithms/frameworks), kicking off a new project or major
feature with established best practices (billing, auth, caching, CLI
design), going deep on how a chosen library/technique works for a specific
use case, hitting repeated errors with an unfamiliar API after a couple of
ordinary web searches, or any explicit request for "deep" or "thorough"
research · **Arguments:** none

## Install

| Mode | When | How |
|---|---|---|
| Plugin (recommended) | Just use it | `/plugin install guided-research@smorinlabs-harness` |
| Dev symlink | Tweak/iterate | `git clone https://github.com/smorinlabs/smorinlabs-harness` then `ln -s "$(pwd)/smorinlabs-harness/plugins/guided-research/skills/guided-research" ~/.claude/skills/guided-research` |
| Direct copy | No marketplace access | copy `plugins/guided-research/skills/guided-research/` into `~/.claude/skills/` |

**Codex:** register the marketplace in `~/.codex/config.toml`
(`[marketplaces.smorinlabs-harness]`, source_type local) and enable the
plugin — or dev-symlink into `~/.agents/skills` (Codex's current skills
location) as well.

## Example session

> "We need to pick a rate-limiting library for the OpenAI client"
> → recognizes the architectural-decision trigger, clears the value test,
> proposes the research ("high value on rate-limiting strategies and
> library choices — want me to kick that off?"), shapes a
> constraint-aware prompt in a sub-agent, invokes `/deep-research`, and
> normalizes the result into `research/reference/rate-limiting.md` plus a
> `DECISION.md` naming the chosen library, the runner-up, and confidence —
> returning just the leaf path and a one-line outcome to the conversation.

## Provenance

Imported from a `.skill` bundle on 2026-07-05; the bundle carried no
embedded author or license. Maintained here by Steve Morin (MIT, repo
license).
