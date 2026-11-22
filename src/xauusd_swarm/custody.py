"""Layer 3 — custody, blinding records, access log, sealing gates (WP8-03, spec WP7-03).

Secrets never enter the ledger. The Vault holds the decryption table, the secret parameters
c, a, b, m with their salts (س 213), the G-Z pseudonym linkage table (§26 غ-08, separate from the
decryption table) and hidden world truth (م7-01). It is persisted ENCRYPTED (AES-256-GCM) in a file
outside the ledger folder; the 32-byte vault key is held by custody only and is never written to
disk by this code. The ledger holds only signed decisions, commitments (salted SHA-256) and log
records.

Trust boundary (round-2 fix, R1 blocker 1):
- Every access request is a Signed statement by the REQUESTER (action "access_request", item,
  family, reason, nonce, time), verified through Governance._signed (registered key, action, nonce).
  Request nonces are single-use across restarts (recorded in the ledger via the access record).
- The track is NOT supplied by the caller. It is derived from ledger state: a holder of role
  "gz_operator" -> track G-Z (symbols only); the appointed court operator on a SEALED family ->
  track after_seal (symbols and that family's hidden truth); anything else -> refused.
- The executor is custody: the access record is signed with the custody key held by this layer and
  verified against the custody role. For outcome "ok" the validator RE-VERIFIES the embedded request
  and re-derives the permission from ledger state, so a forged "ok" record is refused even when
  custody-signed. Refusals are logged too (with authenticated=false if the request did not verify).

Implemented (each cites its source):
- Roles by founder-signed assignment; separation of custody / custody auditor / court operator /
  discovery participant / G-Z operator (§13 #2; G-Z operator added to the separated set, flagged).
  Re-identification checker independent of custody, custody auditor, governance auditor and
  discovery participants (D-02, §26 B).
- Custody decisions recorded BEFORE opening (م-03) via the pre_validate hook.
- Parameters fixed per claim family (س 258); fixed/rotated commitments must exist in the vault and
  Δ > 0 on both. Rotation only at a NEW founder-declared epoch (س 260, ق-02), refused while any
  claim is open under the current parameters (س 261, strictest reading; ruled F-3).
- Decryption only on G-Z or after a recorded seal (س 355); every attempt logged (م7-10 #1, #3)
  with the returned output's SHA-256, never the content. Hidden truth only to the court operator
  after sealing (م7-01, ق-27).
- Z output passage only after a full-scope custody leak review (س 277–284).
- G-Z release to language minds HARD-LOCKED (غ-03).
- ZERO-PRIOR state from lineage; "Z-computational" unreachable while CS-01-04 is open.
- Vault integrity after restart: verify_vault() recomputes every commitment recorded in the ledger
  from the vault's (params, salt) and records a custody-signed "vault_verified" event.
Observer mode: CustodyLayer(None) rebuilds and validates the ledger without the vault (for audit
replicas); it cannot decrypt and skips only the vault-membership checks.
Two-signature commitment audit (D-3, ruled): custody runs verify_vault (custody-signed
"vault_verified" with check_id, every recorded commitment, vault ciphertext sha256); the custody
auditor, WITHOUT the key or contents, hashes the ciphertext file itself and records a signed
"vault_attested" (concur/dissent) bound to the custody statement hash. commitments_attested() is true
only for the latest check with a concurrence.
Vault key (D-2, ruled): no escrow/backup in code; losing the key permanently loses the vault — an
accepted design risk. Key handling rules in docs/CUSTODY_KEY_POLICY.md; load_key() enforces location
and (POSIX) owner-only permissions.
NOT implemented / open: CS-01-04 (announced threshold, allowed representation sets §13 #29–30);
calendar variables for Z (م3-13); sealing mechanism beyond "sealed by hash".
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from .charter import GateError
from .identity import AuthError, Signed, sign
from .numeric import finite_real

ROLES = ("custody", "custody_auditor", "court_operator", "discovery_participant", "gz_operator",
         "reid_checker", "governance_auditor", "world_designer")
SEPARATED = ("custody", "custody_auditor", "court_operator", "discovery_participant", "gz_operator")
CHECKER_EXCLUDES = ("custody", "custody_auditor", "governance_auditor", "discovery_participant")
LEAK_SCOPE = ("engine_outputs", "charts_axes_values", "text_reports", "intermediate_statistics",
              "language_mind_messages", "asset_or_period_revealing_data")                    # س 277–282
TRACKS = ("G-Z", "after_seal", "none")
ACCESS_FIELDS = ("requester", "executor", "item", "track", "reason", "time", "outcome", "returned",
                 "authenticated", "request", "request_sha256")
GZ_RELEASE_LOCKED = True                                                                       # غ-03
_AAD = b"xauusd-swarm-vault-v1"
_HEX64 = re.compile(r"[0-9a-f]{64}")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _valid_time(t) -> bool:
    try:
        return isinstance(t, str) and datetime.fromisoformat(t).tzinfo is not None
    except ValueError:
        return False


def commitment(value, salt: bytes) -> str:
    return hashlib.sha256(salt + json.dumps(value, sort_keys=True).encode()).hexdigest()


def _sha(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True).encode()).hexdigest()


class Vault:
    """Custody-only secret store, persisted encrypted. Never serialized to the ledger."""

    def __init__(self, path: Path | None = None, key: bytes | None = None):
        self.path = Path(path) if path else None
        if self.path is not None and (not isinstance(key, bytes) or len(key) != 32):
            raise GateError("a persisted vault needs a 32-byte key held by custody")
        self._key = key
        self._d = {"decrypt": {}, "linkage": {}, "params": {}, "truth": {}}
        if self.path is not None and self.path.exists():
            blob = self.path.read_bytes()
            try:
                self._d = json.loads(AESGCM(key).decrypt(blob[:12], blob[12:], _AAD))
            except Exception as x:
                raise GateError(f"vault cannot be decrypted or is corrupted: {type(x).__name__}")

    def _save(self):
        if self.path is None:
            return
        n = os.urandom(12)
        blob = n + AESGCM(self._key).encrypt(n, json.dumps(self._d, sort_keys=True).encode(), _AAD)
        fd, tmp = tempfile.mkstemp(dir=self.path.parent, prefix=self.path.name + ".tmp-")
        try:
            with os.fdopen(fd, "wb") as fh:
                fh.write(blob); fh.flush(); os.fsync(fh.fileno())
            os.replace(tmp, self.path)
            _fsync_dir(self.path.parent)                    # durable rename (R2-2)
        except BaseException:
            if os.path.exists(tmp):
                os.unlink(tmp)
            raise

    def ciphertext_sha256(self) -> str | None:
        return hashlib.sha256(self.path.read_bytes()).hexdigest() if self.path and self.path.exists() else None

    def set_params(self, family: str, *, c: float, a: float, b: float, m: float) -> str:
        """Adds a parameter set (history kept; never overwritten). Returns its commitment."""
        for k, v in (("c", c), ("a", a), ("b", b), ("m", m)):
            if not finite_real(v):
                raise GateError(f"parameter {k} must be a finite real number (bool / NaN / inf refused, S3-02)")
        if not a > 0:
            raise GateError("a > 0 is required (س 208)")
        if not m > 0:
            raise GateError("m must be positive")
        salt = os.urandom(16)
        v = {"c": c, "a": a, "b": b, "m": m}
        com = commitment(v, salt)
        self._d["params"].setdefault(family, {})[com] = {**v, "salt": salt.hex()}
        self._save()
        return com

    def has_commitment(self, family: str, com: str) -> bool:
        return com in self._d["params"].get(family, {})

    def params(self, family: str, com: str) -> dict:
        p = self._d["params"][family][com]
        return {k: p[k] for k in ("c", "a", "b", "m")}

    def recompute(self, family: str, com: str) -> bool:
        p = self._d["params"].get(family, {}).get(com)
        return p is not None and commitment({k: p[k] for k in ("c", "a", "b", "m")}, bytes.fromhex(p["salt"])) == com

    def add_symbol(self, symbol: str, real) -> None:
        if symbol in self._d["decrypt"]:
            raise GateError("symbol already mapped")
        self._d["decrypt"][symbol] = real
        self._save()

    def store_truth(self, family: str, truth) -> None:
        if family in self._d["truth"]:
            raise GateError("hidden truth already stored for this family")
        self._d["truth"][family] = truth
        self._save()

    def _lookup(self, item: str):
        if item.startswith("truth:"):
            return self._d["truth"].get(item[6:], _MISSING)
        if item.startswith("symbol:"):
            return self._d["decrypt"].get(item[7:], _MISSING)
        return _MISSING


_MISSING = object()


def _fsync_dir(d: Path) -> None:
    """fsync the parent folder so the rename survives power loss (POSIX). On platforms that cannot
    open a directory (Windows), os.replace is used and this is a documented no-op."""
    try:
        fd = os.open(d, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    except OSError:
        return
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def load_key(key_path, *, vault_path, ledger_path=None) -> bytes:
    """Read the 32-byte vault key from a custody-only file (R2-3; policy docs/CUSTODY_KEY_POLICY.md).
    Refused if the key sits in the vault's or the ledger's folder, if it is not exactly 32 bytes,
    or (POSIX) if group/other have any permission on it."""
    kp = Path(key_path).resolve()
    for other in (vault_path, ledger_path):
        if other is not None and kp.parent == Path(other).resolve().parent:
            raise GateError("the vault key must not sit in the vault's or the ledger's folder")
    if os.name == "posix" and kp.stat().st_mode & 0o077:
        raise GateError("the vault key file must be readable by its owner only (chmod 600)")
    key = kp.read_bytes()
    if len(key) != 32:
        raise GateError("the vault key must be exactly 32 bytes")
    return key


class CustodyLayer:
    KINDS = ("role_assigned", "custody_decision", "params_fixed", "epoch_boundary_declared",
             "params_rotated", "access_logged", "submissions_sealed", "z_output_passed", "vault_verified",
             "vault_attested")

    def __init__(self, vault: Vault | None, *, identity: str | None = None, key=None):
        """vault=None -> observer mode (validate/rebuild only). identity/key: the custody signer."""
        self.vault, self.identity, self._key = vault, identity, key
        self.roles: dict[str, set] = {}
        self.decisions: dict[str, dict] = {}
        self.families: dict[str, dict] = {}
        self.epochs: set = set()
        self.sealed: dict[str, str] = {}
        self.passed: set = set()
        self.access_log: list = []
        self.req_nonces: set = set()
        self.vault_checks: dict = {}               # check_id -> custody statement
        self.attestations: dict = {}               # check_id -> auditor statement
        self.g = None

    def bind(self, g):
        self.g = g
        led = getattr(g.ledger, "_path", None)
        if self.vault is not None and self.vault.path is not None and led is not None:
            if self.vault.path.resolve().parent == Path(led).resolve().parent:
                raise GateError("the vault must live outside the ledger folder")

    # ---------------- helpers ----------------
    def holders(self, role: str) -> list:
        return [h for h, rs in self.roles.items() if role in rs]

    def _signed_by_role(self, p, role, action):
        signer = Signed.from_payload(p).identity
        if role not in self.roles.get(signer, set()):
            raise GateError(f"{signer!r} does not hold the role {role!r}")
        return self.g._signed(p, signer, action)

    def _opened(self, slice_id) -> bool:
        cc = next((x for x in self.g._ext.values() if hasattr(x, "openings")), None)
        return bool(cc) and any(sl == slice_id for (_, sl) in cc.openings)

    def _derive(self, requester: str, item: str):
        """Track and permission from ledger state only. Returns (track, allowed)."""
        rs = self.roles.get(requester, set())
        if item.startswith("truth:"):
            fam = item[6:]
            ok = "court_operator" in rs and fam in self.sealed
            return ("after_seal" if ok else "none"), ok
        if item.startswith("symbol:"):
            if "gz_operator" in rs:
                return "G-Z", True
            return "none", False
        return "none", False

    def _verify_request(self, req_payload) -> dict:
        s = Signed.from_payload(req_payload)
        st = self.g._signed(req_payload, s.identity, "access_request")
        if st["nonce"] in self.req_nonces:
            raise AuthError("replayed request nonce")
        for k in ("item", "reason", "time"):
            if not st.get(k):
                raise AuthError(f"request missing {k!r}")
        return {**st, "identity": s.identity}

    def _vault_needed(self, family, com):
        if self.vault is not None and not self.vault.has_commitment(family, com):
            raise GateError("the vault holds no parameter set with this commitment for this family")

    # ---------------- cross-component precondition ----------------
    def pre_validate(self, kind, p):
        if kind == "claim_opened" and p.get("slice") not in self.decisions:
            raise GateError("custody decision for this slice (boundaries, Δ, m) must be recorded BEFORE opening (م-03)")

    # ---------------- validation ----------------
    def validate(self, kind, p):
        if kind == "role_assigned":
            st = self.g._signed(p, "founder", "assign_role")
            role, holder = st.get("role"), st.get("holder")
            if role not in ROLES:
                raise GateError("unknown role")
            if holder not in self.g.keys() or holder == "founder":
                raise GateError("holder must be a registered identity other than the founder")
            have = self.roles.get(holder, set())
            if role in SEPARATED and any(r in SEPARATED and r != role for r in have):
                raise GateError("role separation (§13 #2)")
            if role == "reid_checker" and have & set(CHECKER_EXCLUDES):
                raise GateError("re-identification checker must be independent (D-02, §26 B)")
            if role in CHECKER_EXCLUDES and "reid_checker" in have:
                raise GateError("re-identification checker must be independent (D-02, §26 B)")
            if role == "custody" and self.holders("custody"):
                raise GateError("custody already assigned")
        elif kind == "custody_decision":
            st = self._signed_by_role(p, "custody", "custody_decision")
            if st.get("slice") in self.decisions:
                raise GateError("custody decision already recorded for this slice")
            fam = self.families.get(st.get("family"))
            if fam is None:
                raise GateError("parameters must be fixed for the family first")
            if st.get("delta") != fam["delta"] or st.get("params_commitment") != fam["commitment"]:
                raise GateError("parameters are fixed across the family's slices (س 258)")
            if not str(st.get("boundaries", "")).strip():
                raise GateError("slice boundaries must be recorded")
        elif kind in ("params_fixed", "params_rotated"):
            st = self._signed_by_role(p, "custody", kind)
            if not (isinstance(st.get("delta"), (int, float)) and not isinstance(st["delta"], bool) and st["delta"] > 0):
                raise GateError("Δ must be positive")
            com = st.get("params_commitment")
            if not (isinstance(com, str) and _HEX64.fullmatch(com)):
                raise GateError("commitment must be 64 lowercase hex")
            self._vault_needed(st.get("family"), com)
            fam = self.families.get(st.get("family"))
            if kind == "params_fixed":
                if fam is not None:
                    raise GateError("parameters already fixed for this family; rotation needs an epoch boundary")
            else:
                if fam is None:
                    raise GateError("unknown family")
                if com == fam["commitment"]:
                    raise GateError("rotation must change the parameter set")
                if st.get("epoch") not in self.epochs or st.get("epoch") == fam.get("epoch"):
                    raise GateError("rotation only at a NEW epoch boundary declared in advance by the founder (س 260, ق-02)")
                if any(d["family"] == st["family"] and d.get("params_commitment") == fam["commitment"]
                       and self._opened(sl) for sl, d in self.decisions.items()):
                    raise GateError("rotation refused: claims are open under the current parameters (س 261; ruled F-3)")
        elif kind == "epoch_boundary_declared":
            st = self.g._signed(p, "founder", "declare_epoch_boundary")
            if st.get("epoch") in self.epochs:
                raise GateError("epoch boundary already declared")
        elif kind == "access_logged":
            st = self._signed_by_role(p, "custody", "access_log")
            for k in ACCESS_FIELDS:
                if k not in st:
                    raise GateError(f"access record missing {k!r} (م7-10 #3)")
            if st["executor"] != Signed.from_payload(p).identity:
                raise GateError("executor must be the signing custody holder")
            if st["track"] not in TRACKS or st["outcome"] not in ("ok", "refused") or not _valid_time(st["time"]):
                raise GateError("invalid track / outcome / time in access record")
            if not str(st["reason"]).strip() or not str(st["item"]).strip():
                raise GateError("access record needs item and reason")
            if st["request_sha256"] != _sha(st["request"]):
                raise GateError("request hash mismatch")
            if st["outcome"] == "refused":
                if st["returned"] != "none":
                    raise GateError("a refusal returns nothing")
            else:
                if not (isinstance(st["returned"], str) and st["returned"].startswith("sha256:") and _HEX64.fullmatch(st["returned"][7:])):
                    raise GateError("ok record must carry the output hash only")
                rq = self._verify_request(st["request"])           # re-verified, not trusted
                track, allowed = self._derive(rq["identity"], rq["item"])
                if not (allowed and st["authenticated"] is True and st["requester"] == rq["identity"]
                        and st["item"] == rq["item"] and st["track"] == track):
                    raise GateError("ok access record not justified by an authenticated, permitted request")
        elif kind == "submissions_sealed":
            st = self._signed_by_role(p, "court_operator", "seal_submissions")
            if st.get("family") in self.sealed:
                raise GateError("already sealed")
            h = st.get("submissions_sha256", "")
            if not (isinstance(h, str) and _HEX64.fullmatch(h)):
                raise GateError("seal needs the submissions hash")
        elif kind == "z_output_passed":
            st = self._signed_by_role(p, "custody", "z_output_passed")
            rv = st.get("reviewed")
            if not isinstance(rv, list) or any(not isinstance(x, str) for x in rv) or set(rv) != set(LEAK_SCOPE):
                raise GateError("leak review must cover the full scope (س 277–282)")
        elif kind == "vault_verified":
            st = self._signed_by_role(p, "custody", "vault_verified")
            if st.get("result") not in ("ok", "failed"):
                raise GateError("vault check result must be ok or failed")
            if not st.get("check_id") or st["check_id"] in self.vault_checks:
                raise GateError("vault check needs a new check_id")
            h = st.get("vault_ciphertext_sha256")
            if not (isinstance(h, str) and _HEX64.fullmatch(h)):
                raise GateError("vault check must record the vault ciphertext sha256")
            if sorted(st.get("commitments", [])) != sorted(
                    [f"{f}:{c}" for f, d in self.families.items() for c in d["history"]]):
                raise GateError("vault check must cover every commitment recorded in the ledger")
        elif kind == "vault_attested":                     # D-3: independent witness, no key, no contents
            st = self._signed_by_role(p, "custody_auditor", "vault_attested")
            chk = self.vault_checks.get(st.get("check_id"))
            if chk is None:
                raise GateError("attestation must reference a recorded vault check")
            if st["check_id"] in self.attestations:
                raise GateError("vault check already attested")
            if st.get("verdict") not in ("concur", "dissent"):
                raise GateError("verdict must be concur or dissent")
            if st["verdict"] == "concur" and (
                    st.get("observed_ciphertext_sha256") != chk["vault_ciphertext_sha256"]
                    or st.get("custody_statement_sha256") != _sha(chk) or chk["result"] != "ok"):
                raise GateError("concurrence must match the custody record and the ciphertext the auditor observed")
            if st["verdict"] == "dissent" and not str(st.get("reason", "")).strip():
                raise GateError("a dissent needs a reason")

    def apply(self, kind, p):
        st = json.loads(bytes.fromhex(p["statement_hex"]))
        if kind == "role_assigned":
            self.roles.setdefault(st["holder"], set()).add(st["role"])
        elif kind == "custody_decision":
            self.decisions[st["slice"]] = st
        elif kind == "params_fixed":
            self.families[st["family"]] = {"commitment": st["params_commitment"], "delta": st["delta"],
                                           "epoch": st.get("epoch"), "history": [st["params_commitment"]]}
        elif kind == "epoch_boundary_declared":
            self.epochs.add(st["epoch"])
        elif kind == "params_rotated":
            f = self.families[st["family"]]
            self.families[st["family"]] = {"commitment": st["params_commitment"], "delta": st["delta"],
                                           "epoch": st["epoch"], "history": f["history"] + [st["params_commitment"]]}
        elif kind == "access_logged":
            self.access_log.append(st)
            if st["authenticated"]:
                self.req_nonces.add(json.loads(bytes.fromhex(st["request"]["statement_hex"]))["nonce"])
        elif kind == "submissions_sealed":
            self.sealed[st["family"]] = st["submissions_sha256"]
        elif kind == "z_output_passed":
            if st.get("passed"):
                self.passed.add(st["output_sha256"])
        elif kind == "vault_verified":
            self.vault_checks[st["check_id"]] = st
        elif kind == "vault_attested":
            self.attestations[st["check_id"]] = st

    # ---------------- API ----------------
    def commit(self, kind, s):
        return self.g._commit(kind, s.to_payload())

    def _csign(self, statement: dict) -> Signed:
        if self._key is None or self.identity is None:
            raise GateError("this custody layer holds no custody signing key")
        return sign(self.identity, self._key, {**statement, "nonce": uuid.uuid4().hex})

    def access(self, request: Signed):
        """The only path to secrets. request: Signed by the requester, action 'access_request'."""
        if self.vault is None:
            raise GateError("observer mode: no vault")
        rp = request.to_payload()
        rec = {"action": "access_log", "executor": self.identity, "request": rp, "request_sha256": _sha(rp),
               "time": _now()}
        try:
            rq = self._verify_request(rp)
        except (AuthError, GateError) as x:
            rec.update(requester=request.identity, item="unverified", track="none", reason=f"unauthenticated: {x}",
                       outcome="refused", returned="none", authenticated=False)
            self.commit("access_logged", self._csign(rec))
            raise GateError(f"request not authenticated; refused and logged ({x})")
        track, allowed = self._derive(rq["identity"], rq["item"])
        value = self.vault._lookup(rq["item"]) if allowed else _MISSING
        rec.update(requester=rq["identity"], item=rq["item"], track=track, reason=rq["reason"], authenticated=True)
        if value is _MISSING:
            rec.update(outcome="refused", returned="none")
            self.commit("access_logged", self._csign(rec))
            raise GateError("decryption only in G-Z or after the seal (س 355); hidden truth only to the court "
                            "operator after sealing (م7-01); refused and logged")
        rec.update(outcome="ok", returned="sha256:" + _sha(value))
        self.commit("access_logged", self._csign(rec))
        return value

    def verify_vault(self) -> dict:
        """Recompute every commitment the ledger recorded from the vault's (params, salt)."""
        if self.vault is None:
            raise GateError("observer mode: no vault")
        bad = [(f, c) for f, d in self.families.items() for c in d["history"] if not self.vault.recompute(f, c)]
        res = {"result": "failed" if bad else "ok", "check_id": uuid.uuid4().hex,
               "commitments": sorted(f"{f}:{c}" for f, d in self.families.items() for c in d["history"]),
               "mismatches": len(bad), "vault_ciphertext_sha256": self.vault.ciphertext_sha256() or "0" * 64,
               "time": _now()}
        self.commit("vault_verified", self._csign({"action": "vault_verified", **res}))
        if bad:
            raise GateError(f"vault integrity check failed for {len(bad)} commitment(s)")
        return res

    def commitments_attested(self) -> bool:
        """True only if the LATEST custody check is ok, covers the current commitments, and the custody
        auditor concurred on it (D-3: two signatures, verifiable from the ledger)."""
        if not self.vault_checks:
            return False
        last = list(self.vault_checks.values())[-1]
        cur = sorted(f"{f}:{c}" for f, d in self.families.items() for c in d["history"])
        a = self.attestations.get(last["check_id"])
        return last["result"] == "ok" and last["commitments"] == cur and bool(a) and a["verdict"] == "concur"

    def export_from_z(self, output: bytes) -> bytes:
        if hashlib.sha256(output).hexdigest() not in self.passed:
            raise GateError("output has not passed custody review; it does not leave Z (س 284)")
        return output

    @staticmethod
    def release_gz_to_language_minds(*_a, **_k):
        if GZ_RELEASE_LOCKED:
            raise GateError("G-Z release to language minds is LOCKED: CS-01-04 (announced threshold) open and "
                            "م5-20 not validated (§26 غ-03)")


