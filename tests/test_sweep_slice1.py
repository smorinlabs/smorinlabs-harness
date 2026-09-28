"""tests/test_sweep_slice1.py — Slice 1 spine: states, cards, leases,
reconciliation, renderer, approval output.

Acceptance mapping: T01 crash accounting, T02 scope preservation,
T03 ten-PR report fixture, T10 replacement/arrival identity. Lease,
transition, and evidence rules carry the F04/F09/F11/F16 contracts.
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "plugins/repo-hygiene/skills/dependabot-sweep/scripts"

assert (SCRIPTS / "sweep_core.py").is_file()
assert (SCRIPTS / "sweep_coordinator.py").is_file()
assert (SCRIPTS / "sweep_report.py").is_file()

sys.path.insert(0, str(SCRIPTS))

import sweep_coordinator as coord
import sweep_report as report
from sweep_core import (
    LeaseError, State, Store, StoreError, TransitionError,
)


def discovery(org, repo, number, title="bump x"):
    return {"org": org, "repo": repo, "number": number,
            "url": f"https://example.test/{org}/{repo}/pull/{number}",
            "title": title, "owner": org, "head_sha": f"{number:040x}",
            "base_ref": "main"}


def make_store(tmp_path, discoveries, run_id="RUN-TEST-01", **options):
    store = Store(str(tmp_path / "run.jsonl"), session="slice1-coordinator")
    coord.create_run(store, run_id, mode="automated",
                     authorization="test-authorization",
                     discoveries=discoveries, **options)
    return store


def hold_result(card_id, state, code="K02", severity="low"):
    result = {"card_id": card_id, "outcome": "hold", "state": state,
              "reason_code": code, "reason_line": f"test reason {code}",
              "severity": severity, "confidence": "high",
              "evidence": [{"id": "EV-001", "link": "x"}],
              "action": "test action", "action_owner": "sweeper",
              "resume_trigger": "next run"}
    if state == "NEEDS_OWNER":
        result["decision"] = {"why": "test decision",
                              "approve_effect": "merge",
                              "decline_effect": "hold",
                              "recommendation": "APPROVE"}
    return result


# T01: a crashed worker leaves every card accounted for.
def test_t01_crash_accounts_every_card(tmp_path):
    store = make_store(tmp_path, [
        discovery("acme", "one", 1), discovery("acme", "one", 2),
        discovery("acme", "two", 3),
    ])
    taskings = coord.schedule(store, model="sol", capacity=5, batch_size=10)
    assert len(taskings) == 2  # one worker per repo
    by_repo = {t["repo_id"]: t for t in taskings}

    # No worker ever returns. Reconcile against fresh observation:
    # PR-001 merged, PR-002 untouched, PR-003 unobservable.
    summary = coord.reconcile(store, observed={
        "PR-001": {"merged": True, "commit": "c0ffee",
                   "at": "2026-09-22T00:00:00Z"},
        "PR-002": {"merged": False, "head": "head2"},
    }, live_attempts=set())

    assert store.cards["PR-001"].state == State.MERGED
    assert store.cards["PR-001"].merge_commit == "c0ffee"
    assert store.cards["PR-002"].state == State.NEW  # reschedulable
    assert store.cards["PR-003"].state == State.UNKNOWN
    assert summary["crashed"] == sorted(summary["crashed"])
    assert len(summary["crashed"]) == 2
    assert store.leases.get("acme/two").state == "quarantined"
    assert "PR-003" in summary["quarantined"]

    # The quarantined repo is not rescheduled; the reschedulable card is.
    retry = coord.schedule(store, model="terra", capacity=5, batch_size=10)
    assert [t["repo_id"] for t in retry] == ["acme/one"]
    assert retry[0]["card_ids"] == ["PR-002"]

    # The dead attempt ids are preserved for the successor story.
    assert store.diary[by_repo["acme/one"]["attempt_id"]].result == "crashed"


# T02: a question about a subset never narrows the objective.
def test_t02_subset_question_preserves_scope(tmp_path):
    store = make_store(tmp_path, [discovery("acme", "r", n) for n in range(
        1, 11)])
    before = list(store.header.scope_ids)
    cards = coord.describe_subset(store, ["PR-002", "PR-005", "PR-007"])
    assert [c.id for c in cards] == ["PR-002", "PR-005", "PR-007"]
    assert store.header.scope_ids == before
    assert len(store.header.scope_ids) == 10


def test_t02_unknown_card_in_query_raises(tmp_path):
    store = make_store(tmp_path, [discovery("acme", "r", 1)])
    try:
        coord.describe_subset(store, ["PR-999"])
    except StoreError:
        pass
    else:
        raise AssertionError("expected StoreError for out-of-scope query")


# T03: five merges plus five distinct blockers render exactly.
def test_t03_ten_pr_report_fixture(tmp_path):
    repos = ["alpha", "beta", "gamma", "delta", "epsilon"]
    store = make_store(tmp_path, [
        discovery("acme", repos[(n - 1) // 2], n, title=f"bump dep{n}")
        for n in range(1, 11)], run_id="RUN-EX-01")
    taskings = coord.schedule(store, model="sol", capacity=5, batch_size=10)
    assert len(taskings) == 5

    merged = [f"PR-00{n}" for n in range(1, 6)]
    holds = {
        "PR-006": ("BLOCKED", "K02", "low"),
        "PR-007": ("BLOCKED", "K05", "medium"),
        "PR-008": ("NEEDS_OWNER", "K07", "high"),
        "PR-009": ("WAITING", "K01", "low"),
        "PR-010": ("NEEDS_OWNER", "K08", "medium"),
    }
    for tasking in taskings:
        results = []
        for card_id in tasking["card_ids"]:
            if card_id in merged:
                results.append({"card_id": card_id, "outcome": "merged",
                                "commit_sha": f"sha{card_id}",
                                "merged_at": "2026-09-22T00:00:00Z"})
            else:
                state, code, sev = holds[card_id]
                results.append(hold_result(card_id, state, code, sev))
        coord.apply_outcome(store, tasking["attempt_id"], results)

    text = report.render_report(store, continuation="none")
    assert "RUN-EX-01 automated pass ended WITH EXCEPTIONS." in text
    assert "Selected scope: 10 PRs." in text
    assert "direct merged 5; delivered via replacement 0; closed without delivery 0; assessed holds 5; prepared 0; unassessed 0; unknown 0." in text
    assert "Delivered 5 selected updates (direct 5, via replacement 0)." in text
    for n in range(1, 11):
        assert f"[PR-{n:03d}]" in text  # ten distinct stable ids
    # Human-first identity on every line.
    assert 'acme/alpha#1 "bump dep1"' in text
    assert 'acme/epsilon#10 "bump dep10"' in text
    # Every selected PR has its own URL, outcome, and continuation, including
    # successful merges. Counts no longer imply an unevidenced live inventory.
    for card in store.cards.values():
        assert card.url in text
    assert "Live open PRs: unknown" in text
    assert text.count("Next:") == 10
    assert text.count("Owner:") == 10
    assert "Continuation: none running." in text
    assert "still running" not in text

    approval = report.render_approval(store)
    assert approval.startswith("DECISIONS REQUESTED -- 2 PRs in 2 scoped decisions.")
    first, second = approval.index("#1"), approval.index("#2")
    assert "[PR-008]" in approval[first:second]  # high severity first
    assert "Why:" in approval and "Recommend:" in approval
    assert "A merge approval must identify each PR and its exact head." in approval
    assert "APPROVE <n|ALL>" not in approval


# T10: replacements link; arrivals extend; nothing renumbers or double counts.
def test_t10_replacement_and_arrival_identity(tmp_path):
    store = make_store(tmp_path, [discovery("acme", "r", 1),
                                  discovery("acme", "r", 2)],
                       scope_fixed=False)
    taskings = coord.schedule(store, capacity=5, batch_size=10)
    coord.apply_outcome(store, taskings[0]["attempt_id"], [
        {"card_id": "PR-001", "outcome": "merged", "commit_sha": "a" * 7,
         "merged_at": "2026-09-22T00:00:00Z"},
        hold_result("PR-002", "BLOCKED", "K09", "medium"),
    ])
    replacement = coord.register_replacement(
        store, "PR-002",
        discovery("acme", "r", 3, title="maintainer redo of #2"))
    assert replacement.id == "PR-003"
    assert replacement.replaces == "PR-002"
    assert store.cards["PR-002"].state == State.CLOSED
    assert store.cards["PR-002"].replaced_by == "PR-003"
    assert store.cards["PR-001"].id == "PR-001"  # no renumbering

    arrival = coord.register_arrival(
        store, discovery("acme", "r", 4, title="late arrival"))
    assert arrival.id == "PR-004"
    assert arrival.state == State.NEW
    assert store.header.scope_ids[-1] == "PR-004"

    counts = coord.delivery_counts(store)
    assert counts == {"direct": 1, "via_replacement": 0, "total": 1}

    # Merging the replacement delivers the original's update exactly once.
    taskings = coord.schedule(store, capacity=5, batch_size=10)
    by_card = {c: t["attempt_id"] for t in taskings for c in t["card_ids"]}
    coord.apply_outcome(store, by_card["PR-003"], [
        {"card_id": "PR-003", "outcome": "merged", "commit_sha": "b" * 7,
         "merged_at": "2026-09-22T00:00:01Z"}])
    counts = coord.delivery_counts(store)
    assert counts == {"direct": 1, "via_replacement": 1, "total": 2}


def test_lease_double_acquire_refused(tmp_path):
    store = make_store(tmp_path, [discovery("acme", "r", 1)])
    coord.schedule(store)
    try:
        store.leases.acquire("acme/r", "AGT-999.1", ["PR-001"])
    except LeaseError:
        pass
    else:
        raise AssertionError("expected LeaseError on double acquire")


def test_lease_release_by_non_holder_refused(tmp_path):
    store = make_store(tmp_path, [discovery("acme", "r", 1)])
    coord.schedule(store)
    try:
        store.leases.release("acme/r", "AGT-999.1")
    except LeaseError:
        pass
    else:
        raise AssertionError("expected LeaseError on foreign release")


def test_illegal_transitions_refused(tmp_path):
    store = make_store(tmp_path, [discovery("acme", "r", 1),
                                  discovery("acme", "r", 2)])
    ambiguous = store.cards["PR-001"]
    ambiguous.transition_to(State.UNKNOWN)  # ambiguity can strike anywhere
    try:
        ambiguous.transition_to(State.CLOSED)
    except TransitionError:
        pass
    else:
        raise AssertionError("UNKNOWN must reconcile, never close directly")
    done = store.cards["PR-002"]
    done.transition_to(State.CLOSED)
    try:
        done.transition_to(State.READY)
    except TransitionError:
        pass
    else:
        raise AssertionError("terminal states must not exit")


def test_merged_outcome_requires_evidence(tmp_path):
    store = make_store(tmp_path, [discovery("acme", "r", 1)])
    taskings = coord.schedule(store)
    try:
        coord.apply_outcome(store, taskings[0]["attempt_id"],
                            [{"card_id": "PR-001", "outcome": "merged"}])
    except StoreError:
        pass
    else:
        raise AssertionError("merged without commit evidence must fail")
    assert store.cards["PR-001"].state == State.NEW


def test_hold_requires_action_owner_and_decision(tmp_path):
    store = make_store(tmp_path, [discovery("acme", "r", 1),
                                  discovery("acme", "r", 2)])
    taskings = coord.schedule(store)
    attempt = taskings[0]["attempt_id"]
    bad = hold_result("PR-001", "BLOCKED")
    del bad["action_owner"]
    try:
        coord.apply_outcome(store, attempt, [bad])
    except StoreError:
        pass
    else:
        raise AssertionError("hold without owner must fail")
    bad_owner = hold_result("PR-002", "NEEDS_OWNER")
    del bad_owner["decision"]["recommendation"]
    try:
        coord.apply_outcome(store, attempt, [bad_owner])
    except StoreError:
        pass
    else:
        raise AssertionError("NEEDS_OWNER without full decision must fail")


def test_unknown_outcome_quarantines_repo(tmp_path):
    store = make_store(tmp_path, [discovery("acme", "r", 1)])
    taskings = coord.schedule(store)
    coord.apply_outcome(store, taskings[0]["attempt_id"],
                        [{"card_id": "PR-001", "outcome": "unknown",
                          "op_note": "PUT timed out after 30s",
                          "action_owner": "sweeper"}])
    assert store.cards["PR-001"].state == State.UNKNOWN
    assert store.cards["PR-001"].reason_code == "K11"
    assert store.leases.get("acme/r").state == "quarantined"
    assert coord.schedule(store) == []  # repo stays unscheduled


def test_verify_merges_demotes_post_merge_surprise(tmp_path):
    store = make_store(tmp_path, [discovery("acme", "r", 1),
                                  discovery("acme", "r", 2)])
    taskings = coord.schedule(store, capacity=5, batch_size=10)
    coord.apply_outcome(store, taskings[0]["attempt_id"], [
        {"card_id": "PR-001", "outcome": "merged", "commit_sha": "a" * 7,
         "merged_at": "2026-09-22T00:00:00Z"},
        {"card_id": "PR-002", "outcome": "merged", "commit_sha": "b" * 7,
         "merged_at": "2026-09-22T00:00:00Z"},
    ])
    demoted = coord.verify_merges(store, {"PR-001": {"merged": False}})
    assert demoted == ["PR-001"]
    assert store.cards["PR-001"].state == State.UNKNOWN
    assert store.cards["PR-002"].state == State.MERGED  # unobserved: stands
    assert store.leases.get("acme/r").state == "quarantined"


def test_store_replay_roundtrip(tmp_path):
    store = make_store(tmp_path, [discovery("acme", "r", 1)])
    taskings = coord.schedule(store, model="sol")
    coord.apply_outcome(store, taskings[0]["attempt_id"],
                        [hold_result("PR-001", "WAITING", "K01", "low")])
    replayed = Store.load(str(tmp_path / "run.jsonl"))
    assert replayed.header.run_id == "RUN-TEST-01"
    assert replayed.header.scope_ids == ["PR-001"]
    assert replayed.cards["PR-001"].state == State.WAITING
    assert replayed.cards["PR-001"].reason_code == "K01"
    assert replayed.diary[taskings[0]["attempt_id"]].result == "completed"
    assert replayed.leases.get("acme/r").state == "released"
    assert replayed.ids.next("PR") == "PR-002"  # counters survive replay


# --- Slice 1 review repairs (Q4.A, 2026-09-22). Core layer. ---

def test_store_replay_recovers_id_counters_without_ids_record(tmp_path):
    """P4: legacy logs lacking an ids event still cannot reuse seen ids."""
    import json
    path = tmp_path / "run.jsonl"
    store = make_store(tmp_path, [discovery("acme", "r", 1),
                                  discovery("acme", "r", 2)])
    coord.schedule(store, model="sol")
    events = []
    for line in path.read_text().splitlines():
        record = json.loads(line)
        events.extend(record["records"] if record["kind"] == "transaction"
                      else [record])
    kept = [json.dumps(event) for event in events if event["kind"] != "ids"]
    path.write_text("\n".join(kept) + "\n")
    replayed = Store.load(str(path))
    assert replayed.ids.next("PR") == "PR-003"
    assert replayed.ids.attempt_id() == "AGT-002.1"


def test_card_observe_merged_from_any_open_state(tmp_path):
    """Observed reality may record a merge on any non-terminal card, with
    evidence; terminal cards refuse; missing evidence refuses."""
    store = make_store(tmp_path, [discovery("acme", "r", n)
                                  for n in range(1, 4)])
    waiting, owner, closed = (store.cards[f"PR-00{n}"] for n in (1, 2, 3))
    waiting.transition_to(State.WAITING)
    owner.transition_to(State.NEEDS_OWNER)
    closed.transition_to(State.CLOSED)
    waiting.observe_merged("c0ffee", "2026-09-22T00:00:00Z")
    owner.observe_merged("beef00", "2026-09-22T00:00:01Z")
    assert waiting.state == State.MERGED and waiting.merge_commit == "c0ffee"
    assert owner.state == State.MERGED and owner.merged_at.endswith(":01Z")
    try:
        closed.observe_merged("dead00", "2026-09-22T00:00:02Z")
    except TransitionError:
        pass
    else:
        raise AssertionError("terminal card must refuse an observed merge")
    fresh = Store()
    coord.create_run(fresh, "RUN-X", "automated", "auth",
                     [discovery("acme", "r", 9)])
    try:
        fresh.cards["PR-001"].observe_merged("", "2026-09-22T00:00:00Z")
    except StoreError:
        pass
    else:
        raise AssertionError("observed merge without commit must refuse")
    assert fresh.cards["PR-001"].state == State.NEW


def test_card_restore_prior_returns_unknown_card_to_prior_state(tmp_path):
    store = make_store(tmp_path, [discovery("acme", "r", 1),
                                  discovery("acme", "r", 2)])
    held = store.cards["PR-001"]
    held.transition_to(State.WAITING)
    held.transition_to(State.UNKNOWN)
    held.restore_prior()
    assert held.state == State.WAITING and held.prior_state == ""
    never = store.cards["PR-002"]
    never.transition_to(State.UNKNOWN)
    never.restore_prior()
    assert never.state == State.NEW
    try:
        never.restore_prior()
    except TransitionError:
        pass
    else:
        raise AssertionError("restore_prior only applies to UNKNOWN cards")


def test_register_replacement_closes_ready_original(tmp_path):
    """P3: a READY original can be superseded."""
    store = make_store(tmp_path, [discovery("acme", "r", 1)])
    taskings = coord.schedule(store)
    coord.apply_outcome(store, taskings[0]["attempt_id"], [
        {"card_id": "PR-001", "outcome": "ready", "reason_line": "green",
         "head_sha": "a" * 40,
         "evidence": [{"id": "EV-001"}]}])
    replacement = coord.register_replacement(
        store, "PR-001", discovery("acme", "r", 2, title="redo"))
    assert store.cards["PR-001"].state == State.CLOSED
    assert store.cards["PR-001"].replaced_by == replacement.id


# --- Slice 1 review repairs. Reconcile path. ---

def partially_returned_run(tmp_path):
    """One worker holds acme/r for PR-001 and PR-002, returns a WAITING
    hold for PR-001 only, then dies with PR-002 still pending."""
    store = make_store(tmp_path, [discovery("acme", "r", 1),
                                  discovery("acme", "r", 2)])
    tasking = coord.schedule(store, model="sol", capacity=5, batch_size=10)[0]
    coord.apply_outcome(store, tasking["attempt_id"],
                        [hold_result("PR-001", "WAITING", "K01", "low")])
    assert store.leases.get("acme/r").state == "held"
    return store, tasking["attempt_id"]


def test_reconcile_records_observed_merge_of_held_card(tmp_path):
    """P1: the queue merged a card a worker left WAITING; reconcile must
    record the merge, not crash on the worker-facing transition table."""
    store, attempt_id = partially_returned_run(tmp_path)
    summary = coord.reconcile(store, observed={
        "PR-001": {"merged": True, "commit": "c0ffee",
                   "at": "2026-09-22T00:00:00Z"},
        "PR-002": {"merged": False},
    }, live_attempts=set())
    assert store.cards["PR-001"].state == State.MERGED
    assert store.cards["PR-001"].merge_commit == "c0ffee"
    assert store.cards["PR-002"].state == State.NEW
    assert summary["merged"] == ["PR-001"]
    assert store.leases.get("acme/r").state == "released"
    assert store.diary[attempt_id].result == "crashed"


def test_reconcile_keeps_recorded_hold_when_observed_unmerged(tmp_path):
    """P2: a recorded WAITING hold is truth; an unmerged observation
    confirms it rather than resetting the card to NEW."""
    store, _ = partially_returned_run(tmp_path)
    summary = coord.reconcile(store, observed={
        "PR-001": {"merged": False}, "PR-002": {"merged": False},
    }, live_attempts=set())
    assert store.cards["PR-001"].state == State.WAITING
    assert store.cards["PR-001"].reason_code == "K01"
    assert store.cards["PR-002"].state == State.NEW
    assert summary["retained"] == ["PR-001"]
    assert summary["rescheduled"] == ["PR-002"]


def test_reconcile_outstanding_excludes_cards_proved_merged(tmp_path):
    """P9: a crashed attempt's outstanding list reflects the reconciled
    truth, not the pre-reconcile snapshot."""
    store = make_store(tmp_path, [discovery("acme", "r", 1),
                                  discovery("acme", "r", 2)])
    tasking = coord.schedule(store, model="sol", capacity=5, batch_size=10)[0]
    coord.reconcile(store, observed={
        "PR-001": {"merged": True, "commit": "c0ffee",
                   "at": "2026-09-22T00:00:00Z"},
        "PR-002": {"merged": False},
    }, live_attempts=set())
    assert store.diary[tasking["attempt_id"]].outstanding == ["PR-002"]


def test_card_observe_merge_retracted_only_from_merged(tmp_path):
    store = make_store(tmp_path, [discovery("acme", "r", 1),
                                  discovery("acme", "r", 2)])
    merged = store.cards["PR-001"]
    merged.observe_merged("c0ffee", "2026-09-22T00:00:00Z")
    merged.observe_merge_retracted("fresh observation shows unmerged")
    assert merged.state == State.UNKNOWN
    assert merged.prior_state == State.READY.value
    assert merged.reason_code == "K11"
    try:
        store.cards["PR-002"].observe_merge_retracted("never merged")
    except TransitionError:
        pass
    else:
        raise AssertionError("retraction applies to MERGED cards only")


# --- Slice 1 review repairs. Outcome collection. ---

def test_rejected_batch_leaves_no_card_mutated(tmp_path):
    """P7: one invalid result rejects the whole batch before any card,
    attempt, or lease changes."""
    store = make_store(tmp_path, [discovery("acme", "r", 1),
                                  discovery("acme", "r", 2)])
    tasking = coord.schedule(store)[0]
    try:
        coord.apply_outcome(store, tasking["attempt_id"], [
            {"card_id": "PR-001", "outcome": "merged", "commit_sha": "a" * 7,
             "merged_at": "2026-09-22T00:00:00Z"},
            {"card_id": "PR-002", "outcome": "merged"},
        ])
    except StoreError:
        pass
    else:
        raise AssertionError("batch with an invalid result must be refused")
    assert store.cards["PR-001"].state == State.NEW
    attempt = store.diary[tasking["attempt_id"]]
    assert attempt.phase == "assigned" and attempt.result == ""
    assert store.leases.get("acme/r").state == "held"


def test_duplicate_card_in_batch_refused(tmp_path):
    store = make_store(tmp_path, [discovery("acme", "r", 1)])
    tasking = coord.schedule(store)[0]
    try:
        coord.apply_outcome(store, tasking["attempt_id"], [
            hold_result("PR-001", "WAITING", "K01"),
            hold_result("PR-001", "BLOCKED", "K02"),
        ])
    except StoreError:
        pass
    else:
        raise AssertionError("a card may resolve once per batch")
    assert store.cards["PR-001"].state == State.NEW


def test_worker_cannot_claim_merge_on_card_it_holds(tmp_path):
    """The observed-merge path is for reconciliation only; a worker claim
    stays bound to the transition table."""
    store = make_store(tmp_path, [discovery("acme", "r", 1),
                                  discovery("acme", "r", 2)])
    attempt_id = coord.schedule(store)[0]["attempt_id"]
    coord.apply_outcome(store, attempt_id,
                        [hold_result("PR-001", "NEEDS_OWNER", "K07", "high")])
    try:
        coord.apply_outcome(store, attempt_id, [
            {"card_id": "PR-001", "outcome": "merged", "commit_sha": "a" * 7,
             "merged_at": "2026-09-22T00:00:00Z"}])
    except StoreError:
        pass
    else:
        raise AssertionError("NEEDS_OWNER -> MERGED by a worker must fail")
    assert store.cards["PR-001"].state == State.NEEDS_OWNER


def test_hold_rejects_unknown_severity_and_reason_code(tmp_path):
    """P6: an unvalidated severity would silently sort a critical item to
    the bottom of the approval set."""
    store = make_store(tmp_path, [discovery("acme", "r", 1)])
    attempt_id = coord.schedule(store)[0]["attempt_id"]
    for bad in (hold_result("PR-001", "NEEDS_OWNER", "K07", "CRITICAL"),
                hold_result("PR-001", "BLOCKED", "K99", "low"),
                {"card_id": "PR-001", "outcome": "unknown",
                 "op_note": "PUT timed out", "severity": "sev1"}):
        try:
            coord.apply_outcome(store, attempt_id, [bad])
        except StoreError:
            pass
        else:
            raise AssertionError(f"must refuse {bad.get('severity')!r} / "
                                 f"{bad.get('reason_code')!r}")
    assert store.cards["PR-001"].state == State.NEW


# --- Slice 1 review repairs. Report and scope. ---

def test_report_lists_ready_cards_under_prepared(tmp_path):
    """P5: a READY card is open work and must be visible in the body."""
    store = make_store(tmp_path, [discovery("acme", "r", 1, title="bump z")])
    tasking = coord.schedule(store)[0]
    coord.apply_outcome(store, tasking["attempt_id"], [
        {"card_id": "PR-001", "outcome": "ready", "reason_line": "green",
         "head_sha": "a" * 40,
         "evidence": [{"id": "EV-001"}]}])
    text = report.render_report(store)
    assert "prepared 1; unassessed 0; unknown 0" in text
    assert 'acme/r#1 "bump z" [PR-001] -- READY' in text
    assert "green" in text and "EV-001" in text
    assert "Run fresh merge gates" in text
    assert store.cards["PR-001"].url in text


def delivered_via_replacement(tmp_path):
    store = make_store(tmp_path, [discovery("acme", "r", 1, title="orig")])
    tasking = coord.schedule(store)[0]
    coord.apply_outcome(store, tasking["attempt_id"],
                        [hold_result("PR-001", "BLOCKED", "K09", "medium")])
    replacement = coord.register_replacement(
        store, "PR-001", discovery("acme", "r", 2, title="redo"))
    return store, replacement


def test_report_shows_delivery_via_replacement(tmp_path):
    """P11: the delivered objective is reported separately from the
    selected denominator, and the replacement merge is listed."""
    store, replacement = delivered_via_replacement(tmp_path)
    tasking = coord.schedule(store)[0]
    coord.apply_outcome(store, tasking["attempt_id"], [
        {"card_id": replacement.id, "outcome": "merged",
         "commit_sha": "b" * 7, "merged_at": "2026-09-22T00:00:01Z"}])
    text = report.render_report(store)
    assert "Selected scope: 1 PRs." in text
    assert "direct merged 0; delivered via replacement 1; closed without delivery 0" in text
    assert "Delivered 1 selected updates (direct 0, via replacement 1)." in text
    assert 'acme/r#1 "orig" [PR-001] -- CLOSED; delivered via replacement PR-002' in text
    assert 'acme/r#2 "redo" [PR-002] -- MERGED' in text
    assert "Replaces [PR-001]" in text
    assert replacement.url in text


def test_report_lists_unresolved_replacement_cards(tmp_path):
    store, replacement = delivered_via_replacement(tmp_path)
    tasking = coord.schedule(store)[0]
    coord.apply_outcome(store, tasking["attempt_id"],
                        [hold_result(replacement.id, "BLOCKED", "K02")])
    text = report.render_report(store)
    assert "Selected scope: 1 PRs." in text  # denominator unchanged
    assert "direct merged 0; delivered via replacement 0; closed without delivery 1" in text
    assert 'acme/r#1 "orig" [PR-001] -- CLOSED without delivery' in text
    assert 'acme/r#2 "redo" [PR-002] -- BLOCKED' in text
    assert "Replaces [PR-001]" in text
    assert replacement.url in text


def test_fixed_scope_arrival_recorded_outside_scope(tmp_path):
    """P10: a fixed-scope run records a late arrival but never widens
    its selected set or schedules the card."""
    store = make_store(tmp_path, [discovery("acme", "r", 1)])
    assert store.header.scope_fixed is True
    arrival = coord.register_arrival(
        store, discovery("acme", "r", 2, title="late"))
    assert arrival.id == "PR-002" and arrival.state == State.NEW
    assert store.header.scope_ids == ["PR-001"]
    assert coord.schedule(store) and all(
        "PR-002" not in t["card_ids"] for t in coord.schedule(store))
    text = report.render_report(store)
    assert "Selected scope: 1 PRs." in text
    assert "UNSELECTED ARRIVALS (1)" in text
    assert 'acme/r#2 "late" [PR-002] -- NEW; unassessed' in text
    assert arrival.url in text


def test_evolving_scope_arrival_extends_scope(tmp_path):
    store = make_store(tmp_path, [discovery("acme", "r", 1)],
                       scope_fixed=False)
    coord.register_arrival(store, discovery("acme", "r", 2))
    assert store.header.scope_ids == ["PR-001", "PR-002"]


def test_run_cutoff_persists_through_replay(tmp_path):
    store = make_store(tmp_path, [discovery("acme", "r", 1)],
                       cutoff="2026-09-22T00:00:00Z")
    assert store.header.cutoff == "2026-09-22T00:00:00Z"
    replayed = Store.load(str(tmp_path / "run.jsonl"))
    assert replayed.header.cutoff == "2026-09-22T00:00:00Z"
