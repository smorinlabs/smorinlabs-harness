# Separate source-review experiment

Prepared on 2026-09-12 as the next P48-T08 experiment for draft PR #67.
The owner approved implementing and testing a fresh reviewer invocation after
the instruction-only source check failed to resolve the original errors.
The [candidate F record](clear-decision-communication-source-check.md) retains
that earlier result and the exact skill-text changes.

**Outcome:** the latest available finals for eight retained drafts comprise
seven material-validity passes and one failure, compared with three original
passes and five failures. These finals combine six R1 results and the two R2
reruns; they are not eight executions of R2. Several passes retain the explicit
qualifications below. The original two material errors are repaired in the
observed revisions, but the reviewer misses a benchmark-to-production guarantee.
Keep the process optional, the PR draft, and P48-T08 open. Neither skill is
merged or activated by this experiment.

## What changed

Before, the evaluation runner requested one response, captured it, and left a
separate grader to judge it. The skill instructed its author to check the draft
against its sources, but the runner did not execute a checker.

After, optional `--source-review` execution gives a fresh reviewer the complete
draft, original request, and raw sources. A valid report with findings causes
one fresh revision session. Independent evaluation then grades both the original
and final response against the same frozen criteria.

```text
Original request + raw sources + fixed skill
    -> complete writer response, retained unchanged as the baseline

Original request + raw sources + complete baseline response
    -> fresh reviewer session
       -> invalid report: retain failure, withhold final response
       -> no findings: retain baseline as final
       -> findings: one fresh revision with skill, sources, and report
                    -> complete revised response as final

Independent grader + original sources + frozen criteria
    -> separate baseline and final verdicts
```

The reviewer is another CLI invocation launched by `evals/run_evals.py`.
It is comparable to a sub-agent pass in purpose. It receives no private reasoning
trace or writer tool history. Visible rationale and process narration remain
included in the complete draft, and the original request remains task data.
It receives no grading criteria or prior grades. Nested agent delegation
remains disabled. The revision session checks
reviewer suggestions against the original sources; suggestions are not new
project facts or permission to act.

This remains an evaluation mechanism. An ordinary invocation of either
communication skill does not launch the new process.

| File | Actual change and reason |
|---|---|
| `evals/run_evals.py` | Add optional review/revision orchestration and exact draft reuse through `--drafts-from`. Preserve stage outputs, provenance, and blocked execution separately from semantic grades. |
| `evals/source-review.md` | Add a source-checking protocol with exact quotations, findings, supported claims to preserve, and calculation assumptions. It is outside the writer's instruction snapshot. |
| `tests/test_decision_eval_runner.py` | Exercise isolation, exact replay, incomplete/failed captures, structured report validation, one revision, and absence of silent fallback using local fake processes. |
| `evals/README.md`, skill page, and repository README | Explain the optional mechanism and its limits without claiming ordinary skill integration. |
| This report, portable results, reader record, historical pointer, and `PROJECTS.md` | Preserve results and P48-T08 dispositions with their exact implementation and source identities. |
| Both `SKILL.md` files and their references | No changes in this experiment. The decision skill remains candidate F; no installed placement changes. |

Paths beginning with `evals/` are relative to
`plugins/clear-decision-communication/skills/clear-decision-communication/`.

## Controlled comparison

R1 reviews eight exact saved F responses: Claude Cases 4, 14, 20, 21, and 22,
and Codex Cases 20, 21, and 22. No new writer response is substituted for a
known failure. Before launching models, the runner checks the prior manifest,
actual instruction hashes, raw input bytes, prompt bytes, and successful
complete captures, then freezes the capture bytes. Mismatches stop execution.

The nine instruction files retain F's fingerprint:
`da9f3c7ae8b83962dfccfca10f73f8f554227f70bfebd322995a88a4f5ef4d57`.
This hashes the sorted filename-to-SHA-256 map using compact JSON. All twenty-two
scenario objects also remain unchanged from commit `a2a2b1e`.

