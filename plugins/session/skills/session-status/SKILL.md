---
name: session-status
allowed-tools: Read, Glob, Grep
description: Mid-flight progress map of the active work, covering what it is, what is done, in progress, and left, read from the plan of record and the conversation without running probes. Adds an ASCII kanban board of what is left when work runs in parallel or much remains. Manual only, fire on /session-status or an explicit "status check", "how far along are we", or "show what's left as a board". Not for returning cold to a session (session-recap).
---

# session-status

A fast, plain-language "you are here" for the stream of work that is active
right now — how much is done, where you stand, and what's left, at the zoom
level the work's own structure calls for.

## Contract

- **Manual only.** This skill fires on an explicit invocation or a direct
  status ask made mid-work. Ambient disorientation — "where was I", "catch me
  up", a user returning cold — routes to `session-recap`, always.
- **Read-only and probe-free.** Observe, never mutate; never run the test
  suite; never probe git, PRs, or CI. Status comes from the plan of record and
  the conversation. This is what keeps it a glance instead of a recap — if
  live state matters, that's `session-recap`'s job.
- **A glance, not a recap.** No owed-item classification, no proof quotes, no
  launch prompts, no close-or-continue verdict. One status ledger (with its
  board, when the board rule includes one), then stop.

## The two laws

Everything in the output obeys these; they are the skill.

1. **Plain language, always.** Every line must be actionable by someone who
   wasn't in the session: say what the thing *is* and where it stands in
   ordinary words. IDs annotate — they are never the content. Never echo a
   task title; translate it. (`T04 codex placements` fails; `T04 — the codex
   copies: links are moved, the ledger records still need writing` passes.)
2. **Asymmetric detail.** Done work rolls up — tasks compress to counts,
   counts to phase names, a finished phase to one line. What's *left* stays
   fine-grained, but only where you're standing: the current area itemizes
   everything remaining with enough detail to act; sibling areas get a count
   and a one-liner; later phases get their name and one plain line. Detail is
   spent where the reader's next hour goes, nowhere else.

## Gathering (quiet — do not narrate)

1. **The active stream** — from the conversation: what's being worked on right
   now, down to the current task.
2. **The plan of record** — the checklist that says what the whole effort is:
   a PROJECTS.md entry, a projects/ file, a task list, a plan doc, or an
   in-chat agreement. Name the source in the footer (`from PROJECTS.md P21`).
   If none exists, reconstruct the list from the conversation and say so
   plainly — `no tracked plan; reconstructed from this conversation` — never
   presenting reconstructed counts as tracked ones.
3. **Statuses** — from the plan's own marks plus what the conversation shows
   has happened since. Where they disagree (work done but never checked off),
   report the truer state and note the drift in one clause.

## Choosing the tier

The work's structure picks the tier — never ask:

- **Small** — a flat task list (no grouping). Every item renders, each as a
  plain sentence with its ID — a flat list is already minimal, so there is
  nothing for Law 2 to roll up.
- **Medium** — one level of grouping. Done groups compress to counts;
  untouched groups itemize, because they are what's left.
- **Large** — two or more levels (goals/phases containing projects containing
  tasks). Open with a big-picture map naming every phase with its rough size
  and state, then zoom: heavy detail on what's left in the current phase, one
  line each for the others.

## The ledger

One grammar at every tier — plain-sentence items, labeled zones, a counts
footer. The zones differ by tier:

- **Header** — `📊 Status — <ID> · <the work, in plain words>` plus counts.
  At the Large tier the header also carries the position path
  (`you are in Phase 2 › P07 › T04`).
- **Small and Medium** use the flat label column `The work` / `Done` / `Now`
  / `Left`. `Now` carries the most detail per item: what works, what's open,
  what the sticking point is. Items under `Left` render in execution order
  when the plan implies one, not ID order.
