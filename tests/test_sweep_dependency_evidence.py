"""Version-2 analysis distinguishes installed versions, fixtures and scans.

These are offline behavioral observations, not string-presence tests of the
skill. Positive controls retain the real required-check gates; each negative
changes one fact in otherwise complete, successful evidence.
"""

from copy import deepcopy
from dataclasses import asdict, replace

import pytest

import test_sweep_slice2 as fx

ev = fx.ev
State = fx.State


def evaluate(obs=None, rec=None, auth=None):
    return fx.evaluate(obs or fx.observe(), rec or fx.receipt(), auth=auth)


def check_validation(context="ci/test", run_id=1):
    return {"kind": "check_run", "head_sha": fx.HEAD, "context": context,
            "producer_id": fx.CI_APP, "run_id": run_id,
            "evidence": f"receipt: runs/{run_id}/installation-version-output"}


def local_validation(command="pip install -r requirements.txt && verify-version"):
    return {"kind": "local", "head_sha": fx.HEAD, "command": command,
            "result": "success", "evidence": "receipt: devsy-install.log"}


def two_consumers():
    """Like Doxa: only export changed; CI consumes an unchanged frozen lock."""
    rec = fx.receipt()
    dep, checks = deepcopy(rec.dependency_evidence), deepcopy(rec.check_evidence)
    changed = [{"filename": "requirements.txt", "sha": "d" * 40,
                "status": "modified", "changes": 2}]
    obs = fx.observe(files=fx.section(changed))
    dep["files"] += [
        {"path": "requirements.txt", "blob_sha": "d" * 40,
         "role": "generated_export", "generated_from": ["uv.lock"]},
        {"path": ".devsy/setup.sh", "blob_sha": "e" * 40,
         "role": "source", "generated_from": []},
    ]
    dep["consumers"].append({
        "id": "devsy", "kind": "install", "files": ["requirements.txt"],
        "entrypoints": [".devsy/setup.sh"], "usage": "pip install -r requirements.txt",
        "evidence": "receipt: setup.sh blob installs the export"})
    update = dep["updates"][0]
    update["files"] = ["requirements.txt"]
    update["consumers"][0]["validation"] = check_validation()
    update["consumers"].append({"consumer": "devsy", "resolved": "2.32.5",
                                "tested": "2.32.5", "validation": local_validation()})
    rec = ev.ClassifierReceipt.for_files(
        fx.HEAD, changed, True, "consumer-review", obs.observed_at,
        base_sha=fx.BASE, dependency_evidence=dep, check_evidence=checks)
    return obs, rec


def scanner(applicability="applicable"):
    record = {"context": "CodeQL", "producer_id": fx.CI_APP,
              "applicability": applicability, "scope": "source",
              "paths": ["pyproject.toml", "uv.lock"],
              "reason": "reviewed default-setup applicability for this change",
              "evidence": "receipt: settings and workflow inspection"}
    if applicability == "excluded":
        record["exclusion"] = {
            "source": ".github/workflows/ci.yml@" + "f3" * 20 + ":paths-ignore",
            "reason": "the reviewed trigger explicitly excludes both changed paths"}
    return record


def with_scanner(applicability="applicable", conclusion=None):
    obs, rec = fx.observe(), fx.receipt()
    rec.check_evidence["checks"].append(scanner(applicability))
    if conclusion is not None:
        obs.check_runs = fx.section(fx.check_runs(
            fx.run("ci/test"), fx.run("CodeQL", conclusion=conclusion, run_id=2)))
    return obs, rec


def assert_gap(result, fragment):
    assert result.state == State.BLOCKED
    assert result.reason_code == "K13"
    assert result.merge_path == "none"
    assert fragment in result.reason_line


def test_each_real_installation_consumer_can_prove_the_requested_version():
    obs, rec = two_consumers()
    result = evaluate(obs, rec)
    assert result.state == State.READY
    established = [e["establishes"] for e in result.evidence]
    assert any("2.32.5 resolved and tested by uv" in line for line in established)
    assert any("2.32.5 resolved and tested by devsy" in line for line in established)


@pytest.mark.parametrize("consumer,field", [(0, "resolved"), (0, "tested"),
                                           (1, "resolved"), (1, "tested")])
