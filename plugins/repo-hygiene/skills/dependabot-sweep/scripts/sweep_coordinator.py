#!/usr/bin/env python3
"""Coordinator for dependabot-sweep, Slice 1: reconcile, schedule, collect.

The coordinator owns inventory, scheduling, recovery, and reporting. It
never merges. Worker returns are outcome records, not prose: every
assigned card must resolve to merged, ready, hold, unknown, or closed.

Stdlib only. GitHub observations enter as plain data (the `observed`
mappings), so every path below is testable without the network.
"""

from __future__ import annotations

import copy
import re
import math
import sys
import os
import time
from copy import deepcopy
from urllib.parse import urlparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sweep_core import (  # noqa: E402
    Card, Issue, K_REASONS, RunHeader, SEVERITIES, State, Store, StoreError,
    TERMINAL, TRANSITIONS, transactional, utc_now,
)
import sweep_discovery as discovery_evidence  # noqa: E402

HOLD_STATES = frozenset({State.WAITING, State.BLOCKED, State.NEEDS_OWNER})
# Outcome vocabulary -> the state a worker claims. "hold" names its own.
OUTCOME_TARGETS = {"merged": State.MERGED, "ready": State.READY,
                   "unknown": State.UNKNOWN, "closed": State.CLOSED}


def _canonical_repo_id(header: RunHeader, cards, repo_id: str) -> str:
    """Reuse one spelling for GitHub's case-insensitive repository identity."""
    known = list(header.authority.get("repositories", {}))
    known.extend(card.repo_id for card in cards)
    return next((rid for rid in known if rid.casefold() == repo_id.casefold()), repo_id)


@transactional
def create_run(store: Store, run_id: str, mode: str, authorization: str,
               discoveries: list, scope_fixed: bool = True,
               exclusions: list | None = None,
               cutoff: str = "", authority: dict | None = None) -> RunHeader:
    """Persist the run header and one NEW card per discovered PR.

    Card ids are assigned in discovery order and never renumbered.
    `cutoff` records the discovery instant a fixed scope was taken at.
    """
    if store.header is not None:
        raise StoreError(f"run {store.header.run_id!r} already exists")
    discoveries = discovery_evidence.normalize(discoveries)
    if exclusions is not None and (not isinstance(exclusions, list)
                                   or not all(isinstance(e, str) and e for e in exclusions)):
        raise StoreError("exclusions must be a list of nonempty owner, repository, or PR identities")
    discovered_at = cutoff or utc_now()
    discovered_epoch = discovery_evidence.timestamp(discovered_at, "cutoff")
    for item in discoveries:
        if item.get("pr_created_at") and discovery_evidence.timestamp(item["pr_created_at"]) > discovered_epoch:
            raise StoreError("PR creation cannot follow its discovery observation")
    header = RunHeader(run_id=run_id, mode=mode,
                       scope_fixed=scope_fixed, cutoff=cutoff,
                       authorization=authorization,
                       exclusions=list(exclusions or []),
                       started_at=utc_now(), authority=deepcopy(authority or {}))
    for discovery in discoveries:
        rid = _canonical_repo_id(header, store.cards.values(),
                                 f"{discovery['org']}/{discovery['repo']}")
        discovery["org"], discovery["repo"] = rid.split("/")
        selected, reason = _arrival_selection(header, discovery, initial=True)
        if selected and authority is not None and ("repositories" in authority
                                                   or "discovery_scopes" in authority):
            grant, _ = discovery_evidence.repository_grant(
                header.authority, rid, discovery.get("visibility", ""))
            header.authority.setdefault("repositories", {})[rid] = grant
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
            pr_created_at=discovery.get("pr_created_at", ""),
            discovered_at=discovered_at,
            created_at=utc_now(), updated_at=utc_now(),
        )
        if not selected:
            _unselected_evidence(card, reason, discovered_at)
        store.upsert_card(card)
        if selected:
            header.scope_ids.append(card_id)
        else:
            header.discovery_complete = False
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


def _protected(store: Store, attempt, confirmed_stopped: set) -> bool:
    """A foreign or unknown owner stays protected until its stop is verified.

    A heartbeat's age cannot establish that a worker has stopped mutating.
    Missing session ids cannot establish same-session ownership.
    """
    if attempt is None:
        return True
    if attempt.id in confirmed_stopped:
        return False
    return not (attempt.session and store.session
                and attempt.session == store.session)


def _unlock(store: Store, repo_id: str, holder: str) -> None:
    if store.locks is not None and holder:
        store.locks.release(repo_id, holder)


@transactional
def reconcile(store: Store, observed: dict, live_attempts: set,
              now: float | None = None,
              stale_after_secs: float | None = None,
              confirmed_stopped=()) -> dict:
    """Restart/crash reconciliation. Runs before any new mutation.

    `observed` maps card id -> {"merged": bool|None, "commit": str,
    "at": str}. `live_attempts` holds attempt ids known to still run.
    Every dead attempt is marked crashed; every orphaned lease is
    reconciled read-only against observed reality; ambiguity quarantines
    the repository. Quarantined repositories are reconciled the same way:
    each UNKNOWN card needs a decisive observation, and the quarantine
    lifts only when none remains. A recorded hold is truth: an unmerged
    observation confirms it, only UNKNOWN cards are restored, and only
    NEW cards are rescheduled. Same-session recovery requires matching,
    nonempty session ids. Other attempts, including quarantined attempts,
    stay protected unless their ids are supplied in `confirmed_stopped`
    after their processes are verified stopped. Age and `stale_after_secs`
    never establish that fact; the timing parameters are retained for
    compatibility with older callers.
    """
    confirmed_stopped = set(confirmed_stopped)
    conflict = confirmed_stopped & set(live_attempts)
    if conflict:
        raise StoreError(f"attempts cannot be live and confirmed stopped: "
                         f"{', '.join(sorted(conflict))}")
    unknown = confirmed_stopped - set(store.diary)
    if unknown:
        raise StoreError(f"unknown confirmed-stopped attempts: "
                         f"{', '.join(sorted(unknown))}")
    summary = {"crashed": [], "merged": [], "rescheduled": [],
               "retained": [], "quarantined": [], "resolved": []}
    crashed = []
    for attempt in store.diary.values():
        if not attempt.result and attempt.id not in live_attempts \
                and not _protected(store, attempt, confirmed_stopped):
            attempt.result = "crashed"
            crashed.append(attempt)
    for lease in list(store.leases.leases.values()):
        if lease.state != "held" or lease.holder in live_attempts \
                or _protected(store, store.diary.get(lease.holder),
                              confirmed_stopped):
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
        if lease.holder in live_attempts or (lease.holder and _protected(
                store, store.diary.get(lease.holder), confirmed_stopped)):
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


