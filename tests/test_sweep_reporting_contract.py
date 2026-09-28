"""Behavioral reporting and durable follow-up contracts; no GitHub calls."""

import copy
import json
import sys
from pathlib import Path

import pytest

SCRIPTS = (Path(__file__).resolve().parents[1]
           / "plugins/repo-hygiene/skills/dependabot-sweep/scripts")
sys.path.insert(0, str(SCRIPTS))

import sweep_coordinator as coord
import sweep_report as report
from sweep_core import Card, Issue, State, Store, StoreError, utc_now

HEAD = "a" * 40
NEW_HEAD = "b" * 40


def make_store(tmp_path, count=1):
    store = Store(str(tmp_path / "run.jsonl"), session="reporting-owner")
    coord.create_run(store, "RUN-REPORT", "automated", "test authority", [
        {"org": "acme", "repo": "project", "number": n,
         "url": f"https://example.test/acme/project/pull/{n}",
         "title": f"bump package {n}", "head_sha": HEAD}
        for n in range(1, count + 1)])
    return store


def evidence(what="repair CI passed", head=HEAD):
    return [{"id": "EV-ci", "what": what, "establishes": what,
             "head_sha": head}]


def followup(**changes):
    result = {"key": "checker-policy", "repo_id": "acme/project",
              "claim": "Configured checker minimum differs from policy",
              "action": "Align the documented checker minimum",
              "action_owner": "repository maintainer",
              "attribution": "unknown", "evidence": evidence()}
    result.update(changes)
    return result


def hold(card_id="PR-001", code="K07", **changes):
    result = {"card_id": card_id, "outcome": "hold", "state": "WAITING",
              "head_sha": HEAD, "reason_code": code,
              "reason_line": "Reviewer thread still unresolved",
              "action": "Complete review on the repaired head",
              "action_owner": "sweeper", "evidence": evidence(),
              "resume_trigger": "review completed"}
    result.update(changes)
    return result


def collect(store, outcomes, **schedule_options):
    schedule_options.setdefault("batch_size", len(outcomes))
    task = coord.schedule(store, **schedule_options)[0]
    return coord.apply_outcome(store, task["attempt_id"], outcomes)


def test_followup_after_merge_preserves_operational_authority_and_replays(tmp_path):
    store = make_store(tmp_path)
    collect(store, [{"card_id": "PR-001", "outcome": "merged",
                     "commit_sha": "c" * 40, "merged_at": "2026-09-27T22:00:00Z"}])
    before = copy.deepcopy(store.cards["PR-001"].to_dict())
    header = copy.deepcopy(store.header.to_dict())
    leases = {key: value.to_dict() for key, value in store.leases.leases.items()}
    issue = coord.record_followup(store, followup(), ["PR-001"])
    loaded = Store.load(store.path, session=store.session)
    assert loaded.issues[issue.id].status == "open"
    assert loaded.issues[issue.id].kind == "followup"
    assert loaded.issues[issue.id].target == "acme/project"
    assert loaded.issues[issue.id].evidence == evidence()
    assert loaded.cards["PR-001"].issue_ids == [issue.id]
    after = loaded.cards["PR-001"].to_dict()
    after["issue_ids"] = before["issue_ids"]
    assert after == before
    assert loaded.header.to_dict() == header
    assert {key: value.to_dict() for key, value in loaded.leases.leases.items()} == leases


def test_followup_update_history_external_link_and_resolution(tmp_path):
    store = make_store(tmp_path)
    issue = coord.record_followup(store, followup(), ["PR-001"])
    coord.update_incident(store, issue.id, {
        "status": "in_progress", "attribution": "pre_existing",
        "attribution_note": "Reproduced on the base revision",
        "evidence": evidence("base control reproduces issue"),
        "external_links": [{"url": "https://example.test/issues/20",
                            "tracker": "github", "title": "Checker policy"}]})
    coord.update_incident(store, issue.id, {
        "status": "resolved", "evidence": evidence("fixed minimum verified")})
    loaded = Store.load(store.path)
    item = loaded.issues[issue.id]
    assert item.status == "resolved" and item.resolved_at
    assert len(item.evidence) == 3
    assert item.history[0]["status"] == "open"
    assert item.history[-1]["status"] == "in_progress"
    text = report.render_report(loaded)
    assert "pre_existing" in text and "fixed minimum verified" in text
    assert "https://example.test/issues/20" in text
    assert "External tracker reference recorded" in text


