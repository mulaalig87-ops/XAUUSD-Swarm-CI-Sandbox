"""WP9-02 part 3: path-1 controls reproduce exactly and match the committed results, including the two
recorded failures (FL-011: v1 and v2 positive controls). SYNTHETIC ONLY."""
import importlib.util
import json
from pathlib import Path

import pytest

from xauusd_swarm.path1 import run_permuted, runs_of

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.heavy
def test_path1_controls_reproduce_committed_results(tmp_path):
    spec = importlib.util.spec_from_file_location("wp9_02c", ROOT / "scripts" / "wp9_02_path1_controls.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    got = m.main(tmp_path / "run")
    ref = json.loads((ROOT / "docs" / "results" / "WP9-02_path1_controls.json").read_text(encoding="utf-8"))
    key = lambda r: (r["control_id"], json.dumps(r["observed"], sort_keys=True), r["outcome"],   # noqa: E731
                     r["world_sha256"], r["impl_sha256"])
    assert [key(r) for r in got["results"]] == [key(r) for r in ref["results"]]
    assert got["generalisation_measure_and_declare"] == ref["generalisation_measure_and_declare"]
    assert got["module_sha256"] == ref["module_sha256"]
    out = {r["control_id"]: r["outcome"] for r in got["results"]}
    assert [out[f"TP21-P1-{v}-real-positive"] for v in ("v1", "v2", "v3")] == ["fail"] * 3     # FL-011


def test_run_permutation_keeps_run_boundaries():
    import random
    lab = ["A"] * 3 + ["B"] * 2 + ["A"] * 4 + ["C"] * 1
    p = run_permuted(lab, random.Random(1))
    assert [(a, b) for a, b, _ in runs_of(lab)] == [(0, 3), (3, 5), (5, 9), (9, 10)]
    assert len(p) == len(lab)
    for a, b, _ in runs_of(lab):                    # each original run carries one cell after permutation
        assert len(set(p[a:b])) == 1


def test_fast_ks_equals_two_list_ks_with_ties():
    import random
    from xauusd_swarm.path1 import cell_stats, segment_labels, sort_order
    for seed in range(10):
        rnd = random.Random(seed)
        r = [round(rnd.gauss(0, 1), 1) for _ in range(150)]
        lab = segment_labels(150, 20, ["A", "B", "C"], rnd)
        assert cell_stats(r, lab) == cell_stats(r, lab, sort_order(r))
