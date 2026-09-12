---
name: clear-decision-communication
description: "Compose and deliver a decision request from an agent to a human during a run, as inline text: decide whether a new decision is needed at all, size the ask by seven axes into three tiers, show the change in the smallest form that exposes it, and hand back numbered questions with lettered options, a recommendation when evidence supports one, evidence with its limits visible, and the exact action approval authorizes. Use whenever an agent is about to ask the user to choose, approve, merge, deploy, or accept a deviation, before opening a decision dialog, or when the user says \"ask me properly\", \"frame this decision\", \"what do you need me to decide\", \"turn this into a decision\". Not for reviewing someone else's draft, walking a whole pile of questions, or producing pages, HTML, or rendered diagrams."
arguments: [target]
argument-hint: "[target]"
allowed-tools: Read, Grep, Glob, Bash, Agent, AskUserQuestion, WebFetch, WebSearch
---

# clear-decision-communication

Turn the moment an agent needs a human decision into the shortest self-contained
ask the reader can answer in a word: one question per decision, lettered options
that name their consequences, a recommendation when supported and what would
change it, evidence with its limits visible, and the exact action approval
authorizes. Use ASCII for authored prose and diagram syntax. Preserve verbatim
paths, identifiers, input data, quotations, and captured output exactly,
including non-ASCII characters. Never produce an HTML artifact or a rendered
diagram; a downstream tool may render this text.

> **NEVER ASK WHAT YOU CAN RESOLVE, AND NEVER SEND AN ASK THE READER MUST
> RECONSTRUCT.** Investigate discoverable facts before asking; request a required
> fact only when authorized investigation cannot obtain it and the user can
> supply it. Escalate unresolved judgment, preference, policy, and authority.
> What reaches the human carries
> its own context: the reader never reopens a plan, scrolls back, or simulates code
> to understand the question.
>
> No exceptions: not "the user knows the plan", not "it is only a quick yes or no",
> not "the option labels carry the trade-off", not "I will assume yes and keep
> going". Violating the letter of this rule is violating the spirit of it.

Three judgments stay separate throughout. Whether to ask is judgment one and is
never set by size. How much to prepare and explain is judgment two, the tier.
Which representation to use is judgment three: resolve the reader's missing
understanding, then use the change type, never the tier. Domain complexity alone
never creates a permission requirement, and a
routine change behind a mandatory gate still gets only a short ask.

Invoked by hand with a target, such as a pasted question, a draft ask, a pull
request, or a diff, treat the target as the situation and run the same workflow;
the output is the brief for that target.

## Workflow

1. **Gate: is a decision needed at all?** Ask only when every check holds.
   - No existing authorization covers the action: instructions, the approved
     plan, a standing preference, an earlier answer. Authorization persists;
     never ask twice. Honor standing preferences; explain their effect on
     sizing only when the reader requests that explanation.
   - The answer is a decision, not a discoverable fact. Read, test, fetch, or
     delegate factual investigation within existing authorization. If a required
     fact remains unavailable and the user can supply it, request that exact
     information with its purpose in ordinary text or a supported information
     dialog. Do not add decision tiers, options, or approval language to that
     information request. Continue independent authorized work while waiting.
   - What resolves it is the human: their judgment, preference, policy, or
     authority. If a rough prototype would resolve it and building one is
     already authorized, build it and ask the human to react
     to it; otherwise offer the prototype as an option. If a task must happen
     first, do it or hand it over, then ask.
   - Name the upcoming commitment that depends on the answer and the
     consequence of waiting. An eventual owner decision need not interrupt
     work that can already proceed. For an unavailable fact, explain what
     that fact determines; account access, for example, establishes an
     available setup path, not the credential policy for every adopter.
   - The question is sharp: you can state it and its options in one sentence.
   - One of these is true: a required gate (name the rule and where it lives),
     a departure from the agreed goal, scope, approach, or constraints, a
     tradeoff whose criterion the human owns, or a blocker you cannot clear.

   When a check fails: a question that is not yet sharp becomes an ask for
   what would sharpen it, stated with what is already known. An unavailable
   fact follows the information-request rule above. A blocker pauses the work
   that depends on it, with the missing input or action stated plainly. Continue
   other work only under existing authorization, report in ordinary form, and
   do not use the decision brief for it. A failed gate creates no authorization.
   Every avoided ask makes the
   remaining ones land. Routine confirmations teach the reader to click through,
   and then the one that matters gets clicked through too.

