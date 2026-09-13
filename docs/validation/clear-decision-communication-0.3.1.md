# Clear decision communication 0.3.1: concrete language and evidence

The owner approved applying the fourth editorial rewrite from the local Q4
review. This update builds on merged PR #67 at `91dd09a` and keeps its context,
source-verification, stable-ID, and authorization safeguards.

## Implemented correction

The brief now names each project, artifact, command, tool, and role before
shorthand. The full recommended action precedes its option ID. Numbered options
appear together immediately afterward, with stable lettered IDs retained for
reply handling. Numeric replies to superseded lists grant no authority.

Evidence is scoped to the property its source establishes. Package metadata
cannot establish speed or suitability. A project ruling determines policy
scope or acceptance, not a general legal conclusion. Applying a review to a
class does not predetermine each candidate's result. Deferral leaves policy
open, and the closing action must agree with every option.

The canonical template, tier guidance, delivery rules, existing examples, and
documentation use the same form. The owner's preferred historical Q4 rewrite
is preserved in `references/project-policy-example.md`. Its facts remain
attributed to the historical research; it is an editorial target, not a raw
model response or a fresh registry check.

## Original-context experiment

Three temporary Claude sessions forked the same original Q4 message. Each
received the same frozen research files and request, with a different skill
snapshot. The native CLI retained the original conversation through that
message. All three source-transcript prefix hashes were unchanged afterward,
and tool events confirm that each run read its assigned `skill/SKILL.md`.

The forks used read tools, no session persistence, restricted mode, no MCP
servers, and no model or effort override. The restored model identified itself
as `claude-opus-5`. Turning off the saved system-prompt snapshot and customizations
isolates the supplied instructions; this is not an exact replay of every
original runtime setting. No research decision or project implementation was
changed by a test.

| Snapshot | SKILL.md SHA-256 | Process | Words in complete final response | Observed result |
|---|---|---|---:|---|
| Upstream 0.3.0 | `c0ffe5a76975d1bf87df91b9e92b051c553c9bce3f854f935460a6101cb6cbb6` | completed, 197.495 s | 855 | Retained abstract "reach", recommendation IDs before definitions, late options, repeated comparisons, and an unsupported legal assertion. |
| First applied candidate | `452ce87b7f0f5e2b483b178395795e255c7bd0ceb22fc969b82727a568127b85` | completed, 172.523 s | 614 | Restored named project and commands, adjacent numbered options, individual review scope, and deferral. Still called an unmeasured alternative "faster" and added drafting commentary. |
| Follow-up candidate | `249a4af7f33c4ca0d1aa78f78251fc7507de3e13337dda3904c5df261d51a07b` | completed, 347.133 s | 632 | Removed the drafting preamble and retained the concrete choice and research-only actions. Still described an unmeasured setup benefit as "established" and included unnecessary research detail. |

Word counts are whitespace-separated words in the entire captured final
response, including any preamble and closing narration. They are observations,
not a quality score or evidence of a stable percentage improvement.

The last small source edit aligned the mirrored tier tables with the new
canonical order and removed the obsolete mandatory extra next-action section.
It followed the model snapshots above. The resulting SKILL.md hash is
`a7de8f7c17933bcd77dbf9c5c04586242a002396c15398c8315b658bfcf231ea`.
Native behavior has not been separately sampled after that alignment edit.

Two independent readers saw only the respective generated brief. Both could
identify the project, policy choice, option effects, evidence limits, and reply.
They still identified unclear auxiliary terms and the unmeasured-benefit claim.
Their comprehension is not proof of source accuracy. The editorial target is
also included in the skill, so Q4 is a regression example; unfamiliar cases
are needed to test whether the change works elsewhere.

## Fresh-session controls and remaining limitations

The first candidate ran cases 7, 20, 23, 24, and 25. The follow-up reran cases 7
and 23 after the instruction changes, retaining all earlier attempts. Every
process completed. The runner's grader expectations stayed outside the model's
context. These are communication simulations, not real approvals or mutations.

| Case | Evidence preserved | Remaining issue |
|---|---|---|
| 7: verified local rename | Exact Unicode paths, checked revision, reversible local scope, and explicit choice remained clear. | The first run narrated internal sizing. The follow-up removed that preamble but retained an unnecessary delivery explanation. |
| 20: opposing benchmark metrics | Both assets, lower measured latency, higher measured cost, absolute changes, and the owner's selection rule were retained. | Long drafting and delivery narration obscured the decision. This run does not establish broad presentation compliance. |
| 23: different development-tool policy | Named project, command and roles; preserved option meanings, individual review, metadata limits, and deferral. | Both runs repeated the options in another matrix and included process narration. This remains a failed concision/presentation check. |
| 24: unavailable setup context | Requested the one setup proposal without inventing its command or installation role. | The 481-word response was too long for the required information request and narrated the workflow. |
| 25: stale numeric reply | Recognized the original list as superseded, executed neither choice, and sought a current answer. | Added unsupported details about the unbuilt prototype and unnecessary process explanation. |

The simulation prompt requests the immediate next action as well as the next
response. That may contribute to separate delivery explanations; it does not
explain away internal sizing narration or duplicated comparisons. No prompt
change was made to hide these failures. The result supports improved concrete
framing in Q4, not a claim that the skill reliably meets every clarity rule.

## Package and content checks

- Independent content review found and corrected a weakened silence rule,
  a possible confusion between policy rulings and legal conclusions, and a
  first-use ordering issue in the retry example.
- Three new scenarios bring the suite to 25. The existing separation check was
  updated from 22 to 25; no evaluation-runner behavior changed.
- Initial repository suite: 334 passed; one failed because of that stale count.
  After repairing it, all 104 evaluation-runner tests passed in 2.33 seconds.
  The unrelated tests were not repeated.
- Generated manifests were refreshed for plugin version 0.3.1 and passed the
  generation check. The skill's trigger description and tools grant did not change.
- Static and isolated runtime loading passed for Claude and Codex. The verifier
  reported informational version drift. Marketplace validation passed with the
  existing 15 warnings about the generator's ignored `_generated` field.
- Whitespace and changed-file checks found no absolute personal paths or
  unfilled documentation placeholders.

Raw native transcripts, frozen sources, prompts, hashes, extracted responses,
and independent reviews are retained locally in `/private/tmp/cdc-applied-c7d7jp_9/`.
They are not committed because they contain original-session context. These
local captures may be removed by temporary-directory cleanup; the table above
retains the source identities and observed limits. The prior diagnostic work
remains in its separate local experiment directory and is not reclassified as
validation of this implementation.

This change is prepared on its own branch. Installed development placements
continue to resolve to the stable main checkout. Repository merge, local
activation, and release are separate from the instruction edits and tests
recorded here.
