"""Admission and read-only scope refresh boundaries from the public sweep."""

from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import json
from pathlib import Path
import sys
import threading

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "plugins/repo-hygiene/skills/dependabot-sweep/scripts"
sys.path.insert(0, str(SCRIPTS))

import sweep_cli as cli
import sweep_coordinator as coord
import sweep_discovery as discovery
import sweep_patience as patience
from sweep_core import Card, RunHeader, State, Store, StoreError

HEAD = "a" * 40
NEW_HEAD = "b" * 40
AT = "2026-09-27T12:00:00Z"
LATER = "2026-09-27T12:01:00Z"
LAST = "2026-09-27T12:02:00Z"


def item(number=1, repo="one", **values):
    return {"org": "acme", "repo": repo, "number": number,
            "url": f"https://github.com/acme/{repo}/pull/{number}",
            "title": "bump dep", "head_sha": HEAD, **values}


def authority(visibility="all", repos=()):
    grant = {"mode": "inspect", "repairs": [], "pause_on_conflict": True,
             "reviewer_contexts": ["review"]}
    return {"mode": "automated", "repairs": ["code_repair"], "approved": [], "holds": [],
            "repositories": {}, "discovery_scopes": [{"kind": "org", "login": "acme",
                "visibility": visibility, "repos": list(repos), "authority": grant}]}


def store_at(tmp_path, items=None, **options):
    store = Store(str(tmp_path / "run.jsonl"), session="owner")
    coord.create_run(store, "R", "automated", "test", items or [item()],
                     scope_fixed=False, cutoff=AT, **options)
    return store


def inventory(store, items, at=AT, repos=("acme/one",), complete=True):
    return {"observed_at": at, "complete": complete,
            "coverage": discovery.coverage(store.header.authority),
            "scope_repositories": list(repos),
            "repositories": [{"nameWithOwner": rid, "visibility": "PUBLIC"} for rid in repos],
            "discoveries": items, "source": "saved-search-and-repository-inventory.json"}


def observation(card, at=AT, head=NEW_HEAD):
    return {"observed_at": at, "head_sha": head,
            "pull": {"status": 200, "data": {"number": card.number,
                "base": {"repo": {"full_name": card.repo_id}}, "head": {"sha": head}}},
            "checks": [{"name": "ci", "conclusion": "success"}]}


@pytest.mark.parametrize("now", [110, 200])
def test_expired_run_refuses_before_any_admission_side_effect(tmp_path, now):
    store = store_at(tmp_path)
    coord.start_run_clock(store, 10, now=100)
    before = Path(store.path).read_bytes()
    assert coord.schedule(store, now=now, pr_budget_secs=600, reserve_secs=0) == []
    assert Path(store.path).read_bytes() == before
    assert not store.diary and not store.leases.leases
    assert not Path(store.path + ".locks").exists()
    assert store.ids.counters == {"PR": 1}
    assert store.cards["PR-001"].state == State.NEW


@pytest.mark.parametrize("deadline,now,reserve", [(100, 100, 0), (130, 100, 30), (129, 100, 30)])
def test_card_boundary_and_validation_reserve_leave_card_unadmitted(tmp_path, deadline, now, reserve):
    store = store_at(tmp_path)
    store.cards["PR-001"].deadline_epoch = deadline
    store.upsert_card(store.cards["PR-001"])
    before = Path(store.path).read_bytes()
    assert coord.schedule(store, now=now, reserve_secs=reserve) == []
    assert Path(store.path).read_bytes() == before and not store.diary


def test_safe_default_batch_starts_only_admitted_card_clock(tmp_path):
    store = store_at(tmp_path, [item(1), item(2), item(3, "two")])
    tasks = coord.schedule(store, pr_budget_secs=600, now=100)
    assert [t["card_ids"] for t in tasks] == [["PR-001"]]
    assert [c.deadline_epoch for c in store.cards.values()] == [700, 0, 0]
    assert coord.schedule(store, pr_budget_secs=600, now=110) == []
    coord.apply_outcome(store, tasks[0]["attempt_id"], [{"card_id": "PR-001", "outcome": "closed",
                                                       "reason": "closed by upstream"}])
    next_task = coord.schedule(store, pr_budget_secs=600, now=120)[0]
    assert next_task["card_ids"] == ["PR-002"]
    assert store.cards["PR-002"].deadline_epoch == 720


