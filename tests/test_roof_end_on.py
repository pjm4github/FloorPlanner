"""R2b -- the End-On marker, its dialog, and the three-way ridge/eaves/
pitch recompute (0139-ruling.md sec2, sharpened by 0140-ruling.md).

Patrick's own check (0140-ruling.md sec3): "drop the marker on the main
ridge and the 45deg wing ridge; drag it end to end; set ridge+pitch and
watch eaves derive; set eaves and watch pitch derive." The recompute tests
below are that worked example, literally (both his examples: the
End-On-marker ruling's R+P->H case, and the dialog ruling's own R,H->P
then P->R sequence).
"""
import math

import pytest
from PyQt6.QtCore import QEvent, QPoint, QPointF, Qt
from PyQt6.QtGui import QContextMenuEvent, QMouseEvent
from PyQt6.QtWidgets import QApplication, QDialog, QMenu

from floorplanner.roofs import RoofItem

pytestmark = pytest.mark.gui


def _send_mouse(win, etype, sx, sy, button, buttons,
                mods=Qt.KeyboardModifier.NoModifier):
    vp = win.view.viewport()
    pos = win.view.mapFromScene(QPointF(sx, sy))
    ev = QMouseEvent(etype, QPointF(pos), QPointF(vp.mapToGlobal(pos)),
                     button, buttons, mods)
    QApplication.sendEvent(vp, ev)


def _right_click(win, sx, sy):
    vp = win.view.viewport()
    p = win.view.mapFromScene(QPointF(sx, sy))
    QApplication.sendEvent(vp, QContextMenuEvent(
        QContextMenuEvent.Reason.Mouse, QPoint(p), vp.mapToGlobal(QPoint(p))))
    QApplication.processEvents()


# --------------------------------------------------------------------------
# the marker: drag between ends
# --------------------------------------------------------------------------
def test_marker_defaults_to_the_ridges_second_end(fp, win):
    roof = RoofItem(QPointF(0, 0), QPointF(200, 0), span_in=100.0)
    win.scene.addItem(roof)
    assert roof.marker_end == 1
    assert (roof.marker.pos().x(), roof.marker.pos().y()) == (200.0, 0.0)


def test_dragging_the_marker_snaps_to_the_nearer_end(fp, win):
    win.prepare_headless()
    roof = RoofItem(QPointF(0, 0), QPointF(200, 0), span_in=100.0)
    win.scene.addItem(roof)
    assert roof.marker_end == 1                   # starts at p2 (200, 0)

    left = Qt.MouseButton.LeftButton
    _send_mouse(win, QEvent.Type.MouseButtonPress, 200, 0, left, left)
    _send_mouse(win, QEvent.Type.MouseMove, 20, 0, Qt.MouseButton.NoButton, left)
    _send_mouse(win, QEvent.Type.MouseButtonRelease, 20, 0, left,
               Qt.MouseButton.NoButton)

    assert roof.marker_end == 0
    assert (roof.marker.pos().x(), roof.marker.pos().y()) == (0.0, 0.0)


def test_dragging_the_marker_while_the_ridge_tool_is_still_active_works(fp, win):
    """The ridge tool stays active after a sketch (sticky, like Door/
    Window) -- a press on the EXISTING marker must be the marker's own
    drag, not "start a new ridge here." Caught by hand: an early cut of
    this tranche let TOOL_ROOF_RIDGE's press handler steal every press
    unconditionally, so dragging the marker right after sketching a ridge
    silently sketched a SECOND ridge instead."""
    win.prepare_headless()
    roof = RoofItem(QPointF(0, 0), QPointF(200, 0), span_in=100.0)
    win.scene.addItem(roof)
    win.set_tool(fp.TOOL_ROOF_RIDGE)     # still active, as it is after a sketch

    left = Qt.MouseButton.LeftButton
    _send_mouse(win, QEvent.Type.MouseButtonPress, 200, 0, left, left)
    _send_mouse(win, QEvent.Type.MouseMove, 10, 0, Qt.MouseButton.NoButton, left)
    _send_mouse(win, QEvent.Type.MouseButtonRelease, 10, 0, left,
               Qt.MouseButton.NoButton)

    roofs = [it for it in win.scene.items() if isinstance(it, RoofItem)]
    assert len(roofs) == 1                # no second ridge sketched
    assert roof.marker_end == 0
    assert (roof.marker.pos().x(), roof.marker.pos().y()) == (0.0, 0.0)


def test_dragging_the_marker_on_a_45_degree_ridge_still_snaps(fp, win):
    """Off-orthogonal ridges are free by construction (0140-ruling.md
    sec1) -- the marker only ever compares distances to p1/p2, never an
    axis, so a 45deg wing ridge works identically."""
    win.prepare_headless()
    roof = RoofItem(QPointF(0, 0), QPointF(120, 120), span_in=50.0)
    win.scene.addItem(roof)

    left = Qt.MouseButton.LeftButton
    _send_mouse(win, QEvent.Type.MouseButtonPress, 120, 120, left, left)
    _send_mouse(win, QEvent.Type.MouseMove, 10, 10, Qt.MouseButton.NoButton, left)
    _send_mouse(win, QEvent.Type.MouseButtonRelease, 10, 10, left,
               Qt.MouseButton.NoButton)

    assert roof.marker_end == 0
    assert (roof.marker.pos().x(), roof.marker.pos().y()) == (0.0, 0.0)


