# RIP-3 build notes — design v0.4 (FD-01-D47) → code. BUILD authorised by OD-S9-11; RUN not authorised

The code is in `src/xauusd_swarm/rip3.py`, the tests in `tests/test_rip3.py`. Nothing here changes the frozen design
(sha256 `efb7e16315476c4d4caa523fc8d45adcdd1c3ae0e6bbc13d35b8d7902def7898`). Each item below is a choice where the
design is silent, made before any run and listed for review (founder condition: no silent difference between design
and code). The same text is kept in `rip3.IMPLEMENTATION_CHOICES` and is written into every result file.

**Guard.** `rip3.run_job` / `run_jobs` refuse the registered sets `eval` (6201) and `confirm` (6301) unless called
with `authorised_run=True`. Nothing in the BUILD calls them so. BUILD-stage checks use the development range only:
6101 (attacker development), 6102 (`build` units, A6 checks, W2 moments), 6103 (`smoke`, small end-to-end checks),
7401+ (W2 truth Monte Carlo).

## Implementation choices
| ID | Choice |
|---|---|
| IC3-01 | Streams. Every random draw comes from a Python random.Random seeded with the string 'RIP3|<base seed>|<role>|<world>|g<g>|<asset>|<period>|<family index>|...' (str seeding is sha512-based and platform independent). Family stream ('fam'): rip1_attack.draw (c, a, b, m), then tau = randint(128, 384), then u = uniform(-1, 1) for the M2 scale. Member stream ('m', member index): the series' own stream (design §4.3 'the series' own random.Random stream'); W1 draws n gauss values, W2 the burn-in then the n (G, Q) pairs. |
| IC3-02 | M2: ln kappa = w·u with the family's single u ~ U(-1, 1), so ln kappa ~ U(-w, w) for each w in {1, 2, 4} (the three grids share the family's u: paired). kappa is per family (shared by members, design §3). |
| IC3-03 | Seed roles. dev 6101 (attacker development); build_holdout 6102 (BUILD-stage validation of A7, M1/M2 A6 checks: development range, design §9); eval 6201 (identity and utility evaluation, roles 'eval', 'util_planted', 'util_null'); confirm 6301 (same roles). Bootstrap: numpy default_rng(6299) for eval, (6399) for confirm; smoke 6103 (BUILD-stage end-to-end checks with small sizes; bootstrap 6193); per world, sets drawn in the order ind, g4, g16, then utility, B sets each, stratified by class. |
| IC3-04 | Development sizes. S-ind: 2000·mult series per class, mult in {1, 2, 4}, nested (the x1 set is the first 2000 family indices of the x4 set). S-pool g: 2000·mult/g families per class (the same number of series), nested likewise. A1, A3 and A4a/A4b use the x1 set; A2, A7 and A8 are built at x1, x2 and x4 (C-O3). The identity number reported for A2, A7 and A8 is the x4 value (the most trained); x1 and x2 are stored. |
| IC3-05 | A7 standardises the summary with development means and population standard deviations (sd 0 -> 1, as reid._standardiser) before the Ledoit-Wolf fit: the shrinkage target (scaled identity) needs commensurate scales. A Gaussian with full covariance is affine invariant; the shrinkage is not. |
| IC3-06 | A7 in S-pool: per-class Gaussian fitted on the member summaries of the S-pool development families of the same g and size; the family score is the sum of the members' log-densities. |
| IC3-07 | A8 in S-pool: the family summary (mean of member raw summaries) is z-scored with the means and sds of the development family summaries; Euclidean k-NN, k = 15, over development families. Tie rule as S-ind: majority, then smallest summed Euclidean distance of that class's neighbours, then lowest class index. |
| IC3-08 | Delta-shown control (M1-Dshown): A1/A2/A4 get the Delta one-hot (rip2 IC-03); A3 never sees Delta; A6 uses delta_seen; A7 and A8 exclude every class whose tick differs from the shown Delta (A8: neighbours searched only among development units with that tick). |
| IC3-09 | Phase of the summary's 64 phase-RMS values: phi = t mod 64 with t the generator step index of each output value (returns-based outputs: t = 1..511; level outputs B-AF, B-LRS: t = 0..511). ACF of x^2 is reid._acf (mean-centred). log-RMS uses max(RMS, 1e-300). |
| IC3-10 | Zero denominators. M1 / M6: if RMS = 0 the output is all zeros. M3: if the window RMS is 0 then x_t = 0 (the numerator is in the window, so it is 0 too). M5: a phase with c_phi = 0 gives x = 0 on that phase; if the mean profile is 0 the output is all zeros. |
| IC3-11 | A1, A2, A3, A4a/A4b are numpy re-implementations of reid.attack / rip2.a1_a2 / rip2.a4_feats with the same standardiser, distances and tie rules (tested equal on sample data); the pure-Python versions are too slow at 32,000 development series. |
| IC3-12 | A6 for M1 and M2 is evaluated in u = 1/lambda (= 1/kappa) where the Gaussian log-density is quadratic: g(v) = C + n·v − (A/2)e^{2v} + B·e^{v}, v = ln u, A = Σx²/s², B = Σμx/s². M1: per member, trapezoid on v* ± 12 sd (sd = (−g''(v*))^{-1/2}), 257 points. M2: members summed (kappa shared), v restricted to [−w, w] with density 1/(2w); window [v* ± 12 sd] ∩ [−w, w], 257 points; if v* lies outside [−w, w], the window runs from the bound to the farther of v* ∓ 12 sd and bound ∓ 40/|g'(bound)| (FL-027), with 16385 points. Verified against dense quadrature. |
| IC3-13 | W2 burn-in: from (h, eps) = (sigma_k^2, 0) the recursion is applied 500 times (burn-in steps 0..499); step t = 0 of the series then uses h_0 = omega + alpha·eps_499^2 + beta·h_499. |
| IC3-14 | W2 truth: the central sum uses the observed price j·tick rounded to 10 decimals (numpy round; rip2.uvol_truth_step uses Python round, which can differ only at an exact decimal half, a 1e-10 price difference); F_nu for the central cells is the closed form for nu = 5; the tail quantities T0, T1, T2, U2 and F_nu(y_f) use the regularised incomplete beta (continued fraction) on the small argument. |
| IC3-15 | Utility of B-AF and B-LRS: U-act and U-event as RIP-2 (s = squared increments of the level series); U-vol is quoted from RIP-2 (design §4.2) and U-ratio is not defined for them (not built on r). |
| IC3-16 | Maximum over attackers: per cell and target, the attacker (x4 for A2/A7/A8) with the highest mean accuracy; ties go to the order A6, A7, A8, A1, A2, A3, A4a, A4b. Paired differences use the per-unit vectors of the chosen attacker on each side. |
| IC3-17 | Selection (§7.4 step 2): the joint-identity reduction in g16 used for ranking is the smaller of the W1 and W2 paired reductions (both must be positive by §7.3). Floors (§7.2) must hold in both worlds. Nearest competitor for the confirmatory step: the next candidate of the same class in that ranking. |
| IC3-18 | Pareto status (report only): candidate X dominates Y in the same class if X's max-attacker joint identity is <= Y's in S-ind and g16 in both worlds and X is at least as good on every §7.2 utility measure in both worlds, with one strict inequality. |
| IC3-19 | C-V2 is checked in W1 (where A6 is the true model), for B-LR and B-AF, every scenario and target: A7 (x4) mean >= lower end of A6's bootstrap interval. C-V3 compares A6 and the B-LR utility with RIP-2 (dev-size-dependent feature attackers are not comparable). |
| IC3-21 | W2 truth central sum is accumulated in chunks of 2,000,000 tick levels (same terms, memory bounded). The frozen algorithm has no cap on the number of tick levels; its cost grows like P·sinh(K·b)/tick. |
| IC3-22 | W2 truth for very wide central sums (more than 1,000,000,000 tick levels; below that the frozen exact sum is always used, which covers every step measured in the registered W2 world, at most 1.5e8 levels): the levels j <= 10,000 and the cells clipped at ±K are summed exactly; the remaining full cells are grouped into blocks of width 0.01 in y and each block's sum Σ p_j ln(j·tick/P̃)² is replaced by the continuous integral ∫ f_5(y)(A + b·y)² dy over the block (closed-form t moments), with the proven bound (tick²·W·f_max/(12·b·p_lo³))·(2·L(c1/b + 1) + 1 + L) + (2L/p_lo)·r·M0 per block (midpoint-cell expansion in price; c1 = (ν+1)/(2√ν); r the 10-decimal rounding). The bounds are added to E_u, so the frozen acceptance E_u ≤ 1e-6·q_u is unchanged. Verified against the exact sum (tests; B1 attempts 3 and 4). |
| IC3-20 | W2 moments (C-V1): the moments of z with finite-variance estimators (E z, E z², P(z <= t) at 7 points) get the 4-standard-error rule of the RIP-2 Monte Carlo check; E[eps²] and E[h] are reported without a rule because eps has no finite fourth moment (design §4.3). The GARCH recursion itself is checked exactly by a test. |

