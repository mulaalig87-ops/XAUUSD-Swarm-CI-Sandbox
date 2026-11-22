"""Governance core: trust root + charters (layers 1–2) + charter-conflict gate (WP8-02).

EVENT-SOURCED. The ledger is the only source of truth:
- Every operation is validated against state that has been CAUGHT UP with the ledger under the
  ledger's write lock (other processes included), then appended, and only then applied in
  memory. A failed write leaves memory unchanged.
- At start-up the whole state (keys, nonces, charters and versions, detector, rules and
  versions, check/withdrawal status, slice bindings) is REBUILT by replaying every event through
  the SAME validation rules, re-verifying every signature. An invalid or inconsistent history is
  refused.

Decided rules implemented:
- م7-04: the charter governs; a conflicting rule is not executed; every conflict is recorded;
  layers 3–10 cannot amend.
- ق-21: amendment = founder-signed, with an independent-audit reference, version and hash; it
  never applies to a slice consumed earlier (fixed binding at consumption).
- D-04 + §26 B / غ-04: founder-appointed detector; not the rule's author or executor; record =
  charter, clause, rule version/hash, finding, timestamp; conflict → suspended; unchecked or
  suspended → no execution. Withdrawal: founder-signed, final per version (ChatGPT decision B
  under founder delegation, WP8-02 review).
- Keys: only founder-signed registration; nonces single-use across restarts and processes.
NOT implemented (undefined in the spec): HOW a conflict is detected. The detector's finding is an
input; the gate enforces and records it, and never claims to detect conflicts itself.
"""
from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from .identity import AuthError, Signed, check_signature, public_hex
from .ledger import Ledger

CHARTERS = ("project", "claims")


class GateError(Exception):
    pass


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class CharterVersion:
    name: str
    version: int
    text: str
    sha256: str


@dataclass(frozen=True)
class Rule:
    rule_id: str
    version: int
    text: str
    author: str
    executor: str
    layer: int
    sha256: str

    @staticmethod
    def make(rule_id, version, text, *, author, executor, layer) -> "Rule":
        return Rule(rule_id, version, text, author, executor, layer, sha256_text(text))

    def intact(self) -> bool:
        return sha256_text(self.text) == self.sha256


@dataclass
class _State:
    keys: dict = field(default_factory=dict)
    nonces: set = field(default_factory=set)
    charters: dict = field(default_factory=lambda: {c: [] for c in CHARTERS})
    detector: str | None = None
    rules: dict = field(default_factory=dict)
    status: dict = field(default_factory=dict)        # (rule_id, version) -> status
    last_check: dict = field(default_factory=dict)    # (rule_id, version) -> check payload
    slices: dict = field(default_factory=dict)