# --------------------------------------------------------------------------
# "one dialog, two doors": marker right-click, and the ridge's own menu
# --------------------------------------------------------------------------
def test_marker_right_click_opens_the_end_on_dialog(fp, win, monkeypatch):
    win.prepare_headless()
    roof = RoofItem(QPointF(0, 0), QPointF(200, 0), ridge_h_in=132.0,
                    eaves_h_in=96.0, span_in=100.0)
    win.scene.addItem(roof)

    def _accept_and_edit(dlg_self):
        dlg_self.sp_ridge.setValue(160.0)
        return QDialog.DialogCode.Accepted
    monkeypatch.setattr(QDialog, "exec", _accept_and_edit)

    _right_click(win, 200, 0)   # the marker sits at the ridge's p2

    assert roof.ridge_h_in == pytest.approx(160.0)


def test_selecting_the_ridge_reaches_the_same_dialog(fp, win, monkeypatch):
    """0140-ruling.md sec1: "selecting any ridge still reaches the same
    dialog ... one dialog, two doors." Right-click the RIDGE LINE itself
    (away from the marker), pick "Roof heights..." from its own menu."""
    win.prepare_headless()
    roof = RoofItem(QPointF(0, 0), QPointF(200, 0), ridge_h_in=132.0,
                    eaves_h_in=96.0, span_in=100.0)
    win.scene.addItem(roof)

    def _pick_heights(self, *a, **k):
        return next(a for a in self.actions() if "heights" in a.text().lower())
    monkeypatch.setattr(QMenu, "exec", _pick_heights)

    def _accept_and_edit(dlg_self):
        dlg_self.sp_eaves.setValue(84.0)
        return QDialog.DialogCode.Accepted
    monkeypatch.setattr(QDialog, "exec", _accept_and_edit)

    _right_click(win, 100, 0)   # midpoint of the ridge, off the marker

    assert roof.eaves_h_in == pytest.approx(84.0)


def test_ridge_menu_delete_removes_the_roof_and_its_marker(fp, win, monkeypatch):
    win.prepare_headless()
    roof = RoofItem(QPointF(0, 0), QPointF(200, 0), span_in=100.0)
    win.scene.addItem(roof)

    def _pick_delete(self, *a, **k):
        return next(a for a in self.actions() if "delete" in a.text().lower())
    monkeypatch.setattr(QMenu, "exec", _pick_delete)

    _right_click(win, 100, 0)

    assert roof.scene() is None
    assert roof.marker.scene() is None


# --------------------------------------------------------------------------
# the three-way recompute -- Patrick's own worked examples, both rulings
# --------------------------------------------------------------------------
def _dialog_for(roof, parent=None):
    from floorplanner.dialogs import RoofEndOnDialog
    return RoofEndOnDialog(roof, parent)


def test_at_first_open_pitch_is_the_derived_field(fp, win):
    roof = RoofItem(QPointF(0, 0), QPointF(200, 0), ridge_h_in=132.0,
                    eaves_h_in=96.0, span_in=100.0)
    dlg = _dialog_for(roof)
    assert dlg._recent[0] == "pitch"
    expected = math.degrees(math.atan2(132.0 - 96.0, 100.0))
    assert dlg.sp_pitch.value() == pytest.approx(expected, abs=0.05)


def test_ridge_then_pitch_edited_derives_eaves(fp, win):
    """0140-ruling.md (End-On marker) sec3's own check: "set ridge+pitch
    and watch eaves derive." """
    roof = RoofItem(QPointF(0, 0), QPointF(200, 0), span_in=100.0)
    dlg = _dialog_for(roof)
    dlg.sp_ridge.setValue(150.0)
    dlg.sp_pitch.setValue(30.0)
    assert dlg._recent[0] == "eaves_h"
    expected = 150.0 - 100.0 * math.tan(math.radians(30.0))
    assert dlg.sp_eaves.value() == pytest.approx(expected, abs=0.05)


def test_ridge_then_height_then_pitch_edited_derives_ridge(fp, win):
    """0140-ruling.md (dialog sharpening) sec2's own worked example,
    literally: "Set R, set H => P (P never edited, oldest); set P => R
    (now oldest)." """
    roof = RoofItem(QPointF(0, 0), QPointF(200, 0), span_in=100.0)
    dlg = _dialog_for(roof)
    dlg.sp_ridge.setValue(140.0)
    dlg.sp_eaves.setValue(90.0)
    assert dlg._recent[0] == "pitch"
    expected_pitch = math.degrees(math.atan2(140.0 - 90.0, 100.0))
    assert dlg.sp_pitch.value() == pytest.approx(expected_pitch, abs=0.05)

    dlg.sp_pitch.setValue(20.0)
    assert dlg._recent[0] == "ridge_h"
    expected_ridge = 90.0 + 100.0 * math.tan(math.radians(20.0))
    assert dlg.sp_ridge.value() == pytest.approx(expected_ridge, abs=0.05)


def test_the_derived_fields_label_is_marked(fp, win):
    roof = RoofItem(QPointF(0, 0), QPointF(200, 0), span_in=100.0)
    dlg = _dialog_for(roof)
    assert "derived" in dlg.lab_pitch.text()
    assert "derived" not in dlg.lab_ridge.text()
    assert "derived" not in dlg.lab_eaves.text()

    dlg.sp_pitch.setValue(25.0)
    assert "derived" not in dlg.lab_pitch.text()
    assert "derived" in dlg.lab_ridge.text() or "derived" in dlg.lab_eaves.text()


def test_apply_writes_only_the_two_heights_pitch_never_stored(fp, win):
    roof = RoofItem(QPointF(0, 0), QPointF(200, 0), span_in=100.0)
    dlg = _dialog_for(roof)
    dlg.sp_ridge.setValue(150.0)
    dlg.sp_pitch.setValue(30.0)
    dlg.apply()
    assert roof.ridge_h_in == pytest.approx(150.0)
    assert roof.eaves_h_in == pytest.approx(
        150.0 - 100.0 * math.tan(math.radians(30.0)), abs=0.05)
    assert not hasattr(roof, "pitch_deg")
