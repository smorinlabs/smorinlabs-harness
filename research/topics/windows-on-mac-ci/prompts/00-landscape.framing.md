# Framing: Windows on an Apple Silicon Mac for ci-fix

Prepared: 2026-09-08. Status: prompt framing, not the research conclusion.

## Decision and scope

Identify the best practical Windows environment on this Mac for reproducing GitHub Actions failures and validating narrow fixes. Compare local execution of the failed command, local execution of workflow steps, and a registered self-hosted GitHub Actions runner. Determine when the original GitHub-hosted runner remains necessary.

This is architecture and tool selection. Use template 2 in `guided-research/references/templates.md`: first determine whether one product solves the exact problem, then compare candidates and recommend a conditional winner with a ranked runner-up.

The user approved research into virtualization, self-hosted runners, fidelity to GitHub-hosted runners, setup requirements, costs, limitations, and a recommendation for the `ci-fix` skill. Research does not authorize installation, VM provisioning, runner registration, workflow dispatch, paid execution, or skill edits.

## Local constraints

The main agent verified the following on 2026-09-08:

- Host: MacBook Pro, model `Mac16,7`, Apple M4 Pro, 48 GB RAM, macOS 26.4; `uname -m` reports `arm64`.
- `/opt/homebrew/bin/qemu-system-x86_64` and `/opt/homebrew/bin/qemu-system-aarch64` resolve. `prlctl`, `vmrun`, `utmctl`, and `act` do not resolve on the current PATH. Absence from PATH is not evidence that an application is uninstalled.
- Repository: `smorinlabs/smorinlabs-harness (ci-fix research worktree)`, branch `feat/ci-fix-local-first`, source commit `0a737f44cf2f2d70e76bcf0abc1532319af11afc`. No research tree or applicable ancestor `AGENTS.md`/`CLAUDE.md` existed before this task.

Read directly for this framing:

- `plugins/repo-hygiene/skills/ci-fix/SKILL.md`: measure successful CI durations before execution; reproduce before editing; enter verification at the lowest available rung; run extracted test IDs before a full step; a local pass does not establish completion; final verification requires all jobs green on the pushed commit.
- `plugins/repo-hygiene/skills/ci-fix/references/targeted-repro.md`: preserve the failed command's wrapper, toolchain, environment, and working directory. Missing environment dependencies make a job unavailable locally. The current macOS sweep excludes Windows and self-hosted runner families and skips action and installer steps.

The main agent also inspected `workflow_inventory.py`: inventory records an operating-system family but not runner or process architecture. This is a reported source finding, not a file inspected by this framing agent.

No language, repository workload, Windows license, vendor preference, or budget was specified. The skill supports pytest, Jest/Vitest, Cargo/nextest, and Go. Compare representative compatibility without claiming every version or action works.

## Light-search record and early signals

Three framing queries were issued, with primary-source restrictions in the query text:

1. `site.docs.github.com OR site:docs.github.com Windows ARM64 self hosted runners GitHub actions supported architectures`
2. `site:knowledge.broadcom.com Fusion Apple silicon Windows 11 ARM vmrun support`
3. `site:docs.getutm.app OR site:kb.parallels.com OR site:nektosact.com Windows Apple silicon automation act`

Opened the primary documentation entry points below. These signals shape the prompt; product editions, costs, release status, and operational support still need full verification.

| Primary source | Framing consequence |
|---|---|
| [GitHub runner selection](https://docs.github.com/en/actions/how-tos/write-workflows/choose-where-workflows-run/choose-the-runner-for-a-job) | Search results distinguish Windows x64 labels from Windows 11 Arm64 labels. Do not assume every Windows job targets x64, or that Windows Arm64 support remains absent. Verify public/private availability and preview status. |
| [GitHub self-hosted runner reference](https://docs.github.com/en/actions/reference/runners/self-hosted-runners) | Search results include Windows Arm64 support in public preview. Verify the English reference and actual release assets; static API examples may omit newer architectures. |
| [GitHub runner images](https://github.com/actions/runner-images) | The repository describes image source and lists Windows Server x64 separately from Windows 11 Arm64. Image source is not evidence that a ready-to-boot local VM image is distributed. |
| [act runner documentation](https://nektosact.com/usage/runners.html) | Windows execution through `-self-hosted` requires running act in that operating system. Mapping a Windows label on macOS does not provide Windows. |
| [UTM documentation](https://docs.getutm.app/) | Documents Windows support, headless operation, disposable VMs, and scripting. These are candidates to investigate, not yet a proven unattended Windows control path. |
| [Parallels developer guide](https://docs.parallels.com/landing/parallels-desktop-developers-guide) | Appropriate starting point for host control and guest execution. Confirm edition requirements and current macOS support. |
| [GitHub runner pricing](https://docs.github.com/en/billing/reference/actions-runner-pricing) | Current prices are available for the remote fallback. Report dated USD rates, billing basis, and included-minute effects rather than old multipliers. |
| [Adding self-hosted runners](https://docs.github.com/en/actions/how-tos/manage-runners/self-hosted-runners/add-runners) | Registration creates an external GitHub execution surface. Keep it separate from direct local reproduction and explain cleanup. |

## Questions most likely to change the recommendation

1. Does the defect depend on Windows behavior alone, x64 execution, or the specific Windows Server and toolchain image used by the failed job? Host CPU, guest CPU, process CPU, and artifact target are separate facts.
2. Which options virtualize Arm64 Windows and which emulate a complete x64 Windows machine? Check current Parallels x86 emulation offerings explicitly before making a categorical claim about x64 guests on Apple Silicon.
3. Can each product run a guest command with a reliable exit status, preserve logs, cancel descendants on a deadline, and restore or discard a clean VM? A lifecycle CLI alone does not prove this.
4. Do ARM-compatible runner releases also support the action versions and toolchain binaries the job invokes? Runner support and action ecosystem support are separate.
5. Is copying a Windows directory from the Mac equivalent to checking out the exact commit inside the Windows filesystem? Research path handling, links, case, permissions, and line endings.
6. Can GitHub image definitions be adapted locally at reasonable cost, or should ci-fix build a smaller pinned toolchain and retain hosted CI as the final oracle?

No Windows guest was booted. No guest command, action, runner, image build, benchmark, or cleanup path was tested. The later report must keep documented support, inference, and empirical validation separate.
