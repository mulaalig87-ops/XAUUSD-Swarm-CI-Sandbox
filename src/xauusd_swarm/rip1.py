"""RIP-1 custody side: Vault-drawn blinding, real ledger, isolated attacker, seal, scoring. SYNTHETIC ONLY.
Design: docs/research/REID_PROGRAMME.md §3 (frozen by FD-01-D45 before the run). Requires root on Linux.

Isolation order (review R2-02), fixed in `sandbox_argv`:
 1. custody (root) creates the namespaces: `unshare --net --mount --pid --fork --mount-proc`;
 2. still root inside them, `sh` hides custody paths with empty tmpfs mounts (mode 000);
 3. `setpriv` drops to the attacker uid/gid, clears groups, sets no_new_privs, empties inheritable and bounding
    capabilities;
 4. `env -i PATH=…` then `python -I` runs the attacker script. subprocess closes inherited descriptors (close_fds).
The attacker verifies the result from inside (probes) before attacking.
Since review R4 (process hardening): the run's input and code directories are additionally bind-mounted
READ-ONLY inside the namespace (not only file permissions); every process of the attacker is gone before the
orchestrator reads the output (PID namespace end + a /proc check); the output is untrusted data (one regular
file, no links, size limit, opened with O_NOFOLLOW, strict schema).
"""
from __future__ import annotations

import gzip
import hashlib
import json
import os
import secrets
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

import numpy as np
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from . import reid
from . import rip1_attack as A
from .charter import Governance
from .custody import CustodyLayer, Vault, request
from .identity import public_hex, sign
from .ledger import AnchorStore, Ledger

ROOT = Path(__file__).resolve().parents[2]
PKG_FILES = ("reid.py", "representations.py", "numeric.py", "rip1_attack.py")
ATTACKER_USER = "rip_attacker"
HIDE = ["/home", "/root", "/tmp", "/mnt", "/var/tmp", "/run/lock", "/dev/shm", "/dev/mqueue",
        "/var/lib/php/sessions"]        # empty tmpfs (mode 000) in the attacker namespace: secrets and shared writable dirs


def sandbox_argv(*, uid: int, gid: int, hide: list[str], script: str, args: list[str], ro: list[str] = ()) -> list[str]:
    # set -e: a failed mount stops the run; a path that does not exist on this host has nothing to hide
    mounts = "; ".join(f"if [ -e {p} ]; then mount -t tmpfs -o size=1m,mode=000 none {p}; fi" for p in hide)
    rob = "".join(f"; mount --bind {p} {p}; mount -o remount,bind,ro {p}" for p in ro)    # read-only bind mounts
    inner = (f"set -e; {mounts}{rob}; exec setpriv --reuid={uid} --regid={gid} --clear-groups --no-new-privs "
             f"--inh-caps=-all --bounding-set=-all -- env -i PATH=/usr/bin:/bin {sys.executable} -I {script} "
             + " ".join(args))
    return ["unshare", "--net", "--mount", "--pid", "--fork", "--mount-proc", "--", "sh", "-c", inner]


MAX_OUTPUT_BYTES = 64 * 1024 * 1024


def _leftover_processes(uid: int) -> list[int]:
    """PIDs (host view) still running as the attacker uid."""
    out = []
    for d in os.listdir("/proc"):
        if d.isdigit():
            try:
                for line in open(f"/proc/{d}/status"):
                    if line.startswith("Uid:") and str(uid) in line.split()[1:]:
                        out.append(int(d))
            except OSError:
                pass
    return out


