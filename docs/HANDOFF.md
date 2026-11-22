# Handoff — state as of 2026-11-23 (RIP-3 section; other sections as last updated)

## Where things are
- Repository: github.com/mulaalig87-ops/XAUUSD-Swarm (private; renamed from XAUUSD-Swarm-Build on 2026-11-16). All branches and history are
  pushed. `main` holds every merged component.
- Governing documents: `docs/reference/` (Unified Candidate 01, Stage-4 index, Stage-6/7 registers,
  WP7-01…WP7-07, test and validation plans, execution plan 07). Section markers ⟨س N⟩ refer to the
  candidate.
- Founder decisions in this repo: `docs/DECISIONS.md` (FD-01 delegation).
- Releases and file hashes: `docs/RELEASES.md`.

## Stage status
- B7 closed; B8 open (build). Unit tests on synthetic data are authorised (register §34).

## Components merged in `main` (dependency order, WP7-01 §5)
| WP | Layer | Module | Merge |
|---|---|---|---|
| WP8-01 | repo setup (Windows package) | `scripts/wp801_*` | package 02 (5b4622b4…), run on Windows 2026-11-16 |
| WP8-02 #1 | governance + ledger | `ledger.py`, `identity.py`, `charter.py` | d3d63110 |
| WP8-02 #2 | 2 claims charter | `claims.py` | 6971c830 |
| WP8-03 | 3 custody/blinding | `custody.py`, `representations.py` | 8e48ee49 |
| WP8-04 | 9 court + 10 knowledge/lineage | `court.py`, `court_service.py`, `knowledge.py` | 7a4feef8 |
| CI | GitHub Actions | `.github/workflows/tests.yml` | c92b7161 |
| CI fix | 2 POSIX-only tests made platform-aware (Windows failed 2/277) | tests only | 7518cd4 |
| WP8-05 | 4 inventory/C0/transforms + 5 slicing/purge/embargo/availability | `inventory.py`, `slicing.py` | see RELEASES |
| WP8-05b | review R1 fixes (FD-01-D11) | `inventory.py`, `slicing.py` | see RELEASES |
| WP8-05c | review R2 fix (audit completeness) | `slicing.py` | see RELEASES |
| WP8-06 | 6 evidence economy (gates, separation, adequacy, Final) + TP-88 (Holm FWER) | `evidence.py` | see RELEASES |
| WP8-06b | review R1 fixes (atomic Final opening) | `evidence.py` | see RELEASES |
| WP8-06c | review R2 fix (signed opening manifest) | `evidence.py` | see RELEASES |
| WP8-06d | review R3 tests | `tests/test_evidence.py` | see RELEASES |
| WP8-07 | 7 discovery system (paths, minds, channels, proposals, queue) | `discovery.py` | see RELEASES |
| WP8-07b | review R1 fixes | `discovery.py` | see RELEASES |
| WP8-08 | 8 falsification/confirmation (stages, nulls, rediscovery, drift) | `falsification.py` | see RELEASES |
| WP8-08b | review R1 fix + controls registry (axis start) | `controls.py`, `falsification.py` | see RELEASES |
| WP8-08c | review R2 fix (verifiable control execution) | `controls.py` | see RELEASES |
| WP8-08d | review R3 fix (independent re-execution) | `controls.py` | see RELEASES |
| WP8-09 | cross-cutting axis: control matrix + governance audit | `controls.py`, `governance_audit.py` | see RELEASES |
| WP8-09b | review R1 fixes (all tool kinds gated) | `controls.py`, `governance_audit.py` | see RELEASES |
| WP9-01a | ledger-level end-to-end integration | `tests/test_integration.py` | see RELEASES |
| WP9-01b | G1 paths Z / G-Z / R and flows | `paths.py`, `tests/test_paths.py` | see RELEASES |
| WP9-01c | review R1 fixes (R origin, closed fields, full-state replay) | `paths.py`, tests | see RELEASES |
| WP9-01d | review R2: recursive full-state comparison | `tests/test_integration.py` | see RELEASES |
| WP9-02a | G3 null generators; TP-21/tool null-card controls | `nulls.py`, `control_runs.py`, `scripts/wp9_02_null_controls.py` | see RELEASES |
| WP9-02b | TP-47 C0 gate and TP-46 court controls | `gate_court_controls.py`, `scripts/wp9_02_gate_court_controls.py` | see RELEASES |
| WP9-02c | WP9-02 review R1 fixes (numeric validation) | `nulls.py`, `representations.py` | see RELEASES |
| WP9-02d | WP9-02 review R2: one numeric check (`numeric.finite_real`) | `numeric.py` and 8 modules | see RELEASES |
| WP9-02e | WP9-02 review R3: transform parameters, vault params, NaN leak-check hole | `representations.py`, `custody.py`, `slicing.py`, `nulls.py` | see RELEASES |
| WP9-02f | TP-81 and TP-82 (measure and declare) | `assumption_tests.py`, `scripts/tp81_tp82.py` | see RELEASES |
| WP9-02g | TP-81/82 review R1: IAAFT use restriction; TP-82 v2 metric | `controls.py`, `assumption_tests.py` | see RELEASES |
| WP9-02h | TP-81/82 review R2: IAAFT restriction mandatory by card | `controls.py`, `nulls.py` | see RELEASES |
| WP9-02i | path 1 built; TP-21/tool v1, v2 FAILED (FL-011) | `path1.py`, `scripts/wp9_02_path1_controls.py` | see RELEASES |
| WP9-02j | path 1 v3 (OD-S9-02): FAILED 0.66 (FL-011 open) | `path1.py` | see RELEASES |
| WP9-03 | graded planted-leak test TP-50 / TP-50.0 | `leakcheck.py`, `scripts/wp9_03_tp50.py` | see RELEASES |
| WP9-03b | review R1 (path 1 + TP-50): card v2, wording, validity limit recorded | docs, `path1.py`, `leakcheck.py` | see RELEASES |
| WP9-04 | traceability TP-04/60/61; ت-09 / م-10 passage | `knowledge_passage.py`, `docs/WP9-04_TRACEABILITY.md` | see RELEASES |
| WP9-05a | cross-layer malformed inputs; statement guard; dry-run apply | `statement_guard.py`, `charter.py` | see RELEASES |
| WP9-05b | review R1 (WP9-04/05a): seen bypass, use-point skips | `knowledge_passage.py`, `controls.py` | see RELEASES |
| WP9-02k | path 1 v4 (OD-S9-05): PASSED all five controls; FL-011 closed | `path1.py`, `scripts/wp9_02_path1_v4.py` | see RELEASES |
| WP9-02l | path 1 v4.1 (review R1-01 of v4): exact constrained reference; PASSED; FL-011 closed | `path1.py` | see RELEASES |
| WP9-05 | engineering test report (draft); TP-11/TP-13 tests | `docs/WP9-05_ENGINEERING_TEST_REPORT.md` | see RELEASES |
| WP9-05c | `uses_events` gate for TP-09 (FD-01-D43 enforced) | `claims.py` | see RELEASES |
| WP9-05d | TP-30 re-ID measured and declared (FD-01-D44) | `reid.py` | see RELEASES |
Tests: 747 passed locally; CI (Ubuntu + Windows) is the merge gate.

