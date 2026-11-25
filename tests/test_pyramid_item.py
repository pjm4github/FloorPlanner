"""0367 stage 2 -- the PYRAMID-ROOF furnishing item.

A pyramid roof is a furnishing: placed from the palette, it OWNS NO WALL and
draws its plan symbol (the wall-line and eave polygons, the hips and the apex)
from its parameters, read from `pyramid_geometry` (C1). These check the Qt item
on top of the pure arithmetic (`tests/test_pyramid_geometry.py`): it is built by
`make_furnishing`, its footprint follows the parameters, the radius knob snaps
to the grid unless Shift is held, it finds the room it sits on, and a pyramid
that cannot be built still draws, in RED (C5).
"""
import math

import pytest
from PyQt6.QtCore import QPointF
from PyQt6.QtGui import QColor, QImage, QPainter, QPainterPath

from floorplanner.config import DEFAULT_FLOOR
from floorplanner.items import (
    PyramidRadiusGrip, PyramidRoofItem, make_furnishing)
from floorplanner.parametric import findings as F
from floorplanner.parametric import pyramid_geometry as pg
from floorplanner.parametric.pyramids import PYRAMID_ROOF
from floorplanner.rooms import RoomItem

pytestmark = [pytest.mark.rooms, pytest.mark.furnishings]


def _pyramid(scene, pos=None, rotation=0.0, state=None, new=True):
    it = make_furnishing("pyramid_roof", pos or QPointF(150, 100), rotation,
                         state or {}, new=new)
    it.floor = DEFAULT_FLOOR
    scene.addItem(it)
    return it


def _rect_room(scene, ceiling_in=108.0):
    path = QPainterPath()
    path.addRect(0, 0, 400, 300)
    room = RoomItem("Room", QPointF(200, 150), path, 100.0)
    room.floor = DEFAULT_FLOOR
    room.properties["ceiling_height_in"] = ceiling_in
    scene.addItem(room)
    return room


def _hex_room(scene, pos, state, ceiling_in=108.0):
    """A room whose outline IS the pyramid's wall-line polygon in plan -- a
    bump-out the pyramid sits exactly on."""
    path = QPainterPath()
    pts = [pg.to_plan((pos.x(), pos.y()), 0.0, v) for v in pg.wall_polygon(state)]
    path.moveTo(*pts[0])
    for p in pts[1:]:
        path.lineTo(*p)
    path.closeSubpath()
    room = RoomItem("Bay", pos, path, 100.0)
    room.floor = DEFAULT_FLOOR
    room.properties["ceiling_height_in"] = ceiling_in
    scene.addItem(room)
    return room


def _render(scene):
    img = QImage(300, 300, QImage.Format.Format_ARGB32)
    img.fill(0)
    p = QPainter(img)
    scene.render(p)
    p.end()
    return img


# -- make_furnishing builds the right item ------------------------------------
def test_make_furnishing_builds_a_pyramid_item():
    it = make_furnishing("pyramid_roof", QPointF(10, 10), new=True)
    assert isinstance(it, PyramidRoofItem)
    assert it.is_parametric() and it.kind == "pyramid_roof"
    assert set(it.extra_state()) == set(pg.STATE_DEFAULTS)


def test_the_plan_symbol_is_a_polygon_drawn_from_the_parameters():
    it = make_furnishing("pyramid_roof", QPointF(10, 10), new=True)
    sym = PYRAMID_ROOF.plan_symbol(it.params)
    ops = [prim[0] for prim in sym["prims"]]
    assert ops.count("poly") == 2            # eave + wall-line polygons
    assert ops.count("line") == it.params["sides"]   # one hip per side
    assert "dot" in ops                      # the apex


def test_the_footprint_follows_the_parameters():
    it = make_furnishing("pyramid_roof", QPointF(10, 10), new=True)
    w, d = pg.bbox(it.params)
    assert (it.w, it.d) == pytest.approx((w, d))
    # a bigger inradius grows the footprint
    it.apply_params({**it.params, "inradius_in": 120.0})
    w2, d2 = pg.bbox(it.params)
    assert (it.w, it.d) == pytest.approx((w2, d2)) and w2 > w


def test_it_paints_without_crashing_selected_and_broken(scene):
    _rect_room(scene)
    it = _pyramid(scene)
    it.setSelected(True)
    _render(scene)                            # the symbol, the knob, the rotator
    it.apply_params({**it.params, "pitch_12": 0.0})   # cannot be built
    _render(scene)


