"""Unit tests for the local branch-policy hook. Synthetic git repositories only, no data (Register §34)."""
import os
import shutil
import subprocess
from pathlib import Path

import pytest

HOOK = Path(__file__).resolve().parents[1] / "hooks" / "pre-commit"
ENV = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@localhost",
       "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@localhost"}

pytestmark = pytest.mark.skipif(shutil.which("git") is None,
                                reason="git is required")


def git(repo, *args, check=True):
    return subprocess.run(["git", *args], cwd=repo, env=ENV, capture_output=True, text=True, check=check)


@pytest.fixture
def repo(tmp_path):
    git(tmp_path, "init", "-q", "-b", "main")
    (tmp_path / "f.txt").write_text("base\n")
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "-q", "-m", "initial")          # before hook, as in WP8-01
    hook = tmp_path / ".git" / "hooks" / "pre-commit"
    shutil.copy(HOOK, hook)
    hook.chmod(0o755)
    return tmp_path


def test_direct_commit_on_main_is_rejected(repo):
    (repo / "f.txt").write_text("direct\n")
    git(repo, "add", "-A")
    r = git(repo, "commit", "-q", "-m", "direct", check=False)
    assert r.returncode != 0 and "BLOCKED" in r.stderr


def test_commit_on_work_branch_is_allowed(repo):
    git(repo, "checkout", "-q", "-b", "wp8-01/x")
    (repo / "f.txt").write_text("work\n")
    git(repo, "add", "-A")
    assert git(repo, "commit", "-q", "-m", "work", check=False).returncode == 0


def test_clean_no_ff_merge_into_main_is_allowed(repo):
    git(repo, "checkout", "-q", "-b", "wp8-01/x")
    (repo / "g.txt").write_text("new\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "work")
    git(repo, "checkout", "-q", "main")
    r = git(repo, "merge", "-q", "--no-ff", "wp8-01/x", "-m", "merge", check=False)
    assert r.returncode == 0
    parents = git(repo, "rev-list", "--parents", "-n", "1", "HEAD").stdout.split()
    assert len(parents) == 3                                  # a real merge commit


def test_conflicted_no_ff_merge_completion_is_allowed(repo):
    git(repo, "checkout", "-q", "-b", "wp8-01/x")
    (repo / "f.txt").write_text("branch\n")
    git(repo, "commit", "-q", "-am", "branch change")
    git(repo, "checkout", "-q", "main")
    # create a divergent main commit, simulating a prior reviewed merge, by bypassing the hook
    (repo / "f.txt").write_text("main\n")
    git(repo, "commit", "-q", "--no-verify", "-am", "main change")
    assert git(repo, "merge", "--no-ff", "wp8-01/x", check=False).returncode != 0   # conflict
    (repo / "f.txt").write_text("resolved\n")
    git(repo, "add", "-A")
    assert git(repo, "commit", "-q", "-m", "merge resolved", check=False).returncode == 0
