# session-recap

Reconstructs where a coding session stands when it's been left idle, compacted,
or reopened cold — or mid-session on request. Gathers the session arc from the
transcript (bundled digest script keyed on `$CLAUDE_CODE_SESSION_ID`), live
git/branch/worktree state, PR and CI via `gh`, each stream's plan-of-record
checklist, and what moved while you were away. Read-only — it gathers and
reports, never commits, pushes, cleans up, or edits files.

The report is a **Past → Worklist** story under labeled dividers: an opening
zone (cockpit line with a 🔴🔵🟡🟢⚪ state + reason, prose TL;DR, `⏸ Left off`
/ `👉 Start here`, a "since you left" delta, and a Context/Scope block), then
the PAST (narrative timeline, Done inventory, the 🗣 Discussed reasoning
trail), then the WORKLIST (impact-ordered: ❓ Decisions, 🔧 in-flight stream
blocks with plan-progress spines, 📌 Committed, 🧹 Cleanup, 💡 Ideas — every
owed row proof-backed with a stable reply-ID, every actionable table ending in
a self-contained, cold-pasteable `▶ Prompt`), closing with a verdict, the
critical path, and a reader-steps block. Output scales by zoom tier — a tiny
session collapses to a few lines; a multi-day one coarsens to milestones
(done work rolls up; blocked and remaining stay fine-grained).

**Triggers on:** "catch me up", "where was I", "where are we", "recap this
session", "what's the state of this", "what was I doing", "get me up to
speed", "did I finish", or returning to a repo after time away and seeming
unsure of the current state.
**Arguments:** none — depth adapts automatically (the former long-ledger flag is
now the long zoom tier).

## Install

| Mode | When | How |
|---|---|---|
| Plugin (recommended) | You just want to use it | `/plugin install session@smorinlabs-harness` |
| Dev symlink | You want to tweak/iterate | `git clone https://github.com/smorinlabs/smorinlabs-harness` then `ln -s "$(pwd)/smorinlabs-harness/plugins/session/skills/session-recap" ~/.claude/skills/session-recap` |
| Direct copy | No marketplace access | copy `plugins/session/skills/session-recap/` into `~/.claude/skills/` |

**Codex:** register the marketplace in `~/.codex/config.toml`
(`[marketplaces.smorinlabs-harness]`) and enable the plugin — or use the
dev-symlink path, also linking into `~/.agents/skills` (Codex's current
skills location).

## Example session

> "Where was I?"
> → digests the transcript, probes git/PR/CI and each stream's plan of record,
> classifies what's owed (1 decision, 1 committed item, 1 cleanup, 1 idea —
> each with its proof), and returns the two-zone recap: cockpit + TL;DR,
> timeline and Done, then the impact-ordered worklist with ▶ prompts,
> ending "🔴 Blocked — settle D1 first; critical path D1 → O1 → merge #212."
