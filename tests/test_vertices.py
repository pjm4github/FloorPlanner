"""P3.1 -- the live vertex table behind `WallItem.p1` / `p2`.

The representation changes here; behaviour deliberately does NOT. `p1`/`p2` are
read-through properties over `Vertex` objects, and assignment is SPLIT-ON-WRITE:
it mints a fresh vertex for that end and leaves any sharer where it was, which
is exactly today's independent-ends semantics. Shared movement is P3.3's
wall-move operation, never a side effect of assignment.

That distinction is the whole point of the task, so it is what these tests pin.
"""
import json
from pathlib import Path

import pytest
from PyQt6.QtCore import QPointF

from floorplanner.vertex import Vertex, split_count

pytestmark = pytest.mark.walls

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


def _wall(fp, x1, y1, x2, y2, t="interior"):
    return fp.WallItem(QPointF(x1, y1), QPointF(x2, y2), t)


# ------------------------------------------------------------ read-through
def test_p1_p2_read_through_to_vertices(fp):
    w = _wall(fp, 0, 0, 100, 0)
    assert (w.p1.x(), w.p1.y()) == (0.0, 0.0)
    assert (w.p2.x(), w.p2.y()) == (100.0, 0.0)
    assert w.v1 == w._v1.uid and w.v2 == w._v2.uid
    assert w.v1 != w.v2


def test_uids_are_persistent_across_edits(fp):
    """Stable across edits, hence macro-addressable -- what P4.5 needs when it
    serializes groups by member id."""
    w = _wall(fp, 0, 0, 100, 0)
    before = w.v1
    w.wall_type = "exterior"
    w.rebuild()
    w.p1 = QPointF(0, 0)                    # a NO-OP assignment
    assert w.v1 == before, "an unrelated edit renamed the vertex"


def test_uid_is_minted_once_not_per_read(fp):
    w = _wall(fp, 0, 0, 100, 0)
    assert w.v1 == w.v1 == w._v1.uid


# --------------------------------------------------- split-on-write semantics
def test_assignment_splits_and_leaves_the_sharer_alone(fp):
    """THE ruling. Two walls sharing a corner: moving one end must not drag the
    other -- that is today's behaviour, and preserving it is what makes 'suite
    green with no test changes' achievable at all."""
    a = _wall(fp, 0, 0, 100, 0)
    b = _wall(fp, 100, 0, 100, 80)
    b._v1 = a._v2                            # EXPLICIT sharing: one corner
    assert b.p1.x() == a.p2.x() and b.p1.y() == a.p2.y()
    assert b.v1 == a.v2

    a.p2 = QPointF(140, 0)                   # move a's end
    assert (a.p2.x(), a.p2.y()) == (140.0, 0.0)
    assert (b.p1.x(), b.p1.y()) == (100.0, 0.0), \
        "assignment dragged the sharer -- that is P3.3's move, not P3.1's"
    assert a.v2 != b.v1, "the split did not break the sharing"


def test_no_op_assignment_keeps_identity_and_sharing(fp):
    """Re-setting the same coordinates must not churn uids or break sharing --
    the codebase does this constantly (every rebuild, every settle)."""
    a = _wall(fp, 0, 0, 100, 0)
    b = _wall(fp, 100, 0, 100, 80)
    b._v1 = a._v2
    uid = a.v2
    n = split_count()
    a.p2 = QPointF(100, 0)
    a.p2 = a.p2
    assert a.v2 == uid and b.v1 == uid, "a no-op assignment split the vertex"
    assert split_count() == n, "a no-op assignment was counted as a split"


def test_a_real_move_is_counted(fp):
    w = _wall(fp, 0, 0, 100, 0)
    n = split_count()
    w.p1 = QPointF(1, 0)
    w.p2 = QPointF(101, 0)
    assert split_count() == n + 2


