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


def test_ctrl_gives_a_15_degree_stepped_ridge_same_as_a_wall(fp, win, monkeypatch):
    """Patrick's own check: Ctrl on the ridge drag should behave exactly
    like Ctrl on a wall drag -- 15deg increments, not just Shift's free
    angle. Same shared `_wall_end_point` fix, so this is the ridge-side
    receipt for `test_wall_draw_ctrl_snaps_to_15_degrees`."""
    win.prepare_headless()
    _eaves_wall(fp, win)
    win.set_tool(fp.TOOL_ROOF_RIDGE)
    monkeypatch.setattr(QDialog, "exec",
                        lambda self: QDialog.DialogCode.Accepted)

    ctrl = Qt.KeyboardModifier.ControlModifier
    _drag_ridge(win, (0, 0), (100, 84), mods=ctrl)   # ~40deg -> snaps to 45
    _click(win, (100, 100))

    roofs = _roofs(win)
    assert len(roofs) == 1
    r = roofs[0]
    length = (r.p2.x() ** 2 + r.p2.y() ** 2) ** 0.5
    assert r.p2.x() == pytest.approx(length * 0.7071067811865476, abs=0.05)
    assert r.p2.y() == pytest.approx(length * 0.7071067811865476, abs=0.05)


def test_a_ridge_too_short_is_discarded(fp, win):
    win.prepare_headless()
    win.set_tool(fp.TOOL_ROOF_RIDGE)
    _drag_ridge(win, (0, 0), (1, 0))       # under MIN_WALL_LEN
    assert _roofs(win) == []
    assert win.view._temp_roof is None
    assert win.view._roof_awaiting_eaves is None


def test_escape_before_the_ridge_is_released_discards_it(fp, win):
    """STILL BEING DRAGGED (not yet released) is the wall tool's own
    precedent exactly: an in-progress drag is free to cancel."""
    win.prepare_headless()
    win.set_tool(fp.TOOL_ROOF_RIDGE)
    left = Qt.MouseButton.LeftButton
    _send_mouse(win, QEvent.Type.MouseButtonPress, 0, 0, left, left)
    _send_mouse(win, QEvent.Type.MouseMove, 200, 0,
               Qt.MouseButton.NoButton, left)
    assert win.view._temp_roof is not None
    win.view.cancel_temp()
    assert _roofs(win) == []
    assert win.view._temp_roof is None


def test_escape_while_awaiting_the_eaves_pick_keeps_the_ridge(fp, win):
    """Patrick's own report (`fixtures/disappearingroof.fpm`, replayed
    verbatim below): a
    ridge already released reads as a finished roof on screen (the full
    eave/gable preview is drawn from the moment it exists) -- abandoning
    the eaves pick (Esc, or -- the real report -- switching tools) must
    not silently discard something that already looked done. It is kept,
    with span_in auto-derived from the nearest qualifying wall, same
    search a LOADED roof already uses; the default constructor heights
    stay adjustable afterward from the marker's own dialog."""
    win.prepare_headless()
    win.scene.addItem(fp.WallItem(QPointF(0, 100), QPointF(200, 100),
                                  "exterior"))
    win.set_tool(fp.TOOL_ROOF_RIDGE)
    _drag_ridge(win, (0, 0), (200, 0))
    pending = win.view._roof_awaiting_eaves
    assert pending is not None

    win.view.cancel_temp()

    assert win.view._roof_awaiting_eaves is None
    assert _roofs(win) == [pending]             # kept, not discarded
    assert pending.span_in == pytest.approx(100.0)   # derived from the wall
    assert pending.ridge_h_in == 132.0 and pending.eaves_h_in == 96.0


def test_switching_tools_while_awaiting_the_eaves_pick_keeps_the_ridge(fp, win):
    """The exact reported scenario: G, drag a ridge, then switch tools
    with NO eaves click at all -- set_tool()'s own cancel_temp() call must
    not throw the ridge away."""
    win.prepare_headless()
    win.scene.addItem(fp.WallItem(QPointF(0, 100), QPointF(200, 100),
                                  "exterior"))
    win.set_tool(fp.TOOL_ROOF_RIDGE)
    _drag_ridge(win, (0, 0), (200, 0))
    assert win.view._roof_awaiting_eaves is not None

    win.set_tool(fp.TOOL_SELECT)

    assert len(_roofs(win)) == 1
    assert win.view._roof_awaiting_eaves is None


def test_replaying_the_reported_macro_keeps_the_roof_after_switching_tools(
        fp, win, monkeypatch):
    """`fixtures/disappearingroof.fpm`, replayed verbatim -- Patrick's own
    reproduced report (see `fixtures/README.md`'s own entry): four walls,
    a ridge sketched across them with NO eaves-pick click, then `S ^Z`
    (Select, Undo). Confirmed RED against the unfixed `cancel_temp()`
    (the roof was gone after `S`), GREEN after."""
    import pathlib
    macro = pathlib.Path(__file__).resolve().parent.parent / "fixtures" / "disappearingroof.fpm"
    win.prepare_headless()
    monkeypatch.setattr(QDialog, "exec",
                        lambda self: QDialog.DialogCode.Accepted)
    lines = macro.read_text(encoding="utf-8").splitlines()
    for line in lines[:-1]:                     # every line except "S ^Z"
        if line.strip():
            res = win.run_macro(line)
            assert res["ok"], res

    # "S": the ridge must survive the tool switch, auto-completed --
    # this is the fix; the fixture's own bug report was that it did not
    res = win.run_macro("S")
    assert res["ok"], res
    roofs = _roofs(win)
    assert len(roofs) == 1
    assert roofs[0].span_in > 0

    # "^Z" (undo, the fixture's own diagnostic step): a NORMAL undo of the
    # roof's own creation now, not a rescue of a wrongly-discarded item --
    # and redo round-trips it back cleanly, not a corrupted shape
    res = win.run_macro("^Z")
    assert res["ok"], res
    assert _roofs(win) == []
    win.redo()
    assert len(_roofs(win)) == 1


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
