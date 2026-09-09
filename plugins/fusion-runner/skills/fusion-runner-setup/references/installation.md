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

### Install and confirm first launch

Verify the completed disk image and any vendor-provided digest. Then follow
Broadcom's [installation instructions](https://knowledge.broadcom.com/external/article/315638):

1. In **Finder ▸ Downloads**, or the recorded download directory, double-click
   the completed Fusion `.dmg`.
2. In the mounted **VMware Fusion** disk window, double-click the **VMware
   Fusion** icon to start installation.
3. Complete first-launch prompts. Broadcom documents the ordinary downloaded-app
   **Open** confirmation, administrator authentication, and the license
   agreement. Have the user handle administrator credentials and agreement
   acceptance directly. These documented prompts were not all observed in the
   validation run; use the actual screen rather than assuming their order.
4. Open **Finder ▸ Applications ▸ VMware Fusion**. Record the installed version
   and confirm that its VM library or **New Virtual Machine** window opens.

The downloaded `.dmg` alone does not establish that Fusion is installed. For
`26H1u1`, the installed app's version metadata was `26.0.1`, build `25689522`;
record the public release name and build as well as the app version.

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

### Windows 11 Arm64 wizard in Fusion 26H1u1

The following screens were observed on Apple Silicon with Fusion `26H1u1` on
2026-09-08, through saving the VM, configuring its hardware, and opening Windows
Setup's language, setup-option, product-key, image-selection, and license-term
screens. The intervening keyboard prompt was reported by the user. Installed
Windows and local CI validation were still pending at this checkpoint.
On another release or an Intel Mac, use the actual labels and matching media.

1. **Choose the existing Windows installer.** From Fusion's **New Virtual
   Machine** window, use **Use another disc or disc image...**. If needed, start
   the wizard from **File ▸ New** and choose the disc or image installation
   route. In the file chooser, press `Command+Shift+G`, enter the full ISO path
   recorded in section 3, press `Return`, and click **Open**. This also works
   when the ISO is inside a hidden local directory.
2. **Verify the detected guest.** The selected ISO appears in the wizard. For
   the Arm64 media used here, its detected system reads **Windows 11 64-bit
   Arm**. Confirm that this matches the Mac and selected media, then click
   **Continue**. Stop and correct a media mismatch before creating the VM.
3. **Set the boot firmware.** At **Choose Firmware Type**, use **UEFI**, select
   **UEFI Secure Boot**, and click **Continue**. In the observed run, UEFI was
   selected already but its Secure Boot checkbox was initially clear.
4. **Let the user create the VM encryption password.** At **Choose Encryption**,
   Fusion requires a password for its virtual Trusted Platform Module (TPM),
   the security device used by Windows 11. The user enters and confirms the
   password and retains it securely. Explain **Remember password in the macOS
   Keychain** before the user continues; this option was selected by default.
   It stores the password for later unlocking, but does not prove unattended
   startup will work. The observed default encrypts only files needed for the
   TPM; the other option encrypts all VM files. Record the chosen options
   without the password. **Done when:** the user completes this screen and the
   next configuration screen is visible.
5. **Review the initial VM configuration.** At **Finish**, inspect the guest,
   disk, memory, networking, and CPU summary. The observed defaults were a
   64 GB disk, 4 GB memory, 2 CPU cores, and **Share with my Mac (NAT)**. Use
   **Customize Settings** to adjust resources before booting. This opens a save
   dialog first; it does not open hardware settings immediately.
6. **Save the VM in its planned directory.** In the **Save** dialog, give the
   `.vmwarevm` bundle a recognizable name. Use `Command+Shift+G` to navigate to
   the actual VM directory selected during host inspection, then click
   **Save**. Do not replace an existing bundle. **Done when:** the VM's
   **Settings** window opens and its actual bundle and `.vmx` paths are recorded
   in the local progress note.
7. **Apply the chosen CPU and memory allocation.** Open **Processors & Memory**,
   select the CPU count, enter memory in MB, and press `Tab` to apply the value.
   The validation VM used 4 cores and `8192` MB on a Mac with 14 cores and
   48 GB of memory. Size another VM for its host and workflow; these values are
   an observed example, not requirements for every Mac.
8. **Apply the chosen disk capacity.** Use **Show All ▸ Hard Disk (NVMe)**. Set
   **Disk size**, expand **Advanced options**, and leave **Pre-allocate disk
   space** clear for a disk that grows as needed. Click **Apply** and verify
   the displayed capacity. The validation VM used 96 GB with **Split into
   multiple files** selected. A growable disk still needs enough host storage
   for actual guest data and any later recovery baseline.
9. **Start the installer.** Close the settings window to return to the VM
   console, then use **Start Up**. Click inside the console so it receives
   keyboard input. When **Press any key to boot from CD or DVD.** appears,
   press `Space` immediately. This is a plain-text message on the guest screen;
   there is no button, selected control, or focus highlight to wait for. Do not
   wait for an additional visual cue before pressing `Space`. Confirm that
   Windows Setup actually appears. A powered-on VM or a firmware screen alone
   is not a successful installer boot.

