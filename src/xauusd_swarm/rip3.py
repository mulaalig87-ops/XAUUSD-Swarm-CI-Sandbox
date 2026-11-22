"""RIP-3 — anonymisation alternatives at the volatility and activity level. SYNTHETIC ONLY.
Design: docs/research/RIP3_DESIGN.md v0.4, frozen by FD-01-D47 (sha256 efb7e163…). BUILD authorised (OD-S9-11);
RUN is NOT authorised: the registered evaluation and confirmatory sets (seeds 6201 / 6301) must not be scored
before a separate founder authorisation. Opens no gate; sets no threshold (CS-01-04 untouched).

Every place where the frozen design is silent and the code had to choose is listed in IMPLEMENTATION_CHOICES and
in docs/research/RIP3_BUILD_NOTES.md (no silent difference between design and code).

Sections: streams and families (§6 C-O1) · worlds W1 / W2 (§3.0, §4.3) · candidates (§3) · summary vector (§4.1) ·
attackers A1–A4, A6, A7, A8 (§4.1) · Student-t helpers and W2 U-vol* truth (§4.3) · utility (§4.2) ·
jobs (resumable) · evaluation: matrix, gates, floors, selection, failure conditions (§5, §7).
"""
from __future__ import annotations

import hashlib
import json
import math
import random
from pathlib import Path
from statistics import NormalDist

import numpy as np

from . import reid
from . import rip1_attack as A
from . import rip2

CLASSES = list(A.CLASSES)
SCEN = {"ind": 1, "g4": 4, "g16": 16}
WORLDS = ("W1", "W2")
SEEDS = {"dev": 6101, "build_holdout": 6102, "smoke": 6103, "eval": 6201, "eval_bootstrap": 6299,
         "confirm": 6301, "confirm_bootstrap": 6399}
SPEC = {
    "n": 512, "fpc": {"ind": 25, "g4": 10, "g16": 5}, "util_fpc": 25, "B": 2000,
    "dev_per_class": 2000, "mults": (1, 2, 4), "knn_k": 15,
    "garch": {"alpha": 0.08, "beta": 0.90, "nu": 5, "burnin": 500},
    "t_K0": 50.0, "t_Kmax": 400.0, "t_acc": 1e-6, "price_floor_ticks": 100,
    "a6_grid": 257, "a6_halfwidth_sd": 12.0, "a6_boundary_grid": 16385, "a6_boundary_decay": 40.0,
    "tau_range": (128, 384), "uact_null_limit": 0.07,
}
CANDIDATES = ["B-LR", "B-AF", "B-LRS", "M1", "M2w1", "M2w2", "M2w4", "M3W32", "M3W128", "M4", "M5", "M6"]
CONTROL = "M1-Dshown"
ALL_CELLS = CANDIDATES + [CONTROL]
LEVEL_CANDS = ("B-AF", "B-LRS")
A6_TRACTABLE = ("B-LR", "B-AF", "B-LRS", "M1", "M2w1", "M2w2", "M2w4", CONTROL)
SCOPE_SENTENCE = ("Bounded by A1–A4, A7 and A8 on the 108-component summary; a lower bound; not the strongest "
                  "possible attacker; not exhaustive (§4.1, C-A5).")
TARGETS = ("asset", "period", "joint")

IMPLEMENTATION_CHOICES = {
    "IC3-01": "Streams. Every random draw comes from a Python random.Random seeded with the string "
              "'RIP3|<base seed>|<role>|<world>|g<g>|<asset>|<period>|<family index>|...' (str seeding is sha512-based "
              "and platform independent). Family stream ('fam'): rip1_attack.draw (c, a, b, m), then tau = randint(128, 384), "
              "then u = uniform(-1, 1) for the M2 scale. Member stream ('m', member index): the series' own stream "
              "(design §4.3 'the series' own random.Random stream'); W1 draws n gauss values, W2 the burn-in then the "
              "n (G, Q) pairs.",
    "IC3-02": "M2: ln kappa = w·u with the family's single u ~ U(-1, 1), so ln kappa ~ U(-w, w) for each w in {1, 2, 4} "
              "(the three grids share the family's u: paired). kappa is per family (shared by members, design §3).",
    "IC3-03": "Seed roles. dev 6101 (attacker development); build_holdout 6102 (BUILD-stage validation of A7, M1/M2 A6 "
              "checks: development range, design §9); eval 6201 (identity and utility evaluation, roles 'eval', "
              "'util_planted', 'util_null'); confirm 6301 (same roles). Bootstrap: numpy default_rng(6299) for eval, "
              "(6399) for confirm; smoke 6103 (BUILD-stage end-to-end checks with small sizes; bootstrap 6193); per world, sets drawn in the order ind, g4, g16, then utility, B sets each, stratified "
              "by class.",
    "IC3-04": "Development sizes. S-ind: 2000·mult series per class, mult in {1, 2, 4}, nested (the x1 set is the first "
              "2000 family indices of the x4 set). S-pool g: 2000·mult/g families per class (the same number of series), "
              "nested likewise. A1, A3 and A4a/A4b use the x1 set; A2, A7 and A8 are built at x1, x2 and x4 (C-O3). The "
              "identity number reported for A2, A7 and A8 is the x4 value (the most trained); x1 and x2 are stored.",
    "IC3-05": "A7 standardises the summary with development means and population standard deviations (sd 0 -> 1, as "
              "reid._standardiser) before the Ledoit-Wolf fit: the shrinkage target (scaled identity) needs commensurate "
              "scales. A Gaussian with full covariance is affine invariant; the shrinkage is not.",
    "IC3-06": "A7 in S-pool: per-class Gaussian fitted on the member summaries of the S-pool development families of the "
              "same g and size; the family score is the sum of the members' log-densities.",
    "IC3-07": "A8 in S-pool: the family summary (mean of member raw summaries) is z-scored with the means and sds of the "
              "development family summaries; Euclidean k-NN, k = 15, over development families. Tie rule as S-ind: "
              "majority, then smallest summed Euclidean distance of that class's neighbours, then lowest class index.",
    "IC3-08": "Delta-shown control (M1-Dshown): A1/A2/A4 get the Delta one-hot (rip2 IC-03); A3 never sees Delta; A6 "
              "uses delta_seen; A7 and A8 exclude every class whose tick differs from the shown Delta (A8: neighbours "
              "searched only among development units with that tick).",
    "IC3-09": "Phase of the summary's 64 phase-RMS values: phi = t mod 64 with t the generator step index of each output "
              "value (returns-based outputs: t = 1..511; level outputs B-AF, B-LRS: t = 0..511). ACF of x^2 is "
              "reid._acf (mean-centred). log-RMS uses max(RMS, 1e-300).",
    "IC3-10": "Zero denominators. M1 / M6: if RMS = 0 the output is all zeros. M3: if the window RMS is 0 then x_t = 0 "
              "(the numerator is in the window, so it is 0 too). M5: a phase with c_phi = 0 gives x = 0 on that phase; "
              "if the mean profile is 0 the output is all zeros.",
    "IC3-11": "A1, A2, A3, A4a/A4b are numpy re-implementations of reid.attack / rip2.a1_a2 / rip2.a4_feats with the same "
              "standardiser, distances and tie rules (tested equal on sample data); the pure-Python versions are too slow "
              "at 32,000 development series.",
    "IC3-12": "A6 for M1 and M2 is evaluated in u = 1/lambda (= 1/kappa) where the Gaussian log-density is quadratic: "
              "g(v) = C + n·v − (A/2)e^{2v} + B·e^{v}, v = ln u, A = Σx²/s², B = Σμx/s². M1: per member, trapezoid "
              "on v* ± 12 sd (sd = (−g''(v*))^{-1/2}), 257 points. M2: members summed (kappa shared), v restricted to "
              "[−w, w] with density 1/(2w); window [v* ± 12 sd] ∩ [−w, w], 257 points; if v* lies outside [−w, w], the "
              "window runs from the bound to the farther of v* ∓ 12 sd and bound ∓ 40/|g'(bound)| (FL-027), with 16385 points. Verified against dense quadrature.",
    "IC3-13": "W2 burn-in: from (h, eps) = (sigma_k^2, 0) the recursion is applied 500 times (burn-in steps 0..499); "
              "step t = 0 of the series then uses h_0 = omega + alpha·eps_499^2 + beta·h_499.",
    "IC3-14": "W2 truth: the central sum uses the observed price j·tick rounded to 10 decimals (numpy round; "
              "rip2.uvol_truth_step uses Python round, which can differ only at an exact decimal half, a 1e-10 price "
              "difference); "
              "F_nu for the central cells is the closed form for nu = 5; the tail quantities T0, T1, T2, U2 and "
              "F_nu(y_f) use the regularised incomplete beta (continued fraction) on the small argument.",
    "IC3-15": "Utility of B-AF and B-LRS: U-act and U-event as RIP-2 (s = squared increments of the level series); "
              "U-vol is quoted from RIP-2 (design §4.2) and U-ratio is not defined for them (not built on r).",
    "IC3-16": "Maximum over attackers: per cell and target, the attacker (x4 for A2/A7/A8) with the highest mean "
              "accuracy; ties go to the order A6, A7, A8, A1, A2, A3, A4a, A4b. Paired differences use the per-unit "
              "vectors of the chosen attacker on each side.",
    "IC3-17": "Selection (§7.4 step 2): the joint-identity reduction in g16 used for ranking is the smaller of the W1 "
              "and W2 paired reductions (both must be positive by §7.3). Floors (§7.2) must hold in both worlds. Nearest "
              "competitor for the confirmatory step: the next candidate of the same class in that ranking.",
    "IC3-18": "Pareto status (report only): candidate X dominates Y in the same class if X's max-attacker joint "
              "identity is <= Y's in S-ind and g16 in both worlds and X is at least as good on every §7.2 utility "
              "measure in both worlds, with one strict inequality.",
    "IC3-19": "C-V2 is checked in W1 (where A6 is the true model), for B-LR and B-AF, every scenario and target: A7 "
              "(x4) mean >= lower end of A6's bootstrap interval. C-V3 compares A6 and the B-LR utility with RIP-2 "
              "(dev-size-dependent feature attackers are not comparable).",
    "IC3-21": "W2 truth central sum is accumulated in chunks of 2,000,000 tick levels (same terms, memory bounded). The "
              "frozen algorithm has no cap on the number of tick levels; its cost grows like P·sinh(K·b)/tick.",
    "IC3-22": "W2 truth for very wide central sums (more than 1,000,000,000 tick levels; below that the frozen exact sum is "
              "always used, which covers every step measured in the registered W2 world, at most 1.5e8 levels): the levels j <= 10,000 and the "
              "cells clipped at ±K are summed exactly; the remaining full cells are grouped into blocks of width 0.01 in y "
              "and each block's sum Σ p_j ln(j·tick/P̃)² is replaced by the continuous integral ∫ f_5(y)(A + b·y)² dy over the "
              "block (closed-form t moments), with the proven bound (tick²·W·f_max/(12·b·p_lo³))·(2·L(c1/b + 1) + 1 + L) "
              "+ (2L/p_lo)·r·M0 per block (midpoint-cell expansion in price; c1 = (ν+1)/(2√ν); r the 10-decimal rounding). "
              "The bounds are added to E_u, so the frozen acceptance E_u ≤ 1e-6·q_u is unchanged. Verified against the exact "
              "sum (tests; B1 attempts 3 and 4).",
    "IC3-20": "W2 moments (C-V1): the moments of z with finite-variance estimators (E z, E z², P(z <= t) at 7 points) "
              "get the 4-standard-error rule of the RIP-2 Monte Carlo check; E[eps²] and E[h] are reported without a "
              "rule because eps has no finite fourth moment (design §4.3). The GARCH recursion itself is checked "
              "exactly by a test.",
}


