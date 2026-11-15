"""Fixtures built from parts -- toilet, bathtub, bookshelf, fireplace, grab
bar -- the island's added slots, and its plan symbol (0338). Pure:
`cabinet_geometry.py` and its kinds."""
import pytest

from floorplanner.parametric import cabinet_geometry as cg
from floorplanner.parametric import findings as F
from floorplanner.parametric import registry

pytestmark = pytest.mark.furnishings


def _st(kind, **over):
    return cg.normalize_state(over, cg.PRESETS[kind])


def _parts(kind, **over):
    return cg.cabinet_parts(_st(kind, **over))


def _span(parts, axis):
    if axis == "z":
        return min(p.z0 for p in parts), max(p.z1 for p in parts)
    i = 0 if axis == "x" else 1
    vals = [q[i] for p in parts for q in p.quad]
    return min(vals), max(vals)


FIXTURES = ("toilet", "bathtub", "bookshelf", "gas_fireplace", "grab_bar")


@pytest.mark.parametrize("kind", FIXTURES)
def test_a_fixture_fills_its_footprint_and_nothing_more(kind):
    st = _st(kind)
    parts = cg.cabinet_parts(st)
    w, d = cg.footprint(st)
    x0, x1 = _span(parts, "x")
    f0, f1 = _span(parts, "f")
    assert (x0, x1) == pytest.approx((-w / 2, w / 2))
    assert f0 == pytest.approx(0.0) and f1 <= d + 1e-9
    z0, z1 = _span(parts, "z")
    assert z1 == pytest.approx(cg.overall_height(st)) or kind == "bathtub"
    assert z0 == pytest.approx(st["floor_to_bottom_in"] if cg.is_mounted(st)
                               else 0.0)
    assert len({p.name for p in parts}) == len(parts), "part names are unique"


@pytest.mark.parametrize("kind", FIXTURES)
def test_every_fixture_role_resolves_to_a_material(kind):
    st = _st(kind)
    mats = cg.resolve_materials(st)
    for p in cg.cabinet_parts(st):
        assert p.role in mats, (kind, p.name, p.role)


def test_the_kind_decides_the_model_never_the_file():
    assert _st("toilet", model="fireplace")["model"] == "toilet"
    assert _st("toilet", width_in=99.0)["width_in"] == 20.0, "one size"


def test_a_toilet_has_a_tank_a_round_bowl_and_a_seat():
    parts = {p.name: p for p in _parts("toilet")}
    assert parts["tank"].z1 > parts["bowl"].z1 > parts["pedestal"].z1
    assert len(parts["bowl"].quad) > 4, "the bowl is an oval, not a box"
    assert parts["seat"].z0 == pytest.approx(parts["bowl"].z1)
    assert min(f for _x, f in parts["bowl"].quad) > max(
        f for _x, f in parts["tank"].quad) - 2.0, "bowl out from the tank"
    mats = cg.resolve_materials(_st("toilet", colour="black"))
    assert mats["porcelain"] == "sheen_gloss#16181b" or mats[
        "porcelain"].startswith("sheen_gloss#")
    assert _st("toilet", colour="red")["colour"] == "white"


def test_a_tub_is_a_shell_round_an_open_well():
    st = _st("bathtub")
    parts = cg.cabinet_parts(st)
    rim = st["height_in"]
    over_centre = [p for p in parts
                   if p.z1 > rim - 1e-6 and len(p.quad) == 4
                   and min(x for x, _f in p.quad) < 0 < max(x for x, _f in p.quad)
                   and min(f for _x, f in p.quad) < 30 < max(f for _x, f in p.quad)]
    assert not over_centre, "nothing roofs the well"
    floor = next(p for p in parts if p.name == "floor")
    assert floor.z1 == 4.0
    assert sum(1 for p in parts if p.name.startswith("ease-")) == 4
    longer = cg.cabinet_parts(_st("bathtub", depth_in=72.0))
    assert _span(longer, "f")[1] == pytest.approx(72.0)


@pytest.mark.parametrize("shelves", [0, 3, 6])
def test_a_bookshelf_has_the_shelves_asked_for(shelves):
    parts = _parts("bookshelf", shelves=shelves, books=False)
    assert sum(1 for p in parts if p.name.startswith("shelf-")) == shelves
    assert not [p for p in parts if p.name.startswith("book-")]


