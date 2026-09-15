# Test local changes in a prepared Windows VM

Use this path for a Windows check whose current Mac worktree files need testing
before a push. `windows_local.py` captures those files and runs the selected
PowerShell command in a separate Windows directory. No GitHub registration or
dispatch is needed. Ordinary required CI still runs after the validated push.

## Select the workload before inspecting Fusion

Generate the normal `workflow_inventory.py --json` inventory first. If it has no
Windows job or resolved Windows matrix cell, stop Windows discovery here.
Do not inspect Fusion, saved images or guest credentials for a Linux-only task.

Read the selected job's steps and effective shell, environment, working directory
and matrix values. Identify the check and necessary preparation. Compare its
architecture, toolchain, services and permissions with the prepared guest before
comparing speed. A native Windows Arm64 check can be suitable on an Arm64 VM;
that result does not establish Windows Server x64 or hosted-image equivalence.
Unresolved workflow expressions and required Git metadata are preparation gaps.

Choose scope using `validation-contract.md`: use a compatible complete bundle
only when its measured total, including necessary preparation, is about 30 seconds
or less. Otherwise reproduce the failing IDs and affected behavior. A full step
needs an affected-behavior reason. Unknown timing permits one bounded informative
check, not a full suite for calibration.

## Prepare access through Fusion

`fusion-runner-setup` and `fusion-runner-run` own VM setup, power and guest
transport. Supply their installed skill directories to the adapter when they are
not adjacent to this plugin. An installed private image/access provider can
supply its existing configuration. This public plugin contains no saved image
or credentials and does not require a private repository.

If Fusion is absent, use setup's installation guide. If the configured guest is
absent, use setup's [manual runner guide](https://github.com/smorinlabs/smorinlabs-harness/blob/main/plugins/fusion-runner/skills/fusion-runner-setup/references/create-your-own-runner.md).
If only guest access or tools are missing, prepare that existing VM. Do not
infer that Windows needs reinstalling. Follow existing authorization; a new
security-sensitive access change may need its own concrete owner decision.

The adapter needs macOS native OpenSSH/SFTP, Python 3.10 or newer, `pexpect==4.9.0`,
native Windows PowerShell 7, and an enabled **standard Windows account**. Resolve
`uv` and use `uv run --no-project --with pexpect==4.9.0 python` when the dependency
is not already installed. Guest authentication uses the provider's existing
password through a protected hidden prompt and an authenticated pinned host key.
It does not change SSH policy, create credentials, or elevate tested code.

The provider supplies two separate local JSON files:

| File | Required fields |
| --- | --- |
| Non-secret Fusion profile | `vm.vmx_path`: observed absolute VMX path; `guest.os_arch`: verified `ARM64` or `X64` |
| Private access file | `address`: current guest IP; `port`: SSH port, default 22; `username`; `password`; `host_public_key`: authenticated OpenSSH key type and base64 data; `account_sid`: expected standard-account SID |

The access file must be a regular file owned by the current Mac user with mode
`0600`. Keep it outside tested source and public Git. Refresh the address and
guest identity after startup or reset. Preserve normal encryption and account
separation. A reset restores baseline access settings, so recheck preparation.

If Windows denies service/process inventory to the standard SSH token, add an
`admission_access` object with the same access fields for the existing maintenance
account. Its address, port and host key must match the standard account's guest;
its SID must differ. This account performs only a fixed read-only inventory.
Tested source and commands always run under the standard account. Keep both
credentials in the same owner-only file outside captured source. Include the
observer connection in local setup and collection timings.

## Describe the actual command

Create a non-secret execution specification outside the captured repository.
For example, a repository with a native Arm64 PowerShell check could use:

```json
{
  "schema_version": 1,
  "workflow_path": ".github/workflows/windows.yml",
  "job": "test",
  "architecture": "ARM64",
  "shell": "pwsh",
  "command": "./scripts/test-paths.ps1",
  "scope": "Windows path parsing assertions",
  "working_directory": ".",
  "environment": {},
  "execution_identity": {"powershell": "7.6.4", "dependencies": "inspected lockfile digest"},
  "timeout_seconds": 120,
  "snapshot_exclude": [],
  "expected_test_ids": ["paths::leaf"],
  "evidence": {"kind": "junit", "path": "artifacts/tests.xml"}
}
```

This is an example command, not a claim that those files or tools exist in the
target repository. Substitute the inspected workflow, command and report path.
`workflow_path` must exactly match the inventory's path. For a matrix, add
`matrix_cell` with enough actual axis values to select one Windows cell.
Record relevant observed tool versions and dependency identity in
`execution_identity`; refresh it when the environment changes. Tool installation
or dependency setup must be completed and timed before declaring compatibility.

The command receives the explicit non-secret environment values. PowerShell's
stop-on-error and native child exit behavior match a GitHub `pwsh` run step.
Expressions such as `${{ matrix.version }}` must be resolved before execution.
Put test IDs into the runner's supported selector, not interpolated shell code.
Do not use this bounded adapter to launch services or detached background work.

Reports can be JUnit XML, JSON, or command-only evidence. JUnit IDs are
`classname::name`, or `name` when `classname` is absent. JSON contains a `tests`
array of unique objects with `id` and `status` equal to `passed`, `failed`, or
`skipped`. The executed IDs must exactly match nonempty `expected_test_ids`.
Missing reports, zero tests and skipped selection are not passing results.
`evidence.kind: "command"` needs no report and verifies only the process exit;
it cannot establish a test-selection claim. Reports must be newly produced.

## Plan the remaining feedback cost

