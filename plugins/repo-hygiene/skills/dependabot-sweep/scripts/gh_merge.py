#!/usr/bin/env python3
"""Bounded, SHA-bound Dependabot merge helper.

One invocation merges at most one PR. Every HTTP call carries its own
timeout; there is no shell kill-watchdog to trust. A timed-out merge is
reported as UNKNOWN and reconciled read-only -- never blind-retried.

Exit codes:
  0  merged (confirmed merge evidence)
  10 deferred (preflight failed: pending/red/dirty/reviews/nontrivial/queue)
  11 unknown (ambiguous outcome: hold the repo mutation slot, human reconciles)
  12 usage/config error (fail closed)

Progress log lines (appended before blocking work and after each outcome):
  ts=<epoch> event=start|result repo=<o/r> pr=<n> phase=<p> head=<sha>
  deadline=<epoch> outcome=<merged|deferred|unknown> reason=<...>
"""

import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

DEFAULT_OP_TIMEOUT = int(os.environ.get("GH_MERGE_OP_TIMEOUT", "30"))
DEFAULT_PR_BUDGET = int(os.environ.get("GH_MERGE_PR_BUDGET_SECS", "600"))
API_BASE = os.environ.get("GH_MERGE_API_BASE", "https://api.github.com").rstrip("/")
TOKEN_ENV = "GH_MERGE_TOKEN"


class DefinitiveFailure(Exception):
    """The server answered: no merge happened, do not retry."""


class AmbiguousFailure(Exception):
    """Transport failed around the PUT: the merge may or may not have applied."""


def log_line(progress_log, **fields):
    line = " ".join(f"{k}={v}" for k, v in fields.items())
    with open(progress_log, "a", encoding="utf-8") as handle:
        handle.write(f"ts={int(time.time())} {line}\n")


def get_token():
    token = os.environ.get(TOKEN_ENV, "")
    if token:
        return token
    env = dict(os.environ, GH_PROMPT_DISABLED="1")
    try:
        completed = subprocess.run(
            ["gh", "auth", "token"], capture_output=True, text=True,
            timeout=15, env=env, check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise DefinitiveFailure(f"credential acquisition failed: {exc}") from exc
    token = (completed.stdout or "").strip()
    if completed.returncode != 0 or not token:
        raise DefinitiveFailure("credential acquisition failed: no token")
    return token


def api_request(method, path, token, body=None, params=None, timeout=None):
    """One bounded HTTP call. Returns (status, json_or_none, headers).

    Raises DefinitiveFailure on HTTP error responses (server answered),
    AmbiguousFailure on transport errors (timeouts, resets, truncations).
    """
    timeout = DEFAULT_OP_TIMEOUT if timeout is None else timeout
    url = API_BASE + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    data = None
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "dependabot-sweep-gh-merge",
    }
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
            status = response.status
            resp_headers = response.headers
    except urllib.error.HTTPError as exc:
        try:
            detail = exc.read().decode("utf-8", "replace")[:200]
        except (OSError, ValueError):
            detail = ""
        raise DefinitiveFailure(
            f"{method} {path} -> HTTP {exc.code} {detail}") from exc
    except (urllib.error.URLError, socket.timeout, TimeoutError,
            ConnectionError, OSError) as exc:
        raise AmbiguousFailure(f"{method} {path} transport failure: {exc}") from exc
    try:
        parsed = json.loads(raw.decode("utf-8")) if raw else None
    except (ValueError, UnicodeDecodeError) as exc:
        raise AmbiguousFailure(f"{method} {path} truncated response") from exc
    return status, parsed, resp_headers


def paged_get(path, token, params=None, max_pages=3):
    """Collect a paginated REST list. Returns (items, truncated)."""
    items = []
    url_path, query = path, dict(params or {})
    for _ in range(max_pages):
        status, parsed, headers = api_request("GET", url_path, token, params=query)
        if not isinstance(parsed, list):
            raise DefinitiveFailure(f"GET {path} unexpected shape")
        items.extend(parsed)
        link = headers.get("Link", "") if headers else ""
        next_url = None
        for part in link.split(","):
            if 'rel="next"' in part:
                next_url = part.split(";")[0].strip().strip("<>")
        if not next_url:
            return items, False
        parsed_url = urllib.parse.urlparse(next_url)
        url_path, query = parsed_url.path, dict(
            urllib.parse.parse_qsl(parsed_url.query))
    return items, True


