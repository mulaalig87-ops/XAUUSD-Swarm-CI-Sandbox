"""R2-3 / R2-6: the boundary between the two replicas, using the R3 interfaces as they are
(CourtLayer, CustodyCourtService, PackageStore). No new roles or rules are introduced here.

- OBSERVER replica (the court operator's process, this test process): CourtLayer() and
  CustodyLayer(None). It holds no store, no store key and no package bytes. It verifies the
  operator's run request, the custody attestation, the hashes and the scope, and records the ruling.
- CUSTODY replica (a SPAWNED process): it generates BOTH its store key and its Ed25519 signing key
  itself; only the custody PUBLIC key leaves it. Custody-signed setup events (parameters, slice
  decision, Z-output passage) are signed and committed inside it through narrow commands; there is
  no general signing command. It holds
  the encrypted PackageStore, and rebuilds its replica with CourtLayer(custody_store=...), so every
  recorded ruling is recomputed from the sealed package on each rebuild. It computes the ruling from
  the package before signing the attestation.
Synthetic values only.
"""
import copy
import hashlib
import json
import multiprocessing as mp
import os
import uuid
from pathlib import Path

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

from xauusd_swarm.charter import GateError, Governance
from xauusd_swarm.claims import ClaimsCharter
from xauusd_swarm.court import CODE_SHA256, CourtLayer, PackageStore, sha
from xauusd_swarm.custody import LEAK_SCOPE, CustodyLayer
from xauusd_swarm.identity import public_hex, sign
from xauusd_swarm.knowledge import KnowledgeRegistry
from xauusd_swarm.ledger import AnchorStore, Ledger


def _ledger(root):
    return Ledger(Path(root) / "led" / "g.jsonl", anchors=AnchorStore(Path(root) / "anc" / "a.jsonl"))


# ======================= CUSTODY replica (spawned process) =================================

def custody_replica_main(conn, root, founder_pub_raw):
    from xauusd_swarm.court import compute
    from xauusd_swarm.court_service import CustodyCourtService
    key = os.urandom(32)                                   # store key: generated here, never sent
    ck = Ed25519PrivateKey.generate()                      # custody signing key: generated here, never sent
    store = PackageStore(Path(root) / "store", key=key)
    fpk = Ed25519PublicKey.from_public_bytes(founder_pub_raw)
    conn.send(("pub", ck.public_key().public_bytes_raw()))

    def C(a, **k):
        return sign("cust", ck, {"action": a, "nonce": uuid.uuid4().hex, **k})

    while True:
        cmd, arg = conn.recv()
        if cmd == "stop":
            conn.close()
            return
        try:
            # full rebuild = recompute every recorded ruling from the store (CourtLayer(custody_store))
            cl, ctc = CustodyLayer(None, identity="cust", key=ck), CourtLayer(custody_store=store)
            g = Governance(fpk, _ledger(root), extensions=[ClaimsCharter(), cl, ctc, KnowledgeRegistry()])
            svc = CustodyCourtService(g, store, identity="cust", key=ck)
            if cmd == "fix_params":
                cl.commit("params_fixed", C("params_fixed", **arg)); res = True
            elif cmd == "decide_slice":
                cl.commit("custody_decision", C("custody_decision", **arg)); res = True
            elif cmd == "pass_output":
                cl.commit("z_output_passed", C("z_output_passed", output_sha256=arg, reviewed=list(LEAK_SCOPE),
                                               passed=True)); res = True
            elif cmd == "deposit":
                res = svc.deposit(arg)
            elif cmd == "execute":
                res = svc.execute(arg)
            elif cmd == "reproduce":
                res = svc.reproduce(arg)
            elif cmd == "rebuild":
                # the rebuild above already recomputed every ruling inside validation; report it explicitly
                res = {rid: {"recorded": r["output_sha256"],
                             "recomputed": sha(compute(json.loads(store.get(r["package_sha256"])), ctc.configs[r["family"]],
                                                       ctc.instances, ctc.scope(r["family"])))}
                       for rid, r in ctc.rulings.items()}
            else:
                raise ValueError(cmd)
            conn.send(("ok", res))
        except Exception as x:                             # noqa: BLE001
            conn.send(("err", f"{type(x).__name__}: {x}"))


