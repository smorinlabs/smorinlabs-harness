"""tests/test_sweep_slice3.py — Slice 3: diagnosis (S3), authority (S4),
patience (S5), and one writer per repository.

Acceptance mapping: T04 baseline vs regression, T08 one writer per repo
and queue state, T09 mode/stop semantics, T11 total bounds across the
process tree. Plus the two Slice 2 gaps Slice 3 depends on: every reason
code has defaults, and a same-state hold refreshes instead of raising.
"""

import os
import sys
import textwrap
import time
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "plugins/repo-hygiene/skills/dependabot-sweep/scripts"
sys.path.insert(0, str(SCRIPTS))

import sweep_coordinator as coord  # noqa: E402
import sweep_diagnosis as diag  # noqa: E402
import sweep_evaluator as ev  # noqa: E402
import sweep_patience as patience  # noqa: E402
import sweep_protocol as proto  # noqa: E402
import sweep_report as report  # noqa: E402
from sweep_core import K_REASONS, State, Store, StoreError  # noqa: E402
import test_sweep_slice2 as evaluator_cases  # noqa: E402

POSIX_ONLY = pytest.mark.skipif(os.name == "nt",
                                reason="process groups are POSIX-only")


def discovery(org, repo, number, title="bump x"):
    return {"org": org, "repo": repo, "number": number,
            "url": f"https://example.test/{org}/{repo}/pull/{number}",
            "title": title, "owner": org, "head_sha": f"{number:040x}",
            "base_ref": "main"}


def make_store(tmp_path, discoveries, run_id="RUN-S3-01", session="slice3-coordinator",
               **options):
    store = Store(str(tmp_path / "run.jsonl"), session=session)
    coord.create_run(store, run_id, mode="automated",
                     authorization="test-authorization",
                     discoveries=discoveries, **options)
    return store


def hold(card_id, state="WAITING", code="K01", **extra):
    result = {"card_id": card_id, "outcome": "hold", "state": state,
              "reason_code": code, "reason_line": f"test {code}",
              "severity": "low", "confidence": "high",
              "evidence": [{"id": "EV-1"}], "action": "observe",
              "action_owner": "sweeper", "resume_trigger": "checks complete"}
    result.update(extra)
    return result


def control(revision, ref_kind="head", conclusion="failure",
            signature="AssertionError: test_parse", **over):
    fields = dict(workflow="ci", job="test", matrix="py3.12", attempt=1,
                  command="uv run pytest", toolchain="python 3.12.5",
                  environment="ubuntu-24.04", inputs="uv.lock@abc",
                  at="2026-09-22T12:00:00Z")
    fields.update(over)
    return diag.Control(revision=revision, ref_kind=ref_kind,
                        conclusion=conclusion, signature=signature, **fields)


# --- Slice 2 gaps Slice 3 depends on --------------------------------------

def test_every_reason_code_has_evaluator_defaults():
    assert set(ev.REASON_DEFAULTS) == set(K_REASONS)


def test_same_state_hold_refreshes_reason_without_transition(tmp_path):
    store = make_store(tmp_path, [discovery("acme", "one", 1)])
    (task,) = coord.schedule(store)
    coord.apply_outcome(store, task["attempt_id"],
                        [hold("PR-001", "BLOCKED", "K04")])
    (again,) = coord.schedule(store, wake=["PR-001"])
    coord.apply_outcome(store, again["attempt_id"],
                        [hold("PR-001", "BLOCKED", "K05")])
    card = Store.load(store.path).cards["PR-001"]
    assert (card.state, card.reason_code) == (State.BLOCKED, "K05")


def test_wake_redispatches_only_named_hold_cards(tmp_path):
    store = make_store(tmp_path, [discovery("acme", "one", 1),
                                  discovery("acme", "one", 2)])
    (task,) = coord.schedule(store)
    coord.apply_outcome(store, task["attempt_id"],
                        [hold("PR-001"), hold("PR-002")])
    assert coord.schedule(store) == []  # holds are never auto-dispatched
    (woken,) = coord.schedule(store, wake=["PR-002"])
    assert woken["card_ids"] == ["PR-002"]
    with pytest.raises(StoreError):
        coord.schedule(store, wake=["PR-404"])


