#!/usr/bin/env python3
"""Validate an html-codesign INPUT spec JSON file.

Usage: validate_spec.py path/to/spec.json

Checks the codesign-spec contract defined in references/spec-format.md:
required fields, the ID grammar from references/id-grammar.md, global ID
uniqueness, section/choice number agreement, exclusive-section selection
counts, and the contexts ENVELOPE (exactly one per section; non-empty
summary and recommendation; resolvable `recommended` choice ids — the
free-form context body lives in the page, not this schema). Run it on the
spec BEFORE rendering (plan-validate-execute).

Inputs only: `codesign-answers` export documents are a different schema
(references/export-formats.md) and are rejected with a pointer — the engine
produces them mechanically, so they need no agent-facing validator.

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
CTX_RE = re.compile(r"^ctx-(\d{2})$")

errors: list[str] = []


def err(msg: str) -> None:
    errors.append(msg)


def validate(spec: dict[str, Any]) -> None:
    if spec.get("kind") == "codesign-answers":
        err(
            "this is a codesign-answers EXPORT, not an input spec —"
            " validate_spec.py checks inputs only (see references/export-formats.md)"
        )
        return
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

    # --- contexts layer: one context per section, required at generation ---
    sec_nums: dict[str, str] = {}  # section id -> zero-padded number
    sec_choice_ids: dict[str, set[str]] = {}  # section id -> its choice ids
    for sec in sections:
        if isinstance(sec, dict):
            sec = cast("dict[str, Any]", sec)
            sid = sec.get("id", "")
            m = SEC_RE.match(sid) if isinstance(sid, str) else None
            if m:
                sec_nums[sid] = m.group(1)
                chs = sec.get("choices")
                sec_choice_ids[sid] = {
                    c["id"]
                    for c in (chs if isinstance(chs, list) else [])
                    if isinstance(c, dict) and isinstance(c.get("id"), str)
                }

    contexts = spec.get("contexts")
    covered: dict[str, int] = dict.fromkeys(sec_nums, 0)
    if not isinstance(contexts, list) or not contexts:
        err(
            "contexts must be a non-empty array — every section needs a context"
            " (comprehensive view + argued recommendation); see spec-format.md"
        )
        contexts = []
    for i, ctx in enumerate(contexts):
        where = f"contexts[{i}]"
        if not isinstance(ctx, dict):
            err(f"{where}: context must be an object")
            continue
        ctx = cast("dict[str, Any]", ctx)
        xid = ctx.get("id", "")
        xm = CTX_RE.match(xid) if isinstance(xid, str) else None
        if not xm:
            err(f"{where}: context id {xid!r} does not match ctx-NN")
        else:
            claim(xid, where)
        target = ctx.get("section")
        if not isinstance(target, str) or target not in sec_nums:
            err(f"{where}: section {target!r} does not name an existing section")
            target = None
        else:
            covered[target] += 1
            if xm and xm.group(1) != sec_nums[target]:
                err(f"{where}: context {xid!r} numbered for a different section than {target!r}")
        # Envelope fields only. The context BODY is free-form HTML in the
        # page, outside this schema; a legacy v0.8.0 "body" key is ignored.
        for field in ("summary", "recommendation"):
            val = ctx.get(field)
            if not isinstance(val, str) or not val.strip():
                err(f"{where}: {field} must be a non-empty string")
            check_embeddable(val, f"{where}.{field}")
        rec = ctx.get("recommended")
        if not isinstance(rec, list):
            err(f"{where}: recommended must be an array of choice ids (may be empty)")
        elif target is not None:
            for rid in rec:
                if rid not in sec_choice_ids.get(target, set()):
                    err(f"{where}: recommended {rid!r} is not a choice in {target!r}")
    for sid, n in covered.items():
        if n == 0:
            err(f"section {sid!r} has no context — every section needs exactly one")
        elif n > 1:
            err(f"section {sid!r} has {n} contexts — every section needs exactly one")

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
