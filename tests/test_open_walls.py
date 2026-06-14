"""Phase 2 of the room/wall refactor: detach a wall from its room and the
resulting dashed 'open wall' that keeps the room closed for area, is
draggable like a wall, re-closes when a real wall fills the gap, and
round-trips through save/load and undo."""

import json

import pytest
from PyQt6.QtCore import QPointF

pytestmark = pytest.mark.rooms


def _room(fp, scene, x=0, y=0, w=120, h=120, name="A"):
    for a, b in [((x, y), (x + w, y)), ((x + w, y), (x + w, y + h)),
                 ((x + w, y + h), (x, y + h)), ((x, y + h), (x, y))]:
        scene.addItem(fp.WallItem(QPointF(*a), QPointF(*b), "interior"))
    fp.rebuild_all_walls(scene)
    c = QPointF(x + w / 2, y + h / 2)
    res = fp.detect_room(scene, c)
    room = fp.RoomItem(name, c, res[0], res[1], corners=res[2])
    scene.addItem(room)
    fp.bind_room_walls(scene, room)
    return room


def _open_count(fp, scene):
    return sum(isinstance(w, fp.OpenWall) for w in scene.items())


def test_detach_unlocks_wall_without_opening_yet(fp, scene):
    # detaching alone makes the wall independent/editable but does NOT open
    # the room (the wall still covers its edge) -- the gap appears on a move
    room = _room(fp, scene)
    area0 = room.area_sqft
    wall = next(w for w in room.walls if not w.is_open)
    fp.detach_wall_from_room(scene, wall)
    assert wall.room is None and wall._detached
    assert _open_count(fp, scene) == 0
    assert room.area_sqft == pytest.approx(area0)


def test_bound_wall_endpoints_locked_detached_unlocked(fp, scene):
    room = _room(fp, scene)
    wall = next(w for w in room.walls if not w.is_open)
    assert wall._ends_editable() is False             # locked while in a room
    fp.detach_wall_from_room(scene, wall)
    assert wall._ends_editable() is True              # editable once detached
    # an open wall (after a move) is editable too
    wall.p1, wall.p2 = QPointF(400, 0), QPointF(400, 120)
    wall.rebuild()
    fp.rebuild_all_walls(scene)
    ow = next(w for w in room.walls if w.is_open)
    assert ow._ends_editable() is True


def test_open_wall_preserves_shape_when_real_wall_moves_away(fp, scene):
    room = _room(fp, scene)
    wall = next(w for w in room.walls if abs(w.p1.x() - 120) < 1
                and abs(w.p2.x() - 120) < 1)
    fp.detach_wall_from_room(scene, wall)
    wall.p1, wall.p2 = QPointF(300, 0), QPointF(300, 120)   # drag it away
    wall.rebuild()
    fp.rebuild_all_walls(scene)
    assert _open_count(fp, scene) == 1
    assert room.area_sqft == pytest.approx(100.0)


def test_reclose_removes_the_open_wall(fp, scene):
    room = _room(fp, scene)
    wall = next(w for w in room.walls if abs(w.p1.x() - 120) < 1
                and abs(w.p2.x() - 120) < 1)
    fp.detach_wall_from_room(scene, wall)
    wall.p1, wall.p2 = QPointF(300, 0), QPointF(300, 120)
    wall.rebuild()
    fp.rebuild_all_walls(scene)
    assert _open_count(fp, scene) == 1
    # drawing a real wall back on the edge re-closes the room
    scene.addItem(fp.WallItem(QPointF(120, 0), QPointF(120, 120), "interior"))
    fp.rebuild_all_walls(scene)
    assert _open_count(fp, scene) == 0
    assert all(not w.is_open for w in room.walls)


def test_dragging_open_wall_reshapes_room(fp, scene):
    room = _room(fp, scene)
    wall = next(w for w in room.walls if abs(w.p1.x() - 120) < 1
                and abs(w.p2.x() - 120) < 1)
    fp.detach_wall_from_room(scene, wall)
    wall.p1, wall.p2 = QPointF(400, 0), QPointF(400, 120)
    wall.rebuild()
    fp.rebuild_all_walls(scene)
    ow = next(w for w in room.walls if w.is_open)
    # slide the open edge out to x=156 (its neighbours stretch with it)
    ow.p1, ow.p2 = QPointF(156, 0), QPointF(156, 120)
    ow.rebuild()
    for w in room.walls:
        if not w.is_open:
            if abs(w.p1.x() - 120) < 1:
                w.p1 = QPointF(156, w.p1.y())
            if abs(w.p2.x() - 120) < 1:
                w.p2 = QPointF(156, w.p2.y())
            w.rebuild()
    fp.rebuild_all_walls(scene)
    assert room.area_sqft == pytest.approx(130.0)     # 120 x 156


def test_open_walls_not_serialized_but_room_reloads(fp, qapp, win):
    sc = win.scene
    room = _room(fp, sc)
    wall = next(w for w in room.walls if abs(w.p1.x() - 120) < 1
                and not w.is_open)
    fp.detach_wall_from_room(sc, wall)
    wall.p1, wall.p2 = QPointF(300, 0), QPointF(300, 120)
    wall.rebuild()
    fp.rebuild_all_walls(sc)
    data = json.loads(json.dumps(win.serialize()))
    assert all(not isinstance(w, dict) or "open" not in w
               for w in data["walls"])               # open walls excluded
    win.load_data(data)
    r = next(x for x in sc.items() if isinstance(x, fp.RoomItem))
    assert sum(w.is_open for w in r.walls) == 1       # regenerated on load
    assert r.area_sqft == pytest.approx(100.0)
    assert win.serialize() == data                    # idempotent


def test_undo_restores_closed_room(fp, qapp, win):
    sc = win.scene
    room = _room(fp, sc)
    win._commit_if_changed()
    wall = next(w for w in room.walls if abs(w.p1.x() - 120) < 1
                and not w.is_open)
    fp.detach_wall_from_room(sc, wall)
    wall.p1, wall.p2 = QPointF(300, 0), QPointF(300, 120)   # move -> opens
    wall.rebuild()
    fp.rebuild_all_walls(sc)
    win._commit_if_changed()
    assert _open_count(fp, sc) == 1
    win.undo()
    assert _open_count(fp, sc) == 0
    r = next(x for x in sc.items() if isinstance(x, fp.RoomItem))
    assert all(not w.is_open for w in r.walls)
    win.redo()
    assert _open_count(fp, sc) == 1
