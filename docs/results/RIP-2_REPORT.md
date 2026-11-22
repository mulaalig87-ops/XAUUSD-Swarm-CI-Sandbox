# RIP-2 — result report (leakage diagnosis) — SYNTHETIC ONLY

One registered run, founder authorisation OD-S9-09.
- **Design:** v0.7 (FD-01-D46) + addendum A1 (OD-S9-08).
- **Code:** commit `dfb8ea56d214fde5eacb1583e9346b6893ddac77`, rip2.py identical to the reviewed cf60cb8.
- **Run:** `python scripts/rip2_run.py docs/results/rip2`, no spec override, 6024 s, 2026-11-18T21:19:10+00:00 → 2026-11-18T22:59:34+00:00.
- **Results:** `docs/results/rip2/results.json` (sha256 in `results.sha256`; 170 cells, 150 effect rows, 408 ablation
  rows, 75 feature-group rows, 18 utility rows), with the run log and the start metadata (code hashes, seeds, spec,
  environment).
- **Partial reproduction:** 12 cells re-executed from the same code and seeds are identical
  (`docs/results/RIP2_partial_reproduction.json`).

No threshold applies (CS-01-04 stays open). Nothing here opens any gate; RIP-3 is not started. Accuracies are
**asset / period / joint**, with chance 0.25 / 0.25 / 0.0625. Units are families; S-ind means 400 units unless
stated.

## 1. Headline
1. **The attacker that knows the generative model (A6) identifies almost everything except where secrecy acts on
   the level.**
   - Raw prices, log_returns (= activity_time), volatility_time and tick_grid: joint accuracy 0.98–1.00.
   - affine_level with secret (a, b): joint 0.357. This is the only large hiding of the **period**: from 1.00 in C1
     to 0.375 in C2. The asset stays at 0.93.
2. **Secrecy works for affine_level and almost nowhere else.**
   - affine_level: secrecy effect on the period +0.625 [+0.583, +0.667].
   - tick_grid: about 0.
   - level_residual: secrecy **raises** identifiability (period −0.160 [−0.207, −0.113]). The public canonical
     m = 100·tick is small, and loses more of the period than the average secret m does.
3. **The representation itself matters mainly for level_residual.** C0 → C1 removes the period, +0.453
   [+0.417, +0.485], while the asset stays at 1.00. Returns-based representations lose only 0.02 against raw prices.
4. **Δ in the ledger adds little once the attacker knows the model** (A6 in C2: +0.000 to +0.062 on the asset).
   Δ matters more to the feature attackers A1 and A2: for example, A1 asset accuracy on tick_grid in C2 rises from
   0.853 to 0.998.
5. **Which generator component carries identity** (A6 ablation, Δ hidden, inside the model; §3):
   - **Volatility level σ_k** for the returns representations: only-σ gives joint 0.68.
   - The **activity amplitude** carries the asset (≈0.62).
   - The **price level Lg_k** carries the asset in level_residual and tick_grid: only-Lg asset 0.91 and 0.67 under
     AP; 0.78 and 0.61 under PP.
   - **Drift** carries almost nothing.
6. **Research utility** (§5): every representation **except level_residual** keeps volatility tracking, the activity
   cycle and change-point recovery **approximately** as raw prices do (audit RR2-02):
   - tick_grid and affine_level: U-act and U-event are identical to raw prices, and U-vol is equal to within
     5 × 10⁻⁷ (floating-point arithmetic of the transform); affine_level C1 (x = P) is identical in every measure.
   - log_returns and volatility_time differ slightly: U-vol 0.894 vs 0.895, U-act 0.818 vs 0.820, U-event success
     0.6775 vs 0.680.

   level_residual destroys them: U-vol ρ 0.09–0.24 against 0.89, cycle detection 0.11–0.22 against 0.82. So, in
   this world, the representations that keep research structure keep almost all identity, except affine_level's
   period hiding, and the representation that loses period identity (level_residual) also loses the research
   structure.

## 2. A6, S-ind — accuracy by condition (Δ hidden | Δ shown)
| Data | Condition | Δ hidden | Δ shown |
|---|---|---|---|
| C0 raw prices | — | 1.000 / 1.000 / 1.000 | — |
| log_returns | C1 = C2 | 0.983 / 0.978 / 0.978 | 0.993 / 0.988 / 0.988 |
| tick_grid | C1 | 1.000 / 1.000 / 1.000 | 1.000 / 1.000 / 1.000 |
| tick_grid | C2 | 0.998 / 0.998 / 0.998 | 1.000 / 1.000 / 1.000 |
| level_residual | C1 | 1.000 / 0.547 / 0.547 | 1.000 / 0.547 / 0.547 |
| level_residual | C2 | 0.973 / 0.708 / 0.703 | 0.973 / 0.708 / 0.703 |
| affine_level | C1 | 1.000 / 1.000 / 1.000 | 1.000 / 1.000 / 1.000 |
| affine_level | C2 | 0.932 / 0.375 / 0.357 | 0.995 / 0.378 / 0.372 |
| volatility_time | C1 = C2 | 0.983 / 0.978 / 0.978 | 0.993 / 0.988 / 0.988 |

