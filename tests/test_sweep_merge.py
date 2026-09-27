"""Approved-head binding around the unchanged gh_merge transport."""

import importlib.util
import os
import subprocess
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

SCRIPTS = (Path(__file__).resolve().parents[1]
           / "plugins/repo-hygiene/skills/dependabot-sweep/scripts")
sys.path.insert(0, str(SCRIPTS))

import sweep_merge as wrapper  # noqa: E402

HEAD = "a" * 40
OTHER_HEAD = "b" * 40


@pytest.fixture
def transport(monkeypatch, tmp_path):
    """Run the real helper, replacing only its API transport."""
    spec = importlib.util.spec_from_file_location("test_transport",
                                                 SCRIPTS / "gh_merge.py")
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    calls = []
    state = SimpleNamespace(head=HEAD, put_error=None, reconciled=False)
    progress = tmp_path / "merge.log"
    deadline = str(int(time.time()) + 600)
    monkeypatch.setenv("GH_MERGE_TOKEN", "test-token")
    monkeypatch.setenv("GH_MERGE_DEADLINE_EPOCH", deadline)

    def api(method, path, token, body=None, params=None, timeout=None):
        calls.append((method, path, body))
        assert token == "test-token"
        if method == "PUT":
            if state.put_error:
                raise state.put_error
            return 200, {"merged": True}, {}
        if path.endswith("/pulls/1"):
            after_put = any(call[0] == "PUT" for call in calls)
            # Ambiguous-response reconciliation ends immediately without
            # sleeping: either confirmed merged or a changed head.
            head = OTHER_HEAD if after_put else state.head
            return 200, {
                "state": "open", "merged": after_put and state.reconciled,
                "draft": False, "mergeable": True, "mergeable_state": "clean",
                "head": {"sha": head},
                "base": {"ref": "main", "sha": "c" * 40},
            }, {}
        if path.endswith("/files"):
            return 200, [{"filename": "requirements.txt"}], {}
        if path.endswith("/reviews") or path.endswith("/rulesets"):
            return 200, [], {}
        if path == "/graphql":
            return 200, {"data": {"repository": {"pullRequest": {
                "reviewThreads": {"pageInfo": {"hasNextPage": False},
                                  "nodes": []}}}}}, {}
        if path.endswith("/check-runs"):
            return 200, {"total_count": 1, "check_runs": [{
                "name": "test", "status": "completed",
                "conclusion": "success"}]}, {}
        if path.endswith("/status"):
            return 200, {"state": "success", "statuses": []}, {}
        if path.endswith("/protection"):
            return 200, {"required_status_checks": {"contexts": ["test"]}}, {}
        raise AssertionError(f"unexpected API call: {method} {path}")

    monkeypatch.setattr(helper, "api_request", api)
    monkeypatch.setattr(wrapper, "_load_helper", lambda path: helper)
    return SimpleNamespace(helper=helper, calls=calls, state=state,
                           progress=progress, deadline=deadline,
                           original_preflight=helper.preflight)


def invoke(transport, head=HEAD, method="merge", flag="--assert-trivial"):
    return wrapper.main([
        "sweep_merge.py", "--expected-head", head,
        "--helper-path", str(SCRIPTS / "gh_merge.py"), "--",
        "acme", "r", "1", method, str(transport.progress), flag])


def test_changed_head_refuses_before_put(transport, capsys):
    transport.state.head = OTHER_HEAD
    assert invoke(transport) == 10
    assert "DEFERRED: head changed since classification or approval" in (
        capsys.readouterr().out)
    assert not any(method == "PUT" for method, _, _ in transport.calls)
    assert "outcome=deferred" in transport.progress.read_text()
    assert transport.helper.preflight is transport.original_preflight


@pytest.mark.parametrize("method", ["merge", "squash", "rebase"])
def test_matching_head_binds_put_and_preserves_deadline(transport, method):
    assert invoke(transport, method=method) == 0
    puts = [call for call in transport.calls if call[0] == "PUT"]
    assert puts == [("PUT", "/repos/acme/r/pulls/1/merge",
                     {"sha": HEAD, "merge_method": method})]
    assert f"deadline={transport.deadline}" in transport.progress.read_text()
    assert transport.helper.preflight is transport.original_preflight


