#!/usr/bin/env python3
"""Coordinator for dependabot-sweep, Slice 1: reconcile, schedule, collect.

The coordinator owns inventory, scheduling, recovery, and reporting. It
never merges. Worker returns are outcome records, not prose: every
assigned card must resolve to merged, ready, hold, unknown, or closed.

Stdlib only. GitHub observations enter as plain data (the `observed`
mappings), so every path below is testable without the network.
"""

from __future__ import annotations

import calendar
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sweep_core import (  # noqa: E402
    Card, Issue, K_REASONS, RunHeader, SEVERITIES, State, Store, StoreError,
    TERMINAL, TRANSITIONS, utc_now,
)

HOLD_STATES = frozenset({State.WAITING, State.BLOCKED, State.NEEDS_OWNER})
# Outcome vocabulary -> the state a worker claims. "hold" names its own.
OUTCOME_TARGETS = {"merged": State.MERGED, "ready": State.READY,
                   "unknown": State.UNKNOWN, "closed": State.CLOSED}


def create_run(store: Store, run_id: str, mode: str, authorization: str,
               discoveries: list, scope_fixed: bool = True,
               exclusions: list | None = None,
               cutoff: str = "") -> RunHeader:
    """Persist the run header and one NEW card per discovered PR.

    Card ids are assigned in discovery order and never renumbered.
    `cutoff` records the discovery instant a fixed scope was taken at.
    """
    header = RunHeader(run_id=run_id, mode=mode,
                       scope_fixed=scope_fixed, cutoff=cutoff,
                       authorization=authorization,
                       exclusions=list(exclusions or []),
                       started_at=utc_now())
    store.set_header(header)
    for discovery in discoveries:
        card_id = store.ids.next("PR")
        card = Card(
            id=card_id,
            org=discovery["org"], repo=discovery["repo"],
            number=discovery["number"],
            url=discovery.get("url", ""),
            title=discovery.get("title", ""),
            owner=discovery.get("owner", ""),
            head_sha=discovery.get("head_sha", ""),
            base_ref=discovery.get("base_ref", ""),
            created_at=utc_now(), updated_at=utc_now(),
        )
        store.upsert_card(card)
        header.scope_ids.append(card_id)
    store.set_header(header)
    store.record_ids()
    return header


def _decide(seen: dict) -> str:
    """Classify one observation: merged (with commit and timestamp),
    unmerged, or ambiguous. A merge claim without its evidence is
    ambiguous, never a success."""
    if seen.get("merged") is True:
        return "merged" if seen.get("commit") and seen.get("at") else "ambiguous"
    if seen.get("merged") is False:
        return "unmerged"
    return "ambiguous"


def _epoch_of(stamp: str) -> float:
    try:
        return float(calendar.timegm(time.strptime(stamp,
                                                   "%Y-%m-%dT%H:%M:%SZ")))
    except (TypeError, ValueError):
        return 0.0


def _protected(store: Store, attempt, now: float | None,
               stale_after_secs: float | None) -> bool:
    """A live attempt of another coordinator session is never reconciled
    away while its heartbeat is fresh: this session cannot know it died.
    Without a staleness bound, another session's attempt is always kept."""
    if attempt is None or not attempt.session \
            or attempt.session == store.session:
        return False
    if stale_after_secs is None:
        return True
    moment = time.time() if now is None else now
    return moment - _epoch_of(attempt.last_progress_at) <= stale_after_secs


def _unlock(store: Store, repo_id: str, holder: str) -> None:
    if store.locks is not None and holder:
        store.locks.release(repo_id, holder)


