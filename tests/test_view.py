"""PlanView zoom behaviour: a wheel burst coalesces into one zoom/repaint.

High-resolution wheels and trackpads emit many wheelEvents per physical notch.
Applying scale() (and a full-viewport repaint) per event stalls a large plan for
seconds.  The view accumulates the delta and applies it once on the next frame.
"""
import pytest
from PyQt6.QtCore import QPoint, Qt
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
