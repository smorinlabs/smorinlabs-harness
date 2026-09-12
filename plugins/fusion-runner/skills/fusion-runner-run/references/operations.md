# Operate the configured VM

Use this reference for one existing VM and its prepared or registered Windows
runner. Refresh the local handoff's identities against live state before
mutations. A completed one-job registration may already be retired; a persistent
registration normally survives shutdown. Never assume that a previous status
observation still holds.

## 1. Bind the command to the correct VM

Read `vm.vmx_path` from the [handoff](../../fusion-runner-setup/references/handoff.md) and verify the file exists. Resolve Python 3 and this operating skill's directory. In the **macOS terminal**, set:

- `FUSION_RUNNER_PYTHON` to the executable found with `command -v python3`, or an existing Python environment's executable.
- `FUSION_RUNNER_RUN_SKILL` to this installed skill's absolute directory.
- `FUSION_RUNNER_VMX` to the handoff's verified absolute `.vmx` path.

Inspect power state with the bundled helper:

```sh
"$FUSION_RUNNER_PYTHON" "$FUSION_RUNNER_RUN_SKILL/scripts/vm_power.py" status --vmx "$FUSION_RUNNER_VMX" --json
```

The helper accepts `--vmrun PATH` for a verified Fusion `vmrun` executable
outside its usual location. `--timeout SECONDS` bounds each vendor call from
`1` to `300` seconds, default `30`. Optional `--wait-seconds SECONDS` supplies
one total deadline, also from `1` to `300` seconds, for a start or stop operation.
It covers initial inventory, the single power request, and subsequent inventory
polls; each vendor call is capped by the remaining deadline. Without it, the
helper makes one post-request observation and does not poll. Status accepts no
power-wait deadline.

The helper reports `running` or `not_running` from Fusion's running list.
`not_running` includes both powered-off and suspended VMs; use Fusion or Windows
evidence to distinguish them. It neither authenticates to Windows nor queries
GitHub. Do not pass it the `.vmwarevm` bundle path or infer a VM by taking the
first list item. A zero vendor exit status does not prove that the requested
power state occurred; a completed inventory observation is required.

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

