"""Blinded representations (layer 3, candidate §3.1.1, س 199–213). Pure functions on SYNTHETIC
arrays; no market data. Each representation has a card (س 211): transform, preserves, loses,
and its own re-identification test result. The result is "not run" until the announced threshold
(CS-01-04) is decided. No threshold is invented here (س 219; Register §13 #29)."""
from __future__ import annotations

import math
from .numeric import finite_real
from dataclasses import dataclass


class ReprError(Exception):
    pass


REID_NOT_RUN = "not_run: announced threshold (CS-01-04) is open"


@dataclass(frozen=True)
class Card:
    name: str
    transform: str
    preserves: str
    loses: str
    reid_result: str = REID_NOT_RUN


CARDS = {  # text from س 205–209
    "log_returns": Card("log_returns", "r_t = ln(P_t/P_{t-1}) (optionally / scale estimated from Discovery)",
                        "relative dynamics; comparability over time", "level; price grid; tick step"),
    "tick_grid": Card("tick_grid", "P'_t = (P_t - c)/Δ, c secret offset, Δ tick step",
                      "discreteness; tick step; distances in ticks", "nominal level"),
    "level_residual": Card("level_residual", "P_t mod m, m chosen in advance",
                           "round-number structure; digit clustering", "level; long-run direction"),
    "affine_level": Card("affine_level", "P'_t = a·P_t + b, a > 0 and b secret",
                         "linear level structure; relative distances between levels", "nominal level; unit"),
    "activity_time": Card("activity_time", "time re-indexed by update count or cumulative volatility",
                          "structure in the internal clock", "wall-clock time"),
    "volatility_time": Card("volatility_time", "τ_t = Σ_{s≤t} r_s² (cumulative squared log returns; the "
                            "cumulative-volatility clock of س 209)",
                            "ordering of events in volatility time; relative activity bursts",
                            "wall-clock time; calendar position; level; sign of returns"),
}


def _check(prices):
    if not isinstance(prices, (list, tuple)) or len(prices) < 2 or any(not finite_real(p) or p <= 0 for p in prices):
        raise ReprError("prices must be a sequence of at least 2 finite positive numbers")


def _param(name, v, *, positive=False):
    """Numeric parameter: finite real, not bool, not a huge int (R3-01); optionally > 0."""
    if not finite_real(v) or (positive and not v > 0):
        raise ReprError(f"{name} must be a finite real number{' > 0' if positive else ''} (bool / NaN / inf refused)")
    return v


def _out(values):
    """Outputs are finite: an overflow (e.g. a huge a or a tiny Δ) is a refusal, not an inf (S3-01)."""
    if any(not math.isfinite(v) for v in values):
        raise ReprError("transform produced a non-finite value; parameters out of range")
    return values


def log_returns(prices, scale: float | None = None):
    _check(prices)
    r = [math.log(prices[i] / prices[i - 1]) for i in range(1, len(prices))]
    if scale is not None:
        _param("scale (estimated from Discovery, س 205)", scale, positive=True)   # S1-02, R2-01
        r = [x / scale for x in r]
    return _out(r)


def tick_grid(prices, c: float, delta: float):
    _check(prices)
    _param("c", c)
    _param("Δ (tick step)", delta, positive=True)
    return _out([(p - c) / delta for p in prices])


def level_residual(prices, m: float):
    _check(prices)
    _param("m", m, positive=True)
    return _out([math.fmod(p, m) for p in prices])


def affine_level(prices, a: float, b: float):
    _check(prices)
    _param("a (a > 0 is required, س 208)", a, positive=True)
    _param("b", b)
    return _out([a * p + b for p in prices])


def activity_time(n_updates: int):
    if isinstance(n_updates, bool) or not isinstance(n_updates, int) or n_updates < 0:
        raise ReprError("n_updates must be a non-negative integer")
    return list(range(n_updates))


def volatility_time(prices):
    """Cumulative squared log-return clock ("cumulative volatility", س 209)."""
    r = log_returns(prices)
    out, acc = [0.0], 0.0
    for x in r:
        acc += x * x
        out.append(acc)
    return out
