"""Layer 8 tests (WP8-08): five stages, basic null and its validity, blind rediscovery, law drift.
SYNTHETIC ONLY. Test-plan items: TP-06 (a)–(c) (no confirmation without a null with a complete card;
status «لم يُختبر تأكيديًا…»), §14.1 order, §14.3 (process test on Discovery, sealed deliverables,
registered criterion), §15 (five types, declared scope, failure is failure, law change = new claim),
§7 #11 (N-c diagnostic only).
"""
import random
import uuid

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from xauusd_swarm.charter import GateError, Governance
from xauusd_swarm.claims import ClaimsCharter
from xauusd_swarm.controls import ControlsLayer
from xauusd_swarm.court import CourtLayer
from xauusd_swarm.custody import CustodyLayer, Vault
from xauusd_swarm.discovery import DiscoveryLayer
from xauusd_swarm.evidence import EvidenceLayer
from xauusd_swarm.falsification import NOT_TESTED, PROCESS_TEST, FalsificationLayer
from xauusd_swarm.identity import AuthError, public_hex, sign
from xauusd_swarm.inventory import InventoryLayer, content_sha256, impl_sha256, run_c0
from xauusd_swarm.ledger import AnchorStore, Ledger
from xauusd_swarm.slicing import SlicingLayer

FK, CK, AK, OK, DK = (Ed25519PrivateKey.generate() for _ in range(5))
H = "cd" * 32


def F(action, **kw):
    return sign("founder", FK, {"action": action, "nonce": uuid.uuid4().hex, **kw})


def C(action, **kw):
    return sign("cust", CK, {"action": action, "nonce": uuid.uuid4().hex, **kw})


def A(action, **kw):
    return sign("aud", AK, {"action": action, "nonce": uuid.uuid4().hex, **kw})


def O(action, **kw):
    return sign("op", OK, {"action": action, "nonce": uuid.uuid4().hex, **kw})


def D(action, **kw):
    return sign("disc", DK, {"action": action, "nonce": uuid.uuid4().hex, **kw})


def world(n=200, seed=5):
    rnd, p, out = random.Random(seed), 100.0, []
    for i in range(n):
        c = p + rnd.gauss(0, 0.3)
        out.append({"id": f"o{i}", "t_market": 60.0 * i, "bid": round(c - 0.02, 5), "ask": round(c + 0.02, 5), "source": "S1"})
        p = c
    return out


def fx_dup(obs):                                    # synthetic C0 fixture (not a project rule)
    seen, aff = set(), []
    for o in obs:
        if o["t_market"] in seen:
            aff.append(o["id"])
        seen.add(o["t_market"])
    return {"outcome": "detected" if aff else "not_detected", "affected_ids": aff}


# ---- synthetic control code and worlds (fixtures, not project controls) ----
def ctl_mean(world):
    return {"mean": round(sum(world["x"]) / len(world["x"]), 9)}


def ctl_mean_other(world):
    return {"mean": 0.0}


W_PLANTED = {"x": [1.0 + 0.1 * (i % 3) for i in range(30)]}           # planted effect: mean ≈ 1.1
W_NULL = {"x": [(-1) ** i * 0.1 for i in range(30)]}                     # no effect: mean 0


SLICES = [{"slice_id": "D1", "station": "Discovery", "start": 0.0, "end": 4000.0},
          {"slice_id": "V1", "station": "Validation", "start": 4000.0, "end": 8000.0},
          {"slice_id": "X1", "station": "Final", "start": 8000.0, "end": 11940.0}]
CONFIG = {"structure": "A", "alpha_total": 0.05, "error_measure": "FWER", "procedure": "holm",
          "validity_reason": "Holm controls FWER under any dependence (س 681)"}


