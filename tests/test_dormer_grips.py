"""Phase 2 of the Build-Dormer controls: the six on-canvas grips a selected
dormer shows beside the five universal roof grips -- two side walls (span),
two side eaves (overhang), the gable-face setback, and the face eave (the
per-end overhang). The drag methods move each line independently.

Dormer geometry (shared with test_roof_dormer.py): a host ridge along x at
y=100 (eaves 96 / ridge 150, span 100); a dormer with its face at (200,190)
and its back toward the host at (200,140), so the ridge axis is (0,-1) --
up-slope is -y -- and the +left normal is +x. span 30 each side.
"""
import math
import pytest
from PyQt6.QtCore import QPointF
from PyQt6.QtGui import QPainterPath

from floorplanner.config import DEFAULT_FLOOR
from floorplanner.roofs import RoofGripItem, RoofItem
from floorplanner.rooms import RoomItem

pytestmark = pytest.mark.walls


def _host(scene):
    rf = RoofItem(QPointF(0, 100), QPointF(400, 100), eaves_h_in=96.0,
                  ridge_h_in=150.0, overhang_in=12.0, span_in=100.0)
    rf.floor = DEFAULT_FLOOR
    path = QPainterPath()
    path.addRect(0, 0, 400, 200)
    room = RoomItem("Loft", QPointF(200, 100), path, 100.0)
    room.floor = DEFAULT_FLOOR
    room.properties["ceiling_height_in"] = 96.0
    scene.addItem(room)
    scene.addItem(rf)
    return rf


def _dormer(scene, host, span=30.0):
    d = RoofItem(QPointF(200, 190), QPointF(200, 140), eaves_h_in=116.0,
                 ridge_h_in=136.0, overhang_in=0.0, span_in=span,
                 marker_end=0, host=host)
    d.floor = DEFAULT_FLOOR
    scene.addItem(d)
    return d


def _grip(rf, kind):
    return next(g for g in rf.grips if g.kind == kind)


# -- visibility -------------------------------------------------------------
def test_a_plain_roof_never_shows_the_dormer_grips(scene):
    host = _host(scene)
    host.setSelected(True)
    vis = {g.kind for g in host.grips if g.isVisible()}
    assert vis == set(RoofGripItem.KINDS)


def test_a_selected_dormer_shows_its_a_g_controls_only(scene):
    # the dormer's own A-G controls plus the ridge (G); the universal eave/end
    # grips are hidden so the frame and walls are not duplicated by extra knobs
    host = _host(scene)
    d = _dormer(scene, host)
    d.setSelected(True)
    vis = {g.kind for g in d.grips if g.isVisible()}
    assert vis == set(RoofGripItem.DORMER_KINDS) | {"ridge"}
    assert "eave_l" not in vis and "end_0" not in vis
    d.setSelected(False)
    assert not any(g.isVisible() for g in d.grips)


# -- the drags --------------------------------------------------------------
def test_the_side_wall_grip_moves_the_wall_not_the_pitch(scene):
    # control C is decoupled from the roof: dragging it moves wall_span_in
    # (the black wall) and leaves span_in -- the eaves line and the pitch --
    # exactly where they were. span [30,30], eaves 116, ridge 136.
    host = _host(scene)
    d = _dormer(scene, host)
    pitch_before = (d.ridge_h_in - d.eaves_h_in) / d.span_in[0]
    assert d.wall_span_in == [30.0, 30.0], "walls start on the eaves line"
    d.drag_wall(0, QPointF(246, 190))          # +x = left; perp 46 (inside the valley)
    assert d.wall_span_in == [46.0, 30.0], "only the left wall moved"
    assert d.span_in == [30.0, 30.0], "the roof's eaves line is untouched"
    pitch_after = (d.ridge_h_in - d.eaves_h_in) / d.span_in[0]
    assert pitch_after == pytest.approx(pitch_before), "the pitch did not change"


def test_the_side_eave_grip_sets_the_overhang_beyond_the_wall(scene):
    # control E is the eave overhang BEYOND the wall (C); the eave reach is
    # wall + overhang
    host = _host(scene)
    d = _dormer(scene, host)                    # span 30, wall 30, valley ~51.9
    assert d.overhang_in == [0.0, 0.0]
    d.drag_soffit(0, QPointF(246, 190))         # eave reach 46: overhang 16 beyond wall 30
    assert d.overhang_in == [16.0, 0.0]
    assert d._eave_reach(0) == pytest.approx(46.0)
    assert d.span_in == [30.0, 30.0], "span (the pitch line) is untouched"
    d.drag_soffit(0, QPointF(210, 190))         # pulled to the wall: overhang 0
    assert d.overhang_in[0] == pytest.approx(0.0)


