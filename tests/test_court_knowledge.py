"""Layers 9–10 tests: deterministic court, knowledge registry, lineage. Synthetic values only."""
import copy
import hashlib
import json
import os
import uuid

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from xauusd_swarm.charter import GateError, Governance
from xauusd_swarm.claims import ClaimsCharter
from xauusd_swarm.court import (CODE_SHA256, IMPORTANCE_UNDEFINED, NO_NULL_STATUS, CourtLayer, PackageStore, compute,
                                holm, sha)
from xauusd_swarm.court_service import CustodyCourtService
from xauusd_swarm.custody import LEAK_SCOPE, CustodyLayer, Vault
from xauusd_swarm.identity import AuthError, public_hex, sign
from xauusd_swarm.knowledge import UNCLASSIFIED, ZP, KnowledgeRegistry
from xauusd_swarm.ledger import AnchorStore, Ledger

FK, CK, OK, DK, LK = (Ed25519PrivateKey.generate() for _ in range(5))
SKEY = os.urandom(32)


def F(action, **kw):
    return sign("founder", FK, {"action": action, "nonce": uuid.uuid4().hex, **kw})


def C(action, **kw):
    return sign("cust", CK, {"action": action, "nonce": uuid.uuid4().hex, **kw})


def OP(st):
    return sign("op", OK, {**st, "nonce": uuid.uuid4().hex})


def card(cid):
    return {"claim_id": cid, "version": 1, "tags": ["الموقع"], "category": None, "path": "أ", "uses_events": False, "scope_type": "stable",
            "scope": "s", "rulings": {"existence": "e", "size_with_uncertainty": "s", "importance": "i"}}


def ident(q, series="Mid"):
    return {"target_quantity": q, "eligible_data_scope": "synthetic", "time_scope_type": "stable", "proof_path": "أ",
            "direction_or_threshold": ">0", "observation_precision": "n/a", "price_series": series}


def ti(tid, cid, path="Z", role="primary", null_ok=True, **kw):
    return F("register_test_instance", test_instance_id=tid, claim_id=cid, statistic="mean", procedure="t",
             null="N0", slice="S1", seeds="1", code_version="v1", representation_id="log_returns",
             transform_version="t1", price_series="Mid", path=path, role=role, null_card_accepted=null_ok, **kw)


_CT: list = []
CONFIG = {"structure": "A", "alpha_total": 0.05, "error_measure": "FWER", "procedure": "holm",
          "validity_reason": "Holm controls FWER under any dependence (س 681)"}
_SVC: list = []


def policy(fam, structure="A", measure="FWER"):
    return F("decide_court_policy", family=fam, structure=structure, error_measure=measure,
             register_ref="سجل 7 §NN (synthetic test)", register_sha256="ab" * 32)


def scope_of(ct, fam="F1"):
    ct.refresh()
    return ct.scope(fam)


def lineage(tid, llm=False, breach=(), mode="automatic"):
    return sign("lin", LK, {"action": "record_lineage", "nonce": uuid.uuid4().hex, "test_instance_id": tid,
        "capture_mode": mode,
        "data": {"source": "synthetic", "transforms": [{"name": "log_returns", "version": "t1", "params": {}}],
                 "block_usage": [], "exclusions": [{"rule": "r1", "reason": "gap", "count": 2}],
                 "blinding_state": "blinded", "availability_time_source": "مرصود"},
        "environment": {"libraries": ["x==1"], "environment": "wp801", "seeds": [1], "training_settings": {}},
        "hypothesis": {"versions_branches_edits": [], "epistemic_path": "as given"},
        "experiments": {"stopped_or_incomplete": [], "exclusion_reasons": []},
        "knowledge": {"seen": [], "tools": [], "touched_gold_or_R_info": False, "llm_in_lineage": llm,
                      "blinding_breach_events": list(breach)}})


