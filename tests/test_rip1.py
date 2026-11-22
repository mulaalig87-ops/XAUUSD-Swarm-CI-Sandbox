"""RIP-1 (re-ID through Custody/Vault): derivation checks with known parameters, isolation order, ledger scan,
A5 rule, and (heavy) the reproduction of the committed run. SYNTHETIC ONLY."""
import json
import math
import os
import random
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from xauusd_swarm import reid
from xauusd_swarm import rip1_attack as A

ROOT = Path(__file__).resolve().parents[1]
RES = Path(os.environ.get("RIP1_RES", ROOT / "docs" / "results" / "rip1"))


def _path(asset, period=1, seed=1, n=512):
    rnd = random.Random(seed)
    return reid.simulate(asset, period, n, rnd), A.draw(asset, rnd)


# ---------------- A6 derivations from the actual transforms (review R2-01) ----------------
@pytest.mark.parametrize("asset", range(4))
def test_inversions_with_known_parameters(asset):
    P, prm = _path(asset)
    r = np.diff(np.log(P))
    x = np.array(A.blind("affine_level", P, asset, prm))            # x = a·P + b (representations.affine_level)
    assert np.max(abs(np.diff(np.log(x - prm["b"])) - r)) < 1e-12   # r = ln((x_t − b)/(x_{t−1} − b)); a cancels
    x = np.array(A.blind("tick_grid", P, asset, prm))               # x = (P − c)/Δ
    assert np.max(abs(np.diff(np.log(prm["c"] + reid.ASSETS[asset]["tick"] * x)) - r)) < 1e-12
    x = np.array(A.blind("volatility_time", P, asset, prm))
    assert np.max(abs(np.diff(x) - r ** 2)) < 1e-15
    x = np.array(A.blind("level_residual", P, asset, prm))          # x_t − x_{t−1} ≡ ΔP_t (mod m)
    w = (np.diff(x) - np.diff(P)) / prm["m"]
    assert np.max(abs(w - np.round(w))) < 1e-9
    assert A.blind("activity_time", P, asset, prm) == A.blind("log_returns", P, asset, prm)


@pytest.mark.parametrize("rep", A.REPS)
def test_a6_true_class_has_finite_likelihood(rep):
    P, prm = _path(2, period=3, seed=7)
    sc = A.a6_scores(rep, [A.blind(rep, P, 2, prm)])
    assert math.isfinite(sc[(2, 3)])


def test_affine_group_closed_form_matches_numerical_integral():
    # ∫ (1/6) Π_k N(w_k − u; 0, s²) du over u ∈ [−3, 3], closed form used in _affine_grid
    s, w = 0.01, np.array([0.31, 0.305, 0.318])
    u = np.linspace(-3, 3, 600001)
    dens = np.prod([np.exp(-0.5 * ((wk - u) / s) ** 2) / (s * math.sqrt(2 * math.pi)) for wk in w], axis=0) / 6
    num = math.log(np.trapezoid(dens, u))
    g, wb = len(w), float(np.mean(w))
    closed = (-math.log(6) - 0.5 * g * math.log(2 * math.pi * s ** 2) - float(np.sum((w - wb) ** 2)) / (2 * s ** 2)
              + 0.5 * math.log(2 * math.pi * s ** 2 / g)
              + A._log_phi_diff((-3 - wb) * math.sqrt(g) / s, (3 - wb) * math.sqrt(g) / s))
    assert closed == pytest.approx(num, abs=1e-6)


def test_a6_v1_delta_excludes_inconsistent_classes():
    P, prm = _path(1)
    sc = A.a6_scores("log_returns", [A.blind("log_returns", P, 1, prm)], delta_seen=reid.ASSETS[1]["tick"])
    assert all(sc[c] == -math.inf for c in A.CLASSES if reid.ASSETS[c[0]]["tick"] != reid.ASSETS[1]["tick"])