# ================= streams and families (§6 C-O1; IC3-01) =================
def stream(*parts) -> random.Random:
    return random.Random("RIP3|" + "|".join(str(p) for p in parts))


def make_family(base, role, world, g, cls, i):
    a, p = cls
    fr = stream(base, role, world, f"g{g}", a, p, i, "fam")
    prm = A.draw(a, fr)
    tau = fr.randint(*SPEC["tau_range"])
    u = fr.uniform(-1.0, 1.0)
    return {"cls": (a, p), "idx": i, "prm": prm, "tau": tau, "u_kappa": u, "g": g,
            "key": (base, role, world, f"g{g}", a, p, i)}


def member_stream(fam, m) -> random.Random:
    return stream(*fam["key"], "m", m)


# ================= worlds (§3.0, §4.3) =================
class WorldError(Exception):
    """C-V1 failure: an observed price of 0 (j = 0) or below; the cell fails, nothing is resampled."""


def sigma_k(a, p):
    return reid.ASSETS[a]["vol"] * reid.PERIODS[p]["volx"]


def innovations(world, cls, rnd, n):
    """W1: n standard-normal draws. W2: (eps, h) of the exact GARCH(1,1)-t specification (§4.3, IC3-13)."""
    if world == "W1":
        return {"z": [rnd.gauss(0, 1) for _ in range(n)]}
    gp = SPEC["garch"]
    al, be, nu, B0 = gp["alpha"], gp["beta"], gp["nu"], gp["burnin"]
    sk = sigma_k(*cls)
    om = sk * sk * (1 - al - be)
    c = math.sqrt((nu - 2) / nu)

    def zdraw():
        G = rnd.gauss(0, 1)
        Q = rnd.gammavariate(nu / 2, 2)
        return G / math.sqrt(Q / nu) * c

    h, e = sk * sk, 0.0
    for _ in range(B0):
        h = om + al * e * e + be * h
        e = math.sqrt(h) * zdraw()
    hs, es = [], []
    for _ in range(n):
        h = om + al * e * e + be * h
        e = math.sqrt(h) * zdraw()
        hs.append(h)
        es.append(e)
    return {"eps": es, "h": hs}


def path_w2(asset, period, eps, tau=None, act_zero=False):
    """W2 prices: r_t = mu_a + m_t·f_t·eps_t; prices and rounding exactly as reid.simulate."""
    a, p = reid.ASSETS[asset], reid.PERIODS[period]
    price = a["level"] * p["growth"]
    lat, obs = [], []
    for t, e in enumerate(eps):
        act = 1 + (0 if act_zero else a["act"]) * math.sin(2 * math.pi * t / 64)
        step = act * e
        if tau is not None and t >= tau:
            step = step * 2
        price *= math.exp(a["drift"] + step)
        lat.append(price)
        obs.append(round(round(price / a["tick"]) * a["tick"], 10))
    return lat, obs


def path(world, cls, inno, tau=None, act_zero=False):
    if world == "W1":
        lat, obs = rip2.path_from_normals(cls[0], cls[1], inno["z"], tau=tau, act_zero=act_zero)
    else:
        lat, obs = path_w2(cls[0], cls[1], inno["eps"], tau=tau, act_zero=act_zero)
    if min(obs) <= 0:
        raise WorldError(f"observed price <= 0 (j = 0) in {world} class {cls}")
    return lat, obs


# ================= candidates (§3) =================
def rms(v):
    v = np.asarray(v, dtype=float)
    return math.sqrt(float(np.mean(v * v))) if v.size else 0.0


def _safe_div(num, den):
    num, den = np.asarray(num, dtype=float), np.asarray(den, dtype=float)
    out = np.zeros_like(num)
    nz = den > 0
    out[nz] = num[nz] / den[nz]
    return out


def m1(r):
    s = rms(r)
    return np.asarray(r, dtype=float) / s if s > 0 else np.zeros(len(r))


def m3(r, W):
    r = np.asarray(r, dtype=float)
    pad = np.concatenate([np.zeros(W - 1), r * r])
    ss = np.lib.stride_tricks.sliding_window_view(pad, W).sum(axis=1)
    cnt = np.minimum(np.arange(1, len(r) + 1), W)
    return _safe_div(r, np.sqrt(ss / cnt))


_ND = NormalDist()


def average_ranks(v):
    v = np.asarray(v, dtype=float)
    order = np.argsort(v, kind="mergesort")
    r = np.empty(len(v))
    r[order] = np.arange(1, len(v) + 1)
    vals, inv, cnt = np.unique(v, return_inverse=True, return_counts=True)
    if np.any(cnt > 1):
        sums = np.bincount(inv, weights=r)
        r = (sums / cnt)[inv]
    return r


def m4(r):
    n = len(r)
    return np.array([_ND.inv_cdf((q - 0.5) / n) for q in average_ranks(r)])


def phases(length, t0):
    return (np.arange(length) + t0) % 64


