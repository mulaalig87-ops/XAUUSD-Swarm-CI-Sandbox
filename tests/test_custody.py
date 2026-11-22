"""Layer 3 tests: custody, blinding records, access log, gates. Synthetic values only; no data."""
import hashlib
import json
import math
import os
import uuid

import pytest
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from xauusd_swarm import representations as R
from xauusd_swarm.charter import GateError, Governance
from xauusd_swarm.claims import ClaimsCharter
from xauusd_swarm.custody import (LEAK_SCOPE, CustodyLayer, Vault, attest, load_key, request, zero_prior_state,
                                  _sha, _now)
from xauusd_swarm.identity import AuthError, public_hex, sign
from xauusd_swarm.ledger import AnchorStore, Ledger

FK, CK, AK, OK, DK, QK, GK = (Ed25519PrivateKey.generate() for _ in range(7))
IDS = (("cust", CK), ("aud", AK), ("op", OK), ("disc", DK), ("chk", QK), ("gz", GK))


def F(action, **kw):
    return sign("founder", FK, {"action": action, "nonce": uuid.uuid4().hex, **kw})


def C(action, **kw):
    return sign("cust", CK, {"action": action, "nonce": uuid.uuid4().hex, **kw})


def build(ledger=None, vault=None):
    v = vault if vault is not None else Vault()
    cl = CustodyLayer(v, identity="cust", key=CK); cc = ClaimsCharter()
    g = Governance(FK.public_key(), ledger if ledger is not None else Ledger(), extensions=[cc, cl])
    for ident, k in IDS:
        g.register_key(F("register_key", identity=ident, public_key_hex=public_hex(k.public_key())))
    for role, h in (("custody", "cust"), ("custody_auditor", "aud"), ("court_operator", "op"),
                    ("discovery_participant", "disc"), ("reid_checker", "chk"), ("gz_operator", "gz")):
        cl.commit("role_assigned", F("assign_role", role=role, holder=h))
    g.set_initial_charter(F("charter_initial", charter="project", text="P"))
    g.set_initial_charter(F("charter_initial", charter="claims", text="C"))
    return g, cl, cc, v


def fix_family(cl, v, fam="F1", delta=0.01):
    com = v.set_params(fam, c=1.5, a=2.0, b=-3.0, m=7.0)
    cl.commit("params_fixed", C("params_fixed", family=fam, params_commitment=com, delta=delta))
    return com


def card(cid="K1"):
    return {"claim_id": cid, "version": 1, "tags": ["الموقع"], "category": None, "path": "أ",
            "uses_events": False, "scope_type": "stable", "scope": "s", "rulings": {"existence": "e", "size_with_uncertainty": "s", "importance": "i"}}


def seal(cl, fam):
    cl.commit("submissions_sealed", sign("op", OK, {"action": "seal_submissions", "nonce": uuid.uuid4().hex,
                                                   "family": fam, "submissions_sha256": "a" * 64}))


@pytest.fixture
def env():
    return build()


# ---------------- representations ----------------

def test_representations_on_synthetic_prices():
    p = [100.0, 101.0, 100.5, 102.0]
    assert R.log_returns(p)[0] == pytest.approx(math.log(1.01))
    assert R.tick_grid(p, c=100.0, delta=0.5) == [0.0, 2.0, 1.0, 4.0]
    assert R.level_residual(p, m=3.0)[0] == pytest.approx(1.0)
    assert R.affine_level(p, a=2.0, b=1.0)[0] == 201.0
    assert R.activity_time(3) == [0, 1, 2]
    assert R.volatility_time(p)[0] == 0.0 and R.volatility_time(p)[-1] > 0


@pytest.mark.parametrize("call", [lambda: R.affine_level([1, 2], a=0, b=1), lambda: R.tick_grid([1, 2], c=0, delta=0),
                                  lambda: R.level_residual([1, 2], m=0), lambda: R.log_returns([1]),
                                  lambda: R.log_returns([1, -2]), lambda: R.log_returns([1, 2], scale=0)])
def test_representation_guards(call):
    with pytest.raises(R.ReprError):
        call()