class Env:
    def __init__(self, ledger=None):
        self.cl = CustodyLayer(Vault(), identity="cust", key=CK)
        self.cc, self.il, self.sl = ClaimsCharter(), InventoryLayer(identity="cust", key=CK), SlicingLayer()
        self.ct, self.ev, self.dl, self.fl = CourtLayer(), EvidenceLayer(), DiscoveryLayer(), FalsificationLayer()
        self.co = ControlsLayer()
        self.g = Governance(FK.public_key(), ledger if ledger is not None else Ledger(),
                            extensions=[self.cc, self.cl, self.il, self.sl, self.ct, self.ev, self.dl, self.fl, self.co])
        for ident, k in (("cust", CK), ("aud", AK), ("op", OK), ("disc", DK)):
            self.g.register_key(F("register_key", identity=ident, public_key_hex=public_hex(k.public_key())))
        for role, h in (("custody", "cust"), ("custody_auditor", "aud"), ("court_operator", "op"),
                        ("discovery_participant", "disc")):
            self.cl.commit("role_assigned", F("assign_role", role=role, holder=h))
        self.g.set_initial_charter(F("charter_initial", charter="project", text="P"))
        self.g.set_initial_charter(F("charter_initial", charter="claims", text="C"))
        self.il.permit(F("permit_inventory", dataset_id="SYN", data_class="synthetic"))
        self.il.record_inventory("SYN", world(), source="gen")
        self.sl.freeze_plan(self.il, "P1", "SYN", basis="calendar_time", slices=SLICES)
        com = self.cl.vault.set_params("F1", c=1.5, a=2.0, b=-3.0, m=7.0)
        self.cl.commit("params_fixed", C("params_fixed", family="F1", params_commitment=com, delta=0.01))
        self.ct.commit("court_policy_decided", F("decide_court_policy", family="F1", structure="A", error_measure="FWER",
                                                 register_ref="synthetic", register_sha256="ab" * 32))
        self.ct.commit("court_frozen", F("freeze_court", family="F1", config=CONFIG))
        self.row("c0_gate", "C0")
        self.row("null_model", "N-shuffle")
        self.row("rediscovery", "blind_rediscovery")
        rule = {"rule_id": "R1", "dataset_id": "SYN", "effect": "feed", "test": "dup timestamps (synthetic)",
                "criterion": "any", "resulting_state": 1, "handling": {str(i): f"h{i}" for i in range(1, 6)},
                "test_impl_sha256": impl_sha256(fx_dup)}
        self.il.record_c0_rule(F("c0_rule_approve", rule=rule))
        self.dl.commit("null_card_accepted", F("accept_null_card", null_model="N-shuffle",
                                               card={"transform": "permutation", "null": "exchangeability"}))
        self.dl.commit("null_card_accepted", F("accept_null_card", null_model="N-c", card={"use": "diagnostic"}))

    def row(self, tool_kind, tool_id):
        """Control-matrix row (R16): one positive and one negative registered control, criterion, cost."""
        tgt = ControlsLayer.target_of(tool_kind, tool_id)
        for pol in ("positive", "negative"):
            self.co.commit("control_registered", F("register_control", control_id=f"row-{tool_kind}-{tool_id}-{pol}",
                           target=tgt, polarity=pol, expected={"metric": "m", "op": ">=", "value": 0},
                           world_sha256=H, impl_sha256=H))
        text = f"criterion for {tool_kind} {tool_id}"
        self.co.commit("tool_row_registered", F("register_tool_row", tool_kind=tool_kind, tool_id=tool_id,
                       controls=[f"row-{tool_kind}-{tool_id}-positive", f"row-{tool_kind}-{tool_id}-negative"],
                       criterion={"text": text, "sha256": content_sha256(text)}, cost_metric="compute seconds"))

    def decide(self, s):
        if s not in self.cl.decisions:
            self.cl.commit("custody_decision", C("custody_decision", slice=s, family="F1", delta=0.01,
                                                 params_commitment=self.cl.families["F1"]["commitment"],
                                                 boundaries=SlicingLayer.boundaries_text(self.sl.slices[s])))

    def claim(self, cid, path="أ"):
        self.cc.register(F("register_claim", card={"claim_id": cid, "version": 1, "tags": ["الموقع"], "category": None,
                                                   "path": path, "uses_events": False, "scope_type": "stable", "scope": "s",
                                                   "rulings": {"existence": "e", "size_with_uncertainty": "s",
                                                               "importance": "i"}, **({"d2_conditions": {
                                                       k: "declared" for k in ("c1", "c2", "c3", "c4", "c5", "c6")}}
                                                       if path == "د2" else {})}))
        self.ct.commit("claim_identity_registered", F("register_claim_identity", claim_id=cid, identity={
            "target_quantity": f"q-{cid}", "eligible_data_scope": "synthetic", "time_scope_type": "stable",
            "proof_path": path, "direction_or_threshold": ">0", "observation_precision": "n/a", "price_series": "Mid"}))

    def register_control(self, cid, null_model, polarity, outcome="pass"):
        world = W_PLANTED if polarity == "positive" else W_NULL
        if polarity == "positive":
            exp = {"metric": "mean", "op": ">=", "value": 0.5 if outcome == "pass" else 5.0}
        else:
            exp = {"metric": "mean", "op": "between", "low": -0.2, "high": 0.2} if outcome == "pass" else \
                {"metric": "mean", "op": ">=", "value": 1.0}
        self.co.commit("control_registered", F("register_control", control_id=cid,
                       target={"kind": "null_model", "id": null_model}, polarity=polarity, expected=exp,
                       world_sha256=content_sha256(world), impl_sha256=impl_sha256(ctl_mean)))
        return world

    def control(self, cid, null_model, polarity, outcome="pass"):
        world = self.register_control(cid, null_model, polarity, outcome)
        self.co.run_control(cid, ctl_mean, world, operator="op", key=OK)
        assert self.co.results[f"r-{cid}"]["outcome"] == outcome
        self.co.attest_reexecution(f"r-{cid}", ctl_mean, world, auditor="aud", key=AK)   # independent re-execution
        return f"r-{cid}"

    def validate_null(self, nm="N-shuffle"):
        ids = [self.control(f"{nm}-pos", nm, "positive"), self.control(f"{nm}-neg", nm, "negative")]
        return self.fl.commit("null_validity_recorded", F("record_null_validity", null_model=nm, control_results=ids))

    def stage(self, cid, n, **kw):
        return self.fl.commit("stage_recorded", F("record_stage", claim_id=cid, stage=n, **kw))

    def c0(self):
        res = run_c0(self.il.c0_rules["R1"], fx_dup, world())
        self.il.record_c0_result("R1", res, time="t")

    def to_stage3(self, cid="K1", null="N-shuffle"):
        self.claim(cid)
        self.stage(cid, 1, slice="D1", difference="mean shift in window w", evidence_sha256=H)
        if not self.il.c0_results:
            self.c0()
        self.stage(cid, 2, null_swaps=["N-shuffle"], temporal_location="first third of D1")
        self.stage(cid, 3, basic_null=null, justification="exchangeability is the target's null",
                   alternatives=[], sensitivity=["block length 5, 10"])

    def final_path(self, cid="K1"):
        """Test instance, screening opening, submission, report, opening (layer 6)."""
        if cid not in self.sl.designs:
            self.sl.record_design(F("record_split_design", claim_id=cid, design="A", rules={}))
        self.decide("X1")
        if f"T-{cid}" not in self.ct.instances:
            self.ct.commit("test_instance_registered", F("register_test_instance", test_instance_id=f"T-{cid}", claim_id=cid,
                       statistic="mean", procedure="t", null="N-shuffle", slice="X1", seeds="1", code_version="v1",
                       representation_id="r", transform_version="t1", price_series="Mid", path="Z", role="primary",
                       null_card_accepted=True))
        self.decide("D1")
        if "D1" not in self.g._s.slices:
            self.g.consume_slice("D1")
        if (cid, "D1") not in self.cc.openings:
            self.cc.open_on_slice(cid, "D1")
        self.ev.commit("confirmation_submitted", F("submit_for_confirmation", unit_id="U1", unit_slices=["X1"], family="F1",
                                                   claims=[{"claim_id": cid, "path": "Z", "screening_slices": ["D1"]}]))


