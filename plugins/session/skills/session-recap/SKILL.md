---
name: session-recap
allowed-tools: Bash, Read, Glob, Grep
description: Orient yourself (and the user) when returning to a coding session that's been left idle, compacted, or reopened cold. Produces a structured recap — what the session is about, where it started and ended, what's done vs. open, the live state of git/PR/worktree, and ranked next steps — ending in a close-or-continue verdict. Use this whenever the user asks to "catch me up", "where was I", "where are we", "recap this session", "what's the state of this", "what was I doing", "get me up to speed", "did I finish", or returns to a repo after time away and seems unsure of the current state. Reach for it even when the user doesn't say "recap" but is clearly disoriented about an in-flight task.
---

# session-recap

You're helping someone who has many sessions open and has lost the thread on this
one. Reconstruct the **full picture** from evidence — the conversation transcript
and the live repo state — so they (and you) can re-enter cold: *where you've
been · what happened · where you are now · the plan if you're mid-stream · the
thread to get back to (you got distracted) · where to go next* — including any
**open decisions, each with the context to actually decide.** Be comprehensive
but organized: a light cockpit for fast orientation on top, the full picture
below, and adapt so a trivial session collapses to a few lines while a multi-day
one zooms out to the milestone level.

This skill is **read-only** — a contract, not a preference. Observe, never mutate;
recommend, never act; never run the test suite. That clean boundary is what
separates this skill from `session-loose-ends`, the sibling that does the acting.
The report is an **interface, not a document**: it carries stable reply-IDs
(`O1`, `D1`, …) and copy-pasteable launches so the user can act in the next
thirty seconds without re-reading anything.

## How to work

Gather evidence first (the six checks below), *then* write the report. Run the
commands quietly and synthesize — do not narrate the gathering. Every check
degrades gracefully: if a tool is missing or a command fails, note it on that line
and move on. **A partial recap is useful; a stalled one is not.**

**Provenance, by zone — not per line.** A stream's facts block is live by nature:
carry its provenance once, in a single footer line — `Live state (PR, CI, tree)
checked just now.` — never with a 🛰 marker on every fact. Mark only **🤔
inference** inline, where you're reading between the lines rather than reporting a
probe. Across the whole recap, keep three provenance classes straight: what you
**know** (🛰 live — the tree is dirty, CI failed), what you **remember** (📜 from
the transcript), and what you **infer** (🤔, hedged so the user can correct it).
Never invent a PR number, a ticket, or a decision.

**Read-only, enforced.** You gather and report; you never commit, push, clean up,
or modify files. For build/test state, infer from the transcript whether the
session ended green or mid-failure — **do not run the suite** (it is slow and has
side effects). If the state is uncertain, *recommend* the verify command
(`just all` / `make check`) as a next step rather than running it. Other sessions'
artifacts are **attributed, never claimed** — reported as parallel work, never
offered for cleanup.

## Gathering

Six checks. Together they answer: what is this session, what happened, where does
it stand live, what's the plan of record, what's still owed, and what moved while
you were away.

### 1. Transcript digest — the session arc

After a long session your own context has been compacted — the opening is
summarized away. The raw transcript still has it. Read a compact digest rather
than the multi-megabyte file. The script ships with this skill, so invoke it by
its path in this skill's directory (the user's working directory is their repo,
not here):

```bash
python3 <skill-dir>/scripts/transcript_digest.py
```

`$CLAUDE_CODE_SESSION_ID` is exported into the environment and names the transcript
file exactly, so the script finds *this* session deterministically — it reads the
variable from its own environment, so don't pass it as an argument (that just risks
the value getting lost if your shell didn't export it). The digest gives you the
title, the opening prompt, compaction markers, branch changes, timing, the last
several turns, and a **references** block — ticket ids (e.g. `ENG-1423`), spec/doc
files, and URLs mentioned in the session. Those references are gold for orienting
open work: they point at the goal's source of truth.

For a long or multi-day session, `python3 <skill-dir>/scripts/transcript_digest.py
--prompts-only` lists the human's substantive prompts with timestamps — those are
the raw material for the 🧵 Timeline's beats (Report → 1 · 🧵 Timeline).

If the script prints `NO_TRANSCRIPT` (unset session id on an older CLI, or a
different harness), fall back to the most recently modified transcript for this
repo and pass it positionally:

```bash
# Transcripts are filed per working directory, so scope to THIS repo instead
# of globbing every project: the newest transcript on the machine is often
# another repo's, and a recap of the wrong repo reads as perfectly correct.
proj=~/.claude/projects/"$(echo "$PWD" | tr '/.' '--')"
newest="$(ls -t "$proj" 2>/dev/null | grep '\.jsonl$' | head -1)"
[ -n "$newest" ] && echo "$proj/$newest"   # then: transcript_digest.py <that-path>
```

Listing the directory rather than globbing it keeps an absent directory quiet
under both bash and zsh.

