# WP9-01 (WP9-01a + WP9-01b) — review register (ChatGPT)

| ID | Severity | Item | Status | Resolution |
|---|---|---|---|---|
| R1-01 | MAJOR | layer (أ) admission into Z does not prove the item came from R | FIXED | `knowledge_a_registered` must cite `origin_message_sha256` of a recorded R → layer-10 message (ت-18), and the item IS that message (content hash = message hash); G-Z messages and other content refused; admission re-checks the R origin. Stated limit: R messages are founder-signed while the R role is undefined, so the proof is "recorded as R output". Tests `test_r1_01_*`. |
| R1-02 | MAJOR | `knowledge_a` admission accepts extra fields | FIXED | every PathsLayer statement has a closed, typed field set (`SHAPES`); extra fields refused in all branches. |
| R1-03 | MAJOR | replay test compares a hand-picked snapshot | FIXED | `full_state()` compares EVERY attribute of every layer (except the Governance back-reference) plus Governance's own state; refuses to run if a layer holds non-data state it would skip; sensitivity test (equal, then one change → unequal). |
| R1-04 | MINOR | `guarded()` misses refusals raised as TypeError | FIXED | closed typed shapes make malformed input a GateError before use (e.g. a list as a direction); programming errors are still not swallowed. Tests `test_r1_04_*`. |
| S1-01 | self-found | same `guarded()` pattern in `discovery.py` (catches GateError/AuthError only) | DEFERRED | not verified whether malformed input can crash other layers; a cross-layer malformed-input test is added to the Stage 9 plan (before WP9-05). |
| S1-02 | self-found | CI evidence not independently verifiable by the reviewer | NOTED | run ids and URLs are listed in RELEASES; the reviewer can open `https://github.com/mulaalig87-ops/XAUUSD-Swarm/actions/runs/<id>`. |
| R2-01 | MAJOR | `full_state()` compared nested objects (CharterVersion, Rule) by type only; `hidden` check was top-level only | FIXED | `norm()` is recursive at every depth: dataclasses compared field by field, any other object at any depth raises TypeError (nothing compared by type alone). The pipeline now registers a Rule so both types are present. Tests: a changed field inside a nested CharterVersion / Rule (same type) is detected; unknown object at depth refused. Mutation check: a type-only dataclass branch makes 2 tests fail. |

**Closed 2026-11-17: ChatGPT R2 verdict "NO BLOCKERS" on main @ d7f7df9 (scope WP9-01 only).** S1-01 stays
deferred (cross-layer malformed-input test before WP9-05). Reviewer notes: test counts and CI are
Claude's reports (CI run URLs listed in RELEASES); no gate opened.
