# session-agent-list

The finder of the session quintet: discovers Claude Code, Codex, Muse, and
OpenCode sessions across the machine and renders them as action-ready cards
in a converged 22-element format — ephemeral ordinals (`[1]`, stable within the
conversation), end-state triage on its own line (`●` open mid-work / `⇥`
handed off / `✔` closed clean / `◒` closed with loose ends), the working set
(spawn dir, repos, ⑂ worktrees — multi-repo is first-class), lineage (↳ forks,
⇤/⇥ handoff in/out — a written-but-unread handoff shows as "baton in the
air"), a three-horizon story (Lately = hours, TLDR = session, longer arc =
months), each tool's own session name beside the UUID (Muse `copper-umbra`,
Codex thread name, Claude Code `/rename` title, OpenCode slug), and
copy-paste commands. The card changes which actions it hands you: open
sessions lead with `cd <spawn-dir> && claude --resume <uuid>` (or `codex
resume <uuid>`, `muse resume <uuid>`, `opencode --session <id>`),
handed-off sessions lead with the handoff doc, closed sessions get
transcript-only, and a session running right now (`live`) gets no resume
command at all — it names the PID and tmux pane where it runs. Listings open with an end-state census, split
into age bands when the results span months, and group by shared milestone —
work items always in triple form (ID + plain name + one-line definition),
never bare.

One canonical card, four views: **the default listing renders full cards,
together** — every found session complete, under the band/group/card
delimiter ladder — while three flag modes reshape it: `--compact` (~3 lines
per session for triaging large sets, with binding compact-discipline rules),
`--exec` (a respawn console of runnable blocks), and `--ledger` (what-it-did
view, working set and narrative leading). In compact mode, "show me [3]"
drills into the full card without renumbering. Read-only by
contract: it never resumes, deletes, or writes — cleanup a `◒` card reveals
routes to `session-loose-ends`. Discovery runs through the bundled
read-only `scripts/session-inventory` CLI (stdlib Python; interface in the
plugin's `docs/session-inventory-cli.md`), which resolves names, liveness,
hidden subagent threads, and safe commands for all four tools. The binding
format spec (glyph budget,
delimiter ladder, card anatomy, golden example) lives in the skill's
`references/format-spec.md`.

**Triggers on:** "list my sessions", "find that session", "which sessions are
open", "what other sessions touched this repo", "find the session where I did
X", "show my Codex sessions", "list my Muse sessions", "what's running
right now", or any ask for a resume command for a past session. NOT orientation inside the current session (`session-recap`), not
active-stream progress (`session-status`), not cleanup (`session-loose-ends`),
not writing handoffs (`session-handoff`).
**Arguments:** `[query] [--tool <name>] [--live] [--compact|--exec|--ledger]`
— an optional free-text/time/repo filter, a tool filter (`claude`, `codex`,
`muse`, `opencode`; repeatable), running-now only, plus the view flags.

## Install

| Mode | When | How |
|---|---|---|
| Plugin (recommended) | You just want to use it | `/plugin install session@smorinlabs-skills` |
| Dev symlink | You want to tweak/iterate | `git clone https://github.com/smorinlabs/smorinlabs-skills` then `ln -s "$(pwd)/smorinlabs-skills/plugins/session/skills/session-agent-list" ~/.claude/skills/session-agent-list` |
| Direct copy | No marketplace access | copy `plugins/session/skills/session-agent-list/` into `~/.claude/skills/` |

**Codex:** register the marketplace in `~/.codex/config.toml`
(`[marketplaces.smorinlabs-skills]`) and enable the plugin — or use the
dev-symlink path, also linking into `~/.agents/skills` (Codex's current
skills location). **Muse and OpenCode** both load skills from
`~/.agents/skills`, so the same dev symlink serves them.

## Example session

> "Which of my sessions are still open? I think one of them was mid-PR."
> → The skill runs `session-inventory list --json` across all four tools'
> stores, filters
> to recent activity, classifies each transcript tail, and renders the
> default listing headed `FOUND 4 SESSIONS · ● 1 open · ⇥ 1 handed off · ✔ 2
> clean` — every session as its full card, together. The one `●` card leads
> with its exact stopping point ("mid-draft of the PR body — sweep complete,
> PR not yet opened · ~90%") and a runnable `cd ~/c && claude --resume
> <uuid>`; the `⇥` card leads with its handoff doc path and flags the baton
> as not yet picked up. Add `--compact` to condense the same set to three
> lines per session for triage.