@transactional
def schedule(store: Store, model: str = "", pr_budget_secs: float | None = None,
             now: float | None = None, wake=(), capacity: int = 1,
             batch_size: int = 1, reserve_secs: float = 30) -> list:
    """Issue one tasking per free repo that holds schedulable cards: NEW,
    or READY awaiting an authorized merge after a fresh evaluation, plus
    any hold card named in `wake` (its resume trigger fired). Holds are
    never dispatched on their own; a woken card must exist, be a hold,
    and have budget left.

    Defaults admit at most one repository and one card, with 30 seconds
    reserved for validation. `capacity` is the total occupied repository
    limit, not an additional slot allowance. Returns tasking records
    {attempt_id, repo_id, card_ids}. Quarantined
    and held repositories are never scheduled. A repository whose last
    attempt crashed gets a successor attempt id (AGT-00n.k+1) on the same
    card ids, never new card ids. Each card's deadline is set once, when
    first scheduled with a budget; successors inherit it because handoffs
    and retries never reset the clock. A card deadline never outlives the
    run deadline. With repository lock files, a repo another session
    holds is skipped.
    """
    assert store.header is not None, "create_run first"
    for name, value, minimum in (("capacity", capacity, 0),
                                 ("batch_size", batch_size, 1)):
        if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
            raise StoreError(f"{name} must be an integer >= {minimum}")
    for name, value, positive in (("reserve_secs", reserve_secs, False),
                                  ("pr_budget_secs", pr_budget_secs, True)):
        if name == "reserve_secs" and value is None:
            raise StoreError("reserve_secs must be a finite nonnegative number")
        if value is not None and (isinstance(value, bool)
                or not isinstance(value, (float, int)) or not math.isfinite(value)
                or value < 0 or (positive and value == 0)):
            raise StoreError(f"{name} must be a finite "
                             f"{'positive' if positive else 'nonnegative'} number")
    moment = time.time() if now is None else now
    if not math.isfinite(moment):
        raise StoreError("now must be finite")
    run_deadline = store.header.deadline_epoch
    if run_deadline and (not math.isfinite(run_deadline)
                         or moment >= run_deadline):
        return []  # Refuse before allocating ids, leases, or repo locks.
    occupied = _occupied_repositories(store)
    slots = max(0, capacity - len(occupied))
    def admissible(card, at):
        deadlines = [d for d in (run_deadline, card.deadline_epoch) if d]
        if not card.deadline_epoch and pr_budget_secs is not None:
            deadlines.append(at + pr_budget_secs)
        return all(math.isfinite(d) and at < d and at + reserve_secs < d
                   for d in deadlines)

    for card_id in wake:
        card = store.cards.get(card_id)
        if card is None:
            raise StoreError(f"cannot wake unknown card {card_id!r}")
        if card.state not in HOLD_STATES:
            raise StoreError(f"{card_id}: only a hold can be woken, not "
                             f"{card.state.value}")
        if not admissible(card, moment):
            raise StoreError(f"{card_id}: budget exhausted; continue in a "
                             f"new run instead of waking it")
        if card.repo_id.casefold() in occupied:
            raise StoreError(f"{card_id}: repository {card.repo_id} is occupied")
        if card_id not in store.header.scope_ids and not card.replaces:
            raise StoreError(f"{card_id}: unselected arrival needs scope reconciliation")
    if not slots:
        return []
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
        if not admissible(card, moment):
            continue  # dead work is expired, never dispatched
        if card.repo_id.casefold() in occupied:
            continue
        # New-format authority must name every admitted repository. A raw
        # discovery cannot broaden the frozen mutation grants.
        authority = store.header.authority
        if discovery_evidence.excluded(store.header.exclusions, card.repo_id, card.number, card.url):
            continue
        if "repositories" in authority:
            grant, _ = discovery_evidence.repository_grant(authority, card.repo_id)
            if grant is None:
                continue
        by_repo.setdefault(card.repo_id, []).append(card_id)
    taskings = []
    for repo_id, card_ids in by_repo.items():
        if len(taskings) >= slots:
            break
        if repo_id.casefold() in occupied:
            continue  # Legacy case aliases still share one repository slot.
        admitted_at = time.time() if now is None else now
        card_ids = [i for i in card_ids
                    if admissible(store.cards[i], admitted_at)][:batch_size]
        if not card_ids:
            continue
        attempt_id, dead = _peek_attempt_id(store, card_ids)
        if store.locks is not None \
                and not store.locks.claim(repo_id, attempt_id):
            continue  # another session holds this repository
        # A filesystem claim can block. Recheck the actual admission instant
        # before allocating any durable id, attempt, lease, or PR deadline.
        admitted_at = time.time() if now is None else now
        if not all(admissible(store.cards[i], admitted_at) for i in card_ids):
            if store.locks is not None:
                store.locks.release(repo_id, attempt_id)
            continue
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
                card.deadline_epoch = admitted_at + pr_budget_secs
                if store.header.deadline_epoch:
                    card.deadline_epoch = min(card.deadline_epoch,
                                              store.header.deadline_epoch)
            store.upsert_card(card)
        taskings.append({"attempt_id": attempt_id, "repo_id": repo_id,
                         "card_ids": list(card_ids)})
        occupied.add(repo_id.casefold())
    if taskings:
        store.record_ids()
    return taskings


