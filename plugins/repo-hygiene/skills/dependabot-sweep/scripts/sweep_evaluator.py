#!/usr/bin/env python3
"""Readiness evaluator for dependabot-sweep, Slice 2.

Five plain checks over one full observation of a PR, bound to an exact
head: Allowed? Is it what we think? Is it green? Did no one lose track?
Did it actually merge? Every input is plain data shaped like the GitHub
REST/GraphQL responses (verified 2026-09-22), so every path is testable
without the network. Stdlib only; never touches the network itself.

Observation sections use one shape: {"status": int|None, "data": ...,
"truncated": bool, "error": str}. status None means transport failure;
404 means absent where absence is meaningful; anything else non-2xx means
unreadable. Unknown never means "none".
"""

from __future__ import annotations

from dataclasses import dataclass, field


def _ok(section: dict) -> bool:
    status = section.get("status")
    return status is not None and 200 <= status < 300


@dataclass(frozen=True)
class RequiredCheck:
    """One required status check. Identity is (context, producer): when a
    producer id is given, only a run from that app satisfies it."""

    context: str
    producer_id: int | None = None
    source: str = ""


@dataclass
class EffectivePolicy:
    """The complete effective merge policy for a base branch (gate G04).

    Built from classic branch protection plus every active ruleset rule
    that applies to the branch. `known` is False whenever any part could
    not be read: unknown requirements do not mean none.
    """

    known: bool = True
    reason: str = ""
    required_checks: list = field(default_factory=list)
    strict: bool = False
    required_approvals: int = 0
    require_code_owner: bool = False
    require_thread_resolution: bool = False
    merge_queue: bool = False
    merge_queue_method: str = ""
    required_signatures: bool = False
    sources: list = field(default_factory=list)

    def fingerprint(self) -> dict:
        """Field-wise snapshot, so a later diff names what changed."""
        return {
            "known": self.known,
            "required_checks": tuple(sorted(
                (c.context, c.producer_id) for c in self.required_checks)),
            "strict": self.strict,
            "required_approvals": self.required_approvals,
            "require_code_owner": self.require_code_owner,
            "require_thread_resolution": self.require_thread_resolution,
            "merge_queue": self.merge_queue,
            "merge_queue_method": self.merge_queue_method,
            "required_signatures": self.required_signatures,
        }


def diff_fingerprints(before: dict, after: dict) -> list:
    """Names of fields whose value differs, in sorted order."""
    keys = set(before) | set(after)
    return sorted(k for k in keys if before.get(k) != after.get(k))


def _unknown(reason: str) -> EffectivePolicy:
    return EffectivePolicy(known=False, reason=reason)


def build_policy(protection: dict, branch_rules: dict,
                 rulesets: dict) -> EffectivePolicy:
    """Assemble the effective policy from three fetched sections.

    `protection`: GET /repos/{o}/{r}/branches/{b}/protection (404 = no
    classic protection). `branch_rules`: GET /repos/{o}/{r}/rules/branches/{b}
    (200 with [] = no rules; 404 or error = unreadable). `rulesets`: maps
    each ruleset_id referenced by the branch rules to its detail section
    (GET /repos/{o}/{r}/rulesets/{id}), which supplies enforcement.
    """
    policy = EffectivePolicy()
    if protection.get("status") == 404:
        pass
    elif _ok(protection) and isinstance(protection.get("data"), dict):
        _apply_protection(policy, protection["data"])
    else:
        return _unknown(f"branch protection unreadable "
                        f"(status {protection.get('status')!r})")
    if not (_ok(branch_rules) and isinstance(branch_rules.get("data"), list)):
        return _unknown(f"branch rules unreadable "
                        f"(status {branch_rules.get('status')!r})")
    if branch_rules.get("truncated"):
        return _unknown("branch rules truncated")
    for item in branch_rules["data"]:
        ruleset_id = item.get("ruleset_id")
        detail = rulesets.get(ruleset_id)
        if detail is None or not _ok(detail) \
                or not isinstance(detail.get("data"), dict):
            return _unknown(f"ruleset {ruleset_id} detail unreadable")
        if detail["data"].get("enforcement") != "active":
            continue
        _apply_rule(policy, item, ruleset_id)
    policy.required_checks = _dedupe(policy.required_checks)
    return policy


