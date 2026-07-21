"""Tests for the repo-finder CLI script.

Run: uv run --with pytest pytest plugins/repo-finder/tests/ -q

Builds a fixture tree of real git repos (checkout, group-dir nested, worktree,
excluded, vendored-nested) and drives the script via subprocess, asserting the
interface spec in docs/cli-interface.md (exit codes R6.1/R6.2, stdout/stderr
split R7.1, JSON contract R7.2/R7.8).
"""

import json
import os
import re
import subprocess
import textwrap
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent.parent / "skills" / "repo-finder" / "scripts" / "repo-finder"


def git(*args, cwd):
    subprocess.run(
        ["git", *args], cwd=cwd, check=True, capture_output=True,
        env={**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
             "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"},
    )


def make_repo(path: Path, origin: str | None = None):
    path.mkdir(parents=True, exist_ok=True)
    git("init", "-q", "-b", "main", cwd=path)
    (path / "README.md").write_text(f"# {path.name}\n")
    git("add", ".", cwd=path)
    git("commit", "-q", "-m", "init", cwd=path)
    if origin:
        git("remote", "add", "origin", origin, cwd=path)
    return path


@pytest.fixture()
def tree(tmp_path):
    """root/ alpha, claim/claim-npm (group), _archive/old (excluded),
    alpha vendored copy inside beta, wt/alpha-fix (worktree of alpha)."""
    root = tmp_path / "c"
    wt = tmp_path / "wt"
    wt.mkdir()
    alpha = make_repo(root / "alpha", "https://github.com/example/alpha.git")
    (alpha / "pyproject.toml").write_text("[project]\nname='alpha'\n")
    (alpha / "justfile").write_text("default:\n\techo hi\n")
    make_repo(root / "claim" / "claim-npm", "git@github.com:example/claim-npm.git")
    make_repo(root / "_archive" / "old-alpha")
    beta = make_repo(root / "beta")
    make_repo(beta / "vendor" / "alpha")  # nested inside beta's tree
    git("worktree", "add", "-q", str(wt / "alpha-fix"), "-b", "fix", cwd=alpha)
    # real-world layout: worktrees grouped under the repo name but each
    # directory named for its TOPIC, so the repo name appears nowhere in it
    git("worktree", "add", "-q", str(wt / "alpha" / "xdg-config-rework"),
        "-b", "xdg-config-rework", cwd=alpha)

    config = tmp_path / "repo-finder_config.toml"
    config.write_text(textwrap.dedent(f"""\
        [[roots]]
        path = "{root}"
        exclude = ["_archive"]

        [[roots]]
        path = "{wt}"

        [orgs]
        owned = ["example-org", "example-labs"]
        member = ["big-org"]

        [remote]
        enabled = false
        """))
    return {"root": root, "wt": wt, "config": config, "tmp": tmp_path}


def run(args, tree, gh_stub=None, check=False):
    env = {**os.environ, "XDG_CONFIG_HOME": str(tree["tmp"] / "xdg-empty")}
    if gh_stub is not None:
        bindir = tree["tmp"] / "bin"
        bindir.mkdir(exist_ok=True)
        gh = bindir / "gh"
        gh.write_text(gh_stub)
        gh.chmod(0o755)
        env["PATH"] = f"{bindir}:{env['PATH']}"
    return subprocess.run(
        [str(SCRIPT), "--config", str(tree["config"]), *args],
        capture_output=True, text=True, env=env, check=check,
    )


# --- basics (R4.1, R7.9, R6.1) ---

def test_help_exits_zero_on_stdout(tree):
    r = run(["--help"], tree)
    assert r.returncode == 0
    assert "repo-finder" in r.stdout


def test_version_exits_zero(tree):
    r = run(["--version"], tree)
    assert r.returncode == 0
    assert r.stdout.strip()


def test_version_matches_plugin_metadata(tree):
    """The CLI's reported version is the installed-contract signal; it must not
    drift from the plugin version consumers install (caught in PR #3)."""
    meta = (Path(__file__).parent.parent / "plugin.meta.toml").read_text()
    declared = re.search(r'^version = "([^"]+)"', meta, re.M).group(1)
    r = run(["--version"], tree)
    assert declared in r.stdout, f"CLI reports {r.stdout.strip()!r}, meta says {declared}"


