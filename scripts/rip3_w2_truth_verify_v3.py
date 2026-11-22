"""RIP-3 BUILD check B1, attempt 3 (founder directive of 2026-11-19): all ten cases, with case 10 computed by the
bounded block method (IC3-22), and the block method verified against the exact sum where the exact sum is feasible.
Pre-registered in docs/research/RIP3_BUILD_NOTES.md §B1 (attempt 3) before this is run. SYNTHETIC ONLY.
Usage: python scripts/rip3_w2_truth_verify_v3.py OUT_JSON [ATTEMPT]   (attempt 4: threshold 1e9, see notes)

Part A — Monte Carlo (unchanged from attempts 1–2: same 10 cases, N = 200,000, seeds 7401 + index, rule |z| ≤ 4):
  the exact side is rip3.uvol_truth_w2 as used in production (exact sum up to rip3.BLOCK_THRESHOLD levels, blocks above;
  2e7 in attempt 3, 1e9 from attempt 4).
Part B — equivalence of the block method: for every case below whose exact sum has at most 2.5e8 levels, the
  central sum at K ∈ {50, 200, 400} by the exact sum and by the block method; rule |exact − blocked| ≤ proven bound
  + 1e-12·|exact| (floating-point allowance: numpy pairwise summation, error ≲ log2(n)·ε·Σ|terms|).
  Cases: the nine computable cases of Part A, and three medium cases at the largest W2 volatility measured on 800
  development series (b = 0.0206, FL-026)."""
import json
import math
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import rip3_w2_truth_verify as V1                                       # noqa: E402  (attempts 1–2: cases, MC)
from xauusd_swarm import reid                                           # noqa: E402
from xauusd_swarm import representations as REP                         # noqa: E402
from xauusd_swarm import rip3                                           # noqa: E402

C = math.sqrt(0.6)
MEDIUM = [("m_a1_b0.0206", 1, 39.0, 0.0206 / C), ("m_a0_b0.0117", 0, 2340.0, 0.0117 / C),
          ("m_a3_b0.0100", 3, 217.5, 0.0100 / C)]
EXACT_LIMIT = 2.5e8
FP_REL = 1e-12


def mc(ci, asset, P, s):
    A = reid.ASSETS[asset]
    tick, mu, nu = A["tick"], A["drift"], V1.SPEC["nu"]
    import random
    rnd = random.Random(V1.SPEC["seed"] + ci)
    p0 = V1.obs(P, tick)
    qs = np.empty(V1.SPEC["N"])
    for i in range(V1.SPEC["N"]):
        G = rnd.gauss(0, 1)
        Q = rnd.gammavariate(nu / 2, 2)
        z = G / math.sqrt(Q / nu) * C
        p1 = V1.obs(P * math.exp(mu + s * z), tick)
        qs[i] = REP.log_returns([p0, p1])[0] ** 2 if p1 > 0 else math.nan
    n0 = int(np.sum(np.isnan(qs)))
    qs = qs[~np.isnan(qs)]
    return float(qs.mean()), float(qs.std(ddof=1) / math.sqrt(len(qs))), n0


def main(out, attempt=3):
    rows, eq = [], []
    for ci, (name, asset, P, s, registered) in enumerate(V1.CASES):
        A = reid.ASSETS[asset]
        t0 = time.time()
        q, E, K, ok = rip3.uvol_truth_w2(P, A["drift"], C * s, A["tick"])
        levels = 2 * P * math.sinh(K * C * s) / A["tick"]
        m, se, n0 = mc(ci, asset, P, s)
        z = (m - q) / se
        rows.append({"case": name, "registered_world": registered, "asset": asset, "P_latent": P, "s": s, "b": C * s,
                     "exact": q, "error_bound": E, "bound_over_q": E / q, "K": K, "accepted": ok,
                     "levels_at_K": levels, "method": "blocks" if levels > rip3.BLOCK_THRESHOLD else "exact sum",
                     "mc_mean": m, "mc_se": se, "z": z, "mc_zero_price_draws": n0, "rel_err_mc_vs_exact": (m - q) / q,
                     "pass": abs(z) <= V1.SPEC["z_limit"], "seconds": round(time.time() - t0, 1)})
    for name, asset, P, s in [(c[0], c[1], c[2], c[3]) for c in V1.CASES] + MEDIUM:
        A = reid.ASSETS[asset]
        tick, mu, b = A["tick"], A["drift"], C * s
        p0 = round(round(P / tick) * tick, 10)
        for K in (50.0, 200.0, 400.0):
            jlo = max(1, math.floor(P * math.exp(mu - K * b) / tick - 0.5))
            jhi = math.ceil(P * math.exp(mu + K * b) / tick + 0.5)
            if jhi - jlo + 1 > EXACT_LIMIT:
                eq.append({"case": name, "K": K, "levels": jhi - jlo + 1, "skipped": "exact sum infeasible"})
                continue
            ex = rip3._central_exact(P, mu, b, tick, K, p0, jlo, jhi)
            bl, bd, nb, ne = rip3._central_blocked(P, mu, b, tick, K, p0)
            d = abs(ex - bl)
            eq.append({"case": name, "K": K, "levels": jhi - jlo + 1, "blocks": nb, "exact_levels": ne,
                       "block_method_applied": nb > 0, "exact": ex, "blocked": bl, "abs_diff": d, "bound": bd,
                       "diff_over_bound": d / bd if bd > 0 else (0.0 if d == 0 else math.inf),
                       "pass": d <= bd + FP_REL * abs(ex)})
    res = {"attempt": attempt, "spec": V1.SPEC, "block": {"threshold_levels": rip3.BLOCK_THRESHOLD,
                                                    "exact_below_j": rip3.BLOCK_EXACT_J, "dy": rip3.BLOCK_DY},
           "rows": rows, "equivalence": eq,
           "all_mc_pass": all(r["pass"] for r in rows), "all_accepted": all(r["accepted"] for r in rows),
           "max_abs_z": max(abs(r["z"]) for r in rows),
           "all_equivalence_pass": all(e["pass"] for e in eq if "pass" in e),
           "equivalence_checked_with_blocks": sum(1 for e in eq if e.get("block_method_applied"))}
    Path(out).write_text(json.dumps(res, indent=1))
    print("MC all pass", res["all_mc_pass"], "max|z|", round(res["max_abs_z"], 2), "accepted", res["all_accepted"],
          "equivalence", res["all_equivalence_pass"], "with blocks", res["equivalence_checked_with_blocks"])


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 3)
