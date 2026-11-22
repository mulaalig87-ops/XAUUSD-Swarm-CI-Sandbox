"""RIP-2 — leakage diagnosis. SYNTHETIC ONLY. Design: docs/research/RIP2_DESIGN.md v0.7, frozen by FD-01-D46.
BUILD ONLY: running the experiment needs the code review and a separate go (FD-01-D46). Opens no gate.

Every place where the design is silent and the code had to choose is listed in IMPLEMENTATION_CHOICES and in
docs/research/RIP2_BUILD_NOTES.md (founder condition 6: no silent difference between design and code).

Sections: world and families (§3, §4a) · conditions (§4) · attackers (§5) · A6 incl. ablation (§5, §7) ·
estimands and stratified paired bootstrap (§6) · feature-group ablation and family-level permutation (§7) ·
research-utility baseline U-vol / U-act / U-event (§8) · run().
"""
from __future__ import annotations

import math
import random

import numpy as np

from . import reid
from . import rip1_attack as A

REPS = list(A.REPS)                         # activity_time ≡ log_returns in this world (RIP-1 alias, kept)
SCEN = dict(A.SCEN)
CLASSES = list(A.CLASSES)
SEEDS = {"dev": 5101, "eval": 5102, "util_planted": 5103, "util_null": 5104, "bootstrap": 5201, "perm": 5202}
SPEC = {"n": 512, "fpc": {"ind": 25, "g4": 10, "g16": 5}, "util_fpc": 25, "B": 2000, "perm_repeats": 50,
        "grid": 257, "tau_range": (128, 384), "uvol_window": 32, "uact_len": 448, "uact_k": 7,
        "uevent_crit": 1.358, "uevent_tol": 16, "truth_nsigma": 12}
COMPONENTS = ["mu", "sigma", "act", "Lg"]
TICKS = sorted({a["tick"] for a in reid.ASSETS})
IMPLEMENTATION_CHOICES = {
    "IC-01": "Each seed stream yields, per family in class order (asset, period) then family index: the secret draw "
             "(rip1_attack.draw: c, a, b, m), then tau (randint 128..384, drawn in every world so streams align), then "
             "the n standard-normal draws of each member in member order.",
    "IC-02": "Seed 5103 gives the planted U-vol/U-event world (shift) and, from the SAME normal draws without the "
             "shift, the planted U-act world (= RIP-1 world). Seed 5104 gives the null U-vol/U-event world (no shift) "
             "and, from the same draws with act = 0, the null U-act world. Paired worlds per seed.",
    "IC-03": "Δ one-hot (3 tick values) appended to the A1/A2/A4 feature vector when Δ is shown; standardised with "
             "the other columns. A3 never sees Δ.",
    "IC-04": "A6 component ablation is computed in every scenario (ind, g4, g16); the design does not restrict it.",
    "IC-05": "Feature-group ablation and permutation importance are computed in C2 with Δ hidden (the operational "
             "case); the design does not name the condition. Groups follow the reid.features docstring.",
    "IC-06": "U-event: σ̂_s is the population standard deviation (ddof = 0) of s_t, t = 1..511.",
    "IC-07": "Bootstrap index sets: numpy default_rng(5201), drawn per scenario in the order ind, g4, g16, B sets "
             "each, stratified by class; the same sets serve every compared condition and the utility measures (ind).",
    "IC-08": "Permutations: numpy default_rng(5202), drawn in the order scenario × representation × group × repeat "
             "(the loop order of run() and _feature_groups(); tested).",
    "IC-09": "A6 under C0 and under C1 for affine_level (a = 1, b = 0, so x = P) use the price likelihood "
             "(lognormal P_0 around Lg, Gaussian log returns, Jacobians); C1 tick_grid uses c = 0 and C1 "
             "level_residual uses m = 100 x tick_k of the CLASS, no integration.",
    "IC-10": "Within-Δ-group results use the Δ-shown predictions; the group-pooled-prior variant differs from AP only "
             "for tick_grid in C2 (c prior), and is computed only there; elsewhere it is reported as identical.",
    "IC-12": "level_residual likelihood: the wrapped-normal sum is computed exactly for every increment — dual "
             "(Poisson summation) series when S/m > 0.5, otherwise the direct sum centred on the nearest image. The "
             "RIP-1 code centres the direct sum on j = 0 and drops mass for large |d| (FL-023); RIP-2 uses the exact "
             "sum (tested against a brute-force wide sum). The support of the transform, x in [0, m), is enforced (FL-024).",
    "IC-11": "Development families use seed 5101 + 1000·g and evaluation families 5102 + 1000·g (g = 1, 4, 16), so the "
             "scenarios do not share paths; utility families use 5103 / 5104 directly (S-ind only).",
}


