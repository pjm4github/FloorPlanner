"""R6.c (0197-ruling.md sec5) -- the roof tool across levels.

Measured before it was built (`docs/evidence/r6c_roof_tool_levels_probe.py`,
its `.before.txt`), on Patrick's own R6 fixture with the upper level being
edited: a ridge pressed on a line of the lower level's ghosted roof never
started; the eaves pick took a ghosted wall of the lower level and measured
the span to it; a ridge still awaiting its eaves pick survived a level
switch and took its eaves from the level switched TO. The start snap was
already scoped to the level (0 of 136 lower-only wall ends drew it), and a
selected roof was already dropped by a level switch.

The rule these pin is D67's own, applied to the roof tool: "an inactive
floor may be drawn; it may not be hit-tested, selected, banded, or
dragged." And one display fact: on a level whose base is not the ground,
the End-On dialog says where the roof stands in the building.
"""
import pytest
from PyQt6.QtCore import QEvent, QPointF, Qt
from PyQt6.QtGui import QMouseEvent
from PyQt6.QtWidgets import QApplication, QDialog

from floorplanner.config import floor_elevation
from floorplanner.dialogs import RoofEndOnDialog
from floorplanner.roofclip import compose_building
from floorplanner.roofs import (
    RoofEndMarkerItem, RoofGripItem, RoofItem, host_roof_at,
)

pytestmark = pytest.mark.gui

FIXTURE = "fixtures/wiscaway-2level-stacked-floor.json"
MANUAL_FIXTURE = "fixtures/r6c-two-level-tool-check.json"
LOWER, UPPER = "default", "upper"
LEFT, NONE = Qt.MouseButton.LeftButton, Qt.MouseButton.NoButton


def _send(win, etype, p, button, buttons):
    vp = win.view.viewport()
    pos = win.view.mapFromScene(QPointF(*p))
    QApplication.sendEvent(vp, QMouseEvent(
        etype, QPointF(pos), QPointF(vp.mapToGlobal(pos)), button, buttons,
        Qt.KeyboardModifier.NoModifier))


def _press(win, p):
    _send(win, QEvent.Type.MouseButtonPress, p, LEFT, LEFT)


def _drag(win, a, b):
    _press(win, a)
    _send(win, QEvent.Type.MouseMove, b, NONE, LEFT)
    _send(win, QEvent.Type.MouseButtonRelease, b, LEFT, NONE)


def _click(win, p):
    _press(win, p)
    _send(win, QEvent.Type.MouseButtonRelease, p, LEFT, NONE)


def _roofs(win, floor=None):
    return [it for it in win.scene.items()
            if isinstance(it, RoofItem) and (floor is None or it.floor == floor)]


def _wall(fp, win, a, b, floor):
    w = fp.WallItem(QPointF(*a), QPointF(*b), "exterior")
    w.floor = floor
    win.scene.addItem(w)
    return w


def _roof(win, a, b, floor, eaves=96.0, ridge=150.0, span=100.0):
    rf = RoofItem(QPointF(*a), QPointF(*b), eaves_h_in=eaves, ridge_h_in=ridge,
                  overhang_in=0.0, span_in=span)
    rf.floor = floor
    win.scene.addItem(rf)
    return rf


def _two_levels(fp, win, show_others=True, upper_elevation=100.0):
    """`default` at 0in and `upper` at `upper_elevation`, the upper one being
    edited -- built on `default` first, the way a plan is drawn."""
    win.prepare_headless()
    win.new_floor_named(UPPER)
    win.set_floor_levels(UPPER, upper_elevation, 96.0)
    win.show_other_floors = show_others
    win.switch_floor(LOWER)
    return win


def _accept_dialogs(monkeypatch):
    monkeypatch.setattr(QDialog, "exec", lambda self: QDialog.DialogCode.Accepted)


