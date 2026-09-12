# Provision and verify the Windows runner

Use this reference after Windows boots. The validated diagnostic path uses a
fresh one-job registration. It retains the VM's working files. The older
interactive persistent recipe remains available for separately chosen setups;
persistent registration across reboot is outside this delivery's acceptance. This is a locally prepared Windows environment,
not GitHub's hosted Windows image.

## 1. Establish which jobs may run

Use the requested repository or organization and inspect its workflows before registration. Record the workflow files, shells, required tool versions, action versions, artifact targets, and relevant permissions. Identify who can cause those workflows to run. GitHub [recommends private repositories for self-hosted runners](https://docs.github.com/en/actions/how-tos/manage-runners/self-hosted-runners/add-runners) because a public pull request can introduce code that runs on the machine.

Publishing this skill does not authorize a runner to accept public fork jobs. Default to the user's trusted repository scope. For an organization, use its established runner group and repository restrictions. If the request needs broader or public access, prepare the configuration and resolve that trust decision before registration. A custom `fusion-ci` label selects a runner; it is not an access-control mechanism.

Check existing workflows and queued jobs that could match the planned runner. The service may accept work as soon as configuration starts it. Do not register into a scope whose job admission has not been established.

## 2. Identify the guest and install its tools

Before guest authentication, obtain the actual Windows account name using
[`whoami`](https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/whoami)
inside Windows. If the agent cannot run it, ask the user for the account name
printed by that command. Do not guess from a display name, email, Mac login, or
profile folder. Record its maintenance or CI role locally. Obtain a password
through a protected prompt or the user's established private credential method;
never copy its value into the public skill.

VMware Tools can provide bootstrap and recovery commands. Native SSH can provide
routine commands and SFTP transfers when that access is configured. Use the
user's chosen password or client-key authentication; client keys are not required
by this skill. Microsoft documents [Windows OpenSSH](https://learn.microsoft.com/en-us/windows-server/administration/openssh/openssh_install_firstuse).
Keep deployment-specific access automation and credential records private.

A VMware Tools command can run with a filtered, non-administrator token even
when the account belongs to Administrators. Verify elevation before installing
privileged prerequisites; use an elevated Windows console when needed. An SSH
service reported as running is not an access test: verify the intended account,
command output and exit status, file-transfer hashes, and access after reboot.
Use the native SSH terminal's hidden password prompt or an established private
helper that checks terminal echo before supplying a saved password. If the
available tool cannot do that, leave password entry to the user's terminal or
Windows console; never substitute a password-bearing command argument.

Run the following in **PowerShell inside Windows**, not in the macOS terminal:

```powershell
[System.Runtime.InteropServices.RuntimeInformation]::OSArchitecture.ToString()
[System.Runtime.InteropServices.RuntimeInformation]::ProcessArchitecture.ToString()
Get-CimInstance Win32_Processor | Select-Object Architecture, AddressWidth
Get-CimInstance Win32_OperatingSystem | Select-Object Caption, Version, BuildNumber
```

Use the verified guest platform for the runner download. Microsoft's [processor schema](https://learn.microsoft.com/en-us/windows/win32/cimwin32prov/win32-processor) defines `Architecture` value `12` as ARM64 and `9` as x64; `AddressWidth` should be `64` for this Windows guest. Compare these with the operating-system and process observations. If they disagree, check **Windows Settings ▸ System ▸ About ▸ System type** before selecting an asset. Emulated processes can report emulated CPU details. GitHub's [supported runner architectures](https://docs.github.com/en/actions/reference/runners/self-hosted-runners) currently list Windows ARM64 as public preview; refresh that status during setup.

Install tools from their official distribution channels according to the target workflow. Typical requirements include Git, PowerShell 7 when the workflow uses `pwsh`, language runtimes, compilers, and SDKs. Inspect the workflow's setup actions before deciding what must already be installed. Do not bulk-install a hosted image's entire tool inventory or change pinned versions merely to fit this VM.

Install tools for the service account or system-wide as appropriate. A tool found in an administrator's interactive `PATH` may be absent from the service's environment. Restart the service after approved environment changes when it is idle, then verify from an actual job. A successful interactive command is weaker evidence.

Keep the runner directory and checkouts on the Windows filesystem, normally under `C:\actions-runner`. On an Arm64 guest, distinguish native Arm64 tools from emulated x64 applications and record the artifact target separately. Microsoft's [emulation documentation](https://learn.microsoft.com/en-us/windows/arm/apps-on-arm-x86-emulation) limits emulation to user-mode applications; kernel components require Arm64 builds. Preserve the original hosted CI check when its different architecture or Windows edition matters.

## 3. Download the runner and prepare a baseline

Open the target repository or organization's GitHub runner registration page. Derive the URL from the actual scope, then use **Settings ▸ Actions ▸ Runners** to add a self-hosted runner. Select **Windows** and the architecture observed in the guest. Use the current download instructions and checksum for that exact asset. The [official runner releases](https://github.com/actions/runner/releases) are a secondary source; do not embed a stale release URL or substitute a different server's required runner version.

Download the archive inside Windows, or transfer an officially downloaded,
verified copy from the Mac. A data ISO can carry the chosen vendor installers
and their checksum manifest without sharing host home folders. Attach that ISO
through **Fusion ▸ Virtual Machine ▸ CD/DVD (SATA) ▸ Choose Disc or Disc Image…**,
then verify its actual drive letter and contents inside Windows. In the
validation run, `D:` exposed the prepared PowerShell, Git, and runner files;
directory visibility alone did not verify their guest-side hashes or install
them. Retain the source URLs and expected digests from the official downloads.

Set `$RunnerZip` to the archive's absolute guest path, including its actual disc
drive if using transfer media, and `$ExpectedSha256` to the SHA-256 digest shown
for that asset in GitHub's instructions or release. This PowerShell check must
succeed before extraction:

```powershell
if ($ExpectedSha256 -notmatch '^[0-9a-fA-F]{64}$') {
    throw 'Expected SHA-256 digest is missing or malformed.'
}
if ((Get-FileHash -LiteralPath $RunnerZip -Algorithm SHA256).Hash -ine $ExpectedSha256) {
    throw 'Runner archive checksum mismatch.'
}
```

Use a new, empty installation directory. Set `$RunnerDir` to its actual path; `C:\actions-runner` is GitHub's documented Windows recommendation. If it contains an existing runner, inspect that identity and resume it or plan an explicit replacement. Do not extract over it blindly. Extract with `Expand-Archive -LiteralPath $RunnerZip -DestinationPath $RunnerDir`, then retain the asset name, version, and verified digest for the handoff.

If a reusable baseline is wanted, take it after Windows and tools are ready and **before GitHub registration**. This baseline can contain Windows account and license state and must remain local. Never publish the installed Windows image as part of this skill. Never clone a VM containing an active runner registration: each independent VM needs a unique runner identity and a fresh registration.

Normal startup reuses the existing VM; a persistent service reuses its
registration, while a completed one-job runner needs fresh registration.
Independent clones also
need Windows image preparation with Sysprep; a snapshot alone does not supply
new Windows identities. Follow [reuse and compatibility](reuse-and-compatibility.md)
for the two procedures and a workflow comparing identical tests on hosted
Windows and Fusion.

## 4. Configure a dedicated Windows service account

Use a non-administrator account dedicated to this runner unless a demonstrated workflow requirement needs additional permissions. Do not casually select `LocalSystem` or add the runner account to Administrators to fix missing tools. Install privileged prerequisites with the setup administrator instead.

When a new local account is needed, set `$RunnerAccount` to the chosen unused account name. Run this in an elevated, native 64-bit PowerShell session inside Windows. Have the user enter the password directly at the secure prompt and retain it in their credential store:

```powershell
$RunnerPassword = Read-Host 'Password for the dedicated runner account' -AsSecureString
$RunnerUser = New-LocalUser -Name $RunnerAccount -Password $RunnerPassword -Description 'GitHub Actions runner service'
Add-LocalGroupMember -SID 'S-1-5-32-545' -Member $RunnerUser
Remove-Variable RunnerPassword
$ServiceAccount = "$env:COMPUTERNAME\$RunnerAccount"
```

The group SID `S-1-5-32-545` identifies the standard Windows Users group across display languages. These commands use Microsoft's [local-user](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.localaccounts/new-localuser?view=powershell-5.1) and [group-membership](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.localaccounts/add-localgroupmember?view=powershell-5.1) interfaces. Do not reset an existing account's password or disable password-expiry policy without a reason established by the task.

## 5. Register and install the service

### Existing interactive persistent option

This separate option is not covered by the one-job diagnostic acceptance.
Never reconfigure a job-writable program directory as administrator: prepare a
new verified distribution first.

Set `$ScopeUrl` to the established GitHub repository or organization URL, `$RunnerName` to the chosen unique name, and `$ServiceAccount` to the dedicated account. In elevated **Windows PowerShell**, change to the actual runner directory and invoke:

```powershell
Set-Location -LiteralPath $RunnerDir
.\config.cmd --url $ScopeUrl --name $RunnerName --labels 'fusion-ci' --work '_work' --runasservice --windowslogonaccount $ServiceAccount
```

Obtain the short-lived registration token from the exact target's registration page and enter it at the runner's prompt. Enter the service password at its prompt. Do not place either value in command arguments, chat, shell history, the handoff, or a shared script. If the environment cannot supply protected interactive input, hand that prompt to the user in the Windows console. Resume after it completes. Keep organization runner-group selection within the established access scope, and do not replace a colliding runner name automatically.

The Windows runner installs its service during configuration. The [runner's service implementation](https://github.com/actions/runner/blob/main/src/Runner.Listener/Configuration/WindowsServiceControlManager.cs) grants the selected account service-logon and runner-directory permissions, writes the exact service name to `.service`, and starts the service. Do not run `run.cmd` alongside it. If an existing runner was configured without a service, follow GitHub's [reconfiguration procedure](https://docs.github.com/en/actions/how-tos/manage-runners/self-hosted-runners/configure-the-application); do not invent a Linux-style `svc.sh` procedure for Windows.

### One-job diagnostic registration

Use `scripts/register_service.ps1` for a prepared guest serving an authorized
`ci-fix` diagnostic. This helper supports an exact repository on `github.com`.
Run it in native PowerShell 7.4 or later, in an elevated maintenance session
using the user's established protected guest connection. Built-in Windows
PowerShell 5.1 is rejected before mutation by the script's runtime requirement. It does not download Windows, install SSH, create a service
account, or fetch a registration token. Verify those prerequisites first.

1. Generate a fresh 32-character lowercase hexadecimal registration invocation.
   Set the runner name to `fusion-ci-` followed by that identifier. Establish
   admission for the trusted repository before the service can start; inspect
   existing workflows, queued jobs and runner labels.
2. Verify the dedicated local service account and its Windows security
   identifier (SID). Select the official stable runner release matching the
   observed native Windows architecture. Record its exact release asset URL
   and published SHA-256; never derive trust from files left by an earlier job. Preserve a host intent as described in
   [the handoff reference](handoff.md#preserve-registration-identity-before-transport-can-fail).
   Choose an administrator-controlled guest receipt directory outside the
   runner's job checkout and a new receipt filename. The helper refuses a
   directory writable by the CI account or other untrusted users. Existing runner processes or services require reconciliation and deliberate
   retirement first. The requested installation directory must not exist.
3. Transfer the public script through the established connection into a verified
   administrator-controlled staging directory and verify its hash in Windows.
   The CI account must not be able to replace those bytes between verification
   and execution. Obtain a short-lived registration token for the exact
   repository through authenticated GitHub tooling. Supply the following JSON
   object to the script on protected standard input. Never place the object
   or its credential values in arguments, chat, shell history, a public file,
   a transcript, or the secret-free handoff.

   | Input key | Value |
   | --- | --- |
   | `repository` | Exact `owner/repository` |
   | `invocation` | Fresh registration identifier from step 1 |
   | `name` | Exact `fusion-ci-<registration-id>` runner name |
   | `mode` | `ephemeral` for one diagnostic job |
   | `runner_directory` | `C:\ProgramData\FusionRunnerPrograms\` followed by the invocation; the directory must not exist |
   | `runner_version` | Official stable release version, such as `2.332.0`; observe the current version rather than copying this example |
   | `runner_archive_url` | Exact `https://github.com/actions/runner/releases/download/vVERSION/actions-runner-win-ARCH-VERSION.zip`, with observed version and `arm64` or `x64` |
   | `runner_archive_sha256` | The selected official asset's published 64-character SHA-256 |
   | `receipt_path` | New absolute local Windows path for the secret-free guest receipt |
   | `service_account`, `service_account_sid` | Exact machine-qualified account name and matching local SID |
   | `token`, `password` | Short-lived registration token and dedicated account password, obtained through protected input |

   The helper creates an administrator-owned `FusionRunnerPrograms` parent
   with no untrusted writers. It refuses reparse paths, an existing invocation
   directory, an unexpected release URL, or a digest mismatch. It downloads
   with a 120-second / 256 MiB bound and extracts only the verified archive.
   Failed preparation remains recorded and never executes `config.cmd`.
   Each registration gets fresh programs; earlier directories are retained as
   data and are never reused for elevated configuration.

   The helper passes credentials to `config.cmd` through its process-scoped
   `ACTIONS_RUNNER_INPUT_*` variables and clears those variables afterward.
   This avoids password-bearing command arguments; it does not make an
   untrusted guest transport or captured stdin safe. Use a protected console
   workflow when the available transport cannot keep those values out of logs.
4. Retrieve the guest receipt even when the command failed. Match its
   invocation, repository, name, numeric runner ID, service name, account/SID
   and installation directory to the host intent and observed guest state.
   Inspect the actual service executable and GitHub runner entry. Update the
   local handoff only from those observations.

The helper configures `--ephemeral --runasservice --no-default-labels`. Its
exclusive custom label equals the runner name. It does not include the
`self-hosted`, `Windows`, `ARM64` or `X64` default labels, so use the exact label
list returned by GitHub for workflow routing. No other runner should share the
registration's label. This prevents ordinary default-label jobs from selecting
the one-job runner; it does not authorize untrusted code or replace repository
access controls.

Fresh programs prevent reuse of persisted job-modified executables. This is
not containment for a compromised guest or surviving hostile background
processes. If prior work is untrusted or guest integrity is uncertain, restore
the verified baseline before administrator maintenance. The supported job
policy remains trusted code.

The helper accepts only `mode: ephemeral`. Ordinary Windows reboot/access
verification is separate from keeping a GitHub registration across reboot.

After one job, GitHub retires an ephemeral registration. Inspect the actual
job and current registration state, then follow
[one-job completion and failure recovery](../../fusion-runner-run/references/operations.md#one-job-completion-and-failure-recovery).
Preserve the receipt on a lost response or partial configuration. Never run
configuration again merely because the transport failed to return success.
The next diagnostic gets a fresh invocation, name, label and registration;
the Windows VM and earlier working files remain in place. The next registration
gets a new verified program directory, not a new Windows installation.

## 6. Verify identity and a real job

Read only the service-name file, then inspect that exact service in **Windows PowerShell**:

```powershell
$ServiceName = (Get-Content -LiteralPath (Join-Path $RunnerDir '.service') -Raw).Trim()
Get-Service | Where-Object Name -eq $ServiceName
Get-CimInstance Win32_Service | Where-Object Name -eq $ServiceName |
    Select-Object Name, State, StartMode, StartName, PathName
```

Verify its executable belongs to this runner directory, its account matches the chosen account, and automatic startup is configured. Verify GitHub's runner entry by name, architecture, labels, and numeric ID. Capture the ID from the target's runner list through the authenticated API or UI. API results may require pagination. Never copy `.credentials` or other runner credential files into the handoff.

GitHub must report this runner **Idle**, or API `status` equal to `online` with
`busy` equal to `false`, before calling it ready for a job. See
[GitHub monitoring guidance](https://docs.github.com/en/actions/how-tos/manage-runners/self-hosted-runners/monitor-and-troubleshoot).
For a persistent registration, reboot the guest and verify that the same service
and runner recover without an interactive Windows login. Record this separately
from a pre-registration reboot or a one-job execution.

Use `templates/fusion-smoke.yml` for an authorized CI smoke test. Its explicit
`pwsh` shell requires PowerShell 7 in the service account's environment. Render
its target labels from the recorded runner. For an Arm64 persistent runner
registered with the interactive recipe and default labels, the selector is:

```yaml
runs-on: [self-hosted, Windows, ARM64, fusion-ci]
```

For an x64 guest, replace `ARM64` with `X64`. Keep the selector specific and verify the job's actual runner ID/name after execution. A shared custom label can select more than one VM. GitHub documents [self-hosted label routing](https://docs.github.com/en/actions/how-tos/manage-runners/self-hosted-runners/use-in-a-workflow).

For the protected helper's exclusive registration, use only its actual custom
label list. A `ci-fix` workflow takes that JSON label list and the selected tests
through the
[Windows diagnostic contract](https://github.com/smorinlabs/smorinlabs-harness/blob/main/plugins/repo-hygiene/skills/ci-fix/references/windows-runners.md).
Verify the job's actual OS/process architecture and non-administrator token;
the label name alone supplies none of those observations.

Prepare the exact workflow change before requesting any missing authorization to publish or dispatch it. GitHub requires a manual `workflow_dispatch` workflow to [exist on the default branch](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/manually-run-a-workflow). Do not merge or modify that branch just to make the smoke test run. Use an existing authorized diagnostic workflow if suitable. Do not retarget production `windows-latest` jobs silently.

The template tests runner identity and basic command execution. Add the target workflow's actual tool/version checks when that testing is authorized. Record run URL, commit, job conclusion, observed architecture, and remaining differences. If no job ran, report **runner online; CI smoke test unverified**. Finish the [handoff](handoff.md), then use the [operations reference](../../fusion-runner-run/references/operations.md) to leave the VM off unless it should stay online.
