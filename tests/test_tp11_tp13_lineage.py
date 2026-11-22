"""WP9-05: TP-11 (failed, stopped and excluded runs stay in the record) and TP-13.01–13.12 (each lineage
element is recorded and retrieved from the lineage). SYNTHETIC ONLY.

Criterion of TP-13 (WP7-04 §1.1): on a planted synthetic run, each element is recorded and retrieved from
the lineage. Here "retrieved" means: read back from a FRESH replica rebuilt from the file ledger alone.
TP-13.09 («المسار المعرفي») is [معلّق] in the test plan (meaning undefined, م3-10): its field is recorded
as text but no meaning is tested. TP-11 criterion: every planted run appears with its state and is not
deleted (س 2237)."""
import uuid

import pytest

from test_court_knowledge import LK, build
from xauusd_swarm.charter import Governance
from xauusd_swarm.claims import ClaimsCharter
from xauusd_swarm.court import CourtLayer
from xauusd_swarm.custody import CustodyLayer
from xauusd_swarm.identity import sign
from xauusd_swarm.knowledge import KnowledgeRegistry
from xauusd_swarm.ledger import AnchorStore, Ledger
from test_court_knowledge import FK

PLANTED = {
    "data": {"source": "synthetic-world-7", "transforms": [{"name": "log_returns", "version": "t3", "params": {"scale": 2.5}}],
             "block_usage": [{"block": "D1-b3", "uses": 2}], "exclusions": [{"rule": "gap>5m", "reason": "gap", "count": 4}],
             "blinding_state": "blinded", "availability_time_source": "مفترض"},
    "environment": {"libraries": ["numpy==none", "xauusd_swarm==9"], "environment": "wp801-test", "seeds": [17, 23],
                    "training_settings": {"epochs": 0}},
    "hypothesis": {"versions_branches_edits": [{"version": 2, "branch": "b1", "edit": "window 5→8"}],
                   "epistemic_path": "as given (TP-13.09 is [معلّق])"},
    "experiments": {"stopped_or_incomplete": [{"run": "r-failed", "state": "failed"}, {"run": "r-stopped", "state": "stopped"}],
                    "exclusion_reasons": [{"run": "r-excluded", "reason": "code-integrity only"}]},
    "knowledge": {"seen": ["paper-A"], "tools": ["kde"], "touched_gold_or_R_info": True, "llm_in_lineage": True,
                  "blinding_breach_events": []},
}

ELEMENTS = {   # TP-13 row → path in the lineage record
    "TP-13.01": ("data", "source"), "TP-13.02": ("data", "transforms"), "TP-13.03": ("data", "block_usage"),
    "TP-13.04": ("data", "exclusions"), "TP-13.05": ("data", "blinding_state"),
    "TP-13.06": ("data", "availability_time_source"),
    "TP-13.07": ("environment", None), "TP-13.08": ("hypothesis", "versions_branches_edits"),
    "TP-13.09": ("hypothesis", "epistemic_path"),
    "TP-13.10": ("experiments", None), "TP-13.11": ("knowledge", None), "TP-13.12": ("knowledge", "llm_in_lineage"),
}


@pytest.fixture
def replayed(tmp_path):
    (tmp_path / "l").mkdir()
    (tmp_path / "a").mkdir()
    led = Ledger(tmp_path / "l" / "g.jsonl", anchors=AnchorStore(tmp_path / "a" / "a.jsonl"))
    g, cc, cl, ct, kr = build(ledger=led)
    st = {"action": "record_lineage", "nonce": uuid.uuid4().hex, "test_instance_id": "T1", "capture_mode": "automatic",
          **PLANTED}
    kr.commit("lineage_recorded", sign("lin", LK, st))
    kr.commit("lineage_sealed", sign("lin", LK, {**kr.seal_statement("T1"), "nonce": uuid.uuid4().hex}))
    fresh = KnowledgeRegistry()
    Governance(FK.public_key(), Ledger(tmp_path / "l" / "g.jsonl", anchors=AnchorStore(tmp_path / "a" / "a.jsonl")),
               extensions=[ClaimsCharter(), CustodyLayer(None), CourtLayer(), fresh])
    return fresh


@pytest.mark.parametrize("tp", sorted(ELEMENTS))
def test_tp13_element_recorded_and_retrieved_after_replay(replayed, tp):
    sec, key = ELEMENTS[tp]
    rec = replayed.lineage["T1"][0]
    got = rec[sec] if key is None else rec[sec][key]
    want = PLANTED[sec] if key is None else PLANTED[sec][key]
    assert got == want
    assert "T1" in replayed.seals                      # sealed, so it can no longer change (only corrections append)


def test_tp11_failed_stopped_excluded_runs_stay_in_the_record(replayed):
    exp = replayed.lineage["T1"][0]["experiments"]
    states = {e["run"]: e["state"] for e in exp["stopped_or_incomplete"]}
    assert states == {"r-failed": "failed", "r-stopped": "stopped"}
    assert exp["exclusion_reasons"] == [{"run": "r-excluded", "reason": "code-integrity only"}]
    assert not [k for k in KnowledgeRegistry.KINDS if "delet" in k or "remov" in k]    # no deletion event exists


def test_tp13_lineage_missing_an_element_is_refused():
    g, cc, cl, ct, kr = build()
    bad = {k: dict(v) for k, v in PLANTED.items()}
    del bad["data"]["availability_time_source"]
    from xauusd_swarm.charter import GateError
    with pytest.raises(GateError):
        kr.commit("lineage_recorded", sign("lin", LK, {"action": "record_lineage", "nonce": uuid.uuid4().hex,
                                                       "test_instance_id": "T1", "capture_mode": "automatic", **bad}))
