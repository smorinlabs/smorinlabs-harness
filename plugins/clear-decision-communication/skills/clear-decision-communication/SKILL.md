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

The complete visible response is the finished decision brief, information
request, or authorized-work update. Keep preparation, sizing, and compliance
notes out of it, including preambles such as "I read the skill" or "Here is the
rewritten question". Source evidence and reasoning that help the reader choose
belong in the response; the drafting process does not.

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
     dialog. Ask for the smallest source artifact that supplies the missing
     context, such as the setup proposal, rather than a questionnaire about
     facts that artifact can answer. Do not invent a missing name or role.
     Do not add decision tiers, options, or approval language to that
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

2. **Size: scan the axes, set the tier.** Read `references/axes-and-tiers.md`
   and rate six axes low, elevated, or high with its tests: impact, reversibility,
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
   | T1 | Confirm | all six rated axes low, such as a required gate on an on-plan, verified, reversible change | the prepared result and its verification, nothing more | a self-contained question, the full recommendation or explicit neutrality, and concise options with consequences | about 100 words |
   | T2 | Compact brief | any axis elevated, none high | facts resolved, verification run, the strongest alternative prepared | grounding L1 and L2 when needed, question, full recommendation or neutrality, complete option list with each option's gain and cost, the runner-up condition, relevant evidence or comparison, and exact reply | about 250 words, excluding grounding and diagrams |
   | T3 | Full brief | any axis high | plus a prototype or experiment where authorized, a correctness argument, and decision sensitivity | every applicable section, grounding L1 to L3, the representation the change type requires, and a details pointer when supporting material exists | about 500 words, excluding grounding and diagrams |

   The length signals are review targets, not caps. Past them, re-run the
   removal test, shorten repeated explanation, and move supporting detail
   behind Details. Do not compress away a material condition to meet a
   sentence or clause count. Keep every material consequence, uncertainty,
   definition, and approval boundary in the initial view, even when it exceeds
   the target.
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
   the decision needs and note the revision it ran on. Read
   `references/evidence.md` and record each claim's evidence status as it
   defines. Prepare a concrete,
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
   connections matter. When a visual trigger below holds, use the change-type
   table to pick the form for the behavior the reader must judge. Forms live in `references/representation.md`, numbered
   F1 to F22 so a form can be named by ID.

   Complexity, not the change type, decides whether a visual is required.
   The change-type table then picks its form. A visual is required when any
   of these holds, whether the decision concerns process, code, or
   architecture:

   | Trigger | Example |
   |---|---|
   | The reader must hold three or more relationships at once | a gateway, two services, and a shared store |
   | The reader must simulate an order of events or a change of state | a retry, a race, a revision lifecycle |
   | Two or more options take visibly different paths | the same request routed differently under each option |
   | The same input produces different outcomes under current and proposed behavior | a validation rule that now rejects an input it accepted |

   When no trigger holds, use a sentence and draw nothing, whatever the
   change-type row names: a rename, a verified merge, or a single setting. At T1 a trigger rarely holds; if it
   does, the size is probably T2. When a trigger holds, the visual is part of
   L2 grounding and precedes the question. A comparison that only confirms
   an outcome can still follow the options.

   | Type of change | Show |
   |---|---|
   | Mechanical, such as a rename | one descriptive sentence naming the change and its purpose |
   | Conditional behavior, such as a validation rule | the same input with the previous and the proposed outcome (F1); if only design rules are known, compare those rules and leave runtime outcomes unknown |
   | Algorithm, such as ranking, scheduling, or retries | a worked example as pseudocode (F2), a whole block (F7), or a table of its steps, plus the boundary case and the rule the algorithm must preserve |
   | Timing or state interaction, such as a race | an ordered sequence with the same event order under current and proposed behavior (F9 or F10), or a span chart (F16) when overlap in time is the fact |
   | Architectural, such as moving responsibilities | a small ASCII system diagram with coded nodes (F8, F17, or F18), the baseline first and the change as a delta, one representative operation through it, and the tradeoffs |
   | Process, sequencing, or dependency across work items, such as which revision carries a change or which work waits on which | a process view (F22): each item's current state, what it depends on or pins, and the path each option takes; required at T2 and above when three or more items or states interact |

   Read `references/representation.md` before drawing: every artifact follows
   its diagram rules, including the frame (a lead-in, the artifact exact and
   unedited, and a reading), identical inputs across comparisons, and the
   outcome-cell checks.

