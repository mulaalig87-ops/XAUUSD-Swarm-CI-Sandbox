"""Stage 9 — assumption experiments TP-81 (م5-05) and TP-82 (م5-06), WP7-04 §11 and §11.1. SYNTHETIC ONLY.

These are MEASURE-AND-DECLARE experiments: «معيارها القياس والإعلان، بلا عتبة عددية؛ والتسامح يُسجَّل قبل
التشغيل. ونجاحها الاصطناعي لا يثبت تحقق الافتراض في الذهب» (WP7-04 §11). There is no pass/fail; the
output is the measured values, each compared with the nominal value and the pre-registered tolerance
(FD-01-D33), and declared as "within tolerance" or "outside tolerance".

TP-81 — weak dependence and block length (block bootstrap, card «Bootstrap بالكتل», uncertainty only):
  quantity: the mean; interval: moving-block bootstrap percentile interval, nominal 0.95, B = 199;
  worlds with known dependence: iid (reference), short memory AR(1) phi = 0.5, long memory ARFIMA(0, d, 0)
  d = 0.3 (truncated MA(∞), 1000 weights); true mean 0; n = 400; block lengths b ∈ {1, 5, 10, 20, 40};
  measured: coverage of the true mean over R = 200 series per (world, b).

TP-82 — IAAFT under non-stationarity (§11.1, redesigned in round 12):
  statistic (the same in both arms): lag-1 autocorrelation of x² (as in TP-21/tool for IAAFT);
  test: surrogate rank test, M = 19 IAAFT surrogates (20 iterations), alpha = 0.05, n = 128, R = 40.
  arm (a) calibration: stationary linear Gaussian AR(1) phi = 0.5 — IAAFT valid by assumption.
  arm (b) non-stationary, NO planted nonlinearity, pre-registered patterns:
     level  — mean shifts by +2 sd at the midpoint;
     var    — sd doubles at the midpoint;
     spec   — AR coefficient changes from 0.0 to 0.8 at the midpoint.
  measured: false rejection rate per arm/pattern; surrogate diagnostics per surrogate:
     marginal match (exact by construction; checked), spectrum distance (relative L2 of amplitude
     spectra), and the NON-STATIONARITY PROFILE (§11.1, round 13): non-overlapping windows of length 32
     (4 windows); per window (1) mean, (2) variance, (3) spectral power in bands [1, 4) and [4, 16) of the
     window's DFT; profile distance = mean absolute difference between the original's and the surrogate's
     profiles, each component scaled by the original's overall sd of that component across windows (+ 1e-12).
  separation of failures (§11.1): inflation in (b) only, with (a) sound and surrogates not reproducing the
  profile → "failure of the null construction"; inflation in (a) → "failure of the statistic or procedure"
  and (b) is not read.
"""
from __future__ import annotations

import math
import random

from .nulls import _fft, amplitude_spectrum, iaaft

# ======================= TP-81 ===================================================================
TP81 = {"n": 400, "reps": 200, "B": 199, "level": 0.95, "blocks": [1, 5, 10, 20, 40],
        "worlds": {"iid": {}, "ar1": {"phi": 0.5}, "arfima": {"d": 0.3, "weights": 1000}},
        "tolerance": 0.03, "seed": 8101}


def _arfima_weights(d, k):
    w = [1.0]
    for j in range(1, k):
        w.append(w[-1] * (j - 1 + d) / j)
    return w


def tp81_series(world, n, rnd, cache):
    if world == "iid":
        return [rnd.gauss(0, 1) for _ in range(n)]
    if world == "ar1":
        x, out = 0.0, []
        for _ in range(n + 100):
            x = TP81["worlds"]["ar1"]["phi"] * x + rnd.gauss(0, 1)
            out.append(x)
        return out[100:]
    w = cache.setdefault("w", _arfima_weights(TP81["worlds"]["arfima"]["d"], TP81["worlds"]["arfima"]["weights"]))
    e = [rnd.gauss(0, 1) for _ in range(n + len(w))]
    k = len(w)
    return [sum(w[j] * e[t + k - 1 - j] for j in range(k)) for t in range(n)]


