# session-agent-list — output format spec (v7, converged 2026-08-08)

This file is the single source of truth for the listing format. It is the
converged result of a seven-iteration design session; the "do not regress"
list at the bottom records the user corrections that produced it. Render from
this spec exactly — modes reorder or drop fields but never invent them.

All paths, session IDs, PR numbers, and worktrees in the examples below are
**fictional mock data** demonstrating the format. Never resolve or verify them.

## Jobs to be done (why this format exists)

The reader is finding a session (or sessions) in order to **access its data or
respawn it**. The format answers these questions, in priority order:

1. **Orientation** — How long ago? Claude Code or Codex? Spawned from another
   session (fork/child)? Started from a handoff?
2. **Triage by end state** — Open mid-work (the resume candidate), handed off
   (follow the doc, don't resume), or closed (leave it alone / clean up)?
3. **Action** — copy-paste commands to resume it or read its transcript.
4. **Context** — what it did: working set (worktrees ≈ working directories,
   possibly multiple repos) and a three-horizon story (hours / session / months).

Guiding principle: *the card doesn't just describe state, it changes which
actions it hands you* — a cleanly-closed session offers only its transcript,
never a resume command.

## The 21 elements

| # | Element | Example | Definition |
|---|---------|---------|------------|
| 1 | Ephemeral ID | `[1]` | Ordinal assigned at first listing, **stable within a conversation**: once a session is [3] it stays [3] across re-filters; new sessions keep counting up; filtered-out sessions leave gaps. "Open [3]" is always safe. Not stored beyond the conversation. Prominent in every format. |
| 2 | Session title | Fix skill symlink placements | Generated human-readable summary of what the session is about. |
| 3 | Literal session ID | `claude:37185d34` / `codex:rollout-2026-08-08T16-18` | The real identifier the tool knows the session by, prefixed with the tool. |
| 4 | Tool | Claude Code · Codex | Which agent CLI owns the session. |
| 5 | Relative time | 1h ago | Human-first "how long ago", keyed to **last activity**; always shown before the literals. |
| 6 | Time span | started 15:21 → last active 16:12, Fri Aug 8, 2026 (51m) | **Both** start and end (or "last active" if still open) plus duration. Sessions can be very long-running; a single timestamp is not enough. Multi-day form: `started Tue Jun 3 → last active Fri Aug 8 (66 days)`. |
| 7 | Spawn directory | `~/c` | Where the session was *launched*. First-class and separate from repos/worktrees — for Claude Code it is part of the resume address (session files are keyed by cwd). |
| 8 | Repos | `acme-api`, `acme-web` | Repo(s) the session worked on — **plural is the norm**; may differ from spawn dir. `—` if none. |
| 9 | Worktrees | ⑂ `~/c/…-placements` @ `fix/placements` | Worktree path(s) + branch(es) — **may be multiple**; one table row per repo/worktree pairing. Worktrees behave like working directories. |
| 10 | Subgroup | MO5 group, sessions [1]–[3] | Related sessions clustered under a shared milestone/topic header. Renders as the container, not on the card. |
| 11 | Lineage | ↳ fork of [1] "Fix skill symlink placements" | Fork/child of another session (shared transcript). Rendered as a labeled `lineage:` line using **title + ephemeral ID**, never the ID alone. |
| 12 | Work item (triple form) | HP02-33 (placement audit — the task verifying skill symlinks resolve for both Claude and Codex) | Never a bare ID. See ID-hygiene convention below. |
| 13 | Milestone / org context | MO5 (harness consolidation — the milestone folding all skills into one marketplace repo) | Same triple-form rule; defined once per group header, then referenced by plain name. |
| 14 | Resume command | `cd ~/c && claude --resume <uuid>` | Copy-pasteable respawn, tool-appropriate, in a highlighted bash block. Includes the `cd` (Claude Code resume is cwd-sensitive). |
| 15 | Session file path | `~/.claude/projects/-Users-alex-c/<uuid>.jsonl` | Path to the raw transcript, tool-appropriate layout, command-styled. Rendered as the **bare path** (no `less` prefix). |
| 16 | Lately (bullets) | three bullets, most recent first | The last three things going on — hours horizon. |
| 17 | TLDR | one/two sentences | What the session is, in one breath — session horizon. Explicitly titled `TLDR:`. |
| 18 | The longer arc | 2–3 sentences | Months-scale narrative: where this thread of work came from. |
| 19 | End status | ● / ⇥ / ✔ / ◒ | One of four closure states; on its own line under the title. See taxonomy. |
| 20 | End-state detail | "merged PR #87, removed worktree…" | The closing section: receipts for closed sessions; for open sessions, `left off:` + progress live in the header block instead. |
| 21 | Handoff origin | ⇤ from `claude:9a01c4e2` on `mbp-m1` · doc `<path>` | Inbound provenance: source session, source machine if different, handoff doc path. |

Non-worktree / no-history sessions collapse #16–18 to a single TLDR (gist).
The format decides by *whether there's a story*, not by card position.

## Glyph table (strict budget — each glyph owns exactly one meaning)

| Glyph | Meaning | Notes |
|---|---|---|
| `⑂` | worktree | Prefixes any worktree path. |
| `↳` | fork / child | Lineage with a *shared transcript* ("same thread, split"). |
| `⇤` | handoff in | Session was *seeded by* a handoff doc ("new thread, seeded"). |
| `⇥` | handoff out | Session *ended by producing* a handoff. Matched pair with ⇤ — makes baton passes trackable (a listing can show a handoff "in the air": written but not yet picked up). |
| `●` | open — mid-work | The resume candidate. |
| `✔` | closed — clean | Goal reached AND capped. |
| `◒` | closed — loose ends | Goal reached, cap missing. |

No other glyphs — scarcity is what keeps these legible. A new glyph requires a
removed one.

## End-state taxonomy + detection signals

| Badge | State | Meaning | Section it drives |
|---|---|---|---|
| `●` | open — mid-work | Ended mid-task. *The* resume candidate. | `left off:` (exact last thing) + progress (% done, what remains) in the header block |
| `⇥` | handed off | Final steps produced a handoff (prompted, or literally invoked `session-handoff`). Resuming is usually wrong — follow the doc. | End state: doc path, addressee, picked-up-yet status |
| `✔` | closed — clean | Goal reached and capped: PR merged (which #), milestone/task checked off (which), cleanup done (worktrees removed, scratch files gone). | End state: the receipts |
| `◒` | closed — loose ends | Goal reached but cap missing: worktree standing, files uncommitted, branch undeleted. | End state: what finished + exactly which loose ends |

**Detection signals** (classifier heuristics, in the transcript tail):

- `session-handoff` skill call or handoff-doc write in final turns → `⇥`
- `gh pr merge` / "merged #n" **plus** `git worktree remove` in the tail → `✔`
- The merge **without** the cleanup → `◒`
- None of the above → `●`
- Conflicting signals → state the evidence, never guess silently.

## Conventions

**ID hygiene (triple form).** Never a bare work-item ID. First mention:
`<ID> (<plain-language name> — <one-line definition in normal words>)`.
After first mention in a listing, plain name alone suffices. Group headers
define shared IDs (milestones) once; member cards then use the plain name.

**Time.** Human-first, and always a **span**: relative-to-last-activity, then
started → ended (or "last active"), then duration:
`1h ago — started 15:21 → last active 16:12, Fri Aug 8, 2026 (51m)`.
Long-running form: `2h ago — started Tue Jun 3 → last active 15:41 Fri Aug 8
(66 days)`. Times are plain prose, never code-styled (see color budget).

**Ordering & age bands.** Sessions are ordered *roughly* chronologically by
last activity, newest first — but within a group, **lineage clusters override
strict chronology**: a parent renders before its forks/children even if a
child is more recent (the golden example shows this: [1] precedes its fork
[2]). Groups and bands take their position from their most recent member. When
the result set spans the thresholds, the listing splits into clearly separated
**age-band sections** (bands appear only if sessions actually fall in them):

- `RECENT — within the last month`
- `1–3 MONTHS AGO`
- `OLDER THAN 3 MONTHS`

Age bands sit **above** groups in the hierarchy (a group whose sessions span
bands is listed in the band of its most recent session, with older members'
spans making their age visible). Band headers use the `══` rule so they cannot
be confused with group (`━━`) or card (`────`) separators:

```text
══ RECENT — within the last month ══════════════════════
   (groups and cards as normal)

══ 1–3 MONTHS AGO ══════════════════════════════════════
   …

══ OLDER THAN 3 MONTHS ═════════════════════════════════
   …
```

**Color/highlight budget** (terminal markdown channels; each channel means one
thing): headings = anchors; inline code = copyable/literal (paths, IDs, repo
names, branches); fenced `bash` = executable; **bold** = labels only; plain =
everything meant to be read. Rule: *color marks what hands use, weight marks
what eyes navigate by, plain is what the mind reads.*

**Delimiter ladder** (one mechanism per level, never mixed):

- `══` = age-band boundary (only when the listing spans the age thresholds)
- `━━` after a `##` heading = group boundary (groups defined by element #10;
  ungrouped sessions go under an `## Ungrouped` header)
- `────` full-width line = card boundary
- texture change + blank line = band boundary inside a card (adjacent bands
  never share a texture: heading → labeled lines → prose → table → code → prose)

**Listing header:** `FOUND <n> SESSIONS · ● 1 open · ⇥ 1 handed off · ✔ 2
clean · ◒ 1 loose ends` — end-state census up front. A filtered listing
names its scope in the census line — `FOUND 3 SESSIONS (query: flox pr) ·
…` — so a narrowed set is never mistaken for the whole machine. These
header rules apply to every listing view (default and all flag modes).

**Coverage footer (optional, one line, any listing view).** When candidates
were dropped by the filter or a source went unverified, one plain line at
the listing's end says what was dropped and how to widen — silent
truncation reads as full coverage.

## Band anatomy — final card ordering (v7)

1. `### [n] Title` — title only; no glyphs, no lineage on this line.
2. **Status line** — its own line: `` `●` **open — mid-work** ``. Fixed
   vertical rhythm: line 1 = name, line 2 = state, line 3 = place.
3. **`at:`** — resolved working location (worktree if any, else checkout),
   `· spawned from <dir>`. Label has a colon; ⑂ used when a worktree.
4. **`TLDR:`** — directly below `at:`.
5. Remaining labeled lines, each with its glyph, present only when applicable:
   - **`origin:`** ⇤ inbound handoff (source session, machine, doc path)
   - **`lineage:`** ↳ fork/child, as *title + ID*: `↳ fork of [1] "Fix skill
     symlink placements"`
   - **`for:`** work item / purpose (triple form)
   - **`left off:`** `●` only for open sessions — exact stopping point +
     progress
6. **Placement table** — 3 columns `Spawned in | Repo | Worktree`, one row per
   repo/worktree pairing, spawn cell filled on first row only. Multi-repo and
   multi-worktree are first-class.
7. **Identity line** — `**Tool** · \`tool:id\` · 1h ago — started 15:21 →
   last active 16:12, Fri Aug 8, 2026 (51m)`. Both endpoints always; for
   long-running sessions the span is the signal (`started Tue Jun 3 → last
   active Fri Aug 8 (66 days)`).
8. **Commands** — one bash block; **blank line between the two entries**;
   resume command first (with `cd`), then the **bare session-file path** (no
   `less`), each with a trailing `# comment`. Commands vary by end state
   (closed sessions get transcript only; handed-off sessions lead with the
   handoff doc and annotate resume as "usually wrong").
9. **`Lately:`** — three bullets, most recent first.
10. **`The longer arc:`** — months-scale narrative.
11. **`End state:`** — closes the card (chronological: history → how it ended).
    Prescriptive/descriptive split: *left off* (top) = what you'd do next;
    *End state* (bottom) = what actually happened.

## Golden example (mock data — every path/ID fictional)

──────────────────────────────────────────────────────────

### [1] Fix skill symlink placements

`●` **open — mid-work**

**at:** ⑂ `~/c/acme-api-placements` · spawned from `~/c`
**TLDR:** repairing every skill symlink that broke when a worktree was deleted, verified against both tools via a second worktree in `acme-web`. Forked by [2].
**origin:** ⇤ handoff from `claude:9a01c4e2` on `mbp-m1` · doc `docs/handoffs/2026-08-06-placement-repair.md`
**for:** HP02-33 (placement audit — the task verifying skill symlinks resolve for both Claude and Codex)
**left off:** `●` mid-draft of the PR body — sweep complete, PR not yet opened · ~90%: 14/14 skills re-linked, doctor clean; remaining: open PR, merge, remove both worktrees

| Spawned in | Repo | Worktree |
|---|---|---|
| `~/c` | `acme-api` | ⑂ `~/c/acme-api-placements` @ `fix/placements` |
| | `acme-web` | ⑂ `~/c/acme-web-verify` @ `chore/verify-matrix` |

**Claude Code** · `claude:37185d34` · 1h ago — started 15:21 → last active 15:41, Fri Aug 8, 2026 (20m)

```bash
cd ~/c && claude --resume 37185d34-a03d-47ae-be38-f29d5e2e5fb5   # resume

~/.claude/projects/-Users-alex-c/37185d34-a03d-47ae-be38-f29d5e2e5fb5.jsonl   # transcript
```

**Lately:**
- Drafting the PR body for the placement sweep
- the placement check ran clean after the full re-link
- Re-linked all 14 skills using the pilot-tested recipe

**The longer arc:** the consolidation push running since early June — folding the scattered service repos into `acme-api` as the single deployable. Third symlink repair since the migration began, first to also patch the verifier.

**End state:** `●` still open — this is the resume candidate; pick up at the PR body (see *left off* above).

──────────────────────────────────────────────────────────

### [2] Retry with tighter scope

`⇥` **handed off**

**at:** ⑂ `~/c/acme-api-retry` · spawned from `~/c`
**TLDR:** a narrow-scope fork of [1] that cornered the flaky gen-check — a stale lockfile — and handed the fix back rather than merging it itself.
**lineage:** ↳ fork of [1] "Fix skill symlink placements"
**for:** same task as [1] (the placement audit), narrowed to the gen-check flake

| Spawned in | Repo | Worktree |
|---|---|---|
| `~/c` | `acme-api` | ⑂ `~/c/acme-api-retry` @ `fix/placements-retry` |

**Claude Code** · `claude:be38f29d` · 45m ago — started 15:48 → last active 16:02, Fri Aug 8, 2026 (14m)

```bash
~/c/docs/handoffs/2026-08-08-gencheck-fix.md                     # the handoff — start here

cd ~/c && claude --resume be38f29d-5e2e-41b8-a03d-47ae37185d34   # resume (usually wrong; follow the doc)

~/.claude/projects/-Users-alex-c/be38f29d-5e2e-41b8-a03d-47ae37185d34.jsonl   # transcript
```

**Lately:**
- Wrote the handoff and stopped
- Gen-check green after regenerating the manifests
- Isolated the flake to a stale lockfile

**The longer arc:** gen-check flakes have dogged the harness repo since the manifest generator was rewritten in July; first session to pin one to a reproducible cause.

**End state:** `⇥` ended by invoking `session-handoff` → `docs/handoffs/2026-08-08-gencheck-fix.md`, addressed to [1]. **Not yet picked up** — [1] shows no read of the doc. The baton is in the air.

──────────────────────────────────────────────────────────

*(Closed cards: no `left off:` line; `End state:` carries the receipts, e.g.
"`✔` merged PR **#87** (eight ordered tasks into `PROJECTS.md`), checked the
scoping task off the docs-renderer project, removed scratch files. Fully
capped." Codex cards use `codex resume <uuid>` and the resolved
`$CODEX_HOME/sessions/YYYY/MM/DD/rollout-<timestamp>-<uuid>.jsonl` path —
`~/.codex/sessions/…` by default; always render the resolved path, never the
variable.)*

## The default listing and the three flag modes

**The default listing is full canonical cards, together** (decided
2026-08-08, superseding an earlier "compact is the default" note that
contradicted the golden example): every found session rendered as its
complete card, stacked under the delimiter ladder — `══` bands when the set
spans the age thresholds, `━━` groups, `────` card boundaries. The golden
example above **is** the default listing's normative form.

The canonical card is the superset; the flag modes reorder/drop but never
invent fields.

1. **Orientation-compact** (`--compact`) — ~3 lines per session for
   triaging large result sets: title + tool + time-ago + status/lineage
   glyphs on line 1, location + repos on line 2, resume command on line 3.
   Status is a first-class column. Drill-down ("show me [1]") returns the
   full card. Long-running sessions show a span instead of a bare time-ago
   (`Jun 3 → Aug 8`).

   ```text
   [1] Fix skill symlink placements   claude · 1h ago  · ● open ~90% · ⇤ from mbp-m1
       ⑂ ~/c/acme-api-placements   repos: acme-api, acme-web
       cd ~/c && claude --resume 37185d34-a03d-47ae-be38-f29d5e2e5fb5
   ```

2. **Respawn console** (`--exec` mode) — every entry a runnable bash block;
   orientation as comments; adds data-access one-liners (grep turn counts,
   cat the handoff doc).
3. **What-it-did ledger** (`--ledger` mode) — working set + Lately/TLDR/arc
   lead; identity + commands demoted to a `<sub>` footer (the only place UUID
   abbreviation is allowed).

### Compact discipline (v7.1 — first-contact fixes, 2026-08-08)

Real listings stress compact mode in ways the golden mocks never did; these
rules are binding whenever `--compact` renders:

- **Line 1 is fixed.** Title + tool + time/span + status glyphs never wrap
  or split across lines. The title is budgeted to fit (~48 chars): generate
  compact titles that short; when one cannot compress, ellipsize it in the
  compact line only — the full card carries the full title.
- **Status annotation: one terse fact.** After the state word, at most one
  short fact — a progress figure (`~90%`) or the single cap-missing fact
  (`7 worktrees standing`). Never a clause chain, never sentence prose.
- **Line 2 is the `at:` resolution.** Worktree with `⑂` when the session
  has one (even when the spawn dir differs); checkout path otherwise — the
  same rule as the card's `at:` line.
- **No invented zones.** Compact renders exactly: header → bands (when
  spanned) → entries → optional one-line coverage footer. Evidence,
  receipts, lineage detail, and left-off specifics live on the drilled
  card — never as prose sections around the listing. A classification
  resting on stated-evidence still shows only glyph + state word here; the
  evidence renders on drill-down.

## Design decisions — do not regress

These were explicit user corrections during the design session:

- **Group by reader question, not data type** — bands answer "what is this? →
  where? → which exactly? → how do I get back in? → what happened?" in scan
  order. (Data-type grouping was explicitly rejected: it optimizes the writer.)
- **Spawn dir is first-class** because Claude Code keys session files and
  resume behavior by cwd; Codex keys by date. The `cd` in the resume command
  and the session-file path move together.
- **Deliberate redundancy:** the UUID appears in identity line, resume command,
  and file path — each serves a different hand (talk / run / grep). Don't
  dedupe.
- **Location echo (`at:`) repeats the table** on purpose: the echo is the
  *resolved* answer ("where do my hands go"), the table is the *decomposed*
  facts. E.g. "no worktree of its own (reads [1]'s)" fits no table cell.
- **Left off (top) vs End state (bottom):** prescriptive vs descriptive; open
  cards lean on the first, closed on the second, same slots for both.
- **Three time horizons:** Lately = hours, TLDR = session, arc = months.
- **No blockquote rail** — removed by user request; the `────` delimiter does
  all card separation.
- Blockquote-rail removal, TLDR position, lineage-with-title, command spacing,
  bare file path, start→end time spans, and age-band sections were all
  explicit user corrections in the final rounds.

**Rejected approaches (don't redo):**

- Vertical facts-table card — kept only as a possible single-session deep
  view; rejected as the listing default (facts crowd out narrative at 10+
  sessions).
- Status glyph on the title line — rejected; it must be its own line.
- Bare work-item IDs anywhere — the whole point of the triple form.
- `less` prefix on the session-file line — rejected; bare path, command-styled.

**Constraints:**

- Output is GitHub-flavored markdown rendered in a terminal: no HTML, tables
  must stay narrow (wide content abbreviates only in the ledger footer),
  syntax coloring comes only from fenced blocks / inline code / headings.
- Glyph and delimiter budgets are strict — new glyphs need a removed one.
