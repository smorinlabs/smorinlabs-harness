# session-loose-ends

The acting sibling of `session-recap`: instead of the full orientation story,
it sweeps the session for what's dangling and cleans it up with per-item
consent. Four evidence classes: working-state artifacts (uncommitted/unpushed
work, stashes, stale worktrees, scratch files), running or zombie processes
(uncollected background tasks, lingering Codex companion jobs, stale watch
loops), promises made in the conversation but never done, and light
project-tracking drift (stalled `[~]` rows, work never checked off — deep
drift hands off to `project-audit`). Every finding is reported with its
evidence and a recommendation in three directions — 🟢 Clean now (with why it's
safe), 🟡 Not yet — gated on <what> (with what gates it), or 🔒 Keep (with why it should survive) — then confirmed one at a time
via the `question-walkthrough` engine, executed, and verified ("no change" is
a failure to investigate, never success).

Findings are *gathered* by evidence source but *reported* by what's owed, in
four ID'd sections split by whether the skill can act: 🧹 cleanup pending and
📌 committed-but-not-done feed the per-item walkthrough, while ❓ decisions
pending and 💡 suggested-but-not-committed are printed report-only — each with
a real recommendation and a copy-pasteable handoff (`question-walkthrough`,
`project-add`), because the skill can't decide for the user or accept its own
suggestions, and dropping them is how they evaporate. 📌 versus 💡 is settled
by the record, not by merit: no quotable assent means it's a suggestion. IDs
(`C1`, `W2`, `D1`, `S3`) double as reply shorthand — `C1 C2 yes, W1 skip` —
and the close-out table accounts for every one of them.

**Triggers on:** "any loose ends?", "anything to clean up?", "what's dangling
here?", "tie this off", returning to a thread wanting only the actionable
state. Not "catch me up" (that's `session-recap`, which stays read-only).
**Arguments:** none.

## Install

| Mode | When | How |
|---|---|---|
| Plugin (recommended) | You just want to use it | `/plugin install session@smorinlabs-harness` |
| Dev symlink | You want to tweak/iterate | `git clone https://github.com/smorinlabs/smorinlabs-harness` then `ln -s "$(pwd)/smorinlabs-harness/plugins/session/skills/session-loose-ends" ~/.claude/skills/session-loose-ends` |
| Direct copy | No marketplace access | copy `plugins/session/skills/session-loose-ends/` into `~/.claude/skills/` |

**Codex:** register the marketplace in `~/.codex/config.toml`
(`[marketplaces.smorinlabs-harness]`) and enable the plugin — or use the
dev-symlink path, also linking into `~/.agents/skills` (Codex's current
skills location).

## Example session

> "Back on this thread — any loose ends?"
> → Sweep finds: 2 uncommitted files (evidence: `git status`), 1 zombie Codex
> job (evidence: `status` sweep), 1 promise ("I'll add the test later" —
> never done), PROJECTS row `[~]` for shipped work, 1 unanswered design
> question, 1 idea floated and never taken up. Reports them as C1–C3 / W1 /
> D1 / S1: cancel the zombie (🟢), keep the dirty experiment file (🔒
> mid-experiment), flip the row (🟢) — then D1 and S1 print report-only with
> `▶ Prompt` to settle decisions and capture ideas. Walks the actionable
> IDs, executes approvals, verifies, closes with every ID accounted for.
