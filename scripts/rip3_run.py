"""RIP-3 — the registered run driver (design v0.4, FD-01-D47). SYNTHETIC ONLY.
NOT AUTHORISED at BUILD (OD-S9-11 is BUILD only). It refuses to score the registered sets unless --authorisation names
a founder RUN authorisation that is recorded both in docs/DECISIONS.md (a heading with its identifier and the words
'RIP-3 RUN') and in
docs/research/RIP3_RUN_AUTHORISATIONS.json (sets, approved commit and tree), whose DECISIONS.md section states the
entry's scope sha256, both added together in one commit and unchanged since, and the checked-out code matches the approved
commit (check_authorisation; OD-S9-17). rip3.run_jobs refuses the registered sets as well (authorised_run guard).
The confirm set's cells are derived from the hash-checked eval_results.json (rip3.confirm_cells, IC3-23); --cands is
refused for it. Assembling the confirm set adds the FC-3 verdict (rip3.fc3).

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


REGISTRY = "docs/research/RIP3_RUN_AUTHORISATIONS.json"
ALLOWED_AFTER_APPROVAL = {REGISTRY, "docs/DECISIONS.md"}


class AuthorisationError(SystemExit):
    pass


def _git(root, *args):
    p = subprocess.run(["git", *args], capture_output=True, text=True, cwd=root)
    return p.returncode, p.stdout.strip()


def scope_sha256(entry):
    """The hash of an authorisation's scope (id, sets, approved commit and tree), canonical JSON."""
    keys = ("id", "sets", "approved_commit", "approved_tree")
    blob = json.dumps({k: entry.get(k) for k in keys}, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(blob.encode("ascii")).hexdigest()


def _decision_section(text, auth_id):
    """The DECISIONS.md section of a RUN authorisation: its '## ' heading (with the id and 'RIP-3 RUN') up to the next
    '## ' heading. None if there is no such heading or more than one."""
    lines = text.splitlines()
    starts = [i for i, ln in enumerate(lines) if ln.startswith("## ") and auth_id in ln and "RIP-3 RUN" in ln]
    if len(starts) != 1:
        return None
    end = next((i for i in range(starts[0] + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
    return "\n".join(lines[starts[0]:end]).rstrip()


def _at(root, rev, path):
    rc, out = _git(root, "show", f"{rev}:{path}")
    return out if rc == 0 else None


def _entry(registry_text, auth_id):
    try:
        es = [e for e in json.loads(registry_text).get("authorisations", []) if e.get("id") == auth_id]
    except (ValueError, AttributeError):
        return None
    return es[0] if len(es) == 1 else None


def check_authorisation(root, auth_id, set_name):
    """OD-S9-17 (hardened after review): the identifier must be a founder RUN authorisation recorded, in the committed
    HEAD, both in RIP3_RUN_AUTHORISATIONS.json (exactly one entry: sets, approved commit and tree) and in DECISIONS.md
    (exactly one 'RIP-3 RUN' heading with the id, whose section states the entry's scope hash). The entry and that
    section must be byte-for-byte what they were in the first commit that recorded the entry: a later change of the
    scope (for example more sets) is refused. The code must be the approved commit, or a descendant that differs from
    it only in these two files. Working-tree files are not read."""
    root = Path(root)
    if not auth_id:
        raise AuthorisationError("the registered sets need the founder's RUN authorisation identifier (--authorisation)")
    reg_head = _at(root, "HEAD", REGISTRY)
    if reg_head is None:
        raise AuthorisationError(f"authorisation registry missing in HEAD: {REGISTRY}")
    e = _entry(reg_head, auth_id)
    if e is None:
        raise AuthorisationError(f"authorisation {auth_id!r} is not recorded (exactly once) in {REGISTRY}")
    sets = e.get("sets")
    if not isinstance(sets, list) or not sets or len(set(sets)) != len(sets) or not set(sets) <= {"eval", "confirm"}:
        raise AuthorisationError(f"authorisation {auth_id}: invalid sets {sets!r}")
    if set_name not in sets:
        raise AuthorisationError(f"authorisation {auth_id} does not cover the set {set_name!r}")
    sec_head = _decision_section(_at(root, "HEAD", "docs/DECISIONS.md") or "", auth_id)
    if sec_head is None:
        raise AuthorisationError(f"authorisation {auth_id} has no single 'RIP-3 RUN' heading in docs/DECISIONS.md")
    h = scope_sha256(e)
    if f"scope sha256: {h}" not in sec_head:
        raise AuthorisationError(f"the DECISIONS.md section of {auth_id} does not state the entry's scope sha256 {h}")
    commit, tree = e.get("approved_commit", ""), e.get("approved_tree", "")
    rc, t = _git(root, "rev-parse", f"{commit}^{{tree}}")
    if rc != 0 or t != tree:
        raise AuthorisationError(f"approved commit {commit} not found or its tree is not {tree}")
    rc, _ = _git(root, "merge-base", "--is-ancestor", commit, "HEAD")
    if rc != 0:
        raise AuthorisationError(f"HEAD does not descend from the approved commit {commit}")
    rc, changed = _git(root, "diff", "--name-only", commit, "HEAD")
    extra = sorted(set(filter(None, changed.splitlines())) - ALLOWED_AFTER_APPROVAL)
    if rc != 0 or extra:
        raise AuthorisationError(f"files changed since the approved commit outside the authorisation records: {extra}")
    rc, revs = _git(root, "rev-list", "--reverse", f"{commit}..HEAD", "--", REGISTRY)
    first = next((c for c in revs.split() if _entry(_at(root, c, REGISTRY) or "{}", auth_id) is not None), None)
    if rc != 0 or first is None:
        raise AuthorisationError(f"no commit after {commit} records {auth_id}")
    if _entry(_at(root, first, REGISTRY), auth_id) != e:
        raise AuthorisationError(f"the registry entry of {auth_id} changed since it was recorded in {first}")
    if _decision_section(_at(root, first, "docs/DECISIONS.md") or "", auth_id) != sec_head:
        raise AuthorisationError(f"the DECISIONS.md section of {auth_id} changed since it was recorded in {first}")
    rc, parents = _git(root, "rev-list", "--parents", "-n", "1", first)
    parents = parents.split()[1:] if rc == 0 else []
    if len(parents) != 1:
        raise AuthorisationError(f"the commit {first} that recorded {auth_id} must have exactly one parent")
    if _decision_section(_at(root, parents[0], "docs/DECISIONS.md") or "", auth_id) is not None:
        raise AuthorisationError(f"the decision section of {auth_id} existed before {first}: the entry and the section "
                                 "must be added together in one commit")
    _, head = _git(root, "rev-parse", "HEAD")
    return {"id": auth_id, "set": set_name, "sets": sets, "approved_commit": commit, "approved_tree": tree,
            "scope_sha256": h, "recorded_in": first, "head": head}


def load_eval_results(out):
    """The assembled evaluation result, checked against its .sha256 file (IC3-23)."""
    f, h = Path(out) / "eval_results.json", Path(out) / "eval_results.sha256"
    if not f.exists() or not h.exists():
        raise SystemExit("confirm needs the assembled eval_results.json and eval_results.sha256 in OUT")
    blob = f.read_bytes()
    if hashlib.sha256(blob).hexdigest() != h.read_text().split()[0]:
        raise SystemExit("eval_results.json does not match eval_results.sha256")
    return json.loads(blob)


def sha(p):
    return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()


def meta(set_name, authorisation, auth_check=None):
    commit = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=ROOT).stdout.strip()
    dirty = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, cwd=ROOT).stdout
    return {"experiment": "RIP-3", "set": set_name, "authorisation": authorisation, "commit": commit,
            "tree_clean": not dirty.strip(), "code_sha256": {p: sha(p) for p in CODE}, "python": sys.version,
            "numpy": np.__version__, "platform": platform.platform(), "seeds": R.SEEDS, "spec": dict(R.SPEC),
            "implementation_choices": R.IMPLEMENTATION_CHOICES, "authorisation_check": auth_check, "utc": datetime.now(timezone.utc).isoformat(timespec="seconds")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("set", choices=["eval", "confirm", "smoke"])
    ap.add_argument("--authorisation", default=None)
    ap.add_argument("--cands", default=None)
    ap.add_argument("--worlds", default="W1,W2")
    ap.add_argument("--assemble", action="store_true")
    ap.add_argument("--rip2", default=str(ROOT / "docs/results/rip2/results.json"))
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    registered = a.set in R.REGISTERED_SETS
    auth = check_authorisation(ROOT, a.authorisation, a.set) if registered else None
    m = meta(a.set, a.authorisation, auth)
    if registered and not m["tree_clean"]:
        raise SystemExit("working tree not clean: the run must use exactly the committed code")
    eval_out = load_eval_results(out) if a.set == "confirm" else None
    if a.set == "confirm":
        if a.cands is not None:
            raise SystemExit("--cands is refused for the confirm set: its cells come from eval_results.json (IC3-23)")
        cands = R.confirm_cells(eval_out)
        if not cands:
            raise SystemExit("no chosen candidate on the evaluation set (FC-1 in both classes): nothing to confirm")
    else:
        cands = (a.cands or ",".join(R.ALL_CELLS)).split(",")
    if a.assemble:
        jobs = R.load_jobs(out, a.set)
        r2 = json.loads(Path(a.rip2).read_text()) if a.rip2 and Path(a.rip2).exists() else None
        res = R.evaluate(jobs, a.set, r2)
        if a.set == "confirm":
            res["confirm_cells"] = cands
            res["fc3"] = R.fc3(eval_out, res, jobs)
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
    done = R.run_jobs(out, a.set, cands, tuple(a.worlds.split(",")), authorised_run=registered)
    print("jobs written", done, round(time.time() - t0, 1), "s")


if __name__ == "__main__":
    main()
