---
name: project-audit
description: Runs eleven drift checks (or a scoped subset) against PROJECTS.md and projects/ by dispatching one project-auditor subagent per check in parallel, then walks each finding interactively and asks before fixing. Defaults to focus mode — auditing only the candidate set most likely to hold drift (out-of-order, stragglers, recent active). Use --all for the full sweep. Each accepted fix is one revertable commit and is post-fix re-verified. Stateless — does not remember past skips.
when_to_use: When the user says "audit projects", "is everything in order?", "did I forget to flip anything?"; periodically (weekly, before merging a long-running branch).
arguments: [scope]
argument-hint: "[P##] [--all|--focus|--candidates] [--check]"
allowed-tools: Read Edit Write Bash Agent
---

# project-audit

**Core principle:** drift accumulates silently. The audit makes it
visible without ever fixing silently — every fix is one user
approval, because the audit cannot tell intentional drift from
forgotten drift.

## Iron Law

> **NO FIX WITHOUT POST-FIX RE-VERIFICATION.** When the user
> approves a fix, apply the edit, then re-run the relevant check
> (or re-read the file) to confirm the finding is gone. Reporting
> *"applied the fix"* without verification is a claim, not
> evidence.
>
> No exceptions: not "the edit is trivial", not "I just edited it
> myself, I know it's right", not "we're behind, batch the
> verification". Re-verify each fix individually.
>
> Violating the letter of this rule is violating the spirit of it.

## When to use

- *"Audit projects."* / *"Run audit."*
- *"Is everything in order?"* / *"Did I forget anything?"*
- *"Audit P21."* — single-project scope.
- *"Audit `--filenames`."* — single-check scope.
- Periodically — weekly, before merging a long-running branch, or
  before promoting a release.

## Scope arg

| Invocation | Behavior |
|---|---|
| `project-audit` (bare) | All 11 checks restricted to focus candidates (out-of-order, stragglers, recent active) — the default |
| `project-audit --focus` | Explicit alias for the bare default; identical behavior |
| `project-audit --all` | All 11 checks across all projects (previous default) |
| `project-audit P21` | All 11 checks restricted to project P21 (overrides focus selection) |
| `project-audit --<check-id>` | One check restricted to focus candidates |
| `project-audit --all --<check-id>` | One check across all projects |
| `project-audit P21 --<check-id>` | One check restricted to P21 |
| `project-audit --candidates` | Print candidate list and matched rules; no auditor dispatch |

`<check-id>` is one of the IDs in `references/checks.md` (e.g.
`--filenames` → `filename-matches-slug`, `--tdd` →
`tdd-ordering`). Unrecognized check IDs cause the skill to print
the list of valid IDs and exit without running anything.

`--focus` and `--all` are mutually exclusive — pass one or the
other. An explicit project ID (`P21`) overrides both: single-project
scope always wins. `--candidates` ignores any `--<check-id>` flag
because it does no dispatch.

If a flag is missing or the syntax is unclear, the skill asks one
clarifying question and otherwise defaults to the bare invocation.

## Focus mode (default)

Bare `project-audit` runs in **focus mode** — narrowing to the
projects most likely to hold drift instead of re-verifying every
closed project. `--focus` is an explicit alias of the default; use
`--all` for the previous full-sweep behavior.

A project is a focus candidate iff its trunk glyph is `[ ]` or
`[~]` AND it matches at least one of:

- **Out-of-order** — at least one *higher-numbered* project is
  already `[x]`. Strong signal of a forgotten trunk-glyph flip.
- **Straggler** — `[~]` with ≥1 unchecked task and ≤2 unchecked
  tasks. Either a missed flip or a real loose end.
- **Recent active** — the next 3 incomplete project numbers above
  the *high-water mark* of completion. The high-water mark `H` is
  the highest P-number among `[x]`, `[-]`, and `[>]` projects.
  Take all `[ ]`/`[~]` projects with P-number > `H` and pick the
  3 with the lowest P-number. If no `[x]`/`[-]`/`[>]` project
  exists, `H` is undefined and the rule selects the lowest 3
  incomplete projects overall (e.g. P1, P2, P3 on a fresh trunk).

`[x]`, `[-]`, `[>]`, and `[?]` projects are never candidates. See
`references/focus-rules.md` for the full definitions and worked
examples.

`--candidates` prints the candidate list with matched tags and
exits — useful for sanity-checking the rules without running
auditors. If the candidate set is empty, the skill prints
*"No focus candidates — trunk looks clean by the focus rules. Run
`project-audit --all` for a full audit."* and exits.

