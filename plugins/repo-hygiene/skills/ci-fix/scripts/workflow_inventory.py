#!/usr/bin/env python3
"""workflow_inventory.py — what a GitHub Actions workflow file declares.

For each workflow file: its triggers (incl. `workflow_dispatch` inputs) and,
per job, the runner family, matrix cells with the display names the jobs API
uses (`unit (ubuntu-latest, 3.12)`), `needs`, `container`, `services`,
`timeout-minutes`, and every step with its display name (`Run <uses>` /
`Run <first run line>`, exactly as the jobs API names unnamed steps), its
`run:` text, `working-directory`, `env`, `if`, `continue-on-error`, `shell`,
the workflow's `trigger_filters` (branches, tags, paths, event types),
and conservative validation hints. `kind` distinguishes `run` from `uses`;
`setup` flags installers that must not run on the host. Effective step
context and three-state conditions guide inspection, never authorization.
Jobs carry merged workflow+job `env` and
`defaults_run`; a matrix job named with `name:` gets that name with
`${{ matrix.* }}` substituted as its cell display name, as the jobs API does.

Needs PyYAML. Run as:
    uv run --no-project --with pyyaml <skill-dir>/scripts/workflow_inventory.py [--json] <workflow.yml> ...

Exit 0 ok; 2 on a usage error (missing file, invalid YAML, PyYAML absent).
"""

from __future__ import annotations

import argparse
import datetime as dt
import itertools
import json
import os
import re
import shlex
import sys

RUNNER_LINE = "uv run --no-project --with pyyaml <skill-dir>/scripts/workflow_inventory.py"


def json_safe(value):
    """Convert YAML values such as unquoted dates into JSON-safe values."""
    if isinstance(value, (dt.datetime, dt.date, dt.time)):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(item) for item in value]
    return value

try:
    import yaml
except ImportError:  # pragma: no cover - exercised by the -S test
    yaml = None

# Installers that write outside the repository are `setup` and never run on
# the host. Project-local installs (`npm ci`, `uv sync`, `pnpm install`) are
# prerequisites to inspect, not permission to execute a local check.
SETUP_RE = re.compile(
    r"^\s*(?:[A-Za-z_][A-Za-z0-9_]*=\S*\s+)*(?:sudo\s+)?("
    r"apt-get|apt|brew|choco|winget|yum|dnf|apk|pacman|zypper"
    r"|pip3?\s+install|pipx\s+install|npm\s+(?:install|i)\s+(?:-g|--global)"
    r"|yarn\s+global\s+add|pnpm\s+add\s+-g|cargo\s+install|go\s+install|gem\s+install"
    r"|rustup|nvm|pyenv"
    r")\b"
)
PIPED_INSTALLER_RE = re.compile(r"^\s*(?:curl|wget)\b.*\|\s*(?:sudo\s+)?(?:ba)?sh\b")


def is_setup(run) -> bool:
    if run is None:
        return False
    for line in str(run).splitlines():
        if SETUP_RE.match(line) or PIPED_INSTALLER_RE.match(line):
            return True
    return False


def constant_boolean(value, default=None):
    """Recognize booleans and literal boolean expressions only; all else is unknown."""
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        text = value.strip()
        if text.startswith("${{") and text.endswith("}}"):
            text = text[3:-2].strip()
        if text.lower() in ("true", "false"):
            return text.lower() == "true"
    return None


def default_shell(family: str, container=False):
    if container:
        return "sh"
    if family == "windows":
        return "pwsh"
    if family in ("linux", "macos"):
        return "bash"  # verify availability; GitHub falls back to sh
    return None  # choose the matrix cell / resolve the runner before execution


def validation_kind(run, shell) -> str:
    """Conservative command hints, never execution authorization or a shell evaluator.

    Wrappers, compound commands and non-POSIX shells require source inspection.
    Even a candidate needs its conditions, environment and prerequisites checked.
    """
    if not isinstance(run, str) or not run.strip():
        return "not-validation"
    if is_setup(run) or re.search(
        r"\b(?:npm\s+publish|cargo\s+publish|twine\s+upload|terraform\s+apply|"
        r"kubectl\s+apply|gh\s+release\s+create)\b",
        run,
    ):
        return "not-validation"
    if shell not in ("bash", "sh") or any(c in run for c in "\n;&|<>`$"):
        return "inspect"
    try:
        args = shlex.split(run)
    except ValueError:
        return "inspect"
    if args[:2] == ["uv", "run"]:
        args = args[2:]
    if (
        len(args) >= 3
        and re.fullmatch(r"python(?:3(?:\.\d+)?)?", args[0])
        and args[1] == "-m"
    ):
        args = args[2:]
    if not args or any(
        a in ("--fix", "--fix-only", "--unsafe-fixes", "fix") for a in args
    ):
        return "inspect"
    if args[0] in ("pytest", "mypy", "actionlint"):
        return "candidate"
    if args[:2] in (
        ["ruff", "check"],
        ["cargo", "test"],
        ["cargo", "check"],
        ["cargo", "clippy"],
        ["go", "test"],
    ):
        return "candidate"
    if args[:3] == ["cargo", "nextest", "run"]:
        return "candidate"
    if args[:2] == ["ruff", "format"] and "--check" in args:
        return "candidate"
    return "inspect"


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


