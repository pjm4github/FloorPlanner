"""P3.6 -- an opening is dimensioned from a NAMED END, not from `p1`.

The three properties the schema claims for `{from, offset_in}` and absolute `s`
cannot deliver, quoted from `design-schema.v5.json`:

    "Dimensioned the way a drawing dimensions it: an offset from a NAMED END,
     not an absolute distance from p1. Survives the wall being stretched, split
     at a new vertex, or reversed -- absolute `s` survives none of those."

(a) and (b) are here; the split is in test_topology_ops.py, where the split
planner's own tests live.
"""
import pytest
from PyQt6.QtCore import QPointF

pytestmark = pytest.mark.walls


def _wall_with_door(fp, scene, x2=240.0, s=200.0):
    w = fp.WallItem(QPointF(0, 0), QPointF(x2, 0), "interior")
    scene.addItem(w)
    op = fp.OpeningItem(w, "door", "3280", s)      # 32" wide, centre at s
    w.openings.append(op)
    w.rebuild()
    return w, op


def test_an_opening_holds_its_offset_when_the_far_end_is_stretched(fp, scene):
    """R1(a) -- THE DISCRIMINATING CASE.

    A door 40" from the v2 end stays 40" from the v2 end when v2 moves. Under
    absolute `s` it holds its distance from v1 instead, so stretching the wall
    at v2 slides the door away from the end it was dimensioned off -- which is
    never what a drawing means."""
    w, op = _wall_with_door(fp, scene, 240.0, 200.0)
    assert op.anchor_from(w) == "v2", "a door past the midpoint anchors to v2"
    off0 = op.offset_in
    gap0 = w.length() - op.s                       # centre-to-v2, 40"

    v = w.end_vertex("p2")                         # stretch AT v2
    w.set_end_vertex("p2", v.relocated_to(QPointF(300.0, 0.0)))
    w.rebuild()

    assert op.offset_in == pytest.approx(off0), "the stored offset moved"
    assert w.length() - op.s == pytest.approx(gap0), \
        "the door did not keep its distance from the end it is dimensioned off"


def test_reversing_a_wall_leaves_its_openings_where_they_are(fp, scene):
    """R1(b). Swapping a wall's two ends is a change of description, not of
    geometry, so nothing may move. Under absolute `s` -- measured from
    whichever end is currently `p1` -- every opening MIRRORS."""
    w, op = _wall_with_door(fp, scene, 240.0, 200.0)
    before = QPointF(w.point_at(op.s))

    v1, v2 = w.end_vertex("p1"), w.end_vertex("p2")
    w.set_end_vertex("p1", v2)                     # a raw swap: same wall,
    w.set_end_vertex("p2", v1)                     # described the other way
    w.rebuild()

    after = w.point_at(op.s)
    assert after.x() == pytest.approx(before.x(), abs=1e-6), \
        f"the door mirrored: {before.x()} -> {after.x()}"
    assert after.y() == pytest.approx(before.y(), abs=1e-6)


def test_a_weld_carries_an_anchor_but_a_share_does_not(fp, scene):
    """The two halves of `_fuse_anchors`, and the refusal is the load-bearing
    one -- it is what keeps R1(b) true.

    A WELD fuses two ends that are already at one corner onto a single
    `Vertex`: same physical corner, so an anchor on the absorbed vertex must
    follow it or the opening is orphaned and mirrors. A SHARE or a swap points
    an end at a vertex somewhere ELSE, and there the anchor must stay exactly
    where it is -- re-pointing it would move the opening, which is the mirroring
    bug wearing different clothes."""
    w, op = _wall_with_door(fp, scene, 240.0, 200.0)
    assert op.anchor_from() == "v2"

    # WELD: a co-located vertex replaces p2 -- the anchor follows
    v2 = w.end_vertex("p2")
    twin = fp.Vertex(v2.point().x(), v2.point().y())
    assert twin is not v2
    w.set_end_vertex("p2", twin)
    assert op.anchor_v is twin, "a weld did not carry the anchor"
    assert op.anchor_from() == "v2"
    assert op.s == pytest.approx(200.0)

    # SHARE: a vertex somewhere else -- the anchor must NOT follow
    elsewhere = fp.Vertex(90.0, 0.0)
    w.set_end_vertex("p2", elsewhere)
    assert op.anchor_v is twin, "a share dragged the anchor off its corner"