def sandbox_run(*, base: Path, rid: str, view: str, code: Path, script: str, files: dict, input_obj: dict,
                hide_extra: list[str], pw, args_extra: list[str] = ()) -> dict:
    """One isolated attacker run. files: {name: source path} copied into a fresh input dir. Returns the run facts;
    the output is NOT read here (see read_output)."""
    rdir = base / "runs" / rid
    ind, outd = rdir / "in", rdir / "out"
    ind.mkdir(parents=True)
    outd.mkdir()
    for name, src in files.items():
        shutil.copy(src, ind / name)
    (ind / "input.json").write_text(json.dumps(input_obj, sort_keys=True))
    _readonly_tree(ind)
    os.chmod(rdir, 0o755)
    os.chown(outd, pw.pw_uid, pw.pw_gid)
    os.chmod(outd, 0o700)
    in_before = _tree_sha(ind)
    argv = sandbox_argv(uid=pw.pw_uid, gid=pw.pw_gid, hide=HIDE + hide_extra, script=script,
                        args=[str(code), str(ind), str(outd), view, *args_extra], ro=[str(code), str(ind)])
    r = subprocess.run(argv, capture_output=True, text=True, stdin=subprocess.DEVNULL, close_fds=True)
    left = _leftover_processes(pw.pw_uid)              # the PID namespace ends with its init; verify it did
    os.chown(outd, 0, 0)                                # attacker loses the output dir before it is read
    os.chmod(outd, 0o700)
    os.chmod(rdir, 0o700)                               # closed; later runs also hide it by tmpfs
    in_after = _tree_sha(ind)
    return {"rid": rid, "view": view, "argv": argv, "returncode": r.returncode, "stdout_tail": r.stdout[-2000:],
            "stderr_tail": r.stderr[-4000:], "leftover_processes": left, "inputs_sha256": in_before,
            "inputs_unchanged": in_after == in_before, "in_dir": str(ind), "out_dir": str(outd)}


