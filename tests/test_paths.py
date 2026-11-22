"""Stage 9 G1 / WP9-01 flows and WP9-04 (path part): Z, G-Z, R. SYNTHETIC ONLY.

Allowed flows tested: ت-03 (blinded input to Z), ت-04 (Z output through custody), ت-05 (Z → G-Z),
ت-06 (Z → R), ت-07 (R → Z through layer (أ) only), ت-18 (G-Z / R → layer 10 with mandatory fields).
Forbidden flows tested: م-03 (Z gets non-blinded input), م-04 (Z calls a «تداول» tool), م-05 (R → Z
outside layer (أ)), م-06 (Z output to anyone before custody); undrawn flows (G-Z → Z, G-Z ↔ R).
"""
import hashlib
import uuid

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from xauusd_swarm.charter import GateError, Governance
from xauusd_swarm.claims import ClaimsCharter
from xauusd_swarm.custody import LEAK_SCOPE, CustodyLayer, Vault
from xauusd_swarm.identity import AuthError, public_hex, sign
from xauusd_swarm.ledger import AnchorStore, Ledger
from xauusd_swarm.paths import GOLD, NO_CLAIM, PRIVATE, PathsLayer

FK, CK, DK, ZK = (Ed25519PrivateKey.generate() for _ in range(4))
KEYS = {"cust": CK, "disc": DK, "gz": ZK}


def S(ident, action, **kw):
    return sign(ident, FK if ident == "founder" else KEYS[ident], {"action": action, "nonce": uuid.uuid4().hex, **kw})


def h(x: str) -> str:
    return hashlib.sha256(x.encode()).hexdigest()


class Env:
    def __init__(self, ledger=None):
        self.cl, self.cc, self.pl = CustodyLayer(Vault(), identity="cust", key=CK), ClaimsCharter(), PathsLayer()
        self.g = Governance(FK.public_key(), ledger if ledger is not None else Ledger(),
                            extensions=[self.cc, self.cl, self.pl])
        for i, k in KEYS.items():
            self.g.register_key(S("founder", "register_key", identity=i, public_key_hex=public_hex(k.public_key())))
        for role, hd in (("custody", "cust"), ("discovery_participant", "disc"), ("gz_operator", "gz")):
            self.cl.commit("role_assigned", S("founder", "assign_role", role=role, holder=hd))
        self.g.set_initial_charter(S("founder", "charter_initial", charter="project", text="P"))
        self.g.set_initial_charter(S("founder", "charter_initial", charter="claims", text="C"))
        com = self.cl.vault.set_params("F1", c=1, a=1, b=0, m=3)
        self.cl.commit("params_fixed", S("cust", "params_fixed", family="F1", params_commitment=com, delta=0.01))
        self.cl.commit("custody_decision", S("cust", "custody_decision", slice="D1", family="F1", boundaries="b",
                                             delta=0.01, params_commitment=com))

    def blinded(self, iid, content, slice_="D1"):
        return self.pl.commit("z_input_admitted", S("cust", "admit_z_input", input_id=iid, source="blinding",
                              slice=slice_, representation_id="log_returns", content_sha256=h(content)))

    def z_output_passes(self, content):
        self.cl.commit("z_output_passed", S("cust", "z_output_passed", output_sha256=h(content),
                                            reviewed=list(LEAK_SCOPE), passed=True))

    def transfer(self, a, b, content):
        return self.pl.commit("path_transfer_recorded", S("cust", "record_path_transfer", **{"from": a, "to": b},
                              item_sha256=h(content)))

    def r_message(self, content="rule text", gold=False, **kw):
        """An R → layer-10 message (ت-18); returns its hash (the origin of a layer (أ) item)."""
        if "observation" not in self.pl.msg_types:
            self.pl.commit("l10_message_type_registered", S("founder", "register_l10_message_type",
                           type="observation", required_fields=["summary", "lineage"]))
        self.pl.commit("l10_message_recorded", S("founder", "send_l10_message", **{"from": "R"}, type="observation",
                       claim_id=NO_CLAIM, gold_observation=gold, fields={"summary": content, "lineage": "L"}, **kw))
        return PathsLayer.message_sha256(self.pl.messages[-1])

    def item_a(self, iid, kind="قاعدة رياضية", content="rule text", origin=None, **kw):
        o = origin or self.r_message(content)
        return self.pl.commit("knowledge_a_registered", S("founder", "register_knowledge_a", item_id=iid, kind=kind,
                              content_sha256=kw.pop("content_sha256", o), origin_message_sha256=o, **kw))


