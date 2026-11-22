"""RIP-2 — the single registered run (founder authorisation OD-S9-09; design v0.7 + addendum A1; code frozen at the
pre-run commit recorded in the output). SYNTHETIC ONLY. Calls xauusd_swarm.rip2.run() with NO spec override.
Usage: python scripts/rip2_run.py OUT_DIR"""
import hashlib
import json
import platform
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import numpy as np                                  # noqa: E402
from xauusd_swarm import rip2 as R                  # noqa: E402

CODE = ["src/xauusd_swarm/rip2.py", "src/xauusd_swarm/rip1_attack.py", "src/xauusd_swarm/reid.py",
        "src/xauusd_swarm/representations.py", "src/xauusd_swarm/numeric.py", "scripts/rip2_run.py",
        "docs/research/RIP2_DESIGN.md", "docs/research/RIP2_DESIGN_ADDENDUM_A1.md", "docs/research/RIP2_BUILD_NOTES.md"]


def sha(p):
    return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()


def main(out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    commit = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=ROOT).stdout.strip()
    dirty = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, cwd=ROOT).stdout
    if dirty.strip():
        raise SystemExit("working tree not clean: the run must use exactly the committed code")
    meta = {"experiment": "RIP-2", "authorisation": "OD-S9-09", "design": "RIP2_DESIGN.md v0.7 (FD-01-D46) + addendum A1 (OD-S9-08)",
            "commit": commit, "code_sha256": {p: sha(p) for p in CODE}, "python": sys.version, "numpy": np.__version__,
            "platform": platform.platform(), "spec_override": None, "seeds": R.SEEDS, "spec": dict(R.SPEC),
            "start_utc": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    (out / "run_meta_start.json").write_text(json.dumps(meta, indent=1, default=str))
    t0 = time.time()
    res = R.run()                                   # registered spec, no override
    meta["end_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    meta["seconds"] = round(time.time() - t0, 1)
    res["run_meta"] = meta
    blob = json.dumps(res, indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o))
    (out / "results.json").write_text(blob)
    (out / "results.sha256").write_text(hashlib.sha256(blob.encode()).hexdigest() + "  results.json\n")
    print("DONE", meta["seconds"], "s; cells", len(res["cells"]), "effects", len(res["effects"]),
          "ablation", len(res["ablation"]), "feature_groups", len(res["feature_groups"]), "utility", len(res["utility"]))


if __name__ == "__main__":
    main(sys.argv[1])
