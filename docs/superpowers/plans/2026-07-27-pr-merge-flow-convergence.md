# PR Merge Flow Convergence Guardrails — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the convergence guardrails design (spec: `docs/superpowers/specs/2026-07-27-pr-merge-flow-convergence-design.md`) in the `pr-merge-flow` skill — scope-gated triage with a value floor, trajectory measurement with a ratcheting bar, and merge-and-defer as a first-class ending.

**Architecture:** Prose-skill edit, no code. One new reference file (`references/convergence.md`) carries the trajectory/ratchet machinery (progressive disclosure keeps SKILL.md lean); `references/triage.md` gains the scope/value rubric; `SKILL.md` wires both into steps 1, 3, 4, 5, 7, 8, 9, the Iron Law, the description, and Red Flags. Version bump + regen close it out.

**Tech Stack:** Markdown skill files; `uv run harness-kit gen` (manifest regen); lefthook pre-commit (`gen-check`); git.

## Global Constraints

- Work in the `pmf-convergence-spec` worktree (`/Users/stevemorin/c/smorinlabs-harness/.claude/worktrees/pmf-convergence-spec`), branch `worktree-pmf-convergence-spec`. Never touch the main checkout.
- **Never write the private cross-tool verifier's name** into any file. Guard before every commit: `git grep -niE 'skill''smith' -- ':!.github/workflows/ci.yml'` must exit 1 (no hits).
- Conventional commits; every commit ends with the trailer `Claude-Session: https://claude.ai/code/session_01PrbE6PuQu5Yap914WA3ZdW`.
- The skill's `description:` frontmatter is a single-quoted YAML scalar — no bare apostrophes in added text.
- Match the skill's existing voice: imperative, tight, bold key phrases, ~80-col wrap.
- Quota/polling rules, browser fallback, and merge-strategy text are untouched (spec: Out of scope).

---

### Task 1: Create `references/convergence.md`

**Files:**
- Create: `plugins/repo-hygiene/skills/pr-merge-flow/references/convergence.md`

**Interfaces:**
- Produces: the terms **trajectory table**, **ratchet**, **ratcheted bar**, **wave**, **fix-of-fix fraction**, **declined fraction**, and the check-in template — referenced by Tasks 3 and 4 as `references/convergence.md`.

- [ ] **Step 1: Write the file with exactly this content**

````markdown
# Convergence — trajectory, ratchet, check-in

Why this file exists: on large PRs the review loop diverges — every push
draws a fresh reviewer wave ~10 minutes later, fixes add code, and new code
is new review surface. Measured across eleven episodes: finding rates
plateau (3–4/cycle indefinitely) instead of decaying, review fixes carry a
~7%-per-commit regression rate, and hardening cost can equal feature cost.
The loop does not terminate on its own; this machinery makes it terminate
honestly.

## The trajectory table

Extend the thread ledger with one row per completed reviewer wave:

| Wave | Bot | New findings | Severity mix | On review-added code | Declined |
|---|---|---|---|---|---|

- **A wave is per-bot.** Reviewers stagger: Codex habitually lands after
  Copilot/Greptile, and CodeRabbit has arrived hours late. Cross-cycle
  comparison is **same-bot only** — a total that doubles because a slow bot
  finally reported is staggering, not escalation.
- **"On review-added code"** counts findings whose subject lines/files were
  introduced by this run's own fix commits (check the blame of the flagged
  lines against the fix SHAs).
- **"Declined"** counts findings below the value floor (triage.md) — style
  taste, convention-conflicting asks, arguable value with real blast radius.

**Convergence is measured in findings received. Fixes chosen is a banned
metric** — "11 → 4 → 2" where 2 is the fixes you elected to make hides a
round that actually received 5.

## The ratchet

The bar ratchets when **any** of these trips:

1. cycle ≥ 3;
2. same-bot new findings not decreasing wave-over-wave;
3. a majority of a wave targets review-added code — the loop is reviewing
   its own output.

Under the ratcheted bar, only **would-ship-broken defects in the PR's own
diff** get code. Everything else defaults to defer, decline, or refute per
the triage rubric. The scope class of a finding never depends on when it
arrived — a ship-breaking P1 in cycle 4 is still a fix.

## Wave composition is a signal

Severity draining toward Minor and the declined fraction rising mean the
reviewers have run out of functional bugs. That is **evidence for merging,
not work to do** — present it at the check-in as support for *merge and
defer the residue*.

## The check-in

