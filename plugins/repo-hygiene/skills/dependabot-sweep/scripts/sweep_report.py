#!/usr/bin/env python3
"""Complete human reports and scoped decision presentation from one snapshot.

The structured snapshot is the common source for saved and inline output.
Every selected, replacement, and unselected arrival has its own result and
continuation. Follow-ups remain visible independently of PR delivery.
"""

from __future__ import annotations

import copy
import json
import os
import sys
from collections import Counter
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sweep_coordinator import delivery_counts, run_ending  # noqa: E402
from sweep_core import SEVERITY_RANK, State, Store, utc_now  # noqa: E402

ENDINGS = {"completed": "COMPLETE", "completed_with_exceptions": "WITH EXCEPTIONS",
           "incomplete": "INCOMPLETE"}


def authority_label(header) -> str:
    """The effective modes, rather than a misleading global default."""
    repositories = header.authority.get("repositories", {})
    modes = {policy.get("mode", "unknown") for policy in repositories.values()}
    return next(iter(modes)) if len(modes) == 1 else (
        "mixed authority" if modes else header.mode)


def repository_authority_lines(header) -> list:
    return [f"{repo}: mode {policy.get('mode', 'unknown')}; "
            f"repairs {', '.join(policy.get('repairs', [])) or 'none'}"
            for repo, policy in sorted(header.authority.get("repositories", {}).items())]


def _linked_replacements(store: Store) -> list:
    scope = set(store.header.scope_ids)
    return [c for c in store.cards.values() if c.replaces and c.id not in scope]


def _late_arrivals(store: Store) -> list:
    scope = set(store.header.scope_ids)
    return [c for c in store.cards.values() if not c.replaces and c.id not in scope]


def _visible(store: Store) -> list:
    return [store.cards[i] for i in store.header.scope_ids] + _linked_replacements(store)


def _replacement_delivered(card, store: Store) -> bool:
    replacement = store.cards.get(card.replaced_by)
    return bool(card.state == State.CLOSED and replacement
                and replacement.state == State.MERGED and replacement.replaces == card.id)


def _counts(store: Store) -> dict:
    counts = dict.fromkeys(("selected", "direct_merged", "delivered_via_replacement",
                            "closed_without_delivery", "assessed_holds", "prepared",
                            "unassessed", "unknown"), 0)
    counts["selected"] = len(store.header.scope_ids)
    for card_id in store.header.scope_ids:
        card = store.cards[card_id]
        if card.state == State.MERGED:
            key = "direct_merged"
        elif card.state == State.CLOSED:
            key = ("delivered_via_replacement" if _replacement_delivered(card, store)
                   else "closed_without_delivery")
        else:
            key = {State.NEW: "unassessed", State.READY: "prepared",
                   State.UNKNOWN: "unknown"}.get(card.state, "assessed_holds")
        counts[key] += 1
    assert sum(v for k, v in counts.items() if k != "selected") == counts["selected"]
    return counts


