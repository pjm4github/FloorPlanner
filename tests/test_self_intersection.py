"""P4.5 section 2a: a deforming move that crosses a room's own outline says so
AT THE GESTURE.

I5b catches this in the document -- but it is deep-only, so shadow mode never
runs it while editing, while `save_path` does run it and refuses to write. Left
alone, the user deforms a room, hears nothing, and finds out at the moment they
try to keep their work. The save refusal is correct and stays; what this adds
is that the gesture speaks first.

Measured while writing these: the two checks do NOT always agree, because the
walk planarises a crossing into a pinched loop that a PROPER-crossing test does
not report. That is register row 41, and it is why the message promises a
remedy but never promises that the save will refuse.
"""
import pytest
from PyQt6.QtCore import QPointF

import FloorPlanner as fp

pytestmark = pytest.mark.rooms


def _room(scene, pts, name):
    corners = [QPointF(*p) for p in pts]
    for i in range(len(corners)):
        scene.addItem(fp.WallItem(corners[i], corners[(i + 1) % len(corners)],
                                  "interior"))
    fp.rebuild_all_walls(scene)
    cx = sum(c.x() for c in corners) / len(corners)
    cy = sum(c.y() for c in corners) / len(corners)
    room = fp.RoomItem(fp.unique_room_name(scene, name), QPointF(cx, cy),
                       fp.room_path_from_corners(corners),
                       fp.poly_area_sqft(corners),
                       corners=corners)
    scene.addItem(room)
    fp.bind_room_walls(scene, room)
    return room


# --------------------------------------------------------------------------
# the predicate -- the SAME one the document check uses
# --------------------------------------------------------------------------
def test_a_simple_rectangle_does_not_self_intersect(fp, scene):
    r = _room(scene, [(0, 0), (120, 0), (120, 96), (0, 96)], "Plain")
    assert fp.outline_self_intersects(r) is False


def test_a_bowtie_does_self_intersect(fp, scene):
    # the classic inversion: swap two adjacent corners and the outline crosses
    r = _room(scene, [(0, 0), (120, 0), (0, 96), (120, 96)], "Bowtie")
    assert fp.outline_self_intersects(r) is True


def test_the_gesture_check_catches_what_i5b_can_miss(fp, win):
    """MEASURED DIVERGENCE, and it is why the message promises no save
    refusal (register row 41).

    I5b is exact on the geometry it is given -- but the walk PLANARISES, so
    two crossing outline walls are split at their intersection and the room
    emits as a PINCHED loop visiting that point twice. `_seg_cross` is a
    PROPER-crossing test (it must not fire on the collinear edges two rooms
    legitimately share), so it does not report a pinch. The scene check runs
    before that split and sees the crossing.

    Pinned so the day I5b is widened, this test fails and the message can be
    strengthened deliberately rather than by accident."""
    import warnings

    from floorplanner.design.bridge import design_from_scene
    from floorplanner.design.validate import check

    r = _room(win.scene, [(0, 0), (120, 0), (0, 96), (120, 96)], "Bowtie")
    assert fp.outline_self_intersects(r) is True, "the gesture check must fire"
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        doc = design_from_scene(win).to_dict()
    pos = {v["id"]: (v["x"], v["y"]) for v in doc["vertices"]}
    loop = [pos[e["v"]] for e in doc["rooms"][0]["outline"]]
    assert len(loop) > len(r.corners), "the walk did not planarise the crossing"
    assert len(loop) != len(set(loop)), "the emitted loop is not pinched"
    assert not [e for e in check(doc, deep=True) if e.startswith("I5b")], (
        "I5b now catches the pinched form -- row 41 is closed, and "
        "report_self_intersections may promise the save refusal again")


# --------------------------------------------------------------------------
# the message -- read at its boundary values (the 06c2145 standard)
# --------------------------------------------------------------------------
def _report(fp, scene, rooms):
    fp.drain_gesture_faults(scene)                 # start clean
    fp.report_self_intersections(scene, rooms)
    return fp.drain_gesture_faults(scene)


def test_a_clean_move_says_nothing(fp, scene):
    r = _room(scene, [(0, 0), (120, 0), (120, 96), (0, 96)], "Plain")
    assert _report(fp, scene, [r]) == []


