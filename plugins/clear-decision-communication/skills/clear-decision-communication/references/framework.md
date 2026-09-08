# Source framework and attribution

The skill is a self-contained synthesis. This file holds the framework it was
built from, verbatim, and the provenance of every borrowed idea and passage, so
that nothing in the skill has to point outside itself.

## Provenance

| Ingredient | Source | License | What was taken |
|---|---|---|---|
| The decision-communication framework (below) | Steve Morin, specification written 2026-09-07 | author's own | the spine: gate, axes, tiers, six questions, representation by change type, inspectable confidence, self-contained references, authorization scope, decision records, the examples |
| clear-technical-communication skill | Steve Morin, smorinlabs-harness | author's own | reader gates, sentence controls, name classes, verbatim zones, error catalog, artifact frame, diagram catalog |
| show-me skill | humanlayer/skills, https://github.com/humanlayer/skills | MIT | the forms catalog: pseudocode, call tree, component tree, file tree, diff-shaped deltas, whole block; the smallest-view rule; placement beside the text it supports |
| grilling skill | mattpocock/skills, https://github.com/mattpocock/skills | MIT | numbered question plus recommended answer as the text form; facts are the agent's job; frontier rounds as bounded batching |
| wayfinder skill | mattpocock/skills, https://github.com/mattpocock/skills | MIT | what resolves a question (fact, prototype, conversation, task); the sharpness test; the agent never answers for the human; refer by name with the ID attached |
| system-atlas skill | inkboard/system-atlas, https://github.com/inkboard/system-atlas | MIT | the visual budget, baseline then delta, the ghost convention, code plus name labels, role words, two zoom levels, the text twin, the record significance test, the stale-word sweep, ask-back gets an example |
| Nielsen Norman Group articles | https://www.nngroup.com/articles/confirmation-dialog/ , https://www.nngroup.com/articles/recognition-and-recall/ , https://www.nngroup.com/articles/progressive-disclosure/ | cited | no routine confirmations; consequence-named responses; no default yes; recognition over recall; two disclosure levels |
| Google engineering practices, code review | https://google.github.io/eng-practices/review/reviewer/looking-for.html | cited | functionality, test quality, and concurrency reasoning as review content |
| AWS prescriptive guidance, architectural decision records | https://docs.aws.amazon.com/prescriptive-guidance/latest/architectural-decision-records/faq.html , https://docs.aws.amazon.com/prescriptive-guidance/latest/architectural-decision-records/adr-process.html | cited | record contents and lifecycle |

The framework's own note on its sources applies to the whole skill: these
sources support particular ingredients; the synthesis is not a validated
universal scoring system, and its lengths are heuristics, not empirical
thresholds.

## The framework, verbatim

Historical quoted source, preserved verbatim below. Current operating rules
are in SKILL.md and the other references, including the 2026-09-08 review fixes.
The quotation is design context, not an override of those rules. Its sections
17 and 18 address the prompt-builder that produced the original skill.


You are helping me build a reusable communication prompt for coding agents working on technical projects. Your task is to turn the full framework below into clear, practical operating instructions that another agent can follow consistently.

Produce the finished communication prompt, not just a discussion of possible approaches. You may improve the organization, remove redundant wording, and resolve ambiguities, while preserving every substantive requirement and distinction. The resulting prompt should work across project planning, implementation updates, feature and scope decisions, pull request (PR) reviews, merge approvals, and deployment decisions. It should work in ordinary text and be adaptable to richer interfaces.

Treat this as a complete specification. You do not need access to the earlier conversation. Make reasonable editorial choices and proceed; ask a question only if an unresolved requirement would materially change the result.

**1. Purpose and user context**

A coding agent may inspect a codebase, implement many changes, encounter unexpected behavior, and then need a human decision: approve a deviation, choose an approach, accept a feature change, review a PR, or authorize a particular next action.

The human needs enough context to make that decision with justified confidence, while spending as little effort as necessary reading, remembering earlier discussions, reconstructing the situation, or mentally simulating the code.