def _live_open_count(store: Store) -> dict:
    snapshot = copy.deepcopy(getattr(store.header, "discovery_snapshot", {}) or {})
    result = {"count": None, "observed_at": snapshot.get("observed_at", ""),
              "reason": "no complete current scope-bound discovery snapshot recorded"}
    if not snapshot:
        return result
    scope = set(store.header.scope_ids)
    repositories = set(store.header.authority.get("repositories", {}))
    ids, repos = snapshot.get("scope_ids"), snapshot.get("scope_repositories")
    open_ids = snapshot.get("open_card_ids")
    observed = _timestamp(snapshot.get("observed_at"))
    newer = any(moment is not None and observed is not None and moment > observed
                for card in store.cards.values()
                for moment in (_timestamp(card.last_observation),
                               _timestamp(getattr(card, "discovered_at", "")),
                               _timestamp((getattr(card, "latest_observation", {}) or {}).get("observed_at")),
                               _timestamp(card.merged_at)))
    if snapshot.get("complete") is not True or not store.header.discovery_complete:
        result["reason"] = "latest discovery snapshot is incomplete"
    elif observed is None or not isinstance(snapshot.get("source"), str) or not snapshot["source"].strip():
        result["reason"] = "discovery observation time or source is missing"
    elif not _distinct_strings(ids) or set(ids) != scope \
            or not _distinct_strings(repos) \
            or set(repos) != repositories:
        result["reason"] = "discovery snapshot is stale for the current selected scope or authority"
    elif not _coverage_matches(snapshot.get("coverage"), store.header.authority):
        result["reason"] = "discovery coverage does not match the frozen selectors"
    elif not repositories and not store.header.authority.get("discovery_scopes"):
        result["reason"] = "repository coverage is not bound to saved authority"
    elif not _distinct_strings(open_ids) \
            or any(i not in store.cards or store.cards[i].repo_id not in repositories for i in open_ids):
        result["reason"] = "discovery snapshot contains unknown or out-of-scope open identities"
    elif newer:
        result["reason"] = "discovery snapshot predates a newer PR observation or arrival"
    else:
        result.update(count=len(open_ids), reason="complete scope-bound discovery",
                      source=snapshot["source"], open_card_ids=open_ids)
    return result


def _distinct_strings(value) -> bool:
    return isinstance(value, list) and all(isinstance(i, str) for i in value) \
        and len(value) == len(set(value))


def _timestamp(value):
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.timestamp() if parsed.tzinfo else None
    except ValueError:
        return None


def _coverage_matches(actual, authority: dict) -> bool:
    """Match frozen selectors without interpreting them as new grants."""
    if not isinstance(actual, list) or not all(isinstance(i, dict) for i in actual):
        return False
    expected = authority.get("discovery_scopes")
    if "discovery_scopes" in authority:
        if not isinstance(expected, list) or not all(isinstance(i, dict) for i in expected):
            return False
        keys = ("kind", "login", "visibility", "repos")
        if any(not all(key in item for key in keys) for item in expected):
            return False
        expected = [{key: item[key] for key in keys} for item in expected]
    else:
        expected = [{"kind": "repo", "login": repo.split("/", 1)[0],
                     "visibility": "all", "repos": [repo.split("/", 1)[1]]}
                    for repo in authority.get("repositories", {})]
    def normalized(items):
        values = []
        for item in items:
            item = copy.deepcopy(item)
            if isinstance(item.get("repos"), list) and all(isinstance(i, str) for i in item["repos"]):
                item["repos"] = sorted(item["repos"])
            values.append(json.dumps(item, sort_keys=True))
        return sorted(values)
    return normalized(actual) == normalized(expected)


def _evidence_head(item: dict) -> str:
    return str(item.get("head_sha") or item.get("head") or "").lower()


def _continuation_text(header, override: str | None) -> str:
    recorded = header.continuation or {}
    if override == "none" or (override is None and recorded.get("kind", "none") == "none"):
        return "Continuation: none running."
    reference = (override if override is not None else
                 f"{recorded.get('kind', 'unknown')}:{recorded.get('ref', '')}")
    matches = override is None or reference == f"{recorded.get('kind')}:{recorded.get('ref', '')}"
    if matches and recorded.get("verified_at") and recorded.get("ref"):
        return (f"Continuation: {reference}; verified at {recorded['verified_at']}. "
                "Status is established at that observation time.")
    return f"Continuation: {reference}; unverified, no running continuation established."


