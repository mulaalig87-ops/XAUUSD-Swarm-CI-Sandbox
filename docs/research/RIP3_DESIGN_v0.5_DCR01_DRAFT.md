# RIP-3 — anonymisation alternatives at the volatility and activity level — design v0.5 — DRAFT (DCR-01 only)

**Status of this version.** v0.5 is a separate draft that carries ONE design change request, DCR-01 (the C-V2 gate,
§4.1 and §7.1; full text and disclosure in §14). It is **not applied**: the frozen design remains v0.4
(`docs/research/RIP3_DESIGN.md`, FD-01-D47, sha256 efb7e163…). Every other section is v0.4 word for word. v0.5 needs
independent review and a founder decision before it can replace v0.4.

**Authorisation:** OD-S9-10 (DESIGN ONLY). v0.2 answered review R1; v0.3 answered review R2; v0.4 answers review R3 (change logs in §11, §12 and §13). Nothing in this document has been built, simulated or run. SYNTHETIC ONLY
when it is ever run. Gold data, G-Z and later phases are untouched. The frozen RIP-1 and RIP-2 packages are not
modified. CS-01-04 (the re-identification threshold) stays with the founder: nothing here sets it.

**Labels used throughout:**
- **[M]** measured in RIP-1 / RIP-2, with its source;
- **[T]** theoretical expectation, derived here and not measured;
- **[H]** hypothesis that RIP-3 would test.

No [T] or [H] statement may be quoted as a result.

---

## 1. What RIP-1 and RIP-2 established, and what they did not

### 1.1 Measured facts used by this design [M]
| # | Fact | Source |
|---|---|---|
| F1 | With an attacker that knows the generative model (A6), raw prices, log_returns (= activity_time), volatility_time and tick_grid are identified almost perfectly: joint 0.98–1.00 (S-ind) | RIP-2 report §2 |
| F2 | Secret parameters hide part of the identity in one representation only. affine_level C1 → C2: period 1.00 → 0.375 (secrecy effect +0.625 [+0.583, +0.667]); the asset stays at 0.93 | RIP-2 §3 |
| F3 | Inside the model, identity sits in the volatility level σ_k = vol_a·volx_p and the activity amplitude act_a, and, for level-type representations, in the price level Lg_k. Drift carries almost nothing. In the returns representations, only-σ gives joint 0.68 and only-act gives asset 0.62 | RIP-2 §4 (ablation, Δ hidden, AP) |
| F4 | Δ in the public ledger gives asset 0.75 alone (RIP-1). It adds ≤ +0.062 to A6 but more to feature attackers (A1 tick_grid C2 asset 0.853 → 0.998) | RIP-1 report §1; RIP-2 §1 |
| F5 | Every representation except level_residual keeps U-vol, U-act and U-event approximately as raw prices do. level_residual destroys them: U-vol ρ 0.09–0.24 vs 0.895; U-act power 0.11–0.22 vs 0.82; U-event success 0.04–0.08 vs 0.68 | RIP-2 §5 |
| F6 | The U-event null false-alarm rate is 0.072–0.077 even on raw prices (nominal 0.05), because s_t is heteroscedastic | RIP-2 §5 |
| F7 | Pooling a family (g = 4, 16) drives A6 to 1.00 wherever it is not already there | RIP-2 §2 |
| F8 | The historical RIP-1 level_residual A6 likelihood was defective (FL-023); with the exact likelihood the asset is identified at about 0.98 (diagnostic RIP-1-D1) | addendum A1 |

### 1.2 Limits carried over (each one shapes a control in §6)
- **L1 — one generative model.** Everything was measured in one synthetic world: Gaussian returns, a deterministic
  activity cycle, 4 × 4 classes. Real markets are not this model.
- **L2 — the attackers are not optimal.** A6 is a strong likelihood attacker, not a proven optimum. For
  transforms without a tractable likelihood, the strongest attacker is unknown.
- **L3 — U-vol is defined in each representation's own units** (RIP-2 §8). It does not extend directly to
  nonlinear transforms (§4.2).
- **L4 — per-unit predictions were not stored by RIP-2's run().**
- **L5 — the RIP-2 A6 ablation is a decomposition inside the model**, not a causal statement about markets.

## 2. The question
Is there a transform, acting on the **volatility level** and/or the **activity pattern**, that removes a
measurable share of the identity (asset, period) while keeping the research structure that RIP-2 measured? And
where does the best balance lie?

**The central tension [T]:**
- The identity in F3 is carried by the **absolute** volatility level σ_k and the **amplitude** act_a.
- U-vol, U-event and the shift-ratio measure (§4) depend on **relative, within-series** structure: changes of the
  volatility over time.
- U-act depends on the **presence** of the cycle, which act_a controls.

Hence:
- the absolute level σ_k can, in principle, be removed without cost to U-vol, U-event and U-act;
- the amplitude act_a cannot be removed without cost to U-act.

**[H1]:** no transform removes the asset identity carried by act_a while keeping U-act power at the RIP-2 level.
RIP-3 would test this; it is not assumed.

## 3. Candidate methods (all applied to log returns r̃_t of the observed prices; Δ hidden by default)

### 3.0 Exact definitions (review R1-01, R1-03)
- **Input.** One released series: r̃_t = ln(P̃_t / P̃_{t−1}), t = 1 … 511, where t is the generator step index.
- **Scope of every normalisation: PER SERIES.** Each released series is transformed using only its own values; no
  statistic is pooled across the members of a family, and no member's transform depends on another member. In
  S-pool a family is g separately transformed series, which the attacker may combine. Family-joint normalisation is
  not used anywhere in RIP-3.
- **RMS(v)** = sqrt((1/|v|) Σ v_i²): the raw second moment, **not** demeaned.
- **Phase:** φ(t) = t mod 64. With t = 1 … 511, phases 1 … 63 hold 8 values each and phase 0 holds 7 values.
  c_φ = RMS{r̃_t : φ(t) = φ}.

