# Decision source-check and measurement review

Prepared on 2026-09-12 from the initial O1 follow-up commit `c3d6ebc`.
The owner requested exact before/after text, then testing, and required reported
results to identify their measured assets, metrics, absolute values, and baselines.
Both changes below were shown before editing and were independently reviewed.
They are changes to `clear-decision-communication/SKILL.md`; no installed
placement or shared technical-communication skill changes in this follow-up.

This work continues the remaining-failure review within P48-T08. The earlier
[O1 audit](clear-decision-communication-0.3.0-o1.md) remains historical evidence;
its candidate E outcomes are not relabeled as outcomes of this revision.

**Outcome:** eight candidate F responses produced three overall passes and
five failures; one pass carries minor precision and test-design qualifications.
Both retained Claude failures remain. The new measurement controls show useful
results, but this instruction-only source check is not an established repair
for whole-response source fidelity. PR #67 remains draft; P48-T08 remains open.

**Subsequent work:** the owner approved and the agent executed the
[separate-review experiment](clear-decision-communication-source-review-experiment.md).
It reuses these exact F drafts and leaves the skill instructions unchanged.
The proposal and results below remain the historical F record; the later
experiment records its own implementations, attempts, and independent grades.

## Source verification

Before:

```text
6. **Pre-send check.** Send only when every line holds:
```

After:

```text
6. **Check the completed draft against its sources.** Before the reader checks
   below, make a separate verification pass over the recommendation, comparison,
   option consequences, summary, and proposed decision record. Reopen the
   supporting passages or results rather than relying on the draft's wording.
   For each decision-critical claim, match the exact asset, source statement,
   conditions, and evidence status. A source that supports only part of a claim
   does not support the whole sentence. Remove the unsupported part, narrow it,
   or state the unresolved fact. Mark calculations as derived and retain their
   input values. Check the revised draft for contradictions, then apply every
   reader check below. Include relevant sources and limits in the brief without
   narrating this verification process:
```

Reason: the existing rules already required evidence fidelity. The retained
failures appeared in recommendations and option consequences despite separate
evidence paragraphs. This instruction calls for checking the completed draft,
including those consequential claims, against the supporting source passages.
It is a proposed process improvement; testing must establish whether the
generated response actually respects the evidence boundary.

## Measurements and comparisons

Before:

```text
Never edit text the reader must type, match, or search. Give every number its
unit, its date, and its source.
```

After:

```text
Never edit text the reader must type, match, or search. For each reported
measurement, identify the exact asset measured and its role, the metric,
statistic or denominator, unit, source, and relevant revision/date and conditions.
For a comparison, identify both baseline and candidate. When reporting a
percentage improvement, include the percentage, both absolute values, and the
absolute difference when the sources supply them or support their calculation.
Say whether the percentage is quoted from the source or calculated from supplied
values. Preserve the direction of change; distinguish relative percent change
from percentage-point change. If a baseline or absolute value is missing, state
the gap instead of inventing it or presenting the percentage as independently
checked. Preserve exact quotations and point to the supporting source.
```

Reason: a percentage without a measured asset, baseline, and absolute values
can be arithmetically correct but unusable. The replacement distinguishes source
measurements, quoted changes, calculated changes, and missing values. It also
prevents a change in percentage points from being reported as relative percent
change. Missing data must remain a stated gap, not a fabricated example passed
off as a measurement.

## Evaluation scope

The source-check pass is an instruction to the generating agent. It is not an
independent checker process, and an output claiming to have checked its sources
is not proof that the check occurred. Review the final claims against the raw
inputs. Preserve every attempt and separate process completion from behavior.

The retained Claude cases 4 and 14 keep their original inputs. New controls
cover fully specified measurement comparisons, a reported percentage without
absolute values, and explicitly supported workflow restrictions and usage.

## Revision and input control

| Revision | Meaning | Instruction-set SHA-256 |
|---|---|---|
| E | O1 baseline, committed at `c3d6ebc` | `ce18c37ce57103ce3753abc426e9a2fa84d8ef4ad4208141eb404a3e79781aab` |
| F | The two exact `SKILL.md` edits above | `da9f3c7ae8b83962dfccfca10f73f8f554227f70bfebd322995a88a4f5ef4d57` |

Each fingerprint hashes the sorted filename-to-SHA-256 map of the nine
instruction files. Only `SKILL.md` differs between E and F; the eight reference
files are unchanged. Each F run freezes that same instruction set. Evaluation
cases, expectations, earlier results, and review documents are excluded from
the model's instruction snapshot.

The first nineteen scenario objects are unchanged from the committed
`evals.json`. Cases 4 and 14 also retain identical staged raw inputs and prompts
between E and F. Cases 20–22 append fictional raw artifacts and separate grader
expectations. Their measurements describe test scenarios, not real export or
workflow performance. No same-case E results exist for these three new controls,
so their outcomes cannot establish a measured improvement over E.

