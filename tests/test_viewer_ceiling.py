"""A room's CEILING is built in 3D (Patrick, 2026-11-06: "there are no
ceilings/floors over the 1st floor"). An enclosed interior room gets a ceiling
slab at the top of its storey -- the attic floor over a 1½-storey -- so from
inside the attic the room below is closed off, not open to the ground. A porch
(exterior) room is open above and gets none. `fp3d.py` is loaded by path.
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
    spec = importlib.util.spec_from_file_location("fp3d_ceiling_test", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _doc(category="interior", ceiling_in=None):
    V = [{"id": "a", "x": 0.0, "y": 0.0}, {"id": "b", "x": 120.0, "y": 0.0},
         {"id": "c", "x": 120.0, "y": 120.0}, {"id": "d", "x": 0.0, "y": 120.0}]
    room = {"id": "r1", "level": "L1", "category": category,
            "outline": [{"v": "a"}, {"v": "b"}, {"v": "c"}, {"v": "d"}]}
    if ceiling_in is not None:
        room["ceiling_in"] = ceiling_in
    return {"format": "floorplanner-design", "version": 6, "units": "inches",
            "settings": {}, "levels": [{"id": "L1", "name": "L1", "elevation_in": 0.0,
                                        "height_in": 96.0, "kind": "storey", "reference": False}],
            "vertices": V, "walls": [], "rooms": [room], "furnishings": [], "groups": []}


def _mesh(model, name):
    return next((m for m in model.meshes if m.name == name), None)


def test_an_interior_room_gets_a_ceiling_at_the_storey_top(fp3d):
    model = fp3d.build_model(_doc("interior"), furnishings=False)
    ceil = _mesh(model, "ceilings")
    assert ceil is not None, "no ceiling slab was built for the interior room"
    z = np.asarray(ceil.verts)[:, 2]
    # the ceiling's underside is the storey top (96); it sits just above it
    assert float(z.min()) == pytest.approx(96.0)
    assert 96.0 < float(z.max()) <= 98.0
    # and it covers the room, like the floor does
    assert _mesh(model, "floors") is not None


def test_the_ceiling_follows_a_room_ceiling_height(fp3d):
    model = fp3d.build_model(_doc("interior", ceiling_in=108.0), furnishings=False)
    z = np.asarray(_mesh(model, "ceilings").verts)[:, 2]
    assert float(z.min()) == pytest.approx(108.0)      # the room's own ceiling


def test_an_exterior_room_has_no_ceiling(fp3d):
    model = fp3d.build_model(_doc("exterior"), furnishings=False)
    assert _mesh(model, "ceilings") is None            # a porch is open above


def test_floors_off_builds_no_ceiling(fp3d):
    model = fp3d.build_model(_doc("interior"), furnishings=False, floors=False)
    assert _mesh(model, "ceilings") is None
