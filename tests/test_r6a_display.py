"""R6.a (0197-ruling.md sec4) -- the plan view's multifloor roof rule, Patrick's
own answer adopted: THIS level's roofs draw solid; a roof on ANY OTHER level
that covers this level's rooms draws ghosted -- even with "show other
floors" off. `roofs.roof_covers_floor` is the predicate, reusing R4b's own
room-coverage overlap rule; `apply_roof_visibility` applies it.

Measured on his own R6 fixture, `fixtures/wiscaway-2level-stacked-floor.json`
(0197 sec3, promoted under exit 1): every roof but one covers rooms on both
levels; the one exception -- L1's 45-degree wing roof, ridge (1426,272) to
(1031,666) -- covers no upper room, so it is the fail-first control: hidden
on the upper plan with "show other floors" off before R6.a and still, and
visible there only when ghosting is on.
"""
import pytest
from PyQt6.QtCore import QPointF
from PyQt6.QtGui import QPainterPath

from floorplanner.config import DEFAULT_FLOOR
from floorplanner.roofs import RoofItem, roof_covers_floor
from floorplanner.rooms import RoomItem

pytestmark = pytest.mark.walls

FIXTURE = "fixtures/wiscaway-2level-stacked-floor.json"


def _roofs(win):
    return sorted((it for it in win.scene.items() if isinstance(it, RoofItem)),
                  key=lambda r: (r.floor, r.p1.x(), r.p1.y()))


def _wing(win):
    return next(r for r in _roofs(win)
                if r.floor == "default" and round(r.p1.x()) == 1426)


# --------------------------------------------------------------------------
# his fixture: the real coverage, and the rule applied to it
# --------------------------------------------------------------------------
def test_the_fixture_is_the_first_multifloor_plan_with_roofs_on_two_levels(fp, win):
    win.prepare_headless()
    win.load_path(FIXTURE)
    floors = {f.name: (f.elevation_in, f.height_in) for f in win.floors}
    assert floors == {"default": (0.0, 96.0), "upper": (100.0, 196.0)}, \
        "R6.0's elevation survived the trip in: L2 sits at 100in"
    by_floor = {}
    for r in _roofs(win):
        by_floor[r.floor] = by_floor.get(r.floor, 0) + 1
    assert by_floor == {"default": 2, "upper": 4}


def test_coverage_measured_on_the_fixture(fp, win):
    win.prepare_headless()
    win.load_path(FIXTURE)
    wing = _wing(win)
    assert roof_covers_floor(win.scene, wing, "default")
    assert not roof_covers_floor(win.scene, wing, "upper"), \
        "the L1 wing covers no upper room -- the control"
    others = [r for r in _roofs(win) if r is not wing]
    assert all(roof_covers_floor(win.scene, r, "default") for r in others)
    assert all(roof_covers_floor(win.scene, r, "upper") for r in others)


def test_on_the_lower_plan_the_upper_roofs_draw_ghosted_even_with_others_hidden(fp, win):
    win.prepare_headless()
    win.load_path(FIXTURE)
    win.show_other_floors = False
    win.switch_floor("default")
    for r in _roofs(win):
        if r.floor == "upper":
            assert r.isVisible() and not r.isEnabled(), "covering roof: shown, not editable"
            assert fp.floor_display_mode(r.floor) == "hidden", \
                "the floor itself is hidden -- only the covering roof shows"
        else:
            assert r.isVisible() and r.isEnabled(), "this level's roof: solid, editable"


def test_on_the_upper_plan_the_wing_that_covers_nothing_stays_hidden(fp, win):
    """The fail-first control: a roof on another level that covers no room
    on this one is NOT shown by the rule -- with ghosting off it is
    hidden, exactly as before R6.a; with ghosting on it shows like any
    other floor's item."""
    win.prepare_headless()
    win.load_path(FIXTURE)
    wing = _wing(win)
    win.show_other_floors = False
    win.switch_floor("upper")
    assert not wing.isVisible()
    main = next(r for r in _roofs(win) if r.floor == "default" and r is not wing)
    assert main.isVisible() and not main.isEnabled(), "L1's main roof covers upper rooms"
    win.show_other_floors = True
    win._sync_floor_state()
    assert wing.isVisible() and not wing.isEnabled()


def test_hiding_roofs_hides_covering_roofs_too(fp, win):
    win.prepare_headless()
    win.load_path(FIXTURE)
    win.show_other_floors = False
    win.switch_floor("default")
    win._set_show_roofs(False)
    assert all(not r.isVisible() for r in _roofs(win))
    win._set_show_roofs(True)
    assert all(r.isVisible() for r in _roofs(win))


# --------------------------------------------------------------------------
# the predicate, on a synthetic pair
# --------------------------------------------------------------------------
def _room(scene, floor, x0, y0, w, h):
    path = QPainterPath()
    path.addRect(x0, y0, w, h)
    room = RoomItem("R", QPointF(x0 + w / 2, y0 + h / 2), path, w * h / 144.0)
    room.floor = floor
    room.properties["ceiling_height_in"] = 96.0
    scene.addItem(room)
    return room


def test_a_roof_covers_a_floor_only_where_it_overlaps_a_room_by_more_than_a_sliver(fp, scene):
    _room(scene, DEFAULT_FLOOR, 0, 0, 300, 200)
    _room(scene, "upper", 1000, 0, 300, 200)
    rf = RoofItem(QPointF(50, 100), QPointF(250, 100), eaves_h_in=96.0,
                  ridge_h_in=132.0, overhang_in=0.0, span_in=100.0)
    rf.floor = "upper"
    scene.addItem(rf)
    assert roof_covers_floor(scene, rf, DEFAULT_FLOOR)
    assert not roof_covers_floor(scene, rf, "upper")
    # a roof whose footprint only grazes a room's edge (0.5in) is not coverage
    graze = RoofItem(QPointF(-150, 100), QPointF(-50, 100), eaves_h_in=96.0,
                     ridge_h_in=132.0, overhang_in=0.0, span_in=100.0)
    graze.floor = "upper"
    scene.addItem(graze)                     # footprint x in [-150, -50]
    assert not roof_covers_floor(scene, graze, DEFAULT_FLOOR)
    graze.set_ridge(QPointF(-99.5, 100), QPointF(0.5, 100))     # 0.5in into the room
    assert not roof_covers_floor(scene, graze, DEFAULT_FLOOR)
    graze.set_ridge(QPointF(-90, 100), QPointF(10, 100))        # 10in into the room
    assert roof_covers_floor(scene, graze, DEFAULT_FLOOR)