# ---------------- world (§3, §4a) ----------------
def path_from_normals(asset, period, z, tau=None, act_zero=False):
    """The reid.simulate step expression on given normal draws: latent prices and observed (rounded) prices.
    With tau=None and act_zero=False this is bit-identical to reid.simulate (tested)."""
    a, p = reid.ASSETS[asset], reid.PERIODS[period]
    price = a["level"] * p["growth"]
    lat, obs = [], []
    for t, zt in enumerate(z):
        act = 1 + (0 if act_zero else a["act"]) * math.sin(2 * math.pi * t / 64)
        step = a["vol"] * p["volx"] * act * zt
        if tau is not None and t >= tau:
            step = step * 2
        price *= math.exp(a["drift"] + step)
        lat.append(price)
        obs.append(round(round(price / a["tick"]) * a["tick"], 10))
    return lat, obs


def make_families(seed, fpc, g, n=None):
    """IC-01. Returns a list of dicts: class, prm (secret draw), tau, z (list of normal vectors, one per member)."""
    n = n or SPEC["n"]
    rnd = random.Random(seed)
    fams = []
    for (a, p) in CLASSES:
        for i in range(fpc):
            prm = A.draw(a, rnd)
            tau = rnd.randint(*SPEC["tau_range"])
            z = [[rnd.gauss(0, 1) for _ in range(n)] for _ in range(g)]
            fams.append({"cls": (a, p), "idx": i, "prm": prm, "tau": tau, "z": z})
    return fams


def canonical_params(asset):
    return {"c": 0.0, "a": 1.0, "b": 0.0, "m": 100 * reid.ASSETS[asset]["tick"]}


def represent(rep, cond, obs, asset, prm):
    """§4: C0 raw observed prices; C1 asset-conditioned public canonical; C2 secret draw."""
    if cond == "C0":
        return list(obs)
    return A.blind(rep, obs, asset, canonical_params(asset) if cond == "C1" else prm)


def pooled_values():
    """§4a / §7 rule from the public table: arithmetic mean over 16 classes for mu and act, geometric for sigma, Lg."""
    mu = [reid.ASSETS[a]["drift"] for a, p in CLASSES]
    act = [reid.ASSETS[a]["act"] for a, p in CLASSES]
    sig = [reid.ASSETS[a]["vol"] * reid.PERIODS[p]["volx"] for a, p in CLASSES]
    lg = [reid.ASSETS[a]["level"] * reid.PERIODS[p]["growth"] for a, p in CLASSES]
    geo = lambda v: math.exp(sum(math.log(x) for x in v) / len(v))     # noqa: E731
    return {"mu": sum(mu) / 16, "act": sum(act) / 16, "sigma": geo(sig), "Lg": geo(lg)}


# ---------------- attackers A1, A2, A4 with optional Δ one-hot (§5) ----------------
def onehot(delta):
    return [1.0 if math.isclose(delta, t, rel_tol=1e-12) else 0.0 for t in TICKS]


def _feat(x, delta=None):
    f = reid.features(x)
    return f + onehot(delta) if delta is not None else f


def a1_a2(dev_f, dev_y, test_f):
    """reid.attack A1/A2 on precomputed features (identical to reid.attack when no one-hot; tested)."""
    z = reid._standardiser(dev_f)
    dz = [z(f) for f in dev_f]
    tz = [z(f) for f in test_f]
    a1 = [reid._nn(dz, dev_y, q) for q in tz]
    classes = sorted(set(dev_y))
    k = len(dz[0])
    cents = {c: [sum(r[j] for r, y in zip(dz, dev_y) if y == c) / sum(1 for y in dev_y if y == c) for j in range(k)]
             for c in classes}
    a2 = [min(classes, key=lambda c: sum((u - v) ** 2 for u, v in zip(cents[c], q))) for q in tz]
    return a1, a2


def a4_feats(dev_ff, dev_y, test_ff):
    """rip1_attack.a4 on precomputed per-member features (identical to A.a4 when no one-hot; tested)."""
    z = reid._standardiser([f for fs in dev_ff for f in fs])
    dz = [[z(f) for f in fs] for fs in dev_ff]
    k = len(dz[0][0])
    gm = [[sum(f[j] for f in fs) / len(fs) for j in range(k)] for fs in dz]
    cent_g = {c: [sum(m[j] for m, y in zip(gm, dev_y) if y == c) / dev_y.count(c) for j in range(k)] for c in CLASSES}
    flat = [(f, y) for fs, y in zip(dz, dev_y) for f in fs]
    cent_s = {c: [sum(f[j] for f, y in flat if y == c) / sum(1 for _, y in flat if y == c) for j in range(k)]
              for c in CLASSES}
    out_a, out_b = [], []
    for fs in test_ff:
        tz = [z(f) for f in fs]
        m = [sum(f[j] for f in tz) / len(tz) for j in range(k)]
        out_a.append(min(CLASSES, key=lambda c: (A._dist2(cent_g[c], m), CLASSES.index(c))))
        votes = [min(CLASSES, key=lambda c: (A._dist2(cent_s[c], f), CLASSES.index(c))) for f in tz]
        top = max(votes.count(c) for c in set(votes))
        tied = [c for c in CLASSES if votes.count(c) == top]
        out_b.append(min(tied, key=lambda c: (sum(A._dist2(cent_s[c], f) for f in tz), CLASSES.index(c))))
    return out_a, out_b


