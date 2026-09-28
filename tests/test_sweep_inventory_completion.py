"""Complete discovery is distinct from fixed worker selection and delivery."""

import copy
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "plugins/repo-hygiene/skills/dependabot-sweep/scripts"
sys.path.insert(0, str(SCRIPTS))

import sweep_coordinator as coord
import sweep_discovery as discovery
import sweep_report as report
from sweep_core import State, Store

AT = "2099-01-01T00:00:00Z"


def found(number=1, repo="one", visibility="public"):
    return {"org": "acme", "repo": repo, "number": number,
            "url": f"https://github.com/acme/{repo}/pull/{number}",
            "visibility": visibility, "title": "dependency", "head_sha": "a" * 40}


def fixed_store(tmp_path):
    grant = {"mode": "inspect", "repairs": [], "pause_on_conflict": False,
             "reviewer_contexts": []}
    authority = {"repositories": {}, "discovery_scopes": [{"kind": "org", "login": "acme",
                  "visibility": "public", "repos": [], "authority": grant}]}
    store = Store(str(tmp_path / "run.jsonl"), session="review")
    coord.create_run(store, "review", "inspect", "test", [found()], authority=authority)
    return store, grant


def inventory(store, extra_repo="acme/quiet", visibility="public", discoveries=None):
    return {"complete": True, "observed_at": AT, "source": "complete repository and PR inventory",
            "coverage": discovery.coverage(store.header.authority),
            "scope_repositories": ["acme/one", extra_repo],
            "repositories": [{"nameWithOwner": "acme/one", "visibility": "public"},
                             {"nameWithOwner": extra_repo, "visibility": visibility,
                              "authority": {"mode": "automated", "repairs": ["code_repair"]}}],
            "discoveries": [found()] if discoveries is None else discoveries}


def test_fixed_public_inventory_includes_quiet_repo_without_selecting_work(tmp_path):
    store, grant = fixed_store(tmp_path)
    before = {card_id: copy.deepcopy(card.to_dict()) for card_id, card in store.cards.items()}
    result = coord.discover_run(store, inventory(store))
    assert result["snapshot"]["complete"] is True
    assert result["new_card_ids"] == []
    assert store.header.scope_ids == ["PR-001"]
    assert {card_id: card.to_dict() for card_id, card in store.cards.items()} == before
    assert not store.diary and not store.leases.leases
    assert store.header.authority["repositories"]["acme/quiet"] == grant
    assert report.report_snapshot(store)["live_open"]["count"] == 1
    tasks = coord.schedule(store, capacity=3, batch_size=3, now=100, pr_budget_secs=600)
    assert len(tasks) == 1 and tasks[0]["card_ids"] == ["PR-001"]


def test_fixed_scope_still_does_not_admit_new_pr_in_derived_repo(tmp_path):
    store, grant = fixed_store(tmp_path)
    result = coord.discover_run(store, inventory(store, discoveries=[found(), found(2, "quiet")]))
    assert result["snapshot"]["complete"] is True
    assert result["snapshot"]["open_card_ids"] == ["PR-001", "PR-002"]
    assert result["snapshot"]["unselected_card_ids"] == ["PR-002"]
    assert result["snapshot"]["incomplete_reasons"] == []
    assert report.report_snapshot(store)["live_open"]["count"] == 2
    assert store.header.scope_ids == ["PR-001"]
    assert store.cards["PR-002"].state == State.NEW
    assert store.cards["PR-002"].deadline_epoch == 0
    assert not store.diary and not store.leases.leases
    tasks = coord.schedule(store, capacity=3, batch_size=3, now=100, pr_budget_secs=600)
    assert [t["card_ids"] for t in tasks] == [["PR-001"]]
    assert store.cards["PR-002"].deadline_epoch == 0
    assert store.cards["PR-002"].attempts == []
    assert store.header.authority["repositories"]["acme/quiet"] == grant


@pytest.mark.parametrize("owner,visibility", [("other", "public"), ("acme", "private")])
def test_out_of_scope_arrival_remains_visible_without_count_or_grant(tmp_path, owner, visibility):
    store, _ = fixed_store(tmp_path)
    arrival = found(2, "quiet", visibility)
    arrival.update(org=owner, url=f"https://github.com/{owner}/quiet/pull/2")
    result = coord.discover_run(store, inventory(
        store, extra_repo=f"{owner}/quiet", visibility=visibility,
        discoveries=[found(), arrival]))
    assert result["snapshot"]["complete"] is False
    assert result["snapshot"]["open_card_ids"] == ["PR-001"]
    assert result["snapshot"]["unselected_card_ids"] == ["PR-002"]
    assert report.report_snapshot(store)["live_open"]["count"] is None
    assert set(store.header.authority["repositories"]) == {"acme/one"}
    assert store.header.scope_ids == ["PR-001"]
    assert store.cards["PR-002"].state == State.NEW
    assert not store.diary and not store.leases.leases


def test_explicitly_excluded_arrival_is_not_counted_as_in_scope(tmp_path):
    store, _ = fixed_store(tmp_path)
    store.header.exclusions = ["acme/quiet#2"]
    store.set_header(store.header)
    result = coord.discover_run(store, inventory(store, discoveries=[found(), found(2, "quiet")]))
    assert result["snapshot"]["complete"] is False
    assert result["snapshot"]["open_card_ids"] == ["PR-001"]
    assert result["snapshot"]["unselected_card_ids"] == ["PR-002"]
    assert store.header.scope_ids == ["PR-001"]
    assert store.cards["PR-002"].state == State.NEW
    assert not store.diary and not store.leases.leases


def test_visibility_outside_frozen_scope_cannot_add_inventory_grant(tmp_path):
    store, _ = fixed_store(tmp_path)
    result = coord.discover_run(store, inventory(store, visibility="private"))
    assert result["snapshot"]["complete"] is False
    assert set(store.header.authority["repositories"]) == {"acme/one"}
    assert store.header.scope_ids == ["PR-001"]
    assert not store.diary


def test_pending_replacement_reason_never_claims_delivery_without_merge(tmp_path):
    store, _ = fixed_store(tmp_path)
    replacement = coord.register_replacement(store, "PR-001", found(2))
    original = store.cards["PR-001"]
    assert "update delivered there" not in original.reason_line
    assert "requires verified replacement merge proof" in original.reason_line
    pending = report.render_report(store)
    assert "CLOSED without delivery" in pending
    assert coord.delivery_counts(store)["total"] == 0
    task = coord.schedule(store, now=100, pr_budget_secs=600)[0]
    coord.apply_outcome(store, task["attempt_id"], [{"card_id": replacement.id, "outcome": "merged",
        "commit_sha": "b" * 40, "merged_at": "2026-09-27T12:00:00Z"}])
    delivered = report.render_report(store)
    assert "CLOSED; delivered via replacement PR-002" in delivered
    assert coord.delivery_counts(store)["total"] == 1


def test_old_premature_delivery_wording_is_explicitly_not_merge_proof(tmp_path):
    store, _ = fixed_store(tmp_path)
    coord.register_replacement(store, "PR-001", found(2))
    store.cards["PR-001"].reason_line = "Superseded by PR-002; update delivered there."
    text = report.render_report(store)
    assert "Historical delivery wording is not merge proof" in text
    assert "CLOSED without delivery" in text
    assert coord.delivery_counts(store)["total"] == 0
