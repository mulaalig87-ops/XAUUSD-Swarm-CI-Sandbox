"""Layer 6 tests (WP8-06): gates, separation conditions, adequacy report, Final consumption.
SYNTHETIC DATA ONLY (Register §34). Test-plan items: TP-04 (station separation), TP-05 (a)–(d),
TP-60.13 (Discovery/Validation data into the adequacy report refused), and §8.2 items 1–6.
"""
import json
import random
import uuid

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from xauusd_swarm.charter import GateError, Governance
from xauusd_swarm.claims import ClaimsCharter
from xauusd_swarm.court import CourtLayer
from xauusd_swarm.custody import CustodyLayer, Vault
from xauusd_swarm.evidence import EvidenceLayer
from xauusd_swarm.identity import AuthError, public_hex, sign
from xauusd_swarm.inventory import InventoryLayer
from xauusd_swarm.ledger import AnchorStore, Ledger
from xauusd_swarm.slicing import SlicingLayer

FK, CK, AK, OK, DK = (Ed25519PrivateKey.generate() for _ in range(5))


def F(action, **kw):
    return sign("founder", FK, {"action": action, "nonce": uuid.uuid4().hex, **kw})


def C(action, **kw):
    return sign("cust", CK, {"action": action, "nonce": uuid.uuid4().hex, **kw})


def world(n=200, seed=3):
    rnd, p, out = random.Random(seed), 100.0, []
    for i in range(n):
        c = p + rnd.gauss(0, 0.3)
        out.append({"id": f"o{i}", "t_market": 60.0 * i, "bid": round(c - 0.02, 5), "ask": round(c + 0.02, 5),
                    "source": "S1"})
        p = c
    return out


SLICES = [{"slice_id": "D1", "station": "Discovery", "start": 0.0, "end": 4000.0},
          {"slice_id": "V1", "station": "Validation", "start": 4000.0, "end": 8000.0},
          {"slice_id": "X1", "station": "Final", "start": 8000.0, "end": 9500.0},
          {"slice_id": "X2", "station": "Final", "start": 9500.0, "end": 10500.0},
          {"slice_id": "X3", "station": "Final", "start": 10500.0, "end": 11940.0}]
CONFIG = {"structure": "A", "alpha_total": 0.05, "error_measure": "FWER", "procedure": "holm",
          "validity_reason": "Holm controls FWER under any dependence (س 681)"}