@pytest.fixture
def env():
    return Env()


# ======================= five stages (§14.1) ===================================================
def test_stages_in_order(env):
    env.claim("K1")
    with pytest.raises(GateError, match="needs stage 1"):
        env.stage("K1", 2, null_swaps=["N-shuffle"], temporal_location="x")
    with pytest.raises(GateError, match="Discovery slice"):
        env.stage("K1", 1, slice="X1", difference="d", evidence_sha256=H)
    with pytest.raises(GateError, match="null failure is not a discovery"):
        env.stage("K1", 1, slice="D1", difference="d", evidence_sha256=H, basis="null_failure")
    env.stage("K1", 1, slice="D1", difference="d", evidence_sha256=H)
    with pytest.raises(GateError, match="recorded once"):
        env.stage("K1", 1, slice="D1", difference="d", evidence_sha256=H)


def test_stage2_needs_c0_null_swaps_and_time(env):
    env.claim("K1")
    env.stage("K1", 1, slice="D1", difference="d", evidence_sha256=H)
    with pytest.raises(GateError, match="C0 results"):
        env.stage("K1", 2, null_swaps=["N-shuffle"], temporal_location="x")
    env.c0()
    with pytest.raises(GateError, match="null swaps|null_swaps"):
        env.stage("K1", 2, null_swaps=[], temporal_location="x")
    with pytest.raises(GateError, match="temporal location"):
        env.stage("K1", 2, null_swaps=["N-shuffle"], temporal_location=" ")
    env.stage("K1", 2, null_swaps=["N-shuffle"], temporal_location="x")


def test_stage3_basic_null_rules(env):                                                     # TP-06 (a)
    env.claim("K1")
    env.stage("K1", 1, slice="D1", difference="d", evidence_sha256=H)
    env.c0()
    env.stage("K1", 2, null_swaps=["N-shuffle"], temporal_location="x")
    base = dict(justification="j", alternatives=[], sensitivity=[])
    with pytest.raises(GateError, match="control-matrix row"):                        # R16: no row, no use
        env.stage("K1", 3, basic_null="N-c", **base)
    env.row("null_model", "N-c")                                                      # N-c has a row (diagnostic)
    env.row("null_model", "N-unknown")
    with pytest.raises(GateError, match="diagnostic only"):
        env.stage("K1", 3, basic_null="N-c", **base)
    with pytest.raises(GateError, match="accepted by the founder"):
        env.stage("K1", 3, basic_null="N-unknown", **base)
    with pytest.raises(GateError, match="JUSTIFIED"):
        env.stage("K1", 3, basic_null="N-shuffle", **{**base, "justification": ""})
    with pytest.raises(GateError, match="diagnostic only"):
        env.stage("K1", 3, basic_null="N-shuffle", **{**base, "alternatives": ["N-c"]})
    env.stage("K1", 3, basic_null="N-shuffle", **base)


def test_no_confirmation_without_valid_null(env):                                          # TP-06 (a), (c)
    env.to_stage3()
    assert env.fl.status("K1") == NOT_TESTED
    with pytest.raises(GateError, match="no confirmatory test without a valid null"):
        env.final_path()
    with pytest.raises(GateError, match="diagnostic only"):
        env.fl.commit("null_validity_recorded", F("record_null_validity", null_model="N-c", control_results=["x"]))
    env.validate_null()
    env.final_path()
    assert env.fl.status("K1") == "stage 3"


def test_confirmation_needs_stages(env):
    env.claim("K9")
    env.sl.record_design(F("record_split_design", claim_id="K9", design="A", rules={}))
    with pytest.raises(GateError, match="follows stages 1–3"):
        env.ev.commit("confirmation_submitted", F("submit_for_confirmation", unit_id="U9", unit_slices=["X1"],
                      family="F1", claims=[{"claim_id": "K9", "path": "Z", "screening_slices": ["D1"]}]))


