"""FL-036 … FL-045: run-driver hardening tests (founder decision OD-S9-19). SYNTHETIC ONLY.

No test here scores a registered set (eval / confirm, seeds 6201 / 6301): every test that reaches a registered code path
first replaces the scoring functions (truth_job, identity_scenario, utility_job, evaluate, run_jobs) with a sentinel
that raises WouldScore, so a missing refusal shows up as a WouldScore failure, never as a computation. Files labelled
'eval' or 'confirm' below are hand-made dicts, not results of those sets.
"""
import hashlib
import importlib.util
import json
import os
import sys
from pathlib import Path

import pytest

from xauusd_swarm import rip3 as R

ROOT = Path(__file__).resolve().parents[1]
CELLS = ["B-LR", "M1", "M5"]                               # a few cells for the smoke set (completeness not required)
ACC = {"B-LR": 1.0, "M1": 0.3, "M5": 0.2}


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


T3 = _load("test_rip3_helpers_for_hardening", ROOT / "tests" / "test_rip3.py")   # _fake_jobs, _git, _record, …


def _run():
    return _load("rip3_run_hardening_under_test", ROOT / "scripts" / "rip3_run.py")


def _sha(b):
    return hashlib.sha256(b).hexdigest()


def _dumps(o):
    return json.dumps(o).encode("utf-8")


class WouldScore(AssertionError):
    pass


def _boom(*a, **k):
    raise WouldScore("a registered set would be scored here")


@pytest.fixture
def no_compute(monkeypatch):
    for name in ("truth_job", "identity_scenario", "utility_job"):
        monkeypatch.setattr(R, name, _boom)


@pytest.fixture
def no_scoring(monkeypatch, no_compute):
    monkeypatch.setattr(R, "evaluate", _boom)
    monkeypatch.setattr(R, "run_jobs", _boom)


def _fake_auth(set_name, **over):
    return dict({"id": "OD-TEST-H", "set": set_name, "sets": ["eval", "confirm"], "approved_commit": "a" * 40,
                 "approved_tree": "b" * 40, "scope_sha256": "c" * 64, "recorded_in": "d" * 40, "head": "e" * 40}, **over)


def _authorised(run, monkeypatch, **over):
    """Replace the recorded-authorisation check by a fixed answer and the clean-tree flag by True (only the driver's
    own refusals are under test; the real guard is tested in test_rip3.py and the FL-044 tests below)."""
    monkeypatch.setattr(run, "check_authorisation", lambda root, auth_id, set_name: _fake_auth(set_name, **over))
    real = run.meta
    monkeypatch.setattr(run, "meta", lambda s, a, c=None: dict(real(s, a, c), tree_clean=True))


def _meta(run, set_name, auth_id=None, auth=None, **over):
    m = json.loads(json.dumps(dict(run.meta(set_name, auth_id, auth), tree_clean=True), default=str))
    m.update(over)
    return m


def _write_meta(out, m, tag, cands=None, worlds=None):
    """A meta file as the driver writes it, with its invocation (review R1-3: the cells and worlds it ran)."""
    m = dict(m, invocation={"pid": 1, "cands": list(cands or R.ALL_CELLS), "worlds": list(worlds or R.WORLDS)})
    name = f"{m['set']}_meta_{tag}.json"
    data = json.dumps(m, indent=1).encode("utf-8")
    (out / name).write_bytes(data)
    return name, _sha(data)


def _job(set_name, cand, world, prov):
    j = T3._fake_jobs({(cand, world): ACC.get(cand, 0.3)})[(cand, world)]
    j.update(set=set_name, candidate=cand, world=world)
    if prov is not None:
        j["provenance"] = prov
    return j


def _folder(out, set_name, cells, prov, truth=True, worlds=R.WORLDS):
    for w in worlds:
        if truth:
            (out / f"{set_name}__truth__{w}.json").write_bytes(
                _dumps({"pairs": [], "w2_truth_failures": 0, "provenance": prov}))
        for c in cells:
            (out / f"{set_name}__{c}__{w}.json").write_bytes(_dumps(_job(set_name, c, w, prov)))


def _main(run, monkeypatch, *args):
    monkeypatch.setattr(sys, "argv", ["rip3_run.py", *map(str, args)])
    return run.main()


def _smoke_folder(run, tmp_path):
    out = tmp_path / "o"
    out.mkdir()
    name, h = _write_meta(out, _meta(run, "smoke"), "1")
    _folder(out, "smoke", CELLS, {"meta": name, "meta_sha256": h}, truth=False)
    return out, name, h


def _eval_folder(run, tmp_path):
    out = tmp_path / "o"
    out.mkdir()
    name, h = _write_meta(out, _meta(run, "eval", "OD-TEST-H", _fake_auth("eval")), "1")
    _folder(out, "eval", R.ALL_CELLS, {"meta": name, "meta_sha256": h})
    return out, name, h


def _eval_result(run, out, **over):
    """A hand-made, consistent eval_results.json (+ .sha256) for the confirm checks: selection, meta, file hashes."""
    meta = json.loads((out / sorted(p.name for p in out.glob("eval_meta_*.json"))[0]).read_bytes())
    meta.pop("invocation", None)
    meta["rip2"] = {"path": str(ROOT / "docs/results/rip2/results.json"),             # as the assembly records it
                    "sha256": _sha((ROOT / "docs/results/rip2/results.json").read_bytes())}
    res = {"selection": {"P": {"chosen": "M1", "nearest_competitor": None}, "S": {"chosen": None}},
           "meta": meta,
           "jobs_sha256": {p.name: _sha(p.read_bytes()) for p in sorted(out.glob("eval__*.json"))},
           "run_meta_sha256": {p.name: _sha(p.read_bytes()) for p in sorted(out.glob("eval_meta_*.json"))}}
    res.update(over)
    blob = json.dumps(res, indent=1).encode("utf-8")
    (out / "eval_results.json").write_bytes(blob)
    (out / "eval_results.sha256").write_bytes(f"{_sha(blob)}  eval_results.json\n".encode("ascii"))
    return res


def _windows_text_mode(monkeypatch):
    """What Path.write_text does on Windows: text mode turns every '\\n' into '\\r\\n' (simulated on every platform)."""
    def write_text(self, data, encoding=None, errors=None, newline=None):
        return self.write_bytes(data.replace("\n", "\r\n").encode(encoding or "utf-8", errors or "strict"))
    monkeypatch.setattr(Path, "write_text", write_text)


# ---------------- FL-036 (A-01): result hash and Windows newlines ----------------
def test_fl036_assembled_result_hash_matches_its_bytes_under_windows_newlines(tmp_path, monkeypatch):
    run = _run()
    monkeypatch.setitem(R.SPEC, "B", 200)
    out, _, _ = _smoke_folder(run, tmp_path)
    _windows_text_mode(monkeypatch)
    _main(run, monkeypatch, out, "smoke", "--assemble", "--rip2", "")
    blob = (out / "smoke_results.json").read_bytes()
    assert (out / "smoke_results.sha256").read_bytes().split()[0].decode() == _sha(blob)


def test_fl036_confirm_accepts_an_eval_result_written_under_windows_newlines(tmp_path, monkeypatch):
    run = _run()
    res = {"selection": {"P": {"chosen": "M1", "nearest_competitor": None}}, "x": [1, 2]}
    _windows_text_mode(monkeypatch)
    run.write_results(tmp_path, "eval", res)
    assert R.confirm_cells(run.load_eval_results(tmp_path)) == ["B-LR", "M1"]


def test_fl036_native_round_trip_keeps_lf_bytes(tmp_path):
    run = _run()                                    # on the Windows CI job this runs with real Windows text mode
    h = run.write_results(tmp_path, "eval", {"selection": {"P": {"chosen": "M1"}}, "x": [1, 2]})
    blob = (tmp_path / "eval_results.json").read_bytes()
    assert b"\r\n" not in blob and b"\n" in blob and _sha(blob) == h
    assert run.load_eval_results(tmp_path)["x"] == [1, 2]


# ---------------- FL-037 (A-02): completeness before assembling a registered set ----------------
@pytest.mark.parametrize("damage", ["missing job", "missing truth", "extra job"])
def test_fl037_registered_assemble_refuses_an_incomplete_or_extended_folder(tmp_path, monkeypatch, no_scoring, damage,
                                                                           threads_one):
    run = _run()
    _authorised(run, monkeypatch)
    out, name, h = _eval_folder(run, tmp_path)
    if damage == "missing job":
        (out / "eval__M3W32__W2.json").unlink()
    elif damage == "missing truth":
        (out / "eval__truth__W1.json").unlink()
    else:
        (out / "eval__B-LR__W3.json").write_bytes(_dumps(_job("eval", "B-LR", "W3", {"meta": name, "meta_sha256": h})))
    with pytest.raises(SystemExit, match="FL-037"):
        _main(run, monkeypatch, out, "eval", "--authorisation", "OD-TEST-H", "--assemble")


def test_fl037_complete_registered_folder_passes_the_checks(tmp_path, monkeypatch, no_scoring, threads_one):
    run = _run()
    _authorised(run, monkeypatch)
    out, _, _ = _eval_folder(run, tmp_path)
    with pytest.raises(WouldScore):                 # every check passed; the sentinel stands in for evaluate
        _main(run, monkeypatch, out, "eval", "--authorisation", "OD-TEST-H", "--assemble")


# ---------------- FL-038 (A-03): assemble once ----------------
def test_fl038_second_assembly_is_refused_and_the_first_result_is_kept(tmp_path, monkeypatch):
    run = _run()
    monkeypatch.setitem(R.SPEC, "B", 200)
    out, _, _ = _smoke_folder(run, tmp_path)
    _main(run, monkeypatch, out, "smoke", "--assemble", "--rip2", "")
    first = ((out / "smoke_results.json").read_bytes(), (out / "smoke_results.sha256").read_bytes())
    with pytest.raises(SystemExit, match="FL-038"):
        _main(run, monkeypatch, out, "smoke", "--assemble", "--rip2", "")
    assert ((out / "smoke_results.json").read_bytes(), (out / "smoke_results.sha256").read_bytes()) == first


def test_fl038_job_run_after_the_result_exists_is_refused(tmp_path, monkeypatch, no_scoring):
    run = _run()
    out = tmp_path / "o"
    out.mkdir()
    (out / "smoke_results.json").write_bytes(b"{}")
    with pytest.raises(SystemExit, match="FL-038"):
        _main(run, monkeypatch, out, "smoke", "--cands", "B-LR", "--worlds", "W1")


