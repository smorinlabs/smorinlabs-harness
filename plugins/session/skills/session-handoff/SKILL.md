---
name: session-handoff
allowed-tools: Bash, Read, Glob, Grep, Write, AskUserQuestion
argument-hint: "[--file|--inline]"
description: Package the CURRENT session into a self-contained handoff a fresh, zero-context session — often on a DIFFERENT machine — can act on cold — the outcome to pursue, full repo identity and paths, the resume state, and the tacit context that dies on compaction (decisions and why, constraints, rejected approaches). Scopes to an outcome first — infers the likely goal(s), shows them, and confirms or asks before generating — then filters everything to that goal. Adapts delivery to size — short handoffs print an inline prompt block, involved ones write a docs/handoffs/ file plus one launch line. Use when the user says "hand this off", "write a handoff", "start a fresh/new session with this context", "continue this in a new window/session", "pick this up on another machine", or "pass the baton". NOT backward orientation of the current session (that is session-recap's "where was I / catch me up") and NOT in-place cleanup (session-loose-ends).
---

# session-handoff

Turn the current session into a **self-contained handoff** that a brand-new
session — one that inherits *nothing*, and may be running on a different
machine — can pick up cold. The forward-facing sibling of read-only
`session-recap` (orient in place) and `session-loose-ends` (act in place).

> **A HANDOFF IS SELF-CONTAINED OR IT IS NOTHING.** Assume the reader has no
> scrollback, no compacted summary, and is on a different machine until proven
> otherwise. **Two failures make a handoff *look* complete while it isn't, and
> both must be surfaced before anything else:** (1) **uncommitted work that
> doesn't exist on the other machine**, and (2) **a referenced doc that's
> missing, won't travel, or is too thin to carry the load.** A handoff that
> delegates its substance to an unverified external file inherits that file's
> failure silently — so **carry the essence, don't just link it.**

**`allowed-tools` is `Bash, Read, Glob, Grep, Write, AskUserQuestion`** — it
gathers (Bash/Read/Glob/Grep), scopes (AskUserQuestion), and writes at most two
files (Write): the handoff doc and — only when you have opted in — a
user-scope effectiveness log. It is otherwise
**near-read-only** — it never commits, pushes, stages, or cleans. Design
rationale lives beside this file in `DESIGN.md` (a companion doc, not loaded).

## Workflow

Scope first, gather quietly, compose against the contract, deliver by size,
record one note. Every probe degrades gracefully — a missing tool or failed
command becomes a noted gap, never a stall. A partial handoff is useful; a
stalled one is not.

### 1. Scope to an outcome (do this before gathering deeply)

A handoff is organized around what the *next* session must achieve — not a
neutral dump. Infer, show, then confirm or ask:

- **Infer** candidate goal(s) from the last human directives, the unfinished
  work, and any open decisions.
- **Show** them back, and decide by confidence:
  - **confident + a single clear goal** → one-line confirm and proceed;
  - **vague, or several plausible goals** → ask (one axis of ambiguity → one
    question; several → an `AskUserQuestion` batch) to pin the goal(s);
  - **low confidence** → just ask. Don't guess the point of the handoff.
- **State what is out of scope** explicitly, and filter everything downstream to
  the chosen goal(s) — which may be plural.

### 2. Gather (standalone forward pass)

- **Transcript digest** — reuse the sibling script from `session-recap`.
  Placement is per-skill symlinks, so resolve this skill's *real* dir first
  (`pwd -P`) before reaching across to the sibling; a lexically-normalized path
  would miss it:

  ```bash
  d="$(cd "<skill-dir>" && pwd -P)"          # -P resolves the symlink to the real plugin path
  digest="$d/../session-recap/scripts/transcript_digest.py"
  [ -f "$digest" ] || echo "sibling digest not installed"
  python3 "$digest"
  ```

  The sibling is present under a plugin or dev-symlink install, which bring
  the whole `session` plugin. A **direct copy of this skill alone does not
  have it** — if the script is missing, say so plainly and compose the
  handoff from what is in context, exactly as when no transcript exists.

  `$CLAUDE_CODE_SESSION_ID` names this session's transcript; the script reads it
  from its own environment, so pass no argument. It returns the title, opening
  prompt, compaction markers, branch changes, the last turns, and a
  **references** block (tickets, spec/doc files, URLs) — the raw material for
  artifacts and tacit context. On `NO_TRANSCRIPT`, fall back to the newest
  transcript **for this repo** — transcripts are filed per working directory,
  so scope the lookup rather than taking the newest on the machine, which is
  frequently another repo's:

  ```bash
  proj=~/.claude/projects/"$(echo "$PWD" | tr '/.' '--')"
  newest="$(ls -t "$proj" 2>/dev/null | grep '\.jsonl$' | head -1)"
  [ -n "$newest" ] && echo "$proj/$newest"
  ```

  Pass that positionally. If there is none, compose from context and say so —
  never widen the search to other repos to fill the gap.

- **Repo identity** (so the target can locate or *clone* the repo):

  ```bash
  git rev-parse --show-toplevel                                   # repo root (this machine)
  git remote get-url origin                                       # origin URL
  git symbolic-ref --short refs/remotes/origin/HEAD | sed 's|origin/||'  # default branch
  git branch --show-current ; git rev-parse HEAD                  # current branch + SHA
  ```

- **Portability preflight** (the reason this skill exists). Each becomes a
  *won't-travel* warning:

  ```bash
  git status --porcelain                       # uncommitted → commit or stash-as-patch
  git log @{upstream}..HEAD --oneline 2>/dev/null   # unpushed → push or it won't exist elsewhere
  git stash list                               # stashes are local-only
  ```

- **Artifacts & sources of truth — and vet each one.** `PROJECTS.md` task IDs,
  spec/plan/design files surfaced by the digest, PR URL via
  `gh pr view --json number,url,state,title 2>/dev/null`. For **every artifact
  the handoff will lean on**, probe three things — a broken reference makes the
  whole handoff hollow:

  ```bash
  test -f "<path>"                             # exists? a dangling reference is a dead handoff
  git ls-files --error-unmatch -- "<path>" 2>/dev/null && \
    git status --porcelain -- "<path>"         # committed & clean? uncommitted → won't travel
  wc -l -- "<path>"; grep -cE 'TBD|TODO|<[a-z-]+>|placeholder' -- "<path>"   # substantive, or a stub?
  ```

  A file that's absent, uncommitted, or tiny/`TBD`-riddled **can't carry the
  load** — carry each artifact's status into the preflight *and* into what you
  inline (§3).

- **Cross-repo** — watch the transcript's `cwd` shifts and any referenced paths
  outside the repo root; if the work spans repos, emit one **repo-identity
  block per repo** and flag it.

### 3. Compose against the content contract

**Inline the essence; reference for depth.** The handoff must stand on its own —
so for every load-bearing artifact (the plan, the design decisions, the spec),
*distill its essence into the handoff itself*: the goal, the key decisions, and
the plan's **step skeleton**. The referenced doc is then "full detail," not the
sole source. Apply the self-test before delivering:

> **Would the next session make real progress if every referenced doc were
> unavailable?** If no, inline more.

This test doubles as a quality check: if a load-bearing doc is *too thin to
distill*, you've just discovered it's a stub — flag it (`⚠ thin`) in the
preflight rather than shipping a confident pointer to a void. The skill can't fix
a bad design doc, but it must never present one as a complete handoff.

Then fill the template, filtered to the goal(s). Every path appears
**repo-relative (canonical)** with an **absolute path as a labeled same-machine
convenience** — absolute breaks across machines, relative breaks off repo-root,
so give both and let the reader pick the one that resolves.

```
# Session handoff — <topic> — <YYYY-MM-DD>

## 🎯 Outcome
Goal(s): <the 1-n goals this handoff is aimed at>
Out of scope: <stated explicitly>
Self-contained: ✓ stands alone  |  ⚠ depends on <doc> (uncommitted / thin) — commit or inline before this travels

## ⚠ Portability & dependency preflight — read first
- Uncommitted: <files> → won't exist on another machine; commit or stash-as-patch
- Unpushed: <n commits> → push or they won't travel
- Referenced docs: <doc> ✓ exists · committed · substantive | ⚠ uncommitted (won't travel) | ⚠ thin (stub — essence inlined below, don't trust the file)
- ✓ Clean, pushed, all references travel  (when true)

## 🧭 Where you are
- Repo: <name> · origin <url> · default <branch>
- Branch: <branch> @ <sha>  · repo root (this machine): <abs> ← may differ on yours
- Build/verify: <cmd>
- [one identity block per repo if multi-repo]

## 📎 Artifacts & sources of truth
| What | Repo-relative path (canonical) | Abs (this machine) | Status | Ticket/PR |
|------|--------------------------------|--------------------|--------|-----------|
| <artifact> | <repo-relative path> | <abs path> | ✓ committed & substantive | <ticket/PR> |
(Status: ✓ committed & substantive · ⚠ uncommitted · ⚠ thin/stub)

## 📋 Plan · inlined skeleton
The essence of the load-bearing artifact(s), carried so this stands alone even if
the referenced doc is missing or thin — the reference above is depth, not payload.
- <step 1> · <step 2> · <step 3> …  (enough that the next session can start cold)

## 🔧 State to resume
- Done: … · In flight: <file:line>, what's failing · CI/PR: …

## 🧠 Critical context that won't survive a fresh window
- Decisions & why
- Constraints / gotchas
- Rejected approaches & why (don't redo)
- Conventions / preferences agreed this session

## 👉 First action
<one concrete step>

## ℹ How this was made
digest: ok/partial · gathered <date> · machine <host> · self-contained: ✓/⚠
```

**Order is deliberate:** Outcome is the spine, and its `Self-contained:` line is
the reader's trust signal; the Portability & dependency preflight sits *above all
content* because "your uncommitted work isn't here" and "the doc this leans on
didn't travel / is a stub" must both land before the reader trusts anything
below. The inlined plan skeleton is what makes the ✓ honest.

### 4. Deliver by size

Score the handoff over {# goals, # artifacts, cross-repo?, volume of tacit
context, in-flight complexity}:

- **Short / simple → inline.** Print the composed block in chat, then offer:
  *"Want me to also save this to a file?"*
- **Involved → file + launch line.** Write to
  `docs/handoffs/$(date +%F)-<topic>.md` (repo-local, so it travels via git),
  then print the launch line:

  > ▶ ⌨️ — Start a new session in `<repo>` and paste:
  > `Read ~/<basedir>/<repo>/docs/handoffs/<file>.md and continue.`
  > ✓ The handoff doc is itself uncommitted until you commit it — commit it if it
  > must reach another machine.

  **The pasted line must locate the file on its own.** Only the code span
  survives a copy-paste; the surrounding "start a session in `<repo>`" prose
  does not. A bare repo-relative path (`docs/handoffs/<file>.md`) resolves to
  nothing when the new session opens in a different repo, and a machine-local
  absolute path breaks on a different machine — so render the full path
  tilde-anchored, with the base directory and repo name inside the code span.
  Keep the absolute path, if you show one at all, beside the pasteable line as
  a local convenience rather than inside it.

- `--file` / `--inline` in the invocation force the mode; the default location is
  overridable on request.

### 5. Record one effectiveness note (opt-in)

**Only if `~/.claude/session-handoff/` already exists**, append a single line to
`~/.claude/session-handoff/effectiveness.md` — did the digest surface the goal,
references, and paths the handoff needed, and was the result self-contained?
This is the evidence that later justifies (or refutes) graduating to a
dedicated gathering script.

Never create the directory: its presence *is* the opt-in, and its absence means
skip this step silently. Never write inside the skill's own directory — an
installed skill is read-only. Appending is non-fatal; a failure here never
blocks the handoff.

## Red Flags

| Thought | Reality |
|---|---|
| "Absolute paths are enough" | They don't resolve on another machine. Repo-relative is canonical; absolute is a labeled convenience. |
| "The dirty tree is fine, I'll mention it later" | On a different machine uncommitted work simply isn't there. It's the preflight, above all content — not a footnote. |
| "The plan's in the design doc, just link it" | A link is not content. Inline the essentials (goal, decisions, step skeleton); the doc is depth, not the payload. A handoff that dies when one referenced file is missing isn't a handoff. |
| "The referenced doc exists, so we're good" | Exists ≠ travels ≠ substantive. Probe all three: committed (or it won't travel) and not a stub (or it can't carry the load). |
| "I'll just dump the whole session" | A handoff is filtered to an outcome. Scope first; state what's out of scope. |
| "The goal is obvious, skip scoping" | Only skip the *question*, not the step — infer, show, confirm. Low confidence → ask. |
| "Rejected approaches aren't worth including" | They're the highest-value payload — without them the new session confidently re-derives a dead end. |
| "It's one repo" | Verify. Watch `cwd` shifts; multi-repo work needs an identity block per repo or the reader can't locate half of it. |
| "This is basically session-recap" | Recap orients someone who still has the context (backward). This packages for someone who has none (forward). |
| "Writing the file means the work is portable" | The handoff doc is itself uncommitted until committed. Say so in the launch line. |

## See also

- `session-recap` — backward orientation ("where was I"); its §8 Outstanding
  classes are a good source of candidate goals for step 1.
- `session-loose-ends` — the acting sibling; when the user wants dangling items
  *cleaned* rather than packaged, route there.
- `question-walkthrough` — the engine to hand ambiguous goals to in step 1.
- `reader-steps` — the format the step-4 launch line follows.
- `DESIGN.md` (beside this file) — purpose, principles, decision log, and the
  verified symlink-safe sibling recipe. Read it before editing this skill.