## Requests for design change
**DCR-01 — the C-V2 gate (FL-030). Raised, NOT implemented; NOT ADOPTED by the founder (OD-S9-12, 2026-11-22): v0.4 governs.** Written as a separate draft version,
`docs/research/RIP3_DESIGN_v0.5_DCR01_DRAFT.md` (identical to v0.4 except the C-V2 text and a new §14); v0.4 stays the
frozen design. The first draft (v0.5, r1) specifies the founder's rule (paired stratified family bootstrap, B = 2000 in
r1 — raised to B = 100,000 in r2, `RIP3_DESIGN_v0.5r2_DCR01_DRAFT.md`, after review R-B1; neither draft adopted; per sample
D_b = mean(A6)_b − max(mean(A7)_b, mean(A8)_b) with the stronger alternative re-selected inside each sample;
one-sided percentile upper bound with Bonferroni over the 9 gating cells of B-LR; strict rule R0: UB ≤ 0 in all nine;
B-AF computed and published, not gating). Computed on development data only (`scripts/rip3_dcr01_study.py`,
`docs/results/rip3_build/DCR01_study_dev.json`): **R0 fails on B-LR S-ind (UB 0.030 / 0.030 / 0.035)**, which is
structural (A6 is the exact likelihood in W1, so D ≥ 0 in expectation). The draft therefore also states the
non-inferiority alternative R-NI(δ) with its meaning and limits; δ is the founder's to set. Disclosed in the draft:
DCR-01 was formulated after seeing development results; no evaluation or confirmatory data exist.
No other design change was needed or made.