Run the helper from the target repository. Set these shell variables from the
actual inspected files: `CI_FIX_SKILL`, `CI_FIX_INVENTORY`, `CI_FIX_SPEC`,
`CI_FIX_PROFILE`, and `CI_FIX_SCRATCH`. The scratch directory stays outside the
captured source. Set `CI_FIX_PYTHON` to the Python environment containing pexpect.

```sh
"$CI_FIX_PYTHON" "$CI_FIX_SKILL/scripts/windows_local.py" plan \
  --inventory "$CI_FIX_INVENTORY" --spec "$CI_FIX_SPEC" \
  --profile "$CI_FIX_PROFILE" --json > "$CI_FIX_SCRATCH/windows-plan.json"
```

Plan reads the workflow inventory before calling Fusion's `host_preflight.py`
and `vm_power.py status`. It starts nothing and reads no access file.
`not-applicable` means the inventory has no Windows job. Missing Fusion, a missing
guest, an ambiguous matrix cell or mismatched architecture names a preparation
gap; resolve it or retain CI as the execution route.

Optional `--costs` reads schema version 1 with the plan's `context` digest,
`source` describing the samples, `local`, `remote`, and `remote_available`.
Both phase objects use seconds, with `null` for unknown values:

| Route | Phases included in remaining cost |
| --- | --- |
| Local Windows | `snapshot_s`, `transfer_s`, `setup_s`, `checks_s`, `collect_s`; add `startup_s` when Windows is not running |
| Suitable additional CI diagnosis | `submit_s`, `queue_s`, `setup_s`, `checks_s`, `collect_s` |

Use comparable scope and environment samples. Separate required one-time setup
from later warm runs. Already-completed preparation is not charged twice.
Declare `remote_available: true` only for an actually suitable CI alternative.
Do not count the final required CI run as avoided, or use hosted step duration
as a measurement of local Windows cost. Preserve sample provenance and refresh
stale runtime/dependency identities. Failed runs measure time to failure and
cannot supply successful check duration.

The planner selects local execution when its complete estimate is lower, and
CI when CI costs no more. Unknown local cost returns `measure`; take one bounded
informative measurement, retain each phase, then update the estimate. An unknown
remote alternative cannot establish a claimed time saving.

Copy the plan's `execution_context` JSON object to the existing ledger context
file. Pass that file and `--local-env windows-vm --windows-plan` to
`ladder_plan.py`. The ladder retains scope rules, disables the hosted-step proxy
for local Windows, and honors a lower-cost suitable CI decision. A step's ledger
median alone never qualifies the complete-bundle shortcut.

## Capture, execute and collect once

Set `CI_FIX_ACCESS` to the provider's private access file and `CI_FIX_RECEIPT` to
a new invocation receipt path outside the source. After inspecting the command,
source exclusions and existing task authorization:

```sh
"$CI_FIX_PYTHON" "$CI_FIX_SKILL/scripts/windows_local.py" run \
  --inventory "$CI_FIX_INVENTORY" --spec "$CI_FIX_SPEC" \
  --profile "$CI_FIX_PROFILE" --access-file "$CI_FIX_ACCESS" \
  --receipt "$CI_FIX_RECEIPT" --yes --json
```

Include the reviewed `--costs` file when timing evidence exists. `--dry-run`
performs planning without capture, guest access or writes. Optional `--ledger`
records only verified, unchanged-source successful execution duration through
the existing `local_ledger.py`. Supply `workflow_name`, `job_name` and `step_name`
in the specification when display names differ from workflow keys or scope.

The snapshot contains current staged and unstaged worktree bytes, tracked
deletions, and non-ignored untracked files. Inspect relevant untracked content
and use explicit `snapshot_exclude` patterns for non-source files. Ignored
untracked files and `.git` are omitted. Required ignored inputs must be prepared
deliberately; absence is not permission to copy credentials. Unsupported links,
submodules, unmaterialized LFS data, conflicts and Windows path collisions are
explicit gaps. The default bounds are 25,000 files and 256 MiB.

Fusion's standard-account adapter verifies archive and file hashes, native
architecture and the exact account SID. Each invocation has a fresh directory
under `%LOCALAPPDATA%\FusionLocalJobs`. A guest lease prevents concurrent local
jobs; active GitHub runner processes prevent admission. Retain the usual trusted
source policy and do not register a GitHub runner concurrently.

The command timeout is 1–900 seconds. The adapter attempts to terminate its own
process tree on timeout and reports uncertainty if termination cannot be proved.
A lost SSH response does not prove that Windows stopped. Reconcile the original
invocation; never create another invocation as an automatic retry:

```sh
"$CI_FIX_PYTHON" "$CI_FIX_SKILL/scripts/windows_local.py" collect \
  --receipt "$CI_FIX_RECEIPT" --access-file "$CI_FIX_ACCESS" --json
```

Collection retrieves that invocation's durable result, stdout, stderr and test
report. It never starts a command. Logs are bounded to 16 MiB each and reports
to 8 MiB; oversized guest files remain available for explicit inspection.
Evidence is bound to the snapshot, command, account and architecture. If Mac
source changed meanwhile, `source-changed` retains the snapshot's result but
does not verify newer edits. Run a new reviewed snapshot for those changes.

Exit 0 can mean a completed plan, an inapplicable route, or a verified pass;
inspect `state`/`status`. Exit 1 reports a verified failure or runtime error,
2 invalid input/consent, 5 an unmet precondition or timeout, and 130 interruption.
JSON errors use stderr; evidence uses stdout and the private receipt. `-o json`
and `--json` are aliases. One non-credential JSON input can use `-` for stdin;
access, receipt and ledger paths must name actual local files.

Preserve failed results and resume uncertain invocations before cleanup. After
all owned commands are terminal and no runner can receive work, follow Fusion's
graceful shutdown procedure. This helper never shuts Windows down or removes
working directories. Reset and deletion remain separate authorized operations.
