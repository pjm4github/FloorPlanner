"""Cabinets and appliances as parts, and the room style (0329) --
`floorplanner/parametric/cabinet_geometry.py` and `cabinets.py`.
Pure: no scene, no window."""
import pytest

from floorplanner.parametric import cabinet_geometry as cg
from floorplanner.parametric import findings as F
from floorplanner.parametric import registry

pytestmark = pytest.mark.furnishings


def _st(kind, **over):
    return cg.normalize_state(over, cg.PRESETS[kind])


def _named(parts, prefix):
    return [p for p in parts if p.name.startswith(prefix)]


def _extent(parts, axis):
    if axis == "z":
        return min(p.z0 for p in parts), max(p.z1 for p in parts)
    i = 0 if axis == "x" else 1
    vals = [q[i] for p in parts for q in p.quad]
    return min(vals), max(vals)


def test_a_base_cabinet_is_the_trades_dimensions():
    """34.5 in box on a 4.5 in toe kick set 3 in back, under a 1.5 in top that
    overhangs the doors by an inch -- 36 in to the counter."""
    st = _st("base_cab_36")
    parts = cg.cabinet_parts(st)
    kick = _named(parts, "toe-kick")[0]
    assert (kick.z0, kick.z1) == (0.0, 4.5)
    assert max(f for _x, f in kick.quad) == pytest.approx(24.0 - 3.0)
    carcass = _named(parts, "carcass")[0]
    assert (carcass.z0, carcass.z1) == (4.5, 34.5)
    top = _named(parts, "countertop")[0]
    assert (top.z0, top.z1) == (34.5, 36.0)
    assert max(f for _x, f in top.quad) == pytest.approx(25.0)
    assert _extent(parts, "z") == pytest.approx((0.0, 36.0))
    assert _extent(parts, "x") == pytest.approx((-18.0, 18.0))
    assert cg.overall_height(st) == 36.0 and cg.trade_code(st) == "B36"


def test_every_preset_stands_at_its_catalog_size():
    """What the generator also refuses to violate: width and depth are the
    footprint; the box plus its top is the catalog height."""
    for kind, preset in cg.PRESETS.items():
        st = cg.normalize_state({}, preset)
        parts = cg.cabinet_parts(st)
        assert parts, kind
        x0, x1 = _extent(parts, "x")
        assert x1 - x0 == pytest.approx(cg.footprint(st)[0]), kind
        assert _extent(parts, "f")[0] == pytest.approx(0.0), kind
        if not cg.is_mounted(st) and st["type"] != "light":
            assert _extent(parts, "z")[0] == pytest.approx(0.0), kind


def test_door_count_and_fronts():
    assert cg.door_count(_st("base_cab_24")) == 2
    assert cg.door_count(_st("drawer_base_18")) == 1
    assert cg.door_count(_st("base_cab_36", doors="1")) == 1
    two = cg.cabinet_parts(_st("base_cab_36", door_style="slab", front="doors"))
    assert len(_named(two, "door-")) == 2 and not _named(two, "drawer-")
    over = cg.cabinet_parts(_st("base_cab_36", door_style="slab"))
    assert len(_named(over, "door-")) == 2
    assert len([p for p in over if p.name in ("drawer-1", "drawer-2")]) == 2
    drawers = cg.cabinet_parts(_st("drawer_base_18", door_style="slab"))
    assert len([p for p in drawers if p.role == "cabinet"
                and p.name.startswith("drawer-")]) == 3
    assert not _named(drawers, "door-")


def test_a_five_piece_door_is_stiles_rails_and_a_recessed_panel():
    slab = cg.cabinet_parts(_st("wall_cab_24", door_style="slab", doors="1"))
    shaker = cg.cabinet_parts(_st("wall_cab_24", door_style="shaker", doors="1"))
    assert len(_named(slab, "door-1")) == 1
    pieces = {p.name: p for p in _named(shaker, "door-1")}
    assert set(pieces) == {"door-1-stile-l", "door-1-stile-r", "door-1-rail-b",
                           "door-1-rail-t", "door-1-panel"}
    front = max(f for _x, f in pieces["door-1-stile-l"].quad)
    assert max(f for _x, f in pieces["door-1-panel"].quad) < front, "recessed"
    glass = cg.cabinet_parts(_st("wall_cab_24", door_style="glass", doors="1"))
    assert [p.role for p in glass if p.name == "door-1-pane"] == ["glass"]


