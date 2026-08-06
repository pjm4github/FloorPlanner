"""The vertex operations -- REWRITTEN AT P4.5 as the spec for what replaced the
P3.1 shim, rather than deleted with it.

This file used to pin `p1`/`p2` assignment as SPLIT-ON-WRITE: a coordinate
written to a wall end minted a fresh `Vertex` and left any sharer behind. That
was P3.1's compatibility shim, and it did its job -- it let the store change
underneath a green suite. Its last production caller went at P4.5(33), and the
setters go with it.

WHAT SURVIVES IS THE DISTINCTION, not the spelling, and it is now made by two
NAMED operations instead of by one ambiguous assignment:

    v.relocated_to(p)   THE CORNER MOVED -- identity carried, so every wall end
                        and outline edge holding it comes along.
    Vertex.at(p)        A NEW CORNER -- what a deliberate DETACH takes, leaving
                        every sharer exactly where it was.

`wall.p1 = ...` was one spelling for both, and a reader could not tell which was
meant. These tests pin the two against each other on the same scene and the same
movement, plus the read-through they rest on and the round-trip composition the
original file guarded.
"""
import json
from pathlib import Path

import pytest
from PyQt6.QtCore import QPointF

from floorplanner.vertex import Vertex

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
    assert w.v1 == before, "an unrelated edit renamed the vertex"


def test_uid_is_minted_once_not_per_read(fp):
    w = _wall(fp, 0, 0, 100, 0)
    assert w.v1 == w.v1 == w._v1.uid


# ------------------------------------------- the two operations, side by side
# `wall.p1 = ...` was ONE spelling for BOTH of these, which is why it is gone.
# The next two tests are deliberately the same scene and the same movement, so
# the only difference between them is which operation was asked for.
def _shared_pair(fp):
    """Two walls holding ONE corner at (100, 0), by identity."""
    a = _wall(fp, 0, 0, 100, 0)
    b = _wall(fp, 100, 0, 100, 80)
    b.set_end_vertex("p1", a.end_vertex("p2"))
    assert b.end_vertex("p1") is a.end_vertex("p2"), "precondition: one corner"
    return a, b


def test_a_detach_moves_one_end_and_leaves_the_sharer(fp):
    """`Vertex.at` -- a NEW corner. This wall's end moved; anything sharing the
    old corner did not. That is the endpoint drag's semantics and the designed
    open-side behaviour, and it is what the retired assignment used to do."""
    a, b = _shared_pair(fp)
    a.set_end_vertex("p2", Vertex.at(QPointF(140, 0)))

    assert (a.p2.x(), a.p2.y()) == (140.0, 0.0)
    assert (b.p1.x(), b.p1.y()) == (100.0, 0.0), \
        "the detach dragged the sharer -- that is a relocation, not a detach"
    assert a.end_vertex("p2") is not b.end_vertex("p1"), \
        "the detach did not break the sharing"


def test_a_relocation_moves_the_corner_and_everything_on_it(fp):
    """`relocated_to` -- the SAME corner in a new place. Identity is carried, so
    the sharer comes along and the uid does not change: a promoted neighbour
    follows a drag because it IS the corner, not because a scan remembered
    it."""
    a, b = _shared_pair(fp)
    corner = a.end_vertex("p2")
    uid = corner.uid
    moved = corner.relocated_to(QPointF(140, 0))
    a.set_end_vertex("p2", moved)
    b.set_end_vertex("p1", moved)

    assert (a.p2.x(), a.p2.y()) == (140.0, 0.0)
    assert (b.p1.x(), b.p1.y()) == (140.0, 0.0), "the sharer was left behind"
    assert a.end_vertex("p2") is b.end_vertex("p1"), "the sharing was broken"
    assert moved.uid == uid, "a relocation renamed the corner"


# ------------------------------------------------------------- the Vertex type
def test_a_no_op_move_keeps_identity_and_sharing(fp):
    """A move to where the corner already is returns `self`, and the codebase
    leans on that constantly -- every rebuild, every settle, and every mouse
    event of a drag that has not yet moved."""
    a, b = _shared_pair(fp)
    corner = a.end_vertex("p2")
    assert corner.relocated_to(QPointF(100, 0)) is corner
    assert corner.relocated_to((100, 0)) is corner
    assert corner.relocated_to(QPointF(100, 0.5)) is not corner
    assert a.end_vertex("p2") is b.end_vertex("p1"), "sharing was disturbed"


def test_vertex_is_never_mutated_in_place(fp):
    """`point()` returns the shared QPointF rather than a copy, which is only
    safe because a move mints a NEW vertex rather than editing this one. A
    caller holding an old `p1` keeps seeing the old position."""
    w = _wall(fp, 0, 0, 100, 0)
    held = w.p1
    w.set_end_vertex("p1", w.end_vertex("p1").relocated_to(QPointF(50, 50)))
    assert (held.x(), held.y()) == (0.0, 0.0), \
        "a captured p1 moved under the caller"


def test_moving_both_ends_moves_the_whole_wall(fp, scene):
    """The ordinary case: nothing about the representation is visible to a
    caller that just wants the wall somewhere else."""
    w = _wall(fp, 0, 0, 100, 0)
    scene.addItem(w)
    for attr, p in (("p1", QPointF(10, 10)), ("p2", QPointF(110, 10))):
        w.set_end_vertex(attr, w.end_vertex(attr).relocated_to(p))
    w.rebuild()
    assert (w.p1.x(), w.p1.y(), w.p2.x(), w.p2.y()) == (10.0, 10.0, 110.0, 10.0)
    assert w.length() == pytest.approx(100.0)


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
