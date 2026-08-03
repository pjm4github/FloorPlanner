"""Rooms bind their enclosing walls (sharing one wall on a boundary between
adjacent rooms -- the shared-wall model), move with them, raise to the front,
and round-trip through save/load and undo."""

import json

import pytest
from PyQt6.QtCore import QLineF, QPointF

pytestmark = pytest.mark.rooms


def _rect_walls(fp, scene, x, y, w, h, skip=None):
    """Add up to four interior walls for a rectangle; `skip` (a list of
    (a,b) endpoint pairs) is omitted so a shared edge can be reused."""
    corners = [QPointF(x, y), QPointF(x + w, y),
               QPointF(x + w, y + h), QPointF(x, y + h)]
    for i in range(4):
        a, b = corners[i], corners[(i + 1) % 4]
        if skip and any(
                (QLineF(a, sa).length() < 1 and QLineF(b, sb).length() < 1)
                or (QLineF(a, sb).length() < 1 and QLineF(b, sa).length() < 1)
                for sa, sb in skip):
            continue
        scene.addItem(fp.WallItem(QPointF(a), QPointF(b), "interior"))
    fp.rebuild_all_walls(scene)


def _make(fp, scene, x, y, w, h, name, skip=None):
    _rect_walls(fp, scene, x, y, w, h, skip)
    c = QPointF(x + w / 2, y + h / 2)
    res = fp.detect_room(scene, c)
    room = fp.RoomItem(fp.unique_room_name(scene, name), c,
                       res[0], res[1], corners=res[2])
    scene.addItem(room)
    fp.bind_room_walls(scene, room)
    return room


def _nwalls(fp, scene):
    return sum(isinstance(i, fp.WallItem) for i in scene.items())


def test_creation_binds_four_walls(fp, scene):
    room = _make(fp, scene, 0, 0, 120, 120, "A")
    assert len(room.walls) == 4
    assert all(room in w.rooms for w in room.walls)


def test_adjacent_rooms_share_one_wall(fp, scene):
    a = _make(fp, scene, 0, 0, 120, 120, "A")
    # B reuses A's right wall (x=120) as its left edge -> shares the SAME wall
    b = _make(fp, scene, 120, 0, 120, 120, "B",
              skip=[(QPointF(120, 0), QPointF(120, 120))])
    assert len(a.walls) == 4 and len(b.walls) == 4
    shared = [w for w in scene.items()
              if isinstance(w, fp.WallItem)
              and abs(w.p1.x() - 120) < 0.5 and abs(w.p2.x() - 120) < 0.5]
    assert len(shared) == 1                       # one shared wall, not two
    assert {r.name for r in shared[0].rooms} == {"A", "B"}


def test_delete_shared_wall_keeps_both_rooms(fp, scene):
    # INTENTIONALLY REPLACES the fracture-era test that asserted the shared
    # edge SURVIVES deletion (the defect-17 no-op). P4.1's measured new truth:
    # the party wall genuinely goes, and BOTH rooms survive through their
    # stored outlines, each with one open edge and its area unchanged
    # (measured at the P4.1 read-back: 100.0 sf, 3 bound + 1 open each).
    a = _make(fp, scene, 0, 0, 120, 120, "A")
    b = _make(fp, scene, 120, 0, 120, 120, "B",
              skip=[(QPointF(120, 0), QPointF(120, 120))])
    shared = next(w for w in scene.items()
                  if isinstance(w, fp.WallItem)
                  and abs(w.p1.x() - 120) < 0.5 and abs(w.p2.x() - 120) < 0.5)
    area_a, area_b = a.area_sqft, b.area_sqft
    fp.delete_wall(scene, shared)
    assert shared.scene() is None
    assert not [w for w in scene.items() if isinstance(w, fp.WallItem)
                and abs(w.p1.x() - 120) < 0.5 and abs(w.p2.x() - 120) < 0.5]
    assert a.area_sqft == pytest.approx(area_a)
    assert b.area_sqft == pytest.approx(area_b)
    assert len(a.walls) == 3 and len(b.walls) == 3
    assert len(a.open_edges()) == 1 and len(b.open_edges()) == 1


def test_rebind_is_idempotent(fp, scene):
    a = _make(fp, scene, 0, 0, 120, 120, "A")
    _make(fp, scene, 120, 0, 120, 120, "B",
          skip=[(QPointF(120, 0), QPointF(120, 120))])
    n = _nwalls(fp, scene)
    for _ in range(3):
        fp.rebuild_all_walls(scene)               # re-detect + re-bind
    assert _nwalls(fp, scene) == n                # no runaway synthesis
    assert len(a.walls) == 4


def test_moving_a_room_does_not_distort_its_neighbour(fp, scene):
    # A and B share one wall; moving A to empty space must leave that wall
    # with B so B keeps its full area. ROUTE CHANGED AT P4.2 (declared): the
    # label-drag's move start is extract_room now -- _privatize_shared_walls,
    # the 51-line shadow of it, is deleted. Assertions unchanged.
    a = _make(fp, scene, 0, 0, 120, 120, "A")
    b = _make(fp, scene, 120, 0, 120, 120, "B",
              skip=[(QPointF(120, 0), QPointF(120, 120))])
    area_a, area_b = a.area_sqft, b.area_sqft
    shared = next(w for w in a.walls if len(w.rooms) == 2)
    a._moving_room = True
    fp.extract_room(scene, a)            # what mousePress does on move start
    # the OUTLINE is what says which walls are the room's (P3.5), so the
    # privatised edge must name the copy -- otherwise `room_walls` still hands
    # the shared wall to bake / room_boolean and the swap only half happened
    assert shared not in fp.room_walls(a)
    assert shared in fp.room_walls(b)
    a._translate(0, 300)                 # drop into empty space below
    fp.rebuild_all_walls(scene)
    assert b.area_sqft == pytest.approx(area_b)   # neighbour untouched
    assert a.area_sqft == pytest.approx(area_a)   # mover keeps its size