def _next_action(card, store: Store) -> tuple:
    if card.state == State.MERGED:
        linked = [i for i in card.issue_ids if i in store.issues
                  and store.issues[i].status not in ("resolved", "dismissed")]
        action = (f"Complete linked follow-ups {', '.join(linked)}" if linked else
                  "Retain the merge receipt; verify post-merge CI if no receipt is recorded")
        return action, "sweeper", "post-merge evidence or linked follow-up completion"
    if card.state == State.CLOSED:
        if _replacement_delivered(card, store):
            return (f"Retain delivery evidence from replacement {card.replaced_by}",
                    "sweeper", "no further merge action on this closed PR")
        return (card.action or "Confirm whether the update still needs a replacement PR",
                card.action_owner or "repository maintainer",
                card.resume_trigger or "a separately authorized replacement or closure disposition")
    if card.state == State.NEW:
        return (card.action or "Assess this PR in an authorized pass; readiness is not established",
                card.action_owner or "sweeper", card.resume_trigger or "available authorized execution budget")
    if card.state == State.UNKNOWN:
        return ("Reconcile the uncertain operation read-only before any retry",
                card.action_owner or "sweeper", "verified remote mutation state")
    if card.state == State.READY:
        return (card.action or "Run fresh same-head gates in the next authorized merge attempt",
                card.action_owner or "sweeper", card.resume_trigger or "fresh gates and required authority")
    return (card.action or "Recommendation missing from legacy record; establish current gates and a concrete action",
            card.action_owner or "unassigned", card.resume_trigger or "resume evidence not recorded")


def _card_row(card, store: Store, role: str) -> dict:
    row = card.to_dict()
    row["decision"] = _decision_view(card.decision)
    row.update(repo_id=card.repo_id, human_id=card.human_id, role=role)
    row["saved_authority_hold"] = card.id in store.header.authority.get("holds", [])
    latest = copy.deepcopy(getattr(card, "latest_observation", {}) or {})
    observed_head = str(latest.get("observed_head", "")).lower()
    evaluated_head = card.head_sha.lower()
    observed_at, evaluated_at = _timestamp(latest.get("observed_at")), _timestamp(card.last_observation)
    newer_observation = observed_at is not None and (evaluated_at is None or observed_at >= evaluated_at)
    effective_head = (observed_head if newer_observation else "") or evaluated_head
    row["latest_observation"] = latest
    row["effective_head"] = effective_head
    row["head_drift"] = bool(newer_observation and observed_head and observed_head != evaluated_head)
    row["current_evidence"], row["historical_evidence"] = [], []
    for item in card.evidence:
        # A raw refresh is separately summarized. It is not an evaluation or
        # readiness receipt, even when its head matches the evaluated head.
        if item.get("kind") == "read_only_refresh":
            continue
        target = "current_evidence" if effective_head and _evidence_head(item) == effective_head else "historical_evidence"
        row[target].append(copy.deepcopy(item))
    blockers = copy.deepcopy(card.blockers)
    if not blockers and card.state in (State.WAITING, State.BLOCKED, State.NEEDS_OWNER) \
            and card.reason_code and card.reason_code != "K14":
        blockers = [{"reason_code": card.reason_code, "reason_line": card.reason_line,
                     "head_sha": card.head_sha, "legacy": True}]
    row["current_blockers"], row["historical_blockers"] = [], []
    for blocker in blockers:
        head = _evidence_head(blocker)
        target = "historical_blockers" if head and head != effective_head else "current_blockers"
        row[target].append(blocker)
    if not row["execution_stop"] and card.reason_code == "K14":
        row["execution_stop"] = {"reason_code": "K14", "reason_line": card.reason_line}
    row["next_action"], row["next_owner"], row["next_trigger"] = _next_action(card, store)
    row["delivered_via_replacement"] = _replacement_delivered(card, store)
    if card.state == State.CLOSED:
        row["result"] = (f"CLOSED; delivered via replacement {card.replaced_by}"
                         if row["delivered_via_replacement"] else "CLOSED without delivery")
    elif card.state == State.NEW:
        row["result"] = "NEW; unassessed"
    elif card.state == State.UNKNOWN:
        row["result"] = "UNKNOWN; mutation outcome requires reconciliation"
    else:
        row["result"] = card.state.value
    return row


