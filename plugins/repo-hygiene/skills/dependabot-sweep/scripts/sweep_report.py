#!/usr/bin/env python3
"""Report renderer and approval presenter for dependabot-sweep, Slice 1.

Both render from the same record store. Every PR line leads with
human identity (org/repo#number plus title); bracketed stable ids ride
along as join keys for resumed runs, never as the headline.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sweep_coordinator import delivery_counts, run_ending  # noqa: E402
from sweep_core import (  # noqa: E402
    SEVERITY_RANK, STATE_REPORT_RANK, State, Store,
)


def authority_label(header) -> str:
    """The effective modes, rather than a misleading global default."""
    repositories = header.authority.get("repositories", {})
    modes = {policy.get("mode", "unknown") for policy in repositories.values()}
    return next(iter(modes)) if len(modes) == 1 else (
        "mixed authority" if modes else header.mode)


def repository_authority_lines(header) -> list:
    return [
        f"{repo}: mode {policy.get('mode', 'unknown')}; "
        f"repairs {', '.join(policy.get('repairs', [])) or 'none'}"
        for repo, policy in sorted(
            header.authority.get("repositories", {}).items())
    ]


def _counts(store: Store) -> dict:
    assert store.header is not None, "create_run first"
    counts = {"selected": len(store.header.scope_ids), "merged": 0,
              "closed": 0, "unknown": 0, "new": 0, "ready": 0,
              "waiting": 0, "blocked": 0, "needs_owner": 0}
    for card_id in store.header.scope_ids:
        state = store.cards[card_id].state
        if state == State.MERGED:
            counts["merged"] += 1
        elif state == State.CLOSED:
            counts["closed"] += 1
        elif state == State.UNKNOWN:
            counts["unknown"] += 1
        elif state == State.NEW:
            counts["new"] += 1
        elif state == State.READY:
            counts["ready"] += 1
        elif state == State.WAITING:
            counts["waiting"] += 1
        elif state == State.BLOCKED:
            counts["blocked"] += 1
        elif state == State.NEEDS_OWNER:
            counts["needs_owner"] += 1
    accounted = (counts["merged"] + counts["closed"] + counts["unknown"]
                 + counts["new"] + counts["ready"] + counts["waiting"]
                 + counts["blocked"] + counts["needs_owner"])
    assert accounted == counts["selected"], (
        f"report would not reconcile: {accounted} vs "
        f"{counts['selected']} selected")
    return counts


def _linked_replacements(store: Store) -> list:
    """Replacement cards outside the selected set: linked evidence for an
    original, never part of the denominator, but real PRs with state."""
    scope = set(store.header.scope_ids)
    return [c for c in store.cards.values()
            if c.replaces and c.id not in scope]


def _late_arrivals(store: Store) -> list:
    """Cards recorded after a fixed scope was taken: reported, not selected."""
    scope = set(store.header.scope_ids)
    return [c for c in store.cards.values()
            if not c.replaces and c.id not in scope]


def _visible(store: Store) -> list:
    """Selected cards first, then linked replacements."""
    return ([store.cards[i] for i in store.header.scope_ids]
            + _linked_replacements(store))


def _tag(card, store: Store) -> str:
    scope = store.header.scope_ids
    if card.replaces and card.id not in scope:
        return f"[{card.id}] replaces [{card.replaces}]"
    return f"[{card.id}]"


def _unresolved(store: Store) -> list:
    assert store.header is not None
    cards = [c for c in _visible(store) if c.state in STATE_REPORT_RANK]
    cards.sort(key=lambda c: (STATE_REPORT_RANK[c.state],
                              SEVERITY_RANK.get(c.severity, 99), c.id))
    return cards


def _evidence_refs(card) -> str:
    refs = [e.get("id", "?") for e in card.evidence]
    return ", ".join(refs) if refs else "none recorded"


ENDINGS = {"completed": "COMPLETE",
           "completed_with_exceptions": "WITH EXCEPTIONS",
           "incomplete": "INCOMPLETE"}


def _continuation_text(store: Store, continuation: str | None) -> str:
    """The explicit string wins; otherwise the run's recorded
    continuation. No record means none is running."""
    if continuation is None:
        recorded = store.header.continuation or {}
        kind = recorded.get("kind", "none")
        continuation = "none" if kind == "none" \
            else f"{kind}:{recorded.get('ref', '')}"
    if continuation == "none":
        return "Continuation: none running."
    if continuation.startswith("watcher:"):
        return (f"Continuation: active watcher "
                f"{continuation.split(':', 1)[1]}.")
    if continuation.startswith("scheduled:"):
        return (f"Continuation: scheduled invocation "
                f"{continuation.split(':', 1)[1]}.")
    return f"Continuation: {continuation}."


def render_report(store: Store, continuation: str | None = None) -> str:
    """Render the full end report. Unresolved first by consequence and
    owner, then prepared cards, then successes with merge evidence, then
    late arrivals, worker reconciliation, and one explicit continuation
    state. Delivered objectives are counted separately from the selected
    denominator: a merged replacement delivers its original's update."""
    assert store.header is not None, "create_run first"
    counts = _counts(store)
    delivered = delivery_counts(store)
    header = store.header
    open_total = (counts["unknown"] + counts["ready"] + counts["waiting"]
                  + counts["blocked"] + counts["needs_owner"])
    ending = ENDINGS[run_ending(store)]
    lines = [
        f"{header.run_id} {authority_label(header)} pass ended {ending}. "
        f"Selected {counts['selected']}; merged {counts['merged']}; "
        f"open {open_total}; unknown {counts['unknown']}; "
        f"unprocessed {counts['new']}. "
        f"Delivered {delivered['total']} (direct {delivered['direct']}, "
        f"via replacement {delivered['via_replacement']}).",
        "",
    ]
    authority_lines = repository_authority_lines(header)
    if authority_lines:
        lines += ["REPOSITORY AUTHORITY", *authority_lines, ""]
    unresolved = _unresolved(store)
    if unresolved:
        lines.append("UNRESOLVED (by consequence, then owner)")
        for card in unresolved:
            lines.append(f"{card.human_id} -- {card.state.value}, "
                         f"{card.severity} {_tag(card, store)}")
            reason = f"{card.reason_code} {card.reason_line}".strip()
            lines.append(f"  {reason or 'No reason recorded'}. "
                         f"Evidence: {_evidence_refs(card)}.")
            if card.action:
                lines.append(f"  Next: {card.action} Owner: "
                             f"{card.action_owner or 'unassigned'}. "
                             f"Resume: {card.resume_trigger or 'next run'}.")
            if card.issue_ids:
                lines.append(f"  Shared incident: "
                             f"{', '.join(card.issue_ids)}.")
        lines.append("")
    if store.issues:
        lines.append(f"INCIDENTS ({len(store.issues)})")
        for issue in sorted(store.issues.values(), key=lambda i: i.id):
            lines.append(f"[{issue.id}] affects {', '.join(issue.card_ids)} "
                         f"-- {issue.reason_code} {issue.claim}")
            lines.append(f"  Next: {issue.action} Owner: "
                         f"{issue.action_owner or 'unassigned'}.")
        lines.append("")
    prepared = [c for c in _visible(store) if c.state == State.READY]
    if prepared:
        lines.append(f"PREPARED ({len(prepared)})")
        for card in prepared:
            lines.append(f"{card.human_id} {_tag(card, store)}")
            lines.append(f"  {card.reason_line or 'No reason recorded'}. "
                         f"Evidence: {_evidence_refs(card)}.")
        lines.append("")
    merged = [c for c in _visible(store) if c.state == State.MERGED]
    if merged:
        lines.append(f"MERGED ({len(merged)})")
        for card in merged:
            tag = (f"[{card.id}] delivers [{card.replaces}]"
                   if card.replaces and card.id not in header.scope_ids
                   else f"[{card.id}]")
            lines.append(f"{card.human_id} {tag}")
            lines.append(f"  commit {card.merge_commit} at {card.merged_at}. "
                         f"Evidence: {_evidence_refs(card)}.")
        lines.append("")
    arrivals = _late_arrivals(store)
    if arrivals:
        lines.append(f"ARRIVED AFTER CUTOFF ({len(arrivals)}), not selected")
        for card in sorted(arrivals, key=lambda c: c.id):
            lines.append(f"{card.human_id} [{card.id}]")
        lines.append("")
    lines.append("WORKERS")
    if not store.diary:
        lines.append("No worker attempts recorded.")
    for attempt in sorted(store.diary.values(), key=lambda a: a.id):
        result = attempt.result or "still running"
        lines.append(f"{attempt.id} ({attempt.model or 'unassigned model'}): "
                     f"{result}; assigned {len(attempt.assigned)}, "
                     f"outstanding {len(attempt.outstanding)}.")
        if attempt.outstanding:
            lines.append(f"  Outstanding: {', '.join(attempt.outstanding)}.")
        if attempt.successor:
            lines.append(f"  Successor: {attempt.successor}.")
    lines.append("")
    lines.append(_continuation_text(store, continuation))
    return "\n".join(lines) + "\n"