# --- T04: matched baseline vs introduced regression (S3) ------------------

def test_t04_matched_baseline_failure_is_baseline_and_still_blocks():
    result = diag.diagnose(candidate=control("head1"),
                           baseline=control("base1", "base"))
    assert result.reason_code == "K05"
    assert result.confidence == "high"
    assert result.state == State.BLOCKED  # CI is never waived
    assert result.action_owner == "ci-fix"
    assert result.incident["key"]


def test_t04_matched_green_baseline_is_regression():
    result = diag.diagnose(candidate=control("head1"),
                           baseline=control("base1", "base",
                                            conclusion="success",
                                            signature=""))
    assert (result.reason_code, result.confidence) == ("K04", "high")
    assert result.state == State.BLOCKED
    assert not result.incident
    record = result.to_outcome("PR-001")
    assert record["action_owner"] == "ci-fix"
    assert record["resume_trigger"] == "after repair"
    assert "never waived" in record["action"]


def test_t04_unmatched_controls_are_inconclusive_and_name_the_gap():
    result = diag.diagnose(candidate=control("head1"),
                           baseline=control("base1", "base",
                                            toolchain="python 3.13.0"))
    assert (result.reason_code, result.confidence) == ("K04", "low")
    assert "toolchain" in result.reason_line
    assert result.mismatched == ["toolchain"]


def test_t04_missing_baseline_or_same_revision_is_not_attribution():
    missing = diag.diagnose(candidate=control("head1"), baseline=None)
    same = diag.diagnose(candidate=control("head1"),
                         baseline=control("head1", "base"))
    for result in (missing, same):
        assert (result.reason_code, result.confidence) == ("K04", "low")


def test_t04_both_fail_with_different_signatures_is_inconclusive():
    result = diag.diagnose(candidate=control("head1"),
                           baseline=control("base1", "base",
                                            signature="TypeError: other"))
    assert (result.reason_code, result.confidence) == ("K04", "low")
    assert not result.incident


def test_t04_same_head_green_retry_is_transient_mechanism_unknown():
    result = diag.diagnose(candidate=control("head1"),
                           baseline=control("base1", "base"),
                           retry=control("head1", conclusion="success",
                                         signature="", attempt=2))
    assert result.reason_code == "K17"
    assert result.confidence == "medium"
    assert "mechanism unknown" in result.reason_line
    assert result.state == State.WAITING  # re-evaluate; never READY


@pytest.mark.parametrize("signature", [
    "OSError: [Errno 28] No space left on device",
    "fatal: Could not resolve host: example.test",
    "The runner has received a shutdown signal",
    "Connection reset by peer",
])
@pytest.mark.parametrize("baseline_conclusion,baseline_signature,code,confidence", [
    ("success", "", "K04", "high"),
    ("failure", None, "K05", "high"),
    ("failure", "AssertionError: other", "K04", "low"),
], ids=["base-passes", "same-failure", "different-failure"])
def test_t04_matched_baseline_takes_precedence_over_environment_signature(
        signature, baseline_conclusion, baseline_signature, code, confidence):
    result = diag.diagnose(
        candidate=control("head1", signature=signature),
        baseline=control("base1", "base", conclusion=baseline_conclusion,
                         signature=(signature if baseline_signature is None
                                    else baseline_signature)))
    assert (result.reason_code, result.confidence) == (code, confidence)
    assert result.state == State.BLOCKED
    assert [item["id"] for item in result.evidence] == [
        "EV-diag-candidate", "EV-diag-baseline"]
    assert bool(result.incident) is (code == "K05")
    if confidence == "low":
        assert "different signatures" in result.reason_line


