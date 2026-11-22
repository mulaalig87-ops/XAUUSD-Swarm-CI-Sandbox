# TP-81 + TP-82 (WP9-02f) — review register (ChatGPT)

| ID | Severity | Item | Status | Resolution |
|---|---|---|---|---|
| R1-01 | MAJOR | IAAFT's stability restriction not enforced at use points | FIXED | controls layer: `use_restriction_registered` (founder; restriction `stable_windows_or_registered_transform`, source text) and `restricted_use_justified` per use (basis `stable_windows` with windows + stationarity method + evidence hash, or `registered_transform` frozen in inventory + evidence hash). Every null use point (stage 2 swaps, stage 3 basic/alternatives, test instance) calls `require_use`: row first, then a justification for THIS use. The stationarity method itself is «غير معرّف في المعمارية» and is recorded, not chosen. Tests in `tests/test_falsification.py` (`test_r1_01_*`). The restriction becomes active when the founder registers it for the IAAFT row (engineering tests register it). |
| R1-02 | MINOR | arm (b) rates named as false-rejection rates | FIXED | arm (b) field `rejection_rate_under_assumption_violation`; arm (a) keeps `false_rejection_rate`. |
| R1-03 | MINOR | R = 40 precision not visible | FIXED | binomial standard error on every rate and coverage; arm (a) note: `within_tolerance` is not proof of calibration. |
| Q1 | answer | FL-009 handling | ACCEPTED by the reviewer | — |
| Q2 | answer | v2 metric choice | IMPLEMENTED as recommended | half-change vectors scaled by an independent stationary calibration set; pre-registered FD-01-D34 (commit a5eb84f) before the run. Result: variance shift classified as null-construction failure; spectral shift at the cut-off (declared fragile). |

## Round R2
| ID | Severity | Item | Status | Resolution |
|---|---|---|---|---|
| R2-01 | MAJOR | the IAAFT restriction applied only if the founder registered it | FIXED | the restriction is now part of the IAAFT card (`nulls.CARDS["iaaft"]["use_restriction"]`). `controls.mandatory_restriction()` recognises the tool by its id or by its accepted null card naming IAAFT. A matrix row for such a tool is refused until the restriction is registered; a registered restriction must be the card's one; every use point refuses the tool without its restriction even if a row exists (defence in depth for older ledgers). Tests `test_r2_01_*` (row refused, IAAFT named only in its card, wrong restriction kind, use refused with a pre-existing row). The WP9-02 run script registers the restriction before the IAAFT row; re-run gives identical control results (module hash of nulls.py only). |

Limit (stated): recognition is by name (`iaaft` in the id or the accepted card). A tool that implements IAAFT under a name that mentions neither is not recognised; the binding of a null-model id to its implementation is outside this component («غير معرّف في المعمارية» at the level of tool identity).

## Round R3 — closed 2026-11-17: ChatGPT verdict "NO BLOCKERS" on main @ 06e3219 (CI run 44092718370 verified by the reviewer)
| ID | Severity | Item | Status | Resolution |
|---|---|---|---|---|
| R3-01 | MINOR | `stationarity_evidence_sha256` (and the transform's evidence hash) is a signed hash value, not bound to stored evidence whose content can be re-hashed | DEFERRED | trigger: before the first use of a restricted null outside engineering tests (i.e. before any real-data stage, which needs OD-10), or earlier if an evidence store is built in Stage 9. Fix: bind the hash to an evidence item frozen in inventory and recompute it at justification time. |
Reviewer's reminder kept: recognition of IAAFT by name is a known tool-identity limit, to be addressed when tool identity is bound to implementation.
