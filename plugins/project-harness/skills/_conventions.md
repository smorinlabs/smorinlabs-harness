# Cross-skill prose conventions

Every `SKILL.md` in `project-harness` follows the same shape so the
five files read as a set, not five solo authors. This document is the
single source — each `SKILL.md` references it instead of restating
these conventions inline.

The conventions are adapted from [obra/superpowers][superpowers], a
larger and battle-tested skill bundle. Citations point at specific
files in that repo so a curious reader can compare.

[superpowers]: https://github.com/obra/superpowers

---

## 1. Frontmatter

```yaml
---
name: project-<verb>
description: <Third-person verb-phrase summary of what the skill does. ≤500 chars.>
when_to_use: <Specific user phrases / contexts that trigger the skill. ≤500 chars.>
arguments: [<positional-arg-name>]          # optional
argument-hint: "[example arg shape]"        # optional, paired with arguments
allowed-tools: Read Edit Write Bash Agent   # scoped per skill
---
```

### Field-by-field guidance

- **`name`** — kebab-case, lowercase letters/numbers/hyphens, ≤64
  chars, never `anthropic` or `claude` (per the Anthropic spec —
  see References). Project-harness uses the `project-` prefix
  except for the meta-skill (`using-project-harness`). Action-
  oriented form (`project-add`) is allowed by the spec as an
  alternative to gerund form (`adding-projects`).

- **`description`** — third-person verb-phrase describing what
  the skill *does*, not who triggers it. The Anthropic best-
  practices doc shows this canonical shape: *"Generate
  descriptive commit messages by analyzing git diffs."* Avoid
  first or second person. Front-load the key verb.

- **`when_to_use`** — Claude Code-specific field appended to
  `description` in the skill listing. Put trigger phrases the
  user might say here (*"when the user asks 'what's next?'"*).
  Combined `description + when_to_use` is truncated at 1,536
  chars in the listing — front-load the key use case.

- **`arguments`** — list of named positional args. Project-harness
  declares `arguments` on the three skills users may invoke
  positionally (`project-add`, `project-refine`, `project-audit`).
  Bodies do **not** yet use `$name` substitution — args still
  parse via the implicit `ARGUMENTS:` append. Substitution is a
  future option once positional invocation usage stabilizes.

- **`argument-hint`** — autocomplete hint shown after the skill
  name in the `/`-menu. Match the shape the user types
  (`"[P##]"`, `"[P##] [--check]"`).

- **`allowed-tools`** — pre-approve the tools the skill needs so
  it runs without permission prompts mid-flow. Scope per skill:
  read-only skills (`project-next`, `using-project-harness`)
  don't get `Edit`/`Write`; only skills that dispatch subagents
  (`project-refine`, `project-audit`) get `Agent`. Bash uses
  the bare `Bash` form (any subcommand) on all five skills —
  narrow `Bash(git add *)` patterns belong on focused skills
  like `/commit`, not on multi-mode workflow skills.

## 2. Body skeleton (every workflow skill)

```markdown
# <skill-name>

**Core principle:** <one sentence — adopted from superpowers' opening
line convention>.

## When to use
<bullet list of trigger phrases the user might say>

## Iron Law (only for discipline skills)
<see §3>

## What it does
<numbered process — actions, not outcomes>

## What it deliberately does not do
<explicit non-goals — closes "while I'm here..." rationalizations>

## Red Flags
<table — see §4>

## Common Rationalizations (only for discipline skills)
<table — see §5>

## See also
<sibling skills as text pointers; never auto-invoke them>
```

`using-project-harness` is meta and uses a slightly different
skeleton; see its SKILL.md.

## 3. Iron Law

A single bold rule, block-quoted, near the top of the body, used only
for skills that need to enforce structural discipline.

> **NO MORE THAN THREE QUESTIONS.** Friction kills idea capture. If
> the user wants depth, that is `project-refine`'s job.
>
> No exceptions: not "just one clarifying question", not "the user
> seems to want depth", not "I'll ask the third combined". Three is
> the cap.
>
> Violating the letter of this rule is violating the spirit of it.

Three structural moves are mandatory after the headline:

1. **No-exceptions list** — close specific rationalizations. (Format
   adopted from `test-driven-development/SKILL.md:39-45`.)
2. **"Violating the letter is violating the spirit"** — defeats
   lawyering. (Adopted from
   `test-driven-development/SKILL.md:14`,
   `systematic-debugging/SKILL.md:14`,
   `verification-before-completion/SKILL.md:14`.)
3. The Iron Law is restated nowhere else. The point is that one rule
   is one rule.

In project-harness:

- `project-add` — `NO MORE THAN THREE QUESTIONS`
- `project-refine` — `NO PROMOTION WITHOUT EXPLICIT CONFIRMATION`
- `project-audit` — `NO FIX WITHOUT POST-FIX RE-VERIFICATION`
- `project-next` and `using-project-harness` are not
  discipline-enforcing — they have no Iron Law.

## 4. Red Flags table

