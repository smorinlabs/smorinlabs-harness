# pr-merge-flow

Drives an open GitHub PR through evidence-based review, verified repairs, and
merge readiness. It waits a bounded few minutes for reviewer bots, collects
all unresolved threads, and checks each claim locally where feasible. A bot
comment is a claim to investigate; failure to reproduce alone does not refute
it.

`pr-merge-flow` owns review dispositions and merge mode. It delegates failing
CI to `ci-fix` and uses the same
[repair validation contract](../../plugins/repo-hygiene/skills/ci-fix/references/validation-contract.md).
A confirmed, small in-scope bug above the value floor receives a minimal fix,
post-edit verification, a commit and push, then a reply naming the actual fix
commit and evidence before resolution. Targeted tests must run the intended
tests; exit 0 with no matching tests is insufficient. When local execution is
unavailable, the thread stays open until appropriate remote evidence supports
the repair, and the reply states the local limitation.

Verification starts with the failing scenario and affected checks. A complete
appropriate local validation bundle measured at approximately 30 seconds or
less can run directly. A single fast job does not establish that the bundle
is fast. Compatible fixes can be batched, and passing results can be reused
while the tested source and relevant execution inputs remain unchanged.
Unrelated action-version and hook audits are not prerequisites for a bot fix.

Scope and value remain separate from evidence. Valid work outside the PR's
goal is deferred to a created tracker item, with its reference in the reply.
Below-floor asks are declined with a reason. False or convention-conflicting
claims are refuted with evidence. Architectural redesigns are escalated to
the user and remain open, holding the merge. Human-authored refutations retain
their user gate.

The thread ledger is keyed by the top comment's `id`. It retains evidence and
reply IDs for each **disposition round**, meaning one investigation through
reply and confirmed resolution. A current authoritative reopen starts a new
round, even when the same comment ID was previously marked resolved. Cosmetic
edits, line movement, and unrelated pushes do not restart old investigations.
A failed resolve retries resolution only; an older round's reply does not
suppress a needed reply after a reopen.

The transitions below prevent stale evidence from becoming merge readiness:

| Event | Next action |
|---|---|
| A repair push changes the PR head, including a `ci-fix` repair | Wait for bots, refresh review collection, then return to merge preflight. |
| A CI rerun leaves the head unchanged | Refresh relevant CI and authoritative review state. Handle new or reopened threads without repeating completed repairs. |
| A required check is absent or pending | Report incomplete evidence; do not treat the observed green subset as complete CI. |
| A head change occurs after preflight | Refresh affected evidence. `--match-head-commit`, the merge guard, rejects a request targeting a different commit. |
| `--one-pass` finishes its one triage pass | Refresh for reporting only; name late or reopened findings as open and never merge. |

Review cycles keep their existing limits: measure findings received per
reviewer wave, with the bar ratcheting at cycle 3, non-decreasing same-bot
counts, or a wave mostly targeting review-added code. Four cycles, or two
successive ratchet waves, trigger the check-in. Its endings are continuation
under a 10-minute wall clock, merge with tracked deferrals, or pause for
redesign. Internal CI diagnostic pushes are not separate completed PR review
cycles. Automatic mode honors existing commit/push authority and downgrades
to a ready-report when a required owner decision or hold prevents progress.

All polling remains quota-safe: rate-limit preflight, 20–30-second intervals,
and bounded waits with one manual recheck on expiry. GraphQL reads thread
resolution state at collection and the final merge gate, and performs resolve
mutations; it is never polled. The gated browser fallback remains available
when GraphQL is exhausted. REST supplies comment IDs, the browser confirms
the PR identity and anchors to each `#discussion_r<id>`, and each resolution
is verified on that thread. Its existing browser consent gate and ephemeral
screenshot policy remain in effect, including in automatic mode.

Before a permitted merge, the skill refreshes the current head and review
state, verifies applicable CI coverage and owner holds, checks the title
against repo conventions, and binds the merge to the reviewed commit. After
a successful merge, it surveys branches, worktrees, dirty state, and possible
local default-branch synchronization. Cleanup and synchronization execute only
when specifically authorized. Dirty state is reported and preserved, and a
permitted synchronization is guarded and fast-forward-only.

The [validation scenarios](../../plugins/repo-hygiene/skills/pr-merge-flow/references/validation-scenarios.md)
trace these instruction-level transitions without posting comments, dispatching
CI, or merging a PR.

**Triggers on:** "merge this PR", "get PR #N merged", "resolve the PR
comments", "address review feedback and merge", "close out this PR", "babysit
the PR"

**Arguments:** `--auto` (merge when clean, no questions) · `--confirm` (final
merge gate; the default) · `--ready` (prepare everything, you merge) ·
`--one-pass` (one triage/fix pass over the threads present — skips the
re-review cycle and always ends as a ready-report, never merging; composes
with any mode) · `--deep` (opt-in deep review via `/code-review`, a Codex
adversarial pass, or the pr-review-toolkit agents). Precedence: invocation flag or plain ask >
`.claude/pr-merge-flow.local.md` (git-ignored per-repo preferences: `mode`,
`deep-review`, `merge-method`, `delete-branch`, `cycle-bound`,
`continue-until-clean`, `defer-target`) > default (confirm, no deep).
Every run opens with an arming line naming the resolved mode, its source,
and what it authorizes. `mode: auto` read from the prefs file asks a
one-line arming confirmation each run (an explicit `--auto` flag never
does — that is current consent, and scheduled runs pass the flag). A prefs
file that is tracked by git arrived with the repo, not from you: its
authority keys (`mode`, `merge-method`, `delete-branch`) are ignored with
a warning.

## Install

| Mode | When | How |
|---|---|---|
| Plugin (recommended) | You just want to use it | `/plugin install repo-hygiene@smorinlabs-harness` |
| Dev symlink | You want to tweak/iterate | `git clone https://github.com/smorinlabs/smorinlabs-harness` then `ln -s "$(pwd)/smorinlabs-harness/plugins/repo-hygiene/skills/pr-merge-flow" ~/.claude/skills/pr-merge-flow` |
| Direct copy | No marketplace access | copy both `plugins/repo-hygiene/skills/pr-merge-flow/` and `plugins/repo-hygiene/skills/ci-fix/` into `~/.claude/skills/`; keep them as siblings for the shared validation references |

**Codex:** register the marketplace in `~/.codex/config.toml`
(`[marketplaces.smorinlabs-harness]`) and enable the plugin — or use the
dev-symlink path, also linking into `~/.agents/skills` (Codex's current
skills location).

## Example session

> Get PR #42 merged — resolve whatever the bots found.
> → Reads `.claude/pr-merge-flow.local.md` (none → confirm mode), waits up to
> ~5 minutes polling every 30s for pending bot reviews, collects 7 unresolved
> threads, verifies each claim (running the failing case where feasible),
> fixes 5, reruns each reproducer with intended-test evidence, and checks the
> affected behavior. It batches compatible repairs into verified commits,
> pushes, replies with the fix SHAs and evidence, refutes 2 with concrete
> reasons, and resolves all 7. It waits out one re-review cycle, confirms
> required CI coverage for the current head and the title
> `feat(api): add rate limiter`,
> then presents the final gate: **Merge now (squash)** / Run deep review
> first / Don't merge. After approval it refreshes the head and threads,
> then merges with `--match-head-commit` bound to the reviewed SHA. The cleanup
> survey lists
> `git branch -d feat/rate-limiter` and one stale worktree as needs-cleanup
> (the remote branch was auto-deleted — already clean); nothing runs until
> selected.
