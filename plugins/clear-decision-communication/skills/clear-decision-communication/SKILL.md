---
name: clear-decision-communication
description: "Compose and deliver a decision request from an agent to a human during a run, as inline ASCII text: decide whether a new decision is needed at all, size the ask by seven axes into three tiers, show the change in the smallest form that exposes it, and hand back numbered questions with lettered options, a recommendation that says when it would flip, evidence with its limits visible, and the exact action approval authorizes. Use whenever an agent is about to ask the user to choose, approve, merge, deploy, or accept a deviation, before raising any question dialog, or when the user says \"ask me properly\", \"frame this decision\", \"what do you need me to decide\", \"turn this into a decision\". Not for reviewing someone else's draft, walking a whole pile of questions, or producing pages, HTML, or rendered diagrams."
arguments: [target]
argument-hint: "[target]"
allowed-tools: Read, Grep, Glob, Bash, Agent, AskUserQuestion, WebFetch, WebSearch
---

# clear-decision-communication

Turn the moment an agent needs a human decision into the shortest self-contained
ask the reader can answer in a word: one question per decision, lettered options
that name their consequences, a recommendation that says when it would flip,
evidence with its limits visible, and the exact action approval authorizes. The
output is inline text in ASCII characters. Never HTML, never a rendered diagram;
a downstream tool may render this text.

> **NEVER ASK WHAT YOU CAN RESOLVE, AND NEVER SEND AN ASK THE READER MUST
> RECONSTRUCT.** Facts are read, tested, fetched, or delegated; only judgment,
> preference, policy, and authority reach the human. What does reach them carries
> its own context: the reader never reopens a plan, scrolls back, or simulates code
> to understand the question.
>
> No exceptions: not "the user knows the plan", not "it is only a quick yes or no",
> not "the option labels carry the trade-off", not "I will assume yes and keep
> going". Violating the letter of this rule is violating the spirit of it.

Three judgments stay separate throughout. Whether to ask is judgment one and is
never set by size. How much to prepare and explain is judgment two, the tier.
Which representation to use is judgment three, set by the change type, never by
the tier. Domain complexity alone never creates a permission requirement, and a
routine change behind a mandatory gate still gets only a short ask.

Invoked by hand with a target, such as a pasted question, a draft ask, a pull
request, or a diff, treat the target as the situation and run the same workflow;
the output is the brief for that target.

## Workflow

1. **Gate: is a decision needed at all?** Ask only when every check holds.
   - No existing authorization covers the action: instructions, the approved
     plan, a standing preference, an earlier answer. Authorization persists;
     never ask twice. When a standing preference changed the sizing below, name
     it in the ask.
   - The answer is not a fact. A fact is read from the code, run, fetched, or
     handed to a subagent; it never reaches the human as a question. Delegate
     the lookup and keep working on whatever does not depend on it.
   - What resolves it is the human: their judgment, preference, policy, or
     authority. If a rough prototype would resolve it and building one is
     already authorized or trivially cheap, build it and ask the human to react
     to it; otherwise offer the prototype as an option. If a task must happen
     first, do it or hand it over, then ask.
   - The question is sharp: you can state it and its options in one sentence.
   - One of these is true: a required gate (name the rule and where it lives),
     a departure from the agreed goal, scope, approach, or constraints, a
     tradeoff whose criterion the human owns, or a blocker you cannot clear.

   When a check fails: a question that is not yet sharp becomes an ask for
   what would sharpen it, stated with what is already known; a blocker you
   cannot clear stops the run with a plain statement of the blocker; every
   other failure means proceed under existing authorization, report the outcome
   in ordinary form, and do not use this skill. Every avoided ask makes the
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
   reversibility. The tier ratchets up only, and preparation stops at the
   tier.

   | ID | Tier | Fires when | Prepare | The initial view holds | Length signal |
   |---|---|---|---|---|---|
   | T1 | Confirm | all six rated axes low, such as a required gate on an on-plan, verified, reversible change | the prepared result and its verification, nothing more | the question line, the recommendation, two or three options with consequences; two or three sentences in all | about 80 words |
   | T2 | Compact brief | any axis elevated, none high | facts resolved, verification run, the strongest alternative prepared | the question line, the recommendation, the sections the elevated axes call for, the options, the next action; one comparison when the change is conditional | about 250 words |
   | T3 | Full brief | any axis high | plus a prototype or experiment where authorized, a correctness argument, and decision sensitivity | every section, the representation the change type requires, and a details pointer when supporting material exists | about 500 words |

   The length signals are review signals: past them, re-run the removal test
   on every sentence and keep every clause that could change the answer. One
   and a half times the signal is the cap: a brief past its cap is not sent
   until the readings are one sentence, each consequence and each evidence
   label one clause, and everything else is behind Details. Say the sizing
   out loud: the question line carries a tag naming the
   tier and only the axes that set it, without levels, such as
   `[T2: departure, uncertainty]`, so the reader can dispute the sizing itself.

