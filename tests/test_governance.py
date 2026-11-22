"""Governance core tests: event-sourced trust root + charter gate (synthetic keys and texts; no data)."""
import multiprocessing as _mp
import uuid

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from xauusd_swarm.charter import GateError, Governance, Rule
from xauusd_swarm.identity import AuthError, public_hex, sign
from xauusd_swarm.ledger import AnchorStore, Ledger, LedgerError

FK = Ed25519PrivateKey.generate()          # founder (synthetic, test only)
DK = Ed25519PrivateKey.generate()          # detector
XK = Ed25519PrivateKey.generate()          # stranger


def F(action, **kw):
    return sign("founder", FK, {"action": action, "nonce": uuid.uuid4().hex, **kw})


def chk(g, rule_id, *, key=DK, ident="det", conflict=False, **kw):
    r = g.rule(rule_id)
    return sign(ident, key, {"action": "charter_check", "nonce": uuid.uuid4().hex, "rule_id": rule_id,
                             "rule_version": r.version, "rule_sha256": r.sha256,
                             "charters": g.charter_state(), "conflict": conflict, **kw})


def setup(g):
    g.register_key(F("register_key", identity="det", public_key_hex=public_hex(DK.public_key())))
    g.set_initial_charter(F("charter_initial", charter="project", text="P1"))
    g.set_initial_charter(F("charter_initial", charter="claims", text="C1"))
    g.appoint_detector(F("appoint_detector", holder="det"))
    g.register_rule(Rule.make("R1", 1, "rule text", author="alice", executor="bob", layer=5))
    return g


def fl(tmp_path):
    (tmp_path / "anchors").mkdir(exist_ok=True)
    return Ledger(tmp_path / "gov.jsonl", anchors=AnchorStore(tmp_path / "anchors" / "a.jsonl"))


@pytest.fixture
def gate():
    return setup(Governance(FK.public_key(), Ledger()))


# ---------------- core behaviour ----------------

def test_unchecked_rule_does_not_execute(gate):
    with pytest.raises(GateError, match="unchecked"):
        gate.authorize_execution("R1", executor="bob")


def test_clear_rule_executes_and_is_logged(gate):
    gate.record_check(chk(gate, "R1"))
    gate.authorize_execution("R1", executor="bob")
    assert [e.kind for e in gate.ledger][-1] == "rule_executed"


def test_conflict_suspends_and_record_holds_required_fields(gate):
    gate.record_check(chk(gate, "R1", conflict=True, charter="claims", clause="§4.4", finding="scope"))
    with pytest.raises(GateError, match="suspended"):
        gate.authorize_execution("R1", executor="bob")
    p = [e for e in gate.ledger if e.kind == "charter_check"][-1].payload
    import json
    st = json.loads(bytes.fromhex(p["statement_hex"]))
    assert st["clause"] == "§4.4" and st["rule_version"] == 1 and len(st["rule_sha256"]) == 64
    assert set(st["charters"]) == {"project", "claims"} and p["timestamp"]


def test_identity_is_signature_not_string(gate):
    with pytest.raises(AuthError, match="invalid signature"):
        gate.appoint_detector(sign("founder", XK, {"action": "appoint_detector", "nonce": "n", "holder": "det"}))
    with pytest.raises(AuthError):
        gate.record_check(chk(gate, "R1", key=XK, ident="det"))


def test_replay_and_wrong_action_refused(gate):
    s = chk(gate, "R1"); gate.record_check(s)
    with pytest.raises(AuthError, match="replayed"):
        gate.record_check(s)
    with pytest.raises(AuthError, match="action"):
        gate.appoint_detector(F("charter_amend", charter="project", text="x", audit_ref="a"))


def test_slice_binding_survives_two_later_amendments(gate):
    gate.consume_slice("S1")
    gate.amend_charter(F("charter_amend", charter="claims", text="C2", audit_ref="A2"))
    gate.consume_slice("S2")
    gate.amend_charter(F("charter_amend", charter="claims", text="C3", audit_ref="A3"))
    assert [gate.charter_for_slice("claims", s).version for s in ("S1", "S2", "S3")] == [1, 2, 3]
    with pytest.raises(GateError, match="already consumed"):
        gate.consume_slice("S1")


