"""P4.2 extract / join — rooms as durable movable units.

The acceptance run, exactly as the task line states it: extract -> move
500" -> join at a new location, with check() clean at EVERY step, I12
holding while floating, and furnishings and openings intact throughout.
Plus the round-trip half of mini-gate item 8: a design saved while a room
floats reloads still floating.
"""
import warnings

import pytest
from PyQt6.QtCore import QPointF

import FloorPlanner as fp
from floorplanner.design.bridge import design_from_scene
from floorplanner.design.validate import check

pytestmark = pytest.mark.rooms


def _walk(source):
    """`design_from_scene` as a dict, weld warning silenced (the tests
    assert through check(), not the warning channel)."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return design_from_scene(source).to_dict()


def _clean(win, label):
    errs = check(_walk(win.scene), deep=True)
    assert errs == [], f"check() not clean {label}: {errs}"


def _make(scene, x, y, w, h, name, skip=None):
    corners = [QPointF(x, y), QPointF(x + w, y),
               QPointF(x + w, y + h), QPointF(x, y + h)]
    for i in range(4):
        a, b = corners[i], corners[(i + 1) % 4]
        if skip and any((a == s[0] and b == s[1]) or (a == s[1] and b == s[0])
                        for s in skip):
            continue
        scene.addItem(fp.WallItem(a, b, "interior"))
    fp.rebuild_all_walls(scene)
    centre = QPointF(x + w / 2, y + h / 2)
    res = fp.detect_room(scene, centre)
    assert res is not None
    room = fp.RoomItem(fp.unique_room_name(scene, name), centre,
                       res[0], res[1], corners=res[2])
    scene.addItem(room)
    fp.bind_room_walls(scene, room)
    return room


def _vertex_ids(room):
    out = {id(e.v) for e in room.outline}
    for w in room.walls:
        out.add(id(w.end_vertex("p1")))
        out.add(id(w.end_vertex("p2")))
    return out


def test_extract_move_join_acceptance(win, first_furnishing):
    sc = win.scene
    a = _make(sc, 0, 0, 144, 120, "Den")
    b = _make(sc, 144, 0, 120, 120, "Kitchen",
              skip=[(QPointF(144, 0), QPointF(144, 120))])
    shared = next(w for w in sc.items() if isinstance(w, fp.WallItem)
                  and abs(w.p1.x() - 144) < 0.5 and abs(w.p2.x() - 144) < 0.5)
    assert {r.name for r in shared.rooms} == {"Den", "Kitchen"}
    door = fp.OpeningItem(shared, "door", "3280", 60.0)
    shared.openings.append(door)
    shared.rebuild()
    furn = fp.FurnishingItem(first_furnishing, QPointF(48, 48), 0)
    sc.addItem(furn)
    fp.rebuild_all_walls(sc)
    area_a, area_b = a.area_sqft, b.area_sqft
    _clean(win, "before extract")

    # -- extract: placed -> floating; the plan keeps every wall it had
    fp.extract_room(sc, a)
    assert a.placement_state == "floating"
    assert a.extracted_from == a.floor
    assert shared.scene() is sc, "the neighbour lost its party wall"
    assert {r.name for r in shared.rooms} == {"Kitchen"}
    assert len(a.walls) == 4 and len(a.open_edges()) == 0
    # I12 by construction: no vertex of the floating room is the plan's
    plan_vids = set()
    a_walls = set(a.walls)
    for w in sc.items():
        if isinstance(w, fp.WallItem) and w not in a_walls:
            plan_vids.add(id(w.end_vertex("p1")))
            plan_vids.add(id(w.end_vertex("p2")))
    assert not (_vertex_ids(a) & plan_vids), "floating room shares a vertex"
    assert a.area_sqft == pytest.approx(area_a)
    _clean(win, "after extract (I12 is in the always-on set)")

    # -- move 500": walls, door and furnishing ride as one closed unit
    fc = QPointF(furn.sceneBoundingRect().center())
    a._translate(500.0, 0.0)
    assert a.area_sqft == pytest.approx(area_a)
    assert b.area_sqft == pytest.approx(area_b)
    moved_fc = furn.sceneBoundingRect().center()
    assert moved_fc.x() - fc.x() == pytest.approx(500.0, abs=0.01)
    a_door = [op for w in a.walls for op in w.openings]
    assert len(a_door) == 1 and a_door[0].kind == "door"
    _clean(win, "while floating, 500 in away")

    # -- join at the new location: placed again, clean, nothing dragged back
    fp.join_room(sc, a)
    assert a.placement_state == "placed"
    assert a.extracted_from is None
    assert a.area_sqft == pytest.approx(area_a)
    assert len([op for w in a.walls for op in w.openings]) == 1
    _clean(win, "after join at the new location")


def test_extract_then_rejoin_at_origin_restores_the_party_wall(win):
    # the inverse trip: extract off a party wall, come straight back, join --
    # the private copy fuses with the plan wall (openings dedup) and the
    # room is bound to the SHARED wall again, wall count back to the start
    sc = win.scene
    a = _make(sc, 0, 0, 144, 120, "Den")
    b = _make(sc, 144, 0, 120, 120, "Kitchen",
              skip=[(QPointF(144, 0), QPointF(144, 120))])
    walls_before = sum(isinstance(i, fp.WallItem) for i in sc.items())
    area_a = a.area_sqft
    fp.extract_room(sc, a)
    a._translate(500.0, 0.0)
    a._translate(-500.0, 0.0)
    fp.join_room(sc, a)
    assert a.placement_state == "placed"
    assert a.area_sqft == pytest.approx(area_a)
    assert sum(isinstance(i, fp.WallItem) for i in sc.items()) == walls_before
    shared = [w for w in sc.items() if isinstance(w, fp.WallItem)
              and abs(w.p1.x() - 144) < 0.5 and abs(w.p2.x() - 144) < 0.5]
    assert len(shared) == 1, "party wall did not fuse back to one"
    assert {r.name for r in shared[0].rooms} == {"Den", "Kitchen"}
    assert b.area_sqft == pytest.approx(100.0)
    _clean(win, "after the round trip home")


def test_floating_room_saves_and_reloads_floating(win):
    # mini-gate item 8's headless half: placement round-trips through the
    # document now that it is modelled on the item (stash retired)
    sc = win.scene
    a = _make(sc, 0, 0, 144, 120, "Den")
    fp.extract_room(sc, a)
    doc = win.design_document()
    rooms = doc.get("rooms", [])
    assert [r["placement"]["state"] for r in rooms] == ["floating"]
    assert rooms[0]["placement"]["extracted_from"] is not None
    win.load_data(doc)
    a2 = next(r for r in win.scene.items() if isinstance(r, fp.RoomItem))
    assert a2.placement_state == "floating"
    assert a2.extracted_from is not None
    _clean(win, "after reload while floating")
    # and joining after the reload still works
    fp.join_room(win.scene, a2)
    assert a2.placement_state == "placed"
    _clean(win, "after join following reload")


@pytest.mark.gui
def test_five_room_macro_round_trip_leaves_no_open_edges(win):
    # Patrick's fiveRoomTest reproduction, pinned VERBATIM: replay his
    # recorded macro (label-drag R1 out to empty canvas, release, drag it
    # back home) and the plan must come back whole. Pre-fix, the join's
    # merge forced the returning room's wall COPY as survivor, absorbing the
    # original party wall that R2/R3's outlines still named -- so both
    # painted their shared edge as a dashed open edge over a wall that was
    # right there ("it leaves a wall behind"). rebind_dead_edges is the fix.
    import pathlib
    ex = pathlib.Path(__file__).resolve().parent.parent / "examples"
    win.resize(1400, 1000)
    win.show()
    win.load_path(str(ex / "fiveRoomTest.json"))
    win.zoom_fit()
    for line in (ex / "fiveRoomTestMacro.fpm").read_text().splitlines():
        if line.strip():
            res = win.run_macro(line)
            assert res["ok"], res
    sc = win.scene
    rooms = sorted((r for r in sc.items() if isinstance(r, fp.RoomItem)),
                   key=lambda r: r.name)
    walls = [w for w in sc.items() if isinstance(w, fp.WallItem)]
    assert len(walls) == 16, f"wall count {len(walls)} after the round trip"
    assert not [w for w in walls if min(w.p1.x(), w.p2.x()) > 850], \
        "a wall was left behind at the drop zone"
    for r in rooms:
        assert r.placement_state == "placed", f"{r.name} not placed"
        assert len(r.open_edges()) == 0, \
            f"{r.name} has a dashed open edge after the round trip"
    r1 = next(r for r in rooms if r.name == "R1")
    assert r1.area_sqft == pytest.approx(149.8, abs=0.5)


@pytest.mark.gui
def test_drag_split_macro_keeps_every_room_rectilinear(win):
    # Patrick's fiveRoomDragSplit macro, pinned VERBATIM -- the finding-5
    # cascade: (a) the join merged at the 6" auto-coalesce tolerance, so a
    # room dropped a gesture-width off SNAPPED its neighbours' walls onto
    # its own line (R4's north wall physically moved 6"); (b) an outline
    # edge named by a wall that only partly covers it was a latent tear the
    # next drag turned diagonal (split_partially_covered_edges); (c) the
    # tee gather tested body-landings against SELF only, so a corner
    # resting mid-span of another RUN member was left floating when the
    # line slid. After every macro line: nothing diagonal anywhere, and no
    # edge names a wall that does not span it.
    import pathlib
    from floorplanner.rooms import _wall_spans_segment
    ex = pathlib.Path(__file__).resolve().parent.parent / "examples"
    win.resize(1400, 1000)
    win.show()
    win.load_path(str(ex / "fiveRoomTest.json"))
    win.zoom_fit()
    for ln, line in enumerate(
            (ex / "fiveRoomDragSplit.fpm").read_text().splitlines(), 1):
        if not line.strip():
            continue
        res = win.run_macro(line)
        assert res["ok"], res
        for r in (x for x in win.scene.items()
                  if isinstance(x, fp.RoomItem)):
            pts = r.corners or []
            n = len(pts)
            for i in range(n):
                a, b = pts[i], pts[(i + 1) % n]
                assert (abs(a.x() - b.x()) < 0.5
                        or abs(a.y() - b.y()) < 0.5), (
                    f"line {ln}: {r.name} tore diagonal "
                    f"({a.x():.1f},{a.y():.1f})->({b.x():.1f},{b.y():.1f})")
            for i, e in enumerate(r.outline):
                if e.wall is not None and e.wall.scene() is not None:
                    assert _wall_spans_segment(e.wall, pts[i],
                                               pts[(i + 1) % n]), (
                        f"line {ln}: {r.name} edge names a wall that does "
                        f"not span it -- a latent tear")