class Env:
    def __init__(self, ledger=None):
        self.cl = CustodyLayer(Vault(), identity="cust", key=CK)
        self.cc, self.il, self.sl = ClaimsCharter(), InventoryLayer(identity="cust", key=CK), SlicingLayer()
        self.ct, self.ev = CourtLayer(), EvidenceLayer()
        self.g = Governance(FK.public_key(), ledger if ledger is not None else Ledger(),
                            extensions=[self.cc, self.cl, self.il, self.sl, self.ct, self.ev])
        g = self.g
        for ident, k in (("cust", CK), ("aud", AK), ("op", OK), ("disc", DK)):
            g.register_key(F("register_key", identity=ident, public_key_hex=public_hex(k.public_key())))
        for role, h in (("custody", "cust"), ("custody_auditor", "aud"), ("court_operator", "op"),
                        ("discovery_participant", "disc")):
            self.cl.commit("role_assigned", F("assign_role", role=role, holder=h))
        g.set_initial_charter(F("charter_initial", charter="project", text="P"))
        g.set_initial_charter(F("charter_initial", charter="claims", text="C"))
        self.il.permit(F("permit_inventory", dataset_id="SYN", data_class="synthetic"))
        self.il.record_inventory("SYN", world(), source="gen")
        self.sl.freeze_plan(self.il, "P1", "SYN", basis="calendar_time", slices=SLICES)
        com = self.cl.vault.set_params("F1", c=1.5, a=2.0, b=-3.0, m=7.0)
        self.cl.commit("params_fixed", C("params_fixed", family="F1", params_commitment=com, delta=0.01))
        self.ct.commit("court_policy_decided", F("decide_court_policy", family="F1", structure="A", error_measure="FWER",
                                                 register_ref="synthetic", register_sha256="ab" * 32))
        self.ct.commit("court_frozen", F("freeze_court", family="F1", config=CONFIG))

    def decide(self, s):
        if s not in self.cl.decisions:
            self.cl.commit("custody_decision", C("custody_decision", slice=s, family="F1", delta=0.01,
                                                 params_commitment=self.cl.families["F1"]["commitment"],
                                                 boundaries=SlicingLayer.boundaries_text(self.sl.slices[s])))

    def claim(self, cid, q=None, design="A", screen="D1", tis=None):
        """tis: test instances [(tid, slice, path)] registered BEFORE the first opening: the court
        treats any instance registered after the claim was opened as descriptive (س 700, 703)."""
        self.cc.register(F("register_claim", card={"claim_id": cid, "version": 1, "tags": ["الموقع"], "category": None,
                                                   "path": "أ", "uses_events": False, "scope_type": "stable", "scope": "s",
                                                   "rulings": {"existence": "e", "size_with_uncertainty": "s",
                                                               "importance": "i"}}))
        self.ct.commit("claim_identity_registered", F("register_claim_identity", claim_id=cid, identity={
            "target_quantity": q or f"q-{cid}", "eligible_data_scope": "synthetic", "time_scope_type": "stable",
            "proof_path": "أ", "direction_or_threshold": ">0", "observation_precision": "n/a", "price_series": "Mid"}))
        self.sl.record_design(F("record_split_design", claim_id=cid, design=design,
                                rules={"embargo": 0.0} if design == "B" else {}))
        for tid, s, path in (tis if tis is not None else [(f"T-{cid}", "X1", "Z")]):
            self.ti(tid, cid, s=s, path=path)
        if screen:
            self.open(cid, screen)

    def open(self, cid, s):
        self.decide(s)
        if s not in self.g._s.slices:
            self.g.consume_slice(s)
        self.cc.open_on_slice(cid, s)

    def ti(self, tid, cid, s="X1", path="Z", role="primary"):
        self.decide(s)
        self.ct.commit("test_instance_registered", F("register_test_instance", test_instance_id=tid, claim_id=cid,
                       statistic="mean", procedure="t", null="N0", slice=s, seeds="1", code_version="v1",
                       representation_id="log_returns", transform_version="t1", price_series="Mid", path=path,
                       role=role, null_card_accepted=True))

    def submit(self, uid="U1", slices=("X1",), claims=(("K1", "Z", ("D1",)),), **kw):
        entries = []
        for c in claims:
            e = {"claim_id": c[0], "path": c[1], "screening_slices": list(c[2])}
            if len(c) > 3:
                e["branch_of"] = c[3]
            entries.append(e)
        for s in slices:
            self.decide(s)
        return self.ev.commit("confirmation_submitted", F("submit_for_confirmation", unit_id=uid, unit_slices=list(slices),
                                                          family="F1", claims=entries, **kw))

    def report(self, uid="U1", **over):
        sub = self.ev.submissions[uid]
        reg = {c: sum(1 for t in self.ct.instances.values() if t["claim_id"] == c) for c in sub["claim_ids"]}
        st = {"unit_id": uid, "source_slices": list(sub["unit_slices"]), "effective_units_after_purge": 120,
              "coverage": 0.9, "censoring_ratio": 0.1, "tie_ratio": 0.05, "tie_includes_ambiguous": True,
              "claims": list(sub["claim_ids"]), "test_instances_per_claim": reg, "detectable_effect": 0.2,
              "family_size": len(sub["claim_ids"]), "procedure": "holm", "alpha": 0.05, "exclusions": [],
              "verdict": "adequate", "time": "2026-11-17T00:00:00Z"}
        st.update(over)
        return self.ev.commit("adequacy_reported", C("adequacy_report", **st))

    def open_final(self, uid="U1"):
        for s in self.ev.submissions[uid]["unit_slices"]:
            if s not in self.g._s.slices:
                self.g.consume_slice(s)
        return self.ev.open_final(F("open_final", unit_id=uid, openings=self.ev.final_manifest(uid)))


