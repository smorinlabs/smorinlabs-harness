---
name: clear-technical-communication
description: >
  Make technical communication reader-centered, explicit, and actionable by minimizing what the reader must infer. Use when the user says "make this draft clearer", "this message is not understandable", "rewrite this technical message", "review this for clarity", or "make this decision request actionable"; and proactively before sending dense artifacts such as design summaries, plans, status reports, handoffs, comparisons, or owner-decision requests. Detects missing purpose/context, undefined terms/IDs/notation, hidden logic, mixed status, false choices, absent consequences, wrong presentation form, stripped or unexplained names, and unframed code, diagrams, or examples; rewrites without inventing facts. Apply aggressively when a reader would reconstruct the author's mental model. Not for teaching the underlying subject (`explain`), interactive form design (`design-by-elements`), walking decisions (`question-walkthrough`), or reader-only task blocks (`reader-steps`).
arguments: [target]
argument-hint: "[target]"
allowed-tools: Read, Grep, Glob, AskUserQuestion, Bash(git diff:*), Bash(git log:*), Bash(git show:*)
---

# clear-technical-communication

Review, rewrite, or compose technical communication so its intended reader can
understand and use it without reconstructing omitted context.

> **MINIMIZE WHAT THE READER MUST INFER.** State the purpose, supply required
> context, define local terms, expose relationships, and name the action. Never
> make the reader reverse-engineer the author's mental model.
>
> No exceptions: domain expertise does not excuse undefined local shorthand;
> short sentences do not repair missing context; punctuation is not a
> substitute for logic; and asking the owner questions does not excuse absent
> analysis. Violating the letter is violating the spirit.

## Workflow

1. **Locate the actual communication.** Use the text in the conversation. If
   the user points to a file, diff, commit, or report, read that artifact rather
   than inventing a representative example.
2. **Identify the reader's job.** Infer the intended reader, what they know,
   why they are reading, and what they must understand, decide, or do. Ask one
   question only when a missing answer would materially change the rewrite. If
   credible candidates exist, use `AskUserQuestion`; otherwise identify the
   missing input as a gap.
3. **Classify the message.** Choose explanation/summary, comparison, status or
   handoff, procedure, or decision request. Split a message that tries to do
   several of these at once.
4. **Run the aggressive error scan.** Read
   `references/common-errors.md`. Check every applicable failure, not only
   sentence length or vocabulary. Quote the smallest evidence that proves each
   finding.
5. **Apply the four reader gates.** A message must be:
   - **Relevant:** it contains what this reader needs and excludes process
     chatter.
   - **Findable:** the outcome, decision, or action is easy to locate.
   - **Understandable:** terms, references, relationships, and status are
     explicit.
   - **Usable:** the reader can reach the intended conclusion, decision, or
     next action.
6. **Choose the form that exposes the structure.** Use prose for a short causal
   chain and a list for parallel items. Treat three or more items with shared
   fields or dimensions as a strong signal to consider a table; use one when
   it materially improves comparison. Use a code block, command, or quoted
   output when the exact form of an input, signature, invocation, or result is
   what the reader needs; a short snippet is often the most precise and
   lowest-inference statement of a behavior available. Use a text diagram when
   the reader must hold three or more relationships at once; two components and
   one arrow is a sentence, so write the sentence. Do not encode a matrix or
   repeated multidimensional comparison inside a paragraph, and do not describe
   in prose a call, signature, or output that could be shown exactly. See
   `references/artifact-forms.md` for the diagram catalog and selection rule.
7. **Rewrite, do not merely criticize.** Preserve technical meaning and
   necessary domain terms. Define local terminology and identifiers. Make
   causal links explicit. Move essential constraints out of parentheses.
   Mark missing analysis with a precise gap; never manufacture facts, options,
   effects, or recommendations.
8. **Cold-read the result.** Confirm that a reader can answer after one pass:
   - What is this about?
   - Why does it matter now?
   - What is known, proposed, estimated, assumed, or unresolved?
   - What conclusion or action follows?
   - For a decision, what happens under each option?

If any answer depends on reconstructing earlier conversation or decoding local
notation, revise again before sending.

## Output contract

### Reviewing existing communication

Lead with the rewritten communication when the user's goal is a usable draft.
Then give only the diagnostic detail that helps future writing:

1. **Evidence** — the exact phrase or structure that failed
2. **Problem** — the named communication error
3. **Prescriptive rule** — what to do in future
4. **Correction** — the concrete before-and-after change
5. **Unresolved gap** — only when the source lacks facts needed for a sound
   rewrite

Do not return a readability score or generic advice such as "simplify this."

### Composing new communication

Return the communication first. Do not narrate the drafting process. Add a
short assumptions or gaps section only when it changes how the reader should
use the result.

## Message templates

### Explanation or technical summary

1. Outcome or central point
2. Necessary context
3. Mechanism or relationships
4. Concrete example
5. Consequence or requested action

Use `explain` instead when the problem is understanding the underlying subject
rather than repairing the communication artifact.

### Comparison

State the comparison question first. Use stable row and column labels. Define
all dimensions and baseline values before showing their combinations. State
the conclusion after the table.

### Status or handoff

1. Outcome and current state
2. Evidence for that state
3. Completed work
4. Blockers or unresolved gaps
5. Next action and owner

### Decision request

Every decision request contains:

1. **Context and why now**
2. **Evidence or constraint** that creates the decision
3. **Decision** as one explicit question
4. **Options** that are genuinely available
5. **Effects** of each option: behavior, cost, and risk where applicable
6. **Recommendation** with rationale
7. **Response needed** in an exact form

Research what can be resolved. Bring the reader only genuine owner decisions.
Do not write "only you can answer" until the evidence shows that policy,
preference, or authority—not missing author analysis—is the remaining input.

If several decisions remain, give each the same labeled structure. The
`question-walkthrough` skill owns conducting those decisions one at a time.

### Procedure or manual handoff

Put prerequisites before actions. Give one primary action per step and state
how success is observed. When the actions can only be performed by the reader,
defer the final rendering to `reader-steps`.

## Show exactly, and say what it means

> **Every embedded artifact carries a frame.** The artifact supplies precision;
> the prose supplies meaning. Neither ships alone.

An artifact is every literal the message embeds: a name, a code block, a
command, a configuration snippet, quoted output, a table, and a diagram. A
diagram dropped in with no prose stating why it is present fails the reader in
the same way as a bare `--ff-only`, at a different scale.

| Part of the frame | Answers | Example, for a diagram |
|---|---|---|
| Lead-in — why it is here | What question does this answer? | "Where does the request pipeline block?" |
| The artifact — exact, unedited | — | the diagram |
| The reading — what to see | What is the takeaway, and so what? | "The queue is the only unbounded stage, so that is where memory grows." |

The frame scales with the artifact. A short name collapses all three parts into
one sentence: ``Use `--ff-only`, the flag that makes `git pull` refuse any
update that is not a fast-forward.`` A diagram or a twenty-line configuration
gets three separate pieces. The frame is never satisfied by the artifact alone,
at any size.

Classify every term before deciding what to do with it.

| Class | Examples | Rule |
|---|---|---|
| Verbatim technical name | `Promise.allSettled`, `--ff-only`, `ENOTEMPTY`, `~/.claude/settings.json`, `UserAccountRepository` | Reproduce it exactly, in code font. Never paraphrase, shorten, or replace it with a description. Pair it with a description at first use in prose. |
| Established domain term | idempotent, fast-forward, backpressure | Keep the term. Define it at first use, then use it consistently and freely. |
| Invented local metaphor | `tombstone`, `ladder`, `slug` | Replace it with literal wording, or coin it explicitly as a defined term when it earns reuse. |

### Pair every name with a description at first use

Give both the name and what it means. Do not judge whether this reader already
knows the name.

- `Use --ff-only.` → ``Use `--ff-only`, the flag that makes `git pull` refuse
  any update that is not a fast-forward.``
- `The fix is in UserAccountRepository.` → ``The fix is in
  `UserAccountRepository`, the class that loads and persists account records.``

The rule has a mechanical boundary:

- It applies at the name's first occurrence in running prose within one
  independently consumable unit: a chat message, a page, or a document a reader
  may reach by deep link. It is not scoped to a heading, which would repeat the
  gloss endlessly, nor to a whole multi-page document, which would leave a
  deep-linked reader without the description.
- Later occurrences in that unit need no further description.
- It does not apply to tokens inside a code block, command, or quoted output.
  Frame the block as a whole; do not gloss its individual tokens.

