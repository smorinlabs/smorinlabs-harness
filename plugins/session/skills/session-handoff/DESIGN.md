# session-handoff — Design, Principles & Choices

> **Status:** design approved (2026-07-22); implementation pending.
> **This file is a companion record, not skill instructions.** Only `SKILL.md` is
> auto-loaded when the skill fires, so this document never enters the skill's
> instruction context and cannot interfere with its behavior. It exists so the
> *why* behind the skill travels with the skill — reopen it before any future edit.

## 1. Purpose & boundary

A **forward-packaging** skill: it turns the *current* session into a
**self-contained handoff** that a zero-context session — likely on a **different
machine** — can act on cold.

It is the third sibling in the `session-recap` plugin:

| Skill | Direction | Job |
|---|---|---|
| `session-recap` | backward | orient *in place* (read-only) |
| `session-loose-ends` | present | *act* on dangling items in place |
| **`session-handoff`** | **forward** | **package the session for transport to a new session** |

**Boundary.** It *generates the handoff*; it does **not** spawn the new session
(no skill can mint a fresh top-level context). It writes at most two files — the
handoff doc and its effectiveness-notes log — and **never commits, pushes, or
cleans**. Near-read-only, like `recap`.

## 2. Design principles

1. **Assume a zero-context reader on a different machine.** The reader inherits
   nothing: no scrollback, no compacted summary, no "as we discussed." Every fact
   must be stated in full; every path must resolve for *them*. This single
   assumption is what separates `handoff` (make self-contained) from `recap`
   (summarize for someone who still has the context).
2. **Portability is the load-bearing constraint, not a nicety.** The #1 silent
   failure of a handoff is not a stale path — it is **uncommitted work that does
   not exist on the other machine.** The skill refuses to be quiet about it.
3. **Focus on an outcome.** A handoff is organized around the goal(s) the *next*
   session must achieve, and states what is explicitly out of scope. It is not a
   neutral full dump.
4. **Scale to size.** Short handoffs stay inline; involved ones become a file.
   Mirrors `session-recap`'s `default`/`--long` split and the `reader-steps`
   scale-to-size ethic — keeps the family coherent.
5. **Build the minimum, instrument it, let evidence justify the next increment.**
   Prose+bash first; graduate to a gathering script only if the effectiveness
   notes show the prose pass is unreliable.
6. **Preserve the tacit.** The highest-value, least-obvious payload is the
   context that lives *only* in the conversation and evaporates on compaction —
   decisions and their *why*, constraints discovered, and **rejected approaches
   and why** (so the new session does not re-derive a dead end).
7. **Self-containment over references — carry the essence, don't just link it.**
   A referenced artifact is a *second* way a handoff looks complete while it
   isn't (the first is uncommitted work, principle #2). If the load-bearing
   substance lives in an external doc, the handoff's real quality is
   `min(handoff, doc)` — and it inherits the doc's failure (missing, uncommitted,
   or a thin stub) silently. So the skill **distills the essence** of every
   load-bearing artifact into the handoff itself, **verifies** each referenced
   artifact (exists · committed · substantive), and prints a **self-containment
   verdict**. The test: *would the next session make progress if every referenced
   doc were unavailable?* Distilling also self-detects a thin doc — you can't
   distill a stub.

## 3. Decision log (what was chosen, and why)

| # | Decision | Choice | Why |
|---|---|---|---|
| D1 | Deliverable form | **Adaptive.** Short ⇒ inline block (offer to also save a file). Involved ⇒ default to a file + one launch line. `--file`/`--inline` override. | Matches how the work actually varies; small handoffs shouldn't pay file overhead, large ones shouldn't die in scrollback. |
| D2 | Scoping interaction | **Infer-then-confirm decision tree** (see §6). Guess goal(s), show them; if vague, ask one or several questions; **if low confidence, just ask.** State out-of-scope; filter to goal(s), possibly plural. | Owner's rule: align on what to hand off before generating; don't over-ask when the goal is obvious, don't guess when it isn't. |
| D3 | Evidence gathering | **Standalone forward pass**, but **reuse `transcript_digest.py`** as a plain tool. Keep an **effectiveness-notes log**; move off the digest only if notes show gaps. | Standalone logic stays tuned for handoffs; reusing the one hard script (transcript parsing) avoids reinventing it. Instrument, then decide. |
| D4 | Home & name | **`session-handoff`** in the `session-recap` plugin. | Natural family; shares the sibling script and the "session-\*" trigger neighborhood. |
| D5 | File-mode location | **`docs/handoffs/YYYY-MM-DD-<topic>.md` in the repo** by default; the user may request another location. | Repo-local ⇒ discoverable and **travels via git**, which is exactly what cross-machine needs. |
| D6 | Implementation shape | **Approach C** — prose+bash reusing the sibling script, plus one codified *portability preflight*. | Family style + rigor spent only where prose is genuinely error-prone (cross-machine). |
| D7 | Sibling-script reference | **Verified works** in the per-skill-symlink placement; recipe resolves the real dir first (see §9). | Empirically tested 2026-07-22; see §9 for the evidence and the exact recipe. |
| D8 | Self-containment over references (v0.6.0) | **Inline the essence** of load-bearing artifacts; **verify** each referenced doc (exists · committed · substantive) in the preflight; print a **self-containment verdict**; add a `📋 Plan · inlined skeleton` section. | Dogfood feedback 2026-07-23: the handoff pointed at a design doc for the plan, so its quality was `min(handoff, doc)` and it inherited a missing/thin doc silently. A link is not content; distilling also self-detects a stub. See principle #7. |