def phase_rms(x, t0):
    x = np.asarray(x, dtype=float)
    ph = phases(len(x), t0)
    s = np.bincount(ph, weights=x * x, minlength=64)
    c = np.bincount(ph, minlength=64)
    return np.sqrt(_safe_div(s, c))


def m5(r):
    r = np.asarray(r, dtype=float)
    c = phase_rms(r, 1)
    mc = float(np.mean(c))
    if mc <= 0:
        return np.zeros(len(r))
    return _safe_div(r, (c / mc)[phases(len(r), 1)])


def transform(cand, obs, asset, fam):
    """The released series of one member (Δ hidden in every candidate except the control's attackers)."""
    prm = fam["prm"]
    if cand == "B-AF":
        return np.array(A.blind("affine_level", obs, asset, prm))
    if cand == "B-LRS":
        return np.array(A.blind("level_residual", obs, asset, prm))
    r = np.array(A.blind("log_returns", obs, asset, prm))
    if cand == "B-LR":
        return r
    if cand in ("M1", CONTROL):
        return m1(r)
    if cand.startswith("M2w"):
        return math.exp(int(cand[3:]) * fam["u_kappa"]) * r
    if cand.startswith("M3W"):
        return m3(r, int(cand[3:]))
    if cand == "M4":
        return m4(r)
    if cand == "M5":
        return m5(r)
    if cand == "M6":
        return m1(m5(r))
    raise ValueError(cand)


# ================= summary vector (§4.1; IC3-09) =================
def summary(x, level=False):
    x = np.asarray(x, dtype=float)
    f = reid.features([float(v) for v in x])
    pr = phase_rms(x, 0 if level else 1)
    x2 = [float(v * v) for v in x]
    acf = [reid._acf(x2, k) for k in range(1, 6)]
    return np.array(f + list(pr) + [math.log(max(rms(x), 1e-300))] + acf, dtype=float)


N_FEAT = 38
N_SUMMARY = 108


# ================= attackers (§4.1) =================
def standardiser(X):
    X = np.asarray(X, dtype=float)
    mu = X.mean(axis=0)
    sd = X.std(axis=0)
    sd[sd == 0] = 1.0
    return lambda Z: (np.asarray(Z, dtype=float) - mu) / sd


def onehot(delta):
    return rip2.onehot(delta)


def _sqdist(Q, D):
    """Squared Euclidean distances, row by row, summed in feature order (as the pure-Python reference)."""
    out = np.empty((len(Q), len(D)))
    for i, q in enumerate(Q):
        out[i] = np.sum((D - q) ** 2, axis=1)
    return out


def a1(dev_F, dev_y, ev_F):
    z = standardiser(dev_F)
    dz, tz = z(dev_F), z(ev_F)
    d = _sqdist(tz, dz)
    return [dev_y[int(np.argmin(row))] for row in d]


def a2(dev_F, dev_y, ev_F):
    z = standardiser(dev_F)
    dz, tz = z(dev_F), z(ev_F)
    classes = sorted(set(dev_y))
    ya = np.array([CLASSES.index(c) for c in dev_y])
    cents = np.array([dz[ya == CLASSES.index(c)].mean(axis=0) for c in classes])
    d = _sqdist(tz, cents)
    return [classes[int(np.argmin(row))] for row in d]


def a3(dev_x, dev_y, ev_x):
    sd = [reid.series_signature([float(v) for v in x]) for x in dev_x]
    z = standardiser(sd)
    dz = z(sd)
    tz = z([reid.series_signature([float(v) for v in x]) for x in ev_x])
    d = _sqdist(tz, dz)
    return [dev_y[int(np.argmin(row))] for row in d]


def a4(dev_FF, dev_y, ev_FF):
    """rip2.a4_feats in numpy: dev_FF array (families, g, k)."""
    dev_FF, ev_FF = np.asarray(dev_FF, dtype=float), np.asarray(ev_FF, dtype=float)
    nf, g, k = dev_FF.shape
    z = standardiser(dev_FF.reshape(-1, k))
    dz = z(dev_FF.reshape(-1, k)).reshape(nf, g, k)
    gm = dz.mean(axis=1)
    yi = np.array([CLASSES.index(c) for c in dev_y])
    cent_g = np.array([gm[yi == ci].mean(axis=0) for ci in range(len(CLASSES))])
    cent_s = np.array([dz[yi == ci].reshape(-1, k).mean(axis=0) for ci in range(len(CLASSES))])
    out_a, out_b = [], []
    for fs in ev_FF:
        tz = z(fs)
        m = tz.mean(axis=0)
        out_a.append(CLASSES[int(np.argmin(np.sum((cent_g - m) ** 2, axis=1)))])
        dm = _sqdist(tz, cent_s)                                  # members × classes
        votes = np.argmin(dm, axis=1)
        cnt = np.bincount(votes, minlength=len(CLASSES))
        tied = np.where(cnt == cnt.max())[0]
        tot = dm[:, tied].sum(axis=0)
        out_b.append(CLASSES[int(tied[int(np.argmin(tot))])])
    return out_a, out_b


# ---- Ledoit–Wolf (sklearn.covariance.ledoit_wolf formula, assume_centered=False) ----
def ledoit_wolf(X):
    X = np.asarray(X, dtype=float)
    n, p = X.shape
    X = X - X.mean(axis=0)
    emp = X.T @ X / n
    mu = float(np.trace(emp)) / p
    X2 = X ** 2
    emp_tr = np.sum(X2, axis=0) / n
    beta_ = float(np.sum(X2.T @ X2))
    delta_ = float(np.sum((X.T @ X) ** 2)) / n ** 2
    beta = 1.0 / (p * n) * (beta_ / n - delta_)
    delta = (delta_ - 2.0 * mu * float(emp_tr.sum()) + p * mu ** 2) / p
    beta = min(beta, delta)
    s = 0.0 if beta == 0 else beta / delta
    return (1.0 - s) * emp + s * mu * np.eye(p), s


class A7Model:
    """Per-class Gaussian with Ledoit–Wolf covariance on z-scored summaries (IC3-05)."""

    def __init__(self, dev_S, dev_y):
        dev_S = np.asarray(dev_S, dtype=float)
        self.z = standardiser(dev_S)
        Z = self.z(dev_S)
        yi = np.array([CLASSES.index(c) for c in dev_y])
        self.par, self.shrink = [], []
        for ci in range(len(CLASSES)):
            Zc = Z[yi == ci]
            cov, s = ledoit_wolf(Zc)
            L = np.linalg.cholesky(cov)
            self.par.append((Zc.mean(axis=0), L, 2.0 * float(np.sum(np.log(np.diag(L))))))
            self.shrink.append(s)

    def logdens(self, S):
        Z = self.z(np.atleast_2d(S))
        out = np.empty((len(Z), len(CLASSES)))
        p = Z.shape[1]
        for ci, (m, L, logdet) in enumerate(self.par):
            sol = np.linalg.solve(L, (Z - m).T)
            out[:, ci] = -0.5 * (np.sum(sol * sol, axis=0) + logdet + p * math.log(2 * math.pi))
        return out


def argmax_classes(scores, allowed=None):
    """Highest score; ties to the lowest class index. allowed: boolean mask over CLASSES."""
    s = np.array(scores, dtype=float)
    if allowed is not None:
        s = np.where(allowed, s, -np.inf)
    return CLASSES[int(np.argmax(s))]


def a8(dev_S, dev_y, ev_S, k=None, ev_allowed=None):
    """k-NN, k = 15 (§4.1): majority; ties: smallest summed Euclidean distance, then lowest class index."""
    k = k or SPEC["knn_k"]
    dev_S = np.asarray(dev_S, dtype=float)
    z = standardiser(dev_S)
    dz, tz = z(dev_S), z(ev_S)
    yi = np.array([CLASSES.index(c) for c in dev_y])
    out = []
    for i, q in enumerate(tz):
        d = np.sqrt(np.sum((dz - q) ** 2, axis=1))
        idx = np.arange(len(dz))
        if ev_allowed is not None:
            keep = ev_allowed[i][yi]
            d, idx = d[keep], idx[keep]
        nn = np.argsort(d, kind="stable")[:k]
        cls_nn, d_nn = yi[idx[nn]], d[nn]
        cnt = np.bincount(cls_nn, minlength=len(CLASSES))
        tied = np.where(cnt == cnt.max())[0]
        sums = np.array([d_nn[cls_nn == c].sum() for c in tied])
        best = tied[np.where(sums == sums.min())[0][0]]
        out.append(CLASSES[int(best)])
    return out


