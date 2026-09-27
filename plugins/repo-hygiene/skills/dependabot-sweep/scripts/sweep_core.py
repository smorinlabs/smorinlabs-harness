#!/usr/bin/env python3
"""Durable spine for dependabot-sweep, Slice 1: states, cards, leases, store.

Stdlib only. This module never touches the network: it is the run's memory.
The coordinator (sweep_coordinator.py) drives it; the renderer
(sweep_report.py) reads it. Records persist as append-only JSONL so a
crashed run can rebuild exact state by replay.
"""

from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import asdict, dataclass, field
from enum import Enum


class State(str, Enum):
    NEW = "NEW"
    READY = "READY"
    WAITING = "WAITING"
    BLOCKED = "BLOCKED"
    NEEDS_OWNER = "NEEDS_OWNER"
    MERGED = "MERGED"
    UNKNOWN = "UNKNOWN"
    CLOSED = "CLOSED"


TERMINAL = frozenset({State.MERGED, State.CLOSED})

TRANSITIONS: dict[State, frozenset] = {
    State.NEW: frozenset(
        {State.READY, State.WAITING, State.BLOCKED, State.NEEDS_OWNER,
         State.MERGED, State.CLOSED, State.UNKNOWN}
    ),
    State.READY: frozenset(
        {State.MERGED, State.WAITING, State.BLOCKED, State.NEEDS_OWNER,
         State.CLOSED, State.UNKNOWN}
    ),
    State.WAITING: frozenset(
        {State.READY, State.BLOCKED, State.NEEDS_OWNER, State.CLOSED,
         State.UNKNOWN}
    ),
    State.BLOCKED: frozenset(
        {State.READY, State.NEEDS_OWNER, State.WAITING, State.CLOSED,
         State.UNKNOWN}
    ),
    # A fresh evaluation after an owner decision can find a technical hold;
    # approval alone never permits a worker to skip READY and claim MERGED.
    State.NEEDS_OWNER: frozenset(
        {State.READY, State.WAITING, State.BLOCKED, State.CLOSED, State.UNKNOWN}),
    # UNKNOWN exits only through observed reality: Card.restore_prior()
    # returns a proved-unmerged card to its recorded prior_state (NEW when
    # it was never evaluated) and Card.observe_merged() confirms a merge.
    # Workers never target these edges. Resolving a quarantined repository
    # so reconcile can reach its UNKNOWN cards (LeaseTable.resolve_quarantine)
    # is Slice 2 work (acceptance test T06).
    State.UNKNOWN: frozenset(
        {State.MERGED, State.NEW, State.READY, State.WAITING, State.BLOCKED,
         State.NEEDS_OWNER}
    ),
    State.MERGED: frozenset(),
    State.CLOSED: frozenset(),
}

# Diagnostic reason codes. One per card; the human line lives on the card.
K_REASONS = {
    "K01": "CI_PENDING", "K02": "CONFLICT_MECHANICAL",
    "K03": "CONFLICT_SEMANTIC", "K04": "PR_REGRESSION",
    "K05": "BASELINE_FAILURE", "K06": "ENVIRONMENT_FAILURE",
    "K07": "REVIEW_REQUIRED", "K08": "REVIEWER_UNAVAILABLE",
    "K09": "POLICY_OR_PERMISSION", "K10": "QUEUE_PENDING",
    "K11": "MUTATION_UNKNOWN", "K12": "WORKER_FAILURE",
    "K13": "EVIDENCE_INCOMPLETE", "K14": "BUDGET_EXHAUSTED",
    "K15": "REVIEW_NOT_CONVERGING", "K16": "APPROVAL_OR_HOLD",
    "K17": "TRANSIENT_FAILURE",
}

SEVERITIES = ("critical", "high", "medium", "low", "advisory", "unknown")
SEVERITY_RANK = {name: rank for rank, name in enumerate(SEVERITIES)}

# Report order for unresolved cards: reconcile-first, then owner, then
# automation, then waiting. Severity breaks ties within a state.
STATE_REPORT_RANK = {
    State.UNKNOWN: 0, State.NEEDS_OWNER: 1, State.BLOCKED: 2,
    State.WAITING: 3, State.NEW: 4,
}


class TransitionError(ValueError):
    """An illegal PR state transition was attempted."""


class LeaseError(ValueError):
    """A repository-lease rule was violated."""


class StoreError(ValueError):
    """The record store refused an inconsistent write."""


def utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


