"""DCR-01 study (RIP-3 design v0.5 draft): the C-V2 rule "strongest of A7 and A8 against A6", computed on the BUILD
development data only (B3 jobs: seeds 6101 / 6102). SYNTHETIC ONLY. Not a gate of the frozen design v0.4.
Usage: python scripts/rip3_dcr01_study.py B3_DIR OUT_JSON

Bootstrap: stratified (by class) paired resampling of the family units, the same index set for A6, A7 (x4) and
A8 (x4) and for all three targets of a scenario; B = 2000; numpy default_rng(6119) (development range), sets drawn
per candidate in the order ind, g4, g16. In every bootstrap sample b and cell (scenario, target):
D_b = mean(A6)_b − max(mean(A7)_b, mean(A8)_b): the stronger alternative is re-selected inside each sample.
One-sided upper bound: the (1 − α/m) percentile of D_b, α = 0.05, Bonferroni over the m = 9 cells
(3 scenarios × 3 targets) of the gating baseline B-LR (simultaneous level ≥ 95 %).
Rules reported:
  R0 (strict, the directive's recommendation): pass iff every B-LR cell has UB ≤ 0
      (meaning: with familywise confidence 95 %, the strongest alternative is not less accurate than A6).
  R-NI(δ) (non-inferiority with margin δ): pass iff every B-LR cell has UB ≤ δ. δ is NOT chosen here; the
      smallest δ that would pass on these development data is reported as information, and it must not be used to
      set δ without that disclosure.
B-AF is computed the same way and reported, not gating (v0.5)."""
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from xauusd_swarm import rip3 as R                                      # noqa: E402

SPEC = {"B": 2000, "seed": 6119, "alpha": 0.05, "cells_gating": 9, "attackers": ["A6", "A7x4", "A8x4"]}


def main(b3_dir, out):
    rng = np.random.default_rng(SPEC["seed"])
    q = 100 * (1 - SPEC["alpha"] / SPEC["cells_gating"])
    res = {"spec": SPEC, "upper_percentile": q, "data": "development only (B3: dev 6101, units 6102)",
           "disclosure": "DCR-01 was proposed after seeing these development results; no evaluation (6201) or "
                         "confirmatory (6301) data exist or were used.", "cells": []}
    for cand in ("B-LR", "B-AF"):
        job = json.loads((Path(b3_dir) / f"build__{cand}__W1.json").read_text())
        for sc in R.SCEN:
            idn = job["identity"][sc]
            lab = idn["labels"]
            sets = R.bootstrap_sets(lab, SPEC["B"], rng)
            V = {a: R.acc_vectors(idn["pred"][a], lab) for a in SPEC["attackers"]}
            for t in R.TARGETS:
                m = {a: np.array([V[a][t][s].mean() for s in sets]) for a in SPEC["attackers"]}
                alt = np.maximum(m["A7x4"], m["A8x4"])
                D = m["A6"] - alt
                which = np.where(m["A7x4"] >= m["A8x4"], "A7", "A8")
                ub = float(np.percentile(D, q))
                res["cells"].append({
                    "candidate": cand, "gating": cand == "B-LR", "scenario": sc, "target": t,
                    "A6": float(V["A6"][t].mean()), "A7x4": float(V["A7x4"][t].mean()), "A8x4": float(V["A8x4"][t].mean()),
                    "D_point_resampled_mean": float(D.mean()), "UB_one_sided_bonferroni": ub,
                    "share_samples_A7_strongest": float(np.mean(which == "A7")), "R0_pass": ub <= 0.0})
    g = [c for c in res["cells"] if c["gating"]]
    res["R0_pass_all_gating"] = all(c["R0_pass"] for c in g)
    res["R0_failing_gating_cells"] = [f"{c['scenario']}|{c['target']}" for c in g if not c["R0_pass"]]
    res["smallest_delta_passing_on_dev_INFORMATION_ONLY"] = max(c["UB_one_sided_bonferroni"] for c in g)
    Path(out).write_text(json.dumps(res, indent=1))
    print("R0 pass:", res["R0_pass_all_gating"], "failing:", res["R0_failing_gating_cells"],
          "smallest delta (info):", res["smallest_delta_passing_on_dev_INFORMATION_ONLY"])


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
