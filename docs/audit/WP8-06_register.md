# WP8-06 audit register (ChatGPT independent review)

Round R1 — 2026-11-17 — reviewer verdict: NO BLOCKERS, 1 MAJOR + 1 MINOR (reviewed main @ 0811362;
did not run tests).

| ID | Severity (reviewer) | Finding | Status | Fix |
|---|---|---|---|---|
| R1-01 | MAJOR | Final claims could be opened one by one before the unit was marked opened (partial exposure, س 551–552) | FIXED | A claim can never be opened on a Final slice by itself (`claim_opened` refused there). The founder-signed `final_opened` is ONE ledger entry that opens every batch claim, after running every layer's opening checks (claims charter, custody, slicing, court); a partial or forged batch is refused and nothing is opened. Tests: `test_final_opened_once_all_claims_together_atomically`, `test_final_opening_runs_every_layer_check` |
| R1-02 | MINOR | TP-88 registration test did not pin the hash | FIXED | asserts equality with `fb7d0da1…26d5` (RELEASES WP8-06) |


Round R2 — 2026-11-17 — reviewer verified R1-01 and R1-02 closed at 9ec6dfb; one new MAJOR.

| ID | Severity (reviewer) | Finding | Status | Fix |
|---|---|---|---|---|
| R2-01 | MAJOR | the founder's signature did not cover the opening manifest (appended outside the signed statement) | FIXED | the manifest (claim, slice, card version + hash per claim) is inside the founder-signed `open_final` statement; any unsigned field is refused; `final_manifest()` builds it for signing; the validator re-checks it against fresh state. Tests `test_r2_01_*`: unsigned manifest refused; altered statement fails the signature; signed wrong card binding refused; signed non-primary slice refused; ledger length and openings unchanged after each refusal; the applied manifest equals the signed one |

Self-check (same kind, my layers 4–6): every other event in inventory.py, slicing.py and evidence.py is a
fully signed statement with no unsigned operative fields. Observation outside this scope (not
changed): `claim_opened` and `slice_consumed` (WP8-02) carry no signature by design; Final openings
now go only through the signed `final_opened`.


Round R3 — 2026-11-17 — reviewer: NO BLOCKERS; R2-01 closed at ecd6fc1; one MINOR (test coverage).

| ID | Severity (reviewer) | Finding | Status | Fix |
|---|---|---|---|---|
| R3-01 | MINOR | no separate tests for `version` or `claim_id` tampering inside a signed manifest | FIXED | `test_r3_01_*`: version raised, version lowered, claim swapped for one outside the batch, same claim twice, bindings crossed between claims — each refused with ledger length and Final openings unchanged; the correct manifest then opens exactly the batch |

OPEN COUNT: 0

Closure — 2026-11-17 — reviewer (ChatGPT) checked main @ a95398b: R3-01 present; no remaining
BLOCKER/MAJOR/MINOR. Verdict: NO BLOCKERS; WP8-06 review closed. Reviewer's stated scope: source,
test and release record only; tests and CI not run by the reviewer; closing WP8-06 opens no real
data, Stage 9 or G-Z and changes no other gate.
