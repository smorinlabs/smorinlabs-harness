---
name: session-status
allowed-tools: Read, Glob, Grep
description: Mid-flight progress check for the ACTIVE stream of work — a fast, plain-language "you are here" map of what the work is, what's done, what's in progress, and what's left, scaled to the shape of the work. Manually triggered only — fire on /session-status or an explicit ask like "session status", "status check", "give me a status", "how far along are we"; never ambiently. Flat work → every task as a plain sentence with its ID; phased work → a named phase map, heavy detail only on what's left in the current phase, one line for the rest; done always rolls up. Reads the plan of record (PROJECTS.md, projects/, task lists, plan docs) plus the conversation; read-only and probe-free — never mutates, never runs tests, never hits git/PR/CI. NOT for returning cold to an idle or compacted session or full orientation with live git/PR probes (session-recap), not cleanup (session-loose-ends), not picking what to work on next (project-next).
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
  launch prompts, no close-or-continue verdict. One status ledger, then stop.

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
column and hanging indents as shown.

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
