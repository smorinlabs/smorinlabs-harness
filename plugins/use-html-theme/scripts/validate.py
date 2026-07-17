#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Validate the use-html-theme plugin structure.

Exit code 0 if all checks pass, 1 otherwise. Prints one line per check.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
THEMES = ["birchline", "technical-minimal", "high-contrast-dark"]

failures: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    mark = "OK  " if ok else "FAIL"
    print(f"[{mark}] {label}" + (f" — {detail}" if detail else ""))
    if not ok:
        failures.append(label)


def file_exists(rel: str) -> bool:
    return (ROOT / rel).is_file()


def file_contains(rel: str, needle: str) -> bool:
    p = ROOT / rel
    if not p.is_file():
        return False
    return needle in p.read_text(encoding="utf-8")


def file_matches(rel: str, pattern: str) -> bool:
    p = ROOT / rel
    if not p.is_file():
        return False
    return bool(re.search(pattern, p.read_text(encoding="utf-8"), re.MULTILINE))


# 1. Plugin manifest (Claude Code convention: .claude-plugin/plugin.json)
manifest_rel = ".claude-plugin/plugin.json"
check("plugin.json exists", file_exists(manifest_rel))
if file_exists(manifest_rel):
    manifest = json.loads((ROOT / manifest_rel).read_text())
    check("plugin.json has name=use-html-theme", manifest.get("name") == "use-html-theme")
    check("plugin.json has version", "version" in manifest)

# 2. SKILL.md
skill_rel = "skills/use-html-theme/SKILL.md"
check("SKILL.md exists", file_exists(skill_rel))
check("SKILL.md has frontmatter name", file_matches(skill_rel, r"^name:\s*use-html-theme"))
check("SKILL.md has frontmatter description", file_matches(skill_rel, r"^description:"))

# 3. Reference files
for ref in ["activation-flow.md", "override-grammar.md", "persistence.md"]:
    check(f"references/{ref} exists", file_exists(f"skills/use-html-theme/references/{ref}"))

# 4. Preview template (rendered by the skill on a "preview the themes" request)
check("assets/preview-template.html exists", file_exists("assets/preview-template.html"))

# 6. Per-theme files
for theme in THEMES:
    base = f"skills/use-html-theme/references/themes/{theme}"
    for fname in ["tokens.md", "components.md", "anti-patterns.md", "example.html"]:
        check(f"{theme}/{fname} exists", file_exists(f"{base}/{fname}"))
    if theme == "birchline":
        check("birchline/illustrations.md exists", file_exists(f"{base}/illustrations.md"))
        svg_dir = ROOT / base / "illustrations"
        svgs = sorted(svg_dir.glob("*.svg")) if svg_dir.is_dir() else []
        check("birchline/illustrations/ has SVG sources", len(svgs) >= 1, detail=f"found {len(svgs)}")

    # tokens.md must contain a :root block
    check(
        f"{theme}/tokens.md has :root block",
        file_matches(f"{base}/tokens.md", r":root\s*\{"),
    )

    # example.html must declare color-scheme via meta
    check(
        f"{theme}/example.html declares color-scheme meta",
        file_matches(f"{base}/example.html", r'<meta\s+name="color-scheme"'),
    )

# 7. Per-theme smoke tests
def smoke_birchline() -> None:
    ex = "skills/use-html-theme/references/themes/birchline/example.html"
    text = (ROOT / ex).read_text(encoding="utf-8") if (ROOT / ex).is_file() else ""
    accent_count = len(re.findall(r'class="[^"]*\baccent\b[^"]*"', text))
    check(
        "birchline example: exactly one .accent span in body",
        accent_count == 1,
        detail=f"found {accent_count}",
    )
    check(
        "birchline example: no font-weight: bold",
        "font-weight: bold" not in text and "font-weight:bold" not in text,
    )
    check(
        "birchline example: no pure-black shadow rgba(0,0,0",
        "rgba(0,0,0" not in text.replace("rgba(0, 0, 0", "rgba(0,0,0"),
    )


def smoke_color_scheme_light(theme: str) -> None:
    ex = f"skills/use-html-theme/references/themes/{theme}/example.html"
    text = (ROOT / ex).read_text(encoding="utf-8") if (ROOT / ex).is_file() else ""
    check(
        f"{theme} example: meta color-scheme=light",
        'name="color-scheme" content="light"' in text,
    )


def smoke_color_scheme_dark(theme: str) -> None:
    ex = f"skills/use-html-theme/references/themes/{theme}/example.html"
    text = (ROOT / ex).read_text(encoding="utf-8") if (ROOT / ex).is_file() else ""
    check(
        f"{theme} example: meta color-scheme=dark",
        'name="color-scheme" content="dark"' in text,
    )


smoke_birchline()
smoke_color_scheme_light("birchline")
smoke_color_scheme_light("technical-minimal")
smoke_color_scheme_dark("high-contrast-dark")

# 8. html-codesign skill (interactive decision pages)
cd_base = "skills/html-codesign"
check("html-codesign/SKILL.md exists", file_exists(f"{cd_base}/SKILL.md"))
check(
    "html-codesign SKILL.md has frontmatter name",
    file_matches(f"{cd_base}/SKILL.md", r"^name:\s*html-codesign"),
)
check(
    "html-codesign SKILL.md has frontmatter description",
    file_matches(f"{cd_base}/SKILL.md", r"^description:"),
)
for ref in [
    "spec-format.md",
    "id-grammar.md",
    "export-formats.md",
    "iteration-loop.md",
    "theming.md",
]:
    check(f"html-codesign references/{ref} exists", file_exists(f"{cd_base}/references/{ref}"))
check(
    "html-codesign template exists",
    file_exists(f"{cd_base}/assets/codesign-template.html"),
)
check(
    "html-codesign template embeds codesign-spec tag",
    file_contains(f"{cd_base}/assets/codesign-template.html", 'id="codesign-spec"'),
)
check("html-codesign validator exists", file_exists(f"{cd_base}/scripts/validate_spec.py"))
for theme in THEMES:
    check(
        f"{theme} codesign overlay exists",
        file_exists(f"skills/use-html-theme/references/themes/{theme}/codesign.md"),
    )

vs_script = ROOT / cd_base / "scripts/validate_spec.py"
fx_good = ROOT / cd_base / "scripts/fixtures/valid-spec.json"
fx_bad = ROOT / cd_base / "scripts/fixtures/invalid-spec.json"
if vs_script.is_file() and fx_good.is_file() and fx_bad.is_file():
    r_good = subprocess.run(
        [sys.executable, str(vs_script), str(fx_good)], capture_output=True
    )
    r_bad = subprocess.run(
        [sys.executable, str(vs_script), str(fx_bad)], capture_output=True
    )
    check("validate_spec accepts valid fixture", r_good.returncode == 0)
    check(
        "validate_spec rejects invalid fixture",
        r_bad.returncode == 1,
        detail=f"exit {r_bad.returncode}",
    )
else:
    check("validate_spec fixtures present", False)

print()
if failures:
    print(f"FAILED: {len(failures)} check(s)")
    sys.exit(1)
print("PASSED: all checks")
sys.exit(0)