## Retained failure comparison

| Case | Candidate E result | Candidate F result | Evidence-backed disposition |
|---|---|---|---|
| Claude 4: stale export-approach answer | Fail: aggregate preference became separate metric wins; missing figures were claimed to exist in another brief. | Fail: still says streaming was favored “on both agreed criteria,” including in the verified-evidence paragraph. Now acknowledges the measured values are absent and drops the invented location. | The evidence-availability defect is absent in F's observed response. The per-metric overclaim remains unresolved. Say the benchmark favored streaming under the agreed criteria; do not claim each metric improved without its measurements. |
| Claude 14: optional repository automation | Fail: asserts a cost ranking without usage data and makes unsupported coverage claims. | Fail: removes the unsupported cost ranking but promises “no workflow can write a branch.” Effective credential permissions remain explicitly unverified. It also retains “every pull request” coverage and calls the author restriction the “only fact” separating the options despite known behavior and invocation differences. | The unsupported cost ranking is absent in F's observed response. The capability and coverage claims remain unresolved. State the observed review-comment behavior and disabled assistant separately from unverified effective write permissions. |

Both F responses pass their original targeted criteria: three of three for
case 4 and five of five for case 14. Both fail the whole-response source-fidelity
review. Narrow criterion passes do not repair contradictory or unsupported
claims elsewhere in the decision brief.

Each trace reads each supplied project input once and then reads or searches
skill references. Neither shows a separate reopening of project passages. This
does not establish whether an internal review happened, but it does not
demonstrate the new source-reopening instruction being followed. More
importantly, the final consequential claims remain unsupported.

## New measurement controls

| Case | Claude on F | Codex on F | Finding and proposed disposition |
|---|---|---|---|
| 20: two export assets, opposing latency and compute changes | Fail; 4/5 original criteria | Pass; 5/5 | Both preserve the measured values and calculations. Claude then promises ongoing exact cost increases and says rollback “restores the earlier latency and cost.” Retain the failure: measurements under one benchmark do not guarantee production or rollback performance. Codex preserves the tested conditions and production uncertainty. |
| 21: reported reduction without absolute measurements | Pass with qualifications; 4/5 original literal criteria | Fail; 4/5 | Neither invents observed baseline or candidate timings. Claude names the asset and keeps budget compliance unresolved, but gives a rounded threshold as an exact boundary and calls the summary “one measurement.” Codex keeps the missing values unknown but omits `web/search/suggestions.ts`, the module that requests and displays catalog suggestions. Restore that exact asset and role. The original symbolic-only grading clause was also too restrictive; see the amendment below. |
| 22: documented author gates and measured workflow usage | Fail; 4/5 original criteria | Pass; 5/5 | Both preserve the documented author restrictions and correctly calculate review/assistant shares as 40% and 60% of 200 allowance units. Claude turns 120 units across 10 assistant invocations into “each assistant invocation consumed 12.0 units.” That establishes an average, not a constant per-invocation amount. Its 2.5-times total is numerically equivalent to a 150% increase, but omits the requested percentage representation. Codex retains the accounting comparison and avoids a future-consumption guarantee. |

The eight F responses comprise the two retained cases and six new-control
responses. All eight processes completed with exit code zero. Independent
semantic review and local source comparison, not process status, produced the
three-pass/five-failure result. These observations do not estimate a success
rate for the twenty-two-case suite or future sessions. No unchanged case was
retried to obtain a pass. No additional skill instructions were added after F
was frozen.

### A measurement that stayed concrete

In the fictional Ledger Exports benchmark `EX-204`, run on 2026-09-11, the
background-worker baseline is revision `7ab91c2` and the direct-streaming
candidate is `8bc02d3`. The successful Codex case 20 response retains the source
measurements and labels the differences and percentages as calculations:

| Exact measured asset and role | p95 completion latency, baseline to candidate | Compute, baseline to candidate, USD per 1,000 successful exports |
|---|---|---|
| `services/exports/orders_csv.py`: customer-order CSV exports | 2,400 to 2,160 ms; 240 ms lower, a 10% reduction from 2,400 ms | $10.00 to $12.00; $2.00 higher, a 20% increase from $10.00 |
| `services/exports/stock_csv.py`: warehouse-stock CSV exports | 1,200 to 1,080 ms; 120 ms lower, a 10% reduction from 1,200 ms | $5.00 to $6.00; $1.00 higher, a 20% increase from $5.00 |

Here p95 is the 95th-percentile completion time from request acceptance through
delivery of the last byte. Each source row covers 1,000 successful exports,
four concurrent clients, and warm processes, with identical infrastructure and
matching input data across the baseline and candidate: `ORD-50K` for orders and
`STK-10K` for stock. The figures support faster exports with higher measured
compute charges under those conditions, not improvement on every metric.