# ---------------- FL-039 (A-04): job files must agree with their names ----------------
@pytest.mark.parametrize("case", ["other candidate", "other set", "unknown world", "unknown cell"])
def test_fl039_load_jobs_refuses_a_file_that_disagrees_with_its_name(tmp_path, case):
    good = _job("smoke", "M1", "W1", None)
    if case == "other candidate":
        name, j = "smoke__M1__W1.json", dict(good, candidate="M2w1")
    elif case == "other set":
        name, j = "smoke__M1__W1.json", dict(good, set="eval")
    elif case == "unknown world":
        name, j = "smoke__M1__W3.json", dict(good, world="W3")
    else:
        name, j = "smoke__ZZ__W1.json", dict(good, candidate="ZZ")
    (tmp_path / "smoke__B-LR__W1.json").write_bytes(_dumps(_job("smoke", "B-LR", "W1", None)))
    (tmp_path / name).write_bytes(_dumps(j))
    with pytest.raises(ValueError, match="FL-039"):
        R.load_jobs(tmp_path, "smoke")


def test_fl039_consistent_files_load(tmp_path):
    for c in CELLS:
        (tmp_path / f"smoke__{c}__W1.json").write_bytes(_dumps(_job("smoke", c, "W1", None)))
    assert set(R.load_jobs(tmp_path, "smoke")) == {(c, "W1") for c in CELLS}


# ---------------- FL-040 (P-01): run-time provenance bound into the result ----------------
@pytest.mark.parametrize("case", ["job without provenance", "unknown meta file", "meta hash mismatch",
                                  "other numpy", "other commit", "other platform"])
def test_fl040_assemble_refuses_unlinked_or_mixed_provenance(tmp_path, monkeypatch, case):
    run = _run()
    monkeypatch.setitem(R.SPEC, "B", 200)
    out, name, h = _smoke_folder(run, tmp_path)
    p = out / "smoke__M1__W2.json"
    j = json.loads(p.read_bytes())
    if case == "job without provenance":
        j.pop("provenance")
    elif case == "unknown meta file":
        j["provenance"] = {"meta": "smoke_meta_gone.json", "meta_sha256": h}
    elif case == "meta hash mismatch":
        j["provenance"] = {"meta": name, "meta_sha256": "0" * 64}
    else:
        key = {"other numpy": "numpy", "other commit": "commit", "other platform": "platform"}[case]
        n2, h2 = _write_meta(out, _meta(run, "smoke", **{key: "something else"}), "2")
        j["provenance"] = {"meta": n2, "meta_sha256": h2}
    p.write_bytes(_dumps(j))
    with pytest.raises(SystemExit, match="FL-040"):
        _main(run, monkeypatch, out, "smoke", "--assemble", "--rip2", "")
    assert not (out / "smoke_results.json").exists()


def test_fl040_result_lists_the_meta_files(tmp_path, monkeypatch):
    run = _run()
    monkeypatch.setitem(R.SPEC, "B", 200)
    out, name, h = _smoke_folder(run, tmp_path)
    _main(run, monkeypatch, out, "smoke", "--assemble", "--rip2", "")
    res = json.loads((out / "smoke_results.json").read_bytes())
    assert res["run_meta_sha256"] == {name: h}
    assert all(json.loads(p.read_bytes())["provenance"] == {"meta": name, "meta_sha256": h}
               for p in out.glob("smoke__*.json"))


# ---------------- FL-041 (P-02): confirm checks where the eval result came from ----------------
@pytest.mark.parametrize("case", ["no authorisation check", "other approved commit", "job hashes differ",
                                  "other python", "meta file changed", "not an eval result"])
def test_fl041_confirm_refuses_an_eval_result_of_unknown_origin(tmp_path, monkeypatch, no_scoring, case, threads_one):
    run = _run()
    _authorised(run, monkeypatch)
    out, name, _ = _eval_folder(run, tmp_path)
    res = _eval_result(run, out)
    if case == "no authorisation check":
        _eval_result(run, out, meta=dict(res["meta"], authorisation_check=None))
    elif case == "other approved commit":
        _authorised(run, monkeypatch, approved_commit="f" * 40)       # the confirm authorisation approves other code
    elif case == "job hashes differ":
        _eval_result(run, out, jobs_sha256=dict(res["jobs_sha256"], **{"eval__M1__W1.json": "0" * 64}))
    elif case == "other python":
        _eval_result(run, out, meta=dict(res["meta"], python="3.0"))
    elif case == "meta file changed":
        (out / name).write_bytes((out / name).read_bytes() + b" ")
    else:
        _eval_result(run, out, meta=dict(res["meta"], set="smoke"))
    with pytest.raises(SystemExit, match="FL-041"):
        _main(run, monkeypatch, out, "confirm", "--authorisation", "OD-TEST-H", "--worlds", "W1")


def test_fl041_consistent_eval_result_passes_the_confirm_checks(tmp_path, monkeypatch, no_scoring, threads_one):
    run = _run()
    _authorised(run, monkeypatch)
    out, _, _ = _eval_folder(run, tmp_path)
    _eval_result(run, out)
    with pytest.raises(WouldScore):                 # every check passed; the sentinel stands in for run_jobs
        _main(run, monkeypatch, out, "confirm", "--authorisation", "OD-TEST-H", "--worlds", "W1")


# ---------------- FL-042 (P-03): the RIP-2 input of the C-V3 gate ----------------
@pytest.mark.parametrize("case", ["missing", "different"])
def test_fl042_registered_assemble_refuses_a_missing_or_different_rip2_file(tmp_path, monkeypatch, no_scoring, case,
                                                                            threads_one):
    run = _run()
    _authorised(run, monkeypatch)
    out, _, _ = _eval_folder(run, tmp_path)
    r2 = tmp_path / "rip2.json"
    if case == "different":
        r2.write_bytes((ROOT / "docs/results/rip2/results.json").read_bytes() + b"\n")
    with pytest.raises(SystemExit, match="FL-042"):
        _main(run, monkeypatch, out, "eval", "--authorisation", "OD-TEST-H", "--assemble", "--rip2", r2)


def test_fl042_result_records_the_rip2_input(tmp_path, monkeypatch):
    run = _run()
    monkeypatch.setitem(R.SPEC, "B", 200)
    out, _, _ = _smoke_folder(run, tmp_path)
    _main(run, monkeypatch, out, "smoke", "--assemble", "--rip2", "")
    assert json.loads((out / "smoke_results.json").read_bytes())["meta"]["rip2"] == {"path": None, "sha256": None}


# ---------------- FL-043 (R-01): parallel writers ----------------
def test_fl043_each_write_uses_its_own_temporary_file(tmp_path, monkeypatch):
    seen = []
    real = os.replace

    def spy(src, dst):
        seen.append(Path(src).name)
        return real(src, dst)
    monkeypatch.setattr(R.os, "replace", spy)
    p = tmp_path / "smoke__X__W1.json"
    R._atomic_write(p, '{"a": 1}')
    R._atomic_write(p, '{"a": 1}')
    assert len(seen) == 2 and seen[0] != seen[1] and all(s.endswith(".json.tmp") for s in seen)
    assert not list(tmp_path.glob("*.tmp"))


def test_fl043_publishing_never_replaces_an_existing_file(tmp_path):
    p = tmp_path / "smoke__X__W1.json"
    assert R._publish_new(p, b'{"a": 1}') is True
    assert R._publish_new(p, b'{"a": 1}') is False                 # identical bytes: accepted, nothing replaced
    with pytest.raises(R.ConflictError):
        R._publish_new(p, b'{"a": 2}')
    assert p.read_bytes() == b'{"a": 1}' and not list(tmp_path.glob("*.tmp"))


def test_fl043_a_job_finished_by_another_process_is_not_overwritten(tmp_path, monkeypatch):
    monkeypatch.setattr(R, "truth_job", lambda base, world, n: {"pairs": [], "w2_truth_failures": 0})
    target = tmp_path / "smoke__M1__W1.json"

    def other_process_first(content):
        def run_job(set_name, cand, world, n=None, truth=None, *a, **k):
            target.write_bytes(_dumps(content))                  # the other process publishes first
            return _job("smoke", "M1", "W1", None)
        return run_job
    monkeypatch.setattr(R, "_run_job", other_process_first(dict(_job("smoke", "M1", "W1", None), c_v1="FAIL: other")))
    with pytest.raises(R.ConflictError):
        R.run_jobs(tmp_path, "smoke", ["M1"], worlds=("W1",), provenance={"meta": "m", "meta_sha256": "0" * 64})
    assert json.loads(target.read_bytes())["c_v1"] == "FAIL: other"
    target.unlink()
    same = dict(_job("smoke", "M1", "W1", None), provenance={"meta": "other", "meta_sha256": "1" * 64})
    monkeypatch.setattr(R, "_run_job", other_process_first(same))
    assert R.run_jobs(tmp_path, "smoke", ["M1"], worlds=("W1",), provenance={"meta": "m", "meta_sha256": "0" * 64}) == []
    assert json.loads(target.read_bytes()) == same               # the same result from another invocation is kept


def test_fl043_two_meta_files_written_in_the_same_second_are_both_kept(tmp_path, monkeypatch):
    run = _run()
    monkeypatch.setattr(run.time, "time", lambda: 1795540932.0)
    a = run.write_meta(tmp_path, dict(_meta(run, "smoke"), invocation={"worlds": ["W1"]}))
    monkeypatch.setattr(run.os, "getpid", lambda: 999999)
    b = run.write_meta(tmp_path, dict(_meta(run, "smoke"), invocation={"worlds": ["W2"]}))
    assert a[0] != b[0] and len(list(tmp_path.glob("smoke_meta_*.json"))) == 2


# ---------------- FL-044 (G-01): the guard enforces the FL-035 rules itself ----------------
@pytest.mark.parametrize("case", ["heading only for a longer id", "orphan H3 heading", "scope line inside a list item"])
def test_fl044_guard_refuses_what_the_consistency_rule_refuses(tmp_path, case):
    run = _run()
    commit, tree = T3._approved_repo(tmp_path, run)
    entry = {"id": "OD-TEST-1", "sets": ["eval"], "approved_commit": commit, "approved_tree": tree}
    h = run.scope_sha256(entry)
    dec = {"heading only for a longer id": f"# Decisions\n\n## Founder authorisation OD-TEST-10 — RIP-3 RUN\n"
                                           f"scope sha256: {h}\n",
           "orphan H3 heading": f"# Decisions\n\n## Founder authorisation OD-TEST-1 — RIP-3 RUN\nscope sha256: {h}\n\n"
                                "### Founder authorisation OD-TEST-9 — RIP-3 RUN\n",
           "scope line inside a list item": f"# Decisions\n\n## Founder authorisation OD-TEST-1 — RIP-3 RUN\n"
                                            f"- scope sha256: {h}\n"}[case]
    (tmp_path / "docs/DECISIONS.md").write_text(dec, encoding="utf-8", newline="\n")
    (tmp_path / run.REGISTRY).write_text(json.dumps({"authorisations": [entry]}), encoding="utf-8")
    T3._git(tmp_path, "add", "-A")
    T3._git(tmp_path, "commit", "-q", "-m", "record")
    with pytest.raises(SystemExit):
        run.check_authorisation(tmp_path, "OD-TEST-1", "eval")


