---
name: document-merge
description: >-
  Merge multiple overlapping markdown documents into one or more consolidated outputs without
  losing information. Use whenever the user wants to consolidate, deduplicate, reconcile, or merge
  two or more research notes, specs, drafts, README variants, design docs, or reference material —
  even when they don't say the word "merge" (phrases like "combine these into one", "make a single
  source of truth", "I have these overlapping docs", or "dedupe this material" should all trigger
  this skill). Produces a verifiable merge: every synthesis decision is logged with a stable ID,
  every source line range is mapped to an output section, originals are archived byte-identical,
  and a validation script enforces the round-trip between markers and the decision log.
---

# Document Merge

Merge N markdown documents into M consolidated outputs (M ≤ N) with **zero information loss** and full traceability. Every judgment call is logged. Every source heading is accounted for. Originals are preserved byte-identical in an archive.

## When this skill applies

Trigger phrases include "merge these docs", "consolidate this research", "combine into one document", "dedupe these notes", "reconcile overlapping specs", "build a single source of truth", or anything where the user has multiple markdown files with overlapping content and wants a clean, comprehensive output.

If the user only has 2 documents *and* they're short *and* there's no real conflict to track, the full workflow is overkill. Ask whether they want the lite path (just merge + diff report) or the full path. For 3+ sources, default to full.

## Core principles

1. **Details are sacred.** The user's complaint with their inputs is duplication, not "too much info." When in doubt, keep the longer/more specific version and log the choice.
2. **Every judgment is logged.** A future reader (often the user themselves) must be able to audit every non-trivial synthesis. Stable `CFL-XXX` IDs round-trip between the merged docs and a separate decisions log.
3. **Originals are inviolable.** Source files are SHA-256-snapshotted before merging and archived byte-identical after. The merge can be re-verified at any time.
4. **Every source heading is accounted for.** Either it's mapped to an output section, or it's logged as intentionally omitted with a reason. No silent drops.

## Tiered workflow

Pick the tier based on input size. When in doubt, ask the user.

| Tier | Trigger | Artifacts produced |
|------|---------|-------------------|
| **Lite** | 2 sources, low-conflict | Consolidated doc + a short diff report (what was deduped, what was kept). No CFL log, no validation script. |
| **Full** | ≥3 sources, OR overlapping/conflicting content, OR user wants traceability | Plan doc, topic-to-source map, consolidated doc(s), `decisions-and-conflicts.md`, validation script, coverage audit, archived originals |

The rest of this skill describes the **full** workflow. For lite, see `references/lite_workflow.md`.

## Inputs to gather before starting

Ask the user (in one message, multiple-choice where possible):

1. **Sources** — paths to the markdown files to merge.
2. **Output location** — directory for consolidated docs (default: `<sources-parent>/consolidated/`).
3. **Number of output docs** — 1, or N split by topic (suggest a split if sources clearly cluster).
4. **Archive location** — where to move originals after the merge (default: `<sources-parent>/archive/`).
5. **Git repo?** — is the source dir tracked in git? If yes, use `git mv` to preserve rename history. If no, use `mv` and rely on the SHA-256 manifest for verification.
6. **Execution mode** — single agent, or subagent-driven (recommended for ≥3 sources or large inputs; defer to `superpowers:subagent-driven-development`).

## The full workflow (8 phases)

The structure below mirrors what produced reliable merges in practice. Each phase ends in a verifiable artifact. **For ≥3 sources, write a plan doc first** (use `assets/plan_template.md`) so the phases are tracked and dispatchable to subagents.

### Phase 1: Pre-flight snapshot

Capture the byte-identical baseline of every source. Without this, you cannot prove later that originals were not modified.

```bash
bash <skill-path>/scripts/capture_source_sha256.sh <output-dir> <source-files...>
```

This writes `<output-dir>/.source-sha256-pre-merge.txt`. **Phase 8 will diff against this.** If the diff fails at the end, the merge corrupted a source file — investigate before archiving.

### Phase 2: Build the topic-to-source map

Extract every `#`, `##`, `###` heading from every source file with its line range. For each output section, list the source file(s) and line ranges that contribute to it.

This produces a table like:

```markdown
| Output section | Source file(s) | Source line range |
|----------------|----------------|-------------------|
| § 1.1 Topic A  | source-a.md    | 12–47             |
| § 2.3 Topic B  | source-a.md, source-b.md | 89–134 (a), 12–55 (b) |
```

The map is the contract: every source heading must appear somewhere (here, or in the "intentionally omitted" log in Phase 7). Save it as the first section of `decisions-and-conflicts.md`.

Use this command to extract headings:

```bash
for f in <source-files>; do
  echo "=== $f ==="
  grep -nE "^#{1,3} " "$f"
done > /tmp/source-headings.txt
```

### Phase 3: Create skeleton output docs

Write the section structure of each output doc *before* filling content. This forces architectural decisions early. Each output doc gets:
- A 1-paragraph purpose statement at top
- The full section/subsection outline (headings only, with brief one-line intent)
- Empty bodies

Reviewing the skeletons with the user before filling them avoids expensive backtracking.

### Phase 4: Write the validation script

Place `scripts/validate_round_trip.sh` (provided) in the consolidated dir. It enforces that every `<!-- CONFLICT: CFL-XXX -->` marker in the merged docs has a matching `### [ ] CFL-XXX` or `### [x] CFL-XXX` entry in the decisions log, and vice versa. **One exception:** an entry retired under the ID-hygiene rule — its body carrying a `**Status:** Withdrawn` line — is expected to have no inline marker, so it is excluded from the comparison and reported as excluded. A withdrawn entry whose marker is still in a doc remains a failure.

Run it after every merge phase. If it fails, fix before continuing.

### Phase 5: Merge content (one output doc at a time)

For each output doc, fill the skeleton from the source ranges identified in Phase 2.

**The merge rules:**

- **Identical text** → keep verbatim, no log entry needed.
- **Same fact, different wording** → choose the clearer version; log a CFL entry if the choice is non-obvious.
- **Different facts on the same topic** → keep both, attribute, log a CFL entry.
- **Conflict (sources disagree)** → log a CFL entry with both excerpts, pick one as the canonical version, leave a `Resolution notes` field empty for the user to confirm later.
- **Same content in 2+ places after merge** → cross-reference, don't duplicate. Pick one canonical home.

**For every CFL-worthy decision:**

1. Append a new entry to `decisions-and-conflicts.md` using `assets/cfl_entry_template.md` (Where / Type / Sources / What I did / Excerpts / Synthesized / Resolution notes).
2. Place an inline marker `<!-- CONFLICT: CFL-XXX -->` at the **end** of the synthesized block in the merged doc (not the start — readers see the content first, then the audit pointer).
3. CFL IDs are monotonic, gap-free, three-digit zero-padded (`CFL-001`, `CFL-002`, ...). Once assigned, they never change.

See `references/cfl_classification.md` for when something is CFL-worthy vs. just merged silently. The standing rule: **every non-trivial synthesis, conflict, or judgment call.**

After completing each output doc, run the validation script. Run a code/spec review pass (or dispatch a reviewer subagent) before moving to the next doc.

### Phase 6: Cross-references between output docs

If you split into ≥2 output docs, content will inevitably reference content in another doc. Use GitHub-flavored anchor links (lowercase, spaces→hyphens, a spaced em-dash yields a *double* hyphen — see `references/anchor_rules.md`). Verify every cross-reference resolves.

### Phase 7: Coverage audit

Prove that every source heading is accounted for. Run:

```bash
bash <skill-path>/scripts/coverage_audit.sh <consolidated-dir> <source-files...>
```

For any source heading not in the topic-to-source map, add an entry to the **"Intentionally omitted source sections"** section of `decisions-and-conflicts.md`. Format:

```markdown
- `<source-file>` § "<heading>" (lines X–Y): <one-sentence reason — usually "fully duplicated by output § Z" with the doc/section that subsumes it>.
```

Conclusion sections, repeated rationale paragraphs, and content fully captured elsewhere are common omissions. **No silent drops** — if it's not in the topic map, it must be in the omitted log.

### Phase 8: Archive and verify

