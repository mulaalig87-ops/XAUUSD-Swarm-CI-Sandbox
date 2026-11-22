"""TP-30 — re-identification accuracy per representation (WP7-04 §3; candidate س 158, 196). SYNTHETIC ONLY.
Design FD-01-D44 (pre-registered), with the reviewer's minimum conditions (WP9-05 review R1, answer C).

Question (س 158): can a classifier identify the ASSET or the PERIOD from blinded samples better than chance?
«تُقاس الدقة، ويُعلن الناتج». The threshold is [معلّق] (CS-01-04, record 7 §13 #29): NO threshold here —
measure and declare, including bad results. A language-mind attacker is not available in the build: not run.

Universe: K = 4 synthetic assets × P = 4 periods = 16 balanced classes. Each class has known, distinct
statistics (price level, tick size, volatility, drift by asset; volatility regime and level growth by
period; an intraday activity pattern by asset). Class labels never appear in what the attacker sees
(no names, no order: samples are shuffled; the attacker receives bare lists of numbers).

Threat model (Kerckhoffs): the attacker knows every blinding METHOD and the DISTRIBUTION of its secret
parameters, and holds unblinded public data of every candidate; it does NOT hold the drawn parameters or the
vault key. It therefore builds its own labelled DEVELOPMENT set by blinding public candidates with
parameters it draws itself; the TEST set is blinded with independent draws (custody's). Every test sample
has its own parameter family (one family per sample), so samples are independent units and a Wilson
interval over samples is valid; the same-family pooling scenario is NOT measured here (declared).

Representations measured (all six cards of representations.py; WP7-04 says "five" — the sixth card,
volatility_time, is measured too): log_returns (scaled by a secret scale), tick_grid (secret c, Δ = the
asset's tick), level_residual (secret m), affine_level (secret a, b), activity_time (returns re-indexed by
update count: wall-clock removed), volatility_time (cumulative squared returns).

Attackers (fixed before the test set is seen):
  A1  1-nearest-neighbour on standardised features (distance: Euclidean on z-scores from the dev set);
  A2  nearest class centroid on the same standardised features (a trained classifier);
  A3  direct series matching, independent of the feature set: 1-NN on the concatenation of the
      standardised series' quantile function (41 points) and its log periodogram in 16 bands.
Features (A1, A2), computed on the representation output x and on its first difference dx:
  distribution (mean, sd, skewness, kurtosis, quantiles 5/25/50/75/95), dependence (ACF lags 1–5 of x and
  of |dx|), spectrum (power share in 4 bands of dx), volatility / extremes (share |z| > 3, max |z|, ACF of
  dx² lag 1), shape / sequence (mean run length of sign(dx), share of zero changes, mean gap of x mod 1).
Outputs per representation and attacker: top-1 accuracy for asset (chance 1/4), period (1/4) and joint
(1/16), each with its count, a 95 % Wilson interval over independent test samples, and confusion matrices.
"""
from __future__ import annotations

import cmath
import math
import random

from .representations import affine_level, level_residual, log_returns, tick_grid, volatility_time

K, P = 4, 4
ASSETS = [  # level, tick, daily-ish vol per step, drift per step, activity pattern amplitude
    {"level": 1800.0, "tick": 0.01, "vol": 0.0009, "drift": 0.00002, "act": 0.6},
    {"level": 30.0, "tick": 0.001, "vol": 0.0014, "drift": 0.0, "act": 0.3},
    {"level": 1.1, "tick": 0.00001, "vol": 0.0005, "drift": -0.00001, "act": 0.1},
    {"level": 150.0, "tick": 0.01, "vol": 0.0011, "drift": 0.00001, "act": 0.45},
]
PERIODS = [{"volx": 0.8, "growth": 1.00}, {"volx": 1.0, "growth": 1.15}, {"volx": 1.6, "growth": 1.30},
           {"volx": 1.2, "growth": 1.45}]
TP30 = {"n": 512, "dev_per_class": 25, "test_per_class": 25, "seed_dev": 3001, "seed_test": 3002,
        "seed_order": 3003, "representations": ["log_returns", "tick_grid", "level_residual", "affine_level",
                                                 "activity_time", "volatility_time"],
        "attackers": ["A1_knn_features", "A2_centroid_features", "A3_series_match"]}


