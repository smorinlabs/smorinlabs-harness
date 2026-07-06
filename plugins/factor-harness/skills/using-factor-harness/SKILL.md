---
name: using-factor-harness
description: Orient across the four factor-harness skills (using-factor-harness, factor-architect, factor-scan, factor-dedup) and route to the right one. factor-harness is the small skill set for two recurring code-quality activities: architecture-aware review/refactor and cross-implementation deduplication. Each workflow skill produces an inline spec that hands off to Superpowers writing-plans for the actual code changes. Use this skill when the user mentions architecture review, refactor opportunities, code scanning, bug hunting, or duplicated implementations — even if they don't name a specific factor-harness skill.
when_to_use: When the user starts a session that mentions architecture, refactoring, code review, bug hunting, quality checks, or duplicate implementations; when the user asks "what factor-harness skills exist?"; before invoking any specific factor-* skill if the right choice is unclear.
allowed-tools: Read
---

# using-factor-harness — orient across the bundle

factor-harness provides three workflow skills for recurring
code-quality activities. Each produces an inline spec that hands
off to Superpowers `writing-plans` / `executing-plans` for the
actual refactor. **factor-harness does the thinking; Superpowers
does the doing.**

See [`../_conventions.md`](../_conventions.md) for shared
conventions across the four skills.

---

## The three workflow skills

| Skill | Trigger | Output |
|---|---|---|
| [`factor-architect`](../factor-architect/SKILL.md) | A spec/plan was just produced (pre-execution) OR features have shipped (post-execution) and you want architectural review | Architectural review + refactor spec |
| [`factor-scan`](../factor-scan/SKILL.md) | You want a broad bug + quality + architectural-smell sweep over a code area | Per-finding inline spec |
| [`factor-dedup`](../factor-dedup/SKILL.md) | You have N implementations doing similar things and want to consolidate | Comparison + unified-design spec (or documented divergence) |

## Routing — when to use which

If the user says... | Reach for...
---|---
"I just got a plan back from /writing-plans, can you review it?" | `factor-architect`
"I just shipped feature X, anything to refactor?" | `factor-architect`
"Does this match our patterns?" / "Is this architecturally sound?" | `factor-architect`
"Scan this directory for bugs and quality issues" | `factor-scan`
"Audit these files" / "Review for problems" / "Code health check" | `factor-scan`
"What's wrong with this code?" / "Any issues here?" | `factor-scan`
"These N files look duplicated" | `factor-dedup`
"Consolidate these implementations" / "DRY this up" | `factor-dedup`
"5 commands doing the same thing" | `factor-dedup`

When the right choice is genuinely unclear, ask **one** clarifying
question rather than guessing — the wrong skill produces a wrong
shape of output.

## Two adjacent tools

factor-harness is one of three plugins in the user's tool family.
Each has a clear lane:

- **[project-harness](https://github.com/smorinlabs/project-harness)**
  — project-level lifecycle. Track what work needs doing
  (PROJECTS.md trunk, per-project files). Orient: what's next,
  what's in progress.
- **Superpowers** — execution discipline. Brainstorming, writing
  plans, executing plans, code review.
- **factor-harness (this plugin)** — quality activities sitting
  *between* project-level planning and per-task execution. Takes
  in a plan or shipped code; produces a spec the user feeds back
  into Superpowers.

The three plugins compose: project-harness might surface an
architectural concern as a refined project; `factor-architect`
runs the review and produces a refactor spec; Superpowers'
`writing-plans` turns that into an executable plan;
`executing-plans` runs the plan; the loop closes.

## Core conventions (every factor-* skill follows these)

These are condensed pointers; full text is in
[`../_conventions.md`](../_conventions.md).

1. **Pure workflow shape.** No trunk file. No managed-item IDs.
   No audit cycle. Skills are runbooks invoked when there's
   specific work to do.
2. **Per-finding interactive UX.** Every finding walks
   accept / modify / skip / mark-intentional. The user's
   judgment gets captured in the spec.
3. **Inline output.** Skills produce findings and specs in
   chat. No persistent artifacts. The user moves spec content
   to Superpowers manually.
4. **Read-only.** No factor-harness skill modifies code.
   Execution is Superpowers' job.
5. **Three subagents** — `factor-scanner` (parallel scan),
   `factor-comparator` (per-implementation read),
   `factor-researcher` (external pattern research with web
   access). Each calibrated for one shape of read; dispatched
   in parallel where the work allows.

## Iron laws (one per workflow skill)

Each workflow skill's SKILL.md states an inviolable discipline up
front:

- **`factor-architect`** — Existing precedent is not automatically
  good precedent. Refactor *both* when the precedent is poor.
- **`factor-scan`** — Severity defaults conservative. The user
  lifts severity, not the skill.
- **`factor-dedup`** — "These look duplicated" is a hypothesis,
  not a fact. The comparators may surface intentional divergence
  and the right answer is "leave them separate".

## What this skill does NOT do

- Does not invoke any of the three workflow skills. It teaches;
  the user invokes (or references this routing table).
- Does not modify code, files, or repo state.
- Does not maintain state across sessions. Each workflow skill is
  invoked freshly when its trigger fires.

## See also

- [`../factor-architect/SKILL.md`](../factor-architect/SKILL.md)
- [`../factor-scan/SKILL.md`](../factor-scan/SKILL.md)
- [`../factor-dedup/SKILL.md`](../factor-dedup/SKILL.md)
- [`../_conventions.md`](../_conventions.md)
- [`../../agents/factor-scanner.md`](../../agents/factor-scanner.md)
- [`../../agents/factor-comparator.md`](../../agents/factor-comparator.md)
- [`../../agents/factor-researcher.md`](../../agents/factor-researcher.md)
- [Superpowers](https://github.com/obra/superpowers) — execution
  toolkit factor-harness hands off to
- [project-harness](https://github.com/smorinlabs/project-harness)
  — sibling plugin for project lifecycle management