def _occupied_repositories(store: Store) -> set:
    """Count each occupied repo once, regardless of session or lock age.

    Unknown/foreign lock payloads consume capacity too. Recovery alone may
    release a claim; scheduling never guesses that an owner has stopped.
    """
    occupied = {rid for rid, lease in store.leases.leases.items()
                if lease.state in ("held", "quarantined")}
    occupied.update(c.repo_id for c in store.cards.values() if c.state == State.UNKNOWN)
    for attempt in store.diary.values():
        if not attempt.result:
            repos = {store.cards[i].repo_id for i in attempt.assigned if i in store.cards}
            occupied.update(repos or {f"unknown-attempt:{attempt.id}"})
    if store.locks is not None and os.path.isdir(store.locks.directory):
        for entry in os.scandir(store.locks.directory):
            if entry.name.endswith(".lock"):
                occupied.add(entry.name[:-5].replace("__", "/", 1))
    return {repo_id.casefold() for repo_id in occupied}


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
                   phase="assigned", outstanding=list(card_ids))


@transactional
def apply_outcome(store: Store, attempt_id: str, results: list) -> dict:
    """Collect one worker's outcome records.

    Each result resolves one assigned card: merged (requires commit sha
    and timestamp), ready (requires evaluated head, reason, and evidence;
    prepared but unmerged), hold (requires target state, known reason code, known
    severity, reason, action, owner), unknown (requires an operation
    note; quarantines the repo), or closed (requires a reason). The whole
    batch is validated before any card changes: one bad record refuses
    the batch and leaves cards, attempt, and lease untouched. Each card
    returns once per attempt; batches cumulatively resolve outstanding cards.
    """
    attempt = store.diary.get(attempt_id)
    if attempt is None:
        raise StoreError(f"unknown attempt {attempt_id}")
    if attempt.result:
        raise StoreError(f"attempt {attempt_id} already "
                         f"{attempt.result}")
    if attempt.session != store.session:
        raise StoreError(f"attempt {attempt_id} belongs to coordinator "
                         f"session {attempt.session!r}, not {store.session!r}")
    # Legacy attempts started with an empty outstanding list. A completed
    # return is rejected above, so an active empty list means no results yet.
    outstanding = list(attempt.outstanding or attempt.assigned)
    for card_id in attempt.assigned:
        card = store.cards[card_id]
        lease = store.leases.get(card.repo_id)
        if lease.state not in ("held", "quarantined") \
                or lease.holder != attempt_id or card_id not in lease.pr_ids:
            raise StoreError(f"{card_id}: current repository lease does not "
                             f"belong to {attempt_id}")
        if not card.attempts or card.attempts[-1] != attempt_id:
            raise StoreError(f"{card_id}: {attempt_id} is not the current "
                             f"attempt generation")
    seen: set = set()
    for result in results:
        card_id = result.get("card_id", "")
        if card_id not in attempt.assigned:
            raise StoreError(f"{attempt_id} was not assigned {card_id!r}")
        if card_id not in outstanding:
            raise StoreError(f"{card_id}: already returned by {attempt_id}")
        if card_id in seen:
            raise StoreError(f"{card_id}: resolved twice in one batch")
        seen.add(card_id)
        card = store.cards[card_id]
        lease = store.leases.get(card.repo_id)
        if lease.state == "quarantined" \
                and result.get("outcome") in ("merged", "ready"):
            raise StoreError(f"{card_id}: repository {card.repo_id} is "
                             f"quarantined; reconcile before claiming "
                             f"{result['outcome']}")
        _validate_result(card, result)
        for followup in result.get("followups", []):
            _validate_followup_links(store, followup, [card.id])
    applied = []
    for result in results:
        card = store.cards[result["card_id"]]
        outcome = result["outcome"]
        previous = card.to_dict()
        if outcome == "merged":
            _apply_merged(card, result)
        elif outcome == "ready":
            _apply_evaluated_head(store, card, result)
            _apply_ready(card, result)
        elif outcome == "hold":
            _apply_evaluated_head(store, card, result)
            _apply_hold(card, result)
        elif outcome == "unknown":
            _apply_unknown(store, card, result)
        else:
            _apply_closed(card, result)
        _record_outcome_context(card, result, previous)
        card.last_observation = utc_now()
        store.upsert_card(card)
        if result.get("incident"):
            link_incident(store, card, result)
        for followup in result.get("followups", []):
            record_followup(store, followup, [card.id])
        applied.append(card.id)
    attempt.last_progress_at = utc_now()
    attempt.phase = "returned"
    pending = [c for c in outstanding if c not in applied]
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
    _validate_outcome_context(result)
    if outcome == "ready" or "head_sha" in result:
        head = result.get("head_sha")
        if not isinstance(head, str) \
                or not re.fullmatch(r"[0-9a-fA-F]{40}", head):
            raise StoreError(f"{card.id}: {outcome} requires head_sha as a "
                             f"full 40-hex commit SHA")
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
        if target == State.NEEDS_OWNER:
            decision = result.get("decision", {})
            for key in ("why", "approve_effect", "decline_effect",
                        "recommendation"):
                if not _nonempty_text(decision.get(key)):
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
    if outcome in ("hold", "ready") and target == card.state:
        return  # fresh evaluations update their existing state in place
    if target not in TRANSITIONS[card.state]:
        raise StoreError(f"{card.id}: {card.state.value} -> {target.value} "
                         f"is not a worker transition")


DECISION_SCOPES = frozenset({"merge", "close", "settings", "repair", "other"})
BLOCKER_KINDS = frozenset({"technical", "review", "evidence", "decision"})
CONDITION_FIELDS = frozenset({"reason_code", "reason_line", "evidence", "action",
                              "action_owner", "resume_trigger", "observed_at",
                              "head_sha"})


def _nonempty_text(value) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _validate_evidence(value, *, strict=False, required=False) -> None:
    if not isinstance(value, list) or (required and not value):
        raise StoreError("evidence must be a list of evidence records")
    for item in value:
        if not isinstance(item, dict) or not item:
            raise StoreError("evidence entries must be nonempty objects")
        if strict and not all(_nonempty_text(item.get(k))
                              for k in ("what", "establishes")):
            raise StoreError("follow-up evidence requires what and establishes")
        if "head_sha" in item and not re.fullmatch(
                r"[0-9a-fA-F]{40}", str(item["head_sha"])):
            raise StoreError("evidence head_sha must be a full 40-hex SHA")


