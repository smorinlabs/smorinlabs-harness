# Create your own Windows runner

Load this reference only when the user needs setup and no suitable configured
VM or private recovery provider is available. The public plugin includes
instructions and general helpers. It supplies no Windows image, license,
personal account, password, or private backup access.

Tell the user: **No configured private recovery skill is available here. You
can prepare your own Fusion Windows runner using these setup instructions.**
Do not assume a particular private repository exists or request access to
someone else's saved VM. A private companion is optional. If an existing VM
already meets the requirements, resume it and perform only missing steps.

## Manual setup path

1. **Identify your Mac and existing software.** Run the setup skill's
   `scripts/host_preflight.py probe --json` using a resolved Python 3 executable.
   Inspect existing VMs. Apple Silicon requires Windows Arm64; Intel requires
   Windows x64. Record the exact working `.vmx` path and intended GitHub scope.
2. **Install the matching Fusion and Windows versions if missing.** Follow
   [installation](installation.md), including the official Broadcom download
   and Microsoft Windows media links. The reference contains the account,
   download, ISO boot, and Windows setup walkthrough. Any license purchase or
   new account decision belongs to the user; never assume it is authorized.
3. **Prepare Windows access and tools.** Follow
   [runner provisioning](runner-provisioning.md): verify the actual Windows
   username and architecture, install VMware Tools and the workflow's native
   tools, and establish an appropriate protected maintenance connection.
   Use your own credential storage. Keep credentials outside the public repo
   and the secret-free handoff. Verify command results and file-transfer hashes.
4. **Save your clean baseline.** Before GitHub registration, gracefully power
   off Windows and preserve the complete VM and every required disk using
   [reuse and compatibility](reuse-and-compatibility.md#reuse-the-same-vm).
   Record the baseline path and file hashes. Keep one changing working copy
   and one unchanged recovery baseline; these have different purposes.
5. **Register and test one authorized job.** Use a standard Windows service
   account and [one-job registration](runner-provisioning.md#one-job-diagnostic-registration).
   Obtain the official runner release URL and SHA-256. The helper downloads
   and verifies a fresh distribution in an unused directory; it never runs a
   previous job's programs as administrator. Record the exact GitHub runner
   ID, labels, scope, and actual job result.
6. **Record how to run and reset it.** Complete the
   [handoff](handoff.md) with your own observed paths and secret-free facts.
   Use `fusion-runner-run` for startup, access checks, graceful shutdown, and
   an explicitly requested reset. Ordinary reuse does not reinstall Windows.

The agent should carry out authorized commands when tools are available.
For a necessary human-only action, provide the exact app or URL, action, and
success check. Never ask the user to paste passwords into chat.
