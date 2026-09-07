"""R4c -- direct manipulation of a roof (0154-ruling.md sec3): a selected
roof grows five grips -- two eave edges, two gable ends, the ridge.

The binding receipts, each its own test: an eave-edge drag edits THAT
side's `span_in` and nothing else, the overhang riding along (0160-ruling.md
sec2: the grips drag exactly the two values the dialog edits -- no second
span convention); a gable-end drag moves that ridge endpoint along the
axis; the ridge drag slides it laterally between FIXED eave edges,
rebalancing the spans (0140-ruling.md sec4's deferral, due here); every
drag LANDS ON the grid rather than moving by it (0070-ruling.md sec3's
class -- tested with an off-grid start, the one case that tells the two
apart); and the settled gesture is one undo step.
"""
import math

import pytest
from PyQt6.QtCore import QEvent, QPointF, Qt
from PyQt6.QtGui import QMouseEvent
from PyQt6.QtWidgets import QApplication

from floorplanner.config import DEFAULT_FLOOR, SETTINGS
from floorplanner.roofs import (
    GRIP_END_OFFSET_IN, MIN_RIDGE_LEN_IN, RoofGripItem, RoofItem,
)

pytestmark = pytest.mark.walls

SPAN, OH = 100.0, 12.0


def _roof(scene, **kw):
    """Ridge (50,100)-(250,100); +y is the LEFT side (index 0)."""
    kw.setdefault("span_in", SPAN)
    kw.setdefault("overhang_in", OH)
    rf = RoofItem(QPointF(50, 100), QPointF(250, 100), **kw)
    rf.floor = DEFAULT_FLOOR
    scene.addItem(rf)
    return rf


def _grip(rf, kind):
    return next(g for g in rf.grips if g.kind == kind)


def _step():
    return float(SETTINGS["wall_snap_in"])


def _on_grid(v):
    return abs(v / _step() - round(v / _step())) < 1e-9


def _eaves(rf):
    return [(round(p.x(), 9), round(p.y(), 9)) for p in rf._eave_ends()]


# --------------------------------------------------------------------------
# the grips themselves
# --------------------------------------------------------------------------
def test_five_grips_hidden_until_the_roof_is_selected(scene):
    rf = _roof(scene)
    assert [g.kind for g in rf.grips] == list(RoofGripItem.KINDS)
    assert not any(g.isVisible() for g in rf.grips)
    rf.setSelected(True)
    assert all(g.isVisible() for g in rf.grips)
    rf.setSelected(False)
    assert not any(g.isVisible() for g in rf.grips)


def test_grips_sit_at_the_midpoints_of_the_lines_they_drag(scene):
    rf = _roof(scene)
    pos = {g.kind: (g.pos().x(), g.pos().y()) for g in rf.grips}
    assert pos["eave_l"] == (pytest.approx(150.0), pytest.approx(100.0 + SPAN + OH))
    assert pos["eave_r"] == (pytest.approx(150.0), pytest.approx(100.0 - SPAN - OH))
    assert pos["end_0"] == (pytest.approx(50.0 - GRIP_END_OFFSET_IN), pytest.approx(100.0))
    assert pos["end_1"] == (pytest.approx(250.0 + GRIP_END_OFFSET_IN), pytest.approx(100.0))
    assert pos["ridge"] == (pytest.approx(150.0), pytest.approx(100.0))


def test_grips_follow_a_rebuild(scene):
    rf = _roof(scene)
    rf.span_in = [140.0, 100.0]
    rf.rebuild()
    assert _grip(rf, "eave_l").pos().y() == pytest.approx(100.0 + 140.0 + OH)


def test_a_grip_has_no_hit_shape_while_roofs_are_not_editable(scene):
    rf = _roof(scene)
    rf.setSelected(True)
    g = _grip(rf, "ridge")
    assert not g.shape().isEmpty()
    SETTINGS["edit_roofs"] = False
    try:
        assert g.shape().isEmpty()
    finally:
        SETTINGS["edit_roofs"] = True