def test_every_representation_function_has_a_card():
    funcs = {"log_returns", "tick_grid", "level_residual", "affine_level", "activity_time", "volatility_time"}
    assert funcs == set(R.CARDS)
    for c in R.CARDS.values():
        assert c.transform and c.preserves and c.loses and c.reid_result == R.REID_NOT_RUN


# ---------------- roles ----------------

def test_role_separation(env):
    g, cl, cc, v = env
    with pytest.raises(GateError, match="separation"):
        cl.commit("role_assigned", F("assign_role", role="court_operator", holder="aud"))
    with pytest.raises(GateError, match="separation"):
        cl.commit("role_assigned", F("assign_role", role="discovery_participant", holder="gz"))
    with pytest.raises(GateError, match="independent"):
        cl.commit("role_assigned", F("assign_role", role="custody_auditor", holder="chk"))
    with pytest.raises(AuthError):
        cl.commit("role_assigned", C("assign_role", role="custody", holder="disc"))


# ---------------- custody decision before opening (pre_validate, F-1) ----------------

def test_claim_opening_requires_prior_custody_decision(env):
    g, cl, cc, v = env
    g.consume_slice("S1")
    cc.register(F("register_claim", card=card()))
    with pytest.raises(GateError, match="BEFORE opening"):
        cc.open_on_slice("K1", "S1")
    com = fix_family(cl, v)
    cl.commit("custody_decision", C("custody_decision", slice="S1", family="F1", boundaries="b", delta=0.01, params_commitment=com))
    cc.open_on_slice("K1", "S1")


def test_pre_validate_does_not_bypass_original_validation(env):
    g, cl, cc, v = env
    com = fix_family(cl, v)
    cl.commit("custody_decision", C("custody_decision", slice="S9", family="F1", boundaries="b", delta=0.01, params_commitment=com))
    cc.register(F("register_claim", card=card()))
    with pytest.raises(GateError):          # pre_validate passes, the claims validator still refuses (slice not consumed)
        cc.open_on_slice("K1", "S9")


def test_params_fixed_across_family_slices(env):
    g, cl, cc, v = env
    com = fix_family(cl, v)
    with pytest.raises(GateError, match="fixed across"):
        cl.commit("custody_decision", C("custody_decision", slice="S1", family="F1", boundaries="b", delta=0.02, params_commitment=com))
    with pytest.raises(GateError, match="already fixed"):
        fix_family(cl, v)


def test_params_commitment_must_be_in_vault_and_delta_positive(env):
    g, cl, cc, v = env
    with pytest.raises(GateError, match="vault holds no"):
        cl.commit("params_fixed", C("params_fixed", family="F1", params_commitment="d" * 64, delta=0.01))
    com = v.set_params("F1", c=1, a=1, b=0, m=2)
    for bad in (0, -1, True, "1"):
        with pytest.raises(GateError, match="Δ"):
            cl.commit("params_fixed", C("params_fixed", family="F1", params_commitment=com, delta=bad))


def test_only_custody_records_decisions(env):
    g, cl, cc, v = env
    com = fix_family(cl, v)
    s = sign("aud", AK, {"action": "custody_decision", "nonce": "x", "slice": "S1", "family": "F1",
                         "boundaries": "b", "delta": 0.01, "params_commitment": com})
    with pytest.raises(GateError, match="does not hold the role"):
        cl.commit("custody_decision", s)


def test_secrets_never_in_ledger(env):
    g, cl, cc, v = env
    fix_family(cl, v)
    v.add_symbol("SYM-1", "REAL-SECRET-1")
    cl.access(request("gz", GK, "symbol:SYM-1", "test"))
    blob = json.dumps([e.as_record() for e in g.ledger])
    assert "REAL-SECRET-1" not in blob
    for k in ("1.5", "-3.0", "7.0"):
        assert f'"c": {k}' not in blob and f'"m": {k}' not in blob and f'"b": {k}' not in blob
    for raw in [bytes.fromhex(e.payload.get("statement_hex", "")) for e in g.ledger]:
        assert b"salt" not in raw and b"REAL-SECRET" not in raw


# ---------------- rotation (F-3, R1-5) ----------------

