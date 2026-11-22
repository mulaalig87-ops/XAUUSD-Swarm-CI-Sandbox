"""Layer 2 — claims charter: claim cards registered and frozen BEFORE opening (WP8-02 #2).

Source: candidate §4 (س 292–342) as specified in WP7-01 §2.2. Every rule below cites its line
and tag. Only enforcement of what the text states; nothing is invented about HOW the court rules.

Implemented:
- §4.1 tags (multiple per claim) from the listed property names only (س 296–298).
- §4.2 special categories: open (same conditions, no separate budget, س 303); composite = one
  frozen model (س 304: a frozen model hash is required); "confirmed and unexplained difference"
  (س 305).
- §4.3 proof paths أ, ب, ج, د1, د2 (س 309–316); path هـ is CLOSED and refused. For د2, the six
  conditions (س 319–324) must each be declared, non-empty, BEFORE opening; a د2 card without them
  is refused. The text says the quantity is "defined before confirmation" (س 319); requiring all
  six BEFORE OPENING is the adopted reading (ChatGPT decision under founder delegation, WP8-02 #2
  review), consistent with س 330.
- س 329: the court's three rulings (existence, size with uncertainty, importance): the CRITERIA
  for each must be declared on the card before opening ("no threshold is invented after the
  result"). "No path counts as evidence for another": evidence may cite only claims on the SAME
  path. س 326: no result moves from د1 to د2 (a special case of the same rule).
- س 330: type and path fixed before opening. Opening a claim on a slice BINDS the card version
  in force at that moment; later versions never apply to that slice (س 336: amendments carry
  version + hash and do not apply to a revealed slice).
- §4.4 scope: declared in advance (س 334), with one of the listed scope types (س 335).
NOT implemented (outside this component): the rulings themselves (layer 9, court operator ق-04),
the importance map (س 340), and evidence evaluation.
Authority (ChatGPT decision under founder delegation, WP8-02 #2 review): a claim card is
registered ONLY by a founder-signed statement. A narrower delegation to a specific role may be
added later by an explicit decision; it is not assumed from key registration.
Openings: a claim may be opened only on a slice already recorded by "slice_consumed" in the
governance ledger.
Identity frozen across versions (reading of س 330 "type and path fixed before opening"; the WP8-02
#2 review asked for the exceptions to be stated explicitly):
  FROZEN after version 1: tags, category, path, and for a composite the frozen model hash
  (a composite IS one frozen model, س 304). A change to any of these is a NEW claim.
  MAY change in a later version (س 336: versioned and hashed, never applied to a revealed slice):
  scope and scope type, the three ruling criteria, and the د2 condition texts.
"""
from __future__ import annotations

import hashlib
import json

from .charter import GateError
from .ledger import canonical

TAGS = (  # س 296 [متفق], س 297 [جديد], س 298 [مبدئي] — names as in the candidate
    "الموقع", "المقياس", "الشكل والذيول", "الاعتماد", "التوقيت", "اللاتناظر الزمني", "الحالة",
    "الهندسة", "الترابط بين المقاييس", "شبكة السعر",
    "الثبات", "شدة الوصول", "الذيل المشترك",
    "التطور التدريجي",
)
CATEGORIES = (None, "open", "composite", "confirmed_unexplained_difference")   # §4.2
PATHS = ("أ", "ب", "ج", "د1", "د2")                                              # §4.3; هـ closed
CLOSED_PATHS = ("هـ",)
D2_CONDITIONS = ("causal_quantity", "causal_structure", "identification_strategy",
                 "confounder_assumptions", "sensitivity_unmeasured", "alternative_explanations")  # س 319–324
RULINGS = ("existence", "size_with_uncertainty", "importance")                   # س 329
FROZEN_FIELDS = ("uses_events", "tags", "category", "path", "frozen_model_sha256")              # identity of the claim
TP09_BUILT = False      # event protocol (TP-09.1–09.3) not built; an event-based claim is refused (FD-01-D43)
SCOPE_TYPES = ("stable", "conditional", "variable_size", "transient", "break_linked")  # س 335


def card_hash(card: dict) -> str:
    return hashlib.sha256(canonical(card)).hexdigest()


