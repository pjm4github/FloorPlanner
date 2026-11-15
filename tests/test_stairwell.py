"""The stairwell (0338): the floor above a parametric stair, and the ceiling
of the stair's own storey, are cut open over it. `fp3d.py` is loaded by path."""
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
    spec = importlib.util.spec_from_file_location("fp3d_well_test", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _doc(state, rotation=0.0, pos=(200.0, 200.0), upper=True):
    """Two storeys, each one 400 x 400 room, and one stair on the first."""
    vs = [{"id": f"v{i}", "x": x, "y": y}
          for i, (x, y) in enumerate([(0, 0), (400, 0), (400, 400), (0, 400)])]
    room = {"category": "interior", "outline": [{"v": v["id"]} for v in vs]}
    levels = [{"id": "L1", "name": "First", "elevation_in": 0.0,
               "height_in": 96.0}]
    rooms = [dict(room, id="r1", level="L1", name="Hall")]
    if upper:
        levels.append({"id": "L2", "name": "Second", "elevation_in": 108.0,
                       "height_in": 96.0})
        rooms.append(dict(room, id="r2", level="L2", name="Landing"))
    fu = {"id": "f1", "level": "L1", "kind": "stairs", "pos": list(pos),
          "rotation": rotation}
    if state is not None:
        fu["state"] = state
    return {"version": 6, "vertices": vs, "walls": [], "rooms": rooms,
            "levels": levels, "furnishings": [fu]}


def _top_area(model, name, z):
    """Area of the upward faces of mesh `name` lying at height z."""
    total = 0.0
    for m in model.meshes:
        if m.name != name:
            continue
        tri = m.verts[m.faces]
        flat = np.all(np.abs(tri[:, :, 2] - z) < 1e-6, axis=1)
        n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
        up = n[:, 2] > 0
        total += float(n[flat & up, 2].sum()) / 2.0
    return total


def _state(fp3d, **over):
    return dict(fp3d.STAIRGEO.STATE_DEFAULTS, **over)


def test_the_floor_above_is_open_over_the_stair(fp3d):
    sg = fp3d.STAIRGEO
    st = _state(fp3d)
    geom = sg.geometry_from_state(st)[0]
    need = sg.required_opening(geom, 80.0)
    model = fp3d.build_model(_doc(st))
    assert _top_area(model, "floors", 0.0) == pytest.approx(160000.0)
    assert _top_area(model, "floors", 108.0) == pytest.approx(
        160000.0 - 36.0 * need)
    assert [i for i in model.info if "cut open over a stairwell" in i]


def test_the_ceiling_under_it_is_open_too(fp3d):
    sg = fp3d.STAIRGEO
    st = _state(fp3d, well_opening_in=100.0)
    model = fp3d.build_model(_doc(st))
    assert _top_area(model, "ceilings", 96.0 + fp3d.SLAB_T) == pytest.approx(
        160000.0 - 36.0 * 100.0), "the STATED opening is the one cut"
    assert sg.stairwell(st)[1]


def test_nothing_is_cut_without_parameters_or_without_a_floor_above(fp3d):
    legacy = fp3d.build_model(_doc({"flight": "full", "turn": "left",
                                    "direction": "up"}))
    assert _top_area(legacy, "floors", 108.0) == pytest.approx(160000.0)
    short = fp3d.build_model(_doc(_state(fp3d, total_rise_in=21.0)))
    assert _top_area(short, "floors", 108.0) == pytest.approx(160000.0)
    assert _top_area(short, "ceilings", 97.0) == pytest.approx(160000.0)


def test_the_hole_is_where_the_stair_is_at_any_rotation(fp3d):
    """Sample the floor above: solid beside the stair, open over its head."""
    sg = fp3d.STAIRGEO
    st = _state(fp3d)
    for rot in (0.0, 90.0, 37.0):
        model = fp3d.build_model(_doc(st, rotation=rot))
        stair = np.vstack([m.verts for m in model.meshes
                           if m.name.startswith("furnishings")])
        head = stair[stair[:, 2] > 100.0][:, :2].mean(axis=0)
        floor = [m for m in model.meshes if m.name == "floors"]
        tri = np.vstack([m.verts[m.faces] for m in floor])
        tri = tri[np.all(np.abs(tri[:, :, 2] - 108.0) < 1e-6, axis=1)]

        def covered(p, tri=tri):
            a, b, c = tri[:, 0, :2], tri[:, 1, :2], tri[:, 2, :2]

            def cr(u, v, w):
                return ((v[:, 0] - u[:, 0]) * (w[1] - u[:, 1])
                        - (v[:, 1] - u[:, 1]) * (w[0] - u[:, 0]))
            d1, d2, d3 = cr(a, b, p), cr(b, c, p), cr(c, a, p)
            inside = ((d1 >= 0) & (d2 >= 0) & (d3 >= 0)) | (
                (d1 <= 0) & (d2 <= 0) & (d3 <= 0))
            return bool(inside.any())

        assert not covered(head), f"rotation {rot}: floor over the stair head"
        assert covered((20.0, -20.0)), "the far corner is still floor"
    assert sg.DEFAULT_FLOOR_T_IN == 12.0


def test_a_u_stair_opens_over_both_flights_and_the_landing(fp3d):
    sg = fp3d.STAIRGEO
    st = _state(fp3d, type="U", turn_deg=180, well_opening_in=400.0)
    geom = sg.geometry_from_state(st)[0]
    quads = sg.opening_rects(geom, 400.0)
    assert len(quads) == 3
    area = sum(abs(fp3d._ring_area2(q)) / 2.0 for q in quads)
    assert area == pytest.approx(36.0 * geom.total_run + 72.0 * 36.0)
    model = fp3d.build_model(_doc(st))
    assert _top_area(model, "floors", 108.0) == pytest.approx(160000.0 - area)


def test_minus_convex_conserves_area(fp3d):
    tri = [(0.0, 0.0), (10.0, 0.0), (0.0, 10.0)]
    hole = [(1.0, 1.0), (3.0, 1.0), (3.0, 3.0), (1.0, 3.0)]
    pieces = fp3d._minus_convex(tri, hole)
    assert sum(abs(fp3d._ring_area2(p)) / 2 for p in pieces) == pytest.approx(46.0)
    assert fp3d._minus_convex(tri, [(-5, -5), (20, -5), (20, 20), (-5, 20)]) == []
    away = fp3d._minus_convex(tri, [(50, 50), (60, 50), (60, 60), (50, 60)])
    assert sum(abs(fp3d._ring_area2(p)) / 2 for p in away) == pytest.approx(50.0)