@pytest.mark.parametrize("baseline", [
    None,
    control("head1", "base"),
    control("base1", "head"),
    control("base1", "base", toolchain="python 3.13.0"),
], ids=["missing", "same-revision", "wrong-ref", "unmatched-conditions"])
def test_t04_environment_signature_without_matched_baseline_is_environment_failure(
        baseline):
    result = diag.diagnose(
        candidate=control("head1", signature="OSError: [Errno 28] No space "
                                             "left on device"),
        baseline=baseline)
    assert (result.reason_code, result.confidence) == ("K06", "medium")
    assert result.state == State.BLOCKED


def test_t04_no_diagnosis_branch_yields_ready():
    shapes = [
        (control("h"), control("b", "base")),
        (control("h"), control("b", "base", conclusion="success",
                               signature="")),
        (control("h"), control("b", "base", job="lint")),
        (control("h"), None),
    ]
    for candidate, baseline in shapes:
        assert diag.diagnose(candidate, baseline).state != State.READY


def test_t04_candidate_must_be_a_failure_on_the_head():
    with pytest.raises(ValueError):
        diag.diagnose(control("h", conclusion="success", signature=""),
                      control("b", "base"))
    with pytest.raises(ValueError):
        diag.diagnose(control("h", ref_kind="base"), control("b", "base"))


def test_t04_shared_baseline_incident_gets_one_issue_id(tmp_path):
    store = make_store(tmp_path, [discovery("acme", "one", 1),
                                  discovery("acme", "one", 2),
                                  discovery("acme", "two", 3)])
    tasks = {t["repo_id"]: t for t in coord.schedule(store)}
    base = control("base1", "base")
    one = [diag.diagnose(control(f"head{n}"), base).to_outcome(f"PR-00{n}")
           for n in (1, 2)]
    coord.apply_outcome(store, tasks["acme/one"]["attempt_id"], one)
    other = diag.diagnose(control("head3"),
                          control("base9", "base")).to_outcome("PR-003")
    coord.apply_outcome(store, tasks["acme/two"]["attempt_id"], [other])
    reloaded = Store.load(store.path)
    first, second, third = (reloaded.cards[f"PR-00{n}"] for n in (1, 2, 3))
    assert first.issue_ids == second.issue_ids == ["ISS-001"]
    assert third.issue_ids == ["ISS-002"]
    issue = reloaded.issues["ISS-001"]
    assert issue.card_ids == ["PR-001", "PR-002"]
    assert issue.reason_code == "K05"
    text = report.render_report(reloaded)
    assert "INCIDENTS (2)" in text
    assert "[ISS-001] affects PR-001, PR-002" in text


def test_t04_incident_record_requires_key_and_claim(tmp_path):
    store = make_store(tmp_path, [discovery("acme", "one", 1)])
    (task,) = coord.schedule(store)
    with pytest.raises(StoreError):
        coord.apply_outcome(store, task["attempt_id"], [
            hold("PR-001", "BLOCKED", "K05", incident={"key": "k"})])


# --- T09: authority and stop semantics (S4) -------------------------------

def tasking_for(store, mode="automated", repairs=(), approved=(), holds=(),
                task=None):
    task = task or coord.schedule(store)[0]
    return proto.Tasking.from_store(
        store, task, mode=mode, repairs=repairs, op_timeout_secs=30,
        progress_log="/tmp/log", helper_path="/tmp/gh_merge.py",
        approved=approved, holds=holds)


def test_t09_mode_matrix_exact_authority(tmp_path):
    rows = [
        # mode, repairs, approved, holds, merge PR-001?, branch_update?
        ("inspect", ["branch_update"], [], [], False, False),
        ("automated", [], [], [], True, False),
        ("automated", ["branch_update"], [], [], True, True),
        ("automated", ["branch_update"], [], ["PR-001"], False, False),
        ("gated", ["branch_update"], [], [], False, True),
        ("gated", [], ["PR-001"], [], True, False),
    ]
    for index, (mode, repairs, approved, holds, merge, update) in \
            enumerate(rows):
        (tmp_path / str(index)).mkdir()
        store = make_store(tmp_path / str(index),
                           [discovery("acme", "one", 1)])
        tasking = tasking_for(store, mode, repairs, approved, holds)
        allowed, why = proto.authorize(tasking, "merge", "PR-001", now=0)
        assert allowed is merge, (mode, why)
        allowed, why = proto.authorize(tasking, "branch_update", "PR-001",
                                       now=0)
        assert allowed is update, (mode, repairs, holds, why)
        for read_only in ("observe", "diagnose"):
            assert proto.authorize(tasking, read_only, "PR-001", now=0)[0]


