"""Crash recovery and serialization for the sweep's append-only store."""

import json
import os
import subprocess
import sys
import textwrap
import threading
from pathlib import Path

import pytest

SCRIPTS = (Path(__file__).resolve().parents[1] /
           "plugins/repo-hygiene/skills/dependabot-sweep/scripts")
sys.path.insert(0, str(SCRIPTS))

from sweep_core import Card, RunHeader, State, Store, StoreError  # noqa: E402


def card(identifier="PR-001"):
    return Card(identifier, "acme", "repo", 1, "url", "bump", "acme")


def seeded(tmp_path):
    store = Store(str(tmp_path / "run.jsonl"), session="owner")
    store.set_header(RunHeader("RUN-1", "gated", scope_ids=["PR-001"]))
    store.upsert_card(card())
    return store


def child_script(source, *args):
    return [sys.executable, "-c",
            "import sys\nsys.path.insert(0, " + repr(str(SCRIPTS)) + ")\n" +
            textwrap.dedent(source), *map(str, args)]


def test_partial_final_legacy_record_keeps_preceding_state(tmp_path):
    store = seeded(tmp_path)
    before = Path(store.path).read_bytes()
    tail = b'{"kind":"card","id":"PR-001","state":"MER'
    with open(store.path, "ab") as handle:
        handle.write(tail)
    with pytest.warns(RuntimeWarning, match="trailing"):
        restored = Store.load(store.path)
    assert restored.cards["PR-001"].state == State.NEW
    assert restored.header.scope_ids == ["PR-001"]
    assert Path(store.path).read_bytes() == before + tail  # read-only replay
    with pytest.warns(RuntimeWarning, match="trailing"):
        with restored.transaction():
            restored.header.stop_reason = "recovered"
            restored.set_header(restored.header)
    quarantines = list(tmp_path.glob("run.jsonl.torn-*.jsonl"))
    assert len(quarantines) == 1 and quarantines[0].read_bytes() == tail
    assert Store.load(store.path).header.stop_reason == "recovered"


def test_tail_recovery_without_events_keeps_snapshot_current(tmp_path):
    store = seeded(tmp_path)
    with open(store.path, "ab") as handle:
        handle.write(b'{"kind":"transaction"')
    with pytest.warns(RuntimeWarning, match="trailing"):
        with store.transaction():
            pass
    store.header.stop_reason = "after recovery"
    store.set_header(store.header)
    assert Store.load(store.path).header.stop_reason == "after recovery"


@pytest.mark.parametrize("suffix", [b'garbage\n', b'garbage\n{}\n'])
def test_malformed_committed_or_middle_record_is_never_skipped(tmp_path, suffix):
    store = seeded(tmp_path)
    with open(store.path, "ab") as handle:
        handle.write(suffix)
    with pytest.raises(StoreError, match="record"):
        Store.load(store.path)


def test_legacy_records_without_last_newline_can_accept_new_transaction(tmp_path):
    path = tmp_path / "run.jsonl"
    path.write_text(json.dumps({"kind": "run_header", "run_id": "RUN-old",
                                "mode": "inspect"}), encoding="utf-8")
    store = Store.load(str(path))
    with store.transaction():
        store.upsert_card(card())
    restored = Store.load(str(path))
    assert restored.header.run_id == "RUN-old"
    assert restored.ids.next("PR") == "PR-002"


def test_transaction_commits_all_events_as_one_replay_unit(tmp_path):
    store = Store(str(tmp_path / "run.jsonl"))
    with store.transaction():
        store.set_header(RunHeader("RUN-1", "gated"))
        created = card(store.ids.next("PR"))
        store.upsert_card(created)
        store.header.scope_ids.append(created.id)
        store.set_header(store.header)
        store.record_ids()
        assert not Path(store.path).exists()
    lines = Path(store.path).read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0])["kind"] == "transaction"
    restored = Store.load(store.path)
    assert restored.header.scope_ids == list(restored.cards) == ["PR-001"]
    assert restored.ids.next("PR") == "PR-002"


def test_exception_rolls_back_memory_and_preserves_existing_objects(tmp_path):
    store = seeded(tmp_path)
    original_header = store.header
    original_card = store.cards["PR-001"]
    before = Path(store.path).read_bytes()
    with pytest.raises(RuntimeError, match="interrupted"):
        with store.transaction():
            original_header.scope_ids.append("PR-002")
            original_card.state = State.BLOCKED
            store.set_header(original_header)
            store.upsert_card(original_card)
            raise RuntimeError("interrupted")
    assert store.header is original_header
    assert store.cards["PR-001"] is original_card
    assert original_header.scope_ids == ["PR-001"]
    assert original_card.state == State.NEW
    assert Path(store.path).read_bytes() == before


