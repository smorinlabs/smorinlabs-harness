# Windows release candidate validation

The v0.27.0 candidate follows the independently published v0.26.0 release.
It contains Fusion 0.3.0 and repo-hygiene 0.15.0. Current main was merged without
changing the native-tested local adapter or executor. Final merge, publication
and installation remain separate delivery steps.

| Gate | Observed result |
| --- | --- |
| Native local source | Failing unpushed source failed; its local repair passed the unchanged three assertions without a push |
| Ordinary reboot and reset | Both accounts passed signed-out reboot access; identical local source passed before and after reset, with marker absence and no SSH repair |
| Bounded failures | Timeout, empty test selection and stale-source collection could not pass |
| Timing | Full local feedback took 22.92 and 26.02 seconds; comparable remote timing was not measured |
| Integrated host checks | 447 tests passed; PowerShell 7.6.6 ran the host PowerShell controls |
| Generated manifests | Current for marketplace 0.27.0, Fusion 0.3.0 and repo-hygiene 0.15.0 |
| Content and public boundary | Public setup, operation and CI responsibilities remain distinct; credentials, images and machine-specific records remain private |
| Loaders | Claude Code and Codex loaded both plugins; Claude retains the existing ignored `_generated` metadata warning |

The [local execution receipt](windows-local-2026-09-15.json) records the current
native checks and public source hashes. The earlier
[GitHub-scheduled acceptance](windows-acceptance-2026-09-13.json) covers four
assertions before and after reset on separate one-job runners. Loader success
establishes discovery; actual Windows execution establishes native behavior.

Fresh Windows installation and persistent-runner reboot testing are excluded.
The native evidence covers the existing Windows 11 Arm64 guest on one Apple
Silicon Mac. Intel Fusion, another Mac and unattended locked-host startup were
not established. Required CI must be refreshed after the final review push.
