"""Layer 7 tests (WP8-07): paths, minds, channels, proposals, discovery queue. SYNTHETIC ONLY.
Test-plan items: TP-63 (channels; no access before freezing), TP-60.08 / TP-60.09 (no unblinded data
to a language mind: a mind cannot obtain a decryption), TP-60.12 (code-integrity results never enter
the queue), TP-60.18, TP-60.19 (refused and logged), TP-61.10 (ت-10 under its condition),
TP-61.16 (ت-16: queue → test interface, eligibility of ق-03; order independence by re-running).
"""
import copy
import uuid

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from xauusd_swarm.charter import GateError, Governance
from xauusd_swarm.claims import ClaimsCharter
from xauusd_swarm.court import CourtLayer
from xauusd_swarm.custody import CustodyLayer, Vault, request as access_request
from xauusd_swarm.discovery import (LANGUAGE, ENGINES, NOT_EVIDENCE, UNVERIFIABLE, DiscoveryLayer, process_batch,
                                    queue_order)
from xauusd_swarm.identity import AuthError, public_hex, sign
from xauusd_swarm.inventory import content_sha256
from xauusd_swarm.ledger import AnchorStore, Ledger

FK, CK, AK, OK = (Ed25519PrivateKey.generate() for _ in range(4))
MK = {m: Ed25519PrivateKey.generate() for m in ("m1", "m2", "m3", "m4")}
H = "ab" * 32


def F(action, **kw):
    return sign("founder", FK, {"action": action, "nonce": uuid.uuid4().hex, **kw})


def M(mind, action, **kw):
    return sign(mind, MK[mind], {"action": action, "nonce": uuid.uuid4().hex, **kw})


def doc(text):
    return {"text": text, "sha256": content_sha256(text)}


def config(llm=False, rep="log_returns", secs=3600):
    return {"representations": [rep], "engines": [{"name": "lm-x" if llm else "kde", "kind": "llm" if llm else "engine"}],
            "statistics_and_nulls": ["N-a"], "experiment_selection": "grid over windows", "adaptation": "none",
            "memory": "private", "permissions_and_resources": {"compute_seconds": secs}}


def lineage(llm=False):
    return {"data": {"source": "synthetic", "transforms": [], "block_usage": [], "exclusions": [], "blinding_state": "blinded",
                     "availability_time_source": "مرصود"},
            "environment": {"libraries": [], "environment": "wp801", "seeds": [1], "training_settings": {}},
            "hypothesis": {"versions_branches_edits": [], "epistemic_path": "as given"},
            "experiments": {"stopped_or_incomplete": [], "exclusion_reasons": []},
            "knowledge": {"seen": [], "tools": [], "touched_gold_or_R_info": False, "llm_in_lineage": llm,
                          "blinding_breach_events": []}}


