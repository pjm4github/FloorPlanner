"""R4b -- the roof parameters dialog (0154-ruling.md sec3): per-side
overhang (requirement 1), heights/pitch via the End-On machinery, gable <->
hip per end, and the `room_top` eaves binding (requirement 5).

Patrick's own check for the tranche: "set an overhang, bind eaves to room
top, change the room height, watch the roof follow." The integration test
at the bottom is that sentence, literally, through the same context-menu
door a user takes -- and its control (an UNBOUND roof does not follow) is
what proves the binding, not a coincidence of defaults, moved it.

A hip end is new geometry (roofs.py's `hip_extension`), so it is measured
three ways here: the 2D footprint, which rooms the binding reads through
it, and R3b's own clip line (a wall beyond the ridge end that a gable roof
does not reach at all, a hip roof clips -- in closed form).
"""
import math

import pytest
from PyQt6.QtCore import QPoint, QPointF
from PyQt6.QtGui import QContextMenuEvent, QPainterPath
from PyQt6.QtWidgets import QApplication, QDialog, QMenu

from floorplanner.config import DEFAULT_FLOOR, DEFAULT_ROOM_PROPS
from floorplanner.design.validate import schema_errors
from floorplanner.roofs import (
    RoofItem, bound_eaves_height, roof_clip_spans, sync_bound_roofs,
)
from floorplanner.rooms import RoomItem
from floorplanner.walls import WallItem

pytestmark = pytest.mark.walls

SPAN, EAVES_H, RIDGE_H = 100.0, 96.0, 132.0
DEFAULT_CEILING = float(DEFAULT_ROOM_PROPS["ceiling_height_in"])


def _room(scene, x0, x1, ceiling_in, name="Room", floor=None):
    """A rectangular room x0..x1 by y 0..200 on `floor` with its own ceiling."""
    path = QPainterPath()
    path.addRect(x0, 0, x1 - x0, 200)
    room = RoomItem(name, QPointF((x0 + x1) / 2.0, 100), path, 100.0)
    room.floor = floor if floor is not None else DEFAULT_FLOOR
    room.properties["ceiling_height_in"] = ceiling_in
    scene.addItem(room)
    return room


def _roof(scene, **kw):
    """Ridge (50,100)-(250,100), span 100 each side -- the same shell every
    roof test in the suite uses."""
    kw.setdefault("span_in", SPAN)
    kw.setdefault("eaves_h_in", EAVES_H)
    kw.setdefault("ridge_h_in", RIDGE_H)
    rf = RoofItem(QPointF(50, 100), QPointF(250, 100), **kw)
    rf.floor = DEFAULT_FLOOR
    if scene is not None:
        scene.addItem(rf)
    return rf


def _dialog(roof, parent=None):
    from floorplanner.dialogs import RoofEndOnDialog
    return RoofEndOnDialog(roof, parent)


# --------------------------------------------------------------------------
# a hip end's geometry, in plan
# --------------------------------------------------------------------------
def test_a_hip_end_extends_the_footprint_past_the_ridge_end(scene):
    rf = _roof(scene, overhang_in=10.0, gable=[False, True])
    e1a, e1b, e2a, e2b = rf._eave_ends()
    # hip at p1: run (= the span, symmetric) + overhang, along -x
    assert e1a.x() == pytest.approx(50.0 - (SPAN + 10.0))
    assert e2a.x() == pytest.approx(50.0 - (SPAN + 10.0))
    # gable at p2: exactly the ridge end
    assert e1b.x() == pytest.approx(250.0)
    assert e2b.x() == pytest.approx(250.0)
    assert rf.boundingRect().left() < 50.0 - SPAN     # the bounds followed


def test_a_gable_roof_is_unchanged_by_the_hip_code_path(scene):
    """Positive control: two gable ends, nothing extends."""
    rf = _roof(scene, overhang_in=10.0)
    e1a, e1b, _, _ = rf._eave_ends()
    assert (e1a.x(), e1b.x()) == (pytest.approx(50.0), pytest.approx(250.0))
    assert rf.hip_extension(0) == (0.0, 0.0)
    assert rf.hip_extension(1) == (0.0, 0.0)