@pytest.fixture
def env():
    return Env()


# ---------------- ت-03 / م-03: what enters Z ----------------
def test_z_receives_only_blinded_or_layer_a(env):
    env.blinded("I1", "blinded block 1")                                         # ت-03
    with pytest.raises(GateError, match="only blinded representations or layer"):
        env.pl.commit("z_input_admitted", S("cust", "admit_z_input", input_id="I2", source="raw",
                                            content_sha256=h("raw prices")))      # م-03
    with pytest.raises(GateError, match="custody decision"):
        env.blinded("I3", "blinded block 2", slice_="D9")                          # blinding before access
    with pytest.raises(GateError, match="signed by the custody"):
        env.pl.commit("z_input_admitted", S("disc", "admit_z_input", input_id="I4", source="blinding", slice="D1",
                                            representation_id="r", content_sha256=h("x")))
    with pytest.raises(GateError, match="closed field set"):
        env.pl.commit("z_input_admitted", S("cust", "admit_z_input", input_id="I5", source="blinding", slice="D1",
                                            representation_id="r", content_sha256=h("y"), plaintext="1.2345"))


# ---------------- ت-04 / ت-05 / ت-06 / م-06 ----------------
def test_z_outputs_reach_gz_and_r_only_through_custody(env):
    with pytest.raises(GateError, match="passes custody"):
        env.transfer("Z", "G-Z", "z result A")                                     # م-06
    env.z_output_passes("z result A")
    env.transfer("Z", "G-Z", "z result A")                                         # ت-05
    env.transfer("Z", "R", "z result A")                                           # ت-06
    assert [(t["from"], t["to"]) for t in env.pl.transfers] == [("Z", "G-Z"), ("Z", "R")]
    with pytest.raises(GateError, match="signed by the custody"):
        env.pl.commit("path_transfer_recorded", S("disc", "record_path_transfer", **{"from": "Z", "to": "R"},
                                                  item_sha256=h("z result A")))


# ---------------- م-05: R → Z refused; ت-07 through layer (أ) ----------------
def test_r_to_z_is_refused(env):
    env.z_output_passes("z result B")
    with pytest.raises(GateError, match="R → Z is forbidden"):
        env.transfer("R", "Z", "z result B")


def test_r_content_cannot_reenter_z_as_blinded_input(env):
    env.z_output_passes("z result C")
    env.transfer("Z", "R", "z result C")
    with pytest.raises(GateError, match="only through layer"):
        env.blinded("I9", "z result C")


def test_r_to_z_only_via_registered_layer_a_item(env):
    with pytest.raises(GateError, match="unregistered item"):
        env.pl.commit("z_input_admitted", S("cust", "admit_z_input", input_id="A0", source="knowledge_a",
                                            knowledge_a_id="KA1", from_path="R", content_sha256=h("rule text")))
    env.item_a("KA1")
    c = env.pl.knowledge_a["KA1"]["content_sha256"]
    with pytest.raises(GateError, match="registered layer"):
        env.pl.commit("z_input_admitted", S("cust", "admit_z_input", input_id="A1", source="knowledge_a",
                                            knowledge_a_id="KA1", from_path="R", content_sha256=h("other")))
    with pytest.raises(GateError, match="origin path R"):
        env.pl.commit("z_input_admitted", S("cust", "admit_z_input", input_id="A1", source="knowledge_a",
                                            knowledge_a_id="KA1", from_path="G-Z", content_sha256=c))
    with pytest.raises(GateError, match="closed field set"):                      # R1-02: nothing rides along
        env.pl.commit("z_input_admitted", S("cust", "admit_z_input", input_id="A1", source="knowledge_a",
                                            knowledge_a_id="KA1", from_path="R", content_sha256=c,
                                            note="extra unhashed content"))
    env.pl.commit("z_input_admitted", S("cust", "admit_z_input", input_id="A1", source="knowledge_a",
                                        knowledge_a_id="KA1", from_path="R", content_sha256=c))  # ت-07
    assert env.pl.z_inputs["A1"]["source"] == "knowledge_a"


