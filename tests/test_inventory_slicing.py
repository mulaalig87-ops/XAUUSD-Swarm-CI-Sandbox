"""Layers 4 and 5 tests (WP8-05): inventory, C0, transforms, capability table, slicing,
purge/embargo, availability time. SYNTHETIC DATA ONLY (Register §34); no gold data.

Test-plan items exercised here: TP-03 (a)–(d), TP-10 (a)–(d), TP-28 (planted insufficient purge),
TP-47 (planted feed / processing / candle effects -> states 1–3; clean world -> 4), TP-61.02 (raw ->
inventory / deterministic transforms, condition enforced and violations refused).
The C0 tests used below are SYNTHETIC FIXTURES written for these unit tests; they are not project
C0 rules (those are the founder's, ق-11, and none exist yet).
"""
import json
import random
import uuid

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from xauusd_swarm import inventory as INV
from xauusd_swarm import slicing as SL
from xauusd_swarm.charter import GateError, Governance
from xauusd_swarm.claims import ClaimsCharter
from xauusd_swarm.custody import CustodyLayer, Vault
from xauusd_swarm.identity import AuthError, public_hex, sign
from xauusd_swarm.inventory import InventoryLayer, take_inventory
from xauusd_swarm.ledger import AnchorStore, Ledger
from xauusd_swarm.slicing import Sample, SlicingLayer, audit_split, split

FK, CK, AK, OK, DK = (Ed25519PrivateKey.generate() for _ in range(5))


def F(action, **kw):
    return sign("founder", FK, {"action": action, "nonce": uuid.uuid4().hex, **kw})


def C(action, key=CK, who="cust", **kw):
    return sign(who, key, {"action": action, "nonce": uuid.uuid4().hex, **kw})


# ---------------- synthetic transform implementations (fixtures) ----------------
def tf_mid(obs, p):
    return [{**o, "mid": (o["bid"] + o["ask"]) / 2} for o in obs]


def tf_scale(obs, p):
    return [p["s"]]


def tf_identity(obs, p):
    return obs


# ---------------- synthetic world ----------------
def world(n=200, seed=7, *, arrival=False):
    rnd, p, out = random.Random(seed), 100.0, []
    for i in range(n):
        o = p
        c = o + rnd.gauss(0, 0.3)
        hi, lo = max(o, c) + abs(rnd.gauss(0, 0.1)), min(o, c) - abs(rnd.gauss(0, 0.1))
        r = {"id": f"o{i}", "t_market": 60.0 * i, "open": round(o, 5), "high": round(hi, 5),
             "low": round(lo, 5), "close": round(c, 5), "bid": round(c - 0.02, 5), "ask": round(c + 0.02, 5),
             "source": "S1"}
        if arrival:
            r["t_arrival"] = 60.0 * i + 0.5
        out.append(r)
        p = c
    return out


def build(ledger=None):
    cl = CustodyLayer(Vault(), identity="cust", key=CK)
    cc, il, sl = ClaimsCharter(), InventoryLayer(identity="cust", key=CK), SlicingLayer()
    g = Governance(FK.public_key(), ledger if ledger is not None else Ledger(), extensions=[cc, cl, il, sl])
    for ident, k in (("cust", CK), ("aud", AK), ("op", OK), ("disc", DK)):
        g.register_key(F("register_key", identity=ident, public_key_hex=public_hex(k.public_key())))
    for role, h in (("custody", "cust"), ("custody_auditor", "aud"), ("court_operator", "op"),
                    ("discovery_participant", "disc")):
        cl.commit("role_assigned", F("assign_role", role=role, holder=h))
    g.set_initial_charter(F("charter_initial", charter="project", text="P"))
    g.set_initial_charter(F("charter_initial", charter="claims", text="C"))
    return g, cl, cc, il, sl


SLICES = [{"slice_id": "D1", "station": "Discovery", "start": 0.0, "end": 4000.0},
          {"slice_id": "V1", "station": "Validation", "start": 4000.0, "end": 8000.0},
          {"slice_id": "X1", "station": "Final", "start": 8000.0, "end": 11940.0}]


def inventoried(env, ds="SYN1", obs=None):
    g, cl, cc, il, sl = env
    il.permit(F("permit_inventory", dataset_id=ds, data_class="synthetic"))
    return il.record_inventory(ds, obs if obs is not None else world(), source="synthetic-generator")


def planned(env, ds="SYN1"):
    inventoried(env, ds)
    g, cl, cc, il, sl = env
    sl.freeze_plan(il, "P1", ds, basis="calendar_time", slices=SLICES)


