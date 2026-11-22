"""Stage 9, gap G1 — the three paths Z, G-Z and R and the flows between them (WP7-02 ت-03 … ت-07, ت-18;
forbidden flows م-03, م-04, م-05, م-06).

Source text: «المسارات: Z، وG-Z، وR. لا يستطيع Z تقنيًا استدعاء أي أداة موسومة «تداول»» ⟨س 353⟩;
«التدفق من Z إلى G-Z وR مسموح. من R إلى Z ممنوع إلا عبر الطبقة (أ)» ⟨س 354⟩; «(أ) منهجية: قاعدة
رياضية، أو أداة، أو ملاحظة من بيانات الذهب. والملاحظة الأخيرة خاصة دائمًا» ⟨س 356–357⟩;
⟦قرار المؤسس CS-01-08⟧ the gold-data observation crosses R → Z tagged «خاصة»; «التعمية تُطبَّق قبل
أي وصول من المسار Z» ⟨س 352⟩; «كل مخرج من Z يمر على جهة الحفظ قبل أن يصل إلى أي طرف آخر» ⟨س 254⟩;
ت-18 (ق-29): G-Z and R → layer 10 messages with mandatory fields by type, Claim ID or «لا ادعاء»,
«خاصة» for a gold-data observation; an incomplete message is refused.

Enforced
- Every input INTO Z is admitted by custody (signed), from exactly one of two sources:
  * "blinding" (ت-03): a blinded representation of a slice that has a custody decision (layer 3);
  * "knowledge_a" (ت-07): an item registered in knowledge layer (أ), arriving from R. The item must
    BE a recorded R → layer-10 message (ت-18): its content hash equals that message's hash (R1-01).
- Every statement has a closed field set with types (SHAPES); extra or mistyped fields are refused,
  so no unhashed content rides along and malformed input is a refusal, not a crash (R1-02, R1-04).
  No other source exists. Content that was ever transferred to R or recorded as an R output is
  refused as a "blinding" input (R → Z only through layer (أ), م-05).
- Transfers between paths: only Z → G-Z (ت-05) and Z → R (ت-06), recorded by custody, and only for an
  output that passed custody's full-scope review (z_output_passed; ت-04, م-06). R → Z as a transfer
  is always refused (it exists only as a "knowledge_a" admission). Every other direction (G-Z → Z,
  G-Z ↔ R) is not drawn in WP7-02 and is refused (FD-01-D29: undrawn = refused).
- Tools: registered by the founder with tags and impl hash; a call from Z to a tool tagged «تداول» is
  refused (م-04). Every refused attempt can be logged by custody as path_refusal_logged, which is
  accepted only if the attempt really is refused.
- Layer (أ) items: kind ∈ {قاعدة رياضية، أداة، ملاحظة من بيانات الذهب}; a gold-data observation must
  carry «خاصة»; and while gold data is locked (OD-10) no gold-data observation can be registered.
- Layer-10 messages from G-Z or R (ت-18): the message type must be registered with its mandatory
  fields; every field present and non-empty; claim_id is a registered claim or «لا ادعاء»;
  gold_observation is declared, and a gold observation carries «خاصة» (and is locked by OD-10).

OPEN (flagged, not invented)
- The list of layer-10 message types and their mandatory fields is «غير معرّف في المعمارية»:
  types are registered by the founder before use (FD-01-D29).
- Who registers layer (أ) items is «غير معرّف في المعمارية»: founder-signed here (FD-01-D29).
  Stated limit: the origin proof is the ledger record of an R message, and R messages are themselves
  founder-signed while the R sender role is undefined; the proof is "recorded as R output", no more.
- The sender role of R is «غير معرّف في المعمارية» (no R role in §13): R messages are founder-signed
  until a role is defined; G-Z messages are signed by the G-Z operator.
- R's own computations, G-Z's decryption workflow and the language-mind release (غ-03, locked) are
  outside this component; decryption stays in custody (س 355).
"""
from __future__ import annotations

import hashlib
import json

from .charter import GateError
from .identity import AuthError, Signed
from .inventory import REAL_DATA_LOCKED

PATHS = ("Z", "G-Z", "R")
ALLOWED_TRANSFERS = {("Z", "G-Z"), ("Z", "R")}                       # ت-05, ت-06
A_KINDS = ("قاعدة رياضية", "أداة", "ملاحظة من بيانات الذهب")          # س 357
GOLD = "ملاحظة من بيانات الذهب"
PRIVATE = "خاصة"
NO_CLAIM = "لا ادعاء"
TRADING = "تداول"
Z_SOURCES = ("blinding", "knowledge_a")


