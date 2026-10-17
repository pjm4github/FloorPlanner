"""0281-report.md (Patrick: "go ahead with undo steps 1 and 2"; his Ctrl+Z
took 3 s on wiscaway2026-10-13R1.json).

Undo reloads the whole document as NEW objects. The reload recomposed every
roof's clip (~950 ms of ~1.7 s) and threw away every roof's clip trace, though
an edit to a wall, room, opening or furnishing changes no roof. Both are now
kept BY VALUE: the compose against the roofs' own geometry and elevations,
the trace against the roof's geometry and the floor's rooms' coordinates.

The receipts are about the keys: the same roofs reuse, a changed roof, a
changed elevation or a changed room recomputes, and nothing is ever wrong.
"""
import pytest
from PyQt6.QtCore import QPointF
from PyQt6.QtGui import QPainterPath

import floorplanner.roofs as R
from floorplanner.config import DEFAULT_FLOOR
from floorplanner.roofs import RoofItem, roof_clip_trace, sync_roof_clips
from floorplanner.rooms import RoomItem

pytestmark = pytest.mark.walls


def _roofs(scene):
    a = RoofItem(QPointF(0, 100), QPointF(400, 100), span_in=[100.0, 100.0])
    b = RoofItem(QPointF(200, -50), QPointF(200, 250), span_in=[80.0, 80.0],
                 eaves_h_in=96.0, ridge_h_in=120.0)
    for rf in (a, b):
        rf.floor = DEFAULT_FLOOR
        scene.addItem(rf)
    return a, b


def _sig(scene):
    out = {}
    for it in scene.items():
        if isinstance(it, RoofItem):
            r = it._clip_region
            out[it.geometry_key()] = (None if r is None else round(r.area(), 3)
                                      if hasattr(r, "area") else repr(type(r)),
                                      sorted((round(p.x(), 3), round(p.y(), 3), round(q.x(), 3), round(q.y(), 3))
                                             for p, q in it._seams))
    return out


@pytest.fixture
def composes(monkeypatch):
    n = {"compose": 0, "trace": 0}
    real_c, real_t = R.compose_building, R.roof_clip_trace

    def c(*a, **k):
        n["compose"] += 1
        return real_c(*a, **k)

    def t(*a, **k):
        n["trace"] += 1
        return real_t(*a, **k)
    monkeypatch.setattr(R, "compose_building", c)
    monkeypatch.setattr(R, "roof_clip_trace", t)
    return n


def test_the_same_roofs_as_new_objects_reuse_the_compose(scene, composes):
    a, b = _roofs(scene)
    sync_roof_clips(scene)
    before = _sig(scene)
    assert any(v[1] for v in before.values()), "the two roofs meet in a seam"
    base = composes["compose"]
    # a reload, as `load_data` does it -- under the hold: the same roofs as
    # new objects
    R.hold_roof_clips(scene, True)
    for rf in (a, b):
        scene.removeItem(rf)
    _roofs(scene)
    R.hold_roof_clips(scene, False)
    assert composes["compose"] == base, "the same roofs recomposed"
    assert _sig(scene) == before, "and the reused clips are the right ones"


def test_a_changed_roof_or_elevation_recomposes(fp, scene, composes, monkeypatch):
    a, b = _roofs(scene)
    sync_roof_clips(scene)
    base = composes["compose"]
    b.set_ridge(QPointF(220, -50), QPointF(220, 250))          # a roof moves
    sync_roof_clips(scene)
    assert composes["compose"] > base
    base = composes["compose"]
    monkeypatch.setattr(R, "floor_elevation", lambda floor: 96.0)   # its level rises
    sync_roof_clips(scene)
    assert composes["compose"] > base


def test_two_identical_roofs_are_never_cached(scene, composes):
    for _ in range(2):
        rf = RoofItem(QPointF(0, 100), QPointF(400, 100), span_in=[100.0, 100.0])
        rf.floor = DEFAULT_FLOOR
        scene.addItem(rf)
    sync_roof_clips(scene)
    base = composes["compose"]
    sync_roof_clips(scene)
    assert composes["compose"] == base + 1, "a twin would make the value key ambiguous"


def _room(scene, ceiling_in=96.0):
    path = QPainterPath()
    path.addRect(0, 0, 300, 200)
    room = RoomItem("Room", QPointF(150, 100), path, 100.0)
    room.floor = DEFAULT_FLOOR
    room.properties["ceiling_height_in"] = ceiling_in
    scene.addItem(room)
    return room


def _trace_roof(scene):
    rf = RoofItem(QPointF(50, 100), QPointF(250, 100), eaves_h_in=80.0, ridge_h_in=132.0,
                  overhang_in=0.0, span_in=100.0)
    rf.floor = DEFAULT_FLOOR
    scene.addItem(rf)
    return rf


def _rounded(segs):
    return sorted(((round(p.x(), 3), round(p.y(), 3)), (round(q.x(), 3), round(q.y(), 3))) for p, q in segs)


def test_a_reloaded_roof_over_the_same_rooms_reuses_its_trace(scene, composes):
    room = _room(scene)
    rf = _trace_roof(scene)
    first = rf.clip_trace()
    assert first
    base = composes["trace"]
    scene.removeItem(rf)
    scene.removeItem(room)
    _room(scene)                                  # the same room, a new object
    rf2 = _trace_roof(scene)                      # the same roof, a new object
    assert _rounded(rf2.clip_trace()) == _rounded(first)
    assert composes["trace"] == base, "recomputed though nothing changed"


def test_a_changed_room_still_recomputes_the_trace(scene, composes):
    room = _room(scene)
    rf = _trace_roof(scene)
    rf.clip_trace()
    base = composes["trace"]
    room.properties["ceiling_height_in"] = 110.0
    got = rf.clip_trace()
    assert composes["trace"] == base + 1
    assert _rounded(got) == _rounded(roof_clip_trace(scene, rf))


def test_undo_of_a_wall_edit_reuses_the_roofs(fp, win, add_walls, composes):
    """End to end: a plan with roofs, a wall edit settled, Ctrl+Z -- the
    restored roofs are not recomposed, and their clips are what a fresh
    compose gives."""
    add_walls(win.scene, 0, 0, 400, 300)
    _roofs(win.scene)
    sync_roof_clips(win.scene)
    win._commit_if_changed()
    w = next(it for it in win.scene.items() if isinstance(it, fp.WallItem))
    w.openings.append(fp.OpeningItem(w, "window", "3648", w.length() / 2))
    w.rebuild()
    win._commit_if_changed()
    assert win._undo_stack, "the edit is on the undo stack"
    base = composes["compose"]
    win.undo()
    assert composes["compose"] == base, "the undo recomposed unchanged roofs"
    kept = _sig(win.scene)
    win.scene._compose_memo = None
    sync_roof_clips(win.scene)
    assert _sig(win.scene) == kept, "the reused clips equal a fresh compose"
