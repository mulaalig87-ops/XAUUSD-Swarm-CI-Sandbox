"""Layer 9 — deterministic court (WP8-04; spec WP7-01 §2.9, WP7-05 §1–§6, TP-08).

Source text: «كود حتمي، وقواعد مجمدة، وثلاثة أحكام» ⟨س 1551⟩; the three rulings are existence,
size with uncertainty, importance; «ولا عتبة تُخترع بعد النتيجة» ⟨س 329⟩. Thresholds: owner ✓
before start; court ✗ (س 774–776). Exercised by the court operator alone, by code alone (م7-03),
appointed by the founder before the first run (ق-04), and the package fields are not shown to the
operator (ق-22).

What this module enforces
- Identities (TP-08 b; س 727–728, 2347, 2369): a Test Instance is registered, founder-signed, with
  its parent Claim ID, statistic, procedure, null, slice, seeds, code version, Representation ID,
  transform version and price series (Bid/Ask/Mid/trade; س 738–739). Its link to a registered Claim
  ID is mandatory; a record without it is refused. A claim may carry identity fields (س 727); a
  second claim with the same identity fields under another ID is refused («ولا ميزانية جديدة
  بتغيير الاسم» س 606, CS-05-04 (ب)).
- Pre-registration (TP-08 c; س 699, 703, 743): a test instance registered after the claim was
  opened is DESCRIPTIVE only; it never enters the confirmatory ruling. Exactly one primary instance
  per (claim, path) decides (س 700–702); a pre-registered aggregation procedure is NOT implemented
  and is refused.
- Frozen court rules per claim family (founder, before start): family structure A (one batch
  family, α_total) or B (α_i per path, Σα_i ≤ α_total; س 660–661, 583), error measure, procedure
  with its documented validity reason (س 682); no importance rule (W-2). Freezing happens before
  any claim of the family is opened (pre_validate on claim_opened); a second freeze is refused, so
  the operator (or anyone) cannot change a threshold after start (TP-08 d).
- Paths for accounting: Z, G-Z, R only (CS-05-06).
- Inputs: the sealed package; its SHA-256 must equal the custody seal of that family (س 2196, ق-27)
  and custody must have recorded its full-scope passage (س 254, 284). The package must contain
  EXACTLY the family's pre-registered primary instances (R1-1): missing ones are refused (no
  pre-registered missing-data rule exists); instances of other families are refused, membership
  being derived from the ledger (openings → custody decisions), not from the package (R1-2).
- Numeric checks: p in [0,1]; p, estimate, CI finite reals (bool/NaN/Inf refused); lo ≤ est ≤ hi.
- Every claim of the family appears with a status for each path Z/G-Z/R (R1-8).
- The test instance's price series must equal the claim identity's (R1-5).
- Release hash: manifest of every module that builds or validates the state (R1-7).
- Every replica requires a custody attestation binding the ruling to (family, package, output,
  scope, frozen config, code release, operator request); the custody replica also RECOMPUTES each
  ruling from the sealed package, so a self-consistent but forged output is refused.
- Determinism (WP8-04 acceptance): the ruling is a pure function of (package bytes, frozen config,
  registry, scope, code); output is canonical JSON with its SHA-256; the custody service's
  reproduce() reruns and compares.
- Claims with no accepted null do not enter confirmation and carry the unified-reading status
  «لم يُختبر تأكيديًا لعدم توفر نموذج صفري (Null) صالح» (مك-128, س 38).
- Per claim: one row with each path's rulings; «مؤكد» if rejected in at least one path; divergence
  shown (س 686–689).

Round 3 (R2 review)
- Freezing is BLOCKED until a founder-signed court_policy_decided for the family records the formal
  A/B (س 2333) and FWER/FDR (س 610) decision, citing its register entry and register version hash;
  the frozen config must follow it. Holm/FWER stays the only implemented procedure ([مبدئي] س 611);
  a decision for FDR therefore cannot be frozen (no FDR procedure is built).
- Importance: no rule exists in the sources; the optional rule was REMOVED (W-2, Q-1). Every ruling
  carries «غير محدد: قاعدة الأهمية لم تُجمَّد»; a config with any importance key is refused.
- Isolation (R2-3/R2-6): CourtLayer holds no store and no key. Execution runs in the custody
  service (court_service.py), which alone holds the encrypted PackageStore; the operator sends a
  signed run request and records the output; every replica verifies the custody attestation and
  the custody replica recomputes.
- Numbers: finite reals only; bool, NaN, Inf and integers too large for float are refused with
  GateError.

OPEN / NOT IMPLEMENTED (flagged, not invented)
- FDR procedures; lifetime error control (س 612: control is declared per batch).
- Who freezes the plan is «غير معرّف في المعمارية» (WP7-05 §6.4): founder signature as a documented
  transitional ruling (W-3).
"""
from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from .charter import GateError
from .identity import Signed
from .numeric import finite_real