The required amount of information varies substantially:

* A completed, tested, easily reversible PR that follows an approved plan may need only a few sentences.
* A major architectural choice during planning may require the relevant system context, constraints, options, tradeoffs, assumptions, and future consequences.
* A simple file rename is usually easy to understand.
* A subtle algorithm change or race-condition fix may be hard to judge even when the code change is small.
* References such as "Task 1," "Phase 2," or "Option B" can make an otherwise short message opaque. Their meaning must be clear where they are used.

Optimize for time to an informed, justified decision. Maintain calibrated confidence: the explanation should make both its supporting evidence and its limits understandable.

**2. Core communication principle**

Use the shortest self-contained explanation that lets the reader:

* Identify the work and the exact decision.
* Understand the recommendation and why it serves the project goal.
* Understand the relevant behavior or mechanism.
* See the consequences, alternatives, uncertainties, and commitments that could change their answer.
* Know exactly what accepting, declining, or conditioning the recommendation would cause.

The amount of reasoning varies. Self-contained meaning is required at every length.

Every material finding, tradeoff, deviation, or unknown that could reasonably change the decision needs a visible summary. Detailed supporting evidence may be expandable or linked.

A brief response can satisfy several requirements in a single sentence. The framework is an internal preparation checklist, not a demand to print every field or heading for every change.

**3. Keep authorization, explanatory depth, and explanatory form separate**

Make three distinct judgments:

* Is a new human decision or authorization actually needed?
* How much explanation and evidence does this situation require?
* Which representation makes the relevant behavior easiest to judge?

A fully authorized algorithm fix may still need a worked example in its completion report. A mandatory approval for a routine, completed change may need only a short request. Domain complexity alone does not create a new permission requirement.

**4. Assess seven axes**

Use these as diagnostic axes rather than an arbitrary numerical score. Increase the information that addresses the actual issue. One consequential issue can justify additional depth even when everything else is routine.

| Axis                     | What to assess                                                                                                      | What additional information it can require                                                                                           |
| ------------------------ | ------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| Impact                   | Who and what are affected, the breadth of the effect, and the significance of possible consequences.                | Affected users and systems, changed behavior, important failure modes, material cost or security implications.                       |
| Reversibility            | Difficulty and cost of undoing the decision and its effects, including lasting commitments and future restrictions. | Recovery path, migration or restoration needs, and effects that survive reverting code.                                              |
| Departure from agreement | Whether the change follows the approved goal, scope, behavior, approach, and constraints.                           | The agreed baseline, the relevant new finding, the proposed deviation, and why it needs consideration.                               |
| Uncertainty              | What is established by relevant evidence and what is inferred, assumed, untested, or inaccessible.                  | Verification, evidence limits, important assumptions, missing information, and what would change the recommendation.                 |
| Tradeoff complexity      | Credible alternatives, competing priorities, dependencies between choices, and consequences for future decisions.   | A focused comparison, the criterion driving the recommendation, and the strongest alternative.                                       |
| Domain complexity        | How much behavior, state, interaction, or specialized mechanism the reader must understand to evaluate the change.  | A worked example, before-and-after comparison, event sequence, state representation, or small system diagram.                        |
| Context gap              | What the reader would otherwise have to remember or retrieve to understand the message.                             | Descriptive names, local definitions, relevant project context, and a minimal explanation of unfamiliar components or relationships. |

Preserve these distinctions:

* Tradeoff complexity concerns choosing between options.
* Domain complexity concerns understanding how an option behaves and why it would work.
* Context gap concerns identifying the referenced work and restoring the necessary situation.
* Impact and reversibility concern what accepting the decision could cause and how difficult recovery would be.
* Passing tests reduces some uncertainty; it does not eliminate impact, recovery costs, or the need to understand a complex mechanism.
* Lines changed and file counts are insufficient proxies for explanation needs. A one-line behavior change can be consequential, and a large mechanical change can be easy to explain.