# ---------------- synthetic world ----------------
def simulate(asset, period, n, rnd):
    a, p = ASSETS[asset], PERIODS[period]
    price = a["level"] * p["growth"]
    out = []
    for t in range(n):
        act = 1 + a["act"] * math.sin(2 * math.pi * t / 64)          # intraday activity pattern
        r = a["drift"] + a["vol"] * p["volx"] * act * rnd.gauss(0, 1)
        price *= math.exp(r)
        out.append(round(round(price / a["tick"]) * a["tick"], 10))   # on the asset's tick grid
    return out


def blind(rep, prices, asset, rnd):
    """Custody-side blinding with freshly drawn secret parameters (one family per sample)."""
    if rep == "log_returns":
        return log_returns(prices, scale=math.exp(rnd.uniform(-7.5, -5.0)))
    if rep == "tick_grid":
        return tick_grid(prices, rnd.uniform(-1, 1) * max(prices), ASSETS[asset]["tick"])
    if rep == "level_residual":
        return level_residual(prices, rnd.choice([0.5, 1.0, 5.0, 10.0]) * ASSETS[asset]["tick"] * 100)
    if rep == "affine_level":
        return affine_level(prices, math.exp(rnd.uniform(-3, 3)), rnd.uniform(-1000, 1000))
    if rep == "activity_time":
        return log_returns(prices)   # one update per step in this world: values in update order (declared)
    if rep == "volatility_time":
        return volatility_time(prices)
    raise ValueError(rep)


def make_set(rep, per_class, seed):
    rnd = random.Random(seed)
    xs, ys = [], []
    for asset in range(K):
        for period in range(P):
            for _ in range(per_class):
                xs.append(blind(rep, simulate(asset, period, TP30["n"], rnd), asset, rnd))
                ys.append((asset, period))
    order = list(range(len(xs)))
    random.Random(seed + 7).shuffle(order)             # no order leaks the label
    return [xs[i] for i in order], [ys[i] for i in order]


# ---------------- features (A1, A2) ----------------
def _moments(v):
    n = len(v)
    m = sum(v) / n
    sd = math.sqrt(sum((x - m) ** 2 for x in v) / n) or 1e-300
    sk = sum(((x - m) / sd) ** 3 for x in v) / n
    ku = sum(((x - m) / sd) ** 4 for x in v) / n
    return m, sd, sk, ku


def _acf(v, lag):
    m = sum(v) / len(v)
    d = [x - m for x in v]
    den = sum(x * x for x in d) or 1e-300
    return sum(d[i] * d[i + lag] for i in range(len(d) - lag)) / den


def _q(v, ps):
    s = sorted(v)
    return [s[min(len(s) - 1, int(p * (len(s) - 1)))] for p in ps]