def test_withdrawal_founder_signed_and_final_per_version(gate):
    gate.register_key(F("register_key", identity="x", public_key_hex=public_hex(XK.public_key())))
    with pytest.raises(AuthError):
        gate.withdraw(sign("x", XK, {"action": "withdraw_rule", "nonce": "w", "rule_id": "R1", "rule_version": 1}))
    gate.withdraw(F("withdraw_rule", rule_id="R1", rule_version=1))
    with pytest.raises(GateError, match="withdrawn"):
        gate.record_check(chk(gate, "R1"))
    gate.register_rule(Rule.make("R1", 2, "v2", author="alice", executor="bob", layer=5))
    gate.record_check(chk(gate, "R1")); gate.authorize_execution("R1", executor="bob")


def test_both_charters_and_current_versions_required():
    g = Governance(FK.public_key(), Ledger())
    g.register_key(F("register_key", identity="det", public_key_hex=public_hex(DK.public_key())))
    g.set_initial_charter(F("charter_initial", charter="project", text="P1"))
    g.appoint_detector(F("appoint_detector", holder="det"))
    g.register_rule(Rule.make("R1", 1, "t", author="a", executor="b", layer=5))
    with pytest.raises(GateError, match="both charters"):
        g.record_check(chk(g, "R1"))
    g.set_initial_charter(F("charter_initial", charter="claims", text="C1"))
    stale = chk(g, "R1")
    g.amend_charter(F("charter_amend", charter="project", text="P2", audit_ref="A"))
    with pytest.raises(GateError, match="BOTH charters"):
        g.record_check(stale)


def test_rule_hash_and_detector_independence(gate):
    with pytest.raises(GateError, match="hash"):
        gate.register_rule(Rule("R9", 1, "text", "a", "b", 5, "0" * 64))
    gate.register_rule(Rule.make("R2", 1, "t2", author="det", executor="bob", layer=6))
    with pytest.raises(GateError, match="does not author or execute"):
        gate.record_check(chk(gate, "R2"))


# ---------------- round-2 blocker 1: anchors must cover the ledger ----------------

def test_deleted_or_emptied_anchor_store_is_detected(tmp_path):
    g = setup(Governance(FK.public_key(), fl(tmp_path)))
    ap = tmp_path / "anchors" / "a.jsonl"
    saved = ap.read_bytes()
    ap.unlink()
    with pytest.raises(LedgerError, match="does not cover"):
        fl(tmp_path)
    ap.write_bytes(b"")
    with pytest.raises(LedgerError, match="does not cover"):
        fl(tmp_path)
    ap.write_bytes(b"\n".join(saved.split(b"\n")[:2]) + b"\n")         # anchors truncated
    with pytest.raises(LedgerError, match="does not cover"):
        fl(tmp_path)


def test_real_crash_between_entry_and_commit_is_recovered(tmp_path, monkeypatch):
    lg = fl(tmp_path)
    lg.append("x", {"n": 1})
    monkeypatch.setattr(lg, "_commit_anchor", lambda e: (_ for _ in ()).throw(KeyboardInterrupt("crash")))
    with pytest.raises(KeyboardInterrupt):
        lg.append("x", {"n": 2})                                     # entry 2 written, commit missing
    monkeypatch.undo()
    re = fl(tmp_path)                                                # accepted: matching INTENT exists
    assert len(re) == 2
    re.append("x", {"n": 3})                                         # completes commit 2, then 3
    recs = AnchorStore(tmp_path / "anchors" / "a.jsonl").read()
    assert [n for n, _ in recs] == [1, 2, 3]
    assert len(fl(tmp_path)) == 3


def test_crash_after_intent_before_entry_is_consistent(tmp_path, monkeypatch):
    lg = fl(tmp_path)
    lg.append("x", {"n": 1})
    import os as _os
    real = _os.write
    def boom(fd, data):
        if b'"kind":"x"' in data:
            raise KeyboardInterrupt("crash before entry write")
        return real(fd, data)
    monkeypatch.setattr(_os, "write", boom)
    with pytest.raises(KeyboardInterrupt):
        lg.append("x", {"n": 2})
    monkeypatch.undo()
    re = fl(tmp_path); assert len(re) == 1                           # dangling intent ignored
    re.append("x", {"n": 2}); assert len(fl(tmp_path)) == 2


def test_single_entry_ledger_with_deleted_anchor_store_is_refused(tmp_path):
    lg = fl(tmp_path); lg.append("x", {"n": 1})
    (tmp_path / "anchors" / "a.jsonl").unlink()
    with pytest.raises(LedgerError, match="no matching declared intent"):
        fl(tmp_path)