def _apply_protection(policy: EffectivePolicy, data: dict) -> None:
    policy.sources.append("branch_protection")
    rsc = data.get("required_status_checks") or {}
    policy.strict = policy.strict or bool(rsc.get("strict"))
    checks = rsc.get("checks")
    if checks is not None:
        for check in checks:
            policy.required_checks.append(RequiredCheck(
                check.get("context", ""), check.get("app_id"),
                "branch_protection"))
    else:
        # `contexts` is the closing-down predecessor of `checks`.
        for context in rsc.get("contexts") or []:
            policy.required_checks.append(RequiredCheck(
                context, None, "branch_protection"))
    reviews = data.get("required_pull_request_reviews") or {}
    policy.required_approvals = max(
        policy.required_approvals,
        int(reviews.get("required_approving_review_count") or 0))
    policy.require_code_owner = policy.require_code_owner or bool(
        reviews.get("require_code_owner_reviews"))
    conversation = data.get("required_conversation_resolution") or {}
    policy.require_thread_resolution = (policy.require_thread_resolution
                                        or bool(conversation.get("enabled")))


def _apply_rule(policy: EffectivePolicy, item: dict, ruleset_id) -> None:
    source = f"ruleset:{ruleset_id}"
    if source not in policy.sources:
        policy.sources.append(source)
    kind = item.get("type")
    params = item.get("parameters") or {}
    if kind == "required_status_checks":
        for check in params.get("required_status_checks") or []:
            policy.required_checks.append(RequiredCheck(
                check.get("context", ""), check.get("integration_id"),
                source))
        policy.strict = policy.strict or bool(
            params.get("strict_required_status_checks_policy"))
    elif kind == "pull_request":
        policy.required_approvals = max(
            policy.required_approvals,
            int(params.get("required_approving_review_count") or 0))
        policy.require_code_owner = policy.require_code_owner or bool(
            params.get("require_code_owner_review"))
        policy.require_thread_resolution = (
            policy.require_thread_resolution
            or bool(params.get("required_review_thread_resolution")))
    elif kind == "merge_queue":
        policy.merge_queue = True
        policy.merge_queue_method = str(params.get("merge_method", ""))
    elif kind == "required_signatures":
        policy.required_signatures = True


def _dedupe(checks: list) -> list:
    seen: dict = {}
    for check in checks:
        seen.setdefault((check.context, check.producer_id), check)
    return list(seen.values())


# ---------------------------------------------------------------------------
# The five checks
# ---------------------------------------------------------------------------

import hashlib  # noqa: E402
import os  # noqa: E402
import re  # noqa: E402
import sys  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sweep_core import State  # noqa: E402

SECTIONS = ("pull", "files", "reviews", "threads", "check_runs",
            "check_suites", "statuses", "queue")
GREEN = frozenset({"success", "neutral"})
FAILED_SUITE = frozenset({"failure", "cancelled", "timed_out",
                          "action_required", "startup_failure", "stale"})
# A reviewer bot reporting its own quota through a commit status is not CI.
REVIEWER_OUTAGE_RE = re.compile(
    r"rate.?limit|quota|could not review|review skipped|reviewer unavailable",
    re.IGNORECASE)

