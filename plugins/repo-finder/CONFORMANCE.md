# CLI Standard Conformance — repo-finder

| | |
|---|---|
| **Standard** | CLI Design Standard v1.4.14 |
| **Profile** | Small-CLI (Appendix A) |
| **Tier** | minimal |
| **Owner** | Steve Morin |

## Applicability

| Axis | Applies | Reason if N/A |
|---|---|---|
| Config (§5) | yes | — |
| Networked (§10) | yes (subset) | auth/TLS/retries delegated to `gh`; only R10.3 pagination + R10.7 rate-limit visibility in play |
| Destructive ops (§8) | no | only mutation is `init` writing a new config file; overwrite gated by `--force` + exit `5` |
| Scripted consumers (R7.2/R7.8) | yes | primary consumer is an LLM agent; `-o json` + JSON error schema |
| Async / long-running | no | all operations synchronous, seconds-scale |
| Streaming / watch | no | no streams |
| Plugins (R9.11) | no | single-file tool |
| Caching / offline (R5.9) | no (v1) | cache is planned phase 2 (remote tier); R5.9 controls arrive with it |
| Secrets handled (R5.5/R5.6) | no | no credentials accepted or stored; GitHub auth lives in `gh` |

## Waived SHOULDs

| Rule | Deviation | Rationale | Owner / date |
|---|---|---|---|
| R4.4 | No `-v/-q/--debug` ladder | minimal tier, single-file tool; diagnostics are already terse and on stderr | Steve Morin / 2026-07-19 |
| R7.5 | Help has usage + command list but no worked example per subcommand | token-lean help; the skill body carries usage examples for the agent | Steve Morin / 2026-07-19 |
| R10.3 | `org` supports `--limit` (total cap, backend pages fetched as needed, truncation warned) but not the `--paginate`/`--page-size`/`--no-paginate` trio | bounded-by-default with an explicit cap meets the rule's intent; the full trio is oversized for a finder | Steve Morin / 2026-07-19 |

## Audit history

| Date | Standard version | Mode | Result |
|---|---|---|---|
| 2026-07-19 | 1.4.14 | plan | Interface spec seeded (`docs/cli-interface.md`); no code yet |
| 2026-07-19 | 1.4.14 | review | Field-feedback round (v0.2.0): degraded remote search now exits 1 per R6.3 (was silently reported as clean miss); `find` remote tier moved to server-side Search API filtering; enumeration pages to `--limit` per R10.3 with truncation warning; rate limits detected via `gh api rate_limit` per R10.7 (was stderr prose matching) |
