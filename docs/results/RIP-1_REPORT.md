# RIP-1 — result report (re-identification through Custody/Vault) — SYNTHETIC ONLY

Design frozen by FD-01-D45 (design v0.6 + code at 206a0cd; ChatGPT R1–R6, final NO BLOCKERS). One run, registered spec,
no override: `xauusd_swarm.rip1.run` (6697 s). Results: `docs/results/rip1/` (`results.json` = all 260 rows with counts,
Wilson 95 % intervals and confusion matrices). No threshold is applied (CS-01-04 stays open with the founder).
Nothing here concerns gold data, OD-10, OD-11 or G-Z; passing or failing re-ID opens no gate.

## 1. Headline
- **The current blindings do not hide identity in this synthetic world.** Using the likelihood attacker A6, which
  knows the public world description, the asset and the period are identified almost perfectly. This holds for
  log_returns (= activity_time), tick_grid and volatility_time: joint accuracy 0.988–1.000 on independent samples,
  where chance is 0.0625.
- **affine_level hides the period better than the asset.** The asset is identified at 0.95 (independent samples)
  to 1.00 (groups of 16). The period is identified at about 0.42, still above chance (0.25).
- **level_residual is the strongest blinding measured, but it is not at chance.** On independent samples the best
  observed asset accuracy is 0.79 (V0, A1) and 0.89 (V1, A6-V1; a difference between views, not a causal estimate
  of Δ, see §5 H4). The period is identified at about 0.37.
- **The public ledger leaks the asset through Δ.** Δ alone (A5-delta) gives asset accuracy 0.75 for every
  representation, exactly the structure of the tick table: assets 0 and 3 share tick 0.01, while assets 1 and 2
  each have their own. Every other ledger field (nonce, signature, commitment, signer, action, family) is at chance.
  The entry order is near chance (0.16–0.30, small groups).
- **Isolation held:**
  - All probes passed in all 10 sandbox runs.
  - The ledger scan found no secret: 43601 secret values checked (c, a, b, m, salt, seed, key), 0 hits. 819
    m values equal a public Δ text and are reported as excluded.
  - The sandboxed protocol reproduction re-ran the ten runs in fresh sandboxes: 10/10 identical (per-run record:
    `docs/results/RIP-1_repro_attestation.json`). Independent re-scoring from predictions and revealed truth only
    (`scripts/rip1_rescore.py`): 260/260 rows match.

## 2. Best attacker per cell — V0 (blinded series + grouping)
Accuracy [Wilson 95 %] and the attacker achieving it. Units: samples (ind) or families (g4, g16).

| Representation | Scenario (units) | asset (chance 0.25) | period (chance 0.25) | joint (chance 0.0625) |
|---|---|---|---|---|
| log_returns (= activity_time) | ind (400) | 0.993 [0.978, 0.997] A6 | 0.988 [0.971, 0.995] A6 | 0.988 [0.971, 0.995] A6 |
| log_returns (= activity_time) | g4 (160) | 1.000 [0.977, 1.000] A6 | 1.000 [0.977, 1.000] A6 | 1.000 [0.977, 1.000] A6 |
| log_returns (= activity_time) | g16 (80) | 1.000 [0.954, 1.000] A4a | 1.000 [0.954, 1.000] A4a | 1.000 [0.954, 1.000] A4a |
| tick_grid | ind (400) | 0.998 [0.986, 1.000] A6 | 0.998 [0.986, 1.000] A6 | 0.998 [0.986, 1.000] A6 |
| tick_grid | g4 (160) | 1.000 [0.977, 1.000] A6 | 1.000 [0.977, 1.000] A6 | 1.000 [0.977, 1.000] A6 |
| tick_grid | g16 (80) | 1.000 [0.954, 1.000] A6 | 1.000 [0.954, 1.000] A6 | 1.000 [0.954, 1.000] A6 |
| level_residual | ind (400) | 0.792 [0.750, 0.829] A1_knn_features | 0.370 [0.324, 0.418] A1_knn_features | 0.310 [0.267, 0.357] A1_knn_features |
| level_residual | g4 (160) | 0.675 [0.599, 0.743] A6 | 0.338 [0.269, 0.414] A4a | 0.194 [0.140, 0.262] A4a |
| level_residual | g16 (80) | 0.750 [0.645, 0.832] A4a | 0.325 [0.232, 0.434] A4a | 0.287 [0.200, 0.395] A4a |
| affine_level | ind (400) | 0.948 [0.921, 0.965] A6 | 0.417 [0.370, 0.466] A6 | 0.393 [0.346, 0.441] A6 |
| affine_level | g4 (160) | 0.988 [0.956, 0.997] A4a | 0.425 [0.351, 0.502] A4a | 0.425 [0.351, 0.502] A4a |
| affine_level | g16 (80) | 1.000 [0.954, 1.000] A4b | 0.438 [0.334, 0.547] A4a | 0.438 [0.334, 0.547] A4a |
| volatility_time | ind (400) | 0.998 [0.986, 1.000] A6 | 0.998 [0.986, 1.000] A6 | 0.998 [0.986, 1.000] A6 |
| volatility_time | g4 (160) | 1.000 [0.977, 1.000] A6 | 1.000 [0.977, 1.000] A6 | 1.000 [0.977, 1.000] A6 |
| volatility_time | g16 (80) | 1.000 [0.954, 1.000] A4a | 1.000 [0.954, 1.000] A6 | 1.000 [0.954, 1.000] A6 |