def test_the_tiny_manual_fixture_keeps_every_target_unambiguous(fp, win):
    """The human check is one operation per reload on a scene whose targets
    cannot be confused with Wiscaway's 166 walls and six roofs."""
    win.prepare_headless()
    win.load_path(MANUAL_FIXTURE)

    assert win.active_floor == UPPER
    assert {f.name: (f.elevation_in, f.height_in) for f in win.floors} == {
        LOWER: (0.0, 96.0), UPPER: (120.0, 96.0)}
    rooms = {it.name: it for it in win.scene.items()
             if isinstance(it, fp.RoomItem)}
    assert set(rooms) == {"LOWER - GREY TARGET", "UPPER - SOLID TARGET"}
    walls = [it for it in win.scene.items() if isinstance(it, fp.WallItem)]
    roofs = _roofs(win)
    assert {floor: sum(it.floor == floor for it in walls)
            for floor in (LOWER, UPPER)} == {LOWER: 4, UPPER: 4}
    assert {floor: sum(it.floor == floor for it in roofs)
            for floor in (LOWER, UPPER)} == {LOWER: 1, UPPER: 1}

    win.show_other_floors = True
    win._sync_floor_state()

    # The exact human targets: each point resolves to only the named level.
    def walls_at(x, y):
        return {it.floor for it in win.scene.items(QPointF(x, y))
                if isinstance(it, fp.WallItem)}

    assert walls_at(180, 300) == {LOWER}, "left box's bottom wall"
    assert walls_at(540, 300) == {UPPER}, "right box's bottom wall"
    lower_roof = next(r for r in roofs if r.floor == LOWER)
    upper_roof = next(r for r in roofs if r.floor == UPPER)
    assert (lower_roof.p1, lower_roof.p2) == (QPointF(60, 180), QPointF(300, 180))
    assert (upper_roof.p1, upper_roof.p2) == (QPointF(420, 180), QPointF(660, 180))
    assert host_roof_at(win.scene, QPointF(180, 120), LOWER) is lower_roof
    assert host_roof_at(win.scene, QPointF(180, 120), UPPER) is None

    assert lower_roof.isVisible() and not lower_roof.isEnabled()
    assert upper_roof.isVisible() and upper_roof.isEnabled()


# --------------------------------------------------------------------------
# a roof of a level that is not being edited: drawn, never hit
# --------------------------------------------------------------------------
def test_a_roof_of_another_level_is_drawn_and_answers_no_hit_query(fp, win):
    _two_levels(fp, win)
    rf = _roof(win, (0, 200), (400, 200), LOWER)
    on_ridge = QPointF(200, 200)
    assert rf in win.scene.items(on_ridge), "on its own level: hittable"
    assert not rf.marker.shape().isEmpty()

    win.switch_floor(UPPER)

    assert rf.isVisible() and not rf.isEnabled(), "ghosted: drawn, not editable"
    assert rf.shape().isEmpty() and rf.marker.shape().isEmpty()
    assert all(g.shape().isEmpty() for g in rf.grips)
    assert not any(isinstance(it, (RoofItem, RoofGripItem, RoofEndMarkerItem))
                   for it in win.scene.items(on_ridge))
    assert not rf.boundingRect().isEmpty(), "it still paints at full extent"

    win.switch_floor(LOWER)
    assert rf in win.scene.items(on_ridge), "and it comes back with its level"


def test_a_ridge_pressed_on_another_levels_ghosted_roof_line_starts(fp, win):
    """The measured fault: the press met the ghosted roof, was taken for a
    press on an existing roof, and fell through to a disabled item."""
    _two_levels(fp, win)
    _roof(win, (0, 200), (400, 200), LOWER)
    win.switch_floor(UPPER)
    win.set_tool(fp.TOOL_ROOF_RIDGE)

    _drag(win, (120, 200), (300, 200))           # along the lower roof's ridge

    pending = win.view._roof_awaiting_eaves
    assert pending is not None, "the ghosted roof did not swallow the press"
    assert pending.floor == UPPER
    assert len(_roofs(win, UPPER)) == 1 and len(_roofs(win, LOWER)) == 1