def test_nested_exception_makes_outer_transaction_rollback_only(tmp_path):
    store = Store(str(tmp_path / "run.jsonl"))
    with pytest.raises(StoreError, match="aborted"):
        with store.transaction():
            store.set_header(RunHeader("RUN-1", "gated"))
            try:
                with store.transaction():
                    store.upsert_card(card())
                    raise ValueError("nested failure")
            except ValueError:
                pass
    assert store.header is None and store.cards == {}
    assert not Path(store.path).exists()


def test_stale_snapshot_refreshes_before_allocating_ids(tmp_path):
    current = seeded(tmp_path)
    stale = Store.load(current.path)
    with current.transaction():
        current.upsert_card(card(current.ids.next("PR")))
        current.record_ids()
    old_header = stale.header
    with stale.transaction():
        assert stale.header is old_header
        assert set(stale.cards) == {"PR-001", "PR-002"}
        stale.upsert_card(card(stale.ids.next("PR")))
        stale.record_ids()
    assert set(Store.load(current.path).cards) == {"PR-001", "PR-002", "PR-003"}


def test_standalone_stale_write_is_refused_and_refreshes_memory(tmp_path):
    current = seeded(tmp_path)
    stale = Store.load(current.path)
    current.header.authority = {"approved": ["PR-001"]}
    current.set_header(current.header)
    before = Path(current.path).read_bytes()
    stale.header.authority = {"approved": []}
    with pytest.raises(StoreError, match="stale"):
        stale.set_header(stale.header)
    assert stale.header.authority == {"approved": ["PR-001"]}
    assert Path(current.path).read_bytes() == before


@pytest.mark.parametrize("persisted", [False, True])
@pytest.mark.parametrize("rollback", [False, True])
def test_standalone_thread_write_waits_for_other_transaction(tmp_path, persisted, rollback):
    store = seeded(tmp_path) if persisted else Store()
    started, returned = threading.Event(), threading.Event()
    errors = []

    def write_independently():
        started.set()
        try:
            store.upsert_card(card("PR-003"))
        except BaseException as exc:
            errors.append(exc)
        finally:
            returned.set()

    writer = threading.Thread(target=write_independently)
    try:
        with store.transaction():
            store.upsert_card(card("PR-002"))
            writer.start()
            assert started.wait(1)
            returned_while_open = returned.wait(0.1)
            visible_while_open = "PR-003" in store.cards
            if rollback:
                raise RuntimeError("rollback only this transaction")
    except RuntimeError as exc:
        assert rollback and str(exc) == "rollback only this transaction"
    finally:
        writer.join(timeout=2)
    assert not writer.is_alive() and returned.is_set()
    assert errors == []
    assert not returned_while_open, "another thread acknowledged an uncommitted write"
    assert not visible_while_open, "another thread modified the open transaction"
    assert "PR-003" in store.cards
    assert ("PR-002" in store.cards) is not rollback
    if persisted:
        restored = Store.load(store.path)
        assert "PR-003" in restored.cards
        assert ("PR-002" in restored.cards) is not rollback


def test_foreign_thread_does_not_borrow_repository_transaction_protocol(tmp_path):
    store = seeded(tmp_path)
    results = {}

    def claim_independently():
        results["claimed"] = store.locks.claim("acme/other", "AGT-foreign")
        try:
            store.locks.recover_orphans()
        except StoreError as exc:
            results["recovery_error"] = str(exc)

    with store.transaction():
        claimant = threading.Thread(target=claim_independently)
        claimant.start()
        claimant.join(timeout=2)
        assert not claimant.is_alive()
        payload = Path(store.locks._path("acme/other")).read_text(encoding="utf-8")
    assert results.get("claimed") is True
    assert "transaction" in results.get("recovery_error", "")
    assert payload == f"{store.locks.token} AGT-foreign"
    with store.transaction():
        assert store.locks.holder("acme/other") == "AGT-foreign"


