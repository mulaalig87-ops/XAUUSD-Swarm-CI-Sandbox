# FL-032 — tree-equivalent CI evidence for rip3/build (separate public sandbox repository)

**What this is:** CI on GitHub Actions for snapshot commits whose Git trees are identical to the trees of
the original commits 155b00f, 61eff1b and 5eeb005. It ran in the separate public repository
`mulaalig87-ops/XAUUSD-Swarm-CI-Sandbox` because GitHub does not start Actions jobs on the private
original repository (billing, FL-032).

**What this is not:** CI on the original commits themselves. Commit SHA, repository and run metadata
differ (see «Environment differences»). The reviewer's wording applies: *CI evidence equivalent to the
original source tree*, not CI on the original commit.

Authority: founder decision OD-S9-13 (DECISIONS.md); reviewer conditional acceptance (2026-11-22).
FL-032 stays OPEN until the reviewer has checked this evidence.

## 1. Source equivalence (per commit)

| Original commit | Original tree | Sandbox commit (no parents) | Sandbox tree | Tree match | Files |
|---|---|---|---|---|---|
| 155b00f9a8f326a619528ef6292e7772704b9c90 | 96ae836537fcdd35404fb2c03a1b20dcc472894a | 8ec0535c0b2f8d3480680663a5fc4e53e14ff2a2 | 96ae836537fcdd35404fb2c03a1b20dcc472894a | yes | 222 / 222 |
| 61eff1b93c2f2b44682538239aea39fa11dca937 | d44fb5eaf230bcc5bdb055459b30df3839d131d6 | bf6b68202efd6e5c193fc29d02af4b3a6a2d60c8 | d44fb5eaf230bcc5bdb055459b30df3839d131d6 | yes | 222 / 222 |
| 5eeb005165bc906241b1fe0bccdde4121a166353 | c2d81912bcb79faf9df38f7ea2ee8d5236048b2e | 547e0eaf95b42f446477b56e3ad0d3915d239cf6 | c2d81912bcb79faf9df38f7ea2ee8d5236048b2e | yes | 222 / 222 |

Method: each sandbox commit was made with `git commit-tree <original>^{tree}` (no parent, neutral author
«CI Snapshot», fixed date 2026-11-22T00:00:00Z). It points at the original tree object itself, so the tree
SHA, every path, every blob and every mode (including the one executable `hooks/pre-commit`, 100755) are
identical by construction; `git rev-parse <commit>^{tree}` was also compared after the push. No history,
branches, tags or settings of the original repository were pushed; no untracked or local files.

Per-file evidence: `tree_manifest.json` — for each commit, every path with its mode, Git blob id, SHA-256
and size; plus run and job metadata.

Workflow: `.github/workflows/tests.yml` is the same blob (`acf37e150c1ed1c35b9b0ff54fa1e424ea95d051`) in all
three commits and was run unmodified (it is part of the identical tree). Trigger: `push`.

## 2. Pre-publication checks (each commit separately, 2026-11-22)
- File modes: 221 × 100644, 1 × 100755 (`hooks/pre-commit`); no symlinks (120000), no submodules (160000).
- No `.gitmodules`; no Git LFS pointer files. `.gitattributes`: one rule `docs/results/** -text`; no `export-ignore`.
- Secret patterns (AWS keys, GitHub tokens `ghp_`/`github_pat_`/`gho_`, `sk-…`, Slack tokens, private-key
  blocks, `password=`, `api_key=`): no hits. E-mail addresses: only `noreply@anthropic.com`.
- ORACLE INFINITY: the name appears only in boundary statements (prohibitions, an interpreter-path refusal);
  no ORACLE code, data or files.
- Personal identifiers disclosed (accepted by the founder): first name, GitHub account name, Windows user
  name in the documented oracle313 path. The founder's e-mail and the repository history are not disclosed.

## 3. CI results (GitHub Actions, sandbox repository)

