"""Regression boundaries from PR 87's producer, deadline and approval review."""

import json
import subprocess
import sys
import time
from dataclasses import asdict, replace
from pathlib import Path

import pytest

SCRIPTS = (Path(__file__).resolve().parents[1]
           / "plugins/repo-hygiene/skills/dependabot-sweep/scripts")
sys.path.insert(0, str(SCRIPTS))

import sweep_cli as cli  # noqa: E402
import sweep_coordinator as coord  # noqa: E402
import sweep_evaluator as ev  # noqa: E402
import sweep_observe as observe  # noqa: E402
import sweep_patience as patience  # noqa: E402
import sweep_protocol as proto  # noqa: E402
import sweep_report as report  # noqa: E402
from sweep_core import State, Store  # noqa: E402
from test_sweep_slice2 import receipt as dependency_receipt_fixture  # noqa: E402

OLD_HEAD = "a" * 40
HEAD = "b" * 40
BASE = "d" * 40
CI_APP = 15368


def section(data):
    return {"status": 200, "data": data, "truncated": False, "error": ""}


def observation(head=HEAD):
    return ev.Observation(
        head_sha=head, observed_at="2026-09-27T08:00:00Z",
        pull=section({"number": 1, "state": "open", "merged": False, "draft": False,
                      "head": {"sha": head}, "base": {"ref": "main", "sha": BASE,
                                                        "repo": {"full_name": "acme/r"}},
                      "mergeable": True, "mergeable_state": "clean"}),
        files=section([{"filename": "uv.lock", "sha": "c" * 40,
                        "status": "modified", "changes": 2}]),
        reviews=section([]), threads=section([]),
        check_runs=section({"total_count": 1, "check_runs": [
            {"id": 1, "name": "ci/test", "status": "completed",
             "conclusion": "success", "head_sha": head, "app": {"id": CI_APP}}]}),
        check_suites=section({}),
        statuses=section({"statuses": [], "total_count": 0, "sha": head}),
        queue=section({}), policy=ev.EffectivePolicy())


def classifier_receipt(obs):
    """The reviewed lock-only update retains its manifest and install consumer.

    The independent install/version assertion is the shared fixture's local
    validation. The required-producer regression varies only GitHub's check
    versus status transport; the receipt never supplies an app-bound waiver.
    """
    receipt = dependency_receipt_fixture(head=obs.head_sha)
    receipt.dependency_evidence["files"][1]["blob_sha"] = "c" * 40
    receipt.dependency_evidence["updates"][0]["files"] = ["uv.lock"]
    receipt.check_evidence["checks"] = receipt.check_evidence["checks"][:1]
    if not obs.check_runs["data"]["check_runs"]:
        receipt.check_evidence["checks"][0].update(
            producer_id=None,
            proof={"kind": "status", "head_sha": obs.head_sha,
                   "creator": "unattributed-bot", "target_url": "https://ci.example/runs/1",
                   "evidence": "fixture: current successful commit status and creator"})
    return replace(receipt, base_sha=BASE,
                   files_digest=ev.files_digest(obs.files["data"]), file_count=1,
                   classifier="boundary-regression", at=obs.observed_at)


def receipt_path(tmp_path, observed):
    path = tmp_path / "classifier-receipt.json"
    path.write_text(json.dumps(asdict(classifier_receipt(observed))))
    return str(path)


def evaluate(obs, mode="automated"):
    return ev.evaluate(obs, classifier_receipt(obs), ev.Authority(mode=mode),
                       ev.Tracking(lease_held=True), now=1_800_000_000)


@pytest.mark.parametrize("producer,run_app,expected", [
    (15368, None, State.WAITING),
    (None, None, State.READY),
    (15368, 15368, State.READY),
    (15368, 999, State.WAITING),
])
def test_required_producer_cannot_be_satisfied_by_commit_status(
        producer, run_app, expected):
    obs = observation()
    obs.policy.required_checks = [ev.RequiredCheck("ci/test", producer)]
    obs.statuses = section({"sha": HEAD, "total_count": 1, "statuses": [
        {"context": "ci/test", "state": "success",
         "creator": {"login": "unattributed-bot"}, "target_url": "https://ci.example/runs/1"}]})
    obs.check_runs = section({"total_count": 0, "check_runs": []})
    if run_app is not None:
        obs.check_runs = section({"total_count": 1, "check_runs": [
            {"id": 1, "name": "ci/test", "status": "completed",
             "conclusion": "success", "head_sha": HEAD,
             "app": {"id": run_app}}]})
    result = evaluate(obs)
    assert result.state == expected
    if expected == State.WAITING:
        assert result.reason_code == "K01"
        assert result.merge_path == "none"


