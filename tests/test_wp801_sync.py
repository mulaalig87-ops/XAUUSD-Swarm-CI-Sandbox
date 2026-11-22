"""Unit tests for safe resume in WP8-01 (synthetic temp folders only; Register §34)."""
import importlib.util
import json
import os
from pathlib import Path

import pytest

_spec = importlib.util.spec_from_file_location(
    "wp801_sync", Path(__file__).resolve().parents[1] / "scripts" / "wp801_sync.py")
sync = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sync)


@pytest.fixture
def pkg(tmp_path):
    src = tmp_path / "pkg"
    (src / "docs").mkdir(parents=True)
    (src / "a.txt").write_text("A\n")
    (src / "docs" / "b.md").write_text("B\n")
    return src


def snapshot(root: Path):
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*") if p.is_file()}


def test_fresh_target_is_claimed_and_filled(pkg, tmp_path):
    tgt = tmp_path / "T"
    r = sync.claim(pkg, tgt)
    assert not r["resumed"] and sorted(r["copied"]) == ["a.txt", "docs/b.md"]
    st = json.loads((tgt / sync.STATE).read_text())
    assert st["status"] == "in-progress" and st["manifest_id"] == r["manifest_id"]


def test_foreign_non_empty_target_is_refused_untouched(pkg, tmp_path):
    tgt = tmp_path / "T"; tgt.mkdir(); (tgt / "mine.txt").write_text("keep\n")
    before = snapshot(tgt)
    with pytest.raises(sync.SyncError, match="no WP8-01 state file"):
        sync.claim(pkg, tgt)
    assert snapshot(tgt) == before


def test_resume_copies_only_missing_files(pkg, tmp_path):
    tgt = tmp_path / "T"
    sync.claim(pkg, tgt)
    (tgt / "docs" / "b.md").unlink()                      # simulate a partial earlier run
    (tgt / "env").mkdir(); (tgt / "env" / "python.txt").write_text("generated\n")
    r = sync.claim(pkg, tgt)
    assert r["resumed"] and r["copied"] == ["docs/b.md"]
    assert (tgt / "env" / "python.txt").read_text() == "generated\n"


def test_resume_stops_on_changed_file_and_does_not_replace_it(pkg, tmp_path):
    tgt = tmp_path / "T"
    sync.claim(pkg, tgt)
    (tgt / "a.txt").write_text("CHANGED\n")
    (tgt / "docs" / "b.md").unlink()
    before = snapshot(tgt)
    with pytest.raises(sync.SyncError, match="a.txt"):
        sync.claim(pkg, tgt)
    assert snapshot(tgt) == before                       # nothing replaced, nothing copied


def test_resume_refuses_unknown_files(pkg, tmp_path):
    tgt = tmp_path / "T"
    sync.claim(pkg, tgt)
    (tgt / "stranger.py").write_text("x\n")
    with pytest.raises(sync.SyncError, match="stranger.py"):
        sync.claim(pkg, tgt)
    assert (tgt / "stranger.py").exists()


def test_resume_refuses_different_package_version(pkg, tmp_path):
    tgt = tmp_path / "T"
    sync.claim(pkg, tgt)
    (pkg / "a.txt").write_text("A v2\n")
    with pytest.raises(sync.SyncError, match="DIFFERENT package version"):
        sync.claim(pkg, tgt)


def test_invalid_state_file_is_refused(pkg, tmp_path):
    tgt = tmp_path / "T"; tgt.mkdir()
    (tgt / sync.STATE).write_text("in-progress")          # old-style or forged marker
    with pytest.raises(sync.SyncError, match="not valid"):
        sync.claim(pkg, tgt)


def test_completed_run_is_refused(pkg, tmp_path):
    (pkg / "hooks").mkdir(); (pkg / "hooks" / "pre-commit").write_text("#!/bin/sh\nexit 0\n")
    tgt = tmp_path / "T"
    sync.claim(pkg, tgt)
    sync.stamp(tgt, ".git"); (tgt / ".git" / "hooks").mkdir()
    sync.install_hook(tgt)                             # complete now requires the verified hook
    sync.complete(tgt)
    with pytest.raises(sync.SyncError, match="already completed"):
        sync.claim(pkg, tgt)


