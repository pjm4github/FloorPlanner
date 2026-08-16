"""The commit gate's own checks.

Currently one: the SESSION_SNAPSHOT staleness condition (Patrick's ruling,
2026-08-12). The snapshot is the file a fresh session reads first, and it has
gone stale three times -- the last cut sat eight commits behind, pinning a head
that had moved and naming as "next" a census already done and ruled. It carried
a warning about exactly that, in bold, at its own line 9, and the warning did
nothing.

So it is a condition now rather than a convention, and these tests exist because
A CHECK NOBODY CAN DEMONSTRATE FAILING IS THE SAME SPECIES AS THE CONVENTION IT
REPLACES: something that looks like a guarantee and has never been asked to
prove it. Every one of the five outcomes is driven here, and the three RED ones
are the point of the file.
"""
import importlib.util
import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.tooling

ROOT = Path(__file__).resolve().parent.parent


def _gate():
    """Load tools/gate.py by path -- it is a script, not an importable module."""
    spec = importlib.util.spec_from_file_location(
        "_gate_under_test", ROOT / "tools" / "gate.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


HEAD = "9bddf21ffeed0000000000000000000000000000"
PARENT = "be2cb95aaaa00000000000000000000000000000"
TIPS = [HEAD, PARENT]


def _snapshot(marker="9bddf21", row="9bddf21"):
    return (f"<!-- SNAPSHOT-HEAD: {marker} -->\n"
            f"# Session snapshot\n\n"
            f"| | |\n|---|---|\n"
            f"| **`main`** | **`{row}`** - the tip. |\n"
            f"| **Branches** | none. |\n")


def test_a_snapshot_cut_against_the_tip_passes():
    """The positive control. Without it every RED case below could be satisfied
    by a check that simply refuses everything."""
    rc, msg = _gate().snapshot_verdict(_snapshot(), TIPS)
    assert rc == 0, msg
    assert "which is HEAD" in msg


def test_a_snapshot_ONE_COMMIT_BEHIND_passes_and_that_is_deliberate():
    """ONE COMMIT OF SLACK, and it is not leniency.

    The gate runs BEFORE a commit, so the marker it approves names the tip at
    that moment -- and the instant that commit lands, the marker is one behind.
    An exact-match rule would leave the repository RED AT REST: red after every
    correct commit, red for CI on every push, red for the next session before it
    had done anything wrong. **A gate that is red in the resting state trains
    people to ignore it**, which would rebuild the problem it closes.

    This is the resting state, so it must be GREEN."""
    rc, msg = _gate().snapshot_verdict(_snapshot(marker="be2cb95",
                                                 row="be2cb95"), TIPS)
    assert rc == 0, msg
    assert "HEAD~1" in msg, "the message must not claim this is HEAD when it is not"


def test_TWO_commits_behind_is_RED():
    """The drift bound. One behind is the resting state; two is neglect -- and
    the case that produced the ruling was EIGHT."""
    rc, msg = _gate().snapshot_verdict(_snapshot(marker="b4d8ea4",
                                                 row="b4d8ea4"), TIPS)
    assert rc == 1
    assert "cut against b4d8ea4" in msg
    assert "neither HEAD" in msg


def test_a_missing_marker_is_RED():
    """Deleting the marker must not be a way to pass. A check that can be
    turned off by removing its input is advisory again."""
    rc, msg = _gate().snapshot_verdict("# Session snapshot\n\nno marker\n", TIPS)
    assert rc == 1
    assert "no `<!-- SNAPSHOT-HEAD" in msg


def test_a_marker_the_PROSE_CONTRADICTS_is_RED():
    """THE SECOND ASSERTION, and the reason there are two.

    A single marker can be bumped mechanically while the human-readable row
    beside it goes on naming an older commit -- the same convention failing in a
    smaller font, and undetectable by a check that only reads the marker."""
    rc, msg = _gate().snapshot_verdict(_snapshot(marker="9bddf21",
                                                 row="b4d8ea4"), TIPS)
    assert rc == 1
    assert "does not carry that hash" in msg


def test_no_HEAD_is_RED_rather_than_waved_through():
    """A guard that cannot verify must not approve -- the same principle the
    commit hook states for unreadable JSON."""
    rc, msg = _gate().snapshot_verdict(_snapshot(), [])
    assert rc == 1
    assert "cannot read HEAD" in msg


def _run(cmd, cwd):
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    assert r.returncode == 0, f"{cmd} failed: {r.stderr}"
    return r.stdout.strip()


def _merge_ref_repo(tmp_path, make_snapshot_text):
    """A real two-parent merge commit, checked out detached -- exactly the
    shape `refs/pull/N/merge` has (handoff 0027, D78): `root` on `main`,
    `feature` branched from it and carrying `docs/SESSION_SNAPSHOT.md` as
    `make_snapshot_text(root_sha)` produces, then `main` merged with
    `--no-ff feature` (parents [root, feature] in that order, matching
    GitHub's base-then-branch) and checked out by sha, detached.

    Real git, not a fixture of hashes -- `_snapshot_head()` shells out to
    `git rev-parse`, so the thing under test IS the subprocess boundary; a
    fabricated `tips` list would test `snapshot_verdict` again, which the
    tests above already cover exhaustively."""
    _run(["git", "init", "-b", "main"], tmp_path)
    _run(["git", "config", "user.email", "t@example.com"], tmp_path)
    _run(["git", "config", "user.name", "T"], tmp_path)
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "SESSION_SNAPSHOT.md").write_text("root\n", encoding="utf-8")
    _run(["git", "add", "-A"], tmp_path)
    _run(["git", "commit", "-m", "root"], tmp_path)
    root_sha = _run(["git", "rev-parse", "HEAD"], tmp_path)

    _run(["git", "checkout", "-b", "feature"], tmp_path)
    (tmp_path / "docs" / "SESSION_SNAPSHOT.md").write_text(
        make_snapshot_text(root_sha), encoding="utf-8")
    _run(["git", "add", "-A"], tmp_path)
    _run(["git", "commit", "-m", "feature"], tmp_path)
    feature_sha = _run(["git", "rev-parse", "HEAD"], tmp_path)

    _run(["git", "checkout", "main"], tmp_path)
    _run(["git", "merge", "--no-ff", "feature", "-m", "Merge feature into main"],
        tmp_path)
    merge_sha = _run(["git", "rev-parse", "HEAD"], tmp_path)
    _run(["git", "checkout", merge_sha], tmp_path)          # detached, like CI
    return root_sha, feature_sha