# ---------------- A6 (§5, §7) ----------------
def class_params(c, pooled=(), pv=None):
    """Generator components of class c, with the components in `pooled` replaced by their pooled values.
    Priors and the transform's asset-conditioning (L for the c prior, tick) stay at the class's asset."""
    pv = pv or pooled_values()
    a, p = c
    A_, P_ = reid.ASSETS[a], reid.PERIODS[p]
    mu = pv["mu"] if "mu" in pooled else A_["drift"]
    sig = pv["sigma"] if "sigma" in pooled else A_["vol"] * P_["volx"]
    act = pv["act"] if "act" in pooled else A_["act"]
    lg = pv["Lg"] if "Lg" in pooled else A_["level"] * P_["growth"]
    t = np.arange(SPEC["n"])
    return {"mu": mu, "s": sig * (1 + act * np.sin(2 * np.pi * t / 64)), "Lg": lg, "L": A_["level"], "tick": A_["tick"]}


def ll_prices(xs, k):
    """IC-09: likelihood of observed prices (C0; C1 affine with a = 1, b = 0)."""
    tot = 0.0
    for x in xs:
        P = np.asarray(x, dtype=float)
        if np.any(P <= 0):
            return -math.inf
        lP = np.log(P)
        tot += float(A._logN(lP[0], math.log(k["Lg"]) + k["mu"], k["s"][0]) - lP[0])
        r = np.diff(lP)
        tot += float(np.sum(A._logN(r, k["mu"], k["s"][1:len(r) + 1]) - lP[1:]))
    return tot


def c_prior(kind, c):
    """c prior as a list of (L, weight): AP = the class's asset; PP = the four assets; group = the Δ group."""
    if kind == "AP":
        return [(reid.ASSETS[c[0]]["level"], 1.0)]
    if kind == "PP":
        return [(a["level"], 0.25) for a in reid.ASSETS]
    if kind == "GP":
        grp = [a for a in reid.ASSETS if math.isclose(a["tick"], reid.ASSETS[c[0]]["tick"], rel_tol=1e-12)]
        return [(a["level"], 1.0 / len(grp)) for a in grp]
    raise ValueError(kind)


def m_prior(kind, c):
    if kind in ("AP", "GP"):                     # the Δ group shares the m set
        t = reid.ASSETS[c[0]]["tick"]
        return [(f * 100 * t, 0.25) for f in A.SPEC["m_set"]]
    if kind == "PP":
        return [(f * 100 * a["tick"], 1 / 16) for a in reid.ASSETS for f in A.SPEC["m_set"]]
    raise ValueError(kind)


def ll_tick_prior(xs, k, mix, G):
    """tick_grid C2 with a mixture c prior (AP single L reproduces rip1_attack.ll_tick; tested)."""
    s0, mu, Lg = k["s"][0], k["mu"], k["Lg"]
    delta = k["tick"]
    Lmax = max(L for L, _ in mix)
    lo, hi = -Lmax, Lmax
    lo_p, hi_p = Lg * math.exp(mu - 8 * s0), Lg * math.exp(mu + 8 * s0)
    for x in xs:
        lo, hi = max(lo, lo_p - delta * x[0]), min(hi, hi_p - delta * x[0])
    if hi <= lo:
        return -math.inf
    cs = lo + (hi - lo) * (np.arange(G) + 0.5) / G
    dens = sum(w * (np.abs(cs) < L) / (2 * L) for L, w in mix)
    with np.errstate(divide="ignore"):
        ld = np.log(dens)
    return A._lse(A._tick_grid_ll(xs, k, cs, delta) + ld) + math.log((hi - lo) / G)


def _wrapped_log_density(d, mean, S, m):
    """log Σ_j N(d + j·m; mean, S²), exact for any d (IC-12, FL-023):
    - S/m > 0.5 at every step: the dual (Poisson summation) series (1/m)[1 + 2 Σ_k e^{-2π²k²S²/m²} cos(2πk(d−mean)/m)],
      truncated where the next term is below e^{-23};
    - otherwise: the direct sum CENTRED on the nearest image j0 = round((mean − d)/m), over j0 ± (8·S/m + 2).
    (rip1_attack._ll_resid_given_m centres the direct sum on j = 0, which drops mass when |d| exceeds about 8·S + 2·m:
    see FL-023.)"""
    d, S = np.asarray(d, dtype=float), np.asarray(S, dtype=float)
    r = S / m
    if float(np.min(r)) > 0.5:
        K = int(math.ceil(math.sqrt(46.0) / (math.pi * math.sqrt(2.0) * float(np.min(r))))) + 1
        kk = np.arange(1, K + 1)[None, :]
        val = 1.0 + 2.0 * np.sum(np.exp(-2 * math.pi ** 2 * kk ** 2 * r[:, None] ** 2)
                                 * np.cos(2 * math.pi * kk * (d - mean)[:, None] / m), axis=1)
        return np.log(val / m)
    J = int(math.ceil(8 * float(np.max(S)) / m)) + 2
    j0 = np.round((mean - d) / m)
    jj = j0[:, None] + np.arange(-J, J + 1)[None, :]
    v = A._logN(d[:, None] + jj * m, mean, S[:, None])
    mx = np.max(v, axis=1)
    return mx + np.log(np.sum(np.exp(v - mx[:, None]), axis=1))