# ---------------- A5 ----------------
def test_a5_learns_a_class_dependent_field_and_ignores_random_ones():
    rows = [{"st.delta": reid.ASSETS[a]["tick"], "st.nonce": os.urandom(8).hex()} for a, p in A.CLASSES for _ in range(3)]
    labs = [c for c in A.CLASSES for _ in range(3)]
    m = A.nb_model(rows, labs, ["st.delta"])
    assert A.argmax(m({"st.delta": 0.001}))[0] == 1
    m2 = A.nb_model(rows, labs, ["st.nonce"])
    assert A.argmax(m2({"st.nonce": "unseen"})) == A.CLASSES[0]      # unseen value carries no information


# ---------------- isolation order and ledger scan ----------------
def test_sandbox_order_namespaces_then_drop_then_python():
    from xauusd_swarm.rip1 import sandbox_argv
    argv = sandbox_argv(uid=999, gid=999, hide=["/home", "/srv/rip1/custody"], script="/c/s.py",
                        args=["/c", "/r/in", "/r/out", "V0"])
    assert argv[:7] == ["unshare", "--net", "--mount", "--pid", "--fork", "--mount-proc", "--"]
    inner = argv[-1]
    i_mount, i_setpriv, i_py = inner.index("mount -t tmpfs"), inner.index("exec setpriv"), inner.index(" -I ")
    assert i_mount < i_setpriv < i_py
    for flag in ("--reuid=999", "--regid=999", "--clear-groups", "--no-new-privs", "--inh-caps=-all",
                 "--bounding-set=-all", "env -i PATH="):
        assert flag in inner


def test_ledger_scan_finds_a_planted_secret_of_every_kind():
    from xauusd_swarm.rip1 import scan_ledger
    st = json.dumps({"action": "params_fixed", "family": "f", "delta": 0.01}).encode().hex()
    line = json.dumps({"payload": {"statement_hex": st}, "note": f"{123.456789012345!r} 9f3a1c 18446744073709551557"}).encode()
    assert scan_ledger(line, {"c": [0.5]}, [0.01])["pass"] is True
    r = scan_ledger(line, {"c": [123.456789012345], "salt": ["9f3a1c"], "seed": [18446744073709551557]}, [0.01])
    assert r["hits"] == {"c": 1, "salt": 1, "seed": 1} and r["pass"] is False
    r = scan_ledger(line, {"m": [0.01]}, [0.01])                    # m equal to a public Δ: excluded, reported
    assert r["excluded_equal_to_public"] == {"m": 1} and r["pass"] is True
    st2 = json.dumps({"action": "x", "c": 1}).encode().hex()
    assert scan_ledger(json.dumps({"payload": {"statement_hex": st2}}).encode(), {}, [])["forbidden_statement_keys"] == ["c"]


@pytest.mark.heavy
@pytest.mark.skipif(not (sys.platform.startswith("linux") and hasattr(os, "geteuid") and os.geteuid() == 0
                         and shutil.which("unshare") and shutil.which("setpriv")),
                    reason="isolation probes need root, unshare and setpriv (the run host); skipped elsewhere")