def test_process_exit_before_commit_writes_no_events_and_releases_store_lock(tmp_path):
    store = seeded(tmp_path)
    before = Path(store.path).read_bytes()
    result = subprocess.run(child_script("""
        import os
        from sweep_core import Store
        store = Store.load(sys.argv[1])
        with store.transaction():
            store.header.scope_ids = []
            store.set_header(store.header)
            os._exit(71)
    """, store.path), capture_output=True, text=True, timeout=10)
    assert result.returncode == 71, result.stderr
    assert Path(store.path).read_bytes() == before
    with store.transaction(timeout=0.3):
        assert store.header.scope_ids == ["PR-001"]


def test_process_exit_during_append_discards_entire_torn_transaction(tmp_path):
    store = seeded(tmp_path)
    result = subprocess.run(child_script("""
        import os
        from sweep_core import Store
        store = Store.load(sys.argv[1])
        original_write = os.write
        def tear(fd, data):
            original_write(fd, data[:len(data) // 2])
            os.fsync(fd)
            os._exit(72)
        os.write = tear
        with store.transaction():
            store.header.scope_ids = []
            store.set_header(store.header)
            store.cards["PR-001"].reason_line = "uncommitted"
            store.upsert_card(store.cards["PR-001"])
    """, store.path), capture_output=True, text=True, timeout=10)
    assert result.returncode == 72, result.stderr
    with pytest.warns(RuntimeWarning, match="trailing"):
        restored = Store.load(store.path)
    assert restored.header.scope_ids == ["PR-001"]
    assert restored.cards["PR-001"].reason_line == ""


def test_store_lock_wait_is_bounded_and_cross_process(tmp_path):
    store = seeded(tmp_path)
    with store.transaction():
        result = subprocess.run(child_script("""
            from sweep_core import Store, StoreError
            store = Store.load(sys.argv[1])
            try:
                with store.transaction(timeout=0.1):
                    pass
            except StoreError as exc:
                assert "lock" in str(exc)
                sys.exit(73)
            sys.exit(1)
        """, store.path), capture_output=True, text=True, timeout=5)
    assert result.returncode == 73, result.stderr


def test_marked_claim_survives_process_crash_only_when_durably_leased(tmp_path):
    store = seeded(tmp_path)
    result = subprocess.run(child_script("""
        import os
        from sweep_core import Store
        store = Store.load(sys.argv[1])
        with store.transaction():
            assert store.locks.claim("acme/repo", "AGT-001.1")
            os._exit(74)
    """, store.path), capture_output=True, text=True, timeout=10)
    assert result.returncode == 74, result.stderr
    with store.transaction():
        assert store.locks.holder("acme/repo") == ""
        assert store.locks.claim("acme/repo", "AGT-001.1")
        store.record_lease(store.leases.acquire("acme/repo", "AGT-001.1", ["PR-001"]))
    foreign = Store.load(store.path, session="other")
    with foreign.transaction():
        assert foreign.locks.holder("acme/repo") == "AGT-001.1"
        assert not foreign.locks.claim("acme/repo", "AGT-002.1")


def test_legacy_or_unknown_repository_lock_is_not_reclaimed(tmp_path):
    store = seeded(tmp_path)
    assert store.locks.claim("acme/repo", "AGT-legacy")  # outside transaction
    with store.transaction():
        assert store.locks.holder("acme/repo") == "AGT-legacy"
        assert not store.locks.claim("acme/repo", "AGT-001.1")


def test_parallel_processes_allocate_distinct_ids_from_stale_snapshots(tmp_path):
    store = seeded(tmp_path)
    program = """
        from pathlib import Path
        import time
        from sweep_core import Store, Card
        store = Store.load(sys.argv[1])
        Path(sys.argv[2]).write_text("loaded")
        deadline = time.monotonic() + 5
        while not Path(sys.argv[3]).exists():
            assert time.monotonic() < deadline
            time.sleep(0.01)
        with store.transaction():
            identifier = store.ids.next("PR")
            store.upsert_card(Card(identifier, "acme", "repo", 2, "u", "bump", "a"))
            store.record_ids()
        print(identifier)
    """
    ready1, ready2 = tmp_path / "ready1", tmp_path / "ready2"
    first = subprocess.Popen(child_script(program, store.path, ready1, ready2),
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    second = subprocess.Popen(child_script(program, store.path, ready2, ready1),
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    outputs = []
    try:
        for process in (first, second):
            out, err = process.communicate(timeout=10)
            assert process.returncode == 0, err
            outputs.append(out.strip())
    finally:
        for process in (first, second):
            if process.poll() is None:
                process.kill()
                process.wait()
    assert set(outputs) == {"PR-002", "PR-003"}
    assert set(Store.load(store.path).cards) == {"PR-001", "PR-002", "PR-003"}
