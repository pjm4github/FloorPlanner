"""Roof ▸ Sketch dormer… -- R5b's own tool (0191-ruling.md sec2: "a separate
Dormer item in the Roof menu -- its own tool, its own macro letter --
sharing the two-stage machinery"). Press on a roof plane (snapped to the
host's clip trace), drag along it for the width, release into the End-On
dialog. Driven through the view exactly as tests/test_roof_ridge_tool.py
drives the ridge tool.
"""
import pytest
from PyQt6.QtCore import QEvent, QPoint, QPointF, Qt
from PyQt6.QtGui import QMouseEvent, QPainterPath
from PyQt6.QtWidgets import QApplication, QDialog, QMenu

pytestmark = pytest.mark.gui


def _send_mouse(win, etype, sx, sy, button, buttons,
                mods=Qt.KeyboardModifier.NoModifier):
    vp = win.view.viewport()
    pos = win.view.mapFromScene(QPointF(sx, sy))
    ev = QMouseEvent(etype, QPointF(pos), QPointF(vp.mapToGlobal(pos)),
                     button, buttons, mods)
    QApplication.sendEvent(vp, ev)


def _drag(win, p1, p2, mods=Qt.KeyboardModifier.NoModifier):
    left = Qt.MouseButton.LeftButton
    _send_mouse(win, QEvent.Type.MouseButtonPress, *p1, left, left)
    _send_mouse(win, QEvent.Type.MouseMove, *p2, Qt.MouseButton.NoButton, left, mods)
    _send_mouse(win, QEvent.Type.MouseButtonRelease, *p2, left,
                Qt.MouseButton.NoButton, mods)


def _house(fp, win):
    """A 96in loft under a host with 80in eaves: the trace sits at
    y = 100 + 54/0.7 = 177.14, well inside the room."""
    from floorplanner.roofs import RoofItem
    from floorplanner.rooms import RoomItem
    path = QPainterPath()
    path.addRect(0, 0, 400, 200)
    room = RoomItem("Loft", QPointF(200, 100), path, 100.0)
    room.floor = fp.DEFAULT_FLOOR
    room.properties["ceiling_height_in"] = 96.0
    win.scene.addItem(room)
    host = RoofItem(QPointF(0, 100), QPointF(400, 100), eaves_h_in=80.0,
                    ridge_h_in=150.0, overhang_in=12.0, span_in=100.0)
    host.floor = fp.DEFAULT_FLOOR
    win.scene.addItem(host)
    return host


def _roofs(win):
    from floorplanner.roofs import RoofItem
    return [it for it in win.scene.items() if isinstance(it, RoofItem)]


TRACE_Y = 100.0 + (150.0 - 96.0) / 0.7


def test_press_on_the_plane_drag_along_the_trace_makes_a_dormer(fp, win, monkeypatch):
    win.prepare_headless()
    host = _house(fp, win)
    win.set_tool(fp.TOOL_ROOF_DORMER)
    monkeypatch.setattr(QDialog, "exec", lambda self: QDialog.DialogCode.Accepted)
    _drag(win, (204.0, TRACE_Y + 3.0), (240.0, TRACE_Y + 3.0))   # 3in off the trace
    roofs = _roofs(win)
    assert len(roofs) == 2
    d = next(r for r in roofs if r.is_dormer())
    assert d.host is host
    assert d.p1.y() == pytest.approx(TRACE_Y), "the face snapped onto the trace"
    assert d.p1.x() == pytest.approx(204.0), "along the trace, on the 6in grid"
    assert d.span_in == [18.0, 18.0], "36in of drag = 18in each side, on the grid"
    assert d.eaves_h_in == pytest.approx(96.0 + 24.0)
    assert d.ridge_h_in == pytest.approx(120.0 + 18.0 * 0.7)
    # ridge up-slope: toward the host ridge (plan y decreasing), back end derived
    assert d.p2.x() == pytest.approx(204.0)
    assert d.p2.y() == pytest.approx(100.0 + (150.0 - d.ridge_h_in) / 0.7, abs=1e-6)
    assert d.marker_end == 0


def test_a_press_off_every_roof_makes_nothing(fp, win):
    win.prepare_headless()
    _house(fp, win)
    win.set_tool(fp.TOOL_ROOF_DORMER)
    _drag(win, (200.0, 400.0), (240.0, 400.0))
    assert len(_roofs(win)) == 1