def _validate_condition(value, *, blocker=False) -> None:
    allowed = CONDITION_FIELDS | ({"kind"} if blocker else set())
    if not isinstance(value, dict) or set(value) - allowed:
        raise StoreError("invalid condition record or unknown condition fields")
    if not isinstance(value.get("reason_code"), str) or value.get("reason_code") not in K_REASONS \
            or not _nonempty_text(value.get("reason_line")):
        raise StoreError("condition requires known reason_code and reason_line")
    if blocker and (not isinstance(value.get("kind"), str) or value.get("kind") not in BLOCKER_KINDS):
        raise StoreError("blocker requires technical, review, evidence, or decision kind")
    if blocker and value["reason_code"] == "K14":
        raise StoreError("K14 records an execution_stop, not a technical blocker")
    for key in ("action", "action_owner", "resume_trigger", "observed_at"):
        if key in value and not _nonempty_text(value[key]):
            raise StoreError(f"condition {key} must be nonempty text")
    if "head_sha" in value and not re.fullmatch(
            r"[0-9a-fA-F]{40}", str(value["head_sha"])):
        raise StoreError("condition head_sha must be a full 40-hex SHA")
    if "evidence" in value:
        _validate_evidence(value["evidence"])


def _validate_outcome_context(result: dict) -> None:
    """Validate reporting additions without weakening legacy outcome gates."""
    if "evidence" in result:
        _validate_evidence(result["evidence"])
    if "blockers" in result:
        if not isinstance(result["blockers"], list):
            raise StoreError("blockers must be a list")
        for blocker in result["blockers"]:
            _validate_condition(blocker, blocker=True)
        if result.get("outcome") == "ready" and result["blockers"]:
            raise StoreError("READY cannot claim unresolved blockers; return a hold")
    if "execution_stop" in result:
        if result["execution_stop"] != {}:
            _validate_condition(result["execution_stop"])
    if "owner_hold" in result:
        value = result["owner_hold"]
        fields = {"source", "reason", "active", "scope", "actor", "recorded_at", "head_sha"}
        if not isinstance(value, dict) or set(value) - fields \
                or not all(_nonempty_text(value.get(k)) for k in ("source", "reason")):
            raise StoreError("owner_hold requires an actual source and reason")
        if "active" in value and not isinstance(value["active"], bool):
            raise StoreError("owner_hold.active must be boolean")
        if "scope" in value and (not isinstance(value["scope"], str) or value["scope"] not in DECISION_SCOPES):
            raise StoreError("invalid owner_hold scope")
        for key in ("actor", "recorded_at"):
            if key in value and not _nonempty_text(value[key]):
                raise StoreError(f"owner_hold.{key} must be nonempty text")
        if "head_sha" in value and not re.fullmatch(
                r"[0-9a-fA-F]{40}", str(value["head_sha"])):
            raise StoreError("owner_hold.head_sha must be a full 40-hex SHA")
    if "decision" in result:
        decision = result["decision"]
        if not isinstance(decision, dict):
            raise StoreError("decision must be an object")
        for key in ("why", "approve_effect", "decline_effect", "recommendation", "source"):
            if key in decision and not _nonempty_text(decision[key]):
                raise StoreError(f"decision.{key} must be nonempty text")
        if "scope" in decision and (not isinstance(decision["scope"], str) or decision["scope"] not in DECISION_SCOPES):
            raise StoreError("invalid decision.scope")
        if "group_key" in decision and not _nonempty_text(decision["group_key"]):
            raise StoreError("decision.group_key must be nonempty text")
    incident = result.get("incident")
    if incident is not None and (not isinstance(incident, dict) or not all(
            _nonempty_text(incident.get(k)) for k in ("key", "claim"))):
        raise StoreError("incident requires key and claim")
    if "followups" in result:
        if not isinstance(result["followups"], list):
            raise StoreError("followups must be a list")
        for followup in result["followups"]:
            _validate_followup_fields(followup)


def _merge_records(previous: list, fresh: list) -> list:
    merged = copy.deepcopy(previous)
    for record in fresh:
        if record not in merged:
            merged.append(copy.deepcopy(record))
    return merged


def _bound_records(records: list, head: str) -> list:
    bound = copy.deepcopy(records)
    for item in bound:
        if head and "head_sha" not in item:
            old = item.get("head")
            # Evaluator receipts historically used an abbreviated `head`.
            # Expand a matching prefix only with this identity-verified result.
            if not old or (isinstance(old, str) and head.startswith(old.lower())):
                item["head_sha"] = head
    return bound


def _primary_blocker(value: dict) -> dict:
    code = value.get("reason_code", "")
    if code not in K_REASONS or code == "K14" or not value.get("reason_line"):
        return {}
    kind = ("review" if code in ("K07", "K08", "K15") else
            "evidence" if code in ("K11", "K13") else
            "decision" if code == "K16" else "technical")
    return {"kind": kind, **{key: copy.deepcopy(value[key])
                            for key in CONDITION_FIELDS if value.get(key)}}


def _record_outcome_context(card: Card, result: dict, previous: dict) -> None:
    """Keep prior-head receipts while replacing only explicitly evaluated facts.

    A deadline is an execution stop, not a new diagnosis. Missing head binding
    remains unknown rather than turning an old receipt into current readiness.
    These fields document conditions; they never authorize a mutation.
    """
    if any(previous.get(k) for k in ("reason_line", "evidence", "blockers",
                                      "execution_stop", "owner_hold")):
        record = {key: copy.deepcopy(previous.get(key)) for key in (
            "head_sha", "state", "reason_code", "reason_line", "evidence",
            "blockers", "execution_stop", "owner_hold", "last_observation")}
        card.condition_history = _merge_records(card.condition_history, [record])
    head = result.get("head_sha", "").lower()
    if result["outcome"] == "merged" and not head:
        head = card.head_sha
    card.evidence = _merge_records(previous.get("evidence", []),
                                   _bound_records(result.get("evidence", []), head))
    if "blockers" in result:
        card.blockers = _bound_records(result["blockers"], head)
    elif result["outcome"] in ("ready", "merged", "closed"):
        card.blockers = []
    elif result.get("reason_code") == "K14":
        card.blockers = copy.deepcopy(previous.get("blockers", []))
        if not card.blockers:
            blocker = _primary_blocker(previous)
            card.blockers = [blocker] if blocker else []
    else:
        blocker = _primary_blocker({**result, "head_sha": head})
        card.blockers = [blocker] if blocker else []
    if "execution_stop" in result:
        card.execution_stop = copy.deepcopy(result["execution_stop"])
    elif result.get("reason_code") == "K14":
        card.execution_stop = {key: copy.deepcopy(result[key])
                               for key in CONDITION_FIELDS if result.get(key)}
        card.execution_stop.setdefault("observed_at", utc_now())
    elif result["outcome"] in ("ready", "merged", "closed"):
        card.execution_stop = {}
    if "owner_hold" in result:
        card.owner_hold = copy.deepcopy(result["owner_hold"])
        card.owner_hold.setdefault("active", True)
        card.owner_hold.setdefault("recorded_at", utc_now())