def reconcile(store: Store, observed: dict, live_attempts: set,
              now: float | None = None,
              stale_after_secs: float | None = None) -> dict:
    """Restart/crash reconciliation. Runs before any new mutation.

    `observed` maps card id -> {"merged": bool|None, "commit": str,
    "at": str}. `live_attempts` holds attempt ids known to still run.
    Every dead attempt is marked crashed; every orphaned lease is
    reconciled read-only against observed reality; ambiguity quarantines
    the repository. Quarantined repositories are reconciled the same way:
    each UNKNOWN card needs a decisive observation, and the quarantine
    lifts only when none remains. A recorded hold is truth: an unmerged
    observation confirms it, only UNKNOWN cards are restored, and only
    NEW cards are rescheduled. Attempts another session issued are left
    alone until their heartbeat is older than `stale_after_secs`.
    """
    summary = {"crashed": [], "merged": [], "rescheduled": [],
               "retained": [], "quarantined": [], "resolved": []}
    crashed = []
    for attempt in store.diary.values():
        if not attempt.result and attempt.id not in live_attempts \
                and not _protected(store, attempt, now, stale_after_secs):
            attempt.result = "crashed"
            crashed.append(attempt)
    for lease in list(store.leases.leases.values()):
        if lease.state != "held" or lease.holder in live_attempts \
                or _protected(store, store.diary.get(lease.holder), now,
                              stale_after_secs):
            continue
        quarantined_here = False
        for card_id in lease.pr_ids:
            card = store.cards[card_id]
            if card.state in TERMINAL:
                continue
            seen = observed.get(card_id, {})
            verdict = _decide(seen)
            if verdict == "merged":
                card.observe_merged(seen["commit"], seen["at"])
                store.upsert_card(card)
                summary["merged"].append(card_id)
            elif verdict == "unmerged":
                if card.state == State.UNKNOWN:
                    card.restore_prior()
                    store.upsert_card(card)
                bucket = ("rescheduled" if card.state == State.NEW
                          else "retained")
                summary[bucket].append(card_id)
            else:
                if card.state != State.UNKNOWN:
                    card.transition_to(State.UNKNOWN)
                    store.upsert_card(card)
                store.leases.quarantine(
                    lease.repo_id,
                    f"uncertain mutation on {card_id}; reconcile first")
                store.record_lease(store.leases.get(lease.repo_id))
                summary["quarantined"].append(card_id)
                quarantined_here = True
        if not quarantined_here:
            # Every card on this dead lease reached a known outcome, so
            # the lease is free for a successor worker to acquire.
            holder = lease.holder
            store.leases.release(lease.repo_id, holder)
            store.record_lease(store.leases.get(lease.repo_id))
            _unlock(store, lease.repo_id, holder)
    for lease in list(store.leases.leases.values()):
        if lease.state != "quarantined":
            continue
        unknown = sorted((c for c in store.cards.values()
                          if c.repo_id == lease.repo_id
                          and c.state == State.UNKNOWN), key=lambda c: c.id)
        proved_merged, still_unknown = False, False
        for card in unknown:
            seen = observed.get(card.id, {})
            verdict = _decide(seen)
            if verdict == "merged":
                card.observe_merged(seen["commit"], seen["at"])
                store.upsert_card(card)
                summary["merged"].append(card.id)
                proved_merged = True
            elif verdict == "unmerged":
                card.restore_prior()
                store.upsert_card(card)
                bucket = ("rescheduled" if card.state == State.NEW
                          else "retained")
                summary[bucket].append(card.id)
            else:
                summary["quarantined"].append(card.id)
                still_unknown = True
        if not still_unknown:
            holder = lease.holder
            store.record_lease(store.leases.resolve_quarantine(
                lease.repo_id, proved_merged))
            _unlock(store, lease.repo_id, holder)
            summary["resolved"].append(lease.repo_id)
    for attempt in crashed:
        # Outstanding reflects reconciled truth, not the pre-reconcile view.
        attempt.outstanding = [c for c in attempt.assigned
                               if store.cards[c].state not in TERMINAL]
        store.record_attempt(attempt)
        summary["crashed"].append(attempt.id)
    return summary


SCHEDULABLE = frozenset({State.NEW, State.READY})


