# CLI Standard Conformance — dependabot-sweep (`scripts/sweep_cli.py`)

| | |
|---|---|
| **Standard** | CLI Design Standard v1.4.14 |
| **Profile** | Standard (noun-verb) |
| **Tier** | minimal |
| **Owner** | Steve Morin |

## Applicability

| Axis | Applies | Reason if N/A |
|---|---|---|
| Config (§5) | yes | — |
| Networked (§10) | yes | read-only `pr observe`; merges are the worker transport's |
| Destructive ops (§8) | no | no command deletes or mutates GitHub; the store is append-only |
| Scripted consumers (R7.2/R7.8) | yes | — |
| Async / long-running | no | every command returns after bounded reads; waits are the skill's, per pr-merge-flow `references/polling.md` |
| Streaming / watch | no | no `--follow`/`--watch`; `attempt collect` reads JSON lines as input only |
| Plugins (R9.11) | no | none |
| Caching / offline (R5.9) | no | nothing cached; the store is the run's record, not a cache |
| Secrets handled (R5.5/R5.6) | yes | token from env or `gh auth token`; never printed |

## Waived SHOULDs

| Rule | Deviation | Rationale | Owner / date |
|---|---|---|---|
| R2.1 | Domain verbs `observe`, `evaluate`, `collect`, `reconcile`, `finish`, `discover`, `refresh`, `record` | No core verb fits: they name the sweep's own stages (retrospective vocabulary R01/R07); `describe` and `view` are used where they fit | Steve Morin / 2026-09-22 |
| R5.2 | Config file is `~/.config/dependabot-sweep/config.toml`, not `dependabot-sweep_config.toml`; no project-local discovery | Existing users and `references/config.md` document this path; `XDG_CONFIG_HOME`, `--config`, and `DEPENDABOT_SWEEP_CONFIG` are honored | Steve Morin / 2026-09-22 |
| R1.5 | Invoked as `python3 scripts/sweep_cli.py`, not an installed `dependabot-sweep` binary | Internal helper shipped inside the skill; `prog` is `dependabot-sweep` so help and errors read as the standard expects | Steve Morin / 2026-09-22 |
| R10.1 | No `auth login/logout/status` group | Credentials belong to `gh`; the CLI consumes `GH_MERGE_TOKEN` or `gh auth token`, the helper's own precedence | Steve Morin / 2026-09-22 |
| R10.7 | No retry or backoff on rate-limit responses | A rate-limited section is recorded unreadable and the evaluator holds (K13); waits are governed by the skill's polling rules, never by this CLI | Steve Morin / 2026-09-22 |
| R5.7 | No `config view --show-origin` | `run view` prints the stored authority; value origins are recorded on `RunConfig.origin` for a later command | Steve Morin / 2026-09-22 |

## Audit history

| Date | Standard version | Mode | Result |
|---|---|---|---|
| 2026-09-22 | 1.4.14 | plan | interface spec written; minimal-tier MUSTs covered by `tests/test_sweep_slice4.py` (help/version to stdout, usage exit 2, no prefix abbreviation, JSON error schema, exit 3/4/130); no live audit yet |

The 0.18.0 additions preserve the same minimal-tier contract. Inventory and
follow-up commands mutate only the local append-only journal. `run describe
--save` writes one report snapshot atomically and emits the same readable
text; JSON embeds that text in `report`. Focused CLI tests cover report identity,
journal-path protection, structured write failures, follow-up replay, bounded
admission and read-only refresh. There are no new GitHub write commands.