def test_successor_inherits_deadline_and_run_caps_new_admission(tmp_path):
    store = store_at(tmp_path, [item(1), item(2, "two")])
    coord.start_run_clock(store, 700, now=100)
    first = coord.schedule(store, pr_budget_secs=600, now=100)[0]
    coord.reconcile(store, {"PR-001": {"merged": False}}, set())
    second = coord.schedule(store, pr_budget_secs=600, now=200)[0]
    assert second["attempt_id"] == "AGT-001.2"
    assert store.cards["PR-001"].deadline_epoch == 700
    other = coord.schedule(store, pr_budget_secs=600, now=250, capacity=2)[0]
    assert other["card_ids"] == ["PR-002"]
    assert store.cards["PR-002"].deadline_epoch == 800


def test_capacity_counts_foreign_quarantined_and_unrecognized_locks(tmp_path):
    store = store_at(tmp_path, [item(1), item(2, "two"), item(3, "three"), item(4, "four")])
    first = coord.schedule(store)[0]
    store.record_lease(store.leases.quarantine("acme/two", "unknown outcome"))
    Path(store.locks.directory, "outside__repo.lock").write_text("unknown protocol")
    foreign = Store.load(store.path, session="different-session")
    assert coord.schedule(foreign, capacity=3) == []
    task = coord.schedule(foreign, capacity=4)[0]
    assert task["card_ids"] == ["PR-003"]
    assert foreign.diary[first["attempt_id"]].session == "owner"
    assert foreign.leases.get("acme/two").state == "quarantined"


def test_concurrent_schedulers_share_one_capacity_and_do_not_spend_ids(tmp_path):
    store = store_at(tmp_path, [item(1), item(2, "two")])
    gate = threading.Barrier(2)
    def run(session):
        worker = Store.load(store.path, session=session)
        gate.wait(timeout=5)
        return coord.schedule(worker, now=100, pr_budget_secs=600)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(run, ["one", "two"]))
    assert sum(len(tasks) for tasks in results) == 1
    current = Store.load(store.path)
    assert set(current.diary) == {"AGT-001.1"}
    assert current.cards["PR-002"].deadline_epoch == 0


@pytest.mark.parametrize("options", [{"capacity": -1}, {"capacity": True}, {"batch_size": 0},
                                    {"reserve_secs": -1}, {"reserve_secs": None},
                                    {"reserve_secs": float("nan")},
                                    {"pr_budget_secs": 0}])
def test_invalid_admission_options_leave_journal_unchanged(tmp_path, options):
    store = store_at(tmp_path)
    before = Path(store.path).read_bytes()
    with pytest.raises(StoreError):
        coord.schedule(store, **options)
    assert Path(store.path).read_bytes() == before


def test_zero_capacity_allocates_nothing(tmp_path):
    store = store_at(tmp_path)
    assert coord.schedule(store, capacity=0) == []
    assert not store.diary


def test_expire_records_unassessed_run_budget_without_allocating_a_lease(tmp_path):
    store = store_at(tmp_path)
    coord.start_run_clock(store, 10, now=100)
    assert coord.expire(store, now=110) == ["PR-001"]
    assert store.cards["PR-001"].state == State.NEW
    assert store.cards["PR-001"].reason_code == "K14"
    assert not store.leases.leases and not store.diary
    assert coord.run_ending(store) == "incomplete"
    assert coord.expire(store, now=111) == []


def test_configured_batch_bound_leaves_rest_unstarted(tmp_path):
    store = store_at(tmp_path, [item(n) for n in range(1, 5)])
    task = coord.schedule(store, batch_size=2, pr_budget_secs=600, now=100)[0]
    assert task["card_ids"] == ["PR-001", "PR-002"]
    assert [c.deadline_epoch for c in store.cards.values()] == [700, 700, 0, 0]


def test_incremental_discovery_uses_frozen_owner_overrides_and_deduplicates(tmp_path):
    store = store_at(tmp_path, authority=authority("public"), items=[item(visibility="public")])
    existing = deepcopy(store.cards["PR-001"].to_dict())
    items = [item(head_sha=NEW_HEAD), item(2, "new", createdAt="2026-09-27T11:58:00Z",
                                        authority={"mode": "automated", "repairs": ["code_repair"]})]
    result = coord.discover_run(store, inventory(store, items + items, repos=("acme/one", "acme/new")))
    assert result["new_card_ids"] == ["PR-002"]
    assert result["snapshot"]["complete"] is True
    assert store.cards["PR-001"].to_dict() == existing
    assert store.cards["PR-002"].pr_created_at == "2026-09-27T11:58:00Z"
    assert store.cards["PR-002"].discovered_at == AT
    assert store.header.authority["repositories"]["acme/new"]["mode"] == "inspect"
    assert store.header.authority["repositories"]["acme/new"]["repairs"] == []