@pytest.fixture
def env():
    e = Env()
    e.claim("K1")
    return e


# ======================= happy path =============================================================
def test_full_path_selection_to_final(env):
    env.submit()
    env.report()
    env.open_final()
    assert "U1" in env.ev.opened_units and ("K1", "X1") in env.cc.openings


# ======================= separation conditions (س 542–546) ======================================
def test_selection_only_from_discovery_or_validation(env):
    with pytest.raises(GateError, match="not Discovery or Validation"):
        env.submit(claims=(("K1", "Z", ("X2",)),))
    env.claim("K2", screen=None)
    with pytest.raises(GateError, match="not opened on screening"):
        env.submit(claims=(("K2", "Z", ("V1",)),))
    with pytest.raises(GateError, match="name the screening slices"):
        env.submit(claims=(("K1", "Z", ()),))


def test_confirmation_only_on_final(env):
    with pytest.raises(GateError, match="Final slices only"):
        env.submit(slices=("V1",))


def test_newer_data_and_embargo_is_not_independence(env):
    env.claim("K2", screen="V1")
    with pytest.raises(GateError, match="embargo"):
        env.submit(claims=(("K2", "Z", ("V1",)),), independence_basis="embargo")
    env.submit(claims=(("K2", "Z", ("V1",)),))                         # V1 ends 8000 = X1 start: newer


def test_full_freeze_required(env):
    env.claim("K2", screen="D1", tis=[])                                # no test instance on the unit
    with pytest.raises(GateError, match="primary test instance"):
        env.submit(claims=(("K2", "Z", ("D1",)),))
    env.claim("K4", screen="D1", tis=[("T4", "X1", "R")])
    with pytest.raises(GateError, match="primary test instance"):       # path differs from the instance's
        env.submit(claims=(("K4", "Z", ("D1",)),))
    env.claim("K5", screen="D1", tis=[])
    env.ti("T5", "K5")                                                  # registered AFTER opening: descriptive
    with pytest.raises(GateError, match="primary test instance"):
        env.submit(claims=(("K5", "Z", ("D1",)),))
    env.claim("K3", design="B", screen="D1")
    with pytest.raises(GateError, match="design A"):
        env.submit(claims=(("K3", "Z", ("D1",)),))
    with pytest.raises(GateError, match="path is Z, G-Z or R"):
        env.submit(claims=(("K1", "Q", ("D1",)),))


def test_submission_is_final_and_unit_exclusive(env):
    env.submit()
    with pytest.raises(GateError, match="one per unit"):
        env.submit()
    with pytest.raises(GateError, match="one confirmation unit only"):
        env.submit(uid="U2")


# ======================= adequacy report (TP-05, TP-60.13) ======================================
def test_report_rejects_discovery_or_validation_data(env):                         # TP-05 (a), TP-60.13
    env.submit()
    for bad in (["X1", "D1"], ["V1"]):
        with pytest.raises(GateError, match="Discovery or Validation"):
            env.report(source_slices=bad)


def test_report_exclusions_need_registered_rule_reason_count(env):                # TP-05 (b)
    env.submit()
    with pytest.raises(GateError, match="registered before"):
        env.report(exclusions=[{"rule_id": "EX1", "reason": "gap", "count": 3}])
    env.ev.commit("exclusion_rule_registered", F("register_exclusion_rule", rule_id="EX1", text="drop feed gaps > 1h"))
    with pytest.raises(GateError, match="reason and count"):
        env.report(exclusions=[{"rule_id": "EX1", "reason": "", "count": 3}])
    with pytest.raises(GateError, match="reason and count"):
        env.report(exclusions=[{"rule_id": "EX1", "reason": "gap", "count": 2.5}])
    env.report(exclusions=[{"rule_id": "EX1", "reason": "gap", "count": 3}])


def test_report_tie_includes_ambiguous_and_no_latent_item(env):                    # TP-05 (c), (d)
    env.submit()
    with pytest.raises(GateError, match="ambiguous"):
        env.report(tie_includes_ambiguous=False)
    with pytest.raises(GateError, match="latent"):
        env.report(latent_ratio=0.1)


