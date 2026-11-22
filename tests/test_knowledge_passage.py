"""WP9-04: knowledge 10 → 7 only through layer 3 (ت-09, م-10; TP-60.10, TP-61.09). SYNTHETIC ONLY.
Builds on the full synthetic pipeline of test_integration (a recorded knowledge row K1) and adds a mind."""
import uuid

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

import test_integration as TI
from xauusd_swarm.charter import GateError, Governance
from xauusd_swarm.court_service import CustodyCourtService
from xauusd_swarm.court import PackageStore
from xauusd_swarm.identity import public_hex, sign
from xauusd_swarm.inventory import content_sha256
from xauusd_swarm.knowledge_passage import KnowledgePassageLayer
from xauusd_swarm.ledger import Ledger

MK = Ed25519PrivateKey.generate()


class SystemKP(TI.System):
    """test_integration's system with the knowledge-passage layer added to both replicas."""
    def __init__(self, led):
        self.led, self.store = led, PackageStore(key=TI.SKEY)
        self.cus = {**TI.layers(True, self.store), "kp": KnowledgePassageLayer()}
        self.gC = Governance(TI.FK.public_key(), led, extensions=[self.cus[k] for k in TI.ORDER + ("kp",)])
        self.svc = CustodyCourtService(self.gC, self.store, identity="cust", key=TI.CK)
        self.crt = {**TI.layers(False), "kp": KnowledgePassageLayer()}
        self.gO = None

    def court_replica(self):
        self.gO = Governance(TI.FK.public_key(), self.led, extensions=[self.crt[k] for k in TI.ORDER + ("kp",)])
        return self.crt


def lineage(seen):
    return {"data": {"source": "synthetic", "transforms": [], "block_usage": [], "exclusions": [],
                     "blinding_state": "blinded", "availability_time_source": "مرصود"},
            "environment": {"libraries": [], "environment": "wp801", "seeds": [1], "training_settings": {}},
            "hypothesis": {"versions_branches_edits": [], "epistemic_path": "as given"},
            "experiments": {"stopped_or_incomplete": [], "exclusion_reasons": []},
            "knowledge": {"seen": seen, "tools": [], "touched_gold_or_R_info": False, "llm_in_lineage": False,
                          "blinding_breach_events": []}}


@pytest.fixture
def sysm():
    s = SystemKP(Ledger())
    ruling = TI.run_pipeline(s)
    c = s.cus
    s.gC.register_key(TI.F("register_key", identity="m1", public_key_hex=public_hex(MK.public_key())))
    c["cl"].commit("role_assigned", TI.F("assign_role", role="discovery_participant", holder="m1"))
    s.row("path", "P-dist")
    doc = lambda t: {"text": t, "sha256": content_sha256(t)}        # noqa: E731
    c["dl"].commit("path_registered", TI.F("register_path", path_id="P-dist", kind="distributional_regularities",
                   card=doc("card"), generalisation_test=doc("gen"), designers_without_sealed_access=True,
                   lineage_sha256=TI.H))
    c["dl"].commit("resource_rule_frozen", TI.F("freeze_resource_rule", family="F1", rule="equal_compute_time",
                   compute_seconds=3600))
    s.row("engine", "kde")
    c["dl"].commit("mind_registered", TI.F("register_mind", mind_id="m1", family="F1", config={
        "representations": ["r"], "engines": [{"name": "kde", "kind": "engine"}], "statistics_and_nulls": ["N-a"],
        "experiment_selection": "grid", "adaptation": "none", "memory": "private",
        "permissions_and_resources": {"compute_seconds": 3600}}))
    s.ruling = ruling
    return s


def C(action, **kw):
    return sign("cust", TI.CK, {"action": action, "nonce": uuid.uuid4().hex, **kw})


def propose(s, pid, seen):
    return s.cus["dl"].commit("proposal_submitted", sign("m1", MK, {"action": "propose", "nonce": uuid.uuid4().hex,
                              "proposal_id": pid, "type": "hypothesis", "family": "F1", "path_id": "P-dist",
                              "content_sha256": TI.H, "lineage": lineage(seen)}))


def passage(s, **kw):
    rec = s.cus["kr"].records[-1]
    base = {"ruling_id": rec["ruling_id"], "claim_id": rec["claim_id"], "mind_id": "m1", "recipient_path": "Z",
            "classification": rec["classification"], "zero_prior": rec["zero_prior"], "blinded": True}
    base.update(kw)
    return s.cus["kp"].commit("knowledge_passage_recorded", C("record_knowledge_passage", **base))


def ref(s):
    rec = s.cus["kr"].records[-1]
    return f"knowledge:{rec['ruling_id']}/{rec['claim_id']}"


def test_m10_knowledge_without_passage_refused(sysm):                         # TP-60.10
    with pytest.raises(GateError, match="without passing through layer 3"):
        propose(sysm, "p1", [ref(sysm)])
    propose(sysm, "p0", ["some paper (not a knowledge row)"])                  # other 'seen' items unaffected


def test_t09_passage_then_use_accepted(sysm):                                  # TP-61.09
    passage(sysm)
    propose(sysm, "p1", [ref(sysm)])
    assert ("p1" in sysm.cus["dl"].proposals)


def test_t09_tags_copied_blinding_to_z_custody_only(sysm):
    with pytest.raises(GateError, match="copied from the recorded row"):
        passage(sysm, zero_prior="ZERO-PRIOR محقق")
    with pytest.raises(GateError, match="blinded"):
        passage(sysm, blinded=False)
    with pytest.raises(GateError, match="registered mind"):
        passage(sysm, mind_id="m9")
    with pytest.raises(GateError, match="no recorded knowledge row"):
        passage(sysm, claim_id="K9")
    with pytest.raises(GateError, match="custody"):
        rec = sysm.cus["kr"].records[-1]
        sysm.cus["kp"].commit("knowledge_passage_recorded", sign("op", TI.OK, {
            "action": "record_knowledge_passage", "nonce": uuid.uuid4().hex, "ruling_id": rec["ruling_id"],
            "claim_id": rec["claim_id"], "mind_id": "m1", "recipient_path": "Z",
            "classification": rec["classification"], "zero_prior": rec["zero_prior"], "blinded": True}))
    passage(sysm, recipient_path="R", blinded=False)                           # not Z: blinding not required


@pytest.mark.parametrize("seen", ["knowledge:R/K1", {"knowledge:R/K1": 1}, None, 5, [5], [["x"]]])
def test_r1_01_malformed_seen_is_refused_not_ignored(sysm, seen):
    with pytest.raises(GateError):
        sysm.cus["dl"].commit("proposal_submitted", sign("m1", MK, {"action": "propose", "nonce": uuid.uuid4().hex,
                              "proposal_id": "px", "type": "hypothesis", "family": "F1", "path_id": "P-dist",
                              "content_sha256": TI.H, "lineage": lineage(seen)}))


@pytest.mark.parametrize("variant", ["Knowledge:{r}/{c}", " knowledge :{r}/{c}", "knowledge：{r}/{c}",
                                     "knowledge:{r}/{c}/extra", "knowledge:{r}"])
def test_r1_01_variant_spellings_refused(sysm, variant):
    rec = sysm.cus["kr"].records[-1]
    passage(sysm)
    with pytest.raises(GateError):
        propose(sysm, "pv", [variant.format(r=rec["ruling_id"], c=rec["claim_id"])])
    propose(sysm, "pok", [ref(sysm)])                                    # the exact form still passes