def test_stage4_and_stage5(env):
    env.to_stage3()
    env.validate_null()
    env.final_path()
    with pytest.raises(GateError, match="opened Final unit"):
        env.stage("K1", 4)
    env.ev.commit("adequacy_reported", C("adequacy_report", unit_id="U1", source_slices=["X1"],
                  effective_units_after_purge=100, coverage=0.9, censoring_ratio=0.1, tie_ratio=0.0,
                  tie_includes_ambiguous=True, claims=["K1"], test_instances_per_claim={"K1": 1}, detectable_effect=0.2,
                  family_size=1, procedure="holm", alpha=0.05, exclusions=[], verdict="adequate", time="t"))
    env.g.consume_slice("X1")
    env.ev.open_final(F("open_final", unit_id="U1", openings=env.ev.final_manifest("U1")))
    env.stage("K1", 4)
    env.claim("K1-int", path="د1")
    with pytest.raises(GateError, match="separate claim"):
        env.stage("K1", 5, interpretation_claim_id="K1")
    env.claim("K-not-d", path="ب")
    with pytest.raises(GateError, match="د1 or د2"):
        env.stage("K1", 5, interpretation_claim_id="K-not-d")
    env.stage("K1", 5, interpretation_claim_id="K1-int")


# ======================= blind rediscovery (§14.3) =============================================
def crit(text="match = same target and sign within window"):
    return {"text": text, "sha256": content_sha256(text)}


def test_rediscovery_rules(env):
    with pytest.raises(GateError, match="Discovery only"):
        env.fl.commit("rediscovery_registered", F("register_rediscovery", run_id="RD1", slice="X1", criterion=crit(),
                                                  shared_tools=["kde"], audit_sample_size=3))
    with pytest.raises(GateError, match="match criterion"):
        env.fl.commit("rediscovery_registered", F("register_rediscovery", run_id="RD1", slice="D1",
                                                  criterion={"text": "x", "sha256": H}, shared_tools=[], audit_sample_size=3))
    with pytest.raises(GateError, match="audit sample"):
        env.fl.commit("rediscovery_registered", F("register_rediscovery", run_id="RD1", slice="D1", criterion=crit(),
                                                  shared_tools=[], audit_sample_size=0))
    env.fl.commit("rediscovery_registered", F("register_rediscovery", run_id="RD1", slice="D1", criterion=crit(),
                                              shared_tools=["kde"], audit_sample_size=3))
    score = dict(run_id="RD1", criterion_sha256=crit()["sha256"], matched=2, planted=3, tag=PROCESS_TEST)
    with pytest.raises(GateError, match="after the deliverables are sealed"):
        env.fl.commit("rediscovery_scored", O("score_rediscovery", **score))
    with pytest.raises(GateError, match="discovery participant"):
        env.fl.commit("rediscovery_sealed", O("seal_rediscovery", run_id="RD1", deliverables_sha256=H))
    env.fl.commit("rediscovery_sealed", D("seal_rediscovery", run_id="RD1", deliverables_sha256=H))
    with pytest.raises(GateError, match="once"):
        env.fl.commit("rediscovery_sealed", D("seal_rediscovery", run_id="RD1", deliverables_sha256=H))
    with pytest.raises(GateError, match="registered criterion"):
        env.fl.commit("rediscovery_scored", O("score_rediscovery", **{**score, "criterion_sha256": H}))
    with pytest.raises(GateError, match="never counts as confirmation"):
        env.fl.commit("rediscovery_scored", O("score_rediscovery", **{**score, "tag": "confirmed"}))
    with pytest.raises(GateError, match="court operator"):
        env.fl.commit("rediscovery_scored", F("score_rediscovery", **score))
    env.fl.commit("rediscovery_scored", O("score_rediscovery", **score))
    assert env.fl.rediscovery["RD1"]["score"]["tag"] == PROCESS_TEST


# ======================= law drift (§15) =======================================================
def test_drift_scope_and_replication(env):
    env.claim("K1")
    with pytest.raises(GateError, match="before it"):
        env.fl.commit("replication_recorded", O("record_replication", claim_id="K1", outcome="failed",
                                                condition="high vol", evidence_sha256=H))
    with pytest.raises(GateError, match="one of the five"):
        env.fl.commit("drift_scope_declared", F("declare_drift_scope", claim_id="K1", drift_type="seasonal",
                                                predicts_failure_when=[]))
    env.fl.commit("drift_scope_declared", F("declare_drift_scope", claim_id="K1", drift_type="مشروطة",
                                            predicts_failure_when=["high vol"]))
    with pytest.raises(GateError, match="frozen"):
        env.fl.commit("drift_scope_declared", F("declare_drift_scope", claim_id="K1", drift_type="مستقرة",
                                                predicts_failure_when=[]))
    env.fl.commit("replication_recorded", O("record_replication", claim_id="K1", outcome="failed", condition="high vol",
                                            evidence_sha256=H))
    env.fl.commit("replication_recorded", O("record_replication", claim_id="K1", outcome="failed", condition="low vol",
                                            evidence_sha256=H))
    assert [r["status"] for r in env.fl.replications["K1"]] == ["فشل متوقَّع ضمن النطاق المعلن", "فشل"]
    with pytest.raises(GateError, match="new claim"):
        env.fl.commit("replication_recorded", O("record_replication", claim_id="K1", outcome="failed", condition="x",
                                                evidence_sha256=H, law_changed=True))


