# Reset the designated working Windows VM

Load only for an explicit reset request. A reset restores saved disk state;
reboot and runner retirement preserve later files and are different operations.

## Choose the owner of the saved state

If an installed private recovery skill owns this VM's baseline and credentials,
read that skill and use its recorded restore procedure. Keep its repository,
asset identifiers, passwords, and machine-specific receipts private. Never copy
those into this public plugin. The public skill defines the run/reset contract;
the private skill supplies that user's assets and transport.

Without a private skill, use the user's own saved baseline and the general
[powered-off restore procedure](../../fusion-runner-setup/references/reuse-and-compatibility.md#reuse-the-same-vm).
If no baseline exists, say that a clean reset is unavailable. A new installation
is a separate choice, not a substitute performed silently. For a user who wants
to create their own runner, load the separate
[manual setup path](../../fusion-runner-setup/references/create-your-own-runner.md).

## Required sequence and evidence

1. Identify the exact working VM, unchanged baseline, all disk dependencies,
   and changes that reset will discard. Preserve requested outputs and logs.
   Honor already established reset/replacement authorization; resolve any
   newly discovered work outside that scope before replacing files.
2. Finish active jobs and verify the exact obsolete GitHub registration is
   retired. An idle runner alone is insufficient. Stop Windows gracefully,
   verify the selected VM is powered off, and close Fusion before copying.
3. Verify the baseline manifest. Restore the complete designated working copy
   using the owner's procedure, leaving the saved baseline unchanged. Keep
   any other copies of that Windows identity off. For recovery of the same
   VM, use **Moved It** if Fusion asks.
4. Verify all restored files before boot. Then verify Windows identity,
   architecture, tools, and the established maintenance connection. A marker
   deliberately created after baseline capture must be absent. Verify that
   pre-registration state has no obsolete runner registration or service.
5. For an authorized GitHub test, configure a fresh one-job runner from a new
   verified distribution and run the selected workload. Record the source
   revision, runner ID, actual result, and later safe retirement. Windows
   commands through the verified maintenance connection need no GitHub runner.

Keep only the baseline and designated working VM as the routine local set.
Remove an obsolete replacement copy only after its successor passes the
required checks and the exact deletion is authorized. Do not delete the
baseline merely because its Windows version matches the working VM.

For skill acceptance after changed routing or recovery instructions, use one
fresh-agent **run → create marker → reset → verify marker absent → run again**
cycle. This tests instruction following. It does not require a fresh Windows
installation or another full restore during the preceding implementation session.
