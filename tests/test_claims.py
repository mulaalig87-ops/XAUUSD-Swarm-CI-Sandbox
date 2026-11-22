"""Claims charter (layer 2) tests — synthetic claim cards only; no data."""
import uuid

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from xauusd_swarm.charter import GateError, Governance
from xauusd_swarm.claims import ClaimsCharter
from xauusd_swarm.identity import AuthError, public_hex, sign
from xauusd_swarm.ledger import AnchorStore, Ledger

FK = Ed25519PrivateKey.generate()
MK = Ed25519PrivateKey.generate()     # a registered NON-founder identity, synthetic
XK = Ed25519PrivateKey.generate()     # unregistered


def F(action, **kw):
    return sign("founder", FK, {"action": action, "nonce": uuid.uuid4().hex, **kw})


def card(cid="C1", version=1, path="أ", **kw):
    c = {"claim_id": cid, "version": version, "tags": ["الموقع"], "category": None, "path": path,
         "uses_events": False, "scope_type": "stable", "scope": "synthetic scope",
         "rulings": {"existence": "e-crit", "size_with_uncertainty": "s-crit", "importance": "i-crit"}}
    c.update(kw)
    return c


def R(c, key=FK, ident="founder"):
    return sign(ident, key, {"action": "register_claim", "nonce": uuid.uuid4().hex, "card": c})


def make(ledger=None):
    cc = ClaimsCharter()
    g = Governance(FK.public_key(), ledger if ledger is not None else Ledger(), extensions=[cc])
    g.register_key(F("register_key", identity="m1", public_key_hex=public_hex(MK.public_key())))
    g.set_initial_charter(F("charter_initial", charter="project", text="P1"))
    g.set_initial_charter(F("charter_initial", charter="claims", text="C1"))
    for sl in ("S1", "S2"):
        g.consume_slice(sl)
    return g, cc


@pytest.fixture
def cc():
    return make()[1]


def test_register_then_open_binds_card(cc):
    cc.register(R(card()))
    cc.open_on_slice("C1", "S1")
    assert cc.card_for_slice("C1", "S1")["rulings"]["existence"] == "e-crit"


def test_open_before_registration_refused(cc):
    with pytest.raises(GateError, match="registered before opening"):
        cc.open_on_slice("C9", "S1")


def test_closed_path_he_refused(cc):
    with pytest.raises(GateError, match="CLOSED"):
        cc.register(R(card(path="هـ")))


@pytest.mark.parametrize("bad", [
    {"tags": []}, {"tags": ["غير مدرج"]}, {"tags": ["الموقع", "الموقع"]},
    {"category": "other"}, {"scope_type": "eternal"}, {"scope": " "},
    {"rulings": {"existence": "x", "importance": "y"}},
    {"rulings": {"existence": "x", "size_with_uncertainty": "", "importance": "y"}},
    {"path": "و"},
])
def test_card_rules(cc, bad):
    with pytest.raises(GateError):
        cc.register(R(card(**bad)))


@pytest.mark.parametrize("h", [None, "", "abc", "AB" * 32, "zz" * 32, "ab" * 31, "ab" * 33, 123])
def test_composite_requires_valid_sha256(cc, h):
    with pytest.raises(GateError, match="SHA-256"):
        cc.register(R(card(category="composite", frozen_model_sha256=h)))


def test_composite_with_valid_hash_accepted(cc):
    cc.register(R(card(category="composite", frozen_model_sha256="ab" * 32)))


def test_d2_requires_all_six_conditions(cc):
    with pytest.raises(GateError, match="six conditions"):
        cc.register(R(card(path="د2", d2_conditions={"causal_quantity": "q"})))
    six = {k: "declared" for k in ("causal_quantity", "causal_structure", "identification_strategy",
                                   "confounder_assumptions", "sensitivity_unmeasured", "alternative_explanations")}
    cc.register(R(card(path="د2", d2_conditions=six)))


def test_new_version_does_not_apply_to_already_opened_slice(cc):
    cc.register(R(card()))
    cc.open_on_slice("C1", "S1")
    cc.register(R(card(version=2, rulings={"existence": "NEW", "size_with_uncertainty": "s", "importance": "i"})))
    cc.open_on_slice("C1", "S2")
    assert cc.card_for_slice("C1", "S1")["rulings"]["existence"] == "e-crit"   # bound v1
    assert cc.card_for_slice("C1", "S2")["rulings"]["existence"] == "NEW"


@pytest.mark.parametrize("change", [{"path": "ب"}, {"tags": ["الموقع", "الحالة"]}, {"category": "open"}])
def test_claim_identity_frozen_across_versions(cc, change):
    cc.register(R(card()))
    with pytest.raises(GateError, match="identity is frozen"):
        cc.register(R(card(version=2, **change)))


def test_composite_model_frozen_across_versions(cc):
    cc.register(R(card(category="composite", frozen_model_sha256="ab" * 32)))
    with pytest.raises(GateError, match="identity is frozen"):
        cc.register(R(card(version=2, category="composite", frozen_model_sha256="cd" * 32)))


def test_allowed_version_changes_scope_and_criteria(cc):
    cc.register(R(card()))
    cc.register(R(card(version=2, scope_type="conditional", scope="narrower",
                       rulings={"existence": "e2", "size_with_uncertainty": "s2", "importance": "i2"})))