- **Large** — the flat column can't hold a hierarchy, so it becomes four
  zones in this order: `Big picture` (every phase named, with its size and
  state), `The work` (where you are, in plain words), `Left in <current
  phase>` (the fine-grained zoom: the current project's tasks itemized,
  sibling projects one line each), then `Later phases` and `Done, rolled up`
  (one line each). Same laws, same glyphs, same footer.
- **Footer** — `N done · N in progress · N left` at the grain of the current
  focus, the plan-of-record source, and the single next thing with one
  clause of why.
- Glyphs: ✅ done · 🔄 in progress · ⬜ not started — at every tier,
  including the phase map. Hanging indent: wrapped text aligns under the
  content column, never back under the labels.

The mockups below are fenced only so their raw structure is legible — **real
output is never fenced** (fencing degrades rendering); keep the aligned label
column and hanging indents as shown. The one exception is the board's grid
(see *The board*). The Medium and Large mockups show the zones without a
board; at their sizes the board rule fires, and *The board* shows the same
two examples as they actually render.

**Small** — flat list, every task explained:

```
📊 Status — P12 · CSV export command (5 tasks)

The work   Let people export reports as CSV files from the CLI.
Done       ✅ T01 — the column layout for the CSV is decided and locked
           ✅ T02 — each report row can now be turned into a CSV line
Now        🔄 T03 — writing rows out as a stream so big files don't
              load into memory. Works, except files over ~1M rows
              still buffer everything — that's the open bit.
Left       ⬜ T04 — hook it up: add the --csv flag so people can
              actually call it (small)
           ⬜ T05 — write the docs and a couple of examples (small)

2 done · 1 in progress · 2 left — from PROJECTS.md P12.
Next: after T03, T04 makes the whole flow runnable end to end.
```

**Medium** — one grouping level; done compresses, the untouched group
itemizes:

```
📊 Status — P21 · Auth revamp (12 tasks in 3 groups)

The work   Replace login cookies with short-lived tokens that
           refresh themselves.
Done       ✅ T01–T04 — the token system itself: creating, signing,
              and storing them
           ✅ T05–T07 — the checks that run on each request now
              accept tokens
Now        🔄 T08 — renewing tokens quietly before they expire. One
              open edge case: two tabs renewing at the same moment.
Left       ⬜ T09 — accept BOTH cookies and tokens for a while so
              nobody gets logged out
           ⬜ T10 — move everyone currently logged in over to tokens
           ⬜ T12 — write the undo plan first, then
           ⬜ T11 — turn the old cookie path off

7 done · 1 in progress · 4 left — from PROJECTS.md P21.
Next: T09 — the switchover is untouched and it's the risky one.
```

**Large** — phase map first, zoom on the current phase's remainder:

```
📊 Status — G2 · Fleet consolidation · you are in Phase 2 › P07 › T04

Big picture — 4 phases
  Phase 1  Foundations   ✅ done (4 projects)
  Phase 2  Migration     🔄 you are here — 3 of 6 projects done
  Phase 3  Docs parity   ⬜ 6 projects, not started
  Phase 4  Release       ⬜ 2 projects, not started

The work   Phase 2 moves every skill's install links onto the new
           ledger. You're in P07, task T04.

Left in Phase 2 — the detail that matters now
  P07 · moving every skill's install links onto the new ledger
      🔄 T04 — the codex copies: links are moved, the ledger
           records still need writing
      ⬜ T05 — the same move for the kilo-code and opencode copies
      ⬜ T06 — prove every skill still loads on all four tools
  P08 · deleting the old install paths — 3 tasks; can't start
       until T06 proves nothing still depends on them
  P09 · alarms that catch this drifting again — 2 tasks,
       independent, could start any time

Later phases, one line each
  Phase 3 — per-skill pages + README rows for everything migrated
  Phase 4 — version bump + marketplace release, gated on Phase 3

Done, rolled up: Phase 1 entirely; P05, P06, P10 within Phase 2.

In Phase 2: 3 projects done · 1 in progress · 2 left — from
PROJECTS.md G2. Next: finish T04's ledger records — T05 and T06
repeat the proven move, so T04 is the only real unknown left.
```

