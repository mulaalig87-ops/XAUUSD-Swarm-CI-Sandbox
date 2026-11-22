# RIP-3 — execution and resume protocol for the registered run (B-2; OD-S9-17)

**Status: preparation only. No RUN is authorised.** This protocol says how a RUN would be executed **if** the founder
issues a separate, explicit RUN authorisation. It changes nothing in the frozen design v0.4 (FD-01-D47), its
acceptance rules or its seeds. The registered sets 6201 (evaluation) and 6301 (confirmation) are not touched by
anything in this document until that authorisation exists. Synthetic data only.

## 1. Preconditions (all must hold before step 1 of §4)
1. A founder decision recorded in `docs/DECISIONS.md` under a heading that contains its identifier and the words
   `RIP-3 RUN` (for example `## Founder authorisation OD-S9-NN — … — RIP-3 RUN`), naming the sets it covers.
2. The matching entry in `docs/research/RIP3_RUN_AUTHORISATIONS.json`:
   `{"id": "OD-S9-NN", "sets": ["eval", "confirm"], "approved_commit": "<sha>", "approved_tree": "<sha>"}`,
   and, in the decision's section, the line `scope sha256: <hash>` with the hash that
   `scripts/rip3_run.py`'s `scope_sha256(entry)` gives for that entry. The approved commit is the reviewed code; the
   entry and the decision are added in one later commit that changes only those two files. The scope can never be
   widened afterwards: the guard compares the entry and the decision's section with the commit that first recorded
   them and refuses any change (`check_authorisation`). A new scope needs a new decision with a new identifier.
3. The approved commit has a passing full local suite and green CI equivalent to its tree (sandbox, OD-S9-13).
4. The reviewer's readiness review of the preparation is closed.

## 2. Machine and environment (decision D-4: the founder's computer)
- **Machine:** the founder's Windows computer.
- **Interpreter:** a Python 3.13 installation that is **not** the ORACLE INFINITY environment named in `CLAUDE.md`
  (it must never be used, read or copied).
- **Environment:** a new virtual environment used only for this run, built from the approved commit's
  `env/test.lock.txt` with `python -m pip install --no-deps -r env\test.lock.txt` (numpy 2.5.3 is the only
  scientific dependency). Its `pip freeze` is saved as evidence.
- **Folders**, under a run root `<RUN_ROOT>` on the founder's computer chosen at run time (not inside the old local
  copy of the repository):
  - `<RUN_ROOT>\code` — a fresh full clone of the private repository at the authorised commit;
  - `<RUN_ROOT>\env` — the virtual environment;
  - `<RUN_ROOT>\out` — the output folder. It must be **outside** the clone: the driver refuses to
    run when the working tree is not clean, and an output folder inside the clone would make it dirty.
- **Threads:** each process runs with `OMP_NUM_THREADS=1`, `OPENBLAS_NUM_THREADS=1` and `MKL_NUM_THREADS=1`, so that
  floating-point reduction order does not depend on thread scheduling.
- **One platform for the whole run.** Evaluation and confirmation run on the same machine and environment. The
  platform, Python and numpy versions are written into every meta file by the driver.

## 3. Pre-flight (before any registered set; development and smoke sets only)
1. `git -C code rev-parse HEAD` and `git -C code rev-parse HEAD^{tree}` are the recorded authorisation commit
   (or its records-only descendant); `git -C code status --porcelain` is empty.
2. `python -c "import sys, numpy; print(sys.version, numpy.__version__)"` shows 3.13.x and 2.5.3.
3. The full test suite passes in this environment: `python -m pytest -q -p no:cacheprovider` (tests marked heavy are
   Linux-only and are skipped on Windows, as in CI).
4. A smoke run of the driver: `python code\scripts\rip3_run.py out_smoke smoke --cands B-LR --worlds W1`, then the
   same with `--assemble`. Smoke uses seed 6103 only; at full sizes one job takes about half an hour. Its
   time per job is the measured basis for the wall-time plan of §4.
5. Free disk space ≥ 2 GB on the drive of `<RUN_ROOT>`.
A failure at any step stops the procedure; it is recorded in `docs/FL.md` and reported, not worked around.

