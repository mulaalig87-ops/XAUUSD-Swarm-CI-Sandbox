# XAUUSD Swarm — Build Repository (Stage 8)

Clean repository for building XAUUSD Swarm (WP8-01).

- **Authority:** Stage 7 Register §34 — B7 closed, B8 open (2026-11-15).
- **Design reference (read-only, not copied here):** `XAUUSD_Swarm_Architecture_Unified_Candidate_01.md`
  (SHA-256 `64dc409b0d85a77b8eee263343a44c6111d449c84e1cdffc5d9165fcf751c794`).
- **Specifications:** Stage 7 WP7-01 to WP7-07 (outside this repository).

## Hard rules
- No code, results or files from N0, V2.2, V2.4 or ORACLE INFINITY (OD-08).
- No gold data, no Stage-9 simulation, no scientific-validation tests (OD-10, OD-11; Register §34).
- Unit tests run on synthetic data only (Register §34).
- Branch policy: `docs/BRANCH_POLICY.md` (local barrier only; not remote protection).
- Two separate environments, dev and test, fully pinned in `env/*.lock.txt` (OD-09, §26 غ-12; `docs/ENVIRONMENT.md`).
