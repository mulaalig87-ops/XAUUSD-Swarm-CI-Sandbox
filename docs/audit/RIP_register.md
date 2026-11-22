# Re-ID research programme (RIP) — review register (ChatGPT)

## Round 1 — RIP-0 / RIP-1 v0.1 (verdict NOT READY TO FREEZE)

| ID | Severity | Item | Status | Resolution (v0.2) |
|---|---|---|---|---|
| R1-01 | BLOCKER | attacker isolation not an OS boundary | FIXED (design) | §3.7: dedicated unprivileged user (setpriv, no-new-privs), net/mount/pid namespaces with fresh /proc, close_fds, empty env, root-owned vault 600 and dirs 700, key only in custody memory; probes inside the attacker that must all fail; listing of readable non-system paths. H5 redefined as OS-level on this host; limits declared (same kernel, not kernel exploits, Linux-only). Feasibility checked on the host: root, unshare net/mount namespaces work, setpriv present. |
| R1-02 | BLOCKER | ambiguity of `params_fixed` content | FIXED | §3.2: exact field list (family UUID, commitment, Δ, epoch, envelope); never c,a,b,m, salts, seeds, labels, prices, key; ledger scan test for every secret value and label (critical on hit). Note: Δ is recorded for every family, so H4 covers all six representations. |
| R1-03 | MAJOR | CSPRNG distributions not specified | FIXED | §3.3 frozen table (ranges, independence, per-representation families, no re-draw: abort on refusal, commitment method). c no longer depends on the path max (changed from TP-30, flagged). |
| R1-04 | MAJOR | H1 descriptive with comparability caveat | FIXED | §2 H1 + §3.9 per-representation comparability flags; log_returns not comparable. |
| R1-05 | MAJOR | A4 / pooling details and units | FIXED | §3.4 (unit = family, Wilson over families) and §3.5 A4a/A4b with deterministic tie rule, dev groups with the same g. |
| R1-06 | MAJOR | A5 does not cover all ledger channels | FIXED | §3.5 A5-Δ, A5-f per field, A5-all, A5-comb, family-level in S-pool; frozen field list = snapshot recorded at attacker start. |
| R1-07 | MAJOR | RIP-2 factorial undefined | FIXED (plan) | §4: paired C0/C1/C2 on the same paths, split, attackers and sizes; paired bootstrap; interaction only where the fourth cell is definable, else declared not identifiable; cells frozen in RIP-2 registration. |
| R1-08 | MINOR | file scans are not evidence of no leak | FIXED | §3.7: reclassified as input-sanity checks. |
| R1-09 | MINOR | reproducibility environment and binding | FIXED | §3.10: versions, lock and freeze hashes, code hashes, schema, config; binding chain data → signed submission → seal → revealed-label hashes in the ledger. numpy added pinned (for A6). |
| R1-10 | MINOR | RIP-3 utility measure | ACCEPTED | §4: RIP-3 does not start before its registration fixes utility measures, sizes and comparison. |
| R1-A6 | — | independent attacker A6 | ACCEPTED | §3.5 A6 (marginal likelihood by Monte Carlo over published priors; group likelihood with shared θ). Implementation by Claude; code to the reviewer before the freeze. |

## Round 2 — RIP-1 v0.2 (verdict NOT READY TO FREEZE; no blocker)

