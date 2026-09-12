# Windows diagnostics through a Fusion runner

Use this path when a Windows failure needs an actual Windows guest and the
user has a suitable Fusion installation. GitHub Actions schedules the diagnostic
on committed, pushed code; Windows on the Mac executes it. Keep host/Linux
reproduction and the ordinary required CI run in the repair plan.

`scripts/windows_runner.py` surveys the configured runner, dispatches one
diagnostic, and verifies its report. The `fusion-runner-setup` and
`fusion-runner-run` skills own VM preparation, protected guest access,
registration, and shutdown. This integration has no private-repository or
private-script dependency. If those skills or a prepared guest are unavailable,
report that preparation gap before selecting this route.

## 1. Check fidelity and admission before registration

Read the failing workflow and selected matrix cell. Compare the Windows edition
and build, OS and process architecture, shell, toolchain versions, setup actions,
services, permissions, environment, and intended artifact target with the guest.
Windows 11 Arm64 does not establish equivalence with Windows Server x64.
Emulated x64 execution does not prove a native Arm64 toolchain. Retain unsupported
requirements explicitly; do not retarget a production `windows-latest` job or
silently change its tool versions to fit the guest.

Start with one-job registrations for a trusted repository. The public setup
helper gives each registration an exclusive `fusion-ci-<registration-id>` label
and omits GitHub's default labels. Therefore the usual
`[self-hosted, Windows, ARM64, fusion-ci]` selector will not match it. Use the
actual registered label list. Verify no other runner shares that invocation
label and inspect jobs that can target it before registration starts the service.
Labels route jobs; repository permissions still determine who can submit code.
Do not run untrusted fork revisions on the Mac.

Two identifiers have separate roles:

| Identifier | Created by | Purpose |
| --- | --- | --- |
| Registration invocation | The Fusion setup operation | Names the runner and its exclusive routing label; preserved in host intent and guest receipt |
| Diagnostic invocation | `windows_runner.py dispatch` | Identifies a workflow dispatch, artifact, report, and local receipt |

