# Operate the configured VM

Use this reference for one existing VM and its registered Windows service. Refresh the local handoff's identities against live state before mutations. Never assume that a previous status observation still holds.

## 1. Bind the command to the correct VM

Read `vm.vmx_path` from the [handoff](../../fusion-runner-setup/references/handoff.md) and verify the file exists. Resolve Python 3 and this operating skill's directory. In the **macOS terminal**, set:

- `FUSION_RUNNER_PYTHON` to the executable found with `command -v python3`, or an existing Python environment's executable.
- `FUSION_RUNNER_RUN_SKILL` to this installed skill's absolute directory.
- `FUSION_RUNNER_VMX` to the handoff's verified absolute `.vmx` path.

Inspect power state with the bundled helper:

```sh
"$FUSION_RUNNER_PYTHON" "$FUSION_RUNNER_RUN_SKILL/scripts/vm_power.py" status --vmx "$FUSION_RUNNER_VMX" --json
```

The helper accepts `--vmrun PATH` for a verified Fusion `vmrun` executable outside its usual location and `--timeout SECONDS` for the command timeout. It reports `running` or `not_running` from Fusion's running list. `not_running` includes both powered-off and suspended VMs; use Fusion or Windows evidence to distinguish them. The helper neither authenticates to Windows nor queries GitHub. Do not pass it the `.vmwarevm` bundle path or infer a VM by taking the first list item.

## 2. Check GitHub's view of this runner

Use an authenticated GitHub tool on the Mac or the target's runner page. If using GitHub CLI, verify it resolves with `command -v gh` and check `gh auth status`; do not print its token. Derive the API endpoint from `runner.scope_type`, `runner.scope_url`, and `runner.id`:

| Scope | API endpoint pattern |
| --- | --- |
| Repository | `repos/OWNER/REPOSITORY/actions/runners/RUNNER_ID` |
| Organization | `orgs/ORGANIZATION/actions/runners/RUNNER_ID` |

Replace the uppercase segments from the handoff's actual scope URL and numeric ID. Store the completed endpoint in `FUSION_RUNNER_ENDPOINT`, then query:

```sh
gh api "$FUSION_RUNNER_ENDPOINT" --jq '{id, name, status, busy, labels: [.labels[].name]}'
```