Both sides receive fresh independent grades using the same current criterion
text. Historical F grades remain untouched. In particular, Case 21 uses the
already documented amendment allowing conditional calculations with stated
assumptions; changing that criterion is not credited to this experiment.

R1's source-review protocol SHA-256 is
`33b944b34927d0fbfd10bc1f952cd14d8f97bce8c2bc0d62d9bf3d2dd88a7434`.
Its runner SHA-256 is
`f6d06e428ff257bc33f67cc0a3f52b790659af68cc88dd86e5e9a4f7398b9b51`.
Complete protocol and runner text, frozen criteria, raw inputs, prompts,
responses, hashes, and independent grades are retained in the
[portable archive](../../plugins/clear-decision-communication/skills/clear-decision-communication/evals/results/decision-source-review.json).

## Output-format correction

Two R1 reviewer responses, Claude Cases 4 and 21, included an introduction before
one fenced JSON report. Both processes completed successfully. The original
parser accepted bare JSON or a fence enclosing the entire response, so it
rejected both introductions. No revision ran and no final response was selected.
The blocked attempts remain in R1's results.

Their JSON bodies already pass the original schema and exact-quotation checks.
The R2 parser correction accepts one unambiguous fenced JSON payload with
surrounding prose. It preserves the complete captured response and does not
relax source paths, excerpts, schema, or independent grading. Ambiguous envelopes
still block. Only the two blocked cases are rerun under R2, with the same F
drafts and unchanged reviewer prompt. The new reviewer outputs are new samples;
any semantic difference cannot be attributed to parsing alone.

R2's runner SHA-256 is
`4270c066e7409734930dbe90d2ab1f49711b589341c6f665d75c617d870ddc6e`.
The original R1 runner is retained in the portable archive. Deterministic probes
against the same captured reports isolate the parser effect: Case 4's three
findings and six supported claims, and Case 21's two findings and nine supported
claims, validate without changing their JSON contents.

## R1 results

The eight original drafts have three overall passes and five failures. R1
selects six final responses: five overall passes and one failure. Two final
responses are unavailable because the reviewer reports were rejected. These
are counts of this retained sample, not estimates of future reliability.
For the six pairs with an available final, the same-sample comparison is two
original passes and four failures versus five final passes and one failure.
The two blocked pairs are excluded from that comparison, not counted as repairs.

| Tool and case | Original draft, current criteria | R1 final | Evidence-backed resolution or proposed disposition |
|---|---|---|---|
| Claude 4: stale export-approach answer | Fail; 3/3 targeted criteria | Unavailable: report envelope rejected | The reviewer identifies the aggregate-to-per-metric overclaim, but no revision runs. Retain the blocked attempt; test the parser correction only on this case and Case 21. |
| Claude 14: repository workflow activation | Fail; 5/5 targeted criteria | Pass; 5/5, with minor wording limits | Removes the repository-wide branch-incapability claim and the assertion that author restrictions are the sole option difference. Restores the documented update trigger and preserves its unmeasured call count. Process narration and a narrower testing-status wording issue remain. |
| Claude 20: two export benchmarks | Fail; 4/5 criteria | Fail; unchanged draft, 4/5 | The reviewer returns no findings despite production-cost and rollback-performance guarantees unsupported by the benchmark. Retain this material false negative; do not treat a valid no-findings report as permission to publish. |
| Claude 21: percentage without absolute timings | Pass with precision qualifications; 5/5 current criteria | Unavailable: report envelope rejected | Conditional mathematics remains allowed. The draft's rounded inclusive threshold and asserted measurement count remain qualifications. Preserve the original grade and test the parser correction without changing the criteria. |
| Claude 22: measured workflow allowance use | Fail; 4/5 literal criteria | Pass with qualifications; 4/5 literal criteria | Adds an immediate statement that per-invocation figures are averages, not observed per-call amounts. The conflicting word “each” remains, as does omission of the requested +150% representation. Do not call this a clean rewrite. |
| Codex 20: two export benchmarks | Pass; 5/5 | Pass; unchanged draft, 5/5 | Retains both exact assets, measured values, opposing metric directions, and production uncertainty. No regression observed. |
| Codex 21: percentage without absolute timings | Fail; 4/5 | Pass; 5/5 | Restores the exact module path and its role while preserving missing measurements, labeled hypothetical examples, and the approval boundary. |
| Codex 22: measured workflow allowance use | Pass; 5/5 | Pass; unchanged draft, 5/5 | Preserves the documented author gates, usage denominators, 40%/60% allowance shares, and pilot-scoped accounting comparison. No regression observed. |

