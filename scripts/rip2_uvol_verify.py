"""RIP-2 U-vol truth: numerical verification of the exact formula against Monte Carlo of the ACTUAL mechanism.
Pre-registered in docs/research/RIP2_UVOL_DERIVATION.md §5 (cases, N, seed, acceptance) before this was run.
SYNTHETIC ONLY. Usage: python scripts/rip2_uvol_verify.py OUT_JSON

Exact side: discrete sum over the tick level j that the deterministic rounding can produce (derivation §3).
Monte Carlo side, independent of the formula code: the generator's own step expression (as in reid.simulate:
price *= exp(r); round(round(price / tick) * tick, 10)) and the frozen representation functions applied to the
two-point series [P̃_prev, P̃_u]."""
import json
import math
import random
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from xauusd_swarm import reid                                            # noqa: E402
from xauusd_swarm import representations as R                           # noqa: E402

KINDS = ["C0_or_level_residual_unwrapped", "tick_grid", "affine_level", "log_returns", "volatility_time"]
SPEC = {"N": 200_000, "seed": 7301, "z_limit": 4.0, "kinds": KINDS}
# (name, asset, latent P_{u-1}, mu, sigma, registered_world?)
CASES = [
    ("a0_high_vol_shift", 0, 2340.0, 0.00002, 0.0009 * 1.6 * 1.6 * 2, True),
    ("a0_low_vol", 0, 1800.0, 0.00002, 0.0009 * 0.8 * 0.4, True),
    ("a1_zero_drift", 1, 34.5, 0.0, 0.0014, True),
    ("a1_high_vol_shift", 1, 39.0, 0.0, 0.0014 * 1.6 * 1.3 * 2, True),
    ("a2_lowest_vol", 2, 1.1, -0.00001, 0.0005 * 0.8 * 0.9, True),
    ("a2_just_below_half_tick", 2, (110000 + 0.5 - 1e-6) * 1e-5, -0.00001, 0.0005 * 0.8 * 0.9, True),
    ("a2_just_above_half_tick", 2, (110000 + 0.5 + 1e-6) * 1e-5, -0.00001, 0.0005 * 0.8 * 0.9, True),
    ("a3_mid", 3, 217.5, 0.00001, 0.0011 * 1.2, True),
    ("stress_a2_sigma_1e-5", 2, 1.1, -0.00001, 1e-5, False),
    ("stress_a2_sigma_3e-6", 2, 1.1, -0.00001, 3e-6, False),
]
PARAMS = {"c_of": lambda a: -reid.ASSETS[a]["level"], "a": math.exp(3.0), "b": -1000.0}


def obs(price, tick):
    """The generator's rounding expression, verbatim (reid.simulate)."""
    return round(round(price / tick) * tick, 10)


def q_from_pair(kind, p0, p1, asset):
    """MC side: the frozen representation functions on the two observed prices."""
    tick = reid.ASSETS[asset]["tick"]
    if kind == "C0_or_level_residual_unwrapped":
        return (p1 - p0) ** 2
    if kind == "tick_grid":
        x = R.tick_grid([p0, p1], PARAMS["c_of"](asset), tick)
        return (x[1] - x[0]) ** 2
    if kind == "affine_level":
        x = R.affine_level([p0, p1], PARAMS["a"], PARAMS["b"])
        return (x[1] - x[0]) ** 2
    if kind == "log_returns":
        return R.log_returns([p0, p1])[0] ** 2
    if kind == "volatility_time":
        x = R.volatility_time([p0, p1])
        return x[1] - x[0]                         # s_u: the increment of the cumulative series (= r̃²)
    raise ValueError(kind)