def substitute_matrix(text: str, cell: dict) -> str:
    return re.sub(
        r"\$\{\{\s*matrix\.([A-Za-z0-9_-]+)\s*\}\}",
        lambda m: scalar(cell.get(m.group(1), m.group(0))),
        text,
    )


def expand_matrix(job_id: str, runs_on, matrix, job_name: str | None = None) -> list[dict]:
    if not isinstance(matrix, dict):
        return []
    include = matrix.get("include") or []
    exclude = matrix.get("exclude") or []
    axes = {k: v for k, v in matrix.items() if k not in ("include", "exclude") and isinstance(v, list)}
    axis_keys = set(axes)
    cells: list[dict] = []
    if axes:
        keys = list(axes)
        for combo in itertools.product(*(axes[k] for k in keys)):
            cells.append(dict(zip(keys, combo)))
    # GitHub semantics: `exclude` is applied to the base matrix first; every
    # include is processed after it, so an include can add a combination back.
    for exc in exclude:
        if isinstance(exc, dict):
            cells = [c for c in cells if not all(c.get(k) == v for k, v in exc.items())]
    # An include is matched against the ORIGINAL axis values only; on a match
    # its non-axis values are added, and a later include may overwrite a value
    # an earlier include added — axis values are never overwritten. An include
    # that matches no cell becomes a new cell.
    for inc in include:
        if not isinstance(inc, dict):
            continue
        inc_axes = {k: v for k, v in inc.items() if k in axis_keys}
        matched = False
        for cell in cells:
            if cell.get("_from_include"):
                continue
            if all(cell.get(k) == v for k, v in inc_axes.items()):
                cell.update({k: v for k, v in inc.items() if k not in axis_keys})
                matched = True
        if not matched:
            cells.append({**inc, "_from_include": True})
    out = []
    for cell in cells:
        cell.pop("_from_include", None)
        if job_name:
            display = substitute_matrix(str(job_name), cell)
        else:
            display = f"{job_id} ({', '.join(scalar(v) for v in cell.values())})"
        out.append({**cell, "display_name": display, "os_family": family_for_cell(runs_on, cell)})
    return out


def step_record(
    index: int,
    step: dict,
    *,
    defaults=None,
    env=None,
    family="unknown",
    container=False,
) -> dict:
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
    defaults = defaults or {}
    effective_shell = (
        step.get("shell") or defaults.get("shell") or default_shell(family, container)
    )
    effective_directory = (
        step.get("working-directory") or defaults.get("working-directory") or "."
    )
    effective_env = {**(env or {}), **(step.get("env") or {})}
    unresolved = sorted(
        set(
            re.findall(
                r"\$\{\{.*?\}\}",
                json.dumps([run, effective_shell, effective_directory, effective_env]),
            )
        )
    )
    return {
        "index": index,
        "display_name": display,
        "kind": "uses" if uses else ("run" if run is not None else "other"),
        "uses": uses,
        "run": run,
        "working_directory": step.get("working-directory"),
        "env": step.get("env") or {},
        "if": step.get("if"),
        "condition_state": constant_boolean(step.get("if"), True),
        "continue_on_error": step.get("continue-on-error", False),
        "continue_on_error_state": constant_boolean(
            step.get("continue-on-error"), False
        ),
        "shell": step.get("shell"),
        "setup": is_setup(run),
        "effective_shell": effective_shell,
        "effective_working_directory": effective_directory,
        "effective_env": effective_env,
        "unresolved_expressions": unresolved,
        "validation_kind": validation_kind(run, effective_shell),
    }


FILTER_KEYS = {
    "branches": "branches",
    "branches-ignore": "branches_ignore",
    "paths": "paths",
    "paths-ignore": "paths_ignore",
    "tags": "tags",
    "tags-ignore": "tags_ignore",
    "types": "types",
}