@pytest.mark.parametrize("head", [None, "", "a" * 39, "a" * 41, "g" * 40])
def test_missing_or_invalid_head_refuses_before_loading_helper(monkeypatch, head,
                                                             capsys):
    def forbidden(path):
        raise AssertionError("invalid expected head must not load the helper")

    monkeypatch.setattr(wrapper, "_load_helper", forbidden)
    argv = ["sweep_merge.py"]
    if head is not None:
        argv += ["--expected-head", head]
    argv += ["--", "acme", "r", "1", "merge", "unused.log", "--assert-trivial"]
    assert wrapper.main(argv) == 12
    assert "expected-head" in capsys.readouterr().out


@pytest.mark.parametrize("options", [
    ["--expected-h", HEAD],
    ["--expected-head", HEAD, "--helper-p", "helper.py"],
])
def test_abbreviated_flags_refuse_before_loading_helper(monkeypatch, options):
    def forbidden(path):
        raise AssertionError("abbreviated flags must not load the helper")

    monkeypatch.setattr(wrapper, "_load_helper", forbidden)
    argv = ["sweep_merge.py", *options, "--", "acme", "r", "1", "merge",
            "unused.log", "--assert-trivial"]
    assert wrapper.main(argv) == 12


@pytest.mark.parametrize("kind, reconciled, expected", [
    ("definitive", False, 10), ("ambiguous", False, 11),
    ("ambiguous", True, 0),
])
def test_original_merge_outcomes_passthrough(transport, kind, reconciled,
                                           expected):
    failure = (transport.helper.DefinitiveFailure if kind == "definitive"
               else transport.helper.AmbiguousFailure)
    transport.state.put_error = failure("test failure")
    transport.state.reconciled = reconciled
    assert invoke(transport) == expected
    assert sum(method == "PUT" for method, _, _ in transport.calls) == 1
    assert transport.helper.preflight is transport.original_preflight


@pytest.mark.parametrize("deadline", ["invalid", "1"])
def test_original_deadline_refusals_passthrough(transport, monkeypatch, deadline):
    monkeypatch.setenv("GH_MERGE_DEADLINE_EPOCH", deadline)
    assert invoke(transport) == 12
    assert transport.calls == []
    assert transport.helper.preflight is transport.original_preflight


def test_original_classifier_flag_refusal_passthrough(transport):
    assert invoke(transport, flag="--wrong-flag") == 12
    assert transport.calls == []
    assert transport.helper.preflight is transport.original_preflight


def test_preflight_is_restored_when_helper_main_raises(transport, monkeypatch):
    def fail(argv):
        raise RuntimeError("unexpected helper failure")

    monkeypatch.setattr(transport.helper, "main", fail)
    with pytest.raises(RuntimeError, match="unexpected helper failure"):
        invoke(transport)
    assert transport.helper.preflight is transport.original_preflight


def test_wrapper_entrypoint_loads_configured_helper_in_dedicated_process(tmp_path):
    helper = tmp_path / "helper.py"
    helper.write_text(
        "class DefinitiveFailure(Exception):\n    pass\n"
        f"def preflight():\n    return ({OTHER_HEAD!r}, 'main', 'base')\n"
        "def main(argv):\n"
        "    try:\n        preflight()\n"
        "    except DefinitiveFailure as exc:\n"
        "        print('DEFERRED: ' + str(exc))\n        return 10\n"
        "    print('PUT')\n    return 0\n")
    result = subprocess.run([
        sys.executable, str(SCRIPTS / "sweep_merge.py"),
        "--expected-head", HEAD, "--helper-path", str(helper), "--",
        "acme", "r", "1", "merge", str(tmp_path / "unused.log"),
        "--assert-trivial"], capture_output=True, text=True, check=False,
        timeout=10, env=dict(os.environ, GH_PROMPT_DISABLED="1"))
    assert result.returncode == 10
    assert result.stdout.strip() == (
        "DEFERRED: head changed since classification or approval")
