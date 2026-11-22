"""WP8-01 safe target sync (called by wp801_setup.ps1). Standard library only.

Rules:
- A new or empty target is claimed: a state file (.wp801_state) is written with a run id and
  the package manifest id (SHA-256 over all package file paths and hashes).
- The state file is a CONSISTENCY / RESUME MARKER, NOT PROOF OF OWNERSHIP: run_id and
  manifest_id are not secrets, so anyone can write a well-formed marker. What protects
  existing content is not the marker but the rules below, which hold even with a forged marker:
  a target with any file that is neither a package file nor a listed generated file is
  refused; no file is ever replaced or deleted.
- A non-empty target is resumed only if the marker is well-formed, says "in-progress", and
  matches this package's manifest id, and the target holds no unknown files.
- Missing package files are copied. Identical files are left alone. A file that exists and
  differs STOPS the run and is listed; it is never replaced. Conflicts are checked before any copy.
- Generated outputs are written by wp801_setup.ps1 to a staging folder OUTSIDE the target and
  placed into the target with "place", under the same rule: copy if missing, skip if identical,
  stop if different. So nothing in the target is ever overwritten.
- Atomic placement: every file is first written completely to <target>/.wp801_tmp/<random>,
  flushed, then given its final name with os.link (fails if the name exists: never replaces;
  on Windows/NTFS falls back to os.rename, which also never replaces). An interrupted copy
  leaves at most an orphan in .wp801_tmp/ (ignored, git-ignored), never a partial file at the
  destination. Orphans are not deleted automatically.
- .git/ and _envs/ are not scanned file by file, but they are not trusted blindly: this script
  creates each one itself and stamps it (<dir>/.wp801_run_id) BEFORE any content goes in. On
  resume, an existing .git/ or _envs/ must carry the stamp with this run's id, or the run is
  refused. Limit, stated: like the state marker, a stamp can be forged by someone who writes
  it on purpose; it prevents accidental reuse of a foreign repository or environment, not a
  deliberate forgery.
Usage:
  python wp801_sync.py claim <source> <target>
  python wp801_sync.py stamp <target> <.git|_envs>
  python wp801_sync.py install_hook <target>
  python wp801_sync.py venv <target> <dev|test> <freeze_out_outside_target>
- State marker and stamps are written atomically too: the marker is created with a no-replace
  link and changed only by an atomic swap of this script's own marker; a stamped folder is
  built inside .wp801_tmp and renamed into place, so it never exists unstamped.
- Every folder publish (.git/, _envs/, _envs/<name>) uses a NO-REPLACE rename (_rename_noreplace):
  a destination that appears after the existence check is never replaced; on a system without
  such a primitive the run is refused. A target that
  holds only .wp801_tmp/ (orphans of an interrupted first claim) counts as empty.
- Environments are built in _envs/.build-<uuid>, verified, then renamed (build_env).
- Stated limit: git's own operations (init, commit) are not made atomic here; an interrupted
  commit can leave .git/index.lock, which git reports; removing it is a manual decision.
- install_hook: copies hooks/pre-commit to .git/hooks/pre-commit if absent (atomic); if present,
  its SHA-256 must equal the package hook, otherwise refused without replacing it.
  "complete" re-checks the same, so a run can never be marked complete with a missing or
  different hook.
  python wp801_sync.py place <staging> <target>
  python wp801_sync.py complete <target>
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

STATE = ".wp801_state"
SKIP_DIRS = {"_envs", ".git", "__pycache__", ".pytest_cache", ".wp801_tmp"}
STAMPED = (".git", "_envs")
STAMP = ".wp801_run_id"
TMP = ".wp801_tmp"
GENERATED = {STATE, "env/dev.installed.txt", "env/test.installed.txt", "env/python.txt",
             "env/separation.txt", "env/unit_tests.txt", "docs/PROVENANCE.md"}


class SyncError(Exception):
    pass


def _files(root: Path):
    out = []
    for p in root.rglob("*"):
        rel = p.relative_to(root)
        if any(part in SKIP_DIRS for part in rel.parts) or not p.is_file():
            continue
        out.append(rel.as_posix())
    return sorted(out)


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _write_chunks(src: Path, fh):
    """Copy src into an open file in chunks (separate function so tests can interrupt it)."""
    with open(src, "rb") as f:
        while True:
            b = f.read(65536)
            if not b:
                break
            fh.write(b)


def _rename_noreplace(src: Path, dst: Path):
    """Publish src under dst in one step, NEVER replacing an existing dst (file or directory),
    even if dst appears after any earlier check.
    - Windows: os.rename fails if dst exists (MoveFileEx without REPLACE_EXISTING).
    - Linux: renameat2(..., RENAME_NOREPLACE).
    - macOS: renamex_np(..., RENAME_EXCL).
    - Anything else, or a filesystem that rejects the flag: refuse (no unsafe fallback)."""
    if os.name == "nt":
        try:
            os.rename(src, dst)
        except FileExistsError:
            raise SyncError(f"destination exists, not replaced: {dst}")
        return
    import ctypes
    import errno
    libc = ctypes.CDLL(None, use_errno=True)
    s_, d_ = os.fsencode(str(src)), os.fsencode(str(dst))
    if sys.platform.startswith("linux") and hasattr(libc, "renameat2"):
        AT_FDCWD, RENAME_NOREPLACE = -100, 1
        rc = libc.renameat2(AT_FDCWD, s_, AT_FDCWD, d_, RENAME_NOREPLACE)
    elif sys.platform == "darwin" and hasattr(libc, "renamex_np"):
        RENAME_EXCL = 0x00000004
        rc = libc.renamex_np(s_, d_, RENAME_EXCL)
    else:
        raise SyncError("no atomic no-replace rename on this system; refusing (no unsafe fallback)")
    if rc != 0:
        e = ctypes.get_errno()
        if e == errno.EEXIST:
            raise SyncError(f"destination exists, not replaced: {dst}")
        raise SyncError(f"atomic no-replace rename unavailable or failed ({errno.errorcode.get(e, e)}); refusing")


def _before_publish(dst: Path):
    """No-op hook between the existence check and the publish step (tests use it to simulate
    a foreign folder appearing in that window)."""


def _tmp(target: Path) -> Path:
    d = target / TMP
    d.mkdir(parents=True, exist_ok=True)
    return d / uuid.uuid4().hex


def _write_data(fh, data: bytes):
    """Separate function so tests can interrupt a small-file write."""
    fh.write(data)


def _link_no_replace(tmp: Path, dst: Path):
    try:
        os.link(tmp, dst)                      # atomic, never replaces an existing name
    except FileExistsError:
        raise SyncError(f"destination exists, not replaced: {dst}")
    except OSError:
        if os.name != "nt":
            raise SyncError("hard link unavailable on this filesystem; refusing (no unsafe fallback)")
        try:
            os.rename(tmp, dst)                # Windows: atomic and never replaces
        except FileExistsError:
            raise SyncError(f"destination exists, not replaced: {dst}")
        return
    os.unlink(tmp)                             # only the temporary second name


def _atomic_write(data: bytes, dst: Path, target: Path, replace: bool = False):
    """Write small file atomically. replace=False: never replaces (create only).
    replace=True: atomic swap (os.replace) used ONLY for this script's own state transitions."""
    tmp = _tmp(target)
    with open(tmp, "xb") as fh:
        _write_data(fh, data)
        fh.flush()
        os.fsync(fh.fileno())
    if replace:
        os.replace(tmp, dst)
    else:
        _link_no_replace(tmp, dst)