# ---- A6 (§4.1) ----
def _lse(v):
    return A._lse(v)


def _trap_log(gv, v):
    """log ∫ e^{g} dv by the trapezoid rule on the grid v."""
    w = np.full(len(v), (v[-1] - v[0]) / (len(v) - 1))
    w[0] *= 0.5
    w[-1] *= 0.5
    return _lse(gv + np.log(w))


def _quad_terms(x, mu, s):
    x, s = np.asarray(x, dtype=float), np.asarray(s, dtype=float)
    Aq = float(np.sum(x * x / (s * s)))
    Bq = float(np.sum(mu * x / (s * s)))
    C = float(np.sum(-mu * mu / (2 * s * s) - np.log(s) - 0.5 * math.log(2 * math.pi)))
    return Aq, Bq, C, len(x)


def _g(v, Aq, Bq, C, n):
    return C + n * v - 0.5 * Aq * np.exp(2 * v) + Bq * np.exp(v)


def _mode(Aq, Bq, n):
    u = (Bq + math.sqrt(Bq * Bq + 4 * Aq * n)) / (2 * Aq)
    v = math.log(u)
    curv = 2 * Aq * u * u - Bq * u
    return v, 1.0 / math.sqrt(curv)


def ll_scale_invariant(x, mu, s):
    """M1: log ∫ p(u·x) u^n d ln u (the maximal-invariant likelihood; IC3-12)."""
    Aq, Bq, C, n = _quad_terms(x, mu, s)
    if Aq <= 0:
        return -math.inf
    v0, sd = _mode(Aq, Bq, n)
    H = SPEC["a6_halfwidth_sd"] * sd
    v = np.linspace(v0 - H, v0 + H, SPEC["a6_grid"])
    return _trap_log(_g(v, Aq, Bq, C, n), v)


def ll_secret_scale(xs, mu, s, w):
    """M2: log ∫_{-w}^{w} (1/2w) Π_members p(u·x) u^n dv, v = ln u = −ln κ (κ shared by the family; IC3-12)."""
    terms = [_quad_terms(x, mu, s[:len(x)]) for x in xs]
    Aq, Bq, C, n = (sum(t[i] for t in terms) for i in range(4))
    if Aq <= 0:
        return -math.inf
    v0, sd = _mode(Aq, Bq, n)
    H = SPEC["a6_halfwidth_sd"] * sd
    lo, hi = v0 - H, v0 + H
    G = SPEC["a6_grid"]
    if not -w <= v0 <= w:                       # the mode is outside the prior: the mass sits at the bound
        G = SPEC["a6_boundary_grid"]
        bnd = w if v0 > w else -w
        slope = abs(float(n - Aq * math.exp(2 * bnd) + Bq * math.exp(bnd)))
        width = SPEC["a6_boundary_decay"] / max(slope, 1e-300)
        if bnd == w:                            # the smaller of the two lower cuts covers both regimes (FL-027)
            lo, hi = min(v0 - H, w - width), w
        else:
            lo, hi = -w, max(v0 + H, -w + width)
    lo, hi = max(lo, -w), min(hi, w)
    v = np.linspace(lo, hi, G)
    return _trap_log(_g(v, Aq, Bq, C, n), v) - math.log(2 * w)


def a6_scores(cand, xs, delta_seen=None):
    """Log-likelihood per class for one unit (xs: the members' outputs)."""
    if cand == "B-LR":
        return rip2.a6_scores("log_returns", "C1", [list(map(float, x)) for x in xs], delta_seen=delta_seen)
    if cand == "B-AF":
        return rip2.a6_scores("affine_level", "C2", [list(map(float, x)) for x in xs], delta_seen=delta_seen)
    if cand == "B-LRS":
        return rip2.a6_scores("level_residual", "C2", [list(map(float, x)) for x in xs], delta_seen=delta_seen)
    out = {}
    for c in CLASSES:
        k = rip2.class_params(c)
        if delta_seen is not None and not math.isclose(delta_seen, k["tick"], rel_tol=1e-12):
            out[c] = -math.inf
            continue
        s = k["s"][1:]
        if cand in ("M1", CONTROL):
            out[c] = sum(ll_scale_invariant(x, k["mu"], s[:len(x)]) for x in xs)
        elif cand.startswith("M2w"):
            out[c] = ll_secret_scale(xs, k["mu"], s, int(cand[3:]))
        else:
            raise ValueError(f"A6 not tractable for {cand}")
    return out


# ================= Student-t helpers and the W2 U-vol* truth (§4.3) =================
def betacf(a, b, x, itmax=10000, eps=1e-16):
    """Continued fraction for the incomplete beta (modified Lentz)."""
    tiny = 1e-300
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c, d = 1.0, 1.0 - qab * x / qap
    d = 1.0 / (d if abs(d) > tiny else tiny)
    h = d
    for m in range(1, itmax + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        d = 1.0 / (d if abs(d) > tiny else tiny)
        c = 1.0 + aa / c
        c = c if abs(c) > tiny else tiny
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        d = 1.0 / (d if abs(d) > tiny else tiny)
        c = 1.0 + aa / c
        c = c if abs(c) > tiny else tiny
        de = d * c
        h *= de
        if abs(de - 1.0) < eps:
            return h
    raise ArithmeticError("betacf did not converge")


def betainc(a, b, x):
    """Regularised incomplete beta I_x(a, b)."""
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    lbt = math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b) + a * math.log(x) + b * math.log1p(-x)
    if x < (a + 1) / (a + b + 2):
        return math.exp(lbt) * betacf(a, b, x) / a
    return 1.0 - math.exp(lbt) * betacf(b, a, 1.0 - x) / b


def t_cdf5(y):
    """F_5 in closed form (nu = 5), vectorised: 1/2 + (θ + sinθ cosθ (1 + (2/3)cos²θ))/π, θ = atan(y/√5)."""
    th = np.arctan(np.asarray(y, dtype=float) / math.sqrt(5.0))
    c = np.cos(th)
    return 0.5 + (th + np.sin(th) * c * (1.0 + (2.0 / 3.0) * c * c)) / math.pi


def t_pdf(y, nu):
    return math.exp(math.lgamma((nu + 1) / 2) - math.lgamma(nu / 2)) / math.sqrt(nu * math.pi) * \
        (1 + y * y / nu) ** (-(nu + 1) / 2)


def t_tail_terms(K, nu):
    """T0 = P(|y|>K), T1 = E[|y|;|y|>K], T2 = E[y²;|y|>K] for y ~ t_nu (§4.3), from the small argument nu/(nu+K²)."""
    xs = nu / (nu + K * K)                                        # = 1 − x
    T0 = betainc(nu / 2, 0.5, xs)
    T2 = nu / (nu - 2) * betainc(nu / 2 - 1, 1.5, xs)
    T1 = 2 * (nu + K * K) / (nu - 1) * t_pdf(K, nu)
    return T0, T1, T2


def t_lower(yf, nu):
    """F_nu(y_f) and U2(y_f) = E[y²; y < y_f] for y_f < 0."""
    xs = nu / (nu + yf * yf)
    return 0.5 * betainc(nu / 2, 0.5, xs), 0.5 * nu / (nu - 2) * betainc(nu / 2 - 1, 1.5, xs)


TRUTH_CHUNK = 2_000_000
BLOCK_THRESHOLD = 1_000_000_000     # the exact sum is used up to 1e9 tick levels; above, the bounded block method (IC3-22)
BLOCK_EXACT_J = 10_000              # levels j <= this are always summed exactly
BLOCK_DY = 0.01                     # block width in standardised units y


def _central_exact(P, mu, b, tick, K, p0, j_from, j_to):
    """Σ_{j_from..j_to} p_j ln(round(j·tick,10)/p0)², cells clipped to y ∈ [−K, K] (the frozen §4.3 sum)."""
    tot = 0.0
    for c0 in range(j_from, j_to + 1, TRUTH_CHUNK):                    # chunked: exact, memory bounded (IC3-21)
        j = np.arange(c0, min(c0 + TRUTH_CHUNK, j_to + 1), dtype=np.float64)
        ylo = np.clip((np.log(np.maximum((j - 0.5) * tick, 1e-300) / P) - mu) / b, -K, K)
        yhi = np.clip((np.log((j + 0.5) * tick / P) - mu) / b, -K, K)
        pj = t_cdf5(yhi) - t_cdf5(ylo)
        p1 = np.round(j * tick, 10)                                   # IC3-14
        tot += float(np.sum(pj * np.log(p1 / p0) ** 2))
    return tot


