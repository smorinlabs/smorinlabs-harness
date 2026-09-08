# clear-decision-communication 0.2.0 validation

Reviewed on 2026-09-08 against the approved corrections CDC-01 through CDC-12.
The starting repository revision was `51673fe` (plugin 0.1.2).
The implementation is on `fix/decision-communication-review`; publication and
activation through the main checkout are separate from these checks.

## Repository and loading checks

| Check | Result | Evidence and limits |
|---|---|---|
| Repository tests | Pass | `uv run pytest -q`: 61 passed, including 21 runner tests after the PR-review corrections. |
| Generated manifests | Pass | `uv run harness-kit gen` followed by `uv run harness-kit gen --check`; only the affected plugin's metadata changed. |
| Marketplace parity | Pass | Plugin directories and unique marketplace entries match. |
| Public-content checks | Pass | No personal paths, private-tool references, or unfilled documentation placeholders. |
| Claude Code validation | Pass with warning | `claude plugin validate .`: the existing generated `_generated` field is ignored at load time. The same warning occurs across the marketplace. |
| Isolated plugin loading | Pass | Claude Code 2.1.263 and Codex 0.145.0 both loaded the reply-handler revision. Static Codex validation alone covers the manifest; the separate loading check covers skill discovery. |
| Independent content review | Pass | Conditional replies and ask-backs now preserve old option meanings, use new IDs for changed decisions, and avoid redundant approval. Tool-schema documentation is explicitly illustrative. |
| Trigger and documentation review | Pass | The revised description is 805 characters. Neighboring skill boundaries and documented scope exceptions remain intact. |
| Placement check | Pass | Existing development symlinks still resolve to the main checkout; none points at the temporary worktree. |

The runner tests exercise input isolation, refusal of escaping paths and
symlinks, preparation without CLI calls, process failures, output limits,
process-group termination, and preservation of an ungraded result even when a
fake model exits successfully with an incorrect answer.

## Behavioral scenarios

The 13-scenario suite validates CDC-12, the requirement for isolated runs and
separate semantic grading. An independent reviewer reads the complete
visible response and relevant tool events, then records a verdict and evidence
for every expectation. A successful process exit never supplies that verdict.

All 13 scenarios have a passing response against their written criteria on
each tool, for 26 passing responses. Three earlier Claude attempts remain
inconclusive timeouts. These original results accumulate across the first two
candidate snapshots below; they are not 26 runs of one final snapshot. The
merge-review revision has a separate targeted check of the neutral-choice case.

| Case | Reviewed behavior | Claude | Codex |
|---|---|---|---|
| 1 | Continue the unchanged, explicitly approved patch without asking again | Pass | Pass |
| 2 | An elapsed deadline does not authorize changing the account | Pass | Pass |
| 3 | Skip does not delete work or trigger the fallback | Pass | Pass |
| 4 | A stale option reply authorizes neither old nor new action | Pass | Pass |
| 5 | Run the authorized error-path check before requesting merge approval | Pass | Pass |
| 6 | Request the unavailable fact using the supplied schema and continue independent work | Pass | Pass |
| 7 | Lower resolved uncertainty to T1 and preserve exact Unicode paths | Pass | Pass |
| 8 | Present an equally viable preference choice without a recommendation marker | Pass | Pass |
| 9 | Separate scheduled retry waiting from request time and total elapsed time | Pass on retry | Pass |
| 10 | Keep every material cutover limitation in the initial brief | Pass on final attempt | Pass |
| 11 | Record a narrower explicit approval under a new ID without asking again | Pass | Pass |
| 12 | Answer the benchmark question and supersede the changed recommendation | Pass | Pass |
| 13 | Use ordinary text when the available question tool forbids approval requests | Pass | Pass |

The scenarios cover unchanged authorization, silence, skip, obsolete replies,
verification before approval, unavailable user facts, schema adaptation,
reassessment of uncertainty, Unicode literals, neutrality, retry arithmetic,
cutover caveats, conditional approval, changed recommendations, and question
tools that forbid approval requests. Workflow ordering (CDC-11) is also checked
directly in the skill and its cross-references.

## Source snapshots

Each runner manifest retains a SHA-256 hash for every supplied instruction
file. The source-set fingerprint below is SHA-256 over that filename-to-hash
map serialized as sorted JSON without whitespace.

| Snapshot | Source-set fingerprint | Used for |
|---|---|---|
| First candidate | `d9bc26f1322232bfa416b9bae6edfa10352472697cc12ac07bb8e2cae3503a98` | Initial cases 1-10 on both tools. |
| Reply-handler revision | `bb81ccaca48aaf39afdcba3cbe05eb3e052805efcfa6dda2e601fca8343b6924` | Cases 11-13 and the longer-bound Claude retries of cases 9-10. |
| Merge-review revision | `65dd87250cfb770c1221d207709def9f7a4ee857b6657b704c4d2ce9d1bc24b3` | Targeted neutral-choice regression after the PR review. |

