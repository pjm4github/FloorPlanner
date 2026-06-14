"""Rubber-band selection: only fully-enclosed items are picked, and a
room enclosed by the band gets a complete loop of selected walls -- any
edge carried by a longer party wall is duplicated rather than dragging
that shared wall into the selection."""
import pytest
from PyQt6.QtCore import QPointF, QRectF

pytestmark = pytest.mark.selection


def test_selects_only_fully_enclosed_walls(fp, win):
    sc = win.scene
    inside = fp.WallItem(QPointF(20, 20), QPointF(80, 20), "interior")
    crossing = fp.WallItem(QPointF(60, 60), QPointF(200, 60), "interior")
    sc.addItem(inside)
    sc.addItem(crossing)
    fp.rebuild_all_walls(sc)

    win.view.select_in_rect(QRectF(0, 0, 100, 100))

    assert inside.isSelected()
    assert not crossing.isSelected()        # one end sticks out -> excluded


def test_selects_only_fully_enclosed_furnishings(fp, win, first_furnishing):
    sc = win.scene
    near = fp.FurnishingItem(first_furnishing, QPointF(60, 60), 0)
    far = fp.FurnishingItem(first_furnishing, QPointF(400, 400), 0)
    sc.addItem(near)
    sc.addItem(far)

    win.view.select_in_rect(QRectF(0, 0, 240, 240))

    assert near.isSelected()
    assert not far.isSelected()


def test_standalone_room_selects_four_walls_no_synthesis(fp, win, make_room):
    sc = win.scene
    room = make_room(sc, 0, 0, 144, 120, "Den")
    n0 = sum(isinstance(i, fp.WallItem) for i in sc.items())

    win.view.select_in_rect(QRectF(-12, -12, 168, 144))

    n1 = sum(isinstance(i, fp.WallItem) for i in sc.items())
    assert n1 == n0                          # every edge already a wall
    assert room.isSelected()
    sel = [w for w in sc.items()
           if isinstance(w, fp.WallItem) and w.isSelected()]
    assert len(sel) == 4


def test_room_edge_on_party_wall_is_duplicated(fp, win):
    sc = win.scene
    # a vertical party wall taller than the room on its left
    party = fp.WallItem(QPointF(120, 0), QPointF(120, 300), "interior")
    sc.addItem(party)
    for p1, p2 in [((0, 0), (120, 0)), ((120, 144), (0, 144)),
                   ((0, 144), (0, 0))]:
        sc.addItem(fp.WallItem(QPointF(*p1), QPointF(*p2), "interior"))
    fp.rebuild_all_walls(sc)
    res = fp.detect_room(sc, QPointF(60, 72))
    assert res is not None
    room = fp.RoomItem("Den", QPointF(60, 72), res[0], res[1], corners=res[2])
    sc.addItem(room)
    n0 = sum(isinstance(i, fp.WallItem) for i in sc.items())

    # band encloses the room but not the top of the party wall
    win.view.select_in_rect(QRectF(-12, -12, 150, 174))

    n1 = sum(isinstance(i, fp.WallItem) for i in sc.items())
    assert n1 == n0 + 1                       # the shared edge was duplicated
    assert not party.isSelected()             # the long wall is left alone
    assert room.isSelected()
    dup = [w for w in sc.items()
           if isinstance(w, fp.WallItem) and w is not party
           and abs(w.p1.x() - 120) < 1 and abs(w.p2.x() - 120) < 1]
    assert len(dup) == 1
    assert dup[0].isSelected()
    assert dup[0].length() == pytest.approx(144, abs=2)


def test_duplicated_edge_does_not_stack_the_door(fp, win):
    # the duplicated party wall stays plain (the door belongs to ONE wall);
    # it just opens its body so the door shows through -- never two on top
    sc = win.scene
    party = fp.WallItem(QPointF(120, 0), QPointF(120, 300), "interior")
    door = fp.OpeningItem(party, "door", "3280", 72)   # within the room edge
    party.openings.append(door)
    for p1, p2 in [((0, 0), (120, 0)), ((120, 144), (0, 144)),
                   ((0, 144), (0, 0))]:
        sc.addItem(fp.WallItem(QPointF(*p1), QPointF(*p2), "interior"))
    sc.addItem(party)
    fp.rebuild_all_walls(sc)
    res = fp.detect_room(sc, QPointF(60, 72))
    room = fp.RoomItem("Den", QPointF(60, 72), res[0], res[1], corners=res[2])
    sc.addItem(room)

    win.view.select_in_rect(QRectF(-12, -12, 150, 174))

    dup = next(w for w in sc.items()
               if isinstance(w, fp.WallItem) and w is not party
               and abs(w.p1.x() - 120) < 1 and abs(w.p2.x() - 120) < 1)
    assert len(dup.openings) == 0             # no duplicate door symbol
    # but the duplicate's body is opened where the party wall's door is
    assert not dup._path.contains(QPointF(120, 72))
