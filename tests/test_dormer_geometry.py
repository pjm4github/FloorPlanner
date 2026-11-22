"""The dormer calculator and its kind (0352, phase 1) --
`floorplanner/parametric/dormer_geometry.py` and `dormers.py`. Pure: no
scene, no window. The last test cross-checks the roof code's own reader."""
import importlib.util
import math
from pathlib import Path

import pytest

from floorplanner.parametric import dormer_geometry as dg
from floorplanner.parametric import findings as F
from floorplanner.parametric import registry
from floorplanner.parametric.dormers import DORMER

pytestmark = [pytest.mark.furnishings, pytest.mark.geometry]

ROOT = Path(__file__).resolve().parents[1]
HOST = (30.0, 10.0 / 12.0)        # 30 in up at the face, rising 10 in 12


def _st(**over):
    return dg.normalize_state(over)


def test_defaults_are_a_ten_foot_gable_at_10_in_12():
    st = _st()
    assert (st["form"], st["symmetric"]) == ("gable", True)
    assert dg.spans(st) == (60.0, 60.0)
    assert dg.ridge_height(st) == pytest.approx(60.0 + 60.0 * 10.0 / 12.0)
    assert dg.slopes(st) == pytest.approx((10.0 / 12.0, 10.0 / 12.0))


def test_symmetric_copies_the_left_side_and_free_keeps_both():
    st = _st(span_left_in=72.0, span_right_in=40.0, eave_overhang_left_in=6.0)
    assert st["span_right_in"] == 72.0 and st["eave_overhang_right_in"] == 6.0
    free = _st(symmetric=False, span_left_in=72.0, span_right_in=40.0)
    assert dg.spans(free) == (72.0, 40.0)
    sl, sr = dg.slopes(free)
    assert sl * 72.0 == pytest.approx(sr * 40.0), "one ridge, one eaves height"


def test_a_shed_rises_from_the_face_to_a_back_ridge_on_the_host():
    # The new shed (Patrick, 2026-11-18): one plane LEVEL across the width,
    # rising from the FACE back to a high ridge at the back where it meets the
    # host; two symmetric side walls; the only host contact is the back ridge.
    st = _st(form="shed", eaves_h_in=84.0, pitch_12=8.0, symmetric=True)
    assert st["span_right_in"] == st["span_left_in"], "a shed keeps both sides"
    assert dg.slopes(st) == pytest.approx((8.0 / 12.0, 8.0 / 12.0)), "one slope, along depth"
    # it meets a steeper host at a single back depth; no side valleys
    depth, back, met = dg.shed_back(st, 48.0, 0.79)
    assert met and depth == pytest.approx((84.0 - 48.0) / (0.79 - 8.0 / 12.0))
    assert back == pytest.approx(84.0 + (8.0 / 12.0) * depth)
    assert dg.valley_lines(st, 48.0, 0.79) == {}
    assert dg.back_height(st, 48.0, 0.79) == pytest.approx(back)
    # one knee line, ACROSS the width, where the plane crosses the ceiling
    knees = dg.knee_lines(st, 96.0, 48.0, 0.79)
    assert len(knees) == 1
    (x0, y), (x1, _y) = knees[0]
    assert x0 == pytest.approx(-st["span_right_in"]) and x1 == pytest.approx(st["span_left_in"])
    assert y == pytest.approx((96.0 - 84.0) / (8.0 / 12.0))


def test_bad_values_fall_back_and_unknown_keys_survive():
    st = dg.normalize_state({"form": "mansard", "pitch_12": "steep",
                             "span_left_in": float("nan"), "note": "keep me"})
    assert st["form"] == "gable" and st["pitch_12"] == 10.0
    assert st["span_left_in"] == 60.0 and st["note"] == "keep me"
    assert dg.normalize_state({"span_left_in": 0.0})["span_left_in"] == dg.MIN_SPAN_IN
    assert dg.is_dormer_state(st) and not dg.is_dormer_state({"type": "U"})


def test_the_ridge_runs_until_it_meets_the_host():
    st = _st()
    depth, met = dg.ridge_depth(st, *HOST)
    assert met and depth == pytest.approx((110.0 - 30.0) / (10.0 / 12.0))
    assert dg.ridge_depth(st) == (96.0, False), "no host: the stored length"
    assert dg.ridge_depth(st, 30.0, 0.0) == (96.0, False), "a level host"
    assert dg.ridge_depth(st, 200.0, 10.0 / 12.0) == (0.0, True), "buried"


def test_valleys_start_at_the_cheek_and_end_at_the_ridge_end():
    st = _st()                                   # eaves 60, host 30 at the face
    v = dg.valley_lines(st, *HOST)
    depth = dg.ridge_depth(st, *HOST)[0]
    (xl, yl), end = v["left"]
    assert end == (0.0, depth)
    assert xl == 60.0, "the eave is above the host at the face: a cheek"
    assert yl == pytest.approx((60.0 - 30.0) / (10.0 / 12.0)), \
        "the valley starts where the host reaches the eaves height"
    assert v["right"][0] == (-60.0, yl)
    low = dg.valley_lines(_st(eaves_h_in=20.0), 30.0, 10.0 / 12.0)
    (x, y), _end = low["left"]
    assert y == 0.0 and x < 60.0, "eaves under the host: the valley starts on the face"
    assert dg.valley_lines(st) == {}


def test_knee_lines_sit_where_the_plane_crosses_the_ceiling():
    st = _st()                                   # ridge 110
    knees = dg.knee_lines(st, 97.0, *HOST)
    assert len(knees) == 2
    (x, y0), (x1, y1) = knees[0]
    assert x == x1 == pytest.approx((110.0 - 97.0) / (10.0 / 12.0))
    assert y0 == 0.0
    assert y1 == pytest.approx((97.0 - 30.0) / (10.0 / 12.0)), \
        "it ends on the valley: the host is at the ceiling height there too"
    assert dg.surface_height(st, x) == pytest.approx(97.0)
    assert knees[1][0][0] == -x
    assert dg.full_height_width(st, 97.0) == pytest.approx(2 * x)


