# WP8-05 audit register (ChatGPT independent review)

Round R1 — 2026-11-17 — reviewer verdict: NO BLOCKERS (reviewed main at 30cc259; did not run tests).

| ID | Severity (reviewer) | Finding | Status | Fix |
|---|---|---|---|---|
| R1-01 | MAJOR | `t_arrival` not validated (non-numeric, NaN/Inf, before `t_market`) | FIXED | `inventory.check_times()` used by `take_inventory()` and `availability_time()`; tests `test_r1_01_*` |
| R1-02 | MAJOR | `audit_split()` does not re-check embargo, combination, or the recorded parameters | FIXED | split result carries `params` + `params_sha256`; audit checks them against the recorded design and recomputes every rule; tests `test_r1_02_*` |
| R1-03 | MAJOR | applied transform not bound to the frozen implementation | FIXED | `impl_sha256` frozen with the transform; other implementations and lambdas refused; recorded per application (FD-01-D11); `test_r1_03_*` |
| R1-04 | MAJOR | C0 result not bound to the founder-approved test | FIXED | rule carries `test_impl_sha256`; `run_c0` and the validator refuse any other implementation (FD-01-D11); `test_r1_04_*` |
| R1-05 | MINOR | `observation_count` boundaries accept fractions | FIXED | integer check; `test_r1_05_*` |

Self-found (same kind, fixed in the same round):
| ID | Finding | Fix |
|---|---|---|
| S1-01 | `availability_time()` did not validate `t_market` | `check_times()` |
| S1-02 | `split()` silently ignored an embargo outside design B | refused |
| S1-03 | `split()` raised KeyError on unknown / duplicate evaluation ids | `GateError` |
| S1-04 | audit did not check that no sample is in both training and evaluation | added |

Stated limit (R1-03/R1-04): the implementation hash covers the function's own source text and
qualified name, not modules it calls.

Round R2 — 2026-11-17 — reviewer checked R1 fixes in source at 6c6225b (not re-opened); one new finding.

| ID | Severity (reviewer) | Finding | Status | Fix |
|---|---|---|---|---|
| R2-01 | MAJOR | `audit_split()` does not check completeness of the split or duplicate ids | FIXED | every sample must be in exactly one of training / evaluation / removed; duplicates in each part refused; overlap of any two parts refused; the expected removed set is rebuilt from the rules and compared both ways (kept-but-forbidden, removed-without-rule); `test_r2_01_*` |

Self-found:
| ID | Finding | Fix |
|---|---|---|
| S2-01 | a removed sample could carry an empty reason | refused by the audit; `test_s2_01_*` |

OPEN COUNT: 0

Closure — 2026-11-17 — reviewer (ChatGPT) checked main @ 9454e1b: R2-01 and S2-01 present; no new
BLOCKER/MAJOR/MINOR. Verdict: NO BLOCKERS; WP8-05 review closed. Reviewer's stated scope: code review
only; tests and CI not run by the reviewer; not an authorisation to open real data, G-Z, or any locked
stage.
