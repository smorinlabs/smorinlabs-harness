# Research prompt: Windows on this Mac for ci-fix

Prepared: 2026-09-08. Trigger: architecture and tool selection. Mode: user-authorized research. Companion provenance: `00-landscape.framing.md`.

## Purpose

Recommend a practical way to reproduce GitHub Actions Windows failures on this Apple Silicon Mac and use that evidence within the existing `ci-fix` verification ladder. Resolve the choice, including a ranked runner-up and explicit fallback conditions. Produce implementation-ready research guidance, but do not implement or install anything.

Exact scope: local Windows virtualization or emulation, self-hosted GitHub Actions runners, fidelity to GitHub-hosted Windows environments, setup, cost, limitations, automation, and the resulting recommendation for ci-fix. Consider remote Windows only as the fallback when local reproduction cannot answer the failure being investigated. Do not expand into a general cloud-provider survey.

## Established constraints

- Hardware verified on 2026-09-08: MacBook Pro `Mac16,7`, Apple M4 Pro, 48 GB RAM, macOS 26.4, native `arm64` host architecture.
- QEMU executables resolve at `/opt/homebrew/bin/qemu-system-x86_64` and `/opt/homebrew/bin/qemu-system-aarch64`. `prlctl`, `vmrun`, `utmctl`, and `act` do not resolve on the current PATH. Do not infer installed applications or working guests from these facts.
- Repository: `smorinlabs/smorinlabs-harness (ci-fix research worktree)`, branch `feat/ci-fix-local-first`, source commit `0a737f44cf2f2d70e76bcf0abc1532319af11afc`.
- Relevant contract: `plugins/repo-hygiene/skills/ci-fix/SKILL.md` and `references/targeted-repro.md`. The skill measures successful CI durations first, reproduces before editing, runs the narrowest target, preserves the failed command's wrapper and environment, and requires final GitHub CI verification. Its current macOS sweep excludes Windows and self-hosted runner families. Inventory records operating-system family but does not establish runner or process architecture.
- Representative test ecosystems: Python/pytest, JavaScript/Jest/Vitest, Rust/Cargo/nextest, and Go. No specific failed workflow or tool versions have been supplied. Do not imply blanket support.
- There is no declared Windows license, vendor preference, or spend budget. Treat costs as comparison inputs. The current task authorizes research artifacts, not purchasing, downloads, installation, provisioning, runner registration, CI dispatch, skill edits, or paid execution.

## Questions to answer

### 1. Separate the problems before selecting a product

Distinguish these modes: execute the exact failed command in Windows; execute selected workflow steps locally; register the Windows guest as a self-hosted GitHub Actions runner. Explain what additional fidelity and operational burden each mode adds.

Define and separately track host CPU architecture, guest OS architecture, running process architecture, and build artifact target architecture. Distinguish native Arm64 virtualization, x64 application emulation inside Windows on Arm, and whole-machine x64 emulation. Explain why these do not establish equivalent evidence for every failure.

Compare the Windows kernel and OS edition, CPU architecture, installed tools, shell behavior, filesystem checkout, environment variables, service dependencies, and GitHub execution context. Use a concrete example of an OS-only defect and an architecture-dependent defect to show when local evidence transfers and when it does not.

Verify the current meaning of `windows-latest`, explicit Windows x64 labels, and Windows Arm64 labels. Check public/private repository availability and preview versus general availability. The failed run's logged image version and software manifest must outrank the current moving label when reproducing an older failure.

### 2. Compare the bounded candidate field

Evaluate Parallels Desktop, VMware Fusion, UTM with QEMU, and direct QEMU. For each establish the current release, supported host versions, guest architectures, Windows version and license requirements, installation and maintenance effort, documented automation, and actual cost. Identify paid editions required for automation separately from base desktop pricing.

Check any current Parallels x86 emulator or technology preview explicitly. Do not claim that x64 Windows guests are categorically impossible on Apple Silicon without considering software emulation. State documented limits and whether they defeat useful CI reproduction. For VMware, prefer a versioned feature matrix when an older limitations page conflicts with it; call out the conflict and resolution.

Evaluate `act` only for the part it actually supplies. Explain whether its native-host execution can run inside a Windows guest, what its workflow emulation omits, and why mapping a Windows label to macOS or a Linux Docker container does not create Windows. Keep Docker actions, job containers, and service-container support tied to the operating system GitHub actually supports.

For each candidate report: precise use-case fit; maintenance and compatibility evidence; a recent regression or limitation that changes this plan, if any; integration cost; vendor-supported versus community-supported status; confidence and its basis. Popularity may be a secondary signal, never a substitute for fit.

### 3. Establish runner and action compatibility independently

Verify current self-hosted Windows Arm64 and x64 runner support using GitHub documentation and current runner release assets. Static REST examples may be stale. Distinguish preview support from stable support.

