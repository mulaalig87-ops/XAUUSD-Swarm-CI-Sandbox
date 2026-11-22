"""Layer 6 — evidence economy (WP8-06; spec WP7-01 §2.6, candidate §8, WP7-05 §2 and §5).

SYNTHETIC DATA ONLY. This layer gates the passage from selection to confirmation and the single
opening of Final. It does not compute statistics on data; the court (layer 9) rules.

Already built elsewhere and only linked here: Claim ID / Test Instance ID, one primary instance,
post-opening instances descriptive (§8.4.1; court.py); family structure A/B, Holm/FWER, freezing
blocked until A/B and FWER/FDR are decided, one row per Claim ID, "confirmed if rejected in at
least one path", divergence shown (§8.4, س 686–689; court.py); error control declared per batch
(س 612; court output "FWER per batch"); code-integrity-only runs kept out of confirmation and of
the knowledge classes (§8.7, س 713–716; court.py, knowledge.py).

Implemented here (each cites its source):
- Gates (س 540): screening on Discovery/Validation, confirmation on Final. A claim reaches the
  confirmation gate only through a founder-signed confirmation submission (FD-01-D12) that names,
  per claim, the path (Z/G-Z/R, CS-05-06) and the screening slices it was selected on.
- Separation conditions (س 542–546), checked mechanically at submission:
  1. separate and newer data: the confirmation unit is Final slices only, every one starting at or
     after the end of every screening slice cited (س 542);
  2. an embargo does not prove independence: no "embargo" basis is accepted in place of (1) (س 543);
  3. full freeze: claim card, Claim ID identity, split design (design A on Final, س 473), at least one
     primary test instance on the unit, and the family's court rules all recorded before (س 544);
  4. selection from Discovery or Validation: each cited screening slice has station Discovery or
     Validation, and the claim was opened there (س 545);
  5. the family includes everything submitted: a submission is final; every submitted claim must be
     opened on the unit before Final is opened, so it enters the court scope (س 546).
- Final consumption (س 550–556; layers 6 and 8): protocol frozen (court rules frozen) before
  opening; all claims of the batch opened together, ATOMICALLY (review R1-01): a claim can never be
  opened on a Final slice by itself; the single founder-signed final_opened event opens every
  claim of the batch in one ledger entry, after running the same checks every layer applies to a
  claim opening (claims charter, custody decision, slice plan/design, court rules), so no claim's
  Final information can exist while another batch claim is unopened; the opening manifest (claim,
  slice, card version and hash for every claim) is INSIDE the founder-signed statement, so the
  signature binds the exact instructions committed (review R2-01); Final opened ONCE per unit, after an adequate
  adequacy report (س 526); nothing more can be opened, submitted or reported on an opened unit; the
  court cannot rule on a family whose Final unit is not opened; a branch of a claim confirmed on a
  unit is tested only on a later unit (س 555). "No new test under another name" (س 554, 606) is
  enforced by the court identity registry. Forward commitment (س 556): «غير معرّف إجرائيًا»
  (CS-03-05) — not built; Forward cannot be planned (layer 5).
- Adequacy report (س 629–651), recorded by custody (FD-01-D13), one per unit, never redone:
  effective units after actual purge, coverage, censoring ratio and tie ratio where the tie count
  includes the ambiguous event (§7 #15), NO latent-cases item (س 635 not activated, §7 #1), number of
  claims and of registered test instances per claim (cross-checked with the court registry),
  detectable effect, family size and procedure (must equal the batch and the frozen court rules: no
  reduction of power or significance, س 643), exclusion log. Constraints: no data from Discovery or
  Validation (TP-05 (a), TP-60.13); every exclusion cites a rule registered by the founder before the
  report, with reason and count (س 651, 576); no exposed slice; inadequacy is a result (س 646): an
  inadequate report is recorded and Final is not opened on it (FD-01-D14).
- Merging non-exposed slices is decided before opening (س 574): founder-signed, Final slices of one
  dataset, none exposed.
NOT implemented / open (flagged): the three budgets have no units in the sources (س 539) — only the
gates and separation are enforced; adequacy criteria ("detectable effect" method) are data;
Reusable Holdout deferred (س 616); stop state [مبدئي] undefined (س 617); R share and FWER/FDR [لاحق]
(س 610, 618); Forward commitment (CS-03-05); lifetime error control (س 612).
"""
from __future__ import annotations

