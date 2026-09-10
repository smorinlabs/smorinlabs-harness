#!/usr/bin/env python3
"""detect_runners.py — what on this machine can run a Linux CI step?

A `runs-on: ubuntu-*` job that cannot run on the host is not automatically
"not reproducible locally": a container runtime or a Linux VM already on the
machine can run the step's command. This script surveys what is here and
writes `runners.toml`, which `ci-fix` reads before deciding that CI is the
only place a failure can be seen.

Two rules shape the ranking:

- **Readiness before fidelity.** Something already running costs nothing to
  use, so it is recommended over a more faithful tool that first needs an
  install, a machine, or a 1 GB image pull. Within one readiness tier the
  fidelity order applies: act (replays the whole job, `uses:` steps included)
  → podman → docker → lima. podman leads the two container runtimes because it
  is rootless, needs no licence, and takes the same CLI as docker; lima is the
  fallback, a full VM that is the most faithful Linux and the slowest to start.
- **Recommend what is here; otherwise recommend the easiest thing to get.**
  A bare machine is told to install podman, not the "best" runner: one
  formula, rootless, no licence and no GUI, and on a Linux host no virtual
  machine at all.

The survey is **read-only**. It never starts a VM or a daemon, never pulls an
image, and never installs anything; it reports the command that would, and
`ci-fix` asks before running one. Every probe is bounded (`--probe-timeout`,
default 10s) because `docker info` against a stopped Docker Desktop hangs
rather than failing.

  detect_runners.py [--out FILE] [--refresh] [--json] [--probe-timeout S]
  detect_runners.py path        → print the default config path, write nothing

Without `--refresh` a config file younger than 24 hours is left alone (the
machine rarely changes); with it, everything is probed again. A hand-written
`pinned = "podman"` in the file overrides the ranking and survives every
re-survey, so a deliberate choice is recorded once rather than re-argued. Exit 0 on a
survey, 2 on a usage error.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

SCHEMA = 1
CI_ARCH = "x86_64"  # GitHub's ubuntu-* runners
FRESH_S = 24 * 60 * 60
# Fidelity order, used only to break ties inside one readiness tier.
# podman leads the runtimes: rootless, no licence, and CLI-compatible with
# docker, so it is the cheapest thing to recommend installing as well as the
# safest default. lima is the fallback — a full VM, most faithful and slowest.
FIDELITY = ["act", "podman", "docker", "lima", "devcontainer"]
READINESS_RANK = {"ready": 0, "needs_start": 1, "absent": 2}


def host_os() -> str:
    return os.environ.get("CI_FIX_FAKE_OS") or platform.system().lower()


def host_arch() -> str:
    return os.environ.get("CI_FIX_FAKE_ARCH") or platform.machine()


def default_path() -> Path:
    base = Path(os.environ.get("XDG_CONFIG_HOME") or (Path.home() / ".config"))
    return base / "ci-fix" / "runners.toml"


PINNED_RE = re.compile(r'^\s*pinned\s*=\s*"([^"]*)"\s*$', re.MULTILINE)


def read_pinned(dest: Path) -> str:
    """A hand-written `pinned = "podman"` survives every re-survey: the machine
    changes, the owner's choice does not. Read with a regex, not a TOML parser,
    because this script must run on whatever python3 the machine has."""
    if not dest.is_file():
        return ""
    m = PINNED_RE.search(dest.read_text())
    return m.group(1) if m else ""


def probe(cmd: list[str], timeout: float) -> tuple[int, str, str]:
    """Run a read-only probe. A missing binary or a hang is 'not available'."""
    try:
        p = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout, check=False
        )
    except FileNotFoundError:
        return 127, "", "not installed"
    except subprocess.TimeoutExpired:
        return 124, "", f"probe timed out after {timeout:g}s"
    except OSError as exc:
        return 126, "", str(exc)
    return p.returncode, p.stdout.strip(), p.stderr.strip()


def absent(name: str) -> dict:
    return {
        "name": name,
        "readiness": "absent",
        "version": "",
        "arch": "",
        "detail": f"{name} is not installed",
        "start_command": "",
    }


def detect_docker(timeout: float) -> dict:
    rc, out, err = probe(
        [
            "docker",
            "info",
            "--format",
            "{{.ServerVersion}}|{{.Architecture}}|{{.OSType}}",
        ],
        timeout,
    )
    if rc == 127:
        return absent("docker")
    if rc == 0 and "|" in out:
        version, arch, ostype = (out.split("|") + ["", ""])[:3]
        return {
            "name": "docker",
            "readiness": "ready",
            "version": version,
            "arch": arch,
            "detail": f"docker {version} is running ({ostype}/{arch})",
            "start_command": "",
        }
    detail = (
        "probe timed out; the docker daemon is not answering"
        if rc == 124
        else "the docker daemon is not running"
    )
    return {
        "name": "docker",
        "readiness": "needs_start",
        "version": "",
        "arch": "",
        "detail": f"{detail} ({err.splitlines()[0] if err else 'no detail'})",
        "start_command": "open -a Docker"
        if host_os() == "darwin"
        else "sudo systemctl start docker",
    }


def detect_podman(timeout: float) -> dict:
    rc, out, err = probe(
        ["podman", "info", "--format", "{{.Version.Version}}|{{.Host.Arch}}"], timeout
    )
    if rc == 127:
        return absent("podman")
    if rc == 0 and "|" in out:
        version, arch = (out.split("|") + [""])[:2]
        return {
            "name": "podman",
            "readiness": "ready",
            "version": version,
            "arch": arch,
            "detail": f"podman {version} is running ({arch})",
            "start_command": "",
        }
    detail = "probe timed out" if rc == 124 else "no podman machine is running"
    return {
        "name": "podman",
        "readiness": "needs_start",
        "version": "",
        "arch": "",
        "detail": f"{detail} ({err.splitlines()[0] if err else 'no detail'})",
        "start_command": "podman machine start",
    }


def detect_lima(timeout: float) -> dict:
    rc, out, err = probe(["limactl", "list", "--json"], timeout)
    if rc == 127:
        return absent("lima")
    if rc != 0:
        detail = (
            "probe timed out"
            if rc == 124
            else (err.splitlines()[0] if err else "limactl failed")
        )
        return {
            "name": "lima",
            "readiness": "needs_start",
            "version": "",
            "arch": "",
            "detail": detail,
            "start_command": "limactl start template://ubuntu",
            "vms": [],
            "running_vm": None,
        }
    # `limactl list --json` is JSONL: one object per line, never an array
    vms = []
    for line in out.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            vm = json.loads(line)
        except ValueError:
            continue
        vms.append(
            {
                "name": vm.get("name", "?"),
                "status": vm.get("status", "?"),
                "arch": vm.get("arch", ""),
            }
        )
    running = next((v["name"] for v in vms if v["status"] == "Running"), None)
    if running:
        return {
            "name": "lima",
            "readiness": "ready",
            "version": "",
            "arch": next((v["arch"] for v in vms if v["name"] == running), ""),
            "detail": f"lima VM {running!r} is running",
            "start_command": "",
            "vms": vms,
            "running_vm": running,
        }
    stopped = next((v["name"] for v in vms if v["status"] != "Running"), None)
    return {
        "name": "lima",
        "readiness": "needs_start",
        "version": "",
        "arch": "",
        "detail": (
            f"{len(vms)} lima VM(s), none running"
            if vms
            else "lima is installed with no VMs"
        ),
        "start_command": f"limactl start {stopped}"
        if stopped
        else "limactl start template://ubuntu",
        "vms": vms,
        "running_vm": None,
    }


def detect_simple(name: str, args: list[str], timeout: float, needs: str) -> dict:
    rc, out, _ = probe([name, *args], timeout)
    if rc == 127:
        return absent(name)
    return {
        "name": name,
        "readiness": "needs_start",
        "version": out.splitlines()[0] if out else "",
        "arch": "",
        "detail": needs,
        "start_command": "",
    }


def survey(timeout: float) -> dict:
    runners = {
        "docker": detect_docker(timeout),
        "podman": detect_podman(timeout),
        "lima": detect_lima(timeout),
        "devcontainer": detect_simple(
            "devcontainer",
            ["--version"],
            timeout,
            "the devcontainer CLI drives a container runtime and a devcontainer.json",
        ),
        "act": detect_simple(
            "act",
            ["--version"],
            timeout,
            "act drives a container runtime; none is ready",
        ),
    }
    # act replays the whole job, but only on top of a ready runtime
    runtime_ready = any(
        runners[r]["readiness"] == "ready" for r in ("docker", "podman")
    )
    if runners["act"]["readiness"] != "absent" and runtime_ready:
        runners["act"]["readiness"] = "ready"
        runners["act"]["detail"] = "act is installed and a container runtime is running"
    return runners


def rank(runners: dict) -> list[str]:
    """Ready first; fidelity only breaks ties. devcontainer never leads alone."""
    ready = [
        n
        for n in FIDELITY
        if runners[n]["readiness"] == "ready" and n != "devcontainer"
    ]
    return ready


def recommend(runners: dict, order: list[str], os_name: str, pinned: str = "") -> dict:
    out = {"recommended": None, "recommend_start": None, "recommend_install": None}
    if pinned:
        if pinned in order:
            out["recommended"] = {
                "runner": pinned,
                "readiness": "ready",
                "reason": f"pinned in runners.toml, and {runners[pinned]['detail']}",
            }
            return out
        state = runners.get(pinned, {}).get("readiness", "absent")
        out["pinned_unavailable"] = {
            "runner": pinned,
            "readiness": state,
            "detail": runners.get(pinned, {}).get("detail", f"{pinned} is unknown"),
            "start_command": runners.get(pinned, {}).get("start_command", ""),
        }
    if order:
        top = order[0]
        out["recommended"] = {
            "runner": top,
            "readiness": "ready",
            "reason": f"{runners[top]['detail']} — already running, so a Linux step can start now "
            "with no install and no boot",
        }
        return out
    startable = [
        n
        for n in FIDELITY
        if runners[n]["readiness"] == "needs_start" and runners[n]["start_command"]
    ]
    if startable:
        # cheapest start first: a container runtime beats booting a VM
        for pick in ("podman", "docker", "lima", "act"):
            if pick in startable:
                out["recommend_start"] = {
                    "runner": pick,
                    "command": runners[pick]["start_command"],
                    "reason": f"{runners[pick]['detail']}; starting it is cheaper than installing anything new",
                }
                break
        return out
    if os_name == "linux":
        out["recommend_install"] = {
            "runner": "podman",
            "command": "sudo dnf install podman   # or: sudo apt install podman",
            "reason": "easiest on a Linux host: rootless containers run natively, with no virtual machine",
        }
    else:
        out["recommend_install"] = {
            "runner": "podman",
            "command": "brew install podman && podman machine init && podman machine start",
            "reason": "easiest to get on this host: one formula, rootless, no licence and no GUI "
            "(lima is the fallback when a full VM is genuinely needed)",
        }
    return out


def arch_note(arch: str) -> str:
    if arch in (CI_ARCH, "amd64"):
        return ""
    return (
        f"this host is {arch}; GitHub's ubuntu-* runners are {CI_ARCH}, so a green here does not prove the CI "
        f"architecture — re-run with the runtime's {CI_ARCH} emulation before concluding CI is the lab"
    )


def build(timeout: float, pinned: str = "") -> dict:
    runners = survey(timeout)
    order = rank(runners)
    os_name, arch = host_os(), host_arch()
    data = {
        "schema": SCHEMA,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),  # noqa: UP017
        "preference": order,
        "pinned": pinned,
        "host": {
            "os": os_name,
            "arch": arch,
            "ci_arch": CI_ARCH,
            "arch_note": arch_note(arch),
        },
        "runners": runners,
    }
    data.update(recommend(runners, order, os_name, pinned))
    return data


# ------------------------------------------------------------------ TOML out
# written by hand: the script must run on any python3 the machine has, and
# tomllib (3.11+) reads but never writes


def _v(value) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, list):
        return "[" + ", ".join(_v(x) for x in value) + "]"
    return json.dumps(str(value))


def render(data: dict) -> str:
    lines = [
        "# ci-fix — how this machine can run a Linux CI step.",
        "# Written by scripts/detect_runners.py; re-run it with --refresh to survey again.",
        "# Ranked by readiness before fidelity: whatever is already running wins.",
        "",
        f"schema = {data['schema']}",
        f"generated_at = {_v(data['generated_at'])}",
        f"preference = {_v(data['preference'])}",
        "",
        "# Set pinned to a runner name to always prefer it; it survives --refresh.",
        f"pinned = {_v(data.get('pinned', ''))}",
        "",
        "[host]",
    ]
    for k, v in data["host"].items():
        lines.append(f"{k} = {_v(v)}")
    for key in (
        "recommended",
        "recommend_start",
        "recommend_install",
        "pinned_unavailable",
    ):
        if data.get(key):
            lines += ["", f"[{key}]"]
            for k, v in data[key].items():
                lines.append(f"{k} = {_v(v)}")
    for name in FIDELITY:
        r = data["runners"][name]
        lines += ["", f"[runners.{name}]"]
        for k, v in r.items():
            if k == "vms":
                continue
            lines.append(f"{k} = {_v(v)}")
        for vm in r.get("vms", []):
            lines += ["", f"[[runners.{name}.vms]]"]
            for k, v in vm.items():
                lines.append(f"{k} = {_v(v)}")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("command", nargs="?", choices=["survey", "path"], default="survey")
    ap.add_argument("--out", type=Path, help=f"config file (default {default_path()})")
    ap.add_argument(
        "--refresh",
        action="store_true",
        help="survey again even when the file is fresh",
    )
    ap.add_argument(
        "--json",
        action="store_true",
        help="print the survey as JSON instead of writing the file",
    )
    ap.add_argument(
        "--probe-timeout",
        type=float,
        default=10.0,
        help="seconds per probe (default 10)",
    )
    args = ap.parse_args(argv)

    if args.command == "path":
        print(args.out or default_path())
        return 0
    if args.probe_timeout <= 0:
        print("error: --probe-timeout must be greater than 0", file=sys.stderr)
        return 2

    dest = args.out or default_path()
    if args.json:
        print(json.dumps(build(args.probe_timeout, read_pinned(dest)), indent=2))
        return 0

    if dest.is_file() and not args.refresh:
        age = datetime.now(timezone.utc).timestamp() - dest.stat().st_mtime  # noqa: UP017
        if age < FRESH_S:
            sys.stdout.write(dest.read_text())
            return 0
    dest.parent.mkdir(parents=True, exist_ok=True)
    text = render(build(args.probe_timeout, read_pinned(dest)))
    tmp = dest.with_suffix(dest.suffix + ".tmp")
    tmp.write_text(text)
    tmp.replace(dest)
    sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
