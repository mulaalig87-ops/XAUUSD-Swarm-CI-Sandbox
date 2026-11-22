# RIP-2 build notes — design v0.7 → code (FD-01-D46). Every choice the design left open (founder condition 6)

The code is in `src/xauusd_swarm/rip2.py` and the tests in `tests/test_rip2.py`. Nothing here changes the design;
each item below is a choice where the design is silent, made before any run and listed for review. The same text
is kept in `rip2.IMPLEMENTATION_CHOICES` and is written into the results.

| ID | Where the design is silent | Choice in the code |
|---|---|---|
| IC-01 | Order of draws in a seed stream | Per family, in class order (asset, period) and then family index: the secret draw (`rip1_attack.draw`: c, a, b, m), then τ (randint 128…384, drawn in every world so that the streams stay aligned), then the n normal draws of each member, in member order. |
| IC-02 | Two worlds per utility seed | Seed 5103 gives the planted U-vol/U-event world (with the shift). The same normal draws without the shift give the planted U-act world, which is the RIP-1 world. Seed 5104 gives the null U-vol/U-event world (no shift), and the same draws with act = 0 give the null U-act world. |
| IC-03 | How Δ is shown to A1, A2 and A4 | A one-hot over the 3 tick values is appended to the feature vector and standardised with the other columns. A3 never sees Δ. |
| IC-04 | Scenarios for the A6 ablation | Every scenario (ind, g4, g16). |
| IC-05 | Condition for feature-group ablation and permutation | C2 with Δ hidden, the operational case (C1 = C2 for representations without a parameter). The groups follow the `reid.features` docstring: distribution 0–17, dependence 18–27, spectrum 28–31, volatility/extremes 32–34, shape/sequence 35–37. |
| IC-06 | σ̂_s in the U-event flag | Population standard deviation (ddof = 0) of s_t, t = 1…511. |
| IC-07 | Order of the bootstrap draws | `numpy.default_rng(5201)`, per scenario in the order ind, g4, g16, B sets each, stratified by class. The same sets serve every compared condition. The utility measures (S-ind) use the same first B sets. |
| IC-08 | Order of the permutation draws | `numpy.default_rng(5202)`, in the order **scenario × representation × group × repeat**, which is the order of the loops in `run()` and `_feature_groups()` (corrected in review B-R1-02; v0.1 of these notes said representation × scenario). Test: `test_permutation_draw_order_scenario_representation_group_repeat`. |
| IC-09 | A6 when the parameters are public | C0, and C1 affine_level (a = 1 and b = 0, so x = P exactly), use the price likelihood: lognormal P_0 around Lg, Gaussian log returns, and the Jacobians. C1 tick_grid uses c = 0, and C1 level_residual uses m = 100 × tick of the class, without integration. |
| IC-10 | Where the group-pooled prior matters | Only tick_grid in C2, where the c prior differs between assets 0 and 3. It is computed there; elsewhere the within-group result equals AP and is reported as identical. |
| IC-12 | Numerics of the level_residual wrapped normal | Computed exactly for every increment: the dual (Poisson summation) series when S/m > 0.5, otherwise the direct sum centred on the nearest image. The frozen RIP-1 function centres the direct sum on j = 0 and drops mass for large increments (**FL-023**, a defect in frozen RIP-1 code). RIP-2 does not inherit it; it is tested against a wide brute-force sum. The support of the transform, x ∈ [0, m), is enforced exactly (x < 0 or x ≥ m → likelihood 0, no tolerance; **FL-024**, review B-R2-02). math.fmod is exact in IEEE 754, so the registered transform never yields a value at or above m. **Deliberate deviation from "the RIP-1 likelihood" in design §5, approved by the founder (OD-S9-08), recorded in `RIP2_DESIGN_ADDENDUM_A1.md`.** Cross-version: compare RIP-2 level_residual A6 results with RIP-1-D1, not with the historical RIP-1 rows. |
| IC-11 | Seeds per scenario | Development families use 5101 + 1000·g and evaluation families 5102 + 1000·g, for g = 1, 4, 16, so the scenarios do not share paths. Utility families use 5103 and 5104 directly (S-ind only). |

## Tests that tie the code to the design
- §4a world table and pooled values against the code: `test_world_table_matches_design_section_4a`.
- The generator path is bit-identical to the frozen `reid.simulate`: `test_path_from_normals_is_the_frozen_generator`.
- Shift and act = 0 worlds, with r_τ the first affected return: `test_shift_and_act_zero_worlds`.
- Attackers with Δ hidden equal the registered RIP-1 code (A1, A2, A4): two equality tests.
- A6 full model with AP priors in C2 equals RIP-1 A6 for log_returns, tick_grid, affine_level and volatility_time.
  level_residual is excluded because of FL-023 and the approved deviation (OD-S9-08). Its exact sum is tested against a
  brute-force wide sum, and its support check against impossible m.
- The U-vol truth equals the registered reference (`scripts/rip2_uvol_verify.exact`) for all five quantity kinds, plus
  level_residual, on all ten cases.
- The permutation draw order scenario × representation × group × repeat is fixed by a test (IC-08).
- Bootstrap stratification and pairing, family-level permutation, Spearman with ties, the U-event index and its
  tie rule, U-act detection, and the registered spec values.
- A smoke run on a tiny spec (throwaway; **not** the registered experiment): about 330 s locally.
- Expected run time at the registered spec, extrapolated from the smoke profile: about 2 to 4 hours (A6 ablation and
  the U-vol truth dominate).

## Status
BUILD only. The registered experiment has not been run. A run needs the code review and a separate go
(FD-01-D46).
