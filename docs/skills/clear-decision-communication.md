# clear-decision-communication

Composes and delivers a decision request from an agent to a human during a run,
as inline ASCII text. It first decides whether a new decision is needed at all:
facts are read, run, fetched, or delegated and never reach the human as a
question; existing authorization persists; the question must be sharp enough to
state in one sentence; and the agent never fills in the human's answer. It then
sizes the ask by seven diagnostic axes (impact, reversibility, departure from
agreement, uncertainty, tradeoff complexity, domain complexity, context gap)
into three tiers, where the highest single axis sets the tier and only the
elevated axes expand: T1 Confirm in two or three sentences, T2 Compact brief,
T3 Full brief with the representation the change type requires. Representation
is chosen from the change type, not the tier: a same-input table for
conditional behavior, a worked example with its boundary case and invariant for
an algorithm, an event sequence with identical event order for a race, and a
small ASCII system diagram with coded nodes, shown baseline-first with the
change as ghosts, for an architectural move. The brief answers six questions in
a fixed order: the decision and recommendation first, then context, the
comparison or example, consequences with verified, inferred, assumed, and
unknown told apart, and the exact action approval authorizes. Questions are
numbered `Q1`, `Q2` across the whole run and options lettered `Q1.A`, `Q1.B`,
so a reply is one word; the recommended option is listed first and is always A,
and the recommendation line says when the runner-up would win; every option is
a verb phrase naming its consequence; when the run cannot wait, a silence
default names the most reversible option, never the recommended one. Plain text
is canonical and a question-dialog rendering is derived from it, with the brief
ending its turn before the dialog opens because same-turn prose may never
render. Replies with conditions, skips, redirects, and ask-backs are handled; a
reader who says "I don't get this" gets a concrete example, not a rephrase; and
a decision that is hard to reverse, surprising without context, or the result
of a real tradeoff is retained as a record keyed by its question ID. The skill
is self-contained by design: it synthesizes a decision-communication framework
with the clarity rules of `clear-technical-communication`, the two standards
behind them (ISO 24495-1 for the brief as a whole, ASD-STE100 for its
sentences), and the text forms of `show-me` inside its own files, names no other skill in its body, and never
produces HTML or rendered diagrams, so a downstream tool can render its text.

**Triggers on:** the moment an agent is about to ask the user to choose,
approve, merge, deploy, or accept a deviation, before any question dialog is
raised; "ask me properly", "frame this decision", "what do you need me to
decide", "turn this into a decision". It does not review someone else's draft
(`clear-technical-communication`), walk a whole pile of questions
(`question-walkthrough`), or produce pages or HTML (`html-codesign`).
**Arguments:** optional `[target]`: a pasted question, a draft ask, a pull
request, or a diff to turn into a decision request.

## Install

| Mode | When | How |
|---|---|---|
| Plugin (recommended) | You just want to use it | `/plugin install clear-decision-communication@smorinlabs-harness` |
| Dev symlink | You want to tweak/iterate | `git clone https://github.com/smorinlabs/smorinlabs-harness` then `ln -s "$(pwd)/smorinlabs-harness/plugins/clear-decision-communication/skills/clear-decision-communication" ~/.claude/skills/clear-decision-communication` |
| Direct copy | No marketplace access | copy `plugins/clear-decision-communication/skills/clear-decision-communication/` into `~/.claude/skills/` |

**Codex:** register the marketplace in `~/.codex/config.toml`
(`[marketplaces.smorinlabs-harness]`) and enable the plugin — or use the
dev-symlink path, also linking into `~/.agents/skills` (Codex's current
skills location). On Codex there is no question dialog; the skill sends its
canonical plain-text form and reads the next message as the answer.

## Example session

> An agent fixing CSV date validation finds the clean fix lives in a shared
> validator that API uploads also use.
> → The gate fires (a departure from the agreed scope, and caller
> compatibility cannot be verified from the repository), the sizing tag reads
> `[T2: departure, uncertainty]`, and the agent sends a compact brief: the
> question line first, "Recommendation: Q1.A, include it ... Q1.B wins if
> existing external caller behavior must be preserved", a same-input table
> showing `2024-02-30` corrected today and rejected with the fix on both
> paths, what accepting means for API callers, "Verified: regression tests pass
> on commit 3f2a9c1. Not verified: third-party caller compatibility", three
> lettered options each naming its consequence, what would change the
> recommendation, and the exact action on approval. The user replies "A, but
> behind a flag for the API"; the agent restates "Q1: decided A with the
> condition: API path flag-gated, default off" and proceeds.

## Files

| File | Role |
|---|---|
| `SKILL.md` | the gate, the tier table, the change-type table, the six questions, the canonical brief template, IDs and reply grammar, confidence statuses, the pre-send check |
| `references/axes-and-tiers.md` | the seven axes verbatim, level tests, the tier rule, stage-of-work guidance |
| `references/representation.md` | the ASCII forms catalog and the diagram rules |
| `references/clarity.md` | reader gates, sentence and term controls, the error catalog |
| `references/standards.md` | ISO 24495-1's four reader outcomes and the selected ASD-STE100 mechanics, their sources, limits, and the operational rubric |
| `references/delivery.md` | the two-turn gate, the dialog mapping, batching, the silence default, reply handling |
| `references/decision-record.md` | when a record is due and its template |
| `references/worked-examples.md` | eight fictional situations rendered at every tier; also the test suite |
| `references/framework.md` | the source framework verbatim and the provenance of every borrowed passage |

## Provenance

The skill is a synthesis. Its own framework was written by Steve Morin on
2026-09-07. Borrowed passages, all attributed in `references/framework.md`:
the clarity rules from `clear-technical-communication` (Steve Morin); the text
forms from `show-me` (humanlayer/skills, MIT); the question form, the
facts-are-the-agent's-job rule, and bounded batching from `grilling`
(mattpocock/skills, MIT); the what-resolves-it classifier, the sharpness test,
and the never-answer-for-the-human rule from `wayfinder` (mattpocock/skills,
MIT); the visual budget, ghost convention, code-plus-name labels, record
significance test, and stale-word sweep from `system-atlas`
(inkboard/system-atlas, MIT); cited guidance from Nielsen Norman Group,
Google's engineering practices, and AWS prescriptive guidance on architectural
decision records.

## Deliberate deviations from the fleet house style

Recorded so the quality gate's findings on them are read as accepted:

- No "See also" section and no reference to any other skill in the body, at
  the owner's instruction; the skill must stand alone.
- Content duplicated from sibling skills rather than delegated, for the same
  reason; attribution lives here and in `references/framework.md`.
- Accepted trigger overlap with three third-party prompts that cannot be edited: `superpowers:brainstorming` (the design-approval gate before implementation), `superpowers:executing-plans` (when to stop during plan execution), and the `learning-output-style` hook (decision points as teaching moments). This skill owns how an in-run ask is composed and delivered; those own when their own gates fire.
- A permissive tools grant (`Bash`, `Agent`, `WebFetch`, `WebSearch`) so the
  preparation step can execute what it needs to gather evidence; the body
  bounds it to information gathering within the run's existing authorization.
