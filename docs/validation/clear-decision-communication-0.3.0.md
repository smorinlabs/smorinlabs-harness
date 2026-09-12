# Decision context and precision validation

Reviewed on 2026-09-11 from repository base `02ace8a`. This change prepares
`clear-decision-communication` 0.3.0 and `clear-technical-communication` 0.2.3
on branch `fix/decision-context-and-precision`. Merge, release, and activation
through the stable main checkout are distinct from these checks.

## Changes under review

The decision skill now restores the goal-to-component connection before an
unfamiliar question, names the actual artifact and its role, and distinguishes
current state from the commitment an answer authorizes. It asks why owner input
is needed now, separates discoverable facts from policy, and exposes unapproved
implementation assumptions shared by the options. Confusion triggers diagnosis
and rewriting. Changed requirements supersede obsolete options without losing
the user's authorization. Representations address the reader's missing
understanding before technical detail. Tier calculations stay internal unless
requested.

Both skills preserve exact identifiers, artifact types, claim scope,
conditions, and uncertainty. A workflow's declared permissions cannot establish
the effective permissions of a separately acquired credential. A safeguard for
one component cannot silently become a claim about another.

## Package and content checks

| Layer | Result | Evidence and limits |
|---|---|---|
| Content | Pass | Frontmatter unchanged; descriptions remain 805 and 494 characters. Exact names and tool grants are unchanged. Existing documented trigger overlaps and broad preparation tools remain accepted. |
| Documentation | Pass | Both skill pages and README entries updated; nine decision examples and three technical-communication examples. No personal paths or unfilled documentation placeholders introduced. |
| Conventions and generation | Pass | Both plugin versions bumped; `uv run harness-kit gen` and `gen --check` pass. Generated changes affect only the two plugin entries and their manifests. |
| Runner regression | Pass | `uv run pytest -q tests/test_decision_eval_runner.py`: 21 passed in 1.53 seconds after the final case-18 expansion. The suite checks nineteen cases and the added finding coverage; the runner implementation is unchanged. |
| Claude loading | Pass with warning | Static validation and isolated loading pass on Claude Code 2.1.269. The existing generated `_generated` field produces the known ignored-field warning. |
| Codex loading | Pass | Static validation and isolated loading pass on Codex 0.145.0 after retry outside the outer execution sandbox. Initial deep checks could not initialize their local client. |
| Independent review | Pass | Review found and corrected residual sizing commentary, missing existing file paths, and an example that confused pull-request authors with comment authors. Re-review of the three repairs passed. |
| Development placements | Pass | Both tools' existing placements resolve to the stable main checkout. They do not point at the temporary implementation worktree and still serve the previous revision until main is refreshed. |

The verifier's aggregate summary did not expose its initial Codex deep-mode
execution error clearly; the per-tool, per-mode records were inspected before
the successful retry. Static manifest success was not treated as skill loading.
The verifier also reports that installed CLI versions differ from its reference
versions. Its loader checks make no model call and do not prove skill following.

## Behavioral review

Fresh-session outputs are reviewed against both the listed expectations and
the raw facts. Meeting a naming or question-ID criterion does not excuse a
material unsupported claim elsewhere in the response. Such responses receive
an overall semantic failure, with the narrower success retained in the
criterion fields. A process exit is not a semantic verdict.

Cases 1 and 4 retain controls for existing authorization and obsolete replies.
New cases 14-19 exercise concrete artifacts, recovery of project context,
approval stage, confusion, replaced implementation premises, and permission
scope. Expected answers remain separate from the generation prompts.

The latest reviewed responses for the original inputs have these results.
"Pass" means the listed criteria were met and no additional material source
error was found; minor limits remain below. Results span the recorded source
snapshots, not one full rerun of the final source.

| Case | Behavior | Codex | Claude |
|---|---|---|---|
| 1 | Existing approval; do not ask again | Pass | Pass after evidence repair |
| 4 | Reject a reply to a superseded question | Pass | Fail: preserves IDs but invents benchmark scope and implementation constraints |
| 14 | Identify workflows, current state, and activation choice | Pass with incomplete update-trigger coverage | Fail: describes an unexercised trigger as reproduced fixture evidence |
| 15 | Restore project-to-component context | Pass | Fail: infers UI behavior and a maximum data age unsupported by the fixtures |
| 16 | Preserve design approval without authorizing implementation or activation | Pass | Pass |
| 17 | Repair a confused explanation while retaining unchanged IDs | Pass | Pass |
| 18, original input | Replace the enable-switch premise and preserve revised requirements | Pass | Fail: preserves the decision but introduces unsupplied platform behavior as a definite constraint |
| 18, expanded input | Preserve both author checks and planning-only approval in the record | Pass | Fail overall: scope is repaired, but a baseline comparison substitutes a different condition |
| 19 | Preserve credential and safeguard scope during simplification | Pass | Pass after evidence repair |

These are mixed behavioral results. The package is prepared as a draft for
review, not as evidence that every generated decision is correct. The remaining
Claude failures persisted after concrete instruction repairs; no further
unchanged retries were made to seek a passing response.

