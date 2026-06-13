"""Arrow-key nudge of selected groups / ungrouped furnishings."""
import pytest
from PyQt6.QtCore import QPointF

pytestmark = pytest.mark.editing


def test_nudge_furnishing_coarse_and_fine(fp, win, first_furnishing):
    sc = win.scene
    f = fp.FurnishingItem(first_furnishing, QPointF(100, 100), 0)
    sc.addItem(f)
    f.setSelected(True)

    win.nudge_selected(1, 0, fine=False)        # right by the wall-snap step
    assert f.pos().x() == pytest.approx(100 + fp.SETTINGS["wall_snap_in"])
    win.nudge_selected(0, -1, fine=True)        # up by a fine 1" step
    assert f.pos().y() == pytest.approx(99)


def test_nudge_group_moves_walls(fp, win, make_room):
    sc = win.scene
    make_room(sc, 0, 0, 144, 96, "Den")
    for w in [it for it in sc.items() if isinstance(it, fp.WallItem)]:
        w.setSelected(True)
    win.group_selected()
    wall = next(it for it in sc.items() if isinstance(it, fp.WallItem))
    y0 = wall.p1.y()

    win.nudge_selected(0, 1, fine=False)
    assert wall.p1.y() == pytest.approx(y0 + fp.SETTINGS["wall_snap_in"])


def test_grouped_furnishing_nudges_once_not_twice(fp, win, make_room,
                                                  first_furnishing):
    # the group and its child furnishing are both selected (Qt couples them);
    # the furnishing must move once via the group, not twice
    sc = win.scene
    make_room(sc, 0, 0, 144, 96, "Den")
    f = fp.FurnishingItem(first_furnishing, QPointF(72, 48), 0)
    sc.addItem(f)
    for it in list(sc.items()):
        if isinstance(it, (fp.WallItem, fp.FurnishingItem)):
            it.setSelected(True)
    win.group_selected()
    x0 = f.scenePos().x()

    win.nudge_selected(1, 0, fine=False)
    assert f.scenePos().x() == pytest.approx(x0 + fp.SETTINGS["wall_snap_in"])


def test_nudge_ignores_non_movable_selection(fp, win, make_room):
    # a selected wall (not grouped) is not nudged
    sc = win.scene
    w = fp.WallItem(QPointF(0, 0), QPointF(100, 0), "interior")
    sc.addItem(w)
    w.setSelected(True)
    assert win.nudge_selected(1, 0, fine=False) is False
    assert w.p1.x() == pytest.approx(0)
