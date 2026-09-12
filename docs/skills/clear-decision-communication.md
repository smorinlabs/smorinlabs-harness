# clear-decision-communication

Composes and delivers a self-contained decision request during an agent run.
It checks existing authorization, investigates discoverable facts, and asks
for necessary human-supplied information without turning it into an approval
decision. Silence and skip never grant permission to act.

Seven diagnostic axes determine preparation and explanation: impact,
reversibility, departure from agreement, uncertainty, tradeoff complexity,
domain complexity, and context gap. The highest of the first six sets T1
(Confirm), T2 (Compact brief), or T3 (Full brief); context is restored at every
tier. Verification can lower uncertainty before final sizing. Length targets
prompt editing but never hide material consequences or approval boundaries.

The brief identifies the topic immediately. When the question needs context,
it first connects the user's goal to the exact artifact and its role, the
relevant discovery, and the remaining choice. Current state and immediate
commitment are clear before the options. Planning, implementation, validation,
and activation remain distinct. Tier calculations stay internal unless the
reader requests them.

Representation follows the reader's missing understanding before the technical
change type: an artifact table or project relationship may be needed before a
same-input comparison, worked example, event sequence, or ASCII diagram.
Precise names retain their artifact type and role: a workflow, its job, an
action, a setting, and a credential are different things. Concise references
are welcome after that first definition. Verbatim identifiers and captured
output keep their exact characters, including Unicode. Simplification preserves
each claim's scope, conditions, and uncertainty.

Outcome comparisons keep independent inputs separate. When sources establish
only design rules, the brief compares requirements and leaves unsupported
runtime outcomes unknown. A separate pass checks the completed draft against
its sources, including option consequences and decision records: documented
behavior is distinct from an exercised test, aggregate results stay aggregate,
and missing evidence stays unknown. Measurements name the exact asset, metric,
unit, statistic or denominator, source, and relevant conditions. Comparisons
identify baseline and candidate values, preserve the direction of change, and
distinguish quoted percentages from calculated changes. Missing absolute values
remain explicit gaps.

Questions use IDs such as `Q1`; options use `Q1.A` and `Q1.B`. A supported
recommendation is A and appears first. Neutral questions mark no recommendation.
Options keep their meanings under their IDs; revised choices supersede the old
question, and stale replies authorize no action. Conditions, redirects, skips,
and requests for explanation have explicit handling. Confusion triggers a
diagnosis of missing identity, project context, state, or commitment before
another explanation of the mechanism. If the user replaces an implementation
premise, the agent retires obsolete options and proceeds within the new
authorization. A discoverable fact is not an owner judgment, and account access
does not decide every adopter's credential policy.

The host's available tools determine whether the brief uses a dialog,
asynchronous question, or ordinary text. Independent authorized work can
continue while required input remains pending. A separate delivering turn is
used only on surfaces that need it. Significant decisions retain their
rationale, alternatives, and approval scope when at least two apply: hard to
reverse, surprising without context, or the result of a real tradeoff.

The skill is self-contained. Its references synthesize the owner's framework,
the clarity rules and standards behind `clear-technical-communication`, and
text forms from `show-me`. It produces no HTML artifacts or rendered diagrams.

**Triggers on:** the moment an agent is about to ask the user to choose,
approve, merge, deploy, or accept a deviation, before a decision dialog is
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

**Codex:** install from a terminal with a Codex CLI that supports plugins:

```sh
codex plugin marketplace add smorinlabs/smorinlabs-harness
codex plugin add clear-decision-communication@smorinlabs-harness
```

For development, link the cloned skill into `~/.agents/skills`. Dialog support
depends on the surface and mode. Inspect the actual tool schema:
`request_user_input_async` has exposed `title` and string `options` on one
surface, but that is an example, not a contract for every tool with that name.
`request_user_input` likewise follows its current limits and mode restrictions.
Use ordinary text when no suitable question tool is available or permitted.
Preselection and tool completion without an answer do not count as consent.

## Example session