class CustodyReplica:
    """Proxy held by the court process: messages only, no store, no key."""

    def __init__(self, conn):
        self._conn = conn

    def _call(self, cmd, arg=None):
        self._conn.send((cmd, arg))
        st, res = self._conn.recv()
        if st == "err":
            raise GateError(res)
        return res

    def deposit(self, data):
        return self._call("deposit", data)

    def execute(self, payload):
        return self._call("execute", payload)

    def reproduce(self, rid):
        return self._call("reproduce", rid)

    def rebuild(self):
        return self._call("rebuild")

    def fix_params(self, **kw):
        return self._call("fix_params", kw)

    def decide_slice(self, **kw):
        return self._call("decide_slice", kw)

    def pass_output(self, h):
        return self._call("pass_output", h)


# ======================= OBSERVER replica (this process) + fixture ===========================

@pytest.fixture
def world(tmp_path):
    for d in ("led", "anc", "store"):
        (tmp_path / d).mkdir()
    FK, OK, DK = (Ed25519PrivateKey.generate() for _ in range(3))     # founder, operator, discovery (test harness)
    ctx = mp.get_context("spawn")
    parent, child = ctx.Pipe()
    p = ctx.Process(target=custody_replica_main, args=(child, str(tmp_path), FK.public_key().public_bytes_raw()))
    p.start()
    tag, cust_pub_raw = parent.recv()
    assert tag == "pub" and len(cust_pub_raw) == 32
    CPUB = Ed25519PublicKey.from_public_bytes(cust_pub_raw)          # the ONLY custody key material here
    custody = CustodyReplica(parent)
    F = lambda a, **k: sign("founder", FK, {"action": a, "nonce": uuid.uuid4().hex, **k})
    OP = lambda st: sign("op", OK, {**st, "nonce": uuid.uuid4().hex})
    cc, cl, ct = ClaimsCharter(), CustodyLayer(None), CourtLayer()        # observer replica
    g = Governance(FK.public_key(), _ledger(tmp_path), extensions=[cc, cl, ct, KnowledgeRegistry()])
    for i, pk in (("cust", CPUB), ("op", OK.public_key()), ("disc", DK.public_key())):
        g.register_key(F("register_key", identity=i, public_key_hex=public_hex(pk)))
    for role, h in (("custody", "cust"), ("court_operator", "op"), ("discovery_participant", "disc")):
        cl.commit("role_assigned", F("assign_role", role=role, holder=h))
    g.set_initial_charter(F("charter_initial", charter="project", text="P"))
    g.set_initial_charter(F("charter_initial", charter="claims", text="C"))
    com = "ef" * 32                                       # observer mode: no vault in this process
    custody.fix_params(family="F1", params_commitment=com, delta=0.01)
    custody.decide_slice(slice="S1", family="F1", boundaries="b", delta=0.01, params_commitment=com)
    g.consume_slice("S1")
    cc.register(F("register_claim", card={"claim_id": "K1", "version": 1, "tags": ["الموقع"], "category": None,
                                          "path": "أ", "uses_events": False, "scope_type": "stable", "scope": "s",
                                          "rulings": {"existence": "e", "size_with_uncertainty": "s", "importance": "i"}}))
    ct.commit("claim_identity_registered", F("register_claim_identity", claim_id="K1", identity={
        "target_quantity": "q", "eligible_data_scope": "synthetic", "time_scope_type": "stable", "proof_path": "أ",
        "direction_or_threshold": ">0", "observation_precision": "n/a", "price_series": "Mid"}))
    ct.commit("test_instance_registered", F("register_test_instance", test_instance_id="T1", claim_id="K1",
              statistic="m", procedure="t", null="N0", slice="S1", seeds="1", code_version="v1",
              representation_id="log_returns", transform_version="t1", price_series="Mid", path="Z",
              role="primary", null_card_accepted=True))
    ct.commit("court_policy_decided", F("decide_court_policy", family="F1", structure="A", error_measure="FWER",
                                        register_ref="synthetic", register_sha256="cd" * 32))
    ct.commit("court_frozen", F("freeze_court", family="F1", config={
        "structure": "A", "alpha_total": 0.05, "error_measure": "FWER", "procedure": "holm",
        "validity_reason": "Holm, any dependence (س 681)"}))
    cc.open_on_slice("K1", "S1")
    pkg = json.dumps({"family": "F1", "submissions": [
        {"test_instance_id": "T1", "p_value": 0.01, "estimate": 0.4, "ci": [0.1, 0.7]}]}, sort_keys=True).encode()
    h = hashlib.sha256(pkg).hexdigest()
    custody.pass_output(h)
    assert custody.deposit(pkg) == h
    del pkg                                               # the harness drops its synthetic copy
    cl.commit("submissions_sealed", sign("op", OK, {"action": "seal_submissions", "nonce": "s", "family": "F1",
                                                   "submissions_sha256": h}))
    w = dict(g=g, cc=cc, cl=cl, ct=ct, custody=custody, OP=OP, F=F, OK=OK, DK=DK, FK=FK, CPUB=CPUB, h=h,
             root=tmp_path, cust_pub_raw=cust_pub_raw)
    try:
        yield w
    finally:
        parent.send(("stop", None))
        p.join(30)
        if p.is_alive():
            p.terminate()