def evaluate_scheduled_card(store, task, observation=None):
    """Evaluate fresh evidence with the persisted approval and actual lease."""
    card = store.cards["PR-001"]
    authority = store.header.authority
    lease = store.leases.get(card.repo_id)
    return evaluator_cases.evaluate(
        obs=observation,
        auth=ev.Authority(
            mode=authority["mode"],
            approved=card.id in authority.get("approved", []),
            deadline_epoch=card.deadline_epoch or None),
        track=ev.Tracking(
            lease_held=(lease.state == "held" and
                        lease.holder == task["attempt_id"]),
            repo_quarantined=lease.state == "quarantined"))


@pytest.fixture
def approved_owner_hold(tmp_path):
    found = discovery("acme", "one", 1)
    found["head_sha"] = evaluator_cases.HEAD
    store = Store(str(tmp_path / "run.jsonl"))
    coord.create_run(store, "RUN-OWNER-01", mode="gated",
                     authorization="test-authorization", discoveries=[found])
    store.header.authority = {"mode": "gated", "approved": []}
    store.set_header(store.header)
    (first,) = coord.schedule(store, now=evaluator_cases.NOW,
                              pr_budget_secs=600)
    owner_hold = evaluate_scheduled_card(store, first)
    assert (owner_hold.state, owner_hold.reason_code) == (State.NEEDS_OWNER, "K16")
    coord.apply_outcome(store, first["attempt_id"],
                        [owner_hold.to_outcome("PR-001")])
    store = Store.load(store.path)
    assert store.cards["PR-001"].state == State.NEEDS_OWNER
    assert store.leases.get("acme/one").state == "released"

    store.header.authority["approved"] = ["PR-001"]
    store.set_header(store.header)
    store = Store.load(store.path)
    assert store.header.authority["approved"] == ["PR-001"]
    (woken,) = coord.schedule(store, wake=["PR-001"], now=evaluator_cases.NOW + 1)
    assert store.cards["PR-001"].state == State.NEEDS_OWNER
    assert store.leases.get("acme/one").state == "held"
    return store, woken


@pytest.mark.parametrize("conclusion,status,state,code", [
    ("failure", "completed", State.BLOCKED, "K04"),
    (None, "in_progress", State.WAITING, "K01"),
], ids=["fresh-ci-failure", "fresh-ci-pending"])
def test_t09_approved_owner_hold_collects_fresh_technical_hold(
        approved_owner_hold, conclusion, status, state, code):
    store, woken = approved_owner_hold
    observation = evaluator_cases.observe(
        check_runs=evaluator_cases.section(evaluator_cases.check_runs(
            evaluator_cases.run("ci/test", conclusion=conclusion, status=status))))
    result = evaluate_scheduled_card(store, woken, observation)
    assert (result.state, result.reason_code) == (state, code)

    collected = coord.apply_outcome(store, woken["attempt_id"],
                                    [result.to_outcome("PR-001")])
    assert collected["pending"] == []
    reloaded = Store.load(store.path)
    card = reloaded.cards["PR-001"]
    assert (card.state, card.reason_code) == (state, code)
    assert card.evidence == result.evidence
    assert reloaded.diary[woken["attempt_id"]].result == "completed"
    assert reloaded.leases.get("acme/one").state == "released"

    # Once CI is green, the same approved card can be evaluated and prepared.
    # Scheduling again also proves collection released the repository lock.
    (again,) = coord.schedule(reloaded, wake=["PR-001"],
                              now=evaluator_cases.NOW + 2)
    ready = evaluate_scheduled_card(reloaded, again)
    assert ready.state == State.READY
    coord.apply_outcome(reloaded, again["attempt_id"],
                        [ready.to_outcome("PR-001")])
    final = Store.load(store.path)
    assert final.cards["PR-001"].state == State.READY
    assert final.leases.get("acme/one").state == "released"


