# session-status

The mid-flight glance of the session quintet: a fast, plain-language
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

When the work calls for it, the ledger carries an **ASCII kanban board** of
what's left. The skill decides each run: it draws one when two or more
pieces of work move in parallel, five or more items remain, or stated
dependencies decide the order — and skips it for a short sequential
remainder. Columns come from the plan's own status words when it tracks
real stages (PROJECTS.md `[~]` / `[ ]` / `[?]` → IN PROGRESS / SCOPED /
IDEAS), otherwise `NOW │ NEXT │ LATER │ BLOCKED`. Parallel work renders as
swimlanes; done work is one rolled-up line under the board, never a column.
"board" forces it on; "brief" or "no board" turns it off.

**Triggers on:** manual invocation only — `/session-status`, "session
status", "status check", "give me a status", "how far along are we",
"show what's left as a board", said mid-work about the active task. Never
ambiently: "where was I" / "catch me up" / a cold return is
`session-recap`; "any loose ends?" is `session-loose-ends`; "what should I work on?" is `project-next`.
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
> groups), reads statuses from the plan plus the conversation, and — with
> five items left — renders the medium-tier ledger with a board: the
> remaining work drawn as `NOW │ NEXT │ LATER │ BLOCKED` columns (T11
> blocked, waiting on T12's undo plan), finished work rolled up to one line
> under it (`✅ Done, rolled up: 7 — the token system (T01–T04), and the
> checks on each request (T05–T07)`), then each NOW and NEXT card spelled
> out in plain words (`🔄 T08 — renewing tokens quietly before they expire.
> One open edge case: two tabs renewing at the same moment.`).
> Footer: `7 done · 1 in progress · 4 left — from PROJECTS.md P21. Next:
> T09 — the switchover is untouched and it's the risky one.` No probes, no
> mutations — one ledger, then back to work.