2. **Size: scan the axes, set the tier.** Rate six axes low, elevated, or high
   with the tests in `references/axes-and-tiers.md`: impact, reversibility,
   departure, uncertainty, tradeoff, domain (those six words are the canonical
   tag names). The highest single axis sets the tier; axes are never summed.
   Only the axes above low expand, each adding exactly the information its row
   names. The seventh axis, context gap, is always treated as elevated because
   the reader was not watching, so self-contained references are on at every
   tier; it never sets the tier. Two floors override the size of the change:
   a timing, ordering, or state interaction, such as a race, a retry policy, a
   cache, or a consistency rule, is always high on domain, however few lines
   it touches; deleting data that cannot be recovered is always high on
   reversibility. Initial sizing is provisional; preparation addresses the
   issues that set it.

   | ID | Tier | Fires when | Prepare | The initial view holds | Length signal |
   |---|---|---|---|---|---|
   | T1 | Confirm | all six rated axes low, such as a required gate on an on-plan, verified, reversible change | the prepared result and its verification, nothing more | a self-contained question, the recommendation or explicit neutrality, two or three options with consequences; two or three sentences in all | about 80 words |
   | T2 | Compact brief | any axis elevated, none high | facts resolved, verification run, the strongest alternative prepared | orientation when needed, the question, the recommendation or explicit neutrality, the sections the elevated axes call for, the options, the next action; one comparison when the change is conditional | about 250 words |
   | T3 | Full brief | any axis high | plus a prototype or experiment where authorized, a correctness argument, and decision sensitivity | every applicable section, the representation the change type requires, and a details pointer when supporting material exists | about 500 words |

   The length signals are review targets, not caps. Past them, re-run the
   removal test, shorten repeated explanation, and move supporting detail
   behind Details. Keep every material consequence, uncertainty, definition,
   and approval boundary in the initial view, even when it exceeds the target.
   Use sizing internally. Omit tier tags and drafting or batching logistics
   from ordinary requests. Explain the actual consequence that needs attention,
   such as repository write access. If the reader asks to inspect sizing, show
   the tier and the axes that set it and honor their standing preferences.
   Do not narrate compliance with these instructions, including promises to
   omit tags or explanations that a decision record is unnecessary.

3. **Prepare to the tier.** Inspect the code, the goal, the approved baseline,
   and the constraints. Resolve every factual question that authorized
   investigation can answer; execute what you need to execute to get evidence,
   and never mutate beyond what the run already authorized. Run the verification
   the decision needs and note the revision it ran on. Prepare a concrete,
   reviewable result: a patch with its checks for an implementation approval,
   concrete alternatives with evidence for a direction. If the user can supply
   an unavailable fact, use step 1's information request. Otherwise, when
   essential information cannot be obtained, write "I cannot verify X without
   Y", say why it matters, and compare the feasible commitments: investigate
   at a stated cost, decide conditionally, or defer to a smaller commitment.

   After preparation, re-rate uncertainty using the evidence obtained. Lower
   the final tier if evidence resolves its only elevated or high issue. Passing
   tests alone never lowers impact, reversibility, departure, tradeoff, or
   domain complexity. Name any material uncertainty that remains. If a check
   could change the recommendation and can run within existing authorization,
   run it before asking for approval of the completed work.

