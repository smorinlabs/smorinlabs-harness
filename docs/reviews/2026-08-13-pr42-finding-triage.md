# Triage record — the 21 inherited review findings from PR #42 — 2026-08-13

**Purpose.** Phase 1 of the triage-first plan: assign a verdict to each of the 21
CodeRabbit/Copilot findings inherited from PR #42, with the evidence that settles
it. **No code was changed in this pass.** Phase 2 (fixing what survived) is a
separate set of PRs.

**Method.** Every verdict was reached by reproducing or refuting the claim against
the code, preferring execution over reading. Where a claim was settled by running
something, the command and its output are recorded below.

## Verdict key

| Verdict | Meaning |
|---|---|
| **REAL** | Reproduced, or the code path is provably wrong |
| **REAL-BUT-DESIGN** | Genuine gap needing an owner decision, not a patch |
| **STYLE** | Preference or convention, no defect |
| **WRONG** | Claim is false, or contradicts a settled project decision |

## Tally

| Verdict | Count | Findings |
|---|---|---|
| REAL | 12 | A2, A3, B1, B2, B4, B5, B7, B9, C2, C3, C4, C5 |
| REAL-BUT-DESIGN | 3 | B3, B8, C6 |
| WRONG | 4 | A1, C1, C7, D2 |
| Mixed (one half wrong, one half real) | 1 | B6 |
| Already fixed in PR #43 | 1 | D1 |

**Nine of 21 findings did not survive triage as stated** (4 wrong, 3 needing a
decision rather than a patch, 1 half-wrong, 1 already fixed). Two of the four
refutations were load-bearing: A1 was the batch's nominated "highest-value" item,
and C7 would have rewritten all 30 pages under `docs/skills/`.

---

## Cluster A — executable code

### A1 · `transcript_digest.py:137` — **WRONG**

**Claim.** `day_segments()` silently drops turns whose timestamp fails
`datetime.fromisoformat()`; RFC3339 `Z` timestamps are rejected by some Python
versions, making `--days` silently empty or wrong.

**Evidence.** The `Z`-rejection mechanism does not exist on this project's
supported interpreters:

```
$ grep -n 'requires-python' pyproject.toml
6:requires-python = ">=3.12"

$ uv run python -V
Python 3.12.12

$ uv run python -c "from datetime import datetime; print(datetime.fromisoformat('2026-08-13T05:27:15.943Z'))"
2026-08-13 05:27:15.943000+00:00
```

Full RFC3339 parsing, including the `Z` suffix, landed in `fromisoformat()` in
Python 3.11. The project floors at 3.12, so no supported interpreter exhibits the
described failure. The finding generalized from Python 3.10-and-earlier behavior.

**Residual observation (not a finding, recorded so the skip is not mistaken for an
oversight).** The `except ValueError: continue` at line 135 and the `len(ts) < 16:
continue` at line 131 are genuinely silent, and a third path is unguarded: if one
transcript ever mixed offset-aware and naive timestamps, `dt - prev_dt` at line 138
would raise `TypeError`, which the surrounding `except ValueError` does not catch.
No transcript format currently in use produces either input. Latent, not live.

### A2 · `tests/test_transcript_digest.py:12` — **REAL**

**Claim.** `SCRIPT` is a CWD-relative path, so pytest run from another directory
cannot find the script.

**Evidence.** Reproduced. Line 8 reads
`SCRIPT = Path("plugins/session/skills/session-recap/scripts/transcript_digest.py")`.
Running the suite from `tests/`:

```
$ cd tests && uv run --project .. pytest test_transcript_digest.py -x -q
>       assert "/r/a" in out and "main" in out
E       AssertionError: assert ('/r/a' in '')
1 failed in 0.65s
```

**Aggravating detail the finding did not mention.** The failure is opaque. Because
the missing script is invoked through `subprocess.run`, the interpreter's "no such
file" goes to stderr while the test asserts on stdout — so the symptom is an
assertion against an empty string, not a file-not-found error. Anyone hitting this
would debug the digest logic, not the path.

**Fix direction.** `Path(__file__).resolve().parents[1] / "plugins/..."`. Add a
check on `result.returncode` in `run()` so a missing script fails loudly.

### A3 · `session-agent-list/references/format-spec.md:299` — **REAL** (security)

**Claim.** `--exec` mode emits runnable bash built from session-derived paths and
metadata, without shell-safe quoting.