# code -> (severity, confidence, action_owner, resume_trigger, action)
REASON_DEFAULTS = {
    "K01": ("low", "high", "sweeper", "checks complete",
            "Observe until checks complete, then re-evaluate at this head."),
    "K02": ("low", "high", "sweeper", "after branch update",
            "Update the branch (authorized repair), then re-evaluate."),
    "K03": ("high", "medium", "pr-merge-flow", "after owner review",
            "Resolve the semantic conflict through pr-merge-flow; never "
            "auto-resolve it."),
    "K04": ("medium", "low", "ci-fix", "after diagnosis",
            "Diagnose the failing check (baseline vs regression) before any "
            "repair; CI is never waived."),
    "K05": ("medium", "high", "ci-fix", "base branch repaired",
            "Repair the base branch once for every PR it blocks; a baseline "
            "failure never waives required CI."),
    "K06": ("medium", "medium", "ci-fix", "environment restored",
            "Restore the CI environment, then re-run at the same head; never "
            "weaken the check."),
    "K07": ("medium", "high", "pr-merge-flow", "review resolved",
            "Resolve review state through pr-merge-flow; never merge over an "
            "open thread or change request."),
    "K08": ("medium", "high", "service owner", "reviewer service restored",
            "Required reviewer is unavailable; hold and disclose. Never route "
            "to ci-fix, never count as passing."),
    "K09": ("medium", "high", "sweeper", "next run",
            "Policy or permission gates the merge; report the exact gate."),
    "K10": ("low", "high", "sweeper", "queue result",
            "Queue acceptance is pending, not merged; observe the queue."),
    "K11": ("high", "high", "sweeper", "after reconcile",
            "Reconcile the repository read-only before any mutation."),
    "K12": ("high", "high", "sweeper", "next run",
            "Worker ran outside its lease; reschedule under a lease."),
    "K13": ("medium", "high", "sweeper", "re-observe",
            "Refresh the incomplete evidence at the same head, then "
            "re-evaluate."),
    "K14": ("low", "high", "sweeper", "next run",
            "Budget exhausted for this PR; continue in the next run."),
    "K15": ("medium", "medium", "pr-merge-flow", "owner decision",
            "Review is not converging; stop the fix loop and report the open "
            "findings."),
    "K16": ("low", "high", "owner", "owner decision",
            "Awaiting the owner's decision or the lifting of their hold."),
    "K17": ("low", "medium", "sweeper", "re-observe",
            "Transport failed before any mutation; re-observe and retry "
            "within budget."),
}


def files_digest(files: list) -> str:
    """Order-independent digest over (path, blob sha) of the PR's files."""
    lines = sorted(f"{f.get('filename', '')}\0{f.get('sha', '')}"
                   for f in files or [])
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ClassifierReceipt:
    """The classifier's dependency-only attestation, bound to an exact head
    and file set (gate G03). Evaluation refuses a receipt for any other
    head or file list: triviality is proven, not asserted."""

    head_sha: str
    files_digest: str
    file_count: int
    dependency_only: bool
    classifier: str
    at: str

    @classmethod
    def for_files(cls, head_sha: str, files: list, dependency_only: bool,
                  classifier: str, at: str) -> "ClassifierReceipt":
        return cls(head_sha, files_digest(files), len(files or []),
                   dependency_only, classifier, at)


@dataclass
class Authority:
    """What this worker may do to this card (gates G01, G10, G11)."""

    mode: str = "automated"  # inspect | automated | gated
    repairs: frozenset = frozenset()
    owner_hold: bool = False
    approved: bool = False
    deadline_epoch: float | None = None


@dataclass
class Tracking:
    """Whether anyone lost track (gate G09): the worker holds the repo lease
    and no sibling mutation in this repo has an unknown outcome."""

    lease_held: bool = True
    repo_quarantined: bool = False


@dataclass
class Observation:
    """One full refresh of a PR, every section bound to `head_sha`."""

    head_sha: str
    observed_at: str
    pull: dict
    files: dict
    reviews: dict
    threads: dict
    check_runs: dict
    check_suites: dict
    statuses: dict
    queue: dict
    policy: EffectivePolicy


@dataclass
class CheckResult:
    name: str
    passed: bool | None = None  # None: not evaluated (an earlier check failed)
    reason_code: str = ""
    reason_line: str = ""
    evidence: list = field(default_factory=list)