def ll_resid_given_m(xs, k, m):
    """level_residual likelihood given m (same model as rip1_attack._ll_resid_given_m; exact wrapped sum), with the
    SUPPORT of the transform enforced (FL-024): x = fmod(P, m) with P > 0 lies in [0, m), so a hypothesis m with any
    observed x outside [0, m) has likelihood 0. (Without this check the exact sum gives log(1/m) per step to every small m,
    whatever the data; the RIP-1 code has no check either, see FL-023.)"""
    mu, s0, Lg = k["mu"], k["s"][0], k["Lg"]
    tot = 0.0
    for x in xs:
        x = np.asarray(x)
        if np.any(x < 0) or np.any(x >= m):                 # exact support [0, m) of fmod(P, m), P > 0
            return -math.inf
        lo, hi = Lg * math.exp(mu - 8 * s0), Lg * math.exp(mu + 8 * s0)
        js = np.arange(math.floor((lo - x[0]) / m), math.ceil((hi - x[0]) / m) + 1)
        P0 = x[0] + js * m
        P0 = P0[P0 > 0]
        if P0.size == 0:
            return -math.inf
        tot += A._lse(A._logN(np.log(P0), math.log(Lg) + mu, s0) - np.log(P0))
        d = np.diff(x)
        tot += float(np.sum(_wrapped_log_density(d, Lg * mu, Lg * k["s"][1:len(d) + 1], m)))
    return tot


def ll_resid_prior(xs, k, mset):
    return A._lse([ll_resid_given_m(xs, k, m) + math.log(w) for m, w in mset])


def a6_scores(rep, cond, xs, pooled=(), prior="AP", delta_seen=None, pv=None):
    """Log-likelihood per class for one unit under condition cond (§5) and ablation (pooled, prior) (§7)."""
    rep = A.ALIASES.get(rep, rep)
    G = SPEC["grid"]
    out = {}
    for c in CLASSES:
        k = class_params(c, pooled, pv)
        if delta_seen is not None and not math.isclose(delta_seen, k["tick"], rel_tol=1e-12):
            out[c] = -math.inf
            continue
        if cond == "C0" or (cond == "C1" and rep == "affine_level"):
            out[c] = ll_prices(xs, k)
        elif rep == "log_returns":
            out[c] = A.ll_returns(xs, k)
        elif rep == "volatility_time":
            out[c] = A.ll_voltime(xs, k)
        elif cond == "C1" and rep == "tick_grid":
            out[c] = float(A._tick_grid_ll(xs, k, np.array([0.0]), k["tick"])[0])
        elif cond == "C1" and rep == "level_residual":
            out[c] = ll_resid_given_m(xs, k, 100 * k["tick"])
        elif rep == "affine_level":
            out[c] = A.ll_affine(xs, k, G)
        elif rep == "tick_grid":
            out[c] = ll_tick_prior(xs, k, c_prior(prior, c), G)
        elif rep == "level_residual":
            out[c] = ll_resid_prior(xs, k, m_prior(prior, c))
        else:
            raise ValueError((rep, cond))
    return out


def ablation_models(rep):
    """§7: (name, pooled set, prior). For representations without asset-linked priors AP = PP: listed once."""
    priors = ["AP", "PP"] if rep in ("tick_grid", "level_residual") else ["AP"]
    ms = [("full", (), "AP")] + [("genpool", tuple(COMPONENTS), pr) for pr in priors]
    for j in COMPONENTS:
        others = tuple(x for x in COMPONENTS if x != j)
        for pr in priors:
            ms += [(f"only_{j}", others, pr), (f"allbut_{j}", (j,), pr)]
    return ms


# ---------------- estimands and bootstrap (§6) ----------------
def bootstrap_sets(labels, B, rng):
    """Stratified by class: within each class, resample its units with replacement keeping the stratum size."""
    by = {}
    for i, y in enumerate(labels):
        by.setdefault(tuple(y), []).append(i)
    strata = [np.array(v) for _, v in sorted(by.items())]
    return [np.concatenate([s[rng.integers(0, len(s), len(s))] for s in strata]) for _ in range(B)]


