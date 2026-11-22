# RIP-2 — status note (audit RR2-01)

The header of `docs/research/RIP2_DESIGN.md` still reads "v0.7 — DRAFT FOR REVIEW (not frozen, nothing built or run)".
That header is **stale**: the file is kept byte-identical on purpose, because it is frozen.

The authoritative status is in `docs/DECISIONS.md`:
- **FD-01-D46:** design v0.7 frozen (sha256 bee007da…), BUILD authorised.
- **OD-S9-08:** addendum A1, the exact level_residual likelihood.
- **OD-S9-09:** the single registered run authorised. It was carried out on 2026-11-19 (`docs/results/RIP-2_REPORT.md`).
- **RIP-2 result audit (ChatGPT, bundle 7dbf1f8):** NO BLOCKERS. RIP-2 is closed; it is not to be re-run under that
  authorisation.

The same holds for every "DRAFT" header in a design file frozen by a recorded decision: the decision record controls.
