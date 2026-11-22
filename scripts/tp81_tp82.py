"""Run TP-81 and TP-82 (measure-and-declare assumption experiments, FD-01-D33) and write the results.

Usage:  python scripts/tp81_tp82.py OUT_JSON      SYNTHETIC ONLY.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

from xauusd_swarm.assumption_tests import TP81, TP82, run_tp81, run_tp82

ROOT = Path(__file__).resolve().parents[1]


def main(out: Path) -> dict:
    res = {"component": "TP-81, TP-82 — assumption experiments (WP7-04 §11, §11.1)", "synthetic_only": True,
           "nature": "measure and declare; no pass threshold; synthetic result does not show the assumption holds in gold",
           "design_decision": "FD-01-D33, FD-01-D34", "spec": {"TP-81": TP81, "TP-82": TP82},
           "TP-81": run_tp81(), "TP-82": run_tp82(),
           "module_sha256": {m: hashlib.sha256((ROOT / "src" / "xauusd_swarm" / m).read_bytes().replace(b"\r\n", b"\n"))
                             .hexdigest() for m in ("assumption_tests.py", "nulls.py")}}
    out.write_text(json.dumps(res, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
    return res


if __name__ == "__main__":
    r = main(Path(sys.argv[1]))
    for row in r["TP-81"]["rows"]:
        print("TP-81", row["world"], row["b"], row["coverage"], row["within_tolerance"])
    for row in r["TP-82"]["rows"]:
        print("TP-82", row["arm"], row["world"], row.get("false_rejection_rate", row.get("rejection_rate_under_assumption_violation")),
              row["profile_distance_mean_v1"], row["change_distance_mean_v2"], row.get("reading", ""))