def test_law_change_is_a_new_claim(env):
    env.claim("K1"); env.claim("K2")
    env.fl.commit("drift_scope_declared", F("declare_drift_scope", claim_id="K1", drift_type="مستقرة",
                                            predicts_failure_when=[]))
    with pytest.raises(GateError, match="failed replication"):
        env.fl.commit("law_change_linked", F("link_law_change", new_claim_id="K2", old_claim_id="K1"))
    env.fl.commit("replication_recorded", O("record_replication", claim_id="K1", outcome="failed", condition="c",
                                            evidence_sha256=H))
    with pytest.raises(GateError, match="NEW registered claim"):
        env.fl.commit("law_change_linked", F("link_law_change", new_claim_id="K1", old_claim_id="K1"))
    env.fl.commit("law_change_linked", F("link_law_change", new_claim_id="K2", old_claim_id="K1"))
    assert env.fl.replications["K1"][-1]["status"] == "فشل"                    # the old failure stays


def test_founder_and_operator_only(env):
    env.claim("K1")
    with pytest.raises((GateError, AuthError)):
        env.fl.commit("stage_recorded", O("record_stage", claim_id="K1", stage=1, slice="D1", difference="d",
                                          evidence_sha256=H))
    with pytest.raises((GateError, AuthError)):
        env.fl.commit("drift_scope_declared", O("declare_drift_scope", claim_id="K1", drift_type="مستقرة",
                                                predicts_failure_when=[]))


def test_history_replays(tmp_path):
    led = tmp_path / "led" / "g.jsonl"; led.parent.mkdir()
    anc = tmp_path / "anc" / "a.jsonl"; anc.parent.mkdir()
    e = Env(Ledger(led, anchors=AnchorStore(anc)))
    e.to_stage3()
    e.fl.commit("drift_scope_declared", F("declare_drift_scope", claim_id="K1", drift_type="عابرة",
                                          predicts_failure_when=[]))
    fl2 = FalsificationLayer()
    Governance(FK.public_key(), Ledger(led, anchors=AnchorStore(anc)),
               extensions=[ClaimsCharter(), CustodyLayer(None), InventoryLayer(), SlicingLayer(), CourtLayer(),
                           EvidenceLayer(), DiscoveryLayer(), fl2, ControlsLayer()])
    assert set(fl2.stages["K1"]) == {1, 2, 3} and fl2.status("K1") == NOT_TESTED and "K1" in fl2.scopes


# ======================= review round R1 (ChatGPT, 2026-11-17) ==================================
def test_r1_01_null_validity_only_from_recorded_controls(env):
    n0 = len(env.fl.null_validity)
    with pytest.raises(GateError, match="no free-standing evidence hashes"):        # the old form is refused
        env.fl.commit("null_validity_recorded", F("record_null_validity", null_model="N-shuffle", control_results=[],
                                                  positive_controls_sha256=H, negative_controls_sha256=H))
    with pytest.raises(GateError, match="not recorded"):
        env.fl.commit("null_validity_recorded", F("record_null_validity", null_model="N-shuffle",
                                                  control_results=["r-ghost"]))
    pos = env.control("p1", "N-shuffle", "positive")
    with pytest.raises(GateError, match="one positive and one negative"):
        env.fl.commit("null_validity_recorded", F("record_null_validity", null_model="N-shuffle", control_results=[pos]))
    other = env.control("n-other", "N-other", "negative")
    with pytest.raises(GateError, match="does not target"):
        env.fl.commit("null_validity_recorded", F("record_null_validity", null_model="N-shuffle",
                                                  control_results=[pos, other]))
    failed = env.control("n1", "N-shuffle", "negative", outcome="fail")
    with pytest.raises(GateError, match="failed"):
        env.fl.commit("null_validity_recorded", F("record_null_validity", null_model="N-shuffle",
                                                  control_results=[pos, failed]))
    with pytest.raises(GateError, match="distinct"):
        env.fl.commit("null_validity_recorded", F("record_null_validity", null_model="N-shuffle",
                                                  control_results=[pos, pos]))
    assert len(env.fl.null_validity) == n0
    neg = env.control("n2", "N-shuffle", "negative")
    env.fl.commit("null_validity_recorded", F("record_null_validity", null_model="N-shuffle", control_results=[pos, neg]))
    assert "N-shuffle" in env.fl.null_validity


def test_r1_01_control_registry_rules(env):
    with pytest.raises(GateError, match="registered before"):
        env.co.commit("control_result_recorded", O("record_control_result", result_id="r0", control_id="ghost",
                      impl_sha256=H, world_sha256=H, observed={"mean": 1}, evidence_sha256=content_sha256({"mean": 1}),
                      outcome="pass"))
    base = dict(target={"kind": "null_model", "id": "N"}, expected={"metric": "mean", "op": ">=", "value": 0.5},
                world_sha256=content_sha256(W_PLANTED), impl_sha256=impl_sha256(ctl_mean))
    with pytest.raises(GateError, match="positive or negative"):
        env.co.commit("control_registered", F("register_control", control_id="c0", polarity="neutral", **base))
    with pytest.raises((GateError, AuthError)):
        env.co.commit("control_registered", O("register_control", control_id="c2", polarity="negative", **base))
    env.co.commit("control_registered", F("register_control", control_id="c1", polarity="positive", **base))
    with pytest.raises(GateError, match="court operator"):
        env.co.run_control("c1", ctl_mean, W_PLANTED, operator="founder", key=FK)
    env.co.run_control("c1", ctl_mean, W_PLANTED, operator="op", key=OK)
    with pytest.raises(GateError, match="one result per registered control"):
        env.co.run_control("c1", ctl_mean, W_PLANTED, operator="op", key=OK, result_id="r-again")


