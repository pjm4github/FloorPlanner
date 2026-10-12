"""0263-report.md: ANNOTATIONS, MEASUREMENTS, ITEM CALLOUTS and the SHOW MENU
(Patrick's four: "1) ... place annotations (text) on the drawing, 2) ...
draw a dimension measurement that can snap to an item ... a single thin
solid line with slash marks ... selectable as feet and inches or in
inches ... parallel to the item being measured ... a datum ..., 3) ... show
the items (the callouts of each wall, vitext, etc.) ... in a settable color
(default = blue). 4) ... menu items that are checkable from the 'show'
menu ... independently checked").
"""
import json

import pytest
from PyQt6.QtCore import QEvent, QPointF, Qt
from PyQt6.QtGui import QMouseEvent
from PyQt6.QtWidgets import QApplication, QInputDialog

from floorplanner.annotations import (
    DatumItem, DimensionItem, TextAnnotationItem, callout_colour, datum_on,
    format_length, sync_annotation_visibility,
)
from floorplanner.config import SETTINGS
from floorplanner.design.bridge import apply_design_to_scene, design_from_scene
from floorplanner.design.validate import schema_errors

pytestmark = pytest.mark.walls

LEFT, NONE = Qt.MouseButton.LeftButton, Qt.MouseButton.NoButton


def _send(win, etype, p, button, buttons):
    vp = win.view.viewport()
    pos = win.view.mapFromScene(QPointF(*p))
    QApplication.sendEvent(vp, QMouseEvent(
        etype, QPointF(pos), QPointF(vp.mapToGlobal(pos)), button, buttons,
        Qt.KeyboardModifier.NoModifier))


def _drag(win, a, b):
    _send(win, QEvent.Type.MouseButtonPress, a, LEFT, LEFT)
    _send(win, QEvent.Type.MouseMove, b, NONE, LEFT)
    _send(win, QEvent.Type.MouseButtonRelease, b, LEFT, NONE)


def _click(win, p):
    _send(win, QEvent.Type.MouseButtonPress, p, LEFT, LEFT)
    _send(win, QEvent.Type.MouseButtonRelease, p, LEFT, NONE)


def _annots(scene, cls):
    return [it for it in scene.items() if isinstance(it, cls)]


# ---------------------------------------------------------------------------
# the items and the document
# ---------------------------------------------------------------------------

def test_the_three_kinds_round_trip_through_the_document(fp, scene):
    scene.addItem(TextAnnotationItem(QPointF(100, 200), "North elevation", rotation=0.0))
    scene.addItem(DimensionItem(QPointF(0, 0), QPointF(240, 0), offset_in=-24.0))
    scene.addItem(DatumItem(QPointF(12, 36)))
    out = design_from_scene(scene).to_dict()
    assert schema_errors(out) == []
    kinds = sorted(a["kind"] for a in out["annotations"])
    assert kinds == ["datum", "dimension", "text"]
    dim = next(a for a in out["annotations"] if a["kind"] == "dimension")
    assert dim["pos"] == [0.0, 0.0] and dim["p2"] == [240.0, 0.0] and dim["offset_in"] == -24.0
    text = next(a for a in out["annotations"] if a["kind"] == "text")
    assert text["text"] == "North elevation" and text["pos"] == [100.0, 200.0]
    scene.clear()
    apply_design_to_scene(scene, out)
    assert len(_annots(scene, TextAnnotationItem)) == 1
    d = _annots(scene, DimensionItem)[0]
    assert (d.a, d.b, d.offset_in) == (QPointF(0, 0), QPointF(240, 0), -24.0)
    assert datum_on(scene, d.floor) is not None
    # no annotations: no key (the block is optional in the schema)
    scene.clear()
    assert "annotations" not in design_from_scene(scene).to_dict()


def test_a_measure_writes_its_length_in_the_plans_units():
    assert format_length(30.5) == "2'-6 1/2\""
    SETTINGS["dimension_units"] = "in"
    try:
        assert format_length(30.5) == "30.5\""
        assert DimensionItem(QPointF(0, 0), QPointF(0, 30.5)).label() == "30.5\""
    finally:
        SETTINGS["dimension_units"] = "ftin"


def test_the_dimension_line_is_parallel_and_offset_to_its_left(fp):
    d = DimensionItem(QPointF(0, 0), QPointF(100, 0), offset_in=18.0)
    p, q = d.line_points()
    # the left normal of +x is +y in the scene's frame (y down on screen)
    assert (p.x(), p.y()) == (0.0, 18.0) and (q.x(), q.y()) == (100.0, 18.0)
    d.set_offset(-12.0)
    p, q = d.line_points()
    assert p.y() == -12.0 and q.y() == -12.0 and d.length() == 100.0