def check_deadline(deadline, what):
    if time.time() > deadline:
        raise DefinitiveFailure(f"per-PR budget exceeded at {what}")


def preflight(owner, repo, pr, token, assert_trivial, deadline, progress_log):
    """Returns (head_sha, base_ref, base_sha). Raises DefinitiveFailure."""
    repo_id = f"{owner}/{repo}"
    check_deadline(deadline, "preflight/pr")
    _, pull, _ = api_request("GET", f"/repos/{owner}/{repo}/pulls/{pr}", token)
    if pull.get("state") != "open" or pull.get("merged"):
        raise DefinitiveFailure("PR is not open")
    if pull.get("draft"):
        raise DefinitiveFailure("PR is a draft")
    head_sha = pull["head"]["sha"]
    base_ref = pull["base"]["ref"]
    base_sha = pull["base"]["sha"]

    check_deadline(deadline, "preflight/files")
    files, truncated = paged_get(f"/repos/{owner}/{repo}/pulls/{pr}/files", token,
                                 params={"per_page": "100"})
    if truncated:
        raise DefinitiveFailure("diff too large to verify (page cap)")
    if not assert_trivial:
        raise DefinitiveFailure("triviality not asserted by classifier")
    if not files:
        raise DefinitiveFailure("empty diff")

    check_deadline(deadline, "preflight/reviews")
    reviews, truncated = paged_get(
        f"/repos/{owner}/{repo}/pulls/{pr}/reviews", token,
        params={"per_page": "100"})
    if truncated:
        raise DefinitiveFailure("review list too large to verify (page cap)")
    latest = {}
    for review in sorted(reviews, key=lambda r: r.get("submitted_at", "")):
        user = (review.get("user") or {}).get("login", "?")
        latest[user] = review.get("state")
    blockers = [u for u, s in latest.items() if s == "CHANGES_REQUESTED"]
    if blockers:
        raise DefinitiveFailure(f"change requests outstanding: {blockers}")
    if any(s == "COMMENTED" for s in latest.values()):
        raise DefinitiveFailure("unresolved review feedback possible")

    check_deadline(deadline, "preflight/threads")
    _, threads, _ = api_request(
        "POST", "/graphql", token,
        body={"query": (
            "query($o:String!,$r:String!,$n:Int!){repository(owner:$o,name:$r){"
            "pullRequest(number:$n){reviewThreads(first:100){nodes{isResolved}}}}}"
        ), "variables": {"o": owner, "r": repo, "n": int(pr)}})
    try:
        nodes = (threads["data"]["repository"]["pullRequest"]
                 ["reviewThreads"]["nodes"])
    except (TypeError, KeyError) as exc:
        raise DefinitiveFailure("review-thread state unreadable") from exc
    if any(not node.get("isResolved", True) for node in nodes):
        raise DefinitiveFailure("unresolved review threads")

    check_deadline(deadline, "preflight/checks")
    _, runs, _ = api_request(
        "GET", f"/repos/{owner}/{repo}/commits/{head_sha}/check-runs", token,
        params={"per_page": "100"})
    run_list = runs.get("check_runs", []) if isinstance(runs, dict) else []
    pending, failed = [], []
    for run in run_list:
        if run.get("status") != "completed":
            pending.append(run.get("name", "?"))
        elif run.get("conclusion") not in ("success", "skipped", "neutral"):
            failed.append(run.get("name", "?"))
    _, combined, _ = api_request(
        "GET", f"/repos/{owner}/{repo}/commits/{head_sha}/status", token)
    combined_state = (combined or {}).get("state", "pending")
    if failed or combined_state == "failure":
        raise DefinitiveFailure(f"failing checks: {failed or combined_state}")
    try:
        _, protection, _ = api_request(
            "GET", f"/repos/{owner}/{repo}/branches/{base_ref}/protection",
            token)
        required = (((protection or {}).get("required_status_checks") or {})
                    .get("contexts", []))
    except DefinitiveFailure as exc:
        if "HTTP 404" in str(exc):
            required = []
        else:
            raise
    if required:
        green_names = {r.get("name", "") for r in run_list
                       if r.get("status") == "completed"
                       and r.get("conclusion") in ("success", "skipped")}
        green_names |= {s.get("context", "") for s in
                        (combined or {}).get("statuses", [])
                        if s.get("state") == "success"}
        missing = [c for c in required if c not in green_names]
        if missing:
            raise DefinitiveFailure(f"required checks not green: {missing}")
    elif pending or combined_state != "success":
        if not run_list and not (combined or {}).get("statuses", []):
            pass  # No CI configured at all: nothing required.
        else:
            raise DefinitiveFailure("checks pending")

    check_deadline(deadline, "preflight/mergeable")
    mergeable = pull.get("mergeable")
    if mergeable is None:
        time.sleep(5)
        check_deadline(deadline, "preflight/mergeable-recheck")
        _, pull, _ = api_request(
            "GET", f"/repos/{owner}/{repo}/pulls/{pr}", token)
        mergeable = pull.get("mergeable")
        if pull["head"]["sha"] != head_sha:
            raise DefinitiveFailure("head changed during preflight")
    if not mergeable or pull.get("mergeable_state") != "clean":
        raise DefinitiveFailure(
            f"not mergeable: state={pull.get('mergeable_state')}")

    check_deadline(deadline, "preflight/queue")
    try:
        _, rulesets, _ = api_request(
            "GET", f"/repos/{owner}/{repo}/rulesets", token,
            params={"includes_parents": "true"})
    except DefinitiveFailure as exc:
        if "HTTP 404" in str(exc):
            rulesets = []  # No rulesets API: no merge queue support.
        else:
            raise
    for ruleset in rulesets or []:
        if ruleset.get("enforcement") != "active":
            continue
        if any(rule.get("type") == "merge_queue"
               for rule in ruleset.get("rules", [])):
            raise DefinitiveFailure("merge queue required: unsupported path")

    log_line(progress_log, event="preflight", repo=repo_id, pr=pr,
             phase="ok", head=head_sha[:12], deadline=int(deadline),
             outcome="pass", reason="eligible")
    return head_sha, base_ref, base_sha