The [fresh reader's recorded answers](decision-source-check/reader-review.md)
recover both exact assets, revisions, absolute values, directions, conditions,
and the owner decision. The brief omits the supplied project name, Ledger
Exports, and handling of an added condition. Those omissions did not prevent
the reader from identifying the concrete choice. This is one reader check;
there is no corresponding E measurement of comprehension for this case.

### Grading amendment, kept separate from model output

The executed case 21 originally included this grading sentence:

> An optional candidate = 0.9 times baseline calculation must remain symbolic.

Independent semantic and content reviews found that sentence too restrictive.
The skill permits calculations from supplied values with their assumptions
stated. A conditional threshold derived from a 150 ms budget and a reported
10% reduction can be useful without pretending to know measured timings.

The future grading sentence is now:

> Clearly labeled conditional calculations may use the supplied inputs and stated assumptions; they must not be presented as observed measurements or proof that the candidate meets the budget.

The archived executed reviews retain the original wording. Claude case 21 has
four of five original criteria marked met and an overall qualified pass. Its
substantive conclusion remains correct: absolute results are still required to
establish compliance. Its numerical limit needs a precision repair: under an
exact 10% reduction, the threshold is `150 / 0.90` ms, approximately
166.6667 ms. Do not use the rounded value 166.7 ms as an exact inclusive
pass boundary. The claim of “one measurement” should instead name the single
supplied summary without inferring a count of measurements.

Codex case 21's explicitly hypothetical 160-to-144 ms and 180-to-162 ms examples
are not fabricated measurements. Its failure is the omitted asset identity.
The grader amendment changes no model input, instruction, response, or recorded
verdict. It required metadata/schema verification, not another model call.

## Evidence and verification

[Portable evidence](../../plugins/clear-decision-communication/skills/clear-decision-communication/evals/results/decision-source-check.json)
retains ten complete responses: eight F responses plus the two unchanged E
comparison records. It includes exact prompts, deduplicated raw inputs, source
maps and fingerprints, CLI version output, process outcomes, response provenance,
stdout hashes, and independent reviews. Earlier E records are copied unchanged
from the O1 archive. Full final messages are retained, including process chatter;
the polished inner brief is not substituted for the full visible result.

| Check | Result and coverage |
|---|---|
| Content | Independent review approved the two exact source edits. Follow-up review found and corrected the overrestrictive grading clause and an evaluation command that omitted the new cases. Frontmatter, descriptions, tool grants, and plugin versions are unchanged in this follow-up. |
| Runner regression | 21 tests passed in 2.14 seconds after the grading amendment. The runner implementation is unchanged; the existing scenario-count and finding-coverage checks now include 22 cases and the two new finding identifiers. |
| Generated manifests | `harness-kit gen --check` passed. |
| Static loading: Claude | Manifest and skill checks ran with no errors; the existing `_generated` manifest-field warning remains. Installed CLI 2.1.269 differs from the verifier's recorded compatibility version. |
| Static loading: Codex | Manifest check passed on CLI 0.145.0; this static mode does not validate skills. The verifier also reports version drift. |
| Session-backed installed loading | Not repeated in this follow-up. Earlier isolated loading remains historical evidence. The F scenarios explicitly read the supplied skill snapshot; they do not test installed discovery or activation. |
| Source and input control | All three run manifests match F's nine instruction files. Exact before/after blocks match committed E and current F. Original nineteen scenario objects, retained-case prompts and raw inputs, and copied E records are unchanged. |
| Reader comprehension | One fresh-reader check of Codex case 20, with exact answers recorded before source comparison. |

## P48-T08 disposition and next-work draft

The requested text changes, affected-case tests, independent review, and failure
dispositions are complete. They belong to P48-T08's behavioral review. They do
not complete promotion, merge, or activation.

Proposed disposition: retain F as a reviewed draft candidate with explicit
limitations. The original failures are unresolved, and the new controls expose
related expansions from measured aggregates into unsupported per-item or
production claims. Do not claim that an instruction to self-check reliably
prevents those failures. Do not expand the shared technical-communication skill
on the assumption that this approach is proven.

Draft follow-up task within P48-T08:

> Evaluate a separately executed source-comparison review of the completed
> decision brief before delivery. Retain the draft, source passages, reviewer
> findings, and revised brief as separate artifacts. Use the retained aggregate
> benchmark and workflow cases plus the three measurement controls. Check whether
> the review removes unsupported metric wins, capability limits, production
> guarantees, and per-invocation constants while preserving supported asset
> names, author checks, values, and calculations. Compare the final revised brief
> against the same raw sources with independent grading. Do not substitute a
> claim that verification occurred for evidence that the claims are supported.

That integrated review process has not been implemented or tested here. The
independent reviews in this evaluation caught failures, but did not exercise an
automatic revise-and-deliver process. Further implementation remains proposed.
Keep PR #67 draft and both tools' development placements on stable main. Any
later promotion, merge, or activation requires the corresponding authorization.
