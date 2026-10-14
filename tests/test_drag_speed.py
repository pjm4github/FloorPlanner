"""0276-report.md (0275's steps 1-3, on Patrick's word "Go ahead with steps
1 to 3"): a drag on his two-floor plan ran at 3 frames a second because
every paint of every roof recomputed its clip trace from scratch (27 ms a
roof), and the 180 ms settle walk then fired inside every move.

The fix is a cache, so the receipts are about the cache's KEY: nothing the
trace or a wall's dashes read may change without the cached answer
changing too (a stale dash is the failure a cache invites), and nothing
they do not read may make them recompute (the failure the cache exists to
prevent). Plus the settle walk's hold.
"""
import pytest
from PyQt6.QtCore import QPointF
from PyQt6.QtGui import QPainterPath

import floorplanner.roofs as R
from floorplanner.config import DEFAULT_FLOOR
from floorplanner.roofs import RoofItem, hold_roof_clips, roof_clip_spans, roof_clip_trace
from floorplanner.rooms import RoomItem
from floorplanner.walls import WallItem

pytestmark = pytest.mark.walls


def _rounded(segs, nd=3):
    return sorted(((round(p.x(), nd), round(p.y(), nd)),
                   (round(q.x(), nd), round(q.y(), nd))) for p, q in segs)


def _room(scene, x0=0.0, x1=300.0, ceiling_in=96.0):
    path = QPainterPath()
    path.addRect(x0, 0, x1 - x0, 200)
    room = RoomItem("Room", QPointF((x0 + x1) / 2.0, 100), path, 100.0)
    room.floor = DEFAULT_FLOOR
    room.properties["ceiling_height_in"] = ceiling_in
    scene.addItem(room)
    return room


def _roof(scene, y=100.0, x0=50.0, x1=250.0):
    rf = RoofItem(QPointF(x0, y), QPointF(x1, y), eaves_h_in=80.0, ridge_h_in=132.0,
                  overhang_in=0.0, span_in=100.0)
    rf.floor = DEFAULT_FLOOR
    scene.addItem(rf)
    return rf


@pytest.fixture
def counted(monkeypatch):
    """Count the real computations behind the cache."""
    n = {"trace": 0}
    real = R.roof_clip_trace

    def counting(scene, roof):
        n["trace"] += 1
        return real(scene, roof)
    monkeypatch.setattr(R, "roof_clip_trace", counting)
    return n


def test_the_cached_trace_is_the_computed_trace(scene):
    _room(scene)
    rf = _roof(scene)
    assert rf.clip_trace(), "the fixture has a trace"
    assert _rounded(rf.clip_trace()) == _rounded(roof_clip_trace(scene, rf))
    assert _rounded(rf._drawn_trace()) == _rounded(roof_clip_trace(scene, rf))


def test_paint_after_paint_does_not_recompute_the_trace(scene, counted):
    """The measured fault: a repaint with nothing changed ran the whole
    trace again for every roof. Now it runs once per change."""
    _room(scene)
    rf = _roof(scene)
    rf.clip_trace()
    base = counted["trace"]
    for _ in range(5):
        rf._drawn_trace()
    assert counted["trace"] == base


def test_another_roofs_drag_leaves_this_roofs_trace_cached(scene, counted):
    """In a drag only the dragged roof's geometry changes; the others'
    traces read nothing that moved."""
    _room(scene)
    still = _roof(scene, y=60.0)
    moving = _roof(scene, y=140.0)
    hold_roof_clips(scene, True)                     # as a grip drag does
    still.clip_trace()
    moving.clip_trace()
    base = counted["trace"]
    moving.set_ridge(QPointF(50, 150), QPointF(250, 150))
    still.clip_trace()
    assert counted["trace"] == base, "the still roof recomputed"
    moving.clip_trace()
    assert counted["trace"] == base + 1, "the moved roof did not"
    hold_roof_clips(scene, False)


