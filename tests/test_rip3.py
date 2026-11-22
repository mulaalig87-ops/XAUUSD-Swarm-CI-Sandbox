"""RIP-3 build tests (design v0.4, FD-01-D47; BUILD OD-S9-11). Synthetic only. Nothing here scores the registered
evaluation (6201) or confirmatory (6301) sets: the only end-to-end calls use the 'smoke' set (6103) with tiny sizes."""
import hashlib
import json
import math
import random
from pathlib import Path

import numpy as np
import pytest

from xauusd_swarm import reid
from xauusd_swarm import rip1_attack as A
from xauusd_swarm import rip2
from xauusd_swarm import rip3 as R

ROOT = Path(__file__).resolve().parents[1]
FROZEN_DESIGN_SHA = "efb7e16315476c4d4caa523fc8d45adcdd1c3ae0e6bbc13d35b8d7902def7898"


def _fam(world="W1", g=1, cls=(0, 2), i=0, role="test"):
    return R.make_family(1, role, world, g, cls, i)


def _obs(fam, m=0, world="W1", **kw):
    return R.path(world, fam["cls"], R.innovations(world, fam["cls"], R.member_stream(fam, m), 512), **kw)[1]


# ---------------- design binding ----------------
def test_frozen_design_file_is_unchanged():
    data = (ROOT / "docs/research/RIP3_DESIGN.md").read_bytes().replace(b"\r\n", b"\n")   # Windows checkout (FL-029)
    assert hashlib.sha256(data).hexdigest() == FROZEN_DESIGN_SHA


def test_constants_match_the_frozen_design():
    assert R.SEEDS["dev"] == 6101 and R.SEEDS["eval"] == 6201 and R.SEEDS["confirm"] == 6301
    s = R.SPEC
    assert s["fpc"] == {"ind": 25, "g4": 10, "g16": 5} and s["B"] == 2000 and s["dev_per_class"] == 2000
    assert s["mults"] == (1, 2, 4) and s["knn_k"] == 15
    assert s["garch"] == {"alpha": 0.08, "beta": 0.90, "nu": 5, "burnin": 500}
    assert (s["t_K0"], s["t_Kmax"], s["t_acc"], s["price_floor_ticks"]) == (50.0, 400.0, 1e-6, 100)
    assert R.CANDIDATES == ["B-LR", "B-AF", "B-LRS", "M1", "M2w1", "M2w2", "M2w4", "M3W32", "M3W128", "M4", "M5", "M6"]
    assert R.N_SUMMARY == 38 + 64 + 1 + 5


def test_every_implementation_choice_is_in_the_build_notes():
    notes = (ROOT / "docs/research/RIP3_BUILD_NOTES.md").read_text(encoding="utf-8")
    for k in R.IMPLEMENTATION_CHOICES:
        assert f"| {k} |" in notes


def test_registered_sets_are_refused_without_the_run_authorisation(tmp_path):
    for set_name in ("eval", "confirm"):
        with pytest.raises(R.NotAuthorised):
            R.run_jobs(tmp_path, set_name, ["B-LR"])
        with pytest.raises(R.NotAuthorised):
            R.run_job(set_name, "B-LR", "W1")
    assert not list(tmp_path.iterdir())


# ---------------- worlds ----------------
def test_w1_is_bit_identical_to_reid_simulate():
    for cls in [(0, 0), (1, 3), (2, 1), (3, 2)]:
        fam = _fam(cls=cls)
        assert _obs(fam) == reid.simulate(cls[0], cls[1], 512, R.member_stream(fam, 0))


def test_w2_recursion_follows_the_specification_exactly():
    cls = (1, 2)
    rnd = R.member_stream(_fam("W2", cls=cls), 0)
    inno = R.innovations("W2", cls, rnd, 64)
    al, be, nu = 0.08, 0.90, 5
    sk = R.sigma_k(*cls)
    om = sk * sk * (1 - al - be)
    assert om == pytest.approx(0.02 * sk * sk, rel=1e-12)
    rnd = R.member_stream(_fam("W2", cls=cls), 0)
    c = math.sqrt((nu - 2) / nu)
    h, e = sk * sk, 0.0
    for _ in range(500):
        h = om + al * e * e + be * h
        G = rnd.gauss(0, 1)
        Q = rnd.gammavariate(nu / 2, 2)
        e = math.sqrt(h) * (G / math.sqrt(Q / nu) * c)
    for t in range(64):
        h = om + al * e * e + be * h
        G = rnd.gauss(0, 1)
        Q = rnd.gammavariate(nu / 2, 2)
        e = math.sqrt(h) * (G / math.sqrt(Q / nu) * c)
        assert inno["h"][t] == h and inno["eps"][t] == e


def test_w2_prices_follow_the_generator_expression():
    fam = _fam("W2", cls=(3, 1))
    inno = R.innovations("W2", (3, 1), R.member_stream(fam, 0), 512)
    a, p = reid.ASSETS[3], reid.PERIODS[1]
    price = a["level"] * p["growth"]
    _, obs = R.path_w2(3, 1, inno["eps"], tau=200)
    for t, e in enumerate(inno["eps"]):
        step = (1 + a["act"] * math.sin(2 * math.pi * t / 64)) * e * (2 if t >= 200 else 1)
        price *= math.exp(a["drift"] + step)
        assert obs[t] == round(round(price / a["tick"]) * a["tick"], 10)


def test_paired_worlds_share_draws():
    fam = _fam("W2")
    inno = R.innovations("W2", fam["cls"], R.member_stream(fam, 0), 512)
    _, a = R.path("W2", fam["cls"], inno)
    _, b = R.path("W2", fam["cls"], inno, tau=fam["tau"])
    assert a[:fam["tau"]] == b[:fam["tau"]] and a != b


def test_streams_are_keyed_and_platform_independent():
    f1, f2 = _fam(i=3), _fam(i=3)
    assert f1["prm"] == f2["prm"] and f1["tau"] == f2["tau"] and f1["u_kappa"] == f2["u_kappa"]
    assert R.member_stream(f1, 2).random() == R.member_stream(f2, 2).random()
    assert R.stream(1, "a").random() == random.Random("RIP3|1|a").random()


# ---------------- candidates (§3.0, §3.1) ----------------
def test_m1_has_unit_rms_exactly_and_keeps_phase_ratios():
    r = np.array(A.blind("log_returns", _obs(_fam()), 0, {}))
    x = R.m1(r)
    assert R.rms(x) == pytest.approx(1.0, abs=1e-14)
    c_r, c_x = R.phase_rms(r, 1), R.phase_rms(x, 1)
    assert np.allclose(c_x / c_x.mean(), c_r / c_r.mean(), rtol=1e-12)


def test_m5_makes_the_per_phase_rms_identical_and_equal_to_the_mean_profile():
    r = np.array(A.blind("log_returns", _obs(_fam(cls=(0, 3))), 0, {}))
    c = R.phase_rms(r, 1)
    x = R.m5(r)
    assert np.allclose(R.phase_rms(x, 1), c.mean(), rtol=1e-12)
    ph = R.phases(511, 1)
    assert np.bincount(ph, minlength=64)[0] == 7 and set(np.bincount(ph, minlength=64)[1:]) == {8}


def test_m6_is_m5_then_m1():
    fam = _fam()
    obs = _obs(fam)
    r = np.array(A.blind("log_returns", obs, 0, {}))
    assert np.array_equal(R.transform("M6", obs, 0, fam), R.m1(R.m5(r)))
    assert R.rms(R.transform("M6", obs, 0, fam)) == pytest.approx(1.0, abs=1e-14)


def test_m3_uses_the_trailing_window_including_t():
    r = np.array([0.3, -0.1, 0.0, 0.2, -0.4, 0.05])
    for W in (1, 2, 4):
        x = R.m3(r, W)
        for t in range(len(r)):
            w = r[max(0, t - W + 1):t + 1]
            den = math.sqrt(np.mean(w * w))
            assert x[t] == pytest.approx(r[t] / den if den > 0 else 0.0, rel=1e-12)
    assert R.m3(np.array([0.0, 0.0, 1.0]), 2)[0] == 0.0           # IC3-10


def test_m4_rank_gauss_with_average_ties():
    r = np.array([0.1, -0.2, 0.1, 0.0, 0.3])
    x = R.m4(r)
    ranks = [3.5, 1, 3.5, 2, 5]
    for v, q in zip(x, ranks):
        assert v == pytest.approx(R._ND.inv_cdf((q - 0.5) / 5), rel=1e-12)


