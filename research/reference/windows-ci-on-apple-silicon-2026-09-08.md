---
type: terminal
status: historical_proposal
created: 2026-09-08
updated: 2026-09-11
confidence: medium
confidence_basis: September 8 platform research; later Fusion runtime evidence is linked separately. The proposed ci-fix integration remains unimplemented.
verified_example: false
assumptions: An Apple Silicon Mac; narrow Windows CI reproduction; final verification remains on the original GitHub runner.
origin_prompt: topics/windows-on-mac-ci/prompts/00-landscape.prompt.md
sources:
  - https://docs.github.com/en/actions/reference/runners/self-hosted-runners
  - https://github.com/actions/runner-images
  - https://learn.microsoft.com/en-us/windows/arm/apps-on-arm-x86-emulation
  - https://docs.parallels.com/landing/parallels-desktop-developers-guide/command-line-interface-utility
  - https://knowledge.broadcom.com/external/article/315609
  - https://docs.getutm.app/scripting/reference/
---

# Windows CI reproduction on Apple Silicon

This reference preserves the September 8 proposal for extending `ci-fix`,
the GitHub Actions troubleshooting skill, with direct Windows guest execution.
Its initial recommendation was a Parallels Desktop Pro pilot, with VMware
Fusion as the first alternative and the original hosted job as final verification.

The owner subsequently selected Fusion with a registered runner. The
[decision history](../topics/windows-on-mac-ci/DECISION.md) records that change;
the [Fusion validation record](../../plugins/fusion-runner/docs/validation.md)
records three completed smoke jobs and two independent restores by September 11.
The `ci-fix` Windows integration below remains a proposal.

The [full comparison](../topics/windows-on-mac-ci/00-landscape.md) supplies
September 8 prices, product versions, primary sources, and alternatives.
Recheck those dated product claims before a new adoption decision.

## Choose an environment from the failure

