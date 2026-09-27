# session-inventory — CLI interface spec

| | |
|---|---|
| **Binary** | `session-inventory` (lowercase, kebab-case — R1.4) |
| **Location** | `plugins/session/skills/session-agent-list/scripts/session-inventory` |
| **Profile** | Small-CLI, verb-first (Appendix A — criteria hold: 1 fixed command, single implicit resource "agent session", unlikely to grow; migration trigger: a second resource type ⇒ noun-verb in the next major) |
| **Tier** | minimal, plus the scripted-consumer rules (R4.2, R7.2, R7.8) |
| **Standard** | CLI Design Standard v1.4.14 |
| **Shape** | Single-file uv-shebang Python script (argparse), stdlib only |

Purpose: one read-only inventory of the agent sessions on this machine across
Claude Code, Codex, Muse, and OpenCode — identity, session name, spawn
directory, times, lineage, whether the session is running right now, and the
resume command a reader may safely run. The `session-agent-list` skill renders
cards from this output; judgment work (titles from turns, handoff evidence,
end-state classification) stays with the skill.

## Command tree

| Command | Purpose | Exit on "nothing" |
|---|---|---|
| `list` | Enumerate sessions from every selected tool, newest activity first | `0` — an empty set is success (R6.2) |

Bare `session-inventory` prints help to stdout and exits `0` (R7.9). `list` is
a core verb (R2.1).

## Flags

Global:

| Long | Short | Type | Default | Notes |
|---|---|---|---|---|
| `--help` | `-h` | flag | — | stdout, exit 0 (R4.1) |
| `--version` | `-V` | flag | — | stdout, exit 0 (R4.1) |
| `--output` | `-o` | enum `text\|json` | `text` | machine output (R4.2) |
| `--json` | — | flag | — | ≡ `-o json` (R4.2) |

`list`:

| Long | Type | Default | Notes |
|---|---|---|---|
| `--tool` | enum `claude\|codex\|muse\|opencode`, repeatable | all four | restrict to these tools (R3.7) |
| `--live` | flag | off | only sessions that may be running: `live` is `yes`, or `unknown` (rendered `live?`) |
| `--since` | `<n>m\|h\|d\|w` or ISO date | none | only sessions updated at or after this point |
| `--include-subagents` | flag | off | also list subagent and guardian threads (hidden by default, always counted in the census) |

`--` terminator honored; no command reads stdin, so `-` has no file role
(R3.1/R3.2 N/A). No credential flags exist (R5.5).

## Sources

Paths honor `HOME`; Codex honors `CODEX_HOME`; Muse and OpenCode honor
`XDG_DATA_HOME` (default `~/.local/share`). A tool whose store is absent is
reported as `absent`, not as an error. SQLite stores are opened read-only
(`mode=ro` URI) and never written.

| Tool | Sessions | Name | Title | Liveness signal |
|---|---|---|---|---|
| `claude` | `~/.claude/projects/*/<uuid>.jsonl` (top level only; sidecar dirs skipped) | last `custom-title` record (`/rename`) | last `ai-title` record | `~/.claude/sessions/<pid>.json` registry: PID alive **and** its UTC start time equals `procStart` |
| `codex` | `$CODEX_HOME/sessions/YYYY/MM/DD/rollout-*.jsonl` | `thread_name` in `$CODEX_HOME/session_index.jsonl` | — | `$CODEX_HOME/thread-writer-locks/<uuid>.lock` held open by a process (one `lsof` call) |
| `muse` | `session-index.db` table `sessions` | canonical claim in `session-names.db` (see below), else `session_name` | `title` | `<session_dir>/.session.lock`: same host, PID alive, process is `muse` or its versioned `muse-bin-*` binary |
| `opencode` | `opencode.db` table `session` | `slug` | `title` | a running `opencode` process: `--session <id>` in its argv, else its working directory (see `opencode_directory_liveness`) |

Hidden by default (counted as `hidden_subagents`): Codex threads whose
`thread_source` is `subagent` or `guardian_review`; OpenCode sessions with a
`parent_id`. Codex `forked_from_id` is a user fork — listed, with lineage.

## Exit codes (R6.1)

| Code | Meaning here |
|---|---|
| `0` | Success, including an empty result. Individual transcripts that fail to parse are listed with `unreadable: true` and counted; they do not fail the run. |
| `1` | Partial failure (R6.3): a store exists but could not be read (locked, corrupt, or an unexpected schema). The other tools' sessions are still printed; the failed source is named. |
| `2` | Usage error (unknown flag, bad `--since`, unknown `--tool`) |
| `130` | SIGINT |

## Output contract

Text (default): one line per session, stable tab-separated field order —
`tool  id  name  live  updated  spawn_dir  title`. After the sessions, one
`# census` line per selected tool (listed, hidden subagents, unreadable, live,
source status) — census is data, so it stays on stdout (R7.1). Absent fields
print `-`.

`--json` (R7.2 open-by-default, additive-only): one object

```json
{
  "sessions": [
    {
      "tool": "muse",
      "id": "01a0ca24-4bbc-7ec1-bd58-21281a1af2bf",
      "name": "copper-umbra",
      "name_resumable": true,
      "title": "can you look at the CI bottleneck issue",
      "spawn_dir": "/home/alex/c",
      "branch": null,
      "created": "2026-09-22T19:10:04Z",
      "updated": "2026-09-22T21:31:27Z",
      "transcript": "/home/alex/.local/share/muse/sessions/2026/09/22/01a0ca24-…/session.jsonl",
      "lineage": null,
      "archived": false,
      "unreadable": false,
      "live": "yes",
      "live_basis": "lock pid 23981 alive (muse)",
      "live_host": "cli",
      "pid": 23981,
      "tmux": null,
      "resume": null,
      "resume_by_name": null,
      "resume_blocked": "running",
      "export_command": "muse export --session 01a0ca24-4bbc-7ec1-bd58-21281a1af2bf"
    }
  ],
  "census": {"muse": {"listed": 146, "hidden_subagents": 0, "unreadable": 0, "live": 6}},
  "sources": {"muse": {"status": "ok", "path": "/home/alex/.local/share/muse/session-index.db"}}
}
```

- `live` is `yes`, `no`, or `unknown`; `live_basis` states the evidence.
  `live_host` is `cli` (a terminal session) or `app-server` (a Codex thread
  loaded in an IDE, desktop-app, or companion-plugin host), `null` when not live.
- `transcript` is the session file; OpenCode has none (`null`) and instead
  carries `export_command`. Muse also carries `export_command`.
- Muse names come from `~/Library/Application Support/Muse/session-name-authority/session-names.db`
  (`kind = 'canonical'` claims), falling back to the index's `session_name`
  column, which is only a projection and can be empty.
- The census `live` count covers listed sessions only (hidden subagents excluded).
- `lineage` is `null` or `{"kind": "fork"|"subagent", "parent_id": "…"}`.
- `resume` is `null` whenever `resume_blocked` is set: `running` (resuming a
  running session puts two writers on one transcript) or `no_workspace` (the
  tool recorded no directory to resume from).
- Sort: `updated` descending, then `tool`, then `id` (deterministic).
- Times are UTC ISO 8601 with a `Z` suffix; paths are absolute.

Errors under `--json` are a single object on stderr (R7.8):
`{"error": {"code": "source_unreadable", "message": "…", "sources": ["muse"]}}`.
Code: `source_unreadable`. Usage errors (exit `2`) are argparse's plain-text
usage message on stderr, not a JSON object.
