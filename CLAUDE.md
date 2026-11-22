# XAUUSD Swarm — build repository (Stage 8)

Read `docs/HANDOFF.md` first: it holds the current state, what is next, and the open items.

## Roles and authority
- Founder: Ali (علي). Replies to him are in Arabic and open with «لعلي:».
- Claude leads execution. Under founder delegation FD-01 (`docs/DECISIONS.md`), Claude writes the
  code and tests and merges into `main` itself, and decides governance questions on the founder's
  behalf, recording each one as «⟦قرار Claude بتفويض المؤسس، FD-01⟧» with reason and source.
- ChatGPT is an independent reviewer. Its review is optional and does not block a merge.

## Hard rules
- Never access or mix ORACLE INFINITY (including the venv `C:\Users\win10\venvs\oracle313`).
- No reuse of N0 / V2.x code. The old repo XAUUSD-Swarm-Lab is history only; do not push there.
- Synthetic data only. No gold data (OD-10), no pilot (OD-11), and no release of G-Z output to
  language minds (§26 غ-03, needs CS-01-04 + م5-20). These three stay with the founder: prepare
  each fully and ask him once.
- Never claim work or tests that were not done. Never present planned tests as executed.
- Do not edit `docs/reference/*` (frozen copies; hashes in `docs/reference/SHA256SUMS.txt`).
  A change to a governing document means a new version.
- Never suggest an external auditor.
- Do not invent what the sources leave open: mark it «غير معرّف في المعمارية» or flag it.

## Workflow
- Branch per component (`wpN-NN/<name>`) → full suite passes → release record in `docs/RELEASES.md`
  (file hashes) on the same branch → CI green → `git merge --no-ff` into `main` (FD-01-D26).
- Failures go to `docs/FL.md` (plan 07 §3.0).
- The local pre-commit hook (`hooks/`) allows commits on `main` only during a merge.
- CI: `.github/workflows/tests.yml` runs `pytest` on Ubuntu and Windows, Python 3.13, with
  `env/test.lock.txt`. Tests marked `heavy` (experiment re-runs) are Linux-only (OD-S9-04).
- CI gate in force (OD-S9-13, FL-032): Actions do not start on this private repository (billing), so the merge gate
  is the CI-equivalent run in the public sandbox repo XAUUSD-Swarm-CI-Sandbox on a parentless snapshot whose tree is
  identical to the commit to merge, green on Ubuntu and Windows. Before any snapshot is pushed there, its content is
  checked and the founder approves its publication separately. A green sandbox run does not mean CI works on the
  private repository; describe it as «CI equivalent to the tree», not CI on the original commit.
- Commit trailer: `Co-Authored-By: Claude <noreply@anthropic.com>` only, with no session line (OD-S9-16).
  Earlier commits that used another wording are not rewritten.
- In every fresh clone, run `git config core.hooksPath hooks` before the first commit; a clone does not carry it.