def block_ci_mean(x, b, B, level, rnd):
    """Moving-block bootstrap percentile interval for the mean (fast: prefix sums)."""
    n = len(x)
    pre = [0.0]
    for v in x:
        pre.append(pre[-1] + v)
    nb = math.ceil(n / b)
    last = n - nb * b + b                                   # length of the final, truncated block
    means = []
    for _ in range(B):
        s = 0.0
        for i in range(nb):
            st = rnd.randrange(0, n - b + 1)
            ln = b if i < nb - 1 else last
            s += pre[st + ln] - pre[st]
        means.append(s / n)
    means.sort()
    lo = means[max(0, int(math.floor((1 - level) / 2 * (B + 1))) - 1)]
    hi = means[min(B - 1, int(math.ceil((1 + level) / 2 * (B + 1))) - 1)]       # B = 199: indices 4 and 194
    return lo, hi


def run_tp81(spec: dict = TP81) -> dict:
    rnd, cache, rows = random.Random(spec["seed"]), {}, []
    for world in spec["worlds"]:
        series = [tp81_series(world, spec["n"], rnd, cache) for _ in range(spec["reps"])]
        for b in spec["blocks"]:
            cov = 0
            for x in series:
                lo, hi = block_ci_mean(x, b, spec["B"], spec["level"], rnd)
                cov += lo <= 0.0 <= hi
            c = cov / spec["reps"]
            rows.append({"world": world, "b": b, "coverage": round(c, 9), "coverage_se": _se(c, spec["reps"]),
                         "covered": cov, "reps": spec["reps"],
                         "nominal": spec["level"], "within_tolerance": abs(c - spec["level"]) <= spec["tolerance"]})
    return {"experiment": "TP-81", "rows": rows}


# ======================= TP-82 ===================================================================
TP82 = {"n": 128, "reps": 40, "M": 19, "iterations": 20, "alpha": 0.05, "window": 32,
        "bands": [[1, 4], [4, 16]], "patterns": ["level", "var", "spec"], "tolerance": 0.10, "seed": 8201,
        # v2 profile metric (FD-01-D34, after FL-009): change vector second half − first half, scaled by a
        # reference spread from an INDEPENDENT stationary calibration set (arm (a) process, own seed)
        "v2": {"calibration_reps": 40, "calibration_seed": 8301, "cutoff_factor": 2.0}}


def _se(rate, reps):
    """Binomial standard error of an estimated rate (review R1-03: precision shown with every rate)."""
    return round(math.sqrt(max(rate * (1 - rate), 1e-12) / reps), 6)


def _acf1(x):
    m = sum(x) / len(x)
    d = [v - m for v in x]
    den = sum(v * v for v in d)
    return 0.0 if den == 0 else sum(d[i] * d[i + 1] for i in range(len(d) - 1)) / den


def stat82(x):
    return _acf1([v * v for v in x])


def tp82_series(kind, n, rnd):
    h = n // 2
    if kind == "calib":
        x, out = 0.0, []
        for _ in range(n + 50):
            x = 0.5 * x + rnd.gauss(0, 1)
            out.append(x)
        return out[50:]
    if kind == "level":
        return [rnd.gauss(0, 1) + (2.0 if t >= h else 0.0) for t in range(n)]
    if kind == "var":
        return [rnd.gauss(0, 1) * (2.0 if t >= h else 1.0) for t in range(n)]
    if kind == "spec":
        x, out = 0.0, []
        for t in range(n):
            x = (0.8 if t >= h else 0.0) * x + rnd.gauss(0, 1)
            out.append(x)
        return out
    raise ValueError(kind)


def profile(x, window, bands):
    out = []
    for s in range(0, len(x) - window + 1, window):
        w = x[s:s + window]
        m = sum(w) / window
        var = sum((v - m) ** 2 for v in w) / window
        spec = [abs(c) ** 2 / window for c in _fft([complex(v - m) for v in w])]
        out.append([m, var] + [sum(spec[a:b]) for a, b in bands])
    return out


def profile_distance(p0, p1):
    k = len(p0[0])
    total = 0.0
    for j in range(k):
        col = [r[j] for r in p0]
        mu = sum(col) / len(col)
        sd = math.sqrt(sum((v - mu) ** 2 for v in col) / len(col)) + 1e-12
        total += sum(abs(a[j] - b[j]) for a, b in zip(p0, p1)) / (len(p0) * sd)
    return total / k


def half_change(x, window, bands):
    """v2: per component (mean, variance, band powers), mean over second-half windows − first-half windows."""
    p = profile(x, window, bands)
    h = len(p) // 2
    k = len(p[0])
    return [sum(r[j] for r in p[h:]) / (len(p) - h) - sum(r[j] for r in p[:h]) / h for j in range(k)]


