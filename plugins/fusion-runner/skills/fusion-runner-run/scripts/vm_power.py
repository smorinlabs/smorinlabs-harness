#!/usr/bin/env python3
"""Control one explicitly selected Fusion VM; never infer GitHub readiness."""

import argparse
import json
import os
import re
import signal
import subprocess
import sys
from pathlib import Path

VERSION = "0.1.0"
DEFAULT_VMRUN = "/Applications/VMware Fusion.app/Contents/Library/vmrun"


class Failure(Exception):
    def __init__(self, code, message, exit_code=1):
        super().__init__(message)
        self.code = code
        self.exit_code = exit_code


def regular_path(value, suffix=None, executable=False):
    path = Path(value).expanduser()
    if not path.is_absolute():
        raise Failure("invalid_path", f"use an absolute path for '{value}'", 2)
    try:
        path = path.resolve(strict=True)
    except OSError as exc:
        raise Failure("not_found", f"cannot resolve '{value}': {exc}", 3) from exc
    if not path.is_file() or (suffix and path.suffix.lower() != suffix):
        raise Failure(
            "invalid_path",
            f"'{value}' must be a regular {suffix or 'executable'} file",
            2,
        )
    if executable and not os.access(path, os.X_OK):
        raise Failure("invalid_path", f"'{value}' is not executable", 2)
    return path


def invoke(vmrun, arguments, timeout):
    try:
        result = subprocess.run(
            [str(vmrun), "-T", "fusion", *arguments],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise Failure(
            "timeout",
            "vmrun timed out; VM power may have changed; inspect Fusion before retrying",
        ) from exc
    except OSError as exc:
        raise Failure("vmrun_failed", f"could not execute vmrun: {exc}") from exc
    if result.returncode:
        # Do not echo arbitrary vendor diagnostics into an agent transcript.
        raise Failure(
            "vmrun_failed",
            f"vmrun exited {result.returncode}; inspect Fusion; an encrypted VM may require an interactive unlock",
        )
    return result.stdout


def is_running(vmrun, vmx, timeout):
    lines = invoke(vmrun, ["list"], timeout).splitlines()
    header = (
        re.fullmatch(r"Total running VMs: (\d+)", lines[0].strip()) if lines else None
    )
    paths = [line.strip() for line in lines[1:] if line.strip()]
    if not header or len(paths) != int(header.group(1)):
        raise Failure(
            "invalid_inventory",
            "unrecognized vmrun list output; inspect Fusion instead of assuming the VM is off",
        )
    if any(not Path(p).is_absolute() for p in paths):
        raise Failure("invalid_inventory", "vmrun reported a non-absolute VM path")
    return any(Path(p).resolve() == vmx for p in paths)


def execute(args):
    vmx = regular_path(args.vmx, suffix=".vmx")
    vmrun = regular_path(args.vmrun, executable=True)
    if args.action != "stop" and (args.runner_offline or args.yes):
        raise Failure(
            "invalid_options", "--runner-offline and --yes apply only to stop", 2
        )
    running = is_running(vmrun, vmx, args.timeout)
    result = {
        "schema_version": 1,
        "action": args.action,
        "vmx_path": str(vmx),
        "power_state": "running" if running else "not_running",
        "runner_state": "not_checked",
        "changed": False,
    }
    if args.action == "status":
        return result
    command = (
        ["start", str(vmx), "nogui"]
        if args.action == "start"
        else ["stop", str(vmx), "soft"]
    )
    needs_change = running != (args.action == "start")
    if args.dry_run:
        return dict(
            result,
            dry_run=True,
            planned_command=command if needs_change else [],
            validation="local paths and live power inventory only",
        )
    if not needs_change:
        return result
    if args.action == "stop":
        if not args.runner_offline:
            raise Failure(
                "runner_not_offline",
                "stop requires --runner-offline after verifying the exact runner service is stopped and GitHub reports it offline",
                5,
            )
        if not args.yes:
            if args.no_input or not sys.stdin.isatty():
                raise Failure(
                    "confirmation_required",
                    "use --yes to authorize graceful shutdown after confirming the runner is offline",
                    2,
                )
            print(
                f"Shut down '{vmx}' gracefully? [y/N] ",
                end="",
                file=sys.stderr,
                flush=True,
            )
            if sys.stdin.readline().strip().lower() not in {"y", "yes"}:
                raise Failure("cancelled", "shutdown cancelled", 5)
    invoke(vmrun, command, args.timeout)
    observed = is_running(vmrun, vmx, args.timeout)
    if observed != (args.action == "start"):
        raise Failure(
            "power_not_confirmed",
            "requested power state is not yet observed; inspect Fusion; no forced action was taken",
            5,
        )
    return dict(
        result, power_state="running" if observed else "not_running", changed=True
    )


def positive_seconds(value):
    try:
        number = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "timeout must be a positive integer in seconds"
        ) from exc
    if not 1 <= number <= 300:
        raise argparse.ArgumentTypeError(
            "timeout must be between 1 and 300 seconds per vmrun call"
        )
    return number


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Inspect or change one Fusion VM's power; GitHub readiness is checked separately.",
        allow_abbrev=False,
        epilog='Example: python3 vm_power.py status --vmx "/absolute/path/Windows.vmwarevm/Windows.vmx" --json',
    )
    parser.add_argument("action", choices=["status", "start", "stop"])
    parser.add_argument("--version", "-V", action="version", version=VERSION)
    parser.add_argument(
        "--vmx", required=True, help="absolute path to the chosen VM configuration"
    )
    parser.add_argument(
        "--vmrun", default=DEFAULT_VMRUN, help="absolute path to Fusion's vmrun"
    )
    parser.add_argument(
        "--timeout",
        type=positive_seconds,
        default=30,
        help="seconds per vmrun call, 1 to 300 (default: 30)",
    )
    parser.add_argument(
        "--runner-offline",
        action="store_true",
        help="attest that the runner service is stopped and GitHub reports it offline",
    )
    parser.add_argument(
        "--yes",
        "-y",
        action="store_true",
        help="authorize graceful shutdown without a prompt",
    )
    parser.add_argument(
        "--no-input", action="store_true", help="fail if a confirmation would be needed"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="show the planned power operation without performing it",
    )
    parser.add_argument("--output", "-o", choices=["table", "json"], default="table")
    parser.add_argument("--json", dest="output", action="store_const", const="json")
    args_list = sys.argv[1:] if argv is None else argv
    if not args_list:
        parser.print_help()
        return 0
    args = parser.parse_args(args_list)
    try:
        result = execute(args)
    except Failure as exc:
        error = {"error": {"code": exc.code, "message": str(exc)}}
        print(json.dumps(error) if args.output == "json" else str(exc), file=sys.stderr)
        return exc.exit_code
    if args.output == "json":
        print(json.dumps(result, indent=2))
    else:
        print(
            f"VM: {result['vmx_path']}\nPower: {result['power_state']}\nGitHub runner: not checked"
        )
        if result.get("dry_run"):
            print(f"Dry run: {json.dumps(result['planned_command'])}")
    return 0


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(143))
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(130)
    except BrokenPipeError:
        sys.exit(0)
