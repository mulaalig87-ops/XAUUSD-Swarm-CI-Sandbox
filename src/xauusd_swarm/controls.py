"""Cross-cutting controls axis — control registry and results (WP8-08b start; candidate س 2313,
WP7-01 §2.11; TP-07, TP-46; ق-06).

"Positive and negative controls for every tool used and for the court" (س 2313). This module holds
the REGISTRY: a control is registered before its result exists (target, polarity, the synthetic world
it runs on, and the expected outcome); its result is recorded once by the court operator, who runs
frozen code (م7-03). Null-model validity (layer 8) can cite only recorded control results of this
registry, targeting that null model, with at least one positive and one negative control, all passed
(review R1-01 of WP8-08; ق-06 "validity by controls alone").

Verifiable execution (review R2-01): a control is registered with the SHA-256 of its frozen
implementation (impl_sha256, as in FD-01-D11), the hash of the synthetic world it runs on, and a
structured expectation {metric, op, value | low, high}. A result is produced only by run_control():
it refuses any other implementation or world, runs the code twice and requires identical output
(determinism), and records the structured observation with impl and world hashes. The validator
recomputes pass/fail from the registered expectation and the recorded observation, and the evidence
hash from the observation, so a "pass" that does not follow from the observation is refused.
reverify() lets anyone holding the code and world re-execute and compare exactly.
Mandatory independent re-execution (review R3-01; FD-01-D23): a result counts toward null validity
only after an auditor INDEPENDENT of the operator who recorded it (role custody_auditor or
governance_auditor, a different identity) re-executed the registered code on the registered world
and recorded a "match" attestation bound to the result's impl, world and evidence hashes. A
"mismatch" attestation makes the result unusable for good. Same two-party pattern as the custody
vault attestation (WP8-03).
Stated limit: the ledger holds no code or world; assurance rests on two independent parties
executing the same frozen code, not on a cryptographic proof of execution.

Control matrix per tool (WP7-04 §2.1, rule R16; WP8-09): «no tool is used in Discovery or after
without a row in the matrix with a positive control, a negative control and a registered criterion;
every tool added later is added before its use». A row names the tool, at least one registered
positive and one registered negative control targeting it, the criterion (text + hash) and the cost
metric ("each layer proves its utility with a positive control, and its cost is measured", س 1442).
Enforced at EVERY point of use of every tool kind (review R1-01):
  path        — proposal_submitted (its path);
  engine      — mind_registered / mind_reconfigured (every engine);
  null_model  — stage 2 null swaps, stage 3 basic null and alternatives, and the null named by any
                court test instance (self-found S1-01);
  c0_gate     — c0_rule_recorded;
  rediscovery — rediscovery_registered;
  leak_check  — a governance audit report that reports planted cases (they are examined by the
                lineage leak check, س 374, 1539);
  court       — court_ruling.
Lenses are NOT a tool kind: no lens component exists ("complete lenses" deferred, س 2330; TP-22
suspended), so no lens row can be registered until a lens and its point of use are built. Rows do not require results:
"none of the controls has been run" (س 1444) is the starting state. N-c rows are diagnostic only.

Built in this module: the registry, verifiable execution, independent re-execution, and the per-tool
matrix with its points of use. The procedural governance audit is in governance_audit.py.
NOT built yet: the control code itself and the synthetic worlds with planted effects (TP-20, TP-21/tool,
TP-46, TP-47 worlds, TP-50); no control has been run (س 1444).
"""
from __future__ import annotations

import json
import math
import uuid

from .charter import GateError
from .identity import Signed, sign
from .inventory import content_sha256, impl_sha256
from .numeric import finite_real

TARGET_KINDS = ("null_model", "tool", "court")
TOOL_KINDS = ("path", "engine", "null_model", "c0_gate", "leak_check", "rediscovery", "court")
USE_POINTS = ("proposal_submitted", "mind_registered", "mind_reconfigured", "stage_recorded",
              "test_instance_registered", "c0_rule_recorded", "rediscovery_registered",
              "governance_audit_reported", "court_ruling")