@pytest.mark.parametrize("changes", [
    {"claim": " "}, {"action": ""}, {"action_owner": ""},
    {"evidence": []}, {"evidence": [{}]}, {"evidence": ["log"]},
    {"status": "finished"}, {"attribution": "probably"},
    {"external_links": [{"url": "javascript:alert(1)"}]},
    {"status": []}, {"attribution": {}}, {"reason_code": []},
    {"unknown_field": "not silently dropped"},
])
def test_followup_strict_creation_rejects_garbage_atomically(tmp_path, changes):
    store = make_store(tmp_path)
    before = Path(store.path).read_bytes()
    with pytest.raises(StoreError):
        coord.record_followup(store, followup(**changes), ["PR-001"])
    assert Path(store.path).read_bytes() == before
    assert not store.issues and not store.cards["PR-001"].issue_ids


@pytest.mark.parametrize("changes", [{}, {"key": "new-identity"},
                                      {"status": "resolved"},
                                      {"evidence": []}, {"action": " "}])
def test_followup_update_rejects_empty_or_unsafe_changes(tmp_path, changes):
    store = make_store(tmp_path)
    issue = coord.record_followup(store, followup(), ["PR-001"])
    before = Path(store.path).read_bytes()
    with pytest.raises(StoreError):
        coord.update_incident(store, issue.id, changes)
    assert Path(store.path).read_bytes() == before


def test_shared_followup_deduplicates_and_links_every_card(tmp_path):
    store = make_store(tmp_path, 2)
    first = coord.record_followup(store, followup(), ["PR-001"])
    second = coord.record_followup(store, followup(), ["PR-002"])
    assert first.id == second.id
    loaded = Store.load(store.path)
    assert loaded.issues[first.id].card_ids == ["PR-001", "PR-002"]
    assert loaded.cards["PR-002"].issue_ids == [first.id]


def test_merged_outcome_can_record_followups_and_legacy_incident(tmp_path):
    store = make_store(tmp_path)
    collect(store, [{"card_id": "PR-001", "outcome": "merged",
                     "commit_sha": "c" * 40, "merged_at": "2026-09-27T22:00:00Z",
                     "evidence": evidence(), "followups": [followup()],
                     "incident": {"key": "old-protocol", "claim": "Old incident"},
                     "action": "Investigate old incident", "action_owner": "sweeper"}])
    assert store.cards["PR-001"].state == State.MERGED
    assert len(store.issues) == 2
    assert len(store.cards["PR-001"].issue_ids) == 2


def test_bad_followup_rolls_back_entire_outcome_batch(tmp_path):
    store = make_store(tmp_path, 2)
    task = coord.schedule(store)[0]
    before = Path(store.path).read_bytes()
    with pytest.raises(StoreError):
        coord.apply_outcome(store, task["attempt_id"], [
            hold(), hold("PR-002", followups=[followup(action="")])])
    assert Path(store.path).read_bytes() == before
    assert all(c.state == State.NEW for c in store.cards.values())


def test_budget_stop_keeps_repaired_ci_and_unresolved_review(tmp_path):
    store = make_store(tmp_path)
    collect(store, [hold()])
    collect(store, [hold(code="K14", reason_line="Original deadline expired",
                         evidence=[], action="Resume review in a new authorized run")],
            wake=["PR-001"])
    card = Store.load(store.path).cards["PR-001"]
    assert card.execution_stop["reason_code"] == "K14"
    assert card.blockers[0]["reason_code"] == "K07"
    assert card.evidence[0]["what"] == "repair CI passed"
    text = report.render_report(store)
    assert "Execution stop: K14 Original deadline expired" in text
    assert "Current blocker: K07 Reviewer thread still unresolved" in text
    assert "repair CI passed" in text


def test_changed_head_keeps_old_receipts_as_history_not_current_readiness(tmp_path):
    store = make_store(tmp_path)
    collect(store, [hold()])
    collect(store, [hold(head_sha=NEW_HEAD, code="K13",
                         reason_line="New head needs fresh checks",
                         evidence=evidence("new head only observed", NEW_HEAD))],
            wake=["PR-001"])
    card = store.cards["PR-001"]
    assert card.condition_history[0]["head_sha"] == HEAD
    row = report.report_snapshot(store)["cards"][0]
    assert [e["head_sha"] for e in row["current_evidence"]] == [NEW_HEAD]
    assert any(e.get("head_sha") == HEAD for e in row["historical_evidence"])
    assert "repair CI passed" in report.render_report(store)


