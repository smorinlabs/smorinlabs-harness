# O1: Remaining decision-communication failures

Reviewed on 2026-09-12 for draft PR #67. O1 is the behavioral-failure review
within **P48-T08: Resolve or explicitly disposition the remaining behavioral
failures before promotion; after an authorized merge, refresh stable main to
activate development placements**. Merge and activation remain outside this
run's authorization. No new project issue is needed for this audit.

The audit starts from `b5affcf`, the initial draft's final revision, called D
below. It does not treat failures from older candidates as observations on D.
The retained [initial validation record](clear-decision-communication-0.3.0.md)
now identifies those distinctions explicitly.

## Evidence and revision boundaries

The [portable evidence](../../plugins/clear-decision-communication/skills/clear-decision-communication/evals/results/decision-context-o1.json) retains exact final
responses, raw input contents, original review records, output-line provenance,
and SHA-256 hashes. It includes the sixteen historical Claude responses, the
final-D Codex case-18 control, and the five new affected-case responses. These
are selected evidence records, not a new run of the nineteen-case suite.
Historical review wording is retained verbatim; qualifications in this report
supersede any broader interpretation of that wording.
Raw JSON lives with evaluation artifacts, separate from rendered documentation;
its captured workflow expressions and other verbatim content are unchanged.

| Snapshot | What was actually tested | Status for this audit |
|---|---|---|
| A: initial implementation | Claude 1, 4, 14-19 | Older candidate; failures remain historical evidence |
| B: example and sizing repair | Selected Codex cases | No Claude results; not evidence of Claude behavior |
| C: evidence repair | Claude 1, 4, 14, 15, 18, 19, including both versions of case 18 | Latest earlier-candidate evidence for cases other than expanded 18 |
| D: approval-record repair | Expanded case 18 on Claude and Codex | Initial draft's final revision; all nine instruction files match `b5affcf` |
| E: O1 correction | Claude 18, 4, 14, 15; Codex 18 | One new response per selected case and tool; no unchanged retries |

D has source-set fingerprint
`7187f0aeef8b5e2a3465d7cfee644401eaee951d6cceb9b35f802f8f84530e0c`.
E has source-set fingerprint
`ce18c37ce57103ce3753abc426e9a2fa84d8ef4ad4208141eb404a3e79781aab`.
As in the initial record, a fingerprint hashes the sorted filename-to-SHA-256
map serialized as JSON without whitespace. All three new run directories
contain the same E source map.

The change from C to D affected only the main skill and one worked example:
it added planning-only record scope and the unknown-baseline rule. Cases 4,
14, and 15 were not rerun on D. Their new E results must not be described as
failures reproduced on D.

The original case-18 reply required current write access. The expanded reply
also explicitly requires OWNER, MEMBER, or COLLABORATOR association, with both
checks required. This audit uses the expanded input. Earlier original-input
results are not retroactively graded against that added condition. The runner,
all current scenario inputs, and grading expectations are unchanged in O1.

## Final-D case 18 and the focused correction

Independent source review confirmed two defects in D's Claude result, at
`cdc-context-claude-v030-plan-record/claude/case-18/stdout.jsonl:109`:

- For the row **Credential missing**, the response says, "The enable variable
  is absent, so the job is skipped." The design establishes skipping when an
  enable variable is absent. It does not connect credential absence to the
  value of that independent variable.
- The proposed decision record calls the permission lookup unprototyped and
  untested. The research note gives that status only to credential detection
  and missing-credential reporting. For the lookup, authentication and author
  mapping are unselected; prototype and test status are not stated.

D already repaired the prior approval-record defect. Both its response and
its record limit authority to updating design and implementation-plan documents.
Both retain the association check and current-write check. D remains an overall
failure because those successes do not repair the two source errors.

The main skill already prohibited substituting baseline conditions. However,
its representation table still demanded runtime outcomes for conditional
changes. E provides an affirmative alternative: compare stated design rules
when runtime outcomes are unknown. The main and reference tables agree.
Evidence checks now cover option consequences, table readings, and decision
records; each finding retains its own evidence status. The same check addresses
the older aggregate-result, tested-event, and interval-versus-age failures.

Independent content re-review found no contradiction or new approval gate in
the correction. Only three instruction files changed: `SKILL.md`,
`references/representation.md`, and `references/decision-record.md`.
The shared technical-communication skill, descriptions, tool grants, versions,
scenario inputs, and runner remain unchanged from the prepared PR.

## Resolutions and proposed dispositions

"Repaired in a response" means that particular output no longer makes the
claim. It is not a reliability estimate or proof that every future output will
obey the rule. A retained failure is not waived by passing its narrower criteria.

