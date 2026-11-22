# WP9-05 — Engineering test report, Stage 9 (B9) — DRAFT for ChatGPT audit

Date: 2026-11-17. Repository main as of this report's merge (see `docs/RELEASES.md`). **SYNTHETIC DATA
ONLY.** Nothing here shows that any method or assumption holds on gold data (س 1460). OD-10 (gold data),
OD-11 (pilot) and the G-Z release to language minds (§26 غ-03) are untouched and stay with the founder.

Plan 07 §3.4 WP9-05: «تقرير الاختبار الهندسي بنجاحاته وإخفاقاته، يدققه ChatGPT»; it is not submitted to
close B9 while a critical failure is open (§3.0). This report lists what passed, what failed, what was not
run and why, so that the founder and the reviewer can judge closure.

**Verdict: B9 CLOSED by founder decision OD-S9-06 (2026-11-18), with the limits of §6 declared.** No critical failure is open; critical item 4 is
complete in its measure-and-declare form: TP-30 was run once (FD-01-D44); every representation is
re-identifiable above chance in the synthetic world (§5a). Closing B9 still needs the founder (§7).
TP-09 (event protocol) is not built; it applies «عند استخدام الأحداث» (CS-05-09) and its gate is enforced
in code (FD-01-D43; accepted by the reviewer). See §2, §3 and §6.

## 1. Rules applied (plan 07 §3.0)
Every failure is in `docs/FL.md` and stays there; a critical test closes only by passing on the same code
version; the only exception is a written founder decision after ChatGPT's audit; no next gate with an open
critical failure. Every design and criterion was committed before its run (commit hashes in
`docs/DECISIONS.md`); results are in `docs/results/*.json` and re-run by tests (heavy ones Linux-only,
OD-S9-04). Test count at this report: see `docs/HANDOFF.md`.

## 2. Critical tests (§3.0, WP7-04 «الحرج 1–7»)
| # | Critical item | Status | Evidence |
|---|---|---|---|
| 1 | Every §18.1 item has a test (TP-01 … TP-13, TP-09.1–3, TP-13.01–12) | **complete except the re-ID part of TP-02 (= item 4)**; TP-09 not triggered, gate enforced (FD-01-D43); TP-13.09 [معلّق] | §3 table |
| 2 | Positive and negative controls for every tool in use and for the court (§2.1 matrix, TP-46) | **passed for every tool in use**; tools without a row cannot be used (enforced) | §4 |
| 3 | Planted leakage ت1–ت8 (+ ت9 by founder decision) | **report complete** (success = complete report, WP7-04 §4); known blind spots ت8 (≤ 0.03), ت9 | `docs/results/WP9-03_TP50.json`, `docs/KNOWN_BLIND_SPOTS.md` |
| 4 | Re-identification test per representation (TP-30) | **MEASURED AND DECLARED** (FD-01-D44; WP7-04 «تُقاس الدقة ويُعلن الناتج»). Threshold stays [معلّق] (CS-01-04). Result: above chance for every representation (§5a). Language-mind attacker not run. | docs/results/WP9-05_TP30.json; test_wp9_05_tp30.py |
| 5 | Separation of paths, R → Z refused (TP-04, TP-60.01–19, TP-61.01–16) | **covered 31, partial 1 (TP-60.01), not operational 5** | `docs/WP9-04_TRACEABILITY.md` |
| 6 | Court determinism (TP-08 a) | **passed**: identical ruling output across reruns and across two independent systems | `tests/test_court_knowledge.py::test_court_deterministic_and_reproducible`, `tests/test_wp9_02_gate_court_controls.py::test_court_ruling_output_is_stable_across_independent_systems` |
| 7 | Tests named critical by the founder or the reviewer | none named | WP7-04 §3.0 table |

