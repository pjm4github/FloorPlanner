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
