"""Rubber-band selection: only fully-enclosed items are picked, and a room
enclosed by the band gets its own edge walls selected. Selection is READ-ONLY
(P0.5 fix 4 / defect 10): an edge backed only by a longer party wall is left
unselected -- it is NOT duplicated into a new wall. The two tests below that
once asserted that duplication now assert that selection creates nothing."""
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


def test_room_edge_on_party_wall_is_not_duplicated(fp, win):
    # REWRITTEN at P0.5 fix 4 (defect 10): this test used to assert the defect --
    # that selecting a room duplicated its party-wall edge into a new wall
    # (n0 + 1). Selection is now read-only, so it must create nothing.
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
    assert n1 == n0                           # selection created nothing
    assert room.isSelected()
    assert not party.isSelected()             # the long wall is left alone
    dup = [w for w in sc.items()
           if isinstance(w, fp.WallItem) and w is not party
           and abs(w.p1.x() - 120) < 1 and abs(w.p2.x() - 120) < 1]
    assert dup == []                          # no synthesized duplicate edge


def test_party_wall_edge_selection_leaves_the_door_intact(fp, win):
    # REWRITTEN at P0.5 fix 4: previously asserted that the *synthesized*
    # duplicate did not stack the party wall's door. With no synthesis, assert
    # instead that selection creates nothing and the party wall + its single
    # door are untouched.
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
    n0 = sum(isinstance(i, fp.WallItem) for i in sc.items())

    win.view.select_in_rect(QRectF(-12, -12, 150, 174))

    n1 = sum(isinstance(i, fp.WallItem) for i in sc.items())
    assert n1 == n0                           # nothing synthesized
    assert room.isSelected()
    assert len(party.openings) == 1           # the door is untouched
    dup = [w for w in sc.items()
           if isinstance(w, fp.WallItem) and w is not party
           and abs(w.p1.x() - 120) < 1 and abs(w.p2.x() - 120) < 1]
    assert dup == []
