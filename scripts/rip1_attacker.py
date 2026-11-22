"""RIP-1 attacker entry point (role reid_checker). Runs ONLY inside the isolation sandbox built by
xauusd_swarm.rip1 (§3.7): unprivileged user, own net/mount/pid namespaces, empty environment, `python -I`.
One run = one representation × one view (review R3-02).
Usage: python -I rip1_attacker.py CODE_DIR IN_DIR OUT_DIR VIEW
  CODE_DIR, IN_DIR: root-owned, read-only for the attacker (copied public code; input.json, data_<rep>.npz,
  ledger.jsonl in V1). OUT_DIR: the only writable directory. Output: OUT_DIR/predictions.json (unsigned: the
  attacker holds no key; the trusted orchestrator verifies hashes and signs the submission record, R3-03)."""
import json
import os
import sys

CODE, IN, OUT, VIEW = sys.argv[1:5]
sys.path.insert(0, CODE)                                # -I does not add the script dir; the copy is explicit

from xauusd_swarm import rip1_attack as A               # noqa: E402


def main():
    inp = json.load(open(os.path.join(IN, "input.json")))
    probes = A.probes(inp["secret_paths"], in_dir=IN, out_dir=OUT)      # before any attack
    out = {"view": VIEW, "rep": inp["rep"], "probes": probes}
    if probes["all_pass"]:
        out["predictions"], out["inputs_sha256"] = A.predict(IN, VIEW, inp)
    else:
        out["aborted"] = "isolation probes failed"
    with open(os.path.join(OUT, "predictions.json"), "w") as fh:
        json.dump(out, fh, sort_keys=True)


if __name__ == "__main__":
    main()