## Pre-registered BUILD-stage checks (fixed before they are run; development range only)

### B1 — W2 U-vol* truth against Monte Carlo (design §4.3: "the RIP-2 Monte Carlo check is repeated for W2 at BUILD,
with the same acceptance rule")
- Script `scripts/rip3_w2_truth_verify.py`. N = 200,000 draws per case, seed 7401 + case index.
- Monte Carlo side independent of the formula code: the W2 innovation drawn exactly as `rip3.innovations` draws it,
  r = μ + s·z, the generator's rounding expression, and the frozen `representations.log_returns`.
- 10 cases: the four assets; typical, spike (h = 9σ_k²) with the shift and the maximum activity factor; zero drift;
  low h; a price just below and just above a half-tick; two stress cases outside the world (s = 1e-5 coarse
  discreteness; s = 0.05 extreme, which exercises the K doubling and the floor terms).
- **Acceptance:** |MC mean − exact| ≤ 4 MC standard errors in **every** case (the RIP-2 rule). Also reported, without a
  rule: the K used, E_u / q_u and whether the 10⁻⁶ acceptance was met.
- A failure goes to FL and is reported as a negative result; neither the formula nor the rule is changed afterwards.

### B2 — A6 for M1 and M2 against an independent dense quadrature (design §9: "derived and verified numerically")
- Script `scripts/rip3_a6_verify.py`. Families: development range (seed 6102, role `a6check`), classes (0,2), (1,0),
  (2,3), (3,1); g = 1, 4, 16; candidates M1, M2 (w = 1, 2, 4); all 16 class hypotheses → 768 comparisons.
