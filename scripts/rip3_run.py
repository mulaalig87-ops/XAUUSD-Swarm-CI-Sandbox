"""RIP-3 — the registered run driver (design v0.4, FD-01-D47). SYNTHETIC ONLY.
NOT AUTHORISED at BUILD (OD-S9-11 is BUILD only). It refuses to score the registered sets unless the founder's RUN
authorisation identifier is given with --authorisation; rip3.run_jobs refuses them as well (authorised_run guard).

Usage:
  python scripts/rip3_run.py OUT_DIR SET --authorisation OD-... [--cands C1,C2,...] [--worlds W1,W2]
  python scripts/rip3_run.py OUT_DIR SET --assemble [--rip2 docs/results/rip2/results.json]
SET is 'eval' or 'confirm' (registered) or 'smoke' (BUILD-stage small checks; no authorisation needed).
Jobs are resumable (one file per set × candidate × world); every draw is keyed, so order and splitting across
processes do not change any result."""
import argparse
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
from xauusd_swarm import rip3 as R                  # noqa: E402

CODE = ["src/xauusd_swarm/rip3.py", "src/xauusd_swarm/rip2.py", "src/xauusd_swarm/rip1_attack.py",
        "src/xauusd_swarm/reid.py", "src/xauusd_swarm/representations.py", "src/xauusd_swarm/numeric.py",
        "scripts/rip3_run.py", "docs/research/RIP3_DESIGN.md", "docs/research/RIP3_BUILD_NOTES.md"]


def sha(p):
    return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()


def meta(set_name, authorisation):
    commit = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=ROOT).stdout.strip()
    dirty = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, cwd=ROOT).stdout
    return {"experiment": "RIP-3", "set": set_name, "authorisation": authorisation, "commit": commit,
            "tree_clean": not dirty.strip(), "code_sha256": {p: sha(p) for p in CODE}, "python": sys.version,
            "numpy": np.__version__, "platform": platform.platform(), "seeds": R.SEEDS, "spec": dict(R.SPEC),
            "implementation_choices": R.IMPLEMENTATION_CHOICES, "utc": datetime.now(timezone.utc).isoformat(timespec="seconds")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("set", choices=["eval", "confirm", "smoke"])
    ap.add_argument("--authorisation", default=None)
    ap.add_argument("--cands", default=",".join(R.ALL_CELLS))
    ap.add_argument("--worlds", default="W1,W2")
    ap.add_argument("--assemble", action="store_true")
    ap.add_argument("--rip2", default=str(ROOT / "docs/results/rip2/results.json"))
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    registered = a.set in R.REGISTERED_SETS
    if registered and not a.authorisation:
        raise SystemExit("the registered sets need the founder's RUN authorisation identifier (--authorisation)")
    m = meta(a.set, a.authorisation)
    if registered and not m["tree_clean"]:
        raise SystemExit("working tree not clean: the run must use exactly the committed code")
    if a.assemble:
        jobs = R.load_jobs(out, a.set)
        r2 = json.loads(Path(a.rip2).read_text()) if a.rip2 and Path(a.rip2).exists() else None
        res = R.evaluate(jobs, a.set, r2)
        res["meta"] = m
        res["jobs_sha256"] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                              for p in sorted(out.glob(f"{a.set}__*.json"))}
        blob = json.dumps(res, indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o))
        (out / f"{a.set}_results.json").write_text(blob)
        (out / f"{a.set}_results.sha256").write_text(hashlib.sha256(blob.encode()).hexdigest() + f"  {a.set}_results.json\n")
        print("assembled", len(jobs), "jobs")
        return
    (out / f"{a.set}_meta_{int(time.time())}.json").write_text(json.dumps(m, indent=1, default=str))
    t0 = time.time()
    done = R.run_jobs(out, a.set, a.cands.split(","), tuple(a.worlds.split(",")), authorised_run=registered)
    print("jobs written", done, round(time.time() - t0, 1), "s")


if __name__ == "__main__":
    main()
