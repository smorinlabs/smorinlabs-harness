#!/usr/bin/env python3
"""ladder_plan.py — choose measured, affected validation and supplemental CI diagnostics.

A compatible measured complete local bundle at or below --isolate-local serves
as both reproducer and post-edit check, without a separate ID-only pass.
Otherwise start with extracted IDs, or localize a meaningful target.
A full step requires --full-step-reason; its duration alone never requires it.
Host and Linux-runner estimates remain visible, with compatible ledger samples
preferred over CI proxies. Estimates never establish the measured-bundle shortcut.

An ordinary push supplies required CI. When CI is the lab and isolation pays,
a filtered dispatch is supplemental evidence on the same commit; no skip marker
or empty trigger commit is used. Match expected coverage before completion.

Exit 0 with the plan; exit 2 on invalid inputs or ambiguous job identity.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import sys
from pathlib import Path

from local_ledger import context_key, load, matching

HERE = Path(__file__).resolve().parent
DEFAULT_ISOLATE_LOCAL = "30s"
DEFAULT_ISOLATE_REMOTE = "5m"
CONTAINER_FIRST_RUN_FACTOR = (
    2  # image pull and start-up, until the ledger has a real sample
)
LOCAL_CAP_S = 600  # foreground wait limit, never a reason to run or skip coverage
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
    profile: dict, workflow: str | None, workflow_path: str | None, job: str
) -> tuple[dict | None, list[str]]:
    """Match on the profile's `job` (the jobs-API name, and the ledger's key);
    `name` is the display string, which becomes `CI / pytest` when two
    workflows share a job name."""
    matches = [j for j in profile.get("jobs", []) if j.get("job", j.get("name")) == job]
    if workflow_path is not None:
        matches = [j for j in matches if j.get("workflow_path") == workflow_path]
    elif workflow is not None:
        matches = [j for j in matches if j.get("workflow_name") == workflow]
    if len(matches) > 1:
        # two workflow *files* can share a `name:`, so --workflow cannot
        # separate them; name the paths, which --workflow-path selects
        return None, sorted(
            {j.get("workflow_path") or j.get("workflow_name") or "?" for j in matches}
        )
    return (matches[0] if matches else None), []


def ledger_median(path, workflow, workflow_path, job, step, context):
    if path is None or context is None:
        return None, 0
    samples = matching(load(path), workflow, workflow_path, job, step, context)[
        -LEDGER_KEEP:
    ]
    if not samples:
        return None, 0
    from statistics import median

    return float(median(s["seconds"] for s in samples)), len(samples)


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


def local_plan(args, floor_s, job_entry, workflow, workflow_path):
    step_median = next(
        (
            s.get("median_s")
            for s in (job_entry or {}).get("steps", [])
            if s.get("name") == args.step
        ),
        None,
    )
    source = "profile" if step_median is not None else "none"
    led, n = ledger_median(
        args.ledger, workflow, workflow_path, args.job, args.step, args.context_key
    )
    if led is not None:
        step_median, source = led, "ledger"
    elif step_median is not None and args.local_env == "container":
        step_median *= CONTAINER_FIRST_RUN_FACTOR
        source = f"profile x{CONTAINER_FIRST_RUN_FACTOR} (container, first run)"
    plan = {
        "step": args.step,
        "step_class": classify(step_median, floor_s),
        "step_expected_s": step_median,
        "source": source,
        "ledger_samples": n,
        "local_env": args.local_env,
        "floor_s": floor_s,
        "cap_s": LOCAL_CAP_S,
        "bundle_measured_s": args.bundle_seconds,
        "scope": "unavailable",
        "entry_rung": None,
        "rung_0": False,
        "rung_1": False,
        "rung_1_gate": "unavailable",
        "rung_1_background": False,
        "required_next": "rerun the chosen scope after each relevant edit; verify intended selection and affected behavior; reconcile required CI",
        "reason": "not reproducible locally: preserve the limitation and use CI diagnostics",
    }
    if not args.local_step:
        return plan
    plan["rung_1_gate"] = "not-needed"
    if args.bundle_seconds is not None and args.bundle_seconds <= floor_s:
        plan.update(
            scope="bundle",
            entry_rung=1,
            rung_1=True,
            rung_1_gate="run",
            rung_1_background=args.bundle_seconds > LOCAL_CAP_S,
            reason=f"complete compatible local bundle measured at {fmt(args.bundle_seconds)}: use it before and after the edit; no separate ID-only pass",
        )
    elif args.full_step_reason:
        plan.update(
            scope="full-step",
            entry_rung=0 if args.ids else 1,
            rung_0=args.ids > 0,
            rung_1=True,
            rung_1_gate="run",
            rung_1_background=step_median is None or step_median > LOCAL_CAP_S,
            reason=f"full step justified by affected behavior: {args.full_step_reason}; reproduce extracted IDs first when available, then verify the affected full step",
        )
    elif args.ids:
        plan.update(
            scope="ids",
            entry_rung=0,
            rung_0=True,
            reason=f"start with {args.ids} failing ID(s), then choose affected checks; no measured fast complete bundle or full-step justification",
        )
    else:
        plan.update(
            scope="localize",
            reason="no exact IDs: identify the smallest useful file, module, package or check; record --full-step-reason only if the full command is necessary",
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
        "required_coverage": "ordinary unfiltered CI for the evaluated commit; see ci-coverage.md",
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
        plan.update(mode="dispatch-filtered", marker=False)
        plan["reason"] = (
            f"CI is the lab and the target job expected {fmt(job_median)} is {slow_text}: use an ordinary push, then "
            f"dispatch only this workflow with inputs[{args.filter_input}] carrying the {args.ids} failing ID(s), "
            "as supplemental diagnosis; ordinary unfiltered required CI on the evaluated commit still gates completion"
        )
        return plan
    if args.ids > 0:
        plan.update(mode="offer-filter", marker=False)
        plan["on_accept"] = {"mode": "dispatch-filtered", "marker": False}
        plan["on_decline"] = {"mode": "push", "marker": False}
        plan["reason"] = (
            f"CI is the lab and the target job expected {fmt(job_median)} is {slow_text}, but the workflow declares "
            "no filter input: offer once to add one (filter-input.md); accepted → supplemental filtered dispatch on the fix "
            f"commit; declined → {same_run}; an extra unfiltered dispatch would duplicate ordinary CI"
        )
        return plan
    plan["reason"] = (
        f"CI is the lab and the target job expected {fmt(job_median)} is {slow_text}, but no test IDs were "
        f"extracted, so there is nothing to isolate: {same_run}"
    )
    return plan


def render(plan: dict) -> str:
    loc, rem = plan["local"], plan["remote"]
    return "\n".join(
        [
            f"validation plan — measured-bundle shortcut {fmt(loc['floor_s'])}; remote isolation floor {fmt(rem['floor_s'])}",
            f"local   {loc['scope']} on {loc['local_env']} — {loc['reason']}",
            f"        step estimate {fmt(loc['step_expected_s'])} ({loc['source']}); foreground bound {fmt(loc['cap_s'])}",
            f"next    {loc['required_next']}",
            f"remote  {rem['mode']} — no skip marker; {'CI is the lab' if rem['ci_is_lab'] else 'local diagnosis available'}",
            f"        {rem['reason']}",
            f"done    {rem['required_coverage']}",
        ]
    )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument(
        "--profile", required=True, type=Path, help="ci_profile.py --json output"
    )
    ap.add_argument("--ledger", type=Path, help="local_ledger.py file (optional)")
    ap.add_argument(
        "--context",
        type=Path,
        help="current non-secret command/scope/environment JSON; required to reuse ledger timings",
    )
    ap.add_argument(
        "--bundle-seconds",
        type=float,
        help="compatible measured total local bundle seconds, including needed preparation; never a single step or CI proxy",
    )
    ap.add_argument(
        "--full-step-reason",
        help="why affected behavior requires the whole step; without this a slow/unknown bundle starts with failing IDs or localization",
    )
    ap.add_argument(
        "--isolate-local",
        default=DEFAULT_ISOLATE_LOCAL,
        help=f"complete measured local bundle shortcut threshold (default {DEFAULT_ISOLATE_LOCAL})",
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
        "--workflow-path",
        help="workflow file path (e.g. .github/workflows/ci.yml); the only way to separate two "
        "workflow files that share a name:, and part of the local ledger's identity",
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
    ap.add_argument(
        "--local-env",
        choices=["host", "container"],
        default="host",
        help="where the local rungs would run: on this host, or in a Linux container or VM from "
        "runners.toml (detect_runners.py). A container's first run is estimated at twice the CI "
        "median, because CI's number excludes the image pull and start-up this machine pays.",
    )
    g3 = ap.add_mutually_exclusive_group()
    g3.add_argument(
        "--ci-is-lab",
        dest="ci_is_lab",
        action="store_true",
        help="needed local validation is unavailable, or a discrepancy remains after local success",
    )
    g3.add_argument("--not-ci-is-lab", dest="ci_is_lab", action="store_false")
    ap.set_defaults(ci_is_lab=False)
    ap.add_argument(
        "--filter-input",
        help="name of the workflow_dispatch input that narrows the test run, if declared",
    )
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    if args.ids < 0 or (
        args.bundle_seconds is not None
        and (not math.isfinite(args.bundle_seconds) or args.bundle_seconds < 0)
    ):
        ap.error("--ids and --bundle-seconds must be finite and non-negative")
    if args.full_step_reason is not None and not args.full_step_reason.strip():
        ap.error("--full-step-reason must state the affected behavior")
    try:
        args.context_key = context_key(args.context) if args.context else None
    except (OSError, ValueError) as exc:
        ap.error(f"cannot read execution context: {exc}")
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

    job_entry, ambiguous = find_job(
        profile, args.workflow, args.workflow_path, args.job
    )
    if ambiguous:
        flag = "--workflow-path" if args.workflow else "--workflow"
        print(
            f"error: job {args.job!r} exists in several workflows ({', '.join(ambiguous)}); pass {flag}",
            file=sys.stderr,
        )
        return 2
    workflow = args.workflow or (job_entry.get("workflow_name") if job_entry else None)
    workflow_path = args.workflow_path or (
        job_entry.get("workflow_path") if job_entry else None
    )

    plan = {
        "workflow": workflow,
        "workflow_path": workflow_path,
        "local": local_plan(args, local_floor, job_entry, workflow, workflow_path),
        "remote": remote_plan(args, remote_floor, job_entry),
    }
    print(json.dumps(plan, indent=2) if args.json else render(plan))
    return 0


if __name__ == "__main__":
    sys.exit(main())