def report_snapshot(store: Store, continuation: str | None = None) -> dict:
    """Capture the complete serializable human result once, without writes.

    A caller can render/save/print this exact snapshot even if the live store
    later changes. Discovery and read-only observations never replace assessed
    state or confer readiness. Live open counts require current scope binding.
    """
    assert store.header is not None, "create_run first"
    cards = [_card_row(store.cards[i], store, "selected") for i in store.header.scope_ids]
    cards += [_card_row(c, store, "replacement") for c in sorted(_linked_replacements(store), key=lambda c: c.id)]
    cards += [_card_row(c, store, "arrival") for c in sorted(_late_arrivals(store), key=lambda c: c.id)]
    continuation_text = _continuation_text(store.header, continuation)
    unfinished = sum(not attempt.result for attempt in store.diary.values())
    if unfinished and continuation_text == "Continuation: none running.":
        continuation_text = (f"Continuation: no watcher or scheduled invocation recorded; {unfinished} "
                             "worker attempts have no final result, liveness unverified.")
    return copy.deepcopy({
        "run_id": store.header.run_id, "authority": authority_label(store.header),
        "authorization": store.header.authorization, "observed_at": utc_now(),
        "ending": ENDINGS[run_ending(store)], "counts": _counts(store),
        "delivery": delivery_counts(store), "live_open": _live_open_count(store),
        "authority_lines": repository_authority_lines(store.header), "cards": cards,
        "followups": [i.to_dict() for i in sorted(store.issues.values(), key=lambda i: i.id)],
        "approval_groups": approval_groups(store),
        "workers": [a.to_dict() for a in sorted(store.diary.values(), key=lambda a: a.id)],
        "continuation": continuation_text,
    })


def _evidence_lines(records: list, label: str) -> list:
    if not records:
        return [f"  {label}: none recorded."]
    lines = []
    for item in records:
        parts = [str(item.get("id", "unidentified receipt"))]
        for key in ("what", "establishes"):
            value = item.get(key)
            if value and str(value) not in parts:
                parts.append(str(value))
        for key in ("url", "link", "path"):
            if item.get(key):
                parts.append(str(item[key]))
        if len(parts) == 1:
            parts.append("supporting facts missing from legacy record")
        parts.append(f"head {_evidence_head(item) or 'unbound'}")
        lines.append(f"  {label}: " + "; ".join(parts) + ".")
    return lines


def _observation_line(latest: dict) -> str:
    snapshot = latest.get("snapshot", {})
    summaries = []
    sections = (("check_runs", "check_runs", "conclusion"),
                ("statuses", "statuses", "state"), ("reviews", None, "state"))
    for section, child, field in sections:
        value = snapshot.get(section)
        if not isinstance(value, dict):
            continue
        data = value.get("data")
        data = data.get(child, []) if child and isinstance(data, dict) else data
        if isinstance(data, list):
            counts = Counter((i.get(field) or i.get("status") or "unknown")
                             for i in data if isinstance(i, dict))
            summaries.append(section + ": " + (", ".join(f"{key}={value}" for key, value in sorted(counts.items())) or "none"))
    threads = snapshot.get("threads")
    if isinstance(threads, dict) and isinstance(threads.get("data"), list):
        unresolved = sum(not item.get("isResolved", False) for item in threads["data"] if isinstance(item, dict))
        summaries.append(f"unresolved review threads={unresolved}")
    return (f"  Read-only observation at {latest.get('observed_at', 'unknown time')}: "
            f"head {latest.get('observed_head') or 'unknown'}; "
            + ("; ".join(summaries) if summaries else "no check/review summary recorded")
            + ". This observation does not establish merge readiness.")