| Finding | Evidence and resolution or proposed disposition |
|---|---|
| Case 18: credential absence becomes absent enable variable | Confirmed on A, expanded C, and final D. E Claude and Codex do not make this substitution. Both use requirements prose instead of an unsupported runtime table. **Repaired in the affected E responses**; table correctness under other inputs remains unmeasured. |
| Case 18: lookup evidence becomes unprototyped/untested | Confirmed on expanded C and D. E keeps credential handling's no-prototype/no-test status separate from lookup authentication and author mapping being unselected. **Repaired in the affected E responses.** |
| Case 18: record grants implementation authority | Confirmed on expanded C. D repairs it, and both E controls retain planning-only authority. **Resolved for the tested record boundary.** No workflow mutation occurred in any simulation. |
| Case 18: unsupplied fork/credential behavior | The original-input C response introduces a platform rule and derives a definite missing-credential result without scenario evidence. **Retain as a historical failure on the superseded fixture version.** E does not repeat that platform rule, but the original input was not rerun; do not claim a same-input repair. Broader platform claims still require their own verification. |
| Case 4: aggregate benchmark becomes separate wins and exclusive coverage | C says streaming wins on both individual criteria and the benchmark scored only those criteria. E preserves the aggregate wording in its recommendation but repeats the stronger statements in its evidence and option text. **Retain as a current E failure.** No further prompt-only expansion or unchanged retry is justified by this result. |
| Case 4: unavailable benchmark figures or implementation facts | C promises to restate unavailable per-case figures and says the approaches share no implementation work. E claims the figures are in Tuesday's brief, whose contents were not supplied, and that neither approach exists. **Retain as a current source-fidelity limitation.** No numeric measurements were fabricated; the defect is unsupported evidence availability and project state. |
| Case 4: invented separate schema approval | A invents a mandatory later approval. C removes it; E retains correct stale-ID handling and starts no implementation. **Historical repair observed on C**, with authorization behavior also passing on E; no D test is claimed. |
| Case 14: documented PR update trigger becomes a reproduced fixture | A and C label opening or updating a PR as tested. The status document supports both triggers, but the fixture exercises opening. E's reproduced table says opening only. **Specific evidence-status defect repaired in E.** E omits the documented update trigger elsewhere, so trigger coverage remains incomplete. |
| Case 14: assistant described as the only repository writer | C blurs review comments, branch creation, and credential authority. E drops the sole-writer statement and preserves unknown credential scope. **Specific precision defect repaired in E.** No result establishes extra privileges in the fictional system. |
| Case 14: mandatory manual cleanup | A and C turn remaining artifacts into a cleanup requirement. E says disabling does not remove existing comments or branches. **Repaired in E.** Cleanup would be conditional on wanting those artifacts removed. |
| Case 14: unknown author restrictions and unsupported cost comparison | E says the main cost sits with reviews, without comparative traffic or cost evidence. It reasons from unreported author restrictions to reviews being unbounded by maintainer activity, then labels those restrictions unverified. **Retain as a current E failure.** The fixture proves neither unrestricted reviews nor the relative operating cost. |
| Case 15: interval becomes maximum data age | A and C promise a maximum age unsupported by response latency, source freshness, or failures. E explicitly distinguishes the request interval from a freshness guarantee. **Specific guarantee repaired in E.** The observed fifty-second delay is one fixture result. |
| Case 15: missing UI warning inferred from retained data | C says neither option informs the supervisor that updating stopped. E no longer makes that inference. **Specific claim removed in E.** Warning behavior remains unknown. |
| Case 15: reverting has no lasting effects | C says nothing survives timer removal and includes unsupported supervisor-state claims. E expressly retains already-served requests and describes the narrower request-only change. **Retain a minor qualification issue in E**, whose assertion of no stored data changes still exceeds direct fixture evidence. Proposed disposition: bound the rollback statement to the refresh module and distinguish observed effects from unverified persistent effects. No actual data-writing or rollback defect was demonstrated. |
| Case 15: five-minute arithmetic | A says a five-minute interval produces one twelfth of a sixty-second interval's requests; the ratio is one fifth. C removes the unsupported extra option; E does not reintroduce it. **Historical error removed**, not a new arithmetic test or proof of general numerical accuracy. |
| Case 1: invented exact patch | A presents placeholder patch content as verified. C removes the artifact and passes. **Retain the C repair as historical evidence.** No D or E run was needed for O1; the latest minor single-link/one-line wording issue remains noted in that review. |
| Case 19: unknown safeguards become absent; planning becomes implementation | A makes those source and scope errors. C preserves unknowns, stays in planning scope, and passes. **Retain the C repair as historical evidence.** No D or E test of case 19 is claimed. |

The proposed disposition for the remaining E failures is to retain them as
explicit limitations in draft review. Consequential generated briefs still
need comparison against their sources. Adding more copies of an already
explicit instruction is not supported by these runs. A separately measured
change to how source claims are checked is a possible follow-up, drafted below;
it is not implemented or asserted effective here.

