# Helper review scope

CLI Design Standard **1.4.14**, small-CLI profile, **minimal tier**. Review
record: initial Fusion runner plugin, 2026-09-08; helper contract corrections
rechecked 2026-09-12. These are bounded skill
helpers: one host probe and three operations on one VM. A standalone CLI with
multiple resource types would require a new interface review.

The [interface](docs/cli-interface.md) records flags, output, exit codes, and
error codes. Tests cover information commands, JSON aliases, unambiguous flags,
explicit shutdown consent, and uncertain or hostile inputs. This is a minimal
helper review, not a claim of the publishable-tier Appendix C audit.

| Applicable area | Evidence |
|---|---|
| R1.4, Appendix A: bounded command naming | `probe`; `status`, `start`, `stop`; descriptive single-file helper names |
| R3.1, R3.3, R3.10: argument parsing | argparse with prefix abbreviation disabled; `--` ends flags and permits only the action operand after it |
| Minimal-tier R4.1, R4.2 | Help/version aliases and `-o json`/`--json` parity |
| R5.5, R5.6 | No credential argument or credential store; vendor error output is not echoed |
| R6.1, R7.1, R7.8, R7.9 | Documented exit codes, result/error stream split, JSON runtime errors, help on bare invocation |
| R8.1, R8.2 | Shutdown guard plus interactive confirmation or explicit `--yes`; noninteractive refusal |
| R8.6 | Dry run observes power and exposes the plan without mutating it |
| R7.2, R9.3 | Host probe 1.0.0 / schema 2 explicitly version the rename to `expected_windows_architecture`; VM power 0.2.0 adds optional total-deadline polling without changing the default single observation |
| Bounded waiting | Four delayed/stuck transition fixtures prove one mutation and a deadline covering the initial inventory and all polls |

N/A: persistent configuration and config discovery, network authentication,
pagination, remote waiting, caching, plugins, updates, and streaming. The full
standard-tier verbosity/configuration options are outside the minimal-tier
helper scope. No telemetry is collected.

SHOULD choices: R3.2 stdin `-` is inapplicable to VM/executable resource
identities; R7.8 usage errors retain argparse's human usage, while runtime
errors are JSON when requested. These choices are part of the initial helper
interface review, not changes to the shared standard.

Fixture tests establish helper behavior. They do not establish vmrun support
for a particular Fusion build, encrypted VM boot, guest shutdown completion,
Windows service behavior, or execution of a GitHub Actions job.

The protected PowerShell adapters use structured stdin and durable local
receipts. They are internal administrative operations rather than standalone
minimal-tier CLIs. Parser and source-derived fixture checks are separate from
Windows service runtime validation; the latter remains explicitly recorded in
the current validation plan.