If that prints nothing — or no transcript exists at all — recap from what's in
your context and say so plainly. Don't pretend to a richer history than you
have, and never widen the search to other repos to fill the gap.

### 2. Working tree, branch, and worktree

```bash
git status --porcelain=v2 --branch   # dirty files + ahead/behind in branch.ab line
git stash list
git log --oneline -5
git worktree list
git log @{upstream}..HEAD --oneline 2>/dev/null   # unpushed commits, if upstream exists

# The default branch, whatever is currently checked out. `git status` only ever
# describes the CURRENT branch, so a repo parked on a feature branch reports
# nothing about `main`.
d=$(git symbolic-ref --short refs/remotes/origin/HEAD | sed 's|origin/||')
git rev-list --left-right --count "origin/$d...$d"   # → "<behind>\t<ahead>"
```

What each fact means for orientation:

- **Dirty tree** — uncommitted/staged changes are work-in-flight. "3 modified, not
  committed" is a top-of-mind fact, not a footnote.
- **Ahead/behind** — the `# branch.ab +X -Y` line tells you unpushed commits (`+X`)
  and un-pulled ones (`-Y`). This is the *current* branch only.
- **Default-branch freshness** — the `rev-list --left-right --count` output is
  `<behind>\t<ahead>` for the default branch regardless of what's checked out.
  `behind>0, ahead=0` is merely stale and fast-forwards cleanly. **`ahead>0` is
  divergence**: `--ff-only` will refuse, and it usually means commits were made
  directly on the default branch, or an upstream squash-merge rewrote them.
  Report it as needing a decision, never as something to clean up.
- **Merged-but-dirty is a red flag** — uncommitted work on a branch that's already
  merged usually means leftover scraps or a forgotten context switch. Surface it.

**The worktree-removed-from-under-you case.** You may be standing in a git worktree
that parallel work has already deregistered. The tells: `git status` fails with
"not a git repository", or your current path is absent from `git worktree list`
even though you're clearly inside what was a checkout. If you see this, say so
directly — "this worktree appears to have been removed (likely cleaned up by
parallel work); the directory is now orphaned" — because it changes the next step
entirely (there's nothing here to finish).

**Multi-location sessions.** When the transcript shows more than one `cwd`/branch
pair, pull its own location history instead of reconstructing it by hand — it
feeds the **🗺 Scope map** (Opening zone) directly:

```bash
python3 <skill-dir>/scripts/transcript_digest.py --scope
```

This emits the first→last-seen span per `cwd`/branch pair, in transcript order,
plus any `worktree-state` / `relocated` events — the raw material for the Scope
map's per-location rows. It's a transcript view, not a live probe: run the git
commands above per location it names to learn what's true *now*.

### 3. Pull request and CI (best-effort via `gh`)

GraphQL-backed `gh` commands (`gh pr view`, `gh pr list`, `gh pr checks`)
rate-limit frequently on this machine — prefer REST:

```bash
gh api "repos/{owner}/{repo}/pulls?head={owner}:{branch}&state=all" 2>&1
gh api "repos/{owner}/{repo}/commits/{sha}/check-runs" 2>&1
```

**One probe per endpoint, per recap — no retry loops.** Don't poll a pending
check to resolution and don't re-hit a rate-limited endpoint hoping it clears;
resolve to one of the five outcomes below and move on.

The `pulls` probe, filtered by `head={owner}:{branch}`, resolves the PR (if any)
for the current branch directly. Translate the raw fields into the cockpit
**state vocabulary** (the five dot-states defined under *The report → Opening
zone*) and into the per-stream facts:

- **No PR** for this branch → say so; that itself is a next-step signal if the work
  looks done. Frame the absence: **⏳ not yet due** (work unfinished — expected) vs
  **⚠ a problem** (work looks finished but unshipped) — never ambiguous.
- **`state`** ("open" / "closed") **+ `merged_at`** — open is OPEN; closed with a
  non-null `merged_at` is MERGED; closed with `merged_at: null` is CLOSED
  unmerged.
- **`draft`** — a draft PR isn't ready for review; don't read it as waiting on a
  reviewer.
- **Review state** isn't on the list response. If it matters (comments to
  address, or a reviewer still owed), fetch `GET …/pulls/{n}/reviews` for the
  latest review per reviewer: an approval (ready to merge), changes requested
  (address comments — skim and name what's actually being asked for, rather
  than just "has comments"), or none yet (waiting on a reviewer).
- **Merge conflicts** also aren't on the list response (GitHub computes
  mergeability per-PR). If the branch looks stale against its base, fetch
  `GET …/pulls/{number}` for that PR's `mergeable` — a conflicting merge means
  a rebase/merge is needed before anything else.
