# Custody vault key — handling policy (WP8-03, D-2 / R2-3)

Status: design decision ruled by ChatGPT under founder delegation (WP8-03 round 2, D-2).

1. **Accepted permanent-loss risk.** The code has no key escrow, backup or recovery path.
   Losing the 32-byte key permanently loses the vault (decryption table, parameters with salts,
   linkage table, hidden truth). This is accepted on purpose: any recovery path would add a
   second holder of the secrets and change the approved custody model.
2. **Holder.** Only the identity holding the `custody` role holds the key. It is never given to the
   custody auditor, the court operator, discovery participants, the G-Z operator or the founder's
   tooling. The custody auditor audits WITHOUT the key (two-signature attestation, D-3).
3. **Never recorded.** The key is never written to the ledger, the anchor store, the access log,
   test output, console output or any report. The code takes the key as bytes or through
   `load_key()`, and never writes it.
4. **Location.** The key file must sit in a folder other than the vault's and the ledger's
   (`load_key` refuses otherwise). The vault must sit outside the ledger folder (`CustodyLayer.bind`
   refuses otherwise).
5. **Permissions.**
   - POSIX: owner-only (`chmod 600`). `load_key` refuses any group/other bit.
   - Windows: the code cannot check ACLs. Required operational step for custody:
     `icacls <keyfile> /inheritance:r /grant:r "%USERNAME%:R"`. Record the resulting ACL listing
     (`icacls <keyfile>`) in the custody log, without the key.
6. **Limit of encryption.** AES-GCM protects the vault only against someone who lacks the key.
   An OS account that can read both the key file and the vault can read every secret.
   Separation therefore depends on OS account and permission boundaries, which custody must keep.
7. **No gold data.** Until OD-10 opens, tests use synthetic values only.
