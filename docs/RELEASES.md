# Releases (merges into main)

| Date | Branch | Merge commit | Notes |
|---|---|---|---|
| 2026-11-15 | wp8-02/governance-core (head bf834ed) | `d3d63110bea03918332579d8d809afe5774c631a` | WP8-02 #1 governance core (ledger + anchors, event-sourced governance, Ed25519 authority). Approved by ChatGPT, review round 4. Tests: 97 passed (Linux, synthetic). Not yet run on Windows. |

### File hashes at merge `d3d63110bea0`

| File | SHA-256 |
|---|---|
| `env/dev.lock.txt` | `e3bf6ac5aebfeb883ac0a053d3d321eba1e4d0c168c958cc5b5d82b7e498523f` |
| `env/test.lock.txt` | `e3bf6ac5aebfeb883ac0a053d3d321eba1e4d0c168c958cc5b5d82b7e498523f` |
| `src/xauusd_swarm/__init__.py` | `9191d70b416fdfe4f1071552ded6c923933f2fdcf52ea72fc21432526aa5407a` |
| `src/xauusd_swarm/charter.py` | `9fb96da791b0d07d129be9314e2623e3128330e4afa115858900a75f72c43c61` |
| `src/xauusd_swarm/identity.py` | `4d472defaccc59cb8db5ad4adf120b0ba115d951c8b3190f4a78089174daa370` |
| `src/xauusd_swarm/ledger.py` | `7909eebea1c94ba30c998218cb1264974fc9de9b5b550237d49da0153dc4ca16` |
| `tests/test_governance.py` | `0a2464d1edb6d5b665c51cb269fb39e0ab62b1f729842614bb97d35edfa5f761` |
| `tests/test_ledger.py` | `7c81e5569970481748368e1140d86ebdae9f25b43dcec7cc9734b045280a6cdf` |

| 2026-11-15 | wp8-02/claims-charter (head 67ecbba) | `6971c830337b4b5f43df8b3c9168b1a5e192aa57` | WP8-02 #2 claims charter (layer 2). Approved by ChatGPT (independent run: 134 passed). Not yet run on Windows. |

### File hashes at merge `6971c830337b`

| File | SHA-256 |
|---|---|
| `src/xauusd_swarm/__init__.py` | `9191d70b416fdfe4f1071552ded6c923933f2fdcf52ea72fc21432526aa5407a` |
| `src/xauusd_swarm/charter.py` | `86b1fe61ddc961273228d6e3e1385706aa948998de6605612cb348c60e2e5811` |
| `src/xauusd_swarm/claims.py` | `2f955d3f58c74aa8a20fb1f089fe14a2849e9fefb643afaf4d99c82ce7c474b8` |
| `src/xauusd_swarm/identity.py` | `4d472defaccc59cb8db5ad4adf120b0ba115d951c8b3190f4a78089174daa370` |
| `src/xauusd_swarm/ledger.py` | `687616d10faff2cb6ea223ed8d60c34dbfb94bd81128d1df83d0b5684e9ba9e6` |
| `tests/test_branch_policy.py` | `fe0028348013be39fc346b1d053e77bb95c21b5e63f110c17e9fd70cc9f2443c` |
| `tests/test_claims.py` | `176b42eb6e57583199a45e8fb5db6d1c712168187a417ba728cf143dad71074c` |
| `tests/test_governance.py` | `0a2464d1edb6d5b665c51cb269fb39e0ab62b1f729842614bb97d35edfa5f761` |
| `tests/test_ledger.py` | `9aba57749a8f2c846f0ede0e4862ae5c0944d9b80f84af2dd63647510c5fbf5c` |
| `tests/test_smoke.py` | `88083e3b8f47758df8ae777dfe2a514ee895fe007b3af36d6ddfd280113492a9` |
| `tests/test_wp801_sync.py` | `ad7e3254f09f93876ab30abd2ddc402dab9ba9fa3087af11b0ba57b6f47c5abc` |

