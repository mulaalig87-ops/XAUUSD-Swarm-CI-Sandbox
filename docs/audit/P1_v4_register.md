# Path 1 v4 — review register (ChatGPT)

| ID | Severity | Item | Status | Resolution |
|---|---|---|---|---|
| R1-01 | MAJOR | v4's permutations did not match the stated H0: shuffling the cells of maximal runs lets adjacent runs receive the same cell and merge | ACCEPTED — FIXED by v4.1 | measured: 100 % of v4 reference draws changed the run structure. v4.1 (FD-01-D42, pre-registered, commit a9d25cd): unit of exchange = maximal runs; H0 = uniform over arrangements with fixed per-cell run counts and no adjacent repeat; exact sampler by DP counting (checked exactly uniform on a small case); tests that every draw keeps the number of runs, their lengths and boundaries, the per-cell run counts and has no merged runs. Result: all five criteria met (real 0.84). v4 kept, marked superseded; FL-011 closed by v4.1 only. |

## Round R2 — ChatGPT verdict "NO BLOCKERS" on main @ f22613d
| ID | Severity | Item | Status | Resolution |
|---|---|---|---|---|
| R2-01 | MINOR | R = 50 gives a first estimate; 0.84 is close to 0.80 | FIXED (wording) | WP9-05 report §4 carries the precision note (95 % Wilson interval for 42/50 ≈ 0.71–0.92); rates are not described as stable estimates. |
| R2-02 | MINOR | script header and results `component` still said v4 | FIXED | header names v4.1 / FD-01-D42 as current; `component` carries the version; v4.1 results regenerated (identical observations). |
Closed.