def test_a_click_without_a_drag_is_too_narrow_and_discarded(fp, win):
    win.prepare_headless()
    _house(fp, win)
    win.set_tool(fp.TOOL_ROOF_DORMER)
    _drag(win, (200.0, TRACE_Y), (200.0, TRACE_Y))
    assert len(_roofs(win)) == 1


def test_escape_during_the_drag_discards_the_dormer(fp, win):
    win.prepare_headless()
    _house(fp, win)
    win.set_tool(fp.TOOL_ROOF_DORMER)
    left = Qt.MouseButton.LeftButton
    _send_mouse(win, QEvent.Type.MouseButtonPress, 200.0, TRACE_Y, left, left)
    _send_mouse(win, QEvent.Type.MouseMove, 236.0, TRACE_Y, Qt.MouseButton.NoButton, left)
    assert len(_roofs(win)) == 2, "precondition: a dormer is being dragged"
    win.view.cancel_temp()
    assert len(_roofs(win)) == 1


def test_cancelling_the_heights_dialog_drops_the_dormer(fp, win, monkeypatch):
    win.prepare_headless()
    _house(fp, win)
    win.set_tool(fp.TOOL_ROOF_DORMER)
    monkeypatch.setattr(QDialog, "exec", lambda self: QDialog.DialogCode.Rejected)
    _drag(win, (200.0, TRACE_Y), (236.0, TRACE_Y))
    assert len(_roofs(win)) == 1


def test_shift_frees_the_ridge_direction(fp, win, monkeypatch):
    win.prepare_headless()
    _house(fp, win)
    win.set_tool(fp.TOOL_ROOF_DORMER)
    monkeypatch.setattr(QDialog, "exec", lambda self: QDialog.DialogCode.Accepted)
    _drag(win, (200.0, TRACE_Y), (236.0, TRACE_Y - 36.0), Qt.KeyboardModifier.ShiftModifier)
    d = next(r for r in _roofs(win) if r.is_dormer())
    dx, dy = d.p2.x() - d.p1.x(), d.p2.y() - d.p1.y()
    assert dx < 0 and dy < 0, "perpendicular to the diagonal drag, still up-slope"
    # the synthetic drag is pixel-quantised by the view, so a few inches
    assert abs(abs(dx) - abs(dy)) < 3.0


def test_the_dialog_refuses_a_ridge_the_host_never_meets(fp, win):
    """The End-On dialog's dormer refusal (0191 sec1): typed above the
    host's ridge, `apply` returns False and the tool drops the dormer."""
    from floorplanner.dialogs import RoofEndOnDialog
    from floorplanner.roofs import RoofItem
    win.prepare_headless()
    host = _house(fp, win)
    d = RoofItem(QPointF(200, TRACE_Y), QPointF(200, TRACE_Y - 12), eaves_h_in=120.0,
                 ridge_h_in=132.0, overhang_in=0.0, span_in=18.0, marker_end=0, host=host)
    d.floor = fp.DEFAULT_FLOOR
    win.scene.addItem(d)
    dlg = RoofEndOnDialog(d, win)
    assert dlg.dormer_meet_in() == pytest.approx(TRACE_Y - (100.0 + (150.0 - 132.0) / 0.7))
    assert dlg.apply() is True
    dlg.sp_ridge.setValue(160.0)                      # above the host ridge
    assert dlg.dormer_meet_in() is None
    assert "cannot stand" in dlg.lab_dormer.text()
    assert dlg.apply() is False
    dlg.accept()
    assert dlg.result() != QDialog.DialogCode.Accepted, "stays open on a refusal"


def test_roof_menu_offers_sketch_dormer_and_the_macro_letter_round_trips(fp, win):
    labels = [a.text() for a in win.menuBar().actions()]
    m_roof = next(a.menu() for a in win.menuBar().actions() if "oof" in a.text())
    texts = [a.text() for a in m_roof.actions()]
    assert any("dormer" in t.lower() for t in texts), texts
    from floorplanner.macro import MacroRecorderDialog, MacroRunner
    assert MacroRunner._TOOL_CODES["H"] == fp.TOOL_ROOF_DORMER
    assert MacroRecorderDialog._TOOL_CODES[fp.TOOL_ROOF_DORMER] == "H"
    assert MacroRunner._TOOL_NAMES["roofdormer"] == fp.TOOL_ROOF_DORMER
    assert labels