The rule bounds the cost of a description, never the obligation:

- A short role phrase satisfies it. ``` `SIGKILL` (forced termination) stopped
  PID 8421 ``` is compliant; a full definition that delays the point is not
  required and usually harms an expert reader.
- One shared gloss may cover a group of parallel names. ``` The configuration
  pipeline — `parseConfig`, `validateConfig`, and `writeConfig` — now preserves
  comments ``` is compliant. Glossing each name separately buries the change.

### Never edit verbatim zones

Text the reader must type, match, or search is reproduced character for
character: commands, flags, paths, identifiers, configuration keys, error
messages, and log output. Clarity edits stop at the boundary of a code span or
block.

- Do not expand shorthand inside quoted text. An error reading `e.g. missing
  arg` stays exactly that.
- Do not correct style inside a value. `A + B` in prose is rewritable; the
  value `--filter=A+B` is not.
- When quoted text is itself unclear, quote it exactly and explain it outside
  the quotation.

For the diagram catalog, annotation markers, before-and-after pairs,
counterexamples, and units with reference scale, read
`references/artifact-forms.md`.

## Sentence and terminology controls

- Use one primary assertion per sentence. Treat approximately 25 words as a
  review signal, not a pass/fail definition of clarity. Code spans,
  identifiers, paths, and quoted output count as one word each toward this
  signal.
- Use literal verbs and consistent terms. Replace avoidable noun piles with an
  actor and an action.
- Keep necessary technical terms, but define unfamiliar local meanings at
  first use.
- Gloss identifiers where they first appear: `REQ-26 (pre-0.95 fallback
  requirement)` rather than bare `REQ-26`.
- Label every symbolic value, tuple, axis, and operator. Do not use `+`, `x`,
  `@`, or `/` as prose unless the notation is defined.
- Repeat the exact noun when a pronoun can refer to more than one thing.
- State causal and contrastive relationships with words such as "because,"
  "therefore," and "but," or with separate labeled fields.
- Reserve parentheses for optional information. Essential constraints belong
  in main sentences.
- In formal technical communication, avoid contractions, Latin abbreviations,
  and conversational shorthand when they could slow or confuse the reader.

For the standards behind these controls and their limits, read
`references/standards-and-rubric.md`. Do not claim formal ASD-STE100 compliance
unless the user explicitly requests a full compliance pass.

## Common errors reference

`references/common-errors.md` is the canonical catalog of common failures,
detection signals, corrections, and compact examples. Read it:

- for every explicit clarity review or rewrite;
- before sending a dense technical explanation, comparison, handoff, or
  decision request;
- when a draft contains three or more local identifiers, several dimensions,
  or multiple unresolved decisions;
- when a user says the communication is confusing but cannot name why.

For calibrated full rewrites of a multidimensional coverage explanation and a
three-decision owner request, read `references/worked-examples.md`.

## Red Flags

| Thought | Reality |
|---|---|
| "The reader is technical; shorthand is fine" | Domain knowledge does not include the author's local IDs, metaphors, or tuple order. Define them. |
| "Shorter means clearer" | Removing required context creates lossy compression. Minimize inference, not word count. |
| "The semicolon shows the relationship" | Punctuation separates clauses; it does not name cause, contrast, scope, or consequence. |
| "The owner can choose once I list the questions" | A usable decision request also supplies evidence, effects, and a recommendation. |
| "A paragraph is more concise than a table" | Repeated fields and dimensions hidden in prose are harder to compare and easier to misread. |
| "I cannot rewrite until every fact is known" | Rewrite what is supported and label the exact remaining gap without inventing it. |
| "Plain language means avoiding jargon" | Plain language means minimizing inference, not removing precision. Give the exact name and its description together. |
| "A code block is not plain language" | A snippet is often the plainest possible statement of a behavior, because it removes the reader's need to reconstruct it from prose. |

## See also

- `explain` — teach or clarify the underlying subject with a concrete example.
  A snippet or diagram in this skill is a precision device: it states exactly
  what prose would approximate. Examples used to teach the underlying subject
  belong to `explain`.
- `design-by-elements` — iteratively prototype the visual or textual form of
  an artifact.
- `question-walkthrough` — conduct a pile of open decisions one at a time.
- `reader-steps` — render actions only the reader can perform.