The generator of RIP-1 and RIP-2 (reid.simulate) gives, before rounding, r_t = μ_a + σ_k · (1 + act_a sin(2πt/64)) · z_t,
with z_t ~ N(0, 1) independent. Two multiplicative parts of this equation carry identity (F3):
- the **scalar level** σ_k, which is the same at every t;
- the **phase modulation** m_t = 1 + act_a sin(2πt/64), whose amplitude act_a is the identity-bearing quantity. The
  shape (one sinusoid of period 64) is the same for every asset; only the amplitude differs.

Because (1/64) Σ_φ m_φ = 1 exactly, **the scalar level and the modulation separate cleanly**: a normalisation by an
overall scalar removes σ_k, and a normalisation by a per-phase profile with mean 1 removes m_t.
Each candidate is fixed here, with its parameter grid. No candidate or parameter is added after the run starts.

| ID | Method | Secret? | Parameters (fixed grid) | What it removes [T] | Expected utility cost [T] |
|---|---|---|---|---|---|
| B-LR | baseline: log_returns (RIP-2 C1 = C2) | no | — | nothing | none (F5) |
| B-AF | baseline: affine_level C2 (RIP-2) | a, b | RIP-1 draw table | part of the period (F2) | none (F5) |
| B-LRS | baseline: level_residual C2 (RIP-2), as the low-utility anchor | m | RIP-1 draw table | period partly | large (F5) |
| M1 | **global standardisation, per series:** x_t = r̃_t / RMS(r̃_1 … r̃_511) | no | — | the absolute volatility level σ_k, up to estimation noise | none on U-vol, U-act, U-event (scale-invariant); the absolute level is lost by design |
| M2 | **secret scale:** x_t = κ·r̃_t, κ = exp(U(−w, w)) drawn per family by custody | κ | w ∈ {1, 2, 4} | σ_k only partly: the attacker knows the prior, so a level outside the overlap of class ranges stays visible; ln σ_k spans ≈ 1.72 | none on the three measures |
| M3 | **rolling standardisation, per series:** x_t = r̃_t / RMS(r̃_{max(1, t−W+1)} … r̃_t), the trailing window including t | no | W ∈ {32, 128} | σ_k; for W ≤ 64 also part of the cycle amplitude | U-act and U-event attenuated, strongly for W = 32; the shift is normalised away after W steps |
| M4 | **rank-Gauss transform, per series:** x_t = Φ⁻¹((rank(r̃_t) − ½)/511), average ranks for ties | no | — | σ_k and the marginal shape (kurtosis) | U-vol and the shift-ratio reduced (magnitudes compressed); U-act partly kept |
| M5 | **phase-profile normalisation, per series:** ĉ_φ = c_φ / ((1/64) Σ_ψ c_ψ); x_t = r̃_t / ĉ_{φ(t)} | no | — | the phase modulation m_t, whose amplitude is act_a (§3.1); **not** the scalar level σ_k | U-act destroyed **by design**; U-vol and U-event kept [T] |
| M6 | **M5 then M1, per series:** x_t = y_t / RMS(y), with y the M5 output | no | — | σ_k and the phase modulation | U-act destroyed by design; the frontier point for asset hiding [T] |

### 3.1 What M1 and M5 remove, derived from the generator (review R1-01)
Write c_φ = σ_k · m̂_φ, where m̂_φ is the sample RMS of {m_t z_t + μ_a/σ_k : φ(t) = φ}.

**M5, exact algebraic property.** For every phase φ:
RMS{x_t : φ(t) = φ} = c_φ / ĉ_φ = (1/64) Σ_ψ c_ψ.
The per-phase RMS of the output is **identical across all 64 phases, exactly** (not only in expectation). So the
phase-RMS profile of the output carries **no** information about act_a.

**What M5 does not remove:**
1. **The scalar level.** (1/64) Σ_ψ c_ψ = σ_k · (1/64) Σ_ψ m̂_ψ, and E[m̂_ψ] ≈ m_ψ · E[RMS of 8 N(0,1)]. Since
   (1/64) Σ m_ψ = 1, this scalar is ≈ σ_k × a constant that does not depend on act_a, to first order. So M5 keeps
   σ_k [T]. This is why M6 adds M1.
2. **Higher-order and within-phase information.** M5 equalises second moments per phase only. Any act_a information
   in other statistics is not removed by construction. Example: the dependence between ĉ_φ (estimated from 8 values)
   and the values it divides. In the Gaussian generator such residual information is expected to be small [T]; it is
   **measured, not assumed** [H2], by A7 and A8.
3. **Phase alignment.** M5 does not hide where the cycle is. The phase is public (it is the time index), and only the
   amplitude carries identity (F3).

**v0.1 wording withdrawn.** v0.1 called M5 "deseasonalisation" and implied that removing the cycle equals removing
act_a. The exact statement is: M5 makes the per-phase RMS flat; it removes the second-moment phase modulation, whose
amplitude is act_a. Removing the cycle is equivalent to removing act_a **only in the second-moment sense** above.

**M1, exact property.** RMS(x) = 1 for every series, exactly. Hence no scalar level survives in the overall second
moment. The phase modulation is untouched: x_t = r̃_t / RMS(r̃), and the ratio c_φ / c_ψ is unchanged, so act_a
stays visible [T]. Residual σ_k information through other channels (for example tick discreteness relative to
volatility: r̃ is computed from prices rounded to the tick, so a low σ_k·P/tick leaves visible discreteness) is
**not** removed [T] and is measured [H3].

**Scope consequences (R1-03).** Per-series normalisation gives every member of a family RMS = 1 separately, so no
member-to-member level ratio is released. A family-joint normalisation would release those ratios, which are noise
around 1 within one class. It is not used, so its information content is not at stake. Pooling (S-pool) still lets
the attacker average the act_a evidence (M1) or residual evidence (M5, M6) over g series. This is measured at g = 4
and 16 (F7, C-S3).

