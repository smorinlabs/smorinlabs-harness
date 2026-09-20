"""Offline behavior checks for Muse installer and credential-free CI preparation."""
from __future__ import annotations

import copy
import fnmatch
import importlib.util
import json
import os
from pathlib import Path
import subprocess

import pytest
import yaml

SKILL = Path(__file__).resolve().parents[1] / "plugins/muse-github/skills/muse-github-setup"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


installer = load("muse_installer", SKILL / "scripts/install.py")
ci = load("muse_ci", SKILL / "templates/.github/scripts/muse_ci.py")


def git(root, *args):
    env = {**os.environ, "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_NOSYSTEM": "1"}
    return subprocess.check_output(
        ["git", "-C", str(root), "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", *args],
        env=env, stderr=subprocess.DEVNULL, text=True,
    ).strip()


@pytest.fixture
def repo_pair(tmp_path):
    remote = tmp_path / "remote.git"
    author = tmp_path / "author"
    runner = tmp_path / "runner"
    remote.mkdir()
    author.mkdir()
    git(remote, "init", "--bare", "--initial-branch=main")
    git(author, "init", "--initial-branch=main")
    installer.apply(author, installer.plan(author, "fixture-org", with_fixes=True))
    (author / "app.py").write_text("answer = 1\n")
    git(author, "add", ".")
    git(author, "commit", "-m", "base")
    base = git(author, "rev-parse", "HEAD")
    git(author, "remote", "add", "origin", str(remote))
    git(author, "push", "-u", "origin", "main")
    git(author, "checkout", "-b", "feature/review")
    (author / "app.py").write_text("answer = 2\n")
    git(author, "commit", "-am", "first PR commit")
    head = git(author, "rev-parse", "HEAD")
    git(author, "push", "-u", "origin", "feature/review")
    git(tmp_path, "clone", str(remote), str(runner))
    return author, runner, base, head


def event(base="a" * 40, head="b" * 40):
    return {
        "repository": {"full_name": "fixture-org/project", "default_branch": "main",
                       "owner": {"login": "fixture-org", "type": "Organization"}},
        "pull_request": {"number": 7, "state": "open", "draft": False,
                         "user": {"login": "author", "type": "User"},
                         "base": {"sha": base, "ref": "main"},
                         "head": {"sha": head, "ref": "feature/review",
                                  "repo": {"full_name": "fixture-org/project"}}},
    }


class API:
    def __init__(self, payload, excluded=(), bots=(), readonly=()):
        self.payload = payload
        self.excluded = excluded
        self.bots = bots
        self.readonly = readonly
        self.calls = []

    def get(self, path):
        self.calls.append(path)
        login = path.split("/")[-1]
        if path.endswith("/pulls/7"):
            return self.payload["pull_request"]
        if path.startswith("users/"):
            return {"type": "Bot" if login in self.bots else "User"}
        if "/members/" in path:
            if login in self.excluded:
                raise ci.Refusal("Membership cannot be verified")
            return None
        if path.endswith("/permission"):
            return {"permission": "read" if path.split("/")[-2] in self.readonly else "write"}
        raise AssertionError(f"Unexpected request {path}")


def test_install_preserves_project_and_is_idempotent(tmp_path):
    (tmp_path / "AGENTS.md").write_text("# Project\nUse the repository's documented checks.\n")
    (tmp_path / "opencode.json").write_text(json.dumps({"model": "other/default", "provider": {"other": {}}}))
    (tmp_path / ".opencode").mkdir()
    (tmp_path / ".opencode/notes.md").write_text("Keep this.\n")
    changes = installer.plan(tmp_path, "fixture-org", with_fixes=True)
    assert not (tmp_path / ".github").exists()  # Planning is read-only.
    installer.apply(tmp_path, changes)
    assert (tmp_path / "AGENTS.md").read_text().startswith("# Project\nUse")
    assert (tmp_path / ".opencode/notes.md").read_text() == "Keep this.\n"
    config = json.loads((tmp_path / "opencode.json").read_text())
    assert config["model"] == "other/default" and "other" in config["provider"]
    assert config["provider"]["model_api"]["options"]["apiKey"] == "{env:META_MUSE_CI_API_KEY}"
    assert installer.plan(tmp_path, "fixture-org", with_fixes=True) == {}