def test_one_room_names_the_room_and_the_remedy(fp, scene):
    r = _room(scene, [(0, 0), (120, 0), (0, 96), (120, 96)], "Great Room")
    msgs = _report(fp, scene, [r])
    assert len(msgs) == 1
    m = msgs[0]
    assert "Great Room" in m                       # WHICH room
    assert "undo" in m and "extract" in m          # what to DO about it
    assert "Great Room's outline now crosses itself" in m
    # ...and it must NOT promise the save will refuse: measured, sometimes it
    # does not (the pinched-loop divergence above, register row 41)
    assert "cannot be saved" not in m


def test_two_and_three_rooms_read_as_english(fp, scene):
    """The 06c2145 lesson: read the sentence the code will actually print, at
    its edge cases. A naive join gives 'A and B and C' or 'A, B, C now has'."""
    a = _room(scene, [(0, 0), (120, 0), (0, 96), (120, 96)], "Den")
    b = _room(scene, [(200, 0), (320, 0), (200, 96), (320, 96)], "Hall")
    two = _report(fp, scene, [a, b])[0]
    assert "Den and Hall now have outlines that cross themselves" in two
    c = _room(scene, [(400, 0), (520, 0), (400, 96), (520, 96)], "Nook")
    three = _report(fp, scene, [a, b, c])[0]
    assert "Den, Hall and Nook now have outlines that cross themselves" in three
    assert " and Hall and " not in three           # not a naive join


# --------------------------------------------------------------------------
# the wiring: a group bake that deforms a room reports it
# --------------------------------------------------------------------------
@pytest.mark.groups
def test_a_bake_that_crosses_an_outline_reports_at_the_gesture(fp, win):
    """FLIPPED xfail -> hard pass at P4.5, and it was the receipt it said it
    was: under copy-based grouping `_corner_records` split any corner an
    outsider held, so a clipped bake could not deform a room at all and there
    was nothing to report. It can now.

    THE OLD BODY WOULD NOT HAVE FLIPPED EITHER, and the reason is geometry, not
    mechanism -- worth stating because "the receipt did not flip" was carried
    for a day as evidence against the mechanism. Two facts the old body had
    wrong. (a) It says "move ONE corner": a group holding the two walls that
    meet at a corner holds THREE corners (2 walls x 2 ends), so three of the
    four move and one stays. (b) Its delta, (-400, 300), translates those three
    clear of the fixed corner and yields an ordinary non-crossing quadrilateral
    -- measured, `outline_self_intersects` is False there, so the silence was
    correct and the assertion was wrong. A delta that FOLDS the moved part back
    across the stationary corner is what crosses the outline: measured
    crossing at (0,150), (0,200), (0,300), (60,240) and (-60,300), non-crossing
    at (-400,300).

    So the deform is asserted as a PRECONDITION before the message is demanded
    -- otherwise this is a negative-shaped verdict wearing a positive's
    clothes, passing whenever the geometry happens not to cross."""
    sc = win.scene
    r = _room(sc, [(0, 0), (120, 0), (120, 96), (0, 96)], "Den")
    fp.drain_gesture_faults(sc)
    # a group of the two walls meeting at (120, 0) holds THREE of the room's
    # four corners; folding them back over the fourth crosses the outline --
    # the clipped-band case in miniature
    g = fp.GroupItem()
    sc.addItem(g)
    corner = r.outline[1].v                       # (120, 0)
    for w in r.walls:
        for attr in ("p1", "p2"):
            if w.end_vertex(attr) is corner:
                g.adopt(w)
                break
    g.setPos(QPointF(0, 300))
    g.bake()

    # PRECONDITION -- the bake really did deform the room into a crossing
    # outline. Without this the verdict is satisfied by a bake that did nothing.
    assert fp.outline_self_intersects(r), (
        "the bake did not cross the outline, so there is nothing to report: "
        f"{[(round(e.p.x()), round(e.p.y())) for e in r.outline]}")
    msgs = fp.drain_gesture_faults(sc)
    assert any("crosses itself" in m for m in msgs), (
        f"the bake deformed a room into a crossing outline and said nothing: "
        f"{msgs}")
    assert any("Den" in m for m in msgs)
    # The crossed outline is this test's SUBJECT, so declare it as the accepted
    # baseline -- the same move `_overlapping_rooms` makes for its deliberate
    # overlap. Placed AFTER the verdicts, so they judge the real state; it only
    # stops the `win` teardown reporting I5b 0 -> 1 under FP_VERIFY_DESIGN=deep,
    # which would blame this test for the state it exists to produce.
    from floorplanner.design.verify import rebase
    rebase(win)


