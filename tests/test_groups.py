"""Group / move / ungroup behaviour, including two regressions:

1. Dragging a *grouped wall* used to run WallItem's slide + join logic on a
   group child, deleting walls on ungroup (the gui test below).
2. dissolve()'s removeFromGroup() handed item ownership back to Python; with
   no external reference the walls were garbage-collected out of the scene on
   ungroup. test_*_survives_gc forces a collection to lock this down."""
import gc
import math

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


def test_grouping_a_room_duplicates_its_walls(fp, win, make_room, counts):
    # selecting a ROOM and grouping duplicates its walls into the group; the
    # original room keeps its own walls (the group is a movable copy)
    sc = win.scene
    room = make_room(sc, 0, 0, 144, 120, "Den")
    n_walls_before = sum(isinstance(i, fp.WallItem) for i in sc.items())
    orig_walls = list(room.walls)
    sc.clearSelection()
    room.setSelected(True)
    win.group_selected()
    g = next(i for i in sc.items() if isinstance(i, fp.GroupItem))
    grouped = [c for c in g.childItems() if isinstance(c, fp.WallItem)]
    assert len(grouped) >= 4                       # the room's 4 walls copied
    # walls doubled (originals + grouped copies); originals still owned by room
    assert sum(isinstance(i, fp.WallItem) for i in sc.items()) >= \
        n_walls_before + 4
    assert all(w in room.walls for w in orig_walls)
    assert all(w.group() is None for w in orig_walls)


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


def test_bake_carries_room_without_traced_corners(fp, win, make_room):
    # regression: a room with no perimeter corners (grid-detected / imported /
    # non-rectilinear) used to be left behind by bake() -- walls_cover_room
    # bailed out on corners is None -- so its region, label anchor and area
    # stayed put while its own walls moved with the group. Group the room AND
    # its walls, drop the corners, then move: the room must ride along and
    # re-detect at the new spot.
    sc = win.scene
    room = make_room(sc, 0, 0, 144, 120, "Den")
    room.corners = None                       # simulate a corner-less room
    # (P3.2 deleted _sync_corner_props: clearing corners now clears the outline,
    # so there is no mirror left to re-sync)
    room._detect_sig = None
    sc.clearSelection()
    room.setSelected(True)
    for w in list(room.walls):
        w.setSelected(True)                   # walls + room grouped together
    win.group_selected()
    g = next(i for i in sc.items() if isinstance(i, fp.GroupItem))
    g.setPos(200, 100)
    g.bake()
    br = room.path.boundingRect()
    assert br.x() == pytest.approx(203, abs=6)          # region followed +200
    assert br.y() == pytest.approx(103, abs=6)          # region followed +100
    assert room.anchor.x() == pytest.approx(272, abs=6)  # label anchor moved
    assert room.anchor.y() == pytest.approx(160, abs=6)
    assert room.area_sqft == pytest.approx(120.0, abs=1)  # area re-detected
    # every wall the room now owns sits at the moved location, not the old one
    assert all(w.p1.x() >= 180 and w.p1.y() >= 80 for w in room.walls)


def _built_walls(fp, sc):
    return sum(isinstance(w, fp.WallItem) for w in sc.items())


def test_grouping_room_with_its_walls_makes_no_coincident_copies(fp, win,
                                                                 make_room):
    # regression (wall leak): selecting a room together with its own walls used
    # to duplicate EVERY edge -- the group carried the 4 originals AND 4
    # coincident copies (8 walls), which only merged away on ungroup. The room's
    # own selected walls must ride in as themselves, so the count stays 4.
    sc = win.scene
    room = make_room(sc, 0, 0, 144, 120, "Den")
    assert _built_walls(fp, sc) == 4
    sc.clearSelection()
    room.setSelected(True)
    for w in list(room.walls):
        w.setSelected(True)
    win.group_selected()
    assert _built_walls(fp, sc) == 4          # no coincident duplicates
    g = next(i for i in sc.items() if isinstance(i, fp.GroupItem))
    g.setPos(120, 0)
    g.bake()
    assert _built_walls(fp, sc) == 4          # still 4 after the move
    assert room.path.boundingRect().x() == pytest.approx(123, abs=6)  # room rode