def test_translate_moves_walls_openings_and_region(fp, scene):
    room = _make(fp, scene, 0, 0, 120, 120, "A")
    wall = room.walls[0]
    op = fp.OpeningItem(wall, "door", "3080", wall.length() / 2)
    wall.openings.append(op)
    wall.rebuild()
    op_x0 = op.pos().x()
    a0 = room.anchor.x()
    room._translate(36, 0)
    assert room.anchor.x() == pytest.approx(a0 + 36)
    assert all(room in w.rooms for w in room.walls)
    assert op.pos().x() == pytest.approx(op_x0 + 36, abs=1)


def test_wall_stretch_keeps_binding(fp, scene):
    """REWRITTEN AT P3.5: the room's bottom corners are RELOCATED rather than
    given new coordinates.

    Same claim -- stretching a room's side grows its area and keeps all four
    walls bound -- but the old mechanism was `w.p1 = ...` per wall followed by
    a re-detection sweep. A bare assignment is split-on-write (P3.1): it mints
    a fresh vertex for that one wall end, so the two walls meeting at a corner
    come apart and only detection could put the room back together. Moving the
    CORNER moves everything holding it, which is what the editor's drag now
    does and what the outline needs to follow without re-detecting."""
    room = _make(fp, scene, 0, 0, 120, 120, "A")
    area0 = room.area_sqft
    # widen the room downward: relocate each corner on the bottom edge once
    seen = {}
    for w in room.walls:
        for a in ("p1", "p2"):
            v = w.end_vertex(a)
            if v.y >= 119.5 and id(v) not in seen:
                seen[id(v)] = (v, v.relocated_to(QPointF(v.x, v.y + 36)))
    for v, moved in seen.values():
        for w in room.walls:
            for a in ("p1", "p2"):
                if w.end_vertex(a) is v:
                    w.set_end_vertex(a, moved)
        for e in room.outline:
            if e.v is v:
                e.v = moved
    fp.rebuild_all_walls(scene)
    assert room.area_sqft > area0
    assert len(room.walls) == 4 and all(room in w.rooms for w in room.walls)


def test_deleting_wall_unbinds_it(fp, scene):
    room = _make(fp, scene, 0, 0, 120, 120, "A")
    w = room.walls[0]
    scene.removeItem(w)
    assert w not in room.walls


def test_deleting_room_releases_walls(fp, scene):
    room = _make(fp, scene, 0, 0, 120, 120, "A")
    walls = list(room.walls)
    room.clear_walls()
    assert all(not w.rooms for w in walls)
    assert walls[0].scene() is scene             # walls stay on the canvas


def test_raise_to_front_orders_rooms(fp, qapp, win):
    sc = win.scene
    a = _make(fp, sc, 0, 0, 120, 120, "A")
    b = _make(fp, sc, 200, 0, 120, 120, "B")
    a.raise_to_front()
    b.raise_to_front()
    assert max(w.zValue() for w in b.walls) > max(w.zValue() for w in a.walls)
    # an opening sits above its wall
    w = a.walls[0]
    op = fp.OpeningItem(w, "window", "3030", w.length() / 2)
    w.openings.append(op)
    a.raise_to_front()
    assert op.zValue() > w.zValue()


def test_binding_survives_save_load(fp, qapp, win):
    sc = win.scene
    _make(fp, sc, 0, 0, 120, 120, "A")
    _make(fp, sc, 120, 0, 120, 120, "B",
          skip=[(QPointF(120, 0), QPointF(120, 120))])
    data = json.loads(json.dumps(win.serialize()))
    win.load_data(data)
    rooms = {r.name: r for r in sc.items() if isinstance(r, fp.RoomItem)}
    for r in rooms.values():
        assert len(r.walls) == 4 and all(r in w.rooms for w in r.walls)
    assert win.serialize() == data               # idempotent round-trip


def test_legacy_v1_plan_binds_on_load(fp, qapp, win):
    # a v1-style document: walls with NO "room" key, rooms by anchor only
    doc = {
        "format": fp.FILE_FORMAT, "version": 1, "units": "inches",
        "settings": {},
        "walls": [{"type": "interior", "p1": p1, "p2": p2, "openings": []}
                  for p1, p2 in [([0, 0], [120, 0]), ([120, 0], [120, 120]),
                                 ([120, 120], [0, 120]), ([0, 120], [0, 0])]],
        "rooms": [{"name": "Den", "anchor": [60, 60], "label_offset": [0, 0],
                   "show_dimensions": False, "properties": {}}],
        "furnishings": [],
    }
    win.load_data(doc)
    room = next(r for r in win.scene.items() if isinstance(r, fp.RoomItem))
    assert len(room.walls) == 4 and all(room in w.rooms for w in room.walls)


def test_serialize_is_z_independent(fp, qapp, win):
    sc = win.scene
    a = _make(fp, sc, 0, 0, 120, 120, "A")
    _make(fp, sc, 200, 0, 120, 120, "B")
    base = win.serialize()
    a.raise_to_front()                           # changes z, not the document
    assert win.serialize() == base