def test_review_only_install_can_add_fixes_later(tmp_path):
    installer.apply(tmp_path, installer.plan(tmp_path, "fixture-org"))
    assert not (tmp_path / ".github/workflows/opencode-fix-pr.yml").exists()
    assert set(installer.plan(tmp_path, "fixture-org", with_fixes=True)) == {
        ".github/workflows/opencode-fix-pr.yml", ".opencode/muse-ci/fix.json",
    }


@pytest.mark.parametrize("filename,body", [
    ("opencode.jsonc", "{ // Preserve comments\n}"),
    ("opencode.json", '{"provider":{"model_api":{"name":"Existing"}}}'),
    (".github/workflows/opencode-pr-review.yml", "name: Existing\n"),
    ("AGENTS.md", installer.MARKER + "\nCustom policy\n"),
])
def test_conflicts_are_not_overwritten(tmp_path, filename, body):
    target = tmp_path / filename
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(body)
    with pytest.raises(installer.Conflict):
        installer.plan(tmp_path, "fixture-org")
    assert target.read_text() == body
    assert not (tmp_path / ".opencode/muse-ci/policy.json").exists()


def test_install_rejects_symlink_parent(tmp_path):
    root = tmp_path / "project"
    root.mkdir()
    other = tmp_path / "outside"
    other.mkdir()
    (root / ".github").symlink_to(other, target_is_directory=True)
    with pytest.raises(installer.Conflict, match="symlink"):
        installer.plan(root, "fixture-org")
    assert list(other.iterdir()) == []


def test_membership_and_write_are_independent_and_all_actors_checked():
    payload = event()
    api = API(payload)
    ci.authorize(payload, "review", "original", "rerunner", api, api, "fixture-org")
    assert {x.rsplit("/", 1)[-1] for x in api.calls if "/members/" in x} == {"author", "original", "rerunner"}
    for subject in ("author", "original", "rerunner"):
        excluded = API(payload, excluded={subject})
        with pytest.raises(ci.Refusal, match="Membership"):
            ci.authorize(payload, "review", "original", "rerunner", excluded, excluded, "fixture-org")
    api = API(payload, readonly={"original"})
    with pytest.raises(ci.Refusal, match="write access"):
        ci.authorize(payload, "review", "original", "rerunner", api, api, "fixture-org")


@pytest.mark.parametrize("case", ["fork", "draft", "bot", "closed", "wrong_base", "personal"])
def test_ineligible_reviews_fail_before_membership_calls(case):
    payload = event()
    pr = payload["pull_request"]
    if case == "fork":
        pr["head"]["repo"]["full_name"] = "someone/fork"
    elif case == "draft":
        pr["draft"] = True
    elif case == "bot":
        pr["user"]["type"] = "Bot"
    elif case == "closed":
        pr["state"] = "closed"
    elif case == "wrong_base":
        pr["base"]["ref"] = "other"
    else:
        payload["repository"]["owner"]["type"] = "User"
    api = API(payload)
    with pytest.raises(ci.Refusal):
        ci.authorize(payload, "review", "original", "rerunner", api, api, "fixture-org")
    assert not any("/members/" in x for x in api.calls)


def test_stale_head_and_unknown_membership_fail_closed():
    payload = event()
    changed = copy.deepcopy(payload)
    changed["pull_request"]["head"]["sha"] = "c" * 40
    with pytest.raises(ci.Refusal, match="changed after"):
        ci.authorize(payload, "review", "original", "rerunner", API(changed), API(payload), "fixture-org")
    api = API(payload, excluded={"rerunner"})
    with pytest.raises(ci.Refusal):
        ci.authorize(payload, "review", "original", "rerunner", api, api, "fixture-org")


def test_manual_fix_requires_default_ref_humans_and_members():
    payload = event()
    payload["ref"] = "feature/untrusted"
    api = API(payload)
    with pytest.raises(ci.Refusal, match="default branch"):
        ci.authorize(payload, "fix", "original", "rerunner", api, api, "fixture-org")
    payload["ref"] = "refs/heads/main"
    api = API(payload, bots={"rerunner"})
    with pytest.raises(ci.Refusal, match="Bots"):
        ci.authorize(payload, "fix", "original", "rerunner", api, api, "fixture-org")
    api = API(payload)
    ci.authorize(payload, "fix", "original", "rerunner", api, api, "fixture-org")
    assert not any("pulls/" in x for x in api.calls)


