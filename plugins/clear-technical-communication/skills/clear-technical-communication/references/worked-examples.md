# Worked examples

These examples calibrate the skill against two recurring shapes: a compressed
multidimensional explanation and an under-analyzed owner-decision request.

Both rewrites below satisfy the artifact-frame rows in
`references/common-errors.md`. Where a name cannot be described without
inventing a fact, the rewrite marks the gap explicitly rather than guessing or
dropping the name. That is the intended behavior: a name is never removed to
avoid explaining it.

## Example 1: multidimensional coverage explanation

### Source

> Explosion control — the part that keeps this buildable: each group's section
> declares which axes vary for it and pins the rest to a canonical baseline
> (plain@branch × exact-copy × claude). G-MAT varies mode and its file-state
> inventory but holds topology at baseline; G-ANC varies topology but holds mode
> at baseline; one deliberate pairwise pass (T-X-… rows in G-VER) covers the
> highest-risk cross terms (e.g. linked-worktree × exact+ignored) instead of the
> full product. Every cell that would be meaningless is marked N/A in the doc —
> so the coverage checker demands tests only for cells that exist. Rough expected
> volume: ~90–120 scenario rows across the 14 groups.

### Principal failures

- No literal goal: `Explosion control` is a metaphor, and `buildable` has no
  measurable meaning.
- Unlabeled tuple: the reader must infer the dimensions represented by
  `plain@branch × exact-copy × claude`.
- Bare local identifiers: `G-MAT`, `G-ANC`, `G-VER`, and `T-X-…` have no
  descriptions.
- Hidden matrix: several group/dimension comparisons are compressed into a
  semicolon-heavy sentence.
- Unsupported exclusions and estimate: `meaningless`, `N/A`, and `~90–120`
  lack their rules, calculation, and implication.
- Missing reader action: the message does not say whether it is an explanation,
  a proposal, or a request for approval.

### Rewritten communication

> **Goal:** Keep the test suite small enough to implement while preserving
> coverage of the combinations most likely to fail.
>
> Each test group changes only the dimensions assigned to that group. It uses
> the canonical baseline for all other dimensions.
>
> The specification must label the dimensions represented by the baseline
> values `plain@branch`, `exact-copy`, and `claude`.
>
> The table below shows which dimensions each group varies. The specification
> must state what each group identifier abbreviates; the names are used here
> exactly as the source writes them.
>
> | Group | Dimensions changed | Dimensions held at baseline |
> |---|---|---|
> | `G-MAT` | Mode and file state | Topology |
> | `G-ANC` | Topology | Mode |
> | `G-VER` | Selected interactions between dimensions | Unrelated dimensions |
>
> Read the table as the coverage contract: every group holds all unlisted
> dimensions at the canonical baseline, which is what keeps the suite bounded.
>
> `G-VER` tests selected high-risk combinations, listed as its `T-X-…` rows.
> One example combines a linked worktree with the `exact+ignored` file state.
> It does not test every possible combination. The specification must state
> what the `T-X-…` identifiers name and how they are numbered.
>
> The specification marks an invalid combination as `N/A`. Add the rule that
> defines an invalid combination. The coverage checker does not require a test
> for a combination marked `N/A`.
>
> The current group counts estimate 90–120 scenarios across 14 groups. Add the
> calculation and the implementation limit that makes this range acceptable.
>
> **Response needed:** [The author must state whether this message is
> informational or requires review or approval, and identify the reader who
> must respond.]

The rewrite does not invent the missing tuple labels, exclusion criterion,
estimate calculation, implementation limit, or requested action. It exposes
each as a precise gap that the author must fill.

Note that all four flagged identifiers survive into the rewrite, `T-X-…`
included. A name is carried forward even when it is a pattern rather than a
single identifier, and even when its meaning is exactly what the author still
has to supply — dropping it would remove the precision the rewrite exists to
protect.

## Example 2: owner-decision request

### Source

> Three questions only you can answer (I'll queue them with anything Codex
> adds):
>
> 1. Pre-0.95 Codex fallback ladder — REQ-26 specifies it, but D14 refusal + the
>    version matrix make it dead code. Test the ladder or tombstone it?
> 2. Auto-name on detached HEAD — there's no parent branch to slug from; the
>    corpus never defines what the name should be.
> 3. Config walk-up boundary in a linked worktree — stop at the worktree root or
>    the project root? Corpus is silent.

### Principal failures

- Owner dumping: `only you can answer` substitutes escalation for research and
  recommendation.
- Process chatter: queueing future Codex additions does not help the reader
  decide.
- Unexplained IDs and jargon: `REQ-26`, `D14`, `fallback ladder`, `tombstone`,
  `slug`, `walk-up`, and `corpus` require reconstruction.
- Uneven questions: item 2 is a problem statement rather than an explicit
  question.
- Missing effects and recommendations: the reader cannot compare the choices.
- Possible false choice: `test or tombstone` may omit changing the policy that
  makes the path unreachable.

### Rewritten communication

> **Decisions needed:** Three behaviors remain undefined. State which artifact
> or implementation task these decisions block.
>
> **1. Support for Codex versions before 0.95**
>
> - **Conflict:** `REQ-26` requires fallback behavior for these versions.
>   `D14` — [the author must state what `D14` is: a design decision, a
>   requirement, or a policy] — and the version matrix currently prevent that
>   behavior from running.
> - **Decision:** Will the product continue to support the fallback behavior?
> - **Option A — keep support:** Change the design so the fallback is reachable,
>   and add tests.
> - **Option B — remove support:** Update `REQ-26` and remove the unreachable
>   implementation.
> - **Other feasible option:** Change the version policy that currently makes
>   the path unreachable.
> - **Recommendation:** [The author must recommend an option and explain why.]
>
> **2. Automatic naming in a detached `HEAD` state**
>
> - **Constraint:** A detached `HEAD` does not identify a parent branch from
>   which to derive a name.
> - **Decision:** What information should generate the automatic name?
> - **Options and effects:** [The author must enumerate the supported naming
>   sources and their consequences.]
> - **Recommendation:** [The author must recommend an option.]
>
> **3. Configuration search in a linked worktree**
>
> - **Missing rule:** The specification does not define the upper boundary of
>   the configuration search.
> - **Decision:** Should the search stop at the linked-worktree root or continue
>   to the project root?
> - **Effects:** [The author must state how each boundary changes isolation,
>   configuration sharing, and compatibility.]
> - **Recommendation:** [The author must recommend an option.]
>
> **Response needed:** Approve or replace the recommendation for each decision.

This version does not pretend that editing can replace missing analysis. It
creates a usable decision structure and makes the absent work explicit.
