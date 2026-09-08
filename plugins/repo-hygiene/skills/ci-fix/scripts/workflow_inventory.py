#!/usr/bin/env python3
"""workflow_inventory.py — what a GitHub Actions workflow file declares.

For each workflow file: its triggers (incl. `workflow_dispatch` inputs) and,
per job, the runner family, matrix cells with the display names the jobs API
uses (`unit (ubuntu-latest, 3.12)`), `needs`, `container`, `services`,
`timeout-minutes`, and every step with its display name (`Run <uses>` /
`Run <first run line>`, exactly as the jobs API names unnamed steps), its
`run:` text, `working-directory`, `env`, and two flags the local sweep keys on:
`kind` (`run` or `uses`) and `setup` (package-manager or installer commands
that must not be executed on the host).

Needs PyYAML. Run as:
    uv run --no-project --with pyyaml <skill-dir>/scripts/workflow_inventory.py [--json] <workflow.yml> ...

Exit 0 ok; 2 on a usage error (missing file, invalid YAML, PyYAML absent).
"""

from __future__ import annotations

import argparse
import itertools
import json
import os
import re
import sys

RUNNER_LINE = "uv run --no-project --with pyyaml <skill-dir>/scripts/workflow_inventory.py"

try:
    import yaml
except ImportError:  # pragma: no cover - exercised by the -S test
    yaml = None

SETUP_RE = re.compile(
    r"^\s*(sudo\s+)?("
    r"apt-get|apt|brew|choco|winget|yum|dnf|apk|pacman|zypper"
    r"|pip3?\s+install|pipx\s+install|npm\s+(install|i)\s+-g|npm\s+(install|i)\s+--global"
    r"|yarn\s+global\s+add|pnpm\s+add\s+-g|cargo\s+install|go\s+install|gem\s+install"
    r"|curl|wget|rustup|nvm|pyenv"
    r")\b"
)


def os_family(runs_on) -> str:
    if isinstance(runs_on, list):
        text = " ".join(str(x) for x in runs_on)
        if "self-hosted" in text:
            return "self-hosted"
    else:
        text = str(runs_on or "")
    if "${{" in text:
        return "matrix"
    low = text.lower()
    if low.startswith("ubuntu") or "linux" in low:
        return "linux"
    if low.startswith("macos"):
        return "macos"
    if low.startswith("windows"):
        return "windows"
    return "unknown"


def family_for_cell(runs_on, cell: dict) -> str:
    """Resolve `${{ matrix.<key> }}` against a cell; else the static family."""
    fam = os_family(runs_on)
    if fam != "matrix":
        return fam
    m = re.search(r"matrix\.([A-Za-z0-9_-]+)", str(runs_on))
    if m and m.group(1) in cell:
        return os_family(cell[m.group(1)])
    return "matrix"


def scalar(value) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def expand_matrix(job_id: str, runs_on, matrix) -> list[dict]:
    if not isinstance(matrix, dict):
        return []
    include = matrix.get("include") or []
    exclude = matrix.get("exclude") or []
    axes = {k: v for k, v in matrix.items() if k not in ("include", "exclude") and isinstance(v, list)}
    cells: list[dict] = []
    if axes:
        keys = list(axes)
        for combo in itertools.product(*(axes[k] for k in keys)):
            cells.append(dict(zip(keys, combo)))
    for inc in include:
        if not isinstance(inc, dict):
            continue
        matched = False
        for cell in cells:
            shared = {k for k in inc if k in cell}
            if shared and all(cell[k] == inc[k] for k in shared):
                cell.update({k: v for k, v in inc.items() if k not in cell})
                matched = True
        if not matched:
            cells.append(dict(inc))
    for exc in exclude:
        if isinstance(exc, dict):
            cells = [c for c in cells if not all(c.get(k) == v for k, v in exc.items())]
    out = []
    for cell in cells:
        values = ", ".join(scalar(v) for v in cell.values())
        out.append({**cell, "display_name": f"{job_id} ({values})", "os_family": family_for_cell(runs_on, cell)})
    return out


def step_record(index: int, step: dict) -> dict:
    uses = step.get("uses")
    run = step.get("run")
    if step.get("name"):
        display = str(step["name"])
    elif uses:
        display = f"Run {uses}"
    elif run is not None:
        display = f"Run {str(run).strip().splitlines()[0] if str(run).strip() else ''}"
    else:
        display = f"step {index}"
    return {
        "index": index,
        "display_name": display,
        "kind": "uses" if uses else "run",
        "uses": uses,
        "run": run,
        "working_directory": step.get("working-directory"),
        "env": step.get("env") or {},
        "setup": bool(run is not None and SETUP_RE.match(str(run).strip())),
    }


