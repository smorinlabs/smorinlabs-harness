# Clarity rules for the brief

The sentence, term, and error rules applied while drafting (workflow step 5) and
checked before sending (step 6). Adapted from the clear-technical-communication
skill (Steve Morin). The four reader gates below are the governing outcomes of
ISO 24495-1, and the sentence controls are selected ASD-STE100 mechanics;
`references/standards.md` describes both standards, their official sources, and
their limits. Do not claim formal compliance with either standard.

## The four reader gates

A brief passes only when it is all four:

- **Relevant:** it contains what this reader needs to decide and excludes
  process chatter about drafting, queuing, or agent coordination.
- **Findable:** the decision, the recommendation, and the requested action are
  easy to locate; the question line is first.
- **Understandable:** terms, references, relationships, and the status of every
  claim are explicit.
- **Usable:** the reader can reach the decision and the next action from the
  text alone.

## Sentence and terminology controls

- One primary assertion per sentence. Treat about 25 words as a review signal,
  not a limit; code spans, identifiers, paths, and quoted output count as one
  word each.
- Literal verbs and consistent terms. Replace a noun pile with an actor and an
  action: "config walk-up boundary" becomes "choose where the configuration
  search stops".
- Gloss identifiers where they first appear: `REQ-26 (pre-0.95 fallback
  requirement)`, never bare `REQ-26`.
- Label every symbolic value, tuple, axis, and operator. Do not use `+`, `x`,
  `@`, or `/` as prose unless the notation is defined.
- Repeat the exact noun when a pronoun could refer to more than one thing.
- State cause and contrast with words: "because", "therefore", "but", or with
  separate labeled fields. Punctuation separates clauses; it does not name a
  relationship.
- Reserve parentheses for optional information. A constraint, exception, or
  consequence belongs in a main sentence or a labeled field.
- In the brief's own prose, avoid contractions, Latin abbreviations, and chat
  shorthand. Never restyle quoted or code text.

## Names: three classes

| Class | Examples | Rule |
|---|---|---|
| Verbatim technical name | `Promise.allSettled`, `--ff-only`, `ENOTEMPTY`, `~/.claude/settings.json`, `UserAccountRepository` | Reproduce it exactly, in code font. Never paraphrase, shorten, or replace it with a description. Pair it with a description at first use in prose. |
| Established domain term | idempotent, fast-forward, backpressure | Keep the term. Define it at first use, then use it freely. |
| Invented local metaphor | `tombstone`, `ladder`, `slug` | Replace it with literal wording, or coin it explicitly as a defined term when it earns reuse. Test: the term appears in no code, command, API, or specification. |

Pair every name with a description at first use, and do not judge whether this
reader already knows it: `Use --ff-only.` becomes "Use `--ff-only`, the flag
that makes `git pull` refuse any update that is not a fast-forward." A short
role phrase satisfies the rule; one shared gloss may cover a group of parallel
names. The rule applies at first occurrence in one message; later occurrences
in the same message need no repeat; tokens inside a code block are framed as a
block, not glossed one by one.

Use the reader's own vocabulary for things they named, and attach the technical
name: "the confirm card (`ApprovalGate`)".

## Verbatim zones

Text the reader must type, match, or search is reproduced character for
character: commands, flags, paths, identifiers, configuration keys, error
messages, log output. Clarity edits stop at the boundary of a code span or
block. Preserve non-ASCII characters in these verbatim zones; the ASCII style
rule applies only to authored prose and diagram syntax. When quoted text is
itself unclear, quote it exactly and explain it outside the quotation.

## Self-contained references

Every statement is understandable from its own wording and the visible text
around it. The reader never reopens an earlier message or a plan to decode
essential meaning.

- Meaningful description first, identifier attached for navigation.
- Define task numbers, phases, option letters, and unfamiliar component names
  on first use in each message.
- Reuse shorthand only while its definition remains visible.
- Give every bullet and table row enough description to stand alone.
- Explain a component's role when its name alone is insufficient.
- Links and paths let the reader inspect supporting material; the surrounding
  text stays meaningful without opening them.

| Before | After |
|---|---|
| Approve Phase 2? | Approve moving report exports into background workers, the second implementation phase? |
| Blocked by Task 1 | The worker rollout is waiting for the database migration that stores queued jobs (Task 1). |
| Recommend Option B | I recommend running exports in a separate worker process (Q1.B). |
| the previous approach, as discussed, this change | name the approach, the discussion's conclusion, and the change |

## Error catalog

Apply every relevant row before sending. A brief can fail several rows at once;
fixing vocabulary or sentence length alone is not enough.

