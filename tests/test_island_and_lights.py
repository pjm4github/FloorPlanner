"""The parametric island, the hood and over-range microwave, the laundry
finishes, and lights (0333). Pure: `cabinet_geometry.py` and its kinds."""
import pytest

from floorplanner.parametric import cabinet_geometry as cg
from floorplanner.parametric import findings as F
from floorplanner.parametric import registry

pytestmark = pytest.mark.furnishings


def _st(kind, **over):
    return cg.normalize_state(over, cg.PRESETS[kind])


def _fs(parts):
    return [f for p in parts for _x, f in p.quad]


# -- the island ----------------------------------------------------------------
def test_an_island_is_as_long_as_what_stands_under_it():
    assert cg.footprint(_st("kitchen_island")) == (72.0, 39.0)
    st = _st("kitchen_island", slot_1="DW24", slot_2="B36", slot_3="DB18")
    assert [c for c, _w, _k, _o in cg.island_slots(st)] == ["DW24", "B36", "DB18"]
    assert st["width_in"] == 78.0 and cg.footprint(st) == (78.0, 39.0)
    assert cg.trade_code(st) == "DW24+B36+DB18"
    empty = _st("kitchen_island", slot_1="none", slot_2="none")
    assert empty["width_in"] == 48.0 and cg.cabinet_parts(empty)


def test_a_slot_holds_a_cabinet_or_an_appliance():
    """Patrick, 2026-11-15: "I want to put a dishwasher in the kitchen island
    or a base unit in the kitchen island"."""
    parts = cg.cabinet_parts(_st("kitchen_island", slot_1="DW24", slot_2="B36"))
    dish = [p for p in parts if p.name.startswith("slot1-DW24-")]
    base = [p for p in parts if p.name.startswith("slot2-B36-")]
    assert {p.role for p in dish} >= {"appliance", "appliance_dark"}
    assert any("door" in p.name for p in base) and all(
        p.role in ("cabinet", "hardware", "kick") for p in base)
    # side by side, slot 1 at the LEFT as you face the doors -- which is +x,
    # because the doors are on the far side of the island's own frame
    assert min(x for p in dish for x, _f in p.quad) >= max(
        x for p in base for x, _f in p.quad) - 1e-9


def test_doors_on_one_side_stools_on_the_other():
    """Seen from one side the cabinet layout; from the other, short-backed
    stools."""
    st = _st("kitchen_island")
    parts = cg.cabinet_parts(st)
    pulls = [p for p in parts if "pull" in p.name]
    stools = [p for p in parts if p.name.startswith("stool-")]
    assert pulls and stools
    assert max(_fs(pulls)) < 3.0, "hardware is at the door side (f near 0)"
    assert min(_fs(stools)) > cg.ISLAND_FRONT_SETBACK + cg.ISLAND_CABINET_D
    assert max(_fs(parts)) <= st["depth_in"] + 1e-9
    assert min(_fs(parts)) >= -1e-9, "nothing outside the footprint"
    seats = [p for p in stools if p.name.endswith("-seat")]
    backs = [p for p in stools if p.name.endswith("-back")]
    assert len(seats) == len(backs) == 3
    for seat, back in zip(seats, backs, strict=True):
        assert back.z1 - seat.z1 <= 9.0, "a SHORT back"
        assert min(_fs([back])) > sum(_fs([seat])) / 4.0, "away from the island"
        assert seat.z1 == cg.STOOL_SEAT_Z


@pytest.mark.parametrize("seats", [0, 1, 4, 8])
def test_the_number_of_seats_is_a_parameter(seats):
    parts = cg.cabinet_parts(_st("kitchen_island", seats=seats))
    assert len([p for p in parts if p.name.endswith("-seat")]) == seats
    assert _st("kitchen_island", seats=99)["seats"] == 8


def test_one_countertop_covers_the_island_and_opens_over_a_sink():
    plain = [p for p in cg.cabinet_parts(_st("kitchen_island"))
             if p.role == "countertop"]
    assert len(plain) == 1
    xs = [x for x, _f in plain[0].quad]
    assert (min(xs), max(xs)) == (-36.0, 36.0)
    assert (min(_fs(plain)), max(_fs(plain))) == (0.0, 39.0)
    assert (plain[0].z0, plain[0].z1) == (34.5, 36.0)
    sink = cg.cabinet_parts(_st("island_sink"))
    bowls = [p for p in sink if p.name.endswith("-floor")]
    assert len(bowls) == 2
    for bowl in bowls:
        bx = sum(x for x, _f in bowl.quad) / 4.0
        bf = sum(f for _x, f in bowl.quad) / 4.0
        for top in (p for p in sink if p.role == "countertop"):
            xs = [x for x, _f in top.quad]
            fs = [f for _x, f in top.quad]
            assert not (min(xs) < bx < max(xs) and min(fs) < bf < max(fs))


