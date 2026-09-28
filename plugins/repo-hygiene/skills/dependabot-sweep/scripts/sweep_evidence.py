#!/usr/bin/env python3
"""Validate v2 classifier analysis without reading files or the network.

The classifier attests repository facts at the receipt's exact head/base.
Changed-file blobs are cross-checked against the full observation. Context
file blobs, consumer discovery, version extraction and documented exclusions
remain reviewed evidence, not facts inferred from a filename or green check.

`requested` is the selected exact version, including for a range update:
the update's evidence must explain that selection. No package resolver or
ecosystem-specific version comparison is silently approximated here.
"""

from __future__ import annotations

import re
from urllib.parse import urlsplit


ROLES = {"manifest", "lockfile", "generated_export", "fixture", "workflow",
         "source", "config"}
DEPENDENCY_ROLES = {"manifest", "lockfile", "generated_export"}
CONSUMER_ROLES = DEPENDENCY_ROLES | {"fixture", "workflow"}
SCOPES = {"source", "dependencies", "source_and_dependencies"}
SHA = re.compile(r"[0-9a-f]{40}\Z")


class EvidenceError(ValueError):
    """An incomplete or contradictory analysis; it never grants a waiver."""


def _object(value, label, required, optional=()):
    if not isinstance(value, dict):
        raise EvidenceError(f"{label} must be an object")
    missing = set(required) - value.keys()
    extra = value.keys() - set(required) - set(optional)
    if missing or extra:
        raise EvidenceError(f"{label}: missing fields {sorted(missing)}, "
                            f"unknown fields {sorted(extra)}")
    return value


def _text(value, label):
    if not isinstance(value, str) or not value.strip():
        raise EvidenceError(f"{label} must be nonempty text")
    return value


def _list(value, label, *, nonempty=False):
    if not isinstance(value, list) or (nonempty and not value):
        raise EvidenceError(f"{label} must be {'a nonempty' if nonempty else 'a'} list")
    return value


def _path(value, label):
    _text(value, label)
    if value.startswith("/") or any(p in ("", ".", "..")
                                    for p in value.split("/")):
        raise EvidenceError(f"{label} must be a repository-relative file path")
    return value


def _sha(value, label):
    if not isinstance(value, str) or not SHA.fullmatch(value):
        raise EvidenceError(f"{label} must be a full lowercase commit/blob SHA")
    return value


def _paths(value, label, files, *, nonempty=False):
    values = _list(value, label, nonempty=nonempty)
    for path in values:
        _path(path, label)
        if path not in files:
            raise EvidenceError(f"{label}: unmapped file {path}")
    if len(set(values)) != len(values):
        raise EvidenceError(f"{label} contains duplicate paths")
    return set(values)


def _producer(value, label):
    if value is not None and (type(value) is not int or value <= 0):
        raise EvidenceError(f"{label} must be a positive app id or null")


def _same_head(value, head, label):
    _sha(value, label)
    if value != head:
        raise EvidenceError(f"{label} is not the evaluated head")


def _files(data, observed):
    files = {}
    for entry in _list(data, "dependency_evidence.files", nonempty=True):
        _object(entry, "file", ("path", "blob_sha", "role", "generated_from"))
        path = _path(entry["path"], "file.path")
        _sha(entry["blob_sha"], f"{path}.blob_sha")
        if entry["role"] not in ROLES:
            raise EvidenceError(f"{path}: unknown file role")
        if path in files:
            raise EvidenceError(f"duplicate file mapping for {path}")
        files[path] = entry
    for entry in files.values():
        path = entry["path"]
        inputs = _paths(entry["generated_from"], f"{path}.generated_from", files)
        if entry["role"] in {"lockfile", "generated_export"} and not inputs:
            raise EvidenceError(f"{path}: generated dependency file lacks its inputs")
        if path in inputs:
            raise EvidenceError(f"{path}: a file cannot generate itself")
        if any(files[p]["role"] not in DEPENDENCY_ROLES for p in inputs):
            raise EvidenceError(f"{path}: generated inputs must be dependency files")
    for changed in observed:
        path = changed.get("filename")
        if path not in files:
            raise EvidenceError(f"changed file {path} is missing from dependency analysis")
        if files[path]["blob_sha"] != changed.get("sha"):
            raise EvidenceError(f"changed file {path} blob does not match observation")
    visiting, visited = set(), set()

    def visit(path):
        if path in visiting:
            raise EvidenceError(f"{path}: generated dependency inputs contain a cycle")
        if path in visited:
            return
        visiting.add(path)
        for source in files[path]["generated_from"]:
            visit(source)
        visiting.remove(path)
        visited.add(path)

    for path in files:
        visit(path)
    return files


