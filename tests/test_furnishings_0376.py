"""0376 (Patrick, 2026-11-26): a corner desk that is one, a sized armchair, the
umbrella table with chairs and parasol, tub styles / showers / enclosures,
woven wicker and a wicker loveseat, a wall TV by its diagonal, and decor.
Qt-free: the calculator and the registered kinds only."""
import pytest

from floorplanner.parametric import cabinet_geometry as cg
from floorplanner.parametric import findings as F
from floorplanner.parametric import registry

pytestmark = pytest.mark.furnishings

NEW = ("wicker_loveseat", "wall_art", "table_picture", "plant_floor",
       "plant_small", "table_arrangement", "floor_vase")
CONVERTED = ("corner_desk", "armchair", "umbrella_table", "large_tv",
             "wicker_chair", "wicker_chair_small", "wicker_table")


def _st(kind, **over):
    return cg.normalize_state(over, cg.PRESETS[kind])


def _parts(kind, **over):
    return cg.cabinet_parts(_st(kind, **over))


def _by(parts):
    return {p.name: p for p in parts}


def _ext(parts, i):
    vals = [q[i] for p in parts for q in p.quad]
    return min(vals), max(vals)


def _top(parts):
    return max(p.z1 for p in parts)


def test_the_new_kinds_are_presets_registered_and_evaluate_clean():
    for name in NEW + CONVERTED:
        assert name in cg.PRESETS, name
        kind = registry.get(name)
        assert kind is not None and registry.is_parametric(name)
        derived, fs = kind.evaluate(kind.normalize({}), {"room_style": None})
        assert derived["parts"] and not F.blocks(fs), name
        assert kind.summary(kind.normalize({}), derived, {})[0][0] == "Fixture"
        assert kind.to_state(kind.normalize({})) == {}, name


def test_no_part_carries_a_role_without_a_material():
    for name in NEW + CONVERTED + ("bathtub",):
        st = _st(name)
        mats = cg.resolve_materials(st)
        for p in cg.cabinet_parts(st):
            assert p.role in mats, (name, p.name, p.role)


# -- 1. the corner desk --------------------------------------------------------
def test_the_corner_desk_is_an_l_on_three_legs():
    parts = _by(_parts("corner_desk"))
    main, ret = parts["top-main"], parts["top-return"]
    assert _ext([main], 0) == (-30.0, 30.0) and _ext([main], 1) == (0.0, 24.0)
    assert _ext([ret], 0) == (-30.0, -6.0), "the return is 24 deep, on the left"
    assert _ext([ret], 1) == (24.0, 60.0)
    assert sum(1 for n in parts if n.startswith("foot-")) == 3
    assert main.z1 == 30.0 and all(parts[f"column-{t}-upper"].z1 < main.z0
                                   for t in ("main", "corner", "return"))
    # nothing under the open quarter of the square: it is an L, not a slab
    assert not [p for p in parts.values()
                if min(x for x, _f in p.quad) > -5.0 and min(f for _x, f in p.quad) > 25.0]


def test_the_corner_desk_turns_its_hand_and_takes_the_e7l_sizes():
    left = _by(_parts("corner_desk"))["top-return"]
    right = _by(_parts("corner_desk", hand="right"))["top-return"]
    assert _ext([right], 0) == (6.0, 30.0) == tuple(-v for v in reversed(_ext([left], 0)))
    st = _st("corner_desk", width_in=63, depth_in=47, height_in=49.2)
    assert cg.footprint(st) == (63.0, 47.0) and _top(cg.cabinet_parts(st)) == 49.2
    assert cg.footprint(_st("corner_desk", width_in=20, depth_in=20)) == (42.0, 42.0)
    kind = registry.get("corner_desk")
    ring = kind.plan_symbol({"hand": "right"})["prims"][0]
    assert ring[0] == "poly" and len(ring[2]) == 6, "the plan symbol is the L"
    assert max(x for x, _f in ring[2]) < 30.0 and min(x for x, _f in ring[2]) < -29.0


