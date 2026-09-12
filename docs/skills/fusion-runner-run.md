# fusion-runner-run

Start, inspect, and gracefully stop a Windows GitHub Actions runner already
configured in VMware Fusion. It uses the setup handoff to identify the exact VM,
Windows service, GitHub runner, and labels. It distinguishes a registered runner
from a prepared VM whose prior one-job registration was retired. It checks VM
power and GitHub readiness separately.

**Triggers on:** "start my Fusion runner", "is my Windows runner online?",
"stop the Fusion CI VM".
**Arguments:** none; describe the operation and give the setup handoff path when
the session does not already have it.

## Install

Install `fusion-runner@smorinlabs-harness`, which contains this skill and
`fusion-runner-setup`:

```text
/plugin marketplace add smorinlabs/smorinlabs-harness
/plugin install fusion-runner@smorinlabs-harness
```

| Mode | When to use it | Instructions |
|---|---|---|
| Plugin | Normal use | Commands above; Codex marketplace setup is in the [README](../../README.md#install) |
| Development symlink | Use a local editable clone | [Both-tool symlink commands](fusion-runner-setup.md#install) |
| Direct copy | No marketplace connection | Copy both complete skill directories into `~/.claude/skills` or `~/.agents/skills` |

## What operation means

| Request | Behavior |
|---|---|
| Start | Locate the recorded VM, start it if needed, and wait a bounded time for an existing registration to connect; a retired one-job profile needs fresh setup registration |
| Status | Report VM power, runner connection, idle or busy status, and labels; inaccessible GitHub state remains unknown |
| Stop | Check active work, stop the exact runner service, verify it is offline, then shut down the guest gracefully |
| Failed startup | Inspect Fusion, Windows, the service, and runner diagnostics without reinstalling or deleting the VM |
| Completed or failed one-job diagnostic | Preserve evidence, prove the exact job ended and registration is retired, then remove only the owned stopped service registration and shut down gracefully |

The helper accepts paths with spaces, refuses an unrecognized VM inventory,
avoids passwords in command arguments, and supports a dry run. Its success
confirms a VM power observation, not completion of a CI job. Optional
`--wait-seconds` polls the power inventory within one total deadline, including
the initial inspection and power request. It does not resend that request,
extend the deadline for each poll, or wait for GitHub readiness. The default
retains one post-request observation. Windows 11 VM
encryption can require an interactive Fusion unlock before headless operation
works.

Use an existing verified guest connection for diagnostics. Windows login names
come from `whoami`, not the display name. Machine-specific access automation,
credentials, and backup locations belong in the user's local or private records;
this public skill does not depend on a private setup. Starting the working VM
preserves its files. A saved baseline is a separate recovery artifact, and an
ordinary start request does not authorize restoring it.

Stopping a busy runner can interrupt its job. GitHub's idle status is a snapshot,
so a noninterrupting stop requires a window in which new jobs cannot be assigned.
Without that window or explicit authorization to interrupt a racing job, the
skill leaves the runner online and reports the unresolved stop. It does not force power
off, suspend active jobs, or delete a VM as a fallback. Mac sleep or lid closure
can make the runner unavailable; the skill addresses power management for the
requested running period without silently installing a permanent Mac daemon.

For an ephemeral runner, a verified terminal job plus current proof that its
registration is retired supplies a barrier against further admission. Preserve
failed-job logs and partial-configuration receipts before cleanup; a passing
report is not required. The public `retire_service.ps1` helper separately checks
the exact installation, stopped service, registration ID/name and absence of
runner processes. It removes only registration files and the owned service.
Its `github_registration_absent` input is an attestation of host-side checks,
not a GitHub query. Unknown identity, active work or uncertain retirement leaves
the VM available for inspection. See
[one-job recovery](../../plugins/fusion-runner/skills/fusion-runner-run/references/operations.md#one-job-completion-and-failure-recovery).

## Example sessions

> "Start the Fusion runner from the setup handoff and tell me when GitHub can
> accept a job."

The agent starts the chosen VM, checks the recorded runner ID in GitHub, and
reports whether it is idle, busy, offline, or unreachable.

> "Stop that runner after the current job finishes."

The agent observes the job, follows the shutdown procedure, verifies the exact
service and GitHub state, and then requests a graceful guest shutdown. It reports
any remaining uncertainty instead of claiming the machine stopped.

## Validation

Automated tests exercise the helper with a simulated `vmrun` executable,
including idempotence, an unrelated running VM, paths containing shell syntax,
timeouts, malformed output, FIFO refusal, and shutdown guards. By 2026-09-11,
the original Fusion Windows 11 Arm64 VM and two independent downloaded restores
passed real local CI jobs under fresh standard-account runner services. Native
SSH/SFTP, signed-out reboot access before registration, and graceful shutdown
also passed. These were one-job registrations; persistent runner restart after
registration and unattended encrypted startup on a locked Mac remain unverified.
The new bounded polling and retirement interfaces have separate automated
checks; they do not turn those historical jobs into live tests of the new paths.
See the [validation evidence and limits](../../plugins/fusion-runner/docs/validation.md),
[operations reference](../../plugins/fusion-runner/skills/fusion-runner-run/references/operations.md),
and [helper interface](../../plugins/fusion-runner/docs/cli-interface.md).