@pytest.mark.parametrize("fields", [item(2, "outside"), item(2, "excluded"),
                                    item(2, "one", visibility="private")])
def test_unconfigured_excluded_or_wrong_visibility_arrivals_never_gain_authority(tmp_path, fields):
    store = store_at(tmp_path, authority=authority("public", ["one", "excluded"]),
                     items=[item(visibility="public")], exclusions=["acme/excluded"])
    new = coord.register_arrival(store, fields, observed_at=LATER)
    assert new.id not in store.header.scope_ids
    assert "Unselected discovery" in new.reason_line
    assert set(store.header.authority["repositories"]) == {"acme/one"}


def test_legacy_new_repository_is_visible_unselected_and_known_repo_still_works(tmp_path):
    store = store_at(tmp_path)
    known = coord.register_arrival(store, item(2))
    new = coord.register_arrival(store, item(3, "new"))
    assert known.id in store.header.scope_ids and new.id not in store.header.scope_ids
    assert "scope reconciliation" in new.reason_line
    assert coord.register_arrival(store, item(2, head_sha=NEW_HEAD)).head_sha == HEAD


def test_late_discovery_records_creation_and_discovery_without_resetting_deadline(tmp_path):
    store = store_at(tmp_path, authority=authority())
    store.header.deadline_epoch = discovery.timestamp(AT)
    store.set_header(store.header)
    new = coord.register_arrival(store, item(2, createdAt="2026-09-27T11:58:00Z"), observed_at=LATER)
    assert new.state == State.NEW and new.reason_code == "K14"
    assert new.pr_created_at < AT < new.discovered_at
    assert coord.schedule(store, now=discovery.timestamp(LATER)) == []
    assert new.deadline_epoch == 0


def test_complete_inventory_can_report_absence_but_never_closes_a_card(tmp_path):
    store = store_at(tmp_path, authority=authority())
    result = coord.discover_run(store, inventory(store, []))
    assert result["snapshot"]["complete"] is True
    assert result["snapshot"]["open_card_ids"] == []
    assert store.cards["PR-001"].state == State.NEW


def test_newer_incomplete_inventory_replaces_live_count_and_finish_cannot_upgrade_it(tmp_path):
    store = store_at(tmp_path, authority=authority())
    coord.discover_run(store, inventory(store, [item()]))
    coord.discover_run(store, inventory(store, [], at=LATER, complete=False))
    assert store.header.discovery_snapshot["complete"] is False
    assert coord.finish_run(store, {"kind": "none"}) == "incomplete"
    with pytest.raises(StoreError):
        coord.finish_run(store, {"kind": "none"}, discovery_complete=True)


def test_decreased_repository_coverage_is_not_a_complete_count(tmp_path):
    store = store_at(tmp_path, authority=authority())
    result = coord.discover_run(store, inventory(store, [], repos=()))
    assert result["snapshot"]["complete"] is False
    assert "acme/one" in store.header.authority["repositories"]


def test_discovery_validation_rolls_back_and_stale_snapshot_cannot_replace_current(tmp_path):
    store = store_at(tmp_path, authority=authority())
    coord.discover_run(store, inventory(store, [item()], at=LATER))
    before = Path(store.path).read_bytes()
    for payload in [inventory(store, [item(2)], at=AT), inventory(store, [item(2), {"number": True}], at=LAST)]:
        with pytest.raises(StoreError):
            coord.discover_run(store, payload)
        assert Path(store.path).read_bytes() == before


def test_claimed_complete_inventory_with_wrong_scope_stays_incomplete(tmp_path):
    store = store_at(tmp_path, authority=authority())
    payload = inventory(store, [item()])
    payload["coverage"] = []
    result = coord.discover_run(store, payload)
    assert result["snapshot"]["complete"] is False
    assert result["snapshot"]["incomplete_reasons"]


