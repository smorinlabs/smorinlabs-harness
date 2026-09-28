"""Actual status-only installation CI is valid consumer evidence."""

import pytest

import test_sweep_slice2 as fx


def status_consumer():
    obs, rec = fx.observe(), fx.receipt()
    obs.policy.required_checks = [fx.ev.RequiredCheck("ci/test")]
    obs.check_runs = fx.section(fx.check_runs())
    obs.statuses = fx.section(fx.combined(fx.status("ci/test", "success")))
    proof = {"kind": "status", "head_sha": fx.HEAD,
             "creator": "ci-bot", "target_url": "https://x.test",
             "evidence": "fixture: external CI log installs requests 2.32.5 and verifies that version"}
    rec.check_evidence["checks"][0].update(producer_id=None, proof=dict(proof))
    rec.dependency_evidence["updates"][0]["consumers"][0]["validation"] = {
        **proof, "context": "ci/test"}
    return obs, rec


def validation(rec):
    return rec.dependency_evidence["updates"][0]["consumers"][0]["validation"]


def test_status_only_dependency_consumer_needs_no_fabricated_local_run():
    obs, rec = status_consumer()
    result = fx.evaluate(obs, rec)
    assert result.state == fx.State.READY and result.merge_path == "put"
    assert validation(rec)["kind"] == "status"
    assert any("requests 2.32.5 resolved and tested by uv" in e["establishes"]
               for e in result.evidence)


@pytest.mark.parametrize("field,value", [
    ("head_sha", fx.BASE), ("creator", "other-bot"),
    ("target_url", "https://other.test"), ("context", "other/context"),
    ("creator", ""), ("target_url", ""),
])
def test_status_consumer_requires_its_exact_current_identity(field, value):
    obs, rec = status_consumer()
    validation(rec)[field] = value
    result = fx.evaluate(obs, rec)
    assert result.state == fx.State.BLOCKED and result.reason_code == "K13"
    assert result.merge_path == "none"


@pytest.mark.parametrize("field", ["creator", "target_url", "context"])
def test_status_consumer_requires_complete_proof(field):
    obs, rec = status_consumer()
    del validation(rec)[field]
    assert fx.evaluate(obs, rec).reason_code == "K13"


@pytest.mark.parametrize("scope,paths,fragment", [
    ("source", ["pyproject.toml", "uv.lock"], "source-only"),
    ("dependencies", ["pyproject.toml"], "installation inputs"),
])
def test_status_proof_needs_dependency_scope_and_all_consumer_inputs(scope, paths, fragment):
    obs, rec = status_consumer()
    rec.check_evidence["checks"][0].update(scope=scope, paths=paths)
    result = fx.evaluate(obs, rec)
    assert result.reason_code == "K13" and fragment in result.reason_line


def test_status_consumer_cannot_satisfy_application_bound_required_check():
    obs, rec = status_consumer()
    obs.policy.required_checks = [fx.ev.RequiredCheck("ci/test", fx.CI_APP)]
    result = fx.evaluate(obs, rec)
    assert result.state == fx.State.WAITING and result.reason_code == "K01"
    assert "required producer" in result.reason_line


@pytest.mark.parametrize("state,code", [("failure", "K04"), ("pending", "K01")])
def test_status_consumer_cannot_override_current_failure_or_pending(state, code):
    obs, rec = status_consumer()
    obs.statuses["data"]["statuses"][0]["state"] = state
    result = fx.evaluate(obs, rec)
    assert result.state != fx.State.READY and result.reason_code == code


@pytest.mark.parametrize("extra,value", [("producer_id", fx.CI_APP), ("run_id", 1),
                                        ("command", "pretend"), ("result", "success")])
def test_status_consumer_cannot_mix_proof_kinds(extra, value):
    obs, rec = status_consumer()
    validation(rec)[extra] = value
    result = fx.evaluate(obs, rec)
    assert result.reason_code == "K13" and "check-run/local fields" in result.reason_line
