"""Patrick, 2026-09-24, on R5b's check: *"lets do the undo. also make sure
that the script tool has commands to handle tha dormer."*

THE UNDO was already there: undo is snapshot-based and driven by the
scene's own change signal (`MainWindow._mark_dirty` <- `scene.changed`),
so deleting a roof -- and a host with its dormers -- always became one undo
step, dormers restored with their host resolved through the document.
0192-report.md sec3 said otherwise; 0193 corrects it, and these tests pin
it so the claim is never made from memory again.

THE MACRO gains a self-contained `DORMER x y width eaves ridge [dx dy]`
token on the DOOR/WINDOW/ROOM pattern: the recorder emits it when a dormer
is finished through the tool (the dialog's values baked in, the raw drag
suppressed) and the runner builds the dormer with no dialog.
"""
import pytest
from PyQt6.QtCore import QEvent, QPointF, Qt
from PyQt6.QtGui import QMouseEvent, QPainterPath
from PyQt6.QtWidgets import QApplication, QDialog

pytestmark = pytest.mark.macro

TRACE_Y = 100.0 + (150.0 - 96.0) / 0.7        # host eaves 80: the trace


def _house(fp, win):
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


def _dormers(win):
    return [r for r in _roofs(win) if r.is_dormer()]


# --------------------------------------------------------------------------
# the undo, pinned
# --------------------------------------------------------------------------
def test_deleting_a_host_with_its_dormer_is_one_undo_step(fp, win):
    from floorplanner.roofs import RoofItem
    win.prepare_headless()
    host = _house(fp, win)
    d = RoofItem(QPointF(200, 190), QPointF(200, 180), eaves_h_in=110.0,
                 ridge_h_in=130.0, overhang_in=0.0, span_in=30.0, marker_end=0,
                 host=host)
    d.floor = fp.DEFAULT_FLOOR
    win.scene.addItem(d)
    win._commit_if_changed()                       # the baseline state
    depth = len(win._undo_stack)
    host.remove_with_dormers()
    win._commit_if_changed()                       # the debounce, settled
    assert _roofs(win) == [] and len(win._undo_stack) == depth + 1
    win.undo()
    roofs = _roofs(win)
    assert len(roofs) == 2
    back = _dormers(win)
    assert len(back) == 1 and back[0].host in roofs
    assert back[0].p2.y() == pytest.approx(100.0 + 20.0 / 0.7, abs=1e-6)
    win.redo()
    assert _roofs(win) == []


def test_a_dormer_sketched_with_the_tool_undoes_as_one_step(fp, win, monkeypatch):
    win.prepare_headless()
    _house(fp, win)
    win._commit_if_changed()
    win.set_tool(fp.TOOL_ROOF_DORMER)
    monkeypatch.setattr(QDialog, "exec", lambda self: QDialog.DialogCode.Accepted)
    win.run_macro(f"CLICK 204 {TRACE_Y:.2f} DRAG 240 {TRACE_Y:.2f}")
    assert len(_dormers(win)) == 1
    win._commit_if_changed()
    win.undo()
    assert len(_dormers(win)) == 0 and len(_roofs(win)) == 1


# --------------------------------------------------------------------------
# the runner: DORMER, dialog-free
# --------------------------------------------------------------------------
def test_dormer_token_builds_a_dormer_on_the_roof_plane(fp, win):
    win.prepare_headless()
    host = _house(fp, win)
    res = win.run_macro(f"DORMER 204 {TRACE_Y + 3:.2f} 36 120 132.6")
    assert res["ok"], res["errors"]
    d = _dormers(win)
    assert len(d) == 1 and d[0].host is host
    d = d[0]
    assert d.p1.x() == pytest.approx(204.0) and d.p1.y() == pytest.approx(TRACE_Y)
    assert d.span_in == [18.0, 18.0]
    assert d.eaves_h_in == 120.0 and d.ridge_h_in == pytest.approx(132.6)
    assert d.p2.x() == pytest.approx(204.0)
    assert d.p2.y() == pytest.approx(100.0 + (150.0 - 132.6) / 0.7, abs=1e-6)
    assert d.marker_end == 0


def test_dormer_token_with_a_direction_and_in_feet(fp, win):
    win.prepare_headless()
    _house(fp, win)
    res = win.run_macro("DORMER 204 177.14 3' 120 132.6 -0.7071 -0.7071")
    assert res["ok"], res["errors"]
    d = _dormers(win)[0]
    dx, dy = d.p2.x() - d.p1.x(), d.p2.y() - d.p1.y()
    assert dx < 0 and dy < 0 and abs(abs(dx) - abs(dy)) < 1e-6
    assert d.span_in == [18.0, 18.0]


