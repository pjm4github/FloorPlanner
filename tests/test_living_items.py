"""Pedal bin, dog crate, sofa table and table lamp (0341) --
`cabinet_geometry.py`, its kinds, and the 3D model."""
import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest

from floorplanner.parametric import cabinet_geometry as cg
from floorplanner.parametric import findings as F
from floorplanner.parametric import registry

pytestmark = pytest.mark.furnishings

ROOT = Path(__file__).resolve().parents[1]
SOLID = ("pedal_bin", "dog_crate", "sofa_table")
ALL = SOLID + ("table_lamp",)


@pytest.fixture(scope="module")
def fp3d():
    path = ROOT / "floorplanner" / "viewer" / "fp3d.py"
    spec = importlib.util.spec_from_file_location("fp3d_living_test", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _st(kind, **over):
    return cg.normalize_state(over, cg.PRESETS[kind])


def _by_name(kind, **over):
    return {p.name: p for p in cg.cabinet_parts(_st(kind, **over))}


def _box(p):
    xs = [x for x, _f in p.quad]
    fs = [f for _x, f in p.quad]
    return min(xs), max(xs), min(fs), max(fs)


@pytest.mark.parametrize("kind", SOLID)
def test_it_fills_its_footprint_and_stands_at_its_catalog_height(kind):
    st = _st(kind)
    parts = cg.cabinet_parts(st)
    w, d = cg.footprint(st)
    xs = [x for p in parts for x, _f in p.quad]
    fs = [f for p in parts for _x, f in p.quad]
    assert (min(xs), max(xs)) == pytest.approx((-w / 2, w / 2))
    assert min(fs) == pytest.approx(0.0, abs=1e-9) and max(fs) <= d + 1e-9
    assert min(p.z0 for p in parts) == 0.0
    assert max(p.z1 for p in parts) == pytest.approx(cg.overall_height(st))
    assert len({p.name for p in parts}) == len(parts)
    mats = cg.resolve_materials(st)
    assert all(p.role in mats for p in parts)


def test_a_pedal_bin_is_round_with_its_pedal_out_front():
    parts = _by_name("pedal_bin")
    assert len(parts["body"].quad) > 4 and len(parts["lid"].quad) > 4
    assert parts["lid"].z0 >= parts["body"].z1
    assert _box(parts["pedal"])[3] == 16.0, "the pedal reaches the front edge"
    assert _box(parts["pedal"])[2] > _box(parts["body"])[3] - 1.0
    assert parts["pedal"].z1 < 2.0, "down at the floor"
    assert cg.resolve_materials(_st("pedal_bin"))["appliance"] == "metal"
    red = _st("pedal_bin", finish_mode="custom", colour="red", sheen="matte")
    assert cg.resolve_materials(red)["appliance"].startswith("sheen_matte#")


def test_a_dog_crate_is_wire_not_a_box():
    st = _st("dog_crate")
    parts = cg.cabinet_parts(st)
    wires = [p for p in parts if p.name.startswith(("wire-", "hoop-"))]
    assert len(wires) > 40
    volume = sum((_box(p)[1] - _box(p)[0]) * (_box(p)[3] - _box(p)[2])
                 * (p.z1 - p.z0) for p in parts if p.name != "bed"
                 and p.name != "bolster" and p.name != "pan")
    assert volume < 0.03 * 36.0 * 24.0 * 26.0, "mostly air"
    names = {p.name for p in parts}
    assert {"door-sill", "door-head", "latch", "pan", "bed"} <= names
    gaps = sorted(_box(p)[0] for p in parts if p.name.startswith("wire-back-"))
    assert max(b - a for a, b in zip(gaps[:-1], gaps[1:], strict=False)) < 3.0
    assert "bed" not in {p.name for p in cg.cabinet_parts(_st("dog_crate",
                                                              bed=False))}
    big = cg.cabinet_parts(_st("dog_crate", width_in=48.0, depth_in=30.0))
    assert len([p for p in big if p.name.startswith("wire-back-")]) > len(
        [p for p in parts if p.name.startswith("wire-back-")])


@pytest.mark.parametrize("shelves", [0, 1, 2])
def test_a_sofa_table_has_four_legs_a_top_and_the_shelves_asked_for(shelves):
    parts = _by_name("sofa_table", shelves=shelves)
    assert sum(1 for n in parts if n.startswith("leg-")) == 4
    assert parts["top"].z1 == 30.0
    assert _box(parts["top"]) == (-24.0, 24.0, 0.0, 14.0)
    assert sum(1 for n in parts if n.startswith("shelf-")) == shelves
    assert all(p.z1 <= parts["top"].z0 for n, p in parts.items() if n != "top")


def test_a_table_lamp_stands_on_its_table_and_is_a_light():
    st = _st("table_lamp")
    parts = {p.name: p for p in cg.cabinet_parts(st, None, 96.0)}
    assert min(p.z0 for p in parts.values()) == 30.0, "on a 30 in table top"
    assert max(p.z1 for p in parts.values()) == pytest.approx(30.0 + 22.0)
    assert parts["lens"].z0 > parts["body"].z0
    src = cg.light_source(st, 96.0)
    assert src["kind"] == "point" and src["lumens"] == 800.0
    assert 30.0 < src["pos"][2] < 52.0, "the source is in the shade"
    assert cg.light_source(_st("table_lamp", lumens=0.0), 96.0) is None
    on_floor = cg.cabinet_parts(_st("table_lamp", floor_to_bottom_in=0.0,
                                    drop_in=40.0), None, 96.0)
    assert (min(p.z0 for p in on_floor), max(p.z1 for p in on_floor)) == (
        0.0, pytest.approx(40.0))
    same = cg.cabinet_parts(st, None, 120.0)
    assert max(p.z1 for p in same) == pytest.approx(52.0), "the ceiling is not its business"


@pytest.mark.parametrize("kind", ALL)
def test_each_has_a_dialog_definition_that_stores_only_changes(kind):
    definition = registry.get(kind)
    assert definition is not None and definition.specs()
    assert definition.to_state({}) == {}
    derived, findings = definition.evaluate({}, {})
    assert derived is not None and not F.blocks(findings)
    assert definition.summary({}, derived, {})


def test_the_lamp_dialog_enables_height_and_lamp_height_for_a_table_lamp():
    specs = {s.key: s for s in registry.get("table_lamp").specs()}
    v = {"fixture": "table"}
    assert specs["floor_to_bottom_in"].enabled(v) and specs["drop_in"].enabled(v)
    assert not specs["beam"].enabled(v)
    assert ("table", "Table lamp") in cg.FIXTURES


# -- in the 3D model -----------------------------------------------------------
def _doc(kind, state=None):
    fu = {"id": "f1", "level": "L1", "kind": kind, "room": "r1",
          "pos": [0.0, 0.0], "rotation": 0.0}
    if state is not None:
        fu["state"] = state
    return {"version": 6, "vertices": [], "walls": [],
            "rooms": [{"id": "r1", "level": "L1", "name": "Living",
                       "outline": [], "properties": {}}],
            "levels": [{"id": "L1", "name": "First", "elevation_in": 0.0}],
            "furnishings": [fu]}


@pytest.mark.parametrize("kind", ALL)
def test_it_builds_from_parts_in_known_materials_wound_outward(fp3d, kind):
    model = fp3d.build_model(_doc(kind), floors=False)
    meshes = [m for m in model.meshes if m.name.startswith("furnishings:")]
    assert kind in model.stats["cabinet_kinds"]
    assert "furnishings:unknown" not in {m.name for m in meshes}
    for m in meshes:
        a, b, c = (m.verts[m.faces[:, i]] for i in range(3))
        assert float(np.einsum("ij,ij->i", a, np.cross(b, c)).sum()) > 0.0, m.name
    v = np.vstack([m.verts for m in meshes])
    spec = fp3d.load_catalog()[0][kind]
    assert v[:, 0].max() - v[:, 0].min() == pytest.approx(spec["width_in"])
    base = float(spec.get("elevation_in", 0.0) or 0.0)
    assert v[:, 2].min() == pytest.approx(base)
    assert v[:, 2].max() == pytest.approx(base + spec["height_in"])


def test_a_table_lamp_reports_a_light_and_glows(fp3d):
    model = fp3d.build_model(_doc("table_lamp", {"light_colour": "amber"}),
                             floors=False)
    assert len(model.lights) == 1 and model.lights[0]["kind"] == "point"
    assert 30.0 < model.lights[0]["pos"][2] < 52.0
    assert any("light_emit#" in m.name for m in model.meshes)