def build(ledger=None, freeze=True, config=None, store=None, structure="A"):
    """Two replicas over one ledger: CUSTODY (vault, package store, court service) and COURT (no store,
    no package key, custody observer). Returns the court-side objects plus the custody layer."""
    led = ledger if ledger is not None else Ledger()
    store = store if store is not None else PackageStore(key=SKEY)
    cl = CustodyLayer(Vault(), identity="cust", key=CK)
    gC = Governance(FK.public_key(), led, extensions=[ClaimsCharter(), cl, CourtLayer(custody_store=store), KnowledgeRegistry()])
    _SVC.append(CustodyCourtService(gC, store, identity="cust", key=CK))
    cc, ct, kr = ClaimsCharter(), CourtLayer(), KnowledgeRegistry()
    g = Governance(FK.public_key(), led, extensions=[cc, CustodyLayer(None), ct, kr])
    _CT.append(ct)
    for i, k in (("cust", CK), ("op", OK), ("disc", DK), ("lin", LK)):
        g.register_key(F("register_key", identity=i, public_key_hex=public_hex(k.public_key())))
    for role, h in (("custody", "cust"), ("court_operator", "op"), ("discovery_participant", "disc")):
        cl.commit("role_assigned", F("assign_role", role=role, holder=h))
    g.set_initial_charter(F("charter_initial", charter="project", text="P"))
    g.set_initial_charter(F("charter_initial", charter="claims", text="C"))
    kr.commit("lineage_recorder_assigned", F("assign_lineage_recorder", holder="lin", capture_mode="automatic"))
    com = cl.vault.set_params("F1", c=1, a=1, b=0, m=3)
    cl.commit("params_fixed", C("params_fixed", family="F1", params_commitment=com, delta=0.01))
    cl.commit("custody_decision", C("custody_decision", slice="S1", family="F1", boundaries="b", delta=0.01, params_commitment=com))
    g.consume_slice("S1")
    for k, q in (("K1", "q1"), ("K2", "q2"), ("K3", "q3")):
        cc.register(F("register_claim", card=card(k)))
        ct.commit("claim_identity_registered", F("register_claim_identity", claim_id=k, identity=ident(q)))
    ct.commit("test_instance_registered", ti("T1", "K1"))
    ct.commit("test_instance_registered", ti("T2", "K2"))
    ct.commit("test_instance_registered", ti("T3", "K1", path="R"))
    ct.commit("test_instance_registered", ti("T4", "K1", role="descriptive"))
    ct.commit("test_instance_registered", ti("T5", "K3", null_ok=False))
    if freeze:
        ct.commit("court_policy_decided", policy("F1", structure))
        ct.commit("court_frozen", F("freeze_court", family="F1", config=config or CONFIG))
        for k in ("K1", "K2", "K3"):
            cc.open_on_slice(k, "S1")
    return g, cc, cl, ct, kr


def package(subs=None):
    subs = subs or [{"test_instance_id": "T1", "p_value": 0.001, "estimate": 0.5, "ci": [0.2, 0.8]},
                    {"test_instance_id": "T2", "p_value": 0.06, "estimate": 0.1, "ci": [-0.1, 0.3]},
                    {"test_instance_id": "T3", "p_value": 0.025, "estimate": 0.4, "ci": [0.1, 0.7]},
                    {"test_instance_id": "T4", "p_value": 0.0001, "estimate": 9.0, "ci": [8.0, 10.0]},
                    {"test_instance_id": "T5", "p_value": 0.0001, "estimate": 1.0, "ci": [0.5, 1.5]}]
    return json.dumps({"family": "F1", "submissions": subs}, sort_keys=True).encode()


def seal(cl, pkg):
    """Custody passage (س 254, 284) → custody store → operator seals by hash."""
    h = hashlib.sha256(pkg).hexdigest()
    if h not in cl.passed:
        cl.commit("z_output_passed", C("z_output_passed", output_sha256=h, reviewed=list(LEAK_SCOPE), passed=True))
    _SVC[-1].deposit(pkg)
    cl.commit("submissions_sealed", sign("op", OK, {"action": "seal_submissions", "nonce": uuid.uuid4().hex,
                                                   "family": "F1", "submissions_sha256": hashlib.sha256(pkg).hexdigest()}))


@pytest.fixture
def env():
    return build()


# ---------------- holm ----------------

def test_holm_known_values():
    d = holm([("a", 0.01), ("b", 0.04), ("c", 0.03), ("d", 0.005)], 0.05)
    assert d == {"d": "rejected", "a": "rejected", "c": "not_rejected", "b": "not_rejected"}  # 0.005≤.0125, .01≤.0167, .03>.025 stop
    assert holm([("x", 0.05)], 0.05) == {"x": "rejected"}


# ---------------- determinism (WP8-04 acceptance, TP-08 a) ----------------

def test_court_deterministic_and_reproducible(env):
    g, cc, cl, ct, kr = env
    pkg = package(); seal(cl, pkg)
    r = ct.run("F1", OP, _SVC[-1])
    outs = {sha(compute(json.loads(pkg), CONFIG, ct.instances, scope_of(ct))) for _ in range(20)}
    assert outs == {r["output_sha256"]}
    assert _SVC[-1].reproduce(r["ruling_id"])
    # reordered package with the same content → same ruling (independent of processing order, ق-03)
    shuffled = json.loads(pkg); shuffled["submissions"].reverse()
    assert sha(compute(shuffled, CONFIG, ct.instances, scope_of(ct))) == r["output_sha256"]
    assert r["code_sha256"] == CODE_SHA256