def test_group_move_room_only_does_not_orphan_walls(fp, win, make_room):
    # regression (wall leak): grouping a room ALONE makes a movable copy (the
    # original stays). bake() used to move the ORIGINAL room onto the coincident
    # copies via walls_cover_room's loop-coverage path, abandoning the room's
    # own walls -- so orphans piled up every group/move/ungroup cycle
    # (4 -> 6 -> 7 -> 8...). Now the original stays put and only the copy moves,
    # so repeated cycles are stable.
    sc = win.scene
    make_room(sc, 0, 0, 144, 120, "Den")
    counts = []
    for _ in range(4):
        room = next(r for r in sc.items() if isinstance(r, fp.RoomItem))
        sc.clearSelection()
        room.setSelected(True)               # room ONLY -> walls duplicated
        win.group_selected()
        g = next(it for it in sc.items() if isinstance(it, fp.GroupItem))
        g.setPos(0, 300)                     # move the copy clear of the original
        g.bake()
        sc.clearSelection()
        g.setSelected(True)
        win.ungroup_selected()
        counts.append(_built_walls(fp, sc))
    # stable across cycles (original 4 + one persistent copy) -- not compounding
    assert counts[1:] == counts[:-1], counts
    assert sum(isinstance(r, fp.RoomItem) for r in sc.items()) == 1


# xfail carried as a Known regression (V5_MIGRATION_PLAN): P0.5 fix 4 made
# select_in_rect read-only, removing the accidental "extract" it performed
# (synthesise the party-wall edge + rebuild rebinds the room to that private
# copy, so bake's room_owns_walls could carry it). The rubber-band-then-move
# route to this workflow is gone until P4.2 rebuilds extract as a real
# operation; P4.2's acceptance flips this back to a hard pass. (Dragging the
# room by its label still works today via _privatize_shared_walls.)
@pytest.mark.xfail(reason="rubber-band extract removed at P0.5 fix 4; real "
                          "extract restores it at P4.2", strict=False)
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


def _group_room_with_furnishing(fp, win, make_room, first_furnishing):
    sc = win.scene
    make_room(sc, 0, 0, 144, 72, "Den")        # wide room
    sc.addItem(fp.FurnishingItem(first_furnishing, QPointF(72, 36), 0))
    for it in list(sc.items()):
        if isinstance(it, (fp.WallItem, fp.FurnishingItem)):
            it.setSelected(True)
    win.group_selected()
    return next(i for i in sc.items() if isinstance(i, fp.GroupItem))


def test_group_rotation_turns_members_about_centre(fp, win, make_room,
                                                   first_furnishing):
    sc = win.scene
    g = _group_room_with_furnishing(fp, win, make_room, first_furnishing)
    furn = next(c for c in g.childItems() if isinstance(c, fp.FurnishingItem))
    box0 = g.childrenBoundingRect()
    c = box0.center()
    g._begin_rotation(QPointF(c.x() + 100, c.y()))         # start angle 0
    g._apply_rotation(QPointF(c.x(), c.y() + 100), False)  # end angle 90
    g._finish_rotation()

    assert furn.rotation() == pytest.approx(90, abs=1)
    box1 = g.childrenBoundingRect()
    assert box0.width() > box0.height()        # was wide
    assert box1.height() > box1.width()        # now tall (quarter turn)
    room = next(r for r in sc.items() if isinstance(r, fp.RoomItem))
    assert room.corners is not None            # region rotated with it


def test_grouped_furnishing_hides_its_own_handle(fp, win, make_room,
                                                 first_furnishing):
    # selecting a group also selects its members (Qt couples them); a
    # grouped furnishing must not draw its own box/handle, only the group's
    g = _group_room_with_furnishing(fp, win, make_room, first_furnishing)
    furn = next(c for c in g.childItems() if isinstance(c, fp.FurnishingItem))
    assert furn.isSelected()              # selected via the group
    assert not furn._handle_visible()     # but shows no individual handle
    g.dissolve()                          # ungrouped + still selected
    furn.setSelected(True)
    assert furn._handle_visible()         # on its own it does


def test_group_box_orients_with_rotation(fp, win, make_room, first_furnishing):
    g = _group_room_with_furnishing(fp, win, make_room, first_furnishing)
    c = g.childrenBoundingRect().center()
    g._begin_rotation(QPointF(c.x() + 100, c.y()))
    ang = math.radians(30)
    g._apply_rotation(QPointF(c.x() + 100 * math.cos(ang),
                              c.y() + 100 * math.sin(ang)), False)
    g._finish_rotation()

    # g._angle is GroupItem's oriented-box rotation state, retired when group
    # semantics are rewritten in v5 P4.5 (V5_MIGRATION_PLAN); assertion kept.
    assert g._angle == pytest.approx(30, abs=1)
    local, _ = g._oriented_box()
    aabb = g.childrenBoundingRect()
    # the oriented box hugs the (rotated) content, so it is tighter than the
    # axis-aligned bounding box -- proving it turns with the group
    assert local.height() < aabb.height()


