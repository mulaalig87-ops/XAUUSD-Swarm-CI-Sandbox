"""WP9-02 part 1: the null-card controls reproduce exactly (same counts and outcomes) from the committed
code and worlds, on this machine, and match the committed results file. SYNTHETIC ONLY."""
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _script():
    spec = importlib.util.spec_from_file_location("wp9_02", ROOT / "scripts" / "wp9_02_null_controls.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


@pytest.mark.heavy
def test_null_controls_reproduce_committed_results(tmp_path):
    got = _script().main(tmp_path / "run")
    ref = json.loads((ROOT / "docs" / "results" / "WP9-02_null_controls.json").read_text(encoding="utf-8"))
    key = lambda r: (r["control_id"], r["observed"]["rejections"], r["observed"]["reps"], r["outcome"],   # noqa: E731
                     r["world_sha256"], r["impl_sha256"])
    assert [key(r) for r in got["results"]] == [key(r) for r in ref["results"]]
    assert got["module_sha256"] == ref["module_sha256"]          # helpers unchanged since the recorded run
    out = {r["control_id"]: r["outcome"] for r in got["results"]}
    # FL-007 stays visible: v1 positive failed; v2 (FD-01-D31) passed; all others passed
    assert out["TP21-pair_shuffle_vol_blocks-positive"] == "fail"
    assert all(v == "pass" for k, v in out.items() if k != "TP21-pair_shuffle_vol_blocks-positive")
