"""0279-report.md (Patrick: "go ahead with the wall and room drag hold,
repaint only on what changed").

1. THE ROOMS HOLD -- while a mouse button is down on the plan, the roof clip
   traces and the walls' roof-clip dashes take the floor's rooms as they
   were at the press; a roof recomputes only for its own geometry; the
   release repaints everything once.
2. REPAINT ONLY WHAT CHANGED -- the view runs MinimalViewportUpdate, which
   is only correct if every item paints inside its own boundingRect. The
   items the audit (docs/evidence/0275-drag-timing/bounds_audit.py) found
   painting outside it are pinned here: a furnishing's callout, a gate's
   swing, a roof's ridge callout.
"""
import pytest
from PyQt6.QtCore import QEvent, QPointF, Qt
from PyQt6.QtGui import QImage, QMouseEvent, QPainter, QPainterPath, QTransform
from PyQt6.QtWidgets import QApplication, QGraphicsView, QStyleOptionGraphicsItem

import floorplanner.roofs as R
from floorplanner.config import DEFAULT_FLOOR, SETTINGS
from floorplanner.roofs import RoofItem, hold_rooms, roof_clip_spans, roof_clip_trace, rooms_held
from floorplanner.rooms import RoomItem
from floorplanner.walls import OpeningItem, WallItem

pytestmark = pytest.mark.walls


def _room(scene, ceiling_in=96.0):
    path = QPainterPath()
    path.addRect(0, 0, 300, 200)
    room = RoomItem("Room", QPointF(150, 100), path, 100.0)
    room.floor = DEFAULT_FLOOR
    room.properties["ceiling_height_in"] = ceiling_in
    scene.addItem(room)
    return room


def _roof(scene, y=100.0):
    rf = RoofItem(QPointF(50, y), QPointF(250, y), eaves_h_in=80.0, ridge_h_in=132.0,
                  overhang_in=0.0, span_in=100.0)
    rf.floor = DEFAULT_FLOOR
    scene.addItem(rf)
    return rf


@pytest.fixture
def counted(monkeypatch):
    n = {"trace": 0}
    real = R.roof_clip_trace

    def counting(scene, roof):
        n["trace"] += 1
        return real(scene, roof)
    monkeypatch.setattr(R, "roof_clip_trace", counting)
    return n


# -- 1. the hold ---------------------------------------------------------------

def test_a_room_change_under_the_hold_does_not_recompute_the_trace(scene, counted):
    room = _room(scene)
    rf = _roof(scene)
    rf.clip_trace()
    base = counted["trace"]
    hold_rooms(scene, True)
    try:
        room.properties["ceiling_height_in"] = 110.0      # a room changes mid-gesture
        held = rf._drawn_trace()
        assert counted["trace"] == base, "the trace recomputed under the hold"
        rf.set_ridge(QPointF(50, 110), QPointF(250, 110))  # the roof's OWN geometry
        rf.clip_trace()
        assert counted["trace"] == base + 1, "the roof's own change must recompute"
    finally:
        hold_rooms(scene, False)
    assert not rooms_held(scene)
    after = rf.clip_trace()
    assert sorted((round(p.y(), 3), round(q.y(), 3)) for p, q in after) == \
        sorted((round(p.y(), 3), round(q.y(), 3)) for p, q in roof_clip_trace(scene, rf)), \
        "after the release the trace reads the rooms as they are"
    assert held is not None


def test_a_walls_dashes_hold_the_rooms_but_follow_their_own_line(scene):
    room = _room(scene)
    _roof(scene)
    w = WallItem(QPointF(150, 0), QPointF(150, 200), "interior")
    w.floor = DEFAULT_FLOOR
    scene.addItem(w)
    first = roof_clip_spans(scene, w)
    assert first
    hold_rooms(scene, True)
    try:
        room.properties["ceiling_height_in"] = 110.0
        assert roof_clip_spans(scene, w) == first, "held: the rooms as at the press"
    finally:
        hold_rooms(scene, False)
    assert roof_clip_spans(scene, w) != first, "released: the new ceiling counts"


def _send(win, etype, sp, button, buttons):
    vp = win.view.viewport()
    pos = win.view.mapFromScene(sp)
    QApplication.sendEvent(vp, QMouseEvent(etype, QPointF(pos), QPointF(vp.mapToGlobal(pos)),
                                           button, buttons, Qt.KeyboardModifier.NoModifier))