# ======================= review round R2 (ChatGPT, 2026-11-17) ==================================
def test_r2_01_control_result_must_follow_from_execution(env):
    world = env.register_control("c-pos", "N-shuffle", "positive")
    good = {"mean": 1.1}
    base = dict(result_id="r-x", control_id="c-pos", impl_sha256=impl_sha256(ctl_mean), world_sha256=content_sha256(world))
    n0 = len(env.co.results)
    with pytest.raises(GateError, match="follow from the registered expectation"):           # pass that does not follow
        env.co.commit("control_result_recorded", O("record_control_result", observed={"mean": 0.0},
                      evidence_sha256=content_sha256({"mean": 0.0}), outcome="pass", **base))
    with pytest.raises(GateError, match="structured"):
        env.co.commit("control_result_recorded", O("record_control_result", observed="looks fine",
                      evidence_sha256=content_sha256("looks fine"), outcome="pass", **base))
    with pytest.raises(GateError, match="hash of the recorded observation"):
        env.co.commit("control_result_recorded", O("record_control_result", observed=good, evidence_sha256=H,
                      outcome="pass", **base))
    with pytest.raises(GateError, match="registered code on the registered world"):
        env.co.commit("control_result_recorded", O("record_control_result", observed=good,
                      evidence_sha256=content_sha256(good), outcome="pass", **{**base, "impl_sha256": H}))
    with pytest.raises(GateError, match="registered code on the registered world"):
        env.co.commit("control_result_recorded", O("record_control_result", observed=good,
                      evidence_sha256=content_sha256(good), outcome="pass", **{**base, "world_sha256": H}))
    with pytest.raises(GateError, match="finite value"):
        env.co.commit("control_result_recorded", O("record_control_result", observed={"other": 1},
                      evidence_sha256=content_sha256({"other": 1}), outcome="pass", **base))
    assert len(env.co.results) == n0
    with pytest.raises(GateError, match="not the registered one"):                            # run with other code
        env.co.run_control("c-pos", ctl_mean_other, world, operator="op", key=OK)
    with pytest.raises(GateError, match="not the registered one"):                            # run on other world
        env.co.run_control("c-pos", ctl_mean, W_NULL, operator="op", key=OK)
    env.co.run_control("c-pos", ctl_mean, world, operator="op", key=OK)
    assert env.co.results["r-c-pos"]["outcome"] == "pass" and env.co.reverify("r-c-pos", ctl_mean, world)
    assert not env.co.reverify("r-c-pos", ctl_mean, W_NULL)


def test_r2_01_expectation_shape(env):
    for e in ({"metric": "mean", "op": "~", "value": 1}, {"metric": "mean", "op": ">=", "value": float("nan")},
              {"metric": "mean", "op": "between", "low": 2, "high": 1}, {"metric": "", "op": "==", "value": 1},
              "planted effect detected"):
        with pytest.raises(GateError, match="expect|between|finite"):
            env.co.commit("control_registered", F("register_control", control_id="cx", target={"kind": "null_model",
                          "id": "N"}, polarity="positive", expected=e, world_sha256=H, impl_sha256=H))


def test_r2_01_nondeterministic_control_refused(env):
    state = {"n": 0}

    def ctl_counter(world):
        state["n"] += 1
        return {"mean": state["n"]}
    env.co.commit("control_registered", F("register_control", control_id="cnd", target={"kind": "null_model", "id": "N"},
                  polarity="positive", expected={"metric": "mean", "op": ">=", "value": 0},
                  world_sha256=content_sha256(W_PLANTED), impl_sha256=impl_sha256(ctl_counter)))
    with pytest.raises(GateError, match="not deterministic"):
        env.co.run_control("cnd", ctl_counter, W_PLANTED, operator="op", key=OK)


# ======================= review round R3 (ChatGPT, 2026-11-17) ==================================
def test_r3_01_validity_needs_independent_reexecution(env):
    wp = env.register_control("rp", "N-shuffle", "positive")
    wn = env.register_control("rn", "N-shuffle", "negative")
    env.co.run_control("rp", ctl_mean, wp, operator="op", key=OK)
    env.co.run_control("rn", ctl_mean, wn, operator="op", key=OK)
    with pytest.raises(GateError, match="no independent re-execution"):
        env.fl.commit("null_validity_recorded", F("record_null_validity", null_model="N-shuffle",
                                                  control_results=["r-rp", "r-rn"]))
    with pytest.raises(GateError, match="auditor"):                                     # the recorder cannot attest
        env.co.attest_reexecution("r-rp", ctl_mean, wp, auditor="op", key=OK)
    with pytest.raises(GateError, match="auditor"):
        env.co.attest_reexecution("r-rp", ctl_mean, wp, auditor="disc", key=DK)
    with pytest.raises(GateError, match="registered code and world"):
        env.co.attest_reexecution("r-rp", ctl_mean_other, wp, auditor="aud", key=AK)
    env.co.attest_reexecution("r-rp", ctl_mean, wp, auditor="aud", key=AK)
    with pytest.raises(GateError, match="one attestation per auditor"):
        env.co.attest_reexecution("r-rp", ctl_mean, wp, auditor="aud", key=AK)
    with pytest.raises(GateError, match="r-rn"):                                         # one still unattested
        env.fl.commit("null_validity_recorded", F("record_null_validity", null_model="N-shuffle",
                                                  control_results=["r-rp", "r-rn"]))
    env.co.attest_reexecution("r-rn", ctl_mean, wn, auditor="aud", key=AK)
    env.fl.commit("null_validity_recorded", F("record_null_validity", null_model="N-shuffle",
                                              control_results=["r-rp", "r-rn"]))


