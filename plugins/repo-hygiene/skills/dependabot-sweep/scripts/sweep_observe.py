#!/usr/bin/env python3
"""Fetch one full observation of a PR for dependabot-sweep, Slice 4.

Read-only. Every HTTP call goes through the merge helper's bounded
`api_request` (gh_merge.py: per-call timeout, definitive vs ambiguous
failure split), so the helper stays the single transport for reads as
well as merges. Each observation section is fetched independently and
recorded as {"status", "data", "truncated", "error"}: a failed section
never aborts the others, and the evaluator's identity check decides what
an unreadable section means. If the pull itself is unreadable, nothing
else is fetched and the head is left empty rather than guessed.

Calls per observation: pull, files, reviews, one GraphQL (threads and
queue), check-runs, check-suites, combined status, branch protection,
branch rules, and one ruleset detail per distinct ruleset id.

Stdlib only.
"""

from __future__ import annotations

import os
import sys
import time
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import gh_merge  # noqa: E402
from sweep_core import utc_now  # noqa: E402
from sweep_evaluator import (  # noqa: E402
    EffectivePolicy, Observation, RequiredCheck, build_policy,
)

GRAPHQL_QUERY = (
    "query($o:String!,$r:String!,$n:Int!){repository(owner:$o,name:$r){"
    "pullRequest(number:$n){isInMergeQueue "
    "mergeQueueEntry{state position} autoMergeRequest{enabledAt} "
    "reviewThreads(first:100){pageInfo{hasNextPage}"
    "nodes{id isResolved isOutdated}}}}}"
)
SECTION_NAMES = ("pull", "files", "reviews", "threads", "check_runs",
                 "check_suites", "statuses", "queue")


def _section(data=None, status=200, truncated=False, error="") -> dict:
    return {"status": status, "data": data, "truncated": truncated,
            "error": error}


def _not_fetched(reason: str) -> dict:
    return _section(None, None, False, f"not fetched: {reason}")


def _guarded(deadline_epoch: float | None, fetch):
    """Run one fetch into a section: HTTP errors keep their status,
    transport failures have status None, a passed deadline fetches
    nothing."""
    if deadline_epoch and time.time() > deadline_epoch:
        return _section(None, None, False, "deadline passed before fetch")
    try:
        return fetch()
    except gh_merge.DefinitiveFailure as exc:
        return _section(None, exc.status or 500, False, str(exc))
    except gh_merge.AmbiguousFailure as exc:
        return _section(None, None, False, f"transport: {exc}")


def _get(path: str, token: str, timeout: float, params=None):
    _, parsed, headers = gh_merge.api_request("GET", path, token,
                                              params=params, timeout=timeout)
    return parsed, headers


def _paged(path: str, token: str, timeout: float, max_pages: int = 3) -> dict:
    """Collect a paginated list into one section; truncated when the page
    cap stops before the last page."""
    items: list = []
    url_path, query = path, {"per_page": "100"}
    for _ in range(max_pages):
        parsed, headers = _get(url_path, token, timeout, params=query)
        if not isinstance(parsed, list):
            raise gh_merge.DefinitiveFailure(f"GET {path} unexpected shape")
        items.extend(parsed)
        link = headers.get("Link", "") if headers else ""
        next_url = None
        for part in link.split(","):
            if 'rel="next"' in part:
                next_url = part.split(";")[0].strip().strip("<>")
        if not next_url:
            return _section(items)
        parsed_url = urllib.parse.urlparse(next_url)
        url_path = parsed_url.path
        query = dict(urllib.parse.parse_qsl(parsed_url.query))
    return _section(items, truncated=True)


def _counted(path: str, token: str, timeout: float, key: str) -> dict:
    """A {total_count, <key>: [...]} listing; truncated when the count
    exceeds what one page returned."""
    parsed, _ = _get(path, token, timeout, params={"per_page": "100"})
    if not isinstance(parsed, dict) or not isinstance(parsed.get(key), list):
        raise gh_merge.DefinitiveFailure(f"GET {path} unexpected shape")
    listed = parsed[key]
    total = parsed.get("total_count", len(listed))
    return _section(parsed, truncated=total > len(listed))


def _graphql(owner: str, repo: str, number: int, token: str,
             timeout: float) -> tuple:
    """Threads and queue state from one GraphQL call. An `errors` array
    makes both sections unreadable, never data."""
    _, parsed, _ = gh_merge.api_request(
        "POST", "/graphql", token,
        body={"query": GRAPHQL_QUERY,
              "variables": {"o": owner, "r": repo, "n": int(number)}},
        timeout=timeout)
    if not isinstance(parsed, dict) or parsed.get("errors"):
        messages = "; ".join(str(e.get("message", e))
                             for e in (parsed or {}).get("errors", [])) \
            if isinstance(parsed, dict) else "unexpected shape"
        bad = _section(None, None, False, f"graphql errors: {messages}")
        return bad, dict(bad)
    try:
        pull = parsed["data"]["repository"]["pullRequest"]
        threads = pull["reviewThreads"]
        nodes = threads["nodes"]
    except (TypeError, KeyError) as exc:
        bad = _section(None, None, False, f"graphql shape: {exc!r}")
        return bad, dict(bad)
    threads_section = _section(
        nodes, truncated=bool((threads.get("pageInfo") or {}).get("hasNextPage")))
    queue_section = _section({
        "isInMergeQueue": bool(pull.get("isInMergeQueue")),
        "mergeQueueEntry": pull.get("mergeQueueEntry"),
        "autoMergeRequest": pull.get("autoMergeRequest"),
    })
    return threads_section, queue_section


