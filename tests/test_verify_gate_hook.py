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


def _write_stub_gate(tmp_path, docs_ok=True):
    """A minimal stand-in for `tools/gate.py --docs` (0107-ruling.md SS3: the
    hook now runs it LIVE at push, not from a result file) -- exercises the
    HOOK's own integration (does it call this, does it block on non-zero, is
    it skipped at commit) without dragging in the real docs machinery
    (`docs/defects/`, `docs/SESSION_SNAPSHOT.md`, ...), which is already
    covered by `defects_index`'s own tests and by running the real tool."""
    tools = tmp_path / "tools"
    tools.mkdir(exist_ok=True)
    body = (
        "import sys\n"
        "if '--docs' in sys.argv:\n"
        + ("    print('Docs-Verdict: GREEN')\n    sys.exit(0)\n"
           if docs_ok else
           "    print('Docs-Refs: unresolved=1')\n"
           "    print('Docs-Verdict: RED')\n    sys.exit(1)\n")
        + "sys.exit(0)\n"
    )
    (tools / "gate.py").write_text(body, encoding="utf-8")


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
    _write_stub_gate(tmp_path, docs_ok=True)
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


# ---------------------------------------------------------------------------
# 0084-ruling.md SS4: a NEW docs/handoff/NNNN-*.md commit only lands on
# `main` -- refused on any other branch, unless it is a merge bringing
# `main` in
# ---------------------------------------------------------------------------

def _stage_new_handoff(tmp_path, name="0086-ruling.md", add=True):
    d = tmp_path / "docs" / "handoff"
    d.mkdir(parents=True, exist_ok=True)
    (d / name).write_text("x\n", encoding="utf-8")
    if add:
        _run_git(["add", f"docs/handoff/{name}"], tmp_path)


def test_a_new_handoff_file_on_a_feature_branch_is_REFUSED(tmp_path):
    hook = _hook_repo(tmp_path)
    _write_result(tmp_path, "GREEN", "full")
    _run_git(["checkout", "-b", "some-feature"], tmp_path)
    _stage_new_handoff(tmp_path)
    r = _invoke(hook, tmp_path, "git commit -m x")
    assert r.returncode == 2, r.stderr
    assert "some-feature" in r.stderr
    assert "0086-ruling.md" in r.stderr


def test_a_new_handoff_file_on_main_is_ALLOWED(tmp_path):
    hook = _hook_repo(tmp_path)
    _stage_new_handoff(tmp_path)
    _write_result(tmp_path, "GREEN", "full")
    r = _invoke(hook, tmp_path, "git commit -m x")
    assert r.returncode == 0, r.stderr


def test_a_modified_EXISTING_handoff_file_on_a_feature_branch_is_ALLOWED(tmp_path):
    """Only an ADD is refused -- a correction to a file that already landed
    on `main` is an ordinary edit, not a mailbox violation."""
    hook = _hook_repo(tmp_path)
    _stage_new_handoff(tmp_path)
    _run_git(["commit", "-m", "land it"], tmp_path)
    _run_git(["checkout", "-b", "some-feature"], tmp_path)
    (tmp_path / "docs" / "handoff" / "0086-ruling.md").write_text(
        "x\ny\n", encoding="utf-8")
    _run_git(["add", "docs/handoff/0086-ruling.md"], tmp_path)
    _write_result(tmp_path, "GREEN", "full")
    r = _invoke(hook, tmp_path, "git commit -m x")
    assert r.returncode == 0, r.stderr


def test_the_commit_pathspec_form_is_also_caught(tmp_path):
    """`git commit <paths>` (this project's own documented pattern when
    something else is already staged) stages the named path itself -- never
    pre-staged via `git add`, so only the command-line scan finds it."""
    hook = _hook_repo(tmp_path)
    _write_result(tmp_path, "GREEN", "full")
    _run_git(["checkout", "-b", "some-feature"], tmp_path)
    _stage_new_handoff(tmp_path, add=False)          # untracked, not staged
    r = _invoke(hook, tmp_path, "git commit docs/handoff/0086-ruling.md -m x")
    assert r.returncode == 2, r.stderr
    assert "some-feature" in r.stderr


