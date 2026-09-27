---
name: session-agent-list
allowed-tools: Read, Glob, Grep, Bash
argument-hint: "[query] [--tool <name>] [--live] [--compact|--exec|--ledger]"
arguments: [query]
description: List Claude Code, Codex, Muse, and OpenCode sessions on this machine as action-ready cards with resume commands, filterable by tool and by what is running now. Use when the user asks to list, find, or resume a past session, which sessions touched a repo, or which sessions are in use. Not for orienting inside the current session (session-recap).
---

# session-agent-list

Find Claude Code, Codex, Muse, and OpenCode sessions on this machine and
render them in the canonical card format — so the user can triage by end
state, see what is running, get back into a session, or read what it did.

## Contract

- **Read-only.** Discover, classify, render. Never resume a session, never
  delete or move a transcript, never write a handoff (that is
  `session-handoff`). Cleanup of what a card reveals routes to
  `session-loose-ends`.
- **The card changes which actions it hands you.** An open session leads with
  its resume command; a handed-off session leads with the handoff doc and
  annotates resume as "usually wrong"; a closed session offers only its
  transcript; a session running right now gets no resume command at all —
  it names where it runs. Never print a resume command a reader shouldn't run.
- **Ephemeral ordinals are stable within the conversation.** Once a session is
  `[3]` it stays `[3]` across re-filters and re-listings; new finds keep
  counting up; filtered-out sessions leave gaps. "Open [3]" must always be
  safe. Ordinals are never stored beyond the conversation.
- **Render exactly to `references/format-spec.md`.** The 22 elements, glyph
  budget, delimiter ladder, and card anatomy are converged design — modes
  reorder or drop fields, never invent them, and the spec's "do not regress"
  list is binding.

## Workflow

1. **Scope.** From the invocation (`[query]`) and conversation, derive the
   filter: time window, tool (`--tool`, or "my Muse sessions"), running now
   (`--live`, or "what's in use"), repo/topic, or free text. No query →
   recent sessions across all four tools. The flags pick the view: none → **full cards,
   together** (the default listing), `--compact` → orientation-compact
   triage, `--exec` → respawn console, `--ledger` → what-it-did ledger (all
   defined in the spec).
2. **Discover.** Run `session-inventory list --json` (see *Data sources*)
   with the scope's `--tool`, `--live`, and `--since`. It returns every
   session's ID, name, spawn dir, times, lineage, liveness, transcript path,
   and the resume command safe to show, plus a per-tool census. Filter to
   scope before reading anything deeply — read transcript heads/tails, not
   whole transcripts, and only for sessions that survive the filter.
3. **Extract per session:** title (the inventory's `title` where present;
   otherwise generate one from the first user turn plus the tail — never
   render an untitled card), repos and worktrees touched, handoff in/out
   evidence, and the work item / milestone when the transcript names one
   (triple form — never a bare ID). Take spawn dir, name, lineage, liveness,
   and commands from the inventory; never rebuild them by hand.
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

One read-only CLI ships inside this skill and reads all four stores. Resolve
it in this order and reuse the result for the whole session:

```bash
SI="$(command -v session-inventory || true)"                      # 1. explicit PATH install, if any
[ -x "$SI" ] || SI="<skill-base>/scripts/session-inventory"       # 2. base dir announced when this skill loaded
if [ ! -x "$SI" ]; then                                           # 3. well-known placements
  for d in "$HOME/.claude/skills/session-agent-list" "$HOME/.agents/skills/session-agent-list"; do
    [ -x "$d/scripts/session-inventory" ] && SI="$d/scripts/session-inventory" && break
  done
fi
"$SI" list --json --tool muse --live
```

No `uv` on the machine? `python3 "$SI" ...` works identically (stdlib only,
Python ≥3.11). Interface: `docs/session-inventory-cli.md` in the session
plugin.

| Tool | Store the CLI reads | Resume (by UUID) | Name source |
|---|---|---|---|
| Claude Code | `~/.claude/projects/<cwd-slug>/<uuid>.jsonl` | `cd <spawn-dir> && claude --resume <uuid>` | `/rename` title |
| Codex | `$CODEX_HOME/sessions/YYYY/MM/DD/rollout-*.jsonl` (default `~/.codex`) | `codex resume <uuid>` | thread name (also resumable) |
| Muse | `~/.local/share/muse/session-index.db` + per-session dirs | `cd <workspace> && muse resume <uuid>` | canonical name (also resumable) |
| OpenCode | `~/.local/share/opencode/opencode.db` | `cd <dir> && opencode --session <id>` | slug |

- **Liveness** (`live`: `yes` / `no` / `unknown`, with `live_basis`) comes
  from each tool's own evidence: Claude Code's `~/.claude/sessions/<pid>.json`
  registry (PID alive and start time matching), Codex writer locks held open,
  Muse `.session.lock` whose PID is a running `muse`, and OpenCode processes.
  A lock file alone never means running — stale locks are common.
- **Subagent and guardian threads** (Codex, OpenCode) are hidden by default
  and counted in `census.<tool>.hidden_subagents`; report the count in the
  coverage footer. `--include-subagents` lists them.
- A transcript that fails to parse is listed with `unreadable: true` and
  counted, never silently dropped. Exit `1` means a whole store could not be
  read: render what came back and name the failed source in the footer.
- Rendered cards always show resolved paths, never `$CODEX_HOME` or other
  variables.

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
| "The lock file is there, so it's running" | Locks outlive their process. Trust the inventory's `live` verdict and show its basis; `unknown` never renders as running. |
| "The name is friendlier — resume by name" | The UUID is exact and never collides. Resume by UUID; the name rides along on the identity line and as an extra by-name line. |
| "I'll just list the directories myself" | The inventory resolves names, liveness, subagents, and safe commands. Hand-rolled discovery drifts from it. |

## See also

- `references/format-spec.md` — the binding output format (21 elements,
  glyphs, taxonomy, anatomy, golden example, projections).
- `session-recap` — orientation *inside* the current session; this skill finds
  sessions *across* the machine.
- `session-handoff` — writes the handoff docs whose lineage (⇤/⇥) this skill
  only reads.
- `session-loose-ends` — acts on the loose ends a `◒` card reveals.
