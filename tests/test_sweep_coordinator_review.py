"""Coordinator regressions from PR 87: atomicity, ownership, and head binding."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "plugins/repo-hygiene/skills/dependabot-sweep/scripts"
sys.path.insert(0, str(SCRIPTS))

import sweep_coordinator as coord
from sweep_core import State, Store, StoreError

HEAD = "a" * 40
NEW_HEAD = "b" * 40


def discovery(number=1, repo="one", head=HEAD):
    return {"org": "acme", "repo": repo, "number": number,
            "url": f"https://example.test/acme/{repo}/pull/{number}",
            "title": "bump dependency", "head_sha": head}


def make_store(tmp_path, discoveries=None, session="owner"):
    store = Store(str(tmp_path / "run.jsonl"), session=session)
    coord.create_run(store, "RUN-REVIEW", "gated", "approved preparation",
                     discoveries if discoveries is not None else [discovery()])
    return store


def ready(card_id="PR-001", head=HEAD):
    return {"card_id": card_id, "outcome": "ready", "head_sha": head,
            "reason_line": "complete fresh evaluation",
            "evidence": [{"id": "EV-head", "head": head}]}


def owner_hold(head=None):
    result = {"card_id": "PR-001", "outcome": "hold",
              "state": "NEEDS_OWNER", "reason_code": "K16",
              "reason_line": "fresh approval needed", "severity": "low",
              "action": "approve the evaluated head", "action_owner": "owner",
              "decision": {"why": "gated", "approve_effect": "merge",
                           "decline_effect": "hold", "recommendation": "APPROVE"}}
    if head is not None:
        result["head_sha"] = head
    return result


def replay(store, session=None):
    return Store.load(store.path, session=store.session if session is None else session)


def approve(store, record_head=None):
    store.header.authority = {"mode": "gated", "approved": ["PR-001"]}
    if record_head is not None:
        store.header.authority["approval_records"] = {
            "PR-001": {"head_sha": record_head, "user_words": "approve"}}
    store.set_header(store.header)


def test_creation_failure_never_publishes_partial_scope(tmp_path, monkeypatch):
    store = Store(str(tmp_path / "run.jsonl"), session="owner")
    original = store.upsert_card

    def fail_after_first_card(card):
        original(card)
        raise RuntimeError("interrupted initialization")

    monkeypatch.setattr(store, "upsert_card", fail_after_first_card)
    with pytest.raises(RuntimeError, match="interrupted initialization"):
        coord.create_run(store, "RUN-X", "gated", "auth",
                         [discovery(1), discovery(2)])
    restored = replay(store) if Path(store.path).exists() else Store()
    assert restored.header is None
    assert restored.cards == {}


def test_every_committed_creation_prefix_has_complete_scope(tmp_path):
    store = make_store(tmp_path, [discovery(1), discovery(2)])
    lines = Path(store.path).read_text().splitlines(keepends=True)
    for length in range(1, len(lines) + 1):
        prefix = tmp_path / f"prefix-{length}.jsonl"
        prefix.write_text("".join(lines[:length]))
        restored = Store.load(str(prefix))
        if restored.header is not None:
            assert restored.header.scope_ids == ["PR-001", "PR-002"]
            assert set(restored.cards) == set(restored.header.scope_ids)


def test_stale_creator_cannot_replace_an_existing_run(tmp_path):
    path = str(tmp_path / "run.jsonl")
    first, stale = Store(path, session="first"), Store(path, session="second")
    coord.create_run(first, "RUN-FIRST", "gated", "auth", [discovery()])
    before = Path(path).read_bytes()
    with pytest.raises(StoreError):
        coord.create_run(stale, "RUN-SECOND", "gated", "auth", [discovery(2)])
    assert Path(path).read_bytes() == before
    assert Store.load(path).header.run_id == "RUN-FIRST"


def test_crash_after_repository_claim_is_recoverable(tmp_path):
    store = make_store(tmp_path)
    code = """
