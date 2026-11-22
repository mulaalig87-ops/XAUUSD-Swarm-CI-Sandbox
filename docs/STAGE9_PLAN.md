# Stage 9 (ب9) — integration and engineering tests: plan and gap analysis

Opened by the founder: «أبدأ المرحلة 9» (2026-11-17). Synthetic data only; OD-10 (gold data), OD-11
(pilot) and G-Z release to language minds stay with the founder.

Sources: execution plan 07 §3.0 (critical-test rule) and §3.4 (WP9-01 … WP9-05); WP7-04 test plan;
WP7-02 flows; candidate §18.1–§18.3.

## 1. Critical-test rule (plan 07 §3.0) — applied as written
1. Every failure is recorded in `docs/FL.md`, and stays there after the fix.
2. Documenting a failure does not replace passing: a critical test closes only by passing on the same
   code version, with its hash.
3. The only exception is a written founder decision after ChatGPT's audit (not for ZERO-PRIOR,
   path independence or leakage unless the founder decides it explicitly after seeing the risk).
4. No next gate opens with an unresolved critical failure. Stage 9 cannot be closed for B9 with one.

## 2. Work packages and what they need — AS AT OPENING (2026-11-17, historical)

This section and §3–§4 record the gap analysis when Stage 9 opened; they are kept unchanged as history.
**The current state is §5** (review P1/TP-50 R2-01: the plan must not contradict the card and FL).