def test_r1_01_layer_a_item_must_be_a_recorded_r_message(env):
    with pytest.raises(GateError, match="recorded R message"):                   # no R origin
        env.item_a("KA9", origin="ab" * 32)
    env.pl.commit("l10_message_type_registered", S("founder", "register_l10_message_type", type="observation",
                                                   required_fields=["summary", "lineage"]))
    env.pl.commit("l10_message_recorded", S("gz", "send_l10_message", **{"from": "G-Z"}, type="observation",
                  claim_id=NO_CLAIM, gold_observation=False, fields={"summary": "gz text", "lineage": "L"}))
    gz_hash = PathsLayer.message_sha256(env.pl.messages[-1])
    with pytest.raises(GateError, match="recorded R message"):                   # a G-Z message is not R
        env.item_a("KA9", origin=gz_hash)
    o = env.r_message("r text")
    with pytest.raises(GateError, match="is the R message it cites"):           # other content under an R origin
        env.item_a("KA9", origin=o, content_sha256=h("founder's own text"))
    env.item_a("KA9", origin=o)


def test_layer_a_kinds_and_gold_observation(env):
    with pytest.raises(GateError, match="kind is one of"):
        env.item_a("KA2", kind="فرضية")
    o = env.r_message("an observation")
    with pytest.raises(GateError, match="always «خاصة»"):
        env.item_a("KA3", kind=GOLD, origin=o)
    with pytest.raises(GateError, match="OD-10"):                                 # tagged, but gold is locked
        env.item_a("KA3", kind=GOLD, tag=PRIVATE, origin=o)
    env.item_a("KA4", kind="أداة", content="tool spec")


# ---------------- undrawn flows ----------------
@pytest.mark.parametrize("a,b", [("G-Z", "Z"), ("G-Z", "R"), ("R", "G-Z"), ("Z", "Z"), ("Z", "X")])
def test_undrawn_flows_refused(env, a, b):
    env.z_output_passes("z result D")
    with pytest.raises(GateError, match="not drawn"):
        env.transfer(a, b, "z result D")


# ---------------- م-04: tools ----------------
def test_z_cannot_call_trading_tool(env):
    env.pl.commit("path_tool_registered", S("founder", "register_path_tool", tool_id="exec", tags=["تداول"],
                                            impl_sha256="ab" * 32))
    env.pl.commit("path_tool_registered", S("founder", "register_path_tool", tool_id="stat", tags=["إحصاء"],
                                            impl_sha256="cd" * 32))
    env.pl.commit("path_tool_called", S("disc", "call_path_tool", path="Z", tool_id="stat"))
    with pytest.raises(GateError, match="«تداول»"):
        env.pl.commit("path_tool_called", S("disc", "call_path_tool", path="Z", tool_id="exec"))
    with pytest.raises(GateError, match="made by the discovery_participant"):
        env.pl.commit("path_tool_called", S("gz", "call_path_tool", path="Z", tool_id="stat"))
    env.pl.commit("path_tool_called", S("gz", "call_path_tool", path="G-Z", tool_id="exec"))   # not forbidden in G-Z


def test_refusals_are_logged_and_return_nothing(env):
    env.pl.commit("path_tool_registered", S("founder", "register_path_tool", tool_id="exec", tags=["تداول"],
                                            impl_sha256="ab" * 32))
    cust = lambda st: sign("cust", CK, {**st, "nonce": uuid.uuid4().hex})          # noqa: E731
    assert env.pl.guarded("path_tool_called", S("disc", "call_path_tool", path="Z", tool_id="exec"), cust) is None
    env.z_output_passes("z result E")
    assert env.pl.guarded("path_transfer_recorded", S("cust", "record_path_transfer", **{"from": "R", "to": "Z"},
                                                       item_sha256=h("z result E")), cust) is None
    assert len(env.pl.refusals) == 2 and "«تداول»" in env.pl.refusals[0]["reason"]
    good = S("cust", "record_path_transfer", **{"from": "Z", "to": "R"}, item_sha256=h("z result E"))
    with pytest.raises(GateError, match="not a refusal"):
        env.pl.commit("path_refusal_logged", cust({"action": "log_path_refusal", "reason": "x",
                                                   "attempt": {"kind": "path_transfer_recorded",
                                                               "payload": good.to_payload()}}))


# ---------------- ت-18: messages to layer 10 ----------------
def msg(ident, **kw):
    base = dict(type="observation", claim_id=NO_CLAIM, gold_observation=False, fields={"summary": "s", "lineage": "L1"})
    base.update(kw)
    return S(ident, "send_l10_message", **{"from": "G-Z" if ident == "gz" else "R"}, **base)