def test_fl044_guard_checker_agrees_with_the_fl035_checker_on_all_its_cases(monkeypatch):
    from xauusd_swarm import rip3_auth
    run = _run()
    ref = T3._registry_problems
    seen = []

    def both(registry_text, decisions_text, run_mod):
        expected = ref(registry_text, decisions_text, run_mod)
        assert bool(rip3_auth.registry_problems(registry_text, decisions_text)) == bool(expected)
        seen.append(bool(expected))
        return expected
    monkeypatch.setattr(T3, "_registry_problems", both)
    T3.test_run_authorisation_registry_consistency_check_cases()
    assert len(seen) == 28 and seen.count(False) == 3
    assert run.check_authorisation is rip3_auth.check_authorisation   # the driver uses the library's guard


# ---------------- FL-045 (G-02): the library does not accept a boolean ----------------
def test_fl045_library_refuses_a_boolean_or_an_unrecorded_identifier(tmp_path, no_compute):
    for set_name in ("eval", "confirm"):
        with pytest.raises(R.NotAuthorised):
            R.run_jobs(tmp_path, set_name, ["B-LR"], authorised_run=True)
        with pytest.raises(R.NotAuthorised):
            R.run_job(set_name, "B-LR", "W1", authorised_run=True)
        with pytest.raises(R.NotAuthorised):
            R.run_job(set_name, "B-LR", "W1", None, None, True)            # positional boolean
        with pytest.raises(R.NotAuthorised):
            R.run_jobs(tmp_path, set_name, ["B-LR"], authorisation="OD-UNRECORDED")
    assert not list(tmp_path.iterdir())


def test_fl045_library_checks_the_record_and_a_clean_tree(tmp_path, monkeypatch, no_compute, threads_one):
    from xauusd_swarm import rip3_auth
    monkeypatch.setattr(rip3_auth, "check_authorisation", lambda root, auth_id, set_name: _fake_auth(set_name))
    monkeypatch.setattr(rip3_auth, "tree_clean", lambda root: False)
    with pytest.raises(R.NotAuthorised, match="clean"):
        R.run_jobs(tmp_path, "eval", ["B-LR"], authorisation="OD-TEST-H")
    monkeypatch.setattr(rip3_auth, "tree_clean", lambda root: True)
    with pytest.raises(WouldScore):                 # recorded (faked) and clean: the guard lets it through
        R.run_jobs(tmp_path, "eval", ["B-LR"], authorisation="OD-TEST-H")


# =============== review R1 of rip3/run-hardening and FL-047 (founder decision OD-S9-20) ===============
import errno                                                       # noqa: E402
import inspect                                                     # noqa: E402
import random                                                      # noqa: E402

import numpy as np                                                 # noqa: E402

REG_BASES = (R.SEEDS["eval"], R.SEEDS["confirm"])                  # 6201, 6301
REG_BOOT = [R.SEEDS["eval_bootstrap"] + k for k in range(8)] + [R.SEEDS["confirm_bootstrap"] + k for k in range(8)]


@pytest.fixture
def no_registered_randomness(monkeypatch):
    """Sentinel: creating a random stream seeded from 6201 / 6301 (rip3.stream) or a bootstrap generator seeded from
    6299…6306 / 6399…6406 raises WouldScore, so a missing guard is seen without drawing any registered number."""
    real_random, real_rng = random.Random, np.random.default_rng

    class Guarded(real_random):
        def __init__(self, x=None):
            if isinstance(x, str) and any(x.startswith(f"RIP3|{b}|") for b in REG_BASES):
                raise WouldScore(f"registered stream {x[:20]}…")
            super().__init__(x)

    def guarded_rng(seed=None, *a, **k):
        try:                                       # review R2-3: a sequence seed [n] gives the same stream as n
            vals = [int(v) for v in np.asarray(seed).ravel()] if seed is not None else []
        except (TypeError, ValueError):
            vals = []
        if any(v in REG_BOOT for v in vals):
            raise WouldScore(f"registered bootstrap seed {seed!r}")
        return real_rng(seed, *a, **k)
    monkeypatch.setattr(random, "Random", Guarded)
    monkeypatch.setattr(np.random, "default_rng", guarded_rng)


@pytest.fixture
def small_spec(monkeypatch):
    monkeypatch.setitem(R.SPEC, "dev_per_class", 16)
    monkeypatch.setitem(R.SPEC, "fpc", {"ind": 1, "g4": 1, "g16": 1})
    monkeypatch.setitem(R.SPEC, "util_fpc", 1)


CALLS = {
    "stream": lambda b: R.stream(b, "eval", "W1"),
    "make_family": lambda b: R.make_family(b, "eval", "W1", 1, (0, 0), 0),
    "member_stream": lambda b: R.member_stream({"key": (b, "eval", "W1", "g1", 0, 0, 0)}, 0),
    "eval_families": lambda b: R.eval_families(b, "eval", "W1", 1, 1),
    "utility_pairs": lambda b: R.utility_pairs(b, "W1"),
    "truth_job": lambda b: R.truth_job(b, "W1", 64),
    "utility_job": lambda b: R.utility_job("B-LR", "W1", 64, b, {"pairs": [], "w2_truth_failures": 0}),
    "identity_scenario": lambda b: R.identity_scenario("B-LR", "W1", "ind", b, "eval", 64),
    "gates": lambda b: R.gates({"matrix": [{"world": "W1", "candidate": "B-LR", "scenario": "ind"}]},
                               T3._fake_jobs({("B-LR", "W1"): 1.0}), None,
                               R.SEEDS["eval_bootstrap" if b == 6201 else "confirm_bootstrap"] + 7),
}
# public functions of rip3 that take a base, seed or set name but build no registered data (reason in the comment)
NOT_DATA = {"job_path": "file name only", "load_jobs": "reads files, checked by FL-039"}
GUARDED_ELSEWHERE = {"run_job", "run_jobs", "evaluate",           # tested in test_fl045_* and test_r1_evaluate_*
                     "authorised_scope"}                          # the guard itself: test_fl047_scope_*


@pytest.mark.parametrize("name", sorted(CALLS))
@pytest.mark.parametrize("base", REG_BASES)
def test_fl047_public_functions_refuse_the_registered_seeds(name, base, no_registered_randomness, small_spec):
    with pytest.raises(R.NotAuthorised):
        CALLS[name](base)


def test_fl047_every_public_function_that_takes_a_base_or_set_is_covered():
    found = set()
    for n, o in vars(R).items():
        if n.startswith("_") or not inspect.isfunction(o) or o.__module__ != R.__name__:
            continue
        ps = list(inspect.signature(o).parameters)
        if any("base" in q or "seed" in q or q == "set_name" for q in ps) or n in ("stream", "member_stream"):
            found.add(n)
    assert found == set(CALLS) | set(NOT_DATA) | GUARDED_ELSEWHERE, found ^ (set(CALLS) | set(NOT_DATA) | GUARDED_ELSEWHERE)


def test_fl047_development_and_smoke_seeds_stay_open(no_registered_randomness):
    assert R.stream(R.SEEDS["smoke"], "eval", "W1").random() == random.Random("RIP3|6103|eval|W1").random()
    assert R.make_family(R.SEEDS["dev"], "dev", "W1", 1, (0, 0), 0)["key"][0] == 6101


def test_fl047_partial_reproduction_needs_the_authorisation(tmp_path, no_registered_randomness, small_spec):
    pr = _load("rip3_partial_repro_under_test", ROOT / "scripts" / "rip3_partial_repro.py")
    j = _job("eval", "B-LR", "W1", None)
    j["identity"]["ind"]["pred"]["A6"] = [[0, 0]]
    (tmp_path / "eval__B-LR__W1.json").write_bytes(_dumps(j))
    for set_name in ("eval", "confirm"):
        (tmp_path / f"{set_name}__B-LR__W1.json").write_bytes(_dumps(dict(j, set=set_name)))
        with pytest.raises(R.NotAuthorised):
            pr.main(str(tmp_path), set_name, str(tmp_path / "pr.json"))
        with pytest.raises(R.NotAuthorised):
            pr.main(str(tmp_path), set_name, str(tmp_path / "pr.json"), 3, "OD-UNRECORDED")
    assert not (tmp_path / "pr.json").exists()


def test_fl047_scope_opens_only_after_the_recorded_authorisation(monkeypatch, no_registered_randomness):
    from xauusd_swarm import rip3_auth
    for bad in (True, None, "", "OD-UNRECORDED"):
        with pytest.raises(R.NotAuthorised):
            with R.authorised_scope("eval", bad):
                pass
    calls = []

    def fake_verify(root, auth_id, set_name):
        calls.append((Path(root), auth_id, set_name))
        return _fake_auth(set_name)
    monkeypatch.setattr(rip3_auth, "verify_registered", fake_verify)
    with R.authorised_scope("eval", "OD-TEST-H"):
        with pytest.raises(WouldScore):                            # the scope lets eval through (sentinel, no data)
            R.stream(6201, "eval", "W1")
        with pytest.raises(R.NotAuthorised):                       # but not the other registered set
            R.stream(6301, "confirm", "W1")
    with pytest.raises(R.NotAuthorised):                           # closed again afterwards
        R.stream(6201, "eval", "W1")
    assert calls == [(R.REPO_ROOT, "OD-TEST-H", "eval")]


@pytest.mark.parametrize("set_name", ["eval", "confirm"])
def test_r1_evaluate_refuses_a_registered_set_without_authorisation(set_name, no_registered_randomness):
    vals = {(c, w): ACC[c] for c in CELLS for w in R.WORLDS}
    for kw in ({}, {"authorisation": True}, {"authorisation": "OD-UNRECORDED"}):
        with pytest.raises(R.NotAuthorised):
            R.evaluate(T3._fake_jobs(vals), set_name, None, B=20, **kw)


def test_r1_publish_refuses_without_hard_links(tmp_path, monkeypatch):
    def no_link(src, dst):
        raise OSError(errno.EPERM, "hard links not supported here")
    monkeypatch.setattr(R.os, "link", no_link)
    p = tmp_path / "smoke__X__W1.json"
    with pytest.raises(R.HardLinkUnsupported):
        R._publish_new(p, b'{"a": 1}')
    assert not p.exists() and not list(tmp_path.glob("*.tmp"))