| ID | Severity | Item | Status | Resolution (v0.3 + code) |
|---|---|---|---|---|
| R2-01 | MAJOR | A6 affine formula; derive from the actual transform and verify with known parameters | REJECTED (formula) + FIXED (derivation, verification) | The code's transform is x = a·P + b (`representations.affine_level`: `a * p + b`), so P = (x − b)/a and r_t = ln((x_t − b)/(x_{t−1} − b)), which is the v0.2 formula (to first order Δx_t/(x_{t−1} − b)). The reviewer's form Δx_t/(x_{t−1} + b/a) follows from the inverse convention P = a·x + b, which is not the code's. Full derivation from the actual transforms, with Jacobians, now in `rip1_attack.py` (A6 block) and §3.5. Verified with known parameters on throwaway paths: test_inversions_with_known_parameters (affine, tick_grid, volatility_time, level_residual: max error < 1e-12), test_a6_true_class_has_finite_likelihood, test_affine_group_closed_form_matches_numerical_integral. |
| R2-02 | MAJOR | isolation order in code | FIXED | `rip1.sandbox_argv`: unshare (root) → tmpfs hiding (root, inside) → setpriv drop (uid/gid/groups/caps, no_new_privs) → env -i → python -I; close_fds. Tests: test_sandbox_order_namespaces_then_drop_then_python, test_isolation_probes_pass_inside_the_sandbox (ran on this host as root: all probes pass); in-attacker probes record uid, CapInh/Prm/Eff/Bnd/Amb = 0, NoNewPrivs = 1, fds 0–2, env, pids, interfaces. |
| R2-03 | MINOR | H2 judgement | FIXED | H2 descriptive only; any trend test registered separately later. |
| S2-01 | self-found | dev for A5 must be labelled ledger data | FIXED | §3.5a: custody-pipeline DEV families with public labels. |
| S2-02 | self-found | V1 ledger snapshot vs final ledger | FIXED | both committed; prefix check in the reproduction test. |
| S2-03 | self-found | activity_time ≡ log_returns here | DECLARED | run once, reported under both names. |

## Round 3 — RIP-1 code review (verdict NOT READY TO FREEZE)

| ID | Severity | Item | Status | Resolution (v0.4 + code) |
|---|---|---|---|---|
| R3-01 | BLOCKER | V0 could change V1's inputs (shared attacker-owned directory) | FIXED | §3.5b: per-run fresh read-only input dir (root, 644/755), separate writable output dir, read-only code copy; input hashes before/after (abort on change); finished run dirs closed and hidden by tmpfs; shared writable dirs hidden; probes `inputs_read_only` and `no_writable_dir_outside_out` (walks the file system). |
| R3-02 | BLOCKER | attacker saw all five representations at once | FIXED | one run per representation × view (10 runs); only that representation's data in the run; multi-representation attacker declared out of scope (not measured). |
| R3-03 | MAJOR | attacker held the signing key | FIXED | attacker writes unsigned predictions; the trusted orchestrator verifies input and output hashes and signs a per-run submission record with the reid_checker key; stated as role attestation, not execution-integrity proof; seal over the hash of all records; reproduction test verifies signatures and hashes. |
| R3-04 | MINOR | ledger scan did not receive m and salt | FIXED | all vault secrets passed (c, a, b, m, salt, seed, key); values equal to a public Δ text reported as excluded by kind; test covers every kind and the exclusion. |
| R3-05 | MINOR | activity_time not explicit in results | FIXED | `aliases.activity_time = {same_result_as: log_returns, counted_as_independent: false}` in results. |

## Round 4 — RIP-1 code (verdict NOT READY TO FREEZE) + reviewer's hardening plan

| ID | Severity | Item | Status | Resolution |
|---|---|---|---|---|
| R4-01 | — | rip1.py still had the shared attacker dir and key | REJECTED with evidence (stale files) | the reviewed copy was not `8c64f54`; at `8c64f54` the shared dir, `chk_key.hex` and the old signature are absent (closure report §1). Review bundles now carry a commit manifest. |
| R4-02 | — | attacker script still signs | REJECTED with evidence (stale files) | as R4-01; the attacker holds no key since R3. |
| R4-03 | MAJOR | reproduction did not re-run the protocol | FIXED | `reproduce_in_sandbox` + 2 tests (identical / altered). |
| R4-04 | MAJOR | isolation between runs not proven by attempts | FIXED | read-only bind mounts; adversarial attacker test with real attempts (closure report §3). |
| R4-05 | — | test/code interface mismatch | REJECTED with evidence (stale files) | consistent at `8c64f54`. |
| R4-plan | — | hardening steps 1–6 | FIXED | termination before reading, untrusted output, no signing library, full run record, reproduction criterion, adversarial tests, closure report, manifest bundle. |

## Round 5 — single-commit bundle 643e5b0 (hashes verified by the reviewer)

