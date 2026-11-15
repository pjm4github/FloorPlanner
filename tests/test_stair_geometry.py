"""The stair calculator (0323) -- `floorplanner/parametric/stair_geometry.py`.

Pure arithmetic: no scene, no window. The numbered cases are the unit tests
docs/furnishing-spec/STAIRS_FURNISHING_SPECIFICATION.md sec 9.1 asks for; the
rest pin the L / U stairs and the landing Patrick added on 2026-11-14.
"""
import math

import pytest

from floorplanner.parametric import stair_geometry as sg

pytestmark = [pytest.mark.furnishings, pytest.mark.geometry]

H_MAX = 7.75


def _calc(rise=108.0, tread=11.0, width=36.0, n=None, kind="straight",
          turn=0, landing=None):
    return sg.calculate_stair_geometry(
        sg.StairInputs(rise, tread, width, n, kind, turn, landing), H_MAX)


def test_spec_example_108_by_11_by_36():
    """9.1 #1. The spec writes the pitch as ~35.05; atan(7.7142857/11) is
    35.04 to two places, so the assertion is on the arithmetic."""
    g = _calc()
    assert g.riser_count == 14
    assert g.riser_height == pytest.approx(7.714285714, abs=1e-8)
    assert g.tread_count == 13
    assert g.total_run == pytest.approx(143.0)
    assert g.pitch_degrees == pytest.approx(math.degrees(math.atan2(108 / 14, 11)))
    assert g.pitch_degrees == pytest.approx(35.04, abs=0.01)
    assert (g.footprint_length, g.footprint_width) == pytest.approx((143.0, 36.0))
    assert g.comfort_index == pytest.approx(26.43, abs=0.005)


def test_exact_boundary_does_not_round_up():
    """9.1 #2: 15.5 / 7.75 is exactly two risers, not three."""
    assert sg.auto_riser_count(15.5, H_MAX) == 2
    assert _calc(rise=15.5).riser_count == 2
    assert sg.auto_riser_count(15.5001, H_MAX) == 3


def test_n_risers_make_n_minus_one_treads_never_n():
    """Spec sec 3, the convention: the upper floor is the top step."""
    for rise in (30.0, 96.0, 108.0, 120.0, 144.0):
        g = _calc(rise=rise)
        assert g.tread_count == g.riser_count - 1
        assert g.total_run == pytest.approx(g.tread_count * 11.0)


def test_manual_riser_count_is_used_as_given():
    g = _calc(n=13)
    assert g.riser_count == 13
    assert g.riser_height == pytest.approx(108.0 / 13)


@pytest.mark.parametrize("field,kwargs", [
    ("total_rise_in", {"rise": 0.0}),
    ("total_rise_in", {"rise": -108.0}),
    ("total_rise_in", {"rise": float("nan")}),
    ("total_rise_in", {"rise": float("inf")}),
    ("tread_depth_in", {"tread": 0.0}),
    ("tread_depth_in", {"tread": float("nan")}),
    ("stair_width_in", {"width": -1.0}),
    ("riser_count", {"n": 0}),
    ("type", {"kind": "spiral"}),
    ("turn_deg", {"kind": "L", "turn": 45}),
])
def test_invalid_input_is_refused_and_names_its_field(field, kwargs):
    """9.1 #6: negative, zero and non-finite values are rejected safely."""
    with pytest.raises(sg.StairError) as exc:
        _calc(**kwargs)
    assert exc.value.field == field


def test_one_riser_has_no_treads_and_draws_no_flight():
    """9.1 #7: N = 1 is not an ordinary staircase -- no tread, no flight
    rectangle, and no tread board in the 3D solid."""
    g = _calc(rise=7.0)
    assert (g.riser_count, g.tread_count) == (1, 0)
    assert sg.plan(g)["rects"] == []
    assert g.total_run == 0.0


def test_L_stair_halves_at_the_landing_by_default():
    g = _calc(kind="L", turn=90)
    assert g.riser_count == 14 and g.landing_risers == 7
    assert g.landing_height == pytest.approx(54.0)
    # one landing: each flight gives up its top tread to a landing or floor
    assert g.tread_count == 12
    assert [f.treads for f in g.flights] == [6, 6]
    assert g.landing == pytest.approx((0.0, 66.0, 36.0, 36.0))
    assert g.bbox == pytest.approx((0.0, 0.0, 102.0, 102.0))


