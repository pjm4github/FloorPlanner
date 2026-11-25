"""0368: four kitchen casework kinds -- a tall cabinet that stands on the floor
or on a counter, a kitchen desk, a corner wall cabinet, and a cabinet hung
from the ceiling over an island. No Qt."""
import pytest

from floorplanner.parametric import cabinet_geometry as cg
from floorplanner.parametric import findings as F
from floorplanner.parametric import registry

NEW = ("tall_cab", "kitchen_desk", "corner_wall_cab", "ceiling_cab")


def _st(kind, **over):
    return cg.normalize_state(over, cg.PRESETS[kind])


def _parts(kind, ceiling=96.0, **over):
    return cg.cabinet_parts(_st(kind, **over), None, ceiling)


def _extent(parts, axis):
    if axis == "z":
        return min(p.z0 for p in parts), max(p.z1 for p in parts)
    i = 0 if axis == "x" else 1
    vals = [q[i] for p in parts for q in p.quad]
    return min(vals), max(vals)


def _named(parts, prefix):
    return [p for p in parts if p.name.startswith(prefix)]


# --------------------------------------------------------------------------
# the tall cabinet
# --------------------------------------------------------------------------
def test_a_tall_cabinet_tops_out_with_the_wall_cabinets():
    wall = _st("wall_cab_36")
    tall = _st("tall_cab")
    assert cg.overall_height(tall) == wall["floor_to_bottom_in"] + wall["height_in"]
    assert _extent(_parts("tall_cab"), "z") == (0.0, 84.0)
    assert cg.trade_code(tall) == "U2484"


@pytest.mark.parametrize("doors", ["1", "2", "3", "4"])
def test_a_tall_cabinets_width_and_doors_are_parameters(doors):
    parts = _parts("tall_cab", width_in=60, doors=doors)
    assert _extent(parts, "x") == (-30.0, 30.0)
    # a floor-standing tall unit splits at the wall cabinets' underside
    for row in ("lower-", "upper-"):
        leaves = {p.name.split("-")[2] for p in _named(parts, f"{row}door-")}
        assert leaves == {str(i + 1) for i in range(int(doors))}, (row, doors)
    assert cg.door_count(_st("tall_cab", width_in=60, doors=doors)) == int(doors)


def test_auto_doors_are_what_they_always_were():
    assert cg.door_count(_st("tall_cab", width_in=18)) == 1
    assert cg.door_count(_st("tall_cab", width_in=60)) == 2
    assert cg.door_count(_st("base_cab_36", doors="7")) == 2      # nonsense: auto


def test_a_tall_cabinet_can_stand_on_a_base_units_counter():
    parts = _parts("tall_cab", stands="counter", depth_in=15)
    assert _extent(parts, "z") == (cg.COUNTER_H, 84.0)
    assert not _named(parts, "toe-kick")
    assert not _named(parts, "upper-") and _named(parts, "door-")
    assert cg.overall_height(_st("tall_cab", stands="counter")) == 84.0
    # its plan symbol is dashed: it is above the plan cut
    assert cg.tall_plan(_st("tall_cab", stands="counter"))[0][0] == "dashed"
    assert cg.tall_plan(_st("tall_cab"))[0][0] == "outline"


def test_the_pantries_are_untouched():
    kind = registry.get("pantry_24")
    assert kind.plan_symbol({}) is None
    assert {s.key for s in kind.specs()} >= {"stands", "doors", "width_in"}


# --------------------------------------------------------------------------
# the kitchen desk
# --------------------------------------------------------------------------
def test_a_kitchen_desk_is_a_counter_top_at_desk_height_with_one_drawer():
    st = _st("kitchen_desk")
    parts = cg.cabinet_parts(st)
    assert cg.overall_height(st) == 30.0 and cg.trade_code(st) == "KD48"
    tops = [p for p in parts if p.role == "countertop"]
    assert len(tops) == 1 and tops[0].z1 == 30.0
    drawers = _named(parts, "drawer-1")
    assert len(drawers) == 1
    x0, x1 = (min(q[0] for q in drawers[0].quad), max(q[0] for q in drawers[0].quad))
    assert x1 - x0 == pytest.approx(48.0 - 2 * cg.REVEAL["full"])     # full width
    assert drawers[0].z1 - drawers[0].z0 < 6.0                        # and small
    assert not _named(parts, "toe-kick") and not _named(parts, "door-")
    # knee space: nothing but the two end panels below the drawer
    below = [p for p in parts if p.z0 < 20.0]
    assert {p.name for p in below} == {"end-panel-l", "end-panel-r"}


