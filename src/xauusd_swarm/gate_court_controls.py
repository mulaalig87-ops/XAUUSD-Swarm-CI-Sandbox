"""Stage 9, WP9-02 part 2 — control code and synthetic worlds for the C0 gate (TP-47) and the court
(TP-46). SYNTHETIC ONLY; deterministic by the seed in the world.

TP-47 (WP7-04 §2.1): positive — «أثر تغذية ومعالجة وبناء شموع مزروع يُعطي الحالة 1 أو 2 أو 3» (س 405–407);
negative — «عالم نظيف يُعطي الحالة 4 (س 408)، لا 1 إلى 3».
  The C0 TESTS are founder rules and the architecture gives no template (CS-03-04). The three detectors
  below are SYNTHETIC FIXTURES that exercise the gate (`inventory.run_c0`: binding to the approved
  implementation, state mapping, damage scope); they are not project rules (FD-01-D32):
    state 1 (feed):        duplicate market timestamps;
    state 2 (processing):  crossed quotes (ask < bid);
    state 3 (candle/order): market timestamps out of order.
  A world plants one effect class (or none) at known ids. Observed: for each of the three rules, the
  state and whether the damage scope equals the planted ids. match = 1 iff the planted class's rule gives
  its state with the exact planted scope AND every other rule gives state 4 (no cross-talk).

TP-46 (مع-21): «الحكم مطابق للمتوقع على عالم صفري وعالم بأثر مزروع، ومستقر بإعادة التشغيل (TP-08 (أ))».
  The court is run AS OPERATED: custody replica (vault, package store, service) and court replica on one
  in-memory ledger; claims and primary test instances registered; court frozen (structure A, Holm,
  alpha 0.05) before opening; the package passes custody, is sealed, and the operator runs the court.
  p-values: exact-ish sign-flip permutation test of mean > 0 (B = 999, seeded) on each claim's synthetic
  series (n = 200). Real world: claims K1, K2 carry a mean shift of 0.4 sd, K3 none. Null world: none.
  Observed: the set of confirmed claims and the ruling output hash. match = 1 iff the confirmed set equals
  the planted set. Stability on re-run is enforced by the controls layer (two identical runs) and the
  independent re-execution.
"""
from __future__ import annotations

import hashlib
import json
import random
import uuid

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from .inventory import content_sha256, impl_sha256, run_c0

# ======================= TP-47: C0 gate ==========================================================
def det_feed(obs):
    seen, aff = set(), []
    for o in obs:
        if o["t_market"] in seen:
            aff.append(o["id"])
        seen.add(o["t_market"])
    return {"outcome": "detected" if aff else "not_detected", "affected_ids": aff}


def det_processing(obs):
    aff = [o["id"] for o in obs if o["ask"] < o["bid"]]
    return {"outcome": "detected" if aff else "not_detected", "affected_ids": aff}


def det_order(obs):
    aff = [obs[i]["id"] for i in range(1, len(obs)) if obs[i]["t_market"] < obs[i - 1]["t_market"]]
    return {"outcome": "detected" if aff else "not_detected", "affected_ids": aff}


DETECTORS = {1: det_feed, 2: det_processing, 3: det_order}


def c0_rule(state):
    return {"rule_id": f"SYN-C0-{state}", "dataset_id": "SYN", "effect": {1: "feed", 2: "processing", 3: "candle"}[state],
            "test": DETECTORS[state].__name__, "criterion": "any", "resulting_state": state,
            "handling": {str(i): f"h{i}" for i in range(1, 6)}, "test_impl_sha256": impl_sha256(DETECTORS[state])}


def c0_world(seed, n, plant, k):
    """Clean synthetic quotes, then plant `k` effects of class `plant` (1, 2, 3 or None)."""
    rnd, p, obs = random.Random(seed), 100.0, []
    for i in range(n):
        p += rnd.gauss(0, 0.3)
        obs.append({"id": f"o{i}", "t_market": 60.0 * i, "bid": round(p - 0.02, 5), "ask": round(p + 0.02, 5)})
    planted = []
    if plant is not None:
        for i in sorted(rnd.sample(range(2, n - 2), k)):
            o = obs[i]
            if plant == 1:
                o["t_market"] = obs[i - 1]["t_market"]                  # feed: duplicated timestamp
            elif plant == 2:
                o["bid"], o["ask"] = o["ask"], o["bid"]                  # processing: crossed quote
            else:
                o["t_market"] = obs[i - 1]["t_market"] - 30.0            # order: earlier than predecessor
            planted.append(o["id"])
    return obs, planted


def run_c0_world(world: dict) -> dict:
    obs, planted = c0_world(world["seed"], world["n"], world["plant"], world["k"])
    states, ok = {}, True
    for state, det in DETECTORS.items():
        r = run_c0(c0_rule(state), det, obs)
        states[str(state)] = r["state"]
        if state == world["plant"]:
            ok = ok and r["state"] == state and sorted(r["scope_lineage"]) == sorted(planted)
        else:
            ok = ok and r["state"] == 4
    return {"match": 1 if ok else 0, "states": states, "planted": len(planted)}


def c0_world_spec(plant, *, seed=4701, n=300, k=5):
    return {"tool": "C0", "plant": plant, "seed": seed + (plant or 0), "n": n, "k": k}


# ======================= TP-46: court ============================================================
CONFIG = {"structure": "A", "alpha_total": 0.05, "error_measure": "FWER", "procedure": "holm",
          "validity_reason": "Holm controls FWER under any dependence (س 681)"}


def sign_flip_p(x, rnd, b=999):
    m = sum(x) / len(x)
    hits = sum(1 for _ in range(b) if sum(v * rnd.choice((-1, 1)) for v in x) / len(x) >= m)
    return (1 + hits) / (1 + b)


