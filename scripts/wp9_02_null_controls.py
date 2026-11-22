"""WP9-02 (part 1): run TP-21/tool for the runnable §11.2 null cards and record each result in a ledger.

Usage:  python scripts/wp9_02_null_controls.py OUT_DIR
Writes OUT_DIR/ledger.jsonl, OUT_DIR/anchors.jsonl and OUT_DIR/results.json. SYNTHETIC ONLY; the keys
are generated per run (engineering test, not an official signature).

Per control: the founder registers target, polarity, the pre-registered expectation (FD-01-D30), the
world hash and the code hash; the court operator runs it (the controls layer runs it twice and requires
identical output); an independent auditor re-executes it; the tool row is registered with both controls.
"""
from __future__ import annotations

import hashlib
import json
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from xauusd_swarm.charter import Governance
from xauusd_swarm.control_runs import CRITERIA, RUNNABLE, VERSION_OF, run_world, world_spec
from xauusd_swarm.controls import ControlsLayer
from xauusd_swarm.custody import CustodyLayer
from xauusd_swarm.identity import public_hex, sign
from xauusd_swarm.inventory import content_sha256, impl_sha256
from xauusd_swarm.ledger import AnchorStore, Ledger


def main(out: Path) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    (out / "led").mkdir(exist_ok=True)
    (out / "anc").mkdir(exist_ok=True)
    fk, ok, ak = (Ed25519PrivateKey.generate() for _ in range(3))

    def F(action, **kw):
        return sign("founder", fk, {"action": action, "nonce": uuid.uuid4().hex, **kw})

    cl, co = CustodyLayer(None), ControlsLayer()
    g = Governance(fk.public_key(), Ledger(out / "led" / "ledger.jsonl", anchors=AnchorStore(out / "anc" / "a.jsonl")),
                   extensions=[cl, co])
    for ident, k in (("op", ok), ("aud", ak)):
        g.register_key(F("register_key", identity=ident, public_key_hex=public_hex(k.public_key())))
    cl.commit("role_assigned", F("assign_role", role="court_operator", holder="op"))
    cl.commit("role_assigned", F("assign_role", role="custody_auditor", holder="aud"))

    rows, latest = [], {}
    for card in RUNNABLE:                          # every version runs; a failed version stays recorded
        tool = VERSION_OF.get(card, card)
        ids = []
        for kind, pol in (("real", "positive"), ("null", "negative")):
            w = world_spec(card, kind)
            cid = f"TP21-{card.replace('/', '-')}-{pol}"
            co.commit("control_registered", F("register_control", control_id=cid,
                      target={"kind": "null_model", "id": tool}, polarity=pol, expected=CRITERIA[kind],
                      world_sha256=content_sha256(w), impl_sha256=impl_sha256(run_world)))
            co.run_control(cid, run_world, w, operator="op", key=ok, result_id=f"r-{cid}")
            co.attest_reexecution(f"r-{cid}", run_world, w, auditor="aud", key=ak)
            r = co.results[f"r-{cid}"]
            rows.append({"control_id": cid, "card": tool, "version": card, "polarity": pol, "world": w,
                         "expected": CRITERIA[kind], "observed": r["observed"], "outcome": r["outcome"],
                         "world_sha256": r["world_sha256"], "impl_sha256": r["impl_sha256"],
                         "evidence_sha256": r["evidence_sha256"]})
            ids.append(cid)
        latest[tool] = (card, ids)                  # the matrix row uses the latest version's controls
    for tool, (card, ids) in latest.items():
        from xauusd_swarm.nulls import CARDS
        if CARDS.get(tool, {}).get("use_restriction"):        # mandatory by the card (R2-01): before the row
            co.commit("use_restriction_registered", F("register_use_restriction", tool_kind="null_model", tool_id=tool,
                      restriction=CARDS[tool]["use_restriction"],
                      text=f"{tool}: assumes stationarity — within stable windows or after a transform (س 829); TP-82"))
        text = f"TP-21/tool for null card {tool} ({card}): criteria FD-01-D30/D31"
        co.commit("tool_row_registered", F("register_tool_row", tool_kind="null_model", tool_id=tool, controls=ids,
                  criterion={"text": text, "sha256": content_sha256(text)}, cost_metric="compute seconds"))
    res = {"component": "WP9-02 part 1 — TP-21/tool, §11.2 null cards", "synthetic_only": True,
           "criteria_decision": "FD-01-D30, FD-01-D31", "results": rows,
           # impl_sha256 binds run_world's own source only; the helper modules are bound by file hash (LF-normalised, so Windows CRLF checkouts match):
           "module_sha256": {m: hashlib.sha256((ROOT / "src" / "xauusd_swarm" / m).read_bytes().replace(b"\r\n", b"\n")).hexdigest()
                             for m in ("control_runs.py", "nulls.py")},
           "not_run": {"time_reversal": "test procedure «غير معرّف في المعمارية»",
                       "zero_cond_mean": "model family «غير معرّف في المعمارية»",
                       "block_bootstrap": "not a null; control is TP-81 (separate)",
                       "iaaft_TP-82_arm_b": "separate experiment"}}
    (out / "results.json").write_text(json.dumps(res, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
    return res


if __name__ == "__main__":
    r = main(Path(sys.argv[1]))
    for row in r["results"]:
        print(row["control_id"], row["observed"], row["outcome"])
