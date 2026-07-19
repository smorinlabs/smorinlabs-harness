# question-walkthrough

Turns a pile of undecided things into a sequence of single, well-framed
decisions. It gathers open questions from one of four sources — mined from the
current conversation, read from a document you point at, given inline, or
pulled from task systems — confirms the pile with you, sequences it by
leverage (questions whose answers could moot or reshape others go first), then
walks it one AskUserQuestion at a time with just-enough anchored context per
item (the explain skill's anatomy). Its defining move: after **every** answer
the remaining pile is re-planned — mooted questions dropped loudly, order
revised, implied follow-ups added only with consent. Decisions are recorded
back at their source (document edits beside the question, task updates) and
the walk ends in an outcome table with parked items called out.

**Triggers on:** "go through these one by one", "walk me through the open
questions", "there's a bunch of to-dos, help me decide", "triage these
decisions with me", a doc or plan blocked on several unanswered questions.
**Arguments:** optional source hint (a doc path, "from this conversation", an
inline list).

## Install

| Mode | When | How |
|---|---|---|
| Plugin (recommended) | You just want to use it | `/plugin install question-walkthrough@smorinlabs-harness` |
| Dev symlink | You want to tweak/iterate | `git clone https://github.com/smorinlabs/smorinlabs-harness` then `ln -s "$(pwd)/smorinlabs-harness/plugins/question-walkthrough/skills/question-walkthrough" ~/.claude/skills/question-walkthrough` |
| Direct copy | No marketplace access | copy `plugins/question-walkthrough/skills/question-walkthrough/` into `~/.claude/skills/` |

**Codex:** register the marketplace in `~/.codex/config.toml`
(`[marketplaces.smorinlabs-harness]`) and enable the plugin — or use the
dev-symlink path, also linking into `~/.agents/skills` (Codex's current
skills location).

## Example session

> "This design doc has six open questions — walk me through them"
> → The skill lists the six for confirmation, opens with the architecture
> question whose answer would moot two others, presents it with a
> recommendation and trade-offs, drops the two mooted questions (saying why)
> after the answer, walks the survivors, writes each decision into the doc,
> and closes with a 6-row outcome table (4 decided, 2 dropped).