**Not included (with reasons):**
- **Asset mixtures** would change the research object.
- **Additive noise dithering** would degrade U-vol and U-event at any noise level that masks act_a. It is
  dominated by M5 on paper [T]. It can be added in a later version only through a recorded design change.
- **Time-warping** hides the phase, not the amplitude act_a, which F3 shows carries the identity.

**Ledger:** Δ is moved out of the public ledger in every RIP-3 candidate (F4). The candidates are measured with
Δ hidden. One control cell, M1 with Δ shown, keeps the RIP-2 comparison.

## 4. Measurements

### 4.1 Re-identification (asset, period, joint; chance 0.25 / 0.25 / 0.0625)
**Attackers, all frozen before the run:**
- **A1, A2, A3** in S-ind and **A4a, A4b** in S-pool, as in RIP-2.
- **A6 (model likelihood)** where it is tractable, derived per transform before the build:
  - B-LR, B-AF, B-LRS: the RIP-2 A6 (exact level_residual likelihood, addendum A1).
  - M2: the log-returns likelihood with κ integrated over its prior, by quadrature on ln κ.
  - M1: the scale-invariant likelihood. The data are invariant to scale, so the likelihood of the maximal
    invariant is ∫ p(x/λ)·λ^{−n} dλ/λ, by quadrature on ln λ; with a flat prior on ln λ this equals the M2
    likelihood as w → ∞.
  - M5, M6: phase-profile normalisation by the series' own profile is nonlinear, and **no exact likelihood is
    claimed**.
- **A7, the simulation-based (synthetic-likelihood) attacker, for every candidate:**
  - Per class, simulate 2000 development series with the transform, using the attacker's own draws of every
    secret.
  - Compute a fixed summary vector:
    - the 38 reid.features;
    - the 64 phase-RMS values of the transformed series;
    - its log-RMS;
    - the lag-1 to lag-5 autocorrelations of x².
  - Fit a Gaussian per class (Ledoit–Wolf shrinkage) and classify by the maximum log-density.
  - A7 is the model-aware attacker that makes candidates comparable when A6 is not available. It is never used
    alone (A8, below).
- **A8, a second, non-parametric classifier on the same feature space (review R1-02; scope R2-01):** k-nearest
  neighbours on the same frozen summary vector as A7.
  - **S-ind:** each summary component is z-scored with development means and standard deviations. Euclidean
    distance, **k = 15**, majority vote. Ties go to the smallest summed distance, then to the lowest class index.
  - **S-pool:** the family summary is the mean of the members' summaries; then the same k-NN at family level, with
    development families of the same g.
  - Every A8 setting is fixed here, including k = 15 (no second k in the primary design; R2 decision). Nothing is
    tuned on evaluation data.
  - A8 is built in each world from that world's development simulations (W1 and W2), as A7.
- **Maximum over attackers.** A1–A4, A6 (where tractable), A7 and A8 all enter the maximum-over-attackers identity
  (C-A1).
- **Scope of the identity measurement for M3–M6 (review R2-01).** A7 and A8 read the **same** 108-component
  summary vector (38 + 64 + 1 + 5). A8 adds **classifier diversity** (a non-parametric decision rule beside a
  Gaussian one); it adds **no feature-space coverage**. A1–A4 read the 38 reid.features, which are a subset of
  that vector. For M3–M6, where no A6 exists, every identity number is therefore **bounded by this attacker family
  and this feature representation**:
  - it is a measured accuracy of these attackers, i.e. a **lower bound** on what an attacker with other features
    or other models could reach;
  - information that the 108 summaries do not capture is **not measured** and is **not claimed absent**;
  - A7 and A8 together do **not** establish the strongest possible attacker, and do **not** establish an
    exhaustive measure of identity leakage.
  This sentence is attached to every M3–M6 identity result (C-A5).
- **Validation of the attackers used for M3–M6 (C-V2, §7; changed in v0.5 by DCR-01, see §14):** on B-LR in W1, the
  stronger of A7 and A8 (x4), re-selected inside every bootstrap sample, must not be less accurate than A6, by the
  rule of §14.2. B-AF is computed the same way and **reported, not gating**; A7's results on B-AF stay published. If
  C-V2 fails, the candidates without a tractable A6 (M3 to M6) are reported as **not assessable**.
  A8 is also run on the baselines and reported beside A6 and A7. Passing the baseline validation does **not**
  establish adequacy on nonlinear transforms; that limit is stated with every M3–M6 result, together with the
  learning-curve flag (C-O3), which is applied to A7 and A8.

**Scenarios and units:** as RIP-2 (S-ind 25 families per class; g = 4 with 10; g = 16 with 5); unit = family;
stratified paired family bootstrap, B = 2000.

### 4.2 Research utility
- **U-vol\*** (unit-free, review-driven change from RIP-2 U-vol):
  - Truth: v_t = sqrt(mean over the window of E[r̃_u² | P_{u−1}]), the exact RIP-2 truth for log returns
    (derivation §3, row log_returns). It is in return units for every candidate, because all candidates are
    built on r̃.
  - Estimate: sqrt(mean of x_u²) over the same window.
  - Statistic: Spearman ρ, invariant to any monotone rescaling. For B-LR, U-vol\* equals RIP-2's U-vol for
    log_returns.
  - For B-AF and B-LRS, which are not built on r̃, the RIP-2 U-vol values are quoted as measured and marked as a
    different definition.
