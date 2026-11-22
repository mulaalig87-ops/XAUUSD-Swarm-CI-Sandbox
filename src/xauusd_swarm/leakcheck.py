"""Stage 9, gap G4 / WP9-03 — the graded planted-leak test (candidate §12, س 1523–1543; WP7-04 §4, TP-50).
SYNTHETIC ONLY. Design under FD-01-D38 (pre-registered).

Purpose (س 1525): measure how likely the lineage check is to MISS each leak type — not assume it catches
them all. Report per type (س 1538–1541): the detection rate of the lineage check, and the statistical
detection rate (inflation of the nominal rejection rate on null worlds); types detected by neither are
recorded as KNOWN BLIND SPOTS and never reported as "no leak". Success = a complete report, not detecting
every type (WP7-04 §4). Planting success does not show the absence of unplanted types (س 1543).

The lineage check («فحص النسب»): its actor and procedure are undefined (مع-58). This module DEFINES one
(FD-01-D38), so every lineage result below measures THIS check:
- features are built through `FeatureBuilder`, which records every operation automatically (the
  architecture's automatic capture mode); the record is the lineage;
- `lineage_check(lineage, ctx)` applies fixed rules to the record (each rule names its source):
    R-target     an input is the tested target s_t (or anything after t)            (س 965)
    R-window     a centered (or forward) window                                       (ت2, س 1530)
    R-norm       normalisation with statistics of the whole tested slice               (ت3)
    R-version    a data version revised after the decision time (version registry)     (ت4)
    R-estimate   a parameter estimated on a range overlapping the tested slice         (ت5)
    R-time       market-time alignment of a field whose availability lags              (ت6, §6.5)
    R-provenance an input artefact without registered provenance (unknown = flagged)   (ت7)
  Code that bypasses the builder is invisible to the check — by construction, as in reality.

Statistical detection: on NULL worlds (iid returns, sign-symmetric: no real predictability), the test of
E[s_t·h_t] = 0 on the tested slice (z statistic, two-sided, alpha 0.05). Its rejection rate over R worlds
is the statistical detection rate; nominal 0.05.

Leak types (plant implementations; each is a natural bug):
  t1 h_t uses s_t directly (col "s", lag 0)                               — via builder
  t2 centered moving average of r over 5 bars                              — via builder
  t3 r_{t−1} normalised by the whole tested slice's mean and sd            — via builder
  t4 E_t from a revised data version (revision blends 0.5·r_t in)          — via builder (version recorded)
  t5 20 noise features weighted by OLS coefficients fit on [150, 600)      — via builder (range recorded)
  t6 field x_t = r_t + noise, available one bar late, aligned on market time — via builder (basis recorded)
  t7 h_t read from a cached artefact of an earlier run (centered smooth)   — via builder (artefact id only)
  t8 weak partial leak: a fraction f of bars use sign(r_t) through direct
     indexing outside the builder; f ∈ {0.01, 0.03, 0.10, 0.30} (the smallest tested fraction with inflation
     is reported; it is not a true minimum detectable leak — levels in between were not tested; س 1536)
  t9 «ترميز ضمني للحجم التالي داخل E_t»: E_t = noise + 0.3·(|r_{t+1}| − E|r|) inside a vendor field;
     included by founder decision (WP7-04 §4, CS-04-08 «يُدرج»); the candidate text still marks it
     not in force (تا4-02) — both are cited.
  t0 TP-50.0: clean pipeline (no plant) — false-alarm rates of both methods.
"""
from __future__ import annotations

import math
import random

N, SPLIT = 600, 300                     # tested slice = [SPLIT, N); Discovery = [0, SPLIT)