# ---------------------------------------------------------------------------
# the tools, through the view
# ---------------------------------------------------------------------------

def test_the_annotation_tool_places_a_text_at_the_click(fp, win, monkeypatch):
    win.prepare_headless()
    monkeypatch.setattr(QInputDialog, "getText", staticmethod(lambda *a, **k: ("Entry", True)))
    win.set_tool(fp.TOOL_TEXT)
    _click(win, (300.0, 300.0))
    texts = _annots(win.scene, TextAnnotationItem)
    assert len(texts) == 1 and texts[0].text == "Entry"
    assert texts[0].pos() == QPointF(300.0, 300.0)
    assert texts[0].floor == fp.active_floor()
    # delete removes it
    texts[0].setSelected(True)
    win.delete_selected()
    assert not _annots(win.scene, TextAnnotationItem)


def test_the_measure_tool_snaps_to_corners_and_runs_along_one_wall(fp, win, add_walls):
    win.prepare_headless()
    add_walls(win.scene, 120, 120, 240, 180)          # a room 120..360 x 120..300
    win.set_tool(fp.TOOL_MEASURE)
    # from near the NW corner to near the NE corner: both snap to the corners
    _drag(win, (122.0, 118.0), (357.0, 123.0))
    dims = _annots(win.scene, DimensionItem)
    assert len(dims) == 1
    d = dims[0]
    assert (d.a, d.b) == (QPointF(120, 120), QPointF(360, 120))
    assert d.length() == 240.0 and d.label() == "20'-0\""
    # a press-release with no drag leaves nothing behind
    _click(win, (200.0, 200.0))
    assert len(_annots(win.scene, DimensionItem)) == 1
    # both ends on the body of one wall: the measure runs along that wall,
    # whatever the cursor's wobble across it
    _drag(win, (150.0, 121.5), (330.0, 118.5))
    d2 = [x for x in _annots(win.scene, DimensionItem) if x is not d][0]
    assert d2.a.y() == pytest.approx(120.0) and d2.b.y() == pytest.approx(120.0)
    assert d2.length() == pytest.approx(180.0)


def test_the_datum_is_one_per_level_and_a_measure_snaps_to_it(fp, win):
    win.prepare_headless()
    win.set_tool(fp.TOOL_DATUM)
    _click(win, (240.0, 240.0))
    assert datum_on(win.scene, fp.active_floor()).pos() == QPointF(240.0, 240.0)
    assert win.tool == fp.TOOL_SELECT, "placing the datum hands the tool back"
    win.set_tool(fp.TOOL_DATUM)
    _click(win, (300.0, 240.0))
    datums = _annots(win.scene, DatumItem)
    assert len(datums) == 1 and datums[0].pos() == QPointF(300.0, 240.0)
    win.set_tool(fp.TOOL_MEASURE)
    _drag(win, (302.0, 241.0), (420.0, 240.0))
    d = _annots(win.scene, DimensionItem)[0]
    assert d.a == QPointF(300.0, 240.0), "the first end snapped to the datum"


# ---------------------------------------------------------------------------
# the Show menu and the callouts
# ---------------------------------------------------------------------------

def test_the_show_switches_hide_each_kind_independently(fp, win):
    win.prepare_headless()
    t = TextAnnotationItem(QPointF(10, 10), "a")
    d = DimensionItem(QPointF(0, 0), QPointF(50, 0))
    z = DatumItem(QPointF(5, 5))
    for it in (t, d, z):
        win.scene.addItem(it)
    sync_annotation_visibility(win.scene)
    assert t.isVisible() and d.isVisible() and z.isVisible()
    win.a_show_annotations.setChecked(False)
    assert not t.isVisible() and d.isVisible() and z.isVisible()
    assert SETTINGS["show_annotations"] is False
    win.a_show_dimensions.setChecked(False)
    assert not d.isVisible() and not z.isVisible()
    win.a_show_annotations.setChecked(True)
    assert t.isVisible() and not d.isVisible()
    win.a_show_dimensions.setChecked(True)
    assert d.isVisible() and z.isVisible()
    # the switches ride in the document's settings and come back on a load
    assert win.a_show_callouts.isChecked(), "item callouts are on (0264: how a reported problem is found)"
    win.a_show_callouts.setChecked(False)
    doc = design_from_scene(win.scene).to_dict()
    assert doc["settings"]["show_callouts"] is False and doc["settings"]["show_annotations"] is True
    assert schema_errors(doc) == []
    win.a_show_callouts.setChecked(True)