def test_green_frozen_ci_does_not_validate_old_or_untested_versions(consumer, field):
    obs, rec = two_consumers()
    rec.dependency_evidence["updates"][0]["consumers"][consumer][field] = "2.31.0"
    assert_gap(evaluate(obs, rec), "requested target is not proven")


def test_unchanged_canonical_lock_consumer_cannot_be_omitted_from_export_update():
    obs, rec = two_consumers()
    rec.dependency_evidence["updates"][0]["consumers"].pop(0)
    assert_gap(evaluate(obs, rec), "missing affected consumers ['uv']")


def test_generated_export_usage_cannot_be_imputed_from_its_lock_consumer():
    obs, rec = two_consumers()
    rec.dependency_evidence["consumers"].pop()
    rec.dependency_evidence["updates"][0]["consumers"].pop()
    assert_gap(evaluate(obs, rec), "requirements.txt: dependency/fixture usage has no consumer")


def test_frozen_check_cannot_be_reused_for_different_installation_inputs():
    obs, rec = two_consumers()
    rec.dependency_evidence["updates"][0]["consumers"][1]["validation"] = check_validation()
    assert_gap(evaluate(obs, rec), "does not cover its installation inputs")


def test_source_analysis_cannot_prove_installed_dependency_versions():
    obs, rec = two_consumers()
    rec.check_evidence["checks"][0]["scope"] = "source"
    assert_gap(evaluate(obs, rec), "source-only analysis does not test dependencies")


def subset_export():
    obs, rec = two_consumers()
    obs.files = fx.section([fx.files()[1]])
    update = rec.dependency_evidence["updates"][0]
    update.update(name="ruff", requested="0.16.8", files=["uv.lock"])
    update["consumers"][0].update(resolved="0.16.8", tested="0.16.8")
    update["consumers"][1].update(
        applicability="excluded", resolved=None, tested=None,
        validation=local_validation("pip install -r requirements.txt && assert-package-absent ruff"),
        exclusion={"source": "receipt: export command selects runtime dependencies only",
                   "reason": "ruff is a development dependency absent from this runtime export"})
    rec = replace(rec, files_digest=ev.files_digest(obs.files["data"]), file_count=1)
    return obs, rec


def test_subset_export_can_prove_a_development_package_is_not_installed():
    obs, rec = subset_export()
    result = evaluate(obs, rec)
    assert result.state == State.READY
    assert any("ruff absent from devsy" in e["establishes"] for e in result.evidence)


def test_directly_changed_consumer_input_cannot_claim_package_absence():
    obs, rec = subset_export()
    update = rec.dependency_evidence["updates"][0]
    obs.files = fx.section([{"filename": "requirements.txt", "sha": "d" * 40,
                            "status": "modified", "changes": 2}])
    rec = replace(rec, files_digest=ev.files_digest(obs.files["data"]))
    update["files"] = ["requirements.txt"]
    assert_gap(evaluate(obs, rec), "directly changed dependency input for this update")


def test_other_update_in_same_export_does_not_overrule_proven_package_absence():
    obs, rec = subset_export()
    obs.files["data"].append({"filename": "requirements.txt", "sha": "d" * 40,
                              "status": "modified", "changes": 2})
    update = deepcopy(rec.dependency_evidence["updates"][0])
    update.update(name="idna", requested="3.20", files=["requirements.txt"],
                  evidence="receipt: separate idna runtime pin update")
    for consumer in update["consumers"]:
        consumer.pop("exclusion", None)
        consumer.pop("applicability", None)
        consumer.update(resolved="3.20", tested="3.20")
    update["consumers"][1]["validation"] = local_validation(
        "pip install -r requirements.txt && assert-installed idna 3.20")
    rec.dependency_evidence["updates"].append(update)
    rec = replace(rec, files_digest=ev.files_digest(obs.files["data"]), file_count=2)
    assert evaluate(obs, rec).state == State.READY


def test_exclusion_cannot_excuse_an_old_installed_version():
    obs, rec = subset_export()
    rec.dependency_evidence["updates"][0]["consumers"][1]["resolved"] = "0.16.0"
    assert_gap(evaluate(obs, rec), "package absence, not excuse an old installed version")