def fetch_observation(owner: str, repo: str, number: int, token: str,
                      op_timeout: float = 30.0,
                      deadline_epoch: float | None = None) -> Observation:
    """One full refresh of owner/repo#number, every section bound to the
    head the pull GET reported."""
    prefix = f"/repos/{owner}/{repo}"
    guard = lambda fetch: _guarded(deadline_epoch, fetch)  # noqa: E731
    pull = guard(lambda: _section(_get(f"{prefix}/pulls/{number}", token,
                                       op_timeout)[0]))
    observed_at = utc_now()
    if not (pull["status"] and 200 <= pull["status"] < 300
            and isinstance(pull["data"], dict)):
        reason = pull["error"] or f"pull status {pull['status']}"
        empty = {name: _not_fetched(f"pull unreadable ({reason})")
                 for name in SECTION_NAMES if name != "pull"}
        return Observation(head_sha="", observed_at=observed_at, pull=pull,
                           policy=EffectivePolicy(
                               known=False, reason="not fetched: pull "
                                                    "unreadable"),
                           **empty)
    head = (pull["data"].get("head") or {}).get("sha", "")
    base = (pull["data"].get("base") or {}).get("ref", "")
    files = guard(lambda: _paged(f"{prefix}/pulls/{number}/files", token,
                                 op_timeout))
    reviews = guard(lambda: _paged(f"{prefix}/pulls/{number}/reviews", token,
                                   op_timeout))
    graph = guard(lambda: _graphql(owner, repo, number, token, op_timeout))
    if isinstance(graph, tuple):
        threads, queue = graph
    else:  # the guard turned an exception into one section
        threads, queue = graph, dict(graph)
    check_runs = guard(lambda: _counted(
        f"{prefix}/commits/{head}/check-runs", token, op_timeout, "check_runs"))
    suites = guard(lambda: _counted(
        f"{prefix}/commits/{head}/check-suites", token, op_timeout,
        "check_suites"))
    if suites["status"] == 200 and isinstance(suites["data"], dict):
        suites = _section({str(s.get("id")): {"status": s.get("status"),
                                              "conclusion": s.get("conclusion")}
                           for s in suites["data"]["check_suites"]},
                          truncated=suites["truncated"])
    statuses = guard(lambda: _section(_get(f"{prefix}/commits/{head}/status",
                                           token, op_timeout)[0]))
    protection = guard(lambda: _section(_get(
        f"{prefix}/branches/{base}/protection", token, op_timeout)[0]))
    rules = guard(lambda: _section(_get(
        f"{prefix}/rules/branches/{base}", token, op_timeout)[0]))
    details: dict = {}
    if rules["status"] == 200 and isinstance(rules["data"], list):
        for item in rules["data"]:
            ruleset_id = item.get("ruleset_id")
            if ruleset_id is None or ruleset_id in details:
                continue
            details[ruleset_id] = guard(lambda rid=ruleset_id: _section(_get(
                f"{prefix}/rulesets/{rid}", token, op_timeout)[0]))
    policy = build_policy(protection, rules, details)
    return Observation(head_sha=head, observed_at=observed_at, pull=pull,
                       files=files, reviews=reviews, threads=threads,
                       check_runs=check_runs, check_suites=suites,
                       statuses=statuses, queue=queue, policy=policy)


def policy_to_dict(policy: EffectivePolicy) -> dict:
    data = dict(policy.__dict__)
    data["required_checks"] = [
        {"context": c.context, "producer_id": c.producer_id,
         "source": c.source} for c in policy.required_checks]
    return data


def policy_from_dict(data: dict) -> EffectivePolicy:
    data = dict(data)
    data["required_checks"] = [RequiredCheck(**c)
                               for c in data.get("required_checks", [])]
    return EffectivePolicy(**data)


def observation_to_dict(observation: Observation) -> dict:
    """JSON-safe form: `pr observe -o json` output, `pr evaluate --file`
    input. Check-suite ids are already strings."""
    return {"head_sha": observation.head_sha,
            "observed_at": observation.observed_at,
            **{name: getattr(observation, name) for name in SECTION_NAMES},
            "policy": policy_to_dict(observation.policy)}


def observation_from_dict(data: dict) -> Observation:
    return Observation(head_sha=data["head_sha"],
                       observed_at=data.get("observed_at", ""),
                       policy=policy_from_dict(data["policy"]),
                       **{name: data[name] for name in SECTION_NAMES})
