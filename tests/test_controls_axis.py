"""Cross-cutting axis tests (WP8-09): control matrix per tool with enforcement at the points of use
(WP7-04 §2.1, R16; س 1442, 2313; TP-07), and the procedural governance audit (مك-13; §13 #1–#3; ق-05).
SYNTHETIC ONLY. No control code or planted world is run here beyond fixtures.
"""
import uuid

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from xauusd_swarm.charter import GateError, Governance
from xauusd_swarm.claims import ClaimsCharter
from xauusd_swarm.controls import ControlsLayer
from xauusd_swarm.court import CourtLayer
from xauusd_swarm.custody import CustodyLayer, Vault, request
from xauusd_swarm.discovery import DiscoveryLayer
from xauusd_swarm.governance_audit import NOT_PROOF, STATES, GovernanceAuditLayer, audit_layer3
from xauusd_swarm.identity import AuthError, public_hex, sign
from xauusd_swarm.inventory import InventoryLayer, content_sha256, impl_sha256
from xauusd_swarm.ledger import AnchorStore, Ledger

FK, CK, AK, OK, GK, MK = (Ed25519PrivateKey.generate() for _ in range(6))
H = "ef" * 32


def F(action, **kw):
    return sign("founder", FK, {"action": action, "nonce": uuid.uuid4().hex, **kw})


def G(action, **kw):
    return sign("gaud", GK, {"action": action, "nonce": uuid.uuid4().hex, **kw})


def M(action, **kw):
    return sign("m1", MK, {"action": action, "nonce": uuid.uuid4().hex, **kw})


def lineage():
    return {"data": {"source": "synthetic", "transforms": [], "block_usage": [], "exclusions": [], "blinding_state": "blinded",
                     "availability_time_source": "مرصود"},
            "environment": {"libraries": [], "environment": "wp801", "seeds": [1], "training_settings": {}},
            "hypothesis": {"versions_branches_edits": [], "epistemic_path": "as given"},
            "experiments": {"stopped_or_incomplete": [], "exclusion_reasons": []},
            "knowledge": {"seen": [], "tools": [], "touched_gold_or_R_info": False, "llm_in_lineage": False,
                          "blinding_breach_events": []}}


def config():
    return {"representations": ["r"], "engines": [{"name": "kde", "kind": "engine"}], "statistics_and_nulls": ["N"],
            "experiment_selection": "grid", "adaptation": "none", "memory": "private",
            "permissions_and_resources": {"compute_seconds": 60}}


class Env:
    def __init__(self, ledger=None):
        self.cl = CustodyLayer(Vault(), identity="cust", key=CK)
        self.cc, self.ct, self.dl, self.co = ClaimsCharter(), CourtLayer(), DiscoveryLayer(), ControlsLayer()
        self.il, self.ga = InventoryLayer(identity="cust", key=CK), GovernanceAuditLayer()
        self.g = Governance(FK.public_key(), ledger if ledger is not None else Ledger(),
                            extensions=[self.cc, self.cl, self.il, self.ct, self.dl, self.co, self.ga])
        for ident, k in (("cust", CK), ("aud", AK), ("op", OK), ("gaud", GK), ("m1", MK)):
            self.g.register_key(F("register_key", identity=ident, public_key_hex=public_hex(k.public_key())))
        for role, h in (("custody", "cust"), ("custody_auditor", "aud"), ("court_operator", "op"),
                        ("governance_auditor", "gaud"), ("discovery_participant", "m1")):
            self.cl.commit("role_assigned", F("assign_role", role=role, holder=h))
        self.g.set_initial_charter(F("charter_initial", charter="project", text="P"))
        self.g.set_initial_charter(F("charter_initial", charter="claims", text="C"))

    def controls_for(self, tool_kind, tool_id, pols=("positive", "negative"), target=None):
        ids = []
        for pol in pols:
            cid = f"{tool_kind}-{tool_id}-{pol}-{uuid.uuid4().hex[:6]}"
            self.co.commit("control_registered", F("register_control", control_id=cid,
                           target=target or ControlsLayer.target_of(tool_kind, tool_id), polarity=pol,
                           expected={"metric": "m", "op": ">=", "value": 0}, world_sha256=H, impl_sha256=H))
            ids.append(cid)
        return ids

    def row(self, tool_kind, tool_id, **over):
        text = "criterion"
        st = dict(tool_kind=tool_kind, tool_id=tool_id, controls=self.controls_for(tool_kind, tool_id),
                  criterion={"text": text, "sha256": content_sha256(text)}, cost_metric="compute seconds")
        st.update(over)
        return self.co.commit("tool_row_registered", F("register_tool_row", **st))


