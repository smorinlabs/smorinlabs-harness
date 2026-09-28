"""Action-scoped owner instructions and resilient decision reporting."""

import copy
import sys
from pathlib import Path

import pytest

SCRIPTS = (Path(__file__).resolve().parents[1]
           / "plugins/repo-hygiene/skills/dependabot-sweep/scripts")
sys.path.insert(0, str(SCRIPTS))

import sweep_coordinator as coord
import sweep_protocol as proto
import sweep_report as report
from sweep_core import State, Store, StoreError

HEAD = "a" * 40


def make_store(tmp_path, repositories=("acme/one",)):
    store = Store(str(tmp_path / "run.jsonl"), session="review")
    discoveries = []
    for number, repository in enumerate(repositories, 1):
        owner, repo = repository.split("/")
        discoveries.append({"org": owner, "repo": repo, "number": number,
                            "head_sha": HEAD, "title": "Update fixture dependency",
                            "url": f"https://example.test/{repository}/pull/{number}"})
    coord.create_run(store, "review", "automated", "test authority", discoveries)
    return store


def tasking(store, hold, *, frozen=False):
    card = store.cards["PR-001"]
    card.owner_hold = hold
    store.upsert_card(card)
    store.header.authority = {"holds": [card.id] if frozen else [],
                              "hold_records": {card.id: {"source": "saved user hold"}}}
    store.set_header(store.header)
    store = Store.load(store.path, session=store.session)
    return proto.Tasking.from_store(
        store, {"attempt_id": "AGT-001.1", "repo_id": card.repo_id,
                "card_ids": [card.id]}, mode="automated", repairs=proto.REPAIRS,
        op_timeout_secs=30, progress_log="unused.log", helper_path="unused.py")


@pytest.mark.parametrize("scope,merge_allowed,repair_allowed", [
    ("merge", False, True), ("repair", True, False), ("other", False, False),
    ("close", True, True), ("settings", True, True),
])
def test_structured_hold_restricts_only_its_action_scope(
        tmp_path, scope, merge_allowed, repair_allowed):
    store = make_store(tmp_path)
    hold = {"scope": scope, "source": "user message 12", "reason": "Pause this action"}
    task = tasking(store, hold)
    restored = proto.Tasking.from_dict(task.to_dict())
    assert restored.broad_holds == []
    for action in proto.MERGE_ACTIONS:
        assert proto.authorize(restored, action, "PR-001", now=0)[0] is merge_allowed
    for action in proto.REPAIRS:
        assert proto.authorize(restored, action, "PR-001", now=0)[0] is repair_allowed
    for action in proto.READ_ONLY_ACTIONS:
        assert proto.authorize(restored, action, "PR-001", now=0)[0]
    assert not proto.authorize(restored, "repo_settings", "PR-001", now=0)[0]
    assert hold["source"] in proto.render_brief(restored)


@pytest.mark.parametrize("hold", [
    {}, {"scope": "merge", "source": "new instruction", "reason": "Resume", "active": False},
    {"scope": "repair", "source": "new instruction", "reason": "Only repair hold"},
    {"scope": "settings", "source": "new instruction", "reason": "Only settings hold"},
])
def test_frozen_hold_still_restricts_every_mutation(tmp_path, hold):
    task = tasking(make_store(tmp_path), hold, frozen=True)
    assert task.broad_holds == ["PR-001"]
    for action in proto.MERGE_ACTIONS | proto.REPAIRS:
        allowed, reason = proto.authorize(task, action, "PR-001", now=0)
        assert not allowed and "K16" in reason
    assert proto.authorize(task, "observe", "PR-001", now=0)[0]


def test_released_structured_hold_does_not_restrict_authorized_actions(tmp_path):
    task = tasking(make_store(tmp_path), {
        "scope": "repair", "source": "user message 13", "reason": "Resume", "active": False})
    for action in proto.MERGE_ACTIONS | proto.REPAIRS:
        assert proto.authorize(task, action, "PR-001", now=0)[0]


