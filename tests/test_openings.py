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
