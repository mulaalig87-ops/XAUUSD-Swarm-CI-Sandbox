"""WP9-02 part 2: TP-47 (C0 gate) and TP-46 (court) controls reproduce exactly from the committed code and
worlds and match the committed results file. SYNTHETIC ONLY."""
import importlib.util
import json
from pathlib import Path

from xauusd_swarm.gate_court_controls import c0_world, court_world_spec, run_court_world

ROOT = Path(__file__).resolve().parents[1]


def _script():
    spec = importlib.util.spec_from_file_location("wp9_02b", ROOT / "scripts" / "wp9_02_gate_court_controls.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_gate_court_controls_reproduce_committed_results(tmp_path):
    got = _script().main(tmp_path / "run")
    ref = json.loads((ROOT / "docs" / "results" / "WP9-02_gate_court_controls.json").read_text(encoding="utf-8"))
    key = lambda r: (r["control_id"], json.dumps(r["observed"], sort_keys=True), r["outcome"],   # noqa: E731
                     r["world_sha256"], r["impl_sha256"])
    assert [key(r) for r in got["results"]] == [key(r) for r in ref["results"]]
    assert got["module_sha256"] == ref["module_sha256"]
    assert all(r["outcome"] == "pass" for r in got["results"])


def test_court_ruling_output_is_stable_across_independent_systems():
    """TP-08 (a): two independently built systems (fresh keys and ledgers) give the same ruling output."""
    w = court_world_spec("real")
    assert run_court_world(w)["output_sha256"] == run_court_world(w)["output_sha256"]


def test_c0_worlds_plant_what_they_claim():
    obs, planted = c0_world(1, 50, 2, 3)
    assert len(planted) == 3 and all(o["ask"] < o["bid"] for o in obs if o["id"] in planted)
    clean, none = c0_world(1, 50, None, 3)
    assert none == [] and all(o["ask"] > o["bid"] for o in clean)
