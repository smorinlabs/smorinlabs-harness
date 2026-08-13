# <Topic> Merge Plan

**Date:** YYYY-MM-DD
**Sources:** N markdown files in `<source-dir>/`
**Outputs:** M consolidated docs in `<consolidated-dir>/`
**Archive:** `<archive-dir>/` (after merge, byte-identical-verified)
**Execution:** <single agent | subagent-driven (one task at a time) | subagent-driven (parallel where safe)>

---

## Source files (with pre-merge SHA-256s)

Captured in `<consolidated-dir>/.source-sha256-pre-merge.txt` by Phase 1.

- `<source-1.md>` — <NN lines>
- `<source-2.md>` — <NN lines>
- ...

## Output structure

- `<output-1.md>` — <one-line purpose>
- `<output-2.md>` — <one-line purpose>
- `decisions-and-conflicts.md` — topic-to-source map + CFL log + intentionally-omitted log
- `validate.sh` — round-trip enforcement (markers ↔ log entries)

## Tasks

### Task 1: Pre-flight + skeletons
- [ ] Capture SHA-256 baseline for all sources
- [ ] Create `<consolidated-dir>/`
- [ ] Write skeleton for each output doc (sections only, empty bodies)
- [ ] Commit

### Task 2: Topic-to-source map
- [ ] Extract every `#`/`##`/`###` heading from every source file with line ranges
- [ ] For each output section, list contributing source(s) and line ranges
- [ ] Save as the first section of `decisions-and-conflicts.md`
- [ ] Commit

### Task 3: Validation script
- [ ] Copy `scripts/validate_round_trip.sh` (from skill) into `<consolidated-dir>/validate.sh`, parameterized for these docs
- [ ] Run it (expect PASS with 0 markers / 0 entries)
- [ ] Commit

### Task 4..(3+M): Merge each output doc
For each output doc:
- [ ] Fill skeleton from source ranges per Task 2 map
- [ ] Log every non-trivial synthesis/conflict/judgment as a CFL entry (use `assets/cfl_entry_template.md`)
- [ ] Place inline `<!-- CONFLICT: CFL-XXX -->` markers at end of synthesized blocks
- [ ] Spec-compliance review (or self-review): every CFL marker has a log entry; nothing in the map is silently dropped
- [ ] Code-quality review (or self-review): cross-references resolve, code samples compile, version pins consistent, no duplication across sections
- [ ] Run validation script (expect PASS)
- [ ] Commit

### Task (4+M): Coverage audit
- [ ] Run `scripts/coverage_audit.sh` to dump every source heading
- [ ] For each heading not in the topic-to-source map, add an entry to "Intentionally omitted source sections" with a one-sentence reason
- [ ] Run validation script (expect PASS)
- [ ] Commit

### Task (5+M): Archive originals
- [ ] Create `<archive-dir>/`
- [ ] Check basenames for collisions before moving anything — any output means stop:
      `for f in <source-files...>; do basename "$f"; done | sort | uniq -d`
- [ ] `git mv` (or `mv` if not a git repo) each source file to archive
- [ ] Verify byte-identical against the Phase 1 baseline (expect zero diff):

      shasum -a 256 <archive-dir>/*.md | sort | sed "s| <archive-dir>/| <source-dir>/|" > /tmp/post-archive-sums.txt
      diff <consolidated-dir>/.source-sha256-pre-merge.txt /tmp/post-archive-sums.txt

- [ ] Run validation script one final time (expect PASS)
- [ ] Commit