def reference_scale(spec, rnd):
    """v2: per-component sd of the half-change vector over an independent stationary calibration set."""
    v = [half_change(tp82_series("calib", spec["n"], rnd), spec["window"], spec["bands"])
         for _ in range(spec["v2"]["calibration_reps"])]
    k = len(v[0])
    out = []
    for j in range(k):
        col = [r[j] for r in v]
        mu = sum(col) / len(col)
        out.append(math.sqrt(sum((c - mu) ** 2 for c in col) / (len(col) - 1)) + 1e-12)
    return out


def change_distance(c0, c1, scale):
    return sum(abs(a - b) / s for a, b, s in zip(c0, c1, scale)) / len(scale)


def spectrum_distance(x, y):
    ax, ay = amplitude_spectrum(x), amplitude_spectrum(y)
    return math.sqrt(sum((p - q) ** 2 for p, q in zip(ax, ay)) / sum(p * p for p in ax))


def run_tp82(spec: dict = TP82) -> dict:
    scale = reference_scale(spec, random.Random(spec["v2"]["calibration_seed"]))    # independent of the run
    rnd, rows = random.Random(spec["seed"]), []
    for kind in ["calib"] + spec["patterns"]:
        rej, sd_list, pd_list, v2_list, marg_ok = 0, [], [], [], True
        for _ in range(spec["reps"]):
            x = tp82_series(kind, spec["n"], rnd)
            p0 = profile(x, spec["window"], spec["bands"])
            c0 = half_change(x, spec["window"], spec["bands"])
            t0, ts = stat82(x), []
            for _ in range(spec["M"]):
                y = iaaft(x, rnd, iterations=spec["iterations"])
                marg_ok = marg_ok and sorted(y) == sorted(x)
                ts.append(stat82(y))
                sd_list.append(spectrum_distance(x, y))
                pd_list.append(profile_distance(p0, profile(y, spec["window"], spec["bands"])))
                v2_list.append(change_distance(c0, half_change(y, spec["window"], spec["bands"]), scale))
            p = (1 + sum(1 for t in ts if t >= t0)) / (1 + spec["M"])
            rej += p <= spec["alpha"]
        rate = rej / spec["reps"]
        # review R1-02: in arm (b) the tool's assumption is violated by design, so the rate is not a type-I
        # error rate under a valid null; it is named for what it is.
        rate_key = "false_rejection_rate" if kind == "calib" else "rejection_rate_under_assumption_violation"
        rows.append({"arm": "a" if kind == "calib" else "b", "world": kind, rate_key: round(rate, 9),
                     "rate_se": _se(rate, spec["reps"]),
                     "rejections": rej, "reps": spec["reps"], "nominal": spec["alpha"],
                     "within_tolerance": rate <= spec["alpha"] + spec["tolerance"],
                     "marginal_exact_all": marg_ok,
                     "spectrum_distance_mean": round(sum(sd_list) / len(sd_list), 6),
                     "profile_distance_mean_v1": round(sum(pd_list) / len(pd_list), 6),
                     "change_distance_mean_v2": round(sum(v2_list) / len(v2_list), 6)})
    a = rows[0]
    a["note"] = ("R = 40: the rate's standard error is about 0.035–0.05; 'within_tolerance' is a declaration "
                 "against the registered tolerance, not proof of calibration (review R1-03)")
    calib_pd = a["profile_distance_mean_v1"]
    calib_v2 = a["change_distance_mean_v2"]
    for r in rows[1:]:
        inflated = not r["within_tolerance"]
        r["profile_reproduced_v1"] = r["profile_distance_mean_v1"] <= calib_pd * (1 + spec["tolerance"] * 10)
        reproduces = r["change_distance_mean_v2"] <= calib_v2 * spec["v2"]["cutoff_factor"]   # FD-01-D34
        if not a["within_tolerance"]:
            r["reading"] = "not read: arm (a) inflated → failure of the statistic or procedure (§11.1)"
        elif inflated and not reproduces:
            r["reading"] = "failure of the null construction (§11.1): inflation in (b) only, (a) sound, profile not reproduced"
        elif inflated:
            r["reading"] = "inflation in (b) with profile reproduced: declared, not classified by §11.1"
        else:
            r["reading"] = "no inflation beyond tolerance"
        r["profile_reproduced_v2"] = reproduces
    return {"experiment": "TP-82", "rows": rows, "reading_uses": "v2 profile metric (FD-01-D34); v1 kept (FL-009)"}
