"""Explicit scope precedence and case-insensitive inventory identity."""

import json
import sys
from copy import deepcopy
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "plugins/repo-hygiene/skills/dependabot-sweep/scripts"
sys.path.insert(0, str(SCRIPTS))

import sweep_cli as cli
import sweep_config as cfg
import sweep_coordinator as coord
import sweep_discovery as discovery
import sweep_report as report
from sweep_core import Store


def config_file(tmp_path, kind="org"):
    path = tmp_path / "scope.toml"
    path.write_text(f'[{kind}."acme"]\nrepos = ["one"]\n'
                    'visibility = "public"\nauto_fix = false\n'
                    'pause_on_conflict = true\nreviewer_contexts = ["review-bot"]\n')
    return path


def found(number, repo, visibility="public"):
    return {"org": "acme", "repo": repo, "number": number,
            "url": f"https://github.com/acme/{repo}/pull/{number}",
            "title": "Update dependency", "head_sha": "a" * 40,
            "visibility": visibility}


def test_explicit_repo_overrides_configured_repository_selection(tmp_path):
    path = tmp_path / "scope.toml"
    path.write_text('[org."acme"]\nrepos = ["one"]\n')
    config = cfg.load_config(str(path), {"repo": ["acme/two"]}, {})
    effective = config.scope_for("acme")
    assert effective.repos == ["two"]
    assert effective.mode == "automated"


@pytest.mark.parametrize("kind", ["org", "user"])
def test_explicit_repo_selection_preserves_owner_behavior_and_visibility(tmp_path, kind):
    config = cfg.load_config(str(config_file(tmp_path, kind)),
                             {"repo": ["ACME/two"], "mode": "automated"}, {})
    effective = config.scope_for("acme")
    assert config.scopes[0].kind == "repo"
    assert effective.repos == ["two"]
    assert effective.visibility == "public"
    assert effective.mode == "inspect" and effective.repairs == []
    assert effective.pause_on_conflict is True
    assert effective.reviewer_contexts == ["review-bot"]


def create_cli_run(tmp_path, capsys, flags, items):
    inputs = tmp_path / "discoveries.json"
    inputs.write_text(json.dumps(items))
    path = tmp_path / "run.jsonl"
    code = cli.main(["--store", str(path), "--config", str(config_file(tmp_path)),
                     "--session", "review", "run", "create", "--run-id", "scope",
                     "--file", str(inputs), *flags, "--json"])
    captured = capsys.readouterr()
    assert code == 0, captured.err
    return Store.load(str(path), session="review")


@pytest.mark.parametrize("flags,selected", [
    (["--repo", "acme/two"], "acme/two"),
    (["--org", "acme"], "acme/one"),
    ([], "acme/one"),
])
def test_cli_explicit_selection_does_not_grant_owner_wide_authority(
        tmp_path, capsys, flags, selected):
    store = create_cli_run(tmp_path, capsys, flags,
                           [found(1, "one"), found(2, "two"), found(3, "three")])
    assert set(store.header.authority["repositories"]) == {selected}
    assert [store.cards[c].repo_id for c in store.header.scope_ids] == [selected]
    grant = store.header.authority["repositories"][selected]
    assert grant["mode"] == "inspect" and grant["repairs"] == []
    assert grant["pause_on_conflict"] is True
    assert grant["reviewer_contexts"] == ["review-bot"]
    assert store.header.authority["discovery_scopes"][0]["repos"] == [selected.split("/")[1]]


@pytest.mark.parametrize("visibility,selected", [("public", True), ("private", False)])
def test_cli_explicit_repo_still_requires_matching_visibility(tmp_path, capsys, visibility, selected):
    store = create_cli_run(tmp_path, capsys, ["--repo", "acme/two"],
                           [found(2, "two", visibility)])
    assert store.header.scope_ids == (["PR-001"] if selected else [])
    assert set(store.header.authority["repositories"]) == ({"acme/two"} if selected else set())
    assert not store.diary and not store.leases.leases


def inventory_fixture(tmp_path, listed, response_name="acme/one"):
    grant = {"mode": "inspect", "repairs": [], "pause_on_conflict": False,
             "reviewer_contexts": []}
    authority = {"repositories": {}, "discovery_scopes": [
        {"kind": "org", "login": "acme", "visibility": "public", "repos": [],
         "authority": grant}]}
    store = Store(str(tmp_path / "run.jsonl"), session="review")
    coord.create_run(store, "scope", "inspect", "test", [found(1, "One")], authority=authority)
    payload = {"observed_at": "2099-01-01T00:00:00Z", "complete": True,
               "source": "complete repository and PR inventory",
               "coverage": discovery.coverage(store.header.authority),
               "scope_repositories": listed,
               "repositories": [{"nameWithOwner": response_name, "visibility": "public"}],
               "discoveries": [found(1, "one")]}
    return store, payload


@pytest.mark.parametrize("listed,response_name", [
    (["acme/one"], "acme/one"),
    (["ACME/ONE"], "acme/One"),
    (["acme/one", "ACME/ONE"], "ACME/one"),
])
def test_inventory_case_aliases_complete_with_one_canonical_identity(
        tmp_path, listed, response_name):
    store, payload = inventory_fixture(tmp_path, listed, response_name)
    card_before = deepcopy(store.cards["PR-001"].to_dict())
    result = coord.discover_run(store, payload)
    assert result["snapshot"]["complete"] is True
    assert result["snapshot"]["scope_repositories"] == ["acme/One"]
    assert result["snapshot"]["open_card_ids"] == ["PR-001"]
    assert result["new_card_ids"] == []
    assert store.cards["PR-001"].to_dict() == card_before
    assert set(store.header.authority["repositories"]) == {"acme/One"}
    reloaded = Store.load(store.path)
    assert report.report_snapshot(reloaded)["live_open"]["count"] == 1
    assert reloaded.header.discovery_snapshot["evidence"]["repositories"] == payload["repositories"]
    assert not reloaded.diary and not reloaded.leases.leases


@pytest.mark.parametrize("listed", [[], ["ACME/ONE", "acme/missing"]])
def test_case_normalization_does_not_hide_inventory_coverage_gaps(tmp_path, listed):
    store, payload = inventory_fixture(tmp_path, listed)
    result = coord.discover_run(store, payload)
    assert result["snapshot"]["complete"] is False
    assert result["snapshot"]["incomplete_reasons"]
    assert report.report_snapshot(store)["live_open"]["count"] is None
    assert set(store.header.authority["repositories"]) == {"acme/One"}
