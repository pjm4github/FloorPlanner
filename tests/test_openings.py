"""P3.6 -- an opening is dimensioned from a NAMED END, not from `p1`.

The three properties the schema claims for `{from, offset_in}` and absolute `s`
cannot deliver, quoted from `design-schema.v5.json`:

    "Dimensioned the way a drawing dimensions it: an offset from a NAMED END,
     not an absolute distance from p1. Survives the wall being stretched, split
     at a new vertex, or reversed -- absolute `s` survives none of those."

(a) and (b) are here; the split is in test_topology_ops.py, where the split
planner's own tests live.
"""
import pytest
from PyQt6.QtCore import QPointF

pytestmark = pytest.mark.walls


def _wall_with_door(fp, scene, x2=240.0, s=200.0):
    w = fp.WallItem(QPointF(0, 0), QPointF(x2, 0), "interior")
    scene.addItem(w)
    op = fp.OpeningItem(w, "door", "3280", s)      # 32" wide, centre at s
    w.openings.append(op)
    w.rebuild()
    return w, op


def test_an_opening_holds_its_offset_when_the_far_end_is_stretched(fp, scene):
    """R1(a) -- THE DISCRIMINATING CASE.

    A door 40" from the v2 end stays 40" from the v2 end when v2 moves. Under
    absolute `s` it holds its distance from v1 instead, so stretching the wall
    at v2 slides the door away from the end it was dimensioned off -- which is
    never what a drawing means."""
    w, op = _wall_with_door(fp, scene, 240.0, 200.0)
    assert op.anchor_from(w) == "v2", "a door past the midpoint anchors to v2"
    off0 = op.offset_in
    gap0 = w.length() - op.s                       # centre-to-v2, 40"

    v = w.end_vertex("p2")                         # stretch AT v2
    w.set_end_vertex("p2", v.relocated_to(QPointF(300.0, 0.0)))
    w.rebuild()

    assert op.offset_in == pytest.approx(off0), "the stored offset moved"
    assert w.length() - op.s == pytest.approx(gap0), \
        "the door did not keep its distance from the end it is dimensioned off"


def test_reversing_a_wall_leaves_its_openings_where_they_are(fp, scene):
    """R1(b). Swapping a wall's two ends is a change of description, not of
    geometry, so nothing may move. Under absolute `s` -- measured from
    whichever end is currently `p1` -- every opening MIRRORS."""
    w, op = _wall_with_door(fp, scene, 240.0, 200.0)
    before = QPointF(w.point_at(op.s))

    v1, v2 = w.end_vertex("p1"), w.end_vertex("p2")
    w.set_end_vertex("p1", v2)                     # a raw swap: same wall,
    w.set_end_vertex("p2", v1)                     # described the other way
    w.rebuild()

    after = w.point_at(op.s)
    assert after.x() == pytest.approx(before.x(), abs=1e-6), \
        f"the door mirrored: {before.x()} -> {after.x()}"
    assert after.y() == pytest.approx(before.y(), abs=1e-6)
