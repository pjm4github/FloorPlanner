"""Phase 2 of the room/wall refactor: 'Detach wall from room' unlocks a
wall's corners (it stays part of the room); pulling a corner away from its
neighbour opens just that side -- a dashed open wall bridges the gap, keeps
the room closed for area, and disappears when the gap is filled again."""

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


def _right_wall(fp, room):
    return next(w for w in room.walls if not w.is_open
                and abs(w.p1.x() - 120) < 1 and abs(w.p2.x() - 120) < 1)


def _open_count(fp, scene):
    return sum(isinstance(w, fp.OpenWall) for w in scene.items())


def _shorten(fp, scene, wall, new_far=None):
    """Pull the wall's far end inward (as a corner drag would)."""
    new_far = new_far or QPointF(120, 60)
    if abs(wall.p2.y() - 120) < 1:
        wall.p2 = QPointF(new_far)
    else:
        wall.p1 = QPointF(new_far)
    wall.rebuild()
    fp.rebuild_all_walls(scene)


def test_detach_unlocks_corners_without_unbinding(fp, scene):
    room = _room(fp, scene)
    wall = _right_wall(fp, room)
    assert wall._ends_editable() is False             # locked while in a room
    fp.detach_wall_from_room(scene, wall)
    assert wall.room is room                          # still part of the room
    assert wall._corners_unlocked and wall._ends_editable()
    assert _open_count(fp, scene) == 0                # nothing open yet


def test_pulling_a_corner_opens_that_side(fp, scene):
    room = _room(fp, scene)
    area0 = room.area_sqft
    wall = _right_wall(fp, room)
    fp.detach_wall_from_room(scene, wall)
    _shorten(fp, scene, wall)                          # pull the far end to y=60
    assert _open_count(fp, scene) == 1
    assert wall.room is room                          # the wall stays bound
    assert room.area_sqft == pytest.approx(area0)     # loop stays closed
    ow = next(w for w in scene.items() if isinstance(w, fp.OpenWall))
    ys = sorted([ow.p1.y(), ow.p2.y()])
    assert ys == pytest.approx([60, 120])             # gap is the vacated part


def test_filling_the_gap_recloses_the_room(fp, scene):
    room = _room(fp, scene)
    wall = _right_wall(fp, room)
    fp.detach_wall_from_room(scene, wall)
    _shorten(fp, scene, wall)
    assert _open_count(fp, scene) == 1
    # extend the wall back to the corner -> gap closes
    if abs(wall.p2.y() - 60) < 1:
        wall.p2 = QPointF(120, 120)
    else:
        wall.p1 = QPointF(120, 120)
    wall.rebuild()
    fp.rebuild_all_walls(scene)
    assert _open_count(fp, scene) == 0


def test_open_wall_is_editable(fp, scene):
    room = _room(fp, scene)
    wall = _right_wall(fp, room)
    fp.detach_wall_from_room(scene, wall)
    _shorten(fp, scene, wall)
    ow = next(w for w in scene.items() if isinstance(w, fp.OpenWall))
    assert ow._ends_editable() is True


def test_open_walls_not_serialized_but_room_reloads(fp, qapp, win):
    sc = win.scene
    room = _room(fp, sc)
    wall = _right_wall(fp, room)
    fp.detach_wall_from_room(sc, wall)
    _shorten(fp, sc, wall)
    data = json.loads(json.dumps(win.serialize()))
    assert all("open" not in w for w in data["walls"])   # open walls excluded
    win.load_data(data)
    assert _open_count(fp, sc) == 1                       # regenerated on load
    r = next(x for x in sc.items() if isinstance(x, fp.RoomItem))
    assert r.area_sqft == pytest.approx(100.0)
    assert win.serialize() == data                       # idempotent


@pytest.mark.gui
def test_corner_drag_opens_side_via_mouse(fp, win, make_room, drag):
    sc = win.scene
    room = make_room(sc, 0, 0, 120, 120, "Den")
    win.set_tool(fp.TOOL_SELECT)
    win.show()
    win.zoom_fit()
    right = next(w for w in room.walls if not w.is_open
                 and abs(w.p1.x() - 120) < 1 and abs(w.p2.x() - 120) < 1)
    fp.detach_wall_from_room(sc, right)
    # drag the (120,120) corner up 60 scene units -> opens the lower-right side
    dy_px = int(-60 * win.view.transform().m11())
    drag(win, QPointF(120, 120), 0, dy_px, steps=4)
    assert sum(isinstance(w, fp.OpenWall) for w in sc.items()) == 1


def test_undo_restores_closed_room(fp, qapp, win):
    sc = win.scene
    room = _room(fp, sc)
    win._commit_if_changed()
    wall = _right_wall(fp, room)
    fp.detach_wall_from_room(sc, wall)
    _shorten(fp, sc, wall)
    win._commit_if_changed()
    assert _open_count(fp, sc) == 1
    win.undo()
    assert _open_count(fp, sc) == 0
    win.redo()
    assert _open_count(fp, sc) == 1
