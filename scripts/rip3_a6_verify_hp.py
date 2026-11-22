"""RIP-3 BUILD check B2, attempt 3 (founder directive of 2026-11-19): the algebra sub-check in HIGH PRECISION.
Pre-registered in docs/research/RIP3_BUILD_NOTES.md §B2 (attempt 3) before this is run. SYNTHETIC ONLY.
Usage: python scripts/rip3_a6_verify_hp.py OUT_JSON

Unchanged from attempts 1–2: the same 768 comparisons (families seed 6102 role 'a6check', classes, g, candidates),
the quadrature comparison (production vs dense trapezoid on the coefficient form, limit 1e-4), the 101 points of the
algebra check, its limit 1e-6.
Changed (directive): both sides of the algebra check are computed in high precision from the inputs converted
BEFORE any arithmetic:
  - all 768 comparisons in numpy longdouble, after verifying its precision on this machine (eps ≤ 1.1e-19 and log/exp
    agreeing with 60-digit Decimal to ≤ 1e-17 relative at test values); the script stops if this is not so;
  - the 2 comparisons that failed in attempt 2 and the 10 with the largest longdouble differences recomputed in
    Python Decimal with 60 significant digits (ln, exp, π by Machin's formula).
Reported: the largest absolute difference, where it occurs, and the precision used; also, for information, the
difference between the production double-precision coefficient form and the high-precision direct form."""
import json
import math
import sys
from decimal import Decimal, getcontext
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import rip3_a6_verify as V                                              # noqa: E402  (attempts 1–2 code, unchanged)
from xauusd_swarm import rip2                                           # noqa: E402
from xauusd_swarm import rip3                                           # noqa: E402

LD = np.longdouble
getcontext().prec = 60


def dec_pi():
    """π by Machin's formula: 16·atan(1/5) − 4·atan(1/239), in the current Decimal context."""
    def atan_inv(n):
        x, n2, s, k, sign = Decimal(1) / n, n * n, Decimal(0), 1, 1
        term = x
        while term != 0:
            s += sign * term / k
            x /= n2
            term = x
            k += 2
            sign = -sign
        return s
    return 16 * atan_inv(5) - 4 * atan_inv(239)


PI = dec_pi()
LN2PI = (2 * PI).ln()


def check_longdouble():
    fi = np.finfo(LD)
    vals = [1e-9, 0.37, 1.0, 2.5, 1e4, 1e10]
    worst = 0.0
    for v in vals:
        ln_ld = np.log(LD(v))
        ex_ld = np.exp(LD(math.log(v)) / LD(7))
        ln_d = Decimal(v).ln()                     # exact binary value of the double v, then 60-digit ln
        ex_d = (Decimal(float(LD(math.log(v)))) / 7).exp()
        ld_str = lambda q: np.format_float_positional(q, unique=True)            # noqa: E731
        worst = max(worst, abs(Decimal(ld_str(ln_ld)) - ln_d) / max(abs(ln_d), Decimal("1e-30")),
                    abs(Decimal(ld_str(ex_ld)) - ex_d) / ex_d)
    ok = float(fi.eps) <= 1.1e-19 and float(worst) <= 1e-17
    return {"dtype": str(fi.dtype), "eps": float(fi.eps), "precision_digits": int(fi.precision),
            "log_exp_max_rel_vs_decimal60": float(worst), "ok": ok}


def direct_ld(xs, mu, s, v):
    v = np.asarray(v, dtype=LD)
    u = np.exp(v)
    tot = np.zeros(len(v), dtype=LD)
    half_ln2pi = LD(str(LN2PI / 2))
    for x in xs:
        xl = np.asarray(x, dtype=np.float64).astype(LD)
        sl = np.asarray(s[:len(x)], dtype=np.float64).astype(LD)
        mul = LD(mu)
        lns = np.sum(np.log(sl))
        for i, ui in enumerate(u):
            z = (ui * xl - mul) / sl
            tot[i] += -np.sum(z * z) / 2 - lns - len(x) * half_ln2pi
        tot += len(x) * v
    return tot


