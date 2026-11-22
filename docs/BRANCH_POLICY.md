# Branch policy (Register §26 غ-11)

1. `main` receives no direct commits.
2. Every change gets its own work branch: `wp8-XX/<short-name>`.
3. Review before merge. The reviewer is ChatGPT (independent audit), and Ali decides.
4. Merge into `main` only with `git merge --no-ff <branch>`, after review.
5. Each merge records its commit hash and file hashes in `docs/RELEASES.md`.

## What enforces this, honestly
- `hooks/pre-commit` (installed into `.git/hooks/`) is a **local barrier only**:
  - It rejects a commit made while on `main`, unless a merge is being completed (`MERGE_HEAD` present).
  - A clean `git merge --no-ff` does not run `pre-commit` at all, so it is allowed.
  - It **can be bypassed**, for example with `git commit --no-verify` or by deleting the hook.
- It is **not** remote branch protection. No remote repository exists yet (OD-08). Remote protection applies only once a remote is verified and configured.
- Compliance therefore also depends on the review step and on the release record in `docs/RELEASES.md`.

The initial commit that creates `main` (WP8-01) is made before the hook is installed and is recorded in `docs/PROVENANCE.md`.