def schedule(store: Store, model: str = "", pr_budget_secs: float | None = None,
             now: float | None = None, wake=()) -> list:
    """Issue one tasking per free repo that holds schedulable cards: NEW,
    or READY awaiting an authorized merge after a fresh evaluation, plus
    any hold card named in `wake` (its resume trigger fired). Holds are
    never dispatched on their own; a woken card must exist, be a hold,
    and have budget left.

    Returns tasking records {attempt_id, repo_id, card_ids}. Quarantined
    and held repositories are never scheduled. A repository whose last
    attempt crashed gets a successor attempt id (AGT-00n.k+1) on the same
    card ids, never new card ids. Each card's deadline is set once, when
    first scheduled with a budget; successors inherit it because handoffs
    and retries never reset the clock. A card deadline never outlives the
    run deadline. With repository lock files, a repo another session
    holds is skipped.
    """
    assert store.header is not None, "create_run first"
    moment = time.time() if now is None else now
    for card_id in wake:
        card = store.cards.get(card_id)
        if card is None:
            raise StoreError(f"cannot wake unknown card {card_id!r}")
        if card.state not in HOLD_STATES:
            raise StoreError(f"{card_id}: only a hold can be woken, not "
                             f"{card.state.value}")
        if card.deadline_epoch and moment > card.deadline_epoch:
            raise StoreError(f"{card_id}: budget exhausted; continue in a "
                             f"new run instead of waking it")
        if store.leases.get(card.repo_id).state in ("held", "quarantined"):
            raise StoreError(f"{card_id}: repository {card.repo_id} is "
                             f"{store.leases.get(card.repo_id).state}")
    by_repo: dict[str, list] = {}
    candidates = list(store.header.scope_ids)
    # Replacement cards are linked evidence, not selected updates, but the
    # replacement PR itself still needs a worker when unevaluated.
    candidates += [c.id for c in store.cards.values()
                   if c.state in SCHEDULABLE and c.replaces
                   and c.id not in store.header.scope_ids]
    candidates += [c for c in wake if c not in candidates]
    for card_id in candidates:
        card = store.cards[card_id]
        if card.state not in SCHEDULABLE and card_id not in wake:
            continue
        if card.deadline_epoch and moment > card.deadline_epoch:
            continue  # dead work is expired, never dispatched
        lease = store.leases.get(card.repo_id)
        if lease.state in ("held", "quarantined"):
            continue
        by_repo.setdefault(card.repo_id, []).append(card_id)
    taskings = []
    for repo_id, card_ids in by_repo.items():
        attempt_id, dead = _peek_attempt_id(store, card_ids)
        if store.locks is not None \
                and not store.locks.claim(repo_id, attempt_id):
            continue  # another session holds this repository
        if dead is not None:
            dead.successor = attempt_id
            store.record_attempt(dead)
        else:
            store.ids.attempt_id()
        attempt = _new_attempt(attempt_id, card_ids, model)
        attempt.session = store.session
        store.record_attempt(attempt)
        lease = store.leases.acquire(repo_id, attempt_id, card_ids)
        store.record_lease(lease)
        for card_id in card_ids:
            card = store.cards[card_id]
            card.attempts.append(attempt_id)
            if not card.deadline_epoch and pr_budget_secs is not None:
                card.deadline_epoch = moment + pr_budget_secs
                if store.header.deadline_epoch:
                    card.deadline_epoch = min(card.deadline_epoch,
                                              store.header.deadline_epoch)
            store.upsert_card(card)
        taskings.append({"attempt_id": attempt_id, "repo_id": repo_id,
                         "card_ids": list(card_ids)})
    store.record_ids()
    return taskings


def _peek_attempt_id(store: Store, card_ids: list) -> tuple:
    """The id the next attempt over these cards will take, without
    committing it: (successor id, dead attempt) after a crash, else
    (next fresh id, None). `schedule` commits only after the repository
    lock is claimed, so a refused claim leaves no trace."""
    crashed = []
    for card_id in card_ids:
        for attempt_id in reversed(store.cards[card_id].attempts):
            attempt = store.diary.get(attempt_id)
            if attempt is not None and attempt.result == "crashed" \
                    and not attempt.successor:
                crashed.append(attempt)
                break
    if not crashed:
        return f"AGT-{store.ids.counters.get('AGT', 0) + 1:03d}.1", None
    dead = max(crashed, key=lambda a: (a.started_at, a.id))
    return store.ids.successor_id(dead.id), dead