def test_owner_hold_requires_actual_source_and_not_state_inference(tmp_path):
    store = make_store(tmp_path)
    task = coord.schedule(store)[0]
    before = Path(store.path).read_bytes()
    with pytest.raises(StoreError):
        coord.apply_outcome(store, task["attempt_id"], [
            hold(owner_hold={"reason": "Owner does not want this"})])
    assert Path(store.path).read_bytes() == before
    coord.apply_outcome(store, task["attempt_id"], [hold()])
    text = report.render_report(store)
    assert "Owner hold: no sourced owner hold recorded" in text


def test_sourced_owner_hold_persists_until_sourced_release(tmp_path):
    store = make_store(tmp_path)
    collect(store, [hold(owner_hold={"source": "user message 31", "reason": "Wait",
                                    "scope": "merge", "head_sha": HEAD})])
    collect(store, [hold(code="K14", evidence=[])], wake=["PR-001"])
    assert store.cards["PR-001"].owner_hold["source"] == "user message 31"
    collect(store, [hold(owner_hold={"source": "user message 34", "reason": "Released",
                                    "active": False, "scope": "merge"})],
            wake=["PR-001"])
    assert store.cards["PR-001"].owner_hold["active"] is False
    assert any(h["owner_hold"].get("source") == "user message 31"
               for h in store.cards["PR-001"].condition_history)


def test_legacy_journal_issue_loads_with_explicit_missing_report_fields(tmp_path):
    store = make_store(tmp_path)
    issue = Issue(id="ISS-001", key="baseline", repo_id="acme/project",
                  reason_code="K05", claim="Baseline problem", card_ids=["PR-001"])
    store.record_issue(issue)
    loaded = Store.load(store.path)
    assert loaded.issues[issue.id].kind == "incident"
    text = report.render_report(loaded)
    assert "recommendation missing from legacy record" in text
    assert "evidence missing from legacy record" in text
    assert "Local record only; no external tracker reference recorded" in text


def test_complete_individual_accounting_includes_closed_replacement_new_and_arrival(tmp_path):
    store = make_store(tmp_path, 6)
    states = [State.MERGED, State.CLOSED, State.CLOSED, State.NEW,
              State.UNKNOWN, State.WAITING]
    for card, state in zip(store.cards.values(), states):
        card.state = state
        store.upsert_card(card)
    replacement = Card("PR-007", "acme", "project", 7,
                       "https://example.test/acme/project/pull/7", "replacement", "acme",
                       state=State.MERGED, replaces="PR-003", head_sha=HEAD)
    arrival = Card("PR-008", "acme", "project", 8,
                   "https://example.test/acme/project/pull/8", "late", "acme")
    store.upsert_card(replacement)
    store.upsert_card(arrival)
    store.cards["PR-003"].replaced_by = "PR-007"
    store.upsert_card(store.cards["PR-003"])
    snap = report.report_snapshot(store)
    assert snap["counts"] == {"selected": 6, "direct_merged": 1,
                               "delivered_via_replacement": 1,
                               "closed_without_delivery": 1, "assessed_holds": 1,
                               "prepared": 0, "unassessed": 1, "unknown": 1}
    assert snap["delivery"] == {"direct": 1, "via_replacement": 1, "total": 2}
    assert len(snap["cards"]) == 8
    assert snap["live_open"]["count"] is None
    text = report.render_report(store, snapshot=snap)
    for card in store.cards.values():
        assert card.url in text and f"[{card.id}]" in text
    assert text.count("Next:") == 8
    assert "closed without delivery 1" in text
    assert "Live open PRs: unknown" in text
    assert "Follow-ups: none identified" in text


def test_delivery_does_not_count_merged_unselected_arrival(tmp_path):
    store = make_store(tmp_path)
    extra = Card("PR-002", "acme", "project", 2, "https://example.test/2", "late", "acme",
                 state=State.MERGED)
    store.upsert_card(extra)
    assert coord.delivery_counts(store)["total"] == 0


@pytest.mark.parametrize("change,known", [({}, True), ({"complete": False}, False),
    ({"scope_ids": []}, False), ({"scope_repositories": ["other/repo"]}, False),
    ({"open_card_ids": ["PR-999"]}, False), ({"observed_at": ""}, False)])
