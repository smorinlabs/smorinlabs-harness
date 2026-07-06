# References block — format spec and helper (v1)

The shared format and discovery procedure for the
`**References**` block at the top of every non-`[?]` per-project
file. Sourced by:

- `project-audit` — the `references-block` check verifies this
  format and the helper is the proposed fix when the check finds
  drift.
- `project-refine` — the helper runs at scope-mode entry (first
  step of promotion) and the format check runs in refine-notes
  mode (with `refresh references` as an opt-in re-search).

Same check, same strictness across both skills.

## Format spec

The block is the **first body section** after the H1 title of
every per-project file with glyph `[ ]`, `[~]`, or `[x]`. Files
with glyph `[?]` MUST NOT have a references block (per
`idea-no-boilerplate`).

### Shape

```markdown
# P21 — Configuration profiles

**References**
- **Trunk:** [PROJECTS.md](../PROJECTS.md)
- **Spec:** [Profiles spec](https://example.com/spec)
- **Plan:** ~/.claude/plans/configuration-profiles.md
- **Depends on:** P19
- **Tracking:** LIN-1234
- **Discussion:** https://github.com/foo/bar/issues/42

(rest of body…)
```

The first bullet is always the **trunk back-pointer**. Together
with the markdown link in the trunk row itself
(`- [~] **P21** — [Title](projects/P21-slug.md)`), this gives the
project state a self-describing bidirectional schema that
external tools — markdown linters, doc generators, AI agents
reading the repo without project-harness loaded — can parse
without prior knowledge of the conventions. The `Trunk` bullet is
required on every non-`[?]` project file; it is added at
promotion time (`[?]` → `[ ]`) and never removed.

### Hard rules

1. Header line is exactly `**References**` — bold only, no colon
   after, no markdown heading prefix.
2. Followed immediately by a markdown bulleted list (`- `
   bullets, no other content between header and first bullet).
3. Each bullet matches `- **<Label>:** <body>` where:
   - `<Label>` is a non-empty bold-prefixed label.
   - `<body>` is non-empty.
4. Block ends at the first blank line followed by non-bullet
   content.
5. Bullets are ordered by the canonical label sequence below.
   Unknown (free-form) labels appear after all canonical bullets,
   in author order. Out-of-order blocks are drift.
6. Empty blocks (no bullets) are drift. Promotion may produce one
   only after the explicit *"proceed with empty block?"*
   confirmation; the next audit run will flag it.

### Canonical label set

Order matters — bullets sort in this sequence. **`Trunk` is
mandatory and always first.** The remaining labels are optional
but, when present, must appear in this order.

| # | Label | Use |
|---|---|---|
| 1 | `Trunk` | Back-pointer to `PROJECTS.md`. Mandatory. Always written as `[PROJECTS.md](../PROJECTS.md)` (relative from `projects/`). |
| 2 | `Spec` | Product spec / PRD this project implements. |
| 3 | `Design` | Design doc / ADR. |
| 4 | `Plan` | Implementation plan, e.g. `~/.claude/plans/<file>.md`. |
| 5 | `Depends on` | Sibling project ID (e.g., `P19`). |
| 6 | `Successor of` | Project this one replaces. |
| 7 | `Tracking` | Ticket ID (e.g., `LIN-1234`, `JIRA-42`). |
| 8 | `Discussion` | Issue / PR / Slack thread URL. |
| 9 | `Prior art` | Related research / external reference. |

Unknown labels are accepted but the helper offers the closest
canonical match. Multiple bullets can share a label (two `Spec`
references are fine; both go in the `Spec` slot, in author order).
A missing `Trunk` bullet on a non-`[?]` project file is drift; the
audit's `references-block` check flags it and the helper writes
the canonical `[PROJECTS.md](../PROJECTS.md)` form as the proposed
fix.

### Resolution rules

- **Filesystem-style** (`~/.claude/...`, `projects/P##-*.md`,
  `docs/...`, `<repo-relative>/...`) — path must resolve to a
  real file. Drift if missing.
- **URL** (`http://...`, `https://...`) — must be syntactically
  well-formed. The skill does NOT fetch the URL.
- **Ticket ID** — must match a recognized regex
  (`[A-Z]+-\d+`, `#\d+`, etc.). Content is not validated.
- **Sibling project** (`P##`) — must exist in the trunk.
  (`cross-refs-resolve` covers the `**Depends on:**` cross-ref
  separately; the references-block check verifies syntactic
  shape.)

## Discovery — what the helper searches

Called by both `project-refine` (at scope entry, first step of
promotion) and `project-audit` (as the proposed fix for a
`references-block` finding).

### Filesystem-resolvable candidates

