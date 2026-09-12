---
name: fusion-runner-run
description: Start, inspect, or gracefully stop an existing VMware Fusion Windows VM configured as a GitHub Actions runner. Use when the user says "start my Fusion runner", "bring the Windows runner online", "check the runner VM", or "stop the Fusion runner after CI". Not for installing Fusion, Windows, or a new runner (fusion-runner-setup).
allowed-tools: Read, Write, Bash, WebFetch, AskUserQuestion
---

# Run a Fusion Windows runner

Operate one configured Windows runner VM and verify its availability to GitHub Actions separately from its power state.

## Workflow

1. **Identify the existing runner.** Read the local [handoff](../fusion-runner-setup/references/handoff.md) and [operations reference](references/operations.md). Identify the VM by its absolute `.vmx` configuration path and its recorded registration phase. A prepared but unregistered profile has no runner ID and cannot be ready. Recover missing values from Fusion, Windows, and GitHub. Resolve ambiguous identity before acting; do not create another runner.
2. **Inspect before acting.** Run `scripts/vm_power.py status --vmx PATH --json` with the observed path. Check the exact GitHub runner's connectivity and busy flag separately. A running VM can have an offline runner. Status requests remain read-only.
3. **Start when requested.** Use the helper's `start` action, or Fusion's UI for an interactive unlock. Use an existing verified guest connection for diagnostics; do not introduce another transport merely to start the VM. Wait for Windows and, when registered, the recorded service, then check GitHub. Report a prepared VM as unregistered and route deliberate new registration to setup. Report ready only when the correct runner is online and idle; report active work if busy. Never start a second listener alongside the service.
4. **Run authorized jobs.** Starting the VM enables jobs already permitted by its scope and labels. It does not authorize workflow edits or unrelated dispatches. For an authorized test, record the run and verify its runner identity and architecture.
5. **Stop when requested.** Follow the operations reference: inspect active work, establish a no-new-jobs window or verify completed ephemeral retirement, stop the exact service after jobs finish, verify GitHub is offline or the exact registration is absent, and use the helper's graceful `stop` action. If admission cannot be paused or retirement verified, leave it running unless interruption is explicitly authorized. An idle observation or expired wait does not authorize interruption. Failed-test evidence and safe retirement are independent outcomes.
6. **Close with observed state.** Report VM power, runner connectivity, relevant job, and unresolved work. For power changes, update the local handoff without treating cached status as current. Powering off preserves guest files and runner identity; it does not restore a clean image.

Use available tools for authorized work. When a necessary choice is unresolved, ask one question at a time using a question tool if available. Delegate only necessary interactive prompts, with the exact surface, action, and success check.

## See also

- [fusion-runner-setup](../fusion-runner-setup/SKILL.md) — install or deliberately reprovision a runner.
- [Operations reference](references/operations.md) — exact helper commands, service checks, and failure handling.
