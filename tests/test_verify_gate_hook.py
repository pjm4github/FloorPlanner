"""The commit/push gate hook's own checks -- the quick/full split
(0043-ruling.md SS4, 0047-ruling.md SS4).

0047's own words: "a change to a guard is indistinguishable from removing it
unless both of its answers are demonstrated." The split creates two events
(commit, push) and each has a pass and a fail, so this drives all four:

    | tree / result state          | at COMMIT | at PUSH  |
    |-------------------------------|-----------|----------|
    | no result at all              | REFUSED   | REFUSED  |
    | `--quick` result, GREEN       | allowed   | REFUSED  |
    | full result, GREEN, fresh     | allowed   | allowed  |
    | any result, RED               | REFUSED   | REFUSED  |

plus the freshness check (carried over, unchanged) and the requirement that
"no result" and "a RED result" produce DIFFERENT messages, not merely both
refuse -- `gate.py`'s own distinction between "you did not run it" and "you
ran it and it failed".
"""
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pytest

pytestmark = pytest.mark.tooling

ROOT = Path(__file__).resolve().parent.parent
HOOK = ROOT / ".claude" / "hooks" / "verify_gate.py"


def _run_git(cmd, cwd):
    r = subprocess.run(["git", *cmd], cwd=cwd, capture_output=True, text=True)
    assert r.returncode == 0, f"git {cmd} failed: {r.stderr}"
    return r.stdout.strip()


def _hook_repo(tmp_path):
    """A throwaway repo shaped like this one, just deep enough for the hook's
    own `ROOT` computation (three `dirname`s up from
    `.claude/hooks/verify_gate.py`) to land on `tmp_path` -- so `RESULT` and
    `git ls-files` both operate on an ISOLATED tree, never this repository's
    own `.gate-result.json`. Same reasoning as `test_gate.py`'s
    `_merge_ref_repo`: the thing under test shells out, so the fixture is real
    git, not a mock of it."""
    hook_dir = tmp_path / ".claude" / "hooks"
    hook_dir.mkdir(parents=True)
    copy = hook_dir / "verify_gate.py"
    shutil.copy(HOOK, copy)

    _run_git(["init", "-b", "main"], tmp_path)
    _run_git(["config", "user.email", "t@example.com"], tmp_path)
    _run_git(["config", "user.name", "T"], tmp_path)
    (tmp_path / "a.txt").write_text("x\n", encoding="utf-8")
    _run_git(["add", "-A"], tmp_path)
    _run_git(["commit", "-m", "root"], tmp_path)
    return copy


def _write_result(tmp_path, verdict, mode, older_than=None):
    """Write `.gate-result.json` at repo root, matching what `gate.py`'s
    `_write_result` produces. `older_than`, if given, back-dates the file's
    mtime by that many seconds -- explicit `os.utime`, not a real-time race,
    so ordering against tracked-file mtimes is deterministic regardless of
    filesystem clock resolution."""
    payload = {
        "verdict": verdict,
        "mode": mode,
        "collected": 1,
        "ruff": "clean",
        "vacuous": 0,
        "end_assign": 0,
        "timestamp": time.time(),
        "written_at": "2026-08-17T00:00:00",
        "trailer": [f"Gate-Verdict: {verdict}"],
    }
    p = tmp_path / ".gate-result.json"
    p.write_text(json.dumps(payload), encoding="utf-8")
    if older_than is not None:
        past = time.time() - older_than
        os.utime(p, (past, past))


def _invoke(hook_path, tmp_path, command):
    payload = {"tool_input": {"command": command}}
    return subprocess.run([sys.executable, str(hook_path)], cwd=tmp_path,
                          input=json.dumps(payload), capture_output=True,
                          text=True)


# ---------------------------------------------------------------------------
# row 1: no result at all -- REFUSED at both events
# ---------------------------------------------------------------------------

def test_no_result_is_REFUSED_at_commit(tmp_path):
    hook = _hook_repo(tmp_path)
    r = _invoke(hook, tmp_path, "git commit -m x")
    assert r.returncode == 2, r.stderr
    assert "has not been run" in r.stderr


def test_no_result_is_REFUSED_at_push(tmp_path):
    hook = _hook_repo(tmp_path)
    r = _invoke(hook, tmp_path, "git push")
    assert r.returncode == 2, r.stderr
    assert "has not been run" in r.stderr


# ---------------------------------------------------------------------------
# row 2: `--quick` GREEN -- allowed at commit, REFUSED at push
# ---------------------------------------------------------------------------

def test_quick_GREEN_is_ALLOWED_at_commit(tmp_path):
    hook = _hook_repo(tmp_path)
    _write_result(tmp_path, "GREEN", "quick")
    r = _invoke(hook, tmp_path, "git commit -m x")
    assert r.returncode == 0, r.stderr


def test_quick_GREEN_is_REFUSED_at_push(tmp_path):
    """THE ROW THAT MATTERS MOST (0047 SS4): if a quick result were silently
    accepted at push, the split would be indistinguishable from removing the
    guard entirely."""
    hook = _hook_repo(tmp_path)
    _write_result(tmp_path, "GREEN", "quick")
    r = _invoke(hook, tmp_path, "git push")
    assert r.returncode == 2, r.stderr
    assert "quick" in r.stderr.lower()
    assert "full" in r.stderr.lower()


