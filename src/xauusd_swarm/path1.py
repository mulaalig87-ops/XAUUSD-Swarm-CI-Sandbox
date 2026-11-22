"""Discovery path 1 — «الانتظامات التوزيعية» (distributional regularities), س 752, مك-91.
Founder decision OD-S9-01 («المسار 1»). The architecture gives the NAME only (index: «اسم فقط»); the
method below is a design under FD-01-D35, recorded with its card (docs/paths/PATH1_CARD.md).

What it does (a discovery tool, not a court): given a return series r_t and a frozen label per
observation (cells, e.g. regimes or sessions recorded before the scan), it proposes the cells whose
return DISTRIBUTION differs from the rest of the series.
- statistic per cell c: two-sample Kolmogorov–Smirnov distance D_c between {r_t : label_t = c} and
  {r_t : label_t ≠ c}; scan statistic T = max_c D_c.
- null: CIRCULAR ROTATION of the label sequence by a random offset (seeded). Rotation keeps the series
  exactly as it is (its dependence, its volatility clustering) and keeps the label runs, and breaks only
  the alignment between labels and returns. This is chosen so that dependence in r_t alone (e.g.
  volatility clustering, the "spurious effect" world) is not read as a cell regularity — a full shuffle
  of labels would break the runs and declare such dependence.
- decision: single-step max-T over cells (family-wise over the cells of one scan): cell c is proposed if
  D_c ≥ the (1 − alpha) quantile of the null distribution of T (M rotations, rank rule).
- output: proposals {cell, D, p_max} — candidates for the queue, never evidence (§9, ق-03).
Minimum rotation offset: n // 10 (so a rotation is not a near-identity).
v1 (rotation null) FAILED its positive control (FL-011). v2 (FD-01-D36): null = permutation of the cell
labels across label runs (`run_permuted`); everything else unchanged. v2 also FAILED (FL-011).
v3 (FD-01-D37, founder decision OD-S9-02): `scan_per_cell` — per-cell nulls by rotation, Holm across cells,
M = 199 rotations (Holm needs p <= alpha/3 to be attainable); worlds and criteria unchanged. v3 FAILED (0.66).
Review R1-01 (accepted): the rotation reference set (offsets in [n/10, n − n/10]) excludes the identity
and is not a group containing the observed alignment, and a linear series is not rotation-invariant: the
p-values of v1 and v3 are not shown valid. Path 1 is paused (OD-S9-03); see docs/paths/PATH1_CARD.md.
"""
from __future__ import annotations

import math
import random

from .numeric import finite_real


class PathError(ValueError):
    pass


def ks_distance(a, b):
    """Two-sample KS distance (exact for ties: steps evaluated at every distinct value)."""
    if not a or not b:
        return 0.0
    xa, xb = sorted(a), sorted(b)
    i = j = 0
    d = 0.0
    while i < len(xa) and j < len(xb):
        v = min(xa[i], xb[j])
        while i < len(xa) and xa[i] <= v:
            i += 1
        while j < len(xb) and xb[j] <= v:
            j += 1
        d = max(d, abs(i / len(xa) - j / len(xb)))
    return d


def cell_stats(r, labels, order=None):
    """Per-cell KS distance vs the rest. With `order` (indices of r sorted by value, from `sort_order`)
    one pass over the sorted series per cell — same values as `ks_distance`, without re-sorting."""
    cells = sorted(set(labels))
    if order is None:
        out = {}
        for c in cells:
            a = [v for v, lab in zip(r, labels) if lab == c]
            b = [v for v, lab in zip(r, labels) if lab != c]
            out[c] = ks_distance(a, b)
        return out
    n = len(r)
    out = {}
    for c in cells:
        na = sum(1 for lab in labels if lab == c)
        nb = n - na
        if na == 0 or nb == 0:
            out[c] = 0.0
            continue
        i = j = 0
        d = 0.0
        k = 0
        while k < n:
            v = r[order[k]]
            while k < n and r[order[k]] == v:           # a tie group moves both ECDFs at once
                if labels[order[k]] == c:
                    i += 1
                else:
                    j += 1
                k += 1
            d = max(d, abs(i / na - j / nb))
        out[c] = d
    return out


def sort_order(r):
    return sorted(range(len(r)), key=lambda t: r[t])


def runs_of(labels):
    """Label runs as (start, end, cell)."""
    out, s = [], 0
    for i in range(1, len(labels) + 1):
        if i == len(labels) or labels[i] != labels[s]:
            out.append((s, i, labels[s]))
            s = i
    return out


