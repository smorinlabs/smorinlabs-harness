"""tests/test_sweep_slice4.py — Slice 4, non-mutating half: config loader,
observation fetch over the helper's bounded HTTP, the noun-verb CLI, and
authority persisted on the run header.

Nothing here mutates GitHub. The mock GitHub server is local; every
network-shaped test runs against it.
"""

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "plugins/repo-hygiene/skills/dependabot-sweep/scripts"
sys.path.insert(0, str(SCRIPTS))

import sweep_config as cfg  # noqa: E402

ALL_REPAIRS = ["branch_update", "code_repair", "lockfile", "major_migration",
               "replacement_pr"]


def write(tmp_path, text, name="config.toml"):
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return str(path)


def load(tmp_path, text=None, flags=None, env=None, path=None):
    if text is not None and path is None:
        path = write(tmp_path, text)
    env = {"HOME": str(tmp_path), **(env or {})}
    return cfg.load_config(path, flags or {}, env)


# --- Defaults reproduce today's behavior ---

def test_defaults_reproduce_todays_behavior(tmp_path):
    run = load(tmp_path, '[org."acme"]\nvisibility = "all"\n')
    assert run.host == "github" and run.tool == "gh"
    assert run.mode == "automated"
    assert run.repairs == ALL_REPAIRS
    assert run.reviewer_contexts == []
    assert run.pause_on_conflict is False
    assert run.op_timeout_secs == 30 and run.pr_budget_secs == 600
    assert run.run_budget_secs == 0  # unbounded, as today
    assert run.observation_window_secs == 600
    assert run.poll_floor_secs == 20
    assert run.stale_after_secs == 600  # defaults to the per-PR budget
    assert [(s.kind, s.login, s.visibility) for s in run.scopes] == [
        ("org", "acme", "all")]


def test_stale_after_follows_pr_budget_unless_set(tmp_path):
    run = load(tmp_path, '[org."acme"]\n[budgets]\npr_budget_secs = 900\n')
    assert run.stale_after_secs == 900
    run = load(tmp_path, '[org."acme"]\n[budgets]\npr_budget_secs = 900\n'
                         'stale_after_secs = 1200\n')
    assert run.stale_after_secs == 1200


# --- Mode resolution reuses resolve_mode; flags beat config ---

def test_no_auto_fix_and_check_flags_resolve_inspect(tmp_path):
    text = '[defaults]\nmode = "gated"\n[org."acme"]\n'
    assert load(tmp_path, text).mode == "gated"
    assert load(tmp_path, text, flags={"no_auto_fix": True}).mode == "inspect"
    assert load(tmp_path, text, flags={"check": True}).mode == "inspect"
    assert load(tmp_path, '[defaults]\nauto_fix = false\n[org."acme"]\n'
                ).mode == "inspect"
    assert load(tmp_path, '[org."acme"]\n',
                flags={"mode": "gated"}).mode == "gated"


def test_unknown_mode_refused(tmp_path):
    with pytest.raises(cfg.ConfigError) as exc:
        load(tmp_path, '[defaults]\nmode = "yolo"\n[org."acme"]\n')
    assert exc.value.code == "config_invalid" and "mode" in str(exc.value)


# --- Precedence: flags > env > config file > defaults, with origins ---

def test_precedence_and_origins(tmp_path):
    text = '[defaults]\npause_on_conflict = true\n[org."acme"]\n'
    run = load(tmp_path, text)
    assert run.pause_on_conflict is True and run.origin["pause_on_conflict"] == "config"
    run = load(tmp_path, text, flags={"pause_on_conflict": False})
    assert run.pause_on_conflict is False and run.origin["pause_on_conflict"] == "flag"
    assert run.origin["mode"] == "default"


def test_config_flag_replaces_env_and_discovery(tmp_path):
    flag_path = write(tmp_path, '[org."from-flag"]\n', "flag.toml")
    env_path = write(tmp_path, '[org."from-env"]\n', "env.toml")
    xdg = tmp_path / "xdg" / "dependabot-sweep"
    xdg.mkdir(parents=True)
    (xdg / "config.toml").write_text('[org."from-xdg"]\n', encoding="utf-8")
    env = {"XDG_CONFIG_HOME": str(tmp_path / "xdg"),
           "DEPENDABOT_SWEEP_CONFIG": env_path}
    assert load(tmp_path, flags={"config": flag_path}, env=env
                ).scopes[0].login == "from-flag"
    assert load(tmp_path, env=env).scopes[0].login == "from-env"
    assert load(tmp_path, env={"XDG_CONFIG_HOME": str(tmp_path / "xdg")}
                ).scopes[0].login == "from-xdg"
    home = tmp_path / ".config" / "dependabot-sweep"
    home.mkdir(parents=True)
    (home / "config.toml").write_text('[org."from-home"]\n', encoding="utf-8")
    assert load(tmp_path).scopes[0].login == "from-home"