Findings are reported with the rule(s) that matched the candidate,
ordered `out-of-order` > `straggler` > `recent` (ties by ascending
P-number), so the most suspicious drift is walked first.

## What it does

1. **Read the trunk and compute scope.** Read `PROJECTS.md` and
   the `projects/` listing. Resolve the invocation to one of:
   focus (the default, also `--focus`), all (`--all`),
   single-project (`P<NN>`), or candidates-only (`--candidates`).
   For focus and candidates modes, compute the candidate set
   inline (see *Focus mode*). For `--candidates`, print the list
   and exit. For an empty focus candidate set, print the empty
   message and exit. Otherwise, read the relevant per-project
   files inline: for `--all` or single-project, all in-scope
   files; for check-scoped invocations, only files relevant to
   that check; for focus mode, only candidate files.
2. **Determine which checks are in scope.** Bare/`--focus`/`--all`
   = all 11. `--<check-id>` = one. Single-check invocations skip
   parallel dispatch (one check is faster inline).
3. **Dispatch one `project-auditor` subagent per check, in
   parallel** (for multi-check scopes only). Each subagent prompt
   contains:
   - The check definition copied verbatim from
     `references/checks.md`.
   - The scope (all / `P21` only / candidate set).
   - For focus mode, a `### Candidate set` block listing the
     candidate IDs and their matched tags so the auditor can
     correlate findings to the rule that surfaced the project.
   - All needed file contents, pasted inline. **Do not have the
     subagent read from disk** — that's the
     `subagent-driven-development:255` anti-pattern.
4. **Aggregate findings.** Each subagent returns either
   `CLEAN` or one or more findings in the structured format from
   `project-auditor.md`. Combine into a single ordered list.
5. **Report a one-line summary:** *"Found N drift findings across
   M projects. Walking through them now."* Or, if zero findings,
   *"All checks clean across <scope>."* and exit.
6. **Walk findings interactively, one at a time.** For each:
   ```
   Finding 3 of 7
     Check: filename-matches-slug
     Project: P21
     Detail: trunk title is "Configuration profiles" but file is
             projects/P21-config-prof.md
     Proposed fix: rename to projects/P21-configuration-profiles.md
             and update the trunk row's link.
   Fix this? [y/n/skip/explain]
   ```
   - `y` — apply the fix, then **re-verify** (Iron Law).
   - `n` / `skip` — leave as-is, move to the next finding.
   - `explain` — describe the check's rationale and the proposed
     fix in more detail, then re-ask `y/n/skip`.
7. **Apply fixes one at a time.** Use direct file edits +
   **one commit per finding**, even when the fix touches multiple
   files (e.g. `filename-matches-slug` renames the project file
   and updates the trunk row in the same commit). The commit
   message names the finding, e.g.
   `fix(projects): P21 filename-matches-slug — rename to
   P21-configuration-profiles.md`. This keeps every accepted fix
   discretely revertable and makes the audit trail readable.

   **`references-block` exception:** when the finding is a
   `references-block` violation (missing block, malformed
   bullets, broken paths, out-of-order labels), the proposed fix
   is **invoke the references-block helper** rather than a
   one-line edit. The helper (defined in
   `references/references-block.md`) searches plans, specs, and
   recent git activity, surfaces candidates, prompts the user,
   and writes the block. The user's `y` accepts running the
   helper; the helper's own one-question-at-a-time prompts then
   apply. The whole helper run is committed as one finding.
8. **Re-verify the specific check after each fix** (Iron Law).
   Re-run *only* the check that produced the finding — not all 11,
   not all in-scope checks. Confirm the finding is gone before
   moving on. Do NOT re-dispatch the other auditors mid-walk; their
   findings were valid against the inputs at audit time.
9. **Stale-finding handling.** A later finding may reference state
   that an earlier fix invalidated (e.g. finding #4 references the
   old filename that finding #3 renamed). When this happens, skip
   the stale finding (`skip` is a valid user response), and note
   *"check redundant after earlier fix"* in the final summary so
   the user knows it wasn't a real skip.
10. **Final summary:** *"Fixed 3 findings. 1 skipped (P15 trunk
    glyph — you said it was intentional). 1 redundant after
    earlier fix. 0 errors."*

## What it deliberately does not do

- Does not batch-apply fixes. Even when 5 findings have an
  identical proposed fix, ask each one. The user may have
  intentional reasons for some.
