"""Independent re-scoring of RIP-1 (audit R1-04). Uses ONLY the committed predictions and the revealed truth
(no project code): recomputes, per view × representation × scenario × attacker, the correct counts for asset,
period and joint, and compares them with docs/results/rip1/results.json. Exit code 0 = every row matches.
Usage: python scripts/rip1_rescore.py [RESULT_DIR]"""
import json
import sys
from pathlib import Path

res = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parents[1] / "docs" / "results" / "rip1")
truth = json.loads((res / "revealed_truth.json").read_text())
rows = json.loads((res / "results.json").read_text())["rows"]
want = {(r["view"], r["representation"], r["scenario"], r["attacker"]):
        (r["units"], r["asset"]["correct"], r["period"]["correct"], r["joint"]["correct"]) for r in rows}
got = {}
for f in sorted(res.glob("predictions_*.json")):
    body = json.loads(f.read_text())
    for sc, atts in body["predictions"].items():
        for att, pred in atts.items():
            y = {fam: (truth[fam]["asset"], truth[fam]["period"]) for fam in pred}
            got[(body["view"], body["rep"], sc, att)] = (
                len(pred),
                sum(p[0] == y[k][0] for k, p in pred.items()),
                sum(p[1] == y[k][1] for k, p in pred.items()),
                sum(tuple(p) == y[k] for k, p in pred.items()))
bad = sorted(k for k in set(want) | set(got) if want.get(k) != got.get(k))
print(f"rows recomputed: {len(got)}; rows in results.json: {len(want)}; mismatches: {len(bad)}")
for k in bad[:20]:
    print("MISMATCH", k, want.get(k), got.get(k))
sys.exit(1 if bad else 0)