## 4. Evaluation set (6201)
Every command is run from `<RUN_ROOT>` with the environment active and the thread variables set.
The authorisation identifier is written as `OD-S9-NN`.

1. **Truth first (one process per world).** Two processes in parallel:
   `python code\scripts\rip3_run.py out eval --authorisation OD-S9-NN --worlds W1 --cands B-LR` and the same with
   `--worlds W2`. Each computes its world's truth file before its first job, so later processes reuse it.
2. **Remaining cells.** Several processes in parallel (fewer than the machine's physical cores), each with a disjoint `--cands` list and one world, until every
   one of the 13 cells × 2 worlds = 26 job files exists. Suggested split per world: {B-AF, B-LRS, M1}, {M2w1, M2w2, M2w4},
   {M3W32, M3W128}, {M4, M5, M6}, {M1-Dshown}. Splitting does not change any result: every draw is keyed (IC3-01).
3. **Completeness check.** `out` holds `eval__truth__W1.json`, `eval__truth__W2.json` and exactly 26
   `eval__<cell>__<world>.json` files; each one parses as JSON. A missing file means its job is run again (step 2).
4. **Assemble once.** `python code\scripts\rip3_run.py out eval --authorisation OD-S9-NN --assemble`. This writes
   `eval_results.json` and `eval_results.sha256`, with the hash of every job file. These two files are not edited.

## 5. Confirmatory step (6301), only after §4.4
1. The cells are **not chosen by anyone**: the driver derives them from the hash-checked `eval_results.json`
   (IC3-23: B-LR plus each class's chosen candidate and nearest competitor; no B-AF) and refuses `--cands`.
   If no class has a chosen candidate (FC-1 in both classes), the driver refuses to run the confirm set; that is the
   result, and 6301 stays unused.
2. Run `python code\scripts\rip3_run.py out confirm --authorisation OD-S9-NN --worlds W1` and the same with
   `--worlds W2` (two processes).
3. Completeness check as in §4.3, for the confirm cells.
4. Assemble once with `--assemble`: `confirm_results.json` (+ `.sha256`) with `confirm_cells` and the per-class
   FC-3 verdict (`fc3`). The confirm set is used once; it is never re-scored after its results are seen.

## 6. Interruption and resume
- Job and truth files are written atomically (IC3-24): a file either exists complete or does not exist.
- To resume after a crash, power loss or reboot: run the **same** command again. Existing job files are skipped; a
  leftover `*.json.tmp` file is ignored by the driver and may be deleted.
- Never edit, move or delete a complete job file to "redo" a job. A job whose result looks wrong is reported, not
  re-run (design §7.5: failures are reported, not repaired).
- A generator failure (C-V1) is written into the job file by the code; it is a result, not an interruption.
- If the code, the environment or the machine has to change mid-run, the run stops; the founder decides whether the
  partial run is reported as invalid. Results from two environments are not mixed.

## 7. Evidence kept (decision package §7)
- every `*_meta_*.json`, job file, truth file, `*_results.json` and `*_results.sha256` in `out`;
- the console output of every process (redirected to `out\logs\<set>_<world>_<n>.log`) and start/end times;
- `pip freeze` of the environment; the pre-flight outputs of §3;
- the independent re-score (`scripts/rip3_rescore.py`) and partial reproduction (`scripts/rip3_partial_repro.py`);
- `SHA256SUMS.txt` over all of the above; a copy in the founder's local records folder (`<RECORDS_ROOT>\<date>_rip3_run\`) and, after review,
  in the private repository. Nothing from the run is merged into `main` or published to the sandbox without a
  content check and a separate founder approval.

## 8. Cost (estimate from BUILD timings, not a measurement)
About 14–16 CPU-hours for the evaluation set and 4–7 CPU-hours for the confirmatory step
(`docs/research/RIP3_BUILD_NOTES.md`, «Cost of the RUN»). The wall time depends on the number of parallel processes
the machine allows; the smoke timing of §3.4 is the basis of the plan, and the actual times are recorded, not assumed.
