"""RIP-3 BUILD-stage validation on DEVELOPMENT-range seeds only (design v0.4 §9 step 2; RIP3_BUILD_NOTES §B3, §B4).
Pre-registered before it is run. SYNTHETIC ONLY. Never touches the registered sets (6201 evaluation, 6301 confirmatory).

  B3  A7 validation (C-V2 rule, IC3-19) on B-LR and B-AF in W1, full development sizes, units from seed 6102.
      Also reports A8 beside A6 and A7 (design §4.1), and the A7 Ledoit–Wolf shrinkage.
  B4  W2 generator moments (C-V1, IC3-20) on development-range series (seed 6102, role 'moments').

Usage: python scripts/rip3_build_validate.py OUT_DIR [b3|b4|all]"""
import json
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from xauusd_swarm import reid                                            # noqa: E402
from xauusd_swarm import rip3 as R                                      # noqa: E402

MOMENTS = {"series_per_class": 50, "n": 512, "z_limit": 4.0, "t_points": [-3.0, -2.0, -1.0, 0.0, 1.0, 2.0, 3.0]}


def b3(out):
    R.run_jobs(out, "build", ["B-LR", "B-AF"], worlds=("W1",))
    jobs = R.load_jobs(out, "build")
    ev = R.evaluate(jobs, "build")
    rows = []
    for r in ev["matrix"]:
        rows.append({k: r[k] for k in ("candidate", "world", "scenario", "per_attacker", "I_joint_attacker",
                                       "unsaturated", "attacker_sensitive")})
    shrink = {f"{c}|{w}|{sc}": jobs[(c, w)]["identity"][sc]["a7_shrinkage_x4"] for (c, w) in jobs for sc in R.SCEN}
    res = {"check": "B3 A7 validation (C-V2 rule) on development seeds", "c_v2": ev["gates"]["C-V2"],
           "rows": rows, "a7_shrinkage_x4": shrink}
    (Path(out) / "B3_a7_validation.json").write_text(json.dumps(res, indent=1, default=str))
    print("B3 C-V2 pass:", ev["gates"]["C-V2"]["pass"])


def b4(out):
    """z-moments with finite-variance estimators get the 4-SE rule; E[eps²] and E[h] are reported without a rule
    (eps has no finite fourth moment, design §4.3)."""
    nu = R.SPEC["garch"]["nu"]
    c = math.sqrt((nu - 2) / nu)
    zs, ratio_e2, ratio_h = [], [], []
    for cls in R.CLASSES:
        sk2 = R.sigma_k(*cls) ** 2
        for i in range(MOMENTS["series_per_class"]):
            fam = R.make_family(R.SEEDS["build_holdout"], "moments", "W2", 1, cls, i)
            inno = R.innovations("W2", cls, R.member_stream(fam, 0), MOMENTS["n"])
            e, h = np.array(inno["eps"]), np.array(inno["h"])
            zs.append(e / np.sqrt(h))
            ratio_e2.append(float(np.mean(e * e)) / sk2)
            ratio_h.append(float(np.mean(h)) / sk2)
    z = np.concatenate(zs)
    N = len(z)
    checks = []
    m, se = float(z.mean()), float(z.std(ddof=1) / math.sqrt(N))
    checks.append({"moment": "E z", "spec": 0.0, "estimate": m, "se": se, "z": m / se})
    v = z * z
    m2, se2 = float(v.mean()), float(v.std(ddof=1) / math.sqrt(N))
    checks.append({"moment": "Var z (E z²)", "spec": 1.0, "estimate": m2, "se": se2, "z": (m2 - 1.0) / se2})
    for tp in MOMENTS["t_points"]:
        y = tp / c                                            # z ≤ tp  ⇔  T ≤ tp / c
        p = float(R.t_cdf5(y)) if nu == 5 else None
        f = float(np.mean(z <= tp))
        sef = math.sqrt(p * (1 - p) / N)
        checks.append({"moment": f"P(z <= {tp})", "spec": p, "estimate": f, "se": sef, "z": (f - p) / sef if sef else 0.0})
    for ck in checks:
        ck["pass"] = abs(ck["z"]) <= MOMENTS["z_limit"]
    res = {"check": "B4 W2 moments (C-V1)", "spec": MOMENTS, "draws": N, "checks": checks,
           "all_pass": all(ck["pass"] for ck in checks),
           "reported_without_rule": {"mean over series of mean(eps²)/sigma_k²": float(np.mean(ratio_e2)),
                                     "median": float(np.median(ratio_e2)),
                                     "mean over series of mean(h)/sigma_k²": float(np.mean(ratio_h)),
                                     "note": "eps has no finite unconditional fourth moment (design §4.3)"}}
    (Path(out) / "B4_w2_moments.json").write_text(json.dumps(res, indent=1))
    print("B4 all_pass:", res["all_pass"])


if __name__ == "__main__":
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    what = sys.argv[2] if len(sys.argv) > 2 else "all"
    if what in ("b4", "all"):
        b4(out)
    if what in ("b3", "all"):
        b3(out)
