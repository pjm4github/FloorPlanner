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


# --------------------------------------------------------------------------
# D74 — decoration along the run, and the gate's symbol
# --------------------------------------------------------------------------
def _marks(wall):
    """The x of every point in a wall's decoration path, in scene coords.

    Read off the path rather than recomputed, so these tests measure what will
    actually be drawn instead of restating the generator."""
    p = wall._decor
    return [] if p is None else [p.elementAt(i).x
                                 for i in range(p.elementCount())]


def _ticks(wall):
    """The x of each TICK, found by its top edge -- which the table's `reach`
    locates for this type.

    Distinguished from `_marks` because a fence tick carries a filled POST, so
    counting raw path elements would count one tick several times and a
    "closer" assertion would silently become an "is decorated more elaborately"
    one."""
    from floorplanner.walls import WALL_DECOR

    spec = WALL_DECOR.get(wall.wall_type)
    p = wall._decor
    if p is None or spec is None:
        return []
    top = wall.p1.y() - spec.reach                 # the path is in scene coords
    return sorted(p.elementAt(i).x for i in range(p.elementCount())
                  if abs(p.elementAt(i).y - top) < 1e-6)


def test_a_fence_and_a_railing_are_distinguishable(fp, scene):
    """THE FINDING THAT PRODUCED D74, as an assertion.

    The first cut asked THICKNESS to say which type a wall is, and it cannot:
    a fence and a railing are both 2.0" because both really are about two
    inches thick. **A channel committed to representing a real quantity cannot
    also carry identity.**

    THE FIRST ASSERTION IS THE PRECONDITION AND IT IS NOT DECORATION: without
    it, "the two differ" would be satisfied by the thickness that was already
    there, and this test would pass on the code it was written to reject.
    """
    from floorplanner.design.validate import STD_T
    from floorplanner.walls import WALL_DECOR
    from PyQt6.QtCore import QPointF

    assert STD_T["fence"] == STD_T["railing"], (
        "PRECONDITION: if these ever differ, thickness alone might carry the "
        "distinction and this test stops measuring the second channel")

    fence = fp.WallItem(QPointF(0, 0), QPointF(120, 0), "fence")
    rail = fp.WallItem(QPointF(0, 60), QPointF(120, 60), "railing")
    scene.addItem(fence)
    scene.addItem(rail)

    assert fence.t == rail.t                      # the channel that cannot
    assert fence._decor is not None, "a fence must be decorated"
    assert rail._decor is not None, "a railing must be decorated"

    # "closer, lighter cross-ticks, reading as related-but-lighter"
    assert len(_ticks(rail)) > len(_ticks(fence)), \
        "the railing's ticks must be closer along the same run"
    assert WALL_DECOR["railing"].reach < WALL_DECOR["fence"].reach, \
        "the railing's ticks are shorter"
    assert WALL_DECOR["railing"].grey > WALL_DECOR["fence"].grey, \
        "the railing's ticks are lighter ink (higher grey = paler)"

    # and the two are different KINDS of mark, not two densities of one -- the
    # fence carries a post, which is what stopped them reading as one ladder
    # at working zoom (evidence/d74-decoration-working-zoom.png)
    assert WALL_DECOR["fence"].post > 0, "a fence draws its posts"
    assert WALL_DECOR["railing"].post == 0, "a railing does not"


def test_a_retaining_wall_draws_plain_because_thickness_works_for_it(fp, scene):
    """The exemption is deliberate, and it is the other half of the ruling:
    thickness fails as an identity channel for the two that share a value, and
    keeps working for the two that genuinely ARE fatter. So `retaining` is
    absent from the table on purpose rather than by omission -- and the second
    assertion is what makes that claim mean something."""
    from floorplanner.design.validate import STD_T
    from PyQt6.QtCore import QPointF

    w = fp.WallItem(QPointF(0, 0), QPointF(120, 0), "retaining")
    scene.addItem(w)
    assert w._decor is None, "retaining keeps thickness; it is not decorated"
    assert STD_T["retaining"] != STD_T["interior"], (
        "PRECONDITION: retaining is legible only because its thickness really "
        "is different -- if that stopped being true it would need the channel")