| Error | Detection signal | Correction | Compact example |
|---|---|---|---|
| No purpose anchor | The opening names a mechanism or artifact but not the decision. | Begin with the requested decision. | `Explosion control...` becomes `Q1. Keep the test suite small enough to implement?` |
| Undefined context | `this`, `the document`, `current`, `baseline` depend on earlier conversation. | Restate the minimum local context. | `This stays buildable.` becomes `Limiting each group to one changing dimension keeps the suite implementable.` |
| Unexplained identifiers | Tasks, phases, options, or decisions appear only as IDs. | Pair each ID with a gloss at first use. | `REQ-26 conflicts with D14.` becomes `REQ-26 (legacy fallback support) conflicts with D14 (reject legacy versions).` |
| Unexplained notation | Symbols, tuples, or compact values are not labeled. | Name every dimension and value before using notation. | `plain@branch x exact-copy x claude` becomes a labeled table. |
| Invented local metaphor | A coined term names nothing in the system. | Replace with literal wording, or define it. | `Tombstone the ladder.` becomes `Remove the legacy fallback requirement and its unreachable code.` |
| Noun pile | Three or more nouns carry a relationship no verb states. | Add an actor and an action. | `config walk-up boundary` becomes `Choose where the configuration search stops.` |
| Ambiguous reference | A pronoun or generic noun has more than one antecedent. | Repeat the exact noun. | `REQ-26 specifies it.` becomes `REQ-26 requires the pre-0.95 fallback behavior.` |
| Too many ideas per sentence | Several actors, conditions, or conclusions in one sentence. | One primary assertion per sentence. | One 40-word matrix sentence becomes one sentence per group plus a table. |
| Logic hidden in punctuation | A dash, semicolon, or slash carries cause or scope. | State the relationship in words or fields. | `D14 refuses it + the matrix excludes it.` becomes `The path is unreachable because D14 rejects those versions and the matrix excludes them.` |
| Wrong presentation form | Repeated dimensions or parallel decisions are encoded in prose. | Use a table for repeated comparison; a fixed template for repeated decisions. | Three group comparisons become `Group | Changes | Holds constant`. |
| Important information demoted | A constraint or consequence appears only in parentheses or a trailing clause. | Put it in a main sentence or a labeled field. | `(no parent branch)` becomes `Constraint: a detached HEAD has no parent branch.` |
| Status is unclear | Facts, proposals, assumptions, estimates, and decisions look alike. | Label each statement's status. | `The search stops here.` becomes `Proposal: stop the search at the worktree root.` |
| Unsupported estimate | A number has no source, basis, or implication. | Give the basis and why it matters. | `Roughly 90-120 rows.` becomes `Estimate: 90-120 rows, from <calculation>; acceptance limit <limit>.` |
| Undefined exclusion | A combination is called invalid or unreachable without a rule. | State the criterion and the evidence. | `These cells are N/A.` becomes `N/A only when <exclusion rule> applies.` |
| Missing reader action | The reader cannot tell whether this is information, a proposal, or an approval request. | End with one explicit action, or state that none is required. | `Expected volume: 120.` becomes `Action: approve the limit, or set another.` |
| No option consequences | Choices are named without effects. | State what changes under each option and why it matters. | `Keep or remove?` becomes `Keep: restore reachability and test it. Remove: update the requirement and delete unreachable code.` |
| No recommendation or owner dumping | Unresolved questions are transferred to the reader without a position. | Resolve discoverable facts, recommend, escalate only policy or preference. | `Only you can answer these.` becomes `Recommendation: Q1.A. Response needed: approve or override.` |
| Possible false choice | Two options without showing they exhaust the feasible set. | Test the set against constraints; add the missing option or invite a bounded alternative. | `Test or remove.` also considers changing the version policy. |
| Process chatter | Drafting, queuing, or coordination talk that does not help the reader act. | Remove it unless it changes ownership, timing, or the response. | `I will queue these with anything Codex adds.` is omitted. |
| Inconsistent question form | Parallel decisions use different structures. | Give every decision the same fields and one explicit question. | A heading plus complaint becomes `Q2. What source should generate the name?` |
| Precise name replaced by description | Prose describes a thing the reader must find, invoke, or edit instead of naming it. | Restore the exact name in code font beside the description. | `Use the fast-forward-only flag.` becomes ``Use `--ff-only`, the flag that ...`` |
| Name present, description absent | A verbatim name appears at first use with no role phrase. | Pair the name with a description. | ``The fix is in `UserAccountRepository`.`` becomes ``... `UserAccountRepository`, the class that loads and persists account records.`` |
| Verbatim text edited | Quoted or code text no longer matches its source. | Reproduce it exactly; explain outside the quotation. | An error `e.g. missing arg` stays exactly that. |
| Behavior described where a snippet is exact | A call, signature, or output is paraphrased where the reader must reproduce it. | Show the code; keep prose for why. | A callback description becomes the signature plus its consequence. |
| Missing example for a mechanism | A non-obvious behavior is asserted with no instance. | Add one minimal input and result, or a before and after. | `The matcher normalizes paths.` adds `./a/../b -> b`. |
| Unframed artifact | A block, table, or diagram appears with no lead-in and no reading. | Add the question it answers above and the takeaway below. | A bare config block gains both. |
| Bare number | A quantity has no unit, or no reference point. | Give the unit and a comparison. | `200ms` becomes `200 ms, about 3x the p50`. |

## Repair order

Fix failures in this order, because later edits depend on earlier meaning:

1. Purpose, intended reader, and required action.
2. Missing context, evidence, constraints, and option consequences.
3. Status and causal relationships.
4. Structure and presentation form.
5. Terms, identifiers, notation, references, and sentence mechanics.

Do not polish an under-analyzed ask; supply the analysis first. Do not shorten a
brief until its context and relationships are explicit. Never remove a name, an
example, or a quoted artifact in the name of simplification; removing required
precision is a defect, not a cleanup.