BASE = {"action": str, "nonce": str}
# Closed field sets per action (review R1-02, R1-04): required fields with types, then optional ones.
SHAPES = {
    "register_path_tool": ({"tool_id": str, "tags": list, "impl_sha256": str}, {}),
    "call_path_tool": ({"path": str, "tool_id": str}, {}),
    "register_knowledge_a": ({"item_id": str, "kind": str, "content_sha256": str, "origin_message_sha256": str},
                             {"tag": str}),
    "admit_z_input/blinding": ({"input_id": str, "source": str, "slice": str, "representation_id": str,
                                "content_sha256": str}, {}),
    "admit_z_input/knowledge_a": ({"input_id": str, "source": str, "knowledge_a_id": str, "from_path": str,
                                   "content_sha256": str}, {"tag": str}),
    "record_path_transfer": ({"from": str, "to": str, "item_sha256": str}, {}),
    "register_l10_message_type": ({"type": str, "required_fields": list}, {}),
    "send_l10_message": ({"from": str, "type": str, "claim_id": str, "gold_observation": bool, "fields": dict},
                         {"tag": str}),
    "log_path_refusal": ({"attempt": dict, "reason": str}, {}),
}


def _shape(st: dict, name: str) -> dict:
    """Closed statement: exactly the declared fields, each of its declared type; anything else refused."""
    req, opt = SHAPES[name]
    allowed = {**BASE, **req, **opt}
    extra = set(st) - set(allowed)
    if extra:
        raise GateError(f"{name}: fields {sorted(extra)} are not part of this statement (closed field set)")
    for k, t in {**BASE, **req}.items():
        if k not in st:
            raise GateError(f"{name}: missing field {k!r}")
    for k, v in st.items():
        if not isinstance(v, allowed[k]) or (allowed[k] is str and isinstance(v, bool)):
            raise GateError(f"{name}: field {k!r} must be {allowed[k].__name__}")
    return st


def _hex64(x) -> bool:
    return isinstance(x, str) and len(x) == 64 and all(c in "0123456789abcdef" for c in x)


