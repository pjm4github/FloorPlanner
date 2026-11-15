"""The 3D stair (0323): a stair that carries parameters is built from them by
the calculator the editor uses; one that does not stays the catalog box.
`fp3d.py` is loaded by path, as `test_viewer_model.py` loads it."""
import importlib.util
import math
import sys
from pathlib import Path

import numpy as np
import pytest

pytestmark = pytest.mark.viewer

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def fp3d():
    path = ROOT / "floorplanner" / "viewer" / "fp3d.py"
    spec = importlib.util.spec_from_file_location("fp3d_stair_test", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _doc(state, rotation=0.0, pos=(100.0, 200.0)):
    fu = {"id": "f1", "level": "L1", "kind": "stairs", "pos": list(pos),
          "rotation": rotation}
    if state is not None:
        fu["state"] = state
    return {"version": 6, "vertices": [], "walls": [], "rooms": [],
            "levels": [{"id": "L1", "name": "First", "elevation_in": 0.0},
                       {"id": "L2", "name": "Second", "elevation_in": 120.0}],
            "furnishings": [fu]}


def _verts(model):
    return np.vstack([m.verts for m in model.meshes
                      if m.name.startswith("furnishings")])


def _volume(model):
    vol = 0.0
    for m in model.meshes:
        if not m.name.startswith("furnishings"):
            continue
        a, b, c = (m.verts[m.faces[:, i]] for i in range(3))
        vol += float(np.einsum("ij,ij->i", a, np.cross(b, c)).sum()) / 6.0
    return vol


def test_the_calculator_loads_without_the_editor(fp3d):
    assert fp3d.STAIRGEO is not None
    assert "floorplanner" not in getattr(fp3d.STAIRGEO, "__name__", "")


@pytest.mark.parametrize("state", [None, {"flight": "full", "turn": "left",
                                          "direction": "up"}])
def test_a_stair_without_parameters_is_still_the_catalog_box(fp3d, state):
    model = fp3d.build_model(_doc(state))
    v = _verts(model)
    assert len(v) == 8
    assert v[:, 2].max() == pytest.approx(108.0)          # the catalog height
    assert not [i for i in model.info if "built from their parameters" in i]


def test_a_parametric_stair_is_treads_not_a_block(fp3d):
    sg = fp3d.STAIRGEO
    state = dict(sg.STATE_DEFAULTS)
    model = fp3d.build_model(_doc(state))
    v = _verts(model)
    box = 36.0 * 143.0 * 108.0
    assert 0.0 < _volume(model) < 0.1 * box, "outward-wound, and mostly air"
    assert v[:, 2].min() == pytest.approx(0.0)
    # 0335: the tallest thing is now the guard rail, over the top nosing
    assert v[:, 2].max() == pytest.approx(108.0 + sg.DEFAULT_RAIL_HEIGHT_IN)
    assert v[:, 0].max() - v[:, 0].min() == pytest.approx(36.0)
    assert v[:, 1].max() - v[:, 1].min() == pytest.approx(143.0)
    assert [i for i in model.info if "1 stair(s) built from their parameters" in i]


def test_a_linked_stair_rises_to_the_next_level(fp3d):
    state = dict(fp3d.STAIRGEO.STATE_DEFAULTS, rise_mode="linked")
    v = _verts(fp3d.build_model(_doc(state)))
    # L2 stands 120 in up: 16 risers, 15 treads of 11 in
    assert v[:, 2].max() == pytest.approx(
        120.0 + fp3d.STAIRGEO.DEFAULT_RAIL_HEIGHT_IN)     # 0335: the rail
    assert v[:, 1].max() - v[:, 1].min() == pytest.approx(15 * 11.0)


def test_the_solid_lands_where_the_editor_draws_the_symbol(fp3d):
    """The editor places a stair by the CENTRE of its footprint and rotates
    it clockwise on a y-down plan; the viewer's world has y up. An L stair
    is asymmetric, so a mirrored or mis-centred solid cannot pass this."""
    sg = fp3d.STAIRGEO
    state = dict(sg.STATE_DEFAULTS, type="L", turn_deg=90)
    geom, _rise, _ok = sg.geometry_from_state(state)
    cx = (geom.bbox[0] + geom.bbox[2]) / 2.0
    cy = (geom.bbox[1] + geom.bbox[3]) / 2.0
    rot, (px, py) = 30.0, (100.0, 200.0)
    r = math.radians(rot)

    def scene(nx, ny):                       # QGraphicsItem: pos + R * local
        ix, iy = nx - cx, ny - cy
        return (px + ix * math.cos(r) - iy * math.sin(r),
                py + ix * math.sin(r) + iy * math.cos(r))

    pts = []
    for solid in sg.solids(geom):
        ring = solid[1] if solid[0] == "box" else solid[1] + solid[2]
        pts += [scene(p[0], p[1]) for p in ring]
    want = np.array(pts)
    v = _verts(fp3d.build_model(_doc(state, rot, (px, py))))
    assert v[:, 0].min() == pytest.approx(want[:, 0].min())
    assert v[:, 0].max() == pytest.approx(want[:, 0].max())
    assert v[:, 1].min() == pytest.approx((-want[:, 1]).min())      # y flips
    assert v[:, 1].max() == pytest.approx((-want[:, 1]).max())


def test_parameters_that_make_no_stair_fall_back_to_the_box(fp3d):
    state = dict(fp3d.STAIRGEO.STATE_DEFAULTS, total_rise_in=-3.0)
    v = _verts(fp3d.build_model(_doc(state)))
    assert len(v) == 8