## 4. Content contract → the handoff document

Seven categories (the inlined plan skeleton joined in v0.6.0 — see D8). Every
path appears **repo-relative (canonical)** with an **absolute path as a labeled
same-machine convenience** — the two fail in opposite situations (absolute
breaks across machines; relative breaks off repo-root), so showing both lets
the reader pick the one that resolves.

```
# Session handoff — <topic> — <YYYY-MM-DD>

## 🎯 Outcome
Goal(s): <the 1-n goals this handoff is aimed at>
Out of scope: <stated explicitly>
Self-contained: ✓ stands alone  |  ⚠ depends on <doc> (uncommitted / thin) — commit or inline before this travels

## ⚠ Portability & dependency preflight — read first
- Uncommitted: <files> → won't exist on another machine; commit or stash-as-patch
- Unpushed: <n commits> → push or they won't travel
- Referenced docs: <doc> ✓ exists · committed · substantive | ⚠ uncommitted (won't travel) | ⚠ thin (stub — essence inlined below)
- ✓ Clean, pushed, all references travel  (when true)

## 🧭 Where you are
- Repo: <name> · origin <url> · default <branch>
- Branch: <branch> @ <sha>   · repo root (this machine): <abs> ← may differ on yours
- Build/verify: <cmd>
- [one identity block per repo if multi-repo]

## 📎 Artifacts & sources of truth
| What | Repo-relative path (canonical) | Abs (this machine) | Status | Ticket/PR |
|------|--------------------------------|--------------------|--------|-----------|
| <artifact> | <repo-relative path> | <abs path> | ✓ committed & substantive | <ticket/PR> |
(Status: ✓ committed & substantive · ⚠ uncommitted · ⚠ thin/stub)

## 📋 Plan · inlined skeleton
The essence of the load-bearing artifact(s), carried so the handoff stands alone
even if the referenced doc is missing or thin — the reference is depth, not payload.
- <step 1> · <step 2> · <step 3> …

## 🔧 State to resume
- Done: … · In flight: <file:line>, what's failing · CI/PR: …

## 🧠 Critical context that won't survive a fresh window
- Decisions & why
- Constraints / gotchas
- **Rejected approaches & why (don't redo)**
- Conventions / preferences agreed this session

## 👉 First action
<one concrete step>

## ℹ How this was made
digest: ok/partial · gathered <date> · machine <host> · self-contained: ✓/⚠
```