## 3. Best attacker per cell — V1 (V0 + read-only ledger snapshot)

| Representation | Scenario (units) | asset (chance 0.25) | period (chance 0.25) | joint (chance 0.0625) |
|---|---|---|---|---|
| log_returns (= activity_time) | ind (400) | 1.000 [0.991, 1.000] A6-V1 | 0.995 [0.982, 0.999] A6-V1 | 0.995 [0.982, 0.999] A6-V1 |
| log_returns (= activity_time) | g4 (160) | 1.000 [0.977, 1.000] A6-V1 | 1.000 [0.977, 1.000] A6-V1 | 1.000 [0.977, 1.000] A6-V1 |
| log_returns (= activity_time) | g16 (80) | 1.000 [0.954, 1.000] A5-comb | 1.000 [0.954, 1.000] A6-V1 | 1.000 [0.954, 1.000] A6-V1 |
| tick_grid | ind (400) | 1.000 [0.991, 1.000] A6-V1 | 1.000 [0.991, 1.000] A6-V1 | 1.000 [0.991, 1.000] A6-V1 |
| tick_grid | g4 (160) | 1.000 [0.977, 1.000] A6-V1 | 1.000 [0.977, 1.000] A6-V1 | 1.000 [0.977, 1.000] A6-V1 |
| tick_grid | g16 (80) | 1.000 [0.954, 1.000] A5-comb | 1.000 [0.954, 1.000] A6-V1 | 1.000 [0.954, 1.000] A6-V1 |
| level_residual | ind (400) | 0.887 [0.853, 0.915] A6-V1 | 0.367 [0.322, 0.416] A6-V1 | 0.333 [0.288, 0.380] A6-V1 |
| level_residual | g4 (160) | 0.863 [0.801, 0.907] A6-V1 | 0.338 [0.269, 0.414] A6-V1 | 0.306 [0.240, 0.382] A6-V1 |
| level_residual | g16 (80) | 0.875 [0.785, 0.931] A6-V1 | 0.325 [0.232, 0.434] A6-V1 | 0.300 [0.211, 0.408] A5-comb |
| affine_level | ind (400) | 0.998 [0.986, 1.000] A6-V1 | 0.412 [0.365, 0.461] A6-V1 | 0.412 [0.365, 0.461] A6-V1 |
| affine_level | g4 (160) | 1.000 [0.977, 1.000] A5-comb | 0.425 [0.351, 0.502] A6-V1 | 0.425 [0.351, 0.502] A6-V1 |
| affine_level | g16 (80) | 1.000 [0.954, 1.000] A5-comb | 0.438 [0.334, 0.547] A6-V1 | 0.438 [0.334, 0.547] A6-V1 |
| volatility_time | ind (400) | 1.000 [0.991, 1.000] A6-V1 | 1.000 [0.991, 1.000] A6-V1 | 1.000 [0.991, 1.000] A6-V1 |
| volatility_time | g4 (160) | 1.000 [0.977, 1.000] A5-comb | 1.000 [0.977, 1.000] A6-V1 | 1.000 [0.977, 1.000] A6-V1 |
| volatility_time | g16 (80) | 1.000 [0.954, 1.000] A5-comb | 1.000 [0.954, 1.000] A6-V1 | 1.000 [0.954, 1.000] A6-V1 |

## 4. Every attacker, V0, independent samples (asset / period / joint accuracy)