def _render_card(row: dict) -> list:
    lines = [f"{row['human_id']} [{row['id']}] -- {row['result']}",
             f"  URL: {row['url'] or 'missing from legacy record'}",
             f"  Evaluated head: {row['head_sha'] or 'not recorded'}. Role: {row['role']}."]
    if row.get("replaces"):
        lines.append(f"  Replaces [{row['replaces']}]; linked evidence outside the selected denominator.")
    if row.get("replaced_by"):
        lines.append(f"  Replacement: [{row['replaced_by']}].")
    if row["state"] == "MERGED":
        lines.append(f"  Merge receipt: commit {row['merge_commit'] or 'missing'} at {row['merged_at'] or 'missing'}.")
    if row["reason_line"]:
        lines.append(f"  Recorded result: {row['reason_code']} {row['reason_line']}".rstrip())
        if row["state"] == "CLOSED" and not row["delivered_via_replacement"] \
                and "update delivered there" in row["reason_line"]:
            lines.append("  Historical delivery wording is not merge proof; no verified merged replacement is recorded.")
    if row["head_drift"]:
        lines.append("  A newer observed head differs from the evaluated head; prior checks do not establish current readiness.")
    for blocker in row["current_blockers"]:
        lines.append(f"  Current blocker: {blocker['reason_code']} {blocker['reason_line']}"
                     + (" (legacy primary reason; complete blocker set not recorded)." if blocker.get("legacy") else "."))
        if blocker.get("action"):
            lines.append(f"    Required action: {blocker['action']}; owner {blocker.get('action_owner', 'not recorded')}.")
        if blocker.get("evidence"):
            lines += _evidence_lines(blocker["evidence"], "Blocker evidence")
    for blocker in row["historical_blockers"]:
        lines.append(f"  Prior-head condition: {blocker['reason_code']} {blocker['reason_line']}; head {_evidence_head(blocker)}. Re-evaluate applicability.")
    stop = row["execution_stop"]
    if stop:
        lines.append(f"  Execution stop: {stop['reason_code']} {stop['reason_line']}. This records why work stopped, not a code defect.")
    owner_hold = row["owner_hold"]
    if owner_hold:
        state = "active" if owner_hold.get("active", True) else "released"
        current_head = row["effective_head"]
        if owner_hold.get("head_sha") and owner_hold["head_sha"].lower() != current_head.lower():
            state += " at a prior head; applicability to the current head is unestablished"
        lines.append(f"  Owner hold: {state}; scope {owner_hold.get('scope', 'unspecified')}; {owner_hold['reason']}; source {owner_hold['source']}."
                     + (f" Bound head {owner_hold['head_sha']}." if owner_hold.get("head_sha") else ""))
    elif row["state"] not in ("MERGED", "CLOSED"):
        lines.append("  Owner hold: no sourced owner hold recorded. A technical hold or requested decision is not an owner veto.")
    if row["saved_authority_hold"]:
        lines.append("  Saved authority: this PR is still listed as held. A reporting-only release does not change that execution restriction.")
    lines += _evidence_lines(row["current_evidence"], "Recorded evidence for current head; refresh before readiness")
    if row["historical_evidence"]:
        lines += _evidence_lines(row["historical_evidence"], "Historical or unbound evidence; not current readiness")
    if row["latest_observation"]:
        lines.append(_observation_line(row["latest_observation"]))
    lines.append(f"  Next: {row['next_action']}. Owner: {row['next_owner']}. Resume: {row['next_trigger']}.")
    if row["issue_ids"]:
        lines.append("  Linked follow-ups: " + ", ".join(row["issue_ids"]) + ".")
    return lines


def _render_followups(items: list) -> list:
    if not items:
        return ["Follow-ups: none identified.", ""]
    counts = Counter(i["status"] for i in items)
    lines = [f"FOLLOW-UPS ({len(items)}; separate from PR delivery): "
             + ", ".join(f"{key}={value}" for key, value in sorted(counts.items()))]
    for item in items:
        lines.append(f"[{item['id']}] affects {', '.join(item['card_ids']) or 'no PR link'} -- {item['claim']}")
        lines.append(f"  Target: {item['target'] or item['repo_id'] or 'not recorded'}. Kind: {item['kind']}. Status: {item['status']}.")
        lines.append(f"  Attribution: {item['attribution']}; {item['attribution_note'] or 'attribution evidence not recorded'}.")
        lines.append(f"  Recommendation: {item['action'] or 'recommendation missing from legacy record'}. Owner: {item['action_owner'] or 'unassigned'}.")
        lines.append(f"  Continuation: {'retain resolution evidence' if item['status'] in ('resolved', 'dismissed') else 'perform the recommendation within separately established authority; record outcome and evidence'}.")
        lines += (_evidence_lines(item["evidence"], "Follow-up evidence") if item["evidence"]
                  else ["  Follow-up evidence: evidence missing from legacy record."])
        if item["external_links"]:
            for link in item["external_links"]:
                lines.append(f"  External tracker reference recorded: {link['url']} {link.get('title', '')}".rstrip())
        else:
            lines.append("  Local record only; no external tracker reference recorded.")
        lines.append("")
    return lines