If the initial boot falls through to **EFI Network** and Fusion reports **No
operating system was found**, verify that the correct ISO is still attached in
**CD/DVD (SATA)** settings. In the observed run, dismissing that notice exposed
the firmware's **Boot Manager**. Click in the console, use the arrow keys to
select **EFI VMware Virtual SATA CDROM Drive (1.0)**, and press `Return`. Press
`Space` immediately when the CD/DVD boot prompt appears. These are two separate
actions: the first selects the drive; the second tells the Windows installer
to boot. If the prompt expires, the guest can return to Boot Manager. Broadcom
documents the [need to focus the console and answer the boot prompt promptly](https://knowledge.broadcom.com/external/article/375069/powering-on-windows-11-vm-on-vmware-fusi.html).
The drive label may differ with another virtual device configuration; select
the attached installer drive, not the empty virtual hard disk or network boot.
Record whether Windows Setup
then opens; do not infer that it did from selecting the drive.

If UI automation cannot reliably answer this brief boot prompt, hand off only
the two keystrokes to the user: `Return` on the selected installer drive, then
`Space` at the CD/DVD prompt. Give the exact VM window name and use Windows
Setup appearing as the completion check. Resume automation after observing that
screen, and preserve the attempted recovery in the progress record.

### Continue Windows Setup

The user confirmed that pressing `Space` immediately succeeded. The following
checkpoint records distinguish observed screens from user-reported actions:

1. **Select language and regional format.** The observed **Windows 11 Setup ▸
   Select language settings** screen had **Language to install** and **Time and
   currency format** both set to **English (United States)**. Select the intended
   values and use **Next**. Reaching this screen verifies installer boot, not an
   installed Windows system.
2. **Select the keyboard layout.** Choose the layout that matches the keyboard
   the user intends to use, then advance. The validation user reported a **US**
   keyboard decision; this screen was not captured directly. Record the actual
   selection rather than inferring it from the language setting.
3. **Choose Windows installation.** The next observed screen was **Select setup
   option**, with **Install Windows 11** selected and the deletion
   acknowledgement checked. For a new installation, verify that the intended
   destination is the new VM's virtual disk before continuing with **Next**.
   Recheck the exact destination if a later disk-selection screen appears.
   Observing these selections does not establish that installation has begun.
4. **Continue past the product-key prompt.** At **Product key**, have the user
   enter a key directly if that is their chosen activation route. Otherwise,
   the installer offers **I don't have a product key**, which Microsoft
   documents for [continuing installation before activation](https://support.microsoft.com/en-us/windows/activation/activate-windows).
   In this run, the key field was empty and the agent used that link; **Select
   Image** then appeared. Do not request or retain a product key in chat or
   public records. Continuing without a key does not establish activation.
5. **Choose the Windows edition.** The observed **Select Image** screen
   offered **Windows 11 Home**, **Windows 11 Home Single Language**, and
   **Windows 11 Pro**, with Home initially selected. Establish the intended
   edition and matching license before continuing. Broadcom's installation
   example uses Pro; that is not permission to override an existing Home license
   or buy Windows. This media does not offer the Enterprise edition used by the
   hosted Arm64 comparison job. Record the deliberate choice separately from
   the initial default. The validation user chose **Windows 11 Pro**. The agent
   selected it, verified the Pro row and description, and clicked **Next**.
6. **Handle the Windows license agreement.** The next observed screen was
   **Applicable notices and license terms**, displaying Microsoft's Windows
   agreement, last updated April 2024, with **Decline** and **Accept**. This is
   separate from the earlier acknowledgement that installing Windows will
   delete the selected destination's contents. Present the actual agreement
   for the user's acceptance, then continue when authorized. Acceptance was
   pending at this checkpoint; do not record it as completed merely because
   the user chose an edition.

Without guest integration tools, the first click may only focus Fusion and
capture the guest mouse. In the product-key step, a fresh check after the first
click showed no verified page transition; a second click on the still-visible
link advanced. Verify the current target and result before another click, and
do not treat mouse capture as completion of a setup step.

Guest controls may not appear in macOS accessibility data even when their pixels
are visible in Fusion. In this run, automatic approval review rejected some
earlier guest inputs for that reason; later product-key input succeeded after
the user completed the preceding screen. If an action cannot be verified, hand
off the specific current step and completion check to the user. Record who performed it
and observe the resulting screen before marking it complete; do not bypass a
rejected action through another input mechanism.

Record subsequent edition, licensing, storage, and first-run screens as they
occur. The remaining procedure below states the required setup and verification;
it was not completed at the checkpoint above.

Continue with the existing VM recorded above; do not create it again on resume.
Verify its recorded location, UEFI firmware, and Windows 11 configuration,
including the virtual Trusted Platform Module (TPM) and its encryption. The user
retains the encryption password in their chosen credential store; never place
it in a command, transcript, or profile JSON. Broadcom documents the
[Windows 11 installation flow and VMware Tools installation](https://knowledge.broadcom.com/external/article/375069/powering-on-windows-11-vm-on-vmware-fusi.html).

Use NAT networking unless the task requires a different network arrangement. A runner initiates outbound connections; registration does not require exposing a listener on the Mac's network. Keep host home folders, credential directories, and unrelated project trees out of the guest. A Mac shared folder is not the runner's Windows work directory.

Complete Windows's first-run prompts, apply updates, install VMware Tools, and reboot when required. Let the user handle identity and password prompts directly. Use the guest console when guest automation is unavailable; do not enable remote administration merely to avoid a short interactive step.

Locate the actual `.vmx` configuration file inside the VM bundle using Fusion's location information or Finder **Show Package Contents**. Record the absolute path. The `.vmwarevm` bundle itself is not the `.vmx` argument consumed by the helper.

Confirm the Windows desktop boots, networking works, VMware Tools is installed, and the guest architecture agrees with the selected media. Continue with [runner provisioning](runner-provisioning.md). A successful Fusion launch alone does not establish any of these guest checks.