> An agent fixing CSV date validation finds the clean fix lives in a shared
> validator that API uploads also use.
> → The gate fires (a departure from the agreed scope, and caller
> compatibility cannot be verified from the repository). The agent sends a
> compact brief that first names the shared validator and explains how the CSV
> fix would also change API uploads. It then asks whether to include that
> additional scope: "Recommendation: Q1.A, include it ... Q1.B wins if
> existing external caller behavior must be preserved", a same-input table
> showing `2024-02-30` corrected today and rejected with the fix on both
> paths, what accepting means for API callers, "Verified: regression tests pass
> on commit 3f2a9c1. Not verified: third-party caller compatibility", three
> lettered options each naming its consequence, what would change the
> recommendation, and the exact action on approval. The user replies "A, but
> behind a flag for the API". Because that changes the action's scope, the agent
> records "Q2: decided A, supersedes Q1; API path flag-gated, default off" and
> proceeds under that explicit conditional approval without asking again.

## Files

| File | Role |
|---|---|
| `SKILL.md` | the gate, preparation and final sizing, representations, the brief template, pre-send check, host-aware delivery, stable IDs, and reply handling |
| `references/axes-and-tiers.md` | the seven axes verbatim, level tests, the tier rule, stage-of-work guidance |
| `references/representation.md` | the ASCII forms catalog, F1 to F21, and the diagram rules; F16 to F21 add the span chart, layer stack, containment boxes, decision tree, threshold on a scale, and a general tree |
| `references/clarity.md` | reader gates, sentence and term controls, the error catalog |
| `references/standards.md` | ISO 24495-1's four reader outcomes and the selected ASD-STE100 mechanics, their sources, limits, and the operational rubric |
| `references/delivery.md` | tool adaptation, conditional two-turn delivery, batching, authorized fallbacks, and reply handling |
| `references/decision-record.md` | when a record is due and its template |
| `references/worked-examples.md` | nine fictional situations across the tiers, including clarification and a replaced implementation premise; illustrations, not behavioral validation |
| `references/framework.md` | historical source framework preserved verbatim and provenance |
| `evals/evals.json` | realistic behavioral scenarios with grading expectations kept out of the scenario prompt |
| `evals/run_evals.py` | bounded CLI runner that preserves inputs, source hashes, process evidence, and ungraded review records |
| `evals/README.md` | runner usage, process evidence, semantic grading, and simulation limits |

## Behavioral validation

The evaluation runner starts a fresh scratch session for each scenario and
tool. It stages the skill, its references, and raw scenario inputs, keeping the
grading expectations separate. Every mode retains inputs and process status.
Runs that invoke a CLI also retain its output and version. Process completion
is not a behavioral pass: a reviewer
must judge the actual response against the expectations, including positive
and negative controls for approval, silence, skip, and superseded replies.
The twenty-two scenarios include artifact identification, recovery of project
context, approval stage, confusion, changed implementation requirements, and
permission-preserving simplification. Measurement cases cover opposing metric
directions, missing absolute values, and documented workflow usage and author
restrictions. A separate reader receives only the
generated brief and neutral questions. Their answers are recorded before a
reviewer compares them with the source facts, so prior familiarity cannot
supply context that the brief omitted.

See [the evaluation guide](../../plugins/clear-decision-communication/skills/clear-decision-communication/evals/README.md)
for commands. The scenarios simulate decision communication and intended next
actions; they do not perform real merges or validate native dialog rendering.
The [0.3.0 validation record](../validation/clear-decision-communication-0.3.0.md)
records the initial draft's checks. The
[O1 follow-up audit](../validation/clear-decision-communication-0.3.0-o1.md)
records the later focused correction, affected-case results, and remaining
limitations with their exact source revisions. The
[source-check and measurement review](../validation/clear-decision-communication-source-check.md)
shows the next skill-text changes verbatim and records their targeted results.
The
[0.2.0 validation record](../validation/clear-decision-communication-0.2.0.md)
retains the earlier source snapshots, reviewed outcomes, and inverse controls.

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