def _t5_upper(y):
    """S(y) = P(Y > y), Q1(y) = E[Y; Y > y], Q2(y) = E[Y²; Y > y] for y ≥ 0 (ν = 5), from the small argument."""
    nu = 5.0
    xs = nu / (nu + y * y)
    return (0.5 * betainc(nu / 2, 0.5, xs), (nu + y * y) / (nu - 1) * t_pdf(y, nu),
            0.5 * nu / (nu - 2) * betainc(nu / 2 - 1, 1.5, xs))


def _t5_interval_moments(y1, y2):
    """M_k = ∫_{y1}^{y2} y^k f_5(y) dy, k = 0, 1, 2, each from tail quantities on the side of the interval
    (no cancellation of near-1 values)."""
    if y1 >= 0:
        a, b_ = _t5_upper(y1), _t5_upper(y2)
        return a[0] - b_[0], a[1] - b_[1], a[2] - b_[2]
    if y2 <= 0:
        a, b_ = _t5_upper(-y2), _t5_upper(-y1)                      # mirror: ∫_{y1}^{y2} = ∫_{−y2}^{−y1} on the other side
        return a[0] - b_[0], -(a[1] - b_[1]), a[2] - b_[2]
    l0, l1, l2 = _t5_interval_moments(y1, 0.0)
    r0, r1, r2 = _t5_interval_moments(0.0, y2)
    return l0 + r0, l1 + r1, l2 + r2


def _central_blocked(P, mu, b, tick, K, p0):
    """The §4.3 central sum by exact levels at both ends and below BLOCK_EXACT_J, and by blocks of full interior cells
    replaced by the continuous integral with a PROVEN per-block bound (IC3-22). Returns (sum, bound, blocks, exact)."""
    nu = 5.0
    c1 = (nu + 1) / (2 * math.sqrt(nu))
    A_ = mu + math.log(P / p0)
    y = lambda price: (math.log(price / P) - mu) / b                        # noqa: E731
    jlo = max(1, math.floor(P * math.exp(mu - K * b) / tick - 0.5))
    jhi = math.ceil(P * math.exp(mu + K * b) / tick + 0.5)
    fl = max(jlo, math.ceil(P * math.exp(mu - K * b) / tick + 0.5), BLOCK_EXACT_J + 1)
    while fl <= jhi and y((fl - 0.5) * tick) < -K:
        fl += 1
    fh = math.floor(P * math.exp(mu + K * b) / tick - 0.5)
    while fh >= fl and y((fh + 0.5) * tick) > K:
        fh -= 1
    if fh - fl < 1000:                                                   # nothing worth blocking
        return _central_exact(P, mu, b, tick, K, p0, jlo, jhi), 0.0, 0, jhi - jlo + 1
    total = _central_exact(P, mu, b, tick, K, p0, jlo, fl - 1) + _central_exact(P, mu, b, tick, K, p0, fh + 1, jhi)
    n_exact = (fl - jlo) + (jhi - fh)
    bound, nblk = 0.0, 0
    grow = math.exp(b * BLOCK_DY)
    j1 = fl
    while j1 <= fh:
        j2 = min(fh, max(j1, math.floor(j1 * grow)))                    # block of full cells j1..j2
        p_lo, p_hi = (j1 - 0.5) * tick, (j2 + 0.5) * tick
        y1, y2 = y(p_lo), y(p_hi)
        M0, M1, M2 = _t5_interval_moments(y1, y2)
        total += A_ * A_ * M0 + 2 * A_ * b * M1 + b * b * M2
        ymin = 0.0 if y1 <= 0 <= y2 else min(abs(y1), abs(y2))
        fmax = t_pdf(ymin, nu)
        Lmax = max(abs(math.log(p_lo / p0)), abs(math.log(p_hi / p0)))
        W = p_hi - p_lo
        bound += (tick * tick * W * fmax / (12 * b * p_lo ** 3)) * (2 * Lmax * (c1 / b + 1) + 1 + Lmax)
        r = 5e-11 + p_hi * 2.3e-16                                       # rounding of j·tick to 10 decimals
        bound += (2 * Lmax / p_lo) * r * M0
        nblk += 1
        j1 = j2 + 1
    return total, bound, nblk, n_exact


def uvol_truth_w2(P, mu, b, tick, K=None, force_blocks=False):
    """Exact E[r̃_u² | P_{u−1}, h_u] in W2 (§4.3) with the per-step error bound and the acceptance loop.
    P: latent previous price; b = c·m_u·f_u·sqrt(h_u). Returns (q, E, K used, accepted).
    Central sums above BLOCK_THRESHOLD levels (or force_blocks) use the block method; its proven bound is added to
    E_u, so the frozen acceptance E_u ≤ 1e-6·q covers it (IC3-22)."""
    nu = SPEC["garch"]["nu"]
    if nu != 5:
        raise ValueError("the closed-form central CDF is for nu = 5")
    p0 = round(round(P / tick) * tick, 10)
    A_ = mu + math.log(P / p0)
    floor = SPEC["price_floor_ticks"] * tick
    delta_f = -math.log(1 - 1 / (2 * SPEC["price_floor_ticks"] - 1))
    Lg = math.log(p0 / tick)
    K = K or SPEC["t_K0"]
    while True:
        jlo = max(1, math.floor(P * math.exp(mu - K * b) / tick - 0.5))
        jhi = math.ceil(P * math.exp(mu + K * b) / tick + 0.5)
        if force_blocks or jhi - jlo + 1 > BLOCK_THRESHOLD:
            central, Eb, _, _ = _central_blocked(P, mu, b, tick, K, p0)
        else:
            central, Eb = _central_exact(P, mu, b, tick, K, p0, jlo, jhi), 0.0
        T0, T1, T2 = t_tail_terms(K, nu)
        q = central + A_ * A_ * T0 + b * b * T2
        yf = min(-K, (math.log(floor / P) - mu) / b)
        Ff, U2 = t_lower(yf, nu)
        E = delta_f * (2 * (abs(A_) * T0 + b * T1) + delta_f * T0) + Ff * (Lg * Lg + 2 * A_ * A_) + 2 * b * b * U2 + Eb
        if E <= SPEC["t_acc"] * q:
            return q, E, K, True
        if K >= SPEC["t_Kmax"]:
            return q, E, K, False
        K = min(2 * K, SPEC["t_Kmax"])


def truth_series(world, cls, lat, inno, tau):
    """q_u for u = 1..n−1 (r̃_u), exact, and the W2 acceptance count."""
    a, p = cls
    A_, P_ = reid.ASSETS[a], reid.PERIODS[p]
    tick, mu = A_["tick"], A_["drift"]
    kinds = {"lr": rip2.q_kinds("log_returns", "C1", a, None)}
    q, fails = [], 0
    c = math.sqrt((SPEC["garch"]["nu"] - 2) / SPEC["garch"]["nu"])
    for u in range(1, len(lat)):
        m_u = 1 + A_["act"] * math.sin(2 * math.pi * u / 64)
        f_u = 2 if tau is not None and u >= tau else 1
        if world == "W1":
            q.append(rip2.uvol_truth_step(lat[u - 1], mu, sigma_k(a, p) * m_u * f_u, tick, kinds)["lr"])
        else:
            b = c * m_u * f_u * math.sqrt(inno["h"][u])
            qq, _, _, ok = uvol_truth_w2(lat[u - 1], mu, b, tick)
            q.append(qq)
            fails += 0 if ok else 1
    return q, fails


# ================= utility (§4.2) =================
def uratio(s, tau):
    """R̂ = mean(s, t = τ..τ+63) / mean(s, t = τ−64..τ−1); s[0] is t = 1."""
    s = np.asarray(s, dtype=float)
    post, pre = s[tau - 1:tau + 63], s[tau - 65:tau - 1]
    return float(post.mean() / pre.mean()) if pre.mean() > 0 else math.inf


def rstar(q, tau):
    q = np.asarray(q, dtype=float)
    return float(q[tau - 1:tau + 63].sum() / q[tau - 65:tau - 1].sum())


