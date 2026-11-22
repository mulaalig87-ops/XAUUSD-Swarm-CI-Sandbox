"""RIP-2 U-vol truth (review R6): mechanism fidelity, exact-sum sanity, and the committed verification result."""
import importlib.util
import json
import math
import random
from pathlib import Path

import pytest

from xauusd_swarm import reid

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("uvol", ROOT / "scripts" / "rip2_uvol_verify.py")
U = importlib.util.module_from_spec(spec)
spec.loader.exec_module(U)
RES = ROOT / "docs" / "results" / "RIP2_uvol_verification.json"


@pytest.mark.parametrize("asset,period", [(0, 2), (1, 0), (2, 3), (3, 1)])
def test_monte_carlo_step_expression_is_the_generator(asset, period):
    # replicate reid.simulate step by step with the verification script's expression `obs`
    a, p = reid.ASSETS[asset], reid.PERIODS[period]
    rnd = random.Random(11)
    price, mine = a["level"] * p["growth"], []
    for t in range(300):
        r = a["drift"] + a["vol"] * p["volx"] * (1 + a["act"] * math.sin(2 * math.pi * t / 64)) * rnd.gauss(0, 1)
        price *= math.exp(r)
        mine.append(U.obs(price, a["tick"]))
    assert mine == reid.simulate(asset, period, 300, random.Random(11))


@pytest.mark.parametrize("case", U.CASES, ids=[c[0] for c in U.CASES])
def test_exact_sum_has_full_probability_mass(case):
    name, asset, P, mu, sigma, _ = case
    for kind in U.KINDS:
        ex, mass = U.exact(kind, asset, P, mu, sigma)
        assert abs(mass - 1.0) < 1e-12 and ex >= 0 and math.isfinite(ex)


def test_committed_verification_passes_and_is_reproducible_on_the_exact_side():
    if not RES.exists():
        pytest.skip("verification not run yet (pre-registration commit)")
    res = json.loads(RES.read_text())
    assert res["spec"] == U.SPEC and res["cases"] == [list(c) for c in U.CASES]
    assert len(res["rows"]) == len(U.CASES) * len(U.KINDS) and res["all_pass"] is True
    for r in res["rows"]:
        ex, _ = U.exact(r["kind"], r["asset"], r["P_latent"], r["mu"], r["sigma"])
        assert ex == pytest.approx(r["exact"], rel=1e-12)