def test_m2_scale_is_exp_w_u_per_family():
    fam = _fam(g=4)
    for w in (1, 2, 4):
        xs = [R.transform(f"M2w{w}", _obs(fam, m), 0, fam) for m in range(2)]
        rs = [np.array(A.blind("log_returns", _obs(fam, m), 0, {})) for m in range(2)]
        for x, r in zip(xs, rs):
            assert np.allclose(x, math.exp(w * fam["u_kappa"]) * r, rtol=1e-14)
    assert -1 <= fam["u_kappa"] <= 1


def test_baselines_are_the_rip2_representations():
    fam = _fam(cls=(2, 1))
    obs = _obs(fam)
    assert list(R.transform("B-AF", obs, 2, fam)) == A.blind("affine_level", obs, 2, fam["prm"])
    assert list(R.transform("B-LRS", obs, 2, fam)) == A.blind("level_residual", obs, 2, fam["prm"])
    assert list(R.transform("B-LR", obs, 2, fam)) == A.blind("log_returns", obs, 2, fam["prm"])


def test_summary_vector_has_108_components_in_the_frozen_order():
    fam = _fam()
    x = R.transform("M1", _obs(fam), 0, fam)
    s = R.summary(x)
    assert len(s) == 108
    assert list(s[:38]) == reid.features([float(v) for v in x])
    assert np.allclose(s[38:102], R.phase_rms(x, 1))
    assert s[102] == pytest.approx(0.0, abs=1e-14)                 # log RMS of an M1 output
    assert list(s[103:]) == [reid._acf([float(v * v) for v in x], k) for k in range(1, 6)]


# ---------------- attackers ----------------
def test_numpy_attackers_equal_the_reference_implementations():
    rng = random.Random(3)
    dev = [[rng.gauss(0, 1) for _ in range(38)] for _ in range(160)]
    dy = [R.CLASSES[i % 16] for i in range(160)]
    ev = [[rng.gauss(0, 1) for _ in range(38)] for _ in range(40)]
    r1, r2 = rip2.a1_a2(dev, dy, ev)
    assert R.a1(dev, dy, ev) == r1 and R.a2(dev, dy, ev) == r2
    dx = [[rng.gauss(0, 1) for _ in range(100)] for _ in range(80)]
    ex = [[rng.gauss(0, 1) for _ in range(100)] for _ in range(20)]
    assert R.a3(dx, dy[:80], ex) == reid.attack("A3_series_match", dx, dy[:80], ex)
    dff = [[[rng.gauss(0, 1) for _ in range(38)] for _ in range(4)] for _ in range(64)]
    eff = [[[rng.gauss(0, 1) for _ in range(38)] for _ in range(4)] for _ in range(32)]
    ya, yb = rip2.a4_feats(dff, dy[:64], eff)
    a, b = R.a4(dff, dy[:64], eff)
    assert a == ya and b == yb


def test_ledoit_wolf_matches_the_published_formula():
    X = np.random.default_rng(1).normal(size=(300, 20)) * np.arange(1, 21)
    cov, s = R.ledoit_wolf(X)
    assert 0 < s < 1
    emp = np.cov(X, rowvar=False, bias=True)
    mu = np.trace(emp) / 20
    assert np.allclose(cov, (1 - s) * emp + s * mu * np.eye(20), rtol=1e-12)
    sk = pytest.importorskip("sklearn.covariance")
    c2, s2 = sk.ledoit_wolf(X)
    assert s == pytest.approx(s2, rel=1e-12) and np.allclose(cov, c2, rtol=1e-12)


def test_a8_majority_and_tie_rules():
    C = R.CLASSES
    dev = np.array([[0.0], [0.1], [0.2], [1.0], [1.1], [5.0]])
    y = [C[0], C[0], C[1], C[1], C[2], C[3]]
    # query at 0.15 with k = 4: C0 has 2 (d 0.15, 0.05), C1 has 2 (d 0.05, 0.85) -> tie, C0 sum 0.2 < C1 0.9
    assert R.a8(dev, y, np.array([[0.15]]), k=4) == [C[0]]
    # equal sums go to the lowest class index
    dev2 = np.array([[-1.0], [1.0]])
    assert R.a8(dev2, [C[5], C[2]], np.array([[0.0]]), k=2) == [C[2]]


def test_a7_classifies_well_separated_gaussians():
    rng = np.random.default_rng(0)
    X = np.vstack([rng.normal(loc=3 * i, size=(50, 5)) for i in range(16)])
    y = [c for c in R.CLASSES for _ in range(50)]
    m = R.A7Model(X, y)
    ld = m.logdens(np.array([[3 * 7] * 5]))
    assert R.argmax_classes(ld[0]) == R.CLASSES[7]
    allowed = np.array([i != 7 for i in range(16)])
    assert R.argmax_classes(ld[0], allowed) != R.CLASSES[7]


# ---------------- A6 for M1 / M2 ----------------
def test_quadratic_form_equals_the_direct_gaussian_log_density():
    fam = _fam(g=4)
    x = R.transform("M1", _obs(fam), 0, fam)
    k = rip2.class_params((1, 2))
    s = k["s"][1:]
    t = R._quad_terms(x, k["mu"], s)
    for v in (-8.0, -6.5, -5.0):
        direct = float(np.sum(A._logN(math.exp(v) * x, k["mu"], s))) + len(x) * v
        assert R._g(v, *t) == pytest.approx(direct, rel=1e-12)


def test_m1_and_m2_likelihoods_against_dense_quadrature():
    fam = _fam(g=4, cls=(0, 2))
    obs = [_obs(fam, m) for m in range(4)]
    for c in [(0, 2), (2, 3)]:
        k = rip2.class_params(c)
        s = k["s"][1:]
        x = R.transform("M1", obs[0], 0, fam)
        t = R._quad_terms(x, k["mu"], s)
        v = np.linspace(-20, 5, 2_000_001)
        assert R.ll_scale_invariant(x, k["mu"], s) == pytest.approx(R._trap_log(R._g(v, *t), v), abs=1e-6)
        for w in (2, 4):
            xs = [R.transform(f"M2w{w}", o, 0, fam) for o in obs]
            T = [R._quad_terms(xx, k["mu"], s) for xx in xs]
            v = np.linspace(-w, w, 2_000_001)
            ref = R._trap_log(sum(R._g(v, *tt) for tt in T), v) - math.log(2 * w)
            assert R.ll_secret_scale(xs, k["mu"], s, w) == pytest.approx(ref, abs=1e-4)


def test_m2_boundary_window_keeps_all_mass():
    """FL-027: the mode outside [−w, w] at a moderate distance (found by the pre-registered check B2)."""
    fc, cand, c = (3, 1), "M2w1", (3, 2)
    fam = R.make_family(6102, "a6check", "W1", 1, fc, 0)
    xs = [R.transform(cand, _obs(fam), fc[0], fam)]
    k = rip2.class_params(c)
    T = [R._quad_terms(xs[0], k["mu"], k["s"][1:])]
    v0, sd = R._mode(T[0][0], T[0][1], T[0][3])
    assert v0 > 1 and (v0 - 1) / sd < 12
    v = np.linspace(-1, 1, 4_000_001)
    ref = R._trap_log(R._g(v, *T[0]), v) - math.log(2)
    assert R.ll_secret_scale(xs, k["mu"], k["s"][1:], 1) == pytest.approx(ref, abs=1e-5)


def test_a6_true_class_wins_on_clear_cases():
    fam = _fam(g=16, cls=(1, 2))
    xs = [R.transform("M2w1", _obs(fam, m), 1, fam) for m in range(16)]
    sc = R.a6_scores("M2w1", xs)
    assert max(sc, key=sc.get)[0] == 1
    sd = R.a6_scores(R.CONTROL, [R.transform("M1", _obs(fam, m), 1, fam) for m in range(2)],
                     delta_seen=reid.ASSETS[1]["tick"])
    assert all(sd[c] == -math.inf for c in R.CLASSES if c[0] != 1)


# ---------------- Student-t helpers and the W2 truth ----------------
def test_t5_cdf_closed_form_against_integration():
    y = np.linspace(-30, 30, 61)
    grid = np.linspace(-2000, 30, 4_000_001)
    f = (8 / (3 * math.pi * math.sqrt(5))) * (1 + grid ** 2 / 5) ** -3
    assert R.t_pdf(1.3, 5) == pytest.approx((8 / (3 * math.pi * math.sqrt(5))) * (1 + 1.3 ** 2 / 5) ** -3, rel=1e-12)
    cdf = np.concatenate([[0.0], np.cumsum((f[1:] + f[:-1]) / 2 * np.diff(grid))])
    tail = (8 / (3 * math.pi * math.sqrt(5))) * 5 ** 3 / (5 * 2000 ** 5)        # mass below −2000
    for v in y:
        assert R.t_cdf5(v) == pytest.approx(np.interp(v, grid, cdf) + tail, abs=1e-7)
    st = pytest.importorskip("scipy.stats")
    assert np.max(np.abs(R.t_cdf5(y) - st.t.cdf(y, 5))) < 1e-14