def test_unknown_command_usage_error(tree):
    r = run(["frobnicate"], tree)
    assert r.returncode == 2


# --- find: local resolution ---

def test_find_exact_match(tree):
    r = run(["find", "alpha"], tree)
    assert r.returncode == 0
    assert str(tree["root"] / "alpha") in r.stdout
    assert "github.com/example/alpha" in r.stdout
    assert "main" in r.stdout


def test_find_group_dir_repo(tree):
    r = run(["find", "claim-npm"], tree)
    assert r.returncode == 0
    assert str(tree["root"] / "claim" / "claim-npm") in r.stdout


def test_find_excluded_root_is_invisible(tree):
    r = run(["find", "old-alpha"], tree)
    assert r.returncode == 3


def test_find_partial_match(tree):
    r = run(["find", "alph"], tree)
    assert r.returncode == 0
    assert "alpha" in r.stdout


def test_find_ranking_checkout_then_worktree_then_nested(tree):
    r = run(["find", "alpha"], tree)
    text = r.stdout
    canon = text.index(str(tree["root"] / "alpha"))
    wt_pos = text.index(str(tree["wt"] / "alpha-fix"))
    nested_pos = text.index(str(tree["root"] / "beta" / "vendor" / "alpha"))
    assert canon < wt_pos < nested_pos


def test_find_repo_returns_topic_named_worktrees(tree):
    """Searching a repo's name must return its worktrees even when their
    directories are named for the topic, not the repo — otherwise every
    worktree is invisible to the search the tool exists to answer."""
    r = run(["find", "alpha", "--no-remote"], tree)
    assert r.returncode == 0
    topic_wt = str(tree["wt"] / "alpha" / "xdg-config-rework")
    assert topic_wt in r.stdout, "topic-named worktree missing from a repo-name search"


def test_topic_worktree_json_links_main(tree):
    r = run(["find", "alpha", "--no-remote", "--json"], tree)
    matches = json.loads(r.stdout)
    topic = next(m for m in matches
                 if m["path"] == str(tree["wt"] / "alpha" / "xdg-config-rework"))
    assert topic["kind"] == "worktree"
    assert topic["worktree_of"] == str(tree["root"] / "alpha")


def test_find_worktree_links_main_and_shows_branch(tree):
    r = run(["find", "alpha-fix"], tree)
    assert r.returncode == 0
    assert "worktree" in r.stdout
    assert str(tree["root"] / "alpha") in r.stdout  # linked main repo
    assert "fix" in r.stdout


def test_find_shows_tooling_profile(tree):
    r = run(["find", "alpha"], tree)
    assert "pyproject.toml" in r.stdout or "uv" in r.stdout
    assert "just" in r.stdout


def test_find_miss_exits_3_diagnostics_on_stderr(tree):
    r = run(["find", "zzz-nope", "--no-remote"], tree)
    assert r.returncode == 3
    assert r.stdout.strip() == ""
    assert r.stderr.strip()  # suggestions are diagnostics (R6.2/R7.6)


def test_find_extra_root_flag(tree):
    extra = tree["tmp"] / "elsewhere"
    make_repo(extra / "gamma")
    r = run(["find", "gamma", "--root", str(extra)], tree)
    assert r.returncode == 0
    assert str(extra / "gamma") in r.stdout


# --- find: JSON contract (R7.2/R7.8) ---

def test_find_json(tree):
    r = run(["find", "alpha", "--json"], tree)
    assert r.returncode == 0
    matches = json.loads(r.stdout)
    assert isinstance(matches, list)
    kinds = {m["kind"] for m in matches}
    assert {"checkout", "worktree", "nested"} <= kinds
    canon = next(m for m in matches if m["kind"] == "checkout"
                 and m["path"] == str(tree["root"] / "alpha"))
    assert canon["origin"].endswith("example/alpha.git")
    assert canon["default_branch"] == "main"
    assert isinstance(canon["tooling"], list)
    wt = next(m for m in matches if m["kind"] == "worktree")
    assert wt["worktree_of"] == str(tree["root"] / "alpha")


