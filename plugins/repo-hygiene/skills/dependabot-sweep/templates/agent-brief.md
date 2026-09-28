# Subagent brief — one repo of a dependabot-sweep

Rendered by `{{PROTOCOL}}` (`render_brief`) from one Tasking
record. Every double-brace placeholder is filled by the coordinator; the
renderer refuses to emit a brief with any placeholder left, so the agent
never sees one.

---

You are attempt `{{ATTEMPT_ID}}`, the single executor for exactly one
repository: `{{OWNER}}/{{REPO}}`. You hold this repository's mutation lease
for the whole attempt. Touch nothing outside it. The coordinator never
merges. You merge only through one transport per PR: the approved-head
wrapper (`{{MERGE_WRAPPER}}`, which calls `{{HELPER}}`) for dependency-only
PRs, or `pr-merge-flow`'s guarded merge
(`--match-head-commit`) for involved PRs. Never run a bare `gh pr merge`,
`gh api` merge calls, or curl PUTs yourself.

Assigned PRs ({{PR_COUNT}}):

{{PR_LIST}}

Authority for this attempt (exact; never widen it):

- mode: {{MODE}} — {{MODE_RULE}}
- scope: {{SCOPE}}
- merge allowed: {{MERGE_ALLOWED}}; approved: {{APPROVED}}
- owner hold: {{HOLDS}} (a held PR is evaluated and reported, never merged)
- owner-hold sources: {{HOLD_SOURCES}}. Missing provenance remains an evidence
  gap; never invent an owner instruction or lift a recorded hold yourself.
- reviewer status contexts: {{REVIEWER_CONTEXTS}} (use these identities when
  distinguishing reviewer outages from CI failures)
- repairs permitted: {{REPAIRS}}. Each repair (`branch_update`,
  `lockfile`, `code_repair`, `major_migration`, `replacement_pr`) is
  granted on its own; one not listed is refused. Repository settings are
  never a repair (branch protection, rulesets, required checks, apps,
  alerts): report the exact enable path instead.
- pause on conflict: {{PAUSE_ON_CONFLICT}} (true: stop this repository at
  the first conflict and report)
- budgets: `GH_MERGE_OP_TIMEOUT={{OP_TIMEOUT}}` per HTTP call; one absolute
  `GH_MERGE_DEADLINE_EPOCH` per PR, listed above. It is inherited, never
  recomputed, and never reset by a retry or handoff. The whole run ends at
  epoch {{RUN_DEADLINE}}; the earlier of the two bounds every call and
  every child you start, and any delegate inherits it. Export
  `GH_PROMPT_DISABLED=1`.
- progress log: `{{LOG}}`

Five checks, in this order, for every PR at one pinned head:

1. Is it what we think? Full refresh (pull, files, reviews, threads,
   check-runs, check suites, statuses, queue, effective policy), every
   section bound to the head. The classifier receipt must match that head
   and file set. Truncated or unreadable evidence is K13, never a pass.
   Identify every affected manifest, lock and generated export, its actual
   installation or fixture consumers, and requested/resolved/tested versions.
   A passing frozen-lock test does not validate a separate requirements
   installer. A path name alone does not establish fixture use. Supply the
   complete receipt described in `{{DEPENDENCY_EVIDENCE}}`; never fabricate
   coverage from a green status.
2. Did no one lose track? Evaluate only under your lease. A quarantined
   repository is never evaluated for merge; report and stop.
3. Is it green? Complete effective policy (branch protection plus branch
   rules, unknown never means none); every required check green from its
   required producer; no pending, failed, or prerequisite-skipped check;
   change requests, required approvals, and threads clear;
   `mergeable_state` clean; not in a merge queue. A reviewer bot's own
   rate limit is reviewer-unavailable, never CI red.
   Record relevant check applicability and its source. A documented exclusion
   can explain a missing analysis; unexplained missing coverage remains a
   hold. No classification claim waives a required check or producer.
4. Allowed? Mode, approval, owner hold, dependency-only receipt, budget.
5. Did it actually merge? After any merge attempt, GET the PR again:
   `merged` with merge commit and timestamp is MERGED; anything else is
   not. Queue acceptance and auto-merge arming are pending.

Transport rules:

- Dependency-only, READY, merge allowed: run
  `python3 {{MERGE_WRAPPER}} --expected-head <approved-head> --helper-path {{HELPER}} -- {{OWNER}} {{REPO}} <number> merge {{LOG}} --assert-trivial`
  in a dedicated process with that PR's deadline exported. Replace
  `<approved-head>` with the full head listed on the assigned card above,
  which must match the classifier receipt and any gated approval.
  Never substitute a newly fetched head for the assigned head. If it
  changed, hold for fresh classification and approval before a new tasking.
  The wrapper refuses a missing or invalid head with exit 12 and a changed
  head with exit 10 before any merge request. Never call `{{HELPER}}`
  directly from a durable worker. Exit 0: run check 5 before recording
  anything. Exit 10: hold with the literal reason. Exit 11: stop
  this repository, record `unknown`, report for quarantine, never retry.
- Involved (not dependency-only): `pr-merge-flow` preparation under this
  same authority; it merges only when merge is allowed for that PR.
- Merge queue required: the helper refuses it. Enqueue through
  `pr-merge-flow` exactly once; a queued PR is a WAITING `K10` hold, never
  merged, and is never enqueued again.
- Red CI: diagnose before repairing. Run the failing job on the base
  revision under matched conditions (workflow, job, matrix, command,
  toolchain, environment, inputs). Same failure there is `K05` baseline;
  base green is `K04` regression; anything unmatched is `K04` with low
  confidence. Every one of these still holds the PR: CI is never waived.
  Then `ci-fix` with the PR's remaining budget.
- No foreground `sleep` over 30 seconds. Never wait on one call twice.
- Before starting a repair, preserve enough of its remaining deadline for the
  required post-push validation. Call `plan_repair(expected_secs, now,
  deadline_epoch, reserve_secs)` from `{{PATIENCE}}`, estimating both the repair
  and validation from the actual commands or prior runs. Proceed only on
  `decision: repair`; its `repair_until` reserves the validation window.
  Report the next action if it does not fit. Never extend the inherited deadline.

Return exactly one outcome record per assigned PR over the life of this
attempt, as JSON lines. Send completed records incrementally or in one final
batch; do not repeat an already returned card. A partial batch leaves the
remaining cards and the repository lease with this attempt. The coordinator
validates every submitted batch before applying any record and refuses missing
required fields, so fill each field from evidence:

- `{"card_id": "PR-001", "outcome": "merged", "commit_sha": "<40 hex>", "merged_at": "<ISO 8601>"}`
- `{"card_id": "PR-001", "outcome": "ready", "head_sha": "<40 hex>", "reason_line": "...", "evidence": [{"id": "EV-...", "what": "...", "establishes": "..."}]}`
- `{"card_id": "PR-001", "outcome": "hold", "state": "WAITING|BLOCKED|NEEDS_OWNER", "reason_code": "K01..K17", "reason_line": "...", "severity": "critical|high|medium|low|advisory|unknown", "confidence": "...", "evidence": [...], "action": "...", "action_owner": "...", "resume_trigger": "...", "decision": {"why", "approve_effect", "decline_effect", "recommendation"}}`
- `{"card_id": "PR-001", "outcome": "unknown", "op_note": "<the uncertain operation>"}`
- `{"card_id": "PR-001", "outcome": "closed", "reason": "...", "replaced_by": "<card id or empty>"}`

A PR you could not reach still gets a record: hold `K12` with what stopped
you. `decision` is required only for `NEEDS_OWNER`. READY always includes the
full evaluated `head_sha`. Include that field on a hold only when the identity
check passed; omit it when observation or classification could not establish
the head. Collection saves the evaluated head and revokes approvals for other
heads. The next attempt then receives that head in its assigned card.

Include any follow-up discovered during or after a merge in the same return,
using the record contract in `{{REPORTING_REFERENCE}}`.
State its repository, problem, cause or attribution uncertainty, status,
recommendation, responsible party and evidence. Record external issue links
only when an issue was actually filed. Preserve completed repair evidence;
distinguish the remaining technical conditions from the reason execution
stopped. An explicit owner hold must cite the instruction that imposed it.
Group a common disposition across related PRs while retaining all their
identities and keeping closure, settings and merge authority separate.
