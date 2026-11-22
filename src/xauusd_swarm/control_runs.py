"""Stage 9, gap G5 / WP9-02 — control code and synthetic worlds for the §11.2 null cards: TP-21/tool
(WP7-04 §2.1): «الأثر الحقيقي يُرفض عدمه» (positive) and «العالم الصفري لا يُرفض عدمه» (negative), with the
two rates registered before running (مع-15). SYNTHETIC ONLY. Deterministic by the seed in the world.

A world is a plain dict (hashed by the controls layer): {"card", "kind": "real"|"null", "n", "reps",
"surrogates", "seed", "alpha", ...}. `run_world(world)` returns {"rejection_rate": r, "rejections": k,
"reps": R} — the observed rate over R independent synthetic series.

Test per series: surrogate rank test, p = (1 + #{T(surrogate) >= T(x)}) / (1 + M); reject if p <= alpha.
Statistic per card (FD-01-D30; the architecture names the target quantity, not the statistic):
- full_shuffle  (target: any temporal dependence): T = |lag-1 autocorrelation|.
    real: Gaussian AR(1), phi = 0.3.         null: iid Gaussian.
- iaaft         (target: nonlinear structure):    T = lag-1 autocorrelation of x².
    real: ARCH(1), a1 = 0.6 (linear acf ≈ 0, squares correlated).  null: Gaussian AR(1), phi = 0.5
    (stationary linear Gaussian — the card's assumption holds; this is the calibration arm, TP-82(a)).
- pair_shuffle_vol_blocks (target: state prediction by sign, asymmetry kept): two known volatility
    states (blocks frozen as an input, as from Discovery); T = |mean(|r_{t+1}| after s_t=-1) −
    mean(|r_{t+1}| after s_t=+1)|.  real: after a negative sign the next size is scaled up (lev = 1.6)
    within each state.  null: iid pairs within each state.
    v1 FAILED its positive control (FL-007). v2 (FD-01-D31, pre-registered): same worlds, statistic
    computed within each state (`stat_pairs_within`). v1 stays runnable so its failure is reproducible.

NOT run here (open, recorded in docs/STAGE9_PLAN.md):
- time_reversal: the card gives one deterministic surrogate; the test procedure that yields a null
  distribution is «غير معرّف في المعمارية».
- zero_cond_mean: the generative model family is «غير معرّف في المعمارية».
- block_bootstrap: not a null; its control is TP-81 (coverage), a separate experiment.
- TP-82 arm (b) (IAAFT under non-stationarity): a separate experiment.
"""
from __future__ import annotations

import math
import random

from .nulls import full_shuffle, iaaft, pair_shuffle_blocks

RUNNABLE = ("full_shuffle", "iaaft", "pair_shuffle_vol_blocks", "pair_shuffle_vol_blocks/v2")
VERSION_OF = {"pair_shuffle_vol_blocks/v2": "pair_shuffle_vol_blocks"}   # FD-01-D31 (after FL-007)


# ---------------- statistics ----------------
def acf1(x):
    m = sum(x) / len(x)
    d = [v - m for v in x]
    den = sum(v * v for v in d)
    return 0.0 if den == 0 else sum(d[i] * d[i + 1] for i in range(len(d) - 1)) / den


def stat_full_shuffle(x):
    return abs(acf1(x))


def stat_iaaft(x):
    return acf1([v * v for v in x])


def stat_pairs_within(s, a, blocks):
    """v2 (FD-01-D31): the sign→next-size difference WITHIN each volatility state, scaled by the state's
    mean size, averaged with weights = number of within-state pairs."""
    tot, w = 0.0, 0
    for lab in dict.fromkeys(blocks):
        neg, pos, sizes = [], [], []
        for t in range(len(s) - 1):
            if blocks[t] == lab and blocks[t + 1] == lab:
                (neg if s[t] == -1 else pos).append(a[t + 1])
                sizes.append(a[t + 1])
        if neg and pos and sum(sizes) > 0:
            m = sum(sizes) / len(sizes)
            tot += len(sizes) * abs(sum(neg) / len(neg) - sum(pos) / len(pos)) / m
            w += len(sizes)
    return tot / w if w else 0.0


