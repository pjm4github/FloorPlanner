"""Vehicles lofted from a SIDE ELEVATION (0325).

A plan symbol is a top view, and a top view extruded is a block; the hood,
the windshield rake, the wheel arches and the daylight under the sills are in
the side view. A vehicle may carry `<id>.side.svg`, and the viewer lofts its
solid from that. These tests pin the file contract (authored in
`_gen_assets.py`) and what the loft must produce. `fp3d.py` is loaded by
path, as `test_viewer_model.py` loads it.
"""
import importlib.util
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
import pytest

pytestmark = pytest.mark.viewer

ROOT = Path(__file__).resolve().parents[1]
FURN_DIR = ROOT / "assets" / "furnishings"


@pytest.fixture(scope="module")
def fp3d():
    path = ROOT / "floorplanner" / "viewer" / "fp3d.py"
    spec = importlib.util.spec_from_file_location("fp3d_vehicle_test", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def manifest():
    return json.loads((FURN_DIR / "manifest.json").read_text(encoding="utf-8"))


def _doc(kind, rotation=0.0):
    return {"version": 6, "vertices": [], "walls": [], "rooms": [],
            "levels": [{"id": "L1", "name": "First", "elevation_in": 0.0}],
            "furnishings": [{"id": "f1", "level": "L1", "kind": kind,
                             "pos": [0.0, 0.0], "rotation": rotation}]}


def _mesh(model, material):
    hits = [m for m in model.meshes if m.name == f"furnishings:{material}"]
    assert hits, f"no {material} mesh among {[m.name for m in model.meshes]}"
    return hits[0]


def _volume(mesh):
    a, b, c = (mesh.verts[mesh.faces[:, i]] for i in range(3))
    return float(np.einsum("ij,ij->i", a, np.cross(b, c)).sum()) / 6.0


def _spec(manifest, kind):
    return next(i for i in manifest if i["id"] == kind)


# -- the file contract -------------------------------------------------------
def test_the_catalog_names_side_elevations_for_the_car_and_the_suv(manifest):
    named = {i["id"] for i in manifest if i.get("side_file")}
    assert {"car", "suv"} <= named
    assert all("side_file" in i for i in manifest), "the key is on every entry"


def test_every_side_elevation_obeys_its_contract(manifest):
    """viewBox = the catalog's LENGTH x HEIGHT; every part a filled polygon or
    circle with a material that exists; no transform anywhere."""
    materials = json.loads((FURN_DIR / "materials.json").read_text(encoding="utf-8"))
    checked = 0
    for item in manifest:
        if not item.get("side_file"):
            continue
        root = ET.parse(FURN_DIR / item["side_file"]).getroot()
        vb = [float(v) for v in root.get("viewBox").split()]
        assert vb == [0.0, 0.0, float(item["depth_in"]), float(item["height_in"])], \
            f"{item['id']}: the side view is not the catalog's length x height"
        parts = [el for el in root.iter() if el.get("data-part")]
        assert len(parts) >= 5, f"{item['id']}: a body, glass and wheels at least"
        for el in root.iter():
            assert el.get("transform") is None
        for el in parts:
            assert el.tag.rsplit("}", 1)[-1] in ("polygon", "circle")
            assert el.get("fill") not in (None, "none")
            assert el.get("data-material") in materials, \
                f"{item['id']}: {el.get('data-part')} names an unknown material"
        checked += 1
    assert checked >= 2, "PRECONDITION: there are side elevations to check"


# -- what the loft produces --------------------------------------------------
@pytest.mark.parametrize("kind,paint", [("car", "auto_paint"),
                                        ("suv", "auto_paint_light")])
def test_a_vehicle_is_lofted_in_its_own_materials(fp3d, manifest, kind, paint):
    model = fp3d.build_model(_doc(kind))
    assert model.stats["side_profile_kinds"] == [kind]
    assert kind not in model.stats["prism_kinds"]
    assert kind not in model.stats["box_fallback_kinds"]
    names = {m.name for m in model.meshes if m.name.startswith("furnishings:")}
    assert {f"furnishings:{paint}", "furnishings:auto_glass",
            "furnishings:rubber"} <= names
    assert "furnishings:unknown" not in names and not model.notes
    for m in model.meshes:
        if m.name.startswith("furnishings:"):
            assert _volume(m) > 0.0, f"{m.name} is wound inward"


@pytest.mark.parametrize("kind,paint", [("car", "auto_paint"),
                                        ("suv", "auto_paint_light")])
def test_it_stays_inside_the_catalog_box_and_is_not_one(fp3d, manifest, kind, paint):
    spec = _spec(manifest, kind)
    w, d, h = spec["width_in"], spec["depth_in"], spec["height_in"]
    model = fp3d.build_model(_doc(kind))
    v = np.vstack([m.verts for m in model.meshes
                   if m.name.startswith("furnishings:")])
    assert v[:, 0].max() - v[:, 0].min() <= w + 1e-6
    assert v[:, 1].max() - v[:, 1].min() <= d + 1e-6
    assert v[:, 2].max() == pytest.approx(h), "the roof is the catalog height"
    assert v[:, 2].min() == pytest.approx(0.0, abs=0.01), "the tyres stand on the floor"
    body = _mesh(model, paint)
    assert body.verts[:, 2].min() > 5.0, "daylight under the sills"
    solid = _volume(body) + _volume(_mesh(model, "auto_glass"))
    assert solid < 0.75 * w * d * h, "a block would fill the whole box"


def test_the_nose_is_at_the_plan_symbols_top_edge(fp3d):
    """The plan symbol is drawn nose-up, and the plan's y runs down, so the
    nose is at WORLD +y. A loft built tail-first would park every car
    backwards."""
    model = fp3d.build_model(_doc("car"))
    assert _mesh(model, "lamp").verts[:, 1].min() > 0.0
    assert _mesh(model, "tail_lamp").verts[:, 1].max() < 0.0
    turned = fp3d.build_model(_doc("car", rotation=180.0))
    assert _mesh(turned, "lamp").verts[:, 1].max() < 0.0


def test_the_body_leans_in_above_the_belt_and_draws_in_at_the_nose(fp3d, manifest):
    spec = _spec(manifest, "car")
    half = spec["width_in"] / 2.0
    glass = _mesh(fp3d.build_model(_doc("car")), "auto_glass").verts
    low = glass[glass[:, 2] < glass[:, 2].min() + 1.0]
    high = glass[glass[:, 2] > glass[:, 2].max() - 1.0]
    assert np.abs(high[:, 0]).max() < np.abs(low[:, 0]).max() - 3.0, "tumblehome"
    body = _mesh(fp3d.build_model(_doc("car")), "auto_paint").verts
    nose = body[body[:, 1] > spec["depth_in"] / 2.0 - 2.0]
    middle = body[np.abs(body[:, 1]) < 10.0]
    assert np.abs(middle[:, 0]).max() == pytest.approx(half)
    assert np.abs(nose[:, 0]).max() < half - 3.0, "the plan corners are rounded"


def test_an_unreadable_side_elevation_falls_back_and_is_named(fp3d):
    specs, materials, problems = fp3d.load_catalog()
    specs = dict(specs)
    specs["car"] = dict(specs["car"], side_file="no_such_file.side.svg")
    model = fp3d.build_model(_doc("car"), catalog=(specs, materials, problems))
    assert model.stats["side_profile_kinds"] == []
    assert "car" in model.stats["prism_kinds"], "back to the plan symbol"
    assert any("side elevation" in n and "car" in n for n in model.notes)


# -- the slicing itself ------------------------------------------------------
def test_a_span_is_the_lowest_to_the_highest_point_on_the_line(fp3d):
    ring = [(0.0, 0.0), (10.0, 0.0), (10.0, 4.0), (5.0, 8.0), (0.0, 4.0)]
    assert fp3d._span_at(ring, 5.0) == pytest.approx((0.0, 8.0))
    assert fp3d._span_at(ring, 2.5) == pytest.approx((0.0, 6.0))
    assert fp3d._span_at(ring, 11.0) is None


def test_a_step_in_the_outline_stays_a_step(fp3d):
    """Stations fall just either side of every corner, so a vertical step is
    not smeared across a whole slice."""
    ring = [(0.0, 0.0), (20.0, 0.0), (20.0, 10.0), (10.0, 10.0), (10.0, 4.0),
            (0.0, 4.0)]
    cuts = fp3d._vehicle_stations(ring, 3.0)
    before = max(c for c in cuts if c < 10.0)
    after = min(c for c in cuts if c > 10.0)
    assert after - before < 0.01
    assert fp3d._span_at(ring, before)[1] == pytest.approx(4.0)
    assert fp3d._span_at(ring, after)[1] == pytest.approx(10.0)
    assert max(b - a for a, b in zip(cuts[:-1], cuts[1:], strict=True)) <= 3.0 + 1e-9


def test_a_side_file_with_a_transform_is_refused(fp3d, tmp_path):
    p = tmp_path / "t.side.svg"
    p.write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 5">'
                 '<polygon points="0,0 10,0 10,5 0,5" fill="#000" '
                 'transform="scale(2)" data-part="body" data-material="metal"/>'
                 '</svg>', encoding="utf-8")
    assert fp3d.load_side_profile(str(p)) is None
    p.write_text(p.read_text(encoding="utf-8").replace(' transform="scale(2)"', ""),
                 encoding="utf-8")
    prof = fp3d.load_side_profile(str(p))
    assert prof is not None and (prof["length"], prof["height"]) == (10.0, 5.0)
    assert prof["parts"][0]["ring"][0] == (0.0, 5.0), "y is flipped to height"