def test_tail_terms_against_integration():
    nu, K = 5, 50.0
    T0, T1, T2 = R.t_tail_terms(K, nu)
    g = np.geomspace(K, 1e7, 2_000_001)
    pdf = (8 / (3 * math.pi * math.sqrt(5))) * (1 + g ** 2 / 5) ** -3
    trap = lambda y: float(np.sum((y[1:] + y[:-1]) / 2 * np.diff(g)))       # noqa: E731
    assert T0 == pytest.approx(2 * trap(pdf), rel=1e-6)
    assert T1 == pytest.approx(2 * trap(g * pdf), rel=1e-6)
    assert T2 == pytest.approx(2 * trap(g * g * pdf), rel=1e-5)
    Ff, U2 = R.t_lower(-80.0, nu)
    g2 = np.geomspace(80, 1e7, 2_000_001)
    pdf2 = (8 / (3 * math.pi * math.sqrt(5))) * (1 + g2 ** 2 / 5) ** -3
    trap2 = lambda y: float(np.sum((y[1:] + y[:-1]) / 2 * np.diff(g2)))     # noqa: E731
    assert Ff == pytest.approx(trap2(pdf2), rel=1e-6) and U2 == pytest.approx(trap2(g2 * g2 * pdf2), rel=1e-5)


def test_betainc_against_scipy_if_available():
    sp = pytest.importorskip("scipy.special")
    for a, b, x in [(2.5, 0.5, 1e-3), (1.5, 1.5, 0.3), (0.5, 2.5, 0.99), (1.5, 1.5, 0.999), (2.5, 0.5, 1e-9)]:
        assert R.betainc(a, b, x) == pytest.approx(float(sp.betainc(a, b, x)), rel=1e-12)


def test_w2_truth_contains_the_drift_and_is_accepted_on_typical_steps():
    q, E, K, ok = R.uvol_truth_w2(2340.0, 0.00002, math.sqrt(0.6) * 0.00144, 0.01)
    assert ok and E <= 1e-6 * q and K in (50.0, 100.0, 200.0, 400.0)
    q0, *_ = R.uvol_truth_w2(2340.0, 0.0, math.sqrt(0.6) * 0.00144, 0.01)
    qm, *_ = R.uvol_truth_w2(2340.0, 0.001, math.sqrt(0.6) * 0.00144, 0.01)
    assert qm - q0 == pytest.approx(0.001 ** 2, rel=0.02)            # E r² = μ² + Var r


def test_w2_truth_chunking_does_not_change_the_sum(monkeypatch):
    a = R.uvol_truth_w2(39.0, 0.0, 0.004, 0.001)
    monkeypatch.setattr(R, "TRUTH_CHUNK", 997)
    b = R.uvol_truth_w2(39.0, 0.0, 0.004, 0.001)
    assert a[2] == b[2] and a[0] == pytest.approx(b[0], rel=1e-12)


def test_w1_truth_is_the_rip2_construction():
    fam = _fam()
    inno = R.innovations("W1", fam["cls"], R.member_stream(fam, 0), 512)
    lat, _ = R.path("W1", fam["cls"], inno, tau=fam["tau"])
    q, fails = R.truth_series("W1", fam["cls"], lat[:40], inno, fam["tau"])
    a, p = fam["cls"]
    kinds = {"lr": rip2.q_kinds("log_returns", "C1", a, None)}
    for u in (1, 17, 39):
        sig = R.sigma_k(a, p) * (1 + reid.ASSETS[a]["act"] * math.sin(2 * math.pi * u / 64))
        assert q[u - 1] == rip2.uvol_truth_step(lat[u - 1], reid.ASSETS[a]["drift"], sig, reid.ASSETS[a]["tick"], kinds)["lr"]
    assert fails == 0


# ---------------- utility ----------------
def test_uratio_windows_and_reference():
    s = np.arange(1, 512, dtype=float)              # s[i] is t = i + 1
    tau = 200
    assert R.uratio(s, tau) == pytest.approx(np.mean(np.arange(200, 264)) / np.mean(np.arange(136, 200)))
    q = np.ones(511)
    q[tau - 1:] = 4.0
    assert R.rstar(q, tau) == 4.0


def test_class_ratio_formula_and_why_not_4():
    for cls in R.CLASSES:
        a, p = cls
        mu, sk, act = reid.ASSETS[a]["drift"], R.sigma_k(a, p), reid.ASSETS[a]["act"]
        t = np.arange(128, 192)
        m2 = (1 + act * np.sin(2 * np.pi * t / 64)) ** 2
        assert m2.sum() == pytest.approx(64 * (1 + act * act / 2), rel=1e-12)
        exp_ratio = np.sum(mu ** 2 + 4 * sk ** 2 * m2) / np.sum(mu ** 2 + sk ** 2 * m2)
        assert R.r_class(cls) == pytest.approx(exp_ratio, rel=1e-12)
        assert (R.r_class(cls) == 4.0) == (mu == 0.0)


# ---------------- end to end on the smoke set (tiny sizes; not the registered sets) ----------------
@pytest.mark.heavy
def test_smoke_end_to_end(tmp_path, monkeypatch):
    monkeypatch.setitem(R.SPEC, "dev_per_class", 16)
    monkeypatch.setitem(R.SPEC, "fpc", {"ind": 1, "g4": 1, "g16": 1})
    monkeypatch.setitem(R.SPEC, "util_fpc", 1)
    monkeypatch.setitem(R.SPEC, "B", 20)
    cands = ["B-LR", "M1", "M5", R.CONTROL]
    R.run_jobs(tmp_path, "smoke", cands, worlds=("W1",))
    jobs = R.load_jobs(tmp_path, "smoke")
    assert set(jobs) == {(c, "W1") for c in cands}
    for (c, _), j in jobs.items():
        assert j["c_v1"] == "ok"
        for sc in R.SCEN:
            pred = j["identity"][sc]["pred"]
            assert {"A2x1", "A2x2", "A2x4"} <= set(pred) if sc == "ind" else {"A4a", "A4b"} <= set(pred)
            assert {"A7x1", "A7x2", "A7x4", "A8x1", "A8x2", "A8x4"} <= set(pred)
            assert ("A6" in pred) == (c in R.A6_TRACTABLE)
            assert len(j["identity"][sc]["labels"]) == 16
        assert (j["utility"] is None) == (c == R.CONTROL)
    ev = R.evaluate(jobs, "smoke", None, B=20)
    assert {r["candidate"] for r in ev["matrix"]} == set(cands)
    assert ev["classes"]["M1"] in ("P", "S") and "M5" in ev["classes"]
    assert any("scope" in r for r in ev["matrix"] if r["candidate"] == "M5")
    # resumable: a second call does nothing
    assert R.run_jobs(tmp_path, "smoke", cands, worlds=("W1",)) == []
    # independent re-score (C-R1) and partial reproduction (C-R2) on the smoke output
    res_file = tmp_path / "smoke_results.json"
    res_file.write_text(json.dumps(ev, default=lambda o: o.item() if hasattr(o, "item") else str(o)))
    assert _script("rip3_rescore").main(str(tmp_path), "smoke", str(res_file)) == []
    pr = _script("rip3_partial_repro").main(str(tmp_path), "smoke", str(tmp_path / "pr.json"), 1)
    assert pr["checked"] > 0 and pr["all_identical"]


def _script(name):
    import importlib.util
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_run_script_refuses_registered_sets_without_authorisation(tmp_path):
    import subprocess
    import sys
    for set_name in ("eval", "confirm"):
        p = subprocess.run([sys.executable, str(ROOT / "scripts/rip3_run.py"), str(tmp_path / "o"), set_name],
                           capture_output=True, text=True)
        assert p.returncode != 0 and "authorisation" in (p.stderr + p.stdout)
    assert not list((tmp_path / "o").glob("eval__*")) if (tmp_path / "o").exists() else True


def test_build_check_results_are_as_reported_in_the_notes():
    d = ROOT / "docs/results/rip3_build"
    b1 = json.loads((d / "B1_w2_truth_verification.json").read_text())
    assert b1["all_computed_pass"] and b1["not_computed"] == ["stress_a0_extreme_s_0.05"] and b1["all_accepted"]
    b2 = json.loads((d / "B2_a6_verification.json").read_text())
    assert b2["comparisons"] == 768 and not b2["all_pass"]
    assert all(r["abs_diff"] <= 1e-4 for r in b2["rows"])
    assert sum(r["algebra_max_abs_diff"] > 1e-6 for r in b2["rows"]) == 2
    b2a = json.loads((d / "B2_a6_verification_attempt1_FAILED.json").read_text())
    assert not b2a["all_pass"]
    b3 = json.loads((d / "B3_a7_validation.json").read_text())
    assert b3["c_v2"]["pass"] is False and sum(not v["pass"] for v in b3["c_v2"]["cells"].values()) == 8
    b4 = json.loads((d / "B4_w2_moments.json").read_text())
    assert b4["all_pass"]


