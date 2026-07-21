# Merge-Commit Default + Fast-Forward-Only Sync Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make merge commits the default PR integration strategy across the fleet (overridable per-repo), and make `git pull --ff-only` the primary sync method with `--rebase` demoted to a documented fallback.

**Architecture:** A single source of truth in `~/.claude/CLAUDE.md` declares the default and the precedence chain. `pr-merge-flow/SKILL.md` defers to that chain instead of hardcoding `--squash`. Per-repo files are edited only to stop asserting squash, not to restate the global rule. `--ff-only` replaces `--rebase` only where the working tree genuinely has no local commits; where it cannot work, `--rebase` stays and is relabeled as the fallback.

**Tech Stack:** Markdown docs, GitHub Actions YAML (`wagoid/commitlint-github-action@v6.2.1`), `gh` REST API, git worktrees.

## Global Constraints

- **Never commit to a local `main`.** Every task creates its own git worktree in a scratch dir; agents never switch branches in the user's live checkouts.
- **Conventional Commits** for every commit message.
- `skillsmith-publish-workflow` is a **worktree of `skillsmith`** — never edited as a separate repo.
- `shelf-press-tb` is a **second clone of `smorinlabs/py-launch-blueprint`** — never edited as a separate repo; it currently sits on branch `chore/remove-dead-cog-recipes`, so do not use it as a base.
- **Do not touch** `forge`, `forge_tui`, `floxcode`, `forge-service` — rebase-merge-only by upstream repo config; they are the intended override case.
- **Do not touch** `doxa-research/CLAUDE.md` lines 64 and 212, or `docs/superpowers/plans/CLAUDE.md:98` — those concern squashing *local WIP commits*, not merge strategy.
- Verification is by `rg` assertion (old string absent, new string present), not a test runner — these are documentation changes.

## Prerequisite already completed

`smorinlabs/skillsmith` repo settings were patched on 2026-07-20 and verified with a cache-busted read:
`merge_commit_title: MERGE_MESSAGE → PR_TITLE`, `merge_commit_message: PR_TITLE → PR_BODY`.
No task below repeats this.

---

## File Structure

| File | Responsibility | Task |
|---|---|---|
| `~/.claude/CLAUDE.md` | Declares the default + precedence chain (source of truth) | 1 |
| `smorinlabs-harness/.../pr-merge-flow/SKILL.md` | Defers to the chain; stops hardcoding `--squash` | 2 |
| `skillsmith/.github/workflows/commitlint.yml` | CI-enforces conventional commits (new) | 3 |
| `skillsmith/commitlint.config.mjs` | commitlint rules (new) | 3 |
| `skillsmith/CLAUDE.md` | Stops asserting squash-merge | 4 |
| `py-launch-blueprint/AGENTS.md` | Stops asserting squash-merge | 5 |
| `doxa-research/CLAUDE.md` | `--ff-only` primary, `--rebase` as fallback | 6 |
| `~/.claude/projects/.../memory/git-main-branch-discipline.md` | Squash divergence becomes legacy note | 7 |

---

### Task 1: Global merge-strategy default

**Files:**
- Modify: `~/.claude/CLAUDE.md` (insert new section after line 98, i.e. after the `## Commit Message Guidelines` block and before `## Repository Welcome Announcement`)

**Interfaces:**
- Produces: the phrase `Default merge strategy: merge commit` and the precedence list that Task 2 references by name.

- [ ] **Step 1: Confirm the insertion point**

Run: `rg -n '^## Commit Message Guidelines' -A3 ~/.claude/CLAUDE.md`
Expected: shows the heading, the "Should follow Conventional Commits Format" line, then `## Repository Welcome Announcement`.

- [ ] **Step 2: Insert the section**

Insert immediately before the `## Repository Welcome Announcement` heading:

```markdown
## Git Merge & Sync Strategy

**Default merge strategy: merge commit** (`gh pr merge <n> --merge`).
Merge commits preserve ancestry, so local branches stay fast-forwardable and
`git pull --ff-only` keeps working. Squash collapses a branch into one commit
with no ancestry link, permanently diverging any local copy of that branch.

Precedence — first match wins:
1. An explicit instruction from me in the conversation
2. The repo's own CLAUDE.md / AGENTS.md
3. The repo's GitHub settings (a disabled strategy is not a choice)
4. This file: merge commit

Known repo overrides: the Flox repos (`forge`, `forge_tui`, `floxcode`,
`forge-service`) are rebase-merge-only — squash and merge commits are disabled
upstream.

**Syncing is fast-forward-only.** Use `git pull --ff-only`, or
`git fetch origin <branch>:<branch>` when the branch is not checked out. Reach
for `--rebase` only when `--ff-only` genuinely cannot work — you have local
commits and origin has moved. Never bare `git pull`, never force.
```

- [ ] **Step 3: Verify**

Run: `rg -c 'Default merge strategy: merge commit' ~/.claude/CLAUDE.md`
Expected: `1`

Run: `rg -n '^## ' ~/.claude/CLAUDE.md | head -12`
Expected: `## Git Merge & Sync Strategy` appears between `## Commit Message Guidelines` and `## Repository Welcome Announcement`.

- [ ] **Step 4: No commit**

`~/.claude/` is not a git repo in this workflow. Do not attempt to commit. Report the diff instead.

---

### Task 2: `pr-merge-flow` defers to the precedence chain

**Files:**
- Modify: `~/c/smorinlabs-harness/plugins/repo-hygiene/skills/pr-merge-flow/SKILL.md:169-172` and `:176-177`

**Interfaces:**
- Consumes: the precedence list from Task 1 (referenced in prose, not imported).

- [ ] **Step 1: Create the worktree**

```bash
cd ~/c/smorinlabs-harness
git worktree add -b chore/merge-commit-default \
  /private/tmp/claude-501/wt/harness-merge-default origin/main
cd /private/tmp/claude-501/wt/harness-merge-default
```

- [ ] **Step 2: Edit the title rationale (line 169-172)**

Replace exactly:

```
- Title: must match the repo convention (CLAUDE.md), else Conventional
  Commits `type(scope): subject` — with squash merges the title becomes the
  commit subject. Fix via `gh pr edit --title`; `--auto` fixes silently,
  `confirm` shows old → new at the gate.
```

with:

```
- Title: must match the repo convention (CLAUDE.md), else Conventional
  Commits `type(scope): subject` — under the default merge-commit strategy
  the branch's own commits are what release tooling parses, and the title
  lands as the merge subject where the repo sets `merge_commit_title=PR_TITLE`.
  Fix via `gh pr edit --title`; `--auto` fixes silently, `confirm` shows
  old → new at the gate.
```

- [ ] **Step 3: Edit the auto-mode default (line 176-177)**

Replace exactly:

```
- **auto** — merge now (`gh pr merge --squash` unless prefs/CLAUDE.md say
  otherwise; `delete-branch` per prefs), then report what was done and run
```

with:

```
- **auto** — merge now (`gh pr merge --merge` per the CLAUDE.md merge-strategy
  precedence — user > repo CLAUDE.md/AGENTS.md > repo GitHub settings >
  global default; `delete-branch` per prefs), then report what was done and run
```

- [ ] **Step 4: Verify no stale squash default remains**

Run: `rg -n 'gh pr merge --squash' plugins/repo-hygiene/skills/pr-merge-flow/SKILL.md`
Expected: no output (exit 1).

Run: `rg -n 'gh pr merge --merge' plugins/repo-hygiene/skills/pr-merge-flow/SKILL.md`
Expected: exactly 1 match on the `**auto**` line.

- [ ] **Step 5: Confirm the ff-only block was NOT touched**

Run: `rg -n 'Never bare .git pull., never .--rebase., never force' plugins/repo-hygiene/skills/pr-merge-flow/SKILL.md`
Expected: 1 match — this block is already correct and must remain byte-identical.