def test_turn_sign_picks_the_side():
    left = _calc(kind="L", turn=90)
    right = _calc(kind="L", turn=-90)
    assert left.bbox[2] > 36.0 and left.bbox[0] == pytest.approx(0.0)
    assert right.bbox[0] < 0.0 and right.bbox[2] == pytest.approx(36.0)
    u_left = _calc(kind="U", turn=180)
    u_right = _calc(kind="U", turn=-180)
    assert u_left.bbox == pytest.approx((0.0, 0.0, 72.0, 102.0))
    assert u_right.bbox == pytest.approx((-36.0, 0.0, 36.0, 102.0))


def test_landing_height_snaps_to_whole_risers_and_moves_the_footprint():
    """Patrick, 2026-11-14: the landing height is adjustable and changes the
    footprint. A low landing on a U stair makes the upper flight OVERHANG the
    foot of the lower one."""
    even = _calc(kind="U", turn=180)
    low = _calc(kind="U", turn=180, landing=30.0)
    assert low.landing_risers == 4                      # 30 / 7.714 = 3.9
    assert low.landing_height == pytest.approx(4 * 108.0 / 14)
    assert [f.treads for f in low.flights] == [3, 9]
    assert low.bbox[1] < 0.0 <= even.bbox[1]            # the overhang
    assert low.footprint_length > even.footprint_length
    assert sum(f.risers for f in low.flights) == low.riser_count


def test_landing_height_is_clamped_inside_the_stair():
    lo = _calc(kind="L", turn=90, landing=0.0)
    hi = _calc(kind="L", turn=90, landing=500.0)
    assert lo.landing_risers == 1
    assert hi.landing_risers == hi.riser_count - 1


def test_plan_shows_exactly_the_treads_the_geometry_has():
    for kind, turn in (("straight", 0), ("L", 90), ("L", -90), ("U", 180)):
        g = _calc(kind=kind, turn=turn)
        p = sg.plan(g)
        # t treads in a flight = t - 1 lines between them
        assert len(p["steps"]) == sum(max(f.treads - 1, 0) for f in g.flights)
        assert len(p["line"]) >= 2
        for x, y, w, h in p["rects"]:
            assert g.bbox[0] - 1e-9 <= x and x + w <= g.bbox[2] + 1e-9
            assert g.bbox[1] - 1e-9 <= y and y + h <= g.bbox[3] + 1e-9


def test_solids_have_one_board_per_tread_and_reach_the_top():
    g = _calc(kind="L", turn=90)
    solids = sg.solids(g)
    boxes = [s for s in solids if s[0] == "box"]
    tread_boards = [b for b in boxes
                    if b[3] - b[2] == pytest.approx(sg.TREAD_T_IN)]
    assert len(tread_boards) == g.tread_count
    assert len([s for s in solids if s[0] == "prism"]) == 4     # 2 per flight
    top = max(b[3] for b in boxes)
    assert top == pytest.approx(g.total_rise - sg.TREAD_T_IN)   # the last riser
    assert min(b[2] for b in boxes) >= 0.0


def test_developed_profile_climbs_the_whole_rise():
    g = _calc(kind="U", turn=-180)
    segs = sg.developed_profile(g)
    assert len([s for s in segs if s[0] == "riser"]) == g.riser_count
    assert len([s for s in segs if s[0] == "tread"]) == g.tread_count
    assert len([s for s in segs if s[0] == "landing"]) == 1
    assert max(s[4] for s in segs) == pytest.approx(g.total_rise)


def test_state_round_trips_through_normalize_and_keeps_unknown_keys():
    st = sg.normalize_state({"type": "U", "turn_deg": -180, "future_key": 7,
                             "tread_depth_in": "12", "riser_count": "x"})
    assert st["type"] == "U" and st["turn_deg"] == -180
    assert st["tread_depth_in"] == 12.0
    assert st["riser_count"] == sg.STATE_DEFAULTS["riser_count"]
    assert st["future_key"] == 7
    assert sg.normalize_state(st) == st
    # a turn that does not belong to the type falls back to that type's first
    assert sg.normalize_state({"type": "L", "turn_deg": 180})["turn_deg"] == 90


def test_legacy_state_is_not_parametric():
    assert not sg.is_parametric_state({"flight": "half", "turn": "left",
                                       "direction": "up"})
    assert not sg.is_parametric_state({})
    assert not sg.is_parametric_state(None)
    assert sg.is_parametric_state({"type": "straight"})