def _apply_merged(card: Card, result: dict) -> None:
    card.merge_commit = result["commit_sha"]
    card.merged_at = result["merged_at"]
    card.severity = "none"
    card.transition_to(State.MERGED)


def _apply_evaluated_head(store: Store, card: Card, result: dict) -> None:
    """Store an identity-verified head and retain only approval bound to it.

    READY always supplies a head. HOLD supplies one only after the
    evaluator's identity check passed; unreadable observations omit it.
    An explicit matching approval remains valid even if discovery was stale.
    Legacy approval ids are bound to the card's previously stored head.
    """
    if "head_sha" not in result:
        return
    head = result["head_sha"].lower()
    authority = store.header.authority if store.header else {}
    records = authority.get("approval_records", {})
    if card.id in records:
        record = records[card.id]
        approved_head = (record.get("head_sha", "")
                         if isinstance(record, dict) else "")
    else:
        approved_head = card.head_sha
    approved = authority.get("approved", [])
    if not isinstance(approved_head, str) or approved_head.lower() != head:
        changed = False
        if card.id in approved:
            authority["approved"] = [i for i in approved if i != card.id]
            changed = True
        if card.id in records:
            del records[card.id]
            changed = True
        if changed:
            store.set_header(store.header)
    card.head_sha = head


def _apply_ready(card: Card, result: dict) -> None:
    """A worker evaluated the card and found it mergeable but did not
    merge (e.g. gated preparation)."""
    card.reason_line = result["reason_line"]
    card.reason_code = ""
    card.action = result.get("action", "Run fresh merge gates in the next authorized attempt")
    card.action_owner = result.get("action_owner", "sweeper")
    card.resume_trigger = result.get("resume_trigger", "fresh gates and required authority")
    card.decision = {}
    card.severity = "none"
    if card.state == State.READY:
        card.updated_at = utc_now()
    else:
        card.transition_to(State.READY)


def _apply_hold(card: Card, result: dict) -> None:
    target = State(result["state"])
    card.reason_code = result["reason_code"]
    card.reason_line = result["reason_line"]
    card.severity = result.get("severity", "unknown")
    card.confidence = result.get("confidence", "unknown")
    card.action = result["action"]
    card.action_owner = result["action_owner"]
    card.resume_trigger = result.get("resume_trigger", "")
    if target == State.NEEDS_OWNER:
        card.decision = result["decision"]
    else:
        card.decision = {}
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


@transactional
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


@transactional
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
    old.reason_line = (f"Superseded by {new_id}; delivery requires verified "
                       "replacement merge proof.")
    if old.state != State.CLOSED:  # a worker may have closed it first
        old.transition_to(State.CLOSED)
    store.upsert_card(old)
    store.record_ids()
    return new


def _arrival_selection(header, fields, initial=False, known_repo=False):
    rid = f"{fields['org']}/{fields['repo']}"
    if discovery_evidence.excluded(header.exclusions, rid, fields["number"], fields.get("url", "")):
        return False, "explicit run exclusion"
    if header.scope_fixed and not initial:
        return False, "fixed scope; new discovery remains unselected"
    if not header.authority or ("repositories" not in header.authority
                                and "discovery_scopes" not in header.authority):
        # Old library journals lack frozen authority. Existing repositories
        # remain usable; a new repository requires scope reconciliation.
        return (True, "legacy selected repository") if initial or known_repo else (
            False, "repository has no frozen discovery scope; scope reconciliation required")
    grant, reason = discovery_evidence.repository_grant(
        header.authority, rid, fields.get("visibility", ""))
    return grant is not None, reason


def _unselected_evidence(card, reason, observed_at):
    card.reason_line = f"Unselected discovery: {reason}."
    card.action = "Reconcile this discovery with the saved scope before any worker admission."
    card.action_owner = "owner"
    card.resume_trigger = "scope reconciliation or a new authorized run"
    card.evidence.append({"kind": "discovery_selection", "selected": False,
                          "observed_at": observed_at, "reason": reason})


@transactional
def register_arrival(store: Store, fields: dict, observed_at: str = "") -> Card:
    """Record a PR discovered after the run started.

    New arrivals get fresh ids; existing ids are never renumbered. In an
    evolving run the card joins the selected set; in a fixed-scope run
    it is recorded and reported but never selected or scheduled.
    """
    assert store.header is not None, "create_run first"
    fields = discovery_evidence.normalize([fields])[0]
    rid = _canonical_repo_id(store.header, store.cards.values(),
                             f"{fields['org']}/{fields['repo']}")
    fields["org"], fields["repo"] = rid.split("/")
    for existing in store.cards.values():
        if existing.repo_id.casefold() == rid.casefold() and existing.number == fields["number"]:
            return existing  # Never overwrite an active worker or evaluated head.
    observed_at = observed_at or utc_now()
    discovered_epoch = discovery_evidence.timestamp(observed_at)
    if fields.get("pr_created_at") and discovery_evidence.timestamp(fields["pr_created_at"]) > discovered_epoch:
        raise StoreError("PR creation cannot follow its discovery observation")
    known = any(c.repo_id.casefold() == rid.casefold() for c in store.cards.values()
                if c.id in store.header.scope_ids)
    selected, reason = _arrival_selection(store.header, fields, known_repo=known)
    if selected and ("repositories" in store.header.authority
                     or "discovery_scopes" in store.header.authority):
        grant, _ = discovery_evidence.repository_grant(
            store.header.authority, rid, fields.get("visibility", ""))
        repositories = store.header.authority.setdefault("repositories", {})
        canonical = next((k for k in repositories if k.casefold() == rid.casefold()), rid)
        fields["org"], fields["repo"] = canonical.split("/")
        repositories[canonical] = grant
    card_id = store.ids.next("PR")
    card = Card(id=card_id, org=fields["org"], repo=fields["repo"],
                number=fields["number"], url=fields.get("url", ""),
                title=fields.get("title", ""),
                owner=fields.get("owner", ""),
                head_sha=fields.get("head_sha", ""),
                base_ref=fields.get("base_ref", ""),
                pr_created_at=fields.get("pr_created_at", ""),
                discovered_at=observed_at,
                created_at=utc_now(), updated_at=utc_now())
    if not selected:
        _unselected_evidence(card, reason, observed_at)
    elif store.header.deadline_epoch and discovered_epoch >= store.header.deadline_epoch:
        # Registering scope is allowed after expiry. Worker admission is not.
        card.reason_code = "K14"
        card.reason_line = "First discovered after the run deadline; remains unassessed."
        card.evidence.append({"kind": "discovery_budget", "observed_at": observed_at,
                              "run_deadline_epoch": store.header.deadline_epoch})
    store.upsert_card(card)
    if selected:
        store.header.scope_ids.append(card_id)
    # The old inventory no longer describes the current selected scope.
    store.header.discovery_complete = False
    store.set_header(store.header)
    store.record_ids()
    return card