@dataclass
class Evaluation:
    """The verdict on one PR at one head, ready to become an outcome record."""

    head_sha: str
    state: State
    reason_code: str = ""
    reason_line: str = ""
    severity: str = "none"
    confidence: str = "high"
    action: str = ""
    action_owner: str = ""
    resume_trigger: str = ""
    merge_path: str = "none"  # put | queue | none
    checks: list = field(default_factory=list)
    evidence: list = field(default_factory=list)
    notes: list = field(default_factory=list)
    fingerprint: dict = field(default_factory=dict)
    decision: dict = field(default_factory=dict)
    resolved: dict = field(default_factory=dict)  # merged/closed by observation

    def to_outcome(self, card_id: str) -> dict:
        """Render as the outcome record `sweep_coordinator.apply_outcome`
        accepts, so evaluation and store never disagree on vocabulary."""
        if self.resolved:
            return {"card_id": card_id, **self.resolved}
        if self.state == State.READY:
            return {"card_id": card_id, "outcome": "ready",
                    "reason_line": self.reason_line,
                    "evidence": list(self.evidence)}
        record = {"card_id": card_id, "outcome": "hold",
                  "state": self.state.value,
                  "reason_code": self.reason_code,
                  "reason_line": self.reason_line,
                  "severity": self.severity, "confidence": self.confidence,
                  "evidence": list(self.evidence), "action": self.action,
                  "action_owner": self.action_owner,
                  "resume_trigger": self.resume_trigger}
        if self.state == State.NEEDS_OWNER:
            record["decision"] = dict(self.decision)
        return record


class _Hold(Exception):
    """Internal: a check decided the verdict."""

    def __init__(self, state: State, code: str, line: str, **over):
        super().__init__(line)
        self.state, self.code, self.line, self.over = state, code, line, over


class _Resolved(Exception):
    """Internal: observation shows the PR merged or closed."""

    def __init__(self, record: dict, line: str):
        super().__init__(line)
        self.record, self.line = record, line


def _ev(bucket: list, name: str, what: str, establishes: str,
        head: str) -> None:
    bucket.append({"id": f"EV-{name}-{len(bucket) + 1}", "what": what,
                   "establishes": establishes, "head": head[:12]})


def evaluate(observation: Observation, receipt: ClassifierReceipt,
             authority: Authority, tracking: Tracking, now: float,
             reviewer_contexts: set | None = None) -> Evaluation:
    """Run the five checks in dependency order and return the verdict.

    Identity (is it what we think?) and tracking (did no one lose track?)
    must hold before green is meaningful; green decides holds; allowed
    (may we?) decides whether READY carries a merge path, a preparation
    only, or an owner decision. "Did it actually merge?" is
    `verify_merged`, run on a fresh GET after any merge attempt.
    """
    reviewer_contexts = set(reviewer_contexts or ())
    result = Evaluation(head_sha=observation.head_sha, state=State.READY)
    result.fingerprint = fingerprint_of(observation)
    steps = (("identity", lambda: _identity(observation, receipt, result)),
             ("tracked", lambda: _tracked(tracking, result)),
             ("green", lambda: _green(observation, reviewer_contexts,
                                      result)),
             ("allowed", lambda: _allowed(authority, receipt, observation,
                                          now, result)))
    for name, step in steps:
        check = CheckResult(name=name)
        result.checks.append(check)
        try:
            step()
        except _Resolved as done:
            check.passed, check.reason_line = True, done.line
            result.resolved = done.record
            result.reason_line = done.line
            _finish_unevaluated(result, name)
            return result
        except _Hold as hold:
            check.passed, check.reason_code = False, hold.code
            check.reason_line = hold.line
            _apply_hold(result, hold)
            _finish_unevaluated(result, name)
            return result
        check.passed = True
        check.evidence = [e for e in result.evidence
                          if e["id"].startswith(f"EV-{name}-")]
    return result


def _finish_unevaluated(result: Evaluation, decided_at: str) -> None:
    names = ["identity", "tracked", "green", "allowed"]
    for name in names[names.index(decided_at) + 1:]:
        result.checks.append(CheckResult(name=name, passed=None,
                                         reason_line="not evaluated"))


