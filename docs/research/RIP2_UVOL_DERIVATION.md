# RIP-2 U-vol — mechanism, exact truth, and numerical verification (review R6)

Part of `RIP2_DESIGN.md` v0.7 §8. SYNTHETIC ONLY. RIP-1 world and results unchanged.

## 1. The actual mechanism (frozen code, FD-01-D45)
From `src/xauusd_swarm/reid.py::simulate` (sha256 4b553a3c…), read line by line:
- **Latent price.** P_{−1} = L_a · growth_p. At step t = 0 … n−1, r_t = μ_a + σ_t · Z_t, with
  σ_t = vol_a · volx_p · (1 + act_a · sin(2πt/64)) and Z_t ~ N(0, 1) from `rnd.gauss` (independent across t).
  Then P_t = P_{t−1} · e^{r_t}. The latent price is never rounded: rounding does not feed back into it.
- **Observed price.** P̃_t = round(round(P_t / tick) · tick, 10). This is **deterministic** nearest-tick rounding,
  then a float clean-up to 10 decimals.
- **Rounding errors.** e_t = P̃_t − P_t is a deterministic function of P_t. Consecutive errors e_{t−1} and e_t are
  functions of P_{t−1} and of P_t = P_{t−1}e^{r_t}, so they are **not independent random variables** in general.
  They behave approximately like independent uniform errors only when a step moves many ticks (σP/tick ≫ 1).
  **v0.6 assumed independence and uniformity without deriving it** (term tick²/6), and still called the truth exact;
  for log_returns and volatility_time it added a first-order rounding term on top. That was an inconsistency,
  stated here, not hidden.
- **Representations of the observed series** (`representations.py`):
  - log_returns: r̃_t = ln(P̃_t / P̃_{t−1});
  - volatility_time: x_t = Σ_{i ≤ t} r̃_i², with x_0 = 0, so its increment is x_t − x_{t−1} = r̃_t²;
  - tick_grid: x = (P̃ − c)/Δ;
  - affine_level: x = a·P̃ + b;
  - level_residual: x = fmod(P̃, m).
- **d_u as the researcher sees it.**
  - C0: P̃_u − P̃_{u−1}.
  - tick_grid: (P̃_u − P̃_{u−1})/Δ, computed as the difference of the two transformed values.
  - affine_level: a·(P̃_u − P̃_{u−1}).
  - level_residual: fmod(P̃_u, m) − fmod(P̃_{u−1}, m), the wrapped difference.
  - log_returns: r̃_u.
  - volatility_time: the increment r̃_u², which already is the squared quantity, so s_u = r̃_u².

## 2. Choice: path A (keep the mechanism, derive the exact truth under it)
- **Path B** (change the generator to independent rounding noise) is rejected. It would change the world that
  RIP-1 measured, and RIP-2 diagnoses that world. A different world would break the link between the RIP-2
  diagnosis and the RIP-1 result.
- **Path A** is exact and cheap. Given the latent P_{u−1}, the observed P̃_{u−1} is fixed. P̃_u can take only the
  tick values j·tick, and the probability of each is a difference of normal CDFs. The conditional expectation is
  therefore a **finite sum over j**, with no approximation of the rounding, the logarithm or the drift.

## 3. Exact truth (all representations, one formula)
Let q(P̃_{u−1}, P̃_u) be the per-step quantity the estimator averages:
- q = d_u² for C0, tick_grid, affine_level and log_returns;
- q = s_u = r̃_u² for volatility_time;
- for level_residual, the **unwrapped** d_u = P̃_u − P̃_{u−1}. This is the design choice of v0.5 §8: the truth
  uses the unwrapped scale, so a loss caused by the wrap counts as a loss. The estimator keeps the wrapped observed
  d_u.

Given the latent P = P_{u−1} (custody side), P̃_{u−1} = round(round(P/tick)·tick, 10) is known, and P̃_u = j·tick
(after the same clean-up) with

  p_j = Φ((ln((j + ½)·tick / P) − μ)/σ_u) − Φ((ln((j − ½)·tick / P) − μ)/σ_u),

since round(P·e^{r}/tick) = j exactly when (j − ½)·tick < P·e^{r} < (j + ½)·tick. The boundary event has
probability 0. Then

  **E[q | P_{u−1}] = Σ_j p_j · q(P̃_{u−1}, round(j·tick, 10)).**

**Truth:** v_t = sqrt(mean of E[q | P_{u−1}] over u = t − 31 … t). **Estimate:** ṽ_t = sqrt(mean of q_u over the same
window), from the observed series. Truth and estimate are the same statistical quantity (the windowed mean of the
raw second moment, or of r̃² for volatility_time), in the same units, under the same mechanism, for every
representation.

**Numerical precision (not a model approximation).**
- The sum runs over j with P·e^{μ ± 12σ}/tick inside the range; the mass outside is below 10⁻³².
- Φ is evaluated with the standard erfc.
- The only remaining difference from the mechanism is floating-point arithmetic.

