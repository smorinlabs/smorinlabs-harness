# Windows diagnostic helper interface

`skills/ci-fix/scripts/windows_runner.py` is a Python 3 standard-library helper
for a configured Fusion Windows runner. It schedules diagnostics through GitHub
on pushed code. Fusion skills retain registration and VM lifecycle ownership.

CLI Design Standard 1.4.14, minimal tier. This interface extends the existing
bounded skill-helper pattern with authenticated GitHub requests and durable
invocation receipts. It has no credential argument or independent credential store.

| Command | Required arguments | Effect |
| --- | --- | --- |
| `survey` | `--repository`, `--handoff`, `--architecture` | Read the local profile, Fusion inventory and paginated GitHub runner list; report compatibility/readiness separately |
| `dispatch` | Survey arguments plus `--workflow`, `--ref`, `--receipt`, `--yes` | Bind a new invocation to a pushed commit and runner; save intent before one dispatch POST |
| `collect` | `--repository`, `--receipt` | Reconcile that invocation and save logs/report; validate exact job identity, attempt, revision and test coverage |

`--repository` is an exact `owner/repository` on github.com. `--architecture`
is `ARM64` or `X64`, observed inside Windows. The handoff is a local secret-free
JSON profile. `--selection` is a JSON file containing unique test IDs; omitted
or `[]` means the complete diagnostic check. A partial or empty executed
selection cannot pass. The [Windows reference](../skills/ci-fix/references/windows-runners.md)
defines the profile and workflow/report contracts.

`--gh` selects the authenticated GitHub CLI executable; `--vmrun` selects the
Fusion executable. `--timeout` sets the entire command's deadline to 1–1800
seconds, default 120. Individual GitHub requests have a 30-second maximum and
inventory a 15-second maximum, each reduced by the remaining budget. Listings
are fully paginated within a 100-page bound. API errors never prove absence.
Completed-job logs retain up to 16 MiB, with `job_log_truncated: true` when only
the beginning was saved. Report archives over 16 MiB are rejected. A log from
an unexpected runner remains diagnostic evidence but cannot verify the job.

`dispatch --dry-run` performs read-only preflight without writing a receipt or
posting a workflow. Normal dispatch needs explicit `--yes`/`-y` and a new receipt;
atomic reservation refuses concurrent reuse. An ambiguous POST is reconciled
with `collect` and the same receipt. The helper never automatically retries a POST.

Help is `--help`/`-h` or bare invocation; version is `--version`/`-V` (0.1.0).
Flags cannot be abbreviated. Results use a readable two-column stdout table by
default; `--output json`, `-o json` and `--json` select JSON. Runtime errors use
stderr, including `{"error":{"code":"stable_code","message":"description"}}`
in JSON mode. argparse usage errors remain human-readable on stderr.

| Exit | Meaning |
| --- | --- |
| 0 | Successful observation/dispatch/collection; inspect `state` for survey readiness |
| 1 | Verified failing tests, or runtime failure distinguished by stdout receipt versus stderr error |
| 2 | Invalid input, unsafe profile, existing receipt, or missing mutation authorization |
| 3 | Required executable unavailable |
| 5 | Unready runner, expired wait, no selection, or another failed precondition |
| 130 / 143 | Interrupted / terminated; retain and reconcile any saved intent |

Validated contracts include minimal-tier help/version/output, no prefix flags,
dry-run, explicit mutation scope, output/error stream separation, no credential
flags, bounded requests and complete pagination. The optional stdin `-` convention is
omitted for profile/receipt paths because dispatch needs a durable filesystem
identity; protected registration stdin belongs to the separate Windows adapter.
The fixture suite does not establish native Windows execution or hosted-image
equivalence. No telemetry is collected.