def _new_attempt(attempt_id: str, card_ids: list, model: str):
    from sweep_core import Attempt
    return Attempt(id=attempt_id, assigned=list(card_ids), model=model,
                   started_at=utc_now(), last_progress_at=utc_now(),
                   phase="assigned")


def apply_outcome(store: Store, attempt_id: str, results: list) -> dict:
    """Collect one worker's outcome records.

    Each result resolves one assigned card: merged (requires commit sha
    and timestamp), ready (requires reason and evidence; prepared but
    unmerged), hold (requires target state, known reason code, known
    severity, reason, action, owner), unknown (requires an operation
    note; quarantines the repo), or closed (requires a reason). The whole
    batch is validated before any card changes: one bad record refuses
    the batch and leaves cards, attempt, and lease untouched.
    """
    attempt = store.diary.get(attempt_id)
    if attempt is None:
        raise StoreError(f"unknown attempt {attempt_id}")
    if attempt.result:
        raise StoreError(f"attempt {attempt_id} already "
                         f"{attempt.result}")
    seen: set = set()
    for result in results:
        card_id = result.get("card_id", "")
        if card_id not in attempt.assigned:
            raise StoreError(f"{attempt_id} was not assigned {card_id!r}")
        if card_id in seen:
            raise StoreError(f"{card_id}: resolved twice in one batch")
        seen.add(card_id)
        card = store.cards[card_id]
        if store.leases.get(card.repo_id).state == "quarantined" \
                and result.get("outcome") in ("merged", "ready"):
            raise StoreError(f"{card_id}: repository {card.repo_id} is "
                             f"quarantined; reconcile before claiming "
                             f"{result['outcome']}")
        _validate_result(card, result)
    applied = []
    for result in results:
        card = store.cards[result["card_id"]]
        outcome = result["outcome"]
        if outcome == "merged":
            _apply_merged(card, result)
        elif outcome == "ready":
            _apply_ready(card, result)
        elif outcome == "hold":
            _apply_hold(card, result)
            if result.get("incident"):
                link_incident(store, card, result)
        elif outcome == "unknown":
            _apply_unknown(store, card, result)
        else:
            _apply_closed(card, result)
        card.last_observation = utc_now()
        store.upsert_card(card)
        applied.append(card.id)
    attempt.last_progress_at = utc_now()
    attempt.phase = "returned"
    pending = [c for c in attempt.assigned if c not in applied]
    attempt.outstanding = pending
    if not pending:
        attempt.result = "completed"
    store.record_attempt(attempt)
    _settle_leases(store, attempt)
    return {"attempt": attempt_id, "applied": applied, "pending": pending}


