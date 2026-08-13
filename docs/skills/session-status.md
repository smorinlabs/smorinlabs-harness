# session-status

The mid-flight glance of the session quartet: a fast, plain-language
"you are here" map of the ACTIVE stream of work — what it is, what's done,
what's in progress, and what's left — rendered as a ledger (`The work` /
`Done` / `Now` / `Left` label column, counts footer) at the zoom level the
work's own structure picks. A flat five-task list renders every task as a
plain sentence with its ID; phased multi-level work opens with a big-picture
map naming every phase, then zooms — heavy detail only on what's left in the
current phase, one line each for the others.

Two laws govern every line. **Plain language, always:** each item says what
the thing *is* in ordinary words a reader outside the session could act on —
IDs annotate, task titles are translated, never echoed. **Asymmetric
detail:** done work rolls up (tasks → counts → phase names) while what's left
stays fine-grained, but only where you're standing. Read-only *and*
probe-free — status comes from the plan of record (PROJECTS.md, projects/,
task lists, plan docs) plus the conversation; it never runs tests or probes
git/PR/CI, which is what keeps it a glance instead of a recap. No owed-item
tables, no launch prompts, no verdict — that machinery belongs to
`session-recap`.

**Triggers on:** manual invocation only — `/session-status`, "session
status", "status check", "give me a status", "how far along are we", said
mid-work about the active task. Never ambiently: "where was I" / "catch me
up" / a cold return is `session-recap`; "any loose ends?" is
`session-loose-ends`; "what should I work on?" is `project-next`.
**Arguments:** none.

## Install

| Mode | When | How |
|---|---|---|
| Plugin (recommended) | You just want to use it | `/plugin install session@smorinlabs-harness` |
| Dev symlink | You want to tweak/iterate | `git clone https://github.com/smorinlabs/smorinlabs-harness` then `ln -s "$(pwd)/smorinlabs-harness/plugins/session/skills/session-status" ~/.claude/skills/session-status` |
| Direct copy | No marketplace access | copy `plugins/session/skills/session-status/` into `~/.claude/skills/` |

**Codex:** register the marketplace in `~/.codex/config.toml`
(`[marketplaces.smorinlabs-harness]`) and enable the plugin — or use the
dev-symlink path, also linking into `~/.agents/skills` (Codex's current
skills location).

## Example session

> Mid-build, the user types `/session-status`.
> → The skill finds the plan of record (PROJECTS.md P21, 12 tasks in 3
> groups), reads statuses from the plan plus the conversation, and renders
> the medium-tier ledger: the token-system group rolled up to `✅ T01–T04 —
> the token system itself: creating, signing, and storing them`, the live
> task spelled out with its sticking point (`🔄 T08 — renewing tokens
> quietly before they expire; open edge case: two tabs renewing at once`),
> and the untouched switchover group itemized task by task in plain words.
> Footer: `7 done · 1 in progress · 4 left — from PROJECTS.md P21. Next:
> T09 — the switchover is untouched and it's the risky one.` No probes, no
> mutations — one ledger, then back to work.