def test_stamped_envs_and_git_contents_are_not_scanned_as_unknown_files(pkg, tmp_path):
    tgt = tmp_path / "T"
    sync.claim(pkg, tgt)
    sync.stamp(tgt, "_envs"); sync.stamp(tgt, ".git")
    (tgt / "_envs" / "dev").mkdir(parents=True); (tgt / "_envs" / "dev" / "x").write_text("v\n")
    (tgt / ".git" / "HEAD").write_text("ref\n")
    assert sync.claim(pkg, tgt)["resumed"]


# ---- marker is a consistency/resume marker, not proof of ownership ----

def _forged_marker(pkg, tgt):
    m = sync.manifest(pkg)
    (tgt / sync.STATE).write_text(json.dumps(
        {"status": "in-progress", "run_id": "forged", "manifest_id": sync.manifest_id(m)}))


def test_wellformed_forged_marker_with_foreign_file_is_refused_untouched(pkg, tmp_path):
    tgt = tmp_path / "T"; tgt.mkdir()
    (tgt / "precious.txt").write_text("user data\n")
    _forged_marker(pkg, tgt)
    before = snapshot(tgt)
    with pytest.raises(sync.SyncError, match="precious.txt"):
        sync.claim(pkg, tgt)
    assert snapshot(tgt) == before


def test_wellformed_forged_marker_with_changed_package_file_is_refused_untouched(pkg, tmp_path):
    tgt = tmp_path / "T"; tgt.mkdir()
    (tgt / "a.txt").write_text("someone else's a.txt\n")
    _forged_marker(pkg, tgt)
    before = snapshot(tgt)
    with pytest.raises(sync.SyncError, match="a.txt"):
        sync.claim(pkg, tgt)
    assert snapshot(tgt) == before


def test_wellformed_forged_marker_alone_is_accepted_documented_limit(pkg, tmp_path):
    # Documented limit: a well-formed marker over only package-identical content is accepted.
    # Nothing foreign exists there to protect, and nothing is replaced.
    tgt = tmp_path / "T"; tgt.mkdir()
    _forged_marker(pkg, tgt)
    r = sync.claim(pkg, tgt)
    assert r["resumed"] and r["run_id"] == "forged"


# ---- generated outputs: placed from staging, never overwritten ----

@pytest.fixture
def stage(tmp_path):
    st = tmp_path / "stage"
    (st / "env").mkdir(parents=True)
    (st / "env" / "python.txt").write_text("python 3.13\n")
    (st / "env" / "unit_tests.txt").write_text("14 passed\n")
    return st


def test_place_copies_missing_outputs(pkg, stage, tmp_path):
    tgt = tmp_path / "T"; sync.claim(pkg, tgt)
    assert sorted(sync.place(stage, tgt)) == ["env/python.txt", "env/unit_tests.txt"]


def test_place_skips_identical_outputs(pkg, stage, tmp_path):
    tgt = tmp_path / "T"; sync.claim(pkg, tgt)
    sync.place(stage, tgt)
    assert sync.place(stage, tgt) == []


def test_place_stops_on_different_existing_output_and_replaces_nothing(pkg, stage, tmp_path):
    tgt = tmp_path / "T"; sync.claim(pkg, tgt)
    (tgt / "env").mkdir(); (tgt / "env" / "unit_tests.txt").write_text("1 failed\n")
    before = snapshot(tgt)
    with pytest.raises(sync.SyncError, match="unit_tests.txt"):
        sync.place(stage, tgt)
    assert snapshot(tgt) == before                      # python.txt was not placed either


def test_place_refuses_unlisted_files(pkg, stage, tmp_path):
    tgt = tmp_path / "T"; sync.claim(pkg, tgt)
    (stage / "other.txt").write_text("x\n")
    with pytest.raises(sync.SyncError, match="other.txt"):
        sync.place(stage, tgt)


# ---- atomic placement: an interrupted copy leaves no partial file at the destination ----

class Interrupted(Exception):
    pass


def _interrupting_writer(src, fh):
    fh.write(src.read_bytes()[:1])                     # part of the file is written
    raise Interrupted("simulated power loss mid-copy")


def test_interrupted_copy_in_claim_leaves_no_partial_file_and_resume_works(pkg, tmp_path, monkeypatch):
    tgt = tmp_path / "T"
    real = sync._write_chunks
    monkeypatch.setattr(sync, "_write_chunks", _interrupting_writer)
    with pytest.raises(Interrupted):
        sync.claim(pkg, tgt)
    assert not (tgt / "a.txt").exists() and not (tgt / "docs" / "b.md").exists()
    monkeypatch.setattr(sync, "_write_chunks", real)
    r = sync.claim(pkg, tgt)                           # resume succeeds
    assert r["resumed"] and (tgt / "a.txt").read_text() == "A\n"


