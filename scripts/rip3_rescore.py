"""RIP-3 independent re-score (C-R1). Recomputes, from the stored per-unit predictions and per-family utility values
only, every per-attacker accuracy, the maximum-over-attackers identity and the utility means, WITHOUT importing
rip3.evaluate, and compares them with an assembled results file. SYNTHETIC ONLY.
Usage: python scripts/rip3_rescore.py JOBS_DIR SET RESULTS_JSON"""
import json
import sys
from pathlib import Path

ORDER = ["A6", "A7x4", "A8x4", "A1", "A2x4", "A3", "A4a", "A4b"]


def acc(pred, lab, t):
    hit = []
    for p, y in zip(pred, lab):
        if t == "asset":
            hit.append(p[0] == y[0])
        elif t == "period":
            hit.append(p[1] == y[1])
        else:
            hit.append(p[0] == y[0] and p[1] == y[1])
    return sum(hit) / len(hit)


def main(jobs_dir, set_name, results):
    res = json.loads(Path(results).read_text())
    mism = []
    for p in sorted(Path(jobs_dir).glob(f"{set_name}__*__W?.json")):
        if "__truth__" in p.name:
            continue
        j = json.loads(p.read_text())
        for sc, idn in j["identity"].items():
            row = [r for r in res["matrix"] if r["candidate"] == j["candidate"] and r["world"] == j["world"]
                   and r["scenario"] == sc][0]
            for t in ("asset", "period", "joint"):
                accs = {a: acc(v, idn["labels"], t) for a, v in idn["pred"].items()}
                for a, v in accs.items():
                    if abs(v - row["per_attacker"][a][t]) > 1e-12:
                        mism.append((p.name, sc, a, t))
                best = max((a for a in ORDER if a in accs), key=lambda a: (accs[a], -ORDER.index(a)))
                if best != row[f"I_{t}_attacker"] or abs(accs[best] - row[f"I_{t}"]) > 1e-12:
                    mism.append((p.name, sc, "max", t))
        if j.get("utility"):
            fam = j["utility"]["families"]
            fl = res["floors"][j["candidate"]][j["world"]]
            for k in ("uact_planted", "uact_null", "uevent_success", "uevent_flag_null") + \
                     (("uvol_rho_planted", "uvol_rho_null") if "uvol_rho_planted" in fam[0] else ()):
                m = sum(float(r[k]) for r in fam) / len(fam)
                if abs(m - fl[k][0]) > 1e-12:
                    mism.append((p.name, "utility", k))
    print("mismatches", len(mism))
    for x in mism[:20]:
        print(x)
    return mism


if __name__ == "__main__":
    sys.exit(1 if main(*sys.argv[1:4]) else 0)
