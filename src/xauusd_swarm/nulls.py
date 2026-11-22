"""Stage 9, gap G3 — generators for the §11.2 model cards (candidate §11.2, س 825–833; مك-156 … مك-161).

Pure Python (no numeric library in the pinned environment, OD-09), deterministic by seed.

| card (CARDS key)        | generator                     | null hypothesis                          | target quantity          |
|-------------------------|-------------------------------|------------------------------------------|--------------------------|
| full_shuffle            | full_shuffle(x, rng)          | full exchangeability                     | any temporal dependence  |
| iaaft                   | iaaft(x, rng, iterations)     | monotone transform of a stationary linear Gaussian process | nonlinear structure |
| pair_shuffle_vol_blocks | pair_shuffle_blocks(s, a, blocks, rng) | within a volatility state, pair order exchangeable | state prediction by sign, asymmetry kept |
| block_bootstrap         | block_bootstrap(x, b, rng)    | — NOT A NULL                             | uncertainty only         |
| zero_cond_mean          | zero_cond_mean(simulate, …)   | zero conditional mean, modelled structure kept | conditional mean only |
| time_reversal           | time_reversal(x)              | time reversibility                       | temporal asymmetry       |

Conditions carried from the cards (not relaxed):
- IAAFT assumes stationarity; it is applied within stable windows or after a transform (س 829). Its
  validity under non-stationarity is TP-82 (WP7-04 §11.1), a separate experiment — not claimed here.
- Block bootstrap is NOT a null (س 831): `null_generator("block_bootstrap")` is refused; block length b
  is open in the architecture and must be given explicitly; weak dependence is assumed (TP-81 tests it).
- Pair shuffle: the volatility blocks are frozen from Discovery (س 830) — they are an INPUT here.
- Zero-conditional-mean generative: the model is "estimated from Discovery"; its family is
  «غير معرّف في المعمارية», so this module does not choose one. It wraps a REGISTERED simulator
  (`simulate(n, rng) -> (r, cond_mean)`) and refuses output whose stated conditional mean is not zero;
  validity is limited to what the simulator models (س 832).
- Zero returns have no sign and are excluded from sign-based statistics by a registered rule, with the
  count documented (س 863): `signs()` returns the signs and the excluded count.
"""
from __future__ import annotations

import cmath
import math
from .numeric import finite_real
import random

CARDS = {
    "full_shuffle": {"null": "قابلية التبادل الكاملة", "target": "وجود أي اعتماد زمني", "is_null": True},
    "iaaft": {"null": "تحويل ساكن رتيب لعملية خطية غاوسية مستقرة", "target": "البنية غير الخطية",
              "is_null": True, "assumes": "الاستقرار (TP-82)",
              # mandatory by the card itself (س 829; TP-82 review R2-01): enforced by controls.py
              "use_restriction": "stable_windows_or_registered_transform"},
    "pair_shuffle_vol_blocks": {"null": "داخل حالة التقلب ترتيب الأزواج قابل للتبادل",
                                "target": "تنبؤ الحالة بالإشارة مع حفظ عدم التماثل", "is_null": True,
                                "assumes": "كتل مجمّدة من Discovery"},
    "block_bootstrap": {"null": None, "target": "عدم اليقين فقط", "is_null": False,
                        "assumes": "اعتماد ضعيف (TP-81)؛ طول الكتلة مفتوح"},
    "zero_cond_mean": {"null": "انعدام المتوسط الشرطي", "target": "المتوسط الشرطي فقط", "is_null": True,
                       "assumes": "نموذج مقدَّر من Discovery (عائلته غير معرّفة في المعمارية)"},
    "time_reversal": {"null": "قابلية الانعكاس الزمني", "target": "اللاتناظر الزمني", "is_null": True},
}


class NullError(ValueError):
    pass


def _finite(v) -> bool:
    """A finite real number, not a bool (review WP9-02 R1-01, R1-02)."""
    return finite_real(v)                                 # huge ints refused (S1-03)


def _check(x):
    if not isinstance(x, (list, tuple)) or len(x) < 2:
        raise NullError("a series of at least 2 values")
    if any(not _finite(v) for v in x):
        raise NullError("finite numbers only")
    return list(map(float, x))


# ---------------- generators ----------------
def full_shuffle(x, rng: random.Random):
    y = _check(x)
    rng.shuffle(y)
    return y


def time_reversal(x, rng: random.Random | None = None):
    return _check(x)[::-1]


def block_bootstrap(x, b: int, rng: random.Random):
    """Moving-block bootstrap: blocks of length b drawn with replacement. Uncertainty only — not a null."""
    y = _check(x)
    if not isinstance(b, int) or isinstance(b, bool) or not 1 <= b <= len(y):
        raise NullError("block length b: an integer 1..n, given explicitly (open in the architecture)")
    out = []
    while len(out) < len(y):
        s = rng.randrange(0, len(y) - b + 1)
        out.extend(y[s:s + b])
    return out[:len(y)]