def test_interrupted_copy_in_place_leaves_no_partial_file_and_retry_works(pkg, stage, tmp_path, monkeypatch):
    tgt = tmp_path / "T"; sync.claim(pkg, tgt)
    real = sync._write_chunks
    monkeypatch.setattr(sync, "_write_chunks", _interrupting_writer)
    with pytest.raises(Interrupted):
        sync.place(stage, tgt)
    assert not (tgt / "env" / "python.txt").exists() and not (tgt / "env" / "unit_tests.txt").exists()
    monkeypatch.setattr(sync, "_write_chunks", real)
    assert sorted(sync.place(stage, tgt)) == ["env/python.txt", "env/unit_tests.txt"]


def test_atomic_copy_never_replaces_existing_destination(pkg, tmp_path):
    tgt = tmp_path / "T"; sync.claim(pkg, tgt)
    with pytest.raises(sync.SyncError, match="not replaced"):
        sync._atomic_copy(pkg / "a.txt", tgt / "docs" / "b.md", tgt)
    assert (tgt / "docs" / "b.md").read_text() == "B\n"


# ---- .git/ and _envs/ are not trusted blindly ----

def test_foreign_git_with_forged_marker_is_refused_untouched(pkg, tmp_path):
    tgt = tmp_path / "T"; (tgt / ".git").mkdir(parents=True)
    (tgt / ".git" / "HEAD").write_text("ref: refs/heads/main\n")      # someone else's repository
    _forged_marker(pkg, tgt)
    before = snapshot(tgt)
    with pytest.raises(sync.SyncError, match=r"\.git/ exists but is not stamped"):
        sync.claim(pkg, tgt)
    assert snapshot(tgt) == before


def test_foreign_envs_with_forged_marker_is_refused(pkg, tmp_path):
    tgt = tmp_path / "T"; (tgt / "_envs" / "dev").mkdir(parents=True)
    _forged_marker(pkg, tgt)
    with pytest.raises(sync.SyncError, match="_envs/ exists but is not stamped"):
        sync.claim(pkg, tgt)


def test_git_stamped_by_a_different_run_is_refused(pkg, tmp_path):
    tgt = tmp_path / "T"; sync.claim(pkg, tgt)
    (tgt / ".git").mkdir(); (tgt / ".git" / sync.STAMP).write_text("another-run")
    with pytest.raises(sync.SyncError, match="not stamped by this run"):
        sync.claim(pkg, tgt)


def test_own_stamped_dirs_are_accepted_on_resume(pkg, tmp_path):
    tgt = tmp_path / "T"; sync.claim(pkg, tgt)
    sync.stamp(tgt, ".git"); sync.stamp(tgt, "_envs")
    (tgt / "_envs" / "dev").mkdir(); (tgt / ".git" / "HEAD").write_text("ref\n")
    assert sync.claim(pkg, tgt)["resumed"]
    sync.stamp(tgt, ".git")                            # re-stamp on resume is a no-op


def test_stamp_refuses_existing_foreign_dir(pkg, tmp_path):
    tgt = tmp_path / "T"; sync.claim(pkg, tgt)
    (tgt / "_envs").mkdir()
    with pytest.raises(sync.SyncError, match="not stamped by this run"):
        sync.stamp(tgt, "_envs")


# ---- hook installation is verified by content, not by presence ----

@pytest.fixture
def gitready(pkg, tmp_path):
    (pkg / "hooks").mkdir()
    (pkg / "hooks" / "pre-commit").write_text("#!/bin/sh\nexit 0\n")
    tgt = tmp_path / "T"
    sync.claim(pkg, tgt)
    sync.stamp(tgt, ".git")
    (tgt / ".git" / "hooks").mkdir()
    return tgt


def test_hook_missing_is_installed_identical(gitready):
    assert sync.install_hook(gitready) == "installed"
    assert (gitready / ".git/hooks/pre-commit").read_bytes() == (gitready / "hooks/pre-commit").read_bytes()


def test_identical_existing_hook_is_accepted(gitready):
    sync.install_hook(gitready)
    assert sync.install_hook(gitready) == "already installed (identical)"


