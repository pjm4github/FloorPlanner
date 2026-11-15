"""Stair rails, the U-stair gap, and the stated checks (0335) --
`floorplanner/parametric/stair_geometry.py` and `stairs.py`. No scene, no
window."""
import pytest

from floorplanner.parametric import findings as F
from floorplanner.parametric import stair_geometry as sg
from floorplanner.parametric.stairs import STAIRS

pytestmark = pytest.mark.furnishings

CTX = {"this_floor": "First", "this_elev": 0.0,
       "elevations": {"First": 0.0, "Second": 108.0}}


def _state(**over):
    st = dict(sg.STATE_DEFAULTS)
    st.update(over)
    return st


def _geom(**over):
    return sg.geometry_from_state(_state(**over))[0]


def _rules(**over):
    _g, fs = STAIRS.evaluate(_state(**over), CTX)
    return {f.rule_id: f for f in fs}, fs


# -- the gap between a U stair's flights ------------------------------------
@pytest.mark.parametrize("turn", [180, -180])
def test_a_u_stair_gap_parts_the_flights_and_widens_the_landing(turn):
    g0 = _geom(type="U", turn_deg=turn)
    g = _geom(type="U", turn_deg=turn, flight_gap_in=4.5)
    assert g.flight_gap == 4.5
    assert g.landing[2] == pytest.approx(2 * 36.0 + 4.5)
    assert g.footprint_width == pytest.approx(g0.footprint_width + 4.5)
    assert g.footprint_length == pytest.approx(g0.footprint_length)
    r1, r2 = (sg._norm_rect(sg.flight_rect(f, 36.0)) for f in g.flights)
    lo, hi = sorted([r1, r2])
    assert hi[0] - (lo[0] + lo[2]) == pytest.approx(4.5), "the well"
    assert (g.riser_count, g.tread_count) == (g0.riser_count, g0.tread_count)


def test_no_gap_is_the_stair_it_always_was():
    a, b = _geom(type="U", turn_deg=180), _geom(type="U", turn_deg=180,
                                                flight_gap_in=0.0)
    assert a == b
    assert a.landing == (0.0, a.flights[0].run, 72.0, 36.0)


def test_the_gap_is_a_u_stair_parameter_only():
    assert _geom(type="L", turn_deg=90, flight_gap_in=9.0).flight_gap == 0.0
    assert _geom(flight_gap_in=9.0).flight_gap == 0.0


def test_a_negative_gap_is_refused_by_name():
    with pytest.raises(sg.StairError) as err:
        _geom(type="U", turn_deg=180, flight_gap_in=-1.0)
    assert err.value.field == "flight_gap_in"


def test_the_plan_arrow_crosses_the_gap():
    g = _geom(type="U", turn_deg=180, flight_gap_in=6.0)
    xs = [x for x, _y in sg.plan(g)["line"]]
    assert max(xs) == pytest.approx(36.0 + 6.0 + 18.0)


# -- rails -------------------------------------------------------------------
def test_bare_inputs_carry_no_rails():
    g = sg.calculate_stair_geometry(sg.StairInputs(108.0, 11.0, 36.0), 7.75)
    assert sg.rail_solids(g) == []


def test_a_stored_stair_defaults_to_guards_and_two_rails():
    g = _geom()
    assert (g.left_side, g.right_side, g.handrail) == ("guard", "guard", "both")
    assert sg.clear_width(g) == (30.0, 2)


def test_the_rail_runs_the_rail_height_above_the_nosing_line():
    g = _geom(left_side="wall", right_side="wall", handrail="left")
    rails = sg.rail_solids(g)
    prisms = [s for s in rails if s[0] == "prism"]
    assert len(prisms) == 1, "one flight, one side"
    zs = sorted(p[2] for p in prisms[0][1])
    h = g.riser_height
    assert zs[-1] == pytest.approx(108.0 + 36.0)          # over the top nosing
    assert zs[1] == pytest.approx(h + 36.0)               # over the first
    xs = {round(p[0], 6) for p in prisms[0][1] + prisms[0][2]}
    assert xs == {36.0 - 3.0, 36.0 - 1.5}, "left is +X, 1.5 in off the wall"


def test_left_and_right_follow_the_walker_round_a_turn():
    """A left U: the inner side is the walker's LEFT on both flights."""
    g = _geom(type="U", turn_deg=180, flight_gap_in=4.5,
              left_side="wall", right_side="wall", handrail="left")
    prisms = [s for s in sg.rail_solids(g) if s[0] == "prism"]
    assert len(prisms) == 2
    for pr in prisms:
        xs = [p[0] for p in pr[1] + pr[2]]
        assert 36.0 - 3.0 - 1e-9 <= min(xs) and max(xs) <= 40.5 + 3.0 + 1e-9


def test_guards_stay_inside_the_footprint_and_above_the_floor():
    for over in ({}, {"type": "L", "turn_deg": -90},
                 {"type": "U", "turn_deg": 180, "flight_gap_in": 5.0},
                 {"type": "U", "turn_deg": -180}):
        g = _geom(**over)
        x0, y0, x1, y1 = g.bbox
        solids = sg.rail_solids(g)
        assert solids
        for s in solids:
            pts = s[1] if s[0] == "box" else s[1] + s[2]
            for p in pts:
                assert x0 - 1e-6 <= p[0] <= x1 + 1e-6
                assert y0 - 1e-6 <= p[1] <= y1 + 1e-6
            if s[0] == "box":
                assert 0.0 <= s[2] < s[3] <= 108.0 + 36.0 + 1e-6


