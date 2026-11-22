"""Layer 10 — knowledge and failures registry, with lineage (WP8-04; spec WP7-01 §2.10, §17 of the
candidate, §5.1 lineage).

Source text: «ملحق فقط، بلا حذف، بنسب كامل، والتقاط آلي» ⟨س 2237⟩; «محتوى §5.1 كاملًا، بما فيه
الاستبعادات وحالة التعمية» ⟨س 2238⟩; ZERO-PRIOR state per result (س 2252–2255) with the §3.2 names
(سجل 7، §7 #6); one row per claim across paths with each path's rulings (س 2256); every record
links Test Instance ID → Claim ID and shows the ruling at Claim-ID level (س 2266); «سلامة كود فقط»
never appears in any knowledge class (س 2271); price series and Representation ID (س 2281);
availability time «مرصود» or «كمون مفترض» (س 2294); level-2 grid parameters (س 2295).
Rulings enter layer 10 from layer 9 through the court operator, AS OUTPUT BY CODE (م7-03 #1).

Enforced (round 2 additions marked)
- [R2, W-5] Lineage is written only by an identity the founder assigned as lineage recorder, with a
  declared capture mode (automatic or manual); every record carries that mode. The court operator
  cannot be a lineage recorder. This does not prove that an "automatic" capture is automatic: the
  mode is a declared, signed attribution, not a verified mechanism (مع-54 stays open).
- [R2, R1-4] Lineage seal per test instance, covering exactly the records written so far (hash of
  their statement hashes). After the seal no new lineage record is accepted; later changes are
  appended as lineage_corrected (reason, content, the corrected record's hash) and never alter the
  sealed set. A knowledge record requires the seal of every instance in it and cites those seals;
  ZERO-PRIOR is computed from the sealed set.
- Append-only: the registry has no delete or edit event; an unknown kind is refused by Governance.
- Lineage record per test instance with the five §5.1 rows (data incl. exclusions with reason and
  count, blinding state, availability-time source; environment; hypothesis; experiments; knowledge
  incl. tools seen, touching gold- or R-specific information, and an LLM in the lineage).
- knowledge_recorded: signed by the court operator; the claim row must equal the court ruling's
  output for that claim byte-for-byte (canonical hash); every test instance in it needs lineage;
  ZERO-PRIOR is recomputed by the validator from lineage and must match.
OPEN (flagged, not invented)
- Who assigns one of the twelve classes (س 2240–2251) is not defined; records carry
  «غير مصنف: جهة التصنيف غير معرّفة». The class list is kept for the future classifier.
- «التقاط آلي» actor and mechanism (مع-54) are undefined: lineage records are signed by the
  registered identity that writes them, and that identity is recorded.
- «المسار المعرفي» (س 368) meaning is open (م3-10): stored as given, not interpreted.
- Knowledge to layer 7 via layer 3 (س 131) is not built in this component.
- Re-identification (CS-01-04) is open, so «Z-حسابي» is never returned.
"""
from __future__ import annotations

import hashlib
import json

from .charter import GateError
from .court import sha
from .identity import Signed

CLASSES = ("مفسَّر آليًا (د1)", "مثبت سببيًا (د2)", "متوافق دون تعرّف", "مؤكد وغير مفسَّر", "انتظام وصفي",
           "تغير بنيوي", "إعادة اكتشاف لمفهوم معروف", "سلبية بحد أعلى", "أثر آلي", "فشل تكرار",
           "عدم كفاية", "لم يُختبر لغياب عدم مناسب")                                       # س 2240–2251
UNCLASSIFIED = "غير مصنف: جهة التصنيف غير معرّفة"
ZP = {"computational": "Z-حسابي",
      "linguistic": "Z مع مساهمة لغوية: صفر المعرفة غير قابل للتحقق",
      "breach": "Z مع خرق تعمية",
      "undetermined": "غير محدد: الحد المعلن (CS-01-04) مفتوح"}                            # §3.2 س 219–221
LINEAGE = {
    "data": ("source", "transforms", "block_usage", "exclusions", "blinding_state", "availability_time_source"),
    "environment": ("libraries", "environment", "seeds", "training_settings"),
    "hypothesis": ("versions_branches_edits", "epistemic_path"),
    "experiments": ("stopped_or_incomplete", "exclusion_reasons"),
    "knowledge": ("seen", "tools", "touched_gold_or_R_info", "llm_in_lineage", "blinding_breach_events"),
}
AVAILABILITY = ("مرصود", "مفترض")                                                         # س 388


