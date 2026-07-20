# pr-merge-flow

Drives an open GitHub PR to merge by resolving every review thread before the
merge happens. It waits a bounded few minutes for AI reviewer bots (Claude,
Codex, Greptile, Copilot, …) to finish commenting, then triages each unresolved
thread with review-receiving rigor: restate the claim, verify it by running the
code or a test where possible, fix valid findings (commit, push, reply naming
the fix, resolve) and refute invalid ones with a reasoned reply before
resolving — never a silent resolve. Because pushed fixes can trigger fresh bot
reviews, it cycles (bounded, 3 by default) until a pass is clean, checks the PR
title against repo conventions (repo `CLAUDE.md` first, Conventional Commits as
the default — with squash merges the title becomes the commit subject), then
ends per mode. All GitHub polling is quota-safe: rate-limit preflight, a
20–30s interval floor, hard-bounded monitors with one manual recheck on
expiry, and a `gh` → `gh api` REST → `curl` fallback ladder (GraphQL is used
only to read thread resolution state and post the resolve mutation). Of those two
GraphQL operations only the `isResolved` read has any substitute: REST already
carries the rest of the inventory — path, line, author, and the `databaseId`
replies need — so the gap is a single boolean per thread. For that one bit
there is an escape hatch: a **read-only Chrome fallback** (the
`claude-in-chrome` skill on Claude Code, the `chrome@openai-bundled` plugin on
Codex, a clean degrade to a ready-report on any harness with neither) that
reads the PR's web UI, whose session-authenticated endpoints draw on a
different quota pool, confirms the page's owner/repo/PR identity before
trusting a word of it, and correlates what it reads back onto the REST
inventory. It is gated in *every* mode including `--auto`, because driving a
logged-in browser is not something automation should assume, and it is bounded:
2–3 failures degrade to an honest report naming which threads are
known-unresolved, known-resolved, and undetermined. It deliberately does **not**
resolve threads — GitHub renders Resolve buttons lazily (absent from the
accessibility tree) and anonymously (`find` returns identical labels carrying no
thread identity), so a click cannot be safely targeted and resolution stays
API-only. With GraphQL exhausted, threads are replied-to and left open until
quota returns: honest and recoverable, never a silent resolve. After a successful merge it runs a read-only cleanup survey — local and remote PR
branch, worktrees on the merged branch, stale merged branches, prunable
worktree entries, dirty uncommitted state — and presents two lists:
*needs cleanup* (each item a named action with its exact command) and
*already clean*. Nothing runs without explicit multi-select confirmation;
`--auto` mode reports the lists and touches nothing; dirty state is only
ever reported, never deleted. The survey also offers — never assumes — a
guarded sync of the local default branch: blocked if the checkout is dirty,
the default branch is checked out in another worktree, local commits sit
ahead of the remote, or a git operation is in progress; guards re-run at
execution time, and the sync itself is fast-forward-only
(`git fetch origin main:main` when main is not checked out,
`git pull --ff-only` when it is).

**Triggers on:** "merge this PR", "get PR #N merged", "resolve the PR
comments", "address review feedback and merge", "close out this PR", "babysit
the PR"

**Arguments:** `--auto` (merge when clean, no questions) · `--confirm` (final
merge gate; the default) · `--ready` (prepare everything, you merge) ·
`--deep` (opt-in deep review via `/code-review`, a Codex adversarial pass, or
the pr-review-toolkit agents). Precedence: invocation flag or plain ask >
`.claude/pr-merge-flow.local.md` (git-ignored per-repo preferences: `mode`,
`deep-review`, `merge-method`, `delete-branch`) > default (confirm, no deep).

## Install

| Mode | When | How |
|---|---|---|
| Plugin (recommended) | You just want to use it | `/plugin install repo-hygiene@smorinlabs-harness` |
| Dev symlink | You want to tweak/iterate | `git clone https://github.com/smorinlabs/smorinlabs-harness` then `ln -s "$(pwd)/smorinlabs-harness/plugins/repo-hygiene/skills/pr-merge-flow" ~/.claude/skills/pr-merge-flow` |
| Direct copy | No marketplace access | copy `plugins/repo-hygiene/skills/pr-merge-flow/` into `~/.claude/skills/` |

**Codex:** register the marketplace in `~/.codex/config.toml`
(`[marketplaces.smorinlabs-harness]`) and enable the plugin — or use the
dev-symlink path, also linking into `~/.agents/skills` (Codex's current
skills location).

## Example session

> Get PR #42 merged — resolve whatever the bots found.
> → Reads `.claude/pr-merge-flow.local.md` (none → confirm mode), waits up to
> ~5 minutes polling every 30s for pending bot reviews, collects 7 unresolved
> threads, verifies each claim (running the failing case where feasible),
> fixes 5 with conventional commits and replies naming the fix SHA, refutes 2
> with concrete reasons, resolves all 7, waits out one re-review cycle,
> confirms checks are green and the title is `feat(api): add rate limiter`,
> then presents the final gate: **Merge now (squash)** / Run deep review
> first / Don't merge. After merging, the cleanup survey lists
> `git branch -d feat/rate-limiter` and one stale worktree as needs-cleanup
> (the remote branch was auto-deleted — already clean); nothing runs until
> selected.
