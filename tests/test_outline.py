"""P3.2 -- `RoomItem.outline`, and the death of the `perimeter_corners` mirror.

Two things are pinned here, and the second is the more important:

  * the outline exists, `corners` derives from it, and every edge knows which
    wall covers it (`None` = an OPEN edge, the v5 `wall: null`);
  * the outline holds COORDINATES, not vertex identity -- and that gap is
    asserted where it is, so the task that closes it has to do so consciously.

RETARGETED P3.4 -> P3.5 (doc only, committed before any P3.5 code). P3.4
replaced the coalesce/weld/fracture ops but never touched outlines, so the two
guards below stayed green straight through it. The task that rebuilds outlines
from traced faces -- and therefore the task they are addressed to -- is P3.5.
"""
import json
from pathlib import Path

import pytest
from PyQt6.QtCore import QPointF

pytestmark = pytest.mark.rooms

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


# --------------------------------------------------------------- the outline
def test_corners_derive_from_the_outline(fp, scene, make_room):
    room = make_room(scene, 0, 0, 144, 120, "Den")
    assert room.outline, "no outline built"
    assert room.corners == [e.p for e in room.outline]
    assert len(room.corners) == len(room.outline)


def test_corners_is_none_not_empty_when_there_is_no_outline(fp, scene,
                                                            make_room):
    """The codebase tests `if room.corners:` and distinguishes None from a
    list everywhere; the derived property must keep that."""
    room = make_room(scene, 0, 0, 144, 120, "Den")
    room.corners = None
    assert room.corners is None and room.outline == []


def test_every_edge_knows_its_wall(fp, scene, make_room):
    """The real content of P3.2: before it, a room had corners and an
    unordered `walls` list with NO edge->wall mapping."""
    room = make_room(scene, 0, 0, 144, 120, "Den")
    assert len(room.outline) == 4
    assert all(e.wall is not None for e in room.outline), \
        "a closed room's edges should each name a wall"
    assert {id(e.wall) for e in room.outline} == {id(w) for w in room.walls}


def test_wall_refs_survive_a_translation_but_not_a_reshape(fp, scene,
                                                           make_room):
    """A group move or nudge translates every corner and keeps the same edges;
    a re-detection with a different shape must drop the stale mapping for
    bind_room_walls to repopulate."""
    room = make_room(scene, 0, 0, 144, 120, "Den")
    walls = [e.wall for e in room.outline]
    room.corners = [QPointF(c.x() + 10, c.y() + 10) for c in room.corners]
    assert [e.wall for e in room.outline] == walls, "translation lost the walls"

    room.corners = [QPointF(0, 0), QPointF(50, 0), QPointF(0, 50)]
    assert [e.wall for e in room.outline] == [None, None, None]


# ------------------------------------------- THE GAP: coordinates, not identity
def test_outline_holds_coordinates_not_vertex_identity(fp, scene, make_room):
    """P3.2's interim representation, asserted so P3.5 must close it knowingly.

    In the target model a corner IS the vertex two walls share. P3.1's
    split-on-write world has no such vertex: at every corner each wall owns a
    distinct `Vertex`. So an outline edge holds a COORDINATE -- equal to the
    wall's end, and deliberately not the same object. Borrowing one wall's
    vertex would pick arbitrarily between two; minting a room-owned one would
    add a third. Both would encode an authority that does not exist yet.

    P3.5 rebuilds outlines from the document's traced faces, giving walls and
    outlines the same vertices at the same moment. When it does, this test
    should be REPLACED by one asserting identity -- its failure is the signal
    that the gap closed, not that something broke."""
    room = make_room(scene, 0, 0, 144, 120, "Den")
    edge = room.outline[0]
    wall = edge.wall
    ends = (wall.p1, wall.p2)

    same_coords = [p for p in ends
                   if abs(p.x() - edge.p.x()) < 1e-9
                   and abs(p.y() - edge.p.y()) < 1e-9]
    assert same_coords, "the outline corner is not at either wall end"
    assert all(p is not edge.p for p in ends), \
        "outline and wall now SHARE a point object -- if P3.5 did this, " \
        "replace this test with an identity assertion"


