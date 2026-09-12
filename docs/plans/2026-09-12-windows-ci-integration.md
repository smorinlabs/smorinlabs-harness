# Windows execution and reset delivery

The owner approved Windows work and explicit restoration of a clean working VM.
This delivery uses the existing Windows 11 Arm64 VM on one Apple Silicon Mac.
The public integration is PR #68, based on public main at `02ace8a`.

## Current contract

`ci-fix` discovers a configured Fusion runner and dispatches trusted, pushed
source through GitHub Actions. The diagnostic supplements required CI. Fusion
setup/run owns Windows access, fresh one-job registration, retirement and
explicit reset. Starting Windows preserves its disk; retiring a one-job runner
does not restore the disk.

Public skills contain reusable instructions and secret-free lifecycle helpers.
An optional private provider supplies the owner's image, credentials and
protected transport. If it is absent, setup explains that fact and loads the
separate manual create-your-own-runner reference. The public package must remain
usable without access to a private repository.

Dispatch and collection bind repository, workflow, source SHA, invocation,
runner identity, native architecture and selected tests. A failing test retains
verified evidence and can be safely retired. An unknown or active job cannot.
Empty execution is rejected. Registration, job verdict and reset are separate
facts, each requiring its own evidence.

## Owner decisions, 2026-09-12

- Keep ordinary Windows reboot and signed-out SSH/SFTP access. This passed on
  the prepared working VM. Fusion GUI startup on an unlocked Mac is the
  supported observed route; a zero `vmrun start` exit alone is insufficient.
- Remove P47-TS05 persistent GitHub registration after reboot from this delivery.
  It is neither passed nor deferred. Each diagnostic uses a fresh one-job runner.
- Remove fresh Windows installation, formerly private R03, with no deferred
  obligation. A future Windows refresh would be a separate request.
- Use a fresh official, checksum-verified runner distribution for every elevated
  registration. Never elevate retained programs writable by a prior CI job.
- Preserve the baseline and the designated working VM. The approved obsolete
  original VM was removed. During reset, retain the previous working copy until
  its replacement passes before removing that exact obsolete copy.
- Reserve one run → marker → reset → marker absent → run acceptance for an
  independent fresh agent session. Two earlier full downloaded restores already
  passed; do not repeat another full restore in the implementation session.
- After that acceptance, finish review, merge, release and install. Authorization
  is already given; the acceptance result is the remaining sequencing gate.

Intel Windows x64, another-Mac recovery and unattended locked-Mac startup are
outside current acceptance. Reusable architecture checks still apply.

## Implementation and acceptance

- [x] P45 diagnostic discovery, dispatch, collection and bounded observations.
- [x] R02 failure evidence, partial identity receipts and guarded cleanup.
- [x] P47-T10 bounded VM power-state polling.
- [x] P45-T23 fresh verified programs, protected parent permissions, runtime guard
  and redirected-path refusal during retirement.
- [x] Progressive public manual setup and explicit reset instructions, with the
  private image/credential provider kept separate.
- [x] GUI startup and ordinary signed-out Windows reboot/access.
- [x] Record all native failure → repair → success and no-selection cleanup results.
- [x] Final changed-source checks, generated metadata and private fresh-session handoff prepared for the reviewed commit/push delivery.
- [ ] Fresh agent follows the skills to run work, reset and run again.
- [ ] Complete PR review, merge, tagged release and installation after acceptance.

Current observations and their limits belong in
[the validation record](../validation/windows-integration.md). Earlier offline
skill scenarios remain historical evidence; they do not replace the fresh
agent's actual reset acceptance.

## Registration trust boundary

GitHub service configuration grants its standard CI account write access to the
runner installation. Retirement preserves those job files. The
[PR #68 finding](https://github.com/smorinlabs/smorinlabs-harness/pull/68#discussion_r3995475242)
therefore required new trusted programs before another administrator invocation.

The helper now verifies the official native release archive digest and extracts
it into a previously unused invocation directory. Only administrators and SYSTEM
can create or replace directories under the protected parent. The CI account can
read and traverse that parent so its service can start. Older installations are
never used for elevated configuration. Reparse paths are refused during owned
registration-file cleanup.

This addresses retained job-modified programs in the trusted-job workflow. An
actively compromised or uncertain guest requires a clean baseline before further
administrator maintenance. Fresh runner programs alone do not establish a clean
Windows system.

## CLI and release checks

Retain the existing minimal CLI tier and CLI Design Standard 1.4.14. Bound
network requests, downloads and observations. Preserve identity receipts before
mutation, distinct exit outcomes, explicit mutation scope and no credential
arguments or environment dumps. Verify the changed source and generated
manifests before pushing; refresh review and CI after the last push.