def test_group_rotation_ctrl_snaps_to_increment(fp, win, make_room,
                                                first_furnishing):
    g = _group_room_with_furnishing(fp, win, make_room, first_furnishing)
    furn = next(c for c in g.childItems() if isinstance(c, fp.FurnishingItem))
    step = fp.SETTINGS["rotate_snap_deg"]
    c = g.childrenBoundingRect().center()
    g._begin_rotation(QPointF(c.x() + 100, c.y()))         # start angle 0
    ang = math.radians(37)                                 # a non-multiple
    g._apply_rotation(
        QPointF(c.x() + 100 * math.cos(ang), c.y() + 100 * math.sin(ang)),
        True)
    g._finish_rotation()

    assert round(furn.rotation()) % int(step) == 0
    assert furn.rotation() == pytest.approx(30, abs=1)     # 37 -> nearest 15


def test_group_box_not_inflated_by_wide_window(fp, win):
    # a wide window on a room wall must not balloon the group's selection
    # box out past the room (regression: opening bounding rects were huge)
    sc = win.scene
    for p1, p2 in [((0, 0), (144, 0)), ((144, 0), (144, 96)),
                   ((144, 96), (0, 96)), ((0, 96), (0, 0))]:
        sc.addItem(fp.WallItem(QPointF(*p1), QPointF(*p2), "interior"))
    top = next(w for w in sc.items() if isinstance(w, fp.WallItem)
               and w.p1.y() == 0 and w.p2.y() == 0)
    op = fp.OpeningItem(top, "window", "9648", 72)   # 96" window on top wall
    top.openings.append(op)
    top.rebuild()
    fp.rebuild_all_walls(sc)
    for w in [it for it in sc.items() if isinstance(it, fp.WallItem)]:
        w.setSelected(True)
    win.group_selected()
    g = next(i for i in sc.items() if isinstance(i, fp.GroupItem))
    box = g.childrenBoundingRect()
    # room is 96" tall; the box must hug it, not extend a window-width above
    assert box.height() < 150            # was ~210 with the old margin


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


# --------------------------------------------------------------------------
# DEFECT 22 -- whole-plan group + move, at a scale the rest of this file never
# reaches. Every group test above tops out at ~5 members and none of them ever
# looked at the document's debris counter, which is exactly why 497 passing
# tests missed a bug a single manual drag surfaced.
# --------------------------------------------------------------------------
def _v5_plan(fp, win, name="symmetricP1.json"):
    import json
    import pathlib
    ex = pathlib.Path(__file__).resolve().parent.parent / "examples" / name
    win.open_document(json.loads(ex.read_text("utf-8")), interactive=False)
    return win


def _unwelded(win):
    import warnings
    from floorplanner.design.bridge import design_from_scene
    rep = {}
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        design_from_scene(win, report=rep)
    return rep["unwelded_ends"]


def _corner_sharing(fp, win):
    """(corners holding one of their own walls' vertices, total corners)."""
    same = total = 0
    for r in win.scene.items():
        if not isinstance(r, fp.RoomItem):
            continue
        ends = {id(w.end_vertex(a)) for w in r.walls
                if isinstance(w, fp.WallItem) for a in ("p1", "p2")}
        for e in r.outline:
            total += 1
            same += id(e.v) in ends
    return same, total


def _group_everything(fp, win):
    win.scene.clearSelection()
    for it in win.scene.items():
        if isinstance(it, (fp.WallItem, fp.FurnishingItem)) \
                and it.group() is None:
            it.setSelected(True)
    win.group_selected()
    return [it for it in win.scene.items() if isinstance(it, fp.GroupItem)]


