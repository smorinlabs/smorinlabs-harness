#!/usr/bin/env python3
"""Bounded execution and observation for dependabot-sweep, Slice 3 (S5).

One absolute deadline bounds a whole process tree: `run_bounded` starts
the child in its own session and kills the entire process group when the
deadline passes, so a hung grandchild, slow credential lookup, or endless
output stream cannot outlive it. Delegation passes the earlier deadline
down and never extends it. `plan_observation` refuses to promise a wait
that cannot finish in the window, and `continuation` refuses a background
owner nobody verified.

Stdlib only. POSIX process groups; the sweep's CI runs on Linux.
"""

from __future__ import annotations

import os
import signal
import subprocess
import time
from dataclasses import dataclass

DEADLINE_ENV = "SWEEP_DEADLINE_EPOCH"
HELPER_DEADLINE_ENV = "GH_MERGE_DEADLINE_EPOCH"


@dataclass
class BoundedResult:
    started: bool
    returncode: int | None
    stdout: str
    stderr: str
    timed_out: bool
    elapsed: float


def effective_deadline(*epochs: float) -> float:
    """The earliest set deadline; 0 when none is set."""
    live = [float(e) for e in epochs if e and float(e) > 0]
    return min(live) if live else 0.0


def _epoch(value: float) -> str:
    return str(int(value)) if float(value).is_integer() else str(value)


def delegate_env(env: dict, deadline_epoch: float) -> dict:
    """Environment for a delegated child: the earlier of the inherited and
    the offered deadline, exported under both names. Never later."""
    inherited = [float((env or {}).get(name) or 0)
                 for name in (DEADLINE_ENV, HELPER_DEADLINE_ENV)]
    deadline = effective_deadline(*inherited, deadline_epoch)
    out = dict(env or {})
    if deadline:
        out[DEADLINE_ENV] = out[HELPER_DEADLINE_ENV] = _epoch(deadline)
    return out


def _decode(data) -> str:
    if data is None:
        return ""
    return data.decode("utf-8", "replace") if isinstance(data, bytes) \
        else data


def _kill_group(proc: subprocess.Popen, sig: int) -> None:
    try:
        os.killpg(proc.pid, sig)
    except (ProcessLookupError, PermissionError):
        pass


def run_bounded(argv: list, deadline_epoch: float, env: dict | None = None,
                grace_secs: float = 2.0) -> BoundedResult:
    """Run argv until it exits or the absolute deadline passes.

    A passed deadline never starts the child, so a retry carrying the same
    epoch gets no fresh window. On expiry the whole process group gets
    SIGTERM, then SIGKILL after `grace_secs`.
    """
    start = time.time()
    if deadline_epoch <= start:
        return BoundedResult(False, None, "", "deadline already passed; "
                             "not started", True, 0.0)
    child_env = None if env is None else {**os.environ, **env}
    proc = subprocess.Popen(argv, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, env=child_env,
                            start_new_session=True)
    try:
        out, err = proc.communicate(timeout=deadline_epoch - start)
        return BoundedResult(True, proc.returncode, _decode(out),
                             _decode(err), False, time.time() - start)
    except subprocess.TimeoutExpired:
        _kill_group(proc, signal.SIGTERM)
        try:
            out, err = proc.communicate(timeout=grace_secs)
        except subprocess.TimeoutExpired:
            _kill_group(proc, signal.SIGKILL)
            out, err = proc.communicate()
        # The leader may exit on SIGTERM while a grandchild ignores it.
        _kill_group(proc, signal.SIGKILL)
        return BoundedResult(True, proc.returncode, _decode(out),
                             _decode(err), True, time.time() - start)


def plan_observation(expected_secs: float, now: float, window_secs: float,
                     deadline_epoch: float) -> dict:
    """Observe only when the expected wait fits inside both the
    observation window and the deadline; otherwise defer to a named
    continuation. A 44-minute job is never promised in a 10-minute
    window."""
    limit = effective_deadline(now + window_secs, deadline_epoch)
    finish = now + expected_secs
    if finish > limit:
        return {"decision": "defer",
                "reason": f"expected {int(expected_secs)}s exceeds the "
                          f"{int(limit - now)}s left in the observation "
                          f"window and deadline"}
    return {"decision": "observe", "until": finish,
            "reason": f"expected {int(expected_secs)}s fits in "
                      f"{int(limit - now)}s"}


CONTINUATION_KINDS = ("watcher", "scheduled", "none")


def continuation(kind: str, ref: str = "", verified_at: str = "") -> dict:
    """The run's one explicit continuation state. A watcher or scheduled
    invocation needs a concrete reference and the time it was verified to
    exist: "someone will re-sweep later" is not a continuation."""
    if kind not in CONTINUATION_KINDS:
        raise ValueError(f"continuation kind must be one of "
                         f"{', '.join(CONTINUATION_KINDS)}")
    if kind == "none":
        return {"kind": "none", "ref": "", "verified_at": ""}
    if not ref or not verified_at:
        raise ValueError(f"a {kind} continuation needs a ref and the time "
                         f"it was verified running")
    return {"kind": kind, "ref": ref, "verified_at": verified_at}