def test_no_knee_line_above_the_ridge_or_below_the_eaves():
    st = _st()
    assert dg.knee_lines(st, 110.0, *HOST) == [], "ceiling at the ridge"
    assert dg.full_height_width(st, 120.0) == 0.0
    assert dg.knee_lines(st, 60.0, *HOST) == [], "ceiling at the eaves: full height"
    assert dg.full_height_width(st, 60.0) == 120.0
    assert dg.knee_lines(st, 50.0, *HOST) == []


def test_a_knee_line_moves_with_the_pitch_and_the_eaves():
    """The spec's own use: the user sizes the dormer to put the line where
    the wall will go."""
    base = dg.knee_lines(_st(), 97.0, *HOST)[0][0][0]
    steeper = dg.knee_lines(_st(pitch_12=12.0), 97.0, *HOST)[0][0][0]
    higher = dg.knee_lines(_st(eaves_h_in=72.0), 97.0, *HOST)[0][0][0]
    assert steeper > base and higher > base


def test_knee_lines_without_a_host_run_the_stored_length():
    knees = dg.knee_lines(_st(), 97.0)
    assert knees[0][1][1] == 96.0


@pytest.mark.parametrize("rotation,want", [(0.0, (0.0, -1.0)), (90.0, (1.0, 0.0)),
                                           (180.0, (0.0, 1.0)), (270.0, (-1.0, 0.0))])
def test_rotation_turns_the_ridge_clockwise_on_screen(rotation, want):
    assert dg.ridge_direction(rotation) == pytest.approx(want, abs=1e-12)


def test_local_and_plan_round_trip_and_left_is_the_roof_codes_left():
    pos = (534.0, 816.0)
    for rot in (0.0, 37.0, 90.0, 180.0, 233.0):
        for pt in ((0.0, 0.0), (15.0, 40.0), (-22.0, 3.0)):
            assert dg.to_local(pos, rot, dg.to_plan(pos, rot, pt)) == \
                pytest.approx(pt, abs=1e-9)
        ux, uy = dg.ridge_direction(rot)
        left = dg.to_plan(pos, rot, (1.0, 0.0))
        assert (left[0] - pos[0], left[1] - pos[1]) == pytest.approx((-uy, ux))


def test_the_footprint_takes_its_overhangs():
    st = _st(eave_overhang_left_in=12.0, face_overhang_in=18.0)
    fp = dg.footprint(st, 80.0)
    assert fp == [(-72.0, -18.0), (72.0, -18.0), (72.0, 80.0), (-72.0, 80.0)]


def test_guides_default_to_the_eaves_line_and_never_pass_it():
    assert dg.guides(_st())[:2] == (60.0, 60.0)
    assert dg.guides(_st(guide_left_in=40.0))[:2] == (40.0, 40.0)
    assert dg.guides(_st(guide_left_in=400.0))[0] == 60.0
    p = dg.plan(_st(), 97.0, *HOST)
    assert len(p["guides"]) == 2 and len(p["valleys"]) == 2 and len(p["knees"]) == 2


def test_the_roof_record_round_trips_through_the_old_shape():
    st = _st(symmetric=False, span_left_in=72.0, span_right_in=48.0,
             eaves_h_in=66.0, pitch_12=9.0, face_overhang_in=14.0,
             guide_left_in=50.0)
    rec = dg.to_roof_record(st, (300.0, 700.0), 180.0, 88.0, datum_shift=134.0,
                            id="rf9", level="L2", host="rf1")
    assert rec["ridge"][0] == [300.0, 700.0]
    assert rec["ridge"][1] == pytest.approx([300.0, 788.0])
    assert rec["eaves_h_in"] == 200.0 and rec["host"] == "rf1"
    assert rec["dormer_walls"] == [] and rec["marker_end"] == 0
    back, pos, rot, depth = dg.from_roof_record(rec, datum_shift=134.0)
    assert pos == (300.0, 700.0) and rot == pytest.approx(180.0)
    assert depth == pytest.approx(88.0)
    assert (back["form"], back["symmetric"]) == (st["form"], st["symmetric"])
    for key in ("span_left_in", "span_right_in", "eaves_h_in",
                "face_overhang_in", "guide_left_in"):
        assert back[key] == pytest.approx(st[key]), key
    assert back["pitch_12"] == pytest.approx(9.0)


def test_an_old_dormer_record_converts():
    """One of Patrick's own: the Nov 15 seed's front dormer."""
    old = {"id": "rf5", "level": "L2", "ridge": [[360.0, 864.0], [360.0, 721.0]],
           "eaves_h_in": 125.0, "ridge_h_in": 275.0, "overhang_in": [10.0, 10.0],
           "span_in": [150.0, 150.0], "gable": [True, True], "host": "rf1",
           "end_overhang_in": [12.0, 0.0], "wall_span_in": [84.0, 78.0],
           "box_half_in": [111.6, 120.0]}
    st, pos, rot, depth = dg.from_roof_record(old)
    assert pos == (360.0, 864.0) and rot == pytest.approx(0.0)
    assert depth == 143.0 and st["pitch_12"] == pytest.approx(12.0)
    assert st["symmetric"] is False, "its two side guides differ"
    assert (st["guide_left_in"], st["guide_right_in"]) == (84.0, 78.0)
    assert dg.ridge_height(st) == pytest.approx(275.0)


def test_host_plane_reads_a_surface_callable():
    def surface(p):                       # a plane rising toward plan -y
        return 30.0 + (816.0 - p[1]) * 0.75
    z, slope = dg.host_plane(surface, (534.0, 816.0), dg.ridge_direction(0.0))
    assert (z, slope) == pytest.approx((30.0, 0.75))


