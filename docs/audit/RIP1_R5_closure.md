# RIP-1 — closure report for review R5 (completeness of the attacker set)

Synthetic only; no test set exists; nothing frozen; RIP-1 design and scope unchanged.

## Finding
R5-01 (MAJOR): `validate_predictions()` checked that attacker names were allowed but not that every registered
attacker was present; `A5-f:` accepted any field name.

## Fix (`src/xauusd_swarm/rip1_attack.py`, `src/xauusd_swarm/rip1.py`)
1. `LEDGER_FIELDS`: frozen tuple of the 11 fields a `params_fixed` entry exposes (entry seq/prev/digest + derived
   seq rank, signer, signature, and the statement written by `rip1.run`: action, nonce, family,
   params_commitment, delta).
2. `expected_attackers(view, scenario, rep)`: frozen set per view × scenario × representation. V0 S-ind:
   A1, A2, A3, A6; V0 S-pool: A4a, A4b, A6; V1 (all scenarios): A5-delta, A5-all, A5-comb, A6-V1 and A5-f for the
   10 non-Δ fields. Unknown view, scenario or representation raises.
3. `validate_predictions`: scenarios exactly `SCEN`; per scenario the attacker names must equal
   `expected_attackers(...)` exactly (missing and unexpected names both refused, with their names).
4. A5-f is derived from `LEDGER_FIELDS`, not from the data: `predict` uses the frozen list and stops if a ledger
   row exposes another set of fields; `run()` checks the real snapshot against the list before any V1 run.
5. The same validation is applied in `reproduce_in_sandbox` (to the reproduced output and to the committed
   one) and in the CI recomputation test.

## Tests (`tests/test_rip1.py`)
| Requirement | Test |
|---|---|
| frozen, complete set per view × scenario × representation | test_expected_attackers_are_frozen_and_complete |
| deleting ANY registered attacker refused (every view × representation × scenario × attacker) | test_validate_refuses_each_missing_attacker_and_any_unregistered_name (10 cases) |
| unregistered A5-f name (`A5-f:entry.bogus`), A5-f on Δ, unknown name, attacker of another scenario refused | same test |
| renamed / missing / extra scenario, groups of another scenario, wrong view or representation refused | test_validate_refuses_renamed_missing_or_extra_scenarios_and_groups |
| frozen field list equals what custody actually writes | test_frozen_ledger_field_list_matches_what_custody_writes |
| validation applied to reproduction | reproduce_in_sandbox (code); test_rip1_reproduces_committed_result (CI recomputation) |

## Results
- tests/test_rip1.py: 32 passed, 3 skipped (no committed RIP-1 result). Against a throwaway smoke result (n = 128):
  35 passed, incl. the sandboxed reproduction with the new validation (10/10 identical) and the altered-result test.
- Smoke run: 260 result rows (52 per representation), all probes passed, ledger scan passed.
- Full suite (local, as root, incl. heavy): 779 passed, 3 skipped (the RIP-1 reproduction tests; no committed result).

## Not changed
RIP-1 design, attackers, scenarios, sizes and scope: unchanged.