def test_t09_approved_owner_hold_cannot_be_collected_as_directly_merged(
        approved_owner_hold):
    store, woken = approved_owner_hold
    before = Path(store.path).read_bytes()
    with pytest.raises(StoreError, match="NEEDS_OWNER -> MERGED"):
        coord.apply_outcome(store, woken["attempt_id"], [{
            "card_id": "PR-001", "outcome": "merged", "commit_sha": "c" * 40,
            "merged_at": "2026-09-22T12:00:00Z"}])
    assert Path(store.path).read_bytes() == before
    reloaded = Store.load(store.path)
    assert reloaded.cards["PR-001"].state == State.NEEDS_OWNER
    assert reloaded.diary[woken["attempt_id"]].result == ""
    assert reloaded.leases.get("acme/one").state == "held"


def test_t09_budget_exhaustion_stops_mutation_not_observation(tmp_path):
    store = make_store(tmp_path, [discovery("acme", "one", 1)])
    task = coord.schedule(store, pr_budget_secs=60, now=1000.0)[0]
    tasking = tasking_for(store, "automated", ["branch_update"], task=task)
    assert proto.authorize(tasking, "merge", "PR-001", now=1059.0)[0]
    allowed, why = proto.authorize(tasking, "merge", "PR-001", now=1061.0)
    assert not allowed and "K14" in why
    assert proto.authorize(tasking, "observe", "PR-001", now=1061.0)[0]


def test_t09_unknown_and_forbidden_repairs_are_refused(tmp_path):
    store = make_store(tmp_path, [discovery("acme", "one", 1)])
    task = coord.schedule(store)[0]
    for repairs in (["repo_settings"], ["rewrite_history"]):
        with pytest.raises(ValueError):
            tasking_for(store, "automated", repairs, task=task)
    tasking = tasking_for(store, "automated", sorted(proto.REPAIRS),
                          task=task)
    for repair in proto.REPAIRS:
        assert proto.authorize(tasking, repair, "PR-001", now=0)[0]
    allowed, _ = proto.authorize(tasking, "repo_settings", "PR-001", now=0)
    assert not allowed


def test_t09_no_auto_fix_compat_maps_to_inspect():
    assert proto.resolve_mode() == "automated"
    assert proto.resolve_mode(auto_fix=False) == "inspect"
    assert proto.resolve_mode(check=True) == "inspect"
    assert proto.resolve_mode(gated=True) == "gated"
    assert proto.resolve_mode(auto_fix=False, gated=True) == "inspect"


def test_t09_scope_and_run_deadline_reach_every_worker(tmp_path):
    store = make_store(tmp_path, [discovery("acme", "one", 1)],
                       scope_fixed=True, cutoff="2026-09-22T10:00:00Z")
    coord.start_run_clock(store, run_budget_secs=300, now=1000.0)
    task = coord.schedule(store, pr_budget_secs=600, now=1000.0)[0]
    tasking = tasking_for(store, task=task)
    assert tasking.scope_fixed is True
    assert tasking.cutoff == "2026-09-22T10:00:00Z"
    assert tasking.run_deadline_epoch == 1300.0
    # A card deadline never outlives the run.
    assert store.cards["PR-001"].deadline_epoch == 1300.0
    brief = proto.render_brief(tasking)
    assert "fixed snapshot taken at 2026-09-22T10:00:00Z" in brief
    assert "never narrows" in brief


def test_t09_run_clock_is_set_once(tmp_path):
    store = make_store(tmp_path, [discovery("acme", "one", 1)])
    coord.start_run_clock(store, run_budget_secs=300, now=1000.0)
    with pytest.raises(StoreError):
        coord.start_run_clock(store, run_budget_secs=900, now=2000.0)
    assert Store.load(store.path).header.deadline_epoch == 1300.0


