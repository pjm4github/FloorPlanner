"""Parametric cabinets and the room style in the editor (0329).

The plan item, the properties dialog, the Room Properties style rows, and
what reaches the plan file. A dialog is never `exec()`-ed (a modal loop hangs
headless); `try_accept()` is exactly what OK calls.
"""
import pytest
from PyQt6.QtCore import QPointF

from floorplanner.dialogs import RoomPropertiesDialog
from floorplanner.parametric import findings as F

pytestmark = pytest.mark.furnishings


def _cabinets(win, fp, kind):
    return [it for it in win.scene.items()
            if isinstance(it, fp.FurnishingItem) and it.kind == kind]


# -- the item ------------------------------------------------------------------
def test_an_untouched_cabinet_is_its_preset_and_writes_no_state(fp):
    it = fp.make_furnishing("base_cab_36", QPointF(0, 0))
    assert it.is_parametric()
    assert it.params is None and it.extra_state() == {}
    assert (it.w, it.d) == (36.0, 24.0)


def test_parameters_resize_the_footprint_and_round_trip(fp):
    it = fp.make_furnishing("base_cab_36", QPointF(10, 20))
    it.apply_params({"width_in": 42.0, "finish": "navy"})
    assert (it.w, it.d) == (42.0, 24.0)
    state = it.extra_state()
    assert state == {"finish": "navy", "width_in": 42.0}, "only what differs"
    again = fp.make_furnishing("base_cab_36", QPointF(10, 20), 0.0, state)
    assert (again.w, again.d) == (42.0, 24.0)
    assert again.extra_state() == state


def test_accepting_the_preset_unchanged_stores_nothing(fp):
    it = fp.make_furnishing("wall_cab_30", QPointF(0, 0))
    it.apply_params({"floor_to_bottom_in": 54.0, "width_in": 30.0})
    assert it.params is None and it.extra_state() == {}


def test_a_plain_furnishing_is_not_parametric(fp):
    sofa = fp.make_furnishing("sofa", QPointF(0, 0))
    assert not sofa.is_parametric() and sofa.make_properties_dialog() is None


def test_a_cabinet_reads_the_style_of_the_room_it_stands_in(fp, scene, make_room):
    room = make_room(scene, 0, 0, 240, 240, "Kitchen")
    room.properties["style"] = {"cabinet_finish": "cherry"}
    inside = fp.make_furnishing("base_cab_36", QPointF(120, 120))
    outside = fp.make_furnishing("base_cab_36", QPointF(900, 900))
    scene.addItem(inside)
    scene.addItem(outside)
    assert inside.param_context()["room_style"] == {"cabinet_finish": "cherry"}
    assert outside.param_context()["room_style"] is None


# -- the dialog ----------------------------------------------------------------
def test_the_cabinet_dialog_previews_in_the_room_style_and_accepts(fp, qapp, scene,
                                                                  make_room):
    room = make_room(scene, 0, 0, 240, 240, "Kitchen")
    room.properties["style"] = {"cabinet_finish": "cherry", "countertop": "granite"}
    it = fp.make_furnishing("base_cab_36", QPointF(120, 120))
    scene.addItem(it)
    dlg = it.make_properties_dialog()
    assert dlg is not None and dlg.preview is not None
    assert dlg._derived["materials"]["cabinet"] == "cab_cherry"
    assert dlg._derived["materials"]["countertop"] == "ct_granite"
    width = dlg._widgets["width_in"]
    width.setValue(33.0)
    assert dlg._derived["footprint"] == (33.0, 24.0)
    assert not F.blocks(dlg.findings()) and not F.needs_ack(dlg.findings())
    assert dlg.try_accept(), "advisories never block and need no acknowledgement"
    assert it.params is None, "the dialog edits a draft"
    it.apply_params(dlg.result_state())
    assert it.extra_state() == {"width_in": 33.0}
    assert it.w == 33.0
    dlg.deleteLater()


def test_drawers_count_is_offered_only_for_an_all_drawer_front(fp, qapp):
    it = fp.make_furnishing("base_cab_36", QPointF(0, 0))
    dlg = it.make_properties_dialog()
    drawers, front = dlg._widgets["drawers"], dlg._widgets["front"]
    assert not drawers.isEnabled()
    front.setCurrentIndex(front.findData("drawers"))
    assert drawers.isEnabled()
    # counted by drawer NUMBER, not by part: a five-piece drawer front is
    # five parts (drawer-2-stile-l ...), a slab one is a single part
    numbers = {p.name.split("-")[1] for p in dlg._derived["parts"]
               if p.name.startswith("drawer-")
               and not p.name.startswith("drawer-pull")}
    assert numbers == {"1", "2", "3"}
    dlg.deleteLater()


