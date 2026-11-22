# Path 1 (WP9-02i/j) + WP9-03 TP-50 — review register (ChatGPT)

| ID | Severity | Item | Status | Resolution |
|---|---|---|---|---|
| R1-01 | MAJOR | v3 (and v1) rotation test: reference set excludes identity / near-identity offsets; validity of the p-value not established; Holm cannot repair it | ACCEPTED — DEFERRED | correct: the reference set is not the full rotation group containing the observed alignment, and a linear series is not invariant under rotation. Recorded in FL-011, the card (v3 section) and `path1.py`. Path 1 stays paused (OD-S9-03); no v4 without a pre-registered design that states the exchangeability hypothesis, justifies the reference set (or uses the full group including the observed alignment) and tests further null and spurious worlds. Trigger: the founder reopens path 1. |
| R1-02 | MINOR | the card still described max-T / v2 | FIXED | card version 2 describes v3 as the current code, keeps v1 and v2, states the R1-01 limitation and the paused status. The card text used by the recorded runs is preserved verbatim as `docs/paths/PATH1_CARD_runs_v1-v3.md` (hash 811377…ed4cd, identical to the recorded one); the run script registers that text, so the recorded runs stay reproducible. |
| R1-03 | MINOR | "minimum detectable fraction" over-claims | FIXED | field renamed `t8_smallest_tested_fraction_with_inflation`; wording in leakcheck.py, KNOWN_BLIND_SPOTS, STAGE9_PLAN: the smallest TESTED fraction with inflation, not a true threshold (levels 0.03–0.10 untested; R = 100). TP-50 re-run: identical rows. |
| Q-TP50-1 | answer | own lineage check under مع-58 | ACCEPTED by the reviewer with the stated separation | the results measure the check of FD-01-D38 only, not an architectural check. |
| Q-TP50-2 | answer | ت9 reading | CONFIRMED by the reviewer | — |

## Round R2 — ChatGPT verdict "NO BLOCKERS" on main @ c76593d
| ID | Severity | Item | Status | Resolution |
|---|---|---|---|---|
| R2-01 | MINOR | `STAGE9_PLAN.md` contradicted the card and FL (gap table still "missing"; §5 "path 1 not run"; §7 read v3 as controlling without the validity caveat) | FIXED | §2–§4 marked "as at opening (historical)" and pointed to §5; §5 G2 row: built, failed v1–v3, validity not shown, paused; §6 TP-82 labels aligned (arm (b) "under assumption violation", R = 40 caveat); §6 points to §6.1 (v2 done); §7 carries the R1-01 validity caveat and reads the v3 rates as measurements, not a guarantee. No experiment re-run. |
Closed.
