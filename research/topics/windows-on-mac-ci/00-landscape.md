---
type: exploratory
status: historical_research
created: 2026-09-08
updated: 2026-09-11
confidence: medium
confidence_basis: September 8 primary documentation and local hardware inspection; the complete ci-fix acceptance experiment was not executed. Later Fusion smoke and recovery validation is linked separately.
verified_example: false
origin_prompt: prompts/00-landscape.prompt.md
---

# Windows on a Mac for ci-fix

**September 8 research recommendation:** pilot Parallels Desktop Pro with Windows 11 Pro Arm64 for local reproduction, using direct guest command execution first. Choose VMware Fusion when avoiding a hypervisor subscription is the priority. Retain the original GitHub-hosted Windows x64 job for final verification and for defects that depend on x64, Windows Server, or the hosted image.

This recommendation concerns `ci-fix`, the skill that diagnoses GitHub Actions failures and verifies changes through progressively broader checks. It was a research conclusion as of September 8, before product adoption, installation, or runner registration. Prices, product versions, and references below retain that date.

The owner later chose Fusion with a registered runner. The [decision history](DECISION.md) records that change, and the [September 11 validation record](../../../plugins/fusion-runner/docs/validation.md) covers the completed Fusion smoke and recovery work. The proposed Windows execution phase in `ci-fix` remains unimplemented.

## The machine and existing contract

Local inspection on September 8, 2026 identified a MacBook Pro with an Apple M4 Pro chip, 48 GB of memory, and macOS 26.4. Its native processor architecture is Arm64. QEMU 11.1.1 is already available as both `qemu-system-aarch64` and `qemu-system-x86_64`. The commands `prlctl`, `vmrun`, `utmctl`, and `act` did not resolve on the current PATH. That does not prove the corresponding applications are absent.

The source reviewed was commit `0a737f44cf2f2d70e76bcf0abc1532319af11afc` on `feat/ci-fix-local-first`. The [skill contract](../../../plugins/repo-hygiene/skills/ci-fix/SKILL.md) requires duration profiling before test execution, reproduction before editing, the narrowest available test first, and final verification in GitHub. Its [local reproduction reference](../../../plugins/repo-hygiene/skills/ci-fix/references/targeted-repro.md) currently excludes Windows jobs from the macOS sweep. Its [workflow inventory](../../../plugins/repo-hygiene/skills/ci-fix/scripts/workflow_inventory.py) records operating-system family but does not establish processor architecture.

A Windows VM can supply an additional local execution environment. It does not remove the skill's requirement to verify the final pushed commit in GitHub.

## What can match GitHub, and what cannot

Four architecture values must remain separate:

| Value | Meaning | Example on this Mac |
|---|---|---|
| Host architecture | Processor architecture of the physical Mac | Arm64 |
| Guest architecture | Processor architecture targeted by the Windows operating system | Arm64 for a virtualized Windows 11 guest |
| Process architecture | Architecture of the interpreter, compiler, or test executable | Arm64 natively, or x64 under Windows application emulation |
| Artifact target | Architecture for which a build produces its output | An x64 executable produced by an Arm64 compiler |

Virtualization lets a guest use the host's matching processor architecture. Whole-machine emulation translates a different processor architecture. Windows application emulation instead runs x64 or x86 user programs within an Arm64 Windows operating system. These mechanisms provide different evidence.