- Reference, **amended before any execution** (the first version, which evaluated the direct Gaussian sum on the
  1.6-million-point grid, would cost ~10¹¹ operations per g = 16 comparison):
  (i) algebra — the integrand computed directly from the Gaussian log-density of u·x equals the quadratic-coefficient
  form used by the production code, at 101 points over the production window: |difference| ≤ 1e-6;
  (ii) quadrature — the coefficient form integrated on a non-uniform grid of 4 × 400,001 points (whole range, both
  bounds, mode window); trapezoid.
- **Acceptance:** (i) holds, and |production − reference| ≤ 1e-4 (log-likelihood units), in every comparison.
- Disclosure: while writing the code, the quadrature was explored on scratch families (seed label 1, role 't'); those
  explorations led to the boundary grid of IC3-12. The registered check uses other families (seed 6102).

### B1 attempt 3 — pre-registered 2026-11-19, before execution (founder directive: case 10 by a method with a proven bound)
- Script `scripts/rip3_w2_truth_verify_v3.py`; result `docs/results/rip3_build/B1_w2_truth_verification_attempt3.json`.
  Attempts 1–2 and their file are kept unchanged.
- Method (IC3-22): above 2e7 levels the central sum is computed by exact levels at both ends and below j = 10,000, and
  by blocks of full interior cells (width 0.01 in y) replaced by the continuous t-integral, each with the proven bound
  of IC3-22; the bounds are added to E_u and the frozen acceptance E_u ≤ 1e-6·q_u applies unchanged. The definition of
  U-vol* and the formula of §4.3 are unchanged.
- **Part A (MC, all 10 cases, unchanged N, seeds, rule |z| ≤ 4).** Case 10 counts as passed only if it is computed,
  accepted (E_u ≤ 1e-6·q_u including the block bounds) and |z| ≤ 4.
- **Part B (equivalence).** Exact sum vs block method at K ∈ {50, 200, 400} for every case of Part A and three medium
  cases at the largest measured W2 volatility (b = 0.0206, 0.0117, 0.0100), wherever the exact sum has ≤ 2.5e8 levels;
  rule |exact − blocked| ≤ proven bound + 1e-12·|exact|. All must pass.

### B1 attempt 3 — record of execution (disclosure)
`docs/results/rip3_build/B1_w2_truth_verification_attempt3.json` (written 2026-11-19 14:37, kept unchanged) was produced
in a working session whose record was lost; whether its execution started before or after the pre-registration commit
d6bce2b (14:37:18) cannot be established from the record (FL-031). It is therefore **not counted** as the registered
result. It is kept and reported for transparency. The registered execution is attempt 4.

### B1 attempt 4 — pre-registration amendment 2026-11-22, before execution
- Same script, cases, N, seeds and rules as attempt 3 (`scripts/rip3_w2_truth_verify_v3.py OUT 4`); result
  `docs/results/rip3_build/B1_w2_truth_verification_attempt4.json`.
- One change, made before execution and for faithfulness to the frozen §4.3 ("the exact sum"):
  `rip3.BLOCK_THRESHOLD` = 1e9 levels (was 2e7). The frozen exact sum is used for every central sum up to 1e9 levels,
  which covers every step measured in the registered W2 world (at most 1.5e8, FL-026); the block method applies only
  above 1e9 (in B1: case 10 at K = 400, 9.6e11 levels). Part B (equivalence, forced blocks against the exact sum) is
  unchanged.
