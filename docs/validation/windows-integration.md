# Windows integration implementation validation

The Windows diagnostic implementation passed an actual failure → source repair
→ success cycle and rejection/cleanup of an empty test selection on 2026-09-12.
Ordinary signed-out Windows reboot/access also passed. A fresh agent following
the revised skills through run → reset → run remains the acceptance gate before
review, merge, release and installation finish.

The [curated native record](windows-native-2026-09-12.json) binds current public
helper hashes to allowlisted observations. Raw reports, identities and job URLs
remain in the separate private validation repository. Earlier recovery evidence
does not establish that the new reset instructions were followed.

| Check | Observed result |
| --- | --- |
| Windows collector, Fusion Python helpers and PowerShell regression | 89 tests passed in 17.26 seconds on the revised registration/retirement helpers |
| PowerShell contracts | Three parsers, four selection cases, five mode cases, fifteen retirement cases and four service-verification cases; a real-filesystem probe verifies ancestor traversal and symlink refusal |
| Full suite on earlier integration source | 257 tests passed initially; 28 existing repo-finder tests needed a writable UV cache, then passed. All 285 then-collected tests were verified across those runs. |
| Generated manifests | Current; Fusion 0.3.0 and repo-hygiene 0.14.0 |
| Current static loading | Both plugins had no errors in Claude/Codex. Claude retains the ignored generated-metadata warning; Codex static coverage is manifest-only. |
| Earlier fresh loading and offline skill scenarios | Both tools loaded the initial integration and produced inspected artifacts for the six scenarios below. These predate the revised reset instructions. |
| Independent review | No concrete blocker in the reviewed helpers, public routing or private diagnostic/reset instructions |
| Public boundary | Generic manual setup is a progressive reference. Credentials, images and protected transport stay in the optional private provider. |

Run the reproducible helper checks from the repository root with its development
Python environment. `tests/test_windows_powershell.py` finds PowerShell 7 as `pwsh`
or accepts its absolute executable path in `P45_PWSH`; it explicitly skips when
neither exists. The PowerShell regression invokes the actual current selection
and mode expressions, plus mocked retirement commands. It does not test actual
Windows services or ACL enforcement.

The reviewed defects included a one-test selection collapsing to a scalar,
omitted persistent `ephemeral: false`, hidden registration files, unique receipt
recovery, interrupted workflow restoration and protected administrative staging.
Their fixes preserve registration, test verdict and retirement as separate facts.

PR #68 review added regression controls for common secret keys, complete and
exclusive runner-label matching, first-observation reruns, truncated failure logs,
wrong-runner log preservation, stopped/wrong-path services and unmatched services
in the same installation. The failing controls were reproduced before repair.
The download follow-up reproduced a complete 25 MiB response being buffered
before truncation. Binary responses now retain at most 16 MiB plus one overflow
byte during capture. Empty, exact-limit, oversized, nonzero-exit and timeout
controls exercise real child processes; timeout and overflow both reap the child.
Logs retain the bounded prefix and an explicit truncation flag; oversized report
archives remain rejected. Binary stderr is discarded instead of buffered.
The public PR's original implementation passed all four GitHub CI checks; its
repair commit requires a fresh check result before integration.

## Fresh-session artifact judgments

Both tools read the initial integration's three skill entrypoints and their Windows references
in isolated temporary working directories. No VM or GitHub mutation was allowed.
The resulting [curated artifact matrix](windows-integration-behavior.json) retains
the action decisions and hashes of the complete artifacts.

| Case | Expected and observed decision in both tools |
| --- | --- |
| A: X64 guest for requested ARM64 diagnostic | Refuse dispatch; preserve the existing VM |
| B: Verified failing test on a retired one-job runner | Preserve verified failure; permit the requested graceful shutdown after the remaining owned-service cleanup |
| C: Ambiguous dispatch response with saved intent | Reconcile the same receipt; no duplicate dispatch or shutdown |
| D: One selected ID but zero reported tests | Reject verification; establish admission and identity evidence before cleanup |
| E: Locked-host start returns zero but inventory is empty | Readiness remains unverified; inspect actual power/unlock state |
| F: Idle persistent runner without an admission pause | Keep service and VM running until safe shutdown preconditions exist |

Both artifacts identify pushed code as required and ordinary required CI as
independent of supplemental Windows diagnostics. These are bounded offline
decision scenarios, not live service or workflow execution.

## Native Windows observations, 2026-09-12

| Scenario | Expected and observed result |
| --- | --- |
| Existing runner directory or persistent mode submitted to the registration adapter | Refused before elevated configuration |
| Fresh official runner distribution | Native Arm64 archive SHA-256 verified; new invocation directory and standard-account service |
| First service attempt lacked parent read permission | Service failed before taking a job; exact unclaimed registration was safely retired and workflow admission restored |
| Protected parent permission repair | Standard CI account can read/traverse the parent but cannot create a sibling installation; real Windows assertion passed |
| Intentionally broken Windows path extraction | One selected assertion failed on the expected source and runner; report and logs retained |
| Repaired path extraction | Same assertion passed, along with parent write denial, Unicode file round trip and native child exit status: four passing assertions |
| Unknown selected test ID | Zero executed tests rejected as `no_selection`; job/report/logs retained and exact runner retired |
| Cleanup | Failed, successful and empty-selection jobs all retired safely; owned registration files removed and working files preserved |
| Ordinary reboot/access | Same Windows identity and native tools; signed-out automatic SSH returned; stdout/stderr, child exit and SFTP hashes passed |
| Final power state | Zero registered runners, runner services and runner processes; graceful Windows shutdown verified |

The runner was version 2.337.0. Registration now requires PowerShell 7.4 or
newer in the native Core edition, downloads into an administrator-controlled
parent, verifies the official archive digest and refuses a reused installation.
Retirement refuses reparse paths before protected file operations. These controls
address retained job-modified programs. A compromised or uncertain guest must
be restored before administrator maintenance.

## Remaining acceptance and explicit exclusions

- A fresh agent must follow setup/run, `ci-fix`, and the optional private provider
  to run Windows work, create a marker, reset the designated working VM, prove
  the marker is absent and run again. The two earlier downloaded restores passed;
  no full restore was repeated during this implementation session.
- After that acceptance: refresh review and CI, merge, release and install.
  Delivery authorization is already recorded. Review comments require current
  source and evidence after the final push.
- Persistent GitHub registration after reboot, P47-TS05, is removed from this
  delivery, with no deferred obligation. Ordinary Windows reboot/access remains.
- Fresh Windows installation, formerly private R03, is removed with no deferred
  task. Use the existing prepared VM and verified baseline.
- Live acceptance covers this Mac's Windows 11 Arm64. Intel x64, another Mac and
  unattended locked-Mac startup are outside delivery. GUI startup on the
  unlocked Mac worked; a zero native start exit alone did not establish a VM.

Four installed Fusion placements still target stable main. The merged PR #57
worktree and local branch were removed, as was the specifically approved
obsolete original VM. Preserve the integration checkout, private recovery
checkouts, baseline, working VM and unrelated public audit files until the
remaining acceptance and deliberate post-merge cleanup.