Two columns: **Thought** | **Reality**. Verbose first-person thoughts
in the left column, terse realities in the right. Adopted from
`using-superpowers/SKILL.md:78-95`,
`test-driven-development/SKILL.md:215-232`,
`systematic-debugging/SKILL.md:215-232`.

| Thought | Reality |
|---------|---------|
| "This is just a simple question" | Questions are tasks. Run the skill. |
| "I'll just ask one more question to be thorough" | Three is the cap. Excess belongs in `project-refine`. |

Seed each table with **4–6 rows** of thoughts the model is genuinely
likely to rationalize when running this skill. Generic rationalizations
("I'll skip TDD just this once") belong in `using-project-harness` —
each workflow skill's table is for the rationalizations specific to
*that skill*.

## 5. Common Rationalizations table

Distinct from Red Flags. Red Flags are introspective thoughts the
model has *while* running the skill ("this feels productive"); Common
Rationalizations are excuses for not following the rule ("I'll test
after"), each with a Reality that closes the loophole. Format adopted
from `test-driven-development/SKILL.md:256-287`,
`verification-before-completion/SKILL.md:64-75`.

| Excuse | Reality |
|--------|---------|
| "The user clearly wants depth, I'll ask follow-up Qs" | They will get depth in `project-refine`. The cap is the cap. |
| "Iron Law is for the average case, this is special" | Every case is "special" by some criterion. The rule survives that. |

Discipline skills (`project-add`, `project-refine`, `project-audit`)
ship **both** tables. `project-next` and `using-project-harness`
ship Red Flags only.

## 6. One-question-at-a-time, iteratively

This is the most important interaction convention. It applies to
`project-add` (Iron-Law-capped at 3) and `project-refine` (multi-turn,
no cap).

> *"For appropriately-scoped projects, ask questions one at a time
> to refine the idea / Prefer multiple choice questions when possible,
> but open-ended is fine too / Only one question per message — if a
> topic needs more exploration, break it into multiple questions."*
>
> — `superpowers/skills/brainstorming/SKILL.md:75-77`

The rule is **not** "decide on N questions, then list them". It is
"ask one, *re-evaluate based on the answer*, then decide what (if
anything) to ask next". Multiple-choice options are preferred over
open-ended when there's a reasonable enumeration.

Behavioral test: a SKILL.md that says *"Ask the user: (1) Title?
(2) Description? (3) Idea or refine now?"* in a single bulleted list
is **wrong**. The correct shape is *"Ask one question. After the user
answers, decide what (if anything) to ask next, up to the cap (if
any)."*

## 7. Cross-skill pointers — text only, never invocations

Skills do not invoke other skills. They point at them in prose. Two
formats:

- **`See also:` block** at the end of every SKILL.md. Soft pointer.
  Example: `**See also:** project-refine — when the user wants to
  scope this idea now.`
- **`REQUIRED SUB-SKILL:` inline** for the rare hard dependency.
  Format adopted from `superpowers/skills/writing-plans/SKILL.md:52`.
  We use it sparingly — most cross-references are soft.

Hand-offs to *other frameworks* (Superpowers, Claude Code, your
editor) follow the same rule: name the framework in prose, never tool-
invoke it.

## 8. Subagents — read-only, fed inline

Two skills (`project-refine`, `project-audit`) dispatch subagents:

- `agents/project-researcher.md` — research subagent for scoping.
- `agents/project-auditor.md` — per-check validation subagent for audit.

Both follow the shape of `superpowers/agents/code-reviewer.md`. Hard
rules:

1. **Subagents are read-only.** Their prompts contain no
   edit/write/commit language. The parent applies edits after the
   user approves.
2. **Inputs are pasted inline** in the subagent prompt — never
   "read PROJECTS.md and ...". This is adopted from
   `superpowers/skills/subagent-driven-development/SKILL.md:255`
   ("Make subagent read plan file" is listed as an anti-pattern).
3. **Parallelize the read, serialize the write.** `project-audit`
   dispatches one subagent per check in parallel; the parent then
   walks findings with the user *one at a time*.
4. **No subagents for trivial tasks.** `project-add` runs inline
   because three questions is faster than one Agent dispatch.

## 9. Heading depth

H2 for major sections, H3 only inside long sections (e.g. sub-modes
of `project-refine`). No H4. Matches superpowers cadence.

## 10. Length targets

| Skill | Target |
|---|---|
| `using-project-harness` | ~80 lines |
| `project-next` | ~120 lines |
| `project-add` | ~140 lines |
| `project-audit` | ~180 lines + `references/checks.md` |
| `project-refine` | ~220 lines + `.dot` decision graph |

Going over by 10–20% is fine; doubling the target means the skill is
trying to do too much and likely needs to push content into
`references/`.

## 11. Forbidden phrasings

In SKILL.md prose and in the parent's responses while running a
skill, do not use:

- *"should"* — replace with *"will"* or evidence ("the file shows X").
- *"probably"* / *"likely"* — replace with verification.
- *"looks fine"* / *"seems good"* — re-read the file or re-dispatch
  the auditor and report what you actually found.