def test_host_extent_places_the_eave_and_ridge_along_the_ridge():
    # P1 (2026-11-18): the host's eave and ridge as signed Y from the face.
    # face 60 above this level, host rises 1 in / in, ridge 120, eave 48.
    ext = dg.host_extent(host_z_face=60.0, host_slope=1.0,
                         host_ridge_in=120.0, host_eave_in=48.0)
    assert ext["ridge_y"] == pytest.approx(60.0)   # 60 up to the host ridge
    assert ext["eave_y"] == pytest.approx(-12.0)   # 12 down to the host eave
    # a face already below the eave height hangs past it -> eave_y > 0
    hang = dg.host_extent(host_z_face=40.0, host_slope=1.0, host_eave_in=48.0)
    assert hang["eave_y"] == pytest.approx(8.0) and hang["ridge_y"] is None
    # no host, or a host that does not rise along the ridge -> None
    assert dg.host_extent() is None
    assert dg.host_extent(host_z_face=60.0, host_slope=0.0) is None


def test_face_type_cantilever_is_the_FACE_past_the_host_eave():
    # P4 (2026-11-18): the FACE (not the eave overhang) past the host eave is a
    # cantilever. host: slope 1, eave 48. face_vs_host_eave > 0 = roof in front.
    st = _st()
    assert dg.face_vs_host_eave(st, 60.0, 1.0, 48.0) == pytest.approx(12.0)
    assert dg.face_type(st, 60.0, 1.0, 48.0) == dg.FACE_STANDARD
    assert dg.face_past_eave(st, 40.0, 1.0, 48.0) == pytest.approx(8.0)
    assert dg.face_type(st, 40.0, 1.0, 48.0) == dg.FACE_CANTILEVER
    assert dg.face_type(st) == dg.FACE_STANDARD          # no host


def test_classify_face_reads_the_four_types():
    st = _st()
    assert dg.classify_face(st, 40.0, 1.0, 48.0)[0] == dg.FACE_CANTILEVER   # past
    assert dg.classify_face(st, 50.0, 1.0, 48.0, wall_below=True)[0] == dg.FACE_WALL
    assert dg.classify_face(st, 90.0, 1.0, 48.0)[0] == dg.FACE_SETBACK      # roof in front
    t, ok = dg.classify_face(st, 90.0, 1.0, 48.0, choice="balcony")
    assert t == dg.FACE_BALCONY and ok
    _t, ok2 = dg.classify_face(st, 50.0, 1.0, 48.0, wall_below=False, choice="plain_wall")
    assert not ok2, "plain wall needs a wall below"
    assert dg.classify_face(st)[0] == dg.FACE_STANDARD   # no host


def test_the_cantilever_boundary_is_the_fascia_not_the_wall():
    # 0360 stage 3 (Patrick 2026-11-22): a cantilever is the face PAST the host
    # roof EDGE, not the wall. host_eave_in is the WALL line; the fascia is
    # host_overhang_in farther downhill, so a face past the wall but short of the
    # fascia is NOT a cantilever once the overhang is known.
    st = _st()
    assert dg.classify_face(st, 40.0, 1.0, 48.0)[0] == dg.FACE_CANTILEVER  # past the wall
    # with a 20in host overhang the fascia is 20in farther out: the same face
    # now reads as host-roof-in-front (setback), not a cantilever.
    assert dg.classify_face(st, 40.0, 1.0, 48.0, host_overhang_in=20.0)[0] == dg.FACE_SETBACK
    assert dg.face_past_eave(st, 40.0, 1.0, 48.0, 20.0) == pytest.approx(-12.0)  # lands on


def test_skirt_available_is_the_A_vs_C_axis_with_a_vertical_check():
    # Table 2 notes 4/7b: available when host roof is in front in plan (A>C);
    # at A==C a zero-width edge (no); at A<C only if the fascia is below the
    # dormer eave so a skirt can bridge (an elevation the ordering lacks).
    st = _st()
    assert dg.skirt_available(st, 90.0, 1.0, 48.0) is True          # A > C: roof in front
    assert dg.skirt_available(st, 48.0, 1.0, 48.0) is False         # A == C: zero width
    assert dg.skirt_available(st, 40.0, 1.0, 48.0) is False         # A < C, no elevation known
    # A < C, fascia (48) below the dormer eave (100) -> a skirt can bridge
    assert dg.skirt_available(st, 40.0, 1.0, 48.0, dormer_eave_z=100.0) is True
    # A < C, fascia (48) NOT below the dormer eave (40) -> no skirt
    assert dg.skirt_available(st, 40.0, 1.0, 48.0, dormer_eave_z=40.0) is False
    assert dg.skirt_available(st) is False                          # no host


def test_skirt_mode_normalises_to_the_enum():
    assert _st()["skirt_mode"] == "auto"
    assert _st(skirt_mode="on")["skirt_mode"] == "on"
    assert _st(skirt_mode="off")["skirt_mode"] == "off"
    assert _st(skirt_mode="banana")["skirt_mode"] == "auto"   # unknown -> auto


def test_a_cantilever_face_is_derived_and_noted():
    # a short-run face (depth 40) with ridge 180 derives z_face = 180 - 40 = 140,
    # which is UP the roof; push the face past the eave with a long run instead.
    ctx = {"host_z_face_in": 40.0, "host_slope": 1.0, "host_eave_in": 48.0}
    d, fs = DORMER.evaluate({}, ctx)
    assert d["face_type"] == dg.FACE_CANTILEVER
    assert any(f.rule_id == "dormer.cantilever" for f in fs) and not F.blocks(fs)
    d2, _fs2 = DORMER.evaluate({}, {"host_z_face_in": 90.0, "host_slope": 1.0,
                                    "host_eave_in": 48.0})
    assert d2["face_type"] == dg.FACE_SETBACK