def test_dormer_token_off_every_roof_is_an_error_and_builds_nothing(fp, win):
    win.prepare_headless()
    _house(fp, win)
    res = win.run_macro("DORMER 200 400 36 120 132")
    assert not res["ok"] and any("no roof plane" in e for e in res["errors"])
    assert _dormers(win) == []


def test_dormer_token_with_a_ridge_the_host_never_meets_is_an_error(fp, win):
    win.prepare_headless()
    _house(fp, win)
    res = win.run_macro(f"DORMER 204 {TRACE_Y:.2f} 36 120 160")
    assert not res["ok"] and any("never meets" in e for e in res["errors"])
    assert _dormers(win) == []


def test_tool_letter_m_and_the_name_switch_to_the_dormer_tool(fp, win):
    win.run_macro("M")
    assert win.tool == fp.TOOL_ROOF_DORMER
    win.run_macro("S")
    win.run_macro("TOOL roofdormer")
    assert win.tool == fp.TOOL_ROOF_DORMER


# --------------------------------------------------------------------------
# the recorder: one DORMER token, the raw drag suppressed
# --------------------------------------------------------------------------
def _send_mouse(win, etype, sx, sy, button, buttons,
                mods=Qt.KeyboardModifier.NoModifier):
    vp = win.view.viewport()
    pos = win.view.mapFromScene(QPointF(sx, sy))
    ev = QMouseEvent(etype, QPointF(pos), QPointF(vp.mapToGlobal(pos)),
                     button, buttons, mods)
    QApplication.sendEvent(vp, ev)


def test_recorder_emits_a_self_contained_dormer_token(fp, win, monkeypatch):
    win.prepare_headless()
    _house(fp, win)
    monkeypatch.setattr(QDialog, "exec", lambda self: QDialog.DialogCode.Accepted)
    dlg = fp.MacroRecorderDialog(win)
    dlg.start()
    win.set_tool(fp.TOOL_ROOF_DORMER)                    # -> "M"
    left = Qt.MouseButton.LeftButton
    _send_mouse(win, QEvent.Type.MouseButtonPress, 204.0, TRACE_Y, left, left)
    _send_mouse(win, QEvent.Type.MouseMove, 240.0, TRACE_Y, Qt.MouseButton.NoButton, left)
    _send_mouse(win, QEvent.Type.MouseButtonRelease, 240.0, TRACE_Y, left,
                Qt.MouseButton.NoButton)
    dlg.stop()
    toks = dlg.edit.toPlainText().split()
    assert toks[0] == "M"
    assert "DORMER" in toks and "CLICK" not in toks and "DRAG" not in toks
    i = toks.index("DORMER")
    assert toks[i + 1:i + 4] == ["204", "177", "36"]
    assert float(toks[i + 4]) == 120.0 and float(toks[i + 5]) == pytest.approx(132.6)
    assert len(toks) == i + 6, "the default up-slope direction is not written"


def test_a_recorded_dormer_replays_to_the_same_dormer(fp, win, monkeypatch):
    """Round trip: record through the tool, replay the text on a fresh copy
    of the same house, compare the dormer's geometry."""
    win.prepare_headless()
    _house(fp, win)
    monkeypatch.setattr(QDialog, "exec", lambda self: QDialog.DialogCode.Accepted)
    dlg = fp.MacroRecorderDialog(win)
    dlg.start()
    win.set_tool(fp.TOOL_ROOF_DORMER)
    left = Qt.MouseButton.LeftButton
    _send_mouse(win, QEvent.Type.MouseButtonPress, 204.0, TRACE_Y, left, left)
    _send_mouse(win, QEvent.Type.MouseMove, 240.0, TRACE_Y, Qt.MouseButton.NoButton, left)
    _send_mouse(win, QEvent.Type.MouseButtonRelease, 240.0, TRACE_Y, left,
                Qt.MouseButton.NoButton)
    dlg.stop()
    text = dlg.edit.toPlainText()
    recorded = _dormers(win)[0]
    want = (recorded.p1.x(), recorded.p1.y(), recorded.p2.x(), recorded.p2.y(),
            *recorded.span_in, recorded.eaves_h_in, recorded.ridge_h_in)
    win.clear_plan()
    _house(fp, win)
    res = win.run_macro(text)
    assert res["ok"], res["errors"]
    got = _dormers(win)[0]
    assert (got.p1.x(), got.p1.y(), got.p2.x(), got.p2.y(), *got.span_in,
            got.eaves_h_in, got.ridge_h_in) == pytest.approx(want)
