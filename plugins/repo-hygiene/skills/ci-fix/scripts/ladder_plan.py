#!/usr/bin/env python3
"""ladder_plan.py — where a fix enters the ladder, and how it reaches CI.

The isolation heuristic as code. Isolating a failure pays only when the
isolated run is much shorter than the whole thing, and the cost of isolating
differs by level: locally it is one command (5–20 s of overhead), in CI it is
a marked commit, a dispatch, and a second commit and run (2–4 min extra).

  local   failed step expected under --isolate-local (30s) → rung 1 only
          over it, or unmeasured                           → rung 0 (the IDs), then rung 1
          rung 1 (the whole step) always runs when the step can run here and
          its expected time is within the cap (10 min); above the cap the
          user is asked once, and a "no" makes CI the lab
  remote  plain push unless CI is the lab AND the target job is expected over
          --isolate-remote (5m) AND the workflow is dispatchable: then only
          that workflow is dispatched with the failing IDs in its filter
          input (offering to add the input when the workflow lacks one). A
          plain push is both rung 2 and rung 3. With one expected CI round,
          which is the usual case after a local green, a dispatch loses time.

"CI is the lab" (--ci-is-lab) means the failure can only be observed in CI:
the job is not reproducible locally (implied by --no-local-step), the whole
local step was declined at the cap, or CI went red again after a local
green. Compute the plan before the local rungs, and again for the remote
mode once the local outcome is known.

Inputs: the ci_profile.py --json document, the failed job and step, the
extracted-ID count, and facts the skill has established from the inventory
(dispatchable, filter input, whether the step runs on this host). An optional
local ledger (local_ledger.py) overrides the CI step median for the local
decision.

Exit 0 with the plan; exit 2 on a usage error (bad duration, ambiguous job).
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_ISOLATE_LOCAL = "30s"
DEFAULT_ISOLATE_REMOTE = "5m"
LOCAL_CAP_S = 600  # the harness's single-command limit; a longer whole-step run is asked about, then backgrounded
LEDGER_KEEP = 10


def _load_parse_duration():
    spec = importlib.util.spec_from_file_location("ci_profile", HERE / "ci_profile.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.parse_duration


def classify(seconds: float | None, floor_s: int) -> str:
    if seconds is None:
        return "unmeasured"
    return "slow" if seconds > floor_s else "fast"


def find_job(
    profile: dict, workflow: str | None, job: str
) -> tuple[dict | None, list[str]]:
    """Match on the profile's `job` (the jobs-API name, and the ledger's key);
    `name` is the display string, which becomes `CI / pytest` when two
    workflows share a job name."""
    matches = [j for j in profile.get("jobs", []) if j.get("job", j.get("name")) == job]
    if workflow is not None:
        matches = [j for j in matches if j.get("workflow_name") == workflow]
    if len(matches) > 1:
        return None, sorted({j.get("workflow_name") or "?" for j in matches})
    return (matches[0] if matches else None), []


def ledger_median(
    path: Path | None, workflow: str | None, job: str, step: str
) -> tuple[float | None, int]:
    if path is None or not path.is_file():
        return None, 0
    try:
        data = json.loads(path.read_text())
    except (OSError, ValueError):
        return None, 0
    samples = [
        s["seconds"]
        for s in data.get("samples", [])
        if s.get("job") == job
        and s.get("step") == step
        and (workflow is None or s.get("workflow") == workflow)
    ]
    samples = samples[-LEDGER_KEEP:]
    if not samples:
        return None, 0
    return float(statistics.median(samples)), len(samples)


def fmt(seconds: float | None) -> str:
    if seconds is None:
        return "unmeasured"
    seconds = round(seconds)
    if seconds < 60:
        return f"{seconds}s"
    m, s = divmod(seconds, 60)
    if m < 60:
        return f"{m}m{s:02d}s" if s else f"{m}m"
    h, m = divmod(m, 60)
    return f"{h}h{m:02d}m"


def local_plan(
    args, floor_s: int, job_entry: dict | None, workflow: str | None
) -> dict:
    step_median = None
    source = "none"
    if job_entry is not None:
        for st in job_entry.get("steps", []):
            if st.get("name") == args.step:
                step_median = st.get("median_s")
                source = "profile" if step_median is not None else "none"
                break
    led, n = ledger_median(args.ledger, workflow, args.job, args.step)
    if led is not None:
        step_median, source = led, "ledger"
    step_class = classify(step_median, floor_s)
    where = (
        f"{fmt(step_median)} ({source})" if step_median is not None else "unmeasured"
    )
    slow_text = (
        f"over the local floor {fmt(floor_s)}"
        if step_class == "slow"
        else "unmeasured, treated as slow"
    )

    plan = {
        "step": args.step,
        "step_class": step_class,
        "step_expected_s": step_median,
        "source": source,
        "ledger_samples": n,
        "floor_s": floor_s,
        "cap_s": LOCAL_CAP_S,
        "entry_rung": None,
        "rung_0": False,
        "rung_1": False,
        "rung_1_gate": "unavailable",  # run | ask | unavailable
        "rung_1_background": False,
        "reason": "",
    }
    if not args.local_step:
        plan["reason"] = (
            "not reproducible locally: no rung 0 or rung 1 for this job; fix from the log evidence, "
            "run the sweep (rung 1s), then enter CI — CI is the lab"
        )
        return plan

    plan["rung_1"] = True
    over_cap = step_median is not None and step_median > LOCAL_CAP_S
    plan["rung_1_gate"] = "ask" if over_cap else "run"
    plan["rung_1_background"] = over_cap or step_median is None
    if step_class == "fast":
        plan["entry_rung"] = 1
        plan["reason"] = (
            f"step expected {where} is under the local floor {fmt(floor_s)}: run the whole step (rung 1); "
            "isolating one test would cost a run of its own and save nothing"
        )
    elif args.ids > 0:
        plan["entry_rung"] = 0
        plan["rung_0"] = True
        plan["reason"] = (
            f"step expected {where} is {slow_text}: run the {args.ids} extracted ID(s) first (rung 0), "
            f"then the whole step (rung 1, expected {fmt(step_median)})"
        )
    else:
        plan["entry_rung"] = 1
        plan["reason"] = (
            f"step expected {where} is {slow_text} but no test IDs were extracted, so rung 0 is unavailable: "
            f"run the whole step (rung 1, expected {fmt(step_median)})"
        )
    if over_cap:
        plan["reason"] += (
            f"; rung 1 exceeds the {fmt(LOCAL_CAP_S)} cap: ask once (background run on yes; on no, CI is the lab "
            "and the full run there is the gate)"
        )
    elif step_median is None:
        plan["reason"] += (
            "; rung 1 is unmeasured: run it in the background and record its duration"
        )
    return plan


def remote_plan(args, floor_s: int, job_entry: dict | None) -> dict:
    job_median = job_entry.get("median_s") if job_entry else None
    job_class = classify(job_median, floor_s)
    wait_bound = job_entry.get("wait_bound_s") if job_entry else None
    ci_is_lab = args.ci_is_lab or not args.local_step
    can_filter = bool(args.filter_input) and args.ids > 0

    plan = {
        "job": args.job,
        "job_class": job_class,
        "job_expected_s": job_median,
        "floor_s": floor_s,
        "wait_bound_s": wait_bound,
        "ci_is_lab": ci_is_lab,
        "mode": "push",
        "marker": False,
        "filter_input": args.filter_input if can_filter else None,
        "reason": "",
    }
    same_run = "plain push, watch the job; rung 2 and rung 3 are the same run, no marker, no dispatch"
    if not ci_is_lab:
        plan["reason"] = (
            "the fix was verified locally, so one CI round is expected and a dispatch would only add its own "
            f"setup and a second cycle: {same_run}"
        )
        return plan
    if job_class == "fast":
        plan["reason"] = (
            f"CI is the lab but the target job expected {fmt(job_median)} is under the remote floor {fmt(floor_s)}: "
            f"an isolated run would still pay checkout and setup and save nothing: {same_run}"
        )
        return plan

    slow_text = (
        f"over the remote floor {fmt(floor_s)}"
        if job_class == "slow"
        else "unmeasured, treated as slow"
    )
    if not args.dispatchable:
        plan["reason"] = (
            f"CI is the lab and the target job expected {fmt(job_median)} is {slow_text}, but the workflow is not "
            "dispatchable (no workflow_dispatch on this branch, or the file is absent from the default branch): "
            f"{same_run}; record --optimize lever 11"
        )
        return plan
    if can_filter:
        plan.update(mode="dispatch-filtered", marker=True)
        plan["reason"] = (
            f"CI is the lab and the target job expected {fmt(job_median)} is {slow_text}: commit with [skip ci], "
            f"dispatch only this workflow with inputs[{args.filter_input}] carrying the {args.ids} failing ID(s), "
            "the remote mirror of rung 0; the full run follows on the marker-free commit"
        )
        return plan
    if args.ids > 0:
        plan.update(mode="offer-filter", marker=False)
        plan["on_accept"] = {"mode": "dispatch-filtered", "marker": True}
        plan["on_decline"] = {"mode": "push", "marker": False}
        plan["reason"] = (
            f"CI is the lab and the target job expected {fmt(job_median)} is {slow_text}, but the workflow declares "
            "no filter input: offer once to add one (filter-input.md); accepted → filtered dispatch on the fix "
            f"commit; declined → {same_run} (dispatching the whole job would save runner minutes, not time)"
        )
        return plan
    plan["reason"] = (
        f"CI is the lab and the target job expected {fmt(job_median)} is {slow_text}, but no test IDs were "
        f"extracted, so there is nothing to isolate: {same_run}"
    )
    return plan


def render(plan: dict) -> str:
    loc, rem = plan["local"], plan["remote"]
    lines = [
        f"ladder plan — local floor {fmt(loc['floor_s'])}, cap {fmt(loc['cap_s'])}; remote floor {fmt(rem['floor_s'])}",
        "",
    ]
    if loc["entry_rung"] is None:
        lines.append(f"local   no rung — {loc['reason']}")
    else:
        rungs = (
            "rung 0 (IDs) then rung 1 (whole step)"
            if loc["rung_0"]
            else "rung 1 (whole step)"
        )
        gate = {"run": "runs", "ask": "asked once (over the cap)"}[loc["rung_1_gate"]]
        bg = ", in the background" if loc["rung_1_background"] else ""
        lines.append(
            f"local   enter at rung {loc['entry_rung']}: {rungs}; rung 1 {gate}{bg}"
        )
        lines.append(
            f"        step {loc['step_class']} · expected {fmt(loc['step_expected_s'])} ({loc['source']}) · {loc['reason']}"
        )
    marker = "[skip ci] on the fix commit" if rem["marker"] else "no marker"
    bound = (
        fmt(rem["wait_bound_s"]) if rem["wait_bound_s"] else "longest measured bound"
    )
    lab = "CI is the lab" if rem["ci_is_lab"] else "verified locally"
    lines.append(f"remote  {rem['mode']} · {marker} · {lab} · wait bound {bound}")
    lines.append(
        f"        job {rem['job_class']} · expected {fmt(rem['job_expected_s'])} · {rem['reason']}"
    )
    if rem["mode"] == "offer-filter":
        lines.append(
            f"        accepted → {rem['on_accept']['mode']}; declined → {rem['on_decline']['mode']}"
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument(
        "--profile", required=True, type=Path, help="ci_profile.py --json output"
    )
    ap.add_argument("--ledger", type=Path, help="local_ledger.py file (optional)")
    ap.add_argument(
        "--isolate-local",
        default=DEFAULT_ISOLATE_LOCAL,
        help=f"local floor: isolate (rung 0) when the step is expected to take longer (default {DEFAULT_ISOLATE_LOCAL})",
    )
    ap.add_argument(
        "--isolate-remote",
        default=DEFAULT_ISOLATE_REMOTE,
        help=f"remote floor: dispatch only when CI is the lab and the job is expected to take longer (default {DEFAULT_ISOLATE_REMOTE})",
    )
    ap.add_argument(
        "--workflow",
        help="workflow name (required when the job name exists in several workflows)",
    )
    ap.add_argument(
        "--job",
        required=True,
        help="job display name as the jobs API reports it, e.g. 'pytest (3.12)'",
    )
    ap.add_argument(
        "--step", required=True, help="failed step display name from the jobs API"
    )
    ap.add_argument(
        "--ids",
        type=int,
        default=0,
        help="number of test IDs extract_failures.py found",
    )
    g = ap.add_mutually_exclusive_group()
    g.add_argument(
        "--dispatchable",
        dest="dispatchable",
        action="store_true",
        help="workflow_dispatch is on this branch's copy AND the file exists on the default branch",
    )
    g.add_argument("--not-dispatchable", dest="dispatchable", action="store_false")
    ap.set_defaults(dispatchable=False)
    g2 = ap.add_mutually_exclusive_group()
    g2.add_argument(
        "--local-step",
        dest="local_step",
        action="store_true",
        help="the failed step can run on this host",
    )
    g2.add_argument("--no-local-step", dest="local_step", action="store_false")
    ap.set_defaults(local_step=True)
    g3 = ap.add_mutually_exclusive_group()
    g3.add_argument(
        "--ci-is-lab",
        dest="ci_is_lab",
        action="store_true",
        help="the failure can only be observed in CI: whole local step declined at the cap, or CI red after a local green",
    )
    g3.add_argument("--not-ci-is-lab", dest="ci_is_lab", action="store_false")
    ap.set_defaults(ci_is_lab=False)
    ap.add_argument(
        "--filter-input",
        help="name of the workflow_dispatch input that narrows the test run, if declared",
    )
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    parse_duration = _load_parse_duration()
    try:
        local_floor = parse_duration(args.isolate_local)
        remote_floor = parse_duration(args.isolate_remote)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    try:
        profile = json.loads(args.profile.read_text())
    except (OSError, ValueError) as e:
        print(f"error: cannot read profile {args.profile}: {e}", file=sys.stderr)
        return 2

    job_entry, ambiguous = find_job(profile, args.workflow, args.job)
    if ambiguous:
        print(
            f"error: job {args.job!r} exists in several workflows ({', '.join(ambiguous)}); pass --workflow",
            file=sys.stderr,
        )
        return 2
    workflow = args.workflow or (job_entry.get("workflow_name") if job_entry else None)

    plan = {
        "workflow": workflow,
        "local": local_plan(args, local_floor, job_entry, workflow),
        "remote": remote_plan(args, remote_floor, job_entry),
    }
    print(json.dumps(plan, indent=2) if args.json else render(plan))
    return 0


if __name__ == "__main__":
    sys.exit(main())