The original Claude Case 21 pass and the revised Claude Case 22 pass are
qualified. Claude Case 14 also retains minor communication limits. Per-criterion
counts are retained separately from the whole-response material-validity verdict.
All eight R1 reviewer captures and all three requested revisions complete with
exit code zero. That does not override the two report-format failures or the
remaining material accuracy failure.

### Concrete changes in the generated responses

| Response | Before, exact captured text | After, exact captured text | What the source supports |
|---|---|---|---|
| Claude 14 | “no workflow can write a branch” | “the branch-preparing assistant job cannot run, and the review workflow is documented only to read the diff and post review comments” | The assistant's absent enable variable prevents that job from running. Documented review behavior does not establish the effective permissions of `HARBOR_TOKEN`. |
| Codex 21 | “For trial `SEARCH-19`, the September 11 summary reports candidate revision `8fd02c2` was 10% faster than baseline revision `7ce91b1`.” | “The affected source file, `web/search/suggestions.ts`, requests and displays catalog suggestions.” | The original response omitted this exact asset and role. The revision adds them; absolute baseline and candidate timings remain unknown. |
| Claude 22 | “each assistant invocation consumed 12.0 units against 2.0 for a review” | “Those per-invocation figures are averages over the window, not per-call measurements.” | The new qualification follows the retained “each” sentence. The pilot reports 120 allowance units across 10 assistant invocations and 80 units across 40 review invocations, establishing averages of 12 and 2 units per invocation. |

For Claude Case 22, the reviewer did not report the average-versus-individual
defect as a finding. It put the required averaging interpretation in its
supported-claim preservation text; the revision added that qualification. This
is observed partial repair, not evidence that the reviewer reliably detected
the error. The original misleading sentence should still be rewritten.

The same pilot's combined allowance use is a calculated 200 units: 80 review
units plus 120 assistant units. Relative to the 80-unit review component,
200 units is 120 units higher, a 150% increase, or 2.5 times as much. Both
workflows were enabled during the seven-day pilot; this accounting comparison
is neither a separate review-only experiment nor a forecast. The Claude final
retains the correct 2.5 multiple but omits the requested 150% representation.

## R2 affected-case results

| Case | R1 outcome | R2 observed final | Remaining qualification |
|---|---|---|---|
| Claude 4 | No final; report envelope rejected | Pass; 3/3 targeted criteria. The recommendation now says the benchmark favored streaming “under the agreed latency and operating-cost criteria.” The evidence explicitly leaves each criterion's outcome and measured values unknown. | “no export code has been written” and the unbuilt-feature claim infer source-tree state from an authorization record. The source establishes that implementation is not authorized, not the complete code state. |
| Claude 21 | No final; report envelope rejected | Qualified pass; 5/5 current criteria. The revision restores the owner's exact question, changes “One measurement” to “One reported summary result”, and makes the owner's ability to supply data conditional. | It still uses a rounded value as an exact inclusive limit, now 166.67 ms, and assumes the benchmark baseline is the current default behavior. Neither qualification establishes actual budget compliance. |

