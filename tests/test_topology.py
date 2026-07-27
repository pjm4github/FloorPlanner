"""P1.3: planar-topology over a Design -- trace_faces recovers rooms, the legacy
weld welds 31 ends, the (dy,-dx) winding is pinned, and the edit ops preserve
the faces they should."""
import json
import math
from collections import Counter
from pathlib import Path

import pytest

from floorplanner.design import legacy, topology
from floorplanner.design.model import Design

pytestmark = pytest.mark.io

ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = ROOT / "examples"


def _design(name):
    return Design.from_dict(json.loads((EXAMPLES / name).read_text("utf-8")))


def _pos(d):
    return {v.id: (v.x, v.y) for v in d.vertices}


def _poly(d, room):
    pos = _pos(d)
    return [pos[e.v] for e in room.outline]


def _room_area(d, room):
    return abs(topology._area2(_poly(d, room))) / 2.0


# --------------------------------------------------------------------------
# Acceptance 1: trace_faces on symmetricP1 recovers 19 room areas
# --------------------------------------------------------------------------
def test_trace_faces_recovers_every_room_area():
    # P1.3b: after the _inner_faces winding fix, ALL 20 rooms are recovered --
    # the Garage (largest, was wrongly dropped by defect 18) included. One extra
    # traced face (a ~60.6 sf wall-bounded region) matches no room; it is inside
    # no room (a genuinely unclaimed void in symmetricP1, not an outline fault).
    d = _design("symmetricP1.json")
    faces = topology.trace_faces(d)
    face_areas = Counter(round(f.area_in2, 1) for f in faces)
    room_areas = Counter(round(_room_area(d, r), 1) for r in d.rooms)
    matched = sum(min(face_areas[a], room_areas[a]) for a in face_areas)
    assert matched == len(d.rooms) == 20             # every room recovered
    unmatched = [r.name for r in d.rooms
                 if room_areas[round(_room_area(d, r), 1)]
                 > face_areas[round(_room_area(d, r), 1)]]
    assert unmatched == []                           # no room lost (Garage back)
    pos = _pos(d)
    extra = [f for f in faces
             if face_areas[round(f.area_in2, 1)] > room_areas[round(f.area_in2, 1)]]
    assert len(extra) == 1                           # the one unclaimed region
    epts = [pos[v] for v in extra[0].vertices]
    ecen = (sum(p[0] for p in epts) / len(epts), sum(p[1] for p in epts) / len(epts))
    assert not any(topology._pip(ecen, _poly(d, r)) for r in d.rooms)  # unclaimed


# --------------------------------------------------------------------------
# Acceptance 2: weld_endpoints welds exactly 31 ends on legacy planc1.json
# --------------------------------------------------------------------------
def test_weld_endpoints_welds_31_on_legacy_planc1():
    legacy_doc = json.loads((EXAMPLES / "planc1.json").read_text("utf-8"))
    walls = [dict(w, p1=list(w["p1"]), p2=list(w["p2"]))
             for w in legacy_doc["walls"]]
    assert legacy.weld_endpoints(walls) == 31


# --------------------------------------------------------------------------
# Winding: left = the (dy, -dx) side. If trace_faces wound the other way every
# left/right would silently swap and I6 would still pass -- so pin it directly.
# --------------------------------------------------------------------------
def test_left_is_the_dy_minus_dx_side():
    d = _design("symmetricP1.json")
    pos = _pos(d)
    rooms = {r.id: r for r in d.rooms}
    checked = 0
    for w in d.walls:
        if not w.left:
            continue
        a, b = pos[w.v1], pos[w.v2]
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy)
        if L < 1e-6:
            continue
        mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        probe = (mid[0] + 2 * dy / L, mid[1] - 2 * dx / L)     # 2" toward (dy,-dx)
        assert topology._pip(probe, _poly(d, rooms[w.left])), \
            f"wall {w.id}: (dy,-dx) probe is not inside its left room {w.left}"
        checked += 1
    assert checked > 0


def test_enclosing_face_agrees_with_the_left_side():
    # the (dy,-dx) probe of a shared wall must land in a face whose area is the
    # left room's -- ties trace_faces' winding to the stored `left`
    d = _design("symmetricP1.json")
    pos = _pos(d)
    rooms = {r.id: r for r in d.rooms}
    w = next(w for w in d.walls if w.left and w.right)         # a shared wall
    a, b = pos[w.v1], pos[w.v2]
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy)
    mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
    probe = (mid[0] + 2 * dy / L, mid[1] - 2 * dx / L)
    f = topology.enclosing_face(d, probe, w.level)
    assert f is not None
    assert round(f.area_in2, 1) == round(_room_area(d, rooms[w.left]), 1)


# --------------------------------------------------------------------------
# Edit ops preserve the faces they should
# --------------------------------------------------------------------------
def test_split_edge_adds_one_wall_and_preserves_faces():
    d = _design("symmetricP1.json")
    pos = _pos(d)
    w = next(w for w in d.walls if not w.openings)
    a, b = pos[w.v1], pos[w.v2]
    mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
    d2 = topology.split_edge(d, w.id, mid[0], mid[1])
    assert len(d2.walls) == len(d.walls) + 1
    assert len(d2.vertices) == len(d.vertices) + 1
    assert len(topology.trace_faces(d2)) == len(topology.trace_faces(d))


def test_split_edge_raises_on_a_wall_with_openings():
    # the landmine guard: splitting a wall that carries a door/window needs the
    # P3.3 redistribution rule, so split_edge must FAIL LOUD rather than quietly
    # leaving the opening on one segment
    d = _design("symmetricP1.json")
    pos = _pos(d)
    w = next(w for w in d.walls if isinstance(w.openings, list) and w.openings)
    a, b = pos[w.v1], pos[w.v2]
    mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
    with pytest.raises(NotImplementedError, match="P3.3"):
        topology.split_edge(d, w.id, mid[0], mid[1])


def test_merge_collinear_preserves_faces_and_reduces_walls():
    d = _design("symmetricP1.json")
    d2 = topology.merge_collinear(d)
    assert len(d2.walls) <= len(d.walls)
    assert len(topology.trace_faces(d2)) == len(topology.trace_faces(d))


def test_planarize_is_idempotent_on_a_planar_design():
    d = _design("symmetricP1.json")
    dp = topology.planarize(d)
    assert len(dp.walls) == len(d.walls)
    assert len(dp.vertices) == len(d.vertices)


# --------------------------------------------------------------------------
# No Qt: model proves it by isolated exec; topology/legacy import only model
# (Qt-free) and the stdlib -- assert that at the source level.
# --------------------------------------------------------------------------
@pytest.mark.parametrize("mod", ["topology.py", "legacy.py", "model.py",
                                 "validate.py"])
def test_design_module_source_is_qt_free(mod):
    src = (ROOT / "floorplanner" / "design" / mod).read_text("utf-8")
    assert "PyQt6" not in src and "from PyQt" not in src, f"{mod} references Qt"
    for line in src.splitlines():
        s = line.strip()
        if s.startswith("import ") or s.startswith("from "):
            assert "floorplanner" not in s or "floorplanner.design" in s, \
                f"{mod} imports a non-design floorplanner module: {s}"