# --- Scope from flags; missing config ---

def test_scope_flags_override_config_and_allow_missing_file(tmp_path):
    run = load(tmp_path, '[org."acme"]\n', flags={"org": ["other"]})
    assert [(s.kind, s.login) for s in run.scopes] == [("org", "other")]
    run = load(tmp_path, flags={"repo": ["acme/web", "acme/api"]})
    assert [(s.kind, s.login, s.repos) for s in run.scopes] == [
        ("repo", "acme", ["web", "api"])]
    assert run.config_path == ""  # no file, and that is fine with --repo
    with pytest.raises(cfg.ConfigError) as exc:
        load(tmp_path)
    assert exc.value.code == "no_scope"


def test_repo_flag_requires_owner_slash_name(tmp_path):
    with pytest.raises(cfg.ConfigError) as exc:
        load(tmp_path, flags={"repo": ["just-a-name"]})
    assert exc.value.code == "config_invalid"


# --- Validation: host, tool, repairs, budgets ---

def test_unsupported_host_or_tool_refused(tmp_path):
    with pytest.raises(cfg.ConfigError) as exc:
        load(tmp_path, '[defaults]\nhost = "gitlab"\n[org."acme"]\n')
    assert exc.value.code == "unsupported_host"
    with pytest.raises(cfg.ConfigError) as exc:
        load(tmp_path, '[defaults]\ntool = "glab"\n[org."acme"]\n')
    assert exc.value.code == "unsupported_tool"


def test_repairs_validated_against_closed_vocabulary(tmp_path):
    run = load(tmp_path, '[defaults]\nrepairs = ["lockfile", "branch_update"]\n'
                         '[org."acme"]\n')
    assert run.repairs == ["branch_update", "lockfile"]
    for bad in ('["repo_settings"]', '["yolo"]'):
        with pytest.raises(cfg.ConfigError) as exc:
            load(tmp_path, f'[defaults]\nrepairs = {bad}\n[org."acme"]\n')
        assert exc.value.code == "config_invalid"


def test_poll_floor_clamped_and_budgets_must_be_non_negative(tmp_path):
    run = load(tmp_path, '[org."acme"]\n[budgets]\npoll_floor_secs = 5\n')
    assert run.poll_floor_secs == 20 and run.origin["poll_floor_secs"] == "clamped"
    with pytest.raises(cfg.ConfigError):
        load(tmp_path, '[org."acme"]\n[budgets]\nrun_budget_secs = -1\n')
    with pytest.raises(cfg.ConfigError):
        load(tmp_path, '[org."acme"]\n[budgets]\nop_timeout_secs = 0\n')


def test_unknown_keys_are_reported_with_location(tmp_path):
    with pytest.raises(cfg.ConfigError) as exc:
        load(tmp_path, '[defaults]\nauto_fx = true\n[org."acme"]\n')
    assert "auto_fx" in str(exc.value) and "defaults" in str(exc.value)


# --- Per-scope overrides and the authority the run header stores ---

def test_per_scope_overrides(tmp_path):
    text = ('[org."acme"]\nvisibility = "private"\nauto_fix = false\n'
            '[user."me"]\nrepos = ["dotfiles"]\n')
    run = load(tmp_path, text)
    assert run.mode == "automated"
    assert run.scope_for("acme").mode == "inspect"
    assert run.scope_for("me").mode == "automated"
    assert run.scope_for("me").repos == ["dotfiles"]


def test_authority_dict_is_complete_and_json_safe(tmp_path):
    run = load(tmp_path, '[defaults]\nreviewer_contexts = ["coderabbitai"]\n'
                         '[org."acme"]\n')
    authority = run.to_authority(helper_path="/opt/h/gh_merge.py")
    assert authority == {
        "mode": "automated", "repairs": ALL_REPAIRS, "approved": [],
        "holds": [], "reviewer_contexts": ["coderabbitai"],
        "pause_on_conflict": False, "op_timeout_secs": 30,
        "pr_budget_secs": 600, "run_budget_secs": 0,
        "observation_window_secs": 600, "poll_floor_secs": 20,
        "stale_after_secs": 600, "helper_path": "/opt/h/gh_merge.py",
    }
    assert json.loads(json.dumps(authority)) == authority


