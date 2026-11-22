# RIP-2 — leakage diagnosis — design v0.7 — DRAFT FOR REVIEW (not frozen, nothing built or run)

v0.2 answered review R1; v0.3 answered R2; v0.4 answered R3; v0.5 answered R4; v0.6 answered R5; v0.7 answers R6 (register: `docs/audit/RIP_register.md`). Scope unchanged.

Programme: OD-S9-07 (`docs/research/REID_PROGRAMME.md` §4). Builds on the RIP-1 result (`docs/results/RIP-1_REPORT.md`)
and its audit (R1 on the result, `docs/audit/RIP_register.md`). SYNTHETIC ONLY. Opens no gate; selects no
alternative; no threshold (CS-01-04 stays with the founder).

## 1. Question
RIP-1 showed *that* the current representations are identifiable. RIP-2 asks **which mathematical information
left in each representation carries the identity, and how much of it each step removes**:
- the transform itself (representation vs raw prices);
- the secret parameters (public canonical vs Vault-style secret draws);
- Δ in the ledger (shown vs hidden).

It also measures the **research-utility baseline** of the current transforms, so that RIP-3 can price every
alternative against it. RIP-2 is diagnostic: none of its results is used to pick or tune a transform.

## 2. What RIP-2 does not test
Custody/Vault isolation was tested in RIP-1 (H5). RIP-2 runs in the research harness with registered public seeds;
the secret parameters are drawn from the frozen RIP-1 table (§3.3 of the programme) with a seeded generator. This is
declared: RIP-2 measures information content, not secrecy of operational parameters.

## 3. Data (paired)
- World, classes and sizes as RIP-1: 4 assets × 4 periods; S-ind 25 families per class (400 units); S-pool g = 4
  with 10 families per class (160 units); g = 16 with 5 per class (80 units); n = 512.
- **Pairing (audit condition 2).** One set of price paths and one set of secret draws per family is generated once
  and reused in every condition. Conditions differ only in what is applied to the same paths.
- Development data (training the attackers) and evaluation data come from separate registered seeds. The
  attackers are trained separately for each condition, on development data produced under that condition.
- Unit of analysis = family (audit condition 3). In S-pool, the g series of a family are never counted as
  separate units.

## 4. Factors
**T — transform and secrecy**, per representation:
- C0: raw prices on the tick grid. No representation, no secret. One cell, shared by all representations.
- C1 (**asset-conditioned public canonical**, review R1-01): the representation with fixed, public parameters,
  c = 0, a = 1, b = 0, and m = 100 × tick_asset, the second value of the asset's own m set and a member of it.
  The values are in the frozen table in §4a.
  log_returns and volatility_time have no parameter. C1 is **not** one uniform transform for all assets. Two
  parameters in the transform definitions themselves depend on the asset:
  - Δ in tick_grid is the asset's tick;
  - the m set in level_residual scales with the tick.

  A single uniform m was rejected. With m = 1 price unit, for example, an asset priced near 1.1 would show almost
  its whole price level, while an asset near 1800 would wrap every step. That would make the uniform choice itself
  a strong asset signal.

  **Interpretation:** C0 − C1 measures the transform in its public asset-conditioned form, and C1 − C2 measures
  secrecy. Any identity carried by the asset-conditioning itself (Δ inside tick_grid data, the m scale) stays in
  C1 and C2 alike, so it appears in neither difference. It is reported as part of the C1 level, not as a secrecy
  effect.
- C2: the representation with secret draws from the frozen table (as in RIP-1).

For the three representations without a secret, C1 and C2 are the same data. This is reported once, not twice.

**4a. Frozen world table used by C1 and by the A6 pooling rule** (review R2-04). The values come from
`src/xauusd_swarm/reid.py` (ASSETS, PERIODS) and the draw rule `src/xauusd_swarm/rip1_attack.py::draw`, both
frozen by FD-01-D45. Their SHA-256 values are:
- reid.py `4b553a3cba79f3b03a387110ede2ba02d0102c4c242df967a1ee3a7e189ca4fb`
- rip1_attack.py `6d28758ed17ee2bc525251b280a24d2c8ea581d426d0c793d3638a0ca38d555e`