@pytest.mark.parametrize("env,offered,expected", [
    ({"GH_MERGE_DEADLINE_EPOCH": "1200"}, 2000, "1200"),
    ({"SWEEP_DEADLINE_EPOCH": "1800", "GH_MERGE_DEADLINE_EPOCH": "1200"},
     2000, "1200"),
    ({"SWEEP_DEADLINE_EPOCH": "900", "GH_MERGE_DEADLINE_EPOCH": "1200"},
     2000, "900"),
    ({"GH_MERGE_DEADLINE_EPOCH": "1200"}, 1100, "1100"),
    ({"GH_MERGE_DEADLINE_EPOCH": "1200"}, 0, "1200"),
])
def test_delegation_preserves_earliest_deadline_from_either_name(
        env, offered, expected):
    parent = {**env, "UNCHANGED": "value"}
    child = patience.delegate_env(parent, offered)
    assert child["SWEEP_DEADLINE_EPOCH"] == expected
    assert child["GH_MERGE_DEADLINE_EPOCH"] == expected
    assert child["UNCHANGED"] == "value"
    assert parent == {**env, "UNCHANGED": "value"}


def discovery(number=1, head=OLD_HEAD):
    return {"org": "acme", "repo": "r", "number": number,
            "title": "bump dependency", "head_sha": head}


def needs_owner(store, card):
    card.state = State.NEEDS_OWNER
    card.reason_code = "K16"
    card.reason_line = "owner approval required"
    card.severity = "low"
    card.decision = {"why": "gated mode", "approve_effect": "merge",
                     "decline_effect": "hold", "recommendation": "APPROVE"}
    store.upsert_card(card)


def test_linked_replacement_appears_in_human_and_json_approval(
        tmp_path, capsys):
    store = Store(str(tmp_path / "run.jsonl"), session="boundary")
    coord.create_run(store, "boundary", "gated", "fixture", [discovery()])
    replacement = coord.register_replacement(store, "PR-001", discovery(2, HEAD))
    needs_owner(store, replacement)
    late = coord.register_arrival(store, discovery(3, HEAD))
    needs_owner(store, late)

    human = report.render_approval(store)
    assert replacement.human_id in human
    assert HEAD in human
    assert late.human_id not in human
    code = cli.main(["--store", store.path, "approval", "list", "-o", "json"])
    captured = capsys.readouterr()
    assert code == 0, captured.err
    rows = json.loads(captured.out)
    assert [row["id"] for row in rows] == [replacement.id]
    assert rows[0]["head_sha"] == HEAD


@pytest.mark.parametrize("kind,expected", [
    ("ready", State.READY),
    ("needs_owner", State.NEEDS_OWNER),
    ("waiting", State.WAITING),
])
def test_valid_identity_outcomes_carry_the_evaluated_head(kind, expected):
    obs = observation()
    if kind == "waiting":
        obs.statuses = section({"sha": HEAD, "total_count": 1, "statuses": [
            {"context": "ci/test", "state": "pending"}]})
    result = evaluate(obs, "gated" if kind == "needs_owner" else "automated")
    assert result.state == expected
    assert result.to_outcome("PR-001")["head_sha"] == HEAD


def test_failed_identity_does_not_transfer_an_unverified_head():
    obs = observation()
    obs.pull["data"]["head"]["sha"] = OLD_HEAD
    result = evaluate(obs, "gated")
    assert result.state == State.BLOCKED
    assert result.reason_code == "K13"
    assert "head_sha" not in result.to_outcome("PR-001")


