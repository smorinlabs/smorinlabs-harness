# Compare a Fusion runner with GitHub-hosted Windows

Copy these files into a trusted validation repository:

| Template | Repository destination |
| --- | --- |
| `compare-windows.yml` | `.github/workflows/compare-windows.yml` |
| `windows-smoke-job.yml` | `.github/workflows/windows-smoke-job.yml` |
| `windows-smoke.ps1` | `scripts/windows-smoke.ps1` |

Keep the shared workflow at the destination shown because the comparison
workflow references it there. Add `/artifacts/` to the repository's `.gitignore`.
Match the local labels in `compare-windows.yml` to the recorded runner. The
example uses `fusion-validation`; the setup reference uses `fusion-ci`.
For an Intel Mac, also change the local job's `expected_architecture` to `X64`
and its `ARM64` label to `X64`. Rename that job and its `report_name` to
`fusion-x64`. The two hosted comparison jobs retain their original architectures.

Publish and dispatch only within the authorized repository. The manual workflow
must exist on its default branch. Run **Compare Windows runners** with
`include_fusion` false for the hosted baseline. Enable it after the local runner
is ready, then compare all three reports from the same commit. Reboot the VM and
repeat to check unattended service startup.

Native PowerShell 7 and Git must be available to the Windows runner service.
Action revisions are pinned to the official v7.0.1 releases as checked on
2026-09-08; refresh their requirements when updating the baseline. The script
compiles C# using PowerShell's runtime. It does not require or verify a separate
Visual Studio installation or .NET SDK.

Read [reuse and compatibility](../../references/reuse-and-compatibility.md) for
the validation boundary and the difference between restarting a VM and cloning it.