def test_r1_publish_never_replaces_a_file_created_during_the_attempt(tmp_path, monkeypatch):
    p = tmp_path / "smoke__X__W1.json"
    real_link, real_replace = os.link, os.replace

    def link_after_other_process(src, dst):                        # another process publishes first
        Path(dst).write_bytes(b'{"other": 1}')
        return real_link(src, dst)
    monkeypatch.setattr(R.os, "link", link_after_other_process)
    with pytest.raises(R.ConflictError):
        R._publish_new(p, b'{"a": 1}')
    assert p.read_bytes() == b'{"other": 1}'
    p.unlink()

    def no_link(src, dst):
        raise OSError(errno.EPERM, "hard links not supported here")

    def replace_after_other_process(src, dst):                     # the old fallback's window: exists() then replace()
        Path(dst).write_bytes(b'{"other": 2}')
        return real_replace(src, dst)
    monkeypatch.setattr(R.os, "link", no_link)
    monkeypatch.setattr(R.os, "replace", replace_after_other_process)
    with pytest.raises(R.HardLinkUnsupported):
        R._publish_new(p, b'{"a": 1}')
    assert not p.exists() or p.read_bytes() == b'{"other": 2}'
    assert not list(tmp_path.glob("*.tmp"))


def test_r1_publish_uses_its_own_temporary_file(tmp_path, monkeypatch):
    seen, real_link = [], os.link

    def spy(src, dst):
        seen.append(Path(src).name)
        return real_link(src, dst)
    monkeypatch.setattr(R.os, "link", spy)
    R._publish_new(tmp_path / "smoke__X__W1.json", b"{}")
    R._publish_new(tmp_path / "smoke__X__W1.json", b"{}")
    assert len(seen) == 2 and seen[0] != seen[1] and all(s.endswith(".json.tmp") for s in seen)
    assert not list(tmp_path.glob("*.tmp"))


@pytest.mark.parametrize("mode", [["--cands", "B-LR", "--worlds", "W1"], ["--assemble", "--rip2", ""]])
def test_r1_driver_checks_the_output_folder_for_hard_links_before_writing(tmp_path, monkeypatch, no_scoring, mode):
    run = _run()

    def no_link(src, dst):
        raise OSError(errno.EPERM, "hard links not supported here")
    monkeypatch.setattr(os, "link", no_link)
    out = tmp_path / "o"
    with pytest.raises(SystemExit, match="hard link"):
        _main(run, monkeypatch, out, "smoke", *mode)
    assert not list(out.glob("*.json"))


@pytest.mark.parametrize("case", ["job cell not in the invocation", "job world not in the invocation",
                                  "truth world not in the invocation", "meta without invocation"])
def test_r1_provenance_must_name_the_invocation_that_ran_the_file(tmp_path, monkeypatch, case):
    run = _run()
    monkeypatch.setitem(R.SPEC, "B", 200)
    out = tmp_path / "o"
    out.mkdir()
    name, h = _write_meta(out, _meta(run, "smoke"), "1")
    _folder(out, "smoke", CELLS, {"meta": name, "meta_sha256": h})
    if case == "meta without invocation":
        m = _meta(run, "smoke")
        data = json.dumps(m, indent=1).encode("utf-8")
        (out / "smoke_meta_2.json").write_bytes(data)
        target, prov = out / "smoke__M1__W1.json", {"meta": "smoke_meta_2.json", "meta_sha256": _sha(data)}
    else:
        cands, worlds = {"job cell not in the invocation": (["B-LR"], R.WORLDS),
                         "job world not in the invocation": (CELLS, ["W2"]),
                         "truth world not in the invocation": (CELLS, ["W2"])}[case]
        n2, h2 = _write_meta(out, _meta(run, "smoke"), "2", cands, worlds)
        target = out / ("smoke__truth__W1.json" if case.startswith("truth") else "smoke__M1__W1.json")
        prov = {"meta": n2, "meta_sha256": h2}
    j = json.loads(target.read_bytes())
    j["provenance"] = prov
    target.write_bytes(_dumps(j))
    with pytest.raises(SystemExit, match="FL-040"):
        _main(run, monkeypatch, out, "smoke", "--assemble", "--rip2", "")
    assert not (out / "smoke_results.json").exists()


@pytest.mark.parametrize("case", ["tree not clean", "no RIP-2 record", "other RIP-2 hash"])
def test_r1_confirm_checks_the_eval_meta_itself(tmp_path, monkeypatch, no_scoring, case, threads_one):
    run = _run()
    _authorised(run, monkeypatch)
    out, _, _ = _eval_folder(run, tmp_path)
    res = _eval_result(run, out)
    meta = dict(res["meta"])
    if case == "tree not clean":
        meta["tree_clean"] = False
    elif case == "no RIP-2 record":
        meta.pop("rip2")
    else:
        meta["rip2"] = dict(meta["rip2"], sha256="0" * 64)
    _eval_result(run, out, meta=meta)
    with pytest.raises(SystemExit, match="FL-041"):
        _main(run, monkeypatch, out, "confirm", "--authorisation", "OD-TEST-H", "--worlds", "W1")


# =============== review R2 (founder decision OD-S9-21): the form of the base must not open the seeds ===============
class _Text:
    """An object whose text is the base (str(obj) == '6201')."""
    def __init__(self, v):
        self.v = v

    def __str__(self):
        return str(self.v)


def _forms(b):
    return {"text": str(b), "numpy int64": np.int64(b), "numpy int32": np.int32(b), "object with that text": _Text(b),
            "text with a separator": f"{b}|eval"}


BASE_CALLS = {k: v for k, v in CALLS.items() if k != "gates"}


@pytest.mark.parametrize("form", ["text", "numpy int64", "numpy int32", "object with that text", "text with a separator"])
@pytest.mark.parametrize("name", sorted(BASE_CALLS))
@pytest.mark.parametrize("base", REG_BASES)
def test_r2_every_form_of_a_registered_base_is_refused(name, base, form, no_registered_randomness, small_spec):
    with pytest.raises(R.NotAuthorised):
        BASE_CALLS[name](_forms(base)[form])


@pytest.mark.parametrize("base", REG_BASES)
def test_r2_stream_decides_on_the_final_seed_string(base, no_registered_randomness):
    for parts in ((str(base), "eval", "W1"), (f"{base}|eval", "W1"), (f"{base}|eval|W1",), (_Text(f"{base}|x"),)):
        with pytest.raises(R.NotAuthorised):
            R.stream(*parts)
    # the same text elsewhere in the string is not the base and stays open (development set 6101)
    assert R.stream(R.SEEDS["dev"], f"{base}", "W1") is not None


@pytest.mark.parametrize("seed", [[6306], np.array([6306]), (6306,), "6306", 6306.0, True, [6406], np.array([6299, 1])])
def test_r2_gates_accepts_only_an_integer_seed(seed, no_registered_randomness):
    with pytest.raises((R.NotAuthorised, TypeError)):
        R.gates({"matrix": [{"world": "W1", "candidate": "B-LR", "scenario": "ind"}]},
                T3._fake_jobs({("B-LR", "W1"): 1.0}), None, seed)


def test_r2_gates_still_runs_on_a_development_seed(no_registered_randomness, monkeypatch):
    monkeypatch.setitem(R.SPEC, "B", 20)
    jobs = T3._fake_jobs({(c, w): ACC[c] for c in CELLS for w in R.WORLDS})
    out = R.evaluate(jobs, "smoke", None, B=20)                     # a complete smoke evaluation (seed 6193)
    g = R.gates(out, jobs, None, np.int64(R.SEEDS["smoke"] + 97))   # a NumPy integer seed is accepted
    assert "C-V2" in g


def test_r2_every_generator_of_rip3_is_created_at_a_guarded_point():
    """Structural control for the re-check of every public path (OD-S9-21 point 4): in rip3.py a random generator is
    created only in stream (guarded on the final seed string), in _evaluate (seed computed inside, guarded) and in
    gates (integer seed, guarded). A new place that creates a generator fails this test until it is reviewed."""
    import ast
    tree = ast.parse((ROOT / "src/xauusd_swarm/rip3.py").read_text(encoding="utf-8"))
    where = []
    for fn in [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]:
        for node in ast.walk(fn):
            if isinstance(node, ast.Call):
                name = ast.unparse(node.func)
                if name in ("random.Random", "np.random.default_rng", "np.random.RandomState", "np.random.seed",
                            "random.seed", "np.random.SeedSequence", "np.random.Generator"):
                    where.append((fn.name, name))
    assert sorted(where) == [("_evaluate", "np.random.default_rng"), ("gates", "np.random.default_rng"),
                             ("stream", "random.Random")], where


# =============== FL-048 (founder decision OD-S9-22): git output is UTF-8 whatever the system encoding ===============
import subprocess                                                  # noqa: E402

GUARD_TESTS = ["test_run_authorisation_guard_needs_a_recorded_matching_decision",
               "test_run_authorisation_guard_accepts_an_unchanged_recorded_scope",
               "test_run_authorisation_guard_refuses_a_scope_widened_after_recording",
               "test_run_authorisation_guard_refuses_an_edited_decision_or_bad_sets_or_code",
               "test_run_authorisation_guard_needs_entry_and_decision_in_the_same_commit",
               "test_run_authorisation_guard_refuses_a_decision_recorded_before_its_entry",
               "test_run_authorisation_guard_accepts_entry_and_decision_added_together"]


@pytest.fixture
def windows_default_encoding(monkeypatch):
    """What a Windows runner does: text-mode subprocess output with no explicit encoding is decoded as cp1252
    (simulated on every platform); an explicit encoding is left as given. Returns the list of git calls seen."""
    real = subprocess.run
    seen = []

    def run(args, *a, **k):
        if k.get("text") or k.get("universal_newlines"):
            if "encoding" not in k:
                k = dict(k, encoding="cp1252", errors="strict")
        if isinstance(args, (list, tuple)) and args and args[0] == "git":
            seen.append({"args": list(args), "encoding": k.get("encoding"), "errors": k.get("errors")})
        return real(args, *a, **k)
    monkeypatch.setattr(subprocess, "run", run)
    return seen


@pytest.mark.parametrize("name", GUARD_TESTS)
def test_fl048_guard_tests_pass_with_a_cp1252_default(name, tmp_path, windows_default_encoding):
    getattr(T3, name)(tmp_path)                                    # the seven tests that failed on Windows CI


def test_fl048_git_output_keeps_the_em_dash(tmp_path, windows_default_encoding):
    from xauusd_swarm import rip3_auth
    heading = "## Founder authorisation OD-TEST-1 — RIP-3 RUN"
    (tmp_path / "d.md").write_bytes((heading + "\n").encode("utf-8"))
    T3._git(tmp_path, "init", "-q")
    T3._git(tmp_path, "add", "-A")
    T3._git(tmp_path, "commit", "-q", "-m", "d")
    rc, out = rip3_auth._git(tmp_path, "show", "HEAD:d.md")
    assert rc == 0 and out == heading
    assert rip3_auth.run_headings([out]) == [(0, "OD-TEST-1")]