def test_a_far_end_anchor_survives_a_round_trip(fp, win):
    """R4b. An anchor that already exists round-trips VERBATIM; the
    nearer-end rule applies only when MINTING.

    Hand-authored: a door on a 240" wall dimensioned 30" from v2, so its centre
    sits at 194" -- past the midpoint, which means the nearer end is v2 and this
    anchor is ALSO the nearer one. So the door is deliberately placed at 40"
    from v1 instead, where nearer-end canonicalization WOULD rewrite it, and
    the test asserts it does not. Re-basing here would be a silent loss of
    intent: the anchor end decides which way the opening travels when the wall
    is stretched."""
    import json

    from floorplanner.design.bridge import design_from_scene

    doc = {
        "format": "floorplanner-design", "version": 5, "units": "inches",
        "settings": {}, "furnishings": [], "groups": [], "rooms": [],
        "levels": [{"id": "L1", "name": "default", "elevation_in": 0.0,
                    "height_in": 96.0, "kind": "storey"}],
        "vertices": [{"id": "a", "level": "L1", "x": 0.0, "y": 0.0},
                     {"id": "b", "level": "L1", "x": 240.0, "y": 0.0}],
        "walls": [{"id": "w1", "level": "L1", "v1": "a", "v2": "b",
                   "type": "interior", "left": None, "right": None,
                   "openings": [{"id": "o1", "kind": "door", "code": "3280",
                                 # centre at 40" -- v1 is the NEARER end, so a
                                 # canonicalizing emit would rewrite this to v1
                                 "anchor": {"from": "v2", "offset_in": 184.0}}]}],
    }
    win.open_document(json.loads(json.dumps(doc)), interactive=False)

    wall = next(it for it in win.scene.items() if isinstance(it, fp.WallItem))
    (op,) = wall.openings
    assert op.anchor_from() == "v2", "the load re-based the anchor"
    assert op.offset_in == pytest.approx(184.0)
    assert op.s == pytest.approx(40.0)            # 240 - 184 - 16

    out = design_from_scene(win).to_dict()
    (w_out,) = out["walls"]
    (o_out,) = w_out["openings"]
    assert o_out["anchor"] == {"from": "v2", "offset_in": 184.0}, \
        "the save re-based the anchor onto the nearer end"


def _tee_through_a_doorway(fp, scene):
    """A door with a wall T-ing into the middle of it -- a scene state a gesture
    can reach today, and one the document can only represent by cutting the
    wall in half through the door."""
    a = fp.WallItem(QPointF(0, 0), QPointF(240, 0), "interior")
    scene.addItem(a)
    op = fp.OpeningItem(a, "door", "3280", 120.0)      # spans 104..136
    a.openings.append(op)
    scene.addItem(fp.WallItem(QPointF(120, 0), QPointF(120, 120), "interior"))
    fp.rebuild_all_walls(scene)
    return a, op


def test_the_walk_reports_the_opening_it_cannot_place_and_emits_it_anyway(
        fp, scene):
    """R2c. The walk is TOTAL: a load cannot decline, so it emits the straddling
    opening where R2b puts it and FILES it. The `max(0.0, off)` that used to
    slide it quietly back onto the segment is gone -- that was the charter's
    silent repair, hiding in the walk rather than in `rebuild`."""
    from floorplanner.design.bridge import design_from_scene

    _tee_through_a_doorway(fp, scene)
    rep = {}
    doc = design_from_scene(scene, report=rep).to_dict()

    assert len(rep["openings_failed"]) == 1, rep["openings_failed"]
    (msg,) = rep["openings_failed"]
    assert "cut by a junction" in msg and "door 3280" in msg
    (oid,) = rep["openings_failed_ids"]

    # EMITTED, not dropped, and not slid: it is still on a wall and still 32"
    emitted = [o for w in doc["walls"] for o in w["openings"]]
    assert len(emitted) == 1 and emitted[0]["id"] == oid
    assert emitted[0]["code"] == "3280"


def test_a_reported_I7_is_expected_but_an_unreported_one_is_not(fp, scene):
    """The exemption is keyed PER OPENING, which is what keeps shadow mode's
    teeth. Exempting the CLASS would blind it to every other way an opening can
    run off a wall."""
    from floorplanner.design.bridge import design_from_scene
    from floorplanner.design.validate import check
    from floorplanner.design.verify import fault_profile

    _tee_through_a_doorway(fp, scene)
    rep = {}
    doc = design_from_scene(scene, report=rep).to_dict()

    # the document really does carry the fault ...
    i7 = [e for e in check(doc) if e.startswith("I7")]
    assert len(i7) == 1 and "runs off" in i7[0]
    # ... and it is expected, because the walk filed it
    assert "I7" not in fault_profile(scene, doc=doc, walk_report=rep)
    # ... but the SAME document with nothing filed is a regression
    assert fault_profile(scene, doc=doc, walk_report={}).get("I7") == 1


