---
name: fusion-runner-setup
description: Install VMware Fusion and Windows on an Apple Silicon or Intel Mac, then provision a GitHub Actions self-hosted runner. Use when the user says "set up a Windows runner on my Mac", "install Fusion for CI", or "prepare a Fusion runner VM". Not for starting, checking, or stopping an already configured runner VM (fusion-runner-run).
allowed-tools: Read, Write, Bash, WebFetch, WebSearch, AskUserQuestion
---

# Set up a Fusion Windows runner

Prepare a Windows virtual machine (VM) in VMware Fusion that accepts authorized GitHub Actions jobs and can be powered off between uses.

## Workflow

1. **Establish the target.** Identify the Mac, VM location, GitHub repository or organization, intended workflows, and existing installations. Resolve consequential missing choices one question at a time, using a question tool when available. Carry forward authorization; do not infer permission to buy Windows, broaden repository access, or dispatch unrelated workflows.
2. **Inspect the host.** Read [installation](references/installation.md). Locate Python 3 and run `scripts/host_preflight.py probe --json` from this skill's directory. Match Windows to the physical Mac processor. Unknown hardware is not evidence for Intel. Inspect existing VMs before creating or changing one.
3. **Install Fusion and Windows.** Follow the installation reference for the detected processor. Execute available operations. Delegate necessary identity, password, license, or unavailable UI prompts with an exact surface, action, and success check. Resume afterward; never request secrets in chat.
4. **Provision the guest.** Read [runner provisioning](references/runner-provisioning.md). Install VMware Tools and the workflow's actual tools inside Windows. Verify the guest's architecture before selecting the runner asset. Use Windows storage for the runner and checkouts. Prepare any reusable baseline before GitHub registration.
5. **Register the runner service.** Apply the established scope and trusted-job policy. Configure one identity under a dedicated Windows service account. Record its exact service name and GitHub runner ID. Labels select runners; they do not restrict who can submit code.
6. **Verify and record.** Verify Windows boot, service startup, and GitHub readiness. For an authorized workflow edit and dispatch, use `templates/fusion-smoke.yml` as described in the provisioning reference. Write the secret-free [handoff](references/handoff.md) from observations. Distinguish a verified CI job from an online runner.
7. **Leave the requested power state.** After verification, shut down gracefully using the operating reference unless the user requested it stay online. Report the handoff path, VM and GitHub states, architecture, verification evidence, and anything incomplete.

## See also

- [fusion-runner-run](../fusion-runner-run/SKILL.md) — operate the configured VM without reinstalling it.
- [Operations reference](../fusion-runner-run/references/operations.md) — readiness checks, graceful shutdown, and recovery.
- [Reuse and compatibility](references/reuse-and-compatibility.md) — reuse one VM, prepare independent clones, and compare identical tests with GitHub-hosted Windows.