def _atomic_copy(src: Path, dst: Path, target: Path, mode=None):
    tmp = _tmp(target)
    with open(tmp, "xb") as fh:
        _write_chunks(src, fh)
        fh.flush()
        os.fsync(fh.fileno())
    shutil.copystat(src, tmp)
    if mode is not None:
        os.chmod(tmp, mode)                    # set BEFORE the final name exists
    dst.parent.mkdir(parents=True, exist_ok=True)
    _link_no_replace(tmp, dst)


def _check_stamps(target: Path, run_id: str):
    for d in STAMPED:
        if (target / d).exists():
            sp = target / d / STAMP
            if not sp.is_file() or sp.read_text(encoding="utf-8").strip() != run_id:
                raise SyncError(f"{d}/ exists but is not stamped by this run: refusing to reuse it")


def stamp(target: Path, name: str):
    if name not in STAMPED:
        raise SyncError("stamp only applies to .git or _envs")
    st = json.loads((target / STATE).read_text(encoding="utf-8"))
    if st.get("status") != "in-progress":
        raise SyncError("cannot stamp: run is not in progress")
    d = target / name
    if d.exists():
        _check_stamps(target, st["run_id"])      # already ours, or refuse
        return
    # Build the folder with its stamp inside .wp801_tmp, then give it its final name in one step.
    # An interruption leaves only an orphan in .wp801_tmp; the final folder never exists unstamped.
    build = _tmp(target)
    build.mkdir()
    with open(build / STAMP, "xb") as fh:
        _write_data(fh, st["run_id"].encode())
        fh.flush()
        os.fsync(fh.fileno())
    if d.exists():
        raise SyncError(f"{name}/ appeared during stamping; not replaced")
    _before_publish(d)
    _rename_noreplace(build, d)