Both fresh R2 reviewers return a pure JSON fence. Their new envelopes would
also fit the original R1 parser; live completion therefore does not isolate the
effect of the correction. The unchanged captured R1-report probes and the
parser tests establish that effect. These two fresh reviews and revisions
establish only their own semantic outcomes. No unchanged case was retried to
obtain a pass, and no model prompt or criterion was amended after seeing R1.

The experiment uses fifteen new model invocations: ten reviewer calls and five
revision calls, including R2. The eight original writer captures are reused;
there are no new writer calls. Every stage has a 240-second bound and there is
no automatic retry or repeated revision loop.

## Remaining dispositions and P48-T08 closeout draft

The experiment is within P48-T08; it needs no separate project. Its implementation
and evidence collection can close while promotion and activation remain open.
The following are proposed dispositions, not edits to the captured responses
or new skill changes:

| Item | Evidence and status | Concrete correction or proposed disposition |
|---|---|---|
| Claude 20: unsupported production and rollback promises | Material failure remains. Correct benchmark tables coexist with “continues for as long as streaming runs” and “restores the earlier latency and cost”; the reviewer reports no findings. | State that EX-204 measured those changes under its stated conditions. Reverting to revision `7ab91c2` restores the implementation; restored production performance is unmeasured. Keep this failure as a required negative control before adopting automatic review. |
| Claude 4: source-tree state | Main benchmark overclaim repaired; minor code-state assertion remains. | Replace the unsupported code-absence assertion with the source fact: “No export implementation is authorized yet.” |
| Claude 14: negative-test status | Main capability and option-difference claims repaired; “no author check was tested” overstates missing records. | Say: “The supplied fixtures do not record whether a non-maintainer comment is rejected.” Do not infer that the guard is absent or has never been tested. |
| Claude 21: exact threshold and deployed baseline | Main conclusion remains correct: compliance is unknown. The source gives no deployment state or absolute measurements. | Use the exact condition “baseline p95 is at most `150 / 0.90` ms, approximately 166.6667 ms” under an exact-10% assumption. State that the candidate is not approved as the default; do not identify the current default without evidence. |
| Claude 22: individual versus average; requested percent | The adjacent averages qualification repairs the material inference, but “each” still conflicts and the +150% representation is missing. | Replace the whole sentence with “During the pilot, assistant invocations consumed an average of 12 allowance units each, compared with 2 units per review invocation.” Add “200 total units versus the 80-unit review component: 120 units higher, a 150% increase.” Keep the both-enabled pilot context. |
| Reviewer and revision narration | Several complete outputs still expose internal review/delivery logistics despite the instruction to return the complete user-facing response. | Preserve this limitation in the archive. Before any ordinary-skill integration, test whether revised responses can omit that narration without losing visible evidence, exact identifiers, or the next action. |

**Recommended closeout draft:** accept the evaluation machinery and evidence as
completed experimental work, while retaining the behavioral limitations above
and keeping PR #67 draft. Do not equate a no-findings report with an approved
response. Any promotion still requires an explicit disposition of those limits,
followed by separately authorized merge and stable-main refresh.

If the owner continues the experiment, a bounded next test is a different
reviewer on the exact failed Claude Case 20 draft, with the same sources and
two passing measurement controls. Keep writer and reviewer identities distinct,
retain all attempts, and check false corrections as well as missed claims.
This is a proposed comparison, not a proven repair or a reason to add another
generic self-check instruction to `SKILL.md`.

## Reader check

A [fresh reader](decision-source-review/reader-review.md) received the complete
Codex Case 21 final response and six neutral questions. It correctly recovered
the affected `web/search/suggestions.ts` module, its role requesting and
displaying catalog suggestions, both revisions, and the missing absolute p95
timings. It understood that the reported 10% reduction cannot establish
compliance with the 150 ms last-keystroke-to-paint budget.

The reader also recognized that no request had been sent and no default changed.
It identified unstated follow-up branches and recipient identity as gaps. There
is no matched baseline reader measurement, so this check does not establish a
measured improvement in comprehension.

