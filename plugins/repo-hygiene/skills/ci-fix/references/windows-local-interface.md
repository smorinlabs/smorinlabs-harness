# Local Windows helper interface review

CLI Design Standard 1.4.14, small-helper profile, minimal tier. The 2026-09-14
addition coordinates one captured local invocation; it is not a general remote
shell, service manager or persistent runner. This records interface scope, not a
publishable-tier Appendix C audit. The full contract and usage are in
[local Windows execution](windows-local.md).

| Applicable rule area | Interface and evidence |
| --- | --- |
| R1.4, Appendix A | Explicit `plan`, `run`, `collect` actions; one invocation receipt |
| R3.1, R3.3, R3.10 | Argparse, no long-option abbreviation; resolved file and skill-directory inputs |
| Minimal R4.1, R4.2 | Bare help; `--help`/`-h`; `--version`/`-V`; `--output`/`-o json` and `--json` |
| R5.5, R5.6 | Credentials stay in the owner-only access file and hidden SSH prompt; no secret flags or environment transport |
| R6.1, R7.1, R7.8 | Results on stdout, runtime errors on stderr; JSON error envelope; exits 0/1/2/5/130 |
| R8.1, R8.2, R8.6 | `--yes` for execution; no prompts; `--no-input`; plan/dry-run observes without guest mutation |
| R10.4 | Host intent before execution; durable guest result; collect never retries execution; process timeout and uncertain SSH completion remain distinct |
| R7.2, R9.3 | Helper 0.1.0, specification/cost/snapshot/receipt schema version 1 |

R3.2 stdin `-` is supported for one non-credential JSON input. The access file
needs local ownership/mode verification; receipt and ledger need durable paths.
Those three accept no stdin/stdout sentinel. Usage errors retain argparse's
human-readable usage; runtime errors support JSON. These are explicit small-helper
interface choices, not changes to the shared standard.

No credential discovery, public image download, telemetry, workflow dispatch,
GitHub runner registration, automatic guest cleanup or automatic shutdown occurs.
Fusion owns network transport and power. The existing workflow inventory, scope
ladder and timing ledger remain the sources for selection and compatible history.

Behavioral checks cover no-Windows/no-probe, actual worktree bytes, deletion and
exclusion handling, stale source, malformed or missing evidence, exact selection,
account/architecture mismatch, cold/warm costs and no duplicate execution.
Native Windows acceptance is recorded separately; fixture success does not prove
that a machine's access, toolchain or startup is ready.