def pair_shuffle_blocks(s, a, blocks, rng: random.Random):
    """Permute the pairs (s_t, |r_t|) within each volatility block (labels frozen from Discovery)."""
    if not (len(s) == len(a) == len(blocks)) or not s:
        raise NullError("s, |r| and block labels have the same non-zero length")
    if any(v not in (-1, 1) for v in s):
        raise NullError("signs are ±1 (zero returns are excluded beforehand, س 863)")
    if any(not _finite(v) or v < 0 for v in a):
        raise NullError("magnitudes are finite, non-negative numbers (not bool)")
    idx: dict = {}
    for i, lab in enumerate(blocks):
        idx.setdefault(lab, []).append(i)
    s2, a2 = list(s), list(a)
    for pos in idx.values():
        perm = pos[:]
        rng.shuffle(perm)
        for dst, src in zip(pos, perm):
            s2[dst], a2[dst] = s[src], a[src]
    return s2, a2


def zero_cond_mean(simulate, n: int, rng: random.Random, tol: float = 1e-12):
    """Wrap a REGISTERED generative simulator; refuse it unless every stated E[r_t | past] is zero."""
    if isinstance(n, bool) or not isinstance(n, int) or n < 2:
        raise NullError("n: an integer >= 2")
    if not finite_real(tol) or tol < 0:
        raise NullError("tol: a finite non-negative number")
    r, cm = simulate(n, rng)
    if len(r) != n or len(cm) != n:
        raise NullError("simulator returns n values and n conditional means")
    if any(not _finite(m) for m in cm):
        raise NullError("every stated conditional mean is a finite number (NaN / inf / bool refused)")
    if any(abs(m) > tol for m in cm):
        raise NullError("generative null requires E[r_t | past] = 0 at every t (س 832)")
    return _check(r)


# ---------------- IAAFT (pure Python FFT) ----------------
def _fft(a, inverse=False):
    n = len(a)
    if n == 1:
        return [a[0]]
    if n & (n - 1):
        return _dft(a, inverse)
    even, odd = _fft(a[0::2], inverse), _fft(a[1::2], inverse)
    sgn = 1 if inverse else -1
    out = [0j] * n
    for k in range(n // 2):
        t = cmath.exp(sgn * 2j * math.pi * k / n) * odd[k]
        out[k], out[k + n // 2] = even[k] + t, even[k] - t
    return out


def _dft(a, inverse=False):
    n, sgn = len(a), (1 if inverse else -1)
    return [sum(a[t] * cmath.exp(sgn * 2j * math.pi * k * t / n) for t in range(n)) for k in range(n)]


def _ifft(a):
    n = len(a)
    return [v / n for v in _fft(a, inverse=True)]


def amplitude_spectrum(x):
    return [abs(v) for v in _fft([complex(v) for v in x])]


def iaaft(x, rng: random.Random, iterations: int = 50):
    """Iterative amplitude-adjusted Fourier transform surrogate (Schreiber & Schmitz): alternately impose
    the original amplitude spectrum and the original marginal (exact by rank reordering)."""
    y = _check(x)
    if isinstance(iterations, bool) or not isinstance(iterations, int) or iterations < 1:
        raise NullError("iterations: a positive integer")
    n = len(y)
    sorted_vals = sorted(y)
    target_amp = amplitude_spectrum(y)
    z = y[:]
    rng.shuffle(z)                                        # random start: phases randomised
    for _ in range(iterations):
        Z = _fft([complex(v) for v in z])
        Z = [target_amp[k] * (Z[k] / abs(Z[k]) if abs(Z[k]) > 0 else 1) for k in range(n)]
        w = [v.real for v in _ifft(Z)]
        order = sorted(range(n), key=lambda i: w[i])
        new = [0.0] * n
        for rank, i in enumerate(order):
            new[i] = sorted_vals[rank]
        if new == z:
            break
        z = new
    return z


# ---------------- helpers ----------------
def signs(r):
    """Signs of non-zero returns and the number of zero returns excluded (س 863)."""
    r = _check(r)                                         # NaN would otherwise become sign −1 (S1-01)
    s = [1 if v > 0 else -1 for v in r if v != 0]
    return s, sum(1 for v in r if v == 0)


GENERATORS = {"full_shuffle": full_shuffle, "iaaft": iaaft, "pair_shuffle_vol_blocks": pair_shuffle_blocks,
              "zero_cond_mean": zero_cond_mean, "time_reversal": time_reversal}


def null_generator(card: str):
    """Generator for a NULL card. Block bootstrap is not a null (س 831) and is refused here."""
    if card not in CARDS:
        raise NullError(f"unknown card {card!r}; cards: {sorted(CARDS)}")
    if not CARDS[card]["is_null"]:
        raise NullError("block bootstrap is not a null; it estimates uncertainty only (س 831)")
    return GENERATORS[card]
