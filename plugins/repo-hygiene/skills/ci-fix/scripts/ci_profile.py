#!/usr/bin/env python3
"""ci_profile.py — per-job duration profile from GitHub Actions jobs JSON.

Input: one or more files, each the REST response of
`repos/{owner}/{repo}/actions/runs/{run_id}/jobs` (an object with a `jobs`
list, or a bare list of jobs). One file per sampled run.

Output (text, or `--json`): for every job name seen across the samples —
median and max duration (completed_at − started_at), median queue wait
(started_at − created_at), a class against the threshold (`slow` when the
median exceeds it, `fast` otherwise, `unmeasured` when no sample completed; skipped and cancelled jobs are never
samples — a skipped job is 0s and a cancelled one is truncated),
the slowest step by median, and `wait_bound_s`, a data-derived lifetime for a
CI-wait monitor: ceil(1.5 × (median + queue)) with a 60s floor. An
`unmeasured` job has no samples, so its `median_s`, `max_s`, and
`wait_bound_s` are null: callers fall back to the longest measured job's bound
(or, with no measured job at all, to 1.5 × the failed run's own duration).

Jobs are keyed by (`workflow_name`, `name`): two workflows that both run a
job called `test` stay two rows, shown as `<workflow> / <job>` only when the
bare name collides. A run whose `total_count` exceeds the jobs delivered is
listed under `truncated_runs` and warned about on stderr — fetch with
`per_page=100` (or paginate).

`--runs LISTING_JSON` (the `actions/runs` listing) joins each job to its run's
workflow `path`; jobs from GitHub-managed workflows (`path` under `dynamic/`,
e.g. the Copilot reviewer) are marked `external` and sorted last — the repo
cannot change them.

Exit 0 on success, 2 on a usage error (bad threshold, unreadable file).
No network: the fetch recipe lives in the skill body.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import statistics
import sys
from datetime import datetime, timezone

DURATION_RE = re.compile(r"^(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?$")
EXCLUDED_CONCLUSIONS = {"skipped", "cancelled"}


def parse_duration(text: str) -> int:
    """'2m' → 120, '90s' → 90, '1h30m' → 5400, '120' → 120."""
    text = text.strip()
    if text.isdigit():
        return int(text)
    m = DURATION_RE.match(text)
    if not m or not any(m.groups()):
        raise ValueError(f"unrecognized threshold {text!r} (use e.g. 2m, 90s, 1h30m, or seconds)")
    h, mi, s = (int(g) if g else 0 for g in m.groups())
    return h * 3600 + mi * 60 + s


def parse_ts(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def seconds_between(start: str | None, end: str | None) -> float | None:
    a, b = parse_ts(start), parse_ts(end)
    if a is None or b is None:
        return None
    return (b - a).total_seconds()


def load_jobs(path: str) -> tuple[list[dict], bool]:
    """Jobs from one run's response, and whether the page was truncated."""
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except OSError as exc:
        raise SystemExit(f"error: cannot read {path}: {exc.strerror}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"error: {path} is not valid JSON: {exc}") from exc
    jobs = data.get("jobs") if isinstance(data, dict) else data
    if not isinstance(jobs, list):
        raise SystemExit(f"error: {path} has no `jobs` list")
    total = data.get("total_count") if isinstance(data, dict) else None
    truncated = isinstance(total, int) and total > len(jobs)
    if truncated:
        print(
            f"warning: {path} holds {len(jobs)} of {total} jobs — the jobs endpoint pages; "
            f"fetch with per_page=100 or paginate",
            file=sys.stderr,
        )
    return jobs, truncated


def load_run_paths(path: str | None) -> dict[int, str]:
    """run id → workflow path, from an `actions/runs` listing."""
    if not path:
        return {}
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except OSError as exc:
        raise SystemExit(f"error: cannot read {path}: {exc.strerror}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"error: {path} is not valid JSON: {exc}") from exc
    runs = data.get("workflow_runs") if isinstance(data, dict) else data
    if not isinstance(runs, list):
        raise SystemExit(f"error: {path} has no `workflow_runs` list")
    return {r["id"]: r.get("path") for r in runs if "id" in r}


def fmt_secs(value: float | None) -> str:
    if value is None:
        return "—"
    value = int(round(value))
    if value >= 3600:
        return f"{value // 3600}h{(value % 3600) // 60:02d}m"
    if value >= 60:
        return f"{value // 60}m{value % 60:02d}s"
    return f"{value}s"


def profile(files: list[str], threshold_s: int, runs_listing: str | None = None) -> dict:
    run_paths = load_run_paths(runs_listing)
    Key = tuple  # (workflow_name, job name)
    workflow_path: dict[Key, str | None] = {}
    durations: dict[Key, list[float]] = {}
    queues: dict[Key, list[float]] = {}
    in_progress: dict[Key, int] = {}
    excluded: dict[Key, int] = {}
    steps: dict[Key, dict[str, list[float]]] = {}
    order: list[Key] = []
    truncated_runs: list[str] = []

    for path in files:
        jobs, truncated = load_jobs(path)
        if truncated:
            truncated_runs.append(path)
        for job in jobs:
            name = (job.get("workflow_name") or "", job.get("name", "<unnamed>"))
            if name not in durations:
                order.append(name)
                durations[name], queues[name], in_progress[name], excluded[name], steps[name] = [], [], 0, 0, {}
                workflow_path[name] = run_paths.get(job.get("run_id"))
            if job.get("conclusion") in EXCLUDED_CONCLUSIONS:
                excluded[name] += 1  # a skipped job is 0s, a cancelled one truncated: not a shape
                continue
            dur = seconds_between(job.get("started_at"), job.get("completed_at"))
            if dur is None:
                in_progress[name] += 1
                continue
            durations[name].append(dur)
            queue = seconds_between(job.get("created_at"), job.get("started_at"))
            if queue is not None:
                queues[name].append(max(queue, 0.0))
            for step in job.get("steps") or []:
                sdur = seconds_between(step.get("started_at"), step.get("completed_at"))
                if sdur is not None:
                    steps[name].setdefault(step.get("name", "<unnamed>"), []).append(sdur)

    bare_counts: dict[str, int] = {}
    for _, bare in order:
        bare_counts[bare] = bare_counts.get(bare, 0) + 1

    rows = []
    for name in order:
        wf, bare = name
        display = f"{wf} / {bare}" if bare_counts[bare] > 1 and wf else bare
        samples = durations[name]
        step_rows = sorted(
            ({"name": s, "median_s": statistics.median(v)} for s, v in steps[name].items()),
            key=lambda r: r["median_s"],
            reverse=True,
        )
        if samples:
            median = statistics.median(samples)
            queue_median = statistics.median(queues[name]) if queues[name] else 0.0
            row = {
                "name": display,
                "job": bare,
                "workflow_name": wf or None,
                "workflow_path": workflow_path[name],
                "external": bool(workflow_path[name] and workflow_path[name].startswith("dynamic/")),
                "class": "slow" if median > threshold_s else "fast",
                "samples": len(samples),
                "in_progress": in_progress[name],
                "excluded": excluded[name],
                "median_s": median,
                "max_s": max(samples),
                "queue_median_s": queue_median,
                "wait_bound_s": max(60, math.ceil(1.5 * (median + queue_median))),
                "slowest_step": step_rows[0] if step_rows else None,
                "steps": step_rows,
            }
        else:
            row = {
                "name": display,
                "job": bare,
                "workflow_name": wf or None,
                "workflow_path": workflow_path[name],
                "external": bool(workflow_path[name] and workflow_path[name].startswith("dynamic/")),
                "class": "unmeasured",
                "samples": 0,
                "in_progress": in_progress[name],
                "excluded": excluded[name],
                "median_s": None,
                "max_s": None,
                "queue_median_s": None,
                "wait_bound_s": None,
                "slowest_step": None,
                "steps": [],
            }
        rows.append(row)

    # external (GitHub-managed) jobs last; then unmeasured on top so they are
    # never overlooked; then slowest first
    rows.sort(key=lambda r: (r["external"], r["median_s"] is not None, -(r["median_s"] or 0)))
    return {
        "threshold_s": threshold_s,
        "runs_sampled": len(files),
        "external_jobs": [r["name"] for r in rows if r["external"]],
        "truncated_runs": truncated_runs,
        "jobs": rows,
    }


def render_text(data: dict) -> str:
    lines = [
        f"CI duration profile — {data['runs_sampled']} run(s) sampled, "
        f"threshold {fmt_secs(data['threshold_s'])} (slow = median above it)",
        "",
        f"{'class':<10} {'job':<32} {'median':>8} {'max':>8} {'queue':>7} {'n':>3}  slowest step",
    ]
    for j in data["jobs"]:
        step = f"{j['slowest_step']['name']} ({fmt_secs(j['slowest_step']['median_s'])})" if j["slowest_step"] else "—"
        n = f"{j['samples']}" + (f"+{j['in_progress']}r" if j["in_progress"] else "")
        flag = "  [external]" if j["external"] else ""
        lines.append(
            f"{j['class']:<10} {j['name'][:32]:<32} {fmt_secs(j['median_s']):>8} "
            f"{fmt_secs(j['max_s']):>8} {fmt_secs(j['queue_median_s']):>7} {n:>3}  {step}{flag}"
        )
    slow = [j["name"] for j in data["jobs"] if j["class"] != "fast" and not j["external"]]
    lines.append("")
    lines.append(
        f"{len(slow)} job(s) at or above threshold or unmeasured: {', '.join(slow)}"
        if slow
        else "All jobs below threshold."
    )
    if data["external_jobs"]:
        lines.append(
            f"external (GitHub-managed, not changeable here): {', '.join(data['external_jobs'])}"
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--threshold", default="2m", help="slow-job threshold (default 2m)")
    parser.add_argument("--json", action="store_true", help="emit JSON instead of a table")
    parser.add_argument("--runs", metavar="LISTING_JSON", help="actions/runs listing: joins jobs to workflow paths")
    parser.add_argument("files", nargs="+", metavar="JOBS_JSON", help="one jobs response per run")
    args = parser.parse_args(argv)
    try:
        threshold_s = parse_duration(args.threshold)
    except ValueError as exc:
        print(f"error: --threshold: {exc}", file=sys.stderr)
        return 2
    try:
        data = profile(args.files, threshold_s, args.runs)
    except SystemExit as exc:
        print(exc, file=sys.stderr)
        return 2
    print(json.dumps(data, indent=2) if args.json else render_text(data))
    return 0


if __name__ == "__main__":
    sys.exit(main())
