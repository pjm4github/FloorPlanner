"""`tools/progress_index.py` -- the generated index for per-task progress
entries (0104-ruling.md SS5 tier 1). Same isolation approach as
`test_verify_gate_hook.py`: the tool computes its root from `__file__`, so
the fixture copies it under a throwaway `tmp_path/tools/` and lets it find
`tmp_path/docs/progress/tasks/` on its own -- never this repository's real
directory.
"""
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.tooling

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "tools" / "progress_index.py"


def _isolated(tmp_path):
    tools_dir = tmp_path / "tools"
    tools_dir.mkdir()
    copy = tools_dir / "progress_index.py"
    shutil.copy(SCRIPT, copy)
    return copy


def _write_task(tmp_path, name, title, date, branch, handoff=None,
                 body="Some body text.\n"):
    tasks = tmp_path / "docs" / "progress" / "tasks"
    tasks.mkdir(parents=True, exist_ok=True)
    meta = f"**{date}**, branch `{branch}`."
    if handoff:
        meta += f" handoff: {handoff}"
    (tasks / name).write_text(f"# {title}\n\n{meta}\n\n{body}",
                              encoding="utf-8")


def _run(script, tmp_path, *args):
    return subprocess.run([sys.executable, str(script), *args], cwd=tmp_path,
                          capture_output=True, text=True)


def test_writes_an_empty_index_with_no_task_files(tmp_path):
    script = _isolated(tmp_path)
    r = _run(script, tmp_path)
    assert r.returncode == 0, r.stderr
    index = tmp_path / "docs" / "progress" / "tasks" / "INDEX.md"
    assert index.exists()
    assert "0 task(s)" in index.read_text(encoding="utf-8")


def test_lists_a_well_formed_task_file(tmp_path):
    script = _isolated(tmp_path)
    _write_task(tmp_path, "2026-08-24-thing.md", "A thing done", "2026-08-24",
               "some-branch", handoff="0104")
    r = _run(script, tmp_path)
    assert r.returncode == 0, r.stderr
    text = (tmp_path / "docs" / "progress" / "tasks" / "INDEX.md").read_text(
        encoding="utf-8")
    assert "1 task(s)" in text
    assert "A thing done" in text
    assert "some-branch" in text
    assert "0104" in text


def test_handoff_is_optional(tmp_path):
    script = _isolated(tmp_path)
    _write_task(tmp_path, "2026-08-24-thing.md", "A thing done", "2026-08-24",
               "some-branch")
    r = _run(script, tmp_path)
    assert r.returncode == 0, r.stderr
    text = (tmp_path / "docs" / "progress" / "tasks" / "INDEX.md").read_text(
        encoding="utf-8")
    assert "| — |" in text


def test_check_passes_when_the_index_already_matches(tmp_path):
    script = _isolated(tmp_path)
    _write_task(tmp_path, "2026-08-24-thing.md", "A thing done", "2026-08-24",
               "some-branch")
    _run(script, tmp_path)
    r = _run(script, tmp_path, "--check")
    assert r.returncode == 0, r.stderr
    assert "matches a regeneration" in r.stdout


def test_check_fails_when_the_index_is_stale(tmp_path):
    script = _isolated(tmp_path)
    _write_task(tmp_path, "2026-08-24-thing.md", "A thing done", "2026-08-24",
               "some-branch")
    r = _run(script, tmp_path, "--check")
    assert r.returncode == 1, r.stdout
    assert "DIFFERS" in r.stdout


def test_a_missing_title_line_is_MALFORMED(tmp_path):
    script = _isolated(tmp_path)
    tasks = tmp_path / "docs" / "progress" / "tasks"
    tasks.mkdir(parents=True)
    (tasks / "2026-08-24-bad.md").write_text("not a title line\n",
                                              encoding="utf-8")
    r = _run(script, tmp_path)
    assert r.returncode == 1, r.stdout
    assert "MALFORMED" in r.stdout
    assert "must be `# <title>`" in r.stdout


def test_a_malformed_meta_line_is_caught(tmp_path):
    script = _isolated(tmp_path)
    tasks = tmp_path / "docs" / "progress" / "tasks"
    tasks.mkdir(parents=True)
    (tasks / "2026-08-24-bad.md").write_text(
        "# A thing\n\nnot the right shape\n", encoding="utf-8")
    r = _run(script, tmp_path)
    assert r.returncode == 1, r.stdout
    assert "must match" in r.stdout


def test_a_filename_date_mismatched_with_the_header_date_is_caught(tmp_path):
    script = _isolated(tmp_path)
    _write_task(tmp_path, "2026-08-24-thing.md", "A thing done", "2026-08-25",
               "some-branch")
    r = _run(script, tmp_path)
    assert r.returncode == 1, r.stdout
    assert "!=" in r.stdout


def test_two_task_files_never_collide_the_index_is_generated_not_appended(tmp_path):
    """THE POINT OF THE WHOLE MECHANISM: two independent task files sort
    into one generated index with no shared line either side had to edit."""
    script = _isolated(tmp_path)
    _write_task(tmp_path, "2026-08-24-first.md", "First thing", "2026-08-24",
               "branch-a")
    _write_task(tmp_path, "2026-08-24-second.md", "Second thing", "2026-08-24",
               "branch-b")
    r = _run(script, tmp_path)
    assert r.returncode == 0, r.stderr
    text = (tmp_path / "docs" / "progress" / "tasks" / "INDEX.md").read_text(
        encoding="utf-8")
    assert "2 task(s)" in text
    assert "First thing" in text and "Second thing" in text