The other attackers are in results.json: A1 / A2 / A3 in S-ind, and A4a / A4b in S-pool. Pooling (g = 4, 16)
raises A6 to 1.000 for every representation except level_residual (period 0.74–0.76) and affine_level (period
0.41–0.54).

## 3. Paired effects for A6, S-ind (stratified paired family bootstrap, B = 2000, 95 %)
| Representation | Target | C0 − C1 | C1 − C2 (Δ hidden) | Δ effect in C2 | secrecy × Δ |
|---|---|---|---|---|---|
| log_returns | asset | +0.018 [+0.007, +0.030] | +0.000 [+0.000, +0.000] | +0.010 [+0.003, +0.020] | +0.000 [+0.000, +0.000] |
| log_returns | period | +0.022 [+0.010, +0.037] | +0.000 [+0.000, +0.000] | +0.010 [+0.003, +0.020] | +0.000 [+0.000, +0.000] |
| tick_grid | asset | +0.000 [+0.000, +0.000] | +0.003 [+0.000, +0.007] | +0.003 [+0.000, +0.007] | -0.003 [-0.007, +0.000] |
| tick_grid | period | +0.000 [+0.000, +0.000] | +0.003 [+0.000, +0.007] | +0.003 [+0.000, +0.007] | -0.003 [-0.007, +0.000] |
| level_residual | asset | +0.000 [+0.000, +0.000] | +0.028 [+0.013, +0.045] | +0.000 [+0.000, +0.000] | +0.000 [+0.000, +0.000] |
| level_residual | period | +0.453 [+0.417, +0.485] | -0.160 [-0.207, -0.113] | +0.000 [+0.000, +0.000] | +0.000 [+0.000, +0.000] |
| affine_level | asset | +0.000 [+0.000, +0.000] | +0.068 [+0.045, +0.092] | +0.062 [+0.040, +0.087] | -0.062 [-0.087, -0.040] |
| affine_level | period | +0.000 [+0.000, +0.000] | +0.625 [+0.583, +0.667] | +0.003 [-0.010, +0.015] | -0.003 [-0.015, +0.010] |
| volatility_time | asset | +0.018 [+0.007, +0.030] | +0.000 [+0.000, +0.000] | +0.010 [+0.003, +0.020] | +0.000 [+0.000, +0.000] |
| volatility_time | period | +0.022 [+0.010, +0.037] | +0.000 [+0.000, +0.000] | +0.010 [+0.003, +0.020] | +0.000 [+0.000, +0.000] |

log_returns and volatility_time have no parameter (C1 = C2 data), so their secrecy effect is 0 by construction.

## 4. A6 component ablation, S-ind, Δ hidden (asset / period; read against the generator-pooled level)
| Representation | Priors | full | generator-pooled | only μ | only σ | only act | only Lg |
|---|---|---|---|---|---|---|---|
| log_returns | AP | 0.98/0.98 | 0.25/0.25 | 0.36/0.25 | 0.69/0.68 | 0.62/0.25 | 0.25/0.25 |
| tick_grid | AP | 1.00/1.00 | 0.51/0.25 | 0.52/0.25 | 0.51/0.21 | 0.51/0.25 | 0.67/0.25 |
| tick_grid | PP | — | 0.25/0.25 | 0.29/0.25 | 0.38/0.25 | 0.31/0.25 | 0.61/0.17 |
| level_residual | AP | 0.97/0.71 | 0.63/0.25 | 0.68/0.25 | 0.57/0.27 | 0.59/0.25 | 0.91/0.33 |
| level_residual | PP | — | 0.25/0.25 | 0.19/0.25 | 0.11/0.24 | 0.07/0.25 | 0.78/0.32 |
| affine_level | AP | 0.93/0.38 | 0.25/0.25 | 0.36/0.25 | 0.50/0.27 | 0.69/0.25 | 0.44/0.25 |
| volatility_time | AP | 0.98/0.98 | 0.25/0.25 | 0.06/0.25 | 0.69/0.68 | 0.61/0.25 | 0.25/0.25 |

- **Pre-stated baselines, confirmed:**
  - The generator-pooled model is at chance for log_returns, volatility_time and affine_level, and under PP for
    tick_grid and level_residual.
  - Under AP it is above chance on the asset for tick_grid (0.51) and level_residual (0.63), through Δ, the c range
    and the m set.
  - The period is at chance in every generator-pooled model.
