"""TP-30 (FD-01-D44): structure tests (no test-set run) and the heavy reproduction of the committed result."""
import inspect
import json
import random
from pathlib import Path

import pytest

from xauusd_swarm import reid

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "docs" / "results" / "WP9-05_TP30.json"


def test_attacker_interface_holds_no_blinding_parameters():
    # the reid_checker side sees blinded series and its own dev labels only — no parameters, no keys
    assert list(inspect.signature(reid.attack).parameters) == ["name", "dev_x", "dev_y", "test_x"]


def test_design_is_balanced_independent_and_has_no_threshold():
    s = reid.TP30
    assert s["seed_dev"] != s["seed_test"] and len(reid.ASSETS) == reid.K == 4 and len(reid.PERIODS) == reid.P == 4
    assert len(s["representations"]) == 6 and len(s["attackers"]) == 3
    xs, ys = reid.make_set("log_returns", 2, 11)
    assert sorted(ys) == sorted((a, p) for a in range(4) for p in range(4) for _ in range(2))
    assert all(isinstance(v, float) for x in xs for v in x)          # bare numbers: no names in the sample


def test_samples_are_shuffled_so_order_does_not_leak():
    _, ys = reid.make_set("log_returns", 2, 11)
    assert ys != sorted(ys)


def test_each_sample_has_its_own_blinding_draw():
    rnd = random.Random(5)
    p = reid.simulate(0, 0, 64, rnd)
    a, b = reid.blind("affine_level", p, 0, rnd), reid.blind("affine_level", p, 0, rnd)
    assert a != b


def test_wilson_interval():
    lo, hi = reid.wilson(100, 400)
    assert lo < 0.25 < hi and reid.wilson(0, 10)[0] == 0.0


@pytest.mark.heavy
def test_tp30_reproduces_committed_result():
    if not RES.exists():
        pytest.skip("TP-30 not run yet (pre-registration commit)")
    got = json.loads(json.dumps(reid.run_tp30()))
    want = json.loads(RES.read_text(encoding="utf-8"))
    assert got["rows"] == want["rows"]