- Case 10 counts as passed only if it is computed, accepted (E_u ≤ 1e-6·q_u including the block bounds) and |z| ≤ 4.

### B2 attempt 3 — pre-registered 2026-11-19, before execution (founder directive: high precision for the algebra check)
- Script `scripts/rip3_a6_verify_hp.py`; result `docs/results/rip3_build/B2_a6_verification_attempt3.json`. Same 768
  comparisons, same 101 points, same limits (algebra 1e-6, quadrature 1e-4). Both sides of the algebra check in numpy
  longdouble (precision verified at start: eps ≤ 1.1e-19, log/exp within 1e-17 of 60-digit Decimal; the script stops
  otherwise), inputs converted before any arithmetic; the two attempt-2 failures and the ten largest differences
  recomputed in 60-digit Decimal. **All 768 and every Decimal recomputation must pass.** A failure stays a failure.

### B3 — A7 validation on development seeds (design §9 step 2; C-V2 rule, IC3-19)
- Script `scripts/rip3_build_validate.py b3`: B-LR and B-AF, W1, all scenarios, full development sizes (seed 6101),
  units from seed 6102 (25 / 10 / 5 families per class, as the evaluation).
- **Rule:** for every scenario and target, A7 (x4) mean ≥ lower end of A6's 95 % bootstrap interval. A8 and the
  Ledoit–Wolf shrinkage are reported beside it.
- If B3 fails, it is recorded in FL and reported; FC-4 then applies in the RUN unless the evaluation-set C-V2 passes
  (the gate itself is evaluated on the registered set in the RUN, §7.1). Nothing is tuned after seeing B3.

### B4 — W2 generator moments (C-V1, IC3-20)
- Script `scripts/rip3_build_validate.py b4`: 50 W2 series per class (seed 6102, role `moments`), n = 512.
- **Rule:** |z| ≤ 4 for E z = 0, E z² = 1 and P(z ≤ t) = F_5(t/c) at t ∈ {−3, −2, −1, 0, 1, 2, 3}.
  E[ε²]/σ_k² and E[h]/σ_k² are reported without a rule (no finite fourth moment of ε).

## Results of the BUILD-stage checks (development range only)
| Check | Result | File |
|---|---|---|
| B1 W2 truth vs Monte Carlo — attempt 1 | 9 of 9 computed cases pass (max abs z 2.00); case 10 not computable (FL-026) | `B1_w2_truth_verification.json` |
| B1 attempt 3 | all pass, but **not counted** (FL-031: order relative to its pre-registration cannot be established) | `B1_w2_truth_verification_attempt3.json` (kept unchanged) |
| **B1 attempt 4 (registered)** | **PASS: 10 of 10 cases computed and accepted, max abs z 2.00**; case 10 by the bounded block method at K = 400 (z = −0.55, E/q = 3.5e-7, the block bound included); every other case by the exact sum; Part B: the block method within its proven bound in 34 of 34 checks (diff / bound ≈ 0.27) | `B1_w2_truth_verification_attempt4.json` |
| B2 A6 of M1 / M2 — attempt 1 | **FAILED** (FL-027, code defect, fixed) | `B2_a6_verification_attempt1_FAILED.json` |
| B2 attempt 2 | quadrature 768 / 768; algebra sub-check (double precision) failed 2 / 768 | `B2_a6_verification.json` |
| **B2 attempt 3 (registered, high precision)** | **PASS: 768 of 768**; quadrature max 6.2e-5 (limit 1e-4, unchanged); algebra in longdouble (eps 1.08e-19, log/exp within 5.6e-20 of Decimal-60) max 1.9e-9 at M2w4 g4 class (2,0), v = 3.76, abs g ≈ 9.7e9 (limit 1e-6, unchanged); 12 recomputations in Decimal-60: max 1.7e-48 | `B2_a6_verification_attempt3.json` |
| B3 A7 validation (C-V2 rule) | **FAILED** in 8 of 18 cells (FL-030): B-AF asset in every scenario and joint in g4, g16; B-LR g4 (one family). See DCR-01 | `B3_a7_validation.json` (+ the two job files) |
| B4 W2 moments | **pass** (9 of 9, max abs z = 2.02); reported without a rule: mean of mean(ε²)/σ_k² = 1.012, of mean(h)/σ_k² = 1.008 | `B4_w2_moments.json` |
| B3 / DCR-01 study (information, development data) | strict rule R0 of the DCR-01 draft: FAILS on B-LR S-ind (UB 0.030–0.035); passes g4, g16 | `DCR01_study_dev.json` |