An Arm64 guest can reproduce Windows behavior, but an x64 application running inside it still uses an Arm64 operating system. Windows application emulation does not emulate x64 kernel components. Record guest architecture and test-process architecture separately. [Microsoft emulation reference](https://learn.microsoft.com/en-us/windows/arm/apps-on-arm-x86-emulation).

| Required evidence | Local choice | Verification still needed |
|---|---|---|
| A Windows-only path, filesystem, or subprocess failure | Same tool version in the Windows guest, on its own filesystem | Original hosted job |
| Failure in an x64 application or package | Exact x64 runtime under Windows emulation, when supported | Native x64 execution on the original runner |
| Arm64 build or package behavior | Native Arm64 guest tools | Original Arm64 hosted job and its image setup |
| Windows Server, x64 driver, or hosted-image dependence | Record local environment unavailable; investigate original hosted job or remote x64 machine | Matching environment |
| GitHub event, permissions, or action setup | Dedicated diagnostic GitHub job, optionally using a registered guest | Original workflow on the candidate commit |

Use the failed job's recorded operating system, runner architecture, image version, and tool manifest. Do not reconstruct an old failure solely from the current `windows-latest` label. [GitHub image definitions](https://github.com/actions/runner-images).

## Separate execution from registration

The original proposal used direct guest execution by default because the existing skill already extracts the narrowest failing test command. GitHub runner registration adds job orchestration; it is not required to execute a Windows test locally.

If registration is needed, GitHub currently documents Windows Arm64 self-hosted support in public preview. Keep a registered guest scoped to trusted diagnostic work. Ephemeral registration removes its GitHub registration after one job; cleaning the VM remains separate. [Self-hosted runner reference](https://docs.github.com/en/actions/reference/runners/self-hosted-runners).

Do not use `act` as a substitute for Windows. Its host mode must run inside Windows, and its documented omissions include job timeouts and run-step cancellation. [act host mode](https://nektosact.com/usage/runners.html), [act limitations](https://nektosact.com/not_supported.html).

## Proposed evidence record

Each reproduction should emit a record with the fields below, alongside logs. The values marked null are information to collect from the failed run, inspected guest, and selected source. This is a proposed record format. It has not been implemented and does not describe a completed run.

```yaml
source:
  base_commit: null
  patch_sha256: null
  input_manifest_sha256: null
ci:
  run_id: null
  job_id: null
  runner_label: null
  runner_architecture: null
  image_version: null
  software_manifest_url: null
local:
  provider: null
  provider_version: null
  baseline_id: null
  vm_id: null
  host_architecture: null
  guest_os_edition: null
  guest_os_build: null
  guest_architecture: null
  process_architecture: null
  artifact_target: null
  execution_user: null
  shell_path: null
  shell_version: null
  working_directory: null
  tool_versions: {}
  action_pins: {}
  relevant_environment: {}
execution:
  command: null
  timeout_seconds: null
  startup_elapsed_seconds: null
  test_elapsed_seconds: null
  exit_code: null
  outcome: not-run
  evidence_scope: null
  stdout_path: null
  stderr_path: null
  artifacts: []
cleanup:
  guest_processes_stopped: null
  github_registration_removed: null
  guest_state_restored_or_discarded: null
```

`base_commit` identifies the initial Git source. `patch_sha256` identifies an applied patch when changes are uncommitted. `input_manifest_sha256` covers the actual source inputs, including intended untracked files. `evidence_scope` describes the environment actually tested. It must never imply native x64 CI from an Arm64 guest. Environment records must omit secret values; record names and nonsecret settings only. A null value must not silently become an inferred match.

## Execution and reset contract

The future backend should provide the following behavior:

1. Acquire exclusive use of a named baseline or disposable VM. Confirm the guest tools, runtime, shell, source-transfer mechanism, and resource limits before treating the environment as available.
2. Start the guest with a separate readiness deadline. Verify a guest command succeeds; power-on status is insufficient.
3. Populate a Windows-local checkout and verify source identity. Preserve the failed command's wrapper, shell, working directory, and relevant environment.
4. Execute the targeted command and preserve its exit status, output streams, elapsed time, and artifacts. Keep transport failure, setup failure, test failure, timeout, and success distinct.
5. On completion or timeout, export evidence and terminate all work associated with the run. Stop the VM if process termination cannot be confirmed. Mark an unclean environment unusable until recovery completes.
6. Restore the baseline or discard the disposable state. Confirm runner deregistration separately when registration was used. Keep credentials out of reusable baselines.

Parallels supplies `prlctl exec`, `prlctl clone`, and `prlctl snapshot-switch` as relevant command interfaces. Guest execution requires Parallels Tools. Pro or higher supplies the documented CLI. The original [guest command documentation](https://docs.parallels.com/landing/parallels-desktop-developers-guide/command-line-interface-utility/manage-virtual-machines-from-cli/general-virtual-machine-management/execute-a-command-in-a-virtual-machine), [clone documentation](https://docs.parallels.com/landing/parallels-desktop-developers-guide/command-line-interface-utility/manage-virtual-machines-from-cli/general-virtual-machine-management/clone-a-virtual-machine), and [snapshot documentation](https://docs.parallels.com/landing/parallels-desktop-developers-guide/command-line-interface-utility/manage-virtual-machines-from-cli/snapshot-management/reverting-to-a-snapshot) are the implementation entry points.

A host CLI timeout alone is not a process-tree cleanup contract. Windows Job Objects offer a mechanism for terminating associated processes, but their integration and exceptional cases still require testing. VM shutdown is the independent fallback. [Microsoft process-group control](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects).

For Fusion, use the versioned [feature matrix](https://knowledge.broadcom.com/external/article/315609) and validate the precise guest operations in the installed version. For UTM, use its [guest scripting API](https://docs.getutm.app/scripting/reference/) with QEMU guest tools. Do not claim equivalent cancellation semantics across providers without a probe.

## Minimal acceptance experiment

All examples and sequences remain empirically untested. The pilot should produce these discriminating results before automatic use:

| Probe | Required observation |
|---|---|
| Guest exit 0 and intentional exit 7 | Host records the two distinct outcomes correctly |
| Separate stdout and stderr markers | Both captured and attributed to the same source and command |
| Known failing commit, intended fix, restored defect | Failure, success, failure for the same targeted check |
| Timed-out command with child process | Host records timeout, descendants stop, and cleanup completes |
| Interrupted host transport | Recovery detects the unfinished run and prevents reuse until cleanup |
| Fresh run after reset | Earlier files, running processes, and credentials are absent |
| Original hosted job on candidate commit | Actual CI result recorded independently of the VM result |

Preserve the skill's existing duration profile, reproduction-before-editing rule, local neighbor checks, and final GitHub verification. Initial VM allocations and hosted durations are not measured local test timings.

## Currency and confidence

Verified on September 8, 2026 against documentation and local hardware inspection. No Windows VM, test suite, self-hosted job, action, or benchmark was run during that research. Later Fusion execution is recorded separately above. Recheck moving image labels, action pins, supported guest tools, product build, and prices before adoption. The original checkout used for integration analysis was `0a737f44cf2f2d70e76bcf0abc1532319af11afc`.

Confidence is high for the platform distinctions and medium for the untested integration. The first pilot may select Fusion over Parallels if its guest-control behavior meets the same contract with acceptable setup effort.