| Asset | Level L_a | tick_a (= Δ) | m set {0.5, 1, 5, 10} × 100 × tick_a | C1 m (= 100 × tick_a) | c prior U(−L_a, L_a) |
|---|---|---|---|---|---|
| 0 | 1800 | 0.01 | {0.5, 1, 5, 10} | 1 | (−1800, 1800) |
| 1 | 30 | 0.001 | {0.05, 0.1, 0.5, 1} | 0.1 | (−30, 30) |
| 2 | 1.1 | 0.00001 | {0.0005, 0.001, 0.005, 0.01} | 0.001 | (−1.1, 1.1) |
| 3 | 150 | 0.01 | {0.5, 1, 5, 10} | 1 | (−150, 150) |

The a prior exp(U(−3, 3)) and the b prior U(−1000, 1000) are the **same for every asset**.

**Generator components** (review R5-02). These come from the same frozen reid.py. The pooled values are computed
from this table by the §7 rule: arithmetic mean over the 16 classes for μ and act, geometric mean over the 16
classes for σ and Lg.

| Asset | drift μ_a | vol_a | act_a |
|---|---|---|---|
| 0 | 0.00002 | 0.0009 | 0.6 |
| 1 | 0 | 0.0014 | 0.3 |
| 2 | −0.00001 | 0.0005 | 0.1 |
| 3 | 0.00001 | 0.0011 | 0.45 |

σ_k = vol_a × volx_p:

| Asset | p0 | p1 | p2 | p3 |
|---|---|---|---|---|
| 0 | 0.00072 | 0.0009 | 0.00144 | 0.00108 |
| 1 | 0.00112 | 0.0014 | 0.00224 | 0.00168 |
| 2 | 0.0004 | 0.0005 | 0.0008 | 0.0006 |
| 3 | 0.00088 | 0.0011 | 0.00176 | 0.00132 |

Lg_k = L_a × growth_p:

| Asset | p0 | p1 | p2 | p3 |
|---|---|---|---|---|
| 0 | 1800 | 2070 | 2340 | 2610 |
| 1 | 30 | 34.5 | 39 | 43.5 |
| 2 | 1.1 | 1.265 | 1.43 | 1.595 |
| 3 | 150 | 172.5 | 195 | 217.5 |

**Pooled values** (16 equal-weight classes):
- μ̄ = 0.000005
- act̄ = 0.3625
- σ̄ = 0.00101574 (geometric)
- L̄g = 66.2936 (geometric)

The build test checks every value in §4a against the code. A difference stops the build.
Periods (volatility factor, growth): p0 (0.8, 1.00), p1 (1.0, 1.15), p2 (1.6, 1.30), p3 (1.2, 1.45).
A build test checks that the code uses exactly these values.

**D — Δ in the ledger** (audit condition 1): hidden or shown. When shown, Δ is the only ledger field given, as a
per-family side value. The other ledger fields were at chance in RIP-1 and are not repeated here. D is crossed
with C1 and C2, so the secrecy × Δ interaction is estimable.

## 5. Attackers (same algorithms across conditions; audit condition 2)
- A1, A2, A3 (S-ind) and A4a, A4b (S-pool) with unchanged code.
- With Δ shown, A1, A2 and A4 append Δ as a one-hot feature, and A3 is run unchanged.
- A6 (likelihood), with only the nuisance handling depending on the condition:
  - C0: class model on prices directly, no nuisance;
  - C1: the RIP-1 likelihood with θ fixed at the canonical values, no integration;
  - C2: the RIP-1 likelihood, integrating over the published prior.
  - With Δ shown, classes whose tick ≠ Δ get probability 0, as A6-V1 in RIP-1.
- Comparisons are always made **attacker by attacker**. A best-of-attackers value is reported for orientation
  only and is never used to attribute an effect.

## 6. Estimands (per representation × scenario × attacker; asset, period, joint)
- Representation effect: acc(C0) − acc(C1).
- Secrecy effect: acc(C1) − acc(C2).
- Δ effect: acc(shown) − acc(hidden), in C1 and in C2.
- Secrecy × Δ interaction: the 2 × 2 contrast of (C1, C2) × (hidden, shown).