def test_a_merge_ref_checkout_with_a_correctly_cut_marker_is_GREEN(
        tmp_path, monkeypatch, capsys):
    """THE POSITIVE-CONTROL DIRECTION, per handoff 0027 SS4 -- a repaired check
    proves nothing until it has produced BOTH of its answers under the shape
    it was repaired for. The marker is cut against `root_sha` (the branch's
    own parent, one commit of slack -- the ordinary resting state), which
    `HEAD^2~1` recovers on the merge ref. `GITHUB_EVENT_NAME=pull_request` is
    what a PR-triggered CI run actually sets -- see the `push` tests below for
    why the substitution must NOT fire without it."""
    root_sha, _feature_sha = _merge_ref_repo(
        tmp_path, lambda root: _snapshot(marker=root[:7], row=root[:7]))
    monkeypatch.setenv("GITHUB_EVENT_NAME", "pull_request")
    monkeypatch.chdir(tmp_path)
    rc = _gate()._snapshot_head()
    out = capsys.readouterr().out
    assert rc == 0, out
    assert "Docs-Snapshot-Shape: merge" in out
    assert "HEAD~1" in out


def test_a_merge_ref_checkout_with_a_STALE_marker_is_RED(
        tmp_path, monkeypatch, capsys):
    """THE NEGATIVE-CONTROL DIRECTION, same section. Without this, `rc == 0`
    above could mean the shape-detection is a no-op that waves everything
    through under a merge ref, which is the exact failure D78 itself is."""
    _merge_ref_repo(
        tmp_path, lambda root: _snapshot(marker="0000000", row="0000000"))
    monkeypatch.setenv("GITHUB_EVENT_NAME", "pull_request")
    monkeypatch.chdir(tmp_path)
    rc = _gate()._snapshot_head()
    out = capsys.readouterr().out
    assert rc == 1, out
    assert "Docs-Snapshot-Shape: merge" in out
    assert "RED" in out