def test_isolation_probes_pass_inside_the_sandbox(tmp_path):
    from xauusd_swarm import rip1
    pw = rip1.ensure_user()
    base = Path("/srv/rip1_probe")
    if base.exists():
        shutil.rmtree(base)
    cust, code, ind, outd = base / "custody", base / "code", base / "run" / "in", base / "run" / "out"
    for d in (cust, code / "xauusd_swarm", ind, outd):
        d.mkdir(parents=True)
    (cust / "vault.bin").write_bytes(b"secret")
    (ind / "data.npz").write_bytes(b"x")
    os.chmod(base, 0o711)
    os.chmod(cust, 0o700)
    for f in rip1.PKG_FILES:
        shutil.copy(ROOT / "src" / "xauusd_swarm" / f, code / "xauusd_swarm" / f)
    (code / "xauusd_swarm" / "__init__.py").write_text("")
    (code / "p.py").write_text("import sys, json; sys.path.insert(0, sys.argv[1])\n"
                               "from xauusd_swarm import rip1_attack as A\n"
                               f"print(json.dumps(A.probes({[str(cust), str(cust / 'vault.bin'), '/home', '/root', '/tmp']!r}, "
                               "in_dir=sys.argv[2], out_dir=sys.argv[3])))\n")
    rip1._readonly_tree(code)
    rip1._readonly_tree(ind)
    os.chmod(base / "run", 0o755)
    os.chown(outd, pw.pw_uid, pw.pw_gid)
    os.chmod(outd, 0o700)
    argv = rip1.sandbox_argv(uid=pw.pw_uid, gid=pw.pw_gid, hide=rip1.HIDE + [str(cust)], script=str(code / "p.py"),
                             args=[str(code), str(ind), str(outd), "V0"])
    out = subprocess.run(argv, capture_output=True, text=True, stdin=subprocess.DEVNULL)
    shutil.rmtree(base)
    pr = json.loads(out.stdout)
    assert pr["all_pass"], {k: pr[k] for k in pr["checks"] if pr[k] is not True}
    assert pr["inputs_read_only"] and pr["no_writable_dir_outside_out"]


# ---------------- reproduction of the committed run ----------------
@pytest.mark.heavy
def test_rip1_reproduces_committed_result(tmp_path):
    if not (RES / "results.json").exists():
        pytest.skip("RIP-1 not run yet (pre-registration commit)")
    import gzip
    import hashlib
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    from xauusd_swarm.custody import _sha
    res = json.loads((RES / "results.json").read_text(encoding="utf-8"))
    for name, h in res["files_sha256"].items():                   # every committed file is the one recorded
        assert hashlib.sha256((RES / name).read_bytes()).hexdigest() == h
    truths = json.loads((RES / "revealed_truth.json").read_text())
    led = gzip.open(RES / "ledger_final.jsonl.gz").read()
    assert led.startswith(gzip.open(RES / "ledger.jsonl.gz").read())   # V1 snapshot is a prefix of the final ledger
    recs = [json.loads(l) for l in led.decode().splitlines()]
    revealed = {}
    for r in recs:                                                  # truth hashes bound in the ledger
        if r["kind"] == "access_logged":
            st = json.loads(bytes.fromhex(r["payload"]["statement_hex"]))
            if st["outcome"] == "ok":
                revealed[st["item"][6:]] = st["returned"]
    assert set(revealed) == set(truths)
    assert all(revealed[f] == "sha256:" + _sha(t) for f, t in truths.items())
    sub_blob = (RES / "submission_records.json").read_bytes()
    seals = {json.loads(bytes.fromhex(r["payload"]["statement_hex"]))["submissions_sha256"]
             for r in recs if r["kind"] == "submissions_sealed"}
    assert seals == {hashlib.sha256(sub_blob).hexdigest()} == {res["submissions_sha256"]}
    pub = Ed25519PublicKey.from_public_bytes(bytes.fromhex(res["reid_checker_public_key"]))
    dev = json.loads((RES / "dev_labels.json").read_text())
    for rid, sr in json.loads(sub_blob).items():
        pub.verify(bytes.fromhex(sr["signature_hex"]),
                   json.dumps(sr["record"], sort_keys=True, separators=(",", ":")).encode())
        pf = RES / f"predictions_{rid}.json"
        assert hashlib.sha256(pf.read_bytes()).hexdigest() == sr["record"]["predictions_sha256"]
        view, rep = rid.split("_", 1)
        body = json.loads(pf.read_text())
        preds, ins = A.predict(str(RES), view, {"spec": res["spec"], "rep": rep, "dev_labels": dev[rep]})
        assert ins == body["inputs_sha256"] and preds == body["predictions"]
        z = np.load(RES / f"data_{rep}.npz")
        from xauusd_swarm.rip1 import validate_predictions
        validate_predictions(body, rep=rep, view=view, fams={sc: [str(f) for f in z[f"F_{sc}"]] for sc in A.SCEN},
                             inputs_sha256=sr["record"]["inputs_sha256"])          # R5: complete attacker set


