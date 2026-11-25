"""The pyramid-roof calculator and its kind (0367 stage 1) --
`floorplanner/parametric/pyramid_geometry.py` and `pyramids.py`. Pure: no
scene, no window. The kind is BUILT but NOT REGISTERED in stage 1."""
import math

import pytest

from floorplanner.parametric import findings as F
from floorplanner.parametric import pyramid_geometry as pg
from floorplanner.parametric import registry
from floorplanner.parametric.pyramids import PYRAMID_ROOF

pytestmark = [pytest.mark.furnishings, pytest.mark.geometry]


def _st(**over):
    return pg.normalize_state(over)


# -- geometry ---------------------------------------------------------------
def test_defaults_are_a_hexagon_whose_apex_is_derived():
    st = _st()
    assert st["sides"] == 6 and st["eaves_bind"] == "room_top" and st["weld"] == "auto"
    assert st["inradius_in"] == 72.0 and st["pitch_12"] == 10.0
    # apex = eaves + inradius * pitch / 12
    assert pg.apex_height(st) == pytest.approx(96.0 + 72.0 * 10.0 / 12.0)
    assert pg.apex_height(st) == pytest.approx(156.0)
    # the eave is below the wall line by the overhang's fall
    assert pg.eave_height(st) == pytest.approx(96.0 - 12.0 * 10.0 / 12.0)


def test_normalize_clamps_sides_falls_back_and_keeps_unknowns():
    assert _st(sides=2)["sides"] == 3 and _st(sides=99)["sides"] == 12
    assert _st(sides=7.6)["sides"] == 8          # rounds to an int in range
    st = pg.normalize_state({"sides": "many", "pitch_12": "steep",
                             "inradius_in": float("nan"), "weld": "glue",
                             "eaves_bind": "sky", "note": "keep me"})
    assert st["sides"] == 6 and st["pitch_12"] == 10.0
    assert st["inradius_in"] == 72.0 and st["weld"] == "auto"
    assert st["eaves_bind"] == "room_top" and st["note"] == "keep me"
    assert pg.normalize_state({"inradius_in": 0.0})["inradius_in"] == pg.MIN_INRADIUS_IN
    assert pg.is_pyramid_roof_state(st)
    assert not pg.is_pyramid_roof_state({"form": "gable"})


def test_the_two_polygons_are_regular_and_the_eave_is_the_overhang_out():
    st = _st(sides=4, inradius_in=72.0, overhang_in=12.0)
    wall = pg.wall_polygon(st)
    eaves = pg.eaves_polygon(st)
    assert len(wall) == 4 and len(eaves) == 4
    # a square: wall-line corners at (+-72, +-72); circumradius = 72/cos45
    assert pg.circumradius(st) == pytest.approx(72.0 / math.cos(math.pi / 4))
    for x, y in wall:
        assert abs(abs(x) - 72.0) < 1e-6 and abs(abs(y) - 72.0) < 1e-6
    # the eave polygon is the same shape, one apothem bigger by the overhang:
    # every corner moves out by overhang / cos(pi/n)
    r_wall = min(math.hypot(*p) for p in wall)
    r_eave = min(math.hypot(*p) for p in eaves)
    assert r_eave - r_wall == pytest.approx(12.0 / math.cos(math.pi / 4))


def test_surface_height_is_the_apex_at_the_centre_and_eaves_at_the_wall():
    st = _st()
    r = st["inradius_in"]
    assert pg.surface_height(st, (0.0, 0.0)) == pytest.approx(pg.apex_height(st))
    # at the wall-line midpoint of face 0 (straight up), height is the eaves
    nx, ny = pg.face_normals(st)[0]
    assert pg.surface_height(st, (nx * r, ny * r)) == pytest.approx(st["eaves_h_in"])
    # out at the eave, lower still; past the eave there is no roof
    reach = r + st["overhang_in"]
    assert pg.surface_height(st, (nx * reach, ny * reach)) == pytest.approx(pg.eave_height(st))
    assert pg.surface_height(st, (nx * (reach + 10.0), ny * (reach + 10.0))) is None
    # every face is the same: the height one inradius out along each normal is
    # the eaves height, whichever face
    for nx, ny in pg.face_normals(st):
        assert pg.surface_height(st, (nx * r, ny * r)) == pytest.approx(st["eaves_h_in"])


def test_face_at_picks_the_governing_face_and_there_is_one_per_side():
    st = _st(sides=5)
    assert len(pg.face_normals(st)) == 5
    for k, (nx, ny) in enumerate(pg.face_normals(st)):
        assert pg.face_at(st, (nx * 50.0, ny * 50.0)) == k


def test_hips_run_from_the_apex_to_each_eave_corner():
    st = _st(sides=6)
    hips = pg.hips(st)
    corners = pg.eaves_polygon(st)
    assert len(hips) == 6
    for (a, b), corner in zip(hips, corners, strict=True):
        assert a == (0.0, 0.0) and b == corner