def read_output(out_dir: str, max_bytes: int = MAX_OUTPUT_BYTES) -> tuple[dict, str]:
    """Untrusted output: the directory must hold exactly one regular file predictions.json (no symlink, no hard
    link, no other entry), within the size limit; opened with O_NOFOLLOW. Returns (object, sha256)."""
    import stat
    names = os.listdir(out_dir)
    if names != ["predictions.json"]:
        raise RuntimeError(f"output dir must hold only predictions.json, found {sorted(names)}")
    p = os.path.join(out_dir, "predictions.json")
    st = os.lstat(p)
    if not stat.S_ISREG(st.st_mode) or st.st_nlink != 1:
        raise RuntimeError("predictions.json is not a plain regular file (link or special file)")
    if st.st_size > max_bytes:
        raise RuntimeError(f"predictions.json too large ({st.st_size} bytes)")
    fd = os.open(p, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    with os.fdopen(fd, "rb") as fh:
        raw = fh.read(max_bytes + 1)
    if len(raw) > max_bytes:
        raise RuntimeError("predictions.json grew past the limit while reading")
    return json.loads(raw), hashlib.sha256(raw).hexdigest()


def validate_predictions(obj: dict, *, rep: str, view: str, fams: dict, inputs_sha256: dict) -> None:
    """Strict schema of the attacker's output (reviews R4, R5): no extra keys (e.g. no self-made signature); the
    scenarios exactly A.SCEN; per scenario the attacker names EXACTLY the frozen set A.expected_attackers (none
    missing, none added; A5-f names derived from the frozen ledger field list)."""
    if set(obj) != {"view", "rep", "probes", "predictions", "inputs_sha256"}:
        raise RuntimeError(f"unexpected output keys {sorted(obj)}")
    if obj["view"] != view or obj["rep"] != rep:
        raise RuntimeError("output names another run")
    if obj["probes"].get("all_pass") is not True:
        raise RuntimeError("isolation probes did not all pass")
    if obj["inputs_sha256"] != {k: v for k, v in inputs_sha256.items() if k != "input.json"}:
        raise RuntimeError("attacker hashed different inputs")
    pr = obj["predictions"]
    if set(pr) != set(A.SCEN):
        raise RuntimeError("scenarios differ")
    if set(fams) != set(A.SCEN):
        raise RuntimeError("expected families must be given for every scenario")
    for sc, atts in pr.items():
        want = A.expected_attackers(view, sc, rep)
        if set(atts) != want:
            raise RuntimeError(f"{view}/{sc}/{rep}: attackers missing {sorted(want - set(atts))}, "
                               f"unexpected {sorted(set(atts) - want)}")
        for att, pred in atts.items():
            if set(pred) != set(fams[sc]):
                raise RuntimeError(f"{att}/{sc}: families differ from the run's test families")
            for lab in pred.values():
                if not (isinstance(lab, list) and len(lab) == 2 and all(type(v) is int for v in lab)
                        and 0 <= lab[0] < reid.K and 0 <= lab[1] < reid.P):
                    raise RuntimeError(f"{att}/{sc}: malformed label {lab!r}")


def scan_ledger(led_bytes: bytes, secret_values: dict, public_values: list) -> dict:
    """§3.2 input-sanity check (not evidence of no leak, review R1-08). secret_values: {kind: [values]} for every
    vault secret (c, a, b, m, salt, seed, key). A float is searched as repr and float.hex, a string (salt, key hex)
    and an int (seed) as their text. A value whose text equals a public value already in the ledger (Δ) cannot be
    told apart from it and is reported as excluded, with its kind (review R3-04). Also: no statement may carry a
    secret field name."""
    stmt_keys = set()
    for line in led_bytes.decode().splitlines():
        rec = json.loads(line)
        if "statement_hex" in rec["payload"]:
            stmt_keys |= set(json.loads(bytes.fromhex(rec["payload"]["statement_hex"])))
    public_txt = {repr(v) for v in public_values} | {float(v).hex() for v in public_values}

    def texts(v):
        if isinstance(v, float):
            return [repr(v), v.hex()]
        return [str(v)]
    hits, excluded, checked = {}, {}, {}
    for kind, vals in secret_values.items():
        checked[kind] = len(vals)
        for v in vals:
            ts = texts(v)
            if any(t in public_txt for t in ts):
                excluded[kind] = excluded.get(kind, 0) + 1
                continue
            if any(t.encode() in led_bytes for t in ts):
                hits[kind] = hits.get(kind, 0) + 1
    forbidden = {"c", "a", "b", "m", "salt", "seeds", "asset", "period", "key"} & stmt_keys
    return {"checked": checked, "hits": hits, "excluded_equal_to_public": excluded,
            "forbidden_statement_keys": sorted(forbidden), "pass": not hits and not forbidden}


def _readonly_tree(d: Path):
    """root-owned, readable, not writable by the attacker."""
    for root, dirs, files in os.walk(d):
        os.chown(root, 0, 0)
        os.chmod(root, 0o755)
        for f in files:
            os.chown(os.path.join(root, f), 0, 0)
            os.chmod(os.path.join(root, f), 0o644)


def _tree_sha(d: Path) -> dict:
    return {p.name: _sha_file(p) for p in sorted(Path(d).iterdir()) if p.is_file()}


def ensure_user():
    import pwd                                          # POSIX only; imported here so Windows can import the module
    try:
        return pwd.getpwnam(ATTACKER_USER)
    except KeyError:
        subprocess.run(["useradd", "--system", "--no-create-home", "--shell", "/usr/sbin/nologin", ATTACKER_USER], check=True)
        return pwd.getpwnam(ATTACKER_USER)


def _sha_file(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def run(out: Path, base: Path = Path("/srv/rip1"), spec: dict | None = None) -> dict:
    if os.geteuid() != 0:
        raise SystemExit("RIP-1 needs root (isolation boundary, §3.7)")
    spec = {**A.SPEC, **(spec or {})}
    A.SPEC.update(spec)
    sysrnd = secrets.SystemRandom()
    pw = ensure_user()
    if base.exists():
        shutil.rmtree(base)
    cust = base / "custody"
    for d in (cust / "led", cust / "anc"):
        d.mkdir(parents=True)
    os.chmod(base, 0o711)
    os.chmod(cust, 0o700)

    # ---- identities, vault (key only in memory), ledger ----
    key = os.urandom(32)
    vault = Vault(cust / "vault.bin", key)
    FK, CK, OK, QK = (Ed25519PrivateKey.generate() for _ in range(4))
    F = lambda a, **kw: sign("founder", FK, {"action": a, "nonce": uuid.uuid4().hex, **kw})   # noqa: E731
    cl = CustodyLayer(vault, identity="cust", key=CK)
    g = Governance(FK.public_key(), Ledger(cust / "led" / "ledger.jsonl", anchors=AnchorStore(cust / "anc" / "a.jsonl")),
                   extensions=[cl])
    for ident, k in (("cust", CK), ("op", OK), ("chk", QK)):
        g.register_key(F("register_key", identity=ident, public_key_hex=public_hex(k.public_key())))
    for role, h in (("custody", "cust"), ("court_operator", "op"), ("reid_checker", "chk")):
        cl.commit("role_assigned", F("assign_role", role=role, holder=h))

    # ---- families: test (series + truth) and dev (ledger only, labels public), in CSPRNG order ----
    tasks = [(rep, sc, part, c) for rep in A.REPS for sc in A.SCEN for part in ("test", "dev")
             for c in A.CLASSES for _ in range(spec["families_per_class"][sc])]
    sysrnd.shuffle(tasks)
    test = {rep: {sc: [] for sc in A.SCEN} for rep in A.REPS}
    dev_labels = {rep: {sc: {} for sc in A.SCEN} for rep in A.REPS}
    secret_values = {"c": [], "a": [], "b": [], "m": [], "salt": [], "seed": [], "key": [key.hex()]}   # ledger scan
    for rep, sc, part, (a, p) in tasks:
        fam = str(uuid.uuid4())
        prm = A.draw(a, sysrnd)
        com = vault.set_params(fam, **prm)             # refusal raises → run aborts (no re-draw)
        cl.commit("params_fixed", sign("cust", CK, {"action": "params_fixed", "nonce": uuid.uuid4().hex, "family": fam,
                                                     "params_commitment": com, "delta": reid.ASSETS[a]["tick"]}))
        for k_ in ("c", "a", "b", "m"):
            secret_values[k_].append(prm[k_])
        secret_values["salt"].append(vault._d["params"][fam][com]["salt"])
        if part == "dev":
            dev_labels[rep][sc][fam] = [a, p]
            continue
        seeds = [sysrnd.getrandbits(64) for _ in range(A.SCEN[sc])]
        import random
        series = [A.blind(rep, reid.simulate(a, p, spec["n"], random.Random(s)), a, prm) for s in seeds]
        vault.store_truth(fam, {"asset": a, "period": p, "seeds": [str(s) for s in seeds]})
        secret_values["seed"] += seeds
        test[rep][sc].append((fam, series))

    # ---- public code copy (root-owned, read-only for the attacker) ----
    code = _prepare_code(base)
    data_dir = cust / "data"
    data_dir.mkdir()
    for rep in A.REPS:
        arrs = {}
        for sc in A.SCEN:
            sysrnd.shuffle(test[rep][sc])
            arrs[f"F_{sc}"] = np.array([f for f, _ in test[rep][sc]])
            arrs[f"X_{sc}"] = np.array([s for _, s in test[rep][sc]], dtype=np.float64)
        np.savez_compressed(data_dir / f"data_{rep}.npz", **arrs)
    shutil.copy(cust / "led" / "ledger.jsonl", cust / "ledger_snapshot.jsonl")   # V1 view: all families fixed, nothing sealed
    snap_rows = A.ledger_fields([json.loads(l) for l in (cust / "ledger_snapshot.jsonl").read_text().splitlines()])
    if any(set(r) != set(A.LEDGER_FIELDS) for r in snap_rows.values()):
        raise RuntimeError("ledger snapshot does not expose exactly the frozen field list (R5)")

    # ---- one sandbox per representation × view; separate read-only input and writable output (R3-01, R3-02, R4) ----
    runs, records, logs, pred_files, inputs_json = {}, {}, {}, {}, {}
    code_sha = _tree_sha(code / "xauusd_swarm") | {"rip1_attacker.py": _sha_file(code / "rip1_attacker.py")}
    for view in ("V0", "V1"):
        for rep in A.REPS:
            rid = f"{view}_{rep}"
            done = [str(base / "runs" / r) for r in runs]
            files = {f"data_{rep}.npz": data_dir / f"data_{rep}.npz"}
            if view == "V1":
                files["ledger.jsonl"] = cust / "ledger_snapshot.jsonl"
            secret_paths = [str(cust), str(cust / "vault.bin"), str(cust / "led"), "/home", "/root", "/tmp", "/mnt",
                            "/var/tmp"] + done
            inp = {"spec": spec, "rep": rep, "dev_labels": dev_labels[rep], "secret_paths": secret_paths}
            fx = sandbox_run(base=base, rid=rid, view=view, code=code, script=str(code / "rip1_attacker.py"),
                             files=files, input_obj=inp, hide_extra=[str(cust)] + done, pw=pw)
            logs[rid] = fx
            if fx["returncode"] != 0 or fx["leftover_processes"] or not fx["inputs_unchanged"]:
                raise RuntimeError(f"attacker {rid} failed: {fx}")
            out_, out_sha = read_output(fx["out_dir"])
            if "aborted" in out_:
                raise RuntimeError(f"isolation probes failed in {rid}: {out_.get('probes')}")
            validate_predictions(out_, rep=rep, view=view, fams={sc: [f for f, _ in test[rep][sc]] for sc in A.SCEN},
                                 inputs_sha256=fx["inputs_sha256"])
            runs[rid] = out_
            inputs_json[rid] = inp
            # trusted orchestrator, outside the sandbox and after it ended, attests the run for the reid_checker
            # role (R3-03, R4): a record of what it verified; NOT a proof of the attacker's execution integrity
            rec = {"run": rid, "view": view, "representation": rep, "inputs_sha256": fx["inputs_sha256"],
                   "predictions_sha256": out_sha, "returncode": fx["returncode"], "leftover_processes": 0,
                   "inputs_unchanged": True, "probes_all_pass": True,
                   "probes_sha256": hashlib.sha256(json.dumps(out_["probes"], sort_keys=True).encode()).hexdigest(),
                   "code_sha256": code_sha, "python": sys.version.split()[0], "numpy": np.__version__}
            blob = json.dumps(rec, sort_keys=True, separators=(",", ":")).encode()
            records[rid] = {"record": rec, "signer": "chk", "signature_hex": QK.sign(blob).hex()}
            pred_files[rid] = Path(fx["out_dir"]) / "predictions.json"

    # ---- seal (court operator), then truth through the logged after-seal path ----
    sub_blob = json.dumps(records, sort_keys=True, separators=(",", ":")).encode()
    sub_sha = hashlib.sha256(sub_blob).hexdigest()
    labels, truths = {}, {}
    for rep in A.REPS:
        for sc in A.SCEN:
            for fam, _ in test[rep][sc]:
                cl.commit("submissions_sealed", sign("op", OK, {"action": "seal_submissions", "nonce": uuid.uuid4().hex,
                                                                "family": fam, "submissions_sha256": sub_sha}))
                t = cl.access(request("op", OK, f"truth:{fam}", "RIP-1 scoring after seal", fam))
                labels[fam] = (t["asset"], t["period"])
                truths[fam] = t

    # ---- ledger scan (custody side): no continuous secret, seed or secret field name in the ledger ----
    led_bytes = (cust / "led" / "ledger.jsonl").read_bytes()
    ledger_scan = scan_ledger(led_bytes, secret_values, [a_["tick"] for a_ in reid.ASSETS])

    # ---- scoring ----
    rows = []
    for view in ("V0", "V1"):
        for rep in A.REPS:
            for sc in A.SCEN:
                for att_name, pr in runs[f"{view}_{rep}"]["predictions"][sc].items():
                    fams = list(pr)
                    y = [labels[f] for f in fams]
                    pp = [tuple(pr[f]) for f in fams]
                    n = len(fams)
                    row = {"view": view, "representation": rep, "scenario": sc, "attacker": att_name, "units": n}
                    for nm, idx, k in (("asset", 0, reid.K), ("period", 1, reid.P)):
                        c = sum(a[idx] == b[idx] for a, b in zip(pp, y))
                        row[nm] = {"correct": c, "accuracy": round(c / n, 4), "chance": round(1 / k, 4),
                                   "wilson95": reid.wilson(c, n),
                                   "confusion": [[sum(1 for a, b in zip(pp, y) if b[idx] == i and a[idx] == j)
                                                  for j in range(k)] for i in range(k)]}
                    c = sum(a == b for a, b in zip(pp, y))
                    row["joint"] = {"correct": c, "accuracy": round(c / n, 4), "chance": round(1 / (reid.K * reid.P), 4),
                                    "wilson95": reid.wilson(c, n)}
                    rows.append(row)

    vault_sha = vault.ciphertext_sha256()
    del key, vault                                       # key discarded: vault permanently sealed (accepted risk D-2)
    out.mkdir(parents=True, exist_ok=True)
    for rep in A.REPS:
        shutil.copy(data_dir / f"data_{rep}.npz", out / f"data_{rep}.npz")
    with gzip.GzipFile(out / "ledger.jsonl.gz", "wb", mtime=0) as fh:          # the V1 snapshot the attacker saw
        fh.write((cust / "ledger_snapshot.jsonl").read_bytes())
    with gzip.GzipFile(out / "ledger_final.jsonl.gz", "wb", mtime=0) as fh:    # after seal and scoring
        fh.write(led_bytes)
    for rid, pp in pred_files.items():
        shutil.copy(pp, out / f"predictions_{rid}.json")
    (out / "submission_records.json").write_text(sub_blob.decode())
    (out / "run_inputs.json").write_text(json.dumps(inputs_json, sort_keys=True))     # each run's input.json content
    (out / "dev_labels.json").write_text(json.dumps(dev_labels, sort_keys=True))
    (out / "revealed_truth.json").write_text(json.dumps(truths, sort_keys=True))   # after seal and scoring
    freeze = subprocess.run([sys.executable, "-m", "pip", "freeze"], capture_output=True, text=True).stdout
    res = {"experiment": "RIP-1", "design": "FD-01-D45", "synthetic_only": True, "threshold": None, "spec": spec,
           "rows": rows, "aliases": {"activity_time": {"same_result_as": "log_returns", "counted_as_independent": False,
                                                       "reason": "one update per step in this world: byte-identical data; one run"}},
           "attacker_scope": "one representation per run; no multi-representation attacker (not measured)",
           "ledger_scan": ledger_scan, "reid_checker_public_key": public_hex(QK.public_key()),
           "probes": {rid: r_["probes"] for rid, r_ in runs.items()}, "attacker_runs": {k: {x: v[x] for x in ("argv", "returncode", "stderr_tail", "leftover_processes",
                                                                  "inputs_unchanged")} for k, v in logs.items()},
           "vault_ciphertext_sha256": vault_sha, "submissions_sha256": sub_sha,
           "files_sha256": {p.name: _sha_file(p) for p in sorted(out.iterdir()) if p.name != "results.json"},
           "environment": {"python": sys.version, "lock_sha256": _sha_file(ROOT / "env" / "test.lock.txt"),
                           "pip_freeze_sha256": hashlib.sha256(freeze.encode()).hexdigest(), "pip_freeze": freeze,
                           "code_sha256": {f: _sha_file(ROOT / "src" / "xauusd_swarm" / f) for f in PKG_FILES + ("rip1.py",)}
                           | {"rip1_attacker.py": _sha_file(ROOT / "scripts" / "rip1_attacker.py")}}}
    (out / "results.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))
    return res


def _prepare_code(base: Path) -> Path:
    code = base / "code"
    (code / "xauusd_swarm").mkdir(parents=True)
    for f in PKG_FILES:
        shutil.copy(ROOT / "src" / "xauusd_swarm" / f, code / "xauusd_swarm" / f)
    (code / "xauusd_swarm" / "__init__.py").write_text("")
    shutil.copy(ROOT / "scripts" / "rip1_attacker.py", code / "rip1_attacker.py")
    _readonly_tree(code)
    return code


def reproduce_in_sandbox(res: Path, base: Path = Path("/srv/rip1")) -> dict:
    """Protocol reproduction (review R4): rebuild the ten isolated runs from the committed data, in the original
    order and with the same hiding, re-run the attacker in a fresh sandbox per run, and compare with the original.
    Criterion fixed in advance: identical input hashes, identical code hashes, identical Python and numpy
    versions, all probes pass, no leftover process, inputs unchanged, and EXACTLY identical predictions.
    Any difference raises. Needs root (same host class as the run)."""
    if os.geteuid() != 0:
        raise SystemExit("sandboxed reproduction needs root")
    recs = json.loads((res / "submission_records.json").read_text())
    inputs = json.loads((res / "run_inputs.json").read_text())
    pw = ensure_user()
    if base.exists():
        shutil.rmtree(base)
    cust = base / "custody"
    cust.mkdir(parents=True)
    os.chmod(base, 0o711)
    os.chmod(cust, 0o700)
    with gzip.open(res / "ledger.jsonl.gz") as fh:
        (cust / "ledger_snapshot.jsonl").write_bytes(fh.read())
    code = _prepare_code(base)
    code_sha = _tree_sha(code / "xauusd_swarm") | {"rip1_attacker.py": _sha_file(code / "rip1_attacker.py")}
    report, done = {}, []
    for view in ("V0", "V1"):
        for rep in A.REPS:
            rid = f"{view}_{rep}"
            rec = recs[rid]["record"]
            for k, want in (("code_sha256", code_sha), ("python", sys.version.split()[0]), ("numpy", np.__version__)):
                if rec[k] != want:
                    raise RuntimeError(f"{rid}: {k} differs from the original run ({rec[k]!r} vs {want!r})")
            files = {f"data_{rep}.npz": res / f"data_{rep}.npz"}
            if view == "V1":
                files["ledger.jsonl"] = cust / "ledger_snapshot.jsonl"
            fx = sandbox_run(base=base, rid=rid, view=view, code=code, script=str(code / "rip1_attacker.py"),
                             files=files, input_obj=inputs[rid], hide_extra=[str(cust)] + done, pw=pw)
            done.append(str(base / "runs" / rid))
            if fx["returncode"] != 0 or fx["leftover_processes"] or not fx["inputs_unchanged"]:
                raise RuntimeError(f"{rid}: sandbox run failed: {fx}")
            if fx["inputs_sha256"] != rec["inputs_sha256"]:
                raise RuntimeError(f"{rid}: input hashes differ from the original run")
            obj, _ = read_output(fx["out_dir"])
            z = np.load(res / f"data_{rep}.npz")
            fams = {sc: [str(f) for f in z[f"F_{sc}"]] for sc in A.SCEN}
            validate_predictions(obj, rep=rep, view=view, fams=fams, inputs_sha256=fx["inputs_sha256"])   # R5
            orig = json.loads((res / f"predictions_{rid}.json").read_text())
            validate_predictions(orig, rep=rep, view=view, fams=fams, inputs_sha256=rec["inputs_sha256"])
            if obj.get("probes", {}).get("all_pass") is not True:
                raise RuntimeError(f"{rid}: probes failed in the reproduction")
            if obj["predictions"] != orig["predictions"] or obj["inputs_sha256"] != orig["inputs_sha256"]:
                raise RuntimeError(f"{rid}: predictions differ from the original run")
            report[rid] = "identical"
    shutil.rmtree(base)
    return report
