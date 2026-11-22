"""RIP-3 BUILD check: the W2 U-vol* truth (design v0.4 §4.3) against Monte Carlo of the ACTUAL W2 step mechanism.
Pre-registered in docs/research/RIP3_BUILD_NOTES.md §B1 (cases, N, seeds, acceptance) before this is run.
Same acceptance rule as the RIP-2 check: |MC mean − exact| ≤ 4 MC standard errors, every case must pass.
SYNTHETIC ONLY; development-range seeds 7401+. Usage: python scripts/rip3_w2_truth_verify.py OUT_JSON

Exact side: rip3.uvol_truth_w2 (central sum + closed-form tails, acceptance loop).
Monte Carlo side, independent of that code: z = G / sqrt(Q/ν)·sqrt((ν−2)/ν) drawn exactly as rip3.innovations draws it
(random.gauss, then random.gammavariate(ν/2, 2)), r = μ + s·z, P_u = P·e^r, observed price by the generator's rounding
expression, and the frozen representations.log_returns on [P̃_{u−1}, P̃_u]."""
import json
import math
import random
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from xauusd_swarm import reid                                            # noqa: E402
from xauusd_swarm import representations as REP                         # noqa: E402
from xauusd_swarm import rip3                                           # noqa: E402

SPEC = {"N": 200_000, "seed": 7401, "z_limit": 4.0, "nu": 5}
SIG = {(a, p): reid.ASSETS[a]["vol"] * reid.PERIODS[p]["volx"] for a in range(4) for p in range(4)}
# (name, asset, latent P_{u-1}, s = m_u·f_u·sqrt(h_u), registered world?)
CASES = [
    ("a0_typical", 0, 2340.0, SIG[(0, 2)], True),
    ("a0_spike_shift_max_act", 0, 2340.0, SIG[(0, 2)] * 1.6 * 2 * 3, True),
    ("a1_zero_drift", 1, 34.5, SIG[(1, 1)], True),
    ("a1_spike_shift", 1, 39.0, SIG[(1, 2)] * 1.3 * 2 * 3, True),
    ("a2_low_h", 2, 1.1, SIG[(2, 0)] * 0.9 * 0.5, True),
    ("a2_just_below_half_tick", 2, (110000 + 0.5 - 1e-6) * 1e-5, SIG[(2, 0)] * 0.9, True),
    ("a2_just_above_half_tick", 2, (110000 + 0.5 + 1e-6) * 1e-5, SIG[(2, 0)] * 0.9, True),
    ("a3_mid", 3, 217.5, SIG[(3, 3)], True),
    ("stress_a2_coarse_s_1e-5", 2, 1.1, 1e-5, False),
    ("stress_a0_extreme_s_0.05", 0, 1800.0, 0.05, False),
]


def obs(price, tick):
    return round(round(price / tick) * tick, 10)


# FL-026: a case whose frozen central sum at K_max would exceed this many tick levels is reported as not computable
# (added after the first execution was killed by memory on case 10, before any result was seen).
MAX_LEVELS = 1e10


def main(out):
    nu = SPEC["nu"]
    c = math.sqrt((nu - 2) / nu)
    rows = []
    for ci, (name, asset, P, s, registered) in enumerate(CASES):
        A = reid.ASSETS[asset]
        tick, mu = A["tick"], A["drift"]
        levels_kmax = 2 * P * math.sinh(rip3.SPEC["t_Kmax"] * c * s) / tick
        if levels_kmax > MAX_LEVELS:
            rows.append({"case": name, "registered_world": registered, "asset": asset, "P_latent": P, "s": s,
                         "b": c * s, "computed": False, "levels_at_Kmax": levels_kmax,
                         "reason": "not computable under the frozen algorithm (FL-026)"})
            continue
        rnd = random.Random(SPEC["seed"] + ci)
        p0 = obs(P, tick)
        qs = np.empty(SPEC["N"])
        for i in range(SPEC["N"]):
            G = rnd.gauss(0, 1)
            Q = rnd.gammavariate(nu / 2, 2)
            z = G / math.sqrt(Q / nu) * c
            p1 = obs(P * math.exp(mu + s * z), tick)
            qs[i] = REP.log_returns([p0, p1])[0] ** 2 if p1 > 0 else math.nan
        n0 = int(np.sum(np.isnan(qs)))
        qs = qs[~np.isnan(qs)]
        m, se = float(qs.mean()), float(qs.std(ddof=1) / math.sqrt(len(qs)))
        q, E, K, ok = rip3.uvol_truth_w2(P, mu, c * s, tick)
        z = (m - q) / se if se > 0 else (0.0 if m == q else math.inf)
        rows.append({"case": name, "registered_world": registered, "asset": asset, "P_latent": P, "P_observed": p0,
                     "mu": mu, "s": s, "b": c * s, "s_P_over_tick": s * P / tick, "exact": q, "error_bound": E,
                     "bound_over_q": E / q, "K": K, "accepted": ok, "mc_mean": m, "mc_se": se, "z": z,
                     "mc_zero_price_draws": n0, "rel_err_mc_vs_exact": (m - q) / q, "pass": abs(z) <= SPEC["z_limit"],
                     "computed": True})
    res = {"spec": SPEC, "cases": [list(c_) for c_ in CASES], "rows": rows,
           "all_computed_pass": all(r["pass"] for r in rows if r["computed"]),
           "not_computed": [r["case"] for r in rows if not r["computed"]],
           "max_abs_z": max(abs(r["z"]) for r in rows if r["computed"]),
           "all_accepted": all(r["accepted"] for r in rows if r["computed"])}
    Path(out).write_text(json.dumps(res, indent=1))
    print("all_computed_pass", res["all_computed_pass"], "not_computed", res["not_computed"], "max|z|", round(res["max_abs_z"], 3), "all_accepted", res["all_accepted"])


if __name__ == "__main__":
    main(sys.argv[1])