def test_overlay_sets_the_reveal_between_doors():
    def gap(overlay):
        doors = _named(cg.cabinet_parts(
            _st("base_cab_36", door_style="slab", front="doors", overlay=overlay)),
            "door-")
        left = max(x for x, _f in doors[0].quad)
        right = min(x for x, _f in doors[1].quad)
        return right - left
    assert gap("full") == pytest.approx(0.125)
    assert gap("partial") == pytest.approx(1.0)


def test_a_wall_cabinet_hangs_at_its_height_from_the_floor():
    """Patrick, 2026-11-14: the wall units have a height-from-floor parameter."""
    parts = cg.cabinet_parts(_st("wall_cab_30"))
    assert _extent(parts, "z") == pytest.approx((54.0, 84.0))
    assert not _named(parts, "toe-kick") and not _named(parts, "countertop")
    high = cg.cabinet_parts(_st("wall_cab_30", floor_to_bottom_in=60.0))
    assert _extent(high, "z") == pytest.approx((60.0, 90.0))
    assert cg.trade_code(_st("wall_cab_30")) == "W3030"


def test_a_sink_is_let_into_the_top():
    parts = cg.cabinet_parts(_st("sink_base_36"))
    floors = [p for p in parts if p.name.endswith("-floor")]
    assert len(floors) == 2, "a double bowl"
    assert all(p.z1 < 36.0 - 5.0 for p in floors)
    tops = [p for p in parts if p.role == "countertop"]
    for bowl in floors:                       # no top lies over a bowl
        bx = sum(x for x, _f in bowl.quad) / 4.0
        bf = sum(f for _x, f in bowl.quad) / 4.0
        for t in tops:
            xs = [x for x, _f in t.quad]
            fs = [f for _x, f in t.quad]
            assert not (min(xs) < bx < max(xs) and min(fs) < bf < max(fs))
    assert _named(cg.cabinet_parts(_st("sink_base_36", sink="none")), "bowl") == []
    assert [p.role for p in cg.cabinet_parts(_st("sink_base_36"))
            if p.name == "false-front-1"] == ["cabinet"]


def _bowl_cx(parts):
    floor = next(p for p in parts if p.name.endswith("-floor"))
    return sum(x for x, _f in floor.quad) / 4.0


def _faucet_cx(parts):
    post = next(p for p in parts if p.name == "faucet-post")
    return sum(x for x, _f in post.quad) / 4.0


def test_a_single_sink_slides_to_its_chosen_side():
    """0366: a single bowl honours `sink_side` -- it sits left, centred or
    right on the vanity top, and the faucet rides its centre. A double bowl
    stays centred whatever the side says."""
    centre = cg.cabinet_parts(_st("vanity_48", sink="single", sink_side="center"))
    left = cg.cabinet_parts(_st("vanity_48", sink="single", sink_side="left"))
    right = cg.cabinet_parts(_st("vanity_48", sink="single", sink_side="right"))
    assert _bowl_cx(centre) == pytest.approx(0.0, abs=0.5)
    assert _bowl_cx(left) < -4.0 and _bowl_cx(right) > 4.0
    assert _bowl_cx(left) == pytest.approx(-_bowl_cx(right), abs=1e-6)
    # the faucet follows the bowl, not the cabinet centre
    assert _faucet_cx(left) == pytest.approx(_bowl_cx(left), abs=0.1)
    assert _faucet_cx(right) == pytest.approx(_bowl_cx(right), abs=0.1)
    # the offset bowl still sits inside the cabinet
    w = cg.footprint(_st("vanity_48"))[0]
    assert all(-w / 2 <= x <= w / 2
               for p in left if p.name.endswith("-floor") for x, _f in p.quad)
    # a double bowl ignores the side
    da = cg.cabinet_parts(_st("vanity_48", sink="double", sink_side="left"))
    db = cg.cabinet_parts(_st("vanity_48", sink="double", sink_side="right"))
    assert _faucet_cx(da) == pytest.approx(0.0, abs=0.5)
    assert _faucet_cx(db) == pytest.approx(0.0, abs=0.5)


