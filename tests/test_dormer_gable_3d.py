"""A dormer's GABLE END must close in 3D even when its face sits on a house
wall (Patrick, 2026-11: the gable ends of his front dormers were open).

The wall there used to cap at the LOWEST roof -- the host it stands on -- so the
dormer gable above was left open, and `_dormer_face` yielded the gable to
`_on_a_wall` expecting a climb that never came. `_wall_under_roofs` now climbs a
wall piece inside a same-level dormer's territory to THAT dormer's surface,
closing the gable; a window in the wall stays a void (no dormer face is
generated, so the 0248 invariant holds). `fp3d.py` is loaded by path, like the
other viewer tests.
"""
import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest

pytestmark = pytest.mark.viewer

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def fp3d():
    path = ROOT / "floorplanner" / "viewer" / "fp3d.py"
    spec = importlib.util.spec_from_file_location("fp3d_gable_under_test", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _doc(window):
    V = [{"id": "wa", "x": 160.0, "y": 240.0}, {"id": "wb", "x": 240.0, "y": 240.0}]
    ops = []
    if window:
        ops = [{"id": "o1", "kind": "window", "code": "2030",
                "anchor": {"from": "v1", "offset_in": 30.0}, "sill_in": 150.0}]
    wall = {"id": "w1", "level": "L1", "v1": "wa", "v2": "wb",
            "type": "exterior", "openings": ops}
    host = {"id": "h", "level": "L1", "ridge": [[-40.0, 100.0], [440.0, 100.0]],
            "eaves_h_in": 96.0, "ridge_h_in": 300.0, "overhang_in": [0.0, 0.0],
            "span_in": [170.0, 170.0], "gable": [True, True], "marker_end": 1}
    dormer = {"id": "d", "level": "L1", "ridge": [[200.0, 240.0], [200.0, 160.0]],
              "eaves_h_in": 180.0, "ridge_h_in": 240.0, "overhang_in": [0.0, 0.0],
              "span_in": [40.0, 40.0], "wall_span_in": [40.0, 40.0],
              "gable": [True, True], "marker_end": 0, "host": "h"}
    return {"format": "floorplanner-design", "version": 6, "units": "inches",
            "settings": {}, "levels": [{"id": "L1", "name": "default", "elevation_in": 0.0,
                                        "height_in": 96.0, "kind": "storey", "reference": False}],
            "vertices": V, "walls": [wall], "rooms": [], "furnishings": [],
            "groups": [], "roofs": [host, dormer]}


def _ext(model):
    return next(m for m in model.meshes if m.name == "walls:exterior")


def test_the_wall_climbs_to_close_the_dormer_gable(fp3d):
    ext = _ext(fp3d.build_model(_doc(window=False), furnishings=False, floors=False))
    # the wall at the dormer face (x=200, world y=-240) rises to the dormer
    # ridge (~240), far above where it would cap at the host roof there (~132)
    v = ext.verts
    near = v[(abs(v[:, 0] - 200.0) < 14.0) & (abs(v[:, 1] + 240.0) < 14.0)]
    assert len(near) and float(near[:, 2].max()) > 220.0, (
        f"the wall did not climb to close the gable: {float(near[:, 2].max()) if len(near) else None}")


def test_a_window_in_the_climbing_wall_stays_a_void(fp3d):
    model = fp3d.build_model(_doc(window=True), furnishings=False, floors=False)
    mesh = _ext(model)
    verts, faces = mesh.verts, mesh.faces
    # a ray across the wall thickness, through the window (x=200, z=165 in the
    # 150..180 opening), must meet no triangle -- the opening is a void
    a = np.array([200.0, -235.0, 165.0])
    b = np.array([200.0, -245.0, 165.0])
    d = b - a
    v0, v1, v2 = verts[faces[:, 0]], verts[faces[:, 1]], verts[faces[:, 2]]
    e1, e2 = v1 - v0, v2 - v0
    pv = np.cross(d, e2)
    det = np.einsum("ij,ij->i", e1, pv)
    ok = np.abs(det) > 1e-12
    inv = np.where(ok, 1.0 / np.where(ok, det, 1.0), 0.0)
    tv = a - v0
    u = np.einsum("ij,ij->i", tv, pv) * inv
    q = np.cross(tv, e1)
    w = np.einsum("j,ij->i", d, q) * inv
    tt = np.einsum("ij,ij->i", e2, q) * inv
    hit = ok & (u >= -1e-9) & (w >= -1e-9) & (u + w <= 1 + 1e-9) & (tt >= 0) & (tt <= 1)
    assert int(hit.sum()) == 0, "the window in the climbing wall is covered"
    # and the gable still closed above the window
    v = verts
    near = v[(abs(v[:, 0] - 200.0) < 14.0) & (abs(v[:, 1] + 240.0) < 14.0)]
    assert float(near[:, 2].max()) > 220.0
