"""Concept rooms + nominal_size (P4.4): a room typed in BY DIMENSION rather
than drawn -- wall-less, floating by construction, carrying its typed intent.
"""
import warnings

import pytest
from PyQt6.QtCore import QPointF

import FloorPlanner as fp
from floorplanner.design.bridge import design_from_scene
from floorplanner.design.validate import check, schema_errors

pytestmark = pytest.mark.rooms


def _walk(win):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return design_from_scene(win).to_dict()


def _room_doc(win, name):
    return next(r for r in _walk(win)["rooms"] if r["name"] == name)


def test_a_concept_room_is_wall_less_and_floating(fp, scene):
    room = fp.make_concept_room(scene, "Bedroom", 144.0, 168.0,
                                QPointF(300, 300))
    assert room.placement_state == "floating"
    assert room.category == "concept"
    assert room.nominal_size == {"width_in": 144.0, "depth_in": 168.0}
    assert room.walls == [], "a concept room is WALL-LESS"
    assert len(room.corners) == 4
    assert len(room.open_edges()) == 4, "every edge is open, and draws dashed"
    # the outline is authoritative, and it agrees with the typed size
    assert room.area_sqft == pytest.approx(144.0 * 168.0 / 144.0)
    assert room.anchor.x() == pytest.approx(300)
    xs = [c.x() for c in room.corners]
    assert min(xs) == pytest.approx(300 - 72) and max(xs) == pytest.approx(372)


def test_a_concept_room_round_trips_through_the_document(win):
    fp.make_concept_room(win.scene, "Bedroom", 144.0, 168.0,
                         QPointF(300, 300))
    doc = _walk(win)
    assert schema_errors(doc) == [], schema_errors(doc)
    assert check(doc, deep=True) == [], check(doc, deep=True)
    rd = _room_doc(win, "Bedroom")
    assert rd["category"] == "concept"
    assert rd["nominal_size"] == {"width_in": 144.0, "depth_in": 168.0}
    assert rd["placement"]["state"] == "floating"
    assert all(e["wall"] is None for e in rd["outline"])

    win.load_data(doc)                      # ...and back into the scene
    room = next(r for r in win.scene.items()
                if isinstance(r, fp.RoomItem) and r.name == "Bedroom")
    assert room.category == "concept"
    assert room.nominal_size == {"width_in": 144.0, "depth_in": 168.0}
    assert room.placement_state == "floating"
    assert _walk(win) == doc, "the round trip is not a fixed point"


def test_i13_holds_by_construction(win):
    # a concept room that is not floating is an I13 violation -- the factory
    # cannot make one, so the guard is asked of the DOCUMENT
    fp.make_concept_room(win.scene, "Sketch", 120.0, 120.0, QPointF(300, 300))
    doc = _walk(win)
    assert check(doc, deep=True) == []
    doc["rooms"][0]["placement"]["state"] = "placed"     # forge it
    errs = check(doc, deep=True)
    assert any(e.startswith("I13") for e in errs), errs


def test_a_concept_room_may_sit_over_the_plan(win):
    # I11 exempts concept rooms -- that is what lets a sketch unit be parked
    # on top of the plan while you decide where it goes
    corners = [QPointF(0, 0), QPointF(240, 0), QPointF(240, 180),
               QPointF(0, 180)]
    for i in range(4):
        win.scene.addItem(fp.WallItem(corners[i], corners[(i + 1) % 4],
                                      "interior"))
    fp.rebuild_all_walls(win.scene)
    res = fp.detect_room(win.scene, QPointF(120, 90))
    placed = fp.RoomItem("Living", QPointF(120, 90), res[0], res[1],
                         corners=res[2])
    win.scene.addItem(placed)
    fp.bind_room_walls(win.scene, placed)

    fp.make_concept_room(win.scene, "Sketch", 96.0, 96.0, QPointF(120, 90))
    assert check(_walk(win), deep=True) == [], "a concept overlap was flagged"


def test_a_wall_less_room_moves_as_a_unit(fp, scene):
    # before P4.4 the label drag required walls, so a wall-less room's REGION
    # stayed behind while the label wandered off
    room = fp.make_concept_room(scene, "Sketch", 120.0, 120.0,
                                QPointF(300, 300))
    x0 = [c.x() for c in room.corners]
    room._translate(60.0, 0.0)
    assert [c.x() for c in room.corners] == pytest.approx([x + 60 for x in x0])
    assert room.anchor.x() == pytest.approx(360)


def test_the_category_heuristic_is_only_a_fallback(win):
    # a room the app never told a category still derives one from its name --
    # the pre-P4.4 behaviour, which must not regress now that the item wins
    corners = [QPointF(0, 0), QPointF(240, 0), QPointF(240, 180),
               QPointF(0, 180)]
    for i in range(4):
        win.scene.addItem(fp.WallItem(corners[i], corners[(i + 1) % 4],
                                      "interior"))
    fp.rebuild_all_walls(win.scene)
    res = fp.detect_room(win.scene, QPointF(120, 90))
    room = fp.RoomItem("Front Porch", QPointF(120, 90), res[0], res[1],
                       corners=res[2])
    win.scene.addItem(room)
    fp.bind_room_walls(win.scene, room)
    assert room.category is None                  # never told
    assert _room_doc(win, "Front Porch")["category"] == "exterior"
    room.category = "interior"                    # told -> the item wins
    assert _room_doc(win, "Front Porch")["category"] == "interior"


def test_a_concept_room_templates_and_inserts(win):
    # the two P4.4 halves compose: a typed sketch unit is itself a template
    room = fp.make_concept_room(win.scene, "Bedroom", 144.0, 168.0,
                                QPointF(300, 300))
    tmpl = win.room_template(room)
    assert tmpl["rooms"][0]["category"] == "concept"
    assert tmpl["rooms"][0]["nominal_size"]["width_in"] == 144.0
    assert tmpl["walls"] == []
    copy = win.insert_room_template(tmpl, at=QPointF(800, 300))
    assert copy is not None and copy.category == "concept"
    assert copy.nominal_size == {"width_in": 144.0, "depth_in": 168.0}
    assert copy.placement_state == "floating"
    assert check(_walk(win), deep=True) == []


@pytest.mark.gui
def test_the_dialog_reports_inches(qapp):
    dlg = fp.ConceptRoomDialog()
    dlg.ed_name.setText("Study")
    dlg.sp_w.setValue(10.0)
    dlg.sp_d.setValue(12.5)
    assert dlg.values() == ("Study", 120.0, 150.0)