def test_books_sit_on_shelves_inside_the_case_and_never_change():
    st = _st("bookshelf")
    parts = cg.cabinet_parts(st)
    books = [p for p in parts if p.name.startswith("book-")]
    assert len(books) > 20
    tops = sorted(p.z1 for p in parts
                  if p.name == "bottom" or p.name.startswith("shelf-"))
    for b in books:
        assert any(abs(b.z0 - t) < 1e-9 for t in tops), b.name
        above = [t for t in tops if t > b.z0 + 1e-9]
        if above:
            assert b.z1 < above[0], f"{b.name} pokes through the shelf above"
        xs = [x for x, _f in b.quad]
        assert -18.0 + 0.75 <= min(xs) and max(xs) <= 18.0 - 0.75
    assert cg.cabinet_parts(st) == parts, "deterministic"


def test_a_fireplace_has_an_open_firebox_and_flames_only_when_lit():
    lit = {p.name: p for p in _parts("gas_fireplace")}
    assert lit["header"].z0 == pytest.approx(lit["firebox-back"].z1)
    assert lit["mantel"].z1 == 40.0 and lit["hearth"].z1 == 2.0
    flames = [p for n, p in lit.items() if n.startswith("flame-")]
    assert len(flames) == 5
    assert all(p.z1 < lit["header"].z0 for p in flames), "flames stay in the box"
    assert cg.resolve_materials(_st("gas_fireplace"))["flame"].startswith(
        "light_emit#")
    out = _parts("gas_fireplace", lit=False)
    assert not [p for p in out if p.name.startswith("flame-")]
    mats = cg.resolve_materials(_st("gas_fireplace", surround="brick"))
    assert mats["surround"] == "fp_brick"


def test_a_grab_bar_hangs_at_its_height_and_turns_upright():
    st = _st("grab_bar")
    assert cg.is_mounted(st) and cg.footprint(st) == (24.0, 3.5)
    bar = next(p for p in cg.cabinet_parts(st) if p.name == "bar")
    assert (bar.z0 + bar.z1) / 2 == pytest.approx(32.0 + 1.5)
    assert min(f for _x, f in bar.quad) == cg.BAR_CLEAR, "1.5 in off the wall"
    up = _st("grab_bar", bar="vertical", length_in=36.0)
    assert cg.footprint(up) == (3.0, 3.5) and cg.overall_height(up) == 32.0 + 36.0
    bar = next(p for p in cg.cabinet_parts(up) if p.name == "bar")
    assert bar.z1 - bar.z0 == 36.0
    _d, fs = registry.get("grab_bar").evaluate({"floor_to_bottom_in": 40.0}, {})
    assert [f.rule_id for f in fs] == ["bar.height"]
    assert fs[0].severity == F.ADVISORY
    assert registry.get("grab_bar").evaluate({}, {})[1] == []


@pytest.mark.parametrize("kind", FIXTURES)
def test_each_fixture_has_a_dialog_definition_that_stores_only_changes(kind):
    definition = registry.get(kind)
    assert definition is not None and definition.title == "Fixture Properties"
    assert definition.specs()
    assert definition.to_state({}) == {}
    derived, findings = definition.evaluate({}, {})
    assert derived is not None and not F.blocks(findings)
    assert definition.summary({}, derived, {})


# -- the island's added slots ------------------------------------------------
def _island(**over):
    return _st("kitchen_island", **over)


def test_the_new_slot_codes_exist_at_their_widths():
    table = {row[0]: row for row in cg.ISLAND_SLOTS}
    for code, width in (("BS18", 18), ("BS24", 24), ("CT30", 30), ("CT36", 36),
                        ("RG30", 30), ("WC15", 15), ("WC24", 24), ("MW24", 24)):
        assert table[code][2] == width
    st = _island(slot_1="BS18", slot_2="CT36", slot_3="WC24", slot_4="RG30",
                 slot_5="MW24")
    assert st["width_in"] == 18 + 36 + 24 + 30 + 24


def test_a_bar_sink_has_one_small_bowl_and_the_top_is_open_over_it():
    st = _island(slot_1="BS18", slot_2="B36")
    parts = cg.cabinet_parts(st)
    floors = [p for p in parts if p.name.endswith("bowl-1-floor")]
    assert len(floors) == 1
    xs = [x for x, _f in floors[0].quad]
    assert max(xs) - min(xs) == pytest.approx(12.0)
    bx = sum(xs) / 4.0
    bf = sum(f for _x, f in floors[0].quad) / 4.0
    top = st["height_in"] + st["top_thickness_in"]
    for p in parts:
        if p.role != "countertop":
            continue
        px = [x for x, _f in p.quad]
        pf = [f for _x, f in p.quad]
        assert not (min(px) < bx < max(px) and min(pf) < bf < max(pf)), p.name
    assert max(p.z1 for p in parts if p.role == "countertop") == top


