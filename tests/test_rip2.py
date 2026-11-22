"""RIP-2 build tests (design v0.7, FD-01-D46). Synthetic only. Nothing here runs the registered experiment:
the only end-to-end call is a smoke run with a tiny spec (heavy)."""
import importlib.util
import math
import random
from pathlib import Path

import numpy as np
import pytest

from xauusd_swarm import reid
from xauusd_swarm import rip1_attack as A
from xauusd_swarm import rip2 as R

ROOT = Path(__file__).resolve().parents[1]


# ---------------- §4a frozen world table: the code must match the design document ----------------
def test_world_table_matches_design_section_4a():
    want_assets = [(1800, 0.01, 0.00002, 0.0009, 0.6), (30, 0.001, 0.0, 0.0014, 0.3),
                   (1.1, 0.00001, -0.00001, 0.0005, 0.1), (150, 0.01, 0.00001, 0.0011, 0.45)]
    for a, (L, tick, mu, vol, act) in zip(reid.ASSETS, want_assets):
        assert (a["level"], a["tick"], a["drift"], a["vol"], a["act"]) == (L, tick, mu, vol, act)
    assert [(p["volx"], p["growth"]) for p in reid.PERIODS] == [(0.8, 1.0), (1.0, 1.15), (1.6, 1.3), (1.2, 1.45)]
    sig = {0: [0.00072, 0.0009, 0.00144, 0.00108], 1: [0.00112, 0.0014, 0.00224, 0.00168],
           2: [0.0004, 0.0005, 0.0008, 0.0006], 3: [0.00088, 0.0011, 0.00176, 0.00132]}
    lg = {0: [1800, 2070, 2340, 2610], 1: [30, 34.5, 39, 43.5], 2: [1.1, 1.265, 1.43, 1.595], 3: [150, 172.5, 195, 217.5]}
    for a in range(4):
        for p in range(4):
            assert reid.ASSETS[a]["vol"] * reid.PERIODS[p]["volx"] == pytest.approx(sig[a][p], rel=1e-12)
            assert reid.ASSETS[a]["level"] * reid.PERIODS[p]["growth"] == pytest.approx(lg[a][p], rel=1e-12)
    m_sets = {0: [0.5, 1, 5, 10], 1: [0.05, 0.1, 0.5, 1], 2: [0.0005, 0.001, 0.005, 0.01], 3: [0.5, 1, 5, 10]}
    for a in range(4):
        assert [m for m, _ in R.m_prior("AP", (a, 0))] == pytest.approx(m_sets[a], rel=1e-12)
        assert R.canonical_params(a)["m"] == pytest.approx(100 * reid.ASSETS[a]["tick"], rel=1e-12)
        assert R.canonical_params(a)["m"] == pytest.approx(m_sets[a][1], rel=1e-12)
    pv = R.pooled_values()
    assert pv["mu"] == pytest.approx(0.000005, rel=1e-12) and pv["act"] == pytest.approx(0.3625, rel=1e-12)
    assert pv["sigma"] == pytest.approx(0.00101574, rel=1e-5) and pv["Lg"] == pytest.approx(66.2936, rel=1e-5)
    assert A.draw.__code__.co_consts is not None and R.SEEDS == {"dev": 5101, "eval": 5102, "util_planted": 5103,
                                                                  "util_null": 5104, "bootstrap": 5201, "perm": 5202}


@pytest.mark.parametrize("asset,period", [(0, 0), (1, 2), (2, 3), (3, 1)])
def test_path_from_normals_is_the_frozen_generator(asset, period):
    rnd = random.Random(99)
    z = [rnd.gauss(0, 1) for _ in range(300)]
    _, obs = R.path_from_normals(asset, period, z)
    assert obs == reid.simulate(asset, period, 300, random.Random(99))


def test_shift_and_act_zero_worlds():
    rnd = random.Random(3)
    z = [rnd.gauss(0, 1) for _ in range(400)]
    lat0, _ = R.path_from_normals(1, 1, z)
    lat1, _ = R.path_from_normals(1, 1, z, tau=200)
    r0, r1 = np.diff(np.log(lat0)), np.diff(np.log(lat1))
    assert np.allclose(r0[:199], r1[:199])                          # steps t < τ unchanged
    a = reid.ASSETS[1]
    assert np.allclose(r1[199:] - a["drift"], 2 * (r0[199:] - a["drift"]))   # r_τ is the first affected (index t-1)
    latz, _ = R.path_from_normals(1, 1, z, act_zero=True)
    rz = np.diff(np.log(latz)) - a["drift"]
    assert np.allclose(rz, a["vol"] * reid.PERIODS[1]["volx"] * np.array(z[1:]))