def test_report_no_reduction_and_family_includes_all(env):
    env.submit()
    with pytest.raises(GateError, match="no reduction"):
        env.report(alpha=0.10)
    with pytest.raises(GateError, match="family includes all"):
        env.report(claims=[], family_size=0)
    with pytest.raises(GateError, match="registered count"):
        env.report(test_instances_per_claim={"K1": 5})
    for k, v in (("coverage", 1.5), ("censoring_ratio", -0.1), ("effective_units_after_purge", float("nan"))):
        with pytest.raises(GateError):
            env.report(**{k: v})


def test_inadequacy_is_a_result(env):
    env.submit()
    env.report(verdict="inadequate")
    with pytest.raises(GateError, match="not redone"):
        env.report()
    with pytest.raises(GateError, match="adequate adequacy report"):
        env.open_final()


def test_report_only_by_custody(env):
    env.submit()
    st = {"unit_id": "U1"}
    with pytest.raises(GateError, match="not custody"):
        env.ev.commit("adequacy_reported", sign("disc", DK, {"action": "adequacy_report", "nonce": "n", **st}))


# ======================= Final consumption (س 550–556) ==========================================
def test_final_opened_once_all_claims_together_atomically(env):                     # review R1-01
    env.claim("K2", screen="V1")
    env.submit(claims=(("K1", "Z", ("D1",)), ("K2", "Z", ("V1",))))
    env.report()
    env.g.consume_slice("X1")
    with pytest.raises(GateError, match="never opened on Final by itself"):         # no first-claim exposure
        env.cc.open_on_slice("K1", "X1")
    assert not any(sl == "X1" for (_c, sl) in env.cc.openings)
    man = env.ev.final_manifest("U1")
    with pytest.raises(GateError, match="all claims of the batch"):                  # signed partial batch
        env.ev.open_final(F("open_final", unit_id="U1", openings=man[:1]))
    assert not any(sl == "X1" for (_c, sl) in env.cc.openings) and "U1" not in env.ev.opened_units
    env.ev.open_final(F("open_final", unit_id="U1", openings=env.ev.final_manifest("U1")))                                 # one entry opens both
    assert {("K1", "X1"), ("K2", "X1")} <= set(env.cc.openings) and "U1" in env.ev.opened_units
    with pytest.raises(GateError, match="once"):
        env.ev.open_final(F("open_final", unit_id="U1", openings=env.ev.final_manifest("U1")))


def test_final_opening_runs_every_layer_check(env):
    env.submit()
    env.report()
    with pytest.raises(GateError, match="slice_consumed"):                           # claims charter check inside
        env.ev.open_final(F("open_final", unit_id="U1", openings=env.ev.final_manifest("U1")))
    assert "U1" not in env.ev.opened_units


def test_no_claim_on_final_outside_the_gate(env):
    env.claim("K9", screen="D1")
    env.submit()
    env.report()
    env.decide("X1")
    env.g.consume_slice("X1")
    with pytest.raises(GateError, match="never opened on Final by itself"):
        env.cc.open_on_slice("K9", "X1")


def test_final_not_opened_before_report(env):
    env.submit()
    env.g.consume_slice("X1")
    with pytest.raises(GateError, match="adequate adequacy report"):
        env.ev.open_final(F("open_final", unit_id="U1", openings=env.ev.final_manifest("U1")))


def test_no_gradual_reveal_after_opening(env):
    env.claim("K2", screen="D1")
    env.submit()
    env.report()
    env.open_final()
    with pytest.raises(GateError, match="never opened on Final by itself"):
        env.cc.open_on_slice("K2", "X1")
    with pytest.raises(GateError, match="one per unit"):             # cannot be added to the batch afterwards
        env.submit(claims=(("K2", "Z", ("D1",)),))


def test_court_waits_for_final_opening(env):
    env.submit()
    env.report()
    req = sign("op", OK, {"action": "court_ruling", "nonce": uuid.uuid4().hex, "family": "F1"})
    with pytest.raises(GateError, match="only after Final is opened"):
        env.g._commit("court_ruling", req.to_payload())


