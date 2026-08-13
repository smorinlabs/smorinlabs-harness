#!/usr/bin/env python3
"""Compact digest of a Claude Code session transcript (JSONL).

Session transcripts can be several megabytes — far too large to read into
context whole. This script extracts only what a recap needs and prints a small
text digest: the session title, the opening prompt, compaction boundaries,
branch changes, timing, and the last handful of turns leading up to now.

Locate the transcript by session id (preferred — deterministic):

    transcript_digest.py --session "$CLAUDE_CODE_SESSION_ID"

or point at a file directly (used by tests and for recapping a specific run):

    transcript_digest.py path/to/transcript.jsonl

Tune how many trailing turns to show with --last (default 8). For long/multi-day
recaps, pass --prompts-only to list the human's substantive prompts instead —
these mark the boundaries between features/topics of work. Stdlib only, so it
runs anywhere python3 does, with no dependencies to install.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

# Tool results and pasted blobs can be enormous; clamp every quoted snippet so
# the digest stays small no matter what the turn contained.
SNIPPET = 220

# References worth surfacing on open items so the recap can point at the goal's
# source of truth. Ticket ids (Linear/Jira-style), URLs, and spec/doc files.
TICKET_RE = re.compile(r"\b[A-Z][A-Z0-9]{1,9}-\d+\b")
URL_RE = re.compile(r"https?://[^\s)\]>'\"]+")
DOC_RE = re.compile(r"\b[\w./-]+\.(?:md|mdx|rst|adoc)\b")
# Common technical tokens that look like tickets but aren't.
TICKET_DENY = {"UTF", "SHA", "ISO", "RFC", "AES", "RSA", "ASCII", "IPV", "ID", "PKCS"}


def find_refs(text: str, tickets: set[str], urls: set[str], docs: set[str]) -> None:
    for m in TICKET_RE.findall(text):
        if m.split("-")[0] not in TICKET_DENY:
            tickets.add(m)
    for m in URL_RE.findall(text):
        urls.add(m.rstrip(".,;"))
    for m in DOC_RE.findall(text):
        docs.add(m)


def locate(session_id: str) -> Path | None:
    """Find the transcript named by a session id across all project dirs.

    Session ids are UUIDs, so at most one file matches — which sidesteps having
    to reconstruct the cwd→project-dir path encoding.
    """
    home = Path.home()
    matches = glob.glob(str(home / ".claude" / "projects" / "*" / f"{session_id}.jsonl"))
    if not matches:
        return None
    return Path(max(matches, key=lambda p: os.path.getmtime(p)))


def text_of(content) -> str:
    """Flatten a message's content into a short human-readable line.

    Content is either a plain string or a list of typed blocks (text, tool_use,
    tool_result). We surface text and tool names, skip bulky tool output, and
    truncate — the goal is a recognizable gist, not a faithful copy.
    """
    if isinstance(content, str):
        return content.strip()
    if not isinstance(content, list):
        return ""
    parts: list[str] = []
    for block in content:
        if not isinstance(block, dict):
            continue
        btype = block.get("type")
        if btype == "text":
            parts.append(block.get("text", "").strip())
        elif btype == "tool_use":
            parts.append(f"[tool: {block.get('name', '?')}]")
        elif btype == "tool_result":
            parts.append("[tool result]")
    return " ".join(p for p in parts if p).strip()


def clip(s: str, n: int = SNIPPET) -> str:
    s = " ".join(s.split())
    return s if len(s) <= n else s[: n - 1] + "…"


def stamp_md_hm(ts: str) -> str:
    """Format an ISO timestamp as 'MM-DD HH:MM' for cross-day views."""
    return ts[5:16].replace("T", " ") if len(ts) >= 16 else ts


# Noise that shows up as "user" turns but isn't a human directive: rendered tool
# results/calls, slash-command wrappers, system reminders, skill preambles.
_NOISE_PREFIXES = (
    "[",
    "<command",
    "<local-command",
    "<system-reminder",
    "Base directory for this skill",
)


def is_human_prompt(role: str, body: str) -> bool:
    """A substantive human turn — what marks the boundaries of a work group."""
    return role == "user" and bool(body) and not body.startswith(_NOISE_PREFIXES)


def day_segments(
    turns: list[tuple[str, str, str]],
) -> list[tuple[str, str, str, int, int]]:
    """Group turns into day segments, splitting on a >4h gap even within a day.

    Returns (date, start_hm, end_hm, turn_count, prompt_count) tuples, in
    chronological order.
    """
    segments: list[list] = []
    prev_dt = None
    for ts, role, body in turns:
        if len(ts) < 16:
            continue
        try:
            dt = datetime.fromisoformat(ts)
        except ValueError:
            continue
        date = ts[:10]
        gap_too_big = prev_dt is not None and (dt - prev_dt).total_seconds() > 4 * 3600
        if not segments or segments[-1][0] != date or gap_too_big:
            segments.append([date, ts, ts, 0, 0])
        seg = segments[-1]
        seg[2] = ts
        seg[3] += 1
        if is_human_prompt(role, body):
            seg[4] += 1
        prev_dt = dt
    return [
        (date, start[11:16], end[11:16], turn_count, prompt_count)
        for date, start, end, turn_count, prompt_count in segments
    ]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("path", nargs="?", help="transcript .jsonl path")
    ap.add_argument("--session", help="session id (e.g. $CLAUDE_CODE_SESSION_ID)")
    ap.add_argument("--last", type=int, default=8, help="trailing turns to show")
    ap.add_argument(
        "--prompts-only",
        action="store_true",
        help="list the human's substantive prompts (group/phase boundaries) instead of trailing turns; for long/multi-day recaps",
    )
    ap.add_argument("--prompts", type=int, default=40, help="max prompts to show in --prompts-only")
    ap.add_argument(
        "--scope",
        action="store_true",
        help="cwd/branch/worktree timeline instead of the default trailing-turns view",
    )
    ap.add_argument(
        "--days",
        action="store_true",
        help="per-day activity stats (gap-split >4h) instead of the default trailing-turns view",
    )
    ap.add_argument(
        "--find",
        action="append",
        metavar="TEXT",
        help="case-insensitive substring search over turn text (repeatable); replaces the default view",
    )
    args = ap.parse_args(argv)

    path: Path | None = None
    if args.path:
        path = Path(args.path)
    elif args.session:
        path = locate(args.session)
    elif os.environ.get("CLAUDE_CODE_SESSION_ID"):
        path = locate(os.environ["CLAUDE_CODE_SESSION_ID"])

    if path is None or not path.exists():
        print("NO_TRANSCRIPT", file=sys.stderr)
        return 2

    title = None
    first_user = None
    turns: list[tuple[str, str, str]] = []  # (ts, role, text)
    turns_full: list[str] = []  # unclipped flattened text, parallel to turns
    branches: list[str] = []
    summaries = 0
    first_ts = last_ts = None
    tickets: set[str] = set()
    urls: set[str] = set()
    docs: set[str] = set()
    prompts: list[tuple[str, str]] = []  # (ts, body) of substantive human turns
    scope_order: list[tuple[str, str]] = []  # (cwd, branch) pairs, first-seen order
    scope_spans: dict[tuple[str, str], list[str]] = {}  # pair -> [first_ts, last_ts]
    worktree_state_events = 0
    relocations = 0

    for line in path.read_text(errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        if d.get("isSidechain"):
            continue
        rtype = d.get("type")
        if rtype == "ai-title":
            title = d.get("aiTitle") or d.get("title") or title
            continue
        if rtype == "summary":
            summaries += 1
            continue
        if rtype == "worktree-state":
            worktree_state_events += 1
            continue
        if rtype == "relocated":
            relocations += 1
            continue
        if rtype not in ("user", "assistant"):
            continue

        ts = d.get("timestamp") or ""
        if ts:
            first_ts = first_ts or ts
            last_ts = ts
        branch = d.get("gitBranch")
        if branch and (not branches or branches[-1] != branch):
            branches.append(branch)
        cwd = d.get("cwd")
        if ts and cwd and branch:
            pair = (cwd, branch)
            span = scope_spans.get(pair)
            if span is None:
                scope_spans[pair] = [ts, ts]
                scope_order.append(pair)
            else:
                span[1] = ts

        msg = d.get("message") or {}
        role = msg.get("role", rtype)
        full = text_of(msg.get("content"))
        if full:
            find_refs(full, tickets, urls, docs)
        body = clip(full)
        if not body:
            continue
        if is_human_prompt(role, body):
            if first_user is None:
                first_user = body
            prompts.append((ts, body))
        turns.append((ts, role, body))
        turns_full.append(full)

    out: list[str] = []
    out.append(f"session_file: {path.name}")
    if title:
        out.append(f"title: {title}")
    out.append(f"first_activity: {first_ts or '?'}")
    out.append(f"last_activity: {last_ts or '?'}")
    out.append(f"total_turns: {len(turns)}")
    if summaries:
        out.append(
            f"compaction_markers: {summaries}  (early context was condensed — "
            "this digest reads the raw file, so the opening below is recovered)"
        )
    if branches:
        out.append(f"branches_seen: {' -> '.join(branches)}")
    if tickets or urls or docs:
        out.append("")
        out.append("=== references mentioned (link open items to these) ===")
        if tickets:
            out.append("tickets: " + ", ".join(sorted(tickets)))
        if docs:
            out.append("docs/specs: " + ", ".join(sorted(docs)[:10]))
        if urls:
            out.append("urls: " + ", ".join(sorted(urls)[:10]))
    out.append("")
    out.append("=== opening prompt ===")
    out.append(clip(first_user or "(none found)", 400))

    extra_views = args.scope or args.days or bool(args.find)
    if extra_views:
        if args.scope:
            out.append("")
            out.append("=== scope history (sidechain excluded) ===")
            for cwd, branch in scope_order:
                first, last = scope_spans[(cwd, branch)]
                if first == last:
                    span = f"[{stamp_md_hm(first)}]"
                else:
                    span = f"[{stamp_md_hm(first)} → {stamp_md_hm(last)}]"
                out.append(f"{span} {cwd} · {branch}")
            out.append(
                f"worktree-state events: {worktree_state_events} · relocations: {relocations}"
            )
        if args.days:
            out.append("")
            out.append("=== activity by day (gaps >4h split) ===")
            for date, start_hm, end_hm, turn_count, prompt_count in day_segments(turns):
                out.append(
                    f"{date}  {start_hm}–{end_hm} · {turn_count} turns · {prompt_count} prompts"
                )
        for pattern in args.find or []:
            needle = pattern.lower()
            matches = [
                (ts, role, body)
                for (ts, role, body), full in zip(turns, turns_full)
                if needle in full.lower()
            ]
            out.append("")
            out.append(f'=== matches for "{pattern}" ({len(matches)}) ===')
            for ts, role, body in matches:
                out.append(f"[{stamp_md_hm(ts)} {role}] {body}")
    elif args.prompts_only:
        # Group/phase boundaries come from the human's directives, not tool
        # noise. Date+time stamps because a session can span days.
        shown = prompts[-args.prompts :]
        out.append("")
        out.append(
            f"=== human prompts ({len(shown)} of {len(prompts)}) — group/phase boundaries ==="
        )
        for ts, body in shown:
            out.append(f"[{stamp_md_hm(ts)}] {clip(body, 280)}")
    else:
        out.append("")
        out.append(f"=== last {args.last} turns ===")
        for ts, role, body in turns[-args.last :]:
            stamp = ts[11:19] if len(ts) >= 19 else ts
            out.append(f"[{stamp} {role}] {body}")

    print("\n".join(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