- **U-act:** as RIP-2: detection of the period-64 cycle on s_t = x_t², with power and null false alarm.
- **U-event:** as RIP-2: CUSUM on s_t = x_t², with flag, success and null flag rate.
- **U-ratio (new; reference corrected in v0.4, review R3-01).** Option (b) of R3: the estimator is unchanged and
  the reference is derived exactly, drift included.
  - **Estimator:** R̂ = mean(s, τ … τ+63) / mean(s, τ−64 … τ−1), with s_t = x_t² and the RIP-2 index convention of
    U-event.
  - **Reference, per family (exact):** R\* = Σ_{u ∈ post} q_u / Σ_{u ∈ pre} q_u over the same two windows, where
    q_u = E[r̃_u² | P_{u−1}] is the exact U-vol\* truth of the planted series: in W1 the RIP-2 exact construction,
    whose tick probabilities already contain μ_a (RIP2_UVOL_DERIVATION.md); in W2 the formula of §4.3. R\* is in
    return units. It is the reference for every candidate, as U-vol\*'s truth is: a scalar rescaling (M1, M2)
    leaves R̂ unchanged, and the loss of nonlinear transforms is what U-ratio measures.
  - **Statistic:** median over planted families of |ln(R̂ / R\*)|.
  - **Why not 4.** The planted shift doubles only the stochastic part, r_t = μ_a + m_t·f_t·ε_t. Each window spans
    one full 64-step cycle, where Σ sin = 0 and Σ sin² = 32, so Σ m_t² = 64·(1 + act_a²/2) exactly. For the latent
    (unrounded) returns this gives the class value
    R_k = (μ_a² + 4·σ_k²·(1 + act_a²/2)) / (μ_a² + σ_k²·(1 + act_a²/2)),
    which equals 4 only when μ_a = 0 (it holds in W2 too, unconditionally, because E ε² = σ_k² and ε is independent
    of m and f). R_k is reported beside R\* as a sanity value only. The observed returns add the rounding, which
    R\* contains and R_k does not. **4 is not used as a target anywhere.**
- **Worlds:** planted and null, as RIP-2 IC-02 (shift world, cycle world; null: no shift, act = 0).

### 4.3 A second world (attacker-model and utility robustness; L1)
- **W2 generator, exact specification (review R2-02).** For one series of class (a, p), with σ_k = vol_a·volx_p,
  α = 0.08, β = 0.90, ν = 5, burn-in B₀ = 500, and the same step index t = 0 … n−1 as reid.simulate:
  - **Innovations.** z_t = T_t·sqrt((ν − 2)/ν), with T_t = G_t / sqrt(Q_t/ν), G_t ~ N(0, 1), Q_t ~ χ²_ν, all
    independent. Hence E z_t = 0 and **Var z_t = 1 exactly** (Var T = ν/(ν − 2)). Draw order per step: G_t
    (random.gauss(0, 1)), then Q_t (random.gammavariate(ν/2, 2)), from the series' own random.Random stream.
  - **Variance recursion.** h_t = ω_k + α·ε²_{t−1} + β·h_{t−1}, ε_t = sqrt(h_t)·z_t.
  - **ω_k.** ω_k = σ_k²·(1 − α − β) = 0.02·σ_k². Then the stationary unconditional variance E h = E ε² =
    ω_k/(1 − α − β) = σ_k² exactly, so W1 and W2 have the same class levels.
  - **Initial conditions and burn-in.** Start from h = σ_k² and ε = 0. Run the recursion for B₀ = 500 steps with
    their own (G, Q) draws, taken first from the stream; nothing of the burn-in is released or priced. The series
    continues from the burn-in's last (h, ε): h_0 = ω_k + α·ε²_{B₀−1} + β·h_{B₀−1}. The remaining weight of the
    start value is (α + β)^500 = 0.98^500 ≈ 4·10⁻⁵.
  - **Returns and prices.** r_t = μ_a + m_t·ε_t·f_t, with m_t = 1 + act_a·sin(2πt/64) as in W1 and f_t = 2 for
    t ≥ τ in the shift world, else 1 (the RIP-2 planted shift, rip2.path_from_normals). The activity pattern and the
    shift act **after** the GARCH recursion, which runs on ε only; so the recursion does not depend on act_a or τ.
    Prices exactly as reid.simulate: start from L_a·growth_p, P_t = P_{t−1}·e^{r_t}, observed
    round(round(P_t/tick)·tick, 10).
  - **Paired worlds.** As RIP-2 IC-02: the null worlds reuse the same (G, Q) draws with f ≡ 1 (U-vol, U-event)
    or with act_a = 0 (U-act).
  - **U-vol\* truth in W2 (exact formula, review R3-02).** Given the latent P = P_{u−1}, the observed
    P̃ = P̃_{u−1} and the latent h_u, the step is r_u = μ_a + b_u·y_u with y_u ~ t_ν (standard Student-t),
    b_u = c·s_u, c = sqrt((ν − 2)/ν), s_u = m_u·f_u·sqrt(h_u). **The location μ_a enters every bound**, as μ does in
    the Gaussian case of RIP2_UVOL_DERIVATION.md:
    - p_j = F_ν((ln((j + ½)·tick/P) − μ_a)/b_u) − F_ν((ln((j − ½)·tick/P) − μ_a)/b_u), F_ν the t_ν CDF;
    - q_u = Σ_j p_j·ln(j·tick/P̃)², over j ≥ 1.
    - **Truncation, centred on the shifted distribution.** The exact sum runs over the j whose cells meet
      y ∈ [−K, K], i.e. prices P·e^{μ_a ± K·b_u}; the end cells are clipped at ±K. Start K = 50.
    - **Tails |y| > K, in closed form** (rounding neglected there). With A = μ_a + ln(P/P̃) and
      x = K²/(ν + K²): tail term = A²·T₀ + b_u²·T₂, where T₀ = P(|y| > K) = 1 − I_x(½, ν/2) and
      T₂ = E[y²; |y| > K] = (ν/(ν − 2))·(1 − I_x(3/2, ν/2 − 1)), I the regularised incomplete beta. The cross term
      vanishes because both tails are included. (These identities were checked against numerical quadrature at
      design time, as arithmetic only; nothing was simulated.)
    - **Error bound, computed per step:**
      E_u = δ_f·(2·(|A|·T₀ + b_u·T₁) + δ_f·T₀) + F_ν(y_f)·(L² + 2A²) + 2·b_u²·U₂(y_f), where:
      - T₁ = E[|y|; |y| > K] = 2·((ν + K²)/(ν − 1))·f_ν(K), f_ν the t_ν density;
      - the price floor is P_f = 100·tick, and δ_f = −ln(1 − 1/199) is the largest log-rounding error above it;
      - y_f = min(−K, (ln(P_f/P) − μ_a)/b_u): only the part of the lower tail below the floor (the central sum is
        exact wherever it reaches);
      - U₂(y_f) = E[y²; y < y_f] = (ν/(ν − 2))·(1 − I_{x_f}(3/2, ν/2 − 1))/2, with x_f = y_f²/(ν + y_f²);
      - L = ln(P̃/tick) bounds |ln(j·tick/P̃)| for 1 ≤ j ≤ 100.
      The first term bounds the rounding neglected in the tails above the floor, through
      |(ℓ + δ)² − ℓ²| ≤ |δ|·(2|ℓ| + |δ|); the other two bound the whole below-floor region, true and closed-form
      parts together.
    - **Acceptance, fixed now:** E_u ≤ 10⁻⁶·q_u. If not met, K is doubled, up to K = 400. A step that still fails is
      counted, its family's W2 U-vol\* is flagged, and the count is reported. The event j = 0 (an observed price of
      0, where ln is undefined) has probability below F_ν(y_f); if the generator ever produces it, that cell fails
      C-V1. It is not resampled.
    - The RIP-2 Monte Carlo check is repeated for W2 at BUILD, with the same acceptance rule, before any W2 utility
      number is used.
  - **A known property, stated not hidden.** With ν = 5 the kurtosis of z is 3 + 6/(ν − 4) = 9, and
    β² + 2αβ + 9α² = 1.0116 > 1, so ε has **no finite unconditional fourth moment**. Statistics of x² (the ACF of x²
    in the summary, the CUSUM on s = x²) are therefore heavy-tailed in W2. This is part of the misspecification
    being tested, not a defect; no W2 claim relies on a converging fourth moment.