def render_report(store: Store, continuation: str | None = None, *, snapshot: dict | None = None) -> str:
    """Render once for both saved and inline delivery; no independent result list."""
    snap = report_snapshot(store, continuation) if snapshot is None else snapshot
    counts, delivered = snap["counts"], snap["delivery"]
    lines = [f"{snap['run_id']} {snap['authority']} pass ended {snap['ending']}.",
             f"Report snapshot: {snap['observed_at']}. Selected scope: {counts['selected']} PRs.",
             f"Outcomes (mutually exclusive): direct merged {counts['direct_merged']}; "
             f"delivered via replacement {counts['delivered_via_replacement']}; "
             f"closed without delivery {counts['closed_without_delivery']}; "
             f"assessed holds {counts['assessed_holds']}; prepared {counts['prepared']}; "
             f"unassessed {counts['unassessed']}; unknown {counts['unknown']}.",
             f"Delivered {delivered['total']} selected updates (direct {delivered['direct']}, via replacement {delivered['via_replacement']})."]
    live = snap["live_open"]
    if live["count"] is None:
        lines.append(f"Live open PRs: unknown; {live['reason']}.")
    else:
        lines.append(f"Live open PRs: {live['count']} at {live['observed_at']}; {live['source']}. This inventory includes open arrivals and replacements and is separate from assessed outcomes.")
    lines += [snap["continuation"], ""]
    if snap["authority_lines"]:
        lines += ["REPOSITORY AUTHORITY", *snap["authority_lines"], ""]
    for role, title in (("selected", "SELECTED PR RESULTS"), ("replacement", "LINKED REPLACEMENTS"),
                        ("arrival", "UNSELECTED ARRIVALS")):
        rows = [row for row in snap["cards"] if row["role"] == role]
        if not rows:
            continue
        lines.append(f"{title} ({len(rows)})")
        current_repo = None
        for row in sorted(rows, key=lambda r: (r["repo_id"], r["number"], r["id"])):
            if current_repo != row["repo_id"]:
                current_repo = row["repo_id"]
                lines.append(current_repo)
            lines += _render_card(row) + [""]
    lines += _render_followups(snap["followups"])
    if snap["approval_groups"]:
        lines += _render_approval_groups(snap["approval_groups"]) + [""]
    lines.append("RECOMMENDED EXECUTION ORDER")
    actionable = [row for row in snap["cards"] if row["state"] not in ("MERGED", "CLOSED")]
    rank = {"UNKNOWN": 0, "READY": 1, "WAITING": 2, "BLOCKED": 3, "NEEDS_OWNER": 4, "NEW": 5}
    for row in sorted(actionable, key=lambda r: (rank.get(r["state"], 6), r["id"])):
        decision = row["decision"] or {}
        authority = (f"decision scope {decision.get('scope', 'unspecified')}; obtain that decision before its action"
                     if row["state"] == "NEEDS_OWNER" else
                     "read-only verification may proceed; any mutation requires saved authority and fresh gates")
        lines.append(f"[{row['id']}] {row['next_action']} ({authority}).")
    if not actionable:
        lines.append("No unresolved PR action; complete any open follow-ups within their own authority.")
    lines += ["", "WORKERS"]
    if not snap["workers"]:
        lines.append("No worker attempts recorded.")
    for attempt in snap["workers"]:
        lines.append(f"{attempt['id']} ({attempt['model'] or 'unassigned model'}): "
                     f"{attempt['result'] or 'no final result recorded; liveness unverified'}; "
                     f"assigned {len(attempt['assigned'])}, outstanding {len(attempt['outstanding'])}.")
        if attempt["outstanding"]:
            lines.append("  Outstanding: " + ", ".join(attempt["outstanding"]) + ".")
        if attempt["successor"]:
            lines.append(f"  Successor: {attempt['successor']}.")
    return "\n".join(lines + ["", snap["continuation"]]) + "\n"


