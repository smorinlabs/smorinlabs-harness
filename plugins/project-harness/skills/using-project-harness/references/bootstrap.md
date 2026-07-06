# Bootstrap procedure (v1)

`using-project-harness` runs a four-step bootstrap sequence on
invocation. Each step is **idempotent** — it reads the per-repo
config file `.project-harness/project-harness.config.json` (created
on first run) and skips itself if the corresponding marker is set.
Steps run in order; later steps may use answers from earlier ones.

## Why the bootstrap exists

A new user adopting project-harness will not know the conventions
on day one. Without a guided first run, three things go wrong:

1. **PROJECTS.md never gets created** — every workflow skill needs
   it; fresh repos sit unable to use the plugin.
2. **AGENTS.md / CLAUDE.md never mention the plugin** — future
   sessions in the same repo (without this skill in context) won't
   know to route project edits through the workflow skills.
3. **References / plans / specs drift away from project files** —
   users keep their plan docs in `~/.claude/plans/` or
   `docs/superpowers/plans/`, but never link them from the
   per-project `**References**` block, so context gets lost.

The bootstrap addresses each in turn — once per repo, with the
user's confirmation, then never again.

## Config file: `.project-harness/project-harness.config.json`

Per-repo config, in version control. Travels with the repo so team
members share state.

```json
{
  "version": 1,
  "init_done": false,
  "projects_md_done": false,
  "agents_md_done": false,
  "claude_md_done": false,
  "planning_system": null,
  "planning_paths": {
    "plans": [],
    "specs": []
  },
  "references_block_nudged": false
}
```

The skill writes the file on first run with `init_done: false` and
all step markers `false`. Each completed step flips its marker to
`true`. When all four step markers are `true`, the skill flips
`init_done: true` and the bootstrap is silent on future
invocations.

If the config file does not exist, the skill creates it (with all
markers `false`) before running step 1. If the file exists but
some step markers are `false`, the skill runs only those steps.

## Step 1: PROJECTS.md scaffold

Skipped when `projects_md_done: true`.

1. Check if `PROJECTS.md` exists at the repo root.
2. If yes, set `projects_md_done: true` and continue. (Pre-existing
   trunk; nothing to do.)
3. If no, ask:
   *"No `PROJECTS.md` yet. The plugin ships a starter trunk at
   `templates/PROJECTS.md`. Copy it to the repo root? [y/n]"*
4. On `y`: copy the template to `./PROJECTS.md`, create empty
   `projects/`, `git add` both, commit
   `chore(projects): scaffold PROJECTS.md trunk and projects/ dir`,
   set `projects_md_done: true`.
5. On `n`: warn that the workflow skills will not function without
   a trunk, leave `projects_md_done: false`, and stop the
   bootstrap. (Re-running the skill later will resume here.)

## Step 2: AGENTS.md / CLAUDE.md mentions

Skipped when `agents_md_done: true` AND `claude_md_done: true`.

For each of `AGENTS.md` and `CLAUDE.md` independently:

1. **Stale rule:** the file is "stale" iff it does not exist OR its
   contents do not contain the literal string `project-harness`.
2. If not stale, set the corresponding `*_md_done: true` and
   continue.
3. If stale, ask:
   *"Your `<file>` doesn't reference project-harness. May I append
   a short pointer block so future Claude sessions know to route
   project edits through the workflow skills? [y/n]"*
4. On `y`: append the **standard block** below and set
   `*_md_done: true`. If the file does not exist, create it with
   only this block.
5. On `n`: set `*_md_done: true` anyway (the user has opted out;
   don't re-ask).

### Standard block (template)

The append text lives in `templates/project-harness-pointer.md`
at the plugin root. Identical content goes into `AGENTS.md` and
`CLAUDE.md` — the helper reads the template once and writes it
to each target file with a leading blank line so it appends
cleanly to existing content.

The template is small, standard, and version-stable. Future
template updates can be detected by running the bootstrap again —
the literal-string staleness rule will not catch *content* drift,
only absence; that is intentional. Template updates are a
separate operation, not the init's job. (Users who want to
re-sync the block content can delete it from their AGENTS.md /
CLAUDE.md and re-run the bootstrap.)

## Step 3: Planning system

Skipped when `planning_system` is non-null.

1. Ask:
   *"Are you using a planning / spec system alongside
   project-harness? Pick one: superpowers / other / none."*
2. Branch on the answer:
   - **superpowers** — set `planning_system: "superpowers"` and
     `planning_paths.plans: ["~/.claude/plans/", "docs/superpowers/plans/"]`,
     `planning_paths.specs: ["docs/superpowers/specs/"]`. Tell the
     user the references-block helper will search those paths
     when run.
   - **other** — ask one follow-up:
     *"Where do plan and spec docs live? Paste paths
     (comma-separated, repo-relative or `~`-relative)."*
     Store the answer; e.g.,
     `planning_paths.plans: ["docs/specs/plans/"]`,
     `planning_paths.specs: ["docs/specs/"]`.
   - **none** — set `planning_system: "none"`. Suggest
     `~/.claude/plans/` and `docs/specs/` as starter conventions
     and offer to create those directories. Set
     `planning_paths.plans: ["~/.claude/plans/"]`,
     `planning_paths.specs: ["docs/specs/"]` regardless of whether
     the user creates the dirs.
3. Mark the step done by setting `planning_system` to a non-null
   value. The references-block helper reads
   `planning_paths.plans` and `planning_paths.specs` from this
   config when it runs, in addition to its built-in fallback paths.

## Step 4: References-block convention nudge

Skipped when `references_block_nudged: true`.

1. Tell the user, in 3–5 lines:
   *"Every non-`[?]` project file should have a `**References**`
   block at the top linking its spec / plan / design / tracking
   ticket. Bullets are `- **<Label>:** <body>` in canonical order
   (Trunk → Spec → Design → Plan → Depends on → Successor of →
   Tracking → Discussion → Prior art, with `Trunk` mandatory and
   first). The full format and the search
   helper are in
   `skills/project-audit/references/references-block.md`. Run
   `project-audit --all --references-block` later to scan
   existing projects."*
2. Set `references_block_nudged: true`.
3. Do **not** offer to backfill existing projects — that's
   `project-audit`'s job. The init's role is to point at the
   convention.

## Finishing

When all four steps are complete (all markers `true`), set
`init_done: true`. Future invocations of `using-project-harness`
read the config first and skip the bootstrap entirely if
`init_done: true`.

If the user adds new repos, deletes their AGENTS.md, or otherwise
breaks the markers, individual steps will re-fire. The skill
re-runs only what's needed; a fully-bootstrapped repo costs one
file read.

## Re-init

If the user wants to re-run the full bootstrap (e.g., they
switched planning systems), they delete
`.project-harness/project-harness.config.json` (or set
`init_done: false` and the relevant step markers to `false`).
The skill does not provide a `--reset` flag; manual edit is the
escape hatch. The config file is small and human-readable on
purpose.

## Scope of writes

The bootstrap writes:

- `PROJECTS.md` (step 1, on `y`).
- `projects/` directory (step 1, on `y`).
- `AGENTS.md` and/or `CLAUDE.md` (step 2, on `y` for each).
- `.project-harness/project-harness.config.json` (every step that
  changes state).
- `docs/specs/` and/or `~/.claude/plans/` (step 3, on `y` if the
  user picked **none** and accepted the offer).

It does NOT write to `projects/P*.md`, `skills/`, or any other
file. References-block backfilling for existing projects is out
of scope — that's the audit's job.