def test_a_range_stands_through_the_top_with_no_backguard():
    st = _island(slot_1="B24", slot_2="RG30", slot_3="B24")
    parts = cg.cabinet_parts(st)
    top = st["height_in"] + st["top_thickness_in"]
    rng = [p for p in parts if p.name.startswith("slot2-RG30-")]
    assert max(p.z1 for p in rng) == pytest.approx(top), "flush with the counter"
    assert not [p for p in rng if p.name.endswith("backguard")]
    cook = next(p for p in rng if p.name.endswith("-cooktop"))
    cx = sum(x for x, _f in cook.quad) / 4.0
    cf = sum(f for _x, f in cook.quad) / 4.0
    tops = [p for p in parts if p.role == "countertop"]
    for p in tops:
        px = [x for x, _f in p.quad]
        pf = [f for _x, f in p.quad]
        assert not (min(px) < cx < max(px) and min(pf) < cf < max(pf)), p.name
    # the top still runs behind the range, over the seating overhang
    behind = cg.ISLAND_FRONT_SETBACK + cg.ISLAND_CABINET_D + 3.0
    assert any(min(x for x, _f in p.quad) < cx < max(x for x, _f in p.quad)
               and min(f for _x, f in p.quad) < behind < max(f for _x, f in p.quad)
               for p in tops)
    area = sum((max(x for x, _f in p.quad) - min(x for x, _f in p.quad))
               * (max(f for _x, f in p.quad) - min(f for _x, f in p.quad))
               for p in tops)
    assert area == pytest.approx(78.0 * 39.0 - 30.0 * (
        cg.ISLAND_FRONT_SETBACK + cg.ISLAND_CABINET_D))


def test_a_cooktop_sits_on_the_counter_with_four_burners():
    st = _island(slot_1="CT36")
    parts = cg.cabinet_parts(st)
    top = st["height_in"] + st["top_thickness_in"]
    glass = next(p for p in parts if p.name == "slot1-CT36-cooktop")
    assert glass.z0 == pytest.approx(top)
    burners = [p for p in parts if "-burner-" in p.name]
    assert len(burners) == 4 and all(len(p.quad) > 4 for p in burners)
    assert [p for p in parts if p.name.startswith("slot1-CT36-drawer")]


def test_a_wine_cooler_and_a_microwave_drawer_stand_under_the_counter():
    st = _island(slot_1="WC24", slot_2="MW24")
    parts = cg.cabinet_parts(st)
    for tag in ("slot1-WC24-", "slot2-MW24-"):
        mine = [p for p in parts if p.name.startswith(tag)]
        assert mine and max(p.z1 for p in mine) <= st["height_in"] + 1e-9
    assert any(p.role == "glass" for p in parts if p.name.startswith("slot1-"))


# -- the island's plan symbol --------------------------------------------------
@pytest.mark.parametrize("seats", [0, 1, 3, 5, 8])
def test_the_plan_symbol_draws_one_stool_per_seat(seats):
    st = _island(seats=seats)
    plan = cg.island_plan(st)
    assert len(plan["stools"]) == seats
    assert plan["top"] == (-36.0, 0.0, 36.0, 39.0)
    n3d = sum(1 for p in cg.cabinet_parts(st) if p.name.endswith("-seat"))
    assert n3d == seats, "the symbol and the 3D agree"
    for x0, f0, x1, f1 in plan["stools"]:
        assert -36.0 <= x0 < x1 <= 36.0 and plan["back"] < f0 < f1 <= 39.0


def test_the_plan_symbol_shows_slots_bowls_and_hobs_where_the_3d_has_them():
    st = _st("island_sink", slot_4="CT30")
    plan = cg.island_plan(st)
    assert [c for _a, _b, c in plan["slots"]] == ["B24", "SB36", "DW24", "CT30"]
    assert plan["slots"][0][1] == st["width_in"] / 2.0, "slot 1 at +x"
    assert len(plan["bowls"]) == 2 and len(plan["hobs"]) == 1
    parts = cg.cabinet_parts(st)
    floors = sorted(sum(x for x, _f in p.quad) / 4.0 for p in parts
                    if p.name.endswith("-floor") and "bowl" in p.name)
    assert sorted((b[0] + b[2]) / 2.0 for b in plan["bowls"]) == pytest.approx(floors)


def test_only_an_island_draws_its_own_symbol():
    assert registry.get("kitchen_island").plan_symbol({"seats": 2})["stools"]
    assert registry.get("base_cab_24").plan_symbol({}) is None
    assert registry.get("toilet").plan_symbol({}) is None
