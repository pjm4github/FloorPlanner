"""Iteration 10 of his house model (0254-report.md): THE GABLE CLIMB STAYS
ON THE WALL'S OWN LEVEL.

The gable wall climbs into its roof (0223-report.md sec3): an exterior
wall perpendicular to a roof's ridge rises to the roof's underside. The
rule had no level: a FIRST-floor gable wall under a SECOND-floor gable
roof climbed through the storey above -- on the house, the bay front
wall's header rose from its window head at 90in to the rake at 266in,
through the second-floor wall and its window, which the shot showed
solid. A wall climbs into a roof of its own level only; a roof of
another level caps it like any other roof, where it is lower than the
wall's top. The dormer climb already said so (R6.b); this is the same
sentence for the gable.
"""
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pytest

pytestmark = pytest.mark.viewer

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def fp3d():
    path = ROOT / "floorplanner" / "viewer" / "fp3d.py"
    spec = importlib.util.spec_from_file_location("fp3d_climb_under_test", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _two_storey_gable():
    """A 200 x 200 body on two storeys (120 + 108) with a gable roof on the
    SECOND floor, ridge along y at x=100 (eaves 48 over L2, ridge 148 at
    12:12): the front walls at y=200 on both levels are its gable walls.
    The first-floor front wall has a 72 x 60 window at sill 30 (head 90);
    the second-floor front wall a 48 x 48 window at sill 52."""
    def level_walls(level, z, openings):
        vs = [{"id": f"{level}a", "level": level, "x": 0.0, "y": 0.0},
              {"id": f"{level}b", "level": level, "x": 200.0, "y": 0.0},
              {"id": f"{level}c", "level": level, "x": 200.0, "y": 200.0},
              {"id": f"{level}d", "level": level, "x": 0.0, "y": 200.0}]
        ws = [{"id": f"{level}w1", "level": level, "v1": f"{level}a", "v2": f"{level}b", "type": "exterior", "openings": []},
              {"id": f"{level}w2", "level": level, "v1": f"{level}b", "v2": f"{level}c", "type": "exterior", "openings": []},
              {"id": f"{level}w3", "level": level, "v1": f"{level}d", "v2": f"{level}c", "type": "exterior",
               "openings": list(openings)},
              {"id": f"{level}w4", "level": level, "v1": f"{level}a", "v2": f"{level}d", "type": "exterior", "openings": []}]
        return vs, ws
    v1, w1 = level_walls("L1", 0.0, [{"id": "o1", "kind": "window", "code": "7260",
                                       "anchor": {"from": "center", "offset_in": 0.0}, "sill_in": 30.0}])
    v2, w2 = level_walls("L2", 120.0, [{"id": "o2", "kind": "window", "code": "4848",
                                         "anchor": {"from": "center", "offset_in": 0.0}, "sill_in": 52.0}])
    return {"format": "floorplanner-design", "version": 6, "units": "inches", "settings": {},
            "levels": [{"id": "L1", "name": "default", "elevation_in": 0.0, "height_in": 120.0,
                        "kind": "storey", "reference": False},
                       {"id": "L2", "name": "second", "elevation_in": 120.0, "height_in": 108.0,
                        "kind": "storey", "reference": False}],
            "vertices": v1 + v2, "walls": w1 + w2, "rooms": [], "furnishings": [], "groups": [],
            "roofs": [{"id": "rf", "level": "L2", "ridge": [[100.0, 0.0], [100.0, 200.0]], "eaves_h_in": 48.0,
                       "ridge_h_in": 148.0, "overhang_in": [0.0, 0.0], "span_in": [100.0, 100.0],
                       "eaves_bind": "manual", "gable": [True, True], "marker_end": 1}]}


def _hits(mesh, a, b):
    verts, faces = mesh.verts, mesh.faces
    a = np.array(a, float)
    b = np.array(b, float)
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
    t = np.einsum("ij,ij->i", e2, q) * inv
    hit = ok & (u >= -1e-9) & (w >= -1e-9) & (u + w <= 1 + 1e-9) & (t >= 0) & (t <= 1)
    return int(hit.sum())


def test_a_first_floor_gable_wall_stops_at_its_own_top_under_a_second_floor_roof(fp3d):
    model = fp3d.build_model(_two_storey_gable(), furnishings=False, floors=False)
    assert not model.notes, model.notes
    ext = next(m for m in model.meshes if m.name == "walls:exterior")
    v = ext.verts
    front = v[abs(-v[:, 1] - 200.0) < 4.0]
    # the first-floor front wall's pieces: nothing above its own top, 120
    first = front[front[:, 2] < 120.0 + 1e-6]
    assert first.size and first[:, 2].max() == pytest.approx(120.0)
    # the second-floor gable wall climbs to the rake: 120 + 148 less the cap at the ridge
    assert front[:, 2].max() == pytest.approx(120.0 + 148.0 - fp3d.WALL_CAP_BELOW_ROOF_IN)
    # and its window is OPEN: a ray through the wall plane inside it meets nothing;
    # under the sill, over the head and beside it, wall
    def ray(x, z):
        return (x, -207.0, z), (x, -193.0, z)
    for x, z in ((100.0, 180.0), (85.0, 190.0), (115.0, 210.0)):
        assert _hits(ext, *ray(x, z)) == 0, (x, z)
    for x, z in ((100.0, 160.0), (100.0, 230.0), (60.0, 180.0), (140.0, 180.0)):
        assert _hits(ext, *ray(x, z)) > 0, (x, z)
    # the first floor's own window is open too; its header (90..120) stands,
    # and above 120 what stands is the second-floor wall under its sill
    assert _hits(ext, *ray(100.0, 60.0)) == 0
    assert _hits(ext, *ray(100.0, 105.0)) > 0 and _hits(ext, *ray(100.0, 125.0)) > 0


def test_a_single_storey_gable_wall_still_climbs_into_its_own_roof(fp3d):
    """The gable-end check plan (0223): one level, the wall climbs to the
    rake as before -- byte-identical walls with the level check in place."""
    doc = json.loads((ROOT / "fixtures" / "single-floor-90-roof-gable-end-check.json").read_text(encoding="utf-8"))
    model = fp3d.build_model(doc, furnishings=False, floors=False)
    ext = next(m for m in model.meshes if m.name == "walls:exterior")
    v = ext.verts
    # rf1's ridge is 165.75 at y=216; its west gable walls at x=180 climb to it
    assert v[abs(v[:, 0] - 180.0) < 4.0][:, 2].max() == pytest.approx(165.75 - fp3d.WALL_CAP_BELOW_ROOF_IN)
