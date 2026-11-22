"""WP9-02 (part 2): run TP-47 (C0 gate) and TP-46 (court) controls and record each result in a ledger.

Usage:  python scripts/wp9_02_gate_court_controls.py OUT_DIR   → OUT_DIR/results.json (+ ledger).
SYNTHETIC ONLY; keys generated per run (engineering test). Criteria: FD-01-D32 (pre-registered).
"""
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
from xauusd_swarm.gate_court_controls import EXPECTED, c0_world_spec, court_world_spec, run_c0_world, run_court_world
from xauusd_swarm.identity import public_hex, sign
from xauusd_swarm.inventory import content_sha256, impl_sha256
from xauusd_swarm.ledger import AnchorStore, Ledger

ROOT = Path(__file__).resolve().parents[1]
PLAN = [("c0_gate", "C0", run_c0_world, [("TP47-feed-positive", "positive", c0_world_spec(1)),
                                         ("TP47-processing-positive", "positive", c0_world_spec(2)),
                                         ("TP47-order-positive", "positive", c0_world_spec(3)),
                                         ("TP47-clean-negative", "negative", c0_world_spec(None))]),
        ("court", "court", run_court_world, [("TP46-planted-positive", "positive", court_world_spec("real")),
                                             ("TP46-null-negative", "negative", court_world_spec("null"))])]


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
    rows = []
    for kind, tid, fn, controls in PLAN:
        target = ControlsLayer.target_of(kind, tid)
        for cid, pol, w in controls:
            co.commit("control_registered", F("register_control", control_id=cid, target=target, polarity=pol,
                      expected=EXPECTED, world_sha256=content_sha256(w), impl_sha256=impl_sha256(fn)))
            co.run_control(cid, fn, w, operator="op", key=ok, result_id=f"r-{cid}")
            co.attest_reexecution(f"r-{cid}", fn, w, auditor="aud", key=ak)
            r = co.results[f"r-{cid}"]
            rows.append({"control_id": cid, "tool": f"{kind}:{tid}", "polarity": pol, "world": w, "expected": EXPECTED,
                         "observed": r["observed"], "outcome": r["outcome"], "world_sha256": r["world_sha256"],
                         "impl_sha256": r["impl_sha256"], "evidence_sha256": r["evidence_sha256"]})
        text = f"{'TP-47' if kind == 'c0_gate' else 'TP-46'} controls: criteria FD-01-D32"
        co.commit("tool_row_registered", F("register_tool_row", tool_kind=kind, tool_id=tid,
                  controls=[c[0] for c in controls], criterion={"text": text, "sha256": content_sha256(text)},
                  cost_metric="compute seconds"))
    res = {"component": "WP9-02 part 2 — TP-47 (C0 gate), TP-46 (court)", "synthetic_only": True,
           "criteria_decision": "FD-01-D32", "results": rows,
           "module_sha256": {m: hashlib.sha256((ROOT / "src" / "xauusd_swarm" / m).read_bytes().replace(b"\r\n", b"\n"))
                             .hexdigest() for m in ("gate_court_controls.py", "inventory.py", "court.py",
                                                    "court_service.py")}}
    (out / "results.json").write_text(json.dumps(res, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
    return res


if __name__ == "__main__":
    for row in main(Path(sys.argv[1]))["results"]:
        print(row["control_id"], {k: v for k, v in row["observed"].items() if k != "output_sha256"}, row["outcome"])