def _validate_result(card: Card, result: dict) -> None:
    """Refuse an outcome record before anything mutates. Every rule the
    appliers rely on lives here, including worker transition legality."""
    outcome = result.get("outcome")
    if outcome == "closed" and card.state == State.CLOSED:
        # The coordinator already recorded the supersession; the worker's
        # own closed record is accepted when it agrees.
        link = result.get("replaced_by", "")
        if link and card.replaced_by and link != card.replaced_by:
            raise StoreError(f"{card.id}: closed with replaced_by {link!r} "
                             f"conflicts with recorded supersession "
                             f"{card.replaced_by!r}")
        if not result.get("reason"):
            raise StoreError(f"{card.id}: closed requires a reason")
        return
    if outcome == "hold":
        try:
            target = State(result.get("state", ""))
        except ValueError:
            raise StoreError(f"{card.id}: hold needs a valid state") from None
        if target not in HOLD_STATES:
            raise StoreError(f"{card.id}: hold target must be WAITING, "
                             f"BLOCKED, or NEEDS_OWNER")
        for key in ("reason_code", "reason_line", "action", "action_owner"):
            if not result.get(key):
                raise StoreError(f"{card.id}: hold requires {key}")
        if result["reason_code"] not in K_REASONS:
            raise StoreError(f"{card.id}: unknown reason_code "
                             f"{result['reason_code']!r}")
        incident = result.get("incident")
        if incident is not None and not (incident.get("key")
                                         and incident.get("claim")):
            raise StoreError(f"{card.id}: incident requires key and claim")
        if target == State.NEEDS_OWNER:
            decision = result.get("decision", {})
            for key in ("why", "approve_effect", "decline_effect",
                        "recommendation"):
                if not decision.get(key):
                    raise StoreError(f"{card.id}: NEEDS_OWNER requires "
                                     f"decision.{key} for the approval "
                                     f"output")
    elif outcome in OUTCOME_TARGETS:
        target = OUTCOME_TARGETS[outcome]
        if outcome == "merged" and not (result.get("commit_sha")
                                        and result.get("merged_at")):
            raise StoreError(f"{card.id}: merged requires commit_sha and "
                             f"merged_at evidence")
        if outcome == "ready" and not (result.get("reason_line")
                                       and result.get("evidence")):
            raise StoreError(f"{card.id}: ready requires reason_line and "
                             f"non-empty evidence")
        if outcome == "unknown" and not result.get("op_note"):
            raise StoreError(f"{card.id}: unknown requires op_note "
                             f"describing the uncertain operation")
        if outcome == "closed" and not result.get("reason"):
            raise StoreError(f"{card.id}: closed requires a reason")
    else:
        raise StoreError(f"{card.id}: unknown outcome {outcome!r}")
    severity = result.get("severity", "unknown")
    if severity not in SEVERITIES:
        raise StoreError(f"{card.id}: unknown severity {severity!r}; "
                         f"expected one of {', '.join(SEVERITIES)}")
    if outcome == "hold" and target == card.state:
        return  # a re-evaluated hold refreshes its reason in place
    if target not in TRANSITIONS[card.state]:
        raise StoreError(f"{card.id}: {card.state.value} -> {target.value} "
                         f"is not a worker transition")


def _apply_merged(card: Card, result: dict) -> None:
    card.merge_commit = result["commit_sha"]
    card.merged_at = result["merged_at"]
    card.severity = "none"
    card.transition_to(State.MERGED)


def _apply_ready(card: Card, result: dict) -> None:
    """A worker evaluated the card and found it mergeable but did not
    merge (e.g. gated preparation)."""
    card.reason_line = result["reason_line"]
    card.evidence = result["evidence"]
    card.severity = "none"
    card.transition_to(State.READY)


def _apply_hold(card: Card, result: dict) -> None:
    target = State(result["state"])
    card.reason_code = result["reason_code"]
    card.reason_line = result["reason_line"]
    card.severity = result.get("severity", "unknown")
    card.confidence = result.get("confidence", "unknown")
    card.evidence = result.get("evidence", [])
    card.action = result["action"]
    card.action_owner = result["action_owner"]
    card.resume_trigger = result.get("resume_trigger", "")
    if target == State.NEEDS_OWNER:
        card.decision = result["decision"]
    if card.state == target:
        card.updated_at = utc_now()
    else:
        card.transition_to(target)


def _apply_unknown(store: Store, card: Card, result: dict) -> None:
    card.reason_code = "K11"
    card.reason_line = result["op_note"]
    card.severity = result.get("severity", "unknown")
    card.action = "Reconcile read-only before any retry; hold repo."
    card.action_owner = result.get("action_owner", "sweeper")
    card.transition_to(State.UNKNOWN)
    lease = store.leases.quarantine(card.repo_id,
                                    f"uncertain mutation on {card.id}")
    store.record_lease(lease)


def _apply_closed(card: Card, result: dict) -> None:
    if result.get("replaced_by") and not card.replaced_by:
        card.replaced_by = result["replaced_by"]
    if card.state == State.CLOSED:
        return  # already superseded by the coordinator; nothing to move
    card.reason_line = result["reason"]
    card.transition_to(State.CLOSED)