class PathsLayer:
    KINDS = ("path_tool_registered", "path_tool_called", "knowledge_a_registered", "z_input_admitted",
             "path_transfer_recorded", "l10_message_type_registered", "l10_message_recorded",
             "path_refusal_logged")

    def __init__(self):
        self.tools: dict[str, dict] = {}
        self.calls: list[dict] = []
        self.knowledge_a: dict[str, dict] = {}
        self.z_inputs: dict[str, dict] = {}
        self.transfers: list[dict] = []
        self.msg_types: dict[str, list] = {}
        self.messages: list[dict] = []
        self.refusals: list[dict] = []
        self.g = None

    def bind(self, g):
        self.g = g

    # ---------------- helpers ----------------
    def _custody(self):
        return next((x for x in self.g._ext.values() if hasattr(x, "access_log")), None)

    def _roles(self, ident):
        cl = self._custody()
        return cl.roles.get(ident, set()) if cl else set()

    def _by_role(self, p, role, action):
        signer = Signed.from_payload(p).identity
        if role not in self._roles(signer):
            raise GateError(f"{action} is signed by the {role}")
        return self.g._signed(p, signer, action)

    def _r_contents(self) -> set:
        """Every content hash that reached R (transfers into R) — never admissible to Z as 'blinding'."""
        return {t["item_sha256"] for t in self.transfers if t["to"] == "R"}

    def _claims(self):
        return next((x for x in self.g._ext.values() if hasattr(x, "cards")), None)

    # ---------------- validation ----------------
    def validate(self, kind, p):
        if kind == "path_tool_registered":
            st = _shape(self.g._signed(p, "founder", "register_path_tool"), "register_path_tool")
            if not st.get("tool_id") or st["tool_id"] in self.tools:
                raise GateError("a tool needs a new tool_id")
            tags = st.get("tags")
            if not isinstance(tags, list) or any(not isinstance(t, str) or not t.strip() for t in tags):
                raise GateError("tool tags are a list of non-empty texts")
            if not _hex64(st.get("impl_sha256")):
                raise GateError("tool needs impl_sha256")
        elif kind == "path_tool_called":
            signer = Signed.from_payload(p).identity
            st = _shape(self.g._signed(p, signer, "call_path_tool"), "call_path_tool")
            path, tool = st.get("path"), self.tools.get(st.get("tool_id"))
            if path not in PATHS:
                raise GateError(f"path is one of {PATHS}")
            if tool is None:
                raise GateError("unregistered tool")
            role = {"Z": "discovery_participant", "G-Z": "gz_operator"}.get(path)
            if role is None:
                raise GateError("R participant role is «غير معرّف في المعمارية»; no R tool call is accepted")
            if role not in self._roles(signer):
                raise GateError(f"a call in {path} is made by the {role}")
            if path == "Z" and TRADING in tool["tags"]:
                raise GateError("Z cannot call any tool tagged «تداول» (س 353; م-04)")
        elif kind == "knowledge_a_registered":
            st = _shape(self.g._signed(p, "founder", "register_knowledge_a"), "register_knowledge_a")
            if not st.get("item_id") or st["item_id"] in self.knowledge_a:
                raise GateError("a layer (أ) item needs a new item_id")
            if st.get("kind") not in A_KINDS:
                raise GateError(f"layer (أ) kind is one of {A_KINDS} (س 357)")
            if not _hex64(st.get("content_sha256")):
                raise GateError("layer (أ) item needs content_sha256")
            if st["kind"] == GOLD:
                if st.get("tag") != PRIVATE:
                    raise GateError("a gold-data observation is always «خاصة» (س 357; CS-01-08)")
                if REAL_DATA_LOCKED:
                    raise GateError("gold data is locked (OD-10): no gold-data observation exists")
            elif st.get("tag") not in (None, PRIVATE):
                raise GateError("tag is «خاصة» or absent")
            # R1-01: the item's origin in R is a recorded R → layer-10 message (ت-18), and the item IS
            # that message (content hash = the message's statement hash).
            msg = self.r_messages().get(st["origin_message_sha256"])
            if msg is None:
                raise GateError("a layer (أ) item names its origin: a recorded R message (ت-18 → ت-07; R1-01)")
            if st["content_sha256"] != st["origin_message_sha256"]:
                raise GateError("the layer (أ) item is the R message it cites (content hash = message hash)")
            if msg["gold_observation"] != (st["kind"] == GOLD):
                raise GateError("gold-observation status must match the origin message")
        elif kind == "z_input_admitted":
            st = self._by_role(p, "custody", "admit_z_input")
            if st.get("source") in Z_SOURCES:
                _shape(st, f"admit_z_input/{st['source']}")
            if not st.get("input_id") or st["input_id"] in self.z_inputs:
                raise GateError("a Z input needs a new input_id")
            src = st.get("source")
            if src not in Z_SOURCES:
                raise GateError(f"Z receives only blinded representations or layer (أ) knowledge: {Z_SOURCES} "
                                "(س 352, 354; م-03, م-05)")
            if src == "blinding":
                cl = self._custody()
                if st.get("slice") not in cl.decisions:
                    raise GateError("blinding precedes any access from Z: the slice needs a custody decision "
                                    "(س 352; ت-03)")
                if not st.get("representation_id") or not _hex64(st.get("content_sha256")):
                    raise GateError("a blinded input names its representation and content hash")
                if st["content_sha256"] in self._r_contents():
                    raise GateError("content that reached R enters Z only through layer (أ) (س 354; م-05)")
            else:
                item = self.knowledge_a.get(st.get("knowledge_a_id"))
                if item is None:
                    raise GateError("R → Z only through knowledge layer (أ): unregistered item (س 354; م-05)")
                if st.get("from_path") != "R" or item["origin_message_sha256"] not in self.r_messages():
                    raise GateError("a layer (أ) admission names its origin path R (ت-07)")
                if st.get("content_sha256") != item["content_sha256"]:
                    raise GateError("the admitted content must be the registered layer (أ) item")
                if item["kind"] == GOLD and st.get("tag") != PRIVATE:
                    raise GateError("a gold-data observation crosses R → Z tagged «خاصة» (CS-01-08)")
        elif kind == "path_transfer_recorded":
            st = _shape(self._by_role(p, "custody", "record_path_transfer"), "record_path_transfer")
            pair = (st.get("from"), st.get("to"))
            if pair == ("R", "Z"):
                raise GateError("R → Z is forbidden except through knowledge layer (أ) (س 354; م-05)")
            if pair not in ALLOWED_TRANSFERS:
                raise GateError(f"flow {pair[0]} → {pair[1]} is not drawn in WP7-02; refused (FD-01-D29)")
            if st.get("item_sha256") not in self._custody().passed:
                raise GateError("every Z output passes custody before reaching any other party (س 254, 284; م-06)")
        elif kind == "l10_message_type_registered":
            st = _shape(self.g._signed(p, "founder", "register_l10_message_type"), "register_l10_message_type")
            f = st.get("required_fields")
            if not st.get("type") or st["type"] in self.msg_types:
                raise GateError("a message type needs a new name")
            if not isinstance(f, list) or not f or any(not isinstance(x, str) or not x.strip() for x in f) \
                    or len(set(f)) != len(f):
                raise GateError("required_fields: a non-empty list of distinct field names")
        elif kind == "l10_message_recorded":
            signer = Signed.from_payload(p).identity
            st = _shape(self.g._signed(p, signer, "send_l10_message"), "send_l10_message")
            src = st.get("from")
            if src == "G-Z":
                if "gz_operator" not in self._roles(signer):
                    raise GateError("a G-Z message is sent by the G-Z operator")
            elif src == "R":
                if signer != "founder":
                    raise GateError("R sender role is «غير معرّف في المعمارية»: founder-signed until defined")
            else:
                raise GateError("ت-18 carries messages from G-Z or R only")
            req = self.msg_types.get(st.get("type"))
            if req is None:
                raise GateError("message type is not registered (its fields are «غير معرّف في المعمارية»)")
            fields = st.get("fields")
            if not isinstance(fields, dict) or any(fields.get(k) in (None, "", [], {}) for k in req):
                raise GateError("incomplete message refused: every mandatory field of its type (ت-18; ق-29)")
            cid = st.get("claim_id")
            cc = self._claims()
            if cid != NO_CLAIM and (cc is None or cid not in cc.cards):
                raise GateError("claim_id is a registered Claim ID or «لا ادعاء» (ت-18)")
            if not isinstance(st.get("gold_observation"), bool):
                raise GateError("message declares gold_observation (true/false)")
            if st["gold_observation"]:
                if st.get("tag") != PRIVATE:
                    raise GateError("a gold-data observation is tagged «خاصة» (CS-01-08)")
                if REAL_DATA_LOCKED:
                    raise GateError("gold data is locked (OD-10)")
        elif kind == "path_refusal_logged":
            st = _shape(self._by_role(p, "custody", "log_path_refusal"), "log_path_refusal")
            att = st.get("attempt") or {}
            if att.get("kind") not in self.KINDS or att.get("kind") == kind or "payload" not in att:
                raise GateError("refusal record names the refused attempt")
            try:
                self.validate(att["kind"], att["payload"])
            except (GateError, AuthError, KeyError, ValueError, TypeError):
                return
            raise GateError("not a refusal: the attempt is valid")

    def apply(self, kind, p):
        st = json.loads(bytes.fromhex(p["statement_hex"]))
        if kind == "path_tool_registered":
            self.tools[st["tool_id"]] = st
        elif kind == "path_tool_called":
            self.calls.append(st)
        elif kind == "knowledge_a_registered":
            self.knowledge_a[st["item_id"]] = st
        elif kind == "z_input_admitted":
            self.z_inputs[st["input_id"]] = st
        elif kind == "path_transfer_recorded":
            self.transfers.append(st)
        elif kind == "l10_message_type_registered":
            self.msg_types[st["type"]] = list(st["required_fields"])
        elif kind == "l10_message_recorded":
            self.messages.append(st)
        elif kind == "path_refusal_logged":
            self.refusals.append(st)

    # ---------------- API ----------------
    @staticmethod
    def message_sha256(st: dict) -> str:
        """Hash of a recorded message statement (canonical JSON without the nonce)."""
        body = {k: v for k, v in st.items() if k != "nonce"}
        return hashlib.sha256(json.dumps(body, sort_keys=True, ensure_ascii=False,
                                         separators=(",", ":")).encode("utf-8")).hexdigest()

    def r_messages(self) -> dict:
        return {self.message_sha256(m): m for m in self.messages if m["from"] == "R"}

    def commit(self, kind, s: Signed):
        return self.g._commit(kind, s.to_payload())

    def guarded(self, kind, s: Signed, sign_as_custody):
        """Attempt; on refusal, custody logs the refused attempt and None is returned (nothing leaks)."""
        try:
            return self.commit(kind, s)
        except (GateError, AuthError) as e:
            self.commit("path_refusal_logged", sign_as_custody(
                {"action": "log_path_refusal", "attempt": {"kind": kind, "payload": s.to_payload()},
                 "reason": str(e)}))
            return None