def test_a_corner_is_still_two_distinct_wall_vertices(fp, scene, make_room):
    """Why the outline cannot name a vertex yet: the corner itself is two
    objects. This is what P3.5 unifies.

    TWO WAYS THIS CAN GO RED, and they are different findings. The DESIGNED one
    is P3.5's outline flip, which gives walls and outlines the same vertices at
    once. The OTHER is a weld reaching the room-creation path -- P3.4 built
    `share_coincident_ends`, and `make_room` simply never calls it. So this
    doubles as a tripwire on that, and P3.5's sub-commits are sequenced
    (retarget -> flip -> path changes) to keep the two apart: red during the
    flip is the flip; red at any other point is a finding."""
    room = make_room(scene, 0, 0, 144, 120, "Den")
    corner = room.outline[0].p
    at = [w for w in room.walls
          for p in (w.p1, w.p2)
          if abs(p.x() - corner.x()) < 1e-9 and abs(p.y() - corner.y()) < 1e-9]
    assert len(at) == 2, "expected two walls meeting at this corner"
    assert at[0].v1 != at[1].v1 and at[0].v2 != at[1].v2
    uids = {at[0]._v1.uid, at[0]._v2.uid} & {at[1]._v1.uid, at[1]._v2.uid}
    assert not uids, ("the walls already share a vertex -- the P3.5 flip, or "
                      "a weld reached the room-creation path?")


# ------------------------------- perimeter_corners: three consumers, three fates
def test_the_live_mirror_is_gone(fp, scene, make_room):
    """Fate 1 of 3: deleted. Geometry never lives in `properties` -- the schema
    calls that bag 'Schedule data only. NO geometry' and forbids the key."""
    room = make_room(scene, 0, 0, 144, 120, "Den")
    assert not hasattr(room, "_sync_corner_props")
    assert "perimeter_corners" not in room.properties


def test_the_legacy_v4_export_still_carries_corners(fp, win, make_room):
    """Fate 2 of 3: kept, byte-compatibly -- re-derived at serialization time
    at the same 2dp rounding. The v4 loader needs it for OPEN rooms, whose
    detection fails and which fall back to the stored corners."""
    room = make_room(win.scene, 0, 0, 144, 120, "Den")
    doc = win.serialize()
    pc = doc["rooms"][0]["properties"]["perimeter_corners"]
    assert pc == [[round(c.x(), 2), round(c.y(), 2)] for c in room.corners]


def test_load_strips_the_stale_mirror(fp, win, make_room):
    """...and 'ignored on load': the value is READ for the open-room fallback
    and then dropped, because nothing in the scene maintains it any more."""
    make_room(win.scene, 0, 0, 144, 120, "Den")
    doc = json.loads(json.dumps(win.serialize()))
    assert "perimeter_corners" in doc["rooms"][0]["properties"]
    win.load_data(doc)
    room = next(r for r in win.scene.items() if isinstance(r, fp.RoomItem))
    assert "perimeter_corners" not in room.properties
    assert room.corners, "the corners themselves must survive the round trip"


def test_the_importer_still_reads_legacy_corners(fp):
    """Fate 3 of 3: stays forever. v1-v4 files carry the key; it is the
    stored-corners fallback, the face-claim area, and the Gate 2 corner weld."""
    from floorplanner.design.importer import import_legacy
    src = json.loads((EXAMPLES / "planc1.json").read_text(encoding="utf-8"))
    assert any((r.get("properties") or {}).get("perimeter_corners")
               for r in src["rooms"])
    _design, rep = import_legacy(src)
    assert rep["corners_welded"] > 0, "the importer stopped reading them"


def test_copying_a_room_does_not_carry_its_geometry(fp, win, make_room):
    """Found by the P3.2 audit, and the mirror was MASKING it: `_copy_spec`
    carried `dict(self.properties)`, including the SOURCE room's
    perimeter_corners, and only `_sync_corner_props` overwriting them on the
    pasted room hid the fact. With the mirror gone the stale geometry would
    have shipped into the paste."""
    room = make_room(win.scene, 0, 0, 144, 120, "Den")
    spec = room._copy_spec()
    assert "perimeter_corners" not in spec["properties"]


# ------------------------------------------------------ areas across the corpus
@pytest.mark.parametrize("name", ["sample_plan.json", "planc1.json"])
def test_room_areas_unchanged_across_the_corpus(fp, win, name):
    """THE acceptance. Both apply paths, per the standing gate addition."""
    from floorplanner.design.bridge import design_from_scene
    win.load_data(json.loads((EXAMPLES / name).read_text(encoding="utf-8")))
    areas = {r.name: r.area_sqft for r in win.scene.items()
             if isinstance(r, fp.RoomItem)}
    assert areas, "no rooms loaded"
    d1 = design_from_scene(win).to_dict()

    win.load_data(json.loads(json.dumps(d1)))          # faithful apply
    after = {r.name: r.area_sqft for r in win.scene.items()
             if isinstance(r, fp.RoomItem)}
    for room, sf in areas.items():
        assert after[room] == pytest.approx(sf, abs=0.1), f"{room} moved"
    assert design_from_scene(win).to_dict() == d1