| ID | Severity | Item | Status | Resolution |
|---|---|---|---|---|
| R5-01 | MAJOR | attacker set not enforced complete; A5-f names not bound to a frozen field list | FIXED | `LEDGER_FIELDS`, `expected_attackers`, exact-set check in `validate_predictions`, snapshot check in `run`, same validation in reproduction; tests in docs/audit/RIP1_R5_closure.md. |

## Round 6 — final pre-freeze review of bundle 206a0cd

| ID | Severity | Item | Status | Resolution |
|---|---|---|---|---|
| R6 | — | verdict | NO BLOCKERS — READY TO FREEZE | frozen by FD-01-D45. Reviewer limits recorded: it did not run the tests or CI itself; no RIP-1 test set exists yet; the approval covers the engineering package only, not real data or any other stage. |

## RIP-1 result audit R1 (bundle 6860896) — verdict: result consistent with report and design; no re-run needed

| ID | Severity | Item | Status | Resolution |
|---|---|---|---|---|
| RR1-01 | — | "upper bound" wording for A6 too strong | FIXED | report §6: strong measurement inside the model, not a proven upper bound (grids, declared approximations, no optimality proof). |
| RR1-02 | — | H4 rise 0.79 → 0.89 not a causal estimate of Δ | FIXED | report §1, §5 H4: observed difference between views (V1 adds the whole ledger); same-attacker A6 0.66 → 0.89 shown; controlled Δ shown/hidden comparison moved to RIP-2 (design §4 factor D). |
| RR1-03 | — | sandboxed reproduction evidence not in the bundle | FIXED | `scripts/rip1_repro_attest.py` (frozen primitives only; rip1.py unchanged) → `docs/results/RIP-1_repro_attestation.json`: per run id, input/code hashes, probe hash, checks, reproduced vs original prediction hashes, verdict; 10/10 identical (whole output files byte-identical too). Test: test_reproduction_attestation_is_complete_and_bound_to_the_original. |
| RR1-04 | — | per-sample recomputation impossible from the report bundle | FIXED | `scripts/rip1_rescore.py` recomputes all 260 rows from predictions + revealed truth only (no project code): 0 mismatches; the next bundle carries predictions, truth and the script. Test: test_independent_rescore_matches_every_result_row. |
| RR1-RIP2 | — | RIP-2 direction sound; register Δ as a separate factor, same attacker across conditions, family-level paired bootstrap, diagnosis separate from selection | ACCEPTED | `docs/research/RIP2_DESIGN.md` v0.1 (draft for review). |

## RIP-2 design — review R1 on v0.1 (RR1 items of the RIP-1 result confirmed closed by the reviewer, incl. independent re-score 260/260)

| ID | Severity | Item | Status | Resolution (RIP2_DESIGN v0.2) |
|---|---|---|---|---|
| R2D1-01 | MAJOR | C1 m is asset-specific | FIXED | §4: C1 renamed asset-conditioned public canonical; m = 100 × tick_asset (a member of the set); uniform m rejected with reason; interpretation of C0−C1 and C1−C2 stated (asset-conditioning stays in both C1 and C2, reported as C1 level). |
| R2D1-02 | MAJOR | utility measures not exact; no null worlds or false-alarm criteria | FIXED | §8: increments and variance proxy per representation; U-vol (truth, estimate, Spearman over t = 32…511, null reference); U-act (448-point periodogram, k = 7, 99th-percentile rule, null act = 0, false-alarm rate measured); U-event (CUSUM, τ̂, bridge 1.358 flag, success |τ̂−τ| ≤ 16, null flag rate measured); seeds §9a. |
| R2D1-03 | MAJOR | A6 ablation undefined | FIXED | §7: components μ_a, σ_k, act_a, Lg_k at generator level (products kept whole); pooled values by fixed rule from the public world table (arithmetic / geometric); priors not pooled; only-j and all-but-j models; brackets; scope stated (inside the model, not a general causal decomposition). |
| R2D1-04 | MAJOR | permutation importance must be family-level | FIXED | §7: one family permutation per repeat; all members of a family get the group values of the members of π(f); A2 (S-ind), A4a (S-pool). |
| R2D1-05 | MINOR | bootstrap stratification | FIXED | §6: stratified by asset × period, whole families, same index sets across compared conditions, B = 2000, seed 5201. |