def test_operator_api_never_receives_package_and_store_is_encrypted(tmp_path, env):
    import inspect
    g, cc, cl, ct, kr = env
    assert list(inspect.signature(CourtLayer.run).parameters) == ["self", "family", "sign_as_operator", "service"]
    assert list(inspect.signature(CustodyCourtService.execute).parameters) == ["self", "request_payload"]
    st = PackageStore(tmp_path, key=SKEY)
    pkg = package(); h = st.put(pkg)
    raw = (tmp_path / h).read_bytes()
    # encrypted at rest; markers long enough not to occur in random ciphertext by chance (a 2-byte
    # marker b"T1" did: CI runs 44042948366, 44044878907)
    assert b"p_value" not in raw and b'"test_instance_id"' not in raw
    with pytest.raises(GateError, match="cannot decrypt"):
        PackageStore(tmp_path, key=os.urandom(32)).get(h)                 # no key, no content
    assert st.get(h) == pkg
    with pytest.raises(GateError, match="32-byte"):
        PackageStore(tmp_path)


def test_package_must_pass_custody_before_store(env):
    g, cc, cl, ct, kr = env
    with pytest.raises(GateError, match="passed custody"):
        _SVC[-1].deposit(package())


def test_court_rulings_content(env):
    g, cc, cl, ct, kr = env
    pkg = package(); seal(cl, pkg)
    out = ct.run("F1", OP, _SVC[-1])["output"]
    k1 = out["claims"]["K1"]
    assert k1["paths"]["Z"]["existence"] == "rejected" and k1["paths"]["R"]["existence"] == "rejected"
    assert k1["confirmed"] and not k1["divergent"]
    assert out["claims"]["K2"]["paths"]["Z"]["existence"] == "not_rejected"
    assert out["claims"]["K3"]["paths"]["Z"]["status"] == NO_NULL_STATUS          # no accepted null: not tested
    assert "T4" in out["descriptive_only"]                                         # descriptive never decides
    assert k1["paths"]["Z"]["importance"] == IMPORTANCE_UNDEFINED
    assert out["error_control"] == "FWER per batch"


def test_structure_b():
    cfg = {**CONFIG, "structure": "B", "alpha_by_path": {"Z": 0.03, "R": 0.02}}
    g, cc, cl, ct, kr = build(config=cfg, structure="B")
    pkg = package(); seal(cl, pkg)
    out = ct.run("F1", OP, _SVC[-1])["output"]
    assert out["claims"]["K1"]["paths"]["R"]["existence"] == "not_rejected"      # 0.025 > 0.02
    assert out["claims"]["K1"]["divergent"] and out["claims"]["K1"]["confirmed"]
    assert all(v.get("importance", IMPORTANCE_UNDEFINED) == IMPORTANCE_UNDEFINED
               for c in out["claims"].values() for v in c["paths"].values())


# ---------------- R2-1 / R2-2: freezing blocked until A/B and FWER/FDR are decided ----------------

def test_freeze_blocked_without_policy_decision():
    g, cc, cl, ct, kr = build(freeze=False)
    with pytest.raises(GateError, match="blocked until A/B and FWER/FDR"):
        ct.commit("court_frozen", F("freeze_court", family="F1", config=CONFIG))


def test_freeze_must_follow_policy_and_fdr_cannot_freeze():
    g, cc, cl, ct, kr = build(freeze=False)
    ct.commit("court_policy_decided", policy("F1", "B"))
    with pytest.raises(GateError, match="follow the recorded policy"):
        ct.commit("court_frozen", F("freeze_court", family="F1", config=CONFIG))           # A ≠ B
    with pytest.raises(GateError, match="one recorded policy"):
        ct.commit("court_policy_decided", policy("F1", "A"))
    ct.commit("court_policy_decided", policy("F3", "A", "FDR"))
    with pytest.raises(GateError, match="FDR procedures are not built"):
        ct.commit("court_frozen", F("freeze_court", family="F3", config={**CONFIG, "error_measure": "FDR"}))


@pytest.mark.parametrize("bad", [{"structure": "C"}, {"error_measure": "x"}, {"register_ref": ""}, {"register_sha256": "zz"}])
def test_policy_decision_validation(bad):
    g, cc, cl, ct, kr = build(freeze=False)
    st = json.loads(bytes.fromhex(policy("F1").to_payload()["statement_hex"]))
    with pytest.raises(GateError):
        ct.commit("court_policy_decided", sign("founder", FK, {**st, **bad, "nonce": uuid.uuid4().hex}))
    with pytest.raises(AuthError):
        ct.commit("court_policy_decided", sign("op", OK, {**st, "nonce": uuid.uuid4().hex}))