def test_find_miss_json_error_schema(tree):
    r = run(["find", "zzz-nope", "--no-remote", "--json"], tree)
    assert r.returncode == 3
    err = json.loads(r.stderr)
    assert err["error"]["code"] == "not_found"


# --- list / orgs ---

def test_list_all(tree):
    r = run(["list"], tree)
    assert r.returncode == 0
    assert "alpha" in r.stdout and "claim-npm" in r.stdout and "beta" in r.stdout
    assert "old-alpha" not in r.stdout


def test_list_empty_is_success(tree):
    empty = tree["tmp"] / "empty-root"
    empty.mkdir()
    cfg = tree["tmp"] / "empty.toml"
    cfg.write_text(f'[[roots]]\npath = "{empty}"\n')
    tree2 = {**tree, "config": cfg}
    r = run(["list"], tree2)
    assert r.returncode == 0


def test_orgs_from_config_no_network(tree):
    r = run(["orgs"], tree)
    assert r.returncode == 0
    assert "example-org" in r.stdout and "big-org" in r.stdout


# --- remote tier (gh stubbed on PATH; stubs branch per endpoint) ---

SEARCH_HIT = ('{"total_count":1,"items":[{"name":"remote-only",'
              '"full_name":"example-org/remote-only","default_branch":"main",'
              '"html_url":"https://github.com/example-org/remote-only"}]}')
LIST_PAGE = ('[{"name":"remote-only","full_name":"example-org/remote-only",'
             '"default_branch":"main",'
             '"html_url":"https://github.com/example-org/remote-only"}]')

GH_OK = f"""#!/bin/sh
echo "$@" >> "$GH_LOG"
case "$*" in
  *"auth status"*) exit 0 ;;
  *rate_limit*) echo 9999; exit 0 ;;
  *search/repositories*) echo '{SEARCH_HIT}'; exit 0 ;;
  *) echo '{LIST_PAGE}'; exit 0 ;;
esac
"""

GH_SEARCH_EMPTY = """#!/bin/sh
case "$*" in
  *"auth status"*) exit 0 ;;
  *rate_limit*) echo 9999; exit 0 ;;
  *search/repositories*) echo '{"total_count":0,"items":[]}'; exit 0 ;;
  *) echo '[]'; exit 0 ;;
esac
"""

GH_ALL_FAIL = """#!/bin/sh
case "$*" in
  *"auth status"*) exit 0 ;;
  *rate_limit*) echo 9999; exit 0 ;;
  *) echo "some opaque 403" >&2; exit 1 ;;
esac
"""

GH_SEARCH_LIMITED = f"""#!/bin/sh
echo "$@" >> "$GH_LOG"
case "$*" in
  *"auth status"*) exit 0 ;;
  *rate_limit*) echo 0; exit 0 ;;
  *search/repositories*) echo "403 secondary throttle" >&2; exit 1 ;;
  *) echo '{LIST_PAGE}'; exit 0 ;;
esac
"""

GH_UNAUTH = """#!/bin/sh
if [ "$1" = "auth" ]; then echo "not logged in" >&2; exit 1; fi
exit 1
"""


def enable_remote(tree):
    tree["config"].write_text(
        tree["config"].read_text().replace("enabled = false", "enabled = true"))


def test_find_remote_uses_search_api(tree):
    enable_remote(tree)
    log = tree["tmp"] / "gh.log"
    os.environ["GH_LOG"] = str(log)
    log.write_text("")
    r = run(["find", "remote-only"], tree, gh_stub=GH_OK)
    assert r.returncode == 0
    assert "remote-only" in r.stdout and "git clone" in r.stdout
    logged = log.read_text()
    assert "search/repositories" in logged
    assert "in:name" in logged and "user:example-org" in logged