- [ ] **Step 6: Commit and push**

```bash
git add plugins/repo-hygiene/skills/pr-merge-flow/SKILL.md
git commit -m "docs(pr-merge-flow): default to merge commit per CLAUDE.md precedence"
git push -u origin chore/merge-commit-default
```

- [ ] **Step 7: Verify the commit landed**

Run: `git log -1 --stat`
Expected: one commit touching exactly `plugins/repo-hygiene/skills/pr-merge-flow/SKILL.md`. A "nothing to commit" result is a failure — investigate.

---

### Task 3: skillsmith commitlint CI (prerequisite for Task 4)

**Files:**
- Create: `skillsmith/.github/workflows/commitlint.yml`
- Create: `skillsmith/commitlint.config.mjs`

**Interfaces:**
- Produces: a CI check named `commitlint` that Task 4's doc text refers to by that exact name.

**Adaptation note:** skillsmith has **no** `dependabot.yml` and **no** `RUNNER_UBUNTU` repo var, and uses `actions/checkout@v4`. Port a single-job, simplified version — do NOT copy py-launch-blueprint's dependabot split (YAGNI).

- [ ] **Step 1: Create the worktree**

```bash
cd ~/c/skillsmith
git worktree add -b ci/commitlint \
  /private/tmp/claude-501/wt/skillsmith-commitlint origin/main
cd /private/tmp/claude-501/wt/skillsmith-commitlint
```

- [ ] **Step 2: Create `commitlint.config.mjs`**

```javascript
// commitlint config for skillsmith.
//
// Extends @commitlint/config-conventional with body/footer caps raised from
// 100 to 200. The 100-char default routinely fails on commits whose bodies
// reference docs URLs or GitHub permalinks that cannot be broken across
// lines. 200 covers the realistic range while still flagging genuinely
// unbounded paragraphs.
//
// This is load-bearing for releases: `main` uses merge commits, so
// release-please parses the branch's individual commits.
export default {
  extends: ['@commitlint/config-conventional'],
  rules: {
    'body-max-line-length': [2, 'always', 200],
    'footer-max-line-length': [2, 'always', 200],
  },
};
```

- [ ] **Step 3: Create `.github/workflows/commitlint.yml`**

```yaml
# Validates every non-merge commit in a PR against conventional-commits.
#
# Load-bearing for releases: `main` uses merge commits, so the branch's
# individual commits land on the trunk and release-please parses them.
# The PR title is separately gated by the `lint-pr-title` job in ci.yml.

name: commitlint

on:
  pull_request:
  merge_group:  # job must report inside the merge queue; lint step no-ops there

permissions: {}

concurrency:
  group: commitlint-${{ github.ref }}
  cancel-in-progress: true

jobs:
  commitlint:
    name: commitlint (humans)
    runs-on: ubuntu-latest
    permissions:
      contents: read
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # range scan needs full history

      # On merge_group there are no PR commits to lint (already linted on the
      # PR) — skip the step so the required check still reports green.
      - name: commitlint
        if: github.event_name != 'merge_group'
        uses: wagoid/commitlint-github-action@v6.2.1
        with:
          configFile: commitlint.config.mjs
```

- [ ] **Step 4: Lint the workflow**

Run: `actionlint .github/workflows/commitlint.yml`
Expected: no output (exit 0). If `actionlint` is not installed, run `brew install actionlint` first.

- [ ] **Step 5: Commit and push**

```bash
git add .github/workflows/commitlint.yml commitlint.config.mjs
git commit -m "ci: enforce conventional commits on every PR commit"
git push -u origin ci/commitlint
```

- [ ] **Step 6: Verify the commit landed**

Run: `git log -1 --stat`
Expected: one commit, exactly two files added.

- [ ] **Step 7: Open the PR and confirm the check runs green**

