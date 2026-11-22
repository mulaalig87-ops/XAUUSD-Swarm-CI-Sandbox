"""Cross-layer malformed-input test (WP9-01 review S1-01; before WP9-05). SYNTHETIC ONLY.

Every statement kind accepted in the full synthetic pipeline (test_integration) is taken from the ledger,
then each of its fields is replaced by malformed values (wrong types, unhashable containers, NaN, ±inf,
huge ints, bools, None, empty, deep nesting), re-signed by the same signer with a fresh nonce, and
submitted. The rule under test: a malformed statement is REFUSED with a governance refusal
(GateError / AuthError / LedgerError) — never a crash with another exception — and nothing is written.
"""
import json
import uuid

import pytest

import test_integration as TI
from xauusd_swarm.charter import GateError
from xauusd_swarm.identity import AuthError, Signed, sign
from xauusd_swarm.ledger import Ledger, LedgerError

BAD = [None, True, 0, -1, 10 ** 400, float("nan"), float("inf"), "", " ", [], {}, [[]], {"x": {"y": [None]}},
       ["a", ["b"]], "x" * 10000, [float("nan")], {"": 1}]
REFUSALS = (GateError, AuthError, LedgerError)
KEY = {"founder": TI.FK, **TI.KEYS}


def _probe_before_commit(results):
    """Wrap Governance._commit so that, before the FIRST commit of each kind, every field of the statement
    is replaced by malformed values, RE-SIGNED with the signer's real key and checked with _validate +
    _dry_apply (pure: nothing written). Probing before the original commit avoids masking by "already
    registered" checks (review S1-02)."""
    from xauusd_swarm import charter
    orig = charter.Governance._commit

    def commit(self, kind, payload):
        p = payload() if callable(payload) else payload
        if kind not in results["kinds"] and isinstance(p, dict) and "statement_hex" in p:
            signer = Signed.from_payload(p).identity
            if signer in KEY:
                results["kinds"].add(kind)
                st = json.loads(bytes.fromhex(p["statement_hex"]))
                self._catch_up(list(self.ledger))
                for field in [k for k in st if k not in ("action", "nonce")]:
                    for bad in BAD:
                        try:
                            mp = {**p, **sign(signer, KEY[signer], {**st, field: bad, "nonce": uuid.uuid4().hex})
                                  .to_payload()}
                        except (TypeError, ValueError):
                            continue
                        results["probes"] += 1
                        try:
                            self._validate(kind, mp)
                            self._dry_apply(kind, mp)
                        except REFUSALS:
                            pass
                        except Exception as x:               # noqa: BLE001 — the point of the test
                            results["crashes"].append((kind, field, repr(bad)[:40], type(x).__name__, str(x)[:80]))
        return orig(self, kind, p)
    return orig, commit


def test_every_kind_refuses_malformed_fields_without_crashing(monkeypatch):
    from xauusd_swarm import charter
    results = {"kinds": set(), "probes": 0, "crashes": []}
    _, commit = _probe_before_commit(results)
    monkeypatch.setattr(charter.Governance, "_commit", commit)
    s = TI.System(Ledger())
    TI.run_pipeline(s)                                       # the pipeline itself must still succeed
    assert len(results["kinds"]) >= 30 and results["probes"] > 1000
    assert not results["crashes"], "\n".join(map(str, results["crashes"][:40]))


@pytest.mark.heavy
def test_suite_wide_sweep_finds_no_crash(tmp_path):
    """Re-runs the suite-wide sweep (tests/fuzz_plugin.py) in a subprocess and requires zero crashes and at
    least as many probed kinds as the recorded run (docs/results/WP9-05a_malformed_sweep.json)."""
    import os
    import subprocess
    import sys
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    out = tmp_path / "sweep.json"
    env = {**os.environ, "XS_FUZZ": str(out), "PYTHONPATH": str(root / "src")}
    subprocess.run([sys.executable, "-m", "pytest", "-p", "fuzz_plugin", "-q", "-p", "no:cacheprovider",
                    "-m", "not heavy", "-x"],
                   cwd=root / "tests", env=env, capture_output=True, timeout=1800)
    got = json.loads(out.read_text(encoding="utf-8"))
    ref = json.loads((root / "docs" / "results" / "WP9-05a_malformed_sweep.json").read_text(encoding="utf-8"))
    assert got["crashes"] == []
    assert set(got["kinds_probed"]) >= set(ref["kinds_probed"])