GH_SEARCH_PAGED = """#!/bin/sh
echo "$@" >> "$GH_LOG"
case "$*" in
  *"auth status"*) exit 0 ;;
  *rate_limit*) echo 9999; exit 0 ;;
  *search/repositories*page=2*)
    echo '{"total_count":150,"items":[{"name":"deep-page-repo",'\\
'"full_name":"example-org/deep-page-repo","default_branch":"main",'\\
'"html_url":"https://github.com/example-org/deep-page-repo"}]}'; exit 0 ;;
  *search/repositories*)
    echo '{"total_count":150,"items":[{"name":"decoy","full_name":"example-org/decoy",'\\
'"default_branch":"main","html_url":"https://github.com/example-org/decoy"}]}'; exit 0 ;;
  *) echo '[]'; exit 0 ;;
esac
"""


def test_find_pages_search_results(tree):
    """A match beyond the first search page must not be reported as a clean
    miss — truncating page 1 produced false not-founds (caught in PR #3)."""
    enable_remote(tree)
    log = tree["tmp"] / "gh.log"
    os.environ["GH_LOG"] = str(log)
    log.write_text("")
    r = run(["find", "deep-page-repo"], tree, gh_stub=GH_SEARCH_PAGED)
    assert r.returncode == 0, f"page-2 match reported as miss: {r.stderr}"
    assert "deep-page-repo" in r.stdout
    assert "page=2" in log.read_text()


def test_find_clean_remote_miss_names_orgs(tree):
    enable_remote(tree)
    r = run(["find", "zzz-nope"], tree, gh_stub=GH_SEARCH_EMPTY)
    assert r.returncode == 3
    assert "example-org" in r.stderr  # message says remote WAS searched


def test_find_remote_failure_degraded_exit_1(tree):
    enable_remote(tree)
    r = run(["find", "zzz-nope"], tree, gh_stub=GH_ALL_FAIL)
    assert r.returncode == 1
    assert "LOCAL-ONLY" in r.stderr or "incomplete" in r.stderr


def test_find_remote_failure_json_schema(tree):
    enable_remote(tree)
    r = run(["find", "zzz-nope", "--json"], tree, gh_stub=GH_ALL_FAIL)
    assert r.returncode == 1
    assert json.loads(r.stderr)["error"]["code"] == "remote_lookup_failed"


def test_find_search_ratelimit_falls_back_to_listing(tree):
    enable_remote(tree)
    log = tree["tmp"] / "gh.log"
    os.environ["GH_LOG"] = str(log)
    log.write_text("")
    r = run(["find", "remote-only"], tree, gh_stub=GH_SEARCH_LIMITED)
    assert r.returncode == 0
    assert "remote-only" in r.stdout
    assert "repos?per_page=" in log.read_text()  # tier-2 listing ran


def test_org_listing_pages_and_warns_on_truncation(tree):
    log = tree["tmp"] / "gh.log"
    os.environ["GH_LOG"] = str(log)
    log.write_text("")
    r = run(["org", "example-org", "--limit", "1"], tree, gh_stub=GH_OK)
    assert r.returncode == 0
    assert "remote-only" in r.stdout
    assert "per_page=1" in log.read_text()  # page size respects the cap
    assert "--limit" in r.stderr  # full page => truncation warning


def test_remote_unauthenticated_exit_4(tree):
    enable_remote(tree)
    r = run(["find", "remote-only-name"], tree, gh_stub=GH_UNAUTH)
    assert r.returncode == 4


# --- init (exit 5 conflict) ---

def test_init_writes_then_conflicts(tree):
    xdg = tree["tmp"] / "xdg-empty"
    env_cfg_dir = xdg / "repo-finder"
    r1 = subprocess.run(
        [str(SCRIPT), "init"], capture_output=True, text=True,
        env={**os.environ, "XDG_CONFIG_HOME": str(xdg)},
    )
    assert r1.returncode == 0
    assert (env_cfg_dir / "repo-finder_config.toml").exists()
    r2 = subprocess.run(
        [str(SCRIPT), "init"], capture_output=True, text=True,
        env={**os.environ, "XDG_CONFIG_HOME": str(xdg)},
    )
    assert r2.returncode == 5