@pytest.mark.parametrize("bad", [
    {**CONFIG, "procedure": "bh"}, {**CONFIG, "error_measure": "FDR"}, {**CONFIG, "validity_reason": ""},
    {**CONFIG, "alpha_total": 1.5}, {**CONFIG, "alpha_total": True}, {**CONFIG, "alpha_total": 10 ** 400},
    {**CONFIG, "alpha_total": float("nan")}, {**CONFIG, "structure": "C"}, {**CONFIG, "alpha_by_path": {"Z": 0.01}},
    {**CONFIG, "importance": {"rule": "abs_interval_vs_threshold", "threshold": 0.1}},
    {**CONFIG, "importance": None}, {**CONFIG, "extra": 1}])
def test_freeze_rejects_invalid_config(bad):
    g, cc, cl, ct, kr = build(freeze=False)
    ct.commit("court_policy_decided", policy("F1"))
    with pytest.raises(GateError):
        ct.commit("court_frozen", F("freeze_court", family="F1", config=bad))


# ---------------- frozen before start; thresholds not changeable (TP-08 d) ----------------

def test_opening_requires_frozen_court_rules():
    g, cc, cl, ct, kr = build(freeze=False)
    with pytest.raises(GateError, match="frozen BEFORE opening"):
        cc.open_on_slice("K1", "S1")


def test_thresholds_cannot_change_after_freeze(env):
    g, cc, cl, ct, kr = env
    with pytest.raises(GateError, match="already frozen"):
        ct.commit("court_frozen", F("freeze_court", family="F1", config={**CONFIG, "alpha_total": 0.1}))
    with pytest.raises(AuthError):
        ct.commit("court_frozen", sign("op", OK, {"action": "freeze_court", "nonce": "z", "family": "F1", "config": CONFIG}))


def test_only_operator_runs_court_and_only_on_sealed_package(env):
    g, cc, cl, ct, kr = env
    pkg = package()
    with pytest.raises(GateError, match="no sealed package"):
        ct.run("F1", OP, _SVC[-1])                                   # not sealed yet
    seal(cl, pkg)
    with pytest.raises(GateError, match="court operator"):
        ct.run("F1", lambda st: sign("disc", DK, {**st, "nonce": uuid.uuid4().hex}), _SVC[-1])


def test_forged_ruling_output_refused(env):
    g, cc, cl, ct, kr = env
    pkg = package(); seal(cl, pkg)
    req = OP({"action": "court_run_request", "family": "F1"})
    resp = _SVC[-1].execute(req.to_payload())
    out2 = copy.deepcopy(resp["output"]); out2["claims"]["K2"]["paths"]["Z"]["existence"] = "rejected"
    base = {"action": "court_ruling", "family": "F1", "ruling_id": "F1:x", "package_sha256": resp["package_sha256"],
            "code_sha256": CODE_SHA256, "request": req.to_payload(), "attestation": resp["attestation"]}
    with pytest.raises(GateError, match="does not match its hash"):
        ct.commit("court_ruling", OP({**base, "output": out2, "output_sha256": resp["output_sha256"]}))
    with pytest.raises(GateError, match="attestation does not match"):        # self-consistent forgery
        ct.commit("court_ruling", OP({**base, "output": out2, "output_sha256": sha(out2)}))
    fake_att = sign("op", OK, json.loads(bytes.fromhex(resp["attestation"]["statement_hex"])))
    with pytest.raises(GateError, match="attested by custody"):
        ct.commit("court_ruling", OP({**base, "output": resp["output"], "output_sha256": resp["output_sha256"],
                                      "attestation": fake_att.to_payload()}))
    with pytest.raises(GateError, match="code version"):
        ct.commit("court_ruling", OP({**base, "output": resp["output"], "output_sha256": resp["output_sha256"],
                                      "code_sha256": "0" * 64}))
    ct.commit("court_ruling", OP({**base, "output": resp["output"], "output_sha256": resp["output_sha256"]}))
    with pytest.raises(GateError, match="replayed"):
        _SVC[-1].execute(req.to_payload())


def test_service_refuses_non_operator_request(env):
    g, cc, cl, ct, kr = env
    seal(cl, package())
    with pytest.raises(GateError, match="only the appointed court operator"):
        _SVC[-1].execute(sign("disc", DK, {"action": "court_run_request", "family": "F1", "nonce": "r1"}).to_payload())