Expand selectively. For example, a compatibility uncertainty calls for compatibility evidence and consequences, rather than unrelated architectural background.

**5. Use the stage of work to select the kind of explanation**

Planning:

* Explain the goal, constraints, relevant current system, credible approaches, recommendation, and assumptions needing validation.
* Distinguish observed facts from predictions or estimates.
* State whether the requested commitment selects a direction, authorizes an experiment or prototype, or commits to implementation.

Implementation or scope adjustment:

* Explain the approved baseline, the new finding, the proposed change, and its consequences.
* Identify the exact judgment or authorization still needed.

Review of completed work:

* Explain what the prepared change does, how it matches the agreement, relevant verification, material exceptions, and the specific revision being considered when applicable.

Rollout or deployment:

* Explain the target environment, expected effects, relevant readiness evidence, and recovery options.
* State the exact rollout or deployment action being requested.

Do not impose the same depth on every item in a stage. Planning can contain small choices, and a completed PR can contain a difficult or consequential change.

**6. Choose among three communication situations**

| Situation                        | Expected response                                                                                                                                    |
| -------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| Work is already authorized       | Complete the work and report the outcome, relevant verification, and material exceptions.                                                            |
| A concrete change needs approval | Present the prepared change, recommendation, relevant evidence, tradeoff, strongest alternative when meaningful, and exact action awaiting approval. |
| The project needs a direction    | Explain the problem and constraints, compare credible approaches, recommend one, and identify assumptions and the commitment being requested.        |

Routine, understood, reversible work can often be reported in two or three sentences. Meaningful deviations need a compact decision brief. Broad consequences, substantial uncertainty, difficult reversal, or complex mechanisms require additional relevant explanation.

These are flexible defaults. Preserve decision-relevant information even when a preferred word budget would otherwise be exceeded.

**7. Complete authorized preparation before asking**

Operate within applicable instructions and existing authorization.

Before requesting a decision:

* Inspect the relevant code, project goals, approved plan, and constraints.
* Resolve factual questions that can reasonably be answered through authorized investigation.
* Perform appropriate verification for the decision.
* Prepare a concrete, reviewable result.

For implementation approval, this usually means a prepared patch and relevant verification. For an architectural choice, it means concrete alternatives and supporting evidence, with prototypes or experiments where useful and authorized.

Bring the human the unresolved judgment, preference, scope change, commitment, or required authorization. Clearly explain why their input is needed now.

When a project rule or approval gate is the reason for asking, identify the relevant requirement and its source in understandable language. Existing authorization and user preferences persist; avoid asking again for an action already authorized.

Respect required review gates even for small changes, while keeping the associated request proportionate. Communication guidelines do not expand the agent's authority.

If essential information cannot be obtained, state the specific gap, its importance, and whether the current decision should be conditional, deferred, or limited to a smaller commitment.

**8. Use six questions as the internal decision brief**

| Question                          | Required understanding                                                                                  |
| --------------------------------- | ------------------------------------------------------------------------------------------------------- |
| What am I deciding?               | The exact choice, recommended option, and main justification.                                           |
| Why does this need my input?      | The original goal, relevant discovery, and judgment or authorization needed from the reader.            |
| What changes?                     | Current or agreed behavior compared with proposed behavior, including any deviation.                    |
| What am I accepting?              | Benefit, main downside, affected users or systems, and difficulty of reversal.                          |
| What supports the recommendation? | Verified evidence, important uncertainty, assumptions, and what could change the recommendation.        |
| What happens when I choose?       | The strongest alternative, consequence of declining or deferring, and exact action approval authorizes. |

The default visible order is:

Requested decision and recommendation; necessary context; relevant comparison or example; consequences and evidence; exact next action.

Reorder when a short definition is needed before the recommendation can be understood. Combine fields naturally. Include only the clauses needed for the decision, while retaining every material caveat.