def test_families_are_paired_and_deterministic():
    f1, f2 = R.make_families(7, 2, 4, 64), R.make_families(7, 2, 4, 64)
    assert [f["prm"] for f in f1] == [f["prm"] for f in f2] and [f["z"] for f in f1] == [f["z"] for f in f2]
    assert len(f1) == 32 and all(len(f["z"]) == 4 for f in f1)
    f = f1[5]
    obs = R.path_from_normals(*f["cls"], f["z"][0])[1]
    c1 = R.represent("affine_level", "C1", obs, f["cls"][0], f["prm"])
    assert c1 == obs                                              # a = 1, b = 0: x = P exactly (IC-09)
    assert R.represent("tick_grid", "C2", obs, f["cls"][0], f["prm"]) == \
        A.blind("tick_grid", obs, f["cls"][0], f["prm"])          # C2 = the RIP-1 transform with the secret draw


# ---------------- attackers: equal to the registered code when Δ is hidden ----------------
def _small(rep, g, fpc=2, n=128, seed=11):
    fams = R.make_families(seed, fpc, g, n)
    xs = [[A.blind(rep, R.path_from_normals(*f["cls"], z)[1], f["cls"][0], f["prm"]) for z in f["z"]] for f in fams]
    return fams, xs


def test_a1_a2_equal_reid_attack_without_onehot():
    dev, dx = _small("tick_grid", 1, seed=1)
    ev, ex = _small("tick_grid", 1, seed=2)
    y = [f["cls"] for f in dev]
    a1, a2 = R.a1_a2([reid.features(x[0]) for x in dx], y, [reid.features(x[0]) for x in ex])
    assert a1 == reid.attack("A1_knn_features", [x[0] for x in dx], y, [x[0] for x in ex])
    assert a2 == reid.attack("A2_centroid_features", [x[0] for x in dx], y, [x[0] for x in ex])


def test_a4_equals_rip1_a4_without_onehot():
    dev, dx = _small("affine_level", 4, seed=3)
    ev, ex = _small("affine_level", 4, seed=4)
    want = A.a4([(xs, f["cls"]) for f, xs in zip(dev, dx)], ex)
    a, b = R.a4_feats([[reid.features(x) for x in xs] for xs in dx], [f["cls"] for f in dev],
                      [[reid.features(x) for x in xs] for xs in ex])
    assert a == want["A4a"] and b == want["A4b"]


def test_onehot_marks_the_tick():
    assert R.onehot(0.01) == [0.0, 0.0, 1.0] and R.onehot(0.00001) == [1.0, 0.0, 0.0]


# ---------------- A6: equal to RIP-1 A6 for the full AP model; C1 variants; pooling ----------------
@pytest.mark.parametrize("rep", [r for r in A.REPS if r != "level_residual"])
def test_a6_full_ap_c2_equals_rip1_a6(rep):
    A.SPEC["n"] = 512
    fams, xs = _small(rep, 1, fpc=1, n=512, seed=5)
    for f, x in list(zip(fams, xs))[::5]:
        got = R.a6_scores(rep, "C2", x)
        want = A.a6_scores(rep, x)
        for c in A.CLASSES:
            assert got[c] == pytest.approx(want[c], rel=1e-12, abs=1e-9) or got[c] == want[c]


def test_pp_prior_equals_ap_where_no_prior_is_asset_linked():
    assert [m for m in R.ablation_models("log_returns") if m[2] == "PP"] == []
    assert len(R.ablation_models("tick_grid")) == 1 + 2 + 4 * 2 * 2
    assert len(R.ablation_models("affine_level")) == 1 + 1 + 4 * 2


def test_generator_pooling_makes_classes_identical_in_the_generator():
    pv = R.pooled_values()
    k = [R.class_params(c, tuple(R.COMPONENTS), pv) for c in A.CLASSES]
    assert all(np.array_equal(k[0]["s"], x["s"]) and k[0]["mu"] == x["mu"] and k[0]["Lg"] == x["Lg"] for x in k)
    assert len({x["L"] for x in k}) == 4                          # priors stay at the class's asset (§7)


def test_group_and_pooled_priors():
    assert R.c_prior("GP", (0, 1)) == [(1800.0, 0.5), (150.0, 0.5)] == R.c_prior("GP", (3, 2))
    assert R.c_prior("GP", (2, 0)) == [(1.1, 1.0)]
    assert sum(w for _, w in R.m_prior("PP", (1, 1))) == pytest.approx(1.0) and len(R.m_prior("PP", (1, 1))) == 16


