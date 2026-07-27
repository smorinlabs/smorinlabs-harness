# PR Merge Flow — Convergence Guardrails — Design

**Date:** 2026-07-27
**Status:** Implemented 2026-07-27
**Target:** `plugins/repo-hygiene/skills/pr-merge-flow` (SKILL.md, `references/triage.md`, new `references/convergence.md`)

## Problem

On large PRs, the review-resolution loop diverges instead of converging. Each
push of review fixes draws a fresh reviewer wave (~10 minutes later), and the
finding rate plateaus rather than decaying, because fixes add code and new code
is new review surface. Measured across eleven episodes in four repos
(template-press, smorin-harness, smorinlabs-harness, harness-kit; transcripts
and GitHub REST data, 2026-07-07 → 2026-07-27):

- **template-press #41** (+6,745 lines): 12 review cycles over 27 hours;
  finding rate plateaued at 3–4/cycle from cycle 3 onward; review-driven fixes
  added 2,997 insertions against a 3,595-insertion feature (hardening cost ≈
  feature cost); a measured ~7% of fix commits shipped a defect of their own.
- **template-press #57** (docs-only): 55 threads, 109 comments, 18 hours; the
  in-session diagnosis — "the review is recursing on its own output: each fix
  paragraph mints fresh reviewable claims" — plus one check that went through
  four refinement rounds (exact → prefix → normalized → attached options) with
  no endpoint. Five more findings arrived *after* the merge.
- **template-press #62**: waves of 11 → 4 → 5 new findings — the run declared
  "the review is converging" eighteen minutes before a wave larger than its
  predecessor, and reported "11 → 4 → 2" by silently switching metric from
  findings-received to fixes-chosen. Round-2 severity was 4-for-4 P1. Roughly
  1,000 lines were added to the PR after review started. Session ended cut
  off: 20 open threads, 0 resolved, unmerged, CI green throughout.
- **smorin-harness #31**: both round-5 CRITICALs were introduced by round-4
  fixes; implementation grew +59% (1,180 → 1,878 lines) from review fixes
  alone. The most dangerous defect of the project (destructive `--force`
  following symlinks) entered *as a review fix* that expanded scope beyond the
  spec; the resolution that finally converged was reverting it (−39 lines),
  not fixing it harder.
- **harness-kit #3**: symlink findings arrived 1 → 3 → 1 → 2, each wave
  targeting the previous wave's fix (`chmod`-fallback and containment-anchor
  lineage traceable commit by commit).

Small PRs are unaffected: #15/#17/#18/#27/#33/#37 and harness #29/#30 all
converged in 1–2 rounds at a cost of 1–2 commits and ~20 minutes. The current
skill is correct in that regime and must not regress there.