def _apply_hold(result: Evaluation, hold: _Hold) -> None:
    severity, confidence, owner, resume, action = REASON_DEFAULTS[hold.code]
    result.state = hold.state
    result.reason_code = hold.code
    result.reason_line = hold.line
    result.severity = hold.over.get("severity", severity)
    result.confidence = hold.over.get("confidence", confidence)
    result.action_owner = hold.over.get("action_owner", owner)
    result.resume_trigger = hold.over.get("resume_trigger", resume)
    result.action = hold.over.get("action", action)
    result.merge_path = "none"
    result.decision = hold.over.get("decision", {})


# --- Check 2: is it what we think? -----------------------------------------

def _identity(obs: Observation, receipt: ClassifierReceipt,
              result: Evaluation) -> None:
    head = obs.head_sha
    for name in SECTIONS:
        section = getattr(obs, name)
        if not _ok(section):
            raise _Hold(State.BLOCKED, "K13",
                        f"{name} unreadable (status {section.get('status')!r}"
                        f"{', ' + section['error'] if section.get('error') else ''})")
        if section.get("truncated"):
            raise _Hold(State.BLOCKED, "K13", f"{name} truncated")
    runs = obs.check_runs["data"] or {}
    listed = runs.get("check_runs", [])
    if runs.get("total_count", len(listed)) > len(listed):
        raise _Hold(State.BLOCKED, "K13",
                    f"check_runs truncated: {runs.get('total_count')} total, "
                    f"{len(listed)} listed")
    pull = obs.pull["data"] or {}
    if pull.get("merged"):
        proof = verify_merged(obs.pull)
        if proof is None:
            raise _Hold(State.WAITING, "K13",
                        "GitHub reports merged without merge commit and "
                        "timestamp; re-observe")
        raise _Resolved({"outcome": "merged", "commit_sha": proof["commit"],
                         "merged_at": proof["at"]},
                        f"merged on GitHub at {proof['at']}")
    if pull.get("state") != "open":
        raise _Resolved({"outcome": "closed",
                         "reason": "PR closed on GitHub without merging"},
                        "closed on GitHub")
    observed_head = (pull.get("head") or {}).get("sha", "")
    if observed_head != head:
        raise _Hold(State.BLOCKED, "K13",
                    f"observation head {observed_head[:12]} does not match "
                    f"the evaluated head {head[:12]}")
    if receipt.head_sha != head:
        raise _Hold(State.BLOCKED, "K13",
                    f"classifier receipt is for head {receipt.head_sha[:12]}, "
                    f"not the observed head {head[:12]}")
    observed_files = obs.files["data"] or []
    digest = files_digest(observed_files)
    if digest != receipt.files_digest:
        raise _Hold(State.BLOCKED, "K13",
                    f"classifier receipt files digest does not match the "
                    f"observed files ({receipt.file_count} attested, "
                    f"{len(observed_files)} observed)")
    if pull.get("draft"):
        raise _Hold(State.BLOCKED, "K09", "PR is a draft")
    _ev(result.evidence, "identity", f"GET pull at {obs.observed_at}",
        f"open PR at head {head[:12]}, base {pull.get('base', {}).get('ref')}"
        f"@{(pull.get('base') or {}).get('sha', '')[:12]}", head)
    _ev(result.evidence, "identity",
        f"classifier receipt by {receipt.classifier} at {receipt.at}",
        f"{receipt.file_count} files, digest {digest[:12]}, "
        f"dependency_only={receipt.dependency_only}", head)


# --- Check 4: did no one lose track? ---------------------------------------

def _tracked(tracking: Tracking, result: Evaluation) -> None:
    if tracking.repo_quarantined:
        raise _Hold(State.BLOCKED, "K11",
                    "repository quarantined: a sibling mutation outcome is "
                    "unknown; reconcile before any retry")
    if not tracking.lease_held:
        raise _Hold(State.BLOCKED, "K12",
                    "evaluating without holding the repository lease")
    _ev(result.evidence, "tracked", "lease and quarantine state",
        "worker holds the repository lease; no unknown sibling mutation",
        result.head_sha)