def test_rotation_needs_prior_founder_epoch_and_no_open_claims(env):
    g, cl, cc, v = env
    com = fix_family(cl, v)
    new = v.set_params("F1", c=9.0, a=3.0, b=1.0, m=5.0)
    with pytest.raises(GateError, match="epoch boundary"):
        cl.commit("params_rotated", C("params_rotated", family="F1", epoch="E2", params_commitment=new, delta=0.01))
    cl.commit("epoch_boundary_declared", F("declare_epoch_boundary", epoch="E2"))
    g.consume_slice("S1"); cc.register(F("register_claim", card=card()))
    cl.commit("custody_decision", C("custody_decision", slice="S1", family="F1", boundaries="b", delta=0.01, params_commitment=com))
    cc.open_on_slice("K1", "S1")
    with pytest.raises(GateError, match="claims are open"):
        cl.commit("params_rotated", C("params_rotated", family="F1", epoch="E2", params_commitment=new, delta=0.01))


def test_rotation_checks_vault_delta_and_change(env):
    g, cl, cc, v = env
    com = fix_family(cl, v)
    cl.commit("epoch_boundary_declared", F("declare_epoch_boundary", epoch="E2"))
    with pytest.raises(GateError, match="vault holds no"):
        cl.commit("params_rotated", C("params_rotated", family="F1", epoch="E2", params_commitment="e" * 64, delta=0.01))
    with pytest.raises(GateError, match="must change"):
        cl.commit("params_rotated", C("params_rotated", family="F1", epoch="E2", params_commitment=com, delta=0.01))
    new = v.set_params("F1", c=9.0, a=3.0, b=1.0, m=5.0)
    with pytest.raises(GateError, match="Δ"):
        cl.commit("params_rotated", C("params_rotated", family="F1", epoch="E2", params_commitment=new, delta=0))
    cl.commit("params_rotated", C("params_rotated", family="F1", epoch="E2", params_commitment=new, delta=0.02))
    assert cl.families["F1"]["epoch"] == "E2" and cl.families["F1"]["history"] == [com, new]
    assert v.params("F1", new)["a"] == 3.0 and v.params("F1", com)["a"] == 2.0     # history kept


# ---------------- authenticated access (R1-1 / S-1) ----------------

def test_gz_decryption_requires_signed_request_from_gz_operator(env):
    g, cl, cc, v = env
    v.add_symbol("SYM-1", "REAL-1")
    assert cl.access(request("gz", GK, "symbol:SYM-1", "G-Z identification")) == "REAL-1"
    last = cl.access_log[-1]
    assert last["outcome"] == "ok" and last["track"] == "G-Z" and last["requester"] == "gz"
    assert last["authenticated"] is True and last["returned"] == "sha256:" + _sha("REAL-1")
    assert "REAL-1" not in json.dumps(last)
    with pytest.raises(GateError, match="refused and logged"):
        cl.access(request("disc", DK, "symbol:SYM-1", "Z participant tries"))
    assert cl.access_log[-1]["outcome"] == "refused" and cl.access_log[-1]["track"] == "none"


def test_forged_or_replayed_request_refused_and_logged(env):
    g, cl, cc, v = env
    v.add_symbol("SYM-1", "REAL-1")
    forged = sign("gz", DK, {"action": "access_request", "item": "symbol:SYM-1", "reason": "x", "time": _now(), "nonce": "n1"})
    with pytest.raises(GateError, match="not authenticated"):
        cl.access(forged)
    assert cl.access_log[-1]["authenticated"] is False and cl.access_log[-1]["outcome"] == "refused"
    rq = request("gz", GK, "symbol:SYM-1", "once")
    cl.access(rq)
    with pytest.raises(GateError, match="not authenticated"):
        cl.access(rq)                                      # replay


def test_custody_cannot_log_an_unjustified_ok(env):
    g, cl, cc, v = env
    rq = request("disc", DK, "symbol:SYM-1", "x").to_payload()
    rec = {"action": "access_log", "executor": "cust", "request": rq, "request_sha256": _sha(rq), "time": _now(),
           "requester": "disc", "item": "symbol:SYM-1", "track": "G-Z", "reason": "x", "authenticated": True,
           "outcome": "ok", "returned": "sha256:" + "0" * 64}
    with pytest.raises(GateError, match="not justified"):
        cl.commit("access_logged", C(**rec))