def stat_pairs(s, a):
    neg = [a[t + 1] for t in range(len(s) - 1) if s[t] == -1]
    pos = [a[t + 1] for t in range(len(s) - 1) if s[t] == 1]
    if not neg or not pos:
        return 0.0
    return abs(sum(neg) / len(neg) - sum(pos) / len(pos))


# ---------------- synthetic worlds ----------------
def _ar1(n, phi, rnd):
    x, out = 0.0, []
    for _ in range(n + 50):
        x = phi * x + rnd.gauss(0, 1)
        out.append(x)
    return out[50:]


def _arch1(n, a1, rnd):
    r, out = 0.0, []
    for _ in range(n + 50):
        r = math.sqrt(1 - a1 + a1 * r * r) * rnd.gauss(0, 1)
        out.append(r)
    return out[50:]


def _pairs(n, lev, rnd):
    blocks = ["lo" if (t // (n // 4)) % 2 == 0 else "hi" for t in range(n)]
    s, a = [], []
    prev = 1
    for t in range(n):
        scale = (1.0 if blocks[t] == "lo" else 3.0) * (lev if prev == -1 else 1.0)
        s.append(rnd.choice((-1, 1)))
        a.append(abs(rnd.gauss(0, 1)) * scale)
        prev = s[-1]
    return s, a, blocks


# ---------------- one series, one test ----------------
def _p_value(t_obs, t_surr):
    return (1 + sum(1 for t in t_surr if t >= t_obs)) / (1 + len(t_surr))


def _one(card, kind, n, m, rnd):
    if card == "full_shuffle":
        x = _ar1(n, 0.3, rnd) if kind == "real" else [rnd.gauss(0, 1) for _ in range(n)]
        return _p_value(stat_full_shuffle(x), [stat_full_shuffle(full_shuffle(x, rnd)) for _ in range(m)])
    if card == "iaaft":
        x = _arch1(n, 0.6, rnd) if kind == "real" else _ar1(n, 0.5, rnd)
        return _p_value(stat_iaaft(x), [stat_iaaft(iaaft(x, rnd, iterations=20)) for _ in range(m)])
    if card == "pair_shuffle_vol_blocks":
        s, a, blocks = _pairs(n, 1.6 if kind == "real" else 1.0, rnd)
        surr = []
        for _ in range(m):
            s2, a2 = pair_shuffle_blocks(s, a, blocks, rnd)
            surr.append(stat_pairs(s2, a2))
        return _p_value(stat_pairs(s, a), surr)
    if card == "pair_shuffle_vol_blocks/v2":
        s, a, blocks = _pairs(n, 1.6 if kind == "real" else 1.0, rnd)
        surr = []
        for _ in range(m):
            s2, a2 = pair_shuffle_blocks(s, a, blocks, rnd)
            surr.append(stat_pairs_within(s2, a2, blocks))
        return _p_value(stat_pairs_within(s, a, blocks), surr)
    raise ValueError(f"no control run for card {card!r} (see module docstring)")


def run_world(world: dict) -> dict:
    """Control code: the observed rejection rate of the card's null on R synthetic series."""
    card, kind = world["card"], world["kind"]
    if card not in RUNNABLE or kind not in ("real", "null"):
        raise ValueError("card in RUNNABLE, kind real|null")
    rnd = random.Random(world["seed"])
    k = sum(1 for _ in range(world["reps"])
            if _one(card, kind, world["n"], world["surrogates"], rnd) <= world["alpha"])
    return {"rejection_rate": round(k / world["reps"], 9), "rejections": k, "reps": world["reps"]}


# Pre-registered criteria (FD-01-D30), fixed BEFORE the first run (مع-15):
CRITERIA = {"real": {"metric": "rejection_rate", "op": ">=", "value": 0.80},
            "null": {"metric": "rejection_rate", "op": "<=", "value": 0.15}}
REPS = {"full_shuffle": 60, "iaaft": 40, "pair_shuffle_vol_blocks": 60, "pair_shuffle_vol_blocks/v2": 60}


def world_spec(card, kind, *, n=128, reps=None, surrogates=19, seed=20261117, alpha=0.05):
    reps = REPS[card] if reps is None else reps
    return {"card": card, "kind": kind, "n": n, "reps": reps, "surrogates": surrogates,
            "seed": seed + (0 if kind == "real" else 1), "alpha": alpha}