def manifest(source: Path) -> dict:
    return {rel: _sha(source / rel) for rel in _files(source) if rel != STATE}


def manifest_id(m: dict) -> str:
    return hashlib.sha256("\n".join(f"{k} {v}" for k, v in sorted(m.items())).encode()).hexdigest()


def _write_state(target: Path, status: str, run_id: str, mid: str, transition: bool = False):
    data = json.dumps({"status": status, "run_id": run_id, "manifest_id": mid}).encode()
    # Creation never replaces an existing marker; a transition is an atomic swap of our own marker.
    _atomic_write(data, target / STATE, target, replace=transition)


def claim(source: Path, target: Path) -> dict:
    m = manifest(source)
    mid = manifest_id(m)
    if not target.exists() or all(e.name == TMP for e in target.iterdir()):
        # empty, or holding only this script's own .wp801_tmp orphans from an interrupted first claim
        target.mkdir(parents=True, exist_ok=True)
        run_id = uuid.uuid4().hex
        _write_state(target, "in-progress", run_id, mid)
        resumed = False
    else:
        sp = target / STATE
        if not sp.is_file():
            raise SyncError(f"{target} is not empty and has no WP8-01 state file: not created by this script")
        try:
            st = json.loads(sp.read_text(encoding="utf-8"))
        except ValueError:
            raise SyncError("state file is not valid; refusing")
        if st.get("status") == "complete":
            raise SyncError("WP8-01 already completed in this target")
        if st.get("status") != "in-progress" or not st.get("run_id"):
            raise SyncError("state file is not an in-progress WP8-01 run; refusing")
        if st.get("manifest_id") != mid:
            raise SyncError("target was started by a DIFFERENT package version (manifest id mismatch); refusing")
        unknown = [f for f in _files(target) if f not in m and f not in GENERATED]
        if unknown:
            raise SyncError("target contains files not from this package or this script: " + ", ".join(unknown))
        run_id = st["run_id"]
        _check_stamps(target, run_id)
        resumed = True
    conflicts = [rel for rel, h in m.items() if (target / rel).is_file() and _sha(target / rel) != h]
    if conflicts:
        raise SyncError("existing files differ from the package (not replaced): " + ", ".join(conflicts))
    copied = []
    for rel in m:
        dst = target / rel
        if not dst.exists():
            _atomic_copy(source / rel, dst, target)
            copied.append(rel)
    return {"run_id": run_id, "manifest_id": mid, "resumed": resumed, "copied": copied}


def place(staging: Path, target: Path) -> list:
    """Copy generated outputs from staging into target: missing -> copy; identical -> skip;
    different -> SyncError listing every such file, and nothing is copied."""
    files = _files(staging)
    bad = [f for f in files if f not in GENERATED or f == STATE]
    if bad:
        raise SyncError("staging holds files that are not listed generated outputs: " + ", ".join(bad))
    diff = [f for f in files if (target / f).is_file() and _sha(target / f) != _sha(staging / f)]
    if diff:
        raise SyncError("generated output already exists in target and differs (not replaced): " + ", ".join(diff))
    placed = []
    for f in files:
        if not (target / f).exists():
            _atomic_copy(staging / f, target / f, target)
            placed.append(f)
    return placed


HOOK_SRC = "hooks/pre-commit"
HOOK_DST = ".git/hooks/pre-commit"


def _check_hook(target: Path):
    src, dst = target / HOOK_SRC, target / HOOK_DST
    if not dst.is_file():
        raise SyncError(f"{HOOK_DST} is missing")
    hs, hd = _sha(src), _sha(dst)
    if hs != hd:
        raise SyncError(f"{HOOK_DST} differs from {HOOK_SRC} (installed {hd[:12]}, package {hs[:12]}); not replaced")


