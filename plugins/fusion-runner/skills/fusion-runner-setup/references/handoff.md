# Local runner handoff

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
