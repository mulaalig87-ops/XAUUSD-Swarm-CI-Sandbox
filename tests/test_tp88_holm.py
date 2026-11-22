"""TP-88 (م5-21; WP7-04 §11.3): the within-path procedure under dependence — FWER part only.

Runs the court's own Holm implementation (court.holm) on synthetic worlds whose null hypotheses are
ALL true, under the five dependence structures named in §11.3, and measures FWER with its Monte
Carlo standard error, at path level and at the unique-claim level with claims duplicated across
paths (structure B; inequality 5, س 678).

NOT run here (stated): the FDR part and mixed worlds — no FDR procedure is built and FWER vs FDR
is still open (س 610; WP7-05 §8). Synthetic worlds only; nothing here is a statement about gold
(م5-11: synthetic results do not transfer by themselves).

Pre-registered (fixed in this file before the run; hash printed by test_registration_hash):
"""
import hashlib
import json
import math
import random

import pytest

from xauusd_swarm.court import holm

REGISTRATION = {
    "nominal_alpha": 0.05,
    "m_tests_per_path": 10,
    "replications": 4000,
    "seed": 20261117,
    "structures": {
        "independent": {},
        "equicorrelated_positive": {"rho": 0.5},
        "block": {"block_size": 3, "rho_within": 0.8},
        "mixed_sign": {"pair_rho": -0.5},
        "shared_time_data": {"window": 5, "shift": 1},
    },
    "unique_claim_level": {"paths": ["Z", "G-Z", "R"], "alpha_by_path": "alpha_total / 3", "claims": 6,
                           "membership": {"c1": ["Z", "G-Z", "R"], "c2": ["Z", "G-Z"], "c3": ["Z"], "c4": ["G-Z", "R"],
                                          "c5": ["R"], "c6": ["Z", "R"]}, "cross_path_rho": 0.7},
    "pass_rule": "FWER_hat <= alpha + 3 * MCSE, MCSE = sqrt(alpha(1-alpha)/replications)",
}


def _phi_upper(z):
    return 0.5 * math.erfc(z / math.sqrt(2))


def _draw(structure, m, rnd):
    if structure == "independent":
        return [rnd.gauss(0, 1) for _ in range(m)]
    if structure == "equicorrelated_positive":
        r = REGISTRATION["structures"][structure]["rho"]
        w = rnd.gauss(0, 1)
        return [math.sqrt(r) * w + math.sqrt(1 - r) * rnd.gauss(0, 1) for _ in range(m)]
    if structure == "block":
        p = REGISTRATION["structures"][structure]
        out = []
        while len(out) < m:
            w = rnd.gauss(0, 1)
            out += [math.sqrt(p["rho_within"]) * w + math.sqrt(1 - p["rho_within"]) * rnd.gauss(0, 1)
                    for _ in range(p["block_size"])]
        return out[:m]
    if structure == "mixed_sign":
        r = REGISTRATION["structures"][structure]["pair_rho"]
        out = []
        while len(out) < m:
            a = rnd.gauss(0, 1)
            out += [a, r * a + math.sqrt(1 - r * r) * rnd.gauss(0, 1)]
        return out[:m]
    if structure == "shared_time_data":
        p = REGISTRATION["structures"][structure]
        e = [rnd.gauss(0, 1) for _ in range(p["window"] + p["shift"] * (m - 1))]
        return [sum(e[i * p["shift"]:i * p["shift"] + p["window"]]) / math.sqrt(p["window"]) for i in range(m)]
    raise ValueError(structure)


def _bound():
    a, n = REGISTRATION["nominal_alpha"], REGISTRATION["replications"]
    return a + 3 * math.sqrt(a * (1 - a) / n)


def test_registration_hash():
    h = hashlib.sha256(json.dumps(REGISTRATION, sort_keys=True).encode()).hexdigest()
    print(f"TP-88 registration sha256 {h}")
    assert h == "fb7d0da123ea7f0bccac0a52f5221de015d2ad54fbc7dd562b2809bb001226d5"   # pinned (review R1-02; RELEASES WP8-06)


@pytest.mark.parametrize("structure", list(REGISTRATION["structures"]))
def test_tp88_holm_fwer_within_path_under_dependence(structure):
    a, m, n = REGISTRATION["nominal_alpha"], REGISTRATION["m_tests_per_path"], REGISTRATION["replications"]
    rnd = random.Random(f"{REGISTRATION['seed']}-{structure}")
    hits = 0
    for _ in range(n):
        z = _draw(structure, m, rnd)
        dec = holm([(f"t{i}", _phi_upper(zi)) for i, zi in enumerate(z)], a)
        hits += any(v == "rejected" for v in dec.values())
    fwer, mcse = hits / n, math.sqrt(a * (1 - a) / n)
    print(f"TP-88 {structure}: FWER {fwer:.4f} (MCSE {mcse:.4f}, bound {_bound():.4f})")
    assert fwer <= _bound()


def test_tp88_unique_claim_fwer_structure_b():
    U = REGISTRATION["unique_claim_level"]
    a, n = REGISTRATION["nominal_alpha"], REGISTRATION["replications"]
    a_i = a / len(U["paths"])
    rho = U["cross_path_rho"]
    rnd = random.Random(f"{REGISTRATION['seed']}-unique")
    unique_hits, path_hits = 0, {p: 0 for p in U["paths"]}
    for _ in range(n):
        rejected = set()
        common = {c: rnd.gauss(0, 1) for c in U["membership"]}               # same claim, correlated across paths
        for path in U["paths"]:
            ps = [(c, _phi_upper(math.sqrt(rho) * common[c] + math.sqrt(1 - rho) * rnd.gauss(0, 1)))
                  for c, paths in U["membership"].items() if path in paths]
            dec = holm(ps, a_i)
            r = {c for c, v in dec.items() if v == "rejected"}
            path_hits[path] += bool(r)
            rejected |= r                                                        # R = ∪ R_i (س 669)
        unique_hits += bool(rejected)                                            # all nulls true: V = |R|
    fwer_u = unique_hits / n
    print(f"TP-88 unique-claim FWER {fwer_u:.4f}; per path {({k: v / n for k, v in path_hits.items()})}")
    assert fwer_u <= _bound()                                                    # FWER_unique ≤ Σ α_i ≤ α_total (س 678)
    assert unique_hits <= sum(path_hits.values())                                # P(V≥1) ≤ Σ P(V_i≥1), empirically


def test_tp88_negative_control_unadjusted_procedure_fails():
    """Negative control: per-test α without correction must exceed the bound, so the measurement
    can detect a procedure that does not control FWER."""
    a, m, n = REGISTRATION["nominal_alpha"], REGISTRATION["m_tests_per_path"], REGISTRATION["replications"]
    rnd = random.Random(f"{REGISTRATION['seed']}-negative")
    hits = sum(any(_phi_upper(z) <= a for z in _draw("independent", m, rnd)) for _ in range(n))
    assert hits / n > _bound()