A completed one-job registration cannot accept the repaired job. Retire it and
register a fresh identity for the next dispatch. This does not restore Windows,
delete working files, or establish isolation between untrusted jobs. GitHub
documents automatic retirement after one processed job in its
[ephemeral runner lifecycle](https://docs.github.com/en/actions/reference/runners/self-hosted-runners#ephemeral-runners-for-autoscaling).

## 2. Survey without starting anything

The commands below run in the target repository's **macOS terminal**. Resolve
these values from the current installation; keep machine state outside version
control:

| Variable | Source |
| --- | --- |
| `CI_FIX_PYTHON` | Python 3 executable resolved with `command -v python3` |
| `CI_FIX_GH` | Authenticated GitHub CLI executable resolved with `command -v gh`; verify `gh auth status` without printing tokens |
| `CI_FIX_SKILL` | Absolute directory of this installed `ci-fix` skill |
| `CI_FIX_REPOSITORY` | Exact `owner/repository` established from the Git remote and GitHub API |
| `CI_FIX_HANDOFF` | Absolute path to the secret-free Fusion JSON handoff |
| `CI_FIX_ARCHITECTURE` | `ARM64` or `X64`, chosen after the workflow/guest comparison |

```sh
"$CI_FIX_PYTHON" "$CI_FIX_SKILL/scripts/windows_runner.py" survey \
  --repository "$CI_FIX_REPOSITORY" --handoff "$CI_FIX_HANDOFF" \
  --architecture "$CI_FIX_ARCHITECTURE" --gh "$CI_FIX_GH" --json
```

The handoff uses schema version `1` and a repository scope on `github.com`.
Its `vm.vmx_path` must resolve to the observed VM configuration, and
`guest.os_arch` must come from Windows. A prepared but unregistered profile may
have `runner.id: null`; its intended name and labels are still required. Never
pass private credential configuration as a handoff.

The survey reads Fusion's power inventory and GitHub's paginated runner list.
It creates no registration, starts no VM, and writes no local state. A successful
survey command means that the survey completed; inspect its `state`:

| State | Meaning and next action |
| --- | --- |
| `ready` | Recorded VM is running; the exact runner is online and idle, its full label set matches the handoff, and no other listed runner matches that routing set |
| `busy` | That runner has work; inspect its job and wait within the chosen bound |
| `offline` | VM is running but the recorded runner is disconnected; inspect its exact service and connectivity |
| `vm_not_running` | Registration exists but its recorded VM is not in Fusion's running inventory; use Fusion operations |
| `unregistered` | Exact runner ID is absent, or the prepared profile has no ID; reconcile prior registration before creating one |
| `incompatible` | Recorded guest architecture differs from the requested architecture |

`power_state` is reported separately, including for an unregistered profile.
`not_running` can include a suspended VM. Invalid inventory, uncertain API
access, changed identity/labels, or an online runner whose VM is absent produces
an error. Preserve that uncertainty; do not convert it into readiness or proof
that a runner is retired. Recorded guest architecture is checked again in the
actual diagnostic report.

For a stopped or unregistered prepared guest, use Fusion's
[registration procedure](https://github.com/smorinlabs/smorinlabs-harness/blob/main/plugins/fusion-runner/skills/fusion-runner-setup/references/runner-provisioning.md#one-job-diagnostic-registration)
and
[operations procedure](https://github.com/smorinlabs/smorinlabs-harness/blob/main/plugins/fusion-runner/skills/fusion-runner-run/references/operations.md).
Refresh the handoff and repeat the survey afterward. Audit mode stops at the
read-only observations.

## 3. Prepare the repository's diagnostic workflow

Use an existing suitable workflow or prepare the concrete addition within the
current task's authority. The supplied
[workflow example](examples/windows-diagnostic.yml) installs as
`.github/workflows/windows-diagnostic.yml`; its
[PowerShell adapter](examples/windows-diagnostic.ps1) installs as
`scripts/windows-diagnostic.ps1` in the target repository. The two example
checks, `windows-file-roundtrip` and `native-child-exit`, verify Unicode file
content and a native child process's exit code. They prove only those checks.
Replace or extend the adapter with the application's actual diagnostic tests
before using it to verify an application repair.

Manual dispatch requires the workflow to
[exist on the default branch](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/manually-run-a-workflow).
Its selected pushed ref must also contain the trusted workflow
and report adapter. Prepare and review that change before any missing merge or
publish decision; the CI skill itself does not merge.

The helper's workflow contract is exact:

| Workflow element | Required value |
| --- | --- |
| Event | `workflow_dispatch` |
| Dispatch input names | `diagnostic_id`, `runner_labels`, `test_ids`, `expected_architecture` |
| `run-name` | `Windows diagnostic ${{ inputs.diagnostic_id }}` |
| Diagnostic job `name` | `Windows diagnostic` |
| Diagnostic job `runs-on` | `${{ fromJSON(inputs.runner_labels) }}` |
| Report artifact name | `windows-diagnostic-${{ inputs.diagnostic_id }}` |
| Artifact contents | Exactly one file named `windows-diagnostic.json` |

`runner_labels` and `test_ids` are JSON arrays encoded in string inputs.
`expected_architecture` is the string `ARM64` or `X64`; the supplied workflow
presents these as a choice input.
`test_ids: []` requests the complete diagnostic check, not an empty test run.
Choose complete scope only when the repair contract justifies it. Accept exactly
one diagnostic job; a matrix that produces multiple matching job names is
ambiguous to the collector.

Preserve the original job's relevant setup, tools and test command. The
repository-specific adapter must pass selected IDs as data to the test runner,
verify the actual selection, and translate its supported test report into this
schema. Do not interpolate input expressions into shell code, evaluate test IDs
as commands, manufacture passing results, or reuse stale report files. A setup
error, cancelled run, unsupported selector, or zero tests is not a test pass.
Upload the current report with the workflow's failure-safe artifact step so a
real test failure still retains evidence. Keep the job failed when a test fails.

The report has these fields:

| Field | Required type and source |
| --- | --- |
| `schema_version` | Integer `1` |
| `commit` | Exact checked-out commit, compared with the dispatch receipt |
| `invocation` | Diagnostic invocation from `diagnostic_id` |
| `run_id`, `run_attempt` | Numeric GitHub run identity and attempt |
| `runner_name` | Actual `RUNNER_NAME`, compared with the registered identity and jobs API |
| `operating_system` | `Windows`, observed in the job |
| `architecture` | `ARM64` or `X64`, from the runner's observed architecture |
| `native_architecture`, `process_architecture` | Native OS and process observations, each equal to the requested architecture |
| `is_administrator` | Boolean `false`, proved from the job's Windows token |
| `tests` | Nonempty array of unique `{ "id": "actual-test-id", "status": "passed" }` or `"failed"` outcomes |
| `status` | `passed` only when every listed test passed; otherwise `failed` |

The collector requires exact selected-ID membership when a selection was
provided. Report status must agree with test outcomes and the GitHub job
conclusion. An extra aggregate or placeholder test ID cannot stand in for the
selected tests. Preserve relevant command, tool versions, durations and native
test output in the logs or additional report fields.

## 4. Dispatch once and collect the evidence

In the same target repository, set `CI_FIX_WORKFLOW` to the active workflow
filename or numeric ID and `CI_FIX_REF` to the trusted pushed branch or tag.
Set `CI_FIX_RECEIPT` to a new local JSON filename in the diagnostic scratch
directory. Optionally set `CI_FIX_SELECTION` to a UTF-8 JSON file containing the
unique test IDs extracted and verified during localization. Omit `--selection`
below when requesting the justified complete diagnostic check.

Preflight without dispatch or receipt writes:

```sh
"$CI_FIX_PYTHON" "$CI_FIX_SKILL/scripts/windows_runner.py" dispatch \
  --repository "$CI_FIX_REPOSITORY" --handoff "$CI_FIX_HANDOFF" \
  --architecture "$CI_FIX_ARCHITECTURE" --gh "$CI_FIX_GH" \
  --workflow "$CI_FIX_WORKFLOW" --ref "$CI_FIX_REF" \
  --selection "$CI_FIX_SELECTION" --receipt "$CI_FIX_RECEIPT" --dry-run --json
```

After establishing authorization for that repository and revision, run the same
command with `--yes` in place of `--dry-run`. The helper checks readiness,
resolves the pushed ref to a commit, and saves a new receipt **before** the
dispatch request. The dry-run invocation ID is only a preview; the actual
dispatch generates its own ID. Do not use `--yes` as a substitute for inspecting
the workflow's trust and admission conditions.

Keep the selected ref stable until the run starts. Collection rejects a run
whose commit differs from the resolved receipt. If the dispatch request times
out, retain the receipt and collect it: an uncertain response can still mean the
workflow was created. Do not create another receipt and dispatch again to
recover from an ambiguous response.

Collect with a total deadline based on relevant queue/execution evidence.
`CI_FIX_WAIT_SECONDS` is that integer bound, from `1` to `1800` seconds:

```sh
"$CI_FIX_PYTHON" "$CI_FIX_SKILL/scripts/windows_runner.py" collect \
  --repository "$CI_FIX_REPOSITORY" --gh "$CI_FIX_GH" \
  --receipt "$CI_FIX_RECEIPT" --timeout "$CI_FIX_WAIT_SECONDS" --json
```

Each helper operation defaults to `120` seconds. Collection can be resumed from
the same receipt after a deadline; elapsed time is not permission to cancel a
job or stop Windows. Match the exact run title, resolved commit, run attempt,
diagnostic job, runner ID and runner name. Multiple matches or a changed attempt
require inspection, not an arbitrary choice. Review any job rerun separately;
the existing receipt remains evidence for its original attempt.

Once the uniquely identified job completes, collection saves its log as a neighboring
`.job.log` file before checking runner identity or requiring an artifact. Logs over
16 MiB retain their first 16 MiB and set `job_log_truncated: true` in the receipt;
retrieve the full log separately when later output is needed. An oversized report
archive is rejected. Collection saves the decoded report as
`.report.json`, then verifies it. Treat reports and logs as private job data.
`evidence_verified: true` and `diagnostic_outcome: passed|failed` describe a
verified test result. A file merely existing is insufficient.

| Outcome | Meaning |
| --- | --- |
| Exit `0`, verified `passed` | Intended diagnostic tests passed on the recorded Windows runner |
| Exit `1`, verified `failed` | Intended tests ran and at least one failed; this can establish reproduction |
| Exit `2` | Invalid input or saved state; repair preparation before another attempt |
| Exit `3` | GitHub CLI is unavailable; resolve the execution prerequisite |
| Exit `5`, including `no_selection` or a deadline | Selection, readiness or waiting requirement remains unresolved |
| Other error, including missing/mismatched evidence | Inspect the error and retained logs; do not claim a reproduced test failure or success |

Exit `1` can also report an API or evidence error, so inspect the receipt and
error code instead of classifying by exit status alone. Missing artifacts after
a setup failure are an environment/preparation problem until logs establish the
cause. A changed ref, wrong runner, zero tests, or mismatched report cannot count
as verification of the repair.

## 5. Retire safely and complete the repair

Use the Fusion
[diagnostic retirement procedure](https://github.com/smorinlabs/smorinlabs-harness/blob/main/plugins/fusion-runner/skills/fusion-runner-run/references/operations.md#one-job-completion-and-failure-recovery)
after a pass, a failure, or partial registration. Preserve logs, host intent,
guest receipt and invocation receipt first. A passing report is not a cleanup
prerequisite. Current proof that the exact job ended and new work cannot be
admitted is a prerequisite. `busy: false` and an empty queue are snapshots, not
an admission barrier. Missing evidence or active/unknown worker state leaves
the service and VM available for inspection.

Record VM startup/registration, queue, test execution, and collection time
separately. Do not record GitHub-scheduled Windows timings as compatible
pre-push local ledger samples. Reproduce on the failing revision, repair and
push, then verify the selected and affected tests through a fresh registration.
Reconcile ordinary required CI on the repaired revision before completing the
handoff to `pr-merge-flow`.

The historical Fusion validation proves three native Arm64 one-job executions
and two restored guests. It does not prove this new diagnostic adapter, a
persistent post-registration reboot, unattended encrypted startup on a locked
Mac, Intel Fusion, or another-Mac recovery. Report each current live scenario
only when its own runner/job evidence exists.
