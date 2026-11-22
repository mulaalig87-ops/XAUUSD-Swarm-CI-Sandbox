# Known blind spots (§21 register; candidate §12, س 1541)

Types of planted leak that were NOT detected by either method are recorded here. They are never reported
as "no leak". Detection of planted types does not show the absence of unplanted types (س 1543).
Every entry is from a SYNTHETIC experiment and measures the lineage check defined in FD-01-D38 (the
architecture's own check is undefined, مع-58).

| # | Type | Lineage check | Statistical (E[s·h] test, null worlds) | Source |
|---|---|---|---|---|
| BS-01 | ت8 weak partial leak, fraction ≤ 0.03 (code bypassing the capture) | 0.00 | 0.04–0.05 (nominal 0.05) | `docs/results/WP9-03_TP50.json` |
| BS-02 | ت9 implicit encoding of the NEXT size inside E_t (vendor field) | 0.00 | 0.04 — the sign test is blind to a size leak in a sign-symmetric world | same |

Measured but not blind: ت8 at fraction 0.10 is detected statistically in 0.38 of worlds and at 0.30 in
all. The smallest TESTED fraction with statistical inflation (rate > 0.10) is 0.10; this is not a
true minimum detectable leak (fractions between 0.03 and 0.10 were not tested; R = 100). ت3 (slice-wide normalisation) is caught only by
the lineage check (statistical 0.06).
Limits of the measurement: iid null worlds only; one statistic (z-test of E[s·h]); n = 600.
