# WP8-08 audit register (ChatGPT independent review)

Round R1 — 2026-11-17 — reviewer: 1 MAJOR, no BLOCKER (reviewed main @ ac3b065; did not run tests).

| ID | Severity (reviewer) | Finding | Status | Fix |
|---|---|---|---|---|
| R1-01 | MAJOR | null validity accepted two free-standing SHA-256 strings, not linked to any recorded control evidence | FIXED | controls registry (`controls.py`): controls registered before results, one result per control by the court operator; `null_validity_recorded` cites `control_results` only, each recorded, targeting that null model, ≥1 positive and ≥1 negative, all passed; any extra hash field refused (FD-01-D21). Tests `test_r1_01_*`: free hashes, unrecorded id, one polarity only, other target, failed result, duplicates — all refused with no validity recorded; registry rules |

Self-check (same kind): no other gate in layers 4–8 grants a permission on an unverified hash. Documentary
hashes remain where they record, not authorise (stage-1 evidence, replication evidence, path lineage
reference).


Round R2 — 2026-11-17 — reviewer verified R1-01 closed at 92c969e; one new MAJOR.

| ID | Severity (reviewer) | Finding | Status | Fix |
|---|---|---|---|---|
| R2-01 | MAJOR | a control result "pass" was not tied to the observation, the registered code or the registered world | FIXED | registration fixes impl hash, world hash and a structured expectation; result must carry the same hashes, a structured observation and its hash; pass/fail is recomputed and must match; `run_control()` refuses other code/world and non-deterministic code; `reverify()` re-executes (FD-01-D22). Tests `test_r2_01_*`: pass not following, free-text observation, wrong evidence hash, wrong impl, wrong world, missing metric — all refused with no result recorded; bad expectation shapes refused; non-deterministic control refused; reverify true on the registered world, false on another |

Stated limit: the ledger cannot re-execute (it holds no code or world); a fabricated observation is caught by reverify().


Round R3 — 2026-11-17 — reviewer verified R2-01's parts at 06c9b13; one MAJOR remained.

| ID | Severity (reviewer) | Finding | Status | Fix |
|---|---|---|---|---|
| R3-01 | MAJOR | re-execution (`reverify`) was optional; a fabricated but self-consistent observation could support null validity | FIXED | `control_result_reverified`: an auditor independent of the recorder re-executes registered code on the registered world and records match/mismatch bound to the hashes (verdict must follow); `validity_evidence` requires a match and no mismatch for every cited result (FD-01-D23). Tests `test_r3_01_*`: validity without attestation refused; recorder or non-auditor cannot attest; other code refused; duplicate attestation refused; fabricated observation → mismatch → validity refused; forged "match" refused |

Stated limit: no cryptographic proof of execution; operator–auditor collusion is outside what the ledger can detect.

OPEN COUNT: 0

Closure — 2026-11-17 — reviewer (ChatGPT) checked main @ c6f7184: R3-01 fixed; no remaining
BLOCKER/MAJOR/MINOR. Verdict: NO BLOCKERS; WP8-08 review closed. Reviewer's stated scope: source,
tests, audit register, FD-01-D23 and release record; tests and CI not run by the reviewer (GitHub
status query returned empty); collusion and the absence of a cryptographic proof of execution are
the declared limits; null generators, N-a/N-a′/N-b and the rest of the controls axis remain open;
no data, Stage 9 or locked gate opened.

Self-found after closure (same kind as the WP8-08c test fix): a second test (`test_court_knowledge.py`)
used the 2-byte plaintext marker b"T1" against random ciphertext and failed once by chance (CI run
44044878907). All ciphertext-marker assertions were searched; this was the last short one; replaced
by long markers. No production code changed.