def test_t09_run_ending_and_stop_reason(tmp_path):
    store = make_store(tmp_path, [discovery("acme", "one", 1),
                                  discovery("acme", "two", 2)])
    assert coord.run_ending(store) == "incomplete"  # unprocessed NEW
    tasks = {t["repo_id"]: t for t in coord.schedule(store)}
    coord.apply_outcome(store, tasks["acme/one"]["attempt_id"], [
        {"card_id": "PR-001", "outcome": "merged", "commit_sha": "c" * 40,
         "merged_at": "2026-09-22T12:00:00Z"}])
    coord.apply_outcome(store, tasks["acme/two"]["attempt_id"],
                        [hold("PR-002")])
    assert coord.run_ending(store) == "completed_with_exceptions"
    assert coord.run_ending(store, discovery_complete=False) == "incomplete"
    ending = coord.finish_run(store, patience.continuation("none"))
    reloaded = Store.load(store.path)
    assert ending == reloaded.header.stop_reason == \
        "completed_with_exceptions"
    assert "Continuation: none running." in report.render_report(reloaded)


# --- T11: total bounds across the process tree (S5) -----------------------

def script(tmp_path, name, body):
    path = tmp_path / name
    path.write_text(textwrap.dedent(body), encoding="utf-8")
    return [sys.executable, str(path)]


@POSIX_ONLY
def test_t11_hung_child_is_killed_at_the_deadline(tmp_path):
    argv = script(tmp_path, "hang.py", "import time\ntime.sleep(60)\n")
    start = time.time()
    result = patience.run_bounded(argv, deadline_epoch=start + 1.0,
                                  grace_secs=0.5)
    assert result.timed_out
    assert result.elapsed < 3.0


@POSIX_ONLY
def test_t11_grandchild_dies_with_the_tree(tmp_path):
    pid_file = tmp_path / "grandchild.pid"
    argv = script(tmp_path, "spawn.py", f"""
        import subprocess, sys, time
        child = subprocess.Popen([sys.executable, "-c",
                                  "import time; time.sleep(60)"])
        open({str(pid_file)!r}, "w").write(str(child.pid))
        time.sleep(60)
        """)
    result = patience.run_bounded(argv, deadline_epoch=time.time() + 1.5,
                                  grace_secs=0.5)
    assert result.timed_out
    grandchild = int(pid_file.read_text())
    for _ in range(40):
        try:
            os.kill(grandchild, 0)
        except ProcessLookupError:
            break
        time.sleep(0.05)
    else:
        os.kill(grandchild, 9)
        pytest.fail("grandchild outlived the deadline")


@POSIX_ONLY
def test_t11_streaming_output_does_not_extend_the_deadline(tmp_path):
    argv = script(tmp_path, "stream.py", """
        import sys, time
        while True:
            print("tick", flush=True)
            time.sleep(0.1)
        """)
    start = time.time()
    result = patience.run_bounded(argv, deadline_epoch=start + 1.0,
                                  grace_secs=0.5)
    assert result.timed_out and "tick" in result.stdout
    assert result.elapsed < 3.0


@POSIX_ONLY
def test_t11_slow_authentication_counts_against_the_same_budget(tmp_path):
    argv = script(tmp_path, "auth.py", """
        import time
        time.sleep(5)  # credential acquisition that never returns in time
        print("authenticated")
        """)
    result = patience.run_bounded(argv, deadline_epoch=time.time() + 0.8,
                                  grace_secs=0.3)
    assert result.timed_out and "authenticated" not in result.stdout


def test_t11_passed_deadline_never_starts_and_retry_gets_no_new_window(
        tmp_path):
    marker = tmp_path / "ran"
    argv = script(tmp_path, "mark.py",
                  f"open({str(marker)!r}, 'w').write('x')\n")
    deadline = time.time() - 1
    for _ in range(2):  # the retry passes the same absolute epoch
        result = patience.run_bounded(argv, deadline_epoch=deadline)
        assert result.timed_out and not result.started
    assert not marker.exists()