- A6 stays the misspecified Gaussian model of W1. This measures the effect of attacker misspecification.
- A7 and A8 are rebuilt on W2 development simulations.
- Every candidate is measured in W1 and W2. A conclusion that holds in W1 only is reported as W1-only.
- **Scope of W2 (review R1-04):** W2 changes the volatility process and the tails only. The activity pattern (one
  sinusoid, the same act_a values) is **unchanged**. W2 therefore tests robustness to **volatility-model
  misspecification**, and nothing about the activity pattern. A robustness claim about other activity shapes would
  need a further world, which is not part of RIP-3 v0.2.

## 5. Comparison matrix (to be filled by the run; the structure is fixed now)
For each candidate × world × scenario:

| Column | Content |
|---|---|
| I_asset, I_period, I_joint | the **maximum over attackers** of the accuracy, with the 95 % interval of that attacker |
| attacker coverage | A6 exact / A7 only / feature attackers only |
| saturation | learning-curve flag, §6 C-O3 |
| U-vol\* planted / null | mean ρ [CI] |
| U-act | power / false alarm |
| U-event | success / flag planted / flag null |
| U-ratio | median |ln(R̂ / R\*)| (R\* exact, per family, §4.2) |
| class | **P** (U-act preserving: power ≥ the §7.2 floor) or **S** (U-act sacrificing) |
| frontier | Pareto status **within its class only** (identity lower and utility not lower); P and S are never ranked together |

**Expected matrix [T], to be confronted with the measurement, not reported as a result:**

| Candidate | asset | period | U-vol\* | U-act | U-event | U-ratio |
|---|---|---|---|---|---|---|
| B-LR | ≈ 0.98 [M] | ≈ 0.98 [M] | 0.894 [M] | 0.818 [M] | 0.68 [M] | kept |
| M1 | ≈ only-act level (RIP-2: asset 0.62) | near chance (only σ separates periods) | = B-LR | = B-LR | = B-LR | kept |
| M2 (w = 4) | between M1 and B-LR | lower than B-LR | = B-LR | = B-LR | = B-LR | kept |
| M3 (W = 32) | lower | near chance | lower | much lower | lower | lost |
| M4 | ≈ M1 or lower | near chance | lower | partly kept | lower | lost |
| M5 | ≈ only-σ level (RIP-2: asset 0.69) | ≈ only-σ level (0.68) | ≈ B-LR | ≈ false-alarm level (by design) | ≈ B-LR | kept |
| M6 | lower than M1 and M5; residual unknown [H2, H3] | near chance | ≈ B-LR | ≈ false-alarm level (by design) | ≈ B-LR | kept |

## 6. Controls

### Overfitting and selection
- **C-O1 — three seed sets.** Development data (seeds 6101 +) for any attacker training. Evaluation data
  (6201 +) for the frontier and the selection. A **confirmatory** set (6301 +), used once, only for the
  recommended candidate and its nearest competitor. This guards against a winner's curse.
- **C-O2 — fixed candidate set and grids** (§3). The selection rule (§7) is fixed now. No parameter is tuned on
  evaluation data.
- **C-O3 — attacker saturation.** A2, A7 and A8 are built at development sizes ×1, ×2 and ×4 (2000, 4000 and
  8000 series per class in S-ind; the corresponding development families in S-pool):
  - A2 and A7: training-set size;
  - **A8 (review R2-03): reference-set size.** The neighbours are searched in the ×1, ×2 or ×4 reference set, and
    the z-scoring statistics are recomputed from that same set. k stays 15 at every size: k is fixed, and only the
    reference density changes.
  The same evaluation units are scored at each size. If the identity accuracy at ×4 is still above ×2 beyond the
  paired interval, the cell is flagged **unsaturated** for that attacker. Its identity number is then reported as a
  **lower bound**, never as resistance.

