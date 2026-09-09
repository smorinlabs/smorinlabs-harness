# fusion-runner-setup

Install VMware Fusion on a Mac, create a Windows 11 virtual machine, install the
tools required by a GitHub Actions workflow, and register a Windows runner
service. The companion `fusion-runner-run` skill operates the resulting VM.

**Triggers on:** "set up a Windows runner on my Mac", "install Fusion for CI",
"prepare a Fusion runner VM".
**Arguments:** none; describe the target repository, workflows, and any existing VM
in ordinary language.

## What it prepares

| Mac | Windows installation | GitHub runner architecture |
|---|---|---|
| Apple Silicon | Windows 11 Arm64; Fusion's Get Windows option or Microsoft's Arm64 ISO | ARM64 |
| Intel | Windows 11 x64 from Microsoft's x64 ISO | X64 |

Fusion virtualizes the Mac's processor architecture. A Windows Arm VM can run
many x64 applications through Windows emulation, but it does not reproduce a
Windows Server x64 GitHub-hosted runner. The skill records that distinction and
installs dependencies from the chosen workflow instead of claiming to supply
GitHub's entire hosted image.

Windows is installed once and the working VM is reused for later jobs. A
preserved, powered-off baseline keeps the prepared state for recovery; the
working VM accumulates job changes and updates. Starting it does not reset it.
The skill requires an actual restoration check before reporting a reusable
baseline as verified. Independent clones need Windows image preparation and
fresh runner identities. An optional comparison workflow runs identical tests
on Fusion, `windows-11-arm`, and `windows-latest`
and records the actual Windows builds and tool versions.

The setup covers official downloads, available disk space, Windows installation,
VMware Tools, Windows updates, Git and PowerShell as needed, workflow-specific
SDKs, a dedicated runner account, runner registration, service startup, and
verification. It writes a local JSON handoff containing the VM path, architecture,
runner identity, exact Windows service name, and evidence. Credentials are not
stored in that handoff.

The agent performs the available operations and hands back individual interactive
steps when necessary. Broadcom account access, administrator prompts, Windows
licensing, and initial Windows setup can require the user's participation.
Fusion is free for personal and commercial use; Windows licensing is separate.
The [Fusion download walkthrough](../../plugins/fusion-runner/skills/fusion-runner-setup/references/installation.md#browser-download-walkthrough)
explains where to create a free Broadcom account, how to sign in and reopen the
product URL, which release and Mac installer to select, and how to complete the
terms and profile prompts. Its dated example is `26H1u1`, build `25689522`, with
the filename `VMware-Fusion-26H1u1-25689522_universal.dmg`. The agent verifies the
current compatible release at setup time.
The [VM creation walkthrough](../../plugins/fusion-runner/skills/fusion-runner-setup/references/installation.md#windows-11-arm64-wizard-in-fusion-26h1u1)
records the observed ISO selection, firmware, encryption, VM save, and hardware
settings screens. It also covers selecting the installer in the firmware boot
menu when the first boot falls through to the network. At **Press any key to
boot from CD or DVD.**, press `Space` immediately: this is plain text with no
button or focus highlight. The guide continues through the language, keyboard,
setup-option, product-key, edition, license, disk, and first-run prompts,
distinguishing observed screens from user reports. It records that Home was the initial edition default,
followed by the user's deliberate choice of Pro, and requires a choice that
matches the intended license. Its [first-run walkthrough](../../plugins/fusion-runner/skills/fusion-runner-setup/references/installation.md#complete-first-run-setup-and-resolve-a-missing-network-driver)
records the region and keyboard choices, the missing network adapter, and
mounting and launching VMware Tools. Tools installation must be verified before
that prerequisite is marked complete.
During setup, the agent saves each completed stage and pending prompt in a local
progress record so a later session can resume from verified state.
The plugin distributes instructions and helpers, with official download links.
It does not redistribute Fusion, Windows installation media, or a registered VM.

## Install

Install the two skills together as the `fusion-runner` plugin:

```text
/plugin marketplace add smorinlabs/smorinlabs-harness
/plugin install fusion-runner@smorinlabs-harness
```

For Codex, use the marketplace installation described in the repository
[README](../../README.md#install), or use the direct skill placement below.

| Mode | When to use it | Placement |
|---|---|---|
| Plugin | Use both skills with their references and helpers | Install `fusion-runner@smorinlabs-harness` |
| Development symlink | Edit a local clone and use those changes | Link both skill directories from the clone into the tool's skills directory |
| Direct copy | Use the skills without a marketplace connection | Copy both complete skill directories into the tool's skills directory |

For a new local clone, these terminal commands install development symlinks for
both Claude Code and Codex. Use an existing clone when one is already available;
do not overwrite existing skill placements.

```bash
git clone https://github.com/smorinlabs/smorinlabs-harness.git
fusion_skills="$(pwd)/smorinlabs-harness/plugins/fusion-runner/skills"
mkdir -p "$HOME/.claude/skills" "$HOME/.agents/skills"
for fusion_skill in fusion-runner-setup fusion-runner-run; do
  ln -s "$fusion_skills/$fusion_skill" "$HOME/.claude/skills/$fusion_skill"
  ln -s "$fusion_skills/$fusion_skill" "$HOME/.agents/skills/$fusion_skill"
done
```

For direct copies, replace each `ln -s` with `cp -R` and keep both directories
together. References and helpers inside each directory must be included.

## Example session

> "Use fusion-runner-setup to prepare a Windows runner in Fusion on this Mac
> for the private repository I have open. Use its Windows test workflow to
> determine the tools. Leave the VM off when setup is complete."

The agent inspects the Mac and workflow, provisions the guest, verifies the
runner's service and GitHub status, and records the setup. A sample
`workflow_dispatch` smoke workflow is included; editing and dispatching it are
separate actions taken when authorized. It reports whether a real CI job ran.

## Scope and validation

The default is one reusable runner in a VM that is powered on when needed. Jobs
must be trusted to run on that Mac. A publicly distributed skill does not make
the machine appropriate for arbitrary public pull requests. A custom runner
label selects the machine; repository permissions and runner-group access
control who can use it.

The host probe has been exercised on macOS. Automated VM-control tests use a
simulated `vmrun` executable. On 2026-09-08, the included compatibility workflow
passed on real GitHub-hosted Windows 11 Arm64 and Windows Server x64 runners.
Its local Fusion job was skipped. Fusion `26H1u1` is installed on an Apple
Silicon Mac. A VM has been created with 4 CPU cores, 8 GB memory, a 96 GB growable
disk, UEFI Secure Boot, and NAT networking. On 2026-09-09, Windows 11 Pro was
installed onto the virtual disk after the user approved its license and clean
installation. Automatic restarts and first-run region and keyboard screens
were observed. First-run setup is incomplete: its network page showed no
adapter, and VMware Tools was launched but has not been verified as installed.
The Windows desktop, runner service registration, a local CI job, and baseline restoration remain
**unverified**.
Hosted success does not validate the VM. The entrypoints preserve that
distinction during actual setup.

Implementation details and current primary sources:
[installation](../../plugins/fusion-runner/skills/fusion-runner-setup/references/installation.md),
[runner provisioning](../../plugins/fusion-runner/skills/fusion-runner-setup/references/runner-provisioning.md),
[reuse and compatibility](../../plugins/fusion-runner/skills/fusion-runner-setup/references/reuse-and-compatibility.md),
[handoff](../../plugins/fusion-runner/skills/fusion-runner-setup/references/handoff.md).