@dataclass
class Card:
    """One PR's card: identity, state, reason, evidence, next action."""

    id: str
    org: str
    repo: str
    number: int
    url: str
    title: str
    owner: str
    head_sha: str = ""
    base_ref: str = ""
    state: State = State.NEW
    prior_state: str = ""
    reason_code: str = ""
    reason_line: str = ""
    severity: str = "unknown"
    confidence: str = "unknown"
    evidence: list = field(default_factory=list)
    action: str = ""
    action_owner: str = ""
    resume_trigger: str = ""
    decision: dict = field(default_factory=dict)
    replaces: str = ""
    replaced_by: str = ""
    issue_ids: list = field(default_factory=list)
    merge_commit: str = ""
    merged_at: str = ""
    attempts: list = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""
    last_observation: str = ""
    # Absolute per-PR deadline, set when first scheduled. Successor
    # attempts inherit it: handoffs and retries never reset the clock.
    deadline_epoch: float = 0.0

    @property
    def repo_id(self) -> str:
        return f"{self.org}/{self.repo}"

    @property
    def human_id(self) -> str:
        return f'{self.repo_id}#{self.number} "{self.title}"'

    def transition_to(self, target: State | str) -> None:
        target = State(target)
        if target not in TRANSITIONS[self.state]:
            raise TransitionError(f"{self.id}: {self.state.value} -> "
                                  f"{target.value} is not allowed")
        if target == State.UNKNOWN:
            self.prior_state = self.state.value
        self.state = target
        self.updated_at = utc_now()

    def observe_merged(self, commit: str, merged_at: str) -> None:
        """Fresh GitHub observation proved this PR merged.

        Observed reality may close out any non-terminal card, including
        ones a worker holds as WAITING, BLOCKED, or NEEDS_OWNER; workers
        themselves stay bound to TRANSITIONS. Evidence is mandatory.
        """
        if self.state in TERMINAL:
            raise TransitionError(f"{self.id}: {self.state.value} is "
                                  f"terminal; cannot observe a merge")
        if not commit or not merged_at:
            raise StoreError(f"{self.id}: observed merge requires commit "
                             f"and merged_at evidence")
        self.merge_commit = commit
        self.merged_at = merged_at
        self.severity = "none"
        self.prior_state = ""
        self.state = State.MERGED
        self.updated_at = utc_now()

    def restore_prior(self) -> None:
        """Observation proved an UNKNOWN card unmerged: return it to the
        recorded prior_state (NEW when it was never evaluated)."""
        if self.state != State.UNKNOWN:
            raise TransitionError(f"{self.id}: restore_prior applies to "
                                  f"UNKNOWN cards, not {self.state.value}")
        prior = self.prior_state or State.NEW.value
        self.prior_state = ""
        self.transition_to(prior)

    def observe_merge_retracted(self, reason_line: str) -> None:
        """Fresh observation shows a recorded MERGED card unmerged. The
        claim is withdrawn to UNKNOWN (prior READY) for reconciliation;
        a post-merge surprise never stands as a success."""
        if self.state != State.MERGED:
            raise TransitionError(f"{self.id}: only a MERGED card can have "
                                  f"its merge retracted, not "
                                  f"{self.state.value}")
        self.prior_state = State.READY.value
        self.state = State.UNKNOWN
        self.reason_code = "K11"
        self.reason_line = reason_line
        self.updated_at = utc_now()

    def to_dict(self) -> dict:
        data = asdict(self)
        data["state"] = self.state.value
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "Card":
        data = dict(data)
        data["state"] = State(data.get("state", "NEW"))
        known = {f.name for f in cls.__dataclass_fields__.values()}
        return cls(**{k: v for k, v in data.items() if k in known})


@dataclass
class Attempt:
    """One worker attempt from the diary. A replacement worker is a new
    attempt id on the same card ids, never new card ids."""

    id: str
    assigned: list = field(default_factory=list)
    model: str = ""
    started_at: str = ""
    last_progress_at: str = ""
    phase: str = ""
    result: str = ""
    successor: str = ""
    outstanding: list = field(default_factory=list)
    # The coordinator session that issued this attempt. Another session
    # never marks it crashed while its heartbeat is fresh.
    session: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Attempt":
        known = {f.name for f in cls.__dataclass_fields__.values()}
        return cls(**{k: v for k, v in data.items() if k in known})