@pytest.mark.parametrize("drop", ["track", "time", "requester", "executor", "item", "reason", "outcome", "returned"])
def test_access_record_fields_mandatory(env, drop):
    g, cl, cc, v = env
    rq = request("gz", GK, "symbol:S", "x").to_payload()
    rec = {"action": "access_log", "executor": "cust", "request": rq, "request_sha256": _sha(rq), "time": _now(),
           "requester": "gz", "item": "symbol:S", "track": "none", "reason": "x", "authenticated": True,
           "outcome": "refused", "returned": "none"}
    rec.pop(drop)
    with pytest.raises(GateError, match="missing"):
        cl.commit("access_logged", C(**rec))


@pytest.mark.parametrize("field,val", [("track", "Z"), ("time", "yesterday"), ("time", "2026-01-01T00:00:00"),
                                       ("outcome", "maybe"), ("returned", "REAL-1"), ("executor", "aud")])
def test_access_record_values_validated(env, field, val):
    g, cl, cc, v = env
    rq = request("gz", GK, "symbol:S", "x").to_payload()
    rec = {"action": "access_log", "executor": "cust", "request": rq, "request_sha256": _sha(rq), "time": _now(),
           "requester": "gz", "item": "symbol:S", "track": "none", "reason": "x", "authenticated": True,
           "outcome": "refused", "returned": "none", field: val}
    with pytest.raises(GateError):
        cl.commit("access_logged", C(**rec))


def test_hidden_truth_only_to_operator_after_seal(env):
    g, cl, cc, v = env
    v.store_truth("F1", {"planted": "law"})
    with pytest.raises(GateError):
        cl.access(request("op", OK, "truth:F1", "before seal"))
    seal(cl, "F1")
    with pytest.raises(GateError):
        cl.access(request("disc", DK, "truth:F1", "not operator"))
    with pytest.raises(GateError):
        cl.access(request("gz", GK, "truth:F1", "gz is not operator"))
    assert cl.access(request("op", OK, "truth:F1", "court")) == {"planted": "law"}
    assert [a["outcome"] for a in cl.access_log] == ["refused", "refused", "refused", "ok"]
    assert cl.access_log[-1]["track"] == "after_seal"


def test_only_court_operator_seals(env):
    g, cl, cc, v = env
    with pytest.raises(GateError, match="does not hold the role"):
        cl.commit("submissions_sealed", C("seal_submissions", family="F1", submissions_sha256="c" * 64))


# ---------------- Z outputs and G-Z ----------------

def test_z_output_leaves_only_after_full_custody_review(env):
    g, cl, cc, v = env
    out = b"synthetic report"
    with pytest.raises(GateError, match="does not leave Z"):
        cl.export_from_z(out)
    with pytest.raises(GateError, match="full scope"):
        cl.commit("z_output_passed", C("z_output_passed", output_sha256=hashlib.sha256(out).hexdigest(),
                                       reviewed=["text_reports"], passed=True))
    cl.commit("z_output_passed", C("z_output_passed", output_sha256=hashlib.sha256(out).hexdigest(),
                                   reviewed=list(LEAK_SCOPE), passed=True))
    assert cl.export_from_z(out) == out


def test_gz_release_to_language_minds_is_locked():
    with pytest.raises(GateError, match="LOCKED"):
        CustodyLayer.release_gz_to_language_minds(b"bundle")


def test_zero_prior_state_never_computational_while_threshold_open():
    assert zero_prior_state(llm_in_lineage=False, unauthorized_decryption=False, reid_failed=False,
                            reid_within_announced_threshold=None).startswith("undetermined")
    assert zero_prior_state(llm_in_lineage=True, unauthorized_decryption=False, reid_failed=False,
                            reid_within_announced_threshold=None).startswith("Z with linguistic")
    assert zero_prior_state(llm_in_lineage=True, unauthorized_decryption=True, reid_failed=False,
                            reid_within_announced_threshold=None) == "Z with blinding breach"


# ---------------- persistence and vault integrity (R1-2, R1-3) ----------------

def _fl(tmp_path):
    return Ledger(tmp_path / "led" / "gov.jsonl", anchors=AnchorStore(tmp_path / "anc" / "x.jsonl"))


