# Environments (OD-09; Register §26 غ-12)

- Two separate virtual environments: `_envs/dev` and `_envs/test` (git-ignored, created by `scripts/wp801_setup.ps1`).
- Python 3.13 via the `py -3.13` launcher. Any interpreter path containing "oracle" is refused (ORACLE INFINITY boundary).
- Install: `python -m pip install --no-deps -r env/<name>.lock.txt`. Every package is pinned, including the transitive dependencies of pytest 9.1.1. No resolver choice remains.
- After install the script runs `pip freeze` into `env/<name>.installed.txt` and fails if the frozen set differs from the lock file.
- **Limitation:** the lock files pin versions, not file hashes. Hash pinning (`--require-hashes`) is a follow-up item once hashes can be fetched on a networked machine.
- No secrets and no gold-data files in either environment.
- The pinned set was verified as a working combination on Linux / Python 3.13. On Windows it is untested until the setup script runs.