@pytest.fixture
def env():
    return Env()


# ======================= control matrix (R16) =================================================
def test_row_needs_positive_negative_criterion_cost(env):
    with pytest.raises(GateError, match="one positive and one negative"):
        env.row("path", "P1", controls=env.controls_for("path", "P1", pols=("positive",)))
    with pytest.raises(GateError, match="not a registered control of this tool"):
        env.row("path", "P1", controls=env.controls_for("path", "OTHER"))
    with pytest.raises(GateError, match="registered criterion"):
        env.row("path", "P1", criterion={"text": "x", "sha256": H})
    with pytest.raises(GateError, match="cost"):
        env.row("path", "P1", cost_metric=" ")
    with pytest.raises(GateError, match="tool_kind"):
        env.row("magic", "P1")
    env.row("path", "P1")
    with pytest.raises(GateError, match="one matrix row per tool"):
        env.row("path", "P1")
    with pytest.raises((GateError, AuthError)):
        env.co.commit("tool_row_registered", G("register_tool_row", tool_kind="path", tool_id="P2", controls=[],
                                               criterion={}, cost_metric="x"))


def test_no_path_used_without_row(env):
    env.dl.commit("path_registered", F("register_path", path_id="P1", kind="distributional_regularities",
                  card={"text": "c", "sha256": content_sha256("c")}, generalisation_test={"text": "g", "sha256": content_sha256("g")},
                  designers_without_sealed_access=True, lineage_sha256=H))
    env.row("engine", "kde")
    env.dl.commit("resource_rule_frozen", F("freeze_resource_rule", family="F1", rule="equal_compute_time", compute_seconds=60))
    env.dl.commit("mind_registered", F("register_mind", mind_id="m1", family="F1", config=config()))
    prop = dict(proposal_id="p1", type="hypothesis", family="F1", path_id="P1", content_sha256=H, lineage=lineage())
    with pytest.raises(GateError, match="path 'P1' in use without its control-matrix row"):
        env.dl.commit("proposal_submitted", M("propose", **prop))
    env.row("path", "P1")
    env.dl.commit("proposal_submitted", M("propose", **prop))


def test_no_engine_used_without_row(env):
    env.dl.commit("resource_rule_frozen", F("freeze_resource_rule", family="F1", rule="equal_compute_time", compute_seconds=60))
    with pytest.raises(GateError, match="engine 'kde'"):
        env.dl.commit("mind_registered", F("register_mind", mind_id="m1", family="F1", config=config()))
    env.row("engine", "kde")
    env.dl.commit("mind_registered", F("register_mind", mind_id="m1", family="F1", config=config()))


def test_no_c0_rule_used_without_row(env):
    def fx(obs):
        return {"outcome": "not_detected", "affected_ids": []}
    env.il.permit(F("permit_inventory", dataset_id="S", data_class="synthetic"))
    env.il.record_inventory("S", [{"id": "o0", "t_market": 0.0, "bid": 1.0}], source="g")
    rule = {"rule_id": "R1", "dataset_id": "S", "effect": "feed", "test": "t", "criterion": "c", "resulting_state": 1,
            "handling": {str(i): "h" for i in range(1, 6)}, "test_impl_sha256": impl_sha256(fx)}
    with pytest.raises(GateError, match="c0_gate"):
        env.il.record_c0_rule(F("c0_rule_approve", rule=rule))
    env.row("c0_gate", "C0")
    env.il.record_c0_rule(F("c0_rule_approve", rule=rule))


def test_no_court_ruling_without_row(env):
    req = sign("op", OK, {"action": "court_ruling", "nonce": uuid.uuid4().hex, "family": "F1"})
    with pytest.raises(GateError, match="court 'court'"):
        env.g._commit("court_ruling", req.to_payload())


# ======================= governance audit (مك-13) =============================================
def report(env, **over):
    if ("leak_check", "lineage") not in env.co.matrix:
        env.row("leak_check", "lineage")
    st = dict(report_id="GA1", checks=audit_layer3(env.g), planted_cases=[{"type": "lagged label", "state": STATES[2]}],
              statement=NOT_PROOF)
    st.update(over)
    return env.ga.commit("governance_audit_reported", G("governance_audit_report", **st))


def test_audit_report_procedural_and_recomputed(env):
    report(env)
    assert all(c["result"] == "pass" for c in env.ga.reports["GA1"]["checks"].values())
    with pytest.raises(GateError, match="no scientific verdict"):
        report(env, report_id="GA2", scientific_verdict="law confirmed")
    bad = audit_layer3(env.g); bad["role_separation"] = {"result": "fail", "checked": 1, "failures": 1}
    with pytest.raises(GateError, match="recomputed from the ledger"):
        report(env, report_id="GA3", checks=bad)
    with pytest.raises(GateError, match="three states"):
        report(env, report_id="GA4", planted_cases=[{"type": "x", "state": "probably fine"}])
    with pytest.raises(GateError, match="ليس إثباتًا"):
        report(env, report_id="GA5", statement="no leak")
    with pytest.raises(GateError, match="new report_id"):
        report(env)


