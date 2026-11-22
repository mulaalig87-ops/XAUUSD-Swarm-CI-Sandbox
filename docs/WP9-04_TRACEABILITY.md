# WP9-04 — separation of stations and of paths: traceability (TP-04, TP-60.01–19, TP-61.01–16)

Plan 07 §3.4 WP9-04: «فصل Discovery وValidation وFinal، ولا انتقال معلومات بين المسارات». §3.0 critical 5:
TP-04, TP-60.01–19 (incl. TP-60.05 R → Z), TP-61.01–16. SYNTHETIC ONLY.

Each row names the tests that exercise the item; `tests/test_wp9_04_traceability.py` checks that every
test named here exists and that the counts match. **What that check proves (review R1-02):** consistency
of the references and the counts — NOT that each test still exercises the condition attributed to it.
The semantic link rests on the test names and contents as reviewed; a later change to a named test's
body would keep the traceability check green. Changes to these tests are therefore reviewed against
this table. "Status" is one of:
**covered** (refusal or condition tested), **partial** (what is and is not tested is stated),
**not operational** (the test plan marks the item «مخطط، غير معتمد للتشغيل» or «معلّق»; mechanism tests
may exist but the item is not claimed).

## Stations (TP-04)
| Item | Tests | Status |
|---|---|---|
| TP-04 Discovery / Validation / Final separate | test_evidence.py::test_selection_only_from_discovery_or_validation, test_evidence.py::test_confirmation_only_on_final, test_evidence.py::test_report_rejects_discovery_or_validation_data, test_inventory_slicing.py::test_design_c_never_in_validation_or_final, test_evidence.py::test_no_claim_on_final_outside_the_gate, test_evidence.py::test_exposed_slice_cannot_be_submitted | covered |
| TP-04 Forward commitment (five fields, sealed before first Forward data) | test_inventory_slicing.py::test_slice_plan_rules (Forward slices refused in plans) | **not operational**: Forward custodian ق-12 is «مخطط» (WP7-04 §13); no Forward data exists |

## Forbidden flows (TP-60, WP7-02 م-01 … م-19)
| Item | Tests | Status |
|---|---|---|
| TP-60.01 م-01 prior XAUUSD research → paths / Z | test_court_knowledge.py::test_zero_prior_breach, test_court_knowledge.py::test_zero_prior_from_lineage_not_supplied | **partial**: recorded lineage drives the ZERO-PRIOR state; a planted attempt is DETECTED through lineage, not refused at entry; unrecorded prior knowledge is invisible (same limit as TP-50 ت8) |
| TP-60.02 م-02 raw data touched by non-custody | test_inventory_slicing.py::test_no_inventory_without_permission_and_custody_only | covered |
| TP-60.03 م-03 Z reaches non-blinded data | test_paths.py::test_z_receives_only_blinded_or_layer_a | covered |
| TP-60.04 م-04 Z calls a «تداول» tool | test_paths.py::test_z_cannot_call_trading_tool, test_paths.py::test_refusals_are_logged_and_return_nothing | covered |
| TP-60.05 م-05 R → Z outside layer (أ) | test_paths.py::test_r_to_z_is_refused, test_paths.py::test_r_content_cannot_reenter_z_as_blinded_input, test_paths.py::test_r_to_z_only_via_registered_layer_a_item, test_integration.py::test_end_to_end_synthetic_path | covered |
| TP-60.06 م-06 Z output leaves before custody | test_paths.py::test_z_outputs_reach_gz_and_r_only_through_custody, test_custody.py::test_z_output_leaves_only_after_full_custody_review | covered |
| TP-60.07 م-07 decryption outside G-Z or before seal | test_custody.py::test_gz_decryption_requires_signed_request_from_gz_operator, test_custody.py::test_hidden_truth_only_to_operator_after_seal, test_custody.py::test_forged_or_replayed_request_refused_and_logged | covered |
| TP-60.08 م-08 decrypted output shown to a language mind | test_discovery.py::test_mind_cannot_obtain_decryption, test_custody.py::test_gz_release_to_language_minds_is_locked | covered (release locked, غ-03) |
| TP-60.09 م-09 language minds see non-blinded data | test_discovery.py::test_mind_cannot_obtain_decryption | covered |
| TP-60.10 م-10 knowledge 10 → 7 not through layer 3 | test_knowledge_passage.py::test_m10_knowledge_without_passage_refused, test_knowledge_passage.py::test_r1_01_malformed_seen_is_refused_not_ignored, test_knowledge_passage.py::test_r1_01_variant_spellings_refused | covered (new in WP9-04); limit: knowledge used but not named in lineage is invisible |
| TP-60.11 م-11 hidden truth revealed before seal | test_custody.py::test_hidden_truth_only_to_operator_after_seal | covered |
| TP-60.12 م-12 code-integrity results → queue / knowledge | test_discovery.py::test_code_integrity_results_never_enter_queue, test_court_knowledge.py::test_code_integrity_only_never_decides | covered |
| TP-60.13 م-13 Discovery / Validation data in the adequacy report | test_evidence.py::test_report_rejects_discovery_or_validation_data | covered |
| TP-60.14 م-14 decision in Validation / Final on design C | test_inventory_slicing.py::test_design_c_never_in_validation_or_final, test_inventory_slicing.py::test_design_c_descriptive_only | covered |
| TP-60.15 م-15 information unavailable at decision time | test_inventory_slicing.py::test_no_information_unavailable_at_decision, test_numeric.py::test_s3_03_leak_check_refuses_unknown_times, test_wp9_03_tp50.py::test_tp50_reproduces_committed_results | covered (+ graded leak test) |
| TP-60.16 م-16 gradual reveal of Final / reuse / renamed test | test_evidence.py::test_no_gradual_reveal_after_opening, test_evidence.py::test_exposed_slice_cannot_be_submitted, test_court_knowledge.py::test_no_new_budget_by_renaming, test_evidence.py::test_final_opened_once_all_claims_together_atomically | covered |
| TP-60.17 م-17 claim moved between paths after the result | test_claims.py::test_no_path_is_evidence_for_another_including_d1_to_d2, test_court_knowledge.py::test_instance_added_after_opening_is_descriptive_only | covered |
| TP-60.18 م-18 a mind sees another's hypotheses before its own freeze | test_discovery.py::test_no_hypotheses_before_own_freeze | covered |
| TP-60.19 م-19 exchange outside a registered channel | test_discovery.py::test_exchange_only_through_registered_channel_and_logged | covered |