Every difference is a paired difference over the same families. The interval is a **stratified paired bootstrap
over families** (review R1-05):
- Strata are the 16 classes (asset × period).
- Within each stratum, families are resampled with replacement, keeping the stratum size (25, 10 or 5).
- A family is always resampled whole, with all its members.
- The **same** resampled index sets are used for every condition in a comparison.
- B = 2000, registered seed, 95 % percentile interval. No test, no threshold. The representation ×
secrecy interaction is not identifiable: there is no "secret without representation" cell, since a secret
parameter exists only inside a transform. It is declared, not computed.

## 7. Which information carries identity
**A6 component ablation** (review R1-03), in C2 with Δ hidden and with Δ shown.
- **Components at generator-parameter level.** Class k = (asset a, period p) is generated by:
  - drift μ_a;
  - volatility scale σ_k = vol_a × volx_p;
  - activity amplitude act_a;
  - level Lg_k = L_a × growth_p.

  σ_k and Lg_k are each kept as one component. Their products are not split, so the relation between asset and
  period factors inside each product is preserved.
- **Tick is not ablated in A6.** A6 ignores tick rounding, so in A6 the tick enters only through the transform
  definition: Δ in tick_grid, and the m set in level_residual. Tick is handled by the D factor and by the C1
  definition instead (declared).
- **Pooled value of a component.** The equal-weight mean over the 16 classes: arithmetic for μ and act, geometric
  for σ and Lg, since these are scale parameters. The pooled values are fixed by this rule before any data are
  generated: they come from the public world table, not from data.
- **Two prior settings** (review R3-01, R3-02):
  - **AP (asset priors, as in RIP-1).** The secret-parameter priors stay at the class's asset: the c range from L_a
    and the m set from tick_a. The a and b ranges are the same for every asset (§4a).
  - **PP (pooled priors).** Every asset-linked prior is replaced by the same asset-independent mixture for every
    class, fixed from §4a:
    - c ~ equal-weight mixture of U(−L_a, L_a) over the four assets;
    - m ~ uniform over the 16 values of the four assets' m sets, with multiplicity.

    log_returns, volatility_time and affine_level have no asset-linked prior, so for them AP = PP and the result
    is reported once.
  - **Δ inside tick_grid cannot be pooled.** Δ is part of the transform's definition (x = (P − c)/Δ); replacing it
    would change the representation itself. Under PP, tick_grid therefore keeps the class's Δ. This residual
    asset-conditioning is declared, and tick_grid's PP results stay conditional on it.
- **Restricted models per component j**, each under AP and PP:
  - **only-j:** the model keeps j as the only generator component that varies between classes; the other three
    are pooled.
    - Under AP it measures what the model achieves with j varying **while the information left in the priors and
      the transform remains**. It is **not** the information of j alone.
    - Under PP that remainder is removed, except Δ inside tick_grid. There it measures j's identifying information
      inside the model, for log_returns, volatility_time, affine_level and level_residual; for tick_grid, j
      together with Δ.
  - **all-but-j:** j is pooled; the other components keep their class values. The drop from the full model is
    **the effect of pooling j inside the full model**. It includes j's interactions with the other components, and
    it is not an independent causal contribution of j.
- **Brackets:**
  - **full model:** no pooling (AP).
  - **generator-pooled model:** all four generator components pooled, under AP and under PP. It is **not** assumed
    to be at chance; its accuracy is the identifying information left in the priors (AP) and in the transform.
  - **Expected baseline, stated before the run, from §4a:**
    - AP: chance (asset 1/4, period 1/4, joint 1/16) for log_returns, volatility_time and affine_level. Possibly
      above chance in the asset for tick_grid (Δ and the c range) and level_residual (the m set). Period stays at
      chance in every case, because no prior depends on the period. Assets 0 and 3 share Δ and the m set and
      differ only in the c range.
    - PP: chance for every representation except tick_grid, which may stay above chance in the asset through Δ.
  - only-j and all-but-j are read against the generator-pooled level **under the same prior setting**, not
    against chance.