For a GitHub host other than `github.com`, use the authenticated tool's matching host configuration and that host's documented API. A permissions error or missing runner is unresolved identity/connectivity, not proof of `offline`. The [runner API](https://docs.github.com/en/rest/actions/self-hosted-runners) supplies connectivity and busy state. The [runner page](https://docs.github.com/en/actions/how-tos/manage-runners/self-hosted-runners/monitor-and-troubleshoot) calls an available runner **Idle**, a working runner **Active**, and a disconnected runner **Offline**.

## 3. Start and wait for readiness

When start is requested, run in the **macOS terminal**:

```sh
"$FUSION_RUNNER_PYTHON" "$FUSION_RUNNER_RUN_SKILL/scripts/vm_power.py" start --vmx "$FUSION_RUNNER_VMX" --json
```

An already running VM can be inspected without creating a second one. Starting a suspended VM may resume its previous guest state; this is not a clean boot or reset. If Fusion requires an encrypted-VM unlock, open this exact VM in Fusion and use the user's interactive authentication or existing Keychain access. Do not put the encryption password in a command argument or change encryption to make the command succeed.

Wait with a bounded deadline while checking actual boot progress. The configured service should start with Windows. A GUI sign-in should not be required. If it does not connect, inspect the exact recorded service through an available guest connection or the Fusion console. In **Windows PowerShell**, set `$ServiceName` to `runner.service_name` from the handoff, then run:

```powershell
$RunnerService = Get-Service | Where-Object Name -eq $ServiceName
if ($null -eq $RunnerService) { throw 'The recorded runner service was not found.' }
$RunnerService
```

If it is stopped, the established start request authorizes `Start-Service -InputObject $RunnerService` once the installation identity is verified. Passing the exactly matched service object avoids wildcard interpretation of the name. Use an elevated guest session when required. Do not launch `run.cmd` alongside the service or reinstall the runner to fix an ordinary boot failure.

Report **ready** only after GitHub identifies this runner as `online` and `busy: false`. If it is already busy, report the active state. Do not claim a workflow passed because the VM started. Record an actual authorized run's URL, commit, target runner, and conclusion separately.

Mac sleep, guest sleep, loss of networking, Windows updates, and runner updates can interrupt availability. Inspect those causes when readiness fails. For a requested CI session, use an existing or authorized temporary sleep-prevention mechanism and release it when done. Do not persistently change the Mac's power settings merely to start the VM.

## 4. Stop admission, then shut down

1. Check the exact runner's busy state and its active workflow job. If a job is running, wait for it to finish unless interrupting that job is explicitly authorized. If it does not finish within the chosen wait budget, report the active run and leave the machine running; a timeout does not authorize interruption.
2. Establish a window in which this runner cannot receive new jobs before a noninterrupting shutdown. GitHub's `busy: false` is a snapshot, not an atomic drain operation. Use the scope's established admission controls or an authorized pause; an empty queue alone does not establish this window. Do not silently disable workflows, remove labels, or broaden permissions. If admission cannot be paused, leave the service and VM running unless the user explicitly authorizes interruption of a job that races with shutdown. Explaining the race is not permission to interrupt it. Report what prevents the requested stop and obtain only the missing authorization.
3. With the admission window established and no jobs active, or with interruption explicitly authorized, stop the exact recorded service from elevated **Windows PowerShell**. In this guest session, set `$ServiceName` to the exact `runner.service_name` in the verified local handoff; do not depend on a variable from a previous start session:

   ```powershell
   $RunnerService = Get-Service | Where-Object Name -eq $ServiceName
   if ($null -eq $RunnerService) { throw 'The recorded runner service was not found.' }
   Stop-Service -InputObject $RunnerService
   Get-Service | Where-Object Name -eq $ServiceName
   ```

   Recheck any job that might have arrived during the transition. Confirm the service is `Stopped` and GitHub reports this runner `offline`. If work raced with stopping, inspect its outcome and report it; do not label the shutdown disruption-free.
4. Only after those observations, request graceful VM shutdown in the **macOS terminal**:

   ```sh
   "$FUSION_RUNNER_PYTHON" "$FUSION_RUNNER_RUN_SKILL/scripts/vm_power.py" stop --vmx "$FUSION_RUNNER_VMX" --runner-offline --yes --json
   ```

   `--runner-offline` and `--yes` are operator attestations that the required checks were performed. They do not perform those checks. Never supply them solely because an API request failed or the Mac lost network access.
5. Re-run the helper's `status` action and verify GitHub remains offline. Confirm completed Windows shutdown or Fusion's powered-off state; `not_running` alone could mean suspended. The helper uses graceful shutdown only. A command timeout or error leaves actual VM state uncertain until inspected. Use the Windows shutdown UI if the tool cannot shut down gracefully; do not switch to a hard power-off or suspend an active job.

For a VM confirmed powered off in Fusion and a runner verified offline, no service stop is necessary. Report that state without booting Windows just to shut it down again. If the VM is off but GitHub says its runner is online, resolve a possible duplicate identity before taking further action.

## 5. Recover without replacing identity

| Observation | Next check |
| --- | --- |
| Fusion rejects the guest architecture | Verify physical Mac processor and the guest OS; use the setup skill for a deliberate replacement |
| CLI reports an encryption or authorization problem | Open the identified VM in Fusion; retain encryption and use protected authentication |
| VM runs but GitHub stays offline | Inspect Windows boot, exact service, outbound connectivity, guest time, and runner diagnostics |
| Interactive tools work but CI cannot find them | Inspect the service account's environment and installation scope; verify the repair in a job |
| Runner is online but the job stays queued | Compare every `runs-on` label, runner-group access, and runner busy state |
| Windows says the service account cannot log on | Inspect account/password-expiry policy and service credentials; do not promote the account to administrator |
| Runner ID no longer exists | Verify scope and permissions, then plan explicit re-registration through setup |

The runner's `_diag` directory contains diagnostic logs. Read only what is needed and redact credentials and private job data before sharing excerpts. Consult [GitHub troubleshooting](https://docs.github.com/en/actions/how-tos/manage-runners/self-hosted-runners/monitor-and-troubleshoot) and the [current Fusion feature matrix](https://knowledge.broadcom.com/external/article/315609) when behavior differs from the installed version.

Do not revert snapshots or clone a registered VM during routine operation. A persistent runner keeps its registration, repository files, caches, and modifications after shutdown. Rebuilding from a baseline requires removing or replacing the old registration deliberately and creating a unique new runner identity.
