"""RIP-3 partial reproduction (C-R2): recompute from scratch, with the committed code, a fixed sample of stored
per-unit predictions (A6 where tractable, otherwise A8 needs the full development set and is not sampled) and of
per-family utility values, and compare them exactly. SYNTHETIC ONLY.
Usage: python scripts/rip3_partial_repro.py JOBS_DIR SET OUT_JSON [--units 3]"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from xauusd_swarm import reid                       # noqa: E402
from xauusd_swarm import rip1_attack as A          # noqa: E402
from xauusd_swarm import rip3 as R                 # noqa: E402


def main(jobs_dir, set_name, out, units=3):
    base = R.SET_BASE[set_name]
    rows = []
    for p in sorted(Path(jobs_dir).glob(f"{set_name}__*__W?.json")):
        if "__truth__" in p.name:
            continue
        j = json.loads(p.read_text())
        cand, world = j["candidate"], j["world"]
        tcand = "M1" if cand == R.CONTROL else cand
        for sc, g in R.SCEN.items():
            idn = j["identity"].get(sc)
            if not idn or "A6" not in idn["pred"]:
                continue
            ev = R.eval_families(base, "eval", world, g, R.SPEC["fpc"][sc])
            for ui in range(min(units, len(ev))):
                f = ev[ui]
                xs = [R.transform(tcand, R.path(world, f["cls"], R.innovations(world, f["cls"], R.member_stream(f, m),
                                                                              R.SPEC["n"]))[1], f["cls"][0], f)
                      for m in range(g)]
                d = reid.ASSETS[f["cls"][0]]["tick"] if cand == R.CONTROL else None
                pred = list(A.argmax(R.a6_scores(tcand, xs, d)))
                rows.append({"job": p.name, "scenario": sc, "unit": ui, "stored": idn["pred"]["A6"][ui],
                             "recomputed": pred, "identical": pred == idn["pred"]["A6"][ui]})
        if j.get("utility"):
            truth = json.loads((Path(jobs_dir) / f"{set_name}__truth__{world}.json").read_text())
            pairs = R.utility_pairs(base, world)
            for ui in range(min(units, len(pairs))):
                f, fn = pairs[ui]
                r = R.utility_family(world, f, fn, [cand], R.SPEC["n"], truth["pairs"][ui]["q_planted"],
                                     truth["pairs"][ui]["q_null"])[cand]
                st = j["utility"]["families"][ui]
                same = all(r[k] == st[k] for k in r)
                rows.append({"job": p.name, "scenario": "utility", "unit": ui, "identical": same})
    res = {"rows": rows, "checked": len(rows), "all_identical": all(r["identical"] for r in rows)}
    Path(out).write_text(json.dumps(res, indent=1))
    print("checked", len(rows), "all_identical", res["all_identical"])
    return res


if __name__ == "__main__":
    u = int(sys.argv[sys.argv.index("--units") + 1]) if "--units" in sys.argv else 3
    main(sys.argv[1], sys.argv[2], sys.argv[3], u)