def test_the_hip_run_is_the_mean_of_the_two_spans(scene):
    rf = _roof(scene, span_in=[80.0, 120.0], overhang_in=[4.0, 8.0],
               gable=[False, False])
    assert rf.hip_extension(0) == (pytest.approx(100.0), pytest.approx(6.0))
    assert rf.hip_extension(1) == (pytest.approx(100.0), pytest.approx(6.0))


def test_the_eaves_start_polygon_extends_by_the_run_not_the_overhang(scene):
    rf = _roof(scene, overhang_in=10.0, gable=[False, False])
    br = rf.eaves_start_polygon().boundingRect()
    assert br.left() == pytest.approx(50.0 - SPAN)
    assert br.right() == pytest.approx(250.0 + SPAN)
    assert (br.top(), br.bottom()) == (pytest.approx(0.0), pytest.approx(200.0))
    # the preview override: the same roof asked "as if both ends were gable"
    br_g = rf.eaves_start_polygon(gable=[True, True]).boundingRect()
    assert (br_g.left(), br_g.right()) == (pytest.approx(50.0), pytest.approx(250.0))


def test_a_hip_ends_shape_covers_its_hip_lines(scene):
    """D85's own rule, extended: everything paint() draws is selectable.
    A hip line's midpoint (ridge end to the far eave corner) is inside the
    shape; the same point on a gable roof is empty air."""
    hip = _roof(scene, gable=[False, True])
    mid = QPointF((50.0 + (50.0 - SPAN)) / 2.0, (100.0 + 0.0) / 2.0)
    assert hip.shape().contains(mid)
    gable = RoofItem(QPointF(50, 400), QPointF(250, 400), span_in=SPAN)
    scene.addItem(gable)
    assert not gable.shape().contains(QPointF(mid.x(), mid.y() + 300.0))


# --------------------------------------------------------------------------
# the room-top binding: what it reads
# --------------------------------------------------------------------------
def test_binding_with_no_room_falls_back_to_the_default_and_says_so(scene):
    rf = _roof(scene)
    b = bound_eaves_height(scene, rf)
    assert b.fallback is True
    assert b.eaves_h_in == DEFAULT_CEILING
    assert b.rooms == []
    assert "No room" in b.note()


def test_binding_without_a_scene_is_the_no_room_case(scene):
    rf = _roof(None)
    b = bound_eaves_height(None, rf)
    assert b.fallback is True and b.eaves_h_in == DEFAULT_CEILING


def test_binding_reads_the_covered_rooms_ceiling(scene):
    _room(scene, 0, 300, 108.0, "Den")
    rf = _roof(scene)
    b = bound_eaves_height(scene, rf)
    assert b.fallback is False
    assert b.eaves_h_in == pytest.approx(108.0)
    assert b.rooms == [("Den", 108.0)]
    assert not b.differs()
    assert "Den" in b.note() and "differ" not in b.note()


def test_binding_ignores_a_room_outside_the_footprint(scene):
    """The control for the test above: a taller room that the roof does
    NOT cover must not be what governs."""
    _room(scene, 0, 300, 100.0, "Den")
    _room(scene, 400, 600, 130.0, "Barn")       # beyond the footprint entirely
    rf = _roof(scene)
    b = bound_eaves_height(scene, rf)
    assert b.eaves_h_in == pytest.approx(100.0)
    assert [n for n, _ in b.rooms] == ["Den"]


def test_binding_ignores_a_room_on_another_floor(scene):
    _room(scene, 0, 300, 130.0, "Upstairs", floor="Second")
    rf = _roof(scene)
    b = bound_eaves_height(scene, rf)
    assert b.fallback is True


def test_binding_highest_governs_and_the_mismatch_is_reported(scene):
    """0154-ruling.md sec2: "the highest governs, and the mismatch is
    warned, not hidden." """
    _room(scene, 0, 150, 96.0, "Den")
    _room(scene, 150, 300, 120.0, "Hall")
    rf = _roof(scene)
    b = bound_eaves_height(scene, rf)
    assert b.eaves_h_in == pytest.approx(120.0)
    assert b.rooms == [("Hall", 120.0), ("Den", 96.0)]   # highest first
    assert b.differs()
    assert "differ" in b.note() and "highest" in b.note()
    assert "Hall" in b.note() and "Den" in b.note()