def test_the_setback_grip_slides_the_face_along_the_ridge(scene):
    host = _host(scene)
    d = _dormer(scene, host)                    # face at y=190
    # control D sits ON the face wall; dragging it to y=180 moves the face there
    d.drag_setback(QPointF(200, 180))
    assert d.p1.y() == pytest.approx(180.0)
    assert d.p1.x() == pytest.approx(200.0), "the face stays on the ridge line"


def test_the_face_eave_grip_sets_the_front_overhang_and_cannot_pass_the_face(scene):
    host = _host(scene)
    d = _dormer(scene, host)                    # face at y=190, axis -y
    d.drag_face_eave(QPointF(200, 216))         # 26in down-slope of the face
    assert d.end_overhang_in == [26.0, 0.0]
    d.drag_face_eave(QPointF(200, 180))         # up past the face: clamps to 0
    assert d.end_overhang_in == [0.0, 0.0]


def test_wall_span_round_trips_and_defaults_to_the_eaves_line(scene):
    from floorplanner.design.bridge import apply_design_to_scene, design_from_scene
    from floorplanner.design.validate import schema_errors
    host = _host(scene)
    d = _dormer(scene, host)
    out = design_from_scene(scene).to_dict()
    drec = next(r for r in out["roofs"] if r.get("host"))
    assert "wall_span_in" not in drec, "walls on the eaves line write no key"
    assert schema_errors(out) == []
    d.wall_span_in = [52.0, 24.0]                   # move the walls off the line
    out2 = design_from_scene(scene).to_dict()
    drec2 = next(r for r in out2["roofs"] if r.get("host"))
    assert drec2["wall_span_in"] == [52.0, 24.0]
    assert drec2["span_in"] == [30.0, 30.0], "the eaves line is still its own field"
    assert schema_errors(out2) == []
    # reload keeps the walls
    scene.clear()
    apply_design_to_scene(scene, out2, report={})
    d2 = next(it for it in scene.items() if isinstance(it, RoofItem) and it.is_dormer())
    assert d2.wall_span_in == [52.0, 24.0]


# -- Phase 3: the solid-black wall lines ------------------------------------
def test_a_dormer_draws_three_walls_a_plain_roof_none(scene):
    host = _host(scene)
    assert host._dormer_wall_lines() == [], "a roof with no host has no walls"
    d = _dormer(scene, host)                    # face (200,190), span 30, axis -y
    walls = d._dormer_wall_lines()
    assert len(walls) == 3, "the face wall and the two cheek walls"
    face = walls[0]
    assert {(round(face[0].x()), round(face[0].y())),
            (round(face[1].x()), round(face[1].y()))} == {(230, 190), (170, 190)}
    # each cheek runs up-slope from the face to where the host reaches the
    # dormer's eaves height (116): y = 100 + (150-116)/0.54 = 162.96
    cheek_ends = sorted(round(w[1].y(), 1) for w in walls[1:])
    assert cheek_ends == [pytest.approx(162.963, abs=0.1),
                          pytest.approx(162.963, abs=0.1)]


# -- Phase B: the roof lines (valleys) --------------------------------------
def test_the_roof_lines_are_valleys_solid_to_the_eave_then_dashed(scene):
    # host slope 0.54; dormer span 30, eaves 116, ridge 136 -> pitch 0.667;
    # host at the face (y=190) is 150 - 0.54*90 = 101.4, so the valley reaches
    # dv = (136 - 101.4)/0.667 = 51.9in off the ridge at the face.
    host = _host(scene)
    d = _dormer(scene, host)
    solid, dashed = d._dormer_roof_lines()
    assert len(solid) == 2 and len(dashed) == 2, "eave inside the valley: both split"
    for a, _b in solid:                         # each starts at the apex (p2)
        assert a.x() == pytest.approx(d.p2.x(), abs=1e-3)
        assert a.y() == pytest.approx(d.p2.y(), abs=1e-3)
    dv = d._face_valley_perp(0)
    assert dv == pytest.approx(51.9, abs=0.6)
    assert dashed[0][1].x() == pytest.approx(200.0 + dv, abs=0.5), "left corner at the face"
    # the walls pushed out to the valley make the whole line solid (no dashed)
    d.wall_span_in = [80.0, 80.0]                # wall past the valley (51.9)
    _s2, dashed2 = d._dormer_roof_lines()
    assert dashed2 == []


def test_the_wall_and_eave_are_capped_at_the_roof_line(scene):
    host = _host(scene)
    d = _dormer(scene, host)
    dv = d._face_valley_perp(0)                  # ~51.9
    d.drag_wall(0, QPointF(200 + dv + 40, 190))  # push the wall past the valley
    assert d.wall_span_in[0] == pytest.approx(dv, abs=0.6), "wall stops at the roof line"
    d.drag_soffit(0, QPointF(200 + dv + 40, 190))  # push the eave past it
    assert d._eave_reach(0) == pytest.approx(dv, abs=0.6), "the eave stops at the roof line"


