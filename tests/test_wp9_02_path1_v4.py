"""Path 1 v4 (OD-S9-05, FD-01-D41): controls reproduce exactly and match the committed results. SYNTHETIC ONLY."""
import importlib.util
import json
import random
from pathlib import Path

import pytest

from xauusd_swarm.path1 import run_permuted, runs_of, scan_v4, segment_labels

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.heavy
def test_path1_v41_reproduces_committed_results(tmp_path):
    """v4.1 (FD-01-D42). v4 is superseded (its reference left the H0 space); its results file was
    regenerated once on the current code and is not re-run in CI, to save paid minutes."""
    spec = importlib.util.spec_from_file_location("p1v4", ROOT / "scripts" / "wp9_02_path1_v4.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    got = json.loads(json.dumps(m.main(tmp_path / "run", "v4.1")))
    ref = json.loads((ROOT / "docs" / "results" / "WP9-02_path1_v41.json").read_text(encoding="utf-8"))
    for k in ("results", "generalisation_measure_and_declare", "module_sha256"):
        assert got[k] == ref[k], k
    assert all(r["outcome"] == "pass" for r in got["results"])


def test_v4_reference_keeps_series_and_run_boundaries():
    rnd = random.Random(3)
    lab = segment_labels(300, 20, ["A", "B", "C"], rnd)
    perm = run_permuted(lab, rnd)
    for a, b, _ in runs_of(lab):
        assert len(set(perm[a:b])) == 1


def test_v4_p_values_bounded_and_deterministic():
    rnd = random.Random(4)
    lab = segment_labels(300, 20, ["A", "B", "C"], rnd)
    r = [random.Random(9).gauss(0, 1) for _ in range(300)]
    a = scan_v4(r, lab, permutations=19, alpha=0.05, rng=random.Random(1))
    b = scan_v4(r, lab, permutations=19, alpha=0.05, rng=random.Random(1))
    assert a == b and all(1 / 20 <= p <= 1 for p in a["p"].values())


# ---------------- v4.1 (review R1-01 of v4): the reference keeps the run structure ----------------
from xauusd_swarm.path1 import _ConstrainedArrangements, constrained_permuted  # noqa: E402


def test_v41_reference_preserves_runs_lengths_counts_and_boundaries():
    for seed in range(20):
        rnd = random.Random(seed)
        lab = segment_labels(1600, 50, ["A", "B", "C"], rnd)
        rs = runs_of(lab)
        perm = constrained_permuted(lab, rnd)
        rp = runs_of(perm)
        assert [(a, b) for a, b, _ in rs] == [(a, b) for a, b, _ in rp]          # number, boundaries, lengths
        cnt = lambda runs: sorted(__import__("collections").Counter(c for _, _, c in runs).items())  # noqa: E731
        assert cnt(rs) == cnt(rp)                                                # runs per cell kept
        assert all(rp[i][2] != rp[i + 1][2] for i in range(len(rp) - 1))       # no merged runs


def test_v41_sampler_is_exactly_uniform_on_a_small_case():
    import collections
    import itertools
    s = _ConstrainedArrangements({"A": 2, "B": 2, "C": 1})
    valid = {p for p in itertools.permutations("AABBC") if all(p[i] != p[i + 1] for i in range(4))}
    assert s.total() == len(valid) == 12
    c = collections.Counter(tuple(s.sample(random.Random(0))) for _ in range(1))
    rng = random.Random(0)
    c = collections.Counter(tuple(s.sample(rng)) for _ in range(24000))
    assert set(c) == valid and max(c.values()) - min(c.values()) < 300    # ≈ 2000 each


def test_v4_reference_merges_runs_documented_defect():
    """v4's reference (run_permuted) leaves the H0 space: adjacent runs receive the same cell and merge."""
    rnd = random.Random(1)
    lab = segment_labels(1600, 50, ["A", "B", "C"], rnd)
    merged = sum(len(runs_of(run_permuted(lab, rnd))) < len(runs_of(lab)) for _ in range(20))
    assert merged > 0