def test_a_hip_end_extends_which_rooms_the_binding_reads(scene):
    """The binding reads the eaves-start footprint, and a hip end extends
    that footprint -- so a room sitting past the ridge end is covered by a
    hip roof and not by a gable roof of the same ridge."""
    _room(scene, 0, 250, 100.0, "Den")
    _room(scene, 250, 350, 130.0, "Porch")     # past p2, under a hip only
    gable = _roof(scene)
    assert bound_eaves_height(scene, gable).eaves_h_in == pytest.approx(100.0)
    hip = _roof(scene, gable=[True, False])
    assert bound_eaves_height(scene, hip).eaves_h_in == pytest.approx(130.0)


# --------------------------------------------------------------------------
# sync_bound_roofs: the hook a room edit calls
# --------------------------------------------------------------------------
def test_sync_moves_only_the_bound_roof(scene):
    room = _room(scene, 0, 300, 110.0)
    bound = _roof(scene, eaves_bind="room_top")
    manual = _roof(scene, eaves_bind="manual")
    assert bound.eaves_h_in == EAVES_H            # precondition: not yet synced

    touched = sync_bound_roofs(scene)
    assert [rf for rf, _ in touched] == [bound]
    assert bound.eaves_h_in == pytest.approx(110.0)
    assert manual.eaves_h_in == EAVES_H           # the control

    room.properties["ceiling_height_in"] = 120.0  # "change the room height"
    sync_bound_roofs(scene, floor=DEFAULT_FLOOR)
    assert bound.eaves_h_in == pytest.approx(120.0)
    assert manual.eaves_h_in == EAVES_H


def test_sync_is_scoped_to_the_floor_it_is_given(scene):
    _room(scene, 0, 300, 110.0)
    bound = _roof(scene, eaves_bind="room_top")
    assert sync_bound_roofs(scene, floor="Second") == []
    assert bound.eaves_h_in == EAVES_H


def test_sync_of_no_scene_is_a_no_op():
    assert sync_bound_roofs(None) == []


# --------------------------------------------------------------------------
# the dialog: overhang, ends, binding
# --------------------------------------------------------------------------
def test_overhang_edits_mirror_while_same_both_sides_is_on(fp, win):
    rf = _roof(win.scene, overhang_in=0.0)
    dlg = _dialog(rf)
    assert dlg.ck_oh_same.isChecked()             # both sides agree at open
    dlg.sp_oh_l.setValue(12.0)
    assert dlg.sp_oh_r.value() == pytest.approx(12.0)
    dlg.ck_oh_same.setChecked(False)
    dlg.sp_oh_l.setValue(18.0)
    assert dlg.sp_oh_r.value() == pytest.approx(12.0)   # no longer mirrored
    dlg.apply()
    assert rf.overhang_in == pytest.approx([18.0, 12.0])
    e1a, _, e2a, _ = rf._eave_ends()
    assert e1a.y() == pytest.approx(100.0 + SPAN + 18.0)   # left = +normal
    assert e2a.y() == pytest.approx(100.0 - SPAN - 12.0)


def test_same_both_sides_starts_off_for_an_asymmetric_overhang(fp, win):
    rf = _roof(win.scene, overhang_in=[6.0, 10.0])
    dlg = _dialog(rf)
    assert not dlg.ck_oh_same.isChecked()
    assert (dlg.sp_oh_l.value(), dlg.sp_oh_r.value()) == (6.0, 10.0)
    dlg.ck_oh_same.setChecked(True)               # re-linking copies left -> right
    assert dlg.sp_oh_r.value() == pytest.approx(6.0)


def test_the_end_combos_map_through_the_marker_end(fp, win):
    """The two ends are named by the marker, the one physical way a user
    tells them apart -- so the same combo writes `gable[0]` or `gable[1]`
    depending on where the marker sits at open time."""
    at_p2 = _roof(win.scene, marker_end=1)
    dlg = _dialog(at_p2)
    dlg.cb_end_marker.setCurrentIndex(1)          # "Hip"
    dlg.apply()
    assert at_p2.gable == [True, False]

    at_p1 = _roof(win.scene, marker_end=0)
    dlg = _dialog(at_p1)
    dlg.cb_end_marker.setCurrentIndex(1)
    dlg.cb_end_other.setCurrentIndex(0)
    dlg.apply()
    assert at_p1.gable == [False, True]