**Evidence.** The skill ships no scripts — it is `SKILL.md` plus
`references/format-spec.md`, i.e. prose instructing a model to emit bash. Searching
the entire skill for any quoting, escaping, or sanitization guidance returns nothing:

```
$ grep -rniE 'quot|shlex|escap|metachar|sanitiz' .
references/format-spec.md:342:- **No blockquote rail** — removed by user request ...
references/format-spec.md:344:- Blockquote-rail removal, TLDR position, lineage-with-title, command spacing ...
```

Both hits are the word "blockquote". There is no quoting rule anywhere.

**Two independent exposure paths, one mundane and one not:**

1. **Correctness.** The rendered command form is `cd <path> && claude --resume <uuid>`.
   Any checkout path containing a space breaks it. This needs no adversary.
2. **Injection.** Session titles are model-generated *from transcript content*. A
   transcript can contain text an agent fetched from the web or read from a
   dependency. That text can therefore reach a bash block the user copy-pastes into
   a shell. This is the chain that justifies the finding's severity rating.

**Fix direction.** Require single-quoted paths with embedded-quote escaping; forbid
transcript-derived free text (titles, summaries) from appearing anywhere in an
executable line — restrict it to comment lines.

---

## Cluster B — `document-merge`

### B1 · `assets/plan_template.md:64` — **REAL**

**Claim.** The Phase 8 byte-identical check compares paths that change during the
archive move, so it cannot match.

**Evidence, with a correction to the finding.** `SKILL.md:153-156` handles the path
change correctly — it rewrites archive paths back to source paths before diffing:

```bash
shasum -a 256 <archive-dir>/*.md | sort | sed "s| <archive-dir>/| <source-dir>/|" > /tmp/post-archive-sums.txt
diff <consolidated-dir>/.source-sha256-pre-merge.txt /tmp/post-archive-sums.txt
```

The defect is confined to the **template**, which abbreviates that pipeline to a
bare, non-runnable `sed`:

```
plan_template.md:64:  - [ ] Verify byte-identical: `shasum -a 256 <archive-dir>/*.md | sort | sed | diff <baseline>` (expect zero diff)
```

`sed` with no script argument is a usage error, and `diff` is given one operand.
The template hands the user a command that cannot run.

**Fix direction.** Replace line 64 with the working pipeline from `SKILL.md`, or
point the checklist at it rather than paraphrasing it.

### B2 · `references/cfl_classification.md:54` — **REAL**

**Claim.** Withdrawn entries make the validation gate fail permanently.

**Evidence.** Reproduced. `cfl_classification.md:54` *requires* a withdrawn ID to
stay in the log: "leave the ID retired with a one-line `**Status:** Withdrawn —
<reason>` note instead of renumbering." Its inline marker is necessarily gone from
the merged doc. Given a log holding `CFL-001` (live) and `CFL-007` (withdrawn), and
a doc marking only `CFL-001`:

```
$ bash validate_round_trip.sh log.md merged.md
FAIL: log entries without matching inline markers:
  - CFL-007
exit=1
```

Two shipped rules contradict each other: the ID-hygiene rule mandates a state the
Phase 4 gate rejects. Once any conflict is withdrawn, the gate can never pass again.

**Fix direction.** Have the validator skip entries whose body carries a
`**Status:** Withdrawn` line.

### B3 · `scripts/validate_round_trip.sh:31` — **REAL-BUT-DESIGN**

**Claim.** `sort -u` makes markers and entries into sets, so two `CFL-001` markers
pass against one log entry. The regex is also too loose.

**Evidence.** The behavior reproduces exactly as described:

```
$ printf 'a <!-- CONFLICT: CFL-001 -->\nb <!-- CONFLICT: CFL-001 -->\n' > dup.md
$ bash validate_round_trip.sh log2.md dup.md
PASS: 1 markers and 1 entries (all matched)
```

**Why this is a decision, not a bug.** The contract as written is set-equality, and
set semantics satisfies it. `SKILL.md:102`: "it enforces that every
`<!-- CONFLICT: CFL-XXX -->` marker in the merged docs has a matching ... entry in
the decisions log, and vice versa." Two markers citing one conflict is plausibly
*legitimate* — one decision affecting two passages. Making this 1:1 would forbid
that, which may or may not be intended.

**Owner decision needed.** Is a CFL ID allowed to be referenced from more than one
place in the merged output?
- **If yes** (recommended): current behavior is correct; close as by-design and
  make `SKILL.md:102` say so explicitly.
- **If no**: drop `-u`, compare with counts, and state the 1:1 rule in
  `cfl_classification.md`.

The "loose regex" sub-claim is minor and true — `grep -oE "CONFLICT: CFL-[0-9]+"`
matches that string anywhere, including inside a fenced code block or prose. Worth
tightening to the full comment form only if the 1:1 decision reopens the file.

### B4 · `scripts/validate_round_trip.sh:25` — **REAL**

**Claim.** The loop silently ignores a missing document path; with all documents
missing and an empty log, both sets are empty and the script passes.

**Evidence.** Reproduced, and this is the most serious defect in Cluster B:

```
$ bash validate_round_trip.sh log.md ./typo-doc-1.md ./typo-doc-2.md
PASS: 0 markers and 0 entries (all matched)
exit=0
```

The gate reports success for files it never opened. A path typo in the Phase 4
invocation converts "I verified the round-trip" into "I verified nothing", with a
green result either way.

**Note on blast radius.** The hole needs an empty log to be fully silent — with a
populated log the missing doc surfaces as a false FAIL instead:

```
$ bash validate_round_trip.sh log2.md ./mergedTYPO.md
FAIL: log entries without matching inline markers:
  - CFL-001
```

So the failure mode is worst exactly where it is least likely to be questioned: a
merge with no conflicts logged yet.

**The script already knows better.** Line 17 hard-fails on a missing decisions log
(`FAIL: decisions log not found`). Line 25 silently skips a missing merged doc. Same
class of input, two policies, one file.

**Fix direction.** Make a missing merged doc a hard error, matching line 17. Also
fail when the argument list resolves to zero readable documents.

### B5 · `scripts/coverage_audit.sh:39` — **REAL** (minor; documentation-vs-behavior)

**Claim.** The script only writes a heading list and a reminder; it never reads
`decisions-and-conflicts.md` and never compares against the topic map and omission
log, so it does not enforce the coverage contract it documents.

**Evidence, with a correction.** The script's own header is honest about what it is
— "dump every source heading **so the model can diff** against the topic-to-source
map" — and `SKILL.md:134-143` correctly describes a human/model comparison step.
The claim that it fails to enforce a contract *it documents* is therefore not quite
right at those two sites.

The mismatch is real at a third site the finding did not cite. `SKILL.md:168` bills
it as:

```
- `scripts/coverage_audit.sh` — Phase 7 source-heading vs. topic-map diff.
```

It performs no diff and never opens the topic map. A reader of the resource list
reasonably concludes Phase 7 is automated when it is manual.

**Fix direction (cheap).** Reword line 168 to "source-heading dump for the Phase 7
manual coverage diff." Promoting the script to a genuine enforcing diff is a larger
change and belongs with B8 as a design question.

**Unrelated observation while reading (recorded, not proposed).** Line 22 hardcodes
`OUT="/tmp/source-headings-audit.txt"`, a fixed path that collides across concurrent
merges. Not part of any finding; noted only so a future reader knows it was seen.

### B6 · `scripts/coverage_audit.sh:30` — **MIXED: half WRONG, half REAL**

**Claim.** Phase 2 and Phase 7 use different, incomplete heading parsers, so source
sections can escape the topic map.

**The "different" half is WRONG.** The two parsers are byte-identical:

```
SKILL.md:87              grep -nE "^#{1,3} " "$f"
coverage_audit.sh:30     grep -nE "^#{1,3} " "$f"
```

**The "incomplete" half is REAL**, and the finding understates it by attributing the
gap to divergence rather than to the shared expression. Both parsers stop at `###`.
Any `####` or deeper heading, and any setext-style heading, is never extracted by
either phase — so it can be neither mapped nor logged as omitted.

That collides with the skill's headline guarantee, `SKILL.md:29`: "**Every source
heading is accounted for.** Either it's mapped to an output section, or it's logged
as intentionally omitted with a reason. **No silent drops.**" Deep headings are a
silent drop by construction.

`SKILL.md:69` does scope the extraction to "every `#`, `##`, `###` heading", so the
document contradicts itself between line 29 and line 69.

**Fix direction.** Decide which promise is true. Either widen both greps to
`^#{1,6} ` (and keep line 29's guarantee), or narrow line 29 to state that the
contract covers headings through `###` only. Whichever is chosen, change both sites
together — their current agreement is the one thing this finding got wrong, and it
would be a shame to break it.

### B7 · `SKILL.md:152` — **REAL**

**Claim.** Plain `mv` can overwrite an existing archive file; source files from
different directories can share a basename; the checksum comparison does not detect
the loss.

**Evidence.** The primary claim reproduces, and it destroys user data:

```
$ mkdir -p a b archive && echo "ORIGINAL-A" > a/notes.md && echo "ORIGINAL-B" > b/notes.md
$ mv a/notes.md archive/notes.md; mv b/notes.md archive/notes.md
archive contains: ORIGINAL-B  (files: 1)
```

`ORIGINAL-A` is gone, with no error and no prompt — a direct breach of the skill's
inviolable-originals guarantee.

**Two corrections to the finding:**

1. **The git path is already safe.** `SKILL.md:152` prefers `git mv` in a repo, and
   `git mv` refuses the clobber: `fatal: destination exists, source=b/notes.md,
   destination=archive/notes.md` (exit 128). Only the non-git `mv` branch is
   exposed.
2. **The checksum comparison *does* detect it.** The baseline holds two entries and
   the post-archive hash holds one, so the Phase 8 `diff` is non-empty and the
   "stop, investigate" guard fires. But detection happens *after* an irreversible
   deletion, in the one environment (non-git) with no way to recover the file.
   Detection is not the same as prevention here.

**Fix direction.** Use `mv -n` and check for basename collisions across source
directories *before* moving anything; on collision, disambiguate with a directory
prefix rather than failing late.

### B8 · `SKILL.md:162` — **REAL-BUT-DESIGN**

**Claim.** Phase 8 moves user files and commits without confirming the
source-to-archive mapping or the commit.

**Evidence.** Confirmed by reading `SKILL.md:149-163`. The five Phase 8 steps run
create-archive, move, verify, validate, commit with no confirmation gate, on the
user's own documents.

**Why this is a decision.** How interactive `document-merge` should be is a product
question about the skill, not a bug with one right patch. It also interacts with B7:
a pre-move collision check would catch the destructive case without adding a prompt.

**Owner decision needed.** Choose one:
- **(a) Pre-move confirmation** — print the full source-to-archive mapping and
  require assent before the first `mv`. Safest; adds a stop to every run.
- **(b) Silent-but-safe** (recommended) — no prompt, but a pre-move collision check
  plus `mv -n`, and stage the archive move without committing, leaving the commit to
  the user. Removes the irreversible step without adding friction.
- **(c) Status quo** — accept it, and state the destructive behavior in the skill's
  preamble so it is disclosed rather than discovered.

### B9 · `references/anchor_rules.md:10` — **REAL** (highest confidence in Cluster B)

**Claim.** `github-slugger` strips em/en dashes and then converts spaces to `-`, so
`## A — B` yields `#a--b`. Rules 3-4, line 42, and `SKILL.md:130` disagree.

**Evidence.** Settled by running the actual library (`github-slugger` v2.0.0):

```
"A — B"                                                          ->  #a--b
"A – B"                                                          ->  #a--b
"4.5 The Special JSON Payload — How GCP Interprets Your stdout"  ->  #45-the-special-json-payload--how-gcp-interprets-your-stdout
"Section 1.2: Topic!"                                            ->  #section-12-topic
"Reads/Writes"                                                   ->  #readswrites
"The `useEffect` Hook"                                           ->  #the-useeffect-hook
```

The dash rules are not merely wrong, they are **inverted**, and the document
reinforces the inversion twice:

- **Rule 3** calls the collapse "the single most common gotcha" and promises `#a-b`.
  Actual output: `#a--b`.
- **Rule 4** promises `#a-b` for en dashes. Actual output: `#a--b`.
- **Line 42**, under "Common bugs caught by reviewers", lists the double-hyphen form
  as *the bug* and the single-hyphen form as the correction. The library emits
  exactly the form the document calls a bug.

Rules 5-10 all verified **correct** (punctuation, slashes, backticks, numbers), so
the damage is confined to the two dash rules and the line-42 example.

**Severity note.** This is the worst shape a reference document can take. It does
not omit a rule; it teaches the inverse and labels the correct output a defect. An
agent following rule 3 writes broken cross-links, and — worse — would "correct"
working ones it encounters.

**Fix direction.** Rewrite rules 3-4 to state that em/en dashes are removed and each
surrounding space becomes a hyphen, yielding a double hyphen; invert the line-42
example to show `#...payload--how-gcp...` as correct; re-check `SKILL.md:130`.

**Secondary defect found while verifying.** The line-42 example writes `#54-` for a
heading numbered `4.5`, which slugs to `#45-`. The digits are transposed in the
document's own example.

---

## Cluster C — skill content and contracts

### C1 · `clear-technical-communication/SKILL.md:28` — **WRONG** (with a minor residual)

**Claim.** Line 176 presents `~/.claude/settings.json` as a normal artifact, lines
26-28 instruct the skill to read a user-pointed file, and lines 210-215 require
exact reproduction — composing into a read-and-echo path for agent configuration.

**Evidence.** The three cited lines do not compose:

- **Line 176** is one cell in a classification table. `~/.claude/settings.json`
  appears as an *example of a path-shaped verbatim name*, in a list alongside
  `Promise.allSettled`, `--ff-only`, `ENOTEMPTY`, and `UserAccountRepository`. The
  rule attached to it is "reproduce the name exactly, in code font" — a rule about
  **names**, not about file contents.
- **Lines 26-28** scope reading to what the user points at: "If the user points to a
  file, diff, commit, or report, read that artifact rather than inventing a
  representative example." That is ordinary skill behavior, and it names no file.
- **Lines 210-215** ("Never edit verbatim zones") forbid *paraphrasing* quoted text.
  Nothing there directs anything to be read or emitted.

No instruction anywhere reads `~/.claude/settings.json`, and nothing echoes file
contents. The finding assembles three unrelated lines into a path that the document
does not contain. This matches the prior assessment carried in the handoff.

**Minor residual worth a line (offered, not urged).** The verbatim-reproduction rule
has no secret-redaction caveat. A user who points the skill at a real settings file
or a log would have it reproduced character-for-character by design. One sentence —
"redact credential values when reproducing a user-supplied artifact; the redaction
is not a verbatim-zone violation" — would close it. This is a genuine small gap, but
it is not the finding as written.

### C2 · `clear-technical-communication/references/worked-examples.md:67` — **REAL** (minor)

**Claim.** The source names `T-X-…` rows in `G-VER`; the rewrite keeps only `G-VER`
plus a generic description, contradicting the file's own rule that names are never
removed.

**Evidence.** Confirmed, and the contradiction is self-inflicted at close range. The
example's own defect list at line 32 names the problem:

```
- Bare local identifiers: `G-MAT`, `G-ANC`, `G-VER`, and `T-X-…` have no descriptions.
```

The rewrite then carries `G-MAT`, `G-ANC`, and `G-VER` into a table — and drops
`T-X-…` entirely. It also asserts at line 55 that "the names are used here exactly
as the source writes them", which is untrue of the fourth name. The skill's iron
rule ("never replace a name with a description", "removing required precision is a
defect") is violated by its own worked example.

**Mild mitigation.** `T-X-…` is itself an elision standing for a family of test IDs,
so dropping it is more defensible than dropping a concrete name would be. That
lowers severity; it does not resolve the contradiction, because the example
diagnosed the name as needing a description and then supplied none.

**Fix direction.** Add one clause to the rewrite naming `T-X-…` as the individual
test-case identifier family and stating that the specification must define its
naming scheme.

### C3 · `session-handoff/SKILL.md:63` — **REAL**

**Claim.** The direct-copy install contract installs only `session-handoff`, but the
skill requires the sibling `session-recap` script; installation is not
self-contained.

**Evidence.** Both halves confirmed. The skill reaches across to the sibling at
`SKILL.md:60-62`:

```bash
d="$(cd "<skill-dir>" && pwd -P)"
python3 "$d/../session-recap/scripts/transcript_digest.py"
```

And the published install row at `docs/skills/session-handoff.md:44` copies one
directory:

```
| Direct copy | No marketplace access | copy `plugins/session/skills/session-handoff/` into `~/.claude/skills/` |
```

After a direct copy, `$d/../session-recap/` does not exist. The plugin and
dev-symlink rows are unaffected — both bring the whole `session` plugin, so the
sibling resolves.

**Sharpened diagnosis.** The skill is careful about *symlink* resolution here (the
`pwd -P` comment explains why a lexical path fails) but not about *existence*. It
handles the hard case and skips the easy one, and there is no fallback when the
sibling is absent.

**Fix direction.** State on the direct-copy row that `session-recap/` must be copied
alongside; and have the skill degrade explicitly when the sibling script is missing,
the way it already degrades on `NO_TRANSCRIPT`.

### C4 · `session-handoff/SKILL.md:200` — **REAL** (and demonstrated live)

**Claim.** The cross-machine launch contract uses an absolute path from the source
machine; it should use the repo-relative path as the portable command.

**Evidence — this session is the reproduction.** The handoff that started this work
rendered its launch line per `SKILL.md:196-198`:

> ▶ Start a new session in `<repo>` and paste:
> `Read <abs-path-to-handoff>.md and continue.`

The pasted prompt was `Read docs/handoffs/2026-08-13-triage-inherited-findings.md
and continue`. It did not resolve: this session opened in a **different repository**
(`smorin-harness/plugins`), so the relative path pointed at nothing and the file had
to be located by searching the filesystem.

**This sharpens the finding rather than confirming it.** The reviewer framed the
problem as absolute-vs-relative. Live evidence says both forms fail, for the same
underlying reason: **the launch line's two halves get separated.** The repo identity
lives in prose *around* the pasteable command, and only the command survives a
copy-paste. An absolute path breaks across machines; a relative path breaks across
repos.

**Fix direction.** Make the pasteable string self-locating, so the surviving half
carries the repo identity — for example `cd ~/c/<repo> && ...`, or a prompt that
names the repository explicitly, with the bare path offered only as a local
convenience. Note that C4's fix must also satisfy this repo's absolute-path CI gate.

### C5 · `session-recap/SKILL.md:87` — **REAL**

**Claim.** Both fallbacks pick the newest transcript across all Claude projects,
though handoff and recap need the *current* session.

**Evidence.** The prose and the command directly contradict each other at
`SKILL.md:82-87`. The sentence promises repo scope — "fall back to the most recently
modified transcript **for this repo**" — and the command has none:

```bash
ls -t ~/.claude/projects/*/*.jsonl | head -1
```

That glob spans **86 project directories** on this machine. It returned a
current-repo transcript when tested, which is precisely the hazard: the bug is
invisible whenever the current session is also the most recent one, and silently
wrong the moment it is not — recapping some other repo's work as if it were yours.

**Note on the sibling.** `session-handoff/SKILL.md:69` uses the same glob but
describes it accurately as "the newest transcript **on this machine**
(best-effort)". Its wording is honest; the behavior is still wrong for the stated
need. Fix both, but only `session-recap` is also mis-documented.

**Fix direction.** Claude Code encodes the working directory into the project
directory name (this session's is `-Users-...-smorin-harness-plugins`), so a
repo-scoped glob is derivable from `$PWD` rather than guessed. Failing that, require
an explicit transcript path instead of silently picking one.

### C6 · `session-agent-list/references/format-spec.md:87` — **REAL-BUT-DESIGN**

**Claim.** `gh pr merge` or "merged #n" in a transcript shows intent or text, not
proof the PR merged; closure evidence should be verified.

**Evidence.** The mechanism is as described, at `format-spec.md:84-85`:

```
- `gh pr merge` / "merged #n" **plus** `git worktree remove` in the tail → `✔`
- The merge **without** the cleanup → `◒`
```

A `gh pr merge` that *failed* leaves identical transcript text to one that
succeeded. So does a user typing "merged #n" in prose.

**Why this is a decision, not a bug.** The spec labels these "Detection signals
(classifier heuristics)" and already requires `Conflicting signals → state the
evidence, never guess silently`, so it is self-aware. The tension is that the
rendered output is a confident factual glyph (`✔` closed clean) derived from
deliberately weak evidence.

**A real constraint bears on the choice.** Verifying closure means one `gh` call per
candidate session, and GitHub GraphQL-backed commands are documented as
rate-limit-prone on this machine, with REST preferred and polling held to one call
per 20 seconds. A listing over many sessions could be slow or rate-limited.

**Owner decision needed.** Choose one:
- **(a) Verify on drill-down only** (recommended) — keep the heuristic for the fast
  listing; when a card is expanded, confirm via `gh api repos/<owner>/<repo>/pulls/<n>`
  (REST, not GraphQL) and correct the glyph. Bounded call volume, accurate where it
  matters.
- **(b) Always verify** — accurate everywhere, but N API calls per listing and
  exposure to rate limits.
- **(c) Keep heuristics, weaken the claim** — render an unverified closure with a
  distinct glyph or an "inferred" qualifier so `✔` never overstates.

### C7 · `docs/skills/design-by-elements.md:36` — **WRONG**

**Claim.** The Codex marketplace install flow should use
`$REPO_ROOT/.agents/plugins/marketplace.json` or `~/.agents/plugins/marketplace.json`
with a `source.path` entry, keeping `.codex-plugin/plugin.json` as the manifest and
`~/.codex/config.toml` only for enable/disable.

**Evidence.** Refuted by the live installation on this machine. The documented
mechanism is in use, and the proposed replacement does not exist:

```
EXISTS: ~/.codex/config.toml
absent: ~/.agents/plugins/marketplace.json