@pytest.fixture
def env():
    return build()


def rule(rid="R1", ds="SYN1", effect="feed"):
    return {"rule_id": rid, "dataset_id": ds, "effect": effect, "test": "synthetic fixture test",
            "criterion": "any affected observation", "resulting_state": INV.C0_EFFECTS[effect],
            "handling": {str(i): f"handling {i}" for i in range(1, 6)},
            "test_impl_sha256": INV.impl_sha256(FIXTURES[effect])}


# ---------------- C0 synthetic fixture tests (NOT project rules) ----------------
def fx_feed(obs):          # duplicated feed timestamps
    seen, aff = set(), []
    for o in obs:
        if o["t_market"] in seen:
            aff.append(o["id"])
        seen.add(o["t_market"])
    return {"outcome": "detected" if aff else "not_detected", "affected_ids": aff}


def fx_processing(obs):    # prices snapped to a coarse grid by processing
    aff = [o["id"] for o in obs if abs(o["close"] * 2 - round(o["close"] * 2)) < 1e-9]
    return {"outcome": "detected" if len(aff) > len(obs) // 2 else "not_detected", "affected_ids": aff}


def fx_candle(obs):        # candle construction: high/low inconsistent with open/close
    aff = [o["id"] for o in obs if o["high"] < max(o["open"], o["close"]) or o["low"] > min(o["open"], o["close"])]
    return {"outcome": "detected" if aff else "not_detected", "affected_ids": aff}


FIXTURES = {"feed": fx_feed, "processing": fx_processing, "candle_or_order": fx_candle}


# ======================= layer 4: inventory ======================================================
def test_inventory_is_descriptive_and_hashed():
    inv = take_inventory("S", world(10), source="gen", data_class="synthetic")
    assert inv["n_observations"] == 10 and "close" in inv["fields"] and "t_market" not in inv["fields"]
    assert inv["has_arrival_time"] is False and inv["n_duplicate_t_market"] == 0
    assert inv == take_inventory("S", world(10), source="gen", data_class="synthetic")      # deterministic
    assert inv["content_sha256"] != take_inventory("S", world(10, seed=8), source="gen", data_class="synthetic")["content_sha256"]


def test_real_data_is_locked(env):
    with pytest.raises(GateError, match="OD-10"):
        take_inventory("G", world(5), source="broker", data_class="real")
    g, cl, cc, il, sl = env
    with pytest.raises(GateError, match="OD-10"):
        il.permit(F("permit_inventory", dataset_id="G", data_class="real"))


def test_no_inventory_without_permission_and_custody_only(env):
    g, cl, cc, il, sl = env
    with pytest.raises(GateError, match="م3-02"):
        il.record_inventory("SYN1", world(), source="gen")
    il.permit(F("permit_inventory", dataset_id="SYN1", data_class="synthetic"))
    with pytest.raises(GateError, match="not custody"):                                     # ق-10
        g._commit("inventory_recorded", C("inventory_recorded", key=DK, who="disc",
                                          inventory=take_inventory("SYN1", world(), source="g", data_class="synthetic")).to_payload())
    with pytest.raises((GateError, AuthError)):                                              # permission is founder's
        il.permit(C("permit_inventory", dataset_id="X", data_class="synthetic"))
    il.record_inventory("SYN1", world(), source="gen")
    with pytest.raises(GateError, match="already"):
        il.record_inventory("SYN1", world(), source="gen")


# ======================= layer 4: transforms (TP-03 a, d; TP-61.02) ==============================
def test_transform_used_only_after_freezing(env):
    inventoried(env)
    g, cl, cc, il, sl = env
    with pytest.raises(GateError, match="frozen"):
        il.apply_transform("T1", tf_mid, world(3))
    il.freeze_transform("T1", "SYN1", kind="deterministic", spec="mid=(bid+ask)/2", outputs=["mid"], params={}, impl=tf_mid)
    out = il.apply_transform("T1", tf_mid, world(3))
    assert out[0]["mid"] == pytest.approx(world(3)[0]["close"])
    rec = il.applied[-1]
    assert rec["input_sha256"] == INV.content_sha256(world(3)) and rec["output_sha256"] == INV.content_sha256(out)


def test_estimated_transform_only_from_discovery(env):
    planned(env)
    g, cl, cc, il, sl = env
    with pytest.raises(GateError, match="WITHOUT parameters"):
        il.freeze_transform("E0", "SYN1", kind="estimated", spec="vol scale", outputs=["z"], params={"s": 1}, impl=tf_scale)
    il.freeze_transform("E1", "SYN1", kind="estimated", spec="vol scale", outputs=["z"], impl=tf_scale)
    with pytest.raises(GateError, match="no Discovery estimate"):
        il.apply_transform("E1", tf_scale, world(3))
    for bad in ("V1", "X1", "nope"):
        with pytest.raises(GateError, match="Discovery only"):
            il.record_estimate("E1", estimated_from_slice=bad, params={"s": 0.3})
    il.record_estimate("E1", estimated_from_slice="D1", params={"s": 0.3})
    assert il.apply_transform("E1", tf_scale, world(3)) == [0.3]


def test_session_calendar_needs_three_elements(env):
    inventoried(env)
    g, cl, cc, il, sl = env
    cal = {"trading_time": "synthetic: all day", "open_event": "synthetic: t=0"}
    with pytest.raises(GateError, match="scheduled_close_vs_outage"):
        il.freeze_transform("CAL", "SYN1", kind="deterministic", spec="calendar", outputs=["session"], params={}, impl=tf_identity,
                            role="session_calendar", calendar=cal)
    cal["scheduled_close_vs_outage"] = "synthetic: gap > 3600 s with no schedule = outage"
    il.freeze_transform("CAL", "SYN1", kind="deterministic", spec="calendar", outputs=["session"], params={}, impl=tf_identity,
                        role="session_calendar", calendar=cal)


def test_deterministic_transforms_before_blinding(env):
    planned(env)
    g, cl, cc, il, sl = env
    il.freeze_transform("T1", "SYN1", kind="deterministic", spec="mid", outputs=["mid"], params={}, impl=tf_mid)
    com = cl.vault.set_params("F1", c=1.5, a=2.0, b=-3.0, m=7.0)
    cl.commit("params_fixed", C("params_fixed", family="F1", params_commitment=com, delta=0.01))
    cl.commit("custody_decision", C("custody_decision", slice="D1", family="F1", delta=0.01, params_commitment=com,
                                    boundaries=SL.SlicingLayer.boundaries_text(sl.slices["D1"])))
    with pytest.raises(GateError, match="before blinding"):                                 # §13 #14
        il.freeze_transform("T2", "SYN1", kind="deterministic", spec="late", outputs=["x"], params={}, impl=tf_identity)


def test_spec_hash_and_tamper(env):
    inventoried(env)
    g, cl, cc, il, sl = env
    st = C("transform_frozen", transform_id="T9", dataset_id="SYN1", kind="deterministic", spec="a",
           spec_sha256="0" * 64, outputs=["x"], params={}, impl_sha256=INV.impl_sha256(tf_identity))
    with pytest.raises(GateError, match="hash"):
        g._commit("transform_frozen", st.to_payload())


# ======================= layer 4: C0 (TP-03 b, c; TP-47) ========================================
def test_c0_rule_founder_creates_custody_records(env):
    inventoried(env)
    g, cl, cc, il, sl = env
    with pytest.raises(GateError, match="founder"):                                         # ق-11
        il.record_c0_rule(C("c0_rule_approve", rule=rule()))
    with pytest.raises(GateError, match="not custody"):
        g._commit("c0_rule_recorded", C("c0_rule_recorded", key=DK, who="disc",
                                        approval=F("c0_rule_approve", rule=rule()).to_payload(),
                                        rule_sha256=INV.content_sha256(rule())).to_payload())
    ap = F("c0_rule_approve", rule=rule())
    il.record_c0_rule(ap)
    with pytest.raises((GateError, AuthError)):                                              # replay
        il.record_c0_rule(ap)


@pytest.mark.parametrize("missing", INV.C0_TEMPLATE)
def test_c0_rule_missing_template_field_refused(env, missing):
    inventoried(env)
    g, cl, cc, il, sl = env
    r = rule(); r.pop(missing)
    with pytest.raises(GateError):
        il.record_c0_rule(F("c0_rule_approve", rule=r))


def test_c0_rule_handling_for_all_five_and_matching_state(env):
    inventoried(env)
    g, cl, cc, il, sl = env
    r = rule(); r["handling"].pop("5")
    with pytest.raises(GateError, match="five states"):
        il.record_c0_rule(F("c0_rule_approve", rule=r))
    r = rule(); r["resulting_state"] = 2
    with pytest.raises(GateError, match="examined effect"):
        il.record_c0_rule(F("c0_rule_approve", rule=r))


@pytest.mark.parametrize("effect", list(INV.C0_EFFECTS))
def test_tp47_planted_effects_and_clean_world(env, effect):
    inventoried(env)
    g, cl, cc, il, sl = env
    il.record_c0_rule(F("c0_rule_approve", rule=rule(f"R-{effect}", effect=effect)))
    clean = world(60)
    planted = [dict(o) for o in clean]
    if effect == "feed":
        planted[10]["t_market"] = planted[9]["t_market"]
    elif effect == "processing":
        for o in planted:
            o["close"] = round(o["close"] * 2) / 2
    else:
        planted[5]["high"] = min(planted[5]["open"], planted[5]["close"]) - 0.5
    r = il.c0_rules[f"R-{effect}"]
    res = INV.run_c0(r, FIXTURES[effect], planted)
    assert res["state"] == INV.C0_EFFECTS[effect] and res["scope_lineage"]
    il.record_c0_result(f"R-{effect}", res, time="2026-11-16T00:00:00Z")
    assert il.c0_state(f"R-{effect}") == INV.C0_EFFECTS[effect]
    res = INV.run_c0(r, FIXTURES[effect], clean)
    assert res["state"] == 4                                                                # TP-47 negative
    il.record_c0_result(f"R-{effect}", res, time="2026-11-16T00:00:01Z")
    assert il.c0_state(f"R-{effect}") == 4


def test_c0_result_constraints(env):
    inventoried(env)
    g, cl, cc, il, sl = env
    il.record_c0_rule(F("c0_rule_approve", rule=rule()))
    h = INV.impl_sha256(fx_feed)
    good = {"state": 1, "scope_lineage": ["o3"], "evidence_sha256": "a" * 64, "handling": "handling 1",
            "test_impl_sha256": h}
    for bad, msg in (({**good, "state": 6}, "five"), ({**good, "state": 2, "handling": "handling 2"}, "another effect"),
                     ({**good, "scope_lineage": []}, "lineage"), ({**good, "handling": "other"}, "handling"),
                     ({**good, "market_phenomenon": "trend"}, "market phenomenon"),
                     ({**good, "test_impl_sha256": INV.impl_sha256(fx_candle)}, "another test implementation")):
        with pytest.raises(GateError, match=msg):
            il.record_c0_result("R1", bad, time="t")
    il.record_c0_result("R1", good, time="t")
    il.record_c0_result("R1", {"state": 5, "scope_lineage": [], "evidence_sha256": "b" * 64, "handling": "handling 5",
                               "test_impl_sha256": h}, time="t")


def test_c0_rule_before_opening(env):
    planned(env)
    g, cl, cc, il, sl = env
    il.record_c0_rule(F("c0_rule_approve", rule=rule("R1")))
    open_claim(env, "K1", "D1")
    with pytest.raises(GateError, match="before opening"):
        il.record_c0_rule(F("c0_rule_approve", rule=rule("R2")))


# ======================= capability table (س 415–425) ==========================================
def test_capabilities_cumulative():
    f = take_inventory("S", world(5), source="g", data_class="synthetic")["fields"]
    assert INV.capabilities(f) == ["ohlc", "bid_ask"]
    INV.require_capability("bid_ask", f)
    with pytest.raises(INV.CapabilityError, match="tick"):
        INV.require_capability("ticks", f)
    with pytest.raises(INV.CapabilityError, match="open"):
        INV.require_capability("bid_ask", ["bid", "ask"])                                   # cumulative reading


def test_fields_available_include_frozen_deterministic_outputs(env):
    inventoried(env)
    g, cl, cc, il, sl = env
    assert "tick" not in il.fields_available("SYN1")
    il.freeze_transform("TK", "SYN1", kind="deterministic", spec="tick marker", outputs=["tick"], params={}, impl=tf_identity)
    assert "ticks" in INV.capabilities(il.fields_available("SYN1"))


# ======================= layer 5: slice plan ====================================================
def test_slice_plan_rules(env):
    inventoried(env)
    g, cl, cc, il, sl = env
    with pytest.raises(GateError, match="carry no results"):
        sl.freeze_plan(il, "P0", "SYN1", basis="outcome_balance", slices=SLICES)
    with pytest.raises(GateError, match="data"):
        sl.freeze_plan(il, "P0", "SYN1", basis="calendar_time", slices=[])
    with pytest.raises(GateError, match="CS-03-05"):
        sl.freeze_plan(il, "P0", "SYN1", basis="calendar_time",
                       slices=[{"slice_id": "F", "station": "Forward", "start": 0.0, "end": 10.0}])
    with pytest.raises(GateError, match="overlap"):
        sl.freeze_plan(il, "P0", "SYN1", basis="calendar_time",
                       slices=[{**SLICES[0]}, {**SLICES[1], "start": 3000.0}])
    with pytest.raises(GateError, match="outside"):
        sl.freeze_plan(il, "P0", "SYN1", basis="calendar_time", slices=[{**SLICES[2], "end": 1e9}])
    with pytest.raises(GateError, match="inventory"):
        sl.freeze_plan(il, "P0", "NOPE", basis="calendar_time", slices=SLICES)
    sl.freeze_plan(il, "P1", "SYN1", basis="calendar_time", slices=SLICES)
    with pytest.raises(GateError, match="already"):
        sl.freeze_plan(il, "P2", "SYN1", basis="calendar_time", slices=SLICES)
    assert sl.slice_station("V1") == "Validation" and sl.slice_dataset("X1") == "SYN1"


def test_custody_decision_needs_plan_and_matching_boundaries(env):
    planned(env)
    g, cl, cc, il, sl = env
    com = cl.vault.set_params("F1", c=1.5, a=2.0, b=-3.0, m=7.0)
    cl.commit("params_fixed", C("params_fixed", family="F1", params_commitment=com, delta=0.01))
    with pytest.raises(GateError, match="frozen slice plan"):
        cl.commit("custody_decision", C("custody_decision", slice="ZZ", family="F1", delta=0.01,
                                        params_commitment=com, boundaries="x"))
    with pytest.raises(GateError, match="equal"):
        cl.commit("custody_decision", C("custody_decision", slice="D1", family="F1", delta=0.01,
                                        params_commitment=com, boundaries="0..4000"))


# ======================= layer 5: split design per claim (TP-10 a, c, d) ========================
def card(cid):
    return {"claim_id": cid, "version": 1, "tags": ["الموقع"], "category": None, "path": "أ",
            "uses_events": False, "scope_type": "stable", "scope": "s", "rulings": {"existence": "e", "size_with_uncertainty": "s", "importance": "i"}}


def decide(env, slice_id):
    g, cl, cc, il, sl = env
    if slice_id in cl.decisions:
        return
    if "F1" not in cl.families:
        com = cl.vault.set_params("F1", c=1.5, a=2.0, b=-3.0, m=7.0)
        cl.commit("params_fixed", C("params_fixed", family="F1", params_commitment=com, delta=0.01))
    cl.commit("custody_decision", C("custody_decision", slice=slice_id, family="F1", delta=0.01,
                                    params_commitment=cl.families["F1"]["commitment"],
                                    boundaries=SL.SlicingLayer.boundaries_text(sl.slices[slice_id])))


def open_claim(env, cid, slice_id, design="A", rules=None):
    g, cl, cc, il, sl = env
    decide(env, slice_id)
    cc.register(F("register_claim", card=card(cid)))
    sl.record_design(F("record_split_design", claim_id=cid, design=design, rules=rules or {}))
    if slice_id not in g._s.slices:
        g.consume_slice(slice_id)
    cc.open_on_slice(cid, slice_id)


def test_design_recorded_before_opening(env):
    planned(env)
    g, cl, cc, il, sl = env
    cc.register(F("register_claim", card=card("K1")))
    decide(env, "D1")
    g.consume_slice("D1")
    with pytest.raises(GateError, match="before opening"):                                # TP-10 (a)
        cc.open_on_slice("K1", "D1")
    sl.record_design(F("record_split_design", claim_id="K1", design="A", rules={}))
    cc.open_on_slice("K1", "D1")
    with pytest.raises(GateError, match="already"):
        sl.record_design(F("record_split_design", claim_id="K1", design="B", rules={"embargo": 1.0}))


@pytest.mark.parametrize("station_slice", ["V1", "X1"])
def test_design_c_never_in_validation_or_final(env, station_slice):                   # TP-10 (c)
    planned(env)
    with pytest.raises(GateError, match="not allowed"):
        open_claim(env, "K1", station_slice, design="C")


def test_final_uses_design_a_only(env):
    planned(env)
    with pytest.raises(GateError, match="not allowed"):
        open_claim(env, "K1", "X1", design="B", rules={"embargo": 60.0})
    open_claim(env, "K2", "X1", design="A")


def test_design_rules(env):
    planned(env)
    g, cl, cc, il, sl = env
    cc.register(F("register_claim", card=card("K1")))
    with pytest.raises(GateError, match="embargo"):
        sl.record_design(F("record_split_design", claim_id="K1", design="B", rules={}))
    with pytest.raises(GateError, match="combination"):
        sl.record_design(F("record_split_design", claim_id="K1", design="A", rules={"combination": {"reason": "x"}}))
    with pytest.raises(GateError, match="كمون مفترض"):                                    # TP-10 (d)
        sl.record_design(F("record_split_design", claim_id="K1", design="A", rules={},
                           latency={"assumed": True, "per_source": {"S1": 0.2},
                                    "sensitivity_dimensions": list(SL.LATENCY_DIMENSIONS)}))
    with pytest.raises(GateError, match="four dimensions"):
        sl.record_design(F("record_split_design", claim_id="K1", design="A", rules={},
                           latency={"assumed": True, "tag": SL.ASSUMED_LATENCY_TAG, "per_source": {"S1": 0.2},
                                    "sensitivity_dimensions": ["between_sources"]}))
    with pytest.raises((GateError, AuthError)):
        sl.record_design(C("record_split_design", claim_id="K1", design="A", rules={}))
    sl.record_design(F("record_split_design", claim_id="K1", design="A", rules={},
                       latency={"assumed": True, "tag": SL.ASSUMED_LATENCY_TAG, "per_source": {"S1": 0.2},
                                "sensitivity_dimensions": list(SL.LATENCY_DIMENSIONS)}))


# ======================= availability time and leakage (TP-10 b) ================================
def test_availability_time():
    o = world(2)[1]
    with pytest.raises(GateError, match="declared latency"):
        SL.availability_time(o)
    assert SL.availability_time(o, {"S1": 0.25}) == (o["t_market"] + 0.25, True)
    oa = world(2, arrival=True)[1]
    assert SL.availability_time(oa) == (oa["t_arrival"], False)


def test_no_information_unavailable_at_decision():
    obs = world(5)
    t_dec, assumed = SL.availability_time(obs[3], {"S1": 0.5})
    SL.assert_no_leak(t_dec, [SL.availability_time(o, {"S1": 0.5})[0] for o in obs[:4]])
    with pytest.raises(SL.LeakError):                                                       # market time earlier, not yet arrived
        SL.assert_no_leak(obs[3]["t_market"], [SL.availability_time(o, {"S1": 0.5})[0] for o in obs[:4]])


# ======================= purge / embargo ========================================================
def samples(n=40, L=3.0, H=2.0, groups=None):
    return [Sample(f"s{i}", float(i), L, float(i) + H, (groups or {}).get(i)) for i in range(n)]


def test_design_a_forward():
    S = samples()
    ev = [f"s{i}" for i in range(30, 40)]
    r = split(S, ev, "A")
    assert all(int(x[1:]) <= 27 for x in r["train"])                    # τ_j = j+2 < 30
    assert r["removed"]["s28"].startswith("unresolved") and r["removed"]["s29"].startswith("unresolved")
    assert audit_split(S, r) == []
    assert r["steps"][:3] == ["1:overlap_check", "2:purge_overlaps", "3:embargo"]


def test_design_b_blocks_purge_and_embargo():
    S = samples()
    ev = [f"s{i}" for i in range(15, 20)]                                 # block [15, 21]
    r = split(S, ev, "B", embargo=3.0)
    rm = r["removed"]
    assert "s13" in rm and "s14" in rm and "s12" not in rm             # O_13=[13,15] overlaps; O_12=[12,14] does not
    assert "s21" in rm and "s24" in rm                                   # I_j reads outcome (s21..s23) / embargo (s24)
    assert "s25" not in rm and "s11" not in rm                           # dependence is not deleted (س 479)
    assert audit_split(S, r) == []


def test_shared_group_kept_in_one_partition():
    S = samples(groups={2: "zone", 33: "zone"})
    r = split(S, [f"s{i}" for i in range(30, 40)], "A")
    assert "s2" in r["removed"] and "shared_group" in r["removed"]["s2"]
    assert audit_split(S, r) == []


def test_combination_rule_only_design_b_with_reason():
    S = samples()
    with pytest.raises(GateError):
        split(S, ["s30"], "A", combination={"reason": "x"})
    with pytest.raises(GateError):
        split(S, ["s30"], "B", combination={"reason": " "})
    r = split(S, [f"s{i}" for i in range(15, 20)], "B", combination={"reason": "exact intervals unavailable"})
    assert "s10" in r["removed"] and "combination_rule" in r["removed"]["s10"]


def test_design_c_descriptive_only():
    r = split(samples(), ["s20"], "C")
    assert r["descriptive_only"] is True


def test_tp28_planted_insufficient_purge_is_detected():
    S = samples()
    r = split(S, [f"s{i}" for i in range(30, 40)], "A")
    bad = {**r, "train": r["train"] + ["s29"]}                            # purge planted as insufficient
    v = audit_split(S, bad)
    assert v and "s29" in v[0]
    rb = split(S, [f"s{i}" for i in range(15, 20)], "B")
    assert audit_split(S, {**rb, "train": rb["train"] + ["s14"]})


def test_invalid_samples_refused():
    with pytest.raises(GateError):
        Sample("x", 5.0, 1.0, 4.0)
    with pytest.raises(GateError):
        split(samples(5), [], "A")


# ======================= replay / restart ========================================================
def test_full_history_replays(tmp_path):
    led = tmp_path / "led" / "g.jsonl"; led.parent.mkdir()
    anc = tmp_path / "anc" / "a.jsonl"; anc.parent.mkdir()
    env1 = build(Ledger(led, anchors=AnchorStore(anc)))
    planned(env1)
    g, cl, cc, il, sl = env1
    il.freeze_transform("T1", "SYN1", kind="deterministic", spec="mid", outputs=["mid"], params={}, impl=tf_mid)
    il.record_c0_rule(F("c0_rule_approve", rule=rule()))
    open_claim(env1, "K1", "D1")
    cl2, il2, sl2 = CustodyLayer(None), InventoryLayer(), SlicingLayer()
    g2 = Governance(FK.public_key(), Ledger(led, anchors=AnchorStore(anc)), extensions=[ClaimsCharter(), cl2, il2, sl2])
    assert il2.inventories == il.inventories and sl2.slices == sl.slices and il2.c0_rules == il.c0_rules
    assert set(sl2.designs) == {"K1"}


# ======================= review round R1 (ChatGPT, 2026-11-17) ==================================
@pytest.mark.parametrize("bad", [float("nan"), float("inf"), True, "5", None])
def test_r1_01_arrival_time_must_be_finite_number(bad):
    o = {**world(2)[1], "t_arrival": bad}
    with pytest.raises(GateError, match="t_arrival"):
        take_inventory("S", [world(2)[0], o], source="g", data_class="synthetic")
    with pytest.raises(GateError, match="t_arrival"):
        SL.availability_time(o)


def test_r1_01_arrival_before_market_refused():
    o = {**world(2)[1], "t_arrival": world(2)[1]["t_market"] - 1}
    with pytest.raises(GateError, match="precedes"):
        SL.availability_time(o)
    with pytest.raises(GateError, match="precedes"):
        take_inventory("S", [o], source="g", data_class="synthetic")
    with pytest.raises(GateError, match="t_market"):
        SL.availability_time({"t_market": float("nan"), "source": "S1"}, {"S1": 0.1})


def test_r1_02_audit_detects_embargo_and_combination_and_param_mismatch():
    S = samples()
    ev = [f"s{i}" for i in range(15, 20)]
    rec = {"design": "B", "rules": {"embargo": 3.0}}
    r = split(S, ev, "B", embargo=3.0)
    assert audit_split(S, r, rec) == []
    v = audit_split(S, {**r, "train": r["train"] + ["s24"]}, rec)              # planted short embargo
    assert any("embargo" in x for x in v)
    r_short = split(S, ev, "B", embargo=1.0)                                    # params differ from record
    assert any("differ from the recorded" in x for x in audit_split(S, r_short, rec))
    rec_c = {"design": "B", "rules": {"embargo": 0.0, "combination": {"reason": "no exact intervals"}}}
    rc = split(S, ev, "B", combination={"reason": "no exact intervals"})
    assert audit_split(S, rc, rec_c) == []
    v = audit_split(S, {**rc, "train": rc["train"] + ["s10"]}, rec_c)          # combination dropped for s10
    assert any("combination" in x for x in v)
    rn = split(S, ev, "B")                                                      # combination disabled entirely
    assert any("differ from the recorded" in x for x in audit_split(S, rn, rec_c))
    tampered = {**r, "params": {**r["params"], "embargo": 0.0}}                 # params edited after the split
    assert any("hash" in x for x in audit_split(S, tampered, rec))


def test_r1_02_audit_other_checks():
    S = samples()
    r = split(S, ["s30"], "A")
    assert any("both" in x for x in audit_split(S, {**r, "train": r["train"] + ["s30"]}))
    with pytest.raises(GateError, match="embargo"):
        split(S, ["s30"], "A", embargo=2.0)
    with pytest.raises(GateError, match="unknown"):
        split(S, ["nope"], "A")
    assert audit_split(S, r, {"design": "A", "rules": {}}) == []


def test_r1_03_transform_runs_only_the_frozen_implementation(env):
    import hashlib
    inventoried(env)
    g, cl, cc, il, sl = env
    il.freeze_transform("T1", "SYN1", kind="deterministic", spec="mid", outputs=["mid"], params={}, impl=tf_mid)
    with pytest.raises(GateError, match="not the frozen one"):
        il.apply_transform("T1", tf_identity, world(3))
    with pytest.raises(GateError, match="lambda"):
        il.apply_transform("T1", lambda o, p: o, world(3))
    with pytest.raises(GateError, match="another implementation"):              # forged record
        g._commit("transform_applied", C("transform_applied", transform_id="T1",
                  spec_sha256=il.transforms["T1"]["spec_sha256"], impl_sha256=INV.impl_sha256(tf_identity),
                  input_sha256="a" * 64, output_sha256="b" * 64).to_payload())
    il.apply_transform("T1", tf_mid, world(3))
    assert il.applied[-1]["impl_sha256"] == INV.impl_sha256(tf_mid)
    with pytest.raises(GateError, match="implementation hash"):
        g._commit("transform_frozen", C("transform_frozen", transform_id="T2", dataset_id="SYN1", kind="deterministic",
                  spec="a", spec_sha256=hashlib.sha256(b"a").hexdigest(), outputs=["x"], params={}).to_payload())


def test_r1_04_c0_result_bound_to_approved_test(env):
    inventoried(env)
    g, cl, cc, il, sl = env
    r = rule(); r.pop("test_impl_sha256")
    with pytest.raises(GateError, match="approved test implementation"):
        il.record_c0_rule(F("c0_rule_approve", rule=r))
    il.record_c0_rule(F("c0_rule_approve", rule=rule()))
    with pytest.raises(GateError, match="not the one the founder approved"):
        INV.run_c0(il.c0_rules["R1"], fx_candle, world(10))
    res = INV.run_c0(il.c0_rules["R1"], fx_feed, world(10))
    assert res["test_impl_sha256"] == INV.impl_sha256(fx_feed)
    il.record_c0_result("R1", res, time="t")


def test_r1_05_observation_count_bounds_are_integers(env):
    inventoried(env)
    g, cl, cc, il, sl = env
    with pytest.raises(GateError, match="whole numbers"):
        sl.freeze_plan(il, "P0", "SYN1", basis="observation_count",
                       slices=[{"slice_id": "A", "station": "Discovery", "start": 10.5, "end": 20.5}])
    sl.freeze_plan(il, "P1", "SYN1", basis="observation_count",
                   slices=[{"slice_id": "A", "station": "Discovery", "start": 0, "end": 100},
                           {"slice_id": "B", "station": "Validation", "start": 100, "end": 200}])


# ======================= review round R2 (ChatGPT, 2026-11-17) ==================================
def test_r2_01_audit_checks_completeness_and_uniqueness():
    S = samples()
    ev = [f"s{i}" for i in range(15, 20)]
    rec = {"design": "B", "rules": {"embargo": 3.0}}
    r = split(S, ev, "B", embargo=3.0)
    assert audit_split(S, r, rec) == []
    dropped = {**r, "train": [x for x in r["train"] if x != "s5"]}                 # eligible sample silently dropped
    assert any("missing from the split" in x and "s5" in x for x in audit_split(S, dropped, rec))
    hidden = {**r, "train": [x for x in r["train"] if x != "s5"], "removed": {**r["removed"], "s5": "made up"}}
    assert any("no rule removes" in x and "s5" in x for x in audit_split(S, hidden, rec))
    dup_tr = {**r, "train": r["train"] + ["s5"]}
    assert any("duplicate ids in training" in x for x in audit_split(S, dup_tr, rec))
    dup_ev = {**r, "eval": r["eval"] + ["s15"]}
    assert any("duplicate ids in evaluation" in x for x in audit_split(S, dup_ev, rec))
    both = {**r, "removed": {**r["removed"], "s5": "x"}}                            # in training and removed
    assert any("training and removed" in x for x in audit_split(S, both, rec))
    ra = split(S, [f"s{i}" for i in range(30, 40)], "A")
    assert audit_split(S, ra, {"design": "A", "rules": {}}) == []
    assert audit_split(S, split(S, ["s20"], "C"), {"design": "C", "rules": {}}) == []


def test_s2_01_removed_needs_a_reason():
    S = samples()
    r = split(S, ["s30"], "A")
    k = next(iter(r["removed"]))
    assert any("without a stated reason" in x for x in audit_split(S, {**r, "removed": {**r["removed"], k: " "}}))
