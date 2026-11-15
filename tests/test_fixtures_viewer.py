"""Fixtures in the 3D model (0338): each is built from its parts, in known
materials, as closed outward-wound solids. `fp3d.py` is loaded by path."""
import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest

pytestmark = pytest.mark.viewer

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ("toilet", "bathtub", "bookshelf", "gas_fireplace", "grab_bar")


@pytest.fixture(scope="module")
def fp3d():
    path = ROOT / "floorplanner" / "viewer" / "fp3d.py"
    spec = importlib.util.spec_from_file_location("fp3d_fixture_test", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _doc(kind, state=None, rotation=0.0):
    fu = {"id": "f1", "level": "L1", "kind": kind, "room": "r1",
          "pos": [0.0, 0.0], "rotation": rotation}
    if state is not None:
        fu["state"] = state
    return {"version": 6, "vertices": [], "walls": [],
            "rooms": [{"id": "r1", "level": "L1", "name": "Bath", "outline": [],
                       "properties": {}}],
            "levels": [{"id": "L1", "name": "First", "elevation_in": 0.0}],
            "furnishings": [fu]}


def _furn(model):
    return [m for m in model.meshes if m.name.startswith("furnishings:")]


def _volume(mesh):
    a, b, c = (mesh.verts[mesh.faces[:, i]] for i in range(3))
    return float(np.einsum("ij,ij->i", a, np.cross(b, c)).sum()) / 6.0


@pytest.mark.parametrize("kind", FIXTURES)
def test_a_fixture_is_built_from_parts_in_known_materials(fp3d, kind):
    model = fp3d.build_model(_doc(kind), floors=False)
    meshes = _furn(model)
    assert kind in model.stats["cabinet_kinds"]
    assert len(meshes) >= 1
    assert "furnishings:unknown" not in {m.name for m in meshes}
    assert not [n for n in model.notes if "unknown material" in n]
    for m in meshes:
        assert _volume(m) > 0.0, f"{m.name} is wound inward"


@pytest.mark.parametrize("kind", FIXTURES)
def test_a_fixture_stands_in_its_catalog_box(fp3d, kind):
    specs, _materials, _problems = fp3d.load_catalog()
    spec = specs[kind]
    v = np.vstack([m.verts for m in _furn(
        fp3d.build_model(_doc(kind), floors=False))])
    assert v[:, 0].max() - v[:, 0].min() == pytest.approx(spec["width_in"])
    assert v[:, 1].max() - v[:, 1].min() <= spec["depth_in"] + 1e-6
    base = float(spec.get("elevation_in", 0.0) or 0.0)
    assert v[:, 2].min() == pytest.approx(base)
    if kind != "bathtub":                      # its filler stands above the rim
        assert v[:, 2].max() == pytest.approx(base + spec["height_in"])


def test_round_parts_are_prisms_with_more_than_four_sides(fp3d):
    ring = [(np.cos(a), np.sin(a)) for a in np.linspace(0, 2 * np.pi, 12,
                                                         endpoint=False)]
    for r in (ring, ring[::-1]):
        v, f = fp3d._ngon_prism(r, 0.0, 2.0)
        assert len(v) == 24 and len(f) == 2 * 10 + 2 * 12
        a, b, c = (v[f[:, i]] for i in range(3))
        vol = float(np.einsum("ij,ij->i", a, np.cross(b, c)).sum()) / 6.0
        assert vol == pytest.approx(12 * 0.5 * np.sin(np.pi / 6) * 2.0)


def test_a_lit_fireplace_glows_and_an_unlit_one_does_not(fp3d):
    lit = {m.name for m in _furn(fp3d.build_model(_doc("gas_fireplace"),
                                                 floors=False))}
    out = {m.name for m in _furn(fp3d.build_model(
        _doc("gas_fireplace", {"lit": False}), floors=False))}
    assert any("light_emit#" in n for n in lit)
    assert not any("light_emit#" in n for n in out)


def test_the_toilet_colour_reaches_the_mesh(fp3d):
    white = _furn(fp3d.build_model(_doc("toilet"), floors=False))
    black = _furn(fp3d.build_model(_doc("toilet", {"colour": "black"}),
                                   floors=False))
    body = max(white, key=lambda m: len(m.faces))
    dark = max(black, key=lambda m: len(m.faces))
    assert sum(body.color[:3]) > 2.4 and sum(dark.color[:3]) < 0.6


def test_island_slots_added_in_0338_build(fp3d):
    state = {"slot_1": "BS18", "slot_2": "CT36", "slot_3": "RG30",
             "slot_4": "WC24", "slot_5": "MW24", "seats": 4}
    model = fp3d.build_model(_doc("kitchen_island", state), floors=False)
    v = np.vstack([m.verts for m in _furn(model)])
    assert v[:, 0].max() - v[:, 0].min() == pytest.approx(18 + 36 + 30 + 24 + 24)
    assert "furnishings:unknown" not in {m.name for m in _furn(model)}
    for m in _furn(model):
        assert _volume(m) > 0.0