# --- Check 3: is it green? -------------------------------------------------

def _latest_runs(check_runs: dict) -> dict:
    """Latest run per check name: a rerun supersedes its predecessor."""
    latest: dict = {}
    for run in (check_runs or {}).get("check_runs", []):
        name = run.get("name", "")
        key = (run.get("completed_at") or "", run.get("id") or 0)
        if name not in latest or key > latest[name][0]:
            latest[name] = (key, run)
    return {name: run for name, (_, run) in latest.items()}


def _green(obs: Observation, reviewer_contexts: set,
           result: Evaluation) -> None:
    head = obs.head_sha
    policy = obs.policy
    if not policy.known:
        raise _Hold(State.BLOCKED, "K09",
                    f"effective policy unreadable: {policy.reason}")
    queue = obs.queue["data"] or {}
    entry = queue.get("mergeQueueEntry") or {}
    if queue.get("isInMergeQueue") or entry:
        raise _Hold(State.WAITING, "K10",
                    f"in merge queue ({entry.get('state', 'QUEUED')}); "
                    f"queue acceptance is pending, not merged")
    if queue.get("autoMergeRequest"):
        raise _Hold(State.WAITING, "K10",
                    "auto-merge armed; GitHub merges when ready. Observe, "
                    "never PUT")
    latest = _latest_runs(obs.check_runs["data"])
    suites = obs.check_suites["data"] or {}
    statuses = {s.get("context", ""): s
                for s in (obs.statuses["data"] or {}).get("statuses", [])}
    pending, red, outages, skipped_ok = [], [], [], []
    for name, run in latest.items():
        if run.get("status") != "completed":
            pending.append(name)
            continue
        conclusion = run.get("conclusion")
        if conclusion in GREEN:
            continue
        if conclusion == "skipped":
            suite_id = (run.get("check_suite") or {}).get("id")
            suite = suites.get(suite_id) or suites.get(str(suite_id)) or {}
            if suite.get("conclusion") in FAILED_SUITE:
                red.append(f"{name} (skipped after a failed prerequisite in "
                           f"its check suite)")
            else:
                skipped_ok.append(name)
            continue
        red.append(f"{name} ({conclusion})")
    for context, status in statuses.items():
        state = status.get("state")
        if state == "success":
            continue
        configured = context in reviewer_contexts
        worded = bool(REVIEWER_OUTAGE_RE.search(status.get("description", "")))
        if state == "pending":
            pending.append(context)
        elif configured or worded:
            outages.append((context, status.get("description", ""),
                            configured))
        else:
            red.append(f"status {context} ({state})")
    required_contexts = {c.context for c in policy.required_checks}
    for context, description, configured in outages:
        if context in required_contexts:
            raise _Hold(State.BLOCKED, "K08",
                        f"required reviewer {context} unavailable: "
                        f"{description or 'no description'}")
        if not configured:
            # Rate-limit wording proves nothing about who produced the
            # status: hold with low confidence rather than pass a build
            # failure as an optional reviewer's outage.
            raise _Hold(State.BLOCKED, "K08",
                        f"status {context} failed with reviewer-outage "
                        f"wording ({description or 'no description'}) but "
                        f"is not a configured reviewer context",
                        confidence="low",
                        action="Confirm the producer: configure it under "
                               "reviewer_contexts if it is a reviewer bot, "
                               "otherwise treat the failure as CI red.")
        result.notes.append(f"reviewer {context} unavailable "
                            f"({description or 'no description'}); the PR "
                            f"is correspondingly less reviewed")
    for req in policy.required_checks:
        run = latest.get(req.context)
        status = statuses.get(req.context)
        if run is None and status is not None and status.get("state") == "success":
            continue
        if run is None:
            if status is None or status.get("state") != "pending":
                raise _Hold(State.WAITING, "K01",
                            f"required check {req.context} has no run on "
                            f"this head yet")
            continue  # pending status, reported below
        if req.producer_id is not None \
                and (run.get("app") or {}).get("id") != req.producer_id:
            raise _Hold(State.WAITING, "K01",
                        f"required check {req.context} has no run from the "
                        f"required producer (app {req.producer_id})")
    if red:
        raise _Hold(State.BLOCKED, "K04",
                    f"applicable check failed on head {head[:12]}: "
                    f"{', '.join(red)}; attribution pending (baseline vs "
                    f"regression is a diagnosis, not a guess)")
    if pending:
        raise _Hold(State.WAITING, "K01",
                    f"checks pending: {', '.join(sorted(pending))}")
    reviews = obs.reviews["data"] or []
    decisive: dict = {}
    for item in sorted(reviews, key=lambda r: r.get("submitted_at", "")):
        state = item.get("state")
        if state in ("APPROVED", "CHANGES_REQUESTED", "DISMISSED"):
            decisive[(item.get("user") or {}).get("login", "?")] = state
    blockers = sorted(u for u, s in decisive.items()
                      if s == "CHANGES_REQUESTED")
    if blockers:
        raise _Hold(State.BLOCKED, "K07",
                    f"changes requested by {', '.join(blockers)}")
    approvals = sum(1 for s in decisive.values() if s == "APPROVED")
    if approvals < policy.required_approvals:
        raise _Hold(State.BLOCKED, "K07",
                    f"{policy.required_approvals} approving review(s) "
                    f"required, {approvals} present")
    unresolved = sorted(t.get("id", "?") for t in (obs.threads["data"] or [])
                        if not t.get("isResolved", False))
    if unresolved:
        raise _Hold(State.BLOCKED, "K07",
                    f"unresolved review threads: {', '.join(unresolved)}")
    pull = obs.pull["data"] or {}
    mergeable, ms = pull.get("mergeable"), pull.get("mergeable_state")
    if mergeable is None or ms == "unknown":
        raise _Hold(State.WAITING, "K13",
                    "mergeability not yet computed by GitHub; re-observe")
    if ms == "dirty" or mergeable is False:
        raise _Hold(State.BLOCKED, "K02", "merge conflict with the base branch")
    if ms == "behind":
        raise _Hold(State.BLOCKED, "K02",
                    "base moved; branch update required before merge")
    if ms == "unstable":
        raise _Hold(State.WAITING, "K01",
                    "GitHub reports a non-passing commit status (unstable); "
                    "re-observe")
    if ms == "blocked":
        raise _Hold(State.BLOCKED, "K09",
                    "GitHub reports the merge blocked by a requirement not "
                    "visible in the effective policy")
    if ms != "clean":
        raise _Hold(State.BLOCKED, "K09",
                    f"mergeable_state {ms!r} is not clean")
    _ev(result.evidence, "green",
        f"check-runs, statuses, reviews, threads at {obs.observed_at}",
        f"{len(latest)} check(s) green"
        f"{', ' + str(len(skipped_ok)) + ' legitimately skipped' if skipped_ok else ''}"
        f"; {approvals} approval(s); 0 unresolved threads; "
        f"mergeable_state clean; policy sources {policy.sources or ['none']}",
        head)