B3 was executed with rip3.py as of 281823b; the later code changes (chunked W2 central sum, M2 boundary window,
_lse delegation, block method above 1e9 levels) do not touch the B-LR / B-AF W1 identity path (see the diff).

## Cost of the RUN (estimate from the BUILD timings, not a measurement of the RUN)
One (candidate, world) job took about 28–33 minutes here (two processes sharing two cores). The evaluation set has
26 jobs plus the truth of each world (W1 ≈ 1.5–2 h, W2 ≈ 1 h of CPU): about 14–16 CPU-hours, about 8 hours on two
cores; the confirmatory step adds about 4–5 CPU-hours. Jobs are resumable and can be split across processes.

## Review R-B1 (independent review of the 76edffd bundle) — resolutions
| # | Severity | Item | Resolution |
|---|---|---|---|
| 1 | BLOCKER | no CI on the final commit | **OPEN — billing (FL-032).** Re-run requested for 76edffd on 2026-11-22 (run 45046829787, attempt 2): GitHub again did not start the jobs. Needs the founder. |
| 2 | MAJOR | B = 2,000 too small for the 99.44 % quantile | Study rev 2 (`scripts/rip3_dcr01_study_v2.py`, committed f141872 before execution): B = 100,000 primary; ladder 2k/10k/50k/100k and three seeds. Statistic and Bonferroni unchanged. R0 decision identical for every B and seed; B-LR UBs unchanged (0.030 / 0.030 / 0.035 in S-ind, 0 elsewhere). The draft now fixes B = 100,000 (`RIP3_DESIGN_v0.5r2_DCR01_DRAFT.md`). |
| 3 | MAJOR | δ = 0.035 read off development data | Withdrawn as a candidate. r2 states the meaning of δ (δ × 100 percentage points of identification accuracy below A6, on returns, per cell, familywise 95 %) and makes the margin costly: for M3–M6 the identity carries a "+δ" allowance and a reduction counts only if its paired lower bound exceeds δ. δ is left to the founder, before any RUN, never changed after evaluation. |
| 4 | MINOR | floating-point error of the block integrals not in the bound | B1-HP (`scripts/rip3_b1_case10_hp.py`, committed before execution): every term of case 10 (10,002 exact levels, 47,152 blocks, tails, E_u) recomputed in Python decimal at 50 digits. |q_float − q_hp| = {hp['abs_diff_float_vs_hp']:.2e} (relative {hp['rel_diff']:.1e}); E_u,hp/q = {hp['E_hp_over_q']:.2e}; criterion |q_float − q_hp| + E_u,hp ≤ 1e-6·q_hp **passes**; the float error uses {hp['diff_share_of_remaining_budget']:.1e} of the remaining budget. Frozen acceptance unchanged. |

## Status
BUILD complete for review (directive of 2026-11-22 and review R-B1 applied; CI still blocked by billing). RUN not authorised. DCR-01 / FL-030: decided by the
founder (OD-S9-12) — v0.4 governs, v0.5 / v0.5r2 and any δ not adopted. Open: FL-032 (CI, billing). IC report: `docs/research/RIP3_IC_REPORT.md`.
