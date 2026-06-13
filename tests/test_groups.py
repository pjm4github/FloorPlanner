"""Group / move / ungroup behaviour, including two regressions:

1. Dragging a *grouped wall* used to run WallItem's slide + join logic on a
   group child, deleting walls on ungroup (the gui test below).
2. dissolve()'s removeFromGroup() handed item ownership back to Python; with
   no external reference the walls were garbage-collected out of the scene on
   ungroup. test_*_survives_gc forces a collection to lock this down."""
import gc

import pytest
from PyQt6.QtCore import QPointF, QRectF

pytestmark = pytest.mark.groups


def _select_walls_and_furnishings(fp, scene):
    for it in list(scene.items()):
        if isinstance(it, (fp.WallItem, fp.FurnishingItem)):
            it.setSelected(True)


def test_group_move_ungroup_preserves_items(fp, win, make_room,
                                            first_furnishing, counts):
    sc = win.scene
    make_room(sc, 0, 0, 144, 120, "Den")
    sc.addItem(fp.FurnishingItem(first_furnishing, QPointF(60, 60), 0))
    before = counts(sc)

    _select_walls_and_furnishings(fp, sc)
    win.group_selected()
    g = next(i for i in sc.items() if isinstance(i, fp.GroupItem))
    g.setPos(60, 48)         # simulate a drag...
    g.bake()                 # ...folded in on release
    sc.clearSelection()
    g.setSelected(True)
    win.ungroup_selected()

    assert counts(sc) == before


def test_ungrouped_walls_survive_gc(fp, win, make_room, first_furnishing,
                                    counts):
    # the items deliberately have no external Python reference, so a GC
    # right after ungroup would destroy them if dissolve() didn't keep the
    # scene owning them
    sc = win.scene
    make_room(sc, 0, 0, 144, 120, "Den")
    sc.addItem(fp.FurnishingItem(first_furnishing, QPointF(60, 60), 0))
    before = counts(sc)
    _select_walls_and_furnishings(fp, sc)
    win.group_selected()
    g = next(i for i in sc.items() if isinstance(i, fp.GroupItem))
    g.setPos(60, 48)
    g.bake()
    sc.clearSelection()
    g.setSelected(True)
    win.ungroup_selected()
    del g
    gc.collect()
    assert counts(sc) == before


def test_bake_translates_room_region(fp, win, make_room):
    sc = win.scene
    room = make_room(sc, 0, 0, 144, 120, "Den")
    before = room.path.boundingRect().x()
    for it in list(sc.items()):
        if isinstance(it, fp.WallItem):
            it.setSelected(True)
    win.group_selected()
    g = next(i for i in sc.items() if isinstance(i, fp.GroupItem))
    g.setPos(72, 0)
    g.bake()
    after = room.path.boundingRect().x()
    assert after - before == pytest.approx(72, abs=6)


def test_extracted_room_region_follows_move(fp, win):
    # extract a room whose right edge is a longer party wall, then move the
    # group clear of that wall: the grey region/outline must follow (baked
    # on release, not live)
    sc = win.scene
    party = fp.WallItem(QPointF(120, 0), QPointF(120, 300), "interior")
    sc.addItem(party)
    for p1, p2 in [((0, 0), (120, 0)), ((120, 144), (0, 144)),
                   ((0, 144), (0, 0))]:
        sc.addItem(fp.WallItem(QPointF(*p1), QPointF(*p2), "interior"))
    fp.rebuild_all_walls(sc)
    res = fp.detect_room(sc, QPointF(60, 72))
    room = fp.RoomItem("Den", QPointF(60, 72), res[0], res[1], corners=res[2])
    sc.addItem(room)

    win.view.select_in_rect(QRectF(-12, -12, 150, 174))   # duplicates the edge
    before = room.path.boundingRect()

    win.group_selected()
    g = next(i for i in sc.items() if isinstance(i, fp.GroupItem))
    g.setPos(200, 100)            # move clear of the stationary party wall
    g.bake()

    after = room.path.boundingRect()
    assert after.x() - before.x() == pytest.approx(200, abs=8)
    assert after.y() - before.y() == pytest.approx(100, abs=8)
    # the original party wall is left exactly where it was
    assert party.p1.x() == pytest.approx(120)
    assert party.p2.y() == pytest.approx(300)


def test_furnishings_ride_along(fp, win, make_room, first_furnishing):
    sc = win.scene
    make_room(sc, 0, 0, 144, 120, "Den")
    f = fp.FurnishingItem(first_furnishing, QPointF(60, 60), 0)
    sc.addItem(f)
    _select_walls_and_furnishings(fp, sc)
    win.group_selected()
    g = next(i for i in sc.items() if isinstance(i, fp.GroupItem))
    g.setPos(40, 30)
    g.bake()
    assert (f.scenePos().x(), f.scenePos().y()) == pytest.approx((100, 90))


@pytest.mark.gui
def test_drag_group_by_wall_preserves_items(fp, win, make_room,
                                            first_furnishing, drag, counts):
    sc = win.scene
    make_room(sc, 0, 0, 144, 120, "Den")
    sc.addItem(fp.FurnishingItem(first_furnishing, QPointF(60, 60), 0))
    before = counts(sc)

    _select_walls_and_furnishings(fp, sc)
    win.group_selected()
    g = next(i for i in sc.items() if isinstance(i, fp.GroupItem))

    win.show()
    win.zoom_fit()

    # press on the midpoint of the top wall -- a grouped WALL (the path that
    # used to corrupt geometry), not a furnishing
    top = min((i for i in g.childItems() if isinstance(i, fp.WallItem)),
              key=lambda w: w.p1.y() + w.p2.y())
    mid = QPointF((top.p1.x() + top.p2.x()) / 2, (top.p1.y() + top.p2.y()) / 2)
    drag(win, mid, 60, 40)

    if g.scene() is not None:
        sc.clearSelection()
        g.setSelected(True)
        win.ungroup_selected()

    assert counts(sc) == before