def test_vault_persists_encrypted_and_commitments_verify_after_restart(tmp_path):
    for d in ("led", "anc", "vault"):
        (tmp_path / d).mkdir()
    key = os.urandom(32); vp = tmp_path / "vault" / "vault.bin"
    g, cl, cc, v = build(_fl(tmp_path), Vault(vp, key))
    com = fix_family(cl, v)
    cl.commit("custody_decision", C("custody_decision", slice="S1", family="F1", boundaries="b", delta=0.01, params_commitment=com))
    v.add_symbol("SYM", "REAL-X"); v.store_truth("F1", {"t": 1})
    cl.access(request("gz", GK, "symbol:SYM", "x"))
    raw = vp.read_bytes()
    assert b"REAL-X" not in raw and b"salt" not in raw            # encrypted at rest
    v2 = Vault(vp, key)
    cl2 = CustodyLayer(v2, identity="cust", key=CK)
    Governance(FK.public_key(), _fl(tmp_path), extensions=[ClaimsCharter(), cl2])
    assert cl2.roles["cust"] == {"custody"} and "S1" in cl2.decisions and cl2.access_log[-1]["outcome"] == "ok"
    res = cl2.verify_vault()
    assert res["result"] == "ok" and len(res["commitments"]) == 1
    assert not cl2.commitments_attested()
    cl2.commit("vault_attested", attest(cl2, "aud", AK, res["check_id"], vp))
    assert cl2.commitments_attested()
    assert cl2.access(request("gz", GK, "symbol:SYM", "after restart")) == "REAL-X"
    with pytest.raises(GateError, match="not authenticated"):          # request nonces survive restart
        cl2.access(cl2_replay := sign("gz", GK, json.loads(bytes.fromhex(cl.access_log[-1]["request"]["statement_hex"]))))


def test_wrong_key_or_tampered_vault_refused(tmp_path):
    vp = tmp_path / "v.bin"; key = os.urandom(32)
    Vault(vp, key).add_symbol("A", "B")
    with pytest.raises(GateError, match="cannot be decrypted"):
        Vault(vp, os.urandom(32))
    b = bytearray(vp.read_bytes()); b[-1] ^= 1; vp.write_bytes(bytes(b))
    with pytest.raises(GateError, match="cannot be decrypted"):
        Vault(vp, key)
    with pytest.raises(GateError, match="32-byte"):
        Vault(tmp_path / "w.bin", b"short")


def test_restart_with_wrong_vault_is_refused(tmp_path):
    for d in ("led", "anc"):
        (tmp_path / d).mkdir()
    g, cl, cc, v = build(_fl(tmp_path))
    fix_family(cl, v)
    with pytest.raises(GateError, match="vault holds no"):
        Governance(FK.public_key(), _fl(tmp_path), extensions=[ClaimsCharter(), CustodyLayer(Vault())])


def test_observer_mode_rebuilds_without_vault(tmp_path):
    for d in ("led", "anc"):
        (tmp_path / d).mkdir()
    g, cl, cc, v = build(_fl(tmp_path))
    fix_family(cl, v)
    obs = CustodyLayer(None)
    Governance(FK.public_key(), _fl(tmp_path), extensions=[ClaimsCharter(), obs])
    assert "F1" in obs.families
    with pytest.raises(GateError, match="observer"):
        obs.access(request("gz", GK, "symbol:X", "x"))


def test_vault_check_detects_mismatch(env):
    g, cl, cc, v = env
    com = fix_family(cl, v)
    v._d["params"]["F1"][com]["c"] = 999.0                     # simulated corruption
    with pytest.raises(GateError, match="integrity check failed"):
        cl.verify_vault()
    assert list(cl.vault_checks.values())[-1]["result"] == "failed" and not cl.commitments_attested()


def test_vault_must_be_outside_ledger_folder(tmp_path):
    (tmp_path / "led").mkdir(); (tmp_path / "anc").mkdir()
    with pytest.raises(GateError, match="outside the ledger folder"):
        build(_fl(tmp_path), Vault(tmp_path / "led" / "vault.bin", os.urandom(32)))


# ---------------- D-3 two-signature attestation, R2-2, R2-3 ----------------