# ---------------- review R4: attacker-side code holds no signing capability ----------------
def test_attacker_side_code_imports_no_signing_or_custody_module():
    import ast
    from xauusd_swarm.rip1 import PKG_FILES
    files = [ROOT / "src" / "xauusd_swarm" / f for f in PKG_FILES] + [ROOT / "scripts" / "rip1_attacker.py"]
    for f in files:
        for node in ast.walk(ast.parse(f.read_text(encoding="utf-8"))):
            names = [a.name for a in node.names] if isinstance(node, ast.Import) else \
                [node.module or ""] if isinstance(node, ast.ImportFrom) else []
            for n in names:
                assert not n.startswith("cryptography"), (f.name, n)
                assert not any(x in n for x in ("identity", "custody", "ledger", "charter")), (f.name, n)
    assert "identity.py" not in PKG_FILES and "custody.py" not in PKG_FILES


def test_read_output_rejects_links_extra_files_and_oversize(tmp_path):
    from xauusd_swarm.rip1 import read_output
    d = tmp_path / "out"
    d.mkdir()
    (d / "predictions.json").write_text("{}")
    assert read_output(str(d))[0] == {}
    (d / "extra").write_text("x")
    with pytest.raises(RuntimeError, match="only predictions.json"):
        read_output(str(d))
    (d / "extra").unlink()
    with pytest.raises(RuntimeError, match="too large"):
        read_output(str(d), max_bytes=1)
    (d / "predictions.json").unlink()
    (tmp_path / "real.json").write_text("{}")
    if hasattr(os, "symlink"):
        try:
            os.symlink(tmp_path / "real.json", d / "predictions.json")
        except OSError:
            pytest.skip("symlinks not permitted on this host")
        with pytest.raises(RuntimeError, match="plain regular file"):
            read_output(str(d))


def _good_output(view, rep):
    fams = {sc: [f"f{sc}1", f"f{sc}2"] for sc in A.SCEN}
    obj = {"view": view, "rep": rep, "probes": {"all_pass": True}, "inputs_sha256": {f"data_{rep}.npz": "h"},
           "predictions": {sc: {att: {f: [1, 2] for f in fams[sc]} for att in A.expected_attackers(view, sc, rep)}
                           for sc in A.SCEN}}
    return obj, fams, {f"data_{rep}.npz": "h", "input.json": "i"}


def test_validate_predictions_rejects_self_signature_and_foreign_families():
    from xauusd_swarm.rip1 import validate_predictions
    good, fams, ins = _good_output("V0", "log_returns")
    validate_predictions(good, rep="log_returns", view="V0", fams=fams, inputs_sha256=ins)
    sc0 = "ind"

    def with_pred(fn):
        o = json.loads(json.dumps(good))
        fn(o["predictions"][sc0]["A6"])
        return o
    for bad in ({**good, "signature_hex": "00"},
                with_pred(lambda d: d.update({"other": [1, 2]})),
                with_pred(lambda d: d.pop("find1")),
                with_pred(lambda d: d.update({"find1": [9, 2]})),
                with_pred(lambda d: d.update({"find1": [True, 2]})),
                {**good, "probes": {"all_pass": False}}):
        with pytest.raises(RuntimeError):
            validate_predictions(bad, rep="log_returns", view="V0", fams=fams, inputs_sha256=ins)