# ---------------- IC3-22 block method (FL-026) ----------------
def test_block_method_matches_the_exact_sum_within_its_proven_bound():
    c = math.sqrt(0.6)
    for P, mu, b, tick in [(2340.0, 0.00002, c * 0.00144 * 9.6, 0.01), (39.0, 0.0, 0.0206, 0.001),
                           (1.1, -1e-5, c * 0.0004 * 0.45, 1e-5)]:
        p0 = round(round(P / tick) * tick, 10)
        for K in (50.0, 200.0):
            jlo = max(1, math.floor(P * math.exp(mu - K * b) / tick - 0.5))
            jhi = math.ceil(P * math.exp(mu + K * b) / tick + 0.5)
            ex = R._central_exact(P, mu, b, tick, K, p0, jlo, jhi)
            bl, bd, nb, _ = R._central_blocked(P, mu, b, tick, K, p0)
            assert nb > 0 and abs(ex - bl) <= bd + 1e-12 * abs(ex)


def test_interval_moments_of_t5():
    g = np.linspace(-3.0, 7.0, 2_000_001)
    f = (8 / (3 * math.pi * math.sqrt(5))) * (1 + g ** 2 / 5) ** -3
    trap = lambda y: float(np.sum((y[1:] + y[:-1]) / 2 * np.diff(g)))     # noqa: E731
    M = R._t5_interval_moments(-3.0, 7.0)
    assert M[0] == pytest.approx(trap(f), rel=1e-9) and M[1] == pytest.approx(trap(g * f), rel=1e-8)
    assert M[2] == pytest.approx(trap(g * g * f), rel=1e-9)


def test_fl026_stress_case_is_now_computable_and_accepted():
    q, E, K, ok = R.uvol_truth_w2(1800.0, 0.00002, math.sqrt(0.6) * 0.05, 0.01)
    assert ok and K == 400.0 and E <= 1e-6 * q
    assert q == pytest.approx(0.0025, rel=1e-3)        # E r² ≈ s² = 0.05² for a fine tick grid


# ---------------- implementation choices without a test before (IC report) ----------------
def test_ic3_03_seed_roles_and_bootstrap_seeds():
    assert R.SET_BASE == {"eval": 6201, "confirm": 6301, "build": 6102, "smoke": 6103}
    assert R.SEEDS["eval_bootstrap"] == 6299 and R.SEEDS["confirm_bootstrap"] == 6399
    assert R.REGISTERED_SETS == ("eval", "confirm")


def test_ic3_04_development_sizes_are_nested_and_equal_in_series():
    for g in (1, 4, 16):
        f4 = R.dev_families("W1", g, 4)
        f1 = R.dev_families("W1", g, 1)
        per4, per1 = len(f4) // 16, len(f1) // 16
        assert per4 * g == 8000 and per1 * g == 2000
        k1 = {(f["cls"], f["idx"]): f["prm"] for f in f1}
        assert all(k1[(f["cls"], f["idx"])] == f["prm"] for f in f4 if f["idx"] < per1)   # the x1 set is a prefix


def test_ic3_05_a7_standardises_before_the_shrinkage():
    rng = np.random.default_rng(2)
    X = np.vstack([rng.normal(loc=0.4 * i, size=(40, 6)) for i in range(16)])
    y = [c for c in R.CLASSES for _ in range(40)]
    Q = rng.normal(loc=2.0, size=(30, 6))
    D = np.diag([1.0, 1e6, 1e-6, 1.0, 50.0, 1.0])
    a = [R.argmax_classes(r) for r in R.A7Model(X, y).logdens(Q)]
    b = [R.argmax_classes(r) for r in R.A7Model(X @ D, y).logdens(Q @ D)]
    assert a == b                                    # column scales do not matter after z-scoring


def test_ic3_07_a8_family_level_uses_the_member_mean():
    dev = np.array([[0.0], [10.0]])
    assert R.a8(dev, [R.CLASSES[0], R.CLASSES[1]], np.array([[1.0, 2.0, 3.0]]).mean(axis=1, keepdims=True), k=1) == [R.CLASSES[0]]


def test_ic3_08_delta_shown_restricts_the_classes():
    allowed = R._allowed(reid.ASSETS[2]["tick"])
    assert [c for c, ok in zip(R.CLASSES, allowed) if ok] == [c for c in R.CLASSES if c[0] == 2]
    scores = np.arange(16, dtype=float)              # the best unrestricted class is (3, 3)
    assert R.argmax_classes(scores, allowed) == (2, 3)


def test_ic3_10_zero_denominators_give_zeros():
    assert np.array_equal(R.m1(np.zeros(511)), np.zeros(511))
    assert np.array_equal(R.m5(np.zeros(511)), np.zeros(511))
    r = np.random.default_rng(0).normal(size=511)
    r[R.phases(511, 1) == 5] = 0.0
    x = R.m5(r)
    assert np.all(x[R.phases(511, 1) == 5] == 0.0) and np.all(np.isfinite(x))


def test_ic3_16_max_attacker_tie_order():
    lab = [[0, 0], [1, 1]]
    pred = {"A8x4": [[0, 0], [1, 1]], "A6": [[0, 0], [1, 1]], "A1": [[0, 0], [0, 0]]}
    att, v = R.max_attacker(pred, lab, "joint")
    assert att == "A6" and v.mean() == 1.0


def _fake_jobs(values):
    """Synthetic job dicts for the evaluation logic: values[(cand, world)] = accuracy of every attacker."""
    jobs = {}
    rng = random.Random(0)
    for (cand, world), acc in values.items():
        ident = {}
        for sc, g in R.SCEN.items():
            lab = [list(c) for c in R.CLASSES for _ in range(4)]
            pr = [l if rng.random() < acc else [(l[0] + 1) % 4, (l[1] + 1) % 4] for l in lab]
            pred = {k: pr for k in ("A6", "A7x1", "A7x2", "A7x4", "A8x1", "A8x2", "A8x4")}
            ident[sc] = {"labels": lab, "pred": pred}
        fam = [{"class": list(c), "uact_planted": 1, "uact_null": 0, "uevent_flag_planted": 1, "uevent_success": 1,
                "uevent_flag_null": 0, "uvol_rho_planted": 0.9, "uvol_rho_null": 0.9, "uratio_err": 0.1}
               for c in R.CLASSES]
        if cand == "M5":
            for f in fam:
                f["uact_planted"] = 0
        jobs[(cand, world)] = {"c_v1": "ok", "identity": ident, "utility": {"families": fam, "w2_truth_failures": 0}}
    return jobs


def test_ic3_17_selection_classes_and_failure_conditions():
    vals = {}
    for w in R.WORLDS:
        vals[("B-LR", w)] = 1.0
        vals[("M1", w)] = 0.3
        vals[("M5", w)] = 0.2
        vals[("M4", w)] = 1.0
    ev = R.evaluate(_fake_jobs(vals), "smoke", None, B=200)
    assert ev["classes"]["M1"] == "P" and ev["classes"]["M5"] == "S"
    assert ev["selection"]["P"]["chosen"] == "M1" and ev["selection"]["S"]["chosen"] == "M5"
    assert "M4" not in ev["selection"]["P"]["ranked"]                 # no identity reduction
    assert ev["fc"]["FC-1_P"] is False and ev["fc"]["FC-1_S"] is False


def test_ic3_18_pareto_within_class_only():
    vals = {(c, w): a for w in R.WORLDS for c, a in (("B-LR", 1.0), ("M1", 0.3), ("M2w1", 0.6), ("M5", 0.2))}
    ev = R.evaluate(_fake_jobs(vals), "smoke", None, B=200)
    assert ev["pareto"]["M2w1"]["dominated_by"] == ["M1"] and ev["pareto"]["M1"]["frontier"]
    assert ev["pareto"]["M5"]["class"] == "S" and ev["pareto"]["M5"]["frontier"]       # not ranked against class P