```bash
gh pr create --title "ci: enforce conventional commits on every PR commit" \
  --body "Prerequisite for switching \`main\` to merge commits: release-please will parse individual branch commits, so they must be CI-enforced conventional. Adapted from py-launch-blueprint (single job; skillsmith has no dependabot)."
```

Then poll no more than once every 20 seconds, bounded to 10 checks:
`gh pr checks --watch` is acceptable, or `gh api repos/smorinlabs/skillsmith/actions/runs --jq '.workflow_runs[0].conclusion'`.
Expected: `commitlint (humans)` concludes `success`.

**GATE:** Do not start Task 4 until this PR is merged.

---

### Task 4: skillsmith stops asserting squash-merge

**Files:**
- Modify: `skillsmith/CLAUDE.md:71`

**Interfaces:**
- Consumes: the CI check name `commitlint (humans)` produced by Task 3.

- [ ] **Step 1: Create the worktree (from post-Task-3 main)**

```bash
cd ~/c/skillsmith
git fetch origin
git worktree add -b docs/merge-commit-default \
  /private/tmp/claude-501/wt/skillsmith-merge-doc origin/main
cd /private/tmp/claude-501/wt/skillsmith-merge-doc
```

- [ ] **Step 2: Replace line 71**

Replace exactly:

```
`main` uses squash-merge, so the PR title becomes the commit release-please parses. The `commit-msg` lefthook hook validates local commits; the `lint-pr-title` CI job validates PR titles.
```

with:

```
`main` uses merge commits, so release-please parses the branch's individual commits — every commit must be Conventional, not just the title. The `commit-msg` lefthook hook validates locally, the `commitlint (humans)` CI job enforces it on the PR, and `lint-pr-title` validates the title (which lands as the merge subject via `merge_commit_title=PR_TITLE`).
```

- [ ] **Step 3: Verify**

Run: `rg -n 'squash-merge' CLAUDE.md`
Expected: no output (exit 1).

Run: `rg -c 'uses merge commits' CLAUDE.md`
Expected: `1`

- [ ] **Step 4: Commit and push**

```bash
git add CLAUDE.md
git commit -m "docs: main uses merge commits, not squash"
git push -u origin docs/merge-commit-default
```

- [ ] **Step 5: Verify the commit landed**

Run: `git log -1 --stat`
Expected: one commit touching only `CLAUDE.md`.

---

### Task 5: py-launch-blueprint stops asserting squash-merge

**Files:**
- Modify: `py-launch-blueprint/AGENTS.md:134-141`

- [ ] **Step 1: Create the worktree**

Base off `py-launch-blueprint` (NOT the `shelf-press-tb` clone, which is on an unrelated branch):

```bash
cd ~/c/py-launch-blueprint
git fetch origin
git worktree add -b docs/merge-commit-default \
  /private/tmp/claude-501/wt/plbp-merge-doc origin/main
cd /private/tmp/claude-501/wt/plbp-merge-doc
```

- [ ] **Step 2: Replace the paragraph**

Replace exactly:

```
This format is REQUIRED for **every** commit — no exceptions for bot or
autofix commits (e.g. Copilot's "Potential fix…"). The required
`commitlint (humans)` CI check lints every non-merge commit in a PR, so a
single non-conventional commit blocks the merge; reword it (or squash the PR)
before merging. PR titles must follow the format too: commitlint does not
lint the title itself, but it becomes the default squash-merge commit
subject, so a non-conventional title lands a non-conventional commit on the
trunk. Always set a conventional title when squash-merging.
```

with:

```
This format is REQUIRED for **every** commit — no exceptions for bot or
autofix commits (e.g. Copilot's "Potential fix…"). The required
`commitlint (humans)` CI check lints every non-merge commit in a PR, so a
single non-conventional commit blocks the merge; reword it before merging.
PR titles must follow the format too: commitlint does not lint the title
itself, but this repo sets `merge_commit_title=PR_TITLE`, so a
non-conventional title lands a non-conventional merge commit on the trunk.
Always set a conventional title.
```

