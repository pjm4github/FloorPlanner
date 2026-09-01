"""Roof ▸ Sketch ridge… -- 0139-ruling.md R2, checked per 0140-ruling.md
sec3's table entry: "sketch the main ridge and the 45deg wing ridge on
wiscaway; modifiers feel like the wall tool."

The ridge gesture reuses the wall tool's own snap machinery (0139-ruling.md
sec1: "the ridge tool calls that machinery"), so these tests mirror
test_macro.py's `_send_mouse` drive-the-view pattern rather than inventing
a second one, and pin exactly the two things that machinery promises: the
default snaps orthogonal, Shift gives a free angle -- same as a wall.
"""
import pytest
from PyQt6.QtCore import QEvent, QPointF, Qt
from PyQt6.QtGui import QMouseEvent
from PyQt6.QtWidgets import QApplication, QDialog

pytestmark = pytest.mark.gui


def _send_mouse(win, etype, sx, sy, button, buttons,
                mods=Qt.KeyboardModifier.NoModifier):
    vp = win.view.viewport()
    pos = win.view.mapFromScene(QPointF(sx, sy))
    ev = QMouseEvent(etype, QPointF(pos), QPointF(vp.mapToGlobal(pos)),
                     button, buttons, mods)
    QApplication.sendEvent(vp, ev)


def _drag_ridge(win, p1, p2, mods=Qt.KeyboardModifier.NoModifier):
    left = Qt.MouseButton.LeftButton
    _send_mouse(win, QEvent.Type.MouseButtonPress, *p1, left, left)
    _send_mouse(win, QEvent.Type.MouseMove, *p2, Qt.MouseButton.NoButton,
               left, mods)
    _send_mouse(win, QEvent.Type.MouseButtonRelease, *p2, left,
               Qt.MouseButton.NoButton, mods)


def _click(win, p, mods=Qt.KeyboardModifier.NoModifier):
    left = Qt.MouseButton.LeftButton
    _send_mouse(win, QEvent.Type.MouseButtonPress, *p, left, left, mods)
    _send_mouse(win, QEvent.Type.MouseButtonRelease, *p, left,
               Qt.MouseButton.NoButton, mods)


def _eaves_wall(fp, win, y=100.0):
    wall = fp.WallItem(QPointF(0, y), QPointF(200, y), "exterior")
    win.scene.addItem(wall)
    return wall


def _roofs(win):
    from floorplanner.roofs import RoofItem
    return [it for it in win.scene.items() if isinstance(it, RoofItem)]


def test_sketch_ridge_defaults_to_orthogonal_like_a_wall(fp, win, monkeypatch):
    win.prepare_headless()
    _eaves_wall(fp, win)
    win.set_tool(fp.TOOL_ROOF_RIDGE)
    monkeypatch.setattr(QDialog, "exec",
                        lambda self: QDialog.DialogCode.Accepted)

    _drag_ridge(win, (0, 0), (198, 5))     # a slight drift off horizontal
    assert win.view._roof_awaiting_eaves is not None
    _click(win, (100, 100))                # picks the eaves wall

    roofs = _roofs(win)
    assert len(roofs) == 1
    r = roofs[0]
    assert r.p1.y() == pytest.approx(0.0) and r.p2.y() == pytest.approx(0.0)
    assert win.view._roof_awaiting_eaves is None


def test_shift_gives_a_free_angle_ridge_same_as_a_wall(fp, win, monkeypatch):
    win.prepare_headless()
    _eaves_wall(fp, win)
    win.set_tool(fp.TOOL_ROOF_RIDGE)
    monkeypatch.setattr(QDialog, "exec",
                        lambda self: QDialog.DialogCode.Accepted)

    shift = Qt.KeyboardModifier.ShiftModifier
    _drag_ridge(win, (0, 0), (120, 120), mods=shift)   # both on-grid: exact 45
    _click(win, (100, 100))

    roofs = _roofs(win)
    assert len(roofs) == 1
    r = roofs[0]
    assert (r.p1.x(), r.p1.y()) == (0.0, 0.0)
    assert (r.p2.x(), r.p2.y()) == (120.0, 120.0)     # true 45deg, not snapped square


def test_a_ridge_too_short_is_discarded(fp, win):
    win.prepare_headless()
    win.set_tool(fp.TOOL_ROOF_RIDGE)
    _drag_ridge(win, (0, 0), (1, 0))       # under MIN_WALL_LEN
    assert _roofs(win) == []
    assert win.view._temp_roof is None
    assert win.view._roof_awaiting_eaves is None


def test_escape_mid_draw_removes_the_ridge(fp, win):
    win.prepare_headless()
    win.set_tool(fp.TOOL_ROOF_RIDGE)
    _drag_ridge(win, (0, 0), (200, 0))
    assert win.view._roof_awaiting_eaves is not None
    win.view.cancel_temp()
    assert _roofs(win) == []
    assert win.view._roof_awaiting_eaves is None


def test_eaves_pick_on_blank_canvas_keeps_waiting(fp, win):
    win.prepare_headless()
    win.set_tool(fp.TOOL_ROOF_RIDGE)
    _drag_ridge(win, (0, 0), (200, 0))
    pending = win.view._roof_awaiting_eaves
    assert pending is not None

    _click(win, (600, 600))                # blank canvas, no wall there

    assert win.view._roof_awaiting_eaves is pending      # still waiting
    assert _roofs(win) == [pending]                      # nothing finished


def test_eaves_pick_sets_span_from_the_picked_wall(fp, win, monkeypatch):
    win.prepare_headless()
    _eaves_wall(fp, win, y=150.0)
    win.set_tool(fp.TOOL_ROOF_RIDGE)
    monkeypatch.setattr(QDialog, "exec",
                        lambda self: QDialog.DialogCode.Accepted)

    _drag_ridge(win, (0, 0), (200, 0))
    _click(win, (100, 150))

    roofs = _roofs(win)
    assert len(roofs) == 1
    assert roofs[0].span_in == pytest.approx(150.0)


def test_cancelling_the_heights_dialog_drops_the_roof(fp, win, monkeypatch):
    win.prepare_headless()
    _eaves_wall(fp, win)
    win.set_tool(fp.TOOL_ROOF_RIDGE)
    monkeypatch.setattr(QDialog, "exec",
                        lambda self: QDialog.DialogCode.Rejected)

    _drag_ridge(win, (0, 0), (200, 0))
    _click(win, (100, 100))

    assert _roofs(win) == []
    assert win.view._roof_awaiting_eaves is None


def test_roof_menu_offers_sketch_ridge(fp, win):
    from PyQt6.QtWidgets import QMenu
    m_roof = next(m for m in win.menuBar().findChildren(QMenu)
                 if m.title().replace("&", "").strip() == "Roof")
    labels = [a.text().replace("&", "") for a in m_roof.actions()]
    assert any("Sketch ridge" in t for t in labels)