import json
import math

from .charter import GateError
from .identity import Signed
from .numeric import finite_real

REPORT_FIELDS = ("action", "nonce", "unit_id", "source_slices", "effective_units_after_purge", "coverage",
                 "censoring_ratio", "tie_ratio", "tie_includes_ambiguous", "claims", "test_instances_per_claim",
                 "detectable_effect", "family_size", "procedure", "alpha", "exclusions", "verdict", "time")
VERDICTS = ("adequate", "inadequate")
SCREENING_STATIONS = ("Discovery", "Validation")


def _num(x) -> bool:
    return finite_real(x)


class EvidenceLayer:
    KINDS = ("exclusion_rule_registered", "slices_merge_decided", "confirmation_submitted", "adequacy_reported",
             "final_opened")

    def __init__(self):
        self.exclusion_rules: dict[str, dict] = {}
        self.merges: dict[str, dict] = {}          # unit_id -> decision
        self.submissions: dict[str, dict] = {}     # unit_id -> submission
        self.reports: dict[str, dict] = {}         # unit_id -> report
        self.opened_units: dict[str, dict] = {}    # unit_id -> final_opened statement
        self.g = None

    def bind(self, g):
        self.g = g

    # ---------------- helpers ----------------
    def _ext(self, attr):
        return next((x for x in self.g._ext.values() if hasattr(x, attr) and x is not self), None)

    def _sl(self):
        sl = self._ext("plans")
        if sl is None:
            raise GateError("layer 6 needs the slicing layer (layer 5)")
        return sl

    def _custody_signed(self, p, action):
        cl = self._ext("access_log")
        signer = Signed.from_payload(p).identity
        if cl is None or "custody" not in cl.roles.get(signer, set()):
            raise GateError(f"{signer!r} is not custody")
        return self.g._signed(p, signer, action)

    def _exposed(self, slice_id) -> bool:
        cc = self._ext("openings")
        return slice_id in self.g._s.slices or (cc is not None and any(s == slice_id for (_c, s) in cc.openings))

    def unit_of(self, slice_id):
        for uid, sub in self.submissions.items():
            if slice_id in sub["unit_slices"]:
                return uid
        return None

    def _unit_slices(self, unit_id, slices):
        """A unit is one Final slice, or several merged by a prior decision (س 574)."""
        sl = self._sl()
        if not isinstance(slices, list) or not slices or len(set(slices)) != len(slices):
            raise GateError("a confirmation unit names its Final slices")
        for s in slices:
            if sl.slice_station(s) != "Final":
                raise GateError(f"confirmation is on Final slices only (س 524); {s!r} is {sl.slice_station(s)}")
        if len(slices) > 1:
            m = self.merges.get(unit_id)
            if m is None or sorted(m["slices"]) != sorted(slices):
                raise GateError("several slices form one unit only by a merge decided before opening (س 574)")
        return slices

    def _family_of_slice(self, s):
        cu = self._ext("decisions")
        d = cu.decisions.get(s) if cu else None
        return d["family"] if d else None

    # ---------------- cross-component preconditions ----------------
    def pre_validate(self, kind, p):
        if kind == "claim_opened":
            if self._sl().slice_station(p.get("slice")) == "Final":
                raise GateError("a claim is never opened on Final by itself: Final is opened for the whole batch "
                                "in one final_opened event, through the confirmation gate (س 540, 551–552)")
        elif kind == "court_ruling":
            st = json.loads(bytes.fromhex(p["statement_hex"]))
            fam = st.get("family")
            for uid, sub in self.submissions.items():
                if sub["family"] == fam and uid not in self.opened_units:
                    raise GateError("the court rules on a Final batch only after Final is opened for the whole batch (س 551–552)")

    # ---------------- validation ----------------
    def validate(self, kind, p):
        sl = self._sl()
        if kind == "exclusion_rule_registered":
            st = self.g._signed(p, "founder", "register_exclusion_rule")
            rid = st.get("rule_id")
            if not rid or rid in self.exclusion_rules:
                raise GateError("exclusion rule needs a new rule_id")
            if not str(st.get("text", "")).strip():
                raise GateError("exclusion rule needs its text (س 651)")
        elif kind == "slices_merge_decided":
            st = self.g._signed(p, "founder", "decide_slice_merge")
            uid, slices = st.get("unit_id"), st.get("slices")
            if not uid or uid in self.merges or uid in self.submissions:
                raise GateError("merge decision needs a new unit_id, before its submission")
            if not isinstance(slices, list) or len(slices) < 2 or len(set(slices)) != len(slices):
                raise GateError("a merge names two or more distinct slices")
            if any(sl.slice_station(s) != "Final" for s in slices):
                raise GateError("only Final slices are merged into a confirmation unit")
            if len({sl.slice_dataset(s) for s in slices}) != 1:
                raise GateError("merged slices belong to one dataset")
            if any(self._exposed(s) for s in slices):
                raise GateError("no merge of exposed slices (س 645); merging is decided before opening (س 574)")
            if any(s in m["slices"] for m in self.merges.values() for s in slices):
                raise GateError("a slice belongs to one merge only")
        elif kind == "confirmation_submitted":
            st = self.g._signed(p, "founder", "submit_for_confirmation")
            uid = st.get("unit_id")
            if not uid or uid in self.submissions:
                raise GateError("a submission is final; one per unit (س 546)")
            slices = self._unit_slices(uid, st.get("unit_slices"))
            if any(self.unit_of(s) for s in slices):
                raise GateError("a slice is in one confirmation unit only")
            if any(self._exposed(s) for s in slices):
                raise GateError("the unit is exposed already (س 553)")
            fams = {self._family_of_slice(s) for s in slices}
            if fams != {st.get("family")} or None in fams:
                raise GateError("the unit's slices must carry the custody decisions of the named family")
            court = self._ext("configs")
            if court is None or st["family"] not in court.configs:
                raise GateError("full freeze: court rules for the family are frozen first (س 544, 774)")
            if str(st.get("independence_basis", "separate_and_newer")) != "separate_and_newer":
                raise GateError("an embargo does not prove independence (س 543); only separate and newer data")
            entries = st.get("claims")
            if not isinstance(entries, list) or not entries or any(
                    not isinstance(e, dict) or not isinstance(e.get("claim_id"), str) for e in entries):
                raise GateError("a submission lists its claims (objects with a claim_id)")
            ids = [e.get("claim_id") for e in entries]
            if len(set(ids)) != len(ids):
                raise GateError("each claim once per submission")
            cc, design = self._ext("cards"), self._ext("designs")
            unit_start = min(sl.slices[s]["start"] for s in slices)
            for e in entries:
                cid = e.get("claim_id")
                if cc is None or cid not in cc.cards:
                    raise GateError(f"{cid}: full freeze: claim card not registered (س 544)")
                if cid not in court.identities:
                    raise GateError(f"{cid}: full freeze: Claim ID identity not registered (س 544, 727)")
                d = design.designs.get(cid) if design else None
                if d is None or d["design"] != "A":
                    raise GateError(f"{cid}: confirmation on Final uses design A, recorded before (س 473, 481)")
                if e.get("path") not in ("Z", "G-Z", "R"):
                    raise GateError(f"{cid}: path is Z, G-Z or R (CS-05-06)")
                if not any(ti["claim_id"] == cid and ti["path"] == e["path"] and ti["slice"] in slices
                           and ti["role"] == "primary" and not ti["descriptive"] and not ti.get("code_integrity_only")
                           for ti in court.instances.values()):
                    raise GateError(f"{cid}: full freeze: a primary test instance on this unit and path is registered first (س 700)")
                scr = e.get("screening_slices")
                if not isinstance(scr, list) or not scr:
                    raise GateError(f"{cid}: selection is from Discovery or Validation (س 545): name the screening slices")
                for s in scr:
                    if sl.slice_station(s) not in SCREENING_STATIONS:
                        raise GateError(f"{cid}: screening slice {s!r} is not Discovery or Validation (س 545)")
                    if (cid, s) not in cc.openings:
                        raise GateError(f"{cid}: not opened on screening slice {s!r}; no selection there")
                    if sl.slices[s]["end"] > unit_start or sl.slice_dataset(s) != sl.slice_dataset(slices[0]):
                        raise GateError(f"{cid}: confirmation data must be separate and NEWER than {s!r} (س 542)")
                parent = e.get("branch_of")
                if parent is not None:
                    pu = [u for u, sub in self.submissions.items() if parent in sub["claim_ids"] and u in self.opened_units]
                    if not pu:
                        raise GateError(f"{cid}: branch_of names a claim not exposed on an opened Final unit")
                    last_end = max(sl.slices[s]["end"] for u in pu for s in self.submissions[u]["unit_slices"])
                    if unit_start < last_end:
                        raise GateError(f"{cid}: a branch is tested on a LATER slice (س 555)")
        elif kind == "adequacy_reported":
            st = self._custody_signed(p, "adequacy_report")
            extra = set(st) - set(REPORT_FIELDS)
            if extra:
                raise GateError(f"unknown report fields {sorted(extra)} (the latent-cases item is not activated, §7 #1)")
            miss = [k for k in REPORT_FIELDS if k not in st]
            if miss:
                raise GateError(f"adequacy report incomplete: {miss} (س 631–639)")
            uid = st["unit_id"]
            sub = self.submissions.get(uid)
            if sub is None:
                raise GateError("adequacy is reported for a submitted confirmation unit")
            if uid in self.reports:
                raise GateError("one adequacy report per unit; it is not redone (inadequacy is a result, س 646)")
            if uid in self.opened_units or any(self._exposed(s) for s in sub["unit_slices"]):
                raise GateError("the report comes before opening; no exposed slice (س 526, 645)")
            src = st["source_slices"]
            if not isinstance(src, list) or not src:
                raise GateError("the report names its source slices")
            bad = [s for s in src if self._sl().slice_station(s) in SCREENING_STATIONS]
            if bad:
                raise GateError(f"no data from Discovery or Validation in the adequacy report (س 642): {bad}")
            if set(src) != set(sub["unit_slices"]):
                raise GateError("the report's source slices are exactly the unit's slices")
            for k in ("effective_units_after_purge", "detectable_effect"):
                if not _num(st[k]) or st[k] < 0:
                    raise GateError(f"{k} must be a non-negative number")
            for k in ("coverage", "censoring_ratio", "tie_ratio"):
                if not _num(st[k]) or not 0 <= st[k] <= 1:
                    raise GateError(f"{k} must be a ratio in [0, 1]")
            if st["tie_includes_ambiguous"] is not True:
                raise GateError("the tie ratio includes the ambiguous event (§7 #15)")
            if sorted(st["claims"]) != sorted(sub["claim_ids"]) or st["family_size"] != len(sub["claim_ids"]):
                raise GateError("claims and family size equal the submitted batch: the family includes all (س 546, 636, 638)")
            court = self._ext("configs")
            reg = {c: sum(1 for t in court.instances.values() if t["claim_id"] == c) for c in sub["claim_ids"]}
            if st["test_instances_per_claim"] != reg:
                raise GateError("test instances per claim must equal the registered count (س 636)")
            cfg = court.configs[sub["family"]]
            if st["procedure"] != cfg["procedure"] or st["alpha"] != cfg["alpha_total"]:
                raise GateError("procedure and α are the frozen ones: no reduction of power or significance (س 643)")
            ex = st["exclusions"]
            if not isinstance(ex, list):
                raise GateError("exclusions is a list (possibly empty)")
            for x in ex:
                r = self.exclusion_rules.get(x.get("rule_id"))
                if r is None:
                    raise GateError("every exclusion cites a rule registered before (س 651, 576)")
                if not str(x.get("reason", "")).strip() or not isinstance(x.get("count"), int) or isinstance(
                        x.get("count"), bool) or x["count"] < 0:
                    raise GateError("every exclusion carries its reason and count (س 651)")
            if st["verdict"] not in VERDICTS:
                raise GateError("verdict is adequate or inadequate")
        elif kind == "final_opened":
            st = self.g._signed(p, "founder", "open_final")
            uid = st.get("unit_id")
            sub = self.submissions.get(uid)
            if sub is None:
                raise GateError("Final is opened for a submitted unit")
            if uid in self.opened_units:
                raise GateError("Final is opened once (س 526, 552)")
            rep = self.reports.get(uid)
            if rep is None or rep["verdict"] != "adequate":
                raise GateError("Final opens only after an adequate adequacy report (س 526, 646)")
            if set(p) != {"signer", "statement_hex", "signature_hex"}:
                raise GateError("final_opened carries only the founder-signed statement; no unsigned fields (R2-01)")
            ops = st.get("openings")
            if not isinstance(ops, list) or sorted(o.get("claim_id") for o in ops) != sorted(sub["claim_ids"]):
                raise GateError("all claims of the batch are opened together, each once (س 551)")
            court = self._ext("configs")
            cc = self._ext("openings")
            for o in ops:
                if set(o) != {"claim_id", "slice", "version", "card_sha256"} or o["slice"] not in sub["unit_slices"]:
                    raise GateError("each opening names claim, a slice of the unit, and the bound card version and hash")
                path = next(e["path"] for e in sub["claims"] if e["claim_id"] == o["claim_id"])
                if not any(t["claim_id"] == o["claim_id"] and t["slice"] == o["slice"] and t["path"] == path
                           and t["role"] == "primary" and not t["descriptive"] for t in court.instances.values()):
                    raise GateError(f"{o['claim_id']}: opened on the slice of its pre-registered primary instance")
                for x in dict.fromkeys(self.g._ext.values()):      # every layer's opening checks, except this gate
                    pre = getattr(x, "pre_validate", None)
                    if pre and x is not self:
                        pre("claim_opened", o)
                cc.validate("claim_opened", o)

    def apply(self, kind, p):
        st = json.loads(bytes.fromhex(p["statement_hex"]))
        if kind == "exclusion_rule_registered":
            self.exclusion_rules[st["rule_id"]] = st
        elif kind == "slices_merge_decided":
            self.merges[st["unit_id"]] = st
        elif kind == "confirmation_submitted":
            self.submissions[st["unit_id"]] = {**st, "claim_ids": [e["claim_id"] for e in st["claims"]]}
        elif kind == "adequacy_reported":
            self.reports[st["unit_id"]] = st
        elif kind == "final_opened":
            cc = self._ext("openings")
            for o in st["openings"]:                      # one ledger entry opens the whole batch (R1-01)
                cc.apply("claim_opened", o)
            self.opened_units[st["unit_id"]] = st

    # ---------------- API ----------------
    def commit(self, kind, s: Signed):
        return self.g._commit(kind, s.to_payload())

    def final_manifest(self, unit_id: str) -> list:
        """The opening manifest the founder signs (R2-01): for each batch claim, the slice of its
        pre-registered primary instance on the unit and the current card version and hash."""
        from .claims import card_hash
        sub, court, cc = self.submissions.get(unit_id), self._ext("configs"), self._ext("cards")
        if sub is None:
            raise GateError("unknown unit")
        ops = []
        for e in sub["claims"]:
            sl = next((t["slice"] for t in court.instances.values() if t["claim_id"] == e["claim_id"]
                       and t["slice"] in sub["unit_slices"] and t["path"] == e["path"] and t["role"] == "primary"
                       and not t["descriptive"]), None)
            v = cc.cards.get(e["claim_id"], [])
            ops.append({"claim_id": e["claim_id"], "slice": sl, "version": len(v),
                        "card_sha256": card_hash(v[-1]) if v else ""})
        return ops

    def open_final(self, s: Signed):
        """Commit the founder-signed 'open_final' statement {unit_id, openings: manifest}. Nothing is
        added outside the signature; the validator re-checks the manifest against fresh state."""
        return self.g._commit("final_opened", s.to_payload())