## Allowed flows (TP-61, WP7-02 ت-01 … ت-16)
| Item | Tests | Status |
|---|---|---|
| TP-61.01 ت-01 raw data → custody | test_inventory_slicing.py::test_no_inventory_without_permission_and_custody_only | covered |
| TP-61.02 ت-02 raw data → inventory and deterministic transforms | test_inventory_slicing.py::test_deterministic_transforms_before_blinding, test_inventory_slicing.py::test_transform_used_only_after_freezing | covered |
| TP-61.03 ت-03 blinding → Z | test_paths.py::test_z_receives_only_blinded_or_layer_a | **not operational**: allowed groups are «معلّق» (سجل 7 §13 #30); the mechanism is tested |
| TP-61.04 ت-04 Z → custody | test_paths.py::test_z_outputs_reach_gz_and_r_only_through_custody | covered |
| TP-61.05 ت-05 Z → G-Z | test_paths.py::test_z_outputs_reach_gz_and_r_only_through_custody | covered |
| TP-61.06 ت-06 Z → R | test_paths.py::test_z_outputs_reach_gz_and_r_only_through_custody | covered |
| TP-61.07 ت-07 R → Z through layer (أ) | test_paths.py::test_r_to_z_only_via_registered_layer_a_item, test_paths.py::test_r1_01_layer_a_item_must_be_a_recorded_r_message | covered |
| TP-61.08 ت-08 decryption table → G-Z | test_custody.py::test_gz_decryption_requires_signed_request_from_gz_operator | **not operational**: G-Z definition ق-01 «مخطط» |
| TP-61.09 ت-09 layer 10 → layer 7 through layer 3 | test_knowledge_passage.py::test_t09_passage_then_use_accepted, test_knowledge_passage.py::test_t09_tags_copied_blinding_to_z_custody_only | covered (new in WP9-04) |
| TP-61.10 ت-10 mind → mind | test_discovery.py::test_exchange_only_through_registered_channel_and_logged | covered |
| TP-61.11 ت-11 Discovery → estimated transforms | test_inventory_slicing.py::test_estimated_transform_only_from_discovery | covered |
| TP-61.12 ت-12 Discovery / Validation → confirmation | test_evidence.py::test_selection_only_from_discovery_or_validation, test_evidence.py::test_full_path_selection_to_final | covered |
| TP-61.13 ت-13 layer 8 → layer 9 | test_court_knowledge.py::test_only_operator_runs_court_and_only_on_sealed_package, test_falsification.py::test_no_confirmation_without_valid_null | covered |
| TP-61.14 ت-14 layer 9 → layer 10 | test_court_knowledge.py::test_knowledge_record_from_court_output, test_court_knowledge.py::test_knowledge_row_must_equal_code_output | covered |
| TP-61.15 ت-15 custody → its log | test_custody.py::test_access_record_fields_mandatory | **not operational**: «الحقبة» ق-02 «مخطط» |
| TP-61.16 ت-16 minds → testing (queue) | test_discovery.py::test_release_interface_t16, test_discovery.py::test_queue_guard_is_court_operator_only | **not operational** per WP7-04 §13 (ق-03, ق-29 «مخطط»); the mechanism is built and tested |

## Summary
Covered 31, partial 1 (TP-60.01), not operational 5 (TP-04 Forward, TP-61.03, TP-61.08, TP-61.15,
TP-61.16). Gap closed in WP9-04: TP-60.10 / TP-61.09 (`knowledge_passage.py`). No item is claimed beyond
what its tests show.