# ---------------- review R5: the attacker set must be complete and exactly the frozen one ----------------
def test_expected_attackers_are_frozen_and_complete():
    assert A.expected_attackers("V0", "ind", "tick_grid") == {"A1_knn_features", "A2_centroid_features",
                                                               "A3_series_match", "A6"}
    assert A.expected_attackers("V0", "g4", "tick_grid") == A.expected_attackers("V0", "g16", "affine_level") == \
        {"A4a", "A4b", "A6"}
    v1 = A.expected_attackers("V1", "g16", "level_residual")
    assert {"A5-delta", "A5-all", "A5-comb", "A6-V1"} <= v1
    assert {x for x in v1 if x.startswith("A5-f:")} == {f"A5-f:{f}" for f in A.LEDGER_FIELDS if f != "st.delta"}
    for bad in (("V2", "ind", "tick_grid"), ("V0", "g8", "tick_grid"), ("V0", "ind", "activity_time")):
        with pytest.raises(ValueError):
            A.expected_attackers(*bad)


@pytest.mark.parametrize("view", ["V0", "V1"])
@pytest.mark.parametrize("rep", A.REPS)
def test_validate_refuses_each_missing_attacker_and_any_unregistered_name(view, rep):
    from xauusd_swarm.rip1 import validate_predictions
    good, fams, ins = _good_output(view, rep)
    validate_predictions(good, rep=rep, view=view, fams=fams, inputs_sha256=ins)
    for sc in A.SCEN:
        for att in A.expected_attackers(view, sc, rep):            # deleting ANY registered attacker is refused
            o = json.loads(json.dumps(good))
            del o["predictions"][sc][att]
            with pytest.raises(RuntimeError, match="missing"):
                validate_predictions(o, rep=rep, view=view, fams=fams, inputs_sha256=ins)
        for extra in ("A5-f:entry.bogus", "A5-f:st.delta", "A7", "A4a" if sc == "ind" else "A1_knn_features"):
            o = json.loads(json.dumps(good))
            o["predictions"][sc][extra] = o["predictions"][sc][next(iter(o["predictions"][sc]))]
            with pytest.raises(RuntimeError, match="unexpected"):
                validate_predictions(o, rep=rep, view=view, fams=fams, inputs_sha256=ins)


def test_validate_refuses_renamed_missing_or_extra_scenarios_and_groups():
    from xauusd_swarm.rip1 import validate_predictions
    good, fams, ins = _good_output("V1", "affine_level")
    for change in (lambda p: p.update({"g8": p.pop("g16")}),      # renamed scenario
                   lambda p: p.pop("g4"),                           # missing scenario
                   lambda p: p.update({"g32": p["g16"]}),           # extra scenario
                   lambda p: p.update({"ind": p["g4"]})):           # groups of another scenario
        o = json.loads(json.dumps(good))
        change(o["predictions"])
        with pytest.raises(RuntimeError):
            validate_predictions(o, rep="affine_level", view="V1", fams=fams, inputs_sha256=ins)
    with pytest.raises(RuntimeError):                               # wrong view or representation
        validate_predictions(good, rep="tick_grid", view="V1", fams=fams, inputs_sha256=ins)


def test_frozen_ledger_field_list_matches_what_custody_writes(tmp_path):
    import uuid
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from xauusd_swarm.charter import Governance
    from xauusd_swarm.custody import CustodyLayer, Vault
    from xauusd_swarm.identity import public_hex, sign
    from xauusd_swarm.ledger import AnchorStore, Ledger
    (tmp_path / "v").mkdir()
    (tmp_path / "l").mkdir()
    (tmp_path / "a").mkdir()
    vault = Vault(tmp_path / "v" / "vault.bin", os.urandom(32))
    FK, CK = Ed25519PrivateKey.generate(), Ed25519PrivateKey.generate()
    F = lambda a, **kw: sign("founder", FK, {"action": a, "nonce": uuid.uuid4().hex, **kw})   # noqa: E731
    cl = CustodyLayer(vault, identity="cust", key=CK)
    led = Ledger(tmp_path / "l" / "ledger.jsonl", anchors=AnchorStore(tmp_path / "a" / "a.jsonl"))
    g = Governance(FK.public_key(), led, extensions=[cl])
    g.register_key(F("register_key", identity="cust", public_key_hex=public_hex(CK.public_key())))
    cl.commit("role_assigned", F("assign_role", role="custody", holder="cust"))
    fam = str(uuid.uuid4())
    com = vault.set_params(fam, **A.draw(0, random.Random(1)))
    cl.commit("params_fixed", sign("cust", CK, {"action": "params_fixed", "nonce": uuid.uuid4().hex, "family": fam,
                                                 "params_commitment": com, "delta": reid.ASSETS[0]["tick"]}))
    recs = [json.loads(line) for line in (tmp_path / "l" / "ledger.jsonl").read_text().splitlines()]
    assert set(A.ledger_fields(recs)[fam]) == set(A.LEDGER_FIELDS)