def _settle_leases(store: Store, attempt) -> None:
    repos = {store.cards[c].repo_id for c in attempt.assigned}
    for repo_id in repos:
        lease = store.leases.get(repo_id)
        if lease.state != "held" or lease.holder != attempt.id:
            continue
        cards = [store.cards[c] for c in attempt.assigned
                 if store.cards[c].repo_id == repo_id]
        if any(c.state == State.UNKNOWN for c in cards):
            store.record_lease(store.leases.quarantine(
                repo_id, "unknown mutation outcome; reconcile first"))
        elif attempt.result == "completed":
            store.record_lease(store.leases.release(repo_id, attempt.id))
            _unlock(store, repo_id, attempt.id)


def verify_merges(store: Store, observed: dict) -> list:
    """Cross-check MERGED claims against fresh observation.

    A card observed unmerged after being recorded merged is demoted to
    UNKNOWN and its repo quarantined: post-merge surprises never stand
    as successes. Cards with no fresh observation keep their recorded
    evidence. Returns demoted card ids.
    """
    demoted = []
    for card in store.cards.values():
        if card.state != State.MERGED:
            continue
        seen = observed.get(card.id)
        if seen is None or seen.get("merged") is not False:
            continue
        card.observe_merge_retracted("recorded merged but fresh observation "
                                     "shows unmerged; reconciling")
        store.upsert_card(card)
        store.record_lease(store.leases.quarantine(
            card.repo_id, f"post-merge surprise on {card.id}"))
        demoted.append(card.id)
    return demoted


def register_replacement(store: Store, old_id: str, fields: dict) -> Card:
    """Link a replacement PR to the original it supersedes.

    Original and replacement stay distinct cards; the original closes
    with a replaced_by link, never counted as merged.
    """
    old = store.cards.get(old_id)
    if old is None:
        raise StoreError(f"unknown card {old_id}")
    if old.replaced_by:
        raise StoreError(f"{old_id} is already superseded by "
                         f"{old.replaced_by}")
    new_id = store.ids.next("PR")
    new = Card(id=new_id, org=fields["org"], repo=fields["repo"],
               number=fields["number"], url=fields.get("url", ""),
               title=fields.get("title", ""),
               owner=fields.get("owner", ""),
               head_sha=fields.get("head_sha", ""),
               base_ref=fields.get("base_ref", ""),
               replaces=old_id, created_at=utc_now(),
               updated_at=utc_now())
    store.upsert_card(new)
    old.replaced_by = new_id
    old.reason_line = f"Superseded by {new_id}; update delivered there."
    if old.state != State.CLOSED:  # a worker may have closed it first
        old.transition_to(State.CLOSED)
    store.upsert_card(old)
    store.record_ids()
    return new


def register_arrival(store: Store, fields: dict) -> Card:
    """Record a PR discovered after the run started.

    New arrivals get fresh ids; existing ids are never renumbered. In an
    evolving run the card joins the selected set; in a fixed-scope run
    it is recorded and reported but never selected or scheduled.
    """
    assert store.header is not None, "create_run first"
    card_id = store.ids.next("PR")
    card = Card(id=card_id, org=fields["org"], repo=fields["repo"],
                number=fields["number"], url=fields.get("url", ""),
                title=fields.get("title", ""),
                owner=fields.get("owner", ""),
                head_sha=fields.get("head_sha", ""),
                base_ref=fields.get("base_ref", ""),
                created_at=utc_now(), updated_at=utc_now())
    store.upsert_card(card)
    if not store.header.scope_fixed:
        store.header.scope_ids.append(card_id)
        store.set_header(store.header)
    store.record_ids()
    return card


def delivery_counts(store: Store) -> dict:
    """Count delivered dependency updates without double counting.

    Direct merges plus originals whose update arrived via a merged
    replacement. Replacement cards are linked evidence, not extra
    selected updates; supporting work stays excluded by construction.
    """
    direct = sum(1 for c in store.cards.values()
                 if c.state == State.MERGED and not c.replaces)
    via_replacement = sum(
        1 for c in store.cards.values()
        if c.state == State.CLOSED and c.replaced_by
        and store.cards.get(c.replaced_by, c).state == State.MERGED)
    return {"direct": direct, "via_replacement": via_replacement,
            "total": direct + via_replacement}