def test_the_wall_cabinet_dialog_has_a_height_from_the_floor(fp, qapp):
    it = fp.make_furnishing("wall_cab_30", QPointF(0, 0))
    dlg = it.make_properties_dialog()
    assert "floor_to_bottom_in" in dlg._widgets
    assert "toe_kick_h_in" not in dlg._widgets and "top_on" not in dlg._widgets
    dlg._widgets["floor_to_bottom_in"].setValue(60.0)
    assert min(p.z0 for p in dlg._derived["parts"]) == pytest.approx(60.0)
    dlg.deleteLater()


def test_the_appliance_dialog_offers_match_and_custom(fp, qapp):
    it = fp.make_furnishing("range", QPointF(0, 0))
    dlg = it.make_properties_dialog()
    assert set(dlg._widgets) == {"finish_mode", "sheen", "colour"}
    mode, sheen = dlg._widgets["finish_mode"], dlg._widgets["sheen"]
    assert not sheen.isEnabled()
    mode.setCurrentIndex(mode.findData("custom"))
    assert sheen.isEnabled()
    assert dlg._derived["materials"]["appliance"].startswith("sheen_")
    mode.setCurrentIndex(mode.findData("match"))
    assert dlg._derived["materials"]["appliance"] == "cab_maple"
    assert dlg.try_accept()
    it.apply_params(dlg.result_state())
    assert it.extra_state() == {"finish_mode": "match"}
    dlg.deleteLater()


# -- the room's style ----------------------------------------------------------
def test_room_properties_sets_and_clears_the_style(fp, qapp, scene, make_room):
    room = make_room(scene, 0, 0, 240, 240, "Kitchen")
    assert "style" not in room.properties
    dlg = RoomPropertiesDialog(room, None)
    finish, top = dlg._style_boxes["cabinet_finish"], dlg._style_boxes["countertop"]
    assert finish.currentData() == "" and top.currentData() == ""
    finish.setCurrentIndex(finish.findData("cherry"))
    top.setCurrentIndex(top.findData("granite"))
    dlg.apply()
    assert room.properties["style"] == {"cabinet_finish": "cherry",
                                        "countertop": "granite"}
    dlg.deleteLater()

    again = RoomPropertiesDialog(room, None)
    assert again._style_boxes["cabinet_finish"].currentData() == "cherry"
    for cb in again._style_boxes.values():
        cb.setCurrentIndex(0)                       # back to "(default)"
    again.apply()
    assert "style" not in room.properties, "an unstyled room keeps no style key"
    again.deleteLater()


def test_a_style_key_from_a_newer_build_survives_the_dialog(fp, qapp, scene,
                                                           make_room):
    room = make_room(scene, 0, 0, 240, 240, "Kitchen")
    room.properties["style"] = {"cabinet_finish": "zebrawood", "future": "x"}
    dlg = RoomPropertiesDialog(room, None)
    assert dlg._style_boxes["cabinet_finish"].currentData() == "zebrawood"
    dlg.apply()
    assert room.properties["style"] == {"cabinet_finish": "zebrawood",
                                        "future": "x"}
    dlg.deleteLater()


# -- the document --------------------------------------------------------------
@pytest.mark.io
def test_style_and_cabinet_state_reach_the_document(fp, qapp, win, make_room):
    room = make_room(win.scene, 0, 0, 240, 240, "Kitchen")
    room.properties["style"] = {"cabinet_finish": "oak", "countertop": "marble"}
    it = fp.make_furnishing("base_cab_36", QPointF(120, 120))
    win.scene.addItem(it)
    it.apply_params({"width_in": 30.0})
    plain = fp.make_furnishing("base_cab_24", QPointF(60, 60))
    win.scene.addItem(plain)
    doc = win.snapshot()
    rooms = [r for r in doc["rooms"] if r["name"] == "Kitchen"]
    assert len(rooms) == 1
    assert rooms[0]["properties"]["style"] == {"cabinet_finish": "oak",
                                               "countertop": "marble"}
    recs = {f["kind"]: f for f in doc["furnishings"]}
    assert recs["base_cab_36"]["state"] == {"width_in": 30.0}
    assert "state" not in recs["base_cab_24"], "untouched: no state written"
    assert recs["base_cab_36"]["room"] == rooms[0]["id"]


def test_a_cabinet_edit_is_one_undo_step(fp, qapp, win):
    it = fp.make_furnishing("base_cab_36", QPointF(60, 60))
    win.scene.addItem(it)
    win._commit_if_changed()
    it.apply_params({"width_in": 42.0})
    win._commit_if_changed()
    assert _cabinets(win, fp, "base_cab_36")[0].w == 42.0
    win.undo()
    back = _cabinets(win, fp, "base_cab_36")
    assert len(back) == 1 and back[0].w == 36.0 and back[0].params is None


