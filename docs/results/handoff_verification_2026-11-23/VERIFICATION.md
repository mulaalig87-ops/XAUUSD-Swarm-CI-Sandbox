# Handoff verification — delivery point main 775ce2b (2026-11-23)

**What this is:** a read-only check of the repository state against the founder's handoff file of
2026-11-23, and of the sandbox CI run that the handoff cites for the delivery point.
Founder decision OD-S9-15.

**What this is not:** a RUN, a new test of any research claim, or a decision on any deferred item
(CS-01-04, OD-10, OD-11, G-Z, RIP-3 RUN, RIP-4, Phase 5). No code, test, design, acceptance rule or
result is changed.

**Evidence location.** The original evidence of this verification is kept in the private repository
and is not published.

## 1. Repository state (read-only)

Method: `git clone --depth 1`, bounded `git fetch --depth=400 origin main`, `git ls-remote origin`.

| Check | Expected (handoff) | Found | Result |
|---|---|---|---|
| `main` on origin and in the clone | 775ce2bba9ca78a6914f1ad187ced9d8388e8288 | 775ce2bba9ca78a6914f1ad187ced9d8388e8288 | match |
| Tree of `main` | eb1bbe0813f1b4b422f7d684643fe507c037b832 | eb1bbe0813f1b4b422f7d684643fe507c037b832 | match |
| Parents of 775ce2b | merge of docs/rip3-build-closure | 1195603 + a213e56 (branch head); tree of a213e56 = eb1bbe0 | match |
| Earlier merge 1195603 | rip3/build head ad41547, tree ddb3ce9 | parents 746df75 + ad41547; tree ddb3ce984673bdd0344b4fed000666f1400fa4a8 | match |
| 1195603 → 775ce2b | documentation only | 9 files, all under `docs/` (records and CI logs); no code or test | match |
| Unmerged branches | none for rip3 | 98 branches on origin; every head is an ancestor of `main` | match |
| Local working tree | clean | clean | match |
| `docs/research/RIP3_DESIGN.md` sha256 | efb7e163…7898 (FD-01-D47) | efb7e16315476c4d4caa523fc8d45adcdd1c3ae0e6bbc13d35b8d7902def7898 | match |
| `docs/reference/*` | frozen | 13 / 13 OK against `SHA256SUMS.txt` | match |
| FINAL STATUS tables (RIP_register.md, FL.md) | FL-030, R-B2-03 DECIDED (OD-S9-12); others closed | as expected | match |
| OD-S9-14 in DECISIONS.md | no RUN; 6201 / 6301 unused | present with that text | match |

## 2. Sandbox CI run 45130818597 for the delivery point

Snapshot commit, read with `git cat-file -p` from the public sandbox repository (branch `snap/a213e56`):

```
d4ea09545e286a7e803df9490035e66e25b96fc9
tree eb1bbe0813f1b4b422f7d684643fe507c037b832
author CI Snapshot <snapshot@invalid> 1795305600 +0000   (2026-11-22T00:00:00Z)
committer CI Snapshot <snapshot@invalid> 1795305600 +0000
(no parent)
CI sandbox snapshot: tree eb1bbe0813f1b4b422f7d684643fe507c037b832 of original commit a213e568049382ee8c41d45874d4ceed250fb3a5 (no history). FL-032.
```

The snapshot was taken from a213e56 (head of docs/rip3-build-closure), not from 775ce2b itself; both
commits have the tree eb1bbe0. The run is therefore **CI equivalent to the tree of 775ce2b**, not CI on
the original commit.

Run: https://github.com/mulaalig87-ops/XAUUSD-Swarm-CI-Sandbox/actions/runs/45130818597 — workflow
`tests.yml`, event `push`, run #7, commit d4ea095, branch `snap/a213e56`. Command in both jobs:
`python -m pytest -q -p no:cacheprovider`; the step «Install the pinned test environment
(env/test.lock.txt, OD-09)» succeeded in both jobs and both attempts.

| Attempt | Run status | Ubuntu (ubuntu-latest, Python 3.13) | Windows (windows-latest, Python 3.13) |
|---|---|---|---|
| 1 | success, 34m 39s | success — 877 passed, 7 skipped in 2064.40s | success — 867 passed, 17 skipped in 194.36s |
| 2 | success, 25m 29s | success — 877 passed, 7 skipped in 1511.37s | success — 867 passed, 17 skipped in 161.75s |

Direct links: `…/actions/runs/45130818597/attempts/1` and `…/actions/runs/45130818597/attempts/2`.

- Totals: 877 + 7 = 884 (Ubuntu), 867 + 17 = 884 (Windows), the normal result recorded in
  `docs/results/rip3_build/test_runs/FL032_sandbox_ci/EVIDENCE.md`.
- Skip positions (the `s` marks in the `-q` progress lines) are identical in both attempts: Ubuntu lines
  20–21 (7), Windows lines 16–22 (17). The same tests were skipped both times.
- Annotations: one warning per job, «Node.js 20 is deprecated …» (GitHub Actions runtime notice), not a
  test result.
- Duration differences between attempts are runner speed; the content is the same tree.

**Evidence form.** The GitHub API for the sandbox repository was not available in the verifying session
(HTTP 403), so no job logs are stored for this run. The values above were read from the run pages and can be
re-checked on the run page itself; the original evidence is kept in the private repository.

## 3. Differences found between the repository and the handoff (open; not fixed)

Recorded only; not corrected in this record.

1. Before this record, no evidence file contained run 45130818597 or 775ce2b (the FL-032 evidence ended
   at run 45077432523 on ad41547). This record fills that gap.
2. `docs/HANDOFF.md` has stale lines: «747 passed» in the components section (current total 884); the
   RIP-2 / RIP-3 lines describe rip2/build and rip3/build as «not merged» (both are ancestors of `main`).
3. The commit-trailer wording in `CLAUDE.md` differs from the wording used in recent commits.
4. `core.hooksPath` is not set in a fresh clone; it must be set (`git config core.hooksPath hooks`)
   before any commit.
5. The sandbox also holds `snap/cf54505` → ca0d59b, not listed in the handoff (an earlier commit on the
   same branch; expected).