def test_the_landing_guard_takes_the_outside_and_the_gap():
    g = _geom(type="U", turn_deg=180, flight_gap_in=4.5)
    assert len(sg.landing_edges(g, "right")) == 3
    assert sg.landing_edges(g, "left") == [((36.0, 66.0), (40.5, 66.0))]
    assert sg.landing_edges(_geom(type="U", turn_deg=180), "left") == []
    assert len(sg.landing_edges(_geom(type="L", turn_deg=90), "right")) == 2
    assert sg.landing_edges(_geom(), "left") == []


@pytest.mark.parametrize("tread", [9.0, 10.0, 11.0, 12.5, 14.0])
def test_balusters_never_leave_more_than_four_inches(tread):
    g = _geom(tread_depth_in=tread)
    assert sg.guard_opening(g) <= sg.BALUSTER_MAX_OPEN_IN + 1e-9


# -- what the dialog now says ------------------------------------------------
def test_a_default_stair_has_one_fewer_open_check_and_no_rail_error():
    rules, fs = _rules()
    assert not F.blocks(fs)
    for rule in ("handrail.required", "handrail.height", "guard.required",
                 "guard.height", "guard.opening", "width.clear"):
        assert rules[rule].severity == F.PASS, rule
    assert sorted(f.rule_id for f in F.unresolved(fs)) == [
        "code.profile", "headroom.min", "landing.top_bottom"]


def test_stating_the_opening_and_landings_leaves_only_the_code_notice():
    rules, fs = _rules(well_opening_in=132.0, bottom_landing_in=36.0,
                       top_landing_in=36.0)
    assert rules["headroom.min"].severity == F.PASS
    assert rules["landing.top_bottom"].severity == F.PASS
    assert [f.rule_id for f in F.unresolved(fs)] == ["code.profile"]


def test_the_required_opening_is_the_headroom_arithmetic():
    g = _geom()                                   # 14 risers, 13 treads of 11
    h = 108.0 / 14
    want = 143.0 - (108.0 - 12.0 - 80.0 - h) * 11.0 / h
    assert sg.required_opening(g, 80.0) == pytest.approx(want)
    assert sg.required_opening(g, 80.0, 30.0) == pytest.approx(143.0), \
        "a floor so deep the whole stair needs the opening"


def test_a_short_opening_or_landing_is_an_error_on_its_own_field():
    rules, fs = _rules(well_opening_in=96.0)
    assert rules["headroom.min"].severity == F.ERROR
    assert rules["headroom.min"].field == "well_opening_in"
    rules, _fs = _rules(bottom_landing_in=36.0, top_landing_in=30.0)
    assert rules["landing.top_bottom"].severity == F.ERROR
    assert rules["landing.top_bottom"].field == "top_landing_in"
    rules, _fs = _rules(bottom_landing_in=36.0)
    assert rules["landing.top_bottom"].severity == F.NOT_EVALUATED


def test_no_handrail_and_an_unguarded_side_are_warnings():
    rules, fs = _rules(left_side="wall", right_side="open", handrail="none")
    assert rules["handrail.required"].severity == F.WARNING
    assert rules["guard.required"].severity == F.WARNING
    assert rules["guard.required"].field == "right_side"
    assert not F.blocks(fs)
    rules, _fs = _rules(left_side="wall", right_side="wall", handrail="none",
                        rise_mode="detached", total_rise_in=21.0)
    assert "handrail.required" not in rules, "3 risers need none"


@pytest.mark.parametrize("height,ok", [(33.5, False), (34.0, True),
                                       (38.0, True), (38.5, False)])
def test_handrail_height_range(height, ok):
    rules, _fs = _rules(left_side="wall", right_side="wall",
                        rail_height_in=height)
    assert (rules["handrail.height"].severity == F.PASS) is ok


def test_a_landing_guard_must_be_36():
    rules, _fs = _rules(rail_height_in=34.0)
    assert rules["guard.height"].severity == F.PASS, "a flight: 34"
    rules, _fs = _rules(type="L", turn_deg=90, rail_height_in=34.0)
    assert rules["guard.height"].severity == F.ERROR
    assert rules["guard.height"].field == "rail_height_in"


def test_clear_width_counts_the_rails():
    rules, _fs = _rules(stair_width_in=36.0, left_side="wall",
                        right_side="wall", handrail="left")
    assert rules["width.clear"].severity == F.PASS            # 33 >= 31.5
    rules, _fs = _rules(stair_width_in=36.0, handrail="left",
                        left_side="open", right_side="open")
    assert rules["width.clear"].actual == 33.0


def test_new_keys_survive_normalize_and_bad_ones_fall_back():
    st = sg.normalize_state({"type": "U", "left_side": "hedge",
                             "handrail": 7, "flight_gap_in": "x"})
    assert (st["left_side"], st["handrail"], st["flight_gap_in"]) == (
        "guard", "both", 0.0)
    keys = {s.key for s in STAIRS.specs()}
    assert {"flight_gap_in", "left_side", "right_side", "handrail",
            "rail_height_in", "well_opening_in", "bottom_landing_in",
            "top_landing_in"} <= keys