def test_the_combos_open_showing_the_stored_flags(fp, win):
    rf = _roof(win.scene, gable=[False, True], marker_end=1)
    dlg = _dialog(rf)
    assert dlg.cb_end_marker.currentText() == "Gable"    # marker at p2, gable[1]
    assert dlg.cb_end_other.currentText() == "Hip"       # p1, gable[0]


def test_binding_locks_the_eaves_field_and_reads_the_rooms(fp, win):
    _room(win.scene, 0, 300, 108.0, "Den")
    rf = _roof(win.scene)
    dlg = _dialog(rf)
    assert dlg.binding is None and dlg.sp_eaves.isEnabled()
    dlg.ck_bind.setChecked(True)
    assert dlg.binding is not None
    assert not dlg.sp_eaves.isEnabled()
    assert dlg.sp_eaves.value() == pytest.approx(108.0)
    assert "bound" in dlg.lab_eaves.text()
    assert "Den" in dlg.lab_bind.text()
    # pitch re-derived from the bound eaves and the untouched ridge
    want = math.degrees(math.atan2(RIDGE_H - 108.0, SPAN))
    assert dlg.sp_pitch.value() == pytest.approx(want, abs=0.05)
    dlg.apply()
    assert rf.eaves_bind == "room_top"
    assert rf.eaves_h_in == pytest.approx(108.0)  # written, not just derived


def test_while_bound_a_pitch_edit_derives_the_ridge_never_the_eaves(fp, win):
    _room(win.scene, 0, 300, 108.0)
    rf = _roof(win.scene)
    dlg = _dialog(rf)
    dlg.ck_bind.setChecked(True)
    dlg.sp_pitch.setValue(30.0)
    assert dlg._derived() == "ridge_h"
    assert dlg.sp_eaves.value() == pytest.approx(108.0)
    assert dlg.sp_ridge.value() == pytest.approx(
        108.0 + SPAN * math.tan(math.radians(30.0)), abs=0.05)
    dlg.sp_ridge.setValue(150.0)                  # now pitch is the derived one
    assert dlg._derived() == "pitch"
    assert dlg.sp_eaves.value() == pytest.approx(108.0)


def test_unbinding_frees_the_eaves_field_again(fp, win):
    _room(win.scene, 0, 300, 108.0)
    rf = _roof(win.scene, eaves_bind="room_top")
    dlg = _dialog(rf)
    assert dlg.ck_bind.isChecked() and not dlg.sp_eaves.isEnabled()
    assert dlg.sp_eaves.value() == pytest.approx(108.0)   # seeded at open
    dlg.ck_bind.setChecked(False)
    assert dlg.binding is None and dlg.sp_eaves.isEnabled()
    assert "bound" not in dlg.lab_eaves.text()
    dlg.apply()
    assert rf.eaves_bind == "manual"


def test_toggling_a_hip_end_re_measures_the_binding(fp, win):
    _room(win.scene, 0, 250, 100.0, "Den")
    _room(win.scene, 250, 350, 130.0, "Porch")
    rf = _roof(win.scene, marker_end=1)           # marker at p2, next to Porch
    dlg = _dialog(rf)
    dlg.ck_bind.setChecked(True)
    assert dlg.sp_eaves.value() == pytest.approx(100.0)
    dlg.cb_end_marker.setCurrentIndex(1)          # p2 becomes a hip
    assert dlg.sp_eaves.value() == pytest.approx(130.0)
    assert "Porch" in dlg.lab_bind.text()
    dlg.apply()
    assert rf.gable == [True, False] and rf.eaves_h_in == pytest.approx(130.0)


def test_the_no_room_fallback_is_shown_not_hidden(fp, win):
    rf = _roof(win.scene)
    dlg = _dialog(rf)
    dlg.ck_bind.setChecked(True)
    assert "No room" in dlg.lab_bind.text()
    assert dlg.sp_eaves.value() == DEFAULT_CEILING


def test_the_drawing_shows_both_pitches_only_when_the_spans_differ(fp, win):
    even = _dialog(_roof(win.scene))
    assert even.canvas.pitch_deg(0) == pytest.approx(even.canvas.pitch_deg(1))
    odd = _dialog(_roof(win.scene, span_in=[80.0, 120.0]))
    assert odd.canvas.span_in == 80.0             # the recompute's reference
    assert odd.canvas.pitch_deg(0) > odd.canvas.pitch_deg(1)