def test_face_planes_spring_from_the_eave_corners_up_to_the_apex():
    st = _st(sides=6)
    faces = pg.face_planes(st)
    assert len(faces) == 6
    apex = (0.0, 0.0, pg.apex_height(st))
    ez = pg.eave_height(st)
    for f in faces:
        assert f["tri"][0] == apex
        assert f["tri"][1][2] == pytest.approx(ez) and f["tri"][2][2] == pytest.approx(ez)
        assert len(f["wall_edge"]) == 2


def test_rotation_zero_is_identity_and_face0_points_up_turning_clockwise():
    st = _st()
    assert pg.to_plan((10.0, 20.0), 0.0, (3.0, 4.0)) == pytest.approx((13.0, 24.0))
    n0 = pg.face_normals(st)[0]
    assert n0 == pytest.approx((0.0, -1.0))                 # up the screen (plan -y)
    up = pg.face_normal_plan(0.0, n0)
    assert up == pytest.approx((0.0, -1.0))
    east = pg.face_normal_plan(90.0, n0)                    # clockwise: up -> east
    assert east == pytest.approx((1.0, 0.0))


def test_to_local_inverts_to_plan():
    for rot in (0.0, 37.0, 180.0, 300.0):
        p = pg.to_plan((5.0, -7.0), rot, (12.0, 9.0))
        back = pg.to_local((5.0, -7.0), rot, p)
        assert back == pytest.approx((12.0, 9.0))


# -- the kind ---------------------------------------------------------------
def test_the_kind_is_built_but_not_registered():
    assert PYRAMID_ROOF.kind == "pyramid_roof"
    assert registry.get("pyramid_roof") is None
    assert not registry.is_parametric("pyramid_roof")


def test_specs_cover_the_state_and_eaves_height_is_manual_only():
    keys = {s.key for s in PYRAMID_ROOF.specs()}
    assert {"sides", "inradius_in", "eaves_bind", "eaves_h_in", "pitch_12",
            "overhang_in", "weld"} <= keys
    by = {s.key: s for s in PYRAMID_ROOF.specs()}
    assert not by["eaves_h_in"].enabled({"eaves_bind": "room_top"})
    assert by["eaves_h_in"].enabled({"eaves_bind": "manual"})


def test_normalize_adds_the_derived_apex_and_to_state_is_the_stored_keys():
    norm = PYRAMID_ROOF.normalize({"sides": 8, "pitch_12": 12.0})
    assert norm["sides"] == 8
    assert norm["apex_h_in"] == pytest.approx(pg.apex_height(norm))
    stored = PYRAMID_ROOF.to_state({"sides": 8, "pitch_12": 12.0, "junk": 1})
    assert set(stored) == set(pg.STATE_DEFAULTS) and "apex_h_in" not in stored


def test_evaluate_binds_the_eaves_to_the_room_ceiling():
    derived, _ = PYRAMID_ROOF.evaluate({"eaves_bind": "room_top"},
                                       {"ceiling_in": 108.0, "room_present": True})
    assert derived["eaves_bound"] and derived["eaves_h_in"] == pytest.approx(108.0)
    assert derived["apex_h_in"] == pytest.approx(108.0 + 72.0 * 10.0 / 12.0)
    # manual ignores the ceiling
    derived, _ = PYRAMID_ROOF.evaluate({"eaves_bind": "manual", "eaves_h_in": 90.0},
                                       {"ceiling_in": 108.0, "room_present": True})
    assert not derived["eaves_bound"] and derived["eaves_h_in"] == pytest.approx(90.0)


def test_findings_name_no_room_off_room_buried_and_a_flat_pitch():
    _, f = PYRAMID_ROOF.evaluate({}, {"room_present": False})
    assert any(x.rule_id == "pyramid.no_room" and x.severity == F.WARNING for x in f)
    _, f = PYRAMID_ROOF.evaluate({"inradius_in": 72.0}, {"off_room_in": 24.0})
    assert any(x.rule_id == "pyramid.off_room" and x.severity == F.ADVISORY for x in f)
    _, f = PYRAMID_ROOF.evaluate({}, {"buried": True})
    assert any(x.rule_id == "pyramid.buried" and x.severity == F.ADVISORY for x in f)
    _, f = PYRAMID_ROOF.evaluate({"pitch_12": 0.0}, {})
    flat = [x for x in f if x.rule_id == "pyramid.flat"]
    assert flat and flat[0].severity == F.ERROR and flat[0].overridable


def test_summary_reports_the_plan_apex_and_pitch():
    derived, _ = PYRAMID_ROOF.evaluate({}, {"room_present": True, "ceiling_in": 96.0})
    labels = {label for label, _ in PYRAMID_ROOF.summary({}, derived, {})}
    assert {"Plan", "Eaves height", "Apex height", "Pitch", "Weld"} <= labels
    assert PYRAMID_ROOF.summary({}, None, {}) == [("Result", "cannot be built")]


def test_footprint_is_the_eave_bounding_box():
    assert PYRAMID_ROOF.footprint({"sides": 4, "inradius_in": 72.0, "overhang_in": 12.0}) \
        == pytest.approx(pg.bbox(_st(sides=4, inradius_in=72.0, overhang_in=12.0)))