# ---------------------------------------------------------------------------
# Observation fetch over the helper's bounded HTTP, against a mock GitHub
# ---------------------------------------------------------------------------

import os  # noqa: E402
import threading  # noqa: E402
import time  # noqa: E402
import urllib.parse  # noqa: E402
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer  # noqa: E402

import gh_merge  # noqa: E402
import sweep_evaluator as ev  # noqa: E402
import sweep_observe as obs  # noqa: E402

HEAD = "a" * 40
BASE_SHA = "b" * 40
CI_APP = 15368
SCENARIO: dict = {}


def scenario():
    return {
        "pull": {"state": "open", "draft": False, "merged": False,
                 "mergeable": True, "mergeable_state": "clean",
                 "merged_at": None, "merge_commit_sha": "c" * 40,
                 "auto_merge": None,
                 "head": {"sha": HEAD, "ref": "dependabot/pip/x-1.2.3"},
                 "base": {"sha": BASE_SHA, "ref": "main"}},
        "pull_status": 200,
        "files": [{"filename": "pyproject.toml", "sha": "f1" * 20,
                   "status": "modified", "changes": 2},
                  {"filename": "uv.lock", "sha": "f2" * 20,
                   "status": "modified", "changes": 9}],
        "files_pages": 1,
        "reviews": [],
        "graphql": {"data": {"repository": {"pullRequest": {
            "isInMergeQueue": False, "mergeQueueEntry": None,
            "autoMergeRequest": None,
            "reviewThreads": {"pageInfo": {"hasNextPage": False},
                              "nodes": [{"id": "T1", "isResolved": True,
                                         "isOutdated": False}]}}}}},
        "check_runs": {"total_count": 1, "check_runs": [
            {"id": 1, "name": "ci/test", "status": "completed",
             "conclusion": "success", "head_sha": HEAD,
             "app": {"id": CI_APP, "slug": "github-actions"},
             "check_suite": {"id": 501},
             "completed_at": "2026-09-22T00:10:00Z"}]},
        "check_suites": {"total_count": 1, "check_suites": [
            {"id": 501, "status": "completed", "conclusion": "success",
             "app": {"id": CI_APP}}]},
        "combined": {"state": "pending", "statuses": [], "total_count": 0,
                     "sha": HEAD},
        "status_delay": 0.0,
        "protection": {"required_status_checks": {
            "strict": False, "checks": [{"context": "ci/test",
                                         "app_id": CI_APP}]},
            "required_pull_request_reviews": {
                "required_approving_review_count": 0},
            "required_conversation_resolution": {"enabled": False}},
        "protection_status": 200,
        "rules": [{"type": "required_status_checks", "ruleset_id": 9,
                   "ruleset_source_type": "Organization",
                   "ruleset_source": "o",
                   "parameters": {"required_status_checks": [
                       {"context": "lint", "integration_id": CI_APP}],
                       "strict_required_status_checks_policy": False}},
                  {"type": "pull_request", "ruleset_id": 9,
                   "parameters": {"required_approving_review_count": 0}}],
        "rules_status": 200,
        "rulesets": {9: {"id": 9, "name": "org", "enforcement": "active",
                         "source_type": "Organization", "source": "o",
                         "target": "branch"}},
        "ruleset_calls": 0,
        "calls": [],
    }


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):  # noqa: D401 - silence
        return

    def _send(self, body, status=200, headers=None):
        data = json.dumps(body).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        for key, value in (headers or {}).items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):  # noqa: N802
        length = int(self.headers.get("Content-Length", "0"))
        self.rfile.read(length)
        SCENARIO["calls"].append("POST /graphql")
        return self._send(SCENARIO["graphql"])

    def do_GET(self):  # noqa: N802
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        SCENARIO["calls"].append(f"GET {path}")
        query = urllib.parse.parse_qs(parsed.query)
        s = SCENARIO
        if path == "/repos/o/r/pulls/7":
            return self._send(s["pull"] if s["pull_status"] == 200
                              else {"message": "x"}, s["pull_status"])
        if path == "/repos/o/r/pulls/7/files":
            page = int(query.get("page", ["1"])[0])
            headers = {}
            if page < s["files_pages"]:
                headers["Link"] = (f'<{s["base"]}/repos/o/r/pulls/7/files?'
                                   f'page={page + 1}>; rel="next"')
            return self._send(s["files"], headers=headers)
        if path == "/repos/o/r/pulls/7/reviews":
            return self._send(s["reviews"])
        if path == f"/repos/o/r/commits/{HEAD}/check-runs":
            return self._send(s["check_runs"])
        if path == f"/repos/o/r/commits/{HEAD}/check-suites":
            return self._send(s["check_suites"])
        if path == f"/repos/o/r/commits/{HEAD}/status":
            if s["status_delay"]:
                time.sleep(s["status_delay"])
            return self._send(s["combined"])
        if path == "/repos/o/r/branches/main/protection":
            return self._send(s["protection"] if s["protection_status"] == 200
                              else {"message": "x"}, s["protection_status"])
        if path == "/repos/o/r/rules/branches/main":
            return self._send(s["rules"] if s["rules_status"] == 200
                              else {"message": "x"}, s["rules_status"])
        if path.startswith("/repos/o/r/rulesets/"):
            s["ruleset_calls"] += 1
            ruleset_id = int(path.rsplit("/", 1)[1])
            detail = s["rulesets"].get(ruleset_id)
            return self._send(detail or {"message": "x"},
                              200 if detail else 404)
        return self._send({"message": f"unrouted {path}"}, 404)


