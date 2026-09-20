# Subagent brief — one repo of a dependabot-sweep

Render one copy per repo-with-PRs and hand it to a Task subagent. All
`{{VARS}}` are filled by the orchestrator; the agent never sees a placeholder.

---

You are sweeping Dependabot PRs in exactly one repo: `{{OWNER}}/{{REPO}}`.
Touch nothing outside it. You classify each PR and execute merges ONLY through
the helper — never run `gh pr merge`, `gh api` merge calls, or curl PUTs
yourself.

Open Dependabot PRs ({{PR_COUNT}}):

{{PR_LIST}}

Flags for this sweep:

- auto_fix = {{AUTO_FIX}} (false: triage and report only, change nothing)
- pause_on_conflict = {{PAUSE_ON_CONFLICT}} (true: on any merge conflict, stop
  this repo's work and report back immediately)
- Budgets: `GH_MERGE_OP_TIMEOUT={{OP_TIMEOUT}}`,
  `GH_MERGE_PR_BUDGET_SECS={{PR_BUDGET}}` (export both; one absolute deadline
  per PR that retries and delegation cannot reset). Also export
  `UV_CACHE_DIR={{UV_CACHE}}` and `GH_PROMPT_DISABLED=1`.
- Helper: `{{HELPER}}` (scripts/gh_merge.py). Progress log: `{{LOG}}`.

Rules (all mandatory):

1. No foreground `sleep` over 30 seconds. Never wait on one call twice.
2. No review archaeology on eligible trivials: read the diff + file list only.
   Anything beyond a mechanical fix goes to `pr-merge-flow` preparation-only
   (triage and fix, do not merge), then re-classify exactly once.
3. Red CI goes to `ci-fix` with the PR's remaining budget, then re-classify
   exactly once. A repaired PR merges only after a fresh helper preflight.
4. Repair scope boundary: never change repo settings (branch protection,
   rulesets, vulnerability alerts, dependency graph, required checks, apps).
   If a repair needs one, report needs-human with the exact enable path.
5. For each PR number N in order: if the diff is dependency-only, run the
   helper (`python3 {{HELPER}} {{OWNER}} {{REPO}} N merge {{LOG}}
   --assert-trivial`) and transcribe its single-line verdict. Exit 0 merged;
   10 deferred (record the reason, continue); 11 unknown (stop this repo,
   hold the mutation slot, report for quarantine — never retry).
6. If pause_on_conflict is true, stop the repo at the first conflict instead
   of recording and continuing.

Report back exactly one line per PR:

- `merged <url>` — helper exit 0 (directly or after one bounded repair cycle)
- `deferred <url> <reason>` — helper exit 10 (pending, failed-checks,
  conflict, queue-required, nontrivial, unreadable-evidence)
- `unknown <url> <reason>` — helper exit 11 (quarantined, slot held)
- `needs-human <url> <reason>` — anything else you could not resolve

End with a one-line tally:
`tally merged=X deferred=Y unknown=Z needs-human=W`.