# -- 2. the armchair -----------------------------------------------------------
def test_the_armchair_takes_its_height_width_and_depth():
    base = _parts("armchair")
    assert _ext(base, 0) == (-16.5, 16.5) and _ext(base, 1) == (0.0, 33.0)
    assert _top(base) == 32.0
    big = _parts("armchair", width_in=40, depth_in=36, height_in=40)
    assert _ext(big, 0) == (-20.0, 20.0) and _ext(big, 1)[1] == 36.0 and _top(big) == 40.0
    seat = _by(big)["seat-cushion"]
    assert seat.z1 == cg.ARM_SEAT_Z, "the seat stays a seat, whatever the back"
    assert _by(big)["arm-l"].z1 > seat.z1 > _by(big)["base"].z1
    assert {p.role for p in big} == {"upholstery", "appliance_dark"}
    assert cg.resolve_materials(_st("armchair", colour="red"))["upholstery"].endswith("#a3211c")


# -- 3. the umbrella table -----------------------------------------------------
def test_the_umbrella_table_is_a_square_table_four_chairs_and_a_parasol():
    parts = _parts("umbrella_table")
    named = _by(parts)
    top = named["top"]
    assert _ext([top], 0) == (-21.0, 21.0) and _ext([top], 1) == (27.0, 69.0)
    seats = [p for p in parts if p.name.endswith("chair-seat")]
    assert len(seats) == 4
    centres = sorted((round(sum(x for x, _f in p.quad) / 4.0), round(sum(f for _x, f in p.quad) / 4.0))
                     for p in seats)
    assert centres == [(-37, 48), (0, 12), (0, 85), (37, 48)] or len(set(centres)) == 4
    canopy = [p for p in parts if p.name.startswith("canopy-")]
    assert len(canopy) >= 6 and min(p.z0 for p in canopy) == cg.PARASOL_Z
    assert all(len(p.quad) == 8 for p in canopy)
    widths = [max(x for x, _f in p.quad) for p in sorted(canopy, key=lambda p: p.z0)]
    assert widths == sorted(widths, reverse=True), "it narrows to the peak"
    assert named["pole"].z1 > max(p.z1 for p in canopy) - 1.0
    assert top.z1 == 30.0 < cg.PARASOL_Z


def test_the_umbrella_table_grows_with_its_table():
    st = _st("umbrella_table", size_in=60)
    assert cg.footprint(st) == (114.0, 114.0)
    assert _ext([_by(cg.cabinet_parts(st))["top"]], 0) == (-30.0, 30.0)
    assert cg.footprint(_st("umbrella_table", size_in=500)) == (126.0, 126.0)
    prims = registry.get("umbrella_table").plan_symbol({"size_in": 60})["prims"]
    assert sum(1 for p in prims if p[0] == "outline") == 4 and prims[0][1] == "dashed"


# -- 4. the tub ----------------------------------------------------------------
def test_the_alcove_tub_is_what_it_was():
    names = [p.name for p in _parts("bathtub")]
    assert names[:5] == ["floor", "wall-l", "wall-r", "wall-head", "wall-foot"]
    assert len(names) == 15 and _top(_parts("bathtub")) == 25.0


def test_tub_styles():
    insert = _by(_parts("bathtub", tub_style="insert"))
    assert insert["surround-head"].z1 == cg.SURROUND_Z == insert["surround-back"].z1
    assert _ext([insert["surround-back"]], 0)[0] == -15.0, "wall on the left by default"
    right = _by(_parts("bathtub", tub_style="insert", hand="right"))
    assert _ext([right["surround-back"]], 0)[1] == 15.0
    walk = _st("bathtub", tub_style="walk_in")
    assert walk["height_in"] == cg.WALK_IN_H
    named = _by(cg.cabinet_parts(walk))
    assert {"door", "door-sill", "door-lever", "seat", "grab-bar"} <= set(named)
    assert _ext([named["door"]], 0)[1] <= 15.0 and _ext([named["door"]], 0)[0] > 10.0
    assert named["seat"].z1 == 17.0
    claw = _parts("bathtub", tub_style="clawfoot")
    assert sum(1 for p in claw if p.name.startswith("claw-")) == 4
    shell = [p for p in claw if p.name.startswith("shell-")]
    assert len(shell) == 16 and min(p.z0 for p in shell) > 6.0, "it stands on its feet"