def run_permuted(labels, rng):
    """v2 null (FD-01-D36): keep run boundaries, permute which cell each run carries."""
    rs = runs_of(labels)
    cells = [c for _, _, c in rs]
    rng.shuffle(cells)
    out = []
    for (a, b, _), c in zip(rs, cells):
        out.extend([c] * (b - a))
    return out


def holm_reject(pvals: dict, alpha: float) -> set:
    out = set()
    for k, (c, p) in enumerate(sorted(pvals.items(), key=lambda kv: (kv[1], kv[0]))):
        if p <= alpha / (len(pvals) - k):
            out.add(c)
        else:
            break
    return out


def scan_per_cell(r, labels, *, rotations: int, alpha: float, rng: random.Random) -> dict:
    """v3 (FD-01-D37): per-cell statistic D_c with its OWN null distribution (rotation of the labels,
    the v1 null that protected against volatility clustering), Holm across the cells of the scan.
    Per-cell nulls avoid v1's contamination of the max and v2's invariance of the max to renaming."""
    if not isinstance(r, (list, tuple)) or len(r) < 20 or any(not finite_real(v) for v in r):
        raise PathError("r: at least 20 finite numbers")
    if not isinstance(labels, (list, tuple)) or len(labels) != len(r) or len(set(labels)) < 2:
        raise PathError("labels: one per observation, at least two cells")
    if isinstance(rotations, bool) or not isinstance(rotations, int) or rotations < 19:
        raise PathError("rotations: an integer >= 19")
    if not finite_real(alpha) or not 0 < alpha < 1:
        raise PathError("alpha in (0, 1)")
    n, order = len(r), sort_order(r)
    obs = cell_stats(r, labels, order)
    lo = max(1, n // 10)
    ge = {c: 0 for c in obs}
    for _ in range(rotations):
        k = rng.randrange(lo, n - lo + 1)
        rot = list(labels[k:]) + list(labels[:k])
        st = cell_stats(r, rot, order)
        for c in obs:
            ge[c] += st.get(c, 0.0) >= obs[c]
    pv = {c: (1 + ge[c]) / (1 + rotations) for c in obs}
    rej = holm_reject(pv, alpha)
    return {"stats": {c: round(v, 9) for c, v in obs.items()}, "p": {c: round(p, 9) for c, p in pv.items()},
            "proposals": [{"cell": c, "D": round(obs[c], 9), "p_holm_step": round(pv[c], 9)} for c in sorted(rej)]}


class _ConstrainedArrangements:
    """Uniform sampling of arrangements of cell labels over k maximal runs with FIXED counts per cell and
    NO two adjacent runs sharing a cell (v4.1, FD-01-D42). Exact: sequential sampling proportional to the
    number of completions (dynamic programming over remaining counts and the previous cell)."""

    def __init__(self, counts: dict):
        self.cells = sorted(counts)
        if len(self.cells) > 6:
            raise PathError("at most 6 cells (exact counting)")
        self.start = tuple(counts[c] for c in self.cells)
        self.memo: dict = {}

    def completions(self, rem, last):
        key = (rem, last)
        if key in self.memo:
            return self.memo[key]
        if sum(rem) == 0:
            return 1
        total = 0
        for i, n in enumerate(rem):
            if n and i != last:
                total += self.completions(rem[:i] + (n - 1,) + rem[i + 1:], i)
        self.memo[key] = total
        return total

    def total(self):
        return self.completions(self.start, -1)

    def sample(self, rng: random.Random):
        rem, last, out = self.start, -1, []
        while sum(rem):
            opts = [(i, self.completions(rem[:i] + (n - 1,) + rem[i + 1:], i)) for i, n in enumerate(rem)
                    if n and i != last]
            u = rng.randrange(sum(w for _, w in opts))
            for i, w in opts:
                if u < w:
                    break
                u -= w
            out.append(self.cells[i])
            rem, last = rem[:i] + (rem[i] - 1,) + rem[i + 1:], i
        return out


def constrained_permuted(labels, rng: random.Random, sampler=None):
    """v4.1 reference draw: run boundaries and lengths kept; per-cell run counts kept; no two adjacent
    runs share a cell (so the maximal-run structure is exactly preserved)."""
    rs = runs_of(labels)
    if sampler is None:
        cnt: dict = {}
        for _, _, c in rs:
            cnt[c] = cnt.get(c, 0) + 1
        sampler = _ConstrainedArrangements(cnt)
    cells = sampler.sample(rng)
    out = []
    for (a, b, _), c in zip(rs, cells):
        out.extend([c] * (b - a))
    return out


def scan_v41(r, labels, *, permutations: int, alpha: float, rng: random.Random) -> dict:
    """v4.1 (FD-01-D42, under OD-S9-05; review of v4 R1-01). H0: given the maximal run structure
    (boundaries and lengths) and the number of runs of each cell, every arrangement of the cells over the
    runs with no two adjacent runs sharing a cell is equally likely, independent of the returns. Reference:
    exact uniform draws from that set (`_ConstrainedArrangements`), so every reference sequence has the
    same runs as the observed one. Per-cell Monte Carlo p-value, Holm across cells."""
    if not isinstance(r, (list, tuple)) or len(r) < 20 or any(not finite_real(v) for v in r):
        raise PathError("r: at least 20 finite numbers")
    if not isinstance(labels, (list, tuple)) or len(labels) != len(r) or len(set(labels)) < 2:
        raise PathError("labels: one per observation, at least two cells")
    if isinstance(permutations, bool) or not isinstance(permutations, int) or permutations < 19:
        raise PathError("permutations: an integer >= 19")
    if not finite_real(alpha) or not 0 < alpha < 1:
        raise PathError("alpha in (0, 1)")
    rs = runs_of(labels)
    cnt: dict = {}
    for _, _, c in rs:
        cnt[c] = cnt.get(c, 0) + 1
    sampler = _ConstrainedArrangements(cnt)
    order = sort_order(r)
    obs = cell_stats(r, labels, order)
    ge = {c: 0 for c in obs}
    for _ in range(permutations):
        st = cell_stats(r, constrained_permuted(labels, rng, sampler), order)
        for c in obs:
            ge[c] += st.get(c, 0.0) >= obs[c]
    pv = {c: (1 + ge[c]) / (1 + permutations) for c in obs}
    rej = holm_reject(pv, alpha)
    return {"stats": {c: round(v, 9) for c, v in obs.items()}, "p": {c: round(p, 9) for c, p in pv.items()},
            "arrangements": sampler.total(),
            "proposals": [{"cell": c, "D": round(obs[c], 9), "p": round(pv[c], 9)} for c in sorted(rej)]}


def scan_v4(r, labels, *, permutations: int, alpha: float, rng: random.Random) -> dict:
    """v4 (FD-01-D41, founder OD-S9-05) — SUPERSEDED by v4.1: its reference permutes the cells of the
    maximal runs freely, so adjacent runs can receive the same cell and merge; the reference sequences do
    not have the observed run structure (review R1-01 of v4; measured: all draws merged runs).
    Exchangeability hypothesis as stated (H0): given the run boundaries, the
    assignment of cells to runs is exchangeable and independent of the returns. Reference distribution:
    uniform random permutations of the cells across runs (the series and the run boundaries untouched),
    which includes the observed assignment's distribution under H0; Monte Carlo p-value
    (1 + #{D_c(perm) >= D_c(obs)}) / (M + 1), per cell, valid under H0 whatever the dependence of the
    returns. Holm across the cells of one scan."""
    if not isinstance(r, (list, tuple)) or len(r) < 20 or any(not finite_real(v) for v in r):
        raise PathError("r: at least 20 finite numbers")
    if not isinstance(labels, (list, tuple)) or len(labels) != len(r) or len(set(labels)) < 2:
        raise PathError("labels: one per observation, at least two cells")
    if isinstance(permutations, bool) or not isinstance(permutations, int) or permutations < 19:
        raise PathError("permutations: an integer >= 19")
    if not finite_real(alpha) or not 0 < alpha < 1:
        raise PathError("alpha in (0, 1)")
    order = sort_order(r)
    obs = cell_stats(r, labels, order)
    ge = {c: 0 for c in obs}
    for _ in range(permutations):
        st = cell_stats(r, run_permuted(labels, rng), order)
        for c in obs:
            ge[c] += st.get(c, 0.0) >= obs[c]
    pv = {c: (1 + ge[c]) / (1 + permutations) for c in obs}
    rej = holm_reject(pv, alpha)
    return {"stats": {c: round(v, 9) for c, v in obs.items()}, "p": {c: round(p, 9) for c, p in pv.items()},
            "proposals": [{"cell": c, "D": round(obs[c], 9), "p": round(pv[c], 9)} for c in sorted(rej)]}


P1V4 = {"n": 1600, "mean_segment": 50, "permutations": 199, "alpha": 0.05, "reps": 50, "seed": 9401,
        "worlds": ["real", "spurious", "null", "spurious_level", "null_heavy"],
        "criteria": {"real": {"metric": "rate", "op": ">=", "value": 0.80},
                     "spurious": {"metric": "rate", "op": "<=", "value": 0.15},
                     "null": {"metric": "rate", "op": "<=", "value": 0.15},
                     "spurious_level": {"metric": "rate", "op": "<=", "value": 0.15},
                     "null_heavy": {"metric": "rate", "op": "<=", "value": 0.15}},
        "generalisation": [{"mean_segment": 20}, {"mean_segment": 120}]}


def world_series_v4(kind, spec, rnd):
    n = spec["n"]
    labels = segment_labels(n, spec["mean_segment"], P1["cells"], rnd)
    if kind == "real":
        r = [rnd.gauss(0, 1) * (P1["real_scale"] if lab == "A" else 1.0) for lab in labels]
    elif kind == "spurious":                   # stochastic volatility, independent of labels (as v1–v3)
        h, r = 0.0, []
        for _ in range(n):
            h = P1["sv_phi"] * h + P1["sv_sigma"] * rnd.gauss(0, 1)
            r.append(math.exp(h) * rnd.gauss(0, 1))
    elif kind == "spurious_level":             # mean regime shifts (runs of mean length 80), independent of labels
        r, mu = [], 0.0
        for _ in range(n):
            if rnd.random() < 1 / 80:
                mu = rnd.choice((-0.6, 0.0, 0.6))
            r.append(mu + rnd.gauss(0, 1))
    elif kind == "null":
        r = [rnd.gauss(0, 1) for _ in range(n)]
    elif kind == "null_heavy":                 # iid Student-t(3), scaled
        r = [rnd.gauss(0, 1) / math.sqrt(sum(rnd.gauss(0, 1) ** 2 for _ in range(3)) / 3) for _ in range(n)]
    else:
        raise PathError(kind)
    return r, labels


def run_p1_world_v4(world: dict) -> dict:
    """Control code v4: real → rate of 'A proposed'; all other worlds → rate of 'any cell proposed'."""
    spec = {**P1V4, **world.get("overrides", {})}
    rnd = random.Random(world["seed"])
    hits = unscannable = 0
    for _ in range(world["reps"]):
        r, labels = world_series_v4(world["kind"], spec, rnd)
        if len(set(labels)) < 2:
            unscannable += 1
            continue
        fn = scan_v41 if world.get("version") == "v4.1" else scan_v4
        res = fn(r, labels, permutations=spec["permutations"], alpha=spec["alpha"], rng=rnd)
        cells = {q["cell"] for q in res["proposals"]}
        hits += ("A" in cells) if world["kind"] == "real" else bool(cells)
    return {"rate": round(hits / world["reps"], 9), "hits": hits, "reps": world["reps"], "unscannable": unscannable}


def p1_world_spec_v4(kind, *, overrides=None, seed_offset=0, version="v4"):
    w = {"tool": "path:P1-distributional", "version": version, "kind": kind, "reps": P1V4["reps"],
         "seed": P1V4["seed"] + P1V4["worlds"].index(kind) + seed_offset + (1000 if version == "v4.1" else 0)}
    if overrides:
        w["overrides"] = overrides
    return w


def scan(r, labels, *, rotations: int, alpha: float, rng: random.Random, null: str = "rotation") -> dict:
    """Path-1 scan. Returns {"stats", "null_max_quantile", "proposals": [{"cell", "D", "p_max"}]}.
    null = "rotation" (v1, FD-01-D35) or "run_permutation" (v2, FD-01-D36); `rotations` = M either way."""
    if not isinstance(r, (list, tuple)) or len(r) < 20 or any(not finite_real(v) for v in r):
        raise PathError("r: at least 20 finite numbers")
    if not isinstance(labels, (list, tuple)) or len(labels) != len(r) or len(set(labels)) < 2:
        raise PathError("labels: one per observation, at least two cells")
    if isinstance(rotations, bool) or not isinstance(rotations, int) or rotations < 19:
        raise PathError("rotations: an integer >= 19")
    if not finite_real(alpha) or not 0 < alpha < 1:
        raise PathError("alpha in (0, 1)")
    if null not in ("rotation", "run_permutation"):
        raise PathError("null: rotation | run_permutation")
    n = len(r)
    obs = cell_stats(r, labels)
    lo = max(1, n // 10)
    null_max = []
    for _ in range(rotations):
        if null == "rotation":
            k = rng.randrange(lo, n - lo + 1)
            rot = list(labels[k:]) + list(labels[:k])
        else:
            rot = run_permuted(labels, rng)
        null_max.append(max(cell_stats(r, rot).values()))
    props = []
    for c, d in sorted(obs.items()):
        p = (1 + sum(1 for t in null_max if t >= d)) / (1 + rotations)
        if p <= alpha:
            props.append({"cell": c, "D": round(d, 9), "p_max": round(p, 9)})
    null_sorted = sorted(null_max)
    q = null_sorted[min(rotations - 1, int(math.ceil((1 - alpha) * (rotations + 1))) - 1)]
    return {"stats": {c: round(v, 9) for c, v in obs.items()}, "null_max_quantile": round(q, 9), "proposals": props}


# ======================= control worlds (TP-21/tool) =============================================
P1 = {"n": 400, "rotations": 49, "alpha": 0.05, "reps": 50, "mean_segment": 50, "cells": ["A", "B", "C"],
      "real_scale": 1.8, "sv_phi": 0.98, "sv_sigma": 0.25, "seed": 9101,
      "criteria": {"real": {"metric": "rate", "op": ">=", "value": 0.80},
                   "spurious": {"metric": "rate", "op": "<=", "value": 0.15},
                   "null": {"metric": "rate", "op": "<=", "value": 0.15}}}


def segment_labels(n, mean_len, cells, rnd):
    out = []
    while len(out) < n:
        ln = 1 + int(rnd.expovariate(1 / (mean_len - 1)))
        out.extend([rnd.choice(cells)] * ln)
    return out[:n]


def world_series(kind, spec, rnd):
    n = spec["n"]
    labels = segment_labels(n, spec["mean_segment"], spec["cells"], rnd)
    if kind == "real":                       # cell A: returns scaled by real_scale (a true distributional regularity)
        r = [rnd.gauss(0, 1) * (spec["real_scale"] if lab == "A" else 1.0) for lab in labels]
    elif kind == "spurious":                 # volatility clustering independent of labels (no cell regularity)
        h, r = 0.0, []
        for _ in range(n):
            h = spec["sv_phi"] * h + spec["sv_sigma"] * rnd.gauss(0, 1)
            r.append(math.exp(h) * rnd.gauss(0, 1))
    elif kind == "null":
        r = [rnd.gauss(0, 1) for _ in range(n)]
    else:
        raise PathError(kind)
    return r, labels


def run_p1_world(world: dict) -> dict:
    """Control code. real: rate = share of series where cell A is proposed; spurious / null: rate =
    share of series where ANY cell is proposed."""
    spec = {**P1, **world.get("overrides", {})}
    rnd = random.Random(world["seed"])
    hits = unscannable = 0
    for _ in range(world["reps"]):
        r, labels = world_series(world["kind"], spec, rnd)
        if len(set(labels)) < 2:            # one run covers the whole series: nothing to compare (FL-010)
            unscannable += 1
            continue
        if world.get("null") == "rotation_per_cell":            # v3 (FD-01-D37)
            res = scan_per_cell(r, labels, rotations=spec["rotations"], alpha=spec["alpha"], rng=rnd)
        else:
            res = scan(r, labels, rotations=spec["rotations"], alpha=spec["alpha"], rng=rnd,
                       null=world.get("null", "rotation"))
        cells = {p["cell"] for p in res["proposals"]}
        hits += ("A" in cells) if world["kind"] == "real" else bool(cells)
    # an unscannable series counts as "not proposed" in the rate (conservative for "real", neutral for
    # "spurious"/"null"); its number is reported
    return {"rate": round(hits / world["reps"], 9), "hits": hits, "reps": world["reps"], "unscannable": unscannable}


def p1_world_spec(kind, *, overrides=None, seed_offset=0, null="rotation"):
    w = {"tool": "path:P1-distributional", "kind": kind, "reps": P1["reps"],
         "seed": P1["seed"] + {"real": 0, "spurious": 1, "null": 2}[kind] + seed_offset}
    if null != "rotation":
        w["null"] = null                     # v2 (FD-01-D36), v3 (FD-01-D37); v1 worlds keep their hash
    if null == "rotation_per_cell":
        w["overrides"] = {**(overrides or {}), "rotations": 199}
        return w
    if overrides:
        w["overrides"] = overrides
    return w


# Generalisation worlds (measure and declare, no threshold; part of the path card's generalisation
# test): other n and other segment lengths than the control worlds.
GENERALISATION = [{"n": 800, "mean_segment": 50}, {"n": 400, "mean_segment": 20}, {"n": 400, "mean_segment": 120}]
