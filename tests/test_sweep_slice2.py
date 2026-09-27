"""tests/test_sweep_slice2.py — Slice 2: effective policy, 5-check evaluator,
readiness fingerprint, classifier receipt, quarantine reconcile, successor
attempts, tasking protocol, helper adapter.

Acceptance mapping: T05 stale readiness invalidation, T06 lost-response
restart, T07 reviewer outage and skip distinctions, T12 evidence by
omission, plus the queue-shape negative control. Fixtures are shaped like
the GitHub REST/GraphQL responses verified on 2026-09-22.
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "plugins/repo-hygiene/skills/dependabot-sweep/scripts"
sys.path.insert(0, str(SCRIPTS))

import sweep_evaluator as ev  # noqa: E402


def section(data, status=200, truncated=False, error=""):
    """One fetched observation section, the shape every evaluator input
    uses: HTTP status (None on transport failure), payload, truncation."""
    return {"status": status, "data": data, "truncated": truncated,
            "error": error}


def protection(checks=None, contexts=None, strict=False, approvals=0,
               code_owner=False, conversation=False):
    rsc = {"strict": strict}
    if checks is not None:
        rsc["checks"] = [{"context": c, "app_id": a} for c, a in checks]
    if contexts is not None:
        rsc["contexts"] = list(contexts)
    return {
        "required_status_checks": rsc,
        "required_pull_request_reviews": {
            "required_approving_review_count": approvals,
            "require_code_owner_reviews": code_owner,
        },
        "required_conversation_resolution": {"enabled": conversation},
    }


def rule(kind, ruleset_id, **params):
    return {"type": kind, "ruleset_id": ruleset_id,
            "ruleset_source_type": "Organization", "ruleset_source": "acme",
            "parameters": params}


def ruleset(ruleset_id, enforcement="active", name="org-rules"):
    return {"id": ruleset_id, "name": name, "enforcement": enforcement,
            "source_type": "Organization", "source": "acme",
            "target": "branch"}


# --- Effective policy (gate G04: unknown requirements do not mean none) ---

def test_policy_none_when_no_protection_and_no_rules():
    policy = ev.build_policy(section(None, status=404), section([]), {})
    assert policy.known is True
    assert policy.required_checks == []
    assert policy.merge_queue is False
    assert policy.required_approvals == 0


def test_policy_unknown_when_protection_fetch_errors():
    policy = ev.build_policy(section(None, status=500), section([]), {})
    assert policy.known is False
    assert "protection" in policy.reason


def test_policy_unknown_when_rules_endpoint_unreadable():
    for bad in (section(None, status=404), section(None, status=None,
                                                    error="timeout")):
        policy = ev.build_policy(section(None, status=404), bad, {})
        assert policy.known is False
        assert "rules" in policy.reason


def test_policy_merges_protection_and_ruleset_checks_with_producers():
    prot = protection(checks=[("ci/test", 15368)], strict=True, approvals=1)
    rules = [rule("required_status_checks", 7,
                  required_status_checks=[
                      {"context": "lint", "integration_id": 15368},
                      {"context": "ci/test", "integration_id": 15368}],
                  strict_required_status_checks_policy=False),
             rule("pull_request", 7, required_approving_review_count=2,
                  dismiss_stale_reviews_on_push=True,
                  require_code_owner_review=True,
                  require_last_push_approval=False,
                  required_review_thread_resolution=True)]
    policy = ev.build_policy(section(prot), section(rules),
                             {7: section(ruleset(7))})
    assert policy.known is True
    assert sorted((c.context, c.producer_id) for c in policy.required_checks) \
        == [("ci/test", 15368), ("lint", 15368)]  # deduped across sources
    assert policy.strict is True
    assert policy.required_approvals == 2  # strictest wins
    assert policy.require_code_owner is True
    assert policy.require_thread_resolution is True
    assert "branch_protection" in policy.sources
    assert "ruleset:7" in policy.sources


def test_policy_prefers_checks_over_deprecated_contexts():
    prot = protection(checks=[("ci/test", None)], contexts=["ci/test", "old"])
    policy = ev.build_policy(section(prot), section([]), {})
    assert [c.context for c in policy.required_checks] == ["ci/test"]
    only_contexts = protection(contexts=["legacy"])
    policy = ev.build_policy(section(only_contexts), section([]), {})
    assert [(c.context, c.producer_id) for c in policy.required_checks] \
        == [("legacy", None)]


def test_policy_unknown_when_referenced_ruleset_detail_missing():
    rules = [rule("merge_queue", 9, merge_method="MERGE")]
    policy = ev.build_policy(section(None, status=404), section(rules), {})
    assert policy.known is False
    assert "ruleset 9" in policy.reason


def test_policy_skips_evaluate_only_ruleset():
    rules = [rule("merge_queue", 9, merge_method="MERGE")]
    policy = ev.build_policy(section(None, status=404), section(rules),
                             {9: section(ruleset(9, enforcement="evaluate"))})
    assert policy.known is True
    assert policy.merge_queue is False


def test_policy_detects_merge_queue_and_signatures():
    rules = [rule("merge_queue", 9, merge_method="SQUASH",
                  grouping_strategy="ALLGREEN"),
             rule("required_signatures", 9)]
    policy = ev.build_policy(section(None, status=404), section(rules),
                             {9: section(ruleset(9))})
    assert policy.merge_queue is True
    assert policy.merge_queue_method == "SQUASH"
    assert policy.required_signatures is True


def test_policy_fingerprint_is_fieldwise():
    base = ev.build_policy(section(protection(checks=[("ci", 1)])),
                           section([]), {})
    changed = ev.build_policy(section(protection(checks=[("ci", 1),
                                                          ("lint", 1)])),
                              section([]), {})
    diff = ev.diff_fingerprints(base.fingerprint(), changed.fingerprint())
    assert diff == ["required_checks"]


# --- Evaluator fixtures: one full observation of a clean, green PR ---

import sweep_coordinator as coord  # noqa: E402
from sweep_core import State, Store  # noqa: E402

HEAD = "a" * 40
BASE = "b" * 40
CI_APP = 15368
NOW = 1_800_000_000.0


def pull(**over):
    data = {"state": "open", "draft": False, "merged": False,
            "mergeable": True, "mergeable_state": "clean",
            "merged_at": None, "merge_commit_sha": "c" * 40,
            "auto_merge": None,
            "head": {"sha": HEAD, "ref": "dependabot/pip/requests-2.32.5"},
            "base": {"sha": BASE, "ref": "main"}}
    data.update(over)
    return data


def files():
    return [{"filename": "pyproject.toml", "sha": "f1" * 20,
             "status": "modified", "changes": 2},
            {"filename": "uv.lock", "sha": "f2" * 20, "status": "modified",
             "changes": 12}]


def run(name, conclusion="success", status="completed", app_id=CI_APP,
        suite=1, run_id=1, completed_at="2026-09-22T00:10:00Z"):
    return {"id": run_id, "name": name, "status": status,
            "conclusion": conclusion, "head_sha": HEAD,
            "app": {"id": app_id, "slug": "github-actions"},
            "check_suite": {"id": suite}, "completed_at": completed_at,
            "details_url": f"https://example.test/runs/{run_id}"}


def check_runs(*runs, total=None):
    runs = list(runs)
    return {"total_count": len(runs) if total is None else total,
            "check_runs": runs}


def status(context, state, description="", login="ci-bot"):
    return {"context": context, "state": state, "description": description,
            "creator": {"login": login}, "target_url": "https://x.test"}


def combined(*statuses):
    state = ("failure" if any(s["state"] in ("failure", "error")
                              for s in statuses)
             else "pending" if not statuses or any(
                 s["state"] == "pending" for s in statuses) else "success")
    return {"state": state, "statuses": list(statuses),
            "total_count": len(statuses), "sha": HEAD}


def thread(thread_id, resolved):
    return {"id": thread_id, "isResolved": resolved, "isOutdated": False}


def review(login, state, at, user_type="User"):
    return {"user": {"login": login, "type": user_type}, "state": state,
            "submitted_at": at, "commit_id": HEAD}


def queue(in_queue=False, entry_state=None, auto_merge=False):
    entry = {"state": entry_state} if entry_state else None
    return {"isInMergeQueue": in_queue, "mergeQueueEntry": entry,
            "autoMergeRequest": {"enabledAt": "x"} if auto_merge else None}


def clean_policy(**over):
    prot = protection(checks=[("ci/test", CI_APP)], strict=False)
    kwargs = {"protection": section(prot), "branch_rules": section([]),
              "rulesets": {}}
    kwargs.update(over)
    return ev.build_policy(**kwargs)


def observe(**over):
    parts = {
        "head_sha": HEAD, "observed_at": "2026-09-22T00:11:00Z",
        "pull": section(pull()), "files": section(files()),
        "reviews": section([]), "threads": section([]),
        "check_runs": section(check_runs(run("ci/test"))),
        "check_suites": section({1: {"conclusion": "success"}}),
        "statuses": section(combined()),
        "queue": section(queue()),
        "policy": clean_policy(),
    }
    parts.update(over)
    return ev.Observation(**parts)


def receipt(head=HEAD, file_list=None, dependency_only=True):
    return ev.ClassifierReceipt.for_files(
        head, files() if file_list is None else file_list,
        dependency_only=dependency_only, classifier="test-classifier",
        at="2026-09-22T00:09:00Z")


def authority(mode="automated", **over):
    fields = {"mode": mode, "repairs": frozenset({"branch_update"}),
              "owner_hold": False, "approved": False,
              "deadline_epoch": NOW + 600}
    fields.update(over)
    return ev.Authority(**fields)


def tracking(**over):
    fields = {"lease_held": True, "repo_quarantined": False}
    fields.update(over)
    return ev.Tracking(**fields)


def evaluate(obs=None, rec=None, auth=None, track=None, **kw):
    return ev.evaluate(obs or observe(), rec or receipt(),
                       auth or authority(), track or tracking(),
                       now=NOW, **kw)


# --- Happy path and the outcome bridge into Slice 1 ---

def test_evaluator_ready_on_clean_green_pr():
    result = evaluate()
    assert result.state == State.READY
    assert result.merge_path == "put"
    assert [c.name for c in result.checks] == [
        "identity", "tracked", "green", "allowed"]
    assert all(c.passed for c in result.checks)
    assert result.evidence  # every check leaves evidence


def test_evaluation_outcome_record_applies_through_coordinator(tmp_path):
    store = Store(str(tmp_path / "run.jsonl"))
    coord.create_run(store, "RUN-S2", "automated", "auth", [
        {"org": "acme", "repo": "r", "number": 1, "title": "bump requests",
         "url": "u", "owner": "acme", "head_sha": HEAD}])
    attempt = coord.schedule(store)[0]["attempt_id"]
    coord.apply_outcome(store, attempt, [evaluate().to_outcome("PR-001")])
    assert store.cards["PR-001"].state == State.READY
    stale = evaluate(observe(check_runs=section(check_runs(
        run("ci/test", status="in_progress", conclusion=None)))))
    outcome = stale.to_outcome("PR-001")
    assert outcome["outcome"] == "hold" and outcome["state"] == "WAITING"
    assert outcome["reason_code"] == "K01"


# --- T12: evidence by omission never passes ---

def test_receipt_head_mismatch_is_evidence_incomplete():
    result = evaluate(rec=receipt(head="0" * 40))
    assert result.state == State.BLOCKED and result.reason_code == "K13"
    assert "receipt" in result.reason_line and "head" in result.reason_line


def test_receipt_files_digest_mismatch_is_evidence_incomplete():
    changed = files() + [{"filename": "src/app.py", "sha": "f3" * 20,
                          "status": "modified", "changes": 40}]
    result = evaluate(observe(files=section(changed)))
    assert result.state == State.BLOCKED and result.reason_code == "K13"
    assert "files" in result.reason_line


def test_truncated_or_unreadable_sections_cannot_pass():
    cases = {
        "check_runs": section(check_runs(run("ci/test")), truncated=True),
        "threads": section(None, status=None, error="timeout"),
        "reviews": section([], truncated=True),
        "files": section(None, status=502),
    }
    for name, bad in cases.items():
        result = evaluate(observe(**{name: bad}))
        assert result.state != State.READY, name
        assert result.reason_code == "K13", name
        assert name in result.reason_line, name


def test_missing_required_check_is_pending_not_passing():
    result = evaluate(observe(check_runs=section(check_runs())))
    assert result.state == State.WAITING and result.reason_code == "K01"
    assert "ci/test" in result.reason_line


def test_required_check_needs_matching_producer():
    impostor = run("ci/test", app_id=999)
    result = evaluate(observe(check_runs=section(check_runs(impostor))))
    assert result.state == State.WAITING and result.reason_code == "K01"
    assert "producer" in result.reason_line


def test_unknown_policy_blocks_with_policy_code():
    unknown = ev.build_policy(section(None, status=403), section([]), {})
    result = evaluate(observe(policy=unknown))
    assert result.state == State.BLOCKED and result.reason_code == "K09"


def test_unsupported_triviality_routes_to_involved_preparation():
    result = evaluate(rec=receipt(dependency_only=False))
    assert result.state == State.BLOCKED and result.reason_code == "K09"
    assert result.action_owner == "pr-merge-flow"


# --- Green: reruns, failures, reviews ---

def test_latest_rerun_per_check_name_wins():
    runs = check_runs(
        run("ci/test", conclusion="failure", run_id=1,
            completed_at="2026-09-22T00:01:00Z"),
        run("ci/test", conclusion="success", run_id=2,
            completed_at="2026-09-22T00:10:00Z"))
    assert evaluate(observe(check_runs=section(runs))).state == State.READY


def test_failed_applicable_check_is_red_with_low_confidence():
    runs = check_runs(run("ci/test"), run("lint", conclusion="failure",
                                          run_id=2))
    result = evaluate(observe(check_runs=section(runs)))
    assert result.state == State.BLOCKED and result.reason_code == "K04"
    assert result.confidence == "low" and "lint" in result.reason_line


def test_not_green_conclusions_never_pass():
    for conclusion in ("cancelled", "timed_out", "action_required", "stale",
                       "startup_failure"):
        runs = check_runs(run("ci/test", conclusion=conclusion))
        result = evaluate(observe(check_runs=section(runs)))
        assert result.state != State.READY, conclusion


def test_changes_requested_and_unresolved_threads_hold_for_review():
    reviews = [review("alice", "CHANGES_REQUESTED", "2026-09-22T00:05:00Z")]
    result = evaluate(observe(reviews=section(reviews)))
    assert result.state == State.BLOCKED and result.reason_code == "K07"
    result = evaluate(observe(threads=section([thread("T1", False)])))
    assert result.state == State.BLOCKED and result.reason_code == "K07"
    assert "T1" in result.reason_line


def test_required_approvals_count_latest_state_per_reviewer():
    policy = clean_policy(protection=section(
        protection(checks=[("ci/test", CI_APP)], approvals=1)))
    dismissed = [review("alice", "APPROVED", "2026-09-22T00:01:00Z"),
                 review("alice", "DISMISSED", "2026-09-22T00:02:00Z")]
    result = evaluate(observe(policy=policy, reviews=section(dismissed)))
    assert result.state == State.BLOCKED and result.reason_code == "K07"
    assert "1 approving" in result.reason_line
    # A later COMMENTED review does not withdraw an approval on GitHub.
    commented = [review("alice", "APPROVED", "2026-09-22T00:01:00Z"),
                 review("alice", "COMMENTED", "2026-09-22T00:02:00Z")]
    assert evaluate(observe(policy=policy,
                            reviews=section(commented))).state == State.READY
    nobody = evaluate(observe(policy=policy, reviews=section([])))
    assert nobody.state == State.BLOCKED and nobody.reason_code == "K07"


# --- T07: reviewer outage and skip distinctions ---

def test_reviewer_unavailable_required_vs_optional():
    outage = combined(status("coderabbitai", "failure",
                             "Review rate limited", login="coderabbitai"))
    required = clean_policy(protection=section(protection(
        checks=[("ci/test", CI_APP), ("coderabbitai", None)])))
    blocked = evaluate(observe(policy=required, statuses=section(outage)),
                       reviewer_contexts={"coderabbitai"})
    assert blocked.state == State.BLOCKED and blocked.reason_code == "K08"
    assert blocked.action_owner == "service owner"
    disclosed = evaluate(observe(statuses=section(outage)),
                         reviewer_contexts={"coderabbitai"})
    assert disclosed.state == State.READY
    assert any("coderabbitai" in note for note in disclosed.notes)


def test_description_only_outage_holds_and_is_never_ci_red():
    """A rate-limit wording on an unconfigured context proves nothing about
    who produced it: hold as a low-confidence reviewer outage, never READY
    (a "Docker Hub rate limit" build failure must not pass) and never K04."""
    outage = combined(status("some-reviewer", "failure", "Review quota exceeded"))
    result = evaluate(observe(statuses=section(outage)))
    assert result.state == State.BLOCKED and result.reason_code == "K08"
    assert result.confidence == "low"
    assert "some-reviewer" in result.reason_line
    assert "configure" in result.action.lower()


def test_legitimate_skip_vs_failed_prerequisite_skip():
    policy = clean_policy(protection=section(protection(
        checks=[("ci/test", CI_APP), ("deploy", CI_APP)])))
    legit = check_runs(run("ci/test"), run("deploy", conclusion="skipped",
                                            run_id=2))
    assert evaluate(observe(policy=policy,
                            check_runs=section(legit))).state == State.READY
    prereq = check_runs(run("ci/test"), run("deploy", conclusion="skipped",
                                             run_id=2, suite=2))
    suites = section({1: {"conclusion": "success"},
                      2: {"conclusion": "failure"}})
    result = evaluate(observe(policy=policy, check_runs=section(prereq),
                              check_suites=suites))
    assert result.state == State.BLOCKED and result.reason_code == "K04"
    assert "prerequisite" in result.reason_line


def test_green_evidence_counts_legitimate_skips_separately():
    checks = check_runs(run("ci/test"),
                        run("deploy", conclusion="skipped", run_id=2))
    result = evaluate(observe(check_runs=section(checks)))
    assert result.state == State.READY
    green = next(e for e in result.evidence if e["id"].startswith("EV-green-"))
    assert green["establishes"].split(";", 1)[0] == (
        "1 check(s) green, 1 legitimately skipped")


# --- Mergeability and queue (negative control) ---

def test_mergeability_states_map_distinctly():
    cases = {
        (None, "unknown"): (State.WAITING, "K13"),
        (False, "dirty"): (State.BLOCKED, "K02"),
        (True, "behind"): (State.BLOCKED, "K02"),
        (True, "blocked"): (State.BLOCKED, "K09"),
        (True, "has_hooks"): (State.BLOCKED, "K09"),
        (True, "unstable"): (State.WAITING, "K01"),
    }
    for (mergeable, ms), (state, code) in cases.items():
        result = evaluate(observe(pull=section(pull(
            mergeable=mergeable, mergeable_state=ms))))
        assert (result.state, result.reason_code) == (state, code), ms


def test_queue_acceptance_is_pending_never_merged():
    for entry in ("QUEUED", "AWAITING_CHECKS", "MERGEABLE", "UNMERGEABLE",
                  "LOCKED"):
        result = evaluate(observe(queue=section(queue(True, entry))))
        assert result.state == State.WAITING and result.reason_code == "K10"
        assert entry in result.reason_line
    armed = evaluate(observe(queue=section(queue(auto_merge=True))))
    assert armed.state == State.WAITING and armed.reason_code == "K10"
    queued_policy = clean_policy(branch_rules=section(
        [rule("merge_queue", 9, merge_method="MERGE")]),
        rulesets={9: section(ruleset(9))})
    result = evaluate(observe(policy=queued_policy))
    assert result.state == State.READY and result.merge_path == "queue"


def test_verify_merged_requires_fresh_complete_evidence():
    merged = pull(state="closed", merged=True, merged_at="2026-09-22T00:20:00Z",
                  merge_commit_sha="d" * 40)
    assert ev.verify_merged(section(merged)) == {
        "merged": True, "commit": "d" * 40, "at": "2026-09-22T00:20:00Z"}
    assert ev.verify_merged(section(pull())) == {"merged": False}
    assert ev.verify_merged(section(pull(merged=True))) is None  # no at
    assert ev.verify_merged(section(None, status=None, error="x")) is None


def test_closed_or_merged_pull_resolves_by_observation():
    merged = pull(state="closed", merged=True, merged_at="2026-09-22T00:20:00Z",
                  merge_commit_sha="d" * 40)
    result = evaluate(observe(pull=section(merged)))
    assert result.to_outcome("PR-001") == {
        "card_id": "PR-001", "outcome": "merged", "commit_sha": "d" * 40,
        "merged_at": "2026-09-22T00:20:00Z"}
    closed = evaluate(observe(pull=section(pull(state="closed"))))
    assert closed.to_outcome("PR-001")["outcome"] == "closed"


# --- Allowed? modes, holds, budget, tracking ---

def test_inspect_mode_prepares_without_merge_path():
    result = evaluate(auth=authority(mode="inspect"))
    assert result.state == State.READY and result.merge_path == "none"


def test_gated_mode_needs_owner_with_decision_block():
    result = evaluate(auth=authority(mode="gated"))
    assert result.state == State.NEEDS_OWNER and result.reason_code == "K16"
    outcome = result.to_outcome("PR-001")
    for key in ("why", "approve_effect", "decline_effect", "recommendation"):
        assert outcome["decision"][key]
    approved = evaluate(auth=authority(mode="gated", approved=True))
    assert approved.state == State.READY and approved.merge_path == "put"


def test_owner_hold_and_budget_wait():
    held = evaluate(auth=authority(owner_hold=True))
    assert held.state == State.WAITING and held.reason_code == "K16"
    spent = evaluate(auth=authority(deadline_epoch=NOW - 1))
    assert spent.state == State.WAITING and spent.reason_code == "K14"


def test_tracking_failures_block_before_green():
    quarantined = evaluate(track=tracking(repo_quarantined=True))
    assert quarantined.state == State.BLOCKED
    assert quarantined.reason_code == "K11"
    no_lease = evaluate(track=tracking(lease_held=False))
    assert no_lease.state == State.BLOCKED and no_lease.reason_code == "K12"


# --- T05: stale readiness is invalidated, and the cause is named ---

def test_readiness_invalidated_by_each_kind_of_change():
    ready = evaluate()
    assert ev.stale_reasons(ready, observe()) == []
    flipped = observe(check_runs=section(check_runs(
        run("ci/test", conclusion="failure"))))
    assert "check_states" in ev.stale_reasons(ready, flipped)
    ready_with_thread = evaluate(observe(threads=section([thread("T1", True)])))
    reopened = observe(threads=section([thread("T1", True),
                                        thread("T2", False)]))
    assert "unresolved_threads" in ev.stale_reasons(ready_with_thread, reopened)
    moved = observe(head_sha="e" * 40,
                    pull=section(pull(head={"sha": "e" * 40, "ref": "x"})))
    assert "head_sha" in ev.stale_reasons(ready, moved)
    rebased = observe(pull=section(pull(base={"sha": "9" * 40,
                                              "ref": "main"})))
    assert "base_sha" in ev.stale_reasons(ready, rebased)
    tightened = observe(policy=clean_policy(protection=section(protection(
        checks=[("ci/test", CI_APP), ("lint", CI_APP)]))))
    assert "policy" in ev.stale_reasons(ready, tightened)


# --- Coordinator recovery: T06, quarantine resolution (P8), successors ---

from sweep_core import StoreError  # noqa: E402


def two_card_run(tmp_path, run_id="RUN-T06"):
    store = Store(str(tmp_path / "run.jsonl"), session="slice2-coordinator")
    coord.create_run(store, run_id, "automated", "auth", [
        {"org": "acme", "repo": "r", "number": n, "title": f"bump {n}",
         "url": "u", "owner": "acme", "head_sha": f"{n:040x}"} for n in (1, 2)])
    return store


def merged_obs(commit="c" * 40, at="2026-09-22T00:20:00Z"):
    return {"merged": True, "commit": commit, "at": at}


def test_t06_lost_response_restart_retains_hold_then_reconciles(tmp_path):
    store = two_card_run(tmp_path)
    tasking = coord.schedule(store, model="sol", pr_budget_secs=600,
                             now=1000.0)[0]
    coord.apply_outcome(store, tasking["attempt_id"], [
        {"card_id": "PR-001", "outcome": "unknown",
         "op_note": "merge PUT accepted by transport; response lost"}])
    # Restart: only the JSONL survives.
    store = Store.load(str(tmp_path / "run.jsonl"), session="slice2-coordinator")
    assert store.leases.get("acme/r").state == "quarantined"
    assert coord.schedule(store) == []  # the hold survives the restart
    try:
        coord.apply_outcome(store, tasking["attempt_id"], [
            {"card_id": "PR-002", "outcome": "merged", "commit_sha": "d" * 40,
             "merged_at": "2026-09-22T00:21:00Z"}])
    except StoreError as exc:
        assert "quarantined" in str(exc)
    else:
        raise AssertionError("no merge claim may land on a quarantined repo")
    summary = coord.reconcile(store, {"PR-001": merged_obs()}, set())
    assert store.cards["PR-001"].state == State.MERGED
    assert store.cards["PR-001"].merge_commit == "c" * 40
    assert summary["merged"] == ["PR-001"]
    assert summary["resolved"] == ["acme/r"]
    assert store.leases.get("acme/r").state == "released"
    dead = store.diary[tasking["attempt_id"]]
    assert dead.result == "crashed" and dead.outstanding == ["PR-002"]
    retry = coord.schedule(store, model="terra", now=1500.0)
    assert retry == [{"attempt_id": "AGT-001.2", "repo_id": "acme/r",
                      "card_ids": ["PR-002"]}]
    assert store.diary["AGT-001.1"].successor == "AGT-001.2"
    assert store.cards["PR-002"].deadline_epoch == 1600.0  # not reset


def test_reconcile_ambiguous_merged_observation_keeps_quarantine(tmp_path):
    store = two_card_run(tmp_path)
    attempt = coord.schedule(store)[0]["attempt_id"]
    coord.apply_outcome(store, attempt, [
        {"card_id": "PR-001", "outcome": "unknown", "op_note": "lost"},
        {"card_id": "PR-002", "outcome": "unknown", "op_note": "lost too"}])
    summary = coord.reconcile(store, {
        "PR-001": {"merged": True},  # no commit, no timestamp: ambiguous
        "PR-002": merged_obs("e" * 40, "2026-09-22T00:22:00Z"),
    }, set())
    assert store.cards["PR-001"].state == State.UNKNOWN
    assert store.cards["PR-002"].state == State.MERGED  # siblings still settle
    assert summary["quarantined"] == ["PR-001"]
    assert summary["resolved"] == []
    assert store.leases.get("acme/r").state == "quarantined"


def test_reconcile_restores_unknown_card_observed_unmerged(tmp_path):
    store = two_card_run(tmp_path)
    attempt = coord.schedule(store)[0]["attempt_id"]
    coord.apply_outcome(store, attempt, [
        {"card_id": "PR-001", "outcome": "unknown", "op_note": "lost"},
        {"card_id": "PR-002", "outcome": "merged", "commit_sha": "d" * 40,
         "merged_at": "2026-09-22T00:21:00Z"}])
    summary = coord.reconcile(store, {"PR-001": {"merged": False}}, set())
    assert store.cards["PR-001"].state == State.NEW
    assert summary["rescheduled"] == ["PR-001"]
    assert summary["resolved"] == ["acme/r"]
    assert store.leases.get("acme/r").state == "free"
    assert coord.schedule(store)[0]["card_ids"] == ["PR-001"]


def test_successor_chain_and_replay_uniqueness(tmp_path):
    store = two_card_run(tmp_path)
    first = coord.schedule(store, pr_budget_secs=600, now=1000.0)[0]
    coord.reconcile(store, {"PR-001": {"merged": False},
                            "PR-002": {"merged": False}}, set())
    second = coord.schedule(store, now=1100.0)[0]
    coord.reconcile(store, {"PR-001": {"merged": False},
                            "PR-002": {"merged": False}}, set())
    third = coord.schedule(store, now=1200.0)[0]
    assert (first["attempt_id"], second["attempt_id"], third["attempt_id"]) \
        == ("AGT-001.1", "AGT-001.2", "AGT-001.3")
    assert store.diary["AGT-001.2"].successor == "AGT-001.3"
    assert store.cards["PR-001"].deadline_epoch == 1600.0
    replayed = Store.load(str(tmp_path / "run.jsonl"))
    assert replayed.ids.attempt_id() == "AGT-002.1"
    assert replayed.cards["PR-001"].deadline_epoch == 1600.0


def test_ready_cards_are_rescheduled_for_merge(tmp_path):
    store = two_card_run(tmp_path)
    attempt = coord.schedule(store)[0]["attempt_id"]
    coord.apply_outcome(store, attempt, [
        {"card_id": "PR-001", "outcome": "ready", "reason_line": "inspect",
         "head_sha": "a" * 40,
         "evidence": [{"id": "EV-1"}]},
        {"card_id": "PR-002", "outcome": "merged", "commit_sha": "d" * 40,
         "merged_at": "2026-09-22T00:21:00Z"}])
    assert coord.schedule(store)[0]["card_ids"] == ["PR-001"]


# --- P12: who records supersession ---

def test_worker_closed_after_coordinator_supersession_is_idempotent(tmp_path):
    store = two_card_run(tmp_path)
    attempt = coord.schedule(store)[0]["attempt_id"]
    replacement = coord.register_replacement(store, "PR-001", {
        "org": "acme", "repo": "r", "number": 3, "title": "redo"})
    coord.apply_outcome(store, attempt, [
        {"card_id": "PR-001", "outcome": "closed",
         "reason": "superseded by #3", "replaced_by": replacement.id},
        {"card_id": "PR-002", "outcome": "merged", "commit_sha": "d" * 40,
         "merged_at": "2026-09-22T00:21:00Z"}])
    assert store.cards["PR-001"].state == State.CLOSED
    assert store.cards["PR-001"].replaced_by == replacement.id
    assert store.diary[attempt].result == "completed"


def test_worker_closed_with_conflicting_link_is_refused(tmp_path):
    store = two_card_run(tmp_path)
    attempt = coord.schedule(store)[0]["attempt_id"]
    coord.register_replacement(store, "PR-001", {
        "org": "acme", "repo": "r", "number": 3, "title": "redo"})
    try:
        coord.apply_outcome(store, attempt, [
            {"card_id": "PR-001", "outcome": "closed", "reason": "x",
             "replaced_by": "PR-999"}])
    except StoreError as exc:
        assert "PR-999" in str(exc)
    else:
        raise AssertionError("conflicting supersession link must be refused")


def test_coordinator_links_replacement_after_worker_closed(tmp_path):
    store = two_card_run(tmp_path)
    attempt = coord.schedule(store)[0]["attempt_id"]
    coord.apply_outcome(store, attempt, [
        {"card_id": "PR-001", "outcome": "closed",
         "reason": "Dependabot: superseded by #3"}])
    replacement = coord.register_replacement(store, "PR-001", {
        "org": "acme", "repo": "r", "number": 3, "title": "redo"})
    assert store.cards["PR-001"].state == State.CLOSED
    assert store.cards["PR-001"].replaced_by == replacement.id
    assert replacement.replaces == "PR-001"


# --- Handoff protocol: tasking record, brief, helper adapter ---

import sweep_protocol as proto  # noqa: E402

HELPER_SRC = (SCRIPTS / "gh_merge.py").read_text()
TEMPLATE = SCRIPTS.parent / "templates" / "agent-brief.md"


def tasked_store(tmp_path, mode="automated"):
    store = two_card_run(tmp_path, run_id="RUN-PROTO")
    tasking = coord.schedule(store, model="sol", pr_budget_secs=600,
                             now=1000.0)[0]
    return store, tasking


def test_tasking_carries_authority_lease_and_deadlines(tmp_path):
    store, record = tasked_store(tmp_path)
    tasking = proto.Tasking.from_store(
        store, record, mode="automated", repairs={"branch_update", "lockfile"},
        op_timeout_secs=30, progress_log="/tmp/x.log",
        helper_path="scripts/gh_merge.py", holds=["PR-002"])
    assert tasking.attempt_id == record["attempt_id"] == tasking.lease_holder
    assert tasking.repo_id == "acme/r" and tasking.card_ids == ["PR-001",
                                                                "PR-002"]
    assert tasking.deadlines == {"PR-001": 1600.0, "PR-002": 1600.0}
    assert tasking.merge_allowed is True and tasking.holds == ["PR-002"]
    assert tasking.repairs == ["branch_update", "lockfile"]
    assert tasking.cards[0]["human_id"] == 'acme/r#1 "bump 1"'
    replayed = proto.Tasking.from_dict(tasking.to_dict())
    assert replayed == tasking


def test_tasking_refuses_repo_settings_repair(tmp_path):
    store, record = tasked_store(tmp_path)
    try:
        proto.Tasking.from_store(store, record, mode="automated",
                                 repairs={"repo_settings"}, op_timeout_secs=30,
                                 progress_log="l", helper_path="h")
    except ValueError as exc:
        assert "repo_settings" in str(exc)
    else:
        raise AssertionError("repository settings are never a worker repair")


def test_tasking_mode_semantics(tmp_path):
    store, record = tasked_store(tmp_path)
    make = lambda mode, **kw: proto.Tasking.from_store(  # noqa: E731
        store, record, mode=mode, repairs={"branch_update"},
        op_timeout_secs=30, progress_log="l", helper_path="h", **kw)
    inspect = make("inspect")
    assert inspect.merge_allowed is False and inspect.repairs == []
    automated = make("automated")
    assert automated.merge_allowed is True and automated.approved == []
    gated = make("gated", approved=["PR-001"])
    assert gated.merge_allowed is True and gated.approved == ["PR-001"]
    try:
        make("yolo")
    except ValueError:
        pass
    else:
        raise AssertionError("unknown mode must be refused")


def test_brief_renders_from_template_without_placeholders(tmp_path):
    store, record = tasked_store(tmp_path)
    store.cards["PR-001"].head_sha = HEAD
    tasking = proto.Tasking.from_store(
        store, record, mode="gated", repairs={"branch_update"},
        op_timeout_secs=30, progress_log="/tmp/sweep.log",
        helper_path="/opt/h/gh_merge.py", approved=["PR-001"],
        holds=["PR-002"])
    brief = proto.render_brief(tasking, template_path=TEMPLATE)
    assert not proto.PLACEHOLDER.search(brief)
    assert record["attempt_id"] in brief
    assert 'acme/r#1 "bump 1" [PR-001]' in brief
    assert "GH_MERGE_DEADLINE_EPOCH=1600" in brief
    assert "mode: gated" in brief and "approved: PR-001" in brief
    assert "owner hold: PR-002" in brief
    assert "single executor" in brief.lower() or "one executor" in brief.lower()
    assert "transport" in brief.lower()
    assert "outcome record" in brief.lower()
    assert "never" in brief and "gh pr merge" in brief
    assert str(SCRIPTS / "sweep_merge.py") in brief
    assert f"head {HEAD}" in brief
    assert "--expected-head <approved-head> --helper-path /opt/h/gh_merge.py" in brief
    assert "Never substitute a newly fetched head" in brief


def test_helper_command_binds_card_deadline_and_timeout(tmp_path):
    store, record = tasked_store(tmp_path)
    store.cards["PR-002"].head_sha = HEAD
    tasking = proto.Tasking.from_store(
        store, record, mode="automated", repairs=set(), op_timeout_secs=45,
        progress_log="/tmp/sweep.log", helper_path="/opt/h/gh_merge.py")
    argv, env = proto.helper_command(tasking, "PR-002")
    assert argv == ["python3", str(SCRIPTS / "sweep_merge.py"),
                    "--expected-head", HEAD, "--helper-path", "/opt/h/gh_merge.py",
                    "--", "acme", "r", "2", "merge", "/tmp/sweep.log",
                    "--assert-trivial"]
    assert env == {"GH_MERGE_OP_TIMEOUT": "45",
                   "GH_MERGE_DEADLINE_EPOCH": "1600", "GH_PROMPT_DISABLED": "1"}


def test_helper_exit_zero_requires_verification_not_a_merged_record():
    step = proto.helper_outcome(0, "MERGED: acme/r#1 at abcdef123456\n")
    assert step["next"] == "verify"
    assert "outcome" not in step  # never a merged record without a fresh GET
    step = proto.helper_outcome(0, "RECONCILED: merge confirmed applied\n")
    assert step["next"] == "verify"


def test_helper_deferred_reasons_map_to_codes():
    cases = {
        "DEFERRED: checks pending": ("K01", "WAITING"),
        "DEFERRED: required checks not green: ['ci']": ("K01", "WAITING"),
        "DEFERRED: failing checks: ['lint']": ("K04", "BLOCKED"),
        "DEFERRED: not mergeable: state=dirty": ("K02", "BLOCKED"),
        "DEFERRED: not mergeable: state=blocked": ("K09", "BLOCKED"),
        "DEFERRED: change requests outstanding: ['a']": ("K07", "BLOCKED"),
        "DEFERRED: unresolved review threads": ("K07", "BLOCKED"),
        "DEFERRED: inline review comments need human reading": ("K07", "BLOCKED"),
        "DEFERRED: triviality not asserted by classifier": ("K13", "BLOCKED"),
        "DEFERRED: diff too large to verify (page cap)": ("K13", "BLOCKED"),
        "DEFERRED: check-run state unreadable": ("K13", "BLOCKED"),
        "DEFERRED: head changed during preflight": ("K13", "WAITING"),
        "DEFERRED: per-PR budget exceeded at preflight/checks": ("K14", "WAITING"),
        "DEFERRED (transport, safe: nothing submitted): GET /x transport failure: timed out":
            ("K17", "WAITING"),
        "DEFERRED: credential acquisition failed: no token": ("K12", "BLOCKED"),
        "DEFERRED: PR is a draft": ("K09", "BLOCKED"),
        "DEFERRED: something nobody anticipated": ("K13", "BLOCKED"),
    }
    for line, (code, state) in cases.items():
        step = proto.helper_outcome(10, line + "\n")
        assert step["next"] == "hold", line
        assert (step["reason_code"], step["state"]) == (code, state), line
        reason = step["reason_line"].removeprefix("helper deferred: ")
        assert line.endswith(reason) and reason, line


def test_helper_queue_refusal_records_wrong_executor_disagreement():
    refusal = "merge queue required: unsupported path"
    assert f'DefinitiveFailure("{refusal}")' in HELPER_SRC
    ready = evaluate()
    assert ready.state == State.READY and ready.merge_path == "put"

    step = proto.helper_outcome(10, f"DEFERRED: {refusal}\n")
    assert step["next"] == "hold"
    assert (step["reason_code"], step["state"]) == ("K12", "BLOCKED")
    assert step["reason_line"].startswith(f"helper deferred: {refusal}")
    assert "helper/evaluator disagreement" in step["reason_line"]
    assert "wrong executor" in step["reason_line"]
    assert "fresh policy re-evaluation" in step["reason_line"]
    assert "merge_path" not in step  # the refusal cannot choose a new executor


def test_wrapper_changed_approved_head_holds_for_fresh_classification():
    step = proto.helper_outcome(
        10, "DEFERRED: head changed since classification or approval")
    assert (step["next"], step["reason_code"], step["state"]) == (
        "hold", "K13", "WAITING")


def test_helper_queue_refusal_replays_and_requires_fresh_executor_choice(tmp_path):
    store = Store(str(tmp_path / "run.jsonl"))
    coord.create_run(store, "RUN-REFUSAL", "automated", "auth", [
        {"org": "acme", "repo": "r", "number": 1, "title": "bump requests",
         "url": "u", "owner": "acme", "head_sha": HEAD}])
    ready = evaluate()
    first = coord.schedule(store, pr_budget_secs=600, now=NOW)[0]
    coord.apply_outcome(store, first["attempt_id"], [
        ready.to_outcome("PR-001")])

    merge_attempt = coord.schedule(store, now=NOW)[0]
    refusal = "DEFERRED: merge queue required: unsupported path"
    step = proto.helper_outcome(10, refusal)
    coord.apply_outcome(store, merge_attempt["attempt_id"], [{
        "card_id": "PR-001", "outcome": step["next"],
        "state": step["state"], "reason_code": step["reason_code"],
        "reason_line": step["reason_line"], "severity": "medium",
        "confidence": "high", "evidence": ready.evidence + [{
            "id": "EV-HELPER", "what": refusal,
            "establishes": "helper refused before submitting a merge"}],
        "action": "Refresh policy and re-evaluate before choosing an executor.",
        "action_owner": "sweeper", "resume_trigger": "fresh policy observation",
    }])

    store = Store.load(store.path)
    card = store.cards["PR-001"]
    assert (card.state, card.reason_code) == (State.BLOCKED, "K12")
    assert "helper/evaluator disagreement" in card.reason_line
    assert coord.schedule(store, now=NOW + 1) == []
    woken = coord.schedule(store, wake=[card.id], now=NOW + 1)[0]
    tasking = proto.Tasking.from_store(
        store, woken, mode="automated", repairs=set(), op_timeout_secs=30,
        progress_log="l", helper_path="h")
    assert proto.authorize(tasking, "observe", card.id, now=NOW + 1)[0]
    # Authority and readiness are separate. A refusal cannot fabricate the
    # duplicate-enqueue prohibition reserved for an observed queued PR.
    for action in ("merge", "enqueue"):
        allowed, why = proto.authorize(tasking, action, card.id, now=NOW + 1)
        assert allowed, why
        assert "already in the merge queue" not in why

    policy = clean_policy(branch_rules=section(
        [rule("merge_queue", 9, merge_method="MERGE")]),
        rulesets={9: section(ruleset(9))})
    refreshed = evaluate(observe(policy=policy))
    assert refreshed.state == State.READY and refreshed.merge_path == "queue"
    assert proto.executor_for(refreshed.merge_path) == "pr-merge-flow enqueue"
    coord.apply_outcome(store, woken["attempt_id"], [
        refreshed.to_outcome(card.id)])
    enqueue_attempt = coord.schedule(store, now=NOW + 2)[0]
    tasking = proto.Tasking.from_store(
        store, enqueue_attempt, mode="automated", repairs=set(),
        op_timeout_secs=30, progress_log="l", helper_path="h")
    assert proto.authorize(tasking, "enqueue", card.id, now=NOW + 2)[0]


def test_helper_closed_pr_and_unknown_and_refusal():
    for line in ("DEFERRED: PR is not open", "DEFERRED: PR closed during preflight"):
        assert proto.helper_outcome(10, line)["next"] == "verify"
    unknown = proto.helper_outcome(
        11, "UNKNOWN after PUT (PUT /x transport failure: reset); "
            "reconciling read-only...\nUNKNOWN: hold the repo mutation slot; "
            "human must reconcile; never auto-retry this PR\n")
    assert unknown["next"] == "unknown"
    assert "never auto-retry" in unknown["op_note"]
    refusal = proto.helper_outcome(12, "refusing: unknown method yolo\n")
    assert refusal["next"] == "hold" and refusal["reason_code"] == "K12"
    weird = proto.helper_outcome(3, "")
    assert weird["next"] == "hold" and weird["reason_code"] == "K12"


def test_helper_reason_literals_exist_in_helper_source():
    """A wording change in gh_merge.py must break this test, not silently
    misroute a deferral."""
    for literal, _code, _state in proto.HELPER_REASONS:
        assert literal in HELPER_SRC, literal


def test_mergeable_state_table_matches_documented_enum():
    documented = {"clean", "dirty", "unstable", "blocked", "behind",
                  "unknown", "has_hooks", "draft"}
    assert set(proto.MERGEABLE_STATE_REASONS) == documented - {"clean"}
