"""Layer 4 — data inventory, integrity (C0) and deterministic transforms (WP8-05; spec WP7-01 §2.4,
candidate §6.1–§6.3).

SYNTHETIC DATA ONLY. Real gold data is HARD-LOCKED here (REAL_DATA_LOCKED): opening it is the
founder's gate OD-10, and an inventory needs the founder's inventory permission (م3-02). No code in
this module reads a file; callers hand in synthetic observation dicts.

Implemented (each cites its source):
- Inventory permission (م3-02) is founder-signed per dataset; the inventory itself is executed and
  recorded by custody only (ق-10), "every operation recorded". The inventory is DESCRIPTIVE: counts,
  fields, time range, content hash, presence of arrival times. It makes no integrity judgment; the
  only judgments are C0 states.
- Transforms (س 399): deterministic ones are frozen in advance (spec + hash + fixed params);
  estimated ones are frozen as a spec and their parameters may be estimated ONLY from a slice whose
  station is Discovery (TP-03 (a)). A transform is applied only after it is frozen (and, if estimated,
  after its estimate is recorded); each application is recorded with input/output hashes (ق-10).
- Session calendar (س 400) is a deterministic transform whose spec must name the three elements:
  trading time, the opening event, and scheduled close vs. outage. Their VALUES for gold are data
  («غير معرّف في المعمارية» here); tests use synthetic calendars.
- Inventory and deterministic transforms come BEFORE blinding (§13 #14): once any custody decision
  (blinding parameters) exists for a slice of a dataset, no new deterministic transform can be
  frozen for that dataset. (The slice→dataset link comes from layer 5.)
- C0 (س 402–411; template §13 #15; authority ق-11): a rule is created and approved by the founder
  (founder-signed approval carrying the five template fields) and recorded by custody only. A rule
  must be recorded before any claim is opened on a slice of its dataset ("قبل الفتح"). A result is
  one of the five states; states 1–3 must match the effect the rule examines and must carry a
  damage scope taken from lineage (س 411); the recorded handling is the one the rule declared for
  that state. There is no field for a "market phenomenon" (س 411): unknown fields are refused.
- Capability table (س 415–423): claims are not promoted without their row's fields (س 425).
  Reading of "+" in the table: cumulative (each row needs its own fields and every row above it).
  ⟦قرار Claude بتفويض المؤسس، FD-01⟧ FD-01-D03 (docs/DECISIONS.md).
- Implementation binding (review R1-03, R1-04; FD-01-D11): a frozen transform and a C0 rule carry the
  SHA-256 of the implementation that must run (impl_sha256: qualified name + source text). Applying a
  transform or recording a C0 result with any other implementation is refused, and the hash is kept
  in the record. Limit, stated: the hash covers the function's own source, not modules it calls.
- Time validity (review R1-01): t_market and t_arrival must be finite numbers (not booleans), and
  t_arrival may not precede t_market (arrival before the market time is impossible).
NOT implemented / open: the C0 tests themselves (they are the founder's rules, ق-11; none exist);
C5 is pending (س 426); the number and size of slices and the inventory of real data (CS-03-07).
"""
from __future__ import annotations

import hashlib
import inspect
import json
import math
import uuid

from .charter import GateError
from .identity import AuthError, Signed, check_signature, sign
from .ledger import canonical
from .numeric import finite_real

REAL_DATA_LOCKED = True                       # OD-10 / م3-02: real gold data stays with the founder
DATA_CLASSES = ("synthetic", "real")
TIME_KEYS = ("t_market", "t_arrival", "id")

# Capability table (س 415–423). Field groups are the names the inventory reports.
CAPABILITY_ROWS = (
    ("ohlc", ("open", "high", "low", "close"),
     "خصائص القانون على مستوى الشمعة", "الترتيب داخل الشمعة، والتنفيذ"),
    ("bid_ask", ("bid", "ask"),
     "السبريد المعروض وديناميكيته، وفصل ارتداد Bid/Ask", "كلفة التنفيذ المحققة، والأحجام"),
    ("ticks", ("tick",),
     "معدل التحديث، والتوقيت بدقة التيك", "الأحجام الحقيقية، وما بين تيكين متتاليين"),
    ("unsigned_volume", ("volume",),
     "النشاط الكلي، والإزاحة لكل وحدة حجم", "الضغط الموقّع (شراء أو بيع)"),
    ("aggressor", ("aggressor_side",),
     "الضغط الموقّع، مع إعلان خطأ التصنيف إن كان مستنتجًا", "النوايا والهوية"),
    ("execution", ("fill_price", "fee", "slippage"),
     "كلفة التنفيذ المحققة (المسار هـ المغلق)", "—"),
    ("order_book", ("book_depth", "book_add", "book_cancel", "book_trade", "book_qty"),
     "السيولة الظاهرة والمسحوبة", "الأوامر المخفية والهوية"),
)
ROW_IDS = tuple(r[0] for r in CAPABILITY_ROWS)