# ---------------- §6 bootstrap; §7 feature groups and permutation ----------------
def test_bootstrap_is_stratified_by_class_and_reusable():
    y = [c for c in A.CLASSES for _ in range(3)]
    sets = R.bootstrap_sets(y, 50, np.random.default_rng(1))
    for s in sets:
        assert len(s) == len(y)
        for c in A.CLASSES:
            assert sum(1 for i in s if y[i] == c) == 3              # stratum size kept, members from the stratum
    d = R.paired_diff(np.ones(len(y)), np.zeros(len(y)), sets)
    assert d["diff"] == 1.0 and d["ci95"] == [1.0, 1.0]


def test_feature_groups_partition_the_38_features():
    cols = sorted(j for v in R.FEATURE_GROUPS.values() for j in v)
    assert cols == list(range(38))


def test_permutation_is_family_level_member_by_member():
    ff = [[[f * 10 + i + 0.1 * j for j in range(4)] for i in range(3)] for f in range(5)]
    perm = [2, 0, 1, 4, 3]
    out = R.permute_family_group(ff, {1, 2}, perm)
    for f in range(5):
        for i in range(3):
            assert out[f][i][1:3] == ff[perm[f]][i][1:3] and out[f][i][0] == ff[f][i][0] and out[f][i][3] == ff[f][i][3]