def test_a_merge_commit_bringing_a_handoff_file_in_is_ALLOWED(tmp_path):
    """`main` merging into a feature branch legitimately carries mailbox
    files that already exist there -- MERGE_HEAD is the exemption."""
    hook = _hook_repo(tmp_path)
    _run_git(["checkout", "-b", "some-feature"], tmp_path)
    (tmp_path / "b.txt").write_text("feature\n", encoding="utf-8")
    _run_git(["add", "-A"], tmp_path)
    _run_git(["commit", "-m", "feature work"], tmp_path)
    _run_git(["checkout", "main"], tmp_path)
    _stage_new_handoff(tmp_path)
    _run_git(["commit", "-m", "land it"], tmp_path)
    _run_git(["checkout", "some-feature"], tmp_path)
    subprocess.run(["git", "merge", "--no-ff", "--no-commit", "main"],
                   cwd=tmp_path, capture_output=True, text=True, check=True)
    _write_result(tmp_path, "GREEN", "full")
    r = _invoke(hook, tmp_path, "git commit -m merge")
    assert r.returncode == 0, r.stderr


def test_a_feature_branch_commit_touching_OTHER_files_is_unaffected(tmp_path):
    hook = _hook_repo(tmp_path)
    _run_git(["checkout", "-b", "some-feature"], tmp_path)
    (tmp_path / "c.txt").write_text("y\n", encoding="utf-8")
    _run_git(["add", "-A"], tmp_path)
    _write_result(tmp_path, "GREEN", "full")
    r = _invoke(hook, tmp_path, "git commit -m x")
    assert r.returncode == 0, r.stderr


# ---------------------------------------------------------------------------
# 0103-ruling.md SS4: a new `NNNN-report.md`/`NNNN-ruling.md` whose
# counterpart (same number, other suffix) is already on disk is a collision
# -- refused, forcing the second writer to pick the next free number instead
# of landing the fourth (0036, 0043, 0050, 0101) repeat of this shape.
# ---------------------------------------------------------------------------

def test_a_report_colliding_with_an_existing_ruling_of_the_same_number_is_REFUSED(tmp_path):
    hook = _hook_repo(tmp_path)
    (tmp_path / "docs" / "handoff").mkdir(parents=True)
    (tmp_path / "docs" / "handoff" / "0101-ruling.md").write_text(
        "x\n", encoding="utf-8")
    _run_git(["add", "-A"], tmp_path)
    _run_git(["commit", "-m", "land the ruling"], tmp_path)
    _stage_new_handoff(tmp_path, name="0101-report.md")
    _write_result(tmp_path, "GREEN", "full")
    r = _invoke(hook, tmp_path, "git commit -m x")
    assert r.returncode == 2, r.stderr
    assert "0101-report.md" in r.stderr
    assert "0101-ruling.md" in r.stderr
    assert "already taken" in r.stderr


def test_a_ruling_colliding_with_an_existing_report_of_the_same_number_is_REFUSED(tmp_path):
    hook = _hook_repo(tmp_path)
    (tmp_path / "docs" / "handoff").mkdir(parents=True)
    (tmp_path / "docs" / "handoff" / "0101-report.md").write_text(
        "x\n", encoding="utf-8")
    _run_git(["add", "-A"], tmp_path)
    _run_git(["commit", "-m", "land the report"], tmp_path)
    _stage_new_handoff(tmp_path, name="0101-ruling.md")
    _write_result(tmp_path, "GREEN", "full")
    r = _invoke(hook, tmp_path, "git commit -m x")
    assert r.returncode == 2, r.stderr
    assert "0101-ruling.md" in r.stderr
    assert "0101-report.md" in r.stderr