def test_audit_report_only_by_governance_auditor(env):
    st = dict(report_id="X", checks=audit_layer3(env.g), planted_cases=[], statement=NOT_PROOF)
    with pytest.raises(GateError, match="governance auditor"):
        env.ga.commit("governance_audit_reported", sign("aud", AK, {"action": "governance_audit_report",
                                                                    "nonce": "n1", **st}))


def test_governance_auditor_role_separation(env):
    with pytest.raises(GateError, match="governance auditor is separate"):
        env.cl.commit("role_assigned", F("assign_role", role="custody_auditor", holder="gaud"))
    with pytest.raises(GateError, match="governance auditor is separate"):
        env.cl.commit("role_assigned", F("assign_role", role="governance_auditor", holder="op"))
    with pytest.raises(GateError, match="governance auditor is separate"):
        env.cl.commit("role_assigned", F("assign_role", role="discovery_participant", holder="gaud"))


def test_governance_auditor_sees_records_only(env):                                     # ق-05
    with pytest.raises(GateError, match="refused and logged"):
        env.cl.access(request("gaud", GK, item="decryption:F1", reason="audit", family="F1"))


def test_audit_detects_a_procedural_breach():
    """A ledger written without the audit layer, then audited: the recomputed check reports the breach."""
    led = Ledger()
    cl = CustodyLayer(Vault(), identity="cust", key=CK)
    g = Governance(FK.public_key(), led, extensions=[ClaimsCharter(), cl])
    for ident, k in (("cust", CK), ("x", AK)):
        g.register_key(F("register_key", identity=ident, public_key_hex=public_hex(k.public_key())))
    cl.commit("role_assigned", F("assign_role", role="custody", holder="cust"))
    cl.commit("role_assigned", F("assign_role", role="governance_auditor", holder="x"))
    cl.commit("role_assigned", F("assign_role", role="custody_auditor", holder="x"))   # breach: not checked here
    assert audit_layer3(g)["role_separation"]["result"] == "fail"


def test_history_replays(tmp_path):
    led = tmp_path / "led" / "g.jsonl"; led.parent.mkdir()
    anc = tmp_path / "anc" / "a.jsonl"; anc.parent.mkdir()
    e = Env(Ledger(led, anchors=AnchorStore(anc)))
    e.row("court", "court")
    report(e)
    co2, ga2 = ControlsLayer(), GovernanceAuditLayer()
    Governance(FK.public_key(), Ledger(led, anchors=AnchorStore(anc)),
               extensions=[ClaimsCharter(), CustodyLayer(None), InventoryLayer(), CourtLayer(), DiscoveryLayer(), co2, ga2])
    assert ("court", "court") in co2.matrix and "GA1" in ga2.reports


# ======================= review round R1 (ChatGPT, 2026-11-17) ==================================
def test_r1_01_leak_check_needs_row_when_planted_cases_reported(env):
    st = dict(report_id="L1", checks=audit_layer3(env.g), planted_cases=[{"type": "t", "state": STATES[0]}],
              statement=NOT_PROOF)
    with pytest.raises(GateError, match="leak_check 'lineage'"):
        env.ga.commit("governance_audit_reported", G("governance_audit_report", **st))
    env.ga.commit("governance_audit_reported", G("governance_audit_report", **{**st, "planted_cases": []}))  # no use, no row
    env.row("leak_check", "lineage")
    env.ga.commit("governance_audit_reported", G("governance_audit_report", **{**st, "report_id": "L2",
                                                                               "checks": audit_layer3(env.g)}))


def test_r1_01_lens_is_not_a_tool_kind(env):
    with pytest.raises(GateError, match="tool_kind"):
        env.row("lens", "L1")


def test_r1_02_planted_types_unique_and_text(env):
    with pytest.raises(GateError, match="appears once"):
        report(env, planted_cases=[{"type": "lag", "state": STATES[0]}, {"type": "lag", "state": STATES[2]}])
    with pytest.raises(GateError, match="non-empty text"):
        report(env, planted_cases=[{"type": 5, "state": STATES[0]}])
    with pytest.raises(GateError, match="appears once"):
        report(env, planted_cases=[{"type": "lag", "state": STATES[0]}, {"type": " lag ", "state": STATES[1]}])