@pytest.fixture(scope="module")
def mock_github():
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    base = f"http://127.0.0.1:{server.server_address[1]}"
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    saved = gh_merge.API_BASE
    gh_merge.API_BASE = base
    os.environ["GH_MERGE_API_BASE"] = base
    yield base
    gh_merge.API_BASE = saved
    server.shutdown()


@pytest.fixture
def github(mock_github):
    SCENARIO.clear()
    SCENARIO.update(scenario())
    SCENARIO["base"] = mock_github
    return SCENARIO


def fetch(**kw):
    return obs.fetch_observation("o", "r", 7, token="t", op_timeout=5, **kw)


def make_green(github):
    """The default policy also requires `lint` (ruleset 9); give it a run."""
    github["check_runs"]["check_runs"].append(
        {"id": 2, "name": "lint", "status": "completed",
         "conclusion": "success", "head_sha": HEAD,
         "app": {"id": CI_APP}, "check_suite": {"id": 501},
         "completed_at": "2026-09-22T00:11:00Z"})
    github["check_runs"]["total_count"] = 2


def test_observe_builds_a_complete_observation(github):
    observation = fetch()
    assert observation.head_sha == HEAD
    assert observation.pull["status"] == 200
    assert [f["filename"] for f in observation.files["data"]] == [
        "pyproject.toml", "uv.lock"]
    assert observation.threads["data"] == [{"id": "T1", "isResolved": True,
                                            "isOutdated": False}]
    assert observation.queue["data"]["isInMergeQueue"] is False
    assert observation.check_suites["data"] == {
        "501": {"status": "completed", "conclusion": "success"}}
    policy = observation.policy
    assert policy.known is True
    assert sorted((c.context, c.producer_id) for c in policy.required_checks) \
        == [("ci/test", CI_APP), ("lint", CI_APP)]
    assert "branch_protection" in policy.sources and "ruleset:9" in policy.sources
    assert github["ruleset_calls"] == 1  # two rules, one ruleset, one fetch
    assert "POST /graphql" in github["calls"]
    assert github["calls"].count(f"GET /repos/o/r/commits/{HEAD}/check-suites") == 1


def test_observe_feeds_the_evaluator(github):
    make_green(github)
    observation = fetch()
    receipt = ev.ClassifierReceipt.for_files(
        HEAD, observation.files["data"], dependency_only=True,
        classifier="test", at="2026-09-22T00:12:00Z")
    result = ev.evaluate(observation, receipt, ev.Authority(),
                         ev.Tracking(), now=1.0)
    assert result.state.value == "READY", result.reason_line


def test_observe_protection_error_leaves_policy_unknown_only(github):
    github["protection_status"] = 500
    observation = fetch()
    assert observation.policy.known is False
    assert observation.pull["status"] == 200
    assert observation.check_runs["status"] == 200


def test_observe_pull_unreadable_stops_without_guessing_head(github):
    github["pull_status"] = 404
    observation = fetch()
    assert observation.head_sha == ""
    assert observation.pull["status"] == 404
    assert observation.files["status"] is None
    assert "not fetched" in observation.files["error"]
    assert len([c for c in github["calls"] if c.startswith("GET")]) == 1
    result = ev.evaluate(observation, ev.ClassifierReceipt.for_files(
        HEAD, [], True, "t", "x"), ev.Authority(), ev.Tracking(), now=1.0)
    assert result.reason_code == "K13"