# C0 (س 404–409)
C0_STATES = {1: "أثر تغذية مثبت", 2: "أثر معالجة مثبت", 3: "أثر بناء شموع أو ترتيب مثبت",
             4: "لم يُكشف أثر ضمن الاختبارات المحددة", 5: "غير محسوم"}
C0_EFFECTS = {"feed": 1, "processing": 2, "candle_or_order": 3}
C0_TEMPLATE = ("effect", "test", "criterion", "resulting_state", "handling")      # §13 #15
C0_BINDING = "test_impl_sha256"                                                    # FD-01-D11
C0_RESULT_FIELDS = ("action", "nonce", "rule_id", "dataset_id", "state", "scope_lineage", "evidence_sha256",
                    "handling", "time", "test_impl_sha256")
CALENDAR_ELEMENTS = ("trading_time", "open_event", "scheduled_close_vs_outage")   # س 400
TRANSFORM_KINDS = ("deterministic", "estimated")


class CapabilityError(GateError):
    pass


def _hex64(h) -> bool:
    return isinstance(h, str) and len(h) == 64 and all(c in "0123456789abcdef" for c in h)


def content_sha256(obj) -> str:
    return hashlib.sha256(canonical(obj)).hexdigest()


def impl_sha256(fn) -> str:
    """Identity of an implementation: SHA-256 over its qualified name and source text (FD-01-D11).
    Lambdas and functions without retrievable source are refused (no identity can be fixed)."""
    if getattr(fn, "__name__", "") == "<lambda>":
        raise GateError("an implementation must be a named function (a lambda has no stable identity)")
    try:
        src = inspect.getsource(fn)
    except (OSError, TypeError):
        raise GateError("implementation source is not retrievable; its identity cannot be fixed")
    ident = f"{getattr(fn, '__module__', '')}.{getattr(fn, '__qualname__', '')}\n{src}"
    return hashlib.sha256(ident.encode("utf-8")).hexdigest()


def valid_time(t) -> bool:
    return finite_real(t)


def check_times(o: dict) -> None:
    """t_market finite number; t_arrival (if present) finite number and not before t_market (R1-01)."""
    if not valid_time(o.get("t_market")):
        raise GateError("every observation needs a finite numeric t_market")
    if "t_arrival" in o:
        if not valid_time(o["t_arrival"]):
            raise GateError("t_arrival must be a finite number")
        if o["t_arrival"] < o["t_market"]:
            raise GateError("t_arrival precedes t_market: arrival before the market time is impossible (س 492)")


# ======================= pure functions ==========================================================
def take_inventory(dataset_id: str, observations: list[dict], *, source: str, data_class: str) -> dict:
    """Descriptive inventory of synthetic observations (dicts with 't_market', optional 't_arrival',
    'id', and value fields). No integrity judgment is made here."""
    if data_class != "synthetic" and REAL_DATA_LOCKED:
        raise GateError("real data is locked (OD-10 / م3-02): founder's gate")
    if not observations:
        raise GateError("empty dataset")
    for o in observations:
        check_times(o)
    ts = [o["t_market"] for o in observations]
    fields = sorted({k for o in observations for k in o if k not in TIME_KEYS})
    return {
        "dataset_id": dataset_id, "source": source, "data_class": data_class,
        "n_observations": len(observations), "fields": fields,
        "t_first": min(ts), "t_last": max(ts),
        "has_arrival_time": all("t_arrival" in o for o in observations),
        "n_duplicate_t_market": len(ts) - len(set(ts)),
        "n_out_of_order": sum(1 for a, b in zip(ts, ts[1:]) if b < a),
        "n_missing_values": sum(1 for o in observations for f in fields if o.get(f) is None),
        "content_sha256": content_sha256(observations),
    }


