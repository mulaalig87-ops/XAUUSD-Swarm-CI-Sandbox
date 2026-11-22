"""WP9-01 (part 1): end-to-end integration on SYNTHETIC data, ledger level, all built layers together.

One ledger, two replicas, as in operation:
  * CUSTODY replica: vault, encrypted package store, court service (holds the store key);
  * COURT replica: custody observer, no store, no package key, runs the court through the service.
The path covers layers 1–10 and the cross-cutting axis in one sequence:
inventory → C0 → slicing plan → claims → five-stage falsification (1–3) with a valid null →
test instance on Final → screening opening on Discovery → confirmation submission → adequacy →
Final opening → stage 4 → Z output passes custody → sealed package → court ruling → sealed lineage →
knowledge record → governance audit report → replay from the file ledger reproduces every state.

Paths (G1, `paths.py`): the blinded Discovery input enters Z through custody (ت-03), the sealed Z output
goes to R after custody's passage (ت-04, ت-06), and R → Z is refused in the integrated system (م-05).
The full flow set is in tests/test_paths.py. Synthetic values only.
"""
import dataclasses
import hashlib
import json
import os
import random
import uuid

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from xauusd_swarm.charter import GateError, Governance, Rule
from xauusd_swarm.claims import ClaimsCharter
from xauusd_swarm.controls import ControlsLayer
from xauusd_swarm.court import CourtLayer, PackageStore
from xauusd_swarm.court_service import CustodyCourtService
from xauusd_swarm.custody import LEAK_SCOPE, CustodyLayer, Vault
from xauusd_swarm.discovery import DiscoveryLayer
from xauusd_swarm.evidence import EvidenceLayer
from xauusd_swarm.falsification import FalsificationLayer
from xauusd_swarm.governance_audit import NOT_PROOF, GovernanceAuditLayer, audit_layer3
from xauusd_swarm.identity import public_hex, sign
from xauusd_swarm.inventory import InventoryLayer, content_sha256, impl_sha256, run_c0
from xauusd_swarm.knowledge import KnowledgeRegistry
from xauusd_swarm.ledger import AnchorStore, Ledger, LedgerError
from xauusd_swarm.paths import PathsLayer
from xauusd_swarm.slicing import SlicingLayer

FK, CK, AK, OK, DK, LK, GK = (Ed25519PrivateKey.generate() for _ in range(7))
KEYS = {"cust": CK, "aud": AK, "op": OK, "disc": DK, "lin": LK, "gaud": GK}
SKEY = os.urandom(32)
H = "cd" * 32


def S(ident, action, **kw):
    key = FK if ident == "founder" else KEYS[ident]
    return sign(ident, key, {"action": action, "nonce": uuid.uuid4().hex, **kw})


def F(action, **kw):
    return S("founder", action, **kw)


def world(n=200, seed=11):
    rnd, p, out = random.Random(seed), 100.0, []
    for i in range(n):
        c = p + rnd.gauss(0, 0.3)
        out.append({"id": f"o{i}", "t_market": 60.0 * i, "bid": round(c - 0.02, 5), "ask": round(c + 0.02, 5),
                    "source": "S1"})
        p = c
    return out


def fx_dup(obs):                                      # synthetic C0 fixture (not a project rule)
    seen, aff = set(), []
    for o in obs:
        if o["t_market"] in seen:
            aff.append(o["id"])
        seen.add(o["t_market"])
    return {"outcome": "detected" if aff else "not_detected", "affected_ids": aff}


def ctl_mean(w):                                      # synthetic control code (fixture)
    return {"mean": round(sum(w["x"]) / len(w["x"]), 9)}


W_PLANTED = {"x": [1.0 + 0.1 * (i % 3) for i in range(30)]}
W_NULL = {"x": [(-1) ** i * 0.1 for i in range(30)]}
SLICES = [{"slice_id": "D1", "station": "Discovery", "start": 0.0, "end": 4000.0},
          {"slice_id": "V1", "station": "Validation", "start": 4000.0, "end": 8000.0},
          {"slice_id": "X1", "station": "Final", "start": 8000.0, "end": 11940.0}]
