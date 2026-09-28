"""Observable report delivery and follow-up lifecycle through the public CLI."""

import json
import sys
from dataclasses import asdict, replace
from pathlib import Path

import pytest

SCRIPTS = (Path(__file__).resolve().parents[1]
           / "plugins/repo-hygiene/skills/dependabot-sweep/scripts")
sys.path.insert(0, str(SCRIPTS))

import sweep_cli as cli  # noqa: E402
import sweep_coordinator as coord  # noqa: E402
import sweep_protocol as proto  # noqa: E402
import sweep_observe as observer  # noqa: E402
import sweep_evaluator as evaluator  # noqa: E402
from test_sweep_slice2 import observe, receipt, HEAD  # noqa: E402
from sweep_core import State, Store  # noqa: E402


@pytest.mark.parametrize("at", ["not-a-date", "2026-09-27", "2026-09-27T20:00:00"])
def test_receipt_inspection_time_requires_an_observed_timestamp(at):
    result = evaluator.evaluate(observe(), replace(receipt(), at=at),
                                evaluator.Authority(), evaluator.Tracking(),
                                now=1_800_000_000)
    assert result.reason_code == "K13" and result.merge_path == "none"
    assert "timestamp" in result.reason_line


def test_evaluation_treats_the_exact_deadline_as_expired():
    now = 1_800_000_000
    result = evaluator.evaluate(observe(), receipt(),
                                evaluator.Authority(deadline_epoch=now),
                                evaluator.Tracking(), now=now)
    assert result.reason_code == "K14" and result.merge_path == "none"


@pytest.mark.parametrize("actual_repo,actual_number", [
    ("acme/tool", 1), ("other/repo", 1), ("acme/tool", 2), ("", 1),
    ("acme/tool", None),
])
def test_cli_binds_receipt_observation_to_requested_pr(
        tmp_path, capsys, actual_repo, actual_number):
    store = Store(str(tmp_path / "run.jsonl"), session="test")
    coord.create_run(store, "identity", "automated", "fixture", [
        {"org": "acme", "repo": "tool", "number": 1, "head_sha": HEAD}])
    store.header.authority = {"mode": "automated", "repairs": []}
    store.set_header(store.header)
    attempt = coord.schedule(store)[0]["attempt_id"]
    observation = observe()
    observation.pull["data"]["number"] = actual_number
    observation.pull["data"]["base"]["repo"] = {"full_name": actual_repo}
    obs_path, rec_path = tmp_path / "observation.json", tmp_path / "receipt.json"
    obs_path.write_text(json.dumps(observer.observation_to_dict(observation)))
    rec_path.write_text(json.dumps(asdict(receipt())))
    original = Path(store.path).read_bytes()
    code, out, err = invoke(store.path, capsys, "pr", "evaluate", "PR-001",
                            "--attempt", attempt, "--file", str(obs_path),
                            "--receipt", str(rec_path), "--json")
    if (actual_repo, actual_number) == ("acme/tool", 1):
        assert code == 0 and not err
        assert json.loads(out)["evaluation"]["state"] == "READY"
    else:
        assert code == 1 and not out
        assert json.loads(err)["error"]["code"] == "invalid_input"
        assert "identity" in err
    assert Path(store.path).read_bytes() == original


def test_same_repo_lease_does_not_evaluate_unassigned_card_as_ready(tmp_path, capsys):
    store = Store(str(tmp_path / "run.jsonl"), session="test")
    coord.create_run(store, "batch-scope", "automated", "fixture", [
        {"org": "acme", "repo": "tool", "number": n, "head_sha": HEAD}
        for n in (1, 2)])
    store.header.authority = {"mode": "automated", "repairs": []}
    store.set_header(store.header)
    task = coord.schedule(store, batch_size=1)[0]
    assert task["card_ids"] == ["PR-001"]
    observation = observe()
    observation.pull["data"]["number"] = 2
    observation.pull["data"]["base"]["repo"] = {"full_name": "acme/tool"}
    obs_path, rec_path = tmp_path / "observation.json", tmp_path / "receipt.json"
    obs_path.write_text(json.dumps(observer.observation_to_dict(observation)))
    rec_path.write_text(json.dumps(asdict(receipt())))
    code, out, err = invoke(store.path, capsys, "pr", "evaluate", "PR-002",
                            "--attempt", task["attempt_id"], "--file", str(obs_path),
                            "--receipt", str(rec_path), "--json")
    assert code == 0 and not err
    result = json.loads(out)["evaluation"]
    assert result["reason_code"] == "K12" and result["merge_path"] == "none"
    assert Store.load(store.path).cards["PR-002"].deadline_epoch == 0