def r_class(cls):
    a, p = cls
    mu, sk, act = reid.ASSETS[a]["drift"], sigma_k(a, p), reid.ASSETS[a]["act"]
    base = sk * sk * (1 + act * act / 2)
    return (mu * mu + 4 * base) / (mu * mu + base)


def observed_s(cand, x):
    if cand == "B-AF":
        return rip2.observed_s("affine_level", "C2", x)
    if cand == "B-LRS":
        return rip2.observed_s("level_residual", "C2", x)
    return np.asarray(x, dtype=float) ** 2


def utility_worlds(world, fam, null_fam, n):
    """The four paired series of one utility pair (IC-02): planted shift and act worlds from the planted family's
    draws; null no-shift and act = 0 worlds from the null family's draws. Also the latent paths and innovations."""
    inno = innovations(world, fam["cls"], member_stream(fam, 0), n)
    lat_s, obs_s = path(world, fam["cls"], inno, tau=fam["tau"])
    _, obs_a = path(world, fam["cls"], inno)
    inno_n = innovations(world, null_fam["cls"], member_stream(null_fam, 0), n)
    lat_n, obs_n = path(world, null_fam["cls"], inno_n)
    _, obs_n0 = path(world, null_fam["cls"], inno_n, act_zero=True)
    return {"inno": inno, "lat_s": lat_s, "obs_s": obs_s, "obs_a": obs_a,
            "inno_n": inno_n, "lat_n": lat_n, "obs_n": obs_n, "obs_n0": obs_n0}


def utility_pairs(base, world):
    fpc = SPEC["util_fpc"]
    return list(zip(eval_families(base, "util_planted", world, 1, fpc), eval_families(base, "util_null", world, 1, fpc)))


def truth_job(base, world, n):
    """Exact U-vol* truth q_u of every utility pair (shared by every candidate of the world)."""
    rows, fails = [], {"planted": 0, "null": 0}
    for fam, fn in utility_pairs(base, world):
        w = utility_worlds(world, fam, fn, n)
        q_s, f_s = truth_series(world, fam["cls"], w["lat_s"], w["inno"], fam["tau"])
        q_n, f_n = truth_series(world, fn["cls"], w["lat_n"], w["inno_n"], None)
        rows.append({"q_planted": q_s, "q_null": q_n})
        fails["planted"] += f_s
        fails["null"] += f_n
    return {"pairs": rows, "w2_truth_failures": fails}


def utility_family(world, fam, null_fam, cands, n, q_s, q_n):
    """Per-family utility values of every candidate (IC-02 pairing), given the exact truth."""
    a = fam["cls"][0]
    w = utility_worlds(world, fam, null_fam, n)
    out = {}
    for c in cands:
        s_s = observed_s(c, transform(c, w["obs_s"], a, fam))
        s_a = observed_s(c, transform(c, w["obs_a"], a, fam))
        s_n = observed_s(c, transform(c, w["obs_n"], null_fam["cls"][0], null_fam))
        s_n0 = observed_s(c, transform(c, w["obs_n0"], null_fam["cls"][0], null_fam))
        ev = rip2.uevent(s_s, fam["tau"])
        evn = rip2.uevent(s_n, None)
        row = {"uact_planted": rip2.uact_detect(s_a), "uact_null": rip2.uact_detect(s_n0),
               "uevent_flag_planted": ev["flag"], "uevent_success": ev["success"], "uevent_flag_null": evn["flag"]}
        if c not in LEVEL_CANDS:
            Rh, Rs = uratio(s_s, fam["tau"]), rstar(q_s, fam["tau"])
            row.update({"uvol_rho_planted": rip2.uvol_rho(s_s, q_s), "uvol_rho_null": rip2.uvol_rho(s_n, q_n),
                        "uratio_hat": Rh, "uratio_rstar": Rs, "uratio_err": abs(math.log(Rh / Rs)),
                        "uratio_rk": r_class(fam["cls"])})
        out[c] = row
    return out


# ================= jobs (resumable) =================
def dev_families(world, g, mult):
    per = SPEC["dev_per_class"] * mult // g
    return [make_family(SEEDS["dev"], "dev", world, g, cls, i) for cls in CLASSES for i in range(per)]


def eval_families(base, role, world, g, fpc):
    return [make_family(base, role, world, g, cls, i) for cls in CLASSES for i in range(fpc)]


def realise(cand, world, fams, n, keep_x=False):
    """Summaries (and optionally outputs) of every member of every family: arrays (families, g, 108).
    keep_x: True, False, or a predicate on the family (outputs kept only where it holds)."""
    S, X = [], []
    for f in fams:
        keep = keep_x(f) if callable(keep_x) else keep_x
        a = f["cls"][0]
        sf, xf = [], []
        for m in range(f["g"]):
            _, obs = path(world, f["cls"], innovations(world, f["cls"], member_stream(f, m), n))
            x = transform(cand, obs, a, f)
            sf.append(summary(x, cand in LEVEL_CANDS))
            if keep:
                xf.append(x)
        S.append(sf)
        X.append(xf)
    return np.array(S), X


def _tick(c):
    return reid.ASSETS[c[0]]["tick"]


def _allowed(delta):
    return np.array([math.isclose(_tick(c), delta, rel_tol=1e-12) for c in CLASSES])


def identity_scenario(cand, world, sc, ev_base, ev_role, n):
    """Per-unit predictions of every attacker in one (candidate, world, scenario)."""
    g = SCEN[sc]
    show = cand == CONTROL
    tcand = "M1" if show else cand
    mults = SPEC["mults"]
    dev4 = dev_families(world, g, max(mults))
    per_cls4 = len(dev4) // len(CLASSES)
    per1 = per_cls4 * min(mults) // max(mults)
    S4, X4 = realise(tcand, world, dev4, n, keep_x=(lambda f: g == 1 and f["idx"] < per1))
    y4 = [f["cls"] for f in dev4]
    ev = eval_families(ev_base, ev_role, world, g, SPEC["fpc"][sc])
    Se, Xe = realise(tcand, world, ev, n, keep_x=True)
    y = [f["cls"] for f in ev]
    oh = (lambda fs: np.array([onehot(_tick(f["cls"])) for f in fs])) if show else None

    def subset(mult):
        per = per_cls4 * mult // max(mults)
        return np.array([f["idx"] < per for f in dev4])

    P = {}
    sel1 = subset(1)
    F1 = S4[sel1][:, :, :N_FEAT]
    y1 = [c for c, s in zip(y4, sel1) if s]
    Fe = Se[:, :, :N_FEAT]
    allowed = [_allowed(_tick(f["cls"])) for f in ev] if show else None
    if g == 1:
        d1, e1 = F1[:, 0], Fe[:, 0]
        if show:
            d1 = np.hstack([d1, oh([f for f, s in zip(dev4, sel1) if s])])
            e1 = np.hstack([e1, oh(ev)])
        P["A1"] = a1(d1, y1, e1)
        P["A3"] = a3([x[0] for x, s in zip(X4, sel1) if s], y1, [x[0] for x in Xe])
    else:
        d1, e1 = F1, Fe
        if show:
            d1 = np.concatenate([d1, np.repeat(oh([f for f, s in zip(dev4, sel1) if s])[:, None, :], g, axis=1)], axis=2)
            e1 = np.concatenate([e1, np.repeat(oh(ev)[:, None, :], g, axis=1)], axis=2)
        P["A4a"], P["A4b"] = a4(d1, y1, e1)
    for mult in mults:
        sel = subset(mult)
        ym = [c for c, s in zip(y4, sel) if s]
        Sm = S4[sel]
        if g == 1:
            dF, eF = Sm[:, 0, :N_FEAT], Se[:, 0, :N_FEAT]
            if show:
                dF = np.hstack([dF, oh([f for f, s in zip(dev4, sel) if s])])
                eF = np.hstack([eF, oh(ev)])
            P[f"A2x{mult}"] = a2(dF, ym, eF)
        a7 = A7Model(Sm.reshape(-1, N_SUMMARY), [c for c in ym for _ in range(g)])
        ld = a7.logdens(Se.reshape(-1, N_SUMMARY)).reshape(len(ev), g, len(CLASSES)).sum(axis=1)
        P[f"A7x{mult}"] = [argmax_classes(ld[i], allowed[i] if show else None) for i in range(len(ev))]
        P[f"A8x{mult}"] = a8(Sm.mean(axis=1), ym, Se.mean(axis=1), ev_allowed=allowed)
        if mult == max(mults):
            shrink = a7.shrink
    if cand in A6_TRACTABLE:
        P["A6"] = [A.argmax(a6_scores(tcand, xs, _tick(f["cls"]) if show else None)) for f, xs in zip(ev, Xe)]
    return {"labels": [list(c) for c in y], "pred": {k: [list(c) for c in v] for k, v in P.items()},
            "a7_shrinkage_x4": shrink}