### Attacker-model limits
- **C-A1 — the maximum over attackers.** The identity of a candidate is the maximum over all attackers. A low
  number from one attacker is never quoted alone.
- **C-A2 — A7 validation** (§4.1); a candidate that fails it is not assessable.
- **C-A3 — the W2 misspecification world** (§4.3).
- **C-A4 — Kerckhoffs.** Every secret's distribution is known to the attackers, as in RIP-1 and RIP-2.
- **C-A5 — feature-space bound (R2-01).** Every M3–M6 identity number carries the §4.1 scope sentence: bounded by
  A1–A4, A7 and A8 on the 108-component summary; not the strongest possible attacker; not exhaustive.

### Misleading security claims
- **C-S1 — no candidate is called "secure", "anonymous" or "safe"** in any RIP-3 document. Results are stated as
  accuracies with intervals under named attackers and worlds.
- **C-S2 — a reduction is stated only as a paired difference** against B-LR, with its family-bootstrap
  interval.
- **C-S3 — pooling.** A result for single series does not stand for families: the g = 16 result is always shown
  beside it (F7).
- **C-S4 — the threshold.** CS-01-04 is not set by RIP-3. RIP-3 supplies the frontier as evidence for the
  founder's decision.

### Reproducibility (L4)
- **C-R1:** per-unit predictions and per-family utility values are stored, so every number can be recomputed by
  an independent re-score script.
- **C-R2:** seeds, code hashes and a partial-reproduction script, as in RIP-2.

## 7. Acceptance criteria and failure conditions (fixed before any build)

### 7.1 Validity gates (all must pass, or the run is reported as invalid for the affected cells)
- **C-V1:** the world generator equals the frozen reid.simulate (W1, bit-identical). W2 is checked by moments
  against its specification.
- **C-V2 (v0.5, DCR-01):** the rule of §14.2 on B-LR, W1, every scenario and target; B-AF reported, not gating.
- **C-V3:** for B-LR and B-AF, the RIP-3 numbers reproduce the RIP-2 numbers within their intervals. This is a
  pipeline check, on new seeds.
- **C-V4:** the utility nulls. The U-act null false alarm is ≤ 0.05 + 0.02 for B-LR. The U-event null flag is
  reported against its RIP-2 value 0.072 (F6), not against 0.05.

### 7.2 Utility floors — PROPOSED values (relative to B-LR in the same world)
**Status: PROPOSED, not confirmed.** The founder must confirm or change these values **before** any BUILD is
authorised. They are not a re-identification threshold; CS-01-04 is untouched.
| Measure | Floor |
|---|---|
| U-vol\* planted | ≥ 0.95 × B-LR |
| U-act | power ≥ 0.90 × B-LR, **or** the candidate is declared U-act-sacrificing |
| U-act false alarm | ≤ B-LR + 0.02 |
| U-event success | ≥ 0.90 × B-LR |
| U-event null flag | ≤ B-LR + 0.02 |
| U-ratio | median error ≤ B-LR + 0.05 |

### 7.3 Identity reduction (no threshold; relative)
A candidate **reduces identity** for a target (asset, period or joint) if the **lower** end of the 95 % interval of
the paired difference B-LR − candidate, for the maximum-attacker identity, is above 0. That is, the reduction is
positive, in W1 and in W2, in S-ind **and** g = 16. The size of the reduction is reported. "Near chance" is never
used as a pass criterion.

### 7.4 Selection rule for the recommended design (applied to the evaluation set, then confirmed once)
Two classes, two frontiers, two possible recommendations (review R1-05):
- **Class P**: U-act preserving, all §7.2 floors including the U-act power floor.
- **Class S**: U-act sacrificing; all §7.2 floors **except** the U-act power floor, which is reported, not waived
  silently.

The rule:
1. Keep, in each class separately, the candidates that pass every validity gate and every floor of that class.
2. In each class, choose the one with the largest joint-identity reduction in g = 16 (the operational case, F7).
   Ties go to the simplest method (fewer secrets, then fewer parameters).
3. On the confirmatory set, each class's choice must reproduce its reduction (paired interval above 0) and its
   floors.
4. The two classes are **never compared** as if U-act loss were free. Whether research can give up U-act is a
   founder decision.

### 7.5 Failure conditions (each one is reported as a negative result, not repaired after the fact)
- **FC-1:** in a class, no candidate passes that class's floors **and** reduces identity. Result: no acceptable
  trade-off in that class under these attackers and worlds. Reported per class.
- **FC-2:** the reductions hold in W1 but not in W2. Result: the conclusion is model-dependent.
- **FC-3:** the chosen candidate fails confirmation. Result: no recommendation from RIP-3.
- **FC-4:** C-V2 fails. Result: the nonlinear candidates (M3 to M6) are not assessable.
- **FC-6:** for a candidate, A8 exceeds A7 beyond the interval. Result: A7 is inadequate there; the candidate's
  identity is the A8 value, flagged "attacker-sensitive", and no claim rests on A7 alone.
- **FC-5:** the best candidate is unsaturated (C-O3). Result: its identity numbers are lower bounds, and no
  resistance is stated.

## 8. Recommended design and its justification [T]
**Class P recommendation: M1 (per-series global standardisation of log returns), with M2 (secret scale, w = 4) as
its secret counterpart. Class S candidate: M6. The two are kept separate (§7.4).** Δ is moved out of the public ledger in all of them.

**Why M1 first:**
- F3 locates a large share of the identity in the absolute volatility level σ_k, and in the returns
  representations σ_k alone gives joint 0.68.