## The board

An ASCII kanban of what's left, drawn inside the ledger when the shape of the
work calls for one. It shows how the remaining work sits relative to itself —
what runs side by side, what waits on what — which a list can only describe.
The same two laws govern it: cards speak plain language, and done work never
gets a column.

### When it appears

Decide on every run from the plan and the conversation — never ask. Include
the board when **any** of these holds:

- two or more pieces of work are moving at once — parallel phases, projects,
  subagents, or worktrees;
- five or more items are left in the current focus;
- the plan states dependencies that decide the order — something waits on
  something else;
- the user asks for a board or a kanban.

Leave it out when everything left is one sequential line of four or fewer
items (the `Left` list is already a glance), when one item is left, or when
the user asks for a brief status or says "no board". The user's words
override the rule both ways.

### Which columns

Take the first source that applies:

1. **The plan's own status words** — when the plan tracks three or more
   not-yet-finished states that say more than started / not started (for
   example PROJECTS.md projects at `[~]`, `[ ]`, `[?]`, or a plan with
   review or QA stages). Each such state becomes a column named in capitals
   (`[~]` → IN PROGRESS, `[ ]` → SCOPED, `[?]` → IDEAS), ordered from
   closest to done to furthest. Finished and retired states (`[x]`, `[-]`,
   `[>]`) go to the Done line, never a column.
2. **Otherwise the default** — `NOW │ NEXT │ LATER │ BLOCKED`:
   - NOW — in progress, per the plan or the conversation.
   - NEXT — what starts as soon as a NOW item frees up: the next item in
     execution order in each lane that has something in NOW.
   - LATER — not started, not gated, not next.
   - BLOCKED — waits on an unfinished item that the plan or the
     conversation names as a gate ("X first, then Y", "can't start until
     X"). Merely following the item before it in list order is LATER, not
     BLOCKED. The card names what it waits on.
3. **BLOCKED is always available.** When the plan's own words have no
   blocked state but a stated dependency exists, add the column anyway.

At most four columns, so the board fits in 80 characters. Fold any extra
plan state into its nearest column and tag those cards with their state. Drop
empty columns, except the one holding current work. Cards inside a column
follow execution order when the plan implies one.

### Which layout

- **One line of work** — one row of cards under the column headers.
- **Parallel work** — swimlanes: one horizontal lane per project, phase, or
  agent that runs alongside the others, labeled with its ID. Law 2 holds
  inside the board: a lane with work in progress itemizes its cards; a lane
  with nothing in progress collapses to one summary card with a count
  (`3 tasks: remove old paths; waits on T06`).

### Where it sits in the ledger

The board replaces the zones that list remaining work, so nothing appears
twice:

- **Small and Medium** — `The work` stays. The board takes the place of
  `Done`, `Now`, and `Left`, and a `✅ Done, rolled up:` line sits directly
  under it. Below that, one plain sentence for each card in the first two
  columns, under labels that take those columns' names (`Now` and `Next`
  on the default board) — Law 1's full sentences live here, since cards are
  too narrow for them.
- **Large** — `Big picture`, `The work`, `Later phases`, and `Done, rolled
  up` stay. The board replaces `Left in <current phase>`, drawn as one lane
  per project of the current phase. Plain sentences follow for the cards in
  the lane you are in.
- The header and the counts footer never change.

### Drawing rules

- **Fence the grid** — only the lines from the top border to the bottom
  border. Column alignment is the board's whole value and unfenced text
  reflows. Everything around it stays unfenced.
- Box-drawing borders (`┌ ┬ ┐ ├ ┼ ┤ └ ┴ ┘ │ ─`), 17 characters inside each
  column; swimlane labels take a 6-character gutter on the left.
- **No emoji inside the grid.** They render two characters wide in most
  terminals and shift every border to their right. Glyphs belong outside it,
  like the `✅` on the Done line.
