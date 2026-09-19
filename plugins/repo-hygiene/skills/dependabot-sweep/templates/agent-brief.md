# Subagent brief — one repo of a dependabot-sweep

Render one copy per repo-with-PRs and hand it to a Task subagent. All
`{{VARS}}` are filled by the orchestrator; the agent never sees a placeholder.

---

You are sweeping Dependabot PRs in exactly one repo: `{{OWNER}}/{{REPO}}`.
Touch nothing outside it.

Open Dependabot PRs ({{PR_COUNT}}):

{{PR_LIST}}

Flags for this sweep:

- auto_fix = {{AUTO_FIX}} (false: triage and report only, change nothing)
- pause_on_conflict = {{PAUSE_ON_CONFLICT}} (true: on any merge conflict, stop
  this repo's work and report back immediately)

Work each PR number from the list above in order through this ladder (N is
that PR's number — always pass it explicitly; never merge "the current
branch's" PR):

1. Fetch the PR (`gh pr view N -R {{OWNER}}/{{REPO}}`) and review the
   diff. Trivially mergeable (CI green, no conflicts, dependency-only diff)
   → merge with `gh pr merge N --merge`.
2. CI red → load and follow the `ci-fix` skill for this repo, then merge
   once green.
3. Review findings, failing checks that need code changes, or anything
   beyond a mechanical fix → load and follow the `pr-merge-flow` skill for
   that PR.
4. Merge conflict: if pause_on_conflict is true, stop and report; otherwise
   record the conflict and continue with the next PR.

Report back exactly one line per PR:

- `merged <url>` — merged (directly or after delegated fix)
- `conflict <url> <what conflicts>` — merge conflict
- `needs-human <url> <reason>` — anything you could not resolve

End with a one-line tally: `tally merged=X conflict=Y needs-human=Z`.