def approval_cards(store: Store) -> list:
    """Stable individual approval choices, including linked replacements."""
    assert store.header is not None, "create_run first"
    return sorted((c for c in _visible(store) if c.state == State.NEEDS_OWNER),
                  key=lambda c: (SEVERITY_RANK.get(c.severity, 99), c.id))


def _decision_view(value) -> dict:
    """Render old invalid decisions as incomplete without changing the record."""
    if not isinstance(value, dict):
        return {"_report_invalid_fields": ["decision"]}
    result, invalid = copy.deepcopy(value), []
    result.pop("_report_invalid_fields", None)
    for key in ("why", "approve_effect", "decline_effect", "recommendation",
                "source", "group_key", "scope"):
        if key in result and (not isinstance(result[key], str) or not result[key].strip()):
            result.pop(key)
            invalid.append(key)
    if result.get("scope", "merge") not in {"merge", "close", "settings", "repair", "other"}:
        result.pop("scope")
        invalid.append("scope")
    if invalid:
        result["_report_invalid_fields"] = invalid
    return result


def approval_groups(store: Store) -> list:
    """Group identical scoped decisions for presentation, never authorization.

    Every member retains its individual card id, URL, and full evaluated head.
    Different effects/scopes cannot share a decision even with the same key.
    """
    groups, positions = [], {}
    for position, card in enumerate(approval_cards(store), start=1):
        decision = _decision_view(card.decision)
        group_key = (card.id if decision.get("_report_invalid_fields")
                     else decision.get("group_key") or card.id)
        key = (card.repo_id.casefold(), group_key, decision.get("scope", "unspecified"),
               *(decision.get(k, "") for k in ("why", "approve_effect", "decline_effect", "recommendation")))
        if key not in positions:
            positions[key] = len(groups)
            groups.append({"group_id": f"DEC-{len(groups) + 1:03d}", "decision": decision,
                           "scope": decision.get("scope", "unspecified"), "cards": []})
        groups[positions[key]]["cards"].append({"position": position, "id": card.id,
                                               "human_id": card.human_id, "url": card.url,
                                               "head_sha": card.head_sha,
                                               "severity": card.severity, "confidence": card.confidence})
    return groups


def _render_approval_groups(groups: list) -> list:
    total = sum(len(group["cards"]) for group in groups)
    lines = [f"DECISIONS REQUESTED -- {total} PRs in {len(groups)} scoped decisions.",
             "Choose a stated decision and list its individual PRs. Grouping is presentation only; it does not authorize a merge.",
             "A merge approval must identify each PR and its exact head. Closure, settings, and repair decisions have separate scope.", ""]
    for group in groups:
        decision = group["decision"]
        lines.append(f"[{group['group_id']}] Scope: {group['scope']}")
        lines.append(f"  Why: {decision.get('why') or 'decision rationale missing from legacy record'}")
        lines.append(f"  Approve -> {decision.get('approve_effect', 'not stated')}")
        lines.append(f"  Decline -> {decision.get('decline_effect', 'not stated')}")
        lines.append(f"  Recommend: {decision.get('recommendation', 'not stated')}")
        if decision.get("_report_invalid_fields"):
            lines.append("  Invalid legacy decision fields: "
                         + ", ".join(decision["_report_invalid_fields"])
                         + ". Establish the decision before interpreting approval.")
        if group["scope"] == "unspecified":
            lines.append("  Decision scope missing from legacy record; establish the requested action before interpreting approval.")
        for card in group["cards"]:
            lines.append(f"  #{card['position']} {card['human_id']} [{card['id']}] -- {card['url'] or 'URL not recorded'}")
            lines.append(f"    Head: {card['head_sha'] or 'not yet verified'}. Risk: {card['severity']}, {card['confidence']}.")
        lines.append("")
    return lines


def render_approval(store: Store) -> str:
    groups = approval_groups(store)
    return "\n".join(_render_approval_groups(groups)) if groups else "No approvals needed.\n"
