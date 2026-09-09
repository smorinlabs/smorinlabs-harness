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
2026-09-08 and 2026-09-09, through VM creation, Windows installation onto its
virtual disk, automatic restarts, and Windows first-run setup. The installer's
keyboard prompt was reported by the user; the later first-run keyboard screen
was observed directly. First-run setup initially stopped at its network page
because no adapter was available. The VMware Tools wizard was then completed,
Windows showed a connected network, and its required restart completed. Fusion
reported Tools as installed and current afterward. Windows first-run setup
repeated its region and keyboard prompts, reached its online update check, and
accepted a device name. The user later reported selecting personal-use setup;
the agent then observed the three-stage Windows update screen. Update completion,
Microsoft-account sign-in, the Windows desktop, and local CI validation were
still pending at this checkpoint.
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
   for the user's acceptance, then continue when authorized. Carry forward
   explicit approval; do not ask again for an already approved agreement or
   routine setup choices. In this run, the user approved the agreement and
   remaining installation steps. The agent selected **Accept** and verified
   that the disk-selection page appeared.
7. **Select the intended virtual disk.** At **Select location to install
   Windows 11**, the observed destination was **Disk 0 Unallocated Space**,
   with **96.0 GB** total and free. This matched the new VM's configured disk.
   Select the intended empty virtual disk and click **Next**; let Setup create
   its required partitions. Stop and investigate a different capacity,
   unexpected existing partitions, or an ambiguous destination before writing.
8. **Start the installation.** At **Ready to install**, verify **Install Windows
   11 Pro** and **Keep nothing**, or the edition and installation mode actually
   authorized. Click **Install**. In this run, **Installing Windows 11** appeared
   and advanced from **11% complete** to **34% complete**. This verifies that
   installation started; it does not establish that Windows setup is complete.
9. **Allow automatic restarts.** Setup warns that the PC will restart several
   times. Leave the VM running. On subsequent restarts, do not press a key at
   the CD/DVD prompt again: installation should continue from the virtual disk.
   Observe the actual first-run screens before recording this stage complete.

### Complete first-run setup and resolve a missing network driver

The following region, keyboard, and network screens were observed after Windows
installed onto the virtual disk. They are separate from the earlier installer
language and keyboard choices.

1. **Confirm the region.** At **Is this the right country or region?**, verify
   the intended country and select **Yes**. The validation VM used **United
   States** and advanced to the keyboard page.
2. **Confirm the keyboard.** At **Is this the right keyboard layout or input
   method?**, verify the intended layout and select **Yes**. The validation VM
   used **US**. At the second-layout prompt, select **Skip** if no second layout
   is needed; this was the observed choice.
3. **Check the actual network state.** At **Let's connect you to a network**,
   distinguish a connected adapter from a missing driver. In this run, no
   adapter appeared, **Install driver** was available, and **Next** was disabled.
   Fusion's adapter was connected using NAT. That host setting alone did not
   establish that Windows had a working network driver. Keep the existing VM
   and install the required vendor driver; do not bypass the network requirement.
4. **Mount the matching VMware Tools disc.** In the Mac's installed **VMware
   Fusion** application, use **Virtual Machine ▸ Install VMware Tools**, then
   **Install** in the confirmation. Fusion connected its bundled Arm64 Tools
   ISO in this run. This replaces the attached installer disc; it does not
   reinstall Windows. Mounting the disc is not evidence that Tools is installed.
5. **Launch the installer from the guest.** Focus the Windows guest and press
   `Shift+F10` to open its Administrator command prompt. Confirm that the command
   window is actually visible and focused before typing. Locate the mounted
   **VMware Tools** volume; it was drive `D:` here. The following commands inspect
   that drive and launch its installer. Substitute the verified drive letter if
   another letter is assigned.

   ```bat
   dir D:\
   D:\setup.exe
   ```

   In this run, `D:` contained `setup.exe`, and a subsequent process check
   identified `D:\setup.exe` with the window title **VMware Tools Setup**.
   Clipboard paste failed before Tools was installed; typing into the focused
   console worked. Verify the complete command before pressing `Return`. Do not
   repeatedly launch the installer when it is already running.
6. **Bring a hidden Tools wizard forward.** If Windows setup or a command
   prompt covers the installer, focus the guest and press `Ctrl+Alt+Tab`.
   On a Mac keyboard, use `Control+Option+Tab` inside the guest. This opens the
   Windows window switcher and keeps it visible after the keys are released.
   Use the arrow keys to select the **VMware Tools Setup** thumbnail, verify
   its selection, and press `Return`. This recovered the running wizard in the
   validation VM. Repeatedly opening `Shift+F10` creates additional command
   windows; it does not bring the existing Tools wizard forward.
