# Axes and tiers

How much preparation and explanation a decision request needs. Read this when
sizing an ask (workflow step 2) or when a reader disputes the sizing tag.

## The seven axes

Diagnostic axes, never a numerical score. Increase the information that
addresses the actual issue. One consequential issue can justify additional depth
even when everything else is routine.

| Axis | What to assess | What additional information it can require |
|---|---|---|
| Impact | Who and what are affected, the breadth of the effect, and the significance of possible consequences. | Affected users and systems, changed behavior, important failure modes, material cost or security implications. |
| Reversibility | Difficulty and cost of undoing the decision and its effects, including lasting commitments and future restrictions. | Recovery path, migration or restoration needs, and effects that survive reverting code. |
| Departure from agreement | Whether the change follows the approved goal, scope, behavior, approach, and constraints. | The agreed baseline, the relevant new finding, the proposed deviation, and why it needs consideration. |
| Uncertainty | What is established by relevant evidence and what is inferred, assumed, untested, or inaccessible. | Verification, evidence limits, important assumptions, missing information, and what would change the recommendation. |
| Tradeoff complexity | Credible alternatives, competing priorities, dependencies between choices, and consequences for future decisions. | A focused comparison, the criterion driving the recommendation, and the strongest alternative. |
| Domain complexity | How much behavior, state, interaction, or specialized mechanism the reader must understand to evaluate the change. | A worked example, before-and-after comparison, event sequence, state representation, or small system diagram. |
| Context gap | What the reader would otherwise have to remember or retrieve to understand the message. | Descriptive names, local definitions, relevant project context, and a minimal explanation of unfamiliar components or relationships. |

Preserve these distinctions:

- Tradeoff complexity concerns choosing between options.
- Domain complexity concerns understanding how an option behaves and why it
  would work.
- Context gap concerns identifying the referenced work and restoring the
  necessary situation.
- Impact and reversibility concern what accepting the decision could cause and
  how difficult recovery would be.
- Passing tests reduce some uncertainty; they do not eliminate impact, recovery
  costs, or the need to understand a complex mechanism.
- Lines changed and file counts are insufficient proxies for explanation needs.
  A one-line behavior change can be consequential, and a large mechanical
  change can be easy to explain.

Expand selectively. A compatibility uncertainty calls for compatibility
evidence and consequences, not unrelated architectural background.

## Level tests

Rate each of the first six axes with the test in its row. Context gap is always
elevated in a run the reader was not watching, so the self-contained reference
rules apply at every tier and the axis never sets the tier by itself.

| Axis | Low | Elevated | High |
|---|---|---|---|
| Impact | local, or behavior already approved | user-visible behavior, or another team's system | many users, data, money, security, or an external contract |
| Reversibility | one revert commit, no lasting effect | revert plus cleanup, such as resubmissions, configuration, or a schema change undone by dropping what it created | a data migration or one not undone by dropping what it created, an external commitment, or effects that survive reverting code |
| Departure from agreement | on plan | scope or approach beyond what was requested, which the human has not seen | changes the project's goal, or breaks a constraint that governs the whole project rather than this request's scope |
| Uncertainty | the change is verified on this revision and its consequences are known | the change is verified, but one consequence depends on something outside the repository that cannot be checked from here | the correctness of the change itself is untested or rests on inference |
| Tradeoff complexity | one obvious option, or a required gate | a real alternative with a criterion that separates them | coupled choices, or consequences for later decisions |
| Domain complexity | the consequence is seen directly | needs a same-input before and after | needs mental simulation of order, timing, or state, or a system diagram; any race, retry policy, cache, or consistency rule is high however small |

## The tier rule

- The highest single axis sets the tier: all six rated axes low is T1, any
  elevated is T2, any high is T3. Axes are never summed.
- Tag names are the six words impact, reversibility, departure, uncertainty,
  tradeoff, domain, and nothing else.
- Two floors override the size of the change: a timing, ordering, or state
  interaction is always high on domain; deleting data that cannot be recovered
  is always high on reversibility.
