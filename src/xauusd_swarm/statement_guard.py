"""Statement guard (WP9-05a, cross-layer malformed-input test; FL-014). Applied by Governance to EVERY
signed statement before any layer's own validation, so that malformed values are refused uniformly and
never reach a dict lookup, a set or arithmetic. Field roles are recognised by name, following the naming
used throughout the package:
- identifiers: names ending in "_id", and family, holder, slice, plan_id (the key identity is checked
  in key registration) → non-empty text
  (stripped), at most 200 characters;
- hashes: names ending in "sha256" → 64 lowercase hex characters (or a {"text","sha256"} document's
  "sha256", which is checked where it occurs);
- objects: config, attempt, inventory → an object; key-like: to, tool_kind, epoch → text or integer;
- text (non-empty): time, requester, item, boundaries, decision_ref, audit_ref, code_version,
  procedure, seeds, statistic, transform_version, text, type, register_ref, stationarity_method, use_key;
  text (may be empty): reason; integers: rule_version, family_size, mismatches (a count);
- flags: authenticated, passed, blinded, conflict, designers_without_sealed_access, null_card_accepted,
  gold_observation, tie_includes_ambiguous → bool;
- anywhere in the statement (recursively): no NaN or ±inf (no statement needs them).
Kind-specific shapes (BY_KIND) take precedence over the name roles. Layer validators still apply their
own rules; this guard only removes malformed shapes."""
from __future__ import annotations

import math

from .charter import GateError

ID_NAMES = {"family", "holder", "slice", "plan_id", "null_model", "null", "basic_null"}     # "identity" is also a claim-identity object
OBJECT_NAMES = {"config", "attempt", "inventory"}            # always objects where they occur
KEYLIKE_NAMES = {"to", "tool_kind", "epoch"}                 # used as dict / set keys: text or integer
TEXT_NAMES = {"time", "requester", "item", "boundaries", "decision_ref", "audit_ref", "code_version",
              "procedure", "seeds", "statistic", "transform_version", "text", "type", "register_ref",
              "stationarity_method", "use_key"}               # non-empty text (WP9-05b accepted-value review)
TEXT_ANY_NAMES = {"reason"}                                   # text, may be empty (e.g. a concurring attestation)
INT_NAMES = {"rule_version", "family_size", "mismatches"}                  # integers, never bool
LSTR_NAMES: set = set()
FLAG_NAMES = {"authenticated", "passed", "blinded", "conflict", "designers_without_sealed_access", "null_card_accepted",
              "gold_observation", "tie_includes_ambiguous"}


# Field shapes that depend on the statement kind (WP9-05b sweep, probes before the original commit).
T_STR, T_DICT, T_LSTR, T_LDICT = "text", "object", "list of text", "list of objects"
BY_KIND = {
    "adequacy_reported": {"claims": T_LSTR, "source_slices": T_LSTR, "exclusions": T_LDICT},
    "channel_registered": {"mind_a": T_STR, "mind_b": T_STR},
    "claim_identity_registered": {"identity": T_DICT},
    "confirmation_submitted": {"unit_slices": T_LSTR, "claims": T_LDICT},
    "control_registered": {"target": T_DICT, "expected": T_DICT},
    "court_ruling": {"attestation": T_DICT, "request": T_DICT, "output": T_DICT},
    "null_validity_recorded": {"control_results": T_LSTR},
    "final_opened": {"openings": T_LDICT},
    "key_registered": {"identity": T_STR, "public_key_hex": T_STR},
    "knowledge_recorded": {"claim_meta": T_DICT, "row": T_DICT, "lineage_seals": T_DICT},
    "panel_consumed": {"configurations": T_LSTR},
    "path_registered": {"card": T_DICT, "generalisation_test": T_DICT},
    "queue_rules_frozen": {"keys": T_LDICT},
    "slice_plan_frozen": {"slices": T_LDICT},
    "slices_merge_decided": {"slices": T_LSTR},
    "split_design_recorded": {"rules": T_DICT},
    "tool_row_registered": {"controls": T_LSTR, "criterion": T_DICT},
    "transform_estimated": {"estimated_from_slice": T_STR},
    "transform_frozen": {"spec": T_STR, "outputs": T_LSTR},
    "vault_verified": {"commitments": T_LSTR},
}


def _shape_ok(v, t) -> bool:
    if t == T_STR:
        return isinstance(v, str)
    if t == T_DICT:
        return isinstance(v, dict)
    if t == T_LSTR:
        return isinstance(v, list) and all(isinstance(x, str) for x in v)
    if t == T_LDICT:
        return isinstance(v, list) and all(isinstance(x, dict) for x in v)
    raise ValueError(t)


def _hex64(v) -> bool:
    return isinstance(v, str) and len(v) == 64 and all(c in "0123456789abcdef" for c in v)


def _no_nonfinite(v, path):
    if isinstance(v, float) and not math.isfinite(v):
        raise GateError(f"{path}: NaN / inf is not a valid statement value")
    if isinstance(v, dict):
        for k, x in v.items():
            _no_nonfinite(x, f"{path}.{k}")
    elif isinstance(v, list):
        for i, x in enumerate(v):
            _no_nonfinite(x, f"{path}[{i}]")


def check_statement(st, kind: str | None = None) -> None:
    if not isinstance(st, dict):
        raise GateError("a statement is an object")
    for k, t in BY_KIND.get(kind, {}).items():
        if k in st and not _shape_ok(st[k], t):
            raise GateError(f"{kind}.{k}: {t} required")
    for k, v in st.items():
        if k in BY_KIND.get(kind, {}):
            continue
        if k in ("action", "nonce"):
            continue
        if k.endswith("_id") or k in ID_NAMES:
            if not isinstance(v, str) or not v.strip() or len(v) > 200:
                raise GateError(f"{k}: an identifier is non-empty text of at most 200 characters")
        elif k.endswith("sha256"):
            if not _hex64(v):
                raise GateError(f"{k}: a SHA-256 hash is 64 lowercase hex characters")
        elif k in OBJECT_NAMES:
            if not isinstance(v, dict):
                raise GateError(f"{k}: an object is required")
        elif k in KEYLIKE_NAMES:
            if isinstance(v, bool) or not isinstance(v, (str, int)) or (isinstance(v, str) and not v.strip()):
                raise GateError(f"{k}: non-empty text or an integer")
        elif k in TEXT_NAMES:
            if not isinstance(v, str) or not v.strip():
                raise GateError(f"{k}: non-empty text required")
        elif k in TEXT_ANY_NAMES:
            if not isinstance(v, str):
                raise GateError(f"{k}: text required")
        elif k in INT_NAMES:
            if isinstance(v, bool) or not isinstance(v, int) or v < 0:
                raise GateError(f"{k}: a non-negative integer is required")
        elif k in LSTR_NAMES:
            if not isinstance(v, list) or any(not isinstance(x, str) for x in v):
                raise GateError(f"{k}: a list of text is required")
        elif k in FLAG_NAMES:
            if not isinstance(v, bool):
                raise GateError(f"{k}: a flag is true or false")
    _no_nonfinite(st, "statement")