# -- the room it sits on (R3) -------------------------------------------------
def test_param_context_reports_the_room_and_its_ceiling(scene):
    room = _rect_room(scene, ceiling_in=120.0)
    it = _pyramid(scene, pos=QPointF(200, 150))
    ctx = it.param_context()
    assert ctx["room_present"] is True
    assert ctx["ceiling_in"] == pytest.approx(120.0)
    # evaluate binds the eaves to that ceiling under room_top
    derived, _ = PYRAMID_ROOF.evaluate(it.params, ctx)
    assert derived["eaves_h_in"] == pytest.approx(120.0)
    assert room is it._owning_room()


def test_no_room_is_reported_and_warned(scene):
    it = _pyramid(scene, pos=QPointF(5, 5))   # outside any room
    ctx = it.param_context()
    assert ctx["room_present"] is False
    _, findings = PYRAMID_ROOF.evaluate(it.params, ctx)
    assert any(f.rule_id == "pyramid.no_room" and f.severity == F.WARNING
               for f in findings)


def test_off_room_is_near_zero_when_the_pyramid_sits_on_its_room(scene):
    pos = QPointF(200, 150)
    st = pg.default_state(108.0)
    _hex_room(scene, pos, st)
    it = _pyramid(scene, pos=pos, state=st)
    ctx = it.param_context()
    assert ctx["off_room_in"] == pytest.approx(0.0, abs=1.0)


def test_off_room_is_large_when_the_wall_line_misses_the_walls(scene):
    _rect_room(scene)                         # a big rectangle
    it = _pyramid(scene, pos=QPointF(200, 150))
    ctx = it.param_context()
    assert ctx["off_room_in"] > pg.MIN_INRADIUS_IN


# -- the radius knob ----------------------------------------------------------
def test_the_knob_rides_the_wall_line_and_shows_with_selection(scene):
    _rect_room(scene)
    it = _pyramid(scene, pos=QPointF(200, 150))
    assert isinstance(it._radius_grip, PyramidRadiusGrip)
    assert it._radius_grip.parentItem() is it
    assert it._radius_grip.pos() == QPointF(0.0, -it.params["inradius_in"])
    it.setSelected(False)
    assert not it._radius_grip.isVisible()
    it.setSelected(True)
    assert it._radius_grip.isVisible()


def test_dragging_the_knob_snaps_the_radius_to_the_grid(scene):
    _rect_room(scene)
    it = _pyramid(scene, pos=QPointF(200, 150))
    # a drag 100 in up from the centre: snaps to the 6 in wall grid -> 102
    it.drag_radius(QPointF(200, 50), free=False)
    assert it.params["inradius_in"] == pytest.approx(102.0)
    # Shift is free: the fine 1 in grid
    it.drag_radius(QPointF(200, 50 + 1), free=True)
    assert it.params["inradius_in"] == pytest.approx(99.0)
    # never below the floor
    it.drag_radius(QPointF(200, 148), free=True)
    assert it.params["inradius_in"] == pytest.approx(pg.MIN_INRADIUS_IN)


def test_the_knob_distance_is_the_inradius_whatever_the_rotation(scene):
    _rect_room(scene)
    it = _pyramid(scene, pos=QPointF(200, 150), rotation=37.0)
    it.drag_radius(QPointF(200, 50), free=True)   # 100 in away, any direction
    assert it.params["inradius_in"] == pytest.approx(100.0)


# -- C5: a broken pyramid still loads and draws red ---------------------------
def test_a_flat_pyramid_draws_red_but_still_loads(scene):
    _rect_room(scene)
    it = _pyramid(scene, state={**pg.STATE_DEFAULTS, "pitch_12": 0.0})
    assert not it._buildable()
    assert it._plan_ink() == QColor(185, 28, 28)
    _, findings = PYRAMID_ROOF.evaluate(it.params, it.param_context())
    flat = [f for f in findings if f.rule_id == "pyramid.flat"]
    assert flat and flat[0].severity == F.ERROR and flat[0].overridable
    # a good pitch draws in the normal slate ink
    it.apply_params({**it.params, "pitch_12": 10.0})
    assert it._buildable() and it._plan_ink() == QColor(55, 65, 81)


# -- state round-trips --------------------------------------------------------
def test_state_round_trips_through_make_furnishing():
    state = {"sides": 8, "inradius_in": 96.0, "pitch_12": 12.0,
             "eaves_bind": "manual", "eaves_h_in": 110.0, "overhang_in": 18.0,
             "weld": "off"}
    it = make_furnishing("pyramid_roof", QPointF(0, 0), 0.0, state)
    out = it.extra_state()
    for k, v in state.items():
        assert out[k] == pytest.approx(v) if isinstance(v, float) else out[k] == v
    assert math.isclose(out["inradius_in"], 96.0)