# -- the kind ---------------------------------------------------------------
def test_the_kind_is_registered_and_offered():
    # phase 2 (0352): the kind is REGISTERED now that DormerItem draws one and
    # the catalog offers it in the Framing group (was withheld in phase 1).
    assert DORMER.kind == "dormer" and DORMER.specs()
    assert registry.get("dormer") is DORMER, "the DORMER kind must be registered"
    assert set(DORMER.to_state({})) == set(dg.STATE_DEFAULTS)


def test_on_a_roof_with_a_ceiling_it_reports_the_knee_lines_and_no_finding():
    ctx = {"ceiling_in": 97.0, "host_z_face_in": 30.0, "host_slope": 10.0 / 12.0,
           "host_ridge_in": 140.0}
    derived, fs = DORMER.evaluate({}, ctx)
    assert fs == [] and derived["on_roof"]
    assert derived["full_height_in"] == pytest.approx(31.2)
    rows = dict(DORMER.summary({}, derived, ctx))
    assert "31.2 in wide" in rows["Full height under it"]
    assert "15.6 in from the ridge" in rows["Knee line, left"]


@pytest.mark.parametrize("ctx,rule,severity", [
    ({}, "dormer.no_host", F.WARNING),
    ({"host_z_face_in": 200.0, "host_slope": 0.8}, "dormer.buried", F.WARNING),
    ({"host_z_face_in": 30.0, "host_slope": 0.8, "ceiling_in": 120.0},
     "dormer.no_full_height", F.ADVISORY),
])
def test_findings(ctx, rule, severity):
    _derived, fs = DORMER.evaluate({}, ctx)
    by = {f.rule_id: f for f in fs}
    assert by[rule].severity == severity
    assert not F.blocks(fs), "a dormer in the wrong place can still be placed"


def test_only_a_flat_dormer_is_refused():
    derived, fs = DORMER.evaluate({"pitch_12": 0.0}, {})
    assert derived is None and F.blocks(fs) and fs[0].field == "pitch_12"


def test_the_spec_keys_are_all_state_keys():
    # every spec maps to a stored key, EXCEPT `ridge_h_in` -- a dialog input
    # that floats the eaves; `to_state` drops it (test_..._floats_the_eaves).
    assert {s.key for s in DORMER.specs()} <= set(dg.STATE_DEFAULTS) | {"ridge_h_in"}
    by = {s.key: s for s in DORMER.specs()}
    # symmetric is editable for a shed too now; the right side follows the left
    # until asymmetric, for BOTH forms (Patrick, 2026-11-18).
    assert by["symmetric"].enabled({"form": "shed"})
    assert not by["span_right_in"].enabled({"symmetric": True})
    assert by["span_right_in"].enabled({"form": "shed", "symmetric": False})
    assert by["span_right_in"].enabled({"form": "gable", "symmetric": False})


def test_ridge_is_the_anchor_last_edited_of_eaves_pitch_is_pinned():
    base = dg.normalize_state({})             # eaves 60, span 60, pitch 10 -> ridge 110
    assert dg.ridge_height(base) == pytest.approx(110.0)

    # EDIT PITCH -> the eaves give way, the ridge held
    p = DORMER.normalize({**base, "_edited": "pitch_12",
                          "ridge_h_in": 110.0, "pitch_12": 12.0})
    assert p["_pinned"] == "pitch_12" and p["pitch_12"] == pytest.approx(12.0)
    assert p["eaves_h_in"] == pytest.approx(110.0 - 60.0 * 12.0 / 12.0)   # 50
    assert dg.ridge_height(p) == pytest.approx(110.0), "ridge anchored"

    # EDIT EAVES -> the pitch gives way, the ridge held
    e = DORMER.normalize({**base, "_edited": "eaves_h_in",
                          "ridge_h_in": 110.0, "eaves_h_in": 80.0})
    assert e["_pinned"] == "eaves_h_in" and e["eaves_h_in"] == pytest.approx(80.0)
    assert e["pitch_12"] == pytest.approx((110.0 - 80.0) * 12.0 / 60.0)   # 6
    assert dg.ridge_height(e) == pytest.approx(110.0), "ridge anchored"

    # EDIT RIDGE after pitch was pinned -> the eaves give way (pitch held)
    r = DORMER.normalize({**p, "_edited": "ridge_h_in", "ridge_h_in": 134.0})
    assert r["pitch_12"] == pytest.approx(12.0), "pitch still pinned, held"
    assert r["eaves_h_in"] == pytest.approx(134.0 - 60.0 * 12.0 / 12.0)   # 74
    assert dg.ridge_height(r) == pytest.approx(134.0)

    # EDIT RIDGE after eaves was pinned -> the pitch gives way (eaves held)
    r2 = DORMER.normalize({**e, "_edited": "ridge_h_in", "ridge_h_in": 128.0})
    assert r2["eaves_h_in"] == pytest.approx(80.0), "eaves still pinned, held"
    assert r2["pitch_12"] == pytest.approx((128.0 - 80.0) * 12.0 / 60.0)  # 9.6
    assert dg.ridge_height(r2) == pytest.approx(128.0)


def test_all_three_height_fields_are_editable_and_the_virtual_key_is_dropped():
    by = {s.key: s for s in DORMER.specs()}
    assert by["ridge_h_in"].enabled({}) and by["eaves_h_in"].enabled({})
    assert by["pitch_12"].enabled({}), "ridge, eaves and pitch all editable"
    norm = DORMER.normalize({"_edited": "pitch_12", "ridge_h_in": 110.0,
                             "pitch_12": 12.0})
    st = DORMER.to_state(norm)                 # the virtual keys never store
    assert "ridge_h_in" not in st and "_pinned" not in st
    assert set(st) == set(dg.STATE_DEFAULTS)


