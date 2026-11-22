# WP8-09 audit register (ChatGPT independent review)

Round R1 — 2026-11-17 — reviewer: 1 MAJOR + 1 MINOR, no BLOCKER (reviewed main @ 198dc40; did not run tests).

| ID | Severity (reviewer) | Finding | Status | Fix |
|---|---|---|---|---|
| R1-01 | MAJOR | rows could be registered for leak_check, rediscovery and lens, but their use was not gated (R16) | FIXED | every tool kind is now gated at its point of use: rediscovery at `rediscovery_registered`; leak_check at a governance report that reports planted cases; lens removed from the tool kinds (no lens component or point of use exists; س 2330, TP-22 suspended). Negative and positive tests for each |
| R1-02 | MINOR | planted types could repeat in one report; type not required to be text | FIXED | type must be non-empty text; each type appears once (after trimming) |

Self-found (same kind as R1-01, fixed in the same round):
| ID | Finding | Fix |
|---|---|---|
| S1-01 | null models were used without a row at three more points: stage-2 null swaps, stage-3 alternatives, and the null named by a court test instance | rows required at all three; tests |

OPEN COUNT: 0

Closure — 2026-11-17 — reviewer (ChatGPT) checked main @ db52c68: R1-01, R1-02, S1-01 closed; no
remaining BLOCKER/MAJOR/MINOR. Verdict: NO BLOCKERS; WP8-09 review closed. The reviewer's unclassified
documentation note (stale "not built yet" sentence in the controls.py header) was corrected in the
closing commit. Reviewer's stated scope: code review only; tests, CI, controls and planted worlds not
run by the reviewer; no data or locked gate opened.