# -- 0333: the island, lights -----------------------------------------------------
def test_island_slots_resize_the_item_and_round_trip(fp, qapp):
    it = fp.make_furnishing("kitchen_island", QPointF(0, 0))
    assert (it.w, it.d) == (72.0, 39.0) and it.params is None
    dlg = it.make_properties_dialog()
    assert not dlg._widgets["width_in"].isEnabled(), "the length is derived"
    slot = dlg._widgets["slot_1"]
    slot.setCurrentIndex(slot.findData("DW24"))
    assert dlg._derived["footprint"] == (60.0, 39.0)
    assert dlg._widgets["width_in"].value() == pytest.approx(60.0)
    dlg._widgets["seats"].setValue(2)
    assert dlg.try_accept()
    it.apply_params(dlg.result_state())
    assert it.extra_state() == {"seats": 2, "slot_1": "DW24"}
    assert (it.w, it.d) == (60.0, 39.0)
    again = fp.make_furnishing("kitchen_island", QPointF(0, 0), 0.0, it.extra_state())
    assert (again.w, again.d) == (60.0, 39.0)
    dlg.deleteLater()


def test_a_light_reads_its_rooms_ceiling(fp, qapp, scene, make_room):
    room = make_room(scene, 0, 0, 240, 240, "Kitchen")
    room.properties["ceiling_height_in"] = 108.0
    it = fp.make_furnishing("light_pendant", QPointF(120, 120))
    scene.addItem(it)
    assert it.param_context()["ceiling_in"] == 108.0
    dlg = it.make_properties_dialog()
    assert dlg._derived["light"]["lumens"] == 800.0
    assert max(p.z1 for p in dlg._derived["parts"]) == pytest.approx(108.0)
    colour = dlg._widgets["light_colour"]
    colour.setCurrentIndex(colour.findData("blue"))
    assert dlg._derived["materials"]["lens"] == "light_emit#5a8cff"
    assert dlg.try_accept()
    it.apply_params(dlg.result_state())
    assert it.extra_state() == {"light_colour": "blue"}
    dlg.deleteLater()


def test_the_washer_dialog_offers_three_gloss_colours(fp, qapp):
    it = fp.make_furnishing("washer", QPointF(0, 0))
    dlg = it.make_properties_dialog()
    box = dlg._widgets["colour"]
    assert [box.itemData(i) for i in range(box.count())] == ["white", "silver",
                                                             "black"]
    box.setCurrentIndex(box.findData("black"))
    assert dlg.try_accept()
    it.apply_params(dlg.result_state())
    assert it.extra_state() == {"colour": "black"}
    dlg.deleteLater()


# -- 0338: fixtures, and the island's own plan symbol --------------------------
def _painted(scene, item):
    """Paint the scene to an image; the count of non-white pixels."""
    from PyQt6.QtGui import QColor, QImage, QPainter
    img = QImage(240, 240, QImage.Format.Format_ARGB32)
    img.fill(QColor(255, 255, 255))
    p = QPainter(img)
    scene.render(p, source=item.sceneBoundingRect().adjusted(-4, -4, 4, 4))
    p.end()
    return sum(1 for x in range(0, 240, 3) for y in range(0, 240, 3)
               if img.pixelColor(x, y).lightness() < 235)


def test_an_island_paints_its_own_symbol_and_the_seats_change_it(fp, qapp, scene):
    it = fp.make_furnishing("kitchen_island", QPointF(200, 200))
    scene.addItem(it)
    none = fp.make_furnishing("kitchen_island", QPointF(600, 200))
    none.apply_params({"seats": 0})
    scene.addItem(none)
    with_stools, bare = _painted(scene, it), _painted(scene, none)
    assert bare > 0, "the island draws without its catalog SVG"
    assert with_stools > bare, "three stools add ink"
    it.apply_params({"seats": 6, "slot_3": "RG30"})
    assert it.w == 72.0 + 30.0
    assert _painted(scene, it) > 0


@pytest.mark.parametrize("kind", ["toilet", "bathtub", "bookshelf",
                                  "gas_fireplace", "grab_bar", "desk",
                                  "office_chair", "office_set", "pedal_bin",
                                  "dog_crate", "sofa_table"])
def test_a_fixture_opens_a_dialog_and_accepts_unchanged(fp, qapp, kind):
    it = fp.make_furnishing(kind, QPointF(0, 0))
    assert it.is_parametric() and it.extra_state() == {}
    dlg = it.make_properties_dialog()
    assert dlg.windowTitle() == "Fixture Properties"
    assert dlg._derived["parts"]
    assert dlg.try_accept()
    it.apply_params(dlg.result_state())
    assert it.extra_state() == {}
    dlg.deleteLater()


def test_a_grab_bar_turned_upright_changes_its_footprint(fp, qapp):
    it = fp.make_furnishing("grab_bar", QPointF(0, 0))
    assert (it.w, it.d) == (24.0, 3.5)
    it.apply_params({"bar": "vertical", "length_in": 36.0})
    assert (it.w, it.d) == (3.0, 3.5)
    assert it.extra_state() == {"bar": "vertical", "length_in": 36.0}
