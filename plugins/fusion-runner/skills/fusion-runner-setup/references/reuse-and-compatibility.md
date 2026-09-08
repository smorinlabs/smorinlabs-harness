# Reuse Windows and measure CI compatibility

Use one persistent Windows VM for ordinary start, test, and shutdown cycles.
Windows is installed once. Rebuilding an image or registering a new runner is
not part of normal startup.

## What is downloaded, created, and shared

| Artifact | Contents | Use |
| --- | --- | --- |
| Microsoft's Windows ISO | Windows installation media | Install into a new VM; Fusion's Get Windows feature obtains this media |
| Prepared Fusion VM | Installed Windows, VMware Tools, and selected workflow tools | Start repeatedly; retain a powered-off recovery baseline |
| Generalized reference VM | Windows prepared to create independent machines | Complete Windows setup and register a different runner in each clone |
| Public skill and recipe | Instructions, helpers, versions, and tests | Share the process; obtain vendor software through official download and license routes |

An ISO is not an installed VM. Neither is a copy of GitHub's hosted runner.
Keep Windows images, activation state, VM encryption secrets, and account state
out of the public skill repository.

## Reuse the same VM

After Windows updates, VMware Tools, and workflow tools are ready, shut down
Windows cleanly. Save a baseline before GitHub registration using Fusion's
supported snapshot or powered-off backup procedure. Record the Fusion version,
VM hardware, Windows edition/build, installer checksum, tool versions and
architectures, and baseline name locally. Retain encryption passwords and any
BitLocker recovery material in the user's credential store. A snapshot depends
on its VM's disk files and is not an independent backup.

Register the working VM once. Normal shutdown and startup preserve its runner
identity. Do not run Sysprep or restore a baseline just to turn the runner on.

Restoring a baseline discards later guest changes and can roll back credentials.
Establish what will be lost before restoring. For a pre-registration baseline,
keep the old runner offline, retire its exact GitHub registration as part of an
authorized replacement, then create and verify a fresh registration. Never run
an old registered copy alongside its replacement.

## Prepare independent clones only when requested

Plan a reference VM before completing personal Windows setup. Follow Microsoft's
[Audit Mode and Sysprep procedure](https://learn.microsoft.com/en-us/windows-hardware/manufacture/desktop/sysprep--generalize--a-windows-installation?view=windows-11).
Install system-wide drivers and tools in Audit Mode, avoid per-user Microsoft
Store app changes, and generalize Windows before capture, including when the
destination has similar hardware. Do not generalize an existing production runner.

Retain a pre-generalization recovery copy. With the reference VM unregistered
from GitHub, run this in elevated Windows PowerShell when ready to prepare and
shut down that reference installation:

```powershell
& "$env:WINDIR\System32\Sysprep\Sysprep.exe" /generalize /oobe /shutdown
```

Verify Sysprep succeeded and Windows shut down. Inspect
`C:\Windows\System32\Sysprep\Panther` on failure; shutdown alone does not prove
generalization. Keep the captured reference powered off until deployment.

Use the installed Fusion release's documented clone/copy procedure for the
actual encrypted Windows VM. Check support and free space before choosing a
clone type; do not assume linked clones are available. Preserve required TPM
and encryption support. Do not remove TPM devices, disable encryption to enable
cloning, or apply vSphere-specific TPM instructions to Fusion.

Each independent VM needs Windows first-run setup, a distinct machine identity,
an applicable Windows license, and its own GitHub registration and service
account configuration. Verify boot, VMware Tools, networking, architecture, and
service startup in the clone. Sysprep does not remove arbitrary application
secrets or make an image safe to publish.

## Select the GitHub comparison target

Refresh labels and inventories in [GitHub's runner-images repository](https://github.com/actions/runner-images)
at setup time. As checked on 2026-09-08:

| Target | OS family and architecture | Relationship to Fusion |
| --- | --- | --- |
| `windows-11-arm` | Windows 11 Enterprise, Arm64 | Closest hosted target for Apple Silicon; check edition and tools |
| `windows-latest` / `windows-2025` | Windows Server 2025, x64 | Different Windows product and CPU architecture from Apple Silicon Fusion |
| `windows-2022` | Windows Server 2022, x64 | Different Windows product; preserve this check when the project depends on it |

Apple Silicon Fusion cannot virtualize an x64 Windows OS. Windows Arm application
emulation does not change that. Intel Fusion can run x64 Windows, but Windows 11
still differs from Windows Server.

Match the workflow's shells, tools, actions, SDKs, and artifact architecture.
Select the local Windows edition under the user's license; do not claim
Enterprise equivalence for Home or Pro. Hosted Windows jobs use administrator
privileges, while this skill defaults to a dedicated non-administrator account.
Record that difference and test under the intended local account.

GitHub labels move over time. Record each job's actual image version from its
**Set up job** log and environment report. The latest inventory may differ during
rollout. Matching a release such as 25H2 does not establish matching updates or tools.

## Run identical compatibility tests

The [compatibility templates](../templates/compatibility/) contain a manual
comparison workflow, a shared job, and one PowerShell script. Copy them to the
repository paths in that directory's README. Follow the scope and default-branch
dispatch requirements in [runner provisioning](runner-provisioning.md).

Run the hosted jobs with `include_fusion` false. Once the VM is ready, match the
Fusion job's labels to its recorded runner and dispatch with `include_fusion`
true. All jobs must use the same committed script. The local service needs native
PowerShell 7, Git, and a current runner compatible with the pinned actions.
On an Intel Mac, update both the local selector's architecture label and
`expected_architecture` to `X64` as described in the template README.

Compare JSON reports for Windows edition/build, native and process architectures,
PowerShell, Git, administrator status, and hosted image version. The test covers
checkout, Windows storage, Unicode data and paths, ZIP archives, C# compilation,
a native Windows API, and child-process exit codes. Add the project's build and
tests before claiming that project's CI is compatible.

Reboot the guest, confirm the same runner returns without an interactive login,
and repeat the local job. For a cloneable image, also boot and test an independent
clone. Retain the commit, run URLs, reports, baseline identity, and differences
locally. Refresh the baseline and repeat relevant tests after OS or tool updates.
