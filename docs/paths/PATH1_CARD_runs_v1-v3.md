# Path card — P1-distributional («الانتظامات التوزيعية», س 752, مك-91)

Founder decision OD-S9-01 («المسار 1»). The architecture names the path only; the method is a design
under FD-01-D35. Required for any path: lineage, card and generalisation test (س 756).

- **Kind:** discovery tool, not a court (§9). Output = proposals to the queue (ق-03), never evidence.
- **Input:** a return series r_t and a frozen label per observation (cells recorded before the scan:
  e.g. regimes or sessions). Labels come from the registered representation and are not chosen after
  seeing the returns.
- **Target:** cells whose return distribution differs from the rest of the series.
- **Statistic:** two-sample Kolmogorov–Smirnov distance per cell vs the rest; scan statistic = max over cells.
- **Null and its assumption (v2, FD-01-D36):** permutation of the cell labels across label runs (run
  boundaries and series kept). Assumes the assignment of cells to runs is exchangeable given the run
  structure. **v1 (FL-011, failed its positive control):** circular rotation of the label sequence (minimum offset n/10). Valid when
  the alignment of labels and returns is the only thing broken: the series' own dependence is kept.
  Assumes the label process is roughly stationary under rotation (very long single runs reduce power).
- **Error control:** single-step max-T over the cells of one scan (family-wise within the scan).
  Across scans, families and paths: the court's procedure applies; the scan is not a confirmation.
- **Known limits:** KS is sensitive mostly to location/scale differences near the centre; tail-only
  differences have low power. Rotation null with few long runs has few distinct alignments.
- **Controls (TP-21/tool, matrix row):** real effect (cell A scaled ×1.8) must be proposed; spurious
  effect (volatility clustering independent of the labels) must not be proposed; null world must not.
  Criteria pre-registered in FD-01-D35.
- **Generalisation test:** the three control worlds re-run at other sample sizes and segment lengths
  (n = 800; mean segment 20; mean segment 120), measured and declared (no threshold).
- **Lineage:** `src/xauusd_swarm/path1.py` (file hash recorded with every run).