def test_legacy_serialized_hold_keeps_broad_restriction(tmp_path):
    task = tasking(make_store(tmp_path), {
        "scope": "merge", "source": "user message 12", "reason": "Pause merges"})
    value = task.to_dict()
    value.pop("broad_holds")
    restored = proto.Tasking.from_dict(value)
    assert restored.broad_holds == restored.holds == ["PR-001"]
    for action in proto.MERGE_ACTIONS | proto.REPAIRS:
        assert not proto.authorize(restored, action, "PR-001", now=0)[0]


@pytest.mark.parametrize("card_deadline,run_deadline", [(100.0, 200.0), (200.0, 100.0)])
def test_exact_deadline_expires_every_mutation_but_not_observation(
        tmp_path, card_deadline, run_deadline):
    task = tasking(make_store(tmp_path), {})
    task.cards[0]["deadline_epoch"] = card_deadline
    task.run_deadline_epoch = run_deadline
    for action in proto.MERGE_ACTIONS | proto.REPAIRS:
        assert proto.authorize(task, action, "PR-001", now=99.0)[0]
        allowed, reason = proto.authorize(task, action, "PR-001", now=100.0)
        assert not allowed and "K14" in reason
    assert proto.authorize(task, "observe", "PR-001", now=100.0)[0]


def decision():
    return {"scope": "close", "group_key": "fixture-only", "why": "Fixture dependency inputs",
            "approve_effect": "Close the listed PRs", "decline_effect": "Keep them open",
            "recommendation": "Close after the requested decision"}


@pytest.mark.parametrize("field", ["why", "approve_effect", "decline_effect", "recommendation", "source"])
@pytest.mark.parametrize("value", [{"cause": "fixture"}, ["close"], 1, True, None, " "])
def test_nontext_decision_is_rejected_before_journal_write(tmp_path, field, value):
    store = make_store(tmp_path)
    attempt = coord.schedule(store)[0]["attempt_id"]
    fields = decision()
    fields[field] = value
    before = Path(store.path).read_bytes()
    with pytest.raises(StoreError, match="decision"):
        coord.apply_outcome(store, attempt, [{
            "card_id": "PR-001", "outcome": "hold", "state": "NEEDS_OWNER", "head_sha": HEAD,
            "reason_code": "K16", "reason_line": "Closure decision needed", "action": "Decide closure",
            "action_owner": "owner", "decision": fields}])
    assert Path(store.path).read_bytes() == before
    assert store.cards["PR-001"].state == State.NEW
    assert not store.diary[attempt].result
    assert store.leases.get("acme/one").state == "held"


@pytest.mark.parametrize("legacy_decision", [
    ["invalid decision"], None,
    {**decision(), "why": {"cause": "fixture"}},
    {**decision(), "approve_effect": ["close"], "scope": ["close"]},
    {**decision(), "group_key": {"key": "fixture"}, "recommendation": True},
    {**decision(), "scope": "unsupported"},
])
def test_malformed_legacy_decision_renders_without_claiming_valid_group(tmp_path, legacy_decision):
    store = make_store(tmp_path, ("acme/one", "acme/one"))
    for card in store.cards.values():
        card.state = State.NEEDS_OWNER
        card.decision = copy.deepcopy(legacy_decision)
        store.upsert_card(card)
    store = Store.load(store.path)
    before = Path(store.path).read_bytes()
    snapshot = report.report_snapshot(store)
    rendered = report.render_report(store, snapshot=snapshot)
    assert len(snapshot["approval_groups"]) == 2
    assert "Invalid legacy decision fields" in rendered
    for card in store.cards.values():
        assert card.url in rendered
        assert card.decision == legacy_decision
    assert Path(store.path).read_bytes() == before


def test_same_decision_key_groups_only_within_each_repository(tmp_path):
    store = make_store(tmp_path, ("acme/one", "acme/two", "acme/one"))
    for card in store.cards.values():
        card.state = State.NEEDS_OWNER
        card.decision = decision()
    groups = report.approval_groups(store)
    assert [[card["id"] for card in group["cards"]] for group in groups] == [
        ["PR-001", "PR-003"], ["PR-002"]]
    text = report.render_approval(store)
    for card in store.cards.values():
        assert card.url in text and card.head_sha in text
    assert "does not authorize a merge" in text
