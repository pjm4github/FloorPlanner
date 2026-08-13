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


def test_the_real_snapshot_carries_a_marker():
    """The file itself, not a fixture. The tests above would all pass against a
    repository whose snapshot had no marker at all."""
    text = (ROOT / "docs" / "SESSION_SNAPSHOT.md").read_text(encoding="utf-8")
    assert _gate().SNAPSHOT_MARK.search(text), \
        "docs/SESSION_SNAPSHOT.md must carry a SNAPSHOT-HEAD marker"
    assert _gate().SNAPSHOT_ROW.search(text), \
        "docs/SESSION_SNAPSHOT.md must carry a `main` row for the marker to agree with"
