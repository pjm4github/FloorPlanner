"""Wall geometry plus door/window opening sizing and garage-door defaults."""
import pytest
from PyQt6.QtCore import QPointF

pytestmark = pytest.mark.walls


def test_wall_length_and_point_at(fp, scene):
    w = fp.WallItem(QPointF(0, 0), QPointF(100, 0), "interior")
    scene.addItem(w)
    assert w.length() == pytest.approx(100)
    pt = w.point_at(50)
    assert (pt.x(), pt.y()) == pytest.approx((50, 0))


def test_opening_size_from_code(fp, scene):
    w = fp.WallItem(QPointF(0, 0), QPointF(120, 0), "interior")
    scene.addItem(w)
    op = fp.OpeningItem(w, "door", "3280", 60)
    w.openings.append(op)
    w.rebuild()
    assert op.width == pytest.approx(32)
    assert op.height == pytest.approx(80)


def test_opening_wider_than_wall_rejected(fp, scene):
    w = fp.WallItem(QPointF(0, 0), QPointF(30, 0), "interior")
    scene.addItem(w)
    with pytest.raises(ValueError):
        fp.OpeningItem(w, "door", "3280", 15)   # 32" door on a 30" wall


def test_garage1_autosizes_to_single(fp, scene):
    w = fp.WallItem(QPointF(0, 0), QPointF(240, 0), "interior")  # 20'
    scene.addItem(w)
    op = fp.OpeningItem(w, "door", "2880", 120)
    w.openings.append(op)
    w.rebuild()
    op.set_door_type("GARAGE-1")
    assert op.width == pytest.approx(108)        # single garage door = 9'


def test_garage2_autosizes_to_double(fp, scene):
    w = fp.WallItem(QPointF(0, 0), QPointF(300, 0), "interior")  # 25'
    scene.addItem(w)
    op = fp.OpeningItem(w, "door", "2880", 150)
    w.openings.append(op)
    w.rebuild()
    op.set_door_type("GARAGE-2")
    assert op.width == pytest.approx(192)         # double garage door = 16'


def test_garage_keeps_size_when_wall_too_short(fp, scene):
    w = fp.WallItem(QPointF(0, 0), QPointF(100, 0), "interior")  # 8'4"
    scene.addItem(w)
    op = fp.OpeningItem(w, "door", "2880", 50)
    w.openings.append(op)
    w.rebuild()
    op.set_door_type("GARAGE-2")                  # 16' won't fit -> keep 28"
    assert op.width == pytest.approx(28)