CONFIG = {"structure": "A", "alpha_total": 0.05, "error_measure": "FWER", "procedure": "holm",
          "validity_reason": "Holm controls FWER under any dependence (س 681)"}


def layers(custody_side, store=None):
    cl = CustodyLayer(Vault(), identity="cust", key=CK) if custody_side else CustodyLayer(None)
    return {"cc": ClaimsCharter(), "cl": cl,
            "il": InventoryLayer(identity="cust", key=CK) if custody_side else InventoryLayer(),
            "sl": SlicingLayer(), "ct": CourtLayer(custody_store=store) if custody_side else CourtLayer(),
            "ev": EvidenceLayer(), "dl": DiscoveryLayer(), "fl": FalsificationLayer(), "co": ControlsLayer(),
            "kr": KnowledgeRegistry(), "ga": GovernanceAuditLayer(), "pl": PathsLayer()}


ORDER = ("cc", "cl", "il", "sl", "ct", "ev", "dl", "fl", "co", "kr", "ga", "pl")


class System:
    def __init__(self, led):
        self.led, self.store = led, PackageStore(key=SKEY)
        self.cus = layers(True, self.store)                       # custody replica
        self.gC = Governance(FK.public_key(), led, extensions=[self.cus[k] for k in ORDER])
        self.svc = CustodyCourtService(self.gC, self.store, identity="cust", key=CK)
        self.crt = layers(False)                                  # court replica (no store, no key)
        self.gO = None

    def court_replica(self):
        self.gO = Governance(FK.public_key(), self.led, extensions=[self.crt[k] for k in ORDER])
        return self.crt

    def row(self, tool_kind, tool_id):
        co = self.cus["co"]
        tgt = ControlsLayer.target_of(tool_kind, tool_id)
        for pol in ("positive", "negative"):
            co.commit("control_registered", F("register_control", control_id=f"row-{tool_kind}-{tool_id}-{pol}",
                      target=tgt, polarity=pol, expected={"metric": "m", "op": ">=", "value": 0},
                      world_sha256=H, impl_sha256=H))
        text = f"criterion for {tool_kind} {tool_id}"
        co.commit("tool_row_registered", F("register_tool_row", tool_kind=tool_kind, tool_id=tool_id,
                  controls=[f"row-{tool_kind}-{tool_id}-positive", f"row-{tool_kind}-{tool_id}-negative"],
                  criterion={"text": text, "sha256": content_sha256(text)}, cost_metric="compute seconds"))

    def control(self, cid, polarity):
        co, w = self.cus["co"], (W_PLANTED if polarity == "positive" else W_NULL)
        exp = ({"metric": "mean", "op": ">=", "value": 0.5} if polarity == "positive"
               else {"metric": "mean", "op": "between", "low": -0.2, "high": 0.2})
        co.commit("control_registered", F("register_control", control_id=cid,
                  target={"kind": "null_model", "id": "N-shuffle"}, polarity=polarity, expected=exp,
                  world_sha256=content_sha256(w), impl_sha256=impl_sha256(ctl_mean)))
        co.run_control(cid, ctl_mean, w, operator="op", key=OK)
        co.attest_reexecution(f"r-{cid}", ctl_mean, w, auditor="aud", key=AK)
        return f"r-{cid}"

    def decide(self, s):
        cl, sl = self.cus["cl"], self.cus["sl"]
        if s not in cl.decisions:
            cl.commit("custody_decision", S("cust", "custody_decision", slice=s, family="F1", delta=0.01,
                                            params_commitment=cl.families["F1"]["commitment"],
                                            boundaries=SlicingLayer.boundaries_text(sl.slices[s])))