4. **Choose the representation for the missing understanding.** Establish
   what answering changes now: a direction, an experiment, implementation,
   completed work, or activation. If the reader cannot identify the work, show
   the artifact types, exact names, and roles. If its connection to the goal is
   missing, show that relationship before its internals. A sentence or artifact
   table often suffices; use a small relationship diagram when several
   connections matter. Then use the change-type table for the behavior the
   reader must judge. Forms use ASCII syntax, preserving verbatim content,
   and live in
   `references/representation.md`, numbered F1 to F21 so a form can be named by
   ID.

   | Type of change | Show |
   |---|---|
   | Mechanical, such as a rename | one descriptive sentence naming the change and its purpose |
   | Conditional behavior, such as a validation rule | the same input with the previous and the proposed outcome (F1); if only design rules are known, compare those rules and leave runtime outcomes unknown |
   | Algorithm, such as ranking, scheduling, or retries | a worked example as pseudocode (F2), a whole block (F7), or a table of its steps, plus the boundary case and the rule the algorithm must preserve |
   | Timing or state interaction, such as a race | an ordered sequence with the same event order under current and proposed behavior (F9 or F10), or a span chart (F16) when overlap in time is the fact |
   | Architectural, such as moving responsibilities | a small ASCII system diagram with coded nodes (F8, F17, or F18), the baseline first and the change as a delta, one representative operation through it, and the tradeoffs |

   Keep inputs and event order identical across comparisons. Choose the smallest
   example that exposes the actual difficulty, and include ordinary behavior plus
   the distinguishing boundary case only when both matter. Every artifact carries
   a frame: a lead-in that says what question it answers, the artifact exact and
   unedited, and a reading that says what to take from it. Skip any artifact that
   adds nothing to a clear sentence. Say whether an example is illustrative or
   reproduced from a real run, and whether verification was performed or is
   proposed.
   Before filling an outcome cell, check that its source establishes the same
   actor, trigger, and condition values as that row. Keep independent inputs
   independent: a missing credential does not establish a setting's value.
   Label an unsupported outcome unknown. When the evidence defines only design
   rules, compare the stated rules instead of constructing a runtime trace.
   Do not complete a table by changing its inputs or supplying missing facts.

5. **Draft the brief.** Establish the decision topic immediately. Put the
   question first when it is understandable by itself. Otherwise precede it
   with the minimum connection from the user's goal to the affected component,
   the relevant discovery, and the remaining choice. State the current
   condition and immediate commitment before the options; present the
   recommendation once its object and consequences are understandable.
   Distinguish agreed requirements, verified constraints, and proposed
   implementation choices. Check whether all options assume a design choice
   the user has not approved. Follow with the comparison, consequences,
   evidence, and exact next action. Combine fields naturally; a T1 can satisfy
   several in one sentence. The template below is the canonical text form.
   `references/clarity.md` holds the sentence, term, and error
   rules applied while drafting, and `references/standards.md` holds the two
   standards behind them: ISO 24495-1's four reader outcomes, relevant,
   findable, understandable, usable, judged on the brief as a whole, and
   selected ASD-STE100 mechanics for its sentences and terms.

   | Question | What the reader must be able to state afterwards |
   |---|---|
   | What am I deciding? | the exact choice, the supported recommendation or neutrality, the main justification |
   | Why does this need my input? | the original goal, the discovery, the judgment or authorization needed |
   | What changes? | current or agreed behavior against proposed behavior, including any deviation |
   | What am I accepting? | benefit, main downside, who and what is affected, how reversal actually works |
   | What supports the recommendation? | verified evidence, material uncertainty, assumptions, what would change the recommendation |
   | What happens when I choose? | the strongest alternative, the consequence of declining or deferring, the exact action approval authorizes |

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
   - The reader can identify the work and state the exact decision and
     commitment without reopening the plan or the conversation.
     The artifact type and exact name, its connection to the goal, current
     condition, and effect of answering are clear. Scope, timing, and
     conditions agree across the question, options, next action, and decision
     record. Approval to update an implementation plan authorizes the plan,
     not implementation of the behavior it describes.
   - A recommendation follows visibly from the evidence and the project's
     priority, and the ask says what would change it. If no option wins under
     established criteria, the brief states why it is neutral and what human
     preference would settle the choice, without a recommended marker.
   - For a non-obvious mechanism, the reader can see the failure and why the
     change addresses it, with identical inputs across the comparison.
   - Every consequence or uncertainty that could change the answer is in the
     initial view; verified, inferred, assumed, and not verified are told
     apart; reversibility is described as actual effects, not "revert the
     commit".
     Rewriting has preserved each claim's subject, scope, and conditions;
     permissions or safeguards for one component do not stand for another's.
     Check claims in options, table readings, and records against their sources
     too; an accurate evidence paragraph cannot repair a stronger claim elsewhere.
   - Remove each sentence in turn: if the decision is no harder, cut it. The
     length target prompts review, never removal of material information.
     Artifact readings, option consequences, and evidence labels are concise
     enough to expose their meaning without hiding a condition or limitation.
     No placeholder text left to fill in later; no hedge words such as "should",
     "probably", "seems" standing in for a statement of what was not verified.
   - Every question and option carries its ID. When a recommendation exists,
     it is A and listed first. IDs have not changed meaning; a materially
     revised question supersedes its previous ID. Every option label names its
     outcome with a verb phrase; alternatives, conditions, and next actions are
     explicit, including the action associated with each neutral option.
   - The brief passes the four ISO 24495-1 outcomes: relevant, findable,
     understandable, usable.
   - Authored prose and diagram syntax use ASCII; verbatim content is exact,
     including non-ASCII characters. There is no HTML artifact or rendered diagram.