# --- Check 1: allowed? -----------------------------------------------------

def _allowed(authority: Authority, receipt: ClassifierReceipt,
             obs: Observation, now: float, result: Evaluation) -> None:
    head = obs.head_sha
    if authority.deadline_epoch is not None and now > authority.deadline_epoch:
        raise _Hold(State.WAITING, "K14", "per-PR budget exhausted")
    if authority.owner_hold:
        raise _Hold(State.WAITING, "K16", "owner hold in effect")
    if not receipt.dependency_only:
        raise _Hold(State.BLOCKED, "K09",
                    "diff is not dependency-only per the classifier; involved "
                    "preparation goes through pr-merge-flow",
                    action_owner="pr-merge-flow",
                    action="Prepare through pr-merge-flow (triage, fix, "
                           "reply); re-evaluate at the resulting head.",
                    resume_trigger="preparation complete")
    path = "queue" if obs.policy.merge_queue else "put"
    if authority.mode == "inspect":
        result.merge_path = "none"
        result.reason_line = (f"eligible at head {head[:12]}; inspect mode "
                              f"performs no merge")
    elif authority.mode == "gated" and not authority.approved:
        raise _Hold(State.NEEDS_OWNER, "K16",
                    f"eligible at head {head[:12]}; gated mode requires "
                    f"your approval to merge",
                    decision={
                        "why": "gated mode: every merge needs an explicit "
                               "owner approval",
                        "approve_effect": f"merge at head {head[:12]} via "
                                          f"{path} after a fresh refresh",
                        "decline_effect": "hold; the PR stays open and "
                                          "unmerged",
                        "recommendation": "APPROVE"})
    else:
        result.merge_path = path
        result.reason_line = (f"eligible at head {head[:12]}; merge via "
                              f"{path}")
    _ev(result.evidence, "allowed",
        f"authority mode={authority.mode} approved={authority.approved}",
        f"merge path {result.merge_path}; repairs "
        f"{sorted(authority.repairs) or 'none'}", head)


