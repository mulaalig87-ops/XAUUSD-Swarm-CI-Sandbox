"""RIP-3 — the registered run driver (design v0.4, FD-01-D47). SYNTHETIC ONLY.
NOT AUTHORISED at BUILD (OD-S9-11 is BUILD only). It refuses to score the registered sets unless --authorisation names
a founder RUN authorisation that is recorded both in docs/DECISIONS.md (an H2 heading '## Founder authorisation <id> —
…' with the words 'RIP-3 RUN') and in docs/research/RIP3_RUN_AUTHORISATIONS.json (sets, approved commit and tree),
whose DECISIONS.md section states the entry's scope sha256, both added together in one commit and unchanged since, and
the checked-out code matches the approved commit (check_authorisation in xauusd_swarm.rip3_auth; OD-S9-17, FL-044).
rip3.run_jobs checks the same record itself (FL-045).
The confirm set's cells are derived from the hash-checked eval_results.json (rip3.confirm_cells, IC3-23); --cands is
refused for it, and the eval result must come from the authorised eval run of the same approved code and environment
(FL-041). Assembling the confirm set adds the FC-3 verdict (rip3.fc3).

Run-driver hardening (FL-036 … FL-045, OD-S9-19): results are written as bytes and hashed on those bytes; a set is
assembled once (an existing result is never replaced or extended); a registered set is assembled only from exactly the
expected job and truth files; every job and truth file names the meta file of the invocation that wrote it, and all
meta files of a set must agree on code and environment; the RIP-2 input of the C-V3 gate is fixed and recorded.

Usage:
  python scripts/rip3_run.py OUT_DIR SET --authorisation OD-... [--cands C1,C2,...] [--worlds W1,W2]
  python scripts/rip3_run.py OUT_DIR SET --assemble [--rip2 docs/results/rip2/results.json]
SET is 'eval' or 'confirm' (registered) or 'smoke' (BUILD-stage small checks; no authorisation needed).
Jobs are resumable (one file per set × candidate × world); every draw is keyed, so order and splitting across
processes do not change any result."""
import argparse
import hashlib
import json
import os
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
from xauusd_swarm import rip3_auth as AUTH          # noqa: E402

CODE = ["src/xauusd_swarm/rip3.py", "src/xauusd_swarm/rip3_auth.py", "src/xauusd_swarm/rip2.py",
        "src/xauusd_swarm/rip1_attack.py", "src/xauusd_swarm/reid.py", "src/xauusd_swarm/representations.py",
        "src/xauusd_swarm/numeric.py", "scripts/rip3_run.py", "docs/research/RIP3_DESIGN.md",
        "docs/research/RIP3_BUILD_NOTES.md"]

# the authorisation check lives in the library (one checker for the driver and the library guard; FL-044, FL-045)
REGISTRY = AUTH.REGISTRY
ALLOWED_AFTER_APPROVAL = AUTH.ALLOWED_AFTER_APPROVAL
AuthorisationError = AUTH.AuthorisationError
scope_sha256 = AUTH.scope_sha256
_decision_section = AUTH.decision_section
check_authorisation = AUTH.check_authorisation
registry_problems = AUTH.registry_problems

RIP2_COMMITTED = "docs/results/rip2/results.json"
# what every meta file of one set must share with the others and with the assembling process (FL-040)
ENV_KEYS = ("commit", "code_sha256", "python", "numpy", "platform", "seeds", "spec", "implementation_choices",
            "authorisation")
# what an eval result must share with the confirm process (FL-041); the commit may differ by records-only commits
EVAL_ENV_KEYS = ("code_sha256", "python", "numpy", "platform", "seeds", "spec", "implementation_choices")
SCOPE_FIELDS = ("id", "sets", "approved_commit", "approved_tree", "scope_sha256", "recorded_in")


def _sha(b):
    return hashlib.sha256(b).hexdigest()


def _plain(o):
    """JSON round trip, so that tuples, numpy scalars and dicts compare as they are stored."""
    return json.loads(json.dumps(o, default=lambda x: x.item() if hasattr(x, "item") else str(x)))


def load_eval_results(out):
    """The assembled evaluation result, checked against its .sha256 file (IC3-23)."""
    f, h = Path(out) / "eval_results.json", Path(out) / "eval_results.sha256"
    if not f.exists() or not h.exists():
        raise SystemExit("confirm needs the assembled eval_results.json and eval_results.sha256 in OUT")
    blob = f.read_bytes()
    if _sha(blob) != h.read_bytes().decode("ascii", "replace").split()[0]:
        raise SystemExit("eval_results.json does not match eval_results.sha256")
    return json.loads(blob)