def _walk(obj, seen=None, depth=0):
    seen = seen if seen is not None else set()
    if id(obj) in seen or depth > 6:
        return
    seen.add(id(obj))
    yield obj
    vals = (obj.values() if isinstance(obj, dict) else obj if isinstance(obj, (list, tuple, set))
            else vars(obj).values() if hasattr(obj, "__dict__") else ())
    for v in vals:
        yield from _walk(v, seen, depth + 1)


def test_court_side_replica_holds_no_store_key_or_package(env):
    g, cc, cl, ct, kr = env
    pkg = package(); seal(cl, pkg); ct.run("F1", OP, _SVC[-1])
    for o in _walk([g, cc, ct, kr]):
        assert not isinstance(o, PackageStore)
        assert not (isinstance(o, (bytes, bytearray)) and (o == SKEY or o == pkg))
    assert ct._store is None


# ---------------- identities and pre-registration (TP-08 b, c) ----------------

def test_test_instance_must_link_to_registered_claim_identity(env):
    g, cc, cl, ct, kr = env
    with pytest.raises(GateError, match="registered Claim ID"):
        ct.commit("test_instance_registered", ti("T9", "NOPE"))
    with pytest.raises(GateError, match="every field"):
        ct.commit("test_instance_registered", F("register_test_instance", test_instance_id="T9", claim_id="K1"))
    with pytest.raises(GateError, match="Z, G-Z or R"):
        ct.commit("test_instance_registered", ti("T9", "K1", path="Q"))
    with pytest.raises(GateError, match="price series"):
        st = json.loads(bytes.fromhex(ti("T9", "K1").to_payload()["statement_hex"]))
        ct.commit("test_instance_registered", sign("founder", FK, {**st, "price_series": "price", "nonce": "n9"}))


def test_no_new_budget_by_renaming():
    g, cc, cl, ct, kr = build(freeze=False)
    cc.register(F("register_claim", card=card("K1b")))
    with pytest.raises(GateError, match="renaming"):
        ct.commit("claim_identity_registered", F("register_claim_identity", claim_id="K1b", identity=ident("q1")))
    with pytest.raises(GateError, match="price series"):
        ct.commit("claim_identity_registered", F("register_claim_identity", claim_id="K1b", identity=ident("qx", "price")))


def test_one_primary_per_claim_and_path_before_opening():
    g, cc, cl, ct, kr = build(freeze=False)
    with pytest.raises(GateError, match="one primary"):
        ct.commit("test_instance_registered", ti("T1b", "K1"))


def test_instance_added_after_opening_is_descriptive_only(env):
    g, cc, cl, ct, kr = env
    ct.commit("test_instance_registered", ti("T6", "K2"))          # after opening (س 703)
    assert ct.instances["T6"]["descriptive"]
    subs = json.loads(package())["submissions"] + [{"test_instance_id": "T6", "p_value": 1e-9, "estimate": 5, "ci": [4, 6]}]
    pkg = package(subs); seal(cl, pkg)
    out = ct.run("F1", OP, _SVC[-1])["output"]
    assert "T6" in out["descriptive_only"] and out["claims"]["K2"]["paths"]["Z"]["test_instance_id"] == "T2"


def test_code_integrity_only_never_decides(env):
    g, cc, cl, ct, kr = env
    ct.commit("test_instance_registered", ti("T7", "K2", path="G-Z", code_integrity_only=True))
    subs = json.loads(package())["submissions"] + [{"test_instance_id": "T7", "p_value": 1e-9, "estimate": 1, "ci": [0, 2]}]
    pkg = package(subs); seal(cl, pkg)
    out = ct.run("F1", OP, _SVC[-1])["output"]
    assert "T7" in out["descriptive_only"] and "G-Z" not in out["claims"]["K2"]["paths"]


def test_package_with_unregistered_instance_refused(env):
    g, cc, cl, ct, kr = env
    pkg = package(json.loads(package())["submissions"] + [{"test_instance_id": "TX", "p_value": 0.1, "estimate": 0, "ci": [-1, 1]}])
    seal(cl, pkg)
    with pytest.raises(GateError, match="unregistered"):
        ct.run("F1", OP, _SVC[-1])


# ---------------- R1-1 completeness, R1-2 family, R1-6 numbers, R1-5 series, R1-8 path status ----------------

@pytest.mark.parametrize("drop", ["T1", "T2", "T3", "T5"])
def test_missing_preregistered_primary_refused(env, drop):
    g, cc, cl, ct, kr = env
    pkg = package([x for x in json.loads(package())["submissions"] if x["test_instance_id"] != drop]); seal(cl, pkg)
    with pytest.raises(GateError, match="lacks pre-registered primary"):
        ct.run("F1", OP, _SVC[-1])