def test_single_entry_ledger_with_emptied_anchor_store_is_refused(tmp_path):
    lg = fl(tmp_path); lg.append("x", {"n": 1})
    (tmp_path / "anchors" / "a.jsonl").write_bytes(b"")
    with pytest.raises(LedgerError, match="no matching declared intent"):
        fl(tmp_path)


def test_unanchored_entry_not_matching_intent_is_refused(tmp_path, monkeypatch):
    lg = fl(tmp_path); lg.append("x", {"n": 1})
    monkeypatch.setattr(lg, "_commit_anchor", lambda e: (_ for _ in ()).throw(KeyboardInterrupt()))
    with pytest.raises(KeyboardInterrupt):
        lg.append("x", {"n": 2})
    monkeypatch.undo()
    f = tmp_path / "gov.jsonl"
    lines = f.read_bytes().split(b"\n")
    other = Ledger(); other.append("x", {"n": 1}); forged = other.append("x", {"n": 999})
    import json as _j
    lines[1] = _j.dumps(forged.as_record(), sort_keys=True, separators=(",", ":")).encode()
    lines[0] = _j.dumps(list(other)[0].as_record(), sort_keys=True, separators=(",", ":")).encode()
    f.write_bytes(b"\n".join(lines))
    with pytest.raises(LedgerError):
        fl(tmp_path)


# ---------------- round-2 blocker 2: state rebuilt from the ledger on restart ----------------

def test_full_state_is_rebuilt_after_restart(tmp_path):
    g = setup(Governance(FK.public_key(), fl(tmp_path)))
    g.record_check(chk(g, "R1", conflict=True, charter="project", clause="§3"))
    g.register_rule(Rule.make("R2", 1, "two", author="a", executor="b", layer=7))
    g.record_check(chk(g, "R2"))
    g.consume_slice("S1")
    g.amend_charter(F("charter_amend", charter="claims", text="C2", audit_ref="A"))
    g.register_rule(Rule.make("R3", 1, "three", author="a", executor="b", layer=8))
    g.withdraw(F("withdraw_rule", rule_id="R3", rule_version=1))
    del g
    h = Governance(FK.public_key(), fl(tmp_path))                     # restart
    assert h.keys()["det"] == public_hex(DK.public_key())
    assert h.current("claims").version == 2 and h.charter_for_slice("claims", "S1").version == 1
    assert (h.status("R1"), h.status("R2"), h.status("R3")) == ("suspended", "clear", "withdrawn")
    with pytest.raises(GateError, match="re-check"):                  # claims amended after R2's check
        h.authorize_execution("R2", executor="b")
    h.record_check(chk(h, "R2")); h.authorize_execution("R2", executor="b")


def test_replay_refused_after_restart(tmp_path):
    g = setup(Governance(FK.public_key(), fl(tmp_path)))
    s = chk(g, "R1"); g.record_check(s)
    h = Governance(FK.public_key(), fl(tmp_path))
    with pytest.raises(AuthError, match="replayed"):
        h.record_check(s)


def test_invalid_history_is_refused_on_restart(tmp_path):
    g = setup(Governance(FK.public_key(), fl(tmp_path)))
    g.ledger.append("rule_executed", {"rule_id": "R1", "executor": "bob"})   # written around the API, unchecked
    with pytest.raises(GateError, match="invalid history"):
        Governance(FK.public_key(), fl(tmp_path))


def test_second_process_sees_first_process_events(tmp_path):
    a = setup(Governance(FK.public_key(), fl(tmp_path)))
    b = Governance(FK.public_key(), fl(tmp_path))
    a.record_check(chk(a, "R1"))
    b.authorize_execution("R1", executor="bob")                        # b catches up under the lock
    s = chk(a, "R1")
    a.record_check(s)
    with pytest.raises(AuthError, match="replayed"):
        b.record_check(s)


# ---------------- round-2 blocker 3: key rebuild applies all registration rules ----------------

def _forge(tmp_path, payload):
    g = Governance(FK.public_key(), fl(tmp_path))
    g.ledger.append("key_registered", payload)                         # around the API
    with pytest.raises(GateError, match="invalid history"):
        Governance(FK.public_key(), fl(tmp_path))


def test_rebuild_refuses_founder_signed_statement_with_other_action(tmp_path):
    s = F("appoint_detector", identity="evil", public_key_hex=public_hex(XK.public_key()))
    _forge(tmp_path, {**s.to_payload(), "identity": "evil"})