- Dividing by the series' own RMS removes that absolute level without touching the relative structure. The three
  RIP-2 utility measures are scale-invariant (Spearman, a relative spectral peak, a normalised CUSUM), so the
  expected utility cost is **zero** on U-vol\*, U-act and U-event. U-ratio is also kept, because a ratio is
  scale-free.
- M1 needs no secret and no custody parameter. It removes a channel instead of hiding it, so it does not depend on
  a secret staying secret.
- Its exact likelihood attacker is tractable (scale-invariant likelihood), so its identity can be measured with
  the strongest available attacker, not only with A7.

**What M1 is expected NOT to do:**
- It leaves the phase modulation, and therefore a large part of the asset identity (RIP-2 only-act 0.62). Removing
  that modulation in the second-moment sense (M5, M6; §3.1) means removing the cycle that U-act measures, which is the research structure U-act measures. **[H1] states this conflict.** If
  it holds, the frontier has two branches: keep the cycle and accept the asset identity, or remove the cycle and
  lose U-act. RIP-3 is designed to measure both branches. Which branch research can afford is a decision for the
  founder, not for the design.
- The period identity is expected to fall towards chance under M1, since only σ_k (via volx) separates periods in
  returns [T]. This is the part most likely to be gained at no utility cost.

**Why M2 is kept beside M1:** it tests whether a secret scale buys anything that deterministic standardisation does
not. Under Kerckhoffs, M2 should approach M1 from above as w grows [T].

**Why M3 and M4 are kept even though they are expected to be dominated:** without them, the claim that cheaper
nonlinear normalisations cost utility would be an untested assumption. They are cheap to include.

## 9. Stages after this design (each needs its own explicit founder authorisation)
1. Independent review of this design, then freeze.
2. BUILD: code and tests. The A6 likelihoods for M1 and M2 are derived and verified numerically (as in RIP-2
   U-vol), and A7 is validated on the baselines with **development** seeds only. Then a build review.
3. RUN: evaluation set, then the single confirmatory step.
4. Result audit.

## 10. Open points
None. R2 decided the two v0.2 points: W2 stays limited to volatility-model misspecification (no third world in
RIP-3), and A8 keeps k = 15 with no second k in the primary design.

## 11. Change log v0.1 → v0.2 (review R1)
| Review item | Resolution |
|---|---|
| MAJOR-1 M5 / act_a | §3.0–3.1: exact generator decomposition (σ_k scalar × m_t phase modulation, with mean m_φ = 1). M5 redefined as phase-profile normalisation, with its exact property (flat per-phase RMS, identically). What M5 does not remove: the scalar level (hence M6 = M5 then M1), higher-order residuals [H2], and phase alignment. The v0.1 wording equating cycle removal with act_a removal is withdrawn. |
| MAJOR-2 A7 sole attacker | §4.1: A8 (k-NN, k = 15, z-scored frozen summary, family-mean summary in S-pool, fixed tie rule) added to the maximum over attackers; run on the baselines too; learning curves for A7 and A8; FC-6 when A8 beats A7. |
| MAJOR-3 S-pool scope | §3.0: every normalisation is per series (M1, M3, M4, M5, M6), never family-joint; §3.1 states what each scope releases. |
| MINOR-4 W2 | §4.3: W2's claim narrowed to volatility-model misspecification; the activity pattern is unchanged. |
| MINOR-5 frontiers | §5, §7.4: class P and class S, separate frontiers, separate choices; never ranked together; FC-1 per class. |
| MINOR-6 floors | §7.2: PROPOSED until the founder confirms them before any BUILD; CS-01-04 untouched. |

## 12. Change log v0.2 → v0.3 (review R2)
| Review item | Resolution |
|---|---|
| R2-01 MAJOR A7/A8 share one feature space | §4.1 A8 renamed a second classifier on the same feature space; scope paragraph: identity for M3–M6 bounded by the attacker family and the 108-component representation, a lower bound, not strongest and not exhaustive; C-A5 attaches this to every M3–M6 result. |
| R2-02 MAJOR W2 specification | §4.3: standardised Student-t (Var 1 exactly) with draw order; ω_k = 0.02·σ_k²; start h = σ_k², ε = 0; burn-in 500 steps, discarded; activity and shift applied after the recursion; prices and rounding as reid.simulate; paired null worlds; W2 U-vol\* truth; infinite fourth moment stated. |
| R2-03 MINOR A8 saturation | §6 C-O3: A8 reference-set size ×1/×2/×4 with z-scoring recomputed per size and k fixed at 15; same flag rule as A2 and A7. |
| R2 open-point decisions | §10: W2 narrowed scope kept; A8 k = 15 only. |
| Self-found S2-01 | §4.2 U-ratio: the planted shift doubles the step, so the variance factor is 4, not 2; the error measure is now median |log(ratio/4)|. |
| Self-found S2-02 | A8 is rebuilt per world (W1, W2), as A7. |

## 13. Change log v0.3 → v0.4 (review R3)
| Review item | Resolution |
|---|---|
| R3-01 MAJOR U-ratio target with drift | §4.2: option (b). Estimator unchanged; the reference is the exact per-family R\* = Σ_post q_u / Σ_pre q_u from the U-vol\* truth (μ_a and rounding included, W1 and W2); statistic median |ln(R̂/R\*)|. The latent class value R_k = (μ_a² + 4σ_k²(1 + act_a²/2))/(μ_a² + σ_k²(1 + act_a²/2)) is derived and reported as a sanity value; 4 is no longer a target. This supersedes the §12 S2-01 wording. |
| R3-02 MAJOR W2 density without μ_a | §4.3: exact W2 transition r_u = μ_a + c·s_u·y_u, y_u ~ t_ν; μ_a in every CDF bound; truncation centred on μ_a (y ∈ [−K, K], K = 50 doubling to 400); closed-form tails with location A = μ_a + ln(P/P̃); per-step error bound with acceptance 10⁻⁶·q_u; the j = 0 event is a C-V1 failure, not resampled. |

