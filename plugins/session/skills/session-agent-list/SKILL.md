---
name: session-agent-list
allowed-tools: Read, Glob, Grep, Bash
argument-hint: "[query] [--compact|--exec|--ledger]"
arguments: [query]
description: Find and list Claude Code and Codex sessions across this machine, rendered as action-ready cards — how long ago, open mid-work vs handed off vs closed (clean / loose ends), what each did (repos, worktrees, three-horizon story), lineage (forks, handoffs in/out), and copy-paste commands to resume or read the transcript. Closed sessions get transcript-only commands — the card changes which actions it hands you. Use when the user asks "list my sessions", "find that session", "which sessions are open", "what other sessions touched this repo", "find the session where I did X", "show my Codex sessions", or wants a resume command for a past session. Full cards by default; --compact condenses to a triage listing, --exec a respawn console, --ledger a what-it-did view. Cross-session discovery only — NOT orienting inside the current session (session-recap), not active-stream progress (session-status), not cleanup (session-loose-ends), not writing handoffs (session-handoff).
---

# session-agent-list

Find Claude Code and Codex sessions on this machine and render them in the
canonical card format — so the user can triage by end state, get back into a
session, or read what it did.

## Contract

- **Read-only.** Discover, classify, render. Never resume a session, never
  delete or move a transcript, never write a handoff (that is
  `session-handoff`). Cleanup of what a card reveals routes to
  `session-loose-ends`.
- **The card changes which actions it hands you.** An open session leads with
  its resume command; a handed-off session leads with the handoff doc and
  annotates resume as "usually wrong"; a closed session offers only its
  transcript. Never print a resume command a reader shouldn't run.
- **Ephemeral ordinals are stable within the conversation.** Once a session is
  `[3]` it stays `[3]` across re-filters and re-listings; new finds keep
  counting up; filtered-out sessions leave gaps. "Open [3]" must always be
  safe. Ordinals are never stored beyond the conversation.
- **Render exactly to `references/format-spec.md`.** The 21 elements, glyph
  budget, delimiter ladder, and card anatomy are converged design — modes
  reorder or drop fields, never invent them, and the spec's "do not regress"
  list is binding.

## Workflow

1. **Scope.** From the invocation (`[query]`) and conversation, derive the
   filter: time window, tool, repo/topic, or free text. No query → recent
   sessions across both tools. The flags pick the view: none → **full cards,
   together** (the default listing), `--compact` → orientation-compact
   triage, `--exec` → respawn console, `--ledger` → what-it-did ledger (all
   defined in the spec).
2. **Discover.** Enumerate session files from both tools' native layouts (see
   *Data sources*). File mtime approximates last activity; the first record's
   timestamp is the start. Filter to scope before reading anything deeply —
   read heads/tails, not whole transcripts, until a session survives the
   filter.
3. **Extract per session:** title (the tool's own summary records where
   present; otherwise generate one from the first user turn plus the tail —
   never render an untitled card), spawn directory, repos and worktrees
   touched, lineage (fork/child markers), handoff in/out evidence, and the
   work item / milestone when the transcript names one (triple form — never a
   bare ID).
4. **Classify end state** with the spec's detection signals: handoff write in
   the tail → `⇥`; merge + cleanup → `✔`; merge without cleanup → `◒`;
   otherwise `●` open. Conflicting signals → state the evidence on the card,
   never guess silently.
5. **Assign ordinals** (or reuse ones already issued this conversation), then
   **render** per the spec: listing header with end-state census, age bands
   only when the set spans them, groups by shared milestone/topic, lineage
   clusters keeping parents before children.
6. **Drill-down.** "Show me [n]" returns that session's full canonical card;
   follow-up filters re-render without renumbering.

## Data sources

- **Claude Code:** `~/.claude/projects/<cwd-slug>/<uuid>.jsonl` — one dir per
  spawn directory (the slug is the cwd with `/` → `-`), one JSONL per session.
  The spawn dir is part of the resume address: `cd <spawn-dir> && claude
  --resume <uuid>`.
- **Codex:** `$CODEX_HOME/sessions/YYYY/MM/DD/rollout-<timestamp>-<uuid>.jsonl`
  (default `~/.codex` when `CODEX_HOME` is unset — sandboxed environments
  relocate it) — keyed by date, not cwd. Resume with `codex resume <uuid>`.
  Rendered cards always show the resolved path, never the variable.
- Sidecar dirs and non-session files inside these trees are ignored; a
  transcript that fails to parse is reported as unreadable, never silently
  dropped from the census.

## Red Flags

| Thought | Reality |
|---------|---------|
| "A resume command on every card is convenient" | The card changes which actions it hands you. Closed → transcript only; handed off → the doc leads. |
| "Abbreviate the UUID, it appears three times" | Deliberate redundancy — identity line, resume command, file path each serve a different hand. Abbreviation is legal only in the ledger footer. |
| "The task ID is enough context" | Never a bare work-item ID — triple form: ID (plain name — one-line definition). |
| "This state needs a new glyph" | The glyph budget is strict: seven glyphs, one meaning each. A new glyph requires a removed one. |
| "Signals conflict — pick the likeliest state" | State the evidence on the card. A wrong `✔` hides a resume candidate; a wrong `●` invites resuming a finished thread. |
| "The user seems lost in *this* session" | That is `session-recap`. This skill fires for finding *other* sessions. |
| "The titles are long — I'll wrap line 1" | Compact's line 1 is fixed. Budget the title (ellipsize in compact); never change the layout. |
| "This evidence matters — I'll add a section under the listing" | No invented zones. Glyph + state word in compact; evidence renders on the full card. |

## See also

- `references/format-spec.md` — the binding output format (21 elements,
  glyphs, taxonomy, anatomy, golden example, projections).
- `session-recap` — orientation *inside* the current session; this skill finds
  sessions *across* the machine.
- `session-handoff` — writes the handoff docs whose lineage (⇤/⇥) this skill
  only reads.
- `session-loose-ends` — acts on the loose ends a `◒` card reveals.
