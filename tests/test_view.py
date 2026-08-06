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


def test_drawing_a_wall_keeps_the_moving_end_one_corner(fp, win, drag):
    """P4.5: the draw gesture RELOCATES the moving end instead of assigning it,
    so the drawn end is ONE corner for the whole gesture.

    `view.py`'s `_temp_wall.p2 = ...` was the last `p1`/`p2` writer in
    `floorplanner/` -- the P3.1 shim's final production call site -- and it
    fired once per mouse-move event, minting a fresh `Vertex` (and a fresh uid)
    for an end nobody else was holding yet.

    CONVERTED AT P4.5 from `assert split_count() == before`, in the same pass
    that retired the counter. The counter answered "how many split-on-writes
    happened", which is a fact about a mechanism now gone; what this test is
    really about is that the drawn corner keeps ONE identity across many
    events. Asserted as the uid, sampled after the first move that actually
    places the end and compared at release -- strictly stronger than the count,
    because it fails on churn arriving by any route, including a route with no
    counter behind it.

    Differential receipt at the conversion: the same 40-event gesture caused 40
    split-on-writes before P4.5(33) and 0 after, with the drawn wall
    byte-identical at (0,0)-(240,0)."""
    win.tool = fp.TOOL_WALL_INT
    n0 = sum(1 for it in win.scene.items() if isinstance(it, fp.WallItem))
    seen = []
    vp = win.view.viewport()
    orig = win.view.mouseMoveEvent

    def spy(e):
        orig(e)
        w = win.view._temp_wall
        if w is not None and w.length() > 0:
            seen.append(w.end_vertex("p2").uid)

    win.view.mouseMoveEvent = spy
    try:
        drag(win, QPointF(0, 0), 240, 0, steps=40)
    finally:
        win.view.mouseMoveEvent = orig
    assert vp is win.view.viewport()          # the spy went to the right object

    walls = [it for it in win.scene.items() if isinstance(it, fp.WallItem)]
    # PRECONDITIONS -- the gesture drew a wall, and it did so over MANY events.
    # Either alone would make the verdict empty: one sample cannot churn, and a
    # gesture that drew nothing has no end to keep.
    assert len(walls) == n0 + 1, "the drag drew no wall"
    assert walls[-1].length() > 0
    assert len(seen) >= 10, f"only {len(seen)} move events placed the end"

    assert len(set(seen)) == 1, (
        f"the drawn end took {len(set(seen))} identities across "
        f"{len(seen)} move events")
    assert walls[-1].end_vertex("p2").uid == seen[0],         "the end was re-minted between the last move and the release"