7. **Finish Tools and verify connectivity.** Follow the actual VMware Tools
   wizard, as described in Broadcom's
   [Fusion Tools installation instructions](https://knowledge.broadcom.com/external/article/315622/installing-vmware-tools-in-a-fusion-virt.html).
   The observed wizard identified version `13.1.5.0.25544008`. At **Welcome**,
   select **Next**. At **Choose Setup Type**, keep **Typical** and select **Next**;
   `Alt+N` worked when keyboard navigation was needed. At **Ready to install
   VMware Tools**, select **Install**. Wait for **Completed the VMware Tools
   Setup Wizard**, then select **Finish**. Accept the requested restart when
   installation is authorized. These screens and choices were observed in this
   run. Windows showed **Network — Connected** and enabled **Next** after the
   drivers installed, before restarting. After the restart, verify that the
   adapter still works and continue first-run setup. A running installer process,
   a mounted disc, or Fusion's **Cancel VMware Tools Installation** menu label
   alone does not establish a successful Tools installation.
8. **Resume first-run setup after the restart.** If the region and keyboard
   prompts reappear, reuse the user's recorded region, primary keyboard, and
   second-layout choices. In this run, Windows repeated those prompts; the
   recorded choices were **United States**, **US**, and **Skip** for a second
   layout. After confirming them again, Windows advanced to
   **Just a moment, checking for updates**, then announced another restart.
   Fusion's post-restart log reported Tools as installed and current. These
   observations confirm progress beyond the missing-driver screen; they do not
   establish a completed Windows desktop or runner setup.
9. **Give the guest a recognizable device name.** At **Name your device**, enter
   a unique name suitable for the CI machine and follow the displayed character
   restrictions. Record the actual name locally. The screen warns that Windows
   will restart after naming. Select **Next** and verify that setup advances.
   In this run, typing the name worked, but a click and `Return` did not advance
   the page. Pressing `Tab` until **Next** had a visible focus outline, then
   pressing `Space`, activated it. Use the current focus outline rather than
   assuming a fixed number of Tab presses.
10. **Select the intended account setup.** The next observed screen was **How
    would you like to set up this device?**, offering **Set up for personal
    use** and **Set up for work or school**. Use the account setup authorized
    for the CI VM. **Personal use** suits a standalone VM: Microsoft requires
    internet access and a personal Microsoft account during Windows 11 Pro's
    [initial personal setup](https://www.microsoft.com/en-us/windows/windows-11-specifications).
    **Work or school** provides a route to
    [organizational sign-in and device management](https://support.microsoft.com/en-us/accounts-billing/work-school/join-your-work-device-to-your-work-or-school-network).
    This is a choice about Windows sign-in and management. GitHub lists
    Windows 11 among its [supported runner operating systems](https://docs.github.com/en/actions/reference/runners/self-hosted-runners)
    without requiring organizational enrollment, so personal setup is suitable
    for running CI jobs. The dedicated Windows account that will run the
    GitHub Actions service is configured separately during runner provisioning.

    For an authorized personal setup, select **Set up for personal use**, then
    **Next**, and verify that Windows advances. Let the user complete protected
    Microsoft-account sign-in and any new password or PIN entry and submission
    directly in Windows. Record the completed stage without copying credentials
    into the progress record. In this validation run, the user authorized
    personal use and later reported clicking it. The agent subsequently
    observed Windows beyond the account-type screen, at the update stage below.
    The click itself and subsequent Microsoft-account sign-in were not observed
    by the agent.

    If a different deployment needs a local-account setup route, inspect the
    options actually offered by that Pro build; this run had not verified such
    a route. Selecting a route does not authorize associating an account or
    enrolling the VM with an organization. Do not bypass account or network
    requirements.
11. **Allow first-run Windows updates to finish.** The next observed screen was
    **Getting the latest features and security updates**, with **Step 1 of 3:
    Starting update - 3%**. Windows said it would restart and then continue
    setup. Leave the VM running through the update and automatic restart.
    **Update later** was available but was not selected in this run. Observe
    the next screen before marking updates or account setup complete; this
    update stage was still in progress at the recorded checkpoint.
12. **Complete the remaining Windows screens.** Use the user's authorized account
    and preference choices; the user handles protected credential entry. The
    Windows desktop and remaining first-run screens were still pending at this
    checkpoint. Continue from the actual screen after the restart.

When automation enters Windows commands through JavaScript, preserve literal
backslashes with `String.raw` or correct string escaping. A path containing
`\v` in an ordinary JavaScript string can become a control character. This
caused a malformed diagnostic command during validation; it was corrected
before further execution. Verify the displayed command before submitting it.

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

A tool error is a separate failure from an approval rejection. At the
personal-use screen, automated coordinate clicks repeatedly returned
`Computer Use server error -10005: noWindowsAvailable`, although screenshots
and native Fusion menu actions still worked. Refreshing the automation session
and bringing the installed Fusion app forward did not restore verified guest
input. The user reported a successful manual click, and Windows then advanced.
The precise cause of the tool failure was not established. Do not describe it
as Windows rejecting the choice or as a missing user authorization. If recovery
does not work, hand off the current click and verify the resulting screen.

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