5. **Draft the brief.** Establish the decision topic immediately. Put the
   question first only when a reader who never watched the run understands it
   by itself. Otherwise ground it first, from high to low:

   | Layer | Holds | Tier |
   |---|---|---|
   | L1 Situation | in plain words and without IDs: the system or document involved, the goal it serves, what happened, and the kind of decision this is | T1 as one clause when needed; T2 and T3 always |
   | L2 Mechanics | the moving parts, their current state, and how they depend on each other; a diagram from step 4 when three or more interact | T2 when an axis needs it; T3 always |
   | L3 Evidence | the source passages, checks, and file references behind the claims | in the evidence section at every tier |

   L1 states the decision layer. A substantive decision chooses what is
   right: a behavior, a design, a policy. A process decision chooses how the
   work proceeds: which revision or batch carries a change, what order work
   runs in, what waits on what. A process decision names the substantive
   question underneath it, says it is not being decided here or where it will
   be decided, and says when an option would settle it anyway. Adding a change
   to a repair revision, for example, approves that change without its own
   review. Explain each identifier by its role in this situation at first use;
   a glossary line of bare definitions is not grounding. State the current
   condition and immediate commitment before the options. Name each command,
   tool, library, document, or concept exactly and define its role at first use.
   Show a relevant command or source statement when it makes the choice concrete.
   Use simple sentences with one primary assertion each.
   Distinguish agreed requirements, verified constraints, and proposed
   implementation choices. Check whether all options assume a design choice
   the user has not approved. State the recommended action in full before
   attaching its option ID. Give its reason in that sentence or the next.
   Then put the complete option list
   immediately after the recommendation or neutral statement. Lead each
   displayed option with its stable lettered ID; the ID is its only label.
   Each option names the affected asset, scope, consequence, and immediate
   action. At T2 and above, each option also states what choosing it gives up
   or costs, including for the recommended option, and how it is reversed or
   what it leaves open. After the list, state when the runner-up, the strongest
   alternative, would be the better choice. Follow with any comparison and evidence needed to judge them, then
   the exact response requested. Mention an alternative before the list only
   by its action and meaning, never by an unexplained ID.

   Treat the template as a reading order, not a checklist of headings. State
   each material fact once unless repeating an exact noun or condition prevents
   ambiguity. Keep necessary context and evidence; remove duplicated summaries
   and drafting narration. Omit extra tracking IDs, parameter names, and audit
   findings unless they change the choice or support a material claim.
   A T1 can satisfy several fields in one sentence.
   Read `references/clarity.md` while drafting: it holds the four reader gates,
   the sentence and term controls, the naming and self-contained-reference
   rules, and the error catalog.

   | Question | What the reader must be able to state afterwards |
   |---|---|
   | What kind of decision is this? | whether it is substantive or process; for process, the substantive question underneath it and whether any option settles it |
   | What am I deciding? | the exact choice, the supported recommendation or neutrality, the main justification |
   | Why does this need my input? | the original goal, the discovery, the judgment or authorization needed |
   | What changes? | current or agreed behavior against proposed behavior, including any deviation |
   | What am I accepting? | benefit, main downside of the recommended option, who and what is affected, how reversal actually works |
   | What supports the recommendation? | verified evidence, material uncertainty, assumptions, what would change the recommendation |
   | What happens when I choose? | the strongest alternative and the condition under which it wins, the consequence of declining or deferring, the exact action approval authorizes |