def test_ic3_19_c_v2_rule_on_b_lr_and_b_af():
    vals = {(c, w): 0.9 for w in R.WORLDS for c in ("B-LR", "B-AF")}
    jobs = _fake_jobs(vals)
    for sc in R.SCEN:                                                  # make A7 much weaker than A6 on B-AF
        idn = jobs[("B-AF", "W1")]["identity"][sc]
        idn["pred"]["A7x4"] = [[(l[0] + 1) % 4, l[1]] for l in idn["labels"]]
    g = R.evaluate(jobs, "smoke", None, B=200)["gates"]["C-V2"]
    assert g["pass"] is False
    assert all(v["pass"] for k, v in g["cells"].items() if k.startswith("B-LR"))


def test_fl029_design_hash_is_line_ending_independent():
    data = (ROOT / "docs/research/RIP3_DESIGN.md").read_bytes().replace(b"\r\n", b"\n")
    assert hashlib.sha256(data.replace(b"\n", b"\r\n").replace(b"\r\n", b"\n")).hexdigest() == FROZEN_DESIGN_SHA


def test_registered_build_check_attempts_of_2026_11_22():
    d = ROOT / "docs/results/rip3_build"
    b1 = json.loads((d / "B1_w2_truth_verification_attempt4.json").read_text())
    assert b1["attempt"] == 4 and b1["all_mc_pass"] and b1["all_accepted"] and b1["all_equivalence_pass"]
    assert len(b1["rows"]) == 10 and b1["block"]["threshold_levels"] == 1_000_000_000
    c10 = [r for r in b1["rows"] if r["case"] == "stress_a0_extreme_s_0.05"][0]
    assert c10["method"] == "blocks" and c10["accepted"] and abs(c10["z"]) <= 4
    assert all(r["method"] == "exact sum" for r in b1["rows"] if r is not c10)
    b2 = json.loads((d / "B2_a6_verification_attempt3.json").read_text())
    assert b2["comparisons"] == 768 and b2["all_pass"]
    assert b2["max_quadrature_abs_diff"] <= 1e-4 and b2["max_algebra_abs_diff_longdouble"] <= 1e-6
    assert b2["precision"]["all_768"]["eps"] <= 1.1e-19
    st = json.loads((d / "DCR01_study_dev.json").read_text())
    assert st["R0_pass_all_gating"] is False and st["R0_failing_gating_cells"] == ["ind|asset", "ind|period", "ind|joint"]
    assert (d / "B1_w2_truth_verification_attempt3.json").exists()            # kept, not counted (FL-031)


def test_review_rb1_evidence():
    d = ROOT / "docs/results/rip3_build"
    hp = json.loads((d / "B1_case10_highprecision.json").read_text())
    assert hp["pass"] and hp["decimal_digits"] >= 50 and hp["abs_diff_float_vs_hp"] + hp["E_hp"] <= 1e-6 * hp["q_hp"]
    st = json.loads((d / "DCR01_study_dev_v2.json").read_text())
    assert st["spec"]["B_primary"] == 100_000 and st["R0_decision_same_for_all_B_and_seeds"]
    assert st["R0_pass_all_gating"] is False
    r2 = (ROOT / "docs/research/RIP3_DESIGN_v0.5r2_DCR01_DRAFT.md").read_text(encoding="utf-8")
    assert "**B = 100,000**" in r2 and "withdrawn as a candidate" in r2


# ---------------- run readiness (OD-S9-17): IC3-23 confirmatory step, IC3-24, authorisation guard ----------------
def test_ic3_23_confirm_cells_come_from_the_evaluation_selection_only():
    ev = {"selection": {"P": {"chosen": "M2w4", "nearest_competitor": "M1"}, "S": {"chosen": "M6", "nearest_competitor": None}}}
    assert R.confirm_cells(ev) == ["B-LR", "M1", "M2w4", "M6"]          # B-LR as reference; no B-AF
    assert "B-AF" not in R.confirm_cells(ev)
    assert R.confirm_cells({"selection": {"P": {"chosen": None}, "S": {"chosen": None}}}) == []
    assert R.confirm_cells({}) == []
    assert "IC3-23" in R.IMPLEMENTATION_CHOICES and "IC3-24" in R.IMPLEMENTATION_CHOICES


def test_ic3_23_floors_must_be_complete_exact_and_readable():
    full = {k: True for k in R.FLOOR_KEYS}
    fl = {w: {"floors": dict(full)} for w in R.WORLDS}
    assert R.class_floors_hold(fl, "P") and R.class_floors_hold(fl, "S")
    for k in R.FLOOR_KEYS:                                                 # any missing floor fails, both classes
        for w in R.WORLDS:
            bad = {x: {"floors": dict(full)} for x in R.WORLDS}
            del bad[w]["floors"][k]
            assert not R.class_floors_hold(bad, "P") and not R.class_floors_hold(bad, "S")
    extra = {w: {"floors": dict(full, extra=True)} for w in R.WORLDS}
    assert not R.class_floors_hold(extra, "P")
    for broken in ({}, None, {"W1": fl["W1"]}, {w: {"floors": {}} for w in R.WORLDS},
                   {w: {"floors": dict(full, uvol="yes")} for w in R.WORLDS}, {w: {} for w in R.WORLDS}):
        assert not R.class_floors_hold(broken, "P") and not R.class_floors_hold(broken, "S")
    no_uact = {w: {"floors": dict(full, uact_power=False)} for w in R.WORLDS}
    assert not R.class_floors_hold(no_uact, "P") and R.class_floors_hold(no_uact, "S")


def test_ic3_23_fc3_is_true_when_a_floor_is_missing():
    ev_vals = {(c, w): a for w in R.WORLDS for c, a in (("B-LR", 1.0), ("M1", 0.3), ("M5", 0.2))}
    ev = R.evaluate(_fake_jobs(ev_vals), "smoke", None, B=200)
    cj = _fake_jobs(ev_vals)
    co = R.evaluate(cj, "smoke", None, B=200)
    assert R.fc3(ev, co, cj)["P"]["fc3"] is False
    for c in ("M1", "M5"):
        for k in R.FLOOR_KEYS:
            co2 = json.loads(json.dumps(co, default=lambda o: o.item() if hasattr(o, "item") else str(o)))
            del co2["floors"][c]["W2"]["floors"][k]
            v = R.fc3(ev, co2, cj)
            K = "P" if c == "M1" else "S"
            assert v[K]["floors_held"] is False and v[K]["fc3"] is True


def test_ic3_23_fc3_verdict_per_class():
    ev_vals = {(c, w): a for w in R.WORLDS for c, a in (("B-LR", 1.0), ("M1", 0.3), ("M5", 0.2))}
    ev = R.evaluate(_fake_jobs(ev_vals), "smoke", None, B=200)
    assert ev["selection"]["P"]["chosen"] == "M1" and ev["selection"]["S"]["chosen"] == "M5"
    # confirmed: the reductions and floors reproduce
    cj = _fake_jobs(ev_vals)
    co = R.evaluate(cj, "smoke", None, B=200)
    v = R.fc3(ev, co, cj)
    assert v["P"]["fc3"] is False and v["P"]["reproduced_reduction"] and v["P"]["floors_held"] and v["P"]["c_v1_ok"]
    assert v["S"]["fc3"] is False                                        # U-act power is not a class-S floor
    # not confirmed: M1 no longer reduces identity
    cj2 = _fake_jobs({(c, w): a for w in R.WORLDS for c, a in (("B-LR", 1.0), ("M1", 1.0), ("M5", 0.2))})
    v2 = R.fc3(ev, R.evaluate(cj2, "smoke", None, B=200), cj2)
    assert v2["P"]["fc3"] is True and not v2["P"]["reproduced_reduction"]
    # a generator failure on the confirm set makes FC-3 true for that class
    cj3 = _fake_jobs(ev_vals)
    cj3[("B-LR", "W2")]["c_v1"] = "FAIL: test"
    v3 = R.fc3(ev, R.evaluate(cj3, "smoke", None, B=200), cj3)
    assert v3["P"]["c_v1_ok"] is False and v3["P"]["fc3"] is True
    # no chosen candidate: no verdict
    assert R.fc3({"selection": {"P": {"chosen": None}, "S": {"chosen": None}}}, co, cj)["P"]["fc3"] is None


def test_ic3_24_job_files_are_written_atomically(tmp_path):
    p = tmp_path / "smoke__X__W1.json"
    R._atomic_write(p, '{"a": 1}')
    R._atomic_write(p, '{"a": 2}')
    assert json.loads(p.read_text()) == {"a": 2}
    assert not list(tmp_path.glob("*.tmp"))


def _git(cwd, *args):
    import subprocess
    p = subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@invalid", "-c", "commit.gpgsign=false",
                        *args], cwd=cwd, capture_output=True, text=True)
    assert p.returncode == 0, p.stderr
    return p.stdout.strip()