def court_package(world):
    rnd = random.Random(world["seed"])
    subs = []
    for cid in world["claims"]:
        mu = world["shift"] if cid in world["planted"] else 0.0
        x = [rnd.gauss(mu, 1.0) for _ in range(world["n"])]
        m = sum(x) / len(x)
        sd = (sum((v - m) ** 2 for v in x) / (len(x) - 1)) ** 0.5
        half = 1.96 * sd / len(x) ** 0.5
        subs.append({"test_instance_id": f"T-{cid}", "p_value": sign_flip_p(x, rnd, world["b"]),
                     "estimate": round(m, 9), "ci": [round(m - half, 9), round(m + half, 9)]})
    return json.dumps({"family": "F1", "submissions": subs}, sort_keys=True).encode()


def run_court_world(world: dict) -> dict:
    from .charter import Governance
    from .claims import ClaimsCharter
    from .court import CourtLayer, PackageStore
    from .court_service import CustodyCourtService
    from .custody import LEAK_SCOPE, CustodyLayer, Vault
    from .identity import public_hex, sign
    from .ledger import Ledger

    fk, ck, ok = (Ed25519PrivateKey.generate() for _ in range(3))
    F = lambda a, **kw: sign("founder", fk, {"action": a, "nonce": uuid.uuid4().hex, **kw})   # noqa: E731
    C = lambda a, **kw: sign("cust", ck, {"action": a, "nonce": uuid.uuid4().hex, **kw})     # noqa: E731
    led, store = Ledger(), PackageStore(key=bytes(32))
    cl = CustodyLayer(Vault(), identity="cust", key=ck)
    gC = Governance(fk.public_key(), led, extensions=[ClaimsCharter(), cl, CourtLayer(custody_store=store)])
    svc = CustodyCourtService(gC, store, identity="cust", key=ck)
    cc, ct = ClaimsCharter(), CourtLayer()
    g = Governance(fk.public_key(), led, extensions=[cc, CustodyLayer(None), ct])
    for i, k in (("cust", ck), ("op", ok)):
        g.register_key(F("register_key", identity=i, public_key_hex=public_hex(k.public_key())))
    cl.commit("role_assigned", F("assign_role", role="custody", holder="cust"))
    cl.commit("role_assigned", F("assign_role", role="court_operator", holder="op"))
    g.set_initial_charter(F("charter_initial", charter="project", text="P"))
    g.set_initial_charter(F("charter_initial", charter="claims", text="C"))
    com = cl.vault.set_params("F1", c=1, a=1, b=0, m=3)
    cl.commit("params_fixed", C("params_fixed", family="F1", params_commitment=com, delta=0.01))
    cl.commit("custody_decision", C("custody_decision", slice="S1", family="F1", boundaries="b", delta=0.01,
                                    params_commitment=com))
    g.consume_slice("S1")
    for cid in world["claims"]:
        cc.register(F("register_claim", card={"claim_id": cid, "version": 1, "tags": ["الموقع"], "category": None,
                      "path": "أ", "uses_events": False, "scope_type": "stable", "scope": "s",
                      "rulings": {"existence": "e", "size_with_uncertainty": "s", "importance": "i"}}))
        ct.commit("claim_identity_registered", F("register_claim_identity", claim_id=cid, identity={
            "target_quantity": f"mean {cid}", "eligible_data_scope": "synthetic", "time_scope_type": "stable",
            "proof_path": "أ", "direction_or_threshold": ">0", "observation_precision": "n/a", "price_series": "Mid"}))
        ct.commit("test_instance_registered", F("register_test_instance", test_instance_id=f"T-{cid}", claim_id=cid,
                  statistic="mean", procedure="sign-flip permutation", null="sign symmetry", slice="S1", seeds="w",
                  code_version="v1", representation_id="r", transform_version="t1", price_series="Mid", path="Z",
                  role="primary", null_card_accepted=True))
    ct.commit("court_policy_decided", F("decide_court_policy", family="F1", structure="A", error_measure="FWER",
                                        register_ref="synthetic TP-46", register_sha256="ab" * 32))
    ct.commit("court_frozen", F("freeze_court", family="F1", config=CONFIG))
    for cid in world["claims"]:
        cc.open_on_slice(cid, "S1")
    pkg = court_package(world)
    h = hashlib.sha256(pkg).hexdigest()
    cl.commit("z_output_passed", C("z_output_passed", output_sha256=h, reviewed=list(LEAK_SCOPE), passed=True))
    svc.deposit(pkg)
    cl.commit("submissions_sealed", sign("op", ok, {"action": "seal_submissions", "nonce": uuid.uuid4().hex,
                                                   "family": "F1", "submissions_sha256": h}))
    ruling = ct.run("F1", lambda st: sign("op", ok, {**st, "nonce": uuid.uuid4().hex}), svc)
    out = ruling["output"]
    confirmed = sorted(c for c, row in out["claims"].items() if row["confirmed"])
    return {"match": 1 if confirmed == sorted(world["planted"]) else 0, "confirmed": confirmed,
            "output_sha256": content_sha256(out),
            "p_values": {s["test_instance_id"]: s["p_value"] for s in json.loads(pkg)["submissions"]}}


def court_world_spec(kind, *, seed=4601, n=200, shift=0.4, b=999):
    return {"tool": "court", "kind": kind, "claims": ["K1", "K2", "K3"],
            "planted": ["K1", "K2"] if kind == "real" else [], "shift": shift, "n": n, "b": b,
            "seed": seed + (0 if kind == "real" else 1)}


EXPECTED = {"metric": "match", "op": "==", "value": 1}