def test_descriptive_may_be_absent(env):
    g, cc, cl, ct, kr = env
    pkg = package([x for x in json.loads(package())["submissions"] if x["test_instance_id"] != "T4"]); seal(cl, pkg)
    assert ct.run("F1", OP, _SVC[-1])["output"]["descriptive_only"] == []


def test_submission_from_other_family_refused(env):
    g, cc, cl, ct, kr = env
    com = cl.vault.set_params("F2", c=1, a=1, b=0, m=3)
    cl.commit("params_fixed", C("params_fixed", family="F2", params_commitment=com, delta=0.01))
    cl.commit("custody_decision", C("custody_decision", slice="S2", family="F2", boundaries="b", delta=0.01, params_commitment=com))
    g.consume_slice("S2")
    cc.register(F("register_claim", card=card("K9")))
    ct.commit("claim_identity_registered", F("register_claim_identity", claim_id="K9", identity=ident("q9")))
    st = json.loads(bytes.fromhex(ti("T9", "K9").to_payload()["statement_hex"]))
    ct.commit("test_instance_registered", sign("founder", FK, {**st, "slice": "S2", "nonce": "x9"}))
    ct.commit("court_policy_decided", policy("F2"))
    ct.commit("court_frozen", F("freeze_court", family="F2", config=CONFIG))
    cc.open_on_slice("K9", "S2")
    pkg = package(json.loads(package())["submissions"] + [{"test_instance_id": "T9", "p_value": 0.001, "estimate": 1, "ci": [0, 2]}])
    seal(cl, pkg)
    with pytest.raises(GateError, match="outside this claim family"):
        ct.run("F1", OP, _SVC[-1])
    pkg2 = {"family": "F2", "submissions": json.loads(package())["submissions"]}
    with pytest.raises(GateError, match="for the requested family"):
        compute(pkg2, CONFIG, ct.instances, scope_of(ct))


@pytest.mark.parametrize("bad", [
    {"p_value": 10 ** 400}, {"estimate": 10 ** 400}, {"ci": [0, 10 ** 400]}, {"ci": [-(10 ** 400), 1]},
    {"p_value": True}, {"p_value": float("nan")}, {"p_value": 1.5}, {"estimate": float("inf")}, {"estimate": "1"},
    {"ci": [0.8, 0.2]}, {"ci": [0.2]}, {"ci": [0.2, float("nan")]}, {"ci": (0.2, 0.8)}, {"estimate": False},
    {"extra": 1}])
def test_numeric_and_shape_validation(env, bad):
    g, cc, cl, ct, kr = env
    subs = json.loads(package())["submissions"]
    subs[0] = {**subs[0], **bad}
    with pytest.raises(GateError):
        compute({"family": "F1", "submissions": subs}, CONFIG, ct.instances, scope_of(ct))


def test_instance_price_series_must_match_claim(env):
    g, cc, cl, ct, kr = env
    st = json.loads(bytes.fromhex(ti("T8", "K2").to_payload()["statement_hex"]))
    with pytest.raises(GateError, match="price series must equal"):
        ct.commit("test_instance_registered", sign("founder", FK, {**st, "price_series": "Bid", "nonce": "s8"}))


def test_every_claim_and_path_has_a_status(env):
    g, cc, cl, ct, kr = env
    pkg = package(); seal(cl, pkg)
    out = ct.run("F1", OP, _SVC[-1])["output"]
    assert set(out["claims"]) == {"K1", "K2", "K3"}
    assert out["claims"]["K1"]["path_status"] == {"Z": "ruled", "G-Z": "no_primary_instance_registered", "R": "ruled"}
    assert out["claims"]["K3"]["path_status"]["Z"] == "not_tested_no_accepted_null"
    assert out["denominators"] == {"A": 3}


def test_release_hash_covers_state_modules():
    from xauusd_swarm.court import CODE_MANIFEST
    assert set(CODE_MANIFEST) == {"charter.py", "claims.py", "court.py", "court_service.py", "custody.py", "identity.py",
                                  "ledger.py"}


# ---------------- knowledge registry and lineage ----------------

def _ruled(env, llm=False, breach=()):
    g, cc, cl, ct, kr = env
    pkg = package(); seal(cl, pkg)
    r = ct.run("F1", OP, _SVC[-1])
    for t in ("T1", "T2", "T3", "T5"):
        kr.commit("lineage_recorded", lineage(t, llm=(llm and t == "T3"), breach=breach))
        kr.commit("lineage_sealed", sign("lin", LK, {**kr.seal_statement(t), "nonce": uuid.uuid4().hex}))
    return r