SET_BASE = {"eval": SEEDS["eval"], "confirm": SEEDS["confirm"], "build": SEEDS["build_holdout"], "smoke": SEEDS["smoke"]}
REGISTERED_SETS = ("eval", "confirm")


class NotAuthorised(Exception):
    """The registered sets are scored only in the authorised RUN (separate founder authorisation)."""


def _guard(set_name, authorised_run):
    if set_name in REGISTERED_SETS and authorised_run is not True:
        raise NotAuthorised(f"set '{set_name}' (seeds {SET_BASE[set_name]}) needs the RUN authorisation")


def run_job(set_name, cand, world, n=None, truth=None, authorised_run=False):
    """One (set, candidate, world) job: identity in every scenario, and utility (not for the control or the build set).
    truth: the world's truth_job output (required for utility)."""
    _guard(set_name, authorised_run)
    n = n or SPEC["n"]
    base = SET_BASE[set_name]
    res = {"set": set_name, "candidate": cand, "world": world, "identity": {}, "utility": None, "c_v1": "ok"}
    try:
        for sc in SCEN:
            res["identity"][sc] = identity_scenario(cand, world, sc, base, "eval", n)
        if cand != CONTROL and set_name != "build":
            res["utility"] = utility_job(cand, world, n, base, truth)
    except WorldError as e:
        res["c_v1"] = f"FAIL: {e}"
    return res


def utility_job(cand, world, n, base, truth):
    rows = []
    for (f, fn), tq in zip(utility_pairs(base, world), truth["pairs"]):
        r = utility_family(world, f, fn, [cand], n, tq["q_planted"], tq["q_null"])
        rows.append({"class": list(f["cls"]), **r[cand]})
    return {"families": rows, "w2_truth_failures": truth["w2_truth_failures"]}


def job_path(out_dir, set_name, cand, world):
    return Path(out_dir) / f"{set_name}__{cand}__{world}.json"


def run_jobs(out_dir, set_name, cands, worlds=WORLDS, n=None, authorised_run=False):
    """Resumable: a job whose file exists is skipped. Order does not affect any result (all draws are keyed)."""
    _guard(set_name, authorised_run)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    n = n or SPEC["n"]
    done = []
    for world in worlds:
        truth = None
        if set_name != "build":
            tp = Path(out_dir) / f"{set_name}__truth__{world}.json"
            if not tp.exists():
                try:
                    tp.write_text(json.dumps(truth_job(SET_BASE[set_name], world, n)))
                except WorldError as e:
                    tp.write_text(json.dumps({"c_v1": f"FAIL: {e}", "pairs": None}))
            truth = json.loads(tp.read_text())
        for cand in cands:
            p = job_path(out_dir, set_name, cand, world)
            if p.exists():
                continue
            if truth is not None and truth.get("pairs") is None:
                res = {"set": set_name, "candidate": cand, "world": world, "c_v1": truth["c_v1"], "identity": {},
                       "utility": None}
            else:
                res = run_job(set_name, cand, world, n, truth, authorised_run)
            p.write_text(json.dumps(res))
            done.append(p.name)
    return done


def load_jobs(out_dir, set_name):
    jobs = {}
    for p in sorted(Path(out_dir).glob(f"{set_name}__*__W?.json")):
        if "__truth__" in p.name:
            continue
        j = json.loads(p.read_text())
        jobs[(j["candidate"], j["world"])] = j
    return jobs


# ================= evaluation (§5, §7) =================
def acc_vectors(pred, labels):
    return rip2.acc_vectors([tuple(p) for p in pred], [tuple(c) for c in labels])


def bootstrap_sets(labels, B, rng):
    return rip2.bootstrap_sets([tuple(c) for c in labels], B, rng)


def ci_of_mean(v, sets):
    bs = np.array([v[s].mean() for s in sets])
    return [float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))]


ATT_ORDER = ["A6", "A7x4", "A8x4", "A1", "A2x4", "A3", "A4a", "A4b"]


def max_attacker(pred, labels, target):
    """IC3-16: the attacker with the highest mean accuracy for the target (identity value: x4 for A2/A7/A8)."""
    best, bv = None, -1.0
    for att in ATT_ORDER:
        if att in pred:
            v = acc_vectors(pred[att], labels)[target]
            if v.mean() > bv:
                best, bv = att, float(v.mean())
    return best, acc_vectors(pred[best], labels)[target]


def evaluate(jobs: dict, set_name="eval", rip2_results=None, B=None):
    """jobs[(cand, world)] -> job dict. Returns the §5 matrix, the §7 gates, floors, selection and FCs."""
    B = B or SPEC["B"]
    seed = {"eval": SEEDS["eval_bootstrap"], "confirm": SEEDS["confirm_bootstrap"]}.get(set_name, SET_BASE[set_name] + 90)
    out = {"matrix": [], "gates": {}, "floors": {}, "classes": {}, "reductions": {}, "selection": {}, "fc": {},
           "scope_sentence_M3_M6": SCOPE_SENTENCE}
    cands = sorted({c for c, _ in jobs}, key=ALL_CELLS.index)
    for world in WORLDS:
        rng = np.random.default_rng(seed + (0 if world == "W1" else 1))
        if ("B-LR", world) not in jobs:
            continue
        ref = jobs[("B-LR", world)]
        sets = {sc: bootstrap_sets(ref["identity"][sc]["labels"], B, rng) for sc in SCEN}
        uref = ref["utility"]
        usets = bootstrap_sets([r["class"] for r in uref["families"]], B, rng) if uref else None
        for cand in cands:
            job = jobs.get((cand, world))
            if job is None:
                continue
            for sc in SCEN:
                idn = job["identity"].get(sc)
                if not idn:
                    continue
                lab, pred = idn["labels"], idn["pred"]
                row = {"candidate": cand, "world": world, "scenario": sc, "c_v1": job["c_v1"]}
                for t in TARGETS:
                    att, v = max_attacker(pred, lab, t)
                    row[f"I_{t}"] = float(v.mean())
                    row[f"I_{t}_ci95"] = ci_of_mean(v, sets[sc])
                    row[f"I_{t}_attacker"] = att
                    ratt, rv = max_attacker(ref["identity"][sc]["pred"], ref["identity"][sc]["labels"], t)
                    row[f"reduction_{t}"] = rip2.paired_diff(rv, v, sets[sc])
                row["per_attacker"] = {a: {t: float(acc_vectors(p, lab)[t].mean()) for t in TARGETS}
                                       for a, p in pred.items()}
                row["coverage"] = "A6 exact" if "A6" in pred else ("A7/A8 + feature attackers" if cand not in LEVEL_CANDS
                                                                  else "feature attackers")
                sat, fc6 = {}, {}
                for att in ("A2", "A7", "A8"):
                    if f"{att}x4" in pred:
                        sat[att] = {t: rip2.paired_diff(acc_vectors(pred[f"{att}x4"], lab)[t],
                                                        acc_vectors(pred[f"{att}x2"], lab)[t], sets[sc]) for t in TARGETS}
                row["unsaturated"] = {att: [t for t in TARGETS if d[t]["ci95"][0] > 0] for att, d in sat.items()}
                row["saturation"] = sat
                for t in TARGETS:
                    fc6[t] = rip2.paired_diff(acc_vectors(pred["A8x4"], lab)[t], acc_vectors(pred["A7x4"], lab)[t], sets[sc])
                row["fc6_a8_minus_a7"] = fc6
                row["attacker_sensitive"] = [t for t in TARGETS if fc6[t]["ci95"][0] > 0]
                if cand in ("M3W32", "M3W128", "M4", "M5", "M6"):
                    row["scope"] = SCOPE_SENTENCE
                out["matrix"].append(row)
            if job.get("utility"):
                out["floors"].setdefault(cand, {})[world] = utility_summary(job["utility"], uref, usets)
    out["gates"] = gates(out, jobs, rip2_results, seed + 7)
    out.update(select(out, cands))
    return out