def test_r3_01_fabricated_observation_caught_by_reexecution(env):
    wp = env.register_control("fp", "N-shuffle", "positive")
    fake = {"mean": 0.9}                                       # satisfies >= 0.5, but the code on wp gives 1.1
    env.co.commit("control_result_recorded", O("record_control_result", result_id="r-fp", control_id="fp",
                  impl_sha256=impl_sha256(ctl_mean), world_sha256=content_sha256(wp), observed=fake,
                  evidence_sha256=content_sha256(fake), outcome="pass"))          # accepted: consistent on its face
    env.co.attest_reexecution("r-fp", ctl_mean, wp, auditor="aud", key=AK)
    assert env.co.reverifications["r-fp"][-1]["verdict"] == "mismatch"
    neg = env.control("fn", "N-shuffle", "negative")
    with pytest.raises(GateError, match="failed independent re-execution"):
        env.fl.commit("null_validity_recorded", F("record_null_validity", null_model="N-shuffle",
                                                  control_results=["r-fp", neg]))
    assert "N-shuffle" not in env.fl.null_validity


def test_r3_01_forged_match_refused(env):
    wp = env.register_control("gp", "N-shuffle", "positive")
    fake = {"mean": 0.9}
    env.co.commit("control_result_recorded", O("record_control_result", result_id="r-gp", control_id="gp",
                  impl_sha256=impl_sha256(ctl_mean), world_sha256=content_sha256(wp), observed=fake,
                  evidence_sha256=content_sha256(fake), outcome="pass"))
    real = content_sha256(ctl_mean(wp))
    with pytest.raises(GateError, match="must follow from comparing"):          # "match" with different evidence
        env.co.commit("control_result_reverified", A("reverify_control_result", result_id="r-gp",
                      impl_sha256=impl_sha256(ctl_mean), world_sha256=content_sha256(wp),
                      reexecuted_evidence_sha256=real, verdict="match"))
    with pytest.raises(GateError, match="result's world_sha256"):
        env.co.commit("control_result_reverified", A("reverify_control_result", result_id="r-gp",
                      impl_sha256=impl_sha256(ctl_mean), world_sha256=H,
                      reexecuted_evidence_sha256=content_sha256(fake), verdict="match"))


# ======================= WP8-09 review R1: every point of use needs a matrix row ===============
def test_wp809_r1_null_swaps_alternatives_and_instances_need_rows(env):
    env.claim("K1")
    env.stage("K1", 1, slice="D1", difference="d", evidence_sha256=H)
    env.c0()
    with pytest.raises(GateError, match="null_model 'N-rowless'"):
        env.stage("K1", 2, null_swaps=["N-shuffle", "N-rowless"], temporal_location="x")
    env.stage("K1", 2, null_swaps=["N-shuffle"], temporal_location="x")
    with pytest.raises(GateError, match="null_model 'N-alt'"):
        env.stage("K1", 3, basic_null="N-shuffle", justification="j", alternatives=["N-alt"], sensitivity=[])
    env.row("null_model", "N-alt")
    env.stage("K1", 3, basic_null="N-shuffle", justification="j", alternatives=["N-alt"], sensitivity=[])
    env.decide("X1")
    with pytest.raises(GateError, match="null_model 'N0'"):
        env.ct.commit("test_instance_registered", F("register_test_instance", test_instance_id="T9", claim_id="K1",
                      statistic="mean", procedure="t", null="N0", slice="X1", seeds="1", code_version="v1",
                      representation_id="r", transform_version="t1", price_series="Mid", path="R", role="primary",
                      null_card_accepted=True))


def test_wp809_r1_rediscovery_needs_row():
    e = Env.__new__(Env)
    Env.__init__(e)
    del e.co.matrix[("rediscovery", "blind_rediscovery")]                  # simulate the row absent
    text = "match rule"
    with pytest.raises(GateError, match="rediscovery 'blind_rediscovery'"):
        e.fl.commit("rediscovery_registered", F("register_rediscovery", run_id="RD1", slice="D1",
                    criterion={"text": text, "sha256": content_sha256(text)}, shared_tools=[], audit_sample_size=1))


# ======================= TP-82 review R1-01: IAAFT use restriction enforced at use points ======
def _restrict_iaaft(env):
    env.dl.commit("null_card_accepted", F("accept_null_card", null_model="iaaft",
                  card={"transform": "IAAFT", "null": "monotone transform of a stationary linear Gaussian process"}))
    env.co.commit("use_restriction_registered", F("register_use_restriction", tool_kind="null_model", tool_id="iaaft",
                  restriction="stable_windows_or_registered_transform",
                  text="IAAFT assumes stationarity: within stable windows or after a transform (س 829); TP-82"))
    env.row("null_model", "iaaft")


def _justify(env, key, **kw):
    base = {"tool_kind": "null_model", "tool_id": "iaaft", "use_key": key}
    return env.co.commit("restricted_use_justified", F("justify_restricted_use", **base, **kw))