# ---------------- §8 utility measures ----------------
def _verify_module():
    spec = importlib.util.spec_from_file_location("uvol", ROOT / "scripts" / "rip2_uvol_verify.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_uvol_truth_equals_the_registered_reference_for_all_kinds_and_cases():
    # review B-R1-03: all five quantity kinds (+ level_residual, unwrapped = C0) on all ten registered cases, against
    # the registered reference scripts/rip2_uvol_verify.exact (separate code, frozen by FD-01-D46)
    U = _verify_module()
    for name, asset, P, mu, sigma, _ in U.CASES:
        tick = reid.ASSETS[asset]["tick"]
        prm = {"c": U.PARAMS["c_of"](asset), "a": U.PARAMS["a"], "b": U.PARAMS["b"], "m": 1.0}
        kinds = {"C0_or_level_residual_unwrapped": R.q_kinds("log_returns", "C0", asset, None),
                 "level_residual_C2": R.q_kinds("level_residual", "C2", asset, prm),
                 "tick_grid": R.q_kinds("tick_grid", "C2", asset, prm),
                 "affine_level": R.q_kinds("affine_level", "C2", asset, prm),
                 "log_returns": R.q_kinds("log_returns", "C1", asset, None),
                 "volatility_time": R.q_kinds("volatility_time", "C1", asset, None)}
        got = R.uvol_truth_step(P, mu, sigma, tick, kinds)
        for kind in U.KINDS:
            want = U.exact(kind, asset, P, mu, sigma)[0]
            assert got[kind] == pytest.approx(want, rel=1e-12), (name, kind)
        assert got["level_residual_C2"] == pytest.approx(U.exact(U.KINDS[0], asset, P, mu, sigma)[0], rel=1e-12)


def test_observed_s_per_representation():
    obs = [100.0, 101.0, 99.0, 100.5]
    assert np.allclose(R.observed_s("C0", "C0", obs), np.diff(obs) ** 2)
    lr = R.represent("log_returns", "C1", obs, 0, None)
    assert np.allclose(R.observed_s("log_returns", "C1", lr), np.diff(np.log(obs)) ** 2)
    vt = R.represent("volatility_time", "C1", obs, 0, None)
    assert np.allclose(R.observed_s("volatility_time", "C1", vt), np.diff(np.log(obs)) ** 2)


def test_spearman_known_values_and_ties():
    assert R.spearman([1, 2, 3, 4], [10, 20, 30, 40]) == pytest.approx(1.0)
    assert R.spearman([1, 2, 3, 4], [4, 3, 2, 1]) == pytest.approx(-1.0)
    assert R.spearman([1, 2, 2, 3], [1, 2, 3, 4]) == pytest.approx(0.9486832980505138)


def test_uevent_index_and_tie_rule():
    s = np.r_[np.ones(199), 9 * np.ones(312)]                      # s_t for t = 1..511; jump at t = τ = 200
    out = R.uevent(s, tau=200)
    assert out["tau_hat"] == 200 and out["flag"] and out["success"]
    s2 = np.array([1.0, 3.0, 1.0, 3.0] * 128)[:511]                 # |S_k| ties: the smallest k wins
    S = np.cumsum(s2 - s2.mean())[:-1]
    assert R.uevent(s2)["tau_hat"] == int(np.argmax(np.abs(S))) + 2


def test_uact_detects_the_cycle_and_not_noise():
    t = np.arange(1, 512)
    rnd = np.random.default_rng(0)
    cyc = (1 + 0.6 * np.sin(2 * np.pi * t / 64)) ** 2 * rnd.chisquare(1, 511)
    assert R.uact_detect(cyc)
    assert sum(R.uact_detect(rnd.chisquare(1, 511)) for _ in range(200)) <= 12   # ~1 % nominal, loose bound


def test_registered_spec_is_the_design():
    assert R.SPEC["fpc"] == {"ind": 25, "g4": 10, "g16": 5} and R.SPEC["B"] == 2000 and R.SPEC["perm_repeats"] == 50
    assert R.SPEC["uvol_window"] == 32 and R.SPEC["uact_len"] == 448 and R.SPEC["uact_k"] == 7
    assert R.SPEC["uevent_crit"] == 1.358 and R.SPEC["uevent_tol"] == 16 and R.SPEC["tau_range"] == (128, 384)
    assert R.SPEC["truth_nsigma"] == 12 and R.SPEC["util_fpc"] == 25


# ---------------- smoke run on a tiny spec (throwaway; NOT the registered experiment) ----------------
@pytest.mark.heavy
def test_smoke_run_tiny_spec():
    saved = dict(R.SPEC)
    try:
        res = R.run({"fpc": {"ind": 1, "g4": 1, "g16": 1}, "util_fpc": 1, "B": 20, "perm_repeats": 2, "grid": 17})
    finally:
        R.SPEC.clear()
        R.SPEC.update(saved)
        A.SPEC["n"] = 512
    assert {c["representation"] for c in res["cells"]} == set(A.REPS) | {"C0(raw prices)"}
    assert len(res["utility"]) == 2 * (1 + 2 * 3 + 2)
    assert all(e["C1_equals_C2_data"] == (e["representation"] in ("log_returns", "volatility_time")) for e in res["effects"])
    assert any("within_group_group_pooled_prior" in r for r in res["ablation"] if r["representation"] == "tick_grid")
    assert len(res["feature_groups"]) == 5 * 3 * 5


def test_wrapped_density_is_exact_against_a_brute_force_sum():
    # IC-12 / FL-023: both branches against a very wide direct sum, incl. |d| far beyond the RIP-1 window
    rnd = np.random.default_rng(3)
    for m, S, spread in ((0.05, 2.0, 10.0), (0.5, 0.2, 10.0), (10.0, 4.0, 10.0), (0.0005, 0.0004, 0.01), (1.0, 0.3, 1.0)):
        d = rnd.uniform(-spread, spread, 40)
        S_v = np.full(40, S)
        got = R._wrapped_log_density(d, 0.01, S_v, m)
        J = int(abs(spread) / m + 60 * S / m) + 10
        jj = np.arange(-J, J + 1)[None, :]
        v = A._logN(d[:, None] + jj * m, 0.01, S)
        mx = np.max(v, axis=1)
        want = mx + np.log(np.sum(np.exp(v - mx[:, None]), axis=1))
        assert np.allclose(got, want, rtol=0, atol=1e-9)


def test_rip1_direct_sum_drops_mass_for_large_increments():
    # FL-023, documented: the frozen RIP-1 wrapped sum is centred on j = 0 (reproduced here as RIP-1 computes it)
    m, S, d, mean = 0.05, 2.04, 9.45, 0.04
    J = int(math.ceil(8 * S / m)) + 2
    jj = np.arange(-J, J + 1)
    v = A._logN(d + jj * m, mean, S)
    rip1_value = float(np.max(v) + np.log(np.sum(np.exp(v - np.max(v)))))
    exact = float(R._wrapped_log_density(np.array([d]), mean, np.array([S]), m)[0])
    assert exact == pytest.approx(math.log(1 / m), abs=1e-9) and rip1_value < exact - 1e-5


def test_level_residual_support_is_enforced():
    # FL-024: x = fmod(P, m) lies in [0, m); a hypothesis m below the observed values is impossible
    A.SPEC["n"] = 512
    k = R.class_params((2, 0))
    x = np.full(512, 3.7)                                           # values up to 3.7: needs m > 3.7
    assert R.ll_resid_given_m([x], k, 0.001) == -math.inf
    assert R.ll_resid_given_m([x], k, 10.0) > -math.inf
    # in-model data: the true class gets a finite likelihood and an impossible m set gets none
    fams, xs = _small("level_residual", 1, fpc=1, n=512, seed=8)
    for f, x in zip(fams, xs):
        m_true = f["prm"]["m"]
        assert np.all(np.asarray(x[0]) < m_true)
        assert R.ll_resid_given_m(x, R.class_params(f["cls"]), m_true) > -math.inf


# ---------------- IC-08: the permutation draw order cannot drift silently (review B-R1-02) ----------------
def test_permutation_draw_order_scenario_representation_group_repeat():
    import ast
    import inspect
    import textwrap
    tree = ast.parse(textwrap.dedent(inspect.getsource(R.run)))

    def loops_around(call_name):
        found = []

        def visit(node, stack):
            if isinstance(node, ast.Call) and getattr(node.func, "id", None) == call_name:
                found.append(list(stack))
            for ch in ast.iter_child_nodes(node):
                visit(ch, stack + ([ast.unparse(node.target)] if isinstance(node, ast.For) else []))
        visit(tree, [])
        return found
    assert loops_around("_feature_groups") == [["(sc, g)", "rep"]]            # scenario outer, representation inner
    calls = []
    real = R.permute_family_group
    try:
        R.permute_family_group = lambda ff, cols, perm: (calls.append(min(cols)), real(ff, cols, perm))[1]
        saved = R.SPEC["perm_repeats"]
        R.SPEC["perm_repeats"] = 3
        dev = R.make_families(1, 1, 1, 64)
        ev = R.make_families(2, 1, 1, 64)
        feat = lambda fams: [[[float(i + j) for j in range(38)]] for i, _ in enumerate(fams)]   # noqa: E731
        R._feature_groups("tick_grid", "ind", 1, dev, {"dff": feat(dev), "eff": feat(ev)}, ev,
                          [f["cls"] for f in ev], np.random.default_rng(0))
    finally:
        R.permute_family_group = real
        R.SPEC["perm_repeats"] = saved
    want = [min(cols) for cols in R.FEATURE_GROUPS.values() for _ in range(3)]  # group outer, repeat inner
    assert calls == want


def test_level_residual_support_boundary_is_strict():
    # review B-R2-02: support [0, m) exactly — x = m and x < 0 are impossible, the largest float below m is possible
    A.SPEC["n"] = 512
    k = R.class_params((1, 1))
    for m in (0.05, 0.1, 0.5, 1.0, 0.001, 10.0):
        below = float(np.nextafter(m, 0.0))
        base = np.full(512, 0.25 * m)
        for bad in (m, -0.0 - 1e-300, float(np.nextafter(0.0, -1.0)), 1.5 * m):
            x = base.copy()
            x[100] = bad
            assert R.ll_resid_given_m([x], k, m) == -math.inf, (m, bad)
        x = base.copy()
        x[100] = below
        assert R.ll_resid_given_m([x], k, m) > -math.inf
    # the registered transform never produces a value at or above m, nor below 0 (math.fmod is exact in IEEE 754)
    rnd = random.Random(4)
    for _ in range(20000):
        m = rnd.choice([0.0005, 0.001, 0.05, 0.1, 0.5, 1.0, 5.0, 10.0])
        P = rnd.uniform(0.5, 3000.0)
        v = math.fmod(P, m)
        assert 0.0 <= v < m


# ---------------- the registered run (OD-S9-09): committed evidence is intact ----------------
def test_registered_run_files_are_intact_and_partially_reproduced():
    import hashlib
    import json
    d = ROOT / "docs" / "results" / "rip2"
    if not (d / "results.json").exists():
        pytest.skip("RIP-2 not run")
    want = (d / "results.sha256").read_text().split()[0]
    assert hashlib.sha256((d / "results.json").read_bytes()).hexdigest() == want
    res = json.loads((d / "results.json").read_text())
    assert res["run_meta"]["spec_override"] is None and res["run_meta"]["authorisation"] == "OD-S9-09"
    assert (len(res["cells"]), len(res["effects"]), len(res["ablation"]), len(res["feature_groups"]),
            len(res["utility"])) == (170, 150, 408, 75, 18)
    rep = json.loads((ROOT / "docs" / "results" / "RIP2_partial_reproduction.json").read_text())
    assert rep["all_identical"] is True and rep["cells_checked"] == 12
