"""Layer 7 — discovery system: paths, minds, channels, proposals, discovery queue (WP8-07; spec
WP7-01 §2.7, candidate §9, §10, §14.2, §16; WP7-02 ت-09, ت-10, ت-16, م-08, م-09, م-12, م-18, م-19).

This layer is the GOVERNANCE of discovery, not the discovery engines. Engines and language models
are the minds' own components; nothing here runs a model or reads market data. SYNTHETIC ONLY.

Implemented (each cites its source):
- Paths (س 751–758; ق-26): registered by the founder with a path card and a generalisation test
  designed without access to sealed worlds, plus a lineage reference. The list is open; the three
  named paths (distributional regularities, conditional information, distinguisher) need not all
  exist to start (س 755). Every registered path carries card and test, the three named included
  (strictest reading; FD-01-D15). The distinguisher is a discovery tool, not a court and not
  evidence of a law (س 754, 2179): its proposals are tagged so.
- Minds (س 759–767; ق-15, ق-16, ق-17, ق-20; م7-13 #1–#2): a mind is a registered identity holding
  the role discovery_participant (separated from custody, court operator and G-Z operator), with a
  frozen configuration of exactly the seven components; "experiment selection" and "permissions
  and resources" must be declared (م7-13 #1). Classification is DERIVED from the configuration:
  "لغوي" if any engine is a language model, else "محركات" (ق-15). Model Swap changes component 2
  only; DNA Swap changes other components and records exactly what changed (ق-16). Diversity: two
  minds of one family differ in at least one component (ق-17). Resources: the family's rule is
  frozen before any mind of the family is registered: equal compute time per mind (ق-20); every
  mind's resources must state it; the actual number of test instances per mind is reported.
  No fixed share for language minds (س 767): none is enforced or computed.
- Memory and channels (م-04 #1–#2; ت-10; م-18, م-19): each mind's memory is private; any exchange
  goes through a founder-registered channel between the two minds and is a ledger event; a mind
  cannot receive another mind's hypotheses or results in a family before freezing its own
  hypothesis there. Refused attempts are logged by the guard (TP-60.18, TP-60.19, TP-63).
- Proposals and permissions (س 769–776; م7-05, م7-08, ق-06): minds may propose representations,
  questions, interpretations, falsifications and candidate hypotheses. A falsification proposal from
  a language mind names its null model and is ADOPTED only if that null model's card was accepted
  by the founder; otherwise it is recorded and not adopted. Language-mind outputs are tagged
  «غير قابل للتحقق» (س 778). Minds cannot guard the queue, set thresholds or rule (✗ in the table):
  those events are signed by other roles only.
- Discovery queue (ق-03; ق-29; م7-07 #2–#3; ت-16; م-12): definition per the founder's first wording
  (§11 #6): an ordered list of candidate discoveries and hypotheses from the discovery paths,
  before freezing. Guard = frozen rules run by the court operator. Eligibility: registered path,
  full lineage, not "code integrity only". A batch lies between two declared bounds (count bounds;
  FD-01-D16) and its elements are frozen before any test: no admission after the batch is closed,
  no release before. Order changes only by the frozen ordering rule: the order is always COMPUTED
  from that rule, never set by hand; every admission is recorded. Results are independent of
  processing order, checked by re-running (process_batch). Release to testing carries exactly the
  identifier, Claim ID, path, lineage reference and type/path registration; release is not
  scientific acceptance (no status field is accepted).
- Panels (ق-16, س 2226): a panel is consumed by one decision only.
- Knowledge to layer 7 only through layer 3 (ت-09, م-10): this layer has no event that carries
  knowledge-registry content to a mind; such content can only arrive through custody.
NOT implemented / open: the discovery engines themselves; convergence definition and influence
criteria (م-04 #3–#4, CS-04-13); checkpoints' dates; null-card field list (§18.1 #6 not in the
reference copies: «غير معرّف في المعمارية» here — completeness is "all declared fields non-empty");
blind cells (ق-07: not built before "proof of need"); path retirement (س 758 gives a keep rule but no
retirement procedure); L and G sets for ΔL|G are defined (D-01) but no analysis exists (no thresholds).
"""
from __future__ import annotations