def test_observe_transport_failure_marks_only_that_section(github):
    github["status_delay"] = 3.0
    observation = obs.fetch_observation("o", "r", 7, token="t", op_timeout=1)
    assert observation.statuses["status"] is None
    assert "transport" in observation.statuses["error"]
    assert observation.check_runs["status"] == 200
    result = ev.evaluate(observation, ev.ClassifierReceipt.for_files(
        HEAD, observation.files["data"], True, "t", "x"), ev.Authority(),
        ev.Tracking(), now=1.0)
    assert result.reason_code == "K13" and "statuses" in result.reason_line


def test_observe_graphql_errors_are_not_data(github):
    github["graphql"] = {"data": None, "errors": [{"message": "rate limited"}]}
    observation = fetch()
    assert observation.threads["status"] is None
    assert observation.queue["status"] is None
    assert "rate limited" in observation.threads["error"]


def test_observe_truncation_flags(github):
    github["files_pages"] = 5  # beyond the helper's page cap
    github["check_runs"]["total_count"] = 250
    observation = fetch()
    assert observation.files["truncated"] is True
    assert observation.check_runs["truncated"] is True


def test_observe_deadline_passed_fetches_nothing(github):
    observation = obs.fetch_observation("o", "r", 7, token="t", op_timeout=5,
                                        deadline_epoch=time.time() - 1)
    assert observation.pull["status"] is None
    assert "deadline" in observation.pull["error"]
    assert github["calls"] == []


def test_observation_round_trips_through_json(github):
    observation = fetch()
    payload = json.loads(json.dumps(obs.observation_to_dict(observation)))
    restored = obs.observation_from_dict(payload)
    assert restored.policy == observation.policy
    assert ev.fingerprint_of(restored) == ev.fingerprint_of(observation)
    receipt = ev.ClassifierReceipt.for_files(
        HEAD, observation.files["data"], True, "t", "x")
    before = ev.evaluate(observation, receipt, ev.Authority(), ev.Tracking(),
                         now=1.0)
    after = ev.evaluate(restored, receipt, ev.Authority(), ev.Tracking(),
                        now=1.0)
    assert (before.state, before.reason_code) == (after.state, after.reason_code)
    assert ev.stale_reasons(before, restored) == []


# ---------------------------------------------------------------------------
# The noun-verb CLI (CLI Design Standard v1.4.14, minimal tier)
# ---------------------------------------------------------------------------

import io  # noqa: E402
import subprocess  # noqa: E402

import sweep_cli as cli  # noqa: E402
from sweep_core import RunHeader, Store  # noqa: E402

PLUGIN_VERSION = json.load(open(
    REPO_ROOT / "plugins/repo-hygiene/.claude-plugin/plugin.json"))["version"]


def config_file(tmp_path, text='[org."acme"]\nvisibility = "all"\n'):
    return write(tmp_path, text, "sweep.toml")


def discoveries_file(tmp_path, items=None):
    items = items if items is not None else [
        {"org": "acme", "repo": "r", "number": n, "url": f"u{n}",
         "title": f"bump {n}", "owner": "acme", "head_sha": f"h{n}",
         "base_ref": "main"} for n in (1, 2)]
    path = tmp_path / "discoveries.json"
    path.write_text(json.dumps(items), encoding="utf-8")
    return str(path)


def run(argv, capsys, monkeypatch=None, stdin=None):
    if monkeypatch is not None and stdin is not None:
        monkeypatch.setattr("sys.stdin", io.StringIO(stdin))
    code = cli.main(list(argv))
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def test_run_header_authority_survives_replay(tmp_path):
    store = Store(str(tmp_path / "s.jsonl"))
    header = RunHeader(run_id="R", mode="automated",
                       authority={"mode": "automated", "repairs": ["lockfile"]})
    store.set_header(header)
    assert Store.load(str(tmp_path / "s.jsonl")).header.authority == {
        "mode": "automated", "repairs": ["lockfile"]}


def test_cli_bare_help_and_version_via_subprocess():
    script = str(SCRIPTS / "sweep_cli.py")
    bare = subprocess.run([sys.executable, script], capture_output=True,
                          text=True)
    assert bare.returncode == 0 and "Usage" in bare.stdout and bare.stderr == ""
    version = subprocess.run([sys.executable, script, "-V"],
                             capture_output=True, text=True)
    assert version.returncode == 0
    assert version.stdout.strip() == f"dependabot-sweep {PLUGIN_VERSION}"
    helped = subprocess.run([sys.executable, script, "run", "create", "--help"],
                            capture_output=True, text=True)
    assert helped.returncode == 0 and "Examples" in helped.stdout