def describe_subset(store: Store, ids: list) -> list:
    """Answer a follow-up about a subset of cards.

    Resolves through the header's read-only query: the run's objective
    is preserved no matter how narrow the question.
    """
    assert store.header is not None, "create_run first"
    return [store.cards[i] for i in store.header.query_subset(ids)]


def link_incident(store: Store, card: Card, result: dict) -> Issue:
    """Link a card to the shared incident its diagnosis named. One issue
    per (repository, incident key): every PR a base-branch failure blocks
    carries the same ISS id, and the incident is repaired once."""
    key = result["incident"]["key"]
    issue = next((i for i in store.issues.values()
                  if i.key == key and i.repo_id == card.repo_id), None)
    if issue is None:
        issue = Issue(id=store.ids.next("ISS"), key=key,
                      repo_id=card.repo_id,
                      reason_code=result["reason_code"],
                      claim=result["incident"]["claim"],
                      action=result["action"],
                      action_owner=result["action_owner"],
                      created_at=utc_now())
        store.record_ids()
    if card.id not in issue.card_ids:
        issue.card_ids.append(card.id)
    store.record_issue(issue)
    if issue.id not in card.issue_ids:
        card.issue_ids.append(issue.id)
    return issue


def start_run_clock(store: Store, run_budget_secs: float,
                    now: float | None = None) -> float:
    """Set the whole-run deadline once. A second call is refused: a
    resumed or retried run inherits the clock, it never resets it."""
    assert store.header is not None, "create_run first"
    if store.header.deadline_epoch:
        raise StoreError(f"run deadline already set to "
                         f"{store.header.deadline_epoch}; never reset")
    moment = time.time() if now is None else now
    store.header.deadline_epoch = moment + run_budget_secs
    store.set_header(store.header)
    return store.header.deadline_epoch


def expire(store: Store, now: float | None = None) -> list:
    """Move idle dispatchable cards (NEW, READY) whose deadline passed to
    WAITING K14, so `schedule` never hands dead work to a worker. A card
    under a held lease keeps its worker's own deadline; holds await their
    owner, not the clock."""
    moment = time.time() if now is None else now
    expired = []
    for card in sorted(store.cards.values(), key=lambda c: c.id):
        if card.state not in SCHEDULABLE or not card.deadline_epoch \
                or moment <= card.deadline_epoch:
            continue
        if store.leases.get(card.repo_id).state == "held":
            continue
        card.reason_code = "K14"
        card.reason_line = "per-PR budget exhausted before dispatch"
        card.severity = "low"
        card.action = "Budget exhausted for this PR; continue in the next run."
        card.action_owner = "sweeper"
        card.resume_trigger = "next run"
        card.transition_to(State.WAITING)
        store.upsert_card(card)
        expired.append(card.id)
    return expired


def run_ending(store: Store, discovery_complete: bool | None = None) -> str:
    """completed: every selected card terminal. incomplete: any card never
    processed, or discovery itself incomplete. Otherwise
    completed_with_exceptions: every card was processed and the rest hold
    with a recorded reason and owner."""
    assert store.header is not None, "create_run first"
    if discovery_complete is None:
        discovery_complete = store.header.discovery_complete
    states = [store.cards[i].state for i in store.header.scope_ids]
    if not discovery_complete or State.NEW in states:
        return "incomplete"
    if all(s in TERMINAL for s in states):
        return "completed"
    return "completed_with_exceptions"


CONTINUATION_KINDS = ("watcher", "scheduled", "none")


def finish_run(store: Store, continuation: dict,
               discovery_complete: bool = True) -> str:
    """Record the stop reason and the one explicit continuation state."""
    assert store.header is not None, "create_run first"
    if continuation.get("kind") not in CONTINUATION_KINDS:
        raise StoreError(f"continuation kind must be one of "
                         f"{', '.join(CONTINUATION_KINDS)}")
    ending = run_ending(store, discovery_complete)
    store.header.discovery_complete = discovery_complete
    store.header.continuation = dict(continuation)
    store.header.stop_reason = ending
    store.set_header(store.header)
    return ending