import json
import math
import random

from .charter import GateError
from .identity import AuthError, Signed, sign
from .inventory import content_sha256
from .knowledge import LINEAGE
from .numeric import finite_real

COMPONENTS = ("representations", "engines", "statistics_and_nulls", "experiment_selection", "adaptation",
              "memory", "permissions_and_resources")                                  # س 760–766
NAMED_PATHS = ("distributional_regularities", "conditional_information", "distinguisher")   # س 752–754
PROPOSAL_TYPES = ("representation", "question", "interpretation", "falsification", "hypothesis")
PATHS = ("Z", "G-Z", "R")
UNVERIFIABLE = "غير قابل للتحقق"                                                          # س 778
NOT_EVIDENCE = "أداة اكتشاف، ليست دليلًا على قانون"                                       # س 754, 2179
SORT_KEYS = ("admission_index", "path_id", "proposal_id", "mind_id")
GUARD_ROLE = "court_operator"                                                          # م7-07 #3
MIND_FORBIDDEN_ROLES = ("custody", "custody_auditor", "court_operator", "gz_operator", "reid_checker",
                        "governance_auditor", "world_designer")
LANGUAGE = "لغوي"
ENGINES = "محركات"


def _hex64(h) -> bool:
    return isinstance(h, str) and len(h) == 64 and all(c in "0123456789abcdef" for c in h)


def _finite_pos(x) -> bool:
    return finite_real(x) and x > 0


def filled(v) -> bool:
    """Every declared field filled, at every depth (R1-02): no None, no empty or blank string, no
    empty list/dict, and every element / value of a list or dict is itself filled. No optional fields."""
    if v is None:
        return False
    if isinstance(v, str):
        return bool(v.strip())
    if isinstance(v, (list, tuple)):
        return bool(v) and all(filled(x) for x in v)
    if isinstance(v, dict):
        return bool(v) and all(isinstance(k, str) and k.strip() and filled(x) for k, x in v.items())
    if isinstance(v, float):
        return math.isfinite(v)
    return True


def classify(config: dict) -> str:
    """ق-15: «لغوي» if any engine is a language model, else «محركات»."""
    return LANGUAGE if any(e.get("kind") == "llm" for e in config.get("engines", [])) else ENGINES


def lineage_complete(lin) -> bool:
    return isinstance(lin, dict) and all(isinstance(lin.get(p), dict) and all(k in lin[p] for k in ks)
                                         for p, ks in LINEAGE.items())


def queue_order(entries: list[dict], rule: dict) -> list[str]:
    """Order computed from the frozen rule (never set by hand); ties broken by proposal_id."""
    keys = rule["keys"]
    out = sorted(entries, key=lambda e: e["proposal_id"])
    for k in reversed(keys):
        out = sorted(out, key=lambda e: e[k["key"]], reverse=(k["direction"] == "desc"))
    return [e["proposal_id"] for e in out]


def process_batch(items: list[dict], fn, *, seed=0) -> dict:
    """Run fn on every item in three orders (as given, reversed, shuffled) and require identical
    per-item results: results independent of processing order, checked by re-running (ق-03)."""
    def run(seq):
        return {it["proposal_id"]: fn(it) for it in seq}
    a = run(items)
    b = run(list(reversed(items)))
    sh = list(items)
    random.Random(seed).shuffle(sh)
    c = run(sh)
    if not (a == b == c):
        raise GateError("results depend on processing order (ق-03)")
    return a