Adopted from
`superpowers/skills/verification-before-completion/SKILL.md:52-75`.
The rule is: evidence before claims, always.

---

## Tips: best-practices applied

Surfaced from Anthropic's official skill-authoring best-practices
guide. These are the bits that aren't already encoded in the
conventions above; treat them as the *positive form* of the rules.

### Concise is key — Claude is already smart

> *"Only add context Claude doesn't already have. Challenge each
> piece of information: 'Does Claude really need this explanation?'
> 'Can I assume Claude knows this?' 'Does this paragraph justify
> its token cost?'"*
>
> — `agent-skills/best-practices.md`

Default assumption for project-harness prose: don't explain what a
git commit is, don't define "PROJECTS.md trunk" each time, don't
unpack what `[~]` means once it's been defined in the status
legend. Each token competes with conversation history once the
SKILL.md loads — be dense.

### Set appropriate degrees of freedom

Match specificity to the task's fragility. The skills in this
bundle land at different points on the freedom spectrum:

- **High freedom** — `project-refine` *refine-notes* sub-mode.
  Many valid approaches; heuristics guide. Body uses prose
  guidance, not numbered scripts.
- **Medium freedom** — `project-next`. A preferred pattern
  (composite menu) exists but the menu adapts to what's in the
  trunk. Body shows a template the skill customizes.
- **Low freedom** — `project-add`'s atomic commit, `project-
  audit`'s post-fix re-verification. Operations are fragile;
  consistency is critical. Body specifies exact sequences.

Don't pull Iron Laws onto high-freedom sub-modes; don't leave
low-freedom operations vague.

### Front-load the key use case

> *"The combined `description` and `when_to_use` text is truncated
> at 1,536 characters in the skill listing to reduce context
> usage."*
>
> — `code.claude.com/docs/en/skills.md`

Put the most distinguishing verb-phrase in the first ~200 chars
of `description`. The truncation happens late, but Claude reads
top-down — the first sentence does the heavy triggering work.

### References one level deep from SKILL.md

> *"Keep references one level deep from SKILL.md. All reference
> files should link directly from SKILL.md to ensure Claude reads
> complete files when needed."*
>
> — `agent-skills/best-practices.md`

Project-harness follows this: `skills/project-audit/references/
checks.md` is linked from `project-audit/SKILL.md` directly.
`_conventions.md` is linked from each SKILL.md directly. No
nested chains.

### Avoid offering too many options

> *"Don't present multiple approaches unless necessary. Provide a
> default with an escape hatch."*
>
> — `agent-skills/best-practices.md`

Project-harness applies this in two places: each skill's
*See also* block names a default sibling for each likely
hand-off, and `project-refine`'s sub-mode disambiguation asks
one focused question rather than presenting a menu of all
three sub-modes.

### Forward slashes always; no Windows paths

> *"Always use forward slashes in file paths, even on Windows."*
>
> — `agent-skills/best-practices.md`

All path references in this bundle use forward slashes
(`projects/P21-foo.md`, `templates/PROJECTS.md`). Verified.

### Avoid time-sensitive content

> *"Don't include information that will become outdated. Use 'old
> patterns' sections for historical context."*
>
> — `agent-skills/best-practices.md`

This bundle has no time-sensitive content. If a future
deprecation arises (e.g. swapping `git log` for a different
recency signal), use a fold-out *Old patterns* section rather
than dating the prose.

---

## References

The canonical authority for skill structure and authoring is
Anthropic's official documentation. The conventions above
implement this guidance for project-harness.

### Primary (Anthropic official)

- **Agent Skills overview** —
  `https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview.md`
  Skill structure, frontmatter rules (`name` ≤64 chars,
  `description` ≤1024 chars), three-level loading
  (metadata always loaded; SKILL.md on trigger; bundled
  files on demand).

- **Skill authoring best practices** —
  `https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices.md`
  Authoring patterns: third-person descriptions,
  progressive disclosure, anti-patterns, the
  evaluation-driven development loop.

- **Use Skills in Claude Code** —
  `https://code.claude.com/docs/en/skills.md`
  Claude Code-specific frontmatter (`when_to_use`,
  `argument-hint`, `arguments`, `disable-model-invocation`,
  `user-invocable`, `allowed-tools`, `model`, `effort`,
  `context: fork`, `agent`, `hooks`, `paths`, `shell`),
  string substitutions, the 1,536-char skill-listing
  truncation.

### Secondary (community examples)

- **superpowers** (Jesse Vincent) —
  `https://github.com/obra/superpowers`
  A 16-skill community plugin that demonstrates the
  Iron Law / Red Flags / Common Rationalizations
  patterns this conventions doc builds on. Specific
  skills cited inline above:
  `using-superpowers`, `brainstorming`,
  `writing-plans`, `test-driven-development`,
  `systematic-debugging`,
  `verification-before-completion`,
  `subagent-driven-development`,
  `dispatching-parallel-agents`,
  `requesting-code-review`,
  `agents/code-reviewer.md`.

When the official docs and superpowers diverge, **follow
the official docs**. Superpowers is one community example;
the docs are the spec.