def _fft(a):
    n = len(a)
    if n == 1:
        return a[:]
    if n & (n - 1):
        return [sum(a[t] * cmath.exp(-2j * math.pi * k * t / n) for t in range(n)) for k in range(n)]
    e, o = _fft(a[0::2]), _fft(a[1::2])
    out = [0j] * n
    for k in range(n // 2):
        w = cmath.exp(-2j * math.pi * k / n) * o[k]
        out[k], out[k + n // 2] = e[k] + w, e[k] - w
    return out


def _bands(v, nb):
    m = sum(v) / len(v)
    n = 1 << (len(v).bit_length() - 1)               # largest power of two ≤ len(v)
    spec = [abs(c) ** 2 for c in _fft([complex(x - m) for x in v[:n]])][1:n // 2]
    tot = sum(spec) or 1e-300
    step = len(spec) / nb
    return [sum(spec[int(i * step):int((i + 1) * step)]) / tot for i in range(nb)]


def features(x):
    dx = [x[i + 1] - x[i] for i in range(len(x) - 1)]
    f = []
    for v in (x, dx):
        m, sd, sk, ku = _moments(v)
        f += [m, sd, sk, ku] + _q(v, [0.05, 0.25, 0.5, 0.75, 0.95])
    f += [_acf(x, k) for k in range(1, 6)] + [_acf([abs(d) for d in dx], k) for k in range(1, 6)]
    f += _bands(dx, 4)
    m, sd, _, _ = _moments(dx)
    z = [(d - m) / sd for d in dx]
    f += [sum(abs(v) > 3 for v in z) / len(z), max(abs(v) for v in z), _acf([d * d for d in dx], 1)]
    signs = [1 if d > 0 else (-1 if d < 0 else 0) for d in dx]
    runs, cur = [], 1
    for i in range(1, len(signs)):
        if signs[i] == signs[i - 1]:
            cur += 1
        else:
            runs.append(cur)
            cur = 1
    runs.append(cur)
    f += [sum(runs) / len(runs), sum(1 for d in dx if d == 0) / len(dx), sum(abs(v) % 1 for v in x) / len(x)]
    return f


def _standardiser(rows):
    k = len(rows[0])
    mu = [sum(r[j] for r in rows) / len(rows) for j in range(k)]
    sd = [math.sqrt(sum((r[j] - mu[j]) ** 2 for r in rows) / len(rows)) or 1.0 for j in range(k)]
    return lambda r: [(r[j] - mu[j]) / sd[j] for j in range(k)]


def _nn(train, labels, q):
    best = min(range(len(train)), key=lambda i: sum((a - b) ** 2 for a, b in zip(train[i], q)))
    return labels[best]


def series_signature(x):
    m, sd, _, _ = _moments(x)
    z = [(v - m) / sd for v in x]
    return _q(z, [i / 40 for i in range(41)]) + [math.log(b + 1e-12) for b in _bands(x, 16)]


# ---------------- attackers: they receive only blinded series and dev labels ----------------
def attack(name, dev_x, dev_y, test_x):
    if name in ("A1_knn_features", "A2_centroid_features"):
        fd = [features(x) for x in dev_x]
        z = _standardiser(fd)
        dz = [z(f) for f in fd]
        tz = [z(features(x)) for x in test_x]
        if name == "A1_knn_features":
            return [_nn(dz, dev_y, q) for q in tz]
        classes = sorted(set(dev_y))
        cents = {c: [sum(r[j] for r, y in zip(dz, dev_y) if y == c) / sum(1 for y in dev_y if y == c)
                     for j in range(len(dz[0]))] for c in classes}
        return [min(classes, key=lambda c: sum((a - b) ** 2 for a, b in zip(cents[c], q))) for q in tz]
    if name == "A3_series_match":
        sd = [series_signature(x) for x in dev_x]
        z = _standardiser(sd)
        dz = [z(s) for s in sd]
        return [_nn(dz, dev_y, z(series_signature(x))) for x in test_x]
    raise ValueError(name)


def wilson(k, n, z=1.96):
    if n == 0:
        return [0.0, 1.0]
    p = k / n
    c = (p + z * z / (2 * n)) / (1 + z * z / n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return [round(max(0.0, c - h), 4), round(min(1.0, c + h), 4)]


def run_tp30(spec=TP30) -> dict:
    rows = []
    for rep in spec["representations"]:
        dev_x, dev_y = make_set(rep, spec["dev_per_class"], spec["seed_dev"])
        test_x, test_y = make_set(rep, spec["test_per_class"], spec["seed_test"])
        for att in spec["attackers"]:
            pred = attack(att, dev_x, dev_y, test_x)
            n = len(test_y)
            ka = sum(p[0] == y[0] for p, y in zip(pred, test_y))
            kp = sum(p[1] == y[1] for p, y in zip(pred, test_y))
            kj = sum(p == y for p, y in zip(pred, test_y))
            conf_a = [[sum(1 for p, y in zip(pred, test_y) if y[0] == i and p[0] == j) for j in range(K)] for i in range(K)]
            conf_p = [[sum(1 for p, y in zip(pred, test_y) if y[1] == i and p[1] == j) for j in range(P)] for i in range(P)]
            rows.append({"representation": rep, "attacker": att, "n_test": n,
                         "asset": {"correct": ka, "accuracy": round(ka / n, 4), "chance": round(1 / K, 4),
                                   "wilson95": wilson(ka, n), "confusion": conf_a},
                         "period": {"correct": kp, "accuracy": round(kp / n, 4), "chance": round(1 / P, 4),
                                    "wilson95": wilson(kp, n), "confusion": conf_p},
                         "joint": {"correct": kj, "accuracy": round(kj / n, 4), "chance": round(1 / (K * P), 4),
                                   "wilson95": wilson(kj, n)}})
    return {"experiment": "TP-30", "rows": rows, "threshold": None,
            "not_run": ["language-mind attacker (not available)", "same-family pooling scenario"]}