def test_branch_tested_on_later_slice(env):
    env.submit()
    env.report()
    env.open_final()
    env.claim("K2", screen="V1", tis=[("T2", "X2", "Z")])
    with pytest.raises(GateError, match="not exposed"):
        env.submit(uid="U2", slices=("X2",), claims=(("K2", "Z", ("V1",), "K404"),))
    env.submit(uid="U2", slices=("X2",), claims=(("K2", "Z", ("V1",), "K1"),))


def test_branch_on_earlier_unit_refused():
    e = Env()
    e.claim("K1", tis=[("T1", "X2", "Z")])
    e.submit(uid="U2", slices=("X2",))
    e.report(uid="U2")
    e.open_final(uid="U2")
    e.claim("K2", screen="V1")
    with pytest.raises(GateError, match="LATER"):
        e.submit(uid="U1", slices=("X1",), claims=(("K2", "Z", ("V1",), "K1"),))


def test_exposed_slice_cannot_be_submitted(env):
    env.claim("K2", screen="D1", tis=[("T2", "X2", "Z")])
    env.decide("X2")
    env.g.consume_slice("X2")
    with pytest.raises(GateError, match="exposed"):
        env.submit(uid="U2", slices=("X2",), claims=(("K2", "Z", ("D1",)),))


# ======================= merges (س 574, 645) ===================================================
def test_merge_decided_before_opening(env):
    with pytest.raises(GateError, match="merge decided before"):
        env.submit(slices=("X1", "X2"))
    with pytest.raises(GateError, match="Final slices"):
        env.ev.commit("slices_merge_decided", F("decide_slice_merge", unit_id="U1", slices=["V1", "X1"]))
    env.ev.commit("slices_merge_decided", F("decide_slice_merge", unit_id="U1", slices=["X1", "X2"]))
    env.submit(slices=("X1", "X2"))
    env.report()
    env.open_final()


def test_no_merge_of_exposed_slices(env):
    env.decide("X2")
    env.g.consume_slice("X2")
    with pytest.raises(GateError, match="exposed"):
        env.ev.commit("slices_merge_decided", F("decide_slice_merge", unit_id="U9", slices=["X1", "X2"]))


def test_founder_only_decisions(env):
    with pytest.raises((GateError, AuthError)):
        env.ev.commit("confirmation_submitted", C("submit_for_confirmation", unit_id="U1", unit_slices=["X1"],
                                                  family="F1", claims=[]))
    with pytest.raises((GateError, AuthError)):
        env.ev.commit("exclusion_rule_registered", C("register_exclusion_rule", rule_id="E", text="t"))


# ======================= replay ================================================================
def test_history_replays(tmp_path):
    led = tmp_path / "led" / "g.jsonl"; led.parent.mkdir()
    anc = tmp_path / "anc" / "a.jsonl"; anc.parent.mkdir()
    e = Env(Ledger(led, anchors=AnchorStore(anc)))
    e.claim("K1")
    e.submit()
    e.report()
    e.open_final()
    ev2 = EvidenceLayer()
    Governance(FK.public_key(), Ledger(led, anchors=AnchorStore(anc)),
               extensions=[ClaimsCharter(), CustodyLayer(None), InventoryLayer(), SlicingLayer(), CourtLayer(), ev2])
    assert set(ev2.opened_units) == {"U1"} and ev2.reports["U1"]["verdict"] == "adequate"


