"""Layer 5 — transform freezing, slicing, purge/embargo and availability time (WP8-05; spec WP7-01
§2.5, candidate §6.4–§6.5, §7).

SYNTHETIC DATA ONLY. The number and size of slices are data (س 432, CS-03-07): no defaults exist;
the caller states them, and real data stays locked in layer 4 (OD-10).

Implemented (each cites its source):
- Slice plan (س 431): custody sets the boundaries by measures that carry no results. Allowed bases:
  calendar time or observation count, which are fixed before any outcome is computed.
  ⟦قرار Claude بتفويض المؤسس، FD-01⟧ FD-01-D04. Slices are contiguous intervals, inside the
  inventoried range, non-overlapping, each with a station (§7). Discovery, Validation and Final can
  be planned; Forward cannot: its commitment is «غير معرّف في المعمارية» (CS-03-05).
- Slices need a frozen plan before a custody decision (blinding parameters) is recorded for them;
  the decision's boundaries must equal the plan's (links layer 3 to layer 5; FD-01-D04).
- Information intervals (س 463–467): I_i = [t_i − L_i, t_i], O_i = [t_i, τ_i], decision moment t_i,
  shared group g_i. t_i is the AVAILABILITY time of the last observation used (س 491–492).
- Availability time (س 491–497, 504–514): with arrival times, t_avail = t_arrival; without them,
  t_avail = t_market + an explicit per-source latency assumption, tagged "assumed"; no default
  latency exists. Every claim relying on an assumed latency carries the tag «كمون مفترض» (س 514);
  its sensitivity plan must cover the four dimensions (س 509–513). The analysis itself is [بيانات].
- Designs A/B/C (س 471–475), common rules (س 478–481), check order (س 449):
  1) check outcome-interval and group overlaps; 2) purge what actually overlaps; 3) embargo;
  4) block-level uncertainty for dependence (flagged for layer 8; not computed here).
  Design C is descriptive in Discovery only; Final always uses design A.
  The combination rule (purge ≥ input window + max outcome window) applies only in design B, only
  when exact intervals cannot be computed, with a recorded reason ("حين يبررها التصميم", §7 #10).
  A shared group is never split between training and evaluation (س 478): members of a group that
  has any evaluation sample are removed from training.
  Statistical dependence between non-overlapping neighbours is NOT deleted (س 479).
- The design and its rules are recorded with each claim before it is opened (س 481): the opening
  is where the claims layer freezes the card version for a slice. Recorder: the founder (same
  authority as claim registration). FD-01-D05.
- audit_split(): an independent re-check of a split result. The result carries its frozen
  parameters (design, embargo, combination) and their hash; the audit checks them against the
  recorded design and recomputes EVERY rule (groups, design A/B overlaps, embargo, combination),
  so a planted insufficient purge, a shortened embargo, a dropped combination rule or a parameter
  mismatch is reported (TP-28; review R1-02).
- observation_count boundaries are integers (review R1-05).
- The audit also rebuilds the expected split from the samples, the evaluation part and the
  parameters, and compares it in full: every sample is in exactly one of training, evaluation or
  removed; no duplicate ids; nothing removed without a rule; nothing kept that a rule removes
  (review R2-01).
NOT implemented / open: embargo length, latency values, slice count/size (all [بيانات]);
block-level uncertainty (layer 8); Forward commitment (CS-03-05).
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass

from .charter import GateError
from .identity import Signed
from .inventory import check_times, content_sha256
from .numeric import finite_real

STATIONS = ("Discovery", "Validation", "Final", "Forward")
PLANNABLE = ("Discovery", "Validation", "Final")
BASES = ("calendar_time", "observation_count")
DESIGNS = ("A", "B", "C")
DESIGN_STATIONS = {"A": ("Discovery", "Validation", "Final"), "B": ("Discovery", "Validation"), "C": ("Discovery",)}
LATENCY_DIMENSIONS = ("between_sources", "across_periods", "irregular_arrival", "recording_delay")  # س 510–513
ASSUMED_LATENCY_TAG = "كمون مفترض"


class LeakError(GateError):
    pass


def _num(x) -> bool:
    return finite_real(x)


# ======================= availability time =======================================================
def availability_time(obs: dict, latency: dict | None = None) -> tuple[float, bool]:
    """(t_avail, assumed). With t_arrival: real arrival, not assumed. Without: t_market + the declared
    latency of obs['source'] (no default; س 494, 507)."""
    check_times(obs)                                                    # R1-01
    if "t_arrival" in obs:
        return float(obs["t_arrival"]), False
    src = obs.get("source")
    if not latency or src not in latency or not _num(latency[src]) or latency[src] < 0:
        raise GateError(f"no arrival time and no declared latency for source {src!r} (س 494)")
    return float(obs["t_market"]) + latency[src], True


def assert_no_leak(t_decision: float, input_avail_times) -> None:
    """No information unavailable at the decision moment (س 469, 491–492)."""
    times = list(input_avail_times)
    if not _num(t_decision) or any(not _num(t) for t in times):    # S3-03: NaN made every comparison False
        raise LeakError("decision and availability times must be finite numbers; an unknown time is not 'available'")
    late = [t for t in times if t > t_decision]
    if late:
        raise LeakError(f"{len(late)} input(s) not available at the decision moment (س 492)")


# ======================= samples and splits ======================================================
@dataclass(frozen=True)
class Sample:
    sid: str
    t: float            # decision moment (availability time)
    L: float            # input window length
    tau: float          # outcome resolution / censoring time
    group: str | None = None

    def __post_init__(self):
        if not (_num(self.t) and _num(self.L) and _num(self.tau)) or self.L < 0 or self.tau < self.t:
            raise GateError(f"invalid intervals for sample {self.sid}")

    @property
    def I(self):
        return (self.t - self.L, self.t)

    @property
    def O(self):
        return (self.t, self.tau)


def _overlap(a, b) -> bool:
    return a[0] <= b[1] and b[0] <= a[1]


def split(samples, eval_ids, design: str, *, embargo: float = 0.0, combination: dict | None = None) -> dict:
    """Training/evaluation split under design A, B or C. Returns
    {design, train, eval, removed: {sid: reason}, steps, descriptive_only, block_uncertainty}.
    combination: {"reason": "..."} enables the combination rule (design B only)."""
    if design not in DESIGNS:
        raise GateError("design is A, B or C (س 471–475)")
    if not _num(embargo) or embargo < 0:
        raise GateError("embargo must be a non-negative number")
    if combination is not None and (design != "B" or not str(combination.get("reason", "")).strip()):
        raise GateError("the combination rule applies only in design B, with a recorded reason (س 480; §7 #10)")
    if embargo > 0 and design != "B":
        raise GateError("embargo after the block belongs to design B (س 473); not applied silently elsewhere")
    by = {s.sid: s for s in samples}
    if len(by) != len(samples):
        raise GateError("duplicate sample ids")
    unknown = [i for i in eval_ids if i not in by]
    if unknown or len(set(eval_ids)) != len(eval_ids):
        raise GateError(f"evaluation ids must be unique known samples; unknown: {unknown}")
    ev = [by[i] for i in eval_ids]
    if not ev:
        raise GateError("empty evaluation part")
    evset = set(eval_ids)
    cand = [s for s in samples if s.sid not in evset]
    removed, steps = {}, []
    t_start = min(s.t for s in ev)
    block = (t_start, max(s.tau for s in ev))
    eval_O = [s.O for s in ev]

    # step 1: overlap check (outcome intervals and shared groups) — س 449
    groups_in_eval = {s.group for s in ev if s.group is not None}
    steps.append("1:overlap_check")
    # step 2: purge what actually overlaps
    for s in cand:
        if s.group is not None and s.group in groups_in_eval:
            removed[s.sid] = "shared_group (س 478)"
            continue
        if design == "A":
            if s.t >= t_start:
                removed[s.sid] = "after_evaluation_start (design A: training before evaluation)"
            elif s.tau >= t_start:
                removed[s.sid] = "unresolved_before_evaluation (τ_j ≥ t_start)"
        elif design == "B":
            if s.t < block[0] and _overlap(s.O, block):
                removed[s.sid] = "O_j overlaps evaluation block"
            elif s.t > block[0] and any(_overlap(s.I, o) for o in eval_O):
                removed[s.sid] = "I_j reads evaluation outcome intervals"
            elif any(_overlap(s.O, o) or _overlap(s.I, o) for o in eval_O):
                removed[s.sid] = "interval overlaps evaluation outcome intervals"
    steps.append("2:purge_overlaps")
    if combination is not None:
        W = max(s.L for s in samples) + max(s.tau - s.t for s in samples)
        for s in cand:
            if s.sid not in removed and block[0] - W <= s.t <= block[1] + W:
                removed[s.sid] = "combination_rule (conservative; may remove legitimate history, س 480)"
        steps.append("2b:combination_rule")
    # step 3: embargo after the block (design B)
    if design == "B" and embargo > 0:
        for s in cand:
            if s.sid not in removed and block[1] < s.t <= block[1] + embargo:
                removed[s.sid] = "embargo"
    steps.append("3:embargo")
    # step 4: block-level uncertainty for dependence — layer 8
    steps.append("4:block_uncertainty_flagged_for_layer_8")
    train = [s.sid for s in cand if s.sid not in removed]
    params = split_params(design, embargo, combination)
    return {"design": design, "train": train, "eval": list(eval_ids), "removed": removed, "steps": steps,
            "descriptive_only": design == "C", "block_uncertainty": "required (س 479); computed in layer 8",
            "params": params, "params_sha256": content_sha256(params)}


def split_params(design, embargo=0.0, combination=None) -> dict:
    return {"design": design, "embargo": float(embargo),
            "combination": None if combination is None else str(combination.get("reason", "")).strip()}


def params_from_record(rec: dict) -> dict:
    """Split parameters as recorded with the claim (split_design_recorded)."""
    r = rec.get("rules") or {}
    return split_params(rec["design"], r.get("embargo", 0.0), r.get("combination"))


def audit_split(samples, result: dict, recorded: dict | None = None) -> list[str]:
    """Independent re-check of a split (TP-28; review R1-02). Recomputes every rule from the
    samples and the result's parameters; with `recorded` (the claim's split_design_recorded
    statement) it also checks that the parameters used are the recorded ones. Returns violations."""
    out = []
    p = result.get("params") or {}
    if result.get("params_sha256") != content_sha256(p):
        out.append("split parameters do not match their hash")
    if p.get("design") != result.get("design"):
        out.append("result design differs from its parameters")
    if recorded is not None and p != params_from_record(recorded):
        out.append(f"split parameters {p} differ from the recorded design {params_from_record(recorded)}")
    by = {s.sid: s for s in samples}
    if len(by) != len(samples):
        return out + ["duplicate ids among the samples"]
    ev_ids, tr_ids = list(result["eval"]), list(result["train"])
    rm_ids = list((result.get("removed") or {}).keys())
    for name, ids in (("evaluation", ev_ids), ("training", tr_ids)):          # R2-01: uniqueness
        dup = sorted({i for i in ids if ids.count(i) > 1})
        if dup:
            out.append(f"duplicate ids in {name}: {dup}")
    for a, b, na, nb in ((ev_ids, tr_ids, "evaluation", "training"), (ev_ids, rm_ids, "evaluation", "removed"),
                         (tr_ids, rm_ids, "training", "removed")):
        both = sorted(set(a) & set(b))
        if both:
            out.append(f"samples in both {na} and {nb}: {both}")
    blank = sorted(k for k, v in (result.get("removed") or {}).items() if not str(v).strip())
    if blank:
        out.append(f"removed without a stated reason: {blank}")
    missing = [i for i in ev_ids + tr_ids + rm_ids if i not in by]
    if missing:
        return out + [f"unknown sample ids {missing}"]
    unplaced = sorted(set(by) - set(ev_ids) - set(tr_ids) - set(rm_ids))      # R2-01: completeness
    if unplaced:
        out.append(f"samples missing from the split (neither training, evaluation nor removed with a reason): {unplaced}")
    ev, tr = [by[i] for i in ev_ids], [by[i] for i in tr_ids]
    if not ev:
        return out + ["empty evaluation part"]
    d, emb, comb = p.get("design"), float(p.get("embargo") or 0.0), p.get("combination")
    if d == "C" and result.get("descriptive_only") is not True:
        out.append("design C result is not marked descriptive-only")
    start, end = min(e.t for e in ev), max(e.tau for e in ev)
    eval_groups = {e.group for e in ev if e.group is not None}
    W = (max(s.L for s in samples) + max(s.tau - s.t for s in samples)) if comb else None
    expected_removed = set()
    for s in samples:
        if s.sid in ev_ids:
            continue
        why = []
        if s.group is not None and s.group in eval_groups:
            why.append("shared group split across partitions (س 478)")
        if d == "A" and (s.t >= start or s.tau >= start):
            why.append("not resolved before evaluation starts (design A)")
        if d == "B":
            if s.t < start and s.tau >= start:
                why.append("O_j overlaps the evaluation block")
            if any(s.t - s.L <= e.tau and e.t <= s.t for e in ev):
                why.append("I_j reads an evaluation outcome interval")
            if any(s.t <= e.tau and e.t <= s.tau for e in ev):
                why.append("O_j overlaps an evaluation outcome interval")
            if emb > 0 and end < s.t <= end + emb:
                why.append(f"inside the embargo ({emb}) after the block")
            if W is not None and start - W <= s.t <= end + W:
                why.append("inside the combination-rule window")
        if why:
            expected_removed.add(s.sid)
            if s.sid in tr_ids:
                out.append(f"{s.sid}: " + "; ".join(why))
    wrongly = sorted(set(rm_ids) - expected_removed)                           # R2-01: full comparison
    if wrongly:
        out.append(f"removed although no rule removes them (eligible training dropped): {wrongly}")
    return out


# ======================= ledger component ========================================================
class SlicingLayer:
    KINDS = ("slice_plan_frozen", "split_design_recorded")

    def __init__(self):
        self.plans: dict[str, dict] = {}          # plan_id -> plan
        self.slices: dict[str, dict] = {}         # slice_id -> {plan_id, dataset_id, station, start, end}
        self.designs: dict[str, dict] = {}        # claim_id -> design record
        self.g = None

    def bind(self, g):
        self.g = g

    def _inv(self):
        return next((x for x in self.g._ext.values() if hasattr(x, "inventories")), None)

    def slice_station(self, slice_id):
        s = self.slices.get(slice_id)
        return s["station"] if s else None

    def slice_dataset(self, slice_id):
        s = self.slices.get(slice_id)
        return s["dataset_id"] if s else None

    @staticmethod
    def boundaries_text(sl: dict) -> str:
        return json.dumps({"basis": sl["basis"], "start": sl["start"], "end": sl["end"]}, sort_keys=True)

    # ---------------- cross-component preconditions ----------------
    def pre_validate(self, kind, p):
        if kind == "custody_decision":
            st = json.loads(bytes.fromhex(p["statement_hex"]))
            sl = self.slices.get(st.get("slice"))
            if sl is None:
                raise GateError("slice must be in a frozen slice plan before its custody decision (س 431)")
            if st.get("boundaries") != self.boundaries_text(sl):
                raise GateError("custody decision boundaries must equal the frozen plan's")
        elif kind == "claim_opened":
            if p.get("claim_id") not in self.designs:
                raise GateError("split design and its rules must be recorded with the claim before opening (س 481)")
            d, stn = self.designs[p["claim_id"]], self.slice_station(p.get("slice"))
            if stn is not None and stn not in DESIGN_STATIONS[d["design"]]:
                raise GateError(f"design {d['design']} is not allowed at station {stn} (س 471–475)")

    # ---------------- validation ----------------
    def validate(self, kind, p):
        if kind == "slice_plan_frozen":
            inv_layer = self._inv()
            if inv_layer is None:
                raise GateError("slicing needs layer 4")
            st = inv_layer._custody_signed(p, "slice_plan")                 # custody sets boundaries (صل-26)
            pid, ds = st.get("plan_id"), st.get("dataset_id")
            if not pid or pid in self.plans:
                raise GateError("slice plan needs a new plan_id")
            if any(pl["dataset_id"] == ds for pl in self.plans.values()):
                raise GateError("this dataset already has a frozen slice plan")
            inv = inv_layer.inventories.get(ds)
            if inv is None:
                raise GateError("slicing follows the inventory (layer 4)")
            if st.get("basis") not in BASES:
                raise GateError("boundaries use measures that carry no results (س 431): calendar_time or observation_count")
            sls = st.get("slices")
            if not isinstance(sls, list) or not sls:
                raise GateError("the number and size of slices are data (س 432): state them explicitly")
            lo, hi = (inv["t_first"], inv["t_last"]) if st["basis"] == "calendar_time" else (0, inv["n_observations"])
            prev_end, seen = None, set()
            for s in sls:
                if s.get("station") == "Forward":
                    raise GateError("Forward: commitment «غير معرّف في المعمارية» (CS-03-05); not plannable")
                if s.get("station") not in PLANNABLE:
                    raise GateError("unknown station (§7)")
                sid = s.get("slice_id")
                if not sid or sid in seen or sid in self.slices:
                    raise GateError("slice ids are unique")
                seen.add(sid)
                if not (_num(s.get("start")) and _num(s.get("end"))) or s["start"] >= s["end"]:
                    raise GateError("each slice is an interval start < end")
                if st["basis"] == "observation_count" and not (
                        isinstance(s["start"], int) and isinstance(s["end"], int)):
                    raise GateError("observation_count boundaries are whole numbers (R1-05)")
                if s["start"] < lo or s["end"] > hi:
                    raise GateError("slice outside the inventoried range")
                if prev_end is not None and s["start"] < prev_end:
                    raise GateError("slices are ordered and do not overlap")
                prev_end = s["end"]
        elif kind == "split_design_recorded":
            st = self.g._signed(p, "founder", "record_split_design")
            cid = st.get("claim_id")
            cc = next((x for x in self.g._ext.values() if hasattr(x, "cards")), None)
            if cc is None or cid not in cc.cards:
                raise GateError("design is recorded for a registered claim")
            if cid in self.designs:
                raise GateError("design already recorded for this claim")
            if cc is not None and any(c == cid for (c, _s) in cc.openings):
                raise GateError("design is recorded before the claim is opened (س 481)")
            d = st.get("design")
            if d not in DESIGNS:
                raise GateError("design is A, B or C")
            r = st.get("rules") or {}
            if d == "B":
                if not _num(r.get("embargo")) or r["embargo"] < 0:
                    raise GateError("design B records its embargo length (a number; value is [بيانات])")
            comb = r.get("combination")
            if comb is not None and (d != "B" or not str(comb.get("reason", "")).strip()):
                raise GateError("combination rule only in design B with a recorded reason (س 480; §7 #10)")
            lat = st.get("latency") or {}
            if lat.get("assumed"):
                if lat.get("tag") != ASSUMED_LATENCY_TAG:
                    raise GateError("a claim on assumed latency carries the tag «كمون مفترض» (س 514)")
                per = lat.get("per_source") or {}
                if not per or any(not _num(v) or v < 0 for v in per.values()):
                    raise GateError("explicit latency assumption per source (س 494)")
                if set(lat.get("sensitivity_dimensions") or []) != set(LATENCY_DIMENSIONS):
                    raise GateError("sensitivity covers the four dimensions (س 509–513)")

    def apply(self, kind, p):
        st = json.loads(bytes.fromhex(p["statement_hex"]))
        if kind == "slice_plan_frozen":
            self.plans[st["plan_id"]] = st
            for s in st["slices"]:
                self.slices[s["slice_id"]] = {"plan_id": st["plan_id"], "dataset_id": st["dataset_id"],
                                              "station": s["station"], "start": s["start"], "end": s["end"],
                                              "basis": st["basis"]}
        elif kind == "split_design_recorded":
            self.designs[st["claim_id"]] = st

    # ---------------- API ----------------
    def freeze_plan(self, inv_layer, plan_id, dataset_id, *, basis, slices):
        return self.g._commit("slice_plan_frozen", inv_layer._csign(
            {"action": "slice_plan", "plan_id": plan_id, "dataset_id": dataset_id, "basis": basis, "slices": slices}).to_payload())

    def record_design(self, s: Signed):
        return self.g._commit("split_design_recorded", s.to_payload())