def _record(tmp_path, run, entry, heading="RIP-3 RUN", scope=None, msg="record"):
    dec, reg = tmp_path / "docs/DECISIONS.md", tmp_path / run.REGISTRY
    h = scope if scope is not None else run.scope_sha256(entry)
    dec.write_text(f"# Decisions\n\n## Founder authorisation {entry['id']} — {heading}\nscope sha256: {h}\n\n## Other\nx\n",
                   encoding="utf-8")
    reg.write_text(json.dumps({"authorisations": [entry]}), encoding="utf-8")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-q", "-m", msg)


def _approved_repo(tmp_path, run):
    (tmp_path / "docs/research").mkdir(parents=True)
    (tmp_path / "docs/DECISIONS.md").write_text("# Decisions\n", encoding="utf-8")
    (tmp_path / run.REGISTRY).write_text(json.dumps({"authorisations": []}), encoding="utf-8")
    (tmp_path / "code.py").write_text("x = 1\n")
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-q", "-m", "approved")
    return _git(tmp_path, "rev-parse", "HEAD"), _git(tmp_path, "rev-parse", "HEAD^{tree}")


def test_run_authorisation_guard_needs_a_recorded_matching_decision(tmp_path):
    run = _script("rip3_run")
    commit, tree = _approved_repo(tmp_path, run)
    with pytest.raises(SystemExit, match="not recorded"):
        run.check_authorisation(tmp_path, "OD-TEST-1", "eval")
    entry = {"id": "OD-TEST-1", "sets": ["eval"], "approved_commit": commit, "approved_tree": tree}
    _record(tmp_path, run, entry, heading="preparation only")             # not a RUN decision
    with pytest.raises(SystemExit, match="'RIP-3 RUN' heading"):
        run.check_authorisation(tmp_path, "OD-TEST-1", "eval")
    _record(tmp_path, run, entry, scope="0" * 64)                         # section does not state the scope hash
    with pytest.raises(SystemExit, match="scope sha256"):
        run.check_authorisation(tmp_path, "OD-TEST-1", "eval")


def test_run_authorisation_guard_accepts_an_unchanged_recorded_scope(tmp_path):
    run = _script("rip3_run")
    commit, tree = _approved_repo(tmp_path, run)
    entry = {"id": "OD-TEST-1", "sets": ["eval"], "approved_commit": commit, "approved_tree": tree}
    _record(tmp_path, run, entry)
    ok = run.check_authorisation(tmp_path, "OD-TEST-1", "eval")
    assert ok["approved_commit"] == commit and ok["head"] != commit and ok["scope_sha256"] == run.scope_sha256(entry)
    with pytest.raises(SystemExit, match="does not cover"):
        run.check_authorisation(tmp_path, "OD-TEST-1", "confirm")
    with pytest.raises(SystemExit, match="RUN authorisation identifier"):
        run.check_authorisation(tmp_path, "", "eval")
    (tmp_path / "docs/DECISIONS.md").write_text("tampered, not committed\n", encoding="utf-8")
    assert run.check_authorisation(tmp_path, "OD-TEST-1", "eval")["recorded_in"]   # only committed HEAD is read


def test_run_authorisation_guard_refuses_a_scope_widened_after_recording(tmp_path):
    run = _script("rip3_run")
    commit, tree = _approved_repo(tmp_path, run)
    entry = {"id": "OD-TEST-1", "sets": ["eval"], "approved_commit": commit, "approved_tree": tree}
    _record(tmp_path, run, entry)
    wider = dict(entry, sets=["eval", "confirm"])                         # both files rewritten consistently
    _record(tmp_path, run, wider, msg="widen")
    with pytest.raises(SystemExit, match="changed since it was recorded"):
        run.check_authorisation(tmp_path, "OD-TEST-1", "confirm")
    with pytest.raises(SystemExit, match="changed since it was recorded"):
        run.check_authorisation(tmp_path, "OD-TEST-1", "eval")


def test_run_authorisation_guard_refuses_an_edited_decision_or_bad_sets_or_code(tmp_path):
    run = _script("rip3_run")
    commit, tree = _approved_repo(tmp_path, run)
    entry = {"id": "OD-TEST-1", "sets": ["eval"], "approved_commit": commit, "approved_tree": tree}
    _record(tmp_path, run, entry)
    dec = tmp_path / "docs/DECISIONS.md"
    dec.write_text(dec.read_text(encoding="utf-8").replace("scope sha256:", "Also confirm. scope sha256:"), encoding="utf-8")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-q", "-m", "edit the decision text")
    with pytest.raises(SystemExit, match="section of OD-TEST-1 changed"):
        run.check_authorisation(tmp_path, "OD-TEST-1", "eval")
    commit2 = _git(tmp_path, "rev-parse", "HEAD")
    tree2 = _git(tmp_path, "rev-parse", "HEAD^{tree}")
    bad = {"id": "OD-TEST-2", "sets": ["eval", "dev"], "approved_commit": commit2, "approved_tree": tree2}
    _record(tmp_path, run, bad)
    with pytest.raises(SystemExit, match="invalid sets"):
        run.check_authorisation(tmp_path, "OD-TEST-2", "eval")
    good = {"id": "OD-TEST-3", "sets": ["eval"], "approved_commit": commit2, "approved_tree": tree2}
    _record(tmp_path, run, good)
    (tmp_path / "code.py").write_text("x = 2\n")                       # code changed after the approval
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-q", "-m", "change code")
    with pytest.raises(SystemExit, match="outside the authorisation records"):
        run.check_authorisation(tmp_path, "OD-TEST-3", "eval")


def _registry_problems(registry_text, decisions_text, run):
    """FL-035: consistency of the RUN-authorisation registry with docs/DECISIONS.md, read from file contents only (no
    git history, so it holds on a parentless sandbox snapshot too). Every entry is a single object with exactly the
    scope keys, a unique id, valid sets and full commit / tree ids. Identifiers are compared whole: each 'RIP-3 RUN'
    Markdown heading (any level H1–H6) must be the H2 '## Founder authorisation <id> — …', and its <id> must equal a recorded id exactly. Each entry has
    exactly one such heading, the guard's own lookup finds that same section, and the section holds exactly one line
    that is, character for character, 'scope sha256: <hash of the entry>'. Returns the problems ([] = consistent).
    The history checks (approved commit, records-only descendant, one recording commit) stay in check_authorisation."""
    import re
    try:
        entries = json.loads(registry_text)["authorisations"]
    except (ValueError, KeyError, TypeError):
        return ["registry is not an object with an 'authorisations' list"]
    if not isinstance(entries, list):
        return ["registry is not an object with an 'authorisations' list"]
    problems, ids = [], [e.get("id") if isinstance(e, dict) else None for e in entries]
    lines = decisions_text.splitlines()
    heads = []                                     # (line number, identifier taken from the heading, None if malformed)
    for n, ln in enumerate(lines):
        if re.match(r"#{1,6}[ \t]", ln) and "RIP-3 RUN" in ln:         # any Markdown heading level H1–H6
            m = re.match(r"## Founder authorisation (\S+) — ", ln)          # only this H2 form is accepted
            heads.append((n, m.group(1) if m else None))
    for e, i in zip(entries, ids):
        if not isinstance(i, str) or not i:
            problems.append(f"entry without an id: {e!r}")
            continue
        if ids.count(i) != 1:
            problems.append(f"{i}: recorded {ids.count(i)} times")
            continue
        if set(e) != {"id", "sets", "approved_commit", "approved_tree"}:
            problems.append(f"{i}: keys {sorted(e)} are not exactly the scope keys")
        s = e.get("sets")
        if (not isinstance(s, list) or not s or not all(isinstance(x, str) for x in s) or len(set(s)) != len(s)
                or not set(s) <= {"eval", "confirm"}):
            problems.append(f"{i}: invalid sets {s!r}")
        for k in ("approved_commit", "approved_tree"):
            if not isinstance(e.get(k), str) or not re.fullmatch(r"[0-9a-f]{40}", e[k]):
                problems.append(f"{i}: {k} is not a full 40-hex id")
        mine = [n for n, h in heads if h == i]                       # headings whose identifier is exactly i
        if len(mine) != 1:
            problems.append(f"{i}: {len(mine)} 'RIP-3 RUN' headings with exactly this identifier (need 1)")
            continue
        end = next((k for k in range(mine[0] + 1, len(lines)) if lines[k].startswith("## ")), len(lines))
        sec = "\n".join(lines[mine[0]:end]).rstrip()
        if run._decision_section(decisions_text, i) != sec:               # the guard must find this same section
            problems.append(f"{i}: the guard's section lookup does not find exactly its own heading")
        scope_lines = [ln for ln in lines[mine[0]:end] if ln.startswith("scope sha256:")]
        if scope_lines != [f"scope sha256: {run.scope_sha256(e)}"]:
            problems.append(f"{i}: its section needs exactly one line 'scope sha256: <hash of the entry>', "
                            f"found {scope_lines!r}")
    for n, h in heads:
        if h is None:
            problems.append(f"'RIP-3 RUN' heading not of the form '## Founder authorisation <id> — …': {lines[n]}")
        elif h not in ids:
            problems.append(f"'RIP-3 RUN' heading without a registry entry: {lines[n]}")
    return problems