# --------------------------------------------------------------------------
# eave-edge drag: that side's span, overhang riding along
# --------------------------------------------------------------------------
def test_eave_drag_edits_that_sides_span_only(scene):
    rf = _roof(scene)
    rf.drag_eave(0, QPointF(150.0, 245.3))
    e1a, _, e2a, _ = rf._eave_ends()
    assert _on_grid(e1a.y()) and e1a.y() == pytest.approx(246.0)   # landed
    assert rf.span_in == pytest.approx([246.0 - 100.0 - OH, SPAN])
    assert rf.overhang_in == [OH, OH]                                # rode along
    assert e2a.y() == pytest.approx(100.0 - SPAN - OH)               # other side untouched
    assert (rf.p1.x(), rf.p1.y(), rf.p2.x(), rf.p2.y()) == (50, 100, 250, 100)


def test_eave_drag_on_the_right_side(scene):
    rf = _roof(scene)
    rf.drag_eave(1, QPointF(150.0, -40.2))
    _, _, e2a, _ = rf._eave_ends()
    assert e2a.y() == pytest.approx(-42.0)
    assert rf.span_in == pytest.approx([SPAN, 142.0 - OH])


def test_eave_drag_lands_on_the_grid_it_does_not_move_by_it(scene):
    """0070-ruling.md sec3's class: start OFF grid (span 100.37, outer eave
    at 212.37) and drag +17.73. A displacement snap (+18) would land at
    230.37 -- the offset carried forever; a destination snap lands on 228
    or 234, a grid line, and the offset is gone."""
    rf = _roof(scene, span_in=100.37)
    before = rf._eave_ends()[0].y()
    assert not _on_grid(before), "precondition: the roof starts off grid"
    rf.drag_eave(0, QPointF(150.0, before + 17.73))
    after = rf._eave_ends()[0].y()
    assert _on_grid(after)
    assert after != pytest.approx(before + 18.0)


def test_eave_drag_cannot_cross_the_ridge(scene):
    rf = _roof(scene)
    rf.drag_eave(0, QPointF(150.0, 100.0))       # onto the ridge itself
    assert rf.span_in[0] == 1.0
    rf.drag_eave(0, QPointF(150.0, -300.0))      # far past it
    assert rf.span_in[0] == 1.0


# --------------------------------------------------------------------------
# gable-end drag: that endpoint, along the axis
# --------------------------------------------------------------------------
def test_end_drag_moves_that_endpoint_along_the_ridge(scene):
    rf = _roof(scene)
    # cursor off-axis (only along counts); the grip sits 18in outside the
    # end line, so the LINE reads 18in inward: 313.4 - 18 -> snapped 294
    rf.drag_end(1, QPointF(313.4, 140.0))
    assert (rf.p2.x(), rf.p2.y()) == (pytest.approx(294.0), pytest.approx(100.0))
    assert (rf.p1.x(), rf.p1.y()) == (50.0, 100.0)
    assert rf.span_in == pytest.approx([SPAN, SPAN])
    rf.drag_end(0, QPointF(20.6, 100.0))          # 20.6 + 18 -> snapped 36
    assert (rf.p1.x(), rf.p1.y()) == (pytest.approx(36.0), pytest.approx(100.0))


def test_end_drag_keeps_a_minimum_ridge(scene):
    rf = _roof(scene)
    rf.drag_end(1, QPointF(40.0, 100.0))         # past p1
    assert rf.length() == pytest.approx(MIN_RIDGE_LEN_IN)
    assert rf.p2.x() > rf.p1.x()                 # direction preserved


