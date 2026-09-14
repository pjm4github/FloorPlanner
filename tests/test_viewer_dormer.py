"""R5b in 3D (0191-ruling.md sec1, sec3 (c)): a dormer's cheeks and face are
walls that stand ON the host's plane under the dormer's own eaves --
prisms whose bottom ring lies on the host surface (sunk a half inch into
its slab) and whose top is the dormer's eaves height (a half inch under
its slab). Qt-free, fp3d loaded by path.
"""
import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest

pytestmark = pytest.mark.viewer

ROOT = Path(__file__).resolve().parents[1]
MEET_Y = 100.0 + (150.0 - 136.0) / 0.54


def _load_fp3d():
    path = ROOT / "floorplanner" / "viewer" / "fp3d.py"
    spec = importlib.util.spec_from_file_location("fp3d_dormer_under_test", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def fp3d():
    return _load_fp3d()


def _doc(with_host=True):
    dormer = {"id": "rf2", "level": "L1", "ridge": [[200, 190], [200, MEET_Y]],
              "eaves_h_in": 116.0, "ridge_h_in": 136.0, "overhang_in": [0, 0],
              "span_in": [30, 30], "gable": [True, True], "marker_end": 0}
    if with_host:
        dormer["host"] = "rf1"
    return {"levels": [{"id": "L1", "elevation_in": 0.0, "height_in": 96.0}],
            "vertices": [], "walls": [], "rooms": [], "furnishings": [],
            "roofs": [{"id": "rf1", "level": "L1", "ridge": [[0, 100], [400, 100]],
                       "eaves_h_in": 96.0, "ridge_h_in": 150.0, "overhang_in": [12, 12],
                       "span_in": [100, 100], "gable": [True, True]}, dormer]}


def _wall_verts(model):
    parts = [m.verts for m in model.meshes if m.name.startswith("walls:")]
    return np.vstack(parts) if parts else np.zeros((0, 3))


def test_a_dormer_builds_three_standing_walls_on_the_host_plane(fp3d):
    model = fp3d.build_model(_doc(), furnishings=False, floors=False)
    assert not model.notes, model.notes
    v = _wall_verts(model)
    assert len(v) == 3 * 8, "face + two cheeks, each a closed prism"
    c = fp3d.DORMER_WALL_CLEAR_IN
    assert v[:, 2].max() == pytest.approx(116.0 - c)
    # every bottom vertex sits on the host's surface less the sink:
    # host at world (x, y_w): 150 - 0.54 * |(-y_w) - 100|
    bottoms = v[~np.isclose(v[:, 2], 116.0 - c)]
    assert len(bottoms) >= 8
    for x, y, z in bottoms:
        assert z == pytest.approx(150.0 - 0.54 * abs(-y - 100.0) - c, abs=1e-6), (x, y, z)
    # the cheeks reach back to where the eaves meet the host: y = 162.96
    assert (-v[:, 1]).min() == pytest.approx(100.0 + (150.0 - 116.0) / 0.54, abs=1e-6)
    # the walls sit inside the dormer's own footprint, inset from its lines
    assert v[:, 0].min() >= 170.0 + c - 1e-9 and v[:, 0].max() <= 230.0 - c + 1e-9


def test_the_roof_meshes_are_unchanged_by_the_host_field(fp3d):
    with_host = fp3d.build_model(_doc(True), furnishings=False, floors=False)
    without = fp3d.build_model(_doc(False), furnishings=False, floors=False)
    a = next(m for m in with_host.meshes if m.name == "roofs")
    b = next(m for m in without.meshes if m.name == "roofs")
    assert np.array_equal(a.verts, b.verts) and np.array_equal(a.faces, b.faces)
    assert len(_wall_verts(without)) == 0, "no host, no dormer walls"


def test_a_dormer_whose_host_is_missing_is_noted_not_built(fp3d):
    doc = _doc()
    doc["roofs"][1]["host"] = "rf9"
    model = fp3d.build_model(doc, furnishings=False, floors=False)
    assert any("rf9" in n for n in model.notes)
    assert len(_wall_verts(model)) == 0
