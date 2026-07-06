# Cross-skill conventions for factor-harness

The four factor-harness skills are a coherent set, not four solo
authors. This document captures the conventions every SKILL.md in
this bundle relies on. Each SKILL.md references it instead of
restating these conventions inline.

These conventions are **specific to factor-harness**. The
project-harness conventions inspired the structure but factor-harness
deliberately diverges into a pure-workflow shape with no lifecycle
machinery — so most project-harness conventions don't apply.

---

## 1. Pure workflow shape

factor-harness skills are **runbooks**, not lifecycle managers.

- There is no trunk file (no `FACTORS.md` / `PROJECTS.md`).
- There are no managed-item IDs (no `F##` / `P##`).
- There is no audit cycle, no orient skill, no capture skill.
- A skill is invoked when the user has specific work in mind. It
  walks through analysis, surfaces findings, helps the user
  produce a spec, then exits.

If you find yourself writing logic to track state across
invocations, stop — that's not what these skills do. State lives
in the user's repo, in git, in the spec content the skill
produces. Not in factor-harness.

## 2. Per-finding interactive UX

Every finding surfaced by a skill walks through user judgment,
one finding at a time. The four allowed user responses are:

- **Accept** — the finding is real and the recommended action is
  right; carry it into the output spec.
- **Modify** — the finding is real but the recommended action
  needs adjustment; capture the user's amendment and carry the
  modified version into the output spec.
- **Skip** — defer this finding (don't include in the spec, but
  don't claim it's wrong; the user may revisit later).
- **Mark intentional** — the finding is *not* a problem; capture
  the user's reasoning so the spec documents *why* this thing
  was considered and consciously preserved. This is the most
  valuable response — it converts noise into permanent context.

**Why per-finding rather than batch.** When you batch-present 30
findings and ask "which do you want to fix?", users skim and
miss subtleties. Per-finding interaction forces a small attention
budget on each one and converts the user's domain knowledge
("oh, that's intentional because of X") into spec content.

## 3. Inline output, no persistence

Skills produce findings and specs **inline in chat**.

- factor-harness skills do **not** write files to the project
  tree at runtime. (This is a runtime convention; the
  implementation files of factor-harness itself are obviously
  written, but that's separate.)
- The user is responsible for routing the spec content to its
  destination — typically Superpowers `writing-plans`.
- There is no `docs/factors/` tree, no per-skill output dir, no
  artifact templates.

**Why inline.** Persistence is a future-self problem. Inline
output forces the spec to be useful *right now* in the
conversation; if it's good enough to act on, the user
copies it into writing-plans. If it isn't, no stale artifact
is left behind to mislead.

## 4. Read-only with respect to the codebase

No factor-harness skill or subagent modifies code or
configuration in the repo being analyzed. Code changes are
Superpowers' responsibility — `writing-plans` produces a plan,
`executing-plans` runs it. factor-harness produces the *spec
that becomes the plan*.

This boundary is load-bearing. It keeps factor-harness skills
small and focused; it leverages Superpowers' execution
discipline (TDD, commit hygiene, review gates) rather than
duplicating it.

## 5. Subagent dispatch patterns

The plugin ships three specialized subagents under `agents/`:

| Subagent | Used by | Dispatch shape |
|---|---|---|
| `factor-scanner` | factor-scan (primary), factor-architect (occasional) | **Parallel** — one per file or area being scanned |
| `factor-comparator` | factor-dedup (primary), factor-architect | **Parallel** — one per implementation or precedent file |
| `factor-researcher` | factor-architect (primary), factor-dedup (when ecosystem matters) | **Sequential** — one targeted research question per dispatch |

**Why subagents.** The skills work in isolation-friendly bursts
(scan many files, compare many implementations). Dispatching
subagents in parallel is faster and keeps the calling skill's
context focused on synthesis rather than raw file content.

**Why three rather than one general agent.** Each agent is
calibrated for a specific shape of read: scanners look for
issues, comparators describe structure for cross-comparison,
researchers consult external references. The prompts and
disciplines differ enough to warrant separate files.

## 6. Precedent caveat

Existing precedent in a codebase is **not automatically good
precedent**. When `factor-architect` finds that proposed code
follows existing patterns, it must separately verify the
pattern is itself worth following.

If precedent is poor, the recommendation is to refactor *both*
the new code and the precedent — never "follow the bad pattern
for consistency". Extending a known-bad pattern is how systems
calcify.

This caveat exists because reflexive precedent-following is the
single most common failure mode of architectural review. A skill
that just checks "does this match existing code" produces dead
weight. A skill that asks "is this a good pattern, AND does this
match it?" produces lift.

## 7. Severity discipline

Findings default to **conservative** severity:

- **Minor** is the safe default for any finding without strong
  evidence of impact.
- **Important** requires concrete evidence (a measurable
  consequence, a user-visible bug path, a clear maintenance
  cost).
- **Critical** requires evidence of likely production impact
  (a real bug being shipped, a security exposure, a data
  integrity risk).

Subagents report what evidence supports. Calling skills do not
inflate severity. If the user wants something marked higher,
they say so during the per-finding walk.

**Why conservative.** False-positive critical findings train the
user to ignore the skill's output entirely. One inflated
finding poisons every future invocation.

## 8. Iron law per skill

Each workflow skill states a single inviolable discipline up
front in its SKILL.md. The current iron laws are:

- **factor-architect** — Existing precedent is not automatically
  good precedent.
- **factor-scan** — Severity defaults conservative; user lifts
  severity, not the skill.
- **factor-dedup** — "These look duplicated" is a hypothesis,
  not a fact; the comparators may surface that the divergence
  is intentional.

Iron laws are stated where they cannot be rationalized away
under deadline pressure. They name the failure mode the skill
is designed to prevent.

## 9. Frontmatter shape

Every workflow `SKILL.md` follows this frontmatter:

```yaml
---
name: factor-<verb>
description: <one-paragraph third-person summary including when to invoke. ≤500 chars.>
when_to_use: <specific user phrases / contexts that trigger the skill>
allowed-tools: <space-separated tool list>
---
```

Subagent files in `agents/` use a simpler frontmatter (matching
the project-harness convention):

```yaml
---
name: factor-<role>
description: <one-paragraph summary of what this subagent investigates>
---
```

Subagent tool restrictions live in **prose at the top of the
body**, not in frontmatter. (Body declarations like "You are
read-only" / "You do not have web access" do the work.)

## 10. Handoff to Superpowers

The output of every factor-harness workflow is a spec ready for
Superpowers. The expected handoff shape:

1. The skill produces a spec inline in chat.
2. The user invokes `superpowers:writing-plans` (or pastes the
   spec into a fresh conversation that does).
3. `writing-plans` writes a plan to
   `docs/superpowers/plans/YYYY-MM-DD-<topic>.md`.
4. `superpowers:executing-plans` (or
   `superpowers:subagent-driven-development`) runs the plan.

A factor-harness spec format is not formal — it's whatever
content the user can hand to writing-plans and have it produce
a sensible plan from. Typically that means:

- Goal (one sentence)
- Architecture (2–3 sentences)
- File-level changes
- Acceptance criteria
- Optional: risks, sequencing notes