class Env:
    def __init__(self, ledger=None, minds=(("m1", False), ("m2", True))):
        self.cl = CustodyLayer(Vault(), identity="cust", key=CK)
        self.cc, self.ct = ClaimsCharter(), CourtLayer()
        self.dl = DiscoveryLayer(guard_identity="op", guard_key=OK)
        self.g = Governance(FK.public_key(), ledger if ledger is not None else Ledger(),
                            extensions=[self.cc, self.cl, self.ct, self.dl])
        for ident, k in (("cust", CK), ("aud", AK), ("op", OK), *((m, MK[m]) for m in MK)):
            self.g.register_key(F("register_key", identity=ident, public_key_hex=public_hex(k.public_key())))
        for role, h in (("custody", "cust"), ("custody_auditor", "aud"), ("court_operator", "op"),
                        *(("discovery_participant", m) for m in MK)):
            self.cl.commit("role_assigned", F("assign_role", role=role, holder=h))
        self.g.set_initial_charter(F("charter_initial", charter="project", text="P"))
        self.g.set_initial_charter(F("charter_initial", charter="claims", text="C"))
        self.dl.commit("path_registered", F("register_path", path_id="P-dist", kind="distributional_regularities",
                                            card=doc("card"), generalisation_test=doc("gen test"),
                                            designers_without_sealed_access=True, lineage_sha256=H))
        self.dl.commit("resource_rule_frozen", F("freeze_resource_rule", family="F1", rule="equal_compute_time",
                                                 compute_seconds=3600))
        for i, (m, llm) in enumerate(minds):
            self.dl.commit("mind_registered", F("register_mind", mind_id=m, family="F1",
                                                config=config(llm=llm, rep=f"rep{i}")))

    def propose(self, mind, pid, typ="hypothesis", **kw):
        llm = self.dl.minds[mind]["class"] == LANGUAGE
        st = dict(proposal_id=pid, type=typ, family="F1", path_id="P-dist", content_sha256=H, lineage=lineage(llm))
        st.update(kw)
        return self.dl.commit("proposal_submitted", M(mind, "propose", **st))

    def queue(self, lo=1, hi=5, keys=None):
        self.dl.commit("queue_rules_frozen", F("freeze_queue_rules", family="F1",
                                               keys=keys or [{"key": "admission_index", "direction": "asc"}]))
        self.dl.commit("queue_batch_declared", F("declare_queue_batch", batch_id="B1", family="F1",
                                                 min_items=lo, max_items=hi))

    def claim(self, cid):
        self.cc.register(F("register_claim", card={"claim_id": cid, "version": 1, "tags": ["الموقع"], "category": None,
                                                   "path": "أ", "uses_events": False, "scope_type": "stable", "scope": "s",
                                                   "rulings": {"existence": "e", "size_with_uncertainty": "s",
                                                               "importance": "i"}}))
        self.ct.commit("claim_identity_registered", F("register_claim_identity", claim_id=cid, identity={
            "target_quantity": f"q-{cid}", "eligible_data_scope": "synthetic", "time_scope_type": "stable",
            "proof_path": "أ", "direction_or_threshold": ">0", "observation_precision": "n/a", "price_series": "Mid"}))


@pytest.fixture
def env():
    return Env()


# ======================= paths (س 751–758; ق-26) ===============================================
def test_path_needs_card_test_lineage(env):
    base = dict(path_id="P2", kind="conditional_information", card=doc("c"), generalisation_test=doc("g"),
                designers_without_sealed_access=True, lineage_sha256=H)
    for k, v, msg in (("card", {"text": "c", "sha256": H}, "card"), ("generalisation_test", {"text": ""}, "generalisation"),
                      ("designers_without_sealed_access", False, "sealed worlds"), ("lineage_sha256", "x", "lineage"),
                      ("kind", "magic", "list is open")):
        with pytest.raises(GateError, match=msg):
            env.dl.commit("path_registered", F("register_path", **{**base, k: v}))
    env.dl.commit("path_registered", F("register_path", **base))
    env.dl.commit("path_registered", F("register_path", **{**base, "path_id": "P3", "kind": "other"}))   # list is open


# ======================= minds (ق-15 … ق-17, ق-20; م7-13) =====================================
def test_classification_is_derived(env):
    assert env.dl.minds["m1"]["class"] == ENGINES and env.dl.minds["m2"]["class"] == LANGUAGE
    with pytest.raises(GateError, match="derived"):
        env.dl.commit("mind_registered", F("register_mind", mind_id="m3", family="F1", config=config(rep="r3"),
                                           classification=ENGINES))


