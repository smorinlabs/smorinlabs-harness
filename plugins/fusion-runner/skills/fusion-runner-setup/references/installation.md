# Install Fusion and Windows

Use this reference until a supported Windows guest boots with VMware Tools installed. It prepares a VM, not a copy of GitHub's hosted runner image.

## 1. Inspect the Mac and existing state

Locate this skill's directory from its installed `SKILL.md` path. In the macOS terminal, resolve Python 3 with `command -v python3`; if absent, use an existing Python environment's executable or install Python through the user's established method. Set `FUSION_RUNNER_PYTHON` to that executable and `FUSION_RUNNER_SETUP_SKILL` to this skill's absolute directory. Then run:

```sh
"$FUSION_RUNNER_PYTHON" "$FUSION_RUNNER_SETUP_SKILL/scripts/host_preflight.py" probe --json
```

The optional `--storage PATH` checks an existing directory on the planned VM volume; `--fusion-app PATH` inspects an installation outside the usual application directory. These flags belong to the helper, not to skill invocation.

Use its host processor, macOS version, memory, free storage, and Fusion findings to choose the next step. If hardware cannot be identified, verify through **Apple menu ▸ About This Mac**. A translated process architecture is insufficient.

Before allocating storage, inspect the proposed VM destination. Reuse a known suitable VM only when that matches the task. Do not overwrite an existing VM bundle, disk, or installer. Size CPU, memory, and disk for the intended builds and available host resources. Windows installation requirements alone do not cover compiler installations, build caches, or snapshots.

## 2. Obtain and install Fusion

Check the current release's host requirements against the actual Mac and macOS version. Use Broadcom's [official download instructions](https://knowledge.broadcom.com/external/article/368667/download-and-license-vmware-desktop-hype.html) to reach the Fusion download. Broadcom currently offers Fusion free for personal, educational, and commercial use; Windows licensing is separate. Refresh the terms during installation rather than embedding a price or license key in this skill.

Download the current compatible installer from Broadcom. Complete the documented installation and first launch. If Broadcom requires account registration, a profile, a compliance form, or terms acceptance, the user supplies their own information. If the Mac requests administrator authentication, have the user respond in the system prompt. Preserve the actual installer path and version for the handoff.

If download access is pending, report that exact state and continue work that does not depend on the installer. Do not substitute an unofficial mirror or describe a downloaded disk image as an installed application.

## 3. Select matching Windows media

Fusion virtualizes the Mac's processor architecture. Match the installation media as follows; consult the [current Fusion feature matrix](https://knowledge.broadcom.com/external/article/315609) if the installed release differs.

| Physical Mac processor | Windows guest | Official media route |
| --- | --- | --- |
| Apple Silicon | Windows 11 Arm64 | Fusion **File ▸ New ▸ Get Windows from Microsoft**, or Microsoft's [Arm64 ISO](https://www.microsoft.com/en-us/software-download/windows11arm64) |
| Intel | Windows 11 x64 | Microsoft's [Windows 11 ISO for x64 devices](https://www.microsoft.com/en-us/software-download/windows11), imported into Fusion |

An ISO is installation media. Neither download is a preconfigured GitHub Actions runner. Fusion's **Get Windows** feature is available for supported Apple Silicon releases; do not direct Intel users to it.

Use the downloaded media's actual edition and language. Verify its checksum against Microsoft's value when available. Complete Windows activation under the user's applicable license; do not buy a license, invent a product key, or bypass setup requirements. If the user chooses an edition during installation, explain the effect before that choice.

## 4. Create and boot the VM

For ordinary CI use, prepare one persistent VM. If the user requests independent
clones, read [reuse and compatibility](reuse-and-compatibility.md) before Windows
first-run setup; a cloneable reference image needs Microsoft's image-preparation
workflow. An installer ISO is not an already prepared runner image.

Follow the installed Fusion wizard with the selected media. Give the VM a recognizable name and record its storage location. Use UEFI firmware and the supported Windows 11 configuration, including the virtual Trusted Platform Module (TPM). Fusion may require encryption for the TPM. Have the user retain the encryption password through their chosen credential store; never place it in a command, transcript, or profile JSON. Broadcom documents the [Windows 11 installation flow and VMware Tools installation](https://knowledge.broadcom.com/external/article/375069/powering-on-windows-11-vm-on-vmware-fusi.html).

Use NAT networking unless the task requires a different network arrangement. A runner initiates outbound connections; registration does not require exposing a listener on the Mac's network. Keep host home folders, credential directories, and unrelated project trees out of the guest. A Mac shared folder is not the runner's Windows work directory.

Complete Windows's first-run prompts, apply updates, install VMware Tools, and reboot when required. Let the user handle identity and password prompts directly. Use the guest console when guest automation is unavailable; do not enable remote administration merely to avoid a short interactive step.

Locate the actual `.vmx` configuration file inside the VM bundle using Fusion's location information or Finder **Show Package Contents**. Record the absolute path. The `.vmwarevm` bundle itself is not the `.vmx` argument consumed by the helper.

Confirm the Windows desktop boots, networking works, VMware Tools is installed, and the guest architecture agrees with the selected media. Continue with [runner provisioning](runner-provisioning.md). A successful Fusion launch alone does not establish any of these guest checks.