def test_a_real_merge_commit_OUTSIDE_a_pull_request_event_stays_linear(
        tmp_path, monkeypatch, capsys):
    """THE BUG THIS PROJECT'S OWN `main` JUST HIT. This repository's normal
    merge strategy is a real two-parent merge commit (`gh pr merge --merge`),
    so `push`-to-`main` CI -- and any local session on `main` right after a
    merge -- checks out a GENUINE, PERMANENT merge commit that must be read as
    itself. The first cut of the fix keyed off parent count alone and got this
    backwards: it substituted `HEAD^2` there too, silently validating the
    marker against the merged branch's own last commit instead of `main`'s
    real first parent -- caught only because on a ONE-commit feature branch
    the two happen to be the same commit (which is why PR #31's own
    push-triggered run stayed accidentally green). A TWO-commit branch tells
    them apart: `feature`'s own marker is correctly cut against its first
    commit (one slack, from the branch's point of view) -- and that is a
    different commit from `main`'s real pre-merge tip, so reading the merge
    commit as itself must be RED here, not silently GREEN for the wrong
    reason."""
    _run(["git", "init", "-b", "main"], tmp_path)
    _run(["git", "config", "user.email", "t@example.com"], tmp_path)
    _run(["git", "config", "user.name", "T"], tmp_path)
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "SESSION_SNAPSHOT.md").write_text("root\n", encoding="utf-8")
    _run(["git", "add", "-A"], tmp_path)
    _run(["git", "commit", "-m", "root"], tmp_path)

    _run(["git", "checkout", "-b", "feature"], tmp_path)
    (tmp_path / "docs" / "SESSION_SNAPSHOT.md").write_text("feature one\n",
                                                            encoding="utf-8")
    _run(["git", "add", "-A"], tmp_path)
    _run(["git", "commit", "-m", "feature one"], tmp_path)
    feature1_sha = _run(["git", "rev-parse", "HEAD"], tmp_path)

    (tmp_path / "docs" / "SESSION_SNAPSHOT.md").write_text(
        _snapshot(marker=feature1_sha[:7], row=feature1_sha[:7]),
        encoding="utf-8")
    _run(["git", "add", "-A"], tmp_path)
    _run(["git", "commit", "-m", "feature two -- re-cuts against feature one"],
        tmp_path)

    _run(["git", "checkout", "main"], tmp_path)
    _run(["git", "merge", "--no-ff", "feature", "-m", "Merge feature into main"],
        tmp_path)

    monkeypatch.delenv("GITHUB_EVENT_NAME", raising=False)
    monkeypatch.chdir(tmp_path)
    rc = _gate()._snapshot_head()
    out = capsys.readouterr().out
    assert "Docs-Snapshot-Shape: linear" in out, out
    assert rc == 1, out
    assert "neither HEAD" in out


def test_a_shallow_merge_ref_checkout_is_labelled_merge_not_linear(
        tmp_path, monkeypatch, capsys):
    """THE REAL CI FAILURE (handoff 0027/0028), reproduced offline, no network
    needed -- `git clone --depth=1` off a local path reproduces the same
    shallow boundary a remote fetch does. Measured directly on CI: under
    `actions/checkout`'s default `fetch-depth: 1`, `HEAD^1` fails with
    "unknown revision" on a genuine two-parent commit -- not just `HEAD^2` --
    because git hides EVERY parent-relative syntax at a shallow boundary, even
    though `git cat-file -p HEAD` still shows both `parent` lines (real
    content of the object already on disk, unaffected by the boundary).

    So this cannot be GREEN -- `HEAD^2~1` genuinely cannot be resolved without
    more history, and the CI-side fix for that is fetch depth, not this
    function. What THIS function owes is an HONEST label: `merge`, not a
    `linear` mislabel that would send a reader chasing the wrong marker."""
    src = tmp_path / "src"
    src.mkdir()
    _merge_ref_repo(src, lambda root: _snapshot(marker=root[:7], row=root[:7]))

    dst = tmp_path / "dst"
    _run(["git", "clone", "--no-local", "--depth=1", "--branch", "main",
         str(src), str(dst)], tmp_path)

    monkeypatch.setenv("GITHUB_EVENT_NAME", "pull_request")
    monkeypatch.chdir(dst)
    rc = _gate()._snapshot_head()
    out = capsys.readouterr().out
    assert rc == 1, out
    assert "Docs-Snapshot-Shape: merge" in out, (
        "a shallow fetch of a merge commit must not be mistaken for a linear "
        "checkout, even though it cannot fully resolve either")


def test_the_real_snapshot_carries_a_marker():
    """The file itself, not a fixture. The tests above would all pass against a
    repository whose snapshot had no marker at all."""
    text = (ROOT / "docs" / "SESSION_SNAPSHOT.md").read_text(encoding="utf-8")
    assert _gate().SNAPSHOT_MARK.search(text), \
        "docs/SESSION_SNAPSHOT.md must carry a SNAPSHOT-HEAD marker"
    assert _gate().SNAPSHOT_ROW.search(text), \
        "docs/SESSION_SNAPSHOT.md must carry a `main` row for the marker to agree with"