def test_sink_side_is_offered_only_for_a_single_bowl():
    """The dialog shows Sink position, enabled for a single bowl and greyed
    for none/double."""
    kind = registry.get("vanity_36")
    spec = next(s for s in kind.specs() if s.key == "sink_side")
    assert spec.enabled_fn({"sink": "single"})
    assert not spec.enabled_fn({"sink": "double"})
    assert not spec.enabled_fn({"sink": "none"})


def test_a_medicine_cabinet_is_a_mounted_mirrored_box():
    """0366: a medicine cabinet hangs at floor_to_bottom, a mirrored door on a
    carcass, and its default bar light glows."""
    st = _st("medicine_cabinet")
    parts = cg.cabinet_parts(st)
    assert cg.footprint(st) == (30.0, 4.5)
    assert cg.is_mounted(st)
    z0, _z1 = _extent(parts, "z")
    assert z0 == pytest.approx(40.0)                 # hung, not on the floor
    assert any(p.role == "cabinet" for p in parts)   # the box
    assert any(p.role == "mirror" for p in parts)    # the door
    assert any(p.role == "lens" for p in parts)      # the bar
    light = cg.light_source(st)
    assert light is not None and light["lumens"] == 800.0


def test_a_plain_mirror_has_no_box_and_its_depth_is_thin():
    st = _st("vanity_mirror")                         # has_cabinet off, backlit
    parts = cg.cabinet_parts(st)
    assert cg.footprint(st) == (36.0, 1.5)
    assert any(p.role == "mirror" for p in parts)
    assert len([p for p in parts if p.role == "lens"]) == 4   # the LED ring
    # a cabinet toggled on makes it a deeper box
    deep = _st("vanity_mirror", has_cabinet=True)
    assert cg.footprint(deep)[1] == 4.5


@pytest.mark.parametrize("style,lit", [("none", False), ("bar", True),
                                       ("sconces", True), ("backlit", True)])
def test_mirror_light_styles_light_or_not(style, lit):
    st = _st("medicine_cabinet", light_style=style)
    has_lens = any(p.role == "lens" for p in cg.cabinet_parts(st))
    assert has_lens is lit
    assert (cg.light_source(st) is not None) is lit
    # zero output keeps the fixture but casts no light
    assert cg.light_source(_st("medicine_cabinet", lumens=0)) is None


def test_mirror_units_are_parametric_with_their_own_controls():
    """The two bathroom wall units register as parametric kinds and offer the
    mirror controls (storage, light style), not the base-cabinet door fields."""
    for kind_id in ("medicine_cabinet", "vanity_mirror"):
        assert registry.is_parametric(kind_id)
        kind = registry.get(kind_id)
        keys = {s.key for s in kind.specs()}
        assert {"has_cabinet", "light_style", "light_colour"} <= keys
        assert "front" not in keys and "drawers" not in keys
        # the light colour only matters when it is lit
        colour = next(s for s in kind.specs() if s.key == "light_colour")
        assert colour.enabled_fn({"light_style": "bar"})
        assert not colour.enabled_fn({"light_style": "none"})


def _bowls(prims):
    return [p for p in prims if p[0] == "bowl"]


def test_the_vanity_plan_symbol_shows_the_sink_on_its_side():
    """0366: the drawn icon matches the unit -- a single bowl appears on its
    chosen side, not a stretched generic vanity."""
    left = cg.sink_base_plan(_st("vanity_48", sink="single", sink_side="left"))
    right = cg.sink_base_plan(_st("vanity_48", sink="single", sink_side="right"))
    lb, rb = _bowls(left), _bowls(right)
    assert len(lb) == len(rb) == 1
    assert (lb[0][1] + lb[0][3]) / 2.0 < -4.0        # bowl centre, left
    assert (rb[0][1] + rb[0][3]) / 2.0 > 4.0         # bowl centre, right
    assert _bowls(cg.sink_base_plan(_st("vanity_48", sink="none"))) == []
    assert len(_bowls(cg.sink_base_plan(_st("vanity_48", sink="double")))) == 2


