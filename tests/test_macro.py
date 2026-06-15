"""Headless macro language (MainWindow.run_macro / MacroRunner) plus the
SVG/PNG canvas-export hooks that the fp_macro.py driver relies on, and the
non-modal MacroRecorderDialog (record / replay / save)."""
import json

import pytest
from PyQt6.QtCore import QEvent, QPointF, Qt
from PyQt6.QtGui import QMouseEvent

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


def test_tool_code_switches_tool(fp, win):
    win.run_macro("E")                        # Exterior-wall
    assert win.tool == fp.TOOL_WALL_EXT
    win.run_macro("S")                        # Select
    assert win.tool == fp.TOOL_SELECT
    win.run_macro("R")                        # Room
    assert win.tool == fp.TOOL_ROOM


def test_legacy_digit_tool_still_works(fp, win):
    win.run_macro("2")                        # legacy exterior-wall code
    assert win.tool == fp.TOOL_WALL_EXT


def test_drag_draws_a_wall_via_synthesized_mouse(fp, win):
    win.prepare_headless()
    before = _counts(win)[0]
    win.run_macro("E  DRAG 24 24 240 24")     # exterior-wall tool, then drag
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


# --------------------------------------------------------------------------
# Macro recorder dialog
# --------------------------------------------------------------------------
def _send_mouse(win, etype, sx, sy, button, buttons):
    from PyQt6.QtWidgets import QApplication
    vp = win.view.viewport()
    pos = win.view.mapFromScene(QPointF(sx, sy))
    ev = QMouseEvent(etype, QPointF(pos), QPointF(vp.mapToGlobal(pos)),
                     button, buttons, Qt.KeyboardModifier.NoModifier)
    QApplication.sendEvent(vp, ev)


def test_recorder_tool_and_place_hooks(fp, win):
    dlg = fp.MacroRecorderDialog(win)
    dlg.start()
    win.set_tool(fp.TOOL_WALL_EXT)                 # -> "E"
    dlg.on_place("sofa", QPointF(120, 96))         # -> PLACE sofa 120 96
    dlg.stop()
    text = dlg.edit.toPlainText()
    assert "E" in text.split()
    assert "PLACE sofa 120 96" in text
    assert win._recorder is None                   # stop unhooks the recorder


def test_recorder_ignores_when_not_started_or_paused(fp, win):
    dlg = fp.MacroRecorderDialog(win)
    win.set_tool(fp.TOOL_DOOR)                      # not recording -> nothing
    assert dlg.edit.toPlainText() == ""
    dlg.start()
    dlg.toggle_pause()                             # paused -> still nothing
    win.set_tool(fp.TOOL_WINDOW)
    assert dlg.edit.toPlainText() == ""
    dlg.toggle_pause()                            # resume
    win.set_tool(fp.TOOL_ROOM)                     # -> "R"
    dlg.stop()
    assert dlg.edit.toPlainText().split() == ["R"]


def test_recorder_captures_live_drag(fp, win):
    win.prepare_headless()
    dlg = fp.MacroRecorderDialog(win)
    dlg.start()
    win.set_tool(fp.TOOL_WALL_EXT)
    left = Qt.MouseButton.LeftButton
    _send_mouse(win, QEvent.Type.MouseButtonPress, 24, 24, left, left)
    _send_mouse(win, QEvent.Type.MouseMove, 130, 24,
                Qt.MouseButton.NoButton, left)
    _send_mouse(win, QEvent.Type.MouseButtonRelease, 240, 24, left,
                Qt.MouseButton.NoButton)
    dlg.stop()
    assert "DRAG" in dlg.edit.toPlainText()


def test_recorder_short_click_is_click_not_drag(fp, win):
    win.prepare_headless()
    dlg = fp.MacroRecorderDialog(win)
    dlg.start()
    left = Qt.MouseButton.LeftButton
    _send_mouse(win, QEvent.Type.MouseButtonPress, 60, 60, left, left)
    _send_mouse(win, QEvent.Type.MouseButtonRelease, 60, 60, left,
                Qt.MouseButton.NoButton)
    dlg.stop()
    assert "CLICK" in dlg.edit.toPlainText()
    assert "DRAG" not in dlg.edit.toPlainText()


