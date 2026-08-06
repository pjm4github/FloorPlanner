"""PlanView zoom behaviour: a wheel burst coalesces into one zoom/repaint.

High-resolution wheels and trackpads emit many wheelEvents per physical notch.
Applying scale() (and a full-viewport repaint) per event stalls a large plan for
seconds.  The view accumulates the delta and applies it once on the next frame.
"""
import pytest
from PyQt6.QtCore import QPoint, QPointF, Qt
from PyQt6.QtGui import QWheelEvent

pytestmark = pytest.mark.gui


def _wheel(view, delta):
    vp = view.viewport()
    pos = QPoint(vp.width() // 2, vp.height() // 2)
    ev = QWheelEvent(pos.toPointF(), view.mapToGlobal(pos).toPointF(),
                     QPoint(0, 0), QPoint(0, delta), Qt.MouseButton.NoButton,
                     Qt.KeyboardModifier.NoModifier,
                     Qt.ScrollPhase.NoScrollPhase, False)
    view.wheelEvent(ev)


def test_wheel_burst_is_deferred_then_coalesced(win):
    view = win.view
    view.resetTransform()
    start = view.transform().m11()

    # a burst of events accumulates without touching the transform yet
    for _ in range(10):
        _wheel(view, 40)
    assert view.transform().m11() == start      # nothing applied synchronously
    # view._zoom_accum: not scheduled for removal — wheel coalescing is deliberate
    # (CLAUDE.md, view.py:159-179). Asserting the exact accumulator value is a bit
    # brittle, but that is a test-quality nit, not a migration hazard.
    assert view._zoom_accum == 400
    assert view._zoom_timer.isActive()

    # the frame timer applies the whole burst in a single scale()
    view._apply_zoom()
    assert view.transform().m11() > start
    assert view._zoom_accum == 0


def test_zoom_is_clamped(win):
    view = win.view
    view.resetTransform()
    for _ in range(50):
        _wheel(view, 120)
        view._apply_zoom()
    assert view.transform().m11() <= 40.0
    for _ in range(80):
        _wheel(view, -120)
        view._apply_zoom()
    assert view.transform().m11() >= 0.03


def test_drawing_a_wall_splits_no_vertices(fp, win, drag):
    """P4.5: the draw gesture RELOCATES the moving end instead of assigning it.

    `view.py`'s `_temp_wall.p2 = ...` was the last `p1`/`p2` writer left in
    `floorplanner/` -- the P3.1 split-on-write shim's final production call
    site -- and it fired once per mouse-move event, minting a fresh `Vertex`
    for an end nobody else was holding yet.

    Differential receipt, one gesture of 40 move events: 40 split-on-writes
    before, 0 after, with the drawn wall byte-identical at (0,0)-(240,0). The
    wall is what makes this a regression test rather than a counter-watch: a
    "0 splits" that also drew nothing would pass an assertion about the
    counter alone.

    `split_count` answers "how many SPLIT-ON-WRITES happened", not "did
    identity change" -- a `relocated_to` changes the object and reports zero,
    deliberately (the instrument-boundary table). That is exactly the
    distinction being asserted: the drawn end stays ONE corner for the whole
    gesture."""
    from floorplanner import vertex as V
    win.tool = fp.TOOL_WALL_INT
    before = V.split_count()
    n0 = sum(1 for it in win.scene.items() if isinstance(it, fp.WallItem))

    drag(win, QPointF(0, 0), 240, 0, steps=40)

    walls = [it for it in win.scene.items() if isinstance(it, fp.WallItem)]
    # PRECONDITION -- the gesture actually drew something, so "0 splits" is a
    # statement about a draw and not about an event stream that did nothing
    assert len(walls) == n0 + 1, "the drag drew no wall"
    w = walls[-1]
    assert w.length() > 0
    assert V.split_count() == before, (
        f"the draw gesture split {V.split_count() - before} vertices")
