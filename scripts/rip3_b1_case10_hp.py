"""RIP-3 BUILD check B1-HP (review item 4, MINOR): floating-point assurance of the bounded block method on the
extreme case (B1 case 10: asset 0, P = 1800, s = 0.05, the only B1 case computed by blocks). SYNTHETIC ONLY.
Pre-registered by its commit, before execution. Usage: python scripts/rip3_b1_case10_hp.py OUT_JSON

Precision: Python decimal at 50 significant digits (mpmath is not installed here; the first committed version
imported mpmath and stopped at that import, before any computation — no result existed). The t5 quantities are the
exact closed forms in θ = atan(y/√5) for ν = 5: S(y) = 8/(3π)·[3φ/8 − sin2θ/4 − sin4θ/32], E[Y;Y>y] = (5+y²)/4·f5(y),
E[Y²;Y>y] = 40/(3π)·[φ/8 + sin4θ/32], φ = π/2 − θ = atan(√5/y) (y > 0), sin2θ = 2t/(1+t²), sin4θ = 4t(1−t²)/(1+t²)²,
t = y/√5 (the same quantities as the incomplete-beta forms of the float code).
What is recomputed, independently of the float code's arithmetic, at 50 significant digits:
every term of the same decomposition that rip3.uvol_truth_w2 uses at K = 400 — the exact levels (both ends), every
block integral A²M0 + 2AbM1 + b²M2 (M_k from mpmath.betainc and the closed-form t5 density), and the tail terms
A²T0 + b²T2. The block partition (which levels are exact, where blocks start and end) is taken from the float
code; any partition is valid for the proven cell-to-integral bound, so the partition is not an error source.
The analytic block bound E_b and the frozen E_u terms are recomputed in mpmath as well.

Criterion (fixed before execution; the frozen acceptance 1e-6·q is NOT changed):
  |q_float − q_hp| + E_u,hp ≤ 1e-6 · q_hp,
where E_u,hp includes the block bound. Reported: |q_float − q_hp|, its share of the remaining budget, E_u,hp / q_hp."""
import json
import math
import sys
import time
from decimal import Decimal as D, getcontext
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from xauusd_swarm import reid                                            # noqa: E402
from xauusd_swarm import rip3 as R                                       # noqa: E402

getcontext().prec = 50
DPS = 50
INF = D("Infinity")
CASE = {"name": "stress_a0_extreme_s_0.05", "asset": 0, "P": 1800.0, "s": 0.05, "K": 400.0}


def pi():
    """Python decimal documentation recipe."""
    getcontext().prec += 4
    three = D(3)
    lasts, t, s, n, na, d, da = 0, three, 3, 1, 0, 0, 24
    while s != lasts:
        lasts = s
        n, na = n + na, na + 8
        d, da = d + da, da + 32
        t = (t * n) / d
        s += t
    getcontext().prec -= 4
    return +s


PI = pi()
SQ5 = D(5).sqrt()


def atan(x):
    """arctan by argument halving (atan x = 2 atan(x/(1+sqrt(1+x²)))) then the Taylor series."""
    if x < 0:
        return -atan(-x)
    getcontext().prec += 10
    k = 0
    while x > D("0.05"):
        x = x / (1 + (1 + x * x).sqrt())
        k += 1
    term, s, n, x2 = x, x, 1, x * x
    while True:
        term = -term * x2
        n += 2
        add = term / n
        if abs(add) < D(10) ** -(DPS + 8):
            break
        s += add
    getcontext().prec -= 10
    return +(s * (2 ** k))


def f5(y):
    return D(8) / (3 * PI * SQ5) * (1 + y * y / 5) ** -3


def upper(y):
    """(S(y), E[Y;Y>y], E[Y²;Y>y]) for y >= 0, exact closed forms for nu = 5."""
    t = y / SQ5
    phi = atan(SQ5 / y) if y > 0 else PI / 2
    s2 = 2 * t / (1 + t * t)
    s4 = 4 * t * (1 - t * t) / (1 + t * t) ** 2
    S = D(8) / (3 * PI) * (3 * phi / 8 - s2 / 4 - s4 / 32)
    return S, (5 + y * y) / 4 * f5(y), D(40) / (3 * PI) * (phi / 8 + s4 / 32)


def F5(y):
    return 1 - upper(y)[0] if y >= 0 else upper(-y)[0]


def moments(y1, y2):
    if y1 >= 0:
        a, b = upper(y1), upper(y2)
        return a[0] - b[0], a[1] - b[1], a[2] - b[2]
    if y2 <= 0:
        a, b = upper(-y2), upper(-y1)
        return a[0] - b[0], -(a[1] - b[1]), a[2] - b[2]
    l, r = moments(y1, D(0)), moments(D(0), y2)
    return l[0] + r[0], l[1] + r[1], l[2] + r[2]