POLARITIES = ("positive", "negative")
# Use restrictions (TP-82 review R1-01). IAAFT: «يفترض الاستقرار… يُطبَّق داخل نوافذ مستقرة أو بعد تحويل» (س 829).
RESTRICTIONS = ("stable_windows_or_registered_transform",)


def mandatory_restriction(g, tool_kind, tool_id):
    """The restriction a tool carries BY ITS CARD (TP-82 review R2-01), independent of any registration:
    a null model whose id or accepted null card names a §11.2 card with a use restriction (today: IAAFT).
    Returns the restriction name or None."""
    from .nulls import CARDS
    if tool_kind != "null_model" or not isinstance(tool_id, str):
        return None
    names = [tool_id]
    dl = next((x for x in g._ext.values() if hasattr(x, "null_cards")), None) if g is not None else None
    if dl is not None and tool_id in dl.null_cards:
        names.append(json.dumps(dl.null_cards[tool_id], ensure_ascii=False))
    for card, spec in CARDS.items():
        if spec.get("use_restriction") and any(card.lower() in n.lower() for n in names):
            return spec["use_restriction"]
    return None
OUTCOMES = ("pass", "fail")
OPS = ("<=", ">=", "==", "between")


def _num(x) -> bool:
    return finite_real(x)


def check_expectation(e) -> None:
    if not isinstance(e, dict) or not isinstance(e.get("metric"), str) or not e["metric"].strip() or e.get("op") not in OPS:
        raise GateError("expected: {metric, op in <=,>=,==,between, value | low, high} (R2-01)")
    if e["op"] == "between":
        if set(e) != {"metric", "op", "low", "high"} or not (_num(e["low"]) and _num(e["high"])) or e["low"] > e["high"]:
            raise GateError("between needs finite low <= high")
    elif set(e) != {"metric", "op", "value"} or not _num(e["value"]):
        raise GateError("expectation needs one finite value")


def _names(v, field, allow_empty=False):
    """A use point's list of tool names: a list of text, never silently treated as empty (review S1-01)."""
    if not isinstance(v, list) or (not v and not allow_empty) or any(not isinstance(x, str) or not x.strip() for x in v):
        raise GateError(f"{field}: a list of names{'' if allow_empty else ' (non-empty)'} — a use point is never skipped")
    return v


def compare(e, observed) -> str:
    """The pre-registered comparison rule: pass iff the observed metric satisfies the expectation."""
    v = observed.get(e["metric"]) if isinstance(observed, dict) else None
    if not _num(v):
        raise GateError(f"observation lacks a finite value for metric {e['metric']!r}")
    ok = {"<=": lambda: v <= e.get("value"), ">=": lambda: v >= e.get("value"), "==": lambda: v == e.get("value"),
          "between": lambda: e["low"] <= v <= e["high"]}[e["op"]]()
    return "pass" if ok else "fail"


def _hex64(h) -> bool:
    return isinstance(h, str) and len(h) == 64 and all(c in "0123456789abcdef" for c in h)


def _text(v) -> bool:
    return isinstance(v, str) and bool(v.strip())