| 2026-11-15 | wp8-03/custody-blinding (head 12521ad) | `8e48ee49b2346be97558c280224c6a3504b192fd` | WP8-03 layer 3 custody/blinding. Approved by ChatGPT R3 (independent: bundle clone, diff --check, test_custody.py 51 passed; full 186 per Claude's run). G-Z release HARD-LOCKED. Not yet run on Windows. |

### File hashes at merge `8e48ee49b234`

| File | SHA-256 |
|---|---|
| `docs/CUSTODY_KEY_POLICY.md` | `cf62b93d7beff8673b777e78c4dde79882fe51f8502b881549a55d42690b738c` |
| `src/xauusd_swarm/__init__.py` | `9191d70b416fdfe4f1071552ded6c923933f2fdcf52ea72fc21432526aa5407a` |
| `src/xauusd_swarm/charter.py` | `207967ea5f1ca981a9b4e33e1476aa93176c18145ef3c25dabb5689bda764130` |
| `src/xauusd_swarm/claims.py` | `2f955d3f58c74aa8a20fb1f089fe14a2849e9fefb643afaf4d99c82ce7c474b8` |
| `src/xauusd_swarm/custody.py` | `7095fae9b7d25bfd61cd4adfba03ebd4df894f2863938e5c29e83bfb93fdf812` |
| `src/xauusd_swarm/identity.py` | `4d472defaccc59cb8db5ad4adf120b0ba115d951c8b3190f4a78089174daa370` |
| `src/xauusd_swarm/ledger.py` | `687616d10faff2cb6ea223ed8d60c34dbfb94bd81128d1df83d0b5684e9ba9e6` |
| `src/xauusd_swarm/representations.py` | `93c6be4fd8f38ed45deb4756bf3cee18ce5f0aac7797e15ee244b7665c14302f` |
| `tests/test_branch_policy.py` | `fe0028348013be39fc346b1d053e77bb95c21b5e63f110c17e9fd70cc9f2443c` |
| `tests/test_claims.py` | `176b42eb6e57583199a45e8fb5db6d1c712168187a417ba728cf143dad71074c` |
| `tests/test_custody.py` | `7c913a09b78ca4eca388c5fbdb38e72eb943bc321b80a8e53066b9ccaff0e2f4` |
| `tests/test_governance.py` | `0a2464d1edb6d5b665c51cb269fb39e0ab62b1f729842614bb97d35edfa5f761` |
| `tests/test_ledger.py` | `9aba57749a8f2c846f0ede0e4862ae5c0944d9b80f84af2dd63647510c5fbf5c` |
| `tests/test_representations_extra.py` | `2a2751d04922f03bdce7f8b065390d401f5017c4ed7f5a4aafc1600c464a69d3` |
| `tests/test_smoke.py` | `88083e3b8f47758df8ae777dfe2a514ee895fe007b3af36d6ddfd280113492a9` |
| `tests/test_wp801_sync.py` | `ad7e3254f09f93876ab30abd2ddc402dab9ba9fa3087af11b0ba57b6f47c5abc` |

| 2026-11-16 | wp8-04/court-knowledge (head b9af4b9) | `7a4feef8ad8440cefa2f292024ecdfa07dbfaa13` | WP8-04 layers 9–10: deterministic court + knowledge registry with lineage. Approved by ChatGPT R3c, NO BLOCKERS (independent: bundle clone, diff --check, WP8-04 tests 91 passed; full suite per Claude's run). Open: A/B & FWER/FDR decision before any freeze; importance rule; CS-01-04; مع-54; OS-account separation is a deployment requirement. Not yet run on Windows. |

### File hashes at merge `7a4feef8ad84`

| File | SHA-256 |
|---|---|
| `docs/CUSTODY_KEY_POLICY.md` | `cf62b93d7beff8673b777e78c4dde79882fe51f8502b881549a55d42690b738c` |
| `src/xauusd_swarm/__init__.py` | `9191d70b416fdfe4f1071552ded6c923933f2fdcf52ea72fc21432526aa5407a` |
| `src/xauusd_swarm/charter.py` | `207967ea5f1ca981a9b4e33e1476aa93176c18145ef3c25dabb5689bda764130` |
| `src/xauusd_swarm/claims.py` | `2f955d3f58c74aa8a20fb1f089fe14a2849e9fefb643afaf4d99c82ce7c474b8` |
| `src/xauusd_swarm/court.py` | `a5471ac211751300776bb7f800e8709bec5169a63d0aac4311206fb922591dc6` |
| `src/xauusd_swarm/court_service.py` | `bb733c929ce052aaf4cb5d8464aa11b2adca455ffe897e16b83e6ebe41ac38ed` |
| `src/xauusd_swarm/custody.py` | `7095fae9b7d25bfd61cd4adfba03ebd4df894f2863938e5c29e83bfb93fdf812` |
| `src/xauusd_swarm/identity.py` | `4d472defaccc59cb8db5ad4adf120b0ba115d951c8b3190f4a78089174daa370` |
| `src/xauusd_swarm/knowledge.py` | `ceafbd23cfc2c79c3a8e611ad6570b68a5a594de010cd01782f9fa17d580a0ac` |
| `src/xauusd_swarm/ledger.py` | `687616d10faff2cb6ea223ed8d60c34dbfb94bd81128d1df83d0b5684e9ba9e6` |
| `src/xauusd_swarm/representations.py` | `93c6be4fd8f38ed45deb4756bf3cee18ce5f0aac7797e15ee244b7665c14302f` |
| `tests/test_branch_policy.py` | `fe0028348013be39fc346b1d053e77bb95c21b5e63f110c17e9fd70cc9f2443c` |
| `tests/test_claims.py` | `176b42eb6e57583199a45e8fb5db6d1c712168187a417ba728cf143dad71074c` |
| `tests/test_court_isolation.py` | `1356fd7c9406b1eb74ad0e44f7ac4568e4c2fa5795829fa71df371b0e5a3f021` |
| `tests/test_court_knowledge.py` | `e493179515b863246bfdfdfa71ec3c34f2f0629d3c69ea8bedb8985c52a8dbae` |
| `tests/test_custody.py` | `7c913a09b78ca4eca388c5fbdb38e72eb943bc321b80a8e53066b9ccaff0e2f4` |
| `tests/test_governance.py` | `0a2464d1edb6d5b665c51cb269fb39e0ab62b1f729842614bb97d35edfa5f761` |
| `tests/test_ledger.py` | `9aba57749a8f2c846f0ede0e4862ae5c0944d9b80f84af2dd63647510c5fbf5c` |
| `tests/test_representations_extra.py` | `2a2751d04922f03bdce7f8b065390d401f5017c4ed7f5a4aafc1600c464a69d3` |
| `tests/test_smoke.py` | `88083e3b8f47758df8ae777dfe2a514ee895fe007b3af36d6ddfd280113492a9` |
| `tests/test_wp801_sync.py` | `ad7e3254f09f93876ab30abd2ddc402dab9ba9fa3087af11b0ba57b6f47c5abc` |


## WP8-05 — layers 4 and 5 (inventory, C0, transforms; slicing, purge/embargo, availability) — 2026-11-16

- Merge: `7505d0d8ea89` (`--no-ff`, by Claude under FD-01). Also merged before it: `fix/windows-ci` (7518cd4),
  `fix/windows-ledger-lock` (Windows lock retry).
- CI: Ubuntu + Windows, Python 3.13, green on runs 43948438440 (push) and 43948480255 (dispatch).
- Tests: 318 passed (Claude's local Linux run). Synthetic data only.
- Decisions: FD-01-D01 … D09 (docs/DECISIONS.md).
- Repository renamed by the founder to `XAUUSD-Swarm` (2026-11-16).

### File hashes at merge `7505d0d8ea89`

| File | SHA-256 |
|---|---|
| `docs/DECISIONS.md` | `461729125dacc8d66ea245a7cb3a5575fbfa20dbc0e438fb08e245e2873a7c2c` |
| `docs/HANDOFF.md` | `98e0e5ba4bab6debfe5c1381c533f834c88af6bf9d2ab6ab9359e2af97d4d555` |
| `src/xauusd_swarm/__init__.py` | `9191d70b416fdfe4f1071552ded6c923933f2fdcf52ea72fc21432526aa5407a` |
| `src/xauusd_swarm/charter.py` | `207967ea5f1ca981a9b4e33e1476aa93176c18145ef3c25dabb5689bda764130` |
| `src/xauusd_swarm/claims.py` | `2f955d3f58c74aa8a20fb1f089fe14a2849e9fefb643afaf4d99c82ce7c474b8` |
| `src/xauusd_swarm/court.py` | `a5471ac211751300776bb7f800e8709bec5169a63d0aac4311206fb922591dc6` |
| `src/xauusd_swarm/court_service.py` | `bb733c929ce052aaf4cb5d8464aa11b2adca455ffe897e16b83e6ebe41ac38ed` |
| `src/xauusd_swarm/custody.py` | `7095fae9b7d25bfd61cd4adfba03ebd4df894f2863938e5c29e83bfb93fdf812` |
| `src/xauusd_swarm/identity.py` | `4d472defaccc59cb8db5ad4adf120b0ba115d951c8b3190f4a78089174daa370` |
| `src/xauusd_swarm/inventory.py` | `f38e0db0cbfe7f5de5e5335fe3da2df39a4e5b1ed23be7661d993b45b1fe3355` |
| `src/xauusd_swarm/knowledge.py` | `ceafbd23cfc2c79c3a8e611ad6570b68a5a594de010cd01782f9fa17d580a0ac` |
| `src/xauusd_swarm/ledger.py` | `86324d6a8d5272ae22a53d7e255207d03f5eaf054af8caaef0f0e344bfadd97d` |
| `src/xauusd_swarm/representations.py` | `93c6be4fd8f38ed45deb4756bf3cee18ce5f0aac7797e15ee244b7665c14302f` |
| `src/xauusd_swarm/slicing.py` | `8058adb631c314f95c27ddcd6a7e0ef6da33104006e98132c748c53d843c6b7e` |
| `tests/test_branch_policy.py` | `fe0028348013be39fc346b1d053e77bb95c21b5e63f110c17e9fd70cc9f2443c` |
| `tests/test_claims.py` | `176b42eb6e57583199a45e8fb5db6d1c712168187a417ba728cf143dad71074c` |
| `tests/test_court_isolation.py` | `1356fd7c9406b1eb74ad0e44f7ac4568e4c2fa5795829fa71df371b0e5a3f021` |
| `tests/test_court_knowledge.py` | `e493179515b863246bfdfdfa71ec3c34f2f0629d3c69ea8bedb8985c52a8dbae` |
| `tests/test_custody.py` | `82aa86f40cce75a914dbc1ced641e1cad9cd25c1cc1d1c4b5fd5a71d97d1ea59` |
| `tests/test_governance.py` | `0a2464d1edb6d5b665c51cb269fb39e0ab62b1f729842614bb97d35edfa5f761` |
| `tests/test_inventory_slicing.py` | `bbf27deee44b2c62fffa0f951e2012b053531d5cb0a90798c0433eb407c02bea` |
| `tests/test_ledger.py` | `6d9e6f0bfe3993d9d6137bf874c930434b332bf311efab3c0cfba74e86e1f26d` |
| `tests/test_representations_extra.py` | `2a2751d04922f03bdce7f8b065390d401f5017c4ed7f5a4aafc1600c464a69d3` |
| `tests/test_smoke.py` | `88083e3b8f47758df8ae777dfe2a514ee895fe007b3af36d6ddfd280113492a9` |
| `tests/test_wp801_sync.py` | `7d43d2272fe5c1ad4674d999cb91c55c34446855117624501b465b1ede76d084` |

## WP8-01 package 02 (FD-01-D10) — 2026-11-16

- Built with `git archive --format=zip --prefix=XAUUSD_SWARM_BUILD/` of `main` at
  `00e35872efb1de3d68a4e79dffa1712d8aeab548` (67 files).
- ZIP: `XAUUSD_SWARM_WP801_package02.zip`, SHA-256
  `5b4622b42d499dc11ebedbc035996d9775edb4104b5346a9009d4434ee928aab`.
- Check before handing over: extracted on Linux, `pytest` → 318 passed (Claude's run). The Windows
  run by the founder is pending; package 01 (afcb45a4…) is superseded.

### WP8-01 package 02 — founder's Windows run (2026-11-16), report as sent by the founder

- repo `C:\XAUUSD_SWARM_BUILD`, commit `19bd1c3506037ccdcf965903b12321404624fd8c`, branch `main`
- Python 3.13.0; git 2.56.0.windows.2
- dev `C:\XAUUSD_SWARM_BUILD\_envs\dev`, test `C:\XAUUSD_SWARM_BUILD\_envs\test`, separate: yes
- unit tests: 317 passed, 1 skipped (the skip is `test_no_unsafe_fallback_when_primitive_missing`,
  POSIX-only by design)
- PROVENANCE.md sha256 `2cb507e0445165877e6aded6a33e86f4a5c0ca2647b7b33e97dfd2b468d04cc4`
- Git printed LF→CRLF notices for text files; they do not change committed content.


## WP8-05b — review round R1 fixes (ChatGPT: NO BLOCKERS; 4 MAJOR + 1 MINOR fixed) — 2026-11-17

- Merge `fa6945cb4de2`; CI green Ubuntu + Windows (run 43960661623). Tests: 329 passed (Claude's local run).
- Register: docs/audit/WP8-05_register.md (OPEN COUNT 0). Decision FD-01-D11.

| File | SHA-256 |
|---|---|
| `src/xauusd_swarm/inventory.py` | `e63ac8c870cf73cdcd5ae926155014a84e155609fe5beb07959e2ec9721ccbcc` |
| `src/xauusd_swarm/slicing.py` | `e9ef2e059c7a0b81b9da0c773a976e2057ed10cc2336fd43c914c3b99aa63739` |
| `tests/test_inventory_slicing.py` | `3760ae6c3f7c91799271addb3716c949857979d95e13c7dc492c74ddba8c6366` |
| `docs/audit/WP8-05_register.md` | `c04ece2014ced1300f35db345a09c972c2a60379db8f86e0758e470858bd05fd` |
| `docs/DECISIONS.md` | `196183127aebb707d44bc92e2a04ca5edda19ee197306851a475852b1f83e2e6` |


## WP8-05c — review round R2 fix (R2-01 MAJOR + S2-01) — 2026-11-17

- Merge `24c016ef1384`; CI green Ubuntu + Windows (run 43963414829). Tests: 331 passed (Claude's local run).

| File | SHA-256 |
|---|---|
| `src/xauusd_swarm/slicing.py` | `5932a53fdb43f1321ed5cb582704aada874d1767163087ca986fcc31e15ea57f` |
| `tests/test_inventory_slicing.py` | `cee02c2fd14ed22200a29ae49e09b15486ba6614ea7f6b813a6ed7167a7db29b` |
| `docs/audit/WP8-05_register.md` | `637971443bb6f0c2deee33ecf5f995e7b5c3b56d7fd622df2fe8c5ad6d7a0432` |


## WP8-06 — layer 6 evidence economy + TP-88 (Holm/FWER) — 2026-11-17

- Merge `a4f175b01660` (`--no-ff`, by Claude under FD-01); CI green Ubuntu + Windows (run 43965792093).
- Tests: 363 passed (Claude's local run). Synthetic data only.
- TP-88 registration sha256 `fb7d0da123ea7f0bccac0a52f5221de015d2ad54fbc7dd562b2809bb001226d5`; FWER measured
  (local run): independent 0.0430, equicorrelated 0.0398, block 0.0360, mixed sign 0.0470, shared time
  data 0.0335, unique-claim (structure B) 0.0455; bound α + 3·MCSE = 0.0603; negative control exceeds
  the bound. FDR part not run.
- Decisions: FD-01-D12 … D14.

| File | SHA-256 |
|---|---|
| `src/xauusd_swarm/evidence.py` | `8a1802a1ec30fe77a0d3d252383ba0203bc2041d9f8b17334e358bda7abf7a26` |
| `tests/test_evidence.py` | `f11952f8c180bc047e743cbb38ceee67dd8d49f9a8df1d441db4d1c783ee58e8` |
| `tests/test_tp88_holm.py` | `1b998077d424ac69c2fdd2e2eb66a6abf65d09bec9863ff4cf38ac8bf46feabd` |
| `docs/DECISIONS.md` | `0b18f1c3273630b997f7b618f43174cff8b067efb2771a4c70fed0230e7d2adc` |


## WP8-06b — review R1 fixes (atomic Final opening; pinned TP-88 hash) — 2026-11-17

- Merge `7fd3c747efbe`; CI green Ubuntu + Windows (run 43967133461). Tests: 364 passed (Claude's local run).

| File | SHA-256 |
|---|---|
| `src/xauusd_swarm/evidence.py` | `f1cf49592c06cda5d6aec1fa181f0d5652aa093bf183c8718dca27434094aa62` |
| `tests/test_evidence.py` | `5476cada68dac3fc157fb394be7116bd1a489f2af1754ffc8735a1a288874c31` |
| `tests/test_tp88_holm.py` | `494e69bf8a789bbf6844d531e61b74e3ca851c322228e030507406d889f40728` |
| `docs/audit/WP8-06_register.md` | `149e15de77364370d7bd53f36e6620e21c4d90dcec7285fbc4eb0e3f03aee7ea` |


## WP8-06c — review R2 fix (signed Final opening manifest) — 2026-11-17

- Merge `9c9d09baa586`; CI green Ubuntu + Windows (run 43968274066). Tests: 365 passed (Claude's local run).

| File | SHA-256 |
|---|---|
| `src/xauusd_swarm/evidence.py` | `8bf91e3efc97a19e1bb632c9ebc7cfa26dedcd07dd7e0e53bda8766cd687900f` |
| `tests/test_evidence.py` | `c5da619b5c754c0999897ce604d7db5324869c3b4c3c46bb9fd8309571dd58d2` |
| `docs/audit/WP8-06_register.md` | `1d3e84fe08e141605b0249cd48f924d4acd80216e3b4368147de38a7dd6372a9` |


## WP8-06d — review R3 (test coverage for signed-manifest tampering) — 2026-11-17

- Merge `5465c112df95`; CI green Ubuntu + Windows (run 44032613931). Tests: 366 passed (Claude's local run).
- WP8-06 review: R1 (1 MAJOR, 1 MINOR), R2 (1 MAJOR), R3 (1 MINOR) — all fixed; OPEN COUNT 0.

| File | SHA-256 |
|---|---|
| `tests/test_evidence.py` | `cbfd01a4ca05d9e51ccac755ce9da6b813ab931c86c4868c3446aa862fefc96f` |
| `docs/audit/WP8-06_register.md` | `7433db1a141e7a0305def62ebccc1cf8f2a1ec9ef13640a2cc1d23318af49175` |


## WP8-07 — layer 7 discovery system — 2026-11-17

- Merge `ee6eb746ad9f` (`--no-ff`, by Claude under FD-01); CI green Ubuntu + Windows (run 44037349955).
- Tests: 392 passed (Claude's local run). Synthetic only; no engine or model is run.
- Decisions: FD-01-D15 … D17.

| File | SHA-256 |
|---|---|
| `src/xauusd_swarm/discovery.py` | `2f015f725b5b07ec705ce6e374479fc734774872e0c8db3be78e3a926ffc7cb8` |
| `tests/test_discovery.py` | `8f300a3920c87390a4eebbdfceb9635938aa8f34a5d208dd26e69a7043953ec1` |
| `docs/DECISIONS.md` | `05913ec2c9855c94f35e0b3cccce3527027118c1affe4a932dda2edc1abe1188` |


## WP8-07b — review R1 fixes (null cards, completeness, compute time) — 2026-11-17

- Merge `995d4f27c22f`; CI green Ubuntu + Windows (run 44038830903). Tests: 409 passed (Claude's local run).

| File | SHA-256 |
|---|---|
| `src/xauusd_swarm/discovery.py` | `05454e04b6608a22ae9c4bb309750034c86f1da13c00a0283f96b6a4ace93d2a` |
| `tests/test_discovery.py` | `c8d44cea8df988c026b1f764f07c1e5a5f485e83b4e218e0efcec622d5754e27` |
| `docs/audit/WP8-07_register.md` | `31fa2131acf3a70f53391acc7383e65541d9af209df17b6915e23253040cd1e2` |


## WP8-08 — layer 8 falsification and confirmation — 2026-11-17

- Merge `fb1455bc01d5` (`--no-ff`, by Claude under FD-01); CI green Ubuntu + Windows (run 44040494876).
- Tests: 420 passed (Claude's local run). Synthetic only; no statistic or null generator is run.
- Decisions: FD-01-D18 … D20.

| File | SHA-256 |
|---|---|
| `src/xauusd_swarm/falsification.py` | `be9e885d0a0d885169ead4413308d10bfaf5d6285cd9a56d331228cc0ab2d12f` |
| `tests/test_falsification.py` | `fe2e4b3f49f24cafbf1caf902fcb3f0ca3d7281ba0198ed7b6c8d15ed7e2986f` |
| `docs/DECISIONS.md` | `c770871b4a8e848a2100d1a34907cf6402482b5be03a45c2a4701e7a74579aac` |


## WP8-08b — review R1 fix: null validity from recorded controls; controls registry — 2026-11-17

- Merge `f3cd7345bd16`; CI green Ubuntu + Windows (run 44041995649). Tests: 422 passed (Claude's local run).
- Decision FD-01-D21 (amends D19).

| File | SHA-256 |
|---|---|
| `src/xauusd_swarm/controls.py` | `10508060a39ef57f20f07f1c686fa870b47aeccd301367687baa3d4546c030b5` |
| `src/xauusd_swarm/falsification.py` | `263697796f373d38e48060899c650f94841550a1b057324cdddbb93b14aaf10a` |
| `tests/test_falsification.py` | `45467fdcb43edde11fc46075b3368d1d9306599943b9ee80210a44a77009943c` |
| `docs/audit/WP8-08_register.md` | `54e296ad0baf4d31c00f4f0f977b384d80503604c560604706594c466686c39e` |
| `docs/DECISIONS.md` | `3923014223a42c2f8be1e8854e3edfb16a2329703c973b9189d4150d764f2349` |


## WP8-08c — review R2 fix: verifiable control execution; flaky test fixed — 2026-11-17

- Merge `9434b285d648`; CI green Ubuntu + Windows (run 44043192500). Tests: 425 passed (Claude's local run).
- First CI run of the branch (44042948366) failed one pre-existing test by chance: a 2-byte plaintext
  marker (b"T1") occurred in random ciphertext. The marker was replaced by long markers; no production
  code changed for it.
- Decision FD-01-D22 (amends D21).

| File | SHA-256 |
|---|---|
| `src/xauusd_swarm/controls.py` | `5100d33c43401aa9e88a5efa807b63009390bb559796697a8b0f4d52cb42037f` |
| `tests/test_falsification.py` | `57e2590144ea05e11e1d425c4772a42c4332afcee7a0a4f14c4f5bc766eb53da` |
| `tests/test_court_isolation.py` | `723ead1a495d2e359420cd665f5870fb00f2dbe936d0991960d9792ee28b6f37` |
| `docs/audit/WP8-08_register.md` | `ca95b2a18a05346c88cb1473596199a263931b922024c473889ff76ad7ac3a4c` |
| `docs/DECISIONS.md` | `8aef105a3e8a2200808c4789b5df35304d537d86cb483045bf3ec52aa39bf054` |


## WP8-08d — review R3 fix: mandatory independent re-execution of control results — 2026-11-17

- Merge `625627973f37`; CI green Ubuntu + Windows (run 44044146818). Tests: 428 passed (Claude's local run).
- Decision FD-01-D23 (amends D22).

| File | SHA-256 |
|---|---|
| `src/xauusd_swarm/controls.py` | `82ead1960b33d41326c8118cfd0e2a62b768fc7c794d2db385a5a937d7ef19c3` |
| `tests/test_falsification.py` | `8549d98c85f7510eee5ef1af12495cab18a76383754cb6dbab5dcdebefa37212` |
| `docs/audit/WP8-08_register.md` | `58e2058a3dad41419de737e040e3b8d4fc024ca1b417a9602399c74547c2eefa` |
| `docs/DECISIONS.md` | `8de187cfa13f3aae17310b583192f0e0cb87c3b4eb74b2a39abc8c1609ea24b2` |


## WP8-09 — cross-cutting axis: control matrix per tool + governance audit — 2026-11-17

- Merge `7497a69bc39f` (`--no-ff`, by Claude under FD-01); CI green Ubuntu + Windows (run 44046433770).
- Tests: 439 passed (Claude's local run). Synthetic only; no control code or planted world is run.
- Decisions: FD-01-D24 … D25. With this merge all ten layers and the cross-cutting axis of Stage 8 are built.

| File | SHA-256 |
|---|---|
| `src/xauusd_swarm/controls.py` | `118f532617015e4168a8914b3a90a7d14973ee83360ddb7735a609e121d18f4c` |
| `src/xauusd_swarm/governance_audit.py` | `3ec3b65388a00caf3b90b525d527721ca5adb9cd19f58ac23ef0de967e09079c` |
| `tests/test_controls_axis.py` | `315b71f475cc7d1f31f1e018dc6547be9fc51faa0c7862b1e50cd89968e08a0c` |
| `tests/test_falsification.py` | `dcb634436824456f1d37018952e42605209c6082d63eebd13bf6264b84098317` |
| `docs/DECISIONS.md` | `aec9718749d14b6674244d1012cf3b57880e818b49605bfd2a4af288a6e5925c` |


## WP8-09b — review R1 fixes (all tool kinds gated; unique planted types) — 2026-11-17

- Merge `0d16b82a20af`; CI green Ubuntu + Windows (run 44047752244). Tests: 444 passed (Claude's local run).

| File | SHA-256 |
|---|---|
| `src/xauusd_swarm/controls.py` | `1ac7f3bb919821091f67ff4e34eb9cda6512017f4c03a45efaaaa894d2d1b600` |
| `src/xauusd_swarm/governance_audit.py` | `57b1ab6edba3d62cb2a7e7fcee0784c6123986de72ece144c376b0f7eab76f15` |
| `tests/test_controls_axis.py` | `e973f8e263d3c0b4b9536de98fb72feff4c537db524d111de8b063441bdc88c7` |
| `tests/test_falsification.py` | `1dc23e081b32f910cc036d9a5ee12043760d8e1ac094b741b160c564ba8897f2` |
| `docs/audit/WP8-09_register.md` | `4d66331bbe024a7c1a79cbfb365894ad641d52f83a45db1fc3b6ce9dfacb1691` |

## WP9-01a — Stage 9 plan, failure log, ledger-level end-to-end integration — 2026-11-17

- Branch `wp9-01/integration`; record written on the branch (FD-01-D26); CI = the run on this commit, merged only when green.
- Tests: 448 passed (Claude's local run). Synthetic only. Path environments Z / G-Z / R not yet built (gap G1).
- Decisions: FD-01-D26 … D28. Failures logged: FL-001 … FL-006.

| File | SHA-256 |
|---|---|
| `tests/test_integration.py` | `d44780cc82bd3ceea58a90a298cdcee447a3a30cb19f15d5d085827133e5e4f7` |
| `docs/STAGE9_PLAN.md` | `895667c352ad75a6f4e702ffe4a507a572beb12b17fbb3e45bc14dde08c4ffbe` |
| `docs/FL.md` | `cd4abece86ea8454a37af754c31997c9e0d2076cc6606c7abb6b1efd9718f16b` |
| `docs/DECISIONS.md` | `97d7bb051a4b0b260d205223f58a65f8fe9a4da0d1d1997abf25321f81d4d2b8` |
| `docs/HANDOFF.md` | `08fb88c01b90fe1b4735478ba629db9b876d322c05d3fcffa5eda925eab54433` |
| `CLAUDE.md` | `0c889bc4e43b71ff24a6bab3d644b979b6e3006a433c30484d4fd6ba7a3f4506` |

## WP9-01b — G1: paths Z / G-Z / R and their flows; founder decision OD-S9-01 (path 1) — 2026-11-17

- Branch `wp9-02/paths`; record on the branch (FD-01-D26); merged only after the CI run on this commit is green.
- Tests: 465 passed (Claude's local run). Mutation check: removing any of four rules (R → Z, «تداول» tool, R content into Z, custody passage) makes tests fail. Synthetic only.
- Decisions: OD-S9-01 (founder), FD-01-D29.

| File | SHA-256 |
|---|---|
| `src/xauusd_swarm/paths.py` | `68d722c2e410ac1342fd2712ac4ebcab76f8746fdaa23856a64ca2739cbca223` |
| `tests/test_paths.py` | `34fdb08f1d8a66e1a3ccf791342ab2c345991be2b369269cd6948a3a7c891568` |
| `tests/test_integration.py` | `12104f78755002a3631512040054f81528b839a3b5b6cf85ac515e2dfcec4a00` |
| `docs/STAGE9_PLAN.md` | `4c82704a02fa0a4006e632d32c735874cb0763ecd11b2c58b7a987450adda4bc` |
| `docs/DECISIONS.md` | `9004838a0dddd58c3dd45f673a9f990f64df50304bb439d8d03ed36bca438fd6` |
| `docs/HANDOFF.md` | `fa9d663d7123fbabbe084a5506ce93134d523d1ec038d72fc92e45aefb0f0652` |

## WP9-01c — review R1 fixes (R origin of layer (أ), closed field sets, full-state replay) — 2026-11-17

- Branch `wp9-01c/review-r1`; record on the branch (FD-01-D26). Tests: 470 passed (Claude's local run). Synthetic only.
- Register: `docs/audit/WP9-01_register.md` (R1-01…R1-04 fixed; S1-01 deferred with a planned test).

| File | SHA-256 |
|---|---|
| `src/xauusd_swarm/paths.py` | `6e84c073ab4e964d5b10ddaa54da5ef46ba960c17c0cd15d040cb1d335e6cf61` |
| `tests/test_paths.py` | `faf1aecf7acebe74b6b32fae670b756e1542e78e9b7c8ff3d79a9bee3843e905` |
| `tests/test_integration.py` | `76640d47e9beabcc125f992cdd975e3f58cbef6479ee0a70b6df63589be1d38a` |
| `docs/audit/WP9-01_register.md` | `ce515bba34f18ed5c9b869352ae6f3736737312ed0d22726c86e8a87060ae4b0` |
| `docs/STAGE9_PLAN.md` | `2c3c1de1979727d0cb3b57233bef648902b2fc4076f94c5f223e5fe0d8f695b7` |
| `docs/HANDOFF.md` | `64beed5f84a97ce78d4eca572b3cb1d10fd737f5ea459ccb26c6aff1042f1f6d` |

## WP9-01d — review R2 fix (recursive full-state comparison) — 2026-11-17

- Branch `wp9-01d/review-r2`; record on the branch (FD-01-D26). Tests: 473 passed (Claude's local run). Synthetic only.

| File | SHA-256 |
|---|---|
| `tests/test_integration.py` | `25ee42b5b91152d86e20aa9cf50c1225852be0524da646fe9ae7e147cf78f76d` |
| `docs/audit/WP9-01_register.md` | `aa62282b30d2eb83342eb15a5e0eab1294129e5a6e097abb9ce8e435343ff847` |
| `docs/HANDOFF.md` | `c32d1252014d6947b088ec7b78e9077d12a13ce73f6b53f969d10eebb3b5be8a` |

## WP9-02a — G3 null generators; TP-21/tool for the §11.2 null cards (actual results) — 2026-11-17

- Branch `wp9-02/nulls-controls`; record on the branch (FD-01-D26). Tests: 484 passed (Claude's local run). Synthetic only.
- Criteria pre-registered before any run: FD-01-D30 (commit fd54402); v2 after FL-007: FD-01-D31 (commit 7bf81d5).
- Results: full_shuffle +0.85/−0.067, iaaft +0.925/−0.075, pair_shuffle v1 +0.683 FAIL/−0.017, v2 +0.817/−0.017 (positive ≥ 0.80, negative ≤ 0.15).
- Also carries the WP9-01 review closure (NO BLOCKERS).

| File | SHA-256 |
|---|---|
| `src/xauusd_swarm/nulls.py` | `5ec7ed8c7a2eaa71278fecc3b4cc81a8d530dde1e18c985b656313b5ce223591` |
| `src/xauusd_swarm/control_runs.py` | `5f0ddbafdf94a747edb7a00ca8ba7d074e8a302d5fca4afb5c45d45abcf531dc` |
| `scripts/wp9_02_null_controls.py` | `fbd548f85944eb898a57b683fdfb864f4372fae97f79b0400ba841326aa705ad` |
| `tests/test_nulls.py` | `57a56f4f1699cdfa2bd90303f4f08cc17b6363c05e98b50e52f59ce31fb8184b` |
| `tests/test_wp9_02_null_controls.py` | `6c1294e20c1011e6d82de790108721e21c90eb582e690e14f5f68e5981638406` |
| `docs/results/WP9-02_null_controls.json` | `8aa619b4365d74956fec72fceb22cb91aa8cef57b65ee17137bf7b0b1d812362` |
| `docs/FL.md` | `af390feb462ef11be2ffa585809beb306cf89153abe78aebcb4da5cff2047ed8` |
| `docs/DECISIONS.md` | `15ba3765ab710d17c64bc5df8ecfb22d993202d601856db5432d05810ee18426` |
| `docs/STAGE9_PLAN.md` | `de2c829817ece98d89bb68cc4c97e3321d1278da6e25bd025cd701e4fd91233c` |
| `docs/HANDOFF.md` | `5b5794875eae39c947a8b5ff2072198f20b5b406bcfbd12d6b74152db020e9a8` |
| `docs/audit/WP9-01_register.md` | `a262a97735e451eb4465eefddd993816d8552add0ab2e8a1366e66d0a2deb157` |

## WP9-02b — TP-47 (C0 gate) and TP-46 (court) controls (actual results) — 2026-11-17

- Branch `wp9-02b/c0-court-controls`; record on the branch (FD-01-D26). Tests: 487 passed (Claude's local run). Synthetic only.
- Criteria pre-registered before any run: FD-01-D32 (commit ef5c70f). Results: TP-47 4/4 pass (feed→1, processing→2, order→3, clean→4, exact scopes, no cross-talk); TP-46 2/2 pass (planted K1,K2 confirmed, K3 not; null world none confirmed); ruling output identical across two independent systems.

| File | SHA-256 |
|---|---|
| `src/xauusd_swarm/gate_court_controls.py` | `e90eb01e105f002c37d5a9d522437567eb05ca9faf5815cdf060ad122d7f8041` |
| `scripts/wp9_02_gate_court_controls.py` | `fdd765522abe6db64590676d6a03efda69bd56e4ab2c95f561c9a026909b9550` |
| `tests/test_wp9_02_gate_court_controls.py` | `6a18b09b056bd78f2f3b3faa51cc87f902d39f249ac7e41e8574bf90e0c16955` |
| `docs/results/WP9-02_gate_court_controls.json` | `8fc54489246d99efcdf9476808b3f2080c014944f87c476228981881a737ab79` |
| `docs/DECISIONS.md` | `f028ddcec65f530426b78d48a95dc47c4226ef660836c45d4d51b48e9edcf8c2` |
| `docs/STAGE9_PLAN.md` | `ff28f3a741df36193ac4df884f7ef6e04e4e00df3b872a43f17468831abe939d` |
| `docs/HANDOFF.md` | `c796b79f6bfce288804507911752288892bc20db236b0948fe3ab30ac725c0cb` |

## WP9-02c — WP9-02 review R1 fixes (finite-number validation) — 2026-11-17

- Branch `wp9-02c/review-r1`; record on the branch (FD-01-D26). Tests: 502 passed (Claude's local run; first written as 495 before the count, corrected). Null-card controls re-run on the fixed code: identical results; module hash updated.

| File | SHA-256 |
|---|---|
| `src/xauusd_swarm/nulls.py` | `ab747cc0cbecd36136941b53f526d51925212b3f82d7501ca5d656be4a3fa8b2` |
| `src/xauusd_swarm/representations.py` | `2d8d2f7ecb0229a4a05a29650813a3c8ae5b147cc854e4832eac6b9b2cd7c822` |
| `tests/test_nulls.py` | `ea750766e64b879affe06dedb64fa29208c61fc773d9853e7a4d8a7fd59ab772` |
| `docs/results/WP9-02_null_controls.json` | `bb4b0bc815970d54ba53e8cb35b3ff1b148708673488cedf7eaef0d4cda97ab2` |
| `docs/audit/WP9-02_register.md` | `50cf5ca3f609349b07a3b0ac25529225329e7a5657e0917d4526c97557b740a1` |
| `docs/HANDOFF.md` | `01f62836469da05ba3a752b01ea09668515a797a783f5bcf4726b566a21fff50` |

## WP9-02d — WP9-02 review R2: one numeric check for the package — 2026-11-17

- Branch `wp9-02d/review-r2`; record on the branch (FD-01-D26). Tests: 596 passed (Claude's local run). Controls re-run: identical verdicts; court output hash changed with court.py (recorded).

| File | SHA-256 |
|---|---|
| `src/xauusd_swarm/numeric.py` | `03d8449e2ae1681a5795559a53551b3c248357ac40f25356094468b437daa631` |
| `src/xauusd_swarm/representations.py` | `1831980210b84e409b898f72daaf26a7f8e515373c08b607808cb37f8b26466b` |
| `src/xauusd_swarm/nulls.py` | `5f99a60771c7c7120eeca936c9c9f5cc2973ff3db3714bffdc2076ef0cd8b444` |
| `src/xauusd_swarm/court.py` | `041ab8dc652db4648a7c5739b8650f95b5a6ccba914e6680d101d35161e45117` |
| `src/xauusd_swarm/controls.py` | `5b760864e5280b9a0edf82dd89f6ae40feef85b0dc25b3eb95b42ef4e4e799b5` |
| `src/xauusd_swarm/evidence.py` | `3d5653ff8e07b2fecd3c5a0f2d2421d653720742baea5bd52d7ba717be0240ac` |
| `src/xauusd_swarm/slicing.py` | `38d291030a1b59871b4b48bdcd33da26859265c02cfee0be6ec3429913d103a1` |
| `src/xauusd_swarm/inventory.py` | `c051a869b31800eff331c2f24f7d294ef26ce916cc62f7c8eb9fbd60686f3481` |
| `src/xauusd_swarm/discovery.py` | `61dbf67e0326c559b00b5ecba3e51dea144ebb3c178e5f9b61efa8d3a2e807ad` |
| `tests/test_numeric.py` | `f86e00f574fcf4ddc805bf0a76754c70d9d3e65cead54f6b2825051be55c417a` |
| `docs/results/WP9-02_null_controls.json` | `97c9c3740d5bbb5d97a32a7bcb1dade3e413ac97a23260fb0b282ab3f2e19f53` |
| `docs/results/WP9-02_gate_court_controls.json` | `edc6a04858874b34bca627cd1cf5b372e630dc56476bd4b14b20a4a3a677a021` |
| `docs/audit/WP9-02_register.md` | `fad2c34c1b0f79ade5a5b0764387a3e7726b135d22b83868fca6ff78a101124f` |
| `docs/HANDOFF.md` | `74112228598aab2c4292faf941a1d26639527749896ce480d78eb0247fb7ae0c` |

## WP9-02e — WP9-02 review R3: numeric parameters of transforms; vault params; NaN leak-check hole (FL-008) — 2026-11-17

- Branch `wp9-02e/review-r3`; record on the branch (FD-01-D26). Tests: 667 passed (Claude's local run). Controls re-run: identical verdicts; court output hash changed with custody.py (in the court code manifest).

| File | SHA-256 |
|---|---|
| `src/xauusd_swarm/representations.py` | `7ff8b95515401c2a74011cca9338ffb3cd67998ee91f9900aee494104c9dda4f` |
| `src/xauusd_swarm/custody.py` | `2f6c12b4acdddc0ce1c2e0b034d08965972033c210a5bacedf60171bc2997fbb` |
| `src/xauusd_swarm/slicing.py` | `cf25ea6bca165bfd62b0acab167c236cdcf4a256835e6510d6e619ef439ed2d6` |
| `src/xauusd_swarm/nulls.py` | `afaf5b7f3fd1ecd063e3751b46da5a1fa98387ce69c85712dd71e852c072b5e1` |
| `tests/test_numeric.py` | `2c368d9a996a17477e6ec7675ea2a29a5d55564caf78f6f1787165cad591321b` |
| `docs/results/WP9-02_null_controls.json` | `7f963510c07ac3bc048464dd6ee3b4f907e89b21796d72cf69ec9b3d6d58ffdd` |
| `docs/results/WP9-02_gate_court_controls.json` | `1b81647b041415493c529e4392426af9e3cf193c5693be081ef5228ed6172bea` |
| `docs/audit/WP9-02_register.md` | `8bb7a6823d1927030b89b40953fd15e3cd3c68da8f40ce60c5469f61e6c07812` |
| `docs/FL.md` | `2db22c5dddd21461a46d23044866fcfb28912c16b8276578669ed49942e68687` |
| `docs/HANDOFF.md` | `9e6cc4021cbe800510c6a7f737a33608f234db959e74723e91f45d93751551b0` |

## WP9-02f — TP-81 and TP-82 (measure and declare); FL-009 — 2026-11-17

- Branch `wp9-02f/tp81-tp82`; record on the branch (FD-01-D26). Tests: 670 passed (Claude's local run). Design pre-registered before any run: FD-01-D33 (commit 2ac214c). Also carries the WP9-02 review closure (NO BLOCKERS, R3).
- Results in `docs/results/TP81_TP82.json`; readings in `docs/STAGE9_PLAN.md` §6. FL-009 open (TP-82 profile metric).

| File | SHA-256 |
|---|---|
| `src/xauusd_swarm/assumption_tests.py` | `9d8d0d89263b2747e9911bed10f97e42c6a02c330fe9ec1c65fc6c50e58a435a` |
| `scripts/tp81_tp82.py` | `a66c380888f3d1977687452ab5ae15d18ea2ebaf51c67be4999c7c7531c23e67` |
| `tests/test_tp81_tp82.py` | `dae0d5140e98cb655aaf89c181441c6bcba57765eb89116ca441c1eb228b387f` |
| `docs/results/TP81_TP82.json` | `b187d7789483aec5fb8edfe1f891b10d075f5457d0bc803f50f582aaa0c8a859` |
| `docs/DECISIONS.md` | `18f0254b9fc5772379c90700414ece5ac2faa8292cb08a0552ea38fcd4f7637b` |
| `docs/STAGE9_PLAN.md` | `5be078d0dddb377adced593b82f70cc0f4d987ef0ca77bd82002325a562b2b18` |
| `docs/FL.md` | `4661d0b2e702eaf00bae2918247a356aedd395b19ba05497e36289a06b6e3547` |
| `docs/HANDOFF.md` | `3c7e68a3c4c920f5476877c4af9069b3ef6747eae6c8a061eb63c15d8f5618df` |
| `docs/audit/WP9-02_register.md` | `a56ab4d0c1505a2875844eee7eebfd5ecf0b69e0b36d3fd14d0b867ceb8dbe91` |

## WP9-02g — TP-81/82 review R1: IAAFT use restriction at use points; TP-82 v2 metric (FL-009 closed) — 2026-11-17

- Branch `wp9-02g/review-tp8182`; record on the branch (FD-01-D26). Tests: 674 passed (Claude's local run). v2 pre-registered before the run: FD-01-D34 (commit a5eb84f). Same seeds: all earlier rates and coverages reproduced exactly.

| File | SHA-256 |
|---|---|
| `src/xauusd_swarm/controls.py` | `99e4f3948c63b1d2dd4d18b391d0a306485b8eab0f06e083dd628405816fbbaa` |
| `src/xauusd_swarm/assumption_tests.py` | `eb6b56b3d937cdbfd9f6582375e3ff1f70071af00d38f274d989ce1c4d9e8313` |
| `scripts/tp81_tp82.py` | `94e1eb631e9f3ae9d44ee0d0bf334231e95d247de791b1af200d31c33a7b530d` |
| `tests/test_falsification.py` | `b4ae46ba375cc665bc3583b9ad4ce3955f69e146564b6e379b152d527660e8ef` |
| `docs/results/TP81_TP82.json` | `afcfdf8f8d102e4adffe05f8f6a9736d62459109c384a4216d73e87a5354304c` |
| `docs/DECISIONS.md` | `e31cb70c60b6d7897b053d79d22bb8ccfaadbe9be501eda2140ef3588d0eaee7` |
| `docs/STAGE9_PLAN.md` | `c5c985e0c8b88da4547c0c32c60d360a5e7aae9e9276e49a192fb443d6cb4db4` |
| `docs/FL.md` | `4b97d345057a22b77b2b9663e63290d6273f6a463b266ceee5282983c276f1f4` |
| `docs/HANDOFF.md` | `8c096cc6f8033ae012d0c05efd363a4adeaa668f76490762fa694c8fb5216906` |
| `docs/audit/TP81_TP82_register.md` | `1a4985164ce7ccc0f583ce5c3964212b52989dd43f61ecc6c89a9a81da11ed5f` |

## WP9-02h — TP-81/82 review R2: IAAFT restriction mandatory by its card — 2026-11-17

- Branch `wp9-02h/review-tp8182-r2`; record on the branch (FD-01-D26). Tests: 678 passed (Claude's local run). Null controls and TP-81/82 re-run: identical results; nulls.py module hash updated.

| File | SHA-256 |
|---|---|
| `src/xauusd_swarm/controls.py` | `91534ae5f9a89590c5069600f7ea1c0160eb3ce5ca4e555295b271e30655ec61` |
| `src/xauusd_swarm/nulls.py` | `3c73f39aa69d3e5d569341d666994cc663efda2e1af42fc6bdd9ecca8cc221fe` |
| `scripts/wp9_02_null_controls.py` | `05a19c14336f4abe45b34ea33ebfa5a75e79e6554413f3b428ba6ea91c51db0b` |
| `tests/test_falsification.py` | `1a4fd31e2b6de0671cadf4b13aeaaee591bfba4c3de9fda8aab50cfd26136b34` |
| `docs/results/WP9-02_null_controls.json` | `319e10b92d4b8c2706a8caf35e5e8a2e5af06a415c4be8418b0cd8e8f8de0bdf` |
| `docs/results/TP81_TP82.json` | `dead57944cfb66381ff6912d625b9d48fe414f123ed30247c4312b289b8dc175` |
| `docs/audit/TP81_TP82_register.md` | `42a414dd4003cbb60426185ec4dc466818e2d54e0d3e8ab2d2cbaffcaffe38b6` |
| `docs/HANDOFF.md` | `56ff6370ad7238bcfb7936c1480ea349fe9b29698fab88c4896b5f34e3155329` |

## WP9-02i — path 1 (P1-distributional) built; TP-21/tool v1 and v2 FAILED (FL-011, open) — 2026-11-17

- Branch `wp9-03/path1`; record on the branch (FD-01-D26). Tests: 684 passed (Claude's local run). Synthetic only.
- Pre-registered before runs: FD-01-D35 (78811ed), FD-01-D36 (35592b9). FL-010 (runner crash, fixed), FL-011 (critical, open). Also carries the TP-81/82 review closure.

| File | SHA-256 |
|---|---|
| `src/xauusd_swarm/path1.py` | `265711b0ec25bda9ffcff49a48f71560ae3d994f6a2f8d22a6f634b3100ddb5b` |
| `docs/paths/PATH1_CARD.md` | `811377327cb374d027ca686676d63bb8bb6a10e19a6e18a60310ce011eced4cd` |
| `scripts/wp9_02_path1_controls.py` | `4462e27c228c03e7999c8873f14bbc5dd943e3766c2797d5654f9d6acb67498a` |
| `tests/test_path1.py` | `86732c5f44a06a62ff11e927ede3ef9104bc03fef963f0544f9a64361a0ab07d` |
| `tests/test_wp9_02_path1_controls.py` | `5ca517bf7e84b5f871b6ef870736bfffadb9b36042534f9ef4f0622b14746757` |
| `docs/results/WP9-02_path1_controls.json` | `08dbc133cf2ca0ebd8caa3f68b5883736765b4e0fd6276b1ada8d9ea3a6c47cd` |
| `docs/DECISIONS.md` | `e96af11e887fc6ba567de72d30e931a95fa1d8b69ec706d85afe7866c59c0bca` |
| `docs/FL.md` | `eb96178acf306e361bfa4f6c3ec5066bc80957e70f2a74a0ed408c34f2fc46bb` |
| `docs/STAGE9_PLAN.md` | `770810fd3358dcc9addaaabce4803b1f1fd2f605270c488cc4f31620ce71a228` |
| `docs/HANDOFF.md` | `34f30bffe9dad6fe80588efccaa3a642a613a530d156e3744baee4ece1e6f266` |
| `docs/audit/TP81_TP82_register.md` | `8b130bc74249d1b5a808c02a72ecb76a2689fea5e81e8bf5a083f746375ac67b` |

## WP9-02j — path 1 v3 (founder decision OD-S9-02): positive control FAILED 0.66 (FL-011 open) — 2026-11-17

- Branch `wp9-03b/path1-v3`; record on the branch (FD-01-D26). Tests: 685 passed (Claude's local run). Pre-registered before the run: FD-01-D37 (commit b26b5f0). v1 and v2 results reproduced unchanged.

| File | SHA-256 |
|---|---|
| `src/xauusd_swarm/path1.py` | `b6c6784f69eb62520f0e59764cd0330678f12784fa7614aebe7d02055a25bf1a` |
| `scripts/wp9_02_path1_controls.py` | `76869160751e50548941e3c1f2824e6656be2ab13d8bd1c971df4d67a6a2c424` |
| `tests/test_wp9_02_path1_controls.py` | `23738a695af56a01c44b0f34ea301d725492d1ad8c59e902ef1bcc121e5dd4fa` |
| `docs/results/WP9-02_path1_controls.json` | `3e852579c4a91a2482260046b7e2cbaa1f1ef6b2a842f0733259accb3a41cd2e` |
| `docs/DECISIONS.md` | `12ef71b6845526ae0fa81922861d5aedd68cfd3ab620924ce73997a96093cf45` |
| `docs/FL.md` | `ee66050f8f2e86a64e17d0ae659f86055c8c27e51ad286eb633cc6176513bc43` |
| `docs/STAGE9_PLAN.md` | `e380b1ee6832bea1ae6169a57eed37af6b4e2bfdf62a6228ca4d8b2bba604ebf` |
| `docs/HANDOFF.md` | `097f5bd443506b6082b904842d0247810e21dc7b0af5a55722e3784e0cb5016a` |

## WP9-CI — founder decisions OD-S9-03 (path 1 paused) and OD-S9-04 (heavy tests Linux-only) — 2026-11-17

- Branch `wp9-ci/heavy-ubuntu`; record on the branch (FD-01-D26). Tests: 685 passed (Claude's local run, Linux; on Windows the 3 heavy tests are skipped).

| File | SHA-256 |
|---|---|
| `tests/conftest.py` | `419d6395cd488c4995b8b6bc0096bbec8735fc35dd0a1e29e4dfc31e6c51dd1f` |
| `tests/test_wp9_02_path1_controls.py` | `b3052e017404e7fc7426a17a5dfb6f30219fbd43750d5ce548b21bf376e55937` |
| `tests/test_tp81_tp82.py` | `f7a5fced837100c949d60fa92b809738a1339da0293bb04cc80319e5c36a7b42` |
| `tests/test_wp9_02_null_controls.py` | `f42d0c995ea0084e9fc58d103f679dcd815841f619bb48f24226ee7a500392bb` |
| `docs/DECISIONS.md` | `5e432e3345f139a3472c382b80e03fb9f9643de26bf97b2a2333ec41c5b762a4` |
| `docs/HANDOFF.md` | `829ddc8c5899c3243be3930537faab906bf935c2323b22b2a7cdfe8c3aed7eb5` |
| `CLAUDE.md` | `37682b7d5522fa9c7f268454f1f5f1520fe696f7f7f26e749546c17b5c02cf12` |

## WP9-03 — graded planted-leak test TP-50 (ت1–ت9) and TP-50.0 (actual results) — 2026-11-17

- Branch `wp9-03/leak-tests`; record on the branch (FD-01-D26). Tests: 690 passed (Claude's local run). Design pre-registered before any run: FD-01-D38 (4232813) and addendum. FL-012 (fixed).
- Blind spots ت8 (≤ 0.03) and ت9 in `docs/KNOWN_BLIND_SPOTS.md`.

| File | SHA-256 |
|---|---|
| `src/xauusd_swarm/leakcheck.py` | `7ff78b1b8f75df93aa323242f4e71c788fe01a88b46d8b878979086559c4edb2` |
| `scripts/wp9_03_tp50.py` | `6a0307ea88381d610d296a3e5a683e9e3f23119d5bd80d951ccb86bb6ede3ae4` |
| `tests/test_leakcheck.py` | `63ed43d872f46956df88e0a23a164d7bd3c191ec13f54aeeb7022003dcf293fa` |
| `tests/test_wp9_03_tp50.py` | `df091c8efabc2d319b715aafad51422b677d0c3b75857fc005e2798bcf5bcb5e` |
| `docs/results/WP9-03_TP50.json` | `dc5294cbe344881ae5c4629b3844a2b1402ceed79da1f59037ba82a1fda04145` |
| `docs/KNOWN_BLIND_SPOTS.md` | `fb4cec5a280bc194f0394f713e382e73abe2d7520bea298adf6ca705cfb28afd` |
| `docs/DECISIONS.md` | `f6c2e0278b9eaec524e2fd0b57fe991b48673c15bb2397a1acc884548a856d25` |
| `docs/FL.md` | `92a956ca3f265eae5d9016f1b768f1b38deeff958da488d6ed88a15cb5e96792` |
| `docs/STAGE9_PLAN.md` | `cb81c30d8724fac88391245dd748efe2c4f7c3c9118a5afdda7e3d30b0032466` |
| `docs/HANDOFF.md` | `0811aa00ce4eb27a09e654ed3a7e600e3fa9befcaadcfc6d8fd946541c532a42` |

## WP9-03b — review R1 (path 1 + TP-50): card v2, validity limit recorded, wording fixed — 2026-11-17

- Branch `wp9-03b/review-r1`; record on the branch (FD-01-D26). Tests: 690 passed (Claude's local run; path-1 reproduction re-checked after the docstring edit). Path-1 and TP-50 runs repeated: identical values; only module hashes / key names changed.

| File | SHA-256 |
|---|---|
| `src/xauusd_swarm/path1.py` | `e5f35d99bfede87ca8730cec66607342ff0ad4eea9ae980b17efb0b551412348` |
| `src/xauusd_swarm/leakcheck.py` | `a4e5ddde4ae9caf5cb7eac498d37078b0b5b60332f1096ee384b015d5b922dad` |
| `scripts/wp9_02_path1_controls.py` | `3b5b59649407da3219ff423938454bebe8111e6ce5ac7c3893d2d524d1fa9ad1` |
| `scripts/wp9_03_tp50.py` | `eb6c2236ba8c934b190d12e8ecff56fdf47678931e8092e94f2ff674af479eee` |
| `docs/paths/PATH1_CARD.md` | `5c8c3ac055b2172b581314dceb9000224788d8d7191a496cf1110a7b3f97095e` |
| `docs/paths/PATH1_CARD_runs_v1-v3.md` | `811377327cb374d027ca686676d63bb8bb6a10e19a6e18a60310ce011eced4cd` |
| `docs/results/WP9-02_path1_controls.json` | `51df3ecb67788844d098bc519729774fb3f53610c4f7a1f40fc49beaaf74c855` |
| `docs/results/WP9-03_TP50.json` | `205b7da2c01331d173ba906ea5e4f1868d5886261d68d33aa1224e94f5711581` |
| `docs/KNOWN_BLIND_SPOTS.md` | `35638537ab171148e31f8ad329ac3db429cc00982648d9467dd069fd697dee6a` |
| `docs/FL.md` | `96980a99f5635089c3e8d6b738e4f4e304af3d999c693d5bbd8513c5cb10e792` |
| `docs/STAGE9_PLAN.md` | `7774c4991c2ba9d5162fcc02687af3881eca12b2fc1400aefe4cbe50e685ed9a` |
| `docs/HANDOFF.md` | `04663b0545231c4a184f70b6e020321971cacf38f0cf5d42f043728afccdaf1b` |
| `docs/audit/P1_TP50_register.md` | `ad1b70e113716869abf31471e024afe674cc47295f5286e2fb1364a367700dd0` |

## WP9-04 — stations and paths: traceability (TP-04, TP-60, TP-61); ت-09 / م-10 passage — 2026-11-17

- Branch `wp9-04/stations`; record on the branch (FD-01-D26). Tests: 696 passed (Claude's local run). Mutation check: removing the م-10 or the blinding rule makes tests fail. Also carries the P1/TP-50 review R2 fix (STAGE9_PLAN).

| File | SHA-256 |
|---|---|
| `src/xauusd_swarm/knowledge_passage.py` | `d9ea750f26f5c58f37dc679210d0af5f086f5359743a66b2b2d70c4539318aee` |
| `tests/test_knowledge_passage.py` | `44d16d4e49768f008a37dc6848c9fd91c3a46ef5f0f680fcb6249be23c5f22f9` |
| `tests/test_wp9_04_traceability.py` | `4d0c76ed652c8192186a59dda3a81bf771bbfbde88db636e02d73668ef9ca927` |
| `docs/WP9-04_TRACEABILITY.md` | `639864fa36ebb26df5c1059970541bdeaa144915f0327088271b0a8df07c48b7` |
| `docs/STAGE9_PLAN.md` | `334de79e4112684ace6c1891a6ac08c90d73f995666953e638286cf2f733eeca` |
| `docs/DECISIONS.md` | `353631a1ad2acd1c66ace92e7195ae4a6fb4bc947b591fa2961d55d1995fa010` |
| `docs/HANDOFF.md` | `64a3f4c5be682c12ee6206a7d898532f43d924f3370fa4d9be072569b4082d18` |
| `docs/audit/P1_TP50_register.md` | `1009ef5c1194b01420d52b1ad0bf75aae8b90f05b33b4846cb867eba9c322e3c` |

## WP9-05a — cross-layer malformed-input test; statement guard; dry-run apply (FL-013, FL-014) — 2026-11-17

- Branch `wp9-05a/malformed-inputs`; record on the branch (FD-01-D26). Tests: 698 passed (Claude's local run). Sweep: 81 kinds, 5 525 probes, 0 crashes after the fixes. C0/court results regenerated (court code manifest includes charter.py/custody.py; verdicts identical).
- Also carries no review closure (WP9-04 review pending, to be sent with this).

| File | SHA-256 |
|---|---|
| `src/xauusd_swarm/statement_guard.py` | `1cf770d00b347bfdf6b748626dc4b153dae9db7148fd967719d6eef9145c4208` |
| `src/xauusd_swarm/charter.py` | `e7bb82fb719bcf665603c2a9a7b0a452f5cc63b9b01e667baad70b179fa07dbf` |
| `src/xauusd_swarm/inventory.py` | `8e3a76e582ad5d83a7357fa032804009165d40fcfb4a565c3d6ada95f4dd7744` |
| `src/xauusd_swarm/claims.py` | `584462acf3f06c5bb96ea0b936c3d203aa3825b246883dfa212cdaa8ee8d683d` |
| `src/xauusd_swarm/evidence.py` | `7ff1deda96e38a6b291fb2a7aea58686cee0e065961b9d4cb4d5f5bc281dbdc5` |
| `src/xauusd_swarm/falsification.py` | `d43d2c54e506b07dc5c284adfae1c7b0ff550df77ddd61836f6534a20c8de58f` |
| `src/xauusd_swarm/custody.py` | `d9155a4a595a49bfb7032914a19b6f49e79f966ada777177b2aff95cd1a68b54` |
| `tests/test_malformed_inputs.py` | `04d4a97c2d679cdba8a0903b3b539486225b4ae467ebdf9b984e39e6009dd62b` |
| `tests/fuzz_plugin.py` | `7d0e8b410e05c07ab9643a5ca53e58b9cb306c64c2fabf7a62f202abbf7a31fb` |
| `docs/results/WP9-05a_malformed_sweep.json` | `8ddb77d768cfb3912f0690980752cba959d70ccc8b93640b2ab42a5c8454b8db` |
| `docs/results/WP9-02_gate_court_controls.json` | `abd329a511f5be9a8ab1c80214b509d2aa041269637103cbf727110f06accb8f` |
| `docs/FL.md` | `3dbc19085c6e369ec8c2405e09bafe8f99174c7a923954bc42d8cda9d11f4054` |
| `docs/DECISIONS.md` | `6f23fb5a671fee7e7d372a5f8f0284f80d5facaa01e9c2cd5b4202c2fc5725ed` |
| `docs/STAGE9_PLAN.md` | `edadfbb8e9c78fc37d6464a0ce62c6a9d24372b0587c2c2e36b680d0562805e2` |
| `docs/HANDOFF.md` | `507993fd9ce08f64c2d71310f4971e2922d6d5689356fa0b7088dff5eeefa60e` |

## WP9-05b — review R1 (WP9-04/05a): seen bypass, use-point skips, sweep before commit (FL-015) — 2026-11-17

- Branch `wp9-05b/review-r1`; record on the branch (FD-01-D26). Tests: 715 passed (Claude's local run). Final sweep: 81 kinds, 5 389 probes, 0 crashes, 65 accepted values listed. C0/court results regenerated (court code manifest includes identity.py; verdicts identical).

| File | SHA-256 |
|---|---|
| `src/xauusd_swarm/statement_guard.py` | `ffbee6d1c885aab13c6f35e497ef9878dcf767213dbbf91c6a5c1b920bf6312a` |
| `src/xauusd_swarm/identity.py` | `b55ae51886b21851bb16bae533e5a626a4eac009cbff6365ba6fac19e646f84a` |
| `src/xauusd_swarm/knowledge_passage.py` | `38e71902806b160abbaff5801cba59f5c32566378c94f4cf62f66a6ce46edd12` |
| `src/xauusd_swarm/controls.py` | `a7203689f95ab15202c9bfc329702e8ae7d86497ee8031b57aca31d4bed69251` |
| `tests/test_malformed_inputs.py` | `105aa660ee191b6f0d51fbc63b6c3d73577182baea8704dc8018f693045048c6` |
| `tests/fuzz_plugin.py` | `2401576fcdbccde93c2180462d486d5ad50be97434890287773595cf59b864ae` |
| `tests/test_knowledge_passage.py` | `06aaac0d9ccf745a3b910fd2c7833f39baf7c474ca2f7329d102f40f7296a6ca` |
| `tests/test_falsification.py` | `5730add088d835f5ad3a635e1f2b6c83245e9f1a909dc8cd4e9ce74786d746fe` |
| `docs/results/WP9-05a_malformed_sweep.json` | `53adfdfaad1f86576896b9c038b81040b23f6c81d4b154bd564fa8b08a723b6b` |
| `docs/results/WP9-02_gate_court_controls.json` | `49dd265d2f4b3c3ca82ddc33525f469b5b13be8e230aec4e2829ec9262ca9a67` |
| `docs/WP9-04_TRACEABILITY.md` | `fbcb06667a980ca1c2ce920753fa6eb6805bbeecb9ccaefcd614be2eacc2718f` |
| `docs/audit/WP9-04_05a_register.md` | `aa94a7fb2697cf1cb25a7af8674301a9c1a234a7d7649cfdd61bc2dabe9f1e2d` |
| `docs/FL.md` | `27524e2f76050ec9fafda04ce7d88d8d0bff6e407b21ea57cb52bc8764284b6d` |
| `docs/STAGE9_PLAN.md` | `98f75deff47b03b6de9904a3865221630a86d1ee466346793f4f5c6252abc2a2` |
| `docs/HANDOFF.md` | `88b9b4b6bf90ad5ddf38f1620c7df55a12807f7d3d8e59a1602f780a47c50e19` |

## WP9-02k — path 1 v4 (founder OD-S9-05): all five TP-21/tool controls PASSED; FL-011 closed — 2026-11-17

- Branch `wp9-03c/path1-v4`; record on the branch (FD-01-D26). Tests: 718 passed (Claude's local run). Pre-registered before any v4 run: FD-01-D41 (commit 3bf3c8a). v1–v3 results regenerated (path1.py module hash only). Also carries the WP9-04/05a review closure (R2-01 time format deferred).

| File | SHA-256 |
|---|---|
| `src/xauusd_swarm/path1.py` | `9beabb5b45c5c02593aa3c42f501c1cffe41716ec77576aaf76a270f9b5f2e43` |
| `scripts/wp9_02_path1_v4.py` | `a395369d03fd57dbe850e81b6691573a6312ef6acfc702589daf499996307e49` |
| `tests/test_wp9_02_path1_v4.py` | `da2f9c82a789bbb4486f6153a0c19f171a7ab79e417ccd2ae70bc85236eedc1d` |
| `docs/results/WP9-02_path1_v4.json` | `c138242d3a9cb92e990a3be460c8e743a487927d99ac560bd6bdd9a309179ac2` |
| `docs/results/WP9-02_path1_controls.json` | `dbfaea916fba121b902ebf5c4ef4d6742e06b7cbc4c64b7d63a80e6333f91326` |
| `docs/paths/PATH1_CARD.md` | `9707487294112343e037324ad6975c7fc25bcecc0799c01c061fd3b36ea844a9` |
| `docs/DECISIONS.md` | `5f9c4a50204f205c0e638c5108969887399502eb83c702007a81bb1879e7b2bd` |
| `docs/FL.md` | `9469cce428fde291bf3dec87cff87b79f1b5f8d0919117f36b1688e7c65a39d0` |
| `docs/STAGE9_PLAN.md` | `89c3f4b02a82aa55f40797d882f0c558bbae4dbef99e9d1e32a0d6d000ffbb16` |
| `docs/HANDOFF.md` | `26f94de381340a9af82abf0742f6cfb021f90fabb3e775c28bfefa72de650dc3` |
| `docs/audit/WP9-04_05a_register.md` | `d7b4f0545dda99bd208f3ac0acc6f431f321ed6ee9d835f96e6ba4c24eade02a` |

## WP9-02l — path 1 v4.1 (review R1-01 of v4): exact constrained reference; all five controls PASSED; FL-011 closed — 2026-11-17

- Branch `wp9-03d/path1-v41`; record on the branch (FD-01-D26). Tests: 721 passed (Claude's local run). Pre-registered before the run: FD-01-D42 (commit a9d25cd). v4 and v1–v3 results regenerated on the current code: identical observations (impl / module hashes only). v4 superseded and no longer re-run in CI.

| File | SHA-256 |
|---|---|
| `src/xauusd_swarm/path1.py` | `7ec348a213553b033fc54feb610e57cc2e23e8ceeab73c5f84d2949f830752ab` |
| `scripts/wp9_02_path1_v4.py` | `d9a785211385915bbfe57a602444a637b5a7ea589606660c36182afcd2d57e41` |
| `tests/test_wp9_02_path1_v4.py` | `8903b320482eb2d341a2770574da1777a16b2657309a28f016f85199bfe3bb7b` |
| `docs/results/WP9-02_path1_v41.json` | `9f080010bf5fd6bedb7b3af46937a6e8239c8a2b42e12674b6cc3b7160f598e5` |
| `docs/results/WP9-02_path1_v4.json` | `f4201b7841cd926ad8d66ceb97662ebe29d978d94ea069a26a243dfdddc7e0bb` |
| `docs/results/WP9-02_path1_controls.json` | `ccf3cc629d30e4d44015a512892d51c18e44db7257ae0e0f0f92c2e108afaa2d` |
| `docs/paths/PATH1_CARD.md` | `eff25d96f98e03b7362e2ff483f99b40756f68f98e2e8c38b5e0bf7914a1e2e3` |
| `docs/DECISIONS.md` | `a6429920327f3aa9f6fb309d8c3ca9a88caa182634c67ba7901b469a4d9d4794` |
| `docs/FL.md` | `d1ef9485b56fcfd86fcd58764d7b1111b23a74fb3fa8b5f4b815fb67adc0d447` |
| `docs/STAGE9_PLAN.md` | `9ab2841728638ce42f9ff43fb3dd285500683235661b2b5434c5f0fad5d56555` |
| `docs/HANDOFF.md` | `ae9fe19c448f3d89a1953d4abba5ed118e39db7928f7c085e44e6883367de014` |
| `docs/audit/P1_v4_register.md` | `b45e02396d9bb59556564063eb1439dff265fc3f1c72e335b6db705fd6b48ced` |

## WP9-05 (draft) — engineering test report; TP-11/TP-13 tests; reading of TP-09 (FD-01-D43) — 2026-11-17

- Branch `wp9-05/report`; record on the branch (FD-01-D26). Tests: 738 passed (Claude's local run). Report verdict: B9 not closable yet (TP-30 measurement not run; TP-09 reading for review). Also carries the path-1 v4.1 review closure (R2 MINORs fixed; v4.1 results regenerated: identical observations).

| File | SHA-256 |
|---|---|
| `docs/WP9-05_ENGINEERING_TEST_REPORT.md` | `f85ea74d2a598763de9d22feee09c274282292c1f215ede2c62ea03e82336c5b` |
| `tests/test_wp9_05_report.py` | `264be4f90752f6a96f16ec202b9207bc9a0abc5de7e7fbddaa45b2ea71c03128` |
| `tests/test_tp11_tp13_lineage.py` | `0b013a6c6231a0f66796b0ae14f47c87dd57b2137611a9b5cb0e0d064fe7bbe8` |
| `scripts/wp9_02_path1_v4.py` | `92bfc88dc57b3f2d53c7c9c2a3d4fc5279a7ff777c646c7544860acf6ef43b5a` |
| `docs/results/WP9-02_path1_v41.json` | `feffbd21d9ba7799f13b630fd87b430b838c31e4fa97520fd2abc14787a158a6` |
| `docs/DECISIONS.md` | `9cb3661c091d9e98b6e5ffdad99ff55492b2da8c25540560bdace06c47b45475` |
| `docs/STAGE9_PLAN.md` | `dc50d585ee5677c985d9c210ab72dfb62a51e9fd582d6eefd57cf04ca9830077` |
| `docs/HANDOFF.md` | `95680b8e694c7a0b010375ee5e75e243c5c548ee12841677620b34eee5d44249` |
| `docs/audit/P1_v4_register.md` | `aec48b9c2e3f3b719cfe8ee2b11258dda10715d598e169bbee8040a23bb89507` |

## WP9-05c — `uses_events` gate for TP-09 (FD-01-D43 enforced in code; WP9-05 review R1-02) — 2026-11-17

- Branch `wp9-05c/uses-events-gate`; record on the branch (FD-01-D26). Tests: 741 passed (Claude's local run, full suite incl. heavy).
- Every claim card carries a mandatory boolean `uses_events`; `true` refused while TP-09 is not built; frozen with the claim identity.
  Card fixtures in 11 test files gained `uses_events: False`. Court control results regenerated (TP-46 output hash changed with the card).

| File | SHA-256 |
|---|---|
| `src/xauusd_swarm/claims.py` | `425a2926f0e47ae5d999027e2994872647812cd7fb9a5808c27baab6e7f5c5dd` |
| `src/xauusd_swarm/gate_court_controls.py` | `356c6ab81e9b74f3440c76abe40582ed4f10969b5a353436ed4d91b7f3d77d31` |
| `tests/test_claims.py` | `9f32e0d9f8b5b055d22ac9dfa53570d68bb07b6ea08715bcd76d0740ebdd6189` |
| `docs/results/WP9-02_gate_court_controls.json` | `b48fe71921c5fffeade8d03dfff14b6ef48e51ae35fbc0eede5f7236651f1838` |
| `docs/WP9-05_ENGINEERING_TEST_REPORT.md` | `9575dab8abb9bccda83e081e441224565d67375b2bba8107f4701b57d11e8bfd` |
| `docs/DECISIONS.md` | `39649d37e51ef2fe9887bb3cc73774592373e1ff094067c766fb00a27cdf87f0` |
| `docs/HANDOFF.md` | `909b838afa76c285e20102a62e35bd5d577d8e1ee127a5523e8f1f3ed5c6b16c` |
| `docs/audit/WP9-05_register.md` | `763528fdadd6f859c62c3d3732e3c4bfffc42e3bb447475c0f0f7faa7d695ab4` |

## WP9-05d — TP-30 re-identification accuracy per representation, measured and declared (FD-01-D44) — 2026-11-17

- Branch `wp9-05d/tp30-reid`; record on the branch (FD-01-D26). Pre-registration commit 129d9f1 (design and code before the run);
  one run. Tests: 747 passed (Claude's local run, full suite incl. heavy). No threshold (CS-01-04 open).

| File | SHA-256 |
|---|---|
| `src/xauusd_swarm/reid.py` | `4b553a3cba79f3b03a387110ede2ba02d0102c4c242df967a1ee3a7e189ca4fb` |
| `scripts/wp9_05_tp30.py` | `6afb8b0d60e5705bcf8d48491aa8abeb834eed501832858f5b8bc6be54658366` |
| `tests/test_wp9_05_tp30.py` | `46daf81901f2b06e427bc3aabe549749751a307bf370f36d547c34d83ad92fe4` |
| `docs/results/WP9-05_TP30.json` | `7ed121879b23308289df3077fbcb8e61c4ce57fb537624268c705d159ad9389e` |
| `docs/WP9-05_ENGINEERING_TEST_REPORT.md` | `a5fe5ed1fb1c561687e82182f96edc35095d5b61e32bd80d9f5ace90ef888e58` |
| `docs/DECISIONS.md` | `85706a1b26dff46e70bbeb1d5d182f1e2a7211943f6cbcdefc1c2fc5ec472c80` |
| `docs/STAGE9_PLAN.md` | `34009fba4aecfb01a5ee7a10acb398b54876ecb31e4e1723c69888f93e5d6abc` |
| `docs/HANDOFF.md` | `b80115548e9b4e9071698ceb9ace1b1a22ae7f4cdd5e41d2a17b8049582e2573` |
| `docs/audit/WP9-05_register.md` | `09c02052f92dd389e99a659a3093248237d793c35563037b95742340b9574343` |

## WP9-05e — TP-30 scope limits stated (review R2-01..04) — 2026-11-18

- Branch `wp9-05e/tp30-scope`; documentation only, no code or result changed. Local: 741 passed (not heavy);
  heavy tests run in CI on Ubuntu.

| File | SHA-256 |
|---|---|
| `docs/WP9-05_ENGINEERING_TEST_REPORT.md` | `ca8fdedb1a71d0f86cba0f4d2400dd8f525dad618a8054357c3676402c838435` |
| `docs/DECISIONS.md` | `43b4e9bac816d30e17cf2e738e0b31f9554054bd71d99cdb0e3a84194d1f1047` |
| `docs/HANDOFF.md` | `d42b39d822b57ddf6b46415beba231d6cedb8cd3109232b29467adfd799c514b` |
| `docs/audit/WP9-05_register.md` | `67591b52b28498097f0afcac192e40433dc79903e5141960b253d5b5c92a0ca0` |

## WP9-05f — Gate B9 closed (founder decision OD-S9-06) — 2026-11-18

- Branch `wp9-05f/b9-closed`; documentation only. Local: 741 passed (not heavy); heavy tests run in CI on Ubuntu.

| File | SHA-256 |
|---|---|
| `docs/WP9-05_ENGINEERING_TEST_REPORT.md` | `4d317c05ebcd3a9229f36823c2f5a2d9104d956fc3c6ae9d4822c6efab989f35` |
| `docs/DECISIONS.md` | `61f6a42693f293c26a8190af2ec622393c0e233d941524754b4cf8627d93a1dc` |
| `docs/STAGE9_PLAN.md` | `4a7cec1e5ceeaca015488175391170dbc03e61ac8104d9299657442f84de6d4e` |
| `docs/HANDOFF.md` | `9726d9eb7fe24a96144947004ffac6a730a257dc92e59b15237e9bc626a3d588` |

## RIP-0 — re-ID research programme plan and RIP-1 design draft (OD-S9-07) — 2026-11-18

- Branch `rip0/programme-draft`; documentation only, draft for review, nothing run. Local: non-heavy suite run; heavy in CI.

| File | SHA-256 |
|---|---|
| `docs/research/REID_PROGRAMME.md` | `6af6a79f273430239ef0896724ea84e9cb9cbff421d17d8fec769db9b5e03034` |
| `docs/DECISIONS.md` | `65307f62c3fe3dce4e1f486bb32547abf173dc561e1f60591dc045a73da9928a` |
| `docs/HANDOFF.md` | `3600d60b23cc732a94548d3b2926f9abf16b1490ce6ef13d95ef931e9ed7cf80` |

## RIP-0 v0.2 — RIP-1 design revised after review R1 — 2026-11-18

- Branch `rip0/programme-draft`; documentation only, draft, nothing run.

| File | SHA-256 |
|---|---|
| `docs/research/REID_PROGRAMME.md` | `4b9f5c8696f36284017d8c481810b8f8d904cf0763ac3e5bb92f12897be37464` |
| `docs/audit/RIP_register.md` | `15be0f41ba12ff3aece73800df3a5e98a893e7a7b4993c2f9978ac9338f142c3` |
| `docs/HANDOFF.md` | `e7a5fa04afebde900905573f412f70ba9c1eca3dee16e3386d03c89fcb4f9161` |

## RIP-0 v0.3 — RIP-1 code for review (not frozen, not run) — 2026-11-18

- Branch `rip0/programme-draft`. Local: 755 passed (not heavy) + tests/test_rip1.py incl. the sandbox probe test as root.
  Smoke runs on throwaway families only (n = 128); the RIP-1 test set does not exist yet. numpy==2.5.3 pinned.

| File | SHA-256 |
|---|---|
| `docs/research/REID_PROGRAMME.md` | `0783f109f6334d1f2f287b01d89c23fa47b48a3706829d2b08e4ffd2c84b6b4a` |
| `docs/audit/RIP_register.md` | `ba491947b6d5beaecc2ccdf965fa95c81c3f8275ed319466d2094079b085a27b` |
| `src/xauusd_swarm/rip1.py` | `e3b1b2b7b86b26d96a85e9ba087fedb386dbd4d2a14e1b7922826e2a1766b6e1` |
| `src/xauusd_swarm/rip1_attack.py` | `3e8684ce5e610578a882aca3922bb156b3060c9465ab5ae6754a0d81f72414e1` |
| `scripts/rip1_attacker.py` | `4ca9cafef8dd25c94b72be6e96bf5fd848bd07659d3e5980e99ebd02acfcbf73` |
| `tests/test_rip1.py` | `a19e93fba553a8a3da4655eeb658b6388a33b4a14138756df936fda8c3dd26b5` |
| `tests/test_numeric.py` | `3a6e4d7bbfb0565bca75537e82c864426175b9d52a462ef77a619dc1cbee11a9` |
| `env/test.lock.txt` | `225576985b2328cc5752a73d72d69b0a5d838330a428e4d30c30933ee5cdbe01` |
| `env/dev.lock.txt` | `225576985b2328cc5752a73d72d69b0a5d838330a428e4d30c30933ee5cdbe01` |
| `docs/HANDOFF.md` | `e5f8917781002e542edb2bce3cd2e52f12f4eeaeafcf138f8165a23952723b75` |

## RIP-0 v0.4 — RIP-1 code after review R3 (not frozen, not run) — 2026-11-18

- Branch `rip0/programme-draft`. Local: 762 passed, 1 skipped (full suite incl. heavy; the sandbox probe test ran as root).
  Smoke run on throwaway families (n = 128): all 10 sandbox runs passed the probes; smoke reproduction passed.

| File | SHA-256 |
|---|---|
| `docs/research/REID_PROGRAMME.md` | `5d4eaeebd77dcc9422cb15a801511300b42fcd92a74fa14f1e33f01f20525f31` |
| `docs/audit/RIP_register.md` | `285224a743a0223375b4965518c016da01b78932a99cefcc7379abfa84d424a3` |
| `src/xauusd_swarm/rip1.py` | `4c6a3e4c6e1d6969e63214e6d2396ca48ce896d7dd53cf1522b81b8aa44ddb2d` |
| `src/xauusd_swarm/rip1_attack.py` | `1bc2270e809d3b1ee1f9ffa002ca64e70725438fd44a34d842ffb352702fb9a1` |
| `scripts/rip1_attacker.py` | `5ff355171a9a53682ebb3ed26df206548ddc3ef3218255bb4f3ae6987686ba69` |
| `tests/test_rip1.py` | `401e26a3a61a5547c319d46e8e2c6187c30d26c1a9ab8ee8369dca6cec6d6509` |
| `docs/FL.md` | `6eb26107be1fa3699442d2cc9620fb821b6c3f533959747488c7d65a1304bf12` |
| `docs/HANDOFF.md` | `d5890074c5d898a1a5d8cd33deb9dc89bd4ab6112c7ae4cb33d49d699158e1ff` |

## RIP-0 v0.5 — RIP-1 execution hardening after review R4 (not frozen, not run) — 2026-11-18

- Branch `rip0/programme-draft`. Local: 766 passed, 3 skipped (full suite incl. heavy, as root; the 3 skips are the
  RIP-1 reproduction tests, which need a committed result). Against a throwaway smoke result: all 22 RIP-1 tests passed,
  incl. adversarial break-out attempts and the sandboxed protocol reproduction (10/10 identical; altered result refused).

| File | SHA-256 |
|---|---|
| `docs/research/REID_PROGRAMME.md` | `e45807aaa5be0952042bcb74e79f4d6eec5eef885cfa8da1d6a959f0710c5b47` |
| `docs/audit/RIP_register.md` | `b4cd450c005678e2d59a5a624647dc0e6759969afb26f7c980e3846a43587ca7` |
| `docs/audit/RIP1_R4_closure.md` | `b93679583dad47cbb19507c9b41af4680a2ff80866493860ca154650de285ce3` |
| `src/xauusd_swarm/rip1.py` | `cb0af666609359dc7a6ab2565f6e6f4121e5c3b09f73589407662a7acfc7570a` |
| `src/xauusd_swarm/rip1_attack.py` | `1bc2270e809d3b1ee1f9ffa002ca64e70725438fd44a34d842ffb352702fb9a1` |
| `scripts/rip1_attacker.py` | `5ff355171a9a53682ebb3ed26df206548ddc3ef3218255bb4f3ae6987686ba69` |
| `tests/test_rip1.py` | `1fe888fc1ccf9ea54ef0937cb9c74edf1a7410c02b857a2a5940eff3f00c3b2f` |
| `tests/helpers/rip1_evil_attacker.py` | `5f273d83bed09262bbd7b29125a3b56bfa46cbcbb4a7973512b116506716f688` |
| `docs/FL.md` | `de4798df0e96bb4205848459476e4218a2681596e8448fa934b72a2def90a3fb` |
| `docs/HANDOFF.md` | `2367f60fb3b30e51e9467ffde07841dc4d3091a5ff97c4828729000515df6c2e` |

## RIP-0 v0.6 — RIP-1 complete attacker set (review R5; not frozen, not run) — 2026-11-18

- Branch `rip0/expected-attackers` (from `rip0/programme-draft` @ 643e5b0). Local: 779 passed, 3 skipped (full suite incl. heavy,
  as root). Against a throwaway smoke result: 35/35 RIP-1 tests passed.

| File | SHA-256 |
|---|---|
| `docs/research/REID_PROGRAMME.md` | `c15a97802ee0672f0720a80814f2b55f2b79aa67fb87f0c44f321fbf45eac805` |
| `docs/audit/RIP_register.md` | `96d140856bea841e67442048b193aa507bd71d654efac5a75033b8626cb6c7a5` |
| `docs/audit/RIP1_R5_closure.md` | `9be9a730302f2c8439bb31a0d038a2dc0bc3da1b6e7b7e045761ee49ec0382cc` |
| `src/xauusd_swarm/rip1.py` | `7d04b40113d64a1e6a4c33fcf7f5e54d2955d7e9af41b002136dafa20ae9014a` |
| `src/xauusd_swarm/rip1_attack.py` | `6d28758ed17ee2bc525251b280a24d2c8ea581d426d0c793d3638a0ca38d555e` |
| `tests/test_rip1.py` | `05183dc020c18982f27e00477347a30abf48abe097bf1f8aa9605f0660485844` |
| `docs/HANDOFF.md` | `e1f2de64bbbc9de1b6417d5e74bbb72d907017ce34fca0d5f6960a0bbc057f5e` |

## RIP-1 freeze — FD-01-D45 (design v0.6 + code at 206a0cd) — 2026-11-18

- Branch `rip0/expected-attackers`. Decision record only; code and design files unchanged from 206a0cd (hashes in D45).
  Local: 771 passed (not heavy); heavy in CI.

| File | SHA-256 |
|---|---|
| `docs/DECISIONS.md` | `3cac0ee2b521e05362f1ffc3b34a0c716d7109f562f3e10d6065f68425157bba` |
| `docs/HANDOFF.md` | `bbfbad32f535c0b9d123b120908b31cc62d703e92bad13b94194504d5f778e58` |
| `docs/audit/RIP_register.md` | `bd665e8b038da7b14fe1269069e692b2caa09bd9367e8718f85cfafed122318b` |

## RIP-1 — the single run (FD-01-D45) and its report — 2026-11-18

- Branch `rip1/run` (from the freeze commit 351c362). One run of `rip1.run` with the registered spec (6697 s), all 10 sandbox runs
  passed the probes, ledger scan passed. tests/test_rip1.py on the committed result: 35 passed, incl. the sandboxed protocol
  reproduction (10/10 identical), the altered-result refusal and the CI recomputation. Full suite (local, as root, incl. heavy): 782 passed.

| File | SHA-256 |
|---|---|
| `docs/results/RIP-1_REPORT.md` | `3882f7241ee5d9a9c83aef0418d48f26be77b905139f7056c476296032011737` |
| `docs/HANDOFF.md` | `8fbdb06910ad28f9ccf6c68806cac5ee46615b816cabc2f4149c0a58cc753729` |
| `docs/results/rip1/data_affine_level.npz` | `94f1dc7bd91c89f69457061133e50f3f88a37633b94a27fd9f0148edc5bc205a` |
| `docs/results/rip1/data_level_residual.npz` | `5acb0269bf2edd795871ae4b82f2329ff90fec30bc29db8823830c6d621b2131` |
| `docs/results/rip1/data_log_returns.npz` | `7ad29bed74b9f36a19db88d82fd8f58526ffba5a2787aba6e404d9d0144e139b` |
| `docs/results/rip1/data_tick_grid.npz` | `59d59937d6a797c5db54f8e05e89ede844c29b437b9846ddbc0878f14e2d4c44` |
| `docs/results/rip1/data_volatility_time.npz` | `3a1719063ce90bfa7c98523cb0e80dd4c20dcedd58b98cd0207a5de34ebc0f63` |
| `docs/results/rip1/dev_labels.json` | `72b4a2274ecfe84026514067b388f8e712056bc9e3179065da557bcbffaa2149` |
| `docs/results/rip1/ledger.jsonl.gz` | `c108645320343beb2a46ea15c9bb1afa7da45c559331e385c78e0a82c0fd2668` |
| `docs/results/rip1/ledger_final.jsonl.gz` | `155df3cb803a4f6cab1ce67b3ec6c5712aa4c85af0a7ef7c59323dfd20aba614` |
| `docs/results/rip1/predictions_V0_affine_level.json` | `7b4dc0ee04ed93b9c60e42258da98da22c7eb225e7370747dba965d0c6f507c6` |
| `docs/results/rip1/predictions_V0_level_residual.json` | `a7b2c65df6a4d15860332b72d2e4d25921c9c954b7e25cbab61295df0e2fcae9` |
| `docs/results/rip1/predictions_V0_log_returns.json` | `2b0973814fd411ebdb29e3ca1220ad14cb41c88c28ed5b06e4d46c3b95edf6a8` |
| `docs/results/rip1/predictions_V0_tick_grid.json` | `c5b4604f4f019e9b75695472908c4621fffcdd8862582e97579c7562a108840e` |
| `docs/results/rip1/predictions_V0_volatility_time.json` | `4117bb1e5ac90b8dce868ece2651d05a2016747933c724b75aff3e2a93a43e6e` |
| `docs/results/rip1/predictions_V1_affine_level.json` | `ee934df310c3dedc18e5078e43b8bd439ce3e23e751ad9237e9951b55bff992a` |
| `docs/results/rip1/predictions_V1_level_residual.json` | `e5f540dcddf02ca01890750b8a5359326615e9bbc63737af32a182734d4733d2` |
| `docs/results/rip1/predictions_V1_log_returns.json` | `e3906b6110605795668f1be51b296fe93adae0933adac4c15877483463cdea25` |
| `docs/results/rip1/predictions_V1_tick_grid.json` | `806a3ee3b4aa0aa013aba3b90605a10c85a6d521752aaec6c9f9091fdc0eff6f` |
| `docs/results/rip1/predictions_V1_volatility_time.json` | `a7966afd36955100bf32f76df8caab719aa3ad7cf3f3cea65906de45ef2c8ccd` |
| `docs/results/rip1/results.json` | `6477591423aa3f66e419e9cbf4e4373a7190f08f1e93ae5e813a51c152bcc38d` |
| `docs/results/rip1/revealed_truth.json` | `678f74826cf24090f88aee4dc2c56bd9082fd1ae07c3f6037fb1be4b4a8df116` |
| `docs/results/rip1/run_inputs.json` | `58fd73886d9aa607bd2460f72e4e1f10b6e527b49a90c7b3d2c910d5350d5ce4` |
| `docs/results/rip1/submission_records.json` | `1a2ff90ad87e081191401fe10a0e0bb2e77376cb8df6a9242d1ec87db53eac9a` |

## RIP-1 result audit R1 answered + RIP-2 design draft v0.1 — 2026-11-18

- Branch `rip1/audit-r1`. Frozen RIP-1 code unchanged. Report wording fixed (RR1-01, RR1-02); sandboxed reproduction
  attestation 10/10 identical (RR1-03); independent re-score 260/260 rows (RR1-04). Local: 784 passed (full suite incl. heavy, as root).

| File | SHA-256 |
|---|---|
| `docs/results/RIP-1_REPORT.md` | `b91daf19e0f9e9267341ec7c0f507c8ab81d1c2c363f33ff1c267fc515af4e12` |
| `docs/results/RIP-1_repro_attestation.json` | `ba6c89898a82fd64a473926874de452faec9e5d45bcec4b0f0f620b8eb981d8c` |
| `scripts/rip1_rescore.py` | `49fffe1163b1b27b3d3b80a8ace5701363ff22a222e6d933abc023360d3f99ff` |
| `scripts/rip1_repro_attest.py` | `3cd04b67cae62b97c4ba297b06104a324e9947141e9725be815749da688db727` |
| `tests/test_rip1.py` | `d09aa034e34175d201061360d4fce7d63267a2180074a21715f0ac3d9e499859` |
| `docs/research/RIP2_DESIGN.md` | `f9f01ea399b3ed85cde9c40e1f4083fe46a64b4dbcd6628405380d1b2652fb84` |
| `docs/audit/RIP_register.md` | `31bcc44ff4822baab67553873632df375e85f649c79568ada2f2c71d5a9a410a` |
| `docs/HANDOFF.md` | `8b6f6146d56eddbd1af0298cb92706132ed1ab32c61d8f0a3832d9a8f3e4fa61` |

## RIP-2 design v0.2 (review R1 answered; draft, nothing built or run) — 2026-11-18

- Branch `rip2/design-v02`; documentation only. Local: 773 passed (not heavy; no code changed); heavy in CI.

| File | SHA-256 |
|---|---|
| `docs/research/RIP2_DESIGN.md` | `80779b2c30e9b0d338f583e69d20c6dc2dc0fc40069e7f2485a0957d31317824` |
| `docs/audit/RIP_register.md` | `bdd8e7381a6c76894f595b29cd09d8acd0d399cc323c40177ca7ae0463745b01` |
| `docs/HANDOFF.md` | `e3f5755f3035990ab101b498045dfe4c39ee809ee0c6e519be442e2d4f0dfecf` |

## RIP-2 design v0.3 (review R2 answered; draft, nothing built or run) — 2026-11-18

- Branch `rip2/design-v03`; documentation only. Local: 773 passed (not heavy; no code changed); heavy in CI.

| File | SHA-256 |
|---|---|
| `docs/research/RIP2_DESIGN.md` | `e6e7d09bf04c59141a7541c99874d75325c84cf4c50d4d1738211e5f00affba1` |
| `docs/audit/RIP_register.md` | `35d00c6f1ed413e6b6144c43df57e81114bfb69c1e10c1244df7ab3fdd41a1c6` |
| `docs/HANDOFF.md` | `de71a63d455e0dcb096d7708fee01e708adf149d2032b5ee451c5ed82e687fae` |

## RIP-2 design v0.4 (review R3 answered; draft, nothing built or run) — 2026-11-18

- Branch `rip2/design-v04` (from rip2/design-v03); documentation only. Local: 773 passed (not heavy). CI blocked by GitHub billing (FL-022); not merged.

| File | SHA-256 |
|---|---|
| `docs/research/RIP2_DESIGN.md` | `a613b9948179074d507f154c3b670039d2ceb409bbfa00f7d987a8411c06c766` |
| `docs/audit/RIP_register.md` | `723b04c1f93c6c71775917dc3a1ec6c0ce2315838ca1bd506bcc41cf478d2855` |
| `docs/HANDOFF.md` | `478459a9bf74ec0342a6bbdde02e6f93dc035db7a4515bd7a493bc47d05c59d0` |

## RIP-2 design v0.5 (review R4 answered; draft, nothing built or run) — 2026-11-18

- Branch `rip2/design-v05` (from rip2/design-v04); documentation only. CI blocked by GitHub billing (FL-022); not merged.

| File | SHA-256 |
|---|---|
| `docs/research/RIP2_DESIGN.md` | `eb82ffb1ce8f2b049d28344c7a8a3127fa8b44ed1d624413d93efce205805346` |
| `docs/audit/RIP_register.md` | `627cecf669747caf3a996932d1776ec2c678cda863a311e1a5a62f9a11721310` |
| `docs/HANDOFF.md` | `7fc9cabfdf4d50685c3535c3b44ea17e11c1946c26fbd2146670ac9fd3edb79e` |

## RIP-2 design v0.6 (review R5 answered; draft, nothing built or run) — 2026-11-18

- Branch `rip2/design-v06` (from rip2/design-v05); documentation only. CI blocked by GitHub billing (FL-022); not merged.

| File | SHA-256 |
|---|---|
| `docs/research/RIP2_DESIGN.md` | `576190f1d70b1d5fd2db7cf077673570f27ab91435276d446236902e24b1f5da` |
| `docs/audit/RIP_register.md` | `bf0b5c45a0764f1a731cca791c91dcb53c776ebb96f0d61137abc43ba5ed2daa` |
| `docs/HANDOFF.md` | `72295295090df22cb55c588aa2b3b4e49cc1c7e55e9f00780c5e0bcf1aa2ca86` |

## RIP-2 design v0.7 — exact U-vol truth + pre-registered numerical verification (review R6) — 2026-11-18

- Branch `rip2/design-v07`. Pre-registration commit f2e7dc7 (script and criterion before the run); one run: 50/50 pass.
  RIP-2 itself not built or run. CI blocked by GitHub billing (FL-022); not merged.

| File | SHA-256 |
|---|---|
| `docs/research/RIP2_DESIGN.md` | `bee007da3bb4b2b87a236ac8ce31b125be81f604916b8e731c209dfe4dc24077` |
| `docs/research/RIP2_UVOL_DERIVATION.md` | `ae48ea1d9c99243b31bcba1b0a6d2fa19e9027e4e93f16b6919c4fdf96f30a1b` |
| `scripts/rip2_uvol_verify.py` | `836cd2b2e78d5d6f47964922d8f7c6008dccba333771a591efd7c7a694b13cc6` |
| `tests/test_rip2_uvol.py` | `96291f984e26d5c7a055efb8eb780b042acb6abb3a56a0ae8f21990313f72326` |
| `docs/results/RIP2_uvol_verification.json` | `10a48479d519a37ab934e8250d8606cd2e0b9143964543b350baf8ba1a282606` |
| `docs/audit/RIP_register.md` | `445c03e079706ed37b7f2840ff1b1e6ee2e98f9dac1813f24fd5fe71b14ca9dd` |
| `docs/HANDOFF.md` | `8faadb2bbaa065a0d1bddbee43223678d52e3ec3080e8fae2047e9e5438c92b1` |

## RIP-2 BUILD (FD-01-D46; code for review, NOT run) — 2026-11-18

- Branch `rip2/build` (from rip2/design-v07). Local: 828 passed (full suite incl. heavy, as root; incl. a RIP-2 smoke run on a
  tiny throwaway spec, ≈330 s). The registered RIP-2 experiment has NOT been run. CI blocked by GitHub billing (FL-022); not merged.
  FL-023 (defect found in frozen RIP-1 level_residual A6 sum) recorded; RIP-1 results unchanged.

| File | SHA-256 |
|---|---|
| `src/xauusd_swarm/rip2.py` | `36f1b0feae5c2c19877cbf4d6e25c110a8c832739ea6593172435fc628503ce6` |
| `tests/test_rip2.py` | `610908c2b68a9447bb5810220041117557b31213b9b39ba3b989fcc01911be8b` |
| `docs/research/RIP2_BUILD_NOTES.md` | `5894792a84d438429454aa439e339aed063e531d22399fa7d28af071e552d51a` |
| `docs/DECISIONS.md` | `b907254602d810e1fd0759530f545d783d258c980490d287295f64d32a8428fb` |
| `docs/FL.md` | `db85ef4649a1b5be11120b750fa3082b4b7ed68a13893195cb21c7d0cd19f6ed` |
| `docs/HANDOFF.md` | `ca2b19384341f89635bafe362ae2a8e47ec02b84f4c0333da174ded2c216d60c` |

## RIP-2 BUILD revision B-R1 (OD-S9-08; NOT run) — 2026-11-18

- Branch `rip2/build`. Founder decision OD-S9-08 recorded; design addendum A1; RIP-1-D1 diagnostic (separate id); FL-024 fixed; IC-08 docs;
  U-vol all-kinds test. Local: focused 45 passed; heavy RIP-2 smoke 1 passed (268 s); full suite 830 passed (as root, incl. heavy).
  CI blocked by GitHub billing (FL-022); not merged. The registered RIP-2 experiment has not been run.

| File | SHA-256 |
|---|---|
| `src/xauusd_swarm/rip2.py` | `b610172e5bc53b99bc1bad24a64d07d066237fa766cc58e1803c7fe0929fd441` |
| `tests/test_rip2.py` | `09938e129e5c0e34c4155826a3712ebf488e9f22c621c192df8449b68b35b448` |
| `scripts/rip1_diag_fl023.py` | `c63ae4f1038c89dcb373e720c1d3986ac509da960a3b288f75550e939aa375dc` |
| `docs/results/RIP-1-D1_fl023_diagnostic.json` | `2571fd5a2142fdc7d0b761d0ae7b7e6663db7bd14eb600841766552846370626` |
| `docs/research/RIP2_DESIGN_ADDENDUM_A1.md` | `9f2bd979de031e13626627e132a35f4b508f96a80267bd0b887bf21d61c375d7` |
| `docs/research/RIP2_BUILD_NOTES.md` | `1cd3f55357e19a1af052ea3575e6924542ff08ceab18b16b8938b3d1813c98df` |
| `docs/DECISIONS.md` | `8bbb015c5430a5651feda0af8be6e1ff5e7ab7cd056c98c589ede7212414dc15` |
| `docs/FL.md` | `819a4d68bdcc7e02c4d1b47943c2a5402cdf004124f3cc691259a11f5533bf2b` |
| `docs/audit/RIP_register.md` | `3825e074eb297d1c70bd570377485f8bc36191d800450eedfb208d53ae79af17` |
| `docs/HANDOFF.md` | `b6dc61f98afe1694dbbb5fd86795034bd078b1310e8f24153f88f4bb15803007` |

## RIP-2 BUILD revision B-R2 (strict support; complete bundle; NOT run) — 2026-11-18

- Branch `rip2/build`. Strict level_residual support (x ≥ m → 0); boundary test. RIP-1-D1 recomputed: byte-identical.
  Local: focused 46 passed; heavy RIP-2 smoke 1 passed (269 s); full 831 passed, 0 skipped (941 warnings under -W default, all
  outside RIP-2). CI blocked by GitHub billing (FL-022); not merged. Registered RIP-2 not run.

| File | SHA-256 |
|---|---|
| `src/xauusd_swarm/rip2.py` | `60900b57a03ff35924828cce8f6a331b168cdd6921f1949d4ddcb9ce9974eb2f` |
| `tests/test_rip2.py` | `805960d6b3f98916a6751c5a80421421d4488ffbd37b90aad74e561c2efbb560` |
| `docs/research/RIP2_BUILD_NOTES.md` | `e0bb905635c39f06af417075079f99317667a1ed921f3441afedfeb346a532c7` |
| `docs/research/RIP2_DESIGN_ADDENDUM_A1.md` | `b253af008cb88a97da35edb925b9a00ceb491d70b36801596dc5553acb19b6c4` |
| `docs/audit/RIP_register.md` | `e3dfafa6239f3ed5a32ef39cb649cf403d7deedffbeeb5bceecc9f8b7f35d510` |

## RIP-2 — the single registered run (OD-S9-09) and its report — 2026-11-19

- Branch `rip2/run`; pre-run commit dfb8ea5 (authorisation + run script); one run, 6024 s, no spec override. Partial reproduction: 12 cells
  identical. Focused tests pass. CI blocked by GitHub billing (FL-022); not merged.

| File | SHA-256 |
|---|---|
| `docs/results/rip2/results.json` | `15f4401d438ddb8b5ee303ce52182ec3f31948d4112b7ffdf940f23b92c87923` |
| `docs/results/rip2/results.sha256` | `a7a950a33f3b9f3c2c894eab8b0a44c3f259276feaefc9382d3bcc941c8e7520` |
| `docs/results/rip2/run_meta_start.json` | `fc1cf4e35ce70d9f8a77c674e29dc8ed5bf07ed096f1b97ddccb2b352db23ea1` |
| `docs/results/rip2/run.log` | `6feb6d992d399f55e850b83488df0c31f45008471d50325bcf0bb838146715b5` |
| `docs/results/RIP-2_REPORT.md` | `3f5dbb112195829cdbfb29912495ae30d52aeab17c7f0fd5ee3ef1db1f857390` |
| `docs/results/RIP2_partial_reproduction.json` | `e6a69df57e0b6cd3790d4430ea972e8d85c5f772a2f03881982f365e4ee8b56d` |
| `scripts/rip2_run.py` | `563edb215986813f813665ba580a561b675d858eabcc3ee6cbeb840b66113e22` |
| `scripts/rip2_partial_repro.py` | `83b3021d76b8421b992a50bf948592bdba1a6e8ed55aa24535d75e29ad3495de` |
| `tests/test_rip2.py` | `2bafaef03cbe4e4ea3cf284f0062eab31b5facf6a6e98565ffa1c23776c747de` |
| `docs/HANDOFF.md` | `6b65e6d3ee65d543ccc9bfecdc2d7c84e4ba8b6373e85348093fe8dc048bc692` |

## RIP-2 result audit closed (NO BLOCKERS; 3 MINOR doc items) — documentation only — 2026-11-19

- Branch `rip2/run`. No code, result or frozen file changed (results.json sha256 15f4401d… unchanged). Focused tests 47 passed.

| File | SHA-256 |
|---|---|
| `docs/results/RIP-2_REPORT.md` | `23beeacbe9b159d1e425f3bf9ed3a27eaa7cf8b21565912432ab28c4ae67ef4b` |
| `docs/research/RIP2_STATUS.md` | `6148c473764988302471293b60194bb9284d3daa52f7812771d571b2994f85ed` |
| `docs/audit/RIP_register.md` | `37c165be4454c448e9efd34c3e9ad6c8d2b1dab6f62b666a0ce3ec260e000b66` |
| `docs/HANDOFF.md` | `079b5cbc04e8845be59096d5730b942e147ada4564c988d1a6f634691143faf6` |

## RIP-3 design v0.1 (OD-S9-10, DESIGN ONLY; nothing built or run) — 2026-11-19

- Branch `rip3/design-v01`; documentation only.

| File | SHA-256 |
|---|---|
| `docs/research/RIP3_DESIGN.md` | `b1f6cc59cc5bcd70e0b28d5921b77780b4e8cf67eaeab324fd912c308d3b76bc` |
| `docs/DECISIONS.md` | `235abc369447781635d7155482f76d1867f9847fcd26b1e19ac0a505d7e3eb87` |
| `docs/audit/RIP_register.md` | `fa7163dd5197cbe57eb96e2e159f366b11bd61fae15457ace824f0ac2addba19` |
| `docs/HANDOFF.md` | `92ac74568bb62e365fdf96258e13273bfc5b9e88c0c019939818137c6bce486d` |

## RIP-3 design v0.2 (review R1 answered; DESIGN ONLY) — 2026-11-19

- Branch `rip3/design-v02` (from rip3/design-v01); documentation only.

| File | SHA-256 |
|---|---|
| `docs/research/RIP3_DESIGN.md` | `fcb12ba15f6253d565a6ed195716cbe89f3b72de9ce27221a4359094a010e8f9` |
| `docs/audit/RIP_register.md` | `0567a9e108c4bfd9b328d1ff2f26502d93a0d2eef7580b53602bc914e53fe786` |
| `docs/HANDOFF.md` | `912894b418ed26e3899f6b48f87280de4d622dff2e96a34304bed8a4505307c2` |

## RIP-3 design v0.3 (review R2 answered; DESIGN ONLY) — 2026-11-19

- Branch `rip3/design-v03` (from rip3/design-v02); documentation only.

| File | SHA-256 |
|---|---|
| `docs/research/RIP3_DESIGN.md` | `27d90c4eb6690f8e7339341966eb90731c11521d505cc028b5e4ff697213c2b1` |
| `docs/audit/RIP_register.md` | `ef89a7e1652af829ac263be604daff571728c8f7b8d9840b34a23396db4942ee` |
| `docs/HANDOFF.md` | `76624b7a9a75ef9518aa53fb016a09aa5fefba9076929ff575dcac0cd9d8fac2` |

## RIP-3 design v0.4 (review R3 answered; DESIGN ONLY) — 2026-11-19

- Branch `rip3/design-v04` (from rip3/design-v03); documentation only.

| File | SHA-256 |
|---|---|
| `docs/research/RIP3_DESIGN.md` | `efb7e16315476c4d4caa523fc8d45adcdd1c3ae0e6bbc13d35b8d7902def7898` |
| `docs/audit/RIP_register.md` | `cc3018080b5662f4b2480379f50456c78c93e136b2393190782ab71ff3ee4f50` |
| `docs/HANDOFF.md` | `955a873ae1aebcd1b91db10f0fc98eee6e87f5a64800b6593b4de6b55ea80852` |

## RIP-3 design v0.4 FROZEN (FD-01-D47; DESIGN FREEZE ONLY) — 2026-11-19

- Branch `rip3/design-freeze` (from rip3/design-v04, which carries v0.1–v0.4); documentation only.
- The design file is byte-identical to the reviewed commit 4e0e861.

| File | SHA-256 |
|---|---|
| `docs/research/RIP3_DESIGN.md` | `efb7e16315476c4d4caa523fc8d45adcdd1c3ae0e6bbc13d35b8d7902def7898` |
| `docs/DECISIONS.md` | `622005ef06d4e01ce4f12b85f2c54d1f7f5664b56cf4164a524c6198f25dc72a` |
| `docs/audit/RIP_register.md` | `26e02402b2cd25e35fb35a48e37266d6a489f7e8020e195ffe5a0ba4654e9702` |
| `docs/HANDOFF.md` | `8af069929ffeb135f91f66f8c9ae10034d6d8438046ed42fb2689eefd931af5b` |

## RIP-3 BUILD (OD-S9-11; BUILD only, RUN not authorised) — 2026-11-19

- Branch `rip3/build` (from main 746df75). Frozen design unchanged. Submitted for independent review; not merged until
  CI is green on Ubuntu and Windows.

| File | SHA-256 |
|---|---|
| `src/xauusd_swarm/rip3.py` | `30740f1cc1bb71b5393bd4790a846289941d0f954c54169253d240ed551353a7` |
| `tests/test_rip3.py` | `ad596fedc4f12807e3166c9d9c772beb239d83efd36bb0fb4dd21ac7ef964eaa` |
| `scripts/rip3_run.py` | `c0b1b846400ab8f2816e502583e88e6e39a2c33c642152c6781257f24771ec09` |
| `scripts/rip3_rescore.py` | `a8792c1d30d5dea30e46e2e6b5b43bdd90b3aa04768c78bf7fbfa7f0f47c9f39` |
| `scripts/rip3_partial_repro.py` | `0011bb5101b5a280292ce9647d20eefea53f072ea86574dc1749c1ac9fc3095e` |
| `scripts/rip3_w2_truth_verify.py` | `1735885a521331073c5d1a6a7e6701a7a9b1e382edd323d13cda8c341ac6dd21` |
| `scripts/rip3_a6_verify.py` | `ca11c92766574b57137900f391960ec0d2ef1bd008d4e370b46575b8ea417a63` |
| `scripts/rip3_build_validate.py` | `fb8f9ed1ccdee0404a9aa765ec529acd93faffec527f54b772d81abd46c0351e` |
| `docs/research/RIP3_BUILD_NOTES.md` | `a2c51d1891e7fcff985cc8a649c1e35f264dd432aa9cebbb28630eb5507c7191` |
| `docs/research/RIP3_DESIGN.md` | `efb7e16315476c4d4caa523fc8d45adcdd1c3ae0e6bbc13d35b8d7902def7898` |
| `docs/results/rip3_build/B1_w2_truth_verification.json` | `020517f888f4dedeb44c1275db6a6330fda8c9c4628628d8e5f0bdcde8a61c7f` |
| `docs/results/rip3_build/B2_a6_verification.json` | `d057be30d6d576e0e4d2461993dd9d050cc3273a146ab51f281af1a8889716e3` |
| `docs/results/rip3_build/B2_a6_verification_attempt1_FAILED.json` | `9dc603ef0a40051e736090587f8e91491d9c06dbfc3e9fa464aa5821d8c974a4` |
| `docs/results/rip3_build/B3_a7_validation.json` | `e60aec71f20deafa46bfe7b3900dfddd2a7d18b3820cff3cf99738d87961badf` |
| `docs/results/rip3_build/B4_w2_moments.json` | `a4358fb17dae99c25400488e164ac79d200da86a9734ef7795a291cb630dfb87` |
| `docs/results/rip3_build/build__B-AF__W1.json` | `5094c0f45cb33991d0591cf0a48ded0497bc02fdd7519cf35ddfc606d5208c39` |
| `docs/results/rip3_build/build__B-LR__W1.json` | `47adbf817185c2b0e1862d87345a8f20681b60e7cf8fa32ef39c12e622a1ba7a` |
| `docs/FL.md` | `8518a84c238d1c1267482cfbb3f14479cb0e670cc30de3c7e2c1a4d9b0dc6254` |
| `docs/DECISIONS.md` | `892326dfc1b634216bb742310830bad0fc0ec85368c15f43f587dfe09f0e0813` |
| `docs/audit/RIP_register.md` | `ad3d93e13ec19fab0e63a583a8676cf6308e81977c4edff524ef9a0cf1982f04` |
| `docs/HANDOFF.md` | `99d6ceb42a1b05d79d2e6d8a1b23608447fefc1c128e91023e4425c39c8a28c7` |

## RIP-3 BUILD — corrective delivery (founder directive 2026-11-22; BUILD only, RUN not authorised)

- Branch `rip3/build`. Code commit 020ea8c: local full suite incl. heavy 883 passed; bundle-extraction run 51 passed.
- CI: runs 45043264239 (4a00e10) and 45043957646 (020ea8c) were NOT started by GitHub (billing, FL-032). Last executed
  CI: 44516479468 on d6bce2b, green on Ubuntu and Windows. Not merged.
- Frozen design v0.4 unchanged; DCR-01 only as the separate draft v0.5.

| File | SHA-256 |
|---|---|
| `src/xauusd_swarm/rip3.py` | `7d009055c14e533987eadcc58d67a2c731c230618d5edcccdde955b60ed0718e` |
| `tests/test_rip3.py` | `58e360a92cdc12103bf87848ed8218aab60d19f7b4e0deb512cc6dc8493cf414` |
| `scripts/rip3_bundle.py` | `b88dfc81ece69d31f4a0f2569d87ac97b2d23835c49dfeb7971335b3c3877f9d` |
| `scripts/rip3_w2_truth_verify_v3.py` | `26dc7519a2e69b0423bff21ba75df1dd58a816b2e36760093d46c92faeafcfd9` |
| `scripts/rip3_a6_verify_hp.py` | `12f4e6e2284be9a2582061bddaa8052697cf8445f331054126f23472f69586ac` |
| `scripts/rip3_dcr01_study.py` | `890de453a13d7396422048cf53385642057bb0a421d216e27a4500ed87f4cb55` |
| `docs/research/RIP3_BUILD_NOTES.md` | `1fd2e965c611916c83f69b58bb71e3050fca812f42199870452b1a72720edda1` |
| `docs/research/RIP3_IC_REPORT.md` | `ce4083a05236e26ef46fe90fbce4ac2d2e8aed3f0f0119b6fa0711d5ba2993f1` |
| `docs/research/RIP3_DESIGN_v0.5_DCR01_DRAFT.md` | `ad83b91f230de0ba3bc4bde64d1f842c00b081b4803028ac765b2f17f71e192f` |
| `docs/research/RIP3_DESIGN.md` | `efb7e16315476c4d4caa523fc8d45adcdd1c3ae0e6bbc13d35b8d7902def7898` |
| `docs/results/rip3_build/B1_w2_truth_verification.json` | `020517f888f4dedeb44c1275db6a6330fda8c9c4628628d8e5f0bdcde8a61c7f` |
| `docs/results/rip3_build/B1_w2_truth_verification_attempt3.json` | `f9ab739fe35572f7425a8fa88a8216074542f4c76c19fbfdf4f1112d5ec5539f` |
| `docs/results/rip3_build/B1_w2_truth_verification_attempt4.json` | `eaa0b9ae6d95be47a5957cf188633253ca7c3a76c545da95baeb325d10e60e5a` |
| `docs/results/rip3_build/B2_a6_verification.json` | `d057be30d6d576e0e4d2461993dd9d050cc3273a146ab51f281af1a8889716e3` |
| `docs/results/rip3_build/B2_a6_verification_attempt1_FAILED.json` | `9dc603ef0a40051e736090587f8e91491d9c06dbfc3e9fa464aa5821d8c974a4` |
| `docs/results/rip3_build/B2_a6_verification_attempt3.json` | `0d3455841f78d8934661d07860fed5c7083e32e0d3fff6ae40556c5e092b4351` |
| `docs/results/rip3_build/B3_a7_validation.json` | `e60aec71f20deafa46bfe7b3900dfddd2a7d18b3820cff3cf99738d87961badf` |
| `docs/results/rip3_build/B4_w2_moments.json` | `a4358fb17dae99c25400488e164ac79d200da86a9734ef7795a291cb630dfb87` |
| `docs/results/rip3_build/DCR01_study_dev.json` | `70c171b84d8a4695b2e4e2e18274f589ba16ad952390619670d25c082db0e1d9` |
| `docs/results/rip3_build/build__B-AF__W1.json` | `5094c0f45cb33991d0591cf0a48ded0497bc02fdd7519cf35ddfc606d5208c39` |
| `docs/results/rip3_build/build__B-LR__W1.json` | `47adbf817185c2b0e1862d87345a8f20681b60e7cf8fa32ef39c12e622a1ba7a` |
| `docs/results/rip3_build/test_runs/bundle_extraction_020ea8c.txt` | `59225a36c66da7e435dc304a6ca2b1299b4cb11f6df25b5391b389dda927b844` |
| `docs/results/rip3_build/test_runs/local_full_suite_020ea8c.txt` | `51404550c5dfbc27fe41090e2e4482a2e1dd9f420a2eb607d3529a579bb53fe0` |

## RIP-3 BUILD — review R-B1 resolutions (BUILD only; RUN not authorised) — 2026-11-22

- Commit 2158e6d: local full suite incl. heavy 884 passed (clean tree). CI run 45054531346 on 2158e6d and the re-run of
  45046829787 on 76edffd were NOT started by GitHub (billing, FL-032). Last executed CI: 44516479468 on d6bce2b (green).
- src/xauusd_swarm/rip3.py unchanged since 4a00e10. Frozen design v0.4 unchanged; DCR-01 only as drafts (r1, r2).

| File | SHA-256 |
|---|---|
| `src/xauusd_swarm/rip3.py` | `7d009055c14e533987eadcc58d67a2c731c230618d5edcccdde955b60ed0718e` |
| `tests/test_rip3.py` | `25d43e074428a50e6c894470ddf27d250c7c9f6048b064cb29c5bd21d59e85d8` |
| `scripts/rip3_bundle.py` | `77842d2ea5bdea69e9ad9681d461f6ca6cb9b0d02fa0b7b87e67e51ae2db4077` |
| `scripts/rip3_b1_case10_hp.py` | `16999e97cab67d37863912df1cb9cfce3523089517f988278c0d42811ac00a84` |
| `scripts/rip3_dcr01_study_v2.py` | `3046f0ecb827ef51bd74931fcf2d197de7b88d5b0f0816f7dd888d442d192429` |
| `docs/research/RIP3_DESIGN_v0.5r2_DCR01_DRAFT.md` | `18100a82898c8fe83a46ebe2728da6881bf075b9c2a64b3c00d697b1b7f7a1c5` |
| `docs/research/RIP3_BUILD_NOTES.md` | `c828939cc9cb46a282275b3f9fd433ac344105bd36960f692ee28a62b2624117` |
| `docs/research/RIP3_DESIGN.md` | `efb7e16315476c4d4caa523fc8d45adcdd1c3ae0e6bbc13d35b8d7902def7898` |
| `docs/results/rip3_build/B1_case10_highprecision.json` | `ccdcc91c7343f60f62b3f02ee23f56ba310baebcb77da10a3cd75904bbbf9800` |
| `docs/results/rip3_build/DCR01_study_dev_v2.json` | `64b981b5129fcedab64576797cee2ae01ffe06dddfd56a2ada2150474d461988` |
| `docs/results/rip3_build/test_runs/local_full_suite_2158e6d.txt` | `5b179be09abbf0cdb041907c5dacfd35ecfc804b1f829ae8cd6c5a1f3779ff89` |

## RIP-3 BUILD — FL-032 tree-equivalent CI evidence (OD-S9-13; BUILD only, RUN not authorised) — 2026-11-23

- CI on GitHub Actions in the public sandbox repository mulaalig87-ops/XAUUSD-Swarm-CI-Sandbox, on parentless snapshot
  commits with trees identical to 155b00f, 61eff1b, 5eeb005: runs 45066506808, 45066507333, 45066507466 — all green on
  Ubuntu (877 passed, 7 skipped) and Windows (867 passed, 17 skipped). Not CI on the original commits themselves.
- No code or test changed in this commit (documentation and evidence only). FL-032 stays OPEN until the reviewer's check.

| File | SHA-256 |
|---|---|
| `docs/results/rip3_build/test_runs/FL032_sandbox_ci/EVIDENCE.md` | `f399d7076a8a36534be99ec87a61d78aceb562845a363bebab44077814129f16` |
| `docs/results/rip3_build/test_runs/FL032_sandbox_ci/tree_manifest.json` | `64ab143984a2c5d76f8c5040ccc4fec299b5429ee5d052a78bec8aa278d0bd2c` |
| `docs/results/rip3_build/test_runs/FL032_sandbox_ci/logs/run_45066506808_155b00f_ubuntu.txt` | `cd18bc288f6a80af4eded0be26c354e527c11e0b10ed3d3bfb887014155ca867` |
| `docs/results/rip3_build/test_runs/FL032_sandbox_ci/logs/run_45066506808_155b00f_windows.txt` | `bb9df4cb995f47848ff1c795d3b7d33eb6309becac760abee1a2260a42ae3245` |
| `docs/results/rip3_build/test_runs/FL032_sandbox_ci/logs/run_45066507333_61eff1b_ubuntu.txt` | `9969183a74f25bb84b007a25a523e6d383333b0c715a784bef9e38ce2fb92d1d` |
| `docs/results/rip3_build/test_runs/FL032_sandbox_ci/logs/run_45066507333_61eff1b_windows.txt` | `2aad9b6808f9f8be79de0bf05e95a62e677f2e4f4aa3422f93cccb71abf3b525` |
| `docs/results/rip3_build/test_runs/FL032_sandbox_ci/logs/run_45066507466_5eeb005_ubuntu.txt` | `8630c96f3145fd408d62398e24f9b736a32e1040bb38bd749bcf7b1815433117` |
| `docs/results/rip3_build/test_runs/FL032_sandbox_ci/logs/run_45066507466_5eeb005_windows.txt` | `8ec3bde3a6ee6141fc89826f29478a62e34fa986f432f86fb320da5112d8eaf5` |

## RIP-3 BUILD — FL-032 closed (reviewer ACCEPTED) — 2026-11-23

- Records the reviewer's acceptance of the FL-032 evidence (commit 8fd8cdb) and closes FL-032, R-B2-01 and R-B2-04.
  Documentation only; no code, test or evidence file changed. BUILD only; RUN not authorised.
- Sandbox CI on 8fd8cdb (snapshot 351ef61, same tree 48a5714a0e4d86c375eb1ea3cc71bd010cd3a09e): run 45073349262
  (https://github.com/mulaalig87-ops/XAUUSD-Swarm-CI-Sandbox/actions/runs/45073349262) — Ubuntu 877 passed, 7 skipped;
  Windows 867 passed, 17 skipped. Local full suite incl. heavy on this commit's tree: 884 passed.

## RIP-3 BUILD — final closure records (documentation only; reviewer verdict «RIP-3 BUILD ACCEPTED»; OD-S9-14) — 2026-11-23

- Reviewer verdict on main 1195603 (tree ddb3ce984673bdd0344b4fed000666f1400fa4a8): RIP-3 BUILD ACCEPTED; R-B1-01 and
  R3B-00 closed. Founder decision OD-S9-14: no RUN authorisation; 6201 / 6301 not to be used.
- Sandbox CI on ad41547 (head of rip3/build; its tree = the main tree ddb3ce9): snapshot 073534d3d277d3fba60e7358cfc0ab2b7a6bff5c,
  run 45077432523 (https://github.com/mulaalig87-ops/XAUUSD-Swarm-CI-Sandbox/actions/runs/45077432523):
  Ubuntu job 137377687716 success — 877 passed, 7 skipped; Windows job 137377687485 success — 867 passed, 17 skipped.
  Also kept: logs of run 45073349262 on 8fd8cdb (snapshot 351ef61e06f22bb4ea14020ec194c8023ea2ac57), jobs 137365048603
  (Ubuntu) and 137365048355 (Windows). Both are CI equivalent to the original source tree in the public sandbox repository,
  NOT CI on the original commits. CI on the private repository (e.g. run 45079393961 on 1195603) is not started by GitHub (billing).
- Adds final-status tables to RIP_register.md and FL.md (earlier rows kept as history), OD-S9-14 to DECISIONS.md, HANDOFF update.
  No code, test, design or acceptance-rule change.

| File | SHA-256 |
|---|---|
| `docs/results/rip3_build/test_runs/FL032_sandbox_ci/logs/run_45073349262_8fd8cdb_ubuntu.txt` | `c20daaa68e431583ddc58bb5febb4701b99ed722b333d43bedec153cb73534fc` |
| `docs/results/rip3_build/test_runs/FL032_sandbox_ci/logs/run_45073349262_8fd8cdb_windows.txt` | `288e83c798176d2242517f2b5b46f841c2d6346bda8ba21e0ae0324144dc1a35` |
| `docs/results/rip3_build/test_runs/FL032_sandbox_ci/logs/run_45077432523_ad41547_ubuntu.txt` | `76cae9a4ecbf8dc290b1c9e3bd7151bf2f1e3eb29859f82b1f7e52462007944a` |
| `docs/results/rip3_build/test_runs/FL032_sandbox_ci/logs/run_45077432523_ad41547_windows.txt` | `a66b112552c7db6f2bea4cf128fc119e209869be0a80a7fa8e397db4112292c8` |

## Handoff verification of the delivery point 775ce2b (documentation only; OD-S9-15) — 2026-11-23

- Read-only verification of `main` 775ce2b (tree eb1bbe0) against the handoff file, and of sandbox run 45130818597
  (snapshot d4ea09545e286a7e803df9490035e66e25b96fc9 of a213e56, same tree): success on Ubuntu (877 passed, 7 skipped)
  and Windows (867 passed, 17 skipped) in attempts 1 and 2. CI equivalent to the tree of 775ce2b, not CI on 775ce2b.
- Adds VERIFICATION.md, two local test outputs, EVIDENCE.md §5, OD-S9-15 (DECISIONS.md), FL-033 and FL-034 (FL.md), a HANDOFF note. The original
  evidence is kept in the private repository and is not published. No code, test, design, acceptance-rule or
  result change. Differences found are recorded, not fixed.
- Local full suite (incl. heavy), `python3 -m pytest -q -p no:cacheprovider`, run alone with a clean working tree at each commit:
  - a799a41 (tree 0c1fe45ae2df23f39374aa48e58b93ccf1637385): 884 passed in 2011.89 s — `local_test_runs/local_full_suite_a799a41.txt`.
  - 1499600 (tree f4b2af0cc5b9bca958162d917232d0c4692deb17): 884 passed in 2014.91 s — `local_test_runs/local_full_suite_1499600.txt`.
  The outputs do not print the commit. Each run was started right after that commit was made (`git add -A`, nothing left
  uncommitted) and nothing in the checkout was changed until the run ended; `git status` was checked clean after the
  1499600 run. The last line `EXIT 0` was appended by the run wrapper. No run is recorded for the
  commit that adds these files and this text (documentation only); a full suite must pass on it before any push (FL-017, FL-033).
- Earlier, two suites run at the same time interfered (FL-034); those runs are not counted.

| File | SHA-256 |
|---|---|
| `docs/results/handoff_verification_2026-11-23/VERIFICATION.md` | `c2e9f086b4ab33fe77adddfcc69a2aa840d52db85aeeb7b2fed827398af44cbb` |
| `docs/results/handoff_verification_2026-11-23/local_test_runs/local_full_suite_a799a41.txt` | `1e4ebfed83f10d1499417fd89c7d73f2f5922c253af868ea8c2e7518fdb09254` |
| `docs/results/handoff_verification_2026-11-23/local_test_runs/local_full_suite_1499600.txt` | `741fc868cbe72690c4fd6557654fc5bd6cbd238b5392adc3b8cd4bac3de271ff` |

## Resume-point documentation fixes (documentation only; OD-S9-16) — 2026-11-23

- `docs/HANDOFF.md`: «884 passed» in the full suite and the sandbox merge gate; rip2/build and rip3/build described as
  merged; latest documented `main` 7fcd418 (tree 9267ff7); delivery point 775ce2b unchanged.
- `CLAUDE.md`: commit trailer `Co-Authored-By: Claude <noreply@anthropic.com>` only (no session line); hook-path step for
  fresh clones; the CI gate in force (sandbox CI equivalent to the tree, content check and founder approval before
  publication, private-repo CI still blocked).
- `docs/DECISIONS.md`: OD-S9-16. No code, test, environment, reference or design change.

| File | SHA-256 |
|---|---|
| `CLAUDE.md` | `735f95c2ed171f3f15517fa7a4430326e0277a57e1553f25779554b478915a0a` |
| `docs/DECISIONS.md` | `5a9970316492378be20fb17ecbda49ebf979494b1d587a32f306317cc3f26817` |
| `docs/HANDOFF.md` | `2f316d2a5101d277fb86ecefb7cd59420c54ed4ee49dcd1cb0e68f7ae7eb2dd3` |

## RIP-3 run readiness — preparation (OD-S9-17; no RUN; 6201 / 6301 untouched) — 2026-11-24

- B-1: IC3-23 (`rip3.confirm_cells`, `rip3.fc3`, `rip3.class_floors_hold`): the confirmatory cells are derived from the
  hash-checked `eval_results.json` (B-LR + chosen + nearest competitor per class; no B-AF); FC-3 per class, with the six
  §7.2 floors required exactly (missing, extra or unreadable = failed). IC3-25: `select()` uses the same complete-floor
  rule (unchanged results with complete floors).
- Authorisation guard (reviews DP-R1-03 and 2026-11-24): `scripts/rip3_run.py` needs a recorded founder decision
  («RIP-3 RUN» heading stating the scope sha256) and an entry in `docs/research/RIP3_RUN_AUTHORISATIONS.json` (empty),
  both unchanged since they were recorded, and the approved commit/tree; committed HEAD only; `--cands` refused for the
  confirm set; confirm assembly adds `confirm_cells` and `fc3`.
- IC3-24: atomic job and truth files. B-2: `docs/research/RIP3_RUN_PROTOCOL.md` (no machine specification, no absolute
  local paths). R14: B1-HP values in the build notes.
- Tests: smoke set, synthetic dicts and throw-away git repositories only. Design v0.4 (sha256 efb7e163…7898) and its
  acceptance rules unchanged.

| File | SHA-256 |
|---|---|
| `src/xauusd_swarm/rip3.py` | `6d7c6520b7cff6502cb4b6cd1106f354bfb0c04cdcb194f88696690d10c51982` |
| `scripts/rip3_run.py` | `e5f07924f9519bed611b83ca9be70072c6d4dd7b20c45324d4af0659dbeb8b3c` |
| `tests/test_rip3.py` | `3eea3ec3beb292231ea305c1a1843e1c151d6bc2d3200790967e083e4b84126f` |
| `docs/research/RIP3_RUN_AUTHORISATIONS.json` | `cf42edc937347732462833d13a1bc8707cd09239717a3e7bc9987d40ae7c79ca` |
| `docs/research/RIP3_RUN_PROTOCOL.md` | `f6e2022bde6062f261ed71815c516a42910ca19cf59e677583e5339ffb2a7b74` |
| `docs/research/RIP3_BUILD_NOTES.md` | `8680ba1a481a265c448be5d78c035be22da80912811a6de84e0e927bc1ee18bf` |
| `docs/research/RIP3_IC_REPORT.md` | `28d0fc246c774e34a95a4f3b040e896e9442cd2b321b8a87c602519d4d177e32` |
| `docs/DECISIONS.md` | `bf9c2ef32d1dec80b8a166647255216a756fa82a7f70b4391bc37014f9885cc4` |

## FL-035 — authorisation-registry consistency test (tests only; OD-S9-18; no RUN; 6201 / 6301 untouched) — 2026-11-24

- `tests/test_rip3.py`: `test_no_run_authorisation_exists_in_the_repository` (empty registry required) replaced by
  `test_run_authorisation_registry_is_consistent_with_the_decisions` and
  `test_run_authorisation_registry_consistency_check_cases` (exact scope keys, unique id, valid sets, full ids; exactly
  one H2 `## Founder authorisation <id> — …` heading with «RIP-3 RUN» and an exactly equal id; exactly one line
  `scope sha256: <hash>`; any H1–H6 «RIP-3 RUN» heading without a matching entry fails; confirm and unrecorded ids
  still refused). 3 accepted, 25 refused cases.
- `docs/FL.md`: FL-035. `docs/DECISIONS.md`: OD-S9-18 (no authorisation recorded). `docs/research/RIP3_BUILD_NOTES.md`:
  FL-035 line. No change to `scripts/rip3_run.py`, `src/`, the registry (still empty), the protocol, the environment,
  `docs/reference/*` or design v0.4.

| File | SHA-256 |
|---|---|
| `tests/test_rip3.py` | `620bfe29a790a94060ed8d1d229ea2fc2e2c19f93cd1081782f4f8c76b50ea9e` |
| `docs/FL.md` | `e01d70180810987ce5c4e217f629a028375518833338ef26043648f6347cba83` |
| `docs/DECISIONS.md` | `99273aee255e59465acfbd23635b2d70546d5e65e8ce915ff3fcbadc1503b41b` |
| `docs/research/RIP3_BUILD_NOTES.md` | `d1b93fc2f628038fa56c63a7316d3d7c01b9ea19aafb730a760397a06ac8e157` |

## FL-036 … FL-046 — run-driver hardening (assemble, resume, provenance, guard; OD-S9-19; no RUN; 6201 / 6301 untouched) — 2026-11-24

- Branch `rip3/run-hardening` from local main 9907d52 (tree 653ae50). Commits: a23e92f (FL-036 … FL-046 recorded, docs
  only), 85a03d5 (one test per defect; 38 failed and 3 positive controls passed on that commit), d3fc049 (fixes; 41
  passed), then this record.
- `scripts/rip3_run.py`: bytes and hash on the same bytes (FL-036); exact expected files before assembling eval / confirm
  (FL-037); assemble once, no job run once a result exists (FL-038); provenance of every job and truth file and one code
  and environment per set (FL-040); origin of the eval result checked by confirm (FL-041); RIP-2 input fixed and
  recorded (FL-042); meta files per process, never overwritten (FL-043).
- `src/xauusd_swarm/rip3.py`: unique temporary files and publish-without-replace for job and truth files (FL-043);
  `load_jobs` checks every file against its name (FL-039); library guard with the recorded authorisation and a clean
  tree, a boolean refused (FL-045); IC3-26. `src/xauusd_swarm/rip3_auth.py` (new): the one strict checker (FL-044).
- `tests/test_rip3_run_hardening.py` (41 tests). No test scores a registered set (sentinels).
- `docs/FL.md` (FL-036 … FL-046), `docs/DECISIONS.md` (OD-S9-19), `docs/research/RIP3_BUILD_NOTES.md` (IC3-26, guard
  paragraph, hardening and FL-046 notes). Unchanged: design v0.4, seeds, acceptance rules, every statistic, the run
  protocol text, `docs/reference/*`, the registry (still empty). FL-036 is not closed until the Windows CI job runs.

| File | SHA-256 |
|---|---|
| `scripts/rip3_run.py` | `7ed5deaf424c824db36f23c35d1d750caac90a51ea8361b2ac6737b6c77dcb58` |
| `src/xauusd_swarm/rip3.py` | `c4b1165ac1caf2f9f4c69d76f0d0c126606542b85cc712c26d78cce911c92497` |
| `src/xauusd_swarm/rip3_auth.py` | `802707dc9685d2b32cbd024c456b38f788a16780cc1bde2215efb0e2a9ffda7b` |
| `tests/test_rip3_run_hardening.py` | `f7abb1f66b764145c967bcd917fb33722f82e70249c05ebaa07a8a9ccc557753` |
| `docs/FL.md` | `e297c6c9abd41469755847df9a4beadf402a89dada3f8c7819f80b67a68a0f96` |
| `docs/DECISIONS.md` | `453b58b3b2503565b761ef6727ad876c5a88c8006b9c393297e84d10cb4c3902` |
| `docs/research/RIP3_BUILD_NOTES.md` | `3a9c953ffbc3ab3b5c41e7f176a1826a60f2ecd49485e1c34ac83d76bf21daf3` |

## Review R1 + FL-047 — second hardening round (OD-S9-20; no RUN; nothing registered generated) — 2026-11-24

- Commits on `rip3/run-hardening` after ce436c0: 1f4e9e0 (R1-1 … R1-4 and FL-047 recorded, docs only), 4c493c9 (tests;
  33 failed and 44 passed on that commit, the failures being the new tests), 4079b35 (fixes; 77 passed), then this
  record. Two tests were adjusted after the before-run, in 4079b35: the patch target of the race test moved from
  `run_job` to `_run_job` (run_jobs no longer calls the public run_job), and the coverage list names
  `authorised_scope` (the guard itself).
- `src/xauusd_swarm/rip3.py`: `authorised_scope`; guarded seeds in `stream`, `make_family`, `eval_families`,
  `utility_pairs`, `truth_job`, `utility_job`, `identity_scenario`, `gates`, `evaluate`; `HardLinkUnsupported`,
  `check_hard_links`, no publish fallback; IC3-26 text. `scripts/rip3_run.py`: hard-link check of the output folder,
  invocation binding, eval meta checks, authorisation passed to `evaluate`. `scripts/rip3_partial_repro.py`:
  `--authorisation`. Unchanged: design v0.4, seeds, acceptance rules, every statistic, the run protocol text,
  `docs/reference/*`, the registry (still empty). R1-2 and FL-036 are not closed until the Windows CI job runs.

| File | SHA-256 |
|---|---|
| `scripts/rip3_run.py` | `5bd93571938162ebd35d46cb1941c641a54d1299fcc66b31299f1c20dd8947cc` |
| `scripts/rip3_partial_repro.py` | `9a2dd809779bc77f982b354f75127cd1a73ced8914cfec32e8871409a75da5b9` |
| `src/xauusd_swarm/rip3.py` | `280ab74a3ddf4a3f042250c0e55f75688ad8f9503f7d386d40c47b2a5c137e1c` |
| `src/xauusd_swarm/rip3_auth.py` | `802707dc9685d2b32cbd024c456b38f788a16780cc1bde2215efb0e2a9ffda7b` |
| `tests/test_rip3_run_hardening.py` | `8e82438a3a519ba96355819b4829392baefa2dc50aeed79bf2598125ada1f86d` |
| `docs/FL.md` | `cfc4f767af5edfa60545caf171ed0d1357f9d4f7d894d4af9053db245547e93d` |
| `docs/DECISIONS.md` | `c493db3c0489083a3f3c02431ea87a06bc1a7481b0a31e9497efd73d77eea498` |
| `docs/research/RIP3_BUILD_NOTES.md` | `5a03542388e023bb5f9d82036b4303ea479cb72b4569f8325c1ed1177da8cd8f` |

## Review R2 — third hardening round, FL-047 and the environment check (OD-S9-21; nothing registered generated) — 2026-11-24

- Commits on `rip3/run-hardening` after 44e48c8: c2e0ca5 (R2-1 … R2-4 recorded, docs only), 8caef9e (tests; 61 failed
  and 110 passed on that commit — the failures are the new tests for text, object and separator forms, sequence
  seeds in gates and the missing environment check; the NumPy-integer forms were already refused and pass as
  controls), f596d72 (fixes; 171 passed), then this record, which also adds one structural control test
  (`test_r2_every_generator_of_rip3_is_created_at_a_guarded_point`: generators are created only in `stream`,
  `_evaluate` and `gates`; the same three places before and after the fix).
- `src/xauusd_swarm/rip3.py`: the seed guard decides on the first field of the final seed string; `gates` takes integer
  seeds only; IC3-26 text. `scripts/env_lock_check.py` (new). `tests/test_rip3_run_hardening.py` (R2 tests; the
  sentinel also catches sequence seeds), `tests/test_env_lock_check.py` (new). Unchanged: design v0.4, seeds,
  acceptance rules, every statistic, the run protocol text, `docs/reference/*`, the registry (still empty). FL-036 and
  R1-2 still need the Windows CI job.

| File | SHA-256 |
|---|---|
| `src/xauusd_swarm/rip3.py` | `f5ceb1c76da5f22d0ee5bad06d3f54b75618d869f887946313084f1cdb356dee` |
| `src/xauusd_swarm/rip3_auth.py` | `802707dc9685d2b32cbd024c456b38f788a16780cc1bde2215efb0e2a9ffda7b` |
| `scripts/rip3_run.py` | `5bd93571938162ebd35d46cb1941c641a54d1299fcc66b31299f1c20dd8947cc` |
| `scripts/rip3_partial_repro.py` | `9a2dd809779bc77f982b354f75127cd1a73ced8914cfec32e8871409a75da5b9` |
| `scripts/env_lock_check.py` | `b5d95b7c1c26f9cd7becae9d54a0fdb0d85bb6915ca07f4d243caa6691ce4c85` |
| `tests/test_rip3_run_hardening.py` | `5084cd84b2d92f92ff6afc848b3dc04cd0a4a8826c20a149d50e26386fb5fd90` |
| `tests/test_env_lock_check.py` | `72c18b775b2bca928455905627daa91dcbdc6bb19c96f198c9c42f1d3ca55d2f` |
| `docs/FL.md` | `6e3a043919f03f84101176d2ed48687e6224ee70c4c563a942b584f1c77517e9` |
| `docs/DECISIONS.md` | `2344f22fef16ecaa71606d54dbc6a3b8da6357e1b6593951ee744e92b5e11e12` |
| `docs/research/RIP3_BUILD_NOTES.md` | `8cced9c1d3ebeb54dda7b726ba135cab45241b1172c39beba9bb02f192a1bfe9` |

## FL-048 — git output decoded as UTF-8 in the guard and meta() (OD-S9-22; nothing registered generated) — 2026-11-25

- Found by the Windows job of sandbox run 45491211968 (snapshot 0d0c720, tree ff93e9c of 828cb27): Ubuntu 1067 passed /
  7 skipped; Windows 7 failed / 1050 passed / 17 skipped (the seven `test_run_authorisation_guard_*`).
- Commits after 828cb27: bd76866 (FL-048 recorded, docs only), 34e30c8 (tests; the 9 FL-048 tests fail on that commit
  as on Windows), a6becb5 (fix; they pass), then this record, which also lists, in the build notes, the text-mode
  subprocess calls outside RIP-3 that are not changed (rip1, rip1_repro_attest, rip2_run, wp801_sync).
- Unchanged: design v0.4, seeds, acceptance rules, every statistic, the run protocol text, `docs/reference/*`, the
  registry (still empty). FL-036, R1-2 and FL-048 stay open until the Windows CI job is green on the full suite.

| File | SHA-256 |
|---|---|
| `src/xauusd_swarm/rip3_auth.py` | `8594a5056ce52ffaa476c15b1488ab2bd90a31d97d30e2324721d9684684f46a` |
| `scripts/rip3_run.py` | `30fec78cf5aecae6a121e902e544f007b89324bf245dc8ac0fee5ed61f77da3d` |
| `tests/test_rip3_run_hardening.py` | `7f512d8d62fc5a0023f913fe718294b9cc517756d02ed7ff60c4f98cee5364ad` |
| `docs/FL.md` | `2c0f0b6e148f7c255137e96dd0f8650f74989e2b4746a7d6bbff9fd42c2eaae5` |
| `docs/DECISIONS.md` | `93e48791411951b9a41cf874c5aa7452c975b539a444098d5a69f68f07a532cc` |
| `docs/research/RIP3_BUILD_NOTES.md` | `947102435e15c0b7ffa84311088bb2abaa0de727227fa6057853d0ed14ddf990` |
