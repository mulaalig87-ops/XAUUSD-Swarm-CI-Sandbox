"""Stage 9, WP9-04 — knowledge from layer 10 back to layer 7 only through layer 3 (WP7-02 ت-09, م-10).

Source: «المعرفة لا تعود من الطبقة 10 إلى الطبقة 7 إلا عبر الطبقة 3» ⟨س 131⟩; ت-09: «عبر الطبقة 3 وحدها:
يُوسم بصنفه وحالة ZERO-PRIOR؛ ويُعمّى إن كان المستقبِل Z؛ ويُسجَّل كل مرور في النسب».

Enforced
- `knowledge_passage_recorded` (custody only): one recorded knowledge row (ruling_id, claim_id) to one
  registered mind, for a recipient path in (Z, G-Z, R). Tags are COPIED from the recorded row, never
  supplied: classification and ZERO-PRIOR state must equal the row's; blinded must be true when the
  recipient path is Z. The passage event is the lineage record of the passage (append-only ledger).
- `proposal_submitted` (pre-validation): every entry of the proposal's lineage `knowledge.seen` that
  names a knowledge row ("knowledge:<ruling_id>/<claim_id>") must have a recorded passage of that row
  to the proposing mind; otherwise refused (م-10).

Stated limits
- `knowledge.seen` must be a list of text; an entry that looks like a knowledge reference in any spelling
  ("Knowledge :", full-width colon, spaces) must have the exact form, or it is refused (review R1-01).
- A mind that uses a knowledge row WITHOUT naming it in its lineage is invisible here — the same
  limit as code that bypasses lineage capture (TP-50 ت8, docs/KNOWN_BLIND_SPOTS.md).
- The content of the blinding for knowledge (what "blinded" means for a knowledge row) is
  «غير معرّف في المعمارية»; the flag is recorded and required, not computed.
"""
from __future__ import annotations

import json
import re

from .charter import GateError
from .identity import Signed

PREFIX = "knowledge:"
REF = re.compile(r"knowledge:([^/\s]+)/([^/\s]+)")
REF_LIKE = re.compile(r"\s*knowledge\s*[:：]", re.IGNORECASE)    # variant spellings are refused, not ignored
RECIPIENT_PATHS = ("Z", "G-Z", "R")


class KnowledgePassageLayer:
    KINDS = ("knowledge_passage_recorded",)

    def __init__(self):
        self.passages: dict[tuple, dict] = {}       # (ruling_id, claim_id, mind_id) -> passage
        self.g = None

    def bind(self, g):
        self.g = g

    def _ext(self, attr):
        return next((x for x in self.g._ext.values() if hasattr(x, attr)), None)

    def _record(self, ruling_id, claim_id):
        kr = self._ext("records")
        if kr is None:
            return None
        return next((r for r in kr.records if r.get("ruling_id") == ruling_id and r.get("claim_id") == claim_id), None)

    def pre_validate(self, kind, p):
        if kind != "proposal_submitted":
            return
        st = json.loads(bytes.fromhex(p["statement_hex"]))
        mind = Signed.from_payload(p).identity
        lin = st.get("lineage")
        kn = lin.get("knowledge") if isinstance(lin, dict) else None
        seen = kn.get("seen") if isinstance(kn, dict) else None
        # review R1-01: a malformed `seen` is refused, never read as "nothing seen"
        if not isinstance(seen, list) or any(not isinstance(x, str) for x in seen):
            raise GateError("lineage knowledge.seen is a list of text entries (ت-09; review R1-01)")
        for item in seen:
            if REF_LIKE.match(item):                        # anything that looks like a knowledge reference
                m = REF.fullmatch(item)
                if m is None:
                    raise GateError(f"{item!r}: a knowledge reference is exactly 'knowledge:<ruling_id>/<claim_id>'")
                if (m.group(1), m.group(2), mind) not in self.passages:
                    raise GateError(f"{item!r} reached this mind without passing through layer 3 "
                                    "(ت-09, م-10, س 131): no recorded passage to it")

    def validate(self, kind, p):
        signer = Signed.from_payload(p).identity
        cl = self._ext("access_log")
        if cl is None or "custody" not in cl.roles.get(signer, set()):
            raise GateError("a knowledge passage is recorded by custody (layer 3) only (ت-09)")
        st = self.g._signed(p, signer, "record_knowledge_passage")
        allowed = {"action", "nonce", "ruling_id", "claim_id", "mind_id", "recipient_path", "classification",
                   "zero_prior", "blinded"}
        if set(st) - allowed or set(allowed) - set(st):
            raise GateError("knowledge passage: exactly " + ", ".join(sorted(allowed - {"action", "nonce"})))
        rec = self._record(st["ruling_id"], st["claim_id"])
        if rec is None:
            raise GateError("no recorded knowledge row for this ruling and claim")
        dl = self._ext("minds")
        if dl is None or st["mind_id"] not in dl.minds:
            raise GateError("the recipient is a registered mind")
        if st["recipient_path"] not in RECIPIENT_PATHS:
            raise GateError(f"recipient path is one of {RECIPIENT_PATHS}")
        if st["classification"] != rec.get("classification") or st["zero_prior"] != rec.get("zero_prior"):
            raise GateError("tags are copied from the recorded row: classification and ZERO-PRIOR state (ت-09)")
        if not isinstance(st["blinded"], bool) or (st["recipient_path"] == "Z" and not st["blinded"]):
            raise GateError("knowledge to Z is blinded (ت-09)")
        if (st["ruling_id"], st["claim_id"], st["mind_id"]) in self.passages:
            raise GateError("this passage is already recorded")

    def apply(self, kind, p):
        st = json.loads(bytes.fromhex(p["statement_hex"]))
        self.passages[(st["ruling_id"], st["claim_id"], st["mind_id"])] = st

    def commit(self, kind, s: Signed):
        return self.g._commit(kind, s.to_payload())