def trigger_filters_of(doc: dict) -> dict:
    """Per `push`/`pull_request`(-target) trigger: its branch, path, and event-type
    filters, so a caller can tell whether the pending event would start it."""
    on = doc.get("on", doc.get(True))
    out = {}
    if not isinstance(on, dict):
        return out
    for name in ("push", "pull_request", "pull_request_target"):
        if name in on:
            spec = on.get(name) or {}
            out[name] = {v: (spec.get(k) if isinstance(spec, dict) else None) for k, v in FILTER_KEYS.items()}
    return out


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
            doc = json_safe(yaml.safe_load(fh))
    except OSError as exc:
        raise SystemExit(f"error: cannot read {path}: {exc.strerror}") from exc
    except yaml.YAMLError as exc:
        raise SystemExit(f"error: {path} is not valid YAML: {exc}") from exc
    if not isinstance(doc, dict) or "jobs" not in doc:
        print(f"warning: {path} is not a workflow (no top-level mapping with `jobs`); skipped", file=sys.stderr)
        return None
    triggers, dispatch = triggers_of(doc)
    workflow_env = doc.get("env") or {}
    workflow_defaults = ((doc.get("defaults") or {}).get("run")) or {}
    jobs = []
    for job_id, job in (doc.get("jobs") or {}).items():
        job = job or {}
        runs_on = job.get("runs-on")
        job_defaults = {**workflow_defaults, **(((job.get("defaults") or {}).get("run")) or {})}
        strategy = job.get("strategy") or {}
        container = job.get("container")
        if isinstance(container, dict):
            container = container.get("image")
        needs = job.get("needs")
        if isinstance(needs, str):
            needs = [needs]
        job_env = {**workflow_env, **(job.get("env") or {})}
        jobs.append(
            {
                "id": str(job_id),
                "name": job.get("name"),
                "runs_on": runs_on,
                "if": job.get("if"),
                "condition_state": constant_boolean(job.get("if"), True),
                "environment": job.get("environment"),
                "continue_on_error": job.get("continue-on-error", False),
                "continue_on_error_state": constant_boolean(
                    job.get("continue-on-error"), False
                ),
                "os_family": os_family(runs_on),
                "needs": needs or [],
                "matrix": strategy.get("matrix")
                if isinstance(strategy, dict)
                else None,
                "matrix_cells": expand_matrix(
                    str(job_id),
                    runs_on,
                    strategy.get("matrix") if isinstance(strategy, dict) else None,
                    job.get("name"),
                ),
                "env": {
                    **{str(k): v for k, v in workflow_env.items()},
                    **{str(k): v for k, v in (job.get("env") or {}).items()},
                },
                "defaults_run": {
                    "working_directory": job_defaults.get("working-directory"),
                    "shell": job_defaults.get("shell"),
                },
                "container": container,
                "container_config": job.get("container"),
                "services": sorted((job.get("services") or {}).keys()),
                "service_configs": job.get("services") or {},
                "timeout_minutes": job.get("timeout-minutes"),
                "steps": [
                    step_record(
                        i,
                        s or {},
                        defaults=job_defaults,
                        env=job_env,
                        family=os_family(runs_on),
                        container=bool(container),
                    )
                    for i, s in enumerate(job.get("steps") or [])
                ],
            }
        )
    return {
        "path": path,
        "name": doc.get("name"),
        "triggers": triggers,
        "trigger_filters": trigger_filters_of(doc),
        "dispatch_inputs": dispatch,
        "jobs": jobs,
    }


def render_text(data: dict) -> str:
    lines = []
    for wf in data["workflows"]:
        base = os.path.basename(wf["path"])
        disp = f" inputs={','.join(wf['dispatch_inputs'])}" if wf["dispatch_inputs"] else ""
        lines.append(f"{base}  triggers={','.join(wf['triggers'])}{disp}")
        for j in wf["jobs"]:
            runs = sum(
                1
                for s in j["steps"]
                if j["condition_state"] is True
                and s["condition_state"] is True
                and s["validation_kind"] == "candidate"
                and not s["unresolved_expressions"]
            )
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
                f"steps={len(j['steps'])} validation-candidates={runs} {' '.join(extras)}".rstrip()
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
        data = {"workflows": [w for w in (inventory_file(f) for f in args.files) if w is not None]}
    except SystemExit as exc:
        print(exc, file=sys.stderr)
        return 2
    print(json.dumps(data, indent=2) if args.json else render_text(data))
    return 0


if __name__ == "__main__":
    sys.exit(main())