def test_the_desk_top_is_the_kitchens_countertop():
    st = _st("kitchen_desk")
    room = {"countertop": "soapstone", "cabinet_finish": "navy"}
    mats = cg.resolve_materials(st, room)
    assert mats["countertop"] == cg.resolve_materials(_st("base_cab_36"), room)[
        "countertop"]
    own = cg.resolve_materials(_st("kitchen_desk", top_material="marble"), room)
    assert own["countertop"] != mats["countertop"]


def test_a_desk_always_has_its_top_and_its_drawer():
    st = _st("kitchen_desk", top_on=False, front="doors", toe_kick_h_in=4.5)
    assert st["top_on"] is True and st["front"] == "drawers"
    assert st["toe_kick_h_in"] == 0.0


# --------------------------------------------------------------------------
# the corner wall cabinet
# --------------------------------------------------------------------------
@pytest.mark.parametrize("corner", ["diagonal", "l_shape"])
@pytest.mark.parametrize("hand", ["left", "right"])
def test_a_corner_wall_cabinet_hangs_in_its_footprint(corner, hand):
    st = _st("corner_wall_cab", corner_type=corner, hand=hand, width_in=30,
             wing_in=27, depth_in=13)
    parts = cg.cabinet_parts(st)
    assert cg.footprint(st) == (30.0, 27.0) and cg.is_mounted(st)
    assert _extent(parts, "x") == pytest.approx((-15.0, 15.0))
    f0, f1 = _extent(parts, "f")
    assert f0 == pytest.approx(0.0) and f1 <= 27.0 + 1e-9
    assert _extent(parts, "z") == (54.0, 84.0)
    assert len(_named(parts, "door-")) == (1 if corner == "diagonal" else 2)
    # the corner is on the hand's side: the long back carcass spans the width,
    # the leg hugs that side
    leg = next(p for p in parts if p.name == "carcass-leg")
    side = [q[0] for q in leg.quad]
    assert (min(side) == pytest.approx(-15.0)) == (hand == "left")
    assert (max(side) == pytest.approx(15.0)) == (hand == "right")


def test_the_wings_and_the_depth_are_parameters():
    st = _st("corner_wall_cab", width_in=36, wing_in=24, depth_in=15)
    assert cg.footprint(st) == (36.0, 24.0)
    back = next(p for p in cg.cabinet_parts(st) if p.name == "carcass")
    assert max(q[1] for q in back.quad) == 15.0
    assert cg.trade_code(st) == "DCW3630"
    # a wing is never shorter than a door past the corner; blind is a base's
    tight = _st("corner_wall_cab", width_in=8, wing_in=8, corner_type="blind")
    assert tight["width_in"] == tight["wing_in"] == 18.0
    assert tight["corner_type"] == "diagonal"


def test_the_corner_wall_plan_symbol_is_its_dashed_outline():
    st = _st("corner_wall_cab", hand="right", corner_type="l_shape")
    op, style, ring = cg.corner_wall_plan(st)[0]
    assert (op, style) == ("poly", "dashed") and len(ring) == 6
    assert max(x for x, _f in ring) == 12.0 and (12.0, 0.0) in ring   # corner right


# --------------------------------------------------------------------------
# the ceiling cabinet
# --------------------------------------------------------------------------
@pytest.mark.parametrize("ceiling", [96.0, 108.0, 120.0])
def test_a_ceiling_cabinet_hangs_from_its_rooms_ceiling(ceiling):
    parts = _parts("ceiling_cab", ceiling)
    z0, z1 = _extent(parts, "z")
    assert z1 == ceiling
    assert next(p for p in parts if p.name == "light-rail").z0 == ceiling - 24.0
    assert z0 == pytest.approx(ceiling - 24.0 - 0.3)        # the strip under it
    assert cg.overall_height(_st("ceiling_cab"), ceiling) == ceiling


def test_a_drop_hangs_it_on_rods():
    parts = _parts("ceiling_cab", 108.0, drop_in=12, height_in=18)
    rods = _named(parts, "rod-")
    assert len(rods) == 4 and all(r.z0 == 96.0 and r.z1 == 108.0 for r in rods)
    assert next(p for p in parts if p.name == "cap").z1 == 96.0
    assert next(p for p in parts if p.name == "light-rail").z0 == 78.0
    assert not _named(_parts("ceiling_cab"), "rod-")