At the bound (4 cycles, or the ratchet tripping in two successive waves),
report:

- the trajectory line — e.g. `11 → 4 → 5 · cycle 3 · majority on fix-added
  code · severity draining`;
- the stopping question: **is the design still being questioned, or only
  the churn?**;
- per-thread recommended dispositions (fix / defer-to-<ref> / decline /
  refute / escalated);

then ask one question with three endings — continue until clean (10-minute
wall clock), merge and defer the residue, or pause for redesign. Details
and mode behavior live in SKILL.md step 5.
````

- [ ] **Step 2: Verify content landed and guard is clean**

Run: `grep -c "ratchet" plugins/repo-hygiene/skills/pr-merge-flow/references/convergence.md && git grep -niE 'skill''smith' -- ':!.github/workflows/ci.yml'; echo "guard: $?"`
Expected: count ≥ 4; `guard: 1`

- [ ] **Step 3: Commit**

```bash
git add plugins/repo-hygiene/skills/pr-merge-flow/references/convergence.md
git commit -m "feat(pr-merge-flow): convergence reference — trajectory table, ratchet, check-in

Claude-Session: https://claude.ai/code/session_01PrbE6PuQu5Yap914WA3ZdW"
```

---

### Task 2: Scope axis + value floor in `references/triage.md`

**Files:**
- Modify: `plugins/repo-hygiene/skills/pr-merge-flow/references/triage.md` (the `## Verdict rubric` and `## Reply etiquette` sections)

**Interfaces:**
- Consumes: `references/convergence.md` (Task 1) — named once as the home of trajectory rules.
- Produces: dispositions **fixed / refuted / declined / deferred / escalated**, the reply forms `Deferred to <ref> — <one line>` and `Declining — <one line>`, and the section heading `## Deferral destinations` — referenced by Task 3.

- [ ] **Step 1: Replace the verdict rubric.** Replace the entire block from `3. **Verdicts**` through the line `Style/naming suggestions with no correctness content: apply when they match repo conventions and are cheap; otherwise reply why not, and resolve.` with:

````markdown
3. **Verdicts**
   - **Invalid** — evidence refutes it → reply with the concrete reason ("the
     null check on line 38 already guards this"), resolve. Never resolve
     without the reply.
   - **Valid** — evidence supports it → classify scope and value below
     before writing any code.
   - **Unclear** — cannot be settled with available evidence → per-mode
     handling in SKILL.md step 4.

## Scope and value classification (valid findings only)

| Class | Test | Action |
|---|---|---|
| **Small in-scope bug** | Defect in code this PR touched; the fix corrects lines rather than adding a mechanism; no new invariant | Minimal fix, conventional commit, push, reply `Fixed in <sha> — <one line>`, resolve |
| **Valid, out of scope** | Hardening/robustness/feature beyond the PR's stated goal, or a defect that predates the PR | Create the tracked item at the repo's `defer-target` first, reply `Deferred to <ref> — <one line>`, resolve |
| **Below the value floor** | See the table below | Reply `Declining — <one line>`, resolve |
| **Architectural** | Asks for a new mechanism, redesign, or trust-boundary change | Post one design-question comment; mark the thread **escalated** — it stays open and holds the merge at the gate; only the user closes it |

Classification signals that proved reliable: CodeRabbit's `Heavy lift` tag ≈
architectural; redesign imperatives ("define/introduce/restructure…",
"compute the fixed-point mapping", "define an allowlist or sandbox
boundary"); a fix that would add more lines than it touches leans out of
scope.

### The value floor

A commit is never free: each one carries measured ~7% regression risk, draws
a fresh reviewer wave on its new surface, and spends cycle budget. A small
fix earns a commit only when its value clears that floor. The test: **would
a maintainer, holding the repo's conventions, ask for this change
unprompted?**

| Finding | Disposition |
|---|---|
| Functional bug — behavior is wrong | Fix |
| Real typo — wrong word, command, or meaning in shipped text | Fix |
| Style/lint a repo convention or CI gate actually enforces | Fix (the gate would fail — functionally a bug) |
| Arbitrary style — reviewer taste, no convention behind it | Decline: "style-only; no repo convention requires this" |
| Contradicts a repo convention | Refute citing the convention — bots accept this and have formally withdrawn findings |
| Arguable value with real blast radius (e.g. "remove redundant guard" on a safety-critical path) | Decline citing risk asymmetry — arguable upside, unarguable regression cost |

Never defer a valueless finding — style noise in the tracker buries real
deferrals. Decline it.

### Three hard rules

- A finding against code added during this review → ask first whether
  **reverting the earlier fix to spec semantics** closes it more cheaply
  than extending it.
- "It extends the PR's own principle" is a **defer signal**, not a fix
  mandate.
- Arrival cycle never changes the class — a ship-breaking P1 in cycle 4 is
  still a fix; a style nit in cycle 1 is still a decline. (Trajectory rules:
  `references/convergence.md`.)

## Deferral destinations

Detect once per run, first match wins; record as `defer-target` in
`.claude/pr-merge-flow.local.md`:

1. `PROJECTS.md` / `projects/` in the repo → a task row in the owning
   project, per its conventions.
2. Issue references in recent commits/PRs, or a non-empty `gh issue list`
   → a GitHub issue.
3. A configured external tracker (e.g. Linear) → that tracker.
4. No evidence → **ask the user once**, save the answer.

A deferral without a created, referenced artifact is a silent drop, not a
deferral. The end-of-run report lists every deferral with its reference —
in every mode.
````

- [ ] **Step 2: Extend reply etiquette.** In `## Reply etiquette`, replace the line `- Every resolution carries a reply: what changed (with commit SHA), or why the claim does not hold. No silent resolves, ever.` with:

```markdown
- Every resolution carries a reply: what changed (with commit SHA), why the
  claim does not hold, `Deferred to <ref> — <one line>`, or
  `Declining — <one line>`. No silent resolves, ever.
```

- [ ] **Step 3: Verify**

Run: `grep -c "value floor\|Deferral destinations\|Declining —" plugins/repo-hygiene/skills/pr-merge-flow/references/triage.md; grep -c "apply when they match repo conventions and are cheap" plugins/repo-hygiene/skills/pr-merge-flow/references/triage.md`
Expected: first ≥ 4; second `0` (old style rule gone)

- [ ] **Step 4: Commit**

```bash
git add plugins/repo-hygiene/skills/pr-merge-flow/references/triage.md
git commit -m "feat(pr-merge-flow): scope axis and value floor in the triage rubric

Claude-Session: https://claude.ai/code/session_01PrbE6PuQu5Yap914WA3ZdW"
```

---

### Task 3: Wire the flow — SKILL.md Iron Law, steps 1, 3, 4, 5

**Files:**
- Modify: `plugins/repo-hygiene/skills/pr-merge-flow/SKILL.md` (Iron Law banner; steps 1, 3, 4, 5)

**Interfaces:**
- Consumes: dispositions and section names from Tasks 1–2 exactly as produced (`references/convergence.md`, `## Deferral destinations`, `defer-target`, fixed/refuted/declined/deferred/escalated).
- Produces: step-5 ending names **Continue until clean / Merge and defer the residue / Pause for redesign** — referenced by Task 4's docs edit.

- [ ] **Step 1: Replace the Iron Law banner.** Replace the blockquote paragraph beginning `> **Iron Law: EVERY THREAD RESOLVED BEFORE MERGE; EVERY WAIT BOUNDED.** A thread closes` and ending `> never silently. Every poll loop has an interval floor and a hard` / `> time bound.` with:

```markdown
> **Iron Law: EVERY THREAD RESOLVED BEFORE MERGE; EVERY WAIT BOUNDED.** A thread
> closes only as fixed (commit pushed, reply posted), refuted (reasoned reply
> posted), declined (valid but below the value floor — reasoned reply posted),
> or deferred (tracked item created, reply names it) — never silently.
> Escalated architectural threads are the one state this skill may not close:
> they stay open and hold the merge at the gate for the user. Every poll loop
> has an interval floor and a hard time bound.
```

(Keep the following "No exceptions…" lines unchanged.)

- [ ] **Step 2: Step 1 — prefs key and defer-target detection.** In step 1, extend the prefs keys list `(keys: `mode`, `deep-review`, `merge-method`, `delete-branch`, `cycle-bound`, `continue-until-clean`)` to `(keys: `mode`, `deep-review`, `merge-method`, `delete-branch`, `cycle-bound`, `continue-until-clean`, `defer-target`)`, and append this bullet to the step-1 list:

```markdown
- Deferral destination: resolve `defer-target` per the detection ladder in
  `references/triage.md` (§ Deferral destinations) — repo evidence first,
  ask once only when there is none, save the answer to the prefs file.
```

- [ ] **Step 3: Step 3 — ledger states and trajectory.** Replace the sentence `Each entry carries: author, file/line, the concrete claim, and its state through `discovered → verdict → fixed → replied → resolved`.` with:

```markdown
Each entry carries: author, file/line, the concrete claim, and its state
through `discovered → verdict → fixed | refuted | declined | deferred |
escalated → replied → resolved`. The ledger also carries the per-wave
trajectory table defined in `references/convergence.md`.
```

- [ ] **Step 4: Step 4 — verdict wiring.** Replace the three verdict bullets (`- **Valid** → minimal fix…`, `- **Invalid** → reply…`, `- **Unclear** → …ready-report — the Iron Law forbids merging over it.`) with:

```markdown
   - **Invalid** → reply with the concrete reason it does not hold, resolve
     the thread.
   - **Valid** → classify scope and value per `references/triage.md` before
     any code: **small in-scope bug above the value floor** → minimal fix,
     conventional commit, push, reply naming the fix commit, resolve ·
     **valid but out of scope** → tracked item at `defer-target`, reply
     `Deferred to <ref>`, resolve · **below the value floor** → decline or
     refute with the one-line reason, resolve · **architectural** → one
     design-question comment, mark **escalated**; it stays open and holds
     the merge at the gate.
   - **Unclear** → `confirm`/`ready` modes: ask the user, one question at a
     time. `--auto` never asks: make the call if verification can settle it;
     if genuinely undecidable, leave the thread open and downgrade the run to
     a ready-report — the Iron Law forbids merging over it.

   Hard rules: a finding against review-added code → consider reverting the
   earlier fix to spec semantics before extending it; "it extends the PR's
   own principle" is a defer signal, not a fix mandate; arrival cycle never
   changes the class.
```

- [ ] **Step 5: Step 5 — trajectory, ratchet, three endings.** Retitle `## 5. Re-review cycle` to `## 5. Re-review cycle — measured, ratcheted`. After the first paragraph (ending `not an anomaly.`), insert:

```markdown
Record the wave in the trajectory table per `references/convergence.md`.
Convergence is measured in **findings received — never fixes chosen**.
**The bar ratchets** when any trips: cycle ≥ 3 · same-bot new findings not
decreasing · a majority of a wave targeting review-added code. Under the
ratcheted bar only would-ship-broken defects in the PR's own diff get code;
everything else defaults to defer, decline, or refute.
```

Then replace the check-in paragraph and options (`**Bound: 4 cycles, then check in…**` through the `- **Stop** — ready-report and hand back.` bullet) with:

```markdown
**Bound: 4 cycles, or the ratchet tripping in two successive waves — then
check in. Never stop silently and never loop silently.** The check-in
reports the trajectory line (e.g. `11 → 4 → 5 · cycle 3 · majority on
fix-added code`), asks the stopping question — **is the design still being
questioned, or only the churn?** — and lists per-thread recommended
dispositions. Then ask the user, one question, three endings:

- **Continue until clean** — keep cycling with no cycle limit, bounded
  instead by a **10-minute wall clock** from the moment they say so. Cycles
  still obey every polling rule inside that window; on expiry, stop and
  report wherever the ledger stands. The escape hatch for a PR that is
  genuinely converging, just slowly.
- **Merge and defer the residue** — batch-create the deferral artifacts at
  `defer-target`, reply-and-resolve each remaining thread with its
  reference, then proceed to step 6. The Iron Law holds: every entry fixed,
  refuted, declined, or deferred.
- **Pause for redesign** — the escalated threads become the agenda;
  ready-report naming them and hand back.

`--auto` cannot ask: a tripped ratchet or an escalated thread downgrades the
run to a ready-report naming the open items.
```

Keep the `cycle-bound`/`continue-until-clean` prefs paragraph, and replace the final paragraph of step 5 (`A cycle that produces only new threads…on its own judgment.`) with:

```markdown
A cycle that produces only new threads and no new fixes still counts against
the bound; the bound is on cycles, not on progress. Convergence is not a
reason to skip the check-in — findings shrinking is exactly when a run is
most tempted to keep going on its own judgment. And a wave that is mostly
minutia (severity draining, declined fraction rising) is evidence to merge,
not work to do.
```

- [ ] **Step 6: Verify**

Run: `grep -c "Merge and defer the residue\|escalated\|ratchet" plugins/repo-hygiene/skills/pr-merge-flow/SKILL.md; grep -c "defer-target" plugins/repo-hygiene/skills/pr-merge-flow/SKILL.md`
Expected: first ≥ 6; second ≥ 3

- [ ] **Step 7: Commit**

```bash
git add plugins/repo-hygiene/skills/pr-merge-flow/SKILL.md
git commit -m "feat(pr-merge-flow): scope-gated verdicts, trajectory ratchet, three check-in endings

Claude-Session: https://claude.ai/code/session_01PrbE6PuQu5Yap914WA3ZdW"
```

---

### Task 4: SKILL.md close-out — steps 7/8/9, Red Flags, description, See also

**Files:**
- Modify: `plugins/repo-hygiene/skills/pr-merge-flow/SKILL.md` (steps 7, 8, 9; Red Flags table; frontmatter `description`; See also list)

**Interfaces:**
- Consumes: ending names and dispositions from Task 3 verbatim.

- [ ] **Step 1: Step 7 — report deferrals in every mode.** In the **confirm** bullet, change `a summary line (threads fixed/refuted, checks, title)` to `a summary line (threads fixed/refuted/declined/deferred — each deferral with its reference — checks, title)`. In the **auto** bullet, after `then report what was done`, insert `— including every deferral with its reference —`. In the **ready** bullet, after `report the ready-to-merge state plus the exact merge command`, insert `, every deferral with its reference,`.

- [ ] **Step 2: Step 8 — deep review, same gate.** Append to the step-8 paragraph:

```markdown
Deep-review findings enter the same ledger with the same scope-and-value
classification and count toward the same ratchet — dispatched reviewers
produce 8–33 findings per round against the bots' 1–5, so they get no
exemption.
```

- [ ] **Step 3: Red Flags.** Replace the row `| "Every finding is valid, but there are a lot — let me ask how to proceed" | Valid is not unclear. The rubric already names the action: fix, commit, reply, resolve. Ask only when a verdict is genuinely undecidable, never about strategy. |` with these two rows:

```markdown
| "Many valid small findings — let me ask how to proceed" | Valid small in-scope is not unclear. The rubric names the action; proceed. |
| "These findings extend the PR's own principle, so they're in scope" | Extension is the defer signal, not a fix mandate. Architectural asks are escalated, never absorbed. |
```

Append these rows to the end of the table:

```markdown
| "Findings dropped 11 → 4 → 2 — we're converging" | Count findings received per bot, never fixes chosen. The round that reported 2 received 5. |
| "The count doubled — the review is escalating" | Bots stagger; a slow bot's first report is not a trend. Compare same-bot across waves. |
| "One more fix for the fix and this thread class is closed" | Fix-of-fix is the divergence engine. Consider reverting to spec semantics first. |
| "It is a one-word fix, cheaper to just do it" | Cheap to type is not cheap in system cost: each commit carries regression risk and draws a fresh wave. The value floor applies. |
| "Fixing the nit is more polite than declining it" | A reasoned decline is the etiquette — bots accept it and have withdrawn findings. Fixing nits trains the loop that nits earn commits. |
```

- [ ] **Step 4: Description frontmatter.** In the `description:` value, replace `then triages each thread — validate the claim, verify by running code where possible, fix valid findings and push, refute invalid ones with a reasoned reply — every thread resolved either way.` with `then triages each thread — validate the claim, verify by running code where possible, then scope-gate it: fix small in-scope bugs, defer out-of-scope work to the repo tracker, decline style-only asks, escalate architectural redesigns to the user — every thread resolved either way. Measures convergence across cycles and ratchets the bar when reviews stop converging.` (No apostrophes; single-quoted YAML stays valid.)

- [ ] **Step 5: See also.** Add to the See also list, after the `references/triage.md` entry:

```markdown
- `references/convergence.md` — trajectory table, ratchet, wave-composition
  signals, the check-in template.
```

- [ ] **Step 6: Verify frontmatter still parses and guard is clean**

Run: `uv run --with pyyaml python -c "import yaml; d=yaml.safe_load(open('plugins/repo-hygiene/skills/pr-merge-flow/SKILL.md').read().split('---')[1]); print(len(d['description']))" && git grep -niE 'skill''smith' -- ':!.github/workflows/ci.yml'; echo "guard: $?"`
Expected: a length prints (no YAML error); `guard: 1`

- [ ] **Step 7: Commit**

```bash
git add plugins/repo-hygiene/skills/pr-merge-flow/SKILL.md
git commit -m "feat(pr-merge-flow): red-flag rows, deferral reporting, deep-review gate, description

Claude-Session: https://claude.ai/code/session_01PrbE6PuQu5Yap914WA3ZdW"
```

---

### Task 5: Docs page, version bump, regen

**Files:**
- Modify: `docs/skills/pr-merge-flow.md`
- Modify: `plugins/repo-hygiene/plugin.meta.toml` (version only)
- Regenerate: whatever `uv run harness-kit gen` touches (marketplace/README manifests)

- [ ] **Step 1: Docs page.** In `docs/skills/pr-merge-flow.md`, replace `fix valid findings (commit, push, reply naming the fix, resolve) and refute invalid ones with a reasoned reply before resolving — never a silent resolve.` with:

```markdown
scope-gate valid findings — small in-scope bugs above the value floor get a
fix (commit, push, reply naming the fix, resolve); valid-but-out-of-scope
work is deferred to the repo's tracker (PROJECTS.md rows, GitHub issues, or
an external tracker, detected from repo evidence) with the reference in the
reply; style-only or convention-conflicting asks are declined with a
one-line reason; architectural redesigns are never absorbed into the PR —
they become a design-question comment escalated to the user and hold the
merge — and refute invalid claims with a reasoned reply before resolving —
never a silent resolve.
```

And replace `it cycles (bounded, 4 by default, then a check-in offering to continue under a 10-minute wall clock) until a pass is clean,` with:

```markdown
it cycles with the trajectory measured per reviewer wave (findings received,
never fixes chosen; the bar ratchets at cycle 3, on non-decreasing same-bot
counts, or when a wave mostly targets review-added code), bounded at 4
cycles before a check-in offering three endings — continue under a
10-minute wall clock, merge and defer the residue, or pause for redesign —
until a pass is clean,
```

- [ ] **Step 2: Version bump.** In `plugins/repo-hygiene/plugin.meta.toml`, change `version = "0.5.0"` to `version = "0.6.0"`.

- [ ] **Step 3: Regenerate and verify**

Run: `uv run harness-kit gen && uv run harness-kit gen --check; echo "gen-check: $?"`
Expected: `gen-check: 0`

- [ ] **Step 4: Commit**

```bash
git add docs/skills/pr-merge-flow.md plugins/repo-hygiene/plugin.meta.toml .claude-plugin/ README.md
git commit -m "docs(pr-merge-flow): convergence behavior on the docs page; repo-hygiene 0.6.0

Claude-Session: https://claude.ai/code/session_01PrbE6PuQu5Yap914WA3ZdW"
```

(If `git status` shows other regenerated files, add those instead of guessing — commit exactly what `gen` changed plus the two edits.)

---

### Task 6: Verification sweep

**Files:**
- Read-only against the worktree; no new files.

- [ ] **Step 1: Retrospective dry-run.** Read the four edited/created skill files end-to-end and confirm each spec assertion has a home — for each, name the file+section that now dictates it:
  1. template-press #62 cycle 2 (4 P1 extensions of the PR's own principle) → defer, not fix (hard rule 2).
  2. smorin-harness #31 round 5 (CRITICALs in review-added code) → revert-first fires (hard rule 1).
  3. template-press #57 → ratchet trips by cycle 3; check-in offers merge-and-defer.
  4. template-press #18 late P1 → still fixed (arrival cycle never changes class).
  5. #27 / #33 / #37 small-PR behavior → unchanged (no ratchet before cycle 3; small in-scope bugs still fix-now).
  6. #17 comment-wording ask, #27 markdown nits on an executed plan doc → declined (value floor).
  7. #41 convention-conflicting import ask → refuted citing the convention.
  8. `--auto` + escalated thread → ready-report, never merge-over.
  Expected: 8/8 have a named home; fix any miss inline and amend the owning task's commit.

- [ ] **Step 2: Full-tree gates**

Run: `git grep -niE 'skill''smith' -- ':!.github/workflows/ci.yml'; echo "guard: $?"; uv run harness-kit gen --check; echo "gen: $?"`
Expected: `guard: 1`, `gen: 0`

- [ ] **Step 3: Quality gate.** Invoke the `skill-quality` skill against `plugins/repo-hygiene/skills/pr-merge-flow` **in this worktree** (gate against the worktree, never the placement). Expected: pass; fix findings inline and amend if not.

- [ ] **Step 4: Report.** Summarize the diff (`git log --oneline main..HEAD`, `git diff main --stat`) and hand back for PR creation — PR title `feat(pr-merge-flow): convergence guardrails — scope-gated triage, value floor, trajectory ratchet`.