| WP | Task (plan 07) | Acceptance | Can run on what is built? |
|---|---|---|---|
| WP9-01 | Integration on synthetic data | flows match WP7-02; forbidden ones (R → Z) refused by a test | **Partly.** The ledger-level pipeline across layers 1–10 + axis is built and is integrated in `tests/test_integration.py`. **Missing:** the Z / G-Z / R path environments and their flows (ت-03 … ت-07, ت-18), so the required "R → Z refused" test has nothing to run against yet. |
| WP9-02 | Positive and negative controls for every tool and the court, each with its actual result | every control with its real result | **Court and C0 gate: yes** (their code exists). **Missing:** a discovery path engine (§18.2: "at least one discovery path with its controls"; candidate "path 1 or 3" is [لاحق], مع-74), the null-model generators (§11.2 cards), and the leak-check detector. |
| WP9-03 | Graded planted leakage ت1 … ت8 (ت9 by founder decision, §7 #13) | result per type; undetected types → known blind spots | **No.** Needs the lineage leak-check detector (مك-126) and the planted-leak worlds. |
| WP9-04 | Separation Discovery / Validation / Final and no information transfer between paths | no leakage between paths | **Stations: yes** (layers 5–6). **Paths: no** (same gap as WP9-01). |
| WP9-05 | Engineering test report, audited by ChatGPT | passes and failures; no open critical failure | After WP9-01 … 04. |

## 3. Components to build in Stage 9 (gaps found; none is a new rule) — as at opening
| # | Component | Source | Decision needed? |
|---|---|---|---|
| G1 | Z / G-Z / R path environments: Z receives only blinded representations (ت-03); every Z output passes custody (ت-04, built); Z → G-Z and Z → R allowed (ت-05, ت-06); R → Z only through knowledge layer (a), gold observations tagged «خاصة» (ت-07); G-Z / R → layer 10 messages with mandatory fields (ت-18) | س 352–355; CS-01-08; ق-29 | No (FD-01) |
| G2 | One discovery path engine with its controls (§18.2) | س 2322–2323 | **Yes: path 1 (distributional regularities) or path 3 (distinguisher)** — [لاحق], مع-74 |
| G3 | Null-model generators for the §11.2 cards used in tests (full shuffle, block bootstrap — uncertainty only —, time reversal, IAAFT, pair shuffle within volatility blocks, zero-conditional-mean generative); IAAFT and block bootstrap only with their assumption tests (TP-82, TP-81) | §11.2; WP7-04 §2.1, §11 | No (FD-01); assumption tests first |
| G4 | Lineage leak-check detector and planted-leak worlds ت1 … ت8 (+ ت9 if the founder includes it, §7 #13 «يُدرج») | مك-126; س 1529–1536 | No |
| G5 | Control code and synthetic worlds for each matrix row (TP-20, TP-21/tool, TP-46, TP-47) | WP7-04 §2, §2.1 | No |

## 4. Order — as planned at opening
1. WP9-01 ledger-level integration (this commit) + FL.
2. G1 (paths and flows) → WP9-01 flow tests incl. R → Z refusal; WP9-04 path part.
3. G3 + G5 for the court and C0 gate → WP9-02 partial results.
4. G2 after the founder's choice → its controls.
5. G4 → WP9-03.
6. WP9-05 report → ChatGPT audit.

## 5. Status (updated per merge)
| Item | Status |
|---|---|
| WP9-01 ledger-level integration | done (WP9-01a) |
| G1 paths and flows; R → Z refusal test | done (WP9-01b, review R1 fixed in WP9-01c, `paths.py`, `tests/test_paths.py`; integrated in `tests/test_integration.py`) |
| G2 discovery path 1 | built (`path1.py`, card `docs/paths/PATH1_CARD.md`); v1–v3 FAILED (FL-011); v4 met the criteria but its reference left H0 (review); **v4.1 PASSED all five controls** (founder OD-S9-05, FD-01-D42; `docs/results/WP9-02_path1_v41.json`); FL-011 closed by v4.1 |
| G3 null generators (6 cards) | done (`nulls.py`) |
| G5 + WP9-02 part 1: TP-21/tool for null cards | run: full_shuffle, iaaft, pair_shuffle (v2) pass; v1 pair_shuffle failed (FL-007). Not runnable (open in architecture): time_reversal procedure, zero_cond_mean model family. TP-81, TP-82 run (§6, §6.1). Path 1: see the G2 row |
| WP9-02 part 2: TP-47 (C0 gate), TP-46 (court) | run: 4/4 C0 worlds and 2/2 court worlds pass (FD-01-D32); court output stable across two independent systems |
| G4 leak check + WP9-03 TP-50 (ت1–ت9) and TP-50.0 | run (FD-01-D38): report complete; blind spots ت8 (≤ 0.03) and ت9 → `docs/KNOWN_BLIND_SPOTS.md` |
| Cross-layer malformed-input test (S1-01 of WP9-01 review) | done (WP9-05a, WP9-05b): FL-013 (critical, fixed), FL-014, FL-015 (fixed); final sweep, probing before each first commit: 81 kinds / 5 389 probes / 0 crashes / 65 accepted values listed |
| WP9-04 stations and paths | done: traceability `docs/WP9-04_TRACEABILITY.md` (TP-04, TP-60.01–19, TP-61.01–16: covered 31, partial 1, not operational 5); gap ت-09 / م-10 closed by `knowledge_passage.py` (FD-01-D39) |
| WP9-05 | DRAFT report written; report audited (R2: NO BLOCKER); **B9 CLOSED** (OD-S9-06) |

## 6. TP-81 and TP-82 — measured and declared (FD-01-D33; `docs/results/TP81_TP82.json`)
Measure-and-declare experiments (WP7-04 §11): no pass threshold; a synthetic result does not show that
the assumption holds in gold.
- **TP-81 (block bootstrap, coverage of the mean, nominal 0.95, tolerance 0.03):** iid: 0.92–0.94 for
  b ≤ 20 (within), 0.87 at b = 40 (outside). AR(1) 0.5: 0.71 at b = 1, 0.89–0.915 for b = 5…40 (all
  outside tolerance, best at b = 20). ARFIMA d = 0.3 (long memory): 0.26–0.57 (far outside at every b).
  Declared: under long memory the weak-dependence assumption of the card fails badly; under short
  memory the interval under-covers by 3.5–6 points at n = 400.
- **TP-82 (IAAFT, nominal 0.05, tolerance +0.10):** arm (a) false-rejection rate 0.125 (within the
  tolerance, above nominal; R = 40, se ≈ 0.05 — not proof of calibration); arm (b) rejection rate under
  assumption violation: level 0.0, variance shift 0.35, spectral shift 0.60.
  Declared: IAAFT's null is NOT valid when the variance or the spectrum changes inside the window
  (as the card warns, س 829).
- **Finding on the pre-registered profile metric:** the profile distance was LOWER in the non-stationary
  worlds (1.09–1.22) than in the stationary arm (1.52), so by the pre-registered rule the surrogates
  "reproduced" the profile and §11.1's "failure of the null construction" could not be assigned. Cause:
  the metric scales each component by the ORIGINAL's spread across windows, which is largest exactly when
  the original is non-stationary. The metric does not discriminate; this is a design defect of
  FD-01-D33, declared here, not corrected after the fact. A corrected metric needs a new pre-registered
  version (scale by arm (a)'s spread, or compare first-half vs second-half profiles). **Done: v2, §6.1
  (FL-009 closed).**

### 6.1 TP-82 re-run with the v2 profile metric (FD-01-D34) — same seeds, rates reproduced exactly
Reference: arm (a) mean v2 distance 1.387 → cut-off 2 × 1.387 = 2.774.
| world | rate (arm b: under assumption violation) | v2 distance | reading (§11.1) |
|---|---|---|---|
| (a) stationary AR(1) | 0.125 (se ≈ 0.052) | 1.387 | calibration arm |
| (b) level shift | 0.000 | 2.183 | no inflation beyond tolerance |
| (b) variance shift | 0.350 | **7.249** | **failure of the null construction**: inflation in (b) only, (a) sound, profile not reproduced |
| (b) spectral shift | 0.600 | 2.757 | inflation with the profile counted as reproduced — **just below the cut-off (2.757 vs 2.774)**; declared, not classified by §11.1 |
The v2 metric discriminates the variance shift clearly; for the spectral shift it sits at the boundary,
so that reading is fragile and is declared as such. FL-009 is closed for the metric (v2 discriminates);
the spectral-shift case stays a declared limitation. IAAFT's use is now restricted at every use point
(`use_restriction_registered` + `restricted_use_justified`, review R1-01).

## 7. Path 1 (P1-distributional) — TP-21/tool results (FD-01-D35, D36; `docs/results/WP9-02_path1_controls.json`)
| version | real (≥ 0.80) | spurious (≤ 0.15) | null (≤ 0.15) |
|---|---|---|---|
| v1 rotation null | **0.28 FAIL** | 0.06 | 0.04 |
| v2 run-permutation null | **0.00 FAIL** | 0.00 | 0.02 |
| v3 per-cell rotation nulls + Holm, M = 199 (OD-S9-02, FD-01-D37) | **0.66 FAIL** | 0.10 | 0.08 |
v3 generalisation (declared): real 0.90 at n = 800, 0.58 with runs of 20, 0.38 with runs of 120;
spurious 0.06–0.14; null 0.04–0.12. Measured (not a guarantee, see the validity caveat): v3's spurious and null rates stayed within the
criteria at every size tried and its real-effect rate grew with n; at the pre-registered n = 400 it is
below the criterion.
FL-011 open (critical). **Validity caveat (review R1-01, accepted):** the v1 and v3 reference sets
(rotations in [n/10, n − n/10]) exclude the identity and a linear series is not rotation-invariant, so
their p-values are not shown valid: the spurious/null rates above are measurements on these worlds, not a
statistical guarantee, and the 0.66 is not read as power only. Generalisation worlds measured and
declared in the results file. Stopped as
pre-committed in FD-01-D36 and FD-01-D37: the next step is the founder's decision (HANDOFF, open items).

## 8. WP9-03 — graded planted-leak test (FD-01-D38; `docs/results/WP9-03_TP50.json`)
| type | lineage check | statistical rejection (nominal 0.05) | state |
|---|---|---|---|
| TP-50.0 clean | 0.00 false alarms | 0.03 | measured |
| ت1 s_t directly | 1.00 | 1.00 | both |
| ت2 centered window | 1.00 | 1.00 | both |
| ت3 slice-wide normalisation | 1.00 | 0.06 | lineage only |
| ت4 revised data version | 1.00 | 1.00 | both |
| ت5 estimation overlapping the slice | 1.00 | 0.99 | both |
| ت6 market vs availability time | 1.00 | 1.00 | both |
| ت7 cached artefact without provenance | 1.00 | 1.00 | both |
| ت8 weak partial, f = 0.01 / 0.03 / 0.10 / 0.30 | 0.00 | 0.04 / 0.05 / 0.38 / 1.00 | blind / blind / statistical / statistical |
| ت9 next size inside E_t | 0.00 | 0.04 | **known blind spot** |
Lineage rates are 0 or 1 by construction of this check (deterministic rules); the informative results
are the statistical rates and the types invisible to the check (code bypassing the capture, implicit
encodings inside an innocuous field). ت8: the smallest TESTED fraction with inflation is 0.10 — not a
true minimum detectable leak (levels between 0.03 and 0.10 untested; review R1-03).

### 7.1 Path 1 v4 (founder OD-S9-05, FD-01-D41) — met the criteria, reference INVALID (superseded by §7.2)
| world | criterion | v4 |
|---|---|---|
| real (cell A ×1.8) | ≥ 0.80 | **0.98** |
| spurious (stochastic volatility) | ≤ 0.15 | 0.04 |
| null (iid) | ≤ 0.15 | 0.06 |
| spurious_level (mean regimes) | ≤ 0.15 | 0.02 |
| null_heavy (t3) | ≤ 0.15 | 0.04 |
Reference set: permutations of cells across runs (exchangeability stated on the card); n = 1600 (declared
change after seeing results). FL-011 closed on this code version.

### 7.2 Path 1 v4.1 (FD-01-D42) — PASSED; closes FL-011
| world | criterion | v4.1 |
|---|---|---|
| real (cell A ×1.8) | ≥ 0.80 | **0.84** |
| spurious (stochastic volatility) | ≤ 0.15 | 0.02 |
| null (iid) | ≤ 0.15 | 0.06 |
| spurious_level (mean regimes) | ≤ 0.15 | 0.02 |
| null_heavy (t3) | ≤ 0.15 | 0.00 |
Reference: exact uniform arrangements of cells over the maximal runs with no adjacent repeat and fixed
per-cell run counts (run structure preserved in every draw, tested). Real-effect rate fell from v4's 0.98
to 0.84 with a valid reference.