def test_the_mirror_plan_symbol_shows_its_lights_and_storage():
    def bulbs(prims):
        return sum(p[0] == "bulb" for p in prims)
    assert bulbs(cg.mirror_plan(_st("medicine_cabinet", light_style="bar"))) >= 2
    assert bulbs(cg.mirror_plan(_st("medicine_cabinet", light_style="sconces"))) == 2
    assert bulbs(cg.mirror_plan(_st("medicine_cabinet", light_style="none"))) == 0
    # backlit adds ONE inner dashed border (a storage cabinet's box is solid)
    backlit = cg.mirror_plan(_st("medicine_cabinet", light_style="backlit"))
    assert sum(p[0] == "dashed" for p in backlit) == 1
    # a storage cabinet is a solid box with a door pull; a plain mirror is dashed
    cab = cg.mirror_plan(_st("medicine_cabinet"))
    assert cab[0][0] == "outline" and any(p[0] == "dot" for p in cab)
    assert cg.mirror_plan(_st("vanity_mirror"))[0][0] == "dashed"


def test_parametric_plan_symbols_route_through_the_registry():
    sym = registry.get("vanity_36").plan_symbol({"sink": "single",
                                                 "sink_side": "left"})
    assert "prims" in sym and any(p[0] == "bowl" for p in sym["prims"])
    assert "prims" in registry.get("medicine_cabinet").plan_symbol({})
    # a plain base keeps the catalog symbol (no parametric override)
    assert registry.get("base_cab_24").plan_symbol({}) is None


@pytest.mark.parametrize("corner", ["diagonal", "l_shape", "blind"])
def test_corner_types_build_and_stay_in_their_footprint(corner):
    st = _st("corner_base_36", corner_type=corner, depth_in=24.0)
    parts = cg.cabinet_parts(st)
    w, d = cg.footprint(st)
    assert (w, d) == ((36.0, 24.0) if corner == "blind" else (36.0, 36.0))
    x0, x1 = _extent(parts, "x")
    assert x0 >= -w / 2 - 1e-9 and x1 <= w / 2 + 1e-9
    assert _extent(parts, "f")[1] <= d + st["top_overhang_in"] + 1.3
    assert any(p.name.startswith("door") for p in parts)
    mirrored = cg.cabinet_parts(_st("corner_base_36", corner_type=corner,
                                    depth_in=24.0, hand="right"))
    assert sorted(-x for p in mirrored for x, _f in p.quad) == pytest.approx(
        sorted(x for p in parts for x, _f in p.quad))


# -- the style ---------------------------------------------------------------
def test_style_resolves_own_choice_then_room_then_default():
    """Patrick, 2026-11-14: the room carries the style; a cabinet follows it
    unless it sets its own."""
    st = _st("base_cab_36")
    assert cg.resolve_materials(st)["cabinet"] == "cab_maple"
    assert cg.resolve_materials(st)["countertop"] == "ct_quartz"
    room = {"cabinet_finish": "cherry", "countertop": "soapstone",
            "hardware": "matte_black"}
    got = cg.resolve_materials(st, room)
    assert (got["cabinet"], got["countertop"], got["hardware"]) == (
        "cab_cherry", "ct_soapstone", "hw_matte_black")
    own = cg.resolve_materials(_st("base_cab_36", finish="navy",
                                   top_material="marble"), room)
    assert (own["cabinet"], own["countertop"]) == ("cab_navy", "ct_marble")
    assert own["hardware"] == "hw_matte_black", "not overridden, so the room's"


