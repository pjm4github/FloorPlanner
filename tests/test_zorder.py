"""Stacking order: Bring to front / Send to back on any item."""
import pytest
from PyQt6.QtCore import QPointF

pytestmark = pytest.mark.editing


def test_bring_to_front_and_send_to_back(fp, scene):
    a = fp.FurnishingItem("sofa", QPointF(0, 0), 0)
    b = fp.FurnishingItem("armchair", QPointF(50, 0), 0)
    scene.addItem(a)
    scene.addItem(b)
    fp.bring_to_front(a)
    assert a.zValue() > b.zValue()
    fp.send_to_back(a)
    assert a.zValue() < b.zValue()


def test_handle_front_back_dispatch(fp, scene):
    a = fp.FurnishingItem("sofa", QPointF(0, 0), 0)
    b = fp.FurnishingItem("armchair", QPointF(50, 0), 0)
    scene.addItem(a)
    scene.addItem(b)
    front, back = object(), object()
    assert fp.handle_front_back(a, front, front, back) is True
    assert a.zValue() > b.zValue()
    assert fp.handle_front_back(a, back, front, back) is True
    assert a.zValue() < b.zValue()
    assert fp.handle_front_back(a, object(), front, back) is False


def test_front_back_works_for_any_item_type(fp, scene, make_room):
    # walls, rooms and furnishings all expose the helpers
    room = make_room(scene, 0, 0, 120, 120, "Den")
    wall = next(it for it in scene.items() if isinstance(it, fp.WallItem))
    fp.bring_to_front(wall)
    fp.send_to_back(room)
    assert wall.zValue() > room.zValue()


def test_room_wall_renders_above_its_fill(fp, win, make_room):
    # a room-bound wall must sit above the translucent room fill (so it is not
    # hidden by its own tint) -- both by default and after raise_to_front
    sc = win.scene
    room = make_room(sc, 0, 0, 120, 120, "Den")
    wall = room.walls[0]
    assert wall.zValue() > room.zValue()          # default state
    room.raise_to_front()
    assert wall.zValue() > room.zValue()          # stays above after a click


def test_bring_wall_to_front_survives_raise(fp, win, make_room):
    # bringing a wall to front then interacting with its room must not bury it
    sc = win.scene
    room = make_room(sc, 0, 0, 120, 120, "Den")
    wall = room.walls[0]
    fp.bring_to_front(wall)
    top = max(it.zValue() for it in sc.items() if it is not wall)
    assert wall.zValue() > top
    room.raise_to_front()                         # a later interaction
    assert wall.zValue() > room.zValue()


def test_clicking_a_shared_wall_lifts_it_above_a_crossing_wall(fp, win):
    # q and t share the vertical wall; one top wall spans both. Clicking the
    # shared wall must lift IT above the spanning top wall (not bury it).
    sc = win.scene
    for p1, p2 in [((0, 0), (240, 0)), ((120, 0), (120, 120)),
                   ((0, 0), (0, 120)), ((0, 120), (120, 120)),
                   ((240, 0), (240, 120)), ((120, 120), (240, 120))]:
        sc.addItem(fp.WallItem(QPointF(*p1), QPointF(*p2), "interior"))
    fp.rebuild_all_walls(sc)
    for name, c in (("q", QPointF(60, 60)), ("t", QPointF(180, 60))):
        res = fp.detect_room(sc, c)
        r = fp.RoomItem(name, c, res[0], res[1], corners=res[2])
        sc.addItem(r)
        fp.bind_room_walls(sc, r)

    def find(a, b):
        for w in sc.items():
            if isinstance(w, fp.WallItem) and not w.is_open:
                k = (round(w.p1.x()), round(w.p1.y()),
                     round(w.p2.x()), round(w.p2.y()))
                if k == a + b or k == b + a:
                    return w
        return None

    shared, top = find((120, 0), (120, 120)), find((0, 0), (240, 0))
    assert {r.name for r in shared.rooms} == {"q", "t"}
    # simulate the wall mouse-press: raise the room, then lift the clicked wall
    shared.primary_room.raise_to_front()
    fp.bring_to_front(shared)
    assert shared.zValue() > top.zValue()
