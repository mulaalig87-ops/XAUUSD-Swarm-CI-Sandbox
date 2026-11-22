"""WP9-03: run the graded planted-leak test TP-50 (ت1–ت9) and TP-50.0, record them as the matrix row of
the lineage leak check, and write the per-type report. Usage: python scripts/wp9_03_tp50.py OUT_DIR.
SYNTHETIC ONLY. Design FD-01-D38. Matrix-row expectations (declared before the run, FD-01-D38 addendum):
positive control = TP-50 report complete (report_complete == 1; success is completeness, WP7-04 §4);
negative control = TP-50.0 measured and declared (measured == 1; no threshold in the sources)."""
from __future__ import annotations

import hashlib
import json
import sys
import uuid
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from xauusd_swarm.charter import Governance
from xauusd_swarm.controls import ControlsLayer
from xauusd_swarm.custody import CustodyLayer
from xauusd_swarm.identity import public_hex, sign
from xauusd_swarm.inventory import content_sha256, impl_sha256
from xauusd_swarm.leakcheck import TP50, tp50_0, tp50_report
from xauusd_swarm.ledger import AnchorStore, Ledger

ROOT = Path(__file__).resolve().parents[1]


def main(out: Path) -> dict:
    (out / "led").mkdir(parents=True, exist_ok=True)
    (out / "anc").mkdir(exist_ok=True)
    fk, ok, ak = (Ed25519PrivateKey.generate() for _ in range(3))
    F = lambda a, **kw: sign("founder", fk, {"action": a, "nonce": uuid.uuid4().hex, **kw})   # noqa: E731
    cl, co = CustodyLayer(None), ControlsLayer()
    g = Governance(fk.public_key(), Ledger(out / "led" / "ledger.jsonl", anchors=AnchorStore(out / "anc" / "a.jsonl")),
                   extensions=[cl, co])
    for ident, k in (("op", ok), ("aud", ak)):
        g.register_key(F("register_key", identity=ident, public_key_hex=public_hex(k.public_key())))
    cl.commit("role_assigned", F("assign_role", role="court_operator", holder="op"))
    cl.commit("role_assigned", F("assign_role", role="custody_auditor", holder="aud"))
    target = ControlsLayer.target_of("leak_check", "lineage")
    rows = []
    for cid, pol, fn, exp in (("TP50-graded-positive", "positive", tp50_report, {"metric": "report_complete", "op": "==", "value": 1}),
                              ("TP50.0-clean-negative", "negative", tp50_0, {"metric": "measured", "op": "==", "value": 1})):
        w = {"tool": "leak_check:lineage", "control": cid, "spec": TP50}
        co.commit("control_registered", F("register_control", control_id=cid, target=target, polarity=pol, expected=exp,
                  world_sha256=content_sha256(w), impl_sha256=impl_sha256(fn)))
        co.run_control(cid, fn, w, operator="op", key=ok, result_id=f"r-{cid}")
        co.attest_reexecution(f"r-{cid}", fn, w, auditor="aud", key=ak)
        r = co.results[f"r-{cid}"]
        rows.append({"control_id": cid, "polarity": pol, "expected": exp, "observed": r["observed"],
                     "outcome": r["outcome"], "world_sha256": r["world_sha256"], "impl_sha256": r["impl_sha256"]})
    text = "TP-50 (ت1–ت9) report completeness + TP-50.0 declared: FD-01-D38"
    co.commit("tool_row_registered", F("register_tool_row", tool_kind="leak_check", tool_id="lineage",
              controls=[r["control_id"] for r in rows], criterion={"text": text, "sha256": content_sha256(text)},
              cost_metric="compute seconds"))
    res = {"component": "WP9-03 — graded planted-leak test TP-50 and TP-50.0", "synthetic_only": True,
           "design_decision": "FD-01-D38", "results": rows,
           "module_sha256": {"leakcheck.py": hashlib.sha256((ROOT / "src" / "xauusd_swarm" / "leakcheck.py")
                                                           .read_bytes().replace(b"\r\n", b"\n")).hexdigest()}}
    (out / "results.json").write_text(json.dumps(res, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
    return res


if __name__ == "__main__":
    r = main(Path(sys.argv[1]))
    rep = r["results"][0]["observed"]["report"]
    for row in rep["rows"]:
        print(row["type"], row["frac"], "lineage", row["lineage_rate"], "stat", row["stat_rejection_rate"], row["states"])
    print("blind spots:", rep["known_blind_spots"], "t8 smallest tested fraction with inflation:", rep["t8_smallest_tested_fraction_with_inflation"])
    print(r["results"][1]["observed"], [x["outcome"] for x in r["results"]])
