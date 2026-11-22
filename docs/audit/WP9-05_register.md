# WP9-05 (draft report) — review register (ChatGPT)

| ID | Severity | Item | Status | Resolution |
|---|---|---|---|---|
| R1-01 | BLOCKER (for B9) | TP-30 re-ID accuracy per representation not measured | FIXED | measured once under FD-01-D44 (pre-registration commit 129d9f1), results docs/results/WP9-05_TP30.json, report §5a. Design with the reviewer's minimum conditions (answer C): balanced K × P candidates with no leaking names/order; independent development and blind test sets with independent blinding draws; feature set covering distribution, dependence, spectrum, volatility/extremes and shape/sequence; a third independent attack (direct series matching after normalisation); per representation top-1 accuracy, confusion matrix, chance level, 95 % interval with the right resampling unit (parameter family); attack run by an independent reid_checker without parameters or keys; no threshold, no post-hoc changes. |
| R1-02 | MAJOR (gate) | TP-09 not-applicable reading needs a code gate | FIXED | mandatory boolean `uses_events` on every claim card; refused if missing / not bool; `true` refused while TP-09 is not built (`claims.TP09_BUILT = False`); frozen with the claim identity in both directions. Tests: test_uses_events_is_mandatory_and_boolean, test_event_based_claim_refused_until_tp09_is_built, test_uses_events_frozen_across_versions. Limit stated: the classification is a signed declaration; automatic detection of event use is undefined. |
| R1-03 | — | TP-13.09 stays [معلّق] | ACCEPTED | unchanged |
| R1-04 | — | report-reference test proves references only | ACCEPTED | stated in the report |
| R1-05 | — | results synthetic only | ACCEPTED | stated in the report |

## Round 2

| ID | Severity | Item | Status | Resolution |
|---|---|---|---|---|
| R2-01 | MAJOR | TP-30 does not test Custody/Vault blinding integration; seeds and generator are public | FIXED (scope) + DEFERRED (test) | report §5a scope paragraph and §6; D44 addendum. Custody/Vault-drawn re-ID test deferred with trigger: before any operational reliance on re-ID results or any real-data stage. TP-30 not re-run (as requested). |
| R2-02 | MINOR | same-family pooling not measured | ACCEPTED | §6: not to be read as safe from the independent-sample result |
| R2-03 | MINOR | language-mind attacker, TP-31, TP-33 not run | ACCEPTED | §6: TP-30 is not a test of every attacker or output |
| R2-04 | MINOR | TP-09 relies on the signed declaration | ACCEPTED | §6 enforcement limit, as in D43 |
| note | — | reviewer cited 738 passed | CORRECTION | the WP9-05d run was 747 passed (full suite incl. heavy); CI green on both OS at 401a5a8 |
