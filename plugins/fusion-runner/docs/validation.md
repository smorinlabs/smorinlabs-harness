# Fusion runner validation

The Windows 11 Arm64 smoke workload passed in a real Fusion VM and in two
independent downloaded restores by 2026-09-11. Each local job used a fresh
one-job runner service under a standard Windows account. This validates the
recorded workload and recovery procedure on one Apple Silicon Mac.

The [machine-readable summary](validation/2026-09-11-arm64.json) retains an
allowlist of environment fields and outcomes from the private evidence.
Maintainers inspected the original job reports, runner identities, archive
checks, and reboot receipts. The raw private records, job URLs, account names,
credentials, and VM files are not distributed here. This is a curated summary,
not a public CI log or a claim that the private recovery helpers ship in this
plugin. Use the [compatibility templates](../skills/fusion-runner-setup/templates/compatibility/)
to verify another installation.

## What passed

| Check | Observed result |
| --- | --- |
| Installation | Fusion 26H1u1; Windows 11 Pro 25H2, build 26200.9445; VMware Tools commands and file copies |
| Guest access | Native SSH commands, stdout/stderr, nonzero child exit status, Unicode SFTP paths, and matching transfer hashes |
| Reboot access | Original VM and both restored VMs retained administrator maintenance access after reboot with no Windows console sign-in; these reboots preceded runner registration |
| Runner execution | Three fresh ephemeral runner services executed the actual GitHub Actions workload with native Arm64 PowerShell and non-administrator job tokens |
| Independent recovery | Each restore independently downloaded and verified the complete archive and every captured VM file, lacked the later marker and registration state, then passed a fresh local job |
| State preservation | The post-capture marker survived each CI job; the preserved pre-registration baseline remained unchanged |
| Shutdown | Each one-job registration retired, its service stopped, and Windows shut down gracefully |

All three local jobs reported PowerShell 7.6.4, Git 2.55.0.windows.5, and
.NET 10.0.10. These are observed versions, not mandatory installation pins.
The public PowerShell smoke script is byte-identical to the executed script;
its SHA-256 is recorded in the summary.

The five checks exercise native Windows and runner architecture, Git checkout
of the exact commit, ordinary file reads/writes and Unicode/space-containing
paths with a ZIP round trip, C# compilation with a native Windows API, and
native child-process exit status. They do not run an application's build or
its full test suite. The historical check identifier
`windows-file-permissions-unicode-spaces-and-zip` is retained in the executed
script and reports. It does not test access-control lists or denied access;
non-administrator execution is a separate recorded environment fact.
The same script also passed the earlier 2026-09-08
GitHub-hosted Windows 11 Arm64 and Windows Server x64 comparison.

## Coverage limits

- The registered runners accepted one job each. Restarting the same persistent
  runner service after a post-registration reboot remains untested here.
  Setup still requires that check before calling another persistent runner ready.
  Persistent registration is removed from the current one-job delivery, with
  no deferred obligation; this historical limit does not create a release gate.
- Encrypted VM startup worked through Fusion with an unlocked Mac. A native
  `vmrun start ... nogui` attempt returned zero while no VM was running.
  Check actual VM power and guest readiness; unattended startup while the Mac
  is locked is not established.
- Intel Fusion, independent generalized clones, and restoration on another Mac
  were not exercised by these local cycles. Arm64 Windows is not an x64 Windows
  Server image, and the hosted comparison retains that distinction.
- Helper fixtures test the public command interface with simulated vendor
  responses. The private live recovery did not prove every public helper path
  or every setup step through a fresh agent session.

## Public package checks

`tests/test_fusion_runner_helpers.py` covers host detection, VM identity,
idempotence, malformed vendor output, timeouts, quoted paths, FIFO refusal,
and graceful-shutdown guards. Repository CI checks the generated manifests,
Python tests, Claude plugin schema, public-content scans, and marketplace
parity. The generator's existing `_generated` field produces a non-fatal
Claude warning. Static Codex manifest checks do not establish runtime skill
loading or successful skill following.

## Windows diagnostic integration

The subsequent [integration validation](../../../docs/validation/windows-integration.md)
separately records fresh verified program preparation, ordinary Windows reboot,
failure → source repair → success, and cleanup after empty selection. Its final
acceptance is a fresh agent following the skills through run → reset → run.
That instruction-following check remains open until observed; the two earlier
downloaded restores do not establish that the revised instructions were followed.