7. **Deliver.** Plain text is canonical; a dialog rendering derives from it.
   Read `references/delivery.md` for tool adaptation and reply handling.
   - Inspect the available question tool, its schema, and host restrictions.
     Put all decision-critical context inside the question payload when using
     a dialog; do not rely on accompanying prose being visible. Use the
     two-turn delivery rule only on surfaces known to lose that prose when
     necessary context cannot fit in the dialog. Plain text is the fallback
     when no suitable tool is available or permitted.
   - An asynchronous question does not stop independent authorized work.
     Dependent work waits for an actual answer. A preselected option, elapsed
     time, and tool completion without an answer are never approval.
   - The ordinary-text brief has no surrounding code fence. Tables use pipes;
     code and pseudocode use fences. Fence diagrams when alignment requires it.
   - Each option names its outcome and consequence. A recommendation is marked
     only when supported. At most three independent T1 or T2 questions share
     one message, further limited by the host; T3 goes alone. Coupled questions
     state their dependency and are asked in order. If a reply already answers
     the question, do not raise a second dialog.

8. **After the answer.**
   - Match the reply to one open question and its unchanged options before
     acting. Never execute a reply to a superseded question. Restate a valid
     decision with its ID, option, and date.
   - A condition ("A, but behind a flag") is restated with the chosen action.
     If it changes the action or approval scope, record the clearly authorized
     revised decision under a new ID with the old question as history; do not
     ask for the same permission again. Clarify only an unresolved commitment.
     An ask-back is answered, then reassessed before re-asking. A redirect
     ("check X first") is done first,
     then the question is reassessed. If the finding changes the options,
     recommendation, or approval scope, issue a new question ID and mark the
     old one superseded. A skip parks the question without selecting its
     fallback or advancing its deadline; continue only independent authorized work.
   - When the reader is confused, first check the concrete artifact, its
     project connection, current condition, and meaning of approval. Then check
     terminology and mechanism. Rewrite around the missing information; add
     or replace an example when it resolves that gap. Reassess whether a
     decision is still needed. If the user replaces a premise shared by the
     options, retire those options and record the new instruction under the
     ID rules. Proceed within that authorization; ask only about an unresolved
     commitment, never for formal confirmation that the explanation is clear.
   - Retain a decision record when at least two of these hold: hard to reverse,
     surprising without its context, the result of a real tradeoff. The
     template and where it lives are in `references/decision-record.md`.
   - Check persistent text for claims the answer made stale. Retain rejected
     alternatives as history in the decision record. When several questions
     are live, keep one tally line: open, decided, skipped, redirected, superseded.

