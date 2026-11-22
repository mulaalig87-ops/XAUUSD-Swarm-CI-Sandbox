"""Path 1 (P1-distributional) unit tests. SYNTHETIC ONLY."""
import random

import pytest

from xauusd_swarm.path1 import PathError, cell_stats, ks_distance, scan, segment_labels


def test_ks_distance_known_values():
    assert ks_distance([1, 2, 3], [1, 2, 3]) == 0.0
    assert ks_distance([1, 2, 3], [4, 5, 6]) == 1.0
    assert abs(ks_distance([1, 2, 3, 4], [3, 4, 5, 6]) - 0.5) < 1e-12


def test_scan_is_deterministic_and_rotation_keeps_series():
    rnd = random.Random(1)
    lab = segment_labels(200, 30, ["A", "B"], rnd)
    r = [random.Random(2).gauss(0, 1) for _ in range(200)]
    a = scan(r, lab, rotations=19, alpha=0.05, rng=random.Random(3))
    b = scan(r, lab, rotations=19, alpha=0.05, rng=random.Random(3))
    assert a == b and set(a["stats"]) == {"A", "B"}


def test_scan_input_checks():
    with pytest.raises(PathError):
        scan([0.1] * 10, ["A"] * 10, rotations=19, alpha=0.05, rng=random.Random(0))
    with pytest.raises(PathError):
        scan([0.1] * 30, ["A"] * 30, rotations=19, alpha=0.05, rng=random.Random(0))
    with pytest.raises(PathError):
        scan([0.1] * 30, ["A", "B"] * 15, rotations=True, alpha=0.05, rng=random.Random(0))
    with pytest.raises(PathError):
        scan([float("nan")] + [0.1] * 29, ["A", "B"] * 15, rotations=19, alpha=0.05, rng=random.Random(0))


def test_cell_stats_one_per_cell():
    assert set(cell_stats([1.0, 2.0, 3.0, 4.0], ["x", "y", "x", "y"])) == {"x", "y"}