# --------------------------------------------------------------------------
# the document: hip flags, per-side overhang and the binding round-trip
# --------------------------------------------------------------------------
@pytest.mark.io
def test_hip_overhang_and_binding_round_trip_through_the_document(fp, win):
    from floorplanner.design.bridge import apply_design_to_scene, design_from_scene
    _room(win.scene, 0, 300, 108.0)
    rf = _roof(win.scene, overhang_in=[6.0, 10.0], gable=[False, True],
               eaves_bind="room_top")
    sync_bound_roofs(win.scene)
    before = [(p.x(), p.y()) for p in rf._eave_ends()]
    doc = design_from_scene(win).to_dict()
    assert schema_errors(doc) == []
    rd = doc["roofs"][0]
    assert rd["gable"] == [False, True]
    assert rd["overhang_in"] == [6.0, 10.0]
    assert rd["eaves_bind"] == "room_top"
    assert rd["eaves_h_in"] == pytest.approx(108.0)     # self-contained

    apply_design_to_scene(win, doc)
    back = next(it for it in win.scene.items() if isinstance(it, RoofItem))
    assert back.gable == [False, True]
    assert back.overhang_in == [6.0, 10.0]
    assert back.eaves_bind == "room_top"
    assert back.eaves_h_in == pytest.approx(108.0)
    after = [(p.x(), p.y()) for p in back._eave_ends()]
    assert after == pytest.approx(before)


# --------------------------------------------------------------------------
# R3b's clip line under a hip end
# --------------------------------------------------------------------------
def test_a_hip_end_clips_a_wall_beyond_the_ridge_end_in_closed_form(scene):
    """A wall running out along the ridge axis past p1, under the eaves
    line (perp = 0, so the SIDE planes never clip it). Gable: the wall is
    outside the footprint, nothing. Hip: the hip plane drops from RIDGE_H
    at p1 at `(RIDGE_H - EAVES_H) / run` per inch, so it is below the
    ceiling once `beyond > (RIDGE_H - CEILING) / slope`, and the footprint
    ends `run` past p1 -- both boundaries exact."""
    ceiling = 96.0
    _room(scene, 0, 300, ceiling)
    wall = WallItem(QPointF(-100, 100), QPointF(50, 100), "exterior")
    wall.floor = DEFAULT_FLOOR
    scene.addItem(wall)

    eaves_h = 80.0
    gable = _roof(scene, eaves_h_in=eaves_h)
    assert roof_clip_spans(scene, wall) == []     # precondition: gable = nothing
    scene.removeItem(gable)

    _roof(scene, eaves_h_in=eaves_h, gable=[False, True])
    slope_hip = (RIDGE_H - eaves_h) / SPAN        # run == span (symmetric)
    thresh = (RIDGE_H - ceiling) / slope_hip      # inches beyond p1
    # wall s runs from x=-100 (s=0) to x=50 (s=150); beyond = 50 - x
    s_lo = 150.0 - SPAN                            # footprint end, x = -50
    s_hi = 150.0 - thresh                          # x = 50 - thresh
    spans = roof_clip_spans(scene, wall)
    assert len(spans) == 1
    assert spans[0] == (pytest.approx(s_lo, abs=1e-6), pytest.approx(s_hi, abs=1e-6))


def test_a_hip_end_does_not_change_the_side_planes_own_clip(scene):
    """The control: the R3b gable-end-wall case (test_roof_clip.py's
    headline) gives the same spans whether that end is a gable or a hip --
    the wall sits AT along == 0, where the hip plane is still at ridge
    height and adds nothing."""
    _room(scene, 0, 300, 96.0)
    wall = WallItem(QPointF(50, 0), QPointF(50, 200), "exterior")
    wall.floor = DEFAULT_FLOOR
    scene.addItem(wall)
    g = _roof(scene, eaves_h_in=80.0)
    with_gable = roof_clip_spans(scene, wall)
    scene.removeItem(g)
    _roof(scene, eaves_h_in=80.0, gable=[False, True])
    assert with_gable and roof_clip_spans(scene, wall) == pytest.approx(with_gable)