def test_fl048_every_git_call_of_the_guard_and_the_meta_decodes_utf8_strictly(tmp_path, windows_default_encoding):
    from xauusd_swarm import rip3_auth
    run = _run()
    rip3_auth._git(ROOT, "rev-parse", "HEAD")                       # path 1: rip3_auth._git
    run.meta("smoke", None)                                         # paths 2 and 3: rev-parse HEAD and status in meta()
    calls = [c for c in windows_default_encoding if c["args"][:2] in (["git", "rev-parse"], ["git", "status"])]
    assert [c["args"][1] for c in calls] == ["rev-parse", "rev-parse", "status"]
    assert all(c["encoding"] == "utf-8" and c["errors"] == "strict" for c in calls), calls


# =============== documentation batch (OD-S9-23): two deferred test improvements ===============
GEN_NAMES = {"Random", "SystemRandom", "default_rng", "RandomState", "SeedSequence", "Generator", "BitGenerator",
             "PCG64", "PCG64DXSM", "MT19937", "Philox", "SFC64"}
GEN_ALLOWED_IN = ("stream", "_evaluate", "gates")
GEN_ROOTS = {"random", "np.random", "numpy.random"}        # the only module paths a generator may be called through
FORBIDDEN_CALLS = {"getattr", "vars", "globals", "locals", "eval", "exec", "compile", "__import__", "setattr",
                   "delattr"}
FORBIDDEN_NAMES = {"importlib", "__builtins__", "builtins"}
# review R3 of the documentation batch: the ONLY import statements allowed in rip3.py, exactly as written there
# (kind, module, level, name, asname); any other import, or the same one under another name, is refused
ALLOWED_IMPORTS = {
    ("from", "__future__", 0, "annotations", None),
    ("import", None, 0, "contextlib", None), ("import", None, 0, "contextvars", None),
    ("import", None, 0, "hashlib", None), ("import", None, 0, "json", None), ("import", None, 0, "math", None),
    ("import", None, 0, "os", None), ("import", None, 0, "random", None),
    ("from", "pathlib", 0, "Path", None), ("from", "statistics", 0, "NormalDist", None),
    ("import", None, 0, "numpy", "np"),
    ("from", None, 1, "reid", None), ("from", None, 1, "rip1_attack", "A"), ("from", None, 1, "rip2", None),
    ("from", None, 1, "rip3_auth", None),                  # the authorisation checker, imported inside _guard
}


def _generator_violations(source):
    """ALLOW-LIST structural check of where random generators can be created (documentation batch, review R2; founder
    decision OD-S9-23 addendum). Allowed, and nothing else:
      A. each of stream, _evaluate, gates defined exactly once (present, not twice), at the top level, as a plain
         function, and never rebound anywhere (no second definition, nested or method definition, assignment, parameter, global/nonlocal,
         import or class of that name);
      B. the random modules (random, np.random / numpy.random) used only as `<module>.<public name>`; a generator name
         only as a DIRECT call `<module>.<generator>(…)` whose innermost scope (function, lambda or class) is one of
         the three definitions of rule A AND which lies inside a statement of that function's BODY (review R4: not in
         a parameter default, keyword-only default, decorator or annotation, which run when the module is loaded;
         review R5: not inside a generator expression, which runs later when consumed; and none of the three bodies
         may contain yield or await, which would defer the whole body); any other use of a module or a generator (stored, passed, getattr, vars,
         __dict__, subscript, aliases by import or assignment) is refused;
      C. none of getattr, vars, globals, locals, eval, exec, compile, __import__, setattr, delattr, importlib,
         builtins or sys.modules appears at all;
      D. (review R3) only the import statements of ALLOWED_IMPORTS, exactly as written in rip3.py (same module,
         names and aliases); any other import, or one under another name, is refused, so modules such as sys,
         importlib or builtins cannot be reached under any name.
    Limit: a static check cannot be complete against deliberate evasion; it stops such code from entering by mistake.
    What keeps the registered seeds closed at run time is the guard of FL-047 (rip3.stream / _require_open).
    Returns sorted (kind, line, text); kind "creation" marks the line where a generator would be made."""
    import ast
    tree = ast.parse(source)
    parent = {}
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            parent[child] = node
    bad = []
    # ---- rule D (review R3): only the allow-listed import statements, exactly
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            items = [("import", None, 0, a.name, a.asname) for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            items = [("from", node.module, node.level, a.name, a.asname) for a in node.names]
        else:
            continue
        for it in items:
            if it not in ALLOWED_IMPORTS:
                bad.append(("import", node.lineno, ast.unparse(node)))
    # ---- rule A
    firsts = {}
    for n in tree.body:
        if isinstance(n, ast.FunctionDef) and n.name in GEN_ALLOWED_IN and n.name not in firsts:
            firsts[n.name] = n
    allowed = set(firsts.values())
    for nm in GEN_ALLOWED_IN:                               # review R3: each must exist (exactly once: see below)
        if nm not in firsts:
            bad.append(("missing", 0, nm))
    for fn in allowed:                                      # review R5: yield / await would defer the whole body
        for node in ast.walk(fn):
            if isinstance(node, (ast.Yield, ast.YieldFrom, ast.Await)):
                inner, cur = None, node
                while cur in parent and cur is not fn:
                    cur = parent[cur]
                    if isinstance(cur, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)) and cur is not fn:
                        inner = cur
                        break
                if inner is None:
                    bad.append(("deferred body", node.lineno, fn.name))
    for node in ast.walk(tree):
        names = []
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node not in allowed:
            names = [node.name]
        elif isinstance(node, ast.Name) and isinstance(node.ctx, (ast.Store, ast.Del)):
            names = [node.id]
        elif isinstance(node, (ast.Global, ast.Nonlocal)):
            names = list(node.names)
        elif isinstance(node, ast.arg):
            names = [node.arg]
        elif isinstance(node, ast.alias):
            names = [node.asname or node.name.split(".")[0]]
        elif isinstance(node, ast.ExceptHandler) and node.name:
            names = [node.name]
        for nm in names:
            if nm in GEN_ALLOWED_IN:
                bad.append(("rebinding", getattr(node, "lineno", getattr(parent.get(node), "lineno", 0)), nm))
    # review R5: a generator expression runs when it is consumed, later: it is a scope of its own, like a lambda
    scopes = (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef, ast.GeneratorExp)

    def in_body_of(node, fn):
        """review R4: True only if node lies inside a STATEMENT of fn's body. Parameter defaults (positional and
        keyword-only), decorators and annotations belong to the definition and run when the module is loaded."""
        cur = node
        while cur in parent:
            up = parent[cur]
            if up is fn:
                return cur in fn.body
            cur = up
        return False

    def scope_of(node):
        while node in parent:
            node = parent[node]
            if isinstance(node, scopes):
                return node
        return None

    annotations = set()                                     # type annotations name a class, they create nothing
    for node in ast.walk(tree):
        roots = []
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.returns is not None:
            roots.append(node.returns)
        if isinstance(node, ast.arg) and node.annotation is not None:
            roots.append(node.annotation)
        if isinstance(node, ast.AnnAssign):
            roots.append(node.annotation)
        for r in roots:
            annotations.update(ast.walk(r))
    # ---- aliases (any alias is itself a violation; tracking them marks the line that would create a generator)
    gen_alias, mod_alias = set(), set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            for a in node.names:
                if mod in ("random", "numpy.random") or (mod == "numpy" and a.name == "random"):
                    bad.append(("import", node.lineno, ast.unparse(node)))
                    (mod_alias if a.name == "random" else gen_alias).add(a.asname or a.name)
        elif isinstance(node, ast.Import):
            for a in node.names:
                if (a.name == "random" and a.asname not in (None, "random")) or a.name == "numpy.random":
                    bad.append(("import", node.lineno, ast.unparse(node)))
                    mod_alias.add(a.asname or a.name)

    def is_module(n):
        return isinstance(n, ast.expr) and (ast.unparse(n) in GEN_ROOTS or (isinstance(n, ast.Name)
                                                                             and n.id in mod_alias))

    def is_gen_ref(n):
        return ((isinstance(n, ast.Attribute) and n.attr in GEN_NAMES)
                or (isinstance(n, ast.Name) and (n.id in GEN_NAMES or n.id in gen_alias)))

    changed = True
    while changed:
        changed = False
        for node in ast.walk(tree):
            targets, value = [], None
            if isinstance(node, ast.Assign):
                targets, value = node.targets, node.value
            elif isinstance(node, (ast.AnnAssign, ast.AugAssign, ast.NamedExpr)) and node.value is not None:
                targets, value = [node.target], node.value
            if value is None:
                continue
            if is_module(value):
                kind_set = mod_alias
            elif any((is_gen_ref(v) and not (isinstance(parent.get(v), ast.Call) and parent[v].func is v))
                     or (is_module(v) and not isinstance(parent.get(v), ast.Attribute)) for v in ast.walk(value)):
                kind_set = gen_alias
            else:
                continue
            for t in targets:
                for n in ast.walk(t):
                    if isinstance(n, ast.Name) and n.id not in kind_set:
                        kind_set.add(n.id)
                        changed = True

    def made_here(node):
        """True if the expression ends up CALLED: climbing through attribute access, subscripts and calls of the
        forbidden introspection functions (getattr(m, n)(…), vars(m)[n](…), m.__dict__[n](…)) reaches a call whose
        function is the climbed expression."""
        cur = node
        while cur in parent:
            up = parent[cur]
            if isinstance(up, ast.Call) and up.func is cur:
                return True
            if (isinstance(up, ast.Call) and cur in up.args and isinstance(up.func, ast.Name)
                    and up.func.id in FORBIDDEN_CALLS) or (isinstance(up, (ast.Subscript, ast.Attribute))
                                                            and up.value is cur):
                cur = up
                continue
            return False
        return False

    # ---- rules B and C
    for node in ast.walk(tree):
        up = parent.get(node)
        if node in annotations and not (isinstance(up, ast.Call) and up.func is node):
            continue                                        # a type named in an annotation creates nothing

        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in FORBIDDEN_CALLS:
            bad.append(("creation" if made_here(node.func) and isinstance(parent.get(node), ast.Call) else "forbidden",
                        node.lineno, node.func.id))
        elif isinstance(node, ast.Name) and (node.id in FORBIDDEN_NAMES or node.id in FORBIDDEN_CALLS):
            if not (isinstance(up, ast.Call) and up.func is node):
                bad.append(("forbidden", node.lineno, node.id))
        elif isinstance(node, ast.Attribute) and ast.unparse(node) == "sys.modules":
            bad.append(("forbidden", node.lineno, "sys.modules"))
        if is_module(node):                                  # rule B for the modules themselves
            if not isinstance(up, ast.Attribute) or up.value is not node or up.attr.startswith("_"):
                bad.append(("creation" if made_here(node) else "module use", node.lineno, ast.unparse(node)))
            continue
        direct = isinstance(up, ast.Call) and up.func is node
        if isinstance(node, ast.Attribute) and node.attr in GEN_NAMES:
            sc = scope_of(node)
            ok = direct and ast.unparse(node.value) in GEN_ROOTS and sc in allowed and in_body_of(node, sc)
            if not ok:
                bad.append(("creation" if direct else "reference", node.lineno, ast.unparse(node)))
        elif isinstance(node, ast.Name) and (node.id in GEN_NAMES or node.id in gen_alias):
            if isinstance(node.ctx, ast.Load):
                bad.append(("creation" if direct else "reference", node.lineno, node.id))
    return sorted(set(bad), key=lambda x: (x[1], x[0], x[2]))