def triggers_of(doc: dict) -> tuple[list[str], dict | None]:
    on = doc.get("on", doc.get(True))  # YAML 1.1 reads a bare `on` key as True
    if on is None:
        return [], None
    if isinstance(on, str):
        names = [on]
        spec = {}
    elif isinstance(on, list):
        names = [str(x) for x in on]
        spec = {}
    else:
        names = [str(k) for k in on]
        spec = on
    names = sorted(names)
    dispatch = None
    if "workflow_dispatch" in names:
        raw = (spec.get("workflow_dispatch") or {}) if isinstance(spec, dict) else {}
        inputs = (raw or {}).get("inputs") or {}
        dispatch = {
            str(k): {
                "required": bool((v or {}).get("required", False)),
                "default": (v or {}).get("default"),
                "type": (v or {}).get("type"),
                "options": (v or {}).get("options"),
            }
            for k, v in inputs.items()
        }
    return names, dispatch


def inventory_file(path: str) -> dict:
    try:
        with open(path, encoding="utf-8") as fh:
            doc = yaml.safe_load(fh)
    except OSError as exc:
        raise SystemExit(f"error: cannot read {path}: {exc.strerror}") from exc
    except yaml.YAMLError as exc:
        raise SystemExit(f"error: {path} is not valid YAML: {exc}") from exc
    if not isinstance(doc, dict):
        raise SystemExit(f"error: {path} is not a workflow mapping")
    triggers, dispatch = triggers_of(doc)
    jobs = []
    for job_id, job in (doc.get("jobs") or {}).items():
        job = job or {}
        runs_on = job.get("runs-on")
        strategy = job.get("strategy") or {}
        container = job.get("container")
        if isinstance(container, dict):
            container = container.get("image")
        needs = job.get("needs")
        if isinstance(needs, str):
            needs = [needs]
        jobs.append(
            {
                "id": str(job_id),
                "name": job.get("name"),
                "runs_on": runs_on,
                "os_family": os_family(runs_on),
                "needs": needs or [],
                "matrix": strategy.get("matrix") if isinstance(strategy, dict) else None,
                "matrix_cells": expand_matrix(str(job_id), runs_on, strategy.get("matrix") if isinstance(strategy, dict) else None),
                "container": container,
                "services": sorted((job.get("services") or {}).keys()),
                "timeout_minutes": job.get("timeout-minutes"),
                "steps": [step_record(i, s or {}) for i, s in enumerate(job.get("steps") or [])],
            }
        )
    return {"path": path, "name": doc.get("name"), "triggers": triggers, "dispatch_inputs": dispatch, "jobs": jobs}


def render_text(data: dict) -> str:
    lines = []
    for wf in data["workflows"]:
        base = os.path.basename(wf["path"])
        disp = f" inputs={','.join(wf['dispatch_inputs'])}" if wf["dispatch_inputs"] else ""
        lines.append(f"{base}  triggers={','.join(wf['triggers'])}{disp}")
        for j in wf["jobs"]:
            runs = sum(1 for s in j["steps"] if s["kind"] == "run" and not s["setup"])
            extras = []
            if j["matrix_cells"]:
                extras.append(f"cells={len(j['matrix_cells'])}")
            if j["container"]:
                extras.append(f"container={j['container']}")
            if j["services"]:
                extras.append(f"services={','.join(j['services'])}")
            if j["needs"]:
                extras.append(f"needs={','.join(j['needs'])}")
            lines.append(
                f"  {j['id']} runs-on={j['runs_on']} os={j['os_family']} "
                f"steps={len(j['steps'])} sweepable={runs} {' '.join(extras)}".rstrip()
            )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--json", action="store_true", help="emit JSON instead of text")
    parser.add_argument("files", nargs="+", metavar="WORKFLOW_YML")
    args = parser.parse_args(argv)
    if yaml is None:
        print(f"error: PyYAML is not importable here. Run:\n    {RUNNER_LINE} {' '.join(args.files)}", file=sys.stderr)
        return 2
    try:
        data = {"workflows": [inventory_file(f) for f in args.files]}
    except SystemExit as exc:
        print(exc, file=sys.stderr)
        return 2
    print(json.dumps(data, indent=2) if args.json else render_text(data))
    return 0


if __name__ == "__main__":
    sys.exit(main())