def render_approval(store: Store) -> str:
    """Render the approval set: every NEEDS_OWNER card, most
    consequential first, each with the fixed 7-part decision block."""
    assert store.header is not None, "create_run first"
    needy = [store.cards[i] for i in store.header.scope_ids
             if store.cards[i].state == State.NEEDS_OWNER]
    if not needy:
        return "No approvals needed.\n"
    needy.sort(key=lambda c: (SEVERITY_RANK.get(c.severity, 99), c.id))
    lines = [f"APPROVAL NEEDED -- {len(needy)} PRs. "
             f"Start with #1: {needy[0].reason_line}",
             "Reply APPROVE <n|ALL> or DECLINE <n> <reason>.",
             ""]
    for pos, card in enumerate(needy, start=1):
        tag = "MOST URGENT -- " if pos == 1 else ""
        lines.append(f"#{pos} {tag}{card.human_id} [{card.id}]")
        decision = card.decision or {}
        lines.append(f"   Why you: {decision.get('why', card.reason_line)}")
        lines.append(f"   Approve -> "
                     f"{decision.get('approve_effect', 'not stated')}")
        lines.append(f"   Decline -> "
                     f"{decision.get('decline_effect', 'not stated')}")
        lines.append(f"   Risk: {card.severity}, {card.confidence}. "
                     f"Evidence: {_evidence_refs(card)}.")
        lines.append(f"   Recommend: "
                     f"{decision.get('recommendation', 'not stated')}")
        lines.append("")
    return "\n".join(lines)