_HEX64 = __import__("re").compile(r"[0-9a-f]{64}")

PATHS = ("Z", "G-Z", "R")
CONFIG_KEYS = {"structure", "alpha_total", "alpha_by_path", "error_measure", "procedure", "validity_reason"}
PRICE_SERIES = ("Bid", "Ask", "Mid", "trade")
TI_FIELDS = ("test_instance_id", "claim_id", "statistic", "procedure", "null", "slice", "seeds",
             "code_version", "representation_id", "transform_version", "price_series", "path", "role",
             "null_card_accepted")
CLAIM_IDENTITY_FIELDS = ("target_quantity", "eligible_data_scope", "time_scope_type", "proof_path",
                         "direction_or_threshold", "observation_precision", "price_series")    # س 727
NO_NULL_STATUS = "لم يُختبر تأكيديًا لعدم توفر نموذج صفري (Null) صالح"
IMPORTANCE_UNDEFINED = "غير محدد: قاعدة الأهمية لم تُجمَّد"
_RELEASE_FILES = ("charter.py", "claims.py", "court.py", "court_service.py", "custody.py", "identity.py", "ledger.py")


def _manifest() -> dict:
    """EOL-normalized SHA-256 of every module whose code builds, validates or rebuilds the state the
    ruling depends on (R1-7). The court release hash is the hash of this manifest."""
    d = Path(__file__).parent
    return {f: hashlib.sha256((d / f).read_bytes().replace(b"\r\n", b"\n")).hexdigest() for f in _RELEASE_FILES}


CODE_MANIFEST = _manifest()
CODE_SHA256 = hashlib.sha256(json.dumps(CODE_MANIFEST, sort_keys=True).encode()).hexdigest()


