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

Download **VMware Fusion for macOS** as a `.dmg` disk image. Fusion is the Mac
application; the Windows ISO in section 3 is a separate download. Check Downloads
and any user-specified location first so an existing installer is not downloaded
again. Broadcom offers Fusion free for personal, educational, and commercial
use; Windows licensing is separate.

**Release checked on 2026-09-08: `26H1u1`, build `25689522`.** The Mac installer
is named `VMware-Fusion-26H1u1-25689522_universal.dmg`. The universal installer
serves both Apple Silicon and Intel Macs; Windows media must still match the
Mac's processor. Broadcom's [release advisory](https://support.broadcom.com/web/ecx/support-content-notification/-/external/content/SecurityAdvisories/0/38288)
identifies `26H1u1` as the updated release. Consult its
[release notes](https://techdocs.broadcom.com/us/en/vmware-cis/desktop-hypervisors/fusion-pro/26H1/release-notes/vmware-fusion-26h1u1-release-notes.html)
and the live download list during future setups. Select the newest compatible
release and state its exact version and filename; do not leave the user with
only the instruction "download the latest." Check its host requirements before
installing. Treat the dated filename above as an example once a newer release
is available.

### Browser download walkthrough

Give the user the account URL, the URL to reopen after sign-in, the selected
release, the installer filename, and the completion check together. Delegate
identity, password, verification, and agreement prompts to the user; never ask
for their values in chat. These steps follow Broadcom's
[account registration](https://knowledge.broadcom.com/external/article/145581/register-for-an-account-on-the-broadcom.html)
and [free software download](https://knowledge.broadcom.com/external/article/397417/downloading-free-software-from-the-broad.html)
instructions.

1. **Create a free Broadcom account, if needed.** In the browser, open
   <https://profile.broadcom.com/web/registration>. Complete registration with an
   individual email address, the emailed verification code, and the account
   prompts. An existing Broadcom account can be used instead. A basic account is
   sufficient for free Fusion downloads; a paid subscription, corporate email,
   and enterprise Site ID are not required. **Done when:** registration is
   complete or the user already has an account they can sign into.
2. **Sign into the support portal.** In the same browser, open
   <https://support.broadcom.com/> and use **Support Portal** to sign in. Complete
   any authentication prompts there. **Done when:** the support portal shows
   the signed-in account or dashboard.
3. **Reopen the Fusion download URL after signing in.** Open this URL explicitly
   in the same browser, even if registration or login sent the user elsewhere:
   <https://support.broadcom.com/group/ecx/productdownloads?freeDownloads=true&subfamily=VMware+Fusion>.
   If the portal lands on a dashboard instead, navigate from
   <https://support.broadcom.com/> through **My Downloads** and
   **Free Software Downloads available HERE**, then search for **VMware Fusion**.
   **Done when:** Fusion's available releases are visible.
4. **Select the Fusion release for the Mac.** On that Fusion download page,
   select **26H1u1** for this dated walkthrough. Expand the **VMware Fusion
   26H1** family first if the portal groups updates under it. For a newer release,
   use the exact version verified above. **Done when:** the selected release's
   file list contains the macOS `.dmg` installer. VMware Workstation's `.exe`
   and Linux `.bundle` installers are for other host operating systems.
5. **Complete the download requirements.** On the selected release's file page,
   open **Terms and Conditions**, read the agreement, and return to the file
   page. Opening the link enables its acceptance checkbox; the user handles
   acceptance. Use the download icon beside the Mac installer. If Broadcom asks
   for additional verification, the user completes their basic profile and
   Trade Compliance form with their actual details. **Done when:** the download
   starts or the portal enables the file's download icon. If the portal reports
   **Account verification is pending**, record that blocker and follow the
   account-help link in Broadcom's download instructions; do not invent a Site ID
   or promise that signing in again will approve the account.
6. **Finish the Mac installer download.** On the same file page, use the download
   icon again if verification only enabled it. Wait for the browser's download
   to complete. For this release, confirm the completed file is
   `VMware-Fusion-26H1u1-25689522_universal.dmg`. **Done when:** the full `.dmg`
   exists on the Mac, with its actual destination path and version recorded.
   A release page, an enabled icon, or a partial browser download is not the file.

Verify the completed disk image and any vendor-provided digest, then open it and
complete Fusion's documented installation and first launch. Have the user handle
macOS administrator authentication in the system prompt. Record the installed
Fusion version and confirm the app opens before continuing to Windows setup.
The downloaded `.dmg` alone does not establish that Fusion is installed.

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
