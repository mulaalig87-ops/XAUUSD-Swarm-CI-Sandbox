# RIP-3 BUILD — implementation choices IC3-01 … IC3-22, item by item

For each choice: where it is implemented in `src/xauusd_swarm/rip3.py`, how the code was checked against the
declared text, and what was actually tested (tests in `tests/test_rip3.py`; checks B1–B4 in
`docs/results/rip3_build/`). "Read against the text" means the code was compared with the declared choice by reading,
without a dedicated test; it is listed as such, not as tested.

| IC | Implemented in | Matches the declared choice | Actually tested |
|---|---|---|---|
| IC3-01 streams | `stream`, `make_family`, `member_stream`, `innovations` | yes: string seeds "RIP3\|…", draw order prm → tau → u; member streams | test_streams_are_keyed_and_platform_independent; test_w1_is_bit_identical_to_reid_simulate; test_w2_recursion_follows_the_specification_exactly (draw order G then Q) |
| IC3-02 M2 scale | `transform` (M2w) | yes: ln κ = w·u, u per family | test_m2_scale_is_exp_w_u_per_family |
| IC3-03 seed roles | `SEEDS`, `SET_BASE`, `evaluate` (bootstrap seed per set) | yes | test_ic3_03_seed_roles_and_bootstrap_seeds; test_registered_sets_are_refused_without_the_run_authorisation; test_run_script_refuses_registered_sets_without_authorisation |
| IC3-04 development sizes | `dev_families`, `identity_scenario` (subset by idx) | yes: 2000·mult/g families per class, nested prefix; A1/A3/A4 at x1; A2/A7/A8 at x1, x2, x4; reported value x4 (`ATT_ORDER`) | test_ic3_04_development_sizes_are_nested_and_equal_in_series; test_smoke_end_to_end (A2x1…x4, A7x1…x4, A8x1…x4 present) |
| IC3-05 A7 z-scoring | `A7Model.__init__` | yes | test_ic3_05_a7_standardises_before_the_shrinkage; test_ledoit_wolf_matches_the_published_formula; test_a7_classifies_well_separated_gaussians |
| IC3-06 A7 in S-pool | `identity_scenario` (A7 fitted on member summaries; log-densities summed over members) | yes | test_smoke_end_to_end (runs the g4/g16 path); the summation itself read against the text |
| IC3-07 A8 in S-pool | `identity_scenario` (family mean of summaries), `a8` | yes | test_ic3_07_a8_family_level_uses_the_member_mean; test_a8_majority_and_tie_rules |
| IC3-08 Δ-shown control | `identity_scenario` (one-hot for A1/A2/A4, `allowed` mask for A7/A8), `a6_scores` (delta_seen) | yes; A3 never sees Δ | test_ic3_08_delta_shown_restricts_the_classes; test_a6_true_class_wins_on_clear_cases (delta_seen excludes other ticks); test_smoke_end_to_end (control cell) |
| IC3-09 summary phase / ACF / log-RMS | `summary`, `phase_rms` | yes | test_summary_vector_has_108_components_in_the_frozen_order |
| IC3-10 zero denominators | `m1`, `m3`, `m5`, `_safe_div` | yes | test_ic3_10_zero_denominators_give_zeros; test_m3_uses_the_trailing_window_including_t |
| IC3-11 numpy attackers | `a1`, `a2`, `a3`, `a4` | yes | test_numpy_attackers_equal_the_reference_implementations (equal to reid / rip2 on sample data) |
| IC3-12 A6 for M1 / M2 | `ll_scale_invariant`, `ll_secret_scale` | yes (window rule as corrected by FL-027) | test_quadratic_form_equals_the_direct_gaussian_log_density; test_m1_and_m2_likelihoods_against_dense_quadrature; test_m2_boundary_window_keeps_all_mass; B2 attempt 3 (768 / 768) |
| IC3-13 W2 burn-in | `innovations` | yes | test_w2_recursion_follows_the_specification_exactly; B4 (moments) |
| IC3-14 rounding in the W2 truth | `_central_exact` (np.round to 10 decimals) | yes | B1 attempt 4 (Monte Carlo uses the generator's Python rounding: agreement within 4 SE in 10 / 10) |
| IC3-15 utility of B-AF / B-LRS | `utility_family`, `observed_s` | yes: U-act, U-event only; no U-vol, no U-ratio | test_baselines_are_the_rip2_representations; the omission read against the text |
| IC3-16 maximum over attackers | `max_attacker`, `ATT_ORDER` | yes | test_ic3_16_max_attacker_tie_order; scripts/rip3_rescore.py recomputes it independently (test_smoke_end_to_end) |
| IC3-17 selection | `select`, `_simplicity` | yes: min over W1/W2 of the g16 joint reduction; floors in both worlds; nearest competitor = next ranked | test_ic3_17_selection_classes_and_failure_conditions |
| IC3-18 Pareto | `pareto` | yes | test_ic3_18_pareto_within_class_only |
| IC3-19 C-V2 (v0.4) | `gates` | yes; on development data the rule FAILED (B3, FL-030) | test_ic3_19_c_v2_rule_on_b_lr_and_b_af; B3 |
| IC3-20 W2 moments | `scripts/rip3_build_validate.py b4` | yes | B4 (9 / 9 within 4 SE) |
| IC3-21 chunked exact sum | `_central_exact`, `TRUTH_CHUNK` | yes | test_w2_truth_chunking_does_not_change_the_sum |
| IC3-22 bounded block method (> 1e9 levels) | `_central_blocked`, `_t5_interval_moments`, `uvol_truth_w2` | yes: exact sum up to 1e9 levels; above, blocks with the proven per-block bound added to E_u under the unchanged acceptance 1e-6·q | test_block_method_matches_the_exact_sum_within_its_proven_bound; test_interval_moments_of_t5; test_fl026_stress_case_is_now_computable_and_accepted; B1 attempt 4 Part B (34 / 34 within the bound) |

## The IC3-22 bound (proof sketch, as implemented)
For a block of full cells j1 … j2 (price cells [j ± ½]·tick, all inside y ∈ [−K, K]) the exact contribution is
Σ_j ∫_cell ρ(p) dp · g(p_j) and the replacement is ∫_block ρ(p) g(p) dp, with g(p) = ln(p/P̃)² and ρ the price density
f₅(y)/(b·p). Per cell, ∫ ρ(p)(g(p_j) − g(p)) dp = −g'(p_j)∫ρ(p)(p − p_j)dp − ½∫ρ(p)g''(ξ)(p − p_j)²dp, and
|∫ρ(p)(p − p_j)dp| ≤ sup|ρ'|·tick³/12. With sup|g'| ≤ 2L/p_lo, sup|g''| ≤ (2 + 2L)/p_lo², sup ρ ≤ f_max/(b·p_lo) and
|ρ'| ≤ f_max(c₁/b + 1)/(b·p_lo²) (|f₅'/f₅| ≤ c₁ = (ν+1)/(2√ν)), summing over the W/tick cells gives
(tick²·W·f_max/(12·b·p_lo³))·(2L(c₁/b + 1) + 1 + L). The observed price round(j·tick, 10) adds at most (2L/p_lo)·r·M₀.
The floating-point evaluation of the closed-form t moments is not part of the proof; it is checked against direct
summation (B1 Part B, diff / bound ≈ 0.27 in every case) and against quadrature (test_interval_moments_of_t5).