class Governance:
    def __init__(self, founder_public_key: Ed25519PublicKey, ledger: Ledger, extensions=()):
        """extensions: components that own further event kinds (e.g. claims.ClaimsCharter).
        They share this ledger, the key registry and the nonce set, and are rebuilt the same way."""
        self.ledger = ledger
        self._founder_hex = public_hex(founder_public_key)
        self._s = _State(keys={"founder": self._founder_hex})
        self._ext = {}
        for x in extensions:
            for k in x.KINDS:
                self._ext[k] = x
            x.bind(self)
        self._seen = 0
        self._catch_up(tuple(ledger))                  # rebuild + validate the whole history

    # ======================= engine ============================================================
    def _catch_up(self, entries) -> None:
        for e in entries[self._seen:]:
            try:
                self._validate(e.kind, e.payload)
            except (GateError, AuthError) as x:
                raise GateError(f"invalid history at entry {e.seq} ({e.kind}): {x}")
            self._apply(e.kind, e.payload)
            self._seen = e.seq + 1

    def _commit(self, kind: str, payload):
        """payload: a dict, or a function of the fresh state returning the dict."""
        def build(entries):
            self._catch_up(entries)                    # fresh state under the lock
            p = payload() if callable(payload) else payload
            self._validate(kind, p)
            self._dry_apply(kind, p)                   # FL-013: an entry that cannot be applied is never written
            return p
        e = self.ledger.append_with(kind, build)       # raises -> nothing written, nothing applied
        self._apply(kind, e.payload)
        self._seen = e.seq + 1
        return e

    def _dry_apply(self, kind: str, p: dict) -> None:
        """Apply the statement to COPIES of the state before it is appended (FL-013). A statement that
        validation let through but that cannot be applied (e.g. an unhashable value reaching a set)
        would otherwise be written to the append-only ledger and break every later replay. Any failure
        here is a refusal and nothing is written."""
        try:
            if kind in self._ext:
                x = self._ext[kind]
                y = copy.copy(x)
                for a, v in vars(x).items():
                    if isinstance(v, (dict, list, set)):
                        setattr(y, a, copy.deepcopy(v))
                y.apply(kind, p)
            else:
                saved = self._s
                self._s = copy.deepcopy(saved)
                try:
                    self._apply(kind, p)
                finally:
                    self._s = saved
        except (GateError, AuthError):
            raise
        except Exception as x:                          # noqa: BLE001 — any failure is a refusal
            raise GateError(f"statement cannot be applied ({type(x).__name__}: {str(x)[:120]}); nothing written") from x

    # ======================= validation (pure; no mutation) ====================================
    def _signed(self, p: dict, identity: str, action: str) -> dict:
        s = Signed.from_payload(p)
        if s.identity != identity:
            raise AuthError(f"statement is signed by {s.identity!r}, but {identity!r} is required")
        pub = self._s.keys.get(identity)
        if pub is None:
            raise AuthError(f"no registered key for {identity!r}")
        st = check_signature(pub, s)
        if st.get("action") != action:
            raise AuthError(f"statement is for action {st.get('action')!r}, not {action!r}")
        if not st.get("nonce"):
            raise AuthError("missing nonce")
        if st["nonce"] in self._s.nonces:
            raise AuthError("replayed nonce")
        return st

    def _both_set(self):
        missing = [c for c in CHARTERS if not self._s.charters[c]]
        if missing:
            raise GateError(f"both charters must be set first; missing: {missing}")

    def _charter_state(self) -> dict:
        return {c: {"version": self._s.charters[c][-1].version, "sha256": self._s.charters[c][-1].sha256}
                for c in CHARTERS if self._s.charters[c]}

    def _validate(self, kind: str, p: dict) -> None:
        if not isinstance(p, dict):
            raise GateError("an event payload is an object")
        if "statement_hex" in p:                         # FL-014: one shape guard for every statement
            from .statement_guard import check_statement
            try:
                st0 = json.loads(bytes.fromhex(p["statement_hex"]))
            except (TypeError, ValueError) as x:
                raise GateError(f"statement is not readable ({type(x).__name__})") from x
            if not isinstance(st0.get("nonce"), str) or not isinstance(st0.get("action"), str):
                raise AuthError("statement needs a text action and nonce")
            check_statement(st0, kind)
        for x in dict.fromkeys(self._ext.values()):      # cross-component preconditions (no-op by default)
            pre = getattr(x, "pre_validate", None)
            if pre:
                pre(kind, p)
        S = self._s
        if kind == "key_registered":
            st = self._signed(p, "founder", "register_key")
            if p.get("identity") != st.get("identity"):
                raise GateError("event identity does not match the signed statement")
            if not isinstance(st.get("identity"), str) or not st["identity"].strip():
                raise GateError("identity: non-empty text")
            if st["identity"] in S.keys:
                raise GateError(f"identity {st['identity']!r} already registered")
            try:
                Ed25519PublicKey.from_public_bytes(bytes.fromhex(st["public_key_hex"]))
            except (ValueError, KeyError):
                raise GateError("invalid public key")
        elif kind == "charter_initial":
            st = self._signed(p, "founder", "charter_initial")
            if st.get("charter") not in CHARTERS:
                raise GateError("unknown charter")
            if S.charters[st["charter"]]:
                raise GateError("initial version already set")
        elif kind == "charter_amended":
            st = self._signed(p, "founder", "charter_amend")
            if st.get("charter") not in CHARTERS or not S.charters[st["charter"]]:
                raise GateError("charter not set")
            if not st.get("audit_ref"):
                raise GateError("amendment needs an independent-audit reference (ق-21)")
        elif kind == "detector_appointed":
            st = self._signed(p, "founder", "appoint_detector")
            if st.get("holder") not in S.keys or st["holder"] == "founder":
                raise GateError("detector must be a registered identity other than the founder")
        elif kind == "rule_registered":
            r = Rule(**p["rule"])
            if not 3 <= r.layer <= 10:
                raise GateError("rules under the gate belong to layers 3–10 (governance)")
            if not r.intact():
                raise GateError("rule text does not match its hash")
            old = S.rules.get(r.rule_id)
            if old and r.version <= old.version:
                raise GateError("a new rule version must be higher than the registered one")
        elif kind == "charter_check":
            if S.detector is None:
                raise GateError("no detector appointed")
            st = self._signed(p, S.detector, "charter_check")
            self._both_set()
            r = S.rules.get(st.get("rule_id"))
            if r is None:
                raise GateError("unknown rule")
            if st.get("rule_version") != r.version or st.get("rule_sha256") != r.sha256 or not r.intact():
                raise GateError("check does not refer to the registered rule version and hash")
            if st.get("charters") != self._charter_state():
                raise GateError("check does not refer to the current versions and hashes of BOTH charters")
            if S.detector in (r.author, r.executor):
                raise GateError("the detector does not author or execute the rule it checks (§26 B)")
            if S.status[(r.rule_id, r.version)] == "withdrawn":
                raise GateError("withdrawn rule version is final; register a new version")
            if st.get("conflict") and (st.get("charter") not in CHARTERS or not st.get("clause")):
                raise GateError("a conflict record needs the charter and the clause")
        elif kind == "rule_withdrawn":
            st = self._signed(p, "founder", "withdraw_rule")
            r = S.rules.get(st.get("rule_id"))
            if r is None or st.get("rule_version") != r.version:
                raise GateError("withdrawal must name the registered rule and version")
        elif kind == "slice_consumed":
            self._both_set()
            if p["slice"] in S.slices:
                raise GateError(f"slice {p['slice']} already consumed")
            if p["charters"] != {c: S.charters[c][-1].version for c in CHARTERS}:
                raise GateError("slice binding must equal the charter versions in force")
        elif kind == "rule_executed":
            self._both_set()
            r = S.rules.get(p["rule_id"])
            if r is None:
                raise GateError("unknown rule")
            if not r.intact():
                raise GateError("rule text no longer matches its registered hash")
            if p["executor"] != r.executor:
                raise GateError("only the registered executor may execute the rule")
            stt = S.status[(r.rule_id, r.version)]
            if stt != "clear":
                raise GateError(f"rule {r.rule_id} is {stt}; it does not execute (م7-04; §26 B)")
            last = S.last_check[(r.rule_id, r.version)]
            if last["rule_sha256"] != r.sha256 or last["charters"] != self._charter_state():
                raise GateError("the clear check does not cover this rule version or the current charters; re-check")
        elif kind in self._ext:
            self._ext[kind].validate(kind, p)
        else:
            raise GateError(f"unknown event kind {kind!r}")

    # ======================= state transition (only after a successful append) ==================
    def _apply(self, kind: str, p: dict) -> None:
        S = self._s
        st = json.loads(bytes.fromhex(p["statement_hex"])) if "statement_hex" in p else None
        if st is not None:
            S.nonces.add(st["nonce"])
        if kind == "key_registered":
            S.keys[st["identity"]] = st["public_key_hex"]
        elif kind == "charter_initial":
            S.charters[st["charter"]].append(CharterVersion(st["charter"], 1, st["text"], sha256_text(st["text"])))
        elif kind == "charter_amended":
            v = S.charters[st["charter"]][-1].version + 1
            S.charters[st["charter"]].append(CharterVersion(st["charter"], v, st["text"], sha256_text(st["text"])))
        elif kind == "detector_appointed":
            S.detector = st["holder"]
        elif kind == "rule_registered":
            r = Rule(**p["rule"])
            S.rules[r.rule_id] = r
            S.status[(r.rule_id, r.version)] = "unchecked"
        elif kind == "charter_check":
            key = (st["rule_id"], st["rule_version"])
            S.status[key] = "suspended" if st["conflict"] else "clear"
            S.last_check[key] = {"rule_sha256": st["rule_sha256"], "charters": st["charters"]}
        elif kind == "rule_withdrawn":
            S.status[(st["rule_id"], st["rule_version"])] = "withdrawn"
        elif kind == "slice_consumed":
            S.slices[p["slice"]] = dict(p["charters"])
        elif kind in self._ext:
            self._ext[kind].apply(kind, p)

    # ======================= public API =========================================================
    def register_key(self, s: Signed):
        st = json.loads(s.statement)
        return self._commit("key_registered", {**s.to_payload(), "identity": st.get("identity")})

    def set_initial_charter(self, s: Signed):
        return self._commit("charter_initial", s.to_payload())

    def amend_charter(self, s: Signed):
        return self._commit("charter_amended", s.to_payload())

    def appoint_detector(self, s: Signed):
        return self._commit("detector_appointed", s.to_payload())

    def register_rule(self, rule: Rule):
        return self._commit("rule_registered", {"rule": dict(rule.__dict__)})

    def record_check(self, s: Signed):
        p = s.to_payload()
        p["timestamp"] = datetime.now(timezone.utc).isoformat()
        return self._commit("charter_check", p)

    def withdraw(self, s: Signed):
        return self._commit("rule_withdrawn", s.to_payload())

    def consume_slice(self, slice_id: str):
        def payload():                                  # computed on FRESH state, under the lock
            b = {c: self._s.charters[c][-1].version for c in CHARTERS if self._s.charters[c]}
            return {"slice": slice_id, "charters": b}
        return self._commit("slice_consumed", payload)

    def authorize_execution(self, rule_id: str, *, executor: str):
        return self._commit("rule_executed", {"rule_id": rule_id, "executor": executor})

    # ---- read-only views (copies) ----
    def current(self, name: str) -> CharterVersion:
        if not self._s.charters.get(name):
            raise GateError(f"charter {name!r} not set")
        return self._s.charters[name][-1]

    def charter_for_slice(self, name: str, slice_id: str) -> CharterVersion:
        b = self._s.slices.get(slice_id)
        return self._s.charters[name][b[name] - 1] if b else self.current(name)

    def status(self, rule_id: str) -> str:
        r = self._s.rules[rule_id]
        return self._s.status[(rule_id, r.version)]

    def rule(self, rule_id: str) -> Rule:
        return self._s.rules[rule_id]

    def charter_state(self) -> dict:
        return json.loads(json.dumps(self._charter_state()))

    def keys(self) -> dict:
        return dict(self._s.keys)