def test_end_drag_on_a_hip_end_moves_the_outer_eave_to_the_cursor(scene):
    """The grip sits on the hip end's outer eave line, ext = run + overhang
    past the ridge end; that LINE lands on the cursor, and the ridge end
    follows ext behind it."""
    rf = _roof(scene, gable=[True, False])
    run, oh = rf.hip_extension(1)
    assert (run, oh) == (SPAN, OH)
    rf.drag_end(1, QPointF(400.0, 100.0))        # 400 - 18 = 382, off the 6in grid
    _, e1b, _, _ = rf._eave_ends()
    assert e1b.x() == pytest.approx(384.0)        # the outer eave LANDED
    assert rf.p2.x() == pytest.approx(384.0 - (run + oh))


# --------------------------------------------------------------------------
# ridge drag: sideways between fixed eaves
# --------------------------------------------------------------------------
def test_ridge_drag_slides_between_fixed_eave_edges(scene):
    rf = _roof(scene)
    before = _eaves(rf)
    rf.drag_ridge(QPointF(150.0, 130.4))
    assert (rf.p1.y(), rf.p2.y()) == (pytest.approx(132.0), pytest.approx(132.0))
    assert (rf.p1.x(), rf.p2.x()) == (50.0, 250.0)
    assert rf.span_in == pytest.approx([SPAN - 32.0, SPAN + 32.0])
    assert _eaves(rf) == before, "the eave edges did not move"


def test_ridge_drag_is_clamped_so_no_span_vanishes(scene):
    rf = _roof(scene)
    before = _eaves(rf)
    rf.drag_ridge(QPointF(150.0, 900.0))
    assert rf.span_in[0] == pytest.approx(1.0)
    assert rf.span_in[1] == pytest.approx(2 * SPAN - 1.0)
    assert _eaves(rf) == before


def test_ridge_drag_rebalances_pitch_the_way_the_dialog_reads_it(scene):
    """The spans the grips write are the ones the dialog shows -- one
    convention (0160-ruling.md sec2)."""
    from floorplanner.dialogs import RoofEndOnDialog
    rf = _roof(scene)
    rf.drag_ridge(QPointF(150.0, 130.4))
    dlg = RoofEndOnDialog(rf)
    assert (dlg.sp_span_l.value(), dlg.sp_span_r.value()) == (
        pytest.approx(SPAN - 32.0), pytest.approx(SPAN + 32.0))


# --------------------------------------------------------------------------
# the 45deg wing
# --------------------------------------------------------------------------
def test_45_degree_eave_drag_lands_on_the_roofs_own_grid(scene):
    """A diagonal line cannot sit on a square grid; the rule is the same
    one in the roof's frame -- the eave line's coordinate along the
    ridge's normal, from the origin, is a multiple of the step -- and the
    line stays parallel to the ridge."""
    rf = RoofItem(QPointF(0, 0), QPointF(200, 200), span_in=50.0, overhang_in=0.0)
    scene.addItem(rf)
    s = math.sqrt(0.5)
    nx, ny = -s, s
    rf.drag_eave(0, QPointF(100.0 - 80.0 * s + 3.1, 100.0 + 80.0 * s + 2.2))
    e1a, e1b, _, _ = rf._eave_ends()
    coord = e1a.x() * nx + e1a.y() * ny
    assert _on_grid(coord)
    assert abs((e1b.x() - e1a.x()) - (e1b.y() - e1a.y())) < 1e-6   # parallel
    assert (rf.p1.x(), rf.p1.y(), rf.p2.x(), rf.p2.y()) == (0, 0, 200, 200)


def test_45_degree_end_drag_stays_on_the_ridge_line(scene):
    rf = RoofItem(QPointF(0, 0), QPointF(200, 200), span_in=50.0, overhang_in=0.0)
    scene.addItem(rf)
    rf.drag_end(1, QPointF(260.0, 230.0))        # off the line: along only
    assert rf.p2.x() == pytest.approx(rf.p2.y())
    s = math.sqrt(0.5)
    assert _on_grid(rf.p2.x() * s + rf.p2.y() * s)