@pytest.mark.parametrize("quarantined", [False, True])
def test_refresh_preserves_active_worker_and_quarantine_even_when_head_changes(tmp_path, quarantined):
    store = store_at(tmp_path, authority=authority())
    task = coord.schedule(store, pr_budget_secs=600, now=100)[0]
    if quarantined:
        coord.apply_outcome(store, task["attempt_id"], [{"card_id": "PR-001", "outcome": "unknown",
                                                       "op_note": "lost response"}])
    card = store.cards["PR-001"]
    original = card.to_dict()
    lease = deepcopy(store.leases.get(card.repo_id).to_dict())
    header = deepcopy(store.header.to_dict())
    result = coord.refresh_card(store, card.id, observation(card))
    assert result["observed_head"] == NEW_HEAD
    for key, value in original.items():
        if key not in ("evidence", "latest_observation"):
            assert card.to_dict()[key] == value
    assert store.leases.get(card.repo_id).to_dict() == lease
    assert store.header.to_dict() == header
    assert card.head_sha == HEAD
    assert Store.load(store.path).cards[card.id].latest_observation == result


def test_refresh_requires_matching_identity_and_rejects_stale_facts(tmp_path):
    store = store_at(tmp_path)
    card = store.cards["PR-001"]
    coord.refresh_card(store, card.id, observation(card, LATER))
    before = Path(store.path).read_bytes()
    bad = observation(card, LAST)
    bad["pull"]["data"]["number"] = 2
    for snapshot in [bad, observation(card, AT)]:
        with pytest.raises(StoreError):
            coord.refresh_card(store, card.id, snapshot)
        assert Path(store.path).read_bytes() == before


def test_old_record_defaults_preserve_journal_compatibility():
    card = Card.from_dict({"id": "PR-001", "org": "acme", "repo": "one", "number": 1,
                           "url": "u", "title": "t", "owner": "o"})
    assert card.pr_created_at == card.discovered_at == ""
    assert card.latest_observation == {}
    assert RunHeader.from_dict({"run_id": "R", "mode": "inspect"}).discovery_snapshot == {}


def test_repair_plan_reserves_validation_and_never_extends_deadline():
    assert patience.plan_repair(20, 100, 151)["decision"] == "repair"
    assert patience.plan_repair(20, 100, 150)["decision"] == "defer"
    assert patience.plan_repair(0, 150, 150, reserve_secs=0)["decision"] == "defer"
    assert patience.plan_repair(20, 100, 0)["decision"] == "defer"
    with pytest.raises(ValueError):
        patience.plan_repair(20, 100, 150, reserve_secs=float("inf"))


def test_cli_freezes_explicit_owner_scope_and_accepts_discovery_and_refresh(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("DEPENDABOT_SWEEP_CONFIG", raising=False)
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    path = tmp_path / "run.jsonl"
    initial = tmp_path / "initial.json"
    initial.write_text("[]")
    common = ["--store", str(path), "--session", "test", "--json"]
    assert cli.main(common + ["run", "create", "--run-id", "R", "--org", "acme",
                              "--evolving", "--file", str(initial)]) == 0
    capsys.readouterr()
    store = Store.load(str(path))
    evidence = tmp_path / "inventory.json"
    evidence.write_text(json.dumps(inventory(store, [item()])))
    assert cli.main(common + ["run", "discover", "--file", str(evidence)]) == 0
    assert json.loads(capsys.readouterr().out)["snapshot"]["complete"] is True
    saved = Store.load(str(path))
    evidence.write_text(json.dumps(observation(saved.cards["PR-001"])))
    assert cli.main(common + ["card", "refresh", "PR-001", "--file", str(evidence)]) == 0
    assert json.loads(capsys.readouterr().out)["observed_head"] == NEW_HEAD
    assert cli.main(common + ["attempt", "create", "--capacity", "0"]) == 0
    assert json.loads(capsys.readouterr().out) == []


def test_cli_inferred_owner_never_becomes_broad_authority(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("DEPENDABOT_SWEEP_CONFIG", raising=False)
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    path = tmp_path / "run.jsonl"
    initial = tmp_path / "initial.json"
    initial.write_text(json.dumps([item()]))
    assert cli.main(["--store", str(path), "--json", "run", "create", "--run-id", "R",
                     "--evolving", "--file", str(initial)]) == 0
    capsys.readouterr()
    store = Store.load(str(path))
    scope = store.header.authority["discovery_scopes"][0]
    assert scope["kind"] == "repo" and scope["repos"] == ["one"]
    arrived = coord.register_arrival(store, item(2, "new"))
    assert arrived.id not in store.header.scope_ids