def test_the_roof_codes_own_reader_agrees_with_this_calculator():
    """`roofclip.RoofGeom.from_record` on `to_roof_record`'s output gives the
    surface this module computes -- so the clipper and the dialog cannot
    disagree about where a dormer's roof is."""
    spec = importlib.util.spec_from_file_location(
        "roofclip_dormer_test", ROOT / "floorplanner" / "roofclip.py")
    rc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rc)
    st = _st(symmetric=False, span_left_in=72.0, span_right_in=48.0)
    pos, rot, depth = (400.0, 600.0), 30.0, 120.0
    geom = rc.RoofGeom.from_record(dg.to_roof_record(st, pos, rot, depth))
    for x, y in ((0.0, 10.0), (30.0, 40.0), (-20.0, 90.0), (71.0, 5.0)):
        px, py = dg.to_plan(pos, rot, (x, y))
        assert rc.surface_height(geom, rc.Pt(px, py)) == pytest.approx(
            dg.surface_height(st, x)), (x, y)
    assert math.isclose(geom.length(), depth)


def test_a_shed_dormers_roof_record_falls_along_the_depth_not_the_width():
    """A SHED is ONE plane: its high ridge is the back edge ACROSS the width,
    its slope falls along the DEPTH to the low face eave. `to_roof_record` once
    encoded every dormer the gable way (ridge down the depth, span across the
    width), which `RoofGeom`'s shed reader built 90 deg rotated (Patrick,
    2026-11-19). So the record's ridge must run across the width, its span be
    the depth, and the surface fall with the depth -- level across the width."""
    spec = importlib.util.spec_from_file_location(
        "roofclip_shed_test", ROOT / "floorplanner" / "roofclip.py")
    rc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rc)
    st = _st(form="shed", symmetric=False, span_left_in=48.0, span_right_in=36.0,
             eaves_h_in=100.0, pitch_12=6.0)
    pos, rot, depth = (400.0, 600.0), 0.0, 90.0
    rise = 6.0 / 12.0
    rec = dg.to_roof_record(st, pos, rot, depth)
    (x0, y0), (x1, y1) = rec["ridge"]
    assert abs(y1 - y0) < 1e-6, "the high ridge runs across the width (flat in y at rot 0)"
    assert abs(x1 - x0) == pytest.approx(48.0 + 36.0), "the full width"
    assert rec["span_in"] == [90.0, 0.0], "the span is the DEPTH, right plane gone"
    assert rec["ridge_h_in"] == pytest.approx(100.0 + rise * depth)
    geom = rc.RoofGeom.from_record(rec)
    assert math.isclose(geom.length(), 48.0 + 36.0), "the ridge spans the width"
    # RoofGeom's own surface: it falls along the depth (y), level across x
    for x, y in ((0.0, 0.0), (30.0, 0.0), (-20.0, 45.0), (10.0, 90.0)):
        px, py = dg.to_plan(pos, rot, (x, y))
        assert rc.surface_height(geom, rc.Pt(px, py)) == pytest.approx(
            100.0 + rise * y), (x, y)


# -- control D, the face guide (0355) ----------------------------------------
def test_the_side_guides_run_from_the_face_back_to_the_host():
    # P3 retirement (2026-11-18): the face guide D is gone -- the two side
    # guides (C) now start on the FACE (dg y = 0) and run to the depth.
    st = _st()
    assert len(dg.guides(st)) == 2, "guides() is (left, right) now"
    lines = dg.plan(st, None, *HOST)["guides"]
    assert len(lines) == 2, "two side guides, no face-guide line"
    assert lines[0][0][1] == 0.0 and lines[1][0][1] == 0.0, "they start on the face"
    assert "guide_face_in" not in dg.STATE_DEFAULTS
    assert "face_guide_in" not in dg.to_roof_record(_st(), (0.0, 0.0), 0.0, 96.0)


# -- the gable end and its openings (0356) -----------------------------------
def _op(x0, x1, sill, head, **more):
    return dict(x0=x0, x1=x1, sill_in=sill, head_in=head, **more)


def test_the_face_profile_is_the_gable_between_the_guides():
    prof = dg.face_profile(_st())                    # eaves 60, ridge 110
    assert prof["peak"] == (0.0, 110.0)
    assert prof["roof"] == [(-72.0, 50.0), (0.0, 110.0), (72.0, 50.0)]
    assert prof["wall"] == [(60.0, 0.0), (60.0, 60.0), (0.0, 110.0),
                            (-60.0, 60.0), (-60.0, 0.0)]
    shed = dg.face_profile(_st(form="shed"))         # a rectangular face + roof band
    back = dg.back_height(_st(form="shed"))          # 60 + (10/12)*96 = 140
    assert shed["peak"] == (0.0, pytest.approx(back))
    assert shed["wall"] == [(60.0, 0.0), (60.0, 60.0), (-60.0, 60.0), (-60.0, 0.0)]
    assert shed["roof"][0] == (72.0, 60.0) and shed["roof"][1] == (72.0, pytest.approx(back))


def test_a_window_above_the_ceiling_line_is_allowed_and_said():
    """Patrick, 0356: the gable may be higher than the ceiling on that
    floor, so a window up there is fine."""
    (op,) = dg.face_openings(_st(), [_op(-12.0, 12.0, 84.0, 98.0)], ceiling_in=97.0)
    assert op["above_ceiling"] is True and op["through_roof"] is False
    (low,) = dg.face_openings(_st(), [_op(-12.0, 12.0, 30.0, 80.0)], ceiling_in=97.0)
    assert low["above_ceiling"] is False