## 3. §18.1 items (critical 1)
| Item | Tests | Status |
|---|---|---|
| TP-01 charters, proof paths, د1/د2 separation | test_claims.py::test_open_before_registration_refused, test_claims.py::test_d2_requires_all_six_conditions, test_claims.py::test_no_path_is_evidence_for_another_including_d1_to_d2, test_governance.py::test_both_charters_and_current_versions_required | covered |
| TP-02 governance and lineage | test_governance.py::test_unchecked_rule_does_not_execute, test_governance.py::test_conflict_suspends_and_record_holds_required_fields | covered |
| TP-02 blinding by representations with cards | test_custody.py::test_every_representation_function_has_a_card, test_custody.py::test_representations_on_synthetic_prices | covered |
| TP-02 re-identification per representation (TP-30), joint test (TP-31), report re-ID (TP-33) | test_wp9_05_tp30.py | TP-30 measured (critical 4); TP-31 / TP-33 not run [معلّق] |
| TP-02 output filtering (TP-34), parameter stability (TP-35) | test_custody.py::test_z_output_leaves_only_after_full_custody_review, test_custody.py::test_params_fixed_across_family_slices | covered |
| TP-03 inventory, frozen transforms, C0, session calendar | test_inventory_slicing.py::test_transform_used_only_after_freezing, test_inventory_slicing.py::test_estimated_transform_only_from_discovery, test_inventory_slicing.py::test_c0_rule_missing_template_field_refused, test_inventory_slicing.py::test_session_calendar_needs_three_elements | covered |
| TP-04 stations and Forward | see `docs/WP9-04_TRACEABILITY.md` | covered (Forward: not operational) |
| TP-05 adequacy report | test_evidence.py::test_report_rejects_discovery_or_validation_data, test_evidence.py::test_report_exclusions_need_registered_rule_reason_count, test_evidence.py::test_report_tie_includes_ambiguous_and_no_latent_item, test_evidence.py::test_report_no_reduction_and_family_includes_all | covered |
| TP-06 justified null with a complete card; no confirmation without a valid null | test_falsification.py::test_stage3_basic_null_rules, test_falsification.py::test_no_confirmation_without_valid_null, test_discovery.py::test_language_falsification_needs_null_model_and_accepted_card | covered |
| TP-07 controls per tool and court | see §4 | covered for tools in use |
| TP-08 court: determinism, identities, no budget by renaming, powers by code | test_court_knowledge.py::test_court_deterministic_and_reproducible, test_court_knowledge.py::test_test_instance_must_link_to_registered_claim_identity, test_court_knowledge.py::test_no_new_budget_by_renaming, test_court_knowledge.py::test_thresholds_cannot_change_after_freeze | covered |
| TP-09 event protocol (first observed, tie, observation process; levels 1–3) | gate: test_claims.py::test_event_based_claim_refused_until_tp09_is_built, test_claims.py::test_uses_events_is_mandatory_and_boolean, test_claims.py::test_uses_events_frozen_across_versions | **not built, conditional, not passed.** Applies «عند استخدام الأحداث (نص V05)» (CS-05-09). Gate enforced in code (FD-01-D43): mandatory `uses_events` on every card; an event-based claim is refused while TP-09 is not built; the field is frozen. |
| TP-10 information periods, split design, availability time | test_inventory_slicing.py::test_design_recorded_before_opening, test_inventory_slicing.py::test_no_information_unavailable_at_decision, test_inventory_slicing.py::test_design_c_never_in_validation_or_final, test_inventory_slicing.py::test_design_rules | covered |
| TP-11 failed, stopped and excluded runs stay in the record | test_tp11_tp13_lineage.py::test_tp11_failed_stopped_excluded_runs_stay_in_the_record, test_court_knowledge.py::test_no_deletion_event_exists | covered (new in WP9-05) |
| TP-12 at least one planted leak test | test_wp9_03_tp50.py::test_tp50_reproduces_committed_results | covered (TP-50) |
| TP-13.01–13.12 lineage elements recorded and retrieved | test_tp11_tp13_lineage.py::test_tp13_element_recorded_and_retrieved_after_replay | covered for 13.01–13.08, 13.10–13.12 (new in WP9-05); 13.09 [معلّق] (field recorded, meaning undefined) |

`tests/test_wp9_05_report.py` checks that every test named in this file exists (references and counts
only, not semantic coverage — as for WP9-04).

## 4. Control matrix (critical 2) — actual results
| Tool (matrix row) | Positive | Negative | Result | Source |
|---|---|---|---|---|
| null: full_shuffle | 0.85 | 0.067 | pass (FD-01-D30) | WP9-02_null_controls.json |
| null: IAAFT (+ use restricted to stable windows, mandatory by card) | 0.925 | 0.075; TP-82 declared | pass | same; TP81_TP82.json |
| null: pair_shuffle_vol_blocks | v1 0.683 FAIL (FL-007) → v2 0.817 | 0.017 | pass (v2) | same |
| null: time_reversal, zero_cond_mean | — | — | **no row → use refused** (procedure / model family undefined) | — |
| null: block_bootstrap | not a null | TP-81 declared (coverage) | n/a | TP81_TP82.json |
| C0 gate (synthetic detectors) | 3/3 states | clean → state 4 | pass (FD-01-D32) | WP9-02_gate_court_controls.json |
| court (TP-46) | planted K1, K2 confirmed | null: none | pass | same |
| path 1 P1-distributional | v1 0.28, v2 0.00, v3 0.66 FAIL; v4 0.98 (reference invalid); **v4.1 0.84** | v4.1: 0.02, 0.06, 0.02, 0.00 | **pass (v4.1)**, FL-011 closed | WP9-02_path1_*.json |
| leak check (lineage, FD-01-D38) | TP-50 report complete | TP-50.0 declared (0 false alarms, stat 0.03) | pass (as defined) | WP9-03_TP50.json |
| N-a, N-a′, N-b, N-c, betting test, rediscovery, distinguisher, conditional-information path, engines, lenses | — | — | **not built; no row → use refused** | — |
Precision note (review of v4.1): R = 50 (or 40–100) per world gives a first estimate, not a stable
estimate of power or error rate; e.g. v4.1 real 42/50 = 0.84 has a 95 % Wilson interval of about
0.71–0.92.