6. **Check the completed draft against its sources.** Before the reader checks
   below, make a separate verification pass over the recommendation, comparison,
   option consequences, summary, and proposed decision record. Reopen the
   supporting passages or results rather than relying on the draft's wording.
   For each decision-critical claim, match the exact asset, source statement,
   conditions, and evidence status. A source that supports only part of a claim
   does not support the whole sentence. Remove the unsupported part, narrow it,
   or state the unresolved fact. Mark calculations as derived and retain their
   input values. Check the revised draft for contradictions, then apply every
   reader check below. Reread `references/evidence.md` and apply it to each
   decision-critical claim. Include relevant sources and limits in the brief without narrating
   this verification process:
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
   - If a step-4 visual trigger holds, a framed visual precedes the question.
     If none holds, the brief contains no diagram.
   - Every consequence or uncertainty that could change the answer is in the
     initial view; verified, inferred, assumed, and not verified are told
     apart; reversibility is described as actual effects, not "revert the
     commit".
     Rewriting has preserved each claim's subject, scope, and conditions;
     permissions or safeguards for one component do not stand for another's.
     Check claims in options, table readings, and records against their sources
     too; an accurate evidence paragraph cannot repair a stronger claim elsewhere.
   - Remove each sentence in turn: if the decision is no harder for a reader
     who never watched the run, cut it. Judge as that reader, not as the
     writer who already holds the context. The
     length target prompts review, never removal of material information.
     Artifact readings, option consequences, and evidence labels are concise
     enough to expose their meaning without hiding a condition or limitation.
     No placeholder text left to fill in later; no hedge words such as "should",
     "probably", "seems" standing in for a statement of what was not verified.
   - Every question and option carries its ID. When a recommendation exists,
     it is A and listed first. IDs have not changed meaning; a materially
     revised question supersedes its previous ID. Every option label names its
     outcome with a verb phrase; alternatives, conditions, and next actions are
     explicit for every option, including hold and defer. Read the closing
     action separately for each choice: deferring a policy leaves it open;
     a shared closing sentence must not imply that every answer approves work.
     The reader knows how to reply.
   - Only actions that have actually happened are reported as done or in
     progress. An authorized action not yet performed is a next step
     ("Next, I will run the dry run"), never present progressive ("I'm
     running it now") and never given a result.
   - The brief passes the four reader gates in `references/clarity.md` and
     applies its error catalog.

7. **Deliver.** Plain text is canonical; a dialog rendering derives from it.
   Read `references/delivery.md` before delivering: it holds tool adaptation,
   the two-turn rule, batching, and the silence default. Put all
   decision-critical context inside a dialog's payload. A preselected option,
   elapsed time, or tool completion without an answer is never approval.

8. **After the answer.** Read `references/delivery.md` and handle the reply
   with its reply table and confusion recovery. Match the reply to one open question
   and its unchanged options before acting; never execute a reply to a
   superseded question. Read `references/decision-record.md` to decide whether
   a decision record is due, and retain one when it is.

## The brief: canonical text form

The topic is immediately identifiable. The question comes first when it is
self-contained; otherwise the grounding layers from step 5 precede it. Use this order,
combining fields when a short question needs no separate sections. The fence
quotes the template; send the brief as ordinary message text.

```
<L1 Situation, when needed: in plain words, the system or document, the goal
  it serves, what happened, what waits on the answer, and the decision layer.
  For a process decision: the substantive question underneath it, and
  whether any option settles it.>
<L2 Mechanics, when needed: the moving parts and their current state, as a
  framed visual when a step-4 trigger holds, with each option's path.>

Q1. <One full sentence naming the concrete choice and its scope>
I recommend <action on the named asset and scope>, because <reason> (Q1.A).
  OR: <Why no option wins under established criteria and which preference settles it>.

- Q1.A (Recommended) <Action and outcome>. <Effect, conditions, and what I will do now.>
  <T2+: You give up or owe: <cost>. Reversal or what stays open: <effect>.>
- Q1.B <Action and outcome>. <Effect, conditions, and what I will do now.>
  <T2+: You give up or owe: <cost>. Reversal or what stays open: <effect>.>
- Q1.C <Action and outcome>. <Effect, conditions, and what I will do now.>
  <T2+: You give up or owe: <cost>. Reversal or what stays open: <effect>.>

<T2+ with a recommendation: <runner-up option ID> would be better if <condition>.>

<Only when needed: the comparison or example that exposes the mechanism.>
Evidence and limits: <Specific source or executed check, what it establishes,
  and the material unknowns. Distinguish source reports, observations,
  inferences, assumptions, and proposals. Omit empty categories.>
<What would change the recommendation: name the evidence or preference and
  the alternative action it favors. Omit when already clear or neutral.>

Reply with A, B, or C. <Restate any approval boundary needed to interpret the
  options. Describe different next actions separately; defer stays open.>
Details: <Supporting diff, logs, source, or trace, when useful>.
```

Use only the options that exist. Choose one recommendation form, never both.
For neutrality, omit every recommended marker and do not invent a runner-up
condition. A supported recommendation
reveals its objective. At T2 and above, name the strongest alternative and the
condition under which it wins, after the list, so the reader never looks forward
to an undefined option. At T1, include it only when that distinction matters.
A missing measurement can justify investigation without selecting an untested
alternative. Say which decision that new evidence would inform.

Rendering by tier:

- **T1** keeps the question, gate, checked result, supported recommendation or
  explicit neutrality, and concise options with consequences. Do not add
  sections whose content is already clear. A T1 has five parts: the question
  line, which names the change and its purpose; the check and the gate, in
  one or two sentences; the recommendation sentence; the options; and the reply line.
  Do not restate the handoff in a context paragraph. Give each option its
  action, what I do now, its effect, and its reversal in short clauses, as in
  the example below; do not repeat facts the question line already states. The
  reply line is "Reply with A or B." Add one sentence for an approval
  boundary only when the handoff or a policy establishes that boundary;
  otherwise omit it. Past about 120 words, cut repeated facts and any claim
  the handoff does not support, then rerun the removal test before sending.
  For example, sent as ordinary text:

  ```
  Q1. Merge PR #142, the fix that stops Tab from moving keyboard focus behind the search dialog?
  The keyboard-interaction test and all required checks passed on revision 9c8d7e6.
  CONTRIBUTING.md requires a human to approve every merge.
  I recommend merging the fix, because it implements the approved change without deviation (Q1.A).

  - Q1.A (Recommended) Merge PR #142. I merge it as soon as you reply. Undoing it takes a revert PR. No stored data changes.
  - Q1.B Hold PR #142. It stays open and unmerged, and you can approve the merge later. I continue with the other planned work.

  Reply with A or B.
  ```

  Those seven lines answer all six reader questions from step 5 by merging
  fields, not dropping them:

  | Line | Reader question it answers |
  |---|---|
  | `Q1. Merge PR #142, the fix that...` | What am I deciding? What changes? (Tab no longer moves focus behind the dialog) |
  | `...checks passed on revision 9c8d7e6` | What supports the recommendation? |
  | `CONTRIBUTING.md requires...` | Why does this need my input? |
  | `I recommend... because...` | What am I deciding? (recommendation and reason) |
  | Q1.A's `Undoing it takes...` | What am I accepting? |
  | Q1.B's `I continue with...` | What happens when I choose? |
- **T2** adds the orientation, material consequences and uncertainty, strongest
  alternative, and conditional comparison that the elevated axes require.
- **T3** adds the applicable representation, correctness argument, decision
  sensitivity, and a details pointer when supporting material exists.

At every tier, name a required gate and where it lives. Keep benefit, main
cost, affected people, material conditions, and actual reversal effects visible.
The option's immediate action distinguishes direction, experiment, implementation,
merge, and activation. A significant decision's record location can accompany
that action; record a deferral as deferred, not decided. Sizing appears only
when requested. Omit optional fields rather than narrating why they are absent.

Add an `If I hear nothing by <when>` line only when the run cannot wait;
`references/delivery.md` defines when it is allowed and what the fallback may
do. In an attended session omit the line and wait on dependent work.

Read the closest example in `references/worked-examples.md`: routine work,
merge, scope deviation, race, architecture, retention policy, retry algorithm,
identifier definitions, clarification after a replaced premise, or a process
decision about what a batch or revision carries. For a
policy question about a named developer tool and a research proposal, read
`references/project-policy-example.md`. Examples illustrate the form; obtain
the current question's facts from its own sources.

## IDs and the reply grammar

Questions are numbered `Q1`, `Q2`, and the numbers continue across the whole
run, so `Q3` means the same decision in every later message. After a context
reset, resume from the highest number visible in the conversation or the
record, and say so. Options are lettered `Q1.A`, `Q1.B`, `Q1.C`. The
recommended option, when one exists, is first and therefore `A`. A neutral
question has no recommendation marker. In ordinary text, display each option
as a bullet that leads with its ID: `- Q1.A (Recommended) <action>`,
`- Q1.B <action>`. The ID is the option's only label; do not add list numbers,
which would give one choice two names. Bullets keep each option on its own line
where markdown would merge adjacent lines. A bare letter selects an option only
when it identifies one live question unambiguously. In a batch or after a
superseded question, clarify an ambiguous reply with the full current ID.
Never reinterpret a stale letter as permission for a replacement option.

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

`references/delivery.md` holds the table of replies the ask must accept, in any
wording.

## Red Flags

| Thought | Reality |
|---|---|
| "I'm running it now" | Say so only after starting it. An action you have not performed is a next step: "Next, I will run it." Never report a result you have not observed. |
| "The user knows the plan; 'Approve Phase 2?' is enough" | Connect the goal to the exact artifact and its role, then state what answering changes now. |
| "It is a quick yes or no" | Yes and No hide the consequence. Options name what happens: "Merge" and "Hold". |
| "I will assume yes and keep going" | Silence grants no authority. A stated fallback can pause, defer, or perform already-authorized work; skip selects none of it. |
| "Tests pass, so the decision is safe" | Passing tests reduce uncertainty. They do not reduce impact, recovery cost, or the need to understand the mechanism. |
| "More context is safer" | Depth is set by the highest axis and spent only on that axis. Unrelated background hides the decision. |
| "The reader has the context I have" | They were not watching. Ground high to low: the situation in plain words, then the moving parts, then the evidence. A missing layer hides the decision as surely as unrelated background. |
| "A glossary line defines the IDs" | Definitions do not describe the situation. Explain each identifier by its role here, and say what process the decision belongs to. |
| "It is only a process question" | Say so, name the substantive question underneath, and say whether any option settles it without its own review. |
| "The recommendation's benefits make the case" | State what the recommended option gives up and when the runner-up wins. A choice shown only by its benefits is a sales pitch. |
| "The host's name tells me which dialog to call" | Inspect the tools actually exposed and their restrictions. Put necessary context in the payload; use a separate delivering turn only when that surface needs it. |
| "A diagram would look thorough" | Show only what changes the answer, in the smallest ASCII form, framed. Decoration is noise. When three or more items, states, or dependencies interact, prose is the defect. |
| "It is code, not a process, so prose will do" | The visual trigger ignores the change type. Three or more relationships, a sequence or state to simulate, or diverging option paths require a visual for code and architecture too. |
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