When `runner.id` is `null`, report a prepared, unregistered profile instead of
constructing a runner endpoint. New registration belongs to
[setup](../../fusion-runner-setup/references/runner-provisioning.md#one-job-diagnostic-registration).
For a completed or partly configured one-job registration, preserve its host
intent and guest receipt and use the retirement procedure below to establish
absence. A `404` response alone does not establish retirement.

## 3. Start and wait for readiness

When start is requested, run in the **macOS terminal**:

```sh
"$FUSION_RUNNER_PYTHON" "$FUSION_RUNNER_RUN_SKILL/scripts/vm_power.py" start --vmx "$FUSION_RUNNER_VMX" --wait-seconds 120 --json
```

The example bounds the power operation at `120` seconds; choose a different
bound when prior observations justify it. `power_not_confirmed` means the
requested state was not observed within that operation. Inspect Fusion and the
current inventory before retrying; polling does not repeat the power request
or authorize a forced action.

An already running VM can be inspected without creating a second one. Starting a suspended VM may resume its previous guest state; this is not a clean boot or reset. If Fusion requires an encrypted-VM unlock, open this exact VM in Fusion and use the user's interactive authentication or existing Keychain access. Do not put the encryption password in a command argument or change encryption to make the command succeed.

Wait with a separate bounded deadline while checking actual boot progress and
runner readiness. A registered persistent service should start with Windows
without a GUI sign-in. A prepared guest whose prior one-job registration was
retired needs fresh setup registration before it can accept work. Do not label
that expected state a boot failure or silently re-register during a status
request. If an existing registered service does not connect, inspect it through
an existing verified guest connection or the Fusion console. Obtain the actual
Windows login from `whoami` if the identity is missing; do not guess it or
silently install another access method. In **Windows PowerShell**, set
`$ServiceName` to `runner.service_name` from the handoff, then run:

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
   "$FUSION_RUNNER_PYTHON" "$FUSION_RUNNER_RUN_SKILL/scripts/vm_power.py" stop --vmx "$FUSION_RUNNER_VMX" --runner-offline --yes --wait-seconds 120 --json
   ```

   `--runner-offline` and `--yes` are operator attestations that the required checks were performed. They do not perform those checks. Never supply them solely because an API request failed or the Mac lost network access.
5. Re-run the helper's `status` action and verify GitHub remains offline. Confirm completed Windows shutdown or Fusion's powered-off state; `not_running` alone could mean suspended. The helper uses graceful shutdown only. A command timeout or error leaves actual VM state uncertain until inspected. Use the Windows shutdown UI if the tool cannot shut down gracefully; do not switch to a hard power-off or suspend an active job.

For a VM confirmed powered off in Fusion and a runner verified offline, no service stop is necessary. Report that state without booting Windows just to shut it down again. If the VM is off but GitHub says its runner is online, resolve a possible duplicate identity before taking further action.

### One-job completion and failure recovery

A failed test does not prevent cleanup. A passing report does not establish
safe shutdown. Preserve the diagnostic receipt, available job logs, guest
receipt and registration intent before retiring the registration. The
`ci-fix` collector saves the correct job's log before it requires a valid report;
if collection itself failed, retrieve the exact run/job logs through the
authenticated API and record why report verification is incomplete.

1. **Reconcile the registration.** Match the host intent, guest receipt,
   `.runner` identity and exact `.service` name with GitHub. Verify the service
   executable belongs to the intended runner directory and its account matches
   the recorded dedicated account. Retrieve the guest receipt after a lost
   transport response; a missing host response does not prove registration
   failed. The guest's `configuration_finished` records the end of the attempt,
   not successful setup. Do not retire while configuration is still running
   or while its completion is unknown.
2. **Prove the job ended and prevent further admission.** Bind any dispatched
   job to the receipt's repository, run/attempt, commit and actual runner ID.
   Wait for its terminal status. After a one-job execution, verify the
   registration is absent through a current authorized, fully paginated runner
   list. This retired identity cannot receive another job. If registration
   remains, or configuration was partial and no job ran, inspect the intended
   scope and work assigned to that exact runner before deliberate retirement.
   Use an already authorized admission pause or remove that exact registration
   within the requested cleanup scope. Do not disable unrelated workflows or
   delete another runner. Recheck for work that raced with retirement before
   stopping the service. `busy: false`, an empty queue, an offline snapshot,
   or a request timeout cannot establish this barrier by themselves.
3. **Stop only the owned service.** Once no job is active and the admission
   barrier is established, use the exact service-object check from section 4.
   Verify its state is `Stopped` and inspect `Runner.Listener` and
   `Runner.Worker` processes. If either is still present, establish why and
   wait within the bound. Do not kill a process or stop another installation
   to make cleanup pass. Requery authorized GitHub inventory to prove the
   registration remains absent. Preserve the VM on uncertainty.
4. **Remove the retired service registration.** Transfer
   `scripts/retire_service.ps1` from this skill and verify its guest-side hash.
   Invoke it in an elevated maintenance session with a secret-free JSON object
   on stdin. Supply `runner_directory`, `service_name`, `runner_id`, and
   `runner_name` from the reconciled receipt, plus
   `github_registration_absent: true` only after the current host-side checks
   above. This boolean is an operator attestation; the script does not query
   GitHub or create an admission barrier.

   The helper independently refuses running listeners/workers, an active
   service, a service executable outside the intended directory, mismatched
   `.service` contents, or a different `.runner` ID/name. Only then does it
   delete the exact stopped service and that registration's `.runner`,
   `.credentials`, `.credentials_rsaparams`, and `.service` files. It preserves
   the runner distribution, checkouts, caches, markers and other working files.
   Preserve the resulting receipt. Do not substitute recursive directory
   deletion or `config.cmd --replace` if it refuses.
5. **Shut down gracefully and record retirement.** With service/process
   absence and current GitHub retirement established, use the power helper's
   `stop --runner-offline --yes` action with the chosen total wait deadline.
   Here the attestation means the owned service is stopped or removed and its
   registration is verified retired. Confirm actual completed Windows shutdown
   and the final Fusion inventory; update the profile's registration phase.
   Preserve the original ID in historical receipts. The next diagnostic uses
   a fresh registration.

For an authorized manual retirement, derive the exact API endpoint from the
verified repository and numeric runner ID as in section 2, then use the
authenticated GitHub tool's runner-deletion operation. Verify absence afterward
with successful access to the scope and a complete runner list. An uncertain
deletion response is a reason to reconcile that ID, not delete a different one.
See the [runner REST API](https://docs.github.com/en/rest/actions/self-hosted-runners).

If partial registration never created a service, pass `service_name: null` and
the observed `configuration_finished: true` receipt to `retire_service.ps1`.
Reconcile the exact runner ID/name and installation directory, prove runner
processes ended, establish the admission barrier, and retire that GitHub
registration first. The helper refuses if a `.service` file or service executable
under that directory has appeared since the partial receipt. It never invents
a service name. Missing runner identity or unfinished configuration still requires
manual reconciliation and preservation of the VM.

## 5. Recover without replacing identity

| Observation | Next check |
| --- | --- |
| Fusion rejects the guest architecture | Verify physical Mac processor and the guest OS; use the setup skill for a deliberate replacement |
| CLI reports an encryption or authorization problem | Open the identified VM in Fusion; retain encryption and use protected authentication |
| VM runs but GitHub stays offline | Inspect Windows boot, exact service, outbound connectivity, guest time, and runner diagnostics |
| Interactive tools work but CI cannot find them | Inspect the service account's environment and installation scope; verify the repair in a job |
| Runner is online but the job stays queued | Compare every `runs-on` label, runner-group access, and runner busy state |
| Windows says the service account cannot log on | Inspect account/password-expiry policy and service credentials; do not promote the account to administrator |
| Runner ID no longer exists | Verify scope and permissions; for a known one-job registration, prove retirement and preserve its receipt before fresh setup |

The runner's `_diag` directory contains diagnostic logs. Read only what is needed and redact credentials and private job data before sharing excerpts. Consult [GitHub troubleshooting](https://docs.github.com/en/actions/how-tos/manage-runners/self-hosted-runners/monitor-and-troubleshoot) and the [current Fusion feature matrix](https://knowledge.broadcom.com/external/article/315609) when behavior differs from the installed version.

Do not revert snapshots or clone a registered VM during routine operation. A persistent runner keeps its registration, repository files, caches, and modifications after shutdown. Rebuilding from a baseline requires removing or replacing the old registration deliberately and creating a unique new runner identity.

Retirement refuses reparse points in the installation, its ancestors, and
registration files. These live checks assume the trusted-job policy and no
hostile background process changing paths during maintenance. If guest
integrity is uncertain, preserve required evidence and restore the verified
baseline before administrator maintenance.