# --------------------------------------------------------------------------
# D42 (G4) -- THE SECOND CALLER. §2a put this check in at the group bake and
# recorded that the party-wall drag was knowingly uncovered: there is no shared
# vertex-translation applier to attach it to, and unifying the three that exist
# is the Phase 6 task. These pin the missing caller -- the same report, the same
# words, a different gesture -- and the second one pins that it stays QUIET,
# because a message that fires on ordinary work is worse than no message.
# --------------------------------------------------------------------------
def _px(win, inches):
    """Scene inches as viewport pixels, at whatever zoom the fixture opens at."""
    return int(inches * win.view.transform().m11())


def test_a_drag_that_crosses_an_outline_says_so(fp, win, drag):
    """An L-shaped room whose inner edge is slid past the far wall.

    A body drag, not an endpoint drag, and that is not incidental: a wall bound
    to a room has LOCKED ENDS (`_ends_editable`), so sliding the run is the
    gesture actually available here -- which is why the exposure is real.
    """
    sc = win.scene
    r = _room(sc, [(0, 0), (200, 0), (200, 100), (100, 100),
                   (100, 200), (0, 200)], "Ell")
    fp.drain_gesture_faults(sc)
    before = [(round(e.p.x()), round(e.p.y())) for e in r.outline]

    drag(win, QPointF(100, 150), _px(win, -150), 0, steps=3)

    after = [(round(e.p.x()), round(e.p.y())) for e in r.outline]
    # PRECONDITION 1 -- the drag moved the room's corners at all. Without this
    # a drag that did nothing satisfies everything below by doing nothing.
    assert after != before, f"the drag moved no outline corner: {after}"
    # PRECONDITION 2 -- and it moved them into a crossing, which is the state
    # the message is about. Same guard the bake test states.
    assert fp.outline_self_intersects(r), \
        f"the drag did not cross the outline, so there is nothing to report: {after}"

    msgs = fp.drain_gesture_faults(sc)
    assert any("crosses itself" in m for m in msgs), \
        f"the drag deformed a room into a crossing outline and said nothing: {msgs}"
    assert any("Ell" in m for m in msgs), f"the message names no room: {msgs}"
    # the remedy, not just the diagnosis -- the 06c2145 standard
    assert any("undo" in m for m in msgs), f"no remedy offered: {msgs}"

    # this crossed outline is the test's SUBJECT; declare it so the win
    # teardown does not report I5b 0 -> 1 against the state it exists to make
    from floorplanner.design.verify import rebase
    rebase(win)


def test_an_ordinary_drag_says_nothing(fp, win, drag):
    """The anti-nagging half, and it is the one worth having.

    A wall drag is the commonest gesture in the app. A check attached to it
    that fires on ordinary work would be worse than no check, so this asserts
    silence -- with the precondition that the drag REALLY MOVED the room,
    because silence is otherwise satisfied by a gesture that did nothing.
    """
    sc = win.scene
    r = _room(sc, [(0, 0), (200, 0), (200, 100), (100, 100),
                   (100, 200), (0, 200)], "Ell")
    fp.drain_gesture_faults(sc)
    before = [(round(e.p.x()), round(e.p.y())) for e in r.outline]

    drag(win, QPointF(100, 150), _px(win, 40), 0, steps=3)   # a modest slide

    after = [(round(e.p.x()), round(e.p.y())) for e in r.outline]
    # PRECONDITION -- the gesture did something, and left a sane room.
    assert after != before, f"the drag moved no outline corner: {after}"
    assert not fp.outline_self_intersects(r), \
        f"this drag was supposed to leave a simple outline: {after}"

    assert fp.drain_gesture_faults(sc) == [], \
        "an ordinary wall drag must not report a self-intersection"