def test_cli_usage_errors_exit_2(capsys):
    for argv in (["run"], ["bogus"], ["run", "creat"],
                 ["--stor", "x", "run", "view"], ["run", "view", "--outpu", "json"]):
        code, out, err = run(argv, capsys)
        assert code == 2, argv
        assert out == "" and err, argv


def test_cli_usage_error_under_json_uses_error_schema(capsys):
    code, out, err = run(["--json", "run", "creat"], capsys)
    assert code == 2 and out == ""
    assert json.loads(err.strip().splitlines()[-1])["error"]["code"] == "usage"


def test_cli_run_lifecycle(tmp_path, capsys):
    store = str(tmp_path / "run.jsonl")
    common = ["--store", store, "--config", config_file(tmp_path)]
    code, out, err = run(common + ["run", "create", "--run-id", "RUN-CLI",
                                   "--file", discoveries_file(tmp_path),
                                   "-o", "json"], capsys)
    assert code == 0, err
    created = json.loads(out)
    assert created["run_id"] == "RUN-CLI" and created["mode"] == "automated"
    assert created["scope_ids"] == ["PR-001", "PR-002"]
    assert created["authority"]["repairs"] == ALL_REPAIRS
    assert created["authority"]["helper_path"].endswith("gh_merge.py")
    assert Store.load(store).header.authority == created["authority"]

    code, out, err = run(common + ["attempt", "create", "--model", "sol",
                                   "-o", "json"], capsys)
    assert code == 0, err
    taskings = json.loads(out)
    assert taskings == [{"attempt_id": "AGT-001.1", "repo_id": "acme/r",
                         "card_ids": ["PR-001", "PR-002"]}]
    assert Store.load(store).cards["PR-001"].deadline_epoch > 0

    code, out, err = run(common + ["brief", "view", "AGT-001.1"], capsys)
    assert code == 0, err
    assert "AGT-001.1" in out and 'acme/r#1 "bump 1" [PR-001]' in out
    assert "mode: automated" in out and "{{" not in out

    outcomes = tmp_path / "outcomes.jsonl"
    outcomes.write_text("\n".join(json.dumps(r) for r in [
        {"card_id": "PR-001", "outcome": "merged", "commit_sha": "c" * 40,
         "merged_at": "2026-09-22T00:20:00Z"},
        {"card_id": "PR-002", "outcome": "hold", "state": "WAITING",
         "reason_code": "K01", "reason_line": "checks pending",
         "severity": "low", "confidence": "high",
         "evidence": [{"id": "EV-1"}], "action": "observe",
         "action_owner": "sweeper", "resume_trigger": "checks complete"},
    ]) + "\n", encoding="utf-8")
    code, out, err = run(common + ["attempt", "collect", "AGT-001.1", "--file",
                                   str(outcomes), "-o", "json"], capsys)
    assert code == 0, err
    assert json.loads(out)["applied"] == ["PR-001", "PR-002"]

    code, out, err = run(common + ["run", "describe"], capsys)
    assert code == 0 and "Selected 2; merged 1;" in out and "MERGED (1)" in out
    code, out, err = run(common + ["approval", "list"], capsys)
    assert code == 0 and out.startswith("No approvals needed")
    code, out, err = run(common + ["card", "list", "-o", "json"], capsys)
    assert code == 0 and [c["id"] for c in json.loads(out)] == ["PR-001", "PR-002"]
    code, out, err = run(common + ["card", "view", "PR-002"], capsys)
    assert code == 0 and "WAITING" in out and "K01" in out
    code, out, err = run(common + ["run", "finish", "--continuation", "none",
                                   "-o", "json"], capsys)
    assert code == 0, err
    assert json.loads(out)["stop_reason"] == "completed_with_exceptions"
    code, out, err = run(common + ["run", "view", "-o", "json"], capsys)
    assert code == 0
    view = json.loads(out)
    assert view["stop_reason"] == "completed_with_exceptions"
    assert view["counts"]["merged"] == 1 and view["authority"]["mode"] == "automated"


