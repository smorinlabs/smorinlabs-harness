---
name: using-project-harness
description: Bootstraps the project-harness bundle by establishing its five skills, running a four-step idempotent setup (PROJECTS.md trunk, AGENTS.md/CLAUDE.md mentions, planning-system question, references-block convention nudge) on first use per repo, and routing hand-edits through the right sibling skill. Use whenever the user mentions a project, plan, roadmap, milestone, or backlog, or starts a session in a repo with project-management state — even if they do not explicitly ask to "set up" or "init" anything. Meta-skill — never edits projects/ files itself.
when_to_use: Whenever the user mentions a project, plan, roadmap, milestone, or backlog; when starting a session in a repo with project-management state; before editing PROJECTS.md or projects/ by hand; when the user asks to "set up project-harness" or "init project-harness".
allowed-tools: Read Write Bash
---

# using-project-harness

**Core principle:** project-harness is a *system*, not a grab bag.
Editing `PROJECTS.md` or files in `projects/` by hand bypasses the
discipline that makes the system reliable. Route every project-state
change through one of the four workflow skills.

<EXTREMELY-IMPORTANT>
If you think there is even a 1% chance a project-harness skill might
apply to what you are doing, you ABSOLUTELY MUST invoke the skill.

IF A PROJECT-HARNESS SKILL APPLIES TO YOUR TASK, YOU DO NOT HAVE A
CHOICE. YOU MUST USE IT.

This is not negotiable. This is not optional. You cannot rationalize
your way out of this.
</EXTREMELY-IMPORTANT>

## Instruction priority

User instructions in `CLAUDE.md`, `AGENTS.md`, or direct chat
override these conventions. The rule is: **user > skills > default**.
If the user says *"don't run audit"*, don't run audit. The user is
in control.

## The five skills

| Skill                  | Use when…                                              |
|------------------------|--------------------------------------------------------|
| `using-project-harness`| starting a session, or about to hand-edit `PROJECTS.md`|
| `project-next`         | the user asks "what's next?" / "what should I work on?"         |
| `project-add`          | the user has an idea to capture                        |
| `project-refine`       | the user wants to flesh out / scope / decompose a project |
| `project-audit`        | the user asks "is everything in order?" / "audit"      |

Skill priority within the bundle: `using-project-harness` orients the
session, `project-next` orients within the trunk, then one of
`project-add` / `project-refine` / `project-audit` runs based on the
user's intent.

## Bootstrap

On invocation, run the **four-step bootstrap** if the per-repo
config file `.project-harness/project-harness.config.json` does
not exist OR has `init_done: false`:

1. **PROJECTS.md trunk** — scaffold from `templates/PROJECTS.md`
   if missing.
2. **AGENTS.md / CLAUDE.md mentions** — append a short pointer
   block if either file is missing or doesn't contain
   `project-harness`.
3. **Planning system** — ask once whether the user uses
   superpowers, another system, or none; persist the answer and
   the plan/spec search paths so the references-block helper
   adapts.
4. **References-block convention nudge** — point at the format
   spec and the discovery helper; do not backfill existing
   projects (that's `project-audit`'s job).

Each step is idempotent — completed steps are recorded in the
config file and skipped on subsequent runs. A fully-bootstrapped
repo costs one config-file read.

See `references/bootstrap.md` for the full procedure: the config
schema, the standard pointer block written to AGENTS.md/CLAUDE.md,
the planning-system branches, and the re-init escape hatch.

`project-add` has its own bootstrap path for the case where the
user invokes it directly in a fresh repo. The two paths are
equivalent; this one runs when the user enters via
`using-project-harness`.

## Red Flags

These thoughts mean **STOP** — you're rationalizing:

