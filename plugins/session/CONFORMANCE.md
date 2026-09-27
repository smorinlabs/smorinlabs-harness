# CLI Standard Conformance — session-inventory

Scope: the `session-inventory` script in the `session-agent-list` skill. The
other session skills ship no CLI.

| | |
|---|---|
| **Standard** | CLI Design Standard v1.4.14 |
| **Profile** | Small-CLI (Appendix A) |
| **Tier** | minimal |
| **Owner** | Steve Morin |

## Applicability

| Axis | Applies | Reason if N/A |
|---|---|---|
| Config (§5) | no | no config file; store locations come from the tools' own env vars (`HOME`, `CODEX_HOME`, `XDG_DATA_HOME`) |
| Networked (§10) | no | reads local files and SQLite only |
| Destructive ops (§8) | no | strictly read-only; SQLite opened with `mode=ro` |
| Scripted consumers (R7.2/R7.8) | yes | primary consumer is the `session-agent-list` agent; `-o json` + JSON error schema |
| Async / long-running | no | synchronous, seconds-scale |
| Streaming / watch | no | no streams |
| Plugins (R9.11) | no | single-file tool |
| Caching / offline (R5.9) | no | no cache |
| Secrets handled (R5.5/R5.6) | no | never reads `auth.json` or credential stores |

## Waived SHOULDs

| Rule | Deviation | Rationale | Owner / date |
|---|---|---|---|
| R4.4 | No `-v/-q/--debug` ladder | minimal tier, single-file tool; diagnostics are terse and on stderr | Steve Morin / 2026-09-22 |
| R7.5 | Help has usage and flags but no worked example | token-lean help; the skill body carries usage for the agent | Steve Morin / 2026-09-22 |

## Judgment calls

| Rule | Call | Rationale |
|---|---|---|
| R6.3 | A single transcript that fails to parse is listed as `unreadable` and counted, exit `0`; a whole store that fails is exit `1` | live sessions are appended to while being read, so a torn last line is routine; the skill contract already requires unreadable transcripts to be reported, never dropped |

## Audit history

| Date | Standard version | Mode | Result |
|---|---|---|---|
| 2026-09-22 | 1.4.14 | plan | Interface spec seeded (`docs/session-inventory-cli.md`); no code yet |
| 2026-09-22 | 1.4.14 | review | Implemented; 35 fixture tests cover R4.1 help/version, R6.1 exits 0/1/2, R7.1 split, R7.8 error object. Live run fixed two real-data gaps (Codex string `subagent` source; Muse versioned `muse-bin-*` binary) |