def test_an_opening_the_roof_line_cuts_is_flagged():
    st = _st()                                       # roof at x=30 is 85
    (ok,) = dg.face_openings(st, [_op(-30.0, 30.0, 30.0, 85.0)])
    assert ok["through_roof"] is False
    (cut,) = dg.face_openings(st, [_op(-30.0, 30.0, 30.0, 86.0)])
    assert cut["through_roof"] is True
    # the shed FRONT caps at the eaves (60): a head above it cuts the roof band
    (shed_cut,) = dg.face_openings(_st(form="shed"), [_op(-20.0, 10.0, 30.0, 70.0)])
    assert shed_cut["through_roof"] is True, "the shed face caps at the eaves"
    (shed_ok,) = dg.face_openings(_st(form="shed"), [_op(-20.0, 10.0, 30.0, 58.0)])
    assert shed_ok["through_roof"] is False


def test_stacked_openings_do_not_overlap_but_crossing_ones_do():
    """Patrick, 0356: an octagon at the peak with a window under it."""
    lower = _op(-18.0, 18.0, 24.0, 72.0, id="o1", kind="window", code="3648")
    upper = _op(-9.0, 9.0, 80.0, 98.0, id="o2", kind="window", shape="octagon")
    ops = dg.face_openings(_st(), [upper, lower], ceiling_in=97.0)
    assert [o["id"] for o in ops] == ["o1", "o2"], "bottom to top"
    assert all(o["overlaps"] == [] and not o["through_roof"] for o in ops)
    assert ops[1]["shape"] == "octagon" and ops[1]["above_ceiling"]
    clash = dg.face_openings(_st(), [lower, _op(-9.0, 9.0, 60.0, 90.0, id="o3")])
    assert clash[0]["overlaps"] == ["o3"] and clash[1]["overlaps"] == ["o1"]


def test_an_octagon_fits_higher_than_its_box_would():
    st = _st()
    box = _op(-12.0, 12.0, 80.0, 104.0)             # roof at x=12 is 100
    assert dg.face_openings(st, [box])[0]["through_roof"] is True
    assert dg.face_openings(st, [dict(box, shape="octagon")])[0]["through_roof"] is False
    assert dg.face_openings(st, [dict(box, shape="star")])[0]["shape"] == "rect"


def test_an_opening_off_the_face_wall_is_flagged():
    ops = dg.face_openings(_st(), [_op(30.0, 50.0, 30.0, 60.0)], wall_span=(-40.0, 40.0))
    assert ops[0]["off_wall"] is True
    assert dg.face_openings(_st(), [_op(30.0, 50.0, 30.0, 60.0)])[0]["off_wall"] is False


def test_a_wall_under_the_face_projects_and_others_do_not():
    pos, rot = (534.0, 816.0), 0.0                   # ridge up the screen
    assert dg.project_wall(pos, rot, (474.0, 816.0), (594.0, 816.0)) == \
        pytest.approx((-60.0, 60.0))
    assert dg.project_wall(pos, rot, (594.0, 818.0), (474.0, 818.0)) == \
        pytest.approx((60.0, -60.0)), "drawn the other way, 2 in off: still it"
    assert dg.project_wall(pos, rot, (474.0, 780.0), (594.0, 780.0)) is None
    assert dg.project_wall(pos, rot, (474.0, 780.0), (594.0, 780.0),
                           guide_face=36.0) is not None, "on the face GUIDE"
    assert dg.project_wall(pos, rot, (534.0, 816.0), (534.0, 700.0)) is None, \
        "a side wall is not a face wall"


def test_wall_openings_project_into_face_coordinates_either_way_round():
    ops = [{"s0": 42.0, "s1": 78.0, "sill_in": 24.0, "head_in": 72.0, "code": "3648"}]
    (a,) = dg.project_openings(-60.0, 60.0, 120.0, ops)
    assert (a["x0"], a["x1"], a["code"]) == (-18.0, 18.0, "3648") and "s0" not in a
    (b,) = dg.project_openings(60.0, -60.0, 120.0,
                               [dict(ops[0], s0=30.0, s1=66.0)])
    assert (b["x0"], b["x1"]) == (-6.0, 30.0)
    assert dg.project_openings(0.0, 0.0, 0.0, ops) == []


def test_the_kind_reports_the_face_and_its_findings():
    ctx = {"ceiling_in": 97.0, "host_z_face_in": 30.0, "host_slope": 10.0 / 12.0,
           "face_wall": (-60.0, 60.0),
           "face_openings": [_op(-18.0, 18.0, 24.0, 72.0, id="o1", kind="window",
                                 code="3648"),
                             _op(-9.0, 9.0, 80.0, 98.0, id="o2", kind="window",
                                 shape="octagon")]}
    derived, fs = DORMER.evaluate({}, ctx)
    assert fs == [], "stacked, one in the gable above the ceiling: no finding"
    rows = dict(DORMER.summary({}, derived, ctx))
    assert rows["Openings in the face"].startswith("2, 1 above the ceiling line")
    ctx["face_openings"].append(_op(40.0, 58.0, 30.0, 90.0, id="o3", kind="window",
                                    code="1860"))
    _d, fs = DORMER.evaluate({}, ctx)
    assert [f.rule_id for f in fs] == ["dormer.opening_through_roof"]
    assert not F.blocks(fs)
    _d, fs = DORMER.evaluate({}, {"face_wall": None})
    assert "dormer.face_open" in {f.rule_id for f in fs}
    _d, fs = DORMER.evaluate({}, {})
    assert "dormer.face_open" not in {f.rule_id for f in fs}, "nobody looked"