def test_run_authorisation_registry_is_consistent_with_the_decisions():
    """Replaces test_no_run_authorisation_exists_in_the_repository (FL-035): that test pinned an empty registry, so it
    would fail at the very commit that records a founder authorisation and stop the pre-flight of the run protocol
    (§3.3). The registry may hold entries, but only consistent ones; a set no entry covers is still refused."""
    run = _script("rip3_run")
    reg_text = (ROOT / run.REGISTRY).read_text(encoding="utf-8")
    dec_text = (ROOT / "docs/DECISIONS.md").read_text(encoding="utf-8")
    assert _registry_problems(reg_text, dec_text, run) == []
    entries = json.loads(reg_text)["authorisations"]
    for e in entries:                                       # a set outside an entry's scope is refused, e.g. confirm
        for set_name in {"eval", "confirm"} - set(e["sets"]):
            with pytest.raises(SystemExit, match="does not cover"):
                run.check_authorisation(ROOT, e["id"], set_name)
    for set_name in ("eval", "confirm"):                    # identifiers with no entry are refused
        for auth_id in ("OD-S9-17", "OD-UNRECORDED"):
            if auth_id not in {e["id"] for e in entries}:
                with pytest.raises(SystemExit, match="not recorded"):
                    run.check_authorisation(ROOT, auth_id, set_name)


def test_run_authorisation_registry_consistency_check_cases():
    run = _script("rip3_run")
    c, t = "a" * 40, "b" * 40

    def entry(i="OD-T-1", sets=("eval",)):
        return {"id": i, "sets": list(sets), "approved_commit": c, "approved_tree": t}

    def reg(*es):
        return json.dumps({"note": "n", "authorisations": list(es)})

    def dec(*sections):
        return "# Decisions\n\n" + "".join(f"## Founder authorisation {i} — RIP-3 RUN\nscope sha256: {h}\n\n"
                                           for i, h in sections) + "## Other\nx\n"

    ev, both = entry(), entry(sets=("eval", "confirm"))
    ok = _registry_problems
    assert ok(reg(), "# Decisions\n", run) == []                                         # empty registry
    assert ok(reg(ev), dec(("OD-T-1", run.scope_sha256(ev))), run) == []                 # eval only, matching
    assert ok(reg(both), dec(("OD-T-1", run.scope_sha256(both))), run) == []             # both sets, matching
    bad = {
        "wrong hash": (reg(ev), dec(("OD-T-1", "0" * 64))),
        "scope widened, old hash": (reg(both), dec(("OD-T-1", run.scope_sha256(ev)))),
        "entry, no section": (reg(ev), "# Decisions\n"),
        "section, no entry": (reg(), dec(("OD-T-1", run.scope_sha256(ev)))),
        "two sections": (reg(ev), dec(("OD-T-1", run.scope_sha256(ev)), ("OD-T-1", run.scope_sha256(ev)))),
        "entry twice": (reg(ev, ev), dec(("OD-T-1", run.scope_sha256(ev)))),
        "registered seed as set": (reg(entry(sets=("6201",))), dec(("OD-T-1", run.scope_sha256(entry(sets=("6201",)))))),
        "no sets": (reg(entry(sets=())), dec(("OD-T-1", run.scope_sha256(entry(sets=()))))),
        "set repeated": (reg(entry(sets=("eval", "eval"))), dec(("OD-T-1", run.scope_sha256(entry(sets=("eval", "eval")))))),
        "short commit": (reg(dict(ev, approved_commit="fdf4508")), dec(("OD-T-1", run.scope_sha256(dict(ev, approved_commit="fdf4508"))))),
        "extra key": (reg(dict(ev, run_now=True)), dec(("OD-T-1", run.scope_sha256(ev)))),
        "not a registry": ("[]", "# Decisions\n"),
        "not json": ("{", "# Decisions\n"),
        # review of the proposal, point 1: the scope line must be a separate line equal to the computed hash
        "hash inside a list item": (reg(ev), dec(("OD-T-1", run.scope_sha256(ev))).replace("scope sha256:", "- scope sha256:")),
        "hash line with extra text": (reg(ev), dec(("OD-T-1", run.scope_sha256(ev) + " (draft)"))),
        "hash as a prefix of a longer value": (reg(ev), dec(("OD-T-1", run.scope_sha256(ev) + "0"))),
        "a second scope line": (reg(ev), dec(("OD-T-1", run.scope_sha256(ev) + "\nscope sha256: " + "0" * 64))),
        # review of the proposal, point 2: identifiers are compared whole, not as substrings of the heading
        "orphan heading whose id extends a recorded id": (reg(ev), dec(("OD-T-1", run.scope_sha256(ev)),
                                                                        ("OD-T-10", run.scope_sha256(ev)))),
        "only a heading for a longer id": (reg(ev), dec(("OD-T-10", run.scope_sha256(ev)))),
        "orphan heading that mentions a recorded id": (
            reg(ev), dec(("OD-T-1", run.scope_sha256(ev))) + "\n## Founder authorisation OD-T-9 — RIP-3 RUN after OD-T-1\n"),
        "malformed RIP-3 RUN heading": (reg(ev), dec(("OD-T-1", run.scope_sha256(ev))) + "\n## RIP-3 RUN OD-T-1\n"),
        # review of v2: an orphan 'RIP-3 RUN' heading at another Markdown level is found too
        "orphan H3 heading": (reg(ev), dec(("OD-T-1", run.scope_sha256(ev))) + "\n### Founder authorisation OD-T-9 — RIP-3 RUN\n"),
        "orphan H1 heading": (reg(ev), dec(("OD-T-1", run.scope_sha256(ev))) + "\n# Founder authorisation OD-T-9 — RIP-3 RUN\n"),
        "orphan H6 heading": (reg(ev), dec(("OD-T-1", run.scope_sha256(ev))) + "\n###### Founder authorisation OD-T-9 — RIP-3 RUN\n"),
        "the entry's own heading at H3": (reg(ev), dec(("OD-T-1", run.scope_sha256(ev))).replace("## Founder", "### Founder")),
    }
    for name, (r, d) in bad.items():
        assert ok(r, d, run), name


def test_run_script_refuses_an_unrecorded_authorisation(tmp_path):
    import subprocess
    import sys
    for set_name in ("eval", "confirm"):
        p = subprocess.run([sys.executable, str(ROOT / "scripts/rip3_run.py"), str(tmp_path / "o"), set_name,
                            "--authorisation", "OD-ANY-TEXT"], capture_output=True, text=True)
        assert p.returncode != 0 and "not recorded" in (p.stderr + p.stdout)
    assert not list((tmp_path / "o").glob("*__*.json")) if (tmp_path / "o").exists() else True


def test_confirm_needs_the_hash_checked_evaluation_result(tmp_path):
    run = _script("rip3_run")
    with pytest.raises(SystemExit, match="eval_results"):
        run.load_eval_results(tmp_path)
    blob = json.dumps({"selection": {"P": {"chosen": "M1", "nearest_competitor": None}}})
    (tmp_path / "eval_results.json").write_text(blob)
    (tmp_path / "eval_results.sha256").write_text("0" * 64 + "  eval_results.json\n")
    with pytest.raises(SystemExit, match="does not match"):
        run.load_eval_results(tmp_path)
    (tmp_path / "eval_results.sha256").write_text(hashlib.sha256(blob.encode()).hexdigest() + "  eval_results.json\n")
    assert R.confirm_cells(run.load_eval_results(tmp_path)) == ["B-LR", "M1"]


