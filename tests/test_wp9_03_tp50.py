"""WP9-03: the TP-50 report reproduces exactly and matches the committed results. SYNTHETIC ONLY."""
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_tp50_reproduces_committed_results(tmp_path):
    spec = importlib.util.spec_from_file_location("wp9_03", ROOT / "scripts" / "wp9_03_tp50.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    got = m.main(tmp_path / "run")
    ref = json.loads((ROOT / "docs" / "results" / "WP9-03_TP50.json").read_text(encoding="utf-8"))
    assert json.loads(json.dumps(got["results"])) == ref["results"]
    assert got["module_sha256"] == ref["module_sha256"]
    rep = got["results"][0]["observed"]["report"]
    assert rep["report_complete"] and rep["known_blind_spots"] == ["t8", "t9"]
    assert {r["type"] for r in rep["rows"]} == {f"t{i}" for i in range(10)}