@dataclass
class RunHeader:
    """The run's header: scope, authority, and stop reason."""

    run_id: str
    mode: str
    scope_ids: list = field(default_factory=list)
    scope_fixed: bool = True
    cutoff: str = ""
    authorization: str = ""
    exclusions: list = field(default_factory=list)
    started_at: str = ""
    stop_reason: str = ""
    # Absolute whole-run deadline, set once; every card deadline is capped
    # by it and no handoff or retry resets it.
    deadline_epoch: float = 0.0
    discovery_complete: bool = True
    # Who continues after this pass: {"kind": watcher|scheduled|none,
    # "ref": ..., "verified_at": ...}. Empty means none.
    continuation: dict = field(default_factory=dict)
    # The run's resolved authority (mode, repairs, approvals, holds,
    # budgets, reviewer contexts, helper path), written once by `run
    # create` so every later command reads the same values instead of
    # re-deriving them from flags.
    authority: dict = field(default_factory=dict)

    def query_subset(self, ids: list) -> tuple:
        """Resolve a follow-up question about a subset of cards.

        Read-only by construction: it returns the requested ids and can
        never narrow the run's objective. Unknown ids raise.
        """
        unknown = [i for i in ids if i not in self.scope_ids]
        if unknown:
            raise StoreError(f"query references cards outside scope: {unknown}")
        return tuple(ids)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "RunHeader":
        known = {f.name for f in cls.__dataclass_fields__.values()}
        return cls(**{k: v for k, v in data.items() if k in known})


@dataclass
class Lease:
    repo_id: str
    state: str = "free"  # free | held | quarantined | released
    holder: str = ""
    pr_ids: list = field(default_factory=list)
    since: str = ""
    reason: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Lease":
        known = {f.name for f in cls.__dataclass_fields__.values()}
        return cls(**{k: v for k, v in data.items() if k in known})


@dataclass
class Issue:
    """One shared incident, such as a baseline failure on a base revision.
    Every PR it blocks links the same issue id instead of repeating it."""

    id: str
    key: str
    repo_id: str
    reason_code: str
    claim: str
    card_ids: list = field(default_factory=list)
    action: str = ""
    action_owner: str = ""
    created_at: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Issue":
        known = {f.name for f in cls.__dataclass_fields__.values()}
        return cls(**{k: v for k, v in data.items() if k in known})