3. **Prepare to the tier.** Inspect the code, the goal, the approved baseline,
   and the constraints. Resolve every factual question that authorized
   investigation can answer; execute what you need to execute to get evidence,
   and never mutate beyond what the run already authorized. Run the verification
   the decision needs and note the revision it ran on. Prepare a concrete,
   reviewable result: a patch with its checks for an implementation approval,
   concrete alternatives with evidence for a direction. When essential
   information cannot be obtained, write "I cannot verify X without Y", say why
   it matters, and offer as the options: investigate at a stated cost, decide
   conditionally, or defer to a smaller commitment.

4. **Choose the representation by change type.** First ask one question: would
   the reader understand this better by seeing it than by reading it? Then take
   the row that matches. All forms are ASCII text and live in
   `references/representation.md`.

   | Type of change | Show |
   |---|---|
   | Mechanical, such as a rename | one descriptive sentence naming the change and its purpose |
   | Conditional behavior, such as a validation rule | the same input with the previous and the proposed outcome, as a table |
   | Algorithm, such as ranking, scheduling, or retries | a worked example as pseudocode, a whole block, or a table of its steps, plus the boundary case and the rule the algorithm must preserve |
   | Timing or state interaction, such as a race | an ordered sequence with the same event order under current and proposed behavior |
   | Architectural, such as moving responsibilities | a small ASCII system diagram with coded nodes, the baseline first and the change as a delta, one representative operation through it, and the tradeoffs |

   Keep inputs and event order identical across comparisons. Choose the smallest
   example that exposes the actual difficulty, and include ordinary behavior plus
   the distinguishing boundary case only when both matter. Every artifact carries
   a frame: a lead-in that says what question it answers, the artifact exact and
   unedited, and a reading that says what to take from it. Skip any artifact that
   adds nothing to a clear sentence. Say whether an example is illustrative or
   reproduced from a real run, and whether verification was performed or is
   proposed.

5. **Draft the brief.** Answer the six questions, then render in the default
   order: decision and recommendation; necessary context; comparison or example;
   consequences and evidence; exact next action. Reorder only when a definition
   must precede the recommendation. Combine fields naturally; a T1 satisfies
   several in one sentence. The template in the next section is the canonical
   text form. `references/clarity.md` holds the sentence, term, and error
   rules applied while drafting, and `references/standards.md` holds the two
   standards behind them: ISO 24495-1's four reader outcomes, relevant,
   findable, understandable, usable, judged on the brief as a whole, and
   selected ASD-STE100 mechanics for its sentences and terms.

   | Question | What the reader must be able to state afterwards |
   |---|---|
   | What am I deciding? | the exact choice, the recommended option, the main justification |
   | Why does this need my input? | the original goal, the discovery, the judgment or authorization needed |
   | What changes? | current or agreed behavior against proposed behavior, including any deviation |
   | What am I accepting? | benefit, main downside, who and what is affected, how reversal actually works |
   | What supports the recommendation? | verified evidence, material uncertainty, assumptions, what would change the recommendation |
   | What happens when I choose? | the strongest alternative, the consequence of declining or deferring, the exact action approval authorizes |

6. **Deliver.** Plain text is canonical; a dialog rendering derives from it.
   Mechanics, the dialog mapping, and reply handling are in
   `references/delivery.md`.
   - The brief goes in the message body as ordinary text, never wrapped in a
     code fence. Tables use pipes. Code and pseudocode sit inside fences; a
     short ASCII diagram may sit inline, a long one goes in a fence.
   - The brief is the final content of its turn, with no tool call after it,
     and the question dialog opens the next turn on the reader's reply, because
     prose in the same turn as a dialog may never render. One exception: a T1
     whose whole text fits inside the dialog may open with the dialog. If the
     reader's reply already answers, no dialog is raised.
   - Every option stands alone in case the brief is lost: the label names the
     outcome, the description carries the consequence.
   - At most three independent T1 or T2 questions share one message, each with
     its own ID and recommendation; a T3 always goes alone; coupled questions
     state the dependency and are asked in order.