def _consumers(data, files):
    consumers, covered = {}, set()
    for entry in _list(data, "dependency_evidence.consumers"):
        _object(entry, "consumer", ("id", "kind", "files", "entrypoints",
                                    "usage", "evidence"))
        name = _text(entry["id"], "consumer.id")
        if name in consumers:
            raise EvidenceError(f"duplicate consumer {name}")
        if entry["kind"] not in {"install", "automation", "fixture"}:
            raise EvidenceError(f"{name}: unknown consumer kind")
        paths = _paths(entry["files"], f"{name}.files", files, nonempty=True)
        if any(files[p]["role"] not in CONSUMER_ROLES for p in paths):
            raise EvidenceError(f"{name}: consumer inputs must identify dependencies or fixtures")
        if entry["kind"] == "fixture":
            if any(files[p]["role"] != "fixture" for p in paths):
                raise EvidenceError(f"{name}: fixture usage cannot exempt a dependency manifest")
        elif any(files[p]["role"] == "fixture" for p in paths):
            raise EvidenceError(f"{name}: an installed fixture must be classified as a manifest")
        _paths(entry["entrypoints"], f"{name}.entrypoints", files, nonempty=True)
        _text(entry["usage"], f"{name}.usage")
        _text(entry["evidence"], f"{name}.evidence")
        consumers[name] = entry
        covered.update(paths)
    # List all files a consumer actually reads (e.g. pyproject + uv.lock).
    # A connection to a tested lock is not usage evidence for its export.
    for path, entry in files.items():
        if entry["role"] in DEPENDENCY_ROLES | {"fixture"}:
            if path not in covered:
                raise EvidenceError(f"{path}: dependency/fixture usage has no consumer evidence")
    return consumers


def _connected(paths, files):
    """Undirected generation graph: changes affect inputs and their exports."""
    result = set(paths)
    while True:
        before = set(result)
        for path, entry in files.items():
            related = {path, *entry["generated_from"]}
            if related & result:
                result.update(related)
        if before == result:
            return result


def latest_runs(check_runs):
    """Keep the current execution of each (context, application) pair.

    A newer execution can still be queued or running, so completed_at is
    not an execution ordering key. GitHub run ids distinguish successive
    executions; started_at breaks ties when an execution is re-observed.
    Different producers never supersede each other's results.
    """
    latest = {}
    for run in (check_runs or {}).get("check_runs", []):
        order = (run.get("id") or 0, run.get("started_at") or "")
        identity = (run.get("name", ""), (run.get("app") or {}).get("id"))
        if identity not in latest or order >= latest[identity][0]:
            latest[identity] = (order, run)
    return {identity: run for identity, (_, run) in latest.items()}


def _matching_run(run, context, producer, head, *, run_id=None):
    if not run or run.get("head_sha") != head:
        raise EvidenceError(f"{context}: no matching-head check run proves coverage")
    if producer is None or (run.get("app") or {}).get("id") != producer:
        raise EvidenceError(f"{context}: coverage proof lacks the matching producer")
    if run_id is not None and run.get("id") != run_id:
        raise EvidenceError(f"{context}: validation refers to a superseded/different run")
    if run.get("status") != "completed" or run.get("conclusion") != "success":
        raise EvidenceError(f"{context}: {run.get('conclusion') or run.get('status')} "
                            "does not prove applicable coverage")


