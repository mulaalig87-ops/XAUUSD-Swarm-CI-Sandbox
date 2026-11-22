"""RIP-1-D1 — SEPARATE post-hoc DIAGNOSTIC for FL-023 (founder decision OD-S9-08). NOT a RIP-1 result.

Re-computes ONLY the A6 (V0) and A6-V1 predictions for level_residual on the committed RIP-1 data, twice:
  (H) with the historical frozen likelihood (rip1_attack._ll_resid_given_m) — must reproduce the committed predictions
      exactly, which proves the pipeline is the same;
  (E) with the exact wrapped-normal sum (rip2._wrapped_log_density, IC-12), patched into this process only.
The historical RIP-1 result files and report are not read for writing and are not changed. Output: a separate file
with identifier RIP-1-D1. SYNTHETIC ONLY. Usage: python scripts/rip1_diag_fl023.py OUT_JSON"""
import gzip
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from xauusd_swarm import reid                       # noqa: E402
from xauusd_swarm import rip1_attack as A           # noqa: E402
from xauusd_swarm import rip2                       # noqa: E402

RES = ROOT / "docs" / "results" / "rip1"
REP = "level_residual"


def predictions(ll_resid_fn):
    A._ll_resid_given_m = ll_resid_fn               # this process only
    spec = json.loads((RES / "results.json").read_text())["spec"]
    A.SPEC.update(spec)
    z = np.load(RES / f"data_{REP}.npz")
    led = [json.loads(l) for l in gzip.open(RES / "ledger.jsonl.gz").read().decode().splitlines()]
    rows = A.ledger_fields(led)
    out = {"V0": {}, "V1": {}}
    for sc, g in A.SCEN.items():
        fams = [str(f) for f in z[f"F_{sc}"]]
        X = z[f"X_{sc}"]
        groups = [[list(map(float, X[u, i])) for i in range(g)] for u in range(len(fams))]
        out["V0"][sc] = {f: list(A.argmax(A.a6_scores(REP, xs))) for f, xs in zip(fams, groups)}
        out["V1"][sc] = {f: list(A.argmax(A.a6_scores(REP, xs, delta_seen=rows[f]["st.delta"])))
                         for f, xs in zip(fams, groups)}
    return out


def exact_ll_resid_given_m(xs, k, m):
    return rip2.ll_resid_given_m(xs, k, m)


def score(pred, truth):
    n = len(pred)
    a = sum(p[0] == truth[f]["asset"] for f, p in pred.items())
    p_ = sum(p[1] == truth[f]["period"] for f, p in pred.items())
    j = sum(p == [truth[f]["asset"], truth[f]["period"]] for f, p in pred.items())
    return {"units": n, "asset": {"correct": a, "accuracy": round(a / n, 4), "wilson95": reid.wilson(a, n)},
            "period": {"correct": p_, "accuracy": round(p_ / n, 4), "wilson95": reid.wilson(p_, n)},
            "joint": {"correct": j, "accuracy": round(j / n, 4), "wilson95": reid.wilson(j, n)}}


def main(out_path):
    hist_fn = A._ll_resid_given_m
    H = predictions(hist_fn)
    E = predictions(exact_ll_resid_given_m)
    A._ll_resid_given_m = hist_fn
    truth = json.loads((RES / "revealed_truth.json").read_text())
    committed = {v: json.loads((RES / f"predictions_{v}_{REP}.json").read_text())["predictions"] for v in ("V0", "V1")}
    att = {"V0": "A6", "V1": "A6-V1"}
    rows, same = [], True
    for v in ("V0", "V1"):
        for sc in A.SCEN:
            ok = H[v][sc] == committed[v][sc][att[v]]
            same &= ok
            changed = sum(H[v][sc][f] != E[v][sc][f] for f in H[v][sc])
            rows.append({"view": v, "scenario": sc, "attacker": att[v],
                         "historical_code_reproduces_committed": ok,
                         "historical": score(H[v][sc], truth), "exact_sum_diagnostic": score(E[v][sc], truth),
                         "predictions_changed": changed})
    res = {"id": "RIP-1-D1", "kind": "post-hoc diagnostic (FL-023, founder decision OD-S9-08)",
           "NOT_A_RIP1_RESULT": "The historical RIP-1 results (docs/results/rip1/, RIP-1_REPORT.md) stand unchanged and "
                                "are the only RIP-1 results. This file must never replace or be mixed into them.",
           "representation": REP, "rows": rows, "historical_reproduced_exactly": same,
           "exact_predictions": E}
    Path(out_path).write_text(json.dumps(res, indent=1))
    print("historical reproduced:", same)
    for r in rows:
        print(r["view"], r["scenario"], "changed", r["predictions_changed"], "asset H/E",
              r["historical"]["asset"]["accuracy"], r["exact_sum_diagnostic"]["asset"]["accuracy"],
              "joint H/E", r["historical"]["joint"]["accuracy"], r["exact_sum_diagnostic"]["joint"]["accuracy"])


if __name__ == "__main__":
    main(sys.argv[1])
