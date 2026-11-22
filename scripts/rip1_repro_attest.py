"""RIP-1 sandboxed protocol reproduction WITH a per-run attestation record (audit R1-03).
Uses only the frozen primitives of xauusd_swarm.rip1 (FD-01-D45; the module is not changed): sandbox_run,
read_output, validate_predictions, _prepare_code. Same procedure and criterion as rip1.reproduce_in_sandbox, but
every run's facts are written down instead of only "identical". Needs root (run host). SYNTHETIC ONLY.
Usage: python scripts/rip1_repro_attest.py OUT_JSON"""
import gzip
import hashlib
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from xauusd_swarm import rip1
from xauusd_swarm import rip1_attack as A

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "docs" / "results" / "rip1"


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def main(out_path: Path):
    if os.geteuid() != 0:
        raise SystemExit("needs root")
    recs = json.loads((RES / "submission_records.json").read_text())
    inputs = json.loads((RES / "run_inputs.json").read_text())
    pw = rip1.ensure_user()
    base = Path("/srv/rip1")                                   # same base as the original run (input.json paths)
    if base.exists():
        shutil.rmtree(base)
    cust = base / "custody"
    cust.mkdir(parents=True)
    os.chmod(base, 0o711)
    os.chmod(cust, 0o700)
    with gzip.open(RES / "ledger.jsonl.gz") as fh:
        (cust / "ledger_snapshot.jsonl").write_bytes(fh.read())
    code = rip1._prepare_code(base)
    code_sha = rip1._tree_sha(code / "xauusd_swarm") | {"rip1_attacker.py": rip1._sha_file(code / "rip1_attacker.py")}
    runs, done = [], []
    for view in ("V0", "V1"):
        for rep in A.REPS:
            rid = f"{view}_{rep}"
            orig_rec = recs[rid]["record"]
            files = {f"data_{rep}.npz": RES / f"data_{rep}.npz"}
            if view == "V1":
                files["ledger.jsonl"] = cust / "ledger_snapshot.jsonl"
            fx = rip1.sandbox_run(base=base, rid=rid, view=view, code=code, script=str(code / "rip1_attacker.py"),
                                  files=files, input_obj=inputs[rid], hide_extra=[str(cust)] + done, pw=pw)
            done.append(str(base / "runs" / rid))
            obj, out_sha = rip1.read_output(fx["out_dir"])
            z = np.load(RES / f"data_{rep}.npz")
            fams = {sc: [str(f) for f in z[f"F_{sc}"]] for sc in A.SCEN}
            schema_ok = True
            try:
                rip1.validate_predictions(obj, rep=rep, view=view, fams=fams, inputs_sha256=fx["inputs_sha256"])
            except RuntimeError as e:
                schema_ok = f"refused: {e}"
            orig = json.loads((RES / f"predictions_{rid}.json").read_text())
            checks = {
                "returncode_0": fx["returncode"] == 0,
                "no_leftover_process": fx["leftover_processes"] == [],
                "inputs_unchanged_during_run": fx["inputs_unchanged"],
                "inputs_sha256_equal_original": fx["inputs_sha256"] == orig_rec["inputs_sha256"],
                "code_sha256_equal_original": code_sha == orig_rec["code_sha256"],
                "python_equal_original": sys.version.split()[0] == orig_rec["python"],
                "numpy_equal_original": np.__version__ == orig_rec["numpy"],
                "probes_all_pass": obj.get("probes", {}).get("all_pass") is True,
                "schema_valid_complete_attacker_set": schema_ok is True,
                "predictions_identical_to_original": obj.get("predictions") == orig["predictions"],
            }
            preds_sha = sha(json.dumps(obj.get("predictions"), sort_keys=True, separators=(",", ":")).encode())
            orig_preds_sha = sha(json.dumps(orig["predictions"], sort_keys=True, separators=(",", ":")).encode())
            runs.append({"run": rid, "view": view, "representation": rep,
                         "inputs_sha256": fx["inputs_sha256"], "code_sha256": code_sha,
                         "probes_sha256": sha(json.dumps(obj.get("probes"), sort_keys=True).encode()),
                         "reproduced_output_file_sha256": out_sha,
                         "reproduced_predictions_sha256": preds_sha, "original_predictions_sha256": orig_preds_sha,
                         "original_predictions_file_sha256": orig_rec["predictions_sha256"],
                         "checks": checks, "schema": schema_ok,
                         "verdict": "identical" if all(v is True for v in checks.values()) else "DIFFERENT"})
    shutil.rmtree(base)
    att = {"experiment": "RIP-1 sandboxed protocol reproduction (audit R1-03)", "synthetic_only": True,
           "commit": subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=ROOT).stdout.strip(),
           "date_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "criterion": "all checks true per run (fixed in advance, FD-01-D45 §3.5c)", "runs": runs,
           "all_identical": all(r["verdict"] == "identical" for r in runs),
           "note": "criterion compares predictions and inputs exactly; whole-file equality is recorded per run "
                   "(reproduced_output_file_sha256 vs original_predictions_file_sha256), not required."}
    out_path.write_text(json.dumps(att, indent=1))
    print("all_identical", att["all_identical"])
    return 0 if att["all_identical"] else 1


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1])))
