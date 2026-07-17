#!/usr/bin/env python3
"""Validate an html-codesign spec (or export) JSON file.

Usage: validate_spec.py path/to/spec.json

Checks the codesign-spec contract defined in references/spec-format.md:
required fields, the ID grammar from references/id-grammar.md, global ID
uniqueness, section/choice number agreement, and exclusive-section selection
counts. Run it on the spec BEFORE rendering (plan-validate-execute) and on
any exported JSON to lint a round-trip.

Exit codes: 0 = valid · 1 = validation errors (printed to stderr) ·
2 = usage or JSON parse error. Stdlib only.
"""

from __future__ import annotations

import json
import re
import sys
from typing import Any, cast

SEC_RE = re.compile(r"^sec-(\d{2})-[a-z0-9]+(?:-[a-z0-9]+)*$")
CH_RE = re.compile(r"^ch-(\d{2})-[a-z]$")
NOTE_RE = re.compile(r"^note-(\d{2})$")

errors: list[str] = []


def err(msg: str) -> None:
    errors.append(msg)


def validate(spec: dict[str, Any]) -> None:
    if spec.get("version") != "1":
        err(f'version must be "1", got {spec.get("version")!r}')
    if spec.get("skill") != "html-codesign":
        err(f'skill must be "html-codesign", got {spec.get("skill")!r}')
    if spec.get("mode") != "codesign":
        err(f'mode must be "codesign", got {spec.get("mode")!r}')
    if not isinstance(spec.get("title"), str) or not spec["title"].strip():
        err("title must be a non-empty string")

    sections = spec.get("sections")
    if not isinstance(sections, list) or not sections:
        err("sections must be a non-empty array")
        return

    seen_ids: set[str] = set()
    seen_sec_nums: set[str] = set()

    def check_embeddable(value: object, where: str) -> None:
        # A literal "</script" in any string would truncate the embedded
        # <script id="codesign-spec"> tag and kill the page after validation.
        if isinstance(value, str) and "</script" in value.lower():
            err(f"{where}: string contains '</script' — breaks the embedded spec tag; rephrase it")

    check_embeddable(spec.get("title"), "title")
    check_embeddable(spec.get("lead"), "lead")

    def claim(eid: str, where: str) -> None:
        if eid in seen_ids:
            err(f"duplicate id {eid!r} ({where})")
        seen_ids.add(eid)

    for i, sec in enumerate(sections):
        where = f"sections[{i}]"
        if not isinstance(sec, dict):
            err(f"{where}: section must be an object")
            continue
        sec = cast("dict[str, Any]", sec)
        sid = sec.get("id", "")
        m = SEC_RE.match(sid) if isinstance(sid, str) else None
        if not m:
            err(f"{where}: section id {sid!r} does not match sec-NN-slug")
            sec_num = None
        else:
            sec_num = m.group(1)
            claim(sid, where)
            if sec_num in seen_sec_nums:
                err(
                    f"{where}: section number {sec_num!r} already used — bare"
                    f" references like sec-{sec_num} and note-{sec_num} would be ambiguous"
                )
            seen_sec_nums.add(sec_num)
        check_embeddable(sec.get("title"), f"{where}.title")
        check_embeddable(sec.get("lead"), f"{where}.lead")
        if not isinstance(sec.get("title"), str) or not sec["title"].strip():
            err(f"{where}: title must be a non-empty string")
        if not isinstance(sec.get("exclusive"), bool):
            err(f"{where}: exclusive must be true or false")

        choices = sec.get("choices")
        if not isinstance(choices, list) or not choices:
            err(f"{where}: choices must be a non-empty array")
            choices = []
        selected_count = 0
        for j, ch in enumerate(choices):
            cwhere = f"{where}.choices[{j}]"
            if not isinstance(ch, dict):
                err(f"{cwhere}: choice must be an object")
                continue
            ch = cast("dict[str, Any]", ch)
            cid = ch.get("id", "")
            cm = CH_RE.match(cid) if isinstance(cid, str) else None
            if not cm:
                err(f"{cwhere}: choice id {cid!r} does not match ch-NN-a")
            else:
                claim(cid, cwhere)
                if sec_num and cm.group(1) != sec_num:
                    err(f"{cwhere}: choice {cid!r} numbered for a different section than {sid!r}")
            label = ch.get("label")
            if not isinstance(label, str) or not label.strip():
                err(f"{cwhere}: label must be a non-empty string")
            elif len(label) > 120:
                err(f"{cwhere}: label exceeds 120 chars")
            check_embeddable(label, f"{cwhere}.label")
            check_embeddable(ch.get("detail"), f"{cwhere}.detail")
            if not isinstance(ch.get("selected", False), bool):
                err(f"{cwhere}: selected must be boolean")
            if ch.get("selected") is True:
                selected_count += 1
        if sec.get("exclusive") is True and selected_count > 1:
            err(f"{where}: exclusive section has {selected_count} selected choices (max 1)")

        note = sec.get("note")
        if note is not None:
            nid = note.get("id", "") if isinstance(note, dict) else ""
            nm = NOTE_RE.match(nid) if isinstance(nid, str) else None
            if not nm:
                err(f"{where}: note id {nid!r} does not match note-NN")
            else:
                claim(nid, f"{where}.note")
                if sec_num and nm.group(1) != sec_num:
                    err(f"{where}: note {nid!r} numbered for a different section than {sid!r}")
            if isinstance(note, dict):
                check_embeddable(note.get("placeholder"), f"{where}.note.placeholder")
                check_embeddable(note.get("value"), f"{where}.note.value")

    fb = spec.get("feedback")
    if fb is not None:
        if not isinstance(fb, dict) or fb.get("id") != "note-overall":
            err('feedback.id must be "note-overall"')
        if isinstance(fb, dict):
            check_embeddable(fb.get("value"), "feedback.value")


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: validate_spec.py path/to/spec.json", file=sys.stderr)
        return 2
    try:
        with open(sys.argv[1], encoding="utf-8") as f:
            spec = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        print(f"cannot read spec: {e}", file=sys.stderr)
        return 2
    if not isinstance(spec, dict):
        print("spec root must be a JSON object", file=sys.stderr)
        return 2
    validate(spec)
    if errors:
        for e in errors:
            print(f"ERROR: {e}", file=sys.stderr)
        print(f"\nINVALID: {len(errors)} error(s)", file=sys.stderr)
        return 1
    print("VALID: all checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