def test_dc_rip3_creates_generators_only_at_the_guarded_points_even_through_aliases():
    src = (ROOT / "src/xauusd_swarm/rip3.py").read_text(encoding="utf-8")
    assert _generator_violations(src) == []


ALIAS_CASES = [   # (source, line where a generator would be created)
    ("from random import Random as Q\ndef f():\n    return Q(1)\n", 3),
    ("import random as rnd\ndef f():\n    return rnd.Random(1)\n", 3),
    ("import numpy as np\nG = np.random.default_rng\ndef f():\n    return G(6299)\n", 4),
    ("import numpy as np\ndef f():\n    return getattr(np.random, 'default_rng')(6299)\n", 3),
    ("from numpy.random import default_rng\ndef f():\n    return default_rng(6299)\n", 3),
    ("import numpy.random as npr\ndef f():\n    return npr.Generator(npr.PCG64(6299))\n", 3),
    ("import random\nR = random.Random\ndef stream(*p):\n    return R('x')\n", 4),
    # review R1 of the documentation batch
    ("import numpy as np\ndef evil():\n    def stream():\n        return np.random.default_rng(6299)\n"
     "    return stream()\n", 4),
    ("import numpy as np\ndef stream():\n    global R\n    R = np.random.default_rng\n    return R(1)\n"
     "def evil():\n    return R(6299)\n", 7),
    # similar cases
    ("import numpy as np\ndef stream():\n    return lambda: np.random.default_rng(6299)\n", 3),
    ("import numpy as np\nclass C:\n    def stream(self):\n        return np.random.default_rng(6299)\n", 4),
    ("import numpy as np\nimport functools\ndef stream():\n    return functools.partial(np.random.default_rng, 6299)\n", 4,
     "reference"),     # the partial object creates the generator wherever it is called: the escape point is flagged
    ("from numpy import random as nr\ndef f():\n    return nr.default_rng(6299)\n", 3),
    ("import numpy as np\ndef gates(o, j, r, s):\n    g = np.random\n    return g.default_rng(s)\n", 4),
    ("import numpy as np\ndef stream():\n    rng = (R := np.random.default_rng)\n    return rng\ndef f():\n"
     "    return R(6299)\n", 6),
    # review R2 of the documentation batch
    ("import random\nimport numpy as np\ndef stream(*p):\n    return random.Random('x')\n"
     "def stream():\n    return np.random.default_rng(6299)\n", 6),
    ("import numpy as np\ndef f():\n    name = 'default_rng'\n    return getattr(np.random, name)(6299)\n", 4),
    # similar cases
    ("import numpy as np\ndef f():\n    return vars(np.random)['default_rng'](6299)\n", 3),
    ("import numpy as np\ndef f():\n    return np.random.__dict__['default_rng'](6299)\n", 3),
    ("import importlib\ndef f():\n    return importlib.import_module('numpy.random').default_rng(6299)\n", 3,
     "forbidden"),
    ("import sys\ndef f():\n    return sys.modules['numpy.random'].default_rng(6299)\n", 3, "forbidden"),
    ("def f():\n    exec('import numpy as np; r = np.random.default_rng(6299)')\n", 2, "forbidden"),
    ("import numpy as np\ndef f(stream):\n    return stream\n", 2, "rebinding"),
    ("import numpy as np\ndef gates(o, j, r, s):\n    return np.random.default_rng(s)\ngates = None\n", 4,
     "rebinding"),
    ("import numpy as np\ndef f():\n    m = np\n    return m.random.default_rng(6299)\n", 4),
    # review R3 of the documentation batch
    ("import importlib as il\n", 1, "import"),
    ("import sys as s\nx = s.modules\n", 1, "import"),
    ("from sys import modules as m\n", 1, "import"),
    # similar cases
    ("import builtins as b\ndef f():\n    return b.__import__('numpy').random.default_rng(6299)\n", 1, "import"),
    ("from os import system as s\n", 1, "import"),
    ("import os as o\n", 1, "import"),
    ("from numpy import random\n", 1, "import"),
    ("from . import rip3_auth as ra\n", 1, "import"),
    ("def f():\n    import importlib\n    return importlib\n", 2, "import"),
    # review R4 of the documentation batch: expressions of the definition run when the module is loaded
    ("import numpy as np\ndef stream(rng=np.random.default_rng(6201)):\n    return rng\n"
     "def _evaluate(x):\n    return np.random.default_rng(2)\ndef gates(*a):\n    return np.random.default_rng(3)\n", 2),
    ("import numpy as np\ndef stream(*p, rng=np.random.default_rng(6201)):\n    return rng\n", 2),
    ("import numpy as np\ndef _evaluate(j, rng=np.random.default_rng(6299)):\n    return rng\n", 2),
    ("import numpy as np\ndef gates(o, j, r, s=np.random.default_rng(6306)):\n    return s\n", 2),
    ("import numpy as np\ndef keep(x):\n    return x\n@keep(np.random.default_rng(6201))\ndef stream(*p):\n"
     "    return p\n", 4),
    ("import numpy as np\ndef stream(*p) -> np.random.default_rng(6201):\n    return p\n", 2),
    ("import numpy as np\ndef stream(rng: np.random.default_rng(6201) = None):\n    return rng\n", 2),
    ("import numpy as np\nclass C:\n    rng = np.random.default_rng(6201)\n", 3),
    ("import numpy as np\nRNG = np.random.default_rng(6201)\n", 2),
    # review R5 of the documentation batch: deferred execution inside the body
    ("import numpy as np\ndef stream(*args):\n    return (np.random.default_rng(6201) for _ in range(1))\n"
     "def _evaluate(x):\n    return x\ndef gates(*args):\n    return None\n", 3),
    ("import numpy as np\ndef _evaluate(j):\n    return (np.random.default_rng(6299) for k in j)\n", 3),
    ("import numpy as np\ndef gates(o, j, r, s):\n    g = sum(np.random.default_rng(s).random() for _ in range(2))\n"
     "    return g\n", 3),
    ("import numpy as np\ndef stream(*p):\n    yield np.random.default_rng(6201)\n", 3, "deferred body"),
    ("import numpy as np\ndef _evaluate(j):\n    yield from [1]\n    return np.random.default_rng(1)\n", 3,
     "deferred body"),
]


@pytest.mark.parametrize("missing", list(GEN_ALLOWED_IN))
def test_dc_the_structural_check_needs_each_guarded_function_exactly_once(missing):
    defs = {"stream": "def stream(*p):\n    return random.Random('x')\n",
            "_evaluate": "def _evaluate(j):\n    return np.random.default_rng(1)\n",
            "gates": "def gates(o, j, r, s):\n    return np.random.default_rng(s)\n"}
    head = "import random\nimport numpy as np\n"
    complete = head + "".join(defs.values())
    assert _generator_violations(complete) == []
    without = head + "".join(v for k, v in defs.items() if k != missing)
    assert ("missing", 0, missing) in _generator_violations(without)
    twice = complete + defs[missing]
    assert any(k == "rebinding" and t == missing for k, _, t in _generator_violations(twice))


@pytest.mark.parametrize("case", ALIAS_CASES, ids=[f"case{i}" for i in range(len(ALIAS_CASES))])
def test_dc_the_structural_check_finds_the_line_that_creates_a_generator(case):
    snippet, line, kind = (case + ("creation",))[:3]
    found = _generator_violations(snippet)
    assert (kind, line) in {(k, ln) for k, ln, _ in found}, found


def test_dc_immediate_comprehensions_in_the_three_bodies_stay_accepted():
    ok = ("import random\nimport numpy as np\n"
          "def stream(*p):\n    return random.Random('|'.join([str(x) for x in p]))\n"
          "def _evaluate(j):\n    return [np.random.default_rng(k) for k in j]\n"
          "def gates(o, j, r, s):\n    g = {k: np.random.default_rng(s + k) for k in range(2)}\n"
          "    return {np.random.default_rng(s).integers(9) for _ in range(1)} | set(g)\n")
    assert _generator_violations(ok) == []


def test_dc_generators_in_the_bodies_of_the_three_functions_stay_accepted():
    ok = ("import random\nimport numpy as np\n"
          "def stream(*p, tag='x'):\n    s = '|'.join(map(str, p))\n    return random.Random('RIP3|' + s)\n"
          "def _evaluate(j, B=None):\n    out = []\n    for k in j:\n        if k:\n"
          "            out.append(np.random.default_rng(k))\n    return out\n"
          "def gates(o, j, r, s: int = 0) -> dict:\n    try:\n        g = np.random.default_rng(s)\n"
          "    finally:\n        pass\n    return {'g': g}\n")
    assert _generator_violations(ok) == []


def test_dc_the_structural_check_accepts_the_three_guarded_points():
    ok = ("import random\nimport numpy as np\n"
          "def stream(*p):\n    return random.Random('x')\n"
          "def _evaluate(j):\n    for w in j:\n        rng = np.random.default_rng(1)\n    return rng\n"
          "def gates(o, j, r, s):\n    return np.random.default_rng(s)\n"
          "def member_stream(fam, m) -> random.Random:\n    return stream(fam, m)\n")   # an annotation only
    assert _generator_violations(ok) == []


@pytest.mark.parametrize("value", [True, False, np.bool_(True)])
def test_dc_gates_refuses_a_boolean_seed_by_its_type(value, no_registered_randomness):
    with pytest.raises(TypeError, match="must be an integer"):
        R.gates({"matrix": []}, {}, None, value)


@pytest.mark.parametrize("value", [True, False])
def test_dc_the_guard_refuses_a_boolean_authorisation_by_its_type(value, tmp_path, no_compute):
    with pytest.raises(R.NotAuthorised, match="a boolean is not an authorisation"):
        R.run_jobs(tmp_path, "eval", ["B-LR"], authorisation=value)
    with pytest.raises(R.NotAuthorised, match="a boolean is not an authorisation"):
        with R.authorised_scope("confirm", value):
            pass
    assert R._registered_set_of(value) is None and R._registered_set_of(True) != "eval"


# =============== FL-049 (founder decision OD-S9-24): the protocol's thread settings ===============
# Every test below sets or removes all three variables itself, so the result does not depend on the environment the
# suite runs in. Registered paths are reached only with the scoring sentinels (no_scoring / no_compute) in place.
THREADS = ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS")
BAD_VALUES = [None, "2", "", " 1", "1 ", "01"]                       # None: the variable is missing


