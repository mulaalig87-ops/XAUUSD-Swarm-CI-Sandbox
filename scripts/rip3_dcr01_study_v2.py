"""DCR-01 study, revision 2 (review R-B1, MAJOR 2: bootstrap size). Same statistic, same rule and same Bonferroni
correction as scripts/rip3_dcr01_study.py; only the number of bootstrap samples changes, and the stability of the
upper bounds across sizes and seeds is reported. Development data only (B3: dev 6101, units 6102). SYNTHETIC ONLY.
Pre-registered by its commit, before execution. Usage: python scripts/rip3_dcr01_study_v2.py B3_DIR OUT_JSON

Bootstrap: stratified (by class) paired family bootstrap; one index set per sample shared by A6, A7x4, A8x4 and by
the three targets of the scenario. Primary: B = 100,000, numpy default_rng(6119). Stability: B ∈ {2,000, 10,000,
50,000, 100,000} with seed 6119 (nested: the first B samples of the same stream), and B = 100,000 with seeds 6120
and 6121. Statistic per sample b and cell: D_b = mean(A6)_b − max(mean(A7)_b, mean(A8)_b) (re-selected per sample).
UB = the (1 − 0.05/9) quantile of D_b (numpy percentile, linear interpolation), Bonferroni over the 9 B-LR cells.
Also reported per cell: the Monte Carlo standard error of UB across the three seeds at B = 100,000.
Rules (unchanged): R0 pass iff UB ≤ 0 in all 9 gating cells; R-NI(δ) pass iff UB ≤ δ (δ NOT chosen here)."""
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from xauusd_swarm import rip3 as R                                      # noqa: E402

SPEC = {"B_primary": 100_000, "B_ladder": [2_000, 10_000, 50_000, 100_000], "seed": 6119, "extra_seeds": [6120, 6121],
        "alpha": 0.05, "cells_gating": 9, "chunk": 5_000, "attackers": ["A6", "A7x4", "A8x4"]}


def strata(labels):
    lab = [tuple(c) for c in labels]
    return [np.array([i for i, c in enumerate(lab) if c == k]) for k in sorted(set(lab))]


def draw(st, B, rng, chunk):
    """Yields index arrays (chunk × n) of a stratified bootstrap, drawn stratum by stratum in class order."""
    done = 0
    while done < B:
        m = min(chunk, B - done)
        parts = [s[rng.integers(0, len(s), size=(m, len(s)))] for s in st]
        yield np.concatenate(parts, axis=1)
        done += m


def d_samples(idn, B, seed, chunk):
    lab = idn["labels"]
    V = {a: {t: R.acc_vectors(idn["pred"][a], lab)[t].astype(float) for t in R.TARGETS} for a in SPEC["attackers"]}
    rng = np.random.default_rng(seed)
    out = {t: [] for t in R.TARGETS}
    for I in draw(strata(lab), B, rng, chunk):
        for t in R.TARGETS:
            m6, m7, m8 = (V[a][t][I].mean(axis=1) for a in SPEC["attackers"])
            out[t].append(m6 - np.maximum(m7, m8))
    return {t: np.concatenate(v) for t, v in out.items()}


def main(b3_dir, out):
    q = 100 * (1 - SPEC["alpha"] / SPEC["cells_gating"])
    res = {"spec": SPEC, "upper_percentile": q, "data": "development only (B3: dev 6101, units 6102)",
           "disclosure": "DCR-01 was proposed after seeing these development results; no evaluation (6201) or "
                         "confirmatory (6301) data exist or were used.", "cells": []}
    for cand in ("B-LR", "B-AF"):
        job = json.loads((Path(b3_dir) / f"build__{cand}__W1.json").read_text())
        for sc in R.SCEN:
            idn = job["identity"][sc]
            main_d = d_samples(idn, SPEC["B_primary"], SPEC["seed"], SPEC["chunk"])
            extra = [d_samples(idn, SPEC["B_primary"], s, SPEC["chunk"]) for s in SPEC["extra_seeds"]]
            for t in R.TARGETS:
                D = main_d[t]
                ladder = {str(B): float(np.percentile(D[:B], q)) for B in SPEC["B_ladder"]}
                ubs = [ladder[str(SPEC["B_primary"])]] + [float(np.percentile(e[t], q)) for e in extra]
                res["cells"].append({
                    "candidate": cand, "gating": cand == "B-LR", "scenario": sc, "target": t,
                    "UB_primary_B100000_seed6119": ubs[0], "UB_by_B_seed6119": ladder,
                    "UB_B100000_by_seed": dict(zip([SPEC["seed"]] + SPEC["extra_seeds"], ubs)),
                    "UB_seed_spread": max(ubs) - min(ubs), "UB_mc_sd_across_seeds": float(np.std(ubs, ddof=1)),
                    "D_resampled_mean": float(D.mean()), "R0_pass": ubs[0] <= 0.0})
    g = [c for c in res["cells"] if c["gating"]]
    res["R0_pass_all_gating"] = all(c["R0_pass"] for c in g)
    res["R0_failing_gating_cells"] = [f"{c['scenario']}|{c['target']}" for c in g if not c["R0_pass"]]
    res["max_gating_UB_primary_INFORMATION_ONLY"] = max(c["UB_primary_B100000_seed6119"] for c in g)
    res["R0_decision_same_for_all_B_and_seeds"] = all(
        (all(v <= 0 for v in c["UB_by_B_seed6119"].values()) or all(v > 0 for v in c["UB_by_B_seed6119"].values()))
        and (all(v <= 0 for v in c["UB_B100000_by_seed"].values()) or all(v > 0 for v in c["UB_B100000_by_seed"].values()))
        for c in g)
    Path(out).write_text(json.dumps(res, indent=1))
    print("R0 pass:", res["R0_pass_all_gating"], res["R0_failing_gating_cells"],
          "stable:", res["R0_decision_same_for_all_B_and_seeds"])


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