def test_a_room_change_reaches_the_cached_trace(scene):
    """R5a's own worry: rooms change without the roof hearing about it.
    The key compares them -- a new ceiling, a new region -- so the cached
    trace is never the stale one."""
    room = _room(scene, ceiling_in=96.0)
    rf = _roof(scene)
    before = _rounded(rf.clip_trace())
    room.properties["ceiling_height_in"] = 110.0
    after = _rounded(rf.clip_trace())
    assert after != before
    assert after == _rounded(roof_clip_trace(scene, rf))
    path = QPainterPath()
    path.addRect(0, 0, 150, 200)                     # the room halves
    room.set_region(path, 50.0)
    assert _rounded(rf.clip_trace()) == _rounded(roof_clip_trace(scene, rf))
    assert _rounded(rf.clip_trace()) != after


def test_a_moved_corner_reaches_the_cached_trace(fp, scene, make_room):
    """A room with an outline: a wall slide relocates its corner vertices
    (new `Vertex` objects), which the key holds by identity."""
    room = make_room(scene, 0, 0, 300, 200, "Den")
    room.properties["ceiling_height_in"] = 110.0     # not the default: the vacated strip differs
    rf = _roof(scene)
    before = _rounded(rf.clip_trace())
    east = next(w for w in scene.items() if isinstance(w, WallItem)
                and abs(w.p1.x() - 300) < 1 and abs(w.p2.x() - 300) < 1)
    from floorplanner.rooms import relocate_corners
    moved = relocate_corners([east], [room],
                             lambda v: QPointF(v.x - 60.0, v.y), scene)
    assert moved >= 2, "the east wall's corners moved"
    fp.rebuild_all_walls(scene)
    assert _rounded(rf.clip_trace()) == _rounded(roof_clip_trace(scene, rf))
    assert _rounded(rf.clip_trace()) != before


def test_a_walls_dashes_follow_a_roof_and_a_room(scene):
    """The wall's roof-clip dashes, cached the same way: a roof's new
    height, then a room's new ceiling, each reaches them."""
    room = _room(scene)
    rf = _roof(scene)
    w = WallItem(QPointF(150, 0), QPointF(150, 200), "interior")   # under the ridge
    w.floor = DEFAULT_FLOOR
    scene.addItem(w)
    first = roof_clip_spans(scene, w)
    assert first, "the fixture's wall is clipped"
    assert first == roof_clip_spans(scene, w), "the cache answers the same"
    rf.ridge_h_in = 120.0                                   # the roof drops
    rf.rebuild()
    lower = roof_clip_spans(scene, w)
    assert lower != first
    room.properties["ceiling_height_in"] = 110.0           # the ceiling rises
    assert roof_clip_spans(scene, w) != lower


def test_the_settle_walk_waits_for_a_roof_gesture(fp, win):
    """0275: the 180 ms debounce fired inside every move of a slow drag and
    filed a mid-gesture snapshot. While a roof gesture holds the clips the
    timer's slot defers; once released it commits."""
    calls = []
    real = win._commit_if_changed
    win._commit_if_changed = lambda: calls.append(1) or real()
    hold_roof_clips(win.scene, True)
    try:
        win._settle()
        assert calls == [] and win._dirty_timer.isActive(), "it re-arms instead"
    finally:
        hold_roof_clips(win.scene, False)
    win._dirty_timer.stop()
    win._settle()
    assert calls == [1]


def test_a_settle_walk_with_nothing_changed_does_not_rearm_itself(fp, win, add_walls, qapp):
    """0276, measured: the settle walk repainted the callouts after every
    walk; the repaint emitted scene.changed, which re-armed the settle
    timer -- a document walk and a full repaint every ~280 ms, forever,
    idle. Now it repaints only when a stamped id changed, so a walk over
    an unchanged plan leaves the timer quiet."""
    from floorplanner.config import SETTINGS
    assert SETTINGS.get("show_callouts", True), "the loop needed the callouts on"
    add_walls(win.scene, 0, 0, 240, 180)
    win._commit_if_changed()                 # the first walk stamps the ids
    qapp.processEvents()
    win._dirty_timer.stop()
    win._commit_if_changed()                 # nothing changed since
    qapp.processEvents()                     # scene.changed is delivered here
    assert not win._dirty_timer.isActive(), "the walk re-armed its own timer"
