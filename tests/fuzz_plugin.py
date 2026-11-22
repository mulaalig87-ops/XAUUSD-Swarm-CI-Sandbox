"""Audit-run plugin for the cross-layer malformed-input sweep (WP9-05a). Enabled only with
XS_FUZZ=<output.json>:  XS_FUZZ=out.json python -m pytest -p fuzz_plugin -q

For the FIRST commit of every statement kind anywhere in the suite, BEFORE that commit, each field of the
statement is replaced by malformed values and the result is passed to that same Governance's
_validate + _dry_apply (pure: nothing is written, the test's own state is untouched). Signature checking
is bypassed for these probes only (the signature is not what is under test: a real attacker with a key
can sign any content). Any exception other than GateError / AuthError / LedgerError is a crash."""
import json
import os
import uuid

BAD = [None, True, 0, -1, 10 ** 400, float("nan"), float("inf"), "", " ", [], {}, [[]], {"x": {"y": [None]}},
       ["a", ["b"]], "x" * 5000, [float("nan")], {"": 1}]


def pytest_configure(config):
    out = os.environ.get("XS_FUZZ")
    if not out:
        return
    from xauusd_swarm import charter
    from xauusd_swarm.charter import GateError
    from xauusd_swarm.identity import AuthError
    from xauusd_swarm.ledger import LedgerError
    refusals = (GateError, AuthError, LedgerError)
    done, crashes, probes, accepted, acc_fields = set(), [], [0], [0], set()
    orig_commit, orig_check = charter.Governance._commit, charter.check_signature

    def lenient(pub, s):
        return json.loads(s.statement)

    def commit(self, kind, payload):
        # Probes run BEFORE the original commit, against the state the original statement was valid for
        # (review S1-02 of WP9-04/05a: probing after the commit was masked by "already registered" checks).
        p = payload() if callable(payload) else payload
        if kind not in done and isinstance(p, dict) and "statement_hex" in p:
            done.add(kind)
            st = json.loads(bytes.fromhex(p["statement_hex"]))
            charter.check_signature = lenient
            try:
                self._catch_up(list(self.ledger))
                for f in [k for k in st if k not in ("action", "nonce")]:
                    for bad in BAD:
                        mut = {**st, f: bad, "nonce": uuid.uuid4().hex}
                        try:
                            raw = json.dumps(mut, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
                        except (TypeError, ValueError):
                            continue
                        mp = {**p, "statement_hex": raw.hex()}
                        probes[0] += 1
                        try:
                            self._validate(kind, mp)
                            self._dry_apply(kind, mp)
                            accepted[0] += 1
                            acc_fields.add((kind, f, repr(bad)[:20]))
                        except refusals:
                            pass
                        except Exception as x:          # noqa: BLE001
                            crashes.append({"kind": kind, "field": f, "value": repr(bad)[:40],
                                            "error": f"{type(x).__name__}: {str(x)[:120]}"})
            finally:
                charter.check_signature = orig_check
        return orig_commit(self, kind, p)

    charter.Governance._commit = commit

    def finish():
        with open(out, "w", encoding="utf-8") as fh:
            json.dump({"kinds_probed": sorted(done), "probes": probes[0], "accepted_by_validation": accepted[0],
                       "accepted_fields": sorted(map(list, acc_fields)), "crashes": crashes}, fh,
                      ensure_ascii=False, indent=1)
    config.add_cleanup(finish)