def install_hook(target: Path) -> str:
    dst = target / HOOK_DST
    if not (target / ".git" / "hooks").is_dir():
        raise SyncError(".git/hooks is missing: run git init first")
    if dst.exists():
        _check_hook(target)
        return "already installed (identical)"
    _atomic_copy(target / HOOK_SRC, dst, target, mode=0o755)
    _check_hook(target)
    return "installed"


def _lock_set(lock: Path):
    return sorted(l.strip().lower() for l in lock.read_text(encoding="utf-8").splitlines()
                  if l.strip() and not l.strip().startswith("#"))


def _env_python(d: Path) -> Path:
    return d / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def _run(cmd):
    """Separate function so tests can interrupt or stub external commands."""
    return subprocess.run(cmd, capture_output=True, text=True)


def _freeze(py: Path):
    r = _run([str(py), "-m", "pip", "freeze", "--exclude", "pip"])
    if r.returncode != 0:
        raise SyncError(f"pip freeze failed: {r.stderr.strip()}")
    return sorted(l.strip().lower() for l in r.stdout.splitlines() if l.strip())


def build_env(target: Path, name: str, freeze_out: Path) -> str:
    """Create _envs/<name> from env/<name>.lock.txt. The env is built in _envs/.build-<uuid>,
    installed with --no-deps, verified (frozen set == lock), and only then renamed to its final
    name. An interruption leaves an orphan build folder, never a half-built final env.
    An existing final env is verified, never modified; a mismatch is refused."""
    st = json.loads((target / STATE).read_text(encoding="utf-8"))
    if st.get("status") != "in-progress":
        raise SyncError("cannot build env: run is not in progress")
    _check_stamps(target, st["run_id"])
    if not (target / "_envs").is_dir():
        raise SyncError("_envs/ is missing: run stamp first")
    lock = target / "env" / f"{name}.lock.txt"
    want = _lock_set(lock)
    final = target / "_envs" / name
    if final.exists():
        got = _freeze(_env_python(final))
        if got != want:
            raise SyncError(f"existing _envs/{name} does not match env/{name}.lock.txt; not modified")
    else:
        build = target / "_envs" / f".build-{uuid.uuid4().hex}"
        r = _run([sys.executable, "-m", "venv", str(build)])
        if r.returncode != 0:
            raise SyncError(f"venv creation failed: {r.stderr.strip()}")
        if want:
            r = _run([str(_env_python(build)), "-m", "pip", "install", "--disable-pip-version-check",
                      "-q", "--no-deps", "-r", str(lock)])
            if r.returncode != 0:
                raise SyncError(f"install from env/{name}.lock.txt failed: {r.stderr.strip()}")
        got = _freeze(_env_python(build))
        if got != want:
            raise SyncError(f"built env differs from env/{name}.lock.txt: {got}")
        if final.exists():
            raise SyncError(f"_envs/{name} appeared during build; not replaced")
        _before_publish(final)
        _rename_noreplace(build, final)
    freeze_out.parent.mkdir(parents=True, exist_ok=True)
    freeze_out.write_text("\n".join(got) + ("\n" if got else ""), encoding="utf-8")   # outside target
    r = _run([str(_env_python(final)), "-c", "import sys; print(sys.prefix)"])
    return r.stdout.strip()


def complete(target: Path):
    st = json.loads((target / STATE).read_text(encoding="utf-8"))
    if st.get("status") != "in-progress":
        raise SyncError("cannot complete: run is not in progress")
    _check_hook(target)
    _write_state(target, "complete", st["run_id"], st["manifest_id"], transition=True)


def main(argv):
    try:
        if argv[1] == "claim":
            r = claim(Path(argv[2]), Path(argv[3]))
            print(f"run_id {r['run_id']}\nmanifest_id {r['manifest_id']}\nresumed {r['resumed']}\ncopied {len(r['copied'])}")
        elif argv[1] == "place":
            r = place(Path(argv[2]), Path(argv[3]))
            print(f"placed {len(r)}")
        elif argv[1] == "stamp":
            stamp(Path(argv[2]), argv[3])
            print(f"stamped {argv[3]}")
        elif argv[1] == "venv":
            print(build_env(Path(argv[2]), argv[3], Path(argv[4])))
        elif argv[1] == "install_hook":
            print(install_hook(Path(argv[2])))
        elif argv[1] == "complete":
            complete(Path(argv[2]))
            print("complete")
        else:
            raise SyncError("unknown command")
    except SyncError as e:
        print(f"REFUSED: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