# ---------------- review R4: real break-out attempts inside the sandbox (run host only) ----------------
ROOT_HOST = (sys.platform.startswith("linux") and hasattr(os, "geteuid") and os.geteuid() == 0
             and shutil.which("unshare") and shutil.which("setpriv"))


@pytest.mark.heavy
@pytest.mark.skipif(not ROOT_HOST, reason="needs root, unshare and setpriv (the run host); skipped elsewhere")
def test_adversarial_attacker_cannot_break_isolation():
    import hashlib
    import time
    from xauusd_swarm import rip1
    pw = rip1.ensure_user()
    base = Path("/srv/rip1_evil")
    if base.exists():
        shutil.rmtree(base)
    cust = base / "custody"
    cust.mkdir(parents=True)
    os.chmod(base, 0o711)
    os.chmod(cust, 0o700)
    (cust / "vault.bin").write_bytes(b"vault-secret")
    (cust / "chk_key.hex").write_text("00" * 32)                    # a planted key file the attacker must not read
    code = rip1._prepare_code(base)
    shutil.copy(ROOT / "tests" / "helpers" / "rip1_evil_attacker.py", code / "evil.py")
    os.chmod(code / "evil.py", 0o644)
    data = base / "data.npz"
    data.write_bytes(os.urandom(4096))
    cust_sha = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in cust.iterdir()}
    markers = ["/tmp", "/var/tmp", "/dev/shm", "/run/lock", "/", "/usr", "/etc", str(base)]
    results, done = {}, []
    for rid, future in (("V0_evil", "V1_evil"), ("V1_evil", None)):
        tg = {"data_name": "data_x.npz", "prior_run": done[-1] if done else None,
              "future_run": str(base / "runs" / future) if future else str(base / "runs" / "never"),
              "runs_dir": str(base / "runs"), "vault": str(cust / "vault.bin"), "custody": str(cust),
              "key_file": str(cust / "chk_key.hex"), "base": str(base)}
        fx = rip1.sandbox_run(base=base, rid=rid, view=rid[:2], code=code, script=str(code / "evil.py"),
                              files={"data_x.npz": data}, input_obj={"targets": tg}, hide_extra=[str(cust)] + done, pw=pw)
        assert fx["returncode"] == 0, fx["stderr_tail"]
        assert fx["inputs_unchanged"] and fx["leftover_processes"] == []
        out = Path(fx["out_dir"])
        with pytest.raises(RuntimeError):                          # links / extra files / self-signature refused
            o, _ = rip1.read_output(str(out))
            rip1.validate_predictions(o, rep="x", view=rid[:2], fams={}, inputs_sha256=fx["inputs_sha256"])
        rep = json.loads((out / "predictions.json").read_text())
        h0 = hashlib.sha256((out / "predictions.json").read_bytes()).hexdigest()
        time.sleep(4)                                              # the background tamperer was killed with the namespace
        assert hashlib.sha256((out / "predictions.json").read_bytes()).hexdigest() == h0
        # creating a symlink INSIDE the writable output dir is possible by design; it must not give access
        # (read_via_symlink denied) and the orchestrator refuses any link in the output (read_output above)
        assert rep["attempts"]["symlink_to_vault"].startswith("ALLOWED")
        assert rep["attempts"]["read_via_symlink"] == "denied"
        allowed = {k: v for k, v in rep["attempts"].items() if v != "denied" and k != "symlink_to_vault"}
        assert allowed == {}, allowed
        assert rep["uid"] == pw.pw_uid
        results[rid] = rep["attempts"]
        done.append(str(base / "runs" / rid))
    assert {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in cust.iterdir()} == cust_sha
    for m in markers:
        assert not Path(m, "rip1_evil_marker").exists(), m
    assert not (base / "runs" / "planted").exists()
    first = base / "runs" / "V0_evil" / "out" / "predictions.json"
    assert json.loads(first.read_text())["attempts"] == results["V0_evil"]    # V1 did not touch V0's output
    shutil.rmtree(base)


