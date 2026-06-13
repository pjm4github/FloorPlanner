"""Wall geometry plus door/window opening sizing and garage-door defaults."""
import pytest
from PyQt6.QtCore import QPointF, Qt

pytestmark = pytest.mark.walls

NOMOD = Qt.KeyboardModifier.NoModifier


def _draw_end(fp, win, p1, drag_to):
    """End point of a wall drawn from p1 toward drag_to (no modifiers)."""
    temp = fp.WallItem(QPointF(*p1), QPointF(*p1), "interior")
    return win.view._wall_end_point(temp, QPointF(*drag_to), NOMOD)


def test_wall_draw_aligns_end_to_orthogonal_wall(fp, win):
    sc = win.scene
    sc.addItem(fp.WallItem(QPointF(300, 0), QPointF(300, 200), "interior"))
    fp.rebuild_all_walls(sc)
    end = _draw_end(fp, win, (0, 102), (291, 108))
    assert end.x() == pytest.approx(300)   # x lines up with the vertical wall
    assert end.y() == pytest.approx(102)   # stays horizontal


def test_wall_draw_stays_orthogonal_not_diagonal(fp, win):
    sc = win.scene
    sc.addItem(fp.WallItem(QPointF(300, 0), QPointF(300, 200), "interior"))
    fp.rebuild_all_walls(sc)
    # drag toward the wall's off-axis bottom endpoint (300, 200)
    end = _draw_end(fp, win, (0, 100), (305, 195))
    assert end.y() == pytest.approx(100)   # not pulled diagonally to 200
    assert end.x() == pytest.approx(300)


def test_wall_draw_leaves_gap_when_not_meeting(fp, win):
    sc = win.scene
    sc.addItem(fp.WallItem(QPointF(300, 0), QPointF(300, 200), "interior"))
    fp.rebuild_all_walls(sc)
    # y is past the vertical wall's extent -> aligned x, but a gap remains
    end = _draw_end(fp, win, (0, 300), (291, 305))
    assert (end.x(), end.y()) == pytest.approx((300, 300))


def test_wall_draw_orthogonal_far_from_walls(fp, win):
    end = _draw_end(fp, win, (0, 500), (250, 540))
    assert end.y() == pytest.approx(500)   # horizontal, no off-axis pull


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


def test_window_bounding_rect_is_tight(fp, scene):
    # a wide opening must not inflate its bounding rect perpendicular to the
    # wall (that used to balloon any enclosing group's selection box)
    w = fp.WallItem(QPointF(0, 0), QPointF(120, 0), "interior")
    scene.addItem(w)
    op = fp.OpeningItem(w, "window", "9648", 60)     # 96" wide window
    w.openings.append(op)
    w.rebuild()
    br = op.boundingRect()
    assert br.height() < 60                # ~ wall thickness + pad, not ~228


def test_door_swing_stays_within_bounding_rect(fp, scene):
    w = fp.WallItem(QPointF(0, 0), QPointF(120, 0), "interior")
    scene.addItem(w)
    op = fp.OpeningItem(w, "door", "3280", 60)       # 32" LH door
    op.swing = -1
    w.openings.append(op)
    w.rebuild()
    br = op.boundingRect()
    # the quarter-circle swing reaches ~width on the swing side; the rect
    # must still cover it
    assert br.top() <= -op.width


def test_garage_keeps_size_when_wall_too_short(fp, scene):
    w = fp.WallItem(QPointF(0, 0), QPointF(100, 0), "interior")  # 8'4"
    scene.addItem(w)
    op = fp.OpeningItem(w, "door", "2880", 50)
    w.openings.append(op)
    w.rebuild()
    op.set_door_type("GARAGE-2")                  # 16' won't fit -> keep 28"
    assert op.width == pytest.approx(28)