- [ ] **Step 3: Verify**

Run: `rg -n 'squash' AGENTS.md`
Expected: no output (exit 1).

Run: `rg -c 'merge_commit_title=PR_TITLE' AGENTS.md`
Expected: `1`

- [ ] **Step 4: Commit and push**

```bash
git add AGENTS.md
git commit -m "docs: trunk uses merge commits, not squash"
git push -u origin docs/merge-commit-default
```

- [ ] **Step 5: Verify the commit landed**

Run: `git log -1 --stat`
Expected: one commit touching only `AGENTS.md`.

---

### Task 6: doxa-research `--ff-only` primary

**Files:**
- Modify: `doxa-research/CLAUDE.md` at lines 139, 197, 204, and the "Fetch first" recipe near line 228-236

**Critical:** three sites convert, two deliberately do NOT. `--ff-only` cannot replace `--rebase` where local commits exist — that is the exact case `--rebase` exists for.

- [ ] **Step 1: Create the worktree**

```bash
cd ~/c/doxa-research
git fetch origin
git worktree add -b docs/ff-only-primary \
  /private/tmp/claude-501/wt/doxa-ff-only origin/main
cd /private/tmp/claude-501/wt/doxa-ff-only
```

- [ ] **Step 2: Convert line 139 (release-PR follow-up, on main, no local commits)**

Replace exactly:

```
5. `git pull --rebase origin main` locally to absorb the release commit; `uv sync` should be a no-op (CI's `sync-uv-lock` job already committed the lock update).
```

with:

```
5. `git pull --ff-only origin main` locally to absorb the release commit; `uv sync` should be a no-op (CI's `sync-uv-lock` job already committed the lock update).
```

- [ ] **Step 3: Convert line 197 (behind-check), naming the fallback**

Replace exactly:

```
If `[behind M]` with `M > 0`, STOP and `git pull --rebase origin main` before committing or pushing. Pushing a stale branch fails with "fetch first" — and any local commits may need re-doing if release-please bumped versions in the meantime.
```

with:

```
If `[behind M]` with `M > 0`, STOP and `git pull --ff-only origin main` before committing or pushing. If `--ff-only` refuses, you have local commits and origin has moved — that refusal is the signal to use `git pull --rebase origin main` instead. Pushing a stale branch fails with "fetch first" — and any local commits may need re-doing if release-please bumped versions in the meantime.
```

- [ ] **Step 4: Convert line 204 (post-tag sync, on main)**

Replace exactly:

```
git pull --rebase origin main      # pulls release bump + CI's lock-sync
```

with:

```
git pull --ff-only origin main     # pulls release bump + CI's lock-sync
```

- [ ] **Step 5: Reframe the "Fetch first" recipe as the documented fallback**

Find the `### "Fetch first" push rejection` section. Replace exactly:

```
Origin moved while you were working. Don't force-push.
```

with:

```
Origin moved while you were working and you have local commits, so
`--ff-only` cannot apply — this is the documented fallback case for
`--rebase`. Don't force-push.
```

Leave the `git pull --rebase origin main` line in that recipe unchanged.

- [ ] **Step 6: Verify the split landed correctly**

Run: `rg -n 'git pull --ff-only origin main' CLAUDE.md`
Expected: exactly 3 matches (lines ~139, ~197, ~204).

Run: `rg -n 'git pull --rebase origin main' CLAUDE.md`
Expected: exactly 2 matches — one inside the line-197 fallback sentence, one in the "Fetch first" recipe.

Run: `rg -n 'squash' CLAUDE.md`
Expected: 2 matches at lines ~64 and ~212 — local WIP squashing, intentionally untouched.

- [ ] **Step 7: Commit and push**

```bash
git add CLAUDE.md
git commit -m "docs: --ff-only is the primary sync, --rebase the fallback"
git push -u origin docs/ff-only-primary
```

- [ ] **Step 8: Verify the commit landed**

Run: `git log -1 --stat`
Expected: one commit touching only `CLAUDE.md`.