def test_cli_discoveries_accept_gh_search_shape(tmp_path, capsys):
    store = str(tmp_path / "run.jsonl")
    items = [{"number": 3, "title": "bump web", "url": "u",
              "repository": {"nameWithOwner": "acme/web"}}]
    code, out, err = run(["--store", store, "--config", config_file(tmp_path),
                          "run", "create", "--run-id", "R", "--file",
                          discoveries_file(tmp_path, items), "-o", "json"],
                         capsys)
    assert code == 0, err
    card = Store.load(store).cards["PR-001"]
    assert (card.org, card.repo, card.number, card.title) == (
        "acme", "web", 3, "bump web")


def test_cli_not_found_and_runtime_errors(tmp_path, capsys):
    store = str(tmp_path / "run.jsonl")
    common = ["--store", store, "--config", config_file(tmp_path)]
    code, out, err = run(common + ["run", "view", "--json"], capsys)
    assert code == 3 and json.loads(err)["error"]["code"] == "not_found"
    run(common + ["run", "create", "--run-id", "R", "--file",
                  discoveries_file(tmp_path)], capsys)
    code, out, err = run(common + ["card", "view", "PR-999", "--json"], capsys)
    assert code == 3 and json.loads(err)["error"]["code"] == "not_found"
    code, out, err = run(common + ["card", "view", "PR-999"], capsys)
    assert code == 3 and err.startswith("error: ") and not err.rstrip().endswith(".")
    run(common + ["attempt", "create"], capsys)
    bad = tmp_path / "bad.jsonl"
    bad.write_text(json.dumps({"card_id": "PR-001", "outcome": "merged"}) + "\n",
                   encoding="utf-8")
    code, out, err = run(common + ["attempt", "collect", "AGT-001.1", "--file",
                                   str(bad), "--json"], capsys)
    assert code == 1 and json.loads(err)["error"]["code"] == "store_error"


def test_cli_reconcile_from_file(tmp_path, capsys):
    store = str(tmp_path / "run.jsonl")
    common = ["--store", store, "--config", config_file(tmp_path)]
    run(common + ["run", "create", "--run-id", "R", "--file",
                  discoveries_file(tmp_path)], capsys)
    run(common + ["attempt", "create"], capsys)
    observed = tmp_path / "observed.json"
    observed.write_text(json.dumps({
        "PR-001": {"merged": True, "commit": "c" * 40,
                   "at": "2026-09-22T00:20:00Z"},
        "PR-002": {"merged": False}}), encoding="utf-8")
    code, out, err = run(common + ["run", "reconcile", "--file", str(observed),
                                   "--live", "AGT-001.1", "-o", "json"], capsys)
    assert code == 0 and json.loads(out)["crashed"] == []
    code, out, err = run(common + ["run", "reconcile", "--file", str(observed),
                                   "-o", "json"], capsys)
    assert code == 0, err
    summary = json.loads(out)
    assert summary["crashed"] == ["AGT-001.1"] and summary["merged"] == ["PR-001"]


def test_cli_pr_observe_and_evaluate_dry_run(github, tmp_path, capsys,
                                             monkeypatch):
    make_green(github)
    monkeypatch.setenv("GH_MERGE_TOKEN", "t")
    code, out, err = run(["pr", "observe", "o/r#7", "-o", "json"], capsys)
    assert code == 0, err
    observation = json.loads(out)
    assert observation["head_sha"] == HEAD
    code, out, err = run(["pr", "evaluate", "o/r#7", "--file", "-",
                          "--dependency-only", "--classifier", "test",
                          "--mode", "inspect", "-o", "json"], capsys,
                         monkeypatch, stdin=json.dumps(observation))
    assert code == 0, err
    result = json.loads(out)
    assert result["outcome"]["outcome"] == "ready"
    assert result["evaluation"]["merge_path"] == "none"
    assert result["receipt"]["classifier"] == "test"
    code, out, err = run(["pr", "evaluate", "o/r#7", "--file", "-",
                          "--mode", "inspect", "-o", "json"], capsys,
                         monkeypatch, stdin=json.dumps(observation))
    assert code == 0 and json.loads(out)["outcome"]["reason_code"] == "K09"
    code, out, err = run(["pr", "evaluate", "o/r#7", "--file", "-",
                          "--dependency-only", "--mode", "inspect"], capsys,
                         monkeypatch, stdin=json.dumps(observation))
    assert code == 0 and "READY" in out and "identity" in out