def attest(cl: "CustodyLayer", identity: str, key, check_id: str, vault_path, *, reason: str = "") -> Signed:
    """Custody auditor's witness statement. The auditor hashes the vault CIPHERTEXT file itself (no key,
    no contents) and compares it, and the custody statement hash, with the ledger record."""
    chk = cl.vault_checks[check_id]
    observed = hashlib.sha256(Path(vault_path).read_bytes()).hexdigest()
    ok = observed == chk["vault_ciphertext_sha256"] and chk["result"] == "ok"
    st = {"action": "vault_attested", "check_id": check_id, "observed_ciphertext_sha256": observed,
          "custody_statement_sha256": _sha(chk), "verdict": "concur" if ok else "dissent",
          "reason": reason or ("" if ok else "ciphertext hash or result does not match"), "time": _now(),
          "nonce": uuid.uuid4().hex}
    return sign(identity, key, st)


def request(identity: str, key, item: str, reason: str, family: str | None = None) -> Signed:
    return sign(identity, key, {"action": "access_request", "item": item, "family": family, "reason": reason,
                                "time": _now(), "nonce": uuid.uuid4().hex})


def zero_prior_state(*, llm_in_lineage: bool, unauthorized_decryption: bool, reid_failed: bool,
                     reid_within_announced_threshold: bool | None) -> str:
    """Mechanical state from lineage (س 172, 217–221). None = threshold undecided (CS-01-04)."""
    if reid_failed or unauthorized_decryption:
        return "Z with blinding breach"
    if llm_in_lineage:
        return "Z with linguistic contribution: zero knowledge unverifiable"
    if reid_within_announced_threshold is True:
        return "Z-computational"
    return "undetermined: announced threshold (CS-01-04) open"