| Path | Type |
|---|---|
| `~/.claude/plans/*.md` | `Plan` |
| `<repo>/docs/superpowers/plans/**/*.md` | `Plan` (superpowers convention) |
| `<repo>/docs/superpowers/specs/**/*.md` | `Spec` (superpowers convention) |
| `<repo>/docs/**/*.md` | `Spec` / `Design` |
| `<repo>/specs/**/*.md` | `Spec` |
| `<repo>/archive/research/**/*.md` | `Prior art` |
| `<repo>/projects/P*.md` | `Depends on` / `Successor of` |

The `docs/superpowers/plans/` and `docs/superpowers/specs/` paths
are *opportunistic* — they exist in some repos and not others.
The helper must tolerate their absence silently. A missing
directory is not an error and produces zero candidates from that
source.

**Heuristic:** title-substring or kebab-slug overlap with the
project title. Top 5 matches per category, ranked by recency
(mtime).

**Deduplication:** when the same basename appears in multiple
paths (e.g., `~/.claude/plans/foo.md` and
`docs/superpowers/plans/foo.md`), surface only the in-repo copy
and note the home copy exists.

### Opaque-identifier candidates (URLs, ticket IDs)

| Source | Type |
|---|---|
| `git log --since=30d --pretty=%s%n%b` | URLs and ticket IDs in commit messages |
| `git for-each-ref refs/heads --format='%(refname:short)'` | Ticket IDs in branch names |

The helper greps for URL patterns and common ticket-ID regexes
(`[A-Z]+-\d+`, `#\d+`, `https?://...`). Output is deduplicated
and ranked, with recent commits weighted higher. The helper does
NOT call out to Linear, Jira, GitHub, or any external service —
the plugin is zero-runtime-dependency by design.

### What the helper does not do

- Does not fetch URLs to verify they 200.
- Does not infer labels — the user picks the label for each
  accepted candidate.
- Does not auto-add references without confirmation. Every
  addition is one user prompt.
- Does not create reference files. It only links to existing
  artifacts.

## The interaction

When the helper runs and the block is missing, malformed, or
out-of-order:

```
References block check
  Project: P21
  Status: missing — non-`[?]` projects must have a **References**
          block at the top.

I searched for candidates:

  Plans (~/.claude/plans/, docs/superpowers/plans/):
    1. ~/.claude/plans/configuration-profiles.md     (today, 2KB)
    2. docs/superpowers/plans/profiles-rollout.md    (yesterday)
    3. ~/.claude/plans/profiles-decision.md          (3 days ago)

  Specs / Design (docs/superpowers/specs/, docs/, specs/, archive/research/):
    4. docs/superpowers/specs/profiles-spec.md       (this week)
    5. docs/profiles-spec.md                         (1 week ago)

  Recent git activity (last 30 days):
    6. URL:    https://github.com/foo/bar/issues/42  (commit a1b2c3d)
    7. Ticket: LIN-1234                              (branch lin-1234-profiles)

  Sibling projects (projects/):
    8. P19 — Auth foundation  (Depends on candidate)

Pick references to include [comma-separated, e.g. "1,4,6,8"], or
"none" to leave empty, or "skip" to defer to the user:
```

For each picked candidate, the helper asks one follow-up:

> *"Label? [Spec/Design/Plan/Depends on/Successor of/Tracking/
> Discussion/Prior art/Other]"*

It defaults to the inferred label (e.g., a `~/.claude/plans/...`
candidate defaults to `Plan`).

After the picklist, the helper prompts for anything not surfaced:

```
Anything else to add? Paste each as `<label>: <body>` per line, or
press enter to finish.
> Spec: https://example.com/another-spec
>
```

The helper writes the block with bullets in canonical order, then
re-reads the file to verify the format check passes. Iron Law:
applied is not done; re-verified is done.

## Empty-block promotion

When the user is promoting `[?]` → `[ ]` and has nothing to add
(no candidates, no pasted references), the helper warns:

```
This project will fail audit (`references-block`) until at least
one reference is added. Proceed with empty block? [y/n]
```

- `n` — promotion aborts. Project stays `[?]`.
- `y` — promotion completes with an empty block. The next
  `project-audit` run flags the project. This is by design: the
  failing-audit state is the visible record that references owe.

## Refinement-loop behavior

In `project-refine` sub-mode 1 (refine-notes), the helper does
not re-search the filesystem on every iteration. It only
re-verifies the existing block against the format spec
(presence + bullet shape + canonical order + resolution of
filesystem-style references). Cheap and predictable.

The user triggers a fresh search by typing `refresh references`
during the loop. This re-runs the full discovery and surfaces
any new plans, specs, or git-derived candidates that have
appeared since refine entry.

## See also

- `references/checks.md` — the `references-block` check
  definition that verifies this spec.
- `skills/project-refine/SKILL.md` — sub-modes 1 and 2 invoke
  this helper.
- `skills/project-audit/SKILL.md` — the `references-block`
  finding's proposed fix invokes this helper.
- `_conventions.md` §6 — one-question-at-a-time convention the
  helper follows during prompting.
