# Windows integration implementation validation

The new P45 diagnostic and Fusion lifecycle contracts pass local fixture and
fresh-session checks. Native Windows acceptance remains open. This record does
not extend the original plugin's three Arm64 smoke-job claims to unrun scenarios.

| Check | Observed result |
| --- | --- |
| Windows collector, Fusion Python helpers and PowerShell contract regression | 79 checks selected after review repairs; current result recorded in the repair commit's PR evidence |
| PowerShell contract details | Three parsers, four selection cases, five registration-mode cases, twelve retirement cases and four service-verification cases |
| Repository Python suite | 257 passed initially; 28 existing repo-finder tests were blocked by UV cache permissions, then all 28 passed in 19.97 seconds with a writable cache. All 285 collected tests were verified across those runs. |
| Generated manifests | Current after plugin versions became Fusion 0.3.0 and repo-hygiene 0.14.0 |
| Claude and Codex static and fresh loader checks | Both plugins loaded in both tools. Claude retains the existing ignored generated-metadata warning. The sandboxed Codex probe initially failed to execute; native isolated loader probes then passed. |
| Fresh skill-following | Both tools wrote artifacts for six independent scenarios; the artifacts were inspected against the expected action and verification states |
| Independent content/code review | No remaining substantive findings after rechecking seven repairs |
| Local links and public scrub | No missing linked files, personal absolute paths, private-tooling terms or unfilled documentation placeholders found |

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
The public PR's original implementation passed all four GitHub CI checks; its
repair commit requires a fresh check result before integration.

## Fresh-session artifact judgments

Both tools read the current three skill entrypoints and their Windows references
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

## Open acceptance gates

- P45-T23: settle and implement verified runner-code preparation before another
  elevated registration; the architectural PR #68 review thread remains open.
- P45/R02: execute an actual Windows test failure, repair the source and pass
  the same assertion on another registration; verify no-selection rejection and
  safe failure retirement.
- P47-TS05: verify the same persistent service/runner identity after reboot,
  Intel Windows x64 execution, and independent recovery on another Mac.
- Locked-host startup: the latest observation was unsuccessful despite exit 0.
  The Mac needed unlocking before the remaining local VM checks could proceed.
- R03: run the integrated prerequisite bootstrap on a fresh VM, then prove
  reboot access and a real job. Additional writable storage is needed.
- Complete PR review, integration and tagged release after the corresponding
  acceptance gates. Delivery authorization is already recorded.

The four Fusion development placements now target the stable main checkout.
The clean merged PR #57 worktree and local branch were removed. The unmerged
integration checkout, private recovery checkouts, VM data and unrelated public
audit files were preserved.
