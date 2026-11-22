"""Path 1 v4 / v4.1 (founder OD-S9-05; designs FD-01-D41 for v4, FD-01-D42 for v4.1 — the current
version; v4 is superseded): TP-21/tool controls on five worlds, recorded in a ledger, plus the
generalisation worlds (measure and declare). Usage: python scripts/wp9_02_path1_v4.py OUT_DIR [v4|v4.1].
SYNTHETIC ONLY."""
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
from xauusd_swarm.ledger import AnchorStore, Ledger
from xauusd_swarm.path1 import P1V4, p1_world_spec_v4, run_p1_world_v4

ROOT = Path(__file__).resolve().parents[1]


def main(out: Path, version: str = "v4") -> dict:
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
    target = ControlsLayer.target_of("path", "P1-distributional")
    rows = []
    for kind in P1V4["worlds"]:
        pol = "positive" if kind == "real" else "negative"
        w = p1_world_spec_v4(kind, version=version)
        cid = f"TP21-P1-{version}-{kind}-{pol}"
        exp = P1V4["criteria"][kind]
        co.commit("control_registered", F("register_control", control_id=cid, target=target, polarity=pol,
                  expected=exp, world_sha256=content_sha256(w), impl_sha256=impl_sha256(run_p1_world_v4)))
        co.run_control(cid, run_p1_world_v4, w, operator="op", key=ok, result_id=f"r-{cid}")
        co.attest_reexecution(f"r-{cid}", run_p1_world_v4, w, auditor="aud", key=ak)
        r = co.results[f"r-{cid}"]
        rows.append({"control_id": cid, "polarity": pol, "world": w, "expected": exp, "observed": r["observed"],
                     "outcome": r["outcome"], "world_sha256": r["world_sha256"], "impl_sha256": r["impl_sha256"],
                     "evidence_sha256": r["evidence_sha256"]})
    text = f"TP-21/tool for path P1-distributional {version} (FD-01-D41/D42, OD-S9-05)"
    co.commit("tool_row_registered", F("register_tool_row", tool_kind="path", tool_id="P1-distributional",
              controls=[r["control_id"] for r in rows], criterion={"text": text, "sha256": content_sha256(text)},
              cost_metric="compute seconds"))
    gen = []
    for i, ov in enumerate(P1V4["generalisation"]):
        for kind in P1V4["worlds"]:
            w = p1_world_spec_v4(kind, overrides=ov, seed_offset=100 * (i + 1), version=version)
            gen.append({"world": w, "observed": run_p1_world_v4(w)})
    res = {"component": f"Path 1 {version} — TP-21/tool and generalisation", "synthetic_only": True,
           "decisions": "OD-S9-05, FD-01-D41" + (", FD-01-D42" if version == "v4.1" else ""), "version": version, "results": rows, "generalisation_measure_and_declare": gen,
           "module_sha256": {"path1.py": hashlib.sha256((ROOT / "src" / "xauusd_swarm" / "path1.py").read_bytes()
                                                        .replace(b"\r\n", b"\n")).hexdigest()}}
    (out / "results.json").write_text(json.dumps(res, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
    return res


if __name__ == "__main__":
    r = main(Path(sys.argv[1]), sys.argv[2] if len(sys.argv) > 2 else "v4")
    for row in r["results"]:
        print(row["control_id"], row["observed"], row["outcome"])
    for row in r["generalisation_measure_and_declare"]:
        print("GEN", row["world"]["kind"], row["world"]["overrides"], row["observed"])
