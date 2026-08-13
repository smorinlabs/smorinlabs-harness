# session-handoff

The forward-facing sibling of `session-recap` and `session-loose-ends`: instead
of orienting you in the current session or cleaning it up, it **packages the
current session into a self-contained handoff** that a brand-new, zero-context
session — often on a *different machine* — can act on cold. Its governing
assumption is that the reader inherits nothing: no scrollback, no compacted
summary, no shared paths. So every fact is stated in full, every path appears
both repo-relative (canonical) and absolute (a labeled same-machine
convenience), and the **portability preflight sits above all content** — because
the load-bearing failure of a handoff is not a stale path but **uncommitted work
that does not exist on the other machine.**

It **scopes to an outcome first** — infers the likely goal(s), shows them, and
confirms or asks (one question, several, or none by confidence) before
generating — then filters the whole handoff to that goal, stating what's out of
scope. It carries the seven content classes, the highest-value of which is the
tacit context that dies on compaction: decisions and *why*, constraints, and
**rejected approaches and why (so the new session doesn't re-derive a dead
end)**. Since v0.6.0 it also **carries the essence instead of just linking it**:
every load-bearing artifact (plan, design, spec) is vetted — exists · committed
· substantive — and distilled into an inlined plan skeleton, with a
`Self-contained: ✓/⚠` verdict on the Outcome line, so the handoff never
silently inherits a missing, untraveled, or stub referenced doc (its quality
would otherwise be `min(handoff, doc)`). Delivery adapts to size: short
handoffs print an inline prompt block; involved ones write a `docs/handoffs/`
file plus one launch line. Evidence gathering reuses `session-recap`'s
`transcript_digest.py` via a verified symlink-safe recipe and records a
one-line effectiveness note each run.

**Triggers on:** "hand this off", "write a handoff", "start a fresh/new session
with this context", "continue this in a new window/session", "pick this up on
another machine", "pass the baton". Not backward orientation ("where was I" —
that's `session-recap`) and not in-place cleanup (`session-loose-ends`).
**Arguments:** `--file` / `--inline` force the delivery mode; an optional
free-text outcome hint seeds scoping.

## Install

| Mode | When | How |
|---|---|---|
| Plugin (recommended) | You just want to use it | `/plugin install session@smorinlabs-harness` |
| Dev symlink | You want to tweak/iterate | `git clone https://github.com/smorinlabs/smorinlabs-harness` then `ln -s "$(pwd)/smorinlabs-harness/plugins/session/skills/session-handoff" ~/.claude/skills/session-handoff` |
| Direct copy | No marketplace access | copy `plugins/session/skills/session-handoff/` into `~/.claude/skills/` |

**Codex:** register the marketplace in `~/.codex/config.toml`
(`[marketplaces.smorinlabs-harness]`) and enable the plugin — or use the
dev-symlink path, also linking into `~/.agents/skills` (Codex's current
skills location).

## Example session

> "Wrap this up — I want to finish it on my laptop tomorrow. Hand it off."
> → Scopes: infers the goal ("finish the session-handoff skill and merge it"),
> shows it, confirms. Gathers: transcript digest, repo identity (origin, branch
> `feat/session-handoff` @ SHA), portability preflight — flags **2 unpushed
> commits** ("push or they won't exist on your laptop"). Composes the handoff
> filtered to that goal, with the plan doc and PR link as sources of truth and
> the "why we reuse the sibling script" decision under tacit context. It's
> involved, so it writes `docs/handoffs/2026-07-22-session-handoff.md` and prints
> the launch line — *Start a new session in the repo and paste: `Read
> <abs-path> and continue.`* — plus a reminder to commit the doc so it travels.