## The brief: canonical text form

The topic is immediately identifiable. The question comes first when it is
self-contained; otherwise a short orientation precedes it. Sections that the
tier does not need are omitted, never left empty. The fence below only quotes
the template; the brief
itself is sent as ordinary message text. `references/worked-examples.md` renders
it at every tier: 1 the gate saying no, 2 a T1 merge, 3 a T2 scope deviation
with a same-input table, 4 a T3 race with an event table, 5 a T3 architectural
direction with a coded diagram and a record, 6 a T3 one-line change with a
policy consequence, 7 a T3 algorithm for an unfamiliar reader, 8 a T2 with
identifiers that must be defined, and 9 clarification that identifies the
artifacts before the user replaces an implementation premise. Read the one
closest to the situation.

```
<When needed: connect the goal, exact artifact and role, relevant discovery,
  and remaining choice. State the current condition and what answering changes now.>
Q1. <The decision as one full sentence naming the thing and commitment>
Recommendation: Q1.A, <what and why in one sentence>. Q1.B wins if <condition>.
  OR: Neutral: <why no option wins under established criteria and which preference settles it>.
Sizing explanation: <tier, axes, and any relevant standing preference>. (only when requested)

Why I am asking: <the upcoming commitment and consequence of waiting; distinguish
  agreed requirements, verified constraints, and proposed implementation choices.
  For a required gate, name the rule and where it lives. Combine with the opening
  when already explained; do not repeat it here>.
What changes: <one or two sentences, or the representation from step 4 when
  the change type needs one: current or agreed behavior, then proposed>.
What you would be accepting: <one sentence each: benefit; main downside; who
  and what is affected; what reversal actually involves>.
Evidence: Verified: <what, on which revision or environment>. Inferred: <what,
  from what>. Assumed: <what>. Not verified: <what, and why not>. <Keep labels
  concise without dropping material limits; omit empty labels.>
Options:                                                <concise consequence, with material conditions>
  Q1.A  <Verb phrase naming the outcome> (Recommended)  -- <what it causes>
  Q1.B  <Verb phrase naming the outcome>                -- <what it causes>
  Q1.C  <Verb phrase naming the outcome>                -- <what it causes>
Would change my recommendation: <the evidence, constraint, or preference; omit when neutral>.
On Q1.A I will: <the exact action and approval scope; for neutrality, specify each option's action>.
If I hear nothing by <when>: <pause, defer, or already-authorized work>, because <reason and prior authorization for any action>.
Record: retained as Decision Q1 in <where> once you answer.   (only when due)
Details: <paths to the diff, logs, test output, or traces>.
```

Choose one recommendation form, never both. For neutrality, omit every
`(Recommended)` marker and the runner-up condition; state the action each choice
authorizes. Options may be concise clauses but must retain material conditions.

Rendering by tier:

- **T1** keeps the self-contained question, the reason for the gate, the recommendation
  or explicit neutrality, and the options with their consequences. Two or three sentences. Example:
  `Q1. Merge PR #142, the keyboard-focus fix for the search dialog? It
  implements the approved change; the keyboard-interaction test and required
  checks passed on revision 9c8d7e6; CONTRIBUTING.md requires a human merge
  approval. Recommendation: Q1.A.` then `Q1.A Merge (Recommended) -- the fix
  ships on the next deploy` and `Q1.B Hold -- the PR stays open; say what to
  change`. The runner-up clause and the "On Q1.A I will" line are required
  whenever tradeoff complexity is above low and a recommendation exists.
  At T1 they may be omitted when the question and options already state the
  precise action and commitment. A neutral T1 still states why the preference
  remains the user's choice.
- **T2** renders the orientation when needed, the question, the recommendation with its runner-up
  clause or explicit neutrality, the sections its elevated axes call for,
  the options, what would change a supported recommendation, and the next
  action; the comparison table when the
  change is conditional.
- **T3** renders every applicable section, the representation from step 4, and the
  details pointer when supporting material exists.