@transactional
def discover_run(store: Store, payload: dict) -> dict:
    """Refresh explicit inventory and append arrivals without touching PR state.

    Completeness belongs to a timestamped, exact coverage claim. Absence
    from a search is never a close/merge observation. A final incomplete
    search replaces the previous current snapshot as incomplete.
    """
    assert store.header is not None, "create_run first"
    header = store.header
    discoveries, visibility = discovery_evidence.validate_inventory(
        payload, header.discovery_snapshot)
    authority = header.authority
    reasons = []
    if not discovery_evidence.same_coverage(payload["coverage"], discovery_evidence.coverage(authority)):
        reasons.append("inventory coverage does not exactly match frozen discovery scope")
    repositories = authority.get("repositories", {})
    # Extend grants only from saved selectors and explicit visibility evidence.
    # Raw payload authority, mode, repairs, and approval fields are ignored.
    authorized_inventory = set()
    for entry in payload["repositories"]:
        rid = entry["nameWithOwner"]
        if discovery_evidence.excluded(header.exclusions, rid):
            continue
        grant, _ = discovery_evidence.repository_grant(authority, rid, visibility[rid.casefold()])
        if grant is None:
            continue
        canonical = next((k for k in repositories if k.casefold() == rid.casefold()), rid)
        authorized_inventory.add(canonical)
        # Inventory covers all repositories selected by the frozen discovery
        # selectors, including quiet repositories in a fixed run. Recording
        # their derived grant does not add cards to the fixed execution scope.
        if "discovery_scopes" in authority:
            repositories[canonical] = grant
    if "repositories" in authority:
        authority["repositories"] = repositories
    if set(payload["scope_repositories"]) != authorized_inventory:
        reasons.append("scope_repositories differs from the authorized visibility inventory")
    if authorized_inventory != set(repositories):
        reasons.append("inventory omits or changes previously authorized repositories")
    store.set_header(header)
    before = set(store.cards)
    open_ids, unselected = [], []
    for fields in discoveries:
        card = register_arrival(store, fields, observed_at=payload["observed_at"])
        # Inventory scope is independent of worker selection. A fixed run
        # still counts authorized late arrivals without admitting them.
        if card.repo_id in authorized_inventory and not discovery_evidence.excluded(
                header.exclusions, card.repo_id, card.number, card.url):
            open_ids.append(card.id)
        else:
            reasons.append(f"{card.id}: discovery is outside authorized repository, "
                           "visibility, or exclusion scope")
        if card.id not in header.scope_ids:
            unselected.append(card.id)
    complete = payload["complete"] and not reasons
    snapshot = {"observed_at": payload["observed_at"], "complete": complete,
                "coverage": deepcopy(payload["coverage"]),
                "scope_ids": list(header.scope_ids),
                "scope_repositories": sorted(payload["scope_repositories"]),
                "open_card_ids": open_ids, "unselected_card_ids": unselected,
                "source": payload["source"], "incomplete_reasons": sorted(set(reasons)),
                "evidence": {"claimed_complete": payload["complete"],
                             "repositories": deepcopy(payload["repositories"]),
                             "discoveries": deepcopy(payload["discoveries"])}}
    header.discovery_snapshot = snapshot
    header.discovery_complete = complete
    store.set_header(header)
    return {"snapshot": deepcopy(snapshot), "new_card_ids": [i for i in store.cards if i not in before]}


@transactional
def refresh_card(store: Store, card_id: str, snapshot: dict) -> dict:
    """Persist current facts separately from outcomes and mutation authority."""
    if card_id not in store.cards:
        raise StoreError(f"unknown card {card_id!r}")
    card = store.cards[card_id]
    observation = discovery_evidence.read_only_observation(card, snapshot)
    card.latest_observation = observation
    card.evidence.append({"kind": "read_only_refresh", **deepcopy(observation)})
    store.upsert_card(card)
    return deepcopy(observation)


def delivery_counts(store: Store) -> dict:
    """Count delivered dependency updates without double counting.

    Direct merges plus originals whose update arrived via a merged
    replacement. Replacement cards are linked evidence, not extra
    selected updates; supporting work stays excluded by construction.
    """
    cards = ([store.cards[i] for i in store.header.scope_ids]
             if store.header else list(store.cards.values()))
    direct = sum(1 for c in cards if c.state == State.MERGED)
    via_replacement = sum(
        1 for c in cards
        if c.state == State.CLOSED and c.replaced_by
        and store.cards.get(c.replaced_by, c).state == State.MERGED
        and store.cards[c.replaced_by].replaces == c.id)
    return {"direct": direct, "via_replacement": via_replacement,
            "total": direct + via_replacement}


def describe_subset(store: Store, ids: list) -> list:
    """Answer a follow-up about a subset of cards.

    Resolves through the header's read-only query: the run's objective
    is preserved no matter how narrow the question.
    """
    assert store.header is not None, "create_run first"
    return [store.cards[i] for i in store.header.query_subset(ids)]


