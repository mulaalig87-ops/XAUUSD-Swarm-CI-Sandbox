# Path card — P1-distributional («الانتظامات التوزيعية», س 752, مك-91)

Founder decision OD-S9-01 («المسار 1»). The architecture names the path only; the method is a design
under FD-01. Required for any path: lineage, card and generalisation test (س 756).

**Status (2026-11-17): v4.1 PASSED all its TP-21/tool controls** (founder OD-S9-05; designs FD-01-D41,
FD-01-D42; FL-011 closed by v4.1). Card version 4 (this text). v4 is superseded (its reference set left the
H0 space). Card version 1 is in git history (commit 78811ed); the card text used by the v1–v3 runs is
`docs/paths/PATH1_CARD_runs_v1-v3.md`. Synthetic results only: nothing here shows the method works on gold.

## Current version — v4.1 (FD-01-D42): `scan_v41`
- **Unit of exchange:** the maximal label runs (adjacent runs differ by definition).
- **H0:** given the run boundaries and lengths and the number of runs of each cell, every arrangement of
  the cells over the runs with no two adjacent runs sharing a cell is equally likely, independent of the
  returns.
- **Reference distribution:** exact uniform draws from that set (dynamic-programming counting); every
  reference sequence keeps the observed runs, lengths, boundaries and per-cell run counts; the returns are
  never changed. Per-cell Monte Carlo p-value (1 + #{D_c(ref) ≥ D_c(obs)}) / (M + 1), M = 199; Holm across
  cells, alpha 0.05.
- **Assumption to check before use on real labels:** H0 above. Labels that follow a calendar cycle, or
  whose cells depend on run length, do not satisfy it and need another reference set. Few runs give a
  coarse p-value (about 20+ runs for 3 cells).
- **World (declared change after seeing results, OD-S9-05):** n = 1600, mean run 50.
- **Results (`docs/results/WP9-02_path1_v41.json`):** real 0.84; spurious (SV) 0.02; null 0.06;
  spurious_level 0.02; null_heavy (t3) 0.00 — all criteria met. Generalisation (declared): runs of 20:
  real 1.00, others 0.04–0.06; runs of 120: real 0.18 (few runs), others 0.00–0.02.

## v4 (FD-01-D41): `scan_v4` — superseded
Same statistic and worlds; reference = free shuffle of the cells of the maximal runs. Adjacent runs then
receive the same cell and merge (100 % of draws on the v4 worlds), so the reference did not match H0
(review R1-01 of v4). Results 0.98 / 0.04 / 0.06 / 0.02 / 0.04 kept, not used to close FL-011.

## v3 (FD-01-D37, founder OD-S9-02): `scan_per_cell` — superseded
- **Statistic:** D_c for each cell separately (no max over cells).
- **Reference distribution:** for each cell, D_c recomputed after rotating the label sequence by a
  random offset k drawn uniformly from [n/10, n − n/10]; M = 199.
- **Decision:** Holm across the cells of one scan, alpha 0.05.
- **Result:** real 0.66 (FAIL), spurious 0.10, null 0.08; generalisation real 0.90 at n = 800.
- **Validity NOT established (review R1-01, accepted):** the reference set excludes the identity and the
  rotations near it, so it is not the full rotation group containing the observed alignment; and a
  linear (non-circular) series is not invariant under rotation. The p-value `(1 + #{T_null ≥ T_obs}) /
  (M + 1)` is therefore not guaranteed valid, and Holm cannot repair an invalid single-cell p-value.
  The same holds for v1. The 0.66 is not read as "power only". Before any v4: state the exchangeability
  hypothesis exactly, justify the reference set (or use the full group including the observed
  alignment), test rejection rates on further null and spurious worlds, and pre-register.

## Earlier versions (kept)
- **v1 (FD-01-D35):** scan statistic max_c D_c; reference = same rotations, M = 49; single-step max-T.
  Result: real 0.28 (FAIL), spurious 0.06, null 0.04.
- **v2 (FD-01-D36):** max_c D_c; reference = permutation of cell labels across label runs (run
  boundaries kept), M = 49. Result: real 0.00 (FAIL), spurious 0.00, null 0.02 — the max over cells is
  invariant to renaming cells, so many permutations reproduce the observed partition.