def test_ic3_25_select_never_uses_missing_extra_or_unreadable_floors():
    vals = {(c, w): a for w in R.WORLDS for c, a in (("B-LR", 1.0), ("M1", 0.3), ("M2w4", 0.4), ("M5", 0.2))}
    out = R.evaluate(_fake_jobs(vals), "smoke", None, B=200)
    cands = [c for c in R.ALL_CELLS if c in out["floors"]]
    base = R.select(out, cands)
    # complete floors: unchanged behaviour (classes, ranking, choice)
    assert base["selection"]["P"]["chosen"] == "M1" and base["selection"]["P"]["nearest_competitor"] == "M2w4"
    assert base["selection"]["S"]["chosen"] == "M5" and base["classes"]["M1"] == "P" and base["classes"]["M5"] == "S"
    assert R.floors_complete(out["floors"]["M1"]) and R.floors_complete(out["floors"]["M5"])

    def broken(mutate):
        o = json.loads(json.dumps(out, default=lambda x: x.item() if hasattr(x, "item") else str(x)))
        mutate(o["floors"]["M1"])
        return R.select(o, cands)

    for k in R.FLOOR_KEYS:                                          # a missing floor in either world
        for w in R.WORLDS:
            r = broken(lambda f: f[w]["floors"].pop(k))
            assert r["classes"]["M1"] == "floors incomplete (not in the selection)"
            assert "M1" not in r["selection"]["P"]["ranked"] and r["selection"]["P"]["chosen"] == "M2w4"
    for mut in (lambda f: f.pop("W2"),                               # a missing world
                lambda f: f["W1"]["floors"].update(extra=True),       # an extra floor
                lambda f: f["W2"]["floors"].update(uvol="yes"),       # an unreadable value
                lambda f: f["W1"].update(floors=[])):                 # not a mapping
        r = broken(mut)
        assert r["classes"]["M1"] == "floors incomplete (not in the selection)"
        assert "M1" not in r["selection"]["P"]["ranked"] + r["selection"]["S"]["ranked"]
    assert "IC3-25" in R.IMPLEMENTATION_CHOICES


def test_run_authorisation_guard_needs_entry_and_decision_in_the_same_commit(tmp_path):
    run = _script("rip3_run")
    commit, tree = _approved_repo(tmp_path, run)
    entry = {"id": "OD-TEST-1", "sets": ["eval"], "approved_commit": commit, "approved_tree": tree}
    (tmp_path / run.REGISTRY).write_text(json.dumps({"authorisations": [entry]}), encoding="utf-8")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-q", "-m", "registry entry alone")            # no decision section yet
    _record(tmp_path, run, entry, msg="decision added later")
    with pytest.raises(SystemExit, match="section of OD-TEST-1 changed since it was recorded"):
        run.check_authorisation(tmp_path, "OD-TEST-1", "eval")


def test_run_authorisation_guard_refuses_a_decision_recorded_before_its_entry(tmp_path):
    run = _script("rip3_run")
    commit, tree = _approved_repo(tmp_path, run)
    entry = {"id": "OD-TEST-1", "sets": ["eval"], "approved_commit": commit, "approved_tree": tree}
    dec = tmp_path / "docs/DECISIONS.md"
    dec.write_text(f"# Decisions\n\n## Founder authorisation OD-TEST-1 — RIP-3 RUN\nscope sha256: {run.scope_sha256(entry)}"
                   "\n\n## Other\nx\n", encoding="utf-8")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-q", "-m", "decision section alone")          # the reversed order
    _record(tmp_path, run, entry, msg="registry entry added later")         # same section text, entry added now
    with pytest.raises(SystemExit, match="must be added together in one commit"):
        run.check_authorisation(tmp_path, "OD-TEST-1", "eval")


def test_run_authorisation_guard_accepts_entry_and_decision_added_together(tmp_path):
    run = _script("rip3_run")
    commit, tree = _approved_repo(tmp_path, run)
    entry = {"id": "OD-TEST-1", "sets": ["eval", "confirm"], "approved_commit": commit, "approved_tree": tree}
    _record(tmp_path, run, entry, msg="entry and decision in one commit")
    r = run.check_authorisation(tmp_path, "OD-TEST-1", "confirm")
    assert r["recorded_in"] == _git(tmp_path, "rev-parse", "HEAD") and r["sets"] == ["eval", "confirm"]


def _select_reference_pre_ic3_25(out, cands):
    """select() exactly as accepted at RIP-3 BUILD (main a7579fe), kept here only to prove that IC3-25 changes nothing
    when the floors are complete."""
    M = {(r["candidate"], r["world"], r["scenario"]): r for r in out["matrix"]}
    red, cls, passes = {}, {}, {}
    for c in cands:
        if c in ("B-LR", R.CONTROL):
            continue
        ok = {}
        for t in R.TARGETS:
            ok[t] = all((c, w, sc) in M and M[(c, w, sc)][f"reduction_{t}"]["ci95"][0] > 0
                        for w in R.WORLDS for sc in ("ind", "g16"))
        g16 = [M[(c, w, "g16")]["reduction_joint"]["diff"] for w in R.WORLDS if (c, w, "g16") in M]
        red[c] = {"reduces": ok, "rank_value_g16_joint": min(g16) if g16 else None}
        fl = out["floors"].get(c, {})
        if c in R.LEVEL_CANDS or not fl or any("floors" not in fl[w] for w in fl):
            cls[c] = "baseline (not in the selection)"
            continue
        p_ok = all(fl[w]["floors"]["uact_power"] for w in fl)
        others = all(all(v for k, v in fl[w]["floors"].items() if k != "uact_power") for w in fl)
        cls[c] = "P" if p_ok else "S"
        passes[c] = others and (p_ok or cls[c] == "S")
    sel, fc = {}, {}
    cv2 = out["gates"].get("C-V2", {}).get("pass")
    for K in ("P", "S"):
        pool = [c for c in cls if cls[c] == K and passes.get(c) and red[c]["reduces"]["joint"]]
        if cv2 is False:
            pool = [c for c in pool if c in R.A6_TRACTABLE]
        pool.sort(key=lambda c: (-red[c]["rank_value_g16_joint"], R._simplicity(c)))
        sel[K] = {"chosen": pool[0] if pool else None, "nearest_competitor": pool[1] if len(pool) > 1 else None,
                  "ranked": pool}
        fc[f"FC-1_{K}"] = not pool
    fc["FC-2"] = [c for c in red if c not in R.LEVEL_CANDS and not red[c]["reduces"]["joint"] and
                  all((c, "W1", sc) in M and M[(c, "W1", sc)]["reduction_joint"]["ci95"][0] > 0 for sc in ("ind", "g16"))]
    fc["FC-4"] = cv2 is False
    fc["FC-5"] = [r["candidate"] + "|" + r["world"] + "|" + r["scenario"] for r in out["matrix"] if any(r["unsaturated"].values())]
    fc["FC-6"] = [r["candidate"] + "|" + r["world"] + "|" + r["scenario"] for r in out["matrix"] if r["attacker_sensitive"]]
    return {"reductions": red, "classes": cls, "selection": sel, "fc": fc, "pareto": R.pareto(out, cls)}


def test_ic3_25_select_is_unchanged_when_floors_are_complete():
    accs = {"B-LR": 1.0, "B-AF": 0.95, "M1": 0.3, "M2w1": 0.6, "M2w2": 0.45, "M2w4": 0.4, "M3W32": 0.35, "M4": 1.0,
            "M5": 0.2, "M6": 0.25}
    cases = []
    jobs = _fake_jobs({(c, w): a for w in R.WORLDS for c, a in accs.items()})
    cases.append(jobs)                                                     # mixed P / S, ranking and baselines
    jobs2 = _fake_jobs({(c, w): a for w in R.WORLDS for c, a in accs.items()})
    for f in jobs2[("M1", "W2")]["utility"]["families"]:
        f["uevent_success"] = 0                                            # M1 fails a non-U-act floor in W2 only
    for f in jobs2[("M6", "W1")]["utility"]["families"]:
        f["uratio_err"] = 5.0                                              # M6 (class S) fails U-ratio in W1
    cases.append(jobs2)
    jobs3 = _fake_jobs({(c, w): a for w in R.WORLDS for c, a in accs.items()})
    for f in jobs3[("M2w4", "W1")]["utility"]["families"]:
        f["uact_planted"] = 0                                              # M2w4 loses U-act in one world -> class S
    cases.append(jobs3)
    for jb in cases:
        out = R.evaluate(jb, "smoke", None, B=200)
        cands = [c for c in R.ALL_CELLS if (c, "W1") in jb]
        for cv2 in (None, False, True):                                    # also the FC-4 path (A6-tractable pool)
            o = dict(out, gates=dict(out["gates"], **{"C-V2": {"pass": cv2}}))
            assert all(R.floors_complete(o["floors"][c]) for c in o["floors"])
            new, ref = R.select(o, cands), _select_reference_pre_ic3_25(o, cands)
            assert new == ref                                              # reductions, classes, ranked, chosen, fc, pareto
    o2 = R.evaluate(cases[1], "smoke", None, B=200)
    assert o2["classes"]["M1"] == "P" and "M1" not in o2["selection"]["P"]["ranked"]   # the floor failure counts
    assert "M6" not in o2["selection"]["S"]["ranked"]