---

### Task 7: Memory reflects the new default

**Files:**
- Modify: `~/.claude/projects/-Users-stevemorin-c/memory/git-main-branch-discipline.md`

- [ ] **Step 1: Read the current file in full**

Run: `cat ~/.claude/projects/-Users-stevemorin-c/memory/git-main-branch-discipline.md`

- [ ] **Step 2: Reframe the squash divergence passage**

The squash-breaks-ancestry explanation stays factually intact, but is relabeled from "the steady state" to "the legacy/exception case". Add one sentence to the body:

```
As of 2026-07-20 the fleet default is merge commits (see the Git Merge &
Sync Strategy section of the global CLAUDE.md), which preserve ancestry and
keep `--ff-only` working. The squash divergence below now applies only to
repos that explicitly opt into squash.
```

Do not change the `--ff-only` guidance itself — it is reinforced, not replaced.

- [ ] **Step 3: Verify**

Run: `rg -c 'fleet default is merge commits' ~/.claude/projects/-Users-stevemorin-c/memory/git-main-branch-discipline.md`
Expected: `1`

- [ ] **Step 4: No commit** — the memory dir is not a git repo in this workflow.

---

## Execution order

```
Task 3 (skillsmith commitlint CI) ──merge──> Task 4 (skillsmith CLAUDE.md)

Task 1 ─┐
Task 2 ─┼── independent, run in parallel
Task 5 ─┤
Task 6 ─┤
Task 7 ─┘
```

Tasks 1, 2, 5, 6, 7 have no interdependencies and may run concurrently. Task 4 is gated on Task 3 merging.

## Verification sweep (after all tasks)

Run from `~/c`:

```bash
rg -n --glob 'CLAUDE.md' --glob 'AGENTS.md' --glob '!skills_ref/**' --glob '!_ext-*/**' \
  'squash-merge|squash-merging|gh pr merge --squash' .
```
Expected: no output. Any hit is an unconverted site.

---

## Deviations from this plan, as executed (2026-07-21)

This plan is preserved as written. Six things changed during execution; the
design doc reflects the corrected decisions.

1. **Task 1 said "no commit needed."** Wrong — `~/.claude/CLAUDE.md` is a symlink
   to `smorin-bootstrap/dotfiles/claude-CLAUDE.md`, which is version-controlled.
   The edit landed as an uncommitted change on that repo's `main` and had to be
   moved onto a branch. Became a PR like every other task.

2. **The `merge_commit_title=PR_TITLE` prerequisite was wrong and was reverted.**
   Under merge commits release-please parses branch commits; making the merge
   subject *also* conventional double-counts every change. Correct value is
   `MERGE_MESSAGE`, which is what 10 of 12 release-please repos already used.

3. **Task 3 must not create `commitlint.config.mjs`.** skillsmith already had a
   `commitlint.config.js`. Two configs split-brain: cosmiconfig resolves `.js`
   first, so the local hook and CI would enforce different rules. Resolution was
   to **rename** `.js` → `.mjs` and point CI at it — not to add a second file.

4. **`configFile: commitlint.config.js` fails 100% of PRs.**
   `wagoid/commitlint-github-action@v6.2.1` hard-rejects a `.js` extension
   (`src/action.mjs:139-143`). The `.mjs` rename is mandatory, not stylistic.

5. **The workflow needs `pull-requests: read`.** The action reads PR commits from
   the REST API, not from git — so `contents: read` alone 403s on a private repo,
   and `fetch-depth: 0` is pure waste. The `merge_group` trigger was dropped as
   dead config (no merge queue is possible without a ruleset).

6. **Task 4's replacement text cited `PR_TITLE`.** Corrected to explain that the
   merge subject is deliberately non-conventional so release-please counts each
   change exactly once.

Added beyond this plan: an org-wide settings sweep (`allow_squash_merge=false`
across 31 repos) and an org ruleset restricting merge methods for future repos.