def test_mind_configuration_rules(env):
    bad = config(rep="r3"); bad.pop("adaptation")
    with pytest.raises(GateError, match="seven components"):
        env.dl.commit("mind_registered", F("register_mind", mind_id="m3", family="F1", config=bad))
    bad = config(rep="r3"); bad["experiment_selection"] = ""
    with pytest.raises(GateError, match="experiment selection"):
        env.dl.commit("mind_registered", F("register_mind", mind_id="m3", family="F1", config=bad))
    with pytest.raises(GateError, match="equal compute time"):
        env.dl.commit("mind_registered", F("register_mind", mind_id="m3", family="F1", config=config(rep="r3", secs=99)))
    with pytest.raises(GateError, match="diversity"):
        env.dl.commit("mind_registered", F("register_mind", mind_id="m3", family="F1", config=config(rep="rep0")))
    with pytest.raises(GateError, match="resource rule is frozen first"):
        env.dl.commit("mind_registered", F("register_mind", mind_id="m3", family="F2", config=config(rep="r3")))
    with pytest.raises(GateError, match="registered identity"):
        env.dl.commit("mind_registered", F("register_mind", mind_id="ghost", family="F1", config=config(rep="r9")))


def test_resource_rule_frozen_before_minds_and_once(env):
    with pytest.raises(GateError, match="one frozen resource rule"):
        env.dl.commit("resource_rule_frozen", F("freeze_resource_rule", family="F1", rule="equal_compute_time",
                                                compute_seconds=10))
    env.dl.commit("resource_rule_frozen", F("freeze_resource_rule", family="F2", rule="equal_compute_time",
                                            compute_seconds=10))
    with pytest.raises(GateError, match="equal compute"):
        env.dl.commit("resource_rule_frozen", F("freeze_resource_rule", family="F3", rule="by_merit", compute_seconds=10))


def test_mind_role_separation(env):
    with pytest.raises(GateError, match="no custody, court"):
        env.cl.commit("role_assigned", F("assign_role", role="gz_operator", holder="m1"))
    with pytest.raises(GateError, match="discovery_participant"):
        Env(minds=()).dl.commit("mind_registered", F("register_mind", mind_id="op", family="F1", config=config()))


def test_model_and_dna_swaps(env):
    cfg = copy.deepcopy(env.dl.minds["m1"]["config"])
    cfg["engines"] = [{"name": "lm-y", "kind": "llm"}]
    env.dl.commit("mind_reconfigured", F("reconfigure_mind", mind_id="m1", swap="model", config=cfg))
    assert env.dl.minds["m1"]["class"] == LANGUAGE and len(env.dl.minds["m1"]["versions"]) == 2
    cfg2 = copy.deepcopy(cfg); cfg2["adaptation"] = "bandit"; cfg2["engines"] = [{"name": "kde", "kind": "engine"}]
    with pytest.raises(GateError, match="component 2"):
        env.dl.commit("mind_reconfigured", F("reconfigure_mind", mind_id="m1", swap="model", config=cfg2))
    with pytest.raises(GateError, match="other than the engines"):
        env.dl.commit("mind_reconfigured", F("reconfigure_mind", mind_id="m1", swap="dna", config=cfg2,
                                             changed=["adaptation", "engines"]))
    cfg3 = copy.deepcopy(cfg); cfg3["adaptation"] = "bandit"
    with pytest.raises(GateError, match="exactly what changed"):
        env.dl.commit("mind_reconfigured", F("reconfigure_mind", mind_id="m1", swap="dna", config=cfg3, changed=[]))
    env.dl.commit("mind_reconfigured", F("reconfigure_mind", mind_id="m1", swap="dna", config=cfg3, changed=["adaptation"]))


def test_panel_consumed_once(env):
    env.dl.commit("panel_consumed", F("consume_panel", panel_id="PN1", decision_ref="family F1 report",
                                      configurations=[content_sha256(env.dl.minds["m1"]["config"])]))
    with pytest.raises(GateError, match="one decision only"):
        env.dl.commit("panel_consumed", F("consume_panel", panel_id="PN1", decision_ref="again",
                                          configurations=[content_sha256(env.dl.minds["m1"]["config"])]))
    with pytest.raises(GateError, match="recorded mind configurations"):                 # S1-02
        env.dl.commit("panel_consumed", F("consume_panel", panel_id="PN2", decision_ref="d", configurations=[H]))