def test_different_existing_hook_is_refused_and_not_replaced(gitready):
    (gitready / ".git/hooks/pre-commit").write_text("#!/bin/sh\n# weakened\nexit 0\n# x\n")
    with pytest.raises(sync.SyncError, match="differs"):
        sync.install_hook(gitready)
    assert "weakened" in (gitready / ".git/hooks/pre-commit").read_text()


def test_complete_refuses_missing_or_different_hook(gitready):
    with pytest.raises(sync.SyncError, match="missing"):
        sync.complete(gitready)
    (gitready / ".git/hooks/pre-commit").write_text("tampered\n")
    with pytest.raises(sync.SyncError, match="differs"):
        sync.complete(gitready)
    assert json.loads((gitready / sync.STATE).read_text())["status"] == "in-progress"


def test_complete_succeeds_with_identical_hook(gitready):
    sync.install_hook(gitready)
    sync.complete(gitready)
    assert json.loads((gitready / sync.STATE).read_text())["status"] == "complete"


# ---- state marker and stamps: atomic writes, safe after interruption ----

def _interrupting_data_writer(fh, data):
    fh.write(data[:3])                                 # part of the marker/stamp is written
    raise Interrupted("simulated power loss mid-write")


def test_interrupted_first_state_write_leaves_claimable_target(pkg, tmp_path, monkeypatch):
    tgt = tmp_path / "T"
    real = sync._write_data
    monkeypatch.setattr(sync, "_write_data", _interrupting_data_writer)
    with pytest.raises(Interrupted):
        sync.claim(pkg, tgt)
    assert not (tgt / sync.STATE).exists()             # no partial marker at its final name
    assert [e.name for e in tgt.iterdir()] == [sync.TMP]
    monkeypatch.setattr(sync, "_write_data", real)
    r = sync.claim(pkg, tgt)                           # only .wp801_tmp orphans -> treated as empty
    assert not r["resumed"] and (tgt / "a.txt").exists()


def test_only_tmp_dir_with_foreign_file_elsewhere_is_still_refused(pkg, tmp_path):
    tgt = tmp_path / "T"; (tgt / sync.TMP).mkdir(parents=True); (tgt / "mine.txt").write_text("x\n")
    with pytest.raises(sync.SyncError, match="no WP8-01 state file"):
        sync.claim(pkg, tgt)


def test_interrupted_complete_transition_keeps_valid_in_progress_marker(pkg, tmp_path, monkeypatch):
    (pkg / "hooks").mkdir(); (pkg / "hooks" / "pre-commit").write_text("#!/bin/sh\nexit 0\n")
    tgt = tmp_path / "T"; sync.claim(pkg, tgt)
    sync.stamp(tgt, ".git"); (tgt / ".git" / "hooks").mkdir(); sync.install_hook(tgt)
    before = (tgt / sync.STATE).read_bytes()
    monkeypatch.setattr(sync, "_write_data", _interrupting_data_writer)
    with pytest.raises(Interrupted):
        sync.complete(tgt)
    assert (tgt / sync.STATE).read_bytes() == before   # old marker intact and valid
    monkeypatch.undo()
    sync.complete(tgt)
    assert json.loads((tgt / sync.STATE).read_text())["status"] == "complete"


def test_interrupted_stamp_leaves_no_unstamped_folder_and_restamp_works(pkg, tmp_path, monkeypatch):
    tgt = tmp_path / "T"; sync.claim(pkg, tgt)
    monkeypatch.setattr(sync, "_write_data", _interrupting_data_writer)
    with pytest.raises(Interrupted):
        sync.stamp(tgt, ".git")
    assert not (tgt / ".git").exists()                 # final folder never exists unstamped
    monkeypatch.undo()
    sync.stamp(tgt, ".git")
    assert (tgt / ".git" / sync.STAMP).read_text() == json.loads((tgt / sync.STATE).read_text())["run_id"]
    assert sync.claim(pkg, tgt)["resumed"]


def test_interrupted_stamp_does_not_touch_foreign_content(pkg, tmp_path, monkeypatch):
    tgt = tmp_path / "T"; sync.claim(pkg, tgt)
    monkeypatch.setattr(sync, "_write_data", _interrupting_data_writer)
    with pytest.raises(Interrupted):
        sync.stamp(tgt, "_envs")
    monkeypatch.undo()
    (tgt / "_envs").mkdir()                            # someone else creates _envs in between
    with pytest.raises(sync.SyncError, match="not stamped by this run"):
        sync.stamp(tgt, "_envs")
    assert list((tgt / "_envs").iterdir()) == []