def capabilities(fields) -> list[str]:
    """Rows of the capability table whose fields are present, cumulatively (FD-01-D03)."""
    have, out = set(fields), []
    for row_id, req, _can, _cannot in CAPABILITY_ROWS:
        if not set(req) <= have:
            break
        out.append(row_id)
    return out


def require_capability(row_id: str, fields) -> None:
    """«لا ترقية للادعاء دون حقول صفه» (س 425)."""
    if row_id not in ROW_IDS:
        raise CapabilityError(f"unknown capability row {row_id!r}")
    if row_id not in capabilities(fields):
        need = []
        for rid, req, *_ in CAPABILITY_ROWS:
            need += [f for f in req if f not in set(fields)]
            if rid == row_id:
                break
        raise CapabilityError(f"no promotion without the row's fields (س 425): {row_id} needs {need}")


def run_c0(rule: dict, test_fn, observations) -> dict:
    """Run a founder C0 rule's test on synthetic data. test_fn(observations) returns
    {"outcome": "detected"|"not_detected"|"undetermined", "affected_ids": [...]}.
    Maps to a state: detected -> the rule's resulting_state (1–3); not_detected -> 4; undetermined -> 5."""
    h = impl_sha256(test_fn)
    if h != rule.get(C0_BINDING):
        raise GateError("this test implementation is not the one the founder approved for the rule (FD-01-D11)")
    r = test_fn(observations)
    out = r.get("outcome")
    if out == "detected":
        state, scope = rule["resulting_state"], list(r.get("affected_ids") or [])
        if not scope:
            raise GateError("a detected effect needs its damage scope from lineage (س 411)")
    elif out == "not_detected":
        state, scope = 4, []
    elif out == "undetermined":
        state, scope = 5, list(r.get("affected_ids") or [])
    else:
        raise GateError("C0 test outcome must be detected / not_detected / undetermined")
    return {"state": state, "scope_lineage": scope, "evidence_sha256": content_sha256(r),
            "handling": rule["handling"][str(state)], C0_BINDING: h}


