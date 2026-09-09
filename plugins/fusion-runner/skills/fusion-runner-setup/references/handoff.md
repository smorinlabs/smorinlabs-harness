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

## Final operational handoff

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
| `runner.id` | Positive numeric ID of the matching GitHub runner |
| `runner.name` | Registered runner name |
| `runner.labels` | Actual label strings returned by GitHub, including the custom selector |
| `runner.install_directory` | Absolute Windows directory containing this runner |
| `runner.work_directory` | Absolute Windows path resolved from this runner's work-directory setting |
| `runner.service_name` | Exact Windows service name read from this installation's `.service` file |
| `runner.service_account` | Account verified through the service's `StartName`, without its password |

Optional `tools` entries may record tool names, versions, paths, and architectures. Optional `verification` may include `checked_at` in UTC, successful boot/service checks, the runner asset/version/digest, and an actual CI run URL, commit, and conclusion. Record an unrun CI check as unverified, not successful. Optional `observations` may record the final power and connectivity states with a timestamp; all state must be refreshed during the next run.

Do not include registration tokens, personal access tokens, authentication cookies, guest or encryption passwords, private keys, full environment dumps, or copies of the runner's credential files. A secret-free file still contains local paths and repository details and should remain local.

Validate that the JSON parses, required identity fields are populated, `vm.vmx_path` resolves to the intended VM, and the service and GitHub runner refer to the same installation. Record partial setup in a separate progress note if those identities do not yet exist; a partial note is not an operational handoff.