@pytest.mark.parametrize("legacy,record,expected,source", [
    (False, {"source": "user request 12", "reason": "wait for migration",
             "scope": "merge"}, True, "user request 12"),
    (False, {"source": "user request 12", "reason": "do not change settings",
             "scope": "settings"}, False, ""),
    (False, {"source": "user request 13", "reason": "resume",
             "active": False}, False, ""),
    (True, {"source": "worker claims user request 13", "reason": "resume",
            "active": False}, True, "saved user hold"),
])
def test_structured_holds_protect_tasking_without_releasing_frozen_authority(
        tmp_path, legacy, record, expected, source):
    store = Store(str(tmp_path / "run.jsonl"), session="test")
    coord.create_run(store, "hold-example", "automated", "fixture", [
        {"org": "acme", "repo": "tool", "number": 1, "head_sha": "a" * 40}])
    card = store.cards["PR-001"]
    card.owner_hold = record
    store.upsert_card(card)
    store.header.authority = {"holds": [card.id] if legacy else [],
                              "hold_records": {card.id: {"source": "saved user hold"}}}
    store.set_header(store.header)
    store = Store.load(store.path, session="test")
    held, actual_source = proto.effective_owner_hold(store.header.authority,
                                                    store.cards[card.id])
    assert (held, actual_source) == (expected, source)
    task = proto.Tasking.from_store(
        store, {"attempt_id": "AGT-001.1", "repo_id": "acme/tool",
                "card_ids": [card.id]}, mode="automated", repairs=[],
        op_timeout_secs=30, progress_log="test.log", helper_path="helper.py")
    assert task.attempt_id == "AGT-001.1"
    assert task.holds == ([card.id] if expected else [])
    text = proto.render_brief(task)
    assert "{{" not in text
    for rel in ("scripts/sweep_patience.py", "scripts/sweep_protocol.py",
                "references/reporting.md", "references/dependency-evidence.md"):
        assert str(SCRIPTS.parent / rel) in text
    if expected:
        assert source in text


@pytest.fixture
def journal(tmp_path):
    path = tmp_path / "run.jsonl"
    store = Store(str(path), session="test")
    coord.create_run(store, "report-example", "inspect", "read-only example", [
        {"org": "acme", "repo": "tool", "number": 1,
         "url": "https://github.com/acme/tool/pull/1",
         "title": "Update test dependency", "head_sha": "a" * 40},
        {"org": "acme", "repo": "tool", "number": 2,
         "url": "https://github.com/acme/tool/pull/2",
         "title": "Update build action", "head_sha": "b" * 40},
    ])
    card = store.cards["PR-001"]
    card.transition_to(State.WAITING)
    card.reason_code = "K14"
    card.reason_line = "Validation passed; the review window exceeded the budget"
    card.action = "Finish the review in a new run and refresh merge checks"
    card.action_owner = "sweeper"
    card.resume_trigger = "new execution budget"
    store.upsert_card(card)
    other = store.cards["PR-002"]
    other.observe_merged("c" * 40, "2026-09-27T21:00:00Z")
    store.upsert_card(other)
    return path


def invoke(path, capsys, *args):
    code = cli.main(["--store", str(path), "--session", "test", *args])
    output = capsys.readouterr()
    return code, output.out, output.err


def test_saved_report_is_the_complete_inline_output(journal, tmp_path, capsys):
    output_path = tmp_path / "report.md"
    original = journal.read_bytes()
    code, out, err = invoke(journal, capsys, "run", "describe", "--save",
                            str(output_path))
    assert code == 0 and not err
    assert output_path.read_text() == out
    for expected in ("https://github.com/acme/tool/pull/1",
                     "https://github.com/acme/tool/pull/2",
                     "Finish the review in a new run", "Continuation: none"):
        assert expected in out
    assert journal.read_bytes() == original


def test_machine_report_contains_the_exact_saved_human_report(
        journal, tmp_path, capsys):
    path = tmp_path / "report.md"
    code, out, err = invoke(journal, capsys, "run", "describe", "--save",
                            str(path), "--json")
    assert code == 0 and not err
    result = json.loads(out)
    assert result["report"] == path.read_text()
    assert len(result["cards"]) == 2