import os, sys
sys.path.insert(0, sys.argv[1])
import sweep_coordinator as coord
from sweep_core import Store
store = Store.load(sys.argv[2], session='crashing')
def stop_after_claim(attempt):
    os._exit(73)
store.record_attempt = stop_after_claim
coord.schedule(store)
"""
    result = subprocess.run([sys.executable, "-c", code, str(SCRIPTS), store.path],
                            env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"),
                            capture_output=True, timeout=10)
    assert result.returncode == 73, result.stderr.decode()
    resumed = replay(store, "successor")
    taskings = coord.schedule(resumed)
    assert len(taskings) == 1
    assert taskings[0]["card_ids"] == ["PR-001"]
    assert resumed.leases.get("acme/one").holder == taskings[0]["attempt_id"]


def test_unmarked_orphan_lock_is_never_stolen(tmp_path):
    store = make_store(tmp_path)
    lock_dir = Path(store.path + ".locks")
    lock_dir.mkdir(exist_ok=True)
    lock = lock_dir / "acme__one.lock"
    lock.write_text("legacy-token AGT-777.1")
    assert coord.schedule(store) == []
    assert lock.read_text() == "legacy-token AGT-777.1"


def test_stale_collector_cannot_overwrite_active_successor(tmp_path):
    store = make_store(tmp_path)
    first = coord.schedule(store)[0]["attempt_id"]
    stale = replay(store)
    current = replay(store)
    coord.reconcile(current, {"PR-001": {"merged": False}}, set())
    successor = coord.schedule(current)[0]["attempt_id"]
    before = Path(store.path).read_bytes()
    with pytest.raises(StoreError):
        coord.apply_outcome(stale, first, [ready()])
    assert Path(store.path).read_bytes() == before
    assert replay(store).leases.get("acme/one").holder == successor


def test_collection_rejects_another_sessions_attempt(tmp_path):
    store = make_store(tmp_path)
    attempt = coord.schedule(store)[0]["attempt_id"]
    stranger = replay(store, "stranger")
    before = Path(store.path).read_bytes()
    with pytest.raises(StoreError, match="session"):
        coord.apply_outcome(stranger, attempt, [ready()])
    assert Path(store.path).read_bytes() == before


@pytest.mark.parametrize("changed", ["lease", "generation"])
@pytest.mark.parametrize("results", [[], [ready()]])
def test_collection_requires_current_lease_and_generation(tmp_path, changed, results):
    store = make_store(tmp_path)
    attempt = coord.schedule(store)[0]["attempt_id"]
    if changed == "lease":
        lease = store.leases.get("acme/one")
        lease.holder = "AGT-001.2"
        store.record_lease(lease)
    else:
        card = store.cards["PR-001"]
        card.attempts.append("AGT-001.2")
        store.upsert_card(card)
    before = Path(store.path).read_bytes()
    with pytest.raises(StoreError):
        coord.apply_outcome(store, attempt, results)
    assert Path(store.path).read_bytes() == before


def test_stale_sessions_allocate_distinct_attempts_across_repos(tmp_path, monkeypatch):
    store = make_store(tmp_path, [discovery(1, "one"), discovery(2, "two")])
    first, second = replay(store, "first"), replay(store, "second")
    original = first.locks.claim
    monkeypatch.setattr(first.locks, "claim", lambda repo, holder:
                        False if repo == "acme/two" else original(repo, holder))
    a = coord.schedule(first)
    b = coord.schedule(second)
    assert [t["repo_id"] for t in a] == ["acme/one"]
    assert [t["repo_id"] for t in b] == ["acme/two"]
    assert a[0]["attempt_id"] != b[0]["attempt_id"]
    assert len(replay(store).diary) == 2


@pytest.mark.parametrize("second_kind", ["arrival", "replacement"])
def test_stale_sessions_allocate_distinct_card_ids(tmp_path, second_kind):
    store = make_store(tmp_path)
    first, second = replay(store, "first"), replay(store, "second")
    arrival = coord.register_arrival(first, discovery(2))
    if second_kind == "arrival":
        other = coord.register_arrival(second, discovery(3))
    else:
        other = coord.register_replacement(second, "PR-001", discovery(3))
    assert arrival.id != other.id
    assert len(replay(store).cards) == 3
    assert replay(store).cards[arrival.id].number == 2


def test_old_foreign_heartbeat_never_proves_the_worker_stopped(tmp_path):
    store = make_store(tmp_path)
    attempt_id = coord.schedule(store)[0]["attempt_id"]
    attempt = store.diary[attempt_id]
    attempt.last_progress_at = "2000-01-01T00:00:00Z"
    store.record_attempt(attempt)
    foreign = replay(store, "foreign")
    summary = coord.reconcile(foreign, {"PR-001": {"merged": False}}, set(),
                              now=2_000_000_000, stale_after_secs=1)
    assert summary["crashed"] == []
    assert foreign.leases.get("acme/one").state == "held"
    assert foreign.locks.holder("acme/one") == attempt_id
    assert coord.schedule(foreign) == []


def test_explicit_stopped_attempt_allows_foreign_recovery(tmp_path):
    store = make_store(tmp_path)
    attempt_id = coord.schedule(store)[0]["attempt_id"]
    foreign = replay(store, "foreign")
    summary = coord.reconcile(foreign, {"PR-001": {"merged": False}}, set(),
                              confirmed_stopped={attempt_id})
    assert summary["crashed"] == [attempt_id]
    assert foreign.leases.get("acme/one").state == "released"
    assert coord.schedule(foreign)[0]["attempt_id"] == "AGT-001.2"


def test_foreign_quarantine_also_needs_confirmed_stop(tmp_path):
    store = make_store(tmp_path)
    attempt_id = coord.schedule(store)[0]["attempt_id"]
    coord.apply_outcome(store, attempt_id, [{"card_id": "PR-001",
                        "outcome": "unknown", "op_note": "response lost"}])
    foreign = replay(store, "foreign")
    coord.reconcile(foreign, {"PR-001": {"merged": False}}, set(),
                     now=2_000_000_000, stale_after_secs=1)
    assert foreign.leases.get("acme/one").state == "quarantined"
    assert foreign.cards["PR-001"].state == State.UNKNOWN
    coord.reconcile(foreign, {"PR-001": {"merged": False}}, set(),
                     confirmed_stopped={attempt_id})
    assert foreign.leases.get("acme/one").state == "free"


def test_live_and_confirmed_stopped_conflict_is_refused(tmp_path):
    store = make_store(tmp_path)
    attempt_id = coord.schedule(store)[0]["attempt_id"]
    before = Path(store.path).read_bytes()
    with pytest.raises(StoreError, match="live"):
        coord.reconcile(store, {}, {attempt_id}, confirmed_stopped={attempt_id})
    assert Path(store.path).read_bytes() == before


@pytest.mark.parametrize("old_head", ["", HEAD])
@pytest.mark.parametrize("outcome", ["ready", "hold"])
def test_evaluated_head_is_saved_and_old_approval_removed(tmp_path, old_head, outcome):
    store = make_store(tmp_path, [discovery(head=old_head)])
    approve(store, record_head=HEAD)
    attempt = coord.schedule(store)[0]["attempt_id"]
    result = ready(head=NEW_HEAD) if outcome == "ready" else owner_hold(NEW_HEAD)
    coord.apply_outcome(store, attempt, [result])
    restored = replay(store)
    assert restored.cards["PR-001"].head_sha == NEW_HEAD
    assert "PR-001" not in restored.header.authority["approved"]
    assert "PR-001" not in restored.header.authority.get("approval_records", {})


def test_changed_head_removes_legacy_id_only_approval(tmp_path):
    store = make_store(tmp_path)
    approve(store)
    attempt = coord.schedule(store)[0]["attempt_id"]
    coord.apply_outcome(store, attempt, [ready(head=NEW_HEAD)])
    assert replay(store).header.authority["approved"] == []


def test_ready_card_can_record_a_new_head_on_fresh_evaluation(tmp_path):
    store = make_store(tmp_path)
    first = coord.schedule(store)[0]["attempt_id"]
    coord.apply_outcome(store, first, [ready()])
    approve(store)
    second = coord.schedule(store)[0]["attempt_id"]
    coord.apply_outcome(store, second, [ready(head=NEW_HEAD)])
    assert replay(store).cards["PR-001"].head_sha == NEW_HEAD
    assert replay(store).header.authority["approved"] == []


@pytest.mark.parametrize("discovery_head", ["", HEAD, NEW_HEAD])
def test_exact_matching_approval_is_preserved(tmp_path, discovery_head):
    store = make_store(tmp_path, [discovery(head=discovery_head)])
    approve(store, record_head=NEW_HEAD)
    before = json.loads(json.dumps(store.header.authority))
    attempt = coord.schedule(store)[0]["attempt_id"]
    coord.apply_outcome(store, attempt, [ready(head=NEW_HEAD)])
    assert replay(store).cards["PR-001"].head_sha == NEW_HEAD
    assert replay(store).header.authority == before


@pytest.mark.parametrize("head", [None, "", "short", "g" * 40])
def test_ready_requires_a_full_valid_evaluated_head(tmp_path, head):
    store = make_store(tmp_path)
    attempt = coord.schedule(store)[0]["attempt_id"]
    result = ready(head=head)
    if head is None:
        result.pop("head_sha")
    before = Path(store.path).read_bytes()
    with pytest.raises(StoreError, match="head_sha"):
        coord.apply_outcome(store, attempt, [result])
    assert Path(store.path).read_bytes() == before


def test_hold_without_valid_identity_head_preserves_saved_head_and_approval(tmp_path):
    store = make_store(tmp_path)
    approve(store)
    attempt = coord.schedule(store)[0]["attempt_id"]
    coord.apply_outcome(store, attempt, [owner_hold()])
    assert replay(store).cards["PR-001"].head_sha == HEAD
    assert replay(store).header.authority["approved"] == ["PR-001"]


@pytest.mark.parametrize("origin_session,recovery_session", [
    ("", ""), ("", "recovery"), ("owner", ""),
])
@pytest.mark.parametrize("quarantined", [False, True])
def test_missing_session_identity_never_proves_recovery_ownership(
        tmp_path, origin_session, recovery_session, quarantined):
    store = make_store(tmp_path, session=origin_session)
    attempt_id = coord.schedule(store)[0]["attempt_id"]
    if quarantined:
        coord.apply_outcome(store, attempt_id, [{
            "card_id": "PR-001", "outcome": "unknown", "op_note": "response lost"}])
    recovering = replay(store, recovery_session)
    before = Path(store.path).read_bytes()
    summary = coord.reconcile(recovering, {"PR-001": {"merged": False}}, set(),
                              now=2_000_000_000, stale_after_secs=1)
    assert summary["crashed"] == []
    assert summary["resolved"] == []
    assert Path(store.path).read_bytes() == before
    assert recovering.leases.get("acme/one").state == (
        "quarantined" if quarantined else "held")
    assert recovering.locks.holder("acme/one") == attempt_id
    assert coord.schedule(recovering) == []


@pytest.mark.parametrize("quarantined", [False, True])
def test_confirmed_stop_allows_anonymous_attempt_recovery(tmp_path, quarantined):
    store = make_store(tmp_path, session="")
    attempt_id = coord.schedule(store)[0]["attempt_id"]
    if quarantined:
        coord.apply_outcome(store, attempt_id, [{
            "card_id": "PR-001", "outcome": "unknown", "op_note": "response lost"}])
    recovering = replay(store, "")
    coord.reconcile(recovering, {"PR-001": {"merged": False}}, set(),
                     confirmed_stopped={attempt_id})
    assert recovering.leases.get("acme/one").state in ("released", "free")
    assert recovering.locks.holder("acme/one") == ""
    assert coord.schedule(recovering)[0]["card_ids"] == ["PR-001"]


def test_current_assigned_anonymous_attempt_can_still_return_outcomes(tmp_path):
    store = make_store(tmp_path, session="")
    attempt_id = coord.schedule(store)[0]["attempt_id"]
    coord.apply_outcome(store, attempt_id, [ready()])
    restored = replay(store)
    assert restored.diary[attempt_id].result == "completed"
    assert restored.leases.get("acme/one").state == "released"


def collected_result(kind, card_id):
    if kind == "ready":
        return ready(card_id)
    if kind == "hold":
        return dict(owner_hold(), card_id=card_id)
    return {"card_id": card_id, "outcome": "merged", "commit_sha": HEAD,
            "merged_at": "2026-09-27T12:00:00Z"}


@pytest.mark.parametrize("kind", ["ready", "hold", "merged"])
@pytest.mark.parametrize("legacy_initial_outstanding", [False, True])
def test_incremental_collection_completes_and_releases_after_final_card(
        tmp_path, kind, legacy_initial_outstanding):
    store = make_store(tmp_path, [discovery(1), discovery(2)])
    attempt_id = coord.schedule(store)[0]["attempt_id"]
    if legacy_initial_outstanding:
        attempt = store.diary[attempt_id]
        attempt.outstanding = []
        store.record_attempt(attempt)
    first = coord.apply_outcome(store, attempt_id,
                                [collected_result(kind, "PR-001")])
    assert first["pending"] == ["PR-002"]
    assert replay(store).leases.get("acme/one").state == "held"
    resumed = replay(store)
    empty = coord.apply_outcome(resumed, attempt_id, [])
    assert empty["pending"] == ["PR-002"]
    last = coord.apply_outcome(resumed, attempt_id,
                               [collected_result(kind, "PR-002")])
    assert last["pending"] == []
    restored = replay(store)
    assert restored.diary[attempt_id].outstanding == []
    assert restored.diary[attempt_id].result == "completed"
    assert restored.leases.get("acme/one").state == "released"
    assert restored.locks.holder("acme/one") == ""


@pytest.mark.parametrize("kind", ["ready", "hold"])
def test_collecting_an_already_returned_card_refuses_the_entire_batch(tmp_path, kind):
    store = make_store(tmp_path, [discovery(1), discovery(2)])
    attempt_id = coord.schedule(store)[0]["attempt_id"]
    coord.apply_outcome(store, attempt_id, [collected_result(kind, "PR-001")])
    resumed = replay(store)
    before = Path(store.path).read_bytes()
    with pytest.raises(StoreError, match="already returned"):
        coord.apply_outcome(resumed, attempt_id, [
            collected_result(kind, "PR-002"), collected_result(kind, "PR-001")])
    assert Path(store.path).read_bytes() == before
    assert resumed.cards["PR-002"].state == State.NEW
    assert resumed.diary[attempt_id].outstanding == ["PR-002"]


def test_standalone_incident_link_persists_both_directions_without_duplicates(tmp_path):
    store = make_store(tmp_path, [discovery(1), discovery(2)])
    result = dict(owner_hold(), incident={"key": "broken-base",
                                         "claim": "the base workflow is broken"})
    issue = coord.link_incident(store, store.cards["PR-001"], result)
    first_replay = replay(store)
    assert first_replay.cards["PR-001"].issue_ids == [issue.id]
    assert first_replay.issues[issue.id].card_ids == ["PR-001"]
    coord.link_incident(first_replay, first_replay.cards["PR-001"], result)
    coord.link_incident(first_replay, first_replay.cards["PR-002"], result)
    restored = replay(store)
    assert len(restored.issues) == 1
    assert restored.issues[issue.id].card_ids == ["PR-001", "PR-002"]
    assert restored.cards["PR-001"].issue_ids == [issue.id]
    assert restored.cards["PR-002"].issue_ids == [issue.id]