def test_versions_consecutive_and_reopen_refused(cc):
    with pytest.raises(GateError, match="consecutive"):
        cc.register(R(card(version=2)))
    cc.register(R(card())); cc.open_on_slice("C1", "S1")
    with pytest.raises(GateError, match="already opened"):
        cc.open_on_slice("C1", "S1")


def test_no_path_is_evidence_for_another_including_d1_to_d2(cc):
    six = {k: "x" for k in ("causal_quantity", "causal_structure", "identification_strategy",
                            "confounder_assumptions", "sensitivity_unmeasured", "alternative_explanations")}
    cc.register(R(card("A", path="د1"))); cc.register(R(card("B", path="د2", d2_conditions=six)))
    cc.register(R(card("C", path="د1")))
    with pytest.raises(GateError, match="no path counts as evidence"):
        cc.cite_evidence("B", "A")                          # د1 -> د2 refused (س 326)
    cc.cite_evidence("C", "A")                              # same path allowed


def test_only_founder_registers_claims(cc):
    with pytest.raises(AuthError, match="founder"):
        cc.register(R(card(), key=MK, ident="m1"))           # registered, but not the founder
    with pytest.raises(AuthError):
        cc.register(R(card(), key=XK, ident="nobody"))
    with pytest.raises(AuthError, match="invalid signature"):
        cc.register(R(card(), key=XK, ident="founder"))


def test_open_on_unrecorded_slice_refused(cc):
    cc.register(R(card()))
    with pytest.raises(GateError, match="unknown slice"):
        cc.open_on_slice("C1", "NOT-RECORDED")


def test_replayed_card_statement_refused(cc):
    s = R(card()); cc.register(s)
    with pytest.raises(AuthError, match="replayed"):
        cc.register(s)


def test_claims_state_rebuilt_after_restart(tmp_path):
    (tmp_path / "a").mkdir()
    def fl(): return Ledger(tmp_path / "gov.jsonl", anchors=AnchorStore(tmp_path / "a" / "x.jsonl"))
    g, cc = make(fl())
    cc.register(R(card())); cc.open_on_slice("C1", "S1")
    cc.register(R(card(version=2, scope="v2")))
    cc2 = ClaimsCharter(); Governance(FK.public_key(), fl(), extensions=[cc2])
    assert cc2.card_for_slice("C1", "S1")["scope"] == "synthetic scope"
    assert len(cc2.cards["C1"]) == 2
    with pytest.raises(GateError, match="already opened"):
        cc2.open_on_slice("C1", "S1")


def test_forged_claim_event_refused_on_restart(tmp_path):
    (tmp_path / "a").mkdir()
    def fl(): return Ledger(tmp_path / "gov.jsonl", anchors=AnchorStore(tmp_path / "a" / "x.jsonl"))
    g, cc = make(fl())
    g.ledger.append("claim_opened", {"claim_id": "GHOST", "slice": "S1", "version": 1, "card_sha256": "0"})
    with pytest.raises(GateError, match="invalid history"):
        Governance(FK.public_key(), fl(), extensions=[ClaimsCharter()])


def test_failed_write_leaves_claims_state_unchanged(cc, monkeypatch):
    from xauusd_swarm.ledger import LedgerError
    cc.register(R(card()))
    before = (len(cc.cards["C1"]), dict(cc.openings))
    def boom(*a, **k): raise LedgerError("injected")
    monkeypatch.setattr(cc.g.ledger, "_append_mem", boom)
    with pytest.raises(LedgerError):
        cc.open_on_slice("C1", "S1")
    with pytest.raises(LedgerError):
        cc.register(R(card(version=2)))
    assert (len(cc.cards["C1"]), dict(cc.openings)) == before


# ---------------- FD-01-D43 gate (WP9-05 review R1-02): uses_events ----------------
def test_uses_events_is_mandatory_and_boolean(cc):
    c = card()
    del c["uses_events"]
    with pytest.raises(GateError, match="missing 'uses_events'"):
        cc.register(R(c))
    for bad in (None, 0, 1, "false", "no", [], {}):
        with pytest.raises(GateError, match="true or false|uses_events"):
            cc.register(R(card(uses_events=bad)))


def test_event_based_claim_refused_until_tp09_is_built(cc):
    with pytest.raises(GateError, match="TP-09"):
        cc.register(R(card(uses_events=True)))
    cc.register(R(card(uses_events=False)))                     # a non-event claim is accepted
    assert "C1" in cc.cards


def test_uses_events_frozen_across_versions(cc, monkeypatch):
    from xauusd_swarm import claims
    monkeypatch.setattr(claims, "TP09_BUILT", True)            # simulate a later build of TP-09
    cc.register(R(card(cid="E1", uses_events=True)))
    with pytest.raises(GateError, match="identity is frozen"):
        cc.register(R(card(cid="E1", version=2, uses_events=False)))   # true → false refused
    cc.register(R(card(cid="N1", uses_events=False)))
    with pytest.raises(GateError, match="identity is frozen"):
        cc.register(R(card(cid="N1", version=2, uses_events=True)))    # false → true refused too
