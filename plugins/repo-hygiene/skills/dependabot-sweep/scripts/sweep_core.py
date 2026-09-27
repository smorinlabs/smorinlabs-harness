#!/usr/bin/env python3
"""Durable spine for dependabot-sweep, Slice 1: states, cards, leases, store.

Stdlib only. This module never touches the network: it is the run's memory.
The coordinator (sweep_coordinator.py) drives it; the renderer
(sweep_report.py) reads it. Records persist as append-only JSONL so a
crashed run can rebuild exact state by replay.
"""

from __future__ import annotations

import copy
import errno
import hashlib
import json
import os
import threading
import time
import uuid
import warnings
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from enum import Enum
from functools import wraps


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
    """Exclusive repository claims, published as complete lock-file payloads.

    Store transactions serialize durable lease decisions and id allocation.
    Claims made under that protocol can be recovered only when locked replay
    proves no matching held or quarantined lease exists. Legacy claims stay
    protected, and each Store keeps its own token to identify its claims.
    """

    def __init__(self, directory: str, store=None) -> None:
        self.directory = directory
        self.token = uuid.uuid4().hex[:12]
        self.store = store

    def _path(self, repo_id: str) -> str:
        return os.path.join(self.directory,
                            repo_id.replace("/", "__") + ".lock")

    def claim(self, repo_id: str, holder: str) -> bool:
        os.makedirs(self.directory, exist_ok=True)
        text = f"{self.token} {holder}"
        if self.store is not None and self.store._owns_transaction():
            text = json.dumps({"protocol": "store-transaction-v1",
                               "store": os.path.realpath(self.store.path),
                               "repo_id": repo_id, "token": self.token,
                               "holder": holder}, sort_keys=True)
        # The exclusive hard link publishes a complete payload. A crash
        # while writing the temporary file cannot leave a half-marked claim.
        temporary = os.path.join(self.directory, f".claim-{uuid.uuid4().hex}")
        try:
            with open(temporary, "x", encoding="utf-8") as handle:
                handle.write(text)
                handle.flush()
                os.fsync(handle.fileno())
            try:
                os.link(temporary, self._path(repo_id))
            except FileExistsError:
                return self._read(repo_id) == text
        finally:
            try:
                os.unlink(temporary)
            except FileNotFoundError:
                pass
        return True

    def _read(self, repo_id: str) -> str:
        try:
            with open(self._path(repo_id), encoding="utf-8") as handle:
                return handle.read().strip()
        except FileNotFoundError:
            return ""

    def holder(self, repo_id: str) -> str:
        text = self._read(repo_id)
        if text.startswith("{"):
            try:
                return json.loads(text).get("holder", "")
            except (ValueError, AttributeError):
                return ""
        return text.partition(" ")[2]

    def recover_orphans(self) -> None:
        """Recover only claims made by the serialized journal protocol.

        The caller holds the store lock and has replayed durable leases.
        No live claim+commit critical section can coexist with that lock.
        Legacy and unrecognized files stay locked; age proves nothing.
        """
        if self.store is None or not self.store._owns_transaction():
            raise StoreError("orphan recovery requires a store transaction")
        if not os.path.isdir(self.directory):
            return
        for entry in os.scandir(self.directory):
            if not entry.name.endswith(".lock") or not entry.is_file():
                continue
            try:
                with open(entry.path, encoding="utf-8") as handle:
                    record = json.load(handle)
            except (ValueError, UnicodeError, FileNotFoundError):
                continue
            if not isinstance(record, dict) or \
                    record.get("protocol") != "store-transaction-v1" or \
                    record.get("store") != os.path.realpath(self.store.path):
                continue
            repo_id, holder = record.get("repo_id"), record.get("holder")
            if not isinstance(repo_id, str) or not isinstance(holder, str) \
                    or not holder or self._path(repo_id) != entry.path:
                continue
            lease = self.store.leases.leases.get(repo_id)
            if lease is not None and lease.holder == holder and \
                    lease.state in ("held", "quarantined"):
                continue
            os.unlink(entry.path)

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


@contextmanager
def _journal_lock(path: str, timeout: float):
    """A bounded kernel lock, released even when the owning process dies."""
    if not path:
        yield
        return
    with open(os.path.realpath(path) + ".write.lock", "a+b") as handle:
        if os.name == "nt":
            import msvcrt

            if handle.seek(0, os.SEEK_END) == 0:
                handle.write(b"\0")
                handle.flush()

            def acquire():
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)

            def release():
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            def acquire():
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)

            def release():
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        deadline = time.monotonic() + timeout
        while True:
            try:
                acquire()
                break
            except OSError as exc:
                if exc.errno not in (errno.EACCES, errno.EAGAIN, errno.EDEADLK):
                    raise
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise StoreError(f"timed out waiting for store lock: {path}") from exc
                time.sleep(min(0.05, remaining))
        try:
            yield
        finally:
            release()


def transactional(function):
    """Run a Store-first coordinator operation under one durable transaction."""
    @wraps(function)
    def wrapped(store, *args, **kwargs):
        with store.transaction():
            return function(store, *args, **kwargs)
    return wrapped


