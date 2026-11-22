"""Compare a pinned lock file (env/test.lock.txt) with `pip freeze` output (review R2-4). Package names are compared
after PEP 503 normalisation (case-insensitive; '-', '_' and '.' are the same), versions exactly. Prints every pinned
line that is not installed exactly; exit code 0 (a report, not a gate).
Usage: python scripts/env_lock_check.py LOCK_FILE FREEZE_FILE"""
import re
import sys
from pathlib import Path


def _norm(name):
    return re.sub(r"[-_.]+", "-", name).lower()


def _pins(text):
    pins = {}
    for line in text.splitlines():
        line = line.split("#", 1)[0].strip()
        m = re.fullmatch(r"([A-Za-z0-9][A-Za-z0-9._-]*)\s*==\s*(\S+)", line)
        if m:
            pins[_norm(m.group(1))] = (m.group(2), line)
    return pins


def missing(lock_text, freeze_text):
    """Pinned lines of the lock file that are not installed with exactly that version."""
    have = {k: v for k, (v, _) in _pins(freeze_text).items()}
    return sorted(line for k, (v, line) in _pins(lock_text).items() if have.get(k) != v)


if __name__ == "__main__":
    lock, freeze = (Path(a).read_text(encoding="utf-8") for a in sys.argv[1:3])
    for line in missing(lock, freeze):
        print(f"  not installed exactly: {line}")