def test_hook_mode_is_set_before_final_name(gitready):
    import os, stat
    sync.install_hook(gitready)
    if os.name != "nt":
        assert stat.S_IMODE((gitready / ".git/hooks/pre-commit").stat().st_mode) == 0o755


# ---- environments: built aside, verified, renamed (real venv; empty lock = offline) ----

@pytest.fixture
def envready(pkg, tmp_path):
    (pkg / "env").mkdir()
    (pkg / "env" / "dev.lock.txt").write_text("# empty lock for an offline test\n")
    tgt = tmp_path / "T"; sync.claim(pkg, tgt); sync.stamp(tgt, "_envs")
    return tgt


def test_build_env_real_venv_then_reuse(envready, tmp_path):
    out = tmp_path / "stage" / "dev.installed.txt"
    prefix = sync.build_env(envready, "dev", out)
    assert (envready / "_envs" / "dev").is_dir() and prefix.endswith("dev")
    assert not [p for p in (envready / "_envs").iterdir() if p.name.startswith(".build-")]
    assert sync.build_env(envready, "dev", out) == prefix          # existing verified env reused


def test_interrupted_env_build_leaves_no_final_env_and_retry_works(envready, tmp_path, monkeypatch):
    real = sync._run
    calls = {"n": 0}
    def flaky(cmd):
        r = real(cmd)
        calls["n"] += 1
        if calls["n"] == 1:                            # interrupt right after "python -m venv"
            raise Interrupted("simulated power loss after venv creation")
        return r
    monkeypatch.setattr(sync, "_run", flaky)
    with pytest.raises(Interrupted):
        sync.build_env(envready, "dev", tmp_path / "o.txt")
    assert not (envready / "_envs" / "dev").exists()   # only an orphan .build-* remains
    monkeypatch.setattr(sync, "_run", real)
    sync.build_env(envready, "dev", tmp_path / "o.txt")
    assert (envready / "_envs" / "dev").is_dir()


def test_existing_env_not_matching_lock_is_refused_unmodified(envready, tmp_path, monkeypatch):
    sync.build_env(envready, "dev", tmp_path / "o.txt")
    monkeypatch.setattr(sync, "_freeze", lambda py: ["something==1.0"])
    with pytest.raises(sync.SyncError, match="does not match"):
        sync.build_env(envready, "dev", tmp_path / "o.txt")
    assert (envready / "_envs" / "dev").is_dir()


# ---- folder publish never replaces a destination that appears after the check ----

def _appear_empty_dir(dst):
    dst.mkdir()                                        # a foreign EMPTY folder appears in the window


def test_rename_noreplace_refuses_existing_empty_dir(tmp_path):
    src = tmp_path / "src"; src.mkdir(); (src / "f").write_text("x")
    dst = tmp_path / "dst"; dst.mkdir()
    with pytest.raises(sync.SyncError, match="not replaced"):
        sync._rename_noreplace(src, dst)
    assert dst.is_dir() and list(dst.iterdir()) == [] and (src / "f").exists()


def test_stamp_race_foreign_empty_dir_is_not_replaced(pkg, tmp_path, monkeypatch):
    tgt = tmp_path / "T"; sync.claim(pkg, tgt)
    monkeypatch.setattr(sync, "_before_publish", _appear_empty_dir)
    with pytest.raises(sync.SyncError, match="not replaced"):
        sync.stamp(tgt, ".git")
    assert (tgt / ".git").is_dir() and list((tgt / ".git").iterdir()) == []   # foreign folder intact


def test_build_env_race_foreign_empty_dir_is_not_replaced(envready, tmp_path, monkeypatch):
    monkeypatch.setattr(sync, "_before_publish", _appear_empty_dir)
    with pytest.raises(sync.SyncError, match="not replaced"):
        sync.build_env(envready, "dev", tmp_path / "o.txt")
    final = envready / "_envs" / "dev"
    assert final.is_dir() and list(final.iterdir()) == []                     # foreign folder intact


@pytest.mark.skipif(os.name == "nt", reason="Windows always uses os.rename (fails if dst exists); "
                    "the no-primitive branch exists only on POSIX")
def test_no_unsafe_fallback_when_primitive_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(sync.sys, "platform", "sunos5")                     # no known primitive
    src = tmp_path / "s"; src.mkdir()
    with pytest.raises(sync.SyncError, match="no unsafe fallback"):
        sync._rename_noreplace(src, tmp_path / "d")
    assert src.exists() and not (tmp_path / "d").exists()