def merge_put(owner, repo, pr, head_sha, method, token):
    """Returns body dict on success. Definitive vs ambiguous split enforced."""
    status, body, _ = api_request(
        "PUT", f"/repos/{owner}/{repo}/pulls/{pr}/merge", token,
        body={"sha": head_sha, "merge_method": method})
    if status not in (200, 201):
        raise DefinitiveFailure(f"merge PUT -> HTTP {status}")
    if not isinstance(body, dict) or body.get("merged") is not True:
        raise DefinitiveFailure(f"merge not applied: {body}")
    return body


def reconcile(owner, repo, pr, head_sha, token, deadline):
    """Bounded read-only reconcile. Returns True if merged confirmed."""
    for attempt in range(3):
        check_deadline(deadline, f"reconcile/{attempt}")
        try:
            _, pull, _ = api_request(
                "GET", f"/repos/{owner}/{repo}/pulls/{pr}", token)
        except AmbiguousFailure:
            time.sleep(5)
            continue
        if pull.get("merged"):
            return True
        if pull.get("head", {}).get("sha") != head_sha:
            return False  # Changed under us: quarantine, do not retry.
        time.sleep(5)
    return False


def self_test():
    """Prove bounded HTTP behavior against a controllable local endpoint."""
    import threading
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == "/slow":
                time.sleep(DEFAULT_OP_TIMEOUT + 10)
            body = b'{"ok": true}'
            self.send_response(200)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            try:
                self.wfile.write(body)
            except (BrokenPipeError, ConnectionResetError):
                pass

        def log_message(self, *args):
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    failures = []
    global API_BASE
    saved_base = API_BASE
    try:
        API_BASE = f"http://127.0.0.1:{port}"
        start = time.monotonic()
        try:
            api_request("GET", "/slow", "test", timeout=2)
            failures.append("slow endpoint did not time out")
        except AmbiguousFailure:
            elapsed = time.monotonic() - start
            if elapsed > 10:
                failures.append(f"slow endpoint took {elapsed:.1f}s")
        try:
            status, _, _ = api_request("GET", "/fast", "test", timeout=10)
            if status != 200:
                failures.append(f"fast endpoint status {status}")
        except Exception as exc:  # noqa: BLE001 -- self-test must report
            failures.append(f"fast endpoint failed: {exc}")
    finally:
        API_BASE = saved_base
        server.shutdown()
        thread.join(timeout=5)
    if failures:
        print("SELF-TEST FAIL:")
        for failure in failures:
            print(f"  - {failure}")
        return 1
    print("SELF-TEST PASS: stalled endpoint bounded, fast endpoint fine")
    return 0