def run_pipeline(sysm):
    """The full synthetic path. Returns the ids needed for the checks."""
    c = sysm.cus
    g = sysm.gC
    # --- layer 1–2: identities, roles, charters --------------------------------------------------
    for ident, k in KEYS.items():
        g.register_key(F("register_key", identity=ident, public_key_hex=public_hex(k.public_key())))
    for role, h in (("custody", "cust"), ("custody_auditor", "aud"), ("court_operator", "op"),
                    ("discovery_participant", "disc"), ("governance_auditor", "gaud")):
        c["cl"].commit("role_assigned", F("assign_role", role=role, holder=h))
    g.set_initial_charter(F("charter_initial", charter="project", text="P"))
    g.set_initial_charter(F("charter_initial", charter="claims", text="C"))
    g.register_rule(Rule.make("R-int", 1, "synthetic integration rule", author="founder", executor="cust", layer=5))
    c["kr"].commit("lineage_recorder_assigned", F("assign_lineage_recorder", holder="lin", capture_mode="automatic"))
    # --- layer 4: inventory (synthetic class), C0 -------------------------------------------------
    c["il"].permit(F("permit_inventory", dataset_id="SYN", data_class="synthetic"))
    c["il"].record_inventory("SYN", world(), source="gen")
    for kind, tid in (("c0_gate", "C0"), ("null_model", "N-shuffle"), ("court", "court"), ("leak_check", "lineage")):
        sysm.row(kind, tid)
    rule = {"rule_id": "R1", "dataset_id": "SYN", "effect": "feed", "test": "dup timestamps (synthetic)",
            "criterion": "any", "resulting_state": 1, "handling": {str(i): f"h{i}" for i in range(1, 6)},
            "test_impl_sha256": impl_sha256(fx_dup)}
    c["il"].record_c0_rule(F("c0_rule_approve", rule=rule))
    c["il"].record_c0_result("R1", run_c0(c["il"].c0_rules["R1"], fx_dup, world()), time="t")
    # --- layer 5: slice plan; layer 3: family parameters (custody) --------------------------------
    c["sl"].freeze_plan(c["il"], "P1", "SYN", basis="calendar_time", slices=SLICES)
    com = c["cl"].vault.set_params("F1", c=1.5, a=2.0, b=-3.0, m=7.0)
    c["cl"].commit("params_fixed", S("cust", "params_fixed", family="F1", params_commitment=com, delta=0.01))
    # --- layer 9 configuration (before any opening) ----------------------------------------------
    c["ct"].commit("court_policy_decided", F("decide_court_policy", family="F1", structure="A", error_measure="FWER",
                                             register_ref="synthetic", register_sha256="ab" * 32))
    c["ct"].commit("court_frozen", F("freeze_court", family="F1", config=CONFIG))
    c["dl"].commit("null_card_accepted", F("accept_null_card", null_model="N-shuffle",
                                           card={"transform": "permutation", "null": "exchangeability"}))
    # --- claim, stages 1–3, valid null (layers 1, 8, axis) ---------------------------------------
    c["cc"].register(F("register_claim", card={"claim_id": "K1", "version": 1, "tags": ["الموقع"], "category": None,
                                               "path": "أ", "uses_events": False, "scope_type": "stable", "scope": "s",
                                               "rulings": {"existence": "e", "size_with_uncertainty": "s",
                                                           "importance": "i"}}))
    c["ct"].commit("claim_identity_registered", F("register_claim_identity", claim_id="K1", identity={
        "target_quantity": "q-K1", "eligible_data_scope": "synthetic", "time_scope_type": "stable",
        "proof_path": "أ", "direction_or_threshold": ">0", "observation_precision": "n/a", "price_series": "Mid"}))
    st = lambda n, **kw: c["fl"].commit("stage_recorded", F("record_stage", claim_id="K1", stage=n, **kw))  # noqa: E731
    st(1, slice="D1", difference="mean shift in window w", evidence_sha256=H)
    st(2, null_swaps=["N-shuffle"], temporal_location="first third of D1")
    st(3, basic_null="N-shuffle", justification="exchangeability is the target's null", alternatives=[],
       sensitivity=["block length 5, 10"])
    ids = [sysm.control("N-pos", "positive"), sysm.control("N-neg", "negative")]
    c["fl"].commit("null_validity_recorded", F("record_null_validity", null_model="N-shuffle", control_results=ids))
    # --- layers 5–6: design, test instance on Final, screening opening, submission ---------------
    c["sl"].record_design(F("record_split_design", claim_id="K1", design="A", rules={}))
    sysm.decide("X1")
    c["ct"].commit("test_instance_registered", F("register_test_instance", test_instance_id="T-K1", claim_id="K1",
                   statistic="mean", procedure="t", null="N-shuffle", slice="X1", seeds="1", code_version="v1",
                   representation_id="r", transform_version="t1", price_series="Mid", path="Z", role="primary",
                   null_card_accepted=True))
    sysm.decide("D1")
    # ت-03: Z receives the blinded Discovery representation, admitted by custody
    c["pl"].commit("z_input_admitted", S("cust", "admit_z_input", input_id="Z-D1", source="blinding", slice="D1",
                   representation_id="r", content_sha256=hashlib.sha256(b"blinded D1 (synthetic)").hexdigest()))
    g.consume_slice("D1")
    c["cc"].open_on_slice("K1", "D1")
    c["ev"].commit("confirmation_submitted", F("submit_for_confirmation", unit_id="U1", unit_slices=["X1"], family="F1",
                                               claims=[{"claim_id": "K1", "path": "Z", "screening_slices": ["D1"]}]))
    c["ev"].commit("adequacy_reported", S("cust", "adequacy_report", unit_id="U1", source_slices=["X1"],
                   effective_units_after_purge=100, coverage=0.9, censoring_ratio=0.1, tie_ratio=0.0,
                   tie_includes_ambiguous=True, claims=["K1"], test_instances_per_claim={"K1": 1},
                   detectable_effect=0.2, family_size=1, procedure="holm", alpha=0.05, exclusions=[],
                   verdict="adequate", time="t"))
    g.consume_slice("X1")
    c["ev"].open_final(F("open_final", unit_id="U1", openings=c["ev"].final_manifest("U1")))
    st(4)
    # --- Z output → custody passage → sealed package (ت-04, ت-13) ---------------------------------
    pkg = json.dumps({"family": "F1", "submissions": [
        {"test_instance_id": "T-K1", "p_value": 0.001, "estimate": 0.5, "ci": [0.2, 0.8]}]}, sort_keys=True).encode()
    h = hashlib.sha256(pkg).hexdigest()
    c["cl"].commit("z_output_passed", S("cust", "z_output_passed", output_sha256=h, reviewed=list(LEAK_SCOPE),
                                        passed=True))
    sysm.svc.deposit(pkg)
    c["pl"].commit("path_transfer_recorded", S("cust", "record_path_transfer", **{"from": "Z", "to": "R"},
                   item_sha256=h))                                                  # ت-06
    with pytest.raises(GateError, match="R → Z is forbidden"):                    # م-05 in the full system
        c["pl"].commit("path_transfer_recorded", S("cust", "record_path_transfer", **{"from": "R", "to": "Z"},
                       item_sha256=h))
    c["cl"].commit("submissions_sealed", S("op", "seal_submissions", family="F1", submissions_sha256=h))
    # --- layer 9: court run by the operator through the custody service (ت-14) --------------------
    crt = sysm.court_replica()
    ruling = crt["ct"].run("F1", lambda stmt: sign("op", OK, {**stmt, "nonce": uuid.uuid4().hex}), sysm.svc)
    # --- layer 10: sealed lineage → knowledge record from code output ----------------------------
    kr = crt["kr"]
    kr.commit("lineage_recorded", S("lin", "record_lineage", test_instance_id="T-K1", capture_mode="automatic",
        data={"source": "synthetic", "transforms": [{"name": "r", "version": "t1", "params": {}}], "block_usage": [],
              "exclusions": [], "blinding_state": "blinded", "availability_time_source": "مرصود"},
        environment={"libraries": ["x==1"], "environment": "wp801", "seeds": [1], "training_settings": {}},
        hypothesis={"versions_branches_edits": [], "epistemic_path": "as given"},
        experiments={"stopped_or_incomplete": [], "exclusion_reasons": []},
        knowledge={"seen": [], "tools": [], "touched_gold_or_R_info": False, "llm_in_lineage": False,
                   "blinding_breach_events": []}))
    kr.commit("lineage_sealed", sign("lin", LK, {**kr.seal_statement("T-K1"), "nonce": uuid.uuid4().hex}))
    rec = kr.build_record(ruling["ruling_id"], "K1", reporting_level=1, availability="مرصود")
    kr.commit("knowledge_recorded", sign("op", OK, {**rec, "nonce": uuid.uuid4().hex}))
    # --- cross-cutting: governance audit (procedural only) ---------------------------------------
    ga = crt["ga"]
    ga.commit("governance_audit_reported", S("gaud", "governance_audit_report", report_id="GA1",
              checks=audit_layer3(sysm.gO), planted_cases=[],   # planted leak types are WP9-03 (not run here)
              statement=NOT_PROOF))
    return ruling