def canon(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode()


def sha(obj) -> str:
    return hashlib.sha256(canon(obj)).hexdigest()


def holm(pvals: list[tuple[str, float]], alpha: float) -> dict:
    """Holm step-down, FWER (valid under any dependence, س 681). Deterministic order: (p, id)."""
    order = sorted(pvals, key=lambda t: (t[1], t[0]))
    m, out, stop = len(order), {}, False
    for k, (tid, p) in enumerate(order):
        if not stop and p <= alpha / (m - k):
            out[tid] = "rejected"
        else:
            stop = True
            out[tid] = "not_rejected"
    return out


def _num(x) -> bool:
    """Finite real, not bool; huge ints are refused (no OverflowError leaks)."""
    return finite_real(x)


def _check_submission(s) -> None:
    if not isinstance(s, dict) or set(s) != {"test_instance_id", "p_value", "estimate", "ci"}:
        raise GateError("submission must hold exactly test_instance_id, p_value, estimate, ci")
    if not (_num(s["p_value"]) and 0 <= s["p_value"] <= 1):
        raise GateError("p_value must be a finite real number in [0, 1]")
    if not _num(s["estimate"]):
        raise GateError("estimate must be a finite real number")
    ci = s["ci"]
    if not (isinstance(ci, list) and len(ci) == 2 and all(_num(v) for v in ci)):
        raise GateError("ci must be a list of two finite real numbers")
    if not ci[0] <= ci[1]:
        raise GateError("ci lower bound must not exceed the upper bound")
    if not ci[0] <= s["estimate"] <= ci[1]:
        raise GateError("estimate must lie inside its interval")


def eligible(ti: dict) -> bool:
    """Pre-registered primary instance that decides (س 700–703, 2271)."""
    return ti["role"] == "primary" and not ti["descriptive"] and not ti.get("code_integrity_only")


def compute(package: dict, config: dict, instances: dict, scope: dict) -> dict:
    """Pure function of (package, frozen config, registered instances, family scope from the ledger).
    scope = {"family", "claims": [claim ids opened in this family], "slice_family": {slice: family}}."""
    fam = scope["family"]
    if not isinstance(package, dict) or package.get("family") != fam or not isinstance(package.get("submissions"), list):
        raise GateError("package must be {family, submissions[]} for the requested family")
    for s in package["submissions"]:
        _check_submission(s)
    subs = {s["test_instance_id"]: s for s in package["submissions"]}
    if len(subs) != len(package["submissions"]):
        raise GateError("duplicate test instance in the package")
    unknown = sorted(set(subs) - set(instances))
    if unknown:
        raise GateError(f"package holds unregistered test instances: {unknown}")
    claims_in = set(scope["claims"])
    foreign = sorted(t for t in subs if instances[t]["claim_id"] not in claims_in
                     or scope["slice_family"].get(instances[t]["slice"]) != fam)
    if foreign:
        raise GateError(f"submissions outside this claim family (by ledger, not by package field): {foreign}")
    expected = sorted(t for t, ti in instances.items() if ti["claim_id"] in claims_in and eligible(ti))
    bad_slice = [t for t in expected if scope["slice_family"].get(instances[t]["slice"]) != fam]
    if bad_slice:
        raise GateError(f"registered primary instances whose slice is not in this family: {bad_slice}")
    missing = sorted(set(expected) - set(subs))
    if missing:                                   # R1-1: no pre-registered rule allows a missing instance
        raise GateError(f"package lacks pre-registered primary instances {missing}; incomplete batches are refused "
                        "(no pre-registered missing-data rule exists)")
    confirm, descriptive, untested = {}, [], {}
    for tid in sorted(subs):
        ti = instances[tid]
        if not eligible(ti):
            descriptive.append(tid)
        elif not ti["null_card_accepted"]:
            untested[tid] = NO_NULL_STATUS
        else:
            confirm[tid] = ti
    if config["structure"] == "A":
        dec = holm([(t, subs[t]["p_value"]) for t in confirm], config["alpha_total"])
    else:
        dec = {}
        for path in PATHS:
            ts = [t for t in confirm if confirm[t]["path"] == path]
            if ts:
                if path not in config["alpha_by_path"]:
                    raise GateError(f"no frozen α for path {path}")
                dec.update(holm([(t, subs[t]["p_value"]) for t in ts], config["alpha_by_path"][path]))

    claims: dict = {c: {"paths": {}} for c in sorted(claims_in)}
    for tid in sorted(set(confirm) | set(untested)):
        ti, s = instances[tid], subs[tid]
        row = claims[ti["claim_id"]]
        if tid in untested:
            row["paths"][ti["path"]] = {"test_instance_id": tid, "status": untested[tid]}
        else:
            row["paths"][ti["path"]] = {"test_instance_id": tid, "existence": dec[tid],
                                        "size": {"estimate": s["estimate"], "ci": list(s["ci"])},
                                        "importance": IMPORTANCE_UNDEFINED}       # W-2: no rule
    for cid, row in claims.items():
        ex = [v.get("existence") for v in row["paths"].values() if "existence" in v]
        row["confirmed"] = "rejected" in ex                                  # س 687
        row["divergent"] = len(set(ex)) > 1                                  # س 688
        row["path_status"] = {pa: ("ruled" if "existence" in row["paths"].get(pa, {}) else
                                   "not_tested_no_accepted_null" if pa in row["paths"] else
                                   "no_primary_instance_registered") for pa in PATHS}     # R1-8
    return {"family": fam, "config_sha256": sha(config), "scope_sha256": sha(scope), "error_control": "FWER per batch",
            "claims": claims, "descriptive_only": descriptive, "denominators": _denoms(config, confirm),
            "code_sha256": CODE_SHA256}


def _denoms(config, confirm) -> dict:
    if config["structure"] == "A":
        return {"A": len(confirm)}
    return {pa: sum(1 for t in confirm.values() if t["path"] == pa) for pa in PATHS}


class PackageStore:
    """Custody-held store of sealed submission packages (R1-3, W-6).

    «كل مخرج من Z يمر على جهة الحفظ قبل أن يصل إلى أي طرف آخر» ⟨س 254⟩; «كلها تمر على جهة الحفظ قبل
    خروجها من Z» ⟨س 284⟩. Submissions are Z outputs, so: the store belongs to CUSTODY; it is encrypted
    at rest (AES-256-GCM, AAD = content hash) with a 32-byte custody key (policy: CUSTODY_KEY_POLICY.md);
    files are named by the plaintext SHA-256; a package is admitted only after custody recorded its
    full-scope passage (z_output_passed). The court operator's API (CourtLayer.run) takes a family
    name only and never receives package bytes; it receives the ruling (code output). Reading needs
    the key, which the operator does not hold. Limit (as for the vault): an OS account that can read
    both the key and the store can read the packages."""

    def __init__(self, path: Path | None = None, key: bytes | None = None):
        if not (isinstance(key, bytes) and len(key) == 32):
            raise GateError("the package store needs the 32-byte custody key")
        self.path, self._key, self._mem = (Path(path) if path else None), key, {}

    def _enc(self, h, data):
        n = os.urandom(12)
        return n + AESGCM(self._key).encrypt(n, data, h.encode())

    def _dec(self, h, blob):
        try:
            data = AESGCM(self._key).decrypt(blob[:12], blob[12:], h.encode())
        except Exception:
            raise GateError("package store: cannot decrypt (wrong key or corrupted)")
        if hashlib.sha256(data).hexdigest() != h:
            raise GateError("package store corrupted: content does not match its hash")
        return data

    def put(self, data: bytes) -> str:
        h = hashlib.sha256(data).hexdigest()
        blob = self._enc(h, data)
        if self.path is None:
            self._mem.setdefault(h, blob)
            return h
        f = self.path / h
        if not f.exists():
            tmp = self.path / (h + ".tmp")
            with open(tmp, "wb") as fh:
                fh.write(blob); fh.flush(); os.fsync(fh.fileno())
            os.replace(tmp, f)
        return h

    def get(self, h: str) -> bytes | None:
        blob = self._mem.get(h) if self.path is None else ((self.path / h).read_bytes() if (self.path / h).exists() else None)
        return None if blob is None else self._dec(h, blob)

    def has(self, h: str) -> bool:
        return h in self._mem if self.path is None else (self.path / h).exists()


class CourtLayer:
    KINDS = ("claim_identity_registered", "test_instance_registered", "court_policy_decided", "court_frozen",
             "court_ruling")

    def __init__(self, custody_store: PackageStore | None = None):
        """Court-side replicas are built WITHOUT a store (default): they verify signatures, the custody
        attestation, hashes and scope. Only the custody service's own replica passes custody_store, and
        then additionally recomputes every ruling (R2-3)."""
        self._store = custody_store
        self.policies: dict = {}
        self.req_nonces: set = set()
        self.att_nonces: set = set()
        self.identities: dict = {}       # claim_id -> identity sha
        self.claim_series: dict = {}     # claim_id -> price series
        self.instances: dict = {}        # tid -> statement (+descriptive)
        self.configs: dict = {}          # family -> config
        self.rulings: dict = {}          # ruling_id -> statement
        self.g = None

    def bind(self, g):
        self.g = g

    def _ext(self, attr):
        return next((x for x in self.g._ext.values() if hasattr(x, attr)), None)

    def _family_of_slice(self, sl):
        cu = self._ext("decisions")
        d = cu.decisions.get(sl) if cu else None
        return d["family"] if d else None

    def _opened(self, claim_id) -> bool:
        cc = self._ext("openings")
        return any(c == claim_id for (c, _) in cc.openings)

    def pre_validate(self, kind, p):
        if kind == "claim_opened":
            fam = self._family_of_slice(p.get("slice"))
            if fam not in self.configs:
                raise GateError("court rules and thresholds for this claim family must be frozen BEFORE opening (س 774; WP7-05 §6)")

    def validate(self, kind, p):
        cc = self._ext("cards")
        if kind == "claim_identity_registered":
            st = self.g._signed(p, "founder", "register_claim_identity")
            cid = st.get("claim_id")
            if cc is None or cid not in cc.cards:
                raise GateError("claim must be registered in the claims charter first")
            if cid in self.identities:
                raise GateError("claim identity already registered")
            ident = st.get("identity", {})
            if set(ident) != set(CLAIM_IDENTITY_FIELDS) or any(ident[k] in (None, "") for k in CLAIM_IDENTITY_FIELDS
                                                               if k != "observation_precision"):
                raise GateError("claim identity needs every field of س 727 (observation_precision may be 'n/a')")
            if ident["price_series"] not in PRICE_SERIES:
                raise GateError("price series must be named: Bid, Ask, Mid or trade (س 738–739)")
            if sha(ident) in self.identities.values():
                raise GateError("same identity under another Claim ID: no new budget by renaming (س 606)")
        elif kind == "test_instance_registered":
            st = self.g._signed(p, "founder", "register_test_instance")
            if any(k not in st for k in TI_FIELDS) or any(st[k] in (None, "") for k in TI_FIELDS):
                raise GateError("test instance needs every field of س 728 plus path, role, price series")
            if st["test_instance_id"] in self.instances:
                raise GateError("test instance already registered")
            if st["claim_id"] not in self.identities:
                raise GateError("Test Instance ID must link to a registered Claim ID (س 2266)")
            if st["path"] not in PATHS:
                raise GateError("path must be Z, G-Z or R (CS-05-06)")
            if st["price_series"] not in PRICE_SERIES:
                raise GateError("price series must be named (س 738–739)")
            if st["price_series"] != self.claim_series[st["claim_id"]]:
                raise GateError("test instance price series must equal the claim identity's (the series is part of "
                                "the Claim ID, س 727; another series is another claim)")
            if st["role"] not in ("primary", "descriptive"):
                raise GateError("role must be primary or descriptive (aggregation procedure not implemented)")
            if not isinstance(st.get("code_integrity_only", False), bool):
                raise GateError("code_integrity_only must be a boolean")
            if not isinstance(st["null_card_accepted"], bool):
                raise GateError("null_card_accepted is the founder's decision at freezing (ق-06)")
            if st["role"] == "primary" and not self._opened(st["claim_id"]) and any(
                    t["claim_id"] == st["claim_id"] and t["path"] == st["path"] and t["role"] == "primary"
                    and not t["descriptive"] for t in self.instances.values()):
                raise GateError("one primary instance per claim and path (س 700–702)")
        elif kind == "court_policy_decided":            # R2-1/R2-2: the formal decision that unblocks freezing
            st = self.g._signed(p, "founder", "decide_court_policy")
            fam = st.get("family")
            if not fam or fam in self.policies:
                raise GateError("one recorded policy decision per claim family")
            if st.get("structure") not in ("A", "B") or st.get("error_measure") not in ("FWER", "FDR"):
                raise GateError("the decision must name structure A|B (س 2333) and error measure FWER|FDR (س 610)")
            ref, rsha = st.get("register_ref"), st.get("register_sha256")
            if not (isinstance(ref, str) and ref.strip() and isinstance(rsha, str) and _HEX64.fullmatch(rsha)):
                raise GateError("the decision must cite its register entry and the register version hash")
        elif kind == "court_frozen":
            st = self.g._signed(p, "founder", "freeze_court")
            fam = st.get("family")
            if fam in self.configs:
                raise GateError("court rules already frozen for this family; thresholds cannot change (س 329, 774)")
            pol = self.policies.get(fam)
            if pol is None:
                raise GateError("freezing is blocked until A/B and FWER/FDR are formally decided for this family "
                                "(WP7-05 §2: س 2333, س 610)")
            cfg = st.get("config", {})
            if not isinstance(cfg, dict) or set(cfg) - CONFIG_KEYS:
                raise GateError(f"config keys must be within {sorted(CONFIG_KEYS)} (no importance rule: W-2)")
            if cfg.get("structure") != pol["structure"] or cfg.get("error_measure") != pol["error_measure"]:
                raise GateError("config must follow the recorded policy decision")
            if cfg["error_measure"] != "FWER" or cfg.get("procedure") != "holm":
                raise GateError("only Holm/FWER is implemented ([مبدئي] س 611); FDR procedures are not built")
            if not str(cfg.get("validity_reason", "")).strip():
                raise GateError("no procedure without its documented validity reason (س 682)")
            a = cfg.get("alpha_total")
            if not (_num(a) and 0 < a < 1):
                raise GateError("alpha_total must be a finite real in (0, 1)")
            if cfg["structure"] == "B":
                ab = cfg.get("alpha_by_path")
                if not (isinstance(ab, dict) and ab and not set(ab) - set(PATHS)
                        and all(_num(v) and 0 < v < 1 for v in ab.values()) and sum(ab.values()) <= a + 1e-12):
                    raise GateError("structure B: α_i per path (Z/G-Z/R) with Σα_i ≤ α_total (س 661)")
            elif "alpha_by_path" in cfg:
                raise GateError("structure A takes alpha_total only")
        elif kind == "court_ruling":
            cu = self._ext("sealed")
            signer = Signed.from_payload(p).identity
            if cu is None or "court_operator" not in cu.roles.get(signer, set()):
                raise GateError("only the appointed court operator runs the court (م7-03, ق-04)")
            st = self.g._signed(p, signer, "court_ruling")
            fam = st.get("family")
            if fam not in self.configs:
                raise GateError("no frozen court rules for this family")
            if cu.sealed.get(fam) != st.get("package_sha256"):
                raise GateError("package must be the sealed submissions of this family (س 2196, ق-27)")
            if st.get("code_sha256") != CODE_SHA256:
                raise GateError("court code version differs from the running code")
            out = st.get("output", {})
            if sha(out) != st.get("output_sha256") or out.get("config_sha256") != sha(self.configs[fam]) \
                    or out.get("code_sha256") != CODE_SHA256 or out.get("family") != fam:
                raise GateError("ruling output does not match its hash, config or code")
            if st.get("ruling_id") in self.rulings:
                raise GateError("ruling id already used")
            if out.get("scope_sha256") != sha(self.scope(fam)):
                raise GateError("ruling scope does not match the claim family recorded in the ledger")
            if st["package_sha256"] not in cu.passed:
                raise GateError("package has not passed custody (س 254, 284)")
            rq = st.get("request", {})
            if Signed.from_payload(rq).identity != signer:
                raise GateError("the run request must come from the operator who records the ruling")
            rqs = self.g._signed(rq, signer, "court_run_request")
            if rqs.get("family") != fam or rqs["nonce"] in self.req_nonces:
                raise GateError("run request does not match this family or was replayed")
            at = st.get("attestation", {})
            aid = Signed.from_payload(at).identity
            if "custody" not in cu.roles.get(aid, set()):
                raise GateError("the computation must be attested by custody, which alone holds the package")
            ats = self.g._signed(at, aid, "court_compute_attest")
            want = {"family": fam, "package_sha256": st["package_sha256"], "output_sha256": st["output_sha256"],
                    "scope_sha256": sha(self.scope(fam)), "config_sha256": sha(self.configs[fam]),
                    "code_sha256": CODE_SHA256, "request_sha256": hashlib.sha256(bytes.fromhex(rq["statement_hex"])).hexdigest()}
            if any(ats.get(k) != v for k, v in want.items()) or ats["nonce"] in self.att_nonces:
                raise GateError("custody attestation does not match this ruling")
            if self._store is not None:                         # custody replica: recompute
                data = self._store.get(st["package_sha256"])
                if data is None:
                    raise GateError("sealed package not in the package store; ruling cannot be recomputed")
                if sha(compute(json.loads(data), self.configs[fam], self.instances, self.scope(fam))) != st["output_sha256"]:
                    raise GateError("ruling output is not the output of the frozen code on the sealed package")

    def apply(self, kind, p):
        st = json.loads(bytes.fromhex(p["statement_hex"]))
        if kind == "claim_identity_registered":
            self.identities[st["claim_id"]] = sha(st["identity"])
            self.claim_series[st["claim_id"]] = st["identity"]["price_series"]
        elif kind == "test_instance_registered":
            self.instances[st["test_instance_id"]] = {**st, "descriptive": st["role"] == "descriptive"
                                                      or self._opened(st["claim_id"])}      # س 703
        elif kind == "court_policy_decided":
            self.policies[st["family"]] = st
        elif kind == "court_frozen":
            self.configs[st["family"]] = st["config"]
        elif kind == "court_ruling":
            self.rulings[st["ruling_id"]] = st
            self.req_nonces.add(json.loads(bytes.fromhex(st["request"]["statement_hex"]))["nonce"])
            self.att_nonces.add(json.loads(bytes.fromhex(st["attestation"]["statement_hex"]))["nonce"])

    # ---------------- API ----------------
    def commit(self, kind, s):
        return self.g._commit(kind, s.to_payload())

    def scope(self, family: str) -> dict:
        """Family membership from the ledger: claims opened on slices whose custody decision names this
        family (R1-2); never from the package's own field."""
        cu, cc = self._ext("decisions"), self._ext("openings")
        sf = {sl: d["family"] for sl, d in cu.decisions.items()}
        claims = sorted({c for (c, sl) in cc.openings if sf.get(sl) == family})
        return {"family": family, "claims": claims, "slice_family": dict(sorted(sf.items()))}

    def refresh(self):
        self.g._catch_up(tuple(self.g.ledger))

    def run(self, family: str, sign_as_operator, service):
        """Court operator entry point. The operator signs a run request naming the family only; the
        custody service (which alone holds the package store and its key) runs the frozen code and
        returns the output with a custody attestation; the operator records it as output (م7-03).
        The package bytes never reach this process."""
        req = sign_as_operator({"action": "court_run_request", "family": family})
        resp = service.execute(req.to_payload())
        self.refresh()
        st = {"action": "court_ruling", "family": family, "ruling_id": f"{family}:{len(self.rulings)}",
              "package_sha256": resp["package_sha256"], "code_sha256": CODE_SHA256, "output": resp["output"],
              "output_sha256": resp["output_sha256"], "request": req.to_payload(), "attestation": resp["attestation"]}
        self.commit("court_ruling", sign_as_operator(st))
        return st