- Only the elevated or high axes expand. Each adds exactly the information in
  its "additional information" column above, and nothing else.
- The tier ratchets up only. Preparation that reveals a higher axis raises the
  tier mid-draft; nothing lowers it.
- Preparation stops at the tier. A T1 does not get a prototype; a T3 does not
  skip the correctness argument.
- Representation is not set by the tier. A low-impact race condition still gets
  its ordered sequence because its change type requires one.
- A decision record is not set by the tier. It is retained when at least two of
  these hold: hard to reverse, surprising without its context, the result of a
  real tradeoff.
- Say the sizing out loud with a tag on the question line, naming the tier and
  only the axes that set it, without levels: `[T1]`, `[T2: departure]`,
  `[T3: reversibility, domain]`. An axis that is merely elevated inside a T3
  is not listed; it shows up as the section it expands. The reader can dispute the sizing; when they do, the next ask on the
  same subject honors their level as a standing preference and says so.

This table mirrors the one in SKILL.md step 2; edit both together.

| ID | Tier | Prepare | The initial view holds | Length signal |
|---|---|---|---|---|
| T1 | Confirm | the prepared result and its verification, nothing more | the question line, the recommendation, two or three options with consequences; two or three sentences in all | about 80 words |
| T2 | Compact brief | facts resolved, verification run, the strongest alternative prepared | the six-question brief, plus one comparison when the change is conditional | about 250 words |
| T3 | Full brief | plus a prototype or experiment where authorized, a correctness argument, and decision sensitivity | T2 plus the representation the change type requires, and a details pointer | about 500 words |

The length signals are review signals, in the same way a 25-word sentence is a
signal: past them, re-run the removal test on every sentence and keep every
clause that could change the answer. One and a half times the signal is the
cap (T1 120, T2 375, T3 750 words): a brief past its cap is not sent until
every reading after an artifact is one sentence, each option consequence and
each evidence label is one clause, the sensitivity line is one sentence, and
everything else is behind Details. A brief that is long because an elevated
axis needs the words is right; one that is long because every section was
filled to its maximum is wrong.

## Stage of work: what kind of explanation

The stage picks the kind of content; the tier still picks the depth. Planning
can contain small choices, and a completed change can contain a consequential
one.

| Stage | Explain | The commitment being requested |
|---|---|---|
| Planning | the goal, the constraints, the relevant current system, the credible approaches, the recommendation, and the assumptions that need validation; observed facts told apart from predictions and estimates | whether approval selects a direction, authorizes an experiment or prototype, or commits to implementation |
| Implementation or scope adjustment | the approved baseline, the new finding, the proposed change, and its consequences | the exact judgment or authorization still needed |
| Review of completed work | what the prepared change does, how it matches the agreement, the relevant verification, material exceptions, and the specific revision under review | approval of the completed work, or merge of a particular revision |
| Rollout or deployment | the target environment, the expected effects, the readiness evidence, and the recovery options | the exact rollout or deployment action, to a named environment |

State which of these approval performs, in the "On Q1.A I will" line, which is
required whenever tradeoff complexity is above low: selects an
approach, authorizes a prototype or experiment, expands implementation scope,
approves completed work, merges a particular revision, or deploys to a named
environment. Approval never expands the agent's authority beyond that line.

## Two shapes of ask

| Situation | The ask |
|---|---|
| A concrete change needs approval | the prepared change, the recommendation, the relevant evidence, the tradeoff, the strongest alternative when one is meaningful, and the exact action awaiting approval |
| The project needs a direction | the problem and its constraints, the credible approaches compared, one recommendation, the assumptions, and the commitment being requested |

Routine, understood, reversible work is a T1 in two or three sentences. A
meaningful deviation is a T2. Broad consequences, substantial uncertainty,
difficult reversal, or a complex mechanism is a T3. These are defaults; keep
every decision-relevant clause even when it breaks the preferred length.