def test_a_collision_against_an_ARCHIVED_counterpart_is_also_REFUSED(tmp_path):
    """The numbering is shared across `docs/handoff/` and its `archive/`
    (README.md protocol item 3: 'next free number ... archive included')."""
    hook = _hook_repo(tmp_path)
    (tmp_path / "docs" / "handoff" / "archive").mkdir(parents=True)
    (tmp_path / "docs" / "handoff" / "archive" / "0050-ruling.md").write_text(
        "x\n", encoding="utf-8")
    _run_git(["add", "-A"], tmp_path)
    _run_git(["commit", "-m", "archive it"], tmp_path)
    _stage_new_handoff(tmp_path, name="0050-report.md")
    _write_result(tmp_path, "GREEN", "full")
    r = _invoke(hook, tmp_path, "git commit -m x")
    assert r.returncode == 2, r.stderr
    assert "0050-report.md" in r.stderr


def test_a_fresh_number_with_no_counterpart_is_ALLOWED(tmp_path):
    hook = _hook_repo(tmp_path)
    _stage_new_handoff(tmp_path, name="0104-report.md")
    _write_result(tmp_path, "GREEN", "full")
    r = _invoke(hook, tmp_path, "git commit -m x")
    assert r.returncode == 0, r.stderr


def test_a_non_standard_handoff_NAME_is_not_checked_for_collision(tmp_path):
    """Older, pre-channel-contract names (e.g. `0010-census-furnishings.md`)
    don't fit the report/ruling split -- the collision check only applies to
    the standard pair pattern, not every `docs/handoff/*.md` add."""
    hook = _hook_repo(tmp_path)
    _stage_new_handoff(tmp_path, name="0010-census-furnishings.md")
    _write_result(tmp_path, "GREEN", "full")
    r = _invoke(hook, tmp_path, "git commit -m x")
    assert r.returncode == 0, r.stderr


# ---------------------------------------------------------------------------
# 0107-ruling.md SS3: `tools/gate.py --docs` runs LIVE at push (it writes no
# result file, so there is nothing to read) -- 0105 cut CI's docs job on the
# claim the commit hook already covers it; it did not, and this closes that.
# ---------------------------------------------------------------------------

def test_a_GREEN_docs_lane_is_ALLOWED_at_push(tmp_path):
    hook = _hook_repo(tmp_path)
    _write_stub_gate(tmp_path, docs_ok=True)
    _write_result(tmp_path, "GREEN", "full")
    r = _invoke(hook, tmp_path, "git push")
    assert r.returncode == 0, r.stderr


def test_a_RED_docs_lane_is_REFUSED_at_push(tmp_path):
    hook = _hook_repo(tmp_path)
    _write_stub_gate(tmp_path, docs_ok=False)
    _write_result(tmp_path, "GREEN", "full")
    r = _invoke(hook, tmp_path, "git push")
    assert r.returncode == 2, r.stderr
    assert "--docs" in r.stderr
    assert "Docs-Refs" in r.stderr           # the stub's own detail line


def test_the_docs_lane_is_NOT_CHECKED_at_commit(tmp_path):
    """Only push -- 0107-ruling.md SS3: 'At push, not commit -- the record is
    what lands.' A RED docs lane must not block an ordinary commit."""
    hook = _hook_repo(tmp_path)
    _write_stub_gate(tmp_path, docs_ok=False)
    _write_result(tmp_path, "GREEN", "full")
    r = _invoke(hook, tmp_path, "git commit -m x")
    assert r.returncode == 0, r.stderr


def test_a_RED_docs_lane_and_a_RED_pytest_gate_produce_DIFFERENT_messages(tmp_path):
    """0047-ruling.md SS4's own distinction, extended to the new check: a
    RED docs lane is not the same failure as a RED pytest gate, and the two
    must not read alike."""
    hook = _hook_repo(tmp_path)
    _write_stub_gate(tmp_path, docs_ok=False)
    _write_result(tmp_path, "GREEN", "full")
    docs_red = _invoke(hook, tmp_path, "git push")
    _write_result(tmp_path, "RED", "full")
    pytest_red = _invoke(hook, tmp_path, "git push")
    assert docs_red.stderr != pytest_red.stderr
    assert "--docs" in docs_red.stderr
    assert "--docs" not in pytest_red.stderr