def test_tub_showers_and_enclosures():
    assert not [p for p in _parts("bathtub") if p.name.startswith("shower")]
    single = _by(_parts("bathtub", shower="single"))
    assert single["shower-head"].z1 > 70.0 and "rain-head" not in single
    multi = _by(_parts("bathtub", shower="multi"))
    assert {"shower-head", "rain-head", "hand-shower", "body-spray-3"} <= set(multi)
    glass = _by(_parts("bathtub", enclosure="glass"))
    assert glass["glass-fixed"].role == "glass" and glass["glass-sliding"].z1 > 70.0
    assert _ext([glass["glass-fixed"]], 0)[0] > 10.0, "on the open side"
    curtain = [p for p in _parts("bathtub", enclosure="curtain")
               if p.name.startswith("curtain-")]
    assert len(curtain) >= 3 and {p.role for p in curtain} == {"curtain"}
    for style in ("alcove", "insert", "walk_in", "clawfoot"):
        for shower in ("none", "single", "multi"):
            for enc in ("none", "glass", "curtain"):
                ps = _parts("bathtub", tub_style=style, shower=shower, enclosure=enc)
                assert _ext(ps, 0) == (-15.0, 15.0), (style, shower, enc)
                assert _ext(ps, 1)[0] == 0.0 and _ext(ps, 1)[1] <= 60.0 + 1e-9


# -- 5, 6. wicker --------------------------------------------------------------
def test_wicker_is_woven_in_two_tones_over_a_dark_core():
    for kind in ("wicker_chair", "wicker_chair_small", "wicker_loveseat"):
        parts = _parts(kind)
        roles = {p.role for p in parts}
        assert {"wicker", "wicker_light", "wicker_dark", "upholstery"} <= roles, kind
        back = [p for p in parts if p.name.startswith("back-strand-")]
        assert len(back) >= 8, "rows of strands"
        proud = sorted({round(min(f for _x, f in p.quad), 2) for p in back})
        assert len(proud) == 2, "alternate rows stand prouder: the weave"
        assert [p.role for p in back[:2]] == ["wicker", "wicker_light"]
        stakes = [p for p in parts if p.name.startswith("back-stake-")]
        assert len(stakes) >= 4 and all(p.role == "wicker_dark" for p in stakes)
        st = _st(kind)
        assert _ext(parts, 0) == (-st["width_in"] / 2.0, st["width_in"] / 2.0)
        assert _ext(parts, 1) == (0.0, st["depth_in"]) and _top(parts) == st["height_in"]
    table = _parts("wicker_table")
    assert [p.role for p in table if p.name.startswith("ring-")][:2] == ["wicker", "wicker_light"]
    assert _by(table)["top"].role == "glass"


def test_the_wicker_loveseat_seats_two_and_keeps_the_chairs_smaller():
    love = _parts("wicker_loveseat")
    assert sum(1 for p in love if p.name.startswith("cushion-")) == 2
    assert cg.footprint(_st("wicker_loveseat")) == (50.0, 29.0)
    assert cg.footprint(_st("wicker_chair")) == (27.0, 28.0)
    assert cg.footprint(_st("wicker_chair_small")) == (23.0, 24.0)
    assert sum(1 for p in _parts("wicker_loveseat", seats=3, width_in=72)
               if p.name.startswith("cushion-")) == 3
    assert cg.footprint(_st("wicker_chair")) < cg.footprint(_st("armchair"))