# -- Phase C: A (apex), G (ridge), B (box top) ------------------------------
def test_dragging_the_ridge_holds_the_pitch_and_shifts_the_walls(scene):
    host = _host(scene)
    d = _dormer(scene, host)                    # span [30,30], walls [30,30]
    pitch = (d.ridge_h_in - d.eaves_h_in) / d.span_in[0]
    d.drag_ridge(QPointF(216, 160))             # +x = +normal; perp +16
    assert d.span_in == [30.0, 30.0], "the eaves line (and pitch) is held"
    assert (d.ridge_h_in - d.eaves_h_in) / d.span_in[0] == pytest.approx(pitch)
    assert d.p1.x() == pytest.approx(216.0), "the ridge (and face) moved +16"
    # the walls stay in place -> relative to the new ridge, left -16, right +16
    assert d.wall_span_in == [pytest.approx(14.0), pytest.approx(46.0)]


def test_the_apex_grip_moves_the_ridge(scene):
    host = _host(scene)
    d = _dormer(scene, host)
    _grip(d, "apex").apply_drag(QPointF(216, 160))
    assert d.p1.x() == pytest.approx(216.0)


def test_box_top_moves_the_apex_up_and_holds_the_pitch(scene):
    host = _host(scene)
    d = _dormer(scene, host)                    # pitch 0.667
    pitch = (d.ridge_h_in - d.eaves_h_in) / d.span_in[0]
    ridge0 = d.ridge_h_in
    d.drag_box_top(QPointF(200, 102))           # drag the apex up the host slope
    assert d.ridge_h_in > ridge0, "the apex rose up the host, the ridge grew"
    assert (d.ridge_h_in - d.eaves_h_in) / d.span_in[0] == pytest.approx(pitch, abs=1e-6)


# -- Phase C.2: B left/right (the frame clips the roof lines) ----------------
def test_the_frame_clips_the_left_roof_line(scene):
    host = _host(scene)
    d = _dormer(scene, host)
    dv = d._face_valley_perp(0)                 # ~51.9
    _s0, d0 = d._dormer_roof_lines()
    far0 = (d0[0] if d0 else _s0[0])[1]         # left line's outer end
    reach0 = math.hypot(far0.x() - d.p2.x(), far0.y() - d.p2.y())
    d.box_half_in = [40.0, 100.0]               # clip the left to 40 (< valley)
    s1, d1 = d._dormer_roof_lines()
    far1 = (d1[0] if d1 else s1[0])[1]
    reach1 = math.hypot(far1.x() - d.p2.x(), far1.y() - d.p2.y())
    assert reach1 < reach0, "the left roof line is clipped shorter"
    assert reach1 == pytest.approx(reach0 * 40.0 / dv, rel=0.03)


def test_drag_box_side_clamps_between_wall_and_host_edge(scene):
    host = _host(scene)
    d = _dormer(scene, host)
    d.drag_box_side(0, QPointF(900, 190))       # push far out past the host
    he = d._host_edge_perp(0)
    assert d.box_half_in[0] == pytest.approx(he, abs=6.0), "stops at the host edge"
    d.drag_box_side(0, QPointF(205, 190))       # drag inside the wall
    assert d.box_half_in[0] == pytest.approx(d.wall_span_in[0], abs=0.6)


def test_box_half_round_trips_dormer_only(scene):
    from floorplanner.design.bridge import design_from_scene
    from floorplanner.design.validate import schema_errors
    host = _host(scene)
    d = _dormer(scene, host)
    out = design_from_scene(scene).to_dict()
    assert "box_half_in" not in next(r for r in out["roofs"] if r.get("host"))
    d.box_half_in = [40.0, 44.0]
    out2 = design_from_scene(scene).to_dict()
    assert next(r for r in out2["roofs"] if r.get("host"))["box_half_in"] == [40.0, 44.0]
    assert schema_errors(out2) == []


# -- the grips sit on the lines they drive ----------------------------------
def test_the_grips_sit_on_their_lines(scene):
    host = _host(scene)
    d = _dormer(scene, host, span=30.0)
    d.overhang_in = [12.0, 12.0]                # control E: eave 12 beyond wall 30
    d.end_overhang_in = [18.0, 0.0]
    d.rebuild()
    d.setSelected(True)
    wl = _grip(d, "wall_l").pos()
    assert wl.x() == pytest.approx(230.0), "left wall on the wall line (x=200+30)"
    sl = _grip(d, "soffit_l").pos()
    assert sl.x() == pytest.approx(242.0), "left eave at wall+overhang (x=200+42)"
    sb = _grip(d, "setback").pos()
    assert (sb.x(), sb.y()) == (pytest.approx(200.0), pytest.approx(190.0)), \
        "the face control sits on the face wall (at p1)"
    fe = _grip(d, "face_eave").pos()
    assert (fe.x(), fe.y()) == (pytest.approx(200.0), pytest.approx(208.0)), \
        "face eave 18in down-slope of the face (y=190+18)"