## RIP-2 design — review R2 on v0.2 (R2D1-01…05 confirmed closed)

| ID | Severity | Item | Status | Resolution (RIP2_DESIGN v0.3) |
|---|---|---|---|---|
| R2D2-01 | MAJOR | "all-pooled = chance" does not follow; priors stay asset-linked | FIXED | §7: renamed generator-pooled model; not assumed at chance; its accuracy = information left in priors and transform; expected baseline stated per representation before the run (chance for log_returns, volatility_time, affine_level; possibly above for tick_grid, level_residual; period at chance); only-j / all-but-j read against it. Note: a and b priors are asset-independent (§4a). |
| R2D2-02 | MAJOR | Δ shown pre-decides the asset; ablation not attributable | FIXED | §7: attribution only with Δ hidden; Δ shown reported as conditional; added within-Δ-group accuracy (8 classes for tick 0.01, chance 1/8; 4 classes otherwise, chance 1/4), attributable to components. |
| R2D2-03 | MINOR | τ indexing | FIXED | §8: r_t = ln P_t − ln P_{t−1}, t = 1…511; shift for every t ≥ τ (r_τ first affected); d_t, s_t same index; τ̂ = argmax_k|S_k| + 1. |
| R2D2-04 | MINOR | C1 values not verifiable | FIXED | §4a: frozen table (L, tick, m set, C1 m, c prior; a and b priors; periods) with SHA-256 of reid.py and rip1_attack.py from FD-01-D45; build test to check the code against it. |

## RIP-2 design — review R3 on v0.3 (R2D2-01…04 confirmed closed)

| ID | Severity | Item | Status | Resolution (RIP2_DESIGN v0.4) |
|---|---|---|---|---|
| R2D3-01 | MAJOR | within-Δ-group accuracy not attributable to components: c prior differs between assets 0 and 3 | FIXED | §7: within-group accuracy reported twice: under AP, labelled "conditional on Δ: components + remaining priors"; under group-pooled priors (c ~ equal mixture of U(−1800,1800) and U(−150,150)), attributable to components inside the model. |
| R2D3-02 | MAJOR | only-j does not isolate j; all-but-j is not an independent contribution | FIXED | §7: AP and PP prior settings; only-j under AP = j varying with the remaining prior/transform information; under PP = j's information inside the model (tick_grid: j with Δ, which cannot be pooled without changing the representation, declared); all-but-j = effect of pooling j inside the full model, including interactions, not an independent causal contribution; brackets and expected baselines per prior setting. |
| R2D3-03 | MINOR | CUSUM tie-break | FIXED | §8: ties broken by the smallest k, everywhere. |

## RIP-2 design — review R4 on v0.4 (R2D3-01…03 confirmed closed)

| ID | Severity | Item | Status | Resolution (RIP2_DESIGN v0.5) |
|---|---|---|---|---|
| R2D4-01 | MAJOR | U-vol compared different quantities across representations (relative-vol truth vs increments in representation units) | FIXED | §8: truth in each representation's own units: v_t = sqrt(mean k_u² σ_u²), with σ_u the generator's exact step standard deviation and k_u the first-order map of a return into the representation's increment (C0 P_{u−1}; log_returns 1; tick_grid P_{u−1}/Δ; affine a·P_{u−1}; level_residual P_{u−1} unwrapped); volatility_time: sqrt(mean σ_u²) against sqrt(mean r_u²). Estimate and truth are the same quantity in the same units; price-level drift sits in both; wrap loss in level_residual counted as a real loss; first-order approximation declared. |

## RIP-2 design — review R5 (full re-evaluation of v0.5; R1–R4 fixes confirmed closed)