def test_upstream_fetch_cannot_advance_frozen_local_branch(repo_pair):
    author, runner, _, expected = repo_pair
    ci.freeze_branch(runner, "feature/review", expected)
    (author / "app.py").write_text("answer = 3\n")
    git(author, "commit", "-am", "newer commit")
    git(author, "push", "origin", "feature/review")
    newer = git(author, "rev-parse", "HEAD")
    # Actual v1.18.31 checkoutLocalBranch sequence, after remote advancement.
    git(runner, "fetch", "origin", "--depth=20", "feature/review")
    git(runner, "checkout", "feature/review")
    assert git(runner, "rev-parse", "HEAD") == expected
    assert git(runner, "rev-parse", "origin/feature/review") == newer
    assert (runner / "app.py").read_text() == "answer = 2\n"


def test_prepare_generates_isolated_configuration_and_exact_diff(repo_pair, tmp_path, monkeypatch):
    _, runner, base, head = repo_pair
    payload = event(base, head)
    api = API(payload)
    monkeypatch.setattr(ci, "GitHub", lambda token: api)
    event_path = tmp_path / "event.json"
    event_path.write_text(json.dumps(payload))
    environ = {
        "GITHUB_WORKSPACE": str(runner), "GITHUB_EVENT_PATH": str(event_path),
        "GITHUB_EVENT_NAME": "pull_request", "GITHUB_REPOSITORY": "fixture-org/project",
        "GITHUB_ACTOR": "original", "MUSE_TRIGGERING_ACTOR": "rerunner", "GH_TOKEN": "fixture-value",
        "RUNNER_TEMP": str(tmp_path), "GITHUB_ENV": str(tmp_path / "env"), "GITHUB_OUTPUT": str(tmp_path / "output"),
        "GITHUB_STEP_SUMMARY": str(tmp_path / "summary"),
    }
    ci.prepare("review", environ)
    runtimes = list(tmp_path.glob("muse-ci-*"))
    assert len(runtimes) == 1
    config = json.loads((runtimes[0] / "config.json").read_text())
    assert config["permission"] == {"*": "deny"}
    assert config["default_agent"] == "muse-review" and config["share"] == "disabled"
    assert config["formatter"] is False and config["lsp"] is False
    assert config["small_model"] == ci.MODEL
    assert "fixture-value" not in (runtimes[0] / "config.json").read_text()
    output = (tmp_path / "output").read_text()
    assert head in output and "-answer = 1" in output and "+answer = 2" in output
    env_file = (tmp_path / "env").read_text()
    assert "OPENCODE_DISABLE_PROJECT_CONFIG" in env_file and "fixture-value" not in env_file
    assert git(runner, "status", "--porcelain") == ""
    state = runtimes[0] / "state.json"
    ci.finish("review", {**environ, "MUSE_CI_STATE": str(state)})
    assert head in (tmp_path / "summary").read_text()
    api.payload = copy.deepcopy(payload)
    api.payload["pull_request"]["head"]["sha"] = "c" * 40
    with pytest.raises(ci.Refusal, match="stale"):
        ci.finish("review", {**environ, "MUSE_CI_STATE": str(state)})
    assert "c" * 40 in (tmp_path / "summary").read_text()


def test_fix_refuses_symlink(repo_pair):
    _, runner, _, _ = repo_pair
    (runner / "shortcut").symlink_to("app.py")
    git(runner, "add", "shortcut")
    with pytest.raises(ci.Refusal, match="symlinks"):
        ci.validate_tree(runner, "fix")


@pytest.mark.parametrize("path", [
    ".npmrc", "config/.PyPiRc", ".NETRC", "keys/credentials.json",
    ".aws/credentials", ".git-credentials", "keys/id_rsa", "keys/id_ED25519",
    "certs/signing.P12", "certs/signing.PFX", "certs/signing.JKS",
    "certs/signing.KEYSTORE", "config/prod.EnV", "keys/private.PEM",
])
def test_fix_refuses_tracked_credential_paths_before_model_access(tmp_path, monkeypatch, path):
    monkeypatch.setattr(ci, "git", lambda *_: "100644 " + "a" * 40 + " 0\t" + path)
    with pytest.raises(ci.Refusal, match="credential-like"):
        ci.validate_tree(tmp_path, "fix")
    assert ci.sensitive(path)  # The same paths must also stay out of review diffs.