# -- 7. the wall TV ------------------------------------------------------------
def test_the_wall_tv_is_sized_by_its_diagonal_and_hangs_where_it_is_set():
    st = _st("large_tv")
    assert (st["width_in"], st["height_in"], st["size_in"]) == (66.0, 38.0, 75.0)
    assert cg.is_mounted(st) and cg.overall_height(st) == 80.0
    parts = cg.cabinet_parts(st)
    assert min(p.z0 for p in parts) == 42.0 and _top(parts) == 80.0
    assert {p.role for p in parts} >= {"screen", "appliance_dark"}
    small = _st("large_tv", size_in=43, floor_to_bottom_in=50)
    assert cg.footprint(small) == (38.0, 4.0) and small["height_in"] == 22.0
    assert min(p.z0 for p in cg.cabinet_parts(small)) == 50.0
    assert _st("large_tv", size_in=5)["size_in"] == 19.0
    assert _st("large_tv", width_in=10)["width_in"] == 66.0, "the diagonal decides"


# -- 8. decor ------------------------------------------------------------------
def test_wall_art_hangs_and_paints_what_it_is_told():
    st = _st("wall_art")
    parts = cg.cabinet_parts(st)
    assert min(p.z0 for p in parts) == 48.0 and _top(parts) == 72.0
    assert sum(1 for p in parts if p.name.startswith("frame-")) == 4
    subjects = {}
    for art, _label in cg.ART_STYLES:
        ps = _parts("wall_art", art=art)
        subjects[art] = tuple(p.role for p in ps if p.name.startswith("art-"))
        faces = [max(f for _x, f in p.quad) for p in ps if p.name.startswith("art-")]
        assert faces == sorted(faces) and len(set(faces)) == len(faces), "no two coplanar"
        frame = max(f for p in ps if p.name.startswith("frame-") for _x, f in p.quad)
        assert max(faces) < frame, "the picture sits inside its frame"
    assert len(set(subjects.values())) == len(cg.ART_STYLES)
    big = _parts("wall_art", width_in=60, height_in=40, floor_to_bottom_in=36)
    assert _ext(big, 0) == (-30.0, 30.0) and _top(big) == 76.0


def test_what_stands_on_a_table_stands_at_its_height():
    for kind in ("table_picture", "plant_small", "table_arrangement"):
        assert min(p.z0 for p in _parts(kind)) == 30.0, kind
        assert min(p.z0 for p in _parts(kind, floor_to_bottom_in=42)) == 42.0, kind
    for kind in ("plant_floor", "floor_vase"):
        assert min(p.z0 for p in _parts(kind)) == 0.0, kind


def test_plants_have_a_pot_and_a_green_head_and_a_vase_its_branches():
    plant = _parts("plant_floor")
    assert {"terracotta", "soil", "foliage", "foliage_dark"} <= {p.role for p in plant}
    pot_top = max(p.z1 for p in plant if p.role == "terracotta")
    assert min(p.z0 for p in plant if p.role.startswith("foliage")) > pot_top
    assert _top(plant) == 60.0 and _top(_parts("plant_floor", height_in=84)) == 84.0
    vase = _parts("floor_vase")
    assert any(p.name.startswith("branch-") for p in vase)
    empty = _parts("floor_vase", vase_fill="empty")
    assert not any(p.name.startswith("branch-") for p in empty) and _top(empty) == 30.0
    radii = [max(x for x, _f in p.quad) for p in empty]
    assert max(radii) == 6.0 and min(radii) < 3.5, "it has a belly and a neck"
    blooms = [p for p in _parts("table_arrangement") if p.name.startswith("bloom-")]
    assert len(blooms) >= 5 and len({p.role for p in blooms}) >= 3


def test_nonsense_falls_back():
    st = _st("bathtub", tub_style="jacuzzi", shower="yes", enclosure=3)
    assert (st["tub_style"], st["shower"], st["enclosure"]) == ("alcove", "none", "none")
    assert _st("wall_art", art="dogs playing poker")["art"] == "abstract"
    assert _st("floor_vase", vase_fill=None)["vase_fill"] == "branches"