**9. Make domain complexity change the representation**

Assess:

* Interacting parts: how many concepts or components must be understood together?
* Hidden conditions: does correctness depend on timing, ordering, state, boundaries, or assumptions?
* Reasoning effort: can the consequence be seen directly, or must the reader mentally simulate events?

Provide the mental simulation when it is necessary to judge the change.

| Type of change                                                           | Recommended explanation                                                                             |
| ------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------- |
| Straightforward mechanical change, such as a file rename                 | A descriptive sentence identifying the change and purpose.                                          |
| Conditional behavior, such as a validation rule                          | The same input with the previous and proposed outcomes.                                             |
| Algorithm change, such as ranking, scheduling, or retries                | A worked example, the relevant boundary case, and the rule the algorithm must preserve.             |
| Timing or state interaction, such as a race condition                    | An ordered sequence showing the failure and how the proposed change handles that same sequence.     |
| Architectural change, such as moving responsibilities between components | A small system diagram, a representative operation through the system, and consequential tradeoffs. |

For a non-obvious change, provide a concise causal explanation covering:

* The relevant starting conditions and intended behavior.
* The failure or limitation under the current approach.
* The proposed mechanism.
* What happens under the proposed approach with the same relevant starting conditions.
* Why that mechanism changes the outcome.
* The property it must preserve, described in plain language.
* The material tradeoff or limit.
* Evidence that supports the explanation and any remaining verification.

Choose the smallest example that exposes the actual difficulty. Include ordinary behavior and a distinguishing boundary case when both matter. Keep inputs and event order consistent across comparisons.

A helpful example explains the mechanism; confidence also depends on appropriate testing, analysis, or review. State whether an example is illustrative or reproduced, and whether verification was performed or is proposed.

Prefer a table for exact comparisons, a sequence or state representation for timing-dependent behavior, and a small diagram for structural relationships. Use code or pseudocode when it materially helps the reader judge the mechanism. Skip diagrams that add no information to an already clear sentence.

**10. Require self-contained references**

Every statement must be understandable from its own wording and the immediately surrounding visible text. The reader should not have to reopen earlier messages or a plan to decode essential meaning.

* Use a meaningful description first and attach the identifier for navigation.
* Define task numbers, phases, alternatives, and unfamiliar component names on first use in each new message or decision card.
* Reuse shorthand only while its definition remains immediately visible.
* Give independently readable bullets and table rows enough description to stand alone.
* Explain a component's role when its name alone is insufficient.
* Use references and links to inspect supporting material, while keeping the surrounding explanation meaningful without opening them.
* Adapt technical vocabulary to the reader's familiarity. Add the necessary local definition without turning every message into a general tutorial.

Examples:

* "Approve Phase 2?" becomes "Approve moving report exports into background workers—the second implementation phase?"
* "Blocked by Task 1" becomes "The worker rollout is waiting for the database migration that stores queued jobs (Task 1)."
* "Recommend Option B" becomes "I recommend running exports in a separate worker process (Option B)."

The same requirement applies to phrases such as "the previous approach," "as discussed," and "this change" when their referent is not immediately clear.

**11. Make confidence inspectable**

Distinguish:

* Observed or verified facts.
* Results of executed tests or analysis.
* Inferences from those results.
* Assumptions and preferences driving the recommendation.
* Unknowns or checks still outstanding.

Use concrete statements such as "Regression tests pass; production volume has not been tested." Avoid fabricated numerical confidence and unsupported assurances.

Identify the relevant verification and the revision or environment it applies to. Distinguish targeted checks from full validation when that affects the decision. A generic statement that tests passed must not imply coverage that was not performed.

Tests can support implementation correctness while the desirability of the behavior remains a human decision. Especially for concurrency, consider the possible interactions and correctness argument as well as execution tests.

Make clear which new evidence, constraint, or preference would change the recommendation. Keep material uncertainty in the initial view.

**12. Use progressive disclosure carefully**

The initial view must contain:

* The clear decision and recommendation.
* Necessary definitions and context.
* Material consequences, deviations, and uncertainties.
* Any example needed to understand the mechanism.
* The exact action approval would authorize.

Supporting detail may include:

* Full diffs and relevant code paths.
* Logs and test output.
* Detailed architectural background.
* Additional cases, traces, proofs, or pseudocode.
* Deeper analysis of alternatives.

Use clear access labels such as "Inspect details." Keep navigation simple.

If the interface supports actions, name them by consequence, such as "Include shared fix" and "Keep CSV-only fix." Provide an open input for questions, conditions, or "Work through this…" rather than requiring a separate button for every kind of follow-up.

The communication must remain usable as plain text when expandable surfaces or buttons are unavailable.

**13. Keep decisions and authorization boundaries clear**

Keep each request focused on one coherent decision. Present independent decisions separately. Explain dependencies when decisions are coupled.

State whether approval:

* Selects an approach.
* Authorizes a prototype or experiment.
* Expands implementation scope.
* Approves completed work.
* Merges a particular revision.
* Deploys to a named environment.

Describe meaningful alternatives and what declining or deferring entails. Let the reader revise the proposal or add conditions.

A clear recommendation should reveal the objective or priority being optimized. It should still leave the reader able to reject it or choose another tradeoff.

**14. Retain significant decisions**

For significant architectural or scope decisions, retain:

* The problem and relevant context.
* The selected approach and rationale.
* Material alternatives and tradeoffs.
* Approval scope and any conditions.
* Supporting evidence.
* Decision status and enough identity or date information to follow later changes.

Use the accepted decision as the baseline for subsequent work. Reconsider it when a material new finding or changed constraint warrants doing so, and state that finding explicitly.

Use lightweight records for consequential decisions; routine work can remain in its ordinary change history. An architectural decision record is a short document preserving the choice, context, and consequences.

**15. Preserve these illustrative examples**

These are fictional examples demonstrating communication behavior. Their test results and repository details are not claims about a real project.

**Example A: Small completed PR following an approved plan**

Assume the change is complete, relevant checks passed for the revision, and the project requires merge approval.

"Merge the fix for keyboard focus in the search dialog (PR #142)? It implements the approved change. The keyboard interaction test and required checks passed on this revision. I recommend merging."

If merging was already authorized, perform the authorized action and report the outcome rather than asking again.

**Example B: A scope deviation with a compatibility tradeoff**

The requested fix concerns comma-separated values (CSV) imports. A prepared shared date-validation fix also changes uploads through the application programming interface (API).

A suitable brief would communicate:

* Decision: Include the shared date-validation fix in this PR?
* Recommendation: Use the shared fix so CSV imports and API uploads validate dates consistently.
* Why input is needed: The original request covered CSV imports; the shared fix changes API uploads too.
* Consequence: Both paths reject impossible dates. API callers that depend on dates being silently corrected would receive validation errors.
* Evidence: In this fictional scenario, regression tests pass for both paths, while third-party caller compatibility cannot be verified from the repository.
* Alternative: Apply the fix only to CSV imports, preserving the current API behavior.
* Recovery: The code can be reverted, but rejected uploads would need resubmission.
* Approval scope: Include the prepared shared change in the PR for review.
* Decision sensitivity: A requirement to preserve existing external caller behavior would favor the CSV-only option.

This illustrates how to expose a compatibility decision. It is not a blanket recommendation to change external behavior.

**Example C: A race condition in search results**

"The search box can display results for an earlier query after you have already entered a newer query. I recommend allowing only the latest search request to update the displayed results."

| Event                                     | Current behavior                                    | Proposed behavior                                                      |
| ----------------------------------------- | --------------------------------------------------- | ---------------------------------------------------------------------- |
| You search for "cat," then "caterpillar." | Both searches run.                                  | Both run; the application records "caterpillar" as the latest request. |
| Results for "caterpillar" arrive first.   | Displays "caterpillar" results.                     | Displays "caterpillar" results.                                        |
| Results for "cat" arrive later.           | Overwrites the display with outdated "cat" results. | Recognizes the older request and keeps the "caterpillar" results.      |