def exact(kind, asset, P, mu, sigma):
    """Derivation §3: E[q | P_{u-1}] = Σ_j p_j q_j, j over the tick levels within μ ± 12σ (mass outside < 1e-32)."""
    tick = reid.ASSETS[asset]["tick"]
    p0 = obs(P, tick)
    lo = math.floor(P * math.exp(mu - 12 * sigma) / tick) - 1
    hi = math.ceil(P * math.exp(mu + 12 * sigma) / tick) + 1
    j = np.arange(lo, hi + 1, dtype=np.float64)
    zb = (np.log(np.maximum((np.append(j, hi + 1) - 0.5) * tick, 1e-300) / P) - mu) / sigma   # boundaries (j ± 1/2)·tick
    cdf = 0.5 * np.array([math.erfc(-v / math.sqrt(2)) for v in zb])
    pj = np.diff(cdf)
    p1 = np.array([round(v * tick, 10) for v in j])       # round(j·tick, 10), as the generator
    if kind == "C0_or_level_residual_unwrapped":
        q = (p1 - p0) ** 2
    elif kind == "tick_grid":
        c = PARAMS["c_of"](asset)
        q = ((p1 - c) / tick - (p0 - c) / tick) ** 2
    elif kind == "affine_level":
        q = ((PARAMS["a"] * p1 + PARAMS["b"]) - (PARAMS["a"] * p0 + PARAMS["b"])) ** 2
    elif kind in ("log_returns", "volatility_time"):
        q = np.log(p1 / p0) ** 2
    return float(np.sum(pj * q)), float(np.sum(pj))


def v06_formula(kind, asset, P, mu, sigma):
    """The v0.6 formula (approximate rounding term), for comparison only."""
    tick = reid.ASSETS[asset]["tick"]
    g = math.exp(2 * mu + 2 * sigma ** 2) - 2 * math.exp(mu + sigma ** 2 / 2) + 1
    if kind == "C0_or_level_residual_unwrapped":
        return P * P * g + tick ** 2 / 6
    if kind == "tick_grid":
        return (P / tick) ** 2 * g + 1 / 6
    if kind == "affine_level":
        return PARAMS["a"] ** 2 * (P * P * g + tick ** 2 / 6)
    return sigma ** 2 + mu ** 2 + tick ** 2 / (6 * P * P)


def main(out):
    rows = []
    for ci, (name, asset, P, mu, sigma, registered) in enumerate(CASES):
        tick = reid.ASSETS[asset]["tick"]
        rnd = random.Random(SPEC["seed"] + ci)
        p0 = obs(P, tick)
        p1s = [obs(P * math.exp(mu + sigma * rnd.gauss(0, 1)), tick) for _ in range(SPEC["N"])]
        for kind in KINDS:
            qs = np.array([q_from_pair(kind, p0, p1, asset) for p1 in p1s])
            m, se = float(qs.mean()), float(qs.std(ddof=1) / math.sqrt(len(qs)))
            ex, mass = exact(kind, asset, P, mu, sigma)
            ap = v06_formula(kind, asset, P, mu, sigma)
            z = (m - ex) / se if se > 0 else (0.0 if m == ex else math.inf)
            rows.append({"case": name, "registered_world": registered, "kind": kind, "asset": asset, "P_latent": P,
                         "P_observed": p0, "mu": mu, "sigma": sigma, "sigma_P_over_tick": sigma * P / tick,
                         "exact": ex, "prob_mass": mass, "mc_mean": m, "mc_se": se, "z": z,
                         "rel_err_mc_vs_exact": (m - ex) / ex if ex else None,
                         "pass": abs(z) <= SPEC["z_limit"],
                         "v06_formula": ap, "v06_rel_dev_from_exact": (ap - ex) / ex if ex else None})
    res = {"spec": SPEC, "cases": [list(c) for c in CASES], "rows": rows,
           "all_pass": all(r["pass"] for r in rows),
           "max_abs_z": max(abs(r["z"]) for r in rows),
           "max_v06_rel_dev_registered": max(abs(r["v06_rel_dev_from_exact"]) for r in rows if r["registered_world"]),
           "max_v06_rel_dev_stress": max(abs(r["v06_rel_dev_from_exact"]) for r in rows if not r["registered_world"])}
    Path(out).write_text(json.dumps(res, indent=1))
    print("all_pass", res["all_pass"], "max|z|", round(res["max_abs_z"], 3),
          "v0.6 dev registered", res["max_v06_rel_dev_registered"], "stress", res["max_v06_rel_dev_stress"])


if __name__ == "__main__":
    main(sys.argv[1])