## Next
1. Layers 4 and 5: done (WP8-05). Layer 6: done (WP8-06; FD-01-D12…D14). Layer 7: done (WP8-07;
   FD-01-D15…D17). Layer 8: done (WP8-08; FD-01-D18…D20).
2. Cross-cutting axis: done (WP8-09; FD-01-D24…D25).
3. Stage 9 opened by the founder (2026-11-17). Plan and gaps: `docs/STAGE9_PLAN.md`. Failure log:
   `docs/FL.md`. Done: WP9-01a (ledger-level end-to-end integration) and WP9-01b (G1: paths Z / G-Z / R,
   flows ت-03…ت-07, ت-18, R → Z refused; FD-01-D29). Founder chose discovery path 1 (OD-S9-01).
   WP9-02 part 1 done: null generators (G3) and TP-21/tool for 3 null cards (results in
   `docs/results/WP9-02_null_controls.json`; FL-007 failed then closed by v2, FD-01-D30/D31).
   WP9-02 part 2 done: TP-47 (C0 gate) and TP-46 (court) pass (`docs/results/WP9-02_gate_court_controls.json`).
   TP-81 / TP-82 measured and declared (`docs/results/TP81_TP82.json`, STAGE9_PLAN §6, §6.1); FL-009
   closed by the v2 metric (FD-01-D34); IAAFT use restricted at use points (review R1-01).
   Path 1 built (`path1.py`, card `docs/paths/PATH1_CARD.md`); v1–v3 failed (FL-011); v4 met the criteria but its reference
   left H0 (review); v4.1 PASSED all five controls (FD-01-D42; STAGE9_PLAN §7.2). FL-011 closed by v4.1. Heavy tests Linux-only (OD-S9-04).
   WP9-03 done: TP-50 (ت1–ت9) and TP-50.0 run (FD-01-D38); blind spots ت8 (≤ 0.03) and ت9 recorded in
   `docs/KNOWN_BLIND_SPOTS.md`.
   WP9-04 done: traceability of TP-04 / TP-60 / TP-61 (`docs/WP9-04_TRACEABILITY.md`); ت-09 / م-10
   built (`knowledge_passage.py`, FD-01-D39).
   WP9-05a done: malformed-input test; FL-013 (ledger written before a failing apply — critical, fixed)
   and FL-014 (validation gaps) fixed; FD-01-D40.
   WP9-05 report DRAFT: `docs/WP9-05_ENGINEERING_TEST_REPORT.md` — TP-30 re-ID measured and declared
   (FD-01-D44; above chance for every representation); TP-09 not built, reading FD-01-D43 accepted
   by the reviewer with the gate enforced in code (`uses_events` on every claim card). TP-11/TP-13 added.
   ChatGPT R2 on WP9-05: NO BLOCKER; R2-01 (TP-30 scope: not a Custody/Vault secrecy test) fixed in wording,
   Custody/Vault-drawn re-ID test deferred with trigger (D44 addendum). **B9 CLOSED by founder (OD-S9-06).** Open with the
   founder: CS-01-04 threshold; next stage not opened.
   Re-ID research programme (OD-S9-07): RIP-1 design v0.6 + code FROZEN (FD-01-D45, commit 206a0cd; ChatGPT
   R1–R6, final NO BLOCKERS; docs/audit/RIP_register.md). RIP-1 RUN DONE (one run, 2026-11-18): report docs/results/RIP-1_REPORT.md — current blindings
   do not hide identity in the synthetic world (A6 joint ≈ 1.0 for log_returns/tick_grid/volatility_time; level_residual
   strongest, asset 0.79–0.89); Δ in the ledger leaks the asset (0.75); isolation held. ChatGPT audit of the result: consistent,
   no re-run; wording fixed, reproduction attestation and independent re-score added. RIP-2 design v0.7 FROZEN (FD-01-D46, BUILD only); build on branch rip2/build, NOT merged: CI blocked by
   GitHub billing (FL-022); build reviewed (B-R3: NO BLOCKERS); RIP-2 RUN DONE once (OD-S9-09, branch rip2/run): report
   docs/results/RIP-2_REPORT.md; result audit NO BLOCKERS (3 MINOR doc items fixed) — RIP-2 CLOSED; RIP-3 DESIGN ONLY
   authorised (OD-S9-10): design v0.4 docs/research/RIP3_DESIGN.md FROZEN (FD-01-D47, sha256 efb7e1631547…, final review NO BLOCKERS);
   BUILD authorised (OD-S9-11, floors confirmed): branch rip3/build (not merged) — code src/xauusd_swarm/rip3.py, tests,
   build notes, IC report. BUILD checks (development seeds only): B1 attempt 4 PASS 10/10 (case 10 by the bounded block
   method IC3-22; 50-digit check B1-HP passes), B2 attempt 3 PASS 768/768, B3 FAILED (FL-030), B4 PASS. DCR-01 drafts
   v0.5 / v0.5r2 written, then NOT ADOPTED by the founder (OD-S9-12): the frozen v0.4 governs, no δ, acceptance rules
   unchanged; FC-4 expected for M3–M6 if the RUN confirms it. Reviews R-B1, R-B2: R-B2-02 CLOSED (founder accepted the
   B1-HP docstring fix in 61eff1b); R-B2-03 decided by OD-S9-12.
   **RIP-3 BUILD ACCEPTED** by the reviewer (2026-11-23, main 1195603, tree ddb3ce9); founder decision OD-S9-14:
   no RUN authorisation, 6201 / 6301 not to be used. Final status of every item: RIP_register.md «FINAL STATUS»
   and FL.md «FINAL STATUS» tables (FL-030 DECIDED, all others closed).
   R-B3-01, R-B2-04, R-B1-01, R3B-00 CLOSED. FL-032 / R-B2-01 CLOSED (reviewer ACCEPTED, 2026-11-23): founder decision OD-S9-13 —
   tree-equivalent CI in the public sandbox repo XAUUSD-Swarm-CI-Sandbox, green on Ubuntu and Windows for 155b00f,
   61eff1b, 5eeb005 (evidence: docs/results/rip3_build/test_runs/FL032_sandbox_ci/). CI on the private repo is still
   blocked by billing: every later commit gets CI the same way (parentless snapshot of its tree, unchanged workflow),
   and rip3/build was merged into main (1195603) after green sandbox CI on its head ad41547; later merges need the same. RUN needs its own
   authorisation; 6201 / 6301 unused; no «READY TO RUN».
   Delivery point verified read-only (OD-S9-15, 2026-11-23): main 775ce2b, tree eb1bbe0; sandbox run 45130818597
   (snapshot d4ea095) green on Ubuntu and Windows in two attempts, 884 each — CI equivalent to that tree. Record:
   docs/results/handoff_verification_2026-11-23/VERIFICATION.md (differences found there are open, not fixed).
   Original evidence kept in the private repository, not published. FL-033: process error (push before the full suite finished).
   Order: RIP-1 Custody/Vault test → RIP-2 diagnosis → RIP-3 alternatives → RIP-4.
   ChatGPT review of WP9-01: R1 answered (WP9-01c), R2 answered (WP9-01d), `docs/audit/WP9-01_register.md`.