def test_package_absence_requires_actual_exact_head_validation():
    obs, rec = subset_export()
    del rec.dependency_evidence["updates"][0]["consumers"][1]["validation"]
    assert_gap(evaluate(obs, rec), "consumer validation must be an object")


@pytest.mark.parametrize("mutation,fragment", [
    (lambda d: d["files"].pop(0), "unmapped file pyproject.toml"),
    (lambda d: d["files"][0].update(blob_sha="0" * 40), "blob does not match"),
    (lambda d: d["updates"][0].update(files=["pyproject.toml"]), "lack updates"),
    (lambda d: d["files"][1].update(generated_from=[]), "lacks its inputs"),
    (lambda d: d.update(complete=False), "inventory is incomplete"),
])
def test_changed_files_and_dependency_graph_need_complete_evidence(mutation, fragment):
    rec = fx.receipt()
    mutation(rec.dependency_evidence)
    assert_gap(evaluate(rec=rec), fragment)


def test_generated_file_graph_cannot_be_cyclic():
    rec = fx.receipt()
    rec.dependency_evidence["files"][0]["generated_from"] = ["uv.lock"]
    assert_gap(evaluate(rec=rec), "contain a cycle")


@pytest.mark.parametrize("proof_change,fragment", [
    ({"head_sha": "0" * 40}, "not the evaluated head"),
    ({"producer_id": 999}, "producer differs"),
    ({"run_id": 99}, "superseded/different run"),
])
def test_installation_validation_is_bound_to_current_head_producer_and_run(proof_change, fragment):
    obs, rec = two_consumers()
    rec.dependency_evidence["updates"][0]["consumers"][0]["validation"].update(proof_change)
    assert_gap(evaluate(obs, rec), fragment)


def test_stale_local_installation_receipt_cannot_validate_a_new_head():
    obs, rec = two_consumers()
    rec.dependency_evidence["updates"][0]["consumers"][1]["validation"]["head_sha"] = "0" * 40
    assert_gap(evaluate(obs, rec), "not the evaluated head")


def fixture_receipt():
    rec = fx.receipt()
    path = "test_data/nodups/seconddir/requirements.txt"
    test_path = "tests/test_onlycopy.py"
    changed = [{"filename": path, "sha": "9" * 40, "status": "modified"}]
    dep = {"complete": True, "files": [
        {"path": path, "blob_sha": "9" * 40, "role": "fixture", "generated_from": []},
        {"path": test_path, "blob_sha": "8" * 40, "role": "source", "generated_from": []},
        rec.dependency_evidence["files"][-1]],
        "consumers": [{"id": "onlycopy", "kind": "fixture", "files": [path],
                       "entrypoints": [test_path], "usage": "read bytes and compare duplicate paths",
                       "evidence": "receipt: full fixture/import/install-use review"}],
        "updates": [{"name": "Jinja2", "requested": "2.11.3", "files": [path],
                     "evidence": "receipt: one fixture pin line changed",
                     "consumers": [{"consumer": "onlycopy"}]}]}
    checks = deepcopy(rec.check_evidence)
    for entry in checks["checks"]:
        entry["paths"] = [path]
        entry["scope"] = "source"
    obs = fx.observe(files=fx.section(changed))
    return obs, ev.ClassifierReceipt.for_files(
        fx.HEAD, changed, True, "fixture-review", obs.observed_at,
        base_sha=fx.BASE, dependency_evidence=dep, check_evidence=checks)


def test_fixture_manifest_is_ordinary_review_not_an_owner_veto_or_runtime_fix():
    obs, rec = fixture_receipt()
    result = evaluate(obs, rec)
    assert result.state == State.BLOCKED
    assert result.reason_code == "K09"
    assert result.action_owner == "pr-merge-flow"
    assert "fixture" in result.reason_line
    assert "not an owner veto" in result.action


def test_fixture_claim_requires_concrete_usage_and_entrypoint_evidence():
    obs, rec = fixture_receipt()
    rec.dependency_evidence["consumers"][0]["evidence"] = ""
    assert_gap(evaluate(obs, rec), "onlycopy.evidence")


def test_installed_manifest_cannot_be_exempted_by_calling_its_consumer_a_fixture():
    rec = fx.receipt()
    rec.dependency_evidence["consumers"][0]["kind"] = "fixture"
    assert_gap(evaluate(rec=rec), "fixture usage cannot exempt a dependency manifest")