def test_r1_01_restricted_null_needs_a_justification_per_use(env):
    _restrict_iaaft(env)
    env.claim("K1")
    env.stage("K1", 1, slice="D1", difference="d", evidence_sha256=H)
    env.c0()
    with pytest.raises(GateError, match="restricted"):
        env.stage("K1", 2, null_swaps=["iaaft"], temporal_location="x")
    _justify(env, "claim:K1/stage:2", basis="stable_windows", windows=[[0.0, 2000.0], [2000.0, 4000.0]],
             stationarity_method="per-window mean/variance/band-power stability (method open in the architecture)",
             stationarity_evidence_sha256=H)
    env.stage("K1", 2, null_swaps=["iaaft"], temporal_location="x")
    with pytest.raises(GateError, match="restricted"):                       # another use needs its own record
        env.stage("K1", 3, basic_null="iaaft", justification="j", alternatives=[], sensitivity=["s"])


def test_r1_01_justification_shape(env):
    _restrict_iaaft(env)
    with pytest.raises(GateError, match="basis"):
        _justify(env, "claim:K1/stage:2", basis="trust me")
    with pytest.raises(GateError, match="start < end"):
        _justify(env, "claim:K1/stage:2", basis="stable_windows", windows=[[5.0, 1.0]], stationarity_method="m",
                 stationarity_evidence_sha256=H)
    with pytest.raises(GateError, match="evidence"):
        _justify(env, "claim:K1/stage:2", basis="stable_windows", windows=[[0.0, 1.0]], stationarity_method="m")
    with pytest.raises(GateError, match="frozen in inventory"):
        _justify(env, "claim:K1/stage:2", basis="registered_transform", transform_id="T-none",
                 stationarity_evidence_sha256=H)
    with pytest.raises(GateError, match="no restriction"):
        env.co.commit("restricted_use_justified", F("justify_restricted_use", tool_kind="null_model",
                      tool_id="N-shuffle", use_key="claim:K1/stage:2", basis="stable_windows", windows=[[0.0, 1.0]],
                      stationarity_method="m", stationarity_evidence_sha256=H))
    _justify(env, "claim:K1/stage:2", basis="stable_windows", windows=[[0.0, 1.0]], stationarity_method="m",
             stationarity_evidence_sha256=H)
    with pytest.raises(GateError, match="one new use"):
        _justify(env, "claim:K1/stage:2", basis="stable_windows", windows=[[0.0, 1.0]], stationarity_method="m",
                 stationarity_evidence_sha256=H)


def test_r1_01_unrestricted_null_unchanged(env):
    env.to_stage3()                                                           # N-shuffle: no restriction
    assert ("null_model", "N-shuffle") not in env.co.restrictions


def test_r1_01_test_instance_with_restricted_null(env):
    _restrict_iaaft(env)
    env.claim("K1")
    env.decide("X1")
    ti = dict(test_instance_id="T-K1", claim_id="K1", statistic="mean", procedure="t", null="iaaft", slice="X1",
              seeds="1", code_version="v1", representation_id="r", transform_version="t1", price_series="Mid",
              path="Z", role="primary", null_card_accepted=True)
    with pytest.raises(GateError, match="restricted"):
        env.ct.commit("test_instance_registered", F("register_test_instance", **ti))
    _justify(env, "test_instance:T-K1", basis="stable_windows", windows=[[8000.0, 11940.0]], stationarity_method="m",
             stationarity_evidence_sha256=H)
    env.ct.commit("test_instance_registered", F("register_test_instance", **ti))



# ======================= TP-82 review R2-01: the restriction is mandatory by the card =========
def test_r2_01_iaaft_row_refused_without_restriction(env):
    with pytest.raises(GateError, match="mandatory restriction"):
        env.row("null_model", "iaaft")


def test_r2_01_iaaft_named_only_in_its_card_is_also_restricted(env):
    """A null model with another id whose accepted card names IAAFT carries the same restriction."""
    env.dl.commit("null_card_accepted", F("accept_null_card", null_model="N-surrogate-7",
                  card={"transform": "IAAFT surrogate", "null": "stationary linear Gaussian"}))
    with pytest.raises(GateError, match="mandatory restriction"):
        env.row("null_model", "N-surrogate-7")


def test_r2_01_wrong_restriction_kind_refused(env):
    with pytest.raises(GateError):
        env.co.commit("use_restriction_registered", F("register_use_restriction", tool_kind="null_model",
                      tool_id="iaaft", restriction="none", text="x"))


def test_r2_01_use_refused_even_if_row_predates_the_rule(env):
    """Defence in depth: a use point refuses an IAAFT tool without its restriction even if a row exists
    (e.g. a ledger written before R2-01)."""
    env.co.matrix[("null_model", "iaaft")] = {"tool_kind": "null_model", "tool_id": "iaaft"}   # simulated old row
    env.claim("K1")
    env.stage("K1", 1, slice="D1", difference="d", evidence_sha256=H)
    env.c0()
    with pytest.raises(GateError, match="mandatory restriction"):
        env.stage("K1", 2, null_swaps=["iaaft"], temporal_location="x")


@pytest.mark.parametrize("bad", ["iaaft", {}, {"iaaft": 1}, [], [None], None])
def test_s1_01_use_point_list_never_skipped(env, bad):
    """review S1-01 (WP9-04/05a): a malformed list at a use point is refused, never read as empty."""
    env.claim("K1")
    env.stage("K1", 1, slice="D1", difference="d", evidence_sha256=H)
    env.c0()
    with pytest.raises(GateError):
        env.stage("K1", 2, null_swaps=bad, temporal_location="x")