def sha(p):
    return _sha((ROOT / p).read_bytes())


def meta(set_name, authorisation, auth_check=None):
    commit = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=ROOT).stdout.strip()
    dirty = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, cwd=ROOT).stdout
    return {"experiment": "RIP-3", "set": set_name, "authorisation": authorisation, "commit": commit,
            "tree_clean": not dirty.strip(), "code_sha256": {p: sha(p) for p in CODE}, "python": sys.version,
            "numpy": np.__version__, "platform": platform.platform(), "seeds": R.SEEDS, "spec": dict(R.SPEC),
            "implementation_choices": R.IMPLEMENTATION_CHOICES, "authorisation_check": auth_check, "utc": datetime.now(timezone.utc).isoformat(timespec="seconds")}


def _scope(auth_check):
    return None if not isinstance(auth_check, dict) else {k: auth_check.get(k) for k in SCOPE_FIELDS}


def signature(m):
    """The part of a meta record that must not change within a set (FL-040)."""
    m = _plain(m)
    return dict({k: m.get(k) for k in ENV_KEYS}, authorisation_scope=_scope(m.get("authorisation_check")))


def write_meta(out, m):
    """FL-043: one meta file per invocation, created without replacing any file (time and process id in the name).
    Returns (file name, sha256 of its bytes)."""
    name = f"{m['set']}_meta_{int(time.time())}_{os.getpid()}.json"
    data = json.dumps(_plain(m), indent=1).encode("utf-8")
    try:
        R._publish_new(Path(out) / name, data)
    except (R.ConflictError, R.HardLinkUnsupported) as e:
        raise SystemExit(f"FL-043: {e}") from None
    return name, _sha(data)


def results_paths(out, set_name):
    return Path(out) / f"{set_name}_results.json", Path(out) / f"{set_name}_results.sha256"


def refuse_existing_results(out, set_name):
    """FL-038: a set is assembled once; once its result exists nothing for that set is run or assembled again."""
    for p in results_paths(out, set_name):
        if p.exists():
            raise SystemExit(f"FL-038: {p.name} exists in {out}: a set is assembled once and its result is never "
                             "replaced or extended")


def write_results(out, set_name, res):
    """FL-036 / FL-038: serialise once, hash exactly those bytes, write them as bytes (no newline translation on any
    platform), never replacing an existing file. Returns the sha256."""
    refuse_existing_results(out, set_name)
    blob = json.dumps(res, indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o)).encode("utf-8")
    h = _sha(blob)
    rp, hp = results_paths(out, set_name)
    never_same = lambda old, new: False                          # noqa: E731
    try:
        R._publish_new(rp, blob, never_same)
        R._publish_new(hp, f"{h}  {rp.name}\n".encode("ascii"), never_same)
    except (R.ConflictError, R.HardLinkUnsupported) as e:
        raise SystemExit(f"FL-038: {e}") from None
    return h


def expected_files(set_name, cands, worlds):
    return ({f"{set_name}__truth__{w}.json" for w in worlds}
            | {f"{set_name}__{c}__{w}.json" for c in cands for w in worlds})


def check_complete(out, set_name, cands, worlds):
    """FL-037: a registered set is assembled only from exactly its expected truth and job files, each readable."""
    present = {p.name for p in Path(out).glob(f"{set_name}__*.json")}
    want = expected_files(set_name, cands, worlds)
    missing, extra = sorted(want - present), sorted(present - want)
    if missing or extra:
        raise SystemExit(f"FL-037: the {set_name} folder is not exactly the expected set of files: missing {missing}, "
                         f"unexpected {extra}")
    for name in sorted(want):
        try:
            json.loads((Path(out) / name).read_bytes())
        except ValueError:
            raise SystemExit(f"FL-037: {name} is not readable JSON") from None


def _file_cell(name, set_name):
    """(candidate or None for a truth file, world) from a job or truth file name of the set."""
    core = name[len(set_name) + 2:-len(".json")]
    if core.startswith("truth__"):
        return None, core[len("truth__"):]
    cand, _, world = core.rpartition("__")
    return cand, world


