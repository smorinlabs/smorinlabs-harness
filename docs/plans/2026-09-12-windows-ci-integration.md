# Windows diagnostic integration and recovery closeout

Authorized by Steve: “All right, complete all of this.” Scope includes the
previously enumerated R02, P45, P47-TS05, R03, polling, tracking, release, and
public worktree cleanup. Source starts at public `02ace8a` and private `26f4fa6`.

## Contract

`ci-fix` will discover a configured Fusion Windows runner and dispatch a trusted
diagnostic job through GitHub Actions. This requires pushed code. It is distinct
from host/Linux reproduction and never replaces applicable required CI.
Fusion setup/run owns the VM, protected guest access, registration, and shutdown.
First live coverage uses one-job Arm64 registrations on the existing Mac.
Persistent, locked-host, Intel, and another-Mac coverage remain separately evidenced.

The public handoff remains secret-free. A registration intent and guest receipt
preserve identity even if configuration succeeds but subsequent transport fails.
Read-only survey distinguishes missing registration, stopped VM, offline, busy,
incompatible and ready. Dispatch binds repository, workflow, revision, invocation,
runner labels and expected runner identity. Collection binds run/job/report to
those facts and distinguishes failure, environment failure, and no selection.
Boot/queue/execution/collection have bounded waits. Cleanup requires current proof
that the exact job ended and no new work can be admitted; it does not require a
passing test. Unknown or active states preserve the machine and diagnostic evidence.

## Delivery checklist

- [x] R02 implementation: partial registration receipt, failure evidence, guarded cleanup, fixture tests. Live acceptance remains below.
- [x] P45 implementation: discovery, dispatch/collection, public one-job lifecycle, documentation. Live acceptance remains below.
- [x] P47-T10: optional bounded power-state polling with one total deadline.
- [ ] Live Windows red → repair → green, plus no-selection and failure cleanup.
- [ ] P47-TS05: persistent reboot and locked-host observations on this Mac.
- [ ] P47-TS05: Intel Windows x64 and independent recovery on another Mac.
- [ ] R03: supported prerequisite bootstrap and fresh-VM validation.
- [x] Fresh Claude/Codex loading and six-case behavioral checks; content/CLI quality gates.
- [ ] PR delivery and review, tagged harness release, tracker reconciliation.
- [x] Repoint four Fusion skill placements to main; remove the merged PR #57 worktree and local branch. The unmerged integration checkout remains.

## Resource constraints observed before implementation

The host has approximately 23 GiB free and no separate writable data volume.
Additional Intel/cross-Mac hardware and access have been requested. Existing VM
archives, working VMs, unrelated audit files, and private recovery worktrees are
preserved. A hardware-dependent check is not complete merely because fixtures pass.

The locked-host probe returned zero but three later inventories showed no
running VM. Locked startup therefore remains unsupported. New Windows diagnostic,
persistent-service and fresh-bootstrap commands have not been executed in the
guest. No merge or tagged-release completion is claimed while their acceptance
gates remain open. [Implementation validation](../validation/windows-integration.md)
records the local and fresh-session results separately.

## CLI review

CLI Design Standard 1.4.14. Retain the existing minimal tier for bounded helpers;
new diagnostic helpers add network requests, local receipts and bounded waiting.
No credential flags or environment dumps. Machine output, exit distinctions,
dry-run, explicit mutation scope, help/version and no flag abbreviation apply.