def test_the_units_switch_and_the_callout_colour_are_plan_settings(fp, win):
    win.prepare_headless()
    assert callout_colour().name() == "#005ac8", "blue by default"
    win.a_dim_ftin.setChecked(False)
    assert SETTINGS["dimension_units"] == "in"
    win.a_dim_ftin.setChecked(True)
    assert SETTINGS["dimension_units"] == "ftin"
    SETTINGS["callout_color"] = "#aa0000"
    try:
        assert callout_colour().name() == "#aa0000"
        doc = design_from_scene(win.scene).to_dict()
        assert doc["settings"]["callout_color"] == "#aa0000"
        assert schema_errors(doc) == []
    finally:
        SETTINGS["callout_color"] = "#005AC8"
    SETTINGS["callout_color"] = "not a colour"
    try:
        assert callout_colour().isValid(), "a malformed setting falls back, never a blank ink"
    finally:
        SETTINGS["callout_color"] = "#005AC8"


def _ink_pixels(item, ink, size=400, shift=(-100, -100)):
    from PyQt6.QtGui import QImage, QPainter
    from PyQt6.QtWidgets import QStyleOptionGraphicsItem
    img = QImage(size, size, QImage.Format.Format_ARGB32)
    img.fill(0xFFFFFFFF)
    p = QPainter(img)
    p.translate(*shift)
    item.paint(p, QStyleOptionGraphicsItem())
    p.end()
    key = ink.rgb() & 0xFFFFFF
    return sum(1 for x in range(size) for y in range(size) if (img.pixel(x, y) & 0xFFFFFF) == key)


def test_the_wall_callout_is_its_session_label_in_the_ink_while_items_are_shown(fp, scene, add_walls):
    """0265 (his word): the callouts are the SESSION LABELS -- `W7`, `V12` --
    always; the file's id beside a label only while the Malformed-design
    report is open and the two differ. An unselected wall paints its label
    in the callout colour while the layer is on, nothing while it is off."""
    from floorplanner.annotations import callout_text, callouts_shown, session_label, set_report_open
    add_walls(scene, 120, 120, 240, 180)
    wall = next(w for w in scene.items() if isinstance(w, fp.WallItem))
    assert callouts_shown(), "on by default"
    lab = session_label(wall)
    assert lab.startswith("W") and lab[1:].isdigit()
    wall.name = "North wall"
    assert callout_text(wall) == f"{lab}  North wall"
    # a stamped document id that matches the label (the open-time case) adds nothing
    wall.doc_id = lab.lower()
    set_report_open(True)
    try:
        assert callout_text(wall) == f"{lab}  North wall"
        wall.doc_id = "w999"                   # the two differ: both, while the report is open
        assert callout_text(wall) == f"{lab} (w999)  North wall"
    finally:
        set_report_open(False)
    assert callout_text(wall) == f"{lab}  North wall", "the report closed: the label alone"
    wall.name = None
    assert _ink_pixels(wall, callout_colour()) > 0, "the label is painted in the callout colour"
    SETTINGS["show_callouts"] = False
    try:
        assert _ink_pixels(wall, callout_colour()) == 0, "switched off, an unselected wall paints no callout"
    finally:
        SETTINGS["show_callouts"] = True


def test_a_load_adopts_the_files_ids_as_the_session_labels(fp, scene, add_walls):
    """When a plan opens, the file's ids ARE the session labels (`w7` ->
    `W7`), for walls, corners, openings, rooms, furnishings and roofs, and
    the counters are kept past them so a new item never collides."""
    from floorplanner import labels
    from floorplanner.annotations import session_label
    add_walls(scene, 120, 120, 240, 180)
    w = next(x for x in scene.items() if isinstance(x, fp.WallItem))
    w.openings.append(fp.OpeningItem(w, "window", "3648", 120.0))
    fp.rebuild_all_walls(scene)
    doc = design_from_scene(scene).to_dict()
    from PyQt6.QtWidgets import QGraphicsScene
    scene2 = QGraphicsScene()
    apply_design_to_scene(scene2, doc)
    walls = [x for x in scene2.items() if isinstance(x, fp.WallItem)]
    assert {session_label(x) for x in walls} == {x["id"].upper() for x in doc["walls"]}
    corners = {session_label(x.end_vertex(a)) for x in walls for a in ("p1", "p2")}
    assert corners == {v["id"].upper() for v in doc["vertices"]}
    ops = [o for x in walls for o in x.openings]
    assert [session_label(o) for o in ops] == [o["id"].upper() for x in doc["walls"] for o in x["openings"]]
    # the counters sit past every adopted number: a fresh wall does not collide
    fresh = fp.WallItem(QPointF(0, 600), QPointF(100, 600), "interior")
    scene2.addItem(fresh)
    assert session_label(fresh) not in {session_label(x) for x in walls}
    assert labels.adopt("W", "wall_3").startswith("W"), "another tool's id: a fresh label"
    assert labels.matches("W7", "w7") and not labels.matches("W7", "w8")


