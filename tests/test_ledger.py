"""Ledger unit tests (synthetic records only)."""
import json
import multiprocessing as mp

import pytest


def L(tmp_path, **kw):
    (tmp_path / "anchors").mkdir(exist_ok=True)
    return Ledger(tmp_path / "l.jsonl", anchors=AnchorStore(tmp_path / "anchors" / "a.jsonl"), **kw)

from xauusd_swarm.ledger import GENESIS, AnchorStore, Ledger, LedgerError


def test_chain_and_verify():
    lg = Ledger()
    a = lg.append("x", {"n": 1}); b = lg.append("x", {"n": 2})
    assert a.prev == GENESIS and b.prev == a.digest and lg.head == b.digest
    lg.verify()


def test_no_update_or_delete_api():
    lg = Ledger()
    assert not any(hasattr(lg, m) for m in ("update", "delete", "remove", "pop", "__setitem__", "__delitem__"))


def test_entries_are_immutable_and_reads_are_copies():
    lg = Ledger(); p = {"n": [1]}
    e = lg.append("x", p); p["n"].append(2)               # caller's dict does not reach the ledger
    got = e.payload; got["n"].append(3)                    # a read copy does not reach the ledger
    assert e.payload == {"n": [1]} and list(lg)[0].payload == {"n": [1]}
    with pytest.raises(Exception):
        e.kind = "y"                                       # frozen entry
    lg.verify()


@pytest.mark.parametrize("tamper", ["edit", "delete", "reorder"])
def test_file_tampering_is_detected(tmp_path, tamper):
    f = tmp_path / "l.jsonl"
    lg = L(tmp_path)
    for i in range(3):
        lg.append("x", {"n": i})
    lines = f.read_text().splitlines()
    if tamper == "edit":
        d = json.loads(lines[1]); d["payload"]["n"] = 99; lines[1] = json.dumps(d)
    elif tamper == "delete":
        del lines[1]
    else:
        lines[0], lines[1] = lines[1], lines[0]
    f.write_text("\n".join(lines) + "\n")
    with pytest.raises(LedgerError):
        L(tmp_path)


def test_full_rewrite_is_detected_automatically_on_load(tmp_path):
    f = tmp_path / "l.jsonl"
    lg = L(tmp_path)
    for i in range(3):
        lg.append("x", {"n": i})
    # attacker rebuilds a consistent chain in the ledger file (anchor store untouched)
    forged = Ledger()
    for i in range(3):
        forged.append("x", {"n": i * 10})
    f.write_bytes(b"".join(__import__("json").dumps(e.as_record(), sort_keys=True, separators=(",", ":")).encode() + b"\n" for e in forged))
    with pytest.raises(LedgerError, match="anchor"):
        L(tmp_path)                                        # no anchor argument: checked on load


def test_truncation_is_detected_automatically(tmp_path):
    f = tmp_path / "l.jsonl"
    lg = L(tmp_path)
    for i in range(3):
        lg.append("x", {"n": i})
    f.write_text("\n".join(f.read_text().splitlines()[:2]) + "\n")
    with pytest.raises(LedgerError, match="anchor"):
        L(tmp_path)


def test_deleted_ledger_file_is_detected(tmp_path):
    lg = L(tmp_path); lg.append("x", {"n": 1})
    (tmp_path / "l.jsonl").unlink()
    with pytest.raises(LedgerError, match="removed"):
        L(tmp_path)


def test_file_ledger_requires_anchor_store_outside_its_folder(tmp_path):
    with pytest.raises(LedgerError, match="requires an AnchorStore"):
        Ledger(tmp_path / "l.jsonl")
    with pytest.raises(LedgerError, match="outside"):
        Ledger(tmp_path / "l.jsonl", anchors=AnchorStore(tmp_path / "a.jsonl"))


def test_partial_trailing_entry_fails_by_default_and_recovers_explicitly(tmp_path):
    f = tmp_path / "l.jsonl"
    lg = L(tmp_path); lg.append("x", {"n": 1}); lg.append("x", {"n": 2})
    good = f.read_bytes()
    with open(f, "ab") as fh:
        fh.write(b'{"seq":2,"kind":"x","pay')               # unfinished last write
    with pytest.raises(LedgerError, match="partial"):
        L(tmp_path)
    rec = L(tmp_path, recover=True)
    assert len(rec) == 2 and f.read_bytes() == good
    assert (tmp_path / "l.jsonl.partial-1").read_bytes() == b'{"seq":2,"kind":"x","pay'
    rec.append("x", {"n": 3}); L(tmp_path).verify()


def test_internal_corruption_is_never_auto_recovered_and_later_entries_kept(tmp_path):
    f = tmp_path / "l.jsonl"
    lg = L(tmp_path)
    for i in range(4):
        lg.append("x", {"n": i})
    lines = f.read_bytes().split(b"\n")
    lines[1] = b'{"broken'                                  # corrupted line in the MIDDLE
    f.write_bytes(b"\n".join(lines))
    before = f.read_bytes()
    for rec in (False, True):
        with pytest.raises(LedgerError, match="INSIDE"):
            L(tmp_path, recover=rec)
    assert f.read_bytes() == before                         # nothing cut; later valid entries intact
    assert not list(tmp_path.glob("l.jsonl.partial-*"))


