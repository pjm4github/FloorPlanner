"""0372 item B: the sec 8.4 cantilever floor closes OPEN AIR only.

A cantilevered dormer's flat attic floor (DORMER_CONTROL_SPEC.md sec 8.4) was
laid across the WHOLE overhang, even where a lower roof is drawn beneath it, so
it stood proud of that roof (0372 §3 measured a hipped skirt 12 in below the
floor, the slab proud at its corners and hanging in air past the hips). The
rule (0372 §4 B): where a roof is drawn under the dormer's overhang the floor is
not laid; only the genuinely open-air part is floored.

Fail-first fixture: a gable dormer on L2 hosted on an L1 roof, cantilevered past
its eave, with a LOW shed on L1 under the WEST half of that overhang. The floor
must cover only the open-air (east) half; the west half, over the shed, is left
to the shed. The control (shed removed) floors the whole overhang, before and
after. `fp3d.py` is loaded by path, like the other viewer tests.
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
    spec = importlib.util.spec_from_file_location("fp3d_floor_open_air", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _doc(shed):
    # host gable on L1, ridge along x at y=100, span 170 -> front eave at y=270.
    host = {"id": "h", "level": "L1", "ridge": [[-40.0, 100.0], [440.0, 100.0]],
            "eaves_h_in": 180.0, "ridge_h_in": 360.0, "overhang_in": [0.0, 0.0],
            "span_in": [170.0, 170.0], "gable": [True, True], "marker_end": 1}
    # dormer on L2 hosted on that roof; sits on it (y250) and cantilevers past
    # the eave to its face (y330). skirt_mode off keeps the FLAT sec 8.4 floor.
    dormer = {"id": "dm", "level": "L2", "ridge": [[200.0, 330.0], [200.0, 250.0]],
              "eaves_h_in": 250.0, "ridge_h_in": 320.0, "overhang_in": [0.0, 0.0],
              "span_in": [40.0, 40.0], "wall_span_in": [40.0, 40.0],
              "gable": [True, True], "marker_end": 0, "host": "h",
              "skirt_mode": "off"}
    roofs = [host, dormer]
    if shed:
        # a low shed on L1 over the WEST half of the cantilever overhang
        # (x 150..210), well below the L2 dormer floor -- a roof drawn beneath.
        roofs.append({"id": "sh", "level": "L1", "ridge": [[150.0, 270.0], [210.0, 270.0]],
                      "eaves_h_in": 90.0, "ridge_h_in": 100.0, "overhang_in": [0.0, 0.0],
                      "span_in": [60.0, 0.0], "eaves_bind": "manual",
                      "gable": [True, True], "marker_end": 1, "form": "shed"})
    return {"format": "floorplanner-design", "version": 6, "units": "inches",
            "settings": {},
            "levels": [{"id": "L1", "name": "default", "elevation_in": 0.0,
                        "height_in": 108.0, "kind": "storey", "reference": False},
                       {"id": "L2", "name": "upper", "elevation_in": 108.0,
                        "height_in": 96.0, "kind": "storey", "reference": False}],
            "vertices": [], "walls": [], "rooms": [], "furnishings": [],
            "groups": [], "roofs": roofs}


def _floor(model):
    ms = [m for m in model.meshes if m.name == "dormer_floor"]
    return np.vstack([m.verts for m in ms]) if ms else None


def test_the_floor_is_not_laid_over_a_roof_drawn_under_the_overhang(fp3d):
    v = _floor(fp3d.build_model(_doc(shed=True), furnishings=False, floors=True))
    assert v is not None, "the cantilever floor mesh is missing"
    # the shed covers x<=210 of the overhang (y>270); the floor must close only
    # the open-air east half -- no floor vertex stands over the shed.
    over_shed = v[(v[:, 0] < 205.0) & (-v[:, 1] > 271.0)]
    assert len(over_shed) == 0, (
        f"the floor is laid over the shed: {len(over_shed)} verts, "
        f"x from {float(v[:, 0].min()):.1f}")
    # and it does floor the open-air half (east of the shed)
    assert float(v[:, 0].max()) > 230.0


def test_the_control_floors_the_whole_overhang_with_no_roof_beneath(fp3d):
    # shed removed: the overhang is all open air, floored end to end -- the
    # invariant that must hold before and after the fix.
    v = _floor(fp3d.build_model(_doc(shed=False), furnishings=False, floors=True))
    assert v is not None
    assert float(v[:, 0].min()) < 165.0 and float(v[:, 0].max()) > 235.0, (
        f"the open-air overhang is not fully floored: x "
        f"[{float(v[:, 0].min()):.1f}, {float(v[:, 0].max()):.1f}]")