def _columns(fp, win, dx, dy, before):
    """Per room: (walls that moved by exactly (dx,dy), walls total, corners
    that moved, corners total, corners still holding one of their own walls'
    vertex objects).

    The four columns the P3.5-followup diagnosis reported, as an assertion.
    Walls-moved vs outline-moved is the COHERENCE question (does the room agree
    with its own walls about where it is); identity is the by-construction
    question underneath it, which no positional column can see."""
    out = {}
    for r in win.scene.items():
        if not isinstance(r, fp.RoomItem) or r.name not in before:
            continue
        w0, c0 = before[r.name]
        walls = {id(w): (round(w.p1.x(), 3), round(w.p1.y(), 3))
                 for w in fp.room_walls(r)}
        wm = sum(1 for k, v in walls.items() if k in w0
                 and abs(v[0] - w0[k][0] - dx) < 1e-3
                 and abs(v[1] - w0[k][1] - dy) < 1e-3)
        corners = [(round(e.p.x(), 3), round(e.p.y(), 3)) for e in r.outline]
        cm = sum(1 for a, b in zip(c0, corners, strict=False)
                 if abs(b[0] - a[0] - dx) < 1e-3 and abs(b[1] - a[1] - dy) < 1e-3)
        ends = {id(w.end_vertex(a)) for w in fp.room_walls(r)
                for a in ("p1", "p2")}
        ident = sum(1 for e in r.outline if id(e.v) in ends)
        out[r.name] = (wm, len(w0), cm, len(c0), ident)
    return out


def _snapshot(fp, win):
    return {r.name: ({id(w): (round(w.p1.x(), 3), round(w.p1.y(), 3))
                      for w in fp.room_walls(r)},
                     [(round(e.p.x(), 3), round(e.p.y(), 3))
                      for e in r.outline])
            for r in win.scene.items() if isinstance(r, fp.RoomItem)}


def test_whole_plan_group_move_carries_every_room(fp, win):
    """A whole-plan group move: EVERY room agrees with its own walls about
    where it ended up, and no junction is torn.

    Asserts the four columns the followup diagnosis reported, per room --
    walls-moved, outline-moved, identity, and the debris counter -- because the
    first three can disagree in ways that look identical on screen. The
    positional half of this passes against the pre-fix code too (the old bake
    translated each carried room's corner list explicitly, so rooms tracked
    POSITIONALLY); the identity column is the half that does not, and it is
    asserted here rather than only in the receipts below so this test cannot go
    vacuous. Scale is the other point: 20 rooms and 80 walls against the ~5
    members every other group test in this file uses."""
    _v5_plan(fp, win)
    dx, dy = 60.0, 36.0
    before = _snapshot(fp, win)
    assert len(before) == 20
    assert _unwelded(win) == 0, "the fixture did not open clean"

    for g in _group_everything(fp, win):
        g.setPos(dx, dy)
        g.bake()

    cols = _columns(fp, win, dx, dy, before)
    assert set(cols) == set(before), "a room went missing"
    for name, (wm, wt, cm, ct, ident) in sorted(cols.items()):
        assert (wm, cm, ident) == (wt, ct, ct), (
            f"{name}: walls {wm}/{wt} moved, corners {cm}/{ct} moved, "
            f"identity {ident}/{ct} -- the room disagrees with its own walls")
    assert _unwelded(win) == 0, "the move tore the wall network"


@pytest.mark.xfail(strict=False,
                   reason="defect 23: a band that clips a room's wall set "
                          "strands that room; the semantics are P4.5's")
def test_a_clipped_band_leaves_every_room_coherent(fp, win):
    """DEFECT 23, characterized against the invariant BOTH candidate semantics
    satisfy, so it flips whichever way P4.5 rules.

    A rubber band takes only items FULLY inside it, so a wall poking out is left
    behind and `group_selected` duplicates the rest of that room's walls --
    `room_owns_walls` is then correctly false and the room is not carried. Its
    walls walk out from under a region that stays put. Measured: 3 of 20 rooms,
    Garage at 6/9 walls moved against 0/9 corners.

    PER-ROOM COHERENCE is what both readings agree on. Under deform-to-follow a
    clipped room's 6 moved walls carry 6 of its corners; under stay-put the
    grouping would have to take the whole room or none of it, so 0 and 0. Either
    way the two columns AGREE, and today they do not. Deliberately NOT asserting
    which -- that is the decision P4.5 owns.

    This predates P3.5 and the branch measurably improves it (148.3" of drift
    before, 46.65" now), so it is a characterization, not a gate."""
    _v5_plan(fp, win)
    dx, dy = 60.0, 36.0
    walls = [it for it in win.scene.items() if isinstance(it, fp.WallItem)]
    xs = [p.x() for w in walls for p in (w.p1, w.p2)]
    ys = [p.y() for w in walls for p in (w.p1, w.p2)]
    win.view.select_in_rect(QRectF(min(xs) - 24, min(ys) - 24,
                                   (max(xs) - min(xs)) * 0.92 + 24,
                                   max(ys) - min(ys) + 48))
    before = _snapshot(fp, win)
    win.group_selected()
    for g in [it for it in win.scene.items() if isinstance(it, fp.GroupItem)]:
        g.setPos(dx, dy)
        g.bake()

    cols = _columns(fp, win, dx, dy, before)
    # The stranded rooms are this test's SUBJECT, so declare the state it built
    # as the accepted baseline -- the same move `_overlapping_rooms` makes for
    # its deliberate overlap. Without it the `win` fixture's teardown verify
    # fires under FP_VERIFY_DESIGN=deep and the test is reported TWICE (an `E`
    # in the progress line and a second xfail), which is what the phantom `E`
    # sighted during the P3.5-followup actually was.
    from floorplanner.design.verify import rebase
    rebase(win)
    incoherent = {n: (wm, wt, cm, ct)
                  for n, (wm, wt, cm, ct, _i) in cols.items() if wm != cm}
    assert not incoherent, (
        "rooms whose walls and outline disagree about the move: "
        + "; ".join(f"{n} walls {a}/{b} vs corners {c}/{d}"
                    for n, (a, b, c, d) in sorted(incoherent.items())))