# --------------------------------------------------------------------------
# Patrick's own check, end to end: change the room height, watch the roof
# follow -- through the room's own Properties door
# --------------------------------------------------------------------------
def _right_click(win, sx, sy):
    vp = win.view.viewport()
    p = win.view.mapFromScene(QPointF(sx, sy))
    QApplication.sendEvent(vp, QContextMenuEvent(
        QContextMenuEvent.Reason.Mouse, QPoint(p), vp.mapToGlobal(QPoint(p))))
    QApplication.processEvents()


@pytest.mark.gui
def test_editing_a_rooms_height_moves_the_bound_roof_and_not_the_other(
        fp, win, monkeypatch):
    win.prepare_headless()
    macro = ("WALL 0 0 300 0 ext WALL 300 0 300 200 ext "
             "WALL 300 200 0 200 ext WALL 0 200 0 0 ext "
             "ROOM Den 150 100")
    res = win.run_macro(macro)
    assert res["ok"], res["errors"]
    room = next(it for it in win.scene.items() if isinstance(it, RoomItem))
    room.raise_to_front()
    bound = _roof(win.scene, eaves_bind="room_top")
    manual = _roof(win.scene, eaves_bind="manual")
    sync_bound_roofs(win.scene)
    assert bound.eaves_h_in == pytest.approx(DEFAULT_CEILING)   # 96 today

    def _pick_props(self, *a, **k):
        return next(a for a in self.actions() if "properties" in a.text().lower())
    monkeypatch.setattr(QMenu, "exec", _pick_props)

    def _set_ceiling(dlg_self):
        dlg_self.sp_ceiling.setValue(120.0)
        return QDialog.DialogCode.Accepted
    monkeypatch.setattr(QDialog, "exec", _set_ceiling)

    _right_click(win, 150, 100)                   # the room's own label
    assert room.properties["ceiling_height_in"] == pytest.approx(120.0)
    assert bound.eaves_h_in == pytest.approx(120.0), "the bound roof followed"
    assert manual.eaves_h_in == EAVES_H, "the unbound roof did not"
    assert "120" in win.statusBar().currentMessage()


# --------------------------------------------------------------------------
# Patrick's check outcome: the eaves pick measures EACH side to its own wall,
# the dialog exposes the two spans, and "overhang 24in" reads as two 12in
# grid lines past each wall in the plan
# --------------------------------------------------------------------------
def _shell_walls(fp, win, y_top, y_bottom):
    top = fp.WallItem(QPointF(0, y_top), QPointF(200, y_top), "exterior")
    bot = fp.WallItem(QPointF(0, y_bottom), QPointF(200, y_bottom), "exterior")
    win.scene.addItem(top)
    win.scene.addItem(bot)
    return top, bot


def _accept(monkeypatch):
    monkeypatch.setattr(QDialog, "exec", lambda self: QDialog.DialogCode.Accepted)


def test_the_eaves_pick_measures_each_side_to_its_own_wall(fp, win, monkeypatch):
    """Ridge at y=100 between walls at y=0 and y=220 -- 20in off-centre,
    the shape of Patrick's own sketch. The picked (y=0) wall sets its side
    at 100; the far side is measured to ITS wall, 120, not mirrored.
    Ridge direction +x: LEFT (index 0) is the +y side."""
    win.prepare_headless()
    top, bot = _shell_walls(fp, win, 0.0, 220.0)
    _accept(monkeypatch)
    item = RoofItem(QPointF(0, 100), QPointF(200, 100))
    win.scene.addItem(item)
    assert win.finish_roof_ridge(item, top) is item
    assert item.span_in == pytest.approx([120.0, 100.0])


def test_picking_the_far_wall_gives_the_same_footprint(fp, win, monkeypatch):
    """Which of the two walls is clicked must not matter to the result."""
    win.prepare_headless()
    top, bot = _shell_walls(fp, win, 0.0, 220.0)
    _accept(monkeypatch)
    item = RoofItem(QPointF(0, 100), QPointF(200, 100))
    win.scene.addItem(item)
    win.finish_roof_ridge(item, bot)
    assert item.span_in == pytest.approx([120.0, 100.0])