Microsoft documents x86 and x64 application emulation in Windows 11 on Arm. Kernel components still require Arm64 builds. An x64 Python process running under emulation therefore does not turn the guest into an x64 Windows machine. [Microsoft: application emulation](https://learn.microsoft.com/en-us/windows/arm/apps-on-arm-x86-emulation).

GitHub's current image list maps `windows-latest` to Windows Server 2025 on x64. `windows-2022` is another x64 image. Windows 11 Arm64 uses separate labels, including `windows-11-arm`. The current hosted-runner reference lists Windows Arm64 for both public and private repositories. [Runner image list](https://github.com/actions/runner-images), [hosted-runner specifications](https://docs.github.com/en/actions/reference/runners/github-hosted-runners).

**For an existing failure, the failed run's image version and software-manifest link take precedence over today's meaning of `windows-latest`.** Image labels and installed software change. Even an explicit operating-system label does not freeze the entire tool image.

The following are proposed routing rules, not measured coverage claims:

| Failure depends on | Useful local environment | What its result establishes |
|---|---|---|
| Windows paths, file locking, subprocess behavior, or shell syntax | Windows 11 Arm64, with the same tool version and a checkout on its own filesystem | Can reproduce the specific Windows failure if it occurs unchanged |
| An x64 interpreter or native package | The exact x64 runtime inside Windows on Arm, if all dependencies work | Evidence under emulation; original x64 CI remains necessary |
| Arm64 compilation or dependencies | Native Arm64 guest tools | Appropriate local architecture; hosted image and environment still differ |
| Windows Server features, an x64 driver, instruction behavior, or a particular hosted image | Original hosted x64 job; remote x64 Windows machine if interactive investigation is needed | Avoids treating an Arm result as equivalent evidence |
| GitHub permissions, event context, caches, artifacts, or action setup | A GitHub-connected diagnostic job | Directly rerunning a test command does not exercise the Actions control plane |

For example, a test that mishandles a Windows path can fail identically in the local guest and in CI. A package that downloads different binaries for Arm64 and x64 can fail for an entirely different reason locally. Both are Windows failures, but only the first reproduction necessarily tests the same defect.

## Candidate comparison

Prices below are US dollar observations from September 8, 2026. Windows licensing is separate from virtualization software. Effort assessments are analytical judgments, not timing measurements.

| Candidate | Windows environment on this M4 Mac | Automation and maintenance | Cost observed | Assessment |
|---|---|---|---|---|
| **Parallels Desktop Pro 27** | Windows 11 Arm64; x64 applications through Windows emulation | Documented guest execution, VM cloning, snapshots, and lifecycle commands; paid support | $119.99/year displayed comparison price; $65.99/year advertised promotion | Preferred pilot for agent-driven local reproduction |
| **VMware Fusion, 25H2 feature baseline** | Windows 11 Arm64; no x64 guest virtualization on Apple Silicon | `vmrun`, REST API, snapshots, clones; community support under free offering | Free for personal, educational, and commercial use | Strongest alternative when subscription cost matters |
| **UTM 4.7.5** | Windows Arm64 virtualization through QEMU; whole-machine x64 emulation also possible | `utmctl`, AppleScript bridge, and QEMU guest agent; more integration work | Free direct download; $9.99 US Mac App Store listing | Good open-source option, especially for command-line tests |
| **Direct QEMU 11.1.1, installed locally** | Arm64 virtualization or x64 software emulation, depending on configuration | Full machine and guest-agent protocols; firmware, virtual hardware, storage, and lifecycle integration must be assembled | No QEMU purchase required | Flexible but unnecessarily much initial work for this skill |
| **Parallels x86 emulator preview** | Whole x64 Windows machine emulation, subject to the documented version limits | Shares Parallels controls but has significant guest limitations | Requires Pro or higher in the documented preview | Specialist experiment, not the normal fix loop |
| **Original GitHub-hosted Windows job** | Actual selected x64 or Arm64 hosted environment | Existing workflow, logs, and check results; no local VM administration | Standard public-repository runners free; private usage subject to allowance and rates | Required verification path and preferred fallback |

Evidence: [Parallels requirements](https://kb.parallels.com/en/124223), [Parallels pricing](https://www.parallels.com/products/desktop/buy/), [Fusion feature matrix](https://knowledge.broadcom.com/external/article/315609), [Fusion free-use announcement](https://blogs.vmware.com/cloud-foundation/2024/11/11/vmware-fusion-and-workstation-are-now-free-for-all-users/), [UTM release](https://github.com/utmapp/UTM/releases/tag/v4.7.5), [UTM installation and pricing model](https://docs.getutm.app/installation/macos/), [UTM App Store listing](https://apps.apple.com/us/app/utm-virtual-machines/id1538878817?mt=12), [UTM architecture support](https://mac.getutm.app/), [Parallels x86 preview](https://kb.parallels.com/en/130217), [GitHub billing](https://docs.github.com/en/billing/concepts/product-billing/github-actions).

### Why Parallels Pro leads

The current Parallels requirements explicitly cover macOS Tahoe 26 and Apple Silicon. Pro includes the command-line tools needed to automate a development VM. `prlctl`, its VM management utility, supports cloning and snapshot operations. `prlctl exec`, its guest command interface, requires Parallels Tools inside Windows and provides explicit user-selection options. [System requirements](https://kb.parallels.com/en/124223), [CLI edition requirements](https://docs.parallels.com/landing/parallels-desktop-developers-guide/command-line-interface-utility), [guest execution](https://docs.parallels.com/landing/parallels-desktop-developers-guide/command-line-interface-utility/manage-virtual-machines-from-cli/general-virtual-machine-management/execute-a-command-in-a-virtual-machine).

That is a close fit for repeatedly starting an environment, running one test, collecting its result, and restoring the environment. Standard's desktop capabilities are useful, but the documented CLI is a Pro-or-higher feature. The recommendation is based on integration fit; no speed advantage over Fusion or UTM was measured.

Parallels also publishes a DevOps Service and a GitHub Action for controlling VMs. The action documents operations for pulling an image, executing commands, and deleting a VM. These are useful existing components if the scope grows into a runner service. A service endpoint, credentials, and machine management would add unnecessary components to the initial local-command pilot. [Parallels GitHub Action](https://github.com/Parallels/parallels-desktop-github-action), [DevOps Service](https://github.com/Parallels/prl-devops-service).

### Why Fusion remains a credible alternative

Fusion 25H2 added macOS Tahoe host support. Its versioned feature matrix lists snapshots, clones, REST API, and `vmrun` on Apple Silicon. It also lists no Windows shared-folder support for that configuration. A Windows-local checkout avoids depending on that feature. Broadcom's free offering does not include the former paid troubleshooting support for new users. [25H2 release announcement](https://blogs.vmware.com/cloud-foundation/2025/10/14/vmware-workstation-fusion-25h2-embracing-calendar-versioning-and-new-features/), [feature matrix](https://knowledge.broadcom.com/external/article/315609), [support model](https://blogs.vmware.com/cloud-foundation/2024/11/11/vmware-fusion-and-workstation-are-now-free-for-all-users/).

There is a documentation conflict: Broadcom article 315602 describes early Arm guest limitations, including unavailable `vmrun` functionality, while article 315609 lists support across later versions. Use the versioned matrix for feature availability. Do not infer from its single `vmrun` row that every guest operation has reliable exit-status and cancellation behavior. The pilot must test those operations. An SSH connection to Windows is a possible transport fallback, subject to its own setup and verification. [Earlier limitations](https://knowledge.broadcom.com/external/article/315602).

### UTM and direct QEMU

UTM can virtualize Arm64 Windows and emulate x64 machines. Its Windows guests do not have hardware 3D acceleration, which matters for graphics-sensitive tests. The scripting interface can execute guest programs and capture output through the QEMU guest agent. That makes UTM a real automation candidate, not just a manual desktop option. [Architecture and graphics support](https://mac.getutm.app/), [guest scripting reference](https://docs.getutm.app/scripting/reference/).

UTM's 4.7.5 release notes include fixes for VM start/stop failures and macOS 26 automation. They explicitly require the corrected build 118 after an earlier build could prevent VMs starting. The Windows installation guide also records a Windows 11 24H2 graphics-driver issue. Pin the tested UTM build and guest-tools version, and evaluate the warning against the actual Windows release selected. [Release notes](https://github.com/utmapp/UTM/releases/tag/v4.7.5), [Windows guide](https://docs.getutm.app/guides/windows/).

Direct QEMU exposes `guest-exec` and `guest-exec-status`, the guest-agent operations for starting a program and retrieving its completion status and captured output. Those interfaces are useful building blocks. They do not supply a complete Windows image or a ready-made `ci-fix` integration. [QEMU guest-agent protocol](https://www.qemu.org/docs/master/interop/qemu-ga-ref.html).

### Whole-machine x64 emulation

It is inaccurate to say that an x64 Windows guest is impossible on Apple Silicon. Both QEMU and Parallels' documented preview provide software emulation. Parallels describes severe performance limitations, a single virtual CPU limitation, and TPM limitations affecting newer Windows 11 builds. Its published boot estimate is 2–7 minutes; that is a vendor observation, not a measurement on this Mac. The preview documentation and the current Parallels product generation are not fully aligned, so availability must be checked for the installed edition and version. [Parallels emulator limitations](https://kb.parallels.com/en/130217).

Whole-machine emulation may help a very narrow x64 investigation when remote access is unavailable. It does not promise the timing, hardware behavior, or preinstalled software of a hosted x64 runner. Prefer the original x64 job for ordinary verification.

## Running a command, a workflow, or a registered runner

| Mode | What runs | What it adds | Recommended role |
|---|---|---|---|
| Direct command in the guest | The failed test or build command with its prerequisites | Windows execution without GitHub runner registration | Default local reproduction |
| `act` inside Windows | Locally interpreted workflow steps | Some action and workflow setup behavior | Optional diagnostic tool after checking its limitations |
| GitHub runner inside the guest | Jobs assigned by GitHub to a self-hosted runner | Real Actions orchestration, action execution, and GitHub logs | Use when the failure depends on Actions behavior |

`act`, the local Actions execution tool, documents Windows host execution through `-self-hosted` when act itself runs inside Windows. Mapping `windows-latest` while running on macOS does not install or boot Windows. Its unsupported-functionality list includes ignored job timeouts, incomplete GitHub context, ignored permissions, and unimplemented run-step cancellation. An independent timeout and cleanup mechanism would therefore be mandatory for this skill. [act runner modes](https://nektosact.com/usage/runners.html), [act limitations](https://nektosact.com/not_supported.html).

GitHub's self-hosted reference lists Windows Arm64 in public preview. The currently inspected runner release, v2.337.0, includes a Windows Arm64 distribution. This is separate from hosted Arm64 image availability. GitHub requires Linux for Docker container actions and service containers, so a Windows VM does not supply those GitHub job features. [Self-hosted support](https://docs.github.com/en/actions/reference/runners/self-hosted-runners), [runner release](https://github.com/actions/runner/releases/tag/v2.337.0).

The runner application executes assigned jobs. It does not automatically install GitHub's collection of compilers, SDKs, runtimes, browsers, and tools. Those remain part of the guest image or job setup. [Self-hosted responsibilities](https://docs.github.com/en/actions/concepts/runners/self-hosted-runners?platform=windows).

### Action and runtime compatibility

No failed workflow or dependency versions were supplied. The table describes the checked support surfaces and the validation still required for a particular job.

| Component | Current documented behavior | Implication for reproduction |
|---|---|---|
| GitHub-provided actions, including checkout | GitHub documents its actions as compatible with hosted Arm64 runners | Check the repository's actual pinned action and minimum runner version; this is not proof of a local image |
| `actions/setup-python` | Its current README supports `x86`, `x64`, and `arm64`; the default follows host OS architecture | Pin interpreter architecture as well as version; a move to Arm can change selected packages |
| `actions/setup-node` | Its current README defaults to system architecture and documents a minimum runner version of 2.327.1 for its Node 24 transition | The action runtime and the Node runtime used by tests are separate prerequisites |
| `actions/setup-go` | Its current README exposes an architecture input with automatic detection by default | Preserve the downloaded Go architecture and build target separately |
| Rust, native Python extensions, Node native modules, and external programs | A guest does not establish availability of the project's required target binaries, SDKs, or libraries | Probe the exact compiler/runtime and dependency set before declaring the job runnable |

Sources: [hosted Arm64 action compatibility](https://docs.github.com/en/actions/reference/runners/github-hosted-runners), [setup-python](https://github.com/actions/setup-python), [setup-node](https://github.com/actions/setup-node), [setup-go](https://github.com/actions/setup-go).

A concrete example: a workflow using Python 3.13 without an explicit architecture gets an x64 interpreter on an x64 runner. Running the same setup action on Arm64 can select Arm64 instead. For an x64-package failure, preserve x64 if Windows emulation supports that dependency set, and label the result as emulated. Do not silently replace it with native Arm64 and call the original failure resolved.

## Image strategy

**Start with a small Windows image containing the failed job's pinned prerequisites.** Microsoft publishes a Windows 11 Arm64 ISO; its current download page identifies version 25H2 and explicitly supports VM installation on supported hardware. Old instructions requiring an Insider VHDX are unnecessary for this route. [Official Arm64 installation media](https://www.microsoft.com/en-us/software-download/windows11arm64).

GitHub's `runner-images` repository provides software inventories and image-building definitions. The documented Windows build path uses Packer and an Azure subscription, creates temporary infrastructure, provisions a VM, and produces an Azure image. The inspected official material does not offer a supported Parallels, Fusion, or UTM Windows runner disk download. This is a bounded finding, not a claim that no third-party image exists. [Official image build procedure](https://github.com/actions/runner-images/blob/main/docs/create-image-and-azure-resources.md).

Adapting that full build to a local hypervisor means maintaining a different builder, guest drivers, firmware, installation assumptions, and many unrelated tools. Building an x64 image also does not make it virtualizable on an Arm64 host. Use the failed run's software manifest to identify the tools that matter; pursue full-image reproduction only if evidence shows the image itself is responsible.

Proposed initial resources for this 48 GB Mac are 4 virtual CPUs, 16 GB of guest memory, and a 128 GB dynamically growing virtual disk. These are pilot settings, not vendor minima, a benchmark, or a guarantee that every toolchain fits. Check free host storage before allocation. Large Visual Studio workloads may require more storage. Keep cold boot, dependency setup, and test execution timings separate.

The source checkout should live on the guest's Windows filesystem, such as its NTFS system volume. A Mac shared folder changes the filesystem under test. Start from the exact failing Git commit, preserve Git attributes and checkout settings, and import the candidate change explicitly. For uncommitted work, record the base commit and the exact patch or file-manifest hash, including intended untracked files.

## Automation requirements for the pilot

The following sequence is proposed and has not been executed:

1. Select an identified, powered-off baseline that contains no repository credentials. Restore it or create a disposable clone within the available Windows license entitlement.
2. Start the guest and wait for a bounded guest-readiness probe. A VM power state alone is insufficient.
3. Transfer source into the guest filesystem and verify the selected commit or patch manifest.
4. Record the environment and run the narrowest reproduction command under the intended Windows account and shell.
5. Export stdout, stderr, exit status, elapsed time, and test artifacts to the host before restoring or discarding state.
6. On timeout, terminate the guest process tree. If that cannot be confirmed, stop the disposable guest and record cleanup failure. Treat host interruption as requiring recovery before another run.

The products provide different building blocks:

| Requirement | Parallels Pro | Fusion | UTM/QEMU |
|---|---|---|---|
| Identify and manage VM state | `prlctl` list/status/power commands | `vmrun` and REST API; validate exact installed operations | `utmctl` and UTM scripting; QEMU machine-control interfaces |
| Restore a clean environment | `prlctl clone`; `prlctl snapshot-switch` | Documented snapshots and clones | Guest-independent disposable image strategy; validate UTM operations before relying on unattended reset |
| Run and capture a guest command | `prlctl exec` with Parallels Tools | Verify the specific guest operation; SSH is an alternative transport | Guest scripting with QEMU guest agent, including captured output and exit status |
| Transfer files | Explicit guest transfer or guest-local Git checkout | Guest-local checkout or SSH file transfer | UTM guest file operations or guest-local checkout |
| Cancel reliably | Guest process control plus independent VM stop fallback | Same requirement | Same requirement |

Sources: [Parallels CLI](https://docs.parallels.com/landing/parallels-desktop-developers-guide/command-line-interface-utility), [cloning](https://docs.parallels.com/landing/parallels-desktop-developers-guide/command-line-interface-utility/manage-virtual-machines-from-cli/general-virtual-machine-management/clone-a-virtual-machine), [snapshot restoration](https://docs.parallels.com/landing/parallels-desktop-developers-guide/command-line-interface-utility/manage-virtual-machines-from-cli/snapshot-management/reverting-to-a-snapshot), [Fusion matrix](https://knowledge.broadcom.com/external/article/315609), [UTM scripting](https://docs.getutm.app/scripting/reference/).

The Parallels command below illustrates the guest-execution seam after installation. `ci-fix-win11-arm64` is a proposed VM name, not an existing machine. The executable must first be located in the installed Parallels application. This is documentation-derived and **not a tested recipe**:

```text
prlctl exec "ci-fix-win11-arm64" cmd.exe /d /c "exit 7"
```

The pilot must demonstrate that an intentional guest exit code of 7 becomes a recorded failure on the Mac. Repeat with exit code 0 and distinct stdout/stderr messages. Also confirm the Windows execution account. A successful transport call alone is not a successful test.

Killing the host-side CLI or SSH process does not establish that Windows descendants have stopped. A Windows Job Object can manage associated processes together and terminate them when its final handle closes. A future implementation could use that mechanism, with VM termination as the fallback for escaped or unresponsive processes. Neither behavior has been tested here. [Microsoft Job Objects](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects).

### When GitHub registration is needed

A diagnostic job could select `[self-hosted, Windows, ARM64, ci-fix-local]` through `runs-on`, the workflow key that chooses its runner. The first labels describe the runner; `ci-fix-local` would be a new custom label. Labels route jobs and are not an access-control boundary. Registration also does not redirect an existing `windows-latest` job automatically. [Runner labels and groups](https://docs.github.com/en/actions/how-tos/manage-runners/self-hosted-runners/use-in-a-workflow).

Use a dedicated diagnostic workflow and scoped runner access for trusted work. GitHub warns against exposing self-hosted machines to public-fork pull-request code. For a personal Mac, disable guest access to host home folders, shared credentials, clipboard contents, and forwarded authentication agents. Permit the networking required for the selected job without exposing a new public management service. [Adding runners and public-repository warning](https://docs.github.com/en/actions/how-tos/manage-runners/self-hosted-runners/add-runners).

An ephemeral runner processes one job and is then deregistered. VM erasure is a separate responsibility. Export logs, confirm deregistration, remove credential-bearing guest state, and restore or discard the VM. Never restore a baseline containing a registered runner identity. [Ephemeral runner behavior](https://docs.github.com/en/actions/reference/runners/self-hosted-runners), [runner credential persistence](https://github.com/actions/runner/blob/main/docs/design/auth.md).

## Costs and purchasing implications

A new Windows 11 Pro license is listed at **$199.99** in the US Microsoft Store. Microsoft says a unique license is needed for each Windows Pro instance and that Pro product keys are architecture agnostic. Existing valid entitlements may change the incremental cost. Windows media availability does not supply a license. [Windows Pro price](https://www.microsoft.com/en-us/d/windows-11-pro/dg7gmgf0d8h4), [Microsoft licensing note](https://support.microsoft.com/en-us/windows/experience/platform-variants/options-for-using-windows-11-with-mac-computers-with-apple-m1-m2-and-m3-chips).

The live Parallels page showed Pro at **$65.99/year on promotion**, alongside **$119.99/year**, and Standard at $54.99/year alongside $99.99/year. Use the Pro comparison price for ongoing budgeting. Promotion duration, renewal terms, and taxes were not established from a purchase checkout. No purchase was made. [Parallels price page](https://www.parallels.com/products/desktop/buy/).

GitHub currently documents self-hosted runner usage as free. Its earlier announcement of a new self-hosted charge was explicitly postponed. Standard hosted Windows x64 and Arm64 usage beyond included private-repository allowances is listed at **$0.010 per minute**. At that rate, 1,000 billable minutes cost $10 before storage or other charges. Standard public-repository runners remain free. [Current billing](https://docs.github.com/en/billing/concepts/product-billing/github-actions), [postponed change](https://github.blog/changelog/2025-12-16-coming-soon-simpler-pricing-and-a-better-experience-for-github-actions/), [runner rates](https://docs.github.com/en/billing/reference/actions-runner-pricing).

The case for a local VM is a faster and more interactive debugging cycle. This research does not establish financial savings or faster test execution. For occasional failures, using the existing hosted runner can be the lowest-effort choice.

## Proposed changes to ci-fix

These changes are recommendations for a later implementation:

1. Discover execution environments separately from the physical host. A configured Windows VM can make a targeted Windows check available locally.
2. Add architecture and image evidence to inventory and reproduction records. Unknown values remain unknown rather than being inferred from the word Windows.
3. Preserve the failed job's shell, working directory, tool versions, environment, and process architecture when mapping its command into the guest.
4. Record the result's scope: local Windows Arm64, x64 under emulation, or the actual hosted job. Do not let a local Arm pass satisfy an x64 CI requirement.
5. Keep the existing duration profile and narrow-test rules. Measure VM startup and guest execution separately; do not use a hosted median as a measured local runtime.
6. Add Windows jobs to the local sweep only when their prerequisites and resource bounds are established. Preserve the existing final GitHub verification requirement.

The first acceptance experiment should use one known Windows failure. Reproduce the unchanged failure, apply the intended fix, and deliberately reintroduce the defect to show that the check can distinguish it. Separately test nonzero exit propagation, timeout with a child process, interrupted transport, exported logs, and clean restoration. Finally verify the same candidate commit on the original GitHub runner. **This complete `ci-fix` acceptance experiment was not executed during the September 8 research.** The separate Fusion validation covers only its [documented smoke and restore/recovery checks](../../../plugins/fusion-runner/docs/validation.md).

## Evidence limits and conclusion

Confidence is high in the architecture distinction, current documented product features, and observed prices. Confidence in the proposed `ci-fix` automation path was medium: the September 8 research did not execute its complete failure/fix/control and cleanup experiment. The later Fusion validation establishes only the smoke and restore/recovery checks linked above. Exact package availability, workload duration, Windows licensing already owned, and free disk space are unresolved inputs for the pilot.

Microsoft's Mac support article still names M1–M3 and older Parallels versions. The M4 and macOS 26 compatibility conclusion comes from current Parallels requirements, not an assumption that the older Microsoft page covers every newer model. Broadcom's versioned matrix also takes precedence over its earlier generic Arm limitations. These documentation differences should remain visible when selecting an installed version.

The original September 8 recommendation was a **Parallels Pro and Windows 11 Arm64 pilot using direct commands**, or **Fusion if avoiding a subscription was preferred**. The [subsequent owner choice](DECISION.md) selected Fusion with a registered runner. Add GitHub registration only for failures that need real Actions orchestration. Keep x64 and hosted-image verification in GitHub.

## Source inventory

All linked primary sources were retrieved on September 8, 2026. Key versioned or dated sources are listed here to support later refreshes; links at the associated claims identify the exact supporting pages.

| Publisher | Source and version/date | Used for |
|---|---|---|
| GitHub | Runner image list and hosted/self-hosted runner references, current pages | Architecture, labels, runner behavior, container restrictions |
| GitHub | `actions/runner` v2.337.0 | Windows Arm64 distribution |
| GitHub | `setup-python`, `setup-node`, `setup-go`, current READMEs | Runtime architecture selection and runner prerequisites |
| GitHub | Runner image build procedure, current page | Azure/Packer image construction |
| GitHub | Current billing/rate pages; updated December 16, 2025 announcement | Usage costs and postponed self-hosted charge |
| Microsoft | Windows 11 Arm64 download, 25H2 | Supported installation-media route |
| Microsoft | Windows Pro store and Mac support article, current pages | License cost and per-instance requirement |
| Microsoft | Application emulation, updated November 7, 2025; Job Objects, updated July 14, 2025 | Architecture and process-control boundaries |
| Parallels | Desktop 27 requirements, reviewed August 25, 2026; live price page | Host compatibility, editions, and prices |
| Parallels | CLI developer guide, current pages | Guest execution, clones, snapshots |
| Parallels | x86 emulator article, reviewed March 1, 2026 | Whole-machine emulation limits |
| Broadcom | Fusion 25H2 announcement, October 14, 2025; articles 315609 and 315602 | Host support, versioned capabilities, documentation conflict |
| Broadcom | Free-use announcement, November 11, 2024 | Hypervisor price and support model |
| UTM | v4.7.5 release/build 118; scripting and Windows guides; installation and store pages | Automation, current fixes, guest constraints, costs |
| QEMU | Guest Agent Protocol Reference; local binaries report 11.1.1 | Guest process interface and installed tooling |
| nektos/act | Runners and Unsupported functionality, current pages | Native-host execution and workflow-emulation limits |

The [reusable reference](../../reference/windows-ci-on-apple-silicon-2026-09-08.md) turns this research into a proposed execution contract. The [decision record](DECISION.md) preserves the recommendation and ranked alternatives.