def test_fix_accepts_ordinary_tracked_project_files(tmp_path, monkeypatch):
    monkeypatch.setattr(ci, "git", lambda *_: "100644 " + "a" * 40 + " 0\tsrc/app.py")
    ci.validate_tree(tmp_path, "fix")
    assert not ci.sensitive("src/app.py")


def test_fix_rules_cover_mixed_case_sensitive_paths_and_preserve_normal_edits():
    config = ci.configuration(SKILL / "templates", "fix")
    # Exercise the documented last-match wildcard policy on the generated rules.
    for tool in ("read", "edit"):
        rules = config["permission"][tool]
        for name in (".env", "config/.ENV", "prod.EnV.local", "keys/private.PEM", "test.kEy"):
            matching = [action for pattern, action in rules.items() if fnmatch.fnmatchcase(name, pattern)]
            assert matching[-1] == "deny", (tool, name)
        matching = [action for pattern, action in rules.items() if fnmatch.fnmatchcase("src/app.py", pattern)]
        assert matching[-1] == "allow"
    rules = config["permission"]["edit"]
    assert [v for k, v in rules.items() if fnmatch.fnmatchcase(".github/workflows/ci.yml", k)][-1] == "deny"


@pytest.mark.parametrize("kind", ["large", "encoded_large", "credential"])
def test_unsafe_review_input_never_publishes_model_prompt(repo_pair, tmp_path, monkeypatch, kind):
    author, runner, base, _ = repo_pair
    filename = "config/prod.EnV" if kind == "credential" else "app.py"
    target = author / filename
    target.parent.mkdir(exist_ok=True)
    target.write_text("private fixture" if kind == "credential" else ("x" * 61000 if kind == "large" else "\x01" * 50000))
    git(author, "add", ".")
    git(author, "commit", "-m", "negative control")
    git(author, "push", "origin", "feature/review")
    head = git(author, "rev-parse", "HEAD")
    payload = event(base, head)
    monkeypatch.setattr(ci, "GitHub", lambda token: API(payload))
    event_path = tmp_path / "event.json"
    event_path.write_text(json.dumps(payload))
    environ = {
        "GITHUB_WORKSPACE": str(runner), "GITHUB_EVENT_PATH": str(event_path),
        "GITHUB_EVENT_NAME": "pull_request", "GITHUB_REPOSITORY": "fixture-org/project",
        "GITHUB_ACTOR": "original", "MUSE_TRIGGERING_ACTOR": "rerunner", "GH_TOKEN": "fixture-value",
        "RUNNER_TEMP": str(tmp_path), "GITHUB_ENV": str(tmp_path / "env"), "GITHUB_OUTPUT": str(tmp_path / "output"),
    }
    message = {"large": "diff limit", "encoded_large": "Encoded prompt", "credential": "credential-like"}[kind]
    with pytest.raises(ci.Refusal, match=message):
        ci.prepare("review", environ)
    assert not (tmp_path / "env").exists()
    assert not (tmp_path / "output").exists()


def test_templates_have_separate_events_and_only_step_scoped_secrets():
    documents = {
        name: yaml.load((SKILL / f"templates/.github/workflows/opencode-{name}.yml").read_text(), Loader=yaml.BaseLoader)
        for name in ("pr-review", "fix-pr")
    }
    assert set(documents["pr-review"]["on"]) == {"pull_request"}
    assert set(documents["fix-pr"]["on"]) == {"workflow_dispatch"}
    for document in documents.values():
        assert document["permissions"] == {}
        assert "env" not in document
        job = next(iter(document["jobs"].values()))
        assert "env" not in job and "id-token" not in job["permissions"]
        action = next(step for step in job["steps"] if step.get("uses", "").startswith("anomalyco/"))
        assert action["with"]["model"] == ci.MODEL
        assert action["with"]["share"] == "false" and action["with"]["use_github_token"] == "true"
        assert "MUSE_MEMBERS_TOKEN" not in action["env"]
        assert len(action["uses"].rsplit("@", 1)[1]) == 40