Check representative versions of `actions/checkout`, `actions/setup-python`, `actions/setup-node`, and `actions/setup-go`, plus the relevant runtime and compiler distributions. Consider native extensions, architecture-selection defaults, Node-based action runtimes, Rust targets and toolchains, emulated x64 binaries, and dependencies without Arm64 builds. Pin claims to the examined version or manifest. Missing compatibility evidence remains unresolved, not silently supported.

Explain how labels and groups route a self-hosted job, how the guest stays online only for authorized work, and how repository registration differs from fully local command execution. Do not propose persistent runner exposure as a prerequisite for every local reproduction.

### 4. Resolve the image strategy

Determine whether GitHub publishes downloadable Windows VM disk images suitable for local use, image-building source only, or another supported artifact. Read the current build instructions and templates before answering. Determine their infrastructure dependencies and architecture assumptions.

Compare a minimal Windows guest with pinned job prerequisites against adapting the GitHub image build definitions. Explain what each preserves, what it omits, update effort, storage requirements, Windows licensing, and why installing the Actions runner alone does not reproduce GitHub's tool image.

Give a small environment manifest suitable for a future ci-fix implementation: source commit, failed CI job and image version, OS edition/build, all relevant architectures, shell and tool versions, action pins when actions are exercised, guest image identifier, and reproduction command. This is a proposed data contract, not a code change.

### 5. Establish an automation and cleanup contract

For leading candidates, cite exact supported APIs or command families for finding a VM, starting it, waiting for guest readiness, transferring source, running a command, capturing stdout/stderr and exit status, cancelling a timed-out run and its descendants, collecting logs, stopping the guest, and restoring or discarding its state. Separate lifecycle control from guest command execution. Identify guest tools, OpenSSH, WinRM, or other prerequisites and licensing gates.

Describe a future bounded-run flow that clones or restores a known baseline, checks out the selected Git commit inside the guest filesystem, records the environment, runs one narrow target, exports evidence, and cleans up on success, failure, timeout, and host interruption. Do not invent measured boot or test durations. Distinguish vendor minima, proposed resource allocations, and measured resource usage.

For a registered runner, separate GitHub deregistration, guest process termination, credential removal, and VM cleanup. Ephemeral registration alone is not evidence that the guest was erased. Address private-repository credentials and untrusted pull-request code because the VM runs on a personal Mac: consider host shares, clipboard, forwarded agents, network access, snapshots containing credentials, and token persistence. State practical isolation boundaries without inventing extra approval flows.

### 6. Fit the result into ci-fix

Recommend a default local path, a ranked runner-up, and an x64 or image-sensitive fallback. State the conditions under which each wins. Decide whether direct guest command execution should precede self-hosted registration and explain why.

Identify the minimum proposed changes to `ci-fix` concepts and inventory needed to use this environment correctly. Preserve duration profiling, reproduction-before-editing, narrow execution, explicit unavailable reasons, bounded waits, neighbor verification, and final GitHub CI validation. A Windows Arm64 pass must not be reported as an x64 CI pass. An environment setup failure must not be reported as a test pass.

Include a small decision table keyed by the failed job's OS, CPU and toolchain dependencies. End with a bounded empirical pilot that could be authorized later: one failure reproduced unchanged, one corrected run, one deliberately broken control, one timeout/cleanup check, and the corresponding hosted verification. Do not execute the pilot during this research.

## Evidence and output rules

- Research current state as of 2026-09-08. Use official vendor documentation, GitHub documentation, project source, release notes, and issue reports from the actual project. Primary sources only for technical conclusions. Cite exact URLs next to claims.
- For rapidly changing labels, versions, prices, preview status, or compatibility, record retrieval date and relevant source version or commit. Compare source publication dates with the underlying event. Do not present future-dated announcements as already effective.
- Resolve contradictory sources explicitly. Prefer a current versioned source over an unversioned or obsolete limitation when that preference is justified. If unresolved, make the recommendation conditional or defer that leaf.
- State actual prices and units in USD with edition, billing period, taxes if material, and date. Separate hypervisor, Windows license, maintenance, and GitHub usage costs. Verify current self-hosted billing rather than relying on an announcement or historical assumption. Do not infer performance or monetary savings without measured workload data.
- Use the research tree's landscape, decision, and reusable reference artifacts as required by guided-research. Lead with the recommendation, then a comparison table and the exact-use-case guidance. Keep research findings distinct from proposed skill changes.
- Mark every command recipe and operational sequence as documentation-derived and empirically untested unless it was actually executed in this task. No Windows guest, runner, action, benchmark, or cleanup experiment is authorized here. A terminal leaf may be complete as researched guidance while its pilot remains explicitly unrun.
- Stop when an actionable conditional choice and a precise reference for this use case exist. Name remaining owner decisions such as product purchase only after research has narrowed them; do not ask clarification questions already answered by these constraints.