| ID | Severity | Item | Status | Resolution (RIP2_DESIGN v0.6) |
|---|---|---|---|---|
| R2D5-01 | MAJOR | U-vol estimator is a raw second moment, truth was a variance (drift) | FIXED | §8: the truth is the exact expected raw second moment E[d_u²|P_{u−1}] per representation, drift included; the estimator stays the raw second moment (no demeaning). |
| R2D5-02 | MAJOR | generator component values not visible in the design | FIXED | §4a: per-asset μ_a, vol_a, act_a; 16-value tables of σ_k and Lg_k; pooled values (μ̄ = 0.000005, act̄ = 0.3625, σ̄ = 0.00101574, L̄g = 66.2936) computable from the tables; build test checks every value. |
| R2D5-03 | MINOR | first-order approximation needs a bound or the exact map | FIXED | §8: exact g(μ,σ) = e^{2μ+2σ²} − 2e^{μ+σ²/2} + 1 replaces the linearisation; tick rounding modelled (tick²/6); the sizes of the terms v0.5 ignored are given (drift ≤ 0.0048, linearisation ≤ 9.7e-5, rounding ≤ 0.0039 for P ≥ 0.9 Lg). |

## RIP-2 design — review R6 on v0.6 (all earlier items confirmed closed) + founder instruction to close U-vol definitively

| ID | Severity | Item | Status | Resolution (RIP2_DESIGN v0.7 + RIP2_UVOL_DERIVATION.md) |
|---|---|---|---|---|
| R2D6-01 | MAJOR | U-vol truth called exact but the rounding term was first-order and assumed independent uniform errors not given by the deterministic rounding | FIXED | Cause found in the frozen generator: rounding is deterministic nearest-tick on the latent price (no feedback); consecutive errors are not independent. Inconsistency of v0.6 stated. Path A chosen (path B would change the RIP-1 world): exact conditional expectation as a finite sum over the tick levels the rounding can produce, for every representation; estimator unchanged; formula and unit table; numerical verification pre-registered (10 cases incl. zero drift, lowest/highest σ with shift, both sides of a half-tick, two coarse-discreteness stress cases; N = 200,000, seed 7301 + i; acceptance |MC − exact| ≤ 4 SE in all 50 comparisons). Result: see below. |
| R2D6-01 result | — | pre-registered verification | PASS | 50/50 comparisons within 4 SE (max |z| 1.80; 10 independent cases); v0.6 formula off by ≤ 8.1e-04 in the registered world and up to 13.9% under coarse discreteness, where the exact sum still matches. Derivation §6. |

## RIP-2 BUILD — review B-R1 on 8ce02e9 (NOT READY TO RUN) + founder decision OD-S9-08