**Section ordering is deliberate:** Outcome first (the spine, with the
`Self-contained:` verdict as the reader's trust signal), then the Portability &
dependency preflight *before any content* — on a different machine, "your
uncommitted work isn't here" and "the doc this leans on didn't travel / is a
stub" must both be hit before the reader trusts anything downstream. The
inlined plan skeleton is what makes a ✓ verdict honest (see D8 / principle #7).

## 5. Pipeline

```
gather (standalone, forward)
  → infer goal(s)
  → scoping decision tree (§6)
  → pick delivery mode (size score, or honor --file/--inline)
  → compose from the content contract, filtered to goal(s), out-of-scope stated
  → emit (inline block  OR  write file + launch line)
  → append effectiveness note
```

## 6. Scoping decision tree

```
infer candidate goal(s) from: last human directives + unfinished work + open decisions
  → SHOW them
  → confident & single goal      ⇒ one-line confirm
  → vague OR multiple plausible  ⇒ ask
        one axis of ambiguity    ⇒ one question
        several                  ⇒ AskUserQuestion batch
  → low confidence               ⇒ just ask (owner's rule: "if not sure, ask")
always: state out-of-scope explicitly, then filter content to the goal(s)
```

Hands scoping questions to the same ergonomics as `question-walkthrough`.

## 7. Machine-portability (load-bearing)

Assume a **different machine** unless proven otherwise. Consequences:

- **Repo-identity block** — origin URL, default branch, current branch, HEAD SHA,
  repo root — so the target can *locate or clone* the repo.
- **Repo-relative paths are canonical**; absolute paths are a labeled
  same-machine convenience.
- **Portability preflight** — warn hard on **uncommitted** (`git status
  --porcelain`), **unpushed** (`git log @{upstream}..HEAD`), and stashes. Each
  becomes a "won't-travel" line telling the reader to commit / push /
  stash-as-patch first.
- **Referenced-artifact vetting (D8)** — every doc the handoff leans on is
  probed: exists (`test -f`), committed & clean (`git ls-files` + `status`),
  substantive (line count / stub-marker grep). Absent, uncommitted, or thin →
  flagged in the preflight and compensated by inlining the essence.
- **Multi-repo tasks** → one identity block per repo, explicitly flagged.
- The **handoff file itself is uncommitted work** until the user commits it — the
  launch line reminds them to commit it if it must travel.

## 8. Evidence gathering & the effectiveness-notes log

Standalone forward pass:

- **Transcript** via the reused `transcript_digest.py` (see §9 for the exact,
  symlink-safe invocation); same `NO_TRANSCRIPT` fallback as `session-recap`.
- **Repo identity + portability preflight** — the git commands in §7.
- **Artifacts** — `PROJECTS.md` task IDs, `docs/` + spec/plan files surfaced by
  the digest, PR URL via `gh` (best-effort).
- **Cross-repo detection** — watch `cwd` shifts and referenced paths outside the
  repo root.

**Effectiveness-notes log** (`~/.claude/session-handoff/effectiveness.md`, at
user scope): after each run, append one line — did the digest surface the goal /
references / paths the handoff needed? This is the evidence that later justifies
(or refutes) graduating to a dedicated `handoff_gather.py`. Appending is
non-fatal.

The log is **opt-in and lives outside the skill directory**. Dogfooding
2026-07-22 caught the first alternative: a *tracked* log beside the skill means
every run anywhere appends through the placement symlink and leaves the harness
checkout dirty. Moving it to a git-ignored file beside the skill fixed that for
one machine but not in general — an installed skill directory is read-only from
the user's point of view, and writing into it mutates the plugin. User scope
solves both. Its one-line schema:

    <YYYY-MM-DD> · digest:<ok|partial|none> · goal:<found|missed> · refs:<found|partial|missed> · paths:<ok|gap> · note:<free text>

The directory's presence is the opt-in signal: step 5 appends only when
`~/.claude/session-handoff/` already exists, and never creates it. A user who
wants the log runs `mkdir -p ~/.claude/session-handoff` once; everyone else gets
a silent no-op and an unmodified plugin directory.

## 9. Sibling-script reference — verified recipe

The reused script lives in the *sibling* skill:
`plugins/session/skills/session-recap/scripts/transcript_digest.py`.

Placement on this machine is **per-skill symlinks** (each skill dir is its own
symlink into the plugin). Verified 2026-07-22 by simulating that exact layout:

- Referencing `<skill-dir>/../session-recap/scripts/transcript_digest.py` and
  letting `open()`/`stat()`/`python3` resolve it **works even when the
  `session-recap` sibling is not separately placed** — the kernel resolves `..`
  **physically**, following the `session-handoff` symlink into the real plugin
  dir where `session-recap` is always a sibling.
- The trap: **lexical** `..` normalization (e.g. `os.path.normpath` without
  touching the filesystem) would instead look in `~/.claude/skills/session-recap/…`,
  which only exists if the sibling is also placed.

**Recipe for `SKILL.md`** — resolve the real dir first, immune to both lexical
normalization and the sibling-not-placed case:

```bash
d="$(cd "<skill-dir>" && pwd -P)"        # -P resolves the symlink to the real plugin path
python3 "$d/../session-recap/scripts/transcript_digest.py"
```

Monitor (in the effectiveness log) that `<skill-dir>/..` resolution keeps working
across harnesses; relocate the script to a plugin-level `scripts/` only if it ever
breaks.

## 10. Delivery modes

Size score over {# goals, # artifacts, cross-repo?, volume of tacit context,
in-flight complexity} → **short ⇒ inline** (then offer to save a file);
**involved ⇒ write file + one launch line**. `--file`/`--inline` force it.

Launch line (a `reader-steps` step): *"Start a new session in `<repo>` and paste:
`Read <path> and continue.`"*

## 11. Trigger description (collision-safe)

Fires on **forward** intent — "hand off this session", "start a fresh/new session
with this context", "write a handoff", "continue this on another machine / in a
new window", "package this session for a new session", "carry this over" —
**explicitly not** `session-recap`'s "where was I / catch me up" nor
`session-loose-ends`' cleanup.

## 12. Layout, error handling, testing

**Layout**
```
plugins/session/skills/session-handoff/
  SKILL.md              (skill instructions — auto-loaded)
  DESIGN.md             (this file — companion record, not loaded)
  # the effectiveness log lives at ~/.claude/session-handoff/effectiveness.md
  # reuses ../session-recap/scripts/transcript_digest.py
```

**Degrades gracefully**
- no transcript → compose from context, say so
- no `gh` → skip PR line
- not a git repo / orphaned worktree → context-only handoff, say so
- note-append failure → non-fatal

**Testing**
- `skill-quality` gate + a cross-tool load check (claude-code + codex)
- **First acceptance test is dogfooding:** run `session-handoff` on *this* session
  and confirm the artifact is act-on-able cold on a hypothetical fresh machine.

## 13. See also

- `session-recap` — backward orientation; its §8 Outstanding classes are a good
  source of candidate goals.
- `session-loose-ends` — the acting sibling for in-place cleanup.
- `question-walkthrough` — where the scoping tree hands off ambiguous goals.
- `reader-steps` — the format for the launch line.
