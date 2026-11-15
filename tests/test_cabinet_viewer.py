"""Cabinets in 3D (0329): parts in the room's style, at the catalog size.
`fp3d.py` is loaded by path, as `test_viewer_model.py` loads it."""
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pytest

pytestmark = pytest.mark.viewer

ROOT = Path(__file__).resolve().parents[1]
FURN_DIR = ROOT / "assets" / "furnishings"


@pytest.fixture(scope="module")
def fp3d():
    path = ROOT / "floorplanner" / "viewer" / "fp3d.py"
    spec = importlib.util.spec_from_file_location("fp3d_cabinet_test", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def manifest():
    return json.loads((FURN_DIR / "manifest.json").read_text(encoding="utf-8"))


def _doc(kind, state=None, style=None, rotation=0.0):
    fu = {"id": "f1", "level": "L1", "kind": kind, "room": "r1",
          "pos": [0.0, 0.0], "rotation": rotation}
    if state is not None:
        fu["state"] = state
    room = {"id": "r1", "level": "L1", "name": "Kitchen", "outline": [],
            "properties": {}}
    if style is not None:
        room["properties"]["style"] = style
    return {"version": 6, "vertices": [], "walls": [], "rooms": [room],
            "levels": [{"id": "L1", "name": "First", "elevation_in": 0.0}],
            "furnishings": [fu]}


def _names(model):
    return {m.name.split(":", 1)[1] for m in model.meshes
            if m.name.startswith("furnishings:")}


def _verts(model):
    return np.vstack([m.verts for m in model.meshes
                      if m.name.startswith("furnishings:")])


def _build(fp3d, *args, **kw):
    return fp3d.build_model(_doc(*args, **kw), floors=False)


def test_the_calculator_loads_and_the_manifest_names_the_presets(fp3d, manifest):
    assert fp3d.CABGEO is not None
    named = {i["id"] for i in manifest if i.get("cabinet")}
    assert named == set(fp3d.CABGEO.PRESETS)
    assert all("cabinet" in i for i in manifest)


def test_every_cabinet_material_is_in_the_catalog(fp3d):
    materials = json.loads((FURN_DIR / "materials.json").read_text(encoding="utf-8"))
    for name, spec in fp3d.CABGEO.MATERIALS.items():
        assert materials.get(name) == spec, name


def test_a_base_cabinet_is_parts_in_the_default_style(fp3d):
    model = _build(fp3d, "base_cab_36")
    assert model.stats["cabinet_kinds"] == ["base_cab_36"]
    assert {"cab_maple", "ct_quartz", "hw_brushed_nickel", "cabinet_kick"} <= _names(model)
    assert "wood" not in _names(model) and "unknown" not in _names(model)
    assert not model.notes
    v = _verts(model)
    assert v[:, 2].min() == pytest.approx(0.0) and v[:, 2].max() == pytest.approx(36.0)
    assert v[:, 0].max() - v[:, 0].min() == pytest.approx(36.0)
    assert model.stats["triangles"] > 100, "a box was twelve"


def test_the_room_style_restyles_the_cabinet(fp3d):
    """The same cabinet, the same empty state, a different room."""
    styled = _build(fp3d, "base_cab_36",
                    style={"cabinet_finish": "cherry", "countertop": "granite",
                           "hardware": "matte_black"})
    assert {"cab_cherry", "ct_granite", "hw_matte_black"} <= _names(styled)
    assert "cab_maple" not in _names(styled)
    own = _build(fp3d, "base_cab_36", state={"finish": "navy"},
                 style={"cabinet_finish": "cherry"})
    assert "cab_navy" in _names(own) and "cab_cherry" not in _names(own)


def test_width_and_the_wall_height_follow_the_state(fp3d):
    wide = _verts(_build(fp3d, "base_cab_36", state={"width_in": 42.0}))
    assert wide[:, 0].max() - wide[:, 0].min() == pytest.approx(42.0)
    hung = _verts(_build(fp3d, "wall_cab_30"))
    assert (hung[:, 2].min(), hung[:, 2].max()) == pytest.approx((54.0, 84.0))
    higher = _verts(_build(fp3d, "wall_cab_30", state={"floor_to_bottom_in": 60.0}))
    assert higher[:, 2].min() == pytest.approx(60.0)


def test_the_doors_face_away_from_the_wall(fp3d):
    """The plan symbol is drawn back-up, so the wall is at world +y and the
    front at -y. Hardware is only ever on the front."""
    model = _build(fp3d, "base_cab_36")
    pulls = next(m for m in model.meshes if m.name.endswith("hw_brushed_nickel"))
    assert pulls.verts[:, 1].max() < -11.0
    turned = _build(fp3d, "base_cab_36", rotation=180.0)
    pulls = next(m for m in turned.meshes if m.name.endswith("hw_brushed_nickel"))
    assert pulls.verts[:, 1].min() > 11.0


def test_an_appliance_matches_the_room_or_takes_a_custom_colour(fp3d):
    std = _build(fp3d, "dishwasher", style={"cabinet_finish": "cherry"})
    assert "metal" in _names(std) and "cab_cherry" not in _names(std)
    match = _build(fp3d, "dishwasher", state={"finish_mode": "match"},
                   style={"cabinet_finish": "cherry"})
    assert "cab_cherry" in _names(match)
    custom = _build(fp3d, "range", state={"finish_mode": "custom",
                                          "sheen": "gel_coat", "colour": "red"})
    mesh = next(m for m in custom.meshes if "sheen_gel_coat#" in m.name)
    assert tuple(round(c, 3) for c in mesh.color[:3]) == (
        round(0xA3 / 255, 3), round(0x21 / 255, 3), round(0x1C / 255, 3))
    assert not custom.notes, "a custom colour is not an unknown material"


def test_every_cabinet_and_appliance_builds_wound_outward(fp3d, manifest):
    for item in manifest:
        if not item.get("cabinet"):
            continue
        model = _build(fp3d, item["id"])
        assert model.stats["cabinet_kinds"] == [item["id"]]
        for m in model.meshes:
            if not m.name.startswith("furnishings:"):
                continue
            a, b, c = (m.verts[m.faces[:, i]] for i in range(3))
            vol = float(np.einsum("ij,ij->i", a, np.cross(b, c)).sum())
            assert vol > 0.0, f"{item['id']} {m.name} is wound inward"


def test_a_hex_colour_needs_a_real_sheen(fp3d):
    mats = {"sheen_gloss": {"colour": [1, 1, 1, 1.0]}}
    assert fp3d._colour(mats, "sheen_gloss#102030") == pytest.approx(
        (0x10 / 255, 0x20 / 255, 0x30 / 255, 1.0))
    assert fp3d._colour(mats, "no_such_sheen#102030") is None
    assert fp3d._colour(mats, "sheen_gloss#zzz") is None


# -- 0333: islands, the hood, the laundry, lights --------------------------------
def test_an_island_builds_with_stools_and_one_top(fp3d):
    model = _build(fp3d, "kitchen_island", state={"slot_1": "DW24", "seats": 2})
    assert model.stats["cabinet_kinds"] == ["kitchen_island"]
    assert {"stool_seat", "ct_quartz", "cab_maple", "metal"} <= _names(model)
    v = _verts(model)
    assert v[:, 0].max() - v[:, 0].min() == pytest.approx(60.0)   # DW24 + B36
    assert v[:, 1].max() - v[:, 1].min() == pytest.approx(39.0)
    stools = next(m for m in model.meshes if m.name.endswith("stool_seat"))
    pulls = next(m for m in model.meshes if m.name.endswith("hw_brushed_nickel"))
    # the door side is the plan symbol's top (world +y); the stools the other
    assert stools.verts[:, 1].max() < 0.0
    assert pulls.verts[:, 1].max() > 15.0


def test_the_laundry_is_gloss_white_unless_told(fp3d):
    white = _build(fp3d, "washer")
    assert "sheen_gloss#f2f2ee" in _names(white) and "metal" not in _names(white)
    black = _build(fp3d, "dryer", state={"colour": "black"})
    assert "sheen_gloss#19191b" in _names(black)


def test_the_hood_and_microwave_hang_at_their_height(fp3d):
    hood = _verts(_build(fp3d, "range_hood"))
    micro = _verts(_build(fp3d, "microwave_otr"))
    assert hood[:, 2].max() == pytest.approx(84.0) and hood[:, 2].min() > 60.0
    assert (micro[:, 2].min(), micro[:, 2].max()) == pytest.approx((54.0, 71.0))


def test_a_light_hangs_from_its_rooms_ceiling_and_is_reported_as_a_source(fp3d):
    doc = _doc("light_pendant", state={"light_colour": "blue", "lumens": 1200.0})
    doc["rooms"][0]["properties"]["ceiling_height_in"] = 108.0
    doc["furnishings"][0]["pos"] = [50.0, 70.0]
    model = fp3d.build_model(doc, floors=False)
    assert model.stats["lights"] == 1 and len(model.lights) == 1
    light = model.lights[0]
    assert light["id"] == "f1" and light["lumens"] == 1200.0
    assert light["colour"] == pytest.approx((0x5a / 255, 0x8c / 255, 1.0))
    assert light["pos"][:2] == pytest.approx((50.0, -70.0)), "world y is -plan y"
    v = _verts(model)
    assert v[:, 2].max() == pytest.approx(108.0)
    assert light["pos"][2] < v[:, 2].min() + 1e-6
    assert "light_emit#5a8cff" in _names(model) and not model.notes


def test_a_plan_with_no_lights_reports_none(fp3d):
    model = _build(fp3d, "base_cab_36")
    assert model.lights == [] and model.stats["lights"] == 0
