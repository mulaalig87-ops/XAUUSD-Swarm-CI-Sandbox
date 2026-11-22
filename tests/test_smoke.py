"""Smoke test: synthetic only; no data of any kind (Register §34)."""
import xauusd_swarm


def test_package_imports():
    assert xauusd_swarm.__version__ == "0.0.0"