def _walk(obj, seen=None, depth=0):
    seen = seen if seen is not None else set()
    if id(obj) in seen or depth > 6:
        return
    seen.add(id(obj))
    yield obj
    if callable(obj) and getattr(obj, "__closure__", None):
        vals = [c.cell_contents for c in obj.__closure__]
    else:
        vals = (obj.values() if isinstance(obj, dict) else obj if isinstance(obj, (list, tuple, set))
                else vars(obj).values() if hasattr(obj, "__dict__") else ())
    for v in vals:
        yield from _walk(v, seen, depth + 1)


# ======================= observer replica: responsibilities =================================

def test_observer_records_ruling_without_custody_secrets(world):
    w = world
    r = w["ct"].run("F1", w["OP"], w["custody"])
    assert r["output"]["claims"]["K1"]["paths"]["Z"]["existence"] == "rejected"
    assert w["ct"]._store is None and w["cl"]._key is None and w["cl"].vault is None
    cust_pub = w["cust_pub_raw"]
    # walk the WHOLE observer environment: replicas, proxy, harness signers and their closures
    for o in _walk(list(w.values())):
        assert not isinstance(o, PackageStore)
        assert not (isinstance(o, (bytes, bytearray)) and b"p_value" in o)                      # no package bytes
        if isinstance(o, Ed25519PrivateKey):                                                     # no custody private key
            assert o.public_key().public_bytes_raw() != cust_pub
        if isinstance(o, (bytes, bytearray)) and len(o) == 32:                                   # 32-byte material is public only
            assert o == cust_pub
    # the observer can verify custody signatures (public key) but cannot produce one
    assert w["g"].keys()["cust"] == public_hex(w["CPUB"])


# ======================= custody replica: responsibilities ==================================

def test_custody_rebuild_recomputes_recorded_ruling(world):
    w = world
    r = w["ct"].run("F1", w["OP"], w["custody"])
    rep = w["custody"].rebuild()
    assert rep == {r["ruling_id"]: {"recorded": r["output_sha256"], "recomputed": r["output_sha256"]}}
    assert sha(r["output"]) == r["output_sha256"]
    assert w["custody"].reproduce(r["ruling_id"]) is True


def test_custody_rebuild_refused_when_package_missing(world):
    w = world
    w["ct"].run("F1", w["OP"], w["custody"])
    (w["root"] / "store" / w["h"]).unlink()
    with pytest.raises(GateError, match="cannot be recomputed"):
        w["custody"].rebuild()


def test_custody_rebuild_refused_when_package_tampered(world):
    w = world
    w["ct"].run("F1", w["OP"], w["custody"])
    f = w["root"] / "store" / w["h"]
    b = bytearray(f.read_bytes()); b[-1] ^= 1; f.write_bytes(bytes(b))
    with pytest.raises(GateError, match="cannot decrypt"):
        w["custody"].rebuild()