def test_t11_finished_child_reports_its_exit(tmp_path):
    argv = script(tmp_path, "ok.py", "print('done')\nraise SystemExit(10)\n")
    result = patience.run_bounded(argv, deadline_epoch=time.time() + 30)
    assert (result.returncode, result.timed_out) == (10, False)
    assert "done" in result.stdout


def test_t11_delegation_inherits_the_earlier_deadline():
    parent = {"SWEEP_DEADLINE_EPOCH": "1500"}
    env = patience.delegate_env(parent, deadline_epoch=2000.0)
    assert env["SWEEP_DEADLINE_EPOCH"] == env["GH_MERGE_DEADLINE_EPOCH"] \
        == "1500"
    env = patience.delegate_env({}, deadline_epoch=1200.0)
    assert env["GH_MERGE_DEADLINE_EPOCH"] == "1200"
    assert patience.effective_deadline(0, 1300.0, 1200.0) == 1200.0
    assert patience.effective_deadline(0, 0) == 0


def test_t11_helper_command_binds_the_earlier_of_card_and_run(tmp_path):
    store = make_store(tmp_path, [discovery("acme", "one", 1)])
    coord.start_run_clock(store, run_budget_secs=100, now=1000.0)
    task = coord.schedule(store, pr_budget_secs=600, now=1000.0)[0]
    tasking = tasking_for(store, task=task)
    _, env = proto.helper_command(tasking, "PR-001")
    assert env["GH_MERGE_DEADLINE_EPOCH"] == "1100"


def test_t11_long_ci_is_deferred_not_promised():
    plan = patience.plan_observation(expected_secs=44 * 60, now=1000.0,
                                     window_secs=600, deadline_epoch=9000.0)
    assert plan["decision"] == "defer"
    assert "exceeds" in plan["reason"]
    plan = patience.plan_observation(expected_secs=120, now=1000.0,
                                     window_secs=600, deadline_epoch=9000.0)
    assert plan == {"decision": "observe", "until": 1120.0,
                    "reason": plan["reason"]}
    plan = patience.plan_observation(expected_secs=120, now=1000.0,
                                     window_secs=600, deadline_epoch=1060.0)
    assert plan["decision"] == "defer"


def test_t11_continuation_must_name_a_real_owner():
    assert patience.continuation("none") == {"kind": "none", "ref": "",
                                             "verified_at": ""}
    with pytest.raises(ValueError):
        patience.continuation("watcher")  # no named watcher
    with pytest.raises(ValueError):
        patience.continuation("scheduled", ref="cron-17")  # unverified
    with pytest.raises(ValueError):
        patience.continuation("background")
    ok = patience.continuation("watcher", ref="bash-7",
                               verified_at="2026-09-22T12:00:00Z")
    assert ok["kind"] == "watcher"


def test_t11_expire_moves_dead_work_to_budget_exhausted(tmp_path):
    store = make_store(tmp_path, [discovery("acme", "one", 1),
                                  discovery("acme", "two", 2)])
    tasks = {t["repo_id"]: t
             for t in coord.schedule(store, pr_budget_secs=60, now=1000.0)}
    coord.apply_outcome(store, tasks["acme/one"]["attempt_id"], [
        {"card_id": "PR-001", "outcome": "ready", "reason_line": "prepared",
         "head_sha": "a" * 40,
         "evidence": [{"id": "EV-1"}]}])
    assert coord.expire(store, now=1061.0) == ["PR-001"]
    # PR-002's worker still holds the lease and its own deadline; only
    # idle cards expire here.
    assert store.cards["PR-002"].state == State.NEW
    coord.apply_outcome(store, tasks["acme/two"]["attempt_id"],
                        [hold("PR-002", "BLOCKED", "K02")])
    assert coord.expire(store, now=1062.0) == []  # BLOCKED awaits a person
    card = Store.load(store.path).cards["PR-001"]
    assert (card.state, card.reason_code) == (State.WAITING, "K14")
    assert coord.schedule(store, wake=[], now=1062.0) == []
    with pytest.raises(StoreError):
        coord.schedule(store, wake=["PR-001"], now=1062.0)