def test_on_his_fixture_a_ridge_starts_on_the_lower_roofs_ghosted_line(fp, win):
    win.prepare_headless()
    win.load_path(FIXTURE)
    win.show_other_floors = False
    win.switch_floor(UPPER)
    win.view.fitInView(win.scene.itemsBoundingRect(),
                       Qt.AspectRatioMode.KeepAspectRatio)
    ghost = next(r for r in _roofs(win, LOWER) if r.isVisible())
    pt = None
    for p, q in ghost._drawn_lines() + list(ghost._seams):
        for k in range(1, 40):
            c = QPointF(p.x() + (q.x() - p.x()) * k / 40.0,
                        p.y() + (q.y() - p.y()) * k / 40.0)
            if not any(isinstance(it, (RoofItem, RoofGripItem, RoofEndMarkerItem,
                                       fp.WallItem))
                       for it in win.scene.items(c)):
                pt = c
                break
        if pt is not None:
            break
    assert pt is not None, "a point on the ghosted roof clear of everything else"
    win.set_tool(fp.TOOL_ROOF_RIDGE)

    _drag(win, (pt.x(), pt.y()), (pt.x() + 96.0, pt.y()))

    assert win.view._roof_awaiting_eaves is not None
    assert win.view._roof_awaiting_eaves.floor == UPPER
    assert len(_roofs(win)) == 7


# --------------------------------------------------------------------------
# the eaves pick: a wall of the roof's own level only
# --------------------------------------------------------------------------
def test_the_eaves_pick_refuses_a_wall_of_another_level(fp, win, monkeypatch):
    _accept_dialogs(monkeypatch)
    _two_levels(fp, win, show_others=True)
    _wall(fp, win, (0, 300), (200, 300), LOWER)
    _wall(fp, win, (0, 100), (200, 100), UPPER)
    win.switch_floor(UPPER)
    win.set_tool(fp.TOOL_ROOF_RIDGE)
    _drag(win, (0, 0), (200, 0))
    pending = win.view._roof_awaiting_eaves
    assert pending is not None

    _click(win, (100, 300))                      # the LOWER level's ghosted wall

    assert win.view._roof_awaiting_eaves is pending, "refused: still awaiting"
    assert "eaves wall" in win.statusBar().currentMessage()

    _click(win, (100, 100))                      # this level's wall

    assert win.view._roof_awaiting_eaves is None
    assert list(pending.span_in) == pytest.approx([100.0, 100.0]), \
        "measured to the upper wall 100in off, not the lower one 300in off"
    assert pending.floor == UPPER


# --------------------------------------------------------------------------
# a gesture belongs to the level it began on
# --------------------------------------------------------------------------
def test_switching_level_settles_a_ridge_awaiting_its_eaves_on_its_own_level(
        fp, win, monkeypatch):
    _accept_dialogs(monkeypatch)
    _two_levels(fp, win, show_others=True)
    lower = _wall(fp, win, (0, 40), (200, 40), LOWER)      # the NEARER wall
    _wall(fp, win, (0, 100), (200, 100), UPPER)
    win.switch_floor(UPPER)
    win.set_tool(fp.TOOL_ROOF_RIDGE)
    _drag(win, (0, 0), (200, 0))
    pending = win.view._roof_awaiting_eaves
    assert pending is not None

    win.switch_floor(LOWER)

    assert win.view._roof_awaiting_eaves is None, "settled before the switch"
    assert pending.scene() is win.scene and pending.floor == UPPER
    assert list(pending.span_in) == pytest.approx([100.0, 100.0]), \
        "its eaves come from its own level's wall, not the nearer lower one"

    _click(win, (100, 40))                       # a click on the lower wall now
    assert list(pending.span_in) == pytest.approx([100.0, 100.0]), \
        "is no eaves pick for a roof of the level just left"
    assert lower.scene() is win.scene
    assert len(_roofs(win, UPPER)) == 1


def test_switching_level_drops_a_ridge_still_being_dragged(fp, win):
    _two_levels(fp, win)
    win.switch_floor(UPPER)
    win.set_tool(fp.TOOL_ROOF_RIDGE)
    _press(win, (0, 0))
    _send(win, QEvent.Type.MouseMove, (150, 0), NONE, LEFT)
    assert win.view._temp_roof is not None

    win.switch_floor(LOWER)

    assert win.view._temp_roof is None
    assert _roofs(win) == [], "an unreleased drag leaves nothing on either level"