# ======================= channels and freezing (م-04; TP-63, TP-60.18, TP-60.19) ===============
def test_exchange_only_through_registered_channel_and_logged(env):
    n = len(env.dl.refusals)
    with pytest.raises(GateError, match="registered channel"):
        env.dl.guarded("exchange_recorded", M("m1", "exchange", channel_id="C1", to="m2", content_type="other",
                                              content_sha256=H))
    assert len(env.dl.refusals) == n + 1                                   # refused AND logged (TP-60.19)
    env.dl.commit("channel_registered", F("register_channel", channel_id="C1", mind_a="m1", mind_b="m2"))
    env.dl.guarded("exchange_recorded", M("m1", "exchange", channel_id="C1", to="m2", content_type="other",
                                          content_sha256=H))
    assert env.dl.exchanges[-1]["from"] == "m1"                           # each use is a ledger event


def test_no_hypotheses_before_own_freeze(env):
    env.dl.commit("channel_registered", F("register_channel", channel_id="C1", mind_a="m1", mind_b="m2"))
    with pytest.raises(GateError, match="before freezing"):
        env.dl.guarded("exchange_recorded", M("m1", "exchange", channel_id="C1", to="m2", content_type="hypothesis",
                                              content_sha256=H))
    assert env.dl.refusals and "before freezing" in env.dl.refusals[-1]["reason"]     # TP-60.18
    env.dl.commit("hypothesis_frozen", M("m2", "freeze_hypothesis", family="F1", hypothesis_sha256=H))
    env.dl.guarded("exchange_recorded", M("m1", "exchange", channel_id="C1", to="m2", content_type="result",
                                          content_sha256=H))


def test_forged_refusal_log_rejected(env):
    env.dl.commit("channel_registered", F("register_channel", channel_id="C1", mind_a="m1", mind_b="m2"))
    ok = M("m1", "exchange", channel_id="C1", to="m2", content_type="other", content_sha256=H)
    with pytest.raises(GateError, match="not a refusal"):
        env.dl.commit("l7_refusal_logged", env.dl._gsign({"action": "l7_refusal", "reason": "x",
                                                          "attempt": {"kind": "exchange_recorded", "payload": ok.to_payload()}}))


def test_mind_cannot_obtain_decryption(env):                                             # TP-60.08, TP-60.09
    with pytest.raises(GateError, match="refused and logged"):
        env.cl.access(access_request("m2", MK["m2"], item="decryption:F1", reason="peek", family="F1"))
    assert env.cl.access_log[-1]["outcome"] == "refused" and env.cl.access_log[-1]["requester"] == "m2"


# ======================= proposals (س 769–778; م7-08) =========================================
def test_language_mind_outputs_tagged_unverifiable(env):
    env.propose("m2", "p1")
    env.propose("m1", "p2")
    assert UNVERIFIABLE in env.dl.proposals["p1"]["tags"] and UNVERIFIABLE not in env.dl.proposals["p2"]["tags"]


def test_distinguisher_proposals_are_not_evidence(env):
    env.dl.commit("path_registered", F("register_path", path_id="P-dx", kind="distinguisher", card=doc("c"),
                                       generalisation_test=doc("g"), designers_without_sealed_access=True, lineage_sha256=H))
    env.propose("m1", "p1", path_id="P-dx")
    assert NOT_EVIDENCE in env.dl.proposals["p1"]["tags"]


def test_language_falsification_needs_null_model_and_accepted_card(env):
    with pytest.raises(GateError, match="null model"):
        env.propose("m2", "f1", typ="falsification")
    env.propose("m2", "f1", typ="falsification", null_model="N-b")
    assert env.dl.proposals["f1"]["adopted"] is False                     # recorded, not adopted
    with pytest.raises(GateError, match="every declared field"):
        env.dl.commit("null_card_accepted", F("accept_null_card", null_model="N-b", card={"assumptions": ""}))
    env.dl.commit("null_card_accepted", F("accept_null_card", null_model="N-b", card={"assumptions": "iid blocks"}))
    env.propose("m2", "f2", typ="falsification", null_model="N-b")
    assert env.dl.proposals["f2"]["adopted"] is True
    env.propose("m1", "f3", typ="falsification")                         # engines: no null condition (✓)
    assert env.dl.proposals["f3"]["adopted"] is True


