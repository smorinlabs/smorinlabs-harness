# project-audit checks (v1)

The 11 drift checks `project-audit` runs. Each check is independent
of the others — it can be dispatched to its own `project-auditor`
subagent in parallel. Each check has a stable identifier (used by
the `--<check>` scope arg), a one-line definition, and an example
finding so the auditor knows what drift looks like.

| ID | Check |
|---|---|
| `trunk-has-file` | Every trunk entry has a corresponding file in `projects/` |
| `file-has-trunk` | Every file in `projects/` is referenced by a trunk row |
| `glyph-matches-state` | Trunk glyph matches per-project rolled-up state |
| `filename-matches-slug` | Filename matches the title slug (kebab-case) |
| `idea-trailing-hyphen` | `[?]` projects have a trailing-hyphen filename; non-`[?]` projects do not |
| `idea-no-boilerplate` | `[?]` files contain no boilerplate sections (no `### Tests & Tasks`, etc.) |
| `references-block` | Scoped/active files have a `**References**` block at the top, with `**Trunk:**` as the mandatory first bullet |
| `trunk-row-link-format` | Trunk rows use the standard markdown-link format `- [glyph] **PID** — [Title](projects/PID-slug.md)` (not the legacy `→` arrow) |
| `tdd-ordering` | At least one `TS` task precedes the first `T` task (unless `**TDD: not applicable**` is in the body) |
| `unique-task-ids` | No duplicate task IDs within a single project |
| `cross-refs-resolve` | `**Depends on:**` and similar cross-references resolve to existing project IDs |

---

## `trunk-has-file`

**Definition:** For every project ID listed in the *Project index*
section of `PROJECTS.md`, there is a corresponding file under
`projects/` whose name starts with that ID.

**Drift example:**
- Trunk lists `[~] **P40** — [Foo](projects/P40-foo.md)`, but
  `projects/P40-foo.md` does not exist.

**Common cause:** A project file was deleted or renamed without
updating the trunk row.

---

## `file-has-trunk`

**Definition:** For every file in `projects/` whose name matches
`P<NN>-*.md` or `P<NN>-*-.md`, there is a corresponding row in the
trunk's *Project index* section that references it.

**Drift example:**
- `projects/P39-foo.md` exists but no trunk row references it.

**Common cause:** A file was added without updating the trunk.

---

## `glyph-matches-state`

**Definition:** The status glyph in the trunk row matches the
rolled-up state of the per-project file:

- `[x]` ⇔ all `T` and `TS` tasks are `[x]`.
- `[~]` ⇔ at least one task is `[x]` and at least one task is
  unchecked.
- `[ ]` ⇔ no tasks are `[x]`, file has full scope + at least one
  task.
- `[?]` ⇔ file has trailing-hyphen filename and no `### Tests &
  Tasks` section.
- `[-]` and `[>]` glyphs are not derived from the file's task state;
  this check skips them.

**Drift example:**
- All tasks in `projects/P21-foo.md` are `[x]`, but the trunk row
  still shows `[~]`.

**Common cause:** The user finished the last task without flipping
the trunk glyph (companion proposal §6.4).

---

## `filename-matches-slug`

**Definition:** The kebab-case slug in the filename (between `P<NN>-`
and `.md` / `-.md`) matches the kebab-cased title in the trunk row.

**Drift example:**
- Trunk says `**P21** — Configuration profiles` but the file is
  `projects/P21-config-prof.md`.

**Common cause:** The title was edited in the trunk but the file
wasn't renamed (companion proposal §6.2).

---

## `idea-trailing-hyphen`

**Definition:**
- A project with trunk glyph `[?]` MUST have a filename ending in
  `-.md` (trailing hyphen before the extension).
- A project with any other glyph (`[ ]`, `[~]`, `[x]`, `[-]`,
  `[>]`) MUST NOT have that trailing hyphen.

**Drift examples:**
- Trunk says `[?] **P33** — ...` but file is
  `projects/P33-foo.md` (missing trailing hyphen).
- Trunk says `[~] **P21** — ...` but file is
  `projects/P21-foo-.md` (trailing hyphen on a non-idea).

**Common cause:** Promotion (`[?]` → `[ ]`) didn't rename the file,
or a file was hand-renamed without flipping the glyph.

---

## `idea-no-boilerplate`

**Definition:** Files for `[?]` projects contain only the title,
a one-line description, and OPTIONALLY `### Open questions` and/or
`### Notes` sections (captured by `project-add` at idea-time to
preserve the volatile context around the idea). They do NOT
contain any of these scoped-state sections (matched as headers,
case-insensitive):

- `### Tests & Tasks`
- `### Scope`
- `### Out of scope`
- `### Verification`
- `**References**` (block, not just inline mention)

`### Open questions` and `### Notes` are explicitly allowed in
idea state — they are the canonical place for the user's day-1
thinking, and `project-refine`'s promotion flow seeds the scoped
state from them.

**Drift example:**
- `projects/P33-foo-.md` contains an empty `### Tests & Tasks`
  heading.