def acc_vectors(pred, y):
    p, t = np.array(pred), np.array(y)
    return {"asset": (p[:, 0] == t[:, 0]).astype(float), "period": (p[:, 1] == t[:, 1]).astype(float),
            "joint": np.all(p == t, axis=1).astype(float)}


def paired_diff(va, vb, sets):
    d = va - vb
    bs = np.array([d[s].mean() for s in sets])
    return {"diff": float(d.mean()), "ci95": [float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))]}


# ---------------- feature groups (§7, IC-05) ----------------
FEATURE_GROUPS = {"distribution": list(range(0, 18)), "dependence": list(range(18, 28)),
                  "spectrum": list(range(28, 32)), "volatility_extremes": list(range(32, 35)),
                  "shape_sequence": list(range(35, 38))}


def drop_cols(F, cols):
    keep = [j for j in range(len(F[0])) if j not in set(cols)]
    return [[f[j] for j in keep] for f in F]


def permute_family_group(test_ff, cols, perm):
    """§7: family f's members get the group values of the members of perm[f], member i by member i."""
    out = []
    for f, fs in enumerate(test_ff):
        src = test_ff[perm[f]]
        out.append([[src[i][j] if j in cols else fs[i][j] for j in range(len(fs[i]))] for i in range(len(fs))])
    return out


# ---------------- research-utility baseline (§8; derivation RIP2_UVOL_DERIVATION.md) ----------------
def _phi(v):
    return 0.5 * np.array([math.erfc(-x / math.sqrt(2)) for x in v])


def uvol_truth_step(P, mu, sigma, tick, kinds):
    """Exact E[q | P_{u-1}] for every quantity kind in `kinds` (dict name -> function(p0, p1_array)). Derivation §3."""
    p0 = round(round(P / tick) * tick, 10)
    nz = SPEC["truth_nsigma"]
    lo = math.floor(P * math.exp(mu - nz * sigma) / tick) - 1
    hi = math.ceil(P * math.exp(mu + nz * sigma) / tick) + 1
    j = np.arange(lo, hi + 1, dtype=np.float64)
    zb = (np.log(np.maximum((np.append(j, hi + 1) - 0.5) * tick, 1e-300) / P) - mu) / sigma
    pj = np.diff(_phi(zb))
    p1 = np.array([round(v * tick, 10) for v in j])
    return {name: float(np.sum(pj * f(p0, p1))) for name, f in kinds.items()}


def q_kinds(rep, cond, asset, prm):
    """The quantity q for the representation (truth side, unwrapped for level_residual by design)."""
    tick = reid.ASSETS[asset]["tick"]
    par = canonical_params(asset) if cond == "C1" else prm
    if cond == "C0" or rep == "level_residual":
        return lambda p0, p1: (p1 - p0) ** 2
    if rep == "tick_grid":
        c = par["c"]
        return lambda p0, p1: ((p1 - c) / tick - (p0 - c) / tick) ** 2
    if rep == "affine_level":
        a_, b_ = par["a"], par["b"]
        return lambda p0, p1: ((a_ * p1 + b_) - (a_ * p0 + b_)) ** 2
    if rep in ("log_returns", "volatility_time"):
        return lambda p0, p1: np.log(p1 / p0) ** 2
    raise ValueError(rep)


def observed_s(rep, cond, x):
    """s_t, t = 1..n-1, from the representation output as a researcher sees it (§8)."""
    x = np.asarray(x, dtype=float)
    if cond != "C0" and rep == "volatility_time":
        return np.diff(x)
    if cond != "C0" and rep == "log_returns":
        return x ** 2
    return np.diff(x) ** 2


def spearman(a, b):
    def rank(v):
        v = np.asarray(v, dtype=float)
        order = np.argsort(v, kind="mergesort")
        r = np.empty(len(v))
        r[order] = np.arange(1, len(v) + 1)
        for val in np.unique(v):                      # average ranks for ties
            idx = np.where(v == val)[0]
            if len(idx) > 1:
                r[idx] = r[idx].mean()
        return r
    ra, rb = rank(a), rank(b)
    ra, rb = ra - ra.mean(), rb - rb.mean()
    den = math.sqrt(float(np.sum(ra * ra) * np.sum(rb * rb)))
    return float(np.sum(ra * rb) / den) if den > 0 else 0.0


def uvol_rho(s_obs, truth_q):
    """§8: v_t = sqrt(mean truth over u = t-31..t), ṽ_t = sqrt(mean s over the same window), t = 32..511."""
    w = SPEC["uvol_window"]
    s_obs, truth_q = np.asarray(s_obs), np.asarray(truth_q)     # index 0 is t = 1
    n1 = len(s_obs)
    vt = [math.sqrt(truth_q[t - w:t].mean()) for t in range(w, n1 + 1)]
    vh = [math.sqrt(s_obs[t - w:t].mean()) for t in range(w, n1 + 1)]
    return spearman(vt, vh)