def test_knowledge_record_from_court_output(env):
    g, cc, cl, ct, kr = env
    r = _ruled(env)
    st = kr.build_record(r["ruling_id"], "K1", reporting_level=1, availability="مرصود")
    kr.commit("knowledge_recorded", OP(st))
    rec = kr.records[-1]
    assert rec["row"] == r["output"]["claims"]["K1"] and set(rec["row"]["paths"]) == {"Z", "R"}   # one row, all paths
    assert rec["zero_prior"] == ZP["undetermined"] and rec["classification"] == UNCLASSIFIED
    assert rec["recorded_by"] == "op" and rec["claim_meta"]["representation_ids"] == ["log_returns"]


def test_knowledge_row_must_equal_code_output(env):
    g, cc, cl, ct, kr = env
    r = _ruled(env)
    st = kr.build_record(r["ruling_id"], "K2", reporting_level=1, availability="مرصود")
    st["row"] = copy.deepcopy(st["row"]); st["row"]["paths"]["Z"]["existence"] = "rejected"
    with pytest.raises(GateError, match="as output by code"):
        kr.commit("knowledge_recorded", OP(st))


def test_knowledge_only_via_operator_and_once(env):
    g, cc, cl, ct, kr = env
    r = _ruled(env)
    st = kr.build_record(r["ruling_id"], "K1", reporting_level=1, availability="مرصود")
    with pytest.raises(GateError, match="court operator only"):
        kr.commit("knowledge_recorded", sign("disc", DK, {**st, "nonce": "d1"}))
    kr.commit("knowledge_recorded", OP(st))
    with pytest.raises(GateError, match="one row per claim"):
        kr.commit("knowledge_recorded", OP(st))


def test_zero_prior_from_lineage_not_supplied(env):
    g, cc, cl, ct, kr = env
    r = _ruled(env, llm=True)
    st = kr.build_record(r["ruling_id"], "K1", reporting_level=1, availability="مرصود")
    assert st["zero_prior"] == ZP["linguistic"]
    with pytest.raises(GateError, match="computed from lineage"):
        kr.commit("knowledge_recorded", OP({**st, "zero_prior": ZP["computational"]}))
    kr.commit("knowledge_recorded", OP(st))


def test_zero_prior_breach():
    env = build()
    r = _ruled(env, breach=[{"event": "synthetic"}])
    assert env[4].build_record(r["ruling_id"], "K2", reporting_level=1, availability="مرصود")["zero_prior"] == ZP["breach"]


def test_knowledge_requires_sealed_lineage(env):
    g, cc, cl, ct, kr = env
    pkg = package(); seal(cl, pkg)
    r = ct.run("F1", OP, _SVC[-1])
    kr.commit("lineage_recorded", lineage("T1")); kr.commit("lineage_recorded", lineage("T3"))
    st = kr.build_record(r["ruling_id"], "K1", reporting_level=1, availability="مرصود")
    with pytest.raises(GateError, match="must be sealed"):
        kr.commit("knowledge_recorded", OP(st))


def test_lineage_seal_freezes_and_corrections_append(env):
    g, cc, cl, ct, kr = env
    r = _ruled(env)
    with pytest.raises(GateError, match="sealed"):
        kr.commit("lineage_recorded", lineage("T1", llm=True))           # cannot change after seal
    first = kr.lineage["T1"][0]["statement_sha256"]
    kr.commit("lineage_corrected", sign("lin", LK, {"action": "correct_lineage", "nonce": "c1", "test_instance_id": "T1",
                                                    "corrects": first, "reason": "typo", "correction": {"tools": ["x"]}}))
    assert len(kr.lineage["T1"]) == 1 and len(kr.corrections["T1"]) == 1  # sealed set unchanged
    st = kr.build_record(r["ruling_id"], "K1", reporting_level=1, availability="مرصود")
    assert st["lineage_seals"] == {"T1": kr.seals["T1"]["lineage_sha256"], "T3": kr.seals["T3"]["lineage_sha256"]}
    kr.commit("knowledge_recorded", OP(st))
    with pytest.raises(GateError, match="cite the lineage seal"):
        kr.commit("knowledge_recorded", OP({**kr.build_record(r["ruling_id"], "K2", reporting_level=1, availability="مرصود"),
                                            "lineage_seals": {}}))
    with pytest.raises(GateError, match="already sealed"):
        kr.commit("lineage_sealed", sign("lin", LK, {**kr.seal_statement("T1"), "nonce": "s2"}))


def test_seal_must_cover_exactly_recorded_lineage(env):
    g, cc, cl, ct, kr = env
    kr.commit("lineage_recorded", lineage("T1"))
    with pytest.raises(GateError, match="exactly"):
        kr.commit("lineage_sealed", sign("lin", LK, {"action": "seal_lineage", "test_instance_id": "T1",
                                                    "lineage_sha256": "0" * 64, "nonce": "s0"}))