# --- T08: one participating writer per repository, accurate queue state ---

def test_t08_two_sessions_over_one_store_share_one_writer(tmp_path):
    store_a = make_store(tmp_path, [discovery("acme", "one", 1)],
                         session="S-A")
    store_b = Store.load(store_a.path, session="S-B")  # loaded before A acts
    assert len(coord.schedule(store_a)) == 1
    assert coord.schedule(store_b) == []  # the repo lock is A's


def test_t08_foreign_live_attempt_is_not_reconciled_away(tmp_path):
    store_a = make_store(tmp_path, [discovery("acme", "one", 1)],
                         session="S-A")
    (task,) = coord.schedule(store_a, now=time.time())
    store_b = Store.load(store_a.path, session="S-B")
    summary = coord.reconcile(store_b, observed={}, live_attempts=set(),
                              now=time.time(), stale_after_secs=600)
    assert summary["crashed"] == []
    assert store_b.leases.get("acme/one").holder == task["attempt_id"]
    # Silence never proves that A or its delegated writer has stopped.
    later = time.time() + 601
    summary = coord.reconcile(store_b, observed={
        "PR-001": {"merged": False}}, live_attempts=set(), now=later,
        stale_after_secs=600)
    assert summary["crashed"] == []
    assert coord.schedule(store_b, now=later) == []
    # B can recover only after explicitly verifying all of A's writers stopped.
    summary = coord.reconcile(store_b, observed={
        "PR-001": {"merged": False}}, live_attempts=set(), now=later,
        confirmed_stopped={task["attempt_id"]})
    assert summary["crashed"] == [task["attempt_id"]]
    (successor,) = coord.schedule(store_b, now=later)
    assert successor["attempt_id"] == "AGT-001.2"


def test_t08_same_session_restart_reconciles_its_own_attempts(tmp_path):
    store = make_store(tmp_path, [discovery("acme", "one", 1)],
                       session="S-A")
    coord.schedule(store)
    restarted = Store.load(store.path, session="S-A")
    summary = coord.reconcile(restarted, observed={
        "PR-001": {"merged": False}}, live_attempts=set())
    assert summary["crashed"] == ["AGT-001.1"]
    assert len(coord.schedule(restarted)) == 1


def test_t08_superseded_attempt_cannot_write(tmp_path):
    store = make_store(tmp_path, [discovery("acme", "one", 1)])
    (first,) = coord.schedule(store)
    coord.reconcile(store, observed={"PR-001": {"merged": False}},
                    live_attempts=set())
    coord.schedule(store)
    with pytest.raises(StoreError):
        coord.apply_outcome(store, first["attempt_id"], [hold("PR-001")])


def test_t08_queue_required_target_uses_the_enqueue_executor():
    assert proto.executor_for("put") == "sweep_merge.py"
    assert proto.executor_for("queue") == "pr-merge-flow enqueue"
    with pytest.raises(ValueError):
        proto.executor_for("none")


def test_t08_queued_card_is_pending_and_never_enqueued_twice(tmp_path):
    store = make_store(tmp_path, [discovery("acme", "one", 1)])
    (task,) = coord.schedule(store)
    coord.apply_outcome(store, task["attempt_id"],
                        [hold("PR-001", "WAITING", "K10")])
    assert coord.delivery_counts(store)["total"] == 0
    (woken,) = coord.schedule(store, wake=["PR-001"])
    tasking = tasking_for(store, task=woken)
    assert proto.authorize(tasking, "observe", "PR-001", now=0)[0]
    for action in ("merge", "enqueue"):
        allowed, why = proto.authorize(tasking, action, "PR-001", now=0)
        assert not allowed and "queue" in why