def test_cli_pr_evaluate_with_store_uses_header_authority_and_lease(
        github, tmp_path, capsys, monkeypatch):
    make_green(github)
    monkeypatch.setenv("GH_MERGE_TOKEN", "t")
    store = str(tmp_path / "run.jsonl")
    common = ["--store", store, "--config", config_file(tmp_path)]
    items = [{"org": "o", "repo": "r", "number": 7, "url": "u", "title": "t",
              "owner": "o", "head_sha": HEAD, "base_ref": "main"}]
    run(common + ["run", "create", "--run-id", "R", "--file",
                  discoveries_file(tmp_path, items)], capsys)
    code, out, err = run(common + ["pr", "observe", "PR-001", "-o", "json"],
                         capsys)
    assert code == 0, err
    obs_path = tmp_path / "obs.json"
    obs_path.write_text(out, encoding="utf-8")
    code, out, err = run(common + ["pr", "evaluate", "PR-001", "--file",
                                   str(obs_path), "--dependency-only",
                                   "-o", "json"], capsys)
    assert code == 0 and json.loads(out)["outcome"]["reason_code"] == "K12"
    run(common + ["attempt", "create"], capsys)
    code, out, err = run(common + ["pr", "evaluate", "PR-001", "--file",
                                   str(obs_path), "--dependency-only",
                                   "--attempt", "AGT-001.1", "-o", "json"],
                         capsys)
    assert code == 0, err
    result = json.loads(out)
    assert result["outcome"]["outcome"] == "ready"
    assert result["evaluation"]["merge_path"] == "put"


def test_cli_auth_failure_exits_4(github, capsys, monkeypatch):
    monkeypatch.delenv("GH_MERGE_TOKEN", raising=False)

    def no_token():
        raise gh_merge.DefinitiveFailure("credential acquisition failed: no token")

    monkeypatch.setattr(gh_merge, "get_token", no_token)
    code, out, err = run(["pr", "observe", "o/r#7", "--json"], capsys)
    assert code == 4 and json.loads(err)["error"]["code"] == "auth_required"


def test_cli_interrupt_exits_130(capsys, monkeypatch):
    def boom(args, ctx):
        raise KeyboardInterrupt

    monkeypatch.setitem(cli.COMMANDS, ("approval", "list"), boom)
    code, out, err = run(["--store", "x.jsonl", "approval", "list"], capsys)
    assert code == 130


def test_cli_named_store_never_falls_back_to_dry_run(github, tmp_path, capsys,
                                                    monkeypatch):
    """With --store, the target must be a card in that store: a long-form
    target must not reach the evaluator with lease and quarantine unchecked."""
    make_green(github)
    monkeypatch.setenv("GH_MERGE_TOKEN", "t")
    store = str(tmp_path / "run.jsonl")
    common = ["--store", store, "--config", config_file(tmp_path)]
    code, out, err = run(["--store", str(tmp_path / "missing.jsonl"), "pr",
                          "observe", "o/r#7", "--json"], capsys)
    assert code == 3 and json.loads(err)["error"]["code"] == "not_found"
    items = [{"org": "o", "repo": "r", "number": 7, "url": "u", "title": "t",
              "owner": "o", "head_sha": HEAD, "base_ref": "main"}]
    run(common + ["run", "create", "--run-id", "R", "--file",
                  discoveries_file(tmp_path, items)], capsys)
    code, out, err = run(common + ["pr", "observe", "PR-001", "-o", "json"],
                         capsys)
    assert code == 0, err
    obs_path = tmp_path / "obs.json"
    obs_path.write_text(out, encoding="utf-8")
    run(common + ["attempt", "create"], capsys)
    unknown = tmp_path / "unknown.jsonl"
    unknown.write_text(json.dumps({"card_id": "PR-001", "outcome": "unknown",
                                   "op_note": "PUT response lost"}) + "\n",
                       encoding="utf-8")
    run(common + ["attempt", "collect", "AGT-001.1", "--file", str(unknown)],
        capsys)
    assert Store.load(store).leases.get("o/r").state == "quarantined"
    code, out, err = run(common + ["pr", "evaluate", "o/r#7", "--file",
                                   str(obs_path), "--dependency-only",
                                   "--json"], capsys)
    assert code == 3, (out, err)
    assert json.loads(err)["error"]["code"] == "not_found"
    code, out, err = run(common + ["pr", "observe", "o/r#7", "--json"], capsys)
    assert code == 3 and json.loads(err)["error"]["code"] == "not_found"
    code, out, err = run(common + ["pr", "evaluate", "PR-001", "--file",
                                   str(obs_path), "--dependency-only",
                                   "--attempt", "AGT-001.1", "-o", "json"],
                         capsys)
    assert code == 0, err
    assert json.loads(out)["outcome"]["reason_code"] == "K11"