def utility_summary(u, uref, usets):
    fam = u["families"]

    def mean(key):
        v = np.array([float(r[key]) for r in fam])
        return float(v.mean()), ci_of_mean(v, usets)
    s = {k: mean(k) for k in ("uact_planted", "uact_null", "uevent_success", "uevent_flag_planted", "uevent_flag_null")}
    if "uvol_rho_planted" in fam[0]:
        s["uvol_rho_planted"] = mean("uvol_rho_planted")
        s["uvol_rho_null"] = mean("uvol_rho_null")
        s["uratio_median_err"] = float(np.median([r["uratio_err"] for r in fam]))
    s["w2_truth_failures"] = u.get("w2_truth_failures")
    if uref is not None and "uvol_rho_planted" in s:
        rf = {k: float(np.mean([float(r[k]) for r in uref["families"]])) for k in
              ("uvol_rho_planted", "uact_planted", "uact_null", "uevent_success", "uevent_flag_null")}
        rf["uratio_median_err"] = float(np.median([r["uratio_err"] for r in uref["families"]]))
        chk = {
            "uvol": s["uvol_rho_planted"][0] >= 0.95 * rf["uvol_rho_planted"],
            "uact_power": s["uact_planted"][0] >= 0.90 * rf["uact_planted"],
            "uact_false_alarm": s["uact_null"][0] <= rf["uact_null"] + 0.02,
            "uevent_success": s["uevent_success"][0] >= 0.90 * rf["uevent_success"],
            "uevent_null_flag": s["uevent_flag_null"][0] <= rf["uevent_flag_null"] + 0.02,
            "uratio": s["uratio_median_err"] <= rf["uratio_median_err"] + 0.05,
        }
        s["floors"] = chk
        s["B_LR"] = rf
    return s


def gates(out, jobs, rip2_results, cv2_seed):
    g = {}
    # C-V1: generator failures
    g["C-V1"] = {f"{c}|{w}": j["c_v1"] for (c, w), j in jobs.items()}
    # C-V2: A7 (x4) >= lower end of A6's interval, W1, B-LR and B-AF
    cv2 = {}
    for row in out["matrix"]:
        if row["world"] == "W1" and row["candidate"] in ("B-LR", "B-AF"):
            job = jobs[(row["candidate"], "W1")]["identity"][row["scenario"]]
            for t in TARGETS:
                v6 = acc_vectors(job["pred"]["A6"], job["labels"])[t]
                v7 = acc_vectors(job["pred"]["A7x4"], job["labels"])[t]
                rng = np.random.default_rng(cv2_seed)
                ci6 = ci_of_mean(v6, bootstrap_sets(job["labels"], SPEC["B"], rng))
                cv2[f"{row['candidate']}|{row['scenario']}|{t}"] = {"A6": float(v6.mean()), "A6_ci95": ci6,
                                                                    "A7x4": float(v7.mean()), "pass": float(v7.mean()) >= ci6[0]}
    g["C-V2"] = {"cells": cv2, "pass": all(v["pass"] for v in cv2.values()) if cv2 else None}
    # C-V3: RIP-2 reproduction (A6 cells and the B-LR utility)
    if rip2_results is not None:
        g["C-V3"] = c_v3(out, rip2_results)
    # C-V4: B-LR U-act null false alarm <= 0.07; U-event null flag reported against 0.072
    cv4 = {}
    for w, s in out["floors"].get("B-LR", {}).items():
        cv4[w] = {"uact_null": s["uact_null"][0], "pass": s["uact_null"][0] <= SPEC["uact_null_limit"],
                  "uevent_null_flag": s["uevent_flag_null"][0], "rip2_reference": 0.072}
    g["C-V4"] = cv4
    return g


def c_v3(out, r2):
    cells = {}
    for row in out["matrix"]:
        if row["world"] != "W1" or row["candidate"] not in ("B-LR", "B-AF"):
            continue
        rep, cond = ("log_returns", "C12") if row["candidate"] == "B-LR" else ("affine_level", "C2")
        ref = [c for c in r2["cells"] if c["representation"] == rep and c["condition"] == cond
               and c["delta"] == "hidden" and c["attacker"] == "A6" and c["scenario"] == row["scenario"]]
        if ref:
            for t in TARGETS:
                mine = row["per_attacker"]["A6"][t]
                cells[f"{row['candidate']}|{row['scenario']}|{t}"] = {"rip2": ref[0][t], "rip3_A6": mine}
    return {"cells": cells, "note": "compared within RIP-3 bootstrap intervals in the report (IC3-19)"}


def select(out, cands):
    """§7.3–§7.5: reductions, classes P / S, selection per class, failure conditions."""
    M = {(r["candidate"], r["world"], r["scenario"]): r for r in out["matrix"]}
    red, cls, passes = {}, {}, {}
    for c in cands:
        if c in ("B-LR", CONTROL):
            continue
        ok = {}
        for t in TARGETS:
            ok[t] = all((c, w, sc) in M and M[(c, w, sc)][f"reduction_{t}"]["ci95"][0] > 0
                        for w in WORLDS for sc in ("ind", "g16"))
        g16 = [M[(c, w, "g16")]["reduction_joint"]["diff"] for w in WORLDS if (c, w, "g16") in M]
        red[c] = {"reduces": ok, "rank_value_g16_joint": min(g16) if g16 else None}
        fl = out["floors"].get(c, {})
        if c in LEVEL_CANDS or not fl or any("floors" not in fl[w] for w in fl):
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
            pool = [c for c in pool if c in A6_TRACTABLE]
        pool.sort(key=lambda c: (-red[c]["rank_value_g16_joint"], _simplicity(c)))
        sel[K] = {"chosen": pool[0] if pool else None, "nearest_competitor": pool[1] if len(pool) > 1 else None,
                  "ranked": pool}
        fc[f"FC-1_{K}"] = not pool
    fc["FC-2"] = [c for c in red if c not in LEVEL_CANDS and not red[c]["reduces"]["joint"] and
                  all((c, "W1", sc) in M and M[(c, "W1", sc)]["reduction_joint"]["ci95"][0] > 0 for sc in ("ind", "g16"))]
    fc["FC-4"] = cv2 is False
    fc["FC-5"] = [r["candidate"] + "|" + r["world"] + "|" + r["scenario"] for r in out["matrix"] if any(r["unsaturated"].values())]
    fc["FC-6"] = [r["candidate"] + "|" + r["world"] + "|" + r["scenario"] for r in out["matrix"] if r["attacker_sensitive"]]
    return {"reductions": red, "classes": cls, "selection": sel, "fc": fc, "pareto": pareto(out, cls)}


def _simplicity(c):
    secrets = 1 if c.startswith("M2") else 0
    params = 1 if c[:2] in ("M2", "M3") else 0
    return (secrets, params, ALL_CELLS.index(c))


def pareto(out, cls):
    M = {(r["candidate"], r["world"], r["scenario"]): r for r in out["matrix"]}
    keys_hi = ("uvol_rho_planted", "uact_planted", "uevent_success")
    keys_lo = ("uact_null", "uevent_flag_null")
    res = {}
    for K in ("P", "S"):
        members = [c for c, k in cls.items() if k == K]
        for c in members:
            dominated_by = []
            for d in members:
                if d == c:
                    continue
                ide = [(M[(d, w, sc)]["I_joint"], M[(c, w, sc)]["I_joint"]) for w in WORLDS for sc in ("ind", "g16")
                       if (d, w, sc) in M and (c, w, sc) in M]
                ut = []
                for w in WORLDS:
                    fd, fc_ = out["floors"][d].get(w), out["floors"][c].get(w)
                    if fd and fc_:
                        ut += [(fd[k][0], fc_[k][0]) for k in keys_hi]
                        ut += [(-fd[k][0], -fc_[k][0]) for k in keys_lo]
                        ut += [(-fd["uratio_median_err"], -fc_["uratio_median_err"])]
                weak = all(a <= b for a, b in ide) and all(a >= b for a, b in ut)
                strict = any(a < b for a, b in ide) or any(a > b for a, b in ut)
                if ide and weak and strict:
                    dominated_by.append(d)
            res[c] = {"class": K, "dominated_by": dominated_by, "frontier": not dominated_by}
    return res


def file_sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()