def test_documented_source_scan_exclusion_does_not_require_every_configured_scanner():
    obs, rec = with_scanner("excluded")
    result = evaluate(obs, rec)
    assert result.state == State.READY
    assert any("CodeQL: excluded; scope source" in e["establishes"] for e in result.evidence)


@pytest.mark.parametrize("conclusion", [None, "neutral", "skipped"])
def test_applicable_missing_or_neutral_scan_is_unknown_coverage_not_ci_failure(conclusion):
    obs, rec = with_scanner(conclusion=conclusion)
    assert_gap(evaluate(obs, rec), "CodeQL")


def test_unexplained_neutral_result_cannot_hide_outside_the_applicability_inventory():
    obs, rec = with_scanner(conclusion="neutral")
    rec.check_evidence["checks"].pop()
    assert_gap(evaluate(obs, rec), "neutral/skipped result lacks applicability evidence")


def test_unknown_scan_applicability_is_distinct_from_a_failed_scan():
    obs, rec = with_scanner("unknown")
    result = evaluate(obs, rec)
    assert_gap(result, "applicability unknown")
    assert "not a CI failure" in result.reason_line


def test_exclusion_without_documented_source_does_not_count():
    obs, rec = with_scanner("excluded")
    del rec.check_evidence["checks"][-1]["exclusion"]
    assert_gap(evaluate(obs, rec), "CodeQL.exclusion")


def analysis_proof():
    return {"kind": "analysis", "head_sha": fx.HEAD, "producer_id": fx.CI_APP,
            "id": 17, "url": "https://example.test/code-scanning/analyses/17",
            "conclusion": "success", "evidence": "receipt: complete analysis response"}


def test_neutral_check_can_be_supported_by_actual_matching_head_analysis():
    obs, rec = with_scanner(conclusion="neutral")
    rec.check_evidence["checks"][-1]["proof"] = analysis_proof()
    assert evaluate(obs, rec).state == State.READY


@pytest.mark.parametrize("change", [{"head_sha": fx.BASE}, {"producer_id": 999},
                                    {"conclusion": "failure"}, {"id": 0},
                                    {"url": "https://"}])
def test_analysis_proof_cannot_be_stale_wrong_producer_or_unsuccessful(change):
    obs, rec = with_scanner(conclusion="neutral")
    proof = analysis_proof()
    proof.update(change)
    rec.check_evidence["checks"][-1]["proof"] = proof
    assert_gap(evaluate(obs, rec), "analysis proof")


@pytest.mark.parametrize("run_value,code", [(None, "K01"), ("failure", "K04")])
def test_exclusion_never_waives_required_missing_or_failed_gate(run_value, code):
    obs, rec = with_scanner("excluded", run_value)
    obs.policy.required_checks.append(ev.RequiredCheck("CodeQL", fx.CI_APP))
    result = evaluate(obs, rec)
    assert result.state != State.READY
    assert result.reason_code == code


def test_exclusion_never_waives_required_producer():
    obs, rec = with_scanner("excluded", "success")
    obs.policy.required_checks.append(ev.RequiredCheck("CodeQL", fx.CI_APP))
    obs.check_runs["data"]["check_runs"][-1]["app"]["id"] = 999
    assert evaluate(obs, rec).reason_code == "K01"


def status_only():
    obs, rec = fx.observe(), fx.receipt()
    obs.policy.required_checks = [ev.RequiredCheck("ci/test")]
    obs.check_runs = fx.section(fx.check_runs())
    obs.statuses = fx.section(fx.combined(fx.status("ci/test", "success")))
    rec.check_evidence["checks"][0].update(
        producer_id=None,
        proof={"kind": "status", "head_sha": fx.HEAD, "creator": "ci-bot",
               "target_url": "https://x.test", "evidence": "receipt: successful status on exact commit"})
    return obs, rec


def test_unbound_required_status_retains_its_supported_success_path():
    obs, rec = status_only()
    assert evaluate(obs, rec).state == State.READY


def test_status_proof_cannot_replace_an_app_bound_required_check():
    obs, rec = status_only()
    obs.policy.required_checks = [ev.RequiredCheck("ci/test", fx.CI_APP)]
    assert evaluate(obs, rec).reason_code == "K01"


