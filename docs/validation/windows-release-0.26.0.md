# Windows release candidate validation

The v0.26.0 candidate passed its local release gates on 2026-09-13 UTC.
It contains Fusion 0.3.0 and repo-hygiene 0.14.0. Review and GitHub CI must
be refreshed on the final pushed revision before merge and tag publication.

| Gate | Observed result |
| --- | --- |
| Native skill acceptance | Four Windows assertions passed before and after a local baseline reset on separate standard-account runners; marker and earlier runner state were absent after reset |
| Preservation | Every baseline file and disk dependency matched, clone inodes were separate, the baseline was rehashed unchanged, and the obsolete predecessor was removed after acceptance |
| Final Windows state | Both one-job registrations retired; no runner services or processes remained; Windows shut down gracefully |
| Complete local release tests | 305 passed, zero skipped, in 50.46 seconds; PowerShell 7.6.6 executed the host-side PowerShell controls |
| Generated manifests | Current for marketplace 0.26.0, Fusion 0.3.0 and repo-hygiene 0.14.0 |
| Content and documentation | Setup, operation, diagnostics and private-provider responsibilities remain distinct; skill pages, README entries and relative links verified |
| Public boundary | Changed public files passed personal-path, private-repository, private-tooling and rendered-placeholder checks; raw native records remain private |
| Claude Code 2.1.269 | Both plugins passed session-backed skill loading; existing ignored `_generated` metadata remains a static warning |
| Codex 0.145.0 | Both plugins passed static manifest validation and session-backed skill loading |

The [curated acceptance receipt](windows-acceptance-2026-09-13.json) retains
public source hashes and observed outcomes. Full runner identities, job URLs,
protected access records and VM assets are held by the separate private provider.
Loading verifies discovery; the actual Windows run/reset/run supplies the
instruction-following evidence.

Fresh Windows installation and persistent-runner reboot testing were removed
from this delivery. This acceptance covers the existing Windows 11 Arm64 VM on
one Apple Silicon Mac. Intel Fusion, another Mac and unattended locked-host
startup remain outside its scope.