def uact_detect(s_obs):
    L, k = SPEC["uact_len"], SPEC["uact_k"]
    s = np.asarray(s_obs[:L], dtype=float)
    s = s - s.mean()
    I = np.abs(np.fft.fft(s)) ** 2
    ks = [i for i in range(1, L // 2) if i not in (k - 1, k, k + 1)]
    return bool(I[k] > np.percentile(I[ks], 99))


def uevent(s_obs, tau=None):
    s = np.asarray(s_obs, dtype=float)                 # s[0] is t = 1
    S = np.cumsum(s - s.mean())[:-1]                   # k = 1 .. n-2 (510 values)
    k0 = int(np.argmax(np.abs(S)))                     # first maximum = smallest k (tie rule)
    tau_hat = (k0 + 1) + 1                             # k̂ = k0 + 1 (1-based); τ̂ = k̂ + 1
    sd = float(s.std())                                # IC-06: ddof = 0
    flag = bool(sd > 0 and np.max(np.abs(S)) / (sd * math.sqrt(len(s))) > SPEC["uevent_crit"])
    success = bool(flag and tau is not None and abs(tau_hat - tau) <= SPEC["uevent_tol"])
    return {"flag": flag, "tau_hat": tau_hat, "success": success}


# ---------------- run (§3–§8) — NOT to be executed before the separate go (FD-01-D46) ----------------
def _materialise(fams, n):
    """Observed (and latent) price paths of every member, base world."""
    out = []
    for f in fams:
        a, p = f["cls"]
        out.append([path_from_normals(a, p, z)[1] for z in f["z"]])
    return out


def _conds(rep):
    """C1 and C2 are the same data for representations without a parameter (§4): reported once (as C1=C2)."""
    return ["C1", "C2"] if rep in ("tick_grid", "level_residual", "affine_level") else ["C12"]


def _data(rep, cond, fams, prices):
    cc = "C1" if cond == "C12" else cond
    return [[represent(rep, cc, obs, f["cls"][0], f["prm"]) for obs in ps] for f, ps in zip(fams, prices)]


def _attack_all(rep, cond, D, dev, dev_x, ev, ev_x, g, sc):
    """Predictions of every §5 attacker for one (representation, condition, Δ) cell."""
    cc = "C1" if cond == "C12" else cond
    show = D == "shown"
    dlt = lambda f: reid.ASSETS[f["cls"][0]]["tick"] if show else None    # noqa: E731
    dev_y = [f["cls"] for f in dev]
    P = {}
    dev_ff = [[_feat(x, dlt(f)) for x in xs] for f, xs in zip(dev, dev_x)]
    ev_ff = [[_feat(x, dlt(f)) for x in xs] for f, xs in zip(ev, ev_x)]
    if g == 1:
        P["A1"], P["A2"] = a1_a2([fs[0] for fs in dev_ff], dev_y, [fs[0] for fs in ev_ff])
        P["A3"] = reid.attack("A3_series_match", [xs[0] for xs in dev_x], dev_y, [xs[0] for xs in ev_x])
    else:
        P["A4a"], P["A4b"] = a4_feats(dev_ff, dev_y, ev_ff)
    P["A6"] = [A.argmax(a6_scores(rep if cond != "C0" else "log_returns", cc, xs,
                                  delta_seen=dlt(f))) for f, xs in zip(ev, ev_x)]
    return P, dev_ff, ev_ff


def run(spec: dict | None = None) -> dict:
    """The RIP-2 experiment. Not to be called for the registered spec before the go (FD-01-D46)."""
    SPEC.update(spec or {})
    A.SPEC["n"] = SPEC["n"]
    n, B = SPEC["n"], SPEC["B"]
    rng_b = np.random.default_rng(SEEDS["bootstrap"])
    rng_p = np.random.default_rng(SEEDS["perm"])
    pv = pooled_values()
    res = {"experiment": "RIP-2", "design": "RIP2_DESIGN.md v0.7 (FD-01-D46)", "synthetic_only": True,
           "threshold": None, "spec": {k: v for k, v in SPEC.items()}, "seeds": SEEDS, "pooled_values": pv,
           "implementation_choices": IMPLEMENTATION_CHOICES, "cells": [], "effects": [], "ablation": [],
           "feature_groups": [], "utility": []}
    for sc, g in SCEN.items():
        fpc = SPEC["fpc"][sc]
        dev = make_families(SEEDS["dev"] + 1000 * g, fpc, g, n)
        ev = make_families(SEEDS["eval"] + 1000 * g, fpc, g, n)
        dev_p, ev_p = _materialise(dev, n), _materialise(ev, n)
        y = [f["cls"] for f in ev]
        sets = bootstrap_sets(y, B, rng_b)
        # C0 (one cell, Δ hidden)
        c0dx, c0ex = _data("log_returns", "C0", dev, dev_p), _data("log_returns", "C0", ev, ev_p)
        P0, _, _ = _attack_all("C0", "C0", "hidden", dev, c0dx, ev, c0ex, g, sc)
        acc0 = {att: acc_vectors(p, y) for att, p in P0.items()}
        for att, v in acc0.items():
            res["cells"].append({"scenario": sc, "representation": "C0(raw prices)", "condition": "C0", "delta": "hidden",
                                 "attacker": att, **{t: float(v[t].mean()) for t in v}, "units": len(y)})
        for rep in REPS:
            accs = {}
            store = {}
            for cond in _conds(rep):
                dx, ex = _data(rep, cond, dev, dev_p), _data(rep, cond, ev, ev_p)
                for D in ("hidden", "shown"):
                    P, dff, eff = _attack_all(rep, cond, D, dev, dx, ev, ex, g, sc)
                    accs[(cond, D)] = {att: acc_vectors(p, y) for att, p in P.items()}
                    for att, v in accs[(cond, D)].items():
                        res["cells"].append({"scenario": sc, "representation": rep, "condition": cond, "delta": D,
                                             "attacker": att, **{t: float(v[t].mean()) for t in v}, "units": len(y)})
                    if cond in ("C2", "C12") and D == "hidden":
                        store = {"dx": dx, "ex": ex, "dff": dff, "eff": eff}
            # §6 effects, attacker by attacker, paired over the same families
            c1, c2 = ("C12", "C12") if rep not in ("tick_grid", "level_residual", "affine_level") else ("C1", "C2")
            for att in acc0:
                for t in ("asset", "period", "joint"):
                    e = {"scenario": sc, "representation": rep, "attacker": att, "target": t}
                    e["representation_effect_C0_minus_C1"] = paired_diff(acc0[att][t], accs[(c1, "hidden")][att][t], sets)
                    for D in ("hidden", "shown"):
                        e[f"secrecy_effect_C1_minus_C2_{D}"] = paired_diff(accs[(c1, D)][att][t], accs[(c2, D)][att][t], sets)
                    for cond, nm in ((c1, "C1"), (c2, "C2")):
                        e[f"delta_effect_shown_minus_hidden_{nm}"] = paired_diff(accs[(cond, "shown")][att][t],
                                                                                 accs[(cond, "hidden")][att][t], sets)
                    inter = (accs[(c1, "shown")][att][t] - accs[(c1, "hidden")][att][t]) - \
                            (accs[(c2, "shown")][att][t] - accs[(c2, "hidden")][att][t])
                    bs = np.array([inter[s].mean() for s in sets])
                    e["interaction_secrecy_x_delta"] = {"diff": float(inter.mean()),
                                                        "ci95": [float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))]}
                    e["C1_equals_C2_data"] = c1 == c2
                    res["effects"].append(e)
            # §7 A6 ablation in C2 (IC-04: every scenario)
            for name, pooled, prior in ablation_models(rep):
                for D in ("hidden", "shown"):
                    preds = [A.argmax(a6_scores(rep, "C1" if c2 == "C12" else "C2", xs, pooled, prior,
                                                reid.ASSETS[f["cls"][0]]["tick"] if D == "shown" else None, pv))
                             for f, xs in zip(ev, store["ex"])]
                    v = acc_vectors(preds, y)
                    row = {"scenario": sc, "representation": rep, "model": name, "pooled": list(pooled), "prior": prior,
                           "delta": D, **{t: float(v[t].mean()) for t in v}, "units": len(y)}
                    if D == "shown":
                        row["within_group"] = _within_group(preds, ev, y)
                        if rep == "tick_grid":                                   # IC-10
                            gp = [A.argmax(a6_scores(rep, "C2", xs, pooled, "GP", reid.ASSETS[f["cls"][0]]["tick"], pv))
                                  for f, xs in zip(ev, store["ex"])]
                            row["within_group_group_pooled_prior"] = _within_group(gp, ev, y)
                    res["ablation"].append(row)
            # §7 feature-group ablation and family-level permutation importance (IC-05: C2, Δ hidden)
            res["feature_groups"] += _feature_groups(rep, sc, g, dev, store, ev, y, rng_p)
    res["utility"] = utility(pv)
    return res


