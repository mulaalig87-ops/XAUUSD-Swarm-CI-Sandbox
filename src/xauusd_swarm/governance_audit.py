"""Cross-cutting axis — procedural governance audit (WP8-09; مك-13; register §13 #1–#3; ق-05; س 374).

- The audit is PROCEDURAL: it checks that layer 3 kept its stated rules, issues its report
  independently of the system's report on itself (س 374), and does NOT judge the scientific
  correctness of results (§13 #1). Any field that would carry a scientific verdict is refused.
- Separation of roles (§13 #2; ق-05): the governance auditor is separate from the custody auditor and
  holds no custody, court-operator, discovery or G-Z role; nobody combines two of custody, custody
  auditor, court operator and discovery participation (the last rule is enforced in custody.py).
  The governance auditor sees records and reports only (ق-05): it has no access track in custody.
- The report's checks are recomputed from the ledger state by the validator (audit_layer3), so a
  report cannot state a check result the ledger does not support.
- Planted cases (§13 #3; س 374, 1539–1541): each planted type is reported in exactly one of three
  states — «كُشف بفحص النسب»، «كُشف إحصائيًا»، «لم يُكشف بأي منهما: نقطة عمى معروفة» — and "not
  detected" is never proof that there is no leak (the report carries that statement).
NOT built: the planted-leak worlds and detectors themselves (TP-50); audit schedule (undefined).
"""
from __future__ import annotations

import json

from .charter import GateError
from .custody import GZ_RELEASE_LOCKED, SEPARATED
from .identity import Signed

STATES = ("كُشف بفحص النسب", "كُشف إحصائيًا", "لم يُكشف بأي منهما: نقطة عمى معروفة")
NOT_PROOF = "«لم يُكشف» ليس إثباتًا لغياب التسرب"
AUDITOR = "governance_auditor"
AUDITOR_EXCLUDES = ("custody", "custody_auditor", "court_operator", "discovery_participant", "gz_operator")
REPORT_FIELDS = {"action", "nonce", "report_id", "checks", "planted_cases", "statement"}


def audit_layer3(g) -> dict:
    """Procedural checks of layer 3 recomputed from ledger state."""
    cl = next(x for x in g._ext.values() if hasattr(x, "access_log"))
    cc = next((x for x in g._ext.values() if hasattr(x, "openings") and hasattr(x, "cards")), None)
    roles = cl.roles
    bad_sep = sorted(i for i, r in roles.items() if len(set(r) & set(SEPARATED)) > 1
                     or (AUDITOR in r and set(r) & set(AUDITOR_EXCLUDES)))
    openings = list(cc.openings) if cc else []
    no_dec = sorted({s for (_c, s) in openings if s not in cl.decisions})
    ok = [a for a in cl.access_log if a["outcome"] == "ok"]
    bad_track = [a["request_sha256"] for a in ok if a["track"] not in ("G-Z", "after_seal")]
    bad_ref = [a["request_sha256"] for a in cl.access_log if a["outcome"] == "refused" and a["returned"] != "none"]

    def chk(fails, n):
        return {"result": "pass" if not fails else "fail", "checked": n, "failures": len(fails)}
    return {
        "role_separation": chk(bad_sep, len(roles)),
        "custody_decision_before_opening": chk(no_dec, len(openings)),
        "decryption_only_g_z_or_after_seal": chk(bad_track, len(ok)),
        "refusals_return_nothing": chk(bad_ref, sum(1 for a in cl.access_log if a["outcome"] == "refused")),
        "gz_release_locked": chk([] if GZ_RELEASE_LOCKED else ["unlocked"], 1),
    }


class GovernanceAuditLayer:
    KINDS = ("governance_audit_reported",)

    def __init__(self):
        self.reports: dict[str, dict] = {}
        self.g = None

    def bind(self, g):
        self.g = g

    def _roles(self, ident):
        cl = next((x for x in self.g._ext.values() if hasattr(x, "access_log")), None)
        return cl.roles.get(ident, set()) if cl else set()

    def pre_validate(self, kind, p):
        if kind == "role_assigned":
            st = json.loads(bytes.fromhex(p["statement_hex"]))
            have = self._roles(st.get("holder"))
            r = st.get("role")
            if (r == AUDITOR and have & set(AUDITOR_EXCLUDES)) or (r in AUDITOR_EXCLUDES and AUDITOR in have):
                raise GateError("the governance auditor is separate from custody, the custody auditor, the court "
                                "operator, discovery and G-Z (§13 #2; ق-05)")

    def validate(self, kind, p):
        if kind == "governance_audit_reported":
            signer = Signed.from_payload(p).identity
            if AUDITOR not in self._roles(signer):
                raise GateError("the governance audit report is issued by the governance auditor (ق-05)")
            st = self.g._signed(p, signer, "governance_audit_report")
            extra = set(st) - REPORT_FIELDS
            if extra:
                raise GateError(f"procedural audit only; no scientific verdict (§13 #1): fields {sorted(extra)} refused")
            if not st.get("report_id") or st["report_id"] in self.reports:
                raise GateError("report needs a new report_id")
            if st.get("checks") != audit_layer3(self.g):
                raise GateError("the report's checks must equal those recomputed from the ledger")
            pc = st.get("planted_cases")
            if not isinstance(pc, list) or any(not isinstance(c, dict) or set(c) != {"type", "state"}
                                               or not isinstance(c["type"], str) or not c["type"].strip()
                                               or c["state"] not in STATES for c in pc):
                raise GateError(f"each planted type (non-empty text) is reported in one of the three states (§13 #3): {STATES}")
            types = [c["type"].strip() for c in pc]
            if len(set(types)) != len(types):
                raise GateError("each planted type appears once, with exactly one state (§13 #3; R1-02)")
            if st.get("statement") != NOT_PROOF:
                raise GateError(f"the report states: {NOT_PROOF}")

    def apply(self, kind, p):
        st = json.loads(bytes.fromhex(p["statement_hex"]))
        if kind == "governance_audit_reported":
            self.reports[st["report_id"]] = st

    def commit(self, kind, s: Signed):
        return self.g._commit(kind, s.to_payload())