Every divergent episode was terminated by the **user**, never by the process
("take a medium step back"; "are we converging or diverging… are we doing
scope creep?"). A mid-flow convergence directive softened behavior but did not
stop code being written — guidance-as-vibes does not hold; the control must be
structural.

### Root cause in the skill

1. **The verdict rubric has no scope axis.** `references/triage.md` offers
   Valid / Invalid / Unclear, and Valid mandates "minimal fix, conventional
   commit, push". A valid architectural redesign and a valid off-by-one
   receive the identical treatment. Observed refutation rate before user
   intervention: ~9%; deferrals: ~2 in ~35+ findings.
2. **The Iron Law funnels toward fixing.** "Every thread resolved as fixed or
   refuted" leaves no honest disposition for a valid-but-out-of-scope finding,
   so it gets fixed.
3. **A Red Flags row forbids the needed check-in.** "Valid is not unclear…
   Ask only when a verdict is genuinely undecidable, never about strategy"
   was hardening against under-triage; on a diverging PR it prohibits exactly
   the conversation that saved every divergent episode.
4. **The cycle bound counts cycles, not divergence.** It never fired in
   practice (sessions ended on cycle 3, or waves outlasted poll windows), and
   it carries no memory of what kind of findings each round produced.

### What already worked (in-corpus precedent)

- **#27**: findings split fix-now vs. defer-(tracked); the architectural ask
  mapped to an existing task ID, a public triage comment posted, deferral
  surfaced to the user — merged in one round.
- **#58**: refute-and-defer posture from the start — 7 → 7 → 0 in 53 minutes.
- **#41 close-out**: residue batch-filed as ten follow-up issues, then merge.
- **#20**: the agent refused to unilaterally fix a P1 that reopened a settled
  design decision and asked the user with options.
- **#31**: the stopping rule that worked — "is the design still being
  questioned? Another round reviews churn, not the product."
- Refutation works on bots: CodeRabbit formally withdrew a finding on #41
  after reasoned pushback.

## Decision

Three mechanisms with distinct roles, adopted together:

> **Scope-gated triage decides what each comment deserves (the policy).
> Trajectory measurement decides when the loop is done deserving (the
> sensor). Merge-and-defer is the named ending the run converges to (the
> exit).**

Not adopted: muting reviewers, skipping comment collection, or any reduction
in read-verify-reply discipline. Every thread is still read, verified, and
answered; what changes is the set of honest outcomes and the pressure toward
"fix".

## 1. Scope axis in the triage rubric

`references/triage.md` verdict step gains a second, mandatory classification
for findings judged **valid** (verify-before-believing is unchanged):

| Class | Test | Action |
|---|---|---|
| **Small in-scope bug** | Defect in code this PR touched; the fix corrects lines rather than adding a mechanism; no new invariant or subsystem | Fix now — current behavior |
| **Valid, out-of-scope** | Hardening/robustness/feature beyond the PR's stated goal, or a defect that predates the PR | **Defer**: create the tracked item first, then reply `Deferred to <ref> — <one line>`, resolve the thread |
| **Architectural** | Asks for a new mechanism, redesign, or trust-boundary change | **Never fixed in this PR**: post one design-question comment on the PR, mark the thread *escalated* in the ledger, keep triaging other threads, hold the merge at the gate |

Classification signals that proved reliable in the corpus, to be listed in the
rubric: CodeRabbit's `Heavy lift` tag ≈ architectural; redesign imperatives
("define/introduce/restructure…", "compute the fixed-point mapping",
"define an allowlist or sandbox boundary"); a fix that would add more lines
than it touches leans out-of-scope.

Three hard rules, each named for the observed rationalization it blocks:

1. **Fix-of-fix considers revert first.** A finding against code added during
   this review triggers "would reverting the earlier fix to spec semantics
   close this more cheaply than extending it?" before any fix-the-fix commit
   (#31's −39-line resolution).
2. **Extension is a defer signal, not a fix mandate.** "The principle it
   extends is the PR's own" was the exact justification that drove #62's
   cycle 2; it now routes to *defer* by default.
3. **Late arrival changes nothing.** The class test is about what a finding
   *asks for* and *where the defect lives*, never about which cycle it arrived
   in. A genuine ship-breaking P1 in cycle 4 is still a small in-scope bug
   (protects the #18 release-breaker and #20 wave-2 P1 cases).

### The value floor for small findings

A commit is never free. Each review-fix commit in the corpus carried three
costs regardless of size: a ~7% measured chance of shipping its own defect
(#41's fix-regression rate), a fresh reviewer wave ~10 minutes later on the
new surface, and a bite out of the cycle budget. A small fix therefore earns
a commit only when its value clears that floor. The one-line test: **would a
maintainer, holding the repo's conventions, ask for this change unprompted?**

Dispositions within valid, small, in-scope findings:

| Finding | Disposition |
|---|---|
| Functional bug — behavior is wrong | Fix |
| Real typo — wrong word, command, or meaning in shipped text | Fix |
| Style/lint a repo convention or CI gate actually enforces | Fix (the gate would fail — functionally a bug) |
| Arbitrary style — reviewer taste with no convention behind it | **Decline**: reply "style-only; no repo convention requires this", resolve |
| Contradicts a repo convention | **Refute citing the convention** (proven: CodeRabbit formally withdrew such a finding on #41) |
| Arguable value with real blast radius (e.g. "remove redundant guard" on a safety-critical path) | **Decline citing risk asymmetry** — arguable upside, unarguable regression cost |

This supersedes triage.md's current "apply when they match repo conventions
and are cheap": *cheap to type is not cheap in system cost*, and "cheap"
disappears as a justification.

**Declined is a fourth first-class disposition**, distinct from refuted (the
claim is false) and deferred (valuable, but not here). Valueless findings are
never deferred — routing style noise into the tracker pollutes it and buries
real deferrals. Declined threads get the same reply-and-resolve treatment.

**Wave composition becomes a convergence signal.** A wave dominated by
style/minutia (high declined-fraction, severities draining toward Minor) is
positive evidence the reviewers have run out of functional bugs — presented
at the check-in as support for *merge now* (#41's own session noticed this:
"all P2 — severity dropping").

**The Iron Law extends, it does not weaken:** every thread resolved as
**fixed, refuted, declined-with-reason, or deferred-with-reference**.
Escalated threads are the one state the agent may not resolve on its own:
they stay open, they hold the merge at the gate, and only the user's
disposition (fix here / defer / redesign) closes them.

### Deferral destinations — follow the repo's own evidence

Detection joins step 1 (which already reads the repo's CLAUDE.md), first
match wins:

1. `PROJECTS.md` / `projects/` present → deferrals become task rows in the
   owning project (or a new idea stub via the project conventions).
2. Repo history shows tracker usage — `gh issue list` non-empty or issue
   references in recent commits/PRs → GitHub issues (the #41 → #42–#51
   pattern).
3. An external tracker is configured for the repo (e.g. Linear) → that
   tracker.
4. **No evidence → ask the user once**, and record the answer as
   `defer-target` in `.claude/pr-merge-flow.local.md` so the question is
   never re-asked for that repo.

A deferral without a created, referenced artifact is not a deferral — it is a
silent drop. The corpus shows the rot risk directly: a #56 finding "never
replied to or fixed" resurfaced two PRs later, and #31's deferred-minors
issue needed explicit close-out tracking. Accordingly, the end-of-run report
(all modes) lists every deferral with its reference.

## 2. Trajectory measurement in the ledger

The thread ledger (SKILL.md step 3) gains per-wave, per-reviewer columns:

- findings received (count, severity mix) — **per bot**, because reviewers
  stagger: Codex habitually lands after Copilot/Greptile (a 5 → 10 "jump" on
  #15 was staggering, not escalation) and CodeRabbit has arrived +14 hours
  late (#20). Cross-cycle comparison is same-bot only.
- fraction of the wave targeting code added during this review (fix-of-fix).
- declined fraction and severity drain (§1 value floor) — a wave that is
  mostly style/minutia is convergence evidence, not work.

**Convergence is always measured in findings-received. Fixes-chosen is banned
as a convergence metric** — the #62 "11 → 4 → 2" substitution is the named
anti-pattern.

**The bar ratchets** when any of these trips:

- cycle ≥ 3, or
- same-bot new findings not decreasing wave-over-wave, or
- a majority of a wave targets review-added code (the second-derivative
  signal: the loop is reviewing its own output).

Under the ratcheted bar, only would-ship-broken defects in the PR's own diff
get code; everything else defaults to defer, decline, or refute — except
architectural findings, which still escalate; the ratchet never downgrades
an escalation. The scope axis of §1
still governs *what class* a finding is; the ratchet only hardens *which
classes* may produce commits.

## 3. The check-in gets teeth

The step-5 check-in (at the cycle bound, or when the ratchet has tripped in
two successive waves) reports:

- the trajectory line, e.g. `11 → 4 → 5 · cycle 3 · majority on review-added
  code · severity rising`;
- the stopping question: **"is the design still being questioned, or only
  the churn?"**;
- per-thread recommended dispositions (fix / defer-to-<ref> / decline /
  refute / escalated);

and offers exactly three endings:

1. **Continue until clean** — existing 10-minute-wall-clock escape hatch,
   unchanged.
2. **Merge and defer the residue** — first-class now: batch-create the
   deferral artifacts, reply-and-resolve each thread with its reference,
   proceed to the merge gate. Offered only when no thread is escalated —
   escalations hold the merge until the user disposes of them.
3. **Pause for redesign** — the escalated architectural threads become the
   agenda; the run downgrades to a ready-report that names them.

`--auto` cannot ask: architectural escalations and ratchet-tripped check-ins
downgrade the run to a ready-report naming the open items — the same
mechanism the mode already uses for undecidable threads. `cycle-bound` /
`continue-until-clean` prefs keep their current meaning.

## 4. Red Flags corrected and extended

The row *"Every finding is valid, but there are a lot — let me ask how to
proceed"* splits:

- many valid **small in-scope** findings → proceed; the rubric names the
  action (current rule, still correct);
- findings that are **extensions or architecture** → that *is* a scope
  question; classifying and (for architectural) escalating is mandatory, not
  forbidden.

New rows, one per observed rationalization:

| Thought | Reality |
|---|---|
| "Findings dropped 11 → 4 → 2, we're converging" | Count findings received per bot, not fixes chosen. #62's round 3 received 5, not 2. |
| "This extends the PR's own principle, so it's in scope" | Extension is the defer signal, not a fix mandate. |
| "The count doubled — the review is escalating" | Bots stagger. Compare same-bot across waves before calling divergence. |
| "One more fix for the fix and this thread class is closed" | Fix-of-fix is the divergence engine. Consider reverting to spec semantics first. |
| "It's a one-word fix, cheaper to just do it" | Cheap to type is not cheap in system cost: every commit carries ~7% regression risk and draws a fresh review wave. Value must clear the floor. |
| "Fixing the nit is more polite than declining it" | A reasoned decline is the etiquette here — bots accept it and have formally withdrawn findings. Fixing nits trains the loop that nits earn commits. |

## 5. Deep review gets the same gate

Dispatched subagent reviewers produced 8–33 findings per round in the corpus
versus the bots' 1–5 — they are the heavier divergence driver. Step-8 deep
review findings enter the same ledger with the same scope axis and count
toward the same ratchet. Deep review remains opt-in and pre-merge-once; no
exemption from classification.

## Change map

| File | Change |
|---|---|
| `SKILL.md` step 1 | Deferral-destination detection joins settings resolution; new pref key `defer-target` |
| `SKILL.md` step 3 | Ledger schema: per-wave per-bot columns, fix-of-fix fraction, `escalated` state |
| `SKILL.md` step 4 | Scope axis summary + the three hard rules + value floor; Iron Law wording extended to fixed/refuted/declined-with-reason/deferred-with-reference, escalation carve-out |
| `SKILL.md` step 5 | Ratchet triggers; check-in report contents; three endings; `--auto` downgrade |
| `SKILL.md` step 7/9 | End-of-run report lists every deferral with reference (all modes) |
| `SKILL.md` step 8 | Deep-review findings share ledger, scope axis, ratchet |
| `SKILL.md` Red Flags | Split one row; add four rows (§4) |
| `references/triage.md` | Verdict rubric: scope classification table, value floor + declined disposition (replaces the "cheap → apply" style rule), signals list, defer reply etiquette, destination-detection details |
| `references/convergence.md` (new) | Trajectory bookkeeping, ratchet definition, staggering correction, check-in template — kept out of SKILL.md to respect progressive disclosure |
| `plugin.meta.toml` / marketplace | Version bump + regen per harness conventions (implementation-plan detail) |
| Skill `description` frontmatter | Add convergence/deferral phrasing so triggering reflects the new behavior; keep collision-safe |

## Out of scope

- Polling, quota, and browser-fallback behavior — untouched.
- Reviewer configuration (which bots run, their settings) — not this skill's
  surface.
- Auto-resolving threads without replies, or any reduction in
  read-verify-reply discipline.
- Merge-strategy selection (governed by the merge-commit-default design).
- Retroactive cleanup of existing deferred-item backlogs (#42–#51, issue
  #32) — tracked in their own repos.

## Verification

1. **Retrospective dry-run.** Apply the new rubric on paper to the three
   flagship episodes and confirm the dictated behavior differs where it
   should: #62 cycle 2 (4 P1 extensions) → defer, not fix; #31 round 5 →
   revert-first fires; #57 → ratchet trips by cycle 3 and offers
   merge-and-defer; #18's late P1 → still fixed (class test, not cycle test);
   #27 / #33 / #37 small-PR behavior → unchanged; #17's comment-wording ask
   and #27's markdown nits on an executed plan doc → declined under the value
   floor; #41's convention-conflicting import ask → refuted citing the
   convention.
2. **Skill-quality gate** against the worktree (frontmatter, house style,
   docs completeness, collision check on the updated description), per the
   gate-against-the-worktree rule.
3. **Live pilot.** First real run on the next mid-size PR observes the new
   check-in and deferral flow end-to-end before the design is considered
   proven; template-press #62 (open, 20 threads, mid-divergence) is the
   natural pilot.