def coef_ld(xs, mu, s, v):
    v = np.asarray(v, dtype=LD)
    half_ln2pi = LD(str(LN2PI / 2))
    out = np.zeros(len(v), dtype=LD)
    mul = LD(mu)
    for x in xs:
        xl = np.asarray(x, dtype=np.float64).astype(LD)
        sl = np.asarray(s[:len(x)], dtype=np.float64).astype(LD)
        A = np.sum(xl * xl / (sl * sl))
        B = np.sum(mul * xl / (sl * sl))
        C = np.sum(-mul * mul / (2 * sl * sl) - np.log(sl) - half_ln2pi)
        out += C + len(x) * v - A * np.exp(2 * v) / 2 + B * np.exp(v)
    return out


def direct_dec(xs, mu, s, v):
    out = []
    for vi in v:
        vd = Decimal(float(vi))
        u = vd.exp()
        tot = Decimal(0)
        for x in xs:
            st = s[:len(x)]
            for xt, sv in zip(x, st):
                sd = Decimal(float(sv))
                z = (u * Decimal(float(xt)) - Decimal(mu)) / sd
                tot += -z * z / 2 - sd.ln() - LN2PI / 2
            tot += len(x) * vd
        out.append(tot)
    return out


def coef_dec(xs, mu, s, v):
    m = Decimal(mu)
    terms = []
    for x in xs:
        st = s[:len(x)]
        A = sum((Decimal(float(xt)) ** 2) / (Decimal(float(sv)) ** 2) for xt, sv in zip(x, st))
        B = sum(m * Decimal(float(xt)) / (Decimal(float(sv)) ** 2) for xt, sv in zip(x, st))
        C = sum(-m * m / (2 * Decimal(float(sv)) ** 2) - Decimal(float(sv)).ln() - LN2PI / 2 for sv in st)
        terms.append((A, B, C, len(x)))
    out = []
    for vi in v:
        vd = Decimal(float(vi))
        out.append(sum(C + n * vd - A * (2 * vd).exp() / 2 + B * vd.exp() for A, B, C, n in terms))
    return out


def comparisons():
    for fc in V.SPEC["family_classes"]:
        for g in V.SPEC["g"]:
            fam = rip3.make_family(V.SPEC["base"], V.SPEC["role"], "W1", g, fc, 0)
            obs = [rip3.path("W1", fc, rip3.innovations("W1", fc, rip3.member_stream(fam, m), 512))[1] for m in range(g)]
            for cand in ["M1", "M2w1", "M2w2", "M2w4"]:
                xs = [rip3.transform(cand, o, fc[0], fam) for o in obs]
                for c in rip3.CLASSES:
                    yield fc, g, cand, c, xs


def windows(cand, xs, mu, s):
    """The algebra-check points of attempts 1–2 (101 points over the production window)."""
    T = [rip3._quad_terms(x, mu, s[:len(x)]) for x in xs]
    if cand == "M1":
        return [(i, T[i], np.linspace(*(lambda v0sd: (v0sd[0] - 12 * v0sd[1], v0sd[0] + 12 * v0sd[1]))(
            rip3._mode(T[i][0], T[i][1], T[i][3])), 101)) for i in range(len(xs))], T
    w = int(cand[3:])
    return [(None, None, np.linspace(-w, w, 101))], T