def _within_group(preds, ev, y):
    out = {}
    for t in TICKS:
        idx = [i for i, f in enumerate(ev) if math.isclose(reid.ASSETS[f["cls"][0]]["tick"], t, rel_tol=1e-12)]
        if not idx:
            continue
        ncls = sum(1 for c in CLASSES if math.isclose(reid.ASSETS[c[0]]["tick"], t, rel_tol=1e-12))
        acc = sum(tuple(preds[i]) == tuple(y[i]) for i in idx) / len(idx)
        out[repr(t)] = {"classes": ncls, "chance": 1 / ncls, "units": len(idx), "joint_accuracy": acc}
    return out


def _feature_groups(rep, sc, g, dev, store, ev, y, rng_p):
    dev_y = [f["cls"] for f in dev]
    dff, eff = store["dff"], store["eff"]
    rows = []

    def score(dF, eF):
        if g == 1:
            return acc_vectors(a1_a2([fs[0] for fs in dF], dev_y, [fs[0] for fs in eF])[1], y)
        return acc_vectors(a4_feats(dF, dev_y, eF)[0], y)
    base = score(dff, eff)
    att = "A2" if g == 1 else "A4a"
    for gname, cols in FEATURE_GROUPS.items():
        dF = [[drop_cols([f], cols)[0] for f in fs] for fs in dff]
        eF = [[drop_cols([f], cols)[0] for f in fs] for fs in eff]
        abl = score(dF, eF)
        drops = []
        for _ in range(SPEC["perm_repeats"]):
            perm = rng_p.permutation(len(eff))
            pv_ = score(dff, permute_family_group(eff, set(cols), perm))
            drops.append({t: float(base[t].mean() - pv_[t].mean()) for t in base})
        rows.append({"scenario": sc, "representation": rep, "attacker": att, "condition": "C2 (C1=C2 if no parameter)",
                     "delta": "hidden", "group": gname,
                     "base": {t: float(base[t].mean()) for t in base},
                     "ablation_drop": {t: float(base[t].mean() - abl[t].mean()) for t in base},
                     "permutation_drop_mean": {t: float(np.mean([d[t] for d in drops])) for t in base},
                     "permutation_drop_sd": {t: float(np.std([d[t] for d in drops])) for t in base}})
    return rows