@pytest.mark.parametrize("alias", ["same", "symlink", "hardlink"])
def test_report_cannot_overwrite_its_journal(journal, tmp_path, capsys, alias):
    target = journal
    if alias != "same":
        target = tmp_path / "alias.md"
        if alias == "symlink":
            target.symlink_to(journal)
        else:
            target.hardlink_to(journal)
    original = journal.read_bytes()
    code, out, err = invoke(journal, capsys, "run", "describe", "--save",
                            str(target), "--json")
    assert code == 1 and not out
    assert json.loads(err)["error"]["code"] == "invalid_input"
    assert journal.read_bytes() == original


def test_unwritable_report_destination_is_a_structured_failure(
        journal, tmp_path, capsys):
    original = journal.read_bytes()
    path = tmp_path / "absent" / "report.md"
    code, out, err = invoke(journal, capsys, "run", "describe", "--save",
                            str(path), "--json")
    assert code == 1 and not out
    assert json.loads(err)["error"]["code"] == "report_write_failed"
    assert journal.read_bytes() == original


def followup():
    return {
        "repo_id": "acme/tool", "key": "push-commitlint",
        "claim": "Push commit-message checks use the wrong bot policy",
        "action": "Select policy from originating commit and PR evidence",
        "action_owner": "sweeper", "status": "open",
        "attribution": "pre_existing",
        "attribution_note": "The same workflow rule was present on the base",
        "evidence": [{"id": "EV-main", "head": "b" * 40,
                      "what": "Read base workflow and push log",
                      "establishes": "Push and PR events select different policies"}],
    }


def test_followup_can_be_recorded_after_merge_and_keeps_pr_state(
        journal, tmp_path, capsys):
    fields = tmp_path / "followup.json"
    fields.write_text(json.dumps(followup()))
    before = Store.load(str(journal)).cards["PR-002"].to_dict()
    code, out, err = invoke(journal, capsys, "incident", "record", "--file",
                            str(fields), "--card", "PR-002", "--json")
    assert code == 0 and not err
    issue = json.loads(out)
    assert issue["status"] == "open" and issue["card_ids"] == ["PR-002"]
    assert not issue["external_links"]
    reloaded = Store.load(str(journal))
    card = reloaded.cards["PR-002"]
    assert card.state == State.MERGED
    assert card.head_sha == before["head_sha"]
    assert card.merge_commit == before["merge_commit"]
    assert issue["id"] in card.issue_ids
    code, report, err = invoke(journal, capsys, "run", "describe")
    assert code == 0 and not err
    assert followup()["claim"] in report
    assert followup()["action"] in report


def test_followup_resolution_is_durable_and_keeps_prior_evidence(
        journal, tmp_path, capsys):
    create = tmp_path / "create.json"
    create.write_text(json.dumps(followup()))
    code, out, _ = invoke(journal, capsys, "incident", "record", "--file",
                          str(create), "--card", "PR-002", "--json")
    assert code == 0
    identity = json.loads(out)["id"]
    update = tmp_path / "update.json"
    update.write_text(json.dumps({
        "status": "resolved", "evidence": [{"id": "EV-fixed",
            "what": "Reviewed passing push checks after the repair",
            "establishes": "Human, bot and mixed commit ranges pass"}],
    }))
    code, out, err = invoke(journal, capsys, "incident", "update", identity,
                            "--file", str(update), "--json")
    assert code == 0 and not err
    issue = json.loads(out)
    assert issue["status"] == "resolved"
    assert {item["id"] for item in issue["evidence"]} >= {"EV-main", "EV-fixed"}
    code, out, err = invoke(journal, capsys, "incident", "list", "--json")
    assert code == 0 and not err
    assert json.loads(out)[0]["status"] == "resolved"


def test_invalid_followup_does_not_partially_write(journal, tmp_path, capsys):
    fields = tmp_path / "bad.json"
    fields.write_text(json.dumps({**followup(), "evidence": []}))
    original = journal.read_bytes()
    code, out, err = invoke(journal, capsys, "incident", "record", "--file",
                            str(fields), "--card", "PR-002", "--json")
    assert code == 1 and not out
    assert json.loads(err)["error"]["code"] == "store_error"
    assert journal.read_bytes() == original


def test_missing_incident_is_not_found(journal, tmp_path, capsys):
    fields = tmp_path / "update.json"
    fields.write_text('{"status":"resolved"}')
    code, out, err = invoke(journal, capsys, "incident", "update", "ISS-999",
                            "--file", str(fields), "--json")
    assert code == 3 and not out
    assert json.loads(err)["error"]["code"] == "not_found"