def main(out):
    ld = check_longdouble()
    if not ld["ok"]:
        raise SystemExit(f"longdouble precision not sufficient on this machine: {ld}")
    rows = []
    for fc, g, cand, c, xs in comparisons():
        k = rip2.class_params(c)
        mu, s = k["mu"], k["s"][1:]
        wins, T = windows(cand, xs, mu, s)
        alg, info, where = 0.0, 0.0, None
        for i, t, v in wins:
            sub = [xs[i]] if i is not None else xs
            d = direct_ld(sub, mu, s, v)
            cf = coef_ld(sub, mu, s, v)
            diff = np.abs(d - cf)
            j = int(np.argmax(diff))
            if float(diff[j]) > alg:
                alg, where = float(diff[j]), {"member": i, "v": float(v[j]), "abs_g": float(abs(d[j]))}
            prod = sum(rip3._g(v, *tt) for tt in ([t] if t is not None else T))
            info = max(info, float(np.max(np.abs(np.asarray(prod, dtype=LD) - d))))
        # quadrature part: exactly as attempt 2
        if cand == "M1":
            prod_ll = sum(rip3.ll_scale_invariant(x, mu, s[:len(x)]) for x in xs)
            ref = sum(V.reference([t], *V.SPEC["M1_range"], *rip3._mode(t[0], t[1], t[3])) for t in T)
        else:
            w = int(cand[3:])
            Aq, Bq, C, n = (sum(t[i] for t in T) for i in range(4))
            prod_ll = rip3.ll_secret_scale(xs, mu, s, w)
            ref = V.reference(T, -w, w, *rip3._mode(Aq, Bq, n)) - math.log(2 * w)
        rows.append({"family_class": list(fc), "g": g, "candidate": cand, "class": list(c),
                     "quadrature_abs_diff": abs(prod_ll - ref), "algebra_abs_diff_longdouble": alg, "algebra_where": where,
                     "info_production_double_vs_hp_direct": info,
                     "pass": abs(prod_ll - ref) <= V.SPEC["tol"] and alg <= V.SPEC["algebra_tol"]})
    # Decimal (60 digits) recomputation: the two attempt-2 failures and the 10 largest longdouble differences
    a2 = json.loads((Path(__file__).resolve().parents[1] / "docs/results/rip3_build/B2_a6_verification.json").read_text())
    keys = {(tuple(r["family_class"]), r["g"], r["candidate"], tuple(r["class"])) for r in a2["rows"]
            if r["algebra_max_abs_diff"] > V.SPEC["algebra_tol"]}
    top = sorted(rows, key=lambda r: -r["algebra_abs_diff_longdouble"])[:10]
    keys |= {(tuple(r["family_class"]), r["g"], r["candidate"], tuple(r["class"])) for r in top}
    dec_rows = []
    for fc, g, cand, c, xs in comparisons():
        if (fc, g, cand, c) not in keys:
            continue
        k = rip2.class_params(c)
        mu, s = k["mu"], k["s"][1:]
        wins, _ = windows(cand, xs, mu, s)
        worst = Decimal(0)
        for i, _t, v in wins:
            sub = [xs[i]] if i is not None else xs
            d, cf = direct_dec(sub, mu, s, v), coef_dec(sub, mu, s, v)
            worst = max(worst, max(abs(a - b) for a, b in zip(d, cf)))
        dec_rows.append({"family_class": list(fc), "g": g, "candidate": cand, "class": list(c),
                         "algebra_abs_diff_decimal60": float(worst), "pass": float(worst) <= V.SPEC["algebra_tol"]})
    worst_row = max(rows, key=lambda r: r["algebra_abs_diff_longdouble"])
    res = {"attempt": 3, "directive": "founder 2026-11-19: high precision for both sides; limits 1e-6 and 1e-4 unchanged",
           "precision": {"all_768": ld, "subset": {"type": "decimal", "significant_digits": getcontext().prec}},
           "comparisons": len(rows), "all_pass": all(r["pass"] for r in rows) and all(r["pass"] for r in dec_rows),
           "max_quadrature_abs_diff": max(r["quadrature_abs_diff"] for r in rows),
           "max_algebra_abs_diff_longdouble": worst_row["algebra_abs_diff_longdouble"],
           "max_algebra_where": {k: worst_row[k] for k in ("family_class", "g", "candidate", "class", "algebra_where")},
           "max_algebra_abs_diff_decimal60": max(r["algebra_abs_diff_decimal60"] for r in dec_rows),
           "max_info_production_double_vs_hp_direct": max(r["info_production_double_vs_hp_direct"] for r in rows),
           "rows": rows, "decimal_rows": dec_rows}
    Path(out).write_text(json.dumps(res, indent=1))
    print("comparisons", len(rows), "all_pass", res["all_pass"], "max quad", res["max_quadrature_abs_diff"],
          "max alg ld", res["max_algebra_abs_diff_longdouble"], "max alg dec60", res["max_algebra_abs_diff_decimal60"])


if __name__ == "__main__":
    main(sys.argv[1])
