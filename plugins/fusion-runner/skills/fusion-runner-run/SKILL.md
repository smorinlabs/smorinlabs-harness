---
name: fusion-runner-run
description: Start, inspect, gracefully stop, or explicitly reset an existing VMware Fusion Windows VM used for GitHub Actions or Windows commands. Use for "start my Fusion runner", "check Windows access", "stop the runner after CI", or "reset the working Windows VM to its saved baseline". Reset requires an identified saved baseline. Installing Fusion, Windows, or a new runner belongs to fusion-runner-setup; fetching a private saved image belongs to the installed private recovery skill.
allowed-tools: Read, Write, Bash, WebFetch, AskUserQuestion
---

# Run a Fusion Windows runner

Operate one configured Windows runner VM and verify its availability to GitHub Actions separately from its power state.

## Workflow

1. **Identify the existing VM and access provider.** Read the local [handoff](../fusion-runner-setup/references/handoff.md) and [operations reference](references/operations.md). Identify the VM by its absolute `.vmx` path and any current GitHub runner by ID. Use an available private recovery skill for its saved configuration; keep credentials and backup identities there. If no VM/configuration is available, report that fact and load [create your own runner](../fusion-runner-setup/references/create-your-own-runner.md). A retired one-job registration does not mean Windows needs reinstalling.
2. **Inspect before acting.** Run `scripts/vm_power.py status --vmx PATH --json` with the observed path. Check the exact GitHub runner's connectivity and busy flag separately. A running VM can have an offline runner. Status requests remain read-only.
3. **Start when requested.** Use the helper's `start` action, or Fusion's UI for an interactive unlock. Verify the exact running VM and its established guest connection. If the CLI reports success but inventory stays empty, inspect Fusion and open the exact working bundle; do not keep repeating the command. Report Windows access separately from GitHub readiness. A current runner is ready only when online and idle. If its one-job registration retired, use setup's fresh verified registration procedure only when another GitHub job is authorized. Never start a second listener alongside a service.
4. **Run authorized jobs.** Starting the VM enables jobs already permitted by its scope and labels. It does not authorize workflow edits or unrelated dispatches. For an authorized test, record the run and verify its runner identity and architecture.
5. **Stop when requested.** Follow the operations reference: inspect active work, establish a no-new-jobs window or verify completed ephemeral retirement, stop the exact service after jobs finish, verify GitHub is offline or the exact registration is absent, and use the helper's graceful `stop` action. If admission cannot be paused or retirement verified, leave it running unless interruption is explicitly authorized. An idle observation or expired wait does not authorize interruption. Failed-test evidence and safe retirement are independent outcomes.
6. **Reset only when explicitly requested.** Read [reset the working VM](references/reset.md). Identify the designated working copy, saved baseline, and changes to discard. Use the installed private recovery skill when it owns those assets; otherwise follow the public powered-off restoration procedure. Preserve required results first. Reset is separate from stopping Windows or retiring a runner.
7. **Close with observed state.** Report VM power, Windows access, runner connectivity, relevant job, and unresolved work. For power changes or reset, update the local handoff from observations. Do not report reset complete from a reboot, service removal, or successful copy alone.

Use available tools for authorized work. When a necessary choice is unresolved, ask one question at a time using a question tool if available. Delegate only necessary interactive prompts, with the exact surface, action, and success check.

## See also

- [fusion-runner-setup](../fusion-runner-setup/SKILL.md) — install or deliberately reprovision a runner.
- [Operations reference](references/operations.md) — exact helper commands, service checks, and failure handling.
