# Founder decisions recorded in the build repository

## FD-01 — 2026-11-16 — Delegation of merging and of decisions to Claude

Founder (Ali, project owner), verbatim:

> «أضف ملف GitHub Actions للمستودع. يشتغل تلقائياً واكمل كل الاختبارات.
> انت اكتب الاكواد والاختبارات وكل شيء في GitHub واكمل وادمج وحدك قد اذنت لك. كل شي ادمجه انت حتى قرارات الحوكمه.
> انا المالك للمشروع علي اقر بتغيير سياسة المشروع و اوكل كلود بالدمج والتصرف بما يخدم المشروع وتسريع انجازه نيابة عني وبهذا اشهد امام القانون.»

Effect, as applied by Claude:
1. Claude writes the code and the tests, and merges into `main` itself (`--no-ff`, with a release
   record). Merging no longer waits for ChatGPT approval.
2. Automated gate: `.github/workflows/tests.yml` runs the full suite on Ubuntu and Windows,
   Python 3.13, on every push and pull request. Claude merges only when the suite passes.
3. ChatGPT review stays available as an independent check but no longer blocks a merge.
4. Governance decisions: Claude may decide them on the founder's behalf. Each one is recorded here
   as «⟦قرار Claude بتفويض المؤسس، FD-01⟧» with its reason and its source references.
5. Kept by Claude unless the founder says otherwise explicitly, because these steps cannot be
   undone:
   - opening real gold data (OD-10), which consumes slices;
   - the pilot run (OD-11);
   - releasing G-Z output to language minds (§26 غ-03).
   Claude prepares each of them fully and asks the founder once, in one message.
6. Unchanged: no ORACLE INFINITY access or mixing; no reuse of N0/V2.x code; no claims of work or
   tests that were not done; the frozen candidate and the Stage-4 index stay frozen.

## FD-01 decisions taken in WP8-05 (layers 4 and 5) — 2026-11-16

Each is «⟦قرار Claude بتفويض المؤسس، FD-01⟧». None opens data, runs a pilot or releases G-Z output.

| ID | Decision | Reason | Source |
|---|---|---|---|
| FD-01-D01 | Real data is hard-locked in code (`inventory.REAL_DATA_LOCKED`). An inventory needs a founder-signed permission per dataset (`permit_inventory`) and is recorded by custody only. | Inventory of real data touches raw gold data; that gate stays with the founder. | م3-02؛ ق-10؛ FD-01 §5 (OD-10) |
| FD-01-D02 | "Inventory and deterministic transforms before blinding" is enforced as: once a custody decision (blinding parameters) exists for any slice of a dataset, no new deterministic transform can be frozen for it. | The candidate gives the order, not the mechanism. | سجل 7 §13 #14؛ ت-02 |
| FD-01-D03 | Capability table "+" read cumulatively: a row needs its own fields and those of every row above it. Fields = raw inventory fields plus outputs of frozen deterministic transforms. | Strictest reading (same rule as ruling F-3). Revisable by a later decision. | س 415–425 |
| FD-01-D04 | Slice boundaries use calendar time or observation count only; a custody decision is accepted only for a slice in a frozen plan, with the plan's boundaries. Forward cannot be planned. | "Measures that carry no results"; ties layer 3 to layer 5; Forward commitment is undefined. | س 431؛ صل-26؛ CS-03-05 |
| FD-01-D05 | Split design and rules are recorded per claim, signed by the founder, before the claim is opened on any slice ("before freezing" = before the opening binds the card). | No recorder is named; the founder already signs the claim card. | س 481؛ claims layer |
| FD-01-D06 | Station limits: Final → design A only; C → Discovery only; B → Discovery or Validation (A preferred in Validation, B not forbidden there by the text). | Table text; only C is explicitly forbidden in Validation. | س 471–475 |
| FD-01-D07 | Estimates of estimated transforms and C0 results are recorded by custody; estimates only from a Discovery slice of the same dataset. | ق-10 makes custody the executor of layer-4 operations; ق-11 makes custody the C0 recorder. | س 399؛ ق-10؛ ق-11 |
| FD-01-D08 | A shared group with any member in evaluation is removed from training; it is never added to evaluation. | "One partition" without moving samples into evaluation. | س 478 |
| FD-01-D09 | C0 rules must be recorded before any claim is opened on a slice of their dataset. | "لكل قاعدة C0، قبل الفتح". | سجل 7 §13 #15 |

## FD-01-D10 — 2026-11-16 — WP8-01 package 02 replaces the lost approved package

«⟦قرار Claude بتفويض المؤسس، FD-01⟧»
- Fact: the approved WP8-01 ZIP (SHA-256 afcb45a4…) is not on the founder's machine (founder,
  2026-11-16: «الحزمة غير موجودة على جهازي»). Its content is the baseline commit 98ead41.
- Fact: that content would fail on Windows: `test_no_unsafe_fallback_when_primitive_missing` is
  POSIX-only (fixed in f0ab631; see CI run 43945691762).
- Decision: WP8-01 package 02 = `git archive` of `main` at the commit named in RELEASES.md, folder
  prefix `XAUUSD_SWARM_BUILD/`, run with the same `scripts/wp801_setup.ps1`. Its ZIP hash is recorded
  in RELEASES.md. Package 01 (afcb45a4…) is superseded, not edited.
- Reason: same setup procedure and rules; content already green on Windows CI; runs all current tests
  on the founder's machine.

## FD-01-D11 — 2026-11-17 — Implementation binding for transforms and C0 tests (review R1-03, R1-04)

«⟦قرار Claude بتفويض المؤسس، FD-01⟧»
- A frozen transform carries `impl_sha256` (SHA-256 of the implementing function's qualified name and
  source). Applying it with any other implementation is refused; each application records the hash.