def _set_threads(monkeypatch, values):
    for k in THREADS:
        if values.get(k) is None:
            monkeypatch.delenv(k, raising=False)
        else:
            monkeypatch.setenv(k, values[k])


def _ones(**over):
    return dict({k: "1" for k in THREADS}, **over)


@pytest.fixture
def threads_one(monkeypatch):
    """The three thread variables set to "1" as protocol §2 requires (set before the driver module is loaded)."""
    _set_threads(monkeypatch, _ones())


def _state(p):
    """Everything in a folder (recursively): relative path -> sha256 of the bytes, or 'dir'. None if it is absent."""
    p = Path(p)
    if not p.exists():
        return None
    return {str(q.relative_to(p)): ("dir" if q.is_dir() else _sha(q.read_bytes())) for q in sorted(p.rglob("*"))}


def test_fl049_driver_and_library_name_the_same_three_variables():
    from xauusd_swarm import rip3_auth
    run = _run()
    assert run.THREAD_VARS == rip3_auth.THREAD_VARS == THREADS
    assert "thread_env" in run.ENV_KEYS and "thread_env" in run.EVAL_ENV_KEYS


def test_fl049_meta_records_the_values_the_process_had_when_the_driver_was_loaded(monkeypatch):
    _set_threads(monkeypatch, {"OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "4"})        # MKL missing
    run = _run()
    want = {"OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "4", "MKL_NUM_THREADS": None}
    assert run.meta("smoke", None)["thread_env"] == want
    _set_threads(monkeypatch, _ones())                                  # changed after loading: not what is recorded
    assert run.meta("smoke", None)["thread_env"] == want


def test_fl049_the_values_are_taken_before_numpy_or_the_library_is_imported():
    """Structural: in scripts/rip3_run.py the snapshot of the three variables is taken by a top-level statement that
    comes before every import of numpy or xauusd_swarm (OpenBLAS reads its variable when numpy is loaded), and the
    only imports before it are standard-library modules that do not import numpy."""
    import ast
    tree = ast.parse((ROOT / "scripts" / "rip3_run.py").read_text(encoding="utf-8"))
    body = tree.body
    snap = [i for i, s in enumerate(body) if isinstance(s, ast.Assign)
            and any(isinstance(t, ast.Name) and t.id == "THREAD_ENV_AT_START" for t in s.targets)]
    assert len(snap) == 1

    def modules(s):
        if isinstance(s, ast.Import):
            return [a.name.split(".")[0] for a in s.names]
        if isinstance(s, ast.ImportFrom):
            return [(s.module or "").split(".")[0]]
        return []
    later = [i for i, s in enumerate(body) for m in modules(s) if m in ("numpy", "xauusd_swarm")]
    assert later and snap[0] < min(later)
    stdlib = {"argparse", "hashlib", "json", "os", "platform", "subprocess", "sys", "time", "datetime", "pathlib"}
    assert {m for s in body[:snap[0]] for m in modules(s)} <= stdlib


@pytest.mark.parametrize("value", BAD_VALUES)
@pytest.mark.parametrize("var", THREADS)
@pytest.mark.parametrize("set_name", ["eval", "confirm"])
def test_fl049_registered_run_is_refused_unless_each_value_is_exactly_one(tmp_path, monkeypatch, no_scoring,
                                                                          set_name, var, value):
    _set_threads(monkeypatch, _ones(**{var: value}))
    run = _run()
    _authorised(run, monkeypatch)
    out = tmp_path / "o"
    out.mkdir()
    (out / "keep.txt").write_bytes(b"x")
    before = _state(tmp_path)
    with pytest.raises(SystemExit, match="FL-049"):
        _main(run, monkeypatch, out, set_name, "--authorisation", "OD-TEST-H", "--cands", "B-LR", "--worlds", "W1")
    assert _state(tmp_path) == before                               # nothing written, not even a meta file
    absent = tmp_path / "absent"
    with pytest.raises(SystemExit, match="FL-049"):
        _main(run, monkeypatch, absent, set_name, "--authorisation", "OD-TEST-H", "--cands", "B-LR", "--worlds", "W1")
    assert not absent.exists()                                      # refused before the output folder is created


@pytest.mark.parametrize("value", BAD_VALUES)
@pytest.mark.parametrize("var", THREADS)
def test_fl049_registered_assembly_is_refused_unless_each_value_is_exactly_one(tmp_path, monkeypatch, no_scoring,
                                                                               var, value):
    _set_threads(monkeypatch, _ones())
    run = _run()
    _authorised(run, monkeypatch)
    out, _, _ = _eval_folder(run, tmp_path)
    _eval_result(run, out)                                           # a complete eval folder with an eval result
    _set_threads(monkeypatch, _ones(**{var: value}))
    run = _run()                                                     # a new process with the wrong value
    _authorised(run, monkeypatch)
    before = _state(tmp_path)
    for args in (("eval", "--assemble"), ("confirm", "--assemble")):
        with pytest.raises(SystemExit, match="FL-049"):
            _main(run, monkeypatch, out, args[0], "--authorisation", "OD-TEST-H", *args[1:])
        assert _state(tmp_path) == before


@pytest.mark.parametrize("var", THREADS)
def test_fl049_a_value_changed_after_the_driver_was_loaded_is_refused(tmp_path, monkeypatch, no_scoring, var):
    _set_threads(monkeypatch, _ones())
    run = _run()
    _authorised(run, monkeypatch)
    out = tmp_path / "o"
    out.mkdir()
    before = _state(tmp_path)
    for value in ("2", None):
        _set_threads(monkeypatch, _ones(**{var: value}))
        with pytest.raises(SystemExit, match="FL-049"):
            _main(run, monkeypatch, out, "eval", "--authorisation", "OD-TEST-H", "--cands", "B-LR", "--worlds", "W1")
        assert _state(tmp_path) == before


def test_fl049_registered_run_with_all_values_one_reaches_the_scoring_sentinel(tmp_path, monkeypatch, no_scoring):
    _set_threads(monkeypatch, _ones())
    run = _run()
    _authorised(run, monkeypatch)
    with pytest.raises(WouldScore):                 # every check passed; the sentinel stands in for run_jobs
        _main(run, monkeypatch, tmp_path / "o", "eval", "--authorisation", "OD-TEST-H", "--cands", "B-LR",
              "--worlds", "W1")
    metas = list((tmp_path / "o").glob("eval_meta_*.json"))
    assert len(metas) == 1 and json.loads(metas[0].read_bytes())["thread_env"] == _ones()


def test_fl049_smoke_is_not_refused_and_records_the_values(tmp_path, monkeypatch):
    _set_threads(monkeypatch, {})                                    # all three missing
    run = _run()
    monkeypatch.setitem(R.SPEC, "B", 200)
    out, _, _ = _smoke_folder(run, tmp_path)
    _main(run, monkeypatch, out, "smoke", "--assemble", "--rip2", "")
    res = json.loads((out / "smoke_results.json").read_bytes())
    assert res["meta"]["thread_env"] == {k: None for k in THREADS}


@pytest.mark.parametrize("other", [{"OMP_NUM_THREADS": "4"}, {"MKL_NUM_THREADS": None}])
def test_fl049_meta_files_that_differ_in_the_values_are_not_mixed(tmp_path, monkeypatch, other):
    _set_threads(monkeypatch, _ones())
    run = _run()
    monkeypatch.setitem(R.SPEC, "B", 200)
    out, name, h = _smoke_folder(run, tmp_path)
    n2, h2 = _write_meta(out, _meta(run, "smoke", thread_env=_ones(**other)), "2")
    p = out / "smoke__M1__W2.json"
    p.write_bytes(_dumps(dict(json.loads(p.read_bytes()), provenance={"meta": n2, "meta_sha256": h2})))
    with pytest.raises(SystemExit, match="FL-040.*thread_env"):
        _main(run, monkeypatch, out, "smoke", "--assemble", "--rip2", "")
    assert not (out / "smoke_results.json").exists()


@pytest.mark.parametrize("other", [{"OPENBLAS_NUM_THREADS": "8"}, {"OMP_NUM_THREADS": None}])
def test_fl049_confirm_refuses_an_eval_result_with_other_values(tmp_path, monkeypatch, no_scoring, threads_one, other):
    run = _run()
    _authorised(run, monkeypatch)
    out, _, _ = _eval_folder(run, tmp_path)
    res = _eval_result(run, out)
    _eval_result(run, out, meta=dict(res["meta"], thread_env=_ones(**other)))
    before = _state(tmp_path)
    with pytest.raises(SystemExit, match="FL-041.*thread_env"):
        _main(run, monkeypatch, out, "confirm", "--authorisation", "OD-TEST-H", "--worlds", "W1")
    assert _state(tmp_path) == before


@pytest.mark.parametrize("value", [None, "2", " 1"])
@pytest.mark.parametrize("var", THREADS)
def test_fl049_library_refuses_a_registered_set_even_with_a_recorded_authorisation(tmp_path, monkeypatch, no_compute,
                                                                                   no_registered_randomness, var, value):
    from xauusd_swarm import rip3_auth
    monkeypatch.setattr(rip3_auth, "check_authorisation", lambda root, auth_id, set_name: _fake_auth(set_name))
    monkeypatch.setattr(rip3_auth, "tree_clean", lambda root: True)
    _set_threads(monkeypatch, _ones(**{var: value}))
    pr = _load("rip3_partial_repro_fl049", ROOT / "scripts" / "rip3_partial_repro.py")
    j = _job("eval", "B-LR", "W1", None)
    j["identity"]["ind"]["pred"]["A6"] = [[0, 0]]
    vals = {(c, w): ACC[c] for c in CELLS for w in R.WORLDS}
    for set_name in ("eval", "confirm"):
        (tmp_path / f"{set_name}__B-LR__W1.json").write_bytes(_dumps(dict(j, set=set_name)))
        before = _state(tmp_path)
        with pytest.raises(R.NotAuthorised, match="FL-049"):
            R.run_jobs(tmp_path / "out", set_name, ["B-LR"], authorisation="OD-TEST-H")
        with pytest.raises(R.NotAuthorised, match="FL-049"):
            R.run_job(set_name, "B-LR", "W1", authorisation="OD-TEST-H")
        with pytest.raises(R.NotAuthorised, match="FL-049"):
            R.evaluate(T3._fake_jobs(vals), set_name, None, B=20, authorisation="OD-TEST-H")
        with pytest.raises(R.NotAuthorised, match="FL-049"):
            with R.authorised_scope(set_name, "OD-TEST-H"):
                pass
        with pytest.raises(R.NotAuthorised, match="FL-049"):
            pr.main(str(tmp_path), set_name, str(tmp_path / "pr.json"), 1, "OD-TEST-H")
        assert _state(tmp_path) == before


def test_fl049_library_lets_a_recorded_authorisation_through_when_all_values_are_one(tmp_path, monkeypatch, no_compute):
    from xauusd_swarm import rip3_auth
    monkeypatch.setattr(rip3_auth, "check_authorisation", lambda root, auth_id, set_name: _fake_auth(set_name))
    monkeypatch.setattr(rip3_auth, "tree_clean", lambda root: True)
    _set_threads(monkeypatch, _ones())
    with pytest.raises(WouldScore):                 # recorded (faked), clean, values "1": the guard lets it through
        R.run_jobs(tmp_path, "eval", ["B-LR"], authorisation="OD-TEST-H")


@pytest.mark.parametrize("env", ["missing", "one"])
def test_fl049_the_command_line_refuses_before_anything_else_when_a_value_is_wrong(tmp_path, env):
    """A real process (no test doubles): with the variables missing the registered set is refused by FL-049 and the
    output folder is unchanged; with all three "1" the same command reaches the authorisation check instead."""
    import subprocess
    e = {k: v for k, v in os.environ.items() if k not in THREADS}
    if env == "one":
        e.update(_ones())
    out = tmp_path / "o"
    out.mkdir()
    before = _state(tmp_path)
    p = subprocess.run([sys.executable, str(ROOT / "scripts/rip3_run.py"), str(out), "eval"], capture_output=True,
                       text=True, env=e)
    msg = p.stderr + p.stdout
    assert p.returncode != 0
    if env == "missing":
        assert "FL-049" in msg
    else:
        assert "FL-049" not in msg and "authorisation" in msg
    assert _state(tmp_path) == before


# =============== batch after FL-049 (founder decision OD-S9-25): audit items A-6, B-5, C-7, T7 and await ===============
def _eval_meta(run, **over):
    return _meta(run, "eval", "OD-TEST-H", _fake_auth("eval"), **over)


# ---- B-5: the normal resumed folder (several invocations of the same environment) is assembled ----
@pytest.mark.parametrize("split", ["by world", "by cell"])
def test_b5_a_folder_written_by_two_invocations_of_the_same_environment_is_assembled(tmp_path, monkeypatch, split):
    run = _run()
    monkeypatch.setitem(R.SPEC, "B", 200)
    out = tmp_path / "o"
    out.mkdir()
    parts = ([(CELLS, ["W1"]), (CELLS, ["W2"])] if split == "by world"
             else [(CELLS[:1], list(R.WORLDS)), (CELLS[1:], list(R.WORLDS))])
    metas = {}
    for tag, (cells, worlds) in enumerate(parts, 1):
        name, h = _write_meta(out, _meta(run, "smoke"), str(tag), cells, worlds)
        metas[name] = h
        _folder(out, "smoke", cells, {"meta": name, "meta_sha256": h}, truth=False, worlds=worlds)
    _main(run, monkeypatch, out, "smoke", "--assemble", "--rip2", "")
    res = json.loads((out / "smoke_results.json").read_bytes())
    assert res["run_meta_sha256"] == metas and len(metas) == 2
    assert set(res["jobs_sha256"]) == {f"smoke__{c}__{w}.json" for c in CELLS for w in R.WORLDS}
    for p in out.glob("smoke__*.json"):
        cand, world = run._file_cell(p.name, "smoke")
        inv = json.loads((out / json.loads(p.read_bytes())["provenance"]["meta"]).read_bytes())["invocation"]
        assert cand in inv["cands"] and world in inv["worlds"]


def test_b5_a_registered_folder_written_by_one_invocation_per_world_passes_every_check(tmp_path, monkeypatch,
                                                                                       no_scoring, threads_one):
    run = _run()
    _authorised(run, monkeypatch)
    out = tmp_path / "o"
    out.mkdir()
    for tag, w in enumerate(R.WORLDS, 1):
        name, h = _write_meta(out, _eval_meta(run), str(tag), R.ALL_CELLS, [w])
        _folder(out, "eval", R.ALL_CELLS, {"meta": name, "meta_sha256": h}, worlds=[w])
    assert len(list(out.glob("eval_meta_*.json"))) == 2
    with pytest.raises(WouldScore):                 # every check passed; the sentinel stands in for evaluate
        _main(run, monkeypatch, out, "eval", "--authorisation", "OD-TEST-H", "--assemble")


# ---- C-7: the two refusals of check_provenance that had no test ----
def test_c7_a_registered_meta_written_from_an_unclean_tree_is_refused(tmp_path, monkeypatch, no_scoring, threads_one):
    run = _run()
    _authorised(run, monkeypatch)
    out = tmp_path / "o"
    out.mkdir()
    name, h = _write_meta(out, _eval_meta(run, tree_clean=False), "1")
    _folder(out, "eval", R.ALL_CELLS, {"meta": name, "meta_sha256": h})
    before = _state(tmp_path)
    with pytest.raises(SystemExit, match="FL-040: meta file .* not clean"):
        _main(run, monkeypatch, out, "eval", "--authorisation", "OD-TEST-H", "--assemble")
    assert _state(tmp_path) == before


@pytest.mark.parametrize("case", ["other authorisation identifier", "other approved commit in the scope",
                                  "other recording commit in the scope", "no authorisation check"])
def test_c7_meta_files_that_differ_in_the_authorisation_or_its_scope_are_not_mixed(tmp_path, monkeypatch, no_scoring,
                                                                                   threads_one, case):
    run = _run()
    _authorised(run, monkeypatch)
    out, name, h = _eval_folder(run, tmp_path)
    over = {"other authorisation identifier": {"authorisation": "OD-TEST-OTHER"},
            "other approved commit in the scope": {"authorisation_check": _fake_auth("eval", approved_commit="f" * 40)},
            "other recording commit in the scope": {"authorisation_check": _fake_auth("eval", recorded_in="9" * 40)},
            "no authorisation check": {"authorisation_check": None}}[case]
    n2, h2 = _write_meta(out, _eval_meta(run, **over), "2", ["M1"], ["W1"])
    p = out / "eval__M1__W1.json"
    p.write_bytes(_dumps(dict(json.loads(p.read_bytes()), provenance={"meta": n2, "meta_sha256": h2})))
    before = _state(tmp_path)
    with pytest.raises(SystemExit, match=r"FL-040: meta file .* differs .*authorisation"):
        _main(run, monkeypatch, out, "eval", "--authorisation", "OD-TEST-H", "--assemble")
    assert _state(tmp_path) == before


# ---- T7: the library's thread check with a real recorded authorisation in a real git repository (no test doubles) ----
def test_t7_verify_registered_on_a_real_recorded_authorisation_checks_the_thread_values(tmp_path, monkeypatch):
    from xauusd_swarm import rip3_auth
    run = _run()
    commit, tree = T3._approved_repo(tmp_path, run)
    entry = {"id": "OD-TEST-1", "sets": ["eval", "confirm"], "approved_commit": commit, "approved_tree": tree}
    T3._record(tmp_path, run, entry)
    assert rip3_auth.tree_clean(tmp_path)
    for set_name in ("eval", "confirm"):
        for bad in ({}, _ones(OMP_NUM_THREADS="2"), _ones(MKL_NUM_THREADS=None), _ones(OPENBLAS_NUM_THREADS=" 1")):
            _set_threads(monkeypatch, bad)
            with pytest.raises(rip3_auth.AuthorisationError, match="FL-049"):
                rip3_auth.verify_registered(tmp_path, "OD-TEST-1", set_name)
        _set_threads(monkeypatch, _ones())
        ok = rip3_auth.verify_registered(tmp_path, "OD-TEST-1", set_name)
        assert (ok["id"], ok["set"], ok["approved_commit"], ok["approved_tree"]) == ("OD-TEST-1", set_name, commit, tree)
        assert ok["recorded_in"] == T3._git(tmp_path, "rev-parse", "HEAD")
    _set_threads(monkeypatch, _ones())
    with pytest.raises(rip3_auth.AuthorisationError, match="not recorded"):     # the record is still required
        rip3_auth.verify_registered(tmp_path, "OD-TEST-2", "eval")
    (tmp_path / "untracked.txt").write_text("x")
    with pytest.raises(rip3_auth.AuthorisationError, match="not clean"):        # and a clean tree
        rip3_auth.verify_registered(tmp_path, "OD-TEST-1", "eval")


# ---- await: refused in the bodies of the three guarded functions; async definitions are not accepted ----
@pytest.mark.parametrize("fn", sorted(GEN_ALLOWED_IN))
def test_dc_await_in_the_body_of_a_guarded_function_is_refused(fn):
    defs = {"stream": "def stream(*p):\n    return random.Random('x')\n",
            "_evaluate": "def _evaluate(j):\n    return np.random.default_rng(1)\n",
            "gates": "def gates(o, j, r, s):\n    return np.random.default_rng(s)\n"}
    defs[fn] = defs[fn].replace("    return", "    await p\n    return", 1)
    src = "import random\nimport numpy as np\n" + "".join(defs[k] for k in ("stream", "_evaluate", "gates"))
    line = src.splitlines().index("    await p") + 1
    assert ("deferred body", line, fn) in _generator_violations(src)


@pytest.mark.parametrize("fn", sorted(GEN_ALLOWED_IN))
def test_dc_an_async_definition_of_a_guarded_function_is_not_accepted(fn):
    defs = {"stream": "def stream(*p):\n    return random.Random('x')\n",
            "_evaluate": "def _evaluate(j):\n    return np.random.default_rng(1)\n",
            "gates": "def gates(o, j, r, s):\n    return np.random.default_rng(s)\n"}
    defs[fn] = "async " + defs[fn]
    src = "import random\nimport numpy as np\n" + "".join(defs[k] for k in ("stream", "_evaluate", "gates"))
    assert _generator_violations(src) != []


# ---- A-6: the state between the result and its hash file (documented, not repaired: build notes «Known limits») ----
def test_a6_a_result_without_its_hash_file_blocks_reassembly_and_confirm(tmp_path, monkeypatch, no_scoring,
                                                                         threads_one):
    run = _run()
    monkeypatch.setitem(R.SPEC, "B", 200)
    out, _, _ = _smoke_folder(run, tmp_path)
    (out / "smoke_results.json").write_bytes(b"{}")                     # the process stopped between the two files
    with pytest.raises(SystemExit, match="FL-038"):
        _main(run, monkeypatch, out, "smoke", "--assemble", "--rip2", "")
    _authorised(run, monkeypatch)
    out2 = tmp_path / "e"
    out2.mkdir()
    (out2 / "eval_results.json").write_bytes(b"{}")
    with pytest.raises(SystemExit, match="eval_results.sha256"):
        _main(run, monkeypatch, out2, "confirm", "--authorisation", "OD-TEST-H", "--worlds", "W1")