def _analysis_proof(proof, entry, head):
    _object(proof, "analysis proof", ("kind", "head_sha", "producer_id", "id",
                                      "url", "conclusion", "evidence"))
    if proof["kind"] != "analysis":
        raise EvidenceError("coverage proof kind must be analysis")
    _same_head(proof["head_sha"], head, "analysis proof.head_sha")
    _producer(proof["producer_id"], "analysis proof.producer_id")
    if proof["producer_id"] != entry["producer_id"] or proof["producer_id"] is None:
        raise EvidenceError("analysis proof has no matching producer")
    if (type(proof["id"]) not in (int, str) or not str(proof["id"]).strip()
            or (type(proof["id"]) is int and proof["id"] <= 0)):
        raise EvidenceError("analysis proof needs its analysis id")
    url = urlsplit(_text(proof["url"], "analysis proof.url"))
    if url.scheme != "https" or not url.hostname:
        raise EvidenceError("analysis proof needs its source HTTPS URL")
    _text(proof["evidence"], "analysis proof.evidence")
    if proof["conclusion"] != "success":
        raise EvidenceError("analysis proof does not establish successful coverage")


def _status_proof(proof, entry, obs):
    _object(proof, "status proof", ("kind", "head_sha", "creator", "target_url", "evidence"))
    _same_head(proof["head_sha"], obs.head_sha, "status proof.head_sha")
    _text(proof["creator"], "status proof.creator")
    _text(proof["target_url"], "status proof.target_url")
    _text(proof["evidence"], "status proof.evidence")
    data = obs.statuses["data"] or {}
    statuses = {s.get("context", ""): s for s in data.get("statuses", [])}
    status = statuses.get(entry["context"], {})
    if (entry["producer_id"] is not None or data.get("sha") != obs.head_sha
            or status.get("state") != "success"
            or (status.get("creator") or {}).get("login") != proof["creator"]
            or status.get("target_url") != proof["target_url"]):
        raise EvidenceError("status proof lacks a matching-head successful status from its creator")


def _checks(data, files, obs, reviewer_contexts):
    _object(data, "check_evidence", ("complete", "basis", "checks"))
    if data["complete"] is not True:
        raise EvidenceError("check applicability inventory is incomplete")
    basis = _object(data["basis"], "check_evidence.basis", ("files", "evidence"))
    _paths(basis["files"], "check_evidence.basis.files", files)
    _text(basis["evidence"], "check_evidence.basis.evidence")
    checks, latest = {}, latest_runs(obs.check_runs["data"])
    for entry in _list(data["checks"], "check_evidence.checks"):
        _object(entry, "check applicability", ("context", "producer_id",
                "applicability", "scope", "paths", "reason", "evidence"),
                ("exclusion", "proof"))
        context = _text(entry["context"], "check.context")
        _producer(entry["producer_id"], f"{context}.producer_id")
        identity = (context, entry["producer_id"])
        if identity in checks:
            raise EvidenceError(f"duplicate applicability record for {context} "
                                f"from producer {entry['producer_id']}")
        if entry["scope"] not in SCOPES:
            raise EvidenceError(f"{context}: unknown coverage scope")
        _paths(entry["paths"], f"{context}.paths", files, nonempty=True)
        _text(entry["reason"], f"{context}.reason")
        _text(entry["evidence"], f"{context}.evidence")
        applicability = entry["applicability"]
        if applicability == "unknown":
            raise EvidenceError(f"{context}: applicability unknown; "
                                f"{entry['reason']} (not a CI failure)")
        if applicability == "excluded":
            exclusion = _object(entry.get("exclusion"), f"{context}.exclusion",
                                ("source", "reason"))
            _text(exclusion["source"], f"{context}.exclusion.source")
            _text(exclusion["reason"], f"{context}.exclusion.reason")
            if "proof" in entry:
                raise EvidenceError(f"{context}: excluded checks cannot claim analysis proof")
        elif applicability == "applicable":
            if "exclusion" in entry:
                raise EvidenceError(f"{context}: applicable check has an exclusion")
            if "proof" in entry:
                proof = entry["proof"]
                if isinstance(proof, dict) and proof.get("kind") == "status":
                    _status_proof(proof, entry, obs)
                else:
                    _analysis_proof(proof, entry, obs.head_sha)
            else:
                _matching_run(latest.get(identity), context, entry["producer_id"],
                              obs.head_sha)
        else:
            raise EvidenceError(f"{context}: invalid applicability value")
        checks[identity] = entry
    # Successful checks are not universally required scanners. Missing
    # configured checks enter via the reviewed applicability inventory;
    # every neutral/skip must explain what it actually means. Repository
    # requirements are independently enforced by the evaluator, never here.
    for identity, run in latest.items():
        context, _ = identity
        if run.get("conclusion") in {"neutral", "skipped"} and identity not in checks:
            raise EvidenceError(f"{context}: neutral/skipped result lacks applicability evidence")
    for req in obs.policy.required_checks:
        present = any(context == req.context and (
            req.producer_id is None or producer == req.producer_id)
            for context, producer in checks)
        if not present and req.context not in reviewer_contexts:
            raise EvidenceError(f"{req.context}: required check lacks applicability evidence")
    return checks, latest