def test_a_split_clear_of_a_door_leaves_it_exactly_where_it_was(fp, scene):
    """R1(c) -- the third of the schema's three claims, and it had no test.

    R1 lists "(c) the split of R2" as acceptance; the split coverage was the two
    pins, and both asserted REFUSAL. Refusal is not a property of the anchor --
    it was the absence of one. This is the property: a cut elsewhere on the wall
    does not move a door, and when the cut takes the door's anchored end away
    the anchor RE-SEATS to the SAME-SIDE end of its new segment (R2b), so the
    description changes and the geometry does not."""
    from floorplanner.walls import split_wall_at

    w = fp.WallItem(QPointF(0, 0), QPointF(240, 0), "interior")
    scene.addItem(w)
    op = fp.OpeningItem(w, "door", "3280", 200.0)   # anchored v2, spans 184..216
    w.openings.append(op)
    fp.rebuild_all_walls(scene)
    assert op.anchor_from() == "v2"
    before = QPointF(w.point_at(op.s))

    seg = split_wall_at(scene, w, QPointF(60, 0))   # well clear of the door
    assert seg is not None

    # the door rode to whichever segment holds it; find it and check the place
    host = next(x for x in scene.items()
                if isinstance(x, fp.WallItem) and x.openings)
    (moved,) = host.openings
    after = host.point_at(moved.s)
    assert after.x() == pytest.approx(before.x()), "the split moved the door"
    assert after.y() == pytest.approx(before.y())
    # SAME SIDE: it was dimensioned off the high end and still is
    assert moved.anchor_from() == "v2"
    assert moved.fits()


def test_an_opening_that_cannot_be_placed_is_reported_not_dropped(fp, win):
    """DEFECT 6, and the v4 LOAD site specifically -- "incl. on load" is what
    the defect text singles out, and it was the one that mattered: a v5 load
    reported a dropped opening (P1.5) while a v4 load said nothing at all.

    Eight sites swallowed `ValueError` with a bare `continue`. They now file
    into one vocabulary, and the two surfaces differ only in where it lands:
    a load's entries join the open report, an edit's reach the status bar."""
    data = {
        "format": "floorplanner-json",
        "version": 4, "settings": {}, "rooms": [], "furnishings": [],
        "floors": [{"name": "default", "reference": False}],
        "walls": [{"p1": [0, 0], "p2": [40, 0], "type": "interior",
                   "floor": "default",
                   # a 96" garage door on a 40" wall: it cannot go on
                   "openings": [{"kind": "door", "code": "9680", "s": 20.0,
                                 "door_type": "LH", "swing": -1}]}],
    }
    win.load_data(data)

    walls = [it for it in win.scene.items() if isinstance(it, fp.WallItem)]
    assert len(walls) == 1
    assert walls[0].openings == [], "the impossible opening was placed anyway"
    msg = win.statusBar().currentMessage()
    assert "could not be placed" in msg, f"the load said nothing: {msg!r}"
    assert "door 9680" in msg, f"the report does not name the opening: {msg!r}"


def test_the_edit_surface_names_the_edit_and_says_it_once(fp, win):
    """The other surface. An edit that cannot carry an opening says so at the
    quiescent point, names which edit dropped it, and does not repeat itself --
    the wording standard set when the unwelded-ends warning was de-spammed."""
    from floorplanner.walls import (drain_opening_failures,
                                    report_opening_failure)

    sc = win.scene
    w = fp.WallItem(QPointF(0, 0), QPointF(40, 0), "interior")
    sc.addItem(w)
    report_opening_failure(sc, w, "door", "9680", 20.0,
                           "Opening is wider than the wall. (pasting)")
    win._commit_if_changed()
    first = win.statusBar().currentMessage()
    assert "Could not place" in first and "pasting" in first

    win.status("something else entirely")
    win._commit_if_changed()                    # nothing new filed
    assert win.statusBar().currentMessage() == "something else entirely", \
        "the report repeated itself with nothing new to say"
    assert drain_opening_failures(sc) == []


# --------------------------------------------------------------------------
# Phase 5 — settable wall types, railings and gates
# --------------------------------------------------------------------------
def test_a_railing_draws_thinner_than_a_wall(fp, scene):
    """THINNESS IS THE CHANNEL. A railing is 2" against an exterior wall's 6",
    and the plan drawing follows because `paint` reads `self.t`.

    Asserted against the MODEL's table rather than literals, so this cannot
    drift from what the app will actually draw (D73)."""
    from floorplanner.design.validate import STD_T
    from PyQt6.QtCore import QPointF

    wall = fp.WallItem(QPointF(0, 0), QPointF(120, 0), "exterior")
    rail = fp.WallItem(QPointF(0, 60), QPointF(120, 60), "railing")
    scene.addItem(wall)
    scene.addItem(rail)
    assert wall.t == STD_T["exterior"]
    assert rail.t == STD_T["railing"]
    assert rail.t < wall.t, "a railing must be thinner than a wall"