def check_provenance(out, set_name, current, registered):
    """FL-040: every job and truth file names an existing meta file of this set with the right hash, and that meta
    file's invocation ran that file's candidate and world (a truth file: its world; review R1-3); all meta files of
    the set agree with each other and with the assembling process on code and environment. Returns {meta: sha256}."""
    metas = {}
    for p in sorted(Path(out).glob(f"{set_name}_meta_*.json")):
        b = p.read_bytes()
        try:
            metas[p.name] = (_sha(b), json.loads(b))
        except ValueError:
            raise SystemExit(f"FL-040: meta file {p.name} is not readable JSON") from None
    if not metas:
        raise SystemExit(f"FL-040: no {set_name}_meta_*.json file in {out}")
    want = signature(current)
    for name, (_, m) in metas.items():
        got = signature(m) if isinstance(m, dict) else {}
        diff = sorted(k for k in want if got.get(k) != want[k])
        if not isinstance(m, dict) or m.get("set") != set_name or diff:
            raise SystemExit(f"FL-040: meta file {name} differs from the assembling process in {diff or ['set']}: "
                             "results from different code or environments are not mixed")
        if registered and m.get("tree_clean") is not True:
            raise SystemExit(f"FL-040: meta file {name} was written from a working tree that was not clean")
        inv = m.get("invocation")
        if (not isinstance(inv, dict) or not isinstance(inv.get("cands"), list)
                or not isinstance(inv.get("worlds"), list)):
            raise SystemExit(f"FL-040: meta file {name} does not record its invocation (cells and worlds run)")
    for p in sorted(Path(out).glob(f"{set_name}__*.json")):
        try:
            pv = json.loads(p.read_bytes()).get("provenance")
        except (ValueError, AttributeError):
            raise SystemExit(f"FL-040: {p.name} is not a readable job or truth file") from None
        if (not isinstance(pv, dict) or pv.get("meta") not in metas
                or pv.get("meta_sha256") != metas[pv["meta"]][0]):
            raise SystemExit(f"FL-040: {p.name} does not name an existing meta file of this set with its sha256")
        inv = metas[pv["meta"]][1]["invocation"]
        cand, world = _file_cell(p.name, set_name)
        if world not in inv["worlds"] or (cand is not None and cand not in inv["cands"]):
            raise SystemExit(f"FL-040: {p.name} names {pv['meta']}, whose invocation did not run "
                             f"{'world ' + world if cand is None else cand + ' in ' + world} (review R1-3)")
    return {name: h for name, (h, _) in metas.items()}


def check_eval_result(out, eval_out, current, confirm_auth):
    """FL-041: the eval result that selects the confirm cells must be the authorised eval result of the same approved
    code and environment, assembled from exactly the eval files in this folder."""
    em = eval_out.get("meta") if isinstance(eval_out, dict) else None
    if not isinstance(em, dict) or em.get("set") != "eval":
        raise SystemExit("FL-041: eval_results.json is not the result of the eval set")
    if not isinstance(em.get("authorisation_check"), dict) or not em.get("authorisation"):
        raise SystemExit("FL-041: eval_results.json carries no authorisation check")
    if em.get("tree_clean") is not True:
        raise SystemExit("FL-041: the eval result was assembled from a working tree that was not clean (review R1-4)")
    c = subprocess.run(["git", "show", f"HEAD:{RIP2_COMMITTED}"], capture_output=True, cwd=ROOT)
    r2 = em.get("rip2")
    if c.returncode != 0 or not isinstance(r2, dict) or r2.get("sha256") != _sha(c.stdout):
        raise SystemExit(f"FL-041: the eval result's RIP-2 record does not match {RIP2_COMMITTED} in HEAD (review R1-4)")
    now = check_authorisation(ROOT, em["authorisation"], "eval")       # still recorded, unchanged, same code
    if _scope(_plain(em["authorisation_check"])) != _scope(_plain(now)):
        raise SystemExit("FL-041: the eval result's authorisation record differs from the record in HEAD")
    if (now["approved_commit"], now["approved_tree"]) != (confirm_auth["approved_commit"], confirm_auth["approved_tree"]):
        raise SystemExit("FL-041: the eval and confirm authorisations approve different code")
    cur = _plain(current)
    diff = sorted(k for k in EVAL_ENV_KEYS if _plain(em.get(k)) != cur.get(k))
    if diff:
        raise SystemExit(f"FL-041: the eval result differs from this process in {diff}: results from different code "
                         "or environments are not mixed")
    files = {p.name: _sha(p.read_bytes()) for p in sorted(Path(out).glob("eval__*.json"))}
    if set(files) != expected_files("eval", R.ALL_CELLS, R.WORLDS) or eval_out.get("jobs_sha256") != files:
        raise SystemExit("FL-041: the eval job and truth files in the folder are not exactly those of eval_results.json")
    metas = {p.name: _sha(p.read_bytes()) for p in sorted(Path(out).glob("eval_meta_*.json"))}
    if eval_out.get("run_meta_sha256") != metas:
        raise SystemExit("FL-041: the eval meta files in the folder are not exactly those of eval_results.json")