| ID | Severity | Item | Status | Resolution |
|---|---|---|---|---|
| B-R1-01 | MAJOR | IC-12 exact level_residual likelihood vs frozen design §5 "RIP-1 likelihood" | DECIDED / FIXED | Founder decision OD-S9-08: keep the exact likelihood as a deliberate deviation (design addendum A1; frozen design file unchanged). Historical RIP-1 kept as reported. Separate diagnostic **RIP-1-D1**: the historical code reproduces the committed predictions; with the exact likelihood, A6 identifies the asset in level_residual at ≈0.98 (historical 0.66–0.89). Cross-version rule recorded. While executing it, **FL-024** was found and fixed (RIP-2's exact sum lacked the transform's support x ∈ [0, m)). |
| B-R1-02 | MINOR | IC-08 permutation order documented wrongly | FIXED | notes and `IMPLEMENTATION_CHOICES` now say scenario × representation × group × repeat (the code's order, unchanged). The test pins both the loop nesting in `run()` (AST) and the group × repeat order in `_feature_groups`. |
| B-R1-03 | MINOR | U-vol regression covers only 2 kinds | FIXED | the test compares `uvol_truth_step` with the registered reference `scripts/rip2_uvol_verify.exact` (separate code) for all 5 kinds, plus level_residual, on all 10 cases. |

## RIP-2 BUILD — review B-R2 on c361c00 (B-R1 fixes accepted in principle; 13 manifest hashes matched)

| ID | Severity | Item | Status | Resolution |
|---|---|---|---|---|
| B-R2-01 | MAJOR | review bundle not self-contained (test_rip2_uvol.py, reid.py, representations.py, numeric.py, RIP2_uvol_verification.json missing) | FIXED | complete bundle: every source in the import closure of the RIP-2 tests and scripts, both test files, conftest.py, pyproject.toml, env/test.lock.txt, all RIP-2 docs and evidence. Every file is in the MANIFEST with its SHA-256. The focused test command was run inside the extracted bundle itself. No frozen file changed. |
| B-R2-02 | MINOR | support check had a 1e-12 tolerance | FIXED | strict `x >= m` (and `x < 0`) → likelihood 0. Test `test_level_residual_support_boundary_is_strict`: x = m, x < 0 and 1.5m refused; the largest float below m accepted; 20,000 draws of the registered fmod transform all land in [0, m). |

## RIP-2 BUILD — review B-R3 on cf60cb8 — verdict NO BLOCKERS — READY TO RUN

| ID | Severity | Item | Status | Resolution |
|---|---|---|---|---|
| B-R3 | — | verdict | NO BLOCKERS — READY TO RUN (engineering) | Reviewer checked all 22 hashes and found no extra or missing files; ran the focused tests from the extracted bundle itself (46 passed). Reviewer's stated limits: the heavy test was not completed (its sandbox stops at 60 s); the full suite and CI were not run (FL-022); historical hash stability was not re-derived. Not a permission to run: the registered RIP-2 run needs the founder's explicit go. |

## RIP-2 result audit (bundle 7dbf1f8) — verdict NO BLOCKERS; RIP-2 CLOSED

Reviewer verified: 27 manifest hashes; results.json sha256; counts 170/150/408/75/18; independently re-ran
scripts/rip2_partial_repro.py (12/12 identical); OD-S9-08 and addendum A1 consistent; seeds and spec metadata; no
override; synthetic only. Not run by the reviewer: the full 100-min reproduction; CI (FL-022).

| ID | Severity | Item | Status | Resolution |
|---|---|---|---|---|
| RR2-01 | MINOR | RIP2_DESIGN.md header says DRAFT / not frozen | FIXED (status note) | `docs/research/RIP2_STATUS.md`: the header is stale; FD-01-D46 / OD-S9-09 control; frozen file unchanged. |
| RR2-02 | MINOR | "exactly" overstated for utility | FIXED | report §1.6: "approximately", with the log_returns / volatility_time numbers; tick_grid and affine_level: U-act and U-event identical, U-vol within 5e-7 (floating point); affine_level C1 identical in every measure (checked in results.json). |
| RR2-03 | MINOR | U-vol CIs not in the report table | FIXED | report §5 table now shows U-vol mean ρ with 95 % bootstrap CIs (planted and null); the Wilson fields in results.json are referenced. |

## RIP-3 — design v0.1 submitted for review (OD-S9-10, DESIGN ONLY)

| ID | Item | Status |
|---|---|---|
| RIP3-D0 | `docs/research/RIP3_DESIGN.md` v0.1: measured facts F1–F8 and limits L1–L5 from RIP-1/2; candidates B-LR, B-AF, B-LRS, M1–M6; attackers A1–A4, A6 where tractable (M1 scale-invariant, M2 integrated scale), A7 synthetic-likelihood for all; utility U-vol*, U-act, U-event, U-ratio; second world W2 (GARCH + t5); controls C-O1–O3, C-A1–A4, C-S1–S4, C-R1–R2; validity gates, proposed utility floors, relative identity criterion, selection rule, failure conditions FC-1–FC-5; recommendation M1 (+ M2, M6 anchor) with [T] justification; open points | AWAITING REVIEW; nothing built or run |

## RIP-3 design — review R1 on v0.1 (NOT READY TO FREEZE) → v0.2

| ID | Severity | Item | Status | Resolution (v0.2) |
|---|---|---|---|---|
| R3D1-01 | MAJOR | M5 / act_a mismatch | FIXED | §3.0–3.1 exact generator decomposition (σ_k scalar × m_t with mean m = 1); M5 = phase-profile normalisation with exact flat per-phase RMS; what M5 does not remove stated (scalar level → M6 = M5 then M1; higher-order residual H2; phase alignment); v0.1 wording withdrawn. |
| R3D1-02 | MAJOR | A7 alone for M3–M6 | FIXED | A8 k-NN (k = 15, fixed) on the frozen summary, in the maximum over attackers; baselines too; learning curves; FC-6. |
| R3D1-03 | MAJOR | S-pool normalisation scope | FIXED | every normalisation per series, never family-joint; consequences stated. |
| R3D1-04 | MINOR | W2 keeps the activity pattern | FIXED | W2's claim narrowed to volatility-model misspecification. |
| R3D1-05 | MINOR | P / S frontiers | FIXED | separate classes, frontiers and choices; never ranked together; FC-1 per class. |
| R3D1-06 | MINOR | floors | FIXED | PROPOSED until founder confirmation before any BUILD; CS-01-04 untouched. |

## RIP-3 design — review R2 on v0.2 (NOT READY TO FREEZE; R1 items accepted as resolved) → v0.3

| ID | Severity | Item | Status | Resolution (v0.3) |
|---|---|---|---|---|
| R3D2-01 | MAJOR | A7/A8 share one feature space | FIXED | §4.1 scope paragraph + C-A5: M3–M6 identity bounded by attacker family and 108-component representation; lower bound; not strongest, not exhaustive. |
| R3D2-02 | MAJOR | W2 generator underspecified | FIXED | §4.3 exact W2: standardised t (Var 1), ω_k = 0.02σ_k², init h = σ_k², ε = 0, burn-in 500, draw order, activity/shift after recursion, paired nulls, U-vol* truth, infinite 4th moment stated. |
| R3D2-03 | MINOR | A8 saturation undefined | FIXED | §6 C-O3: A8 reference-set ×1/×2/×4, z-scoring per size, k fixed. |
| R3D2-S01 | self-found | U-ratio true factor | FIXED | variance factor 4 (step doubled), not 2. |
| R3D2-S02 | self-found | A8 per world | FIXED | rebuilt on W2 development data, as A7. |

## RIP-3 design — review R3 on v0.3 (NOT READY TO FREEZE; R1, R2 accepted as resolved) → v0.4

| ID | Severity | Item | Status | Resolution (v0.4) |
|---|---|---|---|---|
| R3D3-01 | MAJOR | U-ratio target 4 wrong with drift | FIXED | §4.2 option (b): exact per-family R* from the U-vol* truth (μ_a and rounding included); class value R_k derived; 4 no longer a target. |
| R3D3-02 | MAJOR | W2 U-vol* density omits μ_a | FIXED | §4.3: location μ_a in every bound; truncation centred on μ_a; closed-form tails; per-step error bound; acceptance 1e-6·q_u; j = 0 is a C-V1 failure. |

## RIP-3 design — final review on v0.4 → FROZEN

| ID | Item | Status |
|---|---|---|
| R3D-FINAL | Final independent review of v0.4 (4e0e861): NO BLOCKERS — READY TO FREEZE; 0 BLOCKER / MAJOR / MINOR open | FROZEN by FD-01-D47; sha256 `efb7e16315476c4d4caa523fc8d45adcdd1c3ae0e6bbc13d35b8d7902def7898`; design freeze only, no BUILD |

## RIP-3 BUILD (OD-S9-11) — submitted for independent review

| ID | Item | Status |
|---|---|---|
| R3B-00 | BUILD package (code, tests, build notes IC3-01…IC3-21, B1–B4 results, FL-026…FL-030) | SUBMITTED for review |
| R3B-DCR-01 | C-V2 gate: B3 failed on development seeds (B-AF; B-LR g4 one family). Option 1 no change (FC-4 expected) / option 2 design v0.5 | DECIDED — OD-S9-12: option 1, v0.4 governs |

## RIP-3 BUILD — founder corrective directive 2026-11-22 (all items in one delivery)

| ID | Item | Status |
|---|---|---|
| R3B-D1 | BLOCKER bundle completeness (numeric.py missing) | FIXED: bundle built by `scripts/rip3_bundle.py` from the import closure at one commit (incl. numeric.py), tested after extraction into an empty folder |
| R3B-D2 | MAJOR B2 algebra in high precision, limits unchanged | DONE: B2 attempt 3 PASS 768 / 768 |
| R3B-D3 | MAJOR B1 case 10 with a proven error bound | DONE: IC3-22 block method (exact sum up to 1e9 levels); B1 attempt 4 PASS 10 / 10; equivalence 34 / 34 |
| R3B-D4 | MAJOR DCR-01 as separate v0.5 with the per-sample max rule | DONE as draft `RIP3_DESIGN_v0.5_DCR01_DRAFT.md`; R0 fails on development data (structural); NEEDS-ALI after review |
| R3B-D5 | FL evidence, regressions, IC report | DONE: FL status update; IC report; tests for IC3-03…IC3-19 and FL-029 |
| R3B-DCR-01 | founder decision on C-V2 | DECIDED — OD-S9-12: v0.4 governs; v0.5 not adopted |

## RIP-3 BUILD — review R-B1 on the 76edffd bundle (NOT accepted: CI missing; DCR-01 needs work)

| ID | Severity | Item | Status |
|---|---|---|---|
| R-B1-01 | BLOCKER | CI on the final commit | OPEN — billing (FL-032); NEEDS-ALI |
| R-B1-02 | MAJOR | bootstrap B too small | FIXED in DCR-01 r2 (B = 100,000; stability across B and seeds shown) |
| R-B1-03 | MAJOR | δ from development data | FIXED in r2: 0.035 withdrawn; meaning stated; margin coupled to M3–M6 claims; δ not adopted (OD-S9-12) |
| R-B1-04 | MINOR | floating-point assurance of the block method | FIXED: B1-HP at 50 digits passes |

## RIP-3 BUILD — review R-B2 on the 155b00f bundle (51/51 hashes verified by the reviewer)

| ID | Severity | Item | Status |
|---|---|---|---|
| R-B2-01 | BLOCKER | CI on 155b00f itself (FL-032) | OPEN — billing; NEEDS-ALI |
| R-B2-02 | — | B1-HP docstring still named mpmath.betainc | CLOSED — fixed in 61eff1b (docstring only; re-execution identical apart from run time); closure accepted by the founder 2026-11-22 |
| R-B2-03 | — | DCR-01 decision | DECIDED — founder decision OD-S9-12 (DECISIONS.md, 2026-11-22): the frozen v0.4 stays governing; v0.5 and v0.5r2 not adopted; no δ adopted; acceptance rules not changed after development results; FC-4 expected for M3–M6 if the RUN confirms it. Frozen design unchanged |
| R-B2-04 | — | independent check of 61eff1b and its diff | SUBMITTED (diff 155b00f..61eff1b = B1-HP docstring + register) |
| R-B3-01 | MINOR | build notes: the B = 2000 of the DCR-01 description did not say it was r1 | CLOSED — fixed in 5eeb005 (states r1 (B = 2000) and r2 (B = 100,000), neither adopted); closure accepted by the reviewer and the founder 2026-11-22 |
| R-B2-01 (update 2026-11-23) | BLOCKER | CI on 155b00f itself (FL-032) | EVIDENCE SUBMITTED — tree-equivalent CI in the public sandbox repository (OD-S9-13), green on Ubuntu and Windows for 155b00f, 61eff1b and 5eeb005: `docs/results/rip3_build/test_runs/FL032_sandbox_ci/EVIDENCE.md`. Stays open until the reviewer checks it |
| R-B2-01 (closure 2026-11-23) | BLOCKER | CI on 155b00f itself (FL-032) | CLOSED — reviewer verdict ACCEPTED: tree SHAs recomputed independently from tree_manifest.json (3/3 match, 222 files each), six job logs checked (pytest steps executed and passed), workflow blob unchanged, skips not failures. Accepted as CI equivalent to the original source tree, not CI on the original commits |
| R-B2-04 (closure 2026-11-23) | — | independent check of 61eff1b and its diff | CLOSED — reviewer checked the diff: the change in scripts/rip3_b1_case10_hp.py is documentation only, no executed computation changed; the high-precision result is unchanged |