| Thought | Reality |
|---------|---------|
| "I'll just edit PROJECTS.md to add this row" | `project-add` reserves the next ID atomically and avoids merge collisions. Editing by hand loses that. |
| "I'll flip the trunk glyph from `[?]` to `[ ]` myself" | `project-refine` enforces the explicit-promote gate. Hand-flips skip the scope walkthrough. |
| "I'll just rename the file" | Filename, trunk row, and cross-references must update in lockstep. Use `project-refine`. |
| "These drift findings look obvious, I'll fix them all silently" | `project-audit` asks per finding because intentional drift exists and you cannot tell it from forgotten drift. |
| "I'll work on P21 now and capture the new idea later" | Capture is cheap. Use `project-add` first, then return. Lost ideas are the bigger cost. |
| "I'll skip `project-next` and ask the user directly" | `project-next` brings the trunk and recent-touch info into context. Asking blind costs a turn. |
| "This is just a small edit" | Small edits are how drift starts. The cost of running the right skill is one extra round-trip; the cost of drift is hours of audit later. |
| "AGENTS.md/CLAUDE.md mentions look fine, I'll skip step 2" | The stale rule is mechanical: file missing OR doesn't contain `project-harness`. Don't second-guess it from prose vibes — let the rule fire and either confirm or decline once. |
| "I'll write the standard block into AGENTS.md without asking" | Bootstrap writes are gated on `[y/n]`. Silent edits to repo-level docs are exactly the surprise behavior the project's CLAUDE.md warns against. |
| "User picked 'other' for planning system, I'll guess where their plans live" | Don't guess. Ask one follow-up for the paths and persist the answer. The references-block helper depends on this being correct. |

## Composition with other frameworks

The four workflow skills *point at* other frameworks for execution.
They never invoke them.

| Want to do… | Reach for… |
|---|---|
| Decide what to work on | `project-next` (this bundle) |
| Capture an idea | `project-add` (this bundle) |
| Flesh out / scope / decompose | `project-refine` (this bundle) |
| Verify state is consistent | `project-audit` (this bundle) |
| Write a spec or implementation plan | Superpowers (`writing-plans`) |
| Execute a plan / write code | Superpowers (`executing-plans`), Claude Code, your editor |
| Run tests | Your test runner directly |
| Truly inline edits to a project file (e.g. fix a typo) | Just edit the file |

The last row is real: trivial edits like fixing a typo in a
description don't need a skill. The skills exist for *state changes*
(adding, scoping, decomposing, auditing) — not character-level fixes.

## Trunk pointer block

If `PROJECTS.md` is missing the project-harness pointer block, paste
this into the *Conventions* section so future contributors know the
bundle exists:

```markdown
### Project workflow skills (plugin: project-harness)

- `using-project-harness` — bootstrap: when to use which skill below
- `project-next` — orient: what's in progress, what's next, what's recently touched
- `project-add` — capture an idea (≤4 questions, reserves the ID with a commit)
- `project-refine` — flesh out / scope / decompose an existing project
- `project-audit` — verify state matches conventions; fix per finding
```

The full initial-state trunk (with status legend, conventions, and
this pointer block) is at `templates/PROJECTS.md` in the plugin.

## What this skill deliberately does not do

- Does not invoke any of the four workflow skills. It teaches; the
  user invokes.
- Does not encode project conventions (filename rules, glyph rules,
  TDD bias). Those live in `skills/_conventions.md` and the per-skill
  SKILL.md files, plus the trunk's own conventions section.
- Does not run audit checks or capture ideas. If the user is ready
  to do something concrete, point them at the right skill and exit.
- Does not edit `AGENTS.md`, `CLAUDE.md`, `PROJECTS.md`, or any
  other repo file without an explicit `[y/n]` confirmation per step.
  Silent writes to repo-level documentation would surprise users.
- Does not backfill `**References**` blocks in existing projects.
  That's `project-audit`'s job (run
  `project-audit --all --references-block` after the bootstrap).
- Does not re-prompt for the planning system once it is set in the
  config. To switch systems, the user edits the config file
  manually — see `references/bootstrap.md` for the re-init escape
  hatch.

## See also

- `_conventions.md` — shared prose conventions for the four workflow
  skills.
- `templates/PROJECTS.md` — initial-state trunk to copy into a fresh
  repo.
- `references/bootstrap.md` — full four-step bootstrap procedure,
  config schema, AGENTS.md/CLAUDE.md standard block, planning-system
  branches.
- `skills/project-audit/references/references-block.md` — format
  spec and discovery helper for the per-project `**References**`
  block; pointed at by step 4 of the bootstrap.
