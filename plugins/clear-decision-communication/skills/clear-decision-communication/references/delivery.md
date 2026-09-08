# Delivery: plain text, the dialog rendering, and replies

How the brief reaches the reader and how their reply comes back. Read this at
workflow steps 7 and 8, after the pre-send check.

## Plain text is canonical

The brief in its canonical text form is the message. It works in any chat, in a
terminal, in a pull request comment, and on tools that have no question dialog.
Authored prose and diagram syntax use ASCII. Verbatim paths, identifiers,
input data, quotations, and captured output keep their exact characters,
including non-ASCII text. Do not produce an HTML artifact or a rendered diagram.
Where a suitable question tool exists and is permitted, derive its payload from
the brief; the tool's field layout does not decide which facts the reader needs.

The brief is ordinary message text: no surrounding code fence, pipe tables,
bold only on the section labels if the surface renders it. Code and pseudocode
sit inside fences; diagrams use fences whenever alignment requires them.

## Adapt to the host

Inspect the question tools actually exposed in the session. Availability can
vary by product, mode, and version; neither "Claude" nor "Codex" is a schema.
Follow the host's limits, permission rules, and instructions about required
versus optional questions. Do not call a Plan-only tool outside Plan mode, or
use an information-question tool for permission when the host forbids it.

Put the decision, necessary context, consequences, uncertainty, and exact
approval scope inside the payload the reader will see. Accompanying prose may
not render. Every option carries its ID, outcome, and consequence. If a field
is unavailable, combine its content into a supported field instead of sending
an invented argument. If the tool cannot carry essential information, use
ordinary text; never truncate a material caveat to fit the tool.

These are adaptation examples, not fixed cross-product schemas:

| Available shape | Mapping from the brief |
|---|---|
| `AskUserQuestion` with header, question, labels, and descriptions | Put the ID and subject in the header within its declared limit; put all necessary context in the question; pair each consequence with its option. Use `multiSelect` or previews only if that schema supports them and they fit the decision. |
| `request_user_input` with question objects | Follow its current limits and mode restrictions. Use its question and option-description fields; do not assume it supports four options, previews, or `multiSelect`. |
| `request_user_input_async` with `title` and string `options` | Put the self-contained question in `title`; put each ID, outcome, and consequence in one option string. Continue independent authorized work while the question remains pending. |
| No suitable or permitted question tool | Send the ordinary-text brief and obtain the answer in conversation. |

When a recommendation is supported, A is first and marked `(Recommended)`.
When neutral, explain what preference separates the options and omit the marker
and any `Recommended: A.` text. If the host requires a recommendation that the
evidence does not support, use the ordinary-text form instead of inventing one.
Do not add an Other option when the host already supplies free text.

Some interfaces preselect an option automatically. A highlight or preselection
is not a submitted answer. Never submit on the user's behalf or interpret a
tool return without an answer as consent. Required input remains pending;
optional clarification follows the host's rules and existing authorization.

## When the two-turn rule is needed

Use this fallback on a surface known to lose same-turn prose when necessary
context cannot fit in the question dialog:

1. End the delivering turn with the complete ordinary-text brief and no later
   tool call. It must already be answerable in conversation.
2. Interpret the reader's reply first. A valid answer needs no second dialog;
   an information request gets an answer. Raise a dialog in the next turn only
   if a choice is still needed and the host allows that rendering.

Do not impose this extra turn on a self-contained dialog or on an asynchronous
question tool that already displays the complete brief. Pause dependent work
until the required answer arrives; continue other work under existing authority.

## Batching

- At most three independent T1 or T2 questions share one message. Each has its
  own ID, options, and supported recommendation or explicit neutrality. Each
  stands alone. The host may impose a smaller batch or a one-question limit.
- A T3 always goes alone.
- Coupled questions state the dependency and are asked in order: a question
  whose answer depends on another still open waits for the next message.
- A tally line precedes a batch or follows an answer when more than one
  question is live: `Q1 decided (A), Q2 open, Q3 skipped, Q4 superseded by Q5.`

## The silence default

When the human requested unattended work or a scheduled step needs an explicit
fallback while waiting, the ask may end with the line
`If I hear nothing by <when>: <option>, because <reason>.` The deadline is set
by the ask itself, such as "the next scheduled run" or "30 minutes", and the
fallback is eligible only once it passes. It may pause, defer, or perform work
already authorized before the ask; cite that authorization when it permits an
action. Stating a default or deadline creates no authorization and never
satisfies an approval gate. Choose the most reversible eligible option; never
expand scope, merge, or deploy under this fallback. If no action is already
authorized, the fallback is to leave the gated action pending. In an attended
session omit the line and wait on dependent work.

"Skip" and "not now" park the question. They do not select its fallback or
advance its deadline. Do not fire the question's fallback while it is skipped;
continue only independent work already authorized.

## Replies

Accept the reply in any wording and match it to one open question with unchanged
options. A bare letter is sufficient only when it unambiguously identifies one
live choice. When a batch, a quoted old brief, or multiple open questions makes
the mapping unclear, ask which question was meant in one line; do not act yet.

| Reply | Meaning | Handling |
|---|---|---|
| `A`, `Q1.A`, "go with your recommendation" | pick | validate the live question and unchanged option, restate `Q1: decided A, <date>`, then proceed; the recommendation phrase is not a choice on a neutral question |
| `Q1.B, but <condition>` | pick with a condition | restate the conditional action; when action or approval scope changes, record the clearly authorized revised decision under a new ID with Q1 as history, without asking again; clarify only an unresolved commitment |
| `Q1: skip`, "not now" | park | mark skipped without selecting its fallback or advancing its deadline; continue only independent authorized work |
| `Q1: ask <question>` | information needed first | answer with facts and reassess; keep the ID only if options, recommendation, and scope are unchanged, otherwise supersede it before asking for the revised choice |
| `Q1: do <X> first` | redirect | do X within authorization; re-assess, then re-ask only if still needed; supersede the question if its options, recommendation, or approval scope changed |
| a reply to a superseded question | stale answer | explain which current question replaced it; execute neither choice from that reply |
| "I don't get this" | the ask failed | re-ask with a concrete example, never a rephrase of the same sentence |
| a reply naming an option not offered | revised choice | preserve the user's direction under a new question ID, with its consequence and scope; record it directly if the reply already clearly authorizes that action, otherwise clarify only the missing commitment |

A reply that overrides a supported recommendation is recorded as `overrode`;
one that takes it is `followed`. A neutral choice is `no recommendation`.
Do not count neutrality or skipped questions as recommendation overrides.

After any answer, sweep everything that persists, such as pull request text,
a decision record, a plan, or a task row, for any claim the answer made stale.
Keep rejected alternatives and superseded decisions as explicitly labeled
history. A banner over a stale claim about the current plan is not a fix.

## Plain-text form on tools without a dialog

Send the canonical text form. Number the questions, letter the options, and
mark the recommendation only when supported. State a reply grammar using the
actual offered IDs, for example: `Reply with Q1.A or Q1.B, add a condition, or
say skip.` Wait on dependent work and interpret the reply with the table above.