def test_island_advisories():
    kind = registry.get("kitchen_island")
    _d, fs = kind.evaluate(kind.normalize({"seats": 6}), {})
    assert [f.rule_id for f in fs] == ["island.seat_width"]
    _d, fs = kind.evaluate(kind.normalize({"depth_in": 30.0}), {})
    assert [f.rule_id for f in fs] == ["island.overhang"]
    assert not F.blocks(fs) and not F.needs_ack(fs)
    assert "width_in" not in kind.to_state(kind.normalize({"slot_3": "B24"}))


# -- over the range --------------------------------------------------------------
def test_the_hood_and_the_microwave_hang_over_a_range():
    hood = cg.cabinet_parts(_st("range_hood"))
    micro = cg.cabinet_parts(_st("microwave_otr"))
    assert min(p.z0 for p in micro) == pytest.approx(54.0)
    assert max(p.z1 for p in micro) == pytest.approx(71.0)
    assert max(p.z1 for p in hood) == pytest.approx(84.0)
    assert min(p.z0 for p in hood) > 60.0
    assert cg.is_mounted(_st("range_hood")) and not cg.is_mounted(_st("range"))
    raised = cg.cabinet_parts(_st("microwave_otr", floor_to_bottom_in=60.0))
    assert min(p.z0 for p in raised) == pytest.approx(60.0)
    assert cg.resolve_materials(_st("range_hood", finish_mode="match"),
                                {"cabinet_finish": "oak"})["appliance"] == "cab_oak"


# -- the laundry -----------------------------------------------------------------
@pytest.mark.parametrize("kind", ["washer", "dryer"])
def test_a_washer_or_dryer_is_gloss_white_silver_or_black(kind):
    """Patrick, 2026-11-15."""
    hexes = {k: h for k, _l, h in cg.COLOURS}
    assert cg.resolve_materials(_st(kind))["appliance"] == (
        "sheen_gloss" + hexes["white"])
    for colour in cg.LAUNDRY_COLOURS:
        assert cg.resolve_materials(_st(kind, colour=colour))["appliance"] == (
            "sheen_gloss" + hexes[colour])
    odd = _st(kind, colour="red", sheen="matte", finish_mode="standard")
    assert (odd["colour"], odd["sheen"], odd["finish_mode"]) == (
        "white", "gloss", "custom")
    spec = registry.get(kind).specs()
    assert [s.key for s in spec] == ["colour"]
    assert [c[0] for c in spec[0].choices] == ["white", "silver", "black"]


# -- lights ------------------------------------------------------------------------
@pytest.mark.parametrize("kind", ["light_recessed", "light_flush", "light_pendant",
                                  "light_linear", "light_sconce"])
def test_every_light_has_a_fixture_a_glowing_lens_and_a_source(kind):
    st = _st(kind)
    parts = cg.cabinet_parts(st, None, 108.0)
    assert {p.role for p in parts} == {"fixture", "lens"}
    src = cg.light_source(st, 108.0)
    assert src["lumens"] == 800.0 and src["kind"] in ("point", "spot")
    lens = next(p for p in parts if p.role == "lens")
    assert src["pos"][2] < lens.z0 + 1e-9, "the source is at the lens, below it"
    assert cg.resolve_materials(st)["lens"] == "light_emit#ffe4bf"
    if st["fixture"] != "sconce":
        assert max(p.z1 for p in parts) == pytest.approx(108.0), "at the ceiling"


def test_a_lights_shape_colour_and_output_are_parameters():
    """Patrick, 2026-11-15: a light source, shape and colour that can be
    adjusted."""
    st = _st("light_flush", fixture="pendant", light_colour="blue", lumens=1600,
             size_in=18, drop_in=40)
    parts = cg.cabinet_parts(st, None, 96.0)
    assert min(p.z0 for p in parts) < 96.0 - 40.0, "a pendant drops"
    assert cg.footprint(st) == (18.0, 18.0)
    src = cg.light_source(st, 96.0)
    assert src["colour"] == pytest.approx((0x5a / 255, 0x8c / 255, 1.0))
    assert src["lumens"] == 1600.0
    assert cg.resolve_materials(st)["lens"] == "light_emit#5a8cff"
    assert cg.light_source(_st("light_recessed"), 96.0)["kind"] == "spot"
    assert cg.light_source(_st("light_recessed", beam="wide"), 96.0)["kind"] == "point"
    assert cg.footprint(_st("light_linear", size_in=72)) == (72.0, 6.0)


def test_zero_output_keeps_the_fixture_and_drops_the_source():
    st = _st("light_flush", lumens=0)
    assert cg.cabinet_parts(st) and cg.light_source(st) is None
    assert cg.light_source(_st("base_cab_36")) is None


def test_a_sconce_sits_on_the_wall_at_its_height():
    st = _st("light_sconce", floor_to_bottom_in=72.0)
    parts = cg.cabinet_parts(st, None, 96.0)
    assert min(p.z0 for p in parts) == pytest.approx(72.0)
    assert min(_fs(parts)) == pytest.approx(0.0), "against the wall"