class RepoLocks:
    """Cross-session repository locks: one file per repository, created
    with O_EXCL so two coordinator sessions over one store can never both
    issue a writer. The in-memory LeaseTable records what this session
    believes; the lock file decides who actually holds the repository.
    Each Store instance writes its own token beside the holder, so two
    sessions that compute the same attempt id from stale counters still
    cannot both claim."""

    def __init__(self, directory: str) -> None:
        self.directory = directory
        self.token = uuid.uuid4().hex[:12]

    def _path(self, repo_id: str) -> str:
        return os.path.join(self.directory,
                            repo_id.replace("/", "__") + ".lock")

    def claim(self, repo_id: str, holder: str) -> bool:
        os.makedirs(self.directory, exist_ok=True)
        try:
            fd = os.open(self._path(repo_id),
                         os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            return self._read(repo_id) == f"{self.token} {holder}"
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(f"{self.token} {holder}")
        return True

    def _read(self, repo_id: str) -> str:
        try:
            with open(self._path(repo_id), encoding="utf-8") as handle:
                return handle.read().strip()
        except FileNotFoundError:
            return ""

    def holder(self, repo_id: str) -> str:
        return self._read(repo_id).partition(" ")[2]

    def release(self, repo_id: str, holder: str) -> None:
        """Remove the lock only when `holder` owns it; tolerant of a
        lock that is already gone."""
        if self.holder(repo_id) == holder:
            try:
                os.remove(self._path(repo_id))
            except FileNotFoundError:
                pass


class LeaseTable:
    """One-writer-per-repository leases. Repair pushes need the lease
    exactly like merges; read-only diagnosis never does."""

    def __init__(self) -> None:
        self.leases: dict[str, Lease] = {}

    def get(self, repo_id: str) -> Lease:
        return self.leases.setdefault(repo_id, Lease(repo_id=repo_id))

    def acquire(self, repo_id: str, holder: str, pr_ids: list) -> Lease:
        lease = self.get(repo_id)
        if lease.state == "held":
            raise LeaseError(f"{repo_id}: already held by {lease.holder}")
        if lease.state == "quarantined":
            raise LeaseError(f"{repo_id}: quarantined ({lease.reason}); "
                             f"reconcile before any new mutation")
        lease.state = "held"
        lease.holder = holder
        lease.pr_ids = list(pr_ids)
        lease.since = utc_now()
        lease.reason = ""
        return lease

    def release(self, repo_id: str, holder: str) -> Lease:
        lease = self.get(repo_id)
        if lease.state != "held" or lease.holder != holder:
            raise LeaseError(f"{repo_id}: cannot release lease held by "
                             f"{lease.holder!r} as {holder!r}")
        lease.state = "released"
        return lease

    def quarantine(self, repo_id: str, reason: str) -> Lease:
        lease = self.get(repo_id)
        lease.state = "quarantined"
        lease.reason = reason
        return lease

    def resolve_quarantine(self, repo_id: str, proved_merged: bool) -> Lease:
        """Read-only reconciliation proved the uncertain mutation's outcome."""
        lease = self.get(repo_id)
        if lease.state != "quarantined":
            raise LeaseError(f"{repo_id}: not quarantined, cannot resolve")
        lease.state = "released" if proved_merged else "free"
        lease.holder = ""
        lease.reason = ""
        return lease

    def to_dict(self) -> dict:
        return {rid: lease.to_dict() for rid, lease in self.leases.items()}

    def load_dict(self, data: dict) -> None:
        self.leases = {rid: Lease.from_dict(raw)
                       for rid, raw in data.items()}


class IdAssigner:
    """Monotonic id counters. Ids are never reused or renumbered."""

    def __init__(self, counters: dict | None = None) -> None:
        self.counters = dict(counters or {})

    def next(self, prefix: str) -> str:
        self.counters[prefix] = self.counters.get(prefix, 0) + 1
        return f"{prefix}-{self.counters[prefix]:03d}"

    def attempt_id(self) -> str:
        self.counters["AGT"] = self.counters.get("AGT", 0) + 1
        return f"AGT-{self.counters['AGT']:03d}.1"

    def successor_id(self, attempt_id: str) -> str:
        base, _, minor = attempt_id.partition(".")
        return f"{base}.{int(minor or 0) + 1}"

    def observe(self, identifier: str) -> None:
        """Raise a counter to cover an id seen in the log, so replay never
        reissues it even when the trailing ids record was lost."""
        prefix, _, rest = identifier.partition("-")
        number = rest.partition(".")[0]
        if not prefix or not number.isdigit():
            return
        self.counters[prefix] = max(self.counters.get(prefix, 0),
                                    int(number))


class Store:
    """Append-only JSONL record store. Every mutation appends one line;
    load() replays the file to rebuild exact state."""

    def __init__(self, path: str = "", session: str = "") -> None:
        self.path = path
        self.session = session
        self.header: RunHeader | None = None
        self.cards: dict[str, Card] = {}
        self.diary: dict[str, Attempt] = {}
        self.issues: dict[str, Issue] = {}
        self.leases = LeaseTable()
        self.ids = IdAssigner()
        self.locks = RepoLocks(path + ".locks") if path else None

    def _append(self, kind: str, payload: dict) -> None:
        if not self.path:
            return
        line = json.dumps({"ts": utc_now(), "kind": kind, **payload})
        with open(self.path, "a", encoding="utf-8") as handle:
            handle.write(line + "\n")

    def set_header(self, header: RunHeader) -> None:
        self.header = header
        self._append("run_header", header.to_dict())

    def upsert_card(self, card: Card) -> None:
        self.cards[card.id] = card
        self._append("card", card.to_dict())

    def record_attempt(self, attempt: Attempt) -> None:
        self.diary[attempt.id] = attempt
        self._append("attempt", attempt.to_dict())

    def record_lease(self, lease: Lease) -> None:
        self.leases.leases[lease.repo_id] = lease
        self._append("lease", lease.to_dict())

    def record_issue(self, issue: Issue) -> None:
        self.issues[issue.id] = issue
        self._append("issue", issue.to_dict())

    def record_ids(self) -> None:
        self._append("ids", {"counters": dict(self.ids.counters)})

    @classmethod
    def load(cls, path: str, session: str = "") -> "Store":
        store = cls(path, session=session)
        with open(path, encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                record = json.loads(line)
                kind = record.pop("kind", "")
                record.pop("ts", None)
                if kind == "run_header":
                    store.header = RunHeader.from_dict(record)
                elif kind == "card":
                    card = Card.from_dict(record)
                    store.cards[card.id] = card
                elif kind == "attempt":
                    attempt = Attempt.from_dict(record)
                    store.diary[attempt.id] = attempt
                elif kind == "lease":
                    lease = Lease.from_dict(record)
                    store.leases.leases[lease.repo_id] = lease
                elif kind == "issue":
                    issue = Issue.from_dict(record)
                    store.issues[issue.id] = issue
                elif kind == "ids":
                    store.ids = IdAssigner(record.get("counters", {}))
        for identifier in (*store.cards, *store.diary, *store.issues):
            store.ids.observe(identifier)
        return store
