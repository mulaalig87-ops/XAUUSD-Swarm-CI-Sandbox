"""WP9-04: every test named in docs/WP9-04_TRACEABILITY.md exists, every TP-04 / TP-60.xx / TP-61.xx item has
a row, and the summary counts match the rows."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = (ROOT / "docs" / "WP9-04_TRACEABILITY.md").read_text(encoding="utf-8")


def _rows():
    return [ln for ln in DOC.splitlines() if re.match(r"\| TP-(04|60\.\d\d|61\.\d\d) ", ln)]


def test_every_item_has_a_row():
    ids = {re.match(r"\| (TP-[\d.]+)", r).group(1) for r in _rows()}
    expected = {"TP-04"} | {f"TP-60.{i:02d}" for i in range(1, 20)} | {f"TP-61.{i:02d}" for i in range(1, 17)}
    assert ids == expected


def test_every_named_test_exists():
    names = re.findall(r"(test_[a-z0-9_]+\.py)::(test_[a-z0-9_]+)", DOC)
    assert len(names) > 40
    for f, t in names:
        src = (ROOT / "tests" / f).read_text(encoding="utf-8")
        assert re.search(rf"^def {t}\(", src, re.M), f"{f}::{t} not found"


def test_summary_matches_rows():
    status = [r.rsplit("|", 2)[-2].strip() for r in _rows()]
    cov = sum(s.startswith("covered") for s in status)
    part = sum(s.startswith("**partial**") for s in status)
    nop = sum(s.startswith("**not operational**") for s in status)
    assert cov + part + nop == len(status)
    assert f"Covered {cov}, partial {part} (TP-60.01), not operational {nop}" in DOC
