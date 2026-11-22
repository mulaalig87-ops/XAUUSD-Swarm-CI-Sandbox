"""G4 unit tests: lineage capture and rules (no experiment run here). SYNTHETIC ONLY."""
import random

from xauusd_swarm.leakcheck import build, lineage_check, z_test


def _flags(kind, frac=None):
    h, lin, ctx, tgt = build(kind, random.Random(1), frac)
    return lineage_check(lin, ctx)


def test_clean_pipeline_not_flagged():
    assert _flags("t0") == []


def test_each_captured_type_flags_its_rule():
    assert _flags("t1") == ["R-target"]
    assert _flags("t2") == ["R-window"]
    assert _flags("t3") == ["R-norm"]
    assert _flags("t4") == ["R-version"]
    assert _flags("t5") == ["R-estimate"]
    assert _flags("t6") == ["R-time"]
    assert _flags("t7") == ["R-provenance"]


def test_bypassing_and_implicit_types_are_invisible_to_this_check():
    assert _flags("t8", 0.3) == []          # bypasses the builder
    assert _flags("t9") == []               # implicit encoding inside a vendor field


def test_z_test_direct_target_is_extreme():
    h, lin, ctx, tgt = build("t1", random.Random(2))
    assert abs(z_test(h, tgt)) > 100