# -- the two sides (0356, Patrick: "gable end and both sides") ---------------
def test_a_side_wall_runs_from_the_face_to_where_the_host_reaches_its_top():
    st = _st()                                   # side guide at 60: top = eaves 60
    prof = dg.side_profile(st, "left", *HOST)
    assert prof["top"] == 60.0 and dg.side_x(st, "left") == 60.0
    assert prof["span"] == pytest.approx((0.0, (60.0 - 30.0) / (10.0 / 12.0)))
    assert prof["host"][0] == (0.0, 30.0)
    assert prof["host"][1] == pytest.approx((36.0, 60.0)), "the host meets the top"
    assert prof["roof"][0] == (-12.0, 60.0), "the eave runs out over the face"
    free = dg.side_profile(st, "left")
    assert free["host"] is None and free["span"] == (0.0, 96.0)
    # the side wall starts on the FACE now (the face guide D is retired)
    inset = dg.side_profile(_st(guide_left_in=30.0), "right", *HOST)
    assert inset["top"] == pytest.approx(85.0) and inset["span"][0] == 0.0


def test_the_side_shows_the_dormer_roof_as_a_hidden_true_projection():
    st = _st()                                   # ridge 110, eaves/top 60, overhang 12
    prof = dg.side_profile(st, "left", *HOST)
    rh, ridge = dg.ridge_height(st), prof["ridge"]
    assert ridge[0] == (-12.0, 60.0), "front eave corner, out over the face"
    assert ridge[1] == (-12.0, rh), "up the front rake to the ridge, over the face"
    assert ridge[2] == pytest.approx((96.0, rh)), "ridge back to where it meets the host"
    assert ridge[3] == pytest.approx((36.0, 60.0)), "down the host roof to the eave meet"
    for y, z in (ridge[2], ridge[3]):            # the back two legs lie ON the host
        assert z == pytest.approx(30.0 + (10.0 / 12.0) * y)
    free = dg.side_profile(st, "left")           # no host: the back squares off
    assert free["ridge"][2][0] == free["ridge"][3][0] == st["depth_in"]


def test_a_shed_side_is_a_trapezoid_low_at_the_face_high_at_the_back():
    # the new shed side (Patrick, 2026-11-18): a trapezoid, eaves at the face
    # rising to the back ridge on the host; the roof is the visible sloping top
    # (no hidden ridge line), the host diagonal the reference.
    st = _st(form="shed", eaves_h_in=84.0, pitch_12=8.0)
    sp = dg.side_profile(st, "left", 48.0, 0.79)
    depth, back, _met = dg.shed_back(st, 48.0, 0.79)
    assert sp["ridge"] is None, "the shed roof is visible, not a hidden line"
    assert sp["wall"] == [(0.0, 0.0), (0.0, 84.0),
                          (pytest.approx(depth), pytest.approx(back)), (pytest.approx(depth), 0.0)]
    assert sp["roof"][1] == (pytest.approx(depth), pytest.approx(back))
    assert sp["host"][0] == (0.0, 48.0)          # host below the eaves at the face
    assert sp["host"][1] == (pytest.approx(depth), pytest.approx(back)), "meets at the back"


def test_a_wall_on_a_side_guide_projects_and_a_face_wall_does_not():
    pos, rot = (534.0, 816.0), 0.0
    assert dg.project_side_wall(pos, rot, (594.0, 816.0), (594.0, 780.0), 60.0) == \
        pytest.approx((0.0, 36.0))
    assert dg.project_side_wall(pos, rot, (474.0, 780.0), (474.0, 816.0), -60.0) == \
        pytest.approx((36.0, 0.0))
    assert dg.project_side_wall(pos, rot, (594.0, 816.0), (594.0, 780.0), -60.0) is None
    assert dg.project_side_wall(pos, rot, (474.0, 816.0), (594.0, 816.0), 60.0) is None


def test_side_openings_are_judged_against_the_eave_and_the_host():
    st = _st(eaves_h_in=84.0)                    # side top 84; host 30 + 10/12 y
    ops = dg.side_openings(st, "left", [_op(4.0, 28.0, 54.0, 80.0, id="s1"),
                                        _op(40.0, 60.0, 54.0, 90.0, id="s2")],
                           ceiling_in=97.0, host_z_face=30.0, host_slope=10.0 / 12.0)
    by = {o["id"]: o for o in ops}
    assert not by["s1"]["through_roof"] and not by["s1"]["behind_host"]
    assert by["s2"]["through_roof"], "its head is above the eave"
    assert by["s2"]["behind_host"], "the host is at 80 by y = 60: over its sill"
    assert "behind_host" in dg.side_openings(st, "left", [_op(0, 10, 0, 10)])[0]


def test_the_kind_reports_the_sides():
    ctx = {"ceiling_in": 97.0, "host_z_face_in": 30.0, "host_slope": 10.0 / 12.0,
           "face_wall": (-60.0, 60.0), "side_walls": {"left": (0.0, 36.0)},
           "side_openings": {"left": [_op(4.0, 28.0, 20.0, 50.0, id="s1",
                                          kind="window", code="2430")]}}
    derived, fs = DORMER.evaluate({}, ctx)
    assert derived["sides"]["left"]["wall"] == (0.0, 36.0)
    assert derived["sides"]["right"]["wall"] is None
    ids = [f.rule_id for f in fs]
    assert "dormer.side_open.right" in ids and "dormer.side_open.left" not in ids
    assert "dormer.opening_behind_roof" in ids, "sill 20 is under the host at y=28"
    assert dict(DORMER.summary({}, derived, ctx))["Openings in the left side"] == "1"
    derived, fs = DORMER.evaluate({}, {})
    assert not [f for f in fs if f.rule_id.startswith("dormer.side_open")]
    assert set(derived["sides"]) == {"left", "right"}


