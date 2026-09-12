# Fusion runner helper interfaces

These Python 3 standard-library helpers support the skills. They are not a
background service, a VM provisioner, or a replacement for the GitHub runner.
Run them from the corresponding skill directory after resolving `python3`.

## Host probe

```bash
python3 scripts/host_preflight.py probe --storage . --json
```

`--storage` names an existing directory on the intended VM volume and defaults
to the user's home directory. `--fusion-app` overrides the default
`/Applications/VMware Fusion.app`. The probe reads hardware facts, free disk
space, and Fusion's application metadata. It does not download or install
anything. Missing or denied facts become `null`; an x86 process alone does not
establish an Intel Mac because the process could be using Rosetta.

JSON has `schema_version: 2`, `host`, `storage`, `fusion`,
`expected_windows_architecture`, and `compatibility_verified`. The expected
Windows architecture is a planning value derived from the physical Mac; this
host probe does not inspect a Windows guest. Bytes are integers.
`compatibility_verified` is false: version support still needs the current
vendor matrix. Missing Fusion is an observation, not a probe error.

## VM power

The operating skill reads `vm.vmx_path` from its local JSON handoff and supplies
that absolute path as `--vmx`. The `vmrun` path defaults to Fusion's bundled
`Contents/Library/vmrun`; `--vmrun` supports a renamed application bundle.

| Action | Effect |
|---|---|
| `status` | Read `vmrun list` and identify this VM by its resolved path |
| `start` | Start or resume this VM using `nogui`, unless it is already running |
| `stop` | Request graceful shutdown using `soft`, unless it is already absent from the running list |

`power_state` is `running` or `not_running`. Absence from `vmrun list` does
not distinguish powered off from suspended. A successful start can resume an
existing guest session; it does not establish a fresh Windows boot or reset.
Inspect Fusion when that distinction matters.

`--timeout` is seconds **per vmrun call**, from 1 to 300, default 30. A mutation
uses up to three calls: observe, request, observe. A timeout is an uncertain
outcome; it does not trigger a retry or forced shutdown. A successful command
still reports `runner_state: "not_checked"`. GitHub readiness is the skill's
separate responsibility.

`--wait-seconds` optionally sets a **total operation deadline** from 1 to 300
seconds for `start` or `stop`. It covers the initial inventory, one mutation,
and all later observations and sleeps. Each call uses the smaller of its
per-call timeout and the remaining total budget. The helper polls roughly once
per second and never repeats the mutation. Omit this flag to retain the single
post-request observation. A deadline does not establish a successful transition.

For `stop`, `--runner-offline` attests that the operator has already stopped the
exact Windows runner service and verified the GitHub runner is offline or its
exact registration is verifiably retired through current authorized API reads. This
flag does not perform those checks. `--yes` authorizes shutdown without a
prompt. Otherwise the helper confirms on an interactive stdin; `--no-input`
or a pipe requires `--yes` when a shutdown would be requested. An already-absent
VM returns an unchanged power observation without these flags or a shutdown
command; GitHub state remains unchecked. There is no force or password option.

`--dry-run` reads the actual power inventory and prints a planned operation
without changing power. It does not validate GitHub state or attest that
shutdown is safe.

JSON has `schema_version`, `action`, `vmx_path`, `power_state`,
`runner_state`, and `changed`. Dry runs add `dry_run`, `planned_command`, and
`validation`. These are observations of live state, not a durable runner record.

## Common output and failures

`--help`/`-h`, bare invocation, and `--version`/`-V` print information and exit 0.
`--output`/`-o` selects `table` or `json`; `--json` is equivalent to `-o json`.
Long flags cannot be abbreviated. `--` ends option parsing; supply all flags
before it. Only the positional action can follow it.
VM and application paths name resources, not documents to read from stdin;
`-` is not a valid path to a VM or executable.

Requested results use stdout. Runtime errors use stderr, with
`{"error":{"code":"stable_code","message":"description"}}` under JSON
output. Argument-parser errors use standard argparse usage on stderr. Exit
codes are 0 success, 1 runtime error, 2 invalid invocation or missing consent,
3 missing resource, 5 failed precondition, 130 interrupt, and 143 termination.

| Error code | Meaning |
|---|---|
| `preflight_failed` | Host or storage facts could not be collected |
| `invalid_path`, `not_found`, `invalid_options` | Resolve the stated argument before retrying |
| `invalid_inventory` | Fusion's running-VM list could not be interpreted |
| `vmrun_failed` | Fusion rejected the command; inspect its UI, including encryption prompts |
| `timeout`, `power_not_confirmed` | Power may have changed; inspect it before another mutation |
| `runner_not_offline`, `confirmation_required`, `cancelled` | No shutdown was attempted |

No helper reads credentials, registers runners, modifies workflows, performs
telemetry, or contacts a network service itself. The power helper is version
0.2.0. The host probe is version 1.0.0: its major version and JSON schema 2
replace the prototype `windows_architecture` key with
`expected_windows_architecture`, making the unverified planning value explicit.

## Protected Windows adapters

The PowerShell adapters are internal lifecycle scripts, separate from the
Python command-line interfaces above. `register_service.ps1` accepts protected
JSON on stdin, writes a durable secret-free receipt and registers one verified
standard-account service. `retire_service.ps1` accepts a current host retirement
attestation, checks guest identity/processes, deletes only the stopped matching
service and its four registration files, and preserves the working directory.
Their exact input and failure contracts are in [provisioning](../skills/fusion-runner-setup/references/runner-provisioning.md)
and [operations](../skills/fusion-runner-run/references/operations.md). They require
administrator-controlled script staging and receipt storage.
