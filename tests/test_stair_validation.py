"""Stair validation and the floor link (0323) --
`floorplanner/parametric/stairs.py`. Spec sec 6 and sec 9.1 #3-5, #8, #9,
#11, #12. No scene, no window."""
import pytest

from floorplanner.parametric import findings as F
from floorplanner.parametric import stair_geometry as sg
from floorplanner.parametric.stairs import STAIRS

pytestmark = pytest.mark.furnishings

CTX = {"this_floor": "First", "this_elev": 0.0,
       "elevations": {"First": 0.0, "Second": 108.0}}


def _eval(context=None, **over):
    st = dict(sg.STATE_DEFAULTS)
    st.update(over)
    return STAIRS.evaluate(st, CTX if context is None else context)


def _by_rule(findings):
    return {f.rule_id: f for f in findings}


def test_manual_13_risers_over_108_violates_the_riser_limit():
    """9.1 #3 / sec 6.4: 108 / 13 = 8.308 in."""
    geom, fs = _eval(riser_count_mode="manual", riser_count=13)
    f = _by_rule(fs)["riser.max_height"]
    assert f.severity == F.ERROR
    assert f.actual == pytest.approx(108.0 / 13) and f.limit == 7.75
    assert f.field == "riser_count"
    assert F.blocks(fs)
    assert geom is not None, "a bad stair still calculates; validation rejects it"


@pytest.mark.parametrize("tread,severity", [(10.0, F.PASS), (9.999, F.ERROR),
                                            (9.5, F.ERROR), (11.0, F.PASS)])
def test_tread_depth_minimum(tread, severity):
    """9.1 #4."""
    _g, fs = _eval(tread_depth_in=tread)
    assert _by_rule(fs)["tread.min_depth"].severity == severity


@pytest.mark.parametrize("width,severity", [(36.0, F.PASS), (35.999, F.ERROR),
                                            (34.0, F.ERROR), (42.0, F.PASS)])
def test_nominal_width_minimum(width, severity):
    """9.1 #5."""
    _g, fs = _eval(stair_width_in=width)
    assert _by_rule(fs)["width.min_nominal"].severity == severity


def test_the_passing_example_is_not_called_compliant():
    """Sec 6.4, fourth example, and sec 6.1's important rule: the basic
    dimensions pass, headroom and landings are NOT EVALUATED, the comfort
    heuristic is advisory -- and the headline never says 'compliant'."""
    _g, fs = _eval()
    rules = _by_rule(fs)
    assert not F.blocks(fs)
    assert rules["headroom.min"].severity == F.NOT_EVALUATED       # 9.1 #12
    assert rules["landing.top_bottom"].severity == F.NOT_EVALUATED
    assert rules["handrail.guard"].severity == F.NOT_EVALUATED
    assert rules["comfort.2r_plus_t"].severity == F.ADVISORY
    assert F.needs_ack(fs)                                          # 9.1 #11
    head = F.headline(fs)
    assert "pending" in head
    assert "compliant" not in head.lower()


def test_headroom_stays_unevaluated_never_pass():
    """9.1 #12, over every shape of stair this release draws."""
    for over in ({}, {"type": "L", "turn_deg": 90}, {"type": "U", "turn_deg": 180},
                 {"total_rise_in": 60.0}):
        _g, fs = _eval(**over)
        assert _by_rule(fs)["headroom.min"].severity == F.NOT_EVALUATED


def test_an_error_cannot_be_acknowledged_away():
    """9.1 #11: acknowledgement covers warnings; an error still blocks."""
    _g, fs = _eval(tread_depth_in=9.0)
    assert F.blocks(fs) and F.needs_ack(fs)
    assert [f.rule_id for f in F.errors(fs)] == ["tread.min_depth"]


def test_uncalculable_input_is_one_error_and_no_geometry():
    geom, fs = _eval(total_rise_in=-5.0)
    assert geom is None
    assert [f.rule_id for f in fs] == ["input.invalid"]
    assert fs[0].field == "total_rise_in" and F.blocks(fs)


def test_a_single_riser_is_an_unsupported_stair():
    """9.1 #7, at the validator."""
    _g, fs = _eval(total_rise_in=7.0)
    assert _by_rule(fs)["stair.degenerate"].severity == F.ERROR


def test_linked_rise_follows_the_level_above():
    """9.1 #8: move the upper floor and the linked stair re-derives."""
    g1, _ = _eval(rise_mode="linked")
    assert (g1.total_rise, g1.riser_count) == (108.0, 14)
    taller = {"this_floor": "First", "this_elev": 0.0,
              "elevations": {"First": 0.0, "Second": 120.0, "Attic": 240.0}}
    g2, _ = _eval(taller, rise_mode="linked")
    assert g2.total_rise == 120.0                  # the NEXT level, not the top
    assert g2.riser_count == 16 and g2.total_run == pytest.approx(15 * 11.0)


def test_detached_rise_ignores_the_levels():
    """9.1 #9: a detached stair neither reads nor changes floor elevations."""
    ctx = {"this_floor": "First", "this_elev": 0.0,
           "elevations": {"First": 0.0, "Second": 120.0}}
    before = dict(ctx["elevations"])
    g, _ = _eval(ctx, rise_mode="detached", total_rise_in=96.0)
    assert g.total_rise == 96.0
    assert ctx["elevations"] == before


def test_linked_with_no_level_above_warns_and_uses_the_stored_rise():
    ctx = {"this_floor": "Top", "this_elev": 108.0,
           "elevations": {"First": 0.0, "Top": 108.0}}
    g, fs = _eval(ctx, rise_mode="linked", total_rise_in=100.0)
    assert g.total_rise == 100.0
    assert _by_rule(fs)["rise.unlinked"].severity == F.WARNING


def test_new_stair_links_when_there_is_a_level_above():
    assert sg.default_state(0.0, [0.0, 120.0])["rise_mode"] == "linked"
    alone = sg.default_state(0.0, [0.0])
    assert alone["rise_mode"] == "detached"
    assert alone["total_rise_in"] == sg.DEFAULT_DETACHED_RISE_IN


def test_snapped_landing_is_reported_not_hidden():
    g, fs = _eval(type="L", turn_deg=90, landing_mode="custom",
                  landing_height_in=30.0)
    f = _by_rule(fs)["landing.snapped"]
    assert f.severity == F.ADVISORY
    assert f.actual == pytest.approx(g.landing_height) and f.limit == 30.0


def test_a_long_single_flight_is_flagged_between_landings():
    _g, fs = _eval(total_rise_in=160.0)
    assert _by_rule(fs)["flight.max_rise"].severity == F.WARNING
    _g, fs = _eval(total_rise_in=160.0, type="L", turn_deg=90)
    assert "flight.max_rise" not in _by_rule(fs)


def test_summary_reports_what_was_calculated():
    geom, _ = _eval()
    rows = dict(STAIRS.summary(dict(sg.STATE_DEFAULTS), geom, CTX))
    assert rows["Risers"].startswith("14 @ 7.714")
    assert rows["Treads"].startswith("13 @ 11")
    assert rows["Footprint"] == "143 x 36 in"
