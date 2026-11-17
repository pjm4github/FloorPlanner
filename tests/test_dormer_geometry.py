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


def test_a_shed_has_one_plane():
    st = _st(form="shed", span_right_in=50.0, symmetric=True)
    assert st["span_right_in"] == 0.0 and st["symmetric"] is False
    assert dg.slopes(st)[1] == 0.0
    assert len(dg.plan(st)["eaves"]) == 1
    assert len(dg.knee_lines(st, 90.0, *HOST)) <= 1


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
    assert len(p["guides"]) == 3 and len(p["valleys"]) == 2 and len(p["knees"]) == 2


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
    ({"host_z_face_in": 30.0, "host_slope": 0.0}, "dormer.level_host", F.WARNING),
    ({"host_z_face_in": 200.0, "host_slope": 0.8}, "dormer.buried", F.WARNING),
    ({"host_z_face_in": 30.0, "host_slope": 0.8, "host_ridge_in": 100.0},
     "dormer.above_host_ridge", F.ADVISORY),
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
    assert {s.key for s in DORMER.specs()} <= set(dg.STATE_DEFAULTS)
    v = {"form": "shed"}
    by = {s.key: s for s in DORMER.specs()}
    assert not by["span_right_in"].enabled(v) and not by["symmetric"].enabled(v)
    assert by["span_right_in"].enabled({"form": "gable", "symmetric": False})


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
