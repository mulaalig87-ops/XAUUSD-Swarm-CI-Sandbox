"""RIP-3 BUILD check: the A6 likelihoods of M1 (scale-invariant) and M2 (secret scale, w = 1, 2, 4) against an
independent dense quadrature. Pre-registered in docs/research/RIP3_BUILD_NOTES.md §B2 before this is run.
SYNTHETIC ONLY; development-range families (seed 6102, role 'a6check'). Usage: python scripts/rip3_a6_verify.py OUT_JSON

Production side: rip3.ll_scale_invariant / rip3.ll_secret_scale (windowed trapezoid, IC3-12).
Reference side (amended before any execution, see RIP3_BUILD_NOTES §B2): (i) algebra — the integrand evaluated directly
from the Gaussian log-density of u·x equals the quadratic-coefficient form at 101 points over the production window
(|difference| ≤ 1e-6); (ii) quadrature — the coefficient form integrated on a non-uniform grid of 4 × 400,001 points
(whole range, both bounds, mode window), trapezoid. Acceptance: (i) in every comparison, and
|production − reference| ≤ 1e-4 (log units) in every comparison."""
import json
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from xauusd_swarm import rip2                                           # noqa: E402
from xauusd_swarm import rip3                                           # noqa: E402

SPEC = {"tol": 1e-4, "algebra_tol": 1e-6, "base": 6102, "role": "a6check", "family_classes": [(0, 2), (1, 0), (2, 3), (3, 1)],
        "g": [1, 4, 16], "M1_range": (-20.0, 5.0)}


def loglik_direct(xs, mu, s, v):
    """Σ_members Σ_t log N(e^v·x_t; μ, s_t) + n·v, evaluated directly on the grid v."""
    tot = np.zeros(len(v))
    for x in xs:
        x = np.asarray(x, dtype=float)
        st = s[:len(x)]
        u = np.exp(v)[:, None]
        tot += np.sum(-0.5 * ((u * x[None, :] - mu) / st[None, :]) ** 2 - np.log(st)[None, :]
                      - 0.5 * math.log(2 * math.pi), axis=1) + len(x) * v
    return tot


def coef_form(T, v):
    return sum(rip3._g(v, *t) for t in T)


def algebra_check(xs, mu, s, T, lo, hi):
    v = np.linspace(lo, hi, 101)
    return float(np.max(np.abs(loglik_direct(xs, mu, s, v) - coef_form(T, v))))


def reference(T, lo, hi, mode, sd):
    parts = [np.linspace(lo, hi, 400001), np.linspace(lo, min(hi, lo + 0.01), 400001),
             np.linspace(max(lo, hi - 0.01), hi, 400001)]
    if lo < mode < hi:
        parts.append(np.linspace(max(lo, mode - 15 * sd), min(hi, mode + 15 * sd), 400001))
    v = np.unique(np.concatenate(parts))
    gv = coef_form(T, v)
    m = float(gv.max())
    return m + math.log(float(np.trapezoid(np.exp(gv - m), v)))


def main(out):
    rows = []
    for fc in SPEC["family_classes"]:
        for g in SPEC["g"]:
            fam = rip3.make_family(SPEC["base"], SPEC["role"], "W1", g, fc, 0)
            obs = [rip3.path("W1", fc, rip3.innovations("W1", fc, rip3.member_stream(fam, m), 512))[1] for m in range(g)]
            for cand in ["M1", "M2w1", "M2w2", "M2w4"]:
                xs = [rip3.transform(cand, o, fc[0], fam) for o in obs]
                for c in rip3.CLASSES:
                    k = rip2.class_params(c)
                    mu, s = k["mu"], k["s"][1:]
                    T = [rip3._quad_terms(x, mu, s[:len(x)]) for x in xs]
                    if cand == "M1":
                        prod = sum(rip3.ll_scale_invariant(x, mu, s[:len(x)]) for x in xs)
                        ref, alg = 0.0, 0.0
                        for x, t in zip(xs, T):
                            v0, sd = rip3._mode(t[0], t[1], t[3])
                            ref += reference([t], *SPEC["M1_range"], v0, sd)
                            alg = max(alg, algebra_check([x], mu, s, [t], v0 - 12 * sd, v0 + 12 * sd))
                    else:
                        w = int(cand[3:])
                        Aq, Bq, C, n = (sum(t[i] for t in T) for i in range(4))
                        v0, sd = rip3._mode(Aq, Bq, n)
                        prod = rip3.ll_secret_scale(xs, mu, s, w)
                        ref = reference(T, -w, w, v0, sd) - math.log(2 * w)
                        alg = algebra_check(xs, mu, s, T, -w, w)
                    rows.append({"family_class": list(fc), "g": g, "candidate": cand, "class": list(c),
                                 "production": prod, "reference": ref, "abs_diff": abs(prod - ref),
                                 "algebra_max_abs_diff": alg,
                                 "pass": abs(prod - ref) <= SPEC["tol"] and alg <= SPEC["algebra_tol"]})
    res = {"spec": {k: (v if not isinstance(v, tuple) else list(v)) for k, v in SPEC.items()}, "rows": rows,
           "comparisons": len(rows), "all_pass": all(r["pass"] for r in rows),
           "max_abs_diff": max(r["abs_diff"] for r in rows)}
    Path(out).write_text(json.dumps(res, indent=1))
    print("comparisons", len(rows), "all_pass", res["all_pass"], "max_abs_diff", res["max_abs_diff"])


if __name__ == "__main__":
    main(sys.argv[1])
