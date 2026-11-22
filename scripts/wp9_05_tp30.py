"""WP9-05d: run TP-30 (re-identification accuracy per representation) once and write the result.
Usage: python scripts/wp9_05_tp30.py OUT_DIR. SYNTHETIC ONLY. Design FD-01-D44 (pre-registered).
No threshold (CS-01-04 open): measure and declare."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

from xauusd_swarm import reid

ROOT = Path(__file__).resolve().parents[1]


def main(out: Path) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    res = reid.run_tp30()
    src = ROOT / "src" / "xauusd_swarm"
    res["design"] = "FD-01-D44"
    res["spec"] = reid.TP30
    res["module_sha256"] = {m: hashlib.sha256((src / m).read_bytes()).hexdigest()
                            for m in ("reid.py", "representations.py")}
    (out / "results.json").write_text(json.dumps(res, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return res


if __name__ == "__main__":
    main(Path(sys.argv[1]))