- **Δ shown — interpretation** (review R2-02):
  - Component attribution is made **only with Δ hidden**.
  - With Δ shown, A6 sets classes whose tick differs from Δ to probability 0, so Δ decides part of the asset before
    any component acts. The Δ-shown ablation is therefore reported **only as a conditional result**, given what Δ
    reveals. Asset accuracy with Δ shown is never attributed to generator components.
  - The Δ-shown results are also reported **within the Δ-consistent classes**: the accuracy of choosing among the
    classes that share the shown tick.
    - For tick 0.01: assets 0 and 3 × 4 periods = 8 classes; within-group chance 1/8.
    - For 0.001 and 0.00001: one asset × 4 periods = 4 classes; within-group chance 1/4, so in effect the period.
  - Within a group, Δ and the m set are the same for every class, but under AP **the c range still differs**
    between assets 0 and 3 (L = 1800 vs 150; review R3-01). The within-group accuracy is therefore reported twice:
    - under AP, labelled **"conditional on Δ: generator components + remaining priors"**, never attributed to the
      components alone;
    - under **group-pooled priors**: c ~ equal-weight mixture of U(−1800, 1800) and U(−150, 150) for both assets of
      the 0.01 group. Single-asset groups need no pooling. With no asset-linked prior left inside the group, this
      within-group accuracy is attributable to the generator components, **inside the model**.
- **Scope of the conclusion.** This measures each component's contribution **inside the synthetic generative
  model**, for this attacker. It is not a general causal decomposition, and it does not show what drives
  identifiability in real markets.

**Feature-group ablation and permutation importance** (diagnostic only, evaluation data; review R1-04):
- Attackers: A2 in S-ind; A4a in S-pool, using the same A2 feature vector, averaged over the family.
- Feature groups (the reid.features layout): distribution, dependence, spectrum, volatility/extremes,
  shape/sequence.
- **Ablation** drops one group at a time and retrains on development data.
- **Permutation importance at family level:**
  - One random permutation π of the evaluation families is drawn per repeat, within the whole evaluation set.
  - For every family f, the group's feature values of every member of f are replaced by those of the members of
    π(f), member i by member i.
  - The family's internal dependence structure is therefore kept. Series are never shuffled one by one.
  - 50 repeats (registered seed). The importance is the mean accuracy drop, with its spread over repeats.

## 8. Research-utility baseline (cost of hiding, current transforms; review R1-02)
**Scope and data.**
- Measured per representation in C0, C1 and C2, on single series (S-ind design: 25 families per class, so 400
  units per world).
- Two kinds of evaluation world (registered seeds):
  - a **planted** world with the structure;
  - a **null** world without it.

  Everything else is identical to the RIP-1 world. Units are families, which equal series here.

**Increments seen by a researcher.** For a representation output x:
- d_t = x_t − x_{t−1} for C0 prices, tick_grid, affine_level and level_residual. These are raw differences,
  with no wrap correction: what the data show.
- d_t = x_t for log_returns.
- The variance proxy is s_t = d_t². The exception is volatility_time, where s_t = x_t − x_{t−1} (that is r_t²,
  already a variance proxy).
- t runs over 1 … n − 1 (511 values).

**U-vol — volatility tracking.**
- Planted world: the volatility is multiplied by 2 from a step τ ~ U{128, …, 384}, drawn per family.
- **Indexing (review R2-03).** The generator step t = 0 … 511 produces the price P_t. The true return of step t is
  r_t = ln P_t − ln P_{t−1}, for t = 1 … 511. The shift multiplies the standard deviation of r_t for **every t ≥ τ**,
  so r_τ is the first affected return. The increment d_t (and s_t) carries the same index t as r_t, because both
  are built from P_{t−1} and P_t.
- **Truth: the exact conditional expectation under the ACTUAL generator mechanism** (review R6; full derivation,
  table and pre-registered numerical verification in `docs/research/RIP2_UVOL_DERIVATION.md`). This replaces the
  v0.6 rows. v0.6 assumed independent uniform rounding errors, which the deterministic rounding of the generator
  does not give, and used a first-order rounding term for log_returns and volatility_time while calling the truth
  exact. That inconsistency is stated in the derivation §1.
  - Given the latent P_{u−1} (custody side), the observed P̃_{u−1} is fixed, and P̃_u takes the values j·tick with
    p_j = Φ((ln((j+½)tick/P_{u−1}) − μ)/σ_u) − Φ((ln((j−½)tick/P_{u−1}) − μ)/σ_u).
  - E[q_u | P_{u−1}] = Σ_j p_j · q(P̃_{u−1}, round(j·tick, 10)). q is the quantity the estimator averages: d_u² for
    C0, tick_grid, affine_level and log_returns; r̃_u² for volatility_time; the **unwrapped** squared difference for
    level_residual (design choice kept from v0.5).
  - Drift, the exponential map, the deterministic rounding and the log of rounded prices are all inside p_j and q,
    the same way for every representation, with no approximation beyond floating point. The sum is truncated at
    μ ± 12σ, mass < 10⁻³².