def test_shift_click_builds_a_full_gable_dormer_to_the_eaves(fp, win):
    """Build Dormer (the M tool's Shift+click): one point near the host's
    ridge builds a whole gable dormer whose face drops down-slope to the
    eaves, whose cheeks take the host's pitch, and whose ridge apex sits at
    the click -- no drag, no dialog. Host: eaves 80, ridge 150, span 100,
    so pitch 0.7. Shift+click at (204, 150), 50in down-slope from the ridge
    (y = 100): the run to the eave (y = 200) is 100 - 50 = 50."""
    win.prepare_headless()
    host = _house(fp, win)
    win.set_tool(fp.TOOL_ROOF_DORMER)
    shift = Qt.KeyboardModifier.ShiftModifier
    left = Qt.MouseButton.LeftButton
    _send_mouse(win, QEvent.Type.MouseButtonPress, 204.0, 150.0, left, left, shift)
    _send_mouse(win, QEvent.Type.MouseButtonRelease, 204.0, 150.0, left,
                Qt.MouseButton.NoButton, shift)
    roofs = _roofs(win)
    assert len(roofs) == 2, "one Shift+click built one dormer, no dialog"
    d = next(r for r in roofs if r.is_dormer())
    assert d.host is host
    assert d.marker_end == 0
    assert d.p1.x() == pytest.approx(204.0) and d.p1.y() == pytest.approx(200.0), \
        "the face drops straight down-slope to the host's eave line"
    assert d.eaves_h_in == pytest.approx(80.0), "the dormer's eaves are the host's"
    assert d.ridge_h_in == pytest.approx(115.0), "ridge = host surface at the click"
    assert d.span_in == [50.0, 50.0], "half-span = the up-slope run to the eave"
    cheek_pitch = (d.ridge_h_in - d.eaves_h_in) / d.span_in[0]
    assert cheek_pitch == pytest.approx(0.7), "both cheeks take the host's pitch"
    assert d.p2.x() == pytest.approx(204.0) and d.p2.y() == pytest.approx(150.0), \
        "the ridge apex is derived back onto the click point"


def test_shift_click_on_the_ridge_line_builds_nothing(fp, win):
    host = _house(fp, win)
    win.view._build_dormer_auto(host, QPointF(200.0, 100.0))   # on the ridge
    assert len(_roofs(win)) == 1


def test_shift_click_too_close_to_the_eave_builds_nothing(fp, win):
    host = _house(fp, win)
    win.view._build_dormer_auto(host, QPointF(204.0, 199.0))   # 1in off the eave
    assert len(_roofs(win)) == 1


class _CtxEvent:
    """The two things RoofItem.contextMenuEvent reads off its event."""
    def screenPos(self):
        return QPoint(0, 0)

    def accept(self):
        pass


def _menu_labels(item, monkeypatch):
    captured = {}

    def fake_exec(self, *a):
        captured["labels"] = [act.text() for act in self.actions()]
        return None

    monkeypatch.setattr(QMenu, "exec", fake_exec)
    item.contextMenuEvent(_CtxEvent())
    return captured["labels"]


def test_a_dormers_context_menu_offers_edit_and_delete_dormer(fp, win, monkeypatch):
    from floorplanner.roofs import RoofItem
    win.prepare_headless()
    host = _house(fp, win)
    d = RoofItem(QPointF(200, TRACE_Y), QPointF(200, TRACE_Y - 12), eaves_h_in=120.0,
                 ridge_h_in=132.0, overhang_in=0.0, span_in=18.0, marker_end=0, host=host)
    d.floor = fp.DEFAULT_FLOOR
    win.scene.addItem(d)
    labels = _menu_labels(d, monkeypatch)
    assert labels[0].startswith("Edit dormer")
    assert labels[1] == "Delete dormer"


def test_a_plain_roofs_context_menu_is_unchanged(fp, win, monkeypatch):
    win.prepare_headless()
    host = _house(fp, win)
    labels = _menu_labels(host, monkeypatch)
    assert labels[0].startswith("Roof parameters")
    assert labels[1] == "Delete roof"


def test_hiding_roofs_leaves_the_dormer_tool(fp, win):
    win.prepare_headless()
    win.set_tool(fp.TOOL_ROOF_DORMER)
    win._set_show_roofs(False)
    assert win.tool == fp.TOOL_SELECT
