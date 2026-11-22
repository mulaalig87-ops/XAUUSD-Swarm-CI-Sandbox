"""WP9-02 (part 3): path 1 (P1-distributional) — register the path with its card, run its TP-21/tool
controls (real, spurious, null) and record each result; then the card's generalisation worlds
(measure and declare). Usage: python scripts/wp9_02_path1_controls.py OUT_DIR. SYNTHETIC ONLY.
Criteria: FD-01-D35 (pre-registered)."""
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
from xauusd_swarm.discovery import DiscoveryLayer
from xauusd_swarm.identity import public_hex, sign
from xauusd_swarm.inventory import content_sha256, impl_sha256
from xauusd_swarm.ledger import AnchorStore, Ledger
from xauusd_swarm.path1 import GENERALISATION, P1, p1_world_spec, run_p1_world

ROOT = Path(__file__).resolve().parents[1]


def _lf_sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def main(out: Path) -> dict:
    (out / "led").mkdir(parents=True, exist_ok=True)
    (out / "anc").mkdir(exist_ok=True)
    fk, ok, ak = (Ed25519PrivateKey.generate() for _ in range(3))
    F = lambda a, **kw: sign("founder", fk, {"action": a, "nonce": uuid.uuid4().hex, **kw})   # noqa: E731
    cl, co, dl = CustodyLayer(None), ControlsLayer(), DiscoveryLayer()
    g = Governance(fk.public_key(), Ledger(out / "led" / "ledger.jsonl", anchors=AnchorStore(out / "anc" / "a.jsonl")),
                   extensions=[cl, dl, co])
    for ident, k in (("op", ok), ("aud", ak)):
        g.register_key(F("register_key", identity=ident, public_key_hex=public_hex(k.public_key())))
    cl.commit("role_assigned", F("assign_role", role="court_operator", holder="op"))
    cl.commit("role_assigned", F("assign_role", role="custody_auditor", holder="aud"))
    card = (ROOT / "docs" / "paths" / "PATH1_CARD_runs_v1-v3.md").read_text(encoding="utf-8").replace("\r\n", "\n")
    gen = "generalisation worlds: " + json.dumps(GENERALISATION)
    dl.commit("path_registered", F("register_path", path_id="P1-distributional", kind="distributional_regularities",
              card={"text": card, "sha256": content_sha256(card)}, generalisation_test={"text": gen, "sha256": content_sha256(gen)},
              designers_without_sealed_access=True, lineage_sha256=_lf_sha(ROOT / "src" / "xauusd_swarm" / "path1.py")))
    target = ControlsLayer.target_of("path", "P1-distributional")
    rows, latest = [], {}
    for ver, null in (("v1", "rotation"), ("v2", "run_permutation"), ("v3", "rotation_per_cell")):   # v1, v2 failed (FL-011)
        ids = []
        for kind, pol in (("real", "positive"), ("spurious", "negative"), ("null", "negative")):
            w = p1_world_spec(kind, null=null)
            cid = f"TP21-P1-{ver}-{kind}-{pol}"
            exp = P1["criteria"][kind]
            co.commit("control_registered", F("register_control", control_id=cid, target=target, polarity=pol,
                      expected=exp, world_sha256=content_sha256(w), impl_sha256=impl_sha256(run_p1_world)))
            co.run_control(cid, run_p1_world, w, operator="op", key=ok, result_id=f"r-{cid}")
            co.attest_reexecution(f"r-{cid}", run_p1_world, w, auditor="aud", key=ak)
            r = co.results[f"r-{cid}"]
            rows.append({"control_id": cid, "version": ver, "polarity": pol, "world": w, "expected": exp,
                         "observed": r["observed"], "outcome": r["outcome"], "world_sha256": r["world_sha256"],
                         "impl_sha256": r["impl_sha256"], "evidence_sha256": r["evidence_sha256"]})
            ids.append(cid)
        latest = ids
    text = "TP-21/tool for path P1-distributional (v3, FD-01-D37): criteria FD-01-D35"
    co.commit("tool_row_registered", F("register_tool_row", tool_kind="path", tool_id="P1-distributional", controls=latest,
              criterion={"text": text, "sha256": content_sha256(text)}, cost_metric="compute seconds"))
    gen_rows = []
    for ver, null in (("v1", "rotation"), ("v2", "run_permutation"), ("v3", "rotation_per_cell")):
        for i, ov in enumerate(GENERALISATION):
            for kind in ("real", "spurious", "null"):
                w = p1_world_spec(kind, overrides=ov, seed_offset=100 * (i + 1), null=null)
                gen_rows.append({"version": ver, "world": w, "observed": run_p1_world(w)})
    res = {"component": "WP9-02 part 3 — path 1 (P1-distributional): TP-21/tool and generalisation",
           "synthetic_only": True, "criteria_decision": "FD-01-D35, FD-01-D36, FD-01-D37 (OD-S9-02)", "results": rows,
           "generalisation_measure_and_declare": gen_rows,
           "module_sha256": {"path1.py": _lf_sha(ROOT / "src" / "xauusd_swarm" / "path1.py"),
                             "PATH1_CARD_runs_v1-v3.md": _lf_sha(ROOT / "docs" / "paths" / "PATH1_CARD_runs_v1-v3.md")}}
    (out / "results.json").write_text(json.dumps(res, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
    return res


if __name__ == "__main__":
    r = main(Path(sys.argv[1]))
    for row in r["results"]:
        print(row["control_id"], row["observed"], row["outcome"])
    for row in r["generalisation_measure_and_declare"]:
        print("GEN", row["version"], row["world"]["kind"], row["world"].get("overrides"), row["observed"])