## 5. Failures (all in `docs/FL.md`)
FL-001…FL-006 (Stage 8 and early Stage 9: Windows CI, ledger lock, flaky markers, billing, a vacuous
test); FL-007 (pair-shuffle positive control, critical, closed by v2); FL-008 (NaN leak-check hole,
critical, fixed); FL-009 (TP-82 profile metric, closed by v2); FL-010 (path-1 runner crash); FL-011
(path-1 positive control, critical, closed by v4.1 after v1–v3 failed and v4's reference was invalid);
FL-012 (control-code placement); FL-013 (ledger written before a failing apply, critical, fixed by
dry-run apply); FL-014 (validation gaps); FL-015 (malformed-input sweep masked, overstated coverage,
fixed). **No critical failure is open.**

## 5a. TP-30 result (synthetic world, FD-01-D44; best of three attackers, Wilson 95 % over 400 test samples)
| Representation | asset (chance 0.25) | period (chance 0.25) | joint (chance 0.0625) |
|---|---|---|---|
| log_returns | 0.708 [0.6611, 0.7499] (A2) | 0.325 [0.281, 0.3724] (A1) | 0.223 [0.1845, 0.2658] (A2) |
| tick_grid | 0.880 [0.8445, 0.9083] (A2) | 0.463 [0.4142, 0.5115] (A2) | 0.430 [0.3824, 0.479] (A2) |
| level_residual | 0.755 [0.7106, 0.7946] (A1) | 0.407 [0.3604, 0.4563] (A1) | 0.338 [0.2929, 0.3852] (A1) |
| affine_level | 0.807 [0.766, 0.8431] (A2) | 0.330 [0.2857, 0.3775] (A2) | 0.275 [0.2335, 0.3207] (A2) |
| activity_time | 0.850 [0.8117, 0.8817] (A2) | 0.632 [0.5842, 0.6783] (A2) | 0.585 [0.5361, 0.6323] (A2) |
| volatility_time | 0.853 [0.8144, 0.8839] (A1) | 0.600 [0.5513, 0.6468] (A2) | 0.570 [0.521, 0.6176] (A2) |

**Scope of this result (review R2-01):** TP-30 measured how re-identifiable synthetic representations are
when each sample has independent blinding parameters drawn by the experiment's own generator (`reid.blind`,
published seeds 3001/3002). It did **not** test the secrecy of operational blinding parameters drawn inside
Custody/Vault: those were not used, and an attacker holding the code and seeds could regenerate the
parameters. Before TP-30 is relied on as a security measurement of operational blinding, a separate test is
required that draws parameters from Custody/Vault while the attacker has no access to the parameters or the key.

Reading (no threshold applied): no representation hides the asset in this world; period is identifiable above
chance in every representation, most strongly in the time-clock representations. The synthetic assets were
built with distinct tick, volatility and activity patterns, so this measures what these blindings leave, not
gold. A consequence for the founder: with any reasonable threshold under CS-01-04, the current blindings would
not pass as Z-computational on asset identity (candidate §3.2 table) — that verdict is the founder's.

## 6. Not done, deferred, declared limits
- **TP-30 limits:** not a test of Custody/Vault parameter secrecy (§5a scope; a Custody/Vault-drawn re-ID
  test is required before any operational reliance); language-mind attacker not run; same-family pooling not measured; ledger role binding of
  `reid_checker` exercised in custody tests, not in this run; representation cards' `reid_result` unchanged
  until CS-01-04 is decided. TP-31 (joint) and TP-33 (reports) not run. None of these
  may be read as safe from the independent-sample result; TP-30 is not a test of every attacker or output.
- **TP-09 enforcement limit:** the gate trusts the signed `uses_events` declaration; a claim wrongly declared
  `false` is not detected by code (FD-01-D43).
- **TP-09:** event protocol not built; conditional on events being used (CS-05-09). Reading FD-01-D43,
  accepted by the reviewer with the gate enforced in code (`uses_events`, see §3). The founder can
  overrule (then it is built before B9 closes).
- Deferred with triggers: stationarity-evidence binding (TP-81/82 R3-01), time-field format (WP9-04/05a
  R2-01) — both before any real-data stage.
- Known blind spots: ت8 (≤ 0.03), ت9; knowledge used but not named in lineage; IAAFT recognised by name.
- TP-82: spectral-shift reading fragile (2.757 vs cut-off 2.774). TP-81: block bootstrap fails under long
  memory.
- Path 1 v4.1: valid under its H0 (exchangeable cell arrangement over runs); calendar-cycle or
  run-length-dependent labels need another reference; n = 1600 chosen after seeing results (declared).
- Not operational per WP7-04 §13: Forward custodian, allowed blinded groups, G-Z definition, epochs,
  queue (mechanisms built and tested, items not claimed).
