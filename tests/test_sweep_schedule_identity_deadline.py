"""Independent review regressions for repository identity and admission time."""

import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "plugins/repo-hygiene/skills/dependabot-sweep/scripts"
sys.path.insert(0, str(SCRIPTS))

import sweep_coordinator as coord
import sweep_discovery as discovery
from sweep_core import Store, StoreError


def found(number, repo="One"):
    return {"org": "acme", "repo": repo, "number": number,
            "url": f"https://github.com/acme/{repo}/pull/{number}",
            "title": "dependency", "head_sha": "a" * 40}


def authority():
    return {"repositories": {}, "discovery_scopes": [{
        "kind": "org", "login": "acme", "visibility": "all", "repos": [],
        "authority": {"mode": "automated", "repairs": [],
                      "pause_on_conflict": False, "reviewer_contexts": []}}]}


@pytest.mark.parametrize("saved_authority", [None, authority()])
def test_case_aliases_share_one_repository_and_one_worker(saved_authority):
    store = Store(session="review")
    coord.create_run(store, "review", "automated", "test", [found(1), found(2, "one")],
                     authority=saved_authority)
    tasks = coord.schedule(store, capacity=2, batch_size=2, pr_budget_secs=600, now=100)
    assert len(tasks) == 1
    assert tasks[0]["card_ids"] == ["PR-001", "PR-002"]
    assert len({card.repo_id for card in store.cards.values()}) == 1
    if saved_authority is not None:
        assert list(store.header.authority["repositories"]) == ["acme/One"]


def test_legacy_arrival_reuses_known_repository_case():
    store = Store(session="review")
    coord.create_run(store, "review", "automated", "test", [found(1)], scope_fixed=False)
    arrival = coord.register_arrival(store, found(2, "one"))
    assert arrival.repo_id == "acme/One"
    tasks = coord.schedule(store, capacity=2, batch_size=2, pr_budget_secs=600, now=100)
    assert len(tasks) == 1 and len(tasks[0]["card_ids"]) == 2


def test_conflicting_case_alias_grants_never_select_a_permissive_grant():
    value = authority()
    grant = value["discovery_scopes"][0]["authority"]
    value["repositories"] = {"acme/One": grant, "acme/one": {**grant, "mode": "inspect"}}
    selected, reason = discovery.repository_grant(value, "acme/one")
    assert selected is None and "conflict" in reason


def test_old_journal_case_aliases_are_never_dispatched_concurrently():
    store = Store(session="review")
    coord.create_run(store, "review", "automated", "test", [found(1), found(2)])
    store.cards["PR-002"].repo = "one"  # old journals may contain both spellings
    tasks = coord.schedule(store, capacity=2, batch_size=2, pr_budget_secs=600, now=100)
    assert len(tasks) == 1
    assert coord.schedule(store, capacity=2, pr_budget_secs=600, now=110) == []


def test_unknown_lock_under_case_alias_protects_same_repository(tmp_path):
    store = Store(str(tmp_path / "run.jsonl"), session="review")
    coord.create_run(store, "review", "automated", "test", [found(1)])
    lock = Path(store.locks.directory, "acme__one.lock")
    lock.parent.mkdir()
    lock.write_text("unknown legacy lock")
    assert coord.schedule(store, capacity=2, pr_budget_secs=600, now=100) == []
    assert lock.read_text() == "unknown legacy lock"
    assert not store.diary


@pytest.mark.parametrize("after_claim", [201.0, 180.0])
def test_delayed_claim_releases_unadmitted_lock_before_ids_or_lease(tmp_path, monkeypatch, after_claim):
    store = Store(str(tmp_path / "run.jsonl"), session="review")
    coord.create_run(store, "review", "automated", "test", [found(1)])
    coord.start_run_clock(store, 100, now=100)
    baseline = Path(store.path).read_bytes()
    clock = [100.0]
    real_claim = store.locks.claim
    def delayed_claim(repo_id, holder):
        claimed = real_claim(repo_id, holder)
        clock[0] = after_claim
        return claimed
    monkeypatch.setattr(store.locks, "claim", delayed_claim)
    monkeypatch.setattr(coord.time, "time", lambda: clock[0])
    assert coord.schedule(store, pr_budget_secs=600, reserve_secs=30) == []
    assert not store.diary and not store.leases.leases
    assert store.ids.counters == {"PR": 1}
    assert not store.cards["PR-001"].attempts
    assert store.cards["PR-001"].deadline_epoch == 0
    assert not list(Path(store.locks.directory).glob("*.lock"))
    assert Path(store.path).read_bytes() == baseline


def test_successful_claim_starts_clock_at_actual_admission(tmp_path, monkeypatch):
    store = Store(str(tmp_path / "run.jsonl"), session="review")
    coord.create_run(store, "review", "automated", "test", [found(1)])
    clock = [100.0]
    real_claim = store.locks.claim
    def delayed_claim(repo_id, holder):
        claimed = real_claim(repo_id, holder)
        clock[0] = 110.0
        return claimed
    monkeypatch.setattr(store.locks, "claim", delayed_claim)
    monkeypatch.setattr(coord.time, "time", lambda: clock[0])
    assert coord.schedule(store, pr_budget_secs=600)
    assert store.cards["PR-001"].deadline_epoch == 710