def test_a_thickness_override_beats_the_type_default(fp, scene):
    """OVERRIDE IF PRESENT, ELSE THE TYPE'S NORMATIVE DEFAULT.

    A type lookup that discarded the override would turn a display divergence
    into a DATA one: the document carries `wall.thickness_in`, it survives a
    round trip in `_v5_extra`, and the editor would draw one number while the
    file said another and then keep saving the file's.
    """
    from floorplanner.design.validate import STD_T
    from PyQt6.QtCore import QPointF

    w = fp.WallItem(QPointF(0, 0), QPointF(120, 0), "hedge")
    scene.addItem(w)
    assert w.t == STD_T["hedge"]                 # precondition: the default
    w._v5_extra = {"thickness_in": 24.0}
    assert w.t == 24.0, "the document's override must win"
    w._v5_extra = {"thickness_in": 0}            # nonsense value
    assert w.t == STD_T["hedge"], "a bad override falls back, it does not zero"


def test_every_settable_wall_type_is_in_the_schema_enum():
    """The menu names and orders types; it must never DEFINE one. A type the
    menu offers that the schema rejects would produce documents the validator
    refuses, from a click."""
    import json
    from pathlib import Path

    from floorplanner.walls import WALL_TYPE_LABELS

    schema = json.loads(
        (Path(__file__).resolve().parent.parent / "floorplanner" / "design"
         / "design-schema.v5.json").read_text(encoding="utf-8"))
    enum = set(schema["$defs"]["wall"]["properties"]["type"]["enum"])
    offered = {k for k, _ in WALL_TYPE_LABELS}
    assert offered <= enum, f"menu offers types the schema rejects: {offered - enum}"
    assert "railing" in offered, "the point of the feature"


def test_a_door_placed_in_a_railing_becomes_a_gate(fp, win):
    """I7 has required this since P0.7 -- only gates in a landscape wall -- and
    nothing could produce one, so the rule guarded an unreachable state.

    THE GATE IS DERIVED, NOT CHOSEN: the user places a door and gets a gate
    because of what they placed it in, so I7 is true by construction rather
    than by a check the user can fail.

    Asserted through `check()` rather than on the kind string alone, because
    the invariant is the thing that cares.
    """
    from PyQt6.QtCore import QPointF

    from floorplanner.design.bridge import design_from_scene
    from floorplanner.design.validate import check
    from floorplanner.walls import LANDSCAPE_TYPES

    assert "railing" in LANDSCAPE_TYPES                      # precondition

    sc = win.scene
    rail = fp.WallItem(QPointF(0, 0), QPointF(120, 0), "railing")
    sc.addItem(rail)
    op = fp.OpeningItem(rail, "gate", "3068", 60)
    rail.openings.append(op)
    fp.rebuild_all_walls(sc)

    doc = design_from_scene(win).to_dict()
    kinds = {o["kind"] for w in doc["walls"] for o in w.get("openings", [])}
    assert "gate" in kinds, f"the gate did not reach the document: {kinds}"
    assert not [e for e in check(doc, deep=True) if e.startswith("I7")], \
        "a gate in a railing must satisfy I7"


def test_a_door_in_a_railing_would_fail_I7(fp, win):
    """The precondition that makes the test above mean something: the SAME
    scene with a `door` instead of a `gate` must be rejected. Without this,
    'I7 is clean' could be true of an invariant that never fires."""
    from PyQt6.QtCore import QPointF

    from floorplanner.design.bridge import design_from_scene
    from floorplanner.design.validate import check

    sc = win.scene
    rail = fp.WallItem(QPointF(0, 0), QPointF(120, 0), "railing")
    sc.addItem(rail)
    op = fp.OpeningItem(rail, "door", "3068", 60)
    rail.openings.append(op)
    fp.rebuild_all_walls(sc)

    doc = design_from_scene(win).to_dict()
    assert [e for e in check(doc, deep=True) if e.startswith("I7")], \
        "I7 must reject a door in a railing, or the gate test proves nothing"

    # THE VIOLATION IS THE POINT OF THIS TEST, so it is declared as the
    # accepted baseline -- otherwise shadow mode (FP_VERIFY_DESIGN) raises at
    # `win` teardown for a fault this test built on purpose, and the ON/DEEP
    # gate lanes go red while the plain suite passes. Same mechanism
    # `_overlapping_rooms` uses in test_rooms.py, and the same reasoning: a
    # deliberately-constructed fault is not a regression.
    from floorplanner.design.verify import rebase
    rebase(win)