def test_moving_a_wall_still_moves_both_ends(fp, scene):
    """The ordinary case still behaves: nothing about the representation change
    is visible to a caller that just sets both ends."""
    w = _wall(fp, 0, 0, 100, 0)
    scene.addItem(w)
    w.p1 = QPointF(10, 10)
    w.p2 = QPointF(110, 10)
    w.rebuild()
    assert (w.p1.x(), w.p1.y(), w.p2.x(), w.p2.y()) == (10.0, 10.0, 110.0, 10.0)
    assert w.length() == pytest.approx(100.0)


# ------------------------------------------------------------- the Vertex type
def test_vertex_is_never_mutated_in_place(fp):
    """`point()` returns the shared QPointF rather than a copy, which is only
    safe because a MOVE mints a new vertex. A caller holding an old p1 keeps
    seeing the old position -- identical to the pre-P3.1 behaviour, where
    assignment rebound the attribute to a fresh QPointF."""
    w = _wall(fp, 0, 0, 100, 0)
    held = w.p1
    w.p1 = QPointF(50, 50)
    assert (held.x(), held.y()) == (0.0, 0.0), "a captured p1 moved under the caller"


def test_vertex_moved_to_returns_self_when_unchanged():
    v = Vertex(3.0, 4.0)
    assert v.moved_to(QPointF(3.0, 4.0)) is v
    assert v.moved_to((3.0, 4.0)) is v
    assert v.moved_to(QPointF(3.0, 4.5)) is not v


# ---------------------------------------------- --verify-design records splits
def test_verify_logs_splits_per_operation(fp, win, monkeypatch):
    """P3.3 needs to know WHICH call sites move coordinates when they mean to
    move corners; the per-operation split count is that data."""
    from floorplanner.design import verify as V
    monkeypatch.setenv(V.ENV_VAR, "1")
    V.rebase(win)
    V.verify(win, "baseline")                       # establishes the mark

    w = _wall(fp, 0, 0, 100, 0)
    win.scene.addItem(w)
    w.p1 = QPointF(5, 5)
    w.p2 = QPointF(105, 5)
    V.verify(win, "moved a wall")

    log = getattr(win, V.SPLIT_LOG_ATTR)
    assert ("moved a wall", 2) in log
    V.rebase(win)


# ------------------------------------------------------ the COMPOSITION gate
# The Gate 2 lesson, applied to this task: both apply paths were individually
# covered and their composition was not. So exercise BOTH here, not just the
# one the new code happens to use.
def test_round_trip_through_the_faithful_apply(fp, win):
    """load_data -- the undo/restore path, which never welds or migrates."""
    from floorplanner.design.bridge import design_from_scene
    win.load_data(json.loads((EXAMPLES / "sample_plan.json").read_text("utf-8")))
    d1 = design_from_scene(win).to_dict()
    win.load_data(json.loads(json.dumps(d1)))
    assert design_from_scene(win).to_dict() == d1


def test_round_trip_through_the_converting_apply(fp, win, tmp_path):
    """open_document -- the migrating path, which welds. Composed all the way
    out to a legacy export and back, exactly as the Gate 2 regression does."""
    from floorplanner.design.validate import check
    win.load_path(str(EXAMPLES / "planc1.json"))
    areas = {r.name: r.area_sqft for r in win.scene.items()
             if isinstance(r, fp.RoomItem)}
    p = tmp_path / "rt.json"
    win.save_path(str(p))
    win.load_path(str(p))
    assert not win._is_dirty()
    assert check(json.loads(p.read_text(encoding="utf-8")), deep=True) == []

    v4 = tmp_path / "rt.v4.json"
    win.export_legacy_v4_path(str(v4))
    win.load_path(str(v4))
    assert win._conversion["ends_moved"] == 0, "our own export needed repair"
    after = {r.name: r.area_sqft for r in win.scene.items()
             if isinstance(r, fp.RoomItem)}
    for name, sf in areas.items():
        assert after[name] == pytest.approx(sf, abs=0.1), f"{name} moved"