def test_custody_refuses_tampered_store(world):
    w = world
    f = w["root"] / "store" / w["h"]
    b = bytearray(f.read_bytes()); b[-1] ^= 1; f.write_bytes(bytes(b))
    with pytest.raises(GateError, match="cannot decrypt"):
        w["custody"].execute(w["OP"]({"action": "court_run_request", "family": "F1"}).to_payload())


# ======================= negative cases ====================================================

def test_key_access_attempts_from_court_process_fail(world):
    w = world
    blob = (w["root"] / "store" / w["h"]).read_bytes()
    # plaintext markers must not appear; markers are long enough that random ciphertext cannot contain
    # them by chance (a 2-byte marker such as b"T1" did, ~1 run in 300: CI run 44042948366)
    assert b"p_value" not in blob and b'"test_instance_id"' not in blob
    for guess in (os.urandom(32), w["cust_pub_raw"], w["OK"].private_bytes_raw(), w["FK"].private_bytes_raw(), b"\0" * 32):
        with pytest.raises(GateError, match="cannot decrypt"):
            PackageStore(w["root"] / "store", key=guess).get(w["h"])


def test_replayed_and_non_operator_requests_refused(world):
    w = world
    r = w["ct"].run("F1", w["OP"], w["custody"])
    with pytest.raises(GateError, match="replayed"):
        w["custody"].execute(r["request"])
    with pytest.raises(GateError, match="only the appointed court operator"):
        w["custody"].execute(sign("disc", w["DK"], {"action": "court_run_request", "family": "F1", "nonce": "x"}).to_payload())
    with pytest.raises(GateError, match="only the appointed court operator"):
        w["custody"].execute(sign("founder", w["FK"], {"action": "court_run_request", "family": "F1", "nonce": "y"}).to_payload())


def test_observer_cannot_forge_custody_events(world):
    w = world
    fake = Ed25519PrivateKey.generate()
    with pytest.raises(Exception):                         # signature does not verify against the custody public key
        w["cl"].commit("z_output_passed", sign("cust", fake, {"action": "z_output_passed", "nonce": "f",
                                                              "output_sha256": "0" * 64, "reviewed": list(LEAK_SCOPE),
                                                              "passed": True}))


def test_forged_output_attestation_and_code_version_refused(world):
    w = world
    ct, OP = w["ct"], w["OP"]
    req = OP({"action": "court_run_request", "family": "F1"})
    resp = w["custody"].execute(req.to_payload())
    base = {"action": "court_ruling", "family": "F1", "ruling_id": "F1:0", "package_sha256": resp["package_sha256"],
            "code_sha256": CODE_SHA256, "request": req.to_payload(), "attestation": resp["attestation"]}
    forged = copy.deepcopy(resp["output"]); forged["claims"]["K1"]["paths"]["Z"]["existence"] = "not_rejected"
    with pytest.raises(GateError, match="attestation does not match"):
        ct.commit("court_ruling", OP({**base, "output": forged, "output_sha256": sha(forged)}))
    op_att = sign("op", w["OK"], json.loads(bytes.fromhex(resp["attestation"]["statement_hex"])))
    with pytest.raises(GateError, match="attested by custody"):
        ct.commit("court_ruling", OP({**base, "output": resp["output"], "output_sha256": resp["output_sha256"],
                                      "attestation": op_att.to_payload()}))
    with pytest.raises(GateError, match="code version"):
        ct.commit("court_ruling", OP({**base, "output": resp["output"], "output_sha256": resp["output_sha256"],
                                      "code_sha256": "0" * 64}))
    other_req = OP({"action": "court_run_request", "family": "F1"})            # attestation bound to its request
    with pytest.raises(GateError, match="attestation does not match"):
        ct.commit("court_ruling", OP({**base, "request": other_req.to_payload(), "output": resp["output"],
                                      "output_sha256": resp["output_sha256"]}))
    ct.commit("court_ruling", OP({**base, "output": resp["output"], "output_sha256": resp["output_sha256"]}))
    assert w["custody"].rebuild() == {"F1:0": {"recorded": resp["output_sha256"], "recomputed": resp["output_sha256"]}}
