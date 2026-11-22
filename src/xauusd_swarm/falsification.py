"""Layer 8 — falsification and confirmation (WP8-08; spec WP7-01 §2.8, candidate §14, §11, §15;
WP7-05 §1.4 and §3; WP7-02 ت-13).

SYNTHETIC ONLY. This layer governs the inference stages, null models, blind rediscovery and law
drift. It runs no statistic; the court (layer 9) rules, and Final consumption is enforced in
layer 6 (س 550–556).

Implemented (each cites its source):
- The five stages, in order, per claim (س 2169–2175): 1 difference detected (on a Discovery slice);
  2 source identification: C0 results recorded for that slice's dataset, at least one null swap,
  and the temporal location (س 2172); 3 claim formulation: the claim card and Claim ID exist and the
  basic null is assigned; 4 confirmation on Final: the claim is in an opened Final unit (layer 6);
  5 interpretation through د1 or د2 by a separate claim on that path, whose conditions the claims
  charter enforces (س 2175, 319–326). Each stage needs the previous one.
- Null models (§11.1; WP7-05 §1.4; ق-06; §7 #11): one basic null per claim, "justified", with a card
  accepted by the founder (layer 7 registry; immutable once accepted); independent-source alternatives
  and sensitivity analyses listed when available; N-c is diagnostic only and is refused as a basic
  (confirmatory) null. "No confirmatory test without a VALID null" (س 818, صل-131): validity comes
  from controls alone (ق-06), recorded per null model citing RECORDED control results of the controls
  registry (controls.py) that target this null model, at least one positive and one negative, all
  passed (review R1-01; free-standing hashes are not accepted); a claim whose basic null has no validity record cannot be submitted to the confirmation
  gate, and its status reads «لم يُختبر تأكيديًا لعدم توفر نموذج صفري (Null) صالح» (WP7-05 §3).
  "Null failure is not a discovery" (س 820): no stage-1 record may cite a null failure as the difference.
- Blind rediscovery (§14.3): on Discovery only; tests the process and never counts as confirmation;
  registered match criterion before any deliverable; shared tool dependencies documented; an audit
  sample declared; deliverables sealed (hash) before scoring; scoring by the court operator with the
  registered criterion; result tagged "process test, not confirmation" (س 2195–2199).
- Law drift (§15; ق-14): the declared scope names one of the five types and is frozen before any
  replication result; a failed replication is a failure unless the frozen scope predicted it; "the
  law changed" is a NEW claim linked to the old one, never a re-reading of the old result; no
  retroactive justification (س 2209–2211).
- Deliverables to layer 9 (ت-13) are the sealed packages already handled by the court and custody
  service (WP8-04); nothing here opens them.
NOT implemented / open: the null generators themselves and the sign-null family N-a/N-a′/N-b
computations (§11.2; tests TP-82, TP-83, TP-90 belong to the assumptions plan); "justified" has no
mechanical criterion (the justification text is required and recorded); the six د2 conditions live
in the claims charter; change-point handling through path ج (س 2211) is not built; the audit-sample
procedure of blind rediscovery has no size rule in the sources (the size is declared, not derived).
"""
from __future__ import annotations

import json

from .charter import GateError
from .identity import Signed
from .inventory import content_sha256

DRIFT_TYPES = ("مستقرة", "مشروطة", "متغيرة الحجم", "عابرة", "تحولات بنيوية")              # ق-14
DIAGNOSTIC_ONLY = ("N-c",)                                                                # §7 #11
NOT_TESTED = "لم يُختبر تأكيديًا لعدم توفر نموذج صفري (Null) صالح"                         # WP7-05 §3
PROCESS_TEST = "اختبار للعملية، لا يُحتسب تأكيدًا"                                         # س 2195
INTERPRETATION_PATHS = ("د1", "د2")


def _hex64(h) -> bool:
    return isinstance(h, str) and len(h) == 64 and all(c in "0123456789abcdef" for c in h)


def _text(v) -> bool:
    return isinstance(v, str) and bool(v.strip())