| Original | Sandbox commit run | Run | Ubuntu job | Windows job |
|---|---|---|---|---|
| 155b00f | 8ec0535 | [45066506808](https://github.com/mulaalig87-ops/XAUUSD-Swarm-CI-Sandbox/actions/runs/45066506808) | [success](https://github.com/mulaalig87-ops/XAUUSD-Swarm-CI-Sandbox/actions/runs/45066506808/job/137343748933) — 877 passed, 7 skipped, 2063.80 s | [success](https://github.com/mulaalig87-ops/XAUUSD-Swarm-CI-Sandbox/actions/runs/45066506808/job/137343748688) — 867 passed, 17 skipped, 158.98 s |
| 61eff1b | bf6b682 | [45066507333](https://github.com/mulaalig87-ops/XAUUSD-Swarm-CI-Sandbox/actions/runs/45066507333) | [success](https://github.com/mulaalig87-ops/XAUUSD-Swarm-CI-Sandbox/actions/runs/45066507333/job/137343749742) — 877 passed, 7 skipped, 1534.42 s | [success](https://github.com/mulaalig87-ops/XAUUSD-Swarm-CI-Sandbox/actions/runs/45066507333/job/137343749929) — 867 passed, 17 skipped, 170.20 s |
| 5eeb005 | 547e0ea | [45066507466](https://github.com/mulaalig87-ops/XAUUSD-Swarm-CI-Sandbox/actions/runs/45066507466) | [success](https://github.com/mulaalig87-ops/XAUUSD-Swarm-CI-Sandbox/actions/runs/45066507466/job/137343749801) — 877 passed, 7 skipped, 1555.73 s | [success](https://github.com/mulaalig87-ops/XAUUSD-Swarm-CI-Sandbox/actions/runs/45066507466/job/137343749669) — 867 passed, 17 skipped, 126.41 s |

Proof that tests executed (not only accepted): each full job log is in `logs/`; each contains the checkout
of the expected sandbox SHA, `python -m pip freeze` (numpy 2.5.3, pytest 9.1.1), and the pytest summary line
quoted above. Python: 3.13.18 (Ubuntu), 3.13.17 (Windows). All jobs ran 2026-11-22 20:27–21:02 UTC.

Skips (the logs use `pytest -q` and do not print reasons; the following is read from the test code, not from
the logs): Ubuntu 7 = 4 tests that need a root run host (`tests/test_rip1.py`, `ROOT_HOST`) + 3 tests that
`importorskip` scipy/sklearn, which are not in `env/test.lock.txt` (`tests/test_rip3.py`). Windows has 10
more, consistent with the Linux-only heavy tests and the POSIX-only test in `tests/test_wp801_sync.py`.
877 + 7 = 884, the same total as the local full run on 2158e6d (884 passed with root and scipy present).

## 4. Environment differences from the original repository
- `GITHUB_SHA` / checked-out commit: the sandbox commit, not the original commit (same tree).
- `GITHUB_REPOSITORY`: `mulaalig87-ops/XAUUSD-Swarm-CI-Sandbox` (public) instead of the private original.
- `GITHUB_REF`: `refs/heads/snap/<original short SHA>`.
- Token permissions: `contents: read` from the workflow itself (unchanged).
- Secrets and variables: the workflow uses none; no secrets or variables were set in the sandbox
  repository. No setting of the original repository is needed or used.
- Runners: GitHub-hosted `ubuntu-latest` and `windows-latest` (public-repository runners).

## 5. Later run: delivery point main 775ce2b (added 2026-11-23, OD-S9-15)

| Original | Original tree | Sandbox commit (no parents) | Run | Attempt 1 | Attempt 2 |
|---|---|---|---|---|---|
| a213e56 (head of docs/rip3-build-closure; same tree as merge 775ce2b) | eb1bbe0813f1b4b422f7d684643fe507c037b832 | d4ea09545e286a7e803df9490035e66e25b96fc9 (tree eb1bbe0, read with git) | [45130818597](https://github.com/mulaalig87-ops/XAUUSD-Swarm-CI-Sandbox/actions/runs/45130818597) | success — Ubuntu 877 passed, 7 skipped (2064.40 s); Windows 867 passed, 17 skipped (194.36 s) | success — Ubuntu 877 passed, 7 skipped (1511.37 s); Windows 867 passed, 17 skipped (161.75 s) |

Evidence form differs from sections 1–3: no job logs and no per-file manifest are stored for this run (GitHub API
not available in the verifying session). Values read from the run pages (see
`docs/results/handoff_verification_2026-11-23/VERIFICATION.md`); the original evidence is kept in the private
repository and is not published. CI equivalent to the tree of 775ce2b, not CI on 775ce2b.