def _setup_vault(tmp_path):
    for d in ("led", "anc", "vault"):
        (tmp_path / d).mkdir(exist_ok=True)
    vp = tmp_path / "vault" / "vault.bin"
    g, cl, cc, v = build(_fl(tmp_path), Vault(vp, os.urandom(32)))
    fix_family(cl, v)
    return g, cl, v, vp


def test_attestation_requires_auditor_and_matching_ciphertext(tmp_path):
    g, cl, v, vp = _setup_vault(tmp_path)
    res = cl.verify_vault()
    with pytest.raises(GateError, match="does not hold the role"):
        cl.commit("vault_attested", attest(cl, "cust", CK, res["check_id"], vp))       # custody cannot self-attest
    v.add_symbol("NEW", "x")                                                          # ciphertext changes
    a = attest(cl, "aud", AK, res["check_id"], vp)
    assert json.loads(bytes.fromhex(a.to_payload()["statement_hex"]))["verdict"] == "dissent"
    cl.commit("vault_attested", a)
    assert not cl.commitments_attested()
    with pytest.raises(GateError, match="already attested"):
        cl.commit("vault_attested", attest(cl, "aud", AK, res["check_id"], vp))


def test_forged_concurrence_refused(tmp_path):
    g, cl, v, vp = _setup_vault(tmp_path)
    res = cl.verify_vault()
    st = {"action": "vault_attested", "check_id": res["check_id"], "observed_ciphertext_sha256": "f" * 64,
          "custody_statement_sha256": "0" * 64, "verdict": "concur", "reason": "", "nonce": uuid.uuid4().hex}
    with pytest.raises(GateError, match="concurrence must match"):
        cl.commit("vault_attested", sign("aud", AK, st))
    with pytest.raises(GateError, match="recorded vault check"):
        cl.commit("vault_attested", sign("aud", AK, {**st, "check_id": "nope"}))


def test_attestation_stale_after_rotation(tmp_path):
    g, cl, v, vp = _setup_vault(tmp_path)
    res = cl.verify_vault(); cl.commit("vault_attested", attest(cl, "aud", AK, res["check_id"], vp))
    assert cl.commitments_attested()
    cl.commit("epoch_boundary_declared", F("declare_epoch_boundary", epoch="E2"))
    new = v.set_params("F1", c=2, a=2, b=2, m=2)
    cl.commit("params_rotated", C("params_rotated", family="F1", epoch="E2", params_commitment=new, delta=0.01))
    assert not cl.commitments_attested()                                   # new commitment not yet audited


def test_vault_check_must_cover_all_commitments(env):
    g, cl, cc, v = env
    fix_family(cl, v)
    with pytest.raises(GateError, match="every commitment"):
        cl.commit("vault_verified", C("vault_verified", result="ok", check_id="c1", commitments=[],
                                      mismatches=0, vault_ciphertext_sha256="a" * 64))


def test_vault_write_fsyncs_parent_dir(tmp_path, monkeypatch):
    import xauusd_swarm.custody as M
    seen = []
    monkeypatch.setattr(M, "_fsync_dir", lambda d: seen.append(Path(d)))
    Vault(tmp_path / "v.bin", os.urandom(32)).add_symbol("a", "b")
    assert seen == [tmp_path]


def test_load_key_location_and_permissions(tmp_path):
    for d in ("keys", "vault", "led"):
        (tmp_path / d).mkdir()
    kp = tmp_path / "keys" / "k.bin"; kp.write_bytes(os.urandom(32)); os.chmod(kp, 0o600)
    assert len(load_key(kp, vault_path=tmp_path / "vault" / "v.bin", ledger_path=tmp_path / "led" / "g.jsonl")) == 32
    with pytest.raises(GateError, match="must not sit"):
        load_key(kp, vault_path=tmp_path / "keys" / "v.bin")
    if os.name == "posix":                    # POSIX mode bits only; Windows has none (CUSTODY_KEY_POLICY)
        os.chmod(kp, 0o640)
        with pytest.raises(GateError, match="owner only"):
            load_key(kp, vault_path=tmp_path / "vault" / "v.bin")
    os.chmod(kp, 0o600); kp.write_bytes(b"short")
    with pytest.raises(GateError, match="32 bytes"):
        load_key(kp, vault_path=tmp_path / "vault" / "v.bin")