- **`check-runs`** — each run's `status` ("queued" / "in_progress" /
  "completed") and, once completed, its `conclusion` ("success" / "failure" /
  …) give CI passing, failing, or pending: `completed` + `success` → 🟢,
  `completed` + anything else → 🔴, `queued` / `in_progress` → 🟡. **Name the
  failure at the most specific one-line level** — one test by name, several by
  count + cluster, or the job level when broader:

```
CI  🟢 passing
CI  🔴 failing — test_rollup, on the sliding-window path       ← one test: name it
CI  🔴 failing — 7 tests, all in test_rollup.py                ← several: count + cluster
CI  🔴 2 of 5 jobs failing — lint, integration tests           ← job level when broader
CI  🟡 running — started 4 min ago
```

Five-outcome error contract — every probe resolves to exactly one, and the recap
renders the distinction:

| Outcome | Coverage-line rendering |
|---|---|
| ok | facts rendered normally |
| no-PR-exists | `PR — none for this branch` + ⏳/⚠ per empty-state semantics |
| rate-limited | `⚠ GitHub rate-limited — PR/CI state unknown (not "no PR"); retry later` |
| unauthenticated / gh missing | `⚠ GitHub CLI unavailable — PR/CI checks skipped` |
| network/other error | `⚠ GitHub unreachable — PR/CI state unknown` |

Load-bearing rule: **"couldn't check" must never render as "checked, nothing
found."** Rate-limited is unknown-state, not no-PR.

### 4. Plan of record — the checklist behind each stream

For each stream (project / milestone / topic / incident), locate its **plan of
record** — the checklist that says what the whole effort is, done and remaining:
a `PROJECTS.md` entry, a design-doc checklist, an inline-chat agreement, or a
combination. **Name the source** (`Plan — from PROJECTS.md P07`, `Plan — from the
billing-v2.md checklist`). This is the bridge that lets the recap show ✅ done and
⬜ remaining in one view, and it surfaces plan items the session never touched. If
no plan of record exists for a stream, **state its absence** — don't invent a
spine.

### 5. Classify everything still owed

The checks above tell you what *happened*. This pass decides what is still
**owed** — it's what makes the worklist tables fillable. Skip it and you'll reach
the end with nothing classified and start improvising, which shows up as items
duplicated between the close and the tables, or as ideas quietly promoted into
obligations.

Re-read the transcript with one question per unresolved thing: *who has to move
next, and did anyone actually agree to it?* Tag each one, and **keep the quote or
probe that earned the tag**:

| Tag | Test | Proof required |
|-----|------|----------------|
| ❓ `D#` | A question was put to the user and never answered, or two approaches were weighed and never chosen | the unanswered question |
| 📌 `W#` | The user assented (or you stated an intention they didn't refuse) **and** nothing has been written for it yet | the assent, quoted with its turn — **or a standing instruction** (a global/process CLAUDE.md rule that makes the work owed; cite the rule as the proof) |
| 🧹 `C#` | Something that needs only **clearing**, not work — an artifact or process a probe can see and a command can remove | the probe output |
| 💡 `S#` | Floated by either party and never assented to | the origin, quoted with its turn |

Pull the proof quote with `--find` rather than re-reading the raw transcript —
pass the words you remember from the exchange and it returns the matching turns
verbatim, clipped to a standard snippet, with `[timestamp role]` refs ready to
paste as the row's proof (repeatable for more than one phrase):

```bash
python3 <skill-dir>/scripts/transcript_digest.py --find "<remembered words>"
```

**🧹 is checked first and wins ties.** Cleanup is a *special case* of open work:
it's unresolved, but nothing has to be *worked on* — it only has to be cleared.
So ask "does this just need clearing?" before anything else, and when both fit,
cleanup takes precedence. A merged branch's worktree still exists and a probe
still sees it, but nobody has to work on it — that's 🧹, not an in-flight stream.

Two more rules keep this honest:

- **No proof, no row.** If an item can't produce its quote or probe output, it
  doesn't get an ID. The tag is a claim about the record, not a feeling.
- **📌 vs 💡 is decided by the record, not by merit.** A good idea you had and
  the user never answered is 💡, full stop. The distinction is the whole point:
  it's what lets the user trust that 📌 is a real backlog. The one widening of 📌:
  a **standing instruction** — a global or project process rule that makes work
  owed even with no in-session quote — is valid proof; cite the rule.

**In-flight (`O#`) is for work that needs to be worked on and has been started** —
a half-written function, a red CI job, a branch mid-change. Work nobody has started
yet is owed as 📌; anything that needs only clearing is 🧹 no matter how "open" it
looks. Don't route on surface signals — "a branch exists" is true of both a feature
mid-change and a merged branch's leftover worktree, and only the first is in-flight.

### 6. The world moved — deltas the transcript can't know

The transcript is a closed record; the world kept moving. Probe two kinds of
delta:

- **Away-time ("Since you left")** — for a cold return: branch behind/ahead of
  upstream, `origin/main` moves, new review comments on the PR, CI re-runs since
  the last transcript turn.
- **Parallel-while-live** — the default branch advancing mid-session, sibling
  worktrees appearing (`git worktree list`), other checkouts of the same repo.

**Other sessions' artifacts are attributed, never claimed** — report them as
parallel work ("a locked sibling worktree … belongs to a parallel session"), and
**never** offer them for cleanup. That guards the read-only contract.

**Live-session variant.** When the session is active (a "where are we" recap-now,
not a cold return), render the cockpit age as ⏱ *active now*, end the timeline
with *Now:* instead of *Ended:*, and let the delta cover parallel work rather than
away-time.

## Choosing the zoom tier

Fit the recap to the session. Render only non-empty lanes; a section with nothing
in it is omitted (but its absence is *stated* where a reader would expect it).

Pull day-level activity stats before picking — stats only, you choose the tier,
the script doesn't:

```bash
python3 <skill-dir>/scripts/transcript_digest.py --days
```

This emits per-day activity, gap-split at >4h: date, span, turn count, prompt
count — the material for telling Tiny from Normal from Long/multi-day, and for
the milestone grain the Long tier's overview table coarsens to.

- **Tiny** — a short, near-clean session. Collapse to the cockpit line plus a few
  lines; drop the counts line; fold Context inline. (See the worked example.)
- **Normal** — item-level: stream blocks, Done, and the worklist tables.
- **Long / multi-day / many-milestone** — lead with a **milestone-overview table**
  (each milestone → its **repo** + **PR (full URL)** + status), then detail only
  the live milestone(s); merged ones stay one line each. Add the explicit
  **discrete-PRs-vs-one-long-branch callout** — resume one PR alone, or resume the
  whole branch — it's the key resume fact. PR numbers are repo-ambiguous, so the
  overview always carries the repo column and a bulleted full-PR-URL list.

**The law that governs every tier — asymmetric coarsening** (it also governs the
plan-spine roll-up and the timeline grain cap): *when detail outgrows the
container, the container stays the same and the unit coarsens — but only ✅ done
work rolls up; blocked, in-progress, and remaining items stay fine-grained and
highlighted at every tier.* You never cut content to fit; you coarsen the grain of
what's finished (events → milestones) and keep the live edge sharp.

## Line grammar

Seven rules govern every rendered line. They apply recap-wide.

1. **LG1 · Annotate only when non-obvious.** `value — annotation`, and the
   annotation must say something the value doesn't. (`#212 — open, changes
   requested` passes; `feat/billing-metering — feature branch, not main` fails —
   the name already says it.)
2. **LG2 · Status is a colored dot + plain words.** `🔴 failing` / `🟢 passing`
   / `🟡 running` — one glance; never glyph stacks (`🛰 ✗ red` retired).
3. **LG3 · No unglossed symbols.** A bare glyph or shorthand — a section-mark
   before a name, a lone code — is always spelled out: render it as
   `— "Rollup" section`, never the raw token. The `—` separator is the universal
   value/annotation joint.
4. **LG4 · Hanging indent.** Wrapped content aligns under the content column,
   never back under the labels.
5. **LG5 · Provenance by zone.** The facts block is live-by-nature — one footer
   line (`Live state (PR, CI, tree) checked just now.`) carries it once; only
   🤔 inference is still marked inline. Per-line 🛰 markers are retired there.
6. **LG6 · Self-explanatory prompts.** Every ID is glossed where it appears; a
   zero-context reader can act on the prompt alone. (LG1 and LG6 are one test at
   two scales: *could the reader act on this line alone?*)
7. **LG7 · Distinct content classes in one cell are separated by a blank line.**
   A decision and its `Context:` anchor don't touch — the anchor gets a blank line
   above it. A same-fact continuation (a URL directly under its ref) stays
   adjacent. Markdown pipe-table syntax can't express an in-cell blank line — use
   a `<br>` if the renderer honors it, otherwise fall back to no separation; the
   box form is the target.

## The report

The recap must be **visually distinguishable** from the surrounding conversation:
it opens with its 🧭 cockpit line and closes with the 🏁 verdict, with nothing of
the recap outside those bounds.

**Never wrap real recap output in a code fence.** Emit **markdown pipe tables** —
the harness renders them as full box-drawn tables (`┌─┬─┐`) inline, and that
rendered box form is the design target. Emit **real bold** (`**verb**`) for
timeline lead verbs and emphasis. The mockups in this skill are shown fenced and
plain only so their raw structure is legible; fencing real output suppresses
table and bold rendering and degrades the recap to raw pipes.

**IDs are a reply grammar.** Every actionable row carries a class-prefixed ID —
`O#` in-flight · `D#` decision · `W#` committed work · `C#` cleanup · `S#` idea —
numbered within its class in the order rows appear. They let the user answer in
shorthand ("settle D1, defer W2, keep S1") and let one item reference another by
ID. **One item, one home:** an owed item lives in exactly one class table; stream
blocks and the close reference it by ID ("blocked on D1"), never by restating it.
A reply-ID is trustworthy only if it resolves to exactly one row.

**Assembly skeleton** (render order):

```
🧭 Opening zone   (cockpit → TL;DR → ⏸/👉 → 🛰 → 📍/🗺)
──── 🕓 THE PAST — what happened ────
  1 · 🧵 Timeline
  2 · ✅ Done
  3 · 🗣 Discussed
──── 🎯 THE WORKLIST — what's left ────
  4 · ❓ Decisions
  5 · 🔧 In flight        (stream blocks)
  6 · 📌 Committed · not started
  7 · 🧹 Cleanup
  8 · 💡 Ideas
🏁 Close
```

- **Dividers, verbatim:** `──── 🕓 THE PAST — what happened ────` and
  `──── 🎯 THE WORKLIST — what's left ────`. The hard line between the immutable
  PAST (read it to *remember*) and the actionable WORKLIST (read it to *act*) is a
  genuine labeled visual divider, not a soft grouping.
- **Numbering** is continuous 1–8 across the two zones; headers are numbered;
  cross-references are by **ID only** — numbered section *headers* aid navigation,
  but never write "see section 6."

The anatomy of each element follows.

### Opening zone

A stacked cockpit sized by time budget: which session / how stale / what's on fire
(3 sec) → the story (30 sec) → what was interrupted / what's first (30 sec) → what
moved while away (60 sec) → where the work lives (60 sec).

**Cockpit — one line, then a counts line:**

```
🧭 <title> · ⏱ <age> · <dot> <State> — <specific reason naming the gating ID>
   2 repos · 1 decision open · 1 in flight · 2 committed · 1 cleanup
```

A fact rides the cockpit line only if it changes how you read everything below.
The counts line renders at normal tier and auto-drops at tiny tier. If the reason
clause makes the line wrap badly, fall back to a two-line split (title+age / state).

**State vocabulary — dots only, reason clause mandatory:**

- 🔴 **Blocked** — a decision/conflict only you can clear.
- 🔵 **In progress** — mid-flight, nothing external in the way.
- 🟡 **Waiting** — external has the ball (CI, review).
- 🟢 **Ready** — done; only the ship action remains.
- ⚪ **Clean** — nothing open; close.

**TL;DR** — prose, never an enumeration. Tell the story (what happened, where it
stands) and land on the most decision-relevant fact, including the one open
decision.

**⏸ Left off** — renders **only when an interruption exists**. Anatomy: the item
(ID + name) + its half-state + the cause + staleness. The lines are independent of
👉 Start here.
`⏸ Left off: the rollup job (O1) — half-written when the CLI cleanup pulled you away; untouched since.`

**👉 Start here** — the FIRST action only, IDs glossed, with a specific why-first.
The full path lives in the close.
`👉 Start here: settle D1 (rollup granularity) — it unblocks O1 and, with it, PR #212.`

**🛰 Since you left** — render only when the away-time/parallel delta is nonzero.
The news that amends the story: PR comments, upstream moves, CI re-runs, sibling
worktrees.

**📍 Context / 🗺 Scope** — hoist shared facts here so they live *once*, never
repeated per item. Single repo → a **📍 Context** block (repo · branch · state ·
shared refs). Multiple repos → a **🗺 Scope** map (each location: path · branch ·
state) with a goal-grouped body carrying per-item `[repo]` tags; use a repo-first
body only when the repos are fully independent. Stream-specific refs ride on their
stream, not here.

**Order:** cockpit → TL;DR → ⏸/👉 → 🛰 (only when the delta is nonzero) → 📍/🗺 —
news right after the story it amends; stable lookup last.

**Tiny tier:** cockpit + a fused TL;DR whose final sentence carries left-off and
start-here together; Context collapses inline; counts drop.

### 1 · 🧵 Timeline

Zone: PAST. **Narrative only** — beats *narrate* what the streams *expand*; one
fact, two jobs, no duplication.

- **Beat admission** — a beat is a *turn in the story*: a new goal, a direction
  change, an interruption, a stop. Not a commit log; consecutive same-thrust work
  is one beat.
- **Shape** — an intro sentence → bulleted beats with **bold lead verbs**
  (`**Reviewed**`, `**Built**`, `**Started**`) → a closing line. Reads as a story,
  not keyword beats.
- **Anchors — light refs only.** IDs and PR numbers inline, **no URLs** (the
  worklist owns URLs). Every beat gets a handle into the worklist without importing
  its content.
- **⏸ beat marker** — the beat where the thread dropped carries a trailing ⏸,
  matching the cockpit's `Left off:` glyph.
- **Side-quest roll-up** — completed side quests share one beat; one that carried a
  decision or learning keeps its own (consequence overrides size).
- **Sub-bullets = sequence only** — ordered stages get sub-bullets; parallel
  components stay inline.
- **Grain cap: ≤ ~7 beats at every tier.** When a session outgrows the cap,
  coarsen the grain (events → milestones, mirroring the milestone table) — never
  cut content.
- **Closing line** — `Ended:` (cold return) / `Now:` (live variant): one sentence
  handing off to the worklist.

### 2 · ✅ Done

Zone: PAST. Answers "what landed this session, and where do I find it again?" —
acknowledgment plus inventory.

- **Membership** — only **fully-done workstreams** and loose done items. A *live*
  stream's landed items appear in **its plan spine** in the worklist, not here —
  one fact, one home. **State the absence** in the section description ("the live
  stream's landed items appear in its plan spine below").
- **Structure, adaptive** — multi-workstream → grouped blocks with header
  `▸ <name> (+ ID range when tracked) · <repo — only when multi-repo>`; a single
  uniform workstream → one box table (`✓ | What landed`).
- **IDs — natural only, never minted.** No reply-IDs (nothing here is actionable),
  but identifiers that already exist — project/task IDs (`P01`–`P08`), tickets
  (`ACME-991`), PR numbers, version tags — are kept; they identify the work.
- **URLs** — in block form, on a continuation line under the item. In table form,
  keep cells tight and add a **references addendum** under the table mapping
  natural IDs → homes (`Refs: P01–P08 → PROJECTS.md · …`); omit it when there's
  nothing worth mapping.
- Items are **verb-led sentences with concrete deltas** — *"reordered 5 projects:
  P09…, P10…"*, not *"reprioritized roadmap."*

### 3 · 🗣 Discussed

Zone: PAST, zone-level section. The reasoning trail — what was weighed and why —
as **stream-prefixed bullets**. Any **unresolved** output surfaces as a ❓ decision
in the worklist (don't leave a fork buried in prose). Inferences carry 🤔 and are
hedged.

### 4 · ❓ Decisions · 6 · 📌 Committed · 7 · 🧹 Cleanup · 8 · 💡 Ideas (owed tables)

The four owed classes render as counted box tables. Each row is one owed item with
a proof; **no proof, no row.**

**What a row is, and the question each column answers:**

- **❓ Decisions** — a fork only the user can settle.
  `ID | The decision | What's waiting on it | Recommendation`.
  Give a real recommendation (a pick with the reason it wins), not a restatement.
  Context anchors live **in-cell** as a `Context:` line, blank-line separated
  (LG7). Blocking rows sort first (impact order).
- **📌 Committed · not started** — work agreed to, nothing written.
  `ID | Committed work | Proof it was agreed | Next move`.
  Proof = an in-session quote, a probe output, or a standing instruction.
- **🧹 Cleanup** — needs clearing, not work.
  `ID | Artifact | Evidence | Recommendation`, the recommendation **argued in both
  directions** (`Clean — why safe` / `Keep — why it should survive`).
- **💡 Ideas** — floated, never agreed to.
  `ID | Idea | Where it came from | Size` (stream ref in the origin cell).
  Description: "floated, never agreed to — recorded so they don't evaporate; none
  is an obligation."

**Rules:**

- **Column density.** A fact earns a *column* only when dense (present in nearly
  every row) — columns are paid by every row. Sparse facts (a Context anchor) are
  **in-cell lines**, paid only where used.
- **Section header** `N · <emoji> <Name> — <count>` plus a one-line description
  teaching the section's semantics ("no proof, no row"; "argued in both
  directions"). A single obvious section may skip the description.
- **A single row still gets the full box table** — the format never shifts.
- **Prompt placement — one `▶` per independent action.** Under each table, place
  the launch(es): batch items a single skill handles as a pile
  (question-walkthrough, session-loose-ends) into one glossed prompt; skip
  passenger items that ride another item's action; add the raw-command alternative
  when one exists (`or just: git worktree remove …`). Payloads obey LG6 (every ID
  glossed). **An actionable table with no `▶` under it is a defect.**

### 5 · 🔧 In flight — stream blocks

Each in-flight stream renders as a block in this canonical structure (spacing
exactly as the worked example):

1. **Header:** `▸ <emoji> <ID> · <name> — <subtitle>   [kind · flag]`
2. *(blank line)* **Description:** 1–3 plain-language sentences — what it is, and
   why / impact when it matters. Lead with the description, before labels or
   anchors.
3. *(blank line)* **Facts block** — an aligned label column, where-first order:
   `Repo` (name + local path, inline while short) · `Branch` · `PR` (state
   annotation; URL on a continuation line) · `CI` (LG2 dot; name the failure at
   the most specific one-line level) · `Local changes`
   (`N files — not committed, so not in the PR`) · `Spec` (path — "section" gloss)
   · `Ticket` (ID — title; URL below). Footer: `Live state (PR, CI, tree) checked
   just now.` **Field admission test:** a field earns its slot only by answering a
   specific re-entry question — where do I `cd`, which branch, how does it ship, is
   it passing, is anything losable, where's the source of truth.
4. **Plan spine** — only when a plan of record exists; **absence stated**. Header
   `Plan — from <source>` naming the checklist's origin. Default form: the box
   table `Plan item | What it is | Status` with statuses spelled out (✅ done ·
   🔄 in progress · ⬜ not started · ✗ blocked). **Roll-up rule:** finished
   minutiae compress into one counted row with names kept in the description; live
   or blocked items never roll up, however small (asymmetric coarsening). Footer
   count: `N done · N in progress · N not started`. **Compact fallback** for the
   tiny tier or ≤3-item plans: a label column (`Done` / `In progress` /
   `Not started`) + sentence content + hanging indent.
5. *(blank line)* **Launch:** `▶ Prompt — paste this to <outcome, natural
   language>:` + a quoted multi-line body in full sentences, every ID glossed
   (LG6), ending with a done-when. Skill launches use the identical header grammar
   with a `/skill` payload.

### 🏁 Close

The close is `🏁 Close — <verdict>.` (Continue or Close), then:

- The **critical path** — the ordered chain to the next shippable state, by ID
  (`D1 → finish O1 → green CI → merge`). Recommend **Close** only when the tree is
  clean, work is pushed/merged, the PR (if any) is resolved, and nothing is
  mid-flight; otherwise **Continue**.
- The **parked list** — items deliberately set aside, by ID with the one-word why
  (`Parked: W1 (waits on D2) · C2 (keep) · S1 (idea)`).
- A **`reader-steps` block** — the final next moves as outcome-titled steps grouped
  by surface, each carrying its self-contained launch as the command with a
  `✓` / `Done when:` line, scaled per the `reader-steps` skill (inline → medium →
  full block). **If `reader-steps` is unavailable, fall back to a plain numbered
  list** with the same launches.
- **Decisions are never steps.** When every next move is a decision, no steps
  render — the close is the verdict plus the ask.

## Launch prompts

Every actionable row ends with a `▶` launch; pick the vehicle by class, and keep
the payload self-contained so it works even pasted **cold**. Use the header
grammar `▶ Prompt — paste this to <outcome>:` on each.

| Class | Vehicle | Example |
|-------|---------|---------|
| ❓ Decision `D#` | `/question-walkthrough` | `▶ Prompt — paste this to settle D1: /question-walkthrough "D1 — P09 metering rollup shape: one job vs per-tenant jobs. Blocks W1. Compare single vs multi, then pick."` |
| 💡 Idea `S#` | `/project-add` | `▶ Prompt — paste this to keep the idea: /project-add "backfill historical usage → UsageEvent store (large, unscoped)"` |
| 🧹 Cleanup `C#` | `/session-loose-ends` | `▶ Prompt — paste this to clear C1: /session-loose-ends "C1 — remove merged worktree acme-api-hotfix"  ·  or just: git worktree remove acme-api-hotfix` |
| 📌 Committed `W#` | `/writing-plans` | `▶ Prompt — paste this to plan W1: /writing-plans "W1 — build the P09 metering rollup per D1's shape; target ~/c/acme-api"` |
| 🔧 Open `O#` (resume) | continue-prompt | `▶ Prompt — paste this to resume O1: "finish O1 rollup job jobs/rollup.py:40; resolve D1 first; test_rollup red"` |
| ✗ Red CI | `/ci-audit` | `▶ Prompt — paste this to fix CI: /ci-audit "test_rollup failing on PR #212 (acme-api)"` |
| ✅ PR ready / comments | `/pr-merge-flow` | `▶ Prompt — paste this to merge PR #212: /pr-merge-flow "resolve review comments then merge PR #212 (acme-api)"` |

Prefer a `/skill` when the class maps to one; otherwise a quoted continue-prompt.
Launches sit **directly beneath** their table or item — an actionable table with
no `▶` line under it is a defect.

## Worked example

These mockups are shown fenced and plain-text only so their raw structure is
legible. **Real output is never fenced**: emit markdown pipe tables (the harness
draws the boxes) and real bold (`**verb**`).

**Tiny single-repo collapse** — the whole recap folds to a cockpit and a few
lines:

```
🧭 Fix flaky test_login · ⏱ 3h ago · 🟢 READY — CI green, PR approved
👉 merge PR #91, then delete the branch (both safe).
  ◆ O1 · Flaky test_login — retry-once wrapper on the auth mock; green 10/10. Done.
  ◇ C1 · 🧹 branch fix/login-flake — approved + green → merge, then delete.
🏁 Close after merge. Nothing else open.
▶ Prompt — paste this to merge PR #91:
  /pr-merge-flow "resolve any comments and merge PR #91 (acme-api); delete branch fix/login-flake"
```

**Stream block** — the canonical in-flight block (facts block, continuation-line
URLs, plan spine, glossed prompt). In real output the plan table renders as a
box-drawn table and lead labels render bold:

```
▸ 🎯 P07 · Billing v2 — usage-based pricing   [milestone]

  Update to the billing system to increase reliability of the brittle
  transaction service. Metering store landed; the rollup job is
  mid-write, gated on decision D1.

  Repo         acme-api  (~/c/acme-api)
  Branch       feat/billing-metering
  PR           #212 — open, changes requested
               https://github.com/acme/acme-api/pull/212
  CI           🔴 failing — test_rollup, on the sliding-window path
  Local changes  2 config files — not committed, so not in the PR
  Spec         docs/specs/2026-07-18-billing-v2.md — "Rollup" section
  Ticket       BILL-400 — usage-based pricing epic
               https://linear.app/acme/issue/BILL-400

  Live state (PR, CI, tree) checked just now.

  Plan — from PROJECTS.md P07
  ┌───────────────────────┬───────────────────────────────────────────┬────────────────┐
  │ Plan item             │ What it is                                │ Status         │
  ├───────────────────────┼───────────────────────────────────────────┼────────────────┤
  │ UsageEvent model      │ event-sourced store for billable usage    │ ✅ done        │
  │ metering middleware   │ emits a UsageEvent per billable API call  │ ✅ done        │
  │ pricing config        │ per-plan rates the rollup prices against  │ ✅ done        │
  │ rollup job            │ aggregates events into invoice lines (O1) │ 🔄 in progress │
  │ invoice renderer      │ turns rollups into customer invoices      │ ⬜ not started │
  │ rollup + invoice tests│ coverage for rollup + renderer            │ ⬜ not started │
  └───────────────────────┴───────────────────────────────────────────┴────────────────┘
  3 done · 1 in progress · 2 not started

  ▶ Prompt — paste this to finish the rollup job (O1):
    "Resume work on Billing v2 in the acme-api repo. The open item is
     O1, the rollup aggregation job — it turns metered usage events
     into invoice lines, and is half-written at jobs/rollup.py:40.
     Before coding, settle decision D1: should rollups aggregate daily
     or hourly? (Context: docs/specs/2026-07-18-billing-v2.md, the
     'Rollup' section.) Done when the failing test_rollup goes green."
```

## Red Flags

| Thought | Reality |
|---------|---------|
| "It's a good idea — put it in the next steps" | They never agreed to it. It goes in 💡 Ideas. Promoting it invents an obligation they never took on. |
| "They'd probably want this — call it committed" | 📌 requires a quotable assent (or a standing instruction cited as proof). No proof → 💡. The whole value of 📌 is that it's a backlog you can trust. |
| "Nothing outstanding — just leave the section out" | Omit the body, keep the trace. A silent absence reads as "didn't check", which is the exact bug the stated-absence rule fixes. |
| "The close and the tables overlap a bit" | The close cites IDs only. The same item appearing twice in different words is a defect. |
| "It's half-written, so it's committed-not-done" | Started work is 🔧 in flight. 📌 is what's owed and untouched. The test is whether anything has been written. |
| "A branch exists, so it's open work" | Only if someone still has to *work* on it. A merged branch's worktree needs clearing, not working — 🧹 wins ties. |
| "I'll wrap the recap in a code fence so it's tidy" | Fencing suppresses table and bold rendering — the boxes degrade to raw pipes and read as incomplete. Never fence real output. |
| "I'll point back with a `see section 6` cross-reference" | No section-number cross-references. Items reference each other by **ID** (`W1`, `D1`) only; numbered *headers* are for navigation. |
| "I'll mint an ID for this done item" | Done work gets **natural IDs only** — existing project/task IDs, tickets, PR numbers, tags. No reply-IDs; nothing there is actionable. |
| "The state is obvious — state it without the reason" | The cockpit state always names its reason clause (the gating ID). A dot with no reason hands back a shrug. |
| "The annotation can just repeat the value" | LG1: annotate only when the annotation says something the value doesn't. `feat/billing — feature branch` is noise. |

## See also

- `session-loose-ends` — the acting sibling: when the user wants only the
  actionable dangling items *cleaned up* (with per-item confirmation), not the full
  orientation story, route there. This skill stays read-only. It reports the same
  owed classes (❓ 📌 🧹 💡) with the same IDs, so a recap's `C1` is the same item
  loose-ends will offer to clean.
- `question-walkthrough` — where ❓ Decisions hands off; it settles a pile of open
  questions one at a time.
- `project-add` — where 💡 Ideas hands off; captures an idea as a project stub so
  it survives the session.
- `reader-steps` — the format the 🏁 Close uses: outcome-titled steps grouped by
  surface, each carrying its self-contained launch with a `✓` / `Done when:` line.
- `writing-plans` — the 📌 Committed handoff vehicle; turns an agreed-but-unwritten
  work item into a plan.