def _serialized_write(function):
    """Lock before model mutation, including standalone writes from threads."""
    @wraps(function)
    def wrapped(store, *args, **kwargs):
        if not store._mutex.acquire(timeout=5.0):
            raise StoreError(f"timed out waiting for store lock: {store.path}")
        try:
            return function(store, *args, **kwargs)
        finally:
            store._mutex.release()
    return wrapped


_ANY_REVISION = object()


class Store:
    """Append-only JSONL with serialized, atomic multi-record transactions.

    `transaction()` refreshes under a kernel lock before decisions or id
    allocation. One complete JSONL transaction publishes every buffered
    event; a torn final append publishes none. Legacy events still replay.
    Standalone writes reject stale snapshots instead of losing newer state.
    """

    def __init__(self, path: str = "", session: str = "") -> None:
        self.path = path
        self.session = session
        self.header: RunHeader | None = None
        self.cards: dict[str, Card] = {}
        self.diary: dict[str, Attempt] = {}
        self.issues: dict[str, Issue] = {}
        self.leases = LeaseTable()
        self.ids = IdAssigner()
        self.locks = RepoLocks(path + ".locks", self) if path else None
        self._mutex = threading.RLock()
        self._transaction_depth = 0
        self._transaction_owner: int | None = None
        self._transaction_failed = False
        self._records: list = []
        self._revision: str | None = None
        self._tail_offset: int | None = None
        self._tail = b""
        self._needs_newline = False
        self.recovery_warnings: list = []

    @staticmethod
    def _update_object(existing, incoming):
        if incoming is None:
            return None
        if existing is None:
            return copy.deepcopy(incoming)
        existing.__dict__.clear()
        existing.__dict__.update(copy.deepcopy(incoming.__dict__))
        return existing

    def _adopt(self, other: "Store") -> None:
        """Refresh values in place without replacing live locks or card handles."""
        self.header = self._update_object(self.header, other.header)
        for current, incoming in ((self.cards, other.cards),
                                  (self.diary, other.diary),
                                  (self.issues, other.issues),
                                  (self.leases.leases, other.leases.leases)):
            for key in set(current) - set(incoming):
                del current[key]
            for key, value in incoming.items():
                current[key] = self._update_object(current.get(key), value)
        self.ids.counters.clear()
        self.ids.counters.update(other.ids.counters)
        for name in ("_revision", "_tail_offset", "_tail", "_needs_newline",
                     "recovery_warnings"):
            setattr(self, name, copy.deepcopy(getattr(other, name)))

    def _current(self) -> "Store":
        if self.path and os.path.exists(self.path):
            return self.load(self.path, session=self.session)
        current = Store(self.path, session=self.session)
        if not self.path:
            current._adopt(self)
        return current

    def _owns_transaction(self) -> bool:
        return bool(self._transaction_depth and
                    self._transaction_owner == threading.get_ident())

    @contextmanager
    def transaction(self, timeout: float = 5.0, *, _expected_revision=_ANY_REVISION):
        """Refresh, mutate, and commit under a bounded store-wide lock.

        Nested calls share the outer batch. Any nested exception aborts that
        batch, even when caught by its caller. Exceptions restore persisted
        state in place. New journals stay absent until the first commit.
        """
        if timeout < 0:
            raise ValueError("store lock timeout must be non-negative")
        deadline = time.monotonic() + timeout
        if not self._mutex.acquire(timeout=timeout):
            raise StoreError(f"timed out waiting for store lock: {self.path}")
        try:
            if self._owns_transaction():
                self._transaction_depth += 1
                try:
                    yield self
                except BaseException:
                    self._transaction_failed = True
                    raise
                finally:
                    self._transaction_depth -= 1
                return
            with _journal_lock(self.path, max(0.0, deadline - time.monotonic())):
                baseline = self._current()
                self._adopt(baseline)
                if _expected_revision is not _ANY_REVISION and \
                        _expected_revision != self._revision:
                    raise StoreError("stale store snapshot; reload and apply the "
                                     "change inside Store.transaction()")
                self._transaction_depth = 1
                self._transaction_owner = threading.get_ident()
                self._transaction_failed = False
                self._records = []
                try:
                    if self._tail_offset is not None:
                        self._quarantine_tail()
                    if self.locks is not None:
                        self.locks.recover_orphans()
                    yield self
                    if self._transaction_failed:
                        raise StoreError("store transaction aborted by a nested failure")
                    self._commit_records()
                except BaseException:
                    self._adopt(self._current() if self.path else baseline)
                    if self.locks is not None:
                        self.locks.recover_orphans()
                    raise
                finally:
                    self._records = []
                    self._transaction_depth = 0
                    self._transaction_owner = None
                    self._transaction_failed = False
        finally:
            self._mutex.release()

    def _quarantine_tail(self) -> None:
        quarantine = f"{self.path}.torn-{uuid.uuid4().hex}.jsonl"
        with open(quarantine, "xb") as handle:
            handle.write(self._tail)
            handle.flush()
            os.fsync(handle.fileno())
        with open(self.path, "r+b") as handle:
            handle.truncate(self._tail_offset)
            handle.flush()
            os.fsync(handle.fileno())
            handle.seek(0)
            self._revision = hashlib.sha256(handle.read()).hexdigest()
        self.recovery_warnings.append(f"trailing bytes preserved in {quarantine}")
        self._tail_offset, self._tail = None, b""
        self._needs_newline = False

    def _commit_records(self) -> None:
        if not self.path or not self._records:
            return
        record = {"ts": utc_now(), "kind": "transaction", "version": 1,
                  "records": self._records}
        data = (("\n" if self._needs_newline else "") +
                json.dumps(record) + "\n").encode("utf-8")
        descriptor = os.open(self.path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
        try:
            remaining = memoryview(data)
            while remaining:
                written = os.write(descriptor, remaining)
                if written <= 0:
                    raise OSError("store append made no progress")
                remaining = remaining[written:]
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        with open(self.path, "rb") as handle:
            self._revision = hashlib.sha256(handle.read()).hexdigest()
        self._needs_newline = False

    @_serialized_write
    def _append(self, kind: str, payload: dict) -> None:
        record = {"ts": utc_now(), "kind": kind, **payload}
        if self._owns_transaction():
            self._records.append(copy.deepcopy(record))
            return
        if self.path:
            # Callers may already have changed a model object. Preserve that
            # intent as an event, but refuse it if another snapshot committed.
            with self.transaction(_expected_revision=self._revision):
                self._replay_record(record)
                self._records.append(copy.deepcopy(record))

    @_serialized_write
    def set_header(self, header: RunHeader) -> None:
        self.header = header
        self._append("run_header", header.to_dict())

    @_serialized_write
    def upsert_card(self, card: Card) -> None:
        self.cards[card.id] = card
        self._append("card", card.to_dict())

    @_serialized_write
    def record_attempt(self, attempt: Attempt) -> None:
        self.diary[attempt.id] = attempt
        self._append("attempt", attempt.to_dict())

    @_serialized_write
    def record_lease(self, lease: Lease) -> None:
        self.leases.leases[lease.repo_id] = lease
        self._append("lease", lease.to_dict())

    @_serialized_write
    def record_issue(self, issue: Issue) -> None:
        self.issues[issue.id] = issue
        self._append("issue", issue.to_dict())

    @_serialized_write
    def record_ids(self) -> None:
        self._append("ids", {"counters": dict(self.ids.counters)})

    @classmethod
    def load(cls, path: str, session: str = "") -> "Store":
        store = cls(path, session=session)
        with open(path, "rb") as handle:
            raw = handle.read()
        store._revision = hashlib.sha256(raw).hexdigest()
        store._needs_newline = bool(raw and not raw.endswith(b"\n"))
        offset = 0
        for number, line in enumerate(raw.splitlines(keepends=True), 1):
            if not line.strip():
                offset += len(line)
                continue
            try:
                record = json.loads(line)
            except (ValueError, UnicodeError) as exc:
                if not line.endswith(b"\n") and offset + len(line) == len(raw):
                    store._tail_offset, store._tail = offset, line
                    message = (f"incomplete trailing record in {path} at byte {offset}; "
                               "preceding records recovered; next write quarantines the tail")
                    store.recovery_warnings.append(message)
                    warnings.warn(message, RuntimeWarning, stacklevel=2)
                    break
                raise StoreError(f"invalid store record {number} in {path}: {exc}") from exc
            try:
                if isinstance(record, dict) and record.get("kind") == "transaction":
                    if record.get("version") != 1 or not isinstance(record.get("records"), list):
                        raise ValueError("invalid transaction envelope")
                    for event in record["records"]:
                        store._replay_record(event)
                else:
                    store._replay_record(record)
            except (KeyError, TypeError, ValueError) as exc:
                raise StoreError(f"invalid store record {number} in {path}: {exc}") from exc
            offset += len(line)
        for identifier in (*store.cards, *store.diary, *store.issues):
            store.ids.observe(identifier)
        return store

    def _replay_record(self, record: dict) -> None:
        if not isinstance(record, dict):
            raise ValueError("event must be an object")
        kind = record.get("kind")
        if kind == "run_header":
            self.header = self._update_object(self.header, RunHeader.from_dict(record))
        elif kind in ("card", "attempt", "issue", "lease"):
            model, mapping, identifier = {
                "card": (Card, self.cards, "id"),
                "attempt": (Attempt, self.diary, "id"),
                "issue": (Issue, self.issues, "id"),
                "lease": (Lease, self.leases.leases, "repo_id"),
            }[kind]
            value = model.from_dict(record)
            key = getattr(value, identifier)
            mapping[key] = self._update_object(mapping.get(key), value)
            if kind != "lease":
                self.ids.observe(key)
        elif kind == "ids":
            for prefix, value in record.get("counters", {}).items():
                self.ids.counters[prefix] = max(self.ids.counters.get(prefix, 0), value)
        else:
            raise ValueError(f"unknown event kind {kind!r}")
