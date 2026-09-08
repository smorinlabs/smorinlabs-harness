# clear-decision-communication: design record (2026-09-07)

The research and decisions behind the `clear-decision-communication` skill
(PROJECTS P43). Part 1 is the inventory of every installed communication prompt
and the first candidate list. Part 2 is the per-candidate research with the
arguments for and against and the recommendations the owner accepted. The
source framework itself is reproduced verbatim inside the skill at
`plugins/clear-decision-communication/skills/clear-decision-communication/references/framework.md`.

Decisions taken during the session, in order: scope is decision asks only, no
report branch; three tiers with the highest single axis setting the tier;
question IDs continue across the run and key the record, options lettered with
the recommended option always A; the skill is self-contained and names no other
skill; output is inline ASCII text only, never HTML; verdict 4 with a
description-only re-carve of `clear-technical-communication`; home is this
harness as its own plugin; the tools grant is permissive for information
gathering and text-only for output. Two follow-ups are tracked as P44.

---

# Part 1: inventory and candidate aspects

## Coverage

Read in full by the lead: clear-technical-communication (SKILL.md,
references/common-errors.md, references/artifact-forms.md), show-me,
question-walkthrough, reader-steps, grilling, grill-me, grill-with-docs,
explain (rules and modes sections), _conventions.md, _routing.md.

Read by extraction agents (cited by path and line in the agent reports):
explain/references/examples.md, html-codesign (+ spec-format, id-grammar,
iteration-loop, export-formats, design-notes), html-explain (skim),
design-by-elements (+ worked-examples), project-refine, factor-scan,
session-handoff, session-status, session-recap (skim), manual-test-guide,
wizard, wayfinder, system-atlas (skim), setup-matt-pocock-skills;
superpowers brainstorming, writing-plans, receiving-code-review,
requesting-code-review, verification-before-completion, executing-plans;
plugin-dev command-development (+ references/interactive-commands.md);
codex codex-result-handling, gpt-5-4-prompting; skill-creator;
explanatory-output-style and learning-output-style hooks.

Not on disk (Claude Code built-ins, relevant to the HTML path of show-me):
artifact-design, artifact-diagramming, dataviz.