def zero_prior(lineages: list[dict], reid_within_announced_threshold=None) -> str:
    """§3.2 conditions: breach = failed re-ID or an unauthorized decryption event; LLM in lineage;
    computational needs re-ID within the announced threshold (CS-01-04 open → undetermined)."""
    if reid_within_announced_threshold is False or any(l["knowledge"]["blinding_breach_events"] for l in lineages):
        return ZP["breach"]
    if any(l["knowledge"]["llm_in_lineage"] for l in lineages):
        return ZP["linguistic"]
    if reid_within_announced_threshold is True:
        return ZP["computational"]
    return ZP["undetermined"]


CAPTURE_MODES = ("automatic", "manual")


class KnowledgeRegistry:
    KINDS = ("lineage_recorder_assigned", "lineage_recorded", "lineage_sealed", "lineage_corrected",
             "knowledge_recorded")

    def __init__(self):
        self.recorders: dict = {}    # identity -> capture mode (W-5)
        self.lineage: dict = {}      # tid -> [records]
        self.seals: dict = {}        # tid -> seal statement (R1-4)
        self.corrections: dict = {}  # tid -> [post-seal corrections]
        self.records: list = []
        self.g = None

    def bind(self, g):
        self.g = g

    def _court(self):
        return next((x for x in self.g._ext.values() if hasattr(x, "rulings")), None)

    def _custody(self):
        return next((x for x in self.g._ext.values() if hasattr(x, "sealed")), None)

    def validate(self, kind, p):
        court = self._court()
        signer = Signed.from_payload(p).identity
        if kind == "lineage_recorder_assigned":                # W-5: documented role, founder-signed
            st = self.g._signed(p, "founder", "assign_lineage_recorder")
            h = st.get("holder")
            if h not in self.g.keys() or h == "founder":
                raise GateError("holder must be a registered identity other than the founder")
            if h in self.recorders:
                raise GateError("lineage recorder already assigned")
            if st.get("capture_mode") not in CAPTURE_MODES:
                raise GateError("capture_mode must be automatic or manual")
            cu = self._custody()
            if cu is not None and "court_operator" in cu.roles.get(h, set()):
                raise GateError("the court operator does not record the lineage it is judged on")
        elif kind in ("lineage_recorded", "lineage_sealed", "lineage_corrected"):
            if signer not in self.recorders:
                raise GateError("only an assigned lineage recorder writes lineage (W-5)")
        if kind == "lineage_sealed":
            st = self.g._signed(p, signer, "seal_lineage")
            t = st.get("test_instance_id")
            if t in self.seals:
                raise GateError("lineage already sealed for this test instance")
            if not self.lineage.get(t):
                raise GateError("nothing to seal: no lineage recorded")
            if st.get("lineage_sha256") != sha([l["statement_sha256"] for l in self.lineage[t]]):
                raise GateError("seal must cover exactly the lineage records written so far")
        elif kind == "lineage_corrected":
            st = self.g._signed(p, signer, "correct_lineage")
            t = st.get("test_instance_id")
            if t not in self.seals:
                raise GateError("before the seal, add lineage records; corrections are for sealed lineage")
            if st.get("corrects") not in [l["statement_sha256"] for l in self.lineage[t]]:
                raise GateError("a correction must reference a sealed lineage record by hash")
            if not str(st.get("reason", "")).strip() or not isinstance(st.get("correction"), dict):
                raise GateError("a correction needs a reason and its content")
        if kind == "lineage_recorded":
            st = self.g._signed(p, signer, "record_lineage")
            if court is None or st.get("test_instance_id") not in court.instances:
                raise GateError("lineage must reference a registered test instance")
            if st["test_instance_id"] in self.seals:
                raise GateError("lineage is sealed; later changes go through lineage_corrected (R1-4)")
            if st.get("capture_mode") != self.recorders[signer]:
                raise GateError("capture_mode must equal the recorder's assigned mode (automatic vs manual)")
            for sec, keys in LINEAGE.items():
                body = st.get(sec)
                if not isinstance(body, dict) or any(k not in body for k in keys):
                    raise GateError(f"lineage section {sec!r} needs {keys} (§5.1, س 364–370, 387–388)")
            d, k = st["data"], st["knowledge"]
            if not isinstance(d["exclusions"], list) or any(
                    not (isinstance(e, dict) and e.get("rule") and e.get("reason") and isinstance(e.get("count"), int)
                         and e["count"] >= 0) for e in d["exclusions"]):
                raise GateError("each exclusion needs rule, reason and count (س 364)")
            if d["availability_time_source"] not in AVAILABILITY:
                raise GateError("availability time source must be مرصود or مفترض (س 388)")
            if not isinstance(k["llm_in_lineage"], bool) or not isinstance(k["touched_gold_or_R_info"], bool) \
                    or not isinstance(k["blinding_breach_events"], list):
                raise GateError("knowledge row: llm_in_lineage and touched_gold_or_R_info are booleans; breach events a list")
        elif kind == "knowledge_recorded":
            cu = self._custody()
            if cu is None or "court_operator" not in cu.roles.get(signer, set()):
                raise GateError("rulings enter layer 10 through the court operator only (م7-03 #1)")
            st = self.g._signed(p, signer, "record_knowledge")
            r = court.rulings.get(st.get("ruling_id")) if court else None
            if r is None:
                raise GateError("knowledge record must reference a recorded court ruling")
            cid = st.get("claim_id")
            row = r["output"]["claims"].get(cid)
            if row is None or sha(row) != sha(st.get("row")):
                raise GateError("the claim row must equal the court output for this claim, as output by code")
            if any(x["ruling_id"] == r["ruling_id"] and x["claim_id"] == cid for x in self.records):
                raise GateError("one row per claim per ruling (س 2256)")
            tids = [v["test_instance_id"] for v in row["paths"].values()]
            for t in tids:
                ti = court.instances[t]
                if ti["claim_id"] != cid:
                    raise GateError("Test Instance ID must link to this Claim ID (س 2266)")
                if ti.get("code_integrity_only"):
                    raise GateError("«سلامة كود فقط» never enters the knowledge registry (س 2271)")
                if t not in self.seals:
                    raise GateError(f"lineage of {t} must be sealed before the knowledge record (R1-4, W-5)")
            if st.get("lineage_seals") != {t: self.seals[t]["lineage_sha256"] for t in sorted(tids)}:
                raise GateError("knowledge record must cite the lineage seal of every test instance in it")
            lin = [l for t in tids for l in self.lineage[t]]
            if st.get("zero_prior") != zero_prior(lin):
                raise GateError("ZERO-PRIOR state is computed from lineage, not supplied")
            if st.get("classification") != UNCLASSIFIED:
                raise GateError("classification authority is undefined; record stays unclassified")
            meta = st.get("claim_meta", {})
            if meta.get("price_series") != sorted({court.instances[t]["price_series"] for t in tids}) \
                    or meta.get("representation_ids") != sorted({court.instances[t]["representation_id"] for t in tids}):
                raise GateError("price series and Representation IDs must match the test instances (س 2281)")
            if meta.get("reporting_level") not in (1, 2, 3, "n/a"):
                raise GateError("reporting level must be 1, 2, 3 or n/a (س 2281)")
            if meta.get("reporting_level") == 2 and len(meta.get("grid_parameters", [])) != 6:
                raise GateError("level 2 needs the six grid parameters (س 2295)")
            if meta.get("availability") not in ("مرصود", "كمون مفترض", "n/a"):
                raise GateError("availability must be مرصود, كمون مفترض or n/a (س 2294)")

    def apply(self, kind, p):
        st = json.loads(bytes.fromhex(p["statement_hex"]))
        st["recorded_by"] = Signed.from_payload(p).identity
        st["statement_sha256"] = hashlib.sha256(bytes.fromhex(p["statement_hex"])).hexdigest()
        if kind == "lineage_recorder_assigned":
            self.recorders[st["holder"]] = st["capture_mode"]
        elif kind == "lineage_sealed":
            self.seals[st["test_instance_id"]] = st
        elif kind == "lineage_corrected":
            self.corrections.setdefault(st["test_instance_id"], []).append(st)
        elif kind == "lineage_recorded":
            self.lineage.setdefault(st["test_instance_id"], []).append(st)
        elif kind == "knowledge_recorded":
            self.records.append(st)

    # ---------------- API ----------------
    def commit(self, kind, s):
        return self.g._commit(kind, s.to_payload())

    def build_record(self, ruling_id: str, claim_id: str, *, reporting_level, availability, grid_parameters=None) -> dict:
        """Builds the operator's statement from code output (the operator only signs)."""
        court = self._court()
        row = court.rulings[ruling_id]["output"]["claims"][claim_id]
        tids = [v["test_instance_id"] for v in row["paths"].values()]
        lin = [l for t in tids for l in self.lineage.get(t, [])]
        meta = {"price_series": sorted({court.instances[t]["price_series"] for t in tids}),
                "representation_ids": sorted({court.instances[t]["representation_id"] for t in tids}),
                "reporting_level": reporting_level, "availability": availability}
        if grid_parameters is not None:
            meta["grid_parameters"] = grid_parameters
        return {"action": "record_knowledge", "ruling_id": ruling_id, "claim_id": claim_id, "row": row,
                "zero_prior": zero_prior(lin), "classification": UNCLASSIFIED, "claim_meta": meta,
                "lineage_seals": {t: self.seals[t]["lineage_sha256"] for t in sorted(tids) if t in self.seals}}

    def seal_statement(self, test_instance_id: str) -> dict:
        return {"action": "seal_lineage", "test_instance_id": test_instance_id,
                "lineage_sha256": sha([l["statement_sha256"] for l in self.lineage.get(test_instance_id, [])])}