def test_the_report_says_the_session_labels_and_still_zooms(fp, win, add_walls):
    """0265: the Malformed-design report's rows are translated from the
    validator's document ids to the session labels the screen shows; the
    zoom resolves the original. While it is open, a callout whose label
    differs from the file's id shows both; closed, the label alone."""
    from floorplanner.annotations import REPORT
    from floorplanner.problems import DesignProblemsDialog
    win.prepare_headless()
    add_walls(win.scene, 120, 120, 240, 180)
    doc = win.design_document()
    win.load_data(doc)                      # stamps doc ids and adopts the labels
    w = next(x for x in win.scene.items() if isinstance(x, fp.WallItem))
    wid = w.doc_id if isinstance(w.doc_id, str) else w.doc_id[0]
    w._uid = "W77"                           # a label the file does not carry
    msg = f"I7  opening o9 runs off wall {wid} (5.0..185.0 of 180.0)"
    dlg = DesignProblemsDialog(win, "Malformed design file", "1 violation", [msg], doc)
    assert dlg.messages == [msg], "the validator's own text is kept for the zoom"
    assert dlg.shown_messages == [msg.replace(wid, "W77")]
    dlg.show()
    assert REPORT["open"] is True
    assert dlg.zoom_to_current() is None, "no row selected yet: nothing to zoom to"
    dlg.list.setCurrentRow(0)
    spot = dlg.zoom_to_current()
    assert spot is not None and wid in spot.found
    dlg.close()
    assert REPORT["open"] is False


def test_the_document_ids_are_stamped_on_a_load_and_by_every_settle(fp, win, add_walls):
    """A loaded plan's items carry the file's own ids; after an edit the
    settle's walk re-stamps them with the ids the next save writes -- the
    ones the validator's report names."""
    from PyQt6.QtWidgets import QGraphicsScene

    from floorplanner.design.bridge import stamp_document_ids
    win.prepare_headless()
    add_walls(win.scene, 120, 120, 240, 180)
    ids = {}
    state = win.snapshot(ids_out=ids)
    stamp_document_ids(win.scene, ids)
    walls = [w for w in win.scene.items() if isinstance(w, fp.WallItem)]
    doc_ids = {w["id"] for w in state["walls"]}
    stamped = set()
    for w in walls:
        d = w.doc_id
        stamped |= set(d) if isinstance(d, list) else {d}
    assert stamped and stamped <= doc_ids, (stamped, doc_ids)
    v = walls[0].end_vertex("p1")
    assert v.doc_id in {x["id"] for x in state["vertices"]}
    # a load stamps the file's own ids, which the report would name
    doc = design_from_scene(win.scene).to_dict()
    scene2 = QGraphicsScene()
    apply_design_to_scene(scene2, doc)
    w2 = next(w for w in scene2.items() if isinstance(w, fp.WallItem))
    assert w2.doc_id in {w["id"] for w in doc["walls"]}
    assert w2.end_vertex("p1").doc_id in {x["id"] for x in doc["vertices"]}


def test_item_callouts_are_on_whenever_a_plan_is_opened(fp, win, tmp_path, add_walls):
    """0264: "This should be enabled when the plan is opened. The user can
    then uncheck it later." -- a file saved with the layer off opens with
    it on."""
    win.prepare_headless()
    add_walls(win.scene, 120, 120, 240, 180)
    SETTINGS["show_callouts"] = False
    doc = win.design_document()
    assert doc["settings"]["show_callouts"] is False
    path = tmp_path / "off.json"
    path.write_text(json.dumps(doc), encoding="utf-8")
    win.load_path(str(path))
    assert SETTINGS["show_callouts"] is True
    assert win.a_show_callouts.isChecked()


# ---------------------------------------------------------------------------
# the measure's gadget (0264): four knobs
# ---------------------------------------------------------------------------