def test_l10_messages_mandatory_fields(env):
    with pytest.raises(GateError, match="not registered"):
        env.pl.commit("l10_message_recorded", msg("gz"))
    env.pl.commit("l10_message_type_registered", S("founder", "register_l10_message_type", type="observation",
                                                   required_fields=["summary", "lineage"]))
    env.pl.commit("l10_message_recorded", msg("gz"))                                         # G-Z, «لا ادعاء»
    env.pl.commit("l10_message_recorded", msg("founder"))                                    # R (founder-signed)
    with pytest.raises(GateError, match="incomplete"):
        env.pl.commit("l10_message_recorded", msg("gz", fields={"summary": "s"}))
    with pytest.raises(GateError, match="incomplete"):
        env.pl.commit("l10_message_recorded", msg("gz", fields={"summary": "", "lineage": "L"}))
    with pytest.raises(GateError, match="Claim ID or «لا ادعاء»"):
        env.pl.commit("l10_message_recorded", msg("gz", claim_id="K-unknown"))
    with pytest.raises(GateError, match="must be bool|a flag is true or false"):
        env.pl.commit("l10_message_recorded", msg("gz", gold_observation="no"))
    with pytest.raises(GateError, match="tagged «خاصة»"):
        env.pl.commit("l10_message_recorded", msg("gz", gold_observation=True))
    with pytest.raises(GateError, match="OD-10"):
        env.pl.commit("l10_message_recorded", msg("gz", gold_observation=True, tag=PRIVATE))
    with pytest.raises(GateError, match="G-Z operator"):
        env.pl.commit("l10_message_recorded", S("disc", "send_l10_message", **{"from": "G-Z"}, type="observation",
                      claim_id=NO_CLAIM, gold_observation=False, fields={"summary": "s", "lineage": "L"}))
    with pytest.raises(GateError, match="G-Z or R only"):
        env.pl.commit("l10_message_recorded", S("disc", "send_l10_message", **{"from": "Z"}, type="observation",
                      claim_id=NO_CLAIM, gold_observation=False, fields={"summary": "s", "lineage": "L"}))
    assert len(env.pl.messages) == 2


def test_l10_message_with_registered_claim(env):
    env.cc.register(S("founder", "register_claim", card={"claim_id": "K1", "version": 1, "tags": ["الموقع"],
        "category": None, "path": "أ", "uses_events": False, "scope_type": "stable", "scope": "s",
        "rulings": {"existence": "e", "size_with_uncertainty": "s", "importance": "i"}}))
    env.pl.commit("l10_message_type_registered", S("founder", "register_l10_message_type", type="observation",
                                                   required_fields=["summary", "lineage"]))
    env.pl.commit("l10_message_recorded", msg("gz", claim_id="K1"))
    assert env.pl.messages[-1]["claim_id"] == "K1"


# ---------------- replay ----------------
def test_paths_replay(tmp_path):
    led = tmp_path / "l" / "g.jsonl"; led.parent.mkdir()
    anc = tmp_path / "a" / "a.jsonl"; anc.parent.mkdir()
    e = Env(Ledger(led, anchors=AnchorStore(anc)))
    e.blinded("I1", "b1"); e.z_output_passes("out"); e.transfer("Z", "R", "out"); e.item_a("KA1")
    pl2 = PathsLayer()
    Governance(FK.public_key(), Ledger(led, anchors=AnchorStore(anc)),
               extensions=[ClaimsCharter(), CustodyLayer(None), pl2])
    assert set(pl2.z_inputs) == {"I1"} and len(pl2.transfers) == 1 and "KA1" in pl2.knowledge_a
    assert pl2.knowledge_a["KA1"]["origin_message_sha256"] in pl2.r_messages()
    # rules hold after replay: R-touched content still cannot enter Z as blinded input
    assert h("out") in pl2._r_contents()


@pytest.mark.parametrize("bad", [
    {"from": ["Z"], "to": "R"},                     # unhashable direction (R1-04)
    {"from": "Z", "to": "R", "item_sha256": 5},
    {"from": "Z", "to": "R", "item_sha256": "ab" * 32, "payload": "x"}])
def test_r1_04_malformed_transfer_is_a_logged_refusal(env, bad):
    cust = lambda st: sign("cust", CK, {**st, "nonce": uuid.uuid4().hex})          # noqa: E731
    bad = {"item_sha256": "ab" * 32, **bad}
    assert env.pl.guarded("path_transfer_recorded", S("cust", "record_path_transfer", **bad), cust) is None
    assert len(env.pl.refusals) == 1


def test_wrong_signer_refused(env):
    with pytest.raises(AuthError):
        env.pl.commit("knowledge_a_registered", S("cust", "register_knowledge_a", item_id="X", kind="أداة",
                                                  content_sha256=h("t")))
