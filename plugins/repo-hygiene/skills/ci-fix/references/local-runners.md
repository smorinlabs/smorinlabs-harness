# Local Linux runners — reproducing an `ubuntu-*` job off CI

A job whose `runs-on` this host cannot satisfy is not automatically *not
reproducible locally*. A container runtime or a Linux VM already on the
machine can run the step's command, which turns a CI-only failure back into
a rung-0 and rung-1 failure — the cheap end of the ladder.

**A runner changes the execution environment; scope follows the shared
validation contract.** Reproduce selected failures, then verify affected
behavior. A full step needs a reason. A complete compatible bundle measured
at approximately 30 seconds or less runs directly. `--local-env container`
keeps the first-run cost estimate at twice the CI step median until a compatible
local sample exists; this estimate is not a measurement of the complete bundle.
Include setup costs and relevant architecture/toolchain differences explicitly.

## 1. Survey first — use what is already here

```bash
python3 <skill-dir>/scripts/detect_runners.py            # writes ~/.config/ci-fix/runners.toml
python3 <skill-dir>/scripts/detect_runners.py --refresh  # survey again
```

Read-only: it starts nothing, pulls nothing, installs nothing. The file ranks
by **what is on the machine, and what is already on disk**:

1. **Installed beats absent.** Starting a stopped runner is one command;
   installing one is a download. Anything present outranks anything not.
2. **An image or VM on disk beats a fetch.** Between two installed runners,
   the one already holding bytes can begin now while the other downloads
   first — so a stopped lima with a VM outranks a running but empty podman.
   Both pay about the same to become useful; the one holding the bytes wins.
3. **Then the order: podman, lima, docker.** podman is the easiest — rootless,
   no licence, the same CLI as docker. lima is next, and is the right answer
   whenever the job needs a full VM rather than a shared kernel. docker
   follows both.

`preference` is that ranking. `ready` is the subset usable with no start at
all, so the report can say whether the recommendation costs a boot.

| Field | Use |
|---|---|
| `preference` | installed runners, best first; empty means nothing is installed |
| `ready` | the subset needing no start; empty means the recommendation costs a boot |
| `recommended` | the one to use, its readiness, and the reason to quote in the report |
| `recommend_start` | present when the recommendation is not running: the one command that makes it so |
| `recommend_install` | nothing installed at all: the easiest thing to get for this host |
| `runners.<name>.images` | images (or lima VMs) already on disk — the tiebreak above |
| `pinned` | the owner's own choice, honoured over the ranking and kept across `--refresh` |
| `pinned_unavailable` | a pin that is not ready, with the command that would start it |
| `host.arch_note` | non-empty when this host is not CI's `x86_64` |

act sits above the runtimes in that order but is a driver, not a peer: it is
only ready when a runtime is. Respect the current session's authority. For a start, install, pull or pin
outside that scope, present the concrete action once with its cost and reason.
Record a decline so it is not asked again. Existing authorization is not lost
when `pr-merge-flow` delegates the repair.

## 2. Pick the runner for *this* failure

| The failure is in | Use | Because |
|---|---|---|
| a test or a lint rule | the recommended container runtime | it runs the step's own command and starts in seconds |
| the workflow itself — a `uses:` step, `if:`, matrix, or an action's inputs | `act` | it replays the job as GitHub would; nothing else runs `uses:` steps |
| something that needs a real machine — systemd, kernel modules, privileged mounts | lima | a container shares the host kernel; a VM does not |

`act` is worth its first-run image pull only for the second row. For the
first row it is a slower way to get the same red.

## 3. The recipes

`<image>` comes from the failing step's toolchain, read from the inventory's
`setup` steps (`workflow_inventory.py`), never guessed. The table gives
example image families; select the actual job's version/architecture and verify
needed tools. A convenient image with a different toolchain is not CI parity:

| Toolchain in the job | Image |
|---|---|
| `astral-sh/setup-uv`, `uv`, `pip` | `ghcr.io/astral-sh/uv:python3.12-bookworm` |
| `actions/setup-node`, `npm`, `pnpm` | `node:22-bookworm` |
| `dtolnay/rust-toolchain`, `cargo` | `rust:1-bookworm` |
| `actions/setup-go`, `go` | `golang:1-bookworm` |
| none recognised | `ubuntu:24.04`, and say in the report that the toolchain is installed by the step itself |