def test_two_writers_on_one_file_keep_a_valid_chain(tmp_path):
    a, b = L(tmp_path), L(tmp_path)
    a.append("x", {"w": "a1"}); b.append("x", {"w": "b1"}); a.append("x", {"w": "a2"})
    final = L(tmp_path)
    final.verify()
    assert [e.payload["w"] for e in final] == ["a1", "b1", "a2"]


def test_unique_append_refuses_duplicate_across_instances(tmp_path):
    from xauusd_swarm.ledger import DuplicateError
    L(tmp_path).append("nonce_used", {"nonce": "n1"}, unique_key="nonce")
    with pytest.raises(DuplicateError):
        L(tmp_path).append("nonce_used", {"nonce": "n1"}, unique_key="nonce")


def test_unfinished_anchor_write_is_quarantined_not_fatal(tmp_path):
    lg = L(tmp_path); lg.append("x", {"n": 1})
    ap = tmp_path / "anchors" / "a.jsonl"
    with open(ap, "ab") as fh:
        fh.write(b'{"n":2,"he')
    lg2 = L(tmp_path); lg2.append("x", {"n": 2})
    assert len(AnchorStore(ap).read()) == 2 and (tmp_path / "anchors" / "a.jsonl.partial-1").exists()


def _worker(path, tag, n):
    from pathlib import Path
    lg = L(Path(path))
    for i in range(n):
        lg.append("x", {"w": f"{tag}{i}"})


def test_concurrent_processes_keep_a_valid_chain(tmp_path):
    ctx = mp.get_context("spawn")
    ps = [ctx.Process(target=_worker, args=(str(tmp_path), t, 20)) for t in "abcd"]
    for p in ps: p.start()
    for p in ps: p.join(timeout=120)
    assert all(p.exitcode == 0 for p in ps)
    final = L(tmp_path); final.verify()
    assert len(final) == 80 and len(AnchorStore(tmp_path / "anchors" / "a.jsonl").read()) == 80


def test_held_lock_is_not_overridden(tmp_path):
    f = tmp_path / "l.jsonl"
    (tmp_path / "l.jsonl.lock").write_text("held")
    import xauusd_swarm.ledger as LM
    lk = LM._FileLock(tmp_path / "l.jsonl.lock", timeout=0.05)
    with pytest.raises(LedgerError, match="locked"):
        with lk:
            pass
    assert (tmp_path / "l.jsonl.lock").read_text() == "held"


def test_crash_after_first_intent_before_first_entry_is_consistent(tmp_path):
    (tmp_path / "anchors").mkdir()
    AnchorStore(tmp_path / "anchors" / "a.jsonl").record_intent(1, "f" * 64)   # crash: entry 1 never written
    lg = L(tmp_path)
    assert len(lg) == 0
    lg.append("x", {"n": 1})
    assert len(L(tmp_path)) == 1


def test_load_waits_for_a_writer_holding_the_lock(tmp_path):
    lg = L(tmp_path); lg.append("x", {"n": 1})
    lock = tmp_path / "l.jsonl.lock"
    lock.write_text("held")
    import xauusd_swarm.ledger as LM
    real = LM._FileLock.__init__
    def short(self, path, timeout=10.0):
        real(self, path, timeout=0.05)
    LM._FileLock.__init__ = short
    try:
        with pytest.raises(LedgerError, match="locked"):
            L(tmp_path)                                    # does not read a possibly half-done state
    finally:
        LM._FileLock.__init__ = real
    lock.unlink()
    assert len(L(tmp_path)) == 1


def test_empty_ledger_is_truthy(tmp_path):
    assert bool(L(tmp_path)) is True and bool(Ledger()) is True


def test_lock_retries_on_windows_delete_pending(tmp_path, monkeypatch):
    """Windows returns access-denied for O_EXCL on a lock file being deleted; the lock must retry."""
    import xauusd_swarm.ledger as LM
    calls = {"n": 0}
    real_open = LM.os.open

    def flaky(path, flags, *a):
        calls["n"] += 1
        if calls["n"] <= 2:
            raise PermissionError(13, "Permission denied (delete pending)")
        return real_open(path, flags, *a)

    monkeypatch.setattr(LM.os, "name", "nt")
    monkeypatch.setattr(LM.os, "open", flaky)
    with LM._FileLock(tmp_path / "x.lock"):
        assert (tmp_path / "x.lock").exists()
    assert calls["n"] == 3 and not (tmp_path / "x.lock").exists()


def test_lock_permission_error_is_real_on_posix(tmp_path, monkeypatch):
    import xauusd_swarm.ledger as LM

    def denied(path, flags, *a):
        raise PermissionError(13, "Permission denied")

    monkeypatch.setattr(LM.os, "name", "posix")
    monkeypatch.setattr(LM.os, "open", denied)
    with pytest.raises(PermissionError):
        with LM._FileLock(tmp_path / "x.lock"):
            pass
