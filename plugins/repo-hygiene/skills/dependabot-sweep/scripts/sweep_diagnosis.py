#!/usr/bin/env python3
"""Failure diagnosis for dependabot-sweep, Slice 3 (S3).

A red check on a PR head is attributed only by matched controls: the same
workflow, job, matrix cell, command, toolchain, environment, and inputs,
run on the base revision. Unrelated files never prove a pre-existing
failure; only a matched baseline does. Every verdict still holds the PR:
a baseline failure never waives required CI, and a transient failure
re-evaluates rather than passing.

Stdlib only. Controls enter as plain data taken from check-run / job
metadata, so every path is testable without the network.
"""

from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass, field

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sweep_core import State  # noqa: E402

# Conditions a baseline must share with the candidate to be a control.
MATCH_FIELDS = ("workflow", "job", "matrix", "command", "toolchain",
                "environment", "inputs")
PASSED = frozenset({"success", "neutral"})
# Failure signatures that name the runner or network, not the code under
# test. A small explicit table: anything else is attributed by controls.
ENVIRONMENT_SIGNATURES = (
    (re.compile(r"No space left on device|ENOSPC", re.I), "disk full"),
    (re.compile(r"Could not resolve host|Temporary failure in name "
                r"resolution|getaddrinfo", re.I), "DNS resolution"),
    (re.compile(r"lost communication with the server|runner has received "
                r"a shutdown signal", re.I), "runner lost"),
    (re.compile(r"Connection reset by peer|ECONNRESET", re.I),
     "network reset"),
)


@dataclass(frozen=True)
class Control:
    """One check execution: where it ran, under what conditions, and how
    it ended. `signature` is the normalized first failure line."""

    revision: str
    ref_kind: str  # head | merge (candidate) or base (baseline)
    workflow: str
    job: str
    conclusion: str
    matrix: str = ""
    attempt: int = 1
    command: str = ""
    toolchain: str = ""
    environment: str = ""
    inputs: str = ""
    signature: str = ""
    at: str = ""
    url: str = ""


@dataclass
class Diagnosis:
    """A diagnosis, ready to become a hold outcome record."""

    state: State
    reason_code: str
    reason_line: str
    severity: str
    confidence: str
    action_owner: str
    resume_trigger: str
    action: str
    evidence: list = field(default_factory=list)
    mismatched: list = field(default_factory=list)
    incident: dict = field(default_factory=dict)

    def to_outcome(self, card_id: str) -> dict:
        record = {"card_id": card_id, "outcome": "hold",
                  "state": self.state.value, "reason_code": self.reason_code,
                  "reason_line": self.reason_line, "severity": self.severity,
                  "confidence": self.confidence,
                  "evidence": list(self.evidence), "action": self.action,
                  "action_owner": self.action_owner,
                  "resume_trigger": self.resume_trigger}
        if self.incident:
            record["incident"] = dict(self.incident)
        return record


def mismatches(baseline: Control, candidate: Control) -> list:
    """Conditions on which the two runs differ, in MATCH_FIELDS order."""
    return [name for name in MATCH_FIELDS
            if getattr(baseline, name) != getattr(candidate, name)]


def _evidence(control: Control, role: str) -> dict:
    return {"id": f"EV-diag-{role}", "what":
            f"{control.workflow}/{control.job}"
            f"{' [' + control.matrix + ']' if control.matrix else ''} "
            f"attempt {control.attempt} on {control.ref_kind} "
            f"{control.revision[:12]}: {control.conclusion}",
            "establishes": control.signature or "no failure signature",
            "at": control.at, "link": control.url}


def _environment(signature: str) -> str:
    for pattern, label in ENVIRONMENT_SIGNATURES:
        if pattern.search(signature or ""):
            return label
    return ""