- Does not remember skips. If the user skipped a finding last
  week and the drift is still there, it shows up again. This is
  the **stateless principle** — encoded explicitly so that
  intentional drift surfaces every audit and can be reconfirmed.
- Does not run tests, write code, or invoke other frameworks. If
  a finding *implies* a code/test change ("this verification
  command might be stale — re-run it?"), name the command and let
  the user run it themselves.
- Does not widen the scope mid-run. If the user invoked
  `project-audit P21` and the audit notices drift in P22, the
  P22 finding does not appear in the report. The user can
  re-invoke the audit. Same applies to focus mode — drift in a
  non-candidate project is not flagged; that's what `--all` is
  for.
- Does not edit `references/checks.md`. The check definitions are
  versioned with the plugin.

## Red Flags

| Thought | Reality |
|---------|---------|
| "These look like noise, batch-fix them all" | One at a time. Audit can't tell intent from drift. |
| "I'll skip the post-fix re-verification, the edit was trivial" | Iron Law. Trivial edits are exactly where silent failures hide. |
| "User said `audit P21`, but I'll also flag drift in P22 since I noticed it" | No. Scope arg means scope. The user runs another invocation if they want more. |
| "The user already skipped this finding last time, I'll skip it automatically" | The skill is stateless on purpose. Re-surface; let the user reconfirm. |
| "I'll dispatch one auditor for all checks at once to save dispatches" | One subagent per *check*. Parallelism is the win, not consolidation. |
| "The auditor came back `CLEAN` — must be right, move on" | Auditors are read-only and inputs were inline. If a check is suspicious, re-read the input you sent and confirm. |
| "I'll commit the rename and the trunk update separately" | One commit per finding. Multi-file fixes are still one finding. Splitting breaks per-finding revert. |
| "Earlier fix changed state, I should re-dispatch all remaining auditors" | Don't. Only re-verify the *specific* check that was just fixed. Stale findings get `skip`'d with a note, not re-computed. |
| "Focus candidate set was empty, but I'll go ahead and audit everything anyway" | Don't widen scope. Empty means the focus rules see no drift candidates — print the empty message and exit. The user runs `--all` if they want a full sweep. |
| "I noticed drift in a non-candidate project during focus mode — I'll add it to the report" | Don't. Focus scope means focus scope. Tell the user the finding exists in your conversational summary if you must, but it does not appear as a numbered finding in the walk. |
| "References-block finding is just a missing block — I'll write `**References**` and one TODO bullet to make it pass" | No. The fix is the references-block helper — search plans/specs/git, surface candidates, ask the user. A TODO bullet is silent drift the user will never see again. |
| "Helper found no candidates and the user has nothing to add — I'll skip the empty-block confirmation" | No. The empty-block prompt is what makes the failing audit state visible and intentional. Skipping it produces an invalid block silently. |

## Common Rationalizations

| Excuse | Reality |
|--------|---------|
| "Re-verifying every fix is slow" | The cost of a stale fix is a follow-up audit. Re-verify is cheaper. |
| "This drift is obviously a typo, I don't need to ask" | Maybe. Ask anyway — typos and intentional shortenings look identical to the audit. |
| "I'll just fix all the filename mismatches" | A bulk filename rename is a different operation. If the user wants that, run the audit, then have them invoke a different operation. The audit doesn't bulk-fix. |
| "The auditor missed something I can see" | Trust but verify. If you can see it, the auditor was given inputs that obscured it — surface that to the user as its own finding. |

## Quick reference: the 11 checks

See `references/checks.md` for full definitions. IDs:

- `trunk-has-file`
- `file-has-trunk`
- `glyph-matches-state`
- `filename-matches-slug`
- `idea-trailing-hyphen`
- `idea-no-boilerplate`
- `references-block`
- `trunk-row-link-format`
- `tdd-ordering`
- `unique-task-ids`
- `cross-refs-resolve`

## See also

- `references/checks.md` — full definitions of all 11 checks.
- `references/focus-rules.md` — the 3 candidate-selection rules
  used by focus mode (the default).
- `references/references-block.md` — format spec and discovery
  helper used as the proposed fix for `references-block`
  findings; also invoked by `project-refine` at scope entry.
- `agents/project-auditor.md` — the read-only subagent prompt
  this skill dispatches.
- `_conventions.md` §8 — subagent rules (read-only, inputs inline,
  parallelize the read).
- `project-refine` — when a finding is best fixed by walking the
  user through scope/decompose flow rather than by a one-line
  edit.