def test_live_open_count_only_from_complete_scope_bound_snapshot(tmp_path, change, known):
    store = make_store(tmp_path)
    store.header.authority = {"repositories": {"acme/project": {"mode": "automated"}}}
    value = {"observed_at": utc_now(), "complete": True,
             "scope_ids": ["PR-001"], "scope_repositories": ["acme/project"],
             "open_card_ids": ["PR-001"], "unselected_card_ids": [],
             "coverage": [{"kind": "repo", "login": "acme", "visibility": "all", "repos": ["project"]}],
             "source": "fresh REST inventory"}
    value.update(change)
    store.header.discovery_snapshot = value
    snap = report.report_snapshot(store)
    assert snap["live_open"]["count"] == (1 if known else None)


def test_newer_read_only_head_is_shown_without_claiming_repaired_readiness(tmp_path):
    store = make_store(tmp_path)
    collect(store, [hold()])
    card = store.cards["PR-001"]
    card.last_observation = "2026-09-27T23:00:00Z"
    card.latest_observation = {"observed_at": "2026-09-28T00:00:00Z",
                               "observed_head": NEW_HEAD,
                               "snapshot": {"state": "OPEN", "head_sha": NEW_HEAD}}
    row = report.report_snapshot(store)["cards"][0]
    assert row["current_evidence"] == []
    assert len(row["historical_evidence"]) == 1
    assert "newer observed head differs" in report.render_report(store)


def test_grouped_closure_decision_keeps_every_pr_and_no_broad_merge_approval(tmp_path):
    store = make_store(tmp_path, 2)
    decision = {"scope": "close", "group_key": "fixture-only", "why": "Inert fixtures",
                "approve_effect": "Close fixture-only PRs", "decline_effect": "Leave open",
                "recommendation": "Close after owner decision"}
    collect(store, [hold(f"PR-{n:03d}", state="NEEDS_OWNER", code="K16",
                         decision=decision) for n in (1, 2)])
    groups = report.approval_groups(store)
    assert len(groups) == 1 and len(groups[0]["cards"]) == 2
    text = report.render_approval(store)
    assert text.count("Inert fixtures") == 1
    for card in store.cards.values():
        assert card.url in text and card.head_sha in text
    assert "APPROVE ALL" not in text and "APPROVE <n|ALL>" not in text
    assert "does not authorize a merge" in text


def test_group_key_never_combines_different_scope_or_effects(tmp_path):
    store = make_store(tmp_path, 2)
    for n, scope in ((1, "close"), (2, "settings")):
        card = store.cards[f"PR-{n:03d}"]
        card.state = State.NEEDS_OWNER
        card.decision = {"group_key": "same", "scope": scope, "why": "Reason",
                         "approve_effect": "Effect", "decline_effect": "Hold",
                         "recommendation": "Decide"}
    assert len(report.approval_groups(store)) == 2


def test_saved_snapshot_renders_same_report_after_store_changes(tmp_path):
    store = make_store(tmp_path)
    snap = report.report_snapshot(store)
    before = report.render_report(store, snapshot=snap)
    store.cards["PR-001"].title = "changed after capture"
    assert report.render_report(store, snapshot=snap) == before
    assert "changed after capture" not in before


def test_continuation_reference_without_verification_is_not_active(tmp_path):
    store = make_store(tmp_path)
    store.header.continuation = {"kind": "watcher", "ref": "worker-42"}
    text = report.render_report(store)
    assert "unverified" in text and "active watcher" not in text


def test_old_issue_event_without_new_fields_loads_and_keeps_event_kind(tmp_path):
    path = tmp_path / "legacy.jsonl"
    path.write_text(json.dumps({"kind": "issue", "id": "ISS-001", "key": "base",
                                "repo_id": "acme/project", "reason_code": "K05",
                                "claim": "Old baseline finding"}) + "\n")
    store = Store.load(str(path), session="reporting-owner")
    assert store.issues["ISS-001"].kind == "incident"
    coord.update_incident(store, "ISS-001", {"action": "Diagnose with a matched control"})
    assert Store.load(str(path)).issues["ISS-001"].action == "Diagnose with a matched control"
    transaction = json.loads(path.read_text().splitlines()[-1])
    assert transaction["records"][0]["kind"] == "issue"
    assert transaction["records"][0]["issue_kind"] == "incident"


def test_run_report_does_not_claim_no_running_work_for_unreturned_attempt(tmp_path):
    store = make_store(tmp_path)
    coord.schedule(store)
    text = report.render_report(store)
    assert "Continuation: none running" not in text
    assert "worker attempts have no final result, liveness unverified" in text