@pytest.mark.parametrize("saved_head,record,approved,expected", [
    (HEAD, None, True, "READY"),
    (OLD_HEAD, None, True, "NEEDS_OWNER"),
    ("", {"head_sha": HEAD}, True, "READY"),
    (OLD_HEAD, {"head_sha": HEAD}, True, "READY"),
    (HEAD, {"head_sha": OLD_HEAD}, True, "NEEDS_OWNER"),
    (HEAD, {}, True, "NEEDS_OWNER"),
    (HEAD, {"head_sha": HEAD}, False, "NEEDS_OWNER"),
])
def test_cli_approval_is_bound_to_explicit_or_legacy_saved_head(
        tmp_path, capsys, saved_head, record, approved, expected):
    store = Store(str(tmp_path / "run.jsonl"), session="boundary")
    coord.create_run(store, "boundary", "gated", "fixture",
                     [discovery(head=saved_head)])
    store.header.authority = {"mode": "gated", "repairs": [],
                              "approved": ["PR-001"] if approved else []}
    if record is not None:
        store.header.authority["approval_records"] = {"PR-001": record}
    store.set_header(store.header)
    attempt = coord.schedule(store)[0]["attempt_id"]
    input_path = tmp_path / "observation.json"
    observed = observation()
    input_path.write_text(json.dumps(observe.observation_to_dict(observed)))
    classified = receipt_path(tmp_path, observed)
    before = Path(store.path).read_bytes()
    code = cli.main(["--store", store.path, "--session", "boundary", "pr",
                     "evaluate", "PR-001", "--file", str(input_path),
                     "--attempt", attempt, "--receipt", classified, "-o", "json"])
    captured = capsys.readouterr()
    assert code == 0, captured.err
    result = json.loads(captured.out)
    assert result["evaluation"]["state"] == expected
    assert result["outcome"]["head_sha"] == HEAD
    assert Path(store.path).read_bytes() == before


def test_cli_creation_failure_does_not_publish_scope_without_run_deadline(
        tmp_path, capsys, monkeypatch):
    store_path = tmp_path / "run.jsonl"
    input_path = tmp_path / "discoveries.json"
    input_path.write_text(json.dumps([discovery()]))
    config_path = tmp_path / "config.toml"
    config_path.write_text('[defaults]\nmode = "gated"\nrepairs = []\n'
                           '[org."acme"]\n[budgets]\nrun_budget_secs = 900\n')

    def fail_clock(store, budget):
        raise ValueError("injected deadline publication failure")

    monkeypatch.setattr(coord, "start_run_clock", fail_clock)
    code = cli.main(["--store", str(store_path), "--config", str(config_path),
                     "run", "create", "--run-id", "boundary",
                     "--file", str(input_path), "-o", "json"])
    captured = capsys.readouterr()
    assert code == 1
    assert "injected deadline publication failure" in captured.err
    assert not store_path.exists()


def test_cli_foreign_attempt_requires_stopped_confirmation_and_rejects_live_overlap(
        tmp_path, capsys):
    store = Store(str(tmp_path / "run.jsonl"), session="worker-session")
    coord.create_run(store, "boundary", "automated", "fixture", [discovery()])
    store.header.authority = {"mode": "automated", "repairs": [],
                              "stale_after_secs": 1}
    store.set_header(store.header)
    attempt_id = coord.schedule(store)[0]["attempt_id"]
    attempt = store.diary[attempt_id]
    attempt.last_progress_at = "2000-01-01T00:00:00Z"
    store.record_attempt(attempt)
    input_path = tmp_path / "observations.json"
    input_path.write_text(json.dumps({"PR-001": {"merged": False}}))
    args = ["--store", store.path, "--session", "recovery-session",
            "run", "reconcile", "--file", str(input_path), "-o", "json"]

    code = cli.main(args)
    captured = capsys.readouterr()
    assert code == 0, captured.err
    assert json.loads(captured.out)["crashed"] == []
    loaded = Store.load(store.path)
    assert not loaded.diary[attempt_id].result
    assert loaded.leases.get("acme/r").state == "held"

    before = Path(store.path).read_bytes()
    code = cli.main([*args, "--live", attempt_id, "--stopped", attempt_id])
    captured = capsys.readouterr()
    assert code == 1
    assert "live and confirmed stopped" in captured.err
    assert Path(store.path).read_bytes() == before

    code = cli.main([*args, "--stopped", attempt_id])
    captured = capsys.readouterr()
    assert code == 0, captured.err
    assert json.loads(captured.out)["crashed"] == [attempt_id]
    loaded = Store.load(store.path)
    assert loaded.diary[attempt_id].result == "crashed"
    assert loaded.leases.get("acme/r").state == "released"


def cli_json(args, capsys):
    code = cli.main(args)
    captured = capsys.readouterr()
    assert code == 0, captured.err
    return json.loads(captured.out)


