# WP9-02 (parts a + b) — review register (ChatGPT)

| ID | Severity | Item | Status | Resolution |
|---|---|---|---|---|
| R1-01 | MAJOR | `zero_cond_mean()` accepted NaN conditional means (`abs(NaN) > tol` is False) | FIXED | every stated conditional mean must be finite and not bool before the zero check; tests for NaN, ±inf, True. |
| R1-02 | MINOR | `pair_shuffle_blocks()` accepted NaN / inf / bool magnitudes | FIXED | magnitudes finite, non-negative, not bool; tests for NaN, inf, True, −0.1. |
| S1-01 | self-found | `signs()` turned NaN into sign −1 | FIXED | input validated (finite numbers only); test. |
| S1-02 | self-found | `representations.log_returns(scale=…)` accepted True and inf | FIXED | scale finite, positive, not bool; tests. |
| S1-03 | self-found | `math.isfinite` on a huge int raises OverflowError instead of a refusal | FIXED | `_finite()` refuses it as NullError (same pattern as `court._num`); test. |

Re-run on the fixed code (rule 2, plan 07 §3.0: pass on the same code version): the null-card controls give
identical counts, outcomes, world and code hashes; only `module_sha256["nulls.py"]` changed, recorded in
`docs/results/WP9-02_null_controls.json`. Sweep: no other incomplete numeric check found in `src/` by
`grep "isinstance(…(int, float))"` (the other hit, `court._num`, is already complete).

## Round R2
| ID | Severity | Item | Status | Resolution |
|---|---|---|---|---|
| R2-01 | MINOR | S1-02 incomplete: `representations._check` accepted `True` as a price; `math.isfinite` on a huge int (prices or scale) raised OverflowError | FIXED | one check for the whole package, `numeric.finite_real` (bool refused, huge int refused); used in representations (prices, scale), nulls, court, controls, evidence, slicing, inventory, discovery. Tests `tests/test_numeric.py`, incl. a sweep guard: no other direct `isfinite(` on inputs in `src/`. |
| S2-01 | self-found | the same OverflowError path existed in controls, evidence, slicing, inventory and discovery (`math.isfinite(x)` on ints from signed statements) | FIXED | same change (R2-01). Lesson from R1: the R1 sweep searched `isinstance(…(int, float))` but not `isfinite(`; the sweep guard test now pins it. |

Re-run on the fixed code: null-card controls identical except `module_sha256["nulls.py"]`; C0 and court
controls identical in match, states, confirmed sets and p-values; the court ruling `output_sha256` (and
so `evidence_sha256`) changed because the ruling output embeds the court code hash (`court.py` changed);
recorded in both results files.

## Round R3
| ID | Severity | Item | Status | Resolution |
|---|---|---|---|---|
| R3-01 | MINOR | representation transforms did not validate their numeric parameters (`tick_grid` c, Δ; `level_residual` m; `affine_level` a, b; `activity_time` accepted True) | FIXED | `_param()` (finite_real; > 0 where required) for every parameter; `activity_time` refuses bool and non-int; parametrised tests over bool / NaN / ±inf / 10**400 / str / None for each parameter. |
| S3-01 | self-found | finite parameters could still overflow to an infinite output (a = 1e308, Δ = 1e-320) | FIXED | `_out()` refuses non-finite transform outputs; tests. |
| S3-02 | self-found | custody `Vault.set_params` accepted NaN / inf / bool / huge ints for c, a, b, m | FIXED | finite_real on all four; tests. |
| S3-03 | self-found, **leak-relevant** | `slicing.assert_no_leak` with a NaN decision or availability time reported NO leak (every comparison with NaN is False) | FIXED | non-finite / unknown times raise LeakError ("an unknown time is not 'available'"); tests for NaN, True, None, 10**400 in both positions. |
| S3-04 | self-found | `iaaft(iterations)` and `zero_cond_mean(n, tol)` were not validated | FIXED | integer / finite checks; tests. |

Sweep method this round (not only a pattern search): every public function in `src/` with a numeric
parameter (typed `int`/`float` or compared with `> 0`, `>= 0`) was listed and checked; remaining direct
`isfinite(` calls are only on values already known to be floats (guard test updated).
Re-run: null-card controls identical (nulls.py module hash only); C0 controls identical; court verdicts,
p-values and confirmed sets identical, ruling `output_sha256` changed because the court code manifest
includes custody.py (changed) — recorded in the results files.

**Closed 2026-11-17: ChatGPT R3 verdict "NO BLOCKERS" on main @ 07219f3 (scope WP9-02; CI run 44084027353
verified independently by the reviewer).** Limits stated by the reviewer: results synthetic only;
time_reversal and zero_cond_mean not run (reasons documented); no gate opened.