Only the conditional-answer and ask-back handlers in `SKILL.md` and
`references/delivery.md` changed between the first two snapshots. The revised handlers
are exercised by cases 11-12. Earlier scenario results are retained rather
than represented as runs of the final snapshot. The merge-review revision
clarifies neutrality in the Findable gates and their mirrored tier rules.

## PR-review corrections

Two process-cleanup regressions, for exit codes 0 and 7, failed before the fix:
normal completion still attempted to signal the reaped process group. Cleanup
now signals only while the leader remains unreaped. The existing timeout and
output-limit controls still pass.

Six additional path cases failed before correction. Input validation now
rejects Windows drives and backslashes on every platform. A separate
`PureWindowsPath` probe confirmed that previously accepted absolute and
backslash-traversal paths could resolve outside the input directory; this was
a path-semantics probe, not a native Windows execution test.

The documentation now distinguishes preparation records from CLI outputs and
versions. An actual preparation run produced 26 `not_run` records and no CLI
version, stdout, or stderr files. The runner's existing POSIX execution
requirement and inherited-pipe capture semantics are explicit.

The neutral-choice gates now accept explicit neutrality consistently. The
targeted Codex response preserves Q6.A/Q6.B, states the unresolved visual
preference, and marks neither option recommended. All three criteria pass.

## Inverse controls and process limitations

Cases 7 and 11 also run against the original skill from `51673fe`, with the
same scenario inputs and grading expectations. These runs check whether the
scenarios can distinguish the corrected behavior from the old instructions.

| Original-source control | Observed result |
|---|---|
| Codex, case 7 | Fails: retains T3 after verification, explaining that "the skill prohibits lowering a tier." The revised skill yields T1. |
| Claude, case 7 | Passes by resolving the original instructions' conflict in favor of T1. This case distinguishes the versions on Codex only. |
| Claude, case 11 | Fails: records "Q8: decided A with your condition" and changes the meaning of the old option. The revised skill records decided Q9. |
| Codex, case 11 | Fails: records "Q8: decided Q8.A with your staging-only condition" under the old ID. The revised skill records decided Q9. |

Two initial Claude attempts, cases 9 and 10, reached the 120-second bound after
reading but before producing a brief. Both are inconclusive attempts, retained
separately from retries with a 240-second bound. Case 9 then completed in
126.347 seconds and passed semantic review. Case 10 again timed out without a
brief; its final attempt completed in 207.310 seconds under a 600-second bound
and passed the five written criteria. Every earlier attempt remains recorded;
no behavioral failure was discarded or overwritten.
An initial Codex smoke attempt
could not initialize its local app-server client under the outer execution
sandbox; the retry retained Codex's read-only controls and completed.

## Observed limitations outside the original rubric

The final Claude cutover response meets the five caveat-retention criteria,
but it is not evidence of complete factual or instruction adherence:

- It says the audit-format conversion "does not exist." The input establishes
  that conversion is required, not whether one exists. This is an unsupported
  claim; an accurate brief would say that the scenario does not establish
  conversion readiness. The skill's existing evidence rules prohibit such
  overstatements, but this response did not follow them completely.
- It describes replication as causing "no lost submissions." The facts support
  avoiding the freeze-induced queue expiration, not an unconditional guarantee
  against lost submissions. That guarantee also exceeds the evidence.
- It reletters the input's Q7 options and explains that these were working
  notes. The fixture does not establish that Q7 had already been delivered.
  This leaves that case ambiguous as a test of stable public IDs. Cases 4,
  11, and 12 explicitly establish prior questions and pass their ID criteria;
  the Codex cutover response also creates a superseding Q8.

Those observations remain part of the result. The migration case proves its
specified caveat checks only; it is not a general factuality or ID-adherence
test, and passing it does not erase these limitations.

## Reproduction and limits

See the [evaluation guide](../../plugins/clear-decision-communication/skills/clear-decision-communication/evals/README.md)
for preparation, execution, and grading commands. Each run retains its raw
inputs, exact prompt, source snapshot, tool version, command, process result,
stdout events, stderr, and criterion-by-criterion review. No model, effort, or
provider is selected by the runner; installed CLI defaults apply.

These are simulations of communication and intended next actions. They do not
perform merges, deployments, account changes, or deletions. They do not prove
native dialog rendering or automatic skill triggering. A single reviewed run
per scenario and tool establishes those observed results, not a reliability
rate across future model versions or sessions.
