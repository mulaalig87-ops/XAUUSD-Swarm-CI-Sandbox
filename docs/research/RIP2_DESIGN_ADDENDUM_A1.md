# RIP-2 design — addendum A1 (founder decision OD-S9-08) — level_residual likelihood in A6

The frozen design file `RIP2_DESIGN.md` v0.7 (sha256 bee007da…, FD-01-D46) is **not changed**. This addendum records
the one deliberate deviation from it that the founder approved.

**What §5 says:** A6 in C2 uses "the RIP-1 likelihood".
**What RIP-2 uses for level_residual instead (all conditions and ablations):** the same model, computed exactly.
1. **Exact wrapped-normal sum (IC-12):**
   - the dual (Poisson summation) series when S/m > 0.5;
   - otherwise the direct sum centred on the nearest image.

   The RIP-1 code centres the direct sum on j = 0 and drops mass for increments larger than about 8·S + 2·m
   (FL-023).
2. **Support of the transform (FL-024):** x = fmod(P, m) with P > 0 lies in [0, m), so a hypothesis m with any
   observed value outside [0, m) has likelihood 0. The check is exact (x ≥ m, no tolerance); math.fmod is exact in
   IEEE 754 (review B-R2-02). RIP-1 has no such check. Without it, the exact sum gives
   log(1/m) per step to every small m, whatever the data.

**Why:** both are properties of the registered model. The RIP-1 computation is a numerical defect of that model,
not a different model.

**Size of the difference** (separate diagnostic RIP-1-D1 on the committed RIP-1 data; level_residual A6 rows only;
historical / exact):

| View | Scenario | Attacker | asset | period | joint | predictions changed |
|---|---|---|---|---|---|---|
| V0 | ind | A6 | 0.657 / 0.980 | 0.273 / 0.767 | 0.180 / 0.760 | 289 of 400 |
| V0 | g4 | A6 | 0.675 / 0.988 | 0.275 / 0.756 | 0.181 / 0.750 | 111 of 160 |
| V0 | g16 | A6 | 0.675 / 0.988 | 0.225 / 0.787 | 0.163 / 0.787 | 62 of 80 |
| V1 | ind | A6-V1 | 0.887 / 0.980 | 0.367 / 0.767 | 0.333 / 0.760 | 205 of 400 |
| V1 | g4 | A6-V1 | 0.863 / 0.988 | 0.338 / 0.756 | 0.306 / 0.750 | 84 of 160 |
| V1 | g16 | A6-V1 | 0.875 / 0.988 | 0.325 / 0.787 | 0.300 / 0.787 | 51 of 80 |

The historical code reproduces the committed RIP-1 predictions exactly in every row, so the pipeline is the same.
With the exact likelihood, A6 identifies the asset in level_residual at about 0.98, against 0.66–0.89 historically.
**In the synthetic world, level_residual is therefore not the strongest blinding when a correct model-knowing
attacker is used.** The historical RIP-1 report is unchanged; this is a diagnostic only.

**Cross-version rule:** RIP-2 level_residual A6 results are compared with RIP-1-D1, never with the historical RIP-1
A6 / A6-V1 level_residual rows.