1. Create the archive directory (default `<sources-parent>/archive/`).
2. **Check for basename collisions before moving anything.** Sources drawn
   from different directories can share a filename — `README.md`, `notes.md`
   and `index.md` are the common ones in a merge — and the archive is flat, so
   the second move would overwrite the first. Stop and report the colliding
   pair instead; do not rename to disambiguate, because the Phase 1 baseline
   records each file under its original path and a renamed file can never
   match it in step 3.

   ```bash
   # (a) two sources sharing a basename
   for f in <source-files...>; do basename "$f"; done | sort | uniq -d

   # (b) a destination that already exists — e.g. from an earlier run
   for f in <source-files...>; do
     [ -e "<archive-dir>/$(basename "$f")" ] && echo "occupied: $(basename "$f")"
   done
   ```

   Any output from either check is a collision. **Both matter:** (a) catches
   two sources colliding with each other, (b) catches a source colliding with
   a file already in the archive, which (a) cannot see.

   Resolve a collision by renaming or relocating the *source* before Phase 1,
   or by archiving the colliding sources in a separate run with its own
   baseline. Do **not** archive them into subdirectories under
   `<archive-dir>/`: the step-4 verification globs the archive's top level
   only and rewrites a single flat path prefix, so a nested file would not be
   hashed and the guarantee would silently cover less than it claims.
3. Move each source file: `git mv` if in a git repo, plain `mv` otherwise.
   `git mv` already refuses to clobber (`fatal: destination exists`), so this
   only bites outside a repo, where the loss is unrecoverable. Note that
   `mv -n` is **not** a substitute for the check above: it declines silently
   and still exits 0, leaving the source in place with nothing reported.
4. Verify byte-identical against the Phase 1 baseline:

```bash
shasum -a 256 <archive-dir>/*.md | sort | sed "s| <archive-dir>/| <source-dir>/|" > /tmp/post-archive-sums.txt
diff <consolidated-dir>/.source-sha256-pre-merge.txt /tmp/post-archive-sums.txt
```

Expect zero diff. **If the diff is non-empty, stop** — the merge modified a source file, which violates the inviolable-originals guarantee. Investigate and revert before proceeding.

5. Run the validation script one final time (`PASS` expected).
6. Commit the archive move with a message documenting the SHA-256 verification.

## Bundled resources

- `scripts/capture_source_sha256.sh` — Phase 1 snapshot (cross-platform: detects `shasum`/`sha256sum`).
- `scripts/validate_round_trip.sh` — Phase 4 marker↔log enforcement (parameterized).
- `scripts/coverage_audit.sh` — source-heading dump for the Phase 7 manual coverage diff. It lists headings and reminds you what to check; it does not read the topic map, and comparing them is your job.
- `assets/cfl_entry_template.md` — The 6-field CFL entry structure.
- `assets/plan_template.md` — Plan doc template for the 8 phases.
- `references/cfl_classification.md` — Decision tree for "is this CFL-worthy?"
- `references/lite_workflow.md` — 2-source, low-conflict path.
- `references/anchor_rules.md` — GitHub markdown auto-anchor mechanics for Phase 6.

## When to dispatch subagents

For ≥3 sources or sources >500 lines each, recommend `superpowers:subagent-driven-development`. The natural task split is:
- T1: Phase 1 + Phase 3 (snapshot + skeletons)
- T2: Phase 2 (topic-to-source map)
- T3: Phase 4 (validation script)
- T4..T(N+3): Phase 5 (one output doc per task)
- T(N+4): Phase 7 (coverage audit)
- T(N+5): Phase 8 (archive)

Each task gets implementer + spec reviewer + quality reviewer. The plan template in `assets/plan_template.md` is structured for this dispatch.

## Common failure modes

- **Marker at start of block instead of end.** Readers should see content, then the audit pointer. Reviewers will catch this — fix immediately.
- **CFL ID reuse or gaps.** IDs are write-once. If you delete an entry, leave the ID retired with a note; do not renumber.
- **Skipping Phase 1.** Without the SHA-256 baseline, the "originals are inviolable" guarantee is unverifiable. Always snapshot first.
- **Merging silently when sources conflict.** Every disagreement logged is a future bug avoided.
- **Forgetting Phase 7.** It's tempting to declare done after the merge. The audit is what proves no source content was silently dropped.
- **Cross-reference rot.** Phase 6 anchors break when section titles change. Verify after every section rename.