def test_rebuild_refuses_event_identity_not_matching_statement(tmp_path):
    s = F("register_key", identity="det", public_key_hex=public_hex(DK.public_key()))
    _forge(tmp_path, {**s.to_payload(), "identity": "someone_else"})


def test_rebuild_refuses_duplicate_identity_registration(tmp_path):
    g = Governance(FK.public_key(), fl(tmp_path))
    g.register_key(F("register_key", identity="det", public_key_hex=public_hex(DK.public_key())))
    s = F("register_key", identity="det", public_key_hex=public_hex(XK.public_key()))
    g.ledger.append("key_registered", {**s.to_payload(), "identity": "det"})
    with pytest.raises(GateError, match="invalid history"):
        Governance(FK.public_key(), fl(tmp_path))


def test_rebuild_refuses_forged_signature(tmp_path):
    s = sign("founder", XK, {"action": "register_key", "nonce": "z", "identity": "evil",
                              "public_key_hex": public_hex(XK.public_key())})
    _forge(tmp_path, {**s.to_payload(), "identity": "evil"})


# ---------------- round-2 blocker 4: no in-memory change without a durable write ----------------

def _boom(*a, **k):
    raise LedgerError("injected write failure")


@pytest.mark.parametrize("op", ["withdraw", "register", "amend", "consume", "check", "appoint"])
def test_failed_write_leaves_memory_equal_to_ledger(gate, monkeypatch, op):
    before = (dict(gate._s.status), {c: len(v) for c, v in gate._s.charters.items()},
              dict(gate._s.slices), set(gate._s.rules), gate._s.detector, len(gate.ledger))
    monkeypatch.setattr(gate.ledger, "_append_mem", _boom)
    act = {
        "withdraw": lambda: gate.withdraw(F("withdraw_rule", rule_id="R1", rule_version=1)),
        "register": lambda: gate.register_rule(Rule.make("R5", 1, "t", author="a", executor="b", layer=5)),
        "amend": lambda: gate.amend_charter(F("charter_amend", charter="project", text="P2", audit_ref="A")),
        "consume": lambda: gate.consume_slice("S9"),
        "check": lambda: gate.record_check(chk(gate, "R1")),
        "appoint": lambda: gate.appoint_detector(F("appoint_detector", holder="det")),
    }[op]
    with pytest.raises(LedgerError, match="injected"):
        act()
    after = (dict(gate._s.status), {c: len(v) for c, v in gate._s.charters.items()},
             dict(gate._s.slices), set(gate._s.rules), gate._s.detector, len(gate.ledger))
    assert after == before


def test_failed_file_write_then_restart_matches(tmp_path, monkeypatch):
    g = setup(Governance(FK.public_key(), fl(tmp_path)))
    monkeypatch.setattr(g.ledger, "_write", _boom)
    with pytest.raises(LedgerError):
        g.withdraw(F("withdraw_rule", rule_id="R1", rule_version=1))
    assert g.status("R1") == "unchecked"
    assert Governance(FK.public_key(), fl(tmp_path)).status("R1") == "unchecked"


# ---------------- concurrency: one nonce accepted once across processes ----------------

def _race(tmp, founder_pub_hex, stmt_hex, sig_hex, q):
    # spawned child: module-level keys are regenerated there, so the founder key is passed in
    from pathlib import Path
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    from xauusd_swarm.identity import Signed
    fpk = Ed25519PublicKey.from_public_bytes(bytes.fromhex(founder_pub_hex))
    g = Governance(fpk, fl(Path(tmp)))
    try:
        g.register_key(Signed("founder", bytes.fromhex(stmt_hex), bytes.fromhex(sig_hex)))
        q.put("ok")
    except (AuthError, GateError):
        q.put("refused")


def test_concurrent_same_statement_accepted_once(tmp_path):
    fl(tmp_path)
    s = F("register_key", identity="det", public_key_hex=public_hex(DK.public_key()))
    mp = _mp.get_context("spawn")                     # clean children, no inherited test state
    q = mp.Queue()
    ps = [mp.Process(target=_race, args=(str(tmp_path), public_hex(FK.public_key()), s.statement.hex(), s.signature.hex(), q))
          for _ in range(6)]
    for p in ps: p.start()
    res = sorted(q.get(timeout=60) for _ in ps)        # drain the queue BEFORE join (avoids feeder deadlock)
    for p in ps: p.join(timeout=60)
    assert res.count("ok") == 1 and res.count("refused") == 5
    Governance(FK.public_key(), fl(tmp_path))                          # history still valid