def test_recorder_replay_rebuilds_scene(fp, win):
    dlg = fp.MacroRecorderDialog(win)
    dlg.edit.setPlainText("PLACE sofa 60 60 0\nPLACE armchair 120 60 0")
    dlg.edit.selectAll()
    dlg.replay()
    for _ in range(len(dlg._replay_lines) + 1):    # drive the step timer
        dlg._replay_step()
    furn = [it for it in win.scene.items()
            if isinstance(it, fp.FurnishingItem)]
    assert len(furn) == 2


def test_recorder_replay_enabled_only_with_selection(fp, win):
    dlg = fp.MacroRecorderDialog(win)
    dlg.edit.setPlainText("PLACE sofa 60 60 0")
    dlg._sync_buttons()
    assert not dlg.b_replay.isEnabled()            # no selection yet
    dlg.edit.selectAll()
    dlg._sync_buttons()
    assert dlg.b_replay.isEnabled()
    assert dlg.b_saveas.isEnabled()                # text present


def test_recorder_save_writes_file(fp, win, tmp_path):
    dlg = fp.MacroRecorderDialog(win)
    dlg.edit.setPlainText("PLACE sofa 60 60 0\nE DRAG 0 0 120 0")
    out = tmp_path / "m.fpm"
    dlg._write_macro(str(out))
    assert out.read_text(encoding="utf-8") == dlg.edit.toPlainText()


def test_recorder_opening_hook_captures_dialog_value(fp, win):
    # door/window sizes come from a dialog, not keystrokes: they must be
    # baked into a self-contained DOOR/WINDOW token so replay needs no dialog
    dlg = fp.MacroRecorderDialog(win)
    dlg.start()
    dlg.on_opening("door", QPointF(120, 0), "3680")
    dlg.on_opening("window", QPointF(240, 90), "4848")
    dlg.stop()
    text = dlg.edit.toPlainText()
    assert "DOOR 120 0 3680" in text
    assert "WINDOW 240 90 4848" in text


def test_recorder_room_hook_quotes_name(fp, win):
    dlg = fp.MacroRecorderDialog(win)
    dlg.start()
    dlg.on_room("Living Room", QPointF(120, 90))
    dlg.stop()
    assert 'ROOM "Living Room" 120 90' in dlg.edit.toPlainText()


def test_recorder_suppresses_raw_click_for_dialog_tools(fp, win):
    # with the Door tool active, the raw click is NOT recorded as CLICK —
    # the on_opening hook (with the dialog value) records it instead
    win.prepare_headless()
    dlg = fp.MacroRecorderDialog(win)
    dlg.start()
    win.set_tool(fp.TOOL_DOOR)
    left = Qt.MouseButton.LeftButton
    _send_mouse(win, QEvent.Type.MouseButtonPress, 120, 0, left, left)
    _send_mouse(win, QEvent.Type.MouseButtonRelease, 120, 0, left,
                Qt.MouseButton.NoButton)
    dlg.stop()
    assert "CLICK" not in dlg.edit.toPlainText()


def test_recorded_opening_replays_without_dialog(fp, win):
    # a captured DOOR token replays purely via run_macro (no dialog)
    win.run_macro("WALL 0 0 240 0 ext")
    dlg = fp.MacroRecorderDialog(win)
    dlg.edit.setPlainText("DOOR 120 0 3680")
    dlg.edit.selectAll()
    dlg.replay()
    for _ in range(len(dlg._replay_lines) + 1):
        dlg._replay_step()
    wall = next(it for it in win.scene.items() if isinstance(it, fp.WallItem))
    assert len(wall.openings) == 1
    assert wall.openings[0].kind == "door"
