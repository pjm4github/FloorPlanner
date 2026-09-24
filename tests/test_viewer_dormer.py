"""R5b in 3D, as corrected by Patrick's look at the first dormer
(2026-09-24): *"the walls of the dormer are being drawn down from the
dormer. It should show only the roof line and intersect with the walls
under it."* So a dormer builds no walls of its own; the house walls under
its territory CLIMB into its roof -- `fp3d._wall_under_roofs` caps a
pier or header under a dormer at the dormer's plane whether that is
below or above the wall's own top -- and the roof meshes are unchanged
by the `host` field. Qt-free, fp3d loaded by path.
"""
import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest

pytestmark = pytest.mark.viewer

ROOT = Path(__file__).resolve().parents[1]
MEET_Y = 100.0 + (150.0 - 136.0) / 0.54
DORMER_SLOPE = (136.0 - 116.0) / 30.0


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


def _doc(with_host=True, walls=()):
    dormer = {"id": "rf2", "level": "L1", "ridge": [[200, 190], [200, MEET_Y]],
              "eaves_h_in": 116.0, "ridge_h_in": 136.0, "overhang_in": [0, 0],
              "span_in": [30, 30], "gable": [True, True], "marker_end": 0}
    if with_host:
        dormer["host"] = "rf1"
    return {"levels": [{"id": "L1", "elevation_in": 0.0, "height_in": 96.0}],
            "vertices": [{"id": "a", "x": 100, "y": 170}, {"id": "b", "x": 300, "y": 170}],
            "walls": list(walls), "rooms": [], "furnishings": [],
            "roofs": [{"id": "rf1", "level": "L1", "ridge": [[0, 100], [400, 100]],
                       "eaves_h_in": 96.0, "ridge_h_in": 150.0, "overhang_in": [12, 12],
                       "span_in": [100, 100], "gable": [True, True]}, dormer]}


WALL = {"id": "w1", "level": "L1", "v1": "a", "v2": "b", "type": "interior"}


def _wall_verts(model):
    parts = [m.verts for m in model.meshes if m.name.startswith("walls:")]
    return np.vstack(parts) if parts else np.zeros((0, 3))


def test_a_dormer_builds_no_walls_of_its_own(fp3d):
    model = fp3d.build_model(_doc(), furnishings=False, floors=False)
    assert not model.notes, model.notes
    assert len(_wall_verts(model)) == 0


def test_a_wall_under_a_dormer_climbs_into_its_roof(fp3d):
    """An interior wall at plan y=170 crossing the dormer (x 170..230):
    under the dormer its top is the dormer plane less the cap drop --
    131.5in at the ridge line, above the level's 96in walls; outside the
    dormer, where the host plane clears 96in, the wall keeps its top."""
    model = fp3d.build_model(_doc(walls=[WALL]), furnishings=False, floors=False)
    assert not model.notes, model.notes
    v = _wall_verts(model)
    assert len(v) > 8, "the wall was split under the dormer"
    c = fp3d.WALL_CAP_BELOW_ROOF_IN
    under = v[(v[:, 0] > 170.0 + 1e-6) & (v[:, 0] < 230.0 - 1e-6) & (v[:, 2] > 1.0)]
    assert len(under) >= 2
    for x, y, z in under:
        assert z == pytest.approx(136.0 - DORMER_SLOPE * abs(x - 200.0) - c, abs=1e-6), (x, y, z)
    assert v[:, 2].max() == pytest.approx(136.0 - c)
    outside = v[v[:, 0] < 170.0 - 1e-6]
    assert outside[:, 2].max() == pytest.approx(96.0)
    # the control: the same wall with no dormer never rises above its top
    plain = fp3d.build_model(_doc(with_host=False, walls=[WALL]), furnishings=False,
                             floors=False)
    assert _wall_verts(plain)[:, 2].max() <= 96.0 + 1e-6


def test_the_wall_under_a_sill_does_not_climb(fp3d):
    wall = dict(WALL, openings=[{"id": "o1", "kind": "window", "code": "3050",
                                 "anchor": {"from": "start", "offset_in": 100},
                                 "sill_in": 30.0, "head_in": 80.0}])
    model = fp3d.build_model(_doc(walls=[wall]), furnishings=False, floors=False)
    v = _wall_verts(model)
    sill = v[np.isclose(v[:, 2], 30.0)]
    assert len(sill) >= 4, "the under-sill piece keeps its own flat top"
    assert v[:, 2].max() == pytest.approx(136.0 - fp3d.WALL_CAP_BELOW_ROOF_IN)


def test_the_roof_meshes_are_unchanged_by_the_host_field(fp3d):
    with_host = fp3d.build_model(_doc(True), furnishings=False, floors=False)
    without = fp3d.build_model(_doc(False), furnishings=False, floors=False)
    a = next(m for m in with_host.meshes if m.name == "roofs")
    b = next(m for m in without.meshes if m.name == "roofs")
    assert np.array_equal(a.verts, b.verts) and np.array_equal(a.faces, b.faces)