$ grep -n 'marketplace' ~/.codex/config.toml
335:[marketplaces.openai-bundled]
340:[marketplaces.openai-primary-runtime]
345:[marketplaces.py-launch-blueprint]
350:[marketplaces.smorinlabs-harness]
```

`~/.codex/config.toml` carries a working `[marketplaces.smorinlabs-harness]` entry —
exactly what the docs instruct — including entries Codex itself installed
(`openai-bundled`, `openai-primary-runtime`). The file the finding proposes as the
correct location is not present anywhere. The docs describe reality.

**Scope note, and why this verdict earns its keep.** The handoff flagged that this
text is not unique to one page. Confirmed: **all 30 of 30 pages** under
`docs/skills/` carry it. Acting on this finding would have rewritten every skill
page in the repository to point at a path that does not exist.

**Caveat recorded for honesty.** This refutes the claim against the Codex version
installed here. If a future Codex release moves to an `.agents/plugins/marketplace.json`
convention, all 30 pages change together — a migration to plan deliberately, not a
review finding to apply.

---

## Cluster D — already resolved or adjudicated

### D1 · `docs/skills/session-status.md:4` — **ALREADY FIXED** (verified)

```
$ grep -n -i 'quartet\|quintet' docs/skills/session-status.md
3:The mid-flight glance of the session quintet: a fast, plain-language
```

Fixed by PR #43 (commit `fc404ec`). No occurrence of "quartet" remains. No action.

### D2 · `PROJECTS.md:1398` — **WRONG** (previously adjudicated; re-verified)

**Claim.** Remove the private source repository name `smorin/smorin-harness`.

**Evidence.** The name is not a new disclosure. It appears **18 times** across
tracked `.md`, `.json`, `.toml`, and `.yml` files in this public repository, and
`README.md:173` publishes a working link into the private repo:

```
[`smorin-harness/docs/skills-placement-strategy.md`](https://github.com/smorin/smorin-harness/blob/main/docs/skills-placement-strategy.md).
```

Scrubbing the single mention at `PROJECTS.md:1398` — where it records the
provenance of the P39 migration — would remove traceability while leaving 17 other
occurrences and a live hyperlink in place. It was deliberately excluded from every
scrub pattern during the migration.

**Do not act on this finding.** Reversing the decision is an owner conversation
about the repository's disclosure posture, not a code change.

---

## What Phase 2 should look like

Suggested PR clustering, ordered by value. Each behavioral fix ships with a
regression test that fails before it, and `just all` green before each PR.

| PR | Findings | Character |
|---|---|---|
| 1 · `document-merge` validation gates | B2, B4 | Two reproduced gate defects with runnable repros; highest value, lowest risk |
| 2 · anchor rules correction | B9 | Doc-only, verified against the library; currently teaching the inverse rule |
| 3 · shell safety | A3, B7 | Quoting rules for `--exec`; collision-safe archive move |
| 4 · test and install correctness | A2, C3 | Path resolution and the direct-copy contract |
| 5 · session-transcript scoping | C4, C5 | Portable launch line; repo-scoped fallback |
| 6 · documentation accuracy | B1, B5, B6, C2 | Template command, resource-list wording, heading-depth contract, worked example |

**Blocked on owner decisions before any code:** B3 (marker cardinality), B8
(interactivity of Phase 8), C6 (verified closure vs. heuristic), and the B6 half
that asks which coverage promise is true.

**Closed with no action:** A1, C1, C7, D2 (refuted with evidence above) and D1
(already fixed).