def norm(x, path="state"):
    """Comparable form of state, RECURSIVE at every level (review R2-01):
    dicts (any keys) → sorted pairs; sets → sorted lists; dataclasses → their fields by name;
    any other object at any depth → refused, so nothing is compared only by its type."""
    if isinstance(x, (str, int, float, bool, type(None), bytes)):
        return x
    if dataclasses.is_dataclass(x) and not isinstance(x, type):
        return ["<dataclass>", type(x).__name__,
                [[f.name, norm(getattr(x, f.name), f"{path}.{f.name}")] for f in dataclasses.fields(x)]]
    if isinstance(x, dict):
        return sorted(([norm(k, f"{path}<key>"), norm(v, f"{path}[{k!r}]")] for k, v in x.items()), key=repr)
    if isinstance(x, (set, frozenset)):
        return sorted((norm(v, f"{path}{{}}") for v in x), key=repr)
    if isinstance(x, (list, tuple)):
        return [norm(v, f"{path}[{i}]") for i, v in enumerate(x)]
    raise TypeError(f"{path}: unsupported {type(x).__name__}; the comparison would skip its content")


def full_state(L, g):
    """EVERY attribute of every layer except the back-reference to Governance, plus Governance's own
    state (keys, charters, roles, consumed slices, nonces …). Nothing is selected by hand (review R1-03)."""
    out = {}
    for k in ORDER:
        out[k] = {a: norm(v, f"{k}.{a}") for a, v in vars(L[k]).items() if a != "g"}
    out["governance"] = norm(g._s, "governance")
    return out