- `If I hear nothing by <when>` appears at any tier only when the run cannot
  wait: the human said to continue unattended, or a scheduled step would be
  missed. It names the deadline the ask itself sets, such as "the next
  scheduled run" or "30 minutes". The fallback may only pause, defer, or perform
  work authorized before the ask; stating it grants no authority. Choose the
  most reversible eligible option, never scope expansion, merge, or deployment.
  Skip parks the decision without selecting the fallback or changing its
  deadline. In an attended session omit the line and wait on dependent work.

A supported recommendation names the runner-up and the condition under which
it wins when that alternative is meaningful. If no option wins under established
criteria, state neutrality and the preference that would settle it. Do not mark
any option recommended or render `Recommended: A.` for a neutral question. A
supported recommendation reveals its objective; the reader may reject it or
add a condition.

## IDs and the reply grammar

Questions are numbered `Q1`, `Q2`, and the numbers continue across the whole
run, so `Q3` means the same decision in every later message. After a context
reset, resume from the highest number visible in the conversation or the
record, and say so. Options are lettered `Q1.A`, `Q1.B`, `Q1.C`. The
recommended option, when one exists, is first and therefore `A`. A neutral
question keeps lettered options but has no recommendation marker. A bare letter
selects an option only when it identifies one live question unambiguously; in a
batch, request a full ID such as `Q2.A` before acting if the reply is ambiguous.

Keep each question's options and approval scope unchanged under its ID. If new
evidence changes an option's meaning, the recommendation, or the approval scope,
issue the next unused question ID and mark the old one `superseded by Qn`.
For example, when Q1.A meant workers but streaming now wins, Q2.A may recommend
streaming; Q1 is superseded. A later Q1.A reply executes neither action. Tell
the reader which current question replaced it and obtain an unambiguous choice.
A clarification that changes none of these keeps the existing ID. Do not
re-ask when the user's reply already clearly authorizes the revised action;
record that decision under its new ID with the prior question as history.

An answered question keeps its ID as its decision-record key. States are open,
decided with its option, skipped, redirected, and superseded with its successor.

Replies the ask must accept, in any wording:

| Reply | Meaning | What you do |
|---|---|---|
| `A`, `Q1.A` | pick | match one open question and its unchanged option, then proceed |
| `Q1.B, but <condition>` | pick with a condition | restate the exact conditional action; a changed action or scope gets a new ID, recorded directly when clearly authorized, otherwise clarify only the missing commitment |
| `Q1: skip` | park it | select no fallback, change no deadline; continue only independent authorized work |
| `Q1: ask <question>` | need information first | answer and reassess; keep Q1 only if options, recommendation, and scope remain unchanged, otherwise supersede it before re-asking |
| `Q1: do <X> first` | redirect | do authorized X, then reassess; supersede Q1 if its options, recommendation, or scope changed |
| a reply to a superseded question | stale answer | execute no choice; point to the current question and clarify the intended answer |
| a reply naming an option not offered | revised choice | use a new question ID; record directly if already clearly authorized, otherwise clarify the missing commitment |
| "I don't get this" | the ask failed | diagnose missing artifact, project connection, state, commitment, terminology, or mechanism; rewrite and reassess the decision |

## Confidence is inspectable

Every claim in the brief carries one of four labels, in words, never as a
fabricated number: **Verified**, observed directly or established by an executed
test or analysis, with the revision or environment it ran on; **Inferred** from
those results, which includes every estimate together with its basis;
**Assumed**, or a preference driving the recommendation; **Not verified**, an
unknown or a check still outstanding. A generic "tests pass" never implies
coverage that was not run; name the targeted checks and say what full
validation would add. Tests can establish that an implementation is correct
while whether the behavior is desirable remains the human's call. For timing
and concurrency, give the interaction argument as an inference beside the test.
Material uncertainty stays in the initial view; supporting detail such as diffs,
logs, and traces goes behind the details pointer, and only one level of detail
exists below the initial view.