- `projects/P34-bar-.md` contains a `### Scope` section (scope
  belongs in promoted state, not idea state).

**Common cause:** The user pre-populated boilerplate "to be ready
for refinement". Idea state is meant to be minimal apart from the
explicitly-allowed `### Open questions` and `### Notes` sections;
promotion via `project-refine` is what adds the scoping sections.

---

## `references-block`

**Definition:** Files for projects with glyph `[ ]`, `[~]`, or
`[x]` MUST have a `**References**` block at the top of the body
(immediately after the H1 title). The block must:

1. Begin with a header line that is exactly `**References**`
   (bold only, no colon, no markdown heading prefix).
2. Be followed immediately by a markdown bulleted list. Each
   bullet matches `- **<Label>:** <body>` where `<Label>` is a
   non-empty bold-prefixed label and `<body>` is non-empty.
3. End at the first blank line followed by non-bullet content.
4. The **first bullet** must be the trunk back-pointer:
   `- **Trunk:** [PROJECTS.md](../PROJECTS.md)`. Subsequent
   bullets follow the canonical label sequence: `Trunk` → `Spec`
   → `Design` → `Plan` → `Depends on` → `Successor of` →
   `Tracking` → `Discussion` → `Prior art`. Unknown (free-form)
   labels go last in author order.
5. Resolve targets: filesystem-style references must point to a
   real path, URLs must be syntactically well-formed, ticket IDs
   must match a recognized regex (`[A-Z]+-\d+`, `#\d+`, etc.).
   The check does not fetch URLs.

Empty blocks (no bullets), out-of-order blocks, and blocks
missing the mandatory `Trunk` first bullet are all drift.

See `references-block.md` for the full format spec, recommended
labels, and the discovery helper invoked by both `project-audit`
and `project-refine`.

**Drift examples:**
- `projects/P21-foo.md` is `[~]` but has no `**References**`
  block.
- Block present but missing the mandatory `**Trunk:**` first
  bullet.
- Block present but empty (header, then a blank line, then body).
- Bullet missing the bold label: `- Spec: https://example.com/spec`.
- Bullet with a filesystem reference that doesn't resolve:
  `- **Plan:** ~/.claude/plans/missing.md` and the file isn't
  there.
- Bullet order is `Tracking → Spec → Plan` (Tracking should be
  after Spec/Design/Plan/Depends on/Successor of in the canonical
  sequence).

**Common cause:** Promotion forgot to add it, references were
deleted during refinement, a hand-edit broke the bullet syntax,
or a referenced plan/spec was moved without updating the link.

---

## `tdd-ordering`

**Definition:** Within a project's `### Tests & Tasks` section,
at least one `TS` task must appear before the first `T` task,
unless the file body contains the literal opt-out marker
`**TDD: not applicable**`.

**Drift example:**
- `projects/P22-foo.md` has `[ ] [P22-T01] ...` as the first
  entry under `### Tests & Tasks`, no `TS` precedes it, and no
  `**TDD: not applicable**` line exists.

**Common cause:** User added implementation tasks first and
forgot the TDD bias from companion proposal §9.

---

## `unique-task-ids`

**Definition:** Within a single project file, no two tasks share
the same `[P<NN>-T##]` or `[P<NN>-TS##]` identifier.

**Drift example:**
- `projects/P21-foo.md` has two lines starting `- [ ] [P21-T03]`.

**Common cause:** Copy-paste during decomposition.

---

## `cross-refs-resolve`

**Definition:** Every `**Depends on:**` line (or other explicit
cross-reference like `**Successor of:**`, `**Precedes:**`) names
project IDs that exist in the trunk index.

**Drift example:**
- `projects/P21b-foo.md` says `**Depends on:** P19` but P19 is not
  listed in the trunk.

**Common cause:** A referenced project was renumbered or dropped
after this file was written.

---

## `trunk-row-link-format`

**Definition:** Every project-index row in `PROJECTS.md` uses the
standard markdown-link format:

```
- [<glyph>] **P<NN>** — [<Title>](projects/P<NN>-<slug>.md)
```

The legacy `→ projects/...` arrow form is drift. The arrow is
not a markdown link and is invisible to external tools (markdown
linters, doc generators, AI agents reading the repo without
project-harness loaded). The new format makes the file pointer
explicit as a real markdown link, giving the project state a
self-describing schema.

**Drift example:**
- Trunk row reads `- [~] **P21** — Configuration profiles → projects/P21-configuration-profiles.md`
  (legacy arrow). Should be
  `- [~] **P21** — [Configuration profiles](projects/P21-configuration-profiles.md)`.

**Common cause:** The repo started before this format was
introduced and existing rows were never migrated. New rows
written by `project-add` and `project-refine` use the new format
automatically; legacy rows are flagged here and migrated per the
audit's one-finding-at-a-time walk (rename the row, commit,
re-verify).

**Migration:** Per finding, the proposed fix is a one-line edit
that converts the row in place. The check tolerates rows that
don't include any link target at all (the `trunk-has-file` check
covers that gap separately).