def _validation(proof, consumer, checks, latest, obs):
    _object(proof, "consumer validation", ("kind", "head_sha", "evidence"),
            ("context", "producer_id", "run_id", "command", "result",
             "creator", "target_url"))
    head = obs.head_sha
    _same_head(proof["head_sha"], head, "consumer validation.head_sha")
    _text(proof["evidence"], "consumer validation.evidence")
    if proof["kind"] == "local":
        _text(proof.get("command"), "consumer validation.command")
        if proof.get("result") != "success":
            raise EvidenceError("local consumer validation did not succeed")
        if set(proof) & {"context", "producer_id", "run_id", "creator", "target_url"}:
            raise EvidenceError("local consumer validation contains check-run fields")
    elif proof["kind"] in {"check_run", "status"}:
        context = _text(proof.get("context"), "consumer validation.context")
        if proof["kind"] == "check_run":
            _producer(proof.get("producer_id"), "consumer validation.producer_id")
        identity = (context, proof.get("producer_id") if proof["kind"] == "check_run" else None)
        check = checks.get(identity)
        if not check and any(name == context for name, _ in checks):
            raise EvidenceError(f"{consumer['id']}: validation producer differs from coverage")
        if not check or check["applicability"] != "applicable":
            raise EvidenceError(f"{consumer['id']}: validation lacks an applicable check")
        if check["scope"] not in {"dependencies", "source_and_dependencies"}:
            raise EvidenceError(f"{consumer['id']}: source-only analysis does not test dependencies")
        if not set(consumer["files"]).issubset(check["paths"]):
            raise EvidenceError(f"{consumer['id']}: check does not cover its installation inputs")
        if proof["kind"] == "status":
            if set(proof) & {"producer_id", "run_id", "command", "result"}:
                raise EvidenceError("status consumer validation contains check-run/local fields")
            _status_proof({k: v for k, v in proof.items() if k != "context"}, check, obs)
            return
        if proof.get("producer_id") != check["producer_id"]:
            raise EvidenceError(f"{consumer['id']}: validation producer differs from coverage")
        if type(proof.get("run_id")) is not int or proof["run_id"] <= 0:
            raise EvidenceError("consumer validation needs a positive check run_id")
        if set(proof) & {"command", "result", "creator", "target_url"}:
            raise EvidenceError("check-run validation contains local-validation fields")
        _matching_run(latest.get(identity), context, check["producer_id"], head,
                      run_id=proof["run_id"])
    else:
        raise EvidenceError("consumer validation must identify a check_run, status, or local run")