# --------------------------------------------------------------------------
# undo: the settled gesture is one step
# --------------------------------------------------------------------------
@pytest.mark.io
def test_a_grip_drag_is_one_undo_step(fp, win):
    rf = _roof(win.scene)
    win._commit_if_changed()
    rf.drag_eave(0, QPointF(150.0, 245.3))
    rf.drag_eave(0, QPointF(150.0, 264.0))       # mid-gesture moves...
    win._commit_if_changed()                      # ...settle as one step
    roofs = [it for it in win.scene.items() if isinstance(it, RoofItem)]
    assert roofs[0].span_in[0] == pytest.approx(264.0 - 100.0 - OH)
    win.undo()
    roofs = [it for it in win.scene.items() if isinstance(it, RoofItem)]
    assert len(roofs) == 1
    assert roofs[0].span_in == pytest.approx([SPAN, SPAN])
    win.redo()
    roofs = [it for it in win.scene.items() if isinstance(it, RoofItem)]
    assert roofs[0].span_in[0] == pytest.approx(264.0 - 100.0 - OH)


# --------------------------------------------------------------------------
# through the mouse
# --------------------------------------------------------------------------
def _send_mouse(win, etype, sx, sy, button, buttons):
    vp = win.view.viewport()
    pos = win.view.mapFromScene(QPointF(sx, sy))
    ev = QMouseEvent(etype, QPointF(pos), QPointF(vp.mapToGlobal(pos)),
                     button, buttons, Qt.KeyboardModifier.NoModifier)
    QApplication.sendEvent(vp, ev)


def _drag(win, a, b):
    left = Qt.MouseButton.LeftButton
    _send_mouse(win, QEvent.Type.MouseButtonPress, *a, left, left)
    _send_mouse(win, QEvent.Type.MouseMove, *b, Qt.MouseButton.NoButton, left)
    _send_mouse(win, QEvent.Type.MouseButtonRelease, *b, left,
               Qt.MouseButton.NoButton)


@pytest.mark.gui
def test_dragging_the_ridge_grip_with_the_mouse(fp, win):
    win.prepare_headless()
    rf = _roof(win.scene)
    rf.setSelected(True)
    _drag(win, (150, 100), (150, 130.4))
    assert (rf.p1.y(), rf.p2.y()) == (pytest.approx(132.0), pytest.approx(132.0))
    assert rf.span_in == pytest.approx([SPAN - 32.0, SPAN + 32.0])


@pytest.mark.gui
def test_dragging_an_eave_grip_with_the_mouse(fp, win):
    win.prepare_headless()
    rf = _roof(win.scene)
    rf.setSelected(True)
    _drag(win, (150, 100 + SPAN + OH), (150, 245.3))
    assert rf.span_in == pytest.approx([246.0 - 100.0 - OH, SPAN])


@pytest.mark.gui
def test_a_grip_press_does_not_start_a_second_ridge_under_the_ridge_tool(fp, win):
    """Same guard the marker already has (view.py): the ridge tool stays
    sticky after a sketch, and a press on a grip is the grip's own drag."""
    win.prepare_headless()
    rf = _roof(win.scene)
    rf.setSelected(True)
    win.set_tool(fp.TOOL_ROOF_RIDGE)
    _drag(win, (150, 100), (150, 130.4))
    roofs = [it for it in win.scene.items() if isinstance(it, RoofItem)]
    assert len(roofs) == 1
    assert rf.p1.y() == pytest.approx(132.0)


def test_an_end_grip_does_not_cover_the_marker(scene):
    """A gable end's line runs through the ridge endpoint the marker sits
    at; the grip is offset outside the line and drawn BELOW the marker, so
    the End-On dialog's first door keeps its click."""
    rf = _roof(scene)
    rf.setSelected(True)
    g = _grip(rf, "end_1")
    assert g.pos() != rf.marker.pos()
    assert g.zValue() < rf.marker.zValue()
    assert not g.shape().contains(g.mapFromScene(rf.marker.pos()))
