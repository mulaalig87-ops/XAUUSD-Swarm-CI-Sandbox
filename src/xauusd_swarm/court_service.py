"""Custody-side court execution service (WP8-04 R3; R2-3, R2-6).

Boundary: the package store (encrypted, custody key) and the package bytes live ONLY in the custody
service's process. The court operator's process holds a court-side replica (CourtLayer() without a
store, CustodyLayer(None)) and talks to this service through `execute(request)` only:
- input: the operator's signed run request (family name, nonce) — never package bytes;
- output: the code's ruling output, its hash, the package hash, and a custody-signed attestation
  binding (family, package, output, scope, frozen config, code release, request) — never the package.
Every replica verifies the attestation; this service's replica additionally recomputes each ruling
from the package (CourtLayer(custody_store=...)).
The court code runs inside custody because only custody may hold Z outputs (س 254, 284); the ruling
is still the court's: run by code alone, triggered and recorded by the court operator (م7-03).
Stated limit: process separation is shown by tests (spawned process, key generated inside it).
OS-account separation (different users, file permissions) is an operational requirement of the
deployment, as in CUSTODY_KEY_POLICY.md; this code cannot prove it on a single-user machine.
"""
from __future__ import annotations

import hashlib
import json
import uuid

from .charter import GateError
from .court import CODE_SHA256, PackageStore, compute, sha
from .identity import Signed, sign


class CustodyCourtService:
    def __init__(self, governance, store: PackageStore, *, identity: str, key):
        """governance: the CUSTODY replica, built with CourtLayer(custody_store=store)."""
        self.g, self._store, self._id, self._key = governance, store, identity, key
        self.court = next(x for x in governance._ext.values() if hasattr(x, "rulings"))
        self.cust = next(x for x in governance._ext.values() if hasattr(x, "sealed"))
        if self.court._store is not store:
            raise GateError("the custody replica's CourtLayer must hold this service's store")

    def _refresh(self):
        self.g._catch_up(tuple(self.g.ledger))

    def deposit(self, package_bytes: bytes) -> str:
        """Admit a Z-output package after custody's full-scope passage review (س 254, 284)."""
        self._refresh()
        h = hashlib.sha256(package_bytes).hexdigest()
        if h not in self.cust.passed:
            raise GateError("package has not passed custody review (س 254, 284)")
        return self._store.put(package_bytes)

    def execute(self, request_payload: dict) -> dict:
        self._refresh()
        s = Signed.from_payload(request_payload)
        if "court_operator" not in self.cust.roles.get(s.identity, set()):
            raise GateError("only the appointed court operator may request a court run (م7-03, ق-04)")
        rq = self.g._signed(request_payload, s.identity, "court_run_request")
        if rq["nonce"] in self.court.req_nonces:
            raise GateError("replayed run request")
        fam = rq.get("family")
        if fam not in self.court.configs:
            raise GateError("no frozen court rules for this family")
        h = self.cust.sealed.get(fam)
        data = self._store.get(h) if h else None
        if data is None:
            raise GateError("no sealed package of this family in the custody store")
        scope = self.court.scope(fam)
        out = compute(json.loads(data), self.court.configs[fam], self.court.instances, scope)
        att = sign(self._id, self._key, {
            "action": "court_compute_attest", "nonce": uuid.uuid4().hex, "family": fam, "package_sha256": h,
            "output_sha256": sha(out), "scope_sha256": sha(scope), "config_sha256": sha(self.court.configs[fam]),
            "code_sha256": CODE_SHA256,
            "request_sha256": hashlib.sha256(bytes.fromhex(request_payload["statement_hex"])).hexdigest()})
        return {"output": out, "output_sha256": sha(out), "package_sha256": h, "attestation": att.to_payload()}

    def reproduce(self, ruling_id: str) -> bool:
        """Determinism check inside custody: same inputs → same output hash."""
        self._refresh()
        r = self.court.rulings[ruling_id]
        data = self._store.get(r["package_sha256"])
        out = compute(json.loads(data), self.court.configs[r["family"]], self.court.instances, self.court.scope(r["family"]))
        return sha(out) == r["output_sha256"]
