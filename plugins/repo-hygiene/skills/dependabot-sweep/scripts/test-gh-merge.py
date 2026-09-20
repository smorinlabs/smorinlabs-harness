#!/usr/bin/env python3
"""Behavioral gates for gh-merge.py against a scripted mock GitHub.

Covers: timeout enforcement, eligibility matrix (checks/reviews/threads/
mergeable/queue/diff caps), ambiguous-merge reconciliation with no duplicate
PUT, and head-change freshness. No network beyond localhost; no mutations.
"""

import io
import json
import os
import sys
import tempfile
import threading
import time
import unittest
import urllib.parse
from contextlib import redirect_stdout
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gh_merge  # noqa: E402

SCENARIO = {}


def green_pull(**overrides):
    pull = {
        "state": "open", "merged": False, "draft": False,
        "mergeable": True, "mergeable_state": "clean",
        "head": {"sha": "abc123"},
        "base": {"ref": "main", "sha": "base1"},
    }
    pull.update(overrides)
    return pull


def base_scenario():
    return {
        "pull": green_pull(),
        "pull_calls": 0,
        "files": [{"filename": "requirements.txt"}],
        "files_pages": 1,
        "reviews": [],
        "inline_comments": [],
        "threads_unresolved": 0,
        "check_runs": [{"name": "CI", "status": "completed",
                        "conclusion": "success"}],
        "combined": {"state": "success", "statuses": [
            {"context": "CI", "state": "success"}]},
        "protection": {"required_status_checks": {"contexts": ["CI"]}},
        "protection_404": False,
        "rulesets": [],
        "rulesets_404": False,
        "put_behavior": "merge",  # merge | hang-then-apply | hang-open
        "put_status": 200,  # error injection: 429 | 500
        "put_calls": 0,
        "merged": False,
    }


class Handler(BaseHTTPRequestHandler):
    server_version = "MockGitHub/1"

    def _send(self, obj, status=200, headers=None):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        for key, value in (headers or {}).items():
            self.send_header(key, value)
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def _route(self):
        return urllib.parse.urlparse(self.path).path

    def do_GET(self):  # noqa: N802
        path = self._route()
        if path == "/repos/o/r/pulls/1":
            SCENARIO["pull_calls"] += 1
            pull = dict(SCENARIO["pull"])
            if SCENARIO["merged"]:
                pull["state"] = "closed"
                pull["merged"] = True
            return self._send(pull)
        if path == "/repos/o/r/pulls/1/files":
            query = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            page = int(query.get("page", ["1"])[0])
            if page <= SCENARIO["files_pages"]:
                headers = {}
                if page < SCENARIO["files_pages"]:
                    headers["Link"] = (
                        f'<{SCENARIO["base"]}/repos/o/r/pulls/1/files?page='
                        f"{page + 1}>; rel=\"next\"")
                return self._send(SCENARIO["files"], headers=headers)
            return self._send([])
        if path == "/repos/o/r/pulls/1/reviews":
            return self._send(SCENARIO["reviews"])
        if path == "/repos/o/r/pulls/1/comments":
            return self._send(SCENARIO["inline_comments"])
        if path == "/repos/o/r/commits/abc123/check-runs":
            return self._send({"check_runs": SCENARIO["check_runs"]})
        if path == "/repos/o/r/commits/abc123/status":
            return self._send(SCENARIO["combined"])
        if path == "/repos/o/r/branches/main/protection":
            if SCENARIO["protection_404"]:
                return self._send({"message": "not found"}, status=404)
            return self._send(SCENARIO["protection"])
        if path == "/repos/o/r/rulesets":
            if SCENARIO["rulesets_404"]:
                return self._send({"message": "not found"}, status=404)
            return self._send(SCENARIO["rulesets"])
        return self._send({"message": "no mock route"}, status=404)

    def do_POST(self):  # noqa: N802
        if self._route() == "/graphql":
            length = int(self.headers.get("Content-Length", 0))
            self.rfile.read(length)
            nodes = [{"isResolved": False}] * SCENARIO["threads_unresolved"]
            return self._send({"data": {"repository": {"pullRequest": {
                "reviewThreads": {"nodes": nodes}}}}})
        return self._send({"message": "no mock route"}, status=404)

    def do_PUT(self):  # noqa: N802
        if self._route() != "/repos/o/r/pulls/1/merge":
            return self._send({"message": "no mock route"}, status=404)
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length) or b"{}")
        SCENARIO["put_calls"] += 1
        if body.get("sha") != SCENARIO["pull"]["head"]["sha"]:
            return self._send({"message": "head mismatch"}, status=409)
        if SCENARIO["put_status"] != 200:
            return self._send({"message": "injected"},
                              status=SCENARIO["put_status"])
        behavior = SCENARIO["put_behavior"]
        if behavior == "merge":
            SCENARIO["merged"] = True
            return self._send({"merged": True, "sha": "m1"})
        if behavior == "hang-then-apply":
            SCENARIO["merged"] = True
            time.sleep(60)  # Client must time out, then reconcile to merged.
            return self._send({"merged": True, "sha": "m1"})
        time.sleep(60)  # hang-open: never applies; must quarantine, no retry.
        return self._send({"merged": True, "sha": "m1"})

    def log_message(self, *args):
        return


class HelperTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.base = f"http://127.0.0.1:{cls.server.server_address[1]}"
        SCENARIO["base"] = cls.base
        cls.thread = threading.Thread(target=cls.server.serve_forever,
                                      daemon=True)
        cls.thread.start()
        os.environ["GH_MERGE_API_BASE"] = cls.base
        os.environ["GH_MERGE_TOKEN"] = "test"
        os.environ["GH_MERGE_OP_TIMEOUT"] = "3"
        os.environ["GH_MERGE_PR_BUDGET_SECS"] = "60"
        gh_merge.API_BASE = cls.base
        gh_merge.DEFAULT_OP_TIMEOUT = 3
        gh_merge.DEFAULT_PR_BUDGET = 60

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.thread.join(timeout=5)

    def setUp(self):
        SCENARIO.clear()
        SCENARIO.update(base_scenario())
        SCENARIO["base"] = self.base

    def run_helper(self):
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            log = tmp.name
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = gh_merge.main(
                ["gh-merge.py", "o", "r", "1", "merge", log,
                 "--assert-trivial"])
        with open(log, encoding="utf-8") as handle:
            lines = handle.read()
        os.unlink(log)
        return code, buf.getvalue(), lines

    def test_self_test(self):
        with redirect_stdout(io.StringIO()):
            self.assertEqual(gh_merge.self_test(), 0)

    def test_happy_path_merges(self):
        code, out, lines = self.run_helper()
        self.assertEqual(code, 0, out)
        self.assertIn("MERGED", out)
        self.assertIn("event=start", lines)
        self.assertIn("outcome=merged", lines)

    def test_pending_checks_defer(self):
        SCENARIO["check_runs"] = [{"name": "CI", "status": "in_progress",
                                   "conclusion": None}]
        SCENARIO["combined"] = {"state": "pending", "statuses": []}
        SCENARIO["protection_404"] = True
        code, out, _ = self.run_helper()
        self.assertEqual(code, 10, out)
        self.assertEqual(SCENARIO["put_calls"], 0)

    def test_failing_checks_defer(self):
        SCENARIO["check_runs"] = [{"name": "CI", "status": "completed",
                                   "conclusion": "failure"}]
        code, out, _ = self.run_helper()
        self.assertEqual(code, 10, out)
        self.assertEqual(SCENARIO["put_calls"], 0)

    def test_actions_only_failure_defer(self):
        SCENARIO["check_runs"] = [
            {"name": "CI", "status": "completed", "conclusion": "success"},
            {"name": "e2e", "status": "completed", "conclusion": "failure"},
        ]
        code, out, _ = self.run_helper()
        self.assertEqual(code, 10, out)
        self.assertEqual(SCENARIO["put_calls"], 0)

    def test_change_request_blocks(self):
        SCENARIO["reviews"] = [{"user": {"login": "rev"},
                                "state": "CHANGES_REQUESTED",
                                "submitted_at": "2026-01-02T00:00:00Z"}]
        code, out, _ = self.run_helper()
        self.assertEqual(code, 10, out)
        self.assertEqual(SCENARIO["put_calls"], 0)

    def test_superseded_change_request_merges(self):
        SCENARIO["reviews"] = [
            {"user": {"login": "rev"}, "state": "CHANGES_REQUESTED",
             "submitted_at": "2026-01-01T00:00:00Z"},
            {"user": {"login": "rev"}, "state": "APPROVED",
             "submitted_at": "2026-01-02T00:00:00Z"},
        ]
        code, out, _ = self.run_helper()
        self.assertEqual(code, 0, out)

    def test_toplevel_only_comment_merges(self):
        SCENARIO["reviews"] = [{"user": {"login": "some-bot"},
                                "state": "COMMENTED",
                                "submitted_at": "2026-01-02T00:00:00Z"}]
        SCENARIO["inline_comments"] = []
        code, out, _ = self.run_helper()
        self.assertEqual(code, 0, out)

    def test_inline_comments_defer(self):
        SCENARIO["reviews"] = [{"user": {"login": "rev"},
                                "state": "COMMENTED",
                                "submitted_at": "2026-01-02T00:00:00Z"}]
        SCENARIO["inline_comments"] = [{"id": 1, "body": "look here"}]
        code, out, _ = self.run_helper()
        self.assertEqual(code, 10, out)
        self.assertEqual(SCENARIO["put_calls"], 0)

    def test_unresolved_threads_defer(self):
        SCENARIO["threads_unresolved"] = 2
        code, out, _ = self.run_helper()
        self.assertEqual(code, 10, out)
        self.assertEqual(SCENARIO["put_calls"], 0)

    def test_dirty_pr_defers(self):
        SCENARIO["pull"] = green_pull(mergeable=False,
                                      mergeable_state="dirty")
        code, out, _ = self.run_helper()
        self.assertEqual(code, 10, out)
        self.assertEqual(SCENARIO["put_calls"], 0)

    def test_merge_queue_defers(self):
        SCENARIO["rulesets"] = [{"enforcement": "active",
                                 "rules": [{"type": "merge_queue"}]}]
        code, out, _ = self.run_helper()
        self.assertEqual(code, 10, out)
        self.assertEqual(SCENARIO["put_calls"], 0)

    def test_oversize_diff_defers(self):
        SCENARIO["files_pages"] = 5
        code, out, _ = self.run_helper()
        self.assertEqual(code, 10, out)
        self.assertEqual(SCENARIO["put_calls"], 0)

    def test_ambiguous_apply_reconciles_no_duplicate_put(self):
        SCENARIO["put_behavior"] = "hang-then-apply"
        code, out, _ = self.run_helper()
        self.assertEqual(code, 0, out)
        self.assertIn("RECONCILED", out)
        self.assertEqual(SCENARIO["put_calls"], 1)

    def test_ambiguous_open_quarantines_no_retry(self):
        SCENARIO["put_behavior"] = "hang-open"
        code, out, _ = self.run_helper()
        self.assertEqual(code, 11, out)
        self.assertIn("UNKNOWN", out)
        self.assertEqual(SCENARIO["put_calls"], 1)

    def test_actions_only_green_merges(self):
        SCENARIO["combined"] = {"state": "pending", "statuses": []}
        SCENARIO["protection_404"] = True
        code, out, _ = self.run_helper()
        self.assertEqual(code, 0, out)

    def test_put_500_reconciles_no_retry(self):
        SCENARIO["put_status"] = 500
        code, out, _ = self.run_helper()
        self.assertEqual(code, 11, out)
        self.assertIn("UNKNOWN", out)
        self.assertEqual(SCENARIO["put_calls"], 1)

    def test_put_429_defers(self):
        SCENARIO["put_status"] = 429
        code, out, _ = self.run_helper()
        self.assertEqual(code, 10, out)
        self.assertEqual(SCENARIO["put_calls"], 1)

    def test_head_change_rejected(self):
        SCENARIO["pull"] = green_pull()
        original_merge = gh_merge.merge_put

        def stale_put(*args, **kwargs):
            SCENARIO["pull"]["head"]["sha"] = "moved!"
            return original_merge(*args, **kwargs)

        gh_merge.merge_put = stale_put
        try:
            code, out, _ = self.run_helper()
        finally:
            gh_merge.merge_put = original_merge
        self.assertEqual(code, 10, out)
        self.assertIn("head mismatch", out)


if __name__ == "__main__":
    unittest.main(verbosity=2)