FOLLOWUP_STATUSES = frozenset({"open", "in_progress", "blocked", "resolved", "dismissed"})
FOLLOWUP_ATTRIBUTIONS = frozenset({"caused_by_sweep", "pre_existing", "unknown", "not_applicable"})
FOLLOWUP_MUTABLE = frozenset({"claim", "reason_code", "action", "action_owner", "status",
                              "attribution", "attribution_note", "evidence", "external_links"})
FOLLOWUP_FIELDS = FOLLOWUP_MUTABLE | {"key", "repo_id", "target", "kind"}


def _validate_followup_fields(fields: dict, *, update=False) -> None:
    allowed = FOLLOWUP_MUTABLE if update else FOLLOWUP_FIELDS
    if not isinstance(fields, dict) or not fields or set(fields) - allowed:
        raise StoreError("follow-up requires known, nonempty record/update fields")
    if not update:
        for key in ("key", "claim", "action", "action_owner"):
            if not _nonempty_text(fields.get(key)):
                raise StoreError(f"follow-up requires {key}")
        if not (_nonempty_text(fields.get("repo_id")) or _nonempty_text(fields.get("target"))):
            raise StoreError("follow-up requires repo_id or target")
    for key in ("key", "claim", "action", "action_owner", "repo_id", "target", "attribution_note"):
        if key in fields and not _nonempty_text(fields[key]):
            raise StoreError(f"follow-up {key} must be nonempty text")
    if "repo_id" in fields and not re.fullmatch(r"[^/\s]+/[^/\s]+", fields["repo_id"]):
        raise StoreError("follow-up repo_id must identify owner/repository")
    if "reason_code" in fields and (not isinstance(fields["reason_code"], str) or fields["reason_code"] not in K_REASONS):
        raise StoreError("follow-up reason_code must be a known K code")
    if "kind" in fields and fields["kind"] not in ("incident", "followup"):
        raise StoreError("follow-up kind must be incident or followup")
    if "status" in fields and (not isinstance(fields["status"], str) or fields["status"] not in FOLLOWUP_STATUSES):
        raise StoreError("invalid follow-up status")
    if "attribution" in fields and (not isinstance(fields["attribution"], str) or fields["attribution"] not in FOLLOWUP_ATTRIBUTIONS):
        raise StoreError("invalid follow-up attribution")
    if not update or "evidence" in fields:
        _validate_evidence(fields.get("evidence"), strict=True, required=True)
    if update and fields.get("status") in ("resolved", "dismissed") and not fields.get("evidence"):
        raise StoreError("resolving or dismissing a follow-up requires fresh evidence")
    if "external_links" in fields:
        links = fields["external_links"]
        if not isinstance(links, list) or not links:
            raise StoreError("external_links must be a nonempty list of recorded URLs")
        for link in links:
            if not isinstance(link, dict) or set(link) - {"url", "title", "tracker"}:
                raise StoreError("external link requires url and optional title/tracker")
            if any(not _nonempty_text(value) for value in link.values()):
                raise StoreError("external link values must be nonempty text")
            parsed = urlparse(link.get("url", ""))
            if parsed.scheme not in ("https", "http") or not parsed.hostname:
                raise StoreError("external link requires an absolute HTTP(S) URL")


def _validate_followup_links(store: Store, fields: dict, card_ids) -> None:
    if not isinstance(card_ids, (list, tuple)):
        raise StoreError("follow-up card_ids must be a list")
    for card_id in card_ids:
        if not isinstance(card_id, str) or card_id not in store.cards:
            raise StoreError(f"unknown follow-up card {card_id!r}")
        if fields.get("repo_id") and store.cards[card_id].repo_id != fields["repo_id"]:
            raise StoreError(f"{card_id}: follow-up belongs to a different repository")


def _link_issue_cards(store: Store, issue: Issue, card_ids) -> None:
    for card_id in card_ids:
        card = store.cards[card_id]
        if card_id not in issue.card_ids:
            issue.card_ids.append(card_id)
        if issue.id not in card.issue_ids:
            card.issue_ids.append(issue.id)
            store.upsert_card(card)


def _issue_history(issue: Issue) -> dict:
    value = issue.to_dict()
    value.pop("history", None)
    value["recorded_at"] = utc_now()
    return value


@transactional
def record_followup(store: Store, fields: dict, card_ids=()) -> Issue:
    """Record or link a local follow-up, including after its PR has merged.

    Required fields: key, claim, action, action_owner, evidence containing
    what/establishes, and repo_id or target. Optional fields are kind, status,
    reason_code, attribution, attribution_note, and external_links. No external
    write or operational card/authority change occurs. Identity is stable per
    (repo_id, target, key); use update_incident for lifecycle changes.
    """
    _validate_followup_fields(fields)
    _validate_followup_links(store, fields, card_ids)
    target = fields.get("target", fields.get("repo_id", ""))
    repo_id = fields.get("repo_id", "")
    issue = next((i for i in store.issues.values() if i.key == fields["key"]
                  and i.repo_id == repo_id and (i.target or i.repo_id) == target), None)
    if issue is None:
        values = copy.deepcopy(fields)
        values.setdefault("kind", "followup")
        values.setdefault("reason_code", "")
        values["repo_id"] = repo_id
        values["target"] = target
        issue = Issue(id=store.ids.next("ISS"), created_at=utc_now(),
                      updated_at=utc_now(), **values)
        if issue.status in ("resolved", "dismissed"):
            issue.resolved_at = issue.updated_at
        store.record_ids()
    else:
        # Repeated discovery does not silently reopen or rewrite an existing
        # decision. New receipts/links are retained; explicit updates carry
        # lifecycle and recommendation changes.
        old = _issue_history(issue)
        issue.evidence = _merge_records(issue.evidence, fields["evidence"])
        issue.external_links = _merge_records(issue.external_links, fields.get("external_links", []))
        if old["evidence"] != issue.evidence or old["external_links"] != issue.external_links:
            issue.history.append(old)
            issue.updated_at = utc_now()
    _link_issue_cards(store, issue, card_ids)
    store.record_issue(issue)
    return issue