def test_a_left_press_on_the_plan_holds_and_its_release_lets_go(fp, win):
    win.prepare_headless()
    LEFT, NONE = Qt.MouseButton.LeftButton, Qt.MouseButton.NoButton
    _send(win, QEvent.Type.MouseButtonPress, QPointF(500, 500), LEFT, LEFT)
    assert rooms_held(win.scene)
    _send(win, QEvent.Type.MouseMove, QPointF(520, 510), NONE, LEFT)
    assert rooms_held(win.scene)
    _send(win, QEvent.Type.MouseButtonRelease, QPointF(520, 510), LEFT, NONE)
    assert not rooms_held(win.scene)


def test_a_hold_with_no_button_down_never_stalls_the_undo_record(fp, win, add_walls):
    """A release that went to a modal dialog never reaches the view; the
    settle walk lets such a hold go rather than wait for it forever."""
    add_walls(win.scene, 0, 0, 240, 180)
    hold_rooms(win.scene, True)
    calls = []
    real = win._commit_if_changed
    win._commit_if_changed = lambda: calls.append(1) or real()
    win._settle()
    assert calls == [1] and not rooms_held(win.scene)


# -- 2. repaint only what changed ------------------------------------------------

def test_the_view_repaints_only_what_changed(fp, win):
    assert win.view.viewportUpdateMode() == QGraphicsView.ViewportUpdateMode.MinimalViewportUpdate


def _ink_outside(item, zoom=1.0):
    """Pixels the item inks outside its own boundingRect, painted at `zoom`."""
    br = item.boundingRect()
    M = 80
    t = item.sceneTransform() * QTransform.fromScale(zoom, zoom)
    dev = t.mapRect(br)
    w, h = int(dev.width()) + 2 * M, int(dev.height()) + 2 * M
    img = QImage(w, h, QImage.Format.Format_ARGB32_Premultiplied)
    img.fill(0)
    p = QPainter(img)
    p.setTransform(t * QTransform.fromTranslate(M - dev.left(), M - dev.top()))
    item.paint(p, QStyleOptionGraphicsItem(), None)
    p.end()
    x0, y0, x1, y1 = M - 1, M - 1, M + int(dev.width()) + 1, M + int(dev.height()) + 1
    return sum(1 for y in range(h) for x in range(w)
               if not (x0 <= x <= x1 and y0 <= y <= y1) and (img.pixel(x, y) >> 24) & 0xFF)


def test_a_furnishings_callout_is_inside_its_box(fp, win, first_furnishing):
    SETTINGS["show_callouts"] = True
    f = fp.FurnishingItem(first_furnishing, QPointF(300, 300), 0)
    win.scene.addItem(f)
    assert _ink_outside(f) == 0


def test_a_gates_swing_is_inside_its_box(fp, win):
    w = WallItem(QPointF(0, 0), QPointF(300, 0), "fence")
    w.floor = DEFAULT_FLOOR
    win.scene.addItem(w)
    gate = OpeningItem(w, "gate", "4848", 150.0)
    w.openings.append(gate)
    w.rebuild()
    assert _ink_outside(gate) == 0
    assert _ink_outside(gate, zoom=3.0) == 0


def test_a_short_roofs_callout_is_inside_its_box(fp, win):
    SETTINGS["show_callouts"] = True
    rf = RoofItem(QPointF(100, 100), QPointF(112, 100), eaves_h_in=96.0, ridge_h_in=110.0,
                  overhang_in=0.0, span_in=[60.0, 0.0], form="shed")
    rf.floor = DEFAULT_FLOOR
    win.scene.addItem(rf)
    assert _ink_outside(rf) == 0


def test_the_painted_plan_lines_are_cached_and_follow_the_roof(scene):
    rf = _roof(scene)
    first = rf._painted_plan_lines(False)
    assert rf._painted_plan_lines(False) is first, "unchanged: the same answer, not recomputed"
    rf.set_ridge(QPointF(50, 120), QPointF(250, 120))
    moved = rf._painted_plan_lines(False)
    assert moved is not first
    assert [(k, [(round(p.y()), round(q.y())) for p, q in s]) for k, s in moved] == \
        [(k, [(round(p.y()), round(q.y()))]) for k, p, q in rf._plan_lines()]
