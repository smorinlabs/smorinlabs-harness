#!/usr/bin/env python3
"""local_ledger.py — how long a CI step's command takes on this machine.

ci-fix's local decisions (ladder_plan.py) key on the failed step's duration.
CI's median is only a proxy for local time, so after each full-step run on
this host (rung 1 and rung 1s) the skill records the observed seconds here;
the next fix on the same step uses the local median. Successes only, last 10
per (workflow, job, step), the same sampling rule as the CI profile.

The ledger is machine-level and never lives in the repo:
  ${XDG_CACHE_HOME:-~/.cache}/ci-fix/<owner>--<repo>.json   (from --repo)
or any explicit --ledger path.

  record  --repo o/r|--ledger F --workflow W --job J --step S --seconds N --conclusion success|failure
  median  --repo o/r|--ledger F --workflow W --job J --step S     → {"samples": n, "median_s": x|null}
  path    --repo o/r                                              → prints the default path, writes nothing

Exit 0 on success; exit 2 on a usage error.
"""

from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
from datetime import (  # timezone.utc, not UTC: the skill runs on any python3 >= 3.9
    datetime,
    timezone,
)
from pathlib import Path

KEEP = 10
VERSION = 1


def default_path(repo: str) -> Path:
    base = Path(os.environ.get("XDG_CACHE_HOME") or (Path.home() / ".cache"))
    return base / "ci-fix" / (repo.replace("/", "--") + ".json")


def resolve_path(args) -> Path | None:
    if args.ledger:
        return Path(args.ledger)
    if args.repo:
        return default_path(args.repo)
    return None


def load(path: Path) -> dict:
    if not path.is_file():
        return {"version": VERSION, "samples": []}
    try:
        data = json.loads(path.read_text())
    except (OSError, ValueError):
        return {"version": VERSION, "samples": []}
    if not isinstance(data, dict) or not isinstance(data.get("samples"), list):
        return {"version": VERSION, "samples": []}
    return data


def key_of(s: dict) -> tuple:
    return (s.get("workflow"), s.get("job"), s.get("step"))


def matching(data: dict, workflow: str, job: str, step: str) -> list[dict]:
    return [s for s in data["samples"] if key_of(s) == (workflow, job, step)]


def cmd_record(args) -> int:
    path = resolve_path(args)
    if path is None:
        return usage("record needs --ledger <file> or --repo <owner/repo>")
    if args.conclusion != "success":
        print(
            json.dumps(
                {
                    "ledger": str(path),
                    "recorded": False,
                    "reason": f"conclusion {args.conclusion}: failures are not sampled",
                }
            )
        )
        return 0
    data = load(path)
    sample = {
        "workflow": args.workflow,
        "job": args.job,
        "step": args.step,
        "seconds": float(args.seconds),
        "at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),  # noqa: UP017
    }
    others = [s for s in data["samples"] if key_of(s) != key_of(sample)]
    mine = matching(data, args.workflow, args.job, args.step) + [sample]
    data = {"version": VERSION, "samples": others + mine[-KEEP:]}
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=1))
    tmp.replace(path)
    kept = mine[-KEEP:]
    print(
        json.dumps(
            {
                "ledger": str(path),
                "recorded": True,
                "samples": len(kept),
                "median_s": float(statistics.median(s["seconds"] for s in kept)),
            }
        )
    )
    return 0


def cmd_median(args) -> int:
    path = resolve_path(args)
    if path is None:
        return usage("median needs --ledger <file> or --repo <owner/repo>")
    data = load(path)
    mine = matching(data, args.workflow, args.job, args.step)[-KEEP:]
    print(
        json.dumps(
            {
                "samples": len(mine),
                "median_s": float(statistics.median(s["seconds"] for s in mine))
                if mine
                else None,
            }
        )
    )
    return 0


def cmd_path(args) -> int:
    if not args.repo:
        return usage("path needs --repo <owner/repo>")
    print(default_path(args.repo))
    return 0


def usage(msg: str) -> int:
    print(f"error: {msg}", file=sys.stderr)
    return 2


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = ap.add_subparsers(dest="cmd", required=True)

    def where(p):
        p.add_argument("--ledger", help="explicit ledger file")
        p.add_argument("--repo", help="owner/repo, for the default machine-level path")

    def key(p):
        p.add_argument("--workflow", required=True)
        p.add_argument(
            "--job", required=True, help="job display name as the jobs API reports it"
        )
        p.add_argument(
            "--step", required=True, help="step display name as the jobs API reports it"
        )

    p = sub.add_parser("record", help="record one observed run of the step's command")
    where(p)
    key(p)
    p.add_argument("--seconds", required=True, type=float)
    p.add_argument("--conclusion", required=True, choices=["success", "failure"])
    p.set_defaults(fn=cmd_record)

    p = sub.add_parser("median", help="median of the recorded successes for one step")
    where(p)
    key(p)
    p.set_defaults(fn=cmd_median)

    p = sub.add_parser("path", help="print the default ledger path for a repo")
    p.add_argument("--repo", required=False)
    p.set_defaults(fn=cmd_path)

    args = ap.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