class ClaimsCharter:
    KINDS = ("claim_registered", "claim_opened", "claim_evidence_cited")

    def __init__(self):
        self.cards: dict[str, list[dict]] = {}       # claim_id -> versions (card dicts)
        self.openings: dict[tuple[str, str], int] = {}   # (claim_id, slice) -> bound version
        self.g = None

    def bind(self, governance):
        self.g = governance

    # ---------------- validation ----------------
    def _card_rules(self, c: dict) -> None:
        for k in ("claim_id", "version", "tags", "category", "path", "scope_type", "scope", "rulings", "uses_events"):
            if k not in c:
                raise GateError(f"claim card missing {k!r}")
        # FD-01-D43 gate, enforced (WP9-05 review R1-02, B): TP-09 applies «عند استخدام الأحداث» (CS-05-09).
        if not isinstance(c["uses_events"], bool):
            raise GateError("uses_events is true or false — no silent default (FD-01-D43)")
        if c["uses_events"] and not TP09_BUILT:
            raise GateError("an event-based claim needs the event protocol TP-09.1–09.3 built and passed first "
                            "(CS-05-09; FD-01-D43); it is not built")
        if c["path"] in CLOSED_PATHS:
            raise GateError("path هـ (exploitation after costs) is CLOSED (س 316)")
        if c["path"] not in PATHS:
            raise GateError(f"unknown proof path {c['path']!r}")
        if not c["tags"] or any(t not in TAGS for t in c["tags"]) or len(set(c["tags"])) != len(c["tags"]):
            raise GateError("tags must be a non-empty set drawn from §4.1 (س 296–298)")
        if c["category"] not in CATEGORIES:
            raise GateError("unknown special category (§4.2)")
        if c["category"] == "composite":
            h = c.get("frozen_model_sha256")
            if not (isinstance(h, str) and len(h) == 64 and all(ch in "0123456789abcdef" for ch in h)):
                raise GateError("a composite claim is ONE frozen model: a SHA-256 hash (64 lowercase hex) is required (س 304)")
        if c["scope_type"] not in SCOPE_TYPES or not str(c["scope"]).strip():
            raise GateError("scope must be declared in advance with a listed scope type (س 334–335)")
        if set(c["rulings"]) != set(RULINGS) or any(not str(v).strip() for v in c["rulings"].values()):
            raise GateError("criteria for all three rulings must be declared before opening (س 329)")
        if c["path"] == "د2":
            d2 = c.get("d2_conditions") or {}
            missing = [k for k in D2_CONDITIONS if not str(d2.get(k, "")).strip()]
            if missing:
                raise GateError(f"د2 needs all six conditions declared (س 319–324); missing: {missing}")

    def validate(self, kind: str, p: dict) -> None:
        if kind == "claim_registered":
            st = self.g._signed(p, "founder", "register_claim")      # founder only (review decision)
            c = st.get("card")
            if not isinstance(c, dict):
                raise GateError("card is an object (FL-014)")
            self._card_rules(c)
            versions = self.cards.get(c["claim_id"], [])
            if c["version"] != len(versions) + 1:
                raise GateError("claim versions must be consecutive (1, 2, ...)")
            if versions:
                prev = versions[0]
                changed = [f for f in FROZEN_FIELDS if c.get(f) != prev.get(f)]
                if changed:
                    raise GateError(f"claim identity is frozen; changed {changed}: register a NEW claim (س 330, س 304)")
            if p.get("card_sha256") != card_hash(c):
                raise GateError("card hash mismatch")
        elif kind == "claim_opened":
            cid, sl = p["claim_id"], p["slice"]
            if cid not in self.cards:
                raise GateError("a claim must be registered before opening (س 330)")
            if sl not in self.g._s.slices:
                raise GateError("unknown slice: it must be recorded by slice_consumed first")
            if (cid, sl) in self.openings:
                raise GateError("claim already opened on this slice")
            if p["version"] != len(self.cards[cid]) or p["card_sha256"] != card_hash(self.cards[cid][-1]):
                raise GateError("opening must bind the current card version and hash")
        elif kind == "claim_evidence_cited":
            a, b = p["claim_id"], p["evidence_claim_id"]
            if a not in self.cards or b not in self.cards:
                raise GateError("unknown claim")
            pa, pb = self.cards[a][-1]["path"], self.cards[b][-1]["path"]
            if pa != pb:
                raise GateError(f"no path counts as evidence for another (س 329; د1→د2 س 326): {pb} → {pa}")

    def apply(self, kind: str, p: dict) -> None:
        if kind == "claim_registered":
            c = json.loads(bytes.fromhex(p["statement_hex"]))["card"]
            self.cards.setdefault(c["claim_id"], []).append(c)
        elif kind == "claim_opened":
            self.openings[(p["claim_id"], p["slice"])] = p["version"]

    # ---------------- API ----------------
    def register(self, s) -> None:
        st = json.loads(s.statement)
        self.g._commit("claim_registered", {**s.to_payload(), "card_sha256": card_hash(st.get("card") or {})})

    def open_on_slice(self, claim_id: str, slice_id: str) -> None:
        def payload():
            v = self.cards.get(claim_id, [])
            return {"claim_id": claim_id, "slice": slice_id, "version": len(v),
                    "card_sha256": card_hash(v[-1]) if v else ""}
        self.g._commit("claim_opened", payload)

    def cite_evidence(self, claim_id: str, evidence_claim_id: str) -> None:
        self.g._commit("claim_evidence_cited", {"claim_id": claim_id, "evidence_claim_id": evidence_claim_id})

    def card_for_slice(self, claim_id: str, slice_id: str) -> dict:
        """The card bound when the claim was opened on that slice; its criteria are the only ones
        the court may use there (س 329, س 336)."""
        v = self.openings.get((claim_id, slice_id))
        if v is None:
            raise GateError("claim not opened on this slice")
        return json.loads(json.dumps(self.cards[claim_id][v - 1]))