def rip2_input(path, registered):
    """FL-042: the RIP-2 result read by the C-V3 gate. For eval and confirm it must exist and equal, byte for byte, the
    committed docs/results/rip2/results.json; its path and sha256 are recorded. Returns (parsed or None, record)."""
    p = Path(path) if path else None
    if p is None or not p.exists():
        if registered:
            raise SystemExit(f"FL-042: the RIP-2 result ({path!r}) is required for the registered sets")
        return None, {"path": None, "sha256": None}
    data = p.read_bytes()
    if registered:
        c = subprocess.run(["git", "show", f"HEAD:{RIP2_COMMITTED}"], capture_output=True, cwd=ROOT)
        if c.returncode != 0 or data != c.stdout:
            raise SystemExit(f"FL-042: {p} is not byte-identical to {RIP2_COMMITTED} in the committed HEAD")
    return json.loads(data), {"path": str(p), "sha256": _sha(data)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("set", choices=["eval", "confirm", "smoke"])
    ap.add_argument("--authorisation", default=None)
    ap.add_argument("--cands", default=None)
    ap.add_argument("--worlds", default="W1,W2")
    ap.add_argument("--assemble", action="store_true")
    ap.add_argument("--rip2", default=str(ROOT / RIP2_COMMITTED))
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    try:
        R.check_hard_links(out)                       # review R1-2: before anything is written
    except R.HardLinkUnsupported as e:
        raise SystemExit(f"hard link check failed: {e}") from None
    registered = a.set in R.REGISTERED_SETS
    auth = check_authorisation(ROOT, a.authorisation, a.set) if registered else None
    m = meta(a.set, a.authorisation, auth)
    if registered and not m["tree_clean"]:
        raise SystemExit("working tree not clean: the run must use exactly the committed code")
    refuse_existing_results(out, a.set)
    worlds = tuple(a.worlds.split(","))
    if registered and not set(worlds) <= set(R.WORLDS):
        raise SystemExit(f"unknown world in {worlds!r}")
    eval_out = load_eval_results(out) if a.set == "confirm" else None
    if a.set == "confirm":
        check_eval_result(out, eval_out, m, auth)
        if a.cands is not None:
            raise SystemExit("--cands is refused for the confirm set: its cells come from eval_results.json (IC3-23)")
        cands = R.confirm_cells(eval_out)
        if not cands:
            raise SystemExit("no chosen candidate on the evaluation set (FC-1 in both classes): nothing to confirm")
    else:
        cands = (a.cands or ",".join(R.ALL_CELLS)).split(",")
    if registered and not set(cands) <= set(R.ALL_CELLS):
        raise SystemExit(f"unknown cell in {cands!r}")
    if a.assemble:
        if registered:
            check_complete(out, a.set, R.ALL_CELLS if a.set == "eval" else cands, R.WORLDS)
        run_meta = check_provenance(out, a.set, m, registered)
        jobs = R.load_jobs(out, a.set)
        r2, r2_record = rip2_input(a.rip2, registered)
        res = R.evaluate(jobs, a.set, r2, authorisation=a.authorisation if registered else None)
        if a.set == "confirm":
            res["confirm_cells"] = cands
            res["fc3"] = R.fc3(eval_out, res, jobs)
            m["eval_results_sha256"] = _sha((out / "eval_results.json").read_bytes())
        m["rip2"] = r2_record
        res["meta"] = m
        res["jobs_sha256"] = {p.name: _sha(p.read_bytes()) for p in sorted(out.glob(f"{a.set}__*.json"))}
        res["run_meta_sha256"] = run_meta
        h = write_results(out, a.set, res)
        print("assembled", len(jobs), "jobs", h)
        return
    name, h = write_meta(out, dict(m, invocation={"pid": os.getpid(), "cands": cands, "worlds": list(worlds)}))
    t0 = time.time()
    done = R.run_jobs(out, a.set, cands, worlds, authorisation=a.authorisation if registered else None,
                      provenance={"meta": name, "meta_sha256": h})
    print("jobs written", done, round(time.time() - t0, 1), "s")


if __name__ == "__main__":
    main()