def test_an_ordinary_wall_is_not_decorated_at_all(fp, scene):
    """The channel is for the types that need it. An interior wall builds no
    decoration path, so the edit path of an ordinary plan pays nothing for
    this -- the generator returns before its first loop."""
    from PyQt6.QtCore import QPointF

    for kind in ("exterior", "interior", "partition"):
        w = fp.WallItem(QPointF(0, 0), QPointF(120, 0), kind)
        scene.addItem(w)
        assert w._decor is None, f"{kind} must draw plain"


def test_a_gate_breaks_the_decoration_either_side(fp, win):
    """A gate is a BREAK IN THE RUN plus a light swing arc. The break is not
    drawn by the opening: the wall's decoration skips its opening spans, so the
    ticks stop either side and resume after -- one definition
    (`_opening_spans`) feeding both the body's holes and the decoration, so the
    break cannot drift away from the gap.

    THE PRECONDITION IS THE HALF THAT COULD GO VACUOUS: "no tick inside the
    span" is also true of a wall with no ticks anywhere, so the same wall
    WITHOUT the gate is measured first and must have ticks exactly there.
    """
    from PyQt6.QtCore import QPointF

    sc = win.scene
    fence = fp.WallItem(QPointF(0, 0), QPointF(240, 0), "fence")
    sc.addItem(fence)
    fp.rebuild_all_walls(sc)

    op_lo, op_hi = 120 - 16.0, 120 + 16.0          # a 3068 gate at s=120
    before = [x for x in _marks(fence) if op_lo <= x <= op_hi]
    assert before, "PRECONDITION: undecorated here, and the test proves nothing"

    op = fp.OpeningItem(fence, "gate", "3068", 120)
    fence.openings.append(op)
    fp.rebuild_all_walls(sc)

    after = [x for x in _marks(fence) if op_lo <= x <= op_hi]
    assert not after, f"the gate must break the decoration, found marks at {after}"
    assert _marks(fence), "it breaks the run, it does not erase it"


def test_the_gates_arc_is_lighter_than_a_doors(fp, scene):
    """"Lighter than a door's" is the drafting convention, and it is the only
    thing that separates the two symbols now that thinness has been ruled
    unable to carry it -- thinness says how thick the gate is, which is a real
    quantity, and nothing about what it is."""
    from floorplanner.walls import GATE_INK

    door_ink = 20                                  # OpeningItem.paint's ink
    assert GATE_INK.red() > door_ink, "the gate's arc must be the lighter line"
    assert GATE_INK.red() < 255, "...and must still be visible"


def test_the_properties_sheet_names_a_derived_gate(fp, win):
    """DERIVING A PROPERTY IS NOT A LICENCE TO HIDE IT. The sheet this replaces
    asked for a size and put the kind in a title bar, so a user who placed a
    door in a railing and got a GATE was never told.

    The door case is asserted too, and it is not padding: the reason line must
    appear only where there IS one. A door is a door because it was asked for,
    and explaining that would be noise."""
    from PyQt6.QtCore import QPointF
    from PyQt6.QtWidgets import QLabel

    from floorplanner.dialogs import OpeningPropertiesDialog

    def sheet_text(wall_type, kind, y):
        # y keeps the two runs APART, and the reason was MEASURED rather than
        # guessed at: stacked, the two walls fold to ONE wall in the document
        # carrying BOTH openings, which then overlap --
        #     "I7  openings o1/o2 overlap on w1"
        # It is the coincidence that does it, not the missing rebuild: both
        # rebuilt and unrebuilt stacked scenes report it, and both separated
        # ones are clean. Nothing to do with what this test is about.
        w = fp.WallItem(QPointF(0, y), QPointF(120, y), wall_type)
        win.scene.addItem(w)
        op = fp.OpeningItem(w, kind, "3068", 60)
        w.openings.append(op)
        fp.rebuild_all_walls(win.scene)
        dlg = OpeningPropertiesDialog(op)
        return " ".join(lb.text() for lb in dlg.findChildren(QLabel))

    gate = sheet_text("railing", "gate", 0.0)
    assert "Gate" in gate, "the sheet must say what the user made"
    assert "railing" in gate, "...and why it is one"
    assert "I7" in gate, "...naming the rule, so the reason is checkable"

    door = sheet_text("interior", "door", 240.0)
    assert "Door" in door, "the kind is always shown"
    assert "Derived" not in door, "a chosen kind gets no invented explanation"