@pytest.mark.parametrize("change", [
    {"coverage": []}, {"scope_ids": [{}]}, {"observed_at": "not a timestamp"},
    {"open_card_ids": [None]},
])
def test_invalid_inventory_never_establishes_current_open_count(tmp_path, change):
    store = make_store(tmp_path)
    store.header.authority = {"repositories": {"acme/project": {}}}
    store.header.discovery_snapshot = {
        "complete": True, "observed_at": utc_now(), "source": "REST inventory",
        "scope_ids": ["PR-001"], "scope_repositories": ["acme/project"],
        "open_card_ids": ["PR-001"], "coverage": [
            {"kind": "repo", "login": "acme", "visibility": "all", "repos": ["project"]}],
        **change}
    assert report.report_snapshot(store)["live_open"]["count"] is None


def test_inventory_before_newer_merge_cannot_claim_current_open_count(tmp_path):
    store = make_store(tmp_path)
    store.header.authority = {"repositories": {"acme/project": {}}}
    store.header.discovery_snapshot = {
        "complete": True, "observed_at": "2026-09-27T21:00:00Z", "source": "REST inventory",
        "scope_ids": ["PR-001"], "scope_repositories": ["acme/project"],
        "open_card_ids": ["PR-001"], "coverage": [
            {"kind": "repo", "login": "acme", "visibility": "all", "repos": ["project"]}]}
    store.cards["PR-001"].merged_at = "2026-09-27T22:00:00Z"
    live = report.report_snapshot(store)["live_open"]
    assert live["count"] is None and "predates" in live["reason"]


def test_new_result_can_clear_all_current_blockers_without_losing_old_receipts(tmp_path):
    store = make_store(tmp_path)
    collect(store, [hold(blockers=[
        {"kind": "review", "reason_code": "K07", "reason_line": "Review unresolved"},
        {"kind": "technical", "reason_code": "K04", "reason_line": "Regression pending"}])])
    collect(store, [{"card_id": "PR-001", "outcome": "ready", "head_sha": HEAD,
                     "reason_line": "All fresh gates passed", "evidence": evidence("fresh complete gates"),
                     "blockers": []}], wake=["PR-001"])
    assert not store.cards["PR-001"].blockers
    assert len(store.cards["PR-001"].evidence) == 2
    assert len(store.cards["PR-001"].condition_history[-1]["blockers"]) == 2


def test_reporting_release_does_not_erase_frozen_owner_authority(tmp_path):
    store = make_store(tmp_path)
    store.header.authority = {"holds": ["PR-001"]}
    store.set_header(store.header)
    collect(store, [hold(owner_hold={"source": "reported message", "reason": "Reported release",
                                    "active": False, "scope": "merge"})])
    assert Store.load(store.path).header.authority["holds"] == ["PR-001"]
    assert "still listed as held" in report.render_report(store)


def test_abbreviated_receipt_expands_only_with_matching_evaluated_head(tmp_path):
    store = make_store(tmp_path)
    collect(store, [hold(evidence=[{"id": "EV-short", "head": HEAD[:12],
                                   "what": "CI checked", "establishes": "CI passed"}])])
    assert store.cards["PR-001"].evidence[0]["head_sha"] == HEAD
    assert store.cards["PR-001"].evidence[0]["head"] == HEAD[:12]


def test_older_read_only_head_cannot_override_a_newer_evaluation(tmp_path):
    store = make_store(tmp_path)
    collect(store, [hold()])
    card = store.cards["PR-001"]
    card.last_observation = "2026-09-27T23:00:00Z"
    card.latest_observation = {"observed_at": "2026-09-27T22:00:00Z",
                               "observed_head": NEW_HEAD, "snapshot": {}}
    row = report.report_snapshot(store)["cards"][0]
    assert row["head_drift"] is False
    assert len(row["current_evidence"]) == 1


@pytest.mark.parametrize("code,outcome", [("K14", "hold"), ("K07", "ready")])
def test_contradictory_condition_records_are_rejected(tmp_path, code, outcome):
    store = make_store(tmp_path)
    task = coord.schedule(store)[0]
    before = Path(store.path).read_bytes()
    with pytest.raises(StoreError):
        coord.apply_outcome(store, task["attempt_id"], [
            hold(outcome=outcome, blockers=[{"kind": "review", "reason_code": code,
                                            "reason_line": "Unresolved condition"}])])
    assert Path(store.path).read_bytes() == before
