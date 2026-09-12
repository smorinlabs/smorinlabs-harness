---
decided: 2026-09-08
status: decided
adoption_status: fusion_selected_and_runtime_validated_ci_fix_integration_pending
---

# Decision: local Windows reproduction for ci-fix

## Subsequent owner choice and validation

On September 8, the owner selected VMware Fusion with a registered GitHub
runner for the future Windows execution phase in `ci-fix`. That decision is
recorded as Decision Q2 under Project P45 in [PROJECTS.md](../../../PROJECTS.md). It supersedes the
Parallels/direct-execution recommendation below for this implementation.

By September 11, the separate `fusion-runner` plugin work had completed three
Windows 11 Arm64 smoke jobs: the original VM and two independent downloaded
restores. The [validation record](../../../plugins/fusion-runner/docs/validation.md)
states the observed environment and coverage limits. The `ci-fix` Windows
execution phase remains unimplemented; smoke success does not establish its
failure/fix/broken-control, timeout, or interrupted-run recovery contract.
No Parallels purchase or pilot is recorded.

## Original research choice (September 8)

Recommend a Parallels Desktop Pro and Windows 11 Pro Arm64 pilot, using direct guest command execution. Use the original GitHub-hosted Windows job for final verification and whenever the defect requires its x64 architecture, operating-system edition, or image.

This closes the research choice. It does not record a product purchase, successful pilot, user selection of a vendor, or implemented skill change.

## Why

The Mac has an Apple M4 Pro processor and 48 GB of memory. Parallels' documented guest-execution, cloning, and snapshot interfaces fit the existing narrow local-test workflow. An Arm64 Windows guest can provide useful Windows failure evidence without being equivalent to the original hosted x64 environment. The full comparison contains the supporting primary sources and costs.

## Runner-up, ranked

1. **VMware Fusion:** first alternative if avoiding a hypervisor subscription matters, or its installed guest-control operations pass the pilot with comparable integration effort.
2. **UTM:** choose when open-source tooling is preferred and its guest-agent control and reset operations meet the same acceptance contract.
3. **Direct QEMU:** choose when exact virtual hardware or custom machine control is itself a requirement.

Remote x64 Windows is a separate correctness fallback, not a lower-ranked replacement for local Windows behavior testing.

## Why not the other approaches first

- Whole-machine x64 emulation adds substantial performance and compatibility limitations; use it only for a narrow experiment.
- `act` requires Windows underneath its Windows host mode and omits relevant workflow controls.
- Registering a GitHub runner is unnecessary for direct test commands and adds credentials, routing, and cleanup responsibilities.
- Rebuilding the entire GitHub image introduces Azure/Packer and image-maintenance work beyond the initial reproduction need.
- Parallels DevOps Service and its GitHub Action are existing expansion options if a managed runner service becomes necessary.

## Original pilot acceptance contract

The proposed pilot must establish exit-code propagation, output capture, failure/fix/broken-control behavior, timeout cleanup, interrupted-run recovery, clean reset, and the original hosted verification. The later Fusion smoke/recovery checks cover only the subset described in the validation record; this complete `ci-fix` contract remains untested.

## Chain

- [Framing](prompts/00-landscape.framing.md)
- [Research prompt](prompts/00-landscape.prompt.md)
- [Full comparison](00-landscape.md)
- [Reusable reference](../../reference/windows-ci-on-apple-silicon-2026-09-08.md)