def main(argv):
    if len(argv) == 2 and argv[1] == "--self-test":
        return self_test()
    if len(argv) != 7 or argv[1] == "--help":
        print("usage: gh-merge.py <owner> <repo> <pr> <method> "
              "<progress-log> --assert-trivial")
        return 12
    owner, repo, pr, method, progress_log, flag = argv[1:7]
    if flag != "--assert-trivial":
        print("refusing: classifier must pass --assert-trivial")
        return 12
    if method not in ("merge", "squash", "rebase"):
        print(f"refusing: unknown method {method}")
        return 12
    deadline = time.time() + DEFAULT_PR_BUDGET
    repo_id = f"{owner}/{repo}"
    try:
        token = get_token()
    except DefinitiveFailure as exc:
        log_line(progress_log, event="result", repo=repo_id, pr=pr,
                 phase="auth", head="?", deadline=int(deadline),
                 outcome="deferred", reason=str(exc).replace(" ", "_"))
        print(f"DEFERRED: {exc}")
        return 10
    log_line(progress_log, event="start", repo=repo_id, pr=pr,
             phase="preflight", head="?", deadline=int(deadline),
             outcome="?", reason="begin")
    try:
        head_sha, _, _ = preflight(
            owner, repo, pr, token, True, deadline, progress_log)
    except AmbiguousFailure as exc:
        log_line(progress_log, event="result", repo=repo_id, pr=pr,
                 phase="preflight", head="?", deadline=int(deadline),
                 outcome="deferred", reason=f"transport:{exc}".replace(" ", "_"))
        print(f"DEFERRED (transport, safe: nothing submitted): {exc}")
        return 10
    except DefinitiveFailure as exc:
        log_line(progress_log, event="result", repo=repo_id, pr=pr,
                 phase="preflight", head="?", deadline=int(deadline),
                 outcome="deferred", reason=str(exc).replace(" ", "_"))
        print(f"DEFERRED: {exc}")
        return 10
    log_line(progress_log, event="start", repo=repo_id, pr=pr,
             phase="merge", head=head_sha[:12], deadline=int(deadline),
             outcome="?", reason="put")
    try:
        check_deadline(deadline, "merge")
        merge_put(owner, repo, pr, head_sha, method, token)
    except DefinitiveFailure as exc:
        log_line(progress_log, event="result", repo=repo_id, pr=pr,
                 phase="merge", head=head_sha[:12], deadline=int(deadline),
                 outcome="deferred", reason=str(exc).replace(" ", "_"))
        print(f"DEFERRED: {exc}")
        return 10
    except AmbiguousFailure as exc:
        print(f"UNKNOWN after PUT ({exc}); reconciling read-only...")
        try:
            merged = reconcile(owner, repo, pr, head_sha, token, deadline)
        except DefinitiveFailure:
            merged = False
        outcome = "merged" if merged else "unknown"
        log_line(progress_log, event="result", repo=repo_id, pr=pr,
                 phase="reconcile", head=head_sha[:12], deadline=int(deadline),
                 outcome=outcome,
                 reason="reconciled" if merged else "quarantine:no-retry")
        if merged:
            print("RECONCILED: merge confirmed applied")
            return 0
        print("UNKNOWN: hold the repo mutation slot; human must reconcile; "
              "never auto-retry this PR")
        return 11
    log_line(progress_log, event="result", repo=repo_id, pr=pr,
             phase="merge", head=head_sha[:12], deadline=int(deadline),
             outcome="merged", reason="confirmed")
    print(f"MERGED: {owner}/{repo}#{pr} at {head_sha[:12]}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