class ControlsLayer:
    KINDS = ("control_registered", "control_result_recorded", "control_result_reverified", "tool_row_registered",
             "use_restriction_registered", "restricted_use_justified")
    AUDITOR_ROLES = ("custody_auditor", "governance_auditor")

    def __init__(self):
        self.controls: dict[str, dict] = {}
        self.results: dict[str, dict] = {}         # result_id -> result
        self.reverifications: dict[str, list] = {}  # result_id -> attestations
        self.matrix: dict[tuple, dict] = {}          # (tool_kind, tool_id) -> row
        self.restrictions: dict[tuple, dict] = {}    # (tool_kind, tool_id) -> use restriction (TP-82 review R1-01)
        self.justified: dict[tuple, dict] = {}       # (tool_kind, tool_id, use_key) -> justification
        self.g = None

    def bind(self, g):
        self.g = g

    def _roles(self, ident):
        cl = next((x for x in self.g._ext.values() if hasattr(x, "access_log")), None)
        return cl.roles.get(ident, set()) if cl else set()

    @staticmethod
    def target_of(tool_kind, tool_id) -> dict:
        if tool_kind == "null_model":
            return {"kind": "null_model", "id": tool_id}
        if tool_kind == "court":
            return {"kind": "court", "id": tool_id}
        return {"kind": "tool", "id": f"{tool_kind}:{tool_id}"}

    def require_row(self, tool_kind, tool_id) -> None:
        if (tool_kind, tool_id) not in self.matrix:
            raise GateError(f"no {tool_kind} {tool_id!r} in use without its control-matrix row "
                            "(positive and negative control, registered criterion; WP7-04 §2.1, R16)")

    def require_use(self, tool_kind, tool_id, use_key: str) -> None:
        """Row first; then, if the tool carries a use restriction, a justification for THIS use must be
        recorded before it (TP-82 review R1-01: a restriction written only in a card is not enforced)."""
        self.require_row(tool_kind, tool_id)
        must = mandatory_restriction(self.g, tool_kind, tool_id)
        if must and (tool_kind, tool_id) not in self.restrictions:
            raise GateError(f"{tool_kind} {tool_id!r} carries the mandatory restriction {must!r} by its card (س 829); "
                            "it is not usable until the restriction is registered (R2-01)")
        if (tool_kind, tool_id) in self.restrictions and (tool_kind, tool_id, use_key) not in self.justified:
            r = self.restrictions[(tool_kind, tool_id)]
            raise GateError(f"{tool_kind} {tool_id!r} is restricted ({r['restriction']}): record restricted_use_justified "
                            f"for use {use_key!r} before using it")

    @staticmethod
    def use_key(kind, st) -> str:
        if kind == "stage_recorded":
            return f"claim:{st.get('claim_id')}/stage:{st.get('stage')}"
        if kind == "test_instance_registered":
            return f"test_instance:{st.get('test_instance_id')}"
        raise GateError("no use key for this point")

    # ---------------- points of use ----------------
    def pre_validate(self, kind, p):
        if kind not in USE_POINTS:
            return
        st = json.loads(bytes.fromhex(p["statement_hex"]))
        if kind == "proposal_submitted":
            self.require_row("path", st.get("path_id"))
        elif kind in ("mind_registered", "mind_reconfigured"):
            engines = (st.get("config") or {}).get("engines") if isinstance(st.get("config"), dict) else None
            if not isinstance(engines, list) or any(not isinstance(e, dict) or not isinstance(e.get("name"), str)
                                                    for e in engines):
                raise GateError("engines: a list of objects with a name — a use point is never skipped (S1-01)")
            for e in engines:
                self.require_row("engine", e.get("name"))
        elif kind == "stage_recorded" and st.get("stage") == 2:
            for n in _names(st.get("null_swaps"), "null_swaps"):
                self.require_use("null_model", n, self.use_key(kind, st))
        elif kind == "stage_recorded" and st.get("stage") == 3:
            self.require_use("null_model", st.get("basic_null"), self.use_key(kind, st))
            for n in _names(st.get("alternatives"), "alternatives", allow_empty=True):
                self.require_use("null_model", n, self.use_key(kind, st))
        elif kind == "test_instance_registered":
            self.require_use("null_model", st.get("null"), self.use_key(kind, st))
        elif kind == "c0_rule_recorded":
            self.require_row("c0_gate", "C0")
        elif kind == "rediscovery_registered":
            self.require_row("rediscovery", "blind_rediscovery")
        elif kind == "governance_audit_reported" and st.get("planted_cases"):
            self.require_row("leak_check", "lineage")
        elif kind == "court_ruling":
            self.require_row("court", "court")

    def validate(self, kind, p):
        if kind == "use_restriction_registered":
            st = self.g._signed(p, "founder", "register_use_restriction")
            if set(st) - {"action", "nonce", "tool_kind", "tool_id", "restriction", "text"}:
                raise GateError("use restriction: closed field set")
            if st.get("tool_kind") not in TOOL_KINDS or not _text(st.get("tool_id")):
                raise GateError("use restriction names a tool")
            if st.get("restriction") not in RESTRICTIONS:
                raise GateError(f"restriction is one of {RESTRICTIONS}")
            if not _text(st.get("text")):
                raise GateError("restriction text (its source) is required")
            if (st["tool_kind"], st["tool_id"]) in self.restrictions:
                raise GateError("one restriction per tool")
            must = mandatory_restriction(self.g, st["tool_kind"], st["tool_id"])
            if must and st["restriction"] != must:
                raise GateError(f"this tool's card requires the restriction {must!r}")
            return
        if kind == "restricted_use_justified":
            st = self.g._signed(p, "founder", "justify_restricted_use")
            allowed = {"action", "nonce", "tool_kind", "tool_id", "use_key", "basis", "windows",
                       "stationarity_method", "stationarity_evidence_sha256", "transform_id"}
            if set(st) - allowed:
                raise GateError("justification: closed field set")
            key = (st.get("tool_kind"), st.get("tool_id"))
            if key not in self.restrictions:
                raise GateError("no restriction registered for this tool")
            if not _text(st.get("use_key")) or (*key, st["use_key"]) in self.justified:
                raise GateError("a justification names one new use")
            if st.get("basis") == "stable_windows":
                w = st.get("windows")
                if not isinstance(w, list) or not w or any(
                        not (isinstance(x, list) and len(x) == 2 and _num(x[0]) and _num(x[1]) and x[0] < x[1]) for x in w):
                    raise GateError("stable windows: a non-empty list of [start, end], start < end")
                if not _text(st.get("stationarity_method")) or not _hex64(st.get("stationarity_evidence_sha256")):
                    raise GateError("stable windows need the stationarity method (its choice is «غير معرّف في "
                                    "المعمارية») and the hash of its recorded evidence")
                if "transform_id" in st:
                    raise GateError("one basis per justification")
            elif st.get("basis") == "registered_transform":
                inv = next((x for x in self.g._ext.values() if hasattr(x, "transforms")), None)
                if inv is None or st.get("transform_id") not in inv.transforms:
                    raise GateError("the transform must be frozen in inventory (transform_frozen)")
                if set(st) & {"windows", "stationarity_method"}:
                    raise GateError("one basis per justification")
                if not _hex64(st.get("stationarity_evidence_sha256")):
                    raise GateError("the transform's stationarity evidence hash is required")
            else:
                raise GateError("basis: stable_windows | registered_transform (س 829)")
            return
        if kind == "tool_row_registered":
            st = self.g._signed(p, "founder", "register_tool_row")
            tk, tid = st.get("tool_kind"), st.get("tool_id")
            if tk not in TOOL_KINDS or not _text(tid):
                raise GateError(f"tool row: tool_kind in {TOOL_KINDS} and tool_id")
            if (tk, tid) in self.matrix:
                raise GateError("one matrix row per tool")
            must = mandatory_restriction(self.g, tk, tid)
            if must and (tk, tid) not in self.restrictions:
                raise GateError(f"the row for {tid!r} needs its mandatory restriction {must!r} registered first (R2-01)")
            tgt = self.target_of(tk, tid)
            pol = set()
            for cid in st.get("controls") or []:
                c = self.controls.get(cid)
                if c is None or c["target"] != tgt:
                    raise GateError(f"control {cid!r} is not a registered control of this tool")
                pol.add(c["polarity"])
            if pol != set(POLARITIES):
                raise GateError("a matrix row has at least one positive and one negative control (R16)")
            cr = st.get("criterion") or {}
            if not _text(cr.get("text")) or cr.get("sha256") != content_sha256(cr["text"]):
                raise GateError("a matrix row has a registered criterion with its hash (R16)")
            if not _text(st.get("cost_metric")):
                raise GateError("each tool's cost is measured: name the cost metric (س 1442)")
            return
        if kind == "control_registered":
            st = self.g._signed(p, "founder", "register_control")
            cid = st.get("control_id")
            if not cid or cid in self.controls:
                raise GateError("control needs a new control_id")
            t = st.get("target") or {}
            if t.get("kind") not in TARGET_KINDS or not _text(t.get("id")):
                raise GateError(f"control target: {{kind in {TARGET_KINDS}, id}}")
            if st.get("polarity") not in POLARITIES:
                raise GateError("a control is positive or negative (س 2313)")
            check_expectation(st.get("expected"))
            if not _hex64(st.get("world_sha256")) or not _hex64(st.get("impl_sha256")):
                raise GateError("a control names the synthetic world and the frozen implementation it runs (R2-01)")
        elif kind == "control_result_recorded":
            signer = Signed.from_payload(p).identity
            if "court_operator" not in self._roles(signer):
                raise GateError("control results are recorded by the court operator running frozen code (م7-03)")
            st = self.g._signed(p, signer, "record_control_result")
            rid, c = st.get("result_id"), self.controls.get(st.get("control_id"))
            if not rid or rid in self.results:
                raise GateError("result needs a new result_id")
            if c is None:
                raise GateError("a result belongs to a control registered before it")
            if any(r["control_id"] == st["control_id"] for r in self.results.values()):
                raise GateError("one result per registered control; a rerun is a new control")
            if st.get("impl_sha256") != c["impl_sha256"] or st.get("world_sha256") != c["world_sha256"]:
                raise GateError("the result was not produced by the registered code on the registered world (R2-01)")
            obs = st.get("observed")
            if not isinstance(obs, dict):
                raise GateError("the observation is structured, not free text (R2-01)")
            if st.get("evidence_sha256") != content_sha256(obs):
                raise GateError("evidence hash must be the hash of the recorded observation")
            if st.get("outcome") not in OUTCOMES or st["outcome"] != compare(c["expected"], obs):
                raise GateError("outcome must follow from the registered expectation and the observation (R2-01)")

        elif kind == "control_result_reverified":
            signer = Signed.from_payload(p).identity
            if not self._roles(signer) & set(self.AUDITOR_ROLES):
                raise GateError("re-execution is attested by an auditor (custody or governance auditor) (R3-01)")
            st = self.g._signed(p, signer, "reverify_control_result")
            r = self.results.get(st.get("result_id"))
            if r is None:
                raise GateError("attestation refers to a recorded result")
            if signer == r["_recorder"]:
                raise GateError("the re-executor is independent of the operator who recorded the result (R3-01)")
            if any(a["_by"] == signer for a in self.reverifications.get(st["result_id"], [])):
                raise GateError("one attestation per auditor per result")
            for k in ("impl_sha256", "world_sha256"):
                if st.get(k) != r[k]:
                    raise GateError(f"attestation must name the result's {k}")
            if st.get("verdict") not in ("match", "mismatch") or not _hex64(st.get("reexecuted_evidence_sha256")):
                raise GateError("attestation: verdict match|mismatch and the re-executed evidence hash")
            if (st["verdict"] == "match") != (st["reexecuted_evidence_sha256"] == r["evidence_sha256"]):
                raise GateError("verdict must follow from comparing the re-executed evidence with the recorded one")

    def apply(self, kind, p):
        st = json.loads(bytes.fromhex(p["statement_hex"]))
        if kind == "control_registered":
            self.controls[st["control_id"]] = st
        elif kind == "tool_row_registered":
            self.matrix[(st["tool_kind"], st["tool_id"])] = st
        elif kind == "control_result_recorded":
            self.results[st["result_id"]] = {**st, "_recorder": Signed.from_payload(p).identity}
        elif kind == "use_restriction_registered":
            self.restrictions[(st["tool_kind"], st["tool_id"])] = st
        elif kind == "restricted_use_justified":
            self.justified[(st["tool_kind"], st["tool_id"], st["use_key"])] = st
        elif kind == "control_result_reverified":
            self.reverifications.setdefault(st["result_id"], []).append({**st, "_by": Signed.from_payload(p).identity})

    def commit(self, kind, s: Signed):
        return self.g._commit(kind, s.to_payload())

    def run_control(self, control_id: str, fn, world, *, operator: str, key, result_id: str | None = None):
        """Execute a registered control and record its result (court operator's key). Refuses any other
        implementation or world; requires identical output on two runs."""
        c = self.controls.get(control_id)
        if c is None:
            raise GateError("unknown control")
        if impl_sha256(fn) != c["impl_sha256"]:
            raise GateError("this implementation is not the registered one (R2-01)")
        if content_sha256(world) != c["world_sha256"]:
            raise GateError("this world is not the registered one (R2-01)")
        a, b = fn(world), fn(world)
        if content_sha256(a) != content_sha256(b):
            raise GateError("control code is not deterministic on its world")
        st = {"action": "record_control_result", "nonce": uuid.uuid4().hex, "result_id": result_id or f"r-{control_id}",
              "control_id": control_id, "impl_sha256": c["impl_sha256"], "world_sha256": c["world_sha256"],
              "observed": a, "evidence_sha256": content_sha256(a), "outcome": compare(c["expected"], a)}
        return self.commit("control_result_recorded", sign(operator, key, st))

    def attest_reexecution(self, result_id: str, fn, world, *, auditor: str, key):
        """An independent auditor re-executes the registered code on the registered world and records
        match or mismatch. Refuses code or world that are not the registered ones."""
        r = self.results[result_id]
        if impl_sha256(fn) != r["impl_sha256"] or content_sha256(world) != r["world_sha256"]:
            raise GateError("re-execution must use the registered code and world")
        ev = content_sha256(fn(world))
        st = {"action": "reverify_control_result", "nonce": uuid.uuid4().hex, "result_id": result_id,
              "impl_sha256": r["impl_sha256"], "world_sha256": r["world_sha256"], "reexecuted_evidence_sha256": ev,
              "verdict": "match" if ev == r["evidence_sha256"] else "mismatch"}
        return self.commit("control_result_reverified", sign(auditor, key, st))

    def reverify(self, result_id: str, fn, world) -> bool:
        """Re-execute a recorded control with the given code and world; True iff identical observation."""
        r = self.results[result_id]
        return (impl_sha256(fn) == r["impl_sha256"] and content_sha256(world) == r["world_sha256"]
                and content_sha256(fn(world)) == r["evidence_sha256"])

    def validity_evidence(self, null_model: str, result_ids) -> None:
        """Raise unless result_ids are recorded results of controls targeting this null model, with at
        least one positive and one negative control, all passed."""
        if not isinstance(result_ids, list) or not result_ids or len(set(result_ids)) != len(result_ids):
            raise GateError("null validity cites recorded control results (distinct ids)")
        pol = set()
        for rid in result_ids:
            r = self.results.get(rid)
            if r is None:
                raise GateError(f"control result {rid!r} is not recorded (R1-01)")
            c = self.controls[r["control_id"]]
            if c["target"] != {"kind": "null_model", "id": null_model}:
                raise GateError(f"control result {rid!r} does not target null model {null_model!r}")
            if r["outcome"] != "pass":
                raise GateError(f"control result {rid!r} failed: no validity")
            att = self.reverifications.get(rid, [])
            if any(a["verdict"] == "mismatch" for a in att):
                raise GateError(f"control result {rid!r} failed independent re-execution: unusable")
            if not any(a["verdict"] == "match" for a in att):
                raise GateError(f"control result {rid!r} has no independent re-execution attestation (R3-01)")
            pol.add(c["polarity"])
        if pol != set(POLARITIES):
            raise GateError("validity needs at least one positive and one negative passed control (ق-06; س 2313)")