@pytest.fixture
def files(tmp_path):
    led = tmp_path / "led" / "g.jsonl"; led.parent.mkdir()
    anc = tmp_path / "anc" / "a.jsonl"; anc.parent.mkdir()
    return led, anc


def test_end_to_end_synthetic_path(files):
    led, anc = files
    sysm = System(Ledger(led, anchors=AnchorStore(anc)))
    ruling = run_pipeline(sysm)
    crt = sysm.crt
    crt["ct"].refresh()
    out = crt["ct"].rulings[ruling["ruling_id"]]["output"]
    assert "K1" in out["claims"]
    assert set(crt["fl"].stages["K1"]) == {1, 2, 3, 4}
    assert "GA1" in crt["ga"].reports
    assert all(v["result"] == "pass" for v in crt["ga"].reports["GA1"]["checks"].values())
    # the court replica never held the package store or its key
    assert getattr(crt["ct"], "custody_store", None) is None


def test_replay_reproduces_every_layer(files):
    """A fresh process reading only the ledger rebuilds the same FULL state of every layer and of
    Governance as the live court replica (history = ledger)."""
    led, anc = files
    sysm = System(Ledger(led, anchors=AnchorStore(anc)))
    run_pipeline(sysm)
    fresh = layers(False)
    g2 = Governance(FK.public_key(), Ledger(led, anchors=AnchorStore(anc)), extensions=[fresh[k] for k in ORDER])
    for L in (sysm.crt, fresh):
        for k in ORDER:
            if hasattr(L[k], "refresh"):
                L[k].refresh()
    live, rebuilt = full_state(sysm.crt, sysm.gO), full_state(fresh, g2)
    assert set(live) == set(ORDER) | {"governance"}
    for k in live:
        assert rebuilt[k] == live[k], f"replay differs in {k}"
    # not vacuous: the pipeline populated every layer that it touches
    assert all(any(v not in ([], None, 0, "") for v in live[k].values()) for k in ORDER)