Communication limitations remain separate: Claude exposes sizing/tool/process
narration, sometimes requests routine design information, and can omit a known
trigger or shorten page-entry-plus-manual refresh to "manual only." The
simulation asks for a proposed reply and immediate next action, which may
contribute to the wrapper text; that is an inference, not a demonstrated cause.
These limitations are retained, not reclassified as successful ordinary delivery.

Case 15 also describes the final observation as two minutes after the update,
although the supplied timestamps are t=10 seconds and t=120 seconds, a gap of
110 seconds. Its fifty-second prototype delay is correct. The table's page-load
details are reconstructed from documented page-entry behavior, not literal
fixture observations. These are retained as minor accuracy and provenance
limits, not silently treated as measurements. The specific maximum-age and
missing-warning claims that caused the earlier failures are absent in E.

The new Claude case-18 response also says credential permissions cannot be
verified without a real-repository run. The supplied sources do not establish
that necessity. This remains a minor qualification issue: it does not block
planning or alter the required behavior. Proposed disposition: describe any
later verification method as a proposal until its necessity is established.
No additional credential action is authorized by this audit.

## Independent reader and validation limits

| New run | Semantic result | What the result establishes |
|---|---|---|
| `cdc-o1-claude-case18`, case 18 | Pass, 5/5 targeted criteria | Requirements and planning-only authority preserved; baseline substitution and merged research statuses absent; minor verification-method assertion retained |
| `cdc-o1-codex-case18`, case 18 | Pass, 5/5 targeted criteria | Approval boundary and both author checks preserved; no material source error found |
| `cdc-o1-claude-older-cases`, case 4 | Fail overall | Correct stale-ID handling does not repair unsupported benchmark and evidence-availability claims |
| `cdc-o1-claude-older-cases`, case 14 | Fail overall | Specific trigger/cleanup/writer defects repaired; unsupported relative cost and unknown-to-absence reasoning remain |
| `cdc-o1-claude-older-cases`, case 15 | Pass with minor limits | Freshness guarantee and UI-warning inference removed; rollback, timing, and fixture-description qualifications retained |

These five selected responses yield three overall passes and two failures.
They do not revise the initial record's twenty-eight-response totals or measure
the success rate of the whole suite. All outputs were independently graded
against raw inputs and reviewed locally before disposition.

A fresh reader saw only the complete E Claude case-18 response and six neutral
questions. Their [verbatim answers and source comparison](decision-context-o1/reader-review.md)
correctly reconstruct the work, current state, approval scope, both author
checks, and distinct research gaps. They also repeat the unsupported assertion
about needing a real-repository run. Comprehension therefore does not validate
that additional claim. Neither the reader nor the model executed the scenario.

All five new model processes completed. Semantic grading examines full outputs
and source facts, not CLI exit status. The tests do not establish real GitHub
security, automatic triggering, native dialog rendering, live multi-turn repair,
or reliability across future runs. The fixed scenario follow-ups remain a
single fresh-session response each. No comparison with version 0.2.0 was run.

| Quality layer | Result and scope |
|---|---|
| Content | Pass: independent review of the focused instruction diff; no new tool grant, trigger change, or owner gate |
| Documentation | Skill page and README updated; historical snapshot wording corrected; this audit and portable evidence retained |
| Generation | `harness-kit gen --check` passes; versions remain the already prepared 0.3.0 and 0.2.3 |
| Static loading | Claude validation passes with the existing ignored `_generated` warning; Codex manifest validation passes. Codex static mode does not validate skill bodies; the prior isolated-loading evidence remains in the initial record |
| Behavioral checks | The five affected-case results above; same runner and scenario inputs, no full-suite rerun |
| Runner regression | Not rerun: no runner, schema, or scenario change. The prior 21 passing tests are historical evidence, not new E results |
| Activation | Both tools' two existing skill placements still resolve to stable main; no placement or main-checkout change |

## P48-T08 closeout draft

The following is draft follow-up text, not authorization to perform promotion
or activation:

> O1's review and disposition audit is complete within P48-T08. Each remaining
> historical failure has a revision-specific resolution or proposed disposition.
> Preserve the non-passing E responses and their source qualifications. PR #67
> remains draft and the installed development placements remain on stable main.
>
> P48-T08 stays open for disposition review and any later authorized promotion,
> merge, and stable-main refresh. Do not infer those approvals from completing
> O1. When that work is authorized, refresh PR head/reviews/checks, complete the
> agreed promotion and merge process, and only then refresh stable main and
> verify both tools' placement targets before marking activation complete.

If the remaining failures need an engineering follow-up beyond this audit,
the proposed draft is:

> Investigate a separate source-claim review step for generated decision briefs.
> Compare it with E on the retained benchmark, workflow, and refresh cases,
> using the same raw inputs and independent grading. Include a control where
> individual metrics, author restrictions, or persistent effects are actually
> established, so the check does not replace supported facts with uncertainty.
> Report both corrected unsupported claims and lost supported detail. A proposed
> checker is not a proven repair, and this draft does not authorize building it.