4. Do not build on the 12 assumptions without planned tests (WP7-04 §11).

## Founder's local copy (Windows)
- `E:\XAUUSD SWARM\repo` (moved from `C:\XAUUSD_SWARM_BUILD` on 2026-11-17; files verified by SHA-256,
  git fsck ok, HEAD 19bd1c35…; environments rebuilt from the lock files; 317 passed, 1 skipped there).
- `E:\XAUUSD SWARM\packages`: WP8-01 package 02 ZIP (5b4622b4…) and its extracted copy.
- This local repo has its own history from WP8-01 (no GitHub remote); GitHub `main` is the reference.

## Pending on the founder
- WP8-01 is done (package 02, founder's Windows run 2026-11-16; RELEASES.md).

## Open items (do not treat as decided)
- Axis (updated in Stage 9): controls RUN for null cards (TP-21/tool), C0 gate (TP-47), court (TP-46),
  path 1 (TP-21/tool: v1–v3 failed, v4 passed), plus TP-81/TP-82; time_reversal and zero_cond_mean have
  no matrix row (test procedure / model family undefined), so their use is refused (no row → no use); NOT built: TP-20 (distinguisher, not chosen),
  TP-50 leak types; audit schedule undefined.
- Layer 8: null generators and the sign-null family computations (N-a/N-a′/N-b) are not built
  (assumption tests TP-82, TP-83, TP-90); "justified" has no mechanical criterion; change-point via
  path ج (س 2211) not built; audit-sample size rule for blind rediscovery not in the sources; null
  validity now cites recorded control results (controls.py, FD-01-D21); the rest of the
  controls axis (per-tool matrix, governance audit, control code) is next.
- Layer 7: discovery engines themselves are not built (minds' own components); convergence and
  influence criteria and checkpoint dates (م-04 #3–#4, CS-04-13); null-card field list (§18.1 #6 not
  in the reference copies); blind cells not built before "proof of need" (ق-07); no path-retirement
  procedure (س 758 gives only a keep rule); ΔL|G analysis has no thresholds (D-01).
- Layer 6: the three budgets have no units in the sources (س 539) — gates and separation only;
  adequacy criteria / detectable-effect method are data; Reusable Holdout deferred (س 616); stop
  state undefined (س 617); R share and FWER/FDR [لاحق] (س 610, 618); Forward commitment (CS-03-05).
  TP-88 run for Holm/FWER only; its FDR part waits for an FDR procedure and the FWER/FDR decision.
- Layers 4–5: no project C0 rule exists (founder creates them, ق-11); slice count/size, embargo
  length and latency values are data (CS-03-07); C5 pending (س 426); Forward undefined (CS-03-05);
  block-level uncertainty for dependence is left to layer 8.
- A/B family structure and FWER/FDR: each family's freeze is blocked until a recorded decision
  exists (`court_policy_decided`). Only Holm/FWER is implemented.
- Importance rule: none («غير محدد: قاعدة الأهمية لم تُجمَّد»).
- CS-01-04 (announced re-ID threshold) and the allowed representation sets: open; G-Z release HARD-LOCKED.
- مع-54 (automatic lineage capture): "automatic" is a declared, signed attribution only.
- Classification into the 12 knowledge classes: no authority defined; records stay unclassified.
- OS-account separation for custody (key, vault, package store): a deployment requirement.