class FalsificationLayer:
    KINDS = ("stage_recorded", "null_validity_recorded", "rediscovery_registered", "rediscovery_sealed",
             "rediscovery_scored", "drift_scope_declared", "replication_recorded", "law_change_linked")

    def __init__(self):
        self.stages: dict[str, dict] = {}          # claim_id -> {n: record}
        self.null_validity: dict[str, dict] = {}
        self.rediscovery: dict[str, dict] = {}
        self.scopes: dict[str, dict] = {}
        self.replications: dict[str, list] = {}
        self.law_links: dict[str, str] = {}        # new claim -> old claim
        self.g = None

    def bind(self, g):
        self.g = g

    def _ext(self, attr):
        return next((x for x in self.g._ext.values() if hasattr(x, attr) and x is not self), None)

    def _roles(self, ident):
        cl = self._ext("access_log")
        return cl.roles.get(ident, set()) if cl else set()

    def _operator_signed(self, p, action):
        signer = Signed.from_payload(p).identity
        if "court_operator" not in self._roles(signer):
            raise GateError("recorded by the court operator")
        return self.g._signed(p, signer, action)

    def status(self, claim_id) -> str:
        st = self.stages.get(claim_id, {})
        s3 = st.get(3)
        if s3 is None:
            return "stage %d" % max(st) if st else "not started"
        if s3["basic_null"] not in self.null_validity:
            return NOT_TESTED
        return "stage %d" % max(st)

    # ---------------- cross-component preconditions ----------------
    def pre_validate(self, kind, p):
        if kind == "confirmation_submitted":
            st = json.loads(bytes.fromhex(p["statement_hex"]))
            entries = st.get("claims")
            if not isinstance(entries, list) or any(not isinstance(e, dict) or not isinstance(e.get("claim_id"), str)
                                                    for e in entries):
                raise GateError("a submission lists its claims as objects with a claim_id (FL-014)")
            for e in entries:
                cid = e.get("claim_id")
                s3 = self.stages.get(cid, {}).get(3)
                if s3 is None:
                    raise GateError(f"{cid}: confirmation follows stages 1–3 (س 2171–2174)")
                if s3["basic_null"] not in self.null_validity:
                    raise GateError(f"{cid}: {NOT_TESTED} — no confirmatory test without a valid null (س 818)")

    # ---------------- validation ----------------
    def validate(self, kind, p):
        if kind == "stage_recorded":
            st = self.g._signed(p, "founder", "record_stage")
            cid, n = st.get("claim_id"), st.get("stage")
            have = self.stages.get(cid, {})
            if n not in (1, 2, 3, 4, 5) or isinstance(n, bool):
                raise GateError("stage is 1 to 5 (س 2171–2175)")
            if n in have:
                raise GateError("each stage is recorded once")
            if n > 1 and (n - 1) not in have:
                raise GateError(f"stage {n} needs stage {n - 1} first (س 2169)")
            sl = self._ext("plans")
            if n == 1:
                if sl is None or sl.slice_station(st.get("slice")) != "Discovery":
                    raise GateError("differences are detected on a Discovery slice")
                if not _hex64(st.get("evidence_sha256")) or not _text(st.get("difference")):
                    raise GateError("stage 1 records the difference and its evidence hash")
                if st.get("basis") == "null_failure":
                    raise GateError("null failure is not a discovery (س 820)")
            elif n == 2:
                inv = self._ext("c0_rules")
                ds = sl.slice_dataset(have[1]["slice"])
                if inv is None or not any(r["dataset_id"] == ds for r in inv.c0_results):
                    raise GateError("source identification includes C0 results for the dataset (س 2172)")
                swaps = st.get("null_swaps")
                if not isinstance(swaps, list) or not swaps or not all(_text(x) for x in swaps):
                    raise GateError("source identification includes null swaps (س 2172)")
                if not _text(st.get("temporal_location")):
                    raise GateError("source identification includes the temporal location (س 2172)")
            elif n == 3:
                cc, court, dl = self._ext("cards"), self._ext("identities"), self._ext("null_cards")
                if cc is None or cid not in cc.cards or court is None or cid not in court.identities:
                    raise GateError("claim formulation: card and Claim ID registered (س 2173)")
                bn = st.get("basic_null")
                if bn in DIAGNOSTIC_ONLY:
                    raise GateError("N-c is diagnostic only, never a confirmatory null (§7 #11)")
                if dl is None or bn not in dl.null_cards:
                    raise GateError("the basic null has a card accepted by the founder (س 815, 2312; ق-06)")
                if not _text(st.get("justification")):
                    raise GateError("a JUSTIFIED basic null for the target quantity (س 815)")
                for k in ("alternatives", "sensitivity"):
                    if not isinstance(st.get(k), list) or any(not _text(x) for x in st[k]):
                        raise GateError(f"{k} is a list (empty when none is available, س 816–817)")
                if any(x in DIAGNOSTIC_ONLY for x in st["alternatives"]):
                    raise GateError("N-c is diagnostic only (§7 #11)")
            elif n == 4:
                ev = self._ext("opened_units")
                if ev is None or not any(cid in ev.submissions[u]["claim_ids"] for u in ev.opened_units):
                    raise GateError("stage 4 is confirmation on an opened Final unit (س 2174; layer 6)")
            elif n == 5:
                cc = self._ext("cards")
                ic = st.get("interpretation_claim_id")
                if cc is None or ic not in cc.cards or cc.cards[ic][-1]["path"] not in INTERPRETATION_PATHS:
                    raise GateError("interpretation goes through a separate claim on path د1 or د2 (س 2175)")
                if ic == cid:
                    raise GateError("no path counts as evidence for another: interpretation is a separate claim (س 326)")
        elif kind == "null_validity_recorded":
            st = self.g._signed(p, "founder", "record_null_validity")
            dl = self._ext("null_cards")
            nm = st.get("null_model")
            if dl is None or nm not in dl.null_cards:
                raise GateError("validity is recorded for a null model with an accepted card")
            if nm in DIAGNOSTIC_ONLY:
                raise GateError("N-c is diagnostic only (§7 #11)")
            if nm in self.null_validity:
                raise GateError("validity is recorded once per null model")
            ctl = self._ext("controls")
            if ctl is None:
                raise GateError("null validity needs the controls registry (ق-06; س 2313)")
            if set(st) - {"action", "nonce", "null_model", "control_results"}:
                raise GateError("null validity cites control_results only; no free-standing evidence hashes (R1-01)")
            ctl.validity_evidence(nm, st.get("control_results"))
        elif kind == "rediscovery_registered":
            st = self.g._signed(p, "founder", "register_rediscovery")
            rid = st.get("run_id")
            sl = self._ext("plans")
            if not rid or rid in self.rediscovery:
                raise GateError("run needs a new run_id")
            if sl is None or sl.slice_station(st.get("slice")) != "Discovery":
                raise GateError("blind rediscovery runs on Discovery only (س 2195)")
            c = st.get("criterion") or {}
            if not _text(c.get("text")) or c.get("sha256") != content_sha256(c["text"]):
                raise GateError("a registered match criterion, with its hash (س 2197)")
            if not isinstance(st.get("shared_tools"), list):
                raise GateError("shared tool dependencies are documented (س 2198)")
            if not isinstance(st.get("audit_sample_size"), int) or isinstance(st["audit_sample_size"], bool) \
                    or st["audit_sample_size"] < 1:
                raise GateError("an audit sample is declared (س 2199)")
        elif kind == "rediscovery_sealed":
            signer = Signed.from_payload(p).identity
            if "discovery_participant" not in self._roles(signer):
                raise GateError("deliverables are sealed by the discovery participant who made them")
            st = self.g._signed(p, signer, "seal_rediscovery")
            r = self.rediscovery.get(st.get("run_id"))
            if r is None or r.get("sealed"):
                raise GateError("seal a registered, unsealed run once (س 2196)")
            if not _hex64(st.get("deliverables_sha256")):
                raise GateError("sealed deliverables carry their hash")
        elif kind == "rediscovery_scored":
            st = self._operator_signed(p, "score_rediscovery")
            r = self.rediscovery.get(st.get("run_id"))
            if r is None or not r.get("sealed"):
                raise GateError("scoring only after the deliverables are sealed (س 2196)")
            if r.get("scored"):
                raise GateError("scored once")
            if st.get("criterion_sha256") != r["criterion"]["sha256"]:
                raise GateError("scoring uses the registered criterion (س 2197)")
            if st.get("tag") != PROCESS_TEST:
                raise GateError("blind rediscovery is a process test and never counts as confirmation (س 2195)")
            if not isinstance(st.get("matched"), int) or not isinstance(st.get("planted"), int) \
                    or isinstance(st["matched"], bool) or not 0 <= st["matched"] <= st["planted"]:
                raise GateError("score: matched out of planted")
        elif kind == "drift_scope_declared":
            st = self.g._signed(p, "founder", "declare_drift_scope")
            cid = st.get("claim_id")
            cc = self._ext("cards")
            if cc is None or cid not in cc.cards:
                raise GateError("scope is declared for a registered claim")
            if cid in self.scopes:
                raise GateError("the declared scope is frozen (no retroactive justification, س 2209)")
            if self.replications.get(cid):
                raise GateError("the scope is declared before any replication result (س 2209)")
            if st.get("drift_type") not in DRIFT_TYPES:
                raise GateError(f"drift type is one of the five (ق-14): {DRIFT_TYPES}")
            pf = st.get("predicts_failure_when")
            if not isinstance(pf, list) or any(not _text(x) for x in pf):
                raise GateError("predicts_failure_when lists the conditions the scope predicts (empty if none)")
        elif kind == "replication_recorded":
            st = self._operator_signed(p, "record_replication")
            cid = st.get("claim_id")
            if cid not in self.scopes:
                raise GateError("replication is judged against a scope declared before it (س 2209–2210)")
            if st.get("outcome") not in ("replicated", "failed"):
                raise GateError("outcome is replicated or failed")
            if "law_changed" in st or "reinterpretation" in st:
                raise GateError("'the law changed' is a new claim (س 2210), not a re-reading of this result")
            if not _text(st.get("condition")) or not _hex64(st.get("evidence_sha256")):
                raise GateError("replication records the observed condition and evidence hash")
        elif kind == "law_change_linked":
            st = self.g._signed(p, "founder", "link_law_change")
            new, old = st.get("new_claim_id"), st.get("old_claim_id")
            cc = self._ext("cards")
            if cc is None or new not in cc.cards or old not in cc.cards or new == old:
                raise GateError("'the law changed' is a NEW registered claim linked to the old one (س 2210)")
            if not any(r["status"] == "فشل" for r in self.replications.get(old, [])):
                raise GateError("a law change follows a recorded failed replication of the old claim")
            if new in self.law_links:
                raise GateError("already linked")

    def apply(self, kind, p):
        st = json.loads(bytes.fromhex(p["statement_hex"]))
        if kind == "stage_recorded":
            self.stages.setdefault(st["claim_id"], {})[st["stage"]] = st
        elif kind == "null_validity_recorded":
            self.null_validity[st["null_model"]] = st
        elif kind == "rediscovery_registered":
            self.rediscovery[st["run_id"]] = {**st, "sealed": False, "scored": False}
        elif kind == "rediscovery_sealed":
            r = self.rediscovery[st["run_id"]]
            r.update(sealed=True, deliverables_sha256=st["deliverables_sha256"])
        elif kind == "rediscovery_scored":
            self.rediscovery[st["run_id"]].update(scored=True, score=st)
        elif kind == "drift_scope_declared":
            self.scopes[st["claim_id"]] = st
        elif kind == "replication_recorded":
            sc = self.scopes[st["claim_id"]]
            if st["outcome"] == "replicated":
                status = "تكرّر"
            elif st["condition"] in sc["predicts_failure_when"]:
                status = "فشل متوقَّع ضمن النطاق المعلن"
            else:
                status = "فشل"                                                          # س 2210
            self.replications.setdefault(st["claim_id"], []).append({**st, "status": status})
        elif kind == "law_change_linked":
            self.law_links[st["new_claim_id"]] = st["old_claim_id"]

    def commit(self, kind, s: Signed):
        return self.g._commit(kind, s.to_payload())