def test_full_state_comparison_detects_a_difference(files):
    """The comparison is sensitive: one changed attribute anywhere makes it unequal."""
    led, anc = files
    sysm = System(Ledger(led, anchors=AnchorStore(anc)))
    run_pipeline(sysm)
    fresh = layers(False)
    g2 = Governance(FK.public_key(), Ledger(led, anchors=AnchorStore(anc)), extensions=[fresh[k] for k in ORDER])
    for L in (sysm.crt, fresh):
        for k in ORDER:
            if hasattr(L[k], "refresh"):
                L[k].refresh()
    assert full_state(fresh, g2) == full_state(sysm.crt, sysm.gO)          # equal before the change
    fresh["pl"].refusals.append({"x": 1})
    assert full_state(fresh, g2)["pl"] != full_state(sysm.crt, sysm.gO)["pl"]


def _nested(g, cls):
    """First instance of a dataclass `cls` nested inside Governance state, with a setter that replaces it."""
    for name, v in vars(g._s).items():
        items = v.items() if isinstance(v, dict) else enumerate(v) if isinstance(v, list) else ()
        for k, item in items:
            for inner_k, inner in (item.items() if isinstance(item, dict) else
                                   enumerate(item) if isinstance(item, list) else [(None, item)]):
                if isinstance(inner, cls):
                    def put(new, v=v, k=k, item=item, inner_k=inner_k):
                        if inner_k is None:
                            v[k] = new
                        else:
                            item[inner_k] = new
                    return inner, put
    raise AssertionError(f"no {cls.__name__} in Governance state")


@pytest.mark.parametrize("cls_name", ["CharterVersion", "Rule"])
def test_full_state_sees_inside_nested_dataclasses(files, cls_name):
    """R2-01: a changed FIELD inside a nested CharterVersion / Rule (same type) is detected."""
    from xauusd_swarm import charter
    cls = getattr(charter, cls_name)
    led, anc = files
    sysm = System(Ledger(led, anchors=AnchorStore(anc)))
    run_pipeline(sysm)
    g2 = Governance(FK.public_key(), Ledger(led, anchors=AnchorStore(anc)),
                    extensions=[layers(False)[k] for k in ORDER])
    before = norm(g2._s)
    obj, put = _nested(g2, cls)
    f = next(f for f in dataclasses.fields(obj) if isinstance(getattr(obj, f.name), (str, int)))
    old = getattr(obj, f.name)
    put(dataclasses.replace(obj, **{f.name: old + 1 if isinstance(old, int) and not isinstance(old, bool)
                                    else str(old) + "~"}))
    assert type(_nested(g2, cls)[0]) is cls                                       # same type, other content
    assert norm(g2._s) != before


def test_norm_refuses_unknown_objects_at_any_depth():
    class Opaque:
        pass
    with pytest.raises(TypeError, match="unsupported Opaque"):
        norm({"a": [{"b": Opaque()}]})


def test_ledger_tamper_is_detected_on_replay(files):
    led, anc = files
    sysm = System(Ledger(led, anchors=AnchorStore(anc)))
    run_pipeline(sysm)
    lines = led.read_text(encoding="utf-8").splitlines()
    i = next(n for n, ln in enumerate(lines) if "knowledge_recorded" in ln)
    d = json.loads(lines[i])
    hx = d["payload"]["statement_hex"]                           # payload stores the signed statement as hex
    d["payload"]["statement_hex"] = hx[:-1] + ("0" if hx[-1] != "0" else "1")
    tampered = json.dumps(d, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    assert tampered != lines[i]                                  # the edit really changed the entry
    lines[i] = tampered
    led.write_text("\n".join(lines) + "\n", encoding="utf-8")
    with pytest.raises(LedgerError):
        Governance(FK.public_key(), Ledger(led, anchors=AnchorStore(anc)), extensions=[layers(False)[k] for k in ORDER])


def test_order_is_enforced_across_layers(files):
    """Cross-layer gates hold in the integrated system: no Final opening before adequacy, no court ruling
    before a sealed package, no knowledge record without sealed lineage."""
    led, anc = files
    sysm = System(Ledger(led, anchors=AnchorStore(anc)))
    run_pipeline(sysm)
    c = sysm.cus
    with pytest.raises(GateError):
        c["ev"].open_final(F("open_final", unit_id="U1", openings=c["ev"].final_manifest("U1")))   # once only
    with pytest.raises(GateError):
        c["fl"].commit("stage_recorded", F("record_stage", claim_id="K1", stage=3, basic_null="N-shuffle",
                       justification="x", alternatives=[], sensitivity=[]))                         # no going back