- **Below-chance cells.** Some restricted models score below chance, for example only-μ for volatility_time
  (asset 0.06) and only-act under PP for level_residual (0.07). A misspecified restricted model sends the units to
  systematically wrong classes. These cells are reported as measured.
- **Within-Δ-group accuracy** with Δ shown (full model, joint, against within-group chance 1/8 or 1/4):
  - returns representations and tick_grid: 0.98–1.00;
  - level_residual: 0.67–0.72;
  - affine_level: 0.24–0.47.
  - tick_grid under group-pooled priors: identical to AP (1.00).

## 5. Research-utility baseline (S-ind, 400 families per world; planted / null)

U-vol intervals: stratified family bootstrap, B = 2000 (§6 of the design). Wilson intervals for the rates are in
results.json (`U_act_wilson95`, `U_event_success_wilson95`, `U_event_flag_wilson95`) (audit RR2-03).

| Data | Condition | U-vol mean ρ [95 % CI], planted | U-vol mean ρ [95 % CI], null | U-act detection (power / false alarm) | U-event success | U-event flag (planted / null) |
|---|---|---|---|---|---|---|
| C0 | C0 | 0.895 [0.891, 0.899] | 0.694 [0.686, 0.702] | 0.820 / 0.018 | 0.6800 | 1.000 / 0.077 |
| log_returns | C1 | 0.894 [0.890, 0.898] | 0.692 [0.684, 0.700] | 0.818 / 0.020 | 0.6775 | 1.000 / 0.072 |
| tick_grid | C1 | 0.895 [0.891, 0.899] | 0.694 [0.686, 0.702] | 0.820 / 0.018 | 0.6800 | 1.000 / 0.077 |
| tick_grid | C2 | 0.895 [0.891, 0.899] | 0.694 [0.686, 0.702] | 0.820 / 0.018 | 0.6800 | 1.000 / 0.077 |
| level_residual | C1 | 0.093 [0.072, 0.115] | 0.091 [0.074, 0.108] | 0.113 / 0.037 | 0.0425 | 0.170 / 0.120 |
| level_residual | C2 | 0.238 [0.207, 0.268] | 0.179 [0.159, 0.201] | 0.217 / 0.065 | 0.0800 | 0.372 / 0.287 |
| affine_level | C1 | 0.895 [0.891, 0.899] | 0.694 [0.686, 0.702] | 0.820 / 0.018 | 0.6800 | 1.000 / 0.077 |
| affine_level | C2 | 0.895 [0.891, 0.899] | 0.694 [0.686, 0.702] | 0.820 / 0.018 | 0.6800 | 1.000 / 0.077 |
| volatility_time | C1 | 0.894 [0.890, 0.898] | 0.692 [0.684, 0.700] | 0.818 / 0.020 | 0.6775 | 1.000 / 0.072 |

- **Null-world false-alarm rates:** U-act 0.018–0.065; U-event 0.072–0.287. The U-event null rate exceeds the
  nominal 0.05 even on raw prices (0.077), as the design anticipated: s_t is heteroscedastic through the activity
  cycle.
- **Why tick_grid and affine_level match raw prices (to floating-point precision):** tick_grid and affine_level are affine in the price, and the
  three measures do not change under a constant scale.

## 6. Reading and limits
- **Inside one synthetic generative model, with an attacker that knows it.** A6 is a strong likelihood attacker,
  not a proven optimum. Real markets are not this model, and nothing here is a measurement on gold.
- **The component ablation is a decomposition inside the model** (§7 of the design), not a general causal
  statement.
- **level_residual uses the exact likelihood** (addendum A1). Compare it with RIP-1-D1, not with the historical
  RIP-1 rows.
- **Implementation choices IC-01…IC-12** are in the results file and in RIP2_BUILD_NOTES.md.
- **Reproducibility:**
  - Seeds and code are fixed; a full re-run gives the same results.
  - The partial reproduction checked 12 cells exactly.
  - Per-unit predictions are not stored by run(): the frozen code reports accuracy vectors as means. A full
    reproduction needs a full re-run of about 100 minutes.
- **CI** did not run (GitHub billing, FL-022).

## 7. What RIP-3 would start from (no decision taken here; RIP-3 not started)
1. The identity in this world sits in the **volatility level and the activity pattern**, in every representation
   that keeps the research structure.
2. The only measured transform that hides part of the identity **without** losing the utility measures is
   affine_level with secret parameters, and it hides the **period** only.
3. Hiding the asset would require acting on the volatility level and the activity pattern themselves. By §5, that
   is exactly what the utility measures need, so RIP-3 must state that trade-off explicitly.