# -- the ridge may not stand above the host's (0359) -------------------------
@pytest.mark.parametrize("ctx,rule,why", [
    ({"host_z_face_in": 30.0, "host_slope": 0.8, "host_ridge_in": 100.0},
     "dormer.above_host_ridge", dg.OVER_RIDGE),
    ({"host_z_face_in": 30.0, "host_slope": 0.0, "host_ridge_in": 140.0},
     "dormer.level_host", dg.FACES_UPHILL),
    ({"host_z_face_in": 30.0, "host_slope": -0.5}, "dormer.level_host",
     dg.FACES_UPHILL),
])
def test_a_dormer_over_the_main_ridge_or_facing_uphill_is_an_overridable_error(
        ctx, rule, why):
    """Patrick, 2026-11-17: "The ridge of the roof is under the dormer (which
    should be an error)". 2026-11-19: and OVERRIDABLE -- it is fixed out on the
    plan (turn or move the dormer, change the host), so the user may acknowledge
    it and keep the red dormer on the plan rather than being trapped."""
    derived, fs = DORMER.evaluate({}, ctx)
    by = {f.rule_id: f for f in fs}
    assert by[rule].severity == F.ERROR and by[rule].overridable
    assert not F.blocks(fs) and F.needs_ack(fs)      # acknowledge, not hard-block
    assert derived is not None and derived["unbuildable"] == why, \
        "still drawn, so the user can see what to fix"


def test_ridge_to_ridge_is_allowed_and_no_host_is_not_an_error():
    ctx = {"host_z_face_in": 30.0, "host_slope": 0.8, "host_ridge_in": 110.0}
    derived, fs = DORMER.evaluate({}, ctx)            # its own ridge is 110
    assert derived["unbuildable"] is None and not F.blocks(fs)
    assert dg.unbuildable(_st()) is None
    assert dg.unbuildable(_st(), 30.0, 0.8) is None, "host ridge unknown"


def test_couple_ridge_floats_the_unpinned_side_per_form():
    # P2 (2026-11-18): hold the ridge by floating the non-pinned of eaves/pitch;
    # a gable climbs over the HALF-WIDTH, a shed over the DEPTH.
    g = dg.couple_ridge(_st(span_left_in=60.0, pitch_12=6.0), 120.0, "pitch_12")
    assert dg.ridge_height(g) == pytest.approx(120.0)
    assert g["eaves_h_in"] == pytest.approx(90.0)        # 120 - 60*6/12
    e = dg.couple_ridge(_st(span_left_in=60.0, eaves_h_in=84.0), 120.0, "eaves_h_in")
    assert dg.ridge_height(e) == pytest.approx(120.0)    # pitch floated instead
    s = dg.couple_ridge(_st(form="shed", depth_in=80.0, pitch_12=6.0), 130.0, "pitch_12")
    assert dg.ridge_height(s) == pytest.approx(130.0)
    assert s["eaves_h_in"] == pytest.approx(90.0)        # 130 - 80*6/12 (depth, not span)


def test_a_dormer_off_the_host_fall_line_is_not_downhill():
    # P2 (2026-11-18): more than FACING_TOL_DEG off straight-downhill is refused.
    st = _st()                                        # ridge 110, host ridge 240
    assert dg.unbuildable(st, 60.0, 1.0, 240.0, 0.0) is None    # straight downhill
    assert dg.unbuildable(st, 60.0, 1.0, 240.0, dg.FACING_TOL_DEG) is None
    assert dg.unbuildable(st, 60.0, 1.0, 240.0, 30.0) == dg.NOT_DOWNHILL
    # the finding carries through evaluate
    ctx = {"host_z_face_in": 60.0, "host_slope": 1.0, "host_ridge_in": 240.0,
           "host_offaxis_deg": 30.0}
    _d, fs = DORMER.evaluate({}, ctx)
    nd = next(f for f in fs if f.rule_id == "dormer.not_downhill")
    # an error, but OVERRIDABLE (fixed by rotating on the plan) -- not a hard block
    assert nd.severity == F.ERROR and nd.overridable
    assert not F.blocks(fs) and F.needs_ack(fs)


def test_the_message_names_a_width_that_fits():
    ctx = {"host_z_face_in": 30.0, "host_slope": 0.8, "host_ridge_in": 108.0}
    _d, fs = DORMER.evaluate({"span_left_in": 104.0}, ctx)   # ridge 146.67
    (f,) = [f for f in fs if f.rule_id == "dormer.above_host_ridge"]
    assert "146.67 in" in f.message and "50.4 in a side" in f.message
    fitted = dg.fit_under_ridge(_st(span_left_in=104.0), 108.0)
    assert dg.unbuildable(fitted, 30.0, 0.8, 108.0) is None


def test_fit_under_ridge_narrows_first_then_lowers_the_eaves():
    st = dg.fit_under_ridge(_st(span_left_in=104.0), 108.0)
    assert st["eaves_h_in"] == 60.0 and st["pitch_12"] == 10.0, "only narrowed"
    assert dg.ridge_height(st) == pytest.approx(102.0)
    assert st["span_right_in"] == st["span_left_in"] == pytest.approx(50.4)
    low = dg.fit_under_ridge(_st(), 70.0)             # cannot narrow enough
    assert low["span_left_in"] == 24.0 and dg.ridge_height(low) == pytest.approx(64.0)
    same = dg.fit_under_ridge(_st(), 200.0)
    assert same == _st(), "already fits: untouched"
    free = dg.fit_under_ridge(_st(symmetric=False, span_left_in=100.0,
                                  span_right_in=50.0), 108.0)
    assert free["span_right_in"] == pytest.approx(free["span_left_in"] / 2.0)


def test_a_new_dormer_is_born_under_the_host_ridge():
    st = dg.default_state(ceiling_in=96.0, host_slope=10.0 / 12.0, host_ridge_in=108.0)
    assert dg.ridge_height(st) <= 108.0 - dg.RIDGE_CLEAR_IN + 1e-9
    assert dg.unbuildable(st, 30.0, 10.0 / 12.0, 108.0) is None
    assert dg.default_state(96.0, 10.0 / 12.0)["span_left_in"] == 60.0