**Not the `-slim` variants.** A slim image carries the toolchain and almost
nothing else — `git` in particular — while a GitHub runner has a full
toolbox. Measured 2026-09-10: `ghcr.io/astral-sh/uv:python3.12-bookworm-slim`
failed this repo's own pytest step with `Git executable not found`, because a
dependency resolves from a repository; the non-slim image ran the same step
green. A step that fails for a missing tool has not reproduced anything, so
when a container red names a tool rather than the code, add the tool or move
up an image before believing the red.

### Container runtime (podman or docker — same flags)

```bash
# run the selected reproducer/affected command; full scope only when justified
podman run --rm -v "$PWD:/w" -w /w <image> sh -lc '<the command>'
```

Mount read-write only when the step writes (a build cache, a lockfile); add
`--network=none` when the step should not reach the network, which turns a
"works locally, fails in CI" network dependency into a local red. Match CI's
architecture when the host differs (`host.arch_note` non-empty):
`--platform linux/amd64`. Emulated runs are slower — that is a reason to
record the observed duration, not a reason to skip them.

### act — the whole job, as GitHub would run it

```bash
act -j <job-id> -W .github/workflows/<file> --container-architecture linux/amd64
```

`<job-id>` is the workflow's job **key**, not the display name. On Apple
Silicon the architecture flag is effectively required; without it many actions
fail for reasons that have nothing to do with the code. The first run pulls
`catthehacker/ubuntu:act-latest`, 1 to 2 GB — bound that run at 5 minutes at
least, and say in the report that the first run paid for the image.

### lima — a full Linux VM

```bash
limactl start <vm>                                   # ask first; a boot is a mutation
limactl copy -r . <vm>:/tmp/repo                     # do not assume a writable mount
limactl shell <vm> sh -lc 'cd /tmp/repo && <the command>'
```

`limactl copy` rather than the VM's mount: a Lima VM may mount the home
directory read-only, and a step that writes would then fail for the wrong
reason. Some VMs are `protected: true`; leave those alone and use a scratch
VM (`limactl start --name ci-fix template://ubuntu`) rather than the owner's.

## 4. Bounds, and what to record

- **First run in an existing runner**: bound at 2 × the CI step median, floor
  5 minutes — the image pull dominates and is not in CI's number.
- **Creating a VM that does not exist yet**: bound at 10 minutes. Measured
  2026-09-10, a fresh `template://ubuntu` VM took 367s to download and boot
  before running anything, so the 5-minute floor would have expired on a
  healthy run. Say in the report that the wait was VM creation, not the step.
- **After that**: compatible ledger samples estimate cost. Record verified
  successes with `local_ledger.py record --context <execution-context.json>`;
  include runner/image, architecture, toolchain, command and selected scope.
  A host sample cannot stand in for a different container environment.
- The report names the runner, its readiness reason, and the architecture:
  `rung 1 in podman (already running), linux/amd64 emulated, 3m40s, recorded`.

Measured on an arm64 Mac against this repo's own CI, 2026-09-10, as the
orders of magnitude to expect:

| Run | Time | Against |
|---|---|---|
| first container run, image pull included | 30s | — |
| whole pytest step in a container, warm, native arm64 | 38s | 16s for the same job in CI |
| the same tests emulated to `linux/amd64` | 6× the native time | — |
| creating a fresh lima VM: image download and boot | 367s | one-off, before any step runs |
| whole pytest step inside that VM, once up | 27s | 38s in the container |

The VM beat the container on the step itself (23s of test time against 34s),
which is worth knowing before assuming a container is always the faster
choice on Apple Silicon: the VM runs a native-arch kernel, while the
container shares the host's through a translation layer. What the VM costs
is the one-off creation, and a VM that already exists does not pay it.

The container is roughly twice the CI job's own time before emulation, which
is why an untested step is estimated at 2 × the CI median; the estimate is
deliberately replaced by the first recorded run, and on this repo the real
number (38s) exceeded the 18s guess. These historical step timings estimate
cost; the current scope rule requires the measured complete bundle before
using its 30-second shortcut.

**Containers run as root.** Anything that depends on file permissions, a
non-root user, or `sudo` behaves differently: this repo has a test that skips
under root because an unreadable file cannot be simulated. A green in a
container with a skip is not the same green CI reported; the report names the
skip.

## 5. When there is still no local path

`preference` empty and the owner declined the start or the install → the job
is *not reproducible on this host*, `CI is the lab`, and the remote rules in
SKILL.md step 6 take over. Say which runner would have worked and what it
would have cost, so the choice is visible rather than a silent fallback.

macOS and Windows jobs stay not reproducible unless the host matches: a Linux
container cannot run them, and Windows has its own path (a self-hosted runner
VM), which is not this file's subject.
