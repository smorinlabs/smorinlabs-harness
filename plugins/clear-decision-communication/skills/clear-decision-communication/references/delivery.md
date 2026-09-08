# Delivery: plain text, the dialog rendering, and replies

How the brief reaches the reader and how their reply comes back. Read this at
workflow steps 6 and 7.

## Plain text is canonical

The brief in its canonical text form is the message. It works in any chat, in a
terminal, in a pull request comment, and on tools that have no question dialog.
It is ASCII only, with no HTML and no rendered-diagram notation, so that any
downstream tool can render it without parsing prose. Where a question dialog
exists, a dialog rendering is derived from the text; the text is never derived
from the dialog.

The brief is ordinary message text: no surrounding code fence, pipe tables,
bold only on the section labels if the surface renders it. Code and pseudocode
sit inside fences; a short ASCII diagram may sit inline, a long one goes in a
fence; nothing else does.

## The two-turn gate

Prose in the same turn as a question dialog may never render: when a turn ends
in a tool call, the reader can receive only the dialog. This has been confirmed
repeatedly in the field. Two rules follow, one per turn:

- **The delivering turn.** The brief is the turn's final content, with no tool
  call of any kind after it. Wanting to call a tool after the brief is the
  violation signal; that call opens the next turn instead. The reader's reply
  ("go", a question back, a correction) is what proves the brief was in hand.
- **The asking turn.** A turn that raises the dialog contains no prose the
  reader needs. Anything they must read either ended the previous turn or lives
  inside the dialog itself: the question body, the option labels, the option
  descriptions.

Because the brief may still be lost, every option stands alone: the label names
the outcome, the description carries the consequence, and a reader who saw only
the dialog can still choose safely. "Generate the page for these 4" beats "Yes".

The reader's reply starts the asking turn: a reply of "go" or a question back
opens the turn that raises the dialog, and a reply that already answers means
no dialog is raised at all. A T1 is small enough that its whole text fits
inside the dialog: its question line with the tag and its reason for the gate
become the question text, its options become the labels and descriptions. It
may skip the delivering turn only when the turn carries nothing else the reader
must read. When in doubt, deliver first.

## The dialog rendering

| Dialog field | Taken from the brief |
|---|---|
| header (12 characters or fewer) | `Q1` plus one word for the subject: `Q1 scope`, `Q2 merge` |
| question text | the question line with its tag, then `Recommended: A.`; at T1 also the one or two sentences that give the reason for the gate |
| option labels (2 to 4) | `A. <label> (Recommended)`, `B. <label>`, ... ; the ID is inside the label because labels are the one channel that always renders |
| option descriptions | the "what it causes" text of each option, one or two sentences, carrying the trade-off |
| multiSelect | true only when options can genuinely be combined; mutually exclusive choices use false |
| Other | automatic; never add an "Other" or "none of these" row |
| preview | when options are concrete artifacts such as code shapes or formats |

Limits of the channel: one to four questions per dialog call, two to four
options per question, a short header. A decision with more than four options is
under-shaped: split the question or pre-filter, never truncate.

Never give a dialog a default answer, and never pre-select. The recommendation
is stated; the choice is the reader's.

## Batching

- At most three independent T1 or T2 questions share one message. Each has its
  own ID, its own options, and its own recommendation, and each stands alone.
- A T3 always goes alone.
- Coupled questions state the dependency and are asked in order: a question
  whose answer depends on another still open waits for the next message.
- A tally line precedes a batch or follows an answer when more than one
  question is live: `Q1 decided (A), Q2 open, Q3 skipped, Q4 redirected.`

## The silence default

The run cannot wait when the human said to continue unattended, or when a
scheduled step would be missed while waiting. Then the ask ends with the line
`If I hear nothing by <when>: <option>, because <reason>.` The deadline is set
by the ask itself, such as "the next scheduled run" or "30 minutes", and the
default fires only once it passes. The option is always the most reversible
one, never the recommended option when the two differ, and never an option that
expands scope, merges, or deploys. Nothing else is authorized by silence. In an
attended session the line is omitted and the run stops.

## Replies

Accept the reply in any wording and map it to one of these; when the mapping
is unclear, ask which was meant in one line.

| Reply | Meaning | Handling |
|---|---|---|
| `A`, `Q1.A`, "go with your recommendation" | pick | restate `Q1: decided A, <date>` and proceed |
| `Q1.B, but <condition>` | pick with a condition | apply the condition to the option; restate option and condition in one line; proceed |
| `Q1: skip`, "not now" | park | mark skipped; continue on the silence default if one was stated, otherwise stop; the question returns in the next ask on the subject |
| `Q1: ask <question>` | information needed first | answer with facts, then re-ask the same question |
| `Q1: do <X> first` | redirect | do X; re-ask, reframed if X changed the question or mooted it |
| "I don't get this" | the ask failed | re-ask with a concrete example, never a rephrase of the same sentence |
| a reply naming an option not offered | the option set was wrong | add it as `Q1.D` with its consequence and confirm it in one line |

A reply that overrides the recommendation is recorded as `overrode`; one that
takes it is recorded as `followed`. Both are normal. Over a run, the ratio is
the only calibration signal the reader has about the recommendations.

After any answer, sweep everything that persists, such as pull request text,
a decision record, a plan, or a task row, for the rejected option's name and
for any claim the answer made stale. A banner over a stale paragraph is not a
fix; the reader reads everything.

## Plain-text form on tools without a dialog

Send the canonical text form and stop. Number the questions, letter the
options, mark the recommended one, and end with the reply grammar in one line:
`Reply with A, B, or C, add a condition, or say skip.` The reader's next message
is the answer; map it with the table above.