def main(out):
    t0 = time.time()
    A0 = reid.ASSETS[CASE["asset"]]
    tick_f, mu_f, P_f = A0["tick"], A0["drift"], CASE["P"]
    c_f = math.sqrt(0.6)
    b_f = c_f * CASE["s"]
    K_f = CASE["K"]
    q_float, E_float, K_used, ok = R.uvol_truth_w2(P_f, mu_f, b_f, tick_f)
    assert K_used == K_f
    # partition from the float code (same formulas as rip3._central_blocked)
    p0_f = round(round(P_f / tick_f) * tick_f, 10)
    yfl = lambda price: (math.log(price / P_f) - mu_f) / b_f                                   # noqa: E731
    jlo = max(1, math.floor(P_f * math.exp(mu_f - K_f * b_f) / tick_f - 0.5))
    jhi = math.ceil(P_f * math.exp(mu_f + K_f * b_f) / tick_f + 0.5)
    fl = max(jlo, math.ceil(P_f * math.exp(mu_f - K_f * b_f) / tick_f + 0.5), R.BLOCK_EXACT_J + 1)
    while fl <= jhi and yfl((fl - 0.5) * tick_f) < -K_f:
        fl += 1
    fh = math.floor(P_f * math.exp(mu_f + K_f * b_f) / tick_f - 0.5)
    while fh >= fl and yfl((fh + 0.5) * tick_f) > K_f:
        fh -= 1
    blocks, j1, grow = [], fl, math.exp(b_f * R.BLOCK_DY)
    while j1 <= fh:
        j2 = min(fh, max(j1, math.floor(j1 * grow)))
        blocks.append((j1, j2))
        j1 = j2 + 1
    # high precision
    P, mu, b, tick, K = D(P_f), D(mu_f), D(b_f), D(tick_f), D(K_f)
    p0 = D(p0_f)
    A = mu + (P / p0).ln()
    y = lambda price: ((price / P).ln() - mu) / b                                             # noqa: E731
    clip = lambda v: max(-K, min(K, v))                                                        # noqa: E731

    def exact(ja, jb):
        s = D(0)
        for j in range(ja, jb + 1):
            lo = (j - D(1) / 2) * tick
            hi = (j + D(1) / 2) * tick
            pj = F5(clip(y(hi))) - F5(clip(y(lo)))
            s += pj * ((D(round(j * tick_f, 10)) / p0).ln()) ** 2
        return s
    central = exact(jlo, fl - 1) + exact(fh + 1, jhi)
    c1 = D(6) / (2 * SQ5)
    Eb = D(0)
    for (a, bb) in blocks:
        p_lo, p_hi = (a - D(1) / 2) * tick, (bb + D(1) / 2) * tick
        y1, y2 = y(p_lo), y(p_hi)
        M0, M1, M2 = moments(y1, y2)
        central += A * A * M0 + 2 * A * b * M1 + b * b * M2
        ymin = D(0) if y1 <= 0 <= y2 else min(abs(y1), abs(y2))
        Lmax = max(abs((p_lo / p0).ln()), abs((p_hi / p0).ln()))
        W = p_hi - p_lo
        Eb += (tick * tick * W * f5(ymin) / (12 * b * p_lo ** 3)) * (2 * Lmax * (c1 / b + 1) + 1 + Lmax)
        Eb += (2 * Lmax / p_lo) * (D("5e-11") + p_hi * D("2.3e-16")) * M0
    uK = upper(K)
    T0, T1, T2 = 2 * uK[0], 2 * uK[1], 2 * uK[2]
    q_hp = central + A * A * T0 + b * b * T2
    floor = 100 * tick
    delta_f = -(1 - D(1) / 199).ln()
    Lg = (p0 / tick).ln()
    yf = min(-K, ((floor / P).ln() - mu) / b)
    Ff = upper(-yf)[0]
    U2 = upper(-yf)[2]
    E_hp = delta_f * (2 * (abs(A) * T0 + b * T1) + delta_f * T0) + Ff * (Lg * Lg + 2 * A * A) + 2 * b * b * U2 + Eb
    diff = abs(D(q_float) - q_hp)
    budget = D("1e-6") * q_hp
    res = {"case": CASE, "decimal_digits": DPS, "K": K_f, "exact_levels": (fl - jlo) + (jhi - fh), "blocks": len(blocks),
           "q_float": q_float, "q_hp": float(q_hp), "abs_diff_float_vs_hp": float(diff),
           "rel_diff": float(diff / q_hp), "E_float": E_float, "E_hp": float(E_hp), "E_hp_over_q": float(E_hp / q_hp),
           "block_bound_hp": float(Eb), "diff_share_of_remaining_budget": float(diff / (budget - E_hp)),
           "criterion": "|q_float − q_hp| + E_hp ≤ 1e-6·q_hp", "pass": bool(diff + E_hp <= budget),
           "seconds": round(time.time() - t0, 1)}
    Path(out).write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main(sys.argv[1])