def validate_evidence(receipt, obs, reviewer_contexts=()):
    """Return auditable evidence summaries, or raise on missing coverage.

    Called after policy/check failure gates, so exclusions cannot replace a
    required run, override a failed/pending check or waive its producer.
    """
    dep = _object(receipt.dependency_evidence, "dependency_evidence",
                  ("complete", "files", "consumers", "updates"))
    if dep["complete"] is not True:
        raise EvidenceError("dependency/consumer inventory is incomplete")
    files = _files(dep["files"], obs.files["data"] or [])
    consumers = _consumers(dep["consumers"], files)
    checks, latest = _checks(receipt.check_evidence, files, obs, reviewer_contexts)
    covered = set()
    summaries = []
    for update in _list(dep["updates"], "dependency_evidence.updates"):
        _object(update, "dependency update", ("name", "requested", "files",
                                              "evidence", "consumers"))
        name = _text(update["name"], "update.name")
        requested = _text(update["requested"], f"{name}.requested")
        if any(c in requested for c in "<>=,|*^~ \t\r\n"):
            raise EvidenceError(f"{name}: requested must be a selected exact version, "
                                "with range selection explained in evidence")
        _text(update["evidence"], f"{name}.evidence")
        paths = _paths(update["files"], f"{name}.files", files, nonempty=True)
        if any(files[p]["role"] not in CONSUMER_ROLES for p in paths):
            raise EvidenceError(f"{name}: update must identify its dependency/fixture files")
        affected = _connected(paths, files)
        expected = {key for key, consumer in consumers.items()
                    if set(consumer["files"]) & affected}
        if not expected:
            raise EvidenceError(f"{name}: update has no affected consumer")
        seen, tested_consumers = set(), set()
        for entry in _list(update["consumers"], f"{name}.consumers"):
            _object(entry, "update consumer", ("consumer",),
                    ("resolved", "tested", "validation", "applicability", "exclusion"))
            consumer_id = _text(entry["consumer"], "update consumer.consumer")
            if consumer_id not in expected or consumer_id in seen:
                raise EvidenceError(f"{name}: unexpected/duplicate consumer {consumer_id}")
            seen.add(consumer_id)
            consumer = consumers[consumer_id]
            if consumer["kind"] == "fixture":
                if set(entry) != {"consumer"}:
                    raise EvidenceError(f"{name}: fixture text is not installed-version evidence")
                continue
            applicability = entry.get("applicability", "applicable")
            if applicability == "excluded":
                changed_inputs = {f["filename"] for f in obs.files["data"] or []}
                if paths & set(consumer["files"]) & changed_inputs:
                    raise EvidenceError(f"{name}/{consumer_id}: directly changed dependency "
                                        "input for this update cannot be excluded")
                exclusion = _object(entry.get("exclusion"), "consumer exclusion",
                                    ("source", "reason"))
                _text(exclusion["source"], "consumer exclusion.source")
                _text(exclusion["reason"], "consumer exclusion.reason")
                if ("resolved" not in entry or "tested" not in entry
                        or entry["resolved"] is not None or entry["tested"] is not None):
                    raise EvidenceError(f"{name}/{consumer_id}: excluded consumer must prove "
                                        "package absence, not excuse an old installed version")
                _validation(entry.get("validation"), consumer, checks, latest, obs)
                summaries.append((entry["validation"]["evidence"],
                                  f"{name} absent from {consumer_id}: {exclusion['reason']}"))
                continue
            if applicability != "applicable" or "exclusion" in entry:
                raise EvidenceError(f"{name}/{consumer_id}: package applicability is unknown or contradictory")
            resolved = _text(entry.get("resolved"), f"{name}/{consumer_id}.resolved")
            tested = _text(entry.get("tested"), f"{name}/{consumer_id}.tested")
            if requested != resolved or resolved != tested:
                raise EvidenceError(f"{name}/{consumer_id}: requested {requested}, "
                                    f"resolved {resolved}, tested {tested}; "
                                    "requested target is not proven in this consumer")
            _validation(entry.get("validation"), consumer, checks, latest, obs)
            tested_consumers.add(consumer_id)
            summaries.append((entry["validation"]["evidence"],
                              f"{name} {requested} resolved and tested by {consumer_id}"))
        if seen != expected:
            raise EvidenceError(f"{name}: missing affected consumers {sorted(expected - seen)}")
        if any(consumers[c]["kind"] != "fixture" for c in expected) and not tested_consumers:
            raise EvidenceError(f"{name}: no installation consumer tested the requested target")
        covered.update(paths)
    changed = {f["filename"] for f in obs.files["data"] or []}
    missing = {p for p in changed if files[p]["role"] in CONSUMER_ROLES} - covered
    if missing:
        raise EvidenceError(f"changed dependency/fixture files lack updates: {sorted(missing)}")
    summaries.extend((entry["evidence"], f"{context}: {entry['applicability']}; "
                      f"scope {entry['scope']}; {entry['reason']}")
                     for (context, _), entry in checks.items())
    involved = sorted(p for p in changed
                      if files[p]["role"] in {"fixture", "source", "config"})
    return summaries, involved