# ---------------------------------------------------------------------------
# row 3: full GREEN, fresh -- allowed at both
# ---------------------------------------------------------------------------

def test_full_GREEN_is_ALLOWED_at_commit(tmp_path):
    hook = _hook_repo(tmp_path)
    _write_result(tmp_path, "GREEN", "full")
    r = _invoke(hook, tmp_path, "git commit -m x")
    assert r.returncode == 0, r.stderr


def test_full_GREEN_is_ALLOWED_at_push(tmp_path):
    hook = _hook_repo(tmp_path)
    _write_result(tmp_path, "GREEN", "full")
    r = _invoke(hook, tmp_path, "git push")
    assert r.returncode == 0, r.stderr


# ---------------------------------------------------------------------------
# row 4: any RED -- REFUSED at both, in both modes
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("mode", ["quick", "full"])
def test_RED_is_REFUSED_at_commit(tmp_path, mode):
    hook = _hook_repo(tmp_path)
    _write_result(tmp_path, "RED", mode)
    r = _invoke(hook, tmp_path, "git commit -m x")
    assert r.returncode == 2, r.stderr
    assert "RED" in r.stderr


@pytest.mark.parametrize("mode", ["quick", "full"])
def test_RED_is_REFUSED_at_push(tmp_path, mode):
    hook = _hook_repo(tmp_path)
    _write_result(tmp_path, "RED", mode)
    r = _invoke(hook, tmp_path, "git push")
    assert r.returncode == 2, r.stderr
    assert "RED" in r.stderr


# ---------------------------------------------------------------------------
# "you did not run it" vs "you ran it and it failed" -- gate.py's own
# distinction must survive the split, at BOTH events (0047 SS4)
# ---------------------------------------------------------------------------

def test_no_result_and_RED_result_produce_DIFFERENT_messages_at_commit(tmp_path):
    hook = _hook_repo(tmp_path)
    missing = _invoke(hook, tmp_path, "git commit -m x")
    _write_result(tmp_path, "RED", "full")
    red = _invoke(hook, tmp_path, "git commit -m x")
    assert missing.stderr != red.stderr


def test_no_result_and_RED_result_produce_DIFFERENT_messages_at_push(tmp_path):
    hook = _hook_repo(tmp_path)
    missing = _invoke(hook, tmp_path, "git push")
    _write_result(tmp_path, "RED", "full")
    red = _invoke(hook, tmp_path, "git push")
    assert missing.stderr != red.stderr


def test_quick_at_push_and_RED_at_push_produce_DIFFERENT_messages(tmp_path):
    """A third state (0047 SS4 calls it out explicitly): a `--quick` result is
    a real, GREEN result, not a failure -- refusing it at push must not read
    like a RED refusal."""
    hook = _hook_repo(tmp_path)
    _write_result(tmp_path, "GREEN", "quick")
    quick_at_push = _invoke(hook, tmp_path, "git push")
    _write_result(tmp_path, "RED", "full")
    red_at_push = _invoke(hook, tmp_path, "git push")
    assert quick_at_push.stderr != red_at_push.stderr
    assert "RED" not in quick_at_push.stderr


# ---------------------------------------------------------------------------
# freshness (carried over, unchanged) -- still applies to both events
# ---------------------------------------------------------------------------

def test_a_stale_result_is_REFUSED_at_commit(tmp_path):
    hook = _hook_repo(tmp_path)
    _write_result(tmp_path, "GREEN", "full", older_than=10)
    r = _invoke(hook, tmp_path, "git commit -m x")
    assert r.returncode == 2, r.stderr
    assert "STALE" in r.stderr


def test_a_stale_result_is_REFUSED_at_push(tmp_path):
    hook = _hook_repo(tmp_path)
    _write_result(tmp_path, "GREEN", "full", older_than=10)
    r = _invoke(hook, tmp_path, "git push")
    assert r.returncode == 2, r.stderr
    assert "STALE" in r.stderr


# ---------------------------------------------------------------------------
# a command naming both is gated as a push -- the stricter requirement
# ---------------------------------------------------------------------------

def test_a_command_naming_both_commit_and_push_IS_GATED_AS_A_PUSH(tmp_path):
    hook = _hook_repo(tmp_path)
    _write_result(tmp_path, "GREEN", "quick")
    r = _invoke(hook, tmp_path, "git commit -m x && git push")
    assert r.returncode == 2, r.stderr
    assert "full" in r.stderr.lower()


# ---------------------------------------------------------------------------
# the gate-and-commit/push-in-one-call block still fires for push, not only
# commit
# ---------------------------------------------------------------------------

def test_running_the_gate_AND_pushing_in_one_call_is_blocked(tmp_path):
    hook = _hook_repo(tmp_path)
    _write_result(tmp_path, "GREEN", "full")
    r = _invoke(hook, tmp_path, "python tools/gate.py && git push")
    assert r.returncode == 2, r.stderr
    assert "runs the gate AND pushes" in r.stderr
    assert "pushs" not in r.stderr


def test_a_command_UNRELATED_to_commit_or_push_is_untouched(tmp_path):
    hook = _hook_repo(tmp_path)
    r = _invoke(hook, tmp_path, "git status")
    assert r.returncode == 0, r.stderr