def test_a_group_move_leaves_the_outlines_still_holding_their_corners(fp, win):
    """DEFECT 22's receipt. The property the move must PRESERVE, asserted
    directly and then through its symptom: after a bake a room's outline still
    holds the very vertices its walls hold, so the next wall drag moves the
    room. Measured before the fix: 140/140 shared corners -> 0/140, and a
    party-wall drag then resized nothing."""
    _v5_plan(fp, win)
    assert _corner_sharing(fp, win) == (140, 140)
    for g in _group_everything(fp, win):
        g.setPos(48.0, 0.0)
        g.bake()
        g.dissolve()
    fp.rebuild_all_walls(win.scene)
    assert _corner_sharing(fp, win) == (140, 140)

    # DETERMINISTIC PICK (defect 28). `next(w for w in win.scene.items() ...)`
    # took whichever party wall the scene happened to list first, and scene item
    # order is not stable across processes -- so this test moved a DIFFERENT
    # corner on different runs, and 18 of the 59 candidates leave the plan with
    # two rooms overlapping. Sorting on geometry makes the subject the same wall
    # every run; the assertion below is unchanged.
    party = min((w for w in win.scene.items()
                 if isinstance(w, fp.WallItem) and len(w.rooms) == 2
                 and w.group() is None),
                key=lambda w: (w.p1.x(), w.p1.y(), w.p2.x(), w.p2.y()))
    a, b = party.rooms[0], party.rooms[1]
    a0, b0 = a.area_sqft, b.area_sqft
    v = party.end_vertex("p1")
    # EVERY room holding this corner follows it -- which is what the app's own
    # corner-movers do (`_DragVertex.ends`/`.edges` on the drag,
    # `GroupItem._corner_records` on bake and rotation): the holders are
    # collected from the geometry, not from the wall. Re-pointing only the
    # party wall's two rooms left a third holder behind on the old vertex,
    # which is how this test came to leave overlapping rooms behind it.
    holders = [r for r in win.scene.items()
               if isinstance(r, fp.RoomItem) and any(e.v is v for e in r.outline)]
    moved = v.relocated_to(QPointF(v.x + 12, v.y + 12))
    for w in win.scene.items():                    # move that corner for real
        if isinstance(w, fp.WallItem):
            for at in ("p1", "p2"):
                if w.end_vertex(at) is v:
                    w.set_end_vertex(at, moved)
    for r in holders:
        for e in r.outline:
            if e.v is v:
                e.v = moved
    assert (a.area_sqft, b.area_sqft) != (a0, b0), \
        "the rooms did not follow the corner -- the outlines were orphaned"
    left_behind = [r.name for r in holders
                   if not any(e.v is moved for e in r.outline)]
    assert not left_behind, \
        f"rooms left on the old corner while the walls moved: {left_behind}"


def test_a_group_rotation_also_keeps_the_corners(fp, win):
    """The rotation half of defect 22: `_apply_rotation` re-maps every member
    from a start-of-gesture snapshot on each mouse event, which was the same
    coordinate path with the same result (measured 140/140 -> 0/140). Both
    paths now move the same corner records."""
    _v5_plan(fp, win)
    groups = _group_everything(fp, win)
    g = groups[0]
    c = g.sceneBoundingRect().center()
    g._begin_rotation(QPointF(c.x() + 100, c.y()))
    g._apply_rotation(QPointF(c.x(), c.y() + 100), False)      # 90 degrees
    g._finish_rotation()
    fp.rebuild_all_walls(win.scene)
    assert _corner_sharing(fp, win) == (140, 140)
    assert _unwelded(win) == 0