- A card is its ID plus a short plain phrase, at most three lines — a
  compressed translation, never the task title. More than three cards in one
  cell: show three, then `+N more`.

**Medium, with the board** — the P21 example from *The ledger*:

```
📊 Status — P21 · Auth revamp (12 tasks in 3 groups)

The work   Replace login cookies with short-lived tokens that
           refresh themselves.

┌─ NOW ───────────┬─ NEXT ──────────┬─ LATER ─────────┬─ BLOCKED ───────┐
│ T08 renew tokens│ T09 accept both │ T10 move users  │ T11 retire old  │
│     quietly;    │     cookies +   │     onto tokens │     cookie path;│
│     2-tab race  │     tokens for  │                 │     waits on T12│
│     still open  │     a while     │ T12 write undo  │                 │
│                 │                 │     plan first  │                 │
└─────────────────┴─────────────────┴─────────────────┴─────────────────┘
✅ Done, rolled up: 7 — the token system (T01–T04), and the checks
   on each request (T05–T07)

Now        🔄 T08 — renewing tokens quietly before they expire. One
              open edge case: two tabs renewing at the same moment.
Next       ⬜ T09 — accept BOTH cookies and tokens for a while so
              nobody gets logged out

7 done · 1 in progress · 4 left — from PROJECTS.md P21.
Next: T09 — the switchover is untouched and it's the risky one.
```

**Large, with the board** — the G2 example's `Left in Phase 2` zone, drawn
as swimlanes (the zones around it are unchanged):

```
Left in Phase 2 — the board

      ┌─ NOW ───────────┬─ NEXT ──────────┬─ LATER ─────────┬─ BLOCKED ───────┐
 P07  │ T04 codex copies│ T05 kilo-code + │ T06 prove loads │                 │
      │     ledger recs │     opencode    │     on 4 tools  │                 │
      ├─────────────────┼─────────────────┼─────────────────┼─────────────────┤
 P08  │                 │                 │                 │ 3 tasks: remove │
      │                 │                 │                 │  old paths;     │
      │                 │                 │                 │  waits on T06   │
      ├─────────────────┼─────────────────┼─────────────────┼─────────────────┤
 P09  │                 │                 │ 2 tasks: drift  │                 │
      │                 │                 │  alarms; can    │                 │
      │                 │                 │  start any time │                 │
      └─────────────────┴─────────────────┴─────────────────┴─────────────────┘

  P07 · moving every skill's install links onto the new ledger
      🔄 T04 — the codex copies: links are moved, the ledger
           records still need writing
      ⬜ T05 — the same move for the kilo-code and opencode copies
      ⬜ T06 — prove every skill still loads on all four tools
```

In real output, only the grid lines in these mockups go inside a fence.

## Red Flags

| Thought | Reality |
|---------|---------|
| "The task title is short — just quote it" | Titles are jargon to anyone outside the session. Translate: say what it is in plain words; the ID rides along. |
| "Show everything that's done — it's satisfying" | Done rolls up to counts and names. The reader orients on what's left; finished detail buries it. |
| "More detail everywhere is more helpful" | Asymmetric detail: fine grain only where you stand. Uniform depth makes the current phase's real work invisible. |
| "The user seems lost — fire this" | Lost routes to `session-recap`. This skill fires only on an explicit status ask, mid-flight. |
| "Quick git probe, just to be sure" | Probe-free is the contract. Plan of record + conversation, nothing else — live state is `session-recap`'s job. |
| "Round it to a clean percentage" | Counts come from the plan of record. No invented numbers; a reconstructed plan says it's reconstructed. |

## See also

- `session-recap` — the heavyweight sibling: cold returns, full orientation,
  owed-item tables, live git/PR/CI probes, close-or-continue verdict.
- `session-loose-ends` — when the ask is to *clean up* what's dangling, not to
  see progress.
- `session-handoff` — packaging the session forward for a fresh session.
- `project-next` — choosing *what* to work on from the portfolio; this skill
  reports progress *within* the already-active work.