# --- Check 5: did it actually merge? ---------------------------------------

def verify_merged(pull_section: dict) -> dict | None:
    """Read a fresh GET of the PR. Returns {"merged": True, "commit", "at"}
    on complete evidence, {"merged": False} when clearly unmerged, and None
    when the evidence is unreadable or incomplete (ambiguous, never a
    success). Queue acceptance and auto-merge arming are not merges."""
    if not _ok(pull_section) or not isinstance(pull_section.get("data"), dict):
        return None
    pull = pull_section["data"]
    if pull.get("merged") is True:
        commit, at = pull.get("merge_commit_sha"), pull.get("merged_at")
        if not commit or not at:
            return None
        return {"merged": True, "commit": commit, "at": at}
    if pull.get("merged") is False:
        return {"merged": False}
    return None


# --- Readiness fingerprint (T05) -------------------------------------------

def fingerprint_of(obs: Observation) -> dict:
    """Field-wise snapshot of everything a readiness verdict depends on."""
    pull = (obs.pull.get("data") if _ok(obs.pull) else None) or {}
    latest = _latest_runs(obs.check_runs.get("data")
                          if _ok(obs.check_runs) else {})
    threads = (obs.threads.get("data") if _ok(obs.threads) else None) or []
    statuses = ((obs.statuses.get("data") if _ok(obs.statuses) else None)
                or {}).get("statuses", [])
    reviews = (obs.reviews.get("data") if _ok(obs.reviews) else None) or []
    decisive: dict = {}
    for item in sorted(reviews, key=lambda r: r.get("submitted_at", "")):
        if item.get("state") in ("APPROVED", "CHANGES_REQUESTED", "DISMISSED"):
            decisive[(item.get("user") or {}).get("login", "?")] = item["state"]
    queue = (obs.queue.get("data") if _ok(obs.queue) else None) or {}
    return {
        "head_sha": obs.head_sha,
        "base_sha": (pull.get("base") or {}).get("sha", ""),
        "unresolved_threads": tuple(sorted(
            t.get("id", "?") for t in threads if not t.get("isResolved"))),
        "check_states": tuple(sorted(
            (name, run.get("status"), run.get("conclusion"))
            for name, run in latest.items())),
        "statuses": tuple(sorted((s.get("context", ""), s.get("state"))
                                 for s in statuses)),
        "reviews": tuple(sorted(decisive.items())),
        "mergeable_state": pull.get("mergeable_state"),
        "queue": (bool(queue.get("isInMergeQueue")),
                  (queue.get("mergeQueueEntry") or {}).get("state"),
                  bool(queue.get("autoMergeRequest"))),
        "policy": obs.policy.fingerprint(),
    }


def stale_reasons(evaluation: Evaluation, fresh: Observation) -> list:
    """Names of the readiness inputs that changed since `evaluation`.
    Any non-empty result invalidates the old verdict; re-evaluate."""
    return diff_fingerprints(evaluation.fingerprint, fingerprint_of(fresh))
