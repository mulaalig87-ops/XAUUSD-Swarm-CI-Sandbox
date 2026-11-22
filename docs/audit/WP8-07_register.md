# WP8-07 audit register (ChatGPT independent review)

Round R1 — 2026-11-17 — reviewer: no BLOCKER; 2 MAJOR + 1 MINOR (reviewed main @ e88eae5; did not
run tests).

| ID | Severity (reviewer) | Finding | Status | Fix |
|---|---|---|---|---|
| R1-01 | MAJOR | an accepted null card could be replaced under the same null-model name | FIXED | a second acceptance of the same `null_model` is refused; a revised card is a new null-model identity with `supersedes` naming an accepted one; each adopted falsification records the `null_card_sha256` it was adopted on; `test_r1_01_*` |
| R1-02 | MAJOR | completeness check only looked at top-level values | FIXED | `filled()` checks every depth: no None, blank string, empty list/dict, blank key, non-finite float; no optional fields; 9 negative cases + a nested positive case; `test_r1_02_*` |
| R1-03 | MINOR | `compute_seconds` accepted NaN / Infinity | FIXED | finite and > 0 (not bool) at the rule freeze and in each mind's configuration; `test_r1_03_*`, `test_s1_01_*` |

Self-found (same kind, fixed in the same round):
| ID | Finding | Fix |
|---|---|---|
| S1-01 | a mind's `compute_seconds` could be `True`, equal to a rule of 1 | type check (not bool, finite, > 0) |
| S1-02 | panel `configurations` were not checked against recorded configurations | must be hashes of recorded mind configuration versions |

OPEN COUNT: 0

Closure — 2026-11-17 — reviewer (ChatGPT) checked main @ fe11e29: R1-01..R1-03 and S1-01..S1-02 fixed;
no remaining BLOCKER/MAJOR/MINOR. Verdict: NO BLOCKERS; WP8-07 review closed. Reviewer's stated scope:
governance of the discovery system only; discovery engines not built or tested; tests and CI not run
by the reviewer; no lock or later gate changed.
