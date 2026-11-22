"""RIP-2 partial reproduction (evidence for the single registered run, OD-S9-09). Re-executes, with the same frozen code
and registered seeds, the S-ind pipeline for (C0, Δ hidden) and (affine_level, C2, Δ hidden) and (level_residual, C2,
Δ shown), and compares every attacker's asset/period/joint accuracy with docs/results/rip2/results.json EXACTLY.
It calls the same functions run() uses (make_families, _materialise, _data, _attack_all, acc_vectors); it does not call
run(). SYNTHETIC ONLY. Usage: python scripts/rip2_partial_repro.py OUT_JSON"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from xauusd_swarm import rip1_attack as A           # noqa: E402
from xauusd_swarm import rip2 as R                  # noqa: E402


def main(out):
    res = json.loads((ROOT / "docs" / "results" / "rip2" / "results.json").read_text())
    A.SPEC["n"] = R.SPEC["n"]
    sc, g = "ind", 1
    dev = R.make_families(R.SEEDS["dev"] + 1000 * g, R.SPEC["fpc"][sc], g, R.SPEC["n"])
    ev = R.make_families(R.SEEDS["eval"] + 1000 * g, R.SPEC["fpc"][sc], g, R.SPEC["n"])
    dp, ep = R._materialise(dev, R.SPEC["n"]), R._materialise(ev, R.SPEC["n"])
    y = [f["cls"] for f in ev]
    checks = []
    for rep, cond, D, label in (("log_returns", "C0", "hidden", "C0(raw prices)"),
                                ("affine_level", "C2", "hidden", "affine_level"),
                                ("level_residual", "C2", "shown", "level_residual")):
        dx, ex = R._data(rep, cond, dev, dp), R._data(rep, cond, ev, ep)
        P, _, _ = R._attack_all("C0" if cond == "C0" else rep, cond, D, dev, dx, ev, ex, g, sc)
        for att, p in P.items():
            v = R.acc_vectors(p, y)
            got = {t: float(v[t].mean()) for t in v}
            want = [c for c in res["cells"] if c["scenario"] == sc and c["representation"] == label
                    and c["condition"] == cond and c["delta"] == D and c["attacker"] == att][0]
            checks.append({"cell": [sc, label, cond, D, att], "reproduced": got,
                           "original": {t: want[t] for t in got}, "identical": all(got[t] == want[t] for t in got)})
    out_obj = {"id": "RIP-2 partial reproduction", "cells_checked": len(checks), "all_identical": all(c["identical"] for c in checks),
               "checks": checks}
    Path(out).write_text(json.dumps(out_obj, indent=1))
    print("cells", len(checks), "all identical", out_obj["all_identical"])


if __name__ == "__main__":
    main(sys.argv[1])
