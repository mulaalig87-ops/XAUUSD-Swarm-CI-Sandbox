"""Test-suite configuration.

Founder decision OD-S9-04 (2026-11-17): the HEAVY reproduction tests (they re-run whole synthetic
experiments) run on Linux only, to cut paid CI minutes; every other test runs on Ubuntu and Windows.
Cross-platform equality of these experiments was already shown on Windows CI before this decision
(runs 44077139899, 44080175539, 44081755790, 44084027353, 44090924304, 44096364904, 44101283797).
"""
import sys

import pytest


def pytest_configure(config):
    config.addinivalue_line("markers", "heavy: re-runs a whole synthetic experiment; Linux only (OD-S9-04)")


def pytest_collection_modifyitems(config, items):
    if sys.platform != "win32":
        return
    skip = pytest.mark.skip(reason="heavy experiment re-run: Linux only (founder decision OD-S9-04)")
    for item in items:
        if "heavy" in item.keywords:
            item.add_marker(skip)