class DiscoveryLayer:
    KINDS = ("path_registered", "resource_rule_frozen", "mind_registered", "mind_reconfigured",
             "channel_registered", "hypothesis_frozen", "exchange_recorded", "null_card_accepted",
             "proposal_submitted", "queue_rules_frozen", "queue_batch_declared", "queue_entry_admitted",
             "queue_batch_closed", "queue_released", "panel_consumed", "l7_refusal_logged")

    def __init__(self, *, guard_identity: str | None = None, guard_key=None):
        self.guard_identity, self._guard_key = guard_identity, guard_key
        self.paths: dict[str, dict] = {}
        self.resource_rules: dict[str, dict] = {}
        self.minds: dict[str, dict] = {}            # mind_id -> {family, config, versions, class}
        self.channels: dict[str, dict] = {}
        self.frozen_hyp: dict[tuple, list] = {}     # (mind, family) -> hypothesis hashes
        self.exchanges: list[dict] = []
        self.null_cards: dict[str, dict] = {}
        self.proposals: dict[str, dict] = {}
        self.queue_rules: dict[str, dict] = {}
        self.batches: dict[str, dict] = {}
        self.entries: dict[str, dict] = {}          # proposal_id -> entry
        self.released: dict[str, dict] = {}
        self.panels: dict[str, dict] = {}
        self.refusals: list[dict] = []
        self.g = None

    def bind(self, g):
        self.g = g

    def _ext(self, attr):
        return next((x for x in self.g._ext.values() if hasattr(x, attr) and x is not self), None)

    def _roles(self, ident) -> set:
        cl = self._ext("access_log")
        return cl.roles.get(ident, set()) if cl else set()

    def _mind_signed(self, p, action):
        signer = Signed.from_payload(p).identity
        if signer not in self.minds:
            raise GateError(f"{signer!r} is not a registered mind")
        return signer, self.g._signed(p, signer, action)

    def _guard_signed(self, p, action):
        signer = Signed.from_payload(p).identity
        if GUARD_ROLE not in self._roles(signer):
            raise GateError("the queue guard runs as the court operator (م7-07 #3); minds cannot guard the queue (س 773)")
        return self.g._signed(p, signer, action)

    # ---------------- cross-component preconditions ----------------
    def pre_validate(self, kind, p):
        if kind == "role_assigned":
            st = json.loads(bytes.fromhex(p["statement_hex"]))
            if st.get("holder") in self.minds and st.get("role") in MIND_FORBIDDEN_ROLES:
                raise GateError("a mind holds no custody, court, G-Z or audit role (س 769–776; م-08, م-09)")

    # ---------------- validation ----------------
    def validate(self, kind, p):
        if kind == "path_registered":
            st = self.g._signed(p, "founder", "register_path")
            pid = st.get("path_id")
            if not pid or pid in self.paths:
                raise GateError("path needs a new path_id")
            if st.get("kind") not in NAMED_PATHS + ("other",):
                raise GateError(f"path kind is one of {NAMED_PATHS} or 'other' (the list is open, س 756)")
            for k in ("card", "generalisation_test"):
                v = st.get(k) or {}
                if not str(v.get("text", "")).strip() or v.get("sha256") != content_sha256(v.get("text", "")):
                    raise GateError(f"every path carries its {k} with matching hash (س 756; ق-26)")
            if st.get("designers_without_sealed_access") is not True:
                raise GateError("the generalisation test is designed without access to sealed worlds (ق-26)")
            if not _hex64(st.get("lineage_sha256")):
                raise GateError("every path addition carries its lineage (س 756)")
        elif kind == "resource_rule_frozen":
            st = self.g._signed(p, "founder", "freeze_resource_rule")
            fam = st.get("family")
            if not fam or fam in self.resource_rules:
                raise GateError("one frozen resource rule per family; not edited after results (م7-13 #2)")
            if any(m["family"] == fam for m in self.minds.values()):
                raise GateError("the resource rule is frozen before any mind works in the family")
            if st.get("rule") != "equal_compute_time" or not _finite_pos(st.get("compute_seconds")):
                raise GateError("rule: equal compute time per mind, with a finite positive amount (ق-20; R1-03)")
        elif kind in ("mind_registered", "mind_reconfigured"):
            act = "register_mind" if kind == "mind_registered" else "reconfigure_mind"
            st = self.g._signed(p, "founder", act)
            mid, cfg = st.get("mind_id"), st.get("config")
            if kind == "mind_registered":
                if not mid or mid in self.minds:
                    raise GateError("mind needs a new mind_id")
                if mid not in self.g.keys():
                    raise GateError("a mind is a registered identity (its key signs its acts)")
                roles = self._roles(mid)
                if "discovery_participant" not in roles or roles & set(MIND_FORBIDDEN_ROLES):
                    raise GateError("a mind holds the discovery_participant role and no separated role")
                fam = st.get("family")
            else:
                if mid not in self.minds:
                    raise GateError("unknown mind")
                fam = self.minds[mid]["family"]
            rr = self.resource_rules.get(fam)
            if rr is None:
                raise GateError("the family's resource rule is frozen first (م7-13 #2; ق-20)")
            if not isinstance(cfg, dict) or set(cfg) != set(COMPONENTS):
                raise GateError(f"a mind is a search policy of exactly seven components (س 759): {COMPONENTS}")
            if not cfg["experiment_selection"] or not cfg["permissions_and_resources"]:
                raise GateError("experiment selection and permissions/resources are declared in the configuration (م7-13 #1)")
            if not isinstance(cfg["engines"], list) or not cfg["engines"] or any(
                    e.get("kind") not in ("llm", "engine") or not e.get("name") for e in cfg["engines"]):
                raise GateError("engines: list of {name, kind: llm|engine}")
            res = cfg["permissions_and_resources"]
            if not isinstance(res, dict) or not _finite_pos(res.get("compute_seconds")) \
                    or res["compute_seconds"] != rr["compute_seconds"]:
                raise GateError("equal compute time per mind: the family's frozen amount (ق-20)")
            if st.get("classification") is not None:
                raise GateError("the classification is derived from the configuration, not declared (ق-15)")
            for oid, o in self.minds.items():
                if oid != mid and o["family"] == fam and content_sha256(o["config"]) == content_sha256(cfg):
                    raise GateError("diversity: minds of a family differ in at least one component (ق-17)")
            if kind == "mind_reconfigured":
                old = self.minds[mid]["config"]
                changed = sorted(c for c in COMPONENTS if content_sha256(old[c]) != content_sha256(cfg[c]))
                sw = st.get("swap")
                if sw == "model":
                    if changed != ["engines"]:
                        raise GateError(f"Model Swap changes component 2 (engines) only (ق-16); changed: {changed}")
                elif sw == "dna":
                    if not changed or "engines" in changed:
                        raise GateError("DNA Swap changes components other than the engines (ق-16)")
                    if sorted(st.get("changed") or []) != changed:
                        raise GateError(f"DNA Swap records exactly what changed (ق-16): {changed}")
                else:
                    raise GateError("a reconfiguration is a Model Swap or a DNA Swap (ق-16)")
        elif kind == "channel_registered":
            st = self.g._signed(p, "founder", "register_channel")
            cid, a, b = st.get("channel_id"), st.get("mind_a"), st.get("mind_b")
            if not cid or cid in self.channels or a == b or a not in self.minds or b not in self.minds:
                raise GateError("a channel links two registered minds (م-04 #1)")
        elif kind == "hypothesis_frozen":
            mid, st = self._mind_signed(p, "freeze_hypothesis")
            if st.get("family") != self.minds[mid]["family"] or not _hex64(st.get("hypothesis_sha256")):
                raise GateError("a mind freezes a hypothesis (hash) in its own family")
        elif kind == "exchange_recorded":
            mid, st = self._mind_signed(p, "exchange")
            ch = self.channels.get(st.get("channel_id"))
            to = st.get("to")
            if ch is None or {ch["mind_a"], ch["mind_b"]} != {mid, to}:
                raise GateError("exchange between two minds only through a registered channel (م-04 #1; م-19)")
            if st.get("content_type") not in ("hypothesis", "result", "other") or not _hex64(st.get("content_sha256")):
                raise GateError("exchange records its content type and hash")
            fam = self.minds[mid]["family"]
            if st["content_type"] in ("hypothesis", "result") and self.minds[to]["family"] == fam \
                    and not self.frozen_hyp.get((to, fam)):
                raise GateError("no access to another mind's hypotheses or results in the family before "
                                "freezing one's own hypothesis (م-04 #2; م-18)")
        elif kind == "null_card_accepted":
            st = self.g._signed(p, "founder", "accept_null_card")
            nm, card = st.get("null_model"), st.get("card")
            if not isinstance(nm, str) or not nm.strip():
                raise GateError("null card names its null model")
            if nm in self.null_cards:
                raise GateError("an accepted null card is never replaced (R1-01): a revised card is a new null model "
                                "identity, with supersedes naming the old one")
            if st.get("supersedes") is not None and st["supersedes"] not in self.null_cards:
                raise GateError("supersedes names an accepted null model")
            if not isinstance(card, dict) or not filled(card):
                raise GateError("null card: every declared field filled, at every depth (automated completeness, ق-06; R1-02)")
        elif kind == "proposal_submitted":
            mid, st = self._mind_signed(p, "propose")
            pid = st.get("proposal_id")
            if not pid or pid in self.proposals:
                raise GateError("proposal needs a new proposal_id")
            if st.get("type") not in PROPOSAL_TYPES:
                raise GateError(f"proposal type is one of {PROPOSAL_TYPES} (س 771–772)")
            if st.get("family") != self.minds[mid]["family"]:
                raise GateError("a mind proposes in its own family")
            if st.get("path_id") not in self.paths:
                raise GateError("proposals come from a registered discovery path (ق-03)")
            if not _hex64(st.get("content_sha256")):
                raise GateError("proposal carries its content hash")
            if not lineage_complete(st.get("lineage")):
                raise GateError("proposal carries its full lineage (ق-03)")
            llm = self.minds[mid]["class"] == LANGUAGE
            if st["lineage"]["knowledge"]["llm_in_lineage"] is not llm:
                raise GateError("lineage must state whether a language model is in it, as the configuration says")
            if st["type"] == "falsification" and llm and not st.get("null_model"):
                raise GateError("a language mind's falsification proposal names its null model (م7-08 #1)")
        elif kind == "queue_rules_frozen":
            st = self.g._signed(p, "founder", "freeze_queue_rules")
            fam = st.get("family")
            if not fam or fam in self.queue_rules:
                raise GateError("one frozen queue rule set per family")
            keys = st.get("keys")
            if not isinstance(keys, list) or not keys or any(
                    k.get("key") not in SORT_KEYS or k.get("direction") not in ("asc", "desc") for k in keys):
                raise GateError(f"ordering rule: list of {{key in {SORT_KEYS}, direction asc|desc}}")
        elif kind == "queue_batch_declared":
            st = self.g._signed(p, "founder", "declare_queue_batch")
            bid, fam = st.get("batch_id"), st.get("family")
            if not bid or bid in self.batches or fam not in self.queue_rules:
                raise GateError("a batch needs a new id and its family's frozen queue rules")
            lo, hi = st.get("min_items"), st.get("max_items")
            if not all(isinstance(x, int) and not isinstance(x, bool) for x in (lo, hi)) or not 1 <= lo <= hi:
                raise GateError("a batch lies between two declared bounds: 1 <= min_items <= max_items (ق-03)")
            if any(b["family"] == fam and not b["closed"] for b in self.batches.values()):
                raise GateError("one open batch per family")
        elif kind == "queue_entry_admitted":
            st = self._guard_signed(p, "queue_admit")
            pr = self.proposals.get(st.get("proposal_id"))
            b = self.batches.get(st.get("batch_id"))
            if pr is None or b is None or pr["family"] != b["family"]:
                raise GateError("admission names a proposal and a batch of its family")
            if b["closed"]:
                raise GateError("the batch is closed: its elements are frozen (ق-03)")
            if st["proposal_id"] in self.entries:
                raise GateError("a proposal enters the queue once")
            if pr.get("code_integrity_only"):
                raise GateError("'code integrity only' results never enter the discovery queue (س 716; م-12)")
            if pr["type"] not in ("hypothesis", "falsification"):
                raise GateError("the queue holds candidate discoveries and hypotheses (§11 #6)")
            if pr["type"] == "falsification" and not pr["adopted"]:
                raise GateError("a language mind's falsification without an accepted null card is recorded, not adopted (م7-08 #2)")
            if sum(1 for e in self.entries.values() if e["batch_id"] == b["batch_id"]) >= b["max_items"]:
                raise GateError("the batch is at its declared upper bound (ق-03)")
        elif kind == "queue_batch_closed":
            st = self._guard_signed(p, "queue_close")
            b = self.batches.get(st.get("batch_id"))
            if b is None or b["closed"]:
                raise GateError("unknown or already closed batch")
            n = sum(1 for e in self.entries.values() if e["batch_id"] == b["batch_id"])
            if n < b["min_items"]:
                raise GateError(f"the batch is below its declared lower bound ({n} < {b['min_items']}) (ق-03)")
            if st.get("order") != self.order(b["batch_id"]):
                raise GateError("the frozen order is the one computed by the frozen rule (م7-07 #2)")
        elif kind == "queue_released":
            st = self._guard_signed(p, "queue_release")
            allowed = {"action", "nonce", "proposal_id", "claim_id", "path", "lineage_sha256", "type_registration"}
            if set(st) != allowed:
                raise GateError("release carries exactly id, Claim ID, path, lineage reference and type/path "
                                "registration (ت-16); passing is not scientific acceptance")
            e = self.entries.get(st["proposal_id"])
            if e is None or not self.batches[e["batch_id"]]["closed"]:
                raise GateError("release only from a closed batch: elements frozen before any test (ق-03)")
            if st["proposal_id"] in self.released:
                raise GateError("released once")
            if st["path"] not in PATHS:
                raise GateError("path is Z, G-Z or R")
            cc, court = self._ext("cards"), self._ext("identities")
            if cc is None or st["claim_id"] not in cc.cards or court is None or st["claim_id"] not in court.identities:
                raise GateError("release names a registered claim with its Claim ID (ت-16)")
            pr = self.proposals[st["proposal_id"]]
            if st["lineage_sha256"] != content_sha256(pr["lineage"]):
                raise GateError("lineage reference must be the proposal's lineage")
            if st["type_registration"] != {"type": pr["type"], "path_id": pr["path_id"]}:
                raise GateError("type and path registration must be the proposal's")
        elif kind == "panel_consumed":
            st = self.g._signed(p, "founder", "consume_panel")
            pid = st.get("panel_id")
            if not pid or pid in self.panels:
                raise GateError("a panel is consumed by one decision only (ق-16; س 2226)")
            if not str(st.get("decision_ref", "")).strip() or not isinstance(st.get("configurations"), list) \
                    or not st["configurations"]:
                raise GateError("panel consumption names its decision and configurations")
            known = {content_sha256(v) for m in self.minds.values() for v in m["versions"]}
            if any(c not in known for c in st["configurations"]):
                raise GateError("panel configurations must be hashes of recorded mind configurations")
        elif kind == "l7_refusal_logged":
            st = self._guard_signed(p, "l7_refusal")
            att = st.get("attempt") or {}
            if att.get("kind") not in self.KINDS or "payload" not in att:
                raise GateError("refusal record names the refused attempt")
            try:
                self.validate(att["kind"], att["payload"])
            except (GateError, AuthError, KeyError, ValueError, TypeError):
                return
            raise GateError("not a refusal: the attempt is valid")

    def apply(self, kind, p):
        st = json.loads(bytes.fromhex(p["statement_hex"]))
        if kind == "path_registered":
            self.paths[st["path_id"]] = st
        elif kind == "resource_rule_frozen":
            self.resource_rules[st["family"]] = st
        elif kind == "mind_registered":
            self.minds[st["mind_id"]] = {"family": st["family"], "config": st["config"], "versions": [st["config"]],
                                         "class": classify(st["config"])}
        elif kind == "mind_reconfigured":
            m = self.minds[st["mind_id"]]
            m["config"] = st["config"]
            m["versions"].append(st["config"])
            m["class"] = classify(st["config"])
        elif kind == "channel_registered":
            self.channels[st["channel_id"]] = st
        elif kind == "hypothesis_frozen":
            signer = Signed.from_payload(p).identity
            self.frozen_hyp.setdefault((signer, st["family"]), []).append(st["hypothesis_sha256"])
        elif kind == "exchange_recorded":
            self.exchanges.append({**st, "from": Signed.from_payload(p).identity})
        elif kind == "null_card_accepted":
            self.null_cards[st["null_model"]] = st
        elif kind == "proposal_submitted":
            mid = Signed.from_payload(p).identity
            m = self.minds[mid]
            tags = []
            if m["class"] == LANGUAGE:
                tags.append(UNVERIFIABLE)
            if self.paths[st["path_id"]].get("kind") == "distinguisher":
                tags.append(NOT_EVIDENCE)
            adopted, card_sha = True, None
            if st["type"] == "falsification" and m["class"] == LANGUAGE:
                adopted = st.get("null_model") in self.null_cards
                if adopted:
                    card_sha = content_sha256(self.null_cards[st["null_model"]]["card"])
            self.proposals[st["proposal_id"]] = {**st, "mind_id": mid, "tags": tags, "adopted": adopted,
                                                 "null_card_sha256": card_sha,
                                                 "config_sha256": content_sha256(m["config"])}
        elif kind == "queue_rules_frozen":
            self.queue_rules[st["family"]] = st
        elif kind == "queue_batch_declared":
            self.batches[st["batch_id"]] = {**st, "closed": False}
        elif kind == "queue_entry_admitted":
            pr = self.proposals[st["proposal_id"]]
            self.entries[st["proposal_id"]] = {"proposal_id": st["proposal_id"], "batch_id": st["batch_id"],
                                               "admission_index": len(self.entries), "path_id": pr["path_id"],
                                               "mind_id": pr["mind_id"]}
        elif kind == "queue_batch_closed":
            self.batches[st["batch_id"]]["closed"] = True
            self.batches[st["batch_id"]]["order"] = st["order"]
        elif kind == "queue_released":
            self.released[st["proposal_id"]] = st
        elif kind == "panel_consumed":
            self.panels[st["panel_id"]] = st
        elif kind == "l7_refusal_logged":
            self.refusals.append(st)

    # ---------------- API ----------------
    def order(self, batch_id) -> list[str]:
        b = self.batches[batch_id]
        return queue_order([e for e in self.entries.values() if e["batch_id"] == batch_id],
                           self.queue_rules[b["family"]])

    def commit(self, kind, s: Signed):
        return self.g._commit(kind, s.to_payload())

    def _gsign(self, statement):
        if self._guard_key is None:
            raise GateError("this layer holds no guard key")
        import uuid
        return sign(self.guard_identity, self._guard_key, {**statement, "nonce": uuid.uuid4().hex})

    def guarded(self, kind, s: Signed):
        """Commit an attempt; if refused, the guard logs the refusal (refused and recorded) and re-raises."""
        try:
            return self.commit(kind, s)
        except (GateError, AuthError) as x:
            if self._guard_key is not None:
                self.commit("l7_refusal_logged", self._gsign({"action": "l7_refusal", "reason": str(x)[:300],
                                                              "attempt": {"kind": kind, "payload": s.to_payload()}}))
            raise

    def admit(self, proposal_id, batch_id):
        return self.commit("queue_entry_admitted", self._gsign({"action": "queue_admit", "proposal_id": proposal_id,
                                                                "batch_id": batch_id}))

    def close_batch(self, batch_id):
        return self.commit("queue_batch_closed", self._gsign({"action": "queue_close", "batch_id": batch_id,
                                                              "order": self.order(batch_id)}))

    def release(self, proposal_id, claim_id, path):
        pr = self.proposals[proposal_id]
        return self.commit("queue_released", self._gsign({
            "action": "queue_release", "proposal_id": proposal_id, "claim_id": claim_id, "path": path,
            "lineage_sha256": content_sha256(pr["lineage"]),
            "type_registration": {"type": pr["type"], "path_id": pr["path_id"]}}))

    def instances_per_mind(self, family) -> dict:
        """Actual number of test instances per mind (ق-20): court instances of claims released from
        each mind's proposals."""
        court = self._ext("identities")
        out = {m: 0 for m, v in self.minds.items() if v["family"] == family}
        for pid, r in self.released.items():
            mid = self.proposals[pid]["mind_id"]
            if mid in out and court is not None:
                out[mid] += sum(1 for t in court.instances.values() if t["claim_id"] == r["claim_id"])
        return out
