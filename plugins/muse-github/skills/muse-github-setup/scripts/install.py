#!/usr/bin/env python3
"""Plan or apply Muse CI files to a local Git worktree; never changes GitHub."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

TEMPLATES = Path(__file__).resolve().parents[1] / "templates"
MARKER = "<!-- muse-github-setup:security:start -->"
TEMPLATE_FILES = (
    ".github/scripts/muse_ci.py", ".github/workflows/opencode-pr-review.yml",
    ".github/workflows/opencode-fix-pr.yml", ".opencode/muse-ci/review.json",
    ".opencode/muse-ci/fix.json", ".opencode/muse-ci/policy.json", ".opencode/muse-ci/NOTICE",
)


class Conflict(ValueError):
    pass


def destination(root: Path, name: str) -> Path:
    result = root / name
    current = result
    while current != root:
        if current.is_symlink():
            raise Conflict(f"Refusing a symlink at {current.relative_to(root)}")
        current = current.parent
    return result


def provider_merge(existing: dict, fragment: dict) -> dict:
    # Preserve unrelated provider definitions, default model, agents, and settings.
    merged = json.loads(json.dumps(existing))
    providers = merged.setdefault("provider", {})
    if not isinstance(providers, dict):
        raise Conflict("opencode.json provider must be an object")
    proposed = fragment["provider"]["model_api"]
    if "model_api" not in providers:
        providers["model_api"] = proposed
    elif providers["model_api"] != proposed:
        raise Conflict("Existing model_api provider differs; reconcile it explicitly without overwriting other settings")
    merged.setdefault("$schema", fragment["$schema"])
    return merged


def plan(root: Path, organization: str, with_fixes: bool = False) -> dict[str, str]:
    if not re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?", organization):
        raise Conflict("organization must be the actual GitHub organization login")
    result: dict[str, str] = {}
    for name in TEMPLATE_FILES:
        source = TEMPLATES / name
        if not with_fixes and (name.endswith("opencode-fix-pr.yml") or name.endswith("/fix.json")):
            continue
        body = source.read_text().replace("__MUSE_ORG__", organization)
        target = destination(root, name)
        if target.exists() and target.read_text() != body:
            raise Conflict(f"Existing {name} differs; preserve it and prepare a reviewed update")
        if not target.exists():
            result[name] = body
    if destination(root, "opencode.jsonc").exists():
        raise Conflict("Existing opencode.jsonc requires a manual provider merge; do not add a competing opencode.json")
    config = destination(root, "opencode.json")
    fragment = json.loads((TEMPLATES / "opencode.json").read_text())
    if config.exists():
        existing = json.loads(config.read_text())
        if not isinstance(existing, dict):
            raise Conflict("opencode.json must be an object")
        merged = provider_merge(existing, fragment)
        if merged != existing:
            result["opencode.json"] = json.dumps(merged, indent=2) + "\n"
    else:
        result["opencode.json"] = json.dumps(fragment, indent=2) + "\n"
    instructions = destination(root, "AGENTS.md")
    current = instructions.read_text() if instructions.exists() else ""
    security = (TEMPLATES / "AGENTS.muse.md").read_text()
    if MARKER in current:
        if security.strip() not in current:
            raise Conflict("Existing Muse AGENTS.md section differs; preserve its project-specific edits")
    else:
        result["AGENTS.md"] = current.rstrip() + ("\n\n" if current else "") + security
    return result


def apply(root: Path, changes: dict[str, str]) -> None:
    for name, content in changes.items():
        target = destination(root, name)
        target.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary = tempfile.mkstemp(prefix=".muse-install-", dir=target.parent)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as file:
                file.write(content)
            if target.exists():
                os.chmod(temporary, target.stat().st_mode & 0o777)
            else:
                os.chmod(temporary, 0o644)
            os.replace(temporary, target)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("worktree", type=Path)
    parser.add_argument("--organization", required=True)
    parser.add_argument("--with-fixes", action="store_true", help="Include the manual new-PR workflow")
    parser.add_argument("--apply", action="store_true", help="Write the listed files; default only prints a plan")
    args = parser.parse_args()
    root = args.worktree.resolve()
    try:
        probe = subprocess.run(["git", "-C", str(root), "rev-parse", "--show-toplevel"],
                               capture_output=True, text=True)
        if probe.returncode or Path(probe.stdout.strip()).resolve() != root:
            raise Conflict("worktree must name the Git repository root")
        changes = plan(root, args.organization, args.with_fixes)
        for name in changes:
            print(("update " if (root / name).exists() else "create ") + name)
        if args.apply:
            apply(root, changes)
        print(f"{'Applied' if args.apply else 'Planned'} {len(changes)} file changes. "
              "No secrets, GitHub settings, or workflow runs were changed.")
    except (OSError, ValueError) as error:
        print(f"Muse setup stopped: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