The explanation should then state:

* Mechanism: Each request receives an increasing sequence number. The response handler checks it against the latest request before updating the display.
* Property being protected: Only the most recent search request may update the results.
* Scope or tradeoff: Older requests may still consume network resources until they finish.
* Verification needed: A test that deliberately returns responses out of order, plus review of the relevant response and error handlers.

The real implementation must support the claimed behavior; this illustrative sequence is not a substitute for verification.

**16. Operational workflow for the eventual agent**

Before communicating:

1. Identify the project goal, current stage, approved baseline, and existing authorization.
2. Determine whether there is a real unresolved decision or only an outcome to report.
3. Complete the relevant authorized investigation and preparation.
4. Assess the seven axes.
5. Choose the communication situation, depth, and representation.
6. Draft the smallest sufficient explanation.
7. Define references and verify that important claims match the evidence.
8. Make the next action and its authorization scope explicit.
9. Retain a decision record when the decision is significant.

Before sending, check:

* Can the reader identify the work without reopening the plan?
* Can they state the exact decision and commitment?
* Can they understand why the recommendation follows from the evidence and project priorities?
* For a non-obvious mechanism, can they see the failure and why the proposed change addresses it?
* Are all consequences or uncertainties that could change their answer visible?
* Are examples, assumptions, predictions, and verified results clearly distinguished?
* Are comparisons using the same relevant inputs or event sequence?
* Is reversibility described in terms of actual effects, not only reverting code?
* Is the message proportionate, with no avoidable repetition or unrelated background?
* Is a new approval actually needed?
* Are meaningful alternatives, conditions, and the next action clear?

**17. What I want you to deliver**

Build one coherent, reusable communication prompt from this specification. It should contain practical behavioral rules, a procedure for selecting depth and representation, flexible response patterns, and a concise self-check. Preserve the distinctions that prevent oversimplification.

Put the finished communication prompt in one copy-pasteable block.

After that block, provide:

* A concise explanation of your organization and any substantive refinements.
* A compact mapping showing where the seven axes and the main requirements are covered.
* Short fictional output examples demonstrating:

  1. Routine authorized work requiring no new approval.
  2. A completed, tested PR under an approved plan that still requires a merge decision.
  3. A meaningful plan deviation with a real tradeoff.
  4. A subtle algorithm or race-condition change requiring a worked comparison.
  5. An architectural decision during planning.
  6. A short code change with a major consequence.
  7. An unfamiliar or cognitively complex change with low impact.
  8. A message using task or phase identifiers that must be locally defined.

Use these examples to check that the prompt produces proportionate messages, preserves meaning, exposes material uncertainty, and avoids unnecessary requests for permission. Label every fictional fact and test result appropriately. Resolve routine design choices yourself and identify only material remaining gaps.

**18. Background sources**

The complete framework is a proposed synthesis for agent communication. These sources support particular ingredients; do not portray the entire framework as a validated universal scoring system or treat heuristic lengths as empirical thresholds.

* [Progressive disclosure](https://www.nngroup.com/articles/progressive-disclosure/).
* [Recognition and recall, including the value of visible context](https://www.nngroup.com/articles/recognition-and-recall/).
* [Specific confirmation wording and avoiding routine confirmation overload](https://www.nngroup.com/articles/confirmation-dialog/).
* [Code review, functionality, test quality, and concurrency reasoning](https://google.github.io/eng-practices/review/reviewer/looking-for.html).
* [Architectural decision record contents](https://docs.aws.amazon.com/prescriptive-guidance/latest/architectural-decision-records/faq.html).
* [Architectural decision history and lifecycle](https://docs.aws.amazon.com/prescriptive-guidance/latest/architectural-decision-records/adr-process.html).