@pytest.mark.heavy
@pytest.mark.skipif(not ROOT_HOST, reason="needs root (sandboxed protocol reproduction); CI runs the direct recomputation")
def test_rip1_protocol_reproduces_in_fresh_sandboxes():
    if not (RES / "results.json").exists():
        pytest.skip("RIP-1 not run yet")
    from xauusd_swarm import rip1
    rep = rip1.reproduce_in_sandbox(RES, base=Path("/srv/rip1_repro"))
    assert rep == {f"{v}_{r}": "identical" for v in ("V0", "V1") for r in A.REPS}


@pytest.mark.heavy
@pytest.mark.skipif(not ROOT_HOST, reason="needs root (sandboxed protocol reproduction)")
def test_rip1_protocol_reproduction_fails_on_an_altered_result(tmp_path):
    if not (RES / "results.json").exists():
        pytest.skip("RIP-1 not run yet")
    from xauusd_swarm import rip1
    alt = tmp_path / "res"
    shutil.copytree(RES, alt)
    p = alt / "predictions_V0_log_returns.json"
    o = json.loads(p.read_text())
    sc = next(iter(o["predictions"]))
    att = next(iter(o["predictions"][sc]))
    fam = next(iter(o["predictions"][sc][att]))
    a, b = o["predictions"][sc][att][fam]
    o["predictions"][sc][att][fam] = [(a + 1) % reid.K, b]
    p.write_text(json.dumps(o, sort_keys=True))
    with pytest.raises(RuntimeError, match="predictions differ"):
        rip1.reproduce_in_sandbox(alt, base=Path("/srv/rip1_repro"))


# ---------------- audit R1 (RIP-1 result) ----------------
def test_independent_rescore_matches_every_result_row():
    if not (RES / "results.json").exists():
        pytest.skip("RIP-1 not run yet")
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "rip1_rescore.py"), str(RES)], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "mismatches: 0" in r.stdout


def test_reproduction_attestation_is_complete_and_bound_to_the_original():
    p = ROOT / "docs" / "results" / "RIP-1_repro_attestation.json"
    if not p.exists() or RES != ROOT / "docs" / "results" / "rip1":
        pytest.skip("no attestation for this result directory")
    import hashlib
    att = json.loads(p.read_text())
    recs = json.loads((RES / "submission_records.json").read_text())
    assert att["all_identical"] is True
    assert [r["run"] for r in att["runs"]] == [f"{v}_{x}" for v in ("V0", "V1") for x in A.REPS]
    for r in att["runs"]:
        assert all(v is True for v in r["checks"].values()) and r["verdict"] == "identical"
        orig = recs[r["run"]]["record"]
        assert r["inputs_sha256"] == orig["inputs_sha256"] and r["code_sha256"] == orig["code_sha256"]
        assert r["original_predictions_file_sha256"] == orig["predictions_sha256"] == \
            hashlib.sha256((RES / f"predictions_{r['run']}.json").read_bytes()).hexdigest()
        assert r["reproduced_predictions_sha256"] == r["original_predictions_sha256"]
