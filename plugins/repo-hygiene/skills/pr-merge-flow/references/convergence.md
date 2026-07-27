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

- the trajectory line — e.g. `11 → 4 → 5 · cycle 3 · majority on review-added
  code · severity draining`;
- the stopping question: **is the design still being questioned, or only
  the churn?**;
- per-thread recommended dispositions (fix / defer-to-<ref> / decline /
  refute / escalated);

then ask one question with three endings — continue until clean (10-minute
wall clock), merge and defer the residue, or pause for redesign. Details
and mode behavior live in SKILL.md step 5.