# ======================= automatic lineage capture ================================================
class FeatureBuilder:
    def __init__(self, ctx):
        self.ctx, self.lineage = ctx, []

    def col(self, field, lag, basis="availability"):
        self.lineage.append({"op": "col", "field": field, "lag": lag, "basis": basis})
        data = self.ctx["fields"][field]
        shift = lag
        if basis == "availability":
            shift = lag + self.ctx["availability_lag"].get(field, 0)
        return [data[t - shift] if 0 <= t - shift < len(data) else 0.0 for t in range(len(data))]

    def rolling_mean(self, x, length, kind):
        self.lineage.append({"op": "rolling", "kind": kind, "length": length})
        n, out = len(x), []
        for t in range(n):
            lo, hi = (t - length + 1, t + 1) if kind == "causal" else (t - length // 2, t + length // 2 + 1)
            w = x[max(0, lo):min(n, hi)]
            out.append(sum(w) / len(w))
        return out

    def normalize(self, x, source):
        self.lineage.append({"op": "normalize", "source": source})
        out = []
        for t in range(len(x)):
            if source == "slice":
                w = x[SPLIT:] if t >= SPLIT else x[:SPLIT]
            else:                                            # past only
                w = x[max(0, t - 100):t] or [0.0, 1.0]
            m = sum(w) / len(w)
            sd = math.sqrt(sum((v - m) ** 2 for v in w) / len(w)) or 1.0
            out.append((x[t] - m) / sd)
        return out

    def load(self, dataset, version):
        self.lineage.append({"op": "load", "dataset": dataset, "version": version})
        return self.ctx["versions"][(dataset, version)]["data"]

    def estimate_ols(self, xs, y, start, end):
        """Fit y ~ xs on [start, end) by gradient-free normal equations (diagonal: features independent)."""
        self.lineage.append({"op": "estimate", "range": [start, end]})
        beta = []
        for x in xs:
            num = sum(x[t] * y[t] for t in range(start, end))
            den = sum(x[t] * x[t] for t in range(start, end)) or 1.0
            beta.append(num / den)
        return beta

    def cache_read(self, artefact):
        self.lineage.append({"op": "cache", "artefact": artefact})
        return self.ctx["cache"][artefact]


def lineage_check(lineage, ctx) -> list:
    """The rules R-* above. Returns the list of findings (empty = nothing flagged)."""
    found = []
    for op in lineage:
        if op["op"] == "col" and (op["field"] in ctx["targets"] or op["lag"] < 0):
            found.append("R-target")
        if op["op"] == "col" and op["basis"] == "market" and ctx["availability_lag"].get(op["field"], 0) > op["lag"]:
            found.append("R-time")
        if op["op"] == "rolling" and op["kind"] != "causal":
            found.append("R-window")
        if op["op"] == "normalize" and op["source"] == "slice":
            found.append("R-norm")
        if op["op"] == "load":
            v = ctx["versions"].get((op["dataset"], op["version"]))
            if v is None or v["revised_at"] > ctx["decision_time"]:
                found.append("R-version")
        if op["op"] == "estimate" and op["range"][1] > SPLIT:
            found.append("R-estimate")
        if op["op"] == "cache" and op["artefact"] not in ctx["provenance"]:
            found.append("R-provenance")
    return sorted(set(found))


# ======================= worlds and plants ========================================================
def _ctx(rnd):
    r = [rnd.gauss(0, 1) for _ in range(N)]
    s = [1.0 if v > 0 else -1.0 for v in r]
    return {"r": r, "s": s, "fields": {"r": r, "s": s}, "targets": {"s"}, "availability_lag": {},
            "versions": {}, "cache": {}, "provenance": set(), "decision_time": SPLIT}


def build(kind, rnd, frac=None):
    """Returns (h, lineage, ctx, target) for one synthetic world with leak `kind` planted."""
    c = _ctx(rnd)
    fb = FeatureBuilder(c)
    r, s = c["r"], c["s"]
    target = s
    if kind == "t0":
        h = fb.rolling_mean(fb.col("r", 1), 5, "causal")
    elif kind == "t1":
        h = fb.col("s", 0)
    elif kind == "t2":
        h = fb.rolling_mean(fb.col("r", 0), 5, "centered")
    elif kind == "t3":
        h = fb.normalize(fb.col("r", 1), "slice")
    elif kind == "t4":
        e = [rnd.gauss(0, 1) for _ in range(N)]
        c["versions"][("E", "v1")] = {"data": e, "revised_at": 0}
        c["versions"][("E", "v2")] = {"data": [a + 0.5 * b for a, b in zip(e, r)], "revised_at": N + 10}
        h = fb.load("E", "v2")
    elif kind == "t5":
        xs = [[rnd.gauss(0, 1) for _ in range(N)] for _ in range(20)]
        for j, x in enumerate(xs):
            c["fields"][f"x{j}"] = x
        cols = [fb.col(f"x{j}", 0) for j in range(20)]
        beta = fb.estimate_ols(cols, s, 150, N)
        h = [sum(b * x[t] for b, x in zip(beta, cols)) for t in range(N)]
    elif kind == "t6":
        c["fields"]["x"] = [v + rnd.gauss(0, 1) for v in r]
        c["availability_lag"]["x"] = 1
        h = fb.col("x", 0, basis="market")
    elif kind == "t7":
        smooth = []
        for t in range(N):
            w = r[max(0, t - 2):min(N, t + 3)]
            smooth.append(sum(w) / len(w))
        c["cache"]["features_run_0417.bin"] = smooth             # produced by an earlier run, no provenance
        h = fb.cache_read("features_run_0417.bin")
    elif kind == "t8":
        base = fb.col("r", 1)
        h = [s[t] if rnd.random() < frac else base[t] for t in range(N)]   # bypasses the builder
    elif kind == "t9":
        mabs = math.sqrt(2 / math.pi)
        vendor = [rnd.gauss(0, 1) + 0.3 * ((abs(r[t + 1]) if t + 1 < N else mabs) - mabs) for t in range(N)]
        c["fields"]["E_vendor"] = vendor
        h = fb.col("E_vendor", 0)
    else:
        raise ValueError(kind)
    return h, fb.lineage, c, target


def z_test(h, target):
    v = [h[t] * target[t] for t in range(SPLIT, N)]
    m = sum(v) / len(v)
    sd = math.sqrt(sum((x - m) ** 2 for x in v) / (len(v) - 1))
    if sd == 0:
        return 0.0 if m == 0 else 1.0 * (1 if m > 0 else -1) * 1e9
    return m / (sd / math.sqrt(len(v)))


def two_sided_p(z):
    return math.erfc(abs(z) / math.sqrt(2))


# ======================= TP-50 runner =============================================================
TP50 = {"reps": 100, "alpha": 0.05, "tolerance": 0.05, "detect_rate": 0.5, "seed": 5001,
        "types": ["t0", "t1", "t2", "t3", "t4", "t5", "t6", "t7", "t8", "t9"], "t8_fracs": [0.01, 0.03, 0.10, 0.30]}
STATES = ("كُشف بفحص النسب", "كُشف إحصائيًا", "لم يُكشف بأي منهما: نقطة عمى معروفة")


def run_type(kind, spec=TP50, frac=None):
    rnd = random.Random(spec["seed"] + spec["types"].index(kind) * 1000 + int((frac or 0) * 1e4))
    lin = stat = 0
    rules: dict = {}
    for _ in range(spec["reps"]):
        h, lineage, ctx, target = build(kind, rnd, frac)
        f = lineage_check(lineage, ctx)
        lin += bool(f)
        for x in f:
            rules[x] = rules.get(x, 0) + 1
        stat += two_sided_p(z_test(h, target)) <= spec["alpha"]
    lr, sr = lin / spec["reps"], stat / spec["reps"]
    return {"type": kind, "frac": frac, "lineage_rate": round(lr, 9), "stat_rejection_rate": round(sr, 9),
            "stat_inflated": sr > spec["alpha"] + spec["tolerance"], "rules": dict(sorted(rules.items())),
            "reps": spec["reps"]}


def classify(row, spec=TP50):
    states = []
    if row["lineage_rate"] >= spec["detect_rate"]:
        states.append(STATES[0])
    if row["stat_inflated"]:
        states.append(STATES[1])
    return states or [STATES[2]]


def run_tp50(spec=TP50) -> dict:
    rows = []
    for k in spec["types"]:
        if k == "t8":
            for f in spec["t8_fracs"]:
                row = run_type(k, spec, f)
                row["states"] = classify(row, spec)
                rows.append(row)
        else:
            row = run_type(k, spec)
            row["states"] = classify(row, spec) if k != "t0" else ["TP-50.0: false-alarm measurement"]
            rows.append(row)
    t8 = [r for r in rows if r["type"] == "t8"]
    detectable = [r["frac"] for r in t8 if r["stat_inflated"]]
    blind = sorted({r["type"] for r in rows if r["type"] != "t0" and r["states"] == [STATES[2]]})
    return {"experiment": "TP-50 (ت1–ت9) + TP-50.0", "rows": rows,
            # review R1-03: the smallest TESTED fraction with inflation — not a true detection threshold
            # (fractions between the tested levels were not run; R = 100)
            "t8_smallest_tested_fraction_with_inflation": min(detectable) if detectable else None,
            "known_blind_spots": blind, "report_complete": all("states" in r for r in rows)}


# ======================= control code for the matrix row (FD-01-D38 addendum) ======================
# Defined here, not in the run script, so that impl_sha256 (qualified name + source) does not depend on
# how the script is loaded (found when the reproduction test loaded the script under another name).
def tp50_report(world):
    rep = run_tp50({**TP50, **world.get("overrides", {})})
    return {"report_complete": 1 if rep["report_complete"] else 0, "report": rep}


def tp50_0(world):
    row = run_type("t0", {**TP50, **world.get("overrides", {})})
    return {"measured": 1, "lineage_false_alarm_rate": row["lineage_rate"],
            "stat_false_alarm_rate": row["stat_rejection_rate"]}