Simplification preserves the subject, scope, conditions, and status of each
decision-critical claim. Agreed behavior is a requirement, not a validated
implementation. Where components differ, identify each one's permissions,
safeguards, and unknowns. A workflow's declared permissions do not establish
the effective permissions of a separately obtained credential.

Before sending, trace each decision-critical claim back to its support. A label
such as "Verified" does not make a stronger statement follow from its source:

- A documented trigger and an exercised trigger are different evidence. Retain
  the tested actor, event, and conditions; label broader predictions as inferences.
- An overall comparison does not establish a win on each metric. Keep aggregate
  conclusions aggregate unless separate measurements are supplied.
- An omitted check or UI behavior is unknown, not absent. "Not selected",
  "not tested", and "test status not recorded" describe different gaps; carry
  each finding's actual status into summaries and decision records.
- A request interval is not a maximum data age. An age estimate also needs
  assumptions about response time, source freshness, and failures. Remaining
  effects after reversal do not establish a need for manual cleanup.

Derive approval gates from the user's instructions and identified policy, not
from an imagined later stage. If exact patch bytes or other evidence are
unavailable, state the gap and the intended action. Omit unsupported additions;
never fill a template field with invented evidence, effects, or constraints.

## Self-contained references

Every statement is understandable from its own wording and the visible text
around it. Use a meaningful description first and attach the identifier for
navigation: "the database migration that stores queued jobs (Task 1)", never
"Task 1". Define task numbers, phases, option letters, and unfamiliar component
names on first use in each message. Reuse shorthand only while its definition is
still visible. Give every bullet and table row enough words to stand alone. Use
the reader's own names for things and attach the technical name in code font:
"the confirm card (`ApprovalGate`)". On first mention, give the actual artifact
type, exact name or identifier, and a short role description. Distinguish a
workflow file, a job inside it, an invoked action or script, a setting, and a
credential. A familiar label such as "lane" does not identify which one is
meant. Use a concise reference such as "the review workflow" afterward only
while unambiguous. Preserve established terms and real identifiers exactly,
including names that contain metaphor words. Mark proposed names as proposed;
if no name exists yet, say so instead of inventing an existing artifact.
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

## Red Flags

| Thought | Reality |
|---|---|
| "The user knows the plan; 'Approve Phase 2?' is enough" | Connect the goal to the exact artifact and its role, then state what answering changes now. |
| "It is a quick yes or no" | Yes and No hide the consequence. Options name what happens: "Merge" and "Hold". |
| "I will assume yes and keep going" | Silence grants no authority. A stated fallback can pause, defer, or perform already-authorized work; skip selects none of it. |
| "Tests pass, so the decision is safe" | Passing tests reduce uncertainty. They do not reduce impact, recovery cost, or the need to understand the mechanism. |
| "More context is safer" | Depth is set by the highest axis and spent only on that axis. Unrelated background hides the decision. |
| "The host's name tells me which dialog to call" | Inspect the tools actually exposed and their restrictions. Put necessary context in the payload; use a separate delivering turn only when that surface needs it. |
| "A diagram would look thorough" | Show only what changes the answer, in the smallest ASCII form, framed. Decoration is noise. |
| "The label is short, the trade-off is in my head" | Every option stands alone with its consequence, in case the brief is the part that never rendered. |

## Behavioral evaluation

The worked examples illustrate the brief; they do not prove reply handling.
`evals/evals.json` holds realistic scenarios with separate grading expectations.
Use them when changing authorization, IDs, orientation, naming, confusion
recovery, sizing, or delivery. Give an independent reader only the generated
brief and neutral comprehension questions; compare their reconstruction of the
goal, artifact, current condition, commitment, and option effects with the
scenario afterward. Include follow-ups that replace an option's premise and
rewrites that must preserve evidence qualifications. `evals/README.md` specifies
that review procedure and what the simulated follow-ups do not establish.
Evaluate actual responses in fresh sessions on the supported tools; process completion and
manifest validation are not semantic passes. `evals/README.md` explains the
runner, grading, and the limits of the simulation.