def test_a_group_move_never_drags_a_wall_outside_it(fp, win, make_room):
    """The carve-out the vertex move has to respect: a corner a NON-member wall
    also holds is SPLIT before the move, so the group goes and the outsider
    stays. Relocating it wholesale would wire a member to an outside wall --
    exactly what the `group() is None` guards exist to prevent."""
    sc = win.scene
    room = make_room(sc, 0, 0, 120, 120, "A")
    stub = fp.WallItem(QPointF(120, 120), QPointF(240, 120), "interior")
    sc.addItem(stub)                       # meets the room's corner, not a member
    fp.rebuild_all_walls(sc)
    for w in room.walls:                   # weld the stub onto the room corner
        for at in ("p1", "p2"):
            if abs(getattr(w, at).x() - 120) < 1e-9 \
                    and abs(getattr(w, at).y() - 120) < 1e-9:
                stub.set_end_vertex("p1", w.end_vertex(at))
    before = (stub.p1.x(), stub.p1.y(), stub.p2.x(), stub.p2.y())

    sc.clearSelection()
    for w in room.walls:
        w.setSelected(True)
    win.group_selected()
    for g in [it for it in sc.items() if isinstance(it, fp.GroupItem)]:
        g.setPos(36.0, 0.0)
        g.bake()

    assert (stub.p1.x(), stub.p1.y(), stub.p2.x(), stub.p2.y()) == before, \
        "the group dragged a wall that was not in it"
    assert room.corners[0].x() != 0 or room.corners[1].x() != 0


def _nwalls(fp, sc):
    return sum(isinstance(i, fp.WallItem) for i in sc.items())


def test_grouping_twenty_rooms_with_their_walls_creates_no_walls(fp, win):
    """P3.8's acceptance: 'Grouping 20 rooms creates 0 new walls'.

    STATED FOR THE SELECTION A USER ACTUALLY MAKES -- Ctrl+A, or a band over
    the plan -- which takes the rooms AND their walls. Measured on
    symmetricP1: 80 walls in, 80 after grouping, 80 after a bake. The room's
    own selected walls ride in as themselves; nothing is copied.

    The rooms-ONLY selection is a different question and still duplicates; it
    is the xfail below, and P4.5's."""
    _v5_plan(fp, win)
    sc = win.scene
    assert sum(isinstance(i, fp.RoomItem) for i in sc.items()) == 20
    before = _nwalls(fp, sc)
    sc.clearSelection()
    for it in sc.items():
        if isinstance(it, (fp.RoomItem, fp.WallItem)) and it.group() is None:
            it.setSelected(True)
    win.group_selected()
    assert _nwalls(fp, sc) == before, "grouping copied walls"
    for g in [i for i in sc.items() if isinstance(i, fp.GroupItem)]:
        g.setPos(48.0, 0.0)
        g.bake()
    assert _nwalls(fp, sc) == before, "the bake copied walls"


@pytest.mark.xfail(strict=False, reason="grouping a room ALONE still copies "
                   "its walls (duplicate_wall); what a group IS is P4.5's")
def test_grouping_rooms_without_their_walls_still_copies_them(fp, win,
                                                              make_room):
    """The same sentence read literally -- the ROOM items and nothing else.

    Split from the test above for the reason P0.4's test 2 was split: one
    assertion cannot tell today's behaviour from P4.5's, and a test that passes
    in both worlds proves nothing about the change.

    THE MECHANISM IS PINNED HERE; THE SCALE IS RECORDED IN THE LOG. Measured at
    P3.8 on symmetricP1's twenty rooms: +868 walls, and the duplication
    COMPOUNDS -- the same rooms grouped one at a time sum to only 258, because
    each room's copy sees the copies the earlier ones made. Pinning that here
    would cost the suite 40 seconds to rebuild a number the log already states,
    so this uses two rooms: `duplicate_wall` either copies or it does not, and
    at P4.5 it dies and this flips."""
    sc = win.scene
    make_room(sc, 0, 0, 120, 120, "A")
    make_room(sc, 120, 0, 120, 120, "B")
    before = _nwalls(fp, sc)
    sc.clearSelection()
    for it in sc.items():
        if isinstance(it, fp.RoomItem):
            it.setSelected(True)
    win.group_selected()
    assert _nwalls(fp, sc) == before
