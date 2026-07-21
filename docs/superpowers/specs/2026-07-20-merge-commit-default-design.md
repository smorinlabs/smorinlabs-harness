# Merge-Commit Default + Fast-Forward-Only Sync — Design

**Date:** 2026-07-20
**Status:** Implemented 2026-07-21

## Problem

Two independent audit findings converged:

1. The fleet's default PR merge strategy lived in exactly one place — a hardcoded
   `gh pr merge --squash` inside `pr-merge-flow/SKILL.md` — while four Flox repos
   overrode it to rebase-only and three release-please repos described squash in
   their own CLAUDE.md/AGENTS.md. The global `CLAUDE.md` said nothing at all.
2. Several repos documented `git pull --rebase` as the routine sync, despite a
   standing rule (`git-main-branch-discipline`) that `--ff-only` is the only safe
   way to update `main`.

These are the same problem. Squash merge collapses a branch into one commit with
no ancestry link to the originals, which is precisely what makes `git pull
--ff-only` refuse afterwards. The `--rebase` workaround existed to paper over
damage the merge strategy was causing.

## Decision

**Merge commits become the fleet default**, overridable per-repo, with
`--ff-only` as the primary sync and `--rebase` demoted to a documented fallback
for the one case it is actually needed: local commits exist and origin moved.

### Precedence chain

Declared once in the global `CLAUDE.md`; first match wins:

1. An explicit instruction from the user in conversation
2. The repo's own CLAUDE.md / AGENTS.md
3. The repo's GitHub settings (a disabled strategy is not a choice)
4. Global default: merge commit

### Why merge commits, specifically

Three tools constrain the choice, and only merge commits satisfy all three:

| Constraint | Squash | Merge | Rebase |
|---|---|---|---|
| Preserve ancestry so `--ff-only` works | ✗ | ✓ | ✗ (rewrites SHAs) |
| release-please counts each change once | ✓ | ✓ *(conditional)* | ✓ |
| contributors-please attributes correctly | ✗ **destroys** | ✓ | ✓ |

`contributors-please` walks `git log --no-merges` and attributes by author
(`%aN`/`%aE`) plus changed files (`--name-only`). Under squash, a multi-author PR
collapses to one commit with one author and all files credited to that person.
`Co-authored-by:` trailers are not read. The loss is silent and unrecoverable.

Rebase satisfies both tools but rewrites SHAs, breaking the ancestry `--ff-only`
depends on. Merge wins on all three axes; rebase wins two of three.

### The conditional on release-please

release-please walks **all ancestors** (GraphQL `history()`, no merge filter), so
under merge commits it parses the branch's individual commits. If the merge
commit's own subject is *also* conventional, it is parsed too, and every change
is counted twice.

Therefore `merge_commit_title` must be **`MERGE_MESSAGE`**, not `PR_TITLE`. The
deliberately non-conventional `Merge pull request #N from …` subject is
load-bearing: it is what makes release-please skip the merge commit.

This inverts the intuition carried over from squash, where the PR title *was* the
parsed artifact. Ten of the twelve release-please repos already used
`MERGE_MESSAGE`; the two that did not were corrected.

### Consequence for CI

Under squash, the PR title was the release input and was gated by `lint-pr-title`.
Under merge commits, the branch's individual commits become the input — and those
were previously guarded only by a bypassable local hook. Any release-please repo
switching to merge commits therefore needs commitlint enforced in CI, not just
locally.

## Scope

**In:** global `CLAUDE.md`, `pr-merge-flow/SKILL.md`, `skillsmith`,
`py-launch-blueprint`, `doxa-research`, and the `git-main-branch-discipline`
memory.

**Out:** the Flox repos (`forge`, `forge_tui`, `floxcode`, `forge-service`) are
rebase-merge-only with squash and merge commits disabled upstream. They are the
precedence chain working as intended, not drift to correct.

## Enforcement

Documentation states intent; two layers make it real:

- **Per-repo settings** — `allow_squash_merge=false` across all 31 non-archived
  `smorinlabs` repos plus `smorin-bootstrap`. Removes the button, so the mistake
  is unmakeable. Cannot reach repos that do not exist yet.
- **Org ruleset** (`merge-methods: no squash`) — targets `~ALL` repos' default
  branch, `allowed_merge_methods: [merge, rebase]`. Covers future repos. Fails
  late (at merge time) rather than hiding the option.

`allowed_merge_methods` exists only inside the `pull_request` rule, which also
requires a PR before merging. Two workflows (`doxa-research`,`mockcast`) push
directly to `main` under App tokens, so the release-please and
contributors-please Apps are bypass actors; without them, releases break at tag
time with an error that does not mention rulesets.

## Verification

- All 7 PRs merged with 2 parents each — merge commits in practice, not just config
- `commitlint (humans)` green on its own PR
- 31 repos verified uniform via cache-busted reads, zero drift
- Org ruleset confirmed applying to repos never touched individually