def diagnose(candidate: Control, baseline: Control | None = None,
             retry: Control | None = None) -> Diagnosis:
    """Attribute one failed candidate run.

    K17 transient: a same-head retry under matched conditions passed; the
        mechanism stays unknown and the PR re-evaluates (WAITING).
    K06 environment: the failure signature names the runner or network.
    K05 baseline: a matched base-revision run fails with the same
        signature. One shared incident per (base revision, job, signature).
    K04 regression, high confidence: a matched base-revision run passed.
    K04 inconclusive, low confidence: no baseline, a baseline on the same
        revision, unmatched conditions, or a different failure signature.
    """
    if candidate.conclusion in PASSED:
        raise ValueError("diagnosis needs a failed candidate run")
    if candidate.ref_kind not in ("head", "merge"):
        raise ValueError(f"candidate must run on the PR head or merge "
                         f"revision, not {candidate.ref_kind!r}")
    evidence = [_evidence(candidate, "candidate")]
    if retry is not None and retry.revision == candidate.revision \
            and not mismatches(retry, candidate) \
            and retry.attempt > candidate.attempt \
            and retry.conclusion in PASSED:
        evidence.append(_evidence(retry, "retry"))
        return Diagnosis(
            State.WAITING, "K17",
            f"{candidate.job} failed then passed on retry at the same head "
            f"{candidate.revision[:12]}; transient, mechanism unknown",
            "low", "medium", "sweeper", "re-evaluate",
            "Re-evaluate at this head; a green retry is evidence of "
            "transience, not a waiver.", evidence)
    environment = _environment(candidate.signature)
    if environment:
        return Diagnosis(
            State.BLOCKED, "K06",
            f"{candidate.job} failed on {environment}: "
            f"{candidate.signature}",
            "medium", "medium", "ci-fix", "environment restored",
            "Restore the CI environment, then re-run at the same head; "
            "never weaken the check.", evidence)
    mismatched: list = []
    if baseline is None:
        gap = "no baseline control was run"
    elif baseline.ref_kind != "base" or baseline.revision == candidate.revision:
        gap = "the baseline did not run on a distinct base revision"
    else:
        evidence.append(_evidence(baseline, "baseline"))
        mismatched = mismatches(baseline, candidate)
        if mismatched:
            gap = (f"baseline conditions differ on "
                   f"{', '.join(mismatched)}")
        elif baseline.conclusion in PASSED:
            return Diagnosis(
                State.BLOCKED, "K04",
                f"{candidate.job} fails on head {candidate.revision[:12]} "
                f"and passes on base {baseline.revision[:12]} under "
                f"matched conditions: introduced by this PR",
                "medium", "high", "ci-fix", "after repair",
                "Repair on the PR branch within the repair permissions, or "
                "hand to the owner; CI is never waived.", evidence,
                mismatched)
        elif baseline.signature == candidate.signature:
            key = (f"{baseline.revision}:{baseline.workflow}/{baseline.job}"
                   f"[{baseline.matrix}]:{baseline.signature}")
            return Diagnosis(
                State.BLOCKED, "K05",
                f"{candidate.job} fails identically on base "
                f"{baseline.revision[:12]} under matched conditions: "
                f"pre-existing baseline failure; still blocks",
                "medium", "high", "ci-fix", "base branch repaired",
                "Repair the base branch once for every PR it blocks; a "
                "baseline failure never waives required CI.", evidence,
                mismatched,
                {"key": key,
                 "claim": f"base {baseline.revision[:12]} fails "
                          f"{baseline.workflow}/{baseline.job}: "
                          f"{baseline.signature}"})
        else:
            gap = "base and head fail with different signatures"
    return Diagnosis(
        State.BLOCKED, "K04",
        f"{candidate.job} failed on head {candidate.revision[:12]}; "
        f"attribution inconclusive: {gap}",
        "medium", "low", "ci-fix", "after diagnosis",
        "Run a matched baseline control before any repair; CI is never "
        "waived.", evidence, mismatched)