@pytest.mark.parametrize("saved_head", [OLD_HEAD, ""])
def test_exact_approval_blocks_old_head_transport_then_survives_new_head_collection(
        tmp_path, capsys, saved_head):
    marker = tmp_path / "transport-called"
    live_head = tmp_path / "live-head"
    live_head.write_text(OLD_HEAD)
    helper = tmp_path / "fake_helper.py"
    helper.write_text(
        "from pathlib import Path\n"
        "class DefinitiveFailure(Exception): pass\n"
        f"def preflight(*a, **kw): return (Path({str(live_head)!r}).read_text(), {{}})\n"
        "def main(argv):\n"
        "    try: head, _ = preflight()\n"
        "    except DefinitiveFailure: return 10\n"
        f"    Path({str(marker)!r}).write_text(head)\n"
        "    return 0\n")
    store = Store(str(tmp_path / "run.jsonl"), session="boundary")
    coord.create_run(store, "binding", "gated", "fixture",
                     [discovery(head=saved_head)])
    with store.transaction():
        store.header.authority = {
            "mode": "gated", "repairs": [], "op_timeout_secs": 30,
            "approved": ["PR-001"], "helper_path": str(helper),
            "approval_records": {"PR-001": {"head_sha": HEAD}}}
        store.set_header(store.header)
    attempt = coord.schedule(store, pr_budget_secs=600)[0]["attempt_id"]
    args = ["--store", store.path, "--session", "boundary"]
    tasking = proto.Tasking.from_dict(cli_json(
        [*args, "brief", "view", attempt, "-o", "json"], capsys))
    allowed, _ = proto.authorize(tasking, "merge", "PR-001", time.time())
    try:
        argv, _ = proto.helper_command(tasking, "PR-001")
    except ValueError:
        command_refused = True
    else:
        command_refused = False
        subprocess.run([sys.executable, *argv[1:]], check=False, timeout=5,
                       capture_output=True, text=True)
    assert {"authorized": allowed, "command_refused": command_refused,
            "transport_called": marker.exists()} == {
                "authorized": False, "command_refused": True,
                "transport_called": False}

    input_path = tmp_path / "new-observation.json"
    observed = observation()
    input_path.write_text(json.dumps(observe.observation_to_dict(observed)))
    classified = receipt_path(tmp_path, observed)
    result = cli_json([*args, "pr", "evaluate", "PR-001", "--attempt", attempt,
                       "--file", str(input_path), "--receipt", classified,
                       "-o", "json"], capsys)
    assert result["evaluation"]["state"] == "READY"
    coord.apply_outcome(store, attempt, [result["outcome"]])
    assert store.cards["PR-001"].head_sha == HEAD
    assert store.header.authority["approved"] == ["PR-001"]
    assert store.header.authority["approval_records"]["PR-001"]["head_sha"] == HEAD
    successor = coord.schedule(store)[0]["attempt_id"]
    tasking = proto.Tasking.from_dict(cli_json(
        [*args, "brief", "view", successor, "-o", "json"], capsys))
    assert tasking.approval_heads == {"PR-001": HEAD}
    assert proto.authorize(tasking, "merge", "PR-001", time.time())[0]
    argv, _ = proto.helper_command(tasking, "PR-001")
    live_head.write_text(HEAD)
    result = subprocess.run([sys.executable, *argv[1:]], capture_output=True,
                            text=True, timeout=5, check=False)
    assert result.returncode == 0, result.stdout + result.stderr
    assert marker.read_text() == HEAD


def legacy_tasking(head=OLD_HEAD):
    return proto.Tasking.from_dict({
        "attempt_id": "AGT-001.1", "repo_id": "acme/r", "mode": "gated",
        "card_ids": ["PR-001"], "merge_allowed": True, "approved": ["PR-001"],
        "cards": [{"id": "PR-001", "org": "acme", "repo": "r", "number": 1,
                   "state": "READY", "head_sha": head, "deadline_epoch": 0}]})


def test_legacy_tasking_approval_binds_once_to_unchanged_valid_card_head():
    tasking = legacy_tasking()
    assert proto.authorize(tasking, "merge", "PR-001", time.time())[0]
    assert OLD_HEAD in proto.helper_command(tasking, "PR-001")[0]
    tasking.cards[0]["head_sha"] = HEAD
    assert not proto.authorize(tasking, "merge", "PR-001", time.time())[0]
    with pytest.raises(ValueError, match="approved"):
        proto.helper_command(tasking, "PR-001")


@pytest.mark.parametrize("head", ["", "short"])
def test_legacy_tasking_without_valid_approved_head_cannot_authorize(head):
    tasking = legacy_tasking(head)
    assert not proto.authorize(tasking, "merge", "PR-001", time.time())[0]
    with pytest.raises(ValueError, match="approved"):
        proto.helper_command(tasking, "PR-001")
