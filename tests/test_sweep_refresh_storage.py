"""Read-only refreshes retain provenance without recopying old payloads."""

import json
from pathlib import Path
import sys

SCRIPTS = (Path(__file__).resolve().parents[1]
           / "plugins/repo-hygiene/skills/dependabot-sweep/scripts")
sys.path.insert(0, str(SCRIPTS))

import sweep_coordinator as coord
import sweep_report as report
from sweep_core import Store


def make_store(tmp_path):
    store = Store(str(tmp_path / "run.jsonl"), session="refresh-test")
    coord.create_run(store, "refresh", "automated", "test", [{
        "org": "acme", "repo": "project", "number": 1,
        "url": "https://github.com/acme/project/pull/1", "head_sha": "a" * 40}])
    return store


def observation(index, payload_bytes=32768):
    return {
        "repository": "acme/project", "number": 1,
        "observed_at": f"2099-01-01T00:00:{index:02d}Z",
        "head_sha": f"{index:040x}",
        "files": {"data": [{"filename": "package-lock.json",
                             "patch": f"snapshot-{index}-" + "x" * payload_bytes}]},
        "check_runs": {"data": {"check_runs": [{"conclusion": "success"}]}},
        "threads": {"data": [{"isResolved": False}]},
    }


def marker(snapshot):
    return {"kind": "read_only_refresh", "observed_at": snapshot["observed_at"],
            "observed_head": snapshot["head_sha"]}


def test_refresh_keeps_full_current_and_historical_observations_replayable(tmp_path):
    store = make_store(tmp_path)
    first, second = observation(1), observation(2)
    coord.refresh_card(store, "PR-001", first)
    historical = tmp_path / "historical-prefix.jsonl"
    historical.write_bytes(Path(store.path).read_bytes())
    result = coord.refresh_card(store, "PR-001", second)

    assert result["snapshot"] == second
    assert store.cards["PR-001"].evidence == [marker(first), marker(second)]
    assert Store.load(str(historical)).cards["PR-001"].latest_observation["snapshot"] == first
    loaded = Store.load(store.path)
    assert loaded.cards["PR-001"].latest_observation == result
    assert loaded.cards["PR-001"].evidence == [marker(first), marker(second)]
    text = report.render_report(loaded)
    assert f"Read-only observation at {second['observed_at']}: head {second['head_sha']}" in text
    assert "check_runs: success=1; unresolved review threads=1" in text
    assert "This observation does not establish merge readiness." in text
    result["snapshot"]["files"]["data"][0]["patch"] = "caller mutation"
    assert store.cards["PR-001"].latest_observation["snapshot"] == second


def test_later_card_and_condition_history_writes_do_not_repeat_old_snapshot(tmp_path):
    store = make_store(tmp_path)
    task = coord.schedule(store, now=100, pr_budget_secs=600)[0]
    first, second = observation(1), observation(2)
    coord.refresh_card(store, "PR-001", first)
    offset = Path(store.path).stat().st_size
    coord.refresh_card(store, "PR-001", second)
    coord.apply_outcome(store, task["attempt_id"], [{
        "card_id": "PR-001", "outcome": "ready", "head_sha": second["head_sha"],
        "reason_line": "Exact head evaluated", "evidence": [{"id": "EV-check",
        "what": "Checks evaluated", "establishes": "Current head checked"}]}])

    later_records = Path(store.path).read_bytes()[offset:]
    assert first["files"]["data"][0]["patch"].encode() not in later_records
    card = Store.load(store.path).cards["PR-001"]
    assert card.condition_history[-1]["evidence"] == [marker(first), marker(second)]
    assert "snapshot" not in json.dumps(card.condition_history)
    assert card.latest_observation["snapshot"] == second


def test_legacy_full_evidence_copy_still_loads_and_new_refresh_uses_marker(tmp_path):
    store = make_store(tmp_path)
    first, second = observation(1), observation(2)
    legacy = {"observed_at": first["observed_at"], "observed_head": first["head_sha"],
              "snapshot": first}
    card = store.cards["PR-001"]
    card.latest_observation = legacy
    card.evidence.append({"kind": "read_only_refresh", **legacy})
    store.upsert_card(card)

    loaded = Store.load(store.path, session="refresh-test")
    assert loaded.cards["PR-001"].latest_observation == legacy
    assert loaded.cards["PR-001"].evidence[0]["snapshot"] == first
    coord.refresh_card(loaded, "PR-001", second)
    replayed = Store.load(store.path).cards["PR-001"]
    assert replayed.evidence[0]["snapshot"] == first
    assert replayed.evidence[1] == marker(second)
    assert replayed.latest_observation["snapshot"] == second