7. **After the answer.**
   - Restate the decision with its ID, option, and date.
   - A condition ("A, but behind a flag") is applied to the chosen option and
     repeated back in one line. A redirect ("check X first") is done first,
     then the question is re-asked, reframed if the work changed it. A skip
     parks the question and, when the run cannot wait, triggers the silence
     default stated in the ask.
   - When the reader says they do not understand, re-ask with a concrete
     example, never a restatement.
   - Retain a decision record when at least two of these hold: hard to reverse,
     surprising without its context, the result of a real tradeoff. The
     template and where it lives are in `references/decision-record.md`.
   - Sweep everything that persists for the rejected option's name and any
     stale claim. When several questions are live, keep one tally line: open,
     decided, skipped, redirected.

8. **Pre-send check.** Send only when every line holds:
   - The reader can identify the work and state the exact decision and
     commitment without reopening the plan or the conversation.
   - The recommendation follows visibly from the evidence and the project's
     priority, and the ask says what would change it.
   - For a non-obvious mechanism, the reader can see the failure and why the
     change addresses it, with identical inputs across the comparison.
   - Every consequence or uncertainty that could change the answer is in the
     initial view; verified, inferred, assumed, and not verified are told
     apart; reversibility is described as actual effects, not "revert the
     commit".
   - Remove each sentence in turn: if the decision is no harder, cut it. The
     brief is under its tier's cap; every reading after an artifact is one
     sentence; each option consequence and each evidence label is one clause.
     No placeholder text left to fill in later; no hedge words such as "should",
     "probably", "seems" standing in for a statement of what was not verified.
   - Every question and option carries its ID; the recommended option is listed
     first; every option label is a verb phrase naming its outcome; alternatives,
     conditions, and the next action are explicit.
   - The brief passes the four ISO 24495-1 outcomes: relevant, findable,
     understandable, usable.
   - The text is ASCII only, with no HTML and no rendered-diagram notation.

## The brief: canonical text form

The question line always comes first. Sections that the tier does not need are
omitted, never left empty. The fence below only quotes the template; the brief
itself is sent as ordinary message text. `references/worked-examples.md` renders
it at every tier: 1 the gate saying no, 2 a T1 merge, 3 a T2 scope deviation
with a same-input table, 4 a T3 race with an event table, 5 a T3 architectural
direction with a coded diagram and a record, 6 a T3 one-line change with a
policy consequence, 7 a T3 algorithm for an unfamiliar reader, 8 a T2 with
identifiers that must be defined. Read the one closest to the situation.

```
Q1. <The decision as one full sentence naming the thing>   [T2: departure, uncertainty]
Recommendation: Q1.A, <what and why in one sentence>. Q1.B wins if <condition>.
Sized by your standing preference: <the preference>.        (only when one applied)

Why I am asking: <two or three sentences: the agreed baseline, the new
  finding, the judgment needed now; for a required gate, the rule and where
  it lives>.
What changes: <one or two sentences, or the representation from step 4 when
  the change type needs one: current or agreed behavior, then proposed>.
What you would be accepting: <one sentence each: benefit; main downside; who
  and what is affected; what reversal actually involves>.
Evidence: Verified: <what, on which revision or environment>. Inferred: <what,
  from what>. Assumed: <what>. Not verified: <what, and why not>. <One clause
  each; omit a label that has nothing under it.>
Options:                                                <consequence: one clause, about 15 words>
  Q1.A  <Verb phrase naming the outcome> (Recommended)  -- <what it causes>
  Q1.B  <Verb phrase naming the outcome>                -- <what it causes>
  Q1.C  <Verb phrase naming the outcome>                -- <what it causes>
Would change my recommendation: <one sentence: the evidence, constraint, or preference>.
On Q1.A I will: <the exact action>. <What approval does and does not authorize.>
If I hear nothing by <when>: <the most reversible option>, because <reason>.
Record: retained as Decision Q1 in <where> once you answer.   (only when due)
Details: <paths to the diff, logs, test output, or traces>.
```

Rendering by tier:

- **T1** keeps the question line, the reason for the gate, the recommendation,
  and the options with their consequences. Two or three sentences. Example:
  `Q1. Merge PR #142, the keyboard-focus fix for the search dialog? [T1] It
  implements the approved change; the keyboard-interaction test and required
  checks passed on revision 9c8d7e6; CONTRIBUTING.md requires a human merge
  approval. Recommendation: Q1.A.` then `Q1.A Merge (Recommended) -- the fix
  ships on the next deploy` and `Q1.B Hold -- the PR stays open; say what to
  change`. The runner-up clause and the "On Q1.A I will" line are required
  whenever tradeoff complexity is above low, and may be omitted at T1.
- **T2** renders the question line, the recommendation with its runner-up
  clause, the sections its elevated axes call for, the options, what would
  change the recommendation, and the next action; the comparison table when the
  change is conditional.
- **T3** renders every section, the representation from step 4, and the
  details pointer when supporting material exists.
- `If I hear nothing by <when>` appears at any tier only when the run cannot
  wait: the human said to continue unattended, or a scheduled step would be
  missed. It names the deadline the ask itself sets, such as "the next
  scheduled run" or "30 minutes". Its option is always the most reversible one,
  never the recommended one when they differ, and never one that expands
  scope, merges, or deploys. In an attended session the line is omitted and
  the run stops.

The recommendation line names the runner-up and the condition under which it
wins. When the tradeoff is genuinely neutral, say so and name the preference that
would settle it; never fake a lean. The recommendation reveals the objective it
optimizes, and the reader can still reject it or add a condition.

## IDs and the reply grammar

Questions are numbered `Q1`, `Q2`, and the numbers continue across the whole
run, so `Q3` means the same decision in every later message. After a context
reset, resume from the highest number visible in the conversation or the
record, and say so. Options are lettered `Q1.A`, `Q1.B`, `Q1.C`. The
recommended option is listed first and is therefore always `A`, so a bare "A"
reply means "go with your recommendation". An answered question keeps its ID as
the key of its decision record and shows one of four states: open, decided
with its option, skipped, or redirected.

Replies the ask must accept, in any wording:

| Reply | Meaning | What you do |
|---|---|---|
| `A`, `Q1.A` | pick | proceed with the named option |
| `Q1.B, but <condition>` | pick with a condition | apply the condition to the option, restate both in one line, proceed |
| `Q1: skip` | park it | continue on the stated silence default or stop; the question returns later |
| `Q1: ask <question>` | need information first | answer it, then re-ask |
| `Q1: do <X> first` | redirect | do X, re-ask, reframed if X changed the question |
| a reply naming an option not offered | the option set was wrong | add it as `Q1.D` with its consequence, confirm in one line |
| "I don't get this" | the ask failed | re-ask with a concrete example |

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

## Self-contained references

Every statement is understandable from its own wording and the visible text
around it. Use a meaningful description first and attach the identifier for
navigation: "the database migration that stores queued jobs (Task 1)", never
"Task 1". Define task numbers, phases, option letters, and unfamiliar component
names on first use in each message. Reuse shorthand only while its definition is
still visible. Give every bullet and table row enough words to stand alone. Use
the reader's own names for things and attach the technical name in code font:
"the confirm card (`ApprovalGate`)". Pair every verbatim technical name with a
short role phrase at first use, reproduce it exactly, and never edit text the
reader must type, match, or search. Replace invented local metaphors with literal
wording. Give every number its unit, its date, and its source.

## Red Flags

| Thought | Reality |
|---|---|
| "The user knows the plan; 'Approve Phase 2?' is enough" | The reader was not watching. Describe the thing, then attach the ID. |
| "It is a quick yes or no" | Yes and No hide the consequence. Options name what happens: "Merge" and "Hold". |
| "I will assume yes and keep going" | Nothing is authorized by silence except the reversible default the ask itself declared, with its deadline. |
| "Tests pass, so the decision is safe" | Passing tests reduce uncertainty. They do not reduce impact, recovery cost, or the need to understand the mechanism. |
| "More context is safer" | Depth is set by the highest axis and spent only on that axis. Unrelated background hides the decision. |
| "I will put the brief in the same turn as the dialog" | Same-turn prose may never render. The brief ends its turn; the dialog opens the next. Only a T1 that fits inside the dialog skips the delivering turn. |
| "A diagram would look thorough" | Show only what changes the answer, in the smallest ASCII form, framed. Decoration is noise. |
| "The label is short, the trade-off is in my head" | Every option stands alone with its consequence, in case the brief is the part that never rendered. |