## Verification and practical limits

| Layer | Result and coverage |
|---|---|
| Runner tests | 88 local fake-process tests passed in 1.99 seconds. The prior 62-test result preceded the 26 additional parser cases. Tests cover both CLI event formats, stage isolation, exact byte reuse including line endings and capture freezing, blocked/incomplete output, one revision, and unambiguous report extraction. No model calls occur in these tests. |
| Source and input identity | Both skill instruction sets and all twenty-two scenario objects remain unchanged from `a2a2b1e`. R1 and R2 runner/protocol identities and exact original drafts are retained separately. |
| Independent review | Separate code/protocol review caught and corrected replay normalization and capture-freezing issues before R1. Semantic grading covers the complete original and final outputs; a fresh reader checks one revised brief. These reviewers are distinct from the experimental CLI source reviewers. |
| Generated manifests | `harness-kit gen --check` passed. Plugin versions and generated metadata are unchanged in this experiment. |
| Static loading checks | Claude Code 2.1.269 validates the manifest and skills with the existing ignored `_generated` warning. Codex 0.145.0 passes manifest validation only; this does not establish runtime skill loading. Both installed versions differ from the validator's reference versions. No deep installed-skill load or trigger test is claimed. |

All measurements and repository permissions in the scenarios are fictional
fixtures. These tests do not establish real workflow security, production export
performance, account charges, future reliability, automatic skill triggering,
or an end-to-end native dialog. The reader and semantic reviews are manual
evaluation steps; the runner does not recruit or grade them automatically.

The public archive retains all complete visible draft, reviewer, and revision
responses, including process narration. It also retains the exact protocol,
both runner implementations, prompts, input contents, process outcomes,
independent reviews, and response/capture hashes. Raw CLI event streams and
host-specific command paths stay local; their hashes establish provenance.
Historical A–F evidence remains unchanged and linked from the earlier records.

## Subsequent PR review repairs

PR #67 review found two defects in commit `fd12bae`. These repairs follow the
R1/R2 experiment and do not change its archived results or runner snapshots.

| Finding | Reproduction and repair | Verification |
|---|---|---|
| CodeRabbit comment `3997886598`: literal pipes truncate a table example in `references/clarity.md` | GitHub's Markdown API rendered the fourth cell as “Three group comparisons become \`Group”. Replaced the inline code delimiters with an HTML `code` element and encoded the pipes. | The same renderer produces four cells and the complete fourth-cell text: “Three group comparisons become Group \| Changes \| Holds constant.” |
| Copilot review `5188393718`: replay accepts captures edited before preflight | Replacing a saved response with another successful, complete CLI response still reached the reviewer. Original ordinary-run manifests did not contain capture hashes. The runner now records all four writer capture hashes before review and requires an exact match at import. | Sixteen new checks failed before repair. After repair, all 104 runner tests passed in 2.11 seconds. They include rejection of valid-but-altered stdout, stderr and process metadata, missing or invalid hashes, and duplicate case records for both CLI formats. Existing successful reuse and post-preflight freezing controls also pass. |

`harness-kit gen --check` and `git diff --check` passed. No new model calls were
made for these runner and rendering repairs. The replay format now rejects
legacy manifests without original capture hashes; the evaluation README gives
the recovery procedure. A local manifest is an integrity reference, not an
authenticated record against simultaneous edits to the manifest and captures.

Only `references/clarity.md` changes among the nine F instruction files. The
current source is therefore a later revision, not the exact F snapshot used by
R1/R2. Its instruction-set fingerprint is
`e2d5b655d07e132af0d37ab9f1caff8401cba09421743058d226b1a830b9f449`,
using the same sorted-map method as F. The rendering check establishes the repaired table's displayed text;
it does not establish model behavior for this later instruction revision.
The experiment archive is unchanged, with SHA-256
`8cc28a7d52fec87014ac4979fde84fc05ad095b2156266627dd0a57ab2881538`.