| Attacker | log_returns | tick_grid | level_residual | affine_level | volatility_time |
|---|---|---|---|---|---|
| A1_knn_features | 0.77 / 0.53 / 0.49 | 0.86 / 0.45 / 0.43 | 0.79 / 0.37 / 0.31 | 0.79 / 0.27 / 0.21 | 0.84 / 0.54 / 0.51 |
| A2_centroid_features | 0.85 / 0.63 / 0.60 | 0.90 / 0.45 / 0.42 | 0.55 / 0.29 / 0.17 | 0.84 / 0.32 / 0.29 | 0.89 / 0.60 / 0.59 |
| A3_series_match | 0.60 / 0.27 / 0.17 | 0.27 / 0.25 / 0.06 | 0.34 / 0.27 / 0.11 | 0.24 / 0.25 / 0.08 | 0.49 / 0.26 / 0.12 |
| A6 | 0.99 / 0.99 / 0.99 | 1.00 / 1.00 / 1.00 | 0.66 / 0.27 / 0.18 | 0.95 / 0.42 / 0.39 | 1.00 / 1.00 / 1.00 |

## 5. Hypotheses (stated before the run; descriptive, no tests)
- **H1 (comparison with TP-30, descriptive).** The comparison below uses only A1–A3, which both runs share.
  RIP-1 V0 versus TP-30, asset accuracy:
  - tick_grid: 0.90 vs 0.88 (partly comparable: the c distribution changed).
  - level_residual: 0.79 vs 0.76.
  - affine_level: 0.84 vs 0.81.
  - volatility_time: 0.89 vs 0.85.
  - log_returns: 0.85 vs 0.71, **not comparable** (the secret scale was removed).

  Where comparable, drawing parameters from the Vault instead of the local generator left the result in the same
  range. The much higher best values in RIP-1 come from the new attacker A6, not from the change of parameter source.
- **H2 (pooling, descriptive).**
  - affine_level asset: 0.95 → 0.99 → 1.00 for g = 1, 4, 16.
  - The other leaky representations are already near 1.0 at g = 1.
  - level_residual is not monotone in V0 (0.79, 0.68, 0.75; asset). No trend is claimed.
- **H3 (no-secret representations).** log_returns, activity_time and volatility_time are almost fully identifiable
  (A6, joint ≥ 0.988). Blinding cannot act on them because they carry no secret.
- **H4 (ledger).** Δ is an identifying channel: Δ alone (A5-delta) gives asset accuracy 0.75 for all
  representations. That is the direct evidence. For level_residual (independent samples), the best observed
  asset accuracy rises from 0.79 in V0 (A1) to 0.89 in V1 (A6-V1); for the same attacker A6 it rises from 0.66
  (V0) to 0.89 (V1). V1 adds the whole ledger snapshot, not Δ alone, so this rise is an observed difference
  between views, **not an isolated causal estimate of Δ's effect**; a controlled Δ shown/hidden comparison with
  the same attacker is planned for RIP-2 (audit R1-02). No other ledger field carried information.
- **H5 (isolation, pass/fail).** Pass on this host: all probes in 10/10 runs, the ledger scan, the protocol
  reproduction (10/10 identical) and the adversarial tests (test suite).

## 6. How to read this (limits, declared)
- **The attacker knows the exact generative model.** The world is simple: Gaussian returns with known per-class
  drift, volatility, period factor and activity pattern, and A6 knows these parameters (Kerckhoffs, as registered).
  This favours the attacker. A6 is a likelihood attacker that knows the generative model; it gives a strong
  measurement of identifiability inside this synthetic model. It is **not a proven upper bound** (audit R1-01):
  its integrals are numerical (257-point grids), the level_residual model uses a declared approximation of the
  price path, the tick_grid model ignores tick rounding, and nothing proves that another attacker cannot do
  better. Real markets are not described by four known parameter sets, so this is not a measurement on gold. It is still the relevant
  warning: in the synthetic world, the blinding transforms leave the statistical fingerprint of the series
  (volatility level, activity pattern, tick discreteness) intact.
- **Not measured:**
  - a language-mind attacker;
  - a multi-representation attacker;
  - TP-31 and TP-33.
- **Isolation scope:** same host and kernel; not a defence against kernel exploits. The orchestrator signature
  attests what it verified; it is not a proof of execution integrity.
- **Statistics:** the intervals are Wilson intervals over independent units; g16 has 80 families, so its
  intervals are wide.

## 7. What it means for the next phases (no decision taken here)
- RIP-2 (diagnosis) has clear targets:
  - for affine_level and level_residual, which statistics carry the asset (volatility level, tick discreteness,
    activity pattern);
  - why the period survives in tick_grid but much less in affine_level;
  - the share carried by Δ in the ledger.
- RIP-3 alternatives must hide the statistical fingerprint rather than the level, and their cost to research
  utility must be measured. Moving Δ out of the public ledger is one obvious candidate.
- CS-01-04 stays with the founder. With the attackers registered here, every current blinding would fail any
  threshold close to chance on the asset.
