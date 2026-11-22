"""TP-81 / TP-82: the measured values reproduce exactly from the committed code and spec and match the
committed results file (FD-01-D33). Measure-and-declare: no pass threshold is asserted. SYNTHETIC ONLY."""
import importlib.util
import json
from pathlib import Path

import pytest

from xauusd_swarm.assumption_tests import block_ci_mean, profile, profile_distance

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.heavy
def test_tp81_tp82_reproduce_committed_results(tmp_path):
    spec = importlib.util.spec_from_file_location("tp8182", ROOT / "scripts" / "tp81_tp82.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    got = m.main(tmp_path / "r.json")
    ref = json.loads((ROOT / "docs" / "results" / "TP81_TP82.json").read_text(encoding="utf-8"))
    for k in ("TP-81", "TP-82", "spec", "module_sha256"):
        assert json.loads(json.dumps(got[k])) == ref[k], k


def test_block_ci_brackets_resampled_means():
    import random
    lo, hi = block_ci_mean([float(i % 7) for i in range(100)], 5, 199, 0.95, random.Random(0))
    assert lo <= hi


def test_profile_distance_zero_for_identical():
    x = [float(i % 5) for i in range(64)]
    p = profile(x, 32, [[1, 4], [4, 16]])
    assert profile_distance(p, p) == 0.0
