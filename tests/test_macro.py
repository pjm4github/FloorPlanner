"""Headless macro language (MainWindow.run_macro / MacroRunner) plus the
SVG/PNG canvas-export hooks that the fp_macro.py driver relies on."""
import json

import pytest

pytestmark = pytest.mark.macro


def _counts(win):
    s = win.scene_summary()["counts"]
    return s["walls"], s["rooms"], s["furnishings"]


def test_place_adds_furnishing_at_scene_inches(fp, win):
    res = win.run_macro("PLACE sofa 120 96 0")
    assert res["ok"], res["errors"]
    furn = [it for it in win.scene.items() if isinstance(it, fp.FurnishingItem)]
    assert len(furn) == 1
    assert furn[0].kind == "sofa"
    # pos is the centre, in scene inches
    assert (furn[0].pos().x(), furn[0].pos().y()) == pytest.approx((120, 96))


def test_place_rejects_unknown_kind(fp, win):
    res = win.run_macro("PLACE not_a_real_thing 10 10")
    assert not res["ok"]
    assert res["errors"] and "unknown furnishing" in res["errors"][0]
    assert _counts(win)[2] == 0


def test_wall_and_room_build_and_bind(fp, win):
    macro = ("WALL 0 0 240 0 ext  WALL 240 0 240 180 ext "
             "WALL 240 180 0 180 ext  WALL 0 180 0 0 ext  ROOM Den 120 90")
    res = win.run_macro(macro)
    assert res["ok"], res["errors"]
    w, r, _ = _counts(win)
    assert (w, r) == (4, 1)
    room = next(it for it in win.scene.items() if isinstance(it, fp.RoomItem))
    assert room.name == "Den"
    assert len(room.walls) == 4            # the room owns its enclosing walls


def test_door_cuts_the_wall(fp, win):
    win.run_macro("WALL 0 0 240 0 ext")
    res = win.run_macro("DOOR 120 0 3680")
    assert res["ok"], res["errors"]
    wall = next(it for it in win.scene.items() if isinstance(it, fp.WallItem))
    assert len(wall.openings) == 1
    assert wall.openings[0].kind == "door"


def test_quoted_room_name_with_space(fp, win):
    macro = ('WALL 0 0 120 0 int WALL 120 0 120 120 int '
             'WALL 120 120 0 120 int WALL 0 120 0 0 int '
             'ROOM "Living Room" 60 60')
    res = win.run_macro(macro)
    assert res["ok"], res["errors"]
    room = next(it for it in win.scene.items() if isinstance(it, fp.RoomItem))
    assert room.name == "Living Room"


def test_select_copy_paste_adds_a_copy(fp, win):
    win.run_macro("PLACE sofa 120 96 0")
    res = win.run_macro("SELECT 120 96  MOVE 240 96  ^C  ^V")
    assert res["ok"], res["errors"]
    assert _counts(win)[2] == 2            # original + pasted copy


def test_select_prefers_furnishing_over_room(fp, win):
    # a room label sits at the anchor; SELECT there must grab the furnishing
    macro = ("WALL 0 0 240 0 ext WALL 240 0 240 180 ext "
             "WALL 240 180 0 180 ext WALL 0 180 0 0 ext "
             "ROOM Den 120 90 PLACE sofa 120 90 0")
    win.run_macro(macro)
    win.run_macro("SELECT 120 90")
    sel = win.scene.selectedItems()
    assert len(sel) == 1
    assert isinstance(sel[0], fp.FurnishingItem)


def test_arrow_nudge_moves_selection(fp, win):
    win.run_macro("PLACE sofa 120 96 0  SELECT 120 96")
    step = fp.SETTINGS["wall_snap_in"]
    win.run_macro("RIGHT")
    furn = next(it for it in win.scene.items()
                if isinstance(it, fp.FurnishingItem))
    assert furn.pos().x() == pytest.approx(120 + step)
    # fine nudge with the caret prefix uses the 1" step
    win.run_macro("^DOWN")
    assert furn.pos().y() == pytest.approx(96 + fp.SNAP_STEP)


def test_rotate_and_delete(fp, win):
    win.run_macro("PLACE sofa 120 96 0  SELECT 120 96  ROTATE 90")
    furn = next(it for it in win.scene.items()
                if isinstance(it, fp.FurnishingItem))
    assert furn.rotation() == pytest.approx(90)
    win.run_macro("SELECT 120 96  DEL")
    assert _counts(win)[2] == 0


def test_tool_digit_switches_tool(fp, win):
    win.run_macro("2")
    assert win.tool == fp.TOOL_WALL_EXT
    win.run_macro("1")
    assert win.tool == fp.TOOL_SELECT


def test_drag_draws_a_wall_via_synthesized_mouse(fp, win):
    win.prepare_headless()
    before = _counts(win)[0]
    win.run_macro("2  DRAG 24 24 240 24")     # exterior-wall tool, then drag
    assert _counts(win)[0] == before + 1


def test_unknown_token_is_recorded_not_fatal(fp, win):
    res = win.run_macro("PLACE sofa 10 10  FLOOGLE  PLACE armchair 50 50")
    assert not res["ok"]
    assert any("FLOOGLE" in e for e in res["errors"])
    assert _counts(win)[2] == 2               # both PLACEs still ran


def test_open_save_roundtrip(fp, win, tmp_path):
    p = tmp_path / "plan.json"
    win.run_macro(f'PLACE sofa 120 96 0  SAVE "{p}"')
    assert p.exists()
    data = json.loads(p.read_text(encoding="utf-8"))
    assert data["furnishings"][0]["kind"] == "sofa"
    win.run_macro("NEW")
    assert _counts(win) == (0, 0, 0)
    win.run_macro(f'OPEN "{p}"')
    assert _counts(win)[2] == 1


def test_shot_writes_png_and_svg(fp, win, tmp_path):
    win.run_macro("PLACE sofa 120 96 0")
    png, svg = tmp_path / "s.png", tmp_path / "s.svg"
    res = win.run_macro(f'SHOT "{png}"  SHOT "{svg}"')
    assert res["ok"], res["errors"]
    assert png.exists() and png.stat().st_size > 0
    assert svg.exists() and svg.read_text(encoding="utf-8").startswith("<?xml")


def test_export_canvas_png_dimensions(fp, win, tmp_path):
    from PyQt6.QtGui import QImage
    win.run_macro("WALL 0 0 240 0 ext WALL 240 0 240 120 ext")
    out = tmp_path / "c.png"
    assert win.export_canvas(str(out), scale=2.0)
    img = QImage(str(out))
    assert not img.isNull()
    assert img.width() > 0 and img.height() > 0


def test_scene_summary_has_counts_and_model(fp, win):
    win.run_macro("PLACE sofa 0 0 0  PLACE armchair 60 60 0")
    summ = win.scene_summary()
    assert summ["counts"]["furnishings"] == 2
    assert summ["format"] == "floorplanner-json"
    assert len(summ["furnishings"]) == 2


def test_feet_inches_coordinates(fp, win):
    win.run_macro("PLACE sofa 10' 8' 0")      # 120in x 96in
    furn = next(it for it in win.scene.items()
                if isinstance(it, fp.FurnishingItem))
    assert (furn.pos().x(), furn.pos().y()) == pytest.approx((120, 96))