## 4. Formula and unit table
| Data | Observed q_u (estimator) | Truth E[q_u given P_{u−1}] | Units of sqrt |
|---|---|---|---|
| C0 prices | (P̃_u − P̃_{u−1})² | Σ_j p_j (round(j·tick,10) − P̃_{u−1})² | price |
| tick_grid | ((P̃_u − c)/Δ − (P̃_{u−1} − c)/Δ)² | Σ_j p_j ((j·tick − c)/Δ − (P̃_{u−1} − c)/Δ)² | ticks |
| affine_level | (a·P̃_u + b − a·P̃_{u−1} − b)² | Σ_j p_j (a·j·tick − a·P̃_{u−1})² | a × price |
| level_residual | (fmod(P̃_u, m) − fmod(P̃_{u−1}, m))², wrapped | Σ_j p_j (j·tick − P̃_{u−1})², **unwrapped** by design | price |
| log_returns | ln(P̃_u/P̃_{u−1})² | Σ_j p_j ln(j·tick / P̃_{u−1})² | log-return |
| volatility_time | x_u − x_{u−1} = r̃_u² | Σ_j p_j ln(j·tick / P̃_{u−1})² | log-return |

Drift (μ), the exact exponential map, rounding and the log of rounded prices are all inside p_j and q, for every
representation, with no representation-specific approximation. The v0.6 formulas are kept in the verification
only as a comparison.

## 5. Numerical verification — PRE-REGISTERED (fixed before running)
- **Script:** `scripts/rip2_uvol_verify.py`, committed before its run. The Monte Carlo side is independent of the
  formula code: it uses the generator's own step expression (checked against `reid.simulate` by a test) and the
  frozen representation functions on [P̃_{u−1}, P̃_u].
- **Draws:** N = 200,000 per case, seed 7301 + case index, Python `random.gauss` as the generator.
- **Cases** (10 cases × 5 quantity kinds = 50 comparisons):

  | Case | Asset | Latent P | μ | σ | σP/tick | World |
  |---|---|---|---|---|---|---|
  | a0_high_vol_shift | 0 | 2340 | 0.00002 | 0.004608 | 1078 | registered |
  | a0_low_vol | 0 | 1800 | 0.00002 | 0.000288 | 51.8 | registered |
  | a1_zero_drift | 1 | 34.5 | 0 | 0.0014 | 48.3 | registered |
  | a1_high_vol_shift | 1 | 39 | 0 | 0.005824 | 227 | registered |
  | a2_lowest_vol | 2 | 1.1 | −0.00001 | 0.00036 | 39.6 | registered |
  | a2_just_below_half_tick | 2 | (110000.5 − 10⁻⁶)·10⁻⁵ | −0.00001 | 0.00036 | 39.6 | registered |
  | a2_just_above_half_tick | 2 | (110000.5 + 10⁻⁶)·10⁻⁵ | −0.00001 | 0.00036 | 39.6 | registered |
  | a3_mid | 3 | 217.5 | 0.00001 | 0.00132 | 28.7 | registered |
  | stress_a2_sigma_1e-5 | 2 | 1.1 | −0.00001 | 0.00001 | 1.1 | **outside** the world |
  | stress_a2_sigma_3e-6 | 2 | 1.1 | −0.00001 | 0.000003 | 0.33 | **outside** the world |

  The cases cover: zero drift; the lowest and highest σ, including the ×2 shift; a price just below and just above
  a half-tick; and two coarse-discreteness stress cases where the independent-uniform assumption is expected to
  fail. Parameters: c = −L_a for tick_grid; a = e³ and b = −1000 for affine_level (the extremes of the priors).
- **Acceptance criterion (fixed now):** every one of the 50 comparisons satisfies |MC mean − exact| ≤ 4 × MC standard
  error. **All 50 must pass.** The relative errors and the v0.6 formula's deviation are reported, with no criterion.
- A failure is recorded in FL and reported as a negative result. The formula or the criterion is not changed after
  seeing the result.

## 6. Result of the verification (run once after the pre-registration commit f2e7dc7)
- **All 50 comparisons pass** the pre-registered criterion: max |z| = 1.80, against a limit of 4.
  The largest |MC − exact| / exact is 5.74e-03, which is within Monte Carlo noise at N = 200,000.
- **Independence of the comparisons.** The five quantity kinds of one case share the same draws. C0, tick_grid
  and affine_level are exact multiples of each other, and log_returns equals volatility_time. So the evidence is
  10 independent cases, each confirmed for every kind, not 50 independent tests.
- **How far the v0.6 formula was from the exact truth:**
  - At most 8.1e-04 relative inside the registered world. The largest deviation is
    in the half-tick cases of asset 2. v0.6 was therefore numerically close inside this world, but its
    description as exact was wrong.
  - Up to 13.9% in the coarse-discreteness stress cases (σP/tick ≈ 1 and 0.33). There
    the independent-uniform assumption fails, while the exact sum still matches Monte Carlo (|z| ≤ 0.84).
- **Conclusion:** the truth of §3 equals the expectation under the actual mechanism, to Monte Carlo precision,
  for every representation, including at half-ticks, with zero drift, at the lowest and highest σ, and under
  coarse discreteness. Result file: `docs/results/RIP2_uvol_verification.json`.