- A founder-approved C0 rule carries `test_impl_sha256` beside the five template fields (§13 #15);
  results produced by another implementation are refused. The template itself is unchanged.
- Lambdas and functions without retrievable source are refused (no stable identity).
- Limit: the hash covers the function's own source, not modules it calls.
- Reason: ChatGPT review R1 (MAJOR): the record must prove that what ran is what was frozen/approved.
- Source: س 399؛ ق-11؛ سجل 7 §13 #14، #15.

## FD-01 decisions taken in WP8-06 (layer 6, evidence economy) — 2026-11-17

Each is «⟦قرار Claude بتفويض المؤسس، FD-01⟧».

| ID | Decision | Reason | Source |
|---|---|---|---|
| FD-01-D12 | Passage to the confirmation gate is a founder-signed submission per Final unit (claims, path, screening slices; optional `branch_of`). It is final: one per unit, nothing removed or added. Exclusion rules, slice merges and the Final opening are founder-signed too. | The sources name the gates and conditions, not who submits; the founder already signs claims, designs and court rules. | س 540–546, 574, 651؛ WP7-05 §6.4 ("who freezes: undefined") |
| FD-01-D13 | The adequacy report is recorded by custody; one per unit; never redone. | It is computed from Final data before opening; only custody touches raw data. | س 352, 526, 629–646 |
| FD-01-D14 | "Inadequacy is a result": an inadequate report is recorded and Final is NOT opened on that unit. | Opening Final consumes it (س 553); opening on an inadequate report would spend it without a valid test, and re-reporting to pass would be the forbidden reduction (س 643). | س 526, 643, 646 |

Note (no new decision): the court treats a test instance registered after the claim was opened on ANY
slice as descriptive (WP8-04, س 700/703, strict reading). So a claim's Final test instances must be
registered before its first (screening) opening. Layer 6 relies on this.

## FD-01 decisions taken in WP8-07 (layer 7, discovery system) — 2026-11-17

Each is «⟦قرار Claude بتفويض المؤسس، FD-01⟧».

| ID | Decision | Reason | Source |
|---|---|---|---|
| FD-01-D15 | Every registered discovery path, the three named ones included, carries a path card and a generalisation test (designed without sealed-world access) and a lineage reference; paths, minds, channels, resource rules, queue rules, batches, null-card acceptance and panel consumption are founder-signed. | The text requires card and test for "each addition"; applying it to all paths is the strictest reading. No registrar is named; the founder already freezes configurations and rules. | س 756؛ ق-26؛ م7-13؛ ق-06؛ ق-16 |
| FD-01-D16 | The "two declared bounds" of a queue batch are count bounds: min_items and max_items, declared before admissions; admissions stop at the upper bound; the batch closes (freezing its elements and their computed order) only at or above the lower bound; nothing is released before closing. | Bounds that depend only on ledger state replay identically; time bounds would need a clock source the sources do not define. | ق-03 |
| FD-01-D17 | The queue order is never set by hand: it is always computed from the family's frozen ordering rule (sort keys from admission index, path, proposal id, mind; ties by proposal id). Refused attempts on layer-7 events (channel, pre-freeze access, code-integrity admission, …) are logged by the guard (court operator); a refusal record is accepted only if the attempt is actually invalid. | "No change of order except by a rule frozen in advance; every entry and order change recorded"; TP-60.x "refused and recorded". | م7-07 #2–#3؛ WP7-04 TP-60 |

## FD-01 decisions taken in WP8-08 (layer 8, falsification and confirmation) — 2026-11-17

Each is «⟦قرار Claude بتفويض المؤسس، FD-01⟧».

| ID | Decision | Reason | Source |
|---|---|---|---|
| FD-01-D18 | The five inference stages are founder-signed records per claim, each requiring the previous one; stage 2 needs C0 results for the dataset, null swaps and the temporal location; stage 3 assigns one justified basic null with an accepted card (N-c refused); stage 4 = the claim is in an opened Final unit; stage 5 = a separate claim on path د1/د2. Submission to the confirmation gate requires stage 3. | The sources fix the order and content, not the recorder; the founder accepts null cards at freezing (ق-06). | س 2169–2175؛ س 815–818؛ ق-06؛ §7 #11 |
| FD-01-D19 | Null validity is recorded per null model by the founder, citing positive- and negative-control evidence hashes; without it the claim's status is «لم يُختبر تأكيديًا لعدم توفر نموذج صفري (Null) صالح» and it cannot be submitted to the confirmation gate. The evidence itself will come from the controls axis. | "Validity by controls alone"; "no confirmatory test without a valid null". | ق-06؛ س 818؛ صل-131؛ WP7-05 §3 |
| FD-01-D20 | Blind-rediscovery deliverables are sealed by the discovery participant who made them and scored by the court operator with the registered criterion; replication outcomes are recorded by the court operator; the frozen drift scope lists the conditions under which it predicts failure, and only those make a failure "expected"; a law change is a founder-signed link from a NEW claim to the old one after a recorded failure. | The sources fix the rules, not the actors; the court operator already runs frozen code after sealing. | س 2195–2199؛ س 2209–2211؛ ق-14؛ م7-01 |

## FD-01-D21 — 2026-11-17 — Null validity from recorded controls (review R1-01 of WP8-08; amends D19)

«⟦قرار Claude بتفويض المؤسس، FD-01⟧»
- A controls registry (`controls.py`, start of the cross-cutting axis): the founder registers a control
  (target null model / tool / court, polarity positive or negative, expected outcome, synthetic-world
  hash) BEFORE its result; the court operator records ONE result per control (pass/fail, observed,
  evidence hash).
- Null validity cites only recorded control results that target that null model, at least one positive
  and one negative, all passed. Free-standing evidence hashes are refused. D19's "evidence hashes" are
  replaced by this.
- Reason: a validity record must point to evidence the ledger can verify (ق-06 "validity by controls
  alone"; س 818; س 2313).

## FD-01-D22 — 2026-11-17 — Verifiable control execution (review R2-01 of WP8-08; amends D21)

«⟦قرار Claude بتفويض المؤسس، FD-01⟧»
- A control is registered with its frozen implementation hash, its synthetic-world hash, and a
  structured expectation {metric, op (<=, >=, ==, between), value | low, high} — the comparison rule is
  fixed before the result.
- A result carries the implementation and world hashes (must equal the registered ones), a structured
  observation, and evidence_sha256 = hash of that observation; the validator recomputes pass/fail from
  the expectation and the observation and refuses any outcome that does not follow.
- Results are produced by `run_control()` (refuses other code or world; two runs must agree) and can be
  re-executed by anyone holding code and world with `reverify()`.
- Stated limit: the ledger holds no code or world, so a fabricated observation is caught by reverify(),
  not on replay.
- Reason: a "pass" must follow from an execution of the registered code on the registered world
  (ق-06; س 2313; م7-03).

## FD-01-D23 — 2026-11-17 — Mandatory independent re-execution of control results (review R3-01 of WP8-08; amends D22)

«⟦قرار Claude بتفويض المؤسس، FD-01⟧»
- A control result counts toward null validity only after an auditor (custody_auditor or
  governance_auditor), a different identity from the operator who recorded it, re-executes the
  registered code on the registered world and records a "match" attestation naming the result's impl,
  world and re-executed evidence hashes. The verdict must follow from comparing the hashes.
- A "mismatch" attestation makes the result unusable for null validity permanently.
- Reason: re-execution must be a condition, not an option (review R3-01); two independent parties
  executing the same frozen code is the same pattern as the custody vault attestation (WP8-03).
- Stated limit: no cryptographic proof of execution; collusion of operator and auditor is outside what
  the ledger can detect.

## FD-01 decisions taken in WP8-09 (cross-cutting axis: controls and governance audit) — 2026-11-17

Each is «⟦قرار Claude بتفويض المؤسس، FD-01⟧».

| ID | Decision | Reason | Source |
|---|---|---|---|
| FD-01-D24 | Control matrix rows are founder-signed (tool kind and id, ≥1 positive and ≥1 negative registered control targeting the tool, criterion with hash, cost metric). "Use" is enforced at five points: a discovery proposal through a path, the engines of a mind configuration, the basic null at stage 3, recording a C0 rule, and a court ruling. A row needs registered controls, not results ("none has been run", س 1444). | Rule R16 ("no tool used in Discovery or after without a row"); the sources do not list the points of use, so every point where a tool enters the pipeline is gated. | WP7-04 §2.1 (R16)؛ س 1442، 1444، 2313 |
| FD-01-D25 | The governance audit report is issued by the governance auditor; its procedural checks of layer 3 (role separation, custody decision before opening, decryption only on G-Z or after the seal, refusals return nothing, G-Z release locked) are recomputed from the ledger and must match; no scientific-verdict field is accepted; each planted case carries one of the three states and the report states that "not detected" is not proof of absence. The governance auditor cannot combine its role with custody, custody auditor, court operator, discovery or G-Z. | Procedural, independent report (س 374; §13 #1); separation (§13 #2; ق-05); three states (§13 #3). The check list is the layer-3 rules already implemented. | س 374؛ سجل 7 §13 #1–#3؛ ق-05 |

## FD-01 decisions taken at the start of Stage 9 — 2026-11-17

Each is «⟦قرار Claude بتفويض المؤسس، FD-01⟧».

| ID | Decision | Reason | Source |
|---|---|---|---|
| FD-01-D26 | From Stage 9, the release record (`docs/RELEASES.md` with file hashes) is written on the component branch itself, so one CI run (Ubuntu + Windows) covers code and record; the merge into `main` happens only after that run is green. The record names the branch head and CI run; the merge commit is read from `git log`. | Halves CI minutes, which are now paid beyond the free quota (FL-005); same evidence (hashes, run id, local test count). | Founder's billing setup 2026-11-17; CLAUDE.md workflow |
| FD-01-D27 | `docs/FL.md` is opened as the failure log required by plan 07 §3.0 rule 1; Stage 8 failures are reconstructed there from release records, Stage 9 failures are written when they happen. | §3.0 rule 1 names FL; it did not exist as a file. | plan 07 §3.0 |
| FD-01-D28 | Stage 9 gaps G1, G3, G4, G5 (`docs/STAGE9_PLAN.md` §3) are built under FD-01 as components derived from the architecture text; G2 (which discovery path) waits for the founder because the candidate leaves it [لاحق] (مع-74). | Do not invent what the sources leave open. | س 2322–2323; CLAUDE.md |

## Founder decision OD-S9-01 — 2026-11-17 — Discovery path for §18.2 (gap G2)

⟦قرار المؤسس⟧ Question (as asked): «القسم §18.2 يشترط «مسار اكتشاف واحد على الأقل مع ضوابطه»، والمعمارية
تقول «المرشح: المسار 1 أو 3» وتتركه [لاحق] (مع-74). أيهما نبني؟» Answer: **«المسار 1»** (Ali, 2026-11-17,
12:58 Baghdad). Path 1 = «الانتظامات التوزيعية» (س 752). Claude recommended it (deterministic, direct
positive/negative controls, output fits the court); path 3 can be added later with card and controls (س 756).

## FD-01-D29 — 2026-11-17 — Paths Z / G-Z / R: undrawn flows and undefined actors (gap G1)

«⟦قرار Claude بتفويض المؤسس، FD-01⟧»
- A flow between paths that WP7-02 does not draw (G-Z → Z, G-Z ↔ R) is refused. Reason: WP7-02 §6 «لم
  يُرسم اتجاه بلا سند»; refusing is the reversible choice (a later decision can open a flow).
- Every input into Z is admitted by custody, from a blinded representation (ت-03) or a layer (أ) item
  arriving from R (ت-07); transfers out of Z are recorded by custody after z_output_passed (ت-04).
- Undefined in the architecture, handled conservatively and flagged: layer-10 message types and their
  fields are founder-registered before use; layer (أ) items are founder-registered; the R sender role is
  undefined, so R messages are founder-signed until a role is defined; no R tool call is accepted.
- Gold-data observations cannot be registered or sent while OD-10 locks gold data.
- Source: س 352–357; CS-01-08; ت-03 … ت-07, ت-18; م-03 … م-06.

## FD-01-D30 — 2026-11-17 — TP-21/tool for the §11.2 null cards: statistics, worlds, criteria (pre-registered)

«⟦قرار Claude بتفويض المؤسس، FD-01⟧» Recorded and committed BEFORE the first run (مع-15: «بمعدلين
يُسجَّلان قبل التشغيل»). The architecture names each card's target quantity, not the statistic, the
worlds or the numeric rates, so these are design choices:
- Statistics and worlds per card: as in the docstring of `src/xauusd_swarm/control_runs.py`.
- Test per series: surrogate rank test with M = 19 surrogates, alpha = 0.05; n = 128.
- Repetitions R: full_shuffle 60, iaaft 40 (cost of pure-Python IAAFT), pair_shuffle 60.
- Criteria: positive (real effect) rejection rate >= 0.80; negative (null world) rejection rate <= 0.15
  (nominal 0.05; tolerance for Monte Carlo error at R = 40–60).
- Not run (open): time_reversal (test procedure undefined), zero_cond_mean (model family undefined),
  block_bootstrap (not a null; TP-81), TP-82 arm (b).
- A failed criterion is recorded in FL and is NOT fixed by changing these numbers after the run.

## FD-01-D31 — 2026-11-17 — TP-21/tool pair_shuffle_vol_blocks, version 2 (after FL-007), pre-registered

«⟦قرار Claude بتفويض المؤسس، FD-01⟧» The v1 positive control failed (FL-007; stays in FL). One redesign,
declared before running: the statistic is computed WITHIN each volatility state (the card's null is
«داخل حالة التقلب نفسها», س 830): for each block, |mean(|r_{t+1}| after s_t = −1) − mean(|r_{t+1}| after
s_t = +1)| divided by the block's mean size, only for t and t+1 in the same block; the block values are
averaged weighted by their number of pairs. Unchanged: worlds (lev = 1.6, states 1 and 3), n = 128,
M = 19, alpha = 0.05, R = 60, criteria (>= 0.80 positive, <= 0.15 negative). Both controls are re-run
as new control ids (`…-v2`). If v2 fails, the row stays without passing controls and the failure is
reported to the founder; no further redesign without his decision.

## FD-01-D32 — 2026-11-17 — TP-47 (C0 gate) and TP-46 (court): worlds and criteria, pre-registered

«⟦قرار Claude بتفويض المؤسس، FD-01⟧» Recorded and committed BEFORE the first run. Design in the docstring
of `src/xauusd_swarm/gate_court_controls.py`.
- TP-47: the three C0 detectors are synthetic fixtures exercising the gate, not project C0 rules (the
  founder's rules have no template, CS-03-04). Worlds: n = 300 quotes, k = 5 planted effects of one class
  (feed / processing / order) or none. Criterion per world: match == 1 (planted class → its state with the
  exact planted scope; every other rule → state 4; clean world → state 4 for all three).
- TP-46: court run as operated on one ledger; 3 claims, n = 200, sign-flip permutation p (B = 999), Holm
  alpha 0.05; real world: K1, K2 shifted by 0.4 sd, K3 none; null world: none. Criterion: match == 1
  (confirmed set = planted set). Stability: identical output on two runs plus independent re-execution.
- Each world is a single seeded world (not a rate): a chance false confirmation in the null world would
  count as a failure and be logged, not re-seeded.

## FD-01-D33 — 2026-11-17 — TP-81 and TP-82 designs, pre-registered before any run

«⟦قرار Claude بتفويض المؤسس، FD-01⟧» Committed BEFORE the first run. Full design in the docstring and the
`TP81` / `TP82` constants of `src/xauusd_swarm/assumption_tests.py`.
- Nature (WP7-04 §11): measure and declare, no numeric pass threshold; tolerance registered before
  running; a synthetic result does not show that the assumption holds in gold (س 1460).
- TP-81: mean; moving-block bootstrap percentile interval, nominal 0.95, B = 199; worlds iid, AR(1)
  phi 0.5, ARFIMA(0, d = 0.3, 0) (1000 MA weights); n = 400; b ∈ {1, 5, 10, 20, 40}; R = 200; declared
  "within tolerance" iff |coverage − 0.95| ≤ 0.03.
- TP-82: statistic acf1(x²); M = 19 IAAFT surrogates (20 iterations), alpha 0.05, n = 128, R = 40; arm (a)
  AR(1) phi 0.5; arm (b) patterns level (+2 sd at midpoint), var (sd ×2), spec (AR 0 → 0.8); profile
  windows 32, bands [1,4) and [4,16); "within tolerance" iff false-rejection rate ≤ 0.05 + 0.10;
  "profile reproduced" iff the mean profile distance ≤ 2 × the arm (a) mean profile distance (a design
  choice: the architecture names a pre-registered distance but no cut-off).
- Readings follow §11.1's separation of failures literally; a case §11.1 does not classify is declared
  as such.
- Before the run, a smoke check with other seeds and R = 2 is used only to catch code errors; its values
  are not reported or used.

## FD-01-D34 — 2026-11-17 — TP-82 profile metric v2 (after FL-009) and reporting changes, pre-registered

«⟦قرار Claude بتفويض المؤسس، FD-01⟧» Committed BEFORE the v2 run; design follows the reviewer's
recommendation (TP-82 review R1, answer 2).
- v2 metric: per series, the change vector "mean over second-half windows − mean over first-half windows"
  for each profile component (mean, variance, band powers [1,4) and [4,16)); the same for each IAAFT
  surrogate; distance = mean over components of |Δ_original − Δ_surrogate| / reference sd of that
  component. Reference sd: from an INDEPENDENT stationary calibration set (arm (a) process, 40 series,
  seed 8301), fixed before the run and not drawn from the series being judged.
- "Profile reproduced" iff the mean v2 distance ≤ 2 × the arm (a) mean v2 distance. §11.1's readings are
  then assigned with v2. v1 values stay in the results, labelled v1 (FL-009).
- Reporting (review R1-02, R1-03): arm (b) rates are named `rejection_rate_under_assumption_violation`;
  every rate and coverage carries its binomial standard error; arm (a) carries a note that
  `within_tolerance` at R = 40 is not proof of calibration. These change labels, not values.
- Everything else of FD-01-D33 unchanged (worlds, seeds, R, M, alpha, tolerances); the run is repeated
  with the same seeds, so arm rates must reproduce exactly.

## FD-01-D35 — 2026-11-17 — Discovery path 1 (P1-distributional): method, controls and criteria, pre-registered

«⟦قرار Claude بتفويض المؤسس، FD-01⟧» after the founder's choice OD-S9-01. The architecture names the path
only (index مك-91: «اسم فقط»), so the method is a design choice, recorded in `docs/paths/PATH1_CARD.md`
and `src/xauusd_swarm/path1.py` and committed BEFORE any run.
- Method: per-cell two-sample KS vs the rest; max-T over cells; null by circular rotation of labels
  (keeps the series' dependence); M = 49 rotations; alpha 0.05; n = 400; cells A, B, C in runs of mean
  length 50.
- Controls (TP-21/tool, WP7-04 §2.1): real — cell A returns ×1.8, rate of "A proposed" >= 0.80;
  spurious — stochastic volatility (log-vol AR(1) phi 0.98, sigma 0.25) independent of the labels, rate
  of "any cell proposed" <= 0.15; null — iid, rate of "any proposed" <= 0.15. R = 50 series per world.
- Generalisation test (card): the same three worlds at n = 800, mean segment 20 and 120: measure and
  declare.
- A failed criterion goes to FL; no change of these numbers after the run.

## FD-01-D36 — 2026-11-17 — Path 1 v2 null (after FL-011), pre-registered

«⟦قرار Claude بتفويض المؤسس، FD-01⟧» One declared redesign, as with FD-01-D31; v1 and its failure stay
recorded. The rotation null (v1) protected against volatility clustering but lost power because the real
effect contaminates the rotated null. v2 null: **permutation of the cell labels across label RUNS** —
run boundaries are kept, the series is kept, and the cell assigned to each run is permuted (M = 49
permutations). It is valid when the assignment of cells to runs is exchangeable given the run structure
(an assumption written on the card); it breaks exactly the link "this run's cell ↔ this run's returns".
Unchanged: statistic (per-cell KS vs rest, max-T), alpha 0.05, worlds (n 400, mean run 50, ×1.8, SV
phi 0.98 sigma 0.25, iid), R = 50, seeds, criteria (real >= 0.80; spurious and null <= 0.15),
generalisation worlds. If v2 fails, the path-1 row stays without passing controls and the founder
decides; no further redesign without his decision.

## Founder decision OD-S9-02 — 2026-11-17 — path 1 after FL-011

⟦قرار المؤسس⟧ Question (as asked): «فشل الضابط الموجب للمسار 1 مرتين: 0.28 في النسخة 1، ثم 0.00 في النسخة 2،
والمطلوب 0.80. هذا فشل حرج يمنع إغلاق المرحلة 9. كيف نكمل؟» Options: v3 pre-registered (recommended) /
pause path 1 / switch to path 3. Answer: **«نسخة 3 مسجلة مسبقًا (موصى بها)»** (Ali, 2026-11-17).
As offered: per-cell statistic instead of the max, Holm across cells, worlds and criteria unchanged; if v3
fails, stop and return to the founder.

## FD-01-D37 — 2026-11-17 — Path 1 v3 (under OD-S9-02), pre-registered

«⟦قرار Claude بتفويض المؤسس، FD-01⟧» Committed BEFORE the v3 run.
- Statistic: per-cell KS distance D_c vs the rest (no max).
- Null: rotation of the labels (v1's null, which passed the spurious-effect control), but each cell is
  compared with the null distribution of ITS OWN D_c (avoids v1's contamination of the max by the real
  effect, and v2's invariance of the max to renaming cells).
- Decision: Holm across the cells of one scan at alpha 0.05.
- M = 199 rotations (was 49): with 3 cells Holm needs p <= 0.0167; with M = 49 the smallest p is 0.02,
  so a rejection would be impossible. This is the only parameter change, made for attainability, before
  any v3 result exists.
- Unchanged: worlds (n 400, mean run 50, ×1.8, SV phi 0.98 sigma 0.25, iid), R = 50, seeds, criteria
  (real >= 0.80; spurious and null <= 0.15), generalisation worlds.
- Implementation: per-cell KS by one pass over the sorted series (`cell_stats(..., order)`), checked equal
  to the two-list KS on 30 random cases with ties before the run; v1 and v2 keep the original routine.

## Founder decisions OD-S9-03 and OD-S9-04 — 2026-11-17

⟦قرار المؤسس⟧ Question (as asked): «النسخة 3 من المسار 1 فشلت أيضًا: كشفت الأثر الحقيقي في 66% والمطلوب 80% (عند 400
مشاهدة). لكنها ضبطت الأثر الزائف والعالم الصفري، ووصلت 90% عند 800 مشاهدة (نتيجة معلنة لا معيار). كيف نكمل؟»
Answer: **«أوقف المسار 1 مؤقتًا»** (OD-S9-03). FL-011 stays OPEN and critical; Stage 9 cannot close for
B9 while it is open (plan 07 §3.0). Path 1 code, card and all results stay recorded.

⟦قرار المؤسس⟧ Question (as asked): «الفحص على GitHub صار يستهلك نحو 17 دقيقة محسوبة لكل تشغيل (قرابة 0.14
دولار)، لأننا نعيد التجارب الثقيلة على Windows. ميزانية 5 دولارات تكفي نحو 35 تشغيلًا. ماذا نفعل؟»
Answer: **«التجارب الثقيلة على Ubuntu فقط (موصى بها)»** (OD-S9-04). Implemented in `tests/conftest.py`
(marker `heavy`, skipped on Windows with the reason shown); all other tests still run on both systems.

## FD-01-D38 — 2026-11-17 — Graded planted-leak test TP-50 (ت1–ت9) and TP-50.0: design, pre-registered

«⟦قرار Claude بتفويض المؤسس، FD-01⟧» Committed BEFORE any run. Full design in the docstring and `TP50`
of `src/xauusd_swarm/leakcheck.py`.
- The lineage check's actor and procedure are undefined (مع-58). This component defines ONE check
  (automatic capture through `FeatureBuilder` + seven named rules); every lineage result measures that
  check only, and code that bypasses the builder is invisible to it.
- Statistical detection (س 1540): rejection rate of the E[s_t·h_t] = 0 z-test (alpha 0.05) on NULL worlds
  (iid returns, n = 600, tested slice the second half); R = 100 worlds per type.
- Per-type states (founder's three states, WP7-04 §4): "كُشف بفحص النسب" iff lineage detection rate ≥ 0.5;
  "كُشف إحصائيًا" iff rejection rate > 0.05 + 0.05; neither → "نقطة عمى معروفة". These cut-offs are design
  choices (the sources give none).
- ت8: weak partial leak at fractions 0.01, 0.03, 0.10, 0.30 → minimum detectable fraction (س 1536).
- ت9 included per WP7-04 §4 (founder CS-04-08 «يُدرج»); the candidate §12 still marks it not in force
  (تا4-02): both cited.
- Null worlds are iid only (no volatility clustering); this limit is declared.
- Success = a complete report (WP7-04 §4); undetected types are recorded as known blind spots, never as
  "no leak". Nothing here shows the absence of unplanted types (س 1543).
- Addendum (before the run): matrix row of the lineage leak check = positive control "TP-50 report
  complete" (== 1), negative control "TP-50.0 measured and declared" (== 1; the sources give no
  false-alarm threshold). Note: the lineage rules are deterministic per type, so lineage rates are 0 or 1
  by construction of this check; the informative measurements are the statistical rates and which types
  are invisible to the check.

## FD-01-D39 — 2026-11-17 — Knowledge 10 → 7 through layer 3 (ت-09, م-10): passage record and use check

«⟦قرار Claude بتفويض المؤسس، FD-01⟧» Found in WP9-04: ت-09's passage was only "enforced by absence" (no
event carried knowledge to a mind) and its tagging rule was not built. `knowledge_passage.py`: custody
records each passage of a knowledge row to a mind (tags copied from the row; blinded when the recipient
is Z); a proposal whose lineage names a knowledge row without a passage to that mind is refused (م-10).
Format of a knowledge reference in lineage `knowledge.seen`: "knowledge:<ruling_id>/<claim_id>" (a design
choice; the architecture gives no format). What blinding means for a knowledge row is «غير معرّف في
المعمارية» (flag required, not computed). Source: س 131; WP7-02 ت-09, م-10.

## FD-01-D40 — 2026-11-17 — Statement guard and dry-run apply (WP9-05a; FL-013, FL-014)

«⟦قرار Claude بتفويض المؤسس، FD-01⟧» (1) Every signed statement passes one shape guard
(`statement_guard.py`) before any layer validation: field roles recognised by the package's naming
(identifiers `*_id`/family/holder/slice/plan_id/null_model/null/basic_null; hashes `*sha256`; flags;
objects config/attempt/inventory; key-like to/tool_kind/epoch; no NaN/inf anywhere). (2) Every statement
is applied to copies of the state before it is appended (`Governance._dry_apply`), so an entry that cannot
be applied is never written. Reason: the append-only ledger must never hold an entry that breaks replay
(FL-013). Limit: recognition by field name; a field with an unusual name gets only its layer's own checks.
The suite-wide sweep is an audit tool (`tests/fuzz_plugin.py`); it bypasses signature checks for its
probes only.

## Founder decision OD-S9-05 — 2026-11-17 — path 1 v4 with a larger world

⟦قرار المؤسس⟧ Question (as asked): «بقي مانع واحد أمام إغلاق المرحلة 9: المسار 1 (FL-011). نسخة صالحة إحصائيًا (تبديل
الخلايا بين الفترات، لكل خلية على حدة، مع Holm) لا تستطيع رياضيًا أن تنجح بـ 400 مشاهدة (نحو 8 فترات فقط)، فتحتاج عالمًا
أكبر، وهذا تغيير بعد رؤية النتائج يُسجَّل صراحة. كيف نكمل؟» Answer: **«نسخة 4 بعالم أكبر (موصى بها)»**. Path 1 is
reopened (lifts OD-S9-03 for v4 only).

## FD-01-D41 — 2026-11-17 — Path 1 v4 (under OD-S9-05): design, pre-registered

«⟦قرار Claude بتفويض المؤسس، FD-01⟧» Committed BEFORE any v4 run. Code: `scan_v4`, `P1V4`,
`world_series_v4`, `run_p1_world_v4` in `src/xauusd_swarm/path1.py`.
- **Exchangeability hypothesis (review R1-01 of P1/TP-50):** given the run boundaries, the assignment of
  cells to runs is exchangeable and independent of the returns. Reference set: uniform random
  permutations of cells across runs (series and run boundaries untouched); Monte Carlo p-value per cell
  (1 + #{D_c(perm) ≥ D_c(obs)}) / (M + 1), M = 199; valid under H0 whatever the dependence of the returns
  (the series is never transformed). Holm across cells, alpha 0.05.
- **Change made after seeing results, declared:** n = 1600 (was 400) with the same mean run length 50,
  so a scan has about 32 runs instead of 8. Reason: with about 8 runs the smallest attainable per-cell
  p-value exceeds alpha/3, so no version can pass at n = 400. The v3 generalisation result at n = 800
  (0.90) was seen before this choice; v3 is not valid (R1-01), and v4 uses fresh seeds (9401+).
- **Worlds and criteria (unchanged criteria):** real (cell A ×1.8) rate of "A proposed" >= 0.80;
  spurious (stochastic volatility, as before), null (iid) and, per review R1-01, two further worlds —
  spurious_level (mean regime shifts independent of the labels) and null_heavy (iid Student-t(3)) — each
  rate of "any cell proposed" <= 0.15. R = 50 per world.
- **Generalisation (measure and declare):** the five worlds with mean run 20 and 120 at n = 1600.
- If v4 fails any criterion: stop, FL-011 stays open, return to the founder. v1–v3 stay recorded.

## FD-01-D42 — 2026-11-17 — Path 1 v4.1: reference set corrected to the stated H0 (review R1-01 of v4), pre-registered

«⟦قرار Claude بتفويض المؤسس، FD-01⟧» within the founder's decision OD-S9-05 (path 1 v4). The review was
right: v4's `run_permuted` shuffles the cells of the MAXIMAL runs freely, so adjacent runs receive the same
cell and merge; measured on the v4 worlds, 100 % of reference draws changed the run structure. The
reference set therefore did not match H0, and v4's p-values are not shown valid; v4's results stay
recorded and FL-011 stays OPEN until v4.1 is run.
- **Unit of exchange:** the maximal runs (the observable units; adjacent runs differ by definition).
- **H0 (v4.1):** given the run boundaries and lengths and the number of runs of each cell, every
  arrangement of the cells over the runs in which no two adjacent runs share a cell is equally likely,
  independent of the returns. (The synthetic label generator — i.i.d. uniform cells per segment, equal
  neighbours merged — satisfies it: the probability of a run-label sequence does not depend on which
  cells, only on the adjacency constraint.)
- **Reference:** exact uniform draws from that set by dynamic-programming counting
  (`_ConstrainedArrangements`), checked exactly uniform on a small case before the run; every reference
  sequence has the same runs, lengths, boundaries and per-cell run counts as the observed one.
- Unchanged from FD-01-D41: statistic, M = 199, Holm, alpha, R = 50, n = 1600, mean run 50, five worlds,
  criteria, generalisation worlds. New seeds (offset +1000) because the reference changed.
- If v4.1 fails any criterion: stop, FL-011 stays open, return to the founder.

## FD-01-D43 — 2026-11-17 — Reading of TP-09 (event protocol) for Stage 9

«⟦قرار Claude بتفويض المؤسس، FD-01⟧» TP-09 applies «عند استخدام الأحداث (نص V05)» (founder CS-05-09).
No component or claim in the build uses events (first observed, tie, observation process). Reading:
TP-09 is **not triggered** in Stage 9 and is reported as "not built, conditional" (WP9-05 report §3), not
as passed. Gate recorded: **before any event-based claim is registered, TP-09.1–09.3 must be built and pass
on synthetic worlds.** Reason: building an unused protocol now would test nothing that runs; claiming it
would be false. This reading is submitted with the WP9-05 report to the reviewer and the founder; the
founder can overrule it (then TP-09 is built before B9 closes).
**Enforced in code (WP9-05 review R1, answer B):** every claim card carries a mandatory boolean
`uses_events` (no default); `true` is refused while `claims.TP09_BUILT` is False; the field is frozen
with the claim identity (no change in either direction in a later version). Limit: the classification
is a founder-signed declaration on the card (part of its hash); an automatic test of whether a claim's
content uses events is «غير معرّف في المعمارية» (no code-level definition of an event-based claim).

## FD-01-D44 — 2026-11-17 — TP-30 re-identification measurement: design, pre-registered
⟦قرار Claude بتفويض المؤسس، FD-01⟧
**Source:** candidate س 158 («تُقاس الدقة، ويُعلن الناتج»), س 196, س 211; WP7-04 §3 (TP-30); WP9-05 review R1-01
(answer C, minimum design). Threshold CS-01-04 is open → no threshold, measure and declare.
**Design (code: `src/xauusd_swarm/reid.py`, spec `TP30`, committed in this commit before any test-set run):**
- Universe: 4 synthetic assets × 4 periods = 16 balanced classes, known distinct statistics; samples shuffled;
  the attacker gets bare number lists (no names, no order).
- Dev set (seed 3001) and test set (seed 3002), 25 samples per class each, n = 512 steps; every sample has
  its own independent blinding draw (one parameter family per sample → samples are the independent unit;
  Wilson 95 % over samples is valid). The same-family pooling scenario is not measured (declared).
- Threat model: the attacker knows methods and parameter distributions and has public unblinded data; it
  does not hold the drawn parameters or keys (interface: `attack(name, dev_x, dev_y, test_x)`). Role
  binding in the ledger (`reid_checker` independence) is enforced by custody.py and tested there; this
  measurement exercises the interface separation, not a signed ledger run (declared).
- Six representations (the six cards). activity_time: one update per step in this world, so it equals
  unscaled log returns (declared).
- Attackers fixed now: A1 1-NN on standardised features; A2 nearest centroid; A3 direct series matching
  (quantile function + log periodogram), independent of the feature set. Features cover distribution,
  dependence, spectrum, volatility/extremes and shape/sequence (module docstring).
- Report per representation × attacker: top-1 accuracy for asset (chance 1/4), period (1/4), joint (1/16);
  counts; Wilson 95 %; confusion matrices. Language-mind attacker: not run (not available).
- Development note (honest): before this registration a smoke run was made on other seeds (91/92) and small
  sizes to check the code runs; the test seed 3002 was not used. Sizes were then raised from 10 to 25.
- One run; no change after seeing the result. Result: `docs/results/WP9-05_TP30.json`, reproduced by a heavy test.

**FD-01-D44 addendum (2026-11-18, review R2-01):** the TP-30 result is limited to synthetic representations
with experiment-generated independent parameters; it is not a test of Custody/Vault parameter secrecy.
Trigger: before any operational reliance on re-ID results (and before any real-data stage), a re-ID test with
parameters drawn by Custody/Vault and an attacker without parameters or key is built and run.

## Founder decision OD-S9-06 — 2026-11-18 — Gate B9 closed
Founder (Ali), answering a closed question after ChatGPT round R2 on WP9-05 (NO BLOCKER; R2-01 fixed in wording):
**close B9 now with the limits declared.** Conditions carried forward, not waived:
- Custody/Vault-drawn re-ID test is required before any real-data stage or operational reliance on re-ID (D44 addendum).
- CS-01-04 re-ID threshold stays open (founder).
- TP-09 is built before any event-based claim (D43 gate).
- Deferred items TP-81/82 R3-01 and WP9-04/05a R2-01 keep their triggers.
- OD-10 (gold data), OD-11 (pilot) and §26 غ-03 are unchanged: nothing here opens them.

## Founder instruction OD-S9-07 — 2026-11-18 — Re-identification research programme
Founder (Ali): build the real re-ID test through Custody/Vault first, then diagnose the leak, then compare
hardening alternatives with their information cost, then re-measure under pre-registered protocols; treat it
as an independent research programme, not a fix to reach a pass. Present the design for review before any run;
ChatGPT audits each phase. Constraints: synthetic only; no gold data; OD-10, OD-11 and G-Z stay closed; passing
re-ID opens no gate; no change to frozen decisions without record and independent review; CS-01-04 stays open.
Plan and RIP-1 draft: `docs/research/REID_PROGRAMME.md` (v0.1, DRAFT, not frozen, nothing run).

## FD-01-D45 — 2026-11-18 — RIP-1 design and code FROZEN (pre-registration)
⟦قرار Claude بتفويض المؤسس، FD-01⟧
**Source:** founder instruction OD-S9-07 (register before running; independent review of each phase); ChatGPT
review rounds R1–R5 on RIP-1, final verdict «NO BLOCKERS — READY TO FREEZE» on the single-commit bundle
`206a0cd16e7e44421b883e72b32411cb4a31e77b` (reviewer verified the nine bundle hashes).
**Frozen:** `docs/research/REID_PROGRAMME.md` v0.6 §1–§3 (RIP-1) and the code at commit 206a0cd:
  - `src/xauusd_swarm/rip1.py` `7d04b40113d64a1e6a4c33fcf7f5e54d2955d7e9af41b002136dafa20ae9014a`
  - `src/xauusd_swarm/rip1_attack.py` `6d28758ed17ee2bc525251b280a24d2c8ea581d426d0c793d3638a0ca38d555e`
  - `scripts/rip1_attacker.py` `5ff355171a9a53682ebb3ed26df206548ddc3ef3218255bb4f3ae6987686ba69`
  - `src/xauusd_swarm/reid.py` `4b553a3cba79f3b03a387110ede2ba02d0102c4c242df967a1ee3a7e189ca4fb`
  - `src/xauusd_swarm/representations.py` `7ff8b95515401c2a74011cca9338ffb3cd67998ee91f9900aee494104c9dda4f`
  - `src/xauusd_swarm/numeric.py` `03d8449e2ae1681a5795559a53551b3c248357ac40f25356094468b437daa631`
  - `src/xauusd_swarm/custody.py` `d9155a4a595a49bfb7032914a19b6f49e79f966ada777177b2aff95cd1a68b54`
  - `tests/test_rip1.py` `05183dc020c18982f27e00477347a30abf48abe097bf1f8aa9605f0660485844`
  - `tests/helpers/rip1_evil_attacker.py` `5f273d83bed09262bbd7b29125a3b56bfa46cbcbb4a7973512b116506716f688`
  - `docs/research/REID_PROGRAMME.md` `c15a97802ee0672f0720a80814f2b55f2b79aa67fb87f0c44f321fbf45eac805`
  - `env/test.lock.txt` `225576985b2328cc5752a73d72d69b0a5d838330a428e4d30c30933ee5cdbe01`
**Rules from here:** one run of `xauusd_swarm.rip1.run` with the registered spec (no override); the test set is
generated by the CSPRNG inside that run; nothing in the design, code, attackers, sizes or criteria changes after it;
every result is reported, negative ones included; no threshold (CS-01-04 stays open with the founder). A failed run
goes to FL and is reported; a re-run needs a recorded decision and review. Synthetic only; nothing here opens OD-10,
OD-11, G-Z or any gate.

## FD-01-D46 — 2026-11-18 — RIP-2 design v0.7 FROZEN; BUILD authorised (not RUN)
⟦قرار Claude بتفويض المؤسس، FD-01⟧ — recording the founder's message of 2026-11-18 20:21 and the reviewer's verdict.
**Source:** ChatGPT full re-evaluation of RIP-2 v0.7 (bundle 31bbaff): «NO BLOCKERS — READY TO BUILD»; founder: BUILD
authorised under v0.7 only, with six conditions — no change to the frozen design without record and independent review;
no gold data; development / test / evaluation kept separate; no RIP-2 run before the code, tests and file hashes are
reviewed; no later gate and no RIP-3; every design-to-code difference documented, never fixed silently.
**Frozen design files (sha256):**
  - `docs/research/RIP2_DESIGN.md` `bee007da3bb4b2b87a236ac8ce31b125be81f604916b8e731c209dfe4dc24077`
  - `docs/research/RIP2_UVOL_DERIVATION.md` `ae48ea1d9c99243b31bcba1b0a6d2fa19e9027e4e93f16b6919c4fdf96f30a1b`
  - `scripts/rip2_uvol_verify.py` `836cd2b2e78d5d6f47964922d8f7c6008dccba333771a591efd7c7a694b13cc6`
**Approval scope:** BUILD only. RUN needs the code review and a separate go.

## Founder decision OD-S9-08 — 2026-11-18 — FL-023: exact level_residual likelihood in RIP-2; RIP-1 history preserved
Founder (Ali), after the reviewer's BUILD review of RIP-2 (8ce02e9, NOT READY TO RUN; B-R1-01..03):
1. RIP-2 keeps the exact wrapped-normal likelihood for level_residual (IC-12). It is a **deliberate methodological
   deviation** from the historical RIP-1 likelihood named in RIP-2 design §5, recorded in design addendum
   `docs/research/RIP2_DESIGN_ADDENDUM_A1.md` (the frozen design file is unchanged).
2. Historical RIP-1 results stay exactly as reported (docs/results/rip1/, RIP-1_REPORT.md). Nothing is overwritten
   or reinterpreted.
3. A corrected RIP-1 computation, if made, is a separate diagnostic with its own identifier, never mixed into the
   RIP-1 report: **RIP-1-D1** (`docs/results/RIP-1-D1_fl023_diagnostic.json`, `scripts/rip1_diag_fl023.py`).
4. **Cross-version comparisons:** RIP-2 level_residual A6 results are comparable with RIP-1-D1, not with the
   historical RIP-1 A6 / A6-V1 level_residual rows. Every other RIP-1 row is unaffected.
**Consequence found while executing the decision (FL-024, a RIP-2 build defect, fixed before any run):** the exact sum
alone, without the support of the transform (x = fmod(P, m) lies in [0, m)), gives log(1/m) per step to every small m.
RIP-2 now enforces the support, which is part of the same likelihood (addendum A1).

## Founder authorisation OD-S9-09 — 2026-11-19 — the single registered RIP-2 run
Founder (Ali), after the reviewer's B-R3 verdict «NO BLOCKERS — READY TO RUN» on cf60cb8: run exactly one registered,
synthetic-only RIP-2 experiment with the frozen, audited code; no gold data; no change to the frozen package; no RIP-3.
Preserve and report every output, log, seed, manifest, hash and the reproduction evidence; full results go to independent
audit before any next step is requested.
**Code at the run (sha256; rip2.py identical to the reviewed cf60cb8):**
  - `src/xauusd_swarm/rip2.py` `60900b57a03ff35924828cce8f6a331b168cdd6921f1949d4ddcb9ce9974eb2f`
  - `src/xauusd_swarm/rip1_attack.py` `6d28758ed17ee2bc525251b280a24d2c8ea581d426d0c793d3638a0ca38d555e`
  - `src/xauusd_swarm/reid.py` `4b553a3cba79f3b03a387110ede2ba02d0102c4c242df967a1ee3a7e189ca4fb`
  - `src/xauusd_swarm/representations.py` `7ff8b95515401c2a74011cca9338ffb3cd67998ee91f9900aee494104c9dda4f`
  - `scripts/rip2_run.py` `563edb215986813f813665ba580a561b675d858eabcc3ee6cbeb840b66113e22`
  - `docs/research/RIP2_DESIGN_ADDENDUM_A1.md` `b253af008cb88a97da35edb925b9a00ceb491d70b36801596dc5553acb19b6c4`
Run: `python scripts/rip2_run.py docs/results/rip2` (no spec override), once.

## Founder authorisation OD-S9-10 — 2026-11-19 — RIP-3: DESIGN ONLY
Founder (Ali): option A. Design RIP-3 only: alternative anonymisation methods acting on the fluctuation (volatility)
level and the activity pattern; re-identification resistance against the RIP-2 baselines; research-utility cost
(U-vol, U-act, U-event); measured results, theoretical expectations and unverified hypotheses kept apart; controls
against overfitting, attacker-model limits and misleading security claims; RIP-1 and RIP-2 findings and limits used
explicitly; measurable acceptance criteria and failure conditions fixed before any build; a comparison matrix and a
recommended design with its justification. Goal: the best balance between re-identification resistance and research
utility, not maximal secrecy.
**Limits:** no code, no BUILD, no experiment, simulation or RUN; no gold data; G-Z closed; frozen RIP-1 / RIP-2 packages
untouched; no Phase 5 or later. The design goes to independent review; BUILD needs a separate explicit authorisation.

## FD-01-D47 — 2026-11-19 — RIP-3 design v0.4 FROZEN (DESIGN FREEZE ONLY; no BUILD)
⟦قرار Claude بتفويض المؤسس، FD-01⟧ The independent reviewer's final review of v0.4 (commit
4e0e861873f5c5cbff628623cc3e4c703d768b3c) returned «NO BLOCKERS — READY TO FREEZE», with every R1–R3 item resolved
and the 10 bundle hashes verified. The design is frozen as the approved RIP-3 baseline.
- **Frozen file:** `docs/research/RIP3_DESIGN.md` sha256 `efb7e16315476c4d4caa523fc8d45adcdd1c3ae0e6bbc13d35b8d7902def7898`. Its header still reads "v0.4 — DRAFT FOR REVIEW":
  the file is kept byte-identical to the reviewed one, so the hash the reviewer verified stays valid. This record is
  the freeze; any change is a new version with a record and independent review.
- **Scope of the approval:** design freeze only. It does **not** authorise BUILD, implementation, simulation, RUN,
  gold data, G-Z or any later phase (OD-S9-10 limits unchanged).
- **Before any BUILD:** a separate explicit founder authorisation, which must also confirm or change the PROPOSED
  utility floors of §7.2. CS-01-04 untouched.
- **Reason / source:** reviewer's final verdict on v0.4; OD-S9-10; FD-01 (merge and governance by delegation).

## Founder authorisation OD-S9-11 — 2026-11-19 — RIP-3 BUILD (not RUN); §7.2 utility floors confirmed
Founder (Ali): BUILD of RIP-3 under the frozen design v0.4 (main at 746df75). The §7.2 utility floors are adopted
exactly as proposed: U-vol* ≥ 0.95 × B-LR; U-act power ≥ 0.90 × B-LR with false-alarm increase ≤ 0.02 (otherwise the
candidate is U-act-sacrificing and ranked separately); U-event success ≥ 0.90 × B-LR with null-flag increase ≤ 0.02;
U-ratio median error ≤ B-LR + 0.05.
**Conditions:** literal adherence to the frozen design; any needed design change raised as a separate request before
it is made; BUILD only (no RUN, no registered experiment, without a separate authorisation); no gold data; G-Z closed;
no RIP-4 or Phase 5; CS-01-04 untouched; evidence, seeds, logs and hashes kept and results reproducible; tests, then a
complete BUILD package for independent scientific and engineering review before a RUN authorisation is requested.

## Founder decision OD-S9-12 — 2026-11-22 — DCR-01 not adopted; RIP-3 design v0.4 stays governing
Founder (Ali), after independent review R-B2 (which recommended this option):
- The frozen design v0.4 stays governing; the drafts v0.5 and v0.5r2 (DCR-01) are **not adopted**. No δ is adopted.
- Acceptance rules are not changed after seeing development results.
- Expected consequence: if the RUN confirms it, C-V2 fails and M3–M6 are «not assessable» (FC-4); only M1 and M2
  remain assessable within the limits of v0.4, and that does not mean RIP-3 succeeds as a whole.
- Unchanged limits: BUILD only (no RUN authorisation); 6201 and 6301 unused; no real gold data; G-Z closed; no RIP-4,
  no Phase 5; no «READY TO RUN».
- Pending: FL-032 (CI blocked by billing) — CI must be green on Ubuntu and Windows for 155b00f and 61eff1b, with run
  links and logs kept, then independent review of the CI evidence and of commit 61eff1b.

## Founder decision OD-S9-13 — 2026-11-22 — FL-032: CI in a separate public sandbox repository
Founder (Ali), after GitHub refused to start Actions jobs on the private repository (billing; raising the
budget to 10 USD was not accepted by GitHub) and after the reviewer's conditional pre-acceptance:
- CI for the rip3/build commits 155b00f, 61eff1b and 5eeb005 runs in a separate **public** repository
  `mulaalig87-ops/XAUUSD-Swarm-CI-Sandbox`, created by the founder under his existing account (a second
  personal account was ruled out: GitHub allows one free personal account per person).
- Only parentless snapshot commits of the three original trees are published (no history, no branches, no
  settings of the original). The founder accepted the disclosure of those trees (they contain his first name,
  the GitHub account name, the Windows user name in a documented path and the name ORACLE INFINITY in
  boundary statements only); he knows a public disclosure is permanent.
- The original repository stays private and unchanged.
- Reviewer (ChatGPT) conditions, accepted: per-commit pre-publication scan; tree-SHA match per commit;
  per-file SHA-256 manifest with modes; workflow unchanged; Ubuntu and Windows per snapshot with run links,
  full logs and job results; environment differences documented. The evidence is called *CI equivalent to
  the original source tree*, not CI on the original commits. GitLab is NOT pre-approved as a substitute.
  FL-032 stays OPEN until the reviewer has checked the evidence.
- Evidence: `docs/results/rip3_build/test_runs/FL032_sandbox_ci/` (EVIDENCE.md, tree_manifest.json, logs/).
- Unchanged limits: BUILD only; no RUN; 6201 and 6301 unused; no real gold data; design v0.4 unchanged;
  G-Z closed; no RIP-4, no Phase 5; no «READY TO RUN».

## Founder decision OD-S9-14 — 2026-11-23 — RIP-3 BUILD complete; no RUN authorisation
Founder (Ali), after the reviewer's final verdict «RIP-3 BUILD ACCEPTED» on main 1195603 (tree ddb3ce9):
- Recorded: RIP-3 BUILD is complete; FL-032, R-B2-01, R-B2-04 closed (reviewer evidence); reviewer also closed
  R-B1-01 and R3B-00.
- **No RUN authorisation is issued.** Sets 6201 and 6301 must not be used. The closure is not a RUN authorisation;
  any RUN request needs a separate, explicit founder authorisation.
- Unchanged: design v0.4 and its acceptance rules; no real gold data; G-Z closed; no RIP-4, no Phase 5;
  the original repository stays private and the sandbox repository stays public (no privacy change, no deletion
  of evidence or records).

## Founder decision OD-S9-15 — 2026-11-23 — read-only verification of the delivery point, and its recording
Founder (Ali), with no stage resumed:
- Authorised a read-only verification of the delivery point `main` 775ce2b (tree eb1bbe0) against the handoff file,
  and of sandbox run 45130818597 (snapshot d4ea095, tree eb1bbe0), and its recording.
- Result: `docs/results/handoff_verification_2026-11-23/VERIFICATION.md` — the repository matches the handoff;
  run 45130818597 succeeded on Ubuntu and Windows in both attempts (877 + 7 and 867 + 17, total 884 each) on the
  tree of 775ce2b: CI equivalent to that tree, not CI on 775ce2b.
- The original evidence and the full text of this decision are kept in the private repository and are not published.
- Differences found are recorded only; correcting them is not authorised by this decision.
- Unchanged: no RUN; 6201 / 6301 unused; no real gold data; design v0.4 unchanged; CS-01-04, OD-10, OD-11, G-Z,
  RIP-4, Phase 5 deferred; no new track opened.

## Founder decision OD-S9-16 — 2026-11-23 — documentation fixes of the resume point; commit trailer
Founder (Ali):
- Opens one limited item: fix the three documentation differences recorded in
  `docs/results/handoff_verification_2026-11-23/VERIFICATION.md` §3 (items 2–4): stale lines in `docs/HANDOFF.md`,
  the commit-trailer wording, the hook-path step. Reason: they affect the accuracy of the resume point.
  Also, at the founder's request: a note in `CLAUDE.md` on the CI gate in force (sandbox CI equivalent to the tree,
  content check and separate founder approval before each sandbox publication, no claim that private-repo CI works).
- Commit trailer from now on: `Co-Authored-By: Claude <noreply@anthropic.com>` only, with no session line (not needed to
  identify the co-author; no session data in Git history). Earlier commits are not rewritten.
- Scope: `docs/` and `CLAUDE.md` only. No change to `src/`, `tests/`, `env/`, `docs/reference/` or any frozen design.
- Each step (push, sandbox publication after content review, merge) needs its own founder approval.
- Unchanged: delivery point 775ce2b; no RUN; 6201 / 6301 unused; CS-01-04, OD-10, OD-11, G-Z, RIP-4, Phase 5 deferred.

## Founder authorisation OD-S9-17 — 2026-11-24 — RIP-3 run readiness: PREPARATION ONLY (no RUN)
Founder (Ali), after the decision package «RIP-3 Synthetic Run (v0.4)» of 2026-11-24 (verdict: not ready; blockers B-1,
B-2) and the reviewer's review of it (both blockers essential; guard and C-V2 remarks):
- Authorised, as preparation, build and verification only:
  - B-1: implementation choice IC3-23 fixing the confirmatory step before any registered set is scored, with code for
    the FC-3 verdict and its tests; the smoke set only.
  - The RUN-authorisation guard checks a recorded decision (sets, approved commit and tree); this work creates no
    authorisation.
  - B-2: an execution and resume protocol on the founder's computer, in an independent environment built from
    `env/test.lock.txt` (never ORACLE INFINITY's).
  - R14: the actual values in `docs/research/RIP3_BUILD_NOTES.md` (B1-HP row).
  - The preparatory tests, then CI equivalent to the tree in the sandbox; nothing is published there before the
    founder has seen and approved its content; then the reviewer's independent review.
- **B-LR is the only reference cell on the confirmatory set 6301** (paired difference and floors, design §7.4 step 3);
  B-AF is not added there.
- Not authorised: RIP-3 RUN; any use of 6201 or 6301; real gold data; G-Z; RIP-4; Phase 5; any change to design v0.4,
  its acceptance rules or any frozen file. The expected C-V2 failure (FC-4) is not assumed: C-V2 is run as designed and
  its result is accepted either way; its failure would mean M3–M6 not assessable, not RIP-3 success.
- The authorisation ends when the preparation, its evidence, the tests and the reviewer's review are complete; then a
  new founder decision is needed. Success of the preparation is not a prior approval of a RUN.
- Review of the first preparation commit (reviewer, forwarded by the founder, 2026-11-24): fixed before any push —
  FC-3 counts a missing, extra or unreadable §7.2 floor as failed; the guard refuses a scope (sets) changed after it was
  recorded (scope sha256 in the decision, entry and section compared with the recording commit); the run protocol no
  longer states the machine's specification or absolute local paths. No push and no sandbox publication authorised yet.
- Second review (reviewer, 2026-11-24): S-01 — `select()` classifies and selects only on complete floor checks (IC3-25;
  unchanged results when the floors are complete); and a test that the registry entry and the decision section are
  recorded in the same commit. Still no push, no sandbox publication, no RUN.
- Third review (reviewer, 2026-11-24): the guard now also refuses a decision section that existed before the commit that
  added the registry entry (reversed order); the select() test compares the whole output with the accepted BUILD
  select() when floors are complete. Still no push, no sandbox publication, no RUN.

## Founder decision OD-S9-18 — 2026-11-24 — FL-035: fix the empty-registry test first (option b); no RUN authorisation
Founder (Ali), after the readiness review «READY TO RUN — NO BLOCKERS» of main fdf4508 (a review, not an authorisation),
his decision on the scope of a first, eval-only authorisation, and FL-035 (the preparation test that pins an empty
registry would stop the protocol pre-flight once any authorisation is recorded):
- Option (b) chosen: the root cause is fixed in the test first. Option (a) — an exception written into an authorisation
  decision, or a change of the protocol conditions to pass over the test — is not adopted.
- The test checks that every recorded authorisation is consistent with its decision section, its scope and its scope
  hash, instead of requiring the registry to stay empty for ever; it covers an empty registry, a correct matching
  authorisation, a mismatched or unrecorded one, and confirm stays refused without its own authorisation.
- Conditions: main and fdf4508 untouched; design v0.4 untouched; a separate fix branch; the change shown to the founder
  before adoption; the full cycle (full local suite, review, sandbox CI per FL-032 with the tree SHA matched and Ubuntu
  and Windows green); no push, sandbox publication or merge without the founder's independent approval after the
  evidence is shown.
- Reviews of the proposed patch (reviewer, forwarded by the founder, 2026-11-24): v1 → v2 the scope line must be a
  separate line equal to the computed hash, and identifiers are compared whole, not as substrings; v2 → v3 headings of
  every Markdown level H1–H6 with «RIP-3 RUN» are checked, only the H2 form is accepted. v3 approved; local adoption
  (this record, FL-035, build notes, release record, one local commit, the full local suite) authorised, then stop.
- `scripts/rip3_run.py` is not changed: making the guard itself as strict as the test is a separate topic, not mixed
  with FL-035.
- Not authorised by this decision: recording an authorisation or its decision (that wording is shown to the founder
  and approved first, on the new commit and tree, eval only); any change to the registry; push, sandbox publication or
  merge; smoke; RIP-3 RUN; any use of 6201 or 6301; real gold data; G-Z; RIP-4; Phase 5.

## Founder decision OD-S9-19 — 2026-11-24 — run-driver audit before DEC-145: record the defects, then fix them locally
Founder (Ali), after the local merge of `rip3/auth-registry-test` (local main 9907d52, tree 653ae50, not pushed) and the
reviewer's recommendation (a review, not an approval):
- Order of work adopted: (1) audit of `--assemble`, resume and provenance, and of the strictness of the run guard;
  (2) DEC-145 prepared on the final commit that passed that audit; (3) pre-flight and smoke under their own approvals;
  (4) RIP-3 RUN stays forbidden until a separate, explicit authorisation.
- The read-only audit found A-01 … A-04, P-01 … P-04, R-01, G-01, G-02. Approved: branch `rip3/run-hardening` from
  9907d52, locally only; its first commit records every defect in `docs/FL.md` (FL-036 … FL-046: description,
  reproduction, severity and reason, test, acceptance criterion) with no code change, and A-01 is recorded as reproduced
  by simulation on Linux, not yet on Windows; then the fixes of A-01 … A-04, P-01 … P-03, R-01, G-01, G-02, one test per
  defect shown to fail before its fix and pass after; P-04 recorded only; the full suite run locally with a recording
  script (command, Python, `pip freeze`, HEAD, tree, clean state, no other pytest at start and end); then stop and show
  the diff, logs, evidence and hashes.
- Not authorised by this decision: any change to design v0.4, the seeds, the acceptance rules or the scientific
  protocol; real gold data; 6201 / 6301; any run authorisation; smoke; RIP-3 RUN; push, sandbox publication or merge;
  any change to local main (it stays at 9907d52).

## Founder decision OD-S9-20 — 2026-11-24 — second hardening round after review R1 (local only)
Founder (Ali), after review R1 of `rip3/run-hardening` at ce436c0 (reviewer: NOT APPROVED; a review, not an approval)
and Claude's assessment, which added FL-047 (public paths to the seeds 6201 / 6301 without authorisation, including
`scripts/rip3_partial_repro.py`):
- Approved, on the local branch from ce436c0, in this order: record R1-1 … R1-4 and FL-047 first (no code); tests shown
  to fail before the fixes without generating or evaluating 6201 / 6301; the fixes; proof that every public path of
  FL-047 is closed and that the authorisation is checked from the real record in HEAD (booleans and unrecorded
  identifiers refused); the full local suite with the parent process id of every pytest process seen; the evidence
  package; then stop.
- Publishing: atomic publication that never replaces a file; where the file system cannot make a hard link, a clear
  refusal; no return to `os.replace`. The requirement is the hard-link capability itself, not a named file system;
  behaviour on Windows to be checked in CI.
- Not authorised: any change to design v0.4, the acceptance rules or the protocol; real gold data; generating or
  evaluating 6201 / 6301; smoke; RIP-3 RUN; a run authorisation; push, sandbox, merge; any change to main or another
  branch.

## Founder decision OD-S9-21 — 2026-11-24 — third hardening round, limited to FL-047 and the environment check
Founder (Ali), after review R2 of `rip3/run-hardening` at 44e48c8 (reviewer: NOT APPROVED, a text base passes the seed
guard; a review, not an approval) and Claude's check (two more inputs of the same kind: a separator inside a part, and
a sequence seed in `gates`):
- Approved, locally on the same branch: the guard decides on the final seed string before any generator is created,
  for every input form that gives the same string (text, separators, NumPy types); `gates` accepts only integer seeds
  (lists, arrays and any other input refused); regression tests for every refused form of 6201 and 6301 with proof that
  execution stops before any generation or evaluation; a re-check of every public path that takes or passes a base or
  seed; the package-name comparison of the run evidence made case-insensitive, with a test. Order: FL first, tests
  before the fixes, fixes, the full suite alone with the parent process ids, the evidence package with hashes and a
  full archive of the tree; then stop.
- Not authorised: any change to design v0.4, the protocol, the seeds or the acceptance rules; generating or
  evaluating 6201 / 6301; real gold data; a run authorisation; smoke; RIP-3 RUN; push, sandbox, merge; any change to
  main or another branch.

## Founder decision OD-S9-22 — 2026-11-25 — fourth hardening round, limited to FL-048 (git output encoding)
Founder (Ali), after sandbox run 45491211968 on snapshot 0d0c720 (tree ff93e9c): Ubuntu green, Windows 7 failed in the
guard tests, cause shown by the evidence (git output decoded as cp1252):
- Approved, locally on `rip3/run-hardening` from 828cb27: FL-048 recorded first; tests that simulate a Windows cp1252
  default and fail before the fix; UTF-8 decoding with strict errors in `rip3_auth._git` and in the two git calls of
  `meta()`, never the system default; the three paths tested directly, headings with the em dash read and matched,
  the seven guard tests passing; the full suite alone with parent process ids; the evidence package; any deviation
  recorded.
- Not authorised: push, sandbox, merge, push of main; a run authorisation, smoke, RIP-3 RUN; generating or evaluating
  6201 / 6301; real gold data; any change to design v0.4, the acceptance rules, the seeds or the protocol. FL-036 and
  R1-2 stay open until a fully green CI after the fix.

## Founder decision OD-S9-23 — 2026-11-25 — documentation batch after the hardening merge (local branch)
Founder (Ali), after main 634800a (tree 57f961e) was pushed and sandbox run 45542579831 was green on Ubuntu and
Windows (reviewed NO BLOCKERS):
- Approved, on a separate local branch from 634800a: record the closure of FL-036, R1-2 and FL-048 with run
  45542579831 and its evidence, founded on the tested tree 57f961e (tree equivalence, not the merge commit itself);
  update HANDOFF to main 634800a and state that acceptance tests run on the identical tree, not on the merge commit;
  archive the evidence of FL-035 and of the four hardening rounds in `E:\XAUUSD SWARM\records\` with the index updated,
  hashes checked and no original evidence replaced; improve the two deferred tests (a boolean refused by the guard's
  inputs by its type; a structural check that also sees generators created through aliases).
- Not authorised: push, merge, DEC-145; any change to design v0.4, the protocol or the authorisation registry; RIP-3
  RUN; generating or evaluating 6201 / 6301; changing gold data or its files. The closures are not announced as
  official before the batch and its evidence are reviewed.
- Addendum (2026-11-25, after review R1 of the batch, NOT APPROVED): second round approved by the founder, locally on
  `docs/hardening-closure` only: a transfer-and-verification record of the archive on his computer; the structural check
  rebuilt to accept generators only as direct calls inside the three top-level guarded functions (identity, not name),
  refuse stored references and track aliases, with the two reported cases and similar ones; a git bundle and the raw
  commit and tree objects in the evidence; the full suite again. No push, sandbox, CI or merge.
- Addendum 2 (2026-11-25, after review R2 of the batch: one MAJOR, one MINOR): third round approved by the founder,
  locally on `docs/hardening-closure` only: the structural check becomes an allow-list (the three guarded functions
  defined once at the top level and never rebound; the random modules only as `<module>.<public name>`, generators
  only as direct calls inside those functions; no introspection or dynamic-import functions at all), with the two
  reported cases and similar ones; the limit of a static check and the role of the FL-047 run-time guard documented.
  The MINOR (the archive transfer was checked in the session, not by files kept on the computer) is accepted as
  recorded; a direct check on the computer, with its output saved in records\, waits until the computer is connected.
- Addendum 3 (2026-11-25, after review R3 of the batch: one MAJOR): fourth round approved by the founder, locally on
  `docs/hardening-closure` only: an allow-list of the import statements of `rip3.py` (exact modules, names and aliases;
  any other import refused) and the presence of `stream`, `_evaluate` and `gates` exactly once at the top level, with
  the reported cases and similar ones.
- Addendum 4 (2026-11-25, after review R4 of the batch: one MAJOR): fifth round approved by the founder, locally on
  `docs/hardening-closure` only: generators accepted only inside statements of the bodies of `stream`, `_evaluate` and
  `gates`; refused in parameter defaults (positional and keyword-only), decorators and annotations, at module level and
  in class bodies; tests for those cases and for correct calls in the three bodies.
- Addendum 5 (2026-11-25, after review R5 of the batch: one MAJOR, one MINOR): sixth round approved by the founder,
  locally on `docs/hardening-closure` only: generator expressions treated as deferred scopes (a generator created
  inside one is refused); yield and await refused in the bodies of the three functions; immediate comprehensions and
  direct calls stay accepted; tests for these cases. The MINOR (the git bundle needs the base commit 634800a, not in
  the evidence) stays recorded without further work: the full tree archive and the raw objects cover the rebuild.