## 14. DCR-01 — the C-V2 gate (v0.5 only; not applied to v0.4)

### 14.1 Why, and disclosure
The BUILD-stage check B3 (development seeds 6101 / 6102; FL-030) found that A7 does not reach A6 on B-AF (asset
0.65 against 0.93 in S-ind), while A8 does, and that the v0.4 rule (A7 within A6's percentile interval) fails on
B-LR g4 because that interval is degenerate at 1.0. **This request was formulated after seeing those development
results.** No evaluation (6201) or confirmatory (6301) data existed or were used. Nothing in v0.4 was changed.

### 14.2 The rule
- **Data:** B-LR, W1, scenarios S-ind, g4, g16; targets asset, period, joint: m = 9 cells, all gating.
- **Resampling:** stratified (by class) paired bootstrap of the family units; one index set per sample, shared by A6,
  A7 (x4) and A8 (x4) and by the three targets of the scenario; B = 2000; numpy default_rng(SEED), SEED fixed with the
  run's bootstrap seeds (development study: 6119; evaluation: 6299 + 17; confirmation: 6399 + 17).
- **Statistic per sample b and cell:** D_b = mean(A6)_b − max(mean(A7)_b, mean(A8)_b). The stronger alternative is
  re-selected inside every sample; nothing is fixed from the original means.
- **Interval:** one-sided percentile upper bound UB = the (1 − α/m) quantile of D_b, α = 0.05, m = 9 (Bonferroni):
  the nine bounds hold simultaneously with probability ≥ 95 %.
- **Multiplicity:** every gating cell is tested and reported; C-V2 passes only if **all nine** pass (no selection of
  passing cells). B-AF's nine cells are computed with the same procedure and published.
- **R0 (strict; the founder's recommended rule):** pass iff UB ≤ 0 in every gating cell. Meaning: with familywise
  confidence ≥ 95 %, the strongest alternative attacker is not less accurate than the exact-likelihood attacker A6.

### 14.3 What R0 implies, measured on development data (information; `docs/results/rip3_build/DCR01_study_dev.json`)
| Baseline | Scenario | Target | A6 | A7 x4 | A8 x4 | UB (one-sided, Bonferroni) | R0 |
|---|---|---|---|---|---|---|---|
| B-LR | ind | asset | 0.9875 | 0.9775 | 0.9550 | 0.0300 | FAIL |
| B-LR | ind | period | 0.9875 | 0.9775 | 0.9150 | 0.0300 | FAIL |
| B-LR | ind | joint | 0.9875 | 0.9750 | 0.9150 | 0.0350 | FAIL |
| B-LR | g4 | asset | 1.0000 | 0.9938 | 1.0000 | 0.0000 | pass |
| B-LR | g4 | period | 1.0000 | 0.9938 | 1.0000 | 0.0000 | pass |
| B-LR | g4 | joint | 1.0000 | 0.9938 | 1.0000 | 0.0000 | pass |
| B-LR | g16 | asset | 1.0000 | 1.0000 | 1.0000 | 0.0000 | pass |
| B-LR | g16 | period | 1.0000 | 1.0000 | 1.0000 | 0.0000 | pass |
| B-LR | g16 | joint | 1.0000 | 1.0000 | 1.0000 | 0.0000 | pass |
| B-AF | ind | asset | 0.9275 | 0.6475 | 0.9100 | 0.0597 | FAIL |
| B-AF | ind | period | 0.3400 | 0.3875 | 0.3725 | 0.0125 | FAIL |
| B-AF | ind | joint | 0.3125 | 0.2750 | 0.3550 | 0.0275 | FAIL |
| B-AF | g4 | asset | 0.9750 | 0.6188 | 0.9688 | 0.0556 | FAIL |
| B-AF | g4 | period | 0.3875 | 0.3438 | 0.4062 | 0.1063 | FAIL |
| B-AF | g4 | joint | 0.3812 | 0.2188 | 0.4000 | 0.1063 | FAIL |
| B-AF | g16 | asset | 0.9500 | 0.6500 | 1.0000 | 0.0000 | pass |
| B-AF | g16 | period | 0.4125 | 0.3625 | 0.4250 | 0.1375 | FAIL |
| B-AF | g16 | joint | 0.4000 | 0.2500 | 0.4250 | 0.1375 | FAIL |

R0 fails on B-LR in S-ind (UB 0.030–0.035). This is structural, not noise: in W1 A6 is the exact likelihood of the
true model, so its expected accuracy is the Bayes-optimal accuracy; any other attacker has D ≥ 0 in expectation, and
UB ≤ 0 can only be shown where all attackers are at the ceiling (g4, g16). **Under R0, C-V2 is expected to fail in
the RUN, so M3–M6 would be «not assessable» (FC-4)**, the same consequence as v0.4.

### 14.4 The alternative that needs a founder decision: non-inferiority with a margin
- **R-NI(δ):** pass iff UB ≤ δ in every gating cell. Meaning: with familywise confidence ≥ 95 %, the strongest
  alternative attacker is at most δ (absolute accuracy) below A6, on returns, in each cell. A pass does **not** show
  that A7/A8 are as strong as A6, does not cover features outside the 108 summaries (C-A5), and says nothing about
  B-AF or about nonlinear transforms beyond B-LR.
- **δ is a threshold, so it is the founder's to set,** before any RUN. The smallest δ that would pass on these
  development data is 0.035; it is given as information only, and
  any δ chosen now is chosen after seeing development data (disclosed).
- Not proposed: "the interval contains 0" as proof of equivalence (it is not one).

### 14.5 Decision requested (one, after independent review)
(a) keep v0.4 (no DCR-01): FC-4 expected; (b) adopt v0.5 with R0: FC-4 still expected (§14.3); (c) adopt v0.5 with
R-NI(δ) and a founder-set δ. Until a decision, v0.4 governs and no code implements v0.5.
