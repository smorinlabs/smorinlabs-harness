# PR repair and CI validation update: repo-hygiene 0.13.0

Implementation baseline: `e46b8b76cdfc7bf47df0621a811046ca9f171f0f`.
The owner approved implementation after the eight-step audit plan and its
consequence/risk walkthrough. This record covers the local implementation;
it does not claim a release, remote CI result or live skill installation.

## Delivered contract

| Plan step | Result |
|---|---|
| P1 | Both skills use the shared claim, local evidence, selection and handoff contract. PR repairs do not invoke unrelated CI audits. |
| P2 | Inventory retains guards, tolerance expressions, tag filters and effective execution context. Validation hints require inspection and authorization. |
| P3 | Workflow/path/job identity is preserved. Timing reuse additionally requires compatible command, selected scope and environment. Intended-test evidence is required for success. |
| P4 | Failing and affected checks are the default. The approximately 30-second shortcut applies to a measured complete bundle. A full step requires an affected-behavior reason. |
| P5 | Ordinary CI remains enabled. Filtered diagnosis cannot replace expected required coverage on current code. Missing checks and failed-prerequisite skips remain unresolved. |
| P6 | Repairs need post-edit evidence. A CI repair push restarts review collection. Authoritative reopens start a new disposition round; failed resolution retries do not duplicate replies. Merges use the reviewed head guard. |
| P7 | Optimization advice separates measured opportunity from coverage claims. Optional prevention inherits existing authority and joins planned validation when already requested. Public docs and plugin metadata are current. |
| P8 | Focused helper regression tests, original-version controls, instruction scenarios and static compatibility checks provide the evidence below. |

The Linux runner survey, ranking, pins and detection implementation are
preserved. Existing profiler identity, matrix expansion, Jest escaping and
nextest pairing controls remain part of focused verification.

## Executed validation

- **153 focused tests passed in 16.80 seconds** using the existing project
  Python environment. The modules cover workflow inventory, local timing,
  scope planning, CI profiling, failure extraction and Linux runner detection.
- After the review corrections, all 38 planner tests passed in 2.78 seconds.
  The final text-output change then passed its affected test in 2.07 seconds.
- Ruff reported no lint findings in the three edited helpers and their three
  test modules. Formatting was restricted to edited files or changed ranges.
- Generated-manifest consistency passed. The repository's marketplace
  validator passed with its existing generated-metadata warnings.
- Publication checks found no personal paths, private-tooling references,
  unfilled documentation placeholders or marketplace-directory mismatches.
  Both skills' relative Markdown links resolve.
- Comparing identical inputs against the baseline and updated helpers showed:
  the baseline automatically ran a nine-minute full step; the update selects
  affected validation. The baseline emitted a skip marker for filtered
  diagnosis; the update keeps ordinary CI. The baseline treated a literal
  false tolerance expression as true; the update preserves false and excludes
  the guarded publishing command from validation candidates.
- A harmless shell fixture failed with a preparation error for an unresolved
  GitHub expression and produced the expected output after substituting a
  known value. This verifies the distinction, not an automatic expression
  resolver; inventory and instructions deliberately retain unresolved context.

To reproduce the focused Python validation from the repository root:

```bash
uv run python -B -m pytest -q -p no:cacheprovider \
  tests/test_workflow_inventory.py tests/test_local_ledger.py \
  tests/test_ladder_plan.py tests/test_ci_profile.py \
  tests/test_extract_failures.py tests/test_detect_runners.py
uv run harness-kit gen --check
```

## Instruction and adversarial review

The [PR scenario table](../../plugins/repo-hygiene/skills/pr-merge-flow/references/validation-scenarios.md)
and [CI coverage cases](../../plugins/repo-hygiene/skills/ci-fix/references/ci-coverage.md)
trace starting state, required action and permitted completion. They cover
current-code evidence, intended selection, changed and unchanged CI handoffs,
reopens, retries, owner holds, modes, cycle limits and concurrent pushes.
These are source-level acceptance traces, not model execution or live GitHub tests.

The adversarial review requested Opus at high effort and completed with
`claude-opus-5` as the primary reviewer. Its receipt also reports a provider
advisor invocation using `claude-fable-5-1` and auxiliary Haiku usage, despite
built-in CLI tools being disabled. Exact outbound source material and the
system prompt passed credential scanning before transfer. The reviewed packet's
SHA-256 was `ec5762884410bf1abca52baafa93a83a4d877830419d7a50db8d741f45b18dc1`.

All five reported findings were confirmed and corrected locally:

| Finding | Validation and correction |
|---|---|
| Missing profiler output file | Executing the old stdout-only recipe left no profile file. Redirecting the JSON produced a file the real planner consumed. Zero samples now get an explicit empty profile; errors remain preparation failures. |
| Lost timing when a job has no CI profile row | A controlled ledger fixture returned no sample when the workflow name was omitted and returned its five-second sample with the full inventory identity. The command now supplies both workflow name and path. |
| Rung flags confused command scope with pre/post-edit phases | Traced both bundle and ID-only outputs against the prose. The legend now describes command selection, and both the helper and instructions require post-edit reruns. A fast bundle serves as reproducer and post-edit check. |
| Stale browser step numbers | Compared every reported reference against the numbered procedure. Identity points to step 7, the click to step 10 and verification to step 11. |
| Ambiguous reply-first language | The entrypoint now states one sequence: read current state, reply if needed, resolve, then verify. |

The local cross-file review also corrected commit-status producer classification
and rule-policy checks, plus the truncated thread/discussion example. The revised
GraphQL query executed successfully against this repository's closed PR 64,
which returned zero threads. This verifies the live query shape, not pagination
across more than 100 threads; that boundary and long-discussion cases remain
explicit source-level scenarios. The cursor procedure follows the
[GitHub CLI manual](https://cli.github.com/manual/gh_api).

The final corrections were revalidated locally; a second full Opus review was
not run. The review's non-findings preserve runner-specific selector grammars,
measured-bundle provenance rules, mandatory ordinary CI, current-head merge
binding, owner holds, cycle bounds and one-pass behavior.

## Skill quality gate

| Layer | Result | Evidence and limitation |
|---|---|---|
| Content | Pass with advisory | Names and descriptions are valid and resolve to one source per skill. The unchanged review-feedback trigger overlaps the general review-receiving skill, while PR orchestration remains specific. Five adversarial findings were locally confirmed and corrected. |
| Docs | Pass | Skill pages, README, release notes and project tracking are updated; relative links and publication checks pass. |
| Conventions | Pass | Plugin metadata is 0.13.0, both manifests and the marketplace are generated consistently. |
| Static loads | Pass with warning | Claude validates manifest and skills, ignoring the existing generated metadata field. Codex's static check covers only its manifest. Both installed tool versions differ from the verifier's reference versions. |

The local update passes the four-layer gate with the documented advisories.

No fresh-session instruction-following test or live merge was performed.
The static gate cannot prove that either model will follow every instruction.
Ordinary CI remains unchanged and must run when this branch is submitted.

## Compatibility and delivery

Direct callers of `local_ledger.py record` or `median` now supply `--context`
with a non-secret command/scope/environment description. Existing samples
without compatible context remain stored and are ignored for timing reuse.
The planner retains its legacy rung fields while reporting explicit scope;
estimates continue to support wait planning without forcing broad validation.

The update is prepared in an isolated branch. The installed development
symlinks continue to target the main checkout until normal delivery and
synchronization; unrelated work in that checkout is preserved.