def test_a_single_wall_still_mirrors_to_the_far_side(fp, win, monkeypatch):
    """The control, and the pre-R4b behaviour preserved: with nothing
    across the ridge, the far side takes the picked side's span."""
    win.prepare_headless()
    wall = fp.WallItem(QPointF(0, 0), QPointF(200, 0), "exterior")
    win.scene.addItem(wall)
    _accept(monkeypatch)
    item = RoofItem(QPointF(0, 100), QPointF(200, 100))
    win.scene.addItem(item)
    win.finish_roof_ridge(item, wall)
    assert item.span_in == pytest.approx([100.0, 100.0])


def test_a_perpendicular_wall_is_not_an_eaves_wall_for_either_side(
        fp, win, monkeypatch):
    """A gable-end wall (perpendicular to the ridge) fails the parallel
    rule exactly as it always did -- it must not be mistaken for the far
    side's eaves."""
    win.prepare_headless()
    wall = fp.WallItem(QPointF(0, 0), QPointF(200, 0), "exterior")
    end = fp.WallItem(QPointF(200, 0), QPointF(200, 300), "exterior")
    win.scene.addItem(wall)
    win.scene.addItem(end)
    _accept(monkeypatch)
    item = RoofItem(QPointF(0, 100), QPointF(200, 100))
    win.scene.addItem(item)
    win.finish_roof_ridge(item, wall)
    assert item.span_in == pytest.approx([100.0, 100.0])


def test_the_cancel_auto_complete_measures_per_side_too(fp, win):
    """The second pick path (view.py `cancel_temp`, the Esc path: a ridge
    awaiting its eaves is KEPT and picked for, per Patrick's own
    "disappearingroof" report) uses the same per-side measurement, with
    no picked wall at all."""
    win.prepare_headless()
    _shell_walls(fp, win, 0.0, 220.0)
    item = RoofItem(QPointF(0, 100), QPointF(200, 100))
    win.scene.addItem(item)
    win.view._roof_awaiting_eaves = item
    win.view.cancel_temp()
    assert win.view._roof_awaiting_eaves is None
    assert item.scene() is win.scene
    assert item.span_in == pytest.approx([120.0, 100.0])


def test_overhang_lands_two_grid_lines_past_each_wall(fp, win, monkeypatch):
    """Patrick's own acceptance, in his words: "if the overhang says 24
    inches then [the eave] will be 2 grid lines" past the wall -- on BOTH
    sides, with the ridge off-centre. GRID_MINOR is the 12in grid."""
    from floorplanner.config import GRID_MINOR
    assert GRID_MINOR == 12.0
    win.prepare_headless()
    top, bot = _shell_walls(fp, win, 0.0, 240.0)     # both on the grid
    _accept(monkeypatch)
    item = RoofItem(QPointF(0, 108), QPointF(200, 108))   # 12in off-centre
    win.scene.addItem(item)
    win.finish_roof_ridge(item, top)
    dlg = _dialog(item)
    dlg.sp_oh_l.setValue(24.0)                       # linked: both sides
    assert dlg.sp_oh_r.value() == 24.0
    dlg.apply()
    e1a, _, e2a, _ = item._eave_ends()
    assert e1a.y() == pytest.approx(240.0 + 2 * GRID_MINOR)   # +y wall, 2 lines out
    assert e2a.y() == pytest.approx(0.0 - 2 * GRID_MINOR)     # -y wall, 2 lines out


def test_the_dialog_shows_and_writes_both_spans(fp, win):
    rf = _roof(win.scene, span_in=[100.0, 100.0])
    dlg = _dialog(rf)
    assert (dlg.sp_span_l.value(), dlg.sp_span_r.value()) == (100.0, 100.0)
    dlg.sp_span_r.setValue(130.0)                    # the lopsided roof, fixed
    dlg.apply()
    assert rf.span_in == pytest.approx([100.0, 130.0])
    _, _, e2a, _ = rf._eave_ends()
    assert e2a.y() == pytest.approx(100.0 - 130.0)


def test_a_left_span_edit_rederives_the_pitch(fp, win):
    rf = _roof(win.scene)
    dlg = _dialog(rf)
    dlg.sp_span_l.setValue(50.0)
    assert dlg._derived() == "pitch"
    want = math.degrees(math.atan2(RIDGE_H - EAVES_H, 50.0))
    assert dlg.sp_pitch.value() == pytest.approx(want, abs=0.05)
    assert dlg.canvas.span_in == 50.0