# --------------------------------------------------------------------------
# the dormer tool: a host on this level, or a refusal that names the level
# --------------------------------------------------------------------------
def test_the_dormer_tool_names_the_level_of_a_roof_it_cannot_reach(fp, win):
    _two_levels(fp, win, show_others=True)
    lower = _roof(win, (0, 200), (400, 200), LOWER)
    win.switch_floor(UPPER)
    assert lower.isVisible()
    assert host_roof_at(win.scene, QPointF(200, 250), UPPER) is None
    win.set_tool(fp.TOOL_ROOF_DORMER)

    _drag(win, (200, 250), (236, 250))           # on the lower roof's slope

    assert len(_roofs(win)) == 1, "no dormer: the roof is not this level's"
    msg = win.statusBar().currentMessage()
    assert f"'{LOWER}'" in msg and "switch" in msg

    _drag(win, (200, 900), (236, 900))           # where no roof is at all
    assert "press on a roof plane" in win.statusBar().currentMessage()


# --------------------------------------------------------------------------
# a roof sketched on an upper level stands at that level's elevation
# --------------------------------------------------------------------------
def test_a_roof_sketched_on_the_upper_level_composes_at_its_elevation(
        fp, win, monkeypatch):
    _accept_dialogs(monkeypatch)
    _two_levels(fp, win, show_others=True, upper_elevation=100.0)
    main = _roof(win, (0, 200), (400, 200), LOWER, eaves=96.0, ridge=150.0,
                 span=100.0)
    _wall(fp, win, (264, 156), (264, 504), UPPER)
    win.switch_floor(UPPER)
    win.set_tool(fp.TOOL_ROOF_RIDGE)

    _drag(win, (204, 156), (204, 504))           # on the grid, as a drag lands
    _click(win, (264, 300))

    wing = next(iter(_roofs(win, UPPER)))
    assert list(wing.span_in) == pytest.approx([60.0, 60.0])
    assert floor_elevation(wing.floor) == 100.0
    assert wing.eaves_h_in == pytest.approx(96.0), "level-relative, as typed"

    lifted = compose_building([(main, 0.0), (wing, 100.0)])
    one_datum = compose_building([(main, 0.0), (wing, 0.0)])
    assert main._clip_region is not None
    assert main._clip_region.area() == pytest.approx(lifted[id(main)].region.area())
    assert lifted[id(main)].region.area() != pytest.approx(
        one_datum[id(main)].region.area()), \
        "the control: at one datum the same two roofs compose differently"


# --------------------------------------------------------------------------
# the End-On dialog on a level whose base is not the ground
# --------------------------------------------------------------------------
def test_the_dialog_says_where_an_upper_levels_roof_stands(fp, win):
    _two_levels(fp, win, upper_elevation=100.0)
    low = _roof(win, (0, 200), (400, 200), LOWER, eaves=96.0, ridge=150.0)
    up = _roof(win, (0, 600), (400, 600), UPPER, eaves=25.0, ridge=135.0)

    d_low = RoofEndOnDialog(low, win)
    assert d_low.level_base_in() == 0.0
    assert d_low.lab_level.text() == "", "on the ground level there is nothing to add"
    assert d_low.absolute_heights() == pytest.approx((96.0, 150.0))

    d_up = RoofEndOnDialog(up, win)
    assert d_up.level_base_in() == 100.0
    assert d_up.sp_eaves.value() == pytest.approx(25.0), "the fields stay level-relative"
    assert d_up.absolute_heights() == pytest.approx((125.0, 235.0))
    text = d_up.lab_level.text()
    assert f"'{UPPER}'" in text
    assert fp.fmt_in(100.0) in text and fp.fmt_in(125.0) in text \
        and fp.fmt_in(235.0) in text

    d_up.sp_ridge.setValue(160.0)                # live, as the height is typed
    assert d_up.absolute_heights()[1] == pytest.approx(260.0)
    assert fp.fmt_in(260.0) in d_up.lab_level.text()

    assert d_up.apply() is not False
    assert up.ridge_h_in == pytest.approx(160.0), "what is stored is what was typed"
    d_low.deleteLater()
    d_up.deleteLater()
