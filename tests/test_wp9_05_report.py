"""WP9-05: every test named in docs/WP9-05_ENGINEERING_TEST_REPORT.md exists (references only, not semantic
coverage), and every results file named there exists."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = (ROOT / "docs" / "WP9-05_ENGINEERING_TEST_REPORT.md").read_text(encoding="utf-8")


def test_every_named_test_exists():
    names = re.findall(r"(test_[a-z0-9_]+\.py)::(test_[a-z0-9_]+)", DOC)
    assert len(names) > 30
    for f, t in names:
        src = (ROOT / "tests" / f).read_text(encoding="utf-8")
        assert re.search(rf"^def {t}\(", src, re.M), f"{f}::{t} not found"


def test_every_named_results_file_exists():
    for f in set(re.findall(r"(WP9-[0-9A-Za-z_-]+\.json|TP81_TP82\.json)", DOC)):
        if "*" not in f:
            assert (ROOT / "docs" / "results" / f).exists(), f


B9_LAST_FL = 15        # the report covers Stage 9 up to B9 closure (OD-S9-06); later FL entries belong to later work


def test_every_failure_in_fl_is_mentioned():
    fl = (ROOT / "docs" / "FL.md").read_text(encoding="utf-8")
    ids = sorted(set(re.findall(r"FL-0\d\d", fl)))
    assert max(int(i[3:]) for i in ids) >= B9_LAST_FL
    assert f"FL-{B9_LAST_FL:03d}" in DOC