def test_lineage_only_by_assigned_recorder_with_declared_mode(env):
    g, cc, cl, ct, kr = env
    st = json.loads(bytes.fromhex(lineage("T1").to_payload()["statement_hex"]))
    with pytest.raises(GateError, match="assigned lineage recorder"):
        kr.commit("lineage_recorded", sign("disc", DK, st))
    with pytest.raises(GateError, match="capture_mode"):
        kr.commit("lineage_recorded", lineage("T1", mode="manual"))
    with pytest.raises(GateError, match="court operator does not record"):
        kr.commit("lineage_recorder_assigned", F("assign_lineage_recorder", holder="op", capture_mode="manual"))
    with pytest.raises(AuthError):
        kr.commit("lineage_recorder_assigned", sign("lin", LK, {"action": "assign_lineage_recorder", "nonce": "q",
                                                                "holder": "disc", "capture_mode": "manual"}))


@pytest.mark.parametrize("mut", [
    lambda s: s["data"].pop("exclusions"), lambda s: s["data"].update(exclusions=[{"rule": "r", "reason": "x"}]),
    lambda s: s["data"].update(availability_time_source="?"), lambda s: s["knowledge"].update(llm_in_lineage="no"),
    lambda s: s.pop("environment"), lambda s: s.update(test_instance_id="NOPE")])
def test_lineage_record_validation(env, mut):
    g, cc, cl, ct, kr = env
    st = json.loads(bytes.fromhex(lineage("T1").to_payload()["statement_hex"]))
    mut(st)
    with pytest.raises(GateError):
        kr.commit("lineage_recorded", sign("lin", LK, st))


@pytest.mark.parametrize("meta", [{"reporting_level": 4}, {"reporting_level": 2}, {"availability": "?"},
                                  {"price_series": ["Bid"]}])
def test_claim_meta_validation(env, meta):
    g, cc, cl, ct, kr = env
    r = _ruled(env)
    st = kr.build_record(r["ruling_id"], "K1", reporting_level=1, availability="مرصود")
    st["claim_meta"] = {**st["claim_meta"], **meta}
    with pytest.raises(GateError):
        kr.commit("knowledge_recorded", OP(st))


def test_no_deletion_event_exists(env):
    g, cc, cl, ct, kr = env
    with pytest.raises(GateError, match="unknown event kind"):
        g._commit("knowledge_deleted", {"x": 1})


# ---------------- persistence ----------------

def test_court_and_knowledge_rebuilt_after_restart(tmp_path):
    (tmp_path / "l").mkdir(); (tmp_path / "a").mkdir(); (tmp_path / "pk").mkdir()
    def fl(): return Ledger(tmp_path / "l" / "g.jsonl", anchors=AnchorStore(tmp_path / "a" / "x.jsonl"))
    env = build(fl(), store=PackageStore(tmp_path / "pk", key=SKEY))
    r = _ruled(env)
    env[4].commit("knowledge_recorded", OP(env[4].build_record(r["ruling_id"], "K1", reporting_level=1, availability="مرصود")))
    # court-side replica (no store): verifies attestation and hashes
    ct2, kr2 = CourtLayer(), KnowledgeRegistry()
    Governance(FK.public_key(), fl(), extensions=[ClaimsCharter(), CustodyLayer(None), ct2, kr2])
    assert ct2.rulings[r["ruling_id"]]["output_sha256"] == r["output_sha256"]
    assert kr2.records[-1]["row"] == r["output"]["claims"]["K1"] and len(kr2.lineage) == 4
    # custody replica: recomputes every ruling from the store
    st = PackageStore(tmp_path / "pk", key=SKEY)
    gC = Governance(FK.public_key(), fl(), extensions=[ClaimsCharter(), CustodyLayer(None), CourtLayer(custody_store=st),
                                                      KnowledgeRegistry()])
    assert CustodyCourtService(gC, st, identity="cust", key=CK).reproduce(r["ruling_id"])
    with pytest.raises(GateError, match="cannot be recomputed"):
        Governance(FK.public_key(), fl(), extensions=[ClaimsCharter(), CustodyLayer(None),
                                                     CourtLayer(custody_store=PackageStore(key=SKEY)), KnowledgeRegistry()])


def test_package_store_detects_corruption(tmp_path):
    st = PackageStore(tmp_path, key=SKEY)
    h = st.put(b"pkg")
    b = bytearray((tmp_path / h).read_bytes()); b[-1] ^= 1; (tmp_path / h).write_bytes(bytes(b))
    with pytest.raises(GateError, match="cannot decrypt"):
        st.get(h)