# ======================= ledger component ========================================================
class InventoryLayer:
    KINDS = ("inventory_permitted", "inventory_recorded", "transform_frozen", "transform_estimated",
             "transform_applied", "c0_rule_recorded", "c0_result_recorded")

    def __init__(self, *, identity: str | None = None, key=None):
        self.identity, self._key = identity, key
        self.permits: dict[str, str] = {}          # dataset -> data_class
        self.inventories: dict[str, dict] = {}
        self.transforms: dict[str, dict] = {}       # transform_id -> frozen record
        self.estimates: dict[str, dict] = {}        # transform_id -> estimate record
        self.applied: list[dict] = []
        self.c0_rules: dict[str, dict] = {}
        self.c0_results: list[dict] = []
        self.approval_nonces: set = set()
        self.g = None

    def bind(self, g):
        self.g = g

    # ---------------- helpers ----------------
    def _ext(self, attr):
        return next((x for x in self.g._ext.values() if hasattr(x, attr) and x is not self), None)

    def _custody_signed(self, p, action):
        cl = self._ext("access_log")
        if cl is None:
            raise GateError("layer 4 needs the custody layer (ق-10)")
        signer = Signed.from_payload(p).identity
        if "custody" not in cl.roles.get(signer, set()):
            raise GateError(f"{signer!r} is not custody: only custody executes layer 4 (ق-10, ق-11)")
        return self.g._signed(p, signer, action)

    def _station(self, slice_id):
        sl = self._ext("plans")
        return sl.slice_station(slice_id) if sl else None

    def _blinded_dataset(self, dataset_id) -> bool:
        cl, sl = self._ext("access_log"), self._ext("plans")
        if cl is None or sl is None:
            return False
        return any(sl.slice_dataset(s) == dataset_id for s in cl.decisions)

    def _opened_on_dataset(self, dataset_id) -> bool:
        cc, sl = self._ext("openings"), self._ext("plans")
        if cc is None or sl is None:
            return False
        return any(sl.slice_dataset(s) == dataset_id for (_c, s) in cc.openings)

    def fields_available(self, dataset_id) -> list[str]:
        """Raw inventory fields plus outputs of frozen deterministic transforms on the dataset."""
        inv = self.inventories.get(dataset_id)
        if inv is None:
            raise GateError("no inventory recorded for this dataset")
        f = set(inv["fields"])
        for t in self.transforms.values():
            if t["dataset_id"] == dataset_id and t["kind"] == "deterministic":
                f |= set(t["outputs"])
        return sorted(f)

    # ---------------- validation ----------------
    def validate(self, kind, p):
        if kind == "inventory_permitted":
            st = self.g._signed(p, "founder", "permit_inventory")
            if st.get("data_class") not in DATA_CLASSES or not str(st.get("dataset_id", "")).strip():
                raise GateError("permission names a dataset and its data class")
            if st["data_class"] == "real" and REAL_DATA_LOCKED:
                raise GateError("real data is locked in this build (OD-10); prepare and ask the founder")
            if st["dataset_id"] in self.permits:
                raise GateError("inventory permission already recorded for this dataset")
        elif kind == "inventory_recorded":
            st = self._custody_signed(p, "inventory_recorded")
            inv = st.get("inventory")
            if not isinstance(inv, dict):
                raise GateError("inventory is an object (FL-014)")
            ds = inv.get("dataset_id")
            if ds not in self.permits:
                raise GateError("no inventory before the inventory permission (م3-02)")
            if inv.get("data_class") != self.permits[ds]:
                raise GateError("inventory data class differs from the permission")
            if ds in self.inventories:
                raise GateError("inventory already recorded for this dataset")
            need = ("source", "n_observations", "fields", "t_first", "t_last", "has_arrival_time", "content_sha256")
            if any(k not in inv for k in need) or not _hex64(inv["content_sha256"]):
                raise GateError("inventory record is incomplete")
        elif kind == "transform_frozen":
            st = self._custody_signed(p, "transform_frozen")
            tid, ds, k = st.get("transform_id"), st.get("dataset_id"), st.get("kind")
            if not tid or tid in self.transforms:
                raise GateError("a frozen transform needs a new transform_id")
            if ds not in self.inventories:
                raise GateError("transforms follow the inventory of their dataset")
            if k not in TRANSFORM_KINDS:
                raise GateError("transform kind is deterministic or estimated (س 399)")
            if not str(st.get("spec", "")).strip() or st.get("spec_sha256") != hashlib.sha256(
                    st["spec"].encode("utf-8")).hexdigest():
                raise GateError("transform spec text must match its hash")
            if not isinstance(st.get("outputs"), list) or not st["outputs"]:
                raise GateError("transform must declare its output fields")
            if not _hex64(st.get("impl_sha256")):
                raise GateError("a frozen transform names the implementation hash that must run (FD-01-D11)")
            if k == "deterministic":
                if not isinstance(st.get("params"), dict):
                    raise GateError("a deterministic transform is frozen with its fixed parameters")
                if self._blinded_dataset(ds):
                    raise GateError("deterministic transforms come before blinding (§13 #14); this dataset is blinded")
                if st.get("role") == "session_calendar":
                    cal = st.get("calendar") or {}
                    miss = [e for e in CALENDAR_ELEMENTS if not str(cal.get(e, "")).strip()]
                    if miss:
                        raise GateError(f"session calendar must define {miss} (س 400)")
            else:
                if st.get("params") not in (None, {}):
                    raise GateError("an estimated transform is frozen WITHOUT parameters; they are estimated from Discovery")
        elif kind == "transform_estimated":
            st = self._custody_signed(p, "transform_estimated")
            t = self.transforms.get(st.get("transform_id"))
            if t is None or t["kind"] != "estimated":
                raise GateError("estimate must refer to a frozen estimated transform")
            if st["transform_id"] in self.estimates:
                raise GateError("estimate already recorded; register a new transform")
            stn = self._station(st.get("estimated_from_slice"))
            if stn != "Discovery":
                raise GateError(f"estimated transforms are estimated from Discovery only (س 399); slice station: {stn}")
            if self._ext("plans").slice_dataset(st["estimated_from_slice"]) != t["dataset_id"]:
                raise GateError("estimation slice belongs to another dataset")
            if not isinstance(st.get("params"), dict) or not st["params"]:
                raise GateError("estimate must carry its parameters")
        elif kind == "transform_applied":
            st = self._custody_signed(p, "transform_applied")
            t = self.transforms.get(st.get("transform_id"))
            if t is None:
                raise GateError("a transform is used only after it is frozen (س 399)")
            if t["kind"] == "estimated" and st["transform_id"] not in self.estimates:
                raise GateError("estimated transform has no Discovery estimate yet")
            if not (_hex64(st.get("input_sha256")) and _hex64(st.get("output_sha256"))):
                raise GateError("application record carries input and output hashes (ق-10)")
            if st.get("spec_sha256") != t["spec_sha256"]:
                raise GateError("application does not match the frozen spec")
            if st.get("impl_sha256") != t["impl_sha256"]:
                raise GateError("application ran another implementation than the frozen one (FD-01-D11)")
        elif kind == "c0_rule_recorded":
            st = self._custody_signed(p, "c0_rule_recorded")
            ap = st.get("approval") or {}
            try:
                s = Signed.from_payload(ap)
            except (KeyError, ValueError, TypeError):
                raise GateError("C0 rule needs the founder's signed approval (ق-11)")
            if s.identity != "founder":
                raise GateError("only the founder creates and approves a C0 rule (ق-11)")
            a = check_signature(self.g.keys()["founder"], s)
            if a.get("action") != "c0_rule_approve" or not a.get("nonce"):
                raise AuthError("approval is not a C0 rule approval")
            if a["nonce"] in self.approval_nonces or a["nonce"] in self.g._s.nonces:
                raise AuthError("replayed approval")
            rule = a.get("rule") or {}
            rid, ds = rule.get("rule_id"), rule.get("dataset_id")
            if not rid or rid in self.c0_rules:
                raise GateError("C0 rule needs a new rule_id")
            if ds not in self.inventories:
                raise GateError("C0 rule refers to an inventoried dataset")
            miss = [f for f in C0_TEMPLATE if f not in rule or rule[f] in (None, "", {})]
            if miss:
                raise GateError(f"C0 rule template incomplete (§13 #15): {miss}")
            if rule["effect"] not in C0_EFFECTS or rule["resulting_state"] != C0_EFFECTS[rule["effect"]]:
                raise GateError("resulting state must be the state of the examined effect (1–3, س 405–407)")
            if not isinstance(rule["handling"], dict) or set(rule["handling"]) != {str(i) for i in C0_STATES} \
                    or any(not str(v).strip() for v in rule["handling"].values()):
                raise GateError("handling must be recorded for each of the five states (§13 #15)")
            if not _hex64(rule.get(C0_BINDING)):
                raise GateError("C0 rule names the hash of the approved test implementation (FD-01-D11)")
            if self._opened_on_dataset(ds):
                raise GateError("C0 rules are fixed before opening (§13 #15); a claim is already open on this dataset")
            if st.get("rule_sha256") != content_sha256(rule):
                raise GateError("rule hash mismatch")
        elif kind == "c0_result_recorded":
            st = self._custody_signed(p, "c0_result_recorded")
            extra = set(st) - set(C0_RESULT_FIELDS)
            if extra:
                raise GateError(f"unknown fields in a C0 result {sorted(extra)}; C0 declares no market phenomenon (س 411)")
            rule = self.c0_rules.get(st.get("rule_id"))
            if rule is None or st.get("dataset_id") != rule["dataset_id"]:
                raise GateError("C0 result must refer to a recorded rule and its dataset")
            stt = st.get("state")
            if not isinstance(stt, int) or isinstance(stt, bool) or stt not in C0_STATES:
                raise GateError("C0 state is one of the five (س 404–409)")
            if stt in (1, 2, 3) and stt != rule["resulting_state"]:
                raise GateError("this rule examines another effect; its detected state is fixed")
            if stt in (1, 2, 3) and not st.get("scope_lineage"):
                raise GateError("damage scope is set from full lineage (س 411)")
            if st.get("handling") != rule["handling"][str(stt)]:
                raise GateError("handling must be the one the rule recorded for this state")
            if not _hex64(st.get("evidence_sha256")):
                raise GateError("result carries the evidence hash")
            sl = st.get("scope_lineage")
            if not isinstance(sl, list) or any(not isinstance(x, str) or not x.strip() for x in sl):
                raise GateError("scope_lineage is a list of observation ids (FL-014)")
            if not isinstance(st.get("time"), str) or not st["time"].strip():
                raise GateError("time is non-empty text (FL-014)")
            if st.get(C0_BINDING) != rule[C0_BINDING]:
                raise GateError("result was produced by another test implementation than the approved one (FD-01-D11)")

    def apply(self, kind, p):
        st = json.loads(bytes.fromhex(p["statement_hex"]))
        if kind == "inventory_permitted":
            self.permits[st["dataset_id"]] = st["data_class"]
        elif kind == "inventory_recorded":
            self.inventories[st["inventory"]["dataset_id"]] = st["inventory"]
        elif kind == "transform_frozen":
            self.transforms[st["transform_id"]] = st
        elif kind == "transform_estimated":
            self.estimates[st["transform_id"]] = st
        elif kind == "transform_applied":
            self.applied.append(st)
        elif kind == "c0_rule_recorded":
            a = json.loads(bytes.fromhex(st["approval"]["statement_hex"]))
            self.approval_nonces.add(a["nonce"])
            self.c0_rules[a["rule"]["rule_id"]] = a["rule"]
        elif kind == "c0_result_recorded":
            self.c0_results.append(st)

    # ---------------- API (custody side) ----------------
    def _csign(self, statement: dict) -> Signed:
        if self._key is None or self.identity is None:
            raise GateError("this layer holds no custody signing key")
        return sign(self.identity, self._key, {**statement, "nonce": uuid.uuid4().hex})

    def _commit(self, kind, s: Signed):
        return self.g._commit(kind, s.to_payload())

    def permit(self, s: Signed):
        """Founder-signed inventory permission (action 'permit_inventory')."""
        return self._commit("inventory_permitted", s)

    def record_inventory(self, dataset_id, observations, *, source):
        inv = take_inventory(dataset_id, observations, source=source,
                             data_class=self.permits.get(dataset_id, "synthetic"))
        self._commit("inventory_recorded", self._csign({"action": "inventory_recorded", "inventory": inv}))
        return inv

    def freeze_transform(self, transform_id, dataset_id, *, kind, spec, outputs, impl, params=None, role=None,
                         calendar=None):
        """impl: the named function that implements the spec; its hash is frozen (FD-01-D11)."""
        st = {"action": "transform_frozen", "transform_id": transform_id, "dataset_id": dataset_id, "kind": kind,
              "spec": spec, "spec_sha256": hashlib.sha256(spec.encode("utf-8")).hexdigest(),
              "outputs": list(outputs), "params": params, "impl_sha256": impl_sha256(impl)}
        if role:
            st["role"] = role
        if calendar is not None:
            st["calendar"] = calendar
        return self._commit("transform_frozen", self._csign(st))

    def record_estimate(self, transform_id, *, estimated_from_slice, params):
        return self._commit("transform_estimated", self._csign(
            {"action": "transform_estimated", "transform_id": transform_id,
             "estimated_from_slice": estimated_from_slice, "params": params}))

    def apply_transform(self, transform_id, fn, observations):
        """Run fn(observations, params) for a frozen transform; record input/output hashes (ق-10)."""
        t = self.transforms.get(transform_id)
        if t is None:
            raise GateError("a transform is used only after it is frozen (س 399)")
        params = t["params"] if t["kind"] == "deterministic" else (self.estimates.get(transform_id) or {}).get("params")
        if params is None:
            raise GateError("estimated transform has no Discovery estimate yet")
        h = impl_sha256(fn)
        if h != t["impl_sha256"]:
            raise GateError("this implementation is not the frozen one (FD-01-D11)")
        out = fn(observations, params)
        self._commit("transform_applied", self._csign(
            {"action": "transform_applied", "transform_id": transform_id, "spec_sha256": t["spec_sha256"],
             "impl_sha256": h,
             "input_sha256": content_sha256(observations), "output_sha256": content_sha256(out)}))
        return out

    def record_c0_rule(self, approval: Signed):
        rule = json.loads(approval.statement).get("rule") or {}
        return self._commit("c0_rule_recorded", self._csign(
            {"action": "c0_rule_recorded", "approval": approval.to_payload(), "rule_sha256": content_sha256(rule)}))

    def record_c0_result(self, rule_id, result: dict, *, time: str):
        rule = self.c0_rules.get(rule_id)
        if rule is None:
            raise GateError("unknown C0 rule")
        return self._commit("c0_result_recorded", self._csign(
            {"action": "c0_result_recorded", "rule_id": rule_id, "dataset_id": rule["dataset_id"], **result,
             "time": time}))

    def c0_state(self, rule_id) -> int | None:
        r = [x for x in self.c0_results if x["rule_id"] == rule_id]
        return r[-1]["state"] if r else None