def test_proposal_eligibility(env):
    with pytest.raises(GateError, match="registered discovery path"):
        env.propose("m1", "p1", path_id="nope")
    bad = lineage(); bad["data"].pop("source")
    with pytest.raises(GateError, match="full lineage"):
        env.propose("m1", "p1", lineage=bad)
    with pytest.raises(GateError, match="language model is in it"):
        env.propose("m2", "p1", lineage=lineage(False))
    with pytest.raises(GateError, match="own family"):
        env.propose("m1", "p1", family="F9")
    with pytest.raises(GateError, match="not a registered mind"):
        env.dl.commit("proposal_submitted", F("propose", proposal_id="x", type="hypothesis", family="F1",
                                              path_id="P-dist", content_sha256=H, lineage=lineage()))


# ======================= queue (ق-03, ق-29; م7-07; ت-16; TP-60.12, TP-61.16) =================
def test_queue_guard_is_court_operator_only(env):
    env.queue()
    env.propose("m1", "p1")
    with pytest.raises(GateError, match="court operator"):
        env.dl.commit("queue_entry_admitted", M("m1", "queue_admit", proposal_id="p1", batch_id="B1"))


def test_code_integrity_results_never_enter_queue(env):
    env.queue()
    env.propose("m1", "p1", code_integrity_only=True)
    n = len(env.dl.refusals)
    st = env.dl._gsign({"action": "queue_admit", "proposal_id": "p1", "batch_id": "B1"})
    with pytest.raises(GateError, match="code integrity"):
        env.dl.guarded("queue_entry_admitted", st)
    assert len(env.dl.refusals) == n + 1                                    # TP-60.12: refused and logged


def test_queue_only_candidates_and_adopted(env):
    env.queue()
    env.propose("m1", "q1", typ="question")
    with pytest.raises(GateError, match="candidate discoveries"):
        env.dl.admit("q1", "B1")
    env.propose("m2", "f1", typ="falsification", null_model="N-z")
    with pytest.raises(GateError, match="not adopted"):
        env.dl.admit("f1", "B1")


def test_batch_bounds_and_freeze_before_test(env):
    env.queue(lo=2, hi=3)
    for i in range(4):
        env.propose("m1" if i % 2 else "m2", f"p{i}")
    env.dl.admit("p0", "B1")
    env.claim("K1")
    with pytest.raises(GateError, match="lower bound"):
        env.dl.close_batch("B1")
    with pytest.raises(GateError, match="closed batch"):
        env.dl.release("p0", "K1", "Z")
    env.dl.admit("p1", "B1"); env.dl.admit("p2", "B1")
    with pytest.raises(GateError, match="upper bound"):
        env.dl.admit("p3", "B1")
    env.dl.close_batch("B1")
    with pytest.raises(GateError, match="closed"):
        env.dl.admit("p3", "B1")
    env.dl.release("p0", "K1", "Z")
    with pytest.raises(GateError, match="released once"):
        env.dl.release("p0", "K1", "Z")


def test_order_only_by_frozen_rule(env):
    env.queue(keys=[{"key": "mind_id", "direction": "desc"}, {"key": "admission_index", "direction": "asc"}])
    for pid, m in (("a", "m1"), ("b", "m2"), ("c", "m1")):
        env.propose(m, pid)
        env.dl.admit(pid, "B1")
    assert env.dl.order("B1") == ["b", "a", "c"]
    forged = env.dl._gsign({"action": "queue_close", "batch_id": "B1", "order": ["a", "b", "c"]})
    with pytest.raises(GateError, match="computed by the frozen rule"):
        env.dl.commit("queue_batch_closed", forged)
    env.dl.close_batch("B1")
    assert env.dl.batches["B1"]["order"] == ["b", "a", "c"]
    with pytest.raises(GateError, match="one frozen queue rule"):
        env.dl.commit("queue_rules_frozen", F("freeze_queue_rules", family="F1", keys=[{"key": "proposal_id", "direction": "asc"}]))