@transactional
def update_incident(store: Store, issue_id: str, changes: dict) -> Issue:
    """Update a durable incident/follow-up without requiring an active attempt.

    Mutable fields are claim, reason_code, action, action_owner, status,
    attribution, attribution_note, evidence, and external_links. Evidence and
    links append uniquely; resolving/dismissing needs a fresh evidence record.
    Identity, PR outcomes, approved heads, deadlines, and leases are untouched.
    """
    _validate_followup_fields(changes, update=True)
    if issue_id not in store.issues:
        raise StoreError(f"unknown incident {issue_id!r}")
    issue = store.issues[issue_id]
    before = _issue_history(issue)
    for key, value in changes.items():
        if key in ("evidence", "external_links"):
            setattr(issue, key, _merge_records(getattr(issue, key), value))
        else:
            setattr(issue, key, copy.deepcopy(value))
    if all(getattr(issue, key) == before[key] for key in FOLLOWUP_MUTABLE):
        raise StoreError("incident update makes no change")
    if changes.get("status") in ("resolved", "dismissed") \
            and issue.evidence == before["evidence"]:
        raise StoreError("resolution requires evidence not already recorded")
    issue.history.append(before)
    issue.updated_at = utc_now()
    if "status" in changes:
        issue.resolved_at = (issue.updated_at if issue.status in ("resolved", "dismissed") else "")
    store.record_issue(issue)
    return issue


@transactional
def link_incident(store: Store, card: Card, result: dict) -> Issue:
    """Backward-compatible legacy incident adapter, valid for every outcome.

    Historical incident records may lack evidence/recommendations. Keep them
    loadable and render the gaps explicitly; new callers use record_followup.
    """
    card = store.cards[card.id]
    incident = result.get("incident")
    if not isinstance(incident, dict) or not all(
            _nonempty_text(incident.get(k)) for k in ("key", "claim")):
        raise StoreError("incident requires key and claim")
    issue = next((i for i in store.issues.values()
                  if i.key == incident["key"] and i.repo_id == card.repo_id
                  and (i.target or i.repo_id) == card.repo_id), None)
    if issue is None:
        issue = Issue(id=store.ids.next("ISS"), key=incident["key"],
                      repo_id=card.repo_id, target=card.repo_id,
                      reason_code=result.get("reason_code", ""), claim=incident["claim"],
                      action=result.get("action", ""), action_owner=result.get("action_owner", ""),
                      created_at=utc_now(), updated_at=utc_now())
        store.record_ids()
    fresh = result.get("evidence", [])
    _validate_evidence(fresh)
    issue.evidence = _merge_records(issue.evidence, fresh)
    _link_issue_cards(store, issue, [card.id])
    store.record_issue(issue)
    return issue


@transactional
def start_run_clock(store: Store, run_budget_secs: float,
                    now: float | None = None) -> float:
    """Set the whole-run deadline once. A second call is refused: a
    resumed or retried run inherits the clock, it never resets it."""
    assert store.header is not None, "create_run first"
    if store.header.deadline_epoch:
        raise StoreError(f"run deadline already set to "
                         f"{store.header.deadline_epoch}; never reset")
    if isinstance(run_budget_secs, bool) or not isinstance(run_budget_secs, (int, float)) \
            or not math.isfinite(run_budget_secs) or run_budget_secs <= 0:
        raise StoreError("run_budget_secs must be finite and positive")
    moment = time.time() if now is None else now
    if not math.isfinite(moment):
        raise StoreError("now must be finite")
    store.header.deadline_epoch = moment + run_budget_secs
    store.set_header(store.header)
    return store.header.deadline_epoch


@transactional
def expire(store: Store, now: float | None = None) -> list:
    """Record K14 on idle dispatchable cards at the earlier run/PR deadline.

    Never-admitted cards stay NEW/unassessed. Previously admitted cards
    become WAITING. Held/quarantined workers and existing holds remain
    under their current ownership and cannot be reassigned by expiry.
    """
    moment = time.time() if now is None else now
    expired = []
    for card in sorted(store.cards.values(), key=lambda c: c.id):
        if card.state not in SCHEDULABLE:
            continue
        deadlines = [d for d in (card.deadline_epoch,
                                 store.header.deadline_epoch if store.header else 0) if d]
        if not deadlines or moment < min(deadlines):
            continue
        lease = store.leases.leases.get(card.repo_id)
        if lease is not None and lease.state in ("held", "quarantined"):
            continue
        unassessed = card.state == State.NEW and not card.attempts
        reason = ("run budget exhausted before first admission; remains unassessed"
                  if unassessed else "per-PR or run budget exhausted before dispatch")
        if unassessed and card.reason_code == "K14" and card.reason_line == reason:
            continue
        card.reason_code = "K14"
        card.reason_line = reason
        card.severity = "low"
        card.action = "Budget exhausted for this PR; continue in the next run."
        card.action_owner = "sweeper"
        card.resume_trigger = "next run"
        if hasattr(card, "execution_stop"):
            card.execution_stop = {
                "reason_code": "K14", "reason_line": card.reason_line,
                "action": card.action, "action_owner": card.action_owner,
                "resume_trigger": card.resume_trigger, "observed_at": utc_now()}
        if not unassessed:
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
    if discovery_complete and not store.header.discovery_complete:
        raise StoreError("incomplete discovery requires a later complete scope-proven snapshot")
    states = [store.cards[i].state for i in store.header.scope_ids]
    if not discovery_complete or State.NEW in states:
        return "incomplete"
    if all(s in TERMINAL for s in states):
        return "completed"
    return "completed_with_exceptions"


CONTINUATION_KINDS = ("watcher", "scheduled", "none")


@transactional
def finish_run(store: Store, continuation: dict,
               discovery_complete: bool | None = None) -> str:
    """Record the stop reason and the one explicit continuation state."""
    assert store.header is not None, "create_run first"
    if continuation.get("kind") not in CONTINUATION_KINDS:
        raise StoreError(f"continuation kind must be one of "
                         f"{', '.join(CONTINUATION_KINDS)}")
    if discovery_complete is None:
        discovery_complete = store.header.discovery_complete
    if discovery_complete and store.header.discovery_snapshot \
            and not store.header.discovery_snapshot.get("complete"):
        raise StoreError("an incomplete saved discovery snapshot cannot be declared complete")
    ending = run_ending(store, discovery_complete)
    store.header.discovery_complete = discovery_complete
    store.header.continuation = dict(continuation)
    store.header.stop_reason = ending
    store.set_header(store.header)
    return ending
