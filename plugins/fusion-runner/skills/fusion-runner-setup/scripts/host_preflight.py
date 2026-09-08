#!/usr/bin/env python3
"""Read Mac facts without installing software or exposing hardware identifiers."""

import argparse
import json
import os
import platform
import plistlib
import shutil
import signal
import subprocess
import sys
from pathlib import Path

VERSION = "0.1.0"


def probe_value(*command):
    try:
        result = subprocess.run(
            command, capture_output=True, text=True, timeout=10, check=False
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    return result.stdout.strip() if result.returncode == 0 else None


def host_architecture(machine, arm_capable):
    # An x86_64 Python process can be Rosetta on Apple Silicon.
    if machine == "arm64" or arm_capable == "1":
        return "ARM64"
    if machine == "x86_64" and arm_capable == "0":
        return "X64"
    return None


def collect(storage, fusion_app):
    if platform.system() != "Darwin":
        raise ValueError("this probe requires macOS")
    storage = storage.expanduser().resolve(strict=True)
    if not storage.is_dir():
        raise ValueError(
            "--storage must name an existing directory on the VM's destination volume"
        )
    fusion_app = fusion_app.expanduser().resolve()
    architecture = host_architecture(
        platform.machine(), probe_value("/usr/sbin/sysctl", "-n", "hw.optional.arm64")
    )
    memory = probe_value("/usr/sbin/sysctl", "-n", "hw.memsize")
    fusion_version = None
    try:
        with (fusion_app / "Contents/Info.plist").open("rb") as handle:
            fusion_version = plistlib.load(handle).get("CFBundleShortVersionString")
    except (OSError, plistlib.InvalidFileException):
        pass
    vmrun = fusion_app / "Contents/Library/vmrun"
    return {
        "schema_version": 1,
        "host": {
            "os": "macOS",
            "version": platform.mac_ver()[0],
            "process_architecture": platform.machine(),
            "architecture": architecture,
            "memory_bytes": int(memory) if memory and memory.isdigit() else None,
        },
        "storage": {
            "path": str(storage),
            "free_bytes": shutil.disk_usage(storage).free,
        },
        "fusion": {
            "app_path": str(fusion_app),
            "installed": fusion_version is not None,
            "version": fusion_version,
            "vmrun_path": str(vmrun),
            "vmrun_executable": vmrun.is_file() and os.access(vmrun, os.X_OK),
        },
        "windows_architecture": architecture,
        "compatibility_verified": False,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Inspect Mac hardware, destination space, and Fusion installation.",
        allow_abbrev=False,
        epilog="Example: python3 host_preflight.py probe --storage . --json",
    )
    parser.add_argument("action", choices=["probe"])
    parser.add_argument("--version", "-V", action="version", version=VERSION)
    parser.add_argument(
        "--storage",
        type=Path,
        default=Path.home(),
        help="existing directory on the planned VM volume (default: home)",
    )
    parser.add_argument(
        "--fusion-app", type=Path, default=Path("/Applications/VMware Fusion.app")
    )
    parser.add_argument("--output", "-o", choices=["table", "json"], default="table")
    parser.add_argument("--json", dest="output", action="store_const", const="json")
    args_list = sys.argv[1:] if argv is None else argv
    if not args_list:
        parser.print_help()
        return 0
    args = parser.parse_args(args_list)
    try:
        facts = collect(args.storage, args.fusion_app)
    except (ValueError, OSError) as exc:
        error = {"error": {"code": "preflight_failed", "message": str(exc)}}
        print(json.dumps(error) if args.output == "json" else str(exc), file=sys.stderr)
        return 1
    if args.output == "json":
        print(json.dumps(facts, indent=2))
    else:
        print(
            f"Mac architecture: {facts['host']['architecture'] or 'unknown; resolve before choosing Windows'}"
        )
        print(f"Memory bytes: {facts['host']['memory_bytes']}")
        print(
            f"Free bytes at {facts['storage']['path']}: {facts['storage']['free_bytes']}"
        )
        print(f"Fusion version: {facts['fusion']['version'] or 'not detected'}")
        print("Version compatibility still needs the current vendor support matrix.")
    return 0


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(143))
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(130)
    except BrokenPipeError:
        sys.exit(0)