def test_release_interface_t16(env):                                                        # TP-61.16
    env.queue()
    env.propose("m1", "p1")
    env.dl.admit("p1", "B1")
    env.dl.close_batch("B1")
    with pytest.raises(GateError, match="registered claim"):
        env.dl.release("p1", "K-none", "Z")
    env.claim("K1")
    bad = env.dl._gsign({"action": "queue_release", "proposal_id": "p1", "claim_id": "K1", "path": "Z",
                         "lineage_sha256": content_sha256(env.dl.proposals["p1"]["lineage"]),
                         "type_registration": {"type": "hypothesis", "path_id": "P-dist"}, "accepted": True})
    with pytest.raises(GateError, match="not scientific acceptance"):
        env.dl.commit("queue_released", bad)
    with pytest.raises(GateError, match="Z, G-Z or R"):
        env.dl.release("p1", "K1", "Q")
    env.dl.release("p1", "K1", "Z")
    r = env.dl.released["p1"]
    assert set(r) == {"action", "nonce", "proposal_id", "claim_id", "path", "lineage_sha256", "type_registration"}


def test_results_independent_of_processing_order():
    items = [{"proposal_id": f"p{i}", "x": i} for i in range(20)]
    assert process_batch(items, lambda it: it["x"] ** 2)[ "p3"] == 9
    state = {"n": 0}

    def order_dependent(it):
        state["n"] += 1
        return state["n"]
    with pytest.raises(GateError, match="processing order"):
        process_batch(items, order_dependent)


def test_queue_order_function_deterministic():
    es = [{"proposal_id": p, "admission_index": i, "path_id": "P", "mind_id": m} for i, (p, m) in
          enumerate((("x", "m2"), ("y", "m1"), ("z", "m2")))]
    rule = {"keys": [{"key": "mind_id", "direction": "asc"}]}
    assert queue_order(es, rule) == ["y", "x", "z"] == queue_order(list(reversed(es)), rule)


def test_instances_per_mind_reported(env):
    env.queue()
    env.propose("m1", "p1"); env.propose("m2", "p2")
    env.dl.admit("p1", "B1"); env.dl.admit("p2", "B1")
    env.dl.close_batch("B1")
    env.claim("K1"); env.claim("K2")
    env.dl.release("p1", "K1", "Z"); env.dl.release("p2", "K2", "Z")
    for tid, cid in (("T1", "K1"), ("T2", "K1"), ("T3", "K2")):
        env.ct.commit("test_instance_registered", F("register_test_instance", test_instance_id=tid, claim_id=cid,
                      statistic="mean", procedure="t", null="N0", slice="S1", seeds="1", code_version="v1",
                      representation_id="r", transform_version="t1", price_series="Mid",
                      path="R" if tid == "T2" else "Z", role="primary", null_card_accepted=True))
    assert env.dl.instances_per_mind("F1") == {"m1": 2, "m2": 1}


# ======================= replay ================================================================
def test_history_replays(tmp_path):
    led = tmp_path / "led" / "g.jsonl"; led.parent.mkdir()
    anc = tmp_path / "anc" / "a.jsonl"; anc.parent.mkdir()
    e = Env(Ledger(led, anchors=AnchorStore(anc)))
    e.queue()
    e.propose("m1", "p1")
    e.dl.admit("p1", "B1")
    e.dl.commit("channel_registered", F("register_channel", channel_id="C1", mind_a="m1", mind_b="m2"))
    with pytest.raises(GateError):
        e.dl.guarded("exchange_recorded", M("m1", "exchange", channel_id="C1", to="m2", content_type="hypothesis",
                                            content_sha256=H))
    dl2 = DiscoveryLayer()
    Governance(FK.public_key(), Ledger(led, anchors=AnchorStore(anc)),
               extensions=[ClaimsCharter(), CustodyLayer(None), CourtLayer(), dl2])
    assert dl2.minds.keys() == e.dl.minds.keys() and dl2.entries.keys() == {"p1"} and len(dl2.refusals) == 1