def test_a_selected_measure_shows_four_knobs_and_its_bounds_are_tight(fp, scene):
    from floorplanner.annotations import DimensionKnob
    d = DimensionItem(QPointF(0, 0), QPointF(240, 0), offset_in=18.0)
    scene.addItem(d)
    knobs = [k for k in d.childItems() if isinstance(k, DimensionKnob)]
    assert [k.kind for k in knobs] == ["a", "b", "end", "label"]
    assert not any(k.isVisible() for k in knobs)
    d.setSelected(True)
    assert all(k.isVisible() for k in knobs)
    assert knobs[0].pos() == QPointF(0, 0) and knobs[1].pos() == QPointF(240, 0)
    assert knobs[2].pos() == QPointF(240, 18) and knobs[3].pos() == QPointF(120, 18)
    r = d.boundingRect()
    assert r.left() > -10 and r.right() < 250 and r.top() >= -10 and r.bottom() <= 30, r


def test_knobs_one_and_two_move_their_callout_point(fp, scene, add_walls):
    add_walls(scene, 120, 120, 240, 180)
    d = DimensionItem(QPointF(0, 0), QPointF(240, 0))
    scene.addItem(d)
    d.move_point(1, QPointF(300, 0), free=True)
    assert d.b == QPointF(300, 0) and d.a == QPointF(0, 0)
    d.move_point(0, QPointF(10, 40), free=True)
    assert d.a == QPointF(10, 40)
    # without Shift the point snaps as the tool does (no view here: the cursor)
    d.move_point(0, QPointF(122, 118))
    assert d.a == QPointF(122, 118)


def test_ctrl_on_a_knob_rotates_the_measure_about_the_other_knob_on_the_snap(fp, scene):
    import math
    d = DimensionItem(QPointF(100, 100), QPointF(340, 100), offset_in=18.0)
    scene.addItem(d)
    # knob 1 dragged with Ctrl: the measure turns about knob 2 (b), length kept,
    # the angle on the 15-degree step -- 50 degrees asked, 45 given
    ang = math.radians(180 + 50)
    d.rotate_about(1, QPointF(340 + math.cos(ang) * 100, 100 + math.sin(ang) * 100))
    assert d.b == QPointF(340, 100), "knob 2 is the anchor"
    assert d.length() == pytest.approx(240.0), "the length is kept"
    got = math.degrees(math.atan2(d.a.y() - d.b.y(), d.a.x() - d.b.x())) % 360
    assert got == pytest.approx(225.0), got
    assert d.offset_in == 18.0, "the anchored callout keeps its length and stays orthogonal"
    # knob 2 with Ctrl: the roles flip, knob 1 anchors
    a0 = QPointF(d.a)
    d.rotate_about(0, QPointF(a0.x() + 240, a0.y() + 1))
    assert d.a == a0 and d.b.y() == pytest.approx(a0.y()) and d.length() == pytest.approx(240.0)
    # Shift: a free angle
    d.rotate_about(0, QPointF(a0.x() + 100, a0.y() + 50), free=True)
    got = math.degrees(math.atan2(d.b.y() - d.a.y(), d.b.x() - d.a.x()))
    assert got == pytest.approx(math.degrees(math.atan2(50, 100)))


def test_knob_three_slides_the_end_along_the_line_and_knob_four_slides_the_label(fp, scene):
    d = DimensionItem(QPointF(0, 0), QPointF(240, 0), offset_in=18.0)
    scene.addItem(d)
    d.slide_end(QPointF(300, 50))             # along the line: the projection, on the grid
    assert d.b == QPointF(300, 0) and d.a == QPointF(0, 0) and d.offset_in == 18.0
    d.slide_label(QPointF(75, 18))
    assert d.label_t == pytest.approx(0.25)
    assert d.label_point() == QPointF(75, 18)
    d.slide_label(QPointF(-50, 0))             # clamped onto the line
    assert d.label_t == 0.05
    rec = d.to_record("an1", "L1")
    assert rec["label_t"] == 0.05
    back = DimensionItem.from_record(rec, d.floor)
    assert back.label_t == 0.05 and back.b == QPointF(300, 0)


def test_the_house_model_file_with_annotations_validates(fp, scene):
    """A document carrying every kind, written out and read by the checker."""
    scene.addItem(TextAnnotationItem(QPointF(1, 2), "x"))
    scene.addItem(DimensionItem(QPointF(0, 0), QPointF(0, 96), 12.0))
    scene.addItem(DatumItem(QPointF(0, 0)))
    doc = design_from_scene(scene).to_dict()
    text = json.dumps(doc)
    assert '"annotations"' in text and schema_errors(json.loads(text)) == []