Always-on prompts in ~/.claude/CLAUDE.md that are also communication prompts:
the clear-technical-communication digest ("For every decision request,
provide: 1–5"), the reader-steps digest, and the question-dialog discipline
(guard for anthropics/claude-code#74260 text loss).

## Provenance (from ~/.agents/.skill-lock.json, licenses via GitHub REST)

| Skill | Source | License |
|---|---|---|
| show-me | humanlayer/skills (https://github.com/humanlayer/skills.git), installed 2026-08-13 | MIT |
| grilling, grill-me, grill-with-docs, wizard, wayfinder, setup-matt-pocock-skills | mattpocock/skills (https://github.com/mattpocock/skills.git), installed 2026-08-12 | MIT |
| system-atlas | inkboard/system-atlas, installed 2026-08-28 | MIT |
| superpowers:* | claude-plugins-official marketplace, superpowers 6.3.0 | plugin |
| plugin-dev, skill-creator, learning-output-style, explanatory-output-style | claude-plugins-official | plugin |
| codex:* | openai-codex marketplace, codex 1.0.4 | plugin |

## Inventory: installed communication prompts

| Prompt | Origin | What it owns | Relation to the new skill |
|---|---|---|---|
| clear-technical-communication | first-party, smorinlabs-harness (public) | Review, rewrite, compose technical communication; seven-field decision-request template; artifact frame; error catalog | Closest neighbor. Description claims "make a decision request actionable". |
| question-walkthrough | first-party, smorinlabs-harness | Conduct a pile of decisions one at a time; two-turn gate iron law; notes classification; record at source | Closest neighbor. Every fleet skill routes in-chat decisions here. |
| explain | first-party, smorinlabs-harness | Inline explanation anatomy; options mode with recommendation and runner-up | Neighbor on options mode. |
| html-codesign | first-party, smorinlabs-harness | Async decision page; recommendation envelope; skip and ask-back channels; verdict enum; ID grammar | Neighbor by medium; heavy ingredient. |
| html-explain | first-party, smorinlabs-harness | Read-only explainer page | Ingredient (two-turn gate, removal test). |
| reader-steps | first-party, smorinlabs-harness | Human-only action blocks; decisions excluded | Complementary. |
| design-by-elements | first-party, smorinlabs-harness | Opposed variants with IDs; lock plus rationale | Ingredient. |
| session-recap, session-status, session-handoff | first-party, smorinlabs-harness | Proof-gated decisions table; confidence-tiered ask-vs-proceed; trust markers | Ingredient. |
| project-refine, factor-scan | first-party, smorinlabs-harness | Confirm before mutation; per-finding evidence template; four-way disposition | Ingredient. |
| CLAUDE.md digests | first-party, smorin-bootstrap | Always-on CTC digest, reader-steps digest, question-dialog discipline | Neighbor; a sibling digest is likely needed. |
| show-me | third-party, humanlayer/skills, MIT | Visual forms catalog: pseudocode, call tree, component tree, file tree, Mermaid sequence, diff-shaped delta, whole block, focused HTML | Named ingredient. |
| grilling family | third-party, mattpocock/skills, MIT | Frontier rounds; numbered question plus recommended answer format; facts are the agent's job | Ingredient; shares the word "decision" in its trigger. |
| wayfinder | third-party, mattpocock/skills, MIT | Decision tickets; sharpness test; HITL never self-answered | Ingredient. |
| system-atlas | third-party, inkboard, MIT | Question lifecycle open, resolved, routed | Minor ingredient. |
| superpowers:brainstorming | third-party plugin | Design approval gate; seeing-vs-reading test; one question per message; ratchet | Uncontrolled neighbor. |
| superpowers:executing-plans | third-party plugin | Stop conditions during execution | Uncontrolled neighbor on when to stop. |
| superpowers:receiving-code-review, requesting-code-review, verification-before-completion, writing-plans | third-party plugin | Stop-and-ask when unclear; severity tiers; evidence before claims; execution handoff menu | Minor ingredients. |
| plugin-dev:command-development | third-party plugin | AskUserQuestion mechanics | Ingredient for mechanics. |
| codex:codex-result-handling | third-party plugin | Stop after findings and ask; preserve evidence boundaries | Ingredient. |
| learning-output-style hook | third-party plugin | Ask-vs-proceed rubric at decision points; three-part request | Uncontrolled neighbor in concept. |
| Built-ins artifact-design, artifact-diagramming, dataviz | Claude Code | Visual design for pages and diagrams | Ingredient for the HTML path. |

No decision content, excluded: manual-test-guide, wizard, gpt-5-4-prompting,
skill-creator, explanatory-output-style.

## Candidate aspects to incorporate

Tier: Must = the skill is wrong without it. Strong = clear fit, include
unless the interview says otherwise. Optional = worth a line or a reference.
"Borrow" = the idea; "reproduce" = the text (first-party text is free; MIT
third-party text needs attribution; house style prefers delegation).

| # | Aspect | Source | Why it fits an in-run decision moment | Tier |
|---|---|---|---|---|
| 1 | Seven-field decision request: context and why now; evidence or constraint; one explicit question; genuinely available options; effects per option (behavior, cost, risk); recommendation with rationale; response needed in an exact form | clear-technical-communication SKILL.md "Decision request" | The spine of the message. | Must (reproduce) |
| 2 | Research what can be resolved; bring only genuine owner decisions; error rows "No recommendation or owner dumping", "Possible false choice", "No option consequences", "Missing reader action", "Status is unclear" | CTC references/common-errors.md | Stops the agent from dumping questions it could have answered. | Must (reproduce) |
| 3 | Every artifact carries a frame: lead-in, exact artifact, reading | CTC SKILL.md "Show exactly, and say what it means" | Governs how show-me visuals are embedded. | Must (reproduce) |
| 4 | Visual forms catalog and selection rule: "pick the smallest view that makes the key point clear"; diff-shaped deltas when the surrounding shape exists; whole block when most is new; focused HTML for layouts too dense for Mermaid; "place each visual next to the short text it supports" | show-me SKILL.md | Lets an option be seen, not described. Side-by-side diffs of two options are the decision-specific use. | Must (delegate by name; embed a short digest as fallback) |
| 5 | Two-turn gate: the pre-read ends its turn with no tool call after it; AskUserQuestion opens the next turn; every option stands alone in case the pre-read never rendered | question-walkthrough Iron Law; html-codesign SKILL.md 102-109; html-explain SKILL.md 50-55 | Same-turn prose may never render. House-wide convention. | Must (reproduce) |
| 6 | AskUserQuestion mechanics: 2 to 4 options; header 12 characters or fewer; Other is automatic; multiSelect only for combinable choices; previews for concrete artifacts; option descriptions carry the trade-off | plugin-dev command-development references/interactive-commands.md; _conventions.md interaction contract; question-walkthrough step 4 | The channel's hard limits shape the message. | Must (borrow) |
| 7 | Recommendation first, labeled "(Recommended)", reasoning in its description; notes on any selection are read and applied | _conventions.md interaction contract; brainstorming lines 176-178 | Fleet contract. | Must (reproduce) |
| 8 | Ask-vs-proceed criteria: stop on blocker, unclear instruction, repeated verification failure (executing-plans 40-48); confidence tiers: confident plus single goal means confirm and proceed, vague means ask (session-handoff 43-49); ask when multiple valid approaches, skip for boilerplate (learning-output-style); sharpness test "can you state the question precisely now" (wayfinder 88-91) | four sources | Decides whether the moment is a decision at all. | Must (borrow, synthesize) |
| 9 | Name the runner-up when the call is close; state confidence conditionally, not as a bare number | explain references/examples.md 72-80 | Honest recommendation shape. | Strong (reproduce) |
| 10 | Argue the recommendation both ways when genuinely close | session-recap SKILL.md 535 | Prevents a false lean. | Strong (borrow) |
| 11 | Contrast, don't enumerate: 2 to 3 opposed variants with short IDs; more than about 5 choices means the decision is under-shaped | design-by-elements 49-53, 113; html-codesign 335 | Option-count discipline. | Strong (borrow) |
| 12 | Channel test: "would the user understand this better by seeing it than reading it?" | brainstorming 242-247 | The trigger for reaching for a show-me form. | Strong (borrow) |
| 13 | Status labels on every claim: fact, assumption, estimate, proposal, decision; "no proof, no row"; reconstructed counts say so; hedge words "should, probably, seems" flag unverified claims | CTC common-errors "Status is unclear"; session-recap 265; session-status 49-50, 186; verification-before-completion 52; codex-result-handling 13 | Evidence discipline for the options' effects. | Strong (borrow, synthesize) |
| 14 | Skip is a first-class answer distinct from ask-back; parked is not decided | html-codesign 258-263; question-walkthrough red flags | Lets a run continue without a forced pick. | Strong (borrow) |
| 15 | Record at the source: Fork, Decision, Rationale; rationale stops a decision reopening | design-by-elements 59-61; question-walkthrough step 7; wayfinder 125 | Decisions made mid-run must outlive the run. | Strong (borrow) |
| 16 | Facts are the agent's job, never the user's; dispatch a lookup instead of asking | grilling | Removes a class of needless asks. | Strong (borrow) |
| 17 | Confirm before irreversible action; the default answer is "keep" | project-refine Iron Law, 127-131; wizard 37 | Sources for stating the default and reversibility. | Strong (borrow) |
| 18 | Frontier rounds: ask every question whose prerequisites are settled in one numbered round, each with a recommended answer | grilling | Cheaper round-trips in unattended runs. Conflicts with one question per message. | Optional (tension T2) |
| 19 | Per-item evidence template: severity, dimension, file:line, evidence, recommended action; four-way disposition accept, modify, skip, mark intentional | factor-scan 126-140 | Shape for decisions that arise from findings. | Optional (borrow) |
| 20 | Plain-language law: IDs annotate, never the content; translate titles | session-status 29-33 | Options readable by someone not in the session. | Optional (borrow) |
| 21 | Removal test for each detail: remove it; is the decision harder? No means cut | html-explain 146-149 | Keeps the ask short. | Optional (borrow) |
| 22 | Progressive disclosure: a coarse triage question before detail questions | command-development 491-516 | Sequencing within one decision. | Optional (borrow) |
| 23 | Stop after presenting findings; ask which to act on, even when the fix is obvious | codex-result-handling 19 | Gate between report and action. | Optional (borrow) |
| 24 | Three canned reply templates: questions first, another draft, here are my answers | html-codesign references/iteration-loop.md 14-40 | Standing reply forms for a human returning to a paused run. | Optional (borrow) |
| 25 | Self-review checklist before presenting: no placeholders, exact source values | writing-plans 131-151 | Pre-send gate. | Optional (borrow) |
| 26 | Question lifecycle: open, resolved, routed | system-atlas 28 | Minimal answer-tracking schema. | Optional (borrow) |

## Trigger-space map and preliminary verdict

Two facts drive the conflict verdict:

1. clear-technical-communication's description claims "make a decision
   request actionable" and its body holds the seven-field template. Its
   plugin.meta.toml description and keywords also name decision requests.
2. Every fleet skill that touches an in-chat decision routes to
   question-walkthrough: html-codesign, html-explain, design-by-elements,
   session-handoff, session-recap, reader-steps.

Proposed carve:

| Skill | Keeps | Gives up or gains |
|---|---|---|
| new skill | composing and delivering one agent-originated decision request mid-run: when to ask, the seven fields, evidence status, show-me visuals, the two-turn gate, recording the answer | new |
| clear-technical-communication | review, rewrite, compose human-authored technical text; explanation, comparison, status, procedure templates | drops "make a decision request actionable" and the decision-request template body, or keeps the template and points to the new skill for in-run asks (verdict 4 re-carve either way) |
| question-walkthrough | conducting a pile: intake, confirm, sequence, re-plan, batch | may delegate per-question framing to the new skill; description clause "explain each decision" may need a "Not for" line |
| explain | options mode teaching the alternatives | may add "Not for in-run decision requests" |

Preliminary verdict: 4, create new plus re-carve CTC (and possibly
question-walkthrough and explain descriptions).

Uncontrolled neighbors, recorded as accepted overlap for skill-system-doctor:
superpowers:brainstorming (design approval gate before implementation),
superpowers:executing-plans (owns when to stop during plan execution),
learning-output-style hook (decision points as teaching moments).

Name-collision check: no installed skill name contains "decision", "decide",
"choice", or "ask". Clear for any decision-* or clear-decision-* name.

## Design tensions for the interview (lead's leans)

| ID | Tension | Lean |
|---|---|---|
| T1 | Recommendation-first (CTC, brainstorming, fleet contract) vs neutral trade-off framing (learning-output-style) | Recommendation-first always; argued both ways when close. |
| T2 | One question per message (fleet contract, project-refine) vs grilling's frontier round | One decision per ask by default; a numbered frontier batch allowed only for independent questions, each with its recommendation, in unattended runs. |
| T3 | Two-turn gate (question-walkthrough, html-*) vs CLAUDE.md question-dialog discipline (text immediately before the call, no thinking between) | Two-turn gate, with options that stand alone. |
| T4 | Always-on digest in CLAUDE.md like CTC and reader-steps | Yes, as a follow-up task in smorin-bootstrap; outside skill-create's scope. |
| T5 | show-me: delegate by name with an embedded digest fallback (html-codesign's pattern for CTC) vs reproduce the catalog under MIT attribution | Delegate plus digest fallback. |
| T6 | HTML artifacts: local file opened with `open` (show-me) vs the Artifact tool | Local file default so Codex works; Artifact when the session offers it. |
| T7 | Fields specific to agentic runs, proposed by the lead, not sourced: done so far, what is blocked, default if no answer, reversibility, cost of asking | Add as fields; sourced in part by session-handoff "Done so far by me" and project-refine's default-keep rule. |

## Phase-A proposal

Based on the request: a skill that composes and delivers one agent-originated
decision request during an agentic run. It decides whether the moment is a
genuine owner decision, builds the seven-field request with evidence status
on every claim, shows options with show-me forms where seeing beats reading,
delivers through the two-turn AskUserQuestion gate with stand-alone options,
and records the answer at its source. Verdict expected: create new plus
re-carve clear-technical-communication.

---

# Part 2: additions research

Scope settled before this pass: decision asks only (no report branch); three tiers
T1 Confirm / T2 Compact brief / T3 Full brief, highest single axis sets the tier,
context gap always on, representation by change type, record by significance;
IDs Q1, Q2 continuing across the run, options Q1.A, Q1.B, recommended option
listed first so it is always A, a decided question keeps its Q ID as the record key.
The skill is self-contained: it names no other skill; borrowed text is attributed on
the docs page.

External sources used (from the framework's own list):
- NN/g confirmation dialogs: "Do not use confirmation dialogs for routine actions.
  Like in Aesop's fable, if you cry wolf too many times, people will stop paying
  attention to the question." "Instead of Yes/No answers, provide response options
  that summarize what will happen for each possible response." "Avoid giving
  confirmation dialogs a default Yes answer."
- NN/g recognition and recall: "recall involves fewer cues than recognition";
  promote recognition "by making information and interface functions visible".
- NN/g progressive disclosure: "You must disclose everything that users frequently
  need up front"; "designs that go beyond 2 disclosure levels typically have low
  usability".

Steve accepted every recommendation below on 2026-09-07.

## Before asking

| # | Candidate | Source | For | Against | Recommendation | Serves |
|---|---|---|---|---|---|---|
| 1 | What resolves it: fact / prototype / conversation / task | wayfinder ticket types | facts never reach the human; "how should it look" decides best by reaction to an artifact | extra step; prototypes imply unauthorized building | In, as a four-way check in the entry gate; prototypes only where authorized or trivially cheap, else offered as an option | decide |
| 2 | Sharpness test | wayfinder "Fog or ticket?" | half-formed asks make the human finish the agent's thinking | could delay an escalation | In, as the gate wording: question plus options in one sentence, else say what is known and ask for what sharpens it | understand |
| 3 | Never answer for the human | wayfinder HITL rule | "assume yes and continue" is the unattended-run failure mode | a flat ban stalls runs | In, with a stated silence default: "If I hear nothing I will do X because Y", X the most reversible option, never the recommended one when they differ | decide |
| 4 | Ask-or-proceed triggers | executing-plans, learning-output-style hook, session-handoff | concrete triggers beat judgment | three overlapping lists | In, merged to about six bullets: ask on a required gate, a departure, a tradeoff whose criterion the human owns, an unclearable blocker; never for a fact, something authorized, boilerplate | understand |
| 5 | Say the sizing out loud | brainstorming | the human can override the sizing | one more token per ask | In, as a bracketed tag naming tier and elevated axes | understand, answer |
| 6 | Standing preference knob | proposed | section 7 says preferences persist | CLAUDE.md already has "When to Ask vs. Proceed"; adds state | Out as a feature; In as a rule: honor standing preferences and cite the one applied when it changed the tier | understand |

## Composing the question

| # | Candidate | Source | For | Against | Recommendation | Serves |
|---|---|---|---|---|---|---|
| 7 | Seeing versus reading test | brainstorming | one-sentence trigger for the representation table | none | In, opening line of the representation rule | understand |
| 8 | Removal test | html-explain | keeps T2/T3 from bloating | none | In, pre-send checklist | answer |
| 9 | Runner-up plus conditional confidence | explain options mode | tells the human when to override | overlaps section 11 | In, as the recommendation line shape: "Recommend A because X; B wins if Y" | decide |
| 10 | Argued both ways | session-recap, html-codesign | honest when balanced | fence-sitting risk | In only as the exception: argue, or state why neutral and what preference settles it | decide |
| 11 | Contrast, do not enumerate | design-by-elements | opposed options reveal preference; catalogs paralyze | some decisions have four options | In: two to four opposed options; more than four means split | answer, decide |
| 12 | Plain-language law: IDs annotate, never the content | session-status | operational form of section 10 and recognition over recall | none | In, with the framework's own examples | understand |
| 13 | No placeholders, no hedge words | writing-plans, verification-before-completion | hides the uncertainty section 11 wants visible | none | In, pre-send checklist | decide |
| 14 | Cannot-verify pattern | receiving-code-review | right shape for "essential information cannot be obtained" | none | In: "cannot verify X without Y" plus investigate at a cost / decide conditionally / defer | decide |

## Answering and after

| # | Candidate | Source | For | Against | Recommendation | Serves |
|---|---|---|---|---|---|---|
| 15 | Dialog mechanics | plugin-dev command-development, fleet contract | hard limits of the channel | tool-specific | In, body rule plus a references file | answer |
| 16 | Consequence-named options | NN/g, framework section 12 | never Yes/No | none | In: every label is a verb phrase naming the outcome | answer |
| 17 | Plain-text form | grilling | Codex has no dialog; T3 exceeds a dialog | two renderings | In, text canonical, dialog derived | answer |
| 18 | Two-turn gate, stand-alone options | question-walkthrough, html-codesign, html-explain | field-confirmed rendering loss | extra round-trip; conflicts with the CLAUDE.md same-turn guard | In; follow-up: align the CLAUDE.md question-dialog guard to the gate | understand |
| 19 | Frontier batching | grilling | fewer round-trips | "picks the easiest and forgets the rest"; section 13 | In, bounded: at most three independent T1/T2 questions per message; T3 alone; coupled questions in order | answer |
| 20 | Skip and ask-back | html-codesign | defer without a bad pick; request information | clutters options | In as reply grammar: "Q3: skip", "Q3: ask ..." | answer |
| 21 | Conditions on an answer | question-walkthrough notes | how humans decide; section 13 | three classes is heavy | In, two classes: condition (apply, restate back) and redirect (do first, re-ask) | decide |
| 22 | Followed or overrode | html-codesign verdict | the only calibration signal | one field | In, record only | decide over time |
| 23 | Rationale mandatory in the record; one canonical place | design-by-elements, wayfinder | stops reopening; section 14 baseline | none | In; named rules out for v1 | decide later |
| 24 | Question lifecycle: open / decided / skipped / redirected | system-atlas | status at a glance | none | In, folded into the ID scheme | understand |

Out: factor-scan four-way disposition (covered by 20 and 21; "intentional" is the
recorded rationale); codex-result-handling stop-after-findings (review flow).

## Addendum: system-atlas, visualization aspects (read in full 2026-09-07)

Source: ~/.agents/skills/system-atlas (inkboard/system-atlas, MIT). Show-me supplies
static, whole-view forms with names only. The atlas adds a grammar for budgeted,
ordered, labeled views. Transferable items:

| # | Enhancement | From the atlas | For | Against | Recommendation | Serves |
|---|---|---|---|---|---|---|
| A | Visual budget and declared omissions | chapters add at most three structures and one flow; unrevealed structures stay dimmed in the index | "a whole system at once reads as noise" was the first field correction; a partial view must say it is partial | none | In: a decision visual shows at most three new structures and one flow; an "unchanged, not shown" line names what was left out | understand |
| B | Baseline first, then the delta | chapter recipe starts with the two structures the reader knows | matches "the agreed baseline, the new finding, the deviation" | none | In: first view is the approved baseline; the change arrives as a second view or as ghosts | understand |
| C | Ghost convention | dashed outline, no fill = not built | one visual code for "proposed" across every form | none | In: proposed = dashed in Mermaid and HTML, `+` in diff-shaped text; existing = solid | understand |
| D | Role shapes | tall, store, cards, slab, screen, gate, job, box | a store, a gate, a surface read faster as shapes; Mermaid has cylinder, diamond, stadium, hexagon | decoration when the role is irrelevant | In as a small legend, used only when the role matters to the decision | understand |
| E | Code plus name labels | code chip and readable short name on every structure | options can point at the diagram: "A changes V and U; B changes V only" | none | In: nodes carry a short code and a name; option consequences reference the codes | answer, decide |
| F | Same map, one route per option; payload at the hop that changes | flow picker; packets carry a representative payload | the framework's "same input, same event order" rule made visual | none | In: identical node set per option, routes labeled A and B; or a trace table hop / current / proposed with one representative input, payload shown at the changing hop | decide |
| G | Two zoom levels | map, then inside one structure for its steps | matches NN/g's two-level limit | none | In: the map and at most one inside view | understand |
| H | Text twin | SYSTEM.md generated from the same data | the visual and the prose must agree; plain-text fallback | none | In: same names and codes in prose and visual; every HTML artifact ships with its text twin in the message; one file or URL, republished, never a second copy | understand |
| I | Reader's vocabulary | "confirm card" not "HITL prompt"; `what` for a non-engineer, `how` names files in code | recognition over recall; CTC name-plus-description | none | In: use the human's names for things, attach the technical name in code font | understand |
| J | Record significance test | ADRs only for decisions hard to reverse, surprising without context, and the result of a real tradeoff | sharper than "significant" | none | In, replaces the significance rule: a record when any two of the three hold | decide later |
| K | Sweep after a decision | "grep the outputs for the stale words; the person reads everything" | a rejected option name surviving in a record or PR text misleads | none | In: after an answer, sweep anything that persists for the rejected option and stale names | decide later |
| L | Ask-back gets an example | "if they say 'I don't get this', explain with a concrete example before resolving" | a restatement repeats the failure | none | In: a re-ask after "I don't get this" carries a concrete example, never a rephrase | understand |
| M | Question tally | top strip counts open, routed, resolved | one line orients the reader when several questions are live | none | In: when more than one Q is live, one tally line: open, decided, skipped | understand |
| N | HTML hygiene | light and dark tokens, reduced motion, charset, verify in a real browser | the HTML path breaks silently otherwise | none | In, references only | answer |

Out: isometric rendering, packet animation, palette and fonts, build pipeline, docs
folder policy.