# -- 0377: three pictures hung as one, 2 - 3 - 4 --------------------------------
def test_the_picture_arrangement_is_three_frames_two_three_four():
    st = _st("picture_trio")
    frames = cg.trio_frames(st)
    widths = [x1 - x0 for x0, x1, _a, _b, _k in frames]
    assert widths == pytest.approx([66.0 * 2 / 9, 66.0 * 3 / 9, 66.0 * 4 / 9])
    assert frames[0][0] == -36.0 and frames[-1][1] == pytest.approx(36.0)
    gaps = [b[0] - a[1] for a, b in zip(frames, frames[1:], strict=False)]
    assert gaps == pytest.approx([3.0, 3.0])
    assert {(z0, z1) for _a, _b, z0, z1, _k in frames} == {(0.0, 30.0)}, "one height"
    parts = cg.cabinet_parts(st)
    assert sum(1 for p in parts if p.name.endswith("frame-top")) == 3
    assert min(p.z0 for p in parts) == 44.0 and _top(parts) == 74.0
    assert _ext(parts, 0) == pytest.approx((-36.0, 36.0)) and _ext(parts, 1)[0] == 0.0
    kind = registry.get("picture_trio")
    derived, fs = kind.evaluate(kind.normalize({}), {"room_style": None})
    assert derived["parts"] and not F.blocks(fs)
    assert len(kind.plan_symbol({})["prims"]) == 3


def test_the_three_pictures_differ_and_share_one_palette():
    for art, _label in cg.ART_STYLES:
        ps = _parts("picture_trio", art=art)
        per = {tag: tuple((p.role, round(p.z1 - p.z0, 3)) for p in ps
                          if p.name.startswith(f"{tag}-art-")) for tag in ("p1", "p2", "p3")}
        assert len(set(per.values())) == 3, f"{art}: three different pictures"
        roles = [{r for r, _h in v} for v in per.values()]
        assert roles[0] & roles[1] & roles[2], f"{art}: one palette runs through them"
    abstract = _parts("picture_trio")
    area = {}
    for p in abstract:
        if "-art-" in p.name and p.role in ("art_blue", "art_ochre"):
            xs = [x for x, _f in p.quad]
            key = (p.name[:2], p.role)
            area[key] = area.get(key, 0.0) + (max(xs) - min(xs)) * (p.z1 - p.z0)
    w1, w3 = 66.0 * 2 / 9, 66.0 * 4 / 9
    assert area[("p1", "art_blue")] / w1 > area[("p1", "art_ochre")] / w1
    assert area[("p3", "art_ochre")] / w3 > area[("p3", "art_blue")] / w3, (
        "blue leads on the left, its complement on the right")


def test_the_arrangement_turns_round_steps_and_keeps_its_gap():
    asc = cg.trio_frames(_st("picture_trio"))
    desc = cg.trio_frames(_st("picture_trio", trio_order="descending"))
    assert [k for *_r, k in asc] == [0, 1, 2] and [k for *_r, k in desc] == [2, 1, 0]
    assert desc[0][1] - desc[0][0] == pytest.approx(asc[2][1] - asc[2][0])
    stepped = cg.trio_frames(_st("picture_trio", trio_shape="stepped"))
    heights = [z1 - z0 for _a, _b, z0, z1, _k in stepped]
    assert heights == pytest.approx([15.0, 22.5, 30.0])
    assert {round((z0 + z1) / 2.0, 6) for _a, _b, z0, z1, _k in stepped} == {15.0}
    wide = cg.trio_frames(_st("picture_trio", width_in=120, gap_in=6))
    assert wide[1][0] - wide[0][1] == pytest.approx(6.0)
    assert sum(x1 - x0 for x0, x1, *_r in wide) == pytest.approx(108.0)
    assert _st("picture_trio", width_in=5, gap_in=50)["width_in"] == 42.0
    assert _st("picture_trio", trio_order="sideways")["trio_order"] == "ascending"