def utility(pv=None):
    """§8 on S-ind families of the planted (5103) and null (5104) seeds (IC-02)."""
    n, fpc = SPEC["n"], SPEC["util_fpc"]
    planted = make_families(SEEDS["util_planted"], fpc, 1, n)
    null = make_families(SEEDS["util_null"], fpc, 1, n)
    rng = np.random.default_rng(SEEDS["bootstrap"])
    sets = bootstrap_sets([f["cls"] for f in planted], SPEC["B"], rng)
    rows = []
    data_sets = [("C0", "C0")] + [(rep, c) for rep in REPS for c in (("C1", "C2") if rep in
                                                                     ("tick_grid", "level_residual", "affine_level") else ("C1",))]
    for world_name, fams in (("planted", planted), ("null", null)):
        rho = {k: [] for k in data_sets}
        ev_flag = {k: [] for k in data_sets}
        ev_succ = {k: [] for k in data_sets}
        act_det = {k: [] for k in data_sets}
        for f in fams:
            a, p = f["cls"]
            tau = f["tau"] if world_name == "planted" else None
            lat, obs = path_from_normals(a, p, f["z"][0], tau=tau)
            _, obs_act = path_from_normals(a, p, f["z"][0], act_zero=(world_name == "null"))   # IC-02
            A_, P_ = reid.ASSETS[a], reid.PERIODS[p]
            kinds = {f"{r}|{c}": q_kinds("log_returns" if r == "C0" else r, c, a, f["prm"]) for r, c in data_sets}
            truth = {k: [] for k in kinds}
            for u in range(1, n):
                act = 1 + A_["act"] * math.sin(2 * math.pi * u / 64)
                sig = A_["vol"] * P_["volx"] * act * (2 if tau is not None and u >= tau else 1)
                tr = uvol_truth_step(lat[u - 1], A_["drift"], sig, A_["tick"], kinds)
                for k, v in tr.items():
                    truth[k].append(v)
            for (r, c) in data_sets:
                x = represent("log_returns", "C0", obs, a, f["prm"]) if r == "C0" else represent(r, c, obs, a, f["prm"])
                s = observed_s(r, c, x)
                rho[(r, c)].append(uvol_rho(s, truth[f"{r}|{c}"]))
                ue = uevent(s, tau)
                ev_flag[(r, c)].append(ue["flag"])
                ev_succ[(r, c)].append(ue["success"])
                xa = represent("log_returns", "C0", obs_act, a, f["prm"]) if r == "C0" else represent(r, c, obs_act, a, f["prm"])
                act_det[(r, c)].append(uact_detect(observed_s(r, c, xa)))
        for k in data_sets:
            rv = np.array(rho[k])
            bs = [float(rv[s].mean()) for s in sets]
            nf = len(rv)
            row = {"world": world_name, "data": k[0], "condition": k[1],
                   "U_vol_mean_rho": float(rv.mean()), "U_vol_ci95": [float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))],
                   "U_event_flag_rate": sum(ev_flag[k]) / nf, "U_event_flag_wilson95": reid.wilson(sum(ev_flag[k]), nf),
                   "U_act_detection_rate": sum(act_det[k]) / nf, "U_act_wilson95": reid.wilson(sum(act_det[k]), nf),
                   "units": nf}
            if world_name == "planted":
                row["U_event_success_rate"] = sum(ev_succ[k]) / nf
                row["U_event_success_wilson95"] = reid.wilson(sum(ev_succ[k]), nf)
            rows.append(row)
    return rows