# ======================= review round R2 (ChatGPT, 2026-11-17) ==================================
def test_r2_01_signature_binds_the_opening_manifest(env):
    from xauusd_swarm.claims import card_hash
    env.claim("K2", screen="D1", tis=[("T2", "X1", "Z")])       # the court allows ONE primary per claim and path
    env.ev.commit("slices_merge_decided", F("decide_slice_merge", unit_id="U1", slices=["X1", "X2"]))
    env.submit(slices=("X1", "X2"), claims=(("K1", "Z", ("D1",)), ("K2", "Z", ("D1",))))
    env.report()
    env.g.consume_slice("X1"); env.g.consume_slice("X2")
    good = F("open_final", unit_id="U1", openings=env.ev.final_manifest("U1"))
    n0 = len(env.g.ledger)
    # 1. valid founder signature, unsigned manifest appended outside it -> refused
    with pytest.raises(GateError, match="no unsigned fields"):
        env.g._commit("final_opened", {**good.to_payload(), "openings": env.ev.final_manifest("U1")})
    # 2. valid signature, statement altered (other eligible slice for K2) -> signature fails
    st = json.loads(good.statement)
    st["openings"][1]["slice"] = "X2"
    forged = {**good.to_payload(), "statement_hex": json.dumps(st, sort_keys=True, ensure_ascii=False,
                                                              separators=(",", ":")).encode().hex()}
    with pytest.raises((GateError, AuthError)):
        env.g._commit("final_opened", forged)
    # 3. founder signs a manifest with a wrong card binding -> refused by the claims charter check
    bad = env.ev.final_manifest("U1"); bad[0]["card_sha256"] = "0" * 64
    with pytest.raises(GateError, match="card version and hash"):
        env.ev.open_final(F("open_final", unit_id="U1", openings=bad))
    assert len(env.g.ledger) == n0 and not any(sl in ("X1", "X2") for (_c, sl) in env.cc.openings)
    # 4. founder signs a slice that is not the claim's primary-instance slice -> refused
    alt = env.ev.final_manifest("U1"); alt[1]["slice"] = "X2"
    with pytest.raises(GateError, match="pre-registered primary instance"):
        env.ev.open_final(F("open_final", unit_id="U1", openings=alt))
    assert len(env.g.ledger) == n0 and not any(sl in ("X1", "X2") for (_c, sl) in env.cc.openings)
    # 5. the signed manifest is exactly what is applied and kept in the ledger
    man = env.ev.final_manifest("U1")
    env.ev.open_final(F("open_final", unit_id="U1", openings=man))
    assert {("K1", "X1"), ("K2", "X1")} <= set(env.cc.openings)
    assert json.loads(bytes.fromhex(list(env.g.ledger)[-1].payload["statement_hex"]))["openings"] == man


# ======================= review round R3 (ChatGPT, 2026-11-17) ==================================
def test_r3_01_signed_manifest_version_or_claim_tampering_refused(env):
    env.claim("K2", screen="D1")
    env.claim("K3", screen="D1")                      # registered, opened on D1, NOT in the batch
    env.submit(claims=(("K1", "Z", ("D1",)), ("K2", "Z", ("D1",))))
    env.report()
    env.g.consume_slice("X1")
    n0 = len(env.g.ledger)
    cases = []
    m = env.ev.final_manifest("U1"); m[0]["version"] = m[0]["version"] + 1
    cases.append((m, "card version and hash"))                           # version bumped
    m = env.ev.final_manifest("U1"); m[0]["version"] = 0
    cases.append((m, "card version and hash"))                           # version lowered
    m = env.ev.final_manifest("U1"); m[1]["claim_id"] = "K3"
    cases.append((m, "all claims of the batch"))                         # claim swapped for one outside the batch
    m = env.ev.final_manifest("U1"); m[1]["claim_id"] = "K1"
    cases.append((m, "all claims of the batch"))                         # same claim twice
    m = env.ev.final_manifest("U1"); m[0]["claim_id"], m[1]["claim_id"] = "K2", "K1"
    cases.append((m, "card version and hash|pre-registered primary instance"))   # bindings crossed between claims
    for man, msg in cases:
        with pytest.raises(GateError, match=msg):
            env.ev.open_final(F("open_final", unit_id="U1", openings=man))
        assert len(env.g.ledger) == n0
        assert not any(sl == "X1" for (_c, sl) in env.cc.openings) and "U1" not in env.ev.opened_units
    env.ev.open_final(F("open_final", unit_id="U1", openings=env.ev.final_manifest("U1")))
    assert {("K1", "X1"), ("K2", "X1")} <= set(env.cc.openings) and ("K3", "X1") not in env.cc.openings