def test_a_span_edit_re_measures_the_binding(fp, win):
    """A room sitting past the current eaves line (y 200..300) is not
    covered until the left span reaches it."""
    _room(win.scene, 0, 300, 100.0, "Den")
    path = QPainterPath()
    path.addRect(0, 200, 300, 100)
    far = RoomItem("Attic", QPointF(150, 250), path, 100.0)
    far.floor = DEFAULT_FLOOR
    far.properties["ceiling_height_in"] = 130.0
    win.scene.addItem(far)
    rf = _roof(win.scene)
    dlg = _dialog(rf)
    dlg.ck_bind.setChecked(True)
    assert dlg.sp_eaves.value() == pytest.approx(100.0)
    dlg.sp_span_l.setValue(150.0)                    # +y side now reaches Attic
    assert dlg.sp_eaves.value() == pytest.approx(130.0)
    assert "Attic" in dlg.lab_bind.text()


# --------------------------------------------------------------------------
# Patrick's second note: on an angled roof the overhang must be orthogonal
# to the wall it overhangs -- 24in from a 45deg wall reads as 24in
# --------------------------------------------------------------------------
def _perp_distance(pt, a, b):
    """Distance from `pt` to the infinite line a-b."""
    dx, dy = b.x() - a.x(), b.y() - a.y()
    return abs((pt.x() - a.x()) * dy - (pt.y() - a.y()) * dx) / math.hypot(dx, dy)


def test_a_45_degree_wing_overhang_is_24in_from_its_wall(fp, win, monkeypatch):
    """A 45deg wing: eaves walls parallel to the ridge at 100in either
    side, and the ridge deliberately SHORT and shifted along the axis, so
    each wall's midpoint projects PAST a ridge end -- the case the old
    segment-distance pick inflated (its control test is below). Both eave lines must sit
    exactly span + 24in from the ridge, i.e. 24in from each wall,
    measured along the wall's own normal."""
    win.prepare_headless()
    s = math.sqrt(0.5)
    # walls along the (1, 1) direction, offset +-100 along the normal (-1, 1)*s
    n = QPointF(-s, s)
    a, b = QPointF(0, 0), QPointF(400, 400)
    top = fp.WallItem(a + n * 100.0, b + n * 100.0, "exterior")
    bot = fp.WallItem(a - n * 100.0, b - n * 100.0, "exterior")
    win.scene.addItem(top)
    win.scene.addItem(bot)
    _accept(monkeypatch)
    ridge = RoofItem(QPointF(250, 250), QPointF(350, 350))    # short, shifted
    win.scene.addItem(ridge)
    win.finish_roof_ridge(ridge, top)
    assert ridge.span_in == pytest.approx([100.0, 100.0], abs=1e-6)
    ridge.overhang_in = 24.0
    ridge.rebuild()
    e1a, e1b, e2a, e2b = ridge._eave_ends()
    for pt in (e1a, e1b):
        assert _perp_distance(pt, top.p1, top.p2) == pytest.approx(24.0, abs=1e-6)
    for pt in (e2a, e2b):
        assert _perp_distance(pt, bot.p1, bot.p2) == pytest.approx(24.0, abs=1e-6)


def test_the_old_segment_pick_would_have_inflated_that_span(fp, win):
    """The positive control for the test above: the SEGMENT distance the
    pre-R4b pick used gives more than 100 for the same wall and ridge,
    which is the inflation Patrick saw; the LINE distance gives 100."""
    from floorplanner.roofs import eaves_span_from_wall, eaves_span_to_ridge_line
    s = math.sqrt(0.5)
    n = QPointF(-s, s)
    top = fp.WallItem(QPointF(0, 0) + n * 100.0, QPointF(400, 400) + n * 100.0,
                      "exterior")
    p1, p2 = QPointF(250, 250), QPointF(350, 350)
    assert eaves_span_from_wall(p1, p2, top) == pytest.approx(
        math.hypot(100.0, 70.7106781), abs=1e-4)          # the hypotenuse
    assert eaves_span_to_ridge_line(p1, p2, top) == pytest.approx(100.0, abs=1e-6)
