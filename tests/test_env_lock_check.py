"""Review R2-4: the run evidence compares env/test.lock.txt with `pip freeze` by normalised package name (PEP 503:
case-insensitive, '-', '_' and '.' equal) and exact version."""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _mod():
    spec = importlib.util.spec_from_file_location("env_lock_check", ROOT / "scripts" / "env_lock_check.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_env_lock_check_ignores_name_case_and_separators():
    m = _mod()
    lock = "# pinned\npygments==2.21.0\nnumpy==2.5.3\ntyping_extensions==4.0.0\n"
    freeze = "Pygments==2.21.0\nnumpy==2.5.3\ntyping-extensions==4.0.0\nscipy==1.18.1\n"
    assert m.missing(lock, freeze) == []


def test_env_lock_check_reports_a_missing_package_or_another_version():
    m = _mod()
    lock = "pygments==2.21.0\nnumpy==2.5.3\npytest==9.1.1\n"
    freeze = "Pygments==2.21.0\nnumpy==2.5.2\n"
    assert m.missing(lock, freeze) == ["numpy==2.5.3", "pytest==9.1.1"]


def test_env_lock_check_reads_the_project_lock_file():
    m = _mod()
    lock = (ROOT / "env/test.lock.txt").read_text(encoding="utf-8")
    assert m.missing(lock, lock.upper()) == []                     # every pinned name, whatever its case
