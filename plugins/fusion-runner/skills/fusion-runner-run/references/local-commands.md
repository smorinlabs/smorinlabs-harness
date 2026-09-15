# Transport for local Windows commands

`ci-fix` owns selecting and capturing local source, comparing feedback costs,
and interpreting test evidence. This skill supplies the guest transport and
standard-account executor. Follow `ci-fix`'s
[local Windows reference](https://github.com/smorinlabs/smorinlabs-harness/blob/main/plugins/repo-hygiene/skills/ci-fix/references/windows-local.md)
for the execution specification and host commands.

Use the existing VM identified by its absolute VMX path. A private image/access
provider may supply a current profile and private access file; none is bundled
or required. Otherwise use setup's manual provisioning instructions to establish
OpenSSH access, a pinned server key, PowerShell 7 and the workflow's actual tools.
Use a dedicated standard Windows account. Verify the actual identity with
`whoami` and its SID. If that account lacks SSH admission, prepare a concrete
access change under the owner's authority before attempting local work. Preserve
existing firewall restrictions and maintenance access. Never promote the account
or change authentication merely to bypass an access failure.

`scripts/guest_session.py` is the internal macOS native SSH/SFTP transport.
It reads only an explicitly supplied owner-only access file. The password goes
to a hidden SSH terminal prompt, never command arguments or environment variables.
A temporary mode-0700 directory holds a pinned known-hosts file and connection
socket. There is no agent forwarding, alternate host-key acceptance, VM discovery,
installation, power change or GitHub registration in this library.

When the standard account cannot enumerate Windows services or processes,
`admission_access` in that same private file supplies an existing maintenance
account. It uses the same address, port and pinned host key with its own SID and
credential. The adapter uses that account only for a fixed read-only inventory
before execution and before accepting completed evidence. It never sends tested
source or a user-selected command to the maintenance session. The execution
account remains non-administrative. Unknown inventory blocks admission.

Prepare both accounts before image capture. Normal startup verifies the saved
access contract, automatic SSH startup and the current address. A validated
clean reset must provide access immediately without an access-repair step.

`scripts/local_job.ps1` is the internal standard-account executor. Its structured
stdin identifies one invocation, expected account/architecture, source snapshot,
specification and archive hashes. The host transfers fresh copies and verifies
the executor hash before invocation. The executor verifies source-file hashes,
uses an exclusive local-job lease, preserves separate output streams and writes
a durable result. It never elevates source code. A timed-out command gets an
attempt to terminate its own process tree; uncertain termination remains visible.

An active GitHub listener/worker or existing local command prevents local
admission. Do not register/start a GitHub runner concurrently or run arbitrary
detached services from a local test command. These controls assume trusted test
source, not a guest compromised by hostile code. Restore the verified baseline
before administrator work if guest integrity is uncertain.

Keep failed or interrupted invocation directories until results are collected
and process state is reconciled. The adapter does not delete them or stop Windows.
Before graceful shutdown, establish that owned local work ended and no new local
or GitHub work can be admitted. A zero `Runner.Worker` count alone does not prove
that a local command ended. Preserve the saved baseline and follow the separate
reset procedure only when requested.
