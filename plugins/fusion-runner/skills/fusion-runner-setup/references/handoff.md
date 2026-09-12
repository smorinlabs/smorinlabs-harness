# Local runner handoff

## Record partial setup as you work

Keep an installation log and a current progress note in an ignored local
directory, separate from the operational handoff below. Check ignore behavior
before writing. Update the files after each completed stage and before handing
an interactive prompt to the user; do not wait until installation finishes.

Each entry records the UTC timestamp, actual installer or app version, screen
title and control labels, action taken, observed result, and next action with
its owner. Record selected ISO and VM paths locally. Distinguish actions observed
directly from actions the user reports completing. Mark proposed settings,
pending prompts, and unrun checks explicitly. On resume, inspect the current
machine and screen before repeating an action from the log.

Never record passwords, tokens, recovery keys, or screenshots containing those
values. A password step can say "user completed the encryption prompt" without
its value. A VM creation screen does not establish Windows boot or a CI pass.

When the task includes improving this public skill, add reusable instructions
to the installation reference as stages are observed. Include the release and
architecture for version-specific screen labels. Remove personal paths and
identities, and label vendor-documented steps that were not observed. Leave
local machine evidence in the ignored record.

## Secret-free operational profile

Write a UTF-8 JSON file that identifies the installed VM and runner for future operation. Put it in a user-owned local configuration directory, or an ignored `.fusion-runner/` directory near the project. Choose the actual filename from the VM/profile name and report its absolute path. Check repository ignore behavior before writing project-local machine state; do not commit it into a public repository.

Use `schema_version` equal to `1`. Populate fields from observed state, not proposed values. The following paths refer to nested JSON properties:

| Property | Value and source |
| --- | --- |
| `schema_version` | Integer `1` |
| `vm.vmx_path` | Absolute path to the actual `.vmx` file on the Mac |
| `vm.display_name` | VM name observed in Fusion |
| `guest.os_arch` | `ARM64` or `X64`, verified inside Windows |
| `guest.windows_version` | Windows edition, version, and build observed in the guest |
| `runner.scope_type` | `repository` or `organization` |
| `runner.scope_url` | Exact GitHub URL used to register the runner |
| `runner.id` | Positive numeric ID of the matching GitHub runner; `null` only in a prepared but unregistered profile |
| `runner.name` | Registered runner name, or the intended unique name before registration |
| `runner.labels` | Actual label strings returned by GitHub; before registration, the explicitly marked intended list |
| `runner.install_directory` | Absolute Windows directory containing this runner |
| `runner.work_directory` | Absolute Windows path resolved from this runner's work-directory setting |
| `runner.service_name` | Exact Windows service name read from this installation's `.service` file |
| `runner.service_account` | Account verified through the service's `StartName`, without its password |
| `runner.service_account_sid` | Windows security identifier of the dedicated local service account; required by the protected registration helper |
| `registration.mode` | `ephemeral` for one job or `persistent` for a reusable registration |
| `registration.invocation` | Unique registration identifier preserved in host intent and guest receipt |
| `registration.phase` | Observed lifecycle phase, such as `prepared`, `service-verified`, or `retired`; never a readiness assertion |

The `registration` properties describe helper-managed registration. Do not
invent an invocation for an existing interactive persistent installation that
has no such intent/receipt. Record its observed mode and identity instead.

Optional `tools` entries may record tool names, versions, paths, and architectures. Optional `verification` may include `checked_at` in UTC, successful boot/service checks, the runner asset/version/digest, and an actual CI run URL, commit, and conclusion. Record an unrun CI check as unverified, not successful. Optional `observations` may record the final power and connectivity states with a timestamp; all state must be refreshed during the next run.

Do not include registration tokens, personal access tokens, authentication cookies, guest or encryption passwords, private keys, full environment dumps, or copies of the runner's credential files. A secret-free file still contains local paths and repository details and should remain local.

Validate that the JSON parses and `vm.vmx_path` resolves to the intended VM.
For a registered profile, prove that the service and GitHub runner refer to the
same installation. Refresh IDs, labels and the exact service name after every
new registration. The one-job registration helper uses only its exclusive
`fusion-ci-<registration-id>` label and omits default platform labels. Do not
add `self-hosted`, `Windows` or an architecture label to the handoff unless
GitHub actually returns it.

A prepared profile is sufficient for a read-only `ci-fix` survey when Windows
architecture, intended repository/name/labels and the actual VM path are known.
Set its `runner.id` to `null`, mark intended values and leave nonexistent service
identity unset. This reports `unregistered`; it is not an operationally ready
runner. Earlier incomplete installation stages remain in the separate progress
record. After retirement, preserve the completed registration's identity in its
receipt and mark the current profile `retired`; a subsequent registration gets a
fresh identity.

## Preserve registration identity before transport can fail

For protected
[one-job registration](runner-provisioning.md#one-job-diagnostic-registration),
save a host intent before invoking guest configuration. It identifies the exact
repository, VM, registration invocation, intended runner name, guest runner
directory, dedicated account name/SID, requested mode, guest receipt path and
UTC start time. It contains no credential input. Keep it and the eventual guest
receipt in ignored or user-owned local storage.

`scripts/register_service.ps1` writes a guest receipt before `config.cmd`, then
updates it in cleanup even if configuration fails. Its fields include
`runner_id`, `runner_name`, `service_name`, `service_account`,
`service_account_sid`, `runner_directory`, `ephemeral`, `labels`,
`configuration_finished`, `phase`, and native/process architecture. The guest
receipt's `invocation` must match the host intent. `configuration_finished`
means the configuration attempt ended; it does not establish successful
registration, a verified service, GitHub readiness, or a passed job.

If guest configuration succeeds but the transport response is lost, retrieve
the saved guest receipt and inspect the installation's `.runner` and `.service`
identities through the established protected connection. Reconcile those
observations with a current, authorized GitHub runner list. Do not overwrite
the intent, register a replacement, or treat missing stdout as proof that no
runner exists. If identity or process state remains uncertain, preserve the VM
and report the specific missing observation.

The CI diagnostic receipt is separate: `windows_runner.py dispatch` creates its
own invocation for the workflow run, selected tests and artifact. Link it to the
verified registration through the recorded runner ID/name. A diagnostic's
successful collection does not itself perform registration retirement.