@pytest.mark.parametrize("field,value", [("creator", "other-bot"),
                                        ("head_sha", fx.BASE),
                                        ("target_url", "https://other.test")])
def test_status_proof_is_bound_to_head_creator_and_current_target(field, value):
    obs, rec = status_only()
    rec.check_evidence["checks"][0]["proof"][field] = value
    assert_gap(evaluate(obs, rec), "status proof")


def test_excluded_required_run_still_has_to_belong_to_this_head():
    obs, rec = with_scanner("excluded", "success")
    obs.policy.required_checks.append(ev.RequiredCheck("CodeQL", fx.CI_APP))
    obs.check_runs["data"]["check_runs"][-1]["head_sha"] = fx.BASE
    assert_gap(evaluate(obs, rec), "matching-head")


def test_fresh_fingerprint_notices_changed_successful_producer_or_run_identity():
    obs, rec = fx.observe(), fx.receipt()
    result = evaluate(obs, rec)
    assert result.state == State.READY
    fresh = deepcopy(obs)
    fresh.check_runs["data"]["check_runs"][0].update(id=99)
    assert "check_states" in ev.stale_reasons(result, fresh)
    fresh = deepcopy(obs)
    fresh.check_runs["data"]["check_runs"][0]["app"]["id"] = 999
    assert "check_states" in ev.stale_reasons(result, fresh)


def test_successful_but_stale_nonrequired_run_does_not_prove_applicable_coverage():
    obs, rec = with_scanner(conclusion="success")
    obs.check_runs["data"]["check_runs"][-1]["head_sha"] = fx.BASE
    assert_gap(evaluate(obs, rec), "no matching-head check run")


@pytest.mark.parametrize("field,value", [("base_sha", "0" * 40), ("base_sha", None),
                                        ("file_count", 99), ("schema_version", True),
                                        ("dependency_only", "true")])
def test_receipt_metadata_cannot_change_or_coerce_its_binding(field, value):
    assert_gap(evaluate(rec=replace(fx.receipt(), **{field: value})), "receipt")


def test_range_request_requires_explicit_exact_target_selection():
    rec = fx.receipt()
    rec.dependency_evidence["updates"][0]["requested"] = ">=2,<3"
    assert_gap(evaluate(rec=rec), "selected exact version")


@pytest.mark.parametrize("field,value", [("dependency_evidence", None),
                                        ("check_evidence", []),
                                        ("dependency_evidence", {}),
                                        ("check_evidence", {"complete": True})])
def test_missing_or_malformed_analysis_fails_closed(field, value):
    assert_gap(evaluate(rec=replace(fx.receipt(), **{field: value})), "evidence")


def test_malformed_nested_type_returns_hold_without_an_exception():
    rec = fx.receipt()
    rec.dependency_evidence["files"][0]["role"] = []
    assert_gap(evaluate(rec=rec), "analysis incomplete")


def test_legacy_receipt_deserializes_without_claiming_new_analysis():
    payload = asdict(fx.receipt())
    for key in ("schema_version", "base_sha", "dependency_evidence", "check_evidence"):
        payload.pop(key)
    legacy = ev.ClassifierReceipt(**payload)
    assert legacy.schema_version == 1
    assert_gap(evaluate(rec=legacy), "legacy")


def test_legacy_receipt_does_not_prevent_reporting_an_observed_historical_merge():
    obs = fx.observe(pull=fx.section(fx.pull(
        state="closed", merged=True, merge_commit_sha="c" * 40,
        merged_at="2026-09-27T00:00:00Z")))
    result = evaluate(obs, replace(fx.receipt(), schema_version=1))
    assert result.to_outcome("PR-001")["outcome"] == "merged"


def test_owner_hold_needs_provenance_but_gated_authority_is_already_a_source():
    assert_gap(evaluate(auth=fx.authority(owner_hold=True)), "no recorded source")
    held = evaluate(auth=fx.authority(owner_hold=True,
                    owner_hold_source="run authority: owner instruction 2026-09-27"))
    assert held.reason_code == "K16"
    assert held.decision["source"].startswith("run authority:")
    gated = evaluate(auth=fx.authority(mode="gated"))
    assert gated.state == State.NEEDS_OWNER
    assert gated.decision["source"] == "saved authority: mode=gated"