- **Truth:** v_t = sqrt(mean of E[q_u | P_{u−1}] over u = t − 31 … t).
- **Estimate (unchanged):** ṽ_t = sqrt(mean of q_u over the same window), from the observed series.
- **Statistic:** Spearman ρ between v_t and ṽ_t over t = 32 … 511, per family. A constant factor within a series
  (a, 1/Δ) does not change ρ.
- **Verification before build:** formula vs Monte Carlo of the actual mechanism on 10 pre-registered cases × 5
  quantity kinds; acceptance: |MC − exact| ≤ 4 SE in all 50 (derivation §5; result in
  `docs/results/RIP2_uvol_verification.json`).
- **What it measures:** how well the representation's observed increments track the true volatility in that
  representation's own units. Price-level drift is in both truth and estimate. In level_residual the observed
  increments wrap modulo m while the truth uses the unwrapped scale: a loss of tracking caused by the wrap counts
  as a real loss of volatility information.
- **Reported:** mean ρ with a stratified family bootstrap interval (§6), in the planted and in the null world. In
  the null world v_t still varies through the activity cycle and the price level, and that ρ is the reference.

**U-act — activity cycle (period 64).**
- Planted world: the RIP-1 world (activity amplitude act_a). Null world: act = 0 for every asset.
- Use the first 448 values of s_t (7 full cycles), centred. Periodogram I_k = |Σ_t s_t e^{−2πikt/448}|², for
  k = 1 … 223; the cycle is at k = 7.
- **Detection:** I_7 > the 99th percentile (linear interpolation) of {I_k : k = 1 … 223, k ∉ {6, 7, 8}}.
- Reported (Wilson 95 %): the detection rate in the planted world (power) and the detection rate in the null world
  (**false alarm**). The nominal null rate is about 1 %, but it is measured, not assumed.

**U-event — change-point recovery.**
- Same planted shift as U-vol (×2 from τ). Null world: no shift.
- CUSUM: S_k = Σ_{t = 1 … k} (s_t − s̄) for k = 1 … 510; k̂ = argmax_k |S_k|, the last index before the
  change. **Ties are broken by the smallest k** (review R3-03), in every case and world. The estimated first
  affected step is **τ̂ = k̂ + 1**.
- **Detection flag:** max_k |S_k| / (σ̂_s · sqrt(511)) > 1.358, where σ̂_s is the standard deviation of s_t and
  1.358 is the 95 % point of the supremum of a Brownian bridge.
- **Success** (planted) = flag and |τ̂ − τ| ≤ 16.
- Reported (Wilson 95 %): the success rate and the flag rate in the planted world; the flag rate in the null world
  (**false alarm**). s_t is heteroscedastic through the activity cycle, so the bridge approximation is not exact.
  This is why the null false-alarm rate is measured, never assumed.

**Use.** These values are the reference against which RIP-3 must state each alternative's cost. A representation
that hides identity by losing these structures is reported as such. Every definition above is fixed before any
code is written, and is reproducible from the formulas and the registered seeds.

## 9. Reporting and rules
- Every cell is reported, negative results included. Nothing is chosen on these data. RIP-3 gets its own
  registration and fresh evaluation data (audit condition 4).
- The code is written after this design passes review. The design and code are frozen before the single run.
  Seeds are public and fixed in the freeze record.

## 9a. Registered seeds (fixed here, recorded again in the freeze)
| Use | Seed |
|---|---|
| development families | 5101 |
| evaluation families (§3–§7) | 5102 |
| utility, planted world | 5103 |
| utility, null world | 5104 |
| bootstrap | 5201 |
| permutation importance | 5202 |

## 10. Open points for the reviewer (v0.1 points answered in the register)
1. Is the canonical C1 parameter set (c = 0, a = 1, b = 0, m = median) acceptable? m = median keeps the asset's
   own m scale, which is itself asset-dependent.
2. Are the three utility measures sufficient as a baseline, or should a path-1-style planted-effect detection be
   added here rather than in RIP-3?
3. B = 2000 bootstrap replicates and 50 permutation repeats: adequate?