def test_minds_cannot_set_thresholds_or_rule(env):                                 # س 774, 776 (✗ for minds)
    cfg = {"structure": "A", "alpha_total": 0.5, "error_measure": "FWER", "procedure": "holm", "validity_reason": "x"}
    with pytest.raises((GateError, AuthError)):
        env.ct.commit("court_frozen", M("m1", "freeze_court", family="F1", config=cfg))
    with pytest.raises((GateError, AuthError)):
        env.g._commit("court_ruling", M("m2", "court_ruling", family="F1").to_payload())


# ======================= review round R1 (ChatGPT, 2026-11-17) ==================================
def test_r1_01_accepted_null_card_is_never_replaced(env):
    env.dl.commit("null_card_accepted", F("accept_null_card", null_model="N-b", card={"assumptions": "iid blocks"}))
    env.propose("m2", "f1", typ="falsification", null_model="N-b")
    sha1 = env.dl.proposals["f1"]["null_card_sha256"]
    with pytest.raises(GateError, match="never replaced"):
        env.dl.commit("null_card_accepted", F("accept_null_card", null_model="N-b", card={"assumptions": "changed"}))
    assert env.dl.null_cards["N-b"]["card"] == {"assumptions": "iid blocks"}
    with pytest.raises(GateError, match="supersedes names"):
        env.dl.commit("null_card_accepted", F("accept_null_card", null_model="N-b2", card={"a": "x"}, supersedes="N-zz"))
    env.dl.commit("null_card_accepted", F("accept_null_card", null_model="N-b2", card={"assumptions": "revised"},
                                          supersedes="N-b"))
    env.propose("m2", "f2", typ="falsification", null_model="N-b")
    assert env.dl.proposals["f2"]["null_card_sha256"] == sha1                # still bound to the card accepted then


@pytest.mark.parametrize("card", [{"assumptions": {"distribution": ""}}, {"a": ["x", ""]}, {"a": [{}]},
                                  {"a": {"b": {"c": None}}}, {"a": "   "}, {"a": float("nan")}, {"": "x"},
                                  {"a": []}, {}])
def test_r1_02_null_card_completeness_at_every_depth(env, card):
    with pytest.raises(GateError, match="every depth|NaN / inf"):        # NaN refused by the statement guard
        env.dl.commit("null_card_accepted", F("accept_null_card", null_model="N-x", card=card))


def test_r1_02_nested_complete_card_accepted(env):
    env.dl.commit("null_card_accepted", F("accept_null_card", null_model="N-x", card={
        "assumptions": {"distribution": "block bootstrap", "blocks": [5, 10]}, "controls": ["c1"], "seed": 0}))


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), -1, 0, True])
def test_r1_03_compute_seconds_finite_positive(env, bad):
    with pytest.raises(GateError, match="finite positive|NaN / inf"):   # NaN/inf refused by the statement guard
        env.dl.commit("resource_rule_frozen", F("freeze_resource_rule", family="F7", rule="equal_compute_time",
                                                compute_seconds=bad))


def test_s1_01_mind_compute_seconds_not_bool(env):
    env.dl.commit("resource_rule_frozen", F("freeze_resource_rule", family="F8", rule="equal_compute_time",
                                            compute_seconds=1))
    cfg = config(rep="r8"); cfg["permissions_and_resources"] = {"compute_seconds": True}
    with pytest.raises(GateError, match="equal compute time"):
        env.dl.commit("mind_registered", F("register_mind", mind_id="m3", family="F8", config=cfg))