def test_an_unknown_style_key_falls_back_instead_of_failing():
    got = cg.resolve_materials(_st("base_cab_36"),
                               {"cabinet_finish": "zebrawood", "countertop": 7})
    assert got["cabinet"] == "cab_maple" and got["countertop"] == "ct_quartz"
    assert cg.door_style_of(_st("base_cab_36"), {"door_style": "gothic"}) == "shaker"


def test_every_style_choice_names_a_material_that_exists():
    for table in (cg.FINISHES, cg.COUNTERTOPS, cg.HARDWARE):
        for key, label, material in table:
            assert key and label and material in cg.MATERIALS
    wanted = {"modern_white", "maple", "cherry", "oak"}
    assert wanted <= {k for k, _l, _m in cg.FINISHES}
    tops = {"marble", "tile", "quartz", "granite", "soapstone", "laminate"}
    assert tops <= {k for k, _l, _m in cg.COUNTERTOPS}


def test_appliance_finish_standard_match_and_custom():
    """Patrick, 2026-11-14: an appliance match feature, and special finishes
    -- matte, gloss, gel coat -- in a colour."""
    room = {"cabinet_finish": "cherry"}
    assert cg.resolve_materials(_st("dishwasher"), room)["appliance"] == "metal"
    assert cg.resolve_materials(_st("dishwasher", finish_mode="match"),
                                room)["appliance"] == "cab_cherry"
    custom = cg.resolve_materials(
        _st("range", finish_mode="custom", sheen="gel_coat", colour="red"))
    assert custom["appliance"] == "sheen_gel_coat#a3211c"
    assert "sheen_gel_coat" in cg.MATERIALS
    for kind in ("refrigerator", "range", "dishwasher", "washer", "dryer"):
        parts = cg.cabinet_parts(_st(kind))
        assert {"appliance"} <= {p.role for p in parts}, kind
        assert _extent(parts, "z")[1] >= cg.PRESETS[kind]["height_in"]


# -- the state ---------------------------------------------------------------
def test_normalize_is_stable_tolerant_and_keeps_unknown_keys():
    st = cg.normalize_state({"width_in": "33", "front": "nonsense",
                             "drawers": "many", "future": 1, "type": "wall"},
                            cg.PRESETS["base_cab_36"])
    assert st["width_in"] == 33.0 and st["front"] == "drawer_over_doors"
    assert st["drawers"] == 3 and st["future"] == 1
    assert st["type"] == "base", "the KIND decides the type, never the file"
    assert cg.normalize_state(st, cg.PRESETS["base_cab_36"]) == st


def test_only_what_differs_from_the_preset_is_written():
    kind = registry.get("base_cab_36")
    assert kind.to_state(kind.normalize({})) == {}
    edited = kind.normalize({"width_in": 33.0, "finish": "navy"})
    assert kind.to_state(edited) == {"finish": "navy", "width_in": 33.0}
    assert kind.footprint({"width_in": 33.0}) == (33.0, 24.0)
    assert kind.footprint({}) == (36.0, 24.0)


def test_every_preset_kind_is_registered_and_evaluates_clean():
    for name in cg.PRESETS:
        kind = registry.get(name)
        assert kind is not None and registry.is_parametric(name)
        derived, fs = kind.evaluate(kind.normalize({}), {"room_style": None})
        assert derived is not None and derived["parts"]
        assert not F.blocks(fs) and not F.needs_ack(fs), name
        assert kind.summary(kind.normalize({}), derived, {})


def test_advisories_inform_and_never_block():
    kind = registry.get("base_cab_36")
    _d, fs = kind.evaluate(kind.normalize({"width_in": 31.0, "doors": "1",
                                           "front": "doors"}), {})
    rules = {f.rule_id: f.severity for f in fs}
    assert rules == {"width.module": F.ADVISORY, "door.wide": F.ADVISORY}
    wall = registry.get("wall_cab_30")
    _d, fs = wall.evaluate(wall.normalize({"floor_to_bottom_in": 46.0}), {})
    assert [f.rule_id for f in fs] == ["wall.clearance"]
    assert not F.blocks(fs) and not F.needs_ack(fs)
