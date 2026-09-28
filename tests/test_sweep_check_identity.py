"""Current executions and independent check producers cannot hide each other."""

from copy import deepcopy

import pytest

import test_sweep_slice2 as fx


def observation(*runs):
    return fx.observe(check_runs=fx.section(fx.check_runs(*runs)))


@pytest.mark.parametrize("status", ["queued", "in_progress"])
def test_active_rerun_supersedes_old_success_and_invalidates_readiness(status):
    before = fx.evaluate()
    current = observation(
        fx.run("ci/test"),
        fx.run("ci/test", status=status, conclusion=None, run_id=2,
               completed_at=None))
    result = fx.evaluate(current)
    assert result.state == fx.State.WAITING and result.reason_code == "K01"
    assert result.merge_path == "none"
    assert "check_states" in fx.ev.stale_reasons(before, current)


def test_current_execution_is_not_replaced_by_older_run_finishing_later():
    current = observation(
        fx.run("ci/test", conclusion="failure", run_id=1,
               completed_at="2026-09-22T00:12:00Z"),
        fx.run("ci/test", run_id=2, completed_at="2026-09-22T00:11:00Z"))
    assert fx.evaluate(current).state == fx.State.READY


def test_other_successful_producer_does_not_hide_required_producer():
    current = observation(
        fx.run("ci/test"),
        fx.run("ci/test", app_id=999, run_id=2,
               completed_at="2026-09-22T00:12:00Z"))
    assert fx.evaluate(current).state == fx.State.READY


@pytest.mark.parametrize("state,conclusion,code", [
    ("in_progress", None, "K01"),
    ("completed", "failure", "K04"),
])
def test_other_producer_pending_or_failure_cannot_be_hidden_by_required_success(
        state, conclusion, code):
    before = fx.evaluate()
    current = observation(
        fx.run("ci/test", app_id=999, run_id=2, status=state,
               conclusion=conclusion, completed_at=None),
        fx.run("ci/test", run_id=3, completed_at="2026-09-22T00:12:00Z"))
    result = fx.evaluate(current)
    assert result.state != fx.State.READY and result.reason_code == code
    assert "check_states" in fx.ev.stale_reasons(before, current)


def test_two_required_producers_can_share_a_context_with_separate_evidence():
    current = observation(fx.run("ci/test"), fx.run("ci/test", app_id=999, run_id=2))
    current.policy.required_checks.append(fx.ev.RequiredCheck("ci/test", 999))
    receipt = fx.receipt()
    other = deepcopy(receipt.check_evidence["checks"][0])
    other["producer_id"] = 999
    receipt.check_evidence["checks"].append(other)
    assert fx.evaluate(current, receipt).state == fx.State.READY


def test_consumer_validation_uses_its_producer_even_with_a_newer_other_producer():
    current = observation(fx.run("ci/test"), fx.run("ci/test", app_id=999, run_id=2))
    receipt = fx.receipt()
    receipt.dependency_evidence["updates"][0]["consumers"][0]["validation"] = {
        "kind": "check_run", "head_sha": fx.HEAD, "context": "ci/test",
        "producer_id": fx.CI_APP, "run_id": 1,
        "evidence": "fixture: check-run 1 installs and verifies the target dependency"}
    assert fx.evaluate(current, receipt).state == fx.State.READY


def test_a_new_successful_rerun_invalidates_old_consumer_check_proof():
    current = observation(fx.run("ci/test"), fx.run("ci/test", run_id=2))
    receipt = fx.receipt()
    receipt.dependency_evidence["updates"][0]["consumers"][0]["validation"] = {
        "kind": "check_run", "head_sha": fx.HEAD, "context": "ci/test",
        "producer_id": fx.CI_APP, "run_id": 1,
        "evidence": "fixture: superseded execution"}
    result = fx.evaluate(current, receipt)
    assert result.state == fx.State.BLOCKED and result.reason_code == "K13"
    assert "superseded/different run" in result.reason_line


def test_other_producer_neutral_result_needs_its_own_applicability_record():
    current = observation(fx.run("ci/test"),
                          fx.run("ci/test", app_id=999, run_id=2, conclusion="neutral"))
    result = fx.evaluate(current)
    assert result.state == fx.State.BLOCKED and result.reason_code == "K13"
    assert "neutral/skipped result lacks applicability evidence" in result.reason_line