@pytest.mark.parametrize("doors", ["1", "2", "3", "4"])
def test_doors_on_both_sides_or_one(doors):
    both = _parts("ceiling_cab", width_in=72, doors=doors)
    one = _parts("ceiling_cab", width_in=72, doors=doors, door_sides="one")
    n = int(doors)

    def leaves(parts, tag):
        return {p.name.split("-")[1 if tag == "" else 2]
                for p in parts if p.name.startswith(f"{tag}door-")}

    assert len(leaves(both, "")) == n and len(leaves(both, "back-")) == n
    assert len(leaves(one, "")) == n and not leaves(one, "back-")
    # nothing leaves the footprint on either side
    for parts in (both, one):
        f0, f1 = _extent(parts, "f")
        assert f0 == pytest.approx(0.0) and f1 == pytest.approx(15.0)
    # the back doors face the other way: their pulls stand off the BACK face
    pull = next(p for p in both if p.name == "back-pull-1")
    door = next(p for p in both if p.name.startswith("back-door-1"))
    assert max(q[1] for q in pull.quad) <= min(q[1] for q in door.quad) + 1e-9


def test_the_light_under_it_is_selectable_and_is_a_real_source():
    st = _st("ceiling_cab", light_colour="daylight", lumens=1200)
    src = cg.light_source(st, 108.0)
    assert src["kind"] == "spot" and src["lumens"] == 1200.0
    assert src["pos"][2] < 108.0 - 24.0                 # below the cabinet
    assert {p.role for p in cg.cabinet_parts(st, None, 108.0)} >= {"lens"}
    off = _st("ceiling_cab", under_light=False)
    assert cg.light_source(off, 108.0) is None
    assert "lens" not in {p.role for p in cg.cabinet_parts(off, None, 108.0)}
    assert cg.light_source(_st("ceiling_cab", lumens=0), 108.0) is None
    # and no other cabinet became a light
    assert cg.light_source(_st("wall_cab_36"), 96.0) is None


def test_a_low_ceiling_cabinet_is_advised_never_blocked():
    kind = registry.get("ceiling_cab")
    _d, fs = kind.evaluate(kind.normalize({"height_in": 42}), {"ceiling_in": 96.0})
    assert [f.rule_id for f in fs] == ["suspended.clearance"]
    assert not F.blocks(fs)
    _d, fs = kind.evaluate(kind.normalize({}), {"ceiling_in": 96.0})
    assert fs == []


# --------------------------------------------------------------------------
# all four, through the registry
# --------------------------------------------------------------------------
@pytest.mark.parametrize("name", NEW)
def test_each_draws_its_plan_symbol_from_its_parameters(name):
    kind = registry.get(name)
    symbol = kind.plan_symbol({})
    assert symbol and symbol["prims"]
    ops = {prim[0] for prim in symbol["prims"]}
    assert ops <= {"outline", "panel", "dashed", "line", "dline", "dot", "bulb",
                   "poly"}, ops


@pytest.mark.parametrize("name", NEW)
def test_each_stores_only_what_was_changed_and_reads_it_back(name):
    kind = registry.get(name)
    assert kind.to_state(kind.normalize({})) == {}
    spec = next(s for s in kind.specs() if s.key == "width_in")
    changed = dict(kind.normalize({}), width_in=spec.default + 6.0)
    state = kind.to_state(changed)
    assert state == {"width_in": spec.default + 6.0}
    assert kind.normalize(state)["width_in"] == spec.default + 6.0
    derived, fs = kind.evaluate(kind.normalize(state), {"ceiling_in": 108.0})
    assert derived["parts"] and not F.blocks(fs)
    assert kind.summary(kind.normalize(state), derived, {})


def test_what_each_dialog_offers():
    keys = {name: {s.key for s in registry.get(name).specs()} for name in NEW}
    assert {"width_in", "doors", "stands"} <= keys["tall_cab"]
    assert {"width_in", "top_material"} <= keys["kitchen_desk"]
    assert "doors" not in keys["kitchen_desk"] and "top_on" not in keys["kitchen_desk"]
    assert {"width_in", "wing_in", "depth_in", "corner_type", "hand"} <= keys[
        "corner_wall_cab"]
    assert {"height_in", "width_in", "doors", "door_sides", "under_light",
            "light_colour", "lumens", "drop_in"} <= keys["ceiling_cab"]