The initial Claude approval response fabricated a placeholder diff and called
it exact verified evidence. Its final-source response removes that artifact.
The initial permission clarification converted unreported review restrictions
into absent restrictions; the final-source response explicitly preserves them
as unknown. Other retries still broaden benchmark conclusions and tested event
conditions, or infer facts from omitted information. Source inspection remains
necessary when reviewing a consequential generated decision.

An independent reader receives only the complete generated brief and six
neutral questions. Their answers are fixed before comparison with the raw
scenario. This checks whether the brief supplies enough context without the
reader borrowing it from the source conversation.

Two independent-reader checks used different fresh readers. In response BV,
the reader correctly reconstructed the repository, installed but inactive
workflows, configured credential, setting choices, and rollback limits. The
brief illustrated new pull requests but omitted the source's additional update
trigger; this is recorded as incomplete trigger coverage. In response MZ, the
reader correctly distinguished the two token sources, unknown effective
permissions, different bot and author restrictions, and the limit of the
copied-text fixture. No source mismatch was found in that reconstruction.

Neither reader was shown the skill, scenario, model identity, expected answers,
or an earlier version of the same response. Answers were recorded before the
reviewer compared them with the sources. This establishes comprehension of
those two outputs, not of every scenario or future response.

## Source snapshots and retained attempts

The runner records SHA-256 hashes for every supplied instruction file. These
fingerprints hash that filename-to-hash map serialized as sorted JSON without
whitespace. Evaluation inputs and expectations remain unchanged across retries.

| Snapshot | Source-set fingerprint | Runs |
|---|---|---|
| Initial implementation | `fb871071d4de50c83f6ce107c4c8e26901e02ff9bddfb8adaebf193af917ae27` | Eight Claude cases; successful Codex case 14; eight earlier Codex environment failures |
| Example and sizing repair | `5af20150e95aed8590231f60ec6d9d1dc8f0325dcb377748f815d5d8a389d296` | Codex cases 1, 4, and 15-19 |
| Evidence repair | `c0a8da6d2bcfbdf160540e5cf52bf5731f6b644123fead1c4d8bbb47c4043a31` | Codex cases 18-19; Claude cases 1, 4, 14-15, and 18-19; expanded case 18 on both tools |
| Approval-record repair | `7187f0aeef8b5e2a3465d7cfee644401eaee951d6cceb9b35f802f8f84530e0c` | Expanded case 18 on both tools |

The evidence-repair instructions make reproduced actor/trigger conditions
explicit, prohibit fabricated patch evidence and invented approval gates,
preserve missing facts as unknown, and distinguish successful refresh intervals
from failure-case staleness. They also prohibit narration about following the
skill. These were concrete corrections after observed failures. Repeated
failures were retained rather than followed by unchanged retries seeking a pass.

Eight initial Codex attempts exited before producing a model response because
the outer execution sandbox prevented local app-server initialization. They are
inconclusive environment attempts. Successful retries retained Codex's read-only
controls outside that outer sandbox. They did not change project settings or
perform the actions described by the scenarios.

The evaluation guide was subsequently clarified to make overall source-fidelity
failures explicit in grading. That guide is excluded from the model's staged
instruction snapshot; this grading clarification changes none of the fingerprints
or generation inputs above.

Case 18 was subsequently expanded to require both an allowed author association
and current repository write access. The earlier fictional reply required only
the write check; it could not detect loss of the conjunction in the motivating
follow-up. One fresh run per tool exercises the expanded input with the same
final skill snapshot. Earlier case-18 results remain tied to their original
staged inputs and are not graded against the added requirement.

Both tools preserved the two author checks on the expanded input. The first
Claude response nevertheless broadened approval inside its proposed decision
record from updating planning documents to implementing workflow files. The
approval-record repair makes that document part of the scope-consistency check
and gives a paired example of planning versus implementation approval. It also
requires unknown baseline outcomes to remain unknown in comparison tables.

The final targeted run repairs approval scope on both tools: the response and
the proposed decision record both exclude implementation, installation, and
activation. Both also retain association and current write access as separate
requirements. The Claude response still substitutes an unsupported baseline
condition: its missing-credential row says the enable variable is absent and the
job is skipped. The raw inputs do not connect those two absences. That response
therefore remains an overall failure despite the successful approval-scope
repair. No further unchanged retry was made.

Across all snapshots and both versions of case 18, independent review records
28 completed model responses: 16 overall passes and 12 overall failures. The
12 Codex responses pass; the 16 Claude responses include four passes and twelve
failures. These counts include retained earlier attempts and are not a
single-snapshot success rate. The eight initial environment failures are
separate inconclusive attempts. Every listed criterion has an evidence entry;
additional source-fidelity failures are recorded in the existing review summary.

## Limits

These fictional scenarios test communication and intended actions. They do not
execute workflow activation, inspect real service credentials, validate actual
GitHub permission behavior, test native dialog rendering, or prove automatic
skill triggering. Follow-up cases supply a fixed conversation in one fresh
session; they do not run a live multi-turn interaction. Observed passes are
individual results, not estimates of reliability across future sessions.
Comparative reliability against plugin 0.2.0 was not measured.
